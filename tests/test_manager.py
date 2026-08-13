"""P4b.3 — THE MANAGER-TRANSITION MATRIX (design rev. 30 item 3,
completed by rev. 34 item 2).

The root invariant: **every route into and out of the post goes
through the one transition authority, and the opportunity is STATE
rather than timing.**

Every row is invisible at a single manager — the founding address
carries no post at all — so no identity gate proves any of it.

The routes are driven through the REAL paths that produce them: the
morning's staff menu for firing and reassignment, the morning's staff
trouble for resignation, the rival phase for the poach, the real
route resolution for the arrest, and the settlement verb for the
severance. `vacate_manager` is never called directly where a player
path exists.
"""

import copy
import random
import unittest
from dataclasses import FrozenInstanceError

from extra_toppings import (data, evidence, market, models, partner,
                            phases, rivals, routes, save, shop, sitdown)
from extra_toppings.config import GameConfig
from extra_toppings.models import (HOME_SHOP_KEY, ManagerPost,
                                   SitdownSnapshot, new_state)
from extra_toppings.rng import Streams
from extra_toppings.ui import ScriptedConsole

PARTNER_ON = GameConfig(fork_enabled=True,
                        enabled_branches=frozenset({"partner"}))


class Listening(ScriptedConsole):
    def __init__(self, script=None):
        super().__init__(script)
        self.lines: list = []
        self.menus: list = []

    def say(self, text: str = "") -> None:
        self.lines.append(text)

    def bullet(self, text: str) -> None:
        self.lines.append(f"• {text}")

    def menu(self, prompt, options):
        self.menus.append((prompt, list(options)))
        return super().menu(prompt, options)

    def said(self, fragment: str) -> bool:
        return any(fragment in line for line in self.lines)

    def offered(self, fragment: str):
        return next((o for p, o in self.menus if fragment in p), None)


def seated(day: int = 15, payoff_day: int = 13):
    """A real Partner run: the debt dead, the chair taken, the deal
    struck through the actual sit-down scene, so the second address
    and its INITIAL PENDING VACANCY are the ones production builds."""
    state = new_state()
    state.debt = 0
    state.debt_paid_day = payoff_day
    state.day = payoff_day + 1
    state.add_case(20.0, "prior seizures", kind="physical")
    state.sitdown_snapshot = SitdownSnapshot(
        payoff_day=payoff_day, case_at_lockup=20.0,
        evidence_count_at_lockup=len(state.evidence))
    con = Listening([1, 1 + partner.SITE_DISTRICTS.index("university"), 1])
    sitdown.run_scene(state, con, PARTNER_ON)
    state.day = day
    state.clean, state.dirty = 40_000, 4_000
    return state


def second(state):
    return next(s for s in state.shops if s.key != HOME_SHOP_KEY)


def staff(state, first_name: str, shop_key: str, **fields):
    who = next(e for e in state.employees if first_name in e.name)
    who.hired = True
    who.aware = True
    who.shop_key = shop_key
    for k, v in fields.items():
        setattr(who, k, v)
    return who


def install(state, first_name: str = "Angelo"):
    """Somebody in the post, through the real appointment authority."""
    who = staff(state, first_name, second(state).key)
    models.appoint_manager(state, second(state), who)
    return who


def open_doors(state, con=None):
    """The REAL pre-service boundary — the only place an opportunity
    is ever offered."""
    con = con or Listening()
    phases._management_boundary(state, con)
    return con


# ══ the typed value ═══════════════════════════════════════════════

class TestThePostIsOneValue(unittest.TestCase):
    def test_the_four_shapes_are_the_only_shapes(self):
        ManagerPost(manager_key="e0")
        for opportunity in ("pending", "declined", "exhausted"):
            ManagerPost(vacancy_day=3, opportunity=opportunity)

    def test_staffed_and_empty_at_once_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            ManagerPost(manager_key="e0", vacancy_day=3)
        self.assertIn("staffed or it is empty", str(caught.exception))

    def test_a_staffed_post_carries_no_outstanding_window(self):
        with self.assertRaises(ValueError):
            ManagerPost(manager_key="e0", opportunity="pending")

    def test_an_empty_post_must_record_the_day_it_emptied(self):
        # rev. 30 item 2 forbids reconstructing it from the calendar,
        # so a value that could go missing is refused outright.
        for bad in (None, 0, -1, 3.0, True, "3"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    ManagerPost(vacancy_day=bad, opportunity="pending")

    def test_an_empty_post_is_never_none(self):
        with self.assertRaises(ValueError):
            ManagerPost(vacancy_day=3, opportunity="none")

    def test_an_unknown_opportunity_is_refused(self):
        with self.assertRaises(ValueError):
            ManagerPost(vacancy_day=3, opportunity="deferred")

    def test_it_is_frozen(self):
        # The EXACT failure, not any failure: a broad `Exception`
        # assertion blesses whatever goes wrong, which this project
        # has already ruled against once.
        with self.assertRaises(FrozenInstanceError):
            ManagerPost(manager_key="e0").manager_key = "e1"  # type: ignore

    def test_pending_is_not_yet_penalised(self):
        self.assertFalse(ManagerPost(vacancy_day=3,
                                     opportunity="pending").penalised)
        for spent in ("declined", "exhausted"):
            self.assertTrue(ManagerPost(vacancy_day=3,
                                        opportunity=spent).penalised)


# ══ where a post may and must exist ═══════════════════════════════

class TestWhichAddressesCarryAPost(unittest.TestCase):
    def test_the_founding_room_carries_none(self):
        state = seated()
        self.assertIsNone(state.shop_by_key(HOME_SHOP_KEY).manager_post)

    def test_a_post_on_the_founding_room_is_refused(self):
        state = seated()
        state.shop_by_key(HOME_SHOP_KEY).manager_post = ManagerPost(
            vacancy_day=1, opportunity="pending")
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(state))
        self.assertIn("the operator's", str(caught.exception))

    def test_appointing_at_the_founding_room_is_refused(self):
        state = seated()
        who = staff(state, "Angelo", HOME_SHOP_KEY)
        with self.assertRaises(ValueError):
            models.appoint_manager(state, state.shop_by_key(HOME_SHOP_KEY),
                                   who)

    def test_a_partner_address_without_a_post_is_refused(self):
        state = seated()
        second(state).manager_post = None
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(state))
        self.assertIn("never unrecorded", str(caught.exception))

    def test_the_deal_builds_the_initial_pending_vacancy(self):
        state = seated()
        post = second(state).manager_post
        self.assertEqual(post.opportunity, "pending")
        self.assertIsNone(post.manager_key)
        self.assertEqual(post.vacancy_day, second(state).acceptance_day)


