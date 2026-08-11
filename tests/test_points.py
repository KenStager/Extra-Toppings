"""P4b.2 — the points ledger: one history, two derived books.

§2.4.2 with rev. 29 item 1. The canonical state is an append-only
`PointsCycleRecord` history; arrears, strikes, the running total, the
next bill and its vig are DERIVED. "Two misses, consecutive or not"
and "one payment currently outstanding" are different facts, and one
counter cannot carry both — so nothing here writes a counter.

§7's local proof for this PR is an EXHAUSTIVE points-state transition
table plus ledger reconciliation, and both are below. The transitions
are driven through the REAL night phase wherever a real path exists;
the reconciliation is driven through the REAL save boundary.
"""

import unittest

from extra_toppings import models, partner, phases, save
from extra_toppings.models import (BranchState, PointsCycleRecord,
                                   new_state, partner_ledger)
from extra_toppings.rng import Streams
from extra_toppings.ui import ScriptedConsole
from test_partner import PARTNER_ON, seat_partner, table_state

POINTS = models.POINTS_PER_CYCLE            # 2,500
VIG = models.POINTS_VIG                     # 500
CYCLE = models.POINTS_CYCLE_DAYS            # 5


class Listening(ScriptedConsole):
    def __init__(self, script=None):
        super().__init__(script)
        self.lines: list = []

    def say(self, text: str = "") -> None:
        self.lines.append(text)

    def bullet(self, text: str) -> None:
        self.lines.append(f"• {text}")

    def said(self, fragment: str) -> bool:
        return any(fragment in line for line in self.lines)


def seated(clean: int = 50_000):
    """A Partner run standing just after the deal, with whatever
    money the case under test needs."""
    state = table_state(payoff_day=13)
    seat_partner(state)
    state.clean = clean
    state.dirty = 0
    return state


def run_night(state, con=None):
    """The REAL night phase — the points clock is a branch night
    tick, so every transition below goes through the same door play
    does."""
    con = con or Listening()
    phases.night(state, {"routes": {}},
                 {"wagons": phases.WagonNight(state)}, con,
                 Streams(3), PARTNER_ON)
    return con


def advance_to(state, day, con=None):
    """Nights until the calendar reaches `day` — `phases.night`
    advances the day itself."""
    while state.day < day:
        run_night(state, con)
    return state


# ══ the derived view ══════════════════════════════════════════════

class TestBothBooksDerive(unittest.TestCase):
    """No arrears field, no strike counter, no running total — the
    history is the state and the rest is arithmetic over it."""

    def test_the_retired_counters_are_gone_from_the_schema(self):
        names = {f.name for f in BranchState.__dataclass_fields__.values()}
        self.assertNotIn("points_missed", names)
        self.assertNotIn("vig_owed", names)
        self.assertIn("points_cycles", names)

    def test_an_empty_history_owes_the_first_bill_and_nothing_else(self):
        bs = BranchState(points_due_day=19)
        view = partner_ledger(bs)
        self.assertEqual((view.arrears, view.strikes, view.paid_total),
                         (0, 0, 0))
        self.assertEqual((view.next_bill, view.next_vig), (POINTS, 0))
        self.assertEqual(view.next_due_day, 19)
        self.assertFalse(view.foreclosed)

    def test_a_paid_cycle_clears_arrears_and_leaves_no_strike(self):
        bs = BranchState(points_due_day=24, points_cycles=[
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0,
                              paid=True, paid_day=19)])
        view = partner_ledger(bs)
        self.assertEqual((view.arrears, view.strikes), (0, 0))
        self.assertEqual(view.paid_total, POINTS)
        self.assertEqual((view.next_bill, view.next_vig), (POINTS, 0))
        self.assertEqual(view.next_due_day, 24)

    def test_a_miss_owes_it_forward_and_prices_the_vig(self):
        bs = BranchState(points_due_day=24, points_cycles=[
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0, paid=False)])
        view = partner_ledger(bs)
        self.assertEqual((view.arrears, view.strikes), (POINTS, 1))
        self.assertEqual(view.paid_total, 0)
        self.assertEqual(view.next_vig, VIG)
        self.assertEqual(view.next_bill, POINTS + POINTS + VIG)

    def test_paying_the_carried_bill_clears_arrears_and_keeps_the_strike(self):
        # THE reason there are two books: the money is square and the
        # miss still happened.
        bs = BranchState(points_due_day=29, points_cycles=[
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0, paid=False),
            PointsCycleRecord(due_day=24, bill=POINTS * 2 + VIG, vig=VIG,
                              paid=True, paid_day=24)])
        view = partner_ledger(bs)
        self.assertEqual(view.arrears, 0)
        self.assertEqual(view.strikes, 1)
        self.assertEqual(view.paid_total, POINTS * 2 + VIG)
        self.assertEqual((view.next_bill, view.next_vig), (POINTS, 0))
        self.assertFalse(view.foreclosed)

    def test_the_second_strike_forecloses_however_far_apart(self):
        # "At any later cycle, consecutive or not" — a paid cycle
        # between the two misses changes nothing.
        cycles = [
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0, paid=False),
            PointsCycleRecord(due_day=24, bill=POINTS * 2 + VIG, vig=VIG,
                              paid=True, paid_day=24),
            PointsCycleRecord(due_day=29, bill=POINTS, vig=0, paid=False)]
        view = partner_ledger(BranchState(points_due_day=34,
                                          points_cycles=cycles))
        self.assertEqual(view.strikes, 2)
        self.assertTrue(view.foreclosed)


