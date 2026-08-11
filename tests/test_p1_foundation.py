"""P1a foundation: the fork's skeleton, proven inert until entered.

GameConfig (flag gates entry, never continuation), the SitdownSnapshot
frozen at lock-up, the pure chair evaluator, the deterministic sit-down
scene with stand-pat as the only actionable chair, BranchState
constructors and validation, and the save-layer round trips — per
design §8 revisions 4 and 5. The behavioral gates are the equivalence
harness's two modes (`check` flag-off against the untouched goldens,
`standpat` paired flag-on); these tests pin the semantics themselves.
"""

import copy
import random
import unittest
from dataclasses import FrozenInstanceError
from unittest import mock

from analysis import equivalence
from extra_toppings import (data, game, models, partner, phases,
                            save, sitdown)
from extra_toppings.bot import GreedyBot
from extra_toppings.config import GameConfig
from extra_toppings.models import (BranchState, Evidence, SitdownSnapshot,
                                   new_state, validate_branch_state)
from extra_toppings.rng import Streams
from extra_toppings.ui import BotConsole, ScriptedConsole, ScriptExhausted

def _wag(state, **report):
    """Every direct `night` call needs the assignment authority the
    service phase would have opened (P4b.1a). An UNSPENT one is the
    honest fixture here: these tests do not run service, so no wagon
    departed."""
    return {**report, "wagons": phases.WagonNight(state)}

FORK_ON = GameConfig(fork_enabled=True)


class CaptureConsole(ScriptedConsole):
    """Scripted answers plus everything shown, in order; menu prompts are
    tagged so ordering against prose lines can be asserted."""

    def __init__(self, script=None):
        super().__init__(script)
        self.lines: list = []

    def say(self, text=""):
        self.lines.append(text)

    def bullet(self, text):
        self.lines.append(f"• {text}")

    def menu(self, prompt, options):
        self.lines.append(f"[menu] {prompt}")
        return super().menu(prompt, options)

    def find(self, fragment):
        for i, line in enumerate(self.lines):
            if fragment in line:
                return i
        return None

    def menu_count(self):
        return sum(1 for line in self.lines if line.startswith("[menu]"))


class SceneAbort(Exception):
    pass


class AbortingConsole(CaptureConsole):
    """Answers `allowed` scene menus, then bails — a stand-in for the
    player quitting mid-scene before any selection commits."""

    def __init__(self, script=None, allowed=1):
        super().__init__(script)
        self.allowed = allowed

    def scene_menu(self, namespace, prompt, options):
        if self.allowed <= 0:
            raise SceneAbort()
        self.allowed -= 1
        return super().scene_menu(namespace, prompt, options)


def run_night(state, script, seed=1, config=None):
    con = CaptureConsole(list(script))
    phases.night(state, {"routes": {}}, _wag(state), con, Streams(seed), config)
    return con


def scene_state(payoff_day=13, case=20.0, evidence=None):
    """A state standing at the sit-down morning with a pending snapshot."""
    state = new_state()
    state.debt = 0
    state.debt_paid_day = payoff_day
    state.day = payoff_day + 1
    for day, magnitude, why in (evidence or []):
        state.evidence.append(Evidence(day=day, magnitude=magnitude,
                                       kind="physical", why=why))
    state.sitdown_snapshot = SitdownSnapshot(
        payoff_day=payoff_day, case_at_lockup=case,
        evidence_count_at_lockup=len(state.evidence))
    return state


# ══ GameConfig ════════════════════════════════════════════════════

class TestGameConfig(unittest.TestCase):
    def test_defaults_are_fork_off_no_branches(self):
        cfg = GameConfig()
        self.assertFalse(cfg.fork_enabled)
        self.assertEqual(cfg.enabled_branches, frozenset())

    def test_config_is_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            GameConfig().fork_enabled = True  # type: ignore[misc]

    def test_a_mutable_set_cannot_reach_inside_the_config(self):
        branches = {"straight"}
        cfg = GameConfig(fork_enabled=True, enabled_branches=branches)
        branches.add("war")                    # mutate the caller's set
        self.assertEqual(cfg.enabled_branches, frozenset({"straight"}))
        self.assertIsInstance(cfg.enabled_branches, frozenset)

    def test_unknown_branch_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            GameConfig(enabled_branches={"golf_course"})


# ══ The lock-up snapshot ══════════════════════════════════════════

