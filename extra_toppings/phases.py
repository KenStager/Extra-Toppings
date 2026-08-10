"""The daily rhythm: Morning (prepare) → Service (operate) → Night (settle).

Randomness is split by domain (see rng.Streams): the world's dice — prices,
events, rumors, suppliers, demand — are drawn per-day and cannot be shifted
by anything the player does. Player-facing dice use persistent streams.
"""

import random
from dataclasses import dataclass, field

from . import (data, escrow, evidence, market, models, raids, rivals,
               routes, shop, straight, war)
from .config import GameConfig
from .models import Shop, SitdownSnapshot, State, case_prefix
from .rng import Streams
from .ui import Console, money

QUALITY_LEVELS = ["cheap", "standard", "gourmet"]


# ── THE night-assignment authority (rev. 15 item 2) ───────────────

def routes_planned(state: "State", plans: dict) -> dict:
    """Tonight's routes, keyed BY THE ADDRESS THEY LEAVE FROM, in
    stable key order (P4b.1a).

    The schema is a mapping rather than a single slot because canon
    has both wagons running real routes, simultaneously, one per
    address per night (rev. 22 items 1 and 4). A lone `plans["route"]`
    cannot represent that, and a list would put the answer back on
    list position.

    A mapping introduces one new way to disagree with yourself — the
    filing key and the plan's own `origin_shop` — so THIS is where
    that is refused. A route filed under shop 1 while naming shop 2
    would load one address's stock and reserve the other's wagon."""
    if "routes" not in plans:
        raise ValueError(
            "this plan set carries no route schedule — a night with "
            "no routes says so with {'routes': {}}")
    planned = plans["routes"]
    if type(planned) is not dict:
        raise ValueError(
            f"the route schedule is a mapping of address -> plan, "
            f"got {planned!r}")
    out = {}
    for key in sorted(planned):
        plan = planned[key]
        # PRESENCE, never truthiness — the save layer's own rule.
        # None, {} and False here used to read as "no route", which
        # turns a malformed schedule into an empty one and loses a
        # night's work without a word.
        if not isinstance(plan, (dict, routes.RoutePlan)):
            raise ValueError(
                f"the route filed under {key!r} is not a plan, got "
                f"{plan!r}")
        state.shop_by_key(key)          # KeyError on a ghost address
        # THE per-route contract, applied HERE — at the only place
        # routes are read from storage. Validating in `route_schedule`
        # alone left every earlier reader (`night_reserved`, the
        # morning menus, `planned_jobs_at`) looking at unchecked
        # plans, so a missing field still surfaced as a KeyError from
        # whichever line touched it first. Nothing downstream sees an
        # unvalidated route now, because there is no other door.
        routes.validate_route_plan(state, plan)
        origin = plan_origin(state, plan)
        if origin != key:
            raise ValueError(
                f"a route filed under {key!r} says it leaves from "
                f"{origin!r} — one address, or neither")
        out[key] = plan
    return out


def route_schedule(state: "State", plans: dict) -> list:
    """THE night's routes, validated AS A SET before any of them
    moves a crate (P4b.1a review).

    Committing routes one at a time validates each in isolation, and
    isolation is exactly where shared resources hide: two routes can
    each name a legal driver and name the SAME one, or each ride
    along and put the owner in two wagons at once. Worse, route one
    would already have spent its stock before route two raised. So
    the whole schedule is preflighted here — every pairing, manifest
    and district, and every resource shared between them — and only
    then does anything commit."""
    scheduled = routes_planned(state, plans)
    drivers: dict = {}
    riding: list = []
    for shop_key, plan in scheduled.items():
        # `routes_planned` has already applied the per-route
        # contract, so ONLY the facts a single route cannot know are
        # left here. The driver is keyed by identity, which that
        # contract has already proved is one of this world's people,
        # so a look-alike cannot slip past as a second person.
        driver = plan["driver"]
        seen = drivers.get(id(driver))
        if seen is not None:
            raise ValueError(
                f"{driver.name} is driving the route out of {seen!r} "
                f"and the one out of {shop_key!r} — one person, one "
                f"job a night")
        drivers[id(driver)] = shop_key
        if plan["ride_along"]:
            riding.append(shop_key)
    if len(riding) > 1:
        raise ValueError(
            f"you cannot ride along on {len(riding)} routes at once: "
            f"{riding}")
    return list(scheduled.items())


def night_reserved(state: "State", plans: dict,
                   but: str | None = None,
                   but_shop: str | None = None) -> list:
    """Who is spoken for tonight by every job EXCEPT `but`. Routes and
    the salvage pickup reserve their driver; the raid reserves its
    team. Planning menus and the night's execution both consult this
    one derivation — never another ad-hoc reserved= list.

    `but_shop` narrows the route exemption to ONE address: replanning
    the route out of shop 1 frees that driver, and leaves the driver
    already committed to shop 2's route exactly where he was."""
    out: list = []
    for shop_key, plan in routes_planned(state, plans).items():
        if but == "route" and (but_shop is None or but_shop == shop_key):
            continue
        out.append(plan["driver"])
    for job in ("salvage", "raid"):
        plan = plans.get(job)
        if not plan or job == but:
            continue
        if job == "raid":
            out.extend(plan["team"])
        else:
            out.append(plan["driver"])
    return out


def planned_jobs_at(state: "State", plans: dict, shop_key: str,
                    but: str | None = None) -> list:
    """Tonight's planned wagon jobs leaving ONE address, in a stable
    order. This is the per-address replacement for `wagon_job` in
    every availability question: with a fleet, a pickup planned at
    the home shop reserves the home wagon and nothing else."""
    jobs = []
    if but != "route" and shop_key in routes_planned(state, plans):
        jobs.append("route")
    if but != "salvage" and plans.get("salvage") and (
            plan_origin(state, plans["salvage"]) == shop_key):
        jobs.append("salvage")
    return jobs


# The wagon vocabulary and both typed views live in `models` (P4b.1a
# review), beside `wagon_claim` and `WagonAvailability`: one home for
# what a wagon's availability IS, and the only arrangement in which
# `raids` and `war` can take the view intact without importing this
# module back.
WAGON_NOTES = models.WAGON_NOTES
plan_origin = models.plan_origin
plan_wagon = models.plan_wagon
PlannedWagon = models.PlannedWagon


def planned_wagon(state: "State", plans: dict, shop_key: str,
                  but: str | None = None) -> models.PlannedWagon:
    """WHICH wagons can be planned out of ONE address tonight.

    `WagonNight` answers the same question at execution, from the
    claims tonight actually made; this answers it from the PLANS,
    before any of them run. Both compose the same two authorities —
    the lifecycle (`models.wagon_claim`) and the night's own
    reservations — and both answer PER ADDRESS, so a route leaving
    the home shop can never ground a second shop's wagon.
    `WagonNight.claim_at` remains the execution revalidation; this
    exists so the player is refused at the menu rather than when the
    crew is already loading.

    Order matches `WagonNight.note_at` deliberately: a wagon a plan
    has already taken reports THAT job, and the lifecycle speaks only
    when nothing tonight has taken it — so a wagon is never described
    as sitting at the contractor's yard when the pickup has it."""
    kept = state.wagons_at(shop_key)
    claimable = models.claimable_wagons(state, shop_key)
    taken = planned_jobs_at(state, plans, shop_key, but=but)
    # Each planned job at this address spends one of its free wagons,
    # in the same key order `claim_at` would spend them.
    free = claimable[len(taken):]
    if free:
        return models.PlannedWagon(free)
    if taken:
        return models.PlannedWagon(blocked_by=taken[0],
                                   note=WAGON_NOTES[taken[0]])
    for w in kept:
        claim = models.wagon_claim(state, w.key)
        if not claim.available:
            return models.PlannedWagon(blocked_by="lifecycle",
                                       note=claim.note)
    return models.PlannedWagon(blocked_by="unhoused",
                               note="not kept at this address")


