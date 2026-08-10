"""P3.5 — the night's wagon is one stateful answer (design rev. 25
item 1, rev. 26).

The bug these pin: the outgoing raid asked whether the wagon was free
and the incoming raid's decoy never did, so a shop whose wagon was out
on the route could still "empty the stash into the wagon" — and, when
both rivals arrived, two decoys could load the same wagon twice.

Every case drives the real `phases.night`, so the pins fail on the
pre-fix engine rather than on a hand-built state.
"""

import random
import unittest

from extra_toppings import models, phases, raids, war
from extra_toppings.models import BranchState, new_state
from extra_toppings.rng import Streams
from extra_toppings.ui import ScriptedConsole

def _wag(state, **report):
    """Every direct `night` call needs the assignment authority the
    service phase would have opened (P4b.1a). An UNSPENT one is the
    honest fixture here: these tests do not run service, so no wagon
    departed."""
    return {**report, "wagons": phases.WagonNight(state)}

DECOY_PROMPT = "The unfamiliar cars are circling. Your move:"


class Watching(ScriptedConsole):
    """Records what was said and every menu it was offered."""

    def __init__(self, script=None):
        super().__init__(script)
        self.lines: list = []
        self.menus: list = []

    def say(self, text=""):
        self.lines.append(text)

    def bullet(self, text):
        self.lines.append(f"• {text}")

    def menu(self, prompt, options):
        self.menus.append((prompt, list(options)))
        return super().menu(prompt, options)

    def said(self, fragment):
        return any(fragment in line for line in self.lines)

    def decoy_offers(self):
        """Every decoy label this console was actually shown."""
        return [o for prompt, opts in self.menus if prompt == DECOY_PROMPT
                for o in opts if o.startswith("Empty the stash")]


def shop_with_stash(day=6):
    state = new_state()
    state.day = day
    state.clean = 4000
    state.dirty = 400
    state.shop_stash = {"mushrooms": 6}
    return state


def hire(state, first_name):
    person = next(e for e in state.employees
                  if e.name.startswith(first_name))
    person.hired = True
    person.aware = True
    return person


def arriving(state, *rival_keys):
    for key in rival_keys:
        state.rivals[key].warning = models.RaidWarning(1, models.HOME_SHOP_KEY)
    return state


def run_night(state, plans, con, service_report=None, seed=11,
              departed=None):
    """`departed` is what SERVICE already spent (P4b.1a): routes and
    pickups claim their wagon when they roll, so the night inherits a
    populated authority instead of re-deriving one from intentions."""
    wagons = phases.WagonNight(state)
    for wagon_key, by in (departed or {}).items():
        assert wagons.claim_key(wagon_key, by).claimed
    report = {**(service_report or {}), "wagons": wagons}
    phases.night(state, plans, report, con, Streams(seed))
    return con


class TestTheWagonIsSpentByWhatDeparted(unittest.TestCase):
    """Cases 1-4: routes, pickups and outgoing jobs."""

    def test_a_departed_route_denies_the_decoy(self):
        state = arriving(shop_with_stash(), "vinnie")
        driver = hire(state, "Rosa")
        plans = {"routes": {models.HOME_SHOP_KEY: {"district": "old_harbor", "driver": driver,
                           "ride_along": False, "cargo": {}, "legit": 0, "origin_shop": models.HOME_SHOP_KEY,
                           "wagon_key": models.HOME_WAGON_KEY}},
                 "raid": None}
        con = run_night(state, plans, Watching([1, 0]),
                        departed={models.HOME_WAGON_KEY: "route"})
        offers = con.decoy_offers()
        self.assertTrue(offers, "the decoy must still be shown")
        self.assertIn("unavailable", offers[0])
        self.assertIn("out on tonight's route", offers[0])
        self.assertTrue(con.said("There is nothing to load"))

    def test_no_wagon_job_leaves_the_decoy_available(self):
        state = arriving(shop_with_stash(), "vinnie")
        con = run_night(state, {"routes": {}, "raid": None},
                        Watching([1]))
        offers = con.decoy_offers()
        self.assertTrue(offers)
        self.assertNotIn("unavailable", offers[0])
        self.assertFalse(con.said("There is nothing to load"))
        # It really ran: the decoy sets exactly two damage days.
        self.assertEqual(state.shop.damage_days, 2)

    def test_a_departed_pickup_denies_the_decoy(self):
        state = self._war_state()
        arriving(state, "vinnie")
        driver = hire(state, "Rosa")
        plans = { "raid": None,
                 "salvage": {"rival": "sal", "driver": driver,
                             "origin_shop": models.HOME_SHOP_KEY,
                             "wagon_key": models.HOME_WAGON_KEY}}
        con = run_night(state, plans, Watching([1, 0]),
                        departed={models.HOME_WAGON_KEY: "salvage"})
        offers = con.decoy_offers()
        self.assertIn("unavailable", offers[0])
        self.assertIn("out on tonight's pickup", offers[0])

    def test_a_scrubbed_pickup_leaves_the_decoy_available(self):
        # Execution truth: a pickup that never departed never took it.
        state = self._war_state()
        arriving(state, "vinnie")
        driver = hire(state, "Rosa")
        plans = { "raid": None,
                 "salvage": {"rival": "sal", "driver": driver,
                             "origin_shop": models.HOME_SHOP_KEY,
                             "wagon_key": models.HOME_WAGON_KEY}}
        report = {"salvage": war.SalvageResult(outcome="scrubbed",
                                               wagon_used=False)}
        con = run_night(state, plans, Watching([1]), service_report=report)
        offers = con.decoy_offers()
        self.assertNotIn("unavailable", offers[0])

    def _war_state(self):
        state = shop_with_stash()
        state.branch = "war"
        state.act = 2
        state.branch_state = BranchState.war(
            war_target="sal", declared_day=2,
            starting_strength=state.rivals["sal"].strength)
        models.set_relation(state, "sal", models.VENDETTA_RELATION)
        state.branch_state.campaigns[0].salvage_available = True
        return state


