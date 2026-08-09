"""P3 foundation (rev. 14): the campaign model, the rival-damage
authority, the relation authority, and their persistence contracts.

Everything here drives the real machinery: the authorities are the
functions the phases call, the payload probes go through
save.state_from_dict, and the flag-off identity assertions exercise
the exact call-site arithmetic the refactor replaced.
"""

import unittest

from extra_toppings import data, save
from extra_toppings.game import new_state
from extra_toppings.models import (BranchState, DamageRecord,
                                   WarCampaignState, apply_rival_damage,
                                   adjust_relation, live_campaign,
                                   set_relation, validate_branch_state,
                                   validate_cross_state, vendetta_locked,
                                   HEAT_DECAY, LEDGER_LEAN_STRENGTH,
                                   OVEN_BLEED, OVEN_BLEED_FLOOR,
                                   RAID_LEDGER_STRENGTH,
                                   RAID_SABOTAGE_STRENGTH,
                                   RAID_STOCK_STRENGTH, VENDETTA_RELATION,
                                   WAR_CHANNELS)


def war_state(target="vinnie", declared_day=14):
    """A real new_state seated in the war branch on `target`."""
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


class TestCanonicalConstants(unittest.TestCase):
    def test_job_prices_kept_their_pr3_values(self):
        self.assertEqual(RAID_STOCK_STRENGTH, 12)
        self.assertEqual(RAID_SABOTAGE_STRENGTH, 10)
        self.assertEqual(RAID_LEDGER_STRENGTH, 8)
        self.assertEqual(LEDGER_LEAN_STRENGTH, 15)
        self.assertEqual(OVEN_BLEED, 2)
        self.assertEqual(OVEN_BLEED_FLOOR, 1)
        self.assertEqual(HEAT_DECAY, 5)

    def test_the_vendetta_band_has_one_home(self):
        from extra_toppings import straight
        self.assertEqual(straight.FEUD_RELATION, VENDETTA_RELATION)
        self.assertEqual(VENDETTA_RELATION, -60.0)

    def test_the_channel_set_is_the_ruled_five(self):
        self.assertEqual(WAR_CHANNELS,
                         ("jobs", "corners", "ovens", "ledger", "defense"))


class TestDamageAuthorityFlagOff(unittest.TestCase):
    """Without a live campaign the authority IS the old call-site
    arithmetic — plain subtraction, or the caller's own floor."""

    def test_plain_subtraction_matches_the_old_arithmetic(self):
        state = new_state()
        before = state.rivals["vinnie"].strength
        applied = apply_rival_damage(state, "vinnie", "jobs",
                                     RAID_STOCK_STRENGTH)
        self.assertEqual(state.rivals["vinnie"].strength,
                         before - RAID_STOCK_STRENGTH)
        self.assertEqual(applied, RAID_STOCK_STRENGTH)

    def test_overkill_still_goes_negative_flag_off(self):
        state = new_state()
        state.rivals["sal"].strength = 5
        apply_rival_damage(state, "sal", "ledger", LEDGER_LEAN_STRENGTH)
        self.assertEqual(state.rivals["sal"].strength, 5 - 15)

    def test_the_oven_floor_binds_exactly_as_before(self):
        state = new_state()
        state.rivals["vinnie"].strength = 2
        apply_rival_damage(state, "vinnie", "ovens", OVEN_BLEED,
                           floor=OVEN_BLEED_FLOOR)
        self.assertEqual(state.rivals["vinnie"].strength, 1)
        # And int stays int: max(1, 2 - 2) is the old expression.
        self.assertIs(type(state.rivals["vinnie"].strength), int)

    def test_flag_off_records_nothing_anywhere(self):
        state = new_state()
        apply_rival_damage(state, "vinnie", "jobs", 12)
        self.assertIsNone(state.branch_state)

    def test_unknown_channels_are_a_programming_error(self):
        state = new_state()
        with self.assertRaises(ValueError):
            apply_rival_damage(state, "vinnie", "arson", 5)


