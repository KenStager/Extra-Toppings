"""Contraband market: daily prices, city events, rumors, oversell depression."""

import random
from dataclasses import dataclass

from . import data, models, war
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


@dataclass(frozen=True)
class RouteMarket:
    """THE territorial route-market view (rev. 15 item 5): every
    covert-demand factor for a district composes HERE — the base
    underground, the event multiplier, the capture bonus, the heat
    policy, and the corner terms — and every consumer reads this one
    immutable view: the market display and route labels, automated
    and interactive capacity (the drops count), per-stop demand, and
    the corner damage. Flag-off exactness: the legacy expressions are
    computed verbatim inside the methods, in their original operation
    order, and the war adjustments are +0.0 / ×1.0 by construction
    (the P0 bit-identity scar's rule)."""
    district: str
    base: float                  # the district's underground factor
    event: float                 # today's event multiplier
    bonus: float                 # capture bonus; 0.0 outside your turf
    heat: models.HeatPolicy
    owner: str | None            # the turf's owner, dead or alive
    corner_rate: float           # tonight's diversion per unit (0.0 =
    corner_cap: float            # no live campaign on this turf)

    def drops(self, n_cargo: int) -> int:
        """Tonight's stop count — the capacity axis. Amber halves it
        exactly once, here and nowhere else (rev. 14 item 5)."""
        stops_base = (2 + 2 * n_cargo) * (self.base * self.event)
        stops_bonus = (2 + 2 * n_cargo) * self.bonus
        return max(2, int((stops_base + stops_bonus)
                          * self.heat.capacity_mult))

    def top_want(self) -> int:
        """Per-stop appetite — the demand axis; never capacity-halved."""
        return max(2, int(4 * self.base * self.event + 4 * self.bonus))

    @property
    def captured(self) -> bool:
        return self.bonus > 0.0


def route_market(state: State, dk: str) -> RouteMarket:
    dspec = data.DISTRICTS[dk]
    owner = dspec["rival"]
    heat = models.district_heat_policy(state, dk)
    corner_rate = corner_cap = 0.0
    if owner is not None and models.live_campaign(state, owner) is not None:
        outage = state.rivals[owner].ovens_wrecked_days > 0
        mult = war.OUTAGE_MULT if outage else 1
        corner_rate = war.CORNER_RATE * mult
        # Heat's consequence flows through the customer pool (rev. 16
        # item 7): an amber turf has half the divertible custom, so
        # the EFFECTIVE corner cap halves with the same capacity
        # multiplier that halves the stops — the -4/night cap can no
        # longer mask the burned neighborhood.
        corner_cap = war.CORNER_CAP * mult * heat.capacity_mult
    return RouteMarket(
        district=dk,
        base=dspec["underground"],
        event=event_mult(state, dk, "underground"),
        bonus=war.underground_bonus(state, dk),
        heat=heat,
        owner=owner,
        corner_rate=corner_rate, corner_cap=corner_cap)


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
