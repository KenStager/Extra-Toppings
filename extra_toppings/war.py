"""The Harbor War: campaigns, corners, side-picking, and the board.

The branch's mechanics live here the way the Straight Path lives in
straight.py. The state model (WarCampaignState, the damage and
relation authorities, the heat policy) lives in models.py; this
module owns the §2.4.3 numbers and the war's behavior.

Every constant below is a placeholder in the §6.3 sense: structure is
the decision, numbers are tuning, and the §2.7 war rows move them
only on a recorded ruling.
"""

import random
from dataclasses import dataclass

from . import data, evidence, models
from .models import State, WarCampaignState
from .ui import Console, money

# ── The four channels' numbers (rev. 2 item 5, verbatim) ──────────
CORNER_RATE = 0.15        # strength per unit sold in the target's turf
CORNER_CAP = 4.0          # per night; their corner customers are finite
OUTAGE_MULT = 2           # corners count double while their ovens are cold

# ── War posture (rev. 13 items 6-9; rev. 14 item 4) ───────────────
WAR_AGGRESSION = 1.5      # target act-chance multiplier while at war
WAR_VIOLENT = 1.5         # target violent-share multiplier while at war
WAR_RAID_EDGE = 2.0       # their raid's attack-roll bonus while at war
LAW_CALM_ACT = 0.5        # act-chance multiplier while their lawyers work
VIOLENCE_RISE = 1.5       # permanent, after the ledger goes to the law
OPPORTUNIST_MULT = 1.25   # bystander Vinnie, when you look weak
TIP_RUNG_MULT = 3.0       # bystander Sal's tip rung, while uninsured
TIP_RUNG_MAX = 0.60       # ...but tipping never swallows his whole ladder
RAID_RUNG_CAP = 0.95      # no rung may swallow the ladder (rev. 14 item 4)

# ── The alertness pressure policy (rev. 15, sanctioned) ───────────
# The round-10 cooldown grinder won because a failed attempt only
# failed tonight. The review's sanctioned correction: target alertness
# feeds ONE visible war-pressure policy — declining job impact and
# rising retaliation — so every swing teaches him, and what he learns
# makes the rest of the campaign harder. The policy has a KNEE at the
# hardened band (models.security_word's own threshold): a sleepy or
# wary target has hardened nothing, so raiding INTO the quiet windows
# stays full price — which is the pacing thesis — while grinding into
# a hardened fortress is exactly what pays less and provokes more.
# Placeholders per §6.3; FINDINGS reports the calibration.
ALERT_PRESSURE_KNEE = 4.0  # the hardened band: pressure starts here
ALERT_IMPACT = 0.10        # impact lost per alertness point past the knee
ALERT_IMPACT_FLOOR = 0.4   # a landed job always costs him something
ALERT_RETALIATION = 0.10   # act-chance gained per point past the knee


@dataclass(frozen=True)
class WarPressure:
    """One derivation, three consumers (the board explains what the
    payoff and the rival policy execute — they cannot disagree)."""
    impact_mult: float        # scales a job's strength damage
    retaliation_mult: float   # scales the target's act chance
    note: str


def pressure(state: State, rival_key: str) -> "WarPressure":
    if models.live_campaign(state, rival_key) is None:
        return WarPressure(1.0, 1.0, "")
    hard = max(0.0, state.rivals[rival_key].alertness
               - ALERT_PRESSURE_KNEE)
    if hard == 0.0:
        return WarPressure(1.0, 1.0, "")
    impact = max(ALERT_IMPACT_FLOOR, 1.0 - hard * ALERT_IMPACT)
    note = ("his security has learned the handwriting — jobs land "
            "softer now, and he hits back harder")
    return WarPressure(impact, 1.0 + hard * ALERT_RETALIATION, note)


def job_damage(state: State, rival_key: str, base: int) -> float:
    """A job's strength price under the pressure policy. Flag-off (and
    at alertness zero) this returns the caller's own int unchanged —
    the damage authority's flag-off arithmetic stays bit-identical."""
    p = pressure(state, rival_key)
    if p.impact_mult == 1.0:
        return base
    return base * p.impact_mult


# ── The paid-loyalty primitive's third face (rev. 13 item 7) ──────
WAR_PAY_PER_HEAD = 20     # per read-in name, per night at war
INSURANCE_RATE = 800      # Sal's invoice: seven nights of coverage
INSURANCE_NIGHTS = 7

