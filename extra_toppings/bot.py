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
        if prompt.startswith("Delivery orders to run"):
            return min(hi, self.cover_stops)
        if prompt.startswith("Pay Carmine"):
            m = re.search(r"debt \$([\d,]+)", prompt)
            debt = int(m.group(1).replace(",", "")) if m else hi
            if debt <= 2500 <= hi or hi >= debt:
                return hi               # close it out — don't tip the interest
            return max(lo, hi - self.debt_float)
        if prompt.startswith("Run how much"):
            # default is tonight's remaining believable allowance
            return hi if self.launder_all else default
        return default

    def confirm(self, prompt: str) -> bool:
        if prompt.startswith("Ride along"):
            return self.ride_along
        return False

    def scene_menu(self, namespace: str, prompt: str, options: list[str]) -> int:
        # Deterministic and RNG-free (§2.7 rev. 5): the sit-down must not
        # consume bot decision RNG. Last option always progresses.
        return len(options) - 1


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





class MarketBot(StrategyBot):
    """A speculator. Reads rumors, news and price boards from the same text a
    human sees, tracks last-known prices per district, and routes toward
    expected margin instead of away from heat. Holds inventory when the
    numbers are poor."""

    cargo_frac = 1.0
    cover_stops = 8
    MENU_PREFS: ClassVar[list[tuple[str, float]]] = [
        ("Market board", 6.5),
        *StrategyBot.MENU_PREFS,
    ]
    AVOID: ClassVar[list[str]] = \
        [a for a in StrategyBot.AVOID if a != "Market board"]

    # News headlines mapped to expected price pressure (good -> multiplier).
    NEWS_SIGNALS: ClassVar[dict[str, dict[str, float]]] = {
        "PORT SEIZURE": {"truffle": 1.9, "hot_honey": 1.4},
        "STADIUM SELLS OUT": {"hot_honey": 1.5, "truffle": 1.3},
        "EMPTIES WAREHOUSE": {"oregano": 0.6, "mushrooms": 0.6},
    }

    def __init__(self, rng: random.Random, verbose: bool = False) -> None:
        super().__init__(rng, verbose)
        from . import data as _data
        self._data = _data
        self._label_to_good = {v["label"]: k for k, v in _data.GOODS.items()}
        self._dlabel_to_key = {v["label"]: k for k, v in _data.DISTRICTS.items()}
        # (district, good) -> (price, day_heard)
        self.known: dict[tuple[str, str], tuple[float, int]] = {}
        self.day = 0
        self.signal: dict[str, float] = {}       # good -> price multiplier belief
        self.signal_days = 0
        self._board_district: str | None = None

    # ── perception: everything comes in through say() ────────────
    def say(self, text: str = "") -> None:
        if "— MORNING" in text:
            self.day += 1
            self._done_today = set()
            if self.signal_days > 0:
                self.signal_days -= 1
                if self.signal_days == 0:
                    self.signal = {}
        s = text.strip()
        m = re.match(r"(?:• )?RUMOR: .*says (.+) moves around \$(\d+) in (.+)", s)
        if m and m.group(1) in self._label_to_good:
            dk = self._dlabel_to_key.get(m.group(3))
            if dk:
                self.known[(dk, self._label_to_good[m.group(1)])] = \
                    (float(m.group(2)), self.day)
        if s.startswith(("• NEWS:", "NEWS:")):
            for key, mults in self.NEWS_SIGNALS.items():
                if key in s:
                    self.signal = dict(mults)
                    self.signal_days = 3
        dm = re.match(r"(.+) — heat \d+", s)
        if dm and dm.group(1) in self._dlabel_to_key:
            self._board_district = self._dlabel_to_key[dm.group(1)]
        pm = re.match(r"(.+?)\s{2,}\$([\d,]+)/unit", s)
        if pm and self._board_district and pm.group(1) in self._label_to_good:
            self.known[(self._board_district, self._label_to_good[pm.group(1)])] = \
                (float(pm.group(2).replace(",", "")), self.day)
        sm = re.match(r"(?:• )?SUPPLIER: (\d+)x (.+?) at \$([\d,]+)/unit", s)
        if sm and sm.group(2) in self._label_to_good:
            self._supplier = (self._label_to_good[sm.group(2)],
                              int(sm.group(3).replace(",", "")))
        super().say(text)

    # ── beliefs ──────────────────────────────────────────────────
    def _expected(self, dk: str, good: str) -> float:
        """Expected street price, decaying stale intel toward the base."""
        base = self._data.GOODS[good]["base"] \
            * self._data.DISTRICTS[dk].get("good_bias", {}).get(good, 1.0)
        base *= self.signal.get(good, 1.0)
        if (dk, good) in self.known:
            price, when = self.known[(dk, good)]
            trust = max(0.0, 1.0 - 0.25 * (self.day - when))
            return trust * price + (1 - trust) * base
        return base

    def _best_district(self) -> tuple[str, float]:
        best, best_v = None, -1.0
        for dk in self._data.DISTRICTS:
            v = sum(self._expected(dk, g) / self._data.GOODS[g]["bulk"]
                    for g in self._data.GOODS)
            if v > best_v:
                best, best_v = dk, v
        return best or "university", best_v

    # ── decisions ────────────────────────────────────────────────
    def _special_menu(self, prompt: str, options: list[str]) -> int | None:
        if prompt.startswith("Run today's route where?"):
            target, _ = self._best_district()
            label = self._data.DISTRICTS[target]["label"]
            for i, o in enumerate(options[:-1]):
                if o.startswith(label):
                    return i
            return 0
        return super()._special_menu(prompt, options)

    def ask_int(self, prompt: str, lo: int, hi: int, default: int = 0) -> int:
        if lo >= hi:
            return lo
        if prompt.startswith("Load"):
            m = re.match(r"Load (.+?)\?", prompt)
            good = self._label_to_good.get(m.group(1)) if m else None
            if good:
                target, _ = self._best_district()
                hm = re.search(r"~\$([\d,]+)/u here", prompt)
                here = float(hm.group(1).replace(",", "")) if hm else None
                exp = self._expected(target, good)
                floor = here if here is not None \
                    else self._data.GOODS[good]["base"]
                # Load only when the destination beats holding at home.
                return hi if exp > floor * 1.1 else lo
            return hi
        if prompt.startswith("Buy how many units"):
            sup = getattr(self, "_supplier", None)
            if sup:
                good, price = sup
                best = max(self._expected(dk, good)
                           for dk in self._data.DISTRICTS)
                return hi if price < best * 0.55 else lo
            return lo
        return super().ask_int(prompt, lo, hi, default)


BOTS = {
    "greedy": GreedyBot,
    "cautious": CautiousBot,
    "pizza": PizzaFirstBot,
    "crime": CrimeHeavyBot,
    "market": MarketBot,
}
