"""P4b.1a — the address lifecycle authority (§2.4.2; rev. 29 items
3–4): the recorded dates, the phase derivation, the central capability
view, the wagon-claim refusal, and the save-load transitions.

These are SYNTHETIC two-address states, constructed deliberately: no
released branch can create one, which is exactly why they are built
here (§7's P4b.1a clause) — every defect this PR could introduce is
invisible to a one-shop run and to every green gate.
"""

import unittest

from extra_toppings import models, save
from extra_toppings.models import (ADDRESS_CAPABILITIES,
                                   CONSTRUCTION_ALLOWED,
                                   CONSTRUCTION_DAYS, HOME_SHOP_KEY,
                                   Shop, Wagon, address_allows,
                                   new_state, open_shops, shop_is_open,
                                   validate_addresses, wagon_claim)


def _with_site(day: int, acceptance: int) -> models.State:
    """A synthetic world: the founding shop plus a second address
    accepted on `acceptance`, with its wagon — the pair the atomic
    transaction (P4b.1b) will create together."""
    state = new_state()
    state.day = day
    state.shops.append(Shop(
        key="shop2", district="university", reputation=20.0,
        ingredients=0, stash={},
        acceptance_day=acceptance,
        opening_day=acceptance + CONSTRUCTION_DAYS))
    state.wagons.append(Wagon(key="wagon2", shop_key="shop2"))
    return state


class TestLifecycleDerivation(unittest.TestCase):
    def test_a_founding_address_is_open_since_the_world_began(self):
        state = new_state()
        home = state.shop_by_key(HOME_SHOP_KEY)
        self.assertIsNone(home.acceptance_day)
        self.assertIsNone(home.opening_day)
        for day in (1, 15, 30):
            self.assertTrue(shop_is_open(home, day))

    def test_a_site_stands_until_its_recorded_opening_day(self):
        state = _with_site(day=5, acceptance=5)
        site = state.shop_by_key("shop2")
        self.assertFalse(shop_is_open(site, 5))     # accepted tonight
        self.assertFalse(shop_is_open(site, 6))     # under construction
        self.assertTrue(shop_is_open(site, 7))      # opens THAT morning
        self.assertTrue(shop_is_open(site, 30))     # and cannot close

    def test_the_phase_is_derived_never_stored(self):
        # No boolean rides the record: the same address answers
        # differently as the calendar advances, from the dates alone.
        state = _with_site(day=6, acceptance=5)
        site = state.shop_by_key("shop2")
        self.assertFalse(shop_is_open(site, state.day))
        state.day = 7
        self.assertTrue(shop_is_open(site, state.day))


class TestCapabilityMatrix(unittest.TestCase):
    """§2.4.2's capability ruling as a complete matrix — every
    capability × both phases, one authority answering."""

    def test_an_open_address_does_everything(self):
        state = new_state()
        home = state.shop_by_key(HOME_SHOP_KEY)
        for cap in ADDRESS_CAPABILITIES:
            self.assertTrue(address_allows(home, state.day, cap), cap)

    def test_a_building_site_only_prepares(self):
        state = _with_site(day=6, acceptance=5)
        site = state.shop_by_key("shop2")
        for cap in ADDRESS_CAPABILITIES:
            expected = cap in CONSTRUCTION_ALLOWED
            self.assertEqual(address_allows(site, state.day, cap),
                             expected, cap)

    def test_construction_allows_exactly_staffing_and_pantry(self):
        # The ALLOWED set is part of the ruling, not an implementation
        # detail: a capability quietly added here would let a building
        # site do something §2.4.2 disallows.
        self.assertEqual(CONSTRUCTION_ALLOWED,
                         frozenset({"staffing", "pantry_supply"}))

    def test_opening_enables_the_complete_address_in_one_transition(self):
        state = _with_site(day=7, acceptance=5)
        site = state.shop_by_key("shop2")
        for cap in ADDRESS_CAPABILITIES:
            self.assertTrue(address_allows(site, state.day, cap), cap)

    def test_an_unknown_capability_is_refused_in_both_phases(self):
        state = _with_site(day=6, acceptance=5)
        for shop_key in (HOME_SHOP_KEY, "shop2"):
            with self.assertRaises(ValueError):
                address_allows(state.shop_by_key(shop_key), state.day,
                               "demolition")


class TestOpenShopsFiltering(unittest.TestCase):
    def test_one_open_shop_filters_to_exactly_the_shops_list(self):
        # THE behaviour-equivalence anchor: while every address is
        # open, filtering is the identity — same objects, same order.
        state = new_state()
        self.assertEqual(open_shops(state), state.shops)
        self.assertIs(open_shops(state)[0], state.shops[0])

    def test_a_building_site_is_filtered_out_until_it_opens(self):
        state = _with_site(day=6, acceptance=5)
        self.assertEqual([s.key for s in open_shops(state)],
                         [HOME_SHOP_KEY])
        state.day = 7
        self.assertEqual([s.key for s in open_shops(state)],
                         [HOME_SHOP_KEY, "shop2"])