# ── Capture (rev. 13 item 10; rev. 14 item 7) ─────────────────────
CAPTURE_UNDERGROUND = 0.5  # their coded customers call your board

# THE terminal vocabulary (rev. 16 item 4): grade() writes these and
# the study reads them — one spelling, no retired forms.
GOOD_ENDINGS = frozenset({"harbor_yours", "syndicate"})


# ── Campaign lookups (all derived — no duplicate state) ───────────

def campaigns(state: State) -> list:
    if state.branch != "war" or state.branch_state is None:
        return []
    return state.branch_state.campaigns


def campaign_for(state: State, rival_key: str):
    """The campaign naming this rival, live or broken; None outside
    the branch or for an undeclared rival."""
    for c in campaigns(state):
        if c.rival_key == rival_key:
            return c
    return None


def target_key(state: State) -> str | None:
    """The live campaign's rival — the one front (rev. 14 item 9)."""
    camp = models.live_campaign(state)
    return camp.rival_key if camp else None


def bystander_key(state: State) -> str | None:
    """The other rival, while a campaign is live and they still stand."""
    tk = target_key(state)
    if tk is None:
        return None
    for k, r in state.rivals.items():
        if k != tk and r.alive and campaign_for(state, k) is None:
            return k
    return None


def broken_keys(state: State) -> list:
    return [c.rival_key for c in campaigns(state)
            if c.broken_day is not None]


def district_captured(state: State, dk: str) -> bool:
    """A district whose owner fell to a campaign: their underground is
    yours (§6.4 — the underground only; never a second shop)."""
    owner = data.DISTRICTS[dk]["rival"]
    return owner is not None and owner in broken_keys(state)


def underground_bonus(state: State, dk: str) -> float:
    """The capture bonus to the district's underground factor — 0.0
    everywhere outside a captured district, so every flag-off consumer
    adds exactly zero (bit-identity preserved by construction)."""
    return CAPTURE_UNDERGROUND if district_captured(state, dk) else 0.0


def raid_edge(state: State, rival_key: str) -> float:
    """The attack-roll modifier for this rival's raid tonight — one
    computation, consumed by the policy view AND by incoming_raid, so
    execution and explanation cannot drift. 0.0 flag-off: every
    existing attack roll adds exactly zero."""
    return WAR_RAID_EDGE if target_key(state) == rival_key else 0.0


def insurance_paid(state: State) -> bool:
    bs = state.branch_state
    return (state.branch == "war" and bs is not None
            and bs.insurance_paid_until is not None
            and state.day <= bs.insurance_paid_until)


# ── The corner channel (rev. 2 item 5) ────────────────────────────

SALVAGE_HEAT = 8      # trucks at a dead man's dock get noticed (§6.3)

# The record domain in models (rev. 19 item 2) mirrors the corner
# channel's real ceiling — drift is an import error, not a quiet lie.
assert models.CORNER_DAMAGE_MAX_H == round(CORNER_CAP * OUTAGE_MULT * 100)


def _bs(state: State):
    """The war's BranchState, or a loud refusal — these entry points
    are in-branch only, and a misrouted call must not invent state."""
    if state.branch != "war" or state.branch_state is None:
        raise ValueError("not in the war branch")
    return state.branch_state


def declare(state: State, rival_key: str, con: Console) -> None:
    """Open a front (rev. 14 item 9): append the campaign, lock the
    vendetta at the mutation authority, and validate the transition.
    The sit-down's first declaration and the board's second one both
    land here — one path, one lock."""
    bs = _bs(state)
    rival = state.rivals[rival_key]
    if rival_key == "sal" and bs.insurance_paid_until is not None:
        # Rev. 15 item 6: coverage cannot outlive the merchant's
        # neutrality — declaring on Sal tears up his own policy.
        bs.insurance_paid_until = None
        con.say("  Sal's retainer is void the moment his name goes on "
                "the table. Nobody asks for a refund.")
    bs.campaigns.append(WarCampaignState(
        rival_key=rival_key, declared_day=state.day,
        starting_hundredths=round(rival.strength * 100)))
    models.set_relation(state, rival_key,
                        min(rival.relation, models.VENDETTA_RELATION))
    models.validate_branch_state("war", bs)
    spec = data.RIVALS[rival_key]
    con.say(f"  {spec['short']}'s name goes on the table. The tribute and "
            f"truce doors close behind it — no truce, no cannoli, ever.")


