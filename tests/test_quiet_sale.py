"""The Quiet Sale (P1b, design §2.4.4): the escrow week through the
real loop — the scene commit, the itemized mark, incidents and
collapse, laundering off, the closing's tiers and reclassification, and
the brokers stream drawn only after the chair is actually taken."""

import random
import unittest

from extra_toppings import models, data, escrow, game, phases, save, sitdown
from extra_toppings.bot import GreedyBot
from extra_toppings.config import GameConfig
from extra_toppings.models import (BranchState, SitdownSnapshot, new_state,
                                   validate_branch_state)
from extra_toppings.rng import Streams
from extra_toppings.ui import ScriptedConsole

def _wag(state, **report):
    """Every direct `night` call needs the assignment authority the
    service phase would have opened (P4b.1a). An UNSPENT one is the
    honest fixture here: these tests do not run service, so no wagon
    departed."""
    return {**report, "wagons": phases.WagonNight(state)}

SALE_ON = GameConfig(fork_enabled=True,
                     enabled_branches=frozenset({"quiet_sale"}))


class CaptureConsole(ScriptedConsole):
    def __init__(self, script=None):
        super().__init__(script)
        self.lines: list = []

    def say(self, text=""):
        self.lines.append(text)

    def bullet(self, text):
        self.lines.append(f"• {text}")

    def menu(self, prompt, options):
        self.lines.append(f"[menu] {prompt}")
        self.lines.extend(f"    {o}" for o in options)
        return super().menu(prompt, options)

    def find(self, fragment):
        for i, line in enumerate(self.lines):
            if fragment in line:
                return i
        return None


def in_escrow(payoff_day=13, case=0.0, rep=50.0):
    """A state that took the chair through the REAL scene, standing at
    the morning of diligence day 1 (the sit-down day)."""
    state = new_state()
    state.debt = 0
    state.debt_paid_day = payoff_day
    state.day = payoff_day + 1
    state.shop.reputation = rep
    if case:
        state.add_case(case, "prior seizures", kind="physical")
    state.sitdown_snapshot = SitdownSnapshot(
        payoff_day=payoff_day, case_at_lockup=case,
        evidence_count_at_lockup=len(state.evidence))
    sitdown.run_scene(state, CaptureConsole([3, 1]), SALE_ON)
    if state.branch != "quiet_sale":
        raise AssertionError("scene did not enter the sale")
    return state


class ForcedSaleConsole(CaptureConsole):
    """Scene policy for whole-run tests: take the Quiet Sale when the
    table opens, progress-last everywhere else in the scene."""

    def scene_menu(self, namespace, prompt, options):
        if prompt == "Your chair:" and not getattr(self, "_tried", False):
            self._tried = True
            return 3
        return len(options) - 1


def forced_sale_bot(seed):
    class ForcedSale(GreedyBot):
        def scene_menu(self, namespace, prompt, options):
            if prompt == "Your chair:" and not getattr(self, "_tried", False):
                self._tried = True
                return 3
            return len(options) - 1
    return ForcedSale(random.Random(seed), verbose=False)


# ══ Taking the chair ══════════════════════════════════════════════

class TestTakingTheChair(unittest.TestCase):
    def test_commit_sets_branch_state_and_terms(self):
        state = in_escrow()
        self.assertEqual(state.branch, "quiet_sale")
        self.assertEqual(state.act, 2)
        self.assertEqual(state.branch_state.diligence_day, 1)
        validate_branch_state(state.branch, state.branch_state)

    def test_buyer_identity_follows_sal(self):
        state = new_state()
        state.debt = 0
        state.debt_paid_day = 13
        state.day = 14
        state.rivals["sal"].relation = 10.0
        state.sitdown_snapshot = SitdownSnapshot(13, 0.0, 0)
        con = CaptureConsole([3, 1])
        sitdown.run_scene(state, con, SALE_ON)
        self.assertIsNotNone(con.find("straw"))
        state2 = new_state()
        state2.debt = 0
        state2.debt_paid_day = 13
        state2.day = 14
        state2.rivals["sal"].relation = -30.0
        state2.sitdown_snapshot = SitdownSnapshot(13, 0.0, 0)
        con2 = CaptureConsole([3, 1])
        sitdown.run_scene(state2, con2, SALE_ON)
        self.assertIsNotNone(con2.find("out-of-town operator"))

    def test_declining_the_confirmation_returns_to_the_table(self):
        state = new_state()
        state.debt = 0
        state.debt_paid_day = 13
        state.day = 14
        state.sitdown_snapshot = SitdownSnapshot(13, 0.0, 0)
        con = CaptureConsole([3, 0, 4, 1])     # sale, reconsider, stand pat
        sitdown.run_scene(state, con, SALE_ON)
        self.assertEqual(state.branch, "stand_pat")


