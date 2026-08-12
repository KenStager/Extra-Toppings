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
                     PointsCycleRecord, WarCampaignState,
                     validate_branch_state,
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
        # Added post-v3 without a version bump: a primitive with
        # a `.get` default, so older payloads load it as None.
        "arrested_day": state.arrested_day,
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
    # ── THE one-address migration boundary (design rev. 27 item 7) ──
    # This function is the ONLY place in the engine permitted to infer
    # an address for a record that does not name one, and only while
    # the payload carries exactly one address — because then there is
    # precisely one address it could have meant. Nothing outside this
    # boundary infers: the canonical models require every identity,
    # and a multi-address payload missing one is refused, not guessed.
    #
    # The test is PRESENCE, never truthiness. Payloads written before
    # addresses had identities OMITTED these fields; none of them ever
    # carried an empty one. So an absent field is history to migrate,
    # while a present `""`, None or False is a malformed reference —
    # and migrating that would repair a broken save into a plausible
    # one, which is the opposite of what this boundary is for. Present
    # values, whatever they are, flow into canonical validation and
    # are refused there.
    one_address = len(d["shops"]) == 1

    def _addressed(payload: dict, field: str, what: str) -> dict:
        v = dict(payload)
        if field in v:
            return v
        if not one_address:
            raise ValueError(
                f"{what} names no address and the payload carries "
                f"{len(d['shops'])} of them — which one it meant "
                f"cannot be inferred, only guessed")
        v[field] = sole_key
        return v

    shops = []
    for s in d["shops"]:
        sd = dict(s)
        sd["upgrades"] = set(sd["upgrades"])
        # A v3 payload written before addresses had keys carries
        # exactly one shop, and the founding key is the only identity
        # it could ever have had. A payload that HAS a key keeps it,
        # even an unusable one — that is validation's refusal to make.
        if "key" not in sd:
            if not one_address:
                raise ValueError(
                    f"{len(d['shops'])} addresses and one carries no "
                    f"key — its identity cannot be inferred")
            sd["key"] = models.HOME_SHOP_KEY
        shops.append(Shop(**sd))
    # Every later inference resolves to THE sole address, whatever it
    # is called — never to the home key by reflex, which would mint a
    # dangling reference in a single-address save keyed otherwise.
    sole_key = shops[0].key if one_address else ""
    # Same migration for the wagon: a payload written before wagons
    # had identities carries exactly one address and one wagon kept
    # there. More than one address with no wagon list is not a payload
    # this migration can honestly interpret, so it is refused rather
    # than guessed (rev. 27 item 7).
    if "wagons" in d:
        wagons = [models.Wagon(**_addressed(w, "shop_key", "a wagon"))
                  for w in d["wagons"]]
    elif one_address:
        wagons = [models.Wagon(key=models.HOME_WAGON_KEY,
                               shop_key=sole_key)]
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
        employees=[Employee(**_addressed(e, "shop_key", "an employee"))
                   for e in d["employees"]],
        districts={k: District(**v) for k, v in d["districts"].items()},
        rivals={k: _rival_from(v, sole_key)
                for k, v in d["rivals"].items()},
        prices={k: dict(v) for k, v in d["prices"].items()},
        events=[ActiveEvent(spec=_EVENTS_BY_ID[e["id"]], days_left=e["days_left"])
                for e in d["events"]],
        evidence=[Evidence(**e) for e in d["evidence"]],
        news=list(d["news"]),
        game_over=d["game_over"], debt_paid_day=d["debt_paid_day"],
        arrested_day=d.get("arrested_day"),
        total_laundered=d["total_laundered"], raids_led=d["raids_led"],
        kills=d["kills"], demand_shock=d["demand_shock"],
        act=d["act"], branch=d["branch"],
        branch_state=_branch_state_from(d["branch_state"]),
        sitdown_snapshot=SitdownSnapshot(**d["sitdown_snapshot"])
        if d.get("sitdown_snapshot") is not None else None,
        # Typed, validated at construction (rev. 18 items 3-4):
        # malformed or inconsistent log entries are refused, never
        # round-tripped. The same presence rule as the address
        # references: an ABSENT log is history from before the ledgers
        # existed and migrates to empty; a PRESENT one must be a list,
        # because rewriting a malformed log into "nothing ever
        # happened" is the loudest silent repair in the file.
        raid_log=[RaidAttemptRecord(**e)
                  for e in _log(d, "raid_log")],
        route_log=[RouteExecutionRecord(
            **_addressed(e, "origin_shop", "a route record"))
            for e in _log(d, "route_log")],
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


