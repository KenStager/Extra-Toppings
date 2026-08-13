"""P3 views (rev. 14 items 4-5): the rival-policy view, the heat
policy, and the territorial route adjustments — flag-off identity and
in-branch behavior, driven through the real phases where a real path
exists."""

import unittest

from extra_toppings import data, models, phases, routes, war
from extra_toppings.game import new_state
from extra_toppings.models import (BranchState, apply_rival_damage,
                                   district_heat_policy, live_campaign,
                                   set_relation, validate_branch_state,
                                   validate_cross_state, HEAT_AMBER,
                                   HEAT_DECAY, HEAT_RED, HEAT_SLOW_DECAY,
                                   VENDETTA_RELATION)
from extra_toppings.rivals import rival_policy
from extra_toppings.rng import Streams
from extra_toppings.ui import Console
from route_support import departed


class Quiet(Console):
    def __init__(self):
        super().__init__()
        self.quiet = True
        self.lines: list = []

    def say(self, text=""):
        self.lines.append(text)

    def bullet(self, text):
        self.lines.append(f"• {text}")


def war_state(target="vinnie", declared_day=14):
    state = new_state()
    state.day = declared_day
    state.debt = 0
    state.debt_paid_day = declared_day - 1
    state.act = 2
    state.branch = "war"
    state.branch_state = BranchState.war(
        war_target=target, declared_day=declared_day,
        starting_strength=state.rivals[target].strength)
    set_relation(state, target,
                 min(state.rivals[target].relation, VENDETTA_RELATION))
    validate_branch_state("war", state.branch_state)
    validate_cross_state(state)
    return state


def break_target(state, target="vinnie"):
    """Capture through the real authority, as LEGAL history (rev. 20
    item 2): one job a night, booked, the calendar advanced."""
    from extra_toppings.models import RaidAttemptRecord
    camp = live_campaign(state, target)
    while state.rivals[target].alive:
        state.day += 1
        before = round(state.rivals[target].strength * 100)
        apply_rival_damage(state, target, "jobs", 12)
        state.raid_log.append(RaidAttemptRecord(
            day=state.day, rival=target, outcome="succeeded", crew=1,
            damage_h=before - round(state.rivals[target].strength
                                    * 100)))
    return camp


class TestRivalPolicyFlagOff(unittest.TestCase):
    def test_the_view_is_the_old_ladder_exactly(self):
        state = new_state()
        for key in ("sal", "vinnie"):
            spec = data.RIVALS[key]
            rival = state.rivals[key]
            grudge = max(0.0, -rival.relation) / 100
            pol = rival_policy(state, key)
            self.assertEqual(pol.act_chance,
                             spec["aggression"] * 0.5 + grudge * 0.6)
            self.assertEqual(pol.price_war_t, 0.30)
            self.assertEqual(pol.poach_t, 0.50)
            self.assertEqual(pol.extort_t, 0.68)
            self.assertEqual(
                pol.raid_t,
                0.68 + spec["violence"] * (0.5 + grudge) * 0.25)
            self.assertEqual(pol.raid_edge, 0.0)
            self.assertTrue(pol.hostile)
            self.assertEqual(pol.notes, ())

    def test_deep_grudges_keep_the_old_arithmetic(self):
        state = new_state()
        state.rivals["vinnie"].relation = -85.0
        spec = data.RIVALS["vinnie"]
        pol = rival_policy(state, "vinnie")
        self.assertEqual(pol.act_chance,
                         spec["aggression"] * 0.5 + 0.85 * 0.6)
        self.assertEqual(pol.raid_t,
                         0.68 + spec["violence"] * (0.5 + 0.85) * 0.25)