# ══ The mark ══════════════════════════════════════════════════════

class TestTheMark(unittest.TestCase):
    def test_the_formula_term_by_term(self):
        state = in_escrow(case=31.0, rep=24.0)
        state.shop.upgrades = {"walk_in", "guard"}      # $3,000 spent
        # base 3000 + 24*140 + 3000*0.5 = 7860; less 31*45 = 6465
        self.assertEqual(escrow.compute_mark(state), 6465)

    def test_the_war_clause_arms_at_vendetta_or_a_live_telegraph(self):
        state = in_escrow(case=31.0, rep=24.0)
        state.shop.upgrades = {"walk_in", "guard"}
        state.rivals["vinnie"].relation = -60.0
        self.assertEqual(escrow.compute_mark(state), int(6465 * 0.8))
        state.rivals["vinnie"].relation = -10.0
        state.rivals["vinnie"].warning = models.RaidWarning(2, models.HOME_SHOP_KEY)
        self.assertEqual(escrow.compute_mark(state), int(6465 * 0.8))

    def test_incident_discounts_compound_into_the_mark(self):
        state = in_escrow(case=31.0, rep=24.0)
        state.shop.upgrades = {"walk_in", "guard"}
        state.branch_state.escrow_incidents = 1        # a legal state:
        state.branch_state.escrow_discount_pct = 20    # one priced incident
        self.assertEqual(escrow.compute_mark(state),
                         6465 - round(6465 * 20 / 100))

    def test_the_mark_moves_only_when_inputs_move(self):
        state = in_escrow(rep=40.0)
        streams = Streams(3)
        escrow.diligence_morning(state, CaptureConsole([]), streams)
        first = state.branch_state.escrow_mark
        state.day += 1
        escrow.diligence_morning(state, CaptureConsole([]), streams)
        self.assertEqual(state.branch_state.escrow_mark, first)
        state.shop.reputation += 3          # an input moves
        state.day += 1
        con = CaptureConsole([])
        escrow.diligence_morning(state, con, streams)
        self.assertEqual(state.branch_state.escrow_mark,
                         first + 3 * escrow.REP_PRICE)
        self.assertIsNotNone(con.find("only moves when its inputs do"))


# ══ Diligence week rules ══════════════════════════════════════════

class TestDiligenceRules(unittest.TestCase):
    def test_laundering_is_off_all_week(self):
        # The menu never offers laundering in escrow (rev. 7 — the
        # option is replaced, not refused-after-selection)…
        state = in_escrow()
        state.dirty = 5000
        evidence_before = len(state.evidence)
        con = CaptureConsole([0, 0, 4])        # Burn → nothing → Lock up
        phases.night(state, {}, _wag(state), con, Streams(3))
        self.assertIsNotNone(con.find("nothing washes"))
        self.assertEqual(state.dirty, 5000)
        self.assertEqual(len(state.evidence), evidence_before)
        # …and the launder path itself still refuses, as a belt.
        direct = CaptureConsole([])
        self.assertEqual(phases._launder(state, 9999, direct), 0)
        self.assertIsNotNone(direct.find("books are being read"))
        self.assertEqual(state.dirty, 5000)

    def test_contraband_at_the_day_one_walkthrough_is_an_incident(self):
        state = in_escrow(rep=40.0)
        state.shop_stash = {"mushrooms": 10}
        state.branch_state.escrow_mark = escrow.compute_mark(state)
        before = state.branch_state.escrow_mark
        con = CaptureConsole([])
        escrow.walkthrough(state, con, Streams(3))   # day 1: he walks, always
        self.assertEqual(state.branch_state.escrow_incidents, 1)
        # Rev. 8: -20..-35, drawn in whole percentage points.
        self.assertIsInstance(state.branch_state.escrow_discount_pct, int)
        self.assertGreaterEqual(state.branch_state.escrow_discount_pct, 20)
        self.assertLessEqual(state.branch_state.escrow_discount_pct, 35)
        self.assertLess(state.branch_state.escrow_mark, before)
        self.assertIsNotNone(con.find("INCIDENT"))

    def test_a_clean_walkthrough_is_not(self):
        state = in_escrow()
        state.shop_stash = {}
        con = CaptureConsole([])
        escrow.walkthrough(state, con, Streams(3))
        self.assertEqual(state.branch_state.escrow_incidents, 0)
        self.assertIsNotNone(con.find("Flour and receipts"))

    def test_the_second_incident_collapses_to_stand_pat(self):
        state = in_escrow(rep=40.0)
        rep_before = state.shop.reputation
        streams = Streams(3)
        con = CaptureConsole([])
        escrow.record_incident(state, con, streams, "first")
        self.assertEqual(state.branch, "quiet_sale")
        escrow.record_incident(state, con, streams, "second")
        self.assertEqual(state.branch, "stand_pat")
        self.assertIsNone(state.branch_state)
        self.assertEqual(state.shop.reputation, rep_before - 8)
        self.assertIsNone(state.game_over)     # not an ending: play on
        self.assertFalse(sitdown.due(state))   # the buyer is gone for good

    def test_the_offsite_truck_carries_a_one_time_risk(self):
        fired = quiet = False
        for seed in range(60):
            state = in_escrow()
            state.warehouse = {}
            state.shop_stash = {"oregano": 5}
            con = CaptureConsole([2, 0, 5, 4])   # Move stash → shop→wh → all
            phases.night(state, {}, _wag(state), con, Streams(seed))
            if con.find("INCIDENT: a loaded truck") is not None:
                fired = True
            elif con.find("nobody writes anything down") is not None:
                quiet = True
            if fired and quiet:
                return
        self.fail("off-site risk never showed both outcomes across seeds")

    def test_staff_learn_on_day_two(self):
        state = in_escrow()
        state.day += 1                          # diligence day 2
        morale_before = [e.morale for e in state.hired()]
        con = CaptureConsole([])
        escrow.diligence_morning(state, con, Streams(3))
        self.assertIsNotNone(con.find("man in the good suit"))
        for e, before in zip(state.hired(), morale_before):
            self.assertEqual(e.morale, before - 1)