# ══ the exhaustive transition table, through the real night ═══════

class TestTheTransitionTable(unittest.TestCase):
    """Every state the clock can be in, and every way out of it."""

    def test_no_cycle_falls_due_before_its_day(self):
        state = seated()
        due = state.branch_state.points_due_day
        advance_to(state, due)
        self.assertEqual(state.branch_state.points_cycles, [])
        self.assertEqual(state.branch_state.points_due_day, due)

    def test_the_bill_is_paid_on_the_day_it_falls_due(self):
        state = seated()
        due = state.branch_state.points_due_day
        advance_to(state, due + 1)      # runs the night it falls due
        cycles = state.branch_state.points_cycles
        self.assertEqual(len(cycles), 1)
        self.assertEqual((cycles[0].due_day, cycles[0].bill,
                          cycles[0].vig, cycles[0].paid), (due, POINTS, 0, True))
        self.assertEqual(cycles[0].paid_day, due)
        self.assertEqual(state.branch_state.points_due_day, due + CYCLE)

    def test_payment_draws_street_money_first(self):
        # Through the real night, the claim that can be made without
        # pretending the points bill is the night's only spending:
        # the street money is gone and the bill was met. The exact
        # arithmetic is pinned at the authority's own boundary below,
        # where nothing else is moving cash.
        state = seated(clean=10_000)
        state.dirty = 1_000
        due = state.branch_state.points_due_day
        advance_to(state, due + 1)
        self.assertEqual(state.dirty, 0)
        self.assertTrue(state.branch_state.points_cycles[0].paid)

    def test_the_bill_is_taken_dirty_first_at_the_boundary(self):
        # The points authority called directly, where the only money
        # moving is the bill: street money first, to the dollar.
        state = seated(clean=10_000)
        state.dirty = 1_000
        state.day = state.branch_state.points_due_day
        partner.night_points(state, Listening())
        self.assertEqual((state.dirty, state.clean),
                         (0, 10_000 - (POINTS - 1_000)))

    def test_an_empty_till_records_a_miss_and_moves_nothing(self):
        state = seated(clean=0)
        due = state.branch_state.points_due_day
        advance_to(state, due + 1)
        cycle = state.branch_state.points_cycles[0]
        self.assertFalse(cycle.paid)
        self.assertIsNone(cycle.paid_day)
        self.assertEqual((state.clean, state.dirty), (0, 0))
        self.assertIsNone(state.game_over)

    def test_a_partial_purse_is_a_miss_not_a_part_payment(self):
        # There is no partial payment: a half-paid bill is a third
        # state the day-30 grade has no arm for, so the money stays
        # in the till and the cycle records a miss. Driven at the
        # authority's boundary, because the real night also spends on
        # payroll and rent and the claim here is about the bill.
        state = seated(clean=POINTS - 1)
        state.day = state.branch_state.points_due_day
        partner.night_points(state, Listening())
        self.assertFalse(state.branch_state.points_cycles[0].paid)
        self.assertEqual((state.clean, state.dirty), (POINTS - 1, 0))

    def test_a_short_purse_misses_through_the_real_night_too(self):
        state = seated(clean=0)
        due = state.branch_state.points_due_day
        advance_to(state, due + 1)
        self.assertFalse(state.branch_state.points_cycles[0].paid)

    def test_the_next_bill_carries_the_miss_and_the_vig(self):
        state = seated(clean=0)
        due = state.branch_state.points_due_day
        advance_to(state, due + 1)
        state.clean = 50_000                    # money arrives
        advance_to(state, due + CYCLE + 1)
        second = state.branch_state.points_cycles[1]
        self.assertEqual(second.due_day, due + CYCLE)
        self.assertEqual(second.bill, POINTS * 2 + VIG)
        self.assertEqual(second.vig, VIG)
        self.assertTrue(second.paid)
        view = partner.ledger(state)
        self.assertEqual((view.arrears, view.strikes), (0, 1))

    def test_the_second_miss_forecloses_that_night(self):
        state = seated(clean=0)
        due = state.branch_state.points_due_day
        con = Listening()
        advance_to(state, due + 1, con)
        self.assertIsNone(state.game_over)      # one strike stands
        advance_to(state, due + CYCLE + 1, con)
        self.assertEqual(state.game_over, "foreclosed")
        self.assertEqual(partner.ledger(state).strikes, 2)
        self.assertTrue(con.said("Two misses"), con.lines)

    def test_the_schedule_never_drifts_when_a_bill_is_met_late(self):
        # The cursor advances from the DUE DATE, never from the day
        # the money happened to arrive.
        state = seated(clean=0)
        first = state.branch_state.points_due_day
        advance_to(state, first + 1)            # missed
        state.clean = 50_000
        advance_to(state, first + CYCLE + 1)    # paid, carrying arrears
        self.assertEqual(
            [c.due_day for c in state.branch_state.points_cycles],
            [first, first + CYCLE])
        self.assertEqual(state.branch_state.points_due_day,
                         first + 2 * CYCLE)

    def test_the_arrest_latch_outranks_foreclosure(self):
        # §2.5: accrual sets game_over first, and the branch night
        # ticks only run on live games — so a run that latches on the
        # same night is arrested, not foreclosed.
        state = seated(clean=0)
        due = state.branch_state.points_due_day
        advance_to(state, due + 1)              # one strike
        state.add_case(100.0, "the file closes", kind="physical")
        self.assertEqual(state.game_over, "arrested")
        advance_to(state, due + CYCLE + 1)
        self.assertEqual(state.game_over, "arrested")


