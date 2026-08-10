"""Invariant tests demanded by the design brief: determinism, save/reload,
shared capacity, laundering bounds, money-stream separation, telegraphed
raids, recoverable failure, and the Carmine credit line."""

import os
import random
import tempfile
import unittest

from extra_toppings import models, data, market, phases, raids, rivals, routes, save, shop
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
            def spy_night(state, plans, report, con, streams, *args, **kwargs):
                trace.append((state.day,
                              tuple(sorted(e.spec["id"] for e in state.events)),
                              tuple(state.demand_today for _ in (1,))))
                return orig_night(state, plans, report, con, streams,
                                  *args, **kwargs)
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


class TestRevision18Inventory(unittest.TestCase):
    """Rev. 18 items 1-2: the manifest is the route's CANONICAL
    inventory (strict parsing, validation before mutation, honest
    revise bounds) and storage has one capacity authority."""

    def test_malformed_plan_types_are_refused_not_coerced(self):
        for bad in (True, 1.5, "3"):
            with self.assertRaises(ValueError):
                routes.RouteManifest.of_plan(
                    {"cargo": {}, "legit": bad})
        with self.assertRaises(ValueError):
            routes.RouteManifest.of_plan(
                {"cargo": {"oregano": 1.5}, "legit": 0})

    def test_an_illegal_commit_mutates_nothing(self):
        # The reviewer's repro: a 25-space plan committed - stash
        # deducted, an ingredient burned - before resolution raised.
        # Commit now validates FIRST; refusal leaves zero footprint.
        state, _rng = fresh(2)
        state.shop_stash = {"oregano": 12}
        state.shop.ingredients = 30
        state.delivery_pool = 20
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.aware = True
        plan = {"district": "university", "driver": rosa,
                "ride_along": False, "legit": 1,
                "cargo": {"oregano": 12}, "origin_shop": models.HOME_SHOP_KEY}          # 25 space in 24
        con = ScriptedConsole([])
        with self.assertRaises(ValueError):
            phases._commit_route(state, plan, con)
        self.assertEqual(state.shop_stash, {"oregano": 12})
        self.assertEqual(state.shop.ingredients, 30)

    def test_revising_cannot_offer_more_than_the_stash_owns(self):
        # The reviewer's repro: 8 in the stash, load 8, revise - 12
        # offered. Planned goods never leave the stash, so the stash
        # is the ceiling: min(have, loaded + free // space).
        state, rng = fresh(2)
        state.delivery_pool = 0
        state.shop_stash = {"oregano": 8}
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.aware = True
        con = ScriptedConsole([0, 0, False, 8, 0, 12, 1])
        plan = routes.plan_route(state, con, rng,
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))
        self.assertEqual(plan["cargo"], {"oregano": 8})

    def test_the_plan_is_typed_and_carries_one_manifest(self):
        state, rng = fresh(2)
        state.delivery_pool = 10
        state.shop_stash = {"oregano": 4}
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.aware = True
        plan = routes.plan_route(state, ScriptedConsole([0, 0, False, 2, 4]),
                                 rng,
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))
        self.assertIsInstance(plan, routes.RoutePlan)
        self.assertIs(plan["cargo"], plan.manifest.cargo)
        self.assertEqual(plan["legit"], plan.manifest.legit)

    def test_the_warehouse_cap_binds_the_transfer(self):
        # The reviewer's repro: one more oregano into a warehouse at
        # 200/200 landed 202/200. The authority refuses whole.
        from extra_toppings import models
        state, _rng = fresh(2)
        state.warehouse = {"mushrooms": 200}       # exactly at cap
        state.shop_stash = {"oregano": 1}
        with self.assertRaises(ValueError):
            models.move_goods(state, "shop", "warehouse", "oregano", 1)
        self.assertEqual(state.shop_stash, {"oregano": 1})
        self.assertEqual(state.warehouse, {"mushrooms": 200})
        self.assertEqual(
            models.units_that_fit(state, "warehouse", "oregano"), 0)

    def test_storage_over_cap_is_refused_at_persistence(self):
        state, _rng = fresh(2)
        state.warehouse = {"mushrooms": 200}
        d = save.state_to_dict(state)
        d["warehouse"]["mushrooms"] = 202
        with self.assertRaises(ValueError):
            save.state_from_dict(d)
        d["warehouse"]["mushrooms"] = 200
        d["shops"][0]["stash"] = {"oregano": -1}
        with self.assertRaises(ValueError):
            save.state_from_dict(d)