# ══ The closing ═══════════════════════════════════════════════════

def at_closing(**kwargs):
    state = in_escrow(**kwargs)
    state.branch_state.escrow_mark = escrow.compute_mark(state)
    state.day = escrow.sitdown_day(state) + escrow.DILIGENCE_DAYS
    return state


class TestTheClosing(unittest.TestCase):
    def test_signing_ends_the_run_and_pays_the_mark(self):
        state = at_closing(rep=40.0)
        mark = escrow.compute_mark(state)
        heads = len(state.hired())
        clean_before = state.clean
        con = CaptureConsole([1, 1])           # sign; severance a name
        escrow.diligence_morning(state, con, Streams(3))
        self.assertEqual(state.game_over, "sold")
        self.assertEqual(state.clean, clean_before + mark
                         - heads * escrow.SEVERANCE_PER_HEAD)
        # The buyer's price is never overwritten; the outcome persists.
        self.assertEqual(state.branch_state.escrow_mark, mark)
        self.assertEqual(state.branch_state.severance_paid,
                         heads * escrow.SEVERANCE_PER_HEAD)
        self.assertIsNotNone(con.find("hear it from you"))

    def test_unaffordable_severance_is_not_on_the_sheet(self):
        # The review's repro: Case 84.9, rep 5, clean $0, two employees —
        # the mark clamps at zero and the envelopes cannot be funded.
        state = at_closing(case=84.9, rep=5.0)
        state.clean = 0
        state.dirty = 0
        state.shop_stash = {}
        con = CaptureConsole([1])              # sign; no severance menu
        escrow.diligence_morning(state, con, Streams(3))
        self.assertEqual(state.game_over, "sold")
        self.assertGreaterEqual(state.clean, 0)
        self.assertGreaterEqual(state.branch_state.escrow_mark, 0)
        self.assertEqual(state.branch_state.severance_paid, 0)
        self.assertIsNotNone(con.find("can't afford"))

    def test_the_closing_outcome_round_trips(self):
        state = at_closing(rep=40.0)
        escrow.diligence_morning(state, CaptureConsole([1, 1]), Streams(3))
        restored = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(restored.branch_state.severance_outcome, "paid")
        self.assertEqual(restored.branch_state.severance_paid,
                         state.branch_state.severance_paid)
        self.assertEqual(restored.branch_state.closing_headcount, 2)

    def test_every_severance_outcome_is_distinct_and_persists(self):
        # paid
        paid = at_closing(rep=40.0)
        escrow.diligence_morning(paid, CaptureConsole([1, 1]), Streams(3))
        self.assertEqual(paid.branch_state.severance_outcome, "paid")
        # declined
        declined = at_closing(rep=40.0)
        escrow.diligence_morning(declined, CaptureConsole([1, 0]), Streams(3))
        self.assertEqual(declined.branch_state.severance_outcome, "declined")
        self.assertEqual(declined.branch_state.severance_paid, 0)
        # unaffordable
        broke = at_closing(case=84.9, rep=5.0)
        broke.clean = 0
        broke.dirty = 0
        broke.shop_stash = {}
        escrow.diligence_morning(broke, CaptureConsole([1]), Streams(3))
        self.assertEqual(broke.branch_state.severance_outcome, "unaffordable")
        # not_applicable — the review's repro: no crew, and the epilogue
        # must not invent one to be sorry for.
        alone = at_closing(rep=40.0)
        for e in alone.employees:
            e.hired = False
        escrow.diligence_morning(alone, CaptureConsole([1]), Streams(3))
        self.assertEqual(alone.branch_state.severance_outcome,
                         "not_applicable")
        self.assertEqual(alone.branch_state.closing_headcount, 0)
        epi = CaptureConsole([])
        game.epilogue(alone, epi)
        self.assertIsNone(epi.find("crew found out"))
        self.assertIsNone(epi.find("envelopes"))
        # every outcome round-trips
        for state in (paid, declined, broke, alone):
            restored = save.state_from_dict(save.state_to_dict(state))
            self.assertEqual(restored.branch_state.severance_outcome,
                             state.branch_state.severance_outcome)

    def test_unaffordable_severance_reaches_the_epilogue(self):
        broke = at_closing(case=84.9, rep=5.0)
        broke.clean = 0
        broke.dirty = 0
        broke.shop_stash = {}
        escrow.diligence_morning(broke, CaptureConsole([1]), Streams(3))
        epi = CaptureConsole([])
        game.epilogue(broke, epi)
        self.assertIsNotNone(epi.find("difference between broke and cheap"))

    def test_unknown_severance_outcomes_are_rejected(self):
        bad = BranchState.quiet_sale(diligence_day=2)
        bad.severance_outcome = "ghosted"
        with self.assertRaises(ValueError):
            validate_branch_state("quiet_sale", bad)

    def test_the_careful_bot_burns_only_past_the_tolerance(self):
        from extra_toppings.bot import EscrowBot
        bot = EscrowBot(random.Random(1))
        ans = bot.ask_int("Burn how much? (dirty $900; the buyer's ledger "
                          "test tolerates $200)", 0, 900, 0)
        self.assertEqual(ans, 900 - escrow.DIRTY_TOLERANCE)
        bot_low = EscrowBot(random.Random(1))
        self.assertEqual(bot_low.ask_int("Burn how much? (dirty $150…)",
                                         0, 150, 0), 0)

    def test_walking_away_reverts_and_the_run_continues(self):
        state = at_closing()
        rep_before = state.shop.reputation
        con = CaptureConsole([0])              # tear it up
        escrow.diligence_morning(state, con, Streams(3))
        self.assertIsNone(state.game_over)
        self.assertEqual(state.branch, "stand_pat")
        self.assertEqual(state.shop.reputation, rep_before)  # no collapse tax

    def test_cheap_severance_persists_and_the_epilogue_remembers(self):
        state = at_closing()
        con = CaptureConsole([1, 0])           # sign; nothing
        escrow.diligence_morning(state, con, Streams(3))
        self.assertIsNotNone(con.find("envelope that never came"))
        self.assertEqual(state.branch_state.severance_paid, 0)
        epi = CaptureConsole([])
        game.epilogue(state, epi)
        self.assertIsNotNone(epi.find("No envelopes"))

    def test_paid_severance_reaches_the_epilogue_too(self):
        state = at_closing(rep=40.0)
        escrow.diligence_morning(state, CaptureConsole([1, 1]), Streams(3))
        epi = CaptureConsole([])
        game.epilogue(state, epi)
        self.assertIsNotNone(epi.find("handed over before the ink"))

    def test_a_clean_close_reaches_the_sold_well_tier(self):
        state = at_closing(rep=60.0)
        state.clean = 30000
        state.dirty = 0
        state.shop_stash = {}
        escrow.diligence_morning(state, CaptureConsole([1, 1]), Streams(3))
        self.assertEqual(escrow.sale_tier(state), "well")
        con = CaptureConsole([])
        game.epilogue(state, con)
        self.assertIsNotNone(con.find("sold well"))

    def test_kept_trade_caps_at_modest_no_matter_the_number(self):
        state = at_closing(rep=60.0)
        state.clean = 40000
        state.shop_stash = {"oregano": 12}     # rides out the back gate
        escrow.diligence_morning(state, CaptureConsole([1, 1]), Streams(3))
        self.assertEqual(escrow.sale_tier(state), "kept_trade")
        con = CaptureConsole([])
        game.epilogue(state, con)
        self.assertIsNotNone(con.find("kept the trade"))
        self.assertIsNone(con.find("sold well"))

    def test_dirty_cash_over_the_tolerance_also_reclassifies(self):
        state = at_closing()
        state.clean = 30000
        state.shop_stash = {}
        state.dirty = escrow.DIRTY_TOLERANCE + 1
        escrow.diligence_morning(state, CaptureConsole([1, 1]), Streams(3))
        self.assertEqual(escrow.sale_tier(state), "kept_trade")

    def test_the_fire_sale_tier(self):
        # Case 84.9: the chair is still (barely) open; the price is ash.
        state = at_closing(case=84.9, rep=5.0)
        state.clean = 0
        state.dirty = 0
        state.shop_stash = {}
        escrow.diligence_morning(state, CaptureConsole([1, 1]), Streams(3))
        self.assertEqual(escrow.sale_tier(state), "fire")
        con = CaptureConsole([])
        game.epilogue(state, con)
        self.assertIsNotNone(con.find("fire sale"))

    def test_retained_stock_is_priced_at_base_book_value(self):
        state = at_closing()
        state.clean = 1000
        state.dirty = 0
        state.warehouse = {"oregano": 3}
        state.shop_stash = {"mushrooms": 2}
        expected_stock = (3 * data.GOODS["oregano"]["base"]
                          + 2 * data.GOODS["mushrooms"]["base"])
        self.assertEqual(escrow.walkaway_total(state),
                         1000 + expected_stock)


