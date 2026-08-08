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
- **action replay** — a digest of the bot's complete decision trace:
  every menu (prompt, options, chosen index), every amount prompt
  (prompt, bounds, default, answer) and every confirmation (prompt,
  result), in order — two runs cannot pass by merely answering the same
  NUMBER of prompts. The raw prompt count rides along as a diagnostic,
  plus the ending.

The `standpat` mode is the fork era's second gate (§2.7 criterion 6,
the rev. 5 two-trace contract): every seed runs twice — flag off and
flag on — and the flag-on run's GAME trace (ordinary gameplay prompts,
exact current event shape) must equal the flag-off run's event for
event, full lists compared, not digests. Sit-down decisions ride the
namespaced scene_menu channel into a separate SCENE trace, asserted
independently to hold exactly the permitted interaction: one chair
selection choosing stand-pat and one confirmation. Ending, nightly
projection and shared streams stay exact; the fork streams stay
undrawn. golden_act1.json is untouched by all of this.

Usage:
    python3 -m analysis.equivalence generate   # write golden_act1.json
    python3 -m analysis.equivalence check      # compare a rebuilt engine
    python3 -m analysis.equivalence standpat   # paired flag-on control

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
from extra_toppings.config import GameConfig
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


def _tracing(bot_cls):
    class Tracing(bot_cls):
        """Records every interaction AND its answer, in order. Gameplay
        prompts keep the exact pre-fork event shape in `trace` (the
        goldens depend on it); sit-down decisions land in the separate
        namespaced `scene_trace` (§2.7 rev. 5)."""

        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.trace: list = []
            self.scene_trace: list = []

        def menu(self, prompt, options):
            ans = super().menu(prompt, options)
            self.trace.append(["menu", prompt, list(options), ans])
            return ans

        def ask_int(self, prompt, lo, hi, default=0):
            ans = super().ask_int(prompt, lo, hi, default)
            self.trace.append(["int", prompt, lo, hi, default, ans])
            return ans

        def confirm(self, prompt):
            ans = super().confirm(prompt)
            self.trace.append(["confirm", prompt, ans])
            return ans

        def scene_menu(self, namespace, prompt, options):
            ans = super().scene_menu(namespace, prompt, options)
            self.scene_trace.append([namespace, prompt, list(options), ans])
            return ans
    return Tracing


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


def run_recorded(seed: int, bot_key: str,
                 config: GameConfig | None = None) -> dict:
    nights: list[list[str]] = []
    drawn_new: list[str] = []

    night_facts: list[list] = []

    def on_night(state, streams):
        nights.append([_digest(legacy_projection(state)),
                       _streams_digest(streams)])
        # World facts for the existence check (§2.7 rev. 6): whether a
        # sit-down is owed is derived from the flag-off timeline alone —
        # debt_paid_day, the day, and whether the run had already ended —
        # never from fork code or its snapshot.
        night_facts.append([state.day, state.game_over is not None,
                            state.debt_paid_day])
        drawn_new.extend(n for n in _new_streams_undrawn(streams, seed)
                         if n not in drawn_new)

    con = _tracing(BOTS[bot_key])(random.Random(seed), verbose=False)
    state = game.run(seed, con, on_night=on_night, config=config)
    return {"nights": nights, "ending": state.game_over,
            "prompts": len(con.trace), "trace": _digest(con.trace),
            "raw_trace": con.trace, "scene_trace": con.scene_trace,
            "night_facts": night_facts, "drawn_new_streams": drawn_new}


