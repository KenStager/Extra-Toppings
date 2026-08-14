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

import ast
import collections
import dataclasses
import os
import pathlib
import random
import sys
import types
import unittest

import route_support
from extra_toppings import market, models, phases, routes
from extra_toppings.models import (HOME_SHOP_KEY, HOME_WAGON_KEY, Shop,
                                   Wagon, new_state)
from extra_toppings.ui import ScriptedConsole
from route_support import deep_snapshot, departed

_ROOT = str(pathlib.Path(__file__).resolve().parent.parent)
_ROUTE_SUPPORT = os.path.join(_ROOT, "tests", "route_support.py")
_PHASES = os.path.join(_ROOT, "extra_toppings", "phases.py")

# A look-alike: the sanctioned name, calling the sanctioned maker,
# compiled with whatever `__file__` the forger likes.
_FORGERY = ("def {name}(state, plan, routes):\n"
            "    return routes.{maker}(state, plan)\n")


def _compiled(path: str, source: str) -> dict:
    """Code compiled to LOOK like it came from `path`."""
    namespace: dict = {"__file__": path}
    exec(compile(source, path, "exec"), namespace)
    return namespace


def _forged(path: str, name: str):
    maker = ("record_departure_for_probe" if name == "departed"
             else "depart_at_commit")
    return _compiled(path, _FORGERY.format(name=name, maker=maker))[name]


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
            # READ AT DEPARTURE, which is when the band is a fact. A
            # departure that has run is spent — it hands its world,
            # plan and market to the one resolution and keeps nothing,
            # so there is no after-the-fact field here to read.
            bands = sorted((k, d.market.heat.band)
                           for k, d in departures.items())
            for i, key in enumerate(order):
                routes.resolve_route(departures[key], Quiet(),
                                     random.Random(3 + i))
            seen[order] = {
                "departed": bands,
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

    def test_a_departure_cannot_be_constructed_at_all(self):
        """A module-level token was not factory control: it was
        reachable as `routes._DEPARTURE_TOKEN`, and
        `RouteDeparture(state=s, plan=p, token=that)` built one. Every
        field is `init=False` now, so there is no constructor to
        call."""
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        self.assertFalse(
            [f.name for f in dataclasses.fields(routes.RouteDeparture)
             if f.init],
            "a departure still has an init field somebody can pass")
        with self.assertRaises(TypeError):
            routes.RouteDeparture(state=state, plan=plan)
        with self.assertRaises(ValueError):
            routes.RouteDeparture()
        # …and a departure that IS made always carries its own
        # district, read from the state it is bound to.
        departure = departed(state, plan)
        self.assertEqual(departure.market,
                         market.route_market(state, DISTRICT))

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

    def test_the_guard_matches_a_PATH_and_a_FUNCTION_not_a_filename(self):
        """A basename guard is not a scope. Code compiled as
        `/tmp/route_support.py` carried that `__file__` straight
        through an earlier version, and any function in any `phases.py`
        could call the production maker."""
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        for path, func in (("/tmp/route_support.py", "departed"),
                           ("/tmp/phases.py", "_commit_route")):
            with self.assertRaises(ValueError):
                _forged(path, func)(state, plan, routes)
        # And the real seam, from its real home, still works.
        self.assertIsNotNone(departed(state, plan))

    def test_no_other_call_site_exists_anywhere_in_the_tree(self):
        """The AST call-site guard, exhaustive this time.

        The earlier version read TOP-LEVEL FUNCTIONS ONLY, collapsed
        repeated calls in one function into a set, and did not track
        `_make_departure` at all — so a call from a class method, a
        call at module level, a second call beside a sanctioned one,
        and every call to the maker itself were all invisible to it.
        This walks EVERY scope, counts MULTIPLICITY, and covers every
        function that can produce or authorise a departure — including
        this file, which is no longer exempt from its own guard."""
        allowed = {
            ("_make_departure", "extra_toppings/routes.py",
             "depart_at_commit"): 1,
            ("_make_departure", "extra_toppings/routes.py",
             "record_departure_for_probe"): 1,
            ("depart_at_commit", "extra_toppings/phases.py",
             "_commit_route"): 1,
            ("record_departure_for_probe", "analysis/experiments.py",
             "_heat_exposure_probe.night"): 1,
            ("record_departure_for_probe", "tests/route_support.py",
             "departed"): 1,
            # The capability hand-over: module scope, once per owner.
            ("grant_departure_scope", "extra_toppings/phases.py",
             "<module>"): 1,
            ("grant_departure_scope", "analysis/experiments.py",
             "<module>"): 1,
            ("grant_departure_scope", "tests/route_support.py",
             "<module>"): 1,
            # …and this file's own hostile call sites, declared so a
            # new one has to be declared rather than hidden here.
            ("depart_at_commit", "tests/test_route_departure.py",
             "TestOnlyARouteThatLeftCanRun."
             "test_the_probe_seam_is_scope_guarded"): 1,
            ("record_departure_for_probe", "tests/test_route_departure.py",
             "TestOnlyARouteThatLeftCanRun."
             "test_the_probe_seam_is_scope_guarded"): 1,
            ("_make_departure", "tests/test_route_departure.py",
             "TestTheGuardAuthenticatesCodeNotNames."
             "test_the_maker_itself_is_guarded_and_moves_nothing"): 1,
            ("grant_departure_scope", "tests/test_route_departure.py",
             "TestTheGuardAuthenticatesCodeNotNames."
             "test_a_scope_is_granted_once_by_the_code_that_owns_it"): 4,
            ("grant_departure_scope", "tests/test_route_departure.py",
             "TestTheGuardAuthenticatesCodeNotNames."
             "test_a_scope_does_not_depend_on_how_its_file_was_invoked"): 1,
        }
        tracked = {name for name, _rel, _scope in allowed}
        root = pathlib.Path(__file__).resolve().parent.parent
        found: collections.Counter = collections.Counter()

        def scan(node, scope: list, rel: str) -> None:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.Call):
                    fn = child.func
                    name = getattr(fn, "attr", getattr(fn, "id", None))
                    if name in tracked:
                        found[(name, rel,
                               ".".join(scope) or "<module>")] += 1
                inner = scope
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                      ast.ClassDef)):
                    inner = scope + [child.name]
                scan(child, inner, rel)

        for path in root.rglob("*.py"):
            rel = path.relative_to(root).as_posix()
            scan(ast.parse(path.read_text()), [], rel)
        self.assertEqual(dict(found), allowed,
                         "a departure maker is called somewhere new")


