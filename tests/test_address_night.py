"""P4a.3 — the night is address-local (design rev. 22 items 1 and 5,
rev. 23 item 2, rev. 27).

Routes name the address they left, raid warnings name the address they
are coming for, wagons are answered per address, and consequences land
where they were aimed. Behavior-neutral while one shop exists.
"""

import random
import unittest

from extra_toppings import models, phases, save
from extra_toppings.models import (HOME_SHOP_KEY, HOME_WAGON_KEY,
                                   RaidWarning, RouteExecutionRecord,
                                   Shop, Wagon, new_state)
from extra_toppings.ui import ScriptedConsole


def two_addresses():
    # The second address carries its lifecycle dates (P4b.1a): only
    # the founding shop may be undated, and the calendar sits after
    # the opening day so this is the OPEN, operating second address
    # every test below is about.
    # The dates sit as early as the rule allows (acceptance >= day 1,
    # opening = acceptance + 2) because tests below wind the calendar
    # back to day 5, and an acceptance the run has not reached is
    # refused. Day 3 is the earliest a second address can be open.
    state = new_state()
    state.day = 3
    state.shops.append(Shop(key="shop2", district="university",
                            acceptance_day=1, opening_day=3))
    state.wagons.append(Wagon(key="wagon2", shop_key="shop2"))
    return state, state.shops[0], state.shops[1]


class TestTheTypedWarning(unittest.TestCase):
    def test_it_carries_its_address(self):
        w = RaidWarning(3, HOME_SHOP_KEY)
        self.assertEqual((w.nights, w.shop_key), (3, HOME_SHOP_KEY))

    def test_counting_down_keeps_the_address(self):
        w = RaidWarning(3, "shop2").counted_down()
        self.assertEqual((w.nights, w.shop_key), (2, "shop2"))

    def test_the_last_night_counts_down_to_nothing(self):
        self.assertIsNone(RaidWarning(1, "shop2").counted_down())

    def test_an_impossible_countdown_is_refused(self):
        for bad in (0, -1, 1.5, True):
            with self.assertRaises(ValueError, msg=repr(bad)):
                RaidWarning(bad, HOME_SHOP_KEY)

    def test_a_warning_naming_nowhere_is_refused(self):
        with self.assertRaises(ValueError):
            RaidWarning(2, "")

    def test_it_is_frozen(self):
        w = RaidWarning(2, HOME_SHOP_KEY)
        with self.assertRaises(Exception):
            w.shop_key = "shop2"          # type: ignore[misc]

    def test_raid_warning_is_a_derived_read(self):
        state = new_state()
        rv = state.rivals["vinnie"]
        self.assertEqual(rv.raid_warning, 0)
        rv.warning = RaidWarning(2, HOME_SHOP_KEY)
        self.assertEqual(rv.raid_warning, 2)
        # Derived: there is no second field to disagree with it.
        with self.assertRaises(AttributeError):
            rv.raid_warning = 5           # type: ignore[misc]

    def test_a_warning_naming_a_vanished_address_is_refused(self):
        state, _home, _second = two_addresses()
        models.validate_addresses(state)                  # baseline
        state.rivals["vinnie"].warning = RaidWarning(2, "ghost")
        with self.assertRaises(ValueError) as caught:
            models.validate_addresses(state)
        self.assertIn("unknown", str(caught.exception))

    def test_it_round_trips_and_cannot_be_retargeted_by_a_reload(self):
        state, _home, _second = two_addresses()
        state.rivals["vinnie"].warning = RaidWarning(2, "shop2")
        back = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(back.rivals["vinnie"].warning,
                         RaidWarning(2, "shop2"))

    def test_a_pre_typed_payload_migrates_to_the_one_address(self):
        state = new_state()
        payload = save.state_to_dict(state)
        payload["rivals"]["vinnie"].pop("warning", None)
        payload["rivals"]["vinnie"]["raid_warning"] = 2
        back = save.state_from_dict(payload)
        self.assertEqual(back.rivals["vinnie"].warning,
                         RaidWarning(2, HOME_SHOP_KEY))


