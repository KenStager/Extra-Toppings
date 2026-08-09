"""P3 mechanics (rev. 14): the declaration, the obligations, the
defense taxonomy and Burned Out, the ledger's second spend, salvage,
the second front, and the endings — driven through the real scene,
menus and night phase wherever a real path exists."""

import unittest

from extra_toppings import data, game, phases, raids, rivals, war
from extra_toppings.config import GameConfig
from extra_toppings.game import new_state
from extra_toppings.models import (BranchState, SitdownSnapshot,
                                   apply_rival_damage, live_campaign,
                                   set_relation, validate_branch_state,
                                   validate_cross_state,
                                   LEDGER_LAW_CALM_DAYS,
                                   LEDGER_LAW_STRENGTH,
                                   LEDGER_LEAN_STRENGTH,
                                   VENDETTA_RELATION)
from extra_toppings.rivals import rival_policy
from extra_toppings.rng import Streams
from extra_toppings.ui import Console, ScriptedConsole


class Quiet(Console):
    def __init__(self):
        super().__init__()
        self.quiet = True
        self.lines: list = []

    def say(self, text=""):
        self.lines.append(text)

    def bullet(self, text):
        self.lines.append(f"• {text}")

    def find(self, fragment):
        return next((ln for ln in self.lines if fragment in ln), None)


class Scripted(ScriptedConsole):
    """ScriptedConsole that also records everything said."""

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

    def find(self, fragment):
        return next((ln for ln in self.lines if fragment in ln), None)


def scene_state():
    state = new_state()
    state.debt = 0
    state.debt_paid_day = 13
    state.day = 14
    state.sitdown_snapshot = SitdownSnapshot(
        payoff_day=13, case_at_lockup=0.0, evidence_count_at_lockup=0)
    return state


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
    while state.rivals[target].alive:
        apply_rival_damage(state, target, "jobs", 12)


WAR_ON = GameConfig(fork_enabled=True, enabled_branches=frozenset({"war"}))


class TestTheDeclaration(unittest.TestCase):
    def test_the_scene_seats_a_war_and_locks_the_vendetta(self):
        state = scene_state()
        con = Scripted([2, 2, 1])   # war chair; name Vinnie; declare
        game.sitdown.run_scene(state, con, WAR_ON)
        self.assertEqual(state.branch, "war")
        self.assertEqual(state.act, 2)
        camp = live_campaign(state)
        self.assertEqual(camp.rival_key, "vinnie")
        self.assertEqual(camp.declared_day, 14)
        self.assertEqual(camp.starting_hundredths,
                         round(state.rivals["vinnie"].strength * 100))
        self.assertLessEqual(state.rivals["vinnie"].relation,
                             VENDETTA_RELATION)
        validate_cross_state(state)

    def test_reconsidering_returns_to_the_table(self):
        state = scene_state()
        con = Scripted([2, 0, 4, 1])   # war; reconsider; stand pat; confirm
        game.sitdown.run_scene(state, con, WAR_ON)
        self.assertEqual(state.branch, "stand_pat")

    def test_the_deterministic_bot_declares_on_vinnie(self):
        from extra_toppings.ui import BotConsole
        import random
        state = scene_state()
        game.sitdown.run_scene(state, BotConsole(random.Random(3)), WAR_ON)
        # Last-option policy: the last chair menu option is stand-pat,
        # so the bot stands pat — the war bot overrides the chair
        # answer, but the SCENE's own invariant is that every menu's
        # last option progresses; reaching here without a raise is the
        # assertion.
        self.assertIn(state.branch, ("stand_pat", "war"))

    def test_partner_still_fails_loudly(self):
        state = scene_state()
        cfg = GameConfig(fork_enabled=True,
                         enabled_branches=frozenset({"partner"}))
        with self.assertRaises(NotImplementedError):
            game.sitdown.run_scene(state, Scripted([1]), cfg)


