"""Strategy bots: heuristic players used to probe the economy, not to be it.

Each bot answers the same prompts a human sees. They exist to expose
economic behavior across many seeds (see bench.py); human play remains
the test of fun.
"""

import random
import re
from typing import ClassVar

from . import escrow
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
            # The calendar day, read off the header — identical to the
            # old increment on any full run, and correct on harness
            # runs that start mid-calendar (rev. 10 cohorts).
            m0 = re.search(r"DAY (\d+) of", text)
            self.day = int(m0.group(1)) if m0 else self.day + 1
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


class EscrowBot(MarketBot):
    """Minimal per-branch policy over the smart bot (§2.7 criterion 4 —
    the smart bot is the market speculator, the design's named baseline):
    takes the Quiet Sale when the table opens, then plays a CAREFUL
    diligence week — dump the stash through routes before it can be
    walked in on, pay tribute rather than let a raid land, no night
    jobs. The bot reads the same transcript a human does: the ESCROW
    header flips it into diligence mode; the buyer-gone lines flip it
    back."""

    careful = True

    def __init__(self, rng: random.Random, verbose: bool = False) -> None:
        super().__init__(rng, verbose)
        self._tried_sale = False
        self._in_escrow = False

    def say(self, text: str = "") -> None:
        stripped = text.strip()
        if stripped.startswith(("ESCROW —", "CLOSING MORNING")):
            self._in_escrow = True
            self._entered_escrow = True     # latched for the harness: a
            # day-one collapse reverts before the first night hook fires
        if "buys elsewhere" in text or "doesn't slow down" in text:
            self._in_escrow = False
        super().say(text)

    def scene_menu(self, namespace: str, prompt: str, options: list[str]) -> int:
        # Deterministic and RNG-free, like every scene handler: try the
        # Quiet Sale once; if the chair refuses (withheld), fall back to
        # progress-last. Closing menus progress-last too (sign, humane).
        if prompt == "Your chair:" and not self._tried_sale:
            self._tried_sale = True
            return 3
        return len(options) - 1

    def menu(self, prompt: str, options: list[str]) -> int:
        pick = super().menu(prompt, options)
        if "Burn dirty cash" in options[pick]:
            self._done_today.add("Burn dirty cash")   # once a night
        return pick

    def ask_int(self, prompt: str, lo: int, hi: int, default: int = 0) -> int:
        if prompt.startswith("Burn how much"):
            # Careful: burn down to the buyer's tolerance, not past it —
            # the permitted $200 is walking money, and destroying it
            # buys nothing (rev. 8). Careless: the bag stays shut.
            if self.careful:
                return max(0, min(hi, hi - escrow.DIRTY_TOLERANCE))
            return default
        return super().ask_int(prompt, lo, hi, default)

    def _score(self, label: str) -> float:
        if self._in_escrow:
            if "Burn it" in label:
                # The careful close: the stock is worth less than the
                # incidents it invites. The careless one keeps it.
                return 60 if self.careful else -10
            if "Keep it" in label:
                return 60 if not self.careful else -10
            if "Burn dirty cash" in label:
                if not self.careful or "Burn dirty cash" in self._done_today:
                    return -8
                return 45
            if "Pay tribute" in label:
                return 50                     # never let a raid land
            if "Plan a night job" in label:
                return -10
            if self.careful and "Buy from today's supplier" in label:
                return -10                    # nothing new for his man to find
            if "Plan tonight's route" in label:
                # Careful: the stash leaves in the warmer bags before the
                # buyer's man finds it. Careless: it sits where it is.
                # Once per day, like every menu preference — otherwise
                # the morning menu never ends.
                if "Plan tonight's route" in self._done_today:
                    return 0.5
                return 40 if self.careful else -10
        return super()._score(label)