class TestOnlyAStockTheftTakesTheWagon(unittest.TestCase):
    """Case 3 and design rev. 26: departure spends it, and only a
    stock theft loads it — outcome irrelevant."""

    def _raid_night(self, objective, script):
        state = arriving(shop_with_stash(), "vinnie")
        crew = hire(state, "Angelo")
        plans = { "salvage": None,
                 # Only a stock theft loads a wagon (rev. 26); every
                 # other objective records going on foot EXPLICITLY.
                 "raid": {"rival": "sal", "objective": objective,
                          "wagon_key": (models.HOME_WAGON_KEY
                                        if objective == "steal_stock"
                                        else None),
                          "team": [crew], "armed": False,
                          "table_warned": True, "return_shop": models.HOME_SHOP_KEY}}
        return state, run_night(state, plans, Watching(script))

    def test_a_departed_stock_theft_denies_the_decoy(self):
        _state, con = self._raid_night("steal_stock", [1, 0])
        offers = con.decoy_offers()
        self.assertIn("unavailable", offers[0])
        self.assertIn("out with the night crew", offers[0])

    def test_a_ledger_job_goes_on_foot_and_leaves_it(self):
        _state, con = self._raid_night("ledger", [1])
        offers = con.decoy_offers()
        self.assertNotIn("unavailable", offers[0])

    def test_a_scrubbed_raid_never_departed_so_it_leaves_it(self):
        # Case 4: the crew picked in the morning did not survive to
        # nightfall, so nothing drove anywhere.
        state = arriving(shop_with_stash(), "vinnie")
        crew = hire(state, "Angelo")
        crew.injured_days = 2                      # off the job tonight
        plans = { "salvage": None,
                 "raid": {"rival": "sal", "objective": "steal_stock",
                          "wagon_key": models.HOME_WAGON_KEY,
                          "team": [crew], "armed": False,
                          "table_warned": True, "return_shop": models.HOME_SHOP_KEY}}
        con = run_night(state, plans, Watching([1]))
        self.assertTrue(con.said("The night job is scrubbed"))
        offers = con.decoy_offers()
        self.assertNotIn("unavailable", offers[0])

    def test_the_outcome_does_not_matter_only_departure(self):
        # The authority spends at departure, so a lost raid and a won
        # raid leave the wagon in the same state.
        seen = set()
        for seed in range(12):
            state = arriving(shop_with_stash(), "vinnie")
            crew = hire(state, "Angelo")
            plans = { "salvage": None,
                     "raid": {"rival": "sal", "objective": "steal_stock",
                          "wagon_key": models.HOME_WAGON_KEY,
                              "team": [crew], "armed": False,
                              "table_warned": True, "return_shop": models.HOME_SHOP_KEY}}
            con = Watching([1, 0])
            phases.night(state, plans, {"wagons": phases.WagonNight(state)}, con, Streams(seed))
            offers = con.decoy_offers()
            if offers:
                seen.add("unavailable" in offers[0])
        self.assertEqual(seen, {True},
                         "every departed stock theft must deny the decoy, "
                         "whatever the raid's outcome")


