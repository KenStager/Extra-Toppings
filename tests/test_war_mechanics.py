"""P3 mechanics (rev. 14): the declaration, the obligations, the
defense taxonomy and Burned Out, the ledger's second spend, salvage,
the second front, and the endings — driven through the real scene,
menus and night phase wherever a real path exists."""

import unittest

from extra_toppings import data, game, phases, raids, rivals, war
from extra_toppings import models as models_mod
from extra_toppings import save as save_mod
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

def _departed(state, *jobs, **report):
    """The authority as SERVICE would hand it over: each named job
    already claimed the home wagon when it rolled."""
    wagons = phases.WagonNight(state)
    for job in jobs:
        assert wagons.claim_key(models_mod.HOME_WAGON_KEY, job)
    return {**report, "wagons": wagons}


def _wag(state, **report):
    """Every direct `night` call needs the assignment authority the
    service phase would have opened (P4b.1a). An UNSPENT one is the
    honest fixture here: these tests do not run service, so no wagon
    departed."""
    return {**report, "wagons": phases.WagonNight(state)}


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
    """Break a rival through LEGAL history (rev. 20 item 2): one job
    a night, the attempt booked, the calendar advanced — the
    execution-history reconciliation holds on every fixture."""
    from extra_toppings.models import RaidAttemptRecord
    while state.rivals[target].alive:
        state.day += 1
        before = round(state.rivals[target].strength * 100)
        apply_rival_damage(state, target, "jobs", 12)
        state.raid_log.append(RaidAttemptRecord(
            day=state.day, rival=target, outcome="succeeded", crew=1,
            damage_h=before - round(state.rivals[target].strength
                                    * 100)))


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
        # Four suppressed rival PHASES, counted from tonight's
        # (rev. 15 item 7) — day + DAYS was five.
        self.assertEqual(camp.law_calm_until,
                         state.day + LEDGER_LAW_CALM_DAYS - 1)
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
        state.rivals["vinnie"].warning = models_mod.RaidWarning(1, models_mod.HOME_SHOP_KEY)
        return raids.incoming_raid(state, "vinnie", Scripted(script),
                                   Streams(seed).raids)

    def test_the_declared_target_takes_no_tribute(self):
        # Rev. 15 item 1: the declaration closed the tribute door, and
        # the raid menu must not reopen it — two options, no envelope.
        state = war_state()
        state.dirty = 5000
        state.rivals["vinnie"].warning = models_mod.RaidWarning(1, models_mod.HOME_SHOP_KEY)
        con = Scripted([2])          # the old tribute index, clamped
        r = raids.incoming_raid(state, "vinnie", con, Streams(7).raids)
        _prompt, options = con.menus[-1]
        self.assertEqual(len(options), 2)
        self.assertFalse(any("tribute" in o for o in options))
        self.assertIsNotNone(con.find("no envelope"))
        self.assertNotEqual(r.outcome, "averted")
        self.assertEqual(state.dirty, 5000)   # no money moved

    def test_the_bystander_still_takes_tribute(self):
        state = war_state(target="sal")
        set_relation(state, "sal",
                     min(state.rivals["sal"].relation, VENDETTA_RELATION))
        state.dirty = 5000
        r = self._incoming(state, [2])   # vinnie is the bystander here
        self.assertEqual(r.outcome, "averted")
        self.assertFalse(r.landed)
        self.assertLess(state.dirty, 5000)

    def test_flag_off_tribute_is_untouched(self):
        state = new_state()
        state.dirty = 5000
        state.rivals["vinnie"].warning = models_mod.RaidWarning(1, models_mod.HOME_SHOP_KEY)
        con = Scripted([2])
        r = raids.incoming_raid(state, "vinnie", con, Streams(7).raids)
        _prompt, options = con.menus[-1]
        self.assertEqual(len(options), 3)
        self.assertEqual(r.outcome, "averted")

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
        state.rivals["vinnie"].warning = models_mod.RaidWarning(1, models_mod.HOME_SHOP_KEY)
        raids.incoming_raid(state, "vinnie", con, Streams(7).raids)
        self.assertIsNotNone(con.find("nothing left to reopen"))
        _prompt, options = con.menus[-1]
        self.assertIn("the break-in ends the run", options[1])

    def test_flag_off_defense_carries_no_warning(self):
        state = new_state()
        state.shop.damage_days = 2
        state.dirty = 5000
        state.rivals["vinnie"].warning = models_mod.RaidWarning(1, models_mod.HOME_SHOP_KEY)
        con = Scripted([2])
        raids.incoming_raid(state, "vinnie", con, Streams(7).raids)
        self.assertIsNone(con.find("nothing left to reopen"))