class TestTheTargetAuthority(unittest.TestCase):
    def test_one_address_is_the_answer(self):
        state = new_state()
        self.assertEqual(models.raid_target(state, "vinnie"),
                         HOME_SHOP_KEY)

    def test_several_addresses_are_refused_not_picked_by_position(self):
        # P4b owns the "softer shop" policy (rev. 27 item 4). Choosing
        # one here would be choosing by LIST POSITION — reversing
        # state.shops would move the raid — so P4a fails closed.
        state, _home, _second = two_addresses()
        with self.assertRaises(ValueError) as caught:
            models.raid_target(state, "vinnie")
        self.assertIn("no targeting policy", str(caught.exception))
        state.shops.reverse()
        with self.assertRaises(ValueError):
            models.raid_target(state, "vinnie")

    def test_no_address_is_refused_not_defaulted(self):
        state = new_state()
        state.shops = []
        with self.assertRaises(ValueError):
            models.raid_target(state, "vinnie")


class TestRouteOrigin(unittest.TestCase):
    def _rec(self, day, origin):
        return RouteExecutionRecord(
            day=day, district="university", heat_band="cool",
            capacity_mult=1.0, units_sold=0, corner_damage_h=0,
            contested=False, origin_shop=origin)

    def test_a_record_carries_its_origin(self):
        self.assertEqual(self._rec(3, "shop2").origin_shop, "shop2")

    def test_an_origin_must_be_named(self):
        with self.assertRaises(ValueError):
            self._rec(3, "")

    def test_one_address_still_runs_one_route_a_night(self):
        state, _home, _second = two_addresses()
        state.day = 5
        state.route_log = [self._rec(3, HOME_SHOP_KEY),
                           self._rec(3, HOME_SHOP_KEY)]
        with self.assertRaises(ValueError) as caught:
            models.validate_execution_history(state)
        self.assertIn("one route per address", str(caught.exception))

    def test_two_addresses_may_each_run_one_the_same_night(self):
        state, _home, _second = two_addresses()
        state.day = 5
        state.route_log = [self._rec(3, HOME_SHOP_KEY),
                           self._rec(3, "shop2")]
        models.validate_execution_history(state)      # legal

    def test_routes_stay_in_calendar_order(self):
        state, _home, _second = two_addresses()
        state.day = 9
        state.route_log = [self._rec(5, HOME_SHOP_KEY),
                           self._rec(3, "shop2")]
        with self.assertRaises(ValueError) as caught:
            models.validate_execution_history(state)
        self.assertIn("calendar order", str(caught.exception))

    def test_raids_are_still_one_a_night_whatever_the_addresses(self):
        state, _home, _second = two_addresses()
        state.day = 5
        state.raid_log = [
            models.RaidAttemptRecord(day=3, rival="vinnie",
                                     outcome="scrubbed", crew=1,
                                     damage_h=0),
            models.RaidAttemptRecord(day=3, rival="sal",
                                     outcome="scrubbed", crew=1,
                                     damage_h=0)]
        with self.assertRaises(ValueError) as caught:
            models.validate_execution_history(state)
        self.assertIn("one job a night", str(caught.exception))

    def test_an_origin_naming_no_address_is_refused_at_validation(self):
        state, _home, _second = two_addresses()
        state.day = 5
        state.route_log = [self._rec(2, HOME_SHOP_KEY)]
        models.validate_execution_history(state)          # baseline
        state.route_log = [self._rec(2, "ghost")]
        with self.assertRaises(ValueError) as caught:
            models.validate_execution_history(state)
        self.assertIn("not an address", str(caught.exception))

    def test_a_ghost_origin_is_refused_at_load(self):
        state, _home, _second = two_addresses()
        state.day = 5
        state.route_log = [self._rec(2, HOME_SHOP_KEY)]
        save.state_from_dict(save.state_to_dict(state))    # baseline
        state.route_log = [self._rec(2, "ghost")]
        with self.assertRaises(ValueError):
            save.state_from_dict(save.state_to_dict(state))

    def test_a_record_that_names_no_origin_cannot_be_built_at_all(self):
        # The founding-address assumption used to live in the record's
        # own default, where every caller inherited it. It now lives at
        # the save migration and nowhere else.
        with self.assertRaises(TypeError):
            RouteExecutionRecord(                  # type: ignore[call-arg]
                day=2, district="university", heat_band="cool",
                capacity_mult=1.0, units_sold=0, corner_damage_h=0,
                contested=False)

    def test_a_pre_origin_record_migrates_at_the_one_address_boundary(self):
        state = new_state()
        state.day = 5
        state.route_log = [self._rec(2, HOME_SHOP_KEY)]
        payload = save.state_to_dict(state)
        self.assertEqual(save.state_from_dict(payload).route_log[0]
                         .origin_shop, HOME_SHOP_KEY)      # baseline
        del payload["route_log"][0]["origin_shop"]
        back = save.state_from_dict(payload)
        self.assertEqual(back.route_log[0].origin_shop, HOME_SHOP_KEY)

    def test_a_pre_origin_record_is_refused_in_a_multi_address_save(self):
        state, _home, _second = two_addresses()
        state.day = 5
        state.route_log = [self._rec(2, HOME_SHOP_KEY)]
        payload = save.state_to_dict(state)
        save.state_from_dict(payload)                      # baseline
        del payload["route_log"][0]["origin_shop"]
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(payload)
        self.assertIn("cannot be inferred", str(caught.exception))