@dataclass
class WagonNight:
    """THE night's wagon assignments (design rev. 25 item 1, widened
    to a fleet in P4a.3): ONE stateful answer per wagon, updated by
    each consumer as it executes.

    A derived boolean cannot do this job. Any answer computed from
    the morning's plans and the service report is blind to what
    happens later the same night — the outgoing raid that hauls with
    a wagon, and the decoy that loads one against the first of two
    arriving rivals. Opened at SERVICE start (P4b.1a) and threaded
    through the night, this object is spent by each consumer AT
    DEPARTURE; every later consumer asks it rather than re-deriving
    an answer that has gone stale. The inference it replaced
    (`wagon_used`) existed only because the claim used to happen
    after the jobs had already run.

    Availability is answered PER ADDRESS, not globally: a second shop
    with its own wagon is not grounded because the home wagon left.
    """

    state: "State"
    claims: dict = field(default_factory=dict)   # wagon key -> consumer

    def free_at(self, shop_key: str) -> list:
        """Wagons still at an address, in stable key order.

        TWO authorities compose here and neither absorbs the other
        (P4b.1a): the LIFECYCLE says whether a wagon may be claimed at
        all — a construction site's wagon is still at the contractor's
        yard — and this ledger says whether tonight has already spent
        it. A wagon must pass both to be free, and it is asked of
        `models.wagon_claim` rather than re-derived here, so planning
        and execution can never reach different answers."""
        return [w for w in self.state.wagons_at(shop_key)
                if w.key not in self.claims
                and models.wagon_claim(self.state, w.key).available]

    def available_at(self, shop_key: str) -> bool:
        return bool(self.free_at(shop_key))

    def note_at(self, shop_key: str) -> str:
        """Why that address has nothing to load, empty while it has.
        With several wagons gone, the FIRST claim in key order is the
        reason given — one sentence, deterministic."""
        if self.available_at(shop_key):
            return ""
        for w in self.state.wagons_at(shop_key):
            if w.key in self.claims:
                return WAGON_NOTES[self.claims[w.key]]
        # Nothing tonight took it, so the reason is the lifecycle's to
        # give, in its own words — the refusal the player must be able
        # to read (§2.4.2: a silent absence would read as a bug).
        for w in self.state.wagons_at(shop_key):
            claim = models.wagon_claim(self.state, w.key)
            if not claim.available:
                return claim.note
        return "not kept at this address"

    def view_at(self, shop_key: str) -> models.WagonAvailability:
        """The immutable answer consumers read, for one address. One
        value, so availability and its reason cannot contradict."""
        return models.WagonAvailability(self.available_at(shop_key),
                                        self.note_at(shop_key))

    def claim_at(self, shop_key: str, by: str) -> str:
        """Take a wagon out from an address, exclusively; returns the
        wagon key. Fails CLOSED when that address has none left: it
        means a consumer asked `available_at` and acted on a stale
        answer, which is the bug class this authority exists to end."""
        if by not in WAGON_NOTES:
            raise ValueError(f"unknown wagon consumer {by!r}")
        free = self.free_at(shop_key)
        if not free:
            raise RuntimeError(
                f"no wagon left at that address — {by!r} cannot take "
                f"one; every wagon there is {self.note_at(shop_key)}")
        self.claims[free[0].key] = by
        return free[0].key

    def claim_plan(self, state: "State", plan: dict, by: str,
                   field: str = "origin_shop") -> models.ClaimResult:
        """THE execution authority for a planned wagon job: one
        atomic check-and-claim.

        It verifies that this authority belongs to the world being
        mutated, that the plan's origin and wagon are a coherent
        pair, and that the exact named wagon is free — and only then
        spends it. Centralised deliberately: night rejecting a
        foreign authority is too late, because routes and pickups
        depart during SERVICE, and a foreign authority with matching
        wagon keys would record the claim in ANOTHER world while this
        one lost its stock. Two separate checks in two callers is the
        arrangement that let that through."""
        if self.state is not state:
            raise ValueError(
                "this wagon-assignment authority belongs to a "
                "different state — a claim recorded there says "
                "nothing about the world being spent here")
        return self.claim_key(models.plan_wagon(state, plan, field), by)

    def claim_key(self, wagon_key: str, by: str) -> models.ClaimResult:
        """Take THE wagon a plan named, and say whether it was still
        there. This is the execution revalidation the contract asks
        for: a plan records an identity at morning, and the night
        spends THAT vehicle or none — never a different wagon that
        happens to sit at the same address.

        Returns a typed result rather than raising when the wagon is
        gone, because a job losing its wagon between planning and
        nightfall is ordinary play: a route that departed, a site that
        has not opened. The result carries WHY, because this method
        is what knows — a caller asking the address instead gets
        nothing when a different wagon is still parked there. Raises
        only on incoherence: an unknown wagon, or an unknown
        consumer."""
        if by not in WAGON_NOTES:
            raise ValueError(f"unknown wagon consumer {by!r}")
        self.state.wagon_by_key(wagon_key)      # KeyError on a ghost
        held = self.claims.get(wagon_key)
        if held is not None:
            return models.ClaimResult(False, wagon_key, held,
                                      WAGON_NOTES[held])
        lifecycle = models.wagon_claim(self.state, wagon_key)
        if not lifecycle.available:
            return models.ClaimResult(False, wagon_key, "lifecycle",
                                      lifecycle.note)
        self.claims[wagon_key] = by
        return models.ClaimResult(True, wagon_key)


# ══ MORNING ═══════════════════════════════════════════════════════

def morning(state: State, con: Console, streams: Streams) -> dict:
    """Read the news, set the day up. Returns plans for later phases."""
    # The address this surface is about, resolved ONCE at the
    # boundary and threaded through (design rev. 27 item 6):
    # Act I, the Straight Path and the Quiet Sale each concern
    # one established shop, and every helper below takes it as
    # a parameter rather than reaching for "the shop".
    shop_at = models.operating_shop(state)
    market.draw_events(state, streams.daily(state.day, "events"))
    market.roll_prices(state, streams.daily(state.day, "market"))
    shop.roll_demand(state, streams.daily(state.day, "demand"))

    con.header(f"DAY {state.day} of {data.DEBT_DUE_DAY} — MORNING")
    con.say(f"  Clean {money(state.clean)} | Dirty {money(state.dirty)} | "
            f"Debt {money(state.debt)} | Rep {shop_at.reputation:.0f} | "
            f"Case {state.case:.0f}/100")
    if state.debt > 0:
        days_left = data.DEBT_DUE_DAY - state.day
        line = f"  Carmine expects {money(state.debt)} within {days_left} day(s)."
        if state.debt < data.START_DEBT // 2:
            line += " …and he has opinions about what comes after."
        con.say(line)
        _act1_telegraphs(state, con)
    elif state.branch == "straight":
        straight.morning_lines(state, con)
    elif state.branch == "war":
        war.morning_lines(state, con)

    con.say(f"  Order book: ~{shop_at.demand_today} customers expected, "
            f"{shop_at.delivery_pool} delivery orders on the board.")
    for line in state.news:
        con.bullet(f"NEWS: {line}")
    for line in market.rumor_sheet(state, streams.daily(state.day, "rumors")):
        con.bullet(f"RUMOR: {line}")
    hired_before = len(state.hired())
    _staff_trouble(state, con, streams.staff)
    if state.branch == "quiet_sale" and len(state.hired()) < hired_before:
        # A walkout mid-diligence is an incident (§2.4.4).
        escrow.record_incident(state, con, streams,
                               "a staff walkout mid-diligence")

    # Carmine won't let his investment starve: he fronts stock — onto
    # the debt. His emergency credit exists only while the Act I debt
    # is genuinely alive (rev. 15 item 3): once an active branch is
    # chosen, the payoff ended his stake, and a starving pantry is the
    # branch's own problem. Flag-off Act I and stand-pat keep the old
    # behavior to the byte — the golden and stand-pat surfaces are
    # frozen, and stand-pat is the control (the carve-out is recorded
    # in rev. 15, not hidden here).
    active_branch = state.branch is not None and state.branch != "stand_pat"
    if shop_at.ingredients < 10 and state.clean < 200 \
            and not active_branch:
        shop.stock_pantry(state, shop_at, 40)
        state.debt += 40 * data.INGREDIENT_COST[shop_at.quality] + 100
        con.bullet("Carmine's nephew drops off flour, cheese and cans 'on account.' "
                   "The account, of course, is the debt.")

    plans: dict = {"routes": {}, "raid": None}
    if state.branch == "straight":
        # The supplier's van is gone (rev. 9 item 9); the back door gets
        # visitors of its own instead.
        offer = straight.temptation_offer(
            state, streams.daily(state.day, "straight"))
        if offer:
            straight.temptation_card(state, offer, con)
        _straight_morning_menu(state, con, streams, plans, offer)
        return plans

    supplier = _supplier_offer(state, streams.daily(state.day, "supplier"))
    if supplier:
        g = data.GOODS[supplier["good"]]
        con.bullet(f"SUPPLIER: {supplier['units']}x {g['label']} at "
                   f"{money(supplier['price'])}/unit, cash — he doesn't care whose.")

    if state.branch == "war":
        if war.insurance_due(state):
            war.insurance_card(state, con)
        _war_morning_menu(state, con, streams, plans, supplier)
        return plans

    while True:
        c = con.menu("Morning at the shop:", [
            "Market board (prices you actually know)",
            "Kitchen policy (quality / menu prices)",
            "Buy ingredients",
            "Buy from today's supplier" if supplier else "No supplier today",
            "Staff (hire, read in, raises)",
            "Improvements & warehouse",
            "Plan tonight's route",
            "Plan a night job (raid)",
            "Open for service →",
        ])
        if c == 0:
            _market_board(state, shop_at, con)
        elif c == 1:
            _kitchen_policy(state, shop_at, con, plans)
        elif c == 2:
            _buy_ingredients(state, shop_at, con)
        elif c == 3 and supplier:
            supplier = _buy_supplier(state, shop_at, supplier, con)
        elif c == 4:
            _staff_menu(state, con, streams.staff)
        elif c == 5:
            _improvements(state, shop_at, con)
        elif c == 6:
            # The lifecycle can refuse a route before it is planned;
            # with one address it never does, so this adds no
            # reachable branch to the Act I path (there is no salvage
            # here either, so "planned" cannot arise).
            wagon_now = planned_wagon(state, plans, shop_at.key,
                                      but="route")
            if not wagon_now.available:
                con.say(f"  No route leaves here tonight — "
                        f"{wagon_now.note}.")
                continue
            planned = routes.plan_route(
                state, con, streams.routes,
                reserved=night_reserved(state, plans, but="route",
                                        but_shop=shop_at.key),
                wagon=wagon_now)
            if planned is not None:
                plans["routes"][shop_at.key] = planned
            else:
                plans["routes"].pop(shop_at.key, None)
        elif c == 7:
            route = routes_planned(state, plans).get(shop_at.key)
            if route and route["ride_along"]:
                con.say("  You'll be in the wagon tonight — the crew goes "
                        "without you, and without your nerve.")
            plans["raid"] = raids.plan_raid(
                state, con, streams.raids,
                reserved=night_reserved(state, plans, but="raid"),
                wagon=planned_wagon(state, plans, shop_at.key))
        elif c == 8:
            break
    return plans