def entry_scene(state: State, con: Console) -> None:
    """The morning after the declaration seats the branch (§3.3 D14)."""
    tk = target_key(state)
    if tk is None:
        return
    spec = data.RIVALS[tk]
    crew = [e for e in state.hired() if e.aware and not e.arrested]
    con.say("")
    con.say(f"  The war board goes up in the back office. "
            f"{spec['short']} first.")
    if crew:
        con.say(f"  War pay stands at +{money(WAR_PAY_PER_HEAD)} a night "
                f"for {len(crew)} read-in name(s), effective tonight — "
                f"street money for street work.")
    board(state, con)


def morning_lines(state: State, con: Console) -> None:
    """The board's compact face, printed with the morning header — it
    JOINS the market board (rev. 14 item 1a); prices stay."""
    for line in _board_lines(state, compact=True):
        con.say(f"  {line}")


def board(state: State, con: Console) -> None:
    con.say("")
    con.say("  ── THE WAR BOARD ──")
    for line in _board_lines(state, compact=False):
        con.say(f"  {line}")


def _board_lines(state: State, compact: bool) -> list:
    """One derivation for both renderings: the mixed campaign visible
    on screen, not implied in prose (§2.4.3). Explanations come from
    the same views that drive execution — they cannot disagree."""
    from . import rivals as rivals_mod
    lines = []
    camp = models.live_campaign(state)
    if camp is not None:
        rv = state.rivals[camp.rival_key]
        spec = data.RIVALS[camp.rival_key]
        ovens = (f"ovens cold {rv.ovens_wrecked_days}d — corners count "
                 f"double" if rv.ovens_wrecked_days else "ovens intact")
        lines.append(
            f"{spec['short'].upper()} — strength {rv.strength:g} of "
            f"{camp.starting_hundredths / 100:g}, security "
            f"{models.security_word(rv.alertness)}, {ovens}")
        spent: dict = {}
        for r in camp.damage:
            spent[r.channel] = spent.get(r.channel, 0) + r.hundredths
        if spent:
            ledger = " / ".join(f"{ch} {spent[ch] / 100:g}"
                                for ch in models.WAR_CHANNELS
                                if ch in spent)
            lines.append(f"where his strength went: {ledger}")
        press = pressure(state, camp.rival_key)
        if press.impact_mult < 1.0:
            # The actual multipliers, not adjectives (rev. 16 item 5c).
            lines.append(
                f"pressure — jobs land at {press.impact_mult:.0%} "
                f"strength; his response runs "
                f"×{press.retaliation_mult:.2f} (his security learned "
                f"the handwriting)")
        else:
            lines.append("pressure — the window is open: jobs land at "
                         "full strength")
        if rv.ledger_stolen:
            lines.append("his ledger sits in your safe — lean on it, or "
                         "hand it to the woman in the gray suit")
    for c in campaigns(state):
        if c.broken_day is not None:
            spec = data.RIVALS[c.rival_key]
            tail = (" — salvage waiting at his stockroom"
                    if c.salvage_available else "")
            lines.append(f"{spec['short']} broke on day "
                         f"{c.broken_day}{tail}")
    bk = bystander_key(state)
    if bk is not None:
        pol = rivals_mod.rival_policy(state, bk)
        spec = data.RIVALS[bk]
        posture = "merchant" if bk == "sal" else "opportunist"
        note = f" ({pol.notes[0]})" if pol.notes else ""
        lines.append(f"{spec['short']} — posture {posture}{note}")
    if not compact:
        crew_bits = []
        for e in state.hired():
            if e.arrested:
                crew_bits.append(f"{e.name} in custody")
            elif e.injured_days:
                crew_bits.append(f"{e.name} hurt {e.injured_days}d")
            else:
                crew_bits.append(f"{e.name} fit, morale {e.morale}")
        if crew_bits:
            lines.append("crew — " + "; ".join(crew_bits))
        heat_bits = []
        for dk in data.DISTRICTS:
            hpol = models.district_heat_policy(state, dk)
            if hpol.band != "cool":
                heat_bits.append(
                    f"{data.DISTRICTS[dk]['label']} {hpol.band.upper()}")
        if heat_bits:
            lines.append("turf heat — " + "; ".join(heat_bits)
                         + " (take it hot and you take ash)")
        bs = _bs(state)
        if bs.war_pay_short_nights:
            lines.append(f"war pay has bounced "
                         f"{bs.war_pay_short_nights} night(s) — "
                         f"people notice")
    return lines


