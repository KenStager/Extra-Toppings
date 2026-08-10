"""Mutable game state: people, places, money, evidence."""

from dataclasses import dataclass, field, fields

from . import data


# THE stable identities (design rev. 27 item 1). An address and a
# wagon are named by a key that never changes and never depends on
# list position — assignments, route origins, raid targets, storage
# locations and ownership all reference these. Keys are internal:
# nothing here ever reaches the player (rev. 27 item 3).
HOME_SHOP_KEY = "shop1"
HOME_WAGON_KEY = "wagon1"


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
    # WHERE they work (design rev. 27 item 1). One person, one job,
    # one address: staffing two shops off one roster is the Partner
    # branch's binding constraint, so the assignment is persisted
    # rather than re-derived. Defaults to the founding address, which
    # is the only one any existing payload could mean.
    shop_key: str = HOME_SHOP_KEY

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

# §2.3 grants the counterplay verbs to the active branches; each branch
# turns them on in its own phase under its own studies (rev. 9 item 16;
# the war joined by the rev. 14 ruling). THE branch-capability answer —
# counsel availability, the laundering ceiling, settlements, retention
# protection, hiring refusals, cross-state validation and the docket
# all consume this one pair; never a scattered branch check.
REMEDIATION_BRANCHES = frozenset({"straight", "war"})


def remediation_unlocked(state: "State") -> bool:
    return state.branch in REMEDIATION_BRANCHES \
        and state.branch_state is not None


# THE clean-insolvency contract (rev. 15 item 3): post-payoff economic
# failure exists in every active branch — two consecutive
# payroll-short nights with no stock anywhere and no dirty dollar
# hidden anywhere end the run. One transition, one nightly rule; the
# branches narrate it in their own voices.
INSOLVENT_NIGHTS = 2


def insolvency_tick(state: "State", payroll_short: bool) -> str | None:
    """THE shared post-payoff insolvency transition. Returns None
    (solvent tonight — counter reset), "warned" (one bad night on the
    books), or "broke" (the run ends). The arrest latch keeps
    precedence by construction: accrual set game_over first, and the
    branch night ticks only run on live games."""
    bs = state.branch_state
    if bs is None:
        raise ValueError("insolvency_tick called outside an active branch")
    if payroll_short and state.total_stock_units() == 0 \
            and state.unlaundered_total() == 0:
        bs.insolvent_days += 1
        if bs.insolvent_days >= INSOLVENT_NIGHTS:
            if state.game_over is None:
                state.game_over = "broke"
            return "broke"
        return "warned"
    bs.insolvent_days = 0
    return None


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
    # The immutable accrual (rev. 16 item 1): what this record was
    # WORTH when it was booked. Contests and settlements mutate the
    # effective magnitude; nothing but the suspicion record's own
    # top-ups (genuine accrual, moved in lockstep) ever touches this.
    # None fills from magnitude at construction — which is also the
    # migration for pre-rev.16 payloads, whose pre-contest values are
    # unrecoverable. Validation binds 0 <= magnitude <= accrued.
    accrued: float | None = None

    def __post_init__(self) -> None:
        if self.accrued is None:
            self.accrued = self.magnitude


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


# ── The Harbor War: canonical constants (§2.4.3, rev. 13–14) ─────
# THE damage channels. "ledger" covers both spends of the same
# leverage — the prosecution AND the greedy lean — so the accounting
# can never silently omit one (rev. 14 item 3). "defense" is the
# fifth channel: repelling their raid already removes strength, and
# folding it into "jobs" would cook the §2.7 mix row it feeds.
WAR_CHANNELS = ("jobs", "corners", "ovens", "ledger", "defense")
# Job prices exactly as PR #3 left them, moved to canonical homes so
# the payoff and the war board's ledger read the same numbers
# (rev. 13 item 2) — integers, because the flag-off arithmetic is
# integer subtraction and must stay bit-identical.
RAID_STOCK_STRENGTH = 12
RAID_SABOTAGE_STRENGTH = 10
RAID_LEDGER_STRENGTH = 8
DEFENSE_STRENGTH = 10        # repelling their raid (the fifth channel)
OVEN_BLEED = 2               # per day while their ovens are wrecked
OVEN_BLEED_FLOOR = 1         # attrition softens but never kills (rev. 13)
LEDGER_LEAN_STRENGTH = 15    # the greedy spend — existing behavior
LEDGER_LAW_STRENGTH = 20     # the prosecution spend (war-only, §2.4.3)
LEDGER_LAW_CALM_DAYS = 4     # their lawyers keep them busy
# THE vendetta band (rev. 13 item 5): one home for −60 —
# straight.FEUD_RELATION and the sit-down's scene line consume this.
# Escrow's WAR_RELATION (−50) is deliberately NOT unified: it is the
# buyer's looser clause, ruled in rev. 8's constants pass.
VENDETTA_RELATION = -60.0
# THE flat nightly heat cooling (flag-off letter) — an integer,
# because the night phase always subtracted the literal 5.
HEAT_DECAY = 5
# District heat teeth (§2.6's ruling, taken in rev. 13-14: war-only
# in P3, each later branch adopting them in its own phase). All three
# are §6.3 placeholders.
HEAT_AMBER = 50.0         # covert capacity halves: work it hot, work it thin
HEAT_RED = 80.0           # the district cannot be worked at all
HEAT_SLOW_DECAY = 3       # a hot district cools slower: the city remembers


@dataclass(frozen=True)
class HeatPolicy:
    """THE district-heat policy view (rev. 14 item 5): one authority,
    zero scattered branch checks — the branch condition lives here and
    nowhere else. capacity_mult applies ONCE, to the nightly drops
    count (never per axis: the ruling is half capacity, not a
    quarter); plannable binds at planning AND at the service-time
    revalidation; decay is tonight's cooling for this district."""
    band: str                 # "cool" / "amber" / "red"
    capacity_mult: float
    plannable: bool
    decay: float
    note: str = ""


def district_heat_policy(state: "State", dk: str) -> HeatPolicy:
    if state.branch != "war":
        return HeatPolicy("cool", 1.0, True, HEAT_DECAY)
    heat = state.districts[dk].heat
    if heat >= HEAT_RED:
        return HeatPolicy(
            "red", 0.5, False, HEAT_SLOW_DECAY,
            note="crawling with patrols — nobody works it tonight")
    if heat >= HEAT_AMBER:
        return HeatPolicy(
            "amber", 0.5, True, HEAT_SLOW_DECAY,
            note="hot — corner customers stay home; take it hot and "
                 "you take ash")
    return HeatPolicy("cool", 1.0, True, HEAT_DECAY)


@dataclass
class DamageRecord:
    """One applied strength reduction, in integer hundredths of a
    point (rev. 14 item 3): 0.15/unit corner damage must never
    recreate the project's floating-point scars. Append-only —
    records are written once by the damage authority and never
    mutated."""
    day: int
    channel: str          # WAR_CHANNELS
    hundredths: int       # actual damage applied, net of overkill


