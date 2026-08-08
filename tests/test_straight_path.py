"""The Straight Path (P2, design §2.4.1 + rev. 9): the commit scene,
the disposal triangle, temptation offers, counsel's dual use, the
clean-days clock, the siege, insolvency, the day-30 matrix, and the
save round-trip — through the real scene and the real phases."""

import random
import unittest

from extra_toppings import data, game, phases, rivals, save, sitdown, straight
from extra_toppings.config import GameConfig
from extra_toppings.models import SitdownSnapshot, new_state
from extra_toppings.rng import Streams
from extra_toppings.ui import ScriptedConsole

STRAIGHT_ON = GameConfig(fork_enabled=True,
                         enabled_branches=frozenset({"straight"}))


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


def in_branch(payoff_day=13, case=0.0, rep=50.0, stash=None):
    """A state that took the chair through the REAL scene, standing at
    the first branch morning."""
    state = new_state()
    state.debt = 0
    state.debt_paid_day = payoff_day
    state.day = payoff_day + 1
    state.shop.reputation = rep
    if stash is not None:
        state.shop_stash = dict(stash)
    if case:
        state.add_case(case, "prior seizures", kind="physical")
    state.sitdown_snapshot = SitdownSnapshot(
        payoff_day=payoff_day, case_at_lockup=case,
        evidence_count_at_lockup=len(state.evidence))
    sitdown.run_scene(state, CaptureConsole([0, 1]), STRAIGHT_ON)
    if state.branch != "straight":
        raise AssertionError("scene did not enter the Straight Path")
    return state


# ══ Taking the chair ══════════════════════════════════════════════

class TestTakingTheChair(unittest.TestCase):
    def test_commit_sets_branch_state_and_burns_the_book(self):
        state = new_state()
        state.debt = 0
        state.debt_paid_day = 13
        state.day = 14
        state.sitdown_snapshot = SitdownSnapshot(13, 0.0, 0)
        con = CaptureConsole([0, 1])
        sitdown.run_scene(state, con, STRAIGHT_ON)
        self.assertEqual(state.branch, "straight")
        self.assertEqual(state.act, 2)
        self.assertEqual(state.branch_state.disposal_runs_left, 3)
        self.assertIsNone(state.branch_state.last_crime_day)
        self.assertIsNotNone(con.find("the book burns"))
        self.assertIsNotNone(con.find("disposal runs left: 3"))

    def test_declining_the_confirmation_returns_to_the_table(self):
        state = new_state()
        state.debt = 0
        state.debt_paid_day = 13
        state.day = 14
        state.sitdown_snapshot = SitdownSnapshot(13, 0.0, 0)
        con = CaptureConsole([0, 0, 4, 1])   # straight, reconsider, stand pat
        sitdown.run_scene(state, con, STRAIGHT_ON)
        self.assertEqual(state.branch, "stand_pat")

    def test_the_chair_seats_at_any_case(self):
        # §2.1: the Straight Path has no Case gate — the natural play
        # at a burning file.
        state = in_branch(case=90.0)
        self.assertEqual(state.branch, "straight")


# ══ The branch morning ════════════════════════════════════════════

class TestBranchMorning(unittest.TestCase):
    def test_menu_swaps_route_and_raid_for_disposal(self):
        state = in_branch()
        con = CaptureConsole([7])            # straight to service
        phases.morning(state, con, Streams(3))
        self.assertIsNotNone(con.find("Disposal (runs left: 3)"))
        self.assertIsNone(con.find("Plan a night job"))
        self.assertIsNone(con.find("Plan tonight's route"))
        self.assertIsNone(con.find("SUPPLIER:"))

    def test_carmines_nephew_no_longer_fronts_stock(self):
        state = in_branch()
        state.shop.ingredients = 0
        state.clean = 0
        con = CaptureConsole([7])
        phases.morning(state, con, Streams(3))
        self.assertIsNone(con.find("Carmine's nephew"))
        self.assertEqual(state.debt, 0)


# ══ The disposal triangle ═════════════════════════════════════════

