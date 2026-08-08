"""Legacy-equivalence harness: the P0 refactor must not move Act I.

The engine is being rebuilt underneath the game (typed evidence, the
shops collection, save v3). This harness proves the rebuild is
behavior-preserving, per seed, against golden baselines generated from
the pre-refactor engine:

- **legacy projection** — every night's state, rendered in the save-v2
  shape (explicit field list below), hashed. The projection reads only
  public attributes, so the same function runs unchanged on both the old
  engine (fields) and the new one (compat properties / derived values).
- **shared RNG streams** — the four persistent player streams that both
  engines have, hashed nightly. Streams added after v2 must end every
  run exactly as initialized: provably undrawn.
- **action replay** — the bot's total prompt count (menus + amounts +
  confirms) per run, plus the ending.

Usage:
    python3 -m analysis.equivalence generate   # write golden_act1.json
    python3 -m analysis.equivalence check      # compare a rebuilt engine

`check` exits nonzero on the first divergence and names the seed, bot
and night where the engines part ways. The gate for any engine change in
this family: 150/150 seeds identical for both bot profiles.
"""

import argparse
import hashlib
import json
import os
import random
from dataclasses import asdict

from extra_toppings import game, rng
from extra_toppings.bot import GreedyBot
from extra_toppings.ui import BotConsole

GOLDEN_PATH = os.path.join(os.path.dirname(__file__), "golden_act1.json")

# The save-v2 surface, spelled out. The projection must keep producing
# exactly this shape from any future engine.
V2_SHOP_FIELDS = ("quality", "price", "ingredients", "pantry_quality",
                  "reputation", "damage_days", "coupon_days")
SHARED_STREAMS = ("routes", "rivals", "raids", "staff")
BOTS = {"random": BotConsole, "greedy": GreedyBot}


def legacy_projection(state) -> dict:
    """State rendered in the v2 save shape, via public attributes only."""
    shop = {f: getattr(state.shop, f) for f in V2_SHOP_FIELDS}
    shop["upgrades"] = sorted(state.shop.upgrades)
    return {
        "day": state.day,
        "clean": state.clean,
        "dirty": state.dirty,
        "debt": state.debt,
        "shop": shop,
        "shop_stash": dict(state.shop_stash),
        "warehouse": dict(state.warehouse) if state.warehouse is not None else None,
        "warehouse_cash": state.warehouse_cash,
        "employees": [asdict(e) for e in state.employees],
        "districts": {k: asdict(d) for k, d in state.districts.items()},
        "rivals": {k: asdict(r) for k, r in state.rivals.items()},
        "prices": state.prices,
        "events": [{"id": e.spec["id"], "days_left": e.days_left}
                   for e in state.events],
        "case": float(state.case),
        "case_flags": list(state.case_flags),
        "news": list(state.news),
        "game_over": state.game_over,
        "debt_paid_day": state.debt_paid_day,
        "total_laundered": state.total_laundered,
        "raids_led": state.raids_led,
        "kills": state.kills,
        "demand_shock": state.demand_shock,
        "demand_today": state.demand_today,
        "delivery_pool": state.delivery_pool,
        "legit_revenue_today": state.legit_revenue_today,
    }


def _digest(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:12]


def _streams_digest(streams) -> str:
    return _digest({name: rng._rng_state_to_json(getattr(streams, name))
                    for name in SHARED_STREAMS})


def _counting(bot_cls):
    class Counting(bot_cls):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.prompts = 0

        def menu(self, prompt, options):
            self.prompts += 1
            return super().menu(prompt, options)

        def ask_int(self, prompt, lo, hi, default=0):
            self.prompts += 1
            return super().ask_int(prompt, lo, hi, default)

        def confirm(self, prompt):
            self.prompts += 1
            return super().confirm(prompt)
    return Counting


def _new_streams_undrawn(streams, seed: int) -> list[str]:
    """Names of post-v2 persistent streams that HAVE been drawn."""
    drawn = []
    for name in getattr(type(streams), "PERSISTENT", ()):
        if name in SHARED_STREAMS:
            continue
        fresh = random.Random(f"{seed}/{name}")
        if getattr(streams, name).getstate() != fresh.getstate():
            drawn.append(name)
    return drawn


def run_recorded(seed: int, bot_key: str) -> dict:
    nights: list[list[str]] = []
    drawn_new: list[str] = []

    def on_night(state, streams):
        nights.append([_digest(legacy_projection(state)),
                       _streams_digest(streams)])
        drawn_new.extend(n for n in _new_streams_undrawn(streams, seed)
                         if n not in drawn_new)

    con = _counting(BOTS[bot_key])(random.Random(seed), verbose=False)
    state = game.run(seed, con, on_night=on_night)
    return {"nights": nights, "ending": state.game_over,
            "prompts": con.prompts, "drawn_new_streams": drawn_new}


def generate(seeds: int) -> None:
    runs = {}
    for bot_key in BOTS:
        for seed in range(seeds):
            rec = run_recorded(seed, bot_key)
            rec.pop("drawn_new_streams")      # not part of the v2 baseline
            runs[f"{bot_key}/{seed}"] = rec
    payload = {
        "meta": {"engine": "pre-P0 v2 baseline @ 3d79d17",
                 "seeds": seeds, "bots": sorted(BOTS)},
        "runs": runs,
    }
    with open(GOLDEN_PATH, "w") as f:
        json.dump(payload, f, sort_keys=True)
    print(f"wrote {len(runs)} golden runs to {GOLDEN_PATH}")


def check(seeds: int | None) -> int:
    with open(GOLDEN_PATH) as f:
        golden = json.load(f)
    n = seeds or golden["meta"]["seeds"]
    failures = 0
    checked = 0
    for bot_key in golden["meta"]["bots"]:
        for seed in range(n):
            key = f"{bot_key}/{seed}"
            want = golden["runs"][key]
            got = run_recorded(seed, bot_key)
            checked += 1
            if got["drawn_new_streams"]:
                failures += 1
                print(f"FAIL {key}: new streams drawn during Act I: "
                      f"{got['drawn_new_streams']}")
                continue
            if got["ending"] != want["ending"]:
                failures += 1
                print(f"FAIL {key}: ending {got['ending']!r} != "
                      f"golden {want['ending']!r}")
                continue
            if got["prompts"] != want["prompts"]:
                failures += 1
                print(f"FAIL {key}: {got['prompts']} prompts != "
                      f"golden {want['prompts']} (action replay diverged)")
                continue
            for night, (g, w) in enumerate(zip(got["nights"], want["nights"]),
                                           start=1):
                if g != w:
                    failures += 1
                    which = "projection" if g[0] != w[0] else "shared streams"
                    print(f"FAIL {key}: {which} diverges on night {night}")
                    break
            else:
                if len(got["nights"]) != len(want["nights"]):
                    failures += 1
                    print(f"FAIL {key}: run length {len(got['nights'])} != "
                          f"golden {len(want['nights'])}")
    print(f"equivalence: {checked - failures}/{checked} runs identical")
    return 1 if failures else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["generate", "check"])
    ap.add_argument("--seeds", type=int, default=150)
    args = ap.parse_args()
    if args.mode == "generate":
        generate(args.seeds)
    else:
        raise SystemExit(check(args.seeds))


if __name__ == "__main__":
    main()
