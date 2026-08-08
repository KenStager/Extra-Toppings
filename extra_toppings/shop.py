"""The legitimate pizzeria: demand, quality, revenue, reputation.

Demand is rolled each morning from an action-independent daily stream.
A slice of that demand wants delivery — and *only* those real orders can
serve as cover on a route. A hollow restaurant has nothing to hide behind.
"""

import random

from . import data, market
from .models import State


def cooks_skill(state: State) -> int:
    cooks = [e for e in state.hired() if e.available and e.role == "cook"]
    return max([e.food for e in cooks], default=2)


DELIVERY_SHARE = 0.35   # fraction of real demand that phones in a delivery


def roll_demand(state: State, rng: random.Random) -> None:
    """Morning: how many customers actually want your pizza today."""
    shop = state.shop
    dk = data.HOME_DISTRICT
    dspec = data.DISTRICTS[dk]

    base = 55 * dspec["traffic"]
    rep_f = 0.4 + shop.reputation / 100 * 1.2
    price_f = {"cheap": 1.25, "standard": 1.0, "gourmet": 0.75}[shop.price]
    late_f = 1.2 if "late_license" in shop.upgrades else 1.0
    coupon_f = 0.8 if shop.coupon_days > 0 else 1.0
    ev_f = market.event_mult(state, dk, "traffic")
    state.demand_today = int(base * rep_f * price_f * late_f * coupon_f * ev_f
                             * rng.uniform(0.85, 1.15))
    state.delivery_pool = int(state.demand_today * DELIVERY_SHARE)
    state.legit_revenue_today = 0


def simulate_shift(state: State, route_legit: int, rng: random.Random) -> dict:
    """One day of honest counter business. Route deliveries were part of
    today's demand, so they're subtracted before the dining room fills."""
    shop = state.shop

    if shop.damage_days:
        shop.damage_days -= 1
    if shop.coupon_days:
        shop.coupon_days -= 1

    demand = max(0, state.demand_today - route_legit)
    capacity = shop.kitchen_cap
    orders = min(demand, capacity, shop.ingredients)
    lost = demand - orders
    shop.ingredients -= orders

    ticket = data.TICKET_PRICE[shop.price]
    revenue = orders * ticket
    state.clean += revenue
    state.legit_revenue_today += revenue

    # Reputation drifts with quality vs. price expectations and lost orders.
    skill = cooks_skill(state)
    q_score = {"cheap": 3, "standard": 5, "gourmet": 8}[shop.quality] + skill / 2
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
        state.add_heat(data.HOME_DISTRICT, 1.5)  # 2 a.m. crowd, neighbor complaints
    if "guard" in shop.upgrades:
        state.add_heat(data.HOME_DISTRICT, 0.5)  # why the armed man at a pizzeria?

    return {
        "demand": demand, "orders": orders, "lost": lost,
        "revenue": revenue, "critic_line": critic_line,
    }


def believable_ceiling(state: State, todays_legit: int) -> int:
    """Max dirty cash the books can absorb without inventing evidence."""
    factor = data.LAUNDER_FACTOR + (0.75 if "books" in state.shop.upgrades else 0.0)
    return int(todays_legit * factor)
