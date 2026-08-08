"""The Sit-Down: the morning after payoff, once, in Carmine's restaurant.

Everything here is deterministic and draws zero RNG. Chair eligibility
was frozen at lock-up on payoff night (SitdownSnapshot, §2.1 rev. 4);
this module derives the rest — R, every chair's availability, the
structured blocker, the withholding reasons, the evidence record that
closed a Case gate — from that snapshot and the evidence ledger, never
storing a second copy (rev. 5: one source of truth). The canonical
SitdownView (rev. 6) carries BOTH the frozen ledger the offers were cut
from and the live morning Case, and the scene renders every difference
between them, whether or not a threshold moved.

Scene decisions ride the namespaced scene_menu console channel so the
gameplay decision log stays byte-identical to a fork-off run (§2.7
criterion 6, the two-trace contract). Bot consoles answer scene menus
deterministically by taking the LAST option — every scene menu here
must therefore keep its progressing choice (stand pat / the confirming
answer) in last position. The harness holds the stand-pat interaction
to a frozen literal schema (analysis/equivalence.py); changing any
scene prompt or option below is a deliberate act that lands together
with a schema version bump there.
"""

from dataclasses import dataclass

from .config import GameConfig
from .models import (BRANCH_ORDER, SitdownSnapshot, State,
                     validate_branch_state)
from .ui import Console

NAMESPACE = "sitdown"

# Calendar gates, §2.1: minimum R (days remaining including the sit-down
# morning, R = 30 − payoff_day) for a chair to be seated at all.
MIN_R = {"straight": 5, "partner": 10, "war": 8, "quiet_sale": 5}
# Case gates, §2.1: the file must read below this or the chair empties.
CASE_GATE = {"partner": 70.0, "quiet_sale": 85.0}
# R ≤ NO_SITDOWN_R: no scene at all — a line of respect, then the
# endgame the player already knows.
NO_SITDOWN_R = 4

CHAIR_LABELS = {
    "straight": "The Straight Path — wind it down, sell nothing, exit whole",
    "partner": "Carmine's Partner — a second shop on his money, points on his schedule",
    "war": "The Harbor War — take the city, one rival at a time",
    "quiet_sale": "The Quiet Sale — a buyer, an escrow week, a clean walk away",
    "stand_pat": "Stand pat — thank them all, keep what's yours",
}

CALENDAR_REASONS = {
    "straight": "you can't launder a reputation in a weekend",
    "partner": "no time to build anything now",
    "war": "wars outlive months",
    "quiet_sale": "too few days for even a fast close",
}


@dataclass(frozen=True)
class ChairVerdict:
    chair: str
    available: bool
    # Structured blocker (rev. 6): None when seated; "calendar" beats
    # "case" when both gates fail — pinned precedence, one prose reason.
    blocker: str | None = None
    threshold: float | None = None   # the Case gate, when blocker == "case"
    reason: str = ""                 # withholding line when empty; "" seated
    closed_by: str = ""              # the record that shut a Case gate


@dataclass(frozen=True)
class SitdownView:
    """The one canonical view the scene renders from (rev. 6): the
    frozen ledger the offers were cut from, and the live morning file —
    never conflated, both always present."""
    frozen_case: float
    frozen_verdicts: tuple
    live_case: float

    @property
    def frozen_band(self) -> str:
        return case_band(self.frozen_case)

    @property
    def live_band(self) -> str:
        return case_band(self.live_case)


def days_remaining(snapshot: SitdownSnapshot) -> int:
    """R: days left including the sit-down morning (§2.1 base rule)."""
    return 30 - snapshot.payoff_day


def case_band(case: float) -> str:
    if case < 30:
        return "a quiet file"
    if case < 60:
        return "a warm file"
    if case < 70:
        return "a hot file"
    if case < 85:
        return "a burning file"
    return "a file nearly closed"


