"""P4b.3 — THE ADDRESS-PRESSURE MATRIX (design rev. 30 item 3, rows
corrected by rev. 34 item 4).

The root invariant: **a target is selected ONCE by identity,
persisted wherever the consequence is delayed, and every consequence
resolves against THAT identity.**

Every row here is invisible at a single address — one shop is always
the softest, always the one a warning names, and always the district
heat lands in — so no identity gate proves any of it, which is why
rev. 30 item 3 asks for the matrix by name.

The rows are grouped by the authority that OWNS them, because a
matrix that mislabels which authority owns a consequence proves the
wrong thing (rev. 34 item 4): the price war owns coupon days, the tip
owns heat, the warning owns the freeze, the arriving raid owns the
room it hits, and the law sweeps every address independently and
consults the rival target NEVER.
"""

import random
import unittest

from extra_toppings import models, phases, rivals, save
from extra_toppings.models import (HOME_SHOP_KEY, RaidWarning, Shop,
                                   TributeDemand, Wagon, new_state)
from extra_toppings.rng import Streams
from extra_toppings.ui import ScriptedConsole

class Watching(ScriptedConsole):
    def __init__(self, script=None):
        super().__init__(script)
        self.lines: list = []

    def say(self, text: str = "") -> None:
        self.lines.append(text)

    def bullet(self, text: str) -> None:
        self.lines.append(f"• {text}")

    def menu(self, prompt, options):
        # Options are player-facing text too — the guard's presence is
        # announced in a menu label, not in prose.
        self.lines.append(prompt)
        self.lines.extend(options)
        return super().menu(prompt, options)

    def said(self, fragment: str) -> bool:
        return any(fragment in line for line in self.lines)


def two_open(day: int = 6):
    """Two OPEN addresses: the founding room in Old Harbor and a
    second in University Hill, open since day 3. Both are real
    records in the world, not fixtures posed beside it."""
    state = new_state()
    state.day = day
    state.clean, state.dirty = 4000, 4000
    state.shops.append(Shop(key="shop2", district="university",
                            reputation=50.0,
                            acceptance_day=1, opening_day=3,
                            manager_post=models.ManagerPost(
                                vacancy_day=1, opportunity="declined")))
    state.wagons.append(Wagon(key="wagon2", shop_key="shop2"))
    return state, state.shops[0], state.shops[1]


def post(state, first_name: str, shop_key: str, nerve: int | None = None):
    """Put somebody on the payroll, read in, AT a named address —
    which is what makes them a defender of that address and of no
    other."""
    who = next(e for e in state.employees if e.name.startswith(first_name))
    who.hired = True
    who.aware = True
    who.shop_key = shop_key
    if nerve is not None:
        who.nerve = nerve
    return who


# ══ the view both sides read ══════════════════════════════════════

