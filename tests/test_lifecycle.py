"""P4b.1a — the address lifecycle authority (§2.4.2; rev. 29 items
3–4): the recorded dates, the phase derivation, the central capability
view, the wagon-claim refusal, and the save-load transitions.

These are SYNTHETIC two-address states, constructed deliberately: no
released branch can create one, which is exactly why they are built
here (§7's P4b.1a clause) — every defect this PR could introduce is
invisible to a one-shop run and to every green gate.
"""

import random
import unittest

import test_war_mechanics as war_mechanics
from extra_toppings import (data, market, models, phases, raids, routes, shop,
                            save, war)
from extra_toppings.rng import Streams
from extra_toppings.models import (ADDRESS_CAPABILITIES,
                                   CONSTRUCTION_ALLOWED,
                                   CONSTRUCTION_DAYS, HOME_SHOP_KEY,
                                   Shop, Wagon, address_allows,
                                   new_state, open_shops, shop_is_open,
                                   validate_addresses, wagon_claim)
from extra_toppings.ui import ScriptedConsole


class Listening(ScriptedConsole):
    """A scripted console that also keeps what was SAID — the
    refusals here are prose, and prose does not reach `transcript`,
    which records only decision points."""

    def __init__(self, script=None):
        super().__init__(script)
        self.lines: list = []
        self.menus: list = []

    def menu(self, prompt, options):
        self.menus.append((prompt, list(options)))
        return super().menu(prompt, options)

    def offered(self, prompt):
        """The options a given prompt actually showed."""
        return next((o for p, o in self.menus if p == prompt), [])

    def say(self, text: str = "") -> None:
        self.lines.append(text)

    def bullet(self, text: str) -> None:
        self.lines.append(f"• {text}")

    def said(self, fragment: str) -> bool:
        return any(fragment in line for line in self.lines)


def _route_plan(state, shop_key, wagon_key, driver=None, **over):
    """A COMPLETE route plan. Every canonical field is named,
    including a real driver, because the schedule refuses a plan
    missing one — a gap accepted for test convenience is how a
    canonical field stops being canonical."""
    if driver is None:
        driver = next(e for e in state.employees if e.driving >= 4)
        driver.hired = driver.aware = True
    plan = {"district": "old_harbor", "driver": driver,
            "ride_along": False, "cargo": {}, "legit": 0,
            "origin_shop": shop_key, "wagon_key": wagon_key}
    plan.update(over)
    return plan


def _raid_plan(state, objective):
    """A raid planned through the REAL planner: pick the rival, the
    objective, the crew, unarmed."""
    script = [0, ("steal_stock", "ledger", "sabotage").index(objective), 0, False, False]
    return raids.plan_raid(
        state, Listening(script), random.Random(3), reserved=[],
        wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)),
            home=state.shop_by_key(models.HOME_SHOP_KEY))


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


class TestPlanningAsksTheLifecycleToo(unittest.TestCase):
    """The planning half of rev. 29 item 3's "planning AND execution".

    One view (`phases.planned_wagon`) composes the night's planned
    reservations with `models.wagon_claim`; no consumer runs its own
    lifecycle check. The refusal must reach the player at the MENU,
    not as a RuntimeError when the crew is loading.
    """

    def test_a_construction_wagon_cannot_be_planned_out(self):
        state = _with_site(day=6, acceptance=5)
        view = phases.planned_wagon(state, {"routes": {}}, "shop2")
        self.assertFalse(view.available)
        self.assertEqual(view.blocked_by, "lifecycle")
        self.assertIn("contractor's yard", view.note)

    def test_the_open_address_plans_freely_alongside_it(self):
        state = _with_site(day=6, acceptance=5)
        view = phases.planned_wagon(state, {"routes": {}}, HOME_SHOP_KEY)
        self.assertTrue(view.available)
        self.assertEqual((view.note, view.blocked_by), ("", ""))

    def test_a_planned_job_outranks_the_lifecycle_as_the_reason(self):
        # Ordering matches WagonNight.note_at: a wagon the pickup has
        # is never described as sitting at the contractor's yard.
        state = _with_site(day=7, acceptance=5)
        view = phases.planned_wagon(
            state, {"routes": {},
                    "salvage": {"rival": "vinnie",
                                "origin_shop": "shop2"}}, "shop2")
        self.assertFalse(view.available)
        self.assertEqual(view.blocked_by, "salvage")
        self.assertEqual(view.note, phases.WAGON_NOTES["salvage"])

    def test_one_addresss_route_never_grounds_anothers_wagon(self):
        # THE cross-address repro. A route out of the home shop is a
        # reservation of the HOME wagon; shop 2's wagon is a different
        # vehicle at a different address, and a global "the wagon does
        # one job a night" is exactly the single-wagon model P4a
        # removed. Invisible to every gate — no released branch can
        # build two addresses — so it is pinned directly.
        state = _with_site(day=7, acceptance=5)          # shop2 OPEN
        plans = {"routes": {HOME_SHOP_KEY: _route_plan(
            state, HOME_SHOP_KEY, models.HOME_WAGON_KEY)}}
        home = phases.planned_wagon(state, plans, HOME_SHOP_KEY)
        self.assertFalse(home.available)
        self.assertEqual(home.blocked_by, "route")
        away = phases.planned_wagon(state, plans, "shop2")
        self.assertTrue(away.available)
        self.assertEqual(away.free, ("wagon2",))

    def test_the_view_names_which_wagons_not_merely_whether(self):
        # Identity, not a boolean: an address with two wagons must be
        # representable, and a consumer must know WHICH one it takes.
        state = _with_site(day=7, acceptance=5)
        state.wagons.append(Wagon(key="wagon3", shop_key="shop2"))
        view = phases.planned_wagon(state, {"routes": {}}, "shop2")
        self.assertEqual(view.free, ("wagon2", "wagon3"))
        self.assertEqual(view.first, "wagon2")
        plans = {"routes": {"shop2": _route_plan(state, "shop2", "wagon2")}}
        one_left = phases.planned_wagon(state, plans, "shop2")
        self.assertTrue(one_left.available)
        self.assertEqual(one_left.free, ("wagon3",))

    def test_a_wagon_job_must_name_an_exact_origin_key(self):
        # Not merely truthy: a non-string origin is a malformed plan,
        # and inferring the home shop from it is the implicit default
        # rev. 27 item 7 forbids.
        state = _with_site(day=7, acceptance=5)
        for bogus in ({}, {"origin_shop": ""}, {"origin_shop": None},
                      {"origin_shop": 1}, {"origin_shop": True}):
            with self.assertRaises(ValueError, msg=repr(bogus)):
                phases.plan_origin(state, bogus)
        self.assertEqual(
            phases.plan_origin(state, {"origin_shop": "shop2"}), "shop2")

    def test_an_origin_naming_no_address_is_refused(self):
        # Shape is not identity. A "ghost" origin has the right type
        # and belongs to no address, so it reserved nothing and every
        # real wagon reported itself free — a wagonless job sitting in
        # the plans, which is worse than a refused one.
        state = _with_site(day=7, acceptance=5)
        with self.assertRaises(KeyError):
            phases.plan_origin(state, {"origin_shop": "ghost"})
        plans = {"routes": {HOME_SHOP_KEY: _route_plan(
            state, "ghost", models.HOME_WAGON_KEY)}}
        with self.assertRaises(KeyError):
            phases.planned_jobs_at(state, plans, HOME_SHOP_KEY)
        with self.assertRaises(KeyError):
            phases.planned_wagon(state, plans, HOME_SHOP_KEY)
        with self.assertRaises(KeyError):
            phases.planned_wagon(state, plans, "shop2")

    def test_a_pickup_naming_no_address_is_refused_before_it_exists(self):
        # The planner validates its own origin, so a ghost address
        # never becomes a returned job no wagon can serve.
        state, _rosa = war_mechanics.TestSalvage._captured(
            war_mechanics.TestSalvage())
        with self.assertRaises(KeyError):
            war.plan_salvage(
                state, Listening([0]), reserved=[],
                wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)),
                origin_shop="ghost")

    def test_a_free_view_refuses_to_name_a_wagon_it_has_not_got(self):
        blocked = phases.planned_wagon(
            _with_site(day=6, acceptance=5), {"routes": {}}, "shop2")
        with self.assertRaises(RuntimeError):
            blocked.first

    def test_planning_and_execution_agree_on_every_day(self):
        # The two halves must never disagree — that disagreement is
        # exactly what produced a menu that accepted a plan execution
        # would then refuse.
        for day in (5, 6, 7, 8):
            state = _with_site(day=day, acceptance=5)
            planned = phases.planned_wagon(state, {"routes": {}}, "shop2")
            executed = phases.WagonNight(state).view_at("shop2")
            self.assertEqual(planned.available, executed.available, day)
            self.assertEqual(planned.note, executed.note, day)

    def test_the_opening_morning_flips_both_halves_together(self):
        state = _with_site(day=6, acceptance=5)
        self.assertFalse(phases.planned_wagon(state, {"routes": {}}, "shop2").available)
        state.day = 7                       # the recorded opening day
        view = phases.planned_wagon(state, {"routes": {}}, "shop2")
        self.assertTrue(view.available)
        self.assertTrue(phases.WagonNight(state).available_at("shop2"))

    def test_a_contradictory_planning_answer_cannot_be_built(self):
        with self.assertRaises(ValueError):     # free, yet blocked
            models.PlannedWagon(("wagon2",), "route", "out on a route")
        with self.assertRaises(ValueError):     # blocked by nothing
            models.PlannedWagon()
        with self.assertRaises(ValueError):     # blocked, but silent
            models.PlannedWagon(blocked_by="route", note="")

    def test_free_wagons_must_be_a_tuple_of_real_keys(self):
        # A bare string is iterable, so `PlannedWagon("wagon2")` used
        # to load and hand back "w" as the wagon to take.
        for bogus in ("wagon2", ["wagon2"], None, 3):
            with self.assertRaises(ValueError, msg=repr(bogus)):
                models.PlannedWagon(bogus)
        with self.assertRaises(ValueError):          # empty key
            models.PlannedWagon(("",))
        with self.assertRaises(ValueError):          # non-string key
            models.PlannedWagon((1,))
        with self.assertRaises(ValueError):          # the same wagon twice
            models.PlannedWagon(("wagon2", "wagon2"))

    def test_a_job_block_carries_its_canonical_note(self):
        # One home for the prose: a salvage block cannot carry a
        # lifecycle sentence, or any other job's.
        with self.assertRaises(ValueError):
            models.PlannedWagon(blocked_by="salvage",
                                note="at the contractor's yard")
        with self.assertRaises(ValueError):
            models.PlannedWagon(blocked_by="route",
                                note=models.WAGON_NOTES["salvage"])
        with self.assertRaises(ValueError):
            models.PlannedWagon(blocked_by="unhoused", note="somewhere")
        # Only the lifecycle names an address, so only it is free prose.
        models.PlannedWagon(blocked_by="lifecycle",
                            note="the University Hill wagon is still "
                                 "at the contractor's yard")

    def test_an_unknown_block_is_refused_not_carried(self):
        # The vocabulary is closed: arbitrary prose in `blocked_by`
        # would become a case no consumer knows how to render, and
        # the renderer would silently fall through to the route line.
        for bogus in ("banana", "planned", "Route", ""):
            with self.assertRaises(ValueError, msg=bogus):
                models.PlannedWagon(blocked_by=bogus, note="somewhere")


