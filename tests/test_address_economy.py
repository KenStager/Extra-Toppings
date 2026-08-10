"""P4a.2 — the restaurant economy is address-local (design rev. 27
items 1-2). Storage names an address, the kitchen and its order book
belong to one shop, staff are assigned, rent counts addresses, and the
asset authorities see every room the player owns.

Behavior-neutral while one shop exists: every case here that a
one-shop world can reach must give the answer it always gave.
"""

import random
import unittest

from extra_toppings import data, models, phases, save, shop
from extra_toppings.models import (HOME_SHOP_KEY, Shop, Wagon, new_state)
from extra_toppings.ui import ScriptedConsole


def two_addresses():
    """A second address, wired up the way P4b will build it."""
    state = new_state()
    second = Shop(key="shop2", district="university")
    state.shops.append(second)
    state.wagons.append(Wagon(key="wagon2", shop_key="shop2"))
    return state, state.shops[0], second


class TestTheAssetAuthoritiesSeeEveryRoom(unittest.TestCase):
    """rev. 27 item 2: every stash plus the warehouse, exactly once."""

    def test_net_worth_counts_a_second_address(self):
        state, home, second = two_addresses()
        state.clean = state.dirty = state.warehouse_cash = 0
        state.debt = 0
        home.stash = {"mushrooms": 2}
        second.stash = {"mushrooms": 3}
        base = data.GOODS["mushrooms"]["base"]
        self.assertEqual(state.net_worth(), 5 * base)

    def test_total_stock_units_counts_a_second_address(self):
        state, home, second = two_addresses()
        home.stash = {"mushrooms": 2}
        second.stash = {"oregano": 4}
        self.assertEqual(state.total_stock_units(), 6)

    def test_the_warehouse_is_counted_exactly_once(self):
        state, home, second = two_addresses()
        state.clean = state.dirty = state.warehouse_cash = 0
        state.debt = 0
        home.stash = {}
        second.stash = {}
        state.warehouse = {"mushrooms": 3}
        base = data.GOODS["mushrooms"]["base"]
        self.assertEqual(state.net_worth(), 3 * base)
        self.assertEqual(state.total_stock_units(), 3)

    def test_one_shop_answers_exactly_as_before(self):
        state = new_state()
        state.shop_stash = {"mushrooms": 2}
        state.warehouse = {"oregano": 1}
        expected = (state.clean + state.dirty + state.warehouse_cash
                    + 2 * data.GOODS["mushrooms"]["base"]
                    + 1 * data.GOODS["oregano"]["base"] - state.debt)
        self.assertEqual(state.net_worth(), expected)
        self.assertEqual(state.total_stock_units(), 3)