class TestFireSale(unittest.TestCase):
    def test_forty_cents_on_the_book_and_the_clock_resets(self):
        state = in_branch(stash={"oregano": 10, "mushrooms": 5})
        state.warehouse = {"hot_honey": 2}
        streams = Streams(3)
        # Goods list alphabetically per stash: mushrooms, oregano, then
        # the warehouse honey.
        con = CaptureConsole([5, 10, 2])     # hand over everything
        did = straight.fire_sale(state, con, streams)
        self.assertTrue(did)
        expected = (10 * int(45 * 0.40) + 5 * int(130 * 0.40)
                    + 2 * int(260 * 0.40))
        self.assertEqual(state.dirty, data.START_DIRTY + expected)
        self.assertEqual(state.total_stock_units(), 0)
        self.assertEqual(state.branch_state.last_crime_day, state.day)
        self.assertEqual(state.rivals["sal"].relation,
                         -10.0 + straight.FIRE_SALE_RELATION)
        self.assertIsNotNone(con.find("Sal's man pays"))

    def test_handing_over_nothing_is_no_meeting_and_no_crime(self):
        state = in_branch(stash={"oregano": 4})
        con = CaptureConsole([0])
        did = straight.fire_sale(state, con, Streams(3))
        self.assertFalse(did)
        self.assertIsNone(state.branch_state.last_crime_day)
        self.assertEqual(state.shop_stash["oregano"], 4)

    def test_one_meeting_a_day_through_the_real_menu(self):
        state = in_branch(stash={"oregano": 8})
        con = CaptureConsole([
            6, 0, 4,     # Disposal -> fire-sale -> hand over 4
            6, 0,        # Disposal -> fire-sale again: refused
            7,           # open for service
        ])
        phases.morning(state, con, Streams(3))
        self.assertIsNotNone(con.find("One meeting a day"))
        self.assertEqual(state.shop_stash.get("oregano", 0), 4)


class TestBurn(unittest.TestCase):
    def test_burning_is_free_of_crime_and_of_value(self):
        state = in_branch(stash={"oregano": 6, "mushrooms": 2})
        dirty_before = state.dirty
        con = CaptureConsole([])
        straight.burn_stock(state, con)
        self.assertEqual(state.total_stock_units(), 0)
        self.assertEqual(state.dirty, dirty_before)
        self.assertIsNone(state.branch_state.last_crime_day)
        self.assertIsNotNone(con.find("Tony watches"))

    def test_warehouse_stock_must_come_home_first(self):
        state = in_branch(stash={})
        state.warehouse = {"oregano": 5}
        con = CaptureConsole([])
        straight.burn_stock(state, con)
        self.assertEqual(state.warehouse["oregano"], 5)
        self.assertIsNotNone(con.find("has to come home"))


class TestDisposalRuns(unittest.TestCase):
    def _plan(self, state, cargo):
        driver = next(e for e in state.employees if e.hired
                      and e.name.startswith("Rosa"))
        driver.aware = True
        return {"district": "university", "driver": driver,
                "ride_along": False, "cargo": dict(cargo), "legit": 0,
                "disposal": True}

    def test_the_run_spends_at_commit_and_resets_the_clock(self):
        state = in_branch(stash={"mushrooms": 6})
        con = CaptureConsole([])
        plan = self._plan(state, {"mushrooms": 6})
        self.assertTrue(phases._commit_route(state, plan, con))
        self.assertEqual(state.branch_state.disposal_runs_left, 2)
        self.assertEqual(state.branch_state.last_crime_day, state.day)
        self.assertIsNotNone(con.find("disposal run"))

    def test_a_scrubbed_plan_spends_nothing(self):
        state = in_branch(stash={"mushrooms": 6})
        plan = self._plan(state, {"mushrooms": 6})
        plan["driver"].injured_days = 2
        self.assertFalse(phases._commit_route(state, plan,
                                              CaptureConsole([])))
        self.assertEqual(state.branch_state.disposal_runs_left, 3)
        self.assertIsNone(state.branch_state.last_crime_day)

    def test_a_pizzas_only_drive_spends_nothing(self):
        state = in_branch(stash={})
        state.delivery_pool = 8
        state.shop.ingredients = 40
        plan = self._plan(state, {})
        plan["legit"] = 4
        self.assertTrue(phases._commit_route(state, plan,
                                             CaptureConsole([])))
        self.assertEqual(state.branch_state.disposal_runs_left, 3)
        self.assertIsNone(state.branch_state.last_crime_day)

    def test_the_haircut_prices_sixty_to_seventyfive_of_board(self):
        # Resolve a solo disposal run and check every sale landed
        # inside the haircut band of the district board price.
        state = in_branch(stash={"mushrooms": 8})
        phases.market.roll_prices(state, random.Random(5))
        streams = Streams(5)
        con = CaptureConsole([])
        plan = self._plan(state, {"mushrooms": 8})
        phases._commit_route(state, plan, con)
        board = state.prices["university"]["mushrooms"]
        report = None
        for _ in range(20):                      # find a selling night
            trial = dict(plan, cargo={"mushrooms": 8})
            report = phases.routes.resolve_route(state, trial, con,
                                                 streams.routes)
            if report["sold"]:
                break
        self.assertIsNotNone(report)
        self.assertTrue(report["sold"])
        per_unit = report["cash"] / report["sold"]
        self.assertLessEqual(per_unit, board * 0.75 + 1)
        self.assertGreaterEqual(per_unit, board * 0.60 - 1)

    def test_spent_runs_refuse_through_the_real_menu(self):
        state = in_branch(stash={"oregano": 4})
        state.branch_state.disposal_runs_left = 0
        con = CaptureConsole([6, 1, 7])
        phases.morning(state, con, Streams(3))
        self.assertIsNotNone(con.find("The three runs are spent"))