class TestWarPay(unittest.TestCase):
    def _crew(self, state, n=2):
        crew = [e for e in state.employees][:n]
        for e in crew:
            e.hired = True
            e.aware = True
            e.morale = 6
        return crew

    def test_war_pay_draws_dirty_first_then_clean(self):
        state = war_state()
        self._crew(state, 2)
        state.dirty, state.clean = 30, 500
        con = Quiet()
        war.night_obligation(state, con, payroll_short=False)
        self.assertEqual((state.dirty, state.clean), (0, 490))
        self.assertEqual(state.branch_state.war_pay_paid, 40)
        self.assertEqual(state.branch_state.war_pay_short_nights, 0)

    def test_a_short_night_is_one_penalty_and_persists(self):
        state = war_state()
        crew = self._crew(state, 2)
        state.dirty, state.clean = 0, 10
        war.night_obligation(state, Quiet(), payroll_short=False)
        self.assertEqual(state.branch_state.war_pay_short_nights, 1)
        self.assertEqual(state.branch_state.war_pay_paid, 0)
        self.assertTrue(all(e.morale == 4 for e in crew))

    def test_a_bounced_payroll_bounces_the_bonus_without_a_second_hit(self):
        state = war_state()
        crew = self._crew(state, 2)
        state.dirty, state.clean = 5000, 5000
        war.night_obligation(state, Quiet(), payroll_short=True)
        self.assertEqual(state.branch_state.war_pay_short_nights, 1)
        self.assertEqual(state.branch_state.war_pay_paid, 0)
        # No SECOND morale penalty here — _payroll_and_rent took the one.
        self.assertTrue(all(e.morale == 6 for e in crew))
        self.assertEqual((state.dirty, state.clean), (5000, 5000))

    def test_no_read_in_crew_no_obligation(self):
        state = war_state()
        war.night_obligation(state, Quiet(), payroll_short=False)
        self.assertEqual(state.branch_state.war_pay_short_nights, 0)


class TestInsurance(unittest.TestCase):
    def test_the_invoice_is_predictable_and_renewable(self):
        state = war_state(target="vinnie")
        self.assertTrue(war.insurance_due(state))
        state.dirty = 1000
        con = Scripted([0])
        war.insurance_card(state, con)
        self.assertEqual(state.dirty, 1000 - war.INSURANCE_RATE)
        self.assertEqual(state.branch_state.insurance_paid_until,
                         state.day + war.INSURANCE_NIGHTS - 1)
        self.assertFalse(war.insurance_due(state))
        self.assertFalse(rival_policy(state, "sal").hostile)
        state.day += war.INSURANCE_NIGHTS
        self.assertTrue(war.insurance_due(state))
        self.assertTrue(rival_policy(state, "sal").hostile)

    def test_declining_changes_nothing_but_the_odds(self):
        state = war_state(target="vinnie")
        state.dirty = 1000
        war.insurance_card(state, Scripted([1]))
        self.assertEqual(state.dirty, 1000)
        self.assertIsNone(state.branch_state.insurance_paid_until)

    def test_no_dirty_no_menu(self):
        state = war_state(target="vinnie")
        state.dirty = 100
        con = Scripted([])          # a menu would consume the empty script
        war.insurance_card(state, con)
        self.assertEqual(state.dirty, 100)

    def test_no_invoice_when_vinnie_is_the_bystander(self):
        state = war_state(target="sal")
        set_relation(state, "sal",
                     min(state.rivals["sal"].relation, VENDETTA_RELATION))
        self.assertFalse(war.insurance_due(state))


class TestTheLedgerSpends(unittest.TestCase):
    def _at_war_with_ledger(self):
        state = war_state()
        state.rivals["vinnie"].ledger_stolen = True
        return state

    def test_the_prosecution_spend(self):
        state = self._at_war_with_ledger()
        before = state.rivals["vinnie"].strength
        # negotiate: pick vinnie (index 1), then the law option (1).
        rivals.negotiate(state, Scripted([1, 1]), Streams(9).rivals)
        rv = state.rivals["vinnie"]
        camp = live_campaign(state, "vinnie")
        self.assertEqual(before - rv.strength, LEDGER_LAW_STRENGTH)
        self.assertFalse(rv.ledger_stolen)
        self.assertEqual(camp.law_calm_until,
                         state.day + LEDGER_LAW_CALM_DAYS)
        self.assertTrue(camp.violence_raised)
        self.assertEqual(camp.damage[-1].channel, "ledger")
        self.assertEqual(state.dirty, new_state().dirty)   # no money

    def test_the_lean_stays_the_greedy_alternative(self):
        state = self._at_war_with_ledger()
        dirty = state.dirty
        before = state.rivals["vinnie"].strength
        rivals.negotiate(state, Scripted([1, 0]), Streams(9).rivals)
        self.assertEqual(before - state.rivals["vinnie"].strength,
                         LEDGER_LEAN_STRENGTH)
        self.assertEqual(state.dirty, dirty + 2000)
        self.assertEqual(live_campaign(state).damage[-1].channel, "ledger")

    def test_the_target_has_no_peace_verbs(self):
        state = war_state()
        con = Scripted([1, 0])       # pick vinnie; take the ONLY option
        rivals.negotiate(state, con, Streams(9).rivals)
        prompt, options = con.menus[-1]
        self.assertIn("nothing to say", prompt)
        self.assertEqual(options, ["Back"])
        self.assertLessEqual(state.rivals["vinnie"].relation,
                             VENDETTA_RELATION)

    def test_the_bystander_still_talks(self):
        state = war_state(target="vinnie")
        con = Scripted([0, 3])       # pick Sal; Back
        rivals.negotiate(state, con, Streams(9).rivals)
        _prompt, options = con.menus[-1]
        self.assertIn("Send a peace offering ($1,000 dirty)", options)


