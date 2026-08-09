"""Mutable game state: people, places, money, evidence."""

from dataclasses import dataclass, field, fields

from . import data


@dataclass
class Employee:
    key: str
    name: str
    role: str
    food: int
    driving: int
    nerve: int
    loyalty: int
    trait: str
    wage: int
    bio: str
    hired: bool = False
    aware: bool = False          # read in on the real business
    morale: int = 6              # 0-10
    injured_days: int = 0
    arrested: bool = False
    routes_survived: int = 0
    familiarity: dict = field(default_factory=dict)   # district -> routes driven there
    resignation_pending: bool = False    # confronted you; one chance to fix it

    @property
    def available(self) -> bool:
        return self.hired and not self.arrested and self.injured_days == 0

    def tag(self) -> str:
        bits = [self.role]
        if self.aware:
            bits.append("read in")
        if self.injured_days:
            bits.append(f"hurt {self.injured_days}d")
        if self.arrested:
            bits.append("IN CUSTODY")
        return ", ".join(bits)


@dataclass
class District:
    key: str
    heat: float = 10.0            # 0-100 immediate attention
    known_price_age: int = 99     # days since player had firsthand prices
    sold_yesterday: dict = field(default_factory=dict)   # good -> units (price depression)


@dataclass
class Rival:
    key: str
    strength: float
    relation: float = -10.0       # -100 vendetta … +100 partner
    tribute_demanded: int = 0
    raid_warning: int = 0         # days until their telegraphed raid (0 = none)
    ledger_stolen: bool = False
    ovens_wrecked_days: int = 0
    alertness: float = 0.0        # 0-10: how hard their security has learned
    last_raided_day: int = -99    # alertness decays only on quiet days

    @property
    def alive(self) -> bool:
        return self.strength > 0


@dataclass
class ActiveEvent:
    spec: dict
    days_left: int


# A retention-protected witness record counts at half weight (§2.3) —
# the one factor shared by the fold, the ledger view, and the
# settlement arithmetic. The floor and cap are the §2.3 bounds:
# remediation never displays the sum below CASE_FLOOR, and the paid
# verbs never remove more than REMEDIATION_CAP points across a run.
# DORMANT_MORALE is the retention threshold: a current aware employee
# at or above it keeps their own records at half weight, for free.
DORMANT_FACTOR = 0.5
DORMANT_MORALE = 5
CASE_FLOOR = 10.0
REMEDIATION_CAP = 25.0

EVIDENCE_KINDS = ("witness", "paper", "physical", "pattern", "legacy",
                  "suspicion")


def case_prefix(evidence: list):
    """THE shared prefix iterator (rev. 9 item 15): yields (record,
    running_total) with the same explicit left-to-right addition as
    the raw fold — NOT sum(), which Python 3.12 moved to compensated
    summation, breaking bit-identity with the sequential running total
    (found as 15/300 golden failures in review). The Case-60 telegraph
    and the sit-down's gate-crossing record consume it directly (both
    run pre-branch, where retention protection cannot exist); the
    full-ledger fold applies the derived retention relief on top
    (rev. 10). The running total is unclamped — a prefix question is
    about crossing, not display."""
    total = 0.0
    for record in evidence:
        total += record.magnitude
        yield record, total


def _halvable(evidence: list, dormant_sources: frozenset) -> float:
    """Total retention relief available: half of every protected
    witness record's magnitude, summed left to right."""
    total = 0.0
    for record in evidence:
        if record.kind == "witness" and record.source in dormant_sources:
            total += record.magnitude * (1 - DORMANT_FACTOR)
    return total


