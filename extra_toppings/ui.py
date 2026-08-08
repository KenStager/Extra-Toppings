"""Console I/O. The Game only talks to a Console, so a BotConsole can play unattended."""

import random
import sys

RULE = "─" * 62


def money(n: float) -> str:
    n = round(n)
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

    def scene_menu(self, namespace: str, prompt: str, options: list[str]) -> int:
        """Fork-scene decisions ride a channel separate from menu() so
        replay tooling can trace them apart from the gameplay decision
        log (§2.7 rev. 5). Interactive play just delegates; bot consoles
        override with a deterministic handler that consumes no RNG."""
        return self.menu(prompt, options)


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

    def scene_menu(self, namespace: str, prompt: str, options: list[str]) -> int:
        # Deterministic and RNG-free (§2.7 rev. 5): scene choices must
        # not perturb the bot's decision stream — the extra menus would
        # otherwise shift every later gameplay choice. The scene
        # guarantees its last option always progresses (stand pat / the
        # confirming answer), so last-option is a complete policy.
        return len(options) - 1


class ScriptExhausted(Exception):
    """A ScriptedConsole ran out of answers at a scene decision — scene
    choices are irrevocable, so there is no safe fallback to take."""


class ScriptedConsole(Console):
    """Replays an exact list of answers. Used by tests to pin decisions.

    Each script entry answers the next menu/ask_int/confirm call in order.
    When the script runs out: menus take their last option, ask_int takes
    its default, confirm answers False — all safe "do nothing" choices.
    The exception is scene_menu: sit-down decisions permanently dismiss
    chairs, so an exhausted script raises ScriptExhausted (before any
    state mutates) instead of failing open into a commitment (rev. 6).
    """

    def __init__(self, script: list | None = None) -> None:
        super().__init__()
        self.quiet = True
        self.script = list(script or [])
        self.transcript: list[str] = []

    def _next(self, fallback):
        if self.script:
            return self.script.pop(0)
        return fallback

    def menu(self, prompt: str, options: list[str]) -> int:
        ans = self._next(len(options) - 1)
        ans = max(0, min(int(ans), len(options) - 1))
        self.transcript.append(f"menu[{prompt}] -> {options[ans]}")
        return ans

    def ask_int(self, prompt: str, lo: int, hi: int, default: int = 0) -> int:
        if lo >= hi:
            return lo
        ans = max(lo, min(int(self._next(default)), hi))
        self.transcript.append(f"int[{prompt}] -> {ans}")
        return ans

    def confirm(self, prompt: str) -> bool:
        ans = bool(self._next(False))
        self.transcript.append(f"confirm[{prompt}] -> {ans}")
        return ans

    def scene_menu(self, namespace: str, prompt: str, options: list[str]) -> int:
        if not self.script:
            raise ScriptExhausted(
                f"scene_menu[{prompt}] needs an explicit scripted answer")
        ans = max(0, min(int(self.script.pop(0)), len(options) - 1))
        self.transcript.append(f"scene[{namespace}:{prompt}] -> {options[ans]}")
        return ans

    def pause(self) -> None:
        pass


def fatal(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(1)
