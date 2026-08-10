"""Raid pricing: raids must stop being an ATM. Targets harden with each
attempt, patterns feed the Case, hands and storage bound the haul, the
decoy protects one wagonload, and ledger leverage is single-use."""

import random
import unittest

from extra_toppings import models, data, market, raids, rivals
from extra_toppings.models import new_state
from extra_toppings.ui import BotConsole, ScriptedConsole


def fresh(seed=1):
    rng = random.Random(seed)
    state = new_state()
    market.roll_prices(state, rng)
    return state, rng


def crew_for(state, n=3):
    crew = state.employees[:n]
    for e in crew:
        e.hired = e.aware = True
    return crew


def steal_plan(state, wagon_free=True):
    return {"rival": "vinnie", "objective": "steal_stock",
            "team": [e for e in crew_for(state) if e.available],
            "armed": False, "wagon_free": wagon_free}


class TestTargetHardening(unittest.TestCase):
    def test_every_attempt_raises_alertness(self):
        state, rng = fresh(41)
        crew_for(state)
        v = state.rivals["vinnie"]
        self.assertEqual(v.alertness, 0.0)
        raids.run_raid(state, steal_plan(state), BotConsole(random.Random(41)), rng)
        self.assertGreater(v.alertness, 0.0)

    def test_alert_targets_are_harder_to_rob(self):
        def haul_total(alertness):
            total = 0
            for seed in range(60):
                state, rng = fresh(seed)
                state.warehouse = {}          # storage is not the confound here
                state.rivals["vinnie"].alertness = alertness
                before = sum(state.shop_stash.values())
                raids.run_raid(state, steal_plan(state),
                               BotConsole(random.Random(seed)), rng)
                total += sum(state.shop_stash.values()) \
                    + sum(state.warehouse.values()) - before
            return total
        self.assertLess(haul_total(8.0), haul_total(0.0) * 0.7)

    def test_alertness_decays_when_left_alone(self):
        state, rng = fresh(41)
        v = state.rivals["vinnie"]
        v.alertness = 5.0
        v.relation = 0
        rivals.rival_phase(state, ScriptedConsole(), rng)
        self.assertLess(v.alertness, 5.0)
        self.assertGreater(v.alertness, 3.0)   # slow decay, not a reset


class TestPatternEvidence(unittest.TestCase):
    def _case_delta_for_success(self, prior_raids):
        """Identical successful raid, differing only in how many jobs the
        crew has already pulled. Seed chosen so the job succeeds cleanly."""
        for seed in range(50):
            state, _ = fresh(42)
            crew_for(state)
            state.raids_led = prior_raids
            before = state.case
            raids.run_raid(state, steal_plan(state),
                           BotConsole(random.Random(seed)),
                           random.Random(seed))
            if state.raids_led == prior_raids + 1:     # success
                return state.case - before
        self.fail("no successful raid found in 50 seeds")

    def test_repeat_raids_feed_the_case_even_when_quiet(self):
        first = self._case_delta_for_success(0)
        fourth = self._case_delta_for_success(3)
        self.assertGreater(fourth, first,
                           "later jobs must cost more Case than the first")
        self.assertGreaterEqual(fourth - first, 3,
                                "the pattern premium must be material")


class TestCarryAndStorage(unittest.TestCase):
    def _run_haul(self, seed, wagon_free, warehouse=True):
        state, rng = fresh(seed)
        state.shop_stash = {}
        if warehouse:
            state.warehouse = {}
        plan = steal_plan(state, wagon_free=wagon_free)
        raids.run_raid(state, plan, BotConsole(random.Random(seed)), rng)
        bulk = state.stash_bulk(state.shop_stash)
        if state.warehouse:
            bulk += state.stash_bulk(state.warehouse)
        return state, bulk, len(plan["team"])

    def test_haul_bounded_by_crew_hands(self):
        for seed in range(40):
            _, bulk, _ = self._run_haul(seed, wagon_free=True)
            self.assertLessEqual(bulk, 8 * 3)      # 3 crew with the wagon

    def test_no_wagon_means_half_the_hands(self):
        for seed in range(40):
            _, bulk, _ = self._run_haul(seed, wagon_free=False)
            self.assertLessEqual(bulk, 4 * 3)

    def test_haul_never_overflows_storage(self):
        for seed in range(40):
            state, _, _ = self._run_haul(seed, wagon_free=True, warehouse=False)
            self.assertLessEqual(state.stash_bulk(state.shop_stash),
                                 state.shop.stash_cap)


class TestConsumableLedger(unittest.TestCase):
    def test_leaning_on_the_ledger_spends_it(self):
        state, rng = fresh(43)
        v = state.rivals["vinnie"]
        v.ledger_stolen = True
        # negotiate: pick vinnie (idx 1), then the ledger option (idx 2)
        rivals.negotiate(state, ScriptedConsole([1, 2]), rng)
        self.assertFalse(v.ledger_stolen)
        # A second visit no longer offers the ledger play (menu is 3 wide:
        # peace offering / truce / back) — leaning again is impossible.
        dirty_before = state.dirty
        rivals.negotiate(state, ScriptedConsole([1, 2]), rng)
        self.assertEqual(state.dirty, dirty_before)


