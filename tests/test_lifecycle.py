"""P4b.1a — the address lifecycle authority (§2.4.2; rev. 29 items
3–4): the recorded dates, the phase derivation, the central capability
view, the wagon-claim refusal, and the save-load transitions.

These are SYNTHETIC two-address states, constructed deliberately: no
released branch can create one, which is exactly why they are built
here (§7's P4b.1a clause) — every defect this PR could introduce is
invisible to a one-shop run and to every green gate.
"""

import unittest

from extra_toppings import data, models, phases, save
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

    def test_improvements_are_disallowed_during_construction(self):
        # `phases._improvements` is address-bound: without a name in
        # the vocabulary the "only staffing and pantry supply" ruling
        # would hold in prose while a building site bought an oven.
        self.assertIn("improvements", ADDRESS_CAPABILITIES)
        state = _with_site(day=6, acceptance=5)
        self.assertFalse(address_allows(state.shop_by_key("shop2"),
                                        state.day, "improvements"))
        state.day = 7
        self.assertTrue(address_allows(state.shop_by_key("shop2"),
                                       state.day, "improvements"))

    def test_every_address_bound_surface_has_a_capability_name(self):
        # The vocabulary is the enforcement surface: a surface with no
        # name cannot be gated, and the gap is invisible until a
        # building site exercises it.
        for name in ("demand", "service", "routes", "cover",
                     "laundering", "rent", "rival_targeting",
                     "law_targeting", "contraband_storage",
                     "wagon_use", "staffing", "pantry_supply",
                     "improvements"):
            self.assertIn(name, ADDRESS_CAPABILITIES)

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

    def test_the_order_is_by_key_and_survives_reversal(self):
        # Menus will iterate this: storage order would let a save's
        # list position decide prompt order and therefore bot
        # decisions. Pinned BEFORE consumers spread — a key sorting
        # after the founding key proves it is not merely storage
        # order wearing a sort.
        state = _with_site(day=7, acceptance=5)
        state.shops.append(Shop(
            key="aaa_shop", district="meadows",
            acceptance_day=5, opening_day=5 + CONSTRUCTION_DAYS))
        state.wagons.append(Wagon(key="wagon3", shop_key="aaa_shop"))
        expected = ["aaa_shop", HOME_SHOP_KEY, "shop2"]
        self.assertEqual([s.key for s in open_shops(state)], expected)
        state.shops.reverse()
        self.assertEqual([s.key for s in open_shops(state)], expected)
        validate_addresses(state)


class TestWagonClaim(unittest.TestCase):
    def test_a_construction_wagon_refuses_with_visible_words(self):
        state = _with_site(day=6, acceptance=5)
        claim = wagon_claim(state, "wagon2")
        self.assertFalse(claim.available)
        self.assertIn("contractor's yard", claim.note)

    def test_the_refusal_speaks_the_district_label_never_its_key(self):
        # An internal identity in player prose ("the little_sicily
        # wagon") is the leak this pins shut. Every district with a
        # multi-word or underscored key is checked, because the two
        # spellings only diverge there.
        for district in data.DISTRICTS:
            state = new_state()
            state.day = 6
            state.shops.append(Shop(
                key="shop2", district=district,
                acceptance_day=5, opening_day=5 + CONSTRUCTION_DAYS))
            state.wagons.append(Wagon(key="wagon2", shop_key="shop2"))
            note = wagon_claim(state, "wagon2").note
            self.assertIn(data.DISTRICTS[district]["label"], note)
            self.assertNotIn("_", note)
            self.assertNotIn(district, note.replace(
                data.DISTRICTS[district]["label"], ""))

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


