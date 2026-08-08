"""Evidence remediation (§2.3, scoped by rev. 9): counsel, settlements,
retention dormancy, the paid-points cap and the institutional-suspicion
floor.

The Case remains the clamped sum of its records — every verb here works
by changing what the records say, never by touching a separate number,
so displayed Case ≡ the visible ledger holds through every contest and
settlement (asserted nightly by the §2.7 studies). Physical and pattern
records are permanently immune: no verb below ever selects them. Arrest
latched at accrual outranks everything — every entry point is a no-op
on a finished run, and nothing here can un-latch it.

Bounds (§2.3, arithmetic per rev. 9 item 3): the 25-point cap binds the
PAID verbs — contests and settlements — as points actually removed,
truncating an event that exceeds the room left; the reversible
retention halving spends no budget. Evidence-only verbs refuse at or
below the 10-point floor; a settlement below the floor still signs (it
buys the goal term) but relieves nothing. Any event landing the sum
below the floor writes, or tops up in place, the one permanent
institutional-suspicion record by exactly the difference.
"""

from .models import (CASE_FLOOR, DORMANT_FACTOR, REMEDIATION_CAP, BranchState,
                     Employee, Evidence, State, fold_case)
from .ui import Console, money

COUNSEL_FEE = 150               # $/day, clean (§2.3)
COUNSEL_CONTEST_EVERY = 3       # every 3rd retained day contests
CONTEST_RELIEF = 0.60           # a contested paper record loses 60%
SETTLEMENT_WAGE_MULT = 6        # a settlement costs ~6x daily wage, clean
DORMANT_MORALE = 5              # retention keeps records dormant at >= this
SUSPICION_WHY = "they remember your name"
HUM_LABEL = "the routine discrepancies"


def _bs(state: State) -> BranchState:
    if state.branch_state is None:
        raise ValueError("remediation called outside an active branch")
    return state.branch_state


def remediation_left(state: State) -> float:
    return max(0.0, REMEDIATION_CAP - _bs(state).remediation_used)


def _apply_floor(state: State, before: float, con: Console) -> None:
    """§2.3: whenever remediation takes the sum below the floor, the
    suspicion record is written, or topped up in place, by exactly the
    difference — the sum never displays below 10 and always equals the
    records the player can read. The loop guards the one-ulp case where
    total + (floor − total) lands a hair under the floor."""
    total = fold_case(state.evidence)
    if total >= CASE_FLOOR or total >= before:
        return
    record = next((r for r in state.evidence if r.kind == "suspicion"), None)
    if record is None:
        record = Evidence(day=state.day, magnitude=0.0, kind="suspicion",
                          why=SUSPICION_WHY)
        state.evidence.append(record)
    while fold_case(state.evidence) < CASE_FLOOR:
        record.magnitude += CASE_FLOOR - fold_case(state.evidence)
    con.say(f"  The file thins to the part that never leaves: {SUSPICION_WHY}."
            f" (The sum holds at {CASE_FLOOR:.0f} — the climate cools; it"
            f" does not un-happen.)")


# ── counsel ───────────────────────────────────────────────────────

def counsel_nightly(state: State, con: Console) -> None:
    """The retainer, charged with the night's settling; every 3rd
    retained day contests the next record in the queue."""
    bs = _bs(state)
    if not bs.counsel_retained or state.game_over:
        return
    if state.clean < COUNSEL_FEE:
        bs.counsel_retained = False
        con.bullet(f"Counsel's office calls: the retainer bounced. The "
                   f"engagement letter arrives torn in half. "
                   f"({money(COUNSEL_FEE)}/day, clean, or nothing.)")
        return
    state.clean -= COUNSEL_FEE
    bs.counsel_days += 1
    con.say(f"  Counsel retained, day {bs.counsel_days} "
            f"({money(COUNSEL_FEE)} clean).")
    if bs.counsel_days % COUNSEL_CONTEST_EVERY == 0:
        contest_next(state, con)


def _contest_queue(state: State) -> list:
    """Flagged paper first, oldest first, one contest each; then the
    routine hum — every flagless tick — as the single rolling record
    §2.3 calls it (rev. 9 item 2). Returns the next target group."""
    flagged = [r for r in state.evidence
               if r.kind == "paper" and r.why and not r.contested
               and r.magnitude > 0]
    if flagged:
        return [flagged[0]]
    return [r for r in state.evidence
            if r.kind == "paper" and not r.why and not r.contested
            and r.magnitude > 0]


def contest_next(state: State, con: Console) -> None:
    if state.game_over:
        return
    bs = _bs(state)
    targets = _contest_queue(state)
    if not targets:
        con.say("  Counsel reads the file again and shrugs: nothing left "
                "worth arguing. The retainer keeps the books honest.")
        return
    before = fold_case(state.evidence)
    if before <= CASE_FLOOR:
        con.say("  Counsel closes the folder: the file is as cold as they "
                "will let it get. They remember your name.")
        return
    room = remediation_left(state)
    if room <= 0:
        con.say("  Counsel shakes their head: every argument this file will "
                "bear has been made. The remaining pages stand.")
        return
    wanted = sum(r.magnitude for r in targets) * CONTEST_RELIEF
    allowed = min(wanted, room)
    scale = allowed / wanted
    for r in targets:
        r.magnitude -= r.magnitude * CONTEST_RELIEF * scale
        r.contested = True
    bs.remediation_used += allowed
    label = targets[0].why if targets[0].why else HUM_LABEL
    after = fold_case(state.evidence)
    line = (f"  Counsel files the motion: '{label}' contested, "
            f"-{allowed:.1f} points. Case {before:.0f} → {after:.0f}.")
    if allowed < wanted:
        line += " (The last of the room to argue is spent.)"
    con.say(line)
    _apply_floor(state, before, con)