class TestTheRefusalReachesThePlayer(unittest.TestCase):
    """Through the REAL planning functions, not their callers: the
    lifecycle's words must arrive in the player's prose, and every
    pre-existing cause must keep the sentence it already had."""

    def _yard_view(self):
        state = _with_site(day=6, acceptance=5)
        return phases.planned_wagon(state, {"routes": {}}, "shop2")

    def test_a_raid_says_the_wagon_is_at_the_yard(self):
        state = new_state()
        con = Listening()
        raids.plan_raid(state, con, random.Random(3), reserved=[],
                        wagon=self._yard_view(),
            home=state.shop_by_key(models.HOME_SHOP_KEY))
        # THE COMPLETE SENTENCE, not fragments: the first cut read
        # "The wagon is the University Hill wagon is still at the
        # contractor's yard", and every fragment assertion passed.
        self.assertTrue(con.said(
            "  The University Hill wagon is still at the contractor's "
            "yard — whatever the crew takes, they carry on foot."),
            con.lines)

    def test_a_route_held_wagon_keeps_the_sentence_it_always_had(self):
        # The route case is the one the old literal was written for,
        # so it must come through the correction byte-identical.
        state = new_state()
        con = Listening()
        raids.plan_raid(state, con, random.Random(3), reserved=[],
                        wagon=models.PlannedWagon(
                            blocked_by="route",
                            note=models.WAGON_NOTES["route"]),
            home=state.shop_by_key(models.HOME_SHOP_KEY))
        self.assertTrue(con.said(
            "The wagon is out on tonight's route — whatever the crew "
            "takes, they carry on foot."))

    def test_a_ledger_raid_is_unaffected_and_goes_on_foot(self):
        # Only a stock theft loads the wagon (rev. 26); the others
        # were always on foot and must not acquire a refusal.
        state = new_state()
        con = Listening()
        raids.plan_raid(state, con, random.Random(3), reserved=[],
                        wagon=models.PlannedWagon(("wagon1",)),
            home=state.shop_by_key(models.HOME_SHOP_KEY))
        self.assertFalse(con.said("contractor's yard"))

    def test_salvage_says_the_wagon_is_at_the_yard(self):
        state, _rosa = war_mechanics.TestSalvage._captured(
            war_mechanics.TestSalvage())
        con = Listening()
        plan = war.plan_salvage(state, con, reserved=[],
                                wagon=self._yard_view(),
                                origin_shop="shop2")
        self.assertIsNone(plan)
        self.assertTrue(con.said(
            "  The University Hill wagon is still at the contractor's "
            "yard — the stockroom isn't going anywhere."), con.lines)

    def test_salvage_without_a_note_keeps_its_existing_sentence(self):
        state, _rosa = war_mechanics.TestSalvage._captured(
            war_mechanics.TestSalvage())
        con = Listening()
        war.plan_salvage(state, con, reserved=[],
                         wagon=models.PlannedWagon(
                             blocked_by="route",
                             note=models.WAGON_NOTES["route"]),
                         origin_shop=HOME_SHOP_KEY)
        self.assertTrue(con.said(
            "The wagon is spoken for tonight — the stockroom "
            "isn't going anywhere."))


class TestTheAbsenceSentenceNamesTheRightJob(unittest.TestCase):
    """The declared behaviour change: the sentence is rendered FROM
    the blocking job. Before this, every night-consumer cause named
    tonight's route, so a wagon the PICKUP had was described as being
    out on the route — reachable in the released war branch."""

    def test_each_job_names_itself(self):
        for job, expected in (
                ("route", "The wagon is out on tonight's route"),
                ("salvage", "The wagon is out on tonight's pickup"),
                ("raid", "The wagon is out with the night crew"),
                ("decoy", "The wagon is already loaded and gone")):
            self.assertEqual(
                models.wagon_gone_line(models.PlannedWagon(
                    blocked_by=job, note=models.WAGON_NOTES[job])),
                expected)

    def test_the_lifecycle_names_the_address(self):
        view = phases.planned_wagon(
            _with_site(day=6, acceptance=5), {"routes": {}}, "shop2")
        self.assertEqual(
            models.wagon_gone_line(view),
            "The University Hill wagon is still at the contractor's yard")

    def test_a_salvage_held_wagon_no_longer_claims_the_route(self):
        # The defect, as the player met it: the pickup has the wagon
        # and the raid line said it was out on a route.
        state = new_state()
        con = Listening()
        raids.plan_raid(state, con, random.Random(3), reserved=[],
                        wagon=models.PlannedWagon(
                            blocked_by="salvage",
                            note=models.WAGON_NOTES["salvage"]),
            home=state.shop_by_key(models.HOME_SHOP_KEY))
        self.assertTrue(con.said(
            "  The wagon is out on tonight's pickup — whatever the "
            "crew takes, they carry on foot."), con.lines)
        self.assertFalse(con.said("out on tonight's route"))

    def test_a_free_wagon_has_no_absence_to_explain(self):
        with self.assertRaises(ValueError):
            models.wagon_gone_line(models.PlannedWagon(("wagon1",)))

    def test_the_renderer_refuses_loose_strings(self):
        # Taking two primitives undid the typed protection: an
        # invalid pair produced a KeyError or a wrong sentence
        # instead of being unrepresentable.
        for bogus in (("route", "out on tonight's route"), "route",
                      None, 3):
            with self.assertRaises(TypeError, msg=repr(bogus)):
                models.wagon_gone_line(bogus)


class TestTheOneShopPlanningPathIsUnchanged(unittest.TestCase):
    """The behaviour-equivalence anchor, through PRODUCTION `morning`.

    A one-address world can never reach the lifecycle refusal — the
    sole address must be the undated founding one, and an undated
    address is open on every day — so the released game's planning
    path is untouched by construction. Proved, not assumed.
    """

    def test_the_real_morning_plans_a_route_with_no_refusal(self):
        state = new_state()
        # Option 6 is "plan tonight's route"; then leave the menu.
        con = Listening([6, 0, 0, 0, 0, 0, 0, 0, 8])
        phases.morning(state, con, Streams(7))
        self.assertFalse(con.said("contractor's yard"))
        self.assertFalse(con.said("No route leaves here tonight"))

    def test_no_one_shop_world_can_reach_the_refusal(self):
        # Structural, not statistical: validation admits only worlds
        # whose sole address is undated, and those are always open.
        state = new_state()
        validate_addresses(state)
        self.assertTrue(
            phases.planned_wagon(state, {"routes": {}}, HOME_SHOP_KEY).available)
        for day in (1, 15, 30):
            state.day = day
            self.assertTrue(
                phases.planned_wagon(state, {"routes": {}}, HOME_SHOP_KEY).available)


class TestPlansCarryTheirWagon(unittest.TestCase):
    """Conditions 2-4: a plan records WHICH wagon it takes, or
    records going on foot, and execution spends THAT vehicle rather
    than choosing again by address."""

    def test_a_route_plan_names_its_wagon(self):
        # One address here deliberately: `plan_route` still resolves
        # its origin through `operating_shop`, which refuses two — the
        # conversion that lifts it is the next commit, and the
        # two-address route is one of its acceptance conditions.
        state = new_state()
        market.roll_prices(state, random.Random(3))     # a real board
        for e in state.employees[:2]:
            e.hired = e.aware = True
        view = phases.planned_wagon(state, {"routes": {}}, HOME_SHOP_KEY)
        plan = routes.plan_route(state, Listening([0, 0, False, 0, 0]),
                                 random.Random(3), reserved=[],
                                 wagon=view,
            origin=state.shop_by_key(models.HOME_SHOP_KEY))
        self.assertIsNotNone(plan)
        self.assertEqual(plan["wagon_key"], models.HOME_WAGON_KEY)
        self.assertEqual(plan["origin_shop"], HOME_SHOP_KEY)

    def test_a_salvage_plan_names_its_wagon(self):
        state, _rosa = war_mechanics.TestSalvage._captured(
            war_mechanics.TestSalvage())
        plan = war.plan_salvage(
            state, Listening([0]), reserved=[],
            wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)),
            origin_shop=HOME_SHOP_KEY)
        self.assertEqual(plan["wagon_key"], models.HOME_WAGON_KEY)

    def test_a_stock_theft_names_its_wagon_others_record_on_foot(self):
        # rev. 26: only a stock theft loads one. The others do not
        # leave the question unanswered — they record None.
        state = new_state()
        for e in state.employees[:2]:
            e.hired = e.aware = True
        for objective, expected in (("steal_stock",
                                     models.HOME_WAGON_KEY),
                                    ("ledger", None),
                                    ("sabotage", None)):
            plan = _raid_plan(state, objective)
            self.assertEqual(plan["wagon_key"], expected, objective)

    def test_execution_spends_the_named_wagon(self):
        state = _with_site(day=7, acceptance=5)
        night = phases.WagonNight(state)
        self.assertTrue(night.claim_key("wagon2", "route").claimed)
        self.assertEqual(night.claims, {"wagon2": "route"})
        # The home wagon is untouched: a named key spends one vehicle.
        self.assertTrue(night.available_at(HOME_SHOP_KEY))

    def test_a_wagon_taken_since_planning_reports_gone_not_swapped(self):
        # The bug this closes: execution used to ask the ADDRESS for a
        # wagon, so a second job could be handed a different vehicle
        # that happened to sit there.
        state = _with_site(day=7, acceptance=5)
        state.wagons.append(Wagon(key="wagon3", shop_key="shop2"))
        night = phases.WagonNight(state)
        self.assertTrue(night.claim_key("wagon2", "route").claimed)
        # The refusal names the job that HAS it — asking the address
        # would say nothing, because wagon3 is still parked there.
        spent = night.claim_key("wagon2", "raid")
        self.assertFalse(spent.claimed)
        self.assertEqual(spent.blocked_by, "route")
        self.assertEqual(spent.sentence,
                         "The wagon is out on tonight's route")
        self.assertTrue(night.available_at("shop2"))
        self.assertEqual(night.claims, {"wagon2": "route"})

    def test_a_construction_wagon_cannot_be_claimed_by_key(self):
        state = _with_site(day=6, acceptance=5)
        spent = phases.WagonNight(state).claim_key("wagon2", "route")
        self.assertFalse(spent.claimed)
        self.assertEqual(spent.blocked_by, "lifecycle")
        self.assertIn("contractor's yard", spent.note)

    def test_claiming_a_ghost_wagon_is_incoherence_not_bad_luck(self):
        state = _with_site(day=7, acceptance=5)
        night = phases.WagonNight(state)
        with self.assertRaises(KeyError):
            night.claim_key("ghost", "route")
        with self.assertRaises(ValueError):
            night.claim_key("wagon2", "joyride")

    def test_two_addresses_spend_their_own_wagons_independently(self):
        state = _with_site(day=7, acceptance=5)
        night = phases.WagonNight(state)
        self.assertTrue(night.claim_key(models.HOME_WAGON_KEY, "route").claimed)
        self.assertTrue(night.claim_key("wagon2", "route").claimed)
        self.assertEqual(night.claims,
                         {models.HOME_WAGON_KEY: "route",
                          "wagon2": "route"})

    def test_a_raid_names_the_wagon_a_scrubbed_route_gives_back(self):
        # Behaviour PRESERVED: planning records the vehicle even while
        # a route holds it, because a route scrubbed before departure
        # frees it and the crew leaves in it. The key is the identity;
        # availability is execution's question.
        state = new_state()
        for e in state.employees[:2]:
            e.hired = e.aware = True
        plans = {"routes": {HOME_SHOP_KEY: _route_plan(
            state, HOME_SHOP_KEY, models.HOME_WAGON_KEY)}}
        self.assertFalse(
            phases.planned_wagon(state, plans, HOME_SHOP_KEY).available)
        plan = _raid_plan(state, "steal_stock")
        self.assertEqual(plan["wagon_key"], models.HOME_WAGON_KEY)