def generate(seeds: int) -> None:
    runs = {}
    for bot_key in BOTS:
        for seed in range(seeds):
            rec = run_recorded(seed, bot_key)
            # Digest-only in the golden file: no raw traces, and the
            # fork-era fields are not part of the v2 baseline.
            for extra in ("drawn_new_streams", "raw_trace", "scene_trace",
                          "night_facts"):
                rec.pop(extra)
            runs[f"{bot_key}/{seed}"] = rec
    payload = {
        "meta": {"engine": "pre-P0 v2 baseline @ 3d79d17 "
                           "(harness + on_night hook injected; "
                           "engine files untouched)",
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
            if got["trace"] != want["trace"]:
                failures += 1
                print(f"FAIL {key}: decision trace diverged "
                      f"({got['prompts']} prompts vs golden "
                      f"{want['prompts']})")
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


# ── the stand-pat scene schema, FROZEN (rev. 6) ───────────────────
# Deliberately literal, never imported from extra_toppings.sitdown: a
# drifted prompt, option, order or answer must FAIL here, exactly as a
# drifted engine fails the goldens. Changing the scene is a deliberate
# act that lands together with a version bump of this schema.
SCENE_SCHEMA_VERSION = 1
STANDPAT_SCENE = [
    ["sitdown", "Your chair:",
     ["The Straight Path — wind it down, sell nothing, exit whole",
      "Carmine's Partner — a second shop on his money, points on his schedule",
      "The Harbor War — take the city, one rival at a time",
      "The Quiet Sale — a buyer, an escrow week, a clean walk away",
      "Stand pat — thank them all, keep what's yours"],
     4],
    ["sitdown", "Stand pat? The table clears for good.",
     ["Reconsider", "Let them go — I keep what's mine"],
     1],
]
FULL_RUN_DAYS = 30            # the harness always plays full calendars
NO_SITDOWN_R = 4              # §2.1: R ≤ 4 seats no table


def _scene_expected(night_facts: list) -> bool:
    """Whether a sit-down with a table is owed, derived purely from the
    FLAG-OFF nightly timeline — debt_paid_day, the day, and whether the
    run had already ended — never from fork code or its snapshot
    (§2.7 rev. 6). A scene is owed when the debt died on a night the
    run survived, a next morning exists inside the calendar, and
    R = 30 − payoff_day leaves a table worth setting."""
    for _day_after, ended, paid_day in night_facts:
        if paid_day is not None:
            return (not ended
                    and paid_day + 1 <= FULL_RUN_DAYS
                    and FULL_RUN_DAYS - paid_day > NO_SITDOWN_R)
    return False


def _scene_contract(scene: list) -> str | None:
    """None when the scene trace equals the frozen stand-pat schema
    exactly — namespace, prompt, complete ordered options and answer,
    event for event; else a description of the first divergence."""
    if len(scene) != len(STANDPAT_SCENE):
        return (f"scene event count {len(scene)} != schema "
                f"{len(STANDPAT_SCENE)} (v{SCENE_SCHEMA_VERSION})")
    for i, (got, want) in enumerate(zip(scene, STANDPAT_SCENE)):
        if got != want:
            return (f"scene event {i} diverges from schema "
                    f"v{SCENE_SCHEMA_VERSION}: {got!r}")
    return None


def _compare_pair(off: dict, on: dict) -> tuple[str | None, bool]:
    """One flag-off/flag-on pair against the criterion-6 contract.
    Returns (problem, scene_held)."""
    expected = _scene_expected(off["night_facts"])
    held = bool(on["scene_trace"])
    if off["scene_trace"]:
        return "scene events in a flag-off run", held
    if expected and not held:
        return ("the flag-off timeline reaches the table but no "
                "sit-down was held"), held
    if held and not expected:
        return ("a sit-down was held where the flag-off timeline "
                "expects none"), held
    if held:
        problem = _scene_contract(on["scene_trace"])
        if problem:
            return problem, held
    if on["drawn_new_streams"]:
        return (f"fork streams drawn in stand-pat: "
                f"{on['drawn_new_streams']}"), held
    if on["raw_trace"] != off["raw_trace"]:
        return (f"game trace diverged ({len(on['raw_trace'])} events "
                f"vs {len(off['raw_trace'])})"), held
    if on["ending"] != off["ending"]:
        return f"ending {on['ending']!r} != flag-off {off['ending']!r}", held
    if on["nights"] != off["nights"]:
        return "nightly projection or shared streams diverged", held
    return None, held


def check_standpat(seeds: int | None) -> int:
    """§2.7 criterion 6, rev. 5/6: flag-on stand-pat equals flag-off per
    seed on the game trace (event for event), nightly projection, shared
    streams and ending — AND the sit-down exists exactly where the
    flag-off timeline says one is owed, matching the frozen scene schema
    exactly. Equivalence alone cannot pass this gate; the feature has to
    be there."""
    n = seeds or 150
    failures = 0
    checked = 0
    expected_total = 0
    held_total = 0
    for bot_key in sorted(BOTS):
        for seed in range(n):
            key = f"{bot_key}/{seed}"
            off = run_recorded(seed, bot_key)
            on = run_recorded(seed, bot_key, GameConfig(fork_enabled=True))
            checked += 1
            expected_total += 1 if _scene_expected(off["night_facts"]) else 0
            problem, held = _compare_pair(off, on)
            held_total += 1 if held else 0
            if problem:
                failures += 1
                print(f"FAIL {key}: {problem}")
    print(f"paired stand-pat: {checked - failures}/{checked} runs "
          f"identical; sit-downs expected {expected_total}, held "
          f"{held_total} (schema v{SCENE_SCHEMA_VERSION})")
    return 1 if failures else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["generate", "check", "standpat"])
    ap.add_argument("--seeds", type=int, default=150)
    args = ap.parse_args()
    if args.mode == "generate":
        generate(args.seeds)
    elif args.mode == "standpat":
        raise SystemExit(check_standpat(args.seeds))
    else:
        raise SystemExit(check(args.seeds))


if __name__ == "__main__":
    main()