class TestSnapshotCapture(unittest.TestCase):
    """§2.1 rev. 4 through the real night phase: frozen when the player
    locks up, after every discretionary account action, before the
    world's dice."""

    def payoff_night(self, script, case=55.0, dirty=0, clean=1500,
                     debt=1000, seed=1, config=FORK_ON):
        state = new_state()
        state.day = 12
        state.debt = debt
        state.clean = clean
        state.dirty = dirty
        if case:
            state.add_case(case, "prior seizures", kind="physical")
        run_night(state, script, seed=seed, config=config)
        return state

    def test_snapshot_freezes_at_lockup_on_payoff_night(self):
        state = self.payoff_night([1, 1000, 4])
        snap = state.sitdown_snapshot
        self.assertIsNotNone(snap)
        self.assertEqual(snap.payoff_day, 12)
        self.assertEqual(snap.case_at_lockup, 55.0)
        self.assertEqual(snap.evidence_count_at_lockup, 1)

    def test_paying_then_overwashing_cannot_dodge_the_snapshot(self):
        # The rev. 4 exploit, replayed: pay the final dollar at Case 65,
        # over-launder to 85 afterward, then lock up. The snapshot reads
        # 85 and both Case-gated chairs close — ordering buys nothing.
        state = self.payoff_night([1, 1000, 0, 12000, 4],
                                  case=65.0, dirty=12000)
        snap = state.sitdown_snapshot
        self.assertEqual(snap.case_at_lockup, 85.0)
        verdicts = {v.chair: v for v in
                    sitdown.evaluate_chairs(snap, state.evidence)}
        self.assertFalse(verdicts["partner"].available)
        self.assertFalse(verdicts["quiet_sale"].available)
        self.assertIn("register", verdicts["quiet_sale"].closed_by)

    def test_world_dice_after_lockup_do_not_reach_the_snapshot(self):
        # Pay and lock up at 65; the rival/law phases may accrue after.
        # Wherever they do, the snapshot keeps 65 and the offers stand.
        for seed in range(80):
            state = new_state()
            state.day = 12
            state.debt = 1000
            state.clean = 1500
            state.districts[data.HOME_DISTRICT].heat = 100
            state.shop_stash = {"mushrooms": 5}
            state.add_case(65.0, "prior seizures", kind="physical")
            run_night(state, [1, 1000, 4], seed=seed, config=FORK_ON)
            if state.case > 65.0:
                snap = state.sitdown_snapshot
                self.assertEqual(snap.case_at_lockup, 65.0)
                verdicts = {v.chair: v for v in
                            sitdown.evaluate_chairs(snap, state.evidence)}
                self.assertTrue(verdicts["partner"].available)
                return
        self.fail("no seed accrued world evidence after lock-up")

    def test_flag_off_captures_nothing(self):
        state = self.payoff_night([1, 1000, 4], config=None)
        self.assertIsNone(state.sitdown_snapshot)
        state = self.payoff_night([1, 1000, 4], config=GameConfig())
        self.assertIsNone(state.sitdown_snapshot)

    def test_no_capture_without_a_payoff_tonight(self):
        state = self.payoff_night([0, 0, 4], debt=50000)
        self.assertIsNone(state.sitdown_snapshot)


# ══ The pure chair evaluator ══════════════════════════════════════

class TestChairEvaluator(unittest.TestCase):
    def verdicts(self, payoff_day, case=0.0, evidence=(), count=None):
        records = [Evidence(day=d, magnitude=m, kind="physical", why=w)
                   for d, m, w in evidence]
        snap = SitdownSnapshot(
            payoff_day=payoff_day, case_at_lockup=case,
            evidence_count_at_lockup=count if count is not None
            else len(records))
        return {v.chair: v for v in sitdown.evaluate_chairs(snap, records)}

    def test_early_payoff_seats_every_chair(self):
        v = self.verdicts(13)
        for chair in ("straight", "partner", "war", "quiet_sale", "stand_pat"):
            self.assertTrue(v[chair].available, chair)

    def test_payoff_21_withholds_only_the_partner(self):
        v = self.verdicts(21)                      # R = 9
        self.assertFalse(v["partner"].available)
        self.assertIn("no time to build", v["partner"].reason)
        for chair in ("straight", "war", "quiet_sale"):
            self.assertTrue(v[chair].available, chair)

    def test_payoff_23_withholds_the_war_too(self):
        v = self.verdicts(23)                      # R = 7
        self.assertFalse(v["war"].available)
        self.assertIn("wars outlive months", v["war"].reason)

    def test_payoff_25_leaves_straight_sale_and_standing(self):
        v = self.verdicts(25)                      # R = 5 — design edge case
        self.assertTrue(v["straight"].available)
        self.assertTrue(v["quiet_sale"].available)
        self.assertTrue(v["stand_pat"].available)
        self.assertFalse(v["partner"].available)
        self.assertFalse(v["war"].available)

    def test_case_gates_close_at_their_exact_thresholds(self):
        self.assertTrue(self.verdicts(13, case=69.9)["partner"].available)
        self.assertFalse(self.verdicts(13, case=70.0)["partner"].available)
        self.assertTrue(self.verdicts(13, case=84.9)["quiet_sale"].available)
        self.assertFalse(self.verdicts(13, case=85.0)["quiet_sale"].available)

    def test_the_closing_record_is_named_by_prefix_sum(self):
        v = self.verdicts(13, case=75.0,
                          evidence=[(3, 40.0, "a seized shipment"),
                                    (5, 35.0, "the second seizure")])
        self.assertFalse(v["partner"].available)
        self.assertEqual(v["partner"].closed_by, "the second seizure")

    def test_records_after_lockup_are_outside_the_snapshot(self):
        # Third record would cross 85, but it postdates the lock-up count.
        v = self.verdicts(13, case=75.0,
                          evidence=[(3, 40.0, "a seized shipment"),
                                    (5, 35.0, "the second seizure"),
                                    (12, 30.0, "last night's raid")],
                          count=2)
        self.assertTrue(v["quiet_sale"].available)


