"""Save/load: full simulation state plus RNG stream, JSON on disk.

No player-facing save UI yet — this is the engine layer the tests (and a
future in-game save slot) sit on. Loading a save and continuing with the
same decisions must produce the same outcomes, so the RNG state travels
with the world state.

Version 3: the shop became a collection (`shops`, a list of one until a
second branch exists), stash lives inside each shop, and the Case became
typed evidence records whose sum IS the meter. Version-2 saves migrate
forward on load (`_migrate_v2`); newer-than-known versions are refused.
"""

import json
from dataclasses import asdict

from . import data, models
from .models import (RaidAttemptRecord, RouteExecutionRecord,
                     ActiveEvent, BranchState, DamageRecord, District,
                     Employee, Evidence, Rival, Shop, SitdownSnapshot, State,
                     WarCampaignState, validate_branch_state,
                     validate_cross_state, validate_evidence)
from .rng import Streams

SAVE_VERSION = 3

_EVENTS_BY_ID = {e["id"]: e for e in data.EVENTS}


def state_to_dict(state: State) -> dict:
    return {
        "version": SAVE_VERSION,
        "day": state.day,
        "clean": state.clean,
        "dirty": state.dirty,
        "debt": state.debt,
        "shops": [{**asdict(s), "upgrades": sorted(s.upgrades)}
                  for s in state.shops],
        "wagons": [asdict(w) for w in state.wagons],
        "warehouse": dict(state.warehouse) if state.warehouse is not None else None,
        "warehouse_cash": state.warehouse_cash,
        "employees": [asdict(e) for e in state.employees],
        "districts": {k: asdict(d) for k, d in state.districts.items()},
        "rivals": {k: asdict(r) for k, r in state.rivals.items()},
        "prices": state.prices,
        "events": [{"id": e.spec["id"], "days_left": e.days_left}
                   for e in state.events],
        "evidence": [asdict(e) for e in state.evidence],
        "news": list(state.news),
        "game_over": state.game_over,
        "debt_paid_day": state.debt_paid_day,
        "total_laundered": state.total_laundered,
        "raids_led": state.raids_led,
        "kills": state.kills,
        "demand_shock": state.demand_shock,
        "act": state.act,
        "branch": state.branch,
        "branch_state": asdict(state.branch_state)
        if state.branch_state is not None else None,
        # Added post-v3 without a version bump: primitives only, and
        # older v3 payloads load it as None (state_from_dict uses .get).
        "sitdown_snapshot": asdict(state.sitdown_snapshot)
        if state.sitdown_snapshot is not None else None,
        "raid_log": [asdict(e) for e in state.raid_log],
        "route_log": [asdict(e) for e in state.route_log],
    }


def _migrate_v2(d: dict) -> dict:
    """Lift a version-2 payload into version-3 shape.

    Per-flag magnitudes are unrecoverable from a v2 save (it stored one
    scalar and bare strings), so the flags become annotation records
    (magnitude 0, rendered verbatim) and a single carrier record holds
    the whole scalar — the sum equals the stored Case exactly, and the
    epilogue prints the same file it always did."""
    out = dict(d)
    out["version"] = SAVE_VERSION
    shop = dict(out.pop("shop"))
    shop["district"] = data.HOME_DISTRICT
    shop["stash"] = out.pop("shop_stash")
    # v2 kept the order book and honest till on the state; they are
    # shop-local now.
    shop["demand_today"] = out.pop("demand_today")
    shop["delivery_pool"] = out.pop("delivery_pool")
    shop["legit_revenue_today"] = out.pop("legit_revenue_today")
    out["shops"] = [shop]
    evidence = [{"day": 0, "magnitude": 0.0, "kind": "legacy",
                 "why": flag, "source": ""} for flag in out.pop("case_flags")]
    case = out.pop("case")
    if case:
        evidence.append({"day": d["day"], "magnitude": case,
                         "kind": "legacy", "why": "", "source": ""})
    out["evidence"] = evidence
    out.setdefault("act", 1)
    out.setdefault("branch", None)
    out.setdefault("branch_state", None)
    return out


