"""Delivery routes: legit pizzas up front, coded orders in the warmer bag."""

import os
import random
import sys
import types
from collections.abc import Callable
from dataclasses import dataclass, field

from . import data, market, models, straight, war
from .models import Employee, State
from .ui import Console, money



# Every field a route plan must name. Its ONE home is here, beside
# the plan it describes.
ROUTE_FIELDS = ("district", "driver", "ride_along", "cargo", "legit",
                "origin_shop", "wagon_key")


def _named(plan, name: str):
    """A canonical field, PRESENT. Absence is refused here rather
    than surfacing later as a KeyError from whichever line happened
    to read it first."""
    try:
        return plan[name]
    except (KeyError, TypeError):
        raise ValueError(
            f"the route names no {name!r} — a plan missing a "
            f"canonical field is malformed, not lean")


@dataclass
class RouteManifest:
    """THE wagon inventory model (rev. 17 item 1, hardened rev. 18
    item 1): one typed manifest owns cargo space, pizza space,
    remaining capacity and validation. Every quantity says what it
    counts — `cargo` maps good → UNITS (space priced per unit from
    data.GOODS), `legit` counts pizza ORDERS at one box, one
    cargo-space unit — and both share the wagon's capacity, which is
    FIXED BY THE MODEL (rev. 18: no payload chooses its own wagon).
    Parsing is strict — no coercion — and an over-capacity manifest
    is REFUSED, at commit and at resolution, never repaired and
    never merely prevented by a planning screen."""
    cargo: dict = field(default_factory=dict)
    legit: int = 0

    @property
    def capacity(self) -> int:
        return data.VEHICLE_CARGO

    @property
    def cargo_bulk(self) -> int:
        return sum(u * data.GOODS[g]["bulk"] for g, u in self.cargo.items())

    @property
    def pizza_bulk(self) -> int:
        return self.legit

    @property
    def bulk_used(self) -> int:
        return self.cargo_bulk + self.pizza_bulk

    @property
    def free(self) -> int:
        return self.capacity - self.bulk_used

    def validate(self) -> None:
        # The shared inventory-map validator (rev. 19 item 1): exact
        # integers, known goods, no negatives — one contract for the
        # wagon, the stashes and persistence alike.
        models.validate_inventory_map(self.cargo, "manifest")
        if type(self.legit) is not int \
                or self.legit < 0:
            raise ValueError(f"manifest: bad pizza count {self.legit!r}")
        if self.bulk_used > self.capacity:
            raise ValueError(f"manifest: {self.bulk_used} space loaded "
                             f"in a {self.capacity}-space wagon")

    @classmethod
    def of_plan(cls, plan) -> "RouteManifest":
        """The reading of a route plan — a typed RoutePlan hands over
        its own manifest; a legacy dictionary is parsed STRICTLY
        (rev. 18 item 1: no int() coercion — True, 1.5 and "3" are
        refused, not repaired) and refused if illegal."""
        if isinstance(plan, RoutePlan):
            # A typed plan is not automatically a valid one: a
            # manifest that is missing or of the wrong type is a
            # deliberate refusal here, not an AttributeError from the
            # next line that touches it.
            if not isinstance(plan.manifest, RouteManifest):
                raise ValueError(
                    f"a route plan carries a manifest, got "
                    f"{plan.manifest!r}")
            plan.manifest.validate()
            return plan.manifest
        # PRESENCE, never a default. An absent `cargo` or `legit` is
        # a malformed plan, and filling it in with the legal zero is
        # how a broken plan becomes an empty-manifest route nobody
        # planned. `None` is refused for the same reason.
        cargo = _named(plan, "cargo")
        legit = _named(plan, "legit")
        if type(cargo) is not dict:
            raise ValueError(
                f"a route's cargo is a mapping of good -> units, got "
                f"{cargo!r}")
        if legit is None:
            raise ValueError(
                "a route's cover is a whole number of orders, not "
                "nothing at all")
        m = cls(cargo=dict(cargo), legit=legit)
        m.validate()
        return m


@dataclass
class RoutePlan:
    """THE typed route plan (rev. 18 item 1): the manifest IS the
    inventory truth and rides inside — there are no parallel
    cargo/legit dictionaries anywhere. Legacy plan["cargo"] reads
    pass through to the one manifest; the only sanctioned writes
    (the straight branch's disposal flag, commit's clamped pizza
    count) go through the same door."""
    district: str
    driver: Employee
    ride_along: bool
    manifest: RouteManifest
    # The address this wagon rolls out of (design rev. 22 item 1).
    # Named at planning, carried into the execution record — and
    # REQUIRED, because a plan that says nothing about where the
    # wagon loads would load it at the founding address by default
    # (rev. 27 item 7).
    origin_shop: str
    # THE wagon this route rolls out in (P4b.1a). Named at planning
    # and revalidated at execution, so the night spends the vehicle
    # the plan chose rather than re-picking one by address.
    wagon_key: str
    disposal: bool = False

    @property
    def cargo(self) -> dict:
        return self.manifest.cargo

    @property
    def legit(self) -> int:
        return self.manifest.legit

    _KEYS = ("district", "driver", "ride_along", "cargo", "legit",
             "disposal", "origin_shop", "wagon_key")

    def __getitem__(self, key):
        if key in self._KEYS:
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, value) -> None:
        if key == "legit":
            self.manifest.legit = value
        elif key == "disposal":
            self.disposal = value
        else:
            raise KeyError(f"route plan field {key!r} is not writable")


def inventory_lines(label: str, stash: dict, cap: int | None) -> list[str]:
    """Inventory rendered as units × space each = space used (rev. 17
    item 1; one term, rev. 18 item 2) — the same arithmetic
    everywhere a stash is shown: the back room, the warehouse, and
    the wagon manifest."""
    total = models.space_used(stash)     # THE one arithmetic (rev. 19)
    head = f"{label} — {total}" + (f" of {cap}" if cap is not None else "") \
        + " space used:"
    lines = [head]
    for g, u in stash.items():
        if u <= 0:
            continue
        b = data.GOODS[g]["bulk"]
        lines.append(f"    {data.GOODS[g]['label']:<24} {u} × {b} space "
                     f"= {u * b}")
    if len(lines) == 1:
        lines.append("    (empty)")
    return lines


def route_suspicion(covert: int, legit: int) -> float:
    """0..1 — how wrong the route looks to anyone watching."""
    total = covert + legit
    if total == 0:
        return 0.0
    return covert / total