# ── The nightly obligation (rev. 14 item 7) ───────────────────────

def night_obligation(state: State, con: Console,
                     payroll_short: bool) -> None:
    """War pay, transactionally: base payroll and rent resolved FIRST
    (the caller's flag); if base wages bounced, no bonus is paid and
    no second morale penalty lands — one short night, one roster-wide
    hit. Otherwise the bonus draws dirty first, then clean, checked
    before any mutation; the amounts persist separately.

    Counsel's nightly work runs first — the same machinery as
    everywhere the capability policy unlocks it (rev. 14 item 8)."""
    bs = _bs(state)
    evidence.counsel_nightly(state, con)
    crew = [e for e in state.hired() if e.aware and not e.arrested]
    due = WAR_PAY_PER_HEAD * len(crew)
    if due == 0:
        return
    if payroll_short:
        # The base short already took its one roster-wide penalty in
        # _payroll_and_rent; the bonus just visibly bounces with it.
        bs.war_pay_short_nights += 1
        con.say(f"  War pay bounces with the payroll — "
                f"{money(due)} owed to people carrying crowbars.")
        return
    if state.dirty + state.clean < due:
        bs.war_pay_short_nights += 1
        for e in state.hired():
            e.morale -= 2
        con.say(f"  You can't cover war pay ({money(due)}). People "
                f"doing dangerous work notice light envelopes.")
        return
    from_dirty = min(state.dirty, due)
    state.dirty -= from_dirty
    state.clean -= due - from_dirty
    bs.war_pay_paid += due
    con.say(f"  War pay goes out: {money(due)} for {len(crew)} "
            f"name(s), street money first.")


def night_insolvency(state: State, con: Console,
                     payroll_short: bool) -> None:
    """The shared clean-insolvency transition, in the war's voice
    (rev. 15 item 3): a war fought from an empty till ends the same
    way every empty till does."""
    outcome = models.insolvency_tick(state, payroll_short)
    if outcome == "broke":
        con.say("  Two nights running: no payroll, no stock, no hidden "
                "dollar — and a war still on the books. The crew walks "
                "off the battlefield; the ovens never reopen.")
    elif outcome == "warned":
        con.bullet("Payroll missed with nothing left to sell and "
                   "nothing hidden. Wars run on money; one more night "
                   "like this ends yours.")


# ── Sal's insurance (rev. 14 item 1c: a predictable invoice) ──────

def insurance_due(state: State) -> bool:
    bk = bystander_key(state)
    if bk != "sal":
        return False
    bs = _bs(state)
    return bs.insurance_paid_until is None \
        or state.day > bs.insurance_paid_until


def insurance_card(state: State, con: Console) -> None:
    """The invoice arrives at declaration and at every expiry — fixed
    rate, fixed term, no dice anywhere. Dirty funds it (§2.4.3:
    tribute to the bystander), and declining is the safe last option."""
    bs = _bs(state)
    con.say("")
    con.say(f"  Sal's man, hat in hand: {money(INSURANCE_RATE)} keeps a "
            f"merchant a merchant for {INSURANCE_NIGHTS} nights. 'Between "
            f"businessmen — while there's a war on, my employer's memory "
            f"for faces gets expensive.'")
    if state.dirty < INSURANCE_RATE:
        con.say(f"  You don't have {money(INSURANCE_RATE)} dirty to give "
                f"him. He tips his hat anyway. A merchant with no "
                f"retainer freelances.")
        return
    c = con.menu("Sal's insurance:", [
        f"Pay — {money(INSURANCE_RATE)} dirty, {INSURANCE_NIGHTS} quiet "
        f"nights",
        "Decline — let the man who never throws a punch freelance",
    ])
    if c == 0:
        state.dirty -= INSURANCE_RATE
        bs.insurance_paid_until = state.day + INSURANCE_NIGHTS - 1
        con.say("  The envelope changes hands. Sal stays a merchant — "
                "for a week.")
        sal = state.rivals.get("sal")
        if sal is not None and sal.raid_warning > 0:
            # Rev. 15 item 6: "seven quiet nights" must cancel a raid
            # already telegraphed — coverage that lets the cars keep
            # circling is not coverage.
            sal.warning = None
            con.say("  Across the street, the unfamiliar cars start "
                    "their engines and leave. A merchant honors his "
                    "coverage.")
    else:
        con.say("  He nods slowly and writes nothing down. Sal never "
                "writes anything down.")


