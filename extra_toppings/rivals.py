"""Rival syndicates: two families, two strategies, long memories."""

import random
from dataclasses import dataclass

from . import data, models, straight, war
from .models import State
from .ui import Console, money


@dataclass(frozen=True)
class RivalPolicy:
    """THE rival-policy view (rev. 14 item 4): one normalized answer
    to how this rival behaves tonight — act probability, the action
    ladder's cut points, the raid edge, and whether they act at all.
    rival_phase EXECUTES this view and the war board EXPLAINS it; the
    two can never disagree because there is only one derivation.

    Flag-off (no war campaign anywhere) every number is the exact
    expression the old ladder inlined — same floats, same order. War
    modifiers compose inside the view and nowhere else, and the raid
    rung is capped (RAID_RUNG_CAP) so no multiplier can swallow the
    ladder or push a threshold past one."""
    act_chance: float
    price_war_t: float
    poach_t: float
    extort_t: float
    raid_t: float          # tip rung is the remainder to 1.0
    raid_edge: float       # added to their raid's attack roll
    hostile: bool          # False: no hostile act tonight (insurance)
    notes: tuple           # player-facing explanation, war board


def rival_policy(state: State, key: str) -> RivalPolicy:
    rival = state.rivals[key]
    spec = data.RIVALS[key]
    grudge = max(0.0, -rival.relation) / 100      # 0..1
    act_chance = spec["aggression"] * 0.5 + grudge * 0.6
    if state.branch == "straight" and state.total_stock_units() == 0:
        # Rivals smell retreat: a shop that no longer scares anyone
        # (§2.4.1, rev. 9 item 13).
        act_chance *= straight.RETREAT_AGGRESSION
    violent = spec["violence"] * (0.5 + grudge)
    price_war_t, poach_t, extort_t = 0.30, 0.50, 0.68
    raid_t = 0.68 + violent * 0.25
    hostile = True
    notes: list = []

    tk = war.target_key(state)
    if tk == key:
        camp = models.live_campaign(state, key)
        act_chance *= war.WAR_AGGRESSION
        notes.append("at war — they come bigger and more often")
        press = war.pressure(state, key)
        act_chance *= press.retaliation_mult
        if press.note:
            notes.append(press.note)
        if camp is not None and camp.law_calm_until is not None \
                and state.day <= camp.law_calm_until:
            act_chance *= war.LAW_CALM_ACT
            notes.append("their lawyers have them busy — aggression "
                         "halved for now")
        violent_mult = war.WAR_VIOLENT
        if camp is not None and camp.violence_raised:
            violent_mult *= war.VIOLENCE_RISE
            notes.append("cornered by the prosecution, they come back "
                         "meaner — permanently")
        raid_t = min(0.68 + violent * violent_mult * 0.25,
                     war.RAID_RUNG_CAP)
    elif tk is not None and key == war.bystander_key(state):
        if key == "sal":
            if war.insurance_paid(state):
                hostile = False
                notes.append("insurance holds — Sal sells to both sides "
                             "and stays a merchant")
            else:
                # The merchant's price for going uninsured (rev. 14
                # item 4): the EXISTING tip behavior — heat +12, a 30%
                # chance of a 4-point paper record — fires three times
                # as often. The rung widens; _plant itself is
                # unchanged, so no second record is layered on top.
                tip_width = min(war.TIP_RUNG_MAX,
                                (1.0 - raid_t) * war.TIP_RUNG_MULT)
                scale = (1.0 - tip_width) / raid_t
                price_war_t *= scale
                poach_t *= scale
                extort_t *= scale
                raid_t *= scale
                notes.append("uninsured — the man who never throws a "
                             "punch keeps the precinct's number handy")
        elif rival.raid_warning == 0 and (
                any(sh.damage_days > 0 for sh in state.shops)
                or any(e.injured_days for e in state.hired())):
            act_chance *= war.OPPORTUNIST_MULT
            raid_t = min(0.68 + violent * war.OPPORTUNIST_MULT * 0.25,
                         war.RAID_RUNG_CAP)
            notes.append("an opportunist smells blood — you look weak "
                         "and he knows it")

    return RivalPolicy(
        act_chance=min(1.0, act_chance),
        price_war_t=price_war_t, poach_t=poach_t, extort_t=extort_t,
        raid_t=raid_t, raid_edge=war.raid_edge(state, key),
        hostile=hostile, notes=tuple(notes))


