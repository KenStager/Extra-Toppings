"""Raids: short room-by-room tactical jobs on real floor plans.

The same layout grammar drives your raids on rivals and theirs on you.
Violence works, and always costs more than it looks like it costs.
"""

import random

from . import data, models, war
from .models import State
from .ui import Console, money


def plan_raid(state: State, con: Console, rng: random.Random,
              reserved: list | None = None,
              *, wagon: "models.PlannedWagon",
              home: "models.Shop") -> dict | None:
    """`reserved` employees (tonight's driver) already have a job. If the
    wagon runs a route tonight, the crew hauls what duffel bags hold.

    `wagon` arrives as ONE typed value (P4b.1a review) rather than a
    boolean plus loose prose: availability and its reason cannot be
    passed in contradicting each other, and the sentence below is
    rendered FROM the structured block instead of pasting a phrase
    into the middle of another sentence. It is REQUIRED and
    keyword-only — a default would be a synthetic identity, and a
    caller that skipped the authority would silently get one."""
    if not wagon.available:
        con.say(f"  {models.wagon_gone_line(wagon)} — whatever the crew "
                f"takes, they carry on foot.")
    targets = [k for k, r in state.rivals.items() if r.alive]
    if state.branch == "war":
        # One front at a time (rev. 14 item 9): outgoing jobs go to the
        # declared rival only — hitting the bystander is a two-front
        # mechanic, and it is not in this game.
        tk = war.target_key(state)
        if tk is None:
            con.say("  You're not at war with anyone tonight. Name the "
                    "next war before you send crowbars anywhere.")
            return None
        targets = [tk]
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
    while pool and len(team) < models.RAID_CREW_MAX:
        names = [f"{e.name} (nerve {e.nerve}, {e.trait})" for e in pool] + ["Enough"]
        c = con.menu(f"Crew ({len(team)} picked, "
                     f"max {models.RAID_CREW_MAX}):", names)
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
    # WHERE THE CREW COMES BACK TO, chosen by the caller (P4b.1a).
    home_key = home.key
    # WHICH wagon the crew would load, or an explicit None meaning
    # they go on foot (P4b.1a). Only a stock theft loads one at all
    # (rev. 26): ledger and sabotage jobs always walk, and they record
    # that rather than leaving the question unanswered.
    #
    # The candidate is the address's CLAIMABLE wagon, not tonight's
    # free one: a route planned this morning may be scrubbed before it
    # departs, and the crew then leaves in the wagon that came back.
    # Execution revalidates the key and decides; planning only names
    # the vehicle.
    riding = models.claimable_wagons(state, home_key)
    return {"rival": rival_key, "objective": objective, "team": team,
            "armed": armed, "table_warned": warned,
            "wagon_key": (riding[0] if objective == "steal_stock"
                          and riding else None),
            # Where the crew comes back to. Named at planning so the
            # haul cannot be unloaded somewhere nobody drove (design
            # rev. 22 item 5); with one address it is that address.
            "return_shop": home_key}


# The security word moved to models.security_word so the war board can
# read it without importing raids (raids imports war for the raid
# edge). Same function, one home; this name stays for its callers.
_security_word = models.security_word


def run_raid(state: State, plan: dict, con: Console, rng: random.Random) -> None:
    rival = state.rivals[plan["rival"]]
    rspec = data.RIVALS[plan["rival"]]
    obj = data.RAID_OBJECTIVES[plan["objective"]]
    layout = data.RAID_LAYOUTS[obj["layout"]]
    team = plan["team"]
    # The attempt ledger (rev. 18 item 3): the record is constructed
    # ONCE, after the outcome is known, and appended exactly once —
    # never a mutable dict edited in flight. Crew is the committed
    # crew; damage is the ACTUAL strength delta this job applied.
    committed_crew = len(team)
    strength_before_h = round(rival.strength * 100)
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
        models.adjust_relation(state, rival.key, -10)
        rival.alertness = min(10.0, rival.alertness + 1.0)
        rival.last_raided_day = state.day
        con.say("  You got out with nothing but your skins.")
        con.say("  By morning their guards walk in pairs.")
        state.raid_log.append(models.RaidAttemptRecord(
            day=state.day, rival=plan["rival"], outcome="failed",
            crew=committed_crew, damage_h=0))
        return

    _payoff(state, plan, rival, rspec, con, rng, noise < 1.0, team)
    state.raid_log.append(models.RaidAttemptRecord(
        day=state.day, rival=plan["rival"], outcome="succeeded",
        crew=committed_crew,
        damage_h=strength_before_h - round(rival.strength * 100)))
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
        # (THE placement authority, rev. 15 item 2 — the loop moved to
        # models.place_haul verbatim; salvage consumes the same one.)
        kept, left_behind = models.place_haul(
            state, haul, plan["return_shop"])
        models.apply_rival_damage(
            state, rival.key, "jobs",
            war.job_damage(state, rival.key, models.RAID_STOCK_STRENGTH))
        models.adjust_relation(state, rival.key, -25)
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
        models.apply_rival_damage(
            state, rival.key, "jobs",
            war.job_damage(state, rival.key, models.RAID_LEDGER_STRENGTH))
        models.adjust_relation(state, rival.key, -15)
        con.say("  Forty pages of names, dates and numbers on film.")
        con.say("  Leverage now — or a gift to a prosecutor later.")
    else:  # sabotage
        rival.ovens_wrecked_days = 4
        models.apply_rival_damage(
            state, rival.key, "jobs",
            war.job_damage(state, rival.key, models.RAID_SABOTAGE_STRENGTH))
        models.adjust_relation(state, rival.key, -20)
        con.say("  Thermostats smashed, gas lines capped, deck stones cracked.")
        con.say(f"  {rspec['short']}'s shop serves nothing for days — no cover for his routes.")

    if not clean_exit:
        state.add_case(5, "witnesses describe your crew leaving the scene")
    state.add_heat(rspec["home"], 12)
    if not rival.alive and models.vendetta_locked(state, rival.key):
        con.say(f"  And that's the job that finishes it — "
                f"{rspec['short']}'s organization is broken. The "
                f"district changes hands by morning.")