class TestRivalPolicyAtWar(unittest.TestCase):
    def test_the_target_comes_bigger_and_more_often(self):
        state = war_state()
        base = new_state()
        base.rivals["vinnie"].relation = state.rivals["vinnie"].relation
        pol = rival_policy(state, "vinnie")
        flat = rival_policy(base, "vinnie")
        self.assertEqual(pol.act_chance,
                         min(1.0, flat.act_chance * war.WAR_AGGRESSION))
        self.assertGreater(pol.raid_t, flat.raid_t)
        self.assertLessEqual(pol.raid_t, war.RAID_RUNG_CAP)
        self.assertEqual(pol.raid_edge, war.WAR_RAID_EDGE)

    def test_the_law_calm_halves_the_target(self):
        state = war_state()
        camp = live_campaign(state, "vinnie")
        camp.law_calm_until = state.day + 2
        calm = rival_policy(state, "vinnie")
        camp.law_calm_until = None
        loud = rival_policy(state, "vinnie")
        self.assertEqual(calm.act_chance,
                         min(1.0, loud.act_chance * war.LAW_CALM_ACT))

    def test_raised_violence_is_permanent_and_visible(self):
        state = war_state()
        camp = live_campaign(state, "vinnie")
        camp.violence_raised = True
        pol = rival_policy(state, "vinnie")
        self.assertLessEqual(pol.raid_t, war.RAID_RUNG_CAP)
        self.assertTrue(any("meaner" in n for n in pol.notes))

    def test_insured_sal_takes_no_hostile_action(self):
        state = war_state(target="vinnie")
        state.branch_state.insurance_paid_until = state.day + 3
        pol = rival_policy(state, "sal")
        self.assertFalse(pol.hostile)

    def test_uninsured_sal_tips_three_times_as_often(self):
        state = war_state(target="vinnie")
        flat = rival_policy(new_state(), "sal")
        pol = rival_policy(state, "sal")
        base_tip = 1.0 - flat.raid_t
        want = min(war.TIP_RUNG_MAX, base_tip * war.TIP_RUNG_MULT)
        self.assertAlmostEqual(1.0 - pol.raid_t, want, places=12)
        # The ladder keeps its order and stays inside [0, 1].
        self.assertTrue(0 < pol.price_war_t < pol.poach_t
                        < pol.extort_t < pol.raid_t < 1.0)

    def test_opportunist_vinnie_smells_blood(self):
        state = war_state(target="sal")
        set_relation(state, "sal",
                     min(state.rivals["sal"].relation, VENDETTA_RELATION))
        healthy = rival_policy(state, "vinnie")
        state.shop.damage_days = 2
        wounded = rival_policy(state, "vinnie")
        self.assertEqual(wounded.act_chance,
                         min(1.0, healthy.act_chance
                             * war.OPPORTUNIST_MULT))
        self.assertTrue(any("blood" in n for n in wounded.notes))


class TestHeatPolicy(unittest.TestCase):
    def test_flag_off_heat_has_no_teeth(self):
        state = new_state()
        state.districts["meadows"].heat = 95.0
        pol = district_heat_policy(state, "meadows")
        self.assertEqual((pol.band, pol.capacity_mult, pol.plannable,
                          pol.decay), ("cool", 1.0, True, HEAT_DECAY))

    def test_amber_halves_capacity_once_and_cools_slower(self):
        state = war_state()
        state.districts["meadows"].heat = HEAT_AMBER
        pol = district_heat_policy(state, "meadows")
        self.assertEqual((pol.band, pol.capacity_mult, pol.plannable,
                          pol.decay),
                         ("amber", 0.5, True, HEAT_SLOW_DECAY))

    def test_red_denies_the_district(self):
        state = war_state()
        state.districts["meadows"].heat = HEAT_RED
        pol = district_heat_policy(state, "meadows")
        self.assertFalse(pol.plannable)
        self.assertEqual(pol.band, "red")

    def test_red_scrubs_the_committed_route_at_service(self):
        state = war_state()
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.hired = True
        rosa.aware = True
        state.shop_stash["oregano"] = 10
        state.districts["old_harbor"].heat = HEAT_RED
        plan = {"district": "old_harbor", "driver": rosa,
                "ride_along": False, "cargo": {"oregano": 6}, "legit": 0, "origin_shop": models.HOME_SHOP_KEY,
                "wagon_key": models.HOME_WAGON_KEY}
        con = Quiet()
        self.assertFalse(phases._commit_route(state, plan, con, phases.WagonNight(state)))
        self.assertEqual(state.shop_stash["oregano"], 10)
        self.assertTrue(any("scrubbed" in ln for ln in con.lines))

    def test_the_night_decay_consumes_the_policy(self):
        state = war_state()
        state.districts["meadows"].heat = 60.0
        state.districts["university"].heat = 20.0
        for dk, d in state.districts.items():
            d.heat = max(0.0, d.heat - district_heat_policy(state, dk).decay)
        self.assertEqual(state.districts["meadows"].heat,
                         60.0 - HEAT_SLOW_DECAY)
        self.assertEqual(state.districts["university"].heat,
                         20.0 - HEAT_DECAY)