def _straight_morning_menu(state: State, con: Console, streams: Streams,
                           plans: dict, offer: dict | None) -> None:
    # The address this surface is about, resolved ONCE at the
    # boundary and threaded through (design rev. 27 item 6):
    # Act I, the Straight Path and the Quiet Sale each concern
    # one established shop, and every helper below takes it as
    # a parameter rather than reaching for "the shop".
    shop_at = models.operating_shop(state)
    """The branch's morning (rev. 9 item 9): the supplier slot belongs
    to the temptation offer, 'Plan tonight's route' is Disposal with
    the counted runs in its label, and the raid verb is gone."""
    fire_sale_done = False
    while True:
        bs = straight.live(state)
        options = [
            "Market board (prices you actually know)",
            "Kitchen policy (quality / menu prices)",
            "Buy ingredients",
            ("Answer the back door (new trade — not disposal)"
             if offer else "Nobody at the back door today"),
            "Staff (hire, read in, raises)",
            "Improvements & warehouse",
            f"Disposal (runs left: {bs.disposal_runs_left})",
            "The case file (counsel's docket)",
            "Open for service →",
        ]
        c = con.menu("Morning at the shop:", options)
        if c == 0:
            _market_board(state, shop_at, con)
        elif c == 1:
            _kitchen_policy(state, shop_at, con, plans)
        elif c == 2:
            _buy_ingredients(state, shop_at, con)
        elif c == 3 and offer:
            if straight.take_temptation(state, offer, con, streams):
                offer = None
        elif c == 4:
            _staff_menu(state, con, streams.staff)
        elif c == 5:
            _improvements(state, shop_at, con)
        elif c == 6:
            fire_sale_done = _disposal_menu(state, con, streams, plans,
                                            fire_sale_done, shop_at)
        elif c == 7:
            straight.show_case_file(state, con)
        elif c == 8:
            break


def _war_morning_menu(state: State, con: Console, streams: Streams,
                      plans: dict, supplier: dict | None) -> None:
    # The address this surface is about, resolved ONCE at the
    # boundary and threaded through (design rev. 27 item 6):
    # Act I, the Straight Path and the Quiet Sale each concern
    # one established shop, and every helper below takes it as
    # a parameter rather than reaching for "the shop".
    shop_at = models.operating_shop(state)
    """The war's morning: the full market morning plus the board, the
    salvage pickup, and the standing second-declaration offer
    (rev. 14 item 9 — never a missable one-morning prompt). Entries
    rebuild each pass because the war changes shape mid-morning;
    'Open for service' stays last, and nothing destructive ever is."""
    while True:
        entries: list = [
            ("Market board (prices you actually know)", "market"),
            ("Kitchen policy (quality / menu prices)", "kitchen"),
            ("Buy ingredients", "buy"),
            ("Buy from today's supplier" if supplier
             else "No supplier today", "supplier"),
            ("Staff (hire, read in, raises)", "staff"),
            ("Improvements & warehouse", "improve"),
            ("Plan tonight's route", "route"),
            ("Plan a night job (raid)", "raid"),
            ("The war board", "board"),
            ("The case file (counsel's docket)", "case"),
        ]
        next_front = _second_front(state)
        if next_front:
            entries.append(
                (f"Name the next war — "
                 f"{data.RIVALS[next_front]['label']} still stands",
                 "declare"))
        if plans.get("salvage"):
            # A plan is an intention (rev. 15 item 2): the pickup can
            # be recalled and the wagon freely replanned.
            entries.append(("Recall the wagon — cancel tonight's pickup",
                            "salvage_cancel"))
        elif war.salvage_ready(state) is not None:
            entries.append(("Send the wagon for the salvage", "salvage"))
        entries.append(("Open for service →", "open"))
        key = entries[con.menu("Morning at the shop:",
                               [label for label, _k in entries])][1]
        if key == "market":
            _market_board(state, shop_at, con)
        elif key == "kitchen":
            _kitchen_policy(state, shop_at, con, plans)
        elif key == "buy":
            _buy_ingredients(state, shop_at, con)
        elif key == "supplier" and supplier:
            supplier = _buy_supplier(state, shop_at, supplier, con)
        elif key == "staff":
            _staff_menu(state, con, streams.staff)
        elif key == "improve":
            _improvements(state, shop_at, con)
        elif key == "route":
            wagon_now = planned_wagon(state, plans, shop_at.key,
                                      but="route")
            if wagon_now.blocked_by == "planned":
                con.say("  The wagon is spoken for tonight — the pickup "
                        "has it. Recall it first if the route matters "
                        "more.")
                continue
            if not wagon_now.available:
                con.say(f"  No route leaves here tonight — "
                        f"{wagon_now.note}.")
                continue
            planned = routes.plan_route(
                state, con, streams.routes,
                reserved=night_reserved(state, plans, but="route",
                                        but_shop=shop_at.key),
                wagon=wagon_now)
            if planned is not None:
                plans["routes"][shop_at.key] = planned
            else:
                plans["routes"].pop(shop_at.key, None)
        elif key == "raid":
            route = routes_planned(state, plans).get(shop_at.key)
            if route and route["ride_along"]:
                con.say("  You'll be in the wagon tonight — the crew goes "
                        "without you, and without your nerve.")
            plans["raid"] = raids.plan_raid(
                state, con, streams.raids,
                reserved=night_reserved(state, plans, but="raid"),
                wagon=planned_wagon(state, plans, shop_at.key))
        elif key == "board":
            war.board(state, con)
        elif key == "case":
            evidence.show_case_file(state, con)
        elif key == "declare" and next_front:
            c = con.menu(
                f"Take the war to {data.RIVALS[next_front]['short']}? "
                f"Their relation locks at vendetta — no truce, ever.",
                ["Declare — the second front opens this morning",
                 "Not yet — one war at a time is expensive enough"])
            if c == 0:
                war.declare(state, next_front, con)
        elif key == "salvage":
            plans["salvage"] = war.plan_salvage(
                state, con,
                reserved=night_reserved(state, plans, but="salvage"),
                wagon=planned_wagon(state, plans, shop_at.key,
                                    but="salvage"),
                origin_shop=shop_at.key)
        elif key == "salvage_cancel":
            plans["salvage"] = None
            con.say("  The wagon stays home tonight. The stockroom "
                    "isn't going anywhere.")
        else:
            break


def _second_front(state: State) -> str | None:
    """The standing second-declaration offer: no live campaign, one
    rival still standing and undeclared-upon."""
    if models.live_campaign(state) is not None:
        return None
    for k, r in state.rivals.items():
        if r.alive and war.campaign_for(state, k) is None:
            return k
    return None