# ══ Temptation offers ═════════════════════════════════════════════

class TestTemptation(unittest.TestCase):
    def _offer_state(self):
        state = in_branch(stash={"mushrooms": 6})
        offer = None
        for probe in range(200):
            offer = straight.temptation_offer(state, random.Random(probe))
            if offer:
                break
        self.assertIsNotNone(offer)
        return state, offer

    def test_the_card_names_the_distinction(self):
        state, offer = self._offer_state()
        con = CaptureConsole([])
        straight.temptation_card(state, offer, con)
        self.assertIsNotNone(con.find("new trade at full margin, not "
                                      "disposal"))
        self.assertIsNotNone(con.find("spends no disposal run"))

    def test_accepting_is_ordinary_crime_at_full_margin(self):
        state, offer = self._offer_state()
        dirty_before = state.dirty
        runs_before = state.branch_state.disposal_runs_left
        con = CaptureConsole([4])
        straight.take_temptation(state, offer, con, Streams(3))
        self.assertEqual(state.dirty, dirty_before + 4 * offer["price"])
        self.assertEqual(state.branch_state.last_crime_day, state.day)
        self.assertEqual(state.branch_state.disposal_runs_left, runs_before)
        self.assertGreaterEqual(offer["price"],
                                int(data.GOODS[offer["good"]]["base"] * 1.4))

    def test_declining_keeps_the_clock(self):
        state, offer = self._offer_state()
        con = CaptureConsole([0])
        straight.take_temptation(state, offer, con, Streams(3))
        self.assertIsNone(state.branch_state.last_crime_day)
        self.assertEqual(state.shop_stash["mushrooms"], 6)


# ══ Counsel's dual use and the wash ═══════════════════════════════

class TestCounselDualUse(unittest.TestCase):
    def test_retained_counsel_caps_the_wash_at_the_ceiling(self):
        state = in_branch()
        state.branch_state.counsel_retained = True
        state.dirty = 5000
        con = CaptureConsole([5000])         # ask for everything
        washed = phases._launder(state, 800, con)
        self.assertEqual(washed, 800)        # capped at the ceiling
        self.assertTrue(all(r.kind != "paper" or r.magnitude <= 0.5
                            for r in state.evidence))
        self.assertIsNone(state.branch_state.last_crime_day)

    def test_without_counsel_the_over_ceiling_wash_is_a_crime(self):
        state = in_branch()
        state.dirty = 5000
        con = CaptureConsole([5000])
        washed = phases._launder(state, 800, con)
        self.assertEqual(washed, 5000)
        self.assertEqual(state.branch_state.last_crime_day, state.day)
        self.assertIsNotNone(con.find("clean days start over"))

    def test_counsel_with_a_spent_ceiling_says_so(self):
        state = in_branch()
        state.branch_state.counsel_retained = True
        state.dirty = 5000
        con = CaptureConsole([])
        washed = phases._launder(state, 0, con)
        self.assertEqual(washed, 0)
        self.assertIsNotNone(con.find("the ceiling is spent"))

    def test_retain_and_dismiss_through_the_real_improvements_menu(self):
        state = in_branch()
        con = CaptureConsole([5, 0, 6, 7])   # improvements, retain, back
        phases.morning(state, con, Streams(3))
        self.assertTrue(state.branch_state.counsel_retained)
        self.assertIsNotNone(con.find("Retain counsel"))
        con2 = CaptureConsole([5, 0, 6, 7])  # improvements, dismiss, back
        phases.morning(state, con2, Streams(3))
        self.assertFalse(state.branch_state.counsel_retained)
        self.assertIsNotNone(con2.find("Dismiss counsel"))