# ══ Whole runs: streams, endings, crash-freedom ═══════════════════

class TestWholeRuns(unittest.TestCase):
    def test_brokers_draws_only_inside_the_branch(self):
        # A sold run must have drawn brokers and nothing else new; a
        # stand-pat run on the same seed must leave all three fresh.
        captured = {}

        def on_night(state, streams):
            captured["streams"] = streams

        for seed in range(60):
            captured.clear()
            state = game.run(seed, forced_sale_bot(seed),
                             on_night=on_night, config=SALE_ON)
            if state.game_over != "sold":
                continue
            streams = captured["streams"]
            for name in ("sitdown", "war"):
                self.assertEqual(getattr(streams, name).getstate(),
                                 random.Random(f"{seed}/{name}").getstate(),
                                 name)
            self.assertNotEqual(
                streams.brokers.getstate(),
                random.Random(f"{seed}/brokers").getstate())
            # The stand-pat control on the same seed: brokers stays fresh.
            captured.clear()
            game.run(seed, GreedyBot(random.Random(seed), verbose=False),
                     on_night=on_night, config=SALE_ON)
            self.assertEqual(
                captured["streams"].brokers.getstate(),
                random.Random(f"{seed}/brokers").getstate())
            return
        self.fail("no sold run found in the seed scan")

    def test_forced_sale_runs_complete_across_seeds(self):
        # Criterion 3, smoke scale (the study runs the full 150).
        endings = set()
        for seed in range(40):
            state = game.run(seed, forced_sale_bot(seed), config=SALE_ON)
            self.assertIsNotNone(state.game_over, f"seed {seed}")
            endings.add(state.game_over)
        self.assertTrue(endings)

    def test_a_sold_run_ends_before_day_30(self):
        for seed in range(60):
            state = game.run(seed, forced_sale_bot(seed), config=SALE_ON)
            if state.game_over == "sold":
                self.assertEqual(
                    state.day,
                    state.sitdown_snapshot.payoff_day + 1
                    + escrow.DILIGENCE_DAYS)
                return
        self.fail("no seed closed a sale in the scan")