def _disposal_menu(state: State, con: Console, streams: Streams,
                   plans: dict, fire_sale_done: bool,
                   shop_at: Shop) -> bool:
    """Three ways out for the remaining stash (§2.4.1): Sal's truck at
    40%, a counted run at a haircut, or the oven. Back stays last; the
    destructive option is never last (rev. 7's lesson)."""
    bs = straight.live(state)
    c = con.menu("Disposal — what's left goes one of three ways:", [
        "Fire-sale to Sal's people — 40% of book, his truck, one "
        "meeting a day [a crime]",
        f"A disposal run — runs left: {bs.disposal_runs_left}, 60–75% "
        f"of board, full route rules and risks [a crime]",
        "Burn the shop stash — nothing back, no risk, no crime",
        "Back",
    ])
    if c == 0:
        if fire_sale_done:
            con.say("  Sal's man came once today already. One meeting a "
                    "day — his rule, and he keeps it.")
        else:
            fire_sale_done = straight.fire_sale(state, con, streams)
    elif c == 1:
        if bs.disposal_runs_left <= 0:
            con.say("  The three runs are spent. What's left goes to "
                    "Sal's people, or into the oven.")
        elif shop_at.key in routes_planned(state, plans):
            con.say("  Tonight's wagon is already spoken for.")
        else:
            disposal_wagon = planned_wagon(state, plans, shop_at.key,
                                           but="route")
            if not disposal_wagon.available:
                con.say(f"  No run leaves here tonight — "
                        f"{disposal_wagon.note}.")
                return fire_sale_done
            plan = routes.plan_route(state, con, streams.routes,
                                     wagon=disposal_wagon)
            if plan is not None:
                if any(plan["cargo"].values()):
                    plan["disposal"] = True
                    con.say("  A disposal run spends one of the three "
                            "when the wagon actually loads — and the "
                            "clean days start over when it rolls.")
                else:
                    con.say("  Pizzas only: an honest drive spends no "
                            "run and commits no crime.")
                plans["routes"][shop_at.key] = plan
    elif c == 2:
        straight.burn_stock(state, con)
    return fire_sale_done


def _act1_telegraphs(state: State, con: Console) -> None:
    """§2.1 pre-payoff telegraphs. Transcript only — no state change, no
    RNG draw — and the caller guarantees the debt is alive. Everything
    here is a world fact derivable from state, so nothing needs a stored
    once-only flag."""
    if state.day == 20:
        connected = any(e.trait == "connected" and e.available
                        for e in state.hired())
        src = "Lena, sorting receipts," if connected else "A regular at the counter"
        con.bullet(f"{src} says the man who was asking around about buying "
                   f"shops is losing interest. Whatever you're going to be, "
                   f"you're already becoming it.")
    elif state.day == 24:
        con.bullet("Word from Carmine himself: settle up by tomorrow night, "
                   "or the table will be empty. Past day 25, whatever you "
                   "are on day 30 is what you'll be.")
    crossed = _case_first_crossed_60_day(state)
    if crossed is not None and state.day == crossed + 1:
        con.bullet("The morning paper runs a column on 'irregularities' along "
                   "the harbor. Investors and buyers read the papers too — a "
                   "file this thick narrows what anyone will offer you across "
                   "a table.")


def _case_first_crossed_60_day(state: State) -> int | None:
    """Day the Case first reached 60, or None. Consumes the shared
    prefix iterator (rev. 9 item 15) — the same arithmetic as
    State.case, so 'crossed' here agrees bit-for-bit with the meter."""
    for record, running in case_prefix(state.evidence):
        if running >= 60.0:
            return record.day
    return None


def _market_board(state: State, shop_at: Shop, con: Console) -> None:
    con.say("")
    # Inventory reads units × bulk each = bulk used, everywhere a
    # stash is shown (rev. 17 item 1).
    for line in routes.inventory_lines("The back room", shop_at.stash,
                                       shop_at.stash_cap):
        con.say(f"  {line}")
    if state.warehouse is not None:
        for line in routes.inventory_lines("The warehouse", state.warehouse,
                                           data.WAREHOUSE_CAP):
            con.say(f"  {line}")
    for dk, dspec in data.DISTRICTS.items():
        d = state.districts[dk]
        con.say(f"  {dspec['label']} — heat {d.heat:.0f}  ({dspec['flavor']})")
        # The board explains the territory (rev. 15 item 5): capture
        # demand and heat capacity come from the same route-market
        # view the routes run on. Flag-off these lines never print.
        rm = market.route_market(state, dk)
        if rm.captured:
            con.say("      your turf now — the coded customers call "
                    "your board (covert demand up)")
        if rm.heat.band != "cool":
            con.say(f"      {rm.heat.band.upper()} — {rm.heat.note}")
        if d.known_price_age == 0:
            for g, p in state.prices[dk].items():
                con.say(f"      {data.GOODS[g]['label']:<24} {money(p)}/unit")
        elif d.known_price_age > 30:
            con.say("      prices unknown — nobody's run that way in a long while")
        else:
            con.say(f"      prices {d.known_price_age} day(s) stale — "
                    f"run a route to get fresh numbers")


def _kitchen_policy(state: State, shop_at: Shop, con: Console,
                    plans: dict | None = None) -> None:
    con.say(f"  Pantry holds {shop_at.ingredients} orders of "
            f"{shop_at.pantry_quality} stock — the kitchen cooks what "
            f"it has, whatever the menu says.")
    q = con.menu(f"Ingredient quality (now: {shop_at.quality}):",
                 [f"{lv} (cost {money(data.INGREDIENT_COST[lv])}/order)"
                  for lv in QUALITY_LEVELS])
    shop_at.quality = QUALITY_LEVELS[q]
    p = con.menu(f"Menu pricing (now: {shop_at.price}):",
                 [f"{lv} (ticket {money(data.TICKET_PRICE[lv])})"
                  for lv in QUALITY_LEVELS])
    shop_at.price = QUALITY_LEVELS[p]
    if shop_at.price == "gourmet" and shop_at.quality == "cheap":
        con.say("  Charging gourmet prices for cheap pies. Bold. Reviews incoming.")
    # New prices, new crowd — the order book re-forms around the menu.
    shop.recompute_demand(state, shop_at)
    con.say(f"  Order book now: ~{shop_at.demand_today} customers, "
            f"{shop_at.delivery_pool} delivery orders.")
    route = routes_planned(state, plans or {}).get(shop_at.key)
    if route and route["legit"] > shop_at.delivery_pool:
        con.say("  Tonight's route was planned against the old order book — "
                "the kitchen will fill what it can.")


def _buy_ingredients(state: State, shop_at: Shop, con: Console) -> None:
    cost = data.INGREDIENT_COST[shop_at.quality]
    most = state.clean // cost if cost else 0
    restock = max(0, min(most, 80 - shop_at.ingredients))
    n = con.ask_int(f"Buy how many orders of stock? ({money(cost)} each, clean cash, "
                    f"have {shop_at.ingredients} {shop_at.pantry_quality})",
                    0, min(most, 200), restock)
    state.clean -= n * cost
    before_q = shop_at.pantry_quality if shop_at.ingredients else None
    shop.stock_pantry(state, shop_at, n)
    if before_q and shop_at.pantry_quality != before_q:
        con.say(f"  The new {shop_at.quality} stock mixes into the walk-in — "
                f"the pantry now cooks as {shop_at.pantry_quality}.")


def _supplier_offer(state: State, rng: random.Random) -> dict | None:
    if rng.random() < 0.15:
        return None
    g = rng.choice(list(data.GOODS))
    home_price = state.prices[data.HOME_DISTRICT][g]
    return {
        "good": g,
        "units": rng.randint(6, 24),
        "price": max(5, int(home_price * rng.uniform(0.40, 0.68))),
    }


def _buy_supplier(state: State, shop_at: Shop, offer: dict,
                  con: Console) -> dict | None:
    # The storage authority prices the bound (rev. 18 item 2).
    fit = models.units_that_fit(state, shop_at.key, offer["good"])
    afford = (state.dirty + state.clean) // offer["price"]
    top = min(offer["units"], fit, afford)
    if top <= 0:
        con.say("  No cash or no stash space. The van drives off.")
        return offer
    n = con.ask_int(f"Buy how many units at {money(offer['price'])}?", 0, top, top)
    if n:
        cost = n * offer["price"]
        from_dirty = min(state.dirty, cost)   # dirty cash first — it's harder to spend
        state.dirty -= from_dirty
        state.clean -= cost - from_dirty
        shop_at.stash[offer["good"]] = shop_at.stash.get(offer["good"], 0) + n
        offer["units"] -= n
        con.say(f"  Boxes come in through the alley door. The back room: "
                f"{models.space_used(shop_at.stash)}/"
                f"{models.space_cap(state, shop_at.key)} space used.")
    return offer if offer["units"] > 0 else None