class TestDecoyCap(unittest.TestCase):
    def test_decoy_protects_exactly_one_wagonload(self):
        state, rng = fresh(44)
        state.shop_stash = {"mushrooms": 40}       # bulk 40 > wagon 24
        state.rivals["vinnie"].warning = models.RaidWarning(1, models.HOME_SHOP_KEY)
        raids.incoming_raid(state, "vinnie", ScriptedConsole([1]), rng)
        self.assertEqual(state.stash_bulk(state.shop_stash), data.VEHICLE_CARGO)

    def test_decoy_still_saves_a_small_stash_whole(self):
        state, rng = fresh(44)
        state.shop_stash = {"mushrooms": 10}       # bulk 10 <= wagon 24
        state.rivals["vinnie"].warning = models.RaidWarning(1, models.HOME_SHOP_KEY)
        raids.incoming_raid(state, "vinnie", ScriptedConsole([1]), rng)
        self.assertEqual(state.shop_stash["mushrooms"], 10)


class CaptureConsole(ScriptedConsole):
    """Scripted answers plus a record of everything said to the player."""

    def __init__(self, script=None):
        super().__init__(script)
        self.lines: list = []

    def say(self, text=""):
        self.lines.append(text)

    def bullet(self, text):
        self.lines.append(text)

    def menu(self, prompt, options):
        self.lines.extend(options)
        return super().menu(prompt, options)


class TestExpectedValueDeclines(unittest.TestCase):
    """Review acceptance: expected DOLLARS per attempt — not merely success
    rate — must decline across repeated raids on one target."""

    def test_repeat_raids_pay_less_per_attempt(self):
        n = 400
        totals = [0.0, 0.0, 0.0]
        for seed in range(n):
            rng = random.Random(seed)
            state = new_state()
            market.roll_prices(state, rng)
            state.warehouse = {}
            crew = crew_for(state)
            for attempt in range(3):
                def value(s):
                    return sum(u * data.GOODS[g]["base"]
                               for st in (s.shop_stash, s.warehouse or {})
                               for g, u in st.items())
                before = value(state)
                plan = {"rival": "vinnie", "objective": "steal_stock",
                        "team": [e for e in crew if e.available],
                        "armed": False, "wagon_free": True}
                if not plan["team"]:
                    break
                raids.run_raid(state, plan,
                               BotConsole(random.Random(seed * 3 + attempt)), rng)
                totals[attempt] += value(state) - before
                for e in crew:
                    e.injured_days = 0
        self.assertLess(totals[2], totals[0] * 0.85,
                        f"attempt 3 must pay materially less: {totals}")


class TestSurvivorCarry(unittest.TestCase):
    """Review acceptance: extraction capacity uses the crew that reached
    the door, not the crew that walked in."""

    def test_downed_crew_carry_nothing_home(self):
        state, rng = fresh(45)
        state.shop_stash = {}
        state.warehouse = {}
        crew = crew_for(state)
        survivors = crew[:2]                     # one didn't make it upright
        plan = {"rival": "vinnie", "objective": "steal_stock",
                "team": list(crew), "armed": False, "wagon_free": True}
        rspec = data.RIVALS["vinnie"]
        raids._payoff(state, plan, state.rivals["vinnie"], rspec,
                      ScriptedConsole(), rng, True, survivors)
        bulk = state.stash_bulk(state.shop_stash)             + state.stash_bulk(state.warehouse)
        self.assertLessEqual(bulk, 8 * 2)


class TestQuietDayDecay(unittest.TestCase):
    """Review acceptance: alertness decays only on genuinely quiet days —
    never on the night of the raid itself."""

    def test_no_decay_on_the_night_of_the_raid(self):
        state, rng = fresh(46)
        v = state.rivals["vinnie"]
        v.alertness = 6.0
        v.relation = 0
        v.last_raided_day = state.day            # hit tonight
        rivals.rival_phase(state, ScriptedConsole(), rng)
        self.assertEqual(v.alertness, 6.0)

    def test_decay_resumes_the_next_quiet_day(self):
        state, rng = fresh(46)
        v = state.rivals["vinnie"]
        v.alertness = 6.0
        v.relation = 0
        v.last_raided_day = state.day - 1        # yesterday's job
        rivals.rival_phase(state, ScriptedConsole(), rng)
        self.assertLess(v.alertness, 6.0)


