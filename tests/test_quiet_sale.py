"""The Quiet Sale (P1b, design §2.4.4): the escrow week through the
real loop — the scene commit, the itemized mark, incidents and
collapse, laundering off, the closing's tiers and reclassification, and
the brokers stream drawn only after the chair is actually taken."""

import random
import unittest

from extra_toppings import data, escrow, game, phases, save, sitdown
from extra_toppings.bot import GreedyBot
from extra_toppings.config import GameConfig
from extra_toppings.models import (BranchState, SitdownSnapshot, new_state,
                                   validate_branch_state)
from extra_toppings.rng import Streams
from extra_toppings.ui import ScriptedConsole

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
        state.rivals["vinnie"].raid_warning = 2
        self.assertEqual(escrow.compute_mark(state), int(6465 * 0.8))

    def test_incident_discounts_compound_into_the_mark(self):
        state = in_escrow(case=31.0, rep=24.0)
        state.shop.upgrades = {"walk_in", "guard"}
        state.branch_state.escrow_discount = 0.15
        self.assertEqual(escrow.compute_mark(state), int(6465 * 0.85))

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
        state = in_escrow()
        state.dirty = 5000
        evidence_before = len(state.evidence)
        con = CaptureConsole([0, 4])           # Launder → Lock up
        phases.night(state, {}, {}, con, Streams(3))
        self.assertIsNotNone(con.find("books are being read"))
        self.assertEqual(state.dirty, 5000)
        self.assertEqual(len(state.evidence), evidence_before)

    def test_contraband_at_the_day_one_walkthrough_is_an_incident(self):
        state = in_escrow(rep=40.0)
        state.shop_stash = {"mushrooms": 10}
        state.branch_state.escrow_mark = escrow.compute_mark(state)
        before = state.branch_state.escrow_mark
        con = CaptureConsole([])
        escrow.walkthrough(state, con, Streams(3))   # day 1: he walks, always
        self.assertEqual(state.branch_state.escrow_incidents, 1)
        self.assertGreaterEqual(state.branch_state.escrow_discount, 0.10)
        self.assertLessEqual(state.branch_state.escrow_discount, 0.25)
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
            phases.night(state, {}, {}, con, Streams(seed))
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
        self.assertIsNotNone(con.find("hear it from you"))

    def test_walking_away_reverts_and_the_run_continues(self):
        state = at_closing()
        rep_before = state.shop.reputation
        con = CaptureConsole([0])              # tear it up
        escrow.diligence_morning(state, con, Streams(3))
        self.assertIsNone(state.game_over)
        self.assertEqual(state.branch, "stand_pat")
        self.assertEqual(state.shop.reputation, rep_before)  # no collapse tax

    def test_cheap_severance_costs_morale_and_is_remembered(self):
        state = at_closing()
        con = CaptureConsole([1, 0])           # sign; nothing
        escrow.diligence_morning(state, con, Streams(3))
        self.assertIsNotNone(con.find("envelope that never came"))
        for e in state.hired():
            self.assertLessEqual(e.morale, 4)

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


# ══ Persistence ═══════════════════════════════════════════════════

class TestEscrowPersistence(unittest.TestCase):
    def test_mid_escrow_round_trip(self):
        state = in_escrow(case=31.0, rep=24.0)
        state.branch_state.diligence_day = 3
        state.branch_state.escrow_mark = 5000
        state.branch_state.escrow_incidents = 1
        state.branch_state.escrow_discount = 0.18
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


if __name__ == "__main__":
    unittest.main()