def rival_phase(state: State, con: Console, rng: random.Random) -> None:
    """Each rival takes one action a night, scaled to how much they hate
    you. The behavior IS rival_policy's view — this loop only rolls the
    dice and dispatches (rev. 14 item 4)."""
    for key, rival in state.rivals.items():
        if not rival.alive:
            continue
        spec = data.RIVALS[key]

        if rival.ovens_wrecked_days:
            rival.ovens_wrecked_days -= 1
            models.apply_rival_damage(state, key, "ovens", models.OVEN_BLEED,
                                      floor=models.OVEN_BLEED_FLOOR)
        # Guards get bored again, slowly — but not on a night you hit
        # them. THE one transition (rev. 19 item 3), shared with the
        # pacing experiment.
        models.alertness_decay_tick(rival, state.day)

        # A telegraphed raid counts down; landing is handled by the night phase.
        if rival.warning is not None and rival.warning.nights > 1:
            # The countdown moves; the address it named does not.
            rival.warning = rival.warning.counted_down()
            con.bullet(f"{spec['short']}'s cars rolled past the shop again. Twice.")
            continue
        if rival.warning is not None:
            continue   # tonight — night phase resolves it

        pol = rival_policy(state, key)
        if not pol.hostile:
            continue   # the insurance week: a merchant stays a merchant
        if rng.random() > pol.act_chance:
            if rival.relation > 20 and rng.random() < 0.2:
                con.bullet(f"{spec['short']} sends over a tray of cannoli. A truce holds.")
            continue

        roll = rng.random()
        if roll < pol.price_war_t:
            _price_war(state, key, spec, con)
        elif roll < pol.poach_t:
            _poach(state, rival, spec, con, rng)
        elif roll < pol.extort_t:
            _extort(state, rival, spec, con, rng)
        elif roll < pol.raid_t:
            # The warning names its address the moment it is raised
            # (rev. 23 item 2), through the one target authority —
            # UNLESS this rival already collects protection somewhere,
            # in which case the warning goes to the address they are
            # already standing over (rev. 34 item 3). The man taking
            # money for the Meadows ovens does not threaten a
            # different room.
            aimed = (rival.tribute.shop_key if rival.tribute is not None
                     else models.raid_target(state, key))
            rival.warning = models.RaidWarning(rng.randint(2, 3), aimed)
            con.bullet(f"Unfamiliar cars idle across from the shop. {spec['short']}'s "
                       f"plates. Something is coming.")
            if models.multi_address(state):
                con.bullet(f"  Across from the "
                           f"{models.address_label(state, aimed)} room, to be exact.")
        else:
            _plant(state, rival, spec, con, rng)


def _price_war(state: State, key: str, spec: dict, con: Console) -> None:
    # Coupons steal customers for a while; they don't make your pizza worse.
    con.bullet(f"{spec['short']} papers the neighborhood with two-for-one coupons. "
               f"Expect thin order books for a few days.")
    # The blitz papers ONE neighbourhood: the address the rival moved
    # against, through the same target authority the raid uses.
    hit = state.shop_by_key(models.raid_target(state, key))
    hit.coupon_days = max(hit.coupon_days, 3)


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
        models.release_from_posts(state, e, "poach")
        con.bullet(f"{e.name} took {spec['short']}'s offer and didn't finish the shift.")
        if e.aware:
            state.add_case(8, f"{e.name} left for a rival knowing everything",
                           kind="witness", source=e.key)
            con.bullet(f"...and {e.name} knew things. That's a problem now.")
    else:
        e.morale -= 1
        con.bullet(f"{spec['short']} made {e.name} an offer. It was declined — this time.")


