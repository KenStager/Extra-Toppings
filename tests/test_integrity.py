"""System-integrity tests from the post-merge review: the chunked-laundering
exploit, phantom cover orders, route revenue outside the ledger, assignment
double-booking, and permanent coupon damage."""

import random
import unittest

from extra_toppings import market, phases, raids, rivals, routes, shop
from extra_toppings.models import new_state
from extra_toppings.rng import Streams
from extra_toppings.ui import ScriptedConsole


def fresh(seed=1):
    rng = random.Random(seed)
    state = new_state()
    market.roll_prices(state, rng)
    return state, rng


def run_night(state, seed, script):
    plans = {"route": None, "raid": None}
    report = {"revenue": 0}
    # Keep rivals quiet so the only case movement comes from the register.
    for r in state.rivals.values():
        r.strength = 0
    phases.night(state, plans, report, ScriptedConsole(script), Streams(seed))


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
                "cargo": {}, "legit": 8}
        routes.resolve_route(state, plan, ScriptedConsole(), rng)
        self.assertGreater(state.legit_revenue_today, before)
        self.assertGreater(shop.believable_ceiling(state, state.legit_revenue_today),
                           shop.believable_ceiling(state, before))


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
        plan = routes.plan_route(state, con, rng)
        self.assertEqual(plan["legit"], 3)         # only 3 real orders exist

    def test_hollow_shop_offers_no_cover(self):
        state, rng = fresh(13)
        state.delivery_pool = 0
        state.shop_stash = {}
        plan = routes.plan_route(state, ScriptedConsole([0, 0, False, 12]), rng)
        self.assertEqual(plan["legit"], 0)


class TestAssignments(unittest.TestCase):
    def test_raid_crew_cannot_also_drive(self):
        state, rng = fresh(14)
        for e in state.employees[:4]:
            e.hired = e.aware = True
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        plan = routes.plan_route(state, ScriptedConsole([0, 0, False, 0, 0]),
                                 rng, reserved=[rosa])
        self.assertIsNotNone(plan)
        self.assertIsNot(plan["driver"], rosa)

    def test_driver_cannot_also_raid(self):
        state, rng = fresh(14)
        for e in state.employees[:2]:
            e.hired = e.aware = True
        rosa, tony = state.employees[0], state.employees[1]
        raid = raids.plan_raid(state, ScriptedConsole([1, 0, 0, 0, False]),
                               rng, reserved=[rosa])
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
        plans = {"route": None,
                 "raid": {"rival": "vinnie", "objective": "ledger",
                          "team": team, "armed": False}}
        phases.night(state, plans, {"revenue": 0}, ScriptedConsole([4]),
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


if __name__ == "__main__":
    unittest.main()