class TestTheNightLedgerObeysTheLifecycle(unittest.TestCase):
    """The two authorities compose: the lifecycle says whether a
    wagon may be claimed at all, the night ledger says whether tonight
    already spent it. Both bind at planning AND at execution, because
    `claim_at` reads `free_at` — there is no second path."""

    def test_a_construction_wagon_is_not_free_at_its_address(self):
        state = _with_site(day=6, acceptance=5)
        night = phases.WagonNight(state)
        self.assertEqual(night.free_at("shop2"), [])
        self.assertFalse(night.available_at("shop2"))

    def test_the_note_is_the_lifecycles_own_words(self):
        state = _with_site(day=6, acceptance=5)
        night = phases.WagonNight(state)
        self.assertIn("contractor's yard", night.note_at("shop2"))
        self.assertIn("University Hill", night.note_at("shop2"))

    def test_claiming_a_construction_wagon_fails_closed(self):
        # Execution revalidates: a consumer that acted on a stale
        # planning answer hits a refusal, never a silent grant.
        state = _with_site(day=6, acceptance=5)
        night = phases.WagonNight(state)
        with self.assertRaises(RuntimeError):
            night.claim_at("shop2", "route")

    def test_the_wagon_frees_the_morning_its_address_opens(self):
        state = _with_site(day=7, acceptance=5)
        night = phases.WagonNight(state)
        self.assertEqual([w.key for w in night.free_at("shop2")],
                         ["wagon2"])
        self.assertEqual(night.claim_at("shop2", "route"), "wagon2")
        self.assertEqual(night.note_at("shop2"),
                         phases.WAGON_NOTES["route"])

    def test_a_building_site_never_grounds_the_open_address(self):
        # Availability is per address: the home wagon is not held back
        # because a site across town is still being built.
        state = _with_site(day=6, acceptance=5)
        night = phases.WagonNight(state)
        self.assertTrue(night.available_at(HOME_SHOP_KEY))
        self.assertEqual(night.claim_at(HOME_SHOP_KEY, "route"),
                         models.HOME_WAGON_KEY)

    def test_a_spent_wagon_still_reports_the_job_that_took_it(self):
        # The lifecycle answer must not displace the night's reason
        # once a wagon is genuinely out.
        state = _with_site(day=7, acceptance=5)
        night = phases.WagonNight(state)
        night.claim_at("shop2", "salvage")
        self.assertEqual(night.note_at("shop2"),
                         phases.WAGON_NOTES["salvage"])
        self.assertFalse(night.available_at("shop2"))

    def test_one_shop_answers_exactly_as_before(self):
        # The behaviour-equivalence anchor for this surface: with one
        # address nothing the lifecycle adds can change an answer.
        state = new_state()
        night = phases.WagonNight(state)
        self.assertTrue(night.available_at(HOME_SHOP_KEY))
        self.assertEqual(night.note_at(HOME_SHOP_KEY), "")
        self.assertIs(night.view_at(HOME_SHOP_KEY).available, True)
        night.claim_at(HOME_SHOP_KEY, "route")
        self.assertFalse(night.available_at(HOME_SHOP_KEY))
        self.assertEqual(night.note_at(HOME_SHOP_KEY),
                         phases.WAGON_NOTES["route"])


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

    def test_an_acceptance_in_the_future_is_refused(self):
        # The deal is struck at a sit-down that already happened, so
        # an acceptance the run has not reached describes a
        # transaction nobody made. Refused, never clamped forward.
        state = self._valid()
        site = state.shop_by_key("shop2")
        site.acceptance_day = state.day + 1
        site.opening_day = site.acceptance_day + CONSTRUCTION_DAYS
        with self.assertRaises(ValueError) as caught:
            validate_addresses(state)
        self.assertIn("future", str(caught.exception))

    def test_an_acceptance_on_today_is_allowed(self):
        # The boundary the rule turns on: accepted TONIGHT is the
        # normal case P4b.1b creates, and must not be refused.
        state = _with_site(day=5, acceptance=5)
        validate_addresses(state)

    def test_the_construction_span_is_recorded_not_chosen(self):
        state = self._valid()
        site = state.shop_by_key("shop2")
        site.opening_day = site.acceptance_day + CONSTRUCTION_DAYS + 1
        with self.assertRaises(ValueError):
            validate_addresses(state)

    def test_only_the_founding_address_may_be_undated(self):
        # An undated second address silently claims to have been open
        # since the world began — a founding-open shop nobody founded.
        state = new_state()
        state.day = 6
        state.shops.append(Shop(key="shop2", district="university"))
        state.wagons.append(Wagon(key="wagon2", shop_key="shop2"))
        with self.assertRaises(ValueError) as caught:
            validate_addresses(state)
        self.assertIn("undated", str(caught.exception))

    def test_a_dated_founding_address_leaves_none_undated(self):
        # The rule binds at BOTH ends: zero undated addresses is as
        # malformed as two, because every world has exactly one shop
        # that was there before any deal.
        state = self._valid()
        home = state.shop_by_key(HOME_SHOP_KEY)
        home.acceptance_day = 1
        home.opening_day = 1 + CONSTRUCTION_DAYS
        with self.assertRaises(ValueError) as caught:
            validate_addresses(state)
        self.assertIn("undated", str(caught.exception))

    def test_the_sole_address_of_a_one_shop_world_stays_undated(self):
        # The absence migration is untouched: the released game's
        # every save carries exactly one undated address.
        validate_addresses(new_state())

    def test_a_validated_world_always_keeps_an_open_address(self):
        # The open-address guarantee is a CONSEQUENCE of the undated
        # rule, not a check of its own: an undated shop has no opening
        # day, so it is open on every day, and exactly one address is
        # always undated. Asserted as the property it is — over the
        # states validation actually admits — rather than through a
        # payload that only ever reached the undated refusal.
        for state in (new_state(),
                      _with_site(day=5, acceptance=5),   # site today
                      _with_site(day=6, acceptance=5),   # mid-build
                      _with_site(day=7, acceptance=5)):  # opened
            validate_addresses(state)
            self.assertTrue(any(shop_is_open(s, state.day)
                                for s in state.shops))


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