# ══ The disposal verb (rev. 7) ════════════════════════════════════

class TestDisposal(unittest.TestCase):
    def test_burning_cash_destroys_and_converts_nothing(self):
        # Two identical nights on one seed; the only difference is the
        # burn amount — clean must come out identical (no conversion),
        # dirty lighter by exactly the burn, the Case untouched.
        def run_burn(amount):
            state = in_escrow()
            state.dirty = 5000
            state.clean = 1000
            con = CaptureConsole([0, amount, 4])
            phases.night(state, {}, _wag(state), con, Streams(3))
            return state, con
        burned, con = run_burn(4800)
        control, _ = run_burn(0)
        self.assertEqual(burned.dirty, 200)
        self.assertEqual(control.dirty, 5000)
        self.assertEqual(burned.clean, control.clean)      # no conversion
        self.assertEqual(len(burned.evidence), len(control.evidence))
        self.assertIsNotNone(con.find("buys nothing, launders nothing"))

    def test_warehouse_cash_must_be_trucked_back_first(self):
        state = in_escrow()
        state.dirty = 300
        state.warehouse = {}
        state.warehouse_cash = 5000
        con = CaptureConsole([0, 5300, 4])     # try to burn more than held
        phases.night(state, {}, _wag(state), con, Streams(3))
        self.assertEqual(state.dirty, 0)       # capped at the till in hand
        self.assertEqual(state.warehouse_cash, 5000)

    def test_the_settle_menu_is_branch_aware(self):
        state = in_escrow()
        state.dirty = 500
        con = CaptureConsole([4])
        phases.night(state, {}, _wag(state), con, Streams(3))
        self.assertIsNotNone(con.find("Burn dirty cash"))
        self.assertIsNone(con.find("Launder dirty cash"))
        self.assertIsNotNone(con.find("nothing washes"))
        plain = new_state()
        plain.dirty = 500
        con2 = CaptureConsole([4])
        phases.night(plain, {}, _wag(plain), con2, Streams(3))
        self.assertIsNotNone(con2.find("Launder dirty cash"))
        self.assertIsNone(con2.find("Burn dirty cash"))

    def test_a_clean_close_is_now_reachable_by_burning(self):
        # night() itself advances the day, so the burn-to-close path
        # lands exactly at fork+4 with no manual clock-winding — and the
        # careful burn keeps the permitted $200 (rev. 8).
        state = at_closing(rep=60.0)
        state.clean = 30000
        state.dirty = 900
        state.shop_stash = {}
        state.day -= 1                          # one diligence night left
        con = CaptureConsole([0, 700, 4])       # burn down to tolerance
        phases.night(state, {}, _wag(state), con, Streams(3))
        self.assertEqual(state.day,
                         escrow.sitdown_day(state) + escrow.DILIGENCE_DAYS)
        self.assertEqual(state.dirty, escrow.DIRTY_TOLERANCE)
        escrow.diligence_morning(state, CaptureConsole([1, 1]), Streams(3))
        self.assertEqual(state.game_over, "sold")
        self.assertEqual(escrow.sale_tier(state), "well")