class TestTheGuardAuthenticatesCodeNotNames(unittest.TestCase):
    """Every guard this correction has worn died the same death:
    authenticating a NAME instead of an IDENTITY. `__name__` (which is
    `__main__` under `python -m`); a basename (`/tmp/route_support.py`);
    a module-level token (reachable as `routes._DEPARTURE_TOKEN`); an
    absolute path plus a function name (a function COMPILED with those
    strings walked through); and — found while trying to break the
    fix — a lookup through `sys.modules` (a fake module registered
    under a sanctioned name was resolved and honoured).

    So the authority is never READ by name. It is HANDED OVER once, at
    import, by the module that compiled it, and checked against the
    code that module's file actually defines."""

    def test_the_maker_itself_is_guarded_and_moves_nothing(self):
        """A leading underscore is a convention, not a scope. With the
        guard in the two public wrappers only,
        `routes._make_departure(state, plan)` produced a real
        departure; resolving it moved clean cash 2000 → 2032, address
        revenue 0 → 32 and wrote a `RouteExecutionRecord` while the
        pantry stayed at 40 and no wagon had ever been claimed."""
        for role in (routes.PROBE_SCOPE, routes.COMMIT_SCOPE):
            with self.subTest(role=role):
                state, drivers = _two_route_world(NEAR_RED)
                state.clean = 2000
                plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
                before = _snapshot(state)
                with self.assertRaises(ValueError) as caught:
                    routes._make_departure(state, plan, role, "nowhere")
                self.assertIn("a route departs from",
                              str(caught.exception))
                self.assertEqual(_snapshot(state), before)

    def test_code_compiled_with_the_EXACT_sanctioned_path_is_refused(self):
        """The reviewer's second reproduction. The previous guard
        compared an absolute path and a function name, so a function
        compiled with exactly those strings produced an amber
        departure. A code object is not a string."""
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        before = _snapshot(state)
        for path, func in ((_ROUTE_SUPPORT, "departed"),
                           (_PHASES, "_commit_route")):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    _forged(path, func)(state, plan, routes)
        self.assertEqual(_snapshot(state), before)
        # The door is not proved by one that refuses everybody.
        self.assertIsNotNone(departed(state, plan))

    def test_a_fake_module_under_a_sanctioned_name_is_refused(self):
        """Found while trying to break the fix, not reported: the
        first correction resolved the sanctioned function through
        `sys.modules` at guard time, so a module object registered as
        `route_support`, carrying the sanctioned `__file__` and a
        `departed` of its own, was resolved and honoured — the same
        defect one level up. Nothing is looked up by name now."""
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        before = _snapshot(state)
        fake = types.ModuleType("route_support")
        fake.__file__ = _ROUTE_SUPPORT
        exec(compile(_FORGERY.format(name="departed",
                                     maker="record_departure_for_probe"),
                     _ROUTE_SUPPORT, "exec"), fake.__dict__)
        real = sys.modules["route_support"]
        sys.modules["route_support"] = fake
        try:
            with self.assertRaises(ValueError):
                fake.departed(state, plan, routes)
        finally:
            sys.modules["route_support"] = real
        self.assertEqual(_snapshot(state), before)

    def test_rebinding_the_sanctioned_name_authorises_nothing(self):
        """The guard holds the code object, not the attribute, so
        replacing `phases._commit_route` with a look-alike does not
        move the authority with the name."""
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        real = phases._commit_route
        phases._commit_route = _forged(_PHASES, "_commit_route")
        try:
            with self.assertRaises(ValueError):
                phases._commit_route(state, plan, routes)
        finally:
            phases._commit_route = real

    def test_a_scope_is_granted_once_by_the_code_that_owns_it(self):
        """The capability, and its four refusals. An undeclared slot,
        a declaration from the wrong file, a look-alike carrying a
        declared name, and a slot somebody already holds."""
        def sneaks_out(state, plan):          # an undeclared scope
            return None
        with self.assertRaises(ValueError) as caught:
            routes.grant_departure_scope(routes.PROBE_SCOPE, sneaks_out)
        self.assertIn("not a declared departure scope",
                      str(caught.exception))

        # A declared name, from the wrong file.
        elsewhere = _compiled("/tmp/route_support.py",
                              _FORGERY.format(
                                  name="departed",
                                  maker="record_departure_for_probe"))
        with self.assertRaises(ValueError) as caught:
            routes.grant_departure_scope(routes.PROBE_SCOPE,
                                         elsewhere["departed"])
        self.assertIn("is defined in", str(caught.exception))

        # A declared name AND the declared file — but not that file's
        # code.
        lookalike = _compiled(_ROUTE_SUPPORT,
                              _FORGERY.format(
                                  name="departed",
                                  maker="record_departure_for_probe"))
        with self.assertRaises(ValueError) as caught:
            routes.grant_departure_scope(routes.PROBE_SCOPE,
                                         lookalike["departed"])
        self.assertIn("not by a look-alike", str(caught.exception))

        # And the genuine article, which is already held — so nobody
        # can take the slot a second time, whoever they are.
        with self.assertRaises(ValueError) as caught:
            routes.grant_departure_scope(routes.PROBE_SCOPE,
                                         route_support.departed)
        self.assertIn("granted once", str(caught.exception))

    def test_a_scope_does_not_depend_on_how_its_file_was_invoked(self):
        """`__module__` is how a file was INVOKED, not what it is —
        the first guard in this correction's history died on exactly
        that, and keying the grant slot on it repeated the death: under
        `python3 -m analysis.experiments` the probe's module name is
        `__main__`, so the sanctioned probe could not grant its own
        scope and the fork battery died at import. Caught by the
        battery, not by a test, which is why this pin exists.

        The genuine code, carrying a `__main__` module name, must get
        past the slot lookup and the code check and be refused only
        because the slot is already held."""
        real = route_support.departed
        as_main = types.FunctionType(real.__code__, real.__globals__,
                                     real.__name__)
        as_main.__module__ = "__main__"
        with self.assertRaises(ValueError) as caught:
            routes.grant_departure_scope(routes.PROBE_SCOPE, as_main)
        self.assertIn("granted once", str(caught.exception))
        self.assertNotIn("not a declared", str(caught.exception))

    def test_consumption_is_not_a_field_a_caller_can_reset(self):
        """The reviewer's third reproduction. Consumption was a public
        mutable list on the value, so after one resolution
        `departure.spent[0] = False` allowed another: clean cash
        2000 → 2032 → 2064, address revenue 32 → 64 and a second log
        row for one night. There is no flag to reset now — the claim
        hands the world, the plan and the market to the one resolution
        and strikes them off the departure."""
        self.assertNotIn(
            "spent", {f.name for f in
                      dataclasses.fields(routes.RouteDeparture)},
            "consumption is a field on the value again")
        state, drivers = _two_route_world(NEAR_RED)
        state.clean = 2000
        plan = routes.RoutePlan(
            district=DISTRICT, driver=drivers[0], ride_along=False,
            manifest=routes.RouteManifest(cargo={}, legit=2),
            origin_shop=HOME_SHOP_KEY, wagon_key=HOME_WAGON_KEY)
        departure = departed(state, plan)
        routes.resolve_route(departure, Quiet(), random.Random(3))
        after_one = _snapshot(state)
        self.assertEqual(state.clean, 2032)
        self.assertEqual(len(state.route_log), 1)
        # THE EXACT RESET, and then the same reset forced past the
        # frozen dataclass with `object.__setattr__`.
        with self.assertRaises(dataclasses.FrozenInstanceError):
            departure.spent = [False]                    # type: ignore[attr-defined]
        for reset in (lambda: object.__setattr__(departure, "spent",
                                                 [False]),
                      lambda: None):
            reset()
            with self.assertRaises(ValueError) as caught:
                routes.resolve_route(departure, Quiet(),
                                     random.Random(3))
            self.assertIn("already ran tonight", str(caught.exception))
        self.assertEqual(_snapshot(state), after_one)
        self.assertEqual(state.clean, 2032)
        self.assertEqual(len(state.route_log), 1)

    def test_a_hand_built_departure_still_cannot_run_red_or_elsewhere(self):
        """THE RESIDUAL, pinned at its real width rather than claimed
        away. `object.__new__` plus `object.__setattr__` will build any
        object in Python and no guard reaches past that — but the
        departure's own construction contract is RE-CHECKED at the
        claim, so what a hand-built one can still do is narrow: it
        cannot run a red district, cannot carry another district's
        market, and cannot run a plan the canonical contract refuses.
        What remains is a stale-but-legal market snapshot, in a process
        that already owns the engine."""
        def forge(state, view, plan):
            departure = object.__new__(routes.RouteDeparture)
            for name, value in (("state", state), ("plan", plan),
                                ("market", view),
                                ("identity", routes._fingerprint(plan))):
                object.__setattr__(departure, name, value)
            return departure

        red, drivers = _two_route_world(RED_HEAT)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        before = _snapshot(red)
        with self.assertRaises(ValueError) as caught:
            routes.resolve_route(
                forge(red, market.route_market(red, DISTRICT), plan),
                Quiet(), random.Random(3))
        self.assertIn("cannot run under 'red'", str(caught.exception))
        self.assertEqual(_snapshot(red), before)

        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        before = _snapshot(state)
        with self.assertRaises(ValueError) as caught:
            routes.resolve_route(
                forge(state, market.route_market(state, OTHER_DISTRICT),
                      plan), Quiet(), random.Random(3))
        self.assertIn("market for a route into", str(caught.exception))
        self.assertEqual(_snapshot(state), before)

    def test_a_refusal_leaves_the_departure_claimable(self):
        """Refusals mutate nothing — the departure included. A plan
        the canonical contract refuses must not spend the wagon on its
        way out, or a bug at resolution would silently cost the run."""
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        departure = departed(state, plan)
        cargo = dict(plan["cargo"])
        plan["cargo"]["mushrooms"] = 999      # past the wagon's capacity
        object.__setattr__(departure, "identity", routes._fingerprint(plan))
        before = _snapshot(state)
        with self.assertRaises(ValueError):
            routes.resolve_route(departure, Quiet(), random.Random(3))
        self.assertEqual(_snapshot(state), before)
        # …and the wagon is still there to send once the plan is legal.
        plan["cargo"].clear()
        plan["cargo"].update(cargo)
        object.__setattr__(departure, "identity", routes._fingerprint(plan))
        routes.resolve_route(departure, Quiet(), random.Random(3))
        self.assertEqual(len(state.route_log), 1)

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

    def test_the_committed_load_is_fingerprinted_too(self):
        """Identity is not enough. With district, origin, wagon and
        driver all untouched, raising `manifest.legit` from 0 to 2
        after departure moved clean cash 2000 → 2032."""
        state, drivers = _two_route_world(NEAR_RED)
        plan = routes.RoutePlan(
            district=DISTRICT, driver=drivers[0], ride_along=False,
            manifest=routes.RouteManifest(cargo={}, legit=0),
            origin_shop=HOME_SHOP_KEY, wagon_key=HOME_WAGON_KEY)
        state.clean = 2000
        departure = departed(state, plan)
        plan["legit"] = 2
        before = _snapshot(state)
        with self.assertRaises(ValueError) as caught:
            routes.resolve_route(departure, Quiet(), random.Random(3))
        self.assertIn("changed after it departed", str(caught.exception))
        self.assertEqual(_snapshot(state), before)

    def test_an_in_place_cargo_edit_is_caught(self):
        # The cargo MAP is fingerprinted item by item, so an edit that
        # leaves the length alone cannot slip past.
        state, drivers = _two_route_world(NEAR_RED)
        plan = _plan(drivers[0], HOME_SHOP_KEY, HOME_WAGON_KEY)
        departure = departed(state, plan)
        plan["cargo"]["mushrooms"] = 1
        before = _snapshot(state)
        with self.assertRaises(ValueError):
            routes.resolve_route(departure, Quiet(), random.Random(3))
        self.assertEqual(_snapshot(state), before)

    def test_a_departure_resolves_exactly_once(self):
        """A wagon goes out once. Resolving one empty-cargo, two-cover
        departure twice moved clean 2000 → 2032 → 2064, revenue
        0 → 32 → 64, and wrote two log rows for one night."""
        state, drivers = _two_route_world(NEAR_RED)
        plan = routes.RoutePlan(
            district=DISTRICT, driver=drivers[0], ride_along=False,
            manifest=routes.RouteManifest(cargo={}, legit=2),
            origin_shop=HOME_SHOP_KEY, wagon_key=HOME_WAGON_KEY)
        state.clean = 2000
        departure = departed(state, plan)
        routes.resolve_route(departure, Quiet(), random.Random(3))
        after_one = _snapshot(state)
        self.assertEqual(len(state.route_log), 1)
        with self.assertRaises(ValueError) as caught:
            routes.resolve_route(departure, Quiet(), random.Random(3))
        self.assertIn("already ran tonight", str(caught.exception))
        self.assertEqual(_snapshot(state), after_one)
        self.assertEqual(len(state.route_log), 1)

    def test_the_snapshot_is_actually_deep(self):
        # `state_to_dict` keeps `state.prices` BY REFERENCE, so the
        # hand-rolled version changed under its own feet.
        state, _drivers = _two_route_world(NEAR_RED)
        # Prices are rolled by the morning, not by `new_state`.
        market.roll_prices(state, random.Random(3))
        before = _snapshot(state)
        district = next(iter(state.prices))
        good = next(iter(state.prices[district]))
        state.prices[district][good] += 999
        self.assertEqual(before["prices"][district][good],
                         _snapshot(state)["prices"][district][good] - 999)

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