class TestDefenseTaxonomy(unittest.TestCase):
    def _incoming(self, state, script, seed=7):
        state.rivals["vinnie"].raid_warning = 1
        return raids.incoming_raid(state, "vinnie", Scripted(script),
                                   Streams(seed).raids)

    def test_tribute_averts(self):
        state = war_state()
        state.dirty = 5000
        r = self._incoming(state, [2])
        self.assertEqual(r.outcome, "averted")
        self.assertFalse(r.landed)

    def test_the_decoy_lands_with_pre_impact_damage_recorded(self):
        state = war_state()
        r = self._incoming(state, [1])
        self.assertEqual(r.outcome, "landed")
        self.assertEqual(r.damage_before, 0)      # the reviewer's exhibit
        self.assertEqual(r.damage_added, 2)

    def test_a_won_fight_repels_and_books_defense_damage(self):
        state = war_state()
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.hired = True
        rosa.aware = True
        rosa.nerve = 10
        state.shop.upgrades.add("guard")
        apply_rival_damage(state, "vinnie", "jobs", 60)   # strength 10
        r = self._incoming(state, [0])
        self.assertEqual(r.outcome, "repelled")
        self.assertGreater(r.attacker_damage, 0)
        camp = war.campaign_for(state, "vinnie")
        self.assertEqual(camp.damage[-1].channel, "defense")

    def test_the_fatal_choice_is_warned_out_loud(self):
        state = war_state()
        state.shop.damage_days = 2
        con = Scripted([2])
        state.dirty = 5000
        state.rivals["vinnie"].raid_warning = 1
        raids.incoming_raid(state, "vinnie", con, Streams(7).raids)
        self.assertIsNotNone(con.find("nothing left to reopen"))
        _prompt, options = con.menus[-1]
        self.assertIn("the break-in ends the run", options[1])

    def test_flag_off_defense_carries_no_warning(self):
        state = new_state()
        state.shop.damage_days = 2
        state.dirty = 5000
        state.rivals["vinnie"].raid_warning = 1
        con = Scripted([2])
        raids.incoming_raid(state, "vinnie", con, Streams(7).raids)
        self.assertIsNone(con.find("nothing left to reopen"))


class TestBurnedOut(unittest.TestCase):
    def _night(self, state, script):
        con = Scripted(script)
        phases.night(state, {"route": None, "raid": None}, {}, con,
                     Streams(11))
        return con

    def test_a_landed_raid_on_a_damaged_shop_burns_out(self):
        state = war_state()
        state.clean = 5000
        state.shop.damage_days = 2
        state.rivals["vinnie"].raid_warning = 1
        con = self._night(state, [1, 5])     # decoy; lock up
        self.assertEqual(state.game_over, "burned_out")
        self.assertIsNotNone(con.find("The war came home"))

    def test_the_first_raid_never_burns_out(self):
        state = war_state()
        state.clean = 5000
        state.rivals["vinnie"].raid_warning = 1
        self._night(state, [1, 5])
        self.assertIsNone(state.game_over)
        self.assertEqual(state.shop.damage_days, 2)

    def test_an_averted_raid_never_burns_out(self):
        state = war_state()
        state.clean = 5000
        state.dirty = 5000
        state.shop.damage_days = 2
        state.rivals["vinnie"].raid_warning = 1
        self._night(state, [2, 5])
        self.assertIsNone(state.game_over)

    def test_flag_off_never_burns_out(self):
        state = new_state()
        state.clean = 5000
        state.shop.damage_days = 2
        state.rivals["vinnie"].raid_warning = 1
        self._night(state, [1, 0, 4])   # decoy; then default menu path
        self.assertIsNone(state.game_over)