class TestDamageAuthorityInBranch(unittest.TestCase):
    def test_damage_quantizes_and_appends_to_the_ledger(self):
        state = war_state()
        camp = live_campaign(state, "vinnie")
        before_h = round(state.rivals["vinnie"].strength * 100)
        applied = apply_rival_damage(state, "vinnie", "corners", 0.15 * 9)
        self.assertEqual(applied, 1.35)
        self.assertEqual(camp.damage[-1],
                         DamageRecord(day=state.day, channel="corners",
                                      hundredths=135))
        self.assertEqual(round(state.rivals["vinnie"].strength * 100),
                         before_h - 135)

    def test_overkill_is_cut_at_zero_and_capture_fires_once(self):
        state = war_state()
        rv = state.rivals["vinnie"]
        rv.strength = 5.0
        camp = live_campaign(state, "vinnie")
        camp.starting_hundredths = (
            500 + sum(r.hundredths for r in camp.damage))
        applied = apply_rival_damage(state, "vinnie", "jobs",
                                     RAID_STOCK_STRENGTH)
        self.assertEqual(applied, 5.0)          # not 12 — overkill excluded
        self.assertEqual(rv.strength, 0.0)
        self.assertEqual(camp.damage[-1].hundredths, 500)
        self.assertEqual(camp.broken_day, state.day)
        self.assertTrue(camp.salvage_available)
        self.assertTrue(camp.captured_pre_latch)
        # The campaign is no longer live; further damage takes the
        # flag-off path and books nothing.
        n = len(camp.damage)
        self.assertIsNone(live_campaign(state, "vinnie"))
        apply_rival_damage(state, "vinnie", "jobs", 3)
        self.assertEqual(len(camp.damage), n)

    def test_a_latched_run_captures_without_the_verdict_text_flag(self):
        state = war_state()
        rv = state.rivals["vinnie"]
        rv.strength = 1.0
        camp = live_campaign(state, "vinnie")
        camp.starting_hundredths = (
            100 + sum(r.hundredths for r in camp.damage))
        state.game_over = "arrested"            # the latch beat the victory
        apply_rival_damage(state, "vinnie", "corners", 2.0)
        self.assertEqual(camp.broken_day, state.day)
        self.assertFalse(camp.captured_pre_latch)

    def test_the_oven_floor_never_captures(self):
        state = war_state()
        rv = state.rivals["vinnie"]
        rv.strength = 1.5
        camp = live_campaign(state, "vinnie")
        camp.starting_hundredths = (
            150 + sum(r.hundredths for r in camp.damage))
        applied = apply_rival_damage(state, "vinnie", "ovens", OVEN_BLEED,
                                     floor=OVEN_BLEED_FLOOR)
        self.assertEqual(applied, 0.5)
        self.assertEqual(rv.strength, 1.0)
        self.assertIsNone(camp.broken_day)

    def test_bystander_damage_books_to_no_campaign(self):
        state = war_state(target="vinnie")
        camp = live_campaign(state)
        n = len(camp.damage)
        before = state.rivals["sal"].strength
        apply_rival_damage(state, "sal", "defense", 10)
        self.assertEqual(state.rivals["sal"].strength, before - 10)
        self.assertEqual(len(camp.damage), n)