def _staff_trouble(state: State, con: Console, rng: random.Random) -> None:
    for e in state.hired():
        if e.injured_days:
            e.injured_days -= 1
            if e.injured_days == 0:
                con.bullet(f"{e.name} is back on their feet.")
        if e.morale > 3:
            e.resignation_pending = False
        elif e.resignation_pending:
            e.hired = False
            e.resignation_pending = False
            con.bullet(f"{e.name} hangs up the apron mid-morning. 'I told you.' "
                       f"They're gone.")
            if e.aware:
                state.add_case(6, f"{e.name} walked out knowing everything",
                               kind="witness", source=e.key)
            continue
        else:
            e.resignation_pending = True
            con.bullet(f"{e.name} corners you by the walk-in: pay, respect, "
                       f"or they walk tomorrow. (Morale {e.morale} — a raise "
                       f"would fix this.)")
        if e.morale <= 2 and rng.random() < 0.4:
            if e.trait == "greedy" and state.dirty > 0:
                skim = min(state.dirty, rng.randrange(100, 400, 50))
                state.dirty -= skim
                con.bullet(f"The till is light. {e.name} won't meet your eyes. "
                           f"(-{money(skim)} dirty)")
            elif e.aware and rng.random() < 0.3:
                state.add_case(10, f"{e.name} had a long talk with a detective",
                               kind="witness", source=e.key)
                con.bullet(f"{e.name} was seen outside the precinct. Probably nothing.")
                e.morale = 4



def _staff_menu(state: State, con: Console, rng: random.Random) -> None:
    while True:
        con.say("")
        con.say("  Payroll:")
        for e in state.hired():
            con.say(f"    {e.name:<28} {e.tag():<24} "
                    f"F{e.food} D{e.driving} N{e.nerve} L{e.loyalty} "
                    f"morale {e.morale}  {money(e.wage)}/day  [{e.trait}]")
        c = con.menu("Staff:", ["Hire", "Read someone in", "Give a raise (+morale/loyalty)",
                                "Let someone go", "Back"])
        if c == 0:
            pool = [e for e in state.employees if not e.hired and not e.arrested]
            if models.remediation_unlocked(state):
                # Rev. 11: settled-out names never come back — the
                # settlement was severance, not a sabbatical, and a
                # rehire would reopen the witness problem the goal
                # term already counted closed. Capability-gated
                # (rev. 14 item 8): the war settles too.
                from .models import witness_status
                pool = [e for e in pool
                        if not (e.aware and witness_status(state, e.key)
                                == "settled")]
            if not pool:
                con.say("  Nobody worth hiring is looking.")
                continue
            names = [f"{e.name} ({e.role}, {money(e.wage)}/day, {e.trait}) — {e.bio}"
                     for e in pool] + ["Back"]
            p = con.menu("Applicants:", names)
            if p < len(pool):
                pool[p].hired = True
                con.say(f"  {pool[p].name} starts today.")
        elif c == 1:
            naive = [e for e in state.hired() if not e.aware and e.available]
            if not naive:
                con.say("  Everyone left either knows or can't be told.")
                continue
            names = [f"{e.name} (loyalty {e.loyalty}, {e.trait})" for e in naive] + ["Back"]
            p = con.menu("Read in whom? (They become crew — and a witness.)", names)
            if p < len(naive):
                e = naive[p]
                if e.trait == "principled" and e.loyalty < 9:
                    e.morale -= 2
                    con.say(f"  {e.name} stops you mid-sentence: 'Don't finish that.' "
                            f"They stay — for now — but something changed.")
                else:
                    e.aware = True
                    e.wage += 30
                    con.say(f"  {e.name} listens, nods once. In. (+{money(30)}/day)")
        elif c == 2:
            crew = state.hired()
            if not crew:
                continue
            names = [e.name for e in crew] + ["Back"]
            p = con.menu(f"Raise for whom? (+{money(20)}/day, clean)", names)
            if p < len(crew):
                e = crew[p]
                e.wage += 20
                e.morale = min(10, e.morale + 2)
                e.loyalty = min(10, e.loyalty + 1)
                if e.resignation_pending:
                    # The confrontation was answered, and they know it.
                    e.resignation_pending = False
                    e.morale = max(e.morale, 5)
                    con.say(f"  {e.name} reads the new number twice, nods, "
                            f"and ties the apron back on.")
                else:
                    con.say(f"  {e.name} stands a little straighter.")
        elif c == 3:
            crew = state.hired()
            # §2.1 same-night telegraph: firing someone who knows books a
            # 6-point witness record, which can only close a chair from
            # within 6 of a gate — warn pre-action exactly then. A line
            # before the existing menu; the prompt itself is golden.
            if state.payoff_in_reach() and any(e.aware for e in crew) \
                    and any(state.case < g <= state.case + 6.0
                            for g in (60.0, 70.0, 85.0)):
                con.say("  With the debt this close to settled: someone "
                        "walking out with what they know goes straight into "
                        "the file tomorrow's table reads.")
            names = [e.name for e in crew] + ["Back"]
            p = con.menu("Let go whom?", names)
            if p < len(crew):
                e = crew[p]
                e.hired = False
                if e.aware:
                    state.add_case(6, f"{e.name} was fired knowing everything",
                                   kind="witness", source=e.key)
                    con.say(f"  {e.name} leaves quietly. Too quietly. They know things.")
                else:
                    con.say(f"  {e.name} is gone.")
        else:
            return


def _improvements(state: State, shop_at: Shop, con: Console) -> None:
    while True:
        owned = shop_at.upgrades
        # Branch verbs first (rev. 9 items 8 and 10): counsel and
        # advertising live here on the Straight Path. Flag-off and
        # stand-pat menus are untouched — extras is empty there.
        extras = []
        if state.branch == "straight":
            extras = [("counsel", straight.counsel_label(state)),
                      ("advertise", straight.ad_label(state))]
        elif models.remediation_unlocked(state):
            # The war retains the same counsel (rev. 14 item 8);
            # advertising stays the Straight Path's own verb.
            extras = [("counsel", evidence.counsel_label(state))]
        keys = [k for k in data.UPGRADES if k not in owned]
        opts = [label for _key, label in extras]
        opts += [f"{data.UPGRADES[k]['label']} — {money(data.UPGRADES[k]['cost'])} clean. "
                 f"{data.UPGRADES[k]['desc']}" for k in keys]
        if state.warehouse is None:
            opts.append(f"Rent the harbor warehouse — {money(data.WAREHOUSE_RENT)}/day dirty. "
                        f"Bulk space, off-site stash, one more address to defend.")
        opts.append("Back")
        c = con.menu(f"Improvements (clean {money(state.clean)}):", opts)
        if c < len(extras):
            if extras[c][0] == "counsel":
                evidence.toggle_counsel(state, con)
            else:
                straight.advertise(state, con)
            continue
        c -= len(extras)
        if c < len(keys):
            k = keys[c]
            cost = data.UPGRADES[k]["cost"]
            if state.clean < cost:
                con.say("  Not with today's clean cash.")
            else:
                state.clean -= cost
                owned.add(k)
                con.say(f"  {data.UPGRADES[k]['label']}: done by closing time.")
                shop.recompute_demand(state, shop_at)
        elif state.warehouse is None and c == len(keys):
            state.warehouse = {}
            con.say("  Keys to a rusted rolling door. Nobody asks what's in the crates.")
        else:
            return


# ══ SERVICE ═══════════════════════════════════════════════════════

