"""The daily rhythm: Morning (prepare) → Service (operate) → Night (settle).

Randomness is split by domain (see rng.Streams): the world's dice — prices,
events, rumors, suppliers, demand — are drawn per-day and cannot be shifted
by anything the player does. Player-facing dice use persistent streams.
"""

import random
from dataclasses import dataclass

from . import (data, escrow, evidence, market, models, raids, rivals,
               routes, shop, straight, war)
from .config import GameConfig
from .models import SitdownSnapshot, State, case_prefix
from .rng import Streams
from .ui import Console, money

QUALITY_LEVELS = ["cheap", "standard", "gourmet"]


# ── THE night-assignment authority (rev. 15 item 2) ───────────────

def night_reserved(plans: dict, but: str | None = None) -> list:
    """Who is spoken for tonight by every job EXCEPT `but`. Routes and
    the salvage pickup reserve their driver; the raid reserves its
    team. Planning menus and the night's execution both consult this
    one derivation — never another ad-hoc reserved= list."""
    out: list = []
    for job in ("route", "salvage", "raid"):
        plan = plans.get(job)
        if not plan or job == but:
            continue
        if job == "raid":
            out.extend(plan["team"])
        else:
            out.append(plan["driver"])
    return out


def wagon_job(plans: dict, but: str | None = None) -> str | None:
    """The wagon does one job a night: the route or the pickup."""
    for job in ("route", "salvage"):
        if job != but and plans.get(job):
            return job
    return None


# Why the wagon is gone, in the player's words — one home, so the
# menu, the raid line and the tests all read the same sentence.
WAGON_NOTES = {
    "route": "out on tonight's route",
    "salvage": "out on tonight's pickup",
    "raid": "out with the night crew",
    "decoy": "already loaded and gone",
}


@dataclass
class WagonNight:
    """THE night's wagon assignment (design rev. 25 item 1): ONE
    stateful answer, updated by each consumer as it executes.

    A derived boolean cannot do this job. `wagon_used` below reads
    the morning's plans and the service report, so it is blind to
    everything that happens later the same night — the outgoing raid
    that hauls with the wagon, and the decoy that loads it against
    the first of two arriving rivals. The night therefore carries
    this object and spends it exactly once; every later consumer
    asks it rather than re-deriving an answer that has gone stale.
    """

    claimed_by: str | None = None

    @property
    def available(self) -> bool:
        return self.claimed_by is None

    @property
    def note(self) -> str:
        """The player-facing reason, empty while the wagon is free."""
        return WAGON_NOTES.get(self.claimed_by or "", "")

    def view(self) -> models.WagonAvailability:
        """The immutable answer consumers read. One value, so an
        availability flag and its reason cannot arrive contradicting
        each other."""
        return models.WagonAvailability(self.available, self.note)

    def claim(self, by: str) -> None:
        """Take the wagon out, exclusively. Fails CLOSED: there is one
        wagon, so a second claim is not a thing to absorb quietly — it
        means a consumer asked `available` and acted on a stale answer,
        which is exactly the class of bug this authority exists to end.
        Every caller checks availability first, so no legitimate path
        reaches a second claim."""
        if by not in WAGON_NOTES:
            raise ValueError(f"unknown wagon consumer {by!r}")
        if self.claimed_by is not None:
            raise RuntimeError(
                f"the wagon is already {self.note} — {by!r} cannot "
                f"take it too; there is only one wagon")
        self.claimed_by = by


def wagon_used(plans: dict, service_report: dict) -> bool:
    """Execution truth (rev. 17 item 6): by night the wagon jobs have
    already run, so the raid's wagon question reads what HAPPENED —
    not the continued existence of morning intentions. A pickup
    scrubbed before departure never took the wagon out; absent an
    execution record the commitment stands (fail toward the wagon
    being busy, never toward a phantom grant)."""
    job = wagon_job(plans)
    if job == "salvage":
        result = service_report.get("salvage")
        return result is None or result.wagon_used
    return job is not None


# ══ MORNING ═══════════════════════════════════════════════════════