# ══ the two predicates ════════════════════════════════════════════

class TestTheTwoPredicates(unittest.TestCase):
    """Rev. 34 item 1: injury does not vacate a post, but an injured
    person cannot be given one. One predicate could not do both."""

    def test_an_injured_manager_keeps_the_post(self):
        state = seated()
        who = install(state)
        who.injured_days = 3
        self.assertTrue(models.valid_holder(state, second(state), who.key))
        save.state_from_dict(save.state_to_dict(state))   # and it loads
        self.assertEqual(second(state).manager_post.manager_key, who.key)

    def test_an_injured_candidate_cannot_be_appointed(self):
        state = seated()
        who = staff(state, "Angelo", second(state).key, injured_days=3)
        self.assertNotIn(who, models.appointable(state, second(state)))
        with self.assertRaises(ValueError):
            models.appoint_manager(state, second(state), who)

    def test_only_the_read_in_and_assigned_may_be_appointed(self):
        state = seated()
        naive = staff(state, "Bee", second(state).key, aware=False)
        elsewhere = staff(state, "Marcus", HOME_SHOP_KEY)
        ready = staff(state, "Angelo", second(state).key)
        self.assertEqual(models.appointable(state, second(state)), [ready])
        for wrong in (naive, elsewhere):
            with self.assertRaises(ValueError):
                models.appoint_manager(state, second(state), wrong)


# ══ THE SIX LOSS ROUTES, each through its real path ══════════════

class TestEveryRouteOutOfThePost(unittest.TestCase):
    def _vacated(self, state):
        post = second(state).manager_post
        return post.manager_key is None and post.opportunity == "pending"

    def test_firing_empties_the_post(self):
        state = seated()
        boss = install(state)
        crew = state.hired()
        con = Listening([3, crew.index(boss), 5])
        phases._staff_menu(state, con, random.Random(1))
        self.assertFalse(boss.hired)
        self.assertTrue(self._vacated(state))
        self.assertEqual(second(state).manager_post.vacancy_day, state.day)

    def test_reassignment_empties_the_post_before_the_move(self):
        state = seated()
        boss = install(state)
        crew = state.hired()
        # Move → this person → the home room → Back.
        con = Listening([4, crew.index(boss), 0, 5])
        phases._staff_menu(state, con, random.Random(1))
        self.assertEqual(boss.shop_key, HOME_SHOP_KEY)
        self.assertTrue(self._vacated(state))

    def test_resignation_empties_the_post(self):
        state = seated()
        boss = install(state)
        boss.morale = 1
        boss.resignation_pending = True
        phases._staff_trouble(state, Listening(), random.Random(2))
        self.assertFalse(boss.hired)
        self.assertTrue(self._vacated(state))

    def test_a_poach_empties_the_post(self):
        state = seated()
        boss = install(state)
        boss.loyalty, boss.morale, boss.trait = 1, 1, "greedy"
        for e in state.employees:            # the only poachable name
            if e is not boss:
                e.hired = False
        taken = False
        for seed in range(60):
            probe = save.state_from_dict(save.state_to_dict(state))
            rivals._poach(probe, probe.rivals["sal"], {"short": "Sal"},
                          Listening(), random.Random(seed))
            who = next(e for e in probe.employees if e.key == boss.key)
            if not who.hired:
                taken = True
                self.assertTrue(self._vacated(probe))
                break
        self.assertTrue(taken, "no seed produced a successful poach")

    def test_a_settled_witness_does_not_stay_manager(self):
        # THE route revision 33 missed (rev. 34 item 2): settling
        # takes a name off the payroll with no fired record, and
        # Partner reaches the settlement verb through remediation.
        state = seated()
        boss = install(state)
        state.add_case(20.0, "what they saw", kind="witness",
                       source=boss.key)
        evidence.settle_witness(state, boss, Listening())
        self.assertFalse(boss.hired)
        self.assertIn(boss.key, state.branch_state.settled_witnesses)
        self.assertTrue(self._vacated(state))

    def test_a_route_arrest_empties_the_post(self):
        state = seated()
        boss = install(state, "Rosa")            # a driver
        boss.driving = 9
        home = state.shop_by_key(HOME_SHOP_KEY)
        home.stash = {"mushrooms": 8}
        home.ingredients, home.demand_today, home.delivery_pool = 40, 20, 10
        plan = {"district": "old_harbor", "driver": boss,
                "ride_along": False, "cargo": {"mushrooms": 4},
                "legit": 2, "origin_shop": HOME_SHOP_KEY,
                "wagon_key": models.HOME_WAGON_KEY}
        booked = False
        for seed in range(400):
            probe = save.state_from_dict(save.state_to_dict(state))
            driver = next(e for e in probe.employees if e.key == boss.key)
            # Hot, but under the amber band: Partner now feels the
            # weather (rev. 29 item 7), and a red district refuses
            # the route outright rather than busting it.
            probe.districts["old_harbor"].heat = models.HEAT_AMBER - 1
            # The morning rolls prices in a real run; this case drives
            # the route resolution directly, so it rolls them here
            # through the same authority rather than posing a price.
            market.roll_prices(probe, random.Random(seed))
            departed = {**plan, "driver": driver}
            departure = routes.record_departure(probe, departed)
            routes.resolve_route(departure,
                                 Listening(), random.Random(seed))
            if driver.arrested:
                booked = True
                self.assertTrue(self._vacated(probe))
                break
        self.assertTrue(booked, "no seed produced an arrest")

    def test_the_reason_vocabulary_is_closed(self):
        state = seated()
        install(state)
        with self.assertRaises(ValueError):
            models.vacate_manager(state, second(state), "retired")

    def test_vacating_twice_does_not_refresh_a_spent_window(self):
        state = seated()
        boss = install(state)
        models.vacate_manager(state, second(state), "fired")
        boss.hired = False                       # nobody left eligible
        open_doors(state, Listening([0]))        # spent by exhaustion
        spent = second(state).manager_post
        self.assertEqual(spent.opportunity, "exhausted")
        models.release_from_posts(state, boss, "fired")
        self.assertEqual(second(state).manager_post, spent)


