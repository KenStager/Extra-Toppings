"""Delivery routes: legit pizzas up front, coded orders in the warmer bag."""

import random

from . import data, market
from .models import Employee, State
from .ui import Console, money


def route_suspicion(covert: int, legit: int) -> float:
    """0..1 — how wrong the route looks to anyone watching."""
    total = covert + legit
    if total == 0:
        return 0.0
    return covert / total


def plan_route(state: State, con: Console, rng: random.Random,
               reserved: list | None = None) -> dict | None:
    """Morning: pick district, driver, cargo, cover. Returns a route plan.

    `reserved` employees (tonight's raid crew) can't also drive the route —
    one person, one job per night."""
    reserved = reserved or []
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
        labels.append(f"{d['label']} (heat {heat:.0f}{owner_s})")
    labels.append("Cancel — no route today")
    pick = con.menu("Run today's route where?", labels)
    if pick == len(dist_keys):
        return None
    dk = dist_keys[pick]

    names = [f"{e.name} (drive {e.driving}, nerve {e.nerve}"
             f"{', not read in' if not e.aware else ''})" for e in drivers]
    driver = drivers[con.menu("Who drives?", names)]
    ride_along = con.confirm("Ride along yourself? (You can handle trouble — and be caught in it.)")

    # Cargo: only read-in drivers carry product unless you're in the car.
    # Pizzas and product share the same wagon — every box takes a slot.
    cargo: dict[str, int] = {}
    space = data.VEHICLE_CARGO
    can_carry = driver.aware or ride_along
    if not can_carry:
        con.say(f"  {driver.name} isn't read in — pizzas only unless you ride along.")
    else:
        for g, spec in data.GOODS.items():
            have = state.shop_stash.get(g, 0)
            if have <= 0 or space <= 0:
                continue
            fit = min(have, space // spec["bulk"])
            if fit <= 0:
                continue
            price = state.prices[dk][g] if state.districts[dk].known_price_age == 0 \
                else None
            hint = f" (~{money(price)}/u here)" if price is not None else ""
            n = con.ask_int(f"Load {spec['label']}? have {have}, fits {fit}{hint}",
                            0, fit, 0)
            if n:
                cargo[g] = n            # intention only — committed at service
                space -= n * spec["bulk"]

    # Cover has to be real: only customers who actually ordered delivery.
    legit_cap = min(12, state.shop.ingredients, space, state.delivery_pool)
    if state.delivery_pool <= 0:
        con.say("  No delivery orders on the board — a busier, better-liked "
                "shop would give you cover.")
    legit = con.ask_int(
        f"Delivery orders to run for cover ({state.delivery_pool} on the board, "
        f"wagon space {space})",
        0, legit_cap, min(8 if cargo else 4, legit_cap))
    # §2.1 same-night telegraph: a contraband route scheduled while
    # payoff is within tonight's reach can book bust evidence (up to
    # ~20 + 0.3/unit on a ride-along search) and slam a Case gate the
    # sit-down reads tomorrow. What it books depends on the night, so
    # the warning is unconditional in that window — a printed line only;
    # the plan can still be replanned or cancelled from the morning menu.
    if cargo and _payoff_reachable_tonight(state, dk, cargo):
        con.say("  With the debt this close to settled, remember: a bad stop "
                "tonight goes into the file tomorrow's table reads.")
    return {"district": dk, "driver": driver, "ride_along": ride_along,
            "cargo": cargo, "legit": legit}


def _payoff_reachable_tonight(state: State, dk: str, cargo: dict) -> bool:
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
    shop_take = 2 * state.demand_today * data.TICKET_PRICE["gourmet"]
    return state.clean + state.dirty + shop_take + proceeds >= state.debt


# ── resolution ────────────────────────────────────────────────────

def _stop_risk(state: State, plan: dict) -> float:
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


def resolve_route(state: State, plan: dict, con: Console, rng: random.Random) -> dict:
    dk = plan["district"]
    driver: Employee = plan["driver"]
    cargo = plan["cargo"]
    dspec = data.DISTRICTS[dk]
    report: dict = {"sold": 0, "cash": 0, "busted": False, "lines": []}

    # Legit stops: cover, clean revenue, and food-quality exposure.
    if plan["legit"]:
        ticket = data.TICKET_PRICE[state.shop.price]
        late = sum(cargo.values()) > 0 and plan["legit"] < sum(cargo.values())
        state.clean += plan["legit"] * ticket
        state.legit_revenue_today += plan["legit"] * ticket
        if late:
            state.shop.reputation = max(0.0, state.shop.reputation - 3)
            report["lines"].append("Pizzas ran late around the extra stops. Two refunds, one review.")

    if not cargo:
        state.districts[dk].known_price_age = 0 if plan["ride_along"] else 1
        driver.routes_survived += 1
        return report

    und_mult = dspec["underground"] * market.event_mult(state, dk, "underground")
    drops = max(2, int((2 + 2 * len(cargo)) * und_mult))

    if plan["ride_along"]:
        _interactive_drops(state, plan, drops, con, rng, report)
        state.districts[dk].known_price_age = 0
    else:
        _auto_drops(state, plan, drops, con, rng, report)

    # Rival turf: they notice volume moving through their neighborhood.
    owner = dspec["rival"]
    if owner and report["sold"] > 0 and state.rivals[owner].alive:
        state.rivals[owner].relation -= report["sold"] * 0.4
        report["lines"].append(
            f"{data.RIVALS[owner]['short']}'s people watched the car all night.")

    state.add_heat(dk, 2 + report["sold"] * 0.35
                   + route_suspicion(sum(cargo.values()), plan["legit"]) * 6)
    if not report["busted"]:
        driver.routes_survived += 1
        driver.familiarity[dk] = min(10, driver.familiarity.get(dk, 0) + 1)
    return report


def _sell(state: State, dk: str, good: str, units: int, price_mult: float,
          report: dict) -> None:
    price = int(state.prices[dk][good] * price_mult)
    cash = price * units
    state.dirty += cash
    report["sold"] += units
    report["cash"] += cash
    market.record_sales(state, dk, good, units)


def _interactive_drops(state: State, plan: dict, drops: int, con: Console,
                       rng: random.Random, report: dict) -> None:
    dk = plan["district"]
    cargo = plan["cargo"]
    con.say("")
    con.say(f"  You ride shotgun. {plan['driver'].name} drives. "
            f"{drops} coded orders on the board tonight.")
    for stop in range(drops):
        goods_left = [g for g, u in cargo.items() if u > 0]
        if not goods_left:
            break
        g = rng.choice(goods_left)
        spec = data.GOODS[g]
        base_price = state.prices[dk][g]
        mult = rng.uniform(0.85, 1.2)
        offer = int(base_price * mult)
        top_want = max(2, int(4 * data.DISTRICTS[dk]["underground"]
                              * market.event_mult(state, dk, "underground")))
        want = min(cargo[g], rng.randint(1, top_want))
        choice = con.menu(
            f"Stop {stop+1}: buyer wants {want}x {spec['label']} at {money(offer)}/unit.",
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
            state.shop_stash[g] = state.shop_stash.get(g, 0) + u


def _handle_police_stop(state: State, plan: dict, con: Console,
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


def _bust(state: State, plan: dict, con: Console, rng: random.Random,
          report: dict, resisted: bool) -> bool:
    cargo = plan["cargo"]
    seized_units = sum(cargo.values())
    for g in cargo:
        cargo[g] = 0
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
            report["lines"].append(f"{driver.name} is booked for possession.")
            con.say(f"  They take {driver.name} in. The wagon gets towed.")
    report["busted"] = True
    report["lines"].append("The cargo is gone and your name is in a report.")
    con.say(f"  Seized: {seized_units} units. The night is a total loss.")
    return False


def _auto_drops(state: State, plan: dict, drops: int, con: Console,
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
            seized = sum(cargo.values())
            driver.arrested = True
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
                state.shop_stash[g] = state.shop_stash.get(g, 0) + u
        return

    sell_frac = min(1.0, (0.40 + driver.driving * 0.045 + driver.nerve * 0.03
                          + fam * 0.04) * (drops / 3))
    for g in list(cargo):
        units = int(cargo[g] * sell_frac)
        if units:
            cargo[g] -= units
            _sell(state, dk, g, units, rng.uniform(0.9, 1.05), report)
    for g, u in cargo.items():
        if u > 0:
            state.shop_stash[g] = state.shop_stash.get(g, 0) + u
    report["lines"].append(
        f"{driver.name} comes back with {money(report['cash'])} in the bag "
        f"and firsthand prices from {data.DISTRICTS[dk]['label']}.")
    state.districts[dk].known_price_age = 0