class TestRouteCommitmentLoadsWhereThePlanSaid(unittest.TestCase):
    """The bug this pins: service resolved ONE address at its boundary
    and spent that address's stash and pantry, whatever origin the plan
    named. A route planned out of the second shop emptied the first
    shop's shelves, and a plan naming an address that does not exist
    committed successfully."""

    def _plan(self, driver, origin, **over):
        plan = {"district": "old_harbor", "driver": driver,
                "ride_along": False, "cargo": {"mushrooms": 2},
                "legit": 3, "origin_shop": origin,
                "wagon_key": ("wagon2" if origin == "shop2"
                              else HOME_WAGON_KEY)}
        plan.update(over)
        return plan

    def _world(self):
        state, home, second = two_addresses()
        state.day = 6
        driver = next(e for e in state.employees
                      if e.name.startswith("Rosa"))
        driver.hired = True
        for s in (home, second):
            s.stash = {"mushrooms": 4}
            s.ingredients = 40
            s.delivery_pool = 10
        return state, home, second, driver

    def test_it_loads_out_of_the_address_the_plan_named(self):
        state, home, second, driver = self._world()
        self.assertTrue(phases._commit_route(
            state, self._plan(driver, "shop2"), ScriptedConsole(),
            phases.WagonNight(state)))
        self.assertEqual(second.stash["mushrooms"], 2)
        self.assertEqual(second.ingredients, 37)
        self.assertEqual(home.stash["mushrooms"], 4)
        self.assertEqual(home.ingredients, 40)

    def test_a_ghost_origin_refuses_before_anything_is_spent(self):
        state, home, second, driver = self._world()
        with self.assertRaises(KeyError):
            phases._commit_route(state, self._plan(driver, "shop9"),
                                 ScriptedConsole(),
                                 phases.WagonNight(state))
        for s in (home, second):
            self.assertEqual(s.stash["mushrooms"], 4)
            self.assertEqual(s.ingredients, 40)

    def test_an_unnamed_origin_refuses_before_anything_is_spent(self):
        state, home, second, driver = self._world()
        plan = self._plan(driver, "shop2")
        del plan["origin_shop"]
        with self.assertRaises(ValueError):
            phases._commit_route(state, plan, ScriptedConsole(), phases.WagonNight(state))
        for s in (home, second):
            self.assertEqual(s.stash["mushrooms"], 4)
            self.assertEqual(s.ingredients, 40)