# ══ The scene ═════════════════════════════════════════════════════

class TestSitdownScene(unittest.TestCase):
    def test_stand_pat_commits_branch_and_act(self):
        state = scene_state()
        con = CaptureConsole([4, 1])           # stand pat, confirm
        sitdown.run_scene(state, con, FORK_ON)
        self.assertEqual(state.branch, "stand_pat")
        self.assertEqual(state.act, 2)
        self.assertIsNone(state.branch_state)
        self.assertIsNotNone(con.find("Nobody mentions the table again"))

    def test_all_four_chairs_render_with_dev_markers(self):
        state = scene_state()
        con = CaptureConsole([4, 1])
        sitdown.run_scene(state, con, FORK_ON)
        for label in ("The Straight Path", "Carmine's Partner",
                      "The Harbor War", "The Quiet Sale"):
            self.assertIsNotNone(con.find(label), label)
        self.assertIsNotNone(con.find("[not in this build]"))

    def test_a_withheld_chair_refuses_and_names_its_reason(self):
        state = scene_state(payoff_day=21)     # partner withheld
        con = CaptureConsole([1, 4, 1])        # try partner, then stand pat
        sitdown.run_scene(state, con, FORK_ON)
        self.assertIsNotNone(con.find("That chair is empty"))
        self.assertEqual(state.branch, "stand_pat")

    def test_an_unimplemented_chair_never_becomes_stand_pat_silently(self):
        state = scene_state()
        con = CaptureConsole([0, 4, 1])        # try straight, then stand pat
        sitdown.run_scene(state, con, FORK_ON)
        dev = con.find("development build")
        commit = con.find("Nobody mentions the table again")
        self.assertIsNotNone(dev)
        self.assertIsNotNone(commit)
        self.assertLess(dev, commit)

    def test_aborting_before_selection_mutates_nothing_and_replays(self):
        state = scene_state()
        snap_before = state.sitdown_snapshot
        con = AbortingConsole([0], allowed=1)  # one refused pick, then bail
        with self.assertRaises(SceneAbort):
            sitdown.run_scene(state, con, FORK_ON)
        self.assertIsNone(state.branch)
        self.assertEqual(state.act, 1)
        self.assertIs(state.sitdown_snapshot, snap_before)
        # The reload simply replays the scene, which can now conclude.
        sitdown.run_scene(state, CaptureConsole([4, 1]), FORK_ON)
        self.assertEqual(state.branch, "stand_pat")

    def test_reconsider_loops_back_to_the_table(self):
        state = scene_state()
        con = CaptureConsole([4, 0, 4, 1])     # stand pat, reconsider, again
        sitdown.run_scene(state, con, FORK_ON)
        self.assertEqual(state.branch, "stand_pat")

    def test_late_payoff_gets_respect_and_no_table(self):
        state = scene_state(payoff_day=26)     # R = 4: no sit-down
        con = CaptureConsole([])
        sitdown.run_scene(state, con, FORK_ON)
        self.assertIsNotNone(con.find("Respect"))
        self.assertEqual(con.menu_count(), 0)
        self.assertIsNone(state.branch)
        self.assertEqual(state.act, 1)

    def test_due_fires_only_on_the_morning_after_with_no_ending(self):
        state = scene_state()
        self.assertTrue(sitdown.due(state))
        state.game_over = "arrested"           # arrest suppresses the scene
        self.assertFalse(sitdown.due(state))
        state.game_over = None
        state.day += 1                          # a missed morning stays missed
        self.assertFalse(sitdown.due(state))
        state.day -= 1
        state.branch = "stand_pat"              # once, ever
        self.assertFalse(sitdown.due(state))
        state.branch = None
        state.sitdown_snapshot = None
        self.assertFalse(sitdown.due(state))

    def test_post_lockup_evidence_shows_the_offers_stand(self):
        state = scene_state(case=65.0, evidence=[(12, 65.0, "seizures")])
        state.evidence.append(Evidence(day=12, magnitude=25.0,
                                       kind="witness", why="an informant"))
        con = CaptureConsole([1, 4, 1])        # partner: still offered
        sitdown.run_scene(state, con, FORK_ON)
        self.assertIsNotNone(con.find("the offers stand"))
        # The pick is refused for build reasons, not as an empty chair.
        self.assertIsNotNone(con.find("development build"))
        self.assertIsNone(con.find("That chair is empty"))

    def test_rivals_at_war_do_not_delay_the_table(self):
        state = scene_state()
        state.rivals["vinnie"].warning = models.RaidWarning(2, models.HOME_SHOP_KEY)
        con = CaptureConsole([4, 1])
        sitdown.run_scene(state, con, FORK_ON)
        self.assertIsNotNone(con.find("idle across the street"))
        self.assertEqual(state.branch, "stand_pat")

    # The site answer is BUILT FROM THE DISTRICT IDENTITY (rev. 31
    # item 2), never written as a literal index: a positional
    # constant here would claim identity and mean position, and a
    # menu reorder would silently change which world this test
    # builds while the comment still said University Hill.
    SITE = "university"

    def _chair_script(self, chair):
        site_answer = 1 + partner.SITE_DISTRICTS.index(self.SITE)
        return {
            "straight": [0, 1],        # chair, burn the book
            "partner": [1, site_answer, 1],   # chair, the site, shake
            "war": [2, 1, 1],          # chair, name the first rival, declare
            "quiet_sale": [3, 1],      # chair, shake on it
        }[chair]

    def test_every_canonical_chair_has_a_commit_path(self):
        # P4b.1b seated the last chair, so no branch id is left to
        # probe the loud failure WITH. The invariant is now pinned
        # from the other side and over the canonical list itself:
        # every chair in BRANCH_ORDER seats when it is enabled and
        # chosen. Add a fifth chair without a commit path and this
        # fails the day it is added — at test time rather than under
        # a player — while the `NotImplementedError` in `run_scene`
        # stays as the runtime backstop, because without it an
        # unhandled chair falls through to an endless re-prompt,
        # which is worse than a raise.
        for chair in models.BRANCH_ORDER:
            with self.subTest(chair):
                state = scene_state()
                cfg = GameConfig(fork_enabled=True,
                                 enabled_branches=frozenset({chair}))
                sitdown.run_scene(
                    state, CaptureConsole(self._chair_script(chair)), cfg)
                self.assertEqual(state.branch, chair)
                self.assertEqual(state.act, 2)
                if chair == "partner":
                    # The chosen SITE, asserted by identity too.
                    self.assertEqual(state.shops[-1].district, self.SITE)


