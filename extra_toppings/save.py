"""Save/load: full simulation state plus RNG stream, JSON on disk.

No player-facing save UI yet — this is the engine layer the tests (and a
future in-game save slot) sit on. Loading a save and continuing with the
same decisions must produce the same outcomes, so the RNG state travels
with the world state.
"""

import json
import random
from dataclasses import asdict

from . import data
from .models import ActiveEvent, District, Employee, Rival, Shop, State

SAVE_VERSION = 1

_EVENTS_BY_ID = {e["id"]: e for e in data.EVENTS}


def state_to_dict(state: State) -> dict:
    return {
        "version": SAVE_VERSION,
        "day": state.day,
        "clean": state.clean,
        "dirty": state.dirty,
        "debt": state.debt,
        "shop": {**asdict(state.shop), "upgrades": sorted(state.shop.upgrades)},
        "shop_stash": dict(state.shop_stash),
        "warehouse": dict(state.warehouse) if state.warehouse is not None else None,
        "warehouse_cash": state.warehouse_cash,
        "employees": [asdict(e) for e in state.employees],
        "districts": {k: asdict(d) for k, d in state.districts.items()},
        "rivals": {k: asdict(r) for k, r in state.rivals.items()},
        "prices": state.prices,
        "events": [{"id": e.spec["id"], "days_left": e.days_left}
                   for e in state.events],
        "case": state.case,
        "case_flags": list(state.case_flags),
        "news": list(state.news),
        "game_over": state.game_over,
        "debt_paid_day": state.debt_paid_day,
        "total_laundered": state.total_laundered,
        "raids_led": state.raids_led,
        "kills": state.kills,
    }


def state_from_dict(d: dict) -> State:
    if d.get("version") != SAVE_VERSION:
        raise ValueError(f"unsupported save version {d.get('version')!r}")
    shop_d = dict(d["shop"])
    shop_d["upgrades"] = set(shop_d["upgrades"])
    state = State(
        day=d["day"], clean=d["clean"], dirty=d["dirty"], debt=d["debt"],
        shop=Shop(**shop_d),
        shop_stash=dict(d["shop_stash"]),
        warehouse=dict(d["warehouse"]) if d["warehouse"] is not None else None,
        warehouse_cash=d["warehouse_cash"],
        employees=[Employee(**e) for e in d["employees"]],
        districts={k: District(**v) for k, v in d["districts"].items()},
        rivals={k: Rival(**v) for k, v in d["rivals"].items()},
        prices={k: dict(v) for k, v in d["prices"].items()},
        events=[ActiveEvent(spec=_EVENTS_BY_ID[e["id"]], days_left=e["days_left"])
                for e in d["events"]],
        case=d["case"], case_flags=list(d["case_flags"]), news=list(d["news"]),
        game_over=d["game_over"], debt_paid_day=d["debt_paid_day"],
        total_laundered=d["total_laundered"], raids_led=d["raids_led"],
        kills=d["kills"],
    )
    return state


def _rng_state_to_json(rng: random.Random) -> list:
    version, internal, gauss = rng.getstate()
    return [version, list(internal), gauss]


def _rng_state_from_json(blob: list) -> tuple:
    version, internal, gauss = blob
    return (version, tuple(internal), gauss)


def save_game(state: State, rng: random.Random, path: str) -> None:
    payload = {"state": state_to_dict(state), "rng": _rng_state_to_json(rng)}
    with open(path, "w") as f:
        json.dump(payload, f)


def load_game(path: str) -> tuple[State, random.Random]:
    with open(path) as f:
        payload = json.load(f)
    state = state_from_dict(payload["state"])
    rng = random.Random()
    rng.setstate(_rng_state_from_json(payload["rng"]))
    return state, rng