def dormant_relief(evidence: list,
                   dormant_sources: frozenset) -> tuple:
    """The DISPLAY allocation of the closed-form relief (rev. 12
    item 2): (index, cut) pairs distributing min(total halvable,
    raw − floor) across protected witness records in ledger order,
    partial at the boundary. Zero-halving records are SKIPPED, never
    a reason to stop; the loop breaks only when the allowance is
    exhausted. The docket's per-record effective magnitudes and the
    settlement lock-in read this; the TOTAL a fold displays comes
    from the closed form in fold_case, never from summing these
    cuts."""
    if not dormant_sources:
        return ()
    total = 0.0
    for record in evidence:
        total += record.magnitude
    allowance = total - CASE_FLOOR
    if allowance <= 0:
        return ()
    allocated = 0.0
    pairs = []
    for i, record in enumerate(evidence):
        if record.kind == "witness" and record.source in dormant_sources:
            half = record.magnitude * (1 - DORMANT_FACTOR)
            if half <= 0:
                continue                    # a legal zero: skip, not stop
            cut = min(half, allowance - allocated)
            if cut <= 0:
                break                       # allowance exhausted
            allocated += cut
            pairs.append((i, cut))
    return tuple(pairs)


def fold_case(evidence: list, dormant_sources: frozenset = frozenset()) \
        -> float:
    """THE full-ledger Case-total fold (rev. 6 completion, context-
    aware per rev. 10, closed-form per rev. 12): the raw left-to-right
    sum, less relief = min(total halvable, max(0, raw − floor)),
    clamped to 0..100 — and a floor-BOUND display canonicalizes to
    exactly the floor, never an ulp under it (sequential per-cut
    subtraction failed that by 2e-15 under review's probing).
    `dormant_sources` is the live protected set — State.case supplies
    it through the witness-status authority, so no cached flag and no
    second derivation can go stale. An empty set (every pre-branch
    caller) leaves the arithmetic bit-identical to the pre-dormancy
    fold."""
    total = 0.0
    for _record, running in case_prefix(evidence):
        total = running
    if dormant_sources:
        halvable = _halvable(evidence, dormant_sources)
        allowance = total - CASE_FLOOR
        if halvable > 0 and allowance > 0:
            if halvable >= allowance:
                return CASE_FLOOR           # floor-bound: canonical
            total -= halvable
    return max(0.0, min(100.0, total))


@dataclass
class Evidence:
    """One record in the Case file. The Case is the clamped SUM of these —
    never a separately stored number — so what the file says and what the
    meter shows can never drift apart.

    kind: "witness" (a person who knows), "paper" (documents and
    reports in the file), "physical" (seizures and scenes), "pattern"
    (the raid handwriting), "legacy" (migrated from a pre-v3 save;
    renders its text verbatim), "suspicion" (the institutional-
    suspicion floor record, §2.3 — permanent, immune to every
    remediation verb, topped up in place). Routine paper ticks carry
    why="" and render nowhere, exactly like the flagless accruals they
    replace.

    A witness record's source is an Employee.key, or "" for external
    provenance — someone the settlement verb can never reach (the
    patrolman, the watcher at the truck). Retention protection is NOT
    stored here (rev. 10): it is derived from the live roster at every
    read, so it can never go stale. contested: counsel argued this
    paper record down already — each record contests at most once."""
    day: int
    magnitude: float
    kind: str
    why: str
    source: str = ""          # Employee.key when a witness is attached
    contested: bool = False


@dataclass(frozen=True)
class SitdownSnapshot:
    """Chair eligibility frozen at lock-up on payoff night (§2.1 rev. 4;
    shape per rev. 5). Only primitive facts persist — R, chair verdicts,
    withholding prose and the gate-crossing record are all derived by
    the pure evaluator in sitdown.py, so the snapshot can never disagree
    with what the scene computes from it."""
    payoff_day: int
    case_at_lockup: float
    evidence_count_at_lockup: int