class TestTheDefenseView(unittest.TestCase):
    """One definition of "defended" (rev. 29 item 2), and the formula
    preserved rather than paraphrased (rev. 30 item 4)."""

    def test_an_undefended_address_scores_the_baseline_not_zero(self):
        state, home, _second = two_open()
        view = models.shop_defense(state, home)
        self.assertEqual(view.defenders, ())
        self.assertEqual(view.strength, models.DEFENSE_BASELINE_NERVE)
        self.assertEqual(view.strength, 3)      # the number, spelled out
        self.assertFalse(view.guard)

    def test_the_guard_is_worth_exactly_four_and_only_where_it_is(self):
        state, home, second = two_open()
        home.upgrades.add("guard")
        self.assertEqual(models.shop_defense(state, home).strength,
                         models.DEFENSE_BASELINE_NERVE
                         + models.GUARD_DEFENSE_BONUS)
        self.assertEqual(models.shop_defense(state, home).strength, 7)
        # The upgrade is bought for a room and helps that room.
        self.assertEqual(models.shop_defense(state, second).strength, 3)
        self.assertFalse(models.shop_defense(state, second).guard)

    def test_defenders_are_the_people_who_are_actually_there(self):
        state, home, second = two_open()
        here = post(state, "Angelo", HOME_SHOP_KEY, nerve=9)
        there = post(state, "Marcus", "shop2", nerve=8)
        self.assertEqual(models.shop_defense(state, home).defenders,
                         (here,))
        self.assertEqual(models.shop_defense(state, second).defenders,
                         (there,))
        self.assertEqual(models.shop_defense(state, home).strength, 9)
        self.assertEqual(models.shop_defense(state, second).strength, 8)

    def test_the_unread_and_the_unavailable_defend_nothing(self):
        state, home, _second = two_open()
        naive = next(e for e in state.employees
                     if "Bee" in e.name)
        naive.hired, naive.aware, naive.shop_key = True, False, HOME_SHOP_KEY
        hurt = post(state, "Angelo", HOME_SHOP_KEY, nerve=9)
        hurt.injured_days = 2
        self.assertEqual(models.shop_defense(state, home).defenders, ())
        self.assertEqual(models.shop_defense(state, home).strength, 3)

    def test_a_detached_copy_cannot_lend_a_fictional_guard(self):
        # rev. 34 item 1: a `Shop` is a mutable record, not an
        # identity. A copy carrying a real key would otherwise
        # contribute an upgrade the world does not have to a
        # targeting decision.
        state, home, _second = two_open()
        forgery = Shop(key=home.key, district=home.district,
                       upgrades={"guard"})
        with self.assertRaises(ValueError):
            models.shop_defense(state, forgery)
        # …and the same question asked by IDENTITY is answered.
        self.assertEqual(models.shop_defense(state, home.key).strength, 3)


# ══ row 1-2: selection is by identity, and staffing drives it ══════

class TestSelectionIsByIdentity(unittest.TestCase):
    def test_staffing_moves_the_target(self):
        # THE lever, asserted as an exact change of answer rather than
        # as an inspection: the same world, one person moved, a
        # different room chosen.
        state, _home, _second = two_open()
        muscle = post(state, "Angelo", HOME_SHOP_KEY, nerve=9)
        self.assertEqual(models.raid_target(state, "vinnie"), "shop2")
        muscle.shop_key = "shop2"
        self.assertEqual(models.raid_target(state, "vinnie"), HOME_SHOP_KEY)

    def test_the_guard_alone_can_move_the_target(self):
        state, home, _second = two_open()
        self.assertEqual(models.raid_target(state, "sal"), HOME_SHOP_KEY)
        home.upgrades.add("guard")                    # 3 -> 7
        self.assertEqual(models.raid_target(state, "sal"), "shop2")

    def test_list_order_decides_nothing(self):
        # The property the P4a refusal was really protecting.
        state, _home, _second = two_open()
        post(state, "Angelo", HOME_SHOP_KEY, nerve=9)
        chosen = models.raid_target(state, "vinnie")
        state.shops.reverse()
        state.wagons.reverse()
        self.assertEqual(models.raid_target(state, "vinnie"), chosen)

    def test_the_tie_breaks_run_all_one_way(self):
        # Equal strength -> fewer defenders; then equal both ->
        # lower reputation; then equal all three -> the stable key.
        # Every component ASCENDS: softest means smallest on each.
        state, home, second = two_open()
        a = post(state, "Angelo", HOME_SHOP_KEY, nerve=6)
        post(state, "Marcus", "shop2", nerve=6)
        post(state, "Sammy", "shop2", nerve=4)        # a second body
        self.assertEqual(models.raid_target(state, "sal"), HOME_SHOP_KEY)
        a.shop_key = "shop2"                          # 0 here, 3 there
        self.assertEqual(models.raid_target(state, "sal"), HOME_SHOP_KEY)
        # Strength and headcount level; reputation decides.
        for e in list(state.employees):
            e.hired = False
        home.reputation, second.reputation = 60.0, 20.0
        self.assertEqual(models.raid_target(state, "sal"), "shop2")
        home.reputation = second.reputation           # dead level
        self.assertEqual(models.raid_target(state, "sal"), HOME_SHOP_KEY)

    def test_a_construction_site_is_not_a_target(self):
        state, _home, second = two_open()
        second.acceptance_day = state.day             # still being built
        second.opening_day = state.day + models.CONSTRUCTION_DAYS
        second.manager_post = models.ManagerPost(
            vacancy_day=state.day, opportunity="declined")
        self.assertEqual(models.raid_target(state, "vinnie"), HOME_SHOP_KEY)
        # Even when it would obviously be the softest thing standing.
        post(state, "Angelo", HOME_SHOP_KEY, nerve=9)
        self.assertEqual(models.raid_target(state, "vinnie"), HOME_SHOP_KEY)

    def test_no_address_refuses_rather_than_defaulting(self):
        state, _home, _second = two_open()
        state.shops = []
        with self.assertRaises(ValueError):
            models.raid_target(state, "vinnie")