class TestRouteResolutionReadsTheSameOrigin(unittest.TestCase):
    """Commitment and resolution are two chances to spend the wrong
    address's night. Both read the plan, and both refuse the same two
    ways."""

    def _plan(self, driver, origin):
        plan = {"district": "old_harbor", "driver": driver,
                "ride_along": False, "cargo": {}, "legit": 2,
                "origin_shop": origin,
                "wagon_key": ("wagon2" if origin == "shop2"
                              else HOME_WAGON_KEY)}
        if origin is None:
            del plan["origin_shop"]
        return plan

    def _world(self):
        state, home, second = two_addresses()
        state.day = 6
        driver = next(e for e in state.employees
                      if e.name.startswith("Rosa"))
        driver.hired = True
        for s in (home, second):
            s.legit_revenue_today = 0
        return state, home, second, driver

    def test_a_ghost_origin_refuses_at_resolution(self):
        from extra_toppings import routes
        state, home, second, driver = self._world()
        with self.assertRaises(KeyError):
            routes.resolve_route(state, self._plan(driver, "shop9"),
                                 ScriptedConsole(), random.Random(3))
        for s in (home, second):
            self.assertEqual(s.legit_revenue_today, 0)

    def test_an_unnamed_origin_refuses_at_resolution(self):
        from extra_toppings import routes
        state, home, second, driver = self._world()
        # The canonical contract speaks first now: a missing field is
        # a malformed plan (ValueError), not a lookup miss.
        with self.assertRaises(ValueError):
            routes.resolve_route(state, self._plan(driver, None),
                                 ScriptedConsole(), random.Random(3))
        for s in (home, second):
            self.assertEqual(s.legit_revenue_today, 0)

    def test_the_named_address_books_the_cover_revenue(self):
        from extra_toppings import routes
        state, home, second, driver = self._world()
        routes.resolve_route(state, self._plan(driver, "shop2"),
                             ScriptedConsole(), random.Random(3))
        self.assertGreater(second.legit_revenue_today, 0)
        self.assertEqual(home.legit_revenue_today, 0)


class TestTheMigrationReadsPresenceNotTruthiness(unittest.TestCase):
    """The migration's licence is "this field did not exist yet", not
    "this field is falsy". Saves written before addresses had
    identities OMITTED these fields; none of them carried an empty
    one. So an ABSENT reference migrates and a PRESENT-but-unusable
    one is a malformed save — it must reach canonical validation and
    be refused, never be quietly repaired into a plausible payload.

    Each row doctors ONE field of a one-address save and proves the
    pristine payload round-trips first, so the refusal is attributable
    to the doctoring and not to the fixture."""

    def _payload(self):
        state = new_state()
        state.day = 5
        state.route_log = [RouteExecutionRecord(
            day=2, district="university", heat_band="cool",
            capacity_mult=1.0, units_sold=0, corner_damage_h=0,
            contested=False, origin_shop=HOME_SHOP_KEY)]
        payload = save.state_to_dict(state)
        save.state_from_dict(payload)                      # baseline
        return payload

    # (what, where the reference lives, the field's name)
    ROWS = (("a shop", lambda p: p["shops"][0], "key"),
            ("an employee", lambda p: p["employees"][0], "shop_key"),
            ("a wagon", lambda p: p["wagons"][0], "shop_key"),
            ("a route record", lambda p: p["route_log"][0],
             "origin_shop"))

    def test_an_absent_reference_migrates_to_the_one_address(self):
        for what, where, field in self.ROWS:
            with self.subTest(what):
                payload = self._payload()
                del where(payload)[field]
                back = save.state_from_dict(payload)
                self.assertEqual(back.shops[0].key, HOME_SHOP_KEY)
                self.assertEqual(back.employees[0].shop_key,
                                 HOME_SHOP_KEY)
                self.assertEqual(back.wagons[0].shop_key, HOME_SHOP_KEY)
                self.assertEqual(back.route_log[0].origin_shop,
                                 HOME_SHOP_KEY)

    def test_a_present_but_unusable_reference_is_refused(self):
        for what, where, field in self.ROWS:
            for bad in ("", None, False):
                with self.subTest(f"{what}.{field}={bad!r}"):
                    payload = self._payload()
                    where(payload)[field] = bad
                    with self.assertRaises(ValueError):
                        save.state_from_dict(payload)

    def test_the_refusal_names_the_reference_not_the_migration(self):
        # The message must read as "this save is broken", not as
        # "this save is old" — they call for different responses.
        payload = self._payload()
        payload["employees"][0]["shop_key"] = ""
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(payload)
        self.assertIn("unknown address", str(caught.exception))
        self.assertNotIn("cannot be inferred", str(caught.exception))


