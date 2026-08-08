"""The daily rhythm: Morning (prepare) → Service (operate) → Night (settle)."""

import random

from . import data, market, raids, rivals, routes, shop
from .models import State
from .ui import Console, money

QUALITY_LEVELS = ["cheap", "standard", "gourmet"]


# ══ MORNING ═══════════════════════════════════════════════════════

def morning(state: State, con: Console, rng: random.Random) -> dict:
    """Read the news, set the day up. Returns plans for later phases."""
    market.draw_events(state, rng)
    market.roll_prices(state, rng)

    con.header(f"DAY {state.day} of {data.DEBT_DUE_DAY} — MORNING")
    con.say(f"  Clean {money(state.clean)} | Dirty {money(state.dirty)} | "
            f"Debt {money(state.debt)} | Rep {state.shop.reputation:.0f} | "
            f"Case {state.case:.0f}/100")
    if state.debt > 0:
        days_left = data.DEBT_DUE_DAY - state.day
        con.say(f"  Carmine expects {money(state.debt)} within {days_left} day(s).")

    for line in state.news:
        con.bullet(f"NEWS: {line}")
    for line in market.rumor_sheet(state, rng):
        con.bullet(f"RUMOR: {line}")
    _staff_trouble(state, con, rng)

    # Carmine won't let his investment starve: he fronts stock — onto the debt.
    if state.shop.ingredients < 10 and state.clean < 200:
        state.shop.ingredients += 40
        state.debt += 40 * data.INGREDIENT_COST[state.shop.quality] + 100
        con.bullet("Carmine's nephew drops off flour, cheese and cans 'on account.' "
                   "The account, of course, is the debt.")

    supplier = _supplier_offer(state, rng)
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
            _kitchen_policy(state, con)
        elif c == 2:
            _buy_ingredients(state, con)
        elif c == 3 and supplier:
            supplier = _buy_supplier(state, supplier, con)
        elif c == 4:
            _staff_menu(state, con, rng)
        elif c == 5:
            _improvements(state, con)
        elif c == 6:
            plans["route"] = routes.plan_route(state, con, rng)
        elif c == 7:
            plans["raid"] = raids.plan_raid(state, con, rng)
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


def _kitchen_policy(state: State, con: Console) -> None:
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


def _buy_ingredients(state: State, con: Console) -> None:
    cost = data.INGREDIENT_COST[state.shop.quality]
    most = state.clean // cost if cost else 0
    restock = max(0, min(most, 80 - state.shop.ingredients))
    n = con.ask_int(f"Buy how many orders of stock? ({money(cost)} each, clean cash, "
                    f"have {state.shop.ingredients})", 0, min(most, 200), restock)
    state.clean -= n * cost
    state.shop.ingredients += n


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
            else:
                e.hired = False
                con.bullet(f"{e.name} quit. Left the apron on the counter.")


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
        elif state.warehouse is None and c == len(keys):
            state.warehouse = {}
            con.say("  Keys to a rusted rolling door. Nobody asks what's in the crates.")
        else:
            return


# ══ SERVICE ═══════════════════════════════════════════════════════

def service(state: State, plans: dict, con: Console, rng: random.Random) -> dict:
    con.header(f"DAY {state.day} — SERVICE")
    report = shop.simulate_shift(state, rng)
    lost = f" ({report['lost']} turned away)" if report["lost"] else ""
    con.say(f"  Orders {report['orders']}/{report['demand']} demanded{lost}"
            f" | clean revenue {money(report['revenue'])}")
    if report["critic_line"]:
        con.bullet(report["critic_line"])
    if state.shop.ingredients < 10:
        con.bullet(f"Pantry low: {state.shop.ingredients} orders of stock left.")

    if plans.get("route"):
        r = routes.resolve_route(state, plans["route"], con, rng)
        for line in r["lines"]:
            con.bullet(line)
        if r["cash"]:
            con.say(f"  Route take: {money(r['cash'])} dirty, {r['sold']} units moved.")
    return report


# ══ NIGHT ═════════════════════════════════════════════════════════

def night(state: State, plans: dict, service_report: dict, con: Console,
          rng: random.Random) -> None:
    con.header(f"DAY {state.day} — AFTER CLOSE")

    if plans.get("raid"):
        raids.run_raid(state, plans["raid"], con, rng)

    for key, rival in state.rivals.items():
        if rival.alive and rival.raid_warning == 1:
            raids.incoming_raid(state, key, con, rng)

    _payroll_and_rent(state, con)

    ceiling = shop.believable_ceiling(state, service_report["revenue"])
    while True:
        con.say("")
        con.say(f"  Clean {money(state.clean)} | Dirty {money(state.dirty)} | "
                f"Debt {money(state.debt)}")
        con.say(f"  Books can absorb about {money(ceiling)} tonight without "
                f"raising eyebrows.")
        c = con.menu("Settle accounts:", [
            "Launder dirty cash through the register",
            "Pay Carmine (he prefers unmarked bills)",
            "Move stash / cash (shop ↔ warehouse)",
            "Talk to a rival",
            "Lock up →",
        ])
        if c == 0:
            _launder(state, ceiling, con)
        elif c == 1:
            _pay_debt(state, con)
        elif c == 2:
            _storage(state, con)
        elif c == 3:
            rivals.negotiate(state, con, rng)
        else:
            break

    rivals.rival_phase(state, con, rng)
    _law_phase(state, con, rng)

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


def _launder(state: State, ceiling: int, con: Console) -> None:
    if state.dirty <= 0:
        con.say("  No dirty cash on hand.")
        return
    amt = con.ask_int(f"Run how much through the books? (dirty {money(state.dirty)})",
                      0, state.dirty, min(state.dirty, ceiling))
    if amt <= 0:
        return
    state.dirty -= amt
    state.clean += amt
    state.total_laundered += amt
    if amt > ceiling:
        over = amt - ceiling
        evidence = min(20.0, over / 400)
        state.add_case(evidence, f"the register claimed {money(amt)} on a slow day")
        con.say(f"  {money(amt)} washed. {money(over)} of it is hard to explain. "
                f"Somewhere, a spreadsheet notices.")
    else:
        state.add_case(0.5, "")
        con.say(f"  {money(amt)} washed clean. The books look plausible.")
    observant = [e for e in state.hired() if e.trait == "observant" and not e.aware]
    if observant and amt > ceiling:
        e = observant[0]
        e.morale -= 1
        con.say(f"  {e.name} rechecks the till twice and says nothing.")


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
