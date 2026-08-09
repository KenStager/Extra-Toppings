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
                     State, dormant_relief, remediation_disposition,
                     witness_status)
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
        # A top-up is genuine accrual (rev. 16): both move in lockstep.
        diff = CASE_FLOOR - state.case
        record.magnitude += diff
        record.accrued = (record.accrued or 0.0) + diff
    con.say(f"  The file thins to the part that never leaves: {SUSPICION_WHY}."
            f" (The sum holds at {CASE_FLOOR:.0f} — the climate cools; it"
            f" does not un-happen.)")


# ── the ledger view (rev. 10 item 3) ──────────────────────────────

@dataclass(frozen=True)
class LedgerLine:
    day: int
    kind: str
    disposition: str          # models.remediation_disposition, with state
    base: float               # the stored magnitude (grouped: the sum)
    effective: float          # what the meter counts tonight
    relieved: bool            # under derived retention relief now
    partial: bool             # the relief is floor-limited, not the half
    why: str
    source_name: str          # roster name; "" for external/unattached
    count: int = 1            # grouped lines carry their entry count


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
    # Why counsel can or cannot move next (rev. 11 item 3): "target"
    # names next_contest; "empty" / "floor" / "cap" say exactly why no
    # contest can occur — the docket never names a target that cannot
    # be argued.
    contest_state: str
    next_contest: str


def build_ledger_view(state: State) -> EvidenceLedgerView:
    cuts = dict(dormant_relief(state.evidence, state.dormant_sources()))
    by_key = {e.key: e for e in state.employees}
    placed = []           # (ledger position, LedgerLine)
    hum_pos = -1
    hum_count = 0
    hum_base = 0.0
    hum_first_day = 0
    hum_open = False      # any tick still contestable
    for i, r in enumerate(state.evidence):
        if r.kind == "paper" and not r.why:
            # Storage stays per-tick (float identity, round 6); the
            # DISPLAY groups the hum into one line (rev. 11 item 3).
            if hum_pos < 0:
                hum_pos = i
                hum_first_day = r.day
            hum_count += 1
            hum_base += r.magnitude
            hum_open = hum_open or (not r.contested and r.magnitude > 0)
            continue
        cut = cuts.get(i, 0.0)
        employee = by_key.get(r.source)
        placed.append((i, LedgerLine(
            day=r.day, kind=r.kind,
            disposition=remediation_disposition(r, state),
            base=r.magnitude,
            effective=r.magnitude - cut,
            relieved=cut > 0,
            partial=0 < cut < r.magnitude * (1 - DORMANT_FACTOR),
            why=r.why,
            source_name=employee.name if employee is not None else "")))
    if hum_count:
        placed.append((hum_pos, LedgerLine(
            day=hum_first_day, kind="paper",
            disposition="contestable" if hum_open else "contested",
            base=hum_base, effective=hum_base, relieved=False,
            partial=False, why=HUM_LABEL, source_name="",
            count=hum_count)))
    placed.sort(key=lambda pair: pair[0])
    bs = _bs(state)
    targets = _contest_queue(state)
    if not targets:
        contest_state, next_contest = "empty", ""
    elif state.case <= CASE_FLOOR:
        contest_state, next_contest = "floor", ""
    elif remediation_left(state) <= 0:
        contest_state, next_contest = "cap", ""
    else:
        contest_state = "target"
        next_contest = targets[0].why or HUM_LABEL
    return EvidenceLedgerView(
        lines=tuple(line for _pos, line in placed),
        total=state.case,
        floor=CASE_FLOOR,
        cap=REMEDIATION_CAP,
        cap_used=bs.remediation_used,
        cap_left=remediation_left(state),
        counsel_retained=bs.counsel_retained,
        counsel_days=bs.counsel_days,
        contest_state=contest_state,
        next_contest=next_contest)


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
    """Who a settlement can reach, straight from the one relationship
    authority (rev. 11 item 2): reachable and protected witnesses —
    a protected current witness settles OUT, locking the retention
    half in for good. Settled names and the arrested (their statement
    is the state's) never appear."""
    return [e for e in state.employees
            if e.aware and witness_status(state, e.key)
            in ("reachable", "protected")]


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
    # Derive the CURRENT relief allocation before anything mutates
    # (rev. 11: per-record, possibly partial). The cut a record is
    # already receiving locks in for free — effective weight
    # unchanged, no cap charge; the rest of the halving is paid.
    cuts = dict(dormant_relief(state.evidence, state.dormant_sources()))
    records = [(i, r) for i, r in enumerate(state.evidence)
               if r.kind == "witness" and r.source == e.key]
    before = state.case
    state.clean -= cost
    was_current = e.hired
    if e.hired:
        e.hired = False
        e.resignation_pending = False
    bs.settled_witnesses.append(e.key)
    # paid_parts: what full permanence would still remove per record,
    # beyond tonight's free cut (half the magnitude minus the cut).
    paid_parts = []
    locked_any = False
    for i, r in records:
        cut = cuts.get(i, 0.0)
        paid = r.magnitude * (1 - DORMANT_FACTOR) - cut
        if cut > 0:
            r.magnitude -= cut          # the free lock, display-neutral
            locked_any = True
        paid_parts.append((r, paid))
    wanted = sum(paid for _r, paid in paid_parts)
    room = remediation_left(state)
    applied = 0.0
    if not records:
        evidence_outcome = "no_records"
    elif before <= CASE_FLOOR:
        evidence_outcome = "floor"
    elif wanted <= 0:
        evidence_outcome = "locked_free" if locked_any else "no_records"
    elif room <= 0:
        evidence_outcome = "cap_exhausted"
    else:
        applied = min(wanted, room)
        scale = applied / wanted
        for r, paid in paid_parts:
            if paid > 0:
                r.magnitude -= paid * scale
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


