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
from extra_toppings import (data, market, models, phases, raids, routes,
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

    def say(self, text: str = "") -> None:
        self.lines.append(text)

    def bullet(self, text: str) -> None:
        self.lines.append(f"• {text}")

    def said(self, fragment: str) -> bool:
        return any(fragment in line for line in self.lines)


def _raid_plan(state, objective):
    """A raid planned through the REAL planner: pick the rival, the
    objective, the crew, unarmed."""
    script = [0, ("steal_stock", "photograph_ledger",
                  "wreck_ovens").index(objective), 0, False, False]
    return raids.plan_raid(
        state, Listening(script), random.Random(3), reserved=[],
        wagon=models.PlannedWagon((models.HOME_WAGON_KEY,)))


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
        view = phases.planned_wagon(state, {}, "shop2")
        self.assertFalse(view.available)
        self.assertEqual(view.blocked_by, "lifecycle")
        self.assertIn("contractor's yard", view.note)

    def test_the_open_address_plans_freely_alongside_it(self):
        state = _with_site(day=6, acceptance=5)
        view = phases.planned_wagon(state, {}, HOME_SHOP_KEY)
        self.assertTrue(view.available)
        self.assertEqual((view.note, view.blocked_by), ("", ""))

    def test_a_planned_job_outranks_the_lifecycle_as_the_reason(self):
        # Ordering matches WagonNight.note_at: a wagon the pickup has
        # is never described as sitting at the contractor's yard.
        state = _with_site(day=7, acceptance=5)
        view = phases.planned_wagon(
            state, {"salvage": {"rival": "vinnie",
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
        plans = {"route": {"origin_shop": HOME_SHOP_KEY,
                           "driver": None}}
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
        view = phases.planned_wagon(state, {}, "shop2")
        self.assertEqual(view.free, ("wagon2", "wagon3"))
        self.assertEqual(view.first, "wagon2")
        plans = {"route": {"origin_shop": "shop2"}}
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
        plans = {"route": {"origin_shop": "ghost", "driver": None}}
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
            _with_site(day=6, acceptance=5), {}, "shop2")
        with self.assertRaises(RuntimeError):
            blocked.first

    def test_planning_and_execution_agree_on_every_day(self):
        # The two halves must never disagree — that disagreement is
        # exactly what produced a menu that accepted a plan execution
        # would then refuse.
        for day in (5, 6, 7, 8):
            state = _with_site(day=day, acceptance=5)
            planned = phases.planned_wagon(state, {}, "shop2")
            executed = phases.WagonNight(state).view_at("shop2")
            self.assertEqual(planned.available, executed.available, day)
            self.assertEqual(planned.note, executed.note, day)

    def test_the_opening_morning_flips_both_halves_together(self):
        state = _with_site(day=6, acceptance=5)
        self.assertFalse(phases.planned_wagon(state, {}, "shop2").available)
        state.day = 7                       # the recorded opening day
        view = phases.planned_wagon(state, {}, "shop2")
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
        return phases.planned_wagon(state, {}, "shop2")

    def test_a_raid_says_the_wagon_is_at_the_yard(self):
        state = new_state()
        con = Listening()
        raids.plan_raid(state, con, random.Random(3), reserved=[],
                        wagon=self._yard_view())
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
                            note=models.WAGON_NOTES["route"]))
        self.assertTrue(con.said(
            "The wagon is out on tonight's route — whatever the crew "
            "takes, they carry on foot."))

    def test_a_ledger_raid_is_unaffected_and_goes_on_foot(self):
        # Only a stock theft loads the wagon (rev. 26); the others
        # were always on foot and must not acquire a refusal.
        state = new_state()
        con = Listening()
        raids.plan_raid(state, con, random.Random(3), reserved=[],
                        wagon=models.PlannedWagon(("wagon1",)))
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
            view = models.PlannedWagon(blocked_by=job,
                                       note=models.WAGON_NOTES[job])
            self.assertEqual(models.wagon_gone_line(view), expected)

    def test_the_lifecycle_names_the_address(self):
        view = phases.planned_wagon(
            _with_site(day=6, acceptance=5), {}, "shop2")
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
                            note=models.WAGON_NOTES["salvage"]))
        self.assertTrue(con.said(
            "  The wagon is out on tonight's pickup — whatever the "
            "crew takes, they carry on foot."), con.lines)
        self.assertFalse(con.said("out on tonight's route"))

    def test_a_free_wagon_has_no_absence_to_explain(self):
        with self.assertRaises(ValueError):
            models.wagon_gone_line(models.PlannedWagon(("wagon1",)))


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
            phases.planned_wagon(state, {}, HOME_SHOP_KEY).available)
        for day in (1, 15, 30):
            state.day = day
            self.assertTrue(
                phases.planned_wagon(state, {}, HOME_SHOP_KEY).available)


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
        view = phases.planned_wagon(state, {}, HOME_SHOP_KEY)
        plan = routes.plan_route(state, Listening([0, 0, False, 0, 0]),
                                 random.Random(3), reserved=[],
                                 wagon=view)
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
                                    ("photograph_ledger", None),
                                    ("wreck_ovens", None)):
            plan = _raid_plan(state, objective)
            self.assertEqual(plan["wagon_key"], expected, objective)

    def test_execution_spends_the_named_wagon(self):
        state = _with_site(day=7, acceptance=5)
        night = phases.WagonNight(state)
        self.assertTrue(night.claim_key("wagon2", "route"))
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
        self.assertTrue(night.claim_key("wagon2", "route"))
        self.assertFalse(night.claim_key("wagon2", "raid"))
        self.assertEqual(night.claims, {"wagon2": "route"})

    def test_a_construction_wagon_cannot_be_claimed_by_key(self):
        state = _with_site(day=6, acceptance=5)
        self.assertFalse(phases.WagonNight(state).claim_key("wagon2",
                                                            "route"))

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
        self.assertTrue(night.claim_key(models.HOME_WAGON_KEY, "route"))
        self.assertTrue(night.claim_key("wagon2", "route"))
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
        plans = {"route": {"origin_shop": HOME_SHOP_KEY,
                           "wagon_key": models.HOME_WAGON_KEY}}
        self.assertFalse(
            phases.planned_wagon(state, plans, HOME_SHOP_KEY).available)
        plan = _raid_plan(state, "steal_stock")
        self.assertEqual(plan["wagon_key"], models.HOME_WAGON_KEY)


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
