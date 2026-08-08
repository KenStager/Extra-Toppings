"""The daily rhythm: Morning (prepare) → Service (operate) → Night (settle).

Randomness is split by domain (see rng.Streams): the world's dice — prices,
events, rumors, suppliers, demand — are drawn per-day and cannot be shifted
by anything the player does. Player-facing dice use persistent streams.
"""

import random

from . import data, market, raids, rivals, routes, shop
from .models import State
from .rng import Streams
from .ui import Console, money

QUALITY_LEVELS = ["cheap", "standard", "gourmet"]


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
        con.say(f"  Carmine expects {money(state.debt)} within {days_left} day(s).")

    con.say(f"  Order book: ~{state.demand_today} customers expected, "
            f"{state.delivery_pool} delivery orders on the board.")
    for line in state.news:
        con.bullet(f"NEWS: {line}")
    for line in market.rumor_sheet(state, streams.daily(state.day, "rumors")):
        con.bullet(f"RUMOR: {line}")
    _staff_trouble(state, con, streams.staff)

    # Carmine won't let his investment starve: he fronts stock — onto the debt.
    if state.shop.ingredients < 10 and state.clean < 200:
        shop.stock_pantry(state, 40)
        state.debt += 40 * data.INGREDIENT_COST[state.shop.quality] + 100
        con.bullet("Carmine's nephew drops off flour, cheese and cans 'on account.' "
                   "The account, of course, is the debt.")

    supplier = _supplier_offer(state, streams.daily(state.day, "supplier"))
    if supplier:
        g = data.GOODS[supplier["good"]]
        con.bullet(f"SUPPLIER: {supplier['units']}x {g['label']} at "
                   f"{money(supplier['price'])}/unit, cash — he doesn't care whose.")

    plans: dict = {"route": None, "raid": None}
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
            reserved = plans["raid"]["team"] if plans.get("raid") else []
            plans["route"] = routes.plan_route(state, con, streams.routes,
                                               reserved=reserved)
        elif c == 7:
            route = plans.get("route")
            reserved = [route["driver"]] if route else []
            if route and route["ride_along"]:
                con.say("  You'll be in the wagon tonight — the crew goes "
                        "without you, and without your nerve.")
            plans["raid"] = raids.plan_raid(state, con, streams.raids,
                                            reserved=reserved,
                                            wagon_free=route is None)
        elif c == 8:
            break
    return plans


def _market_board(state: State, con: Console) -> None:
    con.say("")
    for dk, dspec in data.DISTRICTS.items():
        d = state.districts[dk]
        con.say(f"  {dspec['label']} — heat {d.heat:.0f}  ({dspec['flavor']})")
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
    shop.recompute_demand(state)
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
    shop.stock_pantry(state, n)
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
    room = state.shop.stash_cap - state.stash_bulk(state.shop_stash)
    fit = room // data.GOODS[offer["good"]]["bulk"]
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
        con.say(f"  Boxes come in through the alley door. Stash: "
                f"{state.stash_bulk(state.shop_stash)}/{state.shop.stash_cap} bulk.")
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
                state.add_case(6, f"{e.name} walked out knowing everything")
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
                state.add_case(10, f"{e.name} had a long talk with a detective")
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
            names = [e.name for e in crew] + ["Back"]
            p = con.menu("Let go whom?", names)
            if p < len(crew):
                e = crew[p]
                e.hired = False
                if e.aware:
                    state.add_case(6, f"{e.name} was fired knowing everything")
                    con.say(f"  {e.name} leaves quietly. Too quietly. They know things.")
                else:
                    con.say(f"  {e.name} is gone.")
        else:
            return