class TestTwoRivalsInOneNight(unittest.TestCase):
    """Cases 5-6: the first arrival's answer binds the second."""

    def test_a_decoy_reserves_the_wagon_against_the_second_raid(self):
        state = arriving(shop_with_stash(), "sal", "vinnie")
        # first raid: take the decoy; second: it must be gone.
        con = run_night(state, {"routes": {}, "raid": None},
                        Watching([1, 1, 0]))
        offers = con.decoy_offers()
        self.assertEqual(len(offers), 2, "both rivals must arrive")
        self.assertNotIn("unavailable", offers[0])
        self.assertIn("unavailable", offers[1])
        self.assertIn("already loaded and gone", offers[1])

    def test_fighting_the_first_leaves_the_wagon_for_the_second(self):
        state = arriving(shop_with_stash(), "sal", "vinnie")
        con = run_night(state, {"routes": {}, "raid": None},
                        Watching([0, 1]))
        offers = con.decoy_offers()
        self.assertEqual(len(offers), 2)
        self.assertNotIn("unavailable", offers[0])
        self.assertNotIn("unavailable", offers[1])

    def test_paying_the_first_leaves_the_wagon_for_the_second(self):
        state = arriving(shop_with_stash(), "sal", "vinnie")
        state.dirty = 6000
        for key in ("sal", "vinnie"):
            state.rivals[key].tribute_demanded = 1500
        con = run_night(state, {"routes": {}, "raid": None},
                        Watching([2, 1]))
        offers = con.decoy_offers()
        self.assertEqual(len(offers), 2)
        self.assertNotIn("unavailable", offers[1])


class TestTheAuthorityItself(unittest.TestCase):
    """The ledger's own contract, independent of any night."""

    def _fleet(self):
        state = new_state()
        return state, phases.WagonNight(state), models.HOME_SHOP_KEY

    def test_it_starts_free_and_is_claimed_once(self):
        _state, wagon, home = self._fleet()
        self.assertTrue(wagon.available_at(home))
        self.assertEqual(wagon.note_at(home), "")
        wagon.claim_at(home, "route")
        self.assertFalse(wagon.available_at(home))
        self.assertEqual(wagon.note_at(home), "out on tonight's route")

    def test_a_second_claim_is_refused_not_absorbed(self):
        # One wagon at that address. A second claim means a consumer
        # acted on a stale `available_at`, which is the bug class this
        # authority exists to end — so it must surface.
        _state, wagon, home = self._fleet()
        wagon.claim_at(home, "route")
        with self.assertRaises(RuntimeError) as caught:
            wagon.claim_at(home, "decoy")
        self.assertIn("no wagon left", str(caught.exception))
        self.assertEqual(wagon.note_at(home), "out on tonight's route")

    def test_even_the_same_consumer_cannot_claim_twice(self):
        _state, wagon, home = self._fleet()
        wagon.claim_at(home, "raid")
        with self.assertRaises(RuntimeError):
            wagon.claim_at(home, "raid")

    def test_an_unknown_consumer_is_refused(self):
        _state, wagon, home = self._fleet()
        with self.assertRaises(ValueError):
            wagon.claim_at(home, "helicopter")

    def test_the_view_is_one_consistent_value(self):
        _state, wagon, home = self._fleet()
        self.assertEqual(wagon.view_at(home),
                         models.WagonAvailability(True, ""))
        wagon.claim_at(home, "route")
        view = wagon.view_at(home)
        self.assertFalse(view.available)
        self.assertEqual(view.note, "out on tonight's route")

    def test_one_addresss_wagon_does_not_ground_another(self):
        # The point of the fleet: a second shop keeps its own wagon.
        state = new_state()
        state.shops.append(models.Shop(key="shop2", district="university"))
        state.wagons.append(models.Wagon(key="wagon2", shop_key="shop2"))
        wagon = phases.WagonNight(state)
        wagon.claim_at(models.HOME_SHOP_KEY, "route")
        self.assertFalse(wagon.available_at(models.HOME_SHOP_KEY))
        self.assertTrue(wagon.available_at("shop2"))
        self.assertEqual(wagon.claim_at("shop2", "route"), "wagon2")

    def test_an_unknown_address_is_refused(self):
        _state, wagon, _home = self._fleet()
        with self.assertRaises(KeyError):
            wagon.available_at("nowhere")

    def test_a_contradictory_availability_is_refused(self):
        # The pair travels as one value precisely so "free, and out on
        # the route" cannot be expressed.
        with self.assertRaises(ValueError):
            models.WagonAvailability(True, "out on tonight's route")
        with self.assertRaises(ValueError):
            models.WagonAvailability(False, "")


class TestTheDecoyMenuTerminates(unittest.TestCase):
    """An exhausted ScriptedConsole answers with the LAST option, and
    against a declared rival the decoy IS last — so the refusal must
    never re-ask with it still on the menu."""

    def test_a_vendetta_raid_with_no_wagon_still_resolves(self):
        state = shop_with_stash()
        state.branch = "war"
        state.act = 2
        state.branch_state = BranchState.war(
            war_target="vinnie", declared_day=2,
            starting_strength=state.rivals["vinnie"].strength)
        models.set_relation(state, "vinnie", models.VENDETTA_RELATION)
        arriving(state, "vinnie")
        con = Watching()                     # empty script: always last
        result = raids.incoming_raid(
            state, "vinnie", con, random.Random(3),
            wagon=models.WagonAvailability(False, "out on tonight's route"))
        self.assertIn(result.outcome, ("landed", "repelled"))
        self.assertFalse(result.wagon_taken)
        self.assertTrue(con.said("There is nothing to load"))


if __name__ == "__main__":
    unittest.main()
