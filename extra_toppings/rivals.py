"""Rival syndicates: two families, two strategies, long memories."""

import random

from . import data
from .models import State
from .ui import Console, money


def rival_phase(state: State, con: Console, rng: random.Random) -> None:
    """Each rival takes one action a night, scaled to how much they hate you."""
    for key, rival in state.rivals.items():
        if not rival.alive:
            continue
        spec = data.RIVALS[key]

        if rival.ovens_wrecked_days:
            rival.ovens_wrecked_days -= 1
            rival.strength = max(1, rival.strength - 2)
        # Guards get bored again, slowly — but not on a night you hit them.
        if rival.last_raided_day != state.day:
            rival.alertness = max(0.0, rival.alertness - 0.34)

        # A telegraphed raid counts down; landing is handled by the night phase.
        if rival.raid_warning > 1:
            rival.raid_warning -= 1
            con.bullet(f"{spec['short']}'s cars rolled past the shop again. Twice.")
            continue
        if rival.raid_warning == 1:
            continue   # tonight — night phase resolves it

        grudge = max(0.0, -rival.relation) / 100      # 0..1
        act_chance = spec["aggression"] * 0.5 + grudge * 0.6
        if rng.random() > act_chance:
            if rival.relation > 20 and rng.random() < 0.2:
                con.bullet(f"{spec['short']} sends over a tray of cannoli. A truce holds.")
            continue

        roll = rng.random()
        violent = spec["violence"] * (0.5 + grudge)
        if roll < 0.30:
            _price_war(state, key, spec, con)
        elif roll < 0.50:
            _poach(state, rival, spec, con, rng)
        elif roll < 0.68:
            _extort(state, rival, spec, con, rng)
        elif roll < 0.68 + violent * 0.25:
            rival.raid_warning = rng.randint(2, 3)
            con.bullet(f"Unfamiliar cars idle across from the shop. {spec['short']}'s "
                       f"plates. Something is coming.")
        else:
            _plant(state, rival, spec, con, rng)


def _price_war(state: State, key: str, spec: dict, con: Console) -> None:
    # Coupons steal customers for a while; they don't make your pizza worse.
    con.bullet(f"{spec['short']} papers the neighborhood with two-for-one coupons. "
               f"Expect thin order books for a few days.")
    state.shop.coupon_days = max(state.shop.coupon_days, 3)


def _poach(state: State, rival, spec: dict, con: Console, rng: random.Random) -> None:
    targets = [e for e in state.hired() if e.available and e.loyalty <= 6]
    if not targets:
        return
    e = rng.choice(targets)
    resist = e.loyalty + e.morale
    if e.trait == "greedy":
        resist -= 3
    if resist + rng.uniform(0, 6) < 12:
        e.hired = False
        con.bullet(f"{e.name} took {spec['short']}'s offer and didn't finish the shift.")
        if e.aware:
            state.add_case(8, f"{e.name} left for a rival knowing everything",
                           kind="witness", source=e.key)
            con.bullet(f"...and {e.name} knew things. That's a problem now.")
    else:
        e.morale -= 1
        con.bullet(f"{spec['short']} made {e.name} an offer. It was declined — this time.")


def _extort(state: State, rival, spec: dict, con: Console, rng: random.Random) -> None:
    demand = rng.randrange(600, 1400, 100)
    rival.tribute_demanded = demand
    con.bullet(f"A note under the door: {money(demand)} a week 'keeps the ovens safe.' "
               f"— {spec['short']}")


def _plant(state: State, rival, spec: dict, con: Console, rng: random.Random) -> None:
    con.bullet("An anonymous tip sends a patrol crawling past your block all night.")
    state.add_heat(data.HOME_DISTRICT, 12)
    if rng.random() < 0.3:
        state.add_case(4, "an informant's tip put your shop in a file",
                       kind="witness")


def negotiate(state: State, con: Console, rng: random.Random) -> None:
    live = [k for k, r in state.rivals.items() if r.alive]
    if not live:
        con.say("  The city's other operators are gone. There's no one to call.")
        return
    labels = [f"{data.RIVALS[k]['label']} (relation {state.rivals[k].relation:+.0f})"
              for k in live] + ["Back"]
    pick = con.menu("Reach out to whom?", labels)
    if pick == len(live):
        return
    key = live[pick]
    rival = state.rivals[key]
    spec = data.RIVALS[key]

    opts = [f"Send a peace offering ({money(1000)} dirty)",
            "Propose a truce (works best from strength)"]
    if rival.ledger_stolen:
        opts.append("Lean on them with the ledger")
    opts.append("Back")
    c = con.menu(f"{spec['short']}: {spec['style']}", opts)

    if c == 0 and state.dirty >= 1000:
        state.dirty -= 1000
        rival.relation += 12
        con.say(f"  {spec['short']} accepts the envelope. The temperature drops a degree.")
    elif c == 1:
        odds = 0.3 + (state.rivals[key].strength < 40) * 0.3 + max(0, rival.relation) / 200
        if rng.random() < odds:
            rival.relation = max(rival.relation, 25)
            rival.tribute_demanded = 0
            con.say("  Handshakes over espresso. Your trucks stay out of each other's mirrors.")
        else:
            rival.relation -= 5
            con.say(f"  {spec['short']} laughs. 'Come back when you own something.'")
    elif rival.ledger_stolen and c == 2:
        rival.strength -= 15
        rival.relation -= 10
        rival.tribute_demanded = 0
        rival.ledger_stolen = False   # leverage used is leverage gone
        state.dirty += 2000
        con.say("  You read three names off page twelve. An envelope arrives by morning.")
        con.say(f"  +{money(2000)} dirty. {spec['short']} will not forget this — "
                f"and by next week those pages are worthless.")