def morning(state: State, con: Console, streams: Streams) -> dict:
    """Read the news, set the day up. Returns plans for later phases."""
    market.draw_events(state, streams.daily(state.day, "events"))
    market.roll_prices(state, streams.daily(state.day, "market"))
    shop.roll_demand(state, streams.daily(state.day, "demand"))

    con.header(f"DAY {state.day} of {data.DEBT_DUE_DAY} — MORNING")
    con.say(f"  Clean {money(state.clean)} | Dirty {money(state.dirty)} | "
            f"Debt {money(state.debt)} | Rep {state.shop.reputation:.0f} | "
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

    con.say(f"  Order book: ~{state.demand_today} customers expected, "
            f"{state.delivery_pool} delivery orders on the board.")
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
    if state.shop.ingredients < 10 and state.clean < 200 \
            and not active_branch:
        shop.stock_pantry(state, state.shop, 40)
        state.debt += 40 * data.INGREDIENT_COST[state.shop.quality] + 100
        con.bullet("Carmine's nephew drops off flour, cheese and cans 'on account.' "
                   "The account, of course, is the debt.")

    plans: dict = {"route": None, "raid": None}
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
            _market_board(state, con)
        elif c == 1:
            _kitchen_policy(state, con, plans)
        elif c == 2:
            _buy_ingredients(state, con)
        elif c == 3 and supplier:
            supplier = _buy_supplier(state, supplier, con)
        elif c == 4:
            _staff_menu(state, con, streams.staff)
        elif c == 5:
            _improvements(state, con)
        elif c == 6:
            plans["route"] = routes.plan_route(
                state, con, streams.routes,
                reserved=night_reserved(plans, but="route"))
        elif c == 7:
            route = plans.get("route")
            if route and route["ride_along"]:
                con.say("  You'll be in the wagon tonight — the crew goes "
                        "without you, and without your nerve.")
            plans["raid"] = raids.plan_raid(
                state, con, streams.raids,
                reserved=night_reserved(plans, but="raid"),
                wagon_free=wagon_job(plans) is None)
        elif c == 8:
            break
    return plans


def _straight_morning_menu(state: State, con: Console, streams: Streams,
                           plans: dict, offer: dict | None) -> None:
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
            _market_board(state, con)
        elif c == 1:
            _kitchen_policy(state, con, plans)
        elif c == 2:
            _buy_ingredients(state, con)
        elif c == 3 and offer:
            if straight.take_temptation(state, offer, con, streams):
                offer = None
        elif c == 4:
            _staff_menu(state, con, streams.staff)
        elif c == 5:
            _improvements(state, con)
        elif c == 6:
            fire_sale_done = _disposal_menu(state, con, streams, plans,
                                            fire_sale_done)
        elif c == 7:
            straight.show_case_file(state, con)
        elif c == 8:
            break


def _war_morning_menu(state: State, con: Console, streams: Streams,
                      plans: dict, supplier: dict | None) -> None:
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
            _market_board(state, con)
        elif key == "kitchen":
            _kitchen_policy(state, con, plans)
        elif key == "buy":
            _buy_ingredients(state, con)
        elif key == "supplier" and supplier:
            supplier = _buy_supplier(state, supplier, con)
        elif key == "staff":
            _staff_menu(state, con, streams.staff)
        elif key == "improve":
            _improvements(state, con)
        elif key == "route":
            if wagon_job(plans, but="route") is not None:
                con.say("  The wagon is spoken for tonight — the pickup "
                        "has it. Recall it first if the route matters "
                        "more.")
                continue
            plans["route"] = routes.plan_route(
                state, con, streams.routes,
                reserved=night_reserved(plans, but="route"))
        elif key == "raid":
            route = plans.get("route")
            if route and route["ride_along"]:
                con.say("  You'll be in the wagon tonight — the crew goes "
                        "without you, and without your nerve.")
            plans["raid"] = raids.plan_raid(
                state, con, streams.raids,
                reserved=night_reserved(plans, but="raid"),
                wagon_free=wagon_job(plans) is None)
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
                reserved=night_reserved(plans, but="salvage"),
                wagon_taken=wagon_job(plans, but="salvage") is not None)
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
                   plans: dict, fire_sale_done: bool) -> bool:
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
        elif plans.get("route"):
            con.say("  Tonight's wagon is already spoken for.")
        else:
            plan = routes.plan_route(state, con, streams.routes)
            if plan is not None:
                if any(plan["cargo"].values()):
                    plan["disposal"] = True
                    con.say("  A disposal run spends one of the three "
                            "when the wagon actually loads — and the "
                            "clean days start over when it rolls.")
                else:
                    con.say("  Pizzas only: an honest drive spends no "
                            "run and commits no crime.")
                plans["route"] = plan
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