def service(state: State, plans: dict, con: Console, streams: Streams) -> dict:
    # The address this surface is about, resolved ONCE at the
    # boundary and threaded through (design rev. 27 item 6):
    # Act I, the Straight Path and the Quiet Sale each concern
    # one established shop, and every helper below takes it as
    # a parameter rather than reaching for "the shop".
    shop_at = models.operating_shop(state)
    con.header(f"DAY {state.day} — SERVICE")
    # THE night's wagon assignments, opened HERE rather than at
    # nightfall: routes and pickups depart during service, so an
    # authority created afterwards could only ever be told what had
    # already happened. It is claimed at departure and threaded
    # forward — `night` consumes this instance, never a fresh one.
    wagons = WagonNight(state)
    report_wagons = wagons
    # The WHOLE schedule is validated before the first crate moves.
    for shop_key, planned in route_schedule(state, plans):
        if not _commit_route(state, planned, con, wagons):
            plans["routes"].pop(shop_key, None)
    plan = routes_planned(state, plans).get(shop_at.key)
    # The cover pizzas were cooked and deducted at the address the
    # plan NAMED; the shift below is this surface's address. They are
    # the same shop while one exists, and `operating_shop` refuses the
    # moment they could differ — the shift going per-address is P4b's
    # work, not something to half-build here.
    route_legit = plan["legit"] if plan else 0
    report = shop.simulate_shift(state, shop_at, route_legit,
                                 streams.daily(state.day, "critic"))
    lost = f" ({report['lost']} turned away)" if report["lost"] else ""
    con.say(f"  Orders {report['orders']}/{report['demand']} demanded{lost}"
            f" | clean revenue {money(report['revenue'])}")
    if report["critic_line"]:
        con.bullet(report["critic_line"])
    if shop_at.ingredients < 10:
        con.bullet(f"Pantry low: {shop_at.ingredients} orders of stock left.")

    for planned in routes_planned(state, plans).values():
        r = routes.resolve_route(state, planned, con, streams.routes)
        for line in r["lines"]:
            con.bullet(line)
        if r["cash"]:
            con.say(f"  Route take: {money(r['cash'])} dirty, {r['sold']} units moved.")
    if plans.get("salvage") and not state.game_over:
        # The capture pickup rolls with the wagon at service — the
        # reserved war stream's one draw per pickup (rev. 14 item 6),
        # revalidated against the same assignment view that planned it.
        # The typed execution result rides the service report so the
        # night reads what happened, not the intention (rev. 17
        # item 6).
        report["salvage"] = war.run_salvage(
            state, plans["salvage"], con, streams.war,
            reserved=night_reserved(state, plans, but="salvage"),
            wagons=wagons)
    if state.branch == "quiet_sale":
        # The buyer's man walks the shop every diligence afternoon.
        escrow.walkthrough(state, con, streams)
    report["wagons"] = report_wagons
    return report


def _commit_route(state: State, plan: dict, con: Console,
                  wagons: "WagonNight") -> bool:
    """Morning plans are intentions; resources commit when service starts.
    Cancelled or replaced plans never touch inventory. Returns False (and
    commits nothing) if the plan can no longer run at all.

    The stash and pantry spent here belong to the address the plan
    NAMED, resolved from the plan itself and never from whichever
    address the surface happens to be about (rev. 22 item 1). A plan
    that names no origin, or names one that does not exist, is a bug
    and refuses BEFORE any inventory moves (rev. 27 item 7) — the
    alternative is a wagon loading out of a shop nobody owns."""
    # THE canonical contract, FIRST — before the address lookup, the
    # wagon claim, or one crate of inventory. `routes_planned` is the
    # only door OUT of storage, but it was not the only door INTO
    # execution: a plan handed straight to this function was taken on
    # trust, and a malformed one claimed a wagon and spent stock
    # before anything noticed.
    routes.validate_route_plan(state, plan)
    origin = state.shop_by_key(models.plan_origin(state, plan))
    driver = plan["driver"]
    if not driver.available:
        con.bullet(f"Tonight's route is scrubbed — {driver.name} isn't "
                   f"around to drive it.")
        return False
    pol = models.district_heat_policy(state, plan["district"])
    if not pol.plannable:
        # Service-time revalidation of the RED-heat refusal (rev. 14
        # item 5): the district may have caught fire since the plan
        # was made. Nothing has committed yet, so nothing is lost.
        con.bullet(f"Tonight's route is scrubbed — "
                   f"{data.DISTRICTS[plan['district']]['label']} is "
                   f"{pol.note}.")
        return False
    # Rev. 18 item 1: the PLANNED manifest is validated BEFORE any
    # state mutation — an illegal plan is refused with the stash and
    # pantry untouched, never discovered mid-deduction.
    planned = routes.RouteManifest.of_plan(plan)
    # The live, availability-revalidated COMMITTED manifest is built
    # first; only then does its inventory transaction apply, atomically.
    committed = routes.RouteManifest()
    for g, want in planned.cargo.items():
        have = origin.stash.get(g, 0)
        take = min(want, have)
        if take < want:
            con.bullet(f"Only {take}x {data.GOODS[g]['label']} left to load — "
                       f"the stash moved since this morning.")
        if take:
            committed.cargo[g] = take
    # Cover pizzas are real orders AND real oven time.
    committed.legit = min(planned.legit, origin.delivery_pool,
                          origin.kitchen_cap, origin.ingredients)
    if committed.legit < planned.legit:
        con.bullet(f"The kitchen fills {committed.legit} of "
                   f"{planned.legit} planned delivery orders — orders, "
                   f"ovens and pantry set the limit.")
    committed.validate()
    # THE DEPARTURE. Everything above validates; nothing above
    # mutates. The wagon is claimed HERE, from the shared
    # assignment authority, before one unit of stock moves — so a
    # wagon that left on another job scrubs this one with the stash
    # and pantry untouched, and never substitutes a different
    # vehicle that happens to sit at the same address.
    # Origin/wagon pairing, world identity and the claim, together
    # and atomically (P4b.1a): nothing above has mutated anything.
    spent = wagons.claim_plan(state, plan, "route")
    if not spent.claimed:
        con.bullet(f"Tonight's route is scrubbed. {spent.sentence}.")
        return False
    for g, take in committed.cargo.items():
        origin.stash[g] = origin.stash.get(g, 0) - take
    origin.ingredients -= committed.legit
    if isinstance(plan, routes.RoutePlan):
        plan.manifest = committed
    else:                       # legacy dict plans (tests only)
        plan["cargo"].clear()
        plan["cargo"].update(committed.cargo)
        plan["legit"] = committed.legit
    # A disposal run spends one of the three at the moment the wagon
    # actually loads product — a plan that scrubbed, or loaded nothing,
    # costs nothing (rev. 9 item 5: the crime is the run that rolls).
    if plan.get("disposal") and any(plan["cargo"].values()):
        bs = straight.live(state)
        bs.disposal_runs_left -= 1
        straight.crime_committed(state)
        con.say(f"  The wagon loads for a disposal run — "
                f"{bs.disposal_runs_left} left after tonight, and the "
                f"clean days start over.")
    return True


# ══ NIGHT ═════════════════════════════════════════════════════════

