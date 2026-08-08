"""Mutable game state: people, places, money, evidence."""

from dataclasses import dataclass, field

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


@dataclass
class Evidence:
    """One record in the Case file. The Case is the clamped SUM of these —
    never a separately stored number — so what the file says and what the
    meter shows can never drift apart.

    kind: "witness" (a person who knows), "paper" (financial trail),
    "physical" (seizures and scenes), "pattern" (the raid handwriting),
    "legacy" (migrated from a pre-v3 save; renders its text verbatim).
    Routine paper ticks carry why="" and render nowhere, exactly like the
    flagless accruals they replace."""
    day: int
    magnitude: float
    kind: str
    why: str
    source: str = ""          # employee name when a witness is attached


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
    total_laundered: int = 0
    raids_led: int = 0
    kills: int = 0
    demand_shock: float = 1.0        # today's demand luck — rolled once, policy-independent
    demand_today: int = 0            # today's real customer demand, recomputed from policy
    delivery_pool: int = 0           # slice of demand that wants delivery (cover comes from here)
    legit_revenue_today: int = 0     # every honest dollar today — feeds the believable ceiling

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

    # ── the Case, derived from its records ───────────────────────
    @property
    def case(self) -> float:
        return min(100.0, sum(e.magnitude for e in self.evidence))

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

    def heat(self, dk: str) -> float:
        return self.districts[dk].heat

    def add_heat(self, dk: str, amount: float) -> None:
        d = self.districts[dk]
        d.heat = max(0.0, min(100.0, d.heat + amount))

    def add_case(self, amount: float, why: str,
                 kind: str = "physical", source: str = "") -> None:
        """Book evidence. Every accrual is its own record, appended in
        order — the sum reproduces the old running total bit for bit.
        The moment the sum reaches 100, prosecution latches: game_over is
        set HERE, at accrual time, and nothing ever unsets it."""
        if amount <= 0:
            return
        self.evidence.append(Evidence(day=self.day, magnitude=amount,
                                      kind=kind, why=why, source=source))
        if self.case >= 100 and not self.game_over:
            self.game_over = "arrested"

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
