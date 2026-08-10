"""The legitimate pizzeria: demand, quality, revenue, reputation.

Demand is rolled each morning from an action-independent daily stream.
A slice of that demand wants delivery — and *only* those real orders can
serve as cover on a route. A hollow restaurant has nothing to hide behind.
"""

import random

from . import data, market, straight
from .models import State


def cooks_skill(state: State, shop) -> int:
    """The best cook ON DUTY AT THIS ADDRESS (design rev. 27). The
    roster does not double when the addresses do: a shop with nobody
    assigned to its kitchen bakes at the floor, which is what makes
    staffing two addresses a real constraint rather than a formality."""
    cooks = [e for e in state.hired()
             if e.available and e.role == "cook"
             and e.shop_key == shop.key]
    return max([e.food for e in cooks], default=2)


DELIVERY_SHARE = 0.35   # fraction of real demand that phones in a delivery
QUALITY_ORDER = {"cheap": 0, "standard": 1, "gourmet": 2}


def stock_pantry(state: State, shop, units: int) -> None:
    """Add stock bought at the CURRENT purchasing policy. Stock keeps its
    identity: mixing grades drags the pantry down to the lower one —
    a gourmet pie built on cheap flour is a cheap pie."""
    if units <= 0:
        return
    if shop.ingredients <= 0 or QUALITY_ORDER[shop.quality] < QUALITY_ORDER[shop.pantry_quality]:
        shop.pantry_quality = shop.quality
    shop.ingredients += units


def roll_demand(state: State, rng: random.Random) -> None:
    """Morning: roll today's demand LUCK once — ONE roll for the city,
    not one per address (design rev. 22 item 6): a day's weather is a
    world fact, and each address then prices that same crowd through
    its own district, reputation and menu. The demand itself is a
    deterministic function of policy, so changing the menu re-prices
    the same crowd honestly — it can't keep a cheap-menu crowd at
    gourmet tickets."""
    state.demand_shock = rng.uniform(0.85, 1.15)
    for s in state.shops:
        s.legit_revenue_today = 0
        recompute_demand(state, s)


def recompute_demand(state: State, shop) -> None:
    """Recompute one address's order book from current policy and
    today's shock. Called whenever pricing or hours change during the
    morning."""
    dk = shop.district
    dspec = data.DISTRICTS[dk]

    base = 55 * dspec["traffic"]
    rep_f = 0.4 + shop.reputation / 100 * 1.2
    price_f = {"cheap": 1.25, "standard": 1.0, "gourmet": 0.75}[shop.price]
    late_f = 1.2 if "late_license" in shop.upgrades else 1.0
    coupon_f = 0.8 if shop.coupon_days > 0 else 1.0
    ev_f = market.event_mult(state, dk, "traffic")
    # An advertising campaign lifts the order book while it runs
    # (Straight Path only, rev. 9 item 8). The 1.0 multiplicand is
    # exact in IEEE, so the flag-off arithmetic is bit-identical.
    ad_f = (straight.AD_DEMAND_MULT
            if state.branch == "straight" and state.branch_state is not None
            and state.branch_state.ad_days_left > 0 else 1.0)
    shop.demand_today = int(base * rep_f * price_f * late_f * coupon_f * ev_f
                            * ad_f * state.demand_shock)
    shop.delivery_pool = int(shop.demand_today * DELIVERY_SHARE)


def simulate_shift(state: State, shop, route_legit: int,
                   rng: random.Random) -> dict:
    """One day of honest counter business at ONE address. Route
    deliveries were part of today's demand AND today's oven time: the
    kitchen bakes every pizza, so delivery production comes out of the
    same capacity."""
    demand = max(0, shop.demand_today - route_legit)
    capacity = max(0, shop.kitchen_cap - route_legit)
    orders = min(demand, capacity, shop.ingredients)
    lost = demand - orders
    shop.ingredients -= orders

    ticket = data.TICKET_PRICE[shop.price]
    revenue = orders * ticket
    state.clean += revenue
    shop.legit_revenue_today += revenue

    # Reputation drifts with what's ACTUALLY in the pantry vs. what the
    # menu charges for — cheap stock at gourmet prices is a short con.
    skill = cooks_skill(state, shop)
    q_score = {"cheap": 3, "standard": 5, "gourmet": 8}[shop.pantry_quality] \
        + skill / 2
    expect = {"cheap": 5, "standard": 7, "gourmet": 10}[shop.price]
    drift = max(-5.0, (q_score - expect) * 0.8 - (lost / max(demand, 1)) * 6)
    shop.reputation = max(0.0, min(100.0, shop.reputation + drift))

    # A food critic event lands squarely on today's kitchen.
    critic = any(e.spec.get("critic") for e in state.events)
    critic_line = None
    if critic and rng.random() < 0.5:
        if q_score >= 8:
            shop.reputation = min(100.0, shop.reputation + 12)
            critic_line = "The Ledger's critic praises your crust. Lines tomorrow."
        else:
            shop.reputation = max(0.0, shop.reputation - 10)
            critic_line = "The Ledger's critic calls your pie 'a cardboard apology.'"

    if "late_license" in shop.upgrades:
        state.add_heat(shop.district, 1.5)  # 2 a.m. crowd, neighbor complaints
    if "guard" in shop.upgrades:
        state.add_heat(shop.district, 0.5)  # why the armed man at a pizzeria?

    return {
        "demand": demand, "orders": orders, "lost": lost,
        "revenue": revenue, "critic_line": critic_line,
    }


def believable_ceiling(state: State, shop, todays_legit: int) -> int:
    """Max dirty cash ONE address's books can absorb without inventing
    evidence. `books` is bought per address and helps only the address
    that has it."""
    factor = data.LAUNDER_FACTOR + (0.75 if "books" in shop.upgrades else 0.0)
    return int(todays_legit * factor)


def total_believable_ceiling(state: State) -> int:
    """THE nightly laundering allowance: the SUM of every open
    address's ceiling, each computed from its own honest till and its
    own upgrades (design rev. 22 item 8). Two believable-revenue
    ceilings help launder — as arithmetic, not as prose — and the
    ceiling still grows only as fast as real trade does."""
    return sum(believable_ceiling(state, s, s.legit_revenue_today)
               for s in state.shops)