@dataclass
class WarCampaignState:
    """One declared war against one rival (rev. 14 item 2): the
    campaign owns its own history, so a second declaration appends a
    new campaign instead of overwriting the first. Strength
    bookkeeping is integer hundredths; the §2.7 oracle asserts
    nightly that starting strength minus current strength reconciles
    exactly with the damage records."""
    rival_key: str
    declared_day: int
    starting_hundredths: int          # rival strength at declaration
    broken_day: int | None = None
    damage: list = field(default_factory=list)   # DamageRecord, append-only
    law_calm_until: int | None = None  # aggression halved through this day
    violence_raised: bool = False      # the prosecution's permanent price
    salvage_available: bool = False    # capture's one-use pickup, uncollected
    salvage_day: int | None = None     # day collected; None if not/never
    captured_pre_latch: bool = False   # capture completed on a live run


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
    # The Harbor War (rev. 14: campaigns per rival — flat one-war
    # fields could not represent a second declaration without
    # overwriting history). Only genuinely branch-wide facts live
    # here; everything campaign-shaped is WarCampaignState.
    campaigns: list = field(default_factory=list)   # WarCampaignState
    war_pay_paid: int = 0             # bonuses actually paid, cumulative
    war_pay_short_nights: int = 0     # nights the bonus bounced
    insurance_paid_until: int | None = None  # bystander coverage through
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
    def war(cls, *, war_target: str, declared_day: int,
            starting_strength: float) -> "BranchState":
        """The declaration seats the first campaign (rev. 14 item 2);
        starting strength is captured here, in hundredths, so the
        reconciliation oracle has its baseline from night one."""
        return cls(campaigns=[WarCampaignState(
            rival_key=war_target, declared_day=declared_day,
            starting_hundredths=round(starting_strength * 100))])

    @classmethod
    def quiet_sale(cls, *, diligence_day: int = 1,
                   escrow_mark: int = 0) -> "BranchState":
        return cls(diligence_day=diligence_day, escrow_mark=escrow_mark)


# THE canonical branch identifiers (rev. 6): config validation, the
# BranchState field map and the scene's chair order all derive from
# this one definition — nothing else may spell a branch id.
BRANCH_ORDER = ("straight", "partner", "war", "quiet_sale")
ACTIVE_BRANCHES = frozenset(BRANCH_ORDER)


@dataclass
class Wagon:
    """A vehicle, owned by one address. Capacity is NOT a field: it is
    fixed by the model (`data.VEHICLE_CARGO`), exactly as
    RouteManifest already states — no payload chooses its own wagon."""

    key: str = HOME_WAGON_KEY
    shop_key: str = HOME_SHOP_KEY


@dataclass(frozen=True)
class WagonAvailability:
    """Whether tonight's wagon is still here, and why it isn't — ONE
    immutable value (design rev. 25 item 1). Two loose arguments could
    arrive contradicting each other ("free, and out on the route"), so
    the pair is validated at construction and travels together."""

    available: bool
    note: str = ""

    def __post_init__(self) -> None:
        if type(self.available) is not bool:
            raise ValueError("wagon availability is a bool, got "
                             f"{type(self.available).__name__}")
        if self.available and self.note:
            raise ValueError(f"a free wagon has no reason, got "
                             f"{self.note!r}")
        if not self.available and not self.note:
            raise ValueError("a wagon that is gone must say where")


WAGON_FREE = WagonAvailability(True)
# THE released set (§7): the Straight Path and the Quiet Sale lifted
# together on the P2 merge approval; the Harbor War joined on the P3
# merge disposition ("keep activation as a separate, minimal
# post-merge change" — design rev. 15 item c). The CLI flag consumes
# this; development builds may still enable other chairs explicitly
# through GameConfig. Growing this set is each later phase's own
# reviewed activation step.
RELEASED_BRANCHES = frozenset({"straight", "quiet_sale", "war"})
if not RELEASED_BRANCHES <= ACTIVE_BRANCHES:      # import-time consistency
    raise RuntimeError("RELEASED_BRANCHES out of step with BRANCH_ORDER")