class TestTerritorialRoutes(unittest.TestCase):
    def _run_route(self, state, dk="old_harbor", units=10, seed=5):
        from extra_toppings import market
        market.roll_prices(state, Streams(seed).daily(state.day, "market"))
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.hired = True
        rosa.aware = True
        state.shop_stash[dk] = state.shop_stash.get(dk, 0)
        state.shop_stash["oregano"] = units
        plan = {"district": dk, "driver": rosa, "ride_along": False,
                "cargo": {"oregano": units}, "legit": 0, "origin_shop": models.HOME_SHOP_KEY,
                "wagon_key": models.HOME_WAGON_KEY}
        departure = departed(state, plan)
        return routes.resolve_route(departure, Quiet(),
                                    Streams(seed).routes)

    def test_corner_diversion_prices_the_night(self):
        state = war_state(target="vinnie")
        camp = live_campaign(state, "vinnie")
        before = state.rivals["vinnie"].strength
        report = self._run_route(state)
        if report["sold"] == 0:
            self.skipTest("route sold nothing under this seed")
        corners = [r for r in camp.damage if r.channel == "corners"]
        self.assertEqual(len(corners), 1)
        want = min(war.CORNER_CAP, report["sold"] * war.CORNER_RATE)
        self.assertEqual(corners[0].hundredths, round(want * 100))
        self.assertEqual(round((before - state.rivals["vinnie"].strength)
                               * 100), corners[0].hundredths)

    def test_the_outage_window_doubles_the_damage(self):
        state = war_state(target="vinnie")
        state.rivals["vinnie"].ovens_wrecked_days = 3
        camp = live_campaign(state, "vinnie")
        report = self._run_route(state)
        if report["sold"] == 0:
            self.skipTest("route sold nothing under this seed")
        corners = [r for r in camp.damage if r.channel == "corners"]
        want = min(war.CORNER_CAP * war.OUTAGE_MULT,
                   report["sold"] * war.CORNER_RATE * war.OUTAGE_MULT)
        self.assertEqual(corners[0].hundredths, round(want * 100))

    def test_the_bystanders_turf_diverts_nothing(self):
        state = war_state(target="vinnie")
        camp = live_campaign(state, "vinnie")
        report = self._run_route(state, dk="little_sicily")   # Sal's turf
        corners = [r for r in camp.damage if r.channel == "corners"]
        self.assertEqual(corners, [])
        self.assertEqual(len(camp.damage), 0)
        del report

    def test_flag_off_routes_divert_nothing(self):
        state = new_state()
        before = state.rivals["vinnie"].strength
        report = self._run_route(state)
        self.assertEqual(state.rivals["vinnie"].strength, before)
        del report

    def test_capture_transfers_the_underground_only(self):
        state = war_state(target="vinnie")
        self.assertEqual(war.underground_bonus(state, "old_harbor"), 0.0)
        break_target(state, "vinnie")
        for dk, want in (("old_harbor", war.CAPTURE_UNDERGROUND),
                         ("meadows", war.CAPTURE_UNDERGROUND),
                         ("university", 0.0), ("little_sicily", 0.0)):
            self.assertEqual(war.underground_bonus(state, dk), want)
        # The underground, and nothing else: no second shop appears.
        self.assertEqual(len(state.shops), 1)

    def test_no_bonus_outside_the_branch(self):
        state = new_state()
        for dk in data.DISTRICTS:
            self.assertEqual(war.underground_bonus(state, dk), 0.0)


class TestRaidEdge(unittest.TestCase):
    def test_edge_belongs_to_the_live_target_only(self):
        state = war_state(target="vinnie")
        self.assertEqual(war.raid_edge(state, "vinnie"), war.WAR_RAID_EDGE)
        self.assertEqual(war.raid_edge(state, "sal"), 0.0)
        self.assertEqual(war.raid_edge(new_state(), "vinnie"), 0.0)


if __name__ == "__main__":
    unittest.main()


class TestRouteMarketView(unittest.TestCase):
    """Rev. 15 item 5: THE territorial route-market view."""

    def test_flag_off_methods_are_the_legacy_arithmetic(self):
        from extra_toppings import market
        state = new_state()
        for dk in data.DISTRICTS:
            rm = market.route_market(state, dk)
            base = data.DISTRICTS[dk]["underground"]
            ev = market.event_mult(state, dk, "underground")
            for n in (0, 1, 2, 3):
                self.assertEqual(rm.drops(n),
                                 max(2, int((2 + 2 * n) * (base * ev))))
            self.assertEqual(rm.top_want(), max(2, int(4 * base * ev)))
            self.assertEqual(rm.bonus, 0.0)
            self.assertEqual(rm.corner_rate, 0.0)
            self.assertFalse(rm.captured)

    def test_the_view_prices_the_corner_terms(self):
        from extra_toppings import market
        state = war_state(target="vinnie")
        rm = market.route_market(state, "old_harbor")
        self.assertEqual((rm.corner_rate, rm.corner_cap),
                         (war.CORNER_RATE, war.CORNER_CAP))
        state.rivals["vinnie"].ovens_wrecked_days = 2
        rm = market.route_market(state, "old_harbor")
        self.assertEqual((rm.corner_rate, rm.corner_cap),
                         (war.CORNER_RATE * war.OUTAGE_MULT,
                          war.CORNER_CAP * war.OUTAGE_MULT))
        # The bystander's turf prices no corners.
        rm = market.route_market(state, "little_sicily")
        self.assertEqual(rm.corner_rate, 0.0)

    def test_capture_and_amber_flow_through_the_view(self):
        from extra_toppings import market
        state = war_state(target="vinnie")
        break_target(state, "vinnie")
        rm = market.route_market(state, "old_harbor")
        self.assertTrue(rm.captured)
        self.assertEqual(rm.bonus, war.CAPTURE_UNDERGROUND)
        state.districts["old_harbor"].heat = 60.0
        rm2 = market.route_market(state, "old_harbor")
        self.assertEqual(rm2.heat.band, "amber")
        self.assertEqual(rm2.drops(2), max(2, int(
            ((2 + 4) * (rm2.base * rm2.event)
             + (2 + 4) * rm2.bonus) * 0.5)))


