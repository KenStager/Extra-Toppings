"""P4a.1 — addresses and wagons have stable identities (design
rev. 27 item 1), the lookups fail closed (item 7), and the one-shop
compatibility aliases refuse both ends through one authority (item 6).

Nothing here is player-facing: P4a is narratively invisible, so these
pin structure and refusals, never prose.
"""

import unittest

from extra_toppings import models, save
from extra_toppings.models import (HOME_SHOP_KEY, HOME_WAGON_KEY, Shop,
                                   Wagon, exactly_one_shop, new_state,
                                   validate_addresses)


class TestStableIdentities(unittest.TestCase):
    def test_a_fresh_state_names_its_address_and_wagon(self):
        state = new_state()
        self.assertEqual([s.key for s in state.shops], [HOME_SHOP_KEY])
        self.assertEqual([w.key for w in state.wagons], [HOME_WAGON_KEY])
        self.assertEqual(state.wagons[0].shop_key, HOME_SHOP_KEY)

    def test_the_key_is_not_the_list_position(self):
        # The whole point: identity survives reordering.
        state = new_state()
        state.shops.append(Shop(key="shop2"))
        state.wagons.append(Wagon(key="wagon2", shop_key="shop2"))
        state.shops.reverse()
        self.assertIs(state.shop_by_key("shop2"), state.shops[0])
        self.assertIs(state.shop_by_key(HOME_SHOP_KEY), state.shops[1])

    def test_lookups_fail_closed_on_an_unknown_key(self):
        state = new_state()
        with self.assertRaises(KeyError):
            state.shop_by_key("nowhere")
        with self.assertRaises(KeyError):
            state.wagon_by_key("nowagon")
        with self.assertRaises(KeyError):
            state.wagons_at("nowhere")

    def test_an_ambiguous_key_is_refused_not_resolved_by_position(self):
        # Returning the first of several duplicates would quietly
        # reinstate list position as the identity — the exact thing
        # stable keys abolish.
        state = new_state()
        state.shops.append(Shop(key=HOME_SHOP_KEY))
        with self.assertRaises(KeyError) as caught:
            state.shop_by_key(HOME_SHOP_KEY)
        self.assertIn("ambiguous", str(caught.exception))
        state2 = new_state()
        state2.wagons.append(Wagon(key=HOME_WAGON_KEY, shop_key=HOME_SHOP_KEY))
        with self.assertRaises(KeyError) as caught:
            state2.wagon_by_key(HOME_WAGON_KEY)
        self.assertIn("ambiguous", str(caught.exception))

    def test_wagons_at_is_ordered_by_key_not_by_storage(self):
        state = new_state()
        state.shops.append(Shop(key="shop2"))
        state.wagons.append(Wagon(key="wagon3", shop_key="shop2"))
        state.wagons.append(Wagon(key="wagon2", shop_key="shop2"))
        expected = ["wagon2", "wagon3"]
        self.assertEqual([w.key for w in state.wagons_at("shop2")],
                         expected)
        state.wagons.reverse()
        self.assertEqual([w.key for w in state.wagons_at("shop2")],
                         expected, "storage order must not leak out")

    def test_wagons_at_lists_only_that_address(self):
        state = new_state()
        state.shops.append(Shop(key="shop2"))
        state.wagons.append(Wagon(key="wagon2", shop_key="shop2"))
        self.assertEqual([w.key for w in state.wagons_at(HOME_SHOP_KEY)],
                         [HOME_WAGON_KEY])
        self.assertEqual([w.key for w in state.wagons_at("shop2")],
                         ["wagon2"])


