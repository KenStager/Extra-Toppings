"""The route-departure market: a route runs under the district as it
stood WHEN IT LEFT.

The defect, reproduced from a Partner run at seed 72. Two addresses
each sent a wagon into The Meadows on the same night. Both passed the
service-time red revalidation at heat 71.45 and both wagons were
claimed. The first route resolved and its own corner damage pushed the
district to 96.6 — red. The second route then REBUILT its market view
from the mutated state, classified an already-departed wagon as red,
and `RouteExecutionRecord` refused it: the run crashed.

Aborting at resolution would have been worse than the crash. It would
make two simultaneous routes depend on iteration order, and it would
strand inventory the departure had already spent — the stash and
pantry come out at commit, and a route that "never happened" would
have eaten them anyway.

So the market is fixed at DEPARTURE, by one authority, and resolution
consumes exactly that view. Canon already said commit is departure and
the red refusal binds at service-time revalidation (rev. 14 item 5);
this is a correctness correction, not a new rule.
"""

import random
import unittest

from extra_toppings import data, market, models, phases, routes
from extra_toppings.models import (HOME_SHOP_KEY, HOME_WAGON_KEY, Shop,
                                   Wagon, new_state)
from extra_toppings.ui import ScriptedConsole


class Quiet(ScriptedConsole):
    def __init__(self):
        super().__init__([])
        self.lines: list = []

    def say(self, text: str = "") -> None:
        self.lines.append(text)

    def bullet(self, text: str) -> None:
        self.lines.append(f"• {text}")

    def said(self, fragment: str) -> bool:
        return any(fragment in line for line in self.lines)


DISTRICT = "meadows"


def _two_route_world(heat: float):
    """Two open addresses, two wagons, two drivers, both routes aimed
    at ONE district sitting at `heat` — the seed-72 shape, built
    deterministically instead of hunted for."""
    state = new_state()
    state.day = 16
    # THE TEETH ONLY BITE ON A BRANCH THAT CARRIES THEM
    # (`HEAT_TEETH_BRANCHES`), and seed 72 was a Partner run — a
    # world with no chair reads every district cool, which would have
    # made this whole file pass while testing nothing.
    state.branch = "partner"
    state.shops.append(Shop(key="shop2", district="university",
                            acceptance_day=14, opening_day=16,
                            ingredients=40,
                            stash={"mushrooms": 6}))
    state.shops[0].stash = {"mushrooms": 6}
    state.shops[0].ingredients = 40
    state.wagons.append(Wagon(key="wagon2", shop_key="shop2"))
    drivers = [e for e in state.employees if e.role == "driver"][:2]
    for e, key in zip(drivers, (HOME_SHOP_KEY, "shop2")):
        e.hired = True
        e.shop_key = key
    state.districts[DISTRICT].heat = heat
    for s in state.shops:
        s.delivery_pool = 8
    return state, drivers


def _plan(state, driver, origin, wagon):
    return routes.RoutePlan(
        district=DISTRICT, driver=driver, ride_along=False,
        manifest=routes.RouteManifest(cargo={"mushrooms": 3}, legit=2),
        origin_shop=origin, wagon_key=wagon)


def _both_plans(state, drivers):
    return {
        HOME_SHOP_KEY: _plan(state, drivers[0], HOME_SHOP_KEY,
                             HOME_WAGON_KEY),
        "shop2": _plan(state, drivers[1], "shop2", "wagon2"),
    }


def _amber_heat() -> float:
    """Amber: plannable, and one nudge below red. Read off the
    canonical thresholds rather than hunted for, so a threshold change
    moves this fixture with it instead of silently making it cool."""
    return float(models.HEAT_AMBER)


RED_HEAT = float(models.HEAT_RED) + 1.0