class TestStorageNamesItsAddress(unittest.TestCase):
    def test_a_stash_is_reached_by_shop_key(self):
        state, home, second = two_addresses()
        home.stash = {"mushrooms": 1}
        second.stash = {"mushrooms": 2}
        self.assertEqual(models.space_used(
            models._stash_at(state, HOME_SHOP_KEY)),
            1 * data.GOODS["mushrooms"]["bulk"])
        self.assertEqual(models.space_used(
            models._stash_at(state, "shop2")),
            2 * data.GOODS["mushrooms"]["bulk"])

    def test_the_bare_shop_token_no_longer_resolves(self):
        # rev. 27 item 7: a location that does not say WHICH address
        # is the implicit home default, and it is gone.
        state = new_state()
        with self.assertRaises(ValueError):
            models.space_cap(state, "shop")
        with self.assertRaises(ValueError):
            models._stash_at(state, "shop")

    def test_moves_between_two_addresses_are_refused_for_now(self):
        # There is no free shop-to-shop transfer (rev. 22 item 9);
        # goods move by wagon or they do not move. P4a.2 leaves the
        # authority address-aware but adds no new route.
        state, home, second = two_addresses()
        home.stash = {"mushrooms": 4}
        before = (dict(home.stash), dict(second.stash))
        with self.assertRaises(ValueError):
            models.move_goods(state, HOME_SHOP_KEY, "shop2", "mushrooms", 1)
        self.assertEqual((home.stash, second.stash), before,
                         "a refused move leaves every stash untouched")

    def test_transfer_refusals_never_expose_a_key(self):
        # rev. 27 item 3: keys are internal. A refusal names the
        # warehouse or the shop by district, never shop1/shop2.
        state, home, second = two_addresses()
        home.stash = {"oregano": 1}
        state.warehouse = {}
        for args in ((HOME_SHOP_KEY, "shop2", "oregano", 1),
                     (HOME_SHOP_KEY, models.WAREHOUSE, "oregano", 5)):
            with self.assertRaises(ValueError) as caught:
                models.move_goods(state, *args)
            message = str(caught.exception)
            for key in (HOME_SHOP_KEY, "shop2"):
                self.assertNotIn(key, message,
                                 f"raw key leaked: {message}")
            self.assertIn("Old Harbor", message)

    def test_a_bogus_endpoint_is_an_unknown_location_not_a_bad_transfer(self):
        # Both endpoints preflight FIRST, so a non-location fails as
        # what it is rather than being misclassified.
        state, home, _second = two_addresses()
        home.stash = {"oregano": 1}
        # Both endpoints non-warehouse is the case that used to be
        # misread: the shop-to-shop rule fired before anything checked
        # that "atlantis" is not a place.
        with self.assertRaises(ValueError) as caught:
            models.move_goods(state, "atlantis", "shop2", "oregano", 1)
        self.assertIn("unknown storage location", str(caught.exception))
        self.assertNotIn("no direct transfer", str(caught.exception))

    def test_storage_locations_lists_every_address(self):
        state, _home, _second = two_addresses()
        self.assertEqual(models.storage_locations(state),
                         (HOME_SHOP_KEY, "shop2", models.WAREHOUSE))

    def test_a_second_addresss_overfull_room_is_refused_at_validation(self):
        state, _home, second = two_addresses()
        models.validate_cross_state(state)          # baseline passes
        second.stash = {"mushrooms": 10_000}
        with self.assertRaises(ValueError) as caught:
            models.validate_cross_state(state)
        self.assertIn("space used over", str(caught.exception))


class TestTheKitchenBelongsToOneAddress(unittest.TestCase):
    def test_each_address_keeps_its_own_order_book(self):
        state, home, second = two_addresses()
        shop.roll_demand(state, random.Random(4))
        # Both were computed; neither wrote the other's row.
        self.assertGreater(home.demand_today, 0)
        self.assertGreater(second.demand_today, 0)
        home.price = "gourmet"
        shop.recompute_demand(state, home)
        self.assertGreater(second.demand_today, 0)

    def test_demand_reads_the_addresss_own_district(self):
        state, home, second = two_addresses()
        self.assertNotEqual(home.district, second.district)
        shop.roll_demand(state, random.Random(4))
        # Traffic differs by district, so the two books differ even
        # with identical policy and one shared shock.
        self.assertNotEqual(home.demand_today, second.demand_today)

    def test_the_shock_is_one_roll_for_the_city(self):
        # rev. 22 item 6: a day's weather is a world fact.
        state, _home, _second = two_addresses()
        shop.roll_demand(state, random.Random(4))
        first = state.demand_shock
        state2, _h, _s = two_addresses()
        shop.roll_demand(state2, random.Random(4))
        self.assertEqual(first, state2.demand_shock)

    def test_the_shift_banks_revenue_at_the_address_that_earned_it(self):
        state, home, second = two_addresses()
        shop.roll_demand(state, random.Random(4))
        home.ingredients = second.ingredients = 40
        shop.simulate_shift(state, second, 0, random.Random(1))
        self.assertEqual(home.legit_revenue_today, 0,
                         "the home till must not take shop 2's money")
        self.assertGreater(second.legit_revenue_today, 0)

    def test_heat_lands_on_the_addresss_own_district(self):
        state, _home, second = two_addresses()
        second.upgrades = {"late_license"}
        shop.roll_demand(state, random.Random(4))
        second.ingredients = 40
        before_home = state.heat(data.HOME_DISTRICT)
        before_second = state.heat(second.district)
        shop.simulate_shift(state, second, 0, random.Random(1))
        self.assertEqual(state.heat(data.HOME_DISTRICT), before_home)
        self.assertGreater(state.heat(second.district), before_second)


