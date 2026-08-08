"""Strategy bots: heuristic players used to probe the economy, not to be it.

Each bot answers the same prompts a human sees. They exist to expose
economic behavior across many seeds (see bench.py); human play remains
the test of fun.
"""

import random
import re
from typing import ClassVar

from .ui import Console


class StrategyBot(Console):
    """Base heuristic player. Subclasses tune the knobs.

    Knobs:
      cargo_frac    fraction of available cargo space actually loaded (0..1)
      cover_stops   preferred legit stops on a route (capped by wagon space)
      debt_float    working capital held back from Carmine
      ride_along    whether the boss rides the route
      launder_all   launder everything (over the ceiling) vs. ceiling only
      do_crime      buy supplier stock and load cargo at all
      do_raids      read in crew and attempt night jobs
      menu_prefs    label-substring -> weight, once per day each
    """

    cargo_frac = 1.0
    cover_stops = 8
    debt_float = 1500
    ride_along = True
    launder_all = False
    do_crime = True
    do_raids = False

    MENU_PREFS: ClassVar[list[tuple[str, float]]] = [
        ("Sell", 10),
        ("Play it cool", 8),
        ("Slip past", 8),
        ("Take him down quietly", 6),
        ("Pay Carmine", 7),
        ("Launder dirty cash", 6),
        ("Buy from today's supplier", 6),
        ("Buy ingredients", 5),
        ("Plan tonight's route", 5),
        ("Lock up", 1),
        ("Open for service", 1),
    ]
    AVOID: ClassVar[list[str]] = [
        "Cancel", "Never mind", "Abort", "Floor it", "Go loud", "Rush him",
             "Skip this stop", "Haggle", "Back", "No route", "Plan a night job",
             "Staff", "Improvements", "Market board", "Kitchen policy",
             "Talk to a rival", "Move stash", "No supplier"]

    def __init__(self, rng: random.Random, verbose: bool = False) -> None:
        super().__init__()
        self.rng = rng
        self.quiet = not verbose
        self._done_today: set[str] = set()

    # ── plumbing ─────────────────────────────────────────────────
    def say(self, text: str = "") -> None:
        if "— MORNING" in text:
            self._done_today = set()
        super().say(text)

    def pause(self) -> None:
        pass

    def _score(self, label: str) -> float:
        if any(a in label for a in self.AVOID):
            return -5 + self.rng.random()
        for key, w in self.MENU_PREFS:
            if key in label:
                if key in self._done_today:
                    return 0.5 + self.rng.random()
                return w + self.rng.random()
        return self.rng.random()

    # ── decisions ────────────────────────────────────────────────
    def menu(self, prompt: str, options: list[str]) -> int:
        special = self._special_menu(prompt, options)
        if special is not None:
            return max(0, min(special, len(options) - 1))
        scores = [self._score(o) for o in options]
        pick = max(range(len(options)), key=lambda i: scores[i])
        for key, _ in self.MENU_PREFS:
            if key in options[pick]:
                self._done_today.add(key)
        return pick

    def _special_menu(self, prompt: str, options: list[str]) -> int | None:
        if prompt.startswith("Run today's route where?"):
            best, best_s = 0, -99.0
            for i, o in enumerate(options[:-1]):
                m = re.search(r"heat (\d+)", o)
                s = self.rng.random() * 2 - (int(m.group(1)) if m else 0) * 0.02
                if s > best_s:
                    best, best_s = i, s
            return best
        if prompt.startswith(("Hit whom?", "The job:", "Read in whom?", "Applicants:")):
            return 0
        if prompt.startswith("Crew ("):
            m = re.match(r"Crew \((\d+) picked", prompt)
            picked = int(m.group(1)) if m else 0
            return 0 if picked < 2 else len(options) - 1
        return None

    def ask_int(self, prompt: str, lo: int, hi: int, default: int = 0) -> int:
        if lo >= hi:
            return lo
        if prompt.startswith("Load"):
            return int(hi * self.cargo_frac) if self.do_crime else lo
        if prompt.startswith("Buy how many units"):
            return hi if self.do_crime else lo
        if prompt.startswith("Legit pizza stops"):
            return min(hi, self.cover_stops)
        if prompt.startswith("Pay Carmine"):
            m = re.search(r"debt \$([\d,]+)", prompt)
            debt = int(m.group(1).replace(",", "")) if m else hi
            if debt <= 2500 <= hi or hi >= debt:
                return hi               # close it out — don't tip the interest
            return max(lo, hi - self.debt_float)
        if prompt.startswith("Run how much"):
            if self.launder_all:
                return hi
            return default if default > 0 else hi
        return default

    def confirm(self, prompt: str) -> bool:
        if prompt.startswith("Ride along"):
            return self.ride_along
        return False