# ══ Advertising ═══════════════════════════════════════════════════

class TestAdvertising(unittest.TestCase):
    def test_a_campaign_lifts_demand_and_reputation(self):
        state = in_branch()
        state.clean = 2000
        con = CaptureConsole([])
        phases.shop.recompute_demand(state)
        before = state.demand_today
        straight.advertise(state, con)
        self.assertEqual(state.clean, 2000 - straight.AD_COST)
        self.assertEqual(state.branch_state.ad_days_left, straight.AD_DAYS)
        self.assertGreater(state.demand_today, before)
        rep_before = state.shop.reputation
        straight.night_tick(state, con, payroll_short=False)
        self.assertEqual(state.shop.reputation,
                         rep_before + straight.AD_REP_PER_NIGHT)
        self.assertEqual(state.branch_state.ad_days_left,
                         straight.AD_DAYS - 1)

    def test_no_campaign_without_clean_cash(self):
        state = in_branch()
        state.clean = straight.AD_COST - 1
        straight.advertise(state, CaptureConsole([]))
        self.assertEqual(state.branch_state.ad_days_left, 0)
        self.assertEqual(state.clean, straight.AD_COST - 1)


# ══ The branch night ══════════════════════════════════════════════

class TestBranchNight(unittest.TestCase):
    def test_settle_menu_replaces_carmine(self):
        state = in_branch()
        con = CaptureConsole([4])            # lock up immediately
        phases.night(state, {"route": None, "raid": None}, {}, con,
                     Streams(3), STRAIGHT_ON)
        self.assertIsNotNone(con.find("Settle with a witness"))
        self.assertIsNone(con.find("Pay Carmine"))

    def test_two_insolvent_nights_end_the_run(self):
        state = in_branch(stash={})
        state.dirty = 0
        con = CaptureConsole([])
        straight.night_tick(state, con, payroll_short=True)
        self.assertEqual(state.branch_state.insolvent_days, 1)
        self.assertIsNone(state.game_over)
        straight.night_tick(state, con, payroll_short=True)
        self.assertEqual(state.game_over, "broke")
        self.assertIsNotNone(con.find("clean life has a rent too"))

    def test_a_solvent_night_resets_the_counter(self):
        state = in_branch(stash={})
        state.dirty = 0
        con = CaptureConsole([])
        straight.night_tick(state, con, payroll_short=True)
        self.assertEqual(state.branch_state.insolvent_days, 1)
        straight.night_tick(state, con, payroll_short=False)
        self.assertEqual(state.branch_state.insolvent_days, 0)

    def test_stock_or_hidden_cash_defers_insolvency(self):
        state = in_branch(stash={"oregano": 1})
        con = CaptureConsole([])
        straight.night_tick(state, con, payroll_short=True)
        self.assertEqual(state.branch_state.insolvent_days, 0)

    def test_the_exit_readout_reads_every_term(self):
        state = in_branch()
        con = CaptureConsole([])
        straight.exit_readout(state, con)
        i = con.find("Exit readout:")
        self.assertIsNotNone(i)
        line = con.lines[i]
        for fragment in ("stock", "dirty", "Case", "rep", "witnesses",
                         "clean days"):
            self.assertIn(fragment, line)


# ══ The siege ═════════════════════════════════════════════════════

class TestTheSiege(unittest.TestCase):
    def test_rivals_smell_retreat_when_the_stash_is_empty(self):
        # Same dice: a roll that Act I shrugs off triggers an action
        # under the branch's ×1.5 aggression (rev. 9 item 13).
        base_chance = data.RIVALS["vinnie"]["aggression"] * 0.5 + 0.06
        seed = next(k for k in range(1000)
                    if base_chance < random.Random(k).random()
                    <= base_chance * straight.RETREAT_AGGRESSION)

        def probe(branch):
            state = in_branch(stash={}) if branch else new_state()
            state.rivals["sal"].strength = 0     # only Vinnie rolls
            state.warehouse = None
            con = CaptureConsole([])
            rivals.rival_phase(state, con, random.Random(seed))
            return len(con.lines)

        self.assertEqual(probe(branch=False), 0)
        self.assertGreater(probe(branch=True), 0)

    def test_a_search_spooks_a_witness_not_a_stash(self):
        state = in_branch()
        bee = next(e for e in state.employees if "Bee" in e.name)
        bee.hired = True
        morale = bee.morale
        con = CaptureConsole([])
        straight.search_spook(state, con)
        self.assertEqual(bee.morale, morale - 1)
        self.assertIsNotNone(con.find("rechecks the till"))