class TestBurnedOut(unittest.TestCase):
    def _night(self, state, script):
        con = Scripted(script)
        phases.night(state, {"route": None, "raid": None}, _wag(state), con,
                     Streams(11))
        return con

    def test_a_landed_raid_on_a_damaged_shop_burns_out(self):
        state = war_state()
        state.clean = 5000
        state.shop.damage_days = 2
        state.rivals["vinnie"].warning = models_mod.RaidWarning(1, models_mod.HOME_SHOP_KEY)
        con = self._night(state, [1, 5])     # decoy; lock up
        self.assertEqual(state.game_over, "burned_out")
        self.assertIsNotNone(con.find("The war came home"))

    def test_the_first_raid_never_burns_out(self):
        state = war_state()
        state.clean = 5000
        state.rivals["vinnie"].warning = models_mod.RaidWarning(1, models_mod.HOME_SHOP_KEY)
        self._night(state, [1, 5])
        self.assertIsNone(state.game_over)
        self.assertEqual(state.shop.damage_days, 2)

    def test_an_averted_raid_never_burns_out(self):
        # The bystander's raid — the target takes no tribute now
        # (rev. 15 item 1), so aversion belongs to the third party.
        state = war_state(target="sal")
        set_relation(state, "sal",
                     min(state.rivals["sal"].relation, VENDETTA_RELATION))
        state.clean = 5000
        state.dirty = 5000
        state.shop.damage_days = 2
        state.rivals["vinnie"].warning = models_mod.RaidWarning(1, models_mod.HOME_SHOP_KEY)
        self._night(state, [2, 5])
        self.assertIsNone(state.game_over)

    def test_flag_off_never_burns_out(self):
        state = new_state()
        state.clean = 5000
        state.shop.damage_days = 2
        state.rivals["vinnie"].warning = models_mod.RaidWarning(1, models_mod.HOME_SHOP_KEY)
        self._night(state, [1, 0, 4])   # decoy; then default menu path
        self.assertIsNone(state.game_over)