# ── defense ───────────────────────────────────────────────────────

from dataclasses import dataclass  # noqa: E402  (defense section header)


@dataclass(frozen=True)
class RaidResult:
    """The typed defense outcome (rev. 14 item 6): Burned Out must
    read the damage the shop carried BEFORE tonight's impact — a
    bare boolean plus mutation made every lost fight look 'already
    damaged' the moment the raid itself added damage.

      outcome         — "landed" / "repelled" / "averted"
      damage_before   — shop.damage_days immediately before impact
      damage_added    — what tonight's raid added
      attacker_damage — strength the defense dealt them (the fifth
                        channel books through the damage authority)
      wagon_taken     — the decoy loaded the wagon and drove it out,
                        so no later consumer tonight may have it
                        (design rev. 25 item 1)
    """
    outcome: str
    damage_before: int
    damage_added: int
    attacker_damage: float
    wagon_taken: bool = False

    @property
    def landed(self) -> bool:
        return self.outcome == "landed"


def incoming_raid(state: State, rival_key: str, con: Console,
                  rng: random.Random, *,
                  wagon: models.WagonAvailability | None = None
                  ) -> RaidResult:
    """A telegraphed rival raid arrives at your shop tonight. Returns
    the typed RaidResult (rev. 14 item 6). Escrow's incident semantics
    are unchanged from the merged behavior: any raid that ARRIVES —
    fought off or not — is a repricing incident, so escrow keys on
    outcome != "averted" (the old boolean's exact truth table); only
    Burned Out distinguishes "landed" from "repelled"."""
    rival = state.rivals[rival_key]
    rspec = data.RIVALS[rival_key]
    # The warning named an address when it went up, and reloading
    # cannot have changed it (design rev. 23 item 2). Every
    # consequence below lands on THAT shop — damage, the guard, the
    # stash they find, the reputation lost and the heat raised.
    if rival.warning is None:
        raise ValueError(f"{rival_key!r} arrives with no warning on "
                         f"the board")
    target = state.shop_by_key(rival.warning.shop_key)
    con.header(f"THEY'RE COMING — {rspec['short']}'s crew hits your shop tonight")

    damage_before = target.damage_days
    fatal_ground = state.branch == "war" and damage_before > 0
    # THE incoming-raid policy (rev. 15 item 1): a DECLARED rival's
    # raid offers no tribute at all — the declaration closed that door
    # forever, and money must not reopen it mid-raid. The bystander's
    # raid keeps the option; flag-off nothing changes.
    target_raid = models.vendetta_locked(state, rival_key)
    # The decoy needs a wagon that is actually here (design rev. 25
    # item 1). It stays ON the menu when it isn't — marked, with the
    # reason — because an option that silently vanishes teaches the
    # player nothing; picking it says why and asks again. Same shape
    # as the RED-district refusal in routes.plan_route.
    wagon = wagon if wagon is not None else models.WAGON_FREE
    decoy = "Empty the stash into the wagon and let them find crumbs"
    if not wagon.available:
        decoy += f" — unavailable, the wagon is {wagon.note}"
    options = ["Defend the shop (your crew's nerve)", decoy]
    if not target_raid:
        options.append(
            f"Pay tribute ({money(rival.tribute_demanded or 1500)} dirty)")
    has_guard = "guard" in target.upgrades
    if has_guard:
        options[0] += " — night security helps"
    if target_raid:
        con.say("  There is no envelope for this one. He isn't "
                "collecting — he's collecting on you.")
    if fatal_ground:
        # The explicit fatal-choice warning (rev. 14 item 6): Burned
        # Out is always a risk knowingly accepted (invariant 7).
        con.say("  The shop is already hurt. If they land tonight — a "
                "lost fight, or the decoy's break-in — there will be "
                "nothing left to reopen. The war comes home.")
        options[1] += " — the break-in ends the run"
    prompt = "The unfamiliar cars are circling. Your move:"
    choice = con.menu(prompt, options)
    if choice == 1 and not wagon.available:
        # Refused, then asked again WITHOUT it — bounded at two menus
        # on purpose. A re-prompt loop cannot be used here: an
        # exhausted ScriptedConsole answers with the last option, and
        # against a declared rival the decoy IS the last option, so a
        # loop would never terminate.
        con.say(f"  There is nothing to load — the wagon is {wagon.note}. "
                f"The stash stays where it is.")
        second = [o for i, o in enumerate(options) if i != 1]
        pick = con.menu(prompt, second)
        choice = 0 if pick == 0 else pick + 1

    tribute = rival.tribute_demanded or 1500
    if not target_raid and choice == 2 and state.dirty >= tribute:
        state.dirty -= tribute
        models.adjust_relation(state, rival_key, 15)
        rival.warning = None
        con.say("  Money changes hands in a parking lot. The cars drive away.")
        con.say("  Everyone on your payroll knows you paid.")
        for e in state.hired():
            e.morale -= 1
        return RaidResult("averted", damage_before, 0, 0.0)

    if choice == 1:
        # The wagon holds a wagonload. Anything past that stays — and is found.
        con.say("  The wagon leaves at midnight, riding low. They break in at two.")
        overflow = state.stash_bulk(target.stash) - data.VEHICLE_CARGO
        lost_units = 0
        if overflow > 0:
            for g in sorted(target.stash,
                            key=lambda g: -data.GOODS[g]["bulk"]):
                while overflow > 0 and target.stash.get(g, 0) > 0:
                    target.stash[g] -= 1
                    overflow -= data.GOODS[g]["bulk"]
                    lost_units += 1
        target.damage_days = 2
        target.reputation -= 8
        if lost_units:
            con.say(f"  A wagon holds a wagonload. They find the other "
                    f"{lost_units} units in the walk-in and take them.")
        else:
            con.say("  They wreck the front and find an empty walk-in. "
                    "Message received — both ways.")
        models.adjust_relation(state, rival_key, -5)
        rival.warning = None
        return RaidResult("landed", damage_before,
                          max(0, target.damage_days - damage_before),
                          0.0, wagon_taken=True)

    # Fight.
    defenders = state.crew()
    strength = max([e.nerve for e in defenders], default=3) + (4 if has_guard else 0)
    attack = 4 + rival.strength / 12 + rng.uniform(0, 4) \
        + war.raid_edge(state, rival_key)
    if strength + rng.uniform(0, 4) >= attack:
        con.say("  It's loud and brief. They leave one man's jacket and all their nerve.")
        dealt = models.apply_rival_damage(state, rival_key, "defense",
                                          models.DEFENSE_STRENGTH)
        models.adjust_relation(state, rival_key, -20)
        state.add_heat(target.district, 15)
        state.add_case(3, "a brawl at your shop made the police blotter")
        rival.warning = None
        return RaidResult("repelled", damage_before, 0, dealt)
    else:
        lost_units = 0
        for g in list(target.stash):
            take = target.stash[g] // 2
            target.stash[g] -= take
            lost_units += take
        grabbed = min(state.dirty, rng.randint(500, 1500))
        state.dirty -= grabbed
        target.damage_days = 3
        target.reputation -= 12
        if defenders and rng.random() < 0.5:
            v = rng.choice(defenders)
            v.injured_days = rng.randint(2, 5)
            con.say(f"  {v.name} is hurt — out {v.injured_days} days.")
        con.say(f"  They take {lost_units} units and {money(grabbed)} from the register,")
        con.say("  and leave the ovens in pieces. The shop limps for days.")
        state.add_heat(target.district, 20)
        state.add_case(4, "an armed robbery at your address raised questions")
    rival.warning = None
    # damage_added is the ACTUAL delta (rev. 15 item 4): a shop already
    # limping reports what tonight added, not tonight's absolute level.
    return RaidResult("landed", damage_before,
                      max(0, target.damage_days - damage_before), 0.0)