# ══ The day-30 matrix ═════════════════════════════════════════════

def _exit_ready(state):
    """Meet every goal term."""
    state.shop_stash = {}
    state.warehouse = None
    state.dirty = 150
    state.warehouse_cash = 0
    state.shop.reputation = 60.0
    for r in state.rivals.values():
        r.raid_warning = 0
        r.relation = -10.0


class TestTheMatrix(unittest.TestCase):
    def test_the_earned_exit(self):
        state = in_branch(case=30.0)
        _exit_ready(state)
        self.assertEqual(straight.grade(state), "straight_exit")

    def test_almost_out_is_the_case_alone(self):
        state = in_branch(case=60.0)
        _exit_ready(state)
        self.assertEqual(straight.grade(state), "almost_out")

    def test_half_measures_names_every_failed_term(self):
        state = in_branch(case=30.0, stash={"oregano": 3})
        state.dirty = 900
        state.shop.reputation = 20.0
        state.rivals["vinnie"].relation = -80.0
        e = next(x for x in state.employees if x.key == "e3")
        e.aware = True
        e.hired = False
        e.morale = 2
        state.branch_state.last_crime_day = 28
        self.assertEqual(straight.grade(state), "half_measures")
        terms = straight.failed_terms(state, as_of=data.DEBT_DUE_DAY)
        joined = " ".join(terms)
        for fragment in ("contraband", "unlaundered", "reputation",
                         "hostile unsettled witness", "open feud",
                         "clean days 2 of 5"):
            self.assertIn(fragment, joined)

    def test_the_clean_days_boundary(self):
        # A crime on day 25 still leaves five clean days; day 26 does
        # not (§2.4.1's liquidation theorem).
        state = in_branch()
        _exit_ready(state)
        state.branch_state.last_crime_day = 25
        self.assertEqual(straight.grade(state), "straight_exit")
        state.branch_state.last_crime_day = 26
        self.assertEqual(straight.grade(state), "half_measures")

    def test_the_r5_boundary_fork_can_still_win(self):
        # Payoff day 25 → sit-down day 26 → five clean days exactly.
        state = in_branch(payoff_day=25)
        _exit_ready(state)
        self.assertEqual(straight.grade(state), "straight_exit")

    def test_epilogue_names_the_failed_terms(self):
        state = in_branch(case=30.0, stash={"oregano": 3})
        state.shop.reputation = 20.0
        state.game_over = straight.grade(state)
        con = CaptureConsole([])
        game.epilogue(state, con)
        self.assertIsNotNone(con.find("Half Measures"))
        self.assertIsNotNone(con.find("contraband still on hand"))
        self.assertIsNotNone(con.find("reputation 20"))

    def test_arrest_beats_the_matrix(self):
        # §2.5 precedence 1: the latch, not the grade.
        state = in_branch(case=95.0)
        _exit_ready(state)
        state.add_case(10, "the last straw", kind="physical")
        self.assertEqual(state.game_over, "arrested")


# ══ Persistence mid-branch ════════════════════════════════════════

class TestMidBranchSave(unittest.TestCase):
    def test_round_trip_preserves_the_whole_exit(self):
        state = in_branch(stash={"oregano": 10})
        streams = Streams(3)
        con = CaptureConsole([10])
        straight.fire_sale(state, con, streams)
        state.branch_state.counsel_retained = True
        loaded = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(loaded.branch, "straight")
        self.assertEqual(loaded.branch_state, state.branch_state)
        self.assertEqual(loaded.branch_state.last_crime_day, state.day)

    def test_exhausted_scripts_destroy_nothing_in_the_new_menus(self):
        # Every new branch prompt under an exhausted script: the
        # morning ends, the disposal menu backs out, the fire-sale
        # sells zero (rev. 7's safe-fallback contract).
        state = in_branch(stash={"oregano": 10})
        con = CaptureConsole([6, 0])   # disposal -> fire-sale, then dry
        phases.morning(state, con, Streams(3))
        self.assertEqual(state.shop_stash["oregano"], 10)
        self.assertEqual(state.dirty, data.START_DIRTY)
        self.assertIsNone(state.branch_state.last_crime_day)
        self.assertEqual(state.branch_state.disposal_runs_left, 3)


if __name__ == "__main__":
    unittest.main()