def state_from_dict(d: dict) -> State:
    if d.get("version") == 2:
        d = _migrate_v2(d)
    if d.get("version") != SAVE_VERSION:
        raise ValueError(f"unsupported save version {d.get('version')!r}")
    shops = []
    for s in d["shops"]:
        sd = dict(s)
        sd["upgrades"] = set(sd["upgrades"])
        # Additive with a default (design rev. 27 item 1): a v3 payload
        # written before addresses had keys carries exactly one shop,
        # so the home key is the only identity it could have had.
        sd.setdefault("key", models.HOME_SHOP_KEY)
        shops.append(Shop(**sd))
    # Same migration for the wagon: a payload written before wagons
    # had identities carries exactly one address and one wagon kept
    # there. More than one address with no wagon list is not a payload
    # this migration can honestly interpret, so it is refused rather
    # than guessed (rev. 27 item 7).
    if "wagons" in d:
        wagons = [models.Wagon(**w) for w in d["wagons"]]
    elif len(shops) == 1:
        wagons = [models.Wagon(key=models.HOME_WAGON_KEY,
                               shop_key=shops[0].key)]
    else:
        raise ValueError(
            f"{len(shops)} addresses but no wagon list — cannot infer "
            f"which address kept the wagon")
    state = State(
        day=d["day"], clean=d["clean"], dirty=d["dirty"], debt=d["debt"],
        shops=shops,
        wagons=wagons,
        warehouse=dict(d["warehouse"]) if d["warehouse"] is not None else None,
        warehouse_cash=d["warehouse_cash"],
        employees=[Employee(**{"shop_key": models.HOME_SHOP_KEY, **e})
                   for e in d["employees"]],
        districts={k: District(**v) for k, v in d["districts"].items()},
        rivals={k: Rival(**v) for k, v in d["rivals"].items()},
        prices={k: dict(v) for k, v in d["prices"].items()},
        events=[ActiveEvent(spec=_EVENTS_BY_ID[e["id"]], days_left=e["days_left"])
                for e in d["events"]],
        evidence=[Evidence(**e) for e in d["evidence"]],
        news=list(d["news"]),
        game_over=d["game_over"], debt_paid_day=d["debt_paid_day"],
        total_laundered=d["total_laundered"], raids_led=d["raids_led"],
        kills=d["kills"], demand_shock=d["demand_shock"],
        act=d["act"], branch=d["branch"],
        branch_state=_branch_state_from(d["branch_state"]),
        sitdown_snapshot=SitdownSnapshot(**d["sitdown_snapshot"])
        if d.get("sitdown_snapshot") is not None else None,
        # Typed, validated at construction (rev. 18 items 3-4):
        # malformed or inconsistent log entries are refused, never
        # round-tripped.
        raid_log=[RaidAttemptRecord(**e) for e in d.get("raid_log") or []],
        route_log=[RouteExecutionRecord(**e)
                   for e in d.get("route_log") or []],
    )
    # A payload naming a branch must carry a coherent BranchState — a
    # mixed, impossible, or terminally-contradictory combination is
    # refused, not repaired (the severance state machine binds here,
    # including the sold-cannot-be-pending terminal invariant). The
    # evidence ledger has its own persistence contract (rev. 9), and
    # the whole payload must cohere across ledger, roster, settlements
    # and branch state (rev. 10) — refused, not repaired.
    validate_branch_state(state.branch, state.branch_state,
                          game_over=state.game_over)
    validate_evidence(state.evidence)
    validate_cross_state(state)
    return state


def _branch_state_from(payload: dict | None) -> BranchState | None:
    if payload is None:
        return None
    payload = dict(payload)
    # Migration: pre-rev.8-completion v3 payloads stored the incident
    # discount as a binary float fraction (0.28000000000000004). The
    # canonical unit is whole percentage points; the float converts
    # once, here, on load.
    if "escrow_discount" in payload and "escrow_discount_pct" not in payload:
        payload["escrow_discount_pct"] = round(
            payload.pop("escrow_discount") * 100)
    if payload.get("campaigns"):
        # War campaigns are typed (rev. 14 item 2): rebuild the nested
        # dataclasses here so validate_branch_state judges real
        # campaign objects. A payload whose shape does not fit the
        # types is refused, not repaired.
        try:
            payload["campaigns"] = [
                WarCampaignState(**{
                    **c, "damage": [DamageRecord(**r)
                                    for r in c.get("damage", [])]})
                for c in payload["campaigns"]]
        except TypeError as exc:
            raise ValueError(f"war: malformed campaign payload ({exc})")
    try:
        return BranchState(**payload)
    except TypeError as exc:
        raise ValueError(f"malformed branch-state payload ({exc})")


def save_game(state: State, streams: Streams, path: str) -> None:
    payload = {"state": state_to_dict(state), "streams": streams.to_dict()}
    with open(path, "w") as f:
        json.dump(payload, f)


def load_game(path: str) -> tuple[State, Streams]:
    with open(path) as f:
        payload = json.load(f)
    return state_from_dict(payload["state"]), Streams.from_dict(payload["streams"])