class TestDepartureIsWhenTheWagonIsClaimed(unittest.TestCase):
    """The claim happens where the job actually rolls — inside
    service — not at nightfall after inventory has already moved.
    Every case drives the REAL commit path."""

    def _world(self):
        state = new_state()
        market.roll_prices(state, random.Random(3))
        driver = next(e for e in state.employees if e.driving >= 4)
        driver.hired = driver.aware = True
        home = state.shop_by_key(HOME_SHOP_KEY)
        home.stash = {"mushrooms": 4}
        home.ingredients = 40
        home.delivery_pool = 10
        return state, home, driver

    def _plan(self, driver, **over):
        plan = {"district": "old_harbor", "driver": driver,
                "ride_along": False, "cargo": {"mushrooms": 2},
                "legit": 3, "origin_shop": HOME_SHOP_KEY,
                "wagon_key": models.HOME_WAGON_KEY}
        plan.update(over)
        return plan

    def test_an_unknown_wagon_refuses_with_inventory_untouched(self):
        state, home, driver = self._world()
        with self.assertRaises(KeyError):
            phases._commit_route(state, self._plan(driver,
                                                   wagon_key="ghost"),
                                 Listening(), phases.WagonNight(state))
        self.assertEqual(home.stash["mushrooms"], 4)
        self.assertEqual(home.ingredients, 40)

    def test_a_wagon_housed_elsewhere_refuses_untouched(self):
        # Shop 1 as origin, shop 2's wagon: two well-formed halves and
        # no coherent assignment.
        state = _with_site(day=7, acceptance=5)
        market.roll_prices(state, random.Random(3))
        driver = next(e for e in state.employees if e.driving >= 4)
        driver.hired = driver.aware = True
        home = state.shop_by_key(HOME_SHOP_KEY)
        home.stash, home.ingredients, home.delivery_pool = (
            {"mushrooms": 4}, 40, 10)
        with self.assertRaises(ValueError):
            phases._commit_route(state,
                                 self._plan(driver, wagon_key="wagon2"),
                                 Listening(), phases.WagonNight(state))
        self.assertEqual(home.stash["mushrooms"], 4)
        self.assertEqual(home.ingredients, 40)

    def test_a_wagon_taken_since_planning_scrubs_untouched(self):
        state, home, driver = self._world()
        wagons = phases.WagonNight(state)
        wagons.claim_key(models.HOME_WAGON_KEY, "raid")   # gone already
        con = Listening()
        self.assertFalse(phases._commit_route(state, self._plan(driver),
                                              con, wagons))
        self.assertEqual(home.stash["mushrooms"], 4)
        self.assertEqual(home.ingredients, 40)
        self.assertTrue(con.said("scrubbed"), con.lines)

    def test_a_departed_route_claims_that_exact_wagon(self):
        state, home, driver = self._world()
        wagons = phases.WagonNight(state)
        self.assertTrue(phases._commit_route(state, self._plan(driver),
                                             Listening(), wagons))
        self.assertEqual(wagons.claims,
                         {models.HOME_WAGON_KEY: "route"})
        self.assertEqual(home.stash["mushrooms"], 2)      # it loaded
        self.assertFalse(wagons.available_at(HOME_SHOP_KEY))

    def test_a_scrubbed_route_leaves_the_wagon_for_the_raid(self):
        # The driver is gone, so the route never rolls — and never
        # takes the wagon with it.
        state, home, driver = self._world()
        driver.hired = False
        wagons = phases.WagonNight(state)
        self.assertFalse(phases._commit_route(state, self._plan(driver),
                                              Listening(), wagons))
        self.assertEqual(wagons.claims, {})
        self.assertTrue(wagons.available_at(HOME_SHOP_KEY))
        self.assertEqual(home.stash["mushrooms"], 4)

    def test_service_hands_the_night_the_authority_it_spent(self):
        # The seam this closes: the authority used to be created AFTER
        # the jobs it governs had already run.
        state, _home, driver = self._world()
        plans = {"routes": {HOME_SHOP_KEY: self._plan(driver)}}
        report = phases.service(state, plans, Listening([0]),
                                Streams(3))
        self.assertIn("wagons", report)
        self.assertEqual(report["wagons"].claims,
                         {models.HOME_WAGON_KEY: "route"})

    def test_night_refuses_to_invent_an_authority(self):
        state, _home, _driver = self._world()
        with self.assertRaises(ValueError):
            phases.night(state, {"routes": {}}, {}, Listening(), Streams(3))


class TestTheClaimCarriesItsOwnReason(unittest.TestCase):
    """The authority that decides why a named wagon cannot leave says
    so in its result. Reconstructing the reason from the ADDRESS is
    what breaks under a fleet."""

    def _two_wagons(self):
        state = _with_site(day=7, acceptance=5)
        state.wagons.append(Wagon(key="wagon3", shop_key="shop2"))
        return state

    def test_the_reason_survives_a_second_wagon_at_the_address(self):
        # THE fleet repro. wagon2 is spoken for; wagon3 is parked
        # right there. Asking the address "why is the wagon gone?"
        # answers "it isn't" — so a caller reconstructing prose that
        # way announces "the wagon is gone" about an address that has
        # one. The claim result knows better.
        state = self._two_wagons()
        night = phases.WagonNight(state)
        self.assertTrue(night.claim_key("wagon2", "route").claimed)
        self.assertEqual(night.note_at("shop2"), "")     # nothing gone
        spent = night.claim_key("wagon2", "raid")
        self.assertFalse(spent.claimed)
        self.assertEqual(spent.wagon_key, "wagon2")
        self.assertEqual(spent.blocked_by, "route")
        self.assertEqual(spent.sentence,
                         "The wagon is out on tonight's route")

    def test_a_claim_result_cannot_contradict_itself(self):
        with self.assertRaises(ValueError):      # spent, yet refused
            models.ClaimResult(True, "wagon2", "route",
                               models.WAGON_NOTES["route"])
        with self.assertRaises(ValueError):      # refused, no reason
            models.ClaimResult(False, "wagon2")
        with self.assertRaises(ValueError):      # refused, silent
            models.ClaimResult(False, "wagon2", "route", "")
        with self.assertRaises(ValueError):      # outside the words
            models.ClaimResult(False, "wagon2", "banana", "somewhere")
        with self.assertRaises(ValueError):      # names no wagon
            models.ClaimResult(True, "")

    def test_a_route_scrub_reads_the_result_not_the_address(self):
        # Through the REAL commit path, with a second wagon parked at
        # the origin so the address-derived note would be empty.
        state = new_state()
        market.roll_prices(state, random.Random(3))
        state.wagons.append(Wagon(key="wagon9",
                                  shop_key=HOME_SHOP_KEY))
        driver = next(e for e in state.employees if e.driving >= 4)
        driver.hired = driver.aware = True
        home = state.shop_by_key(HOME_SHOP_KEY)
        home.stash, home.ingredients, home.delivery_pool = (
            {"mushrooms": 4}, 40, 10)
        wagons = phases.WagonNight(state)
        wagons.claim_key(models.HOME_WAGON_KEY, "raid")
        con = Listening()
        plan = {"district": "old_harbor", "driver": driver,
                "ride_along": False, "cargo": {"mushrooms": 2},
                "legit": 3, "origin_shop": HOME_SHOP_KEY,
                "wagon_key": models.HOME_WAGON_KEY}
        self.assertFalse(phases._commit_route(state, plan, con, wagons))
        self.assertTrue(con.said("The wagon is out with the night crew"),
                        con.lines)
        self.assertFalse(con.said("the wagon is gone"))
        self.assertEqual(home.stash["mushrooms"], 4)


class TestBlockAndNoteAgreeOrAreRefused(unittest.TestCase):
    """One contract, shared by every value carrying a block. A second
    copy is how `ClaimResult` came to accept a lifecycle note under a
    `route` blocker — where the renderer ignored the note and
    announced the route."""

    def test_a_wrong_note_under_a_right_blocker_is_refused(self):
        for kind in (models.ClaimResult, models.PlannedWagon):
            for blocker, note in (
                    ("route", "at the contractor's yard"),
                    ("route", models.WAGON_NOTES["salvage"]),
                    ("salvage", models.WAGON_NOTES["route"]),
                    ("decoy", "somewhere else entirely")):
                with self.assertRaises(ValueError,
                                       msg=f"{kind.__name__} "
                                           f"{blocker}/{note}"):
                    if kind is models.ClaimResult:
                        kind(False, "wagon2", blocker, note)
                    else:
                        kind(blocked_by=blocker, note=note)

    def test_an_empty_lifecycle_note_is_refused(self):
        # Lifecycle prose is free, but it is not optional — it is the
        # only block that names WHICH address is still being built.
        with self.assertRaises(ValueError):
            models.ClaimResult(False, "wagon2", "lifecycle", "")
        with self.assertRaises(ValueError):
            models.PlannedWagon(blocked_by="lifecycle", note="")

    def test_unhoused_carries_its_canonical_note(self):
        for kind in (models.ClaimResult, models.PlannedWagon):
            with self.assertRaises(ValueError):
                if kind is models.ClaimResult:
                    kind(False, "wagon2", "unhoused", "nowhere")
                else:
                    kind(blocked_by="unhoused", note="nowhere")
        models.ClaimResult(False, "wagon2", "unhoused",
                           models.UNHOUSED_NOTE)
        models.PlannedWagon(blocked_by="unhoused",
                            note=models.UNHOUSED_NOTE)

    def test_an_unknown_blocker_is_refused_in_both_values(self):
        for kind in (models.ClaimResult, models.PlannedWagon):
            with self.assertRaises(ValueError):
                if kind is models.ClaimResult:
                    kind(False, "wagon2", "banana", "somewhere")
                else:
                    kind(blocked_by="banana", note="somewhere")

    def test_the_note_must_be_a_string(self):
        with self.assertRaises(ValueError):
            models.ClaimResult(False, "wagon2", "lifecycle", 3)