class TestRelationAuthority(unittest.TestCase):
    def test_flag_off_is_the_exact_old_arithmetic(self):
        state = new_state()
        before = state.rivals["vinnie"].relation
        adjust_relation(state, "vinnie", -(9 * 0.4))
        self.assertEqual(state.rivals["vinnie"].relation, before - 9 * 0.4)

    def test_the_vendetta_lock_holds_on_every_write(self):
        state = war_state()
        self.assertTrue(vendetta_locked(state, "vinnie"))
        adjust_relation(state, "vinnie", +500)
        self.assertLessEqual(state.rivals["vinnie"].relation,
                             VENDETTA_RELATION)
        set_relation(state, "vinnie", 25)       # the truce's shape
        self.assertLessEqual(state.rivals["vinnie"].relation,
                             VENDETTA_RELATION)

    def test_the_bystander_is_not_locked(self):
        state = war_state(target="vinnie")
        self.assertFalse(vendetta_locked(state, "sal"))
        set_relation(state, "sal", 25)
        self.assertEqual(state.rivals["sal"].relation, 25)

    def test_a_broken_campaign_stays_locked(self):
        state = war_state()
        camp = live_campaign(state, "vinnie")
        rv = state.rivals["vinnie"]
        rv.strength = 1.0
        camp.starting_hundredths = (
            100 + sum(r.hundredths for r in camp.damage))
        apply_rival_damage(state, "vinnie", "jobs", 50)
        self.assertIsNotNone(camp.broken_day)
        self.assertTrue(vendetta_locked(state, "vinnie"))
        adjust_relation(state, "vinnie", +200)
        self.assertLessEqual(rv.relation, VENDETTA_RELATION)


class TestCampaignValidation(unittest.TestCase):
    def _bs(self, **kw):
        camp = WarCampaignState(rival_key="vinnie", declared_day=14,
                                starting_hundredths=7000, **kw)
        return BranchState(campaigns=[camp])

    def test_the_constructor_validates(self):
        validate_branch_state("war", BranchState.war(
            war_target="vinnie", declared_day=14, starting_strength=70))

    def test_an_empty_campaign_list_is_refused(self):
        with self.assertRaises(ValueError):
            validate_branch_state("war", BranchState())

    def test_unknown_rivals_and_channels_are_refused(self):
        bs = BranchState(campaigns=[WarCampaignState(
            rival_key="tony", declared_day=14, starting_hundredths=7000)])
        with self.assertRaises(ValueError):
            validate_branch_state("war", bs)
        bs = self._bs(damage=[DamageRecord(day=14, channel="arson",
                                           hundredths=100)])
        with self.assertRaises(ValueError):
            validate_branch_state("war", bs)

    def test_damage_must_be_positive_integer_hundredths(self):
        for bad in (0, -5, 1.5, True):
            bs = self._bs(damage=[DamageRecord(day=14, channel="jobs",
                                               hundredths=bad)])
            with self.assertRaises(ValueError):
                validate_branch_state("war", bs)

    def test_append_only_order_binds(self):
        bs = self._bs(damage=[
            DamageRecord(day=16, channel="jobs", hundredths=1200),
            DamageRecord(day=15, channel="corners", hundredths=135)])
        with self.assertRaises(ValueError):
            validate_branch_state("war", bs)

    def test_overkill_in_the_records_is_refused(self):
        bs = self._bs(damage=[DamageRecord(day=15, channel="jobs",
                                           hundredths=7100)])
        with self.assertRaises(ValueError):
            validate_branch_state("war", bs)

    def test_a_broken_campaign_must_reconcile_exactly(self):
        bs = self._bs(broken_day=20, damage=[
            DamageRecord(day=15, channel="jobs", hundredths=6000)])
        with self.assertRaises(ValueError):
            validate_branch_state("war", bs)

    def test_zero_strength_without_a_capture_is_refused(self):
        bs = self._bs(damage=[DamageRecord(day=15, channel="jobs",
                                           hundredths=7000)])
        with self.assertRaises(ValueError):
            validate_branch_state("war", bs)

    def test_capture_state_requires_a_capture(self):
        for kw in ({"salvage_available": True}, {"salvage_day": 20},
                   {"captured_pre_latch": True}):
            with self.assertRaises(ValueError):
                validate_branch_state("war", self._bs(**kw))

    def test_salvage_cannot_be_both_waiting_and_collected(self):
        bs = self._bs(broken_day=20, salvage_available=True, salvage_day=21,
                      damage=[DamageRecord(day=15, channel="jobs",
                                           hundredths=7000)])
        with self.assertRaises(ValueError):
            validate_branch_state("war", bs)

    def test_two_live_campaigns_are_refused(self):
        bs = BranchState(campaigns=[
            WarCampaignState(rival_key="vinnie", declared_day=14,
                             starting_hundredths=7000),
            WarCampaignState(rival_key="sal", declared_day=16,
                             starting_hundredths=6000)])
        with self.assertRaises(ValueError):
            validate_branch_state("war", bs)

    def test_the_second_front_waits_for_the_first_capture(self):
        first = WarCampaignState(
            rival_key="vinnie", declared_day=14, starting_hundredths=7000,
            broken_day=20,
            damage=[DamageRecord(day=15, channel="jobs", hundredths=7000)])
        early = WarCampaignState(rival_key="sal", declared_day=18,
                                 starting_hundredths=6000)
        with self.assertRaises(ValueError):
            validate_branch_state(
                "war", BranchState(campaigns=[first, early]))
        ok = WarCampaignState(rival_key="sal", declared_day=21,
                              starting_hundredths=6000)
        validate_branch_state("war", BranchState(campaigns=[first, ok]))

    def test_one_campaign_per_rival(self):
        first = WarCampaignState(
            rival_key="vinnie", declared_day=14, starting_hundredths=7000,
            broken_day=20,
            damage=[DamageRecord(day=15, channel="jobs", hundredths=7000)])
        again = WarCampaignState(rival_key="vinnie", declared_day=21,
                                 starting_hundredths=1000)
        with self.assertRaises(ValueError):
            validate_branch_state(
                "war", BranchState(campaigns=[first, again]))

    def test_branch_wide_fields_are_typed(self):
        state = war_state()
        for field, bad in (("war_pay_paid", -1),
                           ("war_pay_paid", 2.5),
                           ("war_pay_short_nights", -2),
                           ("insurance_paid_until", 0),
                           ("insurance_paid_until", 3.5)):
            bs = BranchState(campaigns=list(state.branch_state.campaigns))
            setattr(bs, field, bad)
            with self.assertRaises(ValueError):
                validate_branch_state("war", bs)