class TestWagonClaim(unittest.TestCase):
    def test_a_construction_wagon_refuses_with_visible_words(self):
        state = _with_site(day=6, acceptance=5)
        claim = wagon_claim(state, "wagon2")
        self.assertFalse(claim.available)
        self.assertIn("contractor's yard", claim.note)

    def test_the_refusal_lifts_the_morning_the_address_opens(self):
        state = _with_site(day=7, acceptance=5)
        self.assertIs(wagon_claim(state, "wagon2"), models.WAGON_FREE)

    def test_the_founding_wagon_is_always_claimable(self):
        state = new_state()
        self.assertIs(wagon_claim(state, models.HOME_WAGON_KEY),
                      models.WAGON_FREE)

    def test_an_unknown_wagon_fails_closed(self):
        state = new_state()
        with self.assertRaises(KeyError):
            wagon_claim(state, "nowagon")


class TestLifecycleValidation(unittest.TestCase):
    def _valid(self) -> models.State:
        return _with_site(day=6, acceptance=5)

    def test_a_valid_two_address_state_passes(self):
        validate_addresses(self._valid())

    def test_one_date_without_the_other_is_refused(self):
        for acc, opn in ((5, None), (None, 7)):
            state = self._valid()
            site = state.shop_by_key("shop2")
            site.acceptance_day, site.opening_day = acc, opn
            with self.assertRaises(ValueError):
                validate_addresses(state)

    def test_a_boolean_is_not_a_calendar_day(self):
        state = self._valid()
        site = state.shop_by_key("shop2")
        site.acceptance_day, site.opening_day = True, 3
        with self.assertRaises(ValueError):
            validate_addresses(state)

    def test_a_string_is_not_a_calendar_day(self):
        state = self._valid()
        site = state.shop_by_key("shop2")
        site.acceptance_day, site.opening_day = "5", "7"
        with self.assertRaises(ValueError):
            validate_addresses(state)

    def test_an_acceptance_before_the_calendar_is_refused(self):
        state = self._valid()
        site = state.shop_by_key("shop2")
        site.acceptance_day, site.opening_day = 0, CONSTRUCTION_DAYS
        with self.assertRaises(ValueError):
            validate_addresses(state)

    def test_the_construction_span_is_recorded_not_chosen(self):
        state = self._valid()
        site = state.shop_by_key("shop2")
        site.opening_day = site.acceptance_day + CONSTRUCTION_DAYS + 1
        with self.assertRaises(ValueError):
            validate_addresses(state)

    def test_a_world_of_building_sites_is_refused(self):
        # Morning, service and night need a subject: the founding
        # shop is open by construction, and no path un-opens an
        # address, so every-shop-under-construction is malformed.
        state = new_state()
        home = state.shop_by_key(HOME_SHOP_KEY)
        home.acceptance_day = state.day
        home.opening_day = state.day + CONSTRUCTION_DAYS
        with self.assertRaises(ValueError):
            validate_addresses(state)


class TestLifecycleSaveLoad(unittest.TestCase):
    def test_the_dates_survive_a_round_trip_exactly(self):
        state = _with_site(day=6, acceptance=5)
        loaded = save.state_from_dict(save.state_to_dict(state))
        site = loaded.shop_by_key("shop2")
        self.assertEqual(site.acceptance_day, 5)
        self.assertEqual(site.opening_day, 5 + CONSTRUCTION_DAYS)
        self.assertFalse(shop_is_open(site, loaded.day))

    def test_a_reload_neither_opens_nor_unopens_an_address(self):
        # The transition is derived from the persisted dates, never
        # from a stored flag a reload could lose: the same payload
        # answers by the calendar it carries.
        state = _with_site(day=6, acceptance=5)
        loaded = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual([s.key for s in open_shops(loaded)],
                         [HOME_SHOP_KEY])
        loaded.day = 7
        self.assertEqual([s.key for s in open_shops(loaded)],
                         [HOME_SHOP_KEY, "shop2"])

    def test_an_absent_field_migrates_as_the_founding_state(self):
        # Every payload written before the Partner branch existed
        # omits both fields; absence is history, and it loads open.
        payload = save.state_to_dict(new_state())
        for s in payload["shops"]:
            del s["acceptance_day"]
            del s["opening_day"]
        loaded = save.state_from_dict(payload)
        home = loaded.shop_by_key(HOME_SHOP_KEY)
        self.assertIsNone(home.acceptance_day)
        self.assertIsNone(home.opening_day)
        self.assertTrue(shop_is_open(home, loaded.day))

    def test_a_present_but_malformed_date_refuses_at_load(self):
        # Presence, never truthiness: a payload CLAIMING dates must
        # carry coherent ones — repairing them would silently open or
        # un-open an address.
        state = _with_site(day=6, acceptance=5)
        good = save.state_to_dict(state)
        for doctor in (
            lambda s: s.update(opening_day=9),          # span broken
            lambda s: s.update(acceptance_day=None),    # one without
            lambda s: s.update(acceptance_day=True,     # bool day
                               opening_day=3),
        ):
            payload = save.state_to_dict(state)
            self.assertEqual(payload, good)             # fresh copy
            doctor(payload["shops"][1])
            with self.assertRaises(ValueError):
                save.state_from_dict(payload)


if __name__ == "__main__":
    unittest.main()