class TestAForeignAuthorityCannotSpendThisWorld(unittest.TestCase):
    """Night's refusal comes AFTER departure. Routes and pickups roll
    during service, so a foreign authority with matching wagon keys
    would record the claim in another world while this one lost its
    stock — and night's later complaint could not undo it."""

    def _world(self):
        state = new_state()
        market.roll_prices(state, random.Random(3))
        driver = next(e for e in state.employees if e.driving >= 4)
        driver.hired = driver.aware = True
        home = state.shop_by_key(HOME_SHOP_KEY)
        home.stash, home.ingredients, home.delivery_pool = (
            {"mushrooms": 4}, 40, 10)
        return state, home, driver

    def test_a_route_refuses_a_foreign_authority_untouched(self):
        state, home, driver = self._world()
        foreign = phases.WagonNight(new_state())     # same keys
        plan = {"district": "old_harbor", "driver": driver,
                "ride_along": False, "cargo": {"mushrooms": 2},
                "legit": 3, "origin_shop": HOME_SHOP_KEY,
                "wagon_key": models.HOME_WAGON_KEY}
        with self.assertRaises(ValueError) as caught:
            phases._commit_route(state, plan, Listening(), foreign)
        self.assertIn("different state", str(caught.exception))
        self.assertEqual(home.stash["mushrooms"], 4)
        self.assertEqual(home.ingredients, 40)
        self.assertEqual(foreign.claims, {})

    def test_a_pickup_refuses_a_foreign_authority_untouched(self):
        state, _rosa = war_mechanics.TestSalvage._captured(
            war_mechanics.TestSalvage())
        camp = war.campaign_for(state, "vinnie")
        foreign = phases.WagonNight(new_state())
        rosa = next(e for e in state.employees
                    if e.name.startswith("Rosa"))
        with self.assertRaises(ValueError):
            war.run_salvage(
                state, {"rival": "vinnie", "driver": rosa,
                        "origin_shop": HOME_SHOP_KEY,
                        "wagon_key": models.HOME_WAGON_KEY},
                Listening(), random.Random(3), wagons=foreign)
        self.assertTrue(camp.salvage_available)   # still waiting
        self.assertEqual(foreign.claims, {})

    def test_the_check_and_the_claim_are_one_call(self):
        state, _home, driver = self._world()
        wagons = phases.WagonNight(state)
        plan = {"origin_shop": HOME_SHOP_KEY,
                "wagon_key": models.HOME_WAGON_KEY, "driver": driver}
        self.assertTrue(
            wagons.claim_plan(state, plan, "route").claimed)
        self.assertEqual(wagons.claims,
                         {models.HOME_WAGON_KEY: "route"})

    def test_the_pairing_is_checked_inside_the_same_call(self):
        state = _with_site(day=7, acceptance=5)
        wagons = phases.WagonNight(state)
        with self.assertRaises(ValueError):     # wagon housed away
            wagons.claim_plan(state, {"origin_shop": HOME_SHOP_KEY,
                                      "wagon_key": "wagon2"}, "route")
        self.assertEqual(wagons.claims, {})


class TestNightRefusesAForeignAuthority(unittest.TestCase):
    def test_a_non_authority_is_refused(self):
        state = new_state()
        for bogus in ({}, "wagons", 3, object()):
            with self.assertRaises(ValueError, msg=repr(bogus)):
                phases.night(state, {"routes": {}}, {"wagons": bogus}, Listening(),
                             Streams(3))

    def test_an_authority_from_another_world_is_refused(self):
        # A quiet night would never notice: no claims, no complaint,
        # and every question answered about the wrong world.
        state, other = new_state(), new_state()
        with self.assertRaises(ValueError) as caught:
            phases.night(state, {"routes": {}}, {"wagons": phases.WagonNight(other)},
                         Listening(), Streams(3))
        self.assertIn("different state", str(caught.exception))


class TestARaidPairsItsWagonWithItsReturnAddress(unittest.TestCase):
    """The last direct `claim_key` caller. A raid's wagon belongs to
    the address its haul comes back to; `exactly_one_shop` hid that
    pairing, and two addresses expose it. Same authority, told which
    field names the address — never a raid-shaped copy of it."""

    def _raid_night(self, state, **over):
        plan = {"rival": "sal", "objective": "steal_stock",
                "team": [e for e in state.employees if e.available][:1],
                "armed": False, "table_warned": True,
                "return_shop": HOME_SHOP_KEY,
                "wagon_key": models.HOME_WAGON_KEY}
        plan.update(over)
        for e in plan["team"]:
            e.hired = e.aware = True
        return plan

    def test_a_wagon_from_another_address_refuses_before_the_raid(self):
        state = _with_site(day=7, acceptance=5)
        plan = self._raid_night(state, wagon_key="wagon2")
        wagons = phases.WagonNight(state)
        with self.assertRaises(ValueError) as caught:
            wagons.claim_plan(state, plan, "raid",
                              field="return_shop")
        self.assertIn("kept at", str(caught.exception))
        self.assertEqual(wagons.claims, {})

    def test_an_unknown_return_address_refuses(self):
        state = _with_site(day=7, acceptance=5)
        plan = self._raid_night(state, return_shop="ghost")
        wagons = phases.WagonNight(state)
        with self.assertRaises(KeyError):
            wagons.claim_plan(state, plan, "raid",
                              field="return_shop")
        self.assertEqual(wagons.claims, {})

    def test_a_second_address_raid_claims_its_own_wagon(self):
        state = _with_site(day=7, acceptance=5)
        plan = self._raid_night(state, return_shop="shop2",
                                wagon_key="wagon2")
        wagons = phases.WagonNight(state)
        spent = wagons.claim_plan(state, plan, "raid",
                                  field="return_shop")
        self.assertTrue(spent.claimed)
        self.assertEqual(spent.wagon_key, "wagon2")
        self.assertEqual(wagons.claims, {"wagon2": "raid"})
        # The home wagon is untouched — a raid out of shop 2 does not
        # ground DiNapoli's.
        self.assertTrue(wagons.available_at(HOME_SHOP_KEY))

    def test_the_haul_comes_back_to_the_named_address(self):
        state = _with_site(day=7, acceptance=5)
        site = state.shop_by_key("shop2")
        home = state.shop_by_key(HOME_SHOP_KEY)
        home_before = dict(home.stash)          # the founding stash
        kept, _left = models.place_haul(state, {"oregano": 3}, "shop2")
        self.assertEqual(kept, {"oregano": 3})
        self.assertEqual(site.stash["oregano"], 3)
        self.assertEqual(home.stash, home_before,
                         "the haul must not reach the other address")

    def test_a_walking_raid_claims_nothing_at_all(self):
        # Ledger and sabotage jobs record None and take no wagon
        # (rev. 26) — through the real night, not by inspection.
        state = new_state()
        for e in state.employees[:2]:
            e.hired = e.aware = True
        for objective in ("ledger", "sabotage"):
            plan = _raid_plan(state, objective)
            self.assertIsNone(plan["wagon_key"], objective)


class TestTwoRoutesCanRunTheSameNight(unittest.TestCase):
    """Condition 1: the schema REPRESENTS two simultaneous addressed
    routes. Canon has both wagons running real routes, one per
    address per night (rev. 22 items 1 and 4) — a single
    `plans["route"]` slot could not express it, and the earlier test
    that claimed to cover this was vacuous."""

    def _plan(self, driver, shop_key, wagon_key):
        return {"district": "old_harbor", "driver": driver,
                "ride_along": False, "cargo": {}, "legit": 0,
                "origin_shop": shop_key, "wagon_key": wagon_key}

    def _two(self):
        state = _with_site(day=7, acceptance=5)
        drivers = [e for e in state.employees if e.driving >= 4][:2]
        for e in drivers:
            e.hired = e.aware = True
        plans = {"routes": {
            HOME_SHOP_KEY: self._plan(drivers[0], HOME_SHOP_KEY,
                                      models.HOME_WAGON_KEY),
            "shop2": self._plan(drivers[1], "shop2", "wagon2")}}
        return state, plans, drivers

    def test_both_addresses_hold_a_route_at_once(self):
        state, plans, _drivers = self._two()
        self.assertEqual(list(phases.routes_planned(state, plans)),
                         [HOME_SHOP_KEY, "shop2"])

    def test_each_route_reserves_only_its_own_wagon(self):
        state, plans, _drivers = self._two()
        for shop_key in (HOME_SHOP_KEY, "shop2"):
            view = phases.planned_wagon(state, plans, shop_key)
            self.assertFalse(view.available, shop_key)
            self.assertEqual(view.blocked_by, "route")

    def test_replanning_one_address_frees_only_its_driver(self):
        state, plans, drivers = self._two()
        reserved = phases.night_reserved(state, plans, but="route",
                                         but_shop=HOME_SHOP_KEY)
        self.assertNotIn(drivers[0], reserved)   # replanning this one
        self.assertIn(drivers[1], reserved)      # shop 2 still holds

    def test_both_routes_depart_and_spend_their_own_wagon(self):
        state, plans, _drivers = self._two()
        wagons = phases.WagonNight(state)
        for shop_key, plan in phases.routes_planned(state, plans).items():
            self.assertTrue(
                wagons.claim_plan(state, plan, "route").claimed, shop_key)
        self.assertEqual(wagons.claims,
                         {models.HOME_WAGON_KEY: "route",
                          "wagon2": "route"})

    def test_the_filing_key_and_the_plan_must_agree(self):
        # The one new way a mapping can disagree with itself: a route
        # filed under shop 1 that says it leaves shop 2 would load one
        # address's stock and reserve the other's wagon.
        state, plans, drivers = self._two()
        plans["routes"][HOME_SHOP_KEY] = self._plan(
            drivers[0], "shop2", "wagon2")
        with self.assertRaises(ValueError) as caught:
            phases.routes_planned(state, plans)
        self.assertIn("one address, or neither", str(caught.exception))

    def test_the_order_is_by_key_never_by_insertion(self):
        state, plans, drivers = self._two()
        rebuilt = {"routes": {
            "shop2": plans["routes"]["shop2"],
            HOME_SHOP_KEY: plans["routes"][HOME_SHOP_KEY]}}
        self.assertEqual(list(phases.routes_planned(state, rebuilt)),
                         [HOME_SHOP_KEY, "shop2"])


class TestTheScheduleIsStrictAndPreflighted(unittest.TestCase):
    """The schedule is validated AS A SET before the first crate
    moves. Committing routes one at a time validates each in
    isolation, and isolation is where shared resources hide."""

    def _two(self):
        state = _with_site(day=7, acceptance=5)
        drivers = [e for e in state.employees if e.driving >= 4][:2]
        for e in drivers:
            e.hired = e.aware = True
        return state, drivers

    def test_a_malformed_schedule_is_never_an_empty_one(self):
        state = new_state()
        for bogus in ({}, {"routes": None}, {"routes": False},
                      {"routes": ""}, {"routes": []},
                      {"routes": 3}):
            with self.assertRaises(ValueError, msg=repr(bogus)):
                phases.routes_planned(state, bogus)

    def test_a_hole_in_the_schedule_is_refused_not_skipped(self):
        state = new_state()
        for hole in (None, {}, False, "route"):
            with self.assertRaises(ValueError, msg=repr(hole)):
                phases.routes_planned(
                    state, {"routes": {HOME_SHOP_KEY: hole}})

    def test_a_plan_missing_a_canonical_field_is_refused(self):
        state, drivers = self._two()
        for field in routes.ROUTE_FIELDS:
            plan = _route_plan(state, HOME_SHOP_KEY, models.HOME_WAGON_KEY,
                          driver=drivers[0])
            del plan[field]
            with self.assertRaises(ValueError, msg=field):
                phases.route_schedule(
                    state, {"routes": {HOME_SHOP_KEY: plan}})

    def test_a_route_filed_under_a_ghost_address_is_refused(self):
        state, drivers = self._two()
        plan = _route_plan(state, "ghost", models.HOME_WAGON_KEY,
                      driver=drivers[0])
        with self.assertRaises(KeyError):
            phases.routes_planned(state, {"routes": {"ghost": plan}})

    def test_one_driver_cannot_drive_two_routes(self):
        state, drivers = self._two()
        plans = {"routes": {
            HOME_SHOP_KEY: _route_plan(state, HOME_SHOP_KEY,
                                  models.HOME_WAGON_KEY,
                                  driver=drivers[0]),
            "shop2": _route_plan(state, "shop2", "wagon2",
                            driver=drivers[0])}}
        with self.assertRaises(ValueError) as caught:
            phases.route_schedule(state, plans)
        self.assertIn("one person, one job", str(caught.exception))

    def test_the_owner_cannot_ride_two_wagons(self):
        state, drivers = self._two()
        plans = {"routes": {
            HOME_SHOP_KEY: _route_plan(state, HOME_SHOP_KEY,
                                  models.HOME_WAGON_KEY,
                                  driver=drivers[0], ride_along=True),
            "shop2": _route_plan(state, "shop2", "wagon2",
                            driver=drivers[1], ride_along=True)}}
        with self.assertRaises(ValueError) as caught:
            phases.route_schedule(state, plans)
        self.assertIn("at once", str(caught.exception))

    def test_a_legal_pair_passes_the_preflight(self):
        state, drivers = self._two()
        plans = {"routes": {
            HOME_SHOP_KEY: _route_plan(state, HOME_SHOP_KEY,
                                  models.HOME_WAGON_KEY,
                                  driver=drivers[0], ride_along=True),
            "shop2": _route_plan(state, "shop2", "wagon2",
                            driver=drivers[1])}}
        self.assertEqual([k for k, _p in phases.route_schedule(state, plans)],
                         [HOME_SHOP_KEY, "shop2"])

    def test_the_first_route_spends_nothing_when_the_second_is_bad(self):
        # THE reason the preflight exists: committing in order would
        # let route one load its stock before route two raised.
        state, drivers = self._two()
        home = state.shop_by_key(HOME_SHOP_KEY)
        home.stash = {"mushrooms": 4}
        home.ingredients, home.delivery_pool = 40, 10
        site = state.shop_by_key("shop2")
        site.stash, site.ingredients, site.delivery_pool = (
            {"mushrooms": 4}, 40, 10)
        plans = {"routes": {
            HOME_SHOP_KEY: _route_plan(state, HOME_SHOP_KEY,
                                  models.HOME_WAGON_KEY,
                                  driver=drivers[0],
                                  cargo={"mushrooms": 2}, legit=3),
            # shop 2's route names shop 1's wagon: malformed.
            "shop2": _route_plan(state, "shop2", models.HOME_WAGON_KEY,
                            driver=drivers[1])}}
        with self.assertRaises(ValueError):
            phases.route_schedule(state, plans)
        self.assertEqual(home.stash["mushrooms"], 4)
        self.assertEqual(home.ingredients, 40)