def validate_route_plan(state: State, plan) -> None:
    """THE per-route contract (P4b.1a review).

    One plan, checked completely, before it meets any other plan and
    long before it moves a crate. Cross-route facts — one driver
    twice, the owner riding two wagons — are the SCHEDULE's business
    and stay there; this is only about whether a single route is a
    route at all.

    Falsy is not malformed: `cargo={}`, `legit=0` and
    `ride_along=False` are ordinary legal values — an EMPTY-MANIFEST
    route with the owner staying home (a pizzas-only run is
    `cargo={}` with `legit` above zero; naming them the same thing
    would be a lie about what the plan carries). What is refused is
    falsy of the WRONG SHAPE — `cargo=False`, a missing
    `ride_along`, a driver who is not one of this world's people."""
    for name in ROUTE_FIELDS:
        _named(plan, name)
    if plan["district"] not in data.DISTRICTS:
        raise ValueError(
            f"the route names no real district: {plan['district']!r}")
    # `type(...) is bool` — riding along is a decision, and 1, "yes"
    # and None are not decisions.
    if type(plan["ride_along"]) is not bool:
        raise ValueError(
            f"riding along is a decision, got {plan['ride_along']!r}")
    if type(plan["cargo"]) is not dict:
        raise ValueError(
            f"a route's cargo is a mapping of good -> units, got "
            f"{plan['cargo']!r}")
    # `type(...) is int` excludes bool: True is not a count.
    legit = plan["legit"]
    if type(legit) is not int or legit < 0:
        raise ValueError(
            f"a route's cover is a whole number of orders, got "
            f"{legit!r}")
    # THE driver is one of this world's people, BY IDENTITY. A
    # look-alike carrying a real key compares equal as a dataclass
    # and would ride as a second copy of someone who is standing
    # somewhere else — arrested, injured, or driving another wagon.
    driver = plan["driver"]
    if not any(person is driver for person in state.employees):
        raise ValueError(
            f"the route's driver is not one of this world's people: "
            f"{getattr(driver, 'name', driver)!r}")
    # Origin and wagon as a pair, through the shared authority.
    models.plan_wagon(state, plan)
    RouteManifest.of_plan(plan).validate()