class TestWarPersistence(unittest.TestCase):
    def test_a_campaign_round_trips_exactly(self):
        from extra_toppings.models import (RaidAttemptRecord,
                                           RouteExecutionRecord)
        state = war_state()
        # The damage rides LEGAL execution records (rev. 20 item 2:
        # persistence reconciles the campaign ledger both ways).
        before = round(state.rivals["vinnie"].strength * 100)
        apply_rival_damage(state, "vinnie", "jobs", RAID_STOCK_STRENGTH)
        jobs_h = before - round(state.rivals["vinnie"].strength * 100)
        state.raid_log.append(RaidAttemptRecord(
            day=state.day, rival="vinnie", outcome="succeeded", crew=2,
            damage_h=jobs_h))
        corner = apply_rival_damage(state, "vinnie", "corners", 1.35)
        state.route_log.append(RouteExecutionRecord(
            day=state.day, district="old_harbor", heat_band="cool",
            capacity_mult=1.0, units_sold=9,
            corner_damage_h=round(corner * 100), contested=True))
        d = save.state_to_dict(state)
        restored = save.state_from_dict(d)
        self.assertEqual(restored.branch_state, state.branch_state)
        self.assertEqual(save.state_to_dict(restored), d)

    def _doctored(self, mutate, expect):
        """A negative-persistence probe that PROVES ITS BASELINE
        (rev. 20 final hold): the pristine payload — a LEGAL job
        history, raid record included — must round-trip clean first,
        so the later rejection is caused by the mutation under test
        and nothing else. The mutation lands on a separate copy."""
        import copy
        from extra_toppings.models import RaidAttemptRecord
        state = war_state()
        before = round(state.rivals["vinnie"].strength * 100)
        apply_rival_damage(state, "vinnie", "jobs", RAID_STOCK_STRENGTH)
        state.raid_log.append(RaidAttemptRecord(
            day=state.day, rival="vinnie", outcome="succeeded", crew=2,
            damage_h=before - round(state.rivals["vinnie"].strength
                                    * 100)))
        d = save.state_to_dict(state)
        restored = save.state_from_dict(copy.deepcopy(d))
        self.assertEqual(save.state_to_dict(restored), d)
        doctored = copy.deepcopy(d)
        mutate(doctored)
        with self.assertRaisesRegex(ValueError, expect):
            save.state_from_dict(doctored)

    def test_reconciliation_binds_at_the_persistence_boundary(self):
        # The world says one strength, the records say another.
        self._doctored(lambda d: d["rivals"]["vinnie"].__setitem__(
            "strength", 70), expect="does not reconcile")

    def test_the_vendetta_lock_binds_at_the_persistence_boundary(self):
        self._doctored(lambda d: d["rivals"]["vinnie"].__setitem__(
            "relation", 0), expect="vendetta band")

    def test_fractional_hundredths_are_refused(self):
        self._doctored(lambda d: d["branch_state"]["campaigns"][0]
                       ["damage"][0].__setitem__("hundredths", 120.5),
                       expect="integer number of hundredths")

    def test_unknown_campaign_fields_are_refused(self):
        self._doctored(lambda d: d["branch_state"]["campaigns"][0]
                       .__setitem__("morale", 9),
                       expect="malformed campaign payload")

    def test_a_dead_rival_needs_its_capture_recorded(self):
        def mutate(d):
            d["rivals"]["vinnie"]["strength"] = 0
        self._doctored(mutate, expect="does not reconcile")

    def test_war_fields_on_another_branch_are_refused(self):
        state = new_state()
        d = save.state_to_dict(state)
        d["branch"] = "straight"
        bs = BranchState.straight()
        payload = save.asdict(bs)
        payload["war_pay_paid"] = 40
        d["branch_state"] = payload
        d["act"] = 2
        with self.assertRaises(ValueError):
            save.state_from_dict(d)


