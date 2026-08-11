"""P0 foundation: typed evidence, the accrual-time arrest latch, the
shops collection, save v3 and the v2 migration.

The behavioral gate for this refactor is the equivalence harness
(analysis/equivalence.py: 150 seeds x 2 bot profiles against pre-refactor
goldens); these tests pin the schema semantics themselves."""

import random
import unittest

from extra_toppings import data, market, save
from extra_toppings.models import (BranchState, PointsCycleRecord,
                                   new_state)
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

    def test_fold_matches_the_sequential_total_where_sum_would_not(self):
        """Python 3.12 moved sum() to compensated (Neumaier) summation.
        This game-plausible sequence folds to 61.50000000000001
        sequentially but sums to 61.5 compensated — the Case must keep
        the explicit left-to-right fold, or golden identity breaks on
        3.12+ (found as 15/300 equivalence failures in review)."""
        state, _ = fresh()
        for amount in [10.0, 5.0, 14.6, 0.5, 8.3, 9.2, 0.5, 8.9, 3.0, 1.5]:
            state.add_case(amount, "x")
        self.assertEqual(state.case, 61.50000000000001)

    def test_flags_render_exactly_like_v2(self):
        state, _ = fresh()
        state.day = 7
        state.add_case(6, "Rosa walked out knowing everything",
                       kind="witness", source="e0")
        state.add_case(0.5, "", kind="paper")     # routine ticks never render
        self.assertEqual(state.case_flags,
                         ["day 7: Rosa walked out knowing everything"])

    def test_display_clamps_at_100_but_records_keep_accruing(self):
        state, _ = fresh()
        state.add_case(90, "a very bad month")
        state.add_case(60, "a worse one")
        self.assertEqual(state.case, 100.0)
        self.assertEqual(len(state.evidence), 2)
        self.assertEqual(state.game_over, "arrested")


class TestArrestLatch(unittest.TestCase):
    def test_latch_fires_at_accrual_time(self):
        state, _ = fresh()
        state.add_case(99.5, "the file, nearly complete")
        self.assertIsNone(state.game_over)
        state.add_case(0.5, "", kind="paper")     # the tick that closes it
        self.assertEqual(state.game_over, "arrested")

    def test_case_100_outranks_a_simultaneous_success(self):
        """Design §2.5, precedence 1: arrest beats every outcome decided
        in the same resolution — a success ending set moments earlier
        loses to the latch. (Nothing accrues evidence after a run ends,
        so a finished game is never rewritten.)"""
        state, _ = fresh()
        state.game_over = "survived"
        state.add_case(100, "the file closes at the victory party")
        self.assertEqual(state.game_over, "arrested")


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

    def test_revenue_state_is_shop_local(self):
        state, _ = fresh()
        state.demand_today = 44
        state.delivery_pool = 15
        state.legit_revenue_today = 380
        s0 = state.shops[0]
        self.assertEqual((s0.demand_today, s0.delivery_pool,
                          s0.legit_revenue_today), (44, 15, 380))


# The v2 schema, FROZEN — read off the v2 serializer (save.py @
# 3d79d17), never off today's dataclasses. Borrowing `asdict` for
# these was fine while the schemas matched and quietly stopped being
# fine the moment Employee gained `shop_key` and Rival's countdown
# became a typed `warning`: the fixture kept calling itself an
# authentic v2 payload while carrying fields v2 never wrote, so the
# migration it "proved" was one no real save could ever exercise. A
# fixture that tracks the model cannot test the migration away from
# it. District is frozen for the same reason even though it has not
# drifted yet — it is the third of the same three borrowings.
V2_EMPLOYEE_FIELDS = ("key", "name", "role", "food", "driving", "nerve",
                      "loyalty", "trait", "wage", "bio", "hired",
                      "aware", "morale", "injured_days", "arrested",
                      "routes_survived", "familiarity",
                      "resignation_pending")
V2_RIVAL_FIELDS = ("key", "strength", "relation", "tribute_demanded",
                   "raid_warning", "ledger_stolen", "ovens_wrecked_days",
                   "alertness", "last_raided_day")
V2_DISTRICT_FIELDS = ("key", "heat", "known_price_age", "sold_yesterday")


def _v2(obj, fields) -> dict:
    """One v2 record, built from the frozen field list. `raid_warning`
    is a derived read today and a stored field in v2 — which is
    exactly the shape a v2 save had — so it is taken by name like
    every other field."""
    return {f: getattr(obj, f) for f in fields}


