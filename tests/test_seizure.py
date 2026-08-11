"""The seizure correction: cargo reported seized is cargo GONE.

A route's night can end in a bust two ways, and the two arms
disagreed. The interactive traffic stop counted the load and emptied
the manifest; the DELEGATED arrest — the driver running the route
alone — counted the load and left it in the manifest, so the shared
return loop at the end of that branch carried every "seized" unit
home to the origin's stash. The player was told the load was in an
evidence locker and found it on the shelf in the morning.

Both arms now spell the seizure with one authority
(`routes.seize_cargo`). These tests drive the REAL service path — a
planned route committed and resolved through `phases.service` — and
reach each arm by seed scan, because which way a night goes is the
engine's dice and not something a test may hand-place.
"""

import random
import unittest

from test_lifecycle import Listening, _route_plan, _with_site
from extra_toppings import market, models, phases, routes
from extra_toppings.rng import Streams

# The seeds below were found by scanning the REAL path, not chosen to
# make a number come out: seed 18 is the first that ends a delegated
# route in an arrest, and seed 16 the first that ends a ride-along
# route at a traffic stop. Both are asserted to have actually reached
# their arm, so a future engine change that stops reaching it fails
# here instead of passing vacuously.
DELEGATED_ARREST_SEED = 18
INTERACTIVE_BUST_SEED = 16
STOCK, LOADED = 6, 4          # 6 in the back room, 4 on the wagon


class SeizureCase(unittest.TestCase):
    def _run(self, seed, ride_along, script=None):
        """One real night: a route planned at the founding address,
        committed and resolved by the actual service phase."""
        state = _with_site(day=7, acceptance=5)
        market.roll_prices(state, random.Random(3))
        home = state.shop_by_key(models.HOME_SHOP_KEY)
        home.stash = {"mushrooms": STOCK}
        home.ingredients, home.demand_today = 40, 20
        home.delivery_pool = 10
        driver = next(e for e in state.employees if e.driving >= 4)
        driver.hired = driver.aware = True
        plan = _route_plan(state, models.HOME_SHOP_KEY,
                           models.HOME_WAGON_KEY, driver=driver,
                           cargo={"mushrooms": LOADED}, legit=2,
                           ride_along=ride_along)
        con = Listening(script or [])
        phases.service(state, {"routes": {models.HOME_SHOP_KEY: plan}},
                       con, Streams(seed))
        return state, home, driver, con, plan


class TestTheDelegatedArrestTakesTheLoad(SeizureCase):
    def _busted_night(self):
        state, home, driver, con, plan = self._run(
            DELEGATED_ARREST_SEED, ride_along=False)
        # The arm was actually reached — otherwise everything below
        # would pass by describing a night that never went wrong.
        self.assertTrue(driver.arrested)
        self.assertTrue(con.said("units seized"), con.lines)
        return state, home, driver, con, plan

    def test_the_seized_units_do_not_come_home(self):
        # THE defect: the shared return loop put them back. The back
        # room keeps only what never left it.
        _state, home, _driver, _con, _plan = self._busted_night()
        self.assertEqual(home.stash.get("mushrooms", 0), STOCK - LOADED)

    def test_the_manifest_is_empty_afterwards(self):
        _state, _home, _driver, _con, plan = self._busted_night()
        self.assertEqual(sum(plan["cargo"].values()), 0)

    def test_the_report_and_the_shelf_agree(self):
        # The two facts that used to disagree: what the player is TOLD
        # was taken, and what is actually gone.
        _state, home, _driver, con, _plan = self._busted_night()
        self.assertTrue(con.said(f"{LOADED} units seized"), con.lines)
        self.assertEqual(STOCK - home.stash.get("mushrooms", 0), LOADED)

    def test_the_case_still_records_the_full_seizure(self):
        # The count is taken BEFORE the manifest empties, so the
        # correction changes what comes home and not what the Case
        # knows: an aware driver's arrest is 10 + 0.3 per unit.
        state, _home, driver, _con, _plan = self._busted_night()
        arrest = [e for e in state.evidence
                  if e.source == driver.key and "arrested" in e.why]
        self.assertEqual(len(arrest), 1, [e.why for e in state.evidence])
        self.assertAlmostEqual(arrest[0].magnitude, 10 + LOADED * 0.3)


class TestTheInteractiveStopIsUnchanged(SeizureCase):
    """The control. This arm always cleared the manifest, and must
    still do exactly that — the correction gave the two arms one
    authority, it did not give this one new behaviour."""

    def _busted_night(self):
        state, home, driver, con, plan = self._run(
            INTERACTIVE_BUST_SEED, ride_along=True, script=[0] * 12)
        self.assertTrue(con.said("Seized:"), con.lines)
        return state, home, driver, con, plan

    def test_the_load_is_gone_from_the_manifest(self):
        _state, _home, _driver, _con, plan = self._busted_night()
        self.assertEqual(sum(plan["cargo"].values()), 0)

    def test_nothing_comes_back_to_the_back_room(self):
        _state, home, _driver, _con, _plan = self._busted_night()
        self.assertEqual(home.stash.get("mushrooms", 0), STOCK - LOADED)


class TestOneSeizureAuthority(unittest.TestCase):
    """Both arms call ONE function, so "counted" and "gone" cannot
    come apart again in whichever arm someone edits next."""

    def test_it_counts_and_empties_in_one_call(self):
        plan = {"cargo": {"mushrooms": 3, "oregano": 2}}
        self.assertEqual(routes.seize_cargo(plan), 5)
        self.assertEqual(plan["cargo"], {"mushrooms": 0, "oregano": 0})

    def test_a_second_seizure_finds_nothing_left(self):
        plan = {"cargo": {"mushrooms": 3}}
        routes.seize_cargo(plan)
        self.assertEqual(routes.seize_cargo(plan), 0)

    def test_an_empty_manifest_seizes_nothing(self):
        plan = {"cargo": {}}
        self.assertEqual(routes.seize_cargo(plan), 0)

    def test_the_goods_keep_their_identity(self):
        # Emptied, never deleted: the keys stay, because a manifest
        # that forgets which goods it carried is a different record.
        plan = {"cargo": {"mushrooms": 3, "truffle": 1}}
        routes.seize_cargo(plan)
        self.assertEqual(sorted(plan["cargo"]), ["mushrooms", "truffle"])


if __name__ == "__main__":
    unittest.main()