def plan_route(state: State, con: Console, rng: random.Random,
               reserved: list | None = None, *,
               wagon: models.PlannedWagon,
               origin: "models.Shop") -> "RoutePlan | None":
    """Morning: pick district, driver, cargo, cover. Returns a route plan.

    `reserved` employees (tonight's raid crew) can't also drive the route —
    one person, one job per night."""
    reserved = reserved or []
    # The address this route leaves from is CHOSEN BY THE CALLER
    # (P4b.1a): the morning menu resolves it once through the address
    # picker and hands it here, so planning never reaches for "the
    # shop" and a second address is a real choice rather than a
    # refusal.
    drivers = [e for e in state.hired()
               if e.available and e.driving >= 4 and e not in reserved]
    if not drivers:
        con.say("  Nobody free can drive — your people are spoken for tonight.")
        return None

    dist_keys = list(data.DISTRICTS)
    labels = []
    for dk in dist_keys:
        d = data.DISTRICTS[dk]
        heat = state.heat(dk)
        owner = d["rival"]
        owner_s = f", {data.RIVALS[owner]['short']}'s turf" if owner else ""
        rm = market.route_market(state, dk)
        if rm.captured:
            owner_s = ", your turf now"
        band_s = f" [{rm.heat.band.upper()}]" if rm.heat.band != "cool" \
            else ""
        labels.append(f"{d['label']} (heat {heat:.0f}{owner_s}){band_s}")
    labels.append("Cancel — no route today")
    pick = con.menu("Run today's route where?", labels)
    if pick == len(dist_keys):
        return None
    dk = dist_keys[pick]
    pol = models.district_heat_policy(state, dk)
    if not pol.plannable:
        # RED heat: the district cannot be worked (§2.6's teeth,
        # rev. 14 item 5 — enforced at planning, revalidated at
        # service).
        con.say(f"  {data.DISTRICTS[dk]['label']} is {pol.note}.")
        return None

    names = [f"{e.name} (drive {e.driving}, nerve {e.nerve}"
             f"{', not read in' if not e.aware else ''})" for e in drivers]
    driver = drivers[con.menu("Who drives?", names)]
    ride_along = con.confirm("Ride along yourself? (You can handle trouble — and be caught in it.)")

    # The wagon manifest (rev. 17 item 1): pizzas and product share
    # the wagon through ONE typed model. Every product stays on the
    # board — including rows that can't load tonight, with their
    # reasons — and the load can be revised until it's confirmed;
    # nothing silently disappears when the wagon fills.
    manifest = RouteManifest()
    can_carry = driver.aware or ride_along
    # The route-loading card (rev. 18 item 2): one vocabulary,
    # taught once per planning.
    con.say(f"  The wagon holds {manifest.capacity} space. "
            f"Each pizza uses 1. "
            + ". ".join(f"{s['label']} uses {s['bulk']} per unit"
                        for s in data.GOODS.values() if s["bulk"] > 1)
            + ". Pizzas and coded goods share the same space.")
    while True:
        for g, spec in data.GOODS.items():
            have = origin.stash.get(g, 0)
            loaded = manifest.cargo.get(g, 0)
            unit = spec["bulk"]
            price = state.prices[dk][g] \
                if state.districts[dk].known_price_age == 0 else None
            hint = f" (~{money(price)}/u here)" if price is not None else ""
            row = (f"{spec['label']} — loaded {loaded}, {unit} space "
                   f"each, {have} in the stash{hint}")
            if not can_carry:
                con.say(f"  {row} [{driver.name} isn't read in — pizzas "
                        f"only unless you ride along]")
                continue
            if have <= 0:
                con.say(f"  {row} [none in the stash]")
                continue
            if loaded == 0 and manifest.free < unit:
                con.say(f"  {row} [no room — {manifest.free} of "
                        f"{manifest.capacity} space free]")
                continue
            # Revise bound (rev. 18 item 1): planned goods never left
            # the stash, so the stash IS the ownership ceiling —
            # min(have, loaded + free // space), never have + loaded.
            top = min(have, loaded + manifest.free // unit)
            n = con.ask_int(f"Load {spec['label']}? {unit} space each, "
                            f"{manifest.free} space free{hint}",
                            0, top, loaded)
            if n:
                manifest.cargo[g] = n   # intention only — committed at service
            else:
                manifest.cargo.pop(g, None)
        # Cover has to be real: only customers who actually ordered
        # delivery — and every box takes a slot, all the way to a
        # 24-order pizza wagon (the unexplained 12 cap is gone,
        # rev. 17 item 1).
        pool = origin.delivery_pool
        row = (f"Pizzas for cover — loaded {manifest.legit}, 1 space "
               f"each ({pool} orders on the board)")
        legit_top = min(origin.ingredients, pool,
                        manifest.legit + manifest.free)
        if pool <= 0:
            con.say(f"  {row} [no delivery orders — a busier, better-liked "
                    f"shop would give you cover]")
        elif origin.ingredients <= 0:
            con.say(f"  {row} [the pantry is empty]")
        elif legit_top <= 0 and manifest.legit == 0:
            con.say(f"  {row} [no room — 0 of {manifest.capacity} "
                    f"space free]")
        else:
            manifest.legit = con.ask_int(
                f"Delivery orders to run for cover ({pool} on the board, "
                f"wagon space {manifest.free + manifest.legit})",
                0, legit_top,
                min(manifest.legit or (8 if manifest.cargo else 4),
                    legit_top))
        con.say(f"  The wagon — {manifest.bulk_used} of "
                f"{manifest.capacity} space used:")
        for g, u in manifest.cargo.items():
            b = data.GOODS[g]["bulk"]
            con.say(f"    {data.GOODS[g]['label']:<24} {u} × {b} space "
                    f"= {u * b}")
        if manifest.legit:
            con.say(f"    {'Pizzas for cover':<24} {manifest.legit} × 1 "
                    f"space = {manifest.legit}")
        if not manifest.cargo and not manifest.legit:
            con.say("    (empty)")
        if con.menu(f"The manifest — {manifest.bulk_used} of "
                    f"{manifest.capacity} space loaded:",
                    ["Revise the load", "Confirm the manifest"]) == 1:
            break
    manifest.validate()
    # §2.1 same-night telegraph: a contraband route scheduled while
    # payoff is within tonight's reach can book bust evidence (up to
    # ~20 + 0.3/unit on a ride-along search) and slam a Case gate the
    # sit-down reads tomorrow. What it books depends on the night, so
    # the warning is unconditional in that window — a printed line only;
    # the plan can still be replanned or cancelled from the morning menu.
    if manifest.cargo and _payoff_reachable_tonight(state, origin, dk,
                                                   manifest.cargo):
        con.say("  With the debt this close to settled, remember: a bad stop "
                "tonight goes into the file tomorrow's table reads.")
    return RoutePlan(district=dk, driver=driver, ride_along=ride_along,
                     manifest=manifest,
                     # Which address the wagon leaves from, and WHICH
                     # wagon. Both named at planning; the night
                     # revalidates the key rather than choosing again.
                     origin_shop=origin.key,
                     wagon_key=wagon.first)


def _payoff_reachable_tonight(state: State, shop, dk: str,
                              cargo: dict) -> bool:
    """The route warning's window (§2.1 rev. 4): the route that earns the
    final payoff money is the natural 'one last run,' so 'near payoff'
    counts what tonight could plausibly bring in, each term a supremum
    of its runtime counterpart. A sale tops out at 1.5x today's district
    price (a 1.2 offer roll times the 1.25 haggle premium); shop orders
    never exceed demand and no ticket beats gourmet, doubled to absorb a
    later policy change re-forming the order book. Overestimating only
    ever warns early."""
    if state.debt <= 0:
        return False
    proceeds = sum(u * state.prices[dk][g] * 1.5 for g, u in cargo.items())
    shop_take = 2 * shop.demand_today * data.TICKET_PRICE["gourmet"]
    return state.clean + state.dirty + shop_take + proceeds >= state.debt


# ── resolution ────────────────────────────────────────────────────

def _route_voice(plan: "RoutePlan | dict") -> dict:
    """THE route presentation, branch-aware in one place (rev. 10 item
    7): the burned coded-customer book stays burned — a disposal run
    speaks of cold buyers and one-use contacts, never a resurrected
    order board. Grammar, dice and option lists are identical; only
    the words change, and only on disposal-flagged plans."""
    if plan.get("disposal"):
        return {
            "intro": "{drops} cold buyers on a one-time list tonight — "
                     "strangers, and they know you're leaving.",
            "stop": "Stop {n}: a clearance buyer takes {want}x {label} "
                    "at {price}/unit. No names, no next time.",
            "home": "{driver} comes back with {cash} in the bag. No "
                    "board took these orders — just one-use contacts "
                    "who won't call again.",
        }
    return {
        "intro": "{drops} coded orders on the board tonight.",
        "stop": "Stop {n}: buyer wants {want}x {label} at {price}/unit.",
        "home": "{driver} comes back with {cash} in the bag "
                "and firsthand prices from {district}.",
    }


def _stop_risk(state: State, plan: "RoutePlan | dict") -> float:
    dk = plan["district"]
    susp = route_suspicion(sum(plan["cargo"].values()), plan["legit"])
    heat = state.heat(dk) / 100
    patrol = data.DISTRICTS[dk]["patrol"]
    risk = 0.05 + heat * 0.35 * patrol + susp * 0.15
    if plan["driver"].trait == "reckless":
        risk += 0.05
    if plan["driver"].trait == "known_to_police":
        risk += 0.05
    return min(0.75, risk)


# The plan fields that say WHICH ROUTE THIS IS. Anything here changing
# after departure means the wagon that left is not the wagon being
# resolved.
_IDENTITY_FIELDS = ("district", "origin_shop", "wagon_key",
                    "ride_along", "disposal")

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_PACKAGE_DIR)

COMMIT_SCOPE = "commit"
PROBE_SCOPE = "probe"