def _market_board(state: State, con: Console) -> None:
    con.say("")
    # Inventory reads units × bulk each = bulk used, everywhere a
    # stash is shown (rev. 17 item 1).
    for line in routes.inventory_lines("The back room", state.shop_stash,
                                       state.shop.stash_cap):
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


def _kitchen_policy(state: State, con: Console, plans: dict | None = None) -> None:
    con.say(f"  Pantry holds {state.shop.ingredients} orders of "
            f"{state.shop.pantry_quality} stock — the kitchen cooks what "
            f"it has, whatever the menu says.")
    q = con.menu(f"Ingredient quality (now: {state.shop.quality}):",
                 [f"{lv} (cost {money(data.INGREDIENT_COST[lv])}/order)"
                  for lv in QUALITY_LEVELS])
    state.shop.quality = QUALITY_LEVELS[q]
    p = con.menu(f"Menu pricing (now: {state.shop.price}):",
                 [f"{lv} (ticket {money(data.TICKET_PRICE[lv])})"
                  for lv in QUALITY_LEVELS])
    state.shop.price = QUALITY_LEVELS[p]
    if state.shop.price == "gourmet" and state.shop.quality == "cheap":
        con.say("  Charging gourmet prices for cheap pies. Bold. Reviews incoming.")
    # New prices, new crowd — the order book re-forms around the menu.
    shop.recompute_demand(state, state.shop)
    con.say(f"  Order book now: ~{state.demand_today} customers, "
            f"{state.delivery_pool} delivery orders.")
    route = (plans or {}).get("route")
    if route and route["legit"] > state.delivery_pool:
        con.say("  Tonight's route was planned against the old order book — "
                "the kitchen will fill what it can.")


def _buy_ingredients(state: State, con: Console) -> None:
    cost = data.INGREDIENT_COST[state.shop.quality]
    most = state.clean // cost if cost else 0
    restock = max(0, min(most, 80 - state.shop.ingredients))
    n = con.ask_int(f"Buy how many orders of stock? ({money(cost)} each, clean cash, "
                    f"have {state.shop.ingredients} {state.shop.pantry_quality})",
                    0, min(most, 200), restock)
    state.clean -= n * cost
    before_q = state.shop.pantry_quality if state.shop.ingredients else None
    shop.stock_pantry(state, state.shop, n)
    if before_q and state.shop.pantry_quality != before_q:
        con.say(f"  The new {state.shop.quality} stock mixes into the walk-in — "
                f"the pantry now cooks as {state.shop.pantry_quality}.")


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


def _buy_supplier(state: State, offer: dict, con: Console) -> dict | None:
    # The storage authority prices the bound (rev. 18 item 2).
    fit = models.units_that_fit(state, state.shop.key, offer["good"])
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
        state.shop_stash[offer["good"]] = state.shop_stash.get(offer["good"], 0) + n
        offer["units"] -= n
        con.say(f"  Boxes come in through the alley door. The back room: "
                f"{models.space_used(state.shop_stash)}/"
                f"{models.space_cap(state, state.shop.key)} space used.")
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


def _improvements(state: State, con: Console) -> None:
    while True:
        owned = state.shop.upgrades
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
                shop.recompute_demand(state, state.shop)
        elif state.warehouse is None and c == len(keys):
            state.warehouse = {}
            con.say("  Keys to a rusted rolling door. Nobody asks what's in the crates.")
        else:
            return


# ══ SERVICE ═══════════════════════════════════════════════════════

def service(state: State, plans: dict, con: Console, streams: Streams) -> dict:
    con.header(f"DAY {state.day} — SERVICE")
    plan = plans.get("route")
    if plan and not _commit_route(state, plan, con):
        plans["route"] = plan = None
    route_legit = plan["legit"] if plan else 0
    report = shop.simulate_shift(state, state.shop, route_legit,
                                 streams.daily(state.day, "critic"))
    lost = f" ({report['lost']} turned away)" if report["lost"] else ""
    con.say(f"  Orders {report['orders']}/{report['demand']} demanded{lost}"
            f" | clean revenue {money(report['revenue'])}")
    if report["critic_line"]:
        con.bullet(report["critic_line"])
    if state.shop.ingredients < 10:
        con.bullet(f"Pantry low: {state.shop.ingredients} orders of stock left.")

    if plans.get("route"):
        r = routes.resolve_route(state, plans["route"], con, streams.routes)
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
            reserved=night_reserved(plans, but="salvage"))
    if state.branch == "quiet_sale":
        # The buyer's man walks the shop every diligence afternoon.
        escrow.walkthrough(state, con, streams)
    return report


