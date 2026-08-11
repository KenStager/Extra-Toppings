"""Mutable game state: people, places, money, evidence."""

import math
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
    # WHERE they work (design rev. 27 item 1). One person, one job,
    # one address: staffing two shops off one roster is the Partner
    # branch's binding constraint, so the assignment is persisted
    # rather than re-derived. REQUIRED, with no home default — a
    # roster entry that names no address is a bug, and rev. 27 item 7
    # forbids the fallback that would hide it (the one place the
    # founding address may be inferred is the one-address save
    # migration).
    shop_key: str
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


@dataclass(frozen=True)
class RaidWarning:
    """A telegraphed raid: how many nights out, and WHICH address it
    named (design rev. 23 item 2). One value, validated at
    construction, because a countdown and a target held as two loose
    fields can disagree — and a warning already on the board must not
    be able to change its mind about where it is going when a save is
    reloaded."""

    nights: int
    shop_key: str

    def __post_init__(self) -> None:
        if type(self.nights) is not int or self.nights < 1:
            raise ValueError(f"a warning counts down from at least one "
                             f"night, got {self.nights!r}")
        if not isinstance(self.shop_key, str) or not self.shop_key:
            raise ValueError(f"a warning must name an address, got "
                             f"{self.shop_key!r}")

    def counted_down(self):
        """One night closer. None once it arrives."""
        if self.nights > 1:
            return RaidWarning(self.nights - 1, self.shop_key)
        return None


@dataclass
class Rival:
    key: str
    strength: float
    relation: float = -10.0       # -100 vendetta … +100 partner
    tribute_demanded: int = 0
    # THE telegraphed raid, typed: the countdown and the address it
    # named are one value or they are nothing (rev. 23 item 2).
    warning: "RaidWarning | None" = None
    ledger_stolen: bool = False
    ovens_wrecked_days: int = 0
    alertness: float = 0.0        # 0-10: how hard their security has learned
    last_raided_day: int = -99    # alertness decays only on quiet days

    @property
    def alive(self) -> bool:
        return self.strength > 0

    @property
    def raid_warning(self) -> int:
        """Nights until their raid, 0 when none is on the board. A
        DERIVED read: the warning itself is the typed value, so there
        is no second field to fall out of step with it."""
        return self.warning.nights if self.warning is not None else 0


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

# THE Case domain, in one home (P4b.1b review). Gameplay clamps every
# fold into this range, so persistence must enforce the same finite
# interval: a stored Case of 101, of infinity or of NaN is not a
# number the game could ever have produced, and NaN in particular
# passes `< 0` and `> 100` alike — every comparison against it is
# False, so a bounds check written as two inequalities lets it
# straight through. `case_in_domain` is the one predicate; the fold
# below clamps to the same two constants rather than repeating them.
CASE_MIN = 0.0
CASE_MAX = 100.0


def is_finite_number(value: object) -> bool:
    """THE finite-number predicate, shared by every numeric boundary
    that persistence binds: the Case domain, evidence magnitudes and
    accruals, and the accrual entry point.

    Two hazards, both of which have reached this codebase:

    NaN and the infinities defeat range tests. Every comparison
    against NaN is False, so `x < 0` and `x > 100` both fail and a
    two-inequality bounds check waves it through; `+inf` passes any
    "non-negative" test and folds to a Case of 100. Finiteness is
    therefore asked FIRST and explicitly, never inferred from a
    comparison.

    And it NEVER RAISES, for any object. `math.isfinite(10**1000)`
    raises OverflowError converting a big int to float — so a
    predicate that reached for it unconditionally would turn a
    doctored payload into a crash instead of a refusal. A Python int
    is finite by construction whatever its size, so only floats are
    asked."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if isinstance(value, int):
        return True                 # exact, and finite at any size
    return math.isfinite(value)


def case_in_domain(value: object) -> bool:
    """Whether a value is a Case the engine could have produced: a
    finite real number inside [CASE_MIN, CASE_MAX]. The interval is
    the one `fold_case` clamps into, from the same two constants."""
    return is_finite_number(value) and CASE_MIN <= value <= CASE_MAX  # type: ignore[operator]

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
    return max(CASE_MIN, min(CASE_MAX, total))


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
    RouteManifest already states — no payload chooses its own wagon.

    Both identities are REQUIRED (rev. 27 item 7): a wagon that names
    neither itself nor where it is kept is not a lean record, it is a
    vehicle nobody can find. The founding wagon is inferred in exactly
    one place — the one-address save migration."""

    key: str
    shop_key: str


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

# Why a wagon is gone, in the player's words — ONE home, so the menu,
# the raid line, the pickup line and the tests all read the same
# sentence. Keyed by the night consumer that took it.
WAGON_NOTES = {
    "route": "out on tonight's route",
    "salvage": "out on tonight's pickup",
    "raid": "out with the night crew",
    "decoy": "already loaded and gone",
}
# THE closed vocabulary of reasons no wagon can leave an address: a
# night consumer took it, the lifecycle withholds it, or the address
# keeps none. Closed deliberately — an arbitrary string would become
# a category no consumer knows how to render, which is how a typo
# turns into prose the player reads.
WAGON_BLOCKS = frozenset(WAGON_NOTES) | {"lifecycle", "unhoused"}
# The one address-independent block that is not a night job. Its note
# is canonical too, so `lifecycle` is the ONLY block free to carry
# address-specific prose — everything else reads from one home.
UNHOUSED_NOTE = "not kept at this address"


