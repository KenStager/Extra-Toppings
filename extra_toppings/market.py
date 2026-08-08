"""Contraband market: daily prices, city events, rumors, oversell depression."""

import random

from . import data
from .models import ActiveEvent, State


def event_price_mult(state: State, dk: str, good: str) -> float:
    m = 1.0
    for ev in state.events:
        spec = ev.spec
        if spec.get("district") not in (None, dk):
            continue
        m *= spec.get("price", {}).get(good, 1.0)
    return m


def event_mult(state: State, dk: str, field: str) -> float:
    m = 1.0
    for ev in state.events:
        if ev.spec.get("district") in (None, dk):
            m *= ev.spec.get(field, 1.0)
    return m


def roll_prices(state: State, rng: random.Random) -> None:
    """New day, new numbers. Yesterday's heavy selling depresses today's price."""
    for dk, dspec in data.DISTRICTS.items():
        dist = state.districts[dk]
        row = {}
        for g, gspec in data.GOODS.items():
            base = gspec["base"] * dspec.get("good_bias", {}).get(g, 1.0)
            noise = 1.0 + rng.uniform(-gspec["volatility"], gspec["volatility"])
            glut = 1.0 - min(0.4, dist.sold_yesterday.get(g, 0) * 0.03)
            price = base * noise * event_price_mult(state, dk, g) * glut
            row[g] = max(5, int(price))
        state.prices[dk] = row
        dist.sold_yesterday = {}
        dist.known_price_age += 1
    state.districts[data.HOME_DISTRICT].known_price_age = 0


def draw_events(state: State, rng: random.Random) -> None:
    for ev in state.events:
        ev.days_left -= 1
    state.events = [e for e in state.events if e.days_left > 0]
    state.news = []
    if rng.random() < 0.65:
        active_ids = {e.spec["id"] for e in state.events}
        candidates = [e for e in data.EVENTS if e["id"] not in active_ids]
        if candidates:
            spec = rng.choice(candidates)
            state.events.append(ActiveEvent(spec=spec, days_left=spec["days"]))
            state.news.append(spec["news"])
            for dk in data.DISTRICTS:
                if spec.get("district") in (None, dk):
                    state.add_heat(dk, spec.get("patrol", 0))
            spill = spec.get("spillover")
            if spill:
                state.news.append(
                    f"Word is the trade just moved to {data.DISTRICTS[spill]['label']}."
                )


def rumor_sheet(state: State, rng: random.Random) -> list[str]:
    """Secondhand prices. Accuracy improves with a 'connected' employee on staff."""
    connected = any(e.trait == "connected" and e.available for e in state.hired())
    fuzz = 0.15 if connected else 0.4
    lines = []
    for dk, dspec in data.DISTRICTS.items():
        if dk == data.HOME_DISTRICT:
            continue
        g = rng.choice(list(data.GOODS))
        true = state.prices[dk][g]
        heard = int(true * (1 + rng.uniform(-fuzz, fuzz)))
        src = "a regular" if not connected else "Lena's contact"
        lines.append(
            f"{src} says {data.GOODS[g]['label']} moves around ${heard} "
            f"in {dspec['label']}"
        )
    return lines


def record_sales(state: State, dk: str, good: str, units: int) -> None:
    d = state.districts[dk].sold_yesterday
    d[good] = d.get(good, 0) + units
