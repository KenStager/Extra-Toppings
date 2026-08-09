"""Evidence remediation (§2.3, scoped by rev. 9, corrected rev. 10):
counsel, settlements, derived retention protection, the paid-points
cap, the institutional-suspicion floor — and the ledger view the
player actually reads.

The Case remains the clamped sum of its records — every verb here
works by changing what the records say, never by touching a separate
number. Retention protection is NOT state: it derives from the live
roster inside the one context-aware fold (models.fold_case), so a
poach or a morale slip changes the display the moment it happens —
there is no reconciliation event left to go stale. What may touch a
record is answered in exactly one place (models.remediation_
disposition); the contest queue, the settlement verb, the docket and
validation all consume it.

Bounds (§2.3, arithmetic per rev. 9 item 3 / rev. 10): the 25-point
cap binds the PAID verbs — contests and settlements — as points
actually removed, truncating out loud; derived retention relief
allocates in ledger order inside (raw total − floor) and therefore
can never display the sum below the floor by itself. Paid verbs
refuse at or below the floor (a settlement still signs — it buys the
goal term — but relieves nothing, and says both halves of that).
Arrest latched at accrual outranks everything — every entry point is
a no-op on a finished run, and nothing here can un-latch it.
"""

from dataclasses import dataclass

from .models import (CASE_FLOOR, DORMANT_FACTOR, DORMANT_MORALE,
                     REMEDIATION_CAP, BranchState, Employee, Evidence,
                     State, dormant_relief_indices, remediation_disposition)
from .ui import Console, money

COUNSEL_FEE = 150               # $/day, clean (§2.3)
COUNSEL_CONTEST_EVERY = 3       # every 3rd retained day contests
CONTEST_RELIEF = 0.60           # a contested paper record loses 60%
SETTLEMENT_WAGE_MULT = 6        # a settlement costs ~6x daily wage, clean
SUSPICION_WHY = "they remember your name"
HUM_LABEL = "the routine discrepancies"

__all__ = ["COUNSEL_FEE", "COUNSEL_CONTEST_EVERY", "CONTEST_RELIEF",
           "SETTLEMENT_WAGE_MULT", "DORMANT_MORALE", "SUSPICION_WHY",
           "HUM_LABEL", "EvidenceLedgerView", "LedgerLine",
           "build_ledger_view", "counsel_nightly", "contest_next",
           "settle_targets", "settlement_cost", "settle_witness",
           "remediation_left"]


def _bs(state: State) -> BranchState:
    if state.branch_state is None:
        raise ValueError("remediation called outside an active branch")
    return state.branch_state


def remediation_left(state: State) -> float:
    return max(0.0, REMEDIATION_CAP - _bs(state).remediation_used)


def _apply_floor(state: State, before: float, con: Console) -> None:
    """§2.3: whenever a paid verb takes the display below the floor,
    the suspicion record is written, or topped up in place, by exactly
    the difference. Below the floor no retention relief allocates, so
    the display equals the clamped raw sum and the loop is linear (the
    while guards the one-ulp case)."""
    total = state.case
    if total >= CASE_FLOOR or total >= before:
        return
    record = next((r for r in state.evidence if r.kind == "suspicion"), None)
    if record is None:
        record = Evidence(day=state.day, magnitude=0.0, kind="suspicion",
                          why=SUSPICION_WHY)
        state.evidence.append(record)
    while state.case < CASE_FLOOR:
        record.magnitude += CASE_FLOOR - state.case
    con.say(f"  The file thins to the part that never leaves: {SUSPICION_WHY}."
            f" (The sum holds at {CASE_FLOOR:.0f} — the climate cools; it"
            f" does not un-happen.)")


# ── the ledger view (rev. 10 item 3) ──────────────────────────────

@dataclass(frozen=True)
class LedgerLine:
    day: int
    kind: str
    disposition: str          # models.remediation_disposition
    base: float               # the stored magnitude
    effective: float          # what the meter counts tonight
    relieved: bool            # under derived retention protection now
    why: str
    source_name: str          # roster name; "" for external/unattached


@dataclass(frozen=True)
class EvidenceLedgerView:
    """THE case file, itemized: what the meter counts, record by
    record, plus the paid budget, the floor and counsel's next target.
    total is computed by the same context-aware fold as State.case —
    identity by construction, not by copy. Renderers consume this and
    nothing else; they infer no rules."""
    lines: tuple
    total: float
    floor: float
    cap: float
    cap_used: float
    cap_left: float
    counsel_retained: bool
    counsel_days: int
    next_contest: str         # "" when nothing is left to argue