# ── the shared remediation UI (rev. 14 item 8) ────────────────────
# Moved here from straight.py: every branch the capability policy
# unlocks renders the same docket and spends the same verbs — no
# branch-specific wrappers, no parallel copies.

_DISPOSITION_NOTES = {
    "contestable": "counsel can argue this",
    "contested": "already argued down",
    "settleable": "a settlement can reach this",
    "settled": "their peace is bought",
    "beyond_reach": "in custody — the statement is the state's",
    "external": "outside provenance — no settlement reaches it",
    "immune": "what the city saw, it saw",
    "suspicion": "permanent — they remember your name",
}

_CONTEST_STATES = {
    "empty": "nothing left worth arguing",
    "floor": "the floor holds — nothing to argue below it",
    "cap": "cap exhausted — every point the cap allows is spent",
}


def show_case_file(state: State, con: Console) -> None:
    """The docket: renders the EvidenceLedgerView and nothing else —
    every number comes from the view, and the view's total IS the
    meter (same fold, same context)."""
    view = build_ledger_view(state)
    con.say("")
    con.say(f"  THE CASE FILE — reads {view.total:.1f}/100 tonight "
            f"(the floor under any lawyering: {view.floor:.0f}).")
    if not view.lines:
        con.say("  The file is empty. Keep it that way.")
        return
    for line in view.lines:
        label = line.why
        if line.count > 1:
            label += f" ({line.count} entries, rolled up)"
        if line.relieved and line.partial:
            weight = (f"{line.base:.1f} → counts {line.effective:.1f} "
                      f"({line.source_name}'s loyalty holds part of it "
                      f"down; the floor limits the rest)")
        elif line.relieved:
            weight = (f"{line.base:.1f} → counts {line.effective:.1f} "
                      f"({line.source_name}'s loyalty holds it down)")
        else:
            weight = f"counts {line.effective:.1f}"
        who = f" — {line.source_name}" if line.source_name else ""
        con.say(f"    · day {line.day} · {line.kind} · {weight} · "
                f"{label}{who} [{_DISPOSITION_NOTES[line.disposition]}]")
    con.say(f"  Remedy spent {view.cap_used:.1f} of {view.cap:.0f} "
            f"points; {view.cap_left:.1f} left to argue or settle.")
    if view.counsel_retained:
        status = (f"next in the queue: '{view.next_contest}'"
                  if view.contest_state == "target"
                  else _CONTEST_STATES[view.contest_state])
        con.say(f"  Counsel retained, day {view.counsel_days} — {status}.")
    else:
        con.say("  No counsel retained — the paper stands unargued.")


def counsel_label(state: State) -> str:
    if _bs(state).counsel_retained:
        return ("Dismiss counsel — the retainer ends tonight; the ceiling "
                "is yours to break again.")
    return (f"Retain counsel — {money(COUNSEL_FEE)}/day clean. "
            f"Contests the file every third day; enforces the ceiling "
            f"while retained.")


def toggle_counsel(state: State, con: Console) -> None:
    bs = _bs(state)
    if bs.counsel_retained:
        bs.counsel_retained = False
        con.say("  The engagement letter goes back in its envelope. The "
                "file is yours again — all of it.")
        return
    bs.counsel_retained = True
    con.say(f"  A lawyer with harbor-view offices takes the retainer "
            f"({money(COUNSEL_FEE)}/day, clean, nightly). Their "
            f"one condition: the books make sense while they work — no "
            f"washing past the ceiling. Counsel's office sees the tapes.")


def settle_menu(state: State, con: Console) -> None:
    """The night action: buy a witness's quiet (§2.3, rev. 9 item 4).
    Departed witnesses list first; a current name on this list is
    settled OUT — severance instead of a witness."""
    targets = sorted(settle_targets(state),
                     key=lambda e: (e.hired, e.key))
    if not targets:
        con.say("  Nobody left to settle with — everyone who knows is "
                "either paid, content, or beyond reach.")
        return
    labels = []
    for e in targets:
        status = ("still on payroll — settling means they leave, quietly"
                  if e.hired else f"departed, morale {e.morale}")
        labels.append(f"{e.name} ({status}) — "
                      f"{money(settlement_cost(e))} clean")
    labels.append("Back")
    pick = con.menu("Whose quiet do you buy?", labels)
    if pick < len(targets):
        settle_witness(state, targets[pick], con)