def _extort(state: State, rival, spec: dict, con: Console, rng: random.Random) -> None:
    # The target is chosen ONCE, here, and persisted with the sum
    # (rev. 34 item 3): a standing demand is protection attached to an
    # address, and every later reading of it — including a warning
    # this rival raises while it stands — reads the record rather than
    # asking again.
    demand = rng.randrange(600, 1400, 100)
    rival.tribute = models.TributeDemand(demand,
                                         models.raid_target(state, rival.key))
    con.bullet(f"A note under the door: {money(demand)} a week 'keeps the ovens safe.' "
               f"— {spec['short']}")
    if models.multi_address(state):
        con.bullet(f"  It was slid under the "
                   f"{models.address_label(state, rival.tribute.shop_key)} "
                   f"door. That is the room he means.")


def _plant(state: State, rival, spec: dict, con: Console, rng: random.Random) -> None:
    # The tip names an address through the ONE target authority and
    # the heat lands on THAT district (rev. 33 item 6). It used to
    # land on `data.HOME_DISTRICT` unconditionally, which with two
    # addresses would have had the rival moving against your Meadows
    # room by phoning the police about Old Harbor. With one address
    # the authority returns it and it stands in the home district, so
    # every released run raises the same heat in the same place from
    # the same draw — an identity MEASURED at both gates, not assumed.
    aimed = models.raid_target(state, rival.key)
    con.bullet("An anonymous tip sends a patrol crawling past your block all night.")
    if models.multi_address(state):
        con.bullet(f"  The block is the {models.address_label(state, aimed)} "
                   f"one. Somebody was specific.")
    state.add_heat(state.shop_by_key(aimed).district, 12)
    if rng.random() < 0.3:
        # Paper, not witness (rev. 10 ruling): a tip in a file is an
        # intelligence report, not testimony — counsel can argue it.
        state.add_case(4, "an informant's tip put your shop in a file",
                       kind="paper")


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

    if models.vendetta_locked(state, key):
        # §2.4.3: no truce, no tribute, no cannoli — the peace verbs
        # are GONE for a declared rival, not greyed. What remains is
        # the ledger, if you hold it: the lean, or the woman in the
        # gray suit (war-only per the rev. 14 ruling, and a
        # vendetta-locked rival is war by construction).
        opts = []
        if rival.ledger_stolen:
            opts = ["Lean on them with the ledger",
                    "Hand the ledger to the woman in the gray suit "
                    "(their case, not yours)"]
        opts.append("Back")
        c = con.menu(f"{spec['short']}: at war. There is nothing to "
                     f"say — only things to spend.", opts)
        if rival.ledger_stolen and c == 0:
            _lean(state, key, rival, spec, con)
        elif rival.ledger_stolen and c == 1:
            war.spend_ledger_law(state, key, con)
        return

    opts = [f"Send a peace offering ({money(1000)} dirty)",
            "Propose a truce (works best from strength)"]
    if rival.ledger_stolen:
        opts.append("Lean on them with the ledger")
    opts.append("Back")
    c = con.menu(f"{spec['short']}: {spec['style']}", opts)

    if c == 0 and state.dirty >= 1000:
        state.dirty -= 1000
        models.adjust_relation(state, key, 12)
        con.say(f"  {spec['short']} accepts the envelope. The temperature drops a degree.")
    elif c == 1:
        odds = 0.3 + (state.rivals[key].strength < 40) * 0.3 + max(0, rival.relation) / 200
        if rng.random() < odds:
            models.set_relation(state, key, max(rival.relation, 25))
            rival.tribute = None
            con.say("  Handshakes over espresso. Your trucks stay out of each other's mirrors.")
        else:
            models.adjust_relation(state, key, -5)
            con.say(f"  {spec['short']} laughs. 'Come back when you own something.'")
    elif rival.ledger_stolen and c == 2:
        _lean(state, key, rival, spec, con)


def _lean(state: State, key: str, rival, spec: dict, con: Console) -> None:
    """The greedy ledger spend — one implementation for the peaceful
    menu and the war menu alike (the respell rule)."""
    models.apply_rival_damage(state, key, "ledger",
                              models.LEDGER_LEAN_STRENGTH)
    models.adjust_relation(state, key, -10)
    rival.tribute = None
    rival.ledger_stolen = False   # leverage used is leverage gone
    state.dirty += 2000
    con.say("  You read three names off page twelve. An envelope arrives by morning.")
    con.say(f"  +{money(2000)} dirty. {spec['short']} will not forget this — "
            f"and by next week those pages are worthless.")