# ══ THE APPOINTMENT AUTHORITY HAS NO SIDE ENTRANCE ═══════════════

class TestAppointmentRefusesEveryOtherDoor(unittest.TestCase):
    """P4b.3 review: the authority canonicalized the ADDRESS and not
    the PERSON, and it wrote over any post it was handed. Each
    refusal below must also mutate NOTHING."""

    def test_a_detached_clone_cannot_appoint_its_canonical_twin(self):
        # The reproduction exactly: the real body is in hospital, the
        # copy is on its feet, and the copy's availability was what
        # the authority read while the canonical KEY was what it
        # wrote.
        state = seated()
        real = staff(state, "Angelo", second(state).key)
        real.injured_days = 3
        clone = copy.deepcopy(real)
        clone.injured_days = 0
        before = second(state).manager_post
        with self.assertRaises(ValueError) as caught:
            models.appoint_manager(state, second(state), clone)
        self.assertIn("detached copy", str(caught.exception))
        self.assertEqual(second(state).manager_post, before)

    def test_a_stranger_is_refused(self):
        # KeyError, not ValueError: an unknown key is a lookup that
        # cannot be answered, and this is the same shared authority
        # `shop_by_key` raises from — `canonical_shop` refuses a
        # ghost address exactly this way.
        state = seated()
        outsider = copy.deepcopy(
            next(e for e in state.employees if "Angelo" in e.name))
        outsider.key = "ghost"
        before = second(state).manager_post
        with self.assertRaises(KeyError):
            models.appoint_manager(state, second(state), outsider)
        self.assertEqual(second(state).manager_post, before)

    def test_an_ambiguous_identity_is_refused_not_picked_between(self):
        # Two entries keyed `e6` are not one person a lookup may pick
        # between; they are a payload with no answer. Walking the
        # roster for the first match ACCEPTED that (P4b.3 re-review).
        state = seated()
        who = staff(state, "Angelo", second(state).key)
        state.employees.append(copy.deepcopy(who))
        before = second(state).manager_post
        with self.assertRaises(KeyError) as caught:
            models.appoint_manager(state, second(state), who)
        self.assertIn("ambiguous identity", str(caught.exception))
        self.assertEqual(second(state).manager_post, before)