class TestTheWarningSchemaIsAnExactUnion(unittest.TestCase):
    """A telegraphed raid is the loudest thing on the board: the
    player has been told a crew is coming and has spent nights
    preparing. Erasing one across a reload, or inventing one that was
    never telegraphed, is a story failure — so the two spellings are
    an exact union, and neither coerces."""

    def _payload(self, **rival):
        state = new_state()
        payload = save.state_to_dict(state)
        v = payload["rivals"]["vinnie"]
        v.pop("warning", None)
        v.update(rival)
        return payload

    def test_the_canonical_spelling_round_trips(self):
        state = new_state()
        state.rivals["vinnie"].warning = RaidWarning(2, HOME_SHOP_KEY)
        back = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(back.rivals["vinnie"].warning,
                         RaidWarning(2, HOME_SHOP_KEY))

    def test_a_legacy_countdown_migrates(self):
        back = save.state_from_dict(self._payload(raid_warning=2))
        self.assertEqual(back.rivals["vinnie"].warning,
                         RaidWarning(2, HOME_SHOP_KEY))

    def test_a_legacy_zero_always_meant_no_raid(self):
        back = save.state_from_dict(self._payload(raid_warning=0))
        self.assertIsNone(back.rivals["vinnie"].warning)

    def test_a_malformed_countdown_is_refused_never_read_as_none(self):
        # Every one of these used to load as "no raid coming".
        for bad in ("", None, False, [], {}, -1):
            with self.subTest(repr(bad)):
                with self.assertRaises(ValueError):
                    save.state_from_dict(self._payload(raid_warning=bad))

    def test_a_countdown_is_never_coerced_into_one(self):
        # "2" used to become two nights, 1.5 and True one night. A
        # save that says something impossible is malformed, not a
        # rounding problem.
        for bad in ("2", 1.5, True, 2.0):
            with self.subTest(repr(bad)):
                with self.assertRaises(ValueError):
                    save.state_from_dict(self._payload(raid_warning=bad))

    def test_a_malformed_typed_warning_is_refused(self):
        for bad in ("2", 2, [], False):
            with self.subTest(repr(bad)):
                with self.assertRaises(ValueError):
                    save.state_from_dict(self._payload(warning=bad))

    def test_carrying_both_spellings_is_refused(self):
        payload = self._payload(warning=None, raid_warning=2)
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(payload)
        self.assertIn("both", str(caught.exception))

    def test_carrying_neither_spelling_is_refused(self):
        payload = self._payload()          # both keys removed
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(payload)
        self.assertIn("no warning field", str(caught.exception))


class TestALedgerIsAbsentOrItIsAList(unittest.TestCase):
    """`d.get(name) or []` read a malformed ledger as "nothing ever
    happened" — the quietest way to lose a whole campaign's record."""

    def _payload(self):
        state = new_state()
        state.day = 5
        state.route_log = [RouteExecutionRecord(
            day=2, district="university", heat_band="cool",
            capacity_mult=1.0, units_sold=0, corner_damage_h=0,
            contested=False, origin_shop=HOME_SHOP_KEY)]
        state.raid_log = [models.RaidAttemptRecord(
            day=3, rival="vinnie", outcome="scrubbed", crew=1,
            damage_h=0)]
        payload = save.state_to_dict(state)
        save.state_from_dict(payload)                      # baseline
        return payload

    def test_an_absent_ledger_migrates_to_empty(self):
        for name in ("raid_log", "route_log"):
            with self.subTest(name):
                payload = self._payload()
                del payload[name]
                back = save.state_from_dict(payload)
                self.assertEqual(getattr(back, name), [])

    def test_a_present_empty_ledger_is_still_empty(self):
        for name in ("raid_log", "route_log"):
            with self.subTest(name):
                payload = self._payload()
                payload[name] = []
                self.assertEqual(
                    getattr(save.state_from_dict(payload), name), [])

    def test_a_present_non_list_ledger_is_refused(self):
        for name in ("raid_log", "route_log"):
            for bad in (None, False, "", {}, 0):
                with self.subTest(f"{name}={bad!r}"):
                    payload = self._payload()
                    payload[name] = bad
                    with self.assertRaises(ValueError) as caught:
                        save.state_from_dict(payload)
                    self.assertIn("ledger is a list",
                                  str(caught.exception))


