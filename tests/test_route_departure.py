"""The route departure: a route runs under the district as it stood
WHEN IT LEFT, and only a route that actually left can run at all.

The defect, from a Partner run at seed 72. Two addresses each sent a
wagon into The Meadows on the same night. Both passed the service-time
red revalidation at heat 71.45 and both wagons were claimed. The first
route resolved and its own corner damage pushed the district past red.
The second route then REBUILT its market view from the mutated state,
classified an already-departed wagon as red, and
`RouteExecutionRecord` refused it: the run crashed. The divergence came
from its SIBLING, not from the clock — both were inside one service
phase.

Aborting at resolution would have been worse than the crash: it would
make two simultaneous routes depend on iteration order, and it would
strand inventory the departure had already spent.

So `RouteDeparture` is the execution truth, and it does NOT live on the
morning plan. The first correction hung a market view on `RoutePlan`
and it was forged three ways — the constructor took it directly, dict
plans bypassed the write-once guard, and the reader accepted any
non-`None` object, so University Hill's view on a Meadows plan resolved
and logged University Hill. A plan is an intention; a departure is a
fact, and only `_commit_route` can make one.

Canon already said commit is departure and the red refusal binds at
service-time revalidation (rev. 14 item 5): a correctness correction,
not a new rule.
"""

import dataclasses
import random
import unittest

from extra_toppings import market, models, phases, routes
from extra_toppings.models import (HOME_SHOP_KEY, HOME_WAGON_KEY, Shop,
                                   Wagon, new_state)
from extra_toppings.ui import ScriptedConsole
from route_support import deep_snapshot, departed


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
OTHER_DISTRICT = "university"
# Just under red, so ONE route's own corner damage carries it over —
# the transition is EXERCISED, not assigned.
NEAR_RED = float(models.HEAT_RED) - 1.0
RED_HEAT = float(models.HEAT_RED) + 1.0


def _two_route_world(heat: float):
    """Two open addresses, two wagons, two drivers, both routes aimed
    at ONE district — the seed-72 shape, built deterministically."""
    state = new_state()
    state.day = 16
    # THE TEETH ONLY BITE ON A BRANCH THAT CARRIES THEM
    # (`HEAT_TEETH_BRANCHES`), and seed 72 was a Partner run. A
    # chairless world reads every district cool, which would make this
    # whole file pass while testing nothing.
    state.branch = "partner"
    state.shops.append(Shop(key="shop2", district=OTHER_DISTRICT,
                            acceptance_day=14, opening_day=16,
                            ingredients=40, stash={"mushrooms": 6}))
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


def _plan(driver, origin, wagon, district=DISTRICT):
    return routes.RoutePlan(
        district=district, driver=driver, ride_along=False,
        manifest=routes.RouteManifest(cargo={"mushrooms": 3}, legit=2),
        origin_shop=origin, wagon_key=wagon)


def _both_plans(drivers):
    return {
        HOME_SHOP_KEY: _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY),
        "shop2": _plan(drivers[1], "shop2", "wagon2"),
    }


def _snapshot(state):
    """THE WHOLE WORLD, serialised. A hand-listed "complete" snapshot
    is a promise the list cannot keep: the first one here named cash,
    stash, pantry, revenue, reputation, heat and the Case, and
    silently omitted employees, known prices, rivals, campaigns and
    every other mutable field — so a refusal that moved one of those
    would have passed. This reads the save boundary, the one authority
    that already has to see everything."""
    return deep_snapshot(state)


