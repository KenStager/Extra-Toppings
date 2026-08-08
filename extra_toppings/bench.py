"""Headless bot benchmark: run many seeded games per strategy and report
distributions. Usage:  python3 -m extra_toppings.bench [--seeds N]

This is an instrument, not a target — it exposes economic behavior so a
human can judge it. Do not tune the game so the bots win.
"""

import argparse
import random
from collections import Counter

from .bot import BOTS, StrategyBot
from .game import run
from .ui import BotConsole


def _counting(bot_cls):
    class Counting(bot_cls):
        def __init__(self, rng, verbose=False):
            super().__init__(rng, verbose)
            self.actions: Counter = Counter()

        def menu(self, prompt, options):
            pick = super().menu(prompt, options)
            label = options[pick]
            # Collapse dynamic labels so counts aggregate.
            for prefix in ("Sell", "Load", "Pay Carmine", "Launder", "Buy from",
                           "Buy ingredients", "Plan tonight's route",
                           "Plan a night job", "Read someone in", "Play it cool",
                           "Slip him a bribe", "Floor it", "Defend the shop",
                           "Pay tribute", "Empty the stash"):
                if label.startswith(prefix):
                    label = prefix
                    break
            self.actions[label] += 1
            return pick

    return Counting


def run_bench(seeds: int, verbose: bool = True) -> dict:
    strategies: dict = dict(BOTS)
    strategies["random"] = BotConsole
    results = {}
    for name, cls in strategies.items():
        wrapped = _counting(cls) if issubclass(cls, StrategyBot) else cls
        rows: list[dict] = []
        actions: Counter = Counter()
        for seed in range(seeds):
            con = wrapped(random.Random(seed))
            s = run(seed, con)
            rows.append({
                "ending": s.game_over,
                "paid": s.debt_paid_day is not None,
                "arrested": s.game_over == "arrested",
                "case": s.case,
                "clean": s.clean,
                "dirty": s.dirty + s.warehouse_cash,
                "rep": s.shop.reputation,
                "laundered": s.total_laundered,
                "raids": s.raids_led,
                "net": s.net_worth(),
            })
            if hasattr(con, "actions"):
                actions.update(con.actions)
        n = len(rows)

        def mean(k: str, rows=rows, n=n) -> float:
            return sum(r[k] for r in rows) / n

        summary: dict = {
            "endings": Counter(r["ending"] for r in rows),
            "payoff_rate": sum(r["paid"] for r in rows) / n,
            "arrest_rate": sum(r["arrested"] for r in rows) / n,
            "avg_case": mean("case"),
            "avg_clean": mean("clean"),
            "avg_dirty": mean("dirty"),
            "avg_rep": mean("rep"),
            "avg_laundered": mean("laundered"),
            "raids_total": sum(r["raids"] for r in rows),
            "median_net": sorted(r["net"] for r in rows)[n // 2],
            "top_actions": actions.most_common(6),
        }
        results[name] = summary
        if verbose:
            e = dict(summary["endings"])
            print(f"\n== {name} ({n} seeds) ==")
            print(f"  endings        {e}")
            print(f"  debt payoff    {summary['payoff_rate']:.0%}"
                  f"   arrests {summary['arrest_rate']:.0%}")
            print(f"  avg case {summary['avg_case']:5.1f}   avg rep "
                  f"{summary['avg_rep']:5.1f}   median net ${summary['median_net']:,}")
            print(f"  avg clean ${summary['avg_clean']:,.0f}   avg dirty "
                  f"${summary['avg_dirty']:,.0f}   avg laundered "
                  f"${summary['avg_laundered']:,.0f}   raids led {summary['raids_total']}")
            if summary["top_actions"]:
                acts = ", ".join(f"{a}×{c}" for a, c in summary["top_actions"])
                print(f"  top actions    {acts}")
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=60)
    args = ap.parse_args()
    run_bench(args.seeds)


if __name__ == "__main__":
    main()