class TestNothingOutsideTheSaveInfersAnAddress(unittest.TestCase):
    """rev. 27 item 7, enforced at the type: the founding address is
    named where the world is built and inferred where a one-address
    payload is migrated. Every other construction must say which
    address it means."""

    # The founding constants may be NAMED in exactly three scopes:
    # the State defaults and new_state, which build the world, and
    # state_from_dict, which migrates a one-address payload. Anywhere
    # else they are the old silent default wearing a constant's name —
    # which is how a defect survives a refactor that claims to end it.
    SANCTIONED = {"models.py:State", "models.py:new_state",
                  "save.py:state_from_dict"}

    def test_the_founding_keys_are_named_only_where_they_may_be(self):
        import ast
        import pathlib
        root = pathlib.Path(models.__file__).parent
        seen = set()
        for path in sorted(root.glob("*.py")):
            tree = ast.parse(path.read_text(), filename=str(path))
            scopes: dict = {}

            def walk(node, scope):
                for child in ast.iter_child_nodes(node):
                    here = child.name if isinstance(
                        child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                ast.ClassDef)) else scope
                    scopes[id(child)] = here
                    walk(child, here)

            walk(tree, "<module>")
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) \
                        and node.id in ("HOME_SHOP_KEY", "HOME_WAGON_KEY") \
                        and scopes.get(id(node)) != "<module>":
                    seen.add(f"{path.name}:{scopes.get(id(node))}")
                elif isinstance(node, ast.Attribute) \
                        and node.attr in ("HOME_SHOP_KEY", "HOME_WAGON_KEY"):
                    seen.add(f"{path.name}:{scopes.get(id(node))}")
        self.assertEqual(seen, self.SANCTIONED)

    def test_a_shop_must_say_which_address_it_is(self):
        with self.assertRaises(TypeError):
            Shop()                            # type: ignore[call-arg]

    def test_a_wagon_must_say_which_one_it_is_and_where_it_is_kept(self):
        with self.assertRaises(TypeError):
            Wagon()                           # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            Wagon(key="wagon2")               # type: ignore[call-arg]

    def test_an_employee_must_say_where_they_work(self):
        with self.assertRaises(TypeError):
            models.Employee(                  # type: ignore[call-arg]
                key="e0", name="Nobody", role="cook", food=1, driving=1,
                nerve=1, loyalty=1, trait="", wage=10, bio="")

    def test_a_route_plan_must_say_where_the_wagon_loads(self):
        from extra_toppings import routes
        with self.assertRaises(TypeError):
            routes.RoutePlan(                 # type: ignore[call-arg]
                district="old_harbor", driver=None, ride_along=False,
                manifest=routes.RouteManifest())

    def test_a_multi_address_save_missing_an_employee_address_refuses(self):
        state, _home, _second = two_addresses()
        payload = save.state_to_dict(state)
        save.state_from_dict(payload)                      # baseline
        del payload["employees"][0]["shop_key"]
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(payload)
        self.assertIn("cannot be inferred", str(caught.exception))

    def test_a_multi_address_save_missing_a_wagon_address_refuses(self):
        state, _home, _second = two_addresses()
        payload = save.state_to_dict(state)
        save.state_from_dict(payload)                      # baseline
        del payload["wagons"][0]["shop_key"]
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(payload)
        self.assertIn("cannot be inferred", str(caught.exception))

    def test_a_multi_address_save_missing_a_shop_key_refuses(self):
        state, _home, _second = two_addresses()
        payload = save.state_to_dict(state)
        save.state_from_dict(payload)                      # baseline
        del payload["shops"][1]["key"]
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(payload)
        self.assertIn("cannot be inferred", str(caught.exception))

    def test_a_multi_address_save_with_an_untargeted_warning_refuses(self):
        state, _home, _second = two_addresses()
        payload = save.state_to_dict(state)
        save.state_from_dict(payload)                      # baseline
        payload["rivals"]["vinnie"].pop("warning", None)
        payload["rivals"]["vinnie"]["raid_warning"] = 2
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(payload)
        self.assertIn("cannot be inferred", str(caught.exception))

    def test_a_one_address_save_keyed_otherwise_infers_ITS_key(self):
        # The migration means "the only address there was", not "the
        # home key by reflex" — inferring shop1 into a lone shop2
        # would mint a reference to an address that does not exist.
        state = new_state()
        state.shops[0].key = "shop2"
        state.wagons[0].shop_key = "shop2"
        for e in state.employees:
            e.shop_key = "shop2"
        payload = save.state_to_dict(state)
        save.state_from_dict(payload)                      # baseline
        for e in payload["employees"]:
            e.pop("shop_key", None)
        del payload["wagons"]
        back = save.state_from_dict(payload)
        self.assertTrue(all(e.shop_key == "shop2"
                            for e in back.employees))
        self.assertEqual([w.shop_key for w in back.wagons], ["shop2"])


