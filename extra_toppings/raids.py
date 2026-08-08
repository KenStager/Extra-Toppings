"""Raids: short room-by-room tactical jobs on real floor plans.

The same layout grammar drives your raids on rivals and theirs on you.
Violence works, and always costs more than it looks like it costs.
"""

import random

from . import data
from .models import State
from .ui import Console, money


def plan_raid(state: State, con: Console, rng: random.Random,
              reserved: list | None = None,
              wagon_free: bool = True) -> dict | None:
    """`reserved` employees (tonight's driver) already have a job. If the
    wagon runs a route tonight, the crew hauls what duffel bags hold."""
    if not wagon_free:
        con.say("  The wagon is out on tonight's route — whatever the crew "
                "takes, they carry on foot.")
    targets = [k for k, r in state.rivals.items() if r.alive]
    if not targets:
        con.say("  There's nobody left worth robbing.")
        return None
    reserved = reserved or []
    crew = [e for e in state.crew() if e not in reserved]
    if not crew:
        con.say("  A raid needs read-in crew. Right now the only person you trust is you.")
        return None

    if state.raids_led >= 1:
        premium = min(8.0, 1.5 * state.raids_led)
        con.say(f"  The Ledger has counted {state.raids_led} unsolved "
                f"burglar{'y' if state.raids_led == 1 else 'ies'} this month. "
                f"Another success adds {premium:g} Case to the pattern.")
    t_labels = [f"{data.RIVALS[k]['label']} "
                f"(strength {state.rivals[k].strength:.0f}, "
                f"security {_security_word(state.rivals[k].alertness)})"
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
    # §2.1 same-night telegraph: a raid runs before the night's settling,
    # so its evidence (pattern premium, gunfire, bodies, witnesses) can
    # cross a Case gate hours before a payoff the same night. What it
    # books depends on choices made mid-job, so while payoff is in reach
    # the warning is unconditional — a printed line only; the job can
    # still be replanned or scrapped from the morning menu. The plan
    # remembers whether it warned: service revenue can put payoff in
    # reach after planning, and night() rechecks once before the job.
    warned = state.payoff_in_reach()
    if warned:
        con.say("  With the debt this close to settled, remember: whatever "
                "tonight leaves behind goes into the file tomorrow's table "
                "reads.")
    return {"rival": rival_key, "objective": objective, "team": team,
            "armed": armed, "table_warned": warned}


def _security_word(alertness: float) -> str:
    if alertness >= 7:
        return "fortress"
    if alertness >= 4:
        return "hardened"
    if alertness >= 2:
        return "wary"
    return "sleepy"


def run_raid(state: State, plan: dict, con: Console, rng: random.Random) -> None:
    rival = state.rivals[plan["rival"]]
    rspec = data.RIVALS[plan["rival"]]
    obj = data.RAID_OBJECTIVES[plan["objective"]]
    layout = data.RAID_LAYOUTS[obj["layout"]]
    team = plan["team"]
    guard_skill = 3 + rival.strength / 20 + rival.alertness * 0.3
    if rival.alertness >= 4:
        con.say("  New cameras. New locks. They've been expecting somebody.")

    con.header(f"NIGHT JOB — {obj['label']} at {rspec['short']}'s {layout['label']}")
    noise = 0.0
    aborted = False
    for i, room in enumerate(layout["rooms"]):
        con.say(f"  [{i+1}/{len(layout['rooms'])}] The {room['name']}.")
        guard_here = rng.random() < room["guard"] * (0.6 + rival.strength / 150) \
            * (1 + rival.alertness * 0.08) + noise * 0.3
        if guard_here:
            choice = con.menu(
                f"A guard. Noise so far: {'quiet' if noise < .3 else 'too much'}.",
                ["Slip past (best nerve)", "Take him down quietly",
                 "Go loud" if plan["armed"] else "Rush him", "Abort the job"])
            best_nerve = max(e.nerve for e in team)
            if choice == 0:
                if rng.random() < 0.25 + best_nerve * 0.06 - noise * 0.3 \
                        - rival.alertness * 0.04:
                    con.say("  He lights a cigarette and never turns around.")
                else:
                    noise += room["noise"]
                    _scuffle(state, team, guard_skill, con, rng, loud=False)
            elif choice == 1:
                if rng.random() < 0.35 + best_nerve * 0.05 \
                        - rival.alertness * 0.04:
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
        # Too loud with rooms still ahead = a failed extraction: the crew
        # never reaches the prize. Crossing the threshold in the FINAL room
        # is different — the job is done, just not quietly (clean_exit
        # False prices that below).
        if noise >= 1.0 and i < len(layout["rooms"]) - 1:
            con.say("  Lights snap on across the street. Time's up.")
            aborted = True
            break

    if aborted or not team:
        state.add_heat(rspec["home"], 8)
        rival.relation -= 10
        rival.alertness = min(10.0, rival.alertness + 1.0)
        rival.last_raided_day = state.day
        con.say("  You got out with nothing but your skins.")
        con.say("  By morning their guards walk in pairs.")
        return

    _payoff(state, plan, rival, rspec, con, rng, noise < 1.0, team)
    # Even a ghost leaves a pattern: the same handwriting, night after night.
    if state.raids_led >= 1:
        premium = min(8.0, 1.5 * state.raids_led)
        state.add_case(premium, "a pattern of night jobs in the same handwriting",
                       kind="pattern")
        con.say(f"  Somewhere downtown, tonight's job is pinned beside the "
                f"others. The pattern is starting to look like handwriting. "
                f"(Case +{premium:g})")
    state.raids_led += 1
    rival.alertness = min(10.0, rival.alertness + 2.0)
    rival.last_raided_day = state.day


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
            rng: random.Random, clean_exit: bool, team: list) -> None:
    objective = plan["objective"]
    if objective == "steal_stock":
        # Whoever is still standing carries the haul — with the wagon if
        # it's home tonight, in duffel bags if not.
        carry_bulk = (8 if plan.get("wagon_free", True) else 4) * len(team)
        if len(team) < len(plan["team"]):
            con.say("  Fewer hands make lighter hauls.")
        thin = max(0.3, 1.0 - rival.alertness * 0.07)   # alert targets stock less
        haul: dict = {}
        # Grab the expensive shelves first — which is exactly what an
        # alerted target has already locked down hardest.
        for g in ("hot_honey", "mushrooms", "oregano"):
            want = int(rng.randint(4, 10 + int(rival.strength / 10)) * thin)
            bulk = data.GOODS[g]["bulk"]
            take = min(want, carry_bulk // bulk)
            if take > 0:
                haul[g] = take
                carry_bulk -= take * bulk
        # Stolen goods still need somewhere to live: shop stash, then the
        # warehouse if rented — anything past that stays in their alley.
        left_behind = 0
        kept: dict = {}
        for g, u in haul.items():
            bulk = data.GOODS[g]["bulk"]
            room = max(0, state.shop.stash_cap
                       - state.stash_bulk(state.shop_stash)) // bulk
            to_shop = min(u, room)
            if to_shop:
                state.shop_stash[g] = state.shop_stash.get(g, 0) + to_shop
            rest = u - to_shop
            if rest and state.warehouse is not None:
                wh_room = max(0, data.WAREHOUSE_CAP
                              - state.stash_bulk(state.warehouse)) // bulk
                to_wh = min(rest, wh_room)
                if to_wh:
                    state.warehouse[g] = state.warehouse.get(g, 0) + to_wh
                rest -= to_wh
            left_behind += rest
            if u - rest:
                kept[g] = u - rest
        rival.strength -= 12
        rival.relation -= 25
        if kept:
            got = ", ".join(f"{u}x {data.GOODS[g]['label']}" for g, u in kept.items())
            con.say(f"  You take what hands and storage can hold: {got}.")
        else:
            con.say("  The cage is thin and your arms are full of nothing.")
        if left_behind:
            con.say(f"  {left_behind} units stay behind — nowhere to put them.")
        con.say("  Their corner boys will be dry for a week — prices will feel it.")
        for g in kept:
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
                  rng: random.Random) -> bool:
    """A telegraphed rival raid arrives at your shop tonight. Returns
    whether a raid actually LANDED (paid tribute averts it) — escrow
    counts a landed raid as a repricing incident (§2.4.4)."""
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
        return False

    if choice == 1:
        # The wagon holds a wagonload. Anything past that stays — and is found.
        con.say("  The wagon leaves at midnight, riding low. They break in at two.")
        overflow = state.stash_bulk(state.shop_stash) - data.VEHICLE_CARGO
        lost_units = 0
        if overflow > 0:
            for g in sorted(state.shop_stash,
                            key=lambda g: -data.GOODS[g]["bulk"]):
                while overflow > 0 and state.shop_stash.get(g, 0) > 0:
                    state.shop_stash[g] -= 1
                    overflow -= data.GOODS[g]["bulk"]
                    lost_units += 1
        state.shop.damage_days = 2
        state.shop.reputation -= 8
        if lost_units:
            con.say(f"  A wagon holds a wagonload. They find the other "
                    f"{lost_units} units in the walk-in and take them.")
        else:
            con.say("  They wreck the front and find an empty walk-in. "
                    "Message received — both ways.")
        rival.relation -= 5
        rival.raid_warning = 0
        return True

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
    return True