class StraightBot(MarketBot):
    """Minimal per-branch policy over the smart bot (§2.7 criterion 4):
    takes the Straight Path when the table opens, then liquidates fast
    through the fire-sale channel, retains counsel, settles departed
    witnesses, advertises the reputation up, mends feuds with envelopes,
    pays tribute rather than let a raid land, declines every temptation,
    and washes the pile down under the ceiling night after night. Reads
    the same transcript a human does: the book-burning header flips it
    into branch mode; the exit readout tells it what remains."""

    remediates = True     # criterion 5's ablation flips this

    def __init__(self, rng: random.Random, verbose: bool = False) -> None:
        super().__init__(rng, verbose)
        self._tried_chair = False
        self._in_branch = False
        self._counsel = False
        self._sal_gone = False
        self._stock: int | None = None   # from the exit readout
        self._ad_running = False
        self._feud = False
        self._clean = 0
        self._dirty = 0
        self._rep = 50.0
        self.covert_by_day: dict[int, int] = {}   # transcript-tallied

    def say(self, text: str = "") -> None:
        s = text.strip()
        if s.startswith("THE STRAIGHT PATH"):
            self._in_branch = True
            self._entered_straight = True    # latched for the harness
        if self._in_branch:
            if "takes the retainer" in s:
                self._counsel = True
            if "retainer bounced" in s or "goes back in its envelope" in s:
                self._counsel = False
            if "Sal's people aren't answering" in s:
                self._sal_gone = True
            m = re.match(r"Exit readout: stock (\d+) · dirty \$([\d,]+)",
                         s)
            if m:
                self._stock = int(m.group(1))
                self._feud = "feud:" in s
            for pattern in (r"Sal's man pays \$([\d,]+)",
                            r"The contact pays \$([\d,]+)",
                            r"Route take: \$([\d,]+) dirty"):
                pm = re.search(pattern, s)
                if pm:
                    take = int(pm.group(1).replace(",", ""))
                    # self.day counts MORNING headers, so it names the
                    # calendar day the take landed on.
                    self.covert_by_day[self.day] = \
                        self.covert_by_day.get(self.day, 0) + take
        m = re.match(r"Clean \$([\d,]+) \| Dirty \$([\d,]+) \| Debt \$[\d,]+"
                     r"(?: \| Rep (\d+) \|)?", s)
        if m:
            self._clean = int(m.group(1).replace(",", ""))
            self._dirty = int(m.group(2).replace(",", ""))
            if m.group(3) is not None:
                self._rep = float(m.group(3))
        super().say(text)

    def scene_menu(self, namespace: str, prompt: str, options: list[str]) -> int:
        # Deterministic and RNG-free: try the Straight Path once; the
        # confirmation (and any other scene menu) progresses last.
        if prompt == "Your chair:" and not self._tried_chair:
            self._tried_chair = True
            return 0
        return len(options) - 1

    def _score(self, label: str) -> float:
        if self._in_branch:
            if label.startswith("Disposal"):
                if self._stock == 0 or "Disposal" in self._done_today:
                    return 0.2
                return 50
            if "Improvements" in label:
                want_counsel = self.remediates and not self._counsel
                want_ad = self._clean >= 1200 and self._rep < 60
                if (want_counsel or want_ad) \
                        and "Improvements" not in self._done_today:
                    return 45
                return 0.2
            if "Settle with a witness" in label:
                if self.remediates \
                        and "Settle with a witness" not in self._done_today:
                    return 40
                return 0.2
            if "Talk to a rival" in label:
                if self._feud and self._clean >= 0 \
                        and "Talk to a rival" not in self._done_today:
                    return 35
                return -5
            if "back door" in label:
                return -10                    # every temptation declined
            if "Pay tribute" in label:
                # Never let a raid land — when the bag can cover it.
                m = re.search(r"\(\$([\d,]+) dirty\)", label)
                demand = int(m.group(1).replace(",", "")) if m else 1500
                return 50 if self._dirty >= demand else -5
            if "Empty the stash" in label:
                # A stashless shop eats a guaranteed -8 instead of a
                # near-certain lost fight (no read-in defenders).
                return 45
        return super()._score(label)

    def menu(self, prompt: str, options: list[str]) -> int:
        pick = super().menu(prompt, options)
        if self._in_branch:
            for key in ("Disposal", "Improvements", "Settle with a witness",
                        "Talk to a rival"):
                if key in options[pick]:
                    self._done_today.add(key)
        return pick

    def _special_menu(self, prompt: str, options: list[str]) -> int | None:
        if self._in_branch:
            if prompt.startswith("Disposal — what's left"):
                return 2 if self._sal_gone else 0   # burn if Sal can't buy
            if prompt.startswith("Improvements"):
                for i, o in enumerate(options):
                    if o.startswith("Retain counsel") and self.remediates \
                            and "counsel_pick" not in self._done_today:
                        self._done_today.add("counsel_pick")
                        return i
                if self._clean >= 1200 and self._rep < 60 \
                        and "ad_pick" not in self._done_today:
                    for i, o in enumerate(options):
                        # One campaign at a time — never stack spend.
                        if o.startswith("Advertising") \
                                and "campaign running" not in o:
                            self._done_today.add("ad_pick")
                            return i
                return len(options) - 1
            if prompt.startswith("Whose quiet do you buy?"):
                for i, o in enumerate(options[:-1]):
                    if "departed" in o:
                        return i
                return len(options) - 1
            if prompt.startswith("Reach out to whom?"):
                for i, o in enumerate(options[:-1]):
                    m = re.search(r"relation (-\d+)", o)
                    if m and int(m.group(1)) <= -60:
                        return i
                return len(options) - 1
            if prompt.startswith(("Sal Moretti", "Vinnie 'The Oven'")):
                return 0                      # the envelope, not the threat
        return super()._special_menu(prompt, options)

    def ask_int(self, prompt: str, lo: int, hi: int, default: int = 0) -> int:
        if self._in_branch:
            if prompt.startswith("Hand over"):
                return hi                     # the whole shelf goes
            if prompt.startswith("Sell how many"):
                return 0                      # temptations declined
            if prompt.startswith("Run how much"):
                # Wash the pile down — but while a feud is live and the
                # calendar allows, hold a tribute-and-envelope reserve:
                # the goal's $200 line matters on day 30, not tonight.
                m = re.search(r"dirty \$([\d,]+)", prompt)
                dirty = int(m.group(1).replace(",", "")) if m else hi
                reserve = 1600 if self._feud and self.day <= 26 else 0
                # Never past tonight's ceiling (the default) — washing
                # over it is a crime on the branch's own clock.
                return max(0, min(default, dirty - reserve))
        return super().ask_int(prompt, lo, hi, default)


class NoRemediationBot(StraightBot):
    """Criterion 5's ablation: the branch's stated counterplay removed —
    never retains counsel, never settles a witness. Everything else is
    the same policy. If this bot's earned-exit rate doesn't crater, the
    pressure is decorative."""
    remediates = False


class SloppyEscrowBot(EscrowBot):
    """The valuation study's control (§2.7 criterion 4): same chair,
    but the lesson arrives by invoice — stock keeps sitting in the
    walk-in until the first incident has already repriced the deal,
    and only then does the diligence turn careful."""
    careful = False

    def say(self, text: str = "") -> None:
        if "INCIDENT" in text:
            self.careful = True          # instance shadow: lesson learned
        super().say(text)


class KeepsStashBot(EscrowBot):
    """Criterion 5's ablation: the branch's stated counterplay removed
    entirely — the stash stays on premises all week, every week. If
    this bot's close rate doesn't crater, the pressure is decorative."""
    careful = False


BOTS = {
    "greedy": GreedyBot,
    "cautious": CautiousBot,
    "pizza": PizzaFirstBot,
    "crime": CrimeHeavyBot,
    "market": MarketBot,
}