class TestAddressedHaul(unittest.TestCase):
    def test_the_haul_lands_where_the_crew_returned(self):
        state, home, second = two_addresses()
        kept, left = models.place_haul(state, {"mushrooms": 3}, "shop2")
        self.assertEqual(second.stash.get("mushrooms"), 3)
        self.assertEqual(home.stash.get("mushrooms"), None)
        self.assertEqual((kept, left), ({"mushrooms": 3}, 0))

    def test_an_unknown_destination_is_refused(self):
        state, _home, _second = two_addresses()
        with self.assertRaises(KeyError):
            models.place_haul(state, {"mushrooms": 1}, "ghost")

    def test_a_refusal_places_nothing(self):
        state, home, second = two_addresses()
        before = (dict(home.stash), dict(second.stash))
        with self.assertRaises(KeyError):
            models.place_haul(state, {"mushrooms": 1}, "ghost")
        self.assertEqual((home.stash, second.stash), before)


class TestTheWagonFleet(unittest.TestCase):
    def test_each_address_answers_for_itself(self):
        state, _home, _second = two_addresses()
        fleet = phases.WagonNight(state)
        self.assertTrue(fleet.available_at(HOME_SHOP_KEY))
        self.assertTrue(fleet.available_at("shop2"))
        fleet.claim_at(HOME_SHOP_KEY, "route")
        self.assertFalse(fleet.available_at(HOME_SHOP_KEY))
        self.assertTrue(fleet.available_at("shop2"),
                        "one address's wagon must not ground another")

    def test_the_claim_returns_the_wagon_it_took(self):
        state, _home, _second = two_addresses()
        fleet = phases.WagonNight(state)
        self.assertEqual(fleet.claim_at(HOME_SHOP_KEY, "route"),
                         HOME_WAGON_KEY)
        self.assertEqual(fleet.claim_at("shop2", "salvage"), "wagon2")

    def test_a_second_wagon_at_one_address_covers_a_second_job(self):
        state, _home, _second = two_addresses()
        state.wagons.append(Wagon(key="wagon3", shop_key=HOME_SHOP_KEY))
        fleet = phases.WagonNight(state)
        fleet.claim_at(HOME_SHOP_KEY, "route")
        self.assertTrue(fleet.available_at(HOME_SHOP_KEY))
        fleet.claim_at(HOME_SHOP_KEY, "raid")
        self.assertFalse(fleet.available_at(HOME_SHOP_KEY))

    def test_the_view_never_contradicts_itself(self):
        state, _home, _second = two_addresses()
        fleet = phases.WagonNight(state)
        for key in (HOME_SHOP_KEY, "shop2"):
            view = fleet.view_at(key)
            self.assertTrue(view.available)
            self.assertEqual(view.note, "")
        fleet.claim_at("shop2", "decoy")
        view = fleet.view_at("shop2")
        self.assertFalse(view.available)
        self.assertEqual(view.note, "already loaded and gone")