class TestVacatingHasTheSameDoorAsAppointing(unittest.TestCase):
    """P4b.3 re-review: appointment was closed against detached
    records and VACATING was not, so the authority had one locked
    door and one open one. A clone could empty the canonical
    manager's post while the real person stayed hired, read in and
    assigned there — a vacancy created by a record that is not
    anybody."""

    def test_a_detached_clone_cannot_vacate_the_canonical_post(self):
        state = seated()
        boss = install(state)
        before = second(state).manager_post
        with self.assertRaises(ValueError) as caught:
            models.release_from_posts(state, copy.deepcopy(boss), "fired")
        self.assertIn("detached copy", str(caught.exception))
        # Byte for byte: the refusal mutated nothing at all.
        self.assertEqual(second(state).manager_post, before)
        self.assertEqual(second(state).manager_post.manager_key, boss.key)
        self.assertTrue(boss.hired)

    def test_an_ambiguous_identity_cannot_vacate_either(self):
        state = seated()
        boss = install(state)
        state.employees.append(copy.deepcopy(boss))
        before = second(state).manager_post
        with self.assertRaises(KeyError) as caught:
            models.release_from_posts(state, boss, "fired")
        self.assertIn("ambiguous identity", str(caught.exception))
        self.assertEqual(second(state).manager_post, before)

    def test_a_stranger_cannot_vacate_either(self):
        state = seated()
        install(state)
        outsider = copy.deepcopy(
            next(e for e in state.employees if "Marcus" in e.name))
        outsider.key = "ghost"
        before = second(state).manager_post
        with self.assertRaises(KeyError):
            models.release_from_posts(state, outsider, "fired")
        self.assertEqual(second(state).manager_post, before)

    def test_every_real_route_still_empties_the_post(self):
        # The positive controls, so the refusals above are not proved
        # by a door that refuses everybody. Each is the REAL path.
        routes_taken = []

        state = seated()
        boss = install(state)
        crew = state.hired()
        phases._staff_menu(state, Listening([3, crew.index(boss), 5]),
                           random.Random(1))
        routes_taken.append(("fired", second(state).manager_post.vacant))

        state = seated()
        boss = install(state)
        crew = state.hired()
        phases._staff_menu(state, Listening([4, crew.index(boss), 0, 5]),
                           random.Random(1))
        routes_taken.append(("reassigned",
                             second(state).manager_post.vacant))

        state = seated()
        boss = install(state)
        boss.morale, boss.resignation_pending = 1, True
        phases._staff_trouble(state, Listening(), random.Random(2))
        routes_taken.append(("resigned", second(state).manager_post.vacant))

        state = seated()
        boss = install(state)
        state.add_case(20.0, "what they saw", kind="witness",
                       source=boss.key)
        evidence.settle_witness(state, boss, Listening())
        routes_taken.append(("settled", second(state).manager_post.vacant))

        for label, vacated in routes_taken:
            with self.subTest(route=label):
                self.assertTrue(vacated)

    def test_a_spent_window_is_not_handed_back(self):
        for spent in ("declined", "exhausted"):
            with self.subTest(spent=spent):
                state = seated()
                who = staff(state, "Angelo", second(state).key)
                at = second(state)
                at.manager_post = ManagerPost(
                    vacancy_day=at.acceptance_day, opportunity=spent)
                before = at.manager_post
                with self.assertRaises(ValueError) as caught:
                    models.appoint_manager(state, at, who)
                self.assertIn("spent window", str(caught.exception))
                self.assertEqual(at.manager_post, before)

    def test_an_occupied_post_is_not_written_over(self):
        state = seated()
        sitting = install(state)
        challenger = staff(state, "Marcus", second(state).key)
        before = second(state).manager_post
        with self.assertRaises(ValueError) as caught:
            models.appoint_manager(state, second(state), challenger)
        self.assertIn("not empty", str(caught.exception))
        self.assertEqual(second(state).manager_post, before)
        self.assertEqual(before.manager_key, sitting.key)

    def test_the_pending_transition_still_works(self):
        # The positive control, so the four refusals above are not
        # proved by an authority that refuses everything.
        state = seated()
        who = staff(state, "Angelo", second(state).key)
        self.assertEqual(second(state).manager_post.opportunity, "pending")
        models.appoint_manager(state, second(state), who)
        self.assertEqual(second(state).manager_post,
                         ManagerPost(manager_key=who.key))


class TestThePolicyInputsAreBound(unittest.TestCase):
    """P4b.3 review: the targeting order and the defense formula READ
    these fields, so a payload validation admits must never make the
    policy throw or answer arbitrarily. Each doctored save is proved
    against a pristine baseline that round-trips."""

    def _baseline(self):
        """The pristine control, proved rather than assumed: the
        payload must round-trip to ITSELF before any doctoring, or a
        refusal below could be the baseline's own defect wearing the
        mutation's name (the standing doctored-payload rule)."""
        state = seated()
        staff(state, "Angelo", second(state).key)
        payload = save.state_to_dict(state)
        restored = save.state_from_dict(payload)
        self.assertEqual(save.state_to_dict(restored), payload)
        return state

    def test_a_reputation_that_cannot_be_compared_is_refused(self):
        for bad in ("bad", None, True, False, float("nan"),
                    float("inf"), float("-inf")):
            with self.subTest(bad=bad):
                state = self._baseline()
                payload = save.state_to_dict(state)
                payload["shops"][0]["reputation"] = bad
                with self.assertRaises(ValueError) as caught:
                    save.state_from_dict(payload)
                self.assertIn("reputation", str(caught.exception))

    def test_the_reachable_reputations_still_load(self):
        # No balance clamp was invented: the domain refuses only what
        # the engine can never produce. NEGATIVE reputation IS
        # reachable — `incoming_raid` subtracts 8 and 12 directly,
        # with no floor — so it belongs in the controls rather than
        # being quietly outlawed by a validator (P4b.3 re-review).
        for good in (-12.0, -8.0, 0, 0.0, 20.0, 50, 100.0):
            with self.subTest(good=good):
                state = self._baseline()
                payload = save.state_to_dict(state)
                payload["shops"][0]["reputation"] = good
                save.state_from_dict(payload)

    def test_a_negative_reputation_is_reached_by_playing_the_game(self):
        # Not asserted from a literal: DRIVEN. A raid that lands
        # subtracts 12 with no floor, so a room already scraping by
        # goes under zero, and the save taken that night carries it.
        # That is why the domain refuses only what cannot be
        # COMPARED, and imposes no range.
        state = seated()
        state.day = second(state).opening_day + 1
        at = second(state)
        at.reputation = 5.0
        at.stash = {"mushrooms": 6}
        staff(state, "Marcus", at.key, nerve=1)
        state.rivals["vinnie"].warning = models.RaidWarning(1, at.key)
        state.rivals["sal"].strength = 0
        phases.night(state, {"routes": {}, "raid": None},
                     {"wagons": phases.WagonNight(state)},
                     Listening([0]), Streams(11))
        self.assertLess(at.reputation, 0.0)
        back = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(back.shop_by_key(at.key).reputation,
                         at.reputation)
        self.assertIn(models.raid_target(back, "vinnie"),
                      {sh.key for sh in back.shops})

    def test_a_nerve_that_cannot_be_added_is_refused(self):
        for bad in ("9", 9.0, None, True):
            with self.subTest(bad=bad):
                state = self._baseline()
                payload = save.state_to_dict(state)
                payload["employees"][0]["nerve"] = bad
                with self.assertRaises(ValueError) as caught:
                    save.state_from_dict(payload)
                self.assertIn("nerve", str(caught.exception))

    def test_a_truthy_roster_flag_is_refused(self):
        for flag in ("hired", "aware", "arrested"):
            for bad in (1, 0, "yes", None):
                with self.subTest(flag=flag, bad=bad):
                    state = self._baseline()
                    payload = save.state_to_dict(state)
                    payload["employees"][0][flag] = bad
                    with self.assertRaises(ValueError) as caught:
                        save.state_from_dict(payload)
                    self.assertIn(flag, str(caught.exception))

    def test_an_impossible_injury_count_is_refused(self):
        for bad in (-1, 2.0, True, "2"):
            with self.subTest(bad=bad):
                state = self._baseline()
                payload = save.state_to_dict(state)
                payload["employees"][0]["injured_days"] = bad
                with self.assertRaises(ValueError) as caught:
                    save.state_from_dict(payload)
                self.assertIn("injured days", str(caught.exception))

    def test_the_targeting_order_is_total_over_what_loads(self):
        # The consequence the domain exists for: whatever survives
        # the boundary, the policy answers without throwing.
        state = self._baseline()
        for reputation in (0.0, 50.0, 100.0):
            for nerve in (0, 5, 10):
                payload = save.state_to_dict(state)
                payload["shops"][0]["reputation"] = reputation
                payload["employees"][0]["nerve"] = nerve
                back = save.state_from_dict(payload)
                self.assertIn(models.raid_target(back, "sal"),
                              {s.key for s in back.shops})