@dataclass
class BranchState:
    """Act II branch-specific state — None until the sit-down seats a
    chair. One sparse dataclass rather than a union: State.branch names
    the chair and says which fields are live; the save carries all of
    them (fields per docs/ACT1_FORK_DESIGN.md §2.4). Construct through
    the per-chair classmethods and check with validate_branch_state —
    dead fields must stay at their defaults."""
    # The Straight Path
    disposal_runs_left: int = 0
    last_crime_day: int | None = None
    counsel_retained: bool = False
    counsel_days: int = 0                # retained days served, ever
    remediation_used: float = 0.0        # paid points removed, of the cap
    settled_witnesses: list = field(default_factory=list)  # Employee.key
    ad_days_left: int = 0                # advertising campaign days
    insolvent_days: int = 0              # consecutive clean-insolvent nights
    # Carmine's Partner
    points_due_day: int | None = None
    points_missed: int = 0
    vig_owed: int = 0
    # The Harbor War
    war_target: str | None = None
    declared_day: int | None = None
    # The Quiet Sale
    diligence_day: int = 0
    escrow_mark: int = 0
    escrow_incidents: int = 0
    # Cumulative incident repricing in WHOLE percentage points (rev. 8
    # completion): the integer is the canonical stored unit — dividing
    # by 100 turns 28 into 28.000000000000004, so the division happens
    # once, at term-computation time, never at storage time.
    escrow_discount_pct: int = 0
    # Closing outcome (rev. 8): a real discriminator, because an amount
    # alone collapses distinct outcomes — refusal, unaffordability and
    # an empty roster all looked like $0. The full state machine is
    # enforced by validate_branch_state.
    severance_outcome: str = "pending"   # SEVERANCE_OUTCOMES
    severance_paid: int | None = None    # amount; None while pending
    closing_headcount: int | None = None # hired heads at the closing table

    @classmethod
    def straight(cls, *, disposal_runs_left: int = 3,
                 last_crime_day: int | None = None) -> "BranchState":
        return cls(disposal_runs_left=disposal_runs_left,
                   last_crime_day=last_crime_day)

    @classmethod
    def partner(cls, *, points_due_day: int) -> "BranchState":
        return cls(points_due_day=points_due_day)

    @classmethod
    def war(cls, *, war_target: str, declared_day: int) -> "BranchState":
        return cls(war_target=war_target, declared_day=declared_day)

    @classmethod
    def quiet_sale(cls, *, diligence_day: int = 1,
                   escrow_mark: int = 0) -> "BranchState":
        return cls(diligence_day=diligence_day, escrow_mark=escrow_mark)


# THE canonical branch identifiers (rev. 6): config validation, the
# BranchState field map and the scene's chair order all derive from
# this one definition — nothing else may spell a branch id.
BRANCH_ORDER = ("straight", "partner", "war", "quiet_sale")
ACTIVE_BRANCHES = frozenset(BRANCH_ORDER)

# Which BranchState fields are live per active branch; everything else
# must sit at its dataclass default or the payload is a cross-branch mix.
_BRANCH_FIELDS = {
    "straight": {"disposal_runs_left", "last_crime_day", "counsel_retained",
                 "counsel_days", "remediation_used", "settled_witnesses",
                 "ad_days_left", "insolvent_days"},
    "partner": {"points_due_day", "points_missed", "vig_owed"},
    "war": {"war_target", "declared_day"},
    "quiet_sale": {"diligence_day", "escrow_mark", "escrow_incidents",
                   "escrow_discount_pct", "severance_outcome",
                   "severance_paid", "closing_headcount"},
}
SEVERANCE_OUTCOMES = ("pending", "paid", "declined", "unaffordable",
                      "not_applicable")
# THE canonical severance rate: validation, the closing sheet and the
# epilogue all price envelopes from this one number.
SEVERANCE_PER_HEAD = 300
# THE canonical repricing domain (rev. 8 ruling): whole percentage
# points, first incident only. Validation and the escrow draw share it.
REPRICE_MIN_PCT = 20
REPRICE_MAX_PCT = 35
if set(_BRANCH_FIELDS) != ACTIVE_BRANCHES:      # import-time consistency
    raise RuntimeError("BranchState field map out of step with BRANCH_ORDER")
_BRANCH_REQUIRED = {
    "straight": (),
    "partner": ("points_due_day",),
    "war": ("war_target", "declared_day"),
    "quiet_sale": ("diligence_day",),
}