# ══ ledger reconciliation at the persistence boundary ═════════════

class TestTheLedgerReconciles(unittest.TestCase):
    """The war's reconciliation oracle, applied to Carmine's book: a
    cached summary reconciles exactly against the history or it is
    not a summary."""

    def _state(self, cycles, cursor):
        """A seated run standing AFTER the cycles it carries — a
        record for a day the run has not reached is its own refusal
        (the calendar check), and these cases are about the ledger's
        arithmetic."""
        state = table_state(payoff_day=13)
        seat_partner(state)
        state.branch_state.points_cycles = list(cycles)
        state.branch_state.points_due_day = cursor
        if cycles:
            state.day = max(state.day, max(c.due_day for c in cycles))
        return state

    def test_a_true_history_round_trips(self):
        state = self._state([
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0,
                              paid=True, paid_day=19)], 24)
        loaded = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(loaded.branch_state.points_cycles,
                         state.branch_state.points_cycles)
        self.assertEqual(partner_ledger(loaded.branch_state).paid_total,
                         POINTS)

    def test_a_doctored_bill_is_refused(self):
        state = self._state([
            PointsCycleRecord(due_day=19, bill=POINTS - 500, vig=0,
                              paid=True, paid_day=19)], 24)
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(state))
        self.assertIn("the ledger owes", str(caught.exception))

    def test_a_vig_charged_on_nothing_is_refused(self):
        state = self._state([
            PointsCycleRecord(due_day=19, bill=POINTS + VIG, vig=VIG,
                              paid=True, paid_day=19)], 24)
        with self.assertRaises(ValueError):
            save.state_from_dict(save.state_to_dict(state))

    def test_a_carried_bill_that_forgets_its_arrears_is_refused(self):
        state = self._state([
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0, paid=False),
            PointsCycleRecord(due_day=24, bill=POINTS, vig=0,
                              paid=True, paid_day=24)], 29)
        with self.assertRaises(ValueError):
            save.state_from_dict(save.state_to_dict(state))

    def test_a_cycle_out_of_cadence_is_refused(self):
        state = self._state([
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0,
                              paid=True, paid_day=19),
            PointsCycleRecord(due_day=26, bill=POINTS, vig=0,
                              paid=True, paid_day=26)], 31)
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(state))
        self.assertIn("cadence", str(caught.exception))

    def test_a_cursor_that_disagrees_with_the_ledger_is_refused(self):
        state = self._state([
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0,
                              paid=True, paid_day=19)], 19)
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(state))
        self.assertIn("cursor", str(caught.exception))

    def test_a_payment_before_the_bill_is_refused(self):
        state = self._state([
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0,
                              paid=True, paid_day=17)], 24)
        with self.assertRaises(ValueError):
            save.state_from_dict(save.state_to_dict(state))

    def test_an_unpaid_cycle_cannot_record_a_payment_day(self):
        state = self._state([
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0,
                              paid=False, paid_day=19)], 24)
        with self.assertRaises(ValueError):
            save.state_from_dict(save.state_to_dict(state))

    def test_inexact_numbers_are_refused(self):
        for field, bad in (("due_day", 19.0), ("bill", float(POINTS)),
                           ("vig", True), ("paid", 1)):
            with self.subTest(f"{field}={bad!r}"):
                record = PointsCycleRecord(due_day=19, bill=POINTS, vig=0,
                                           paid=True, paid_day=19)
                setattr(record, field, bad)
                state = self._state([record], 24)
                with self.assertRaises(ValueError):
                    save.state_from_dict(save.state_to_dict(state))

    def test_a_cycle_the_run_has_not_reached_is_refused(self):
        # The RULER class: the ledger's internal arithmetic can be
        # perfect and still describe a Tuesday nobody has lived.
        state = self._state([
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0,
                              paid=True, paid_day=19)], 24)
        state.day = 18
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(state))
        self.assertIn("has not reached", str(caught.exception))

    def test_a_payment_the_run_has_not_reached_is_refused(self):
        state = self._state([
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0,
                              paid=True, paid_day=25)], 24)
        state.day = 20
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(state))
        self.assertIn("has not reached", str(caught.exception))

    def test_a_bill_that_is_not_whole_dollars_never_moves_money(self):
        # The payment authority is a mutation boundary: a float or a
        # NaN would slip past the affordability comparison and then
        # subtract something that is not a number of dollars.
        state = new_state()
        state.dirty, state.clean = 500, 500
        for bad in (2500.0, float("nan"), True, "2500"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    models.pay_dirty_first(state, bad)
                self.assertEqual((state.dirty, state.clean), (500, 500))

    def test_a_live_run_cannot_carry_two_strikes(self):
        # The second strike forecloses THAT NIGHT, so a payload
        # carrying two on a live run is a run that should have ended.
        state = self._state([
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0, paid=False),
            PointsCycleRecord(due_day=24, bill=POINTS * 2 + VIG, vig=VIG,
                              paid=False)], 29)
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(state))
        self.assertIn("forecloses", str(caught.exception))

    def test_the_same_two_strikes_load_on_a_finished_run(self):
        state = self._state([
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0, paid=False),
            PointsCycleRecord(due_day=24, bill=POINTS * 2 + VIG, vig=VIG,
                              paid=False)], 29)
        state.game_over = "foreclosed"
        loaded = save.state_from_dict(save.state_to_dict(state))
        self.assertTrue(partner_ledger(loaded.branch_state).foreclosed)

    def test_a_real_run_survives_its_own_save_at_every_step(self):
        # The reconciliation that matters: whatever the night writes,
        # the boundary accepts — asserted after every cycle rather
        # than once at the end.
        state = seated(clean=POINTS * 2)        # pays once, then misses
        for _ in range(3):
            due = state.branch_state.points_due_day
            advance_to(state, due + 1)
            save.state_from_dict(save.state_to_dict(state))
            if state.game_over:
                break
        # Exactly what a purse of two bills buys: the first cycle
        # paid, then misses, and the second miss ends it — asserted
        # as a shape, not as "at least something happened".
        cycles = state.branch_state.points_cycles
        self.assertEqual([c.paid for c in cycles], [True, False, False])
        view = partner_ledger(state.branch_state)
        self.assertEqual(view.paid_total, POINTS)
        self.assertEqual(view.strikes, 2)
        self.assertEqual(state.game_over, "foreclosed")