# ── The ledger's second spend (rev. 13 item 4, war-only) ──────────

def spend_ledger_law(state: State, rival_key: str, con: Console) -> None:
    """Hand the stolen ledger to the woman in the gray suit: their
    case, not yours — strength −20, their aggression halved while the
    lawyers work, and their violence rises for good. Either spend
    consumes the leverage."""
    camp = models.live_campaign(state, rival_key)
    rival = state.rivals[rival_key]
    spec = data.RIVALS[rival_key]
    rival.ledger_stolen = False   # leverage used is leverage gone
    models.apply_rival_damage(state, rival_key, "ledger",
                              models.LEDGER_LAW_STRENGTH)
    if camp is not None and camp.broken_day is None:
        # Four suppressed rival PHASES (rev. 15 item 7): the spend
        # lands before tonight's rival phase, so tonight is the first
        # of the four — day + DAYS was five.
        camp.law_calm_until = state.day + models.LEDGER_LAW_CALM_DAYS - 1
        camp.violence_raised = True
    con.say("  The woman in the gray suit reads three pages, then asks "
            "if there are more. There are forty.")
    con.say(f"  {spec['short']}'s people spend the week with lawyers — "
            f"and when they surface, they'll be meaner for good. "
            f"It's their case now, not yours.")
    if not rival.alive:
        con.say(f"  The subpoenas finish what the jobs started — "
                f"{spec['short']}'s organization is done.")


# ── Salvage: a physical pickup (rev. 14 item 6) ───────────────────

def salvage_ready(state: State):
    for c in campaigns(state):
        if c.salvage_available:
            return c
    return None


def plan_salvage(state: State, con: Console, reserved: list,
                 wagon: models.PlannedWagon,
                 origin_shop: str) -> dict | None:
    """Morning: assign the wagon and a driver to the dead man's
    stockroom. Reservations come from THE night-assignment view
    (rev. 15 item 2): people already spoken for by the route or the
    raid are not offered, and the wagon does one job a night.
    Execution and inventory commit at service, transactionally,
    against the same view."""
    camp = salvage_ready(state)
    if camp is None:
        return None
    if not wagon.available:
        # The lifecycle names the address it is talking about; every
        # pre-existing cause keeps the sentence the game ships.
        con.say(f"  {models.wagon_gone_line(wagon)} — the stockroom "
                f"isn't going anywhere."
                if wagon.blocked_by in ("lifecycle", "unhoused") else
                "  The wagon is spoken for tonight — the stockroom "
                "isn't going anywhere.")
        return None
    drivers = [e for e in state.hired()
               if e.available and e.aware and e.driving >= 4
               and e not in reserved]
    if not drivers:
        con.say("  Nobody read-in is fit and free to drive the pickup "
                "tonight.")
        return None
    spec = data.RIVALS[camp.rival_key]
    names = [f"{e.name} (drive {e.driving})" for e in drivers] + ["Not tonight"]
    pick = con.menu(f"Send the wagon to {spec['short']}'s stockroom — "
                    f"who drives?", names)
    if pick == len(drivers):
        return None
    # The pickup NAMES the address it leaves from (P4b.1a), and the
    # caller must say which — a wagon job with no origin cannot be
    # answered per address, and inferring the home shop here is the
    # implicit default rev. 27 item 7 forbids.
    # The origin is validated HERE, before the plan exists: a pickup
    # that names an address the world does not have is refused rather
    # than returned as a job no wagon can serve.
    plan = {"rival": camp.rival_key, "driver": drivers[pick],
            "origin_shop": origin_shop, "wagon_key": wagon.first}
    models.plan_origin(state, plan)
    return plan


@dataclass(frozen=True)
class SalvageResult:
    """What the pickup ACTUALLY did (rev. 17 item 6) — the night's
    wagon question reads this, never the morning's intention. outcome:
    "collected" (the wagon went out), "scrubbed" (driver lost before
    departure — the wagon never left), "gone" (nothing waiting)."""
    outcome: str
    wagon_used: bool
    collected_units: int = 0