class TestRevision19Storage(unittest.TestCase):
    """Rev. 19 items 1-2: the storage authority is SAFE (one shared
    inventory-map validator, explicit locations) and the historical
    ledgers bind to the actual mechanical domains."""

    def test_the_authority_refuses_impossible_inventory(self):
        from extra_toppings import models
        state, _rng = fresh(2)
        state.warehouse = {}
        state.shop_stash = {"oregano": 3}
        for bad_units in (True, 1.5, -1):
            with self.assertRaises(ValueError):
                models.move_goods(state, "shop", "warehouse",
                                  "oregano", bad_units)
        with self.assertRaises(ValueError):
            models.move_goods(state, "bogus", "warehouse", "oregano", 1)
        with self.assertRaises(ValueError):
            models.move_goods(state, "shop", "bogus", "oregano", 1)
        with self.assertRaises(ValueError):
            models.place_haul(state, {"oregano": True}, state.shop.key)
        with self.assertRaises(ValueError):
            models.place_haul(state, {"oregano": 1.5}, state.shop.key)
        with self.assertRaises(ValueError):
            models.place_haul(state, {"oregano": -2}, state.shop.key)
        with self.assertRaises(ValueError):
            models.space_used({"oregano": -2})
        self.assertEqual(state.shop_stash, {"oregano": 3})
        self.assertEqual(state.warehouse, {})

    def test_rendering_consumes_the_one_arithmetic(self):
        with self.assertRaises(ValueError):
            routes.inventory_lines("The back room", {"oregano": -2}, 40)

    def test_attempt_records_bind_to_the_planning_domains(self):
        from extra_toppings.models import RaidAttemptRecord
        with self.assertRaises(ValueError):
            RaidAttemptRecord(day=15, rival="sal", outcome="succeeded",
                              crew=100, damage_h=0)
        with self.assertRaises(ValueError):
            RaidAttemptRecord(day=15, rival="sal", outcome="succeeded",
                              crew=1, damage_h=9999)
        RaidAttemptRecord(day=15, rival="sal", outcome="succeeded",
                          crew=3, damage_h=1200)     # the real ceiling

    def test_route_records_bind_to_the_mechanical_domains(self):
        from extra_toppings.models import RouteExecutionRecord
        ok = {"day": 15, "district": "old_harbor", "heat_band": "cool",
              "capacity_mult": 1.0, "units_sold": 5,
              "corner_damage_h": 0, "contested": False,
              "origin_shop": models.HOME_SHOP_KEY}
        RouteExecutionRecord(**ok)
        for change in ({"heat_band": "cool", "capacity_mult": 0.5},
                       {"heat_band": "amber", "capacity_mult": 1.0},
                       {"heat_band": "red", "capacity_mult": 0.5},
                       {"units_sold": 999},
                       {"district": "university", "contested": True},
                       {"contested": True, "corner_damage_h": 9999}):
            with self.assertRaises(ValueError):
                RouteExecutionRecord(**{**ok, **change})

    def test_chronology_binds_at_persistence(self):
        from extra_toppings.models import RaidAttemptRecord
        state, _rng = fresh(2)
        state.day = 10
        state.raid_log = [RaidAttemptRecord(
            day=20, rival="sal", outcome="failed", crew=1, damage_h=0)]
        with self.assertRaises(ValueError):
            save.state_to_dict(state) and save.state_from_dict(
                save.state_to_dict(state))
        state.day = 25
        state.raid_log = [
            RaidAttemptRecord(day=20, rival="sal", outcome="failed",
                              crew=1, damage_h=0),
            RaidAttemptRecord(day=18, rival="sal", outcome="failed",
                              crew=1, damage_h=0)]
        with self.assertRaises(ValueError):
            save.state_from_dict(save.state_to_dict(state))


