"""The legitimate pizzeria: demand, quality, revenue, reputation."""

import random

from . import data, market
from .models import State


def cooks_skill(state: State) -> int:
    cooks = [e for e in state.hired() if e.available and e.role == "cook"]
    return max([e.food for e in cooks], default=2)


def simulate_shift(state: State, rng: random.Random) -> dict:
    """One day of honest business. Returns a report dict; mutates state."""
    shop = state.shop
    dk = data.HOME_DISTRICT
    dspec = data.DISTRICTS[dk]

    if shop.damage_days:
        shop.damage_days -= 1

    base = 55 * dspec["traffic"]
    rep_f = 0.4 + state.shop.reputation / 100 * 1.2
    price_f = {"cheap": 1.25, "standard": 1.0, "gourmet": 0.75}[shop.price]
    late_f = 1.2 if "late_license" in shop.upgrades else 1.0
    ev_f = market.event_mult(state, dk, "traffic")
    demand = int(base * rep_f * price_f * late_f * ev_f * rng.uniform(0.85, 1.15))

    capacity = shop.kitchen_cap
    orders = min(demand, capacity, shop.ingredients)
    lost = demand - orders
    shop.ingredients -= orders

    ticket = data.TICKET_PRICE[shop.price]
    revenue = orders * ticket
    state.clean += revenue

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
        state.add_heat(dk, 1.5)   # neighbors complain about the 2 a.m. crowd
    if "guard" in shop.upgrades:
        state.add_heat(dk, 0.5)   # why does a pizzeria need armed security?

    return {
        "demand": demand, "orders": orders, "lost": lost,
        "revenue": revenue, "critic_line": critic_line,
    }


def believable_ceiling(state: State, todays_legit: int) -> int:
    """Max dirty cash the books can absorb without inventing evidence."""
    factor = data.LAUNDER_FACTOR + (0.75 if "books" in state.shop.upgrades else 0.0)
    return int(todays_legit * factor)
