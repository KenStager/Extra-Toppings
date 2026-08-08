"""Invariant tests demanded by the design brief: determinism, save/reload,
shared capacity, laundering bounds, money-stream separation, telegraphed
raids, recoverable failure, and the Carmine credit line."""

import os
import random
import tempfile
import unittest

from extra_toppings import data, market, phases, raids, rivals, routes, save, shop
from extra_toppings.bot import GreedyBot
from extra_toppings.game import run
from extra_toppings.models import new_state
from extra_toppings.rng import Streams
from extra_toppings.ui import BotConsole, ScriptedConsole


def fresh(seed=1):
    rng = random.Random(seed)
    state = new_state()
    market.roll_prices(state, rng)
    return state, rng


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_actions_same_full_state(self):
        dicts = []
        for _ in range(2):
            s = run(9, GreedyBot(random.Random(9)))
            dicts.append(save.state_to_dict(s))
        self.assertEqual(dicts[0], dicts[1])

    def test_save_reload_preserves_simulation_exactly(self):
        def play_days(state, streams, con, n):
            for _ in range(n):
                if state.game_over:
                    break
                plans = phases.morning(state, con, streams)
                report = phases.service(state, plans, con, streams)
                phases.night(state, plans, report, con, streams)
                if state.debt > 0:
                    state.debt = int(state.debt * (1 + data.DEBT_RATE))

        # Play three days, save world + streams + bot-RNG.
        streams = Streams(5)
        con = BotConsole(random.Random(5))
        state = new_state()
        play_days(state, streams, con, 3)
        path = os.path.join(tempfile.mkdtemp(), "save.json")
        save.save_game(state, streams, path)
        bot_rng_state = con.rng.getstate()

        # Branch A: continue in place.
        play_days(state, streams, con, 3)
        result_a = save.state_to_dict(state)

        # Branch B: reload and replay the same three days.
        state_b, streams_b = save.load_game(path)
        con_b = BotConsole(random.Random(0))
        con_b.rng.setstate(bot_rng_state)
        play_days(state_b, streams_b, con_b, 3)
        result_b = save.state_to_dict(state_b)

        self.assertEqual(result_a, result_b)

    def test_world_is_action_independent(self):
        """Same seed, wildly different play -> identical event schedule and
        (absent player market impact) identical prices each day."""
        def world_trace(bot):
            trace = []
            orig_night = phases.night
            def spy_night(state, plans, report, con, streams):
                trace.append((state.day,
                              tuple(sorted(e.spec["id"] for e in state.events)),
                              tuple(state.demand_today for _ in (1,))))
                return orig_night(state, plans, report, con, streams)
            phases.night = spy_night
            try:
                run(77, bot, max_days=8)
            finally:
                phases.night = orig_night
            return trace

        t1 = world_trace(BotConsole(random.Random(1)))
        t2 = world_trace(GreedyBot(random.Random(2)))
        # The event schedule — the world's dice — is identical under any play.
        self.assertEqual([x[:2] for x in t1], [x[:2] for x in t2])
        # Demand DICE are shared too, but computed demand also depends on
        # reputation/policy, which the player owns — so only day 1 (before
        # any divergence) must match exactly.
        self.assertEqual(t1[0], t2[0])


class TestSharedCapacity(unittest.TestCase):
    def _plan(self, load_units):
        state, rng = fresh(2)
        state.delivery_pool = 20                    # plenty of real orders today
        state.shop_stash = {"oregano": 12}          # bulk 2: can fill the wagon
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.aware = True
        # script: district 0, driver Rosa (only driver option order varies) ->
        # pick 0, ride_along False, load N, legit 12 requested
        con = ScriptedConsole([0, 0, False, load_units, 12])
        plan = routes.plan_route(state, con, rng)
        return plan

    def test_full_cargo_leaves_no_room_for_pizzas(self):
        plan = self._plan(12)   # 12 units x bulk 2 = 24 slots = whole wagon
        self.assertEqual(sum(plan["cargo"].values()), 12)
        self.assertEqual(plan["legit"], 0)

    def test_empty_cargo_leaves_full_pizza_capacity(self):
        plan = self._plan(0)
        self.assertEqual(sum(plan["cargo"].values()), 0)
        self.assertEqual(plan["legit"], 12)

    def test_partial_cargo_partial_cover(self):
        plan = self._plan(9)    # 18 slots used, 6 left
        self.assertEqual(plan["legit"], 6)


class TestLaundering(unittest.TestCase):
    def test_ceiling_derives_from_actual_sales(self):
        state, _ = fresh()
        self.assertEqual(shop.believable_ceiling(state, 0), 0)
        self.assertGreater(shop.believable_ceiling(state, 1000),
                           shop.believable_ceiling(state, 100))

    def test_over_ceiling_laundering_creates_evidence(self):
        state, _ = fresh()
        state.dirty = 6000
        ceiling = 1000
        base_case = state.case
        phases._launder(state, ceiling, ScriptedConsole([6000]))
        over_case = state.case - base_case
        state2, _ = fresh()
        state2.dirty = 6000
        phases._launder(state2, ceiling, ScriptedConsole([800]))
        under_case = state2.case
        self.assertGreater(over_case, 5)
        self.assertLess(under_case, 1)
        self.assertTrue(any("register claimed" in f for f in state.case_flags))