def _log(d: dict, name: str) -> list:
    """One execution ledger, read by the presence rule. Absent means a
    payload written before the ledgers existed — empty history is the
    only thing it could have meant. Present means the save claims to
    carry one, so it must actually be a list; None, False, "" and {}
    are malformed, and quietly reading them as "no history" would
    erase a campaign's whole record without a word."""
    if name not in d:
        return []
    value = d[name]
    if not isinstance(value, list):
        raise ValueError(f"{name}: a ledger is a list of records, got "
                         f"{value!r}")
    return value


def _rival_from(payload: dict, sole_key: str) -> Rival:
    """A telegraphed raid is a typed value carrying its target address
    (design rev. 23 item 2). A payload written before warnings named
    an address carries the bare countdown, and with one address there
    was only one target it could ever have meant — `sole_key` is empty
    when the payload carries several, and an untargeted countdown is
    then refused rather than aimed at a guess.

    The two spellings are an EXACT SCHEMA UNION: canonical `warning`
    or legacy `raid_warning`, exactly one of them, never both and
    never neither. A payload carrying both is two sources of truth
    about the same raid with no rule for which wins; a payload
    carrying neither is a rival record shaped like no version this
    game ever wrote. Both are refused. Nothing here coerces: a
    countdown is an `int` or it is not a countdown, and erasing or
    inventing a telegraphed raid across a reload is a story failure,
    not a rounding error."""
    v = dict(payload)
    has_typed = "warning" in v
    has_legacy = "raid_warning" in v
    warning = v.pop("warning", None)
    nights = v.pop("raid_warning", None)
    if has_typed and has_legacy:
        raise ValueError(
            "a rival carries both a typed warning and a legacy "
            "countdown — two answers about the same raid, with no "
            "rule for which one is true")
    if not has_typed and not has_legacy:
        raise ValueError(
            "a rival carries no warning field at all — every version "
            "wrote one of the two, so this payload is malformed")
    if has_typed:
        if warning is None:
            v["warning"] = None                   # no raid on the board
        elif isinstance(warning, dict):
            v["warning"] = models.RaidWarning(**warning)
        else:
            raise ValueError(f"a typed warning must be a record or "
                             f"nothing, got {warning!r}")
    else:
        # `True` is not an int here — `type(...) is int` — because a
        # boolean countdown is a malformed save, not a one-night raid.
        if type(nights) is not int or nights < 0:
            raise ValueError(f"a legacy countdown must be a whole "
                             f"number of nights, got {nights!r}")
        if nights == 0:
            v["warning"] = None                   # 0 always meant none
        else:
            if not sole_key:
                raise ValueError(
                    "a telegraphed raid names no target address and "
                    "the payload carries several — which shop the "
                    "crew was coming for cannot be inferred")
            v["warning"] = models.RaidWarning(nights, sole_key)
    return Rival(**v)


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
    if payload.get("points_cycles"):
        # The points history is typed the same way and for the same
        # reason (rev. 29 item 1): both books DERIVE from these
        # records, so validation must judge real ones. A payload
        # whose shape does not fit is refused, not repaired.
        try:
            payload["points_cycles"] = [
                PointsCycleRecord(**c) for c in payload["points_cycles"]]
        except TypeError as exc:
            raise ValueError(f"partner: malformed points payload ({exc})")
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