def gate_crossing_record(evidence: list, count: int, gate: float) -> str:
    """The why-text of the record whose prefix sum first reached `gate`,
    scanning only the first `count` records (the lock-up ledger). Same
    left-to-right fold as State.case, so 'crossed' agrees with the
    meter. Routine flagless ticks fall back to a generic description."""
    total = 0.0
    for record in evidence[:count]:
        total += record.magnitude
        if total >= gate:
            return record.why or "the register's quiet accumulation"
    return ""


def evaluate_chairs(snapshot: SitdownSnapshot,
                    evidence: list) -> list[ChairVerdict]:
    """The complete computed offer set (§2.7 criterion 2) — all four
    chairs plus stand-pat, judged on the lock-up snapshot alone."""
    r = days_remaining(snapshot)
    case = snapshot.case_at_lockup
    count = snapshot.evidence_count_at_lockup
    verdicts = []
    for chair in BRANCH_ORDER:
        if r < MIN_R[chair]:
            verdicts.append(ChairVerdict(
                chair, False, blocker="calendar",
                reason=CALENDAR_REASONS[chair]))
            continue
        gate = CASE_GATE.get(chair)
        if gate is not None and case >= gate:
            reason = ("nobody invests in a burning building — he sends "
                      "a nephew instead of coming"
                      if chair == "partner"
                      else "any buyer's diligence would subpoena itself")
            verdicts.append(ChairVerdict(
                chair, False, blocker="case", threshold=gate, reason=reason,
                closed_by=gate_crossing_record(evidence, count, gate)))
            continue
        verdicts.append(ChairVerdict(chair, True))
    verdicts.append(ChairVerdict("stand_pat", True))
    return verdicts


def build_view(snapshot: SitdownSnapshot, evidence: list) -> SitdownView:
    """Frozen verdicts from the snapshot; the live Case from the full
    ledger, folded exactly like State.case."""
    total = 0.0
    for record in evidence:
        total += record.magnitude
    live = max(0.0, min(100.0, total))
    return SitdownView(
        frozen_case=snapshot.case_at_lockup,
        frozen_verdicts=tuple(evaluate_chairs(snapshot, evidence)),
        live_case=live)


def due(state: State) -> bool:
    """Whether the sit-down scene fires this morning. State-only — the
    launch configuration never gates continuation (rev. 5): a save with
    a pending snapshot resumes into its scene whatever the flags say."""
    return (state.sitdown_snapshot is not None
            and state.branch is None
            and state.game_over is None
            and state.day == state.sitdown_snapshot.payoff_day + 1)