class TestWorldStillWorks(unittest.TestCase):
    def test_data_rivals_agree_with_campaign_validation(self):
        for key in data.RIVALS:
            validate_branch_state("war", BranchState.war(
                war_target=key, declared_day=14, starting_strength=60))




class TestAccruedPersistence(unittest.TestCase):
    """Rev. 16 item 1 at the persistence boundary: 0 <= effective <=
    accrued binds at load, and an older payload without the field
    migrates to the stored magnitude — refused, never repaired."""

    def _war_with_evidence(self):
        state = war_state()
        state.add_case(10, "a pattern of night jobs", kind="pattern")
        return state

    def test_effective_above_accrued_is_refused(self):
        state = self._war_with_evidence()
        d = save.state_to_dict(state)
        d["evidence"][-1]["magnitude"] = \
            d["evidence"][-1]["accrued"] + 1.0
        with self.assertRaises(ValueError):
            save.state_from_dict(d)

    def test_a_negative_accrual_is_refused(self):
        state = self._war_with_evidence()
        d = save.state_to_dict(state)
        d["evidence"][-1]["magnitude"] = 0.0
        d["evidence"][-1]["accrued"] = -1.0
        with self.assertRaises(ValueError):
            save.state_from_dict(d)

    def test_an_older_payload_without_accrued_migrates(self):
        state = self._war_with_evidence()
        d = save.state_to_dict(state)
        for e in d["evidence"]:
            e.pop("accrued")
        restored = save.state_from_dict(d)
        self.assertTrue(all(r.accrued == r.magnitude
                            for r in restored.evidence))


if __name__ == "__main__":
    unittest.main()