# THE DECLARED SLOTS: `(role, file, function)`. A slot is a
# DECLARATION, not a credential — nothing here is ever compared
# against a caller; the file and name only say WHERE TO READ the code
# that the grant must then match, byte for byte. Each
# slot is filled ONCE, at import, by the module that owns the code,
# which hands over the function itself; the guard then asks whether
# THAT EXACT CODE OBJECT is on the stack.
#
# Five guards have died on this line, every one by authenticating a
# NAME instead of an IDENTITY: `__name__` (which is `__main__` under
# `python -m`, and refused the sanctioned probe); a basename (which let
# `/tmp/route_support.py` through); a module-level token (reachable as
# `routes._DEPARTURE_TOKEN`); an absolute path plus a function name —
# which a function COMPILED WITH THOSE STRINGS walked straight
# through:
#
#     ns = {"__file__": "<repo>/tests/route_support.py"}
#     exec(compile("def departed(s, p, r):\n"
#                  "    return r.record_departure_for_probe(s, p)\n",
#                  "<repo>/tests/route_support.py", "exec"), ns)
#     ns["departed"](state, plan, routes)   # -> an amber departure
#
# …and then, found while trying to break the fix, a LOOKUP THROUGH
# `sys.modules`: resolving the sanctioned function by module name at
# guard time meant a fake module registered under that name, carrying
# the sanctioned `__file__`, was resolved and honoured. Reading the
# authority by name is the same defect one level up. So the authority
# is not read at all — it is HANDED OVER, once, by the module that
# compiled it.
#
# AND NOT KEYED ON THE MODULE NAME. Keying the slot on
# `func.__module__` was the FIRST guard's death repeated: under
# `python -m analysis.experiments` the probe's module name is
# `__main__`, so the sanctioned probe could not grant its own scope
# and the fork battery died at import. A module name says how a file
# was invoked, not what it is. The file and the function name locate
# the code; the code itself is what is checked.
_SCOPE_SLOTS = frozenset({
    (COMMIT_SCOPE, os.path.join(_PACKAGE_DIR, "phases.py"),
     "_commit_route"),
    (PROBE_SCOPE, os.path.join(_REPO_ROOT, "analysis", "experiments.py"),
     "_heat_exposure_probe"),
    (PROBE_SCOPE, os.path.join(_REPO_ROOT, "tests", "route_support.py"),
     "departed"),
})

# Filled slot -> (code object, defining namespace). Empty at import of
# this module, and a role with no filled slot authorises NOBODY: a
# shipped game never imports the test support, so the probe seam is not
# a live door in it.
_GRANTED: dict = {}


def _declared_code(path: str, name: str):
    """The code object the DECLARED FILE compiles `name` to, read from
    disk at grant time.

    This is what makes the grant a capability rather than a claim.
    Code objects compare by body, argument shape, constants and line
    number, and NOT by `co_filename` — so a look-alike compiled from a
    string cannot equal this, whatever filename it was compiled with,
    while the real function compiled from the real file does. A forger
    who reproduces this exactly has not bypassed anything: they have
    reproduced the sanctioned function, and it does what the sanctioned
    function does.

    Top-level definitions only, deliberately: a nested look-alike
    buried in the same file is not the sanctioned scope."""
    with open(path, encoding="utf-8") as handle:
        module_code = compile(handle.read(), path, "exec")
    for const in module_code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == name:
            return const
    return None


def grant_departure_scope(role: str, func: Callable) -> None:
    """A sanctioned module HANDS OVER its own function, at import.

    This is the capability. It is not a password and not a name: the
    caller passes the function object it just compiled, and this
    records the code object and the namespace it was defined in. Only
    a declared slot can be filled, only from the declared file, only
    with THAT FILE'S OWN CODE, and ONLY ONCE — so the authority is
    claimed by whoever compiled the real module, at the moment the
    engine loads.

    The failure mode is deliberate and LOUD. If something else fills a
    slot first, the real module's own grant raises at import and the
    engine does not start. A forged departure is therefore only
    reachable in a process where the real engine never loaded — which
    is a process that cannot run the game."""
    name = getattr(func, "__name__", "")
    declared = {path for role_, path, name_ in _SCOPE_SLOTS
                if (role_, name_) == (role, name)}
    if not declared:
        raise ValueError(
            f"({role!r}, {name!r}) is not a declared departure scope — "
            f"the scopes a route may depart from are fixed in `routes`")
    origin = func.__globals__.get("__file__") or ""
    path = os.path.abspath(origin) if origin else ""
    if path not in declared:
        raise ValueError(
            f"the departure scope ({role!r}, {name!r}) is defined in "
            f"{sorted(declared)!r}, not in {origin!r}")
    slot = (role, path, name)
    # …AND IT MUST BE THAT FILE'S CODE. The path above is a string a
    # forger sets freely; this is not. Without it, a function compiled
    # from a string and granted before the real module imported filled
    # the slot and departed a route.
    #
    # WHAT is being granted is settled before WHETHER the slot is free,
    # so a look-alike is refused for being a look-alike whatever the
    # grant order was — and so the one-shot refusal below can only ever
    # be reached by the genuine code, which makes "somebody else got
    # here first" mean what it says.
    if func.__code__ != _declared_code(path, name):
        raise ValueError(
            f"the departure scope {slot!r} is granted by the code "
            f"{path!r} defines, not by a look-alike carrying its name")
    if slot in _GRANTED:
        raise ValueError(
            f"the departure scope {slot!r} is granted once, at import, "
            f"by the module that owns the code")
    _GRANTED[slot] = (func.__code__, func.__globals__)


def _exact_chain(expected: list) -> bool:
    """THE AUTHORISED CALL EDGE, frame by adjacent frame.

    Called from `_make_departure`, so the walk starts at whoever
    called it and proceeds outward with NOTHING allowed in between:
    each frame must be the expected code object in the expected
    namespace, and its immediate caller must be the next one.

    Being inside a sanctioned function's dynamic extent is NOT the
    same as being its authorised caller, and treating them as the same
    was a live production bypass. `_commit_route` calls
    `Console.bullet` before it claims a wagon — to say a route is
    scrubbed — and a console whose `bullet` reached for
    `depart_at_commit` got a valid departure, because `_commit_route`
    was still an ancestor on the stack. It resolved: clean cash
    2000 → 2032, address legit revenue 0 → 32 and a route record
    written, while the pantry stayed at 40 and the wagon claims stayed
    empty. No fabrication and no forged code — the ordinary public
    maker, during an ordinary engine callback.

    So the commit role asks a stricter question than "is a sanctioned
    function somewhere below me": it asks whether THIS call is the one
    edge the design sanctions."""
    frame: "types.FrameType | None" = sys._getframe(2)
    for code, namespace in expected:
        if frame is None:
            return False
        if frame.f_code is not code or frame.f_globals is not namespace:
            return False
        frame = frame.f_back
    return True


def _commit_chain() -> "list | None":
    """`_make_departure` ← `depart_at_commit` ← `phases._commit_route`,
    and nothing else, in that order and adjacent.

    `depart_at_commit`'s code is captured at import (below its
    definition) rather than looked up here, so the first link is not a
    module attribute a later rebind could move."""
    granted = [v for slot, v in _GRANTED.items()
               if slot[0] == COMMIT_SCOPE]
    if len(granted) != 1 or _DEPART_AT_COMMIT_CODE is None:
        return None
    return [(_DEPART_AT_COMMIT_CODE, globals()), granted[0]]