class TestStaffAreAssigned(unittest.TestCase):
    def test_a_cook_serves_only_their_own_kitchen(self):
        state, home, second = two_addresses()
        cook = next(e for e in state.employees if e.role == "cook")
        cook.hired = True
        cook.shop_key = HOME_SHOP_KEY
        self.assertGreater(shop.cooks_skill(state, home), 2)
        self.assertEqual(shop.cooks_skill(state, second), 2,
                         "an unstaffed kitchen bakes at the floor")

    def test_reassignment_moves_the_skill(self):
        state, home, second = two_addresses()
        cook = next(e for e in state.employees if e.role == "cook")
        cook.hired = True
        cook.shop_key = "shop2"
        self.assertEqual(shop.cooks_skill(state, home), 2)
        self.assertGreater(shop.cooks_skill(state, second), 2)

    def test_an_assignment_to_no_real_address_is_refused(self):
        # The ghost-shop repro: it used to load fine, and then every
        # kitchen quietly ran at the no-cook floor.
        state, _home, _second = two_addresses()
        models.validate_addresses(state)               # baseline
        state.employees[0].shop_key = "ghost-shop"
        with self.assertRaises(ValueError) as caught:
            models.validate_addresses(state)
        self.assertIn("unknown address", str(caught.exception))

    def test_even_an_unhired_employee_must_work_somewhere_real(self):
        state, _home, _second = two_addresses()
        ghost = next(e for e in state.employees if not e.hired)
        ghost.shop_key = "ghost-shop"
        with self.assertRaises(ValueError):
            models.validate_addresses(state)

    def test_a_ghost_assignment_is_refused_at_load(self):
        state, _home, _second = two_addresses()
        pristine = save.state_to_dict(state)
        save.state_from_dict(pristine)                 # baseline loads
        doctored = save.state_to_dict(state)
        doctored["employees"][0]["shop_key"] = "ghost-shop"
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(doctored)
        self.assertIn("unknown address", str(caught.exception))

    def test_a_second_address_assignment_round_trips(self):
        state, _home, _second = two_addresses()
        cook = next(e for e in state.employees if e.role == "cook")
        cook.hired = True
        cook.shop_key = "shop2"
        back = save.state_from_dict(save.state_to_dict(state))
        restored = next(e for e in back.employees if e.key == cook.key)
        self.assertEqual(restored.shop_key, "shop2")
        self.assertGreater(shop.cooks_skill(back, back.shop_by_key("shop2")), 2)
        self.assertEqual(shop.cooks_skill(back, back.shop_by_key(HOME_SHOP_KEY)), 2)

    def test_everyone_starts_at_the_founding_address(self):
        state = new_state()
        self.assertTrue(all(e.shop_key == HOME_SHOP_KEY
                            for e in state.employees))


class TestRentAndCeilingCountAddresses(unittest.TestCase):
    def test_rent_is_charged_per_open_address(self):
        state, _home, _second = two_addresses()
        state.clean = 100_000
        before = state.clean
        phases._payroll_and_rent(state, ScriptedConsole([]))
        wages = sum(e.wage for e in state.hired() if not e.arrested)
        self.assertEqual(before - state.clean,
                         wages + data.RENT_PER_DAY * 2)

    def test_one_address_pays_exactly_one_rent(self):
        state = new_state()
        state.clean = 100_000
        before = state.clean
        phases._payroll_and_rent(state, ScriptedConsole([]))
        wages = sum(e.wage for e in state.hired() if not e.arrested)
        self.assertEqual(before - state.clean, wages + data.RENT_PER_DAY)

    def test_the_nightly_ceiling_sums_the_addresses(self):
        state, home, second = two_addresses()
        home.legit_revenue_today = 400
        second.legit_revenue_today = 600
        self.assertEqual(
            shop.total_believable_ceiling(state),
            shop.believable_ceiling(state, home, 400)
            + shop.believable_ceiling(state, second, 600))

    def test_books_helps_only_the_address_that_bought_it(self):
        state, home, second = two_addresses()
        home.upgrades = {"books"}
        self.assertGreater(shop.believable_ceiling(state, home, 1000),
                           shop.believable_ceiling(state, second, 1000))

    def test_one_address_ceiling_is_unchanged(self):
        state = new_state()
        state.shop.legit_revenue_today = 500
        self.assertEqual(shop.total_believable_ceiling(state),
                         shop.believable_ceiling(state, state.shop, 500))


if __name__ == "__main__":
    unittest.main()