def validate_branch_state(branch: str | None,
                          branch_state: "BranchState | None",
                          game_over: str | None = None) -> None:
    """Reject impossible branch/BranchState combinations, raising
    ValueError (never assert — assertions vanish under optimized
    Python). Called at branch transition and at save-load. Pass the
    run's game_over so terminal invariants bind too — a sold run may
    not carry a pending severance outcome."""
    if branch is None or branch == "stand_pat":
        if branch_state is not None:
            raise ValueError(
                f"branch {branch!r} must not carry a BranchState")
        return
    if branch not in _BRANCH_FIELDS:
        raise ValueError(f"unknown branch {branch!r}")
    if branch_state is None:
        raise ValueError(f"branch {branch!r} requires a BranchState")
    defaults = BranchState()
    live = _BRANCH_FIELDS[branch]
    for f in fields(BranchState):
        if f.name not in live and \
                getattr(branch_state, f.name) != getattr(defaults, f.name):
            raise ValueError(
                f"branch {branch!r}: dead field {f.name!r} is set — "
                f"mixed-branch payload")
    for name in _BRANCH_REQUIRED[branch]:
        if getattr(branch_state, name) is None:
            raise ValueError(f"branch {branch!r}: required field "
                             f"{name!r} is unset")
    if branch == "quiet_sale":
        if branch_state.diligence_day < 1:
            raise ValueError("quiet_sale: the sit-down is diligence day 1")
        _validate_escrow_pricing(branch_state)
        _validate_severance(branch_state, game_over)
    elif branch == "straight":
        _validate_straight(branch_state, game_over)


def _validate_straight(bs: "BranchState", game_over: str | None) -> None:
    """The Straight Path's field contracts (rev. 9): counted disposal
    runs, the paid-remediation budget, the settled-witness roster and
    the insolvency counter all bind at transition and load — a doctored
    payload is refused, not repaired."""
    runs = bs.disposal_runs_left
    if type(runs) is not int or not 0 <= runs <= 3:
        raise ValueError(f"straight: disposal_runs_left must be an integer "
                         f"in 0..3, got {runs!r}")
    if bs.last_crime_day is not None and (
            type(bs.last_crime_day) is not int or bs.last_crime_day < 1):
        raise ValueError(f"straight: last_crime_day must be None or a "
                         f"positive day, got {bs.last_crime_day!r}")
    if not isinstance(bs.counsel_retained, bool):
        raise ValueError(f"straight: counsel_retained must be a bool, "
                         f"got {bs.counsel_retained!r}")
    if type(bs.counsel_days) is not int or bs.counsel_days < 0:
        raise ValueError(f"straight: counsel_days must be a non-negative "
                         f"integer, got {bs.counsel_days!r}")
    used = bs.remediation_used
    if isinstance(used, bool) or not isinstance(used, (int, float)) \
            or not 0 <= used <= REMEDIATION_CAP:
        raise ValueError(f"straight: remediation_used must lie in "
                         f"0..{REMEDIATION_CAP:.0f} points, got {used!r}")
    names = bs.settled_witnesses
    if not isinstance(names, list) \
            or any(not isinstance(k, str) or not k for k in names) \
            or len(set(names)) != len(names):
        raise ValueError(f"straight: settled_witnesses must be a list of "
                         f"unique employee keys, got {names!r}")
    if type(bs.ad_days_left) is not int or bs.ad_days_left < 0:
        raise ValueError(f"straight: ad_days_left must be a non-negative "
                         f"integer, got {bs.ad_days_left!r}")
    days = bs.insolvent_days
    if type(days) is not int or days < 0:
        raise ValueError(f"straight: insolvent_days must be a non-negative "
                         f"integer, got {days!r}")
    if days >= 2 and game_over != "broke":
        raise ValueError("straight: two clean-insolvent nights end the run "
                         "— a live run cannot carry them")