class TestOneRouteIsARouteAtAll(unittest.TestCase):
    """The per-route contract, beside the plan it describes. Falsy
    is not malformed: an EMPTY-MANIFEST route with the owner at home
    is `cargo={}`, `legit=0`, `ride_along=False`, and every one of
    those is legal. (A pizzas-only run is `cargo={}` with `legit`
    above zero — a different route, named differently.) Falsy of the
    WRONG SHAPE is not legal."""

    def _plan(self, **over):
        state = new_state()
        driver = next(e for e in state.employees if e.driving >= 4)
        driver.hired = driver.aware = True
        plan = _route_plan(state, HOME_SHOP_KEY, models.HOME_WAGON_KEY,
                      driver=driver)
        plan.update(over)
        return state, plan

    def test_the_empty_manifest_route_passes(self):
        state, plan = self._plan(cargo={}, legit=0, ride_along=False)
        routes.validate_route_plan(state, plan)      # a quiet night

    def test_the_pizzas_only_route_passes_too(self):
        # Distinct from the empty manifest: real cover, no product.
        state, plan = self._plan(cargo={}, legit=4, ride_along=False)
        routes.validate_route_plan(state, plan)

    def test_malformed_cargo_is_not_an_empty_load(self):
        # `plan.get("cargo") or {}` turned each of these into a
        # legal empty-manifest route.
        for bad in (False, "", [], None, 0, ["mushrooms"]):
            state, plan = self._plan(cargo=bad)
            with self.assertRaises(ValueError, msg=repr(bad)):
                routes.validate_route_plan(state, plan)

    def test_ride_along_is_exactly_a_bool(self):
        # It was EXEMPTED from the presence check, so a missing one
        # surfaced later as a KeyError from whichever line read it.
        for bad in (None, 1, 0, "yes", ""):
            state, plan = self._plan(ride_along=bad)
            with self.assertRaises(ValueError, msg=repr(bad)):
                routes.validate_route_plan(state, plan)
        state, plan = self._plan()
        del plan["ride_along"]
        with self.assertRaises(ValueError):
            routes.validate_route_plan(state, plan)

    def test_the_cover_count_is_an_exact_whole_number(self):
        for bad in (None, -1, 1.5, "3", True):
            state, plan = self._plan(legit=bad)
            with self.assertRaises(ValueError, msg=repr(bad)):
                routes.validate_route_plan(state, plan)

    def test_a_foreign_driver_is_refused(self):
        class Nobody:
            name, key = "Nobody", "e0"
            available = aware = hired = True
            driving = 9
        state, plan = self._plan(driver=Nobody())
        with self.assertRaises(ValueError):
            routes.validate_route_plan(state, plan)

    def test_a_clone_carrying_a_real_key_is_not_that_person(self):
        # THE case identity exists for: a dataclass copy compares
        # EQUAL to the original, so a look-alike would ride as a
        # second copy of someone standing somewhere else — arrested,
        # injured, or driving another wagon.
        import copy
        state, plan = self._plan()
        twin = copy.deepcopy(plan["driver"])
        self.assertEqual(twin, plan["driver"])       # equal...
        self.assertIsNot(twin, plan["driver"])       # ...not the same
        plan["driver"] = twin
        with self.assertRaises(ValueError):
            routes.validate_route_plan(state, plan)

    def test_a_bad_district_or_pairing_is_refused(self):
        state, plan = self._plan(district="atlantis")
        with self.assertRaises(ValueError):
            routes.validate_route_plan(state, plan)
        state, plan = self._plan(wagon_key="ghost")
        with self.assertRaises(KeyError):
            routes.validate_route_plan(state, plan)


class TestEveryDoorConsumesTheOneContract(unittest.TestCase):
    """A contract only one caller applies is a contract with a side
    entrance. `routes_planned` is the single door routes come out of
    storage through, so validation lives THERE — and every reader
    downstream is reading checked plans by construction."""

    def _stored(self, **broken):
        state = new_state()
        driver = next(e for e in state.employees if e.driving >= 4)
        driver.hired = driver.aware = True
        plan = _route_plan(state, HOME_SHOP_KEY, models.HOME_WAGON_KEY,
                      driver=driver)
        for field in broken.pop("drop", ()):
            del plan[field]
        plan.update(broken)
        return state, {"routes": {HOME_SHOP_KEY: plan}}

    def test_night_reserved_refuses_a_malformed_stored_route(self):
        # It used to hand back the driver of a route that could never
        # run, reserving a person for a job with no wagon named.
        state, plans = self._stored(drop=("ride_along",))
        with self.assertRaises(ValueError):
            phases.night_reserved(state, plans)

    def test_the_availability_view_refuses_one_too(self):
        state, plans = self._stored(drop=("wagon_key",))
        with self.assertRaises(ValueError):
            phases.planned_wagon(state, plans, HOME_SHOP_KEY)

    def test_the_reservation_count_refuses_one_too(self):
        state, plans = self._stored(cargo=False)
        with self.assertRaises(ValueError):
            phases.planned_jobs_at(state, plans, HOME_SHOP_KEY)

    def test_the_schedule_refuses_one_too(self):
        state, plans = self._stored(legit=None)
        with self.assertRaises(ValueError):
            phases.route_schedule(state, plans)

    def test_service_refuses_before_it_commits_anything(self):
        # Commit and resolution cannot bypass the canonical contract:
        # the stored route is malformed, so nothing is spent.
        state, plans = self._stored(drop=("ride_along",))
        home = state.shop_by_key(HOME_SHOP_KEY)
        home.stash = {"mushrooms": 4}
        before = (dict(home.stash), home.ingredients)
        with self.assertRaises(ValueError):
            phases.service(state, plans, Listening([0]), Streams(3))
        self.assertEqual((home.stash, home.ingredients), before)


class TestExecutionIsNotADoorOfItsOwn(unittest.TestCase):
    """`routes_planned` is the only door OUT of storage — but it was
    not the only door INTO execution. A plan handed straight to
    commit or resolution was taken on trust, and a wagonless route
    could become real history."""

    def _world(self):
        state = new_state()
        market.roll_prices(state, random.Random(3))
        driver = next(e for e in state.employees if e.driving >= 4)
        driver.hired = driver.aware = True
        home = state.shop_by_key(HOME_SHOP_KEY)
        home.stash, home.ingredients, home.delivery_pool = (
            {"mushrooms": 4}, 40, 10)
        return state, home, driver

    def _plan(self, state, driver, **over):
        plan = _route_plan(state, HOME_SHOP_KEY, models.HOME_WAGON_KEY,
                      driver=driver, cargo={"mushrooms": 2}, legit=3)
        for field in over.pop("drop", ()):
            del plan[field]
        plan.update(over)
        return plan

    def test_commit_refuses_a_plan_missing_ride_along(self):
        # Reproduced before the fix: it committed, claimed the wagon
        # and took two mushrooms out of the stash.
        state, home, driver = self._world()
        plan = self._plan(state, driver, drop=("ride_along",))
        wagons = phases.WagonNight(state)
        with self.assertRaises(ValueError):
            phases._commit_route(state, plan, Listening(), wagons)
        self.assertEqual(home.stash, {"mushrooms": 4})
        self.assertEqual(home.ingredients, 40)
        self.assertEqual(wagons.claims, {})
        self.assertTrue(wagons.available_at(HOME_SHOP_KEY))

    def test_resolution_refuses_a_plan_missing_its_wagon(self):
        # Reproduced before the fix: the route completed and appended
        # a RouteExecutionRecord — a wagonless ghost route becoming
        # real history.
        state, _home, driver = self._world()
        plan = self._plan(state, driver, drop=("wagon_key",))
        with self.assertRaises(ValueError):
            routes.resolve_route(state, plan, Listening(),
                                 random.Random(3))
        self.assertEqual(state.route_log, [])
        self.assertEqual(driver.familiarity, {})

    def test_a_valid_plan_still_runs_through_both(self):
        # The contract refuses malformed plans, not ordinary ones.
        state, home, driver = self._world()
        plan = self._plan(state, driver)
        wagons = phases.WagonNight(state)
        self.assertTrue(
            phases._commit_route(state, plan, Listening(), wagons))
        self.assertEqual(wagons.claims,
                         {models.HOME_WAGON_KEY: "route"})
        self.assertEqual(home.stash["mushrooms"], 2)
        routes.resolve_route(state, plan, Listening(),
                             random.Random(3))
        self.assertEqual(len(state.route_log), 1)


class TestTheManifestReaderIsStrict(unittest.TestCase):
    def test_absence_is_not_the_legal_zero(self):
        for missing in ({}, {"cargo": {}}, {"legit": 0}):
            with self.assertRaises(ValueError, msg=repr(missing)):
                routes.RouteManifest.of_plan(missing)

    def test_a_cover_of_nothing_at_all_is_refused(self):
        with self.assertRaises(ValueError):
            routes.RouteManifest.of_plan({"cargo": {}, "legit": None})

    def test_the_legal_zero_still_reads(self):
        m = routes.RouteManifest.of_plan({"cargo": {}, "legit": 0})
        self.assertEqual((m.cargo, m.legit), ({}, 0))

    def test_a_typed_plan_without_a_manifest_is_refused(self):
        # A deliberate refusal, not an AttributeError from the next
        # line that happens to touch it.
        state = new_state()
        driver = next(e for e in state.employees if e.driving >= 4)
        for bogus in (None, {}, "manifest"):
            plan = routes.RoutePlan(
                district="old_harbor", driver=driver, ride_along=False,
                manifest=bogus, origin_shop=HOME_SHOP_KEY,
                wagon_key=models.HOME_WAGON_KEY)
            with self.assertRaises(ValueError, msg=repr(bogus)):
                routes.RouteManifest.of_plan(plan)