class TestRevision20Storage(unittest.TestCase):
    """Rev. 20 item 1: storage is transactionally safe — both
    locations preflighted, complete allocation before one commit,
    every refusal leaving every stash byte-identical."""

    def test_an_invalid_source_refuses_the_move_whole(self):
        from extra_toppings import models
        state, _rng = fresh(2)
        state.warehouse = {}
        for bad_source in ({"oregano": True}, {"oregano": 1.5},
                           {"fake": 3}):
            state.shop_stash = dict(bad_source)
            frozen = dict(state.shop_stash)
            with self.assertRaises(ValueError):
                models.move_goods(state, "shop", "warehouse",
                                  "oregano", 1)
            self.assertEqual(state.shop_stash, frozen)
            self.assertEqual(state.warehouse, {})

    def test_place_haul_never_leaves_a_partial_placement(self):
        # The reviewer's repro: 40 mushrooms landed in the shop, THEN
        # the invalid warehouse was discovered — the partial mutation
        # stayed. Preflight-then-commit refuses with zero footprint.
        from extra_toppings import models
        state, _rng = fresh(2)
        state.shop_stash = {}
        state.warehouse = {"oregano": 1.5}          # invalid
        with self.assertRaises(ValueError):
            models.place_haul(state, {"mushrooms": 60}, state.shop.key)
        self.assertEqual(state.shop_stash, {})
        self.assertEqual(state.warehouse, {"oregano": 1.5})

    def test_place_haul_refuses_an_over_cap_warehouse(self):
        from extra_toppings import models
        state, _rng = fresh(2)
        state.shop_stash = {}
        state.warehouse = {"mushrooms": 250}        # already over cap
        with self.assertRaises(ValueError):
            models.place_haul(state, {"mushrooms": 5}, state.shop.key)
        self.assertEqual(state.shop_stash, {})
        self.assertEqual(state.warehouse, {"mushrooms": 250})


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
        plan = routes.plan_route(state, con, rng,
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))
        return plan

    def test_full_cargo_leaves_no_room_for_pizzas(self):
        plan = self._plan(12)   # 12 units x bulk 2 = 24 slots = whole wagon
        self.assertEqual(sum(plan["cargo"].values()), 12)
        self.assertEqual(plan["legit"], 0)

    def test_empty_cargo_frees_the_slots_for_pizzas(self):
        plan = self._plan(0)
        self.assertEqual(sum(plan["cargo"].values()), 0)
        self.assertEqual(plan["legit"], 12)     # the 12 is the REQUEST

    def test_partial_cargo_partial_cover(self):
        plan = self._plan(9)    # 18 slots used, 6 left
        self.assertEqual(plan["legit"], 6)

    def test_a_pizza_only_route_loads_the_whole_wagon(self):
        # Rev. 17 item 1: the unexplained 12-pizza cap is gone — 24
        # real orders, ingredients and slots load 24.
        state, rng = fresh(2)
        state.delivery_pool = 30
        state.shop.ingredients = 30
        state.shop_stash = {}
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.aware = True
        con = ScriptedConsole([0, 0, False, 24])
        plan = routes.plan_route(state, con, rng,
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))
        self.assertEqual(plan["legit"], 24)

    def test_an_over_capacity_manifest_is_refused_at_resolution(self):
        # Rev. 17 item 1: resolution refuses what planning should
        # never have produced — unchecked dictionaries ran 52-slot
        # loads through the 24-slot wagon.
        state, rng = fresh(2)
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.aware = True
        plan = {"district": "university", "driver": rosa,
                "ride_along": False, "legit": 10,
                "cargo": {"oregano": 12, "mushrooms": 10, "hot_honey": 8}, "origin_shop": models.HOME_SHOP_KEY}
        with self.assertRaises(ValueError):
            routes.resolve_route(state, plan, ScriptedConsole([]), rng)

    def test_the_manifest_counts_bulk_not_units(self):
        m = routes.RouteManifest(cargo={"oregano": 12})   # bulk 2 each
        self.assertEqual(m.bulk_used, 24)
        self.assertEqual(m.free, 0)
        m.legit = 1
        with self.assertRaises(ValueError):
            m.validate()


class TestLaundering(unittest.TestCase):
    def test_ceiling_derives_from_actual_sales(self):
        state, _ = fresh()
        self.assertEqual(shop.believable_ceiling(state, state.shop, 0), 0)
        self.assertGreater(shop.believable_ceiling(state, state.shop, 1000),
                           shop.believable_ceiling(state, state.shop, 100))

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
        shop.simulate_shift(state, state.shop, 0, rng)
        self.assertEqual(state.dirty, dirty_before)

    def test_street_sales_are_dirty_only(self):
        state, rng = fresh(4)
        clean_before = state.clean
        driver = next(e for e in state.employees if e.hired and e.driving >= 4)
        driver.aware = True
        plan = {"district": "university", "driver": driver, "ride_along": False,
                "cargo": {"mushrooms": 8}, "legit": 0, "origin_shop": models.HOME_SHOP_KEY}
        routes.resolve_route(state, plan, ScriptedConsole(), rng)
        self.assertEqual(state.clean, clean_before)


class TestTelegraphedRaids(unittest.TestCase):
    def test_rival_never_raids_without_prior_warning(self):
        """A fresh decision to raid always sets >= 2 days of visible warning."""
        for seed in range(300):
            state, rng = fresh(seed)
            vinnie = state.rivals["vinnie"]
            vinnie.relation = -90     # maximum grudge, maximum aggression
            vinnie.warning = None
            rivals.rival_phase(state, ScriptedConsole(), rng)
            self.assertNotEqual(vinnie.raid_warning, 1,
                                "raid must never arrive the night it is decided")

    def test_warning_countdown_passes_through_a_visible_day(self):
        state, _ = fresh(6)
        state.rivals["vinnie"].warning = models.RaidWarning(3, models.HOME_SHOP_KEY)
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
            state.rivals["vinnie"].warning = models.RaidWarning(1, models.HOME_SHOP_KEY)
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
                    "team": list(crew), "armed": False, "return_shop": models.HOME_SHOP_KEY}
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
