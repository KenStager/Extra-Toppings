"""Raids: short room-by-room tactical jobs on real floor plans.

The same layout grammar drives your raids on rivals and theirs on you.
Violence works, and always costs more than it looks like it costs.
"""

import random

from . import data
from .models import State
from .ui import Console, money


def plan_raid(state: State, con: Console, rng: random.Random,
              reserved: list | None = None) -> dict | None:
    """`reserved` employees (tonight's driver) already have a job."""
    targets = [k for k, r in state.rivals.items() if r.alive]
    if not targets:
        con.say("  There's nobody left worth robbing.")
        return None
    reserved = reserved or []
    crew = [e for e in state.crew() if e not in reserved]
    if not crew:
        con.say("  A raid needs read-in crew. Right now the only person you trust is you.")
        return None

    t_labels = [f"{data.RIVALS[k]['label']} (strength {state.rivals[k].strength:.0f})"
                for k in targets] + ["Never mind"]
    pick = con.menu("Hit whom?", t_labels)
    if pick == len(targets):
        return None
    rival_key = targets[pick]

    obj_keys = list(data.RAID_OBJECTIVES)
    o_labels = [f"{data.RAID_OBJECTIVES[k]['label']} — {data.RAID_OBJECTIVES[k]['desc']}"
                for k in obj_keys] + ["Never mind"]
    opick = con.menu("The job:", o_labels)
    if opick == len(obj_keys):
        return None
    objective = obj_keys[opick]

    team: list = []
    pool = list(crew)
    while pool and len(team) < 3:
        names = [f"{e.name} (nerve {e.nerve}, {e.trait})" for e in pool] + ["Enough"]
        c = con.menu(f"Crew ({len(team)} picked, max 3):", names)
        if c == len(pool):
            break
        team.append(pool.pop(c))
    if not team:
        con.say("  No crew, no job.")
        return None

    armed = con.confirm("Go in armed? (Safer in a fight. Gunfire changes the city.)")
    return {"rival": rival_key, "objective": objective, "team": team, "armed": armed}


def run_raid(state: State, plan: dict, con: Console, rng: random.Random) -> None:
    rival = state.rivals[plan["rival"]]
    rspec = data.RIVALS[plan["rival"]]
    obj = data.RAID_OBJECTIVES[plan["objective"]]
    layout = data.RAID_LAYOUTS[obj["layout"]]
    team = plan["team"]
    guard_skill = 3 + rival.strength / 20

    con.header(f"NIGHT JOB — {obj['label']} at {rspec['short']}'s {layout['label']}")
    noise = 0.0
    aborted = False
    for i, room in enumerate(layout["rooms"]):
        con.say(f"  [{i+1}/{len(layout['rooms'])}] The {room['name']}.")
        guard_here = rng.random() < room["guard"] * (0.6 + rival.strength / 150) + noise * 0.3
        if guard_here:
            choice = con.menu(
                f"A guard. Noise so far: {'quiet' if noise < .3 else 'too much'}.",
                ["Slip past (best nerve)", "Take him down quietly",
                 "Go loud" if plan["armed"] else "Rush him", "Abort the job"])
            best_nerve = max(e.nerve for e in team)
            if choice == 0:
                if rng.random() < 0.25 + best_nerve * 0.06 - noise * 0.3:
                    con.say("  He lights a cigarette and never turns around.")
                else:
                    noise += room["noise"]
                    _scuffle(state, team, guard_skill, con, rng, loud=False)
            elif choice == 1:
                if rng.random() < 0.35 + best_nerve * 0.05:
                    con.say("  A tap behind the ear. He'll wake up embarrassed.")
                    noise += 0.1
                else:
                    noise += room["noise"]
                    _scuffle(state, team, guard_skill, con, rng, loud=False)
            elif choice == 2:
                _scuffle(state, team, guard_skill, con, rng, loud=plan["armed"])
                noise += 0.5 if plan["armed"] else room["noise"]
            else:
                aborted = True
                break
        else:
            con.say("  Empty. Keep moving.")
        team = [e for e in team if e.injured_days == 0]
        if not team:
            con.say("  Everyone's down or dragging someone who is. The job collapses.")
            aborted = True
            break
        if noise >= 1.0:
            con.say("  Lights snap on across the street. Time's up.")
            break

    if aborted or not team:
        state.add_heat(rspec["home"], 8)
        rival.relation -= 10
        con.say("  You got out with nothing but your skins.")
        return

    _payoff(state, plan, rival, rspec, con, rng, clean_exit=noise < 1.0)
    state.raids_led += 1