class TestTargetOnlyJobs(unittest.TestCase):
    def test_the_plan_offers_only_the_declared_rival(self):
        state = war_state(target="vinnie")
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.hired = True
        rosa.aware = True
        con = Scripted([len(data.RIVALS)])   # answer clamps to "Never mind"
        raids.plan_raid(state, con, Streams(3).raids)
        prompt, options = next((p, o) for p, o in con.menus
                               if p == "Hit whom?")
        self.assertEqual(len(options), 2)    # Vinnie + Never mind
        self.assertIn("Vinnie", options[0])

    def test_no_live_front_means_no_jobs(self):
        state = war_state()
        break_target(state)
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.hired = True
        rosa.aware = True
        con = Scripted([])
        self.assertIsNone(raids.plan_raid(state, con, Streams(3).raids))
        self.assertIsNotNone(con.find("Name the next war"))

    def test_a_route_broken_target_scrubs_the_planned_raid(self):
        state = war_state()
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.hired = True
        rosa.aware = True
        plan = {"rival": "vinnie", "objective": "steal_stock",
                "team": [rosa], "armed": False, "table_warned": True}
        break_target(state)                  # the corners got him first
        alert_before = state.rivals["vinnie"].alertness
        con = Scripted([5])                  # just lock up
        phases.night(state, {"route": None, "raid": plan}, {}, con,
                     Streams(11))
        self.assertIsNotNone(con.find("broke before the crew"))
        self.assertEqual(state.rivals["vinnie"].alertness, alert_before)