def run_salvage(state: State, plan: dict, con: Console,
                rng: random.Random,
                reserved: list | None = None) -> SalvageResult:
    """Service: the pickup rolls. Revalidated transactionally against
    the SAME assignment view that planned it (rev. 15 item 2) — the
    driver must still be standing and still unclaimed by any other
    job, and the salvage still waiting. The wagon carries a wagonload;
    what comes home lands through THE haul-placement authority (shop,
    then warehouse, then left behind) exactly as a raid haul does.
    Draw budget: EXACTLY ONE draw on the war stream per pickup (the
    want roll, §2.7-pinned); the split across goods is deterministic
    value-first. Returns the typed execution result."""
    camp = campaign_for(state, plan["rival"])
    driver = plan["driver"]
    if camp is None or not camp.salvage_available:
        return SalvageResult(outcome="gone", wagon_used=False)
    if not driver.available or driver in (reserved or []):
        con.bullet(f"The pickup is scrubbed — {driver.name} isn't "
                   f"free to drive it after all.")
        return SalvageResult(outcome="scrubbed", wagon_used=False)
    rival = state.rivals[camp.rival_key]
    spec = data.RIVALS[camp.rival_key]
    camp.salvage_available = False
    camp.salvage_day = state.day
    thin = max(0.3, 1.0 - rival.alertness * 0.07)
    want = int(rng.randint(4, 10 + camp.starting_hundredths // 1000)
               * thin)                                     # the ONE draw
    space = data.VEHICLE_CARGO
    haul: dict = {}
    wagon_left = 0
    for g in ("hot_honey", "mushrooms", "oregano"):        # value-first
        if want <= 0:
            break
        bulk = data.GOODS[g]["bulk"]
        share = max(0, want // 2) if g != "oregano" else want
        take = min(share, space // bulk)
        if take:
            haul[g] = take
            space -= take * bulk
        wagon_left += max(0, share - take)
        want -= share
    # The pickup unloads at the address its wagon came home to
    # (rev. 22 item 5) — explicit, never a home default.
    kept, storage_left = models.place_haul(
        state, haul, models.exactly_one_shop(state).key)
    left_behind = wagon_left + storage_left
    state.add_heat(data.RIVALS[camp.rival_key]["home"], SALVAGE_HEAT)
    if kept:
        got = ", ".join(f"{u}x {data.GOODS[g]['label']}"
                        for g, u in kept.items())
        con.say(f"  {driver.name} backs the wagon up to a dead man's "
                f"dock. Salvage: {got}.")
    else:
        con.say(f"  {spec['short']}'s stockroom is picked cleaner than "
                f"the war left it. The trip buys nothing but attention.")
    if left_behind:
        con.say(f"  {left_behind} unit(s) stay behind — the wagon holds "
                f"a wagonload.")
    return SalvageResult(outcome="collected", wagon_used=True,
                         collected_units=sum(kept.values()))


# ── Day 30 (§2.5, campaign-count per rev. 14 item 9) ──────────────

def grade(state: State) -> str:
    broken = len(broken_keys(state))
    if broken >= 2:
        # An explicit terminal (rev. 15 item 4): the outcome matrix
        # must not depend on generic epilogue ordering — a two-capture
        # war was printing the legitimate-exit text.
        return "syndicate"
    if broken == 1:
        return "harbor_yours"
    return "long_war"


def won_then_lost(state: State) -> bool:
    """The Won-the-War-Lost-the-Verdict styling: a capture transition
    completed BEFORE the arrest latch — transition ordering, never
    calendar-day equality (rev. 14 item 9)."""
    return any(c.captured_pre_latch for c in campaigns(state))


def corner_diversion(state: State, dk: str, owner: str, sold: int,
                     report: dict, *, rate: float, cap: float) -> float:
    """Units sold in the target's turf divert their income: strength
    −rate per unit, capped per night, doubled while their ovens are
    cold — the §2.4.3 outage window. The terms come from THE
    route-market view (rev. 15 item 5), which prices them alongside
    everything else territorial; a zero rate is the view saying no
    live campaign owns this turf. One route runs per night, so the
    per-route cap IS the per-night cap. Books to the 'corners' channel
    through the one damage authority."""
    camp = models.live_campaign(state, owner)
    if camp is None or rate <= 0.0 or sold <= 0:
        return 0.0
    amount = min(cap, sold * rate)
    applied = models.apply_rival_damage(state, owner, "corners", amount)
    if applied > 0:
        window = (" — his ovens are cold and his customers keep your number"
                  if state.rivals[owner].ovens_wrecked_days > 0 else "")
        report["lines"].append(
            f"His corner customers took your number tonight{window} "
            f"(strength −{applied:g}).")
    return applied