# ── settlements ───────────────────────────────────────────────────

def settle_targets(state: State) -> list:
    """Who a settlement can reach: any aware employee, current or
    departed, not already settled. Arrested witnesses are beyond hush
    money — their statement is the state's."""
    settled = set(_bs(state).settled_witnesses)
    return [e for e in state.employees
            if e.aware and not e.arrested and e.key not in settled]


def settlement_cost(e: Employee) -> int:
    return SETTLEMENT_WAGE_MULT * e.wage


def settle_witness(state: State, e: Employee, con: Console) -> None:
    """One-time settlement (§2.3 + §3.1 D15): the witness's records are
    permanently halved (capped; nothing below the floor), the name goes
    on the settled roster for the goal term, and a current employee is
    settled OUT — they leave quietly, with no fired-knowing-everything
    record. Severance instead of a witness."""
    if state.game_over:
        return
    bs = _bs(state)
    cost = settlement_cost(e)
    if state.clean < cost:
        con.say(f"  {e.name}'s quiet costs {money(cost)} clean; the till "
                f"holds {money(state.clean)}. Not tonight.")
        return
    state.clean -= cost
    bs.settled_witnesses.append(e.key)
    was_current = e.hired
    if e.hired:
        e.hired = False
        e.resignation_pending = False
    records = [r for r in state.evidence
               if r.kind == "witness" and r.source == e.key]
    before = fold_case(state.evidence)
    # A record already dormant through retention locks in at half
    # weight — sum-neutral, so it happens below the floor and outside
    # the cap: permanence for free (rev. 9 item 4).
    active = [r for r in records if not r.dormant]
    for r in records:
        if r.dormant:
            r.magnitude *= DORMANT_FACTOR
            r.dormant = False
    # New relief is the paid, capped, floor-gated part.
    allowed = 0.0
    if active and before > CASE_FLOOR:
        wanted = sum(r.magnitude for r in active) * (1 - DORMANT_FACTOR)
        allowed = min(wanted, remediation_left(state))
        if wanted > 0 and allowed > 0:
            scale = allowed / wanted
            for r in active:
                r.magnitude -= r.magnitude * (1 - DORMANT_FACTOR) * scale
            bs.remediation_used += allowed
    if was_current:
        con.say(f"  {money(cost)} in an envelope, and {e.name} hangs up the "
                f"apron on their own terms. No scene, no statement — "
                f"severance instead of a witness.")
    else:
        con.say(f"  {money(cost)} finds {e.name} where they landed. What "
                f"they know goes quiet for good.")
    after = fold_case(state.evidence)
    if allowed > 0:
        con.say(f"  Their records go dormant: -{allowed:.1f} points. "
                f"Case {before:.0f} → {after:.0f}.")
    elif active and before <= CASE_FLOOR:
        con.say("  The file is as cold as they will let it get — the "
                "settlement buys peace, not arithmetic.")
    _apply_floor(state, before, con)


# ── retention dormancy ────────────────────────────────────────────

def reconcile_dormancy(state: State, con: Console) -> None:
    """Nightly (in-branch): a current aware employee at morale ≥ 5
    keeps their own records dormant for free — retention as case
    defense (§2.3). Reversible: protection lapses when morale slips or
    the person leaves. New dormancy stops at the floor (an evidence-
    only verb, rev. 9 item 3); a lapse always applies — the file only
    warms freely."""
    if state.game_over:
        return
    settled = set(_bs(state).settled_witnesses)
    by_key = {e.key: e for e in state.employees}
    before = fold_case(state.evidence)
    lapsed: list[str] = []
    protected: list[str] = []
    for r in state.evidence:
        if not r.dormant:
            continue
        e = by_key.get(r.source)
        if e is None or not e.hired or not e.aware \
                or e.morale < DORMANT_MORALE or r.source in settled:
            r.dormant = False
            # A settled source going quiet-for-pay is not a lapse.
            if e is not None and r.source not in settled \
                    and e.name not in lapsed:
                lapsed.append(e.name)
    for r in state.evidence:
        if r.dormant or r.kind != "witness" or not r.source \
                or r.source in settled:
            continue
        e = by_key.get(r.source)
        if e is None or not e.hired or not e.aware \
                or e.morale < DORMANT_MORALE:
            continue
        if fold_case(state.evidence) <= CASE_FLOOR:
            break
        r.dormant = True
        if e.name not in protected:
            protected.append(e.name)
    for name in protected:
        con.say(f"  {name} keeps what they know to themselves — loyalty "
                f"is case defense, while it lasts.")
    for name in lapsed:
        con.say(f"  {name}'s discretion is no longer yours to count on — "
                f"their records wake back up.")
    _apply_floor(state, before, con)