# Which BranchState fields are live per active branch; everything else
# must sit at its dataclass default or the payload is a cross-branch mix.
_BRANCH_FIELDS = {
    "straight": {"disposal_runs_left", "last_crime_day", "counsel_retained",
                 "counsel_days", "remediation_used", "settled_witnesses",
                 "ad_days_left", "insolvent_days"},
    "partner": {"points_due_day", "points_missed", "vig_owed"},
    "war": {"campaigns", "war_pay_paid", "war_pay_short_nights",
            "insurance_paid_until",
            # The shared remediation fields (rev. 14 item 8): the war
            # unlocks the same verbs through the same machinery.
            "counsel_retained", "counsel_days", "remediation_used",
            "settled_witnesses",
            # The shared insolvency counter (rev. 15 item 3).
            "insolvent_days"},
    "quiet_sale": {"diligence_day", "escrow_mark", "escrow_incidents",
                   "escrow_discount_pct", "severance_outcome",
                   "severance_paid", "closing_headcount",
                   # The shared insolvency counter (rev. 16 item 3:
                   # "every active branch" includes the sale).
                   "insolvent_days"},
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
    "war": (),                    # rev. 14: _validate_war owns the shape
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
        _validate_insolvency("quiet_sale", branch_state, game_over)
    elif branch == "straight":
        _validate_straight(branch_state, game_over)
    elif branch == "war":
        _validate_war(branch_state, game_over)


def _validate_remediation_fields(branch: str, bs: "BranchState") -> None:
    """The shared remediation contracts (rev. 14 item 8): the counsel
    ledger, the paid budget and the settled roster bind identically in
    every branch the capability policy unlocks."""
    if not isinstance(bs.counsel_retained, bool):
        raise ValueError(f"{branch}: counsel_retained must be a bool, "
                         f"got {bs.counsel_retained!r}")
    if type(bs.counsel_days) is not int or bs.counsel_days < 0:
        raise ValueError(f"{branch}: counsel_days must be a non-negative "
                         f"integer, got {bs.counsel_days!r}")
    used = bs.remediation_used
    if isinstance(used, bool) or not isinstance(used, (int, float)) \
            or not 0 <= used <= REMEDIATION_CAP:
        raise ValueError(f"{branch}: remediation_used must lie in "
                         f"0..{REMEDIATION_CAP:.0f} points, got {used!r}")
    names = bs.settled_witnesses
    if not isinstance(names, list) \
            or any(not isinstance(k, str) or not k for k in names) \
            or len(set(names)) != len(names):
        raise ValueError(f"{branch}: settled_witnesses must be a list of "
                         f"unique employee keys, got {names!r}")


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
    _validate_remediation_fields("straight", bs)
    if type(bs.ad_days_left) is not int or bs.ad_days_left < 0:
        raise ValueError(f"straight: ad_days_left must be a non-negative "
                         f"integer, got {bs.ad_days_left!r}")
    _validate_insolvency("straight", bs, game_over)


def _validate_insolvency(branch: str, bs: "BranchState",
                         game_over: str | None) -> None:
    """The shared insolvency persistence contract (rev. 15 item 3):
    the counter binds identically in every active branch that runs
    the transition."""
    days = bs.insolvent_days
    if type(days) is not int or days < 0:
        raise ValueError(f"{branch}: insolvent_days must be a non-negative "
                         f"integer, got {days!r}")
    if days >= INSOLVENT_NIGHTS and game_over != "broke":
        raise ValueError(f"{branch}: two clean-insolvent nights end the "
                         f"run — a live run cannot carry them")


def _validate_war(bs: "BranchState", game_over: str | None) -> None:
    """The war's field contracts (rev. 14): campaigns are typed,
    append-only-shaped and internally reconciled — a doctored payload
    is refused, not repaired. Cross-world facts (the rival's actual
    strength, the vendetta lock) bind in validate_cross_state."""
    camps = bs.campaigns
    if not isinstance(camps, list) or not camps:
        raise ValueError("war: a declared war carries at least one "
                         "campaign")
    live = 0
    seen_rivals: set = set()
    prev_broken: int | None = None
    for i, c in enumerate(camps):
        if not isinstance(c, WarCampaignState):
            raise ValueError(f"war: campaigns[{i}] is not a campaign "
                             f"payload")
        if c.rival_key not in data.RIVALS:
            raise ValueError(f"war: campaigns[{i}] names unknown rival "
                             f"{c.rival_key!r}")
        if c.rival_key in seen_rivals:
            raise ValueError(f"war: campaigns[{i}] re-declares on "
                             f"{c.rival_key!r} — one campaign per rival")
        seen_rivals.add(c.rival_key)
        if type(c.declared_day) is not int or c.declared_day < 1:
            raise ValueError(f"war: campaigns[{i}] declared_day must be "
                             f"a positive day, got {c.declared_day!r}")
        if type(c.starting_hundredths) is not int \
                or c.starting_hundredths <= 0:
            raise ValueError(f"war: campaigns[{i}] starting strength "
                             f"must be a positive integer in hundredths, "
                             f"got {c.starting_hundredths!r}")
        if i > 0 and (prev_broken is None or c.declared_day < prev_broken):
            raise ValueError(f"war: campaigns[{i}] declared before the "
                             f"previous campaign broke — one front at a "
                             f"time (rev. 14)")
        prev_broken = c.broken_day
        if c.broken_day is not None and (
                type(c.broken_day) is not int
                or c.broken_day < c.declared_day):
            raise ValueError(f"war: campaigns[{i}] broken_day must be on "
                             f"or after the declaration, got "
                             f"{c.broken_day!r}")
        if c.broken_day is None:
            live += 1
        total = 0
        last_day = c.declared_day
        if not isinstance(c.damage, list):
            raise ValueError(f"war: campaigns[{i}] damage must be a list")
        for j, r in enumerate(c.damage):
            if not isinstance(r, DamageRecord):
                raise ValueError(f"war: campaigns[{i}].damage[{j}] is "
                                 f"not a damage record")
            if r.channel not in WAR_CHANNELS:
                raise ValueError(f"war: campaigns[{i}].damage[{j}] "
                                 f"unknown channel {r.channel!r}")
            if type(r.hundredths) is not int or r.hundredths <= 0:
                raise ValueError(f"war: campaigns[{i}].damage[{j}] must "
                                 f"record a positive integer number of "
                                 f"hundredths, got {r.hundredths!r}")
            if type(r.day) is not int or r.day < last_day:
                raise ValueError(f"war: campaigns[{i}].damage[{j}] day "
                                 f"{r.day!r} breaks append-only order")
            last_day = r.day
            total += r.hundredths
        if total > c.starting_hundredths:
            raise ValueError(f"war: campaigns[{i}] records more damage "
                             f"than the rival had strength — overkill is "
                             f"never recorded")
        if c.broken_day is not None and total != c.starting_hundredths:
            raise ValueError(f"war: campaigns[{i}] is broken but its "
                             f"damage records do not reconcile to its "
                             f"starting strength")
        if c.broken_day is None and total == c.starting_hundredths:
            raise ValueError(f"war: campaigns[{i}] records the rival at "
                             f"zero with no capture recorded — the "
                             f"authority detects capture exactly once")
        if c.broken_day is None and (
                c.salvage_available or c.salvage_day is not None
                or c.captured_pre_latch):
            raise ValueError(f"war: campaigns[{i}] carries capture state "
                             f"without a capture")
        if c.salvage_available and c.salvage_day is not None:
            raise ValueError(f"war: campaigns[{i}] salvage cannot be both "
                             f"waiting and collected")
        if c.salvage_day is not None and (
                type(c.salvage_day) is not int
                or c.broken_day is None or c.salvage_day < c.broken_day):
            raise ValueError(f"war: campaigns[{i}] salvage_day must be on "
                             f"or after the capture, got {c.salvage_day!r}")
        if c.law_calm_until is not None and (
                type(c.law_calm_until) is not int
                or c.law_calm_until < c.declared_day):
            raise ValueError(f"war: campaigns[{i}] law_calm_until must be "
                             f"a day on or after the declaration, got "
                             f"{c.law_calm_until!r}")
        if not isinstance(c.violence_raised, bool):
            raise ValueError(f"war: campaigns[{i}] violence_raised must "
                             f"be a bool")
        if not isinstance(c.captured_pre_latch, bool):
            raise ValueError(f"war: campaigns[{i}] captured_pre_latch "
                             f"must be a bool")
    if live > 1:
        raise ValueError("war: at most one campaign may be live — one "
                         "front at a time (rev. 14)")
    for name in ("war_pay_paid", "war_pay_short_nights"):
        v = getattr(bs, name)
        if type(v) is not int or v < 0:
            raise ValueError(f"war: {name} must be a non-negative "
                             f"integer, got {v!r}")
    ins = bs.insurance_paid_until
    if ins is not None and (type(ins) is not int or ins < 1):
        raise ValueError(f"war: insurance_paid_until must be None or a "
                         f"positive day, got {ins!r}")
    _validate_remediation_fields("war", bs)
    _validate_insolvency("war", bs, game_over)


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
        if isinstance(r.accrued, bool) \
                or not isinstance(r.accrued, (int, float)) \
                or r.accrued < 0 or r.magnitude > r.accrued:
            raise ValueError(f"evidence[{i}]: accrued must be a number "
                             f"with 0 <= effective <= accrued, got "
                             f"effective {r.magnitude!r} of "
                             f"{r.accrued!r} (rev. 16)")
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


def _only_with_key(items: list, key: str, kind: str):
    """THE keyed lookup behind every by-key accessor. Refuses BOTH
    failure modes: nothing with that key, and — the subtle one — more
    than one. Returning the first of several duplicates would quietly
    reinstate list position as the identity, which is the exact thing
    stable keys exist to abolish; validation refuses duplicates, so a
    lookup that meets them is reading a state that should never have
    been built."""
    found = [it for it in items if it.key == key]
    if not found:
        raise KeyError(f"no {kind} with key {key!r}")
    if len(found) > 1:
        raise KeyError(f"{len(found)} {kind}s share the key {key!r} — "
                       f"an ambiguous identity is not a lookup result")
    return found[0]


def exactly_one_shop(state: "State") -> "Shop":
    """THE single-address authority behind every compatibility alias
    (rev. 27 item 6). Refuses BOTH ends: a state with no address is
    as malformed as a state with several, and either means a caller
    is using a one-shop shortcut where it no longer holds.

    This is deliberately a refusal rather than a `shops[0]`: the whole
    point of P4a is that the day a second address exists, every
    remaining shortcut fails loudly in a test instead of quietly
    banking the second shop's takings in the first shop's till."""
    if not state.shops:
        raise ValueError("the state has no shop at all")
    if len(state.shops) != 1:
        raise ValueError(
            f"{len(state.shops)} addresses exist — this caller still "
            f"assumes one; it must name the shop it means")
    return state.shops[0]


def validate_addresses(state: "State") -> None:
    """Shops and wagons are identified by key, so the keys must BE
    identities (rev. 27 item 1): present, non-empty, unique within
    their kind, and — for a wagon — pointing at an address that
    actually exists. Refused, never repaired."""
    if not state.shops:
        raise ValueError("a state must carry at least one shop")
    seen: set = set()
    for i, s in enumerate(state.shops):
        if not isinstance(s.key, str) or not s.key:
            raise ValueError(f"shops[{i}]: a shop key must be a "
                             f"non-empty string, got {s.key!r}")
        if s.key in seen:
            raise ValueError(f"shops[{i}]: duplicate shop key {s.key!r}")
        seen.add(s.key)
        # An address stands somewhere real: its district drives demand,
        # heat and the route board, so an unknown one is refused here
        # rather than raising a KeyError deep in the morning.
        if s.district not in data.DISTRICTS:
            raise ValueError(f"shops[{i}]: unknown district "
                             f"{s.district!r}")
    wagon_keys: set = set()
    housed: set = set()
    for i, w in enumerate(state.wagons):
        if not isinstance(w.key, str) or not w.key:
            raise ValueError(f"wagons[{i}]: a wagon key must be a "
                             f"non-empty string, got {w.key!r}")
        if w.key in wagon_keys:
            raise ValueError(f"wagons[{i}]: duplicate wagon key {w.key!r}")
        wagon_keys.add(w.key)
        if w.shop_key not in seen:
            raise ValueError(f"wagons[{i}]: kept at unknown address "
                             f"{w.shop_key!r}")
        housed.add(w.shop_key)
    # Canon creates an address and its wagon in one transaction — the
    # $13,000 buys the build-out, the permits AND the used second
    # wagon together (§2.4.2), and the founding shop opened with one.
    # So an address with no wagon is not a lean game state, it is a
    # payload that lost something; a wagonless address would need its
    # own design ruling before it could load.
    for s in state.shops:
        if s.key not in housed:
            raise ValueError(f"shop {s.key!r} keeps no wagon — an "
                             f"address and its wagon arrive together")
    # Everyone works somewhere real — hired or not. An assignment to a
    # shop that does not exist loads without complaint and then simply
    # never matches, so both kitchens quietly run at the no-cook floor:
    # a silent capability loss, which is precisely what validation
    # exists to turn into a refusal.
    for i, e in enumerate(state.employees):
        if e.shop_key not in seen:
            raise ValueError(f"employees[{i}] ({e.key}): assigned to "
                             f"unknown address {e.shop_key!r}")


def validate_cross_state(state: "State") -> None:
    """Rev. 10 item 2, tightened rev. 11: the ledger, the roster, the
    settled list and the branch state must cohere as ONE payload —
    duplicate employee keys (ambiguous provenance), a witness record
    sourced to nobody or to someone never read in, a settlement
    naming a nonexistent or never-aware employee, or a settled name
    still on the payroll (the closed rehire lifecycle) are refused,
    not repaired."""
    validate_addresses(state)
    all_keys = [e.key for e in state.employees]
    keys = set(all_keys)
    if len(keys) != len(all_keys):
        raise ValueError("employees: duplicate keys make witness "
                         "provenance ambiguous")
    # The storage authority binds at persistence too (rev. 18 item 2;
    # via the shared validator, rev. 19 item 1): a stash of unknown
    # goods, inexact or negative counts, or over its space cap is
    # refused — never repaired.
    # Every address's room, plus the warehouse — each named, none
    # assumed (rev. 27 item 7).
    for where in storage_locations(state):
        stash = _stash_at(state, where) if (
            where != WAREHOUSE or state.warehouse is not None) else None
        if stash is None:
            continue
        label = location_label(state, where)
        validate_inventory_map(stash, f"{label} stash")
        if space_used(stash) > space_cap(state, where):
            raise ValueError(
                f"{label} stash: {space_used(stash)} space used over "
                f"the {space_cap(state, where)}-space cap")
    validate_execution_history(state)
    _validate_witnesses_and_campaigns(state)


def validate_execution_history(state: "State") -> None:
    """Rev. 20 item 2: the ledgers must BE the history they claim,
    not merely well-typed rows. Chronology is strict (one route and
    one raid per night); the capacity multiplier is the canonical
    TYPE (Boolean equality satisfies nothing); contested is DERIVED
    from the campaign's declared/broken interval, so a contested
    route cannot predate its war or load into an Act I state; corner
    damage sits under the band-adjusted ceiling; and the campaign
    ledger reconciles against the execution records BOTH ways —
    succeeded raid damage against jobs-channel damage, and route
    corner damage against corners-channel damage, by day and rival.
    Refused, never repaired."""
    for name, log, kind in (("raid_log", state.raid_log,
                             RaidAttemptRecord),
                            ("route_log", state.route_log,
                             RouteExecutionRecord)):
        prev = 0
        for i, rec in enumerate(log):
            if not isinstance(rec, kind):
                raise ValueError(f"{name}[{i}]: not a {kind.__name__}")
            if rec.day > state.day:
                raise ValueError(f"{name}[{i}]: day {rec.day} post-dates "
                                 f"the state's day {state.day}")
            if rec.day <= prev:
                raise ValueError(f"{name}[{i}]: one job a night — days "
                                 f"must strictly increase "
                                 f"({prev} → {rec.day})")
            prev = rec.day

    camps = (state.branch_state.campaigns
             if state.branch == "war" and state.branch_state is not None
             else [])

    def covered(rival_key: str, day: int) -> bool:
        return any(c.rival_key == rival_key and c.declared_day <= day
                   and (c.broken_day is None or day <= c.broken_day)
                   for c in camps)

    for i, rec in enumerate(state.route_log):
        if type(rec.capacity_mult) is not float:
            raise ValueError(f"route_log[{i}]: the capacity multiplier "
                             f"is a float, got "
                             f"{type(rec.capacity_mult).__name__}")
        owner = data.DISTRICTS[rec.district]["rival"]
        should = owner is not None and covered(owner, rec.day)
        if rec.contested != should:
            raise ValueError(f"route_log[{i}]: contested={rec.contested} "
                             f"contradicts the campaign record for "
                             f"{rec.district} on day {rec.day}")
        ceiling = round(CORNER_DAMAGE_MAX_H * rec.capacity_mult)
        if rec.corner_damage_h > ceiling:
            raise ValueError(f"route_log[{i}]: corner damage "
                             f"{rec.corner_damage_h} over the "
                             f"{rec.heat_band}-band ceiling {ceiling}")

    booked_jobs: dict = {}
    booked_corners: dict = {}
    for c in camps:
        for dr in c.damage:
            if dr.channel == "jobs":
                key = (c.rival_key, dr.day)
                booked_jobs[key] = booked_jobs.get(key, 0) + dr.hundredths
            elif dr.channel == "corners":
                key = (c.rival_key, dr.day)
                booked_corners[key] = (booked_corners.get(key, 0)
                                       + dr.hundredths)
    claimed_jobs: dict = {}
    for rec in state.raid_log:
        if rec.outcome == "succeeded" and rec.damage_h \
                and covered(rec.rival, rec.day):
            key = (rec.rival, rec.day)
            claimed_jobs[key] = claimed_jobs.get(key, 0) + rec.damage_h
    if booked_jobs != claimed_jobs:
        raise ValueError(f"execution history: campaign jobs damage "
                         f"{booked_jobs} does not reconcile with the "
                         f"raid ledger {claimed_jobs}")
    claimed_corners: dict = {}
    for rec in state.route_log:
        if rec.corner_damage_h:
            owner = data.DISTRICTS[rec.district]["rival"]
            key = (owner, rec.day)
            claimed_corners[key] = (claimed_corners.get(key, 0)
                                    + rec.corner_damage_h)
    if booked_corners != claimed_corners:
        raise ValueError(f"execution history: campaign corners damage "
                         f"{booked_corners} does not reconcile with "
                         f"the route ledger {claimed_corners}")


def _validate_witnesses_and_campaigns(state: "State") -> None:
    """The roster/ledger/campaign coherence half of cross-state
    validation (split for readability when the execution-history
    reconciliation joined, rev. 20)."""
    keys = {e.key for e in state.employees}
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
    if remediation_unlocked(state) and state.branch_state is not None:
        b = state.branch
        for k in state.branch_state.settled_witnesses:
            if k not in keys:
                raise ValueError(f"{b}: settled witness {k!r} names "
                                 f"nobody on the roster")
            if k not in aware:
                raise ValueError(f"{b}: settled witness {k!r} was "
                                 f"never read in — there is nothing to "
                                 f"have settled")
            if k in hired:
                raise ValueError(f"{b}: settled witness {k!r} is "
                                 f"still on the payroll — settled-out "
                                 f"names cannot be rehired (rev. 11)")
    if state.branch == "war" and state.branch_state is not None:
        # The campaign payload must cohere with the WORLD it claims to
        # describe (rev. 14): the reconciliation identity binds at the
        # persistence boundary exactly as the nightly oracle asserts it
        # in play, and the vendetta lock is a fact of the save, not a
        # hope of the runtime.
        for i, c in enumerate(state.branch_state.campaigns):
            if c.rival_key not in state.rivals:
                raise ValueError(f"war: campaigns[{i}] names a rival "
                                 f"missing from the world")
            rv = state.rivals[c.rival_key]
            spent = sum(r.hundredths for r in c.damage)
            if round(rv.strength * 100) != c.starting_hundredths - spent:
                raise ValueError(
                    f"war: campaigns[{i}] does not reconcile — "
                    f"{c.rival_key!r} reads {rv.strength}, the records "
                    f"say {(c.starting_hundredths - spent) / 100}")
            if rv.relation > VENDETTA_RELATION:
                raise ValueError(
                    f"war: campaigns[{i}] rival {c.rival_key!r} sits "
                    f"above the vendetta band — the lock is permanent")
        ins = state.branch_state.insurance_paid_until
        if ins is not None:
            # Rev. 15 item 6: paid coverage belongs to a living,
            # undeclared-upon Sal — anything else is an impossible
            # payload, refused.
            sal = state.rivals.get("sal")
            if sal is None or not sal.alive:
                raise ValueError("war: insurance held on a dead or "
                                 "missing merchant")
            if any(c.rival_key == "sal"
                   for c in state.branch_state.campaigns):
                raise ValueError("war: insurance cannot survive a "
                                 "declaration on Sal")


def security_word(alertness: float) -> str:
    """The rival-security display bands (PR #3). One home: the raid
    target menu and the war board describe the same guard with the
    same word."""
    if alertness >= 7:
        return "fortress"
    if alertness >= 4:
        return "hardened"
    if alertness >= 2:
        return "wary"
    return "sleepy"


RAID_ATTEMPT_OUTCOMES = frozenset({"scrubbed", "failed", "succeeded"})
RAID_CREW_MAX = 3          # planning's cap — one home (rev. 19 item 2)

# ── The quiet-night alertness transition (rev. 19 item 3) ─────────
ALERTNESS_DECAY = 0.34


def alertness_decay_tick(rival, day: int) -> None:
    """THE quiet-night transition, one home: guards get bored again,
    slowly — but never on a night you hit them (the rival phase runs
    after the raid, so a raid tonight blocks tonight's decay).
    Production's rival phase AND the pacing experiment consume this
    single function; the transition cannot drift between them."""
    if rival.last_raided_day != day:
        rival.alertness = max(0.0, rival.alertness - ALERTNESS_DECAY)
# The corner channel's mechanical ceiling in hundredths: the -4/night
# cap doubled by the outage window. war.py asserts this equals its
# CORNER_CAP × OUTAGE_MULT at import, so the homes cannot drift.
CORNER_DAMAGE_MAX_H = 800


@dataclass(frozen=True)
class RaidAttemptRecord:
    """One outgoing job, booked once (rev. 18 item 3), bound to the
    ACTUAL mechanical domains (rev. 19 item 2): constructed locally
    AFTER the outcome is known, appended exactly once, frozen
    thereafter. A 100-person crew or 99.99 strength of job damage is
    history gameplay cannot produce, so persistence refuses it."""
    day: int
    rival: str
    outcome: str            # scrubbed | failed | succeeded
    crew: int
    damage_h: int           # ACTUAL applied strength damage, hundredths

    def __post_init__(self) -> None:
        if type(self.day) is not int or self.day < 1:
            raise ValueError(f"raid attempt: bad day {self.day!r}")
        if self.rival not in data.RIVALS:
            raise ValueError(f"raid attempt: unknown rival {self.rival!r}")
        if self.outcome not in RAID_ATTEMPT_OUTCOMES:
            raise ValueError(f"raid attempt: unknown outcome "
                             f"{self.outcome!r}")
        if type(self.crew) is not int \
                or not 1 <= self.crew <= RAID_CREW_MAX:
            raise ValueError(f"raid attempt: crew {self.crew!r} outside "
                             f"the 1..{RAID_CREW_MAX} planning cap")
        if type(self.damage_h) is not int or self.damage_h < 0 \
                or self.damage_h > RAID_STOCK_STRENGTH * 100:
            raise ValueError(f"raid attempt: damage {self.damage_h!r} "
                             f"outside the strongest job's "
                             f"{RAID_STOCK_STRENGTH}-strength ceiling")
        if self.outcome != "succeeded" and self.damage_h != 0:
            raise ValueError("raid attempt: only a succeeded job "
                             "applies damage")


# Only bands a route can actually EXECUTE under (rev. 19 item 2):
# red is refused at planning AND at the commit revalidation, so an
# executed red route is history that never happened. Each band pins
# its policy multiplier.
ROUTE_EXECUTED_BANDS = {"cool": 1.0, "amber": 0.5}


@dataclass(frozen=True)
class RouteExecutionRecord:
    """One route night, booked at RESOLUTION (rev. 18 item 4), bound
    to the actual mechanical domains (rev. 19 item 2): the
    execution-time district, its band with the band's OWN policy
    multiplier, units a 24-space wagon can actually move, corner
    damage under the mechanical cap, and a contested flag only a
    turf with an owner can carry. Prefer `of_market` — the record
    built from the authoritative RouteMarket view — so no study can
    invent a combination gameplay cannot produce."""
    day: int
    district: str
    heat_band: str
    capacity_mult: float
    units_sold: int
    corner_damage_h: int
    contested: bool

    def __post_init__(self) -> None:
        if type(self.day) is not int or self.day < 1:
            raise ValueError(f"route record: bad day {self.day!r}")
        if self.district not in data.DISTRICTS:
            raise ValueError(f"route record: unknown district "
                             f"{self.district!r}")
        if self.heat_band not in ROUTE_EXECUTED_BANDS:
            raise ValueError(f"route record: a route cannot execute "
                             f"under {self.heat_band!r}")
        if self.capacity_mult != ROUTE_EXECUTED_BANDS[self.heat_band]:
            raise ValueError(
                f"route record: band {self.heat_band!r} carries "
                f"multiplier {ROUTE_EXECUTED_BANDS[self.heat_band]}, "
                f"got {self.capacity_mult!r}")
        if type(self.units_sold) is not int \
                or not 0 <= self.units_sold <= data.VEHICLE_CARGO:
            raise ValueError(f"route record: {self.units_sold!r} units "
                             f"from a {data.VEHICLE_CARGO}-space wagon")
        if type(self.corner_damage_h) is not int \
                or not 0 <= self.corner_damage_h <= CORNER_DAMAGE_MAX_H:
            raise ValueError(f"route record: corner damage "
                             f"{self.corner_damage_h!r} outside the "
                             f"mechanical cap")
        if type(self.contested) is not bool:
            raise ValueError(f"route record: bad contested flag "
                             f"{self.contested!r}")
        if self.contested and data.DISTRICTS[self.district]["rival"] is None:
            raise ValueError(f"route record: {self.district} has no "
                             f"owner to contest")
        if self.corner_damage_h and not self.contested:
            raise ValueError("route record: corner damage on an "
                             "uncontested turf is impossible")

    @classmethod
    def of_market(cls, day: int, rm, units_sold: int,
                  corner_damage_h: int) -> "RouteExecutionRecord":
        """The authoritative constructor: band, multiplier, district
        and contested flag come from the RouteMarket view the route
        actually ran on."""
        return cls(day=day, district=rm.district,
                   heat_band=rm.heat.band,
                   capacity_mult=rm.heat.capacity_mult,
                   units_sold=units_sold,
                   corner_damage_h=corner_damage_h,
                   contested=rm.corner_rate > 0.0)


# ── THE storage capacity authority (rev. 18 item 2, made SAFE per
# rev. 19 item 1) ─────────────────────────────────────────────────
# One home for space arithmetic: space used, a destination's
# capacity, the units that fit, and the transactional transfer.
# Supplier purchases, the storage menu, haul placement, the route
# planner, rendering and persistence validation all consume THESE —
# and everything passes through ONE inventory-map validator first:
# exact integers, known goods, no negatives, explicit locations.

# A storage location is either THE warehouse or an address, named by
# its stable shop key (design rev. 27 item 1). There is no bare "shop"
# token any more: once addresses have identities, a location that does
# not say WHICH address is exactly the implicit home default rev. 27
# item 7 forbids.
WAREHOUSE = "warehouse"


def storage_locations(state: "State") -> tuple:
    """Every valid storage token for this state, addresses first."""
    return tuple(s.key for s in state.shops) + (WAREHOUSE,)


def location_label(state: "State", where: str) -> str:
    """The human name for a location. Keys are internal (rev. 27
    item 3), so prose and refusals name the warehouse, or the shop —
    by district once more than one address exists, never by key."""
    if where == WAREHOUSE:
        return WAREHOUSE
    shop = state.shop_by_key(where)
    if len(state.shops) == 1:
        return "shop"
    return f"{data.DISTRICTS[shop.district]['label']} shop"


def validate_inventory_map(stash: dict, where: str = "inventory") -> None:
    """THE shared inventory-map validator (rev. 19 item 1): every
    key a known good, every count an EXACT integer (True and 1.5
    are refused, never coerced), never negative. Consumed by every
    space computation, transfer, placement, render and persistence
    read — impossible inventory is refused, not reported as zero."""
    for g, u in stash.items():
        if g not in data.GOODS:
            raise ValueError(f"{where}: unknown good {g!r}")
        if type(u) is not int:
            raise ValueError(f"{where}: count for {g} must be an exact "
                             f"integer, got {u!r}")
        if u < 0:
            raise ValueError(f"{where}: negative {g} count {u}")


def space_used(stash: dict | None) -> int:
    """Space units a stash occupies (units × space each). Refuses an
    impossible map — never silently drops a negative row."""
    if not stash:
        return 0
    validate_inventory_map(stash)
    return sum(u * data.GOODS[g]["bulk"] for g, u in stash.items())


def space_cap(state: "State", where: str) -> int:
    """A destination's capacity in space units."""
    if where == WAREHOUSE:
        return data.WAREHOUSE_CAP
    try:
        return state.shop_by_key(where).stash_cap
    except KeyError as exc:
        raise ValueError(f"unknown storage location {where!r}") from exc


def _stash_at(state: "State", where: str) -> dict:
    """Explicit locations only (rev. 19 item 1: an unknown name must
    never alias a real stash — and rev. 27 item 7: nor may it quietly
    resolve to the home address)."""
    if where == WAREHOUSE:
        if state.warehouse is None:
            raise ValueError("no warehouse is rented")
        return state.warehouse
    try:
        return state.shop_by_key(where).stash
    except KeyError as exc:
        raise ValueError(f"unknown storage location {where!r}") from exc


def units_that_fit(state: "State", where: str, good: str) -> int:
    """How many units of `good` the destination can still take."""
    if good not in data.GOODS:
        raise ValueError(f"unknown good {good!r}")
    stash = _stash_at(state, where)
    room = max(0, space_cap(state, where) - space_used(stash))
    return room // data.GOODS[good]["bulk"]


def storage_preflight(state: "State", where: str) -> dict:
    """THE storage-state preflight (rev. 20 item 1): a location's
    map is valid AND within its space cap, or the operation that
    would touch it refuses before mutating anything. Returns the
    stash for the caller."""
    stash = _stash_at(state, where)
    label = location_label(state, where)
    validate_inventory_map(stash, label)
    if space_used(stash) > space_cap(state, where):
        raise ValueError(f"{label}: {space_used(stash)} space used "
                         f"over the {space_cap(state, where)}-space cap")
    return stash


def move_goods(state: "State", src: str, dst: str, good: str,
               units: int) -> None:
    """THE transactional transfer: BOTH locations preflighted before
    any mutation (rev. 20 item 1 — a source holding True, 1.5 or an
    unknown row refuses whole), never over a destination's capacity,
    never a boolean, a fraction, or an unknown location. Any refusal
    leaves every stash byte-identical."""
    if type(units) is not int:
        raise ValueError(f"cannot move {units!r} units — exact "
                         f"integers only")
    if good not in data.GOODS:
        raise ValueError(f"unknown good {good!r}")
    if units < 0:
        raise ValueError(f"cannot move {units} units")
    # BOTH endpoints are preflighted before anything else is decided,
    # so an endpoint that is not a location at all fails as an unknown
    # location rather than being misread as a prohibited transfer —
    # and so the labels below exist to name what went wrong. Keys are
    # internal (rev. 27 item 3): every refusal below speaks in labels.
    a = storage_preflight(state, src)
    b = storage_preflight(state, dst)
    src_label = location_label(state, src)
    dst_label = location_label(state, dst)
    # No free address-to-address transfer (design rev. 22 item 9):
    # goods move between shops by wagon or they do not move. The
    # storage authority shuttles stock between an address and the
    # warehouse, and refuses to teleport it across the city.
    if src != WAREHOUSE and dst != WAREHOUSE:
        raise ValueError(
            f"no direct transfer between addresses ({src_label} → "
            f"{dst_label}) — goods travel by wagon or not at all")
    if units == 0:
        return
    if a.get(good, 0) < units:
        raise ValueError(f"only {a.get(good, 0)}x {good} at the "
                         f"{src_label}")
    if units > units_that_fit(state, dst, good):
        raise ValueError(f"{units}x {good} does not fit at the "
                         f"{dst_label}")
    a[good] -= units
    b[good] = b.get(good, 0) + units


def place_haul(state: "State", haul: dict) -> tuple:
    """THE haul-placement authority (rev. 15 item 2): stolen or
    salvaged goods fill the shop stash first, then the warehouse if
    rented, and anything past that stays where it was found. Returns
    (kept, left_behind). Raid payoffs and the salvage pickup both
    consume this — the loop lives once, its arithmetic is the
    storage authority's, and space caps can never be quietly
    skipped again. Preflight-then-commit (rev. 20 item 1): the haul
    map AND every destination are validated first, the COMPLETE
    allocation is computed locally, and only then does anything
    mutate — a refusal leaves every stash byte-identical, never a
    half-placed haul."""
    validate_inventory_map(haul, "haul")
    # P4a.2 names the address explicitly instead of indexing it; the
    # crew's actual RETURN address becomes a parameter in P4a.3, which
    # is where haul placement stops assuming there is only one.
    home = exactly_one_shop(state).key
    storage_preflight(state, home)
    if state.warehouse is not None:
        storage_preflight(state, WAREHOUSE)
    shop_room = space_cap(state, home) - space_used(state.shop_stash)
    wh_room = (space_cap(state, WAREHOUSE)
               - space_used(state.warehouse)
               if state.warehouse is not None else 0)
    to_shop_all: dict = {}
    to_wh_all: dict = {}
    left_behind = 0
    kept: dict = {}
    for g, u in haul.items():
        bulk = data.GOODS[g]["bulk"]
        to_shop = min(u, max(0, shop_room) // bulk)
        shop_room -= to_shop * bulk
        rest = u - to_shop
        to_wh = 0
        if rest and state.warehouse is not None:
            to_wh = min(rest, max(0, wh_room) // bulk)
            wh_room -= to_wh * bulk
            rest -= to_wh
        if to_shop:
            to_shop_all[g] = to_shop
        if to_wh:
            to_wh_all[g] = to_wh
        left_behind += rest
        if u - rest:
            kept[g] = u - rest
    for g, u in to_shop_all.items():             # the ONE commit
        state.shop_stash[g] = state.shop_stash.get(g, 0) + u
    if to_wh_all:
        wh = state.warehouse
        assert wh is not None                    # allocation implies rented
        for g, u in to_wh_all.items():
            wh[g] = wh.get(g, 0) + u
    return kept, left_behind


def live_campaign(state: "State",
                  rival_key: str | None = None) -> "WarCampaignState | None":
    """The one live (unbroken) war campaign, optionally only if it
    targets rival_key. None outside the war branch — every consumer's
    flag-off path is 'no campaign'."""
    if state.branch != "war" or state.branch_state is None:
        return None
    for c in state.branch_state.campaigns:
        if c.broken_day is None and (rival_key is None
                                     or c.rival_key == rival_key):
            return c
    return None


def apply_rival_damage(state: "State", rival_key: str, channel: str,
                       amount: float, *,
                       floor: float | None = None) -> float:
    """THE rival-damage authority (rev. 14 item 3): every strength
    reduction in the engine flows through here — jobs, the oven
    bleed, both ledger spends, defense, and the war's corners.

    Without a live campaign on this rival the arithmetic is the exact
    subtraction the call sites always did, bit for bit (plain
    subtraction, or max(floor, …) where the caller always had a
    floor). With a live campaign, damage quantizes to integer
    hundredths, overkill is cut at the floor (capture at zero; the
    oven bleed's floor of 1 still binds above it), the applied amount
    is appended to the campaign's ledger, and capture is detected
    exactly once — the moment strength reaches zero. Returns the
    damage actually applied."""
    if channel not in WAR_CHANNELS:
        raise ValueError(f"unknown damage channel {channel!r}")
    rival = state.rivals[rival_key]
    camp = live_campaign(state, rival_key)
    if camp is None:
        before = rival.strength
        if floor is None:
            rival.strength = before - amount
        else:
            rival.strength = max(floor, before - amount)
        return before - rival.strength
    before_h = round(rival.strength * 100)
    floor_h = 0 if floor is None else round(floor * 100)
    applied_h = max(0, min(round(amount * 100), before_h - floor_h))
    if applied_h:
        rival.strength = (before_h - applied_h) / 100
        camp.damage.append(DamageRecord(
            day=state.day, channel=channel, hundredths=applied_h))
        if before_h - applied_h == 0:
            # Capture, detected here and only here (rev. 14 item 3):
            # the transition is recorded on whatever run state exists
            # THIS moment — a latch that already fired means the
            # verdict beat the victory (§2.5 precedence, rev. 14).
            camp.broken_day = state.day
            camp.salvage_available = True
            camp.captured_pre_latch = state.game_over is None
    return applied_h / 100


def vendetta_locked(state: "State", rival_key: str) -> bool:
    """A rival named by any war campaign — live or broken — is
    vendetta-locked for the rest of the run (§2.4.3: no truce, ever)."""
    return (state.branch == "war" and state.branch_state is not None
            and any(c.rival_key == rival_key
                    for c in state.branch_state.campaigns))


def adjust_relation(state: "State", rival_key: str, delta: float) -> None:
    """THE relation-mutation authority (rev. 14 item 4): every
    relation write flows through here, so the vendetta lock is
    enforced at the mutation site — never by an eventual-consistency
    sweep. Flag-off the arithmetic is the exact `+=` it replaced."""
    rival = state.rivals[rival_key]
    rival.relation = rival.relation + delta
    if vendetta_locked(state, rival_key):
        rival.relation = min(rival.relation, VENDETTA_RELATION)


def set_relation(state: "State", rival_key: str, value: float) -> None:
    """Absolute-value sibling of adjust_relation (the truce's
    max(relation, 25) is a set, not a delta); the lock binds here
    identically."""
    rival = state.rivals[rival_key]
    rival.relation = value
    if vendetta_locked(state, rival_key):
        rival.relation = min(rival.relation, VENDETTA_RELATION)


@dataclass
class Shop:
    # THE address's stable identity (rev. 27 item 1) — never its index
    # in state.shops, which changes the moment a second address opens.
    key: str = HOME_SHOP_KEY
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
    shops: list = field(default_factory=lambda: [Shop()])  # keyed, not indexed
    wagons: list = field(default_factory=lambda: [Wagon()])
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
    # Append-only TYPED execution logs (rev. 17 item 4, typed and
    # validated per rev. 18 items 3–4): RaidAttemptRecord and
    # RouteExecutionRecord, constructed once AFTER the outcome is
    # known, appended exactly once, frozen thereafter. The honest
    # denominators for every pacing and exposure claim.
    raid_log: list = field(default_factory=list)
    route_log: list = field(default_factory=list)

    # ── addressing ───────────────────────────────────────────────
    def shop_by_key(self, key: str) -> Shop:
        """THE address lookup (rev. 27 item 1), through the shared
        unique-key authority: an unknown key is a bug, never a reason
        to hand back the home shop (rev. 27 item 7)."""
        return _only_with_key(self.shops, key, "shop")

    def wagon_by_key(self, key: str) -> Wagon:
        """THE wagon lookup. Same authority, same refusals."""
        return _only_with_key(self.wagons, key, "wagon")

    def wagons_at(self, shop_key: str) -> list:
        """Every wagon kept at an address, in stable KEY order — not
        storage order, which would make the answer depend on the list
        position identity exists to escape. The address must exist:
        an unknown key is refused, never answered with an empty list."""
        self.shop_by_key(shop_key)
        return sorted((w for w in self.wagons if w.shop_key == shop_key),
                      key=lambda w: w.key)

    # ── the shop, addressed as one while there is one ────────────
    # Every alias below routes through the ONE exactly_one_shop
    # authority (rev. 27 item 6), which refuses zero addresses as
    # firmly as it refuses several: a state with no shop is as
    # malformed as a state with two the caller never expected. These
    # exist only until their consumers name an address; by the end of
    # P4a.3 the legacy-equivalence projection is the only place a
    # bare "the shop" is still the correct idea.
    @property
    def shop(self) -> Shop:
        return exactly_one_shop(self)

    @property
    def shop_stash(self) -> dict:
        return exactly_one_shop(self).stash

    @shop_stash.setter
    def shop_stash(self, value: dict) -> None:
        exactly_one_shop(self).stash = value

    @property
    def demand_today(self) -> int:
        return exactly_one_shop(self).demand_today

    @demand_today.setter
    def demand_today(self, value: int) -> None:
        exactly_one_shop(self).demand_today = value

    @property
    def delivery_pool(self) -> int:
        return exactly_one_shop(self).delivery_pool

    @delivery_pool.setter
    def delivery_pool(self, value: int) -> None:
        exactly_one_shop(self).delivery_pool = value

    @property
    def legit_revenue_today(self) -> int:
        return exactly_one_shop(self).legit_revenue_today

    @legit_revenue_today.setter
    def legit_revenue_today(self, value: int) -> None:
        exactly_one_shop(self).legit_revenue_today = value

    # ── the Case, derived from its records ───────────────────────
    def dormant_sources(self) -> frozenset:
        """The retention-protected set, derived from the LIVE roster
        at every read (rev. 10) — and derived through the one
        witness-relationship authority (rev. 12 item 1): exactly the
        aware employees whose witness_status IS "protected". No cache,
        no reconciliation event, and no second derivation to forget
        what the authority knows — an arrest, a poach or a morale slip
        changes the display the moment it happens."""
        if not remediation_unlocked(self):
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
        # Legacy name; the arithmetic lives in the one storage
        # authority (rev. 18 item 2).
        return space_used(stash)

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
        """Contraband anywhere — EVERY address's stash plus the
        warehouse, each counted exactly once (design rev. 27 item 2).
        The Straight Path's stock-zero goal term, the rivals'
        smell-of-retreat test and the insolvency definition all read
        this one sum, so it must see every room the player owns."""
        units = sum(u for s in self.shops for u in s.stash.values() if u > 0)
        if self.warehouse:
            units += sum(u for u in self.warehouse.values() if u > 0)
        return units

    def unlaundered_total(self) -> int:
        """Dirty cash anywhere — till plus warehouse stash."""
        return self.dirty + self.warehouse_cash

    def net_worth(self) -> int:
        """THE address-agnostic asset authority (rev. 27 item 2):
        every address's stash plus the warehouse stock, counted
        exactly once, on top of cash less debt. Deliberately NOT
        branch-aware, and its inventory arithmetic lives nowhere else —
        the Partner grading view subtracts arrears from this rather
        than re-deriving what money means."""
        stock = sum(u * data.GOODS[g]["base"]
                    for s in self.shops for g, u in s.stash.items())
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
