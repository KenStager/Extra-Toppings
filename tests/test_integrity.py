"""System-integrity tests from the post-merge review: the chunked-laundering
exploit, phantom cover orders, route revenue outside the ledger, assignment
double-booking, and permanent coupon damage."""

import random
import unittest

from extra_toppings import (market, models, phases, raids, rivals,
                            routes, shop)
from extra_toppings.models import new_state
from extra_toppings.rng import Streams
from extra_toppings.ui import ScriptedConsole

def _wag(state, **report):
    """Every direct `night` call needs the assignment authority the
    service phase would have opened (P4b.1a). An UNSPENT one is the
    honest fixture here: these tests do not run service, so no wagon
    departed."""
    return {**report, "wagons": phases.WagonNight(state)}


def fresh(seed=1):
    rng = random.Random(seed)
    state = new_state()
    market.roll_prices(state, rng)
    return state, rng


def run_night(state, seed, script):
    plans = {"routes": {}, "raid": None}
    report = {"revenue": 0}
    # Keep rivals quiet so the only case movement comes from the register.
    for r in state.rivals.values():
        r.strength = 0
    phases.night(state, plans, _wag(state, **report), ScriptedConsole(script), Streams(seed))


class TestChunkedLaundering(unittest.TestCase):
    def test_chunking_the_wash_buys_nothing(self):
        """Five $1,000 chunks vs one $5,000 lump against a ~$1,000 ceiling
        must generate at least as much evidence — the allowance is nightly."""
        lump, _ = fresh(11)
        lump.dirty = 6000
        lump.clean = 10000                     # payroll noise off the books
        lump.legit_revenue_today = 800         # ceiling = 800 * 1.25 = 1000
        run_night(lump, 11, [0, 5000, 4])
        lump_case = lump.case

        chunk, _ = fresh(11)
        chunk.dirty = 6000
        chunk.clean = 10000
        chunk.legit_revenue_today = 800
        run_night(chunk, 11, [0, 1000, 0, 1000, 0, 1000, 0, 1000, 0, 1000, 4])
        chunk_case = chunk.case

        self.assertEqual(lump.total_laundered, chunk.total_laundered)
        self.assertGreaterEqual(chunk_case, lump_case - 0.6,
                                "chunking must not reduce evidence")
        self.assertGreater(chunk_case, 5, "over-ceiling chunks must be evidence")


class TestCompleteLegitLedger(unittest.TestCase):
    def test_route_pizza_revenue_feeds_the_ceiling(self):
        state, rng = fresh(12)
        state.delivery_pool = 10
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        before = state.legit_revenue_today
        plan = {"district": "university", "driver": rosa, "ride_along": False,
                "cargo": {}, "legit": 8, "origin_shop": models.HOME_SHOP_KEY,
                "wagon_key": models.HOME_WAGON_KEY}
        routes.resolve_route(state, plan, ScriptedConsole(), rng)
        self.assertGreater(state.legit_revenue_today, before)
        self.assertGreater(shop.believable_ceiling(state, state.shop, state.legit_revenue_today),
                           shop.believable_ceiling(state, state.shop, before))


class TestRealCover(unittest.TestCase):
    def _pool_at_rep(self, rep):
        state, _ = fresh(13)
        state.shop.reputation = rep
        shop.roll_demand(state, random.Random(99))
        return state.delivery_pool

    def test_cover_orders_scale_with_reputation(self):
        self.assertLess(self._pool_at_rep(0), self._pool_at_rep(90))

    def test_cover_capped_by_delivery_pool(self):
        state, rng = fresh(13)
        state.delivery_pool = 3
        state.shop_stash = {}
        con = ScriptedConsole([0, 0, False, 12])   # ask for 12 cover stops
        plan = routes.plan_route(state, con, rng,
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))
        self.assertEqual(plan["legit"], 3)         # only 3 real orders exist

    def test_hollow_shop_offers_no_cover(self):
        state, rng = fresh(13)
        state.delivery_pool = 0
        state.shop_stash = {}
        plan = routes.plan_route(state, ScriptedConsole([0, 0, False, 12]), rng,
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))
        self.assertEqual(plan["legit"], 0)