# ══ row 3-4: delayed consequences persist their address ═══════════

class TestDelayedConsequencesKeepTheirAddress(unittest.TestCase):
    def test_a_warning_survives_the_save_boundary_unretargeted(self):
        state, _home, _second = two_open()
        state.rivals["vinnie"].warning = RaidWarning(2, "shop2")
        # Make the OTHER room softest after the warning went up: a
        # reload must not re-ask the question.
        post(state, "Marcus", "shop2", nerve=9)
        self.assertEqual(models.raid_target(state, "vinnie"), HOME_SHOP_KEY)
        back = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(back.rivals["vinnie"].warning,
                         RaidWarning(2, "shop2"))

    def test_a_standing_demand_survives_the_save_boundary(self):
        state, _home, _second = two_open()
        state.rivals["sal"].tribute = TributeDemand(900, "shop2")
        back = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(back.rivals["sal"].tribute,
                         TributeDemand(900, "shop2"))
        self.assertEqual(back.rivals["sal"].tribute_demanded, 900)

    def test_a_demand_and_a_warning_must_name_one_room(self):
        state, _home, _second = two_open()
        state.rivals["sal"].tribute = TributeDemand(900, "shop2")
        state.rivals["sal"].warning = RaidWarning(2, HOME_SHOP_KEY)
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(state))
        self.assertIn("one man, two rooms", str(caught.exception))

    def test_a_standing_demand_aims_the_warning_it_precedes(self):
        # THE operational half (rev. 34 item 3), driven through the
        # real rival phase: the man already collecting on University
        # Hill threatens University Hill, even though the home room
        # is softer tonight.
        state, _home, _second = two_open()
        post(state, "Marcus", "shop2", nerve=9)       # shop2 is HARDEST
        self.assertEqual(models.raid_target(state, "sal"), HOME_SHOP_KEY)
        state.rivals["sal"].tribute = TributeDemand(900, "shop2")
        state.rivals["vinnie"].strength = 0            # one actor only
        state.rivals["sal"].relation = -100.0          # they will act
        con, seen = Watching(), None
        for seed in range(200):
            probe = save.state_from_dict(save.state_to_dict(state))
            rivals.rival_phase(probe, con, random.Random(seed))
            if probe.rivals["sal"].warning is not None:
                seen = probe.rivals["sal"].warning
                break
        self.assertIsNotNone(seen, "no seed raised a warning")
        self.assertEqual(seen.shop_key, "shop2")

    def test_a_legacy_scalar_demand_with_two_rooms_refuses(self):
        # Its target is unrecoverable and a home default would enrol
        # the wrong room in a weekly shakedown.
        state, _home, _second = two_open()
        payload = save.state_to_dict(state)
        payload["rivals"]["sal"].pop("tribute")
        payload["rivals"]["sal"]["tribute_demanded"] = 900
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(payload)
        self.assertIn("cannot be inferred", str(caught.exception))

    def test_a_legacy_scalar_demand_with_one_room_migrates(self):
        state = new_state()
        payload = save.state_to_dict(state)
        payload["rivals"]["sal"].pop("tribute")
        payload["rivals"]["sal"]["tribute_demanded"] = 900
        back = save.state_from_dict(payload)
        self.assertEqual(back.rivals["sal"].tribute,
                         TributeDemand(900, HOME_SHOP_KEY))

    def test_a_legacy_zero_is_no_demand_at_all(self):
        state = new_state()
        payload = save.state_to_dict(state)
        payload["rivals"]["sal"].pop("tribute")
        payload["rivals"]["sal"]["tribute_demanded"] = 0
        self.assertIsNone(save.state_from_dict(payload).rivals["sal"].tribute)

    def test_the_two_spellings_are_an_exact_union(self):
        state = new_state()
        both = save.state_to_dict(state)
        both["rivals"]["sal"]["tribute_demanded"] = 900
        with self.assertRaises(ValueError):
            save.state_from_dict(both)          # both
        neither = save.state_to_dict(state)
        neither["rivals"]["sal"].pop("tribute")
        with self.assertRaises(ValueError):
            save.state_from_dict(neither)       # neither