# ══ The canonical view: frozen ledger vs live morning file ════════

class TestSitdownView(unittest.TestCase):
    """Rev. 6: one canonical SitdownView carries frozen and live Case;
    every difference renders, whether or not a threshold moved."""

    def test_view_carries_both_ledgers_and_bands(self):
        state = scene_state(case=20.0, evidence=[(12, 20.0, "seizures")])
        state.evidence.append(Evidence(day=12, magnitude=12.0,
                                       kind="witness", why="an informant"))
        view = sitdown.build_view(state.sitdown_snapshot, state.evidence)
        self.assertEqual(view.frozen_case, 20.0)
        self.assertEqual(view.live_case, 32.0)
        self.assertEqual(view.frozen_band, "a quiet file")
        self.assertEqual(view.live_band, "a warm file")

    def test_a_warming_below_every_threshold_still_renders(self):
        # 20 → 32: no gate moved, the difference is shown anyway.
        state = scene_state(case=20.0, evidence=[(12, 20.0, "seizures")])
        state.evidence.append(Evidence(day=12, magnitude=12.0,
                                       kind="witness", why="an informant"))
        con = CaptureConsole([4, 1])
        sitdown.run_scene(state, con, FORK_ON)
        i = con.find("has warmed since the books closed")
        self.assertIsNotNone(i)
        self.assertIn("32", con.lines[i])
        self.assertIn("chairs were set at closing time", con.lines[i])

    def test_a_crossing_after_lockup_says_the_offers_stand(self):
        # 65 → 72: the live file crosses the Partner gate; the frozen
        # offer stands and the scene says exactly that.
        state = scene_state(case=65.0, evidence=[(12, 65.0, "seizures")])
        state.evidence.append(Evidence(day=12, magnitude=7.0,
                                       kind="witness", why="an informant"))
        con = CaptureConsole([1, 4, 1])
        sitdown.run_scene(state, con, FORK_ON)
        i = con.find("has warmed since the books closed")
        self.assertIsNotNone(i)
        self.assertIn("offers stand", con.lines[i])
        self.assertIsNotNone(con.find("development build"))
        self.assertIsNone(con.find("That chair is empty"))

    def test_an_unchanged_file_renders_no_disagreement(self):
        state = scene_state(case=20.0, evidence=[(12, 20.0, "seizures")])
        con = CaptureConsole([4, 1])
        sitdown.run_scene(state, con, FORK_ON)
        self.assertIsNone(con.find("has warmed"))

    def test_open_chairs_at_case_85_are_visibly_dangerous(self):
        state = scene_state(case=85.0, evidence=[(10, 85.0, "the ledger fire")])
        con = CaptureConsole([4, 1])
        sitdown.run_scene(state, con, FORK_ON)
        self.assertIsNotNone(con.find("dignified way to lose"))
        self.assertIsNotNone(con.find("near-suicidal"))
        verdicts = {v.chair: v for v in
                    sitdown.evaluate_chairs(state.sitdown_snapshot,
                                            state.evidence)}
        self.assertTrue(verdicts["straight"].available)
        self.assertTrue(verdicts["war"].available)

    def test_blockers_are_structured_with_calendar_precedence(self):
        # Both gates fail: calendar wins, one reason, no closing record —
        # and the gate facts carry requirement AND actual (rev. 6).
        both = {v.chair: v for v in sitdown.evaluate_chairs(
            SitdownSnapshot(21, 72.0, 1),
            [Evidence(day=9, magnitude=72.0, kind="physical", why="a fire")])}
        self.assertEqual(both["partner"].blocker, "calendar")
        self.assertEqual(both["partner"].requirement, 10.0)
        self.assertEqual(both["partner"].actual, 9.0)
        self.assertEqual(both["partner"].closed_by, "")
        # Case alone: requirement, actual, and the closing record.
        case_only = {v.chair: v for v in sitdown.evaluate_chairs(
            SitdownSnapshot(13, 72.0, 1),
            [Evidence(day=9, magnitude=72.0, kind="physical", why="a fire")])}
        self.assertEqual(case_only["partner"].blocker, "case")
        self.assertEqual(case_only["partner"].requirement, 70.0)
        self.assertEqual(case_only["partner"].actual, 72.0)
        self.assertEqual(case_only["partner"].closed_by, "a fire")
        seated = {v.chair: v for v in sitdown.evaluate_chairs(
            SitdownSnapshot(13, 10.0, 0), [])}
        self.assertIsNone(seated["straight"].blocker)
        self.assertEqual(seated["partner"].case_gate, 70.0)   # for the note

    def test_frozen_65_live_90_offers_stand_but_danger_is_live(self):
        # Eligibility belongs to the frozen file; present danger to the
        # live one. The frozen offers stand AND both open chairs carry
        # this morning's warnings.
        state = scene_state(case=65.0, evidence=[(12, 65.0, "seizures")])
        state.evidence.append(Evidence(day=12, magnitude=25.0,
                                       kind="witness", why="an informant"))
        view = sitdown.build_view(state.sitdown_snapshot, state.evidence)
        self.assertEqual(view.live_case, 90.0)
        self.assertTrue(view.live_danger)
        self.assertTrue(view.offers_would_change)
        con = CaptureConsole([4, 1])
        sitdown.run_scene(state, con, FORK_ON)
        self.assertIsNotNone(con.find("offers stand"))
        self.assertIsNotNone(con.find("dignified way to lose"))
        self.assertIsNotNone(con.find("near-suicidal"))

    def test_a_case_rejection_states_the_math_and_the_record(self):
        state = scene_state(case=72.0, evidence=[(9, 72.0, "a fire")])
        con = CaptureConsole([4, 1])
        sitdown.run_scene(state, con, FORK_ON)
        i = con.find("required a file below 70")
        self.assertIsNotNone(i)
        self.assertIn("72", con.lines[i])
        self.assertIsNotNone(con.find("What closed it: a fire"))

    def test_a_calendar_rejection_states_the_days(self):
        state = scene_state(payoff_day=21)     # Partner: needs 10, has 9
        con = CaptureConsole([4, 1])
        sitdown.run_scene(state, con, FORK_ON)
        i = con.find("needed 10 days on the calendar")
        self.assertIsNotNone(i)
        self.assertIn("9 remain", con.lines[i])

    def test_the_live_ledger_shares_the_case_fold(self):
        # The 3.12-sensitive sequence: folds to 61.50000000000001
        # sequentially, sums to 61.5 compensated. The view's live Case
        # must agree with State.case bit for bit because they are the
        # SAME fold_case call, not a copy of its arithmetic.
        state = scene_state(case=10.0)
        for amount in [10.0, 5.0, 14.6, 0.5, 8.3, 9.2, 0.5, 8.9, 3.0, 1.5]:
            state.evidence.append(Evidence(day=12, magnitude=amount,
                                           kind="paper", why="x"))
        self.assertEqual(state.case, 61.50000000000001)
        view = sitdown.build_view(state.sitdown_snapshot, state.evidence)
        self.assertEqual(view.live_case, state.case)
        self.assertIs(sitdown.fold_case, models.fold_case)