@dataclass(frozen=True)
class PlannedWagon:
    """WHICH wagons may leave an address tonight — and if none, why.

    Identity, not a boolean (P4b.1a review): `free` carries the wagon
    KEYS, in stable order, exactly as `WagonNight.free_at` returns
    wagon records. A boolean cannot say WHICH wagon, so it cannot
    represent an address with two of them, nor two routes leaving
    different addresses on the same night — and the fleet is the whole
    point of the Partner branch.

    `blocked_by` is a value from `WAGON_BLOCKS`, never free prose, so
    a consumer chooses its sentence by CASE and the note is rendered
    from one home rather than pasted into another sentence's middle.
    """

    free: tuple = ()
    blocked_by: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        # `free` is a TUPLE OF KEYS, checked as one — a bare string is
        # iterable, so `PlannedWagon("wagon2")` would otherwise load
        # and hand back "w" as the wagon a consumer should take.
        if type(self.free) is not tuple:
            raise ValueError(
                f"free wagons are a tuple of keys, got "
                f"{type(self.free).__name__}")
        for key in self.free:
            if type(key) is not str or not key:
                raise ValueError(
                    f"a wagon key is a non-empty string, got {key!r}")
        if len(set(self.free)) != len(self.free):
            raise ValueError(
                f"the same wagon cannot be free twice: {self.free}")
        if self.free:
            if self.blocked_by or self.note:
                raise ValueError(
                    f"a free wagon carries no reason, got "
                    f"{self.blocked_by!r}/{self.note!r}")
            return
        # A block's prose comes from its ONE home, so a salvage block
        # cannot carry a lifecycle sentence (or any other). Only
        # `lifecycle` is address-specific, because only it names which
        # address is still being built.
        _validate_block(self.blocked_by, self.note)

    @property
    def available(self) -> bool:
        return bool(self.free)

    @property
    def first(self) -> str:
        """The wagon a consumer would take. Fails closed rather than
        handing back a name when there is nothing to take."""
        if not self.free:
            raise RuntimeError(f"no wagon is free — {self.note}")
        return self.free[0]


def _validate_block(blocked_by: str, note: str) -> None:
    """THE block/note contract, shared by every value carrying one.

    Spelling it once is the point: a second copy is how `ClaimResult`
    came to accept a lifecycle note under a `route` blocker, where the
    renderer then ignored the note and announced the route. The pair
    is either canonical or refused."""
    if blocked_by not in WAGON_BLOCKS:
        raise ValueError(
            f"unknown wagon block {blocked_by!r} — the vocabulary is "
            f"{sorted(WAGON_BLOCKS)}")
    if type(note) is not str or not note:
        raise ValueError(
            f"a blocked wagon must say where it is, got {note!r}")
    canonical = WAGON_NOTES.get(blocked_by)
    if blocked_by == "unhoused":
        canonical = UNHOUSED_NOTE
    if canonical is not None and note != canonical:
        raise ValueError(
            f"the {blocked_by!r} note is canonical: expected "
            f"{canonical!r}, got {note!r}")


@dataclass(frozen=True)
class ClaimResult:
    """What happened when a job tried to spend the wagon it named.

    The authority that decides ALREADY KNOWS why, so it says so here
    rather than returning a bare boolean and leaving each caller to
    reconstruct prose from the address. That reconstruction breaks
    under a fleet: asking an address why its wagon is gone returns
    nothing at all when a DIFFERENT wagon is still parked there, and
    the route would announce "the wagon is gone" about an address
    that has one. Same anti-contradiction contract as
    `WagonAvailability` and `PlannedWagon`: the outcome and its
    reason travel as one value and are validated together."""

    claimed: bool
    wagon_key: str
    blocked_by: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if type(self.wagon_key) is not str or not self.wagon_key:
            raise ValueError(
                f"a claim names a wagon, got {self.wagon_key!r}")
        if self.claimed:
            if self.blocked_by or self.note:
                raise ValueError("a spent wagon carries no refusal")
            return
        _validate_block(self.blocked_by, self.note)

    @property
    def sentence(self) -> str:
        """The refusal as the player reads it, from the one home."""
        return wagon_gone_line(self)


def founding_shop(state: "State") -> "Shop":
    """THE founding address, resolved from the lifecycle record itself
    (P4b.1a review).

    Absence of dates IS the founding identity (§2.4.2, and the
    invariant `validate_addresses` binds): every address created after
    the world was built is created by a dated transaction, so exactly
    one address is undated and that one is the founding shop. Nothing
    here reads a KEY SPELLING and nothing reads list position — a
    world whose founding address happens to be called `shop2` has the
    same founding address it always had, and reversing `state.shops`
    changes nothing.

    It is deliberately the same question `validate_addresses` asks, in
    one place: the validator delegates its count here rather than
    re-spelling "exactly one is undated" beside it."""
    undated = [s for s in state.shops
               if s.acceptance_day is None and s.opening_day is None]
    if len(undated) != 1:
        raise ValueError(
            f"exactly one address is undated (the founding shop); "
            f"{len(undated)} are: {sorted(s.key for s in undated)}")
    return undated[0]