def v2_payload() -> dict:
    """An authentic version-2 save, shaped field-for-field like the v2
    serializer (save.py @ 3d79d17) wrote it: the shop and Case in the
    old flat shape, and employees, districts and rivals through the
    frozen v2 field lists above."""
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
        "employees": [_v2(e, V2_EMPLOYEE_FIELDS) for e in state.employees],
        "districts": {k: _v2(d, V2_DISTRICT_FIELDS)
                      for k, d in state.districts.items()},
        "rivals": {k: _v2(r, V2_RIVAL_FIELDS)
                   for k, r in state.rivals.items()},
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


class TestTheV2FixtureIsFrozen(unittest.TestCase):
    """A migration fixture that borrows today's dataclasses migrates
    nothing: it drifts forward with the model it is supposed to be
    testing the migration AWAY from. These pin that the payload is
    shaped like v2 and not like now."""

    def test_it_carries_no_field_v2_never_wrote(self):
        payload = v2_payload()
        for e in payload["employees"]:
            self.assertEqual(tuple(e), V2_EMPLOYEE_FIELDS)
        for r in payload["rivals"].values():
            self.assertEqual(tuple(r), V2_RIVAL_FIELDS)
        for d in payload["districts"].values():
            self.assertEqual(tuple(d), V2_DISTRICT_FIELDS)

    def test_it_stores_the_countdown_v2_stored(self):
        # v2 had no typed warning and no address on it; the countdown
        # was a bare stored int, and 0 meant none.
        for r in v2_payload()["rivals"].values():
            self.assertNotIn("warning", r)
            self.assertIs(type(r["raid_warning"]), int)

    def test_it_assigns_nobody_to_an_address(self):
        # Addresses did not have identities in v2, so nothing in the
        # payload names one — the migration supplies it.
        for e in v2_payload()["employees"]:
            self.assertNotIn("shop_key", e)
        self.assertNotIn("wagons", v2_payload())

    def test_the_migration_supplies_what_v2_left_out(self):
        loaded = save.state_from_dict(v2_payload())
        self.assertEqual([s.key for s in loaded.shops], ["shop1"])
        self.assertEqual([w.shop_key for w in loaded.wagons], ["shop1"])
        self.assertTrue(all(e.shop_key == "shop1"
                            for e in loaded.employees))
        self.assertTrue(all(r.warning is None
                            for r in loaded.rivals.values()))


class TestV2Migration(unittest.TestCase):
    def test_v2_save_loads_with_case_and_flags_intact(self):
        loaded = save.state_from_dict(v2_payload())
        self.assertEqual(loaded.case, 37.5)
        self.assertEqual(loaded.case_flags, v2_payload()["case_flags"])
        self.assertEqual(loaded.shop.quality, "gourmet")
        self.assertEqual(loaded.shop.upgrades, {"books"})
        self.assertEqual(loaded.shop.district, data.HOME_DISTRICT)
        self.assertEqual(loaded.shop_stash, {"oregano": 5, "mushrooms": 2})
        self.assertEqual(loaded.demand_today, 58)     # moved into the shop
        self.assertEqual(loaded.delivery_pool, 20)
        self.assertEqual(loaded.legit_revenue_today, 0)
        self.assertEqual(loaded.act, 1)
        self.assertIsNone(loaded.branch)
        self.assertIsNone(loaded.branch_state)

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


class TestBranchStatePersistence(unittest.TestCase):
    def test_none_and_populated_both_round_trip(self):
        state, _ = fresh()
        d = save.state_to_dict(state)
        self.assertIn("branch_state", d)
        self.assertIsNone(d["branch_state"])
        state.act = 2
        state.branch = "partner"
        state.day = max(state.day, 19)
        # A paid first cycle: the run stands on the day it was paid,
        # and the cursor has advanced past it — what the calendar
        # check and the ledger reconciliation each require.
        state.branch_state = BranchState(
            points_due_day=24,
            points_cycles=[PointsCycleRecord(
                due_day=19, bill=2500, vig=0, paid=True, paid_day=19)])
        restored = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(restored.act, 2)
        self.assertEqual(restored.branch, "partner")
        self.assertEqual(restored.branch_state,
                         state.branch_state)


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