class TestTheOneShopAliasesRefuseBothEnds(unittest.TestCase):
    """rev. 27 item 6: no address is as malformed as several."""

    def test_one_shop_is_returned(self):
        state = new_state()
        self.assertIs(exactly_one_shop(state), state.shops[0])
        self.assertIs(state.shop, state.shops[0])

    def test_zero_shops_is_refused(self):
        state = new_state()
        state.shops = []
        with self.assertRaises(ValueError) as caught:
            _ = state.shop
        self.assertIn("no shop", str(caught.exception))

    def test_two_shops_are_refused(self):
        state = new_state()
        state.shops.append(Shop(key="shop2"))
        for read in (lambda s: s.shop,
                     lambda s: s.shop_stash,
                     lambda s: s.demand_today,
                     lambda s: s.delivery_pool,
                     lambda s: s.legit_revenue_today):
            with self.assertRaises(ValueError):
                read(state)

    def test_the_setters_refuse_too(self):
        # A silent write to shops[0] is the exact bug this prevents:
        # the second address's takings banked in the first's till.
        state = new_state()
        state.shops.append(Shop(key="shop2"))
        with self.assertRaises(ValueError):
            state.demand_today = 5
        with self.assertRaises(ValueError):
            state.delivery_pool = 5
        with self.assertRaises(ValueError):
            state.legit_revenue_today = 5
        with self.assertRaises(ValueError):
            state.shop_stash = {}


class TestAddressValidation(unittest.TestCase):
    def _valid(self):
        state = new_state()
        validate_addresses(state)          # the baseline must pass
        return state

    def test_a_pristine_state_validates(self):
        self._valid()

    def test_duplicate_shop_keys_are_refused(self):
        state = self._valid()
        state.shops.append(Shop(key=HOME_SHOP_KEY))
        with self.assertRaises(ValueError) as caught:
            validate_addresses(state)
        self.assertIn("duplicate shop key", str(caught.exception))

    def test_duplicate_wagon_keys_are_refused(self):
        state = self._valid()
        state.wagons.append(Wagon(key=HOME_WAGON_KEY, shop_key=HOME_SHOP_KEY))
        with self.assertRaises(ValueError) as caught:
            validate_addresses(state)
        self.assertIn("duplicate wagon key", str(caught.exception))

    def test_a_wagon_kept_at_no_address_is_refused(self):
        state = self._valid()
        state.wagons.append(Wagon(key="wagon2", shop_key="shop9"))
        with self.assertRaises(ValueError) as caught:
            validate_addresses(state)
        self.assertIn("unknown address", str(caught.exception))

    def test_an_empty_key_is_refused(self):
        state = self._valid()
        state.shops[0].key = ""
        with self.assertRaises(ValueError):
            validate_addresses(state)

    def test_a_non_string_key_is_refused(self):
        state = self._valid()
        state.shops[0].key = 1
        with self.assertRaises(ValueError):
            validate_addresses(state)

    def test_an_address_in_no_real_district_is_refused(self):
        state = self._valid()
        state.shops[0].district = "atlantis"
        with self.assertRaises(ValueError) as caught:
            validate_addresses(state)
        self.assertIn("unknown district", str(caught.exception))

    def test_an_address_keeping_no_wagon_is_refused(self):
        # Canon buys the address and its wagon in one transaction —
        # including from acceptance, while the site is still being
        # built (rev. 29 item 3), which is why a DATED second address
        # with no wagon is the case that proves this rule. The dates
        # are what let it reach the wagon check at all: an undated
        # second address is refused earlier, by the founding-address
        # rule (P4b.1a).
        state = self._valid()
        state.shops.append(Shop(key="shop2", acceptance_day=1,
                                opening_day=3))
        with self.assertRaises(ValueError) as caught:
            validate_addresses(state)
        self.assertIn("keeps no wagon", str(caught.exception))

    def test_an_empty_wagon_list_is_refused(self):
        state = self._valid()
        state.wagons = []
        with self.assertRaises(ValueError) as caught:
            validate_addresses(state)
        self.assertIn("keeps no wagon", str(caught.exception))

    def test_a_state_with_no_shop_is_refused(self):
        state = self._valid()
        state.shops = []
        with self.assertRaises(ValueError):
            validate_addresses(state)