class TestAssignments(unittest.TestCase):
    def test_raid_crew_cannot_also_drive(self):
        state, rng = fresh(14)
        for e in state.employees[:4]:
            e.hired = e.aware = True
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        plan = routes.plan_route(state, ScriptedConsole([0, 0, False, 0, 0]),
                                 rng, reserved=[rosa],
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))
        self.assertIsNotNone(plan)
        self.assertIsNot(plan["driver"], rosa)

    def test_driver_cannot_also_raid(self):
        state, rng = fresh(14)
        for e in state.employees[:2]:
            e.hired = e.aware = True
        rosa, tony = state.employees[0], state.employees[1]
        raid = raids.plan_raid(
            state, ScriptedConsole([1, 0, 0, 0, False]), rng,
            reserved=[rosa],
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))
        self.assertIsNotNone(raid)
        self.assertNotIn(rosa, raid["team"])
        self.assertIn(tony, raid["team"])

    def test_arrested_since_morning_is_off_the_night_job(self):
        state, _ = fresh(15)
        for e in state.employees[:3]:
            e.hired = e.aware = True
        team = list(state.employees[:3])
        for e in team:
            e.arrested = True                      # the day went very badly
        raids_led_before = state.raids_led
        plans = {                 "raid": {"rival": "vinnie", "objective": "ledger",
                          "team": team, "armed": False, "return_shop": models.HOME_SHOP_KEY}}
        phases.night(state, plans, _wag(state, revenue=0), ScriptedConsole([4]),
                     Streams(15))
        self.assertEqual(state.raids_led, raids_led_before)
        self.assertFalse(state.rivals["vinnie"].ledger_stolen)


class TestCouponIsTemporary(unittest.TestCase):
    def test_coupons_steal_customers_not_reputation(self):
        state, _ = fresh(16)
        rep_before = state.shop.reputation
        rivals._price_war(state, "sal", {"short": "Sal"}, ScriptedConsole())
        self.assertEqual(state.shop.reputation, rep_before)
        self.assertGreater(state.shop.coupon_days, 0)

        shop.roll_demand(state, random.Random(7))
        couponed = state.demand_today
        state.shop.coupon_days = 0
        shop.roll_demand(state, random.Random(7))
        self.assertGreater(state.demand_today, couponed)


class TestDemandPolicyIntegrity(unittest.TestCase):
    """Blocking finding 1: changing menu price must re-price the same crowd —
    it can never keep the old policy's demand at the new policy's ticket."""

    def test_price_switch_reforms_the_order_book(self):
        state, _ = fresh(21)
        state.shop.price = "cheap"
        shop.roll_demand(state, random.Random(42))
        cheap_demand = state.demand_today

        state.shop.price = "gourmet"
        shop.recompute_demand(state, state.shop)          # what _kitchen_policy now does
        switched = state.demand_today

        state2, _ = fresh(21)
        state2.shop.price = "gourmet"
        shop.roll_demand(state2, random.Random(42))   # same shock, honest gourmet
        honest = state2.demand_today

        self.assertEqual(switched, honest)
        self.assertLess(switched, cheap_demand)

    def test_service_charges_the_crowd_the_menu_created(self):
        """Revenue under switch == revenue under honest gourmet, same shock."""
        def revenue(switch):
            state, _ = fresh(21)
            state.shop.ingredients = 200
            state.shop.price = "cheap" if switch else "gourmet"
            shop.roll_demand(state, random.Random(42))
            if switch:
                state.shop.price = "gourmet"
                shop.recompute_demand(state, state.shop)
            report = shop.simulate_shift(state, state.shop, 0, random.Random(1))
            return report["revenue"]
        self.assertEqual(revenue(switch=True), revenue(switch=False))


class TestSharedKitchenCapacity(unittest.TestCase):
    """Blocking finding 2: delivery orders are real oven work."""

    def test_route_and_counter_share_the_ovens(self):
        state, _ = fresh(22)
        state.shop.ingredients = 200
        state.demand_today = 100
        report = shop.simulate_shift(state, state.shop, 12, random.Random(1))
        total_baked = report["orders"] + 12
        self.assertLessEqual(total_baked, state.shop.kitchen_cap)
        self.assertEqual(report["orders"], state.shop.kitchen_cap - 12)

    def test_damaged_kitchen_throttles_deliveries_too(self):
        state, _ = fresh(22)
        state.shop.damage_days = 2
        state.delivery_pool = 12
        state.shop.ingredients = 200
        rosa = next(e for e in state.employees if e.hired)
        plan = {"cargo": {}, "legit": 12, "district": "university",
                "ride_along": False, "driver": rosa, "origin_shop": models.HOME_SHOP_KEY,
                "wagon_key": models.HOME_WAGON_KEY}
        phases._commit_route(state, plan, ScriptedConsole(), phases.WagonNight(state))
        state.demand_today = 100
        report = shop.simulate_shift(state, state.shop, plan["legit"], random.Random(1))
        self.assertLessEqual(report["orders"] + plan["legit"],
                             state.shop.kitchen_cap)

    def test_empty_pantry_fills_no_delivery_orders(self):
        state, _ = fresh(22)
        state.delivery_pool = 12
        state.shop.ingredients = 3
        rosa = next(e for e in state.employees if e.hired)
        plan = {"cargo": {}, "legit": 12, "district": "university",
                "ride_along": False, "driver": rosa, "origin_shop": models.HOME_SHOP_KEY,
                "wagon_key": models.HOME_WAGON_KEY}
        phases._commit_route(state, plan, ScriptedConsole(), phases.WagonNight(state))
        self.assertEqual(plan["legit"], 3)