class TestTheMarketIsFixedAtDeparture(unittest.TestCase):

    def test_both_routes_depart_amber_and_both_log_amber(self):
        """THE seed-72 case, with the crossing EARNED. The district
        starts a point below red and the first route's own corner
        damage carries it over; the second still runs under the band
        it left under."""
        state, drivers = _two_route_world(NEAR_RED)
        plans = _both_plans(drivers)
        wagons = phases.WagonNight(state)
        con = Quiet()
        departures = {}
        for key, plan in plans.items():
            departures[key] = phases._commit_route(state, plan, con, wagons)
            self.assertIsNotNone(departures[key])
            self.assertEqual(departures[key].market.heat.band, "amber")

        self.assertEqual(
            models.district_heat_policy(state, DISTRICT).band, "amber")
        routes.resolve_route(departures[HOME_SHOP_KEY], Quiet(),
                             random.Random(3))
        # The transition is ASSERTED, not assigned: the first route's
        # own consequences did this.
        self.assertGreaterEqual(state.districts[DISTRICT].heat,
                                models.HEAT_RED)
        self.assertEqual(
            models.district_heat_policy(state, DISTRICT).band, "red")

        routes.resolve_route(departures["shop2"], Quiet(), random.Random(4))
        bands = [r.heat_band for r in state.route_log
                 if r.district == DISTRICT]
        self.assertEqual(bands, ["amber", "amber"])

    def test_the_departure_band_does_not_depend_on_filing_order(self):
        """Narrowed to what the fixture actually establishes: the BAND
        each route departs under, and the band it logs, are the same
        whichever address commits first. The full monetary outcome is
        not claimed — the two orders draw the same seeds in a
        different sequence."""
        seen = {}
        for order in ((HOME_SHOP_KEY, "shop2"), ("shop2", HOME_SHOP_KEY)):
            state, drivers = _two_route_world(NEAR_RED)
            plans = _both_plans(drivers)
            wagons = phases.WagonNight(state)
            departures = {}
            for key in order:
                departures[key] = phases._commit_route(
                    state, plans[key], Quiet(), wagons)
            for i, key in enumerate(order):
                routes.resolve_route(departures[key], Quiet(),
                                     random.Random(3 + i))
            seen[order] = {
                "departed": sorted((k, d.market.heat.band)
                                   for k, d in departures.items()),
                "logged": sorted((r.origin_shop, r.heat_band,
                                  r.capacity_mult)
                                 for r in state.route_log),
            }
        first, second = seen.values()
        self.assertEqual(first, second)
        for _key, band in first["departed"]:
            self.assertEqual(band, "amber")

    def test_red_before_departure_leaves_everything_untouched(self):
        """A route red at DEPARTURE scrubs before the wagon, the
        pantry, the stash or the log move — rev. 14 item 5's refusal,
        still binding and still atomic."""
        state, drivers = _two_route_world(RED_HEAT)
        self.assertEqual(
            models.district_heat_policy(state, DISTRICT).band, "red")
        plans = _both_plans(drivers)
        before = _snapshot(state)
        wagons = phases.WagonNight(state)
        con = Quiet()
        for plan in plans.values():
            self.assertIsNone(
                phases._commit_route(state, plan, con, wagons))
        self.assertEqual(_snapshot(state), before)
        # THE ORIGINAL wagon authority — a fresh one would answer
        # "nothing is claimed" no matter what happened tonight.
        for shop_key in (HOME_SHOP_KEY, "shop2"):
            self.assertTrue(wagons.free_at(shop_key),
                            "the scrubbed route claimed a wagon")
        self.assertTrue(con.said("is scrubbed"))