def canonical_shop(state: "State", shop: "Shop") -> "Shop":
    """THE address-REFERENCE authority (P4b.1a review): a surface
    handed a `Shop` proves it is THIS WORLD'S shop before it reads a
    lifecycle date off it or writes a crate into it.

    A `Shop` is a mutable record, not an identity. A detached copy
    carrying a real key passes every key-based lookup, answers the
    lifecycle question with ITS OWN dates, and then receives the
    goods while the canonical address's stash never moves — real cash
    spent, stock delivered into a world that does not exist. Mixing
    the two at one transaction boundary (check the copy, price
    against the state, mutate the copy) is the defect this closes.
    `routes.validate_route_plan` already refuses the same thing for a
    driver: a clone carrying a real key is not that person.

    Refused, never redirected. Substituting the canonical object
    would repair the call while leaving everything the caller already
    read off the copy — its dates, its upgrades, its stash — sourced
    from somewhere else, which is a quieter version of the same bug.

    WHERE IT BINDS, stated once so the roster is not guesswork: the
    six player-facing morning surfaces that take a `Shop` — the
    market board, kitchen policy, buying ingredients, the supplier,
    improvements and storage. That is the complete set of generic
    address-specific phase surfaces, and it is a defect class rather
    than a spending rule: a board can DISPLAY a detached room, policy
    can mutate a copy, and storage can combine copy-derived
    information (`shop_at.stash`) with canonical transfers
    (`move_goods(state, shop_at.key, …)`) in one operation.

    Domain internals are deliberately NOT swept: `simulate_shift`,
    route commitment and resolution, and the raid path derive their
    address from the state or carry their own contracts
    (`validate_route_plan`, `plan_origin`), and adding a second check
    there would be a second authority for a settled question."""
    canonical = state.shop_by_key(shop.key)     # KeyError on a ghost
    if canonical is not shop:
        raise ValueError(
            f"the address handed in is not this world's {shop.key!r} "
            f"— a detached copy carrying a real key is not that "
            f"address")
    return canonical


def address_channel(state: "State", shop_key: str, channel: str) -> str:
    """THE per-address world channel (rev. 27 item 5, made real).

    The founding address keeps EXACTLY the channel it has always
    used, so its dice never move: that is what makes every existing
    study and both identity gates still mean something. Additional
    addresses derive a channel from their own STABLE KEY, so a second
    shop's critic is a different critic — and reordering
    `state.shops` cannot change anybody's roll, because nothing here
    reads list position.

    Re-creating one `daily(day, channel)` generator per address gave
    every address the SAME first roll, which is not a shared world
    fact, it is the same coin flipped once and reported twice.

    The identity is RESOLVED, both halves (P4b.1a review). A key that
    names no address used to come back with a plausible channel of its
    own — `critic@ghost` — so a typo drew a whole address's dice out
    of nothing; `state` was passed in and never consulted. And the
    legacy channel followed the SPELLING `shop1` rather than the
    founding address, so a world whose founding shop is keyed
    otherwise silently lost the legacy generator its studies were
    measured on. Both now go through the lifecycle identity."""
    shop = state.shop_by_key(shop_key)          # KeyError on a ghost
    if shop.key == founding_shop(state).key:
        return channel
    return f"{channel}@{shop.key}"


def claimable_wagons(state: "State", shop_key: str) -> tuple:
    """The wagons an address could send out tonight IF nothing had
    taken them — the LIFECYCLE answer alone, in stable key order.

    Deliberately blind to tonight's plans, because two questions are
    being asked and they have different answers. "Which wagon would
    this job take?" is settled at planning and must survive a route
    being scrubbed before it departs; "is that wagon still here?" is
    settled at execution. `planned_wagon` subtracts the night's
    reservations from this; the plans record the identity from it."""
    return tuple(w.key for w in state.wagons_at(shop_key)
                 if wagon_claim(state, w.key).available)


def plan_wagon(state: "State", plan, field: str = "origin_shop") -> str:
    """THE wagon a plan departs in, validated against its own origin.

    A key alone is not an assignment: shop 1 can name shop 2's wagon
    and both halves look well-formed. The pair is checked together,
    here, so no departure path has to remember to do it — and a job
    that names a vehicle kept somewhere else is refused before it
    touches anything."""
    origin = plan_origin(state, plan, field)
    key = plan.get("wagon_key")
    if type(key) is not str or not key:
        raise ValueError(
            f"a wagon job names no wagon, got {key!r}")
    wagon = state.wagon_by_key(key)          # KeyError on a ghost
    if wagon.shop_key != origin:
        raise ValueError(
            f"wagon {key!r} is kept at {wagon.shop_key!r}, not at "
            f"{origin!r} where this job loads")
    return key


def plan_origin(state: "State", plan, field: str = "origin_shop") -> str:
    """The address a planned wagon job leaves from — validated as a
    key AND resolved to a real address.

    Shape alone is not identity. A job naming "ghost" has the right
    type and belongs to no address, so every real address reports its
    wagons free while a job that reserves nothing sits in the plans:
    a wagonless job, which is worse than a refused one. The key
    therefore resolves through `state.shop_by_key`, which fails closed
    on an unknown address exactly as every other lookup does
    (rev. 27 items 1 and 7).

    It lives here rather than in `phases` so the planners that build
    these jobs — `war.plan_salvage` among them — can validate through
    the same authority without importing the phase machinery back.

    `field` names WHICH address the plan pairs its wagon with: routes
    and pickups load at an `origin_shop`, an outgoing raid brings its
    haul back to a `return_shop`. One authority, told where to look —
    never a second, raid-shaped copy of the same three checks."""
    origin = plan.get(field)
    if type(origin) is not str or not origin:
        raise ValueError(
            f"a planned wagon job names no address in {field!r}, got "
            f"{origin!r}")
    state.shop_by_key(origin)          # KeyError on a ghost address
    return origin