# ══ The card is one source of truth (rev. 7) ══════════════════════

class TestMarkBreakdown(unittest.TestCase):
    def test_fractional_inputs_display_what_they_compute(self):
        # The review's repro: rep 24.9, Case 61.5 — the old card printed
        # rounded inputs but computed truncated ones.
        state = in_escrow(rep=24.9)
        state.evidence.clear()
        state.add_case(61.5, "seizures", kind="physical")
        card = escrow.build_mark(state)
        self.assertEqual(card.rep_term, 3486)      # round(24.9 * 140)
        self.assertEqual(card.case_term, 2768)     # round(61.5 * 45)
        self.assertEqual(card.final, escrow.BASE_PRICE + card.rep_term
                         + card.upgrade_term - card.case_term
                         - card.war_term - card.incident_term)

    def test_the_rendered_card_shows_the_terms_that_sum(self):
        state = in_escrow(rep=24.9)
        state.evidence.clear()
        state.add_case(61.5, "seizures", kind="physical")
        card = escrow.build_mark(state)
        con = CaptureConsole([1])              # keep the default stash
        escrow.diligence_morning(state, con, Streams(3))
        i = con.find("The broker's card")
        self.assertIsNotNone(i)
        self.assertIn("$3,486", con.lines[i])
        self.assertIn("$2,768", con.lines[i])
        self.assertIn("24.9", con.lines[i])
        self.assertIn("61.5", con.lines[i])
        mark_line = con.find("MARK:")
        self.assertIn(f"${card.final:,}", con.lines[mark_line])

    def test_every_display_path_uses_the_same_view(self):
        state = in_escrow(rep=33.3, case=17.7)
        self.assertEqual(escrow.compute_mark(state),
                         escrow.build_mark(state).final)

    def test_a_negative_subtotal_floors_before_any_deduction(self):
        # Rev. 8 pin: rep 5, Case 84.9, war clause armed, an incident
        # booked — deductions against a negative subtotal must never
        # become credits, and the card must say the floor out loud.
        state = in_escrow(case=84.9, rep=5.0)
        state.rivals["vinnie"].relation = -60.0     # arms the war clause
        state.branch_state.escrow_incidents = 1
        state.branch_state.escrow_discount_pct = 20
        card = escrow.build_mark(state)
        self.assertTrue(card.floored)
        self.assertEqual(card.war_term, 0)
        self.assertEqual(card.incident_term, 0)
        self.assertEqual(card.final, 0)
        self.assertGreaterEqual(card.war_term, 0)
        self.assertGreaterEqual(card.incident_term, 0)
        con = CaptureConsole([1])
        escrow.diligence_morning(state, con, Streams(3))
        self.assertIsNotNone(con.find("the mark floors at $0"))
        self.assertFalse(any("--$" in line for line in con.lines))

    def test_the_card_projects_the_closing_classification(self):
        state = in_escrow()
        state.dirty = 900
        con = CaptureConsole([1])
        escrow.diligence_morning(state, con, Streams(3))
        i = con.find("ledger test")
        self.assertIsNotNone(i)
        self.assertIn("$200 tolerance", con.lines[i])
        self.assertIn("kept the trade", con.lines[i])
        state2 = in_escrow()
        state2.dirty = 0
        state2.shop_stash = {}
        con2 = CaptureConsole([])
        escrow.diligence_morning(state2, con2, Streams(3))
        j = con2.find("ledger test")
        self.assertIn("a clean close", con2.lines[j])


# ══ Safe fallbacks on every ordinary escrow prompt (rev. 7) ═══════