def _validate_escrow_pricing(bs: "BranchState") -> None:
    """The persistence half of the canonical-unit contract (rev. 8
    completion): the integer contract must hold at the model boundary,
    not just on the producer path — otherwise a doctored payload
    reintroduces the representation defect (0.28, 29.5, −10-as-credit,
    200) through save-load."""
    pct = bs.escrow_discount_pct
    if type(pct) is not int:                 # bools are ints; refuse those too
        raise ValueError(f"quiet_sale: escrow_discount_pct must be an "
                         f"integer number of percentage points, got {pct!r}")
    incidents = bs.escrow_incidents
    if incidents == 0:
        if pct != 0:
            raise ValueError(f"quiet_sale: a repricing of {pct}% with no "
                             f"incident on record")
    elif incidents == 1:
        if not REPRICE_MIN_PCT <= pct <= REPRICE_MAX_PCT:
            raise ValueError(f"quiet_sale: first-incident repricing must "
                             f"lie in {REPRICE_MIN_PCT}..{REPRICE_MAX_PCT} "
                             f"points, got {pct}")
    else:
        raise ValueError(f"quiet_sale: {incidents} incidents cannot remain "
                         f"in an active sale — the second collapses it")


def _validate_severance(bs: "BranchState", game_over: str | None) -> None:
    """The complete severance state machine (rev. 8 completion) — the
    label alone permitted contradictory rows like paid/None/2:
      pending        → amount and headcount both None (no sold run)
      paid           → headcount > 0, amount == rate × headcount
      declined       → headcount > 0, amount == 0
      unaffordable   → headcount > 0, amount == 0
      not_applicable → headcount == 0, amount == 0
    """
    outcome = bs.severance_outcome
    paid = bs.severance_paid
    heads = bs.closing_headcount
    if outcome not in SEVERANCE_OUTCOMES:
        raise ValueError(f"quiet_sale: unknown severance outcome {outcome!r}")
    if outcome == "pending":
        if paid is not None or heads is not None:
            raise ValueError("quiet_sale: pending severance must carry no "
                             "amount and no headcount")
        if game_over == "sold":
            raise ValueError("quiet_sale: a sold run cannot leave the "
                             "severance outcome pending")
        return
    if heads is None or paid is None:
        raise ValueError(f"quiet_sale: outcome {outcome!r} requires both "
                         f"amount and headcount")
    if outcome == "paid":
        if heads <= 0 or paid != SEVERANCE_PER_HEAD * heads:
            raise ValueError(f"quiet_sale: paid severance must be "
                             f"{SEVERANCE_PER_HEAD} x a positive headcount "
                             f"(got {paid} for {heads})")
    elif outcome in ("declined", "unaffordable"):
        if heads <= 0 or paid != 0:
            raise ValueError(f"quiet_sale: {outcome} requires a positive "
                             f"headcount and zero paid (got {paid} for "
                             f"{heads})")
    else:                                   # not_applicable
        if heads != 0 or paid != 0:
            raise ValueError(f"quiet_sale: not_applicable requires zero "
                             f"headcount and zero paid (got {paid} for "
                             f"{heads})")


def validate_evidence(records: list) -> None:
    """The evidence ledger's persistence contract (rev. 9, tightened
    rev. 10): magnitudes are never negative (a doctored −50 record
    would be a credit against the Case), kinds come from the known
    taxonomy, contests only mark paper, and the institutional-
    suspicion record — permanent and immune — exists at most once,
    topped up in place. Raises ValueError; bound at save-load."""
    suspicion_seen = False
    for i, r in enumerate(records):
        if r.kind not in EVIDENCE_KINDS:
            raise ValueError(f"evidence[{i}]: unknown kind {r.kind!r}")
        if isinstance(r.magnitude, bool) \
                or not isinstance(r.magnitude, (int, float)) \
                or r.magnitude < 0:
            raise ValueError(f"evidence[{i}]: magnitude must be a "
                             f"non-negative number, got {r.magnitude!r}")
        if not isinstance(r.contested, bool):
            raise ValueError(f"evidence[{i}]: contested must be a boolean")
        if r.contested and r.kind != "paper":
            raise ValueError(f"evidence[{i}]: only paper records are "
                             f"contestable (kind {r.kind!r})")
        if r.kind == "suspicion":
            if suspicion_seen:
                raise ValueError("evidence: the institutional-suspicion "
                                 "record exists at most once, topped up "
                                 "in place")
            suspicion_seen = True


