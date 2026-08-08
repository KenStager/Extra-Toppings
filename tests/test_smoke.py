"""Smoke tests: the whole 30-day loop must survive bot play across many seeds."""

import random
import unittest

from extra_toppings import data
from extra_toppings.bot import GreedyBot
from extra_toppings.game import run
from extra_toppings.models import new_state
from extra_toppings.ui import BotConsole


class TestFullRuns(unittest.TestCase):
    def test_random_bot_survives_the_engine(self):
        """Chaos-monkey play must never crash the loop or corrupt state."""
        for seed in range(20):
            con = BotConsole(random.Random(seed))
            state = run(seed, con)
            self.assertIsNotNone(state.game_over)
            self.assertLessEqual(state.day, data.DEBT_DUE_DAY + 1)
            # Money and stock never go structurally negative.
            self.assertGreaterEqual(state.dirty, 0)
            self.assertGreaterEqual(state.warehouse_cash, 0)
            for units in state.shop_stash.values():
                self.assertGreaterEqual(units, 0)

    def test_game_is_winnable_but_not_trivial(self):
        """A simple sensible strategy beats the debt on some seeds, not all."""
        wins = 0
        for seed in range(12):
            state = run(seed, GreedyBot(random.Random(seed)))
            if state.debt_paid_day is not None:
                wins += 1
        self.assertGreaterEqual(wins, 2, "debt should be beatable by decent play")
        self.assertLess(wins, 12, "the deadline should still bite sometimes")

    def test_deterministic_with_seed(self):
        results = []
        for _ in range(2):
            con = BotConsole(random.Random(42))
            state = run(42, con)
            results.append((state.game_over, state.clean, state.dirty,
                            state.debt, state.case))
        self.assertEqual(results[0], results[1])


class TestVerticalSliceInventory(unittest.TestCase):
    """The design doc's checklist for the first playable version."""

    def test_slice_contents(self):
        self.assertEqual(len(data.DISTRICTS), 4)
        self.assertEqual(len(data.GOODS), 4)
        self.assertEqual(len(data.RIVALS), 2)
        self.assertEqual(len(data.EMPLOYEE_POOL), 8)
        self.assertEqual(len(data.RAID_OBJECTIVES), 3)
        self.assertEqual(data.DEBT_DUE_DAY, 30)

    def test_new_state_shape(self):
        s = new_state()
        self.assertEqual(len(s.hired()), 2)          # Rosa and Tony
        self.assertEqual(s.debt, data.START_DEBT)
        self.assertIsNone(s.warehouse)                # rented, not owned, later
        self.assertEqual(len(s.rivals), 2)


if __name__ == "__main__":
    unittest.main()