def wagon_gone_line(blocked: "PlannedWagon | ClaimResult") -> str:
    """THE sentence-initial rendering of a missing wagon.

    Two registers, one home: `note` is a mid-sentence CLAUSE ("out on
    tonight's route", "the University Hill wagon is still at the
    contractor's yard") for use after a dash; this is the same fact
    as a sentence OPENING. Pasting a clause where a sentence belongs
    is what produced "The wagon is the University Hill wagon is still
    at the contractor's yard".
    """
    if not isinstance(blocked, (PlannedWagon, ClaimResult)):
        raise TypeError(
            f"the wagon sentence renders a validated value, not "
            f"loose strings — got {type(blocked).__name__}")
    blocked_by, note = blocked.blocked_by, blocked.note
    if not blocked_by:
        raise ValueError("a free wagon has no absence to explain")
    if blocked_by in ("lifecycle", "unhoused"):
        return note[0].upper() + note[1:]
    # RENDERED FROM THE BLOCKING JOB, not from whichever job the
    # sentence happened to be written for. The literal that used to
    # sit here named the route unconditionally, so a wagon the PICKUP
    # had was described as being out on the route.
    return f"The wagon is {WAGON_NOTES[blocked_by]}"
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
        # FINITE, through the shared predicate (P4b.1b review). The
        # old spelling asked type and `< 0`, and both NaN and +inf
        # walked past it: NaN because every comparison against it is
        # False, +inf because it is cheerfully non-negative. Either
        # one folds the whole ledger to a Case of 100 — an arrest
        # written by a doctored save rather than by play.
        if not is_finite_number(r.magnitude) or r.magnitude < 0:
            raise ValueError(f"evidence[{i}]: magnitude must be a "
                             f"finite non-negative number, got "
                             f"{r.magnitude!r}")
        if not is_finite_number(r.accrued) or r.accrued < 0 \
                or r.magnitude > r.accrued:
            raise ValueError(f"evidence[{i}]: accrued must be a finite "
                             f"number with 0 <= effective <= accrued, "
                             f"got effective {r.magnitude!r} of "
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


# ── identity minting (rev. 31 item 1) ────────────────────────────
# The founding pair is NAMED where the world is built; every later
# address and vehicle has its identity MINTED here, and the numbering
# starts at 2 because 1 is the founding suffix those constants carry.
_FIRST_MINTED_SUFFIX = 2


def _lowest_unused_key(taken, prefix: str) -> str:
    """THE suffix arithmetic, spelled once: the lowest unused
    `{prefix}{n}` from 2 upward.

    LIST ORDER IS NEVER READ (rev. 31 item 1). Counting records, or
    taking "the last key plus one", makes the answer depend on how
    many rows exist and in what order — so a sparse set (`shop1`,
    `shop3`, shop 2 having never existed or been removed by some
    future editor) would mint a key that is already taken, and
    reversing the list would change what a save is called. Membership
    in the set of existing keys is the only question asked.

    It deliberately does not know what a shop or a wagon IS: two
    copies of "find the free number" is the respelling this project
    refuses, so the domain wrappers below are three lines each."""
    used = set(taken)
    n = _FIRST_MINTED_SUFFIX
    while f"{prefix}{n}" in used:
        n += 1
    return f"{prefix}{n}"


def mint_shop_key(state: "State") -> str:
    """The identity a NEW address will carry.

    MINTING RESERVES NOTHING — this is a calculation, not a claim, so
    two calls before a commit return the SAME key and the second
    record would silently overwrite the first. The atomic deal
    transaction is therefore the sole production caller (rev. 31
    item 1): mint once, build both records locally, preflight the
    whole transaction, commit once. A test guards that scope."""
    return _lowest_unused_key((s.key for s in state.shops), "shop")


def mint_wagon_key(state: "State") -> str:
    """The identity a NEW wagon will carry. Same authority, same
    reservation-free warning: an address and its wagon are created by
    ONE transaction, so both keys are minted inside it."""
    return _lowest_unused_key((w.key for w in state.wagons), "wagon")


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


def operating_shop(state: "State") -> "Shop":
    """THE address a single-address surface is talking about (design
    rev. 27 item 6).

    Act I, the Straight Path and the Quiet Sale all concern ONE
    established shop — that is their story, not an accident of the
    schema — so they resolve it here, ONCE, at their boundary and
    thread the result through instead of each call site reaching for
    "the shop". It is deliberately the same refusal as
    `exactly_one_shop`: the day a surface that assumed one address
    meets two, it fails in a test rather than silently operating on
    whichever happens to sit first in the list.

    This is not a compatibility alias by another spelling. An alias
    is read wherever a shop is wanted; this is called at a boundary,
    and everything downstream takes a Shop parameter."""
    return exactly_one_shop(state)


def raid_target(state: "State", rival_key: str) -> str:
    """THE address-target authority (design rev. 22 item 5): which of
    the player's addresses a rival moves against. P4a supplies the
    mechanism and P4b the policy (rev. 27 item 4) — while one address
    exists the answer is that address, and "the softer of your two
    shops" becomes a real decision only once there are two.

    It never guesses: with no address there is nothing to raid, and
    that is a refusal rather than a home default."""
    targetable = addresses_allowing(state, "rival_targeting")
    if not targetable:
        raise ValueError("no address exists for a raid to target")
    # A site under construction is not a target — there is nothing
    # there to raid — so a founding shop plus a building site is
    # still ONE targetable address, and the policy question does not
    # arise until two are actually open (§2.4.2).
    if len(targetable) != 1:
        # P4b owns the "softer of your two shops" policy (rev. 27
        # item 4). Until it exists, picking one would be picking by
        # LIST POSITION — reversing state.shops would move the raid to
        # a different address, which is the whole defect stable keys
        # exist to abolish. So this refuses rather than guessing.
        raise ValueError(
            f"{len(targetable)} targetable addresses exist and no "
            f"targeting policy has been ruled on — P4b owns that "
            f"choice")
    return targetable[0].key


# ── the address lifecycle (§2.4.2; rev. 29 items 3–4) ────────────
# THE canonical capability vocabulary. §2.4.2's capability ruling,
# spelled once: every surface that wonders what an address may do asks
# `address_allows` with one of these names — no consumer decides for
# itself what a building site may do, and an unknown capability is a
# caller bug, refused rather than defaulted either way.
ADDRESS_CAPABILITIES = (
    "demand",              # the order book: rolling and serving demand
    "service",             # running a service phase at all
    "routes",              # originating delivery routes
    "cover",               # counting as cover for concealed drops
    "laundering",          # contributing a believable ceiling
    "rent",                # being charged rent
    "rival_targeting",     # a rival may move against it
    "law_targeting",       # the law phase may search it
    "contraband_storage",  # holding stash
    "wagon_use",           # its wagon leaving the yard (any consumer)
    "staffing",            # assigning employees to it
    "pantry_supply",       # buying ingredients for opening preparation
    # `phases._improvements` is a real address-bound surface: upgrades
    # are bought for a named shop and land in that shop's `upgrades`.
    # Without a capability name the authority could not actually
    # ENFORCE "only staffing and pantry supply" — the ruling would
    # hold in prose while a building site bought a second oven.
    "improvements",        # buying upgrades for it
)
# Under construction, ALLOWED: staffing, and pantry supply for opening
# preparation. Everything else is DISALLOWED (§2.4.2's central ruling:
# today's engine would roll demand for a building site and charge it
# rent the moment the record exists). Opening enables the complete
# address in ONE transition — there is no third, partially-capable
# phase.
CONSTRUCTION_ALLOWED = frozenset({"staffing", "pantry_supply"})
# THE construction span (rev. 29 item 4): opening day = acceptance
# day + 2, deterministically — Carmine's own contractor, no dice.
CONSTRUCTION_DAYS = 2


def shop_is_open(shop: "Shop", day: int) -> bool:
    """THE lifecycle question (§2.4.2's three recorded phases, made
    operational). An address with no recorded dates is a founding
    address: open since the world began. An address with dates stands
    under construction until its recorded opening day and opens at
    the start of that morning — `day >= opening_day` — after which it
    cannot close (raid damage limps a shop, never shutters it)."""
    if shop.opening_day is None:
        return True
    return day >= shop.opening_day


def open_shops(state: "State") -> list:
    """Every address that is open TODAY, in stable KEY order — the
    filtering authority behind every morning/service/night surface
    that operates over 'the shops'.

    KEY order, never storage order (`wagons_at`'s rule, and the same
    reason): menus will iterate this result, so storage order would
    make a save's list position decide prompt order and therefore bot
    decisions — reinstating exactly the positional identity stable
    keys exist to abolish. Pinned before consumers spread, not after.

    While one address exists this is exactly `state.shops`, which is
    why P4b.1a's conversion is behaviour-equivalent by construction
    on every released path."""
    return sorted((s for s in state.shops if shop_is_open(s, state.day)),
                  key=lambda s: s.key)


def addresses_allowing(state: "State", capability: str) -> list:
    """Every address that may do `capability` TODAY, in stable key
    order (P4b.1a review).

    THE filter every consumer uses — the picker, the demand roll,
    service, rent, the laundering ceiling, law and rival targeting.
    `open_shops` was not enough: "open" and "allowed" are different
    questions, and a site under construction is legitimately allowed
    to take a pantry delivery while it may not roll an order book or
    be charged rent. Spelling "open means allowed" in each consumer
    is how the lifecycle became decorative in the first place."""
    return [s for s in sorted(state.shops, key=lambda a: a.key)
            if address_allows(s, state.day, capability)]


def address_allows(shop: "Shop", day: int, capability: str) -> bool:
    """THE central capability decision (§2.4.2, rev. 29 item 3): one
    lifecycle view decides what an address can do. Open addresses do
    everything; a building site does nothing but prepare — staffing
    and pantry supply — and no consumer gets to reach a different
    answer by asking a different question."""
    if capability not in ADDRESS_CAPABILITIES:
        raise ValueError(f"unknown address capability {capability!r} — "
                         f"the vocabulary is ADDRESS_CAPABILITIES")
    if shop_is_open(shop, day):
        return True
    return capability in CONSTRUCTION_ALLOWED


def wagon_claim(state: "State", wagon_key: str) -> "WagonAvailability":
    """THE lifecycle leg of wagon claimability (rev. 29 item 3): a
    wagon exists from acceptance — an address keeps its wagon from the
    same transaction — but it is unclaimable until its address opens.
    Consulted by routes, outgoing raids, salvage and the decoy alike,
    at planning AND at execution, and the refusal is visible, in the
    player's words — a silent absence would read as a bug, and the
    whole point of the construction window is that the player can see
    what they are waiting for.

    This answers only the lifecycle question. Whether the wagon is
    out tonight is the night-assignment ledger's question (P3.5);
    the two authorities compose, they do not merge."""
    wagon = state.wagon_by_key(wagon_key)
    home = state.shop_by_key(wagon.shop_key)
    if address_allows(home, state.day, "wagon_use"):
        return WAGON_FREE
    # The district's LABEL, never its key: `little_sicily` is an
    # internal identity, and a refusal the player reads is prose.
    return WagonAvailability(
        False, f"the {data.DISTRICTS[home.district]['label']} wagon "
               f"is still at the contractor's yard")


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
        # The lifecycle dates bind together (§2.4.2, rev. 29 item 4):
        # both or neither, whole calendar days (a bool is not a day —
        # `type(...) is int`, the save layer's own rule), the recorded
        # relationship exactly, and a chronology that the calendar can
        # actually have reached. A present-but-malformed value is
        # refused, because repairing it would silently open or un-open
        # an address.
        acc, opn = s.acceptance_day, s.opening_day
        if (acc is None) != (opn is None):
            raise ValueError(
                f"shops[{i}]: an address records both its acceptance "
                f"and its opening day or neither — got acceptance "
                f"{acc!r}, opening {opn!r}")
        if acc is None:
            continue
        if type(acc) is not int or type(opn) is not int:
            raise ValueError(
                f"shops[{i}]: lifecycle dates are whole calendar "
                f"days, got acceptance {acc!r}, opening {opn!r}")
        if acc < 1:
            raise ValueError(
                f"shops[{i}]: acceptance day {acc} predates the "
                f"calendar")
        # An address cannot have been accepted on a day the run has
        # not reached: the deal is struck at a sit-down that already
        # happened, so a future acceptance is a payload describing a
        # transaction nobody made. Refused, never clamped forward.
        if acc > state.day:
            raise ValueError(
                f"shops[{i}]: acceptance day {acc} is in the future "
                f"on day {state.day} — an address cannot be accepted "
                f"before the run reaches the day it was accepted")
        if opn != acc + CONSTRUCTION_DAYS:
            raise ValueError(
                f"shops[{i}]: opening day {opn} must be "
                f"acceptance day {acc} + {CONSTRUCTION_DAYS} — "
                f"the construction span is recorded, not chosen")
        # A SITE UNDER CONSTRUCTION CARRIES NO ORDER BOOK — §2.4.2's
        # initial state, bound at persistence (P4b.1a review). The
        # daily roll now establishes that as a complete postcondition
        # rather than merely skipping the address, and this is the
        # other half: a payload arriving with customers, a delivery
        # pool or a day's honest till at an address that serves nobody
        # is describing a restaurant that does not exist. Refused,
        # never zeroed — repairing it would accept the impossible day
        # and silently keep whatever the numbers were worth.
        # EXACT INTEGER ZERO, not a value that merely compares equal
        # to it (P4b.1a review): `False == 0` and `0.0 == 0`, so a
        # bare `!= 0` accepted a boolean and a float where the field
        # is a count of customers, of delivery orders and of dollars.
        # This project has ruled the same way everywhere it matters —
        # `type(...) is int` on the lifecycle dates just above, the
        # cover count in `validate_route_plan` — because a payload
        # that types a count as a flag is malformed even when its
        # arithmetic happens to agree today.
        if not address_allows(s, state.day, "demand"):
            for name in ("demand_today", "delivery_pool",
                         "legit_revenue_today"):
                value = getattr(s, name)
                if type(value) is not int or value != 0:
                    raise ValueError(
                        f"shops[{i}]: an address under construction "
                        f"serves nobody and carries no order book — "
                        f"{name} is {value!r}")
    # Absence identifies THE founding address, and only it. Every
    # address created after the world was built is created by a dated
    # transaction, so a second undated address is not a lean record:
    # it is a shop that silently claims to have been open since the
    # beginning — the same silent default that put every stolen crate
    # in DiNapoli's, wearing a lifecycle instead of an origin.
    #
    # THIS INVARIANT ALSO PROVES THE WORLD ALWAYS HAS AN OPEN ADDRESS,
    # which morning, service and night all require a subject for: an
    # undated shop has no opening day, so `shop_is_open` returns True
    # on every day, and exactly one address is always undated. A
    # separate "at least one shop is open" check was written here and
    # removed — once this check passes it could never fire, and a
    # guard that cannot fire is worse than none, because it reads as
    # live. It is not restated as a second check ordered before this
    # one either: that would be two authorities for one fact.
    #
    # The count is `founding_shop`'s own refusal, invoked rather than
    # copied (P4b.1a review): the resolver and the validator must not
    # be able to disagree about which address is the founding one, and
    # two spellings of "exactly one is undated" is exactly how they
    # would come to.
    founding_shop(state)
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
    # A telegraphed raid names an address that exists — a warning
    # pointing nowhere could never be resolved, and reloading must not
    # be able to retarget one already on the board (rev. 23 item 2).
    for key, rv in state.rivals.items():
        if rv.warning is not None and rv.warning.shop_key not in seen:
            raise ValueError(f"rival {key!r}: warning names unknown "
                             f"address {rv.warning.shop_key!r}")


def validate_cross_state(state: "State") -> None:
    """Rev. 10 item 2, tightened rev. 11: the ledger, the roster, the
    settled list and the branch state must cohere as ONE payload —
    duplicate employee keys (ambiguous provenance), a witness record
    sourced to nobody or to someone never read in, a settlement
    naming a nonexistent or never-aware employee, or a settled name
    still on the payroll (the closed rehire lifecycle) are refused,
    not repaired."""
    # The calendar FIRST: every dated validator below compares
    # against `state.day`, so a counterfeit ruler would let real
    # dates pass by measuring them wrongly.
    validate_calendar(state)
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
    validate_sitdown_snapshot(state)
    _validate_witnesses_and_campaigns(state)


def validate_calendar(state: "State") -> None:
    """THE calendar primitives, bound at the shared boundary (P4b.1b
    review).

    Every dated check in the engine — the lifecycle's acceptance and
    opening days, the snapshot's payoff day, the points schedule —
    compares against `state.day` and `debt_paid_day`, and Python's
    equality is happy to reconcile `13.0` with `13` and to satisfy
    `<= state.day` with `14.0`. So the counterfeit day never has to
    be the value under test; it can be the ruler. Both are exact
    whole days here, once, and every dated validator downstream is
    then comparing against a real calendar."""
    if type(state.day) is not int or state.day < 1:
        raise ValueError(
            f"the calendar day is a positive whole day, got "
            f"{state.day!r}")
    if state.debt_paid_day is not None:
        if type(state.debt_paid_day) is not int:
            raise ValueError(
                f"the payoff day is a whole calendar day, got "
                f"{state.debt_paid_day!r}")
        if not 1 <= state.debt_paid_day <= state.day:
            raise ValueError(
                f"the debt was paid on day {state.debt_paid_day}, "
                f"outside the calendar the run has reached (day "
                f"{state.day})")


def validate_sitdown_snapshot(state: "State") -> None:
    """The lock-up snapshot must BE a lock-up (P4b.1b review).

    It is three primitives, and every one of them is load-bearing
    somewhere permanent: `payoff_day` decides R and therefore which
    chairs are offered at all, and the Partner deal reads it into a
    points schedule that outlives the scene by the whole month. So a
    payload carrying `payoff_day=13.0` used to sail through the
    scene's arithmetic — `30 - 13.0` compares fine — and set a
    permanent schedule from a day that is not a day.

    This binds at the SHARED boundary rather than inside the branch
    that noticed it: every consumer of the snapshot deserves the same
    guarantee, and a check living in Partner would leave the same
    payload malformed for everyone else. Refused, never repaired —
    coercing 13.0 to 13 would accept a save nobody could have
    written by playing."""
    snap = state.sitdown_snapshot
    if snap is None:
        return
    # Whole calendar days and whole counts — `type(...) is int`, the
    # save layer's own rule, so a bool is not a day and 13.0 is not
    # day 13.
    if type(snap.payoff_day) is not int:
        raise ValueError(
            f"the sit-down snapshot's payoff day is a whole calendar "
            f"day, got {snap.payoff_day!r}")
    if type(snap.evidence_count_at_lockup) is not int:
        raise ValueError(
            f"the sit-down snapshot's evidence count is a whole "
            f"number of records, got "
            f"{snap.evidence_count_at_lockup!r}")
    # THE Case domain, from its one home — the same interval the fold
    # clamps every gameplay total into. Type and `< 0` were not
    # enough: 101.0 is not a Case the engine could produce, infinity
    # is not a number of evidence points, and NaN passes BOTH `< 0`
    # and `> 100` because every comparison against it is False.
    if not case_in_domain(snap.case_at_lockup):
        raise ValueError(
            f"the sit-down snapshot's Case must be a finite number in "
            f"[{CASE_MIN:g}, {CASE_MAX:g}], got {snap.case_at_lockup!r}")
    if not 1 <= snap.payoff_day <= state.day:
        raise ValueError(
            f"the sit-down snapshot's payoff day {snap.payoff_day} is "
            f"outside the calendar the run has reached (day "
            f"{state.day})")
    # The ledger only grows, so the lock-up count is a prefix of it.
    # A count beyond the ledger would make `evidence[:count]` silently
    # short and the gate-crossing record wrong.
    if not 0 <= snap.evidence_count_at_lockup <= len(state.evidence):
        raise ValueError(
            f"the sit-down snapshot counted "
            f"{snap.evidence_count_at_lockup} records at lock-up; the "
            f"ledger holds {len(state.evidence)}")
    # And it reconciles with the payoff it was taken on: the snapshot
    # is frozen on the night the debt died, by construction. Two
    # different answers to "when was Carmine paid" is the two-homes
    # defect, and here it would silently reprice a chair.
    if state.debt_paid_day != snap.payoff_day:
        raise ValueError(
            f"the sit-down snapshot says the debt died on day "
            f"{snap.payoff_day}; the ledger says "
            f"{state.debt_paid_day!r}")


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
    # Raids stay one a night. Routes are ordered by day and unique on
    # (day, ORIGIN) — design rev. 22 item 1: one wagon per address per
    # night, so a second address may run its own route the same night
    # while no address runs two. With one address that is exactly the
    # old rule.
    prev = 0
    for i, rec in enumerate(state.raid_log):
        if not isinstance(rec, RaidAttemptRecord):
            raise ValueError(f"raid_log[{i}]: not a RaidAttemptRecord")
        if rec.day > state.day:
            raise ValueError(f"raid_log[{i}]: day {rec.day} post-dates "
                             f"the state's day {state.day}")
        if rec.day <= prev:
            raise ValueError(f"raid_log[{i}]: one job a night — days "
                             f"must strictly increase "
                             f"({prev} → {rec.day})")
        prev = rec.day
    prev = 0
    seen_routes: set = set()
    for i, rec in enumerate(state.route_log):
        if not isinstance(rec, RouteExecutionRecord):
            raise ValueError(f"route_log[{i}]: not a "
                             f"RouteExecutionRecord")
        if rec.day > state.day:
            raise ValueError(f"route_log[{i}]: day {rec.day} post-dates "
                             f"the state's day {state.day}")
        if rec.day < prev:
            raise ValueError(f"route_log[{i}]: routes are booked in "
                             f"calendar order ({prev} → {rec.day})")
        if (rec.day, rec.origin_shop) in seen_routes:
            raise ValueError(f"route_log[{i}]: one route per address "
                             f"per night — day {rec.day} already has "
                             f"one from that address")
        seen_routes.add((rec.day, rec.origin_shop))
        prev = rec.day
        # A booked route left a REAL address (rev. 27 item 7): an
        # origin naming nowhere could never have happened, so the
        # payload is refused rather than loaded and puzzled over.
        if rec.origin_shop not in {sh.key for sh in state.shops}:
            raise ValueError(f"route_log[{i}]: origin "
                             f"{rec.origin_shop!r} is not an address "
                             f"this state has")

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
    # WHICH address the wagon rolled out of (design rev. 22 item 1).
    # Chronology is keyed on (day, origin), so without it a second
    # address's route is indistinguishable from a duplicate of the
    # first's. REQUIRED (rev. 27 item 7): a record that names no
    # origin would silently book itself against the founding address
    # and collide with a route that really ran there. Pre-origin
    # payloads are migrated at the one-address save boundary, which is
    # the only place the founding address may be assumed.
    origin_shop: str

    def __post_init__(self) -> None:
        if type(self.day) is not int or self.day < 1:
            raise ValueError(f"route record: bad day {self.day!r}")
        if not isinstance(self.origin_shop, str) or not self.origin_shop:
            raise ValueError(f"route record: bad origin "
                             f"{self.origin_shop!r}")
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
                  corner_damage_h: int, origin_shop: str
                  ) -> "RouteExecutionRecord":
        """The authoritative constructor: band, multiplier, district
        and contested flag come from the RouteMarket view the route
        actually ran on, and the origin from the address it left."""
        return cls(day=day, district=rm.district,
                   heat_band=rm.heat.band,
                   capacity_mult=rm.heat.capacity_mult,
                   units_sold=units_sold,
                   corner_damage_h=corner_damage_h,
                   contested=rm.corner_rate > 0.0,
                   origin_shop=origin_shop)


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