# ══ row 5-6: the tip and the price war, by their own owners ═══════

class TestThePriceWarAndTheTip(unittest.TestCase):
    """Rev. 34 item 4: coupon days belong to the price war and heat
    to the tip. Neither is a raid consequence."""

    def test_the_price_war_papers_the_selected_neighbourhood(self):
        state, home, second = two_open()
        post(state, "Angelo", HOME_SHOP_KEY, nerve=9)   # shop2 is softest
        rivals._price_war(state, "vinnie", {"short": "Vinnie"}, Watching())
        self.assertEqual(second.coupon_days, 3)
        self.assertEqual(home.coupon_days, 0)

    def test_the_tip_heats_the_addressed_district_not_the_home_one(self):
        state, _home, _second = two_open()
        post(state, "Angelo", HOME_SHOP_KEY, nerve=9)   # shop2 is softest
        before_home = state.heat("old_harbor")
        before_there = state.heat("university")
        rivals._plant(state, state.rivals["sal"], {"short": "Sal"},
                      Watching(), random.Random(4))
        self.assertEqual(state.heat("old_harbor"), before_home)
        self.assertEqual(state.heat("university"), before_there + 12)

    def test_the_tip_still_lands_home_when_home_is_all_there_is(self):
        # The released identity, asserted rather than assumed.
        state = new_state()
        before = state.heat("old_harbor")
        rivals._plant(state, state.rivals["sal"], {"short": "Sal"},
                      Watching(), random.Random(4))
        self.assertEqual(state.heat("old_harbor"), before + 12)


# ══ row 7: the arriving raid resolves against the frozen address ═══

