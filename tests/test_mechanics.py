"""Targeted tests for subsystems the bots rarely reach on their own."""

import random
import unittest

from extra_toppings import models, data, market, raids, routes, shop
from extra_toppings.models import new_state
from extra_toppings.ui import BotConsole
from route_support import departed


def prepped_state(seed: int = 1):
    rng = random.Random(seed)
    state = new_state()
    market.roll_prices(state, rng)
    return state, rng


class TestRaids(unittest.TestCase):
    def _crew(self, state, n=3):
        crew = []
        for e in state.employees:
            if len(crew) == n:
                break
            e.hired = True
            e.aware = True
            crew.append(e)
        return crew

    def test_all_three_objectives_resolve(self):
        for objective in data.RAID_OBJECTIVES:
            for seed in range(8):
                state, rng = prepped_state(seed)
                con = BotConsole(random.Random(seed))
                team = self._crew(state)
                plan = {"rival": "vinnie", "objective": objective,
                        "team": list(team), "armed": seed % 2 == 0, "return_shop": models.HOME_SHOP_KEY}
                before = state.rivals["vinnie"].strength
                raids.run_raid(state, plan, con, rng)
                # A raid always leaves a mark on someone: rival weakened,
                # crew hurt, or heat raised.
                after = state.rivals["vinnie"].strength
                marked = (after < before
                          or any(e.injured_days for e in team)
                          or any(d.heat > 10 for d in state.districts.values()))
                self.assertTrue(marked, f"{objective} seed {seed} changed nothing")

    def test_steal_stock_fills_stash(self):
        state, rng = prepped_state(3)
        con = BotConsole(random.Random(99))   # seed where the crew gets through
        team = self._crew(state)
        for seed in range(20):
            state, rng = prepped_state(seed)
            team = self._crew(state)
            plan = {"rival": "vinnie", "objective": "steal_stock",
                    "team": team, "armed": False, "return_shop": models.HOME_SHOP_KEY}
            raids.run_raid(state, plan, con, rng)
            if sum(state.shop_stash.values()) > sum(data.START_STASH.values()):
                return   # at least one clean haul across seeds
        self.fail("steal_stock never produced a haul in 20 attempts")

    def test_incoming_raid_resolves(self):
        for seed in range(8):
            state, rng = prepped_state(seed)
            state.rivals["vinnie"].warning = models.RaidWarning(1, models.HOME_SHOP_KEY)
            state.dirty = 3000
            raids.incoming_raid(state, "vinnie", BotConsole(random.Random(seed)), rng)
            self.assertEqual(state.rivals["vinnie"].raid_warning, 0)
            self.assertGreaterEqual(state.dirty, 0)


class TestRoutes(unittest.TestCase):
    def test_auto_route_moves_product_or_fails_loudly(self):
        outcomes = set()
        for seed in range(30):
            state, rng = prepped_state(seed)
            driver = next(e for e in state.employees if e.hired and e.driving >= 4)
            driver.aware = True
            state.shop_stash = {}   # plan_route already moved cargo to the wagon
            plan = {"district": "university", "driver": driver,
                    "ride_along": False, "cargo": {"mushrooms": 10}, "legit": 8, "origin_shop": models.HOME_SHOP_KEY,
                "wagon_key": models.HOME_WAGON_KEY}
            departure = departed(state, plan)
            report = routes.resolve_route(departure, BotConsole(random.Random(seed)), rng)
            if report["busted"]:
                outcomes.add("busted")
            elif report["sold"]:
                outcomes.add("sold")
            total = report["sold"] + state.shop_stash.get("mushrooms", 0)
            robbed = any("jumped" in line for line in report["lines"])
            if not report["busted"] and not robbed:
                self.assertEqual(total, 10)   # goods are conserved
            else:
                self.assertLessEqual(total, 10)   # seizure/robbery only shrinks
        self.assertIn("sold", outcomes)

    def test_suspicious_routes_run_hotter(self):
        pure = routes.route_suspicion(10, 0)
        covered = routes.route_suspicion(3, 20)
        self.assertGreater(pure, covered)


class TestEconomy(unittest.TestCase):
    def test_laundering_ceiling_tracks_sales(self):
        state, _ = prepped_state()
        low = shop.believable_ceiling(state, state.shop, 400)
        high = shop.believable_ceiling(state, state.shop, 2000)
        self.assertGreater(high, low)
        state.shop.upgrades.add("books")
        self.assertGreater(shop.believable_ceiling(state, state.shop, 400), low)

    def test_oversell_depresses_next_day_price(self):
        heavy, light = [], []
        for seed in range(40):
            s, r = prepped_state(seed)
            market.record_sales(s, "university", "oregano", 12)
            market.roll_prices(s, r)
            heavy.append(s.prices["university"]["oregano"])
            s2, r2 = prepped_state(seed)
            market.roll_prices(s2, r2)
            light.append(s2.prices["university"]["oregano"])
        self.assertLess(sum(heavy) / len(heavy), sum(light) / len(light))


if __name__ == "__main__":
    unittest.main()