def _scuffle(state: State, team: list, guard_skill: float, con: Console,
             rng: random.Random, loud: bool) -> None:
    ours = max(e.nerve for e in team) + rng.uniform(0, 4) + (2 if loud else 0)
    theirs = guard_skill + rng.uniform(0, 4)
    if ours >= theirs:
        con.say("  It's short and ugly and it goes your way.")
        if loud and rng.random() < 0.3:
            state.kills += 1
            state.add_case(10, "a body left behind on a night job")
            con.say("  ...he isn't getting up. That will follow you.")
    else:
        victim = rng.choice(team)
        victim.injured_days = rng.randint(2, 4)
        con.say(f"  {victim.name} takes a bad one — out {victim.injured_days} days.")
    if loud:
        for dk in data.DISTRICTS:
            state.add_heat(dk, 6)
        state.add_case(4, "gunfire reported during a burglary")


def _payoff(state: State, plan: dict, rival, rspec, con: Console,
            rng: random.Random, clean_exit: bool) -> None:
    objective = plan["objective"]
    if objective == "steal_stock":
        haul = {}
        for g in ("oregano", "mushrooms", "hot_honey"):
            units = rng.randint(4, 10 + int(rival.strength / 10))
            haul[g] = units
            state.shop_stash[g] = state.shop_stash.get(g, 0) + units
        rival.strength -= 12
        rival.relation -= 25
        got = ", ".join(f"{u}x {data.GOODS[g]['label']}" for g, u in haul.items())
        con.say(f"  The cage is full. You take: {got}.")
        con.say("  Their corner boys will be dry for a week — prices will feel it.")
        for g in haul:
            # A shortage: their unsold supply props up prices tomorrow.
            state.districts[rspec["home"]].sold_yesterday[g] = -8
    elif objective == "ledger":
        rival.ledger_stolen = True
        rival.strength -= 8
        rival.relation -= 15
        con.say("  Forty pages of names, dates and numbers on film.")
        con.say("  Leverage now — or a gift to a prosecutor later.")
    else:  # sabotage
        rival.ovens_wrecked_days = 4
        rival.strength -= 10
        rival.relation -= 20
        con.say("  Thermostats smashed, gas lines capped, deck stones cracked.")
        con.say(f"  {rspec['short']}'s shop serves nothing for days — no cover for his routes.")

    if not clean_exit:
        state.add_case(5, "witnesses describe your crew leaving the scene")
    state.add_heat(rspec["home"], 12)


# ── defense ───────────────────────────────────────────────────────

def incoming_raid(state: State, rival_key: str, con: Console,
                  rng: random.Random) -> None:
    """A telegraphed rival raid arrives at your shop tonight."""
    rival = state.rivals[rival_key]
    rspec = data.RIVALS[rival_key]
    con.header(f"THEY'RE COMING — {rspec['short']}'s crew hits your shop tonight")

    options = ["Defend the shop (your crew's nerve)",
               "Empty the stash into the wagon and let them find crumbs",
               f"Pay tribute ({money(rival.tribute_demanded or 1500)} dirty)"]
    has_guard = "guard" in state.shop.upgrades
    if has_guard:
        options[0] += " — night security helps"
    choice = con.menu("The unfamiliar cars are circling. Your move:", options)

    tribute = rival.tribute_demanded or 1500
    if choice == 2 and state.dirty >= tribute:
        state.dirty -= tribute
        rival.relation += 15
        rival.raid_warning = 0
        con.say("  Money changes hands in a parking lot. The cars drive away.")
        con.say("  Everyone on your payroll knows you paid.")
        for e in state.hired():
            e.morale -= 1
        return

    if choice == 1:
        # Stash survives; the shop takes the beating.
        con.say("  The wagon leaves at midnight, riding low. They break in at two.")
        state.shop.damage_days = 2
        state.shop.reputation -= 8
        con.say("  They wreck the front and find an empty walk-in. Message received — both ways.")
        rival.relation -= 5
        rival.raid_warning = 0
        return

    # Fight.
    defenders = state.crew()
    strength = max([e.nerve for e in defenders], default=3) + (4 if has_guard else 0)
    attack = 4 + rival.strength / 12 + rng.uniform(0, 4)
    if strength + rng.uniform(0, 4) >= attack:
        con.say("  It's loud and brief. They leave one man's jacket and all their nerve.")
        rival.strength -= 10
        rival.relation -= 20
        state.add_heat(data.HOME_DISTRICT, 15)
        state.add_case(3, "a brawl at your shop made the police blotter")
    else:
        lost_units = 0
        for g in list(state.shop_stash):
            take = state.shop_stash[g] // 2
            state.shop_stash[g] -= take
            lost_units += take
        grabbed = min(state.dirty, rng.randint(500, 1500))
        state.dirty -= grabbed
        state.shop.damage_days = 3
        state.shop.reputation -= 12
        if defenders and rng.random() < 0.5:
            v = rng.choice(defenders)
            v.injured_days = rng.randint(2, 5)
            con.say(f"  {v.name} is hurt — out {v.injured_days} days.")
        con.say(f"  They take {lost_units} units and {money(grabbed)} from the register,")
        con.say("  and leave the ovens in pieces. The shop limps for days.")
        state.add_heat(data.HOME_DISTRICT, 20)
        state.add_case(4, "an armed robbery at your address raised questions")
    rival.raid_warning = 0