class TestAWalkingRaidClaimsNothingAtNight(unittest.TestCase):
    """Driven through the real night, not by inspecting the plan:
    ledger and sabotage jobs must leave the shared authority empty."""

    def _night(self, objective):
        state = new_state()
        crew = [e for e in state.employees if e.available][:1]
        for e in crew:
            e.hired = e.aware = True
        plans = {"routes": {},
                 "raid": {"rival": "sal", "objective": objective,
                          "team": crew, "armed": False,
                          "table_warned": True,
                          "wagon_key": None,
                          "return_shop": HOME_SHOP_KEY}}
        wagons = phases.WagonNight(state)
        phases.night(state, plans, {"wagons": wagons}, Listening([0]),
                     Streams(11))
        return plans, wagons

    def test_a_ledger_job_records_no_claim(self):
        plans, wagons = self._night("ledger")
        self.assertEqual(wagons.claims, {})
        self.assertIs(plans["raid"]["wagon_free"], False)

    def test_a_sabotage_job_records_no_claim(self):
        plans, wagons = self._night("sabotage")
        self.assertEqual(wagons.claims, {})
        self.assertIs(plans["raid"]["wagon_free"], False)

    def test_the_wagon_is_still_there_afterwards(self):
        _plans, wagons = self._night("sabotage")
        self.assertTrue(wagons.available_at(HOME_SHOP_KEY))


class TestTheAddressPickerIsSilentAtOne(unittest.TestCase):
    """Condition 5's first term: the released game gains no prompt."""

    def test_one_open_address_is_returned_without_asking(self):
        state = new_state()
        con = Listening()
        self.assertIs(phases.choose_address(state, con, "Whose board?", "demand"),
                      state.shop_by_key(HOME_SHOP_KEY))
        self.assertEqual(con.menus, [])           # nothing was asked

    def test_a_building_site_is_never_offered(self):
        # It cannot do any of the things the picker leads to.
        state = _with_site(day=6, acceptance=5)
        con = Listening()
        self.assertIs(phases.choose_address(state, con, "Whose board?", "demand"),
                      state.shop_by_key(HOME_SHOP_KEY))
        self.assertEqual(con.menus, [])

    def test_two_open_addresses_are_offered_by_district(self):
        state = _with_site(day=7, acceptance=5)
        con = Listening([1])
        picked = phases.choose_address(state, con, "Whose kitchen?", "service")
        self.assertEqual(picked.key, "shop2")
        shown = con.offered("Whose kitchen?")
        self.assertEqual(shown, ["Old Harbor", "University Hill", "Back"])
        # A raw key is an internal identity and never reaches prose.
        self.assertNotIn("shop1", " ".join(shown))
        self.assertNotIn("shop2", " ".join(shown))

    def test_the_order_is_stable_identity_order(self):
        state = _with_site(day=7, acceptance=5)
        state.shops.reverse()
        con = Listening([0])
        self.assertEqual(
            phases.choose_address(state, con, "Whose kitchen?", "service").key,
            HOME_SHOP_KEY)


class TestTheLifecycleActuallyBinds(unittest.TestCase):
    """The capability view is what makes the lifecycle real: `open`
    and `allowed` are different questions, and every consumer asks
    the one authority rather than re-deriving it."""

    def _building(self):
        return _with_site(day=6, acceptance=5)

    def test_a_building_site_rolls_no_order_book(self):
        state = self._building()
        site = state.shop_by_key("shop2")
        shop.roll_demand(state, Streams(3).daily(6, "demand"))
        self.assertEqual((site.demand_today, site.delivery_pool), (0, 0))
        self.assertGreater(
            state.shop_by_key(HOME_SHOP_KEY).demand_today, 0)

    def test_the_roll_leaves_a_building_site_with_nothing_at_all(self):
        # Skipping the address was not the same as clearing it
        # (P4b.1a review, blocking item 2). Whatever a site was
        # carrying survived the morning, the shift AND a save/load
        # round trip, so the record could claim 49 customers, 17
        # deliveries and a day's takings at an address canon says
        # serves nothing and earns nothing. The daily authority owns
        # the complete postcondition now.
        state = self._building()
        site = state.shop_by_key("shop2")
        site.demand_today, site.delivery_pool = 49, 17
        site.legit_revenue_today = 123
        shop.roll_demand(state, Streams(3).daily(6, "demand"))
        self.assertEqual((site.demand_today, site.delivery_pool,
                          site.legit_revenue_today), (0, 0, 0))
        self.assertGreater(
            state.shop_by_key(HOME_SHOP_KEY).demand_today, 0)

    def test_the_postcondition_survives_the_real_morning(self):
        # Through the REAL morning, not the roll alone: the injected
        # numbers are gone by the time the player sees a menu, and the
        # payload they leave behind is one a reload accepts.
        state = self._building()
        site = state.shop_by_key("shop2")
        site.demand_today, site.delivery_pool = 49, 17
        site.legit_revenue_today = 123
        market.roll_prices(state, random.Random(3))
        phases.morning(state, Listening([8]), Streams(3))
        self.assertEqual((site.demand_today, site.delivery_pool,
                          site.legit_revenue_today), (0, 0, 0))
        save.state_from_dict(save.state_to_dict(state))

    def test_a_building_site_pays_no_rent(self):
        state = self._building()
        self.assertEqual(
            len(models.addresses_allowing(state, "rent")), 1)

    def test_a_building_site_launders_nothing(self):
        state = self._building()
        self.assertEqual(
            len(models.addresses_allowing(state, "laundering")), 1)

    def test_a_building_site_is_not_watched_by_the_law(self):
        state = self._building()
        self.assertEqual(
            [a.key for a in models.addresses_allowing(
                state, "law_targeting")], [HOME_SHOP_KEY])

    def test_a_building_site_may_still_take_a_pantry_delivery(self):
        # Canon ALLOWS pantry supply during construction, so the
        # picker must offer it — excluding it was the lifecycle being
        # decorative in the other direction.
        state = self._building()
        self.assertEqual(
            [a.key for a in models.addresses_allowing(
                state, "pantry_supply")], [HOME_SHOP_KEY, "shop2"])

    def test_the_view_is_stable_under_reordering(self):
        state = self._building()
        state.shops.reverse()
        self.assertEqual(
            [a.key for a in models.addresses_allowing(
                state, "pantry_supply")], [HOME_SHOP_KEY, "shop2"])


class TestThePickerFailsClosed(unittest.TestCase):
    def test_an_exhausted_script_takes_back_not_a_shop(self):
        # The last option is what an exhausted script picks, and it
        # used to be an ADDRESS — so a script that ran out silently
        # chose shop 2.
        state = _with_site(day=7, acceptance=5)
        before = [(a.key, a.quality, a.price) for a in state.shops]
        con = Listening([])                      # exhausted
        self.assertIsNone(phases.choose_address(
            state, con, "Whose kitchen?", "service"))
        self.assertEqual(
            [(a.key, a.quality, a.price) for a in state.shops], before)

    def test_back_is_the_last_option_offered(self):
        state = _with_site(day=7, acceptance=5)
        con = Listening([2])
        self.assertIsNone(phases.choose_address(
            state, con, "Whose kitchen?", "service"))
        self.assertEqual(con.offered("Whose kitchen?")[-1], "Back")

    def test_an_exhausted_morning_kitchen_changes_nothing(self):
        # Through the REAL morning menu: option 1 is the kitchen.
        state = _with_site(day=7, acceptance=5)
        before = [(a.key, a.quality, a.price) for a in state.shops]
        phases.morning(state, Listening([1]), Streams(3))
        self.assertEqual(
            [(a.key, a.quality, a.price) for a in state.shops], before)


class TestTheSupplierNeverStocksABuildingSite(unittest.TestCase):
    """P4b.1a review, blocking item 1. The supplier's crates are
    CONTRABAND and land in the stash, so the capability is
    `contraband_storage`. The morning asked `pantry_supply` — the
    flour-and-cans permission a site legitimately has — which offered
    the building site and then made it the criminal stockroom §2.4.2
    says it is not.

    The seeds are chosen so an offer actually exists on the day: seed
    3 has a supplier on day 6, seed 5 on day 7. A test that silently
    ran a morning with no van would pass without testing anything.
    """

    def _morning(self, day, seed, script):
        """One REAL morning, with the van's offer resolved the way the
        morning itself resolves it and the founding room's opening
        stock recorded, so a purchase can be counted as a delta."""
        state = _with_site(day=day, acceptance=5)
        market.roll_prices(state, random.Random(3))
        offer = phases._supplier_offer(
            state, Streams(seed).daily(day, "supplier"))
        self.assertIsNotNone(offer, "no van on this seed/day")
        before = dict(state.shop_by_key(HOME_SHOP_KEY).stash)
        con = Listening(script)
        phases.morning(state, con, Streams(seed))
        return state, con, offer, before

    def test_the_site_is_never_offered_the_van(self):
        # The reviewer's exact repro, inverted: with the site under
        # construction exactly one address may hold contraband, so the
        # picker is SILENT and the crates can only go home.
        state, con, offer, before = self._morning(6, 3, [3, 5])
        site = state.shop_by_key("shop2")
        home = state.shop_by_key(HOME_SHOP_KEY)
        self.assertEqual(con.offered("Deliver where?"), [])
        self.assertEqual(site.stash, {})
        # The five units were actually bought, and bought AT HOME —
        # counted as a delta against the founding room's opening
        # stock, so the pin cannot pass on a morning that bought
        # nothing.
        self.assertEqual(home.stash[offer["good"]]
                         - before.get(offer["good"], 0), 5)

    def test_both_open_addresses_are_offered_it(self):
        # The other direction, so the fix is a capability correction
        # and not a disabled menu: once the site OPENS it is a back
        # room like any other and the player chooses.
        state, con, offer, _before = self._morning(7, 5, [3, 1, 4])
        self.assertEqual(con.offered("Deliver where?"),
                         ["Old Harbor", "University Hill", "Back"])
        self.assertEqual(
            state.shop_by_key("shop2").stash.get(offer["good"]), 4)

    def test_the_purchase_refuses_a_site_with_nothing_touched(self):
        # The MUTATION BOUNDARY, called directly: a menu is one door,
        # and an authority only the menu consults is a suggestion.
        # Nothing moves — not the cash, not the crates, not the van's
        # remaining stock.
        state = _with_site(day=6, acceptance=5)
        site = state.shop_by_key("shop2")
        state.clean, state.dirty = 500, 500
        offer = {"good": "mushrooms", "units": 10, "price": 10}
        with self.assertRaises(ValueError) as caught:
            phases._buy_supplier(state, site, offer, Listening([10]))
        self.assertIn("contraband", str(caught.exception))
        self.assertEqual((state.clean, state.dirty), (500, 500))
        self.assertEqual(site.stash, {})
        self.assertEqual(offer["units"], 10)

    def test_a_detached_copy_is_refused_with_nothing_touched(self):
        # The mixed-identity seam (P4b.1a review, second pass): the
        # boundary read the lifecycle off the object handed in,
        # priced the space against the canonical address BY KEY,
        # spent real cash, and put the crates back into the object
        # handed in. A faithful clone of an OPEN address is refused
        # too — the copy is not the address, however truthful it is.
        state = _with_site(day=7, acceptance=5)
        real = state.shop_by_key("shop2")
        clone = Shop(key="shop2", district="university",
                     acceptance_day=5, opening_day=7)
        state.clean, state.dirty = 500, 500
        offer = {"good": "mushrooms", "units": 10, "price": 10}
        with self.assertRaises(ValueError) as caught:
            phases._buy_supplier(state, clone, offer, Listening([4]))
        self.assertIn("detached copy", str(caught.exception))
        self.assertEqual((state.clean, state.dirty), (500, 500))
        self.assertEqual((real.stash, clone.stash), ({}, {}))
        self.assertEqual(offer["units"], 10)

    def test_a_copy_claiming_to_be_open_cannot_answer_for_the_site(self):
        # The sharp case: the canonical address is under
        # CONSTRUCTION and the copy carries dates that say otherwise.
        # Identity is checked BEFORE the lifecycle, so the copy never
        # gets to answer the question at all.
        state = _with_site(day=6, acceptance=5)      # still building
        real = state.shop_by_key("shop2")
        self.assertFalse(shop_is_open(real, state.day))
        clone = Shop(key="shop2", district="university")   # "founding"
        self.assertTrue(shop_is_open(clone, state.day))
        state.clean, state.dirty = 500, 500
        offer = {"good": "mushrooms", "units": 10, "price": 10}
        with self.assertRaises(ValueError) as caught:
            phases._buy_supplier(state, clone, offer, Listening([4]))
        self.assertIn("detached copy", str(caught.exception))
        self.assertEqual((state.clean, state.dirty), (500, 500))
        self.assertEqual((real.stash, clone.stash), ({}, {}))
        self.assertEqual(offer["units"], 10)

    def test_the_purchase_still_serves_an_open_address(self):
        # The refusal is the lifecycle's, not a new rule about
        # suppliers: the same call at the same address succeeds the
        # morning it opens.
        state = _with_site(day=7, acceptance=5)
        site = state.shop_by_key("shop2")
        state.clean, state.dirty = 500, 500
        offer = {"good": "mushrooms", "units": 10, "price": 10}
        phases._buy_supplier(state, site, offer, Listening([4]))
        self.assertEqual(site.stash, {"mushrooms": 4})