class TestTheMarketIsFixedAtDeparture(unittest.TestCase):

    def test_both_routes_depart_amber_and_both_log_amber(self):
        """THE seed-72 case. The first route's own consequences must
        not reclassify the second one's already-departed wagon."""
        state, drivers = _two_route_world(_amber_heat())
        plans = _both_plans(state, drivers)
        wagons = phases.WagonNight(state)
        con = Quiet()
        for plan in plans.values():
            self.assertTrue(phases._commit_route(state, plan, con, wagons))
            self.assertEqual(plan["market_view"].heat.band, "amber")

        # The first resolution drives the district into red — the
        # mutation that used to poison its sibling.
        first, second = plans[HOME_SHOP_KEY], plans["shop2"]
        routes.resolve_route(state, first, Quiet(), random.Random(3))
        state.districts[DISTRICT].heat = RED_HEAT
        self.assertEqual(
            models.district_heat_policy(state, DISTRICT).band, "red")

        # …and the second still runs, under the band it left under.
        routes.resolve_route(state, second, Quiet(), random.Random(4))
        bands = [r.heat_band for r in state.route_log
                 if r.district == DISTRICT]
        self.assertEqual(bands, ["amber", "amber"])
        self.assertEqual(len(state.route_log), 2)

    def test_the_result_does_not_depend_on_filing_order(self):
        """A route's outcome must not depend on which address sorts
        first — the property an abort-at-resolution fix would have
        destroyed."""
        results = {}
        for order in (("shop1", "shop2"), ("shop2", "shop1")):
            state, drivers = _two_route_world(_amber_heat())
            plans = _both_plans(state, drivers)
            wagons = phases.WagonNight(state)
            for key in order:
                phases._commit_route(state, plans[key], Quiet(), wagons)
            for i, key in enumerate(order):
                routes.resolve_route(state, plans[key], Quiet(),
                                     random.Random(3 + i))
                state.districts[DISTRICT].heat = RED_HEAT
            results[order] = sorted(
                (r.origin_shop, r.heat_band, r.capacity_mult)
                for r in state.route_log)
        self.assertEqual(results[("shop1", "shop2")],
                         results[("shop2", "shop1")])
        for row in results[("shop1", "shop2")]:
            self.assertEqual(row[1], "amber")

    def test_red_before_departure_leaves_everything_untouched(self):
        """A route red at DEPARTURE scrubs before the wagon, the
        pantry, the stash or the log move — rev. 14 item 5's refusal,
        still binding and still atomic."""
        state, drivers = _two_route_world(RED_HEAT)
        self.assertEqual(
            models.district_heat_policy(state, DISTRICT).band, "red")
        plans = _both_plans(state, drivers)
        before = [(s.key, dict(s.stash), s.ingredients)
                  for s in state.shops]
        wagons = phases.WagonNight(state)
        con = Quiet()
        for plan in plans.values():
            self.assertFalse(phases._commit_route(state, plan, con, wagons))
            self.assertIsNone(plan["market_view"])
        self.assertEqual([(s.key, dict(s.stash), s.ingredients)
                          for s in state.shops], before)
        self.assertEqual(state.route_log, [])
        # …and no wagon was claimed: a fresh night still finds both
        # of them free at their own addresses.
        fresh = phases.WagonNight(state)
        for shop_key in (HOME_SHOP_KEY, "shop2"):
            self.assertTrue(fresh.free_at(shop_key))
        self.assertTrue(con.said("is scrubbed"))

    def test_resolution_cannot_synthesise_its_own_market(self):
        """The side entrance, closed. A plan that never departed has
        no band to run under, and resolution refuses rather than
        reading whatever the district happens to say now."""
        state, drivers = _two_route_world(_amber_heat())
        plan = _plan(state, drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        self.assertIsNone(plan["market_view"])
        with self.assertRaises(ValueError) as caught:
            routes.resolve_route(state, plan, Quiet(), random.Random(3))
        self.assertIn("departure-time market", str(caught.exception))
        self.assertEqual(state.route_log, [])

    def test_the_positive_control_departs_and_resolves(self):
        # Without this, the refusal above would be proved by a door
        # that refuses everybody.
        state, drivers = _two_route_world(_amber_heat())
        plan = _plan(state, drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        routes.record_departure(state, plan)
        routes.resolve_route(state, plan, Quiet(), random.Random(3))
        self.assertEqual(len(state.route_log), 1)

    def test_a_route_departs_once(self):
        state, drivers = _two_route_world(_amber_heat())
        plan = _plan(state, drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        routes.record_departure(state, plan)
        with self.assertRaises(ValueError) as caught:
            routes.record_departure(state, plan)
        self.assertIn("already departed", str(caught.exception))

    def test_the_recorded_view_is_the_districts_own(self):
        # The view is not invented for the record: it is exactly what
        # `market.route_market` says at that instant.
        state, drivers = _two_route_world(_amber_heat())
        plan = _plan(state, drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        want = market.route_market(state, DISTRICT)
        self.assertEqual(routes.record_departure(state, plan), want)
        self.assertEqual(plan["market_view"].district, DISTRICT)
        self.assertIn(plan["market_view"].heat.band,
                      tuple(models.ROUTE_EXECUTED_BANDS))
        self.assertIn(DISTRICT, data.DISTRICTS)


if __name__ == "__main__":
    unittest.main()