def _within(role: str) -> bool:
    """Is this call inside the dynamic extent of a sanctioned
    function — the REAL one?

    THE PROBE ROLE ONLY. Dynamic extent is the right question there
    and only there: the analysis probe makes its call from a closure
    of its own (`_heat_exposure_probe.night`), so the sanctioned frame
    is genuinely an ancestor rather than the immediate caller. The
    commit role uses `_exact_chain` instead — see the bypass recorded
    there.

    Two identity checks per frame, and not one string comparison: the
    frame's code object IS the granted code object, and the frame's
    globals ARE the namespace that code was defined in. A look-alike
    compiled from a string is a different code object in a different
    namespace and fails both, whatever it is called and whatever
    `__file__` it carries.

    The whole stack is walked, unbounded, because "inside the dynamic
    extent" is exactly the authorisation: a sanctioned function may
    make the call from a closure of its own (the analysis probe does,
    from `_heat_exposure_probe.night`). The old depth bound existed to
    stop an unrelated deep stack colliding on a basename; identity
    cannot collide, so the magic number goes.

    WHAT THIS DOES NOT DEFEND AGAINST, stated plainly: code that
    rebinds the granted function's own module contents, or that fills a
    slot before the engine imports — and the second of those stops the
    engine importing at all. Neither is a bypass of this guard; both
    are a rewrite of the engine, and the same power replaces
    `resolve_route` outright. No Python guard reaches past that."""
    granted = [v for slot, v in _GRANTED.items() if slot[0] == role]
    if not granted:
        return False
    frame: "types.FrameType | None" = sys._getframe(1)
    while frame is not None:
        for code, namespace in granted:
            if frame.f_code is code and frame.f_globals is namespace:
                return True
        frame = frame.f_back
    return False


def _caller() -> tuple:
    """The first frame OUTSIDE this module, so a wrong call site names
    itself in the refusal. Found by namespace identity rather than by
    a frame count, which stays right however deep the makers nest."""
    frame: "types.FrameType | None" = sys._getframe(1)
    while frame is not None and frame.f_globals is globals():
        frame = frame.f_back
    if frame is None:                                  # pragma: no cover
        return ("<unknown>", "<unknown>")
    return (os.path.abspath(frame.f_globals.get("__file__", "")),
            frame.f_code.co_name)


def _fingerprint(plan) -> tuple:
    """WHICH ROUTE THIS IS AND WHAT IT CARRIES, frozen at departure.
    `RouteDeparture` is frozen but its PLAN is not: a caller could
    record a Meadows departure, set `plan.district` to University Hill
    and resolve — execution updated University Hill while the ledger
    recorded Meadows — or leave the identity alone and raise
    `manifest.legit` from 0 to 2, which moved clean cash 2000 → 2032.

    The COMMITTED LOAD is part of it, cargo map included item by item
    so an in-place edit cannot slip past a length check. The driver is
    fingerprinted BY IDENTITY, not by key, because a look-alike
    carrying a real key is the substitution `validate_route_plan`
    already refuses elsewhere."""
    driver = plan["driver"]
    cargo = plan["cargo"]
    return (tuple(plan.get(f) for f in _IDENTITY_FIELDS),
            id(driver), getattr(driver, "key", None),
            tuple(sorted(cargo.items())), plan["legit"])


# WHAT A SPENT DEPARTURE HOLDS: nothing. See `RouteDeparture.claim`.
_SPENT = object()


@dataclass(frozen=True, eq=False)
class RouteDeparture:
    """A ROUTE THAT LEFT. The only thing `resolve_route` accepts.

    A morning plan is an INTENTION and stays one: it carries no
    execution truth, because a field on the plan is a field anybody
    can set. The first version of this correction hung the market view
    on `RoutePlan` and was forged three ways — the constructor took it
    directly, dict plans bypassed the write-once guard entirely, and
    the reader accepted any non-`None` object, so University Hill's
    view attached to a Meadows plan resolved and logged University
    Hill.

    This value is produced ONLY by a departure that survived every
    refusal, and it binds the three things that make it one:

      * `state` BY IDENTITY — a departure cannot be replayed against
        a different world;
      * `plan`, the exact route;
      * `market`, the district as it stood when the wagon left.

    Its own contract is checked at construction: the market must
    describe THIS plan's district, and its band must be one a route
    can execute under. A red band cannot become a departure at all."""
    # EVERY FIELD IS `init=False`, so there is no constructor to call
    # at all. A module-level token was not enough: it was reachable
    # from outside as `routes._DEPARTURE_TOKEN`, and passing it built
    # a departure. The factory below allocates the object itself and
    # fills these in directly.
    state: State = field(init=False)
    # `RoutePlan` or a legacy dict plan — both answer `plan["field"]`,
    # which is the only thing this value asks of it.
    plan: "RoutePlan | dict" = field(init=False)
    # DERIVED, never supplied. A caller who could hand in a market
    # could hand in ANOTHER WORLD'S: a cool Meadows view from state B
    # attached to an amber Meadows route in state A resolved and
    # logged cool.
    market: "market.RouteMarket" = field(init=False)
    identity: tuple = field(init=False)

    def __post_init__(self) -> None:
        raise ValueError(
            "a departure is made by the route that left, not "
            "constructed: it comes from the commit path")

    def claim(self) -> tuple:
        """TAKE THE WAGON — every refusal first, then the departure is
        SPENT, and spent means GONE rather than flagged.

        A wagon goes out once. The previous version recorded that in a
        one-element list on the value, and a public mutable field is
        not a fact: after one resolution, `departure.spent[0] = False`
        allowed another, moving clean cash 2000 → 2032 → 2064, address
        revenue 32 → 64 and writing two log rows for one night. There
        is no flag here to reset. The state, the plan and the market
        are handed to the caller and then struck off the value, so a
        second resolution has nothing to run and no field a caller can
        put back short of rebuilding the departure by hand.

        EVERY CHECK PRECEDES THE STRIKE-OFF, so a refusal leaves both
        the world and the departure exactly as they were. The
        departure's own construction contract is RE-CHECKED here, not
        merely trusted: `_make_departure` verified it once, and a value
        that reached this method some other way must satisfy it again.
        A hand-built departure therefore still cannot run a red
        district, cannot run a market view belonging to some other
        district, and cannot run a plan the canonical contract
        refuses."""
        if self.state is _SPENT:
            raise ValueError(
                "this route already ran tonight — a departure "
                "resolves once")
        # THE ROUTE FIRST, and it is the one that left carrying what it
        # left with. Ordered ahead of the market checks deliberately: a
        # plan edited after departure makes the view disagree with the
        # plan too, and "this route changed after it departed" is the
        # diagnosis, where "the market is for another district" is only
        # its symptom.
        if _fingerprint(self.plan) != self.identity:
            raise ValueError(
                "this route changed after it departed — the wagon "
                "that left is not the one being resolved")
        if not isinstance(self.market, market.RouteMarket):
            raise ValueError(
                "this departure carries no route market — a route "
                "runs under the district it left under, not under a "
                "look-alike")
        if self.market.district != self.plan["district"]:
            raise ValueError(
                f"this departure carries {self.market.district!r}'s "
                f"market for a route into {self.plan['district']!r}")
        if self.market.heat.band not in models.ROUTE_EXECUTED_BANDS:
            raise ValueError(f"a route cannot run under "
                             f"{self.market.heat.band!r}")
        # THE canonical contract, and the resolution-side manifest
        # refusal (rev. 17 item 1): the night runs no route the game
        # would refuse and no manifest the wagon could not carry,
        # whoever built the dict. Both were downstream of the
        # strike-off until now, which would have spent a departure on
        # its way to refusing it.
        validate_route_plan(self.state, self.plan)
        RouteManifest.of_plan(self.plan)
        taken = (self.state, self.plan, self.market)
        for name in ("state", "plan", "market", "identity"):
            object.__setattr__(self, name, _SPENT)
        return taken