class TestBothAddressesTradeAndRun(unittest.TestCase):
    """Conditions 5's operating terms, through the REAL service."""

    def _open_pair(self):
        state = _with_site(day=7, acceptance=5)
        market.roll_prices(state, random.Random(3))
        drivers = [e for e in state.employees if e.driving >= 4][:2]
        for e in drivers:
            e.hired = e.aware = True
        for a_shop, stock in ((state.shop_by_key(HOME_SHOP_KEY), 4),
                              (state.shop_by_key("shop2"), 4)):
            a_shop.stash = {"mushrooms": stock}
            a_shop.ingredients, a_shop.delivery_pool = 40, 10
            a_shop.demand_today = 20
        return state, drivers

    def _route_plan(self, state, driver, shop_key, wagon_key, **over):
        return _route_plan(state, shop_key, wagon_key, driver=driver,
                           cargo={"mushrooms": 2}, legit=3, **over)

    def test_service_trades_at_every_open_address(self):
        # It must not ask which restaurant opens.
        state, _drivers = self._open_pair()
        con = Listening()
        phases.service(state, {"routes": {}}, con, Streams(3))
        self.assertEqual(con.menus, [])       # no choice offered
        self.assertTrue(con.said("Old Harbor: Orders"), con.lines)
        self.assertTrue(con.said("University Hill: Orders"), con.lines)
        # Both kitchens actually BAKED and both tills actually rang —
        # two printed lines are not two trading restaurants.
        for a_shop in state.shops:
            self.assertLess(a_shop.ingredients, 40, a_shop.key)
            self.assertGreater(a_shop.legit_revenue_today, 0, a_shop.key)

    def test_each_address_gets_its_own_critic(self):
        # One `daily(day, "critic")` per address handed every shop the
        # SAME first roll: not a shared world fact, one coin reported
        # twice. The founding address keeps the legacy channel.
        state, _drivers = self._open_pair()
        self.assertEqual(
            models.address_channel(state, HOME_SHOP_KEY, "critic"),
            "critic")
        self.assertNotEqual(
            models.address_channel(state, "shop2", "critic"), "critic")
        s = Streams(3)
        self.assertNotEqual(
            s.daily(7, models.address_channel(state, HOME_SHOP_KEY,
                                              "critic")).random(),
            s.daily(7, models.address_channel(state, "shop2",
                                              "critic")).random())

    def test_reordering_the_shops_changes_no_address_result(self):
        state, _drivers = self._open_pair()
        state.shops.reverse()
        self.assertEqual(
            [a.key for a in models.addresses_allowing(state, "service")],
            [HOME_SHOP_KEY, "shop2"])
        self.assertEqual(
            models.address_channel(state, "shop2", "critic"),
            "critic@shop2")

    def test_a_construction_site_does_not_trade(self):
        state = _with_site(day=6, acceptance=5)    # still building
        market.roll_prices(state, random.Random(3))
        con = Listening()
        phases.service(state, {"routes": {}}, con, Streams(3))
        self.assertFalse(con.said("University Hill"), con.lines)

    def test_two_routes_commit_and_resolve_independently(self):
        state, drivers = self._open_pair()
        plans = {"routes": {
            HOME_SHOP_KEY: self._route_plan(state, drivers[0], HOME_SHOP_KEY,
                                       models.HOME_WAGON_KEY),
            "shop2": self._route_plan(state, drivers[1], "shop2", "wagon2")}}
        report = phases.service(state, plans, Listening(), Streams(3))
        # Both wagons rolled, each out of its own address.
        self.assertEqual(report["wagons"].claims,
                         {models.HOME_WAGON_KEY: "route",
                          "wagon2": "route"})
        # Each address ran ITS OWN route, once. The post-resolution
        # stash is deliberately NOT asserted here: what a route
        # leaves behind depends on the night it had (sold, seized,
        # jumped, returned), and pinning it would make this test
        # about route outcomes rather than about two addresses
        # operating independently.
        self.assertEqual(len(state.route_log), 2)
        self.assertEqual({r.origin_shop for r in state.route_log},
                         {HOME_SHOP_KEY, "shop2"})

    def test_a_malformed_second_route_leaves_the_first_untouched(self):
        # THE binding acceptance carried from the schedule work: the
        # preflight refuses the SET, so the valid first route never
        # loads, never bakes, and never takes its wagon.
        state, drivers = self._open_pair()
        home = state.shop_by_key(HOME_SHOP_KEY)
        before = (dict(home.stash), home.ingredients)
        plans = {"routes": {
            HOME_SHOP_KEY: self._route_plan(state, drivers[0], HOME_SHOP_KEY,
                                       models.HOME_WAGON_KEY),
            # shop 2's route names shop 1's wagon.
            "shop2": self._route_plan(state, drivers[1], "shop2",
                                 models.HOME_WAGON_KEY)}}
        with self.assertRaises(ValueError):
            phases.service(state, plans, Listening(), Streams(3))
        self.assertEqual((home.stash, home.ingredients), before)
        self.assertEqual(state.route_log, [])


def _shop_snapshot(a_shop) -> tuple:
    """Everything a morning surface could move at one address. A
    partial snapshot would let a surface mutate the field nobody
    thought to record, which is the failure mode this guards."""
    return (a_shop.quality, a_shop.price, a_shop.ingredients,
            a_shop.pantry_quality, dict(a_shop.stash),
            set(a_shop.upgrades), a_shop.demand_today,
            a_shop.delivery_pool, a_shop.legit_revenue_today,
            a_shop.reputation)


class TestEverySurfaceTakesTheWorldsAddress(unittest.TestCase):
    """P4b.1a review, third pass: the bounded surface completion.

    THE SIX generic address-specific phase surfaces — the complete
    set of player-facing boundaries that accept a `Shop` — each
    resolve their address through the state before reading from it or
    writing to it. Not a spending rule: a board can DISPLAY a
    detached room as if the player owned it, kitchen policy can take
    the player's decisions and leave the real kitchen unchanged, and
    storage reads what to move off the object handed in while moving
    it canonically by key.

    Domain internals are deliberately out of scope (`simulate_shift`,
    route commitment and resolution, the raid path): they derive
    their address from state or carry their own contracts, and a
    second check there would be a second authority.
    """

    SURFACES = ("_market_board", "_kitchen_policy", "_buy_ingredients",
                "_buy_supplier", "_improvements", "_storage")

    def _world(self):
        """An open second address with a warehouse to move goods to,
        stock worth moving, and money worth spending — so every
        surface below would really do something if it ran."""
        state = _with_site(day=7, acceptance=5)
        market.roll_prices(state, random.Random(3))
        state.warehouse = {}
        state.clean, state.dirty = 5000, 5000
        real = state.shop_by_key("shop2")
        real.stash = {"mushrooms": 3}
        real.ingredients = 10
        return state, real

    def _clone_of(self, real):
        """A faithful copy: same key, same district, same dates. It
        is refused for being a copy, not for being wrong."""
        return Shop(key=real.key, district=real.district,
                    ingredients=real.ingredients,
                    stash=dict(real.stash),
                    acceptance_day=real.acceptance_day,
                    opening_day=real.opening_day)

    def _call(self, name, state, a_shop):
        """Each surface driven with answers that WOULD move something
        — buy stock, take an upgrade, move goods, set both policies —
        so "nothing touched" means the guard stopped it rather than
        the script having asked for nothing."""
        return {
            "_market_board":
                lambda: phases._market_board(state, a_shop, Listening()),
            # The plan set is REQUIRED, so it is passed like every
            # production caller passes it.
            "_kitchen_policy":
                lambda: phases._kitchen_policy(state, a_shop,
                                               Listening([0, 2]),
                                               {"routes": {}}),
            "_buy_ingredients":
                lambda: phases._buy_ingredients(state, a_shop,
                                                Listening([12])),
            "_buy_supplier":
                lambda: phases._buy_supplier(
                    state, a_shop,
                    {"good": "mushrooms", "units": 10, "price": 10},
                    Listening([6])),
            "_improvements":
                lambda: phases._improvements(state, a_shop,
                                             Listening([0])),
            "_storage":
                lambda: phases._storage(state, a_shop, Listening([0, 3]),
                                        Streams(3)),
        }[name]()

    def test_the_roster_is_the_six_surfaces_and_they_all_exist(self):
        for name in self.SURFACES:
            self.assertTrue(callable(getattr(phases, name)), name)

    def test_kitchen_policy_requires_the_plan_set_it_reads(self):
        # The optional default was a lie the type told: `plans or {}`
        # handed the route contract an empty mapping, which it
        # refuses — a night with no routes says so with
        # `{"routes": {}}`. So the default could not work if taken,
        # while reading as a supported way to call this. Required
        # now, and a caller that forgets fails AT THE CALL.
        state, real = self._world()
        with self.assertRaises(TypeError):
            phases._kitchen_policy(          # type: ignore[call-arg]
                state, real, Listening([0, 2]))
        # And the empty-night plan set, spelled the one canonical way,
        # still passes.
        phases._kitchen_policy(state, real, Listening([0, 2]),
                               {"routes": {}})

    def test_every_surface_refuses_a_detached_copy_untouched(self):
        for name in self.SURFACES:
            with self.subTest(name):
                state, real = self._world()
                clone = self._clone_of(real)
                before = (_shop_snapshot(real), _shop_snapshot(clone),
                          state.clean, state.dirty,
                          dict(state.warehouse))
                with self.assertRaises(ValueError) as caught:
                    self._call(name, state, clone)
                self.assertIn("detached copy", str(caught.exception))
                self.assertEqual(
                    (_shop_snapshot(real), _shop_snapshot(clone),
                     state.clean, state.dirty, dict(state.warehouse)),
                    before)

    def test_every_surface_refuses_a_ghost_address(self):
        # A key naming no address is not a copy but the same class of
        # incoherence, and it fails closed through the same lookup.
        for name in self.SURFACES:
            with self.subTest(name):
                state, _real = self._world()
                ghost = Shop(key="nowhere", district="university")
                with self.assertRaises(KeyError):
                    self._call(name, state, ghost)

    def test_every_surface_takes_the_canonical_address(self):
        # The authority refuses COPIES, not addresses: the object the
        # picker actually hands over is the state's own, and it must
        # pass every one of the six.
        for name in self.SURFACES:
            with self.subTest(name):
                state, real = self._world()
                self.assertIs(models.canonical_shop(state, real), real)
                self._call(name, state, real)     # must not raise

    def test_the_authority_is_reached_before_anything_is_read(self):
        # Order matters: a copy must not get to answer the lifecycle,
        # price against the canonical room, or print a room's stock
        # before being refused. A copy whose fields would all produce
        # DIFFERENT answers is refused just the same.
        state, real = self._world()
        liar = Shop(key="shop2", district="meadows", ingredients=99,
                    stash={"truffle": 40}, quality="gourmet")
        for name in self.SURFACES:
            with self.subTest(name):
                with self.assertRaises(ValueError) as caught:
                    self._call(name, state, liar)
                # THE identity refusal specifically. A bare
                # `assertRaises(ValueError)` was satisfied on the
                # pre-guard engine by `_storage` refusing the liar's
                # 40 truffles on space grounds — the right exception
                # type for the wrong reason, which is a pin that
                # proves nothing.
                self.assertIn("detached copy", str(caught.exception))