class TestTheBoundaryIsClosed(unittest.TestCase):
    """rev. 27 item 6: by the end of P4a.3 no production module reads
    the one-shop aliases, and no identity-based answer depends on the
    order shops or wagons happen to sit in a list."""

    # The five one-shop aliases, by the name they are READ under —
    # not by the receiver they happen to be read from. `state.shop`
    # and `s.shop` are the same defect; a guard that only knows the
    # first spelling certifies nothing.
    ALIASES = ("shop", "shop_stash", "demand_today", "delivery_pool",
               "legit_revenue_today")

    def test_the_aliases_are_still_the_five_this_guard_knows(self):
        # If an alias is renamed or retired, this guard must be told —
        # silently guarding names that no longer exist would pass
        # forever while the real ones went unwatched.
        for name in self.ALIASES:
            self.assertIsInstance(vars(models.State).get(name), property,
                                  f"{name} is no longer a State alias")

    def test_no_production_module_names_an_alias_on_any_receiver(self):
        """Static half: `.shop` and `.shop_stash` exist ONLY as State
        aliases — no other type in the engine has either — so any
        attribute of that name, on any receiver whatsoever, is an
        alias read. The other three collide with real Shop fields and
        cannot be judged from the text; the runtime half below judges
        them exactly."""
        import ast
        import pathlib
        root = pathlib.Path(models.__file__).parent
        offenders = []
        for path in sorted(root.glob("*.py")):
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) \
                        and node.attr in ("shop", "shop_stash"):
                    offenders.append(f"{path.name}:{node.lineno}: "
                                     f".{node.attr}")
        self.assertEqual(offenders, [],
                         "P4a.3 leaves no production alias reads")

    def test_no_production_module_touches_an_alias_while_playing(self):
        """Runtime half: the aliases themselves report who read them.
        This is blind to spelling, to the receiver's name and to
        getattr indirection — it records the file and line of whatever
        actually reached the property during a full game, a save
        round-trip and world creation."""
        import pathlib
        import random
        import sys
        from extra_toppings import game
        from extra_toppings.bot import BOTS

        package = pathlib.Path(models.__file__).resolve().parent
        offenders: set = set()

        def instrumented(name, prop):
            def record():
                fr = sys._getframe(2)   # record → fget/fset → the reader
                path = pathlib.Path(fr.f_code.co_filename).resolve()
                if path.parent == package:
                    offenders.add(f"{path.name}:{fr.f_lineno}: .{name}")

            def fget(self):
                record()
                return prop.fget(self)

            if prop.fset is None:
                return property(fget)

            def fset(self, value):
                record()
                prop.fset(self, value)

            return property(fget, fset)

        original = {n: vars(models.State)[n] for n in self.ALIASES}
        for name, prop in original.items():
            setattr(models.State, name, instrumented(name, prop))
        try:
            new_state()
            for seed in (0, 1, 2):
                con = BOTS["greedy"](random.Random(seed), verbose=False)
                end = game.run(seed, con)
                save.state_from_dict(save.state_to_dict(end))
        finally:
            for name, prop in original.items():
                setattr(models.State, name, prop)
        self.assertEqual(sorted(offenders), [],
                         "no production module reads a one-shop alias "
                         "during a played game")

    def test_reordering_shops_changes_no_identity_answer(self):
        state, _home, _second = two_addresses()
        state.shops[0].stash = {"mushrooms": 2}
        state.shops[1].stash = {"oregano": 3}
        before = (state.net_worth(), state.total_stock_units(),
                  models.storage_locations(state),
                  [w.key for w in state.wagons_at(HOME_SHOP_KEY)],
                  models.space_cap(state, "shop2"))
        state.shops.reverse()
        state.wagons.reverse()
        after = (state.net_worth(), state.total_stock_units(),
                 tuple(sorted(models.storage_locations(state))),
                 [w.key for w in state.wagons_at(HOME_SHOP_KEY)],
                 models.space_cap(state, "shop2"))
        self.assertEqual(before[0], after[0])
        self.assertEqual(before[1], after[1])
        self.assertEqual(tuple(sorted(before[2])), after[2])
        self.assertEqual(before[3], after[3])
        self.assertEqual(before[4], after[4])

    def test_an_old_one_address_save_still_loads(self):
        # The one place inference is allowed: the save boundary.
        state = new_state()
        payload = save.state_to_dict(state)
        del payload["wagons"]
        del payload["shops"][0]["key"]
        for r in payload["rivals"].values():
            # A pre-typed payload did not omit the warning — it stored
            # the bare countdown, 0 for "none". Deleting the field
            # instead modelled a save no version ever wrote.
            r.pop("warning", None)
            r["raid_warning"] = 0
        for e in payload["employees"]:
            e.pop("shop_key", None)
        back = save.state_from_dict(payload)
        self.assertEqual(back.shops[0].key, HOME_SHOP_KEY)
        self.assertEqual([w.key for w in back.wagons], [HOME_WAGON_KEY])
        self.assertTrue(all(e.shop_key == HOME_SHOP_KEY
                            for e in back.employees))


if __name__ == "__main__":
    unittest.main()