class TestTheRaidLandsWhereItWasAimed(unittest.TestCase):
    """Every consequence of the raid — the guard consulted, the crew
    that fights, the damage, the stash, the reputation and the heat —
    reads the WARNING's address."""

    def _arrive(self, aimed: str, script, seed=11, muscle_at=HOME_SHOP_KEY):
        state, home, second = two_open()
        home.stash = {"mushrooms": 6}
        second.stash = {"mushrooms": 6}
        home.upgrades.add("guard")
        post(state, "Angelo", muscle_at, nerve=9)
        post(state, "Marcus", "shop2", nerve=2)
        state.rivals["vinnie"].warning = RaidWarning(1, aimed)
        state.rivals["sal"].strength = 0
        con = Watching(script)
        report = {"wagons": phases.WagonNight(state)}
        phases.night(state, {"routes": {}, "raid": None}, report, con,
                     Streams(seed))
        return state, home, second, con

    def test_the_named_room_takes_the_damage_and_the_other_is_untouched(self):
        state, home, second, _con = self._arrive("shop2", [0])
        self.assertGreater(second.damage_days, 0)
        self.assertEqual(home.damage_days, 0)
        self.assertLess(second.reputation, 50.0)
        self.assertEqual(home.reputation, 50.0)

    def test_the_heat_rises_in_the_named_room_s_district(self):
        # Paired, because the night also cools every district by the
        # flat decay: what is asserted is the raid's OWN addition
        # landing in the aimed district and in no other.
        there, _h, _s, _c = self._arrive("shop2", [0])
        self.assertGreater(there.heat("university"),
                           there.heat("old_harbor"))
        here, _h2, _s2, _c2 = self._arrive(HOME_SHOP_KEY, [0])
        self.assertGreater(here.heat("old_harbor"),
                           here.heat("university"))

    def test_the_stash_taken_is_the_named_room_s(self):
        _state, home, second, _con = self._arrive("shop2", [0])
        self.assertEqual(home.stash, {"mushrooms": 6})
        self.assertLess(second.stash.get("mushrooms", 0), 6)

    def test_the_guard_is_the_named_room_s_own(self):
        # Home has night security; the raid on shop2 must not read it.
        _s, _h, _second, con = self._arrive("shop2", [0])
        self.assertFalse(con.said("night security helps"))
        _s2, _h2, _sec2, con2 = self._arrive(HOME_SHOP_KEY, [0])
        self.assertTrue(con2.said("night security helps"))

    def test_nobody_across_town_is_hurt_defending_a_room_they_are_not_in(self):
        # EXECUTED, not inspected. The raid draws its casualty from
        # the defenders; with the global crew, Angelo — who works the
        # home room — could be carried out of a fight in University
        # Hill. Scan real nights until one lands with an injury.
        hurt_somebody = False
        for seed in range(80):
            state, _home, _second, _con = self._arrive("shop2", [0],
                                                       seed=seed)
            wounded = [e for e in state.employees if e.injured_days]
            if not wounded:
                continue
            hurt_somebody = True
            for e in wounded:
                self.assertEqual(e.shop_key, "shop2", e.name)
        self.assertTrue(hurt_somebody, "no seed produced an injury")

    def test_the_room_s_own_crew_decides_whether_it_holds(self):
        # The same night, the same seed, one person moved: Angelo
        # (nerve 9) at the door changes whether University Hill is
        # repelled. With a global crew he was already defending it
        # from across town, so the two runs were identical.
        flipped = False
        for seed in range(80):
            weak, _h, second, _c = self._arrive("shop2", [0], seed=seed)
            strong, _h2, second2, _c2 = self._arrive(
                "shop2", [0], seed=seed, muscle_at="shop2")
            if second.damage_days and not second2.damage_days:
                flipped = True
                break
        self.assertTrue(
            flipped,
            "moving the muscle to the threatened room changed no night")


# ══ row 8: the law is not an instrument of Sal's grudge ═══════════

