"""The released-set activations (§7): the released branch set has one
canonical home, the CLI flag consumes it, and exactly the released
chairs are actionable — the Straight Path and the Quiet Sale together
on the P2 merge approval, the Harbor War on the P3 merge disposition.
The one unbuilt chair (Carmine's Partner) still renders with its true
verdict and refuses with the development-build marker."""

import os
import unittest
from unittest import mock

from extra_toppings import sitdown
from extra_toppings.__main__ import _config_from_env
from extra_toppings.models import (ACTIVE_BRANCHES, RELEASED_BRANCHES,
                                   SitdownSnapshot, new_state)
from extra_toppings.ui import ScriptedConsole


class CaptureConsole(ScriptedConsole):
    def __init__(self, script=None):
        super().__init__(script)
        self.lines: list = []

    def say(self, text=""):
        self.lines.append(text)

    def bullet(self, text):
        self.lines.append(f"• {text}")

    def find(self, fragment):
        for i, line in enumerate(self.lines):
            if fragment in line:
                return i
        return None


def at_the_table():
    state = new_state()
    state.debt = 0
    state.debt_paid_day = 13
    state.day = 14
    state.sitdown_snapshot = SitdownSnapshot(13, 0.0, 0)
    return state


class TestTheReleasedSet(unittest.TestCase):
    def test_one_canonical_home(self):
        self.assertEqual(RELEASED_BRANCHES,
                         frozenset({"straight", "quiet_sale", "war"}))
        self.assertTrue(RELEASED_BRANCHES <= ACTIVE_BRANCHES)

    def test_the_cli_flag_consumes_it(self):
        with mock.patch.dict(os.environ, {"EXTRA_TOPPINGS_FORK": "1"}):
            config = _config_from_env()
        self.assertTrue(config.fork_enabled)
        self.assertEqual(config.enabled_branches, RELEASED_BRANCHES)

    def test_without_the_flag_the_fork_stays_off(self):
        env = {k: v for k, v in os.environ.items()
               if k != "EXTRA_TOPPINGS_FORK"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = _config_from_env()
        self.assertFalse(config.fork_enabled)
        self.assertEqual(config.enabled_branches, frozenset())


class TestExactlyTheReleasedChairsAreActionable(unittest.TestCase):
    def _config(self):
        with mock.patch.dict(os.environ, {"EXTRA_TOPPINGS_FORK": "1"}):
            return _config_from_env()

    def test_the_straight_path_commits(self):
        state = at_the_table()
        sitdown.run_scene(state, CaptureConsole([0, 1]), self._config())
        self.assertEqual(state.branch, "straight")
        self.assertEqual(state.act, 2)

    def test_the_quiet_sale_commits(self):
        state = at_the_table()
        sitdown.run_scene(state, CaptureConsole([3, 1]), self._config())
        self.assertEqual(state.branch, "quiet_sale")
        self.assertEqual(state.act, 2)

    def test_the_harbor_war_commits(self):
        state = at_the_table()
        # Chair, name the first live rival (0 reconsiders), declare.
        sitdown.run_scene(state, CaptureConsole([2, 1, 1]), self._config())
        self.assertEqual(state.branch, "war")
        self.assertEqual(state.act, 2)
        self.assertEqual(state.branch_state.campaigns[0].rival_key,
                         [k for k, r in state.rivals.items() if r.alive][0])

    def test_partner_still_carries_the_dev_build_marker(self):
        state = at_the_table()
        con = CaptureConsole([1, 4, 1])   # partner, refuse, stand pat
        sitdown.run_scene(state, con, self._config())
        self.assertIsNotNone(con.find("development build"))
        self.assertIsNone(con.find("That chair is empty"))
        self.assertEqual(state.branch, "stand_pat")


if __name__ == "__main__":
    unittest.main()