def _make_departure(state: State, plan, role: str,
                    where: str) -> "RouteDeparture":
    """THE one construction — AND THE GUARD LIVES HERE, in the maker
    itself, not in a wrapper around it.

    A leading underscore is a convention, not a scope. The previous
    version guarded only the two public wrappers and left this
    reachable: `routes._make_departure(state, plan)` produced a real
    departure, and resolving it moved clean cash 2000 → 2032 and wrote
    a `RouteExecutionRecord` while the pantry stayed at 40 and no
    wagon had ever been claimed. There is now no second maker to find,
    because there is no unguarded maker at all.

    Validates the plan, so a malformed route never becomes a
    departure, and refuses a band no route can execute under."""
    # THE COMMIT ROLE ASKS FOR THE EXACT CALL EDGE, not for a
    # sanctioned ancestor: production departures happen at one place
    # in the engine, and a callback made from inside `_commit_route`
    # is not that place. The probe role keeps dynamic extent, which is
    # separately justified — the analysis probe calls from its own
    # closure.
    if role == COMMIT_SCOPE:
        chain = _commit_chain()
        authorised = chain is not None and _exact_chain(chain)
    else:
        authorised = _within(role)
    if not authorised:
        path, name = _caller()
        raise ValueError(
            f"a route departs from {where}, not from {name!r} in "
            f"{path!r}")
    validate_route_plan(state, plan)
    view = market.route_market(state, plan["district"])
    if view.heat.band not in models.ROUTE_EXECUTED_BANDS:
        raise ValueError(f"a route cannot depart under "
                         f"{view.heat.band!r}")
    departure = object.__new__(RouteDeparture)
    for name, value in (("state", state), ("plan", plan),
                        ("market", view),
                        ("identity", _fingerprint(plan))):
        object.__setattr__(departure, name, value)
    return departure


def depart_at_commit(state: State, plan) -> "RouteDeparture":
    """THE production maker, and `_commit_route` is the only thing
    that may call it — not merely the only thing that must be
    somewhere beneath it."""
    return _make_departure(state, plan, COMMIT_SCOPE,
                           "`_commit_route`, called directly")


# CAPTURED AT DEFINITION, not read back by name. `_commit_chain` needs
# the first link of the authorised edge, and a module attribute is
# something a later rebind can move; the function object created right
# here cannot be.
_DEPART_AT_COMMIT_CODE = depart_at_commit.__code__


def record_departure_for_probe(state: State, plan) -> "RouteDeparture":
    """THE departure-time market authority, and its only writer.

    A route's band and every territorial factor are fixed at the
    moment it departs — after the service-time red revalidation has
    accepted it and at the instant its wagon is claimed — and
    resolution consumes exactly this view. Rebuilding it at
    resolution made two simultaneous routes depend on iteration
    order: both departed at heat 71.45, the first pushed the district
    to 96.6, and the second was then classified red for a wagon that
    had already left.

    One home, so a caller that wants a departed route asks for a
    DEPARTURE rather than assembling a market view of its own — the
    alternative is the second spelling this project treats as a defect
    class. It RETURNS the value and mutates nothing: the plan is still
    the morning's intention when this is done.

    The plan is validated here, so a malformed route cannot become a
    departure, and `RouteDeparture` refuses a red band — neither a
    broken plan nor a burning district produces one."""
    return _make_departure(
        state, plan, PROBE_SCOPE,
        "the analysis probe and the centralised test support")