def build_ledger_view(state: State) -> EvidenceLedgerView:
    sources = state.dormant_sources()
    relieved = frozenset(dormant_relief_indices(state.evidence, sources))
    by_key = {e.key: e for e in state.employees}
    lines = []
    for i, r in enumerate(state.evidence):
        protected = i in relieved
        employee = by_key.get(r.source)
        lines.append(LedgerLine(
            day=r.day, kind=r.kind,
            disposition=remediation_disposition(r),
            base=r.magnitude,
            effective=r.magnitude * DORMANT_FACTOR if protected
            else r.magnitude,
            relieved=protected,
            why=r.why,
            source_name=employee.name if employee is not None else ""))
    bs = _bs(state)
    targets = _contest_queue(state)
    return EvidenceLedgerView(
        lines=tuple(lines),
        total=state.case,
        floor=CASE_FLOOR,
        cap=REMEDIATION_CAP,
        cap_used=bs.remediation_used,
        cap_left=remediation_left(state),
        counsel_retained=bs.counsel_retained,
        counsel_days=bs.counsel_days,
        next_contest=(targets[0].why or HUM_LABEL) if targets else "")


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
    §2.3 calls it (rev. 9 item 2). Disposition-driven: only records
    the one disposition function calls contestable ever enter."""
    contestable = [r for r in state.evidence
                   if remediation_disposition(r) == "contestable"
                   and r.magnitude > 0]
    flagged = [r for r in contestable if r.why]
    if flagged:
        return [flagged[0]]
    return [r for r in contestable if not r.why]


def contest_next(state: State, con: Console) -> None:
    if state.game_over:
        return
    bs = _bs(state)
    targets = _contest_queue(state)
    if not targets:
        con.say("  Counsel reads the file again and shrugs: nothing left "
                "worth arguing. The retainer keeps the books honest.")
        return
    before = state.case
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
    after = state.case
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
    """One-time settlement (§2.3 + §3.1 D15): one result, two outcomes
    stated separately (rev. 10 item 6) — the RELATIONSHIP (the name
    goes on the settled roster; a current employee leaves quietly,
    with no fired-knowing-everything record) and the EVIDENCE (relief
    applied / truncated at the cap / cap exhausted / floor-bound /
    nothing in the file / permanence locked in for free). Every path
    says both."""
    if state.game_over:
        return
    bs = _bs(state)
    cost = settlement_cost(e)
    if state.clean < cost:
        con.say(f"  {e.name}'s quiet costs {money(cost)} clean; the till "
                f"holds {money(state.clean)}. Not tonight.")
        return
    # Derive the CURRENT relief allocation before anything mutates —
    # records it already halves lock in for free (effective weight
    # unchanged, no cap charge); the rest is the paid part.
    relieved = set(dormant_relief_indices(state.evidence,
                                          state.dormant_sources()))
    records = [(i, r) for i, r in enumerate(state.evidence)
               if remediation_disposition(r) == "settleable"
               and r.source == e.key]
    before = state.case
    state.clean -= cost
    was_current = e.hired
    if e.hired:
        e.hired = False
        e.resignation_pending = False
    bs.settled_witnesses.append(e.key)
    for i, r in records:
        if i in relieved:
            r.magnitude *= DORMANT_FACTOR
    active = [r for i, r in records if i not in relieved]
    wanted = sum(r.magnitude for r in active) * (1 - DORMANT_FACTOR)
    room = remediation_left(state)
    applied = 0.0
    if not records:
        evidence_outcome = "no_records"
    elif not active:
        evidence_outcome = "locked_free"
    elif before <= CASE_FLOOR:
        evidence_outcome = "floor"
    elif room <= 0:
        evidence_outcome = "cap_exhausted"
    else:
        applied = min(wanted, room)
        scale = applied / wanted
        for r in active:
            r.magnitude -= r.magnitude * (1 - DORMANT_FACTOR) * scale
        bs.remediation_used += applied
        evidence_outcome = "applied" if applied == wanted else "truncated"
    # The relationship, first — it happened regardless of arithmetic.
    if was_current:
        con.say(f"  {money(cost)} in an envelope, and {e.name} hangs up the "
                f"apron on their own terms. No scene, no statement — "
                f"severance instead of a witness.")
    else:
        con.say(f"  {money(cost)} finds {e.name} where they landed. The "
                f"engagement is settled; their peace is bought.")
    # The evidence, second — exactly what the money did to the file.
    after = state.case
    if evidence_outcome == "applied":
        con.say(f"  Their records go dormant for good: -{applied:.1f} "
                f"points. Case {before:.0f} → {after:.0f}.")
    elif evidence_outcome == "truncated":
        con.say(f"  Their records soften -{applied:.1f} of the "
                f"{wanted:.1f} the halving was worth — the cap allowed "
                f"no more. Case {before:.0f} → {after:.0f}.")
    elif evidence_outcome == "cap_exhausted":
        con.say("  The file does not move: every point the cap allows "
                "is already spent. The engagement is settled; the "
                "evidence is not.")
    elif evidence_outcome == "floor":
        con.say("  The file is as cold as they will let it get — the "
                "settlement buys peace, not arithmetic.")
    elif evidence_outcome == "locked_free":
        con.say("  Their silence was already holding the file down; now "
                "it is permanent, and no longer depends on their mood.")
    else:
        con.say("  Nothing in the file carries their name — the money "
                "buys certainty, not arithmetic.")
    _apply_floor(state, before, con)
