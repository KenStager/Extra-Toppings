"""GreedyBot: a heuristic player. Exists to prove the 30 days are beatable
and to probe balance from the command line (--auto-smart)."""

import random

from .ui import Console


class GreedyBot(Console):
    """Plays the obvious hustle: stock up, run routes, sell, launder, pay debt."""

    MENU_PREFS = [
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
    AVOID = ["Cancel", "Never mind", "Abort", "Floor it", "Go loud", "Rush him",
             "Skip this stop", "Haggle", "Back", "No route", "Plan a night job",
             "Staff", "Improvements", "Market board", "Kitchen policy",
             "Talk to a rival", "Move stash", "No supplier"]

    def __init__(self, rng: random.Random, verbose: bool = False) -> None:
        super().__init__()
        self.rng = rng
        self.quiet = not verbose
        self._done_today: set[str] = set()

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

    def menu(self, prompt: str, options: list[str]) -> int:
        if prompt.startswith("Run today's route where?"):
            # Any district but Cancel; mildly prefer low heat.
            import re
            best, best_s = 0, -99.0
            for i, o in enumerate(options[:-1]):
                m = re.search(r"heat (\d+)", o)
                s = self.rng.random() * 2 - (int(m.group(1)) if m else 0) * 0.02
                if s > best_s:
                    best, best_s = i, s
            return best
        scores = [self._score(o) for o in options]
        pick = max(range(len(options)), key=lambda i: scores[i])
        for key, _ in self.MENU_PREFS:
            if key in options[pick]:
                self._done_today.add(key)
        return pick

    def ask_int(self, prompt: str, lo: int, hi: int, default: int = 0) -> int:
        if lo >= hi:
            return lo
        if prompt.startswith(("Load", "Buy how many units")):
            return hi
        if prompt.startswith("Pay Carmine"):
            import re
            m = re.search(r"debt \$([\d,]+)", prompt)
            debt = int(m.group(1).replace(",", "")) if m else hi
            if debt <= 2500 <= hi or hi >= debt:
                return hi               # close it out — don't tip the interest
            return max(lo, hi - 1500)   # keep working capital for the trade
        if prompt.startswith("Run how much"):
            return default if default > 0 else hi
        return default

    def confirm(self, prompt: str) -> bool:
        if prompt.startswith("Ride along"):
            return True
        return False