def resolve_route(departure: "RouteDeparture", con: Console,
                  rng: random.Random) -> dict:
    """Run the route that departed, under the market it departed
    under. The DEPARTURE is the only input: a plan alone cannot be
    resolved, because a plan alone never left.

    EVERYTHING IS CHECKED BEFORE ANYTHING MOVES. The first version of
    this correction read the departure AFTER booking cover revenue and
    docking reputation, so an undeparted route raised as designed and
    still moved money on the way out — clean 2000 → 2032, address
    revenue 0 → 32, reputation 50 → 47 — while a pin that only
    inspected `route_log` called it clean."""
    if not isinstance(departure, RouteDeparture):
        raise ValueError(
            "a route resolves from the departure it made, never from "
            "a plan or a market view handed in on its own")
    # ONE CLAIM, BEFORE ANYTHING MOVES. It refuses unless the route is
    # the one that left carrying what it left with, its market is this
    # district's and executable, the canonical contract still holds and
    # the wagon has not already gone out tonight — and only then hands
    # over the three things this night runs on, striking them off the
    # departure as it goes. Without the contract check here a route
    # missing its wagon completed and appended a RouteExecutionRecord:
    # a wagonless ghost route becoming real history.
    #
    # `rm` IS THE ROUTE-MARKET VIEW RECORDED AT DEPARTURE (rev. 15
    # item 5). The RouteMarket's territorial-demand factors compose in
    # `market.route_market`, and this resolution consumes the
    # departure's view for them. Narrowed deliberately (review of the
    # second correction): raw stop risk still reads LIVE heat at
    # resolution, so "every territorial factor" promised more than this
    # correction implements. The typed record below carries the band
    # and multiplier so no study samples exposure at the wrong time
    # (rev. 18 item 4).
    #
    # FAIL CLOSED WITHOUT ONE. Synthesising the view here is exactly
    # the side entrance this correction closes: a caller who never
    # departed would resolve under whatever the district happens to
    # read now, which is how an already-departed route came to be
    # classified red by a sibling route's own heat.
    state, plan, rm = departure.claim()
    dk = plan["district"]
    # The address this wagon rolled out of (design rev. 22 item 1) —
    # the record carries it, and chronology is keyed on it.
    origin = plan["origin_shop"]
    origin_shop = state.shop_by_key(origin)
    home_shop = origin_shop            # unsold product rides back home
    driver: Employee = plan["driver"]
    cargo = plan["cargo"]
    dspec = data.DISTRICTS[dk]
    report: dict = {"sold": 0, "cash": 0, "busted": False, "lines": []}

    # Legit stops: cover, clean revenue, and food-quality exposure.
    if plan["legit"]:
        ticket = data.TICKET_PRICE[origin_shop.price]
        late = sum(cargo.values()) > 0 and plan["legit"] < sum(cargo.values())
        state.clean += plan["legit"] * ticket
        origin_shop.legit_revenue_today += plan["legit"] * ticket
        if late:
            origin_shop.reputation = max(0.0, origin_shop.reputation - 3)
            report["lines"].append("Pizzas ran late around the extra stops. Two refunds, one review.")

    if not cargo:
        state.districts[dk].known_price_age = 0 if plan["ride_along"] else 1
        driver.routes_survived += 1
        state.route_log.append(models.RouteExecutionRecord.of_market(
            state.day, rm, 0, 0, origin))
        return report

    drops = rm.drops(len(cargo))

    if plan["ride_along"]:
        _interactive_drops(state, plan, rm, home_shop, drops, con, rng,
                           report)
        state.districts[dk].known_price_age = 0
    else:
        _auto_drops(state, home_shop, plan, drops, con, rng, report)

    # Rival turf: they notice volume moving through their neighborhood.
    owner = dspec["rival"]
    corner_applied = 0.0
    if owner and report["sold"] > 0 and state.rivals[owner].alive:
        models.adjust_relation(state, owner, -(report["sold"] * 0.4))
        report["lines"].append(
            f"{data.RIVALS[owner]['short']}'s people watched the car all night.")
        # The corner channel (§2.4.3): in the war, units sold in the
        # target's turf divert their income through the one damage
        # authority, priced by the same route-market view that shaped
        # the night. A capture mid-route is detected by the authority.
        corner_applied = war.corner_diversion(
            state, dk, owner, report["sold"], report,
            rate=rm.corner_rate, cap=rm.corner_cap)
        if models.vendetta_locked(state, owner) \
                and not state.rivals[owner].alive:
            report["lines"].append(
                f"{data.RIVALS[owner]['short']}'s organization broke "
                f"tonight — the corners finished what the jobs started.")

    state.add_heat(dk, 2 + report["sold"] * 0.35
                   + route_suspicion(sum(cargo.values()), plan["legit"]) * 6)
    if not report["busted"]:
        driver.routes_survived += 1
        driver.familiarity[dk] = min(10, driver.familiarity.get(dk, 0) + 1)
    state.route_log.append(models.RouteExecutionRecord.of_market(
        state.day, rm, report["sold"], round(corner_applied * 100),
        origin))
    return report


def _sell(state: State, dk: str, good: str, units: int, price_mult: float,
          report: dict) -> None:
    price = int(state.prices[dk][good] * price_mult)
    cash = price * units
    state.dirty += cash
    report["sold"] += units
    report["cash"] += cash
    market.record_sales(state, dk, good, units)


def _interactive_drops(state: State, plan, rm: "market.RouteMarket",
                       home_shop, drops: int, con: Console,
                       rng: random.Random, report: dict) -> None:
    # The stops are handed the SAME claimed departure the resolution
    # runs on — a second reader here would be a second answer to "what
    # was this district like when the wagon left". They are passed in
    # rather than re-read off the departure, which by now is spent: a
    # wagon that has gone out has nothing left to ask.
    dk = plan["district"]
    cargo = plan["cargo"]
    voice = _route_voice(plan)
    con.say("")
    con.say(f"  You ride shotgun. {plan['driver'].name} drives. "
            + voice["intro"].format(drops=drops))
    for stop in range(drops):
        goods_left = [g for g, u in cargo.items() if u > 0]
        if not goods_left:
            break
        g = rng.choice(goods_left)
        spec = data.GOODS[g]
        base_price = state.prices[dk][g]
        # A disposal run prices like a seller without a network (rev. 9
        # item 1): the haircut replaces the ordinary offer roll, draw
        # for draw, on the same stream.
        mult = rng.uniform(straight.DISPOSAL_HAIRCUT_LO,
                           straight.DISPOSAL_HAIRCUT_HI) \
            if plan.get("disposal") else rng.uniform(0.85, 1.2)
        offer = int(base_price * mult)
        top_want = rm.top_want()
        want = min(cargo[g], rng.randint(1, top_want))
        choice = con.menu(
            voice["stop"].format(n=stop + 1, want=want, label=spec["label"],
                                 price=money(offer)),
            ["Sell", "Haggle (nerve)", "Skip this stop"])
        if choice == 2:
            continue
        if choice == 1:
            if rng.random() < 0.35 + plan["driver"].nerve * 0.03:
                offer = int(offer * 1.25)
                con.say("  They grumble and pay the new number.")
            else:
                con.say("  They walk. The pizza goes cold on the seat.")
                continue
        cargo[g] -= want
        _sell(state, dk, g, want, offer / base_price, report)
        con.say(f"  +{money(offer * want)} dirty.")

        if rng.random() < _stop_risk(state, plan) \
                and not _handle_police_stop(state, plan, con, rng, report):
            return   # busted: route over

    # Unsold product rides home.
    for g, u in cargo.items():
        if u > 0:
            home_shop.stash[g] = home_shop.stash.get(g, 0) + u