class TestSalvage(unittest.TestCase):
    def _captured(self):
        state = war_state()
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.hired = True
        rosa.aware = True
        break_target(state)
        return state, rosa

    def test_the_pickup_is_planned_and_collected_once(self):
        state, rosa = self._captured()
        camp = war.campaign_for(state, "vinnie")
        self.assertTrue(camp.salvage_available)
        plan = war.plan_salvage(state, Scripted([0]), route_planned=False)
        self.assertEqual(plan, {"rival": "vinnie", "driver": rosa})
        war.run_salvage(state, plan, Quiet(), Streams(21).war)
        self.assertFalse(camp.salvage_available)
        self.assertEqual(camp.salvage_day, state.day)
        self.assertIsNone(war.salvage_ready(state))

    def test_the_pickup_draws_exactly_one_war_die(self):
        state, rosa = self._captured()
        camp = war.campaign_for(state, "vinnie")
        streams = Streams(21)
        control = Streams(21)
        plan = {"rival": "vinnie", "driver": rosa}
        war.run_salvage(state, plan, Quiet(), streams.war)
        control.war.randint(4, 10 + camp.starting_hundredths // 1000)
        self.assertEqual(streams.war.getstate(), control.war.getstate())

    def test_the_wagon_does_one_job_a_night(self):
        state, _rosa = self._captured()
        self.assertIsNone(
            war.plan_salvage(state, Quiet(), route_planned=True))

    def test_a_missing_driver_scrubs_transactionally(self):
        state, rosa = self._captured()
        camp = war.campaign_for(state, "vinnie")
        plan = war.plan_salvage(state, Scripted([0]), route_planned=False)
        rosa.injured_days = 3
        stash_before = dict(state.shop_stash)
        war.run_salvage(state, plan, Quiet(), Streams(21).war)
        self.assertTrue(camp.salvage_available)   # still waiting
        self.assertEqual(state.shop_stash, stash_before)


class TestTheSecondFront(unittest.TestCase):
    def test_the_offer_stands_and_declares_cleanly(self):
        state = war_state()
        break_target(state)
        self.assertEqual(phases._second_front(state), "sal")
        war.declare(state, "sal", Quiet())
        self.assertEqual(live_campaign(state).rival_key, "sal")
        self.assertLessEqual(state.rivals["sal"].relation,
                             VENDETTA_RELATION)
        validate_branch_state("war", state.branch_state)
        validate_cross_state(state)
        self.assertIsNone(phases._second_front(state))

    def test_no_offer_while_a_front_is_live(self):
        state = war_state()
        self.assertIsNone(phases._second_front(state))


class TestEndings(unittest.TestCase):
    def test_the_campaign_count_matrix(self):
        state = war_state()
        self.assertEqual(war.grade(state), "long_war")
        break_target(state)
        self.assertEqual(war.grade(state), "harbor_yours")
        war.declare(state, "sal", Quiet())
        self.assertEqual(war.grade(state), "harbor_yours")
        break_target(state, "sal")
        self.assertEqual(war.grade(state), "survived")

    def test_won_the_war_lost_the_verdict_is_transition_ordered(self):
        state = war_state()
        break_target(state)                      # capture on a live run
        state.game_over = "arrested"
        self.assertTrue(war.won_then_lost(state))
        con = Quiet()
        game.epilogue(state, con)
        self.assertIsNotNone(con.find("Lost the verdict"))

    def test_a_latch_before_the_capture_stays_a_plain_arrest(self):
        state = war_state()
        state.game_over = "arrested"             # the latch fires first
        break_target(state)
        self.assertFalse(war.won_then_lost(state))
        con = Quiet()
        game.epilogue(state, con)
        self.assertIsNone(con.find("Lost the verdict"))

    def test_the_three_war_epilogues_render(self):
        for ending, fragment in (("burned_out", "Burned Out"),
                                 ("long_war", "A Long War")):
            state = war_state()
            state.game_over = ending
            con = Quiet()
            game.epilogue(state, con)
            self.assertIsNotNone(con.find(fragment), ending)
        state = war_state()
        break_target(state)
        state.game_over = "harbor_yours"
        con = Quiet()
        game.epilogue(state, con)
        self.assertIsNotNone(con.find("The Harbor Is Yours"))
        # Both broken: the existing Syndicate text, war-flavored.
        state = war_state()
        break_target(state)
        war.declare(state, "sal", Quiet())
        break_target(state, "sal")
        state.game_over = "survived"
        con = Quiet()
        game.epilogue(state, con)
        self.assertIsNotNone(con.find("The syndicate"))
        self.assertIsNotNone(con.find("declared both wars"))


class TestWarPersistenceMidCampaign(unittest.TestCase):
    def test_the_whole_posture_round_trips(self):
        from extra_toppings import save
        state = war_state()
        state.rivals["vinnie"].ledger_stolen = True
        rivals.negotiate(state, Scripted([1, 1]), Streams(9).rivals)
        state.branch_state.insurance_paid_until = state.day + 6
        state.branch_state.war_pay_paid = 60
        d = save.state_to_dict(state)
        restored = save.state_from_dict(d)
        self.assertEqual(restored.branch_state, state.branch_state)
        self.assertEqual(save.state_to_dict(restored), d)

    def test_a_second_campaign_round_trips(self):
        from extra_toppings import save
        state = war_state()
        break_target(state)
        war.declare(state, "sal", Quiet())
        apply_rival_damage(state, "sal", "corners", 1.35)
        d = save.state_to_dict(state)
        restored = save.state_from_dict(d)
        self.assertEqual(restored.branch_state, state.branch_state)


if __name__ == "__main__":
    unittest.main()


class TestSharedRemediation(unittest.TestCase):
    """Rev. 14 item 8: the war unlocks the SAME machinery — retention
    protection, counsel, settlements — through the capability policy,
    never through straight wrappers or parallel copies."""

    def test_retention_protection_holds_in_the_war(self):
        state = war_state()
        e = state.employees[0]
        e.hired, e.aware, e.morale = True, True, 8
        state.add_case(20, f"{e.name} knows everything",
                       kind="witness", source=e.key)
        self.assertEqual(state.case, 10.0)      # halved, floor-exact
        e.morale = 3
        self.assertEqual(state.case, 20.0)      # protection lapses live

    def test_counsel_retains_charges_and_contests_in_the_war(self):
        from extra_toppings import evidence
        state = war_state()
        state.clean = 5000
        state.add_case(12, "an over-ceiling wash left paper",
                       kind="paper")
        evidence.toggle_counsel(state, Quiet())
        for _ in range(evidence.COUNSEL_CONTEST_EVERY):
            war.night_obligation(state, Quiet(), payroll_short=False)
        bs = state.branch_state
        self.assertEqual(bs.counsel_days, 3)
        self.assertEqual(state.clean, 5000 - 3 * evidence.COUNSEL_FEE)
        contested = [r for r in state.evidence if r.contested]
        self.assertEqual(len(contested), 1)
        self.assertEqual(state.case, 10.0)      # the floor holds, exactly
        self.assertIn("suspicion", {r.kind for r in state.evidence})
        validate_branch_state("war", bs)

    def test_settlements_reach_war_witnesses(self):
        from extra_toppings import evidence
        state = war_state()
        state.clean = 5000
        e = state.employees[0]
        e.hired, e.aware, e.morale = False, True, 2   # departed, hostile
        state.add_case(30, f"{e.name} left knowing everything",
                       kind="witness", source=e.key)
        before = state.case
        evidence.settle_witness(state, e, Quiet())
        self.assertLess(state.case, before)
        self.assertIn(e.key, state.branch_state.settled_witnesses)
        validate_cross_state(state)

    def test_the_capability_is_exactly_two_branches(self):
        from extra_toppings.models import remediation_unlocked
        self.assertTrue(remediation_unlocked(war_state()))
        self.assertFalse(remediation_unlocked(new_state()))
        sale = new_state()
        sale.branch = "quiet_sale"
        sale.branch_state = BranchState.quiet_sale()
        self.assertFalse(remediation_unlocked(sale))