class TestThePostBelongsToItsAddressSpan(unittest.TestCase):
    def test_a_vacancy_before_the_address_existed_is_refused(self):
        # A second room struck on day 14 cannot have emptied on day 1.
        state = seated()
        at = second(state)
        self.assertEqual(at.acceptance_day, 14)
        at.manager_post = ManagerPost(vacancy_day=1, opportunity="pending")
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(state))
        self.assertIn("outside the span this address has existed",
                      str(caught.exception))

    def test_the_acceptance_day_itself_is_allowed(self):
        state = seated()
        at = second(state)
        at.manager_post = ManagerPost(vacancy_day=at.acceptance_day,
                                      opportunity="pending")
        save.state_from_dict(save.state_to_dict(state))
        at.manager_post = ManagerPost(vacancy_day=state.day,
                                      opportunity="pending")
        save.state_from_dict(save.state_to_dict(state))


# ══ THE GHOST GUARD: the authority cannot be bypassed quietly ═════

class TestAGhostManagerIsRefused(unittest.TestCase):
    def test_a_manager_off_the_payroll_is_refused(self):
        state = seated()
        boss = install(state)
        boss.hired = False                       # a route that "forgot"
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(state))
        self.assertIn("cannot hold the post", str(caught.exception))

    def test_a_manager_moved_away_is_refused(self):
        state = seated()
        boss = install(state)
        boss.shop_key = HOME_SHOP_KEY
        with self.assertRaises(ValueError):
            save.state_from_dict(save.state_to_dict(state))

    def test_a_manager_in_custody_is_refused(self):
        state = seated()
        boss = install(state)
        boss.arrested = True
        with self.assertRaises(ValueError):
            save.state_from_dict(save.state_to_dict(state))

    def test_a_manager_who_was_never_read_in_is_refused(self):
        state = seated()
        boss = install(state)
        boss.aware = False
        with self.assertRaises(ValueError):
            save.state_from_dict(save.state_to_dict(state))

    def test_a_vacancy_day_beyond_the_calendar_is_refused(self):
        state = seated()
        second(state).manager_post = ManagerPost(
            vacancy_day=state.day + 1, opportunity="pending")
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(state))
        self.assertIn("outside the span this address has existed",
                      str(caught.exception))


# ══ THE ONE BOUNDARY: appoint / decline / exhaust ════════════════

class TestTheOpportunityBoundary(unittest.TestCase):
    def test_appointing_clears_the_vacancy(self):
        state = seated()
        who = staff(state, "Angelo", second(state).key)
        con = open_doors(state, Listening([0]))
        self.assertEqual(second(state).manager_post,
                         ManagerPost(manager_key=who.key))
        self.assertFalse(second(state).unmanaged)
        self.assertTrue(con.said(f"{who.name} takes the"))

    def test_declining_spends_the_window_and_starts_the_nephew(self):
        state = seated()
        staff(state, "Angelo", second(state).key)
        con = open_doors(state, Listening([1]))       # the last option
        post = second(state).manager_post
        self.assertEqual(post.opportunity, "declined")
        self.assertTrue(second(state).unmanaged)
        self.assertTrue(con.said("nephew"))

    def test_exhaustion_is_a_different_fact_from_declining(self):
        state = seated()                       # nobody eligible at all
        con = open_doors(state)
        self.assertEqual(second(state).manager_post.opportunity,
                         "exhausted")
        self.assertTrue(second(state).unmanaged)
        self.assertIsNone(con.offered("Who runs the"))   # never asked
        self.assertTrue(con.said("nobody to put in charge"))

    def test_the_window_is_offered_once_and_not_again(self):
        state = seated()
        staff(state, "Angelo", second(state).key)
        open_doors(state, Listening([1]))                # declined
        again = open_doors(state, Listening([0]))
        self.assertIsNone(again.offered("Who runs the"))
        self.assertEqual(second(state).manager_post.opportunity,
                         "declined")

    def test_a_fresh_loss_grants_a_fresh_window(self):
        # Canon grants the menu after EACH of arrest, poach,
        # resignation, firing and reassignment — not once per run.
        state = seated()
        staff(state, "Angelo", second(state).key)
        open_doors(state, Listening([0]))                # appointed
        boss = state.shop_by_key(second(state).key)
        who = next(e for e in state.employees
                   if e.key == boss.manager_post.manager_key)
        state.day += 1
        models.release_from_posts(state, who, "fired")
        who.hired = False
        staff(state, "Marcus", second(state).key)
        con = open_doors(state, Listening([0]))
        self.assertIsNotNone(con.offered("Who runs the"))
        self.assertEqual(second(state).manager_post.manager_key,
                         next(e.key for e in state.employees
                              if "Marcus" in e.name))

    def test_the_menu_speaks_districts_and_never_keys(self):
        state = seated()
        staff(state, "Angelo", second(state).key)
        con = open_doors(state, Listening([0]))
        prompt = next(p for p, _o in con.menus if "Who runs" in p)
        self.assertIn("University Hill", prompt)
        for line in con.lines + [prompt]:
            self.assertNotIn("shop2", line)

    def test_the_safe_fallback_is_last(self):
        # An exhausted script answers with the LAST option, and that
        # must never hand somebody the keys by accident.
        state = seated()
        staff(state, "Angelo", second(state).key)
        open_doors(state, Listening())                # no script at all
        self.assertEqual(second(state).manager_post.opportunity,
                         "declined")