def night(state: State, plans: dict, service_report: dict, con: Console,
          streams: Streams, config: GameConfig | None = None) -> None:
    # The address this surface is about, resolved ONCE at the
    # boundary and threaded through (design rev. 27 item 6):
    # Act I, the Straight Path and the Quiet Sale each concern
    # one established shop, and every helper below takes it as
    # a parameter rather than reaching for "the shop".
    shop_at = models.operating_shop(state)
    con.header(f"DAY {state.day} — AFTER CLOSE")
    # The night's wagon, opened from what the service phase actually
    # did (a departed route or pickup holds it; a pickup scrubbed
    # before departure never took it out) and spent by each later
    # consumer in turn — design rev. 25 item 1.
    # THE assignment authority the service phase opened and spent
    # (P4b.1a): routes and pickups claimed their wagons when they
    # actually departed, so the night inherits the truth rather than
    # reconstructing it from intentions and a report.
    wagon = service_report.get("wagons")
    if not isinstance(wagon, WagonNight):
        raise ValueError(
            f"night was given no wagon-assignment authority — service "
            f"opens it and every departure spends it; got "
            f"{type(wagon).__name__}")
    if wagon.state is not state:
        raise ValueError(
            "the wagon-assignment authority belongs to a different "
            "state — claims made against another world say nothing "
            "about this one")

    # Today's wear is booked at close, BEFORE tonight's raids and rival
    # moves create new effects — a coupon blitz or smashed oven tonight
    # keeps its full stated duration of service days.
    # Every address heals and every coupon blitz expires on its own
    # clock — the counters belong to the shop that carries them.
    for a_shop in state.shops:
        if a_shop.damage_days:
            a_shop.damage_days -= 1
        if a_shop.coupon_days:
            a_shop.coupon_days -= 1

    raid_plan = plans.get("raid")
    if raid_plan and not state.rivals[raid_plan["rival"]].alive:
        # Rev. 14 item 9: the service route may have broken the target
        # after the job was planned — corners can finish a war before
        # the crowbars leave the shop.
        con.say(f"  The night job is scrubbed — "
                f"{data.RIVALS[raid_plan['rival']]['short']}'s "
                f"organization broke before the crew left the kitchen.")
        state.raid_log.append(models.RaidAttemptRecord(
            day=state.day, rival=raid_plan["rival"], outcome="scrubbed",
            crew=len(raid_plan["team"]), damage_h=0))
        raid_plan = None
    if raid_plan:
        # The day happened between planning and doing: anyone arrested,
        # injured or gone since morning is off the job — and anyone
        # the assignment view says another job owns tonight (rev. 15
        # item 2: execution revalidates the same view planning used).
        taken = night_reserved(state, plans, but="raid")
        team = [e for e in raid_plan["team"]
                if e.available and e not in taken]
        if not team:
            con.say("  The night job is scrubbed — the crew you picked this "
                    "morning didn't make it to nightfall intact.")
            state.raid_log.append(models.RaidAttemptRecord(
                day=state.day, rival=raid_plan["rival"],
                outcome="scrubbed", crew=len(raid_plan["team"]),
                damage_h=0))
        else:
            if len(team) < len(raid_plan["team"]):
                con.say("  The crew is short tonight; the job goes ahead anyway.")
            raid_plan["team"] = team
            # Execution truth for the wagon (rev. 17 item 6): the raid
            # asks what actually happened tonight — a committed route
            # or a pickup that DEPARTED holds the wagon; a pickup
            # scrubbed before departure never took it out.
            # §2.1 rev. 4: the day's takings can put payoff in reach
            # after the job was planned — recheck once, before it runs.
            if not raid_plan.get("table_warned") and state.payoff_in_reach():
                con.say("  With the debt this close to settled, remember: "
                        "whatever tonight leaves behind goes into the file "
                        "tomorrow's table reads.")
            # Departure spends the wagon, and only a stock theft
            # loads it (design rev. 26): ledger and sabotage jobs go
            # on foot. The outcome is irrelevant — a repelled theft
            # still drove away with it.
            #
            # Claimed BEFORE the job runs, by the KEY the plan named:
            # departure is what consumes the wagon, not the outcome,
            # and a wagon that left on the route since morning simply
            # is not there — which is what the claim reports.
            # An explicit None is the crew walking (rev. 26): ledger
            # and sabotage jobs never load. A named wagon goes through
            # the SAME assignment authority, paired against the
            # address the haul comes back to — `exactly_one_shop`
            # hides that pairing today and two addresses expose it.
            if raid_plan.get("wagon_key") is None:
                raid_plan["wagon_free"] = False
            else:
                raid_plan["wagon_free"] = wagon.claim_plan(
                    state, raid_plan, "raid",
                    field="return_shop").claimed
            raids.run_raid(state, raid_plan, con, streams.raids)

    for key, rival in state.rivals.items():
        if rival.alive and rival.raid_warning == 1:
            # Both rivals can arrive on one night, and the first
            # decoy takes the wagon with it — the second gets the
            # truth, not the morning's answer (design rev. 25).
            # The decoy loads a wagon kept at the address they are
            # hitting — the home wagon cannot cover a shop across town.
            hit = rival.warning.shop_key
            result = raids.incoming_raid(state, key, con, streams.raids,
                                         wagon=wagon.view_at(hit))
            if result.wagon_taken:
                wagon.claim_at(hit, "decoy")
            # Escrow's truth table is the merged one: any raid that
            # arrives — fought off or not — is an incident.
            if result.outcome != "averted" and state.branch == "quiet_sale" \
                    and not state.game_over:
                escrow.record_incident(state, con, streams,
                                       "a rival raid landing mid-diligence")
            if state.branch == "war" and result.landed \
                    and result.damage_before > 0 and not state.game_over:
                # Burned Out (§2.5 precedence 2, rev. 14 item 6): a
                # raid LANDING on a shop already damaged BEFORE impact
                # destroys it. The arrest latch, checked at accrual
                # inside the raid itself, has already had its chance —
                # precedence 1 wins a shared night.
                # Like the arrest latch, the terminal is set where it
                # happens and the night runs itself out — the run loop
                # reads it after close.
                state.game_over = "burned_out"
                con.say("")
                con.say("  The fire crews give up on the kitchen by "
                        "three. The war came home, and the shop that "
                        "was the point of everything is gone.")

    payroll_short = _payroll_and_rent(state, con)

    # The ceiling covers every honest dollar of the day — and it's a
    # nightly total, not a per-transaction allowance.
    ceiling = shop.total_believable_ceiling(state)
    laundered_tonight = 0
    while True:
        con.say("")
        con.say(f"  Clean {money(state.clean)} | Dirty {money(state.dirty)} | "
                f"Debt {money(state.debt)}")
        remaining = max(0, ceiling - laundered_tonight)
        if state.branch == "quiet_sale":
            con.say("  The register is being read line by line this week — "
                    "nothing washes until the papers are signed or torn.")
        else:
            con.say(f"  Books can absorb about {money(remaining)} more tonight "
                    f"without raising eyebrows.")
        # Branch-aware (rev. 7): during escrow the register is being
        # read, so the menu offers disposal instead of advertising a
        # laundering allowance it would refuse after selection. On the
        # Straight Path (rev. 9) the debt is history — Carmine's line
        # leaves the menu and the settlement verb takes a seat.
        first_action = ("Burn dirty cash (the buyer's ledger test is coming)"
                        if state.branch == "quiet_sale"
                        else "Launder dirty cash through the register")
        entries = [(first_action, "cash")]
        if state.branch == "straight":
            entries += [
                ("Move stash / cash (shop ↔ warehouse)", "storage"),
                ("Talk to a rival", "rival"),
                ("Settle with a witness (clean cash buys quiet)", "settle"),
                ("Lock up →", "lockup"),
            ]
        else:
            entries += [
                ("Pay Carmine (he prefers unmarked bills)", "debt"),
                ("Move stash / cash (shop ↔ warehouse)", "storage"),
                ("Talk to a rival", "rival"),
            ]
            if models.remediation_unlocked(state):
                # The war settles witnesses through the same verb
                # (rev. 14 item 8) — crew versus Case, priced nightly.
                entries += [("Settle with a witness (clean cash buys "
                             "quiet)", "settle")]
            entries += [("Lock up →", "lockup")]
        key = entries[con.menu("Settle accounts:",
                               [label for label, _k in entries])][1]
        if key == "cash":
            if state.branch == "quiet_sale":
                escrow.burn_cash_action(state, con)
            else:
                laundered_tonight += _launder(state, remaining, con)
        elif key == "debt":
            _pay_debt(state, con)
        elif key == "storage":
            _storage(state, shop_at, con, streams)
        elif key == "rival":
            rivals.negotiate(state, con, streams.rivals)
        elif key == "settle":
            evidence.settle_menu(state, con)
        else:
            break

    # §2.1 rev. 4: chair eligibility freezes at lock-up on payoff night —
    # after every discretionary account action, before the world's dice.
    # The flag gates ENTRY only (rev. 5): capture happens while it's on;
    # a snapshot already in a save stays authoritative regardless.
    if config is not None and config.fork_enabled \
            and state.debt_paid_day == state.day \
            and state.sitdown_snapshot is None and state.branch is None \
            and not state.game_over:
        state.sitdown_snapshot = SitdownSnapshot(
            payoff_day=state.day,
            case_at_lockup=state.case,
            evidence_count_at_lockup=len(state.evidence))

    # The branch's own night work: counsel, the campaign, dormancy, the
    # insolvency counter (rev. 9) — after the discretionary actions,
    # before the world's dice.
    if state.branch == "straight" and not state.game_over:
        straight.night_tick(state, con, payroll_short)
    elif state.branch == "war" and not state.game_over:
        war.night_obligation(state, con, payroll_short)
        war.night_insolvency(state, con, payroll_short)
    elif state.branch == "quiet_sale" and not state.game_over:
        escrow.night_insolvency(state, con, payroll_short)

    rivals.rival_phase(state, con, streams.rivals)
    _law_phase(state, con, streams.daily(state.day, "law"))

    if state.branch == "straight":
        straight.exit_readout(state, con)

    # The city cools a little overnight — a hot district, slower (the
    # heat-policy authority; flag-off the decay IS the old flat 5).
    for dk, d in state.districts.items():
        d.heat = max(0.0, d.heat
                     - models.district_heat_policy(state, dk).decay)
    state.day += 1


def _payroll_and_rent(state: State, con: Console) -> bool:
    """Returns whether payroll came up short — the Straight Path's
    clean-insolvency counter reads it (rev. 9 item 11)."""
    wages = sum(e.wage for e in state.hired() if not e.arrested)
    # Rent is charged per open address (design rev. 22 item 7): two
    # addresses, two rents, one canonical constant — never respelled.
    costs = wages + data.RENT_PER_DAY * len(state.shops)
    if state.warehouse is not None:
        if state.dirty >= data.WAREHOUSE_RENT:
            state.dirty -= data.WAREHOUSE_RENT
        else:
            costs += data.WAREHOUSE_RENT
    if state.clean >= costs:
        state.clean -= costs
        con.say(f"  Wages and rent paid: {money(costs)} clean.")
        return False
    short = costs - state.clean
    state.clean = 0
    con.say(f"  You come up {money(short)} short on payroll. People notice.")
    for e in state.hired():
        e.morale -= 2
    return True