def witness_status(state: "State", key: str) -> str:
    """THE witness-relationship authority (rev. 11 item 2, ordered
    matrix per rev. 12): one answer for a sourced witness, read by the
    docket, the settlement target list, the derived protection set,
    hostile-witness grading, hiring eligibility and cross-state
    validation alike:
      "settled"     — their peace is bought; nothing reopens it
      "beyond_reach"— arrested: the statement is the state's now, and
                      no loyalty halves it
      "protected"   — current, aware, content, at liberty: retention
                      is holding their records down for free
      "reachable"   — a settlement can reach them tonight
    Precedence is the listed order — settled beats arrested beats
    protected. Protection is derived HERE and nowhere else (rev. 12
    item 1: dormant_sources consumes this answer; it no longer
    re-derives a version of its own that forgot the arrest). Callers
    guarantee the key names a roster employee."""
    if state.branch_state is not None \
            and key in state.branch_state.settled_witnesses:
        return "settled"
    e = next(x for x in state.employees if x.key == key)
    if e.arrested:
        return "beyond_reach"
    if e.hired and e.aware and e.morale >= DORMANT_MORALE:
        return "protected"
    return "reachable"


def remediation_disposition(record, state: "State | None" = None) -> str:
    """THE single answer to what may touch a record (rev. 10 item 4,
    context-aware per rev. 11):
      "contestable"  — paper counsel has not argued yet
      "contested"    — paper counsel already argued
      "settleable"   — witness testimony a settlement can still reach
      "settled"      — witness testimony whose source's peace is bought
      "beyond_reach" — witness testimony whose source is in custody
      "external"     — witness testimony with outside provenance: no
                       settlement can reach it (the patrolman, the
                       watcher at the truck)
      "immune"       — physical, pattern, legacy: what the city saw,
                       it saw
      "suspicion"    — the floor record; permanent by definition
    Without state, a sourced witness answers the type-level
    "settleable"; WITH state (every player-facing caller) the answer
    reflects the live relationship via witness_status. The contest
    queue, the settlement verb, the docket and validation all consume
    this — kind, provenance and UI cannot disagree."""
    if record.kind == "suspicion":
        return "suspicion"
    if record.kind == "paper":
        return "contested" if record.contested else "contestable"
    if record.kind == "witness":
        if not record.source:
            return "external"
        if state is None:
            return "settleable"
        status = witness_status(state, record.source)
        if status == "settled":
            return "settled"
        if status == "beyond_reach":
            return "beyond_reach"
        return "settleable"
    return "immune"


def validate_cross_state(state: "State") -> None:
    """Rev. 10 item 2, tightened rev. 11: the ledger, the roster, the
    settled list and the branch state must cohere as ONE payload —
    duplicate employee keys (ambiguous provenance), a witness record
    sourced to nobody or to someone never read in, a settlement
    naming a nonexistent or never-aware employee, or a settled name
    still on the payroll (the closed rehire lifecycle) are refused,
    not repaired."""
    all_keys = [e.key for e in state.employees]
    keys = set(all_keys)
    if len(keys) != len(all_keys):
        raise ValueError("employees: duplicate keys make witness "
                         "provenance ambiguous")
    aware = {e.key for e in state.employees if e.aware}
    hired = {e.key for e in state.employees if e.hired}
    for i, r in enumerate(state.evidence):
        if r.kind == "witness" and r.source:
            if r.source not in keys:
                raise ValueError(f"evidence[{i}]: witness source "
                                 f"{r.source!r} names nobody on the roster")
            if r.source not in aware:
                raise ValueError(f"evidence[{i}]: witness source "
                                 f"{r.source!r} was never read in — they "
                                 f"cannot know what this record says "
                                 f"they know")
    if state.branch == "straight" and state.branch_state is not None:
        for k in state.branch_state.settled_witnesses:
            if k not in keys:
                raise ValueError(f"straight: settled witness {k!r} names "
                                 f"nobody on the roster")
            if k not in aware:
                raise ValueError(f"straight: settled witness {k!r} was "
                                 f"never read in — there is nothing to "
                                 f"have settled")
            if k in hired:
                raise ValueError(f"straight: settled witness {k!r} is "
                                 f"still on the payroll — settled-out "
                                 f"names cannot be rehired (rev. 11)")