def _improvements(state: State, con: Console) -> None:
    while True:
        owned = state.shop.upgrades
        keys = [k for k in data.UPGRADES if k not in owned]
        opts = [f"{data.UPGRADES[k]['label']} — {money(data.UPGRADES[k]['cost'])} clean. "
                f"{data.UPGRADES[k]['desc']}" for k in keys]
        if state.warehouse is None:
            opts.append(f"Rent the harbor warehouse — {money(data.WAREHOUSE_RENT)}/day dirty. "
                        f"Bulk space, off-site stash, one more address to defend.")
        opts.append("Back")
        c = con.menu(f"Improvements (clean {money(state.clean)}):", opts)
        if c < len(keys):
            k = keys[c]
            cost = data.UPGRADES[k]["cost"]
            if state.clean < cost:
                con.say("  Not with today's clean cash.")
            else:
                state.clean -= cost
                owned.add(k)
                con.say(f"  {data.UPGRADES[k]['label']}: done by closing time.")
                shop.recompute_demand(state)
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
    report = shop.simulate_shift(state, route_legit,
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
    for g in list(plan["cargo"]):
        have = state.shop_stash.get(g, 0)
        take = min(plan["cargo"][g], have)
        if take < plan["cargo"][g]:
            con.bullet(f"Only {take}x {data.GOODS[g]['label']} left to load — "
                       f"the stash moved since this morning.")
        plan["cargo"][g] = take
        state.shop_stash[g] = have - take
    # Cover pizzas are real orders AND real oven time.
    doable = min(plan["legit"], state.delivery_pool,
                 state.shop.kitchen_cap, state.shop.ingredients)
    if doable < plan["legit"]:
        con.bullet(f"The kitchen fills {doable} of {plan['legit']} planned "
                   f"delivery orders — orders, ovens and pantry set the limit.")
    plan["legit"] = doable
    state.shop.ingredients -= doable
    return True


# ══ NIGHT ═════════════════════════════════════════════════════════

def night(state: State, plans: dict, service_report: dict, con: Console,
          streams: Streams) -> None:
    con.header(f"DAY {state.day} — AFTER CLOSE")

    # Today's wear is booked at close, BEFORE tonight's raids and rival
    # moves create new effects — a coupon blitz or smashed oven tonight
    # keeps its full stated duration of service days.
    if state.shop.damage_days:
        state.shop.damage_days -= 1
    if state.shop.coupon_days:
        state.shop.coupon_days -= 1

    raid_plan = plans.get("raid")
    if raid_plan:
        # The day happened between planning and doing: anyone arrested,
        # injured or gone since morning is off the job.
        team = [e for e in raid_plan["team"] if e.available]
        if not team:
            con.say("  The night job is scrubbed — the crew you picked this "
                    "morning didn't make it to nightfall intact.")
        else:
            if len(team) < len(raid_plan["team"]):
                con.say("  The crew is short tonight; the job goes ahead anyway.")
            raid_plan["team"] = team
            raid_plan["wagon_free"] = plans.get("route") is None
            raids.run_raid(state, raid_plan, con, streams.raids)

    for key, rival in state.rivals.items():
        if rival.alive and rival.raid_warning == 1:
            raids.incoming_raid(state, key, con, streams.raids)

    _payroll_and_rent(state, con)

    # The ceiling covers every honest dollar of the day — and it's a
    # nightly total, not a per-transaction allowance.
    ceiling = shop.believable_ceiling(state, state.legit_revenue_today)
    laundered_tonight = 0
    while True:
        con.say("")
        con.say(f"  Clean {money(state.clean)} | Dirty {money(state.dirty)} | "
                f"Debt {money(state.debt)}")
        remaining = max(0, ceiling - laundered_tonight)
        con.say(f"  Books can absorb about {money(remaining)} more tonight "
                f"without raising eyebrows.")
        c = con.menu("Settle accounts:", [
            "Launder dirty cash through the register",
            "Pay Carmine (he prefers unmarked bills)",
            "Move stash / cash (shop ↔ warehouse)",
            "Talk to a rival",
            "Lock up →",
        ])
        if c == 0:
            laundered_tonight += _launder(state, remaining, con)
        elif c == 1:
            _pay_debt(state, con)
        elif c == 2:
            _storage(state, con)
        elif c == 3:
            rivals.negotiate(state, con, streams.rivals)
        else:
            break

    rivals.rival_phase(state, con, streams.rivals)
    _law_phase(state, con, streams.daily(state.day, "law"))

    # The city cools a little overnight.
    for d in state.districts.values():
        d.heat = max(0.0, d.heat - 5)
    state.day += 1


def _payroll_and_rent(state: State, con: Console) -> None:
    wages = sum(e.wage for e in state.hired() if not e.arrested)
    costs = wages + data.RENT_PER_DAY
    if state.warehouse is not None:
        if state.dirty >= data.WAREHOUSE_RENT:
            state.dirty -= data.WAREHOUSE_RENT
        else:
            costs += data.WAREHOUSE_RENT
    if state.clean >= costs:
        state.clean -= costs
        con.say(f"  Wages and rent paid: {money(costs)} clean.")
    else:
        short = costs - state.clean
        state.clean = 0
        con.say(f"  You come up {money(short)} short on payroll. People notice.")
        for e in state.hired():
            e.morale -= 2


def _launder(state: State, remaining: int, con: Console) -> int:
    """Wash dirty cash against tonight's REMAINING allowance. Returns the
    amount washed so the night loop can shrink the allowance — chunking
    the wash into small calls buys nothing."""
    if state.dirty <= 0:
        con.say("  No dirty cash on hand.")
        return 0
    amt = con.ask_int(f"Run how much through the books? (dirty {money(state.dirty)})",
                      0, state.dirty, min(state.dirty, remaining))
    if amt <= 0:
        return 0
    state.dirty -= amt
    state.clean += amt
    state.total_laundered += amt
    if amt > remaining:
        over = amt - remaining
        evidence = min(20.0, over / 400)
        state.add_case(evidence, f"the register claimed {money(amt)} beyond "
                                 f"any plausible night's sales")
        con.say(f"  {money(amt)} washed. {money(over)} of it is hard to explain. "
                f"Somewhere, a spreadsheet notices.")
    else:
        state.add_case(0.5, "")
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


def _storage(state: State, con: Console) -> None:
    if state.warehouse is None:
        con.say("  You'd need the warehouse for that. (Improvements, mornings.)")
        return
    c = con.menu("Move what?", ["Goods shop → warehouse", "Goods warehouse → shop",
                                f"Cash to warehouse stash (dirty here: {money(state.dirty)})",
                                f"Cash from stash (stashed: {money(state.warehouse_cash)})",
                                "Back"])
    if c == 0:
        for g, u in list(state.shop_stash.items()):
            if u <= 0:
                continue
            n = con.ask_int(f"Move {data.GOODS[g]['label']} (have {u})", 0, u, u)
            state.shop_stash[g] -= n
            state.warehouse[g] = state.warehouse.get(g, 0) + n
    elif c == 1:
        for g, u in list(state.warehouse.items()):
            if u <= 0:
                continue
            room = (state.shop.stash_cap - state.stash_bulk(state.shop_stash)) \
                // data.GOODS[g]["bulk"]
            n = con.ask_int(f"Bring back {data.GOODS[g]['label']} (there {u}, fits {room})",
                            0, min(u, room), 0)
            state.warehouse[g] -= n
            state.shop_stash[g] = state.shop_stash.get(g, 0) + n
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
    home_heat = state.heat(data.HOME_DISTRICT)
    if home_heat > 70 and rng.random() < 0.35:
        con.bullet("A squad car parks across the street for an hour. Just parks.")
        if rng.random() < 0.4 and state.stash_bulk(state.shop_stash) > 0:
            con.bullet("Then two officers 'stop in for a slice' and look at everything.")
            if rng.random() < 0.5:
                seized = 0
                for g in list(state.shop_stash):
                    seized += state.shop_stash[g]
                    state.shop_stash[g] = 0
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