class TestTransactionalPlanning(unittest.TestCase):
    """Blocking finding 3: plans are intentions; only service commits."""

    def _fresh_planner(self):
        state, rng = fresh(23)
        state.delivery_pool = 12
        state.shop_stash = {"oregano": 8}
        state.shop.ingredients = 40
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.aware = True
        return state, rng

    def test_planning_and_cancelling_leaves_inventory_untouched(self):
        state, rng = self._fresh_planner()
        before = (dict(state.shop_stash), state.shop.ingredients,
                  state.delivery_pool)
        plan = routes.plan_route(state, ScriptedConsole([0, 0, False, 4, 4]), rng,
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))
        self.assertEqual(sum(plan["cargo"].values()), 4)
        cancelled = routes.plan_route(state, ScriptedConsole([4]), rng,
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))
        self.assertIsNone(cancelled)
        after = (dict(state.shop_stash), state.shop.ingredients,
                 state.delivery_pool)
        self.assertEqual(before, after)

    def test_replanning_never_strands_stock(self):
        state, rng = self._fresh_planner()
        for _ in range(5):
            routes.plan_route(state, ScriptedConsole([0, 0, False, 8, 4]), rng,
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))
        self.assertEqual(state.shop_stash["oregano"], 8)
        self.assertEqual(state.shop.ingredients, 40)

    def test_commit_takes_exactly_the_plan_once(self):
        state, rng = self._fresh_planner()
        plan = routes.plan_route(state, ScriptedConsole([0, 0, False, 4, 4]), rng,
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))
        phases._commit_route(state, plan, ScriptedConsole(), phases.WagonNight(state))
        self.assertEqual(state.shop_stash["oregano"], 4)
        self.assertEqual(state.shop.ingredients, 36)


class TestResignationFlow(unittest.TestCase):
    """Smaller issue: confrontation -> one management window -> departure."""

    def _worker(self, state):
        return next(e for e in state.employees if e.hired)

    def test_confrontation_precedes_every_departure(self):
        state, _ = fresh(24)
        e = self._worker(state)
        e.morale = 1
        phases._staff_trouble(state, ScriptedConsole(), random.Random(0))
        self.assertTrue(e.hired)                  # warned, not gone
        self.assertTrue(e.resignation_pending)
        phases._staff_trouble(state, ScriptedConsole(), random.Random(0))
        self.assertFalse(e.hired)                 # ignored the warning

    def test_a_raise_saves_them(self):
        state, _ = fresh(24)
        e = self._worker(state)
        e.morale = 2
        phases._staff_trouble(state, ScriptedConsole(), random.Random(0))
        self.assertTrue(e.resignation_pending)
        e.morale = 6                              # the raise landed
        phases._staff_trouble(state, ScriptedConsole(), random.Random(0))
        self.assertTrue(e.hired)
        self.assertFalse(e.resignation_pending)


class TestRaiseAnswersConfrontation(unittest.TestCase):
    """Review round 3, finding 1: the raise must travel the REAL raise path
    and must save an employee even from morale 1."""

    def test_actual_raise_cancels_resignation_at_morale_one(self):
        state, _ = fresh(31)
        e = next(x for x in state.employees if x.hired)
        e.morale = 1
        phases._staff_trouble(state, ScriptedConsole(), random.Random(0))
        self.assertTrue(e.resignation_pending)
        # The real menu path: Staff -> Give a raise -> pick them -> Back.
        idx = state.hired().index(e)
        phases._staff_menu(state, ScriptedConsole([2, idx, 4]), random.Random(0))
        self.assertFalse(e.resignation_pending)
        self.assertGreater(e.morale, 3)
        # They stay — this morning and the next.
        for _ in range(2):
            phases._staff_trouble(state, ScriptedConsole(), random.Random(0))
        self.assertTrue(e.hired)


class TestDriverRevalidation(unittest.TestCase):
    """Review round 3, finding 2: a route whose driver is gone must scrub
    before committing any resource."""

    def _plan(self, state, rng):
        state.delivery_pool = 12
        state.shop_stash = {"oregano": 8}
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.aware = True
        return routes.plan_route(state, ScriptedConsole([0, 0, False, 4, 4]), rng,
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))

    def test_fired_driver_scrubs_the_route_uncommitted(self):
        state, rng = fresh(32)
        plan = self._plan(state, rng)
        plan["driver"].hired = False               # fired after planning
        before = (dict(state.shop_stash), state.shop.ingredients)
        ok = phases._commit_route(state, plan, ScriptedConsole(), phases.WagonNight(state))
        self.assertFalse(ok)
        self.assertEqual((dict(state.shop_stash), state.shop.ingredients), before)

    def test_service_skips_the_scrubbed_route_entirely(self):
        state, rng = fresh(32)
        plan = self._plan(state, rng)
        driver = plan["driver"]
        driver.hired = False
        survived_before = driver.routes_survived
        shop.roll_demand(state, random.Random(1))
        phases.service(state, {"routes": {models.HOME_SHOP_KEY: plan}, "raid": None},
                       ScriptedConsole(), Streams(32))
        self.assertEqual(driver.routes_survived, survived_before)
        self.assertEqual(state.shop_stash.get("oregano"), 8)   # cargo never left