def _commit_route(state: State, plan: dict, con: Console) -> bool:
    """Morning plans are intentions; resources commit when service starts.
    Cancelled or replaced plans never touch inventory. Returns False (and
    commits nothing) if the plan can no longer run at all."""
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
        have = state.shop_stash.get(g, 0)
        take = min(want, have)
        if take < want:
            con.bullet(f"Only {take}x {data.GOODS[g]['label']} left to load — "
                       f"the stash moved since this morning.")
        if take:
            committed.cargo[g] = take
    # Cover pizzas are real orders AND real oven time.
    committed.legit = min(planned.legit, state.delivery_pool,
                          state.shop.kitchen_cap, state.shop.ingredients)
    if committed.legit < planned.legit:
        con.bullet(f"The kitchen fills {committed.legit} of "
                   f"{planned.legit} planned delivery orders — orders, "
                   f"ovens and pantry set the limit.")
    committed.validate()
    for g, take in committed.cargo.items():
        state.shop_stash[g] = state.shop_stash.get(g, 0) - take
    state.shop.ingredients -= committed.legit
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
    con.header(f"DAY {state.day} — AFTER CLOSE")
    # The night's wagon, opened from what the service phase actually
    # did (a departed route or pickup holds it; a pickup scrubbed
    # before departure never took it out) and spent by each later
    # consumer in turn — design rev. 25 item 1.
    wagon = WagonNight()
    service_job = wagon_job(plans)
    if service_job is not None and wagon_used(plans, service_report):
        wagon.claim(service_job)

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
        taken = night_reserved(plans, but="raid")
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
            raid_plan["wagon_free"] = wagon.available
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
            if (raid_plan["objective"] == "steal_stock"
                    and raid_plan["wagon_free"]):
                # Claimed BEFORE the job runs: departure is what
                # consumes the wagon, not the outcome.
                wagon.claim("raid")
            raids.run_raid(state, raid_plan, con, streams.raids)

    for key, rival in state.rivals.items():
        if rival.alive and rival.raid_warning == 1:
            # Both rivals can arrive on one night, and the first
            # decoy takes the wagon with it — the second gets the
            # truth, not the morning's answer (design rev. 25).
            result = raids.incoming_raid(state, key, con, streams.raids,
                                         wagon=wagon.view())
            if result.wagon_taken:
                wagon.claim("decoy")
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
            _storage(state, con, streams)
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


def _storage(state: State, con: Console, streams: Streams) -> None:
    if state.warehouse is None:
        con.say("  You'd need the warehouse for that. (Improvements, mornings.)")
        return
    c = con.menu("Move what?", ["Goods shop → warehouse", "Goods warehouse → shop",
                                f"Cash to warehouse stash (dirty here: {money(state.dirty)})",
                                f"Cash from stash (stashed: {money(state.warehouse_cash)})",
                                "Back"])
    if c == 0:
        moved = 0
        for g, u in list(state.shop_stash.items()):
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
            models.move_goods(state, state.shop.key, models.WAREHOUSE, g, n)
            moved += n
        if moved and state.branch == "quiet_sale":
            # A truck at the rolling door while the buyer's man watches
            # the neighborhood: 20% incident risk per move (§2.4.4).
            escrow.offsite_move_risk(state, con, streams)
    elif c == 1:
        for g, u in list(state.warehouse.items()):
            if u <= 0:
                continue
            fits = models.units_that_fit(state, state.shop.key, g)
            n = con.ask_int(
                f"Bring back {data.GOODS[g]['label']} (there {u}; back "
                f"room {models.space_used(state.shop_stash)}/"
                f"{models.space_cap(state, state.shop.key)} space used; "
                f"{fits} more units fit)",
                0, min(u, fits), 0)
            models.move_goods(state, models.WAREHOUSE, state.shop.key, g, n)
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