class TestNoServiceRunsPastAPendingWindow(unittest.TestCase):
    """Rev. 34 item 2: the boundary sits before service, so an address
    fired-or-reassigned during the SAME morning cannot trade once at
    full capacity before the window arrives."""

    def _service(self, state, con):
        return phases.service(state, {"routes": {}}, con,
                              Streams(5))

    def test_service_resolves_the_window_before_the_doors_open(self):
        state = seated()
        state.day = second(state).opening_day + 1
        staff(state, "Angelo", second(state).key)
        con = Listening([0])
        self._service(state, con)
        self.assertEqual(second(state).manager_post.manager_key,
                         next(e.key for e in state.employees
                              if "Angelo" in e.name))
        self.assertFalse(second(state).unmanaged)

    def test_a_manager_fired_this_morning_is_replaced_before_trading(self):
        state = seated()
        state.day = second(state).opening_day + 1
        boss = install(state)
        staff(state, "Marcus", second(state).key)
        crew = state.hired()
        phases._staff_menu(state, Listening([3, crew.index(boss), 5]),
                           random.Random(1))
        self.assertEqual(second(state).manager_post.opportunity, "pending")
        # The kitchen is NOT yet penalised: the window is unspent.
        self.assertFalse(second(state).unmanaged)
        self._service(state, Listening([0]))
        self.assertIsNotNone(second(state).manager_post.manager_key)
        self.assertFalse(second(state).unmanaged)

    def test_a_declined_window_halves_the_kitchen(self):
        # RENAMED (P4b.3 review): it only ever asserted the kitchen,
        # and a name claiming the ceiling too would have blessed an
        # unasserted half of the contract. The ceiling has its own
        # case below, driven through the laundering boundary.
        state = seated()
        state.day = second(state).opening_day + 1
        at = second(state)
        staff(state, "Angelo", at.key)
        full_kitchen = at.kitchen_cap
        self._service(state, Listening([1]))          # declined
        self.assertTrue(at.unmanaged)
        self.assertEqual(at.kitchen_cap, full_kitchen // 2)

    def test_the_founding_kitchen_never_changes(self):
        state = seated()
        state.day = second(state).opening_day + 1
        home = state.shop_by_key(HOME_SHOP_KEY)
        before = home.kitchen_cap
        self._service(state, Listening([1]))
        self.assertEqual(home.kitchen_cap, before)


class TestTheNephewThinsTheBooks(unittest.TestCase):
    """The ceiling half of §2.4.2's penalty, at the boundary the
    night actually launders through — `total_believable_ceiling` is
    what the player's allowance is computed from, so proving the
    per-shop helper alone would prove the wrong function."""

    def _earning(self):
        state = seated()
        state.day = second(state).opening_day + 1
        home = state.shop_by_key(HOME_SHOP_KEY)
        at = second(state)
        home.legit_revenue_today = 800
        at.legit_revenue_today = 800
        return state, home, at

    def test_the_unmanaged_room_contributes_exactly_half(self):
        state, home, at = self._earning()
        staff(state, "Angelo", at.key)
        managed = shop.total_believable_ceiling(state)
        alone = shop.believable_ceiling(state, at, at.legit_revenue_today)
        phases._management_boundary(state, Listening([1]))   # declined
        self.assertTrue(at.unmanaged)
        thinned = shop.total_believable_ceiling(state)
        # EXACT deltas on the thing that should move, and on the
        # thing that must not.
        self.assertEqual(managed - thinned, alone - alone // 2)
        self.assertEqual(
            shop.believable_ceiling(state, at, at.legit_revenue_today),
            alone // 2)
        self.assertEqual(
            shop.believable_ceiling(state, home, home.legit_revenue_today),
            int(home.legit_revenue_today * data.LAUNDER_FACTOR))

    def test_the_founding_room_s_books_never_thin(self):
        state, home, at = self._earning()
        before = shop.believable_ceiling(state, home,
                                         home.legit_revenue_today)
        phases._management_boundary(state, Listening([1]))
        self.assertTrue(at.unmanaged)
        self.assertIsNone(home.manager_post)
        self.assertEqual(
            shop.believable_ceiling(state, home, home.legit_revenue_today),
            before)

    def test_appointing_leaves_the_books_whole(self):
        state, _home, at = self._earning()
        staff(state, "Angelo", at.key)
        full = shop.total_believable_ceiling(state)
        phases._management_boundary(state, Listening([0]))   # appointed
        self.assertFalse(at.unmanaged)
        self.assertEqual(shop.total_believable_ceiling(state), full)

    def test_a_pending_window_has_not_yet_thinned_anything(self):
        state, _home, at = self._earning()
        self.assertEqual(at.manager_post.opportunity, "pending")
        staff(state, "Angelo", at.key)
        self.assertFalse(at.unmanaged)
        self.assertEqual(
            shop.believable_ceiling(state, at, at.legit_revenue_today),
            int(at.legit_revenue_today * data.LAUNDER_FACTOR))
        whole = shop.total_believable_ceiling(state)
        phases._management_boundary(state, Listening([1]))
        self.assertLess(shop.total_believable_ceiling(state), whole)

# ══ save / load continuity, both directions ══════════════════════

class TestTheWindowSurvivesAReload(unittest.TestCase):
    def test_a_spent_window_is_not_handed_back(self):
        state = seated()
        staff(state, "Angelo", second(state).key)
        open_doors(state, Listening([1]))             # declined
        back = save.state_from_dict(save.state_to_dict(state))
        again = open_doors(back, Listening([0]))
        self.assertIsNone(again.offered("Who runs the"))
        self.assertEqual(second(back).manager_post.opportunity, "declined")

    def test_a_held_window_is_not_consumed_by_reloading(self):
        state = seated()
        staff(state, "Angelo", second(state).key)
        back = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(second(back).manager_post.opportunity, "pending")
        con = open_doors(back, Listening([0]))
        self.assertIsNotNone(con.offered("Who runs the"))

    def test_an_appointment_round_trips(self):
        state = seated()
        who = install(state)
        back = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(second(back).manager_post,
                         ManagerPost(manager_key=who.key))

    def test_a_malformed_post_refuses(self):
        state = seated()
        payload = save.state_to_dict(state)
        for bad in ({"manager_key": "e0", "vacancy_day": 3,
                     "opportunity": "none"},
                    {"manager_key": None, "vacancy_day": None,
                     "opportunity": "pending"},
                    {"manager_key": None, "vacancy_day": 3,
                     "opportunity": "later"},
                    "pending", 3):
            with self.subTest(bad=bad):
                doctored = save.state_to_dict(state)
                for s in doctored["shops"]:
                    if s["key"] != HOME_SHOP_KEY:
                        s["manager_post"] = bad
                with self.assertRaises(ValueError):
                    save.state_from_dict(doctored)
        save.state_from_dict(payload)                # the control loads


class TestTheMigration(unittest.TestCase):
    """Absence is the licence, and two absences mean two things
    (rev. 34 item 1)."""

    def test_the_founding_room_migrates_to_no_post(self):
        payload = save.state_to_dict(new_state())
        for s in payload["shops"]:
            s.pop("manager_post")
        back = save.state_from_dict(payload)
        self.assertIsNone(back.shop_by_key(HOME_SHOP_KEY).manager_post)

    def test_a_dated_address_migrates_to_its_owed_window(self):
        state = seated()
        payload = save.state_to_dict(state)
        acceptance = None
        for s in payload["shops"]:
            if s["key"] != HOME_SHOP_KEY:
                s.pop("manager_post")
                acceptance = s["acceptance_day"]
        back = save.state_from_dict(payload)
        self.assertEqual(second(back).manager_post,
                         ManagerPost(vacancy_day=acceptance,
                                     opportunity="pending"))

    def test_the_migrated_window_round_trips_and_is_stable(self):
        state = seated()
        payload = save.state_to_dict(state)
        for s in payload["shops"]:
            if s["key"] != HOME_SHOP_KEY:
                s.pop("manager_post")
        loaded = save.state_from_dict(payload)
        again = save.state_to_dict(loaded)
        reloaded = save.state_from_dict(again)
        self.assertEqual(save.state_to_dict(reloaded), again)
        self.assertEqual(second(reloaded).manager_post,
                         second(loaded).manager_post)


# ══ the lines the player actually reads ══════════════════════════

class TestTheStoryTellsTheMechanicsTruth(unittest.TestCase):
    """P4b.3 review, item 4: four lines promised something the engine
    does not do. Complete strings are pinned, and no raw key leaks."""

    def test_reassignment_says_tonight_because_it_means_tonight(self):
        state = seated()
        state.day = second(state).opening_day
        who = staff(state, "Angelo", HOME_SHOP_KEY, nerve=9)
        crew = state.hired()
        con = Listening([4, crew.index(who), 0, 5])
        phases._staff_menu(state, con, random.Random(1))
        line = next(ln for ln in con.lines if who.name in ln
                    and "works the" in ln)
        self.assertIn("from tonight", line)
        self.assertNotIn("tomorrow", line)
        # …and it IS tonight: the move is live for the defense the
        # very next question anybody asks.
        self.assertEqual(models.raid_target(state, "sal"), HOME_SHOP_KEY)

    def test_declining_does_not_promise_it_can_be_undone(self):
        state = seated()
        staff(state, "Angelo", second(state).key)
        con = Listening([1])
        phases._management_boundary(state, con)
        _prompt, options = next((p, o) for p, o in con.menus
                                if "Who runs" in p)
        self.assertEqual(options[-1],
                         "Leave it to Carmine's nephew — he keeps the keys")
        self.assertNotIn("for now", options[-1])
        # The window really is gone, which is what the option now says.
        again = Listening([0])
        phases._management_boundary(state, again)
        self.assertIsNone(again.offered("Who runs the"))

    def test_the_price_war_names_the_neighbourhood_it_papers(self):
        state = seated()
        state.day = second(state).opening_day + 1
        staff(state, "Angelo", HOME_SHOP_KEY, nerve=9)   # second is soft
        con = Listening()
        rivals._price_war(state, "vinnie", {"short": "Vinnie"}, con)
        self.assertTrue(con.said("University Hill neighborhood"))
        self.assertEqual(second(state).coupon_days, 3)
        self.assertEqual(state.shop_by_key(HOME_SHOP_KEY).coupon_days, 0)

    def test_the_arriving_raid_names_the_room(self):
        state = seated()
        state.day = second(state).opening_day + 1
        state.rivals["vinnie"].warning = models.RaidWarning(
            1, second(state).key)
        state.rivals["sal"].strength = 0
        con = Listening([0])
        phases.night(state, {"routes": {}, "raid": None},
                     {"wagons": phases.WagonNight(state)}, con, Streams(11))
        self.assertTrue(con.said("The University Hill room."))

    def test_no_raw_key_reaches_the_player_anywhere(self):
        state = seated()
        state.day = second(state).opening_day + 1
        staff(state, "Angelo", second(state).key)
        con = Listening([0])
        phases._management_boundary(state, con)
        phases._staff_menu(state, Listening([5]), random.Random(1))
        rivals._price_war(state, "vinnie", {"short": "Vinnie"}, con)
        rivals._plant(state, state.rivals["sal"], {"short": "Sal"},
                      con, random.Random(3))
        spoken = con.lines + [p for p, _o in con.menus] \
            + [o for _p, opts in con.menus for o in opts]
        for line in spoken:
            for key in (s.key for s in state.shops):
                self.assertNotIn(key, line, line)


class TestOneAddressProseIsUntouched(unittest.TestCase):
    """Rev. 34 item 5: released narration is frozen byte-for-byte,
    not merely the strings the golden digests."""

    def test_the_raid_header_gains_no_address_line(self):
        state = new_state()
        state.day = 6
        state.clean, state.dirty = 4000, 400
        state.rivals["vinnie"].warning = models.RaidWarning(
            1, HOME_SHOP_KEY)
        state.rivals["sal"].strength = 0
        con = Listening([0])
        phases.night(state, {"routes": {}, "raid": None},
                     {"wagons": phases.WagonNight(state)}, con, Streams(11))
        self.assertFalse(con.said("room. They have known"))

    def test_the_price_war_says_only_what_it_always_said(self):
        state = new_state()
        con = Listening()
        rivals._price_war(state, "vinnie", {"short": "Vinnie"}, con)
        self.assertEqual(
            con.lines,
            ["• Vinnie papers the neighborhood with two-for-one "
             "coupons. Expect thin order books for a few days."])

    def test_the_tip_says_only_what_it_always_said(self):
        state = new_state()
        con = Listening()
        rivals._plant(state, state.rivals["sal"], {"short": "Sal"},
                      con, random.Random(3))
        self.assertEqual(
            con.lines,
            ["• An anonymous tip sends a patrol crawling past your "
             "block all night."])


# ══ the allocation lever, and what it shows ══════════════════════

class TestTheAllocationSurface(unittest.TestCase):
    def test_it_is_absent_while_one_address_exists(self):
        state = new_state()
        con = Listening([4])
        phases._staff_menu(state, con, random.Random(1))
        prompt, options = con.menus[0]
        self.assertEqual(options, ["Hire", "Read someone in",
                                   "Give a raise (+morale/loyalty)",
                                   "Let someone go", "Back"])

    def test_it_appears_with_a_second_address(self):
        state = seated()
        con = Listening([5])
        phases._staff_menu(state, con, random.Random(1))
        _prompt, options = con.menus[0]
        self.assertIn("Move somebody to another address", options)
        self.assertEqual(options[-1], "Back")

    def test_the_board_shows_strength_headcount_and_the_guard(self):
        state = seated()
        at = second(state)
        at.upgrades.add("guard")
        muscle = staff(state, "Angelo", at.key, nerve=9)
        con = Listening([5])
        phases._staff_menu(state, con, random.Random(1))
        self.assertTrue(con.said("defense 13"))          # 9 + 4
        self.assertTrue(con.said("night security +4"))
        self.assertTrue(con.said(muscle.name))
        self.assertTrue(con.said("University Hill"))
        for line in con.lines:
            self.assertNotIn("shop2", line)

    def test_a_construction_site_may_still_be_staffed(self):
        # §2.4.2 allows staffing and pantry supply while it is built.
        state = seated()
        state.day = second(state).acceptance_day        # still building
        who = staff(state, "Angelo", HOME_SHOP_KEY)
        crew = state.hired()
        con = Listening([4, crew.index(who), 0, 5])
        phases._staff_menu(state, con, random.Random(1))
        self.assertEqual(who.shop_key, second(state).key)
        self.assertEqual(who.familiarity, {})

    def test_moving_somebody_changes_what_the_rival_chooses(self):
        # The whole point of the lever, as an exact change of answer.
        state = seated()
        state.day = second(state).opening_day
        muscle = staff(state, "Angelo", HOME_SHOP_KEY, nerve=9)
        self.assertEqual(models.raid_target(state, "sal"),
                         second(state).key)
        crew = state.hired()
        phases._staff_menu(state,
                           Listening([4, crew.index(muscle), 0, 5]),
                           random.Random(1))
        self.assertEqual(muscle.shop_key, second(state).key)
        self.assertEqual(models.raid_target(state, "sal"), HOME_SHOP_KEY)


if __name__ == "__main__":
    unittest.main()