class TestPersistence(unittest.TestCase):
    def test_identities_survive_the_round_trip(self):
        state = new_state()
        state.shops[0].key = HOME_SHOP_KEY
        payload = save.state_to_dict(state)
        self.assertEqual(payload["shops"][0]["key"], HOME_SHOP_KEY)
        self.assertEqual(payload["wagons"],
                         [{"key": HOME_WAGON_KEY,
                           "shop_key": HOME_SHOP_KEY}])
        back = save.state_from_dict(payload)
        self.assertEqual(back.shops[0].key, HOME_SHOP_KEY)
        self.assertEqual(back.wagons[0].key, HOME_WAGON_KEY)

    def test_a_v3_payload_without_identities_migrates(self):
        # Written before addresses had keys: exactly one shop, so the
        # home key is the only identity it could have carried.
        state = new_state()
        payload = save.state_to_dict(state)
        del payload["wagons"]
        del payload["shops"][0]["key"]
        back = save.state_from_dict(payload)
        self.assertEqual(back.shops[0].key, HOME_SHOP_KEY)
        self.assertEqual([w.key for w in back.wagons], [HOME_WAGON_KEY])
        self.assertEqual(back.wagons[0].shop_key, HOME_SHOP_KEY)

    def test_a_malformed_identity_is_refused_at_load(self):
        state = new_state()
        pristine = save.state_to_dict(state)
        # PROVE the untouched payload round-trips before asserting a
        # rejection, so the refusal is caused by the mutation alone.
        save.state_from_dict(pristine)
        doctored = save.state_to_dict(state)
        doctored["wagons"] = [{"key": HOME_WAGON_KEY,
                               "shop_key": "a-shop-that-never-existed"}]
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(doctored)
        self.assertIn("unknown address", str(caught.exception))

    def test_a_wagonless_address_is_refused_at_load(self):
        state = new_state()
        save.state_from_dict(save.state_to_dict(state))   # baseline
        doctored = save.state_to_dict(state)
        doctored["wagons"] = []
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(doctored)
        self.assertIn("keeps no wagon", str(caught.exception))

    def test_an_ambiguous_wagon_identity_is_refused_at_load(self):
        state = new_state()
        save.state_from_dict(save.state_to_dict(state))   # baseline
        doctored = save.state_to_dict(state)
        doctored["wagons"].append(dict(doctored["wagons"][0]))
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(doctored)
        self.assertIn("duplicate wagon key", str(caught.exception))

    def test_duplicate_keys_are_refused_at_load(self):
        state = new_state()
        save.state_from_dict(save.state_to_dict(state))   # baseline
        doctored = save.state_to_dict(state)
        doctored["shops"].append(dict(doctored["shops"][0]))
        with self.assertRaises(ValueError):
            save.state_from_dict(doctored)

    def test_an_uninterpretable_wagon_migration_is_refused(self):
        # Two addresses and no wagon list cannot be honestly read, so
        # the loader refuses rather than attaching it to shops[0].
        state = new_state()
        payload = save.state_to_dict(state)
        payload["shops"].append({**payload["shops"][0], "key": "shop2"})
        del payload["wagons"]
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(payload)
        self.assertIn("cannot infer", str(caught.exception))

    def test_a_v2_save_still_migrates_and_gains_identity(self):
        state = new_state()
        v3 = save.state_to_dict(state)
        shop = dict(v3["shops"][0])
        v2 = {k: v for k, v in v3.items()
              if k not in ("shops", "wagons", "evidence")}
        v2["version"] = 2
        v2["shop"] = {k: v for k, v in shop.items()
                      if k not in ("stash", "district", "demand_today",
                                   "delivery_pool", "legit_revenue_today",
                                   "key")}
        v2["shop_stash"] = shop["stash"]
        v2["demand_today"] = shop["demand_today"]
        v2["delivery_pool"] = shop["delivery_pool"]
        v2["legit_revenue_today"] = shop["legit_revenue_today"]
        v2["case"] = 0
        v2["case_flags"] = []
        back = save.state_from_dict(v2)
        self.assertEqual(back.shops[0].key, HOME_SHOP_KEY)
        self.assertEqual(back.shops[0].district, models.data.HOME_DISTRICT)
        self.assertEqual([w.key for w in back.wagons], [HOME_WAGON_KEY])


if __name__ == "__main__":
    unittest.main()