class TestEscrowSafeFallbacks(unittest.TestCase):
    """An exhausted script must never destroy assets through an
    ordinary (non-scene) escrow prompt."""

    def test_exhausted_morning_keeps_the_stash(self):
        state = in_escrow()
        state.shop_stash = {"oregano": 7}
        escrow.diligence_morning(state, CaptureConsole([]), Streams(3))
        self.assertEqual(state.shop_stash, {"oregano": 7})

    def test_exhausted_night_keeps_the_cash(self):
        state = in_escrow()
        state.dirty = 5000
        phases.night(state, {}, _wag(state), CaptureConsole([]), Streams(3))
        self.assertEqual(state.dirty, 5000)

    def test_a_selected_burn_with_no_amount_answer_burns_nothing(self):
        state = in_escrow()
        state.dirty = 5000
        phases.night(state, {}, _wag(state), CaptureConsole([0]), Streams(3))
        self.assertEqual(state.dirty, 5000)    # ask_int default is zero


# ══ The canonical units and the severance machine (rev. 8 compl.) ═

class _FixedBrokers:
    """A stub streams object whose brokers draw a chosen repricing."""

    class _Rng:
        def __init__(self, value):
            self.value = value

        def randint(self, lo, hi):
            return self.value

    def __init__(self, value):
        self.brokers = self._Rng(value)


class TestIntegerPercentageStorage(unittest.TestCase):
    def test_all_sixteen_repricings_store_exactly(self):
        # The review's finding: cut_points / 100 stored 28 as
        # 28.000000000000004. The canonical unit is the integer, so
        # every one of the 16 possible draws must persist bit-exactly —
        # no round(), no isclose(), plain equality on ints.
        for pct in range(escrow.REPRICE_MIN_PCT, escrow.REPRICE_MAX_PCT + 1):
            state = in_escrow(rep=40.0)
            con = CaptureConsole([])
            escrow.record_incident(state, con, _FixedBrokers(pct), "test")
            stored = state.branch_state.escrow_discount_pct
            self.assertIsInstance(stored, int)
            self.assertEqual(stored, pct)
            self.assertIsNotNone(con.find(f"-{pct}% to"), pct)
            restored = save.state_from_dict(save.state_to_dict(state))
            self.assertEqual(restored.branch_state.escrow_discount_pct, pct)
            card = escrow.build_mark(restored)
            self.assertEqual(card.incident_discount_pct, pct)

    def test_legacy_float_discounts_migrate_to_whole_points(self):
        state = in_escrow(rep=40.0)
        state.branch_state.escrow_incidents = 1
        d = save.state_to_dict(state)
        bs = d["branch_state"]
        del bs["escrow_discount_pct"]
        bs["escrow_discount"] = 28.000000000000004 / 100   # the old unit
        restored = save.state_from_dict(d)
        self.assertEqual(restored.branch_state.escrow_discount_pct, 28)
        self.assertIs(type(restored.branch_state.escrow_discount_pct), int)

    def test_malformed_pct_payloads_are_refused_on_load(self):
        # The review's table: float, fractional, negative-as-credit and
        # out-of-domain values must all die at the persistence boundary.
        for bad in (0.28, 29.5, -10, 200, True):
            state = in_escrow(rep=40.0)
            state.branch_state.escrow_incidents = 1
            state.branch_state.escrow_discount_pct = 28
            d = save.state_to_dict(state)
            d["branch_state"]["escrow_discount_pct"] = bad
            with self.assertRaises(ValueError, msg=repr(bad)):
                save.state_from_dict(d)

    def test_the_pct_incident_relationship_is_enforced(self):
        # A repricing with no incident on record…
        state = in_escrow(rep=40.0)
        state.branch_state.escrow_discount_pct = 20
        with self.assertRaises(ValueError):
            validate_branch_state("quiet_sale", state.branch_state)
        # …an incident priced outside the ruled domain…
        state2 = in_escrow(rep=40.0)
        state2.branch_state.escrow_incidents = 1
        state2.branch_state.escrow_discount_pct = 0
        with self.assertRaises(ValueError):
            validate_branch_state("quiet_sale", state2.branch_state)
        # …and a second incident cannot remain in an active sale.
        state3 = in_escrow(rep=40.0)
        state3.branch_state.escrow_incidents = 2
        state3.branch_state.escrow_discount_pct = 28
        d = save.state_to_dict(state3)
        with self.assertRaises(ValueError):
            save.state_from_dict(d)