class TestAlertnessPressure(unittest.TestCase):
    """Rev. 15's sanctioned war-pressure policy: one derivation for
    the payoff, the rival policy, and the board."""

    def test_flag_off_job_damage_is_the_same_object(self):
        state = new_state()
        base = 12
        self.assertIs(war.job_damage(state, "vinnie", base), base)

    def test_alert_targets_take_softer_jobs(self):
        from extra_toppings.models import apply_rival_damage
        state = war_state(target="vinnie")
        state.rivals["vinnie"].alertness = 6.0
        dmg = war.job_damage(state, "vinnie", 12)
        hard = 6.0 - war.ALERT_PRESSURE_KNEE
        self.assertAlmostEqual(dmg, 12 * (1.0 - hard * war.ALERT_IMPACT))
        applied = apply_rival_damage(state, "vinnie", "jobs", dmg)
        camp = live_campaign(state, "vinnie")
        self.assertEqual(camp.damage[-1].hundredths, round(dmg * 100))
        self.assertEqual(applied, round(dmg * 100) / 100)

    def test_the_impact_floor_holds(self):
        state = war_state(target="vinnie")
        state.rivals["vinnie"].alertness = 10.0
        self.assertAlmostEqual(
            war.job_damage(state, "vinnie", 12),
            12 * war.ALERT_IMPACT_FLOOR)

    def test_the_quiet_window_carries_no_pressure(self):
        # The knee (rev. 15): a sleepy or wary target has hardened
        # nothing — raiding into the window stays full price.
        state = war_state(target="vinnie")
        state.rivals["vinnie"].alertness = war.ALERT_PRESSURE_KNEE
        self.assertIs(war.job_damage(state, "vinnie", 12), 12)
        self.assertEqual(war.pressure(state, "vinnie").retaliation_mult,
                         1.0)

    def test_alert_targets_retaliate_harder(self):
        state = war_state(target="vinnie")
        calm = rival_policy(state, "vinnie")
        state.rivals["vinnie"].alertness = 6.0
        angry = rival_policy(state, "vinnie")
        self.assertGreater(angry.act_chance, calm.act_chance)
        self.assertTrue(any("learned the handwriting" in n
                            for n in angry.notes))

    def test_the_bystander_feels_no_pressure_policy(self):
        state = war_state(target="vinnie")
        state.rivals["sal"].alertness = 8.0
        self.assertEqual(war.pressure(state, "sal").impact_mult, 1.0)


class TestHeatCornersCoupling(unittest.TestCase):
    """Rev. 16 item 7: an amber turf has half the divertible custom —
    the EFFECTIVE corner cap halves with the same capacity multiplier
    that halves the stops, so the -4/night cap can no longer mask the
    burned neighborhood."""

    def test_amber_halves_the_effective_corner_cap(self):
        from extra_toppings import market
        state = war_state(target="vinnie")
        rm = market.route_market(state, "old_harbor")
        self.assertEqual(rm.corner_cap, war.CORNER_CAP)
        state.districts["old_harbor"].heat = 60.0
        rm = market.route_market(state, "old_harbor")
        self.assertEqual(rm.heat.band, "amber")
        self.assertEqual(rm.corner_cap,
                         war.CORNER_CAP * rm.heat.capacity_mult)
        self.assertLess(rm.corner_cap, war.CORNER_CAP)
        # The rate is untouched — the pool shrinks, not the price.
        self.assertEqual(rm.corner_rate, war.CORNER_RATE)


if __name__ == "__main__":
    unittest.main()
