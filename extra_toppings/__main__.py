"""CLI entry: python -m extra_toppings [--seed N] [--auto [DAYS]] [--verbose]"""

import argparse
import os
import random

from .bot import GreedyBot
from .config import GameConfig
from .game import run
from .models import RELEASED_BRANCHES
from .ui import BotConsole, Console


def _config_from_env() -> GameConfig:
    """The CLI is the only place the environment is read; the engine
    takes an explicit GameConfig (design §8 rev. 5). EXTRA_TOPPINGS_FORK=1
    turns the sit-down trigger on with the RELEASED chairs actionable
    (§7: the Straight Path and the Quiet Sale on the P2 merge
    approval; the Harbor War on the P3 merge disposition) — the
    canonical set lives in models.py, and the flag consumes it rather
    than spelling its own."""
    if os.environ.get("EXTRA_TOPPINGS_FORK") == "1":
        return GameConfig(fork_enabled=True,
                          enabled_branches=RELEASED_BRANCHES)
    return GameConfig()


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="extra_toppings",
        description="Extra Toppings — build a pizza empire, run the city's "
                    "underground market, keep the books believable.")
    ap.add_argument("--seed", type=int, default=None, help="RNG seed for a repeatable run")
    ap.add_argument("--auto", nargs="?", const=30, type=int, default=None,
                    metavar="DAYS", help="let a random bot play (default 30 days)")
    ap.add_argument("--smart", action="store_true",
                    help="with --auto: use the greedy strategy bot instead")
    ap.add_argument("--verbose", action="store_true",
                    help="with --auto: print the bot's full playthrough")
    args = ap.parse_args()

    config = _config_from_env()
    if args.auto is not None:
        rng = random.Random(args.seed)
        bot_cls = GreedyBot if args.smart else BotConsole
        con = bot_cls(rng, verbose=args.verbose)
        state = run(args.seed, con, max_days=args.auto, config=config)
        print(f"[auto] ended day {state.day} — ending: {state.game_over}, "
              f"net {state.net_worth():+,}, case {state.case:.0f}/100")
    else:
        run(args.seed, Console(), config=config)


if __name__ == "__main__":
    main()