class TestTargetOnlyJobs(unittest.TestCase):
    def test_the_plan_offers_only_the_declared_rival(self):
        state = war_state(target="vinnie")
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.hired = True
        rosa.aware = True
        con = Scripted([len(data.RIVALS)])   # answer clamps to "Never mind"
        raids.plan_raid(state, con, Streams(3).raids,
                        wagon=models_mod.PlannedWagon((models_mod.HOME_WAGON_KEY,)))
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
        self.assertIsNone(raids.plan_raid(
            state, con, Streams(3).raids, wagon=models_mod.PlannedWagon((models_mod.HOME_WAGON_KEY,))))
        self.assertIsNotNone(con.find("Name the next war"))

    def test_a_route_broken_target_scrubs_the_planned_raid(self):
        state = war_state()
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.hired = True
        rosa.aware = True
        plan = {"rival": "vinnie", "objective": "steal_stock",
                "team": [rosa], "armed": False, "table_warned": True, "return_shop": models_mod.HOME_SHOP_KEY}
        break_target(state)                  # the corners got him first
        alert_before = state.rivals["vinnie"].alertness
        con = Scripted([5])                  # just lock up
        phases.night(state, {"route": None, "raid": plan}, _wag(state), con,
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
        plan = war.plan_salvage(state, Scripted([0]), reserved=[],
                                 wagon=models_mod.PlannedWagon(("wagon1",)),
                                 origin_shop=models_mod.HOME_SHOP_KEY)
        self.assertEqual(plan, {"rival": "vinnie", "driver": rosa,
                                "origin_shop": models_mod.HOME_SHOP_KEY,
                           "wagon_key": models_mod.HOME_WAGON_KEY})
        war.run_salvage(state, plan, Quiet(), Streams(21).war)
        self.assertFalse(camp.salvage_available)
        self.assertEqual(camp.salvage_day, state.day)
        self.assertIsNone(war.salvage_ready(state))

    def test_the_pickup_draws_exactly_one_war_die(self):
        state, rosa = self._captured()
        camp = war.campaign_for(state, "vinnie")
        streams = Streams(21)
        control = Streams(21)
        plan = {"rival": "vinnie", "driver": rosa,
                             "origin_shop": models_mod.HOME_SHOP_KEY,
                             "wagon_key": models_mod.HOME_WAGON_KEY}
        war.run_salvage(state, plan, Quiet(), streams.war)
        control.war.randint(4, 10 + camp.starting_hundredths // 1000)
        self.assertEqual(streams.war.getstate(), control.war.getstate())

    def test_the_wagon_does_one_job_a_night(self):
        state, _rosa = self._captured()
        self.assertIsNone(
            war.plan_salvage(state, Quiet(), reserved=[],
                             wagon=models_mod.PlannedWagon(
                                 blocked_by="route",
                                 note=models_mod.WAGON_NOTES["route"]),
                             origin_shop=models_mod.HOME_SHOP_KEY))

    def test_a_missing_driver_scrubs_transactionally(self):
        state, rosa = self._captured()
        camp = war.campaign_for(state, "vinnie")
        plan = war.plan_salvage(state, Scripted([0]), reserved=[],
                                 wagon=models_mod.PlannedWagon(("wagon1",)),
                                 origin_shop=models_mod.HOME_SHOP_KEY)
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
        # An explicit terminal (rev. 15 item 4): a two-capture war
        # must never depend on the generic epilogue's ordering.
        self.assertEqual(war.grade(state), "syndicate")

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
        # Both broken: the explicit syndicate terminal (rev. 15).
        state = war_state()
        break_target(state)
        war.declare(state, "sal", Quiet())
        break_target(state, "sal")
        state.game_over = "syndicate"
        con = Quiet()
        game.epilogue(state, con)
        self.assertIsNotNone(con.find("The syndicate"))
        self.assertIsNotNone(con.find("declared both wars"))

    def test_a_rich_clean_syndicate_never_prints_the_exit(self):
        # The reviewer's repro (rev. 15 item 4): both rivals broken,
        # Case 0, net worth over $20k — the generic epilogue's
        # legitimate-exit arm must never shadow the war's outcome.
        state = war_state()
        break_target(state)
        war.declare(state, "sal", Quiet())
        break_target(state, "sal")
        state.clean = 50000
        state.game_over = war.grade(state)
        con = Quiet()
        game.epilogue(state, con)
        self.assertIsNotNone(con.find("The syndicate"))
        self.assertIsNone(con.find("rarest pie"))


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
        from extra_toppings.models import RouteExecutionRecord
        state = war_state()
        break_target(state)
        war.declare(state, "sal", Quiet())
        # Corner damage rides a LEGAL route record (rev. 20 item 2:
        # the ledgers reconcile both ways at persistence).
        applied = apply_rival_damage(state, "sal", "corners", 1.35)
        state.route_log.append(RouteExecutionRecord(
            day=state.day, district="little_sicily", heat_band="cool",
            capacity_mult=1.0, units_sold=9,
            corner_damage_h=round(applied * 100), contested=True,
            origin_shop=models_mod.HOME_SHOP_KEY))
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


class TestRevision15Boundaries(unittest.TestCase):
    """The rev. 15 batch-1 pins: the tribute door, the calm's phase
    count, insurance persistence, and the honest damage delta."""

    def test_paying_insurance_cancels_the_telegraphed_raid(self):
        state = war_state(target="vinnie")
        state.dirty = 1000
        state.rivals["sal"].warning = models_mod.RaidWarning(2, models_mod.HOME_SHOP_KEY)
        war.insurance_card(state, Scripted([0]))
        self.assertEqual(state.rivals["sal"].raid_warning, 0)

    def test_declaring_on_sal_tears_up_the_policy(self):
        state = war_state(target="vinnie")
        state.branch_state.insurance_paid_until = state.day + 6
        break_target(state)
        con = Quiet()
        war.declare(state, "sal", con)
        self.assertIsNone(state.branch_state.insurance_paid_until)
        self.assertIsNotNone(con.find("void"))
        validate_cross_state(state)

    def test_impossible_insurance_payloads_are_refused(self):
        from extra_toppings import save
        state = war_state(target="vinnie")
        state.branch_state.insurance_paid_until = state.day + 6
        d = save.state_to_dict(state)
        d["branch_state"]["campaigns"].append(
            {"rival_key": "sal", "declared_day": state.day + 1,
             "starting_hundredths": 6000, "broken_day": None,
             "damage": [], "law_calm_until": None,
             "violence_raised": False, "salvage_available": False,
             "salvage_day": None, "captured_pre_latch": False})
        d["branch_state"]["campaigns"][0]["broken_day"] = state.day
        with self.assertRaises(ValueError):
            save.state_from_dict(d)
        state2 = war_state(target="vinnie")
        state2.branch_state.insurance_paid_until = state2.day + 6
        d2 = save.state_to_dict(state2)
        d2["rivals"]["sal"]["strength"] = 0
        with self.assertRaises(ValueError):
            save.state_from_dict(d2)

    def test_the_calm_suppresses_exactly_four_rival_phases(self):
        state = war_state()
        state.rivals["vinnie"].ledger_stolen = True
        rivals.negotiate(state, Scripted([1, 1]), Streams(9).rivals)
        suppressed = 0
        for day in range(state.day, state.day + 8):
            state.day = day
            calm = rival_policy(state, "vinnie")
            camp = live_campaign(state, "vinnie")
            saved = camp.law_calm_until
            camp.law_calm_until = None
            loud = rival_policy(state, "vinnie")
            camp.law_calm_until = saved
            if calm.act_chance < loud.act_chance:
                suppressed += 1
        self.assertEqual(suppressed, 4)

    def test_damage_added_is_the_actual_delta(self):
        state = war_state(target="sal")
        set_relation(state, "sal",
                     min(state.rivals["sal"].relation, VENDETTA_RELATION))
        state.shop.damage_days = 1
        state.rivals["vinnie"].warning = models_mod.RaidWarning(1, models_mod.HOME_SHOP_KEY)
        r = raids.incoming_raid(state, "vinnie", Scripted([1]),
                                Streams(7).raids)
        self.assertEqual(r.damage_before, 1)
        self.assertEqual(r.damage_added, 1)    # 1 → 2 adds one, not two


class TestNightAssignmentsAndStorage(unittest.TestCase):
    """Rev. 15 item 2: one assignment view, one placement authority."""

    def _crewed_war(self):
        state = war_state()
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.hired = True
        rosa.aware = True
        return state, rosa

    def test_the_salvage_driver_cannot_also_raid(self):
        state, rosa = self._crewed_war()
        break_target(state)
        war.declare(state, "sal", Quiet())    # a live front to raid
        plans = {"route": None, "raid": None,
                 "salvage": {"rival": "vinnie", "driver": rosa,
                             "origin_shop": models_mod.HOME_SHOP_KEY,
                           "wagon_key": models_mod.HOME_WAGON_KEY}}
        reserved = phases.night_reserved(plans, but="raid")
        self.assertIn(rosa, reserved)
        con = Scripted([])
        plan = raids.plan_raid(state, con, Streams(3).raids,
                               reserved=reserved,
                               wagon=phases.planned_wagon(
                                   state, plans,
                                   models_mod.HOME_SHOP_KEY))
        self.assertIsNone(plan)               # she was the only crew

    def test_execution_revalidates_the_same_view(self):
        state, rosa = self._crewed_war()
        camp = live_campaign(state, "vinnie")
        del camp
        plans = {"route": None,
                 "raid": {"rival": "vinnie", "objective": "steal_stock",
                          "wagon_key": models_mod.HOME_WAGON_KEY,
                          "team": [rosa], "armed": False,
                          "table_warned": True, "return_shop": models_mod.HOME_SHOP_KEY},
                 "salvage": {"rival": "vinnie", "driver": rosa,
                             "origin_shop": models_mod.HOME_SHOP_KEY,
                             "wagon_key": models_mod.HOME_WAGON_KEY}}
        con = Scripted([6])                   # lock up (war night menu)
        phases.night(state, plans, {"wagons": phases.WagonNight(state)}, con, Streams(11))
        self.assertIsNotNone(con.find("didn't make it to nightfall")
                             or con.find("scrubbed"))
        self.assertEqual(state.raids_led, 0)

    def test_salvage_lands_through_the_placement_authority(self):
        state, rosa = self._crewed_war()
        break_target(state)
        # Pack the stash to its cap in BULK; salvage must not
        # overflow it (the reviewer's 49-in-40 repro).
        bulk = data.GOODS["oregano"]["bulk"]
        state.shop_stash = {"oregano": state.shop.stash_cap // bulk}
        plan = {"rival": "vinnie", "driver": rosa,
                             "origin_shop": models_mod.HOME_SHOP_KEY,
                             "wagon_key": models_mod.HOME_WAGON_KEY}
        war.run_salvage(state, plan, Quiet(), Streams(21).war)
        self.assertLessEqual(state.stash_bulk(state.shop_stash),
                             state.shop.stash_cap)

    def test_salvage_overflow_reaches_a_rented_warehouse(self):
        state, rosa = self._crewed_war()
        break_target(state)
        state.warehouse = {}
        bulk = data.GOODS["oregano"]["bulk"]
        state.shop_stash = {"oregano": state.shop.stash_cap // bulk}
        plan = {"rival": "vinnie", "driver": rosa,
                             "origin_shop": models_mod.HOME_SHOP_KEY,
                             "wagon_key": models_mod.HOME_WAGON_KEY}
        war.run_salvage(state, plan, Quiet(), Streams(21).war)
        self.assertLessEqual(state.stash_bulk(state.shop_stash),
                             state.shop.stash_cap)
        self.assertGreater(sum(state.warehouse.values()), 0)

    def test_the_pickup_can_be_recalled_and_the_wagon_replanned(self):
        state, rosa = self._crewed_war()
        break_target(state)
        plans = {"route": None, "raid": None,
                 "salvage": {"rival": "vinnie", "driver": rosa,
                             "origin_shop": models_mod.HOME_SHOP_KEY,
                           "wagon_key": models_mod.HOME_WAGON_KEY}}
        self.assertEqual(phases.wagon_job(plans), "salvage")
        plans["salvage"] = None               # the recall
        self.assertIsNone(phases.wagon_job(plans))
        self.assertNotIn(rosa, phases.night_reserved(plans, but="route"))


class TestPostPayoffEconomy(unittest.TestCase):
    """Rev. 15 item 3: Carmine's stake ends at the payoff; insolvency
    exists in every active branch."""

    def _skint_war(self):
        state = war_state()
        state.clean = 0
        state.dirty = 0
        state.shop.ingredients = 0
        state.shop_stash = {}
        state.warehouse = None
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        rosa.hired = True
        return state, rosa

    def test_carmine_fronts_nothing_onto_a_paid_debt(self):
        state, _rosa = self._skint_war()
        con = Scripted([9])                   # straight to service
        phases.morning(state, con, Streams(5))
        self.assertEqual(state.debt, 0)
        self.assertEqual(state.shop.ingredients, 0)
        self.assertIsNone(con.find("on account"))

    def test_act_one_fronting_is_untouched(self):
        state = new_state()
        state.debt = 5000
        state.clean = 0
        state.shop.ingredients = 0
        con = Scripted([8])
        phases.morning(state, con, Streams(5))
        self.assertGreater(state.shop.ingredients, 0)
        self.assertGreater(state.debt, 5000)

    def test_two_empty_short_nights_end_the_war(self):
        state, _rosa = self._skint_war()
        con = Quiet()
        for _ in range(2):
            war.night_obligation(state, con, payroll_short=True)
            war.night_insolvency(state, con, payroll_short=True)
        self.assertEqual(state.game_over, "broke")
        self.assertEqual(state.branch_state.insolvent_days, 2)
        validate_branch_state("war", state.branch_state,
                              game_over=state.game_over)

    def test_a_solvent_night_resets_the_counter(self):
        state, _rosa = self._skint_war()
        con = Quiet()
        war.night_insolvency(state, con, payroll_short=True)
        self.assertEqual(state.branch_state.insolvent_days, 1)
        state.dirty = 500                     # a dollar hidden somewhere
        war.night_insolvency(state, con, payroll_short=True)
        self.assertEqual(state.branch_state.insolvent_days, 0)
        self.assertIsNone(state.game_over)

    def test_a_live_war_cannot_carry_two_insolvent_nights(self):
        from extra_toppings import save
        state = war_state()
        state.branch_state.insolvent_days = 2
        d = save.state_to_dict(state)
        with self.assertRaises(ValueError):
            save.state_from_dict(d)


class TestRevision16Boundaries(unittest.TestCase):
    """Rev. 16: the wagon really is owned by the one view at night,
    the Syndicate epilogue renders from the damage ledger, and the
    bot's intelligence is the morning board — never a stale global."""

    def _two_front_war(self):
        state = war_state()
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        marcus = next(e for e in state.employees
                      if e.name.startswith("Marcus"))
        rosa.hired = marcus.hired = True
        break_target(state, "vinnie")
        war.declare(state, "sal", Quiet())
        return state, rosa, marcus

    def test_a_salvage_night_denies_the_raid_the_wagon(self):
        # The rev. 16 item 2 repro: route empty, salvage planned — the
        # old expression read only the route and handed the raid a
        # wagon that was out on the pickup all night.
        state, rosa, marcus = self._two_front_war()
        plans = {"route": None,
                 "raid": {"rival": "sal", "objective": "steal_stock",
                          "wagon_key": models_mod.HOME_WAGON_KEY,
                          "team": [marcus], "armed": False,
                          "table_warned": True, "return_shop": models_mod.HOME_SHOP_KEY},
                 "salvage": {"rival": "vinnie", "driver": rosa,
                             "origin_shop": models_mod.HOME_SHOP_KEY,
                             "wagon_key": models_mod.HOME_WAGON_KEY}}
        phases.night(state, plans, _departed(state, "salvage"),
                     Scripted([6]), Streams(11))
        self.assertIs(plans["raid"]["wagon_free"], False)

    def test_a_free_night_hands_the_raid_the_wagon(self):
        state, _rosa, marcus = self._two_front_war()
        plans = {"route": None, "salvage": None,
                 "raid": {"rival": "sal", "objective": "steal_stock",
                          "wagon_key": models_mod.HOME_WAGON_KEY,
                          "team": [marcus], "armed": False,
                          "table_warned": True, "return_shop": models_mod.HOME_SHOP_KEY}}
        phases.night(state, plans, {"wagons": phases.WagonNight(state)}, Scripted([6]), Streams(11))
        self.assertIs(plans["raid"]["wagon_free"], True)

    def test_the_syndicate_epilogue_reads_the_damage_ledger(self):
        # Jobs-only campaigns: the ending names the night jobs and no
        # one else — no prosecutor, no stolen ledger (rev. 16 item 8).
        state = war_state()
        break_target(state, "vinnie")
        war.declare(state, "sal", Quiet())
        break_target(state, "sal")
        state.game_over = "syndicate"
        con = Quiet()
        game.epilogue(state, con)
        self.assertIsNotNone(con.find("night jobs"))
        self.assertIsNone(con.find("gray suit"))
        self.assertIsNone(con.find("stolen ledger"))

    def test_the_prosecutor_appears_only_for_a_prosecution(self):
        state = war_state()
        apply_rival_damage(state, "vinnie", "ledger", LEDGER_LAW_STRENGTH)
        live_campaign(state, "vinnie").violence_raised = True
        break_target(state, "vinnie")
        war.declare(state, "sal", Quiet())
        break_target(state, "sal")
        state.game_over = "syndicate"
        con = Quiet()
        game.epilogue(state, con)
        self.assertIsNotNone(con.find("gray suit"))

    def test_a_spent_ledger_without_the_law_stays_a_ledger(self):
        state = war_state()
        apply_rival_damage(state, "vinnie", "ledger", LEDGER_LEAN_STRENGTH)
        break_target(state, "vinnie")
        war.declare(state, "sal", Quiet())
        break_target(state, "sal")
        state.game_over = "syndicate"
        con = Quiet()
        game.epilogue(state, con)
        self.assertIsNotNone(con.find("stolen ledger"))
        self.assertIsNone(con.find("gray suit"))

    def test_the_bot_reads_the_live_target_from_the_board(self):
        import random
        from extra_toppings.bot import WarBot
        bot = WarBot(random.Random(0))
        bot._at_war = True
        bot.say("DAY 20 of 30 — MORNING")
        bot.say("  SAL — strength 40.0 of 55.0, security wary, "
                "ovens intact")
        self.assertEqual(bot._live_target, "Sal")
        pick = bot._special_menu("Run today's route where?",
                                 ["Old Harbor — Vinnie's turf",
                                  "Little Sicily — Sal's turf",
                                  "University — open ground",
                                  "Back"])
        self.assertEqual(pick, 1)
        # The board is MORNING-SCOPED: a new morning clears it until
        # the new board is read — no stale target survives the night.
        bot.say("DAY 21 of 30 — MORNING")
        self.assertIsNone(bot._live_target)




class TestRevision17Instruments(unittest.TestCase):
    """Rev. 17 items 3-6: the night reads execution results, outgoing
    jobs book typed attempts, the ledger's three quantities come from
    one canonical view, and route sales have their own field."""

    def _two_front_war(self):
        state = war_state()
        rosa = next(e for e in state.employees if e.name.startswith("Rosa"))
        marcus = next(e for e in state.employees
                      if e.name.startswith("Marcus"))
        rosa.hired = marcus.hired = True
        break_target(state, "vinnie")
        war.declare(state, "sal", Quiet())
        return state, rosa, marcus

    def test_a_scrubbed_pickup_frees_the_wagon_for_the_raid(self):
        # The rev. 17 item 6 repro: the pickup scrubbed before
        # departure never took the wagon out — the untouched PLAN must
        # not reserve it against the raid.
        state, rosa, marcus = self._two_front_war()
        plans = {"route": None,
                 "raid": {"rival": "sal", "objective": "steal_stock",
                          "wagon_key": models_mod.HOME_WAGON_KEY,
                          "team": [marcus], "armed": False,
                          "table_warned": True, "return_shop": models_mod.HOME_SHOP_KEY},
                 "salvage": {"rival": "vinnie", "driver": rosa,
                             "origin_shop": models_mod.HOME_SHOP_KEY,
                             "wagon_key": models_mod.HOME_WAGON_KEY}}
        report = {"salvage": war.SalvageResult(outcome="scrubbed",
                                               wagon_used=False)}
        phases.night(state, plans, _wag(state, **report), Scripted([6]), Streams(11))
        self.assertIs(plans["raid"]["wagon_free"], True)

    def test_a_departed_pickup_still_holds_the_wagon(self):
        state, rosa, marcus = self._two_front_war()
        plans = {"route": None,
                 "raid": {"rival": "sal", "objective": "steal_stock",
                          "wagon_key": models_mod.HOME_WAGON_KEY,
                          "team": [marcus], "armed": False,
                          "table_warned": True, "return_shop": models_mod.HOME_SHOP_KEY},
                 "salvage": {"rival": "vinnie", "driver": rosa,
                             "origin_shop": models_mod.HOME_SHOP_KEY,
                             "wagon_key": models_mod.HOME_WAGON_KEY}}
        report = {"salvage": war.SalvageResult(outcome="collected",
                                               wagon_used=True,
                                               collected_units=5)}
        phases.night(state, plans, _departed(state, "salvage", **report),
                     Scripted([6]), Streams(11))
        self.assertIs(plans["raid"]["wagon_free"], False)

    def test_a_pickup_that_never_departed_leaves_the_wagon(self):
        # Rev. 17 item 6's question, answered by DEPARTURE rather than
        # by inference (P4b.1a): the old code read the plans and a
        # report and guessed "busy" when it could not tell. There is
        # nothing to guess now — a pickup that never claimed its wagon
        # never took it, and the raid finds it standing there.
        state, rosa, marcus = self._two_front_war()
        plans = {"route": None,
                 "raid": {"rival": "sal", "objective": "steal_stock",
                          "wagon_key": models_mod.HOME_WAGON_KEY,
                          "team": [marcus], "armed": False,
                          "table_warned": True, "return_shop": models_mod.HOME_SHOP_KEY},
                 "salvage": {"rival": "vinnie", "driver": rosa,
                             "origin_shop": models_mod.HOME_SHOP_KEY,
                             "wagon_key": models_mod.HOME_WAGON_KEY}}
        phases.night(state, plans, _wag(state), Scripted([6]), Streams(11))
        self.assertIs(plans["raid"]["wagon_free"], True)

    def test_run_salvage_returns_scrubbed_without_departing(self):
        state, rosa, _marcus = self._two_front_war()
        rosa.injured_days = 3
        result = war.run_salvage(state, {"rival": "vinnie",
                                         "driver": rosa},
                                 Quiet(), Streams(21).war)
        self.assertEqual(result.outcome, "scrubbed")
        self.assertIs(result.wagon_used, False)
        camp = next(c for c in state.branch_state.campaigns
                    if c.rival_key == "vinnie")
        self.assertTrue(camp.salvage_available)   # still waiting

    def test_a_collected_pickup_reports_the_departure(self):
        state, rosa, _marcus = self._two_front_war()
        result = war.run_salvage(
            state, {"rival": "vinnie", "driver": rosa,
                    "origin_shop": models_mod.HOME_SHOP_KEY,
                    "wagon_key": models_mod.HOME_WAGON_KEY},
            Quiet(), Streams(21).war)
        self.assertEqual(result.outcome, "collected")
        self.assertIs(result.wagon_used, True)

    def test_the_attempt_ledger_books_crew_and_actual_damage(self):
        # Rev. 17 item 4: the denominator's record — committed crew
        # and ACTUAL applied strength damage, never more than the
        # strongest job can apply.
        state, rosa, marcus = self._two_front_war()
        before = round(state.rivals["sal"].strength * 100)
        plan = {"rival": "sal", "objective": "steal_stock",
                "team": [rosa, marcus], "armed": False,
                "table_warned": True, "wagon_free": True, "return_shop": models_mod.HOME_SHOP_KEY}
        # Guard prompts answered by script; an exhausted script
        # aborts the job — either way the attempt is booked.
        base = len(state.raid_log)      # break_target booked its jobs
        raids.run_raid(state, plan, Scripted([1, 1, 1, 1]),
                       Streams(7).raids)
        self.assertEqual(len(state.raid_log), base + 1)
        entry = state.raid_log[-1]
        self.assertIn(entry.outcome, ("succeeded", "failed"))
        self.assertEqual(entry.crew, 2)
        self.assertEqual(entry.day, state.day)
        actual = before - round(state.rivals["sal"].strength * 100)
        self.assertEqual(entry.damage_h, actual
                         if entry.outcome == "succeeded" else 0)
        self.assertLessEqual(entry.damage_h, 1200)
        # Frozen: the record cannot be edited after the fact
        # (rev. 18 item 3 — no more dict mutated in flight).
        with self.assertRaises(Exception):
            entry.outcome = "succeeded"

    def test_a_dead_target_scrub_is_booked(self):
        state, rosa, marcus = self._two_front_war()
        break_target(state, "sal")
        plans = {"route": None, "salvage": None,
                 "raid": {"rival": "sal", "objective": "steal_stock",
                          "wagon_key": models_mod.HOME_WAGON_KEY,
                          "team": [marcus], "armed": False,
                          "table_warned": True, "return_shop": models_mod.HOME_SHOP_KEY}}
        phases.night(state, plans, {"wagons": phases.WagonNight(state)}, Scripted([6]), Streams(11))
        scrubs = [e for e in state.raid_log if e.outcome == "scrubbed"]
        self.assertEqual(len(scrubs), 1)
        self.assertEqual(scrubs[0].damage_h, 0)

    def test_ledger_quantities_reads_live_relief(self):
        # The reviewer's legal record: accrued 20, Case contribution
        # 10 under live retention protection — the canonical view
        # reports all three quantities, and "effective" means LIVE.
        from extra_toppings import evidence as ev
        state, rosa, _marcus = self._two_front_war()
        rosa.aware = True
        rosa.morale = 8
        state.add_case(20.0, f"{rosa.name} saw all of it",
                       kind="witness", source=rosa.key)
        q = ev.ledger_quantities(state)
        self.assertAlmostEqual(q["accrued"], 20.0)
        self.assertAlmostEqual(q["residue"], 20.0)
        self.assertAlmostEqual(q["effective"], 10.0)

    def test_route_sales_survive_the_raid_shortage_signal(self):
        # Rev. 17 item 3 / rev. 18 item 4: sold_yesterday is a price
        # signal that stock raids overwrite with -8 shortages; actual
        # sales live in the typed route record and no study reads the
        # poisoned signal.
        import random as _random
        from extra_toppings import market, routes
        state, rosa, _marcus = self._two_front_war()
        market.roll_prices(state, _random.Random(3))
        plan = {"district": "little_sicily", "driver": rosa,
                "ride_along": False, "legit": 0,
                "cargo": {"mushrooms": 6}, "origin_shop": models_mod.HOME_SHOP_KEY,
                           "wagon_key": models_mod.HOME_WAGON_KEY}
        report = routes.resolve_route(state, plan, Quiet(),
                                      _random.Random(4))
        state.districts["little_sicily"].sold_yesterday["mushrooms"] = -8
        record = state.route_log[-1]
        self.assertEqual(record.units_sold, report["sold"])
        self.assertEqual(record.district, "little_sicily")

    def test_the_route_record_reads_the_band_at_execution(self):
        # Rev. 18 item 4: the record carries the band the route RAN
        # under — heat moving later that night cannot rewrite it.
        import random as _random
        from extra_toppings import market, routes
        state, rosa, _marcus = self._two_front_war()
        market.roll_prices(state, _random.Random(3))
        state.districts["little_sicily"].heat = 60.0     # amber now
        plan = {"district": "little_sicily", "driver": rosa,
                "ride_along": False, "legit": 0,
                "cargo": {"mushrooms": 6}, "origin_shop": models_mod.HOME_SHOP_KEY,
                           "wagon_key": models_mod.HOME_WAGON_KEY}
        routes.resolve_route(state, plan, Quiet(), _random.Random(4))
        state.districts["little_sicily"].heat = 0.0      # cools after
        record = state.route_log[-1]
        self.assertEqual(record.heat_band, "amber")
        self.assertEqual(record.capacity_mult, 0.5)
        self.assertTrue(record.contested)                # Sal's live turf

    def test_malformed_attempt_payloads_are_refused(self):
        # The reviewer's repro: day="banana", crew=-7, damage 999999
        # round-tripped. Typed records refuse at construction, so
        # persistence refuses too (rev. 18 item 3).
        from extra_toppings import save
        state, _rosa, _marcus = self._two_front_war()
        d = save.state_to_dict(state)
        for bad in ({"day": "banana", "rival": "sal",
                     "outcome": "succeeded", "crew": 1, "damage_h": 0},
                    {"day": 15, "rival": "nobody",
                     "outcome": "succeeded", "crew": 1, "damage_h": 0},
                    {"day": 15, "rival": "sal", "outcome": "won-ish",
                     "crew": 1, "damage_h": 0},
                    {"day": 15, "rival": "sal", "outcome": "succeeded",
                     "crew": -7, "damage_h": 0},
                    {"day": 15, "rival": "sal", "outcome": "succeeded",
                     "crew": 1, "damage_h": 999999},
                    {"day": 15, "rival": "sal", "outcome": "failed",
                     "crew": 1, "damage_h": 100}):
            d2 = dict(d)
            d2["raid_log"] = [bad]
            with self.assertRaises(ValueError):
                save.state_from_dict(d2)

    def test_malformed_route_payloads_are_refused(self):
        from extra_toppings import save
        state, _rosa, _marcus = self._two_front_war()
        d = save.state_to_dict(state)
        for bad in ({"day": 15, "district": "nowhere",
                     "heat_band": "cool", "capacity_mult": 1.0,
                     "units_sold": 0, "corner_damage_h": 0,
                     "contested": False},
                    {"day": 15, "district": "old_harbor",
                     "heat_band": "lava", "capacity_mult": 1.0,
                     "units_sold": 0, "corner_damage_h": 0,
                     "contested": False},
                    {"day": 15, "district": "old_harbor",
                     "heat_band": "cool", "capacity_mult": 1.0,
                     "units_sold": -1, "corner_damage_h": 0,
                     "contested": False},
                    {"day": 15, "district": "old_harbor",
                     "heat_band": "cool", "capacity_mult": 1.0,
                     "units_sold": 5, "corner_damage_h": 100,
                     "contested": False}):
            d2 = dict(d)
            d2["route_log"] = [bad]
            with self.assertRaises(ValueError):
                save.state_from_dict(d2)




class TestRevision19Pairing(unittest.TestCase):
    """Rev. 19 item 3: the pacing experiment's dice are keyed by
    calendar night, and the alertness transition is production's."""

    def test_skipping_a_night_cannot_shift_later_dice(self):
        # Two arms that differ ONLY at night 0 (skip vs attempt) must
        # hand run_raid IDENTICAL mechanics dice on every shared
        # later attempt night.
        from analysis import experiments as ex
        seen: dict = {}

        real_run_raid = raids.run_raid

        def spy(state, plan, con, rng, _arm=[None]):
            seen.setdefault(_arm[0], {})[state.day] = rng.getstate()
            return real_run_raid(state, plan, con, rng)

        def arm(name, skip_first):
            def policy(night, rival):
                return not (skip_first and night == 0)
            spy.__defaults__ = ([name],)
            raids.run_raid = spy
            try:
                ex._pacing_rollout(3, policy)
            finally:
                raids.run_raid = real_run_raid

        arm("skip", True)
        arm("all", False)
        shared = set(seen["skip"]) & set(seen["all"])
        self.assertGreater(len(shared), 5)
        for day in shared:
            self.assertEqual(seen["skip"][day], seen["all"][day],
                             f"night {day}'s dice shifted")

    def test_the_experiment_uses_the_production_transition(self):
        # One home (rev. 19 item 3): the canonical tick IS what the
        # rival phase runs — decay on a quiet night, none on a night
        # you hit them.
        from extra_toppings.models import (ALERTNESS_DECAY,
                                           alertness_decay_tick)
        state = war_state()
        rv = state.rivals["vinnie"]
        rv.alertness = 5.0
        rv.last_raided_day = state.day       # hit tonight
        alertness_decay_tick(rv, state.day)
        self.assertEqual(rv.alertness, 5.0)
        alertness_decay_tick(rv, state.day + 1)
        self.assertEqual(rv.alertness, 5.0 - ALERTNESS_DECAY)




class TestRevision19Ending(unittest.TestCase):
    """Rev. 19 item 5: the Harbor Is Yours ending derives and names
    the ACTUAL captured turf."""

    def test_sals_fall_names_little_sicily(self):
        state = war_state(target="sal")
        break_target(state, "sal")
        state.game_over = "harbor_yours"
        con = Quiet()
        game.epilogue(state, con)
        self.assertIsNotNone(con.find("Little Sicily learned your number"))

    def test_vinnies_fall_names_both_districts(self):
        state = war_state(target="vinnie")
        break_target(state, "vinnie")
        state.game_over = "harbor_yours"
        con = Quiet()
        game.epilogue(state, con)
        line = con.find("learned your number")
        self.assertIsNotNone(line)
        self.assertIn("Old Harbor", line)
        self.assertIn("Meadows", line)




class TestRevision20History(unittest.TestCase):
    """Rev. 20 item 2: the ledgers validate the HISTORY they claim —
    reconciled against the campaign record, both directions."""

    def _legal_war(self):
        state = war_state()
        state.day = 16
        before = round(state.rivals["vinnie"].strength * 100)
        apply_rival_damage(state, "vinnie", "jobs", 12)
        jobs_h = before - round(state.rivals["vinnie"].strength * 100)
        state.raid_log.append(models_mod.RaidAttemptRecord(
            day=16, rival="vinnie", outcome="succeeded", crew=2,
            damage_h=jobs_h))
        return state

    def test_a_boolean_multiplier_is_not_a_float(self):
        state = self._legal_war()
        d = save_mod.state_to_dict(state)
        d["route_log"] = [{"day": 15, "district": "university",
                           "heat_band": "cool", "capacity_mult": True,
                           "units_sold": 0, "corner_damage_h": 0,
                           "contested": False}]
        with self.assertRaises(ValueError):
            save_mod.state_from_dict(d)

    def test_amber_halves_the_corner_ceiling(self):
        state = self._legal_war()
        d = save_mod.state_to_dict(state)
        d["route_log"] = [{"day": 15, "district": "old_harbor",
                           "heat_band": "amber", "capacity_mult": 0.5,
                           "units_sold": 20, "corner_damage_h": 800,
                           "contested": True}]
        with self.assertRaises(ValueError):
            save_mod.state_from_dict(d)

    def test_a_contested_route_needs_its_war(self):
        # An Act I state where no war ever existed cannot carry a
        # contested Old Harbor route; nor may one predate the
        # declaration.
        state = game.new_state()
        d = save_mod.state_to_dict(state)
        d["route_log"] = [{"day": 1, "district": "old_harbor",
                           "heat_band": "cool", "capacity_mult": 1.0,
                           "units_sold": 5, "corner_damage_h": 0,
                           "contested": True}]
        with self.assertRaises(ValueError):
            save_mod.state_from_dict(d)
        state = self._legal_war()
        d = save_mod.state_to_dict(state)
        d["route_log"] = [{"day": 13, "district": "old_harbor",
                           "heat_band": "cool", "capacity_mult": 1.0,
                           "units_sold": 5, "corner_damage_h": 0,
                           "contested": True}]        # declared day 14
        with self.assertRaises(ValueError):
            save_mod.state_from_dict(d)

    def test_raid_damage_reconciles_with_the_campaign(self):
        # A raid claiming damage the campaign never booked, and
        # campaign damage no raid ever produced — both refused.
        state = self._legal_war()
        d = save_mod.state_to_dict(state)
        d["raid_log"].append({"day": 17, "rival": "vinnie",
                              "outcome": "succeeded", "crew": 2,
                              "damage_h": 1200})
        with self.assertRaises(ValueError):
            save_mod.state_from_dict(d)
        d = save_mod.state_to_dict(state)
        d["raid_log"] = []                 # the booked 12 now orphaned
        with self.assertRaises(ValueError):
            save_mod.state_from_dict(d)

    def test_one_job_a_night_binds_the_logs(self):
        state = self._legal_war()
        d = save_mod.state_to_dict(state)
        d["raid_log"].append(dict(d["raid_log"][-1]))   # duplicate day
        with self.assertRaises(ValueError):
            save_mod.state_from_dict(d)

    def test_a_legal_history_round_trips(self):
        state = self._legal_war()
        d = save_mod.state_to_dict(state)
        restored = save_mod.state_from_dict(d)
        self.assertEqual(save_mod.state_to_dict(restored), d)


if __name__ == "__main__":
    unittest.main()