def run_scene(state: State, con: Console, config: GameConfig) -> None:
    """Deterministic, atomic: no state mutation before the final
    selection, so reloading a save taken before the choice simply
    replays the scene. Draws zero RNG."""
    snap = state.sitdown_snapshot
    if snap is None:            # guarded by due(); belt for direct calls
        return
    r = days_remaining(snap)

    if r <= NO_SITDOWN_R:
        # Payoff day 26 or later: the month is spent. The day-24 warning
        # told the player exactly where this line was.
        con.say("  Carmine sends a bottle with a note: 'Your uncle would "
                "not have managed it. Respect.' There is no table to sit "
                "at — whatever you are on day 30 is what you'll be.")
        return

    con.header("THE SIT-DOWN — Carmine's restaurant, before the lunch crowd")
    if snap.payoff_day <= 7:
        con.say("  Carmine stands when you come in. He does not do that. "
                "'Paid in a week. I have known men thirty years I trust "
                "less.' The offer he makes will remember this morning.")
    if any(rv.alive and (rv.raid_warning > 0 or rv.relation <= -60)
           for rv in state.rivals.values()):
        con.say("  Unfamiliar cars idle across the street the whole meal. "
                "Carmine glances at them once and decides they can wait.")

    view = build_view(snap, state.evidence)
    con.say(f"  The debt died on day {snap.payoff_day}. {r} days remain, "
            f"and the offers were cut from {view.frozen_band} "
            f"({view.frozen_case:.0f}/100 when the books closed).")
    # Invariant 8 + rev. 6: every difference between the lock-up ledger
    # and the live morning file is rendered, threshold or no threshold.
    if view.live_case != view.frozen_case:
        offers_moved = (
            [v.available for v in view.frozen_verdicts]
            != [v.available for v in
                evaluate_chairs(SitdownSnapshot(
                    payoff_day=snap.payoff_day,
                    case_at_lockup=view.live_case,
                    evidence_count_at_lockup=len(state.evidence)),
                    state.evidence)])
        coda = ("Last night didn't help — but the offers stand."
                if offers_moved else
                "The chairs were set at closing time.")
        con.say(f"  (The file has warmed since the books closed — it reads "
                f"{view.live_band} this morning, {view.live_case:.0f}, "
                f"not {view.frozen_case:.0f}. {coda})")

    by_chair = {v.chair: v for v in view.frozen_verdicts}
    con.say("")
    con.say("  Four chairs at the table, and the one you came in with:")
    for chair in BRANCH_ORDER:
        v = by_chair[chair]
        if v.available:
            gate = CASE_GATE.get(chair)
            gate_note = (f" (open while the file reads under {gate:.0f})"
                         if gate is not None else "")
            marker = ("" if chair in config.enabled_branches
                      else "  [not in this build]")
            con.bullet(f"{CHAIR_LABELS[chair]}{gate_note}{marker}")
        else:
            con.bullet(f"{CHAIR_LABELS[chair].split(' — ')[0]} — an empty "
                       f"chair: {v.reason}.")
            if v.closed_by:
                con.say(f"      What closed it: {v.closed_by}.")
    if view.frozen_case >= 85.0:
        # §2.1: open chairs at a near-closed file are visibly dangerous —
        # the scene says so rather than letting "open" read as "wise".
        if by_chair["straight"].available:
            con.say("      With the file this hot, the Straight Path is "
                    "the natural play — and maybe a dignified way to lose.")
        if by_chair["war"].available:
            con.say("      Declaring the war now is legal, and "
                    "near-suicidal — the law finishes whoever wins.")
    con.say("")
    con.say("  The offers are live while everyone is at the table, and "
            "only then. Choosing one dismisses the rest for good — and "
            "standing pat dismisses them all. Carmine does not ask twice; "
            "the buyer buys elsewhere.")

    options = [CHAIR_LABELS[c] for c in BRANCH_ORDER] + \
              [CHAIR_LABELS["stand_pat"]]   # stand pat LAST: bot invariant
    order = BRANCH_ORDER + ("stand_pat",)
    while True:
        pick = con.scene_menu(NAMESPACE, "Your chair:", options)
        chair = order[pick]
        v = by_chair[chair]
        if not v.available:
            con.say(f"  That chair is empty — {v.reason}.")
            continue
        if chair != "stand_pat" and chair not in config.enabled_branches:
            con.say(f"  [development build: '{chair}' is rendered but not "
                    f"yet playable — it arrives in a later phase. "
                    f"Choosing it is disabled so this build's limitation "
                    f"can't become your permanent decision.]")
            continue
        if chair == "stand_pat":
            confirmed = con.scene_menu(
                NAMESPACE,
                "Stand pat? The table clears for good.",
                ["Reconsider", "Let them go — I keep what's mine"])
            if confirmed == 0:
                continue
            validate_branch_state("stand_pat", None)
            state.branch = "stand_pat"
            state.act = 2
            con.say("  Carmine finishes his espresso and shakes your hand "
                    "like a door closing. 'The shop is yours. The city is "
                    "what it is.' Nobody mentions the table again.")
            return
        # A branch both seated and enabled commits here — P1b and later.
        # Reaching this in a P1a build is a configuration error, and it
        # fails loudly rather than quietly becoming stand-pat.
        raise NotImplementedError(
            f"branch {chair!r} is enabled but has no commit path yet")