def place_haul(state: "State", haul: dict, destination: str) -> tuple:
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
    # The crew unloads where they actually came back to (design
    # rev. 22 item 5). An unknown destination is refused, never
    # resolved to the founding address — a silent home default is
    # exactly how every stolen crate used to land at DiNapoli's
    # whichever address the wagon drove home.
    shop = state.shop_by_key(destination)
    storage_preflight(state, destination)
    if state.warehouse is not None:
        storage_preflight(state, WAREHOUSE)
    shop_room = space_cap(state, destination) - space_used(shop.stash)
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
        shop.stash[g] = shop.stash.get(g, 0) + u
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
    # REQUIRED (rev. 27 item 7): an address that does not say which
    # one it is cannot be looked up, targeted or staffed, and quietly
    # becoming the home shop is precisely the silent default that put
    # every stolen crate in DiNapoli's. The founding address is named
    # once, where the world is built; a keyless payload is inferred
    # once, at the one-address save migration.
    key: str
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
    # The lifecycle dates (§2.4.2, rev. 29 item 4): BOTH persisted on
    # the address, their relationship validated, and the opening day
    # never duplicated in BranchState — two homes for one date is two
    # dates. Absent on every address written before the Partner branch
    # existed, and absence migrates as the founding state: open since
    # the world began (`Shop(**payload)` leaves an omitted field at
    # this default, which is exactly P4a's absence-only discipline).
    # A PRESENT-but-malformed value is refused in validate_addresses.
    acceptance_day: int | None = None
    opening_day: int | None = None

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
    # The founding address and its wagon, NAMED — not inferred. A
    # bare State() is still the one-shop world every test and study
    # starts from; what it may no longer do is build an address whose
    # identity nobody stated.
    shops: list = field(          # keyed, not indexed
        default_factory=lambda: [Shop(key=HOME_SHOP_KEY)])
    wagons: list = field(default_factory=lambda: [
        Wagon(key=HOME_WAGON_KEY, shop_key=HOME_SHOP_KEY)])
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
    # NO production module reads these any more (rev. 27 item 6,
    # completed in P4a.3): every engine surface names the address it
    # means, and a surface that is deliberately about one address
    # resolves it through `operating_shop` at its own boundary. What
    # remains is the legacy-equivalence projection — which renders a
    # save-v2 world where "the shop" genuinely WAS the whole story —
    # and tests that deliberately exercise one-address worlds.
    #
    # They still route through the ONE exactly_one_shop authority,
    # which refuses zero addresses as firmly as several, so a
    # consumer creeping back in fails in a test the moment a second
    # address exists rather than quietly picking the first.
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
        so a finished game is never rewritten.

        THE ACCRUAL BOUNDARY refuses a non-finite magnitude rather
        than booking it (P4b.1b review): `add_case(float("inf"), …)`
        would append a record the fold turns into an immediate Case
        of 100 and an arrest, and `add_case(float("nan"), …)` slips
        past `amount <= 0` because every comparison against NaN is
        False. Nothing in the engine computes either, so reaching
        here with one is a caller bug — refused loudly, never
        booked."""
        if not is_finite_number(amount):
            raise ValueError(
                f"evidence accrues in finite amounts, got {amount!r}")
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
    # The founding address, its stash and its roster all name the one
    # address they belong to at the moment the world is built. Nothing
    # here reads a one-shop alias to get there.
    s.shops = [Shop(key=HOME_SHOP_KEY, district=data.HOME_DISTRICT,
                    stash=dict(data.START_STASH))]
    s.wagons = [Wagon(key=HOME_WAGON_KEY, shop_key=HOME_SHOP_KEY)]
    s.employees = [
        Employee(key=f"e{i}", shop_key=HOME_SHOP_KEY, **spec)
        for i, spec in enumerate(data.EMPLOYEE_POOL)
    ]
    # You start with Rosa (driver) and Tony (cook) already on payroll.
    for e in s.employees:
        if e.name.startswith(("Rosa", "Tony")):
            e.hired = True
    s.districts = {k: District(key=k) for k in data.DISTRICTS}
    s.districts[data.HOME_DISTRICT].known_price_age = 0
    s.rivals = {k: Rival(key=k, strength=v["strength"]) for k, v in data.RIVALS.items()}
    return s