class TestOnlyARouteThatLeftCanRun(unittest.TestCase):

    def test_a_plan_alone_cannot_resolve_and_moves_nothing(self):
        """The side entrance, closed — and closed BEFORE any mutation.
        The first version read the departure after booking cover
        revenue and docking reputation, so an undeparted route raised
        as designed and still moved clean 2000 → 2032, address revenue
        0 → 32 and reputation 50 → 47 on the way out."""
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        state.clean = 2000
        before = _snapshot(state)
        with self.assertRaises(ValueError) as caught:
            routes.resolve_route(plan, Quiet(), random.Random(3))
        self.assertIn("departure", str(caught.exception))
        self.assertEqual(_snapshot(state), before)

    def test_a_forged_departure_object_is_refused(self):
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        before = _snapshot(state)
        for forgery in (None, {"market": None},
                        market.route_market(state, DISTRICT), plan):
            with self.assertRaises(ValueError):
                routes.resolve_route(forgery, Quiet(), random.Random(3))
        self.assertEqual(_snapshot(state), before)

    def test_the_positive_control_departs_and_resolves(self):
        # Without this the refusals above would be proved by a door
        # that refuses everybody.
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        departure = departed(state, plan)
        routes.resolve_route(departure, Quiet(), random.Random(3))
        self.assertEqual(len(state.route_log), 1)

    def test_no_caller_can_supply_a_market_at_all(self):
        """The forgeries that worked against the second correction are
        now unreachable BY CONSTRUCTION rather than by validation: the
        market is derived from the bound state, so neither another
        district's view nor ANOTHER WORLD's can be handed in. A cool
        Meadows view from state B attached to an amber Meadows route
        in state A resolved and logged cool."""
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        elsewhere = market.route_market(state, OTHER_DISTRICT)
        with self.assertRaises(TypeError):
            routes.RouteDeparture(state=state, plan=plan,
                                  token=routes._DEPARTURE_TOKEN,
                                  market=elsewhere)
        # …and a departure that IS made always carries its own
        # district, read from the state it is bound to.
        departure = departed(state, plan)
        self.assertEqual(departure.market,
                         market.route_market(state, DISTRICT))
        self.assertEqual(departure.market.district, DISTRICT)

    def test_a_cool_view_from_another_world_cannot_be_smuggled_in(self):
        """The exact second reproduction. Two worlds, same district,
        different heat: the departure reads the world it is bound to
        and nothing else."""
        hot, drivers = _two_route_world(NEAR_RED)
        cool, _other = _two_route_world(0.0)
        self.assertEqual(
            market.route_market(cool, DISTRICT).heat.band, "cool")
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        departure = departed(hot, plan)
        self.assertIs(departure.state, hot)
        self.assertEqual(departure.market.heat.band, "amber")
        routes.resolve_route(departure, Quiet(), random.Random(3))
        self.assertEqual([r.heat_band for r in hot.route_log], ["amber"])

    def test_a_plan_edited_after_departure_refuses_before_mutating(self):
        """The exact first reproduction. `RouteDeparture` is frozen
        but its PLAN is not: a Meadows departure whose `district` was
        then set to University Hill executed against University Hill
        while the ledger recorded Meadows."""
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        departure = departed(state, plan)
        plan.district = OTHER_DISTRICT
        before = _snapshot(state)
        with self.assertRaises(ValueError) as caught:
            routes.resolve_route(departure, Quiet(), random.Random(3))
        self.assertIn("changed after it departed", str(caught.exception))
        self.assertEqual(_snapshot(state), before)

    def test_every_identity_field_is_fingerprinted(self):
        # District, origin, wagon, driver, ride-along and disposal all
        # say WHICH ROUTE THIS IS; an edit to any of them means the
        # wagon that left is not the one being resolved.
        edits = {"district": OTHER_DISTRICT, "origin_shop": "shop2",
                 "wagon_key": "wagon2", "ride_along": True,
                 "disposal": True}
        for field_name, value in edits.items():
            with self.subTest(field=field_name):
                state, drivers = _two_route_world(NEAR_RED)
                plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
                departure = departed(state, plan)
                setattr(plan, field_name, value)
                before = _snapshot(state)
                with self.assertRaises(ValueError):
                    routes.resolve_route(departure, Quiet(),
                                         random.Random(3))
                self.assertEqual(_snapshot(state), before)
        # …and the driver, by identity.
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        departure = departed(state, plan)
        plan.driver = drivers[1]
        with self.assertRaises(ValueError):
            routes.resolve_route(departure, Quiet(), random.Random(3))

    def test_the_market_view_is_gone_from_the_plan_model(self):
        # Removed from the MODEL, not merely from mapping access.
        self.assertNotIn(
            "market_view", {f.name for f in
                            dataclasses.fields(routes.RoutePlan)})
        self.assertNotIn("market_view", routes.RoutePlan._KEYS)

    def test_the_probe_seam_is_scope_guarded(self):
        # It is a sanctioned test/analysis seam, not a second general
        # gameplay maker: this module is not on the list, and the call
        # below is made from HERE rather than from `route_support`.
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        with self.assertRaises(ValueError) as caught:
            routes.record_departure_for_probe(state, plan)
        self.assertIn("centralised test support", str(caught.exception))
        with self.assertRaises(ValueError):
            routes.depart_at_commit(state, plan)

    def test_a_red_district_cannot_produce_a_departure_at_all(self):
        state, drivers = _two_route_world(RED_HEAT)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        with self.assertRaises(ValueError) as caught:
            departed(state, plan)
        self.assertIn("cannot depart under", str(caught.exception))

    def test_a_malformed_plan_cannot_produce_a_departure(self):
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], "shop9", HOME_WAGON_KEY)
        before = _snapshot(state)
        # A ghost address refuses as a KeyError from the address
        # authority rather than a ValueError — the point is that no
        # departure is produced, whichever refusal fires first.
        with self.assertRaises((ValueError, KeyError)):
            departed(state, plan)
        self.assertEqual(_snapshot(state), before)

    def test_the_departure_binds_its_own_world_by_identity(self):
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        departure = departed(state, plan)
        self.assertIs(departure.state, state)
        self.assertIs(departure.plan, plan)
        self.assertEqual(departure.market,
                         market.route_market(state, DISTRICT))

    def test_recording_a_departure_mutates_nothing(self):
        # The morning plan stays an intention: the departure is a
        # separate value, not a field anybody can set on the plan.
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        before = _snapshot(state)
        departed(state, plan)
        self.assertEqual(_snapshot(state), before)
        self.assertNotIn("market_view", routes.RoutePlan._KEYS)


if __name__ == "__main__":
    unittest.main()