def _launder(state: State, remaining: int, con: Console) -> int:
    """Wash dirty cash against tonight's REMAINING allowance. Returns the
    amount washed so the night loop can shrink the allowance — chunking
    the wash into small calls buys nothing."""
    if state.branch == "quiet_sale":
        # §2.4.4: the one week the two ledgers cannot touch.
        con.say("  Not this week. The books are being read line by line — "
                "the register stays boring until closing.")
        return 0
    if state.dirty <= 0:
        con.say("  No dirty cash on hand.")
        return 0
    # §2.3 dual use: while counsel is retained the believable ceiling
    # is enforced — the "wash more anyway" branch is simply not offered
    # (counsel's office sees the tapes). Capability-gated (rev. 14
    # item 8); the flag-off prompt and bounds are untouched.
    counsel = models.remediation_unlocked(state) \
        and state.branch_state is not None \
        and state.branch_state.counsel_retained
    top = min(state.dirty, remaining) if counsel else state.dirty
    if counsel and top <= 0:
        con.say("  Counsel's rule holds: nothing washes past tonight's "
                "ceiling, and the ceiling is spent.")
        return 0
    # §2.1 same-night telegraph: near payoff, an over-ceiling wash that
    # could slam a Case gate is warned about BEFORE the act — a printed
    # line only; the prompt below is part of the golden decision trace
    # and must not change.
    if state.payoff_in_reach() and state.dirty > remaining:
        could = state.case + min(20.0, (state.dirty - remaining) / 400)
        if any(state.case < gate <= could for gate in (60.0, 70.0, 85.0)):
            con.say("  With the debt this close to settled, mind what the "
                    "register claims tonight: whoever sits across a table "
                    "from you tomorrow reads the same spreadsheet the law "
                    "does.")
    amt = con.ask_int(f"Run how much through the books? (dirty {money(state.dirty)})",
                      0, top, min(state.dirty, remaining))
    if amt <= 0:
        return 0
    state.dirty -= amt
    state.clean += amt
    state.total_laundered += amt
    if amt > remaining:
        over = amt - remaining
        evidence = min(20.0, over / 400)
        state.add_case(evidence, f"the register claimed {money(amt)} beyond "
                                 f"any plausible night's sales", kind="paper")
        con.say(f"  {money(amt)} washed. {money(over)} of it is hard to explain. "
                f"Somewhere, a spreadsheet notices.")
        if state.branch == "straight":
            # Washing past the ceiling is a crime on the branch's clock
            # (§2.4.1) — the clean days start over.
            straight.crime_committed(state)
            con.say("  And it was a crime, tonight of all nights: the "
                    "clean days start over.")
    else:
        state.add_case(0.5, "", kind="paper")
        con.say(f"  {money(amt)} washed clean. The books look plausible.")
    observant = [e for e in state.hired() if e.trait == "observant" and not e.aware]
    if observant and amt > remaining:
        e = observant[0]
        e.morale -= 1
        con.say(f"  {e.name} rechecks the till twice and says nothing.")
    return amt


def _pay_debt(state: State, con: Console) -> None:
    if state.debt <= 0:
        con.say("  Paid in full. Carmine sends his regards and a fruit basket.")
        return
    top = min(state.clean + state.dirty, state.debt)
    if top <= 0:
        con.say("  Nothing to give him.")
        return
    amt = con.ask_int(f"Pay Carmine how much? (debt {money(state.debt)})", 0, top, top)
    from_dirty = min(state.dirty, amt)   # he prefers the bills nobody's counted
    state.dirty -= from_dirty
    state.clean -= amt - from_dirty
    state.debt -= amt
    if state.debt <= 0:
        state.debt = 0
        state.debt_paid_day = state.day
        con.say("  PAID. Carmine counts it twice, smiles once. 'Knew your uncle. "
                "Good man. Bad cook.' The clock stops ticking.")
    else:
        _carmine_remark(state, amt, con)


def _carmine_remark(state: State, amt: int, con: Console) -> None:
    """§2.1 payment-remark telegraph: Carmine reacts to a partial payment,
    keyed to trajectory. Deterministic in (day, amount) — transcript only."""
    if amt < 500:
        return
    big = amt >= data.START_DEBT // 4
    early = state.day <= 15
    if big and early:
        con.say("  Carmine folds the bills away without counting. 'A man who "
                "pays early is a man worth backing. We should talk when this "
                "is done.'")
    elif big:
        con.say("  Carmine weighs the envelope in one hand. 'Serious money. "
                "Finish this, and there'll be things worth discussing.'")
    elif early:
        con.say("  Carmine nods once. 'Keep paying like this and people will "
                "want to know you when it's done.'")
    else:
        con.say("  Carmine counts it slowly. 'It's something. What you'll be "
                "when this is over — you're deciding that now.'")


def _storage(state: State, shop_at: Shop, con: Console,
             streams: Streams) -> None:
    if state.warehouse is None:
        con.say("  You'd need the warehouse for that. (Improvements, mornings.)")
        return
    c = con.menu("Move what?", ["Goods shop → warehouse", "Goods warehouse → shop",
                                f"Cash to warehouse stash (dirty here: {money(state.dirty)})",
                                f"Cash from stash (stashed: {money(state.warehouse_cash)})",
                                "Back"])
    if c == 0:
        moved = 0
        for g, u in list(shop_at.stash.items()):
            if u <= 0:
                continue
            # The storage authority prices the bound and says why
            # (rev. 18 item 2): the warehouse has a cap too.
            fits = models.units_that_fit(state, models.WAREHOUSE, g)
            n = con.ask_int(
                f"Move {data.GOODS[g]['label']} (have {u}; warehouse "
                f"{models.space_used(state.warehouse)}/"
                f"{models.space_cap(state, models.WAREHOUSE)} space used; "
                f"{fits} more units fit)",
                0, min(u, fits), min(u, fits))
            models.move_goods(state, shop_at.key, models.WAREHOUSE, g, n)
            moved += n
        if moved and state.branch == "quiet_sale":
            # A truck at the rolling door while the buyer's man watches
            # the neighborhood: 20% incident risk per move (§2.4.4).
            escrow.offsite_move_risk(state, con, streams)
    elif c == 1:
        for g, u in list(state.warehouse.items()):
            if u <= 0:
                continue
            fits = models.units_that_fit(state, shop_at.key, g)
            n = con.ask_int(
                f"Bring back {data.GOODS[g]['label']} (there {u}; back "
                f"room {models.space_used(shop_at.stash)}/"
                f"{models.space_cap(state, shop_at.key)} space used; "
                f"{fits} more units fit)",
                0, min(u, fits), 0)
            models.move_goods(state, models.WAREHOUSE, shop_at.key, g, n)
    elif c == 2:
        n = con.ask_int("Stash how much dirty cash off-site?", 0, state.dirty, 0)
        state.dirty -= n
        state.warehouse_cash += n
    elif c == 3:
        n = con.ask_int("Bring back how much?", 0, state.warehouse_cash, 0)
        state.warehouse_cash -= n
        state.dirty += n


def _law_phase(state: State, con: Console, rng: random.Random) -> None:
    """Heat is local weather. The Case is climate."""
    # The law watches every address the player keeps, each against its
    # OWN district's weather — a second shop in a quiet district is not
    # sheltered by the home district's heat, nor punished by it. Shops
    # are walked in stable key order so the sweep never depends on list
    # position.
    for a_shop in sorted(state.shops, key=lambda sh: sh.key):
        if state.heat(a_shop.district) <= 70 or rng.random() >= 0.35:
            continue
        con.bullet("A squad car parks across the street for an hour. Just parks.")
        if state.branch == "straight":
            # §2.4.1: with nothing to find, searches attack the exit
            # through people — no RNG, first watcher on the roster.
            straight.search_spook(state, con)
        if rng.random() < 0.4 and state.stash_bulk(a_shop.stash) > 0:
            con.bullet("Then two officers 'stop in for a slice' and look at everything.")
            if rng.random() < 0.5:
                seized = 0
                for g in list(a_shop.stash):
                    seized += a_shop.stash[g]
                    a_shop.stash[g] = 0
                state.add_case(12 + seized * 0.2, "a walk-through found the shop stash")
                con.bullet(f"They leave with {seized} units in evidence bags. "
                           f"Nobody's under arrest. Yet.")

    if state.case >= 60 and rng.random() < 0.3:
        con.bullet("A woman in a gray suit orders espresso and asks how business is. "
                   "She doesn't give a name. She doesn't have to.")
    if state.case >= 85:
        con.bullet("Your bank calls: certain deposits are 'under review.' "
                   "The Case is nearly assembled.")
        frozen = min(state.clean, 500)
        state.clean -= frozen
    if state.case >= 100:
        state.game_over = "arrested"