@dataclass
class Shop:
    quality: str = "standard"        # purchasing policy: cheap / standard / gourmet
    price: str = "standard"          # cheap / standard / gourmet  (menu pricing)
    ingredients: int = 40            # one unit = one order
    pantry_quality: str = "standard" # what the stock on hand actually IS
    reputation: float = 50.0         # 0-100
    upgrades: set = field(default_factory=set)
    damage_days: int = 0             # closed/limping after a raid
    coupon_days: int = 0             # rival coupon blitz siphoning customers
    district: str = data.HOME_DISTRICT
    stash: dict = field(default_factory=dict)    # good -> units hidden here
    # This address's own order book and honest till — per shop, so a
    # second branch brings its own demand, cover pool and believable
    # ceiling instead of another schema change.
    demand_today: int = 0
    delivery_pool: int = 0
    legit_revenue_today: int = 0

    @property
    def stash_cap(self) -> int:
        return data.SHOP_STASH_CAP * (2 if "walk_in" in self.upgrades else 1)

    @property
    def kitchen_cap(self) -> int:
        base = 60
        if "second_oven" in self.upgrades:
            base = int(base * 1.5)
        if self.damage_days:
            base //= 2
        return base


@dataclass
class State:
    day: int = 1
    clean: int = data.START_CLEAN
    dirty: int = data.START_DIRTY
    debt: int = data.START_DEBT
    shops: list = field(default_factory=lambda: [Shop()])  # [0] is DiNapoli's
    warehouse: dict | None = None                        # good -> units, None = not rented
    warehouse_cash: int = 0                              # dirty cash stashed off-site
    employees: list = field(default_factory=list)
    districts: dict = field(default_factory=dict)
    rivals: dict = field(default_factory=dict)
    prices: dict = field(default_factory=dict)           # district -> good -> price
    events: list = field(default_factory=list)           # ActiveEvent
    evidence: list = field(default_factory=list)         # Evidence records; Case = their sum
    news: list = field(default_factory=list)
    game_over: str | None = None                         # ending id once decided
    debt_paid_day: int | None = None
    act: int = 1                                         # 1 = the hustle; 2 after the sit-down
    branch: str | None = None                            # act-2 chair id once chosen
    branch_state: BranchState | None = None              # chair-specific state after the fork
    sitdown_snapshot: SitdownSnapshot | None = None      # frozen at lock-up on payoff night
    total_laundered: int = 0
    raids_led: int = 0
    kills: int = 0
    demand_shock: float = 1.0        # today's demand luck — rolled once, policy-independent

    # ── the shop, addressed as one while there is one ────────────
    @property
    def shop(self) -> Shop:
        return self.shops[0]

    @property
    def shop_stash(self) -> dict:
        return self.shops[0].stash

    @shop_stash.setter
    def shop_stash(self, value: dict) -> None:
        self.shops[0].stash = value

    @property
    def demand_today(self) -> int:
        return self.shops[0].demand_today

    @demand_today.setter
    def demand_today(self, value: int) -> None:
        self.shops[0].demand_today = value

    @property
    def delivery_pool(self) -> int:
        return self.shops[0].delivery_pool

    @delivery_pool.setter
    def delivery_pool(self, value: int) -> None:
        self.shops[0].delivery_pool = value

    @property
    def legit_revenue_today(self) -> int:
        return self.shops[0].legit_revenue_today

    @legit_revenue_today.setter
    def legit_revenue_today(self, value: int) -> None:
        self.shops[0].legit_revenue_today = value

    # ── the Case, derived from its records ───────────────────────
    def dormant_sources(self) -> frozenset:
        """The retention-protected set, derived from the LIVE roster
        at every read (rev. 10) — and derived through the one
        witness-relationship authority (rev. 12 item 1): exactly the
        aware employees whose witness_status IS "protected". No cache,
        no reconciliation event, and no second derivation to forget
        what the authority knows — an arrest, a poach or a morale slip
        changes the display the moment it happens."""
        if self.branch != "straight" or self.branch_state is None:
            return frozenset()
        return frozenset(
            e.key for e in self.employees
            if e.aware and witness_status(self, e.key) == "protected")

    @property
    def case(self) -> float:
        return fold_case(self.evidence, self.dormant_sources())

    @property
    def case_flags(self) -> list:
        return [e.why if e.kind == "legacy" else f"day {e.day}: {e.why}"
                for e in self.evidence if e.why]

    # ── derived ──────────────────────────────────────────────────
    def stash_bulk(self, stash: dict) -> int:
        return sum(u * data.GOODS[g]["bulk"] for g, u in stash.items())

    def hired(self) -> list:
        return [e for e in self.employees if e.hired]

    def crew(self) -> list:
        """Read-in, available employees — the people you can use for the real work."""
        return [e for e in self.hired() if e.aware and e.available]

    def payoff_in_reach(self) -> bool:
        """§2.1 'near payoff': the debt is alive and on-hand cash could
        clear it tonight — the window in which the sit-down table is at
        stake and evidence-capable acts must warn before they run."""
        return self.debt > 0 and self.clean + self.dirty >= self.debt

    def heat(self, dk: str) -> float:
        return self.districts[dk].heat

    def add_heat(self, dk: str, amount: float) -> None:
        d = self.districts[dk]
        d.heat = max(0.0, min(100.0, d.heat + amount))

    def add_case(self, amount: float, why: str,
                 kind: str = "physical", source: str = "") -> None:
        """Book evidence. Every accrual is its own record, appended in
        order — the fold reproduces the old running total bit for bit.
        The moment the sum reaches 100, prosecution latches: game_over is
        set HERE, at accrual time, and arrest outranks every simultaneous
        outcome (design §2.5) — a success ending set moments earlier
        loses to the latch. Nothing accrues evidence after a run ends,
        so a finished game is never rewritten."""
        if amount <= 0:
            return
        self.evidence.append(Evidence(day=self.day, magnitude=amount,
                                      kind=kind, why=why, source=source))
        if self.case >= 100:
            self.game_over = "arrested"

    def total_stock_units(self) -> int:
        """Contraband anywhere — shop stash plus warehouse. The Straight
        Path's stock-zero goal term, the rivals' smell-of-retreat test
        and the insolvency definition all read this one sum."""
        units = sum(u for u in self.shop_stash.values() if u > 0)
        if self.warehouse:
            units += sum(u for u in self.warehouse.values() if u > 0)
        return units

    def unlaundered_total(self) -> int:
        """Dirty cash anywhere — till plus warehouse stash."""
        return self.dirty + self.warehouse_cash

    def net_worth(self) -> int:
        stock = sum(u * data.GOODS[g]["base"] for g, u in self.shop_stash.items())
        if self.warehouse:
            stock += sum(u * data.GOODS[g]["base"] for g, u in self.warehouse.items())
        return self.clean + self.dirty + self.warehouse_cash + stock - self.debt


def new_state() -> State:
    s = State()
    s.shops = [Shop(district=data.HOME_DISTRICT)]
    s.employees = [
        Employee(key=f"e{i}", **spec) for i, spec in enumerate(data.EMPLOYEE_POOL)
    ]
    # You start with Rosa (driver) and Tony (cook) already on payroll.
    for e in s.employees:
        if e.name.startswith(("Rosa", "Tony")):
            e.hired = True
    s.shop_stash = dict(data.START_STASH)
    s.districts = {k: District(key=k) for k in data.DISTRICTS}
    s.districts[data.HOME_DISTRICT].known_price_age = 0
    s.rivals = {k: Rival(key=k, strength=v["strength"]) for k, v in data.RIVALS.items()}
    return s