class TestMoneySeparation(unittest.TestCase):
    def test_laundering_moves_exactly_what_was_asked(self):
        state, _ = fresh()
        state.dirty, state.clean = 3000, 500
        phases._launder(state, 10000, ScriptedConsole([1200]))
        self.assertEqual((state.clean, state.dirty), (1700, 1800))

    def test_debt_payment_conserves_total_and_prefers_dirty(self):
        state, _ = fresh()
        state.clean, state.dirty, state.debt = 1000, 700, 5000
        phases._pay_debt(state, ScriptedConsole([1500]))
        self.assertEqual(state.dirty, 0)          # dirty spent first
        self.assertEqual(state.clean, 200)
        self.assertEqual(state.debt, 3500)

    def test_restaurant_revenue_is_clean_only(self):
        state, rng = fresh(3)
        state.shop.ingredients = 100
        shop.roll_demand(state, rng)
        dirty_before = state.dirty
        shop.simulate_shift(state, 0, rng)
        self.assertEqual(state.dirty, dirty_before)

    def test_street_sales_are_dirty_only(self):
        state, rng = fresh(4)
        clean_before = state.clean
        driver = next(e for e in state.employees if e.hired and e.driving >= 4)
        driver.aware = True
        plan = {"district": "university", "driver": driver, "ride_along": False,
                "cargo": {"mushrooms": 8}, "legit": 0}
        routes.resolve_route(state, plan, ScriptedConsole(), rng)
        self.assertEqual(state.clean, clean_before)


class TestTelegraphedRaids(unittest.TestCase):
    def test_rival_never_raids_without_prior_warning(self):
        """A fresh decision to raid always sets >= 2 days of visible warning."""
        for seed in range(300):
            state, rng = fresh(seed)
            vinnie = state.rivals["vinnie"]
            vinnie.relation = -90     # maximum grudge, maximum aggression
            vinnie.raid_warning = 0
            rivals.rival_phase(state, ScriptedConsole(), rng)
            self.assertNotEqual(vinnie.raid_warning, 1,
                                "raid must never arrive the night it is decided")

    def test_warning_countdown_passes_through_a_visible_day(self):
        state, _ = fresh(6)
        state.rivals["vinnie"].raid_warning = 3
        state.rivals["sal"].strength = 0          # keep sal quiet
        plans = {"route": None, "raid": None}
        report = {"revenue": 0}
        phases.night(state, plans, report, ScriptedConsole(), Streams(6))
        self.assertEqual(state.rivals["vinnie"].raid_warning, 2)
        self.assertEqual(state.shop.damage_days, 0)   # no raid yet


class TestRecoverableFailure(unittest.TestCase):
    def test_lost_defense_hurts_but_never_ends_the_run(self):
        losses = 0
        for seed in range(40):
            state, rng = fresh(seed)
            state.shop_stash = {"mushrooms": 10}
            state.dirty = 2000
            state.rivals["vinnie"].strength = 95
            state.rivals["vinnie"].raid_warning = 1
            raids.incoming_raid(state, "vinnie",
                                ScriptedConsole([0]), rng)   # always fight
            if state.shop.damage_days > 0:
                losses += 1
                self.assertLessEqual(state.shop.damage_days, 3)
                self.assertGreaterEqual(state.shop_stash["mushrooms"], 5)
                self.assertGreaterEqual(state.dirty, 0)
                self.assertIsNone(state.game_over)
        self.assertGreater(losses, 0, "no defense ever failed in 40 tries")

    def test_aborted_player_raid_is_survivable(self):
        aborts = 0
        for seed in range(60):
            state, rng = fresh(seed)
            crew = [e for e in state.employees[:3]]
            for e in crew:
                e.hired = e.aware = True
            case_before = state.case
            plan = {"rival": "vinnie", "objective": "ledger",
                    "team": list(crew), "armed": False}
            # Always pick "Abort the job" whenever a guard forces a choice.
            raids.run_raid(state, plan, ScriptedConsole([3] * 10), rng)
            if not state.rivals["vinnie"].ledger_stolen:
                aborts += 1
                self.assertIsNone(state.game_over)
                self.assertLessEqual(state.case, case_before + 15)
                for e in crew:
                    self.assertLessEqual(e.injured_days, 5)
        self.assertGreater(aborts, 0)


class TestCarmineCredit(unittest.TestCase):
    def _run_morning(self, state, seed=7):
        # Immediately open for service (option 9 in the morning menu).
        return phases.morning(state, ScriptedConsole([8]), Streams(seed))

    def test_credit_costs_more_than_the_groceries_are_worth(self):
        state, _ = fresh(7)
        state.clean, state.shop.ingredients = 0, 0
        debt_before = state.debt
        self._run_morning(state)
        granted = state.shop.ingredients
        debt_added = state.debt - debt_before
        self.assertGreater(granted, 0)
        self.assertGreater(debt_added,
                           granted * data.INGREDIENT_COST[state.shop.quality])

    def test_credit_does_not_fire_when_solvent(self):
        state, _ = fresh(8)
        state.clean, state.shop.ingredients = 5000, 50
        debt_before = state.debt
        self._run_morning(state, seed=8)
        self.assertEqual(state.debt, debt_before)

    def test_leaning_on_credit_compounds_against_you(self):
        """Ten days of deliberate starvation: debt grows faster than the
        retail value of everything Carmine delivered. No free lunch."""
        state, _ = fresh(9)
        state.clean = 0
        total_groceries_value = 0
        debt_start = state.debt
        for _ in range(10):
            state.shop.ingredients = 0
            state.clean = 0
            before = state.shop.ingredients
            self._run_morning(state, seed=9)
            state.day += 1
            total_groceries_value += (state.shop.ingredients - before) \
                * data.INGREDIENT_COST[state.shop.quality]
            state.debt = int(state.debt * (1 + data.DEBT_RATE))
        self.assertGreater(state.debt - debt_start, total_groceries_value)


if __name__ == "__main__":
    unittest.main()