def _renamed_founding(key: str) -> models.State:
    """A VALID one-address world whose founding shop is keyed
    something other than `shop1`. Nothing in the engine promises the
    founding key is spelled `shop1` — the save layer infers that
    spelling only for a keyless legacy payload, and a payload that
    carries a key keeps it — so this is a state the loader admits."""
    state = new_state()
    home = state.shops[0]
    for w in state.wagons:
        w.shop_key = key
    for e in state.employees:
        e.shop_key = key
    for rv in state.rivals.values():
        if rv.warning is not None:
            rv.warning.shop_key = key
    home.key = key
    validate_addresses(state)
    return state


class TestTheFoundingAddressIsResolvedNotSpelled(unittest.TestCase):
    """P4b.1a review, blocking items 3 and 4. Which address is the
    founding one is a LIFECYCLE fact — the undated record — and one
    resolver answers it. Comparing key spellings and reading list
    position were two different ways of answering it wrongly."""

    def test_the_undated_address_is_the_founding_one(self):
        state = _with_site(day=7, acceptance=5)
        self.assertIs(models.founding_shop(state),
                      state.shop_by_key(HOME_SHOP_KEY))

    def test_it_is_not_the_first_address_by_key_or_by_position(self):
        state = _with_site(day=7, acceptance=5)
        state.shops.append(Shop(
            key="aaa_shop", district="meadows",
            acceptance_day=5, opening_day=5 + CONSTRUCTION_DAYS))
        state.wagons.append(Wagon(key="wagon3", shop_key="aaa_shop"))
        validate_addresses(state)
        self.assertEqual(models.founding_shop(state).key, HOME_SHOP_KEY)
        state.shops.reverse()
        self.assertEqual(models.founding_shop(state).key, HOME_SHOP_KEY)

    def test_a_world_with_no_single_undated_address_fails_closed(self):
        # Two undated shops each claim to predate the world; none
        # leaves a world nobody founded. Both are incoherence, and
        # this resolver answers neither with a guess.
        two = _with_site(day=7, acceptance=5)
        two.shops.append(Shop(key="shop3", district="meadows"))
        none = _with_site(day=7, acceptance=5)
        home = none.shop_by_key(HOME_SHOP_KEY)
        home.acceptance_day = 1
        home.opening_day = 1 + CONSTRUCTION_DAYS
        for state in (two, none):
            with self.assertRaises(ValueError) as caught:
                models.founding_shop(state)
            self.assertIn("undated", str(caught.exception))

    def test_the_validator_and_the_resolver_are_one_authority(self):
        # The count is not spelled twice: the validator raises through
        # the resolver, so they cannot come to disagree about which
        # address is the founding one.
        state = new_state()
        state.day = 6
        state.shops.append(Shop(key="shop2", district="university"))
        state.wagons.append(Wagon(key="wagon2", shop_key="shop2"))
        with self.assertRaises(ValueError) as caught:
            validate_addresses(state)
        self.assertIn("undated", str(caught.exception))
        with self.assertRaises(ValueError) as also:
            models.founding_shop(state)
        self.assertEqual(str(caught.exception), str(also.exception))

    def test_the_channel_refuses_an_address_that_does_not_exist(self):
        # `critic@ghost` was a whole address's dice conjured out of a
        # typo: `state` was passed in and never consulted.
        state = _with_site(day=7, acceptance=5)
        with self.assertRaises(KeyError):
            models.address_channel(state, "ghost", "critic")
        with self.assertRaises(KeyError):
            models.address_channel(state, "", "law")

    def test_the_legacy_channel_follows_the_founding_address(self):
        # Not the SPELLING `shop1`: a valid world whose founding shop
        # is keyed otherwise used to lose the legacy generator every
        # existing study and both identity gates were measured on.
        state = _renamed_founding("zzz_home")
        self.assertEqual(
            models.address_channel(state, "zzz_home", "critic"), "critic")
        self.assertEqual(
            models.address_channel(state, "zzz_home", "law"), "law")

    def test_a_second_address_still_derives_from_its_own_key(self):
        state = _with_site(day=7, acceptance=5)
        self.assertEqual(
            models.address_channel(state, "shop2", "critic"),
            "critic@shop2")
        self.assertEqual(
            models.address_channel(state, HOME_SHOP_KEY, "critic"),
            "critic")


class TestTheCompatibilityReportIsTheFoundingShift(unittest.TestCase):
    """P4b.1a review, blocking item 4: service promised the founding
    shift as the legacy top-level report and delivered the FIRST shift
    in key order. A second address keyed `aaa` therefore handed every
    existing consumer a different restaurant's day under the name they
    have always read."""

    def _pair_sorting_before_home(self):
        state = new_state()
        state.day = 7
        state.shops.append(Shop(
            key="aaa_shop", district="university", reputation=20.0,
            ingredients=40, stash={}, acceptance_day=5,
            opening_day=5 + CONSTRUCTION_DAYS))
        state.wagons.append(Wagon(key="wagon2", shop_key="aaa_shop"))
        market.roll_prices(state, random.Random(3))
        validate_addresses(state)
        # Two DIFFERENT days, so the report can only be one of them.
        state.shop_by_key(HOME_SHOP_KEY).demand_today = 20
        state.shop_by_key("aaa_shop").demand_today = 7
        return state

    def test_the_report_describes_the_founding_address(self):
        state = self._pair_sorting_before_home()
        self.assertEqual([a.key for a in models.addresses_allowing(
            state, "service")], ["aaa_shop", HOME_SHOP_KEY])
        report = phases.service(state, {"routes": {}}, Listening(),
                                Streams(3))
        self.assertEqual(report["demand"], 20)
        self.assertEqual(
            report["revenue"],
            state.shop_by_key(HOME_SHOP_KEY).legit_revenue_today)

    def test_both_addresses_still_trade(self):
        # The correction picks WHICH shift is the compatibility
        # report; it does not stop the other address trading.
        state = self._pair_sorting_before_home()
        con = Listening()
        phases.service(state, {"routes": {}}, con, Streams(3))
        self.assertTrue(con.said("University Hill: Orders"), con.lines)
        self.assertTrue(con.said("Old Harbor: Orders"), con.lines)
        self.assertGreater(
            state.shop_by_key("aaa_shop").legit_revenue_today, 0)

    def test_one_address_reports_exactly_as_it_always_did(self):
        # The behaviour-equivalence anchor: with one address the
        # founding shift IS the only shift, so every consumer reads
        # what it always read.
        state = new_state()
        market.roll_prices(state, random.Random(3))
        report = phases.service(state, {"routes": {}}, Listening(),
                                Streams(3))
        home = state.shop_by_key(HOME_SHOP_KEY)
        self.assertEqual(report["revenue"], home.legit_revenue_today)


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

    def test_a_site_carrying_an_order_book_is_refused(self):
        # §2.4.2's initial state, bound at persistence (P4b.1a
        # review): an address that serves nobody cannot also record
        # customers, a delivery pool or a day's honest till.
        for name, value in (("demand_today", 49),
                            ("delivery_pool", 17),
                            ("legit_revenue_today", 123)):
            state = self._valid()
            setattr(state.shop_by_key("shop2"), name, value)
            with self.assertRaises(ValueError) as caught:
                validate_addresses(state)
            self.assertIn("no order book", str(caught.exception))
            self.assertIn(name, str(caught.exception))

    def test_an_open_address_keeps_its_order_book(self):
        # The refusal is the CONSTRUCTION phase's, not a new rule
        # about order books: the same numbers pass the morning the
        # address opens.
        state = _with_site(day=7, acceptance=5)
        site = state.shop_by_key("shop2")
        site.demand_today, site.delivery_pool = 49, 17
        site.legit_revenue_today = 123
        validate_addresses(state)

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

    def test_an_injected_order_book_no_longer_survives_a_round_trip(self):
        # The reviewer's exact repro: demand 49, deliveries 17 and
        # $123 of takings written onto a building site survived the
        # morning AND a save/load, so the payload claimed a
        # restaurant that does not exist. It refuses at the boundary
        # now — one field at a time, because each is a separate claim.
        state = _with_site(day=6, acceptance=5)
        save.state_from_dict(save.state_to_dict(state))      # baseline
        for name, value in (("demand_today", 49),
                            ("delivery_pool", 17),
                            ("legit_revenue_today", 123)):
            payload = save.state_to_dict(state)
            payload["shops"][1][name] = value
            with self.assertRaises(ValueError) as caught:
                save.state_from_dict(payload)
            self.assertIn("no order book", str(caught.exception))

    def test_a_false_zero_is_not_an_empty_order_book(self):
        # `False == 0` and `0.0 == 0`, so a bare `!= 0` accepted a
        # boolean and a float where the field counts customers,
        # delivery orders and dollars (P4b.1a review, second pass).
        # Each field and each false zero separately, through the REAL
        # save boundary — a payload that types a count as a flag is
        # malformed even when its arithmetic agrees today.
        state = _with_site(day=6, acceptance=5)
        for name in ("demand_today", "delivery_pool",
                     "legit_revenue_today"):
            for bad in (False, True, 0.0, 0.5):
                with self.subTest(f"{name}={bad!r}"):
                    payload = save.state_to_dict(state)
                    payload["shops"][1][name] = bad
                    with self.assertRaises(ValueError) as caught:
                        save.state_from_dict(payload)
                    self.assertIn("no order book", str(caught.exception))

    def test_exact_integer_zero_still_loads(self):
        # The other end: absence and exact integer zero are the valid
        # states, and a site that carries them reloads unremarkably.
        state = _with_site(day=6, acceptance=5)
        payload = save.state_to_dict(state)
        for name in ("demand_today", "delivery_pool",
                     "legit_revenue_today"):
            self.assertEqual(payload["shops"][1][name], 0)
            payload["shops"][1][name] = 0
        loaded = save.state_from_dict(payload)
        site = loaded.shop_by_key("shop2")
        self.assertEqual((site.demand_today, site.delivery_pool,
                          site.legit_revenue_today), (0, 0, 0))

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
