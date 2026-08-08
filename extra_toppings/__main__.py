"""CLI entry: python -m extra_toppings [--seed N] [--auto [DAYS]] [--verbose]"""

import argparse
import random

from .bot import GreedyBot
from .game import run
from .ui import BotConsole, Console


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

    if args.auto is not None:
        rng = random.Random(args.seed)
        bot_cls = GreedyBot if args.smart else BotConsole
        con = bot_cls(rng, verbose=args.verbose)
        state = run(args.seed, con, max_days=args.auto)
        print(f"[auto] ended day {state.day} — ending: {state.game_over}, "
              f"net {state.net_worth():+,}, case {state.case:.0f}/100")
    else:
        run(args.seed, Console())


if __name__ == "__main__":
    main()