# ══ Scripted scene input fails closed ═════════════════════════════

class TestSceneScriptExhaustion(unittest.TestCase):
    """Rev. 6: an exhausted script must never fail open into an
    irrevocable commitment — it raises before anything mutates."""

    def test_exhaustion_before_the_chair_selection(self):
        state = scene_state()
        with self.assertRaises(ScriptExhausted):
            sitdown.run_scene(state, CaptureConsole([]), FORK_ON)
        self.assertIsNone(state.branch)
        self.assertEqual(state.act, 1)

    def test_exhaustion_between_selection_and_confirmation(self):
        state = scene_state()
        with self.assertRaises(ScriptExhausted):
            sitdown.run_scene(state, CaptureConsole([4]), FORK_ON)
        self.assertIsNone(state.branch)
        self.assertEqual(state.act, 1)
        # The reload replays the scene, which can now conclude.
        sitdown.run_scene(state, CaptureConsole([4, 1]), FORK_ON)
        self.assertEqual(state.branch, "stand_pat")

    def test_gameplay_prompts_keep_their_safe_fallbacks(self):
        con = ScriptedConsole([])
        self.assertEqual(con.menu("Settle accounts:", ["a", "b"]), 1)
        self.assertEqual(con.ask_int("Pay?", 0, 10, 3), 3)
        self.assertFalse(con.confirm("Ride along?"))


