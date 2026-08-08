"""§2.1 pre-payoff telegraphs — transcript additions only.

The fork is telegraphed while the debt still exists, through four
channels (payment remarks, calendar warnings, the Case-60 warning,
Carmine's ledger clause) plus the same-night pre-action warning on an
over-ceiling wash. Every test here drives the ACTUAL phase code —
morning() and night() with scripted consoles — and asserts on the
transcript, per the §2.7 telegraphy criterion: calendar gates warn at
least two days before any payoff they could gate; Case gates warn on an
earlier morning OR same-night before the act that would cross them.

These lines must never touch state, draw RNG, or alter a prompt string —
the equivalence harness (300/300 golden decision traces) is the gate for
that; these tests pin the transcript itself."""

import unittest

from extra_toppings import data, phases
from extra_toppings.models import new_state
from extra_toppings.rng import Streams
from extra_toppings.ui import ScriptedConsole

# Fragments that identify each telegraph line in a transcript.
REMARK_BIG_EARLY = "worth backing"
REMARK_BIG_LATE = "Serious money"
REMARK_SMALL_EARLY = "want to know you"
REMARK_SMALL_LATE = "deciding that now"
ALL_REMARKS = (REMARK_BIG_EARLY, REMARK_BIG_LATE,
               REMARK_SMALL_EARLY, REMARK_SMALL_LATE)
DAY20_WARNING = "losing interest"
DAY24_WARNING = "the table will be empty"
CASE60_WARNING = "read the papers too"
LEDGER_CLAUSE = "opinions about what comes after"
SAMENIGHT_WARNING = "reads the same spreadsheet"
LAUNDER_PROMPT = "Run how much through the books?"


class CaptureConsole(ScriptedConsole):
    """Scripted answers plus everything shown to the player, in order.
    Prompts are recorded into the same stream as say/bullet lines so
    tests can assert that a warning printed BEFORE its prompt."""

    def __init__(self, script=None):
        super().__init__(script)
        self.lines: list = []

    def say(self, text=""):
        self.lines.append(text)

    def bullet(self, text):
        self.lines.append(f"• {text}")

    def menu(self, prompt, options):
        self.lines.append(f"[menu] {prompt}")
        return super().menu(prompt, options)

    def ask_int(self, prompt, lo, hi, default=0):
        self.lines.append(f"[ask] {prompt}")
        return super().ask_int(prompt, lo, hi, default)

    def find(self, fragment):
        """Index of the first line containing fragment, or None."""
        for i, line in enumerate(self.lines):
            if fragment in line:
                return i
        return None


def run_morning(state, script=None, seed=1):
    con = CaptureConsole(script if script is not None else [8])
    phases.morning(state, con, Streams(seed))
    return con


def run_night(state, script, seed=1):
    con = CaptureConsole(script)
    phases.night(state, {}, {}, con, Streams(seed))
    return con


# ══ Channel 1: payment remarks in _pay_debt ═══════════════════════

class TestPaymentRemarks(unittest.TestCase):
    """Every non-trivial partial payment draws a remark keyed to
    trajectory; big-and-early is where the player first hears that
    finishing is the beginning of something."""

    def pay(self, day, amount, clean=20000):
        state = new_state()
        state.day = day
        state.clean = clean
        # menu: Pay Carmine → amount → Lock up
        return run_night(state, [1, amount, 4])

    def test_big_early_payment_draws_the_we_should_talk_line(self):
        con = self.pay(day=5, amount=6000)
        self.assertIsNotNone(con.find(REMARK_BIG_EARLY))
        self.assertIsNotNone(con.find("We should talk when this is done"))

    def test_big_late_and_small_payments_key_to_their_quadrants(self):
        self.assertIsNotNone(self.pay(day=20, amount=6000).find(REMARK_BIG_LATE))
        self.assertIsNotNone(self.pay(day=5, amount=1000).find(REMARK_SMALL_EARLY))
        self.assertIsNotNone(self.pay(day=20, amount=1000).find(REMARK_SMALL_LATE))

    def test_trivial_payments_draw_no_remark(self):
        con = self.pay(day=5, amount=100)
        for fragment in ALL_REMARKS:
            self.assertIsNone(con.find(fragment))

    def test_the_payoff_payment_keeps_the_paid_line_not_a_remark(self):
        con = self.pay(day=5, amount=data.START_DEBT)
        self.assertIsNotNone(con.find("PAID. Carmine counts it twice"))
        for fragment in ALL_REMARKS:
            self.assertIsNone(con.find(fragment))


# ══ Channel 2: calendar warnings on days 20 and 24 ════════════════

class TestCalendarWarnings(unittest.TestCase):
    """Unconditional on their days while the debt is alive — world
    facts, not chance. Day 24 warns about a day-25 deadline: at least
    two days before any payoff it could gate (§2.7)."""

    def morning_on(self, day, debt=data.START_DEBT):
        state = new_state()
        state.day = day
        state.debt = debt
        return run_morning(state)

    def test_day_20_carries_the_buyer_interest_warning(self):
        self.assertIsNotNone(self.morning_on(20).find(DAY20_WARNING))

    def test_day_24_turns_explicit(self):
        con = self.morning_on(24)
        self.assertIsNotNone(con.find(DAY24_WARNING))
        self.assertIsNotNone(con.find("Past day 25"))

    def test_other_days_carry_neither(self):
        for day in (19, 21, 23, 25):
            con = self.morning_on(day)
            self.assertIsNone(con.find(DAY20_WARNING), f"day {day}")
            self.assertIsNone(con.find(DAY24_WARNING), f"day {day}")

    def test_a_settled_debt_silences_the_calendar(self):
        for day in (20, 24):
            con = self.morning_on(day, debt=0)
            self.assertIsNone(con.find(DAY20_WARNING))
            self.assertIsNone(con.find(DAY24_WARNING))


