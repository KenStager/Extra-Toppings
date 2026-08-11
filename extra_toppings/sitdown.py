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

from . import data, models, partner, straight
from .config import GameConfig
from .models import (BRANCH_ORDER, BranchState, SitdownSnapshot, State,
                     case_prefix, fold_case, validate_branch_state)
from .ui import Console, money

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


# The live file at which open chairs become visibly dangerous — present
# danger keys to the LIVE Case; eligibility keys to the frozen one.
DANGER_CASE = 85.0


@dataclass(frozen=True)
class ChairVerdict:
    chair: str
    available: bool
    # Structured gate facts (rev. 6, completed at the rendering
    # boundary): None when seated; "calendar" beats "case" when both
    # gates fail — pinned precedence, one prose reason. A failed gate
    # carries its requirement AND what the player actually had, so the
    # scene can state the math in player language.
    blocker: str | None = None
    requirement: float | None = None  # min R (calendar) / the Case gate (case)
    actual: float | None = None       # R remaining / the Case at lock-up
    case_gate: float | None = None    # the chair's Case gate, seated or not
    reason: str = ""                  # withholding line when empty; "" seated
    closed_by: str = ""               # the record that shut a Case gate


@dataclass(frozen=True)
class SitdownView:
    """The one canonical view the scene renders from (rev. 6): frozen
    eligibility, live risk, and whether live conditions would alter the
    offers — the renderer consumes this and nothing else."""
    frozen_case: float
    frozen_verdicts: tuple
    live_case: float
    offers_would_change: bool     # live conditions would re-verdict chairs

    @property
    def frozen_band(self) -> str:
        return case_band(self.frozen_case)

    @property
    def live_band(self) -> str:
        return case_band(self.live_case)

    @property
    def live_danger(self) -> bool:
        """Present danger belongs to the live file, not the frozen one."""
        return self.live_case >= DANGER_CASE


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
    scanning only the first `count` records (the lock-up ledger).
    Consumes the shared prefix iterator (rev. 9 item 15) — the same
    arithmetic as State.case, so 'crossed' agrees with the meter.
    Routine flagless ticks fall back to a generic description."""
    for record, running in case_prefix(evidence[:count]):
        if running >= gate:
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
        gate = CASE_GATE.get(chair)
        if r < MIN_R[chair]:
            verdicts.append(ChairVerdict(
                chair, False, blocker="calendar",
                requirement=float(MIN_R[chair]), actual=float(r),
                case_gate=gate, reason=CALENDAR_REASONS[chair]))
            continue
        if gate is not None and case >= gate:
            reason = ("nobody invests in a burning building — he sends "
                      "a nephew instead of coming"
                      if chair == "partner"
                      else "any buyer's diligence would subpoena itself")
            verdicts.append(ChairVerdict(
                chair, False, blocker="case", requirement=gate, actual=case,
                case_gate=gate, reason=reason,
                closed_by=gate_crossing_record(evidence, count, gate)))
            continue
        verdicts.append(ChairVerdict(chair, True, case_gate=gate))
    verdicts.append(ChairVerdict("stand_pat", True))
    return verdicts


def build_view(snapshot: SitdownSnapshot, evidence: list) -> SitdownView:
    """Frozen verdicts from the snapshot; the live Case from the full
    ledger through fold_case — the same arithmetic as State.case, by
    construction rather than by copy (rev. 6 completion)."""
    live = fold_case(evidence)
    frozen = tuple(evaluate_chairs(snapshot, evidence))
    live_verdicts = evaluate_chairs(SitdownSnapshot(
        payoff_day=snapshot.payoff_day, case_at_lockup=live,
        evidence_count_at_lockup=len(evidence)), evidence)
    return SitdownView(
        frozen_case=snapshot.case_at_lockup,
        frozen_verdicts=frozen,
        live_case=live,
        offers_would_change=[v.available for v in frozen]
        != [v.available for v in live_verdicts])


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
    if any(rv.alive and (rv.raid_warning > 0
                         or rv.relation <= models.VENDETTA_RELATION)
           for rv in state.rivals.values()):
        con.say("  Unfamiliar cars idle across the street the whole meal. "
                "Carmine glances at them once and decides they can wait.")

    # From here down the renderer consumes the view and nothing else —
    # no re-evaluation, no reaching into gate tables (rev. 6 completion).
    view = build_view(snap, state.evidence)
    con.say(f"  The debt died on day {snap.payoff_day}. {r} days remain, "
            f"and the offers were cut from {view.frozen_band} "
            f"({view.frozen_case:.0f}/100 when the books closed).")
    # Invariant 8 + rev. 6: every difference between the lock-up ledger
    # and the live morning file is rendered, threshold or no threshold.
    if view.live_case != view.frozen_case:
        coda = ("Last night didn't help — but the offers stand."
                if view.offers_would_change else
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
            gate_note = (f" (open while the file reads under "
                         f"{v.case_gate:.0f})"
                         if v.case_gate is not None else "")
            marker = ("" if chair in config.enabled_branches
                      else "  [not in this build]")
            con.bullet(f"{CHAIR_LABELS[chair]}{gate_note}{marker}")
        else:
            # A failed gate is stated in-scene, in player language, with
            # the math: what it required and what the player had.
            con.bullet(f"{CHAIR_LABELS[chair].split(' — ')[0]} — an empty "
                       f"chair: {v.reason}.")
            if v.blocker == "calendar":
                con.say(f"      The math: it needed {v.requirement:.0f} "
                        f"days on the calendar; {v.actual:.0f} remain.")
            else:
                con.say(f"      The math: it required a file below "
                        f"{v.requirement:.0f}; yours read {v.actual:.0f} "
                        f"when the books closed.")
                if v.closed_by:
                    con.say(f"      What closed it: {v.closed_by}.")
    if view.live_danger:
        # §2.1: open chairs at a near-closed file are visibly dangerous —
        # keyed to the LIVE file (eligibility stays frozen; danger is a
        # fact about this morning, not about closing time).
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
        if chair == "straight":
            con.say("  Carmine slides a folded thing across the table: "
                    "your own coded-customer book, bought back from a "
                    "man who found it. 'A gift. Whichever way it goes "
                    "in the oven.'")
            confirmed = con.scene_menu(
                NAMESPACE,
                "Take the Straight Path? The book burns this morning.",
                ["Reconsider", "Burn the book — wind it down"])
            if confirmed == 0:
                continue
            branch_state = BranchState.straight()
            validate_branch_state("straight", branch_state)
            state.branch_state = branch_state
            state.branch = "straight"
            state.act = 2
            straight.entry_scene(state, con)
            return
        if chair == "quiet_sale":
            sal = state.rivals.get("sal")
            buyer = ("Sal's man with the clean fingernails — a straw "
                     "purchase, and everyone at this table knows it"
                     if sal is not None and sal.alive and sal.relation >= 0
                     else "an out-of-town operator who asks very few "
                     "questions")
            con.say(f"  The buyer at the table's edge: {buyer}.")
            confirmed = con.scene_menu(
                NAMESPACE,
                "Take the Quiet Sale? His man walks the shop this afternoon.",
                ["Reconsider", "Shake on it — the week starts now"])
            if confirmed == 0:
                continue
            branch_state = BranchState.quiet_sale(diligence_day=1)
            validate_branch_state("quiet_sale", branch_state)
            state.branch_state = branch_state
            state.branch = "quiet_sale"
            state.act = 2
            con.say("  A handshake, no papers yet. Today is diligence day "
                    "one of four; closing is the morning after day four, "
                    "and the register had better be boring all week.")
            return
        if chair == "partner":
            con.say("  Carmine puts a folded napkin on the table with a "
                    "number on it. 'Twenty. Not a loan — I don't lend to "
                    "family twice. A second room, my contractor, my "
                    "schedule. You run it, I take points.'")
            # The cards read safe to dangerous, and that order is the
            # STORY's (rev. 31 item 2): the Partner bot and every
            # ablation name their district by identity, never by index,
            # so this order decides what a player reads and nothing a
            # study measures. Reconsider is first, so the last option
            # is a real site and the deterministic last-option bot
            # always seats a deal — landing on Vinnie's floor, which
            # is CHAOS COVERAGE of territorial retaliation and not
            # anybody's study policy.
            site_options = ["Reconsider"] + [
                partner.site_label(d) for d in partner.SITE_DISTRICTS]
            picked = con.scene_menu(
                NAMESPACE, "Where does the second room go?", site_options)
            if picked == 0:
                continue
            district = partner.SITE_DISTRICTS[picked - 1]
            confirmed = con.scene_menu(
                NAMESPACE,
                f"Open on {data.DISTRICTS[district]['label']}? "
                f"{money(partner.COMMITTED)} commits this morning and "
                f"the points clock starts.",
                ["Reconsider", "Shake on it — his contractor starts today"])
            if confirmed == 0:
                continue
            # ONE act: the address, its wagon, the committed capital
            # and the points clock. Nothing is assigned before it —
            # the branch fields are set inside the transaction, so a
            # refusal leaves the table exactly as it was.
            shop = partner.accept_deal(state, district)
            partner.entry_scene(state, shop, con)
            return
        if chair == "war":
            live_rivals = [k for k, r in state.rivals.items() if r.alive]
            if not live_rivals:
                con.say("  There is no war left to declare — the city's "
                        "other operators are already gone.")
                continue
            con.say("  Carmine looks at the window, then at you. 'Name "
                    "one. Not two — one. The other will pick a side "
                    "by who he is.'")
            # Target naming rides the scene channel like every other
            # sit-down decision; every option but the first progresses,
            # so the deterministic last-option bot always seats a war.
            name_options = ["Reconsider"] + [
                f"Name {data.RIVALS[k]['label']} — strength "
                f"{state.rivals[k].strength:g}, "
                f"{data.RIVALS[k]['style']}" for k in live_rivals]
            named = con.scene_menu(NAMESPACE, "Whose name goes on the "
                                   "table?", name_options)
            if named == 0:
                continue
            target = live_rivals[named - 1]
            confirmed = con.scene_menu(
                NAMESPACE,
                f"Declare the Harbor War on "
                f"{data.RIVALS[target]['short']}? Their relation locks "
                f"at vendetta — no truce, ever.",
                ["Reconsider", "Declare — the war starts this morning"])
            if confirmed == 0:
                continue
            branch_state = BranchState.war(
                war_target=target, declared_day=state.day,
                starting_strength=state.rivals[target].strength)
            validate_branch_state("war", branch_state)
            state.branch_state = branch_state
            state.branch = "war"
            state.act = 2
            # The lock binds the moment the campaign exists (the
            # relation authority reads the campaign list).
            models.set_relation(
                state, target, min(state.rivals[target].relation,
                                   models.VENDETTA_RELATION))
            from . import war as war_mod
            war_mod.entry_scene(state, con)
            return
        # A branch both seated and enabled commits above — anything else
        # reaching here is a configuration error, and it fails loudly
        # rather than quietly becoming stand-pat.
        raise NotImplementedError(
            f"branch {chair!r} is enabled but has no commit path yet")