class GreedyBot(StrategyBot):
    """Max cargo, decent cover, boss in the car, launders under the ceiling."""


class CautiousBot(StrategyBot):
    """Half loads, full cover, steady debt payments, never over the ceiling."""
    cargo_frac = 0.5
    cover_stops = 12
    debt_float = 800


class PizzaFirstBot(StrategyBot):
    """Runs the restaurant straight: no product, no supplier, no rides."""
    do_crime = False
    ride_along = False
    cover_stops = 12
    debt_float = 400
    MENU_PREFS: ClassVar[list[tuple[str, float]]] = [
        ("Pay Carmine", 7),
        ("Launder dirty cash", 6),
        ("Buy ingredients", 6),
        ("Improvements", 4),
        ("Plan tonight's route", 4),
        ("Lock up", 1),
        ("Open for service", 1),
    ]
    AVOID: ClassVar[list[str]] = \
        [a for a in StrategyBot.AVOID if a != "Improvements"] + \
        ["Buy from today's supplier"]

    def _special_menu(self, prompt: str, options: list[str]) -> int | None:
        if prompt.startswith("Improvements"):
            # Buy the first affordable upgrade once a day, then leave.
            if "improv_done" in self._done_today:
                return len(options) - 1
            self._done_today.add("improv_done")
            m = re.search(r"clean \$([\d,]+)", prompt)
            clean = int(m.group(1).replace(",", "")) if m else 0
            for i, o in enumerate(options[:-1]):
                cm = re.search(r"— \$([\d,]+) clean", o)
                if cm and int(cm.group(1).replace(",", "")) <= clean:
                    return i
            return len(options) - 1
        return super()._special_menu(prompt, options)


class CrimeHeavyBot(StrategyBot):
    """Full cargo, minimal cover, reads in crew, raids, launders everything."""
    cargo_frac = 1.0
    cover_stops = 2
    debt_float = 2500
    launder_all = True
    do_raids = True
    MENU_PREFS: ClassVar[list[tuple[str, float]]] = [
        ("Sell", 10),
        ("Play it cool", 8),
        ("Slip past", 8),
        ("Take him down quietly", 6),
        ("Pay Carmine", 7),
        ("Launder dirty cash", 6),
        ("Buy from today's supplier", 6),
        ("Plan tonight's route", 5),
        ("Read someone in", 5),
        ("Staff", 4),
        ("Plan a night job", 4),
        ("Buy ingredients", 3),
        ("Back", 1.2),
        ("Enough", 1.2),
        ("Lock up", 1),
        ("Open for service", 1),
    ]
    AVOID: ClassVar[list[str]] = [
        "Cancel", "Never mind", "Abort", "Floor it", "Skip this stop",
             "Haggle", "No route", "Improvements", "Market board",
             "Kitchen policy", "Talk to a rival", "Move stash", "No supplier",
             "Give a raise", "Let someone go", "Hire"]


BOTS = {
    "greedy": GreedyBot,
    "cautious": CautiousBot,
    "pizza": PizzaFirstBot,
    "crime": CrimeHeavyBot,
}
