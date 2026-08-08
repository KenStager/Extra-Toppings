"""P0 foundation: typed evidence, the accrual-time arrest latch, the
shops collection, save v3 and the v2 migration.

The behavioral gate for this refactor is the equivalence harness
(analysis/equivalence.py: 150 seeds x 2 bot profiles against pre-refactor
goldens); these tests pin the schema semantics themselves."""

import random
import unittest
from dataclasses import asdict

from extra_toppings import data, market, save
from extra_toppings.models import new_state
from extra_toppings.rng import Streams


def fresh(seed=1):
    rng = random.Random(seed)
    state = new_state()
    market.roll_prices(state, rng)
    return state, rng


class TestDerivedCase(unittest.TestCase):
    def test_case_is_the_sum_of_its_records(self):
        """Bit-for-bit the old running total: same amounts, same order."""
        state, _ = fresh()
        old_style = 0.0
        for amount, why in [(6, "walked out"), (0.5, ""), (0.5, ""),
                            (12.2, "walk-through"), (1.5, "pattern")]:
            state.add_case(amount, why)
            old_style = max(0.0, min(100.0, old_style + amount))
            self.assertEqual(state.case, old_style)

    def test_flags_render_exactly_like_v2(self):
        state, _ = fresh()
        state.day = 7
        state.add_case(6, "Rosa walked out knowing everything",
                       kind="witness", source="Rosa Delgado")
        state.add_case(0.5, "", kind="paper")     # routine ticks never render
        self.assertEqual(state.case_flags,
                         ["day 7: Rosa walked out knowing everything"])

    def test_display_clamps_at_100_but_records_keep_accruing(self):
        state, _ = fresh()
        state.game_over = "arrested"              # pre-latched; keep adding
        state.add_case(90, "a very bad month")
        state.add_case(60, "a worse one")
        self.assertEqual(state.case, 100.0)
        self.assertEqual(len(state.evidence), 2)


class TestArrestLatch(unittest.TestCase):
    def test_latch_fires_at_accrual_time(self):
        state, _ = fresh()
        state.add_case(99.5, "the file, nearly complete")
        self.assertIsNone(state.game_over)
        state.add_case(0.5, "", kind="paper")     # the tick that closes it
        self.assertEqual(state.game_over, "arrested")

    def test_latch_never_overwrites_a_decided_ending(self):
        state, _ = fresh()
        state.game_over = "kneecaps"
        state.add_case(100, "everything at once")
        self.assertEqual(state.game_over, "kneecaps")


class TestShopsCollection(unittest.TestCase):
    def test_singular_accessors_address_shop_zero(self):
        state, _ = fresh()
        self.assertIs(state.shop, state.shops[0])
        state.shop_stash = {"oregano": 3}
        self.assertEqual(state.shops[0].stash, {"oregano": 3})
        state.shop_stash["oregano"] += 1
        self.assertEqual(state.shops[0].stash["oregano"], 4)

    def test_new_state_opens_one_shop_in_old_harbor(self):
        state, _ = fresh()
        self.assertEqual(len(state.shops), 1)
        self.assertEqual(state.shop.district, data.HOME_DISTRICT)
        self.assertEqual(state.shop_stash, dict(data.START_STASH))


def v2_payload() -> dict:
    """An authentic version-2 save, shaped field-for-field like the v2
    serializer (save.py @ 3d79d17) wrote it. Employees, districts and
    rivals kept the same schema across versions, so they are borrowed
    from a fresh state; the shop and Case use the old flat shape."""
    state, _ = fresh(9)
    return {
        "version": 2,
        "day": 11, "clean": 2500, "dirty": 900, "debt": 4200,
        "shop": {"quality": "gourmet", "price": "standard",
                 "ingredients": 33, "pantry_quality": "standard",
                 "reputation": 41.5, "upgrades": ["books"],
                 "damage_days": 0, "coupon_days": 2},
        "shop_stash": {"oregano": 5, "mushrooms": 2},
        "warehouse": {"oregano": 4},
        "warehouse_cash": 300,
        "employees": [asdict(e) for e in state.employees],
        "districts": {k: asdict(d) for k, d in state.districts.items()},
        "rivals": {k: asdict(r) for k, r in state.rivals.items()},
        "prices": state.prices,
        "events": [],
        "case": 37.5,
        "case_flags": ["day 3: product seized in a traffic stop",
                       "day 9: the register claimed $4,000 beyond any "
                       "plausible night's sales"],
        "news": [], "game_over": None, "debt_paid_day": None,
        "total_laundered": 5100, "raids_led": 1, "kills": 0,
        "demand_shock": 1.02, "demand_today": 58, "delivery_pool": 20,
        "legit_revenue_today": 0,
    }


class TestV2Migration(unittest.TestCase):
    def test_v2_save_loads_with_case_and_flags_intact(self):
        loaded = save.state_from_dict(v2_payload())
        self.assertEqual(loaded.case, 37.5)
        self.assertEqual(loaded.case_flags, v2_payload()["case_flags"])
        self.assertEqual(loaded.shop.quality, "gourmet")
        self.assertEqual(loaded.shop.upgrades, {"books"})
        self.assertEqual(loaded.shop.district, data.HOME_DISTRICT)
        self.assertEqual(loaded.shop_stash, {"oregano": 5, "mushrooms": 2})
        self.assertEqual(loaded.act, 1)
        self.assertIsNone(loaded.branch)

    def test_migrated_state_resaves_as_v3_and_round_trips(self):
        loaded = save.state_from_dict(v2_payload())
        d3 = save.state_to_dict(loaded)
        self.assertEqual(d3["version"], 3)
        again = save.state_from_dict(d3)
        self.assertEqual(save.state_to_dict(again), d3)
        self.assertEqual(again.case, 37.5)

    def test_unknown_versions_are_refused(self):
        bad = v2_payload()
        bad["version"] = 1
        with self.assertRaises(ValueError):
            save.state_from_dict(bad)


class TestStreamMigration(unittest.TestCase):
    def test_missing_new_streams_stay_seed_fresh(self):
        s = Streams(7)
        s.routes.random()                          # a drawn shared stream
        payload = s.to_dict()
        for name in ("sitdown", "brokers", "war"):
            del payload["streams"][name]           # a v2-era payload
        restored = Streams.from_dict(payload)
        self.assertEqual(restored.routes.getstate(), s.routes.getstate())
        self.assertEqual(restored.war.getstate(),
                         random.Random("7/war").getstate())


if __name__ == "__main__":
    unittest.main()