# ══ The paired gate detects absence and drift ═════════════════════

class TestPairedGateMutations(unittest.TestCase):
    """Rev. 6: the standpat gate must prove the feature EXISTS, not just
    that nothing else moved — a disabled sit-down, a drifted prompt, a
    reordered event and a changed answer must each fail a pair that
    reaches the table."""

    @classmethod
    def setUpClass(cls):
        cls.off = equivalence.run_recorded(1, "greedy")
        cls.on = equivalence.run_recorded(1, "greedy", FORK_ON)

    def test_the_reference_pair_reaches_the_table_and_passes(self):
        self.assertTrue(equivalence._scene_expected(self.off["night_facts"]))
        problem, held = equivalence._compare_pair(self.off, self.on)
        self.assertIsNone(problem)
        self.assertTrue(held)

    def test_a_disabled_sitdown_fails_the_gate(self):
        # The review's exact probe: turn due() off and replay. Every
        # equivalence surface still matches — the existence check is
        # what catches it.
        with mock.patch.object(sitdown, "due", lambda s: False):
            broken = equivalence.run_recorded(1, "greedy", FORK_ON)
        self.assertEqual(broken["raw_trace"], self.off["raw_trace"])
        self.assertEqual(broken["nights"], self.off["nights"])
        problem, held = equivalence._compare_pair(self.off, broken)
        self.assertIsNotNone(problem)
        self.assertIn("no sit-down was held", problem)
        self.assertFalse(held)

    def test_an_unexpected_scene_fails_the_gate(self):
        off_no_payoff = dict(self.off)
        off_no_payoff["night_facts"] = [[d, e, None] for d, e, _ in
                                        self.off["night_facts"]]
        problem, _ = equivalence._compare_pair(off_no_payoff, self.on)
        self.assertIsNotNone(problem)
        self.assertIn("expects none", problem)

    def test_every_schema_mutation_is_caught(self):
        self.assertIsNone(equivalence._scene_contract(
            copy.deepcopy(equivalence.STANDPAT_SCENE)))
        mutations = {
            "missing event": lambda m: m.pop(1),
            "extra event": lambda m: m.append(copy.deepcopy(m[1])),
            "reordered events": lambda m: m.reverse(),
            "changed prompt": lambda m: m[0].__setitem__(1, "Pick a chair:"),
            "changed option": lambda m: m[0][2].__setitem__(
                0, "The Crooked Path"),
            "changed answer": lambda m: m[0].__setitem__(3, 0),
            "changed namespace": lambda m: m[1].__setitem__(0, "scene"),
        }
        for name, mutate in mutations.items():
            mutated = copy.deepcopy(equivalence.STANDPAT_SCENE)
            mutate(mutated)
            self.assertIsNotNone(equivalence._scene_contract(mutated), name)
            bad = dict(self.on)
            bad["scene_trace"] = mutated
            problem, _ = equivalence._compare_pair(self.off, bad)
            self.assertIsNotNone(problem, name)