# ══ the shared authorities Partner now joins ══════════════════════

class TestPartnerJoinsTheSharedMachinery(unittest.TestCase):
    def test_the_remediation_verbs_are_unlocked(self):
        # rev. 29 item 7: two registers give the Case a new paper
        # source, and counsel is affordable here and busy.
        self.assertIn("partner", models.REMEDIATION_BRANCHES)
        state = seated()
        self.assertTrue(models.remediation_unlocked(state))

    def test_the_insolvency_counter_is_the_shared_one(self):
        state = seated(clean=0)
        # Insolvency is an EMPTY world, not merely an empty till:
        # no stock anywhere and no dirty dollar hidden anywhere.
        for a_shop in state.shops:
            a_shop.stash, a_shop.ingredients = {}, 0
        state.dirty = state.warehouse_cash = 0
        state.branch_state.insolvent_days = 0
        outcome = models.insolvency_tick(state, payroll_short=True)
        self.assertEqual(outcome, "warned")     # one bad night, exactly
        self.assertEqual(state.branch_state.insolvent_days, 1)
        self.assertIsNone(state.game_over)
        # And the second night ends it, through the same authority.
        self.assertEqual(models.insolvency_tick(state, payroll_short=True),
                         "broke")
        self.assertEqual(state.game_over, "broke")

    def test_the_dirty_first_authority_is_one_home(self):
        # Hoisted out of `war.night_obligation` (rev. 29 item 7): the
        # war and the points now draw money the same way, and the
        # arithmetic is the one the war always used — street money
        # first, affordability checked before any mutation.
        state = new_state()
        state.dirty, state.clean = 300, 1_000
        self.assertTrue(models.pay_dirty_first(state, 800))
        self.assertEqual((state.dirty, state.clean), (0, 500))

    def test_an_unaffordable_bill_moves_neither_till(self):
        state = new_state()
        state.dirty, state.clean = 300, 100
        self.assertFalse(models.pay_dirty_first(state, 800))
        self.assertEqual((state.dirty, state.clean), (300, 100))

    def test_the_war_still_pays_the_way_it_always_did(self):
        # The hoist must not have moved the war's behaviour: dirty
        # first, and a bounced bonus leaves both tills alone.
        state = new_state()
        state.dirty, state.clean = 100, 100
        self.assertFalse(models.pay_dirty_first(state, 500))
        self.assertEqual((state.dirty, state.clean), (100, 100))


if __name__ == "__main__":
    unittest.main()
