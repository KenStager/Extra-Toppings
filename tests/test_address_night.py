"""P4a.3 — the night is address-local (design rev. 22 items 1 and 5,
rev. 23 item 2, rev. 27).

Routes name the address they left, raid warnings name the address they
are coming for, wagons are answered per address, and consequences land
where they were aimed. Behavior-neutral while one shop exists.
"""

import unittest

from extra_toppings import models, phases, save
from extra_toppings.models import (HOME_SHOP_KEY, HOME_WAGON_KEY,
                                   RaidWarning, RouteExecutionRecord,
                                   Shop, Wagon, new_state)


def two_addresses():
    state = new_state()
    state.shops.append(Shop(key="shop2", district="university"))
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

    def test_it_always_names_a_real_address(self):
        state, _home, _second = two_addresses()
        self.assertIn(models.raid_target(state, "vinnie"),
                      [s.key for s in state.shops])

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

    def test_a_record_written_before_origins_reads_as_the_founding_one(self):
        rec = RouteExecutionRecord(
            day=2, district="university", heat_band="cool",
            capacity_mult=1.0, units_sold=0, corner_damage_h=0,
            contested=False)
        self.assertEqual(rec.origin_shop, HOME_SHOP_KEY)


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


if __name__ == "__main__":
    unittest.main()