def _handle_police_stop(state: State, plan: "RoutePlan | dict", con: Console,
                        rng: random.Random, report: dict) -> bool:
    """Blue lights in the mirror. Returns False if the route ends here."""
    driver = plan["driver"]
    con.say("")
    con.say("  Blue lights. A patrol car crawls up behind the wagon.")
    choice = con.menu("What's the play?",
                      ["Play it cool (driver's nerve)",
                       f"Slip him a bribe ({money(300)} dirty)",
                       "Floor it (driver's driving)"])
    if choice == 1 and state.dirty >= 300:
        state.dirty -= 300
        if rng.random() < 0.8:
            con.say("  He tucks the bills under his citation pad and waves you off.")
            state.add_case(2, "a patrolman on the take knows your face",
                           kind="witness")
            return True
        con.say("  Wrong cop. He steps back and calls it in.")
        return _bust(state, plan, con, rng, report, resisted=False)
    if choice == 2:
        if rng.random() < 0.25 + driver.driving * 0.06:
            con.say(f"  {driver.name} loses him in the harbor alleys. Heart rates recover.")
            state.add_heat(plan["district"], 12)
            return True
        con.say("  The wagon fishtails into a fence. It's over.")
        return _bust(state, plan, con, rng, report, resisted=True)
    # play it cool
    if rng.random() < 0.35 + driver.nerve * 0.06:
        con.say("  'Delivery for the night shift.' He checks a box and lets you go.")
        return True
    con.say("  He asks to see the warmer bags.")
    return _bust(state, plan, con, rng, report, resisted=False)


def seize_cargo(plan: "RoutePlan | dict") -> int:
    """THE seizure: count the units AND empty the manifest, in ONE
    call, returning what was taken.

    "Reported seized" and "actually gone" were two facts kept in two
    places, and only one of the two bust arms made them agree. The
    interactive stop counted and cleared; the delegated arrest counted
    and did not, so the shared return loop at the end of that branch
    handed every "seized" unit back to the origin's stash — the
    player was told the load was in an evidence locker and found it
    on the shelf in the morning. One call now decides both halves,
    because a seizure that leaves the goods behind is not a seizure
    and no caller should be able to spell only half of it."""
    cargo = plan["cargo"]
    seized = sum(cargo.values())
    for g in cargo:
        cargo[g] = 0
    return seized


def _bust(state: State, plan: "RoutePlan | dict", con: Console, rng: random.Random,
          report: dict, resisted: bool) -> bool:
    seized_units = seize_cargo(plan)
    fine = min(state.dirty + state.clean, 500)
    state.dirty -= min(state.dirty, fine)
    state.add_heat(plan["district"], 20)
    state.add_case(8 + (6 if resisted else 0) + seized_units * 0.3,
                   "product seized in a traffic stop")
    if plan["ride_along"]:
        # You were in the car. That is now a fact the Case owns.
        state.add_case(6, "the owner was in the vehicle when it was searched")
        con.say("  They photograph you next to the open warmer bags.")
    driver = plan["driver"]
    if seized_units > 0 and not driver.arrested:
        arrest_odds = 0.35 if plan["ride_along"] else 0.6
        if rng.random() < arrest_odds:
            driver.arrested = True
            models.release_from_posts(state, driver, "arrest")
            report["lines"].append(f"{driver.name} is booked for possession.")
            con.say(f"  They take {driver.name} in. The wagon gets towed.")
    report["busted"] = True
    report["lines"].append("The cargo is gone and your name is in a report.")
    con.say(f"  Seized: {seized_units} units. The night is a total loss.")
    return False


def _auto_drops(state: State, home_shop, plan: "RoutePlan | dict", drops: int,
                 con: Console,
                rng: random.Random, report: dict) -> None:
    """Driver runs the route alone. One risk roll decides the night."""
    dk = plan["district"]
    driver = plan["driver"]
    cargo = plan["cargo"]
    fam = driver.familiarity.get(dk, 0)
    risk = _stop_risk(state, plan) * (1.15 - driver.nerve * 0.05) \
        * max(0.5, 1.0 - fam * 0.07)
    if rng.random() < max(0.03, risk):
        # It goes wrong out of your sight.
        if rng.random() < 0.5:
            # THE seizure authority, the same one the traffic stop
            # uses: counted and TAKEN. Counting alone left the units
            # in the manifest, and the return loop below then carried
            # them home — the defect this correction exists for.
            seized = seize_cargo(plan)
            driver.arrested = True
            models.release_from_posts(state, driver, "arrest")
            state.add_heat(dk, 18)
            evidence = 10 if driver.aware else 4
            # Physical, not witness: the record is dominated by the
            # seizure and the arrest report, which no settlement may ever
            # soften. (Splitting an aware driver's what-they-know premium
            # into its own witness record would change float-addition
            # order and break bit-exact Case identity; if that premium
            # should be remediable, it becomes a separate record in a
            # deliberate balance pass, not here.)
            state.add_case(evidence + seized * 0.3,
                           f"{driver.name} arrested on a route",
                           kind="physical", source=driver.key)
            report["busted"] = True
            report["lines"].append(
                f"{driver.name} didn't come back. Precinct says possession, "
                f"{seized} units seized.")
        else:
            lost = max(1, sum(cargo.values()) // 2)
            for g in list(cargo):
                take = min(cargo[g], lost)
                cargo[g] -= take
                lost -= take
            report["lines"].append(
                f"{driver.name} got jumped near the drop. Half the load is gone.")
            driver.morale -= 2
        for g, u in cargo.items():
            if u > 0:
                home_shop.stash[g] = home_shop.stash.get(g, 0) + u
        return

    sell_frac = min(1.0, (0.40 + driver.driving * 0.045 + driver.nerve * 0.03
                          + fam * 0.04) * (drops / 3))
    for g in list(cargo):
        units = int(cargo[g] * sell_frac)
        if units:
            cargo[g] -= units
            # Disposal runs sell at the haircut, same draw (rev. 9).
            mult = rng.uniform(straight.DISPOSAL_HAIRCUT_LO,
                               straight.DISPOSAL_HAIRCUT_HI) \
                if plan.get("disposal") else rng.uniform(0.9, 1.05)
            _sell(state, dk, g, units, mult, report)
    for g, u in cargo.items():
        if u > 0:
            home_shop.stash[g] = home_shop.stash.get(g, 0) + u
    report["lines"].append(_route_voice(plan)["home"].format(
        driver=driver.name, cash=money(report["cash"]),
        district=data.DISTRICTS[dk]["label"]))
    state.districts[dk].known_price_age = 0
