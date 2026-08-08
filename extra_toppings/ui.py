"""Console I/O. The Game only talks to a Console, so a BotConsole can play unattended."""

import random
import sys

RULE = "─" * 62


def money(n: float) -> str:
    n = int(round(n))
    return f"-${abs(n):,}" if n < 0 else f"${n:,}"


class Console:
    """Interactive terminal front end."""

    def __init__(self) -> None:
        self.quiet = False

    # ── output ────────────────────────────────────────────────────
    def say(self, text: str = "") -> None:
        if not self.quiet:
            print(text)

    def header(self, title: str) -> None:
        self.say("")
        self.say(RULE)
        self.say(f"  {title}")
        self.say(RULE)

    def bullet(self, text: str) -> None:
        self.say(f"  • {text}")

    def pause(self) -> None:
        try:
            input("  [enter] ")
        except EOFError:
            raise SystemExit(0)

    # ── input ─────────────────────────────────────────────────────
    def menu(self, prompt: str, options: list[str]) -> int:
        """Show numbered options, return the chosen index."""
        self.say("")
        self.say(f"  {prompt}")
        for i, opt in enumerate(options, 1):
            self.say(f"    {i}. {opt}")
        while True:
            try:
                raw = input("  > ").strip()
            except EOFError:
                raise SystemExit(0)
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return int(raw) - 1
            self.say(f"  Pick 1-{len(options)}.")

    def ask_int(self, prompt: str, lo: int, hi: int, default: int = 0) -> int:
        if lo >= hi:
            return lo
        while True:
            try:
                raw = input(f"  {prompt} [{lo}-{hi}, enter={default}]: ").strip()
            except EOFError:
                raise SystemExit(0)
            if raw == "":
                return default
            if raw.lstrip("-").isdigit() and lo <= int(raw) <= hi:
                return int(raw)
            self.say(f"  Enter a number from {lo} to {hi}.")

    def confirm(self, prompt: str) -> bool:
        return self.menu(prompt, ["Yes", "No"]) == 0


class BotConsole(Console):
    """Plays by itself: random-but-sane choices. Used by --auto and the tests."""

    def __init__(self, rng: random.Random, verbose: bool = False) -> None:
        super().__init__()
        self.rng = rng
        self.quiet = not verbose
        self._menu_calls = 0

    def pause(self) -> None:
        pass

    def menu(self, prompt: str, options: list[str]) -> int:
        self._menu_calls += 1
        # Bias toward the last option (usually "continue"/"done") so phase
        # menus terminate; still explores the rest of the option space.
        if self.rng.random() < 0.35:
            return len(options) - 1
        return self.rng.randrange(len(options))

    def ask_int(self, prompt: str, lo: int, hi: int, default: int = 0) -> int:
        if lo >= hi:
            return lo
        if self.rng.random() < 0.3:
            return default
        return self.rng.randint(lo, hi)

    def confirm(self, prompt: str) -> bool:
        return self.rng.random() < 0.5


def fatal(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(1)