class TestSecurityVisibility(unittest.TestCase):
    """Review acceptance: security level and pattern evidence must be
    visible when the player can still act on them."""

    def test_target_menu_shows_security_level(self):
        state, rng = fresh(47)
        crew_for(state)
        state.rivals["vinnie"].alertness = 5.0
        con = CaptureConsole([3])                # look, then Never mind
        raids.plan_raid(state, con, rng)
        text = "\n".join(con.lines)
        self.assertIn("security hardened", text)
        self.assertIn("security sleepy", text)   # sal, untouched

    def test_pattern_premium_warned_before_committing(self):
        state, rng = fresh(47)
        crew_for(state)
        state.raids_led = 3
        con = CaptureConsole([3])
        raids.plan_raid(state, con, rng)
        text = "\n".join(con.lines)
        self.assertIn("unsolved burglaries", text)
        self.assertIn("Case", text)

    def test_pattern_evidence_announced_when_incurred(self):
        for seed in range(50):
            state, _ = fresh(47)
            crew_for(state)
            state.raids_led = 2
            con = CaptureConsole()
            raids.run_raid(state, steal_plan(state), con, random.Random(seed))
            if state.raids_led == 3:             # success
                text = "\n".join(con.lines)
                self.assertIn("pinned beside the others", text)
                return
        self.fail("no successful raid found to check the announcement")


class TestNoiseTimeout(unittest.TestCase):
    """Issue #4 regression: running out of time BEFORE the last room is a
    failed extraction — no objective, no job counted, abort-grade
    hardening. Driven through run_raid's actual room loop: the crew
    rushes every guard until the noise gives them away."""

    def _noisy_run(self, seed):
        state, rng = fresh(seed)
        state.shop_stash = {}
        state.warehouse = {}
        con = CaptureConsole([2] * 12)      # answer every guard: "Rush him"
        raids.run_raid(state, steal_plan(state), con, random.Random(seed))
        return state, "\n".join(con.lines)

    def test_early_timeout_awards_nothing(self):
        timeouts = successes = 0
        for seed in range(150):
            state, text = self._noisy_run(seed)
            v = state.rivals["vinnie"]
            if "Time's up" in text:
                timeouts += 1
                self.assertEqual(state.raids_led, 0,
                                 "an early timeout must not count as a job")
                self.assertEqual(v.strength,
                                 data.RIVALS["vinnie"]["strength"],
                                 "the stockroom was never reached")
                self.assertEqual(sum(state.shop_stash.values())
                                 + sum(state.warehouse.values()), 0,
                                 "nothing comes home from a failed extraction")
                self.assertEqual(v.alertness, 1.0,
                                 "a timeout hardens like an abort (+1), "
                                 "not a success (+2)")
                home = data.RIVALS["vinnie"]["home"]
                self.assertEqual(state.heat(home), 18.0,
                                 "abort heat (+8) is part of the promise")
                self.assertEqual(v.relation, -20.0,
                                 "abort relation (-10) is part of the promise")
                self.assertIn("nothing but your skins", text)
            elif state.raids_led == 1:
                successes += 1
        self.assertGreater(timeouts, 0,
                           "no early timeout reproduced in 150 seeds")
        self.assertGreater(successes, 0,
                           "the fix must not kill successful jobs")

    def test_final_room_crossing_is_a_loud_success(self):
        """The deliberate exception: crossing the noise threshold in the
        FINAL room completes the job — loudly. The objective is awarded,
        the job is counted, witnesses feed the Case (+5), and the target
        hardens at success grade (+2), not abort grade."""
        found = 0
        for seed in range(150):
            state, text = self._noisy_run(seed)
            v = state.rivals["vinnie"]
            loud = any("witnesses describe" in f for f in state.case_flags)
            if "Time's up" not in text and state.raids_led == 1 and loud:
                found += 1
                self.assertEqual(v.strength,
                                 data.RIVALS["vinnie"]["strength"] - 12,
                                 "the objective must be awarded")
                self.assertEqual(v.alertness, 2.0,
                                 "a loud completion hardens like a success "
                                 "(+2), not an abort (+1)")
                self.assertEqual(state.case, 5.0,
                                 "the loud exit is priced: witness Case +5, "
                                 "and nothing else on a first job")
        self.assertGreater(found, 0,
                           "no final-room crossing reproduced in 150 seeds")


class TestPatternDisplayHonesty(unittest.TestCase):
    """Issue #4 display nit: the warned premium and the incurred premium
    must be the same number — 4.5 reads 4.5, not a ties-to-even 4."""

    def test_planning_warning_shows_exact_premium(self):
        state, rng = fresh(48)
        crew_for(state)
        state.raids_led = 3                  # premium = min(8, 1.5*3) = 4.5
        con = CaptureConsole([3])            # look, then Never mind
        raids.plan_raid(state, con, rng)
        self.assertIn("adds 4.5 Case", "\n".join(con.lines))

    def test_incurred_announcement_matches_the_warning(self):
        for seed in range(80):
            state, _ = fresh(48)
            crew_for(state)
            state.raids_led = 3              # premium = 4.5
            before = state.case
            con = CaptureConsole()
            raids.run_raid(state, steal_plan(state), con, random.Random(seed))
            if state.raids_led == 4:         # success
                self.assertIn("(Case +4.5)", "\n".join(con.lines))
                self.assertGreaterEqual(state.case - before, 4.5)
                return
        self.fail("no successful raid found to check the announcement")


if __name__ == "__main__":
    unittest.main()