# ══ Bots and the scene: zero decision RNG ═════════════════════════

class TestBotSceneDeterminism(unittest.TestCase):
    def test_scene_menu_is_rng_free_for_both_bot_families(self):
        for bot in (BotConsole(random.Random(3)),
                    GreedyBot(random.Random(3))):
            before = bot.rng.getstate()
            ans = bot.scene_menu("sitdown", "Your chair:", ["a", "b", "c"])
            self.assertEqual(ans, 2)
            self.assertEqual(bot.rng.getstate(), before)

    def test_a_real_scene_leaves_bot_rng_untouched(self):
        state = scene_state()
        bot = BotConsole(random.Random(7))
        before = bot.rng.getstate()
        sitdown.run_scene(state, bot, FORK_ON)
        self.assertEqual(bot.rng.getstate(), before)
        self.assertEqual(state.branch, "stand_pat")


# ══ BranchState constructors and validation ═══════════════════════

class TestBranchStateValidation(unittest.TestCase):
    def test_constructors_produce_valid_states(self):
        validate_branch_state("straight", BranchState.straight())
        validate_branch_state("partner",
                              BranchState.partner(points_due_day=19))
        validate_branch_state("war", BranchState.war(war_target="vinnie",
                                                     declared_day=14,
                                                     starting_strength=70))
        validate_branch_state("quiet_sale", BranchState.quiet_sale())

    def test_stand_pat_and_prefork_require_no_branch_state(self):
        validate_branch_state(None, None)
        validate_branch_state("stand_pat", None)
        with self.assertRaises(ValueError):
            validate_branch_state("stand_pat", BranchState())
        with self.assertRaises(ValueError):
            validate_branch_state(None, BranchState())

    def test_active_branches_require_their_state_and_fields(self):
        with self.assertRaises(ValueError):
            validate_branch_state("quiet_sale", None)
        with self.assertRaises(ValueError):
            validate_branch_state("partner", BranchState())   # no due day
        with self.assertRaises(ValueError):
            validate_branch_state("war", BranchState())   # no campaign
        with self.assertRaises(ValueError):
            validate_branch_state("quiet_sale",
                                  BranchState(diligence_day=0))

    def test_mixed_branch_payloads_are_rejected(self):
        mixed = BranchState(diligence_day=1, war_pay_paid=40)
        with self.assertRaises(ValueError):
            validate_branch_state("quiet_sale", mixed)
        with self.assertRaises(ValueError):
            validate_branch_state("straight",
                                  BranchState(disposal_runs_left=3,
                                              points_missed=1))

    def test_unknown_branches_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_branch_state("golf_course", BranchState())


# ══ Save round trips ══════════════════════════════════════════════