class TestQualityIdentity(unittest.TestCase):
    """Review round 3, finding 3: stock keeps the quality it was bought at.
    Cheap flour served under a gourmet menu cooks — and reviews — as cheap."""

    def _serve_day(self, buy_quality, serve_policy_quality):
        state, _ = fresh(33)
        state.shop.ingredients = 0
        state.shop.quality = buy_quality
        state.clean = 10000
        phases._buy_ingredients(state, state.shop, ScriptedConsole([40]))
        state.shop.quality = serve_policy_quality
        state.shop.price = "gourmet"
        shop.roll_demand(state, random.Random(9))
        shop.simulate_shift(state, state.shop, 0, random.Random(9))
        return state

    def test_pantry_keeps_purchase_quality(self):
        state = self._serve_day("cheap", "gourmet")
        self.assertEqual(state.shop.pantry_quality, "cheap")

    def test_cheap_stock_under_gourmet_menu_burns_reputation(self):
        scam = self._serve_day("cheap", "gourmet")
        honest = self._serve_day("gourmet", "gourmet")
        self.assertLess(scam.shop.reputation, honest.shop.reputation)

    def test_mixing_grades_drags_the_pantry_down(self):
        state, _ = fresh(33)
        state.shop.ingredients = 0
        state.clean = 10000
        state.shop.quality = "gourmet"
        phases._buy_ingredients(state, state.shop, ScriptedConsole([20]))
        self.assertEqual(state.shop.pantry_quality, "gourmet")
        state.shop.quality = "cheap"
        phases._buy_ingredients(state, state.shop, ScriptedConsole([20]))
        self.assertEqual(state.shop.pantry_quality, "cheap")


class TestEffectDurations(unittest.TestCase):
    """Review round 3, finding 4: effects created tonight keep their full
    duration; only effects that served today age at close."""

    def test_preexisting_effects_age_at_close(self):
        state, _ = fresh(34)
        state.shop.coupon_days = 2
        state.shop.damage_days = 2
        for r in state.rivals.values():
            r.strength = 0
        phases.night(state, {"routes": {}, "raid": None}, _wag(state, revenue=0),
                     ScriptedConsole([4]), Streams(34))
        self.assertEqual(state.shop.coupon_days, 1)
        self.assertEqual(state.shop.damage_days, 1)

    def test_effects_created_tonight_keep_full_duration(self):
        state, _ = fresh(34)
        for r in state.rivals.values():
            r.strength = 0
        orig = rivals.rival_phase

        def blitz_tonight(st, con, rng):
            st.shop.coupon_days = 3          # Sal's coupons land tonight
            st.shop.damage_days = 3          # and so does a wrecking crew

        rivals.rival_phase = blitz_tonight
        try:
            phases.night(state, {"routes": {}, "raid": None}, _wag(state, revenue=0),
                         ScriptedConsole([4]), Streams(34))
        finally:
            rivals.rival_phase = orig
        self.assertEqual(state.shop.coupon_days, 3)   # three full service days
        self.assertEqual(state.shop.damage_days, 3)


class TestSaveCompleteness(unittest.TestCase):
    """Review round 3, finding 5: the save must carry every State field —
    including demand_shock — so a reload never quietly resets anything."""

    def test_every_state_field_is_serialized(self):
        import dataclasses

        from extra_toppings import save
        state, _ = fresh(35)
        d = save.state_to_dict(state)
        for f in dataclasses.fields(type(state)):
            self.assertIn(f.name, d, f"State.{f.name} missing from save")

    def test_demand_shock_survives_the_round_trip(self):
        from extra_toppings import save
        state, _ = fresh(35)
        state.demand_shock = 1.0418
        restored = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(restored.demand_shock, 1.0418)
        # And the reviewer's exact symptom: the same policy change must
        # produce the same demand after a reload.
        state.shop.price = "gourmet"
        shop.recompute_demand(state, state.shop)
        restored.shop.price = "gourmet"
        shop.recompute_demand(restored, restored.shop)
        self.assertEqual(state.demand_today, restored.demand_today)


if __name__ == "__main__":
    unittest.main()