# ══ Channel 3: the Case-60 warning, morning after the crossing ════

class TestCaseWarning(unittest.TestCase):
    """First prefix-sum crossing of 60 is derivable from the evidence
    records (each carries its day) — no stored flag, so the warning is
    trace-safe and prints exactly once: the morning after day D."""

    def crossed_state(self, records, debt=data.START_DEBT):
        state = new_state()
        state.debt = debt
        for day, magnitude in records:
            state.day = day
            state.add_case(magnitude, "seizure", kind="physical")
        return state

    def test_warning_prints_the_morning_after_the_crossing(self):
        state = self.crossed_state([(5, 65.0)])
        state.day = 6
        self.assertIsNotNone(run_morning(state).find(CASE60_WARNING))

    def test_warning_is_once_only_no_flag_needed(self):
        state = self.crossed_state([(5, 65.0)])
        state.day = 7
        self.assertIsNone(run_morning(state).find(CASE60_WARNING))

    def test_crossing_day_is_the_first_prefix_sum_at_60(self):
        # 30 on day 3, 35 on day 5: the file reaches 60 on day 5.
        state = self.crossed_state([(3, 30.0), (5, 35.0)])
        state.day = 4
        self.assertIsNone(run_morning(state).find(CASE60_WARNING))
        state = self.crossed_state([(3, 30.0), (5, 35.0)])
        state.day = 6
        self.assertIsNotNone(run_morning(state).find(CASE60_WARNING))

    def test_a_cold_case_never_warns(self):
        state = self.crossed_state([(5, 40.0)])
        state.day = 6
        self.assertIsNone(run_morning(state).find(CASE60_WARNING))


# ══ Channel 4: Carmine's ledger clause under half debt ════════════

class TestLedgerClause(unittest.TestCase):
    def morning_with_debt(self, debt):
        state = new_state()
        state.day = 10
        state.debt = debt
        return run_morning(state)

    def test_clause_appears_once_debt_drops_below_half(self):
        con = self.morning_with_debt(data.START_DEBT // 2 - 1)
        self.assertIsNotNone(con.find(LEDGER_CLAUSE))

    def test_no_clause_at_half_or_above(self):
        self.assertIsNone(
            self.morning_with_debt(data.START_DEBT // 2).find(LEDGER_CLAUSE))
        self.assertIsNone(
            self.morning_with_debt(data.START_DEBT).find(LEDGER_CLAUSE))


# ══ The same-night threshold warning, before the launder prompt ═══

class TestSameNightWarning(unittest.TestCase):
    """Near payoff, an over-ceiling wash that could push the Case past a
    gate (60/70/85) warns BEFORE the act — §2.7's same-night arm of the
    Case-gate disjunction. The warning is a printed line ahead of the
    launder prompt; the prompt string itself is golden and unchanged."""

    def night_with(self, debt=2000, clean=1000, dirty=12000, case=55.0,
                   script=(0, 0, 4)):
        state = new_state()
        state.day = 12
        state.debt = debt
        state.clean = clean
        state.dirty = dirty
        if case:
            state.add_case(case, "seizure", kind="physical")
        # legit_revenue_today stays 0 → believable ceiling 0 → any wash
        # is over-ceiling. Script: Launder → wash nothing → Lock up.
        return run_night(state, list(script))

    def test_warning_prints_before_the_launder_prompt(self):
        con = self.night_with()
        warn, prompt = con.find(SAMENIGHT_WARNING), con.find(LAUNDER_PROMPT)
        self.assertIsNotNone(warn)
        self.assertIsNotNone(prompt)
        self.assertLess(warn, prompt)

    def test_silent_when_the_debt_is_not_within_reach(self):
        con = self.night_with(debt=50000)
        self.assertIsNone(con.find(SAMENIGHT_WARNING))
        self.assertIsNotNone(con.find(LAUNDER_PROMPT))

    def test_silent_when_no_gate_is_in_reach(self):
        # Case 10 + at most 20 from a wash tops out at 30: no gate.
        con = self.night_with(case=10.0)
        self.assertIsNone(con.find(SAMENIGHT_WARNING))

    def test_silent_when_the_wash_fits_the_books(self):
        state = new_state()
        state.day = 12
        state.debt = 2000
        state.clean = 1000
        state.dirty = 500
        state.legit_revenue_today = 20000   # huge ceiling: dirty fits
        state.add_case(59.0, "seizure", kind="physical")
        con = run_night(state, [0, 0, 4])
        self.assertIsNone(con.find(SAMENIGHT_WARNING))
        self.assertIsNotNone(con.find(LAUNDER_PROMPT))

    def test_settled_debt_never_warns(self):
        con = self.night_with(debt=0, script=(0, 0, 4))
        self.assertIsNone(con.find(SAMENIGHT_WARNING))


if __name__ == "__main__":
    unittest.main()