class TestSeveranceStateMachine(unittest.TestCase):
    """The review's contradiction matrix: every row it exhibited must
    now be refused, at transition and at load alike."""

    def quiet_sale_state(self, outcome, paid, heads):
        bs = BranchState.quiet_sale(diligence_day=2)
        bs.severance_outcome = outcome
        bs.severance_paid = paid
        bs.closing_headcount = heads
        return bs

    def test_the_exhibited_contradictions_are_refused(self):
        rows = [("paid", None, 2),
                ("paid", 600, 0),
                ("declined", 600, 2),
                ("not_applicable", 0, 2),
                ("pending", 0, 2)]
        for outcome, paid, heads in rows:
            with self.assertRaises(ValueError, msg=(outcome, paid, heads)):
                validate_branch_state(
                    "quiet_sale",
                    self.quiet_sale_state(outcome, paid, heads))

    def test_the_legitimate_states_pass(self):
        validate_branch_state("quiet_sale",
                              self.quiet_sale_state("pending", None, None))
        validate_branch_state("quiet_sale",
                              self.quiet_sale_state("paid", 600, 2))
        validate_branch_state("quiet_sale",
                              self.quiet_sale_state("declined", 0, 2))
        validate_branch_state("quiet_sale",
                              self.quiet_sale_state("unaffordable", 0, 3))
        validate_branch_state("quiet_sale",
                              self.quiet_sale_state("not_applicable", 0, 0))

    def test_paid_must_match_the_canonical_rate(self):
        with self.assertRaises(ValueError):
            validate_branch_state("quiet_sale",
                                  self.quiet_sale_state("paid", 500, 2))

    def test_a_sold_run_cannot_stay_pending(self):
        pending = self.quiet_sale_state("pending", None, None)
        validate_branch_state("quiet_sale", pending, game_over=None)
        with self.assertRaises(ValueError):
            validate_branch_state("quiet_sale", pending, game_over="sold")

    def test_a_contradictory_save_is_refused_on_load(self):
        # The review's exact scenario: paid / None / 2 in a v3 payload
        # loaded silently and the epilogue said nothing.
        state = at_closing(rep=40.0)
        escrow.diligence_morning(state, CaptureConsole([1, 1]), Streams(3))
        d = save.state_to_dict(state)
        d["branch_state"]["severance_paid"] = None
        with self.assertRaises(ValueError):
            save.state_from_dict(d)
        d2 = save.state_to_dict(state)
        d2["branch_state"]["severance_outcome"] = "pending"
        d2["branch_state"]["severance_paid"] = None
        d2["branch_state"]["closing_headcount"] = None
        with self.assertRaises(ValueError):        # sold + pending
            save.state_from_dict(d2)


# ══ Persistence ═══════════════════════════════════════════════════

class TestEscrowPersistence(unittest.TestCase):
    def test_mid_escrow_round_trip(self):
        state = in_escrow(case=31.0, rep=24.0)
        state.branch_state.diligence_day = 3
        state.branch_state.escrow_mark = 5000
        state.branch_state.escrow_incidents = 1
        state.branch_state.escrow_discount_pct = 28
        restored = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(restored.branch, "quiet_sale")
        self.assertEqual(restored.branch_state, state.branch_state)

    def test_quiet_sale_constructor_and_dead_fields(self):
        validate_branch_state("quiet_sale",
                              BranchState.quiet_sale(diligence_day=2))
        with self.assertRaises(ValueError):
            validate_branch_state(
                "quiet_sale",
                BranchState(diligence_day=1, points_missed=2))




class TestSaleInsolvency(unittest.TestCase):
    """Rev. 16 item 3: "every active branch" includes the sale — a
    diligence week run on a till this empty ends before the buyer
    signs anything. The narratively-tempting exemption was declined."""

    def _skint(self):
        state = in_escrow()
        state.clean = 0
        state.dirty = 0
        state.shop_stash = {}
        state.shop.ingredients = 0
        state.warehouse = None
        return state

    def test_two_short_empty_nights_end_the_run_mid_diligence(self):
        state = self._skint()
        con = CaptureConsole([])
        escrow.night_insolvency(state, con, payroll_short=True)
        self.assertIsNone(state.game_over)
        self.assertEqual(state.branch_state.insolvent_days, 1)
        self.assertIsNotNone(con.find("won't survive"))
        escrow.night_insolvency(state, con, payroll_short=True)
        self.assertEqual(state.game_over, "broke")
        self.assertIsNotNone(con.find("nothing left to sell him"))

    def test_a_hidden_dollar_resets_the_counter(self):
        state = self._skint()
        con = CaptureConsole([])
        escrow.night_insolvency(state, con, payroll_short=True)
        state.dirty = 50
        escrow.night_insolvency(state, con, payroll_short=True)
        self.assertEqual(state.branch_state.insolvent_days, 0)
        self.assertIsNone(state.game_over)

    def test_insolvent_days_round_trips_and_validates(self):
        state = self._skint()
        escrow.night_insolvency(state, CaptureConsole([]),
                                payroll_short=True)
        d = save.state_to_dict(state)
        restored = save.state_from_dict(d)
        self.assertEqual(restored.branch_state.insolvent_days, 1)
        d["branch_state"]["insolvent_days"] = -1
        with self.assertRaises(ValueError):
            save.state_from_dict(d)


if __name__ == "__main__":
    unittest.main()