class TestSaveRoundTrips(unittest.TestCase):
    def test_pending_snapshot_round_trips(self):
        state = scene_state(payoff_day=12, case=65.0)
        restored = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(restored.sitdown_snapshot, state.sitdown_snapshot)
        self.assertTrue(sitdown.due(restored))

    def test_post_selection_round_trips(self):
        state = scene_state()
        sitdown.run_scene(state, CaptureConsole([4, 1]), FORK_ON)
        restored = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(restored.branch, "stand_pat")
        self.assertEqual(restored.act, 2)
        self.assertIsNone(restored.branch_state)
        self.assertFalse(sitdown.due(restored))

    def test_a_snapshot_must_be_a_lock_up_at_the_load_boundary(self):
        # P4b.1b review: `payoff_day=13.0` passed every arithmetic the
        # scene does (`30 - 13.0` compares fine) and set a PERMANENT
        # points schedule from a day that is not a day. The refusal
        # binds at the SHARED persistence boundary, not inside the
        # branch that noticed it — every consumer of the snapshot
        # deserves the same guarantee.
        good = scene_state(payoff_day=12, case=65.0)
        good.evidence.append(Evidence(day=1, magnitude=1.0,
                                      kind="physical", why="a crate"))
        save.state_from_dict(save.state_to_dict(good))       # baseline
        for field, bad in (
            ("payoff_day", 13.0),            # not a whole day
            ("payoff_day", True),            # a bool is not a day
            ("payoff_day", "12"),            # nor a string
            ("payoff_day", 0),               # before the calendar
            ("payoff_day", 99),              # after the run's reach
            ("payoff_day", 11),              # disagrees with the ledger
            ("evidence_count_at_lockup", 1.0),
            ("evidence_count_at_lockup", True),
            ("evidence_count_at_lockup", -1),
            ("evidence_count_at_lockup", 99),   # beyond the ledger
            ("case_at_lockup", "65"),
            ("case_at_lockup", True),
            ("case_at_lockup", -1.0),
            # THE Case domain (P4b.1b review). Type plus `< 0` let
            # all three of these through: 101 is not a Case the fold
            # could produce, infinity is not a number of evidence
            # points, and NaN defeats a two-inequality bounds check
            # outright, because every comparison against it is False.
            ("case_at_lockup", 100.1),
            ("case_at_lockup", 101.0),
            ("case_at_lockup", float("nan")),
            ("case_at_lockup", float("inf")),
            ("case_at_lockup", float("-inf")),
        ):
            with self.subTest(f"{field}={bad!r}"):
                payload = save.state_to_dict(good)
                payload["sitdown_snapshot"][field] = bad
                with self.assertRaises(ValueError):
                    save.state_from_dict(payload)

    def test_the_case_domain_is_the_folds_own_and_its_ends_are_valid(self):
        # One home, shared with the fold: the persisted bound IS the
        # interval gameplay clamps into, so the endpoints must load.
        self.assertEqual((models.CASE_MIN, models.CASE_MAX), (0.0, 100.0))
        for value in (0, 0.0, 100, 100.0, 50.5):
            with self.subTest(value=value):
                state = scene_state(payoff_day=12, case=value)
                loaded = save.state_from_dict(save.state_to_dict(state))
                self.assertEqual(loaded.sitdown_snapshot.case_at_lockup,
                                 value)

    def test_the_domain_predicate_and_the_fold_agree(self):
        # The fold cannot produce a value the predicate refuses —
        # asserted over the fold's own output rather than by reading
        # its source, so the two cannot drift.
        for magnitude in (0.0, 1.0, 99.0, 100.0, 250.0):
            with self.subTest(magnitude=magnitude):
                folded = models.fold_case(
                    [Evidence(day=1, magnitude=magnitude, kind="physical",
                              why="x")])
                self.assertTrue(models.case_in_domain(folded), folded)

    def test_a_snapshot_reconciles_with_the_payoff_it_records(self):
        # Two answers to "when was Carmine paid" would silently
        # reprice a chair, since R is derived from the snapshot.
        state = scene_state(payoff_day=12)
        payload = save.state_to_dict(state)
        payload["debt_paid_day"] = None
        with self.assertRaises(ValueError):
            save.state_from_dict(payload)

    def test_the_lock_up_count_may_equal_the_ledger_length(self):
        # The boundary the bound turns on: the count is a PREFIX
        # length, and freezing after the last record is the ordinary
        # case, not an off-by-one.
        state = scene_state(payoff_day=12, case=65.0,
                            evidence=[(11, 65.0, "seizures")])
        self.assertEqual(state.sitdown_snapshot.evidence_count_at_lockup,
                         len(state.evidence))
        save.state_from_dict(save.state_to_dict(state))

    def test_older_v3_payloads_load_the_snapshot_as_none(self):
        d = save.state_to_dict(new_state())
        del d["sitdown_snapshot"]
        self.assertIsNone(save.state_from_dict(d).sitdown_snapshot)

    def test_exact_round_trip_guard_still_holds(self):
        state = scene_state(payoff_day=12, case=65.0)
        d = save.state_to_dict(state)
        self.assertEqual(save.state_to_dict(save.state_from_dict(d)), d)

    def test_mixed_branch_payloads_are_refused_on_load(self):
        state = new_state()
        d = save.state_to_dict(state)
        d["branch"] = "quiet_sale"
        d["branch_state"] = save.asdict(
            BranchState(diligence_day=1, war_pay_paid=40))
        with self.assertRaises(ValueError):
            save.state_from_dict(d)
        d["branch"] = "stand_pat"
        d["branch_state"] = save.asdict(BranchState())
        with self.assertRaises(ValueError):
            save.state_from_dict(d)


# ══ Whole-run behavior under the flag ═════════════════════════════

class TestFlagAtRunLevel(unittest.TestCase):
    def test_truncated_runs_are_identical_under_the_flag(self):
        # --max-days shorter than any payoff: the fork never fires and
        # the run is byte-identical (the full-length version of this is
        # the paired standpat harness).
        for seed in range(4):
            off = game.run(seed, BotConsole(random.Random(seed)), max_days=6)
            on = game.run(seed, BotConsole(random.Random(seed)), max_days=6,
                          config=FORK_ON)
            d_off, d_on = save.state_to_dict(off), save.state_to_dict(on)
            self.assertEqual(d_off, d_on, f"seed {seed}")
            self.assertIsNone(on.sitdown_snapshot)


if __name__ == "__main__":
    unittest.main()