class TestTheLawSweepsIndependently(unittest.TestCase):
    def test_every_address_is_swept_against_its_own_district(self):
        # rev. 34 item 4: the law consults NO rival target. Only the
        # hot district's room is searched, whoever the rivals are
        # currently interested in.
        state, home, second = two_open()
        second.stash = {"mushrooms": 8}
        home.stash = {"mushrooms": 8}
        state.districts["university"].heat = 95.0
        state.districts["old_harbor"].heat = 0.0
        # A warning aimed at the HOME room, to prove the sweep does
        # not follow it.
        state.rivals["vinnie"].warning = RaidWarning(3, HOME_SHOP_KEY)
        searched = False
        for seed in range(60):
            probe = save.state_from_dict(save.state_to_dict(state))
            phases._law_phase(probe, Watching(), Streams(seed))
            hit = probe.shop_by_key("shop2")
            if hit.stash.get("mushrooms", 0) == 0:
                searched = True
                # The cold room keeps everything, every time.
                self.assertEqual(
                    probe.shop_by_key(HOME_SHOP_KEY).stash,
                    {"mushrooms": 8})
                break
            self.assertEqual(probe.shop_by_key(HOME_SHOP_KEY).stash,
                             {"mushrooms": 8})
        self.assertTrue(searched, "no seed reached a walk-through")

    def test_a_construction_site_is_never_searched(self):
        state, _home, second = two_open()
        second.acceptance_day = state.day
        second.opening_day = state.day + models.CONSTRUCTION_DAYS
        # The post's vacancy day belongs to the address's own span.
        second.manager_post = models.ManagerPost(
            vacancy_day=state.day, opportunity="declined")
        second.stash = {"mushrooms": 8}
        state.districts["university"].heat = 100.0
        for seed in range(40):
            probe = save.state_from_dict(save.state_to_dict(state))
            phases._law_phase(probe, Watching(), Streams(seed))
            self.assertEqual(probe.shop_by_key("shop2").stash,
                             {"mushrooms": 8})


# ══ row 9: a dead owner mounts no counterplay ═════════════════════

class TestADeadOwnerAnswersNothing(unittest.TestCase):
    def test_a_broken_rival_takes_no_action_at_all(self):
        state, _home, _second = two_open()
        state.rivals["sal"].strength = 0
        state.rivals["vinnie"].strength = 0
        for seed in range(30):
            probe = save.state_from_dict(save.state_to_dict(state))
            rivals.rival_phase(probe, Watching(), random.Random(seed))
            for key in ("sal", "vinnie"):
                self.assertIsNone(probe.rivals[key].warning)
                self.assertIsNone(probe.rivals[key].tribute)

    def test_the_grudge_is_the_intensification_and_it_is_already_there(self):
        # rev. 34: the −25 turf delta IS the ongoing counterplay,
        # because `rival_policy` derives grudge from relation. No
        # second multiplier prices the same offense twice.
        state, _home, _second = two_open()
        calm = rivals.rival_policy(state, "sal").act_chance
        models.adjust_relation(state, "sal", -25.0)
        self.assertGreater(rivals.rival_policy(state, "sal").act_chance,
                           calm)

    def test_an_offended_owner_still_hits_the_softest_room(self):
        # They are not obliged to hit the room that provoked them.
        state, _home, _second = two_open()
        post(state, "Marcus", "shop2", nerve=9)   # University is hard
        models.adjust_relation(state, "sal", -25.0)
        self.assertEqual(models.raid_target(state, "sal"), HOME_SHOP_KEY)


# ══ the heat teeth Partner adopts ════════════════════════════════

class TestTheHeatTeeth(unittest.TestCase):
    def test_partner_feels_the_weather_at_the_war_s_own_constants(self):
        state, _home, _second = two_open()
        state.districts["university"].heat = models.HEAT_RED
        self.assertTrue(
            models.district_heat_policy(state, "university").plannable)
        state.branch = "partner"
        red = models.district_heat_policy(state, "university")
        self.assertFalse(red.plannable)
        self.assertEqual(red.band, "red")
        state.districts["university"].heat = models.HEAT_AMBER
        amber = models.district_heat_policy(state, "university")
        self.assertEqual((amber.band, amber.capacity_mult), ("amber", 0.5))

    def test_the_released_chairs_still_feel_nothing(self):
        state, _home, _second = two_open()
        state.districts["university"].heat = 100.0
        for branch in (None, "straight", "quiet_sale"):
            with self.subTest(branch=branch):
                state.branch = branch
                pol = models.district_heat_policy(state, "university")
                self.assertEqual((pol.band, pol.capacity_mult), ("cool", 1.0))


if __name__ == "__main__":
    unittest.main()
