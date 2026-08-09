"""Deep-analysis experiment harness. Versioned so every finding in
docs/FINDINGS.md can be reproduced against any future engine revision.

Usage:
    python3 -m analysis.experiments sweep [--seeds 150]
    python3 -m analysis.experiments grid [--seeds 40]
    python3 -m analysis.experiments policy [--seeds 60]
    python3 -m analysis.experiments trajectory [--seeds 40]
    python3 -m analysis.experiments raids [--trials 300]
    python3 -m analysis.experiments events [--seeds 150]
    python3 -m analysis.experiments all
"""

import argparse
import random
import statistics
from collections import Counter, defaultdict
from typing import ClassVar

from extra_toppings import data, escrow, market, phases, raids
from extra_toppings import war as war_mod
from extra_toppings.bot import (BOTS, CooldownRaiderBot, CounselOnlyBot,
                                CrimeHeavyBot, EscrowBot, GreedyBot,
                                KeepsStashBot, MarketBot, NeglectWarBot,
                                NoRemediationBot, RaidOnlyBot,
                                SettlementOnlyBot, SloppyEscrowBot,
                                StraightBot, WarBot)
from extra_toppings.config import GameConfig
from extra_toppings.game import run
from extra_toppings.models import new_state
from extra_toppings.rng import Streams
from extra_toppings.ui import BotConsole


def sweep(seeds: int) -> None:
    """Ending distributions, payoff timing and staff attrition per strategy."""
    strategies: dict = dict(BOTS)
    strategies["random"] = BotConsole
    for name, cls in strategies.items():
        endings: Counter = Counter()
        paid_days, cases, reps, nets = [], [], [], []
        emp_arrests = founders_lost = 0
        for seed in range(seeds):
            s = run(seed, cls(random.Random(seed)))
            endings[s.game_over] += 1
            if s.debt_paid_day:
                paid_days.append(s.debt_paid_day)
            cases.append(s.case)
            reps.append(s.shop.reputation)
            nets.append(s.net_worth())
            emp_arrests += sum(1 for e in s.employees if e.arrested)
            founders_lost += sum(1 for e in s.employees[:2] if not e.hired)
        paid_days.sort()
        nets.sort()
        med = paid_days[len(paid_days) // 2] if paid_days else None
        print(f"{name:>9}: {dict(endings)}  payoff {len(paid_days)}/{seeds}"
              f"  median payday {med}  case μ{sum(cases)/seeds:.0f}"
              f"  rep μ{sum(reps)/seeds:.0f}  net med {nets[seeds//2]:+,}"
              f"  driver arrests {emp_arrests}  founders lost {founders_lost}")


def grid(seeds: int) -> None:
    """Cargo fraction x cover stops: payoff% / arrest% / mean case."""
    print(f"{'':>8}", *[f"cover={c:>2}" for c in (0, 4, 8, 12)])
    for cf in (0.25, 0.5, 0.75, 1.0):
        row = []
        for cover in (0, 4, 8, 12):
            Bot = type("B", (GreedyBot,), {"cargo_frac": cf, "cover_stops": cover})
            paid = arr = 0
            case = 0.0
            for seed in range(seeds):
                s = run(seed, Bot(random.Random(seed)))
                paid += s.debt_paid_day is not None
                arr += s.game_over == "arrested"
                case += s.case
            row.append(f"{100*paid//seeds:>3}/{100*arr//seeds:>2}/{case/seeds:>4.0f}")
        print(f"cf={cf:<5}", *[f"{r:>10}" for r in row])


def policy(seeds: int) -> None:
    """Laundering discipline and delegation, matched pairs."""
    def measure(name, Bot):
        paid = arr = earr = 0
        case = 0.0
        nets = []
        for seed in range(seeds):
            s = run(seed, Bot(random.Random(seed)))
            paid += s.debt_paid_day is not None
            arr += s.game_over == "arrested"
            earr += sum(1 for e in s.employees if e.arrested)
            case += s.case
            nets.append(s.net_worth())
        nets.sort()
        print(f"{name:>30}: payoff {100*paid//seeds}%  arrest {100*arr//seeds}%  "
              f"driver arrests {earr}  case μ{case/seeds:.0f}  "
              f"net med {nets[seeds//2]:+,}")

    measure("wash to ceiling", GreedyBot)
    measure("launder everything", type("G", (GreedyBot,), {"launder_all": True}))

    class SendDriver(CrimeHeavyBot):
        ride_along = False
        cover_stops = 8
        launder_all = False
        do_raids = False
        MENU_PREFS: ClassVar = [p for p in CrimeHeavyBot.MENU_PREFS
                                if p[0] != "Plan a night job"]

    measure("read-in crew, boss rides",
            type("R", (SendDriver,), {"ride_along": True}))
    measure("read-in crew, driver alone", SendDriver)


def trajectory(seeds: int) -> None:
    """Averaged day-by-day arc for the greedy line."""
    days = 30
    acc = {k: [0.0] * days for k in ("debt", "cash", "case", "rep", "pool")}
    for seed in range(seeds):
        streams = Streams(seed)
        con = GreedyBot(random.Random(seed))
        st = new_state()
        for d in range(days):
            if st.game_over:
                break
            plans = phases.morning(st, con, streams)
            rep = phases.service(st, plans, con, streams)
            phases.night(st, plans, rep, con, streams)
            if st.debt > 0:
                st.debt = int(st.debt * (1 + data.DEBT_RATE))
            acc["debt"][d] += st.debt
            acc["cash"][d] += st.clean + st.dirty + st.warehouse_cash
            acc["case"][d] += st.case
            acc["rep"][d] += st.shop.reputation
            acc["pool"][d] += st.delivery_pool
    print(f"{'day':>4} {'debt':>7} {'cash':>7} {'case':>5} {'rep':>4} {'pool':>5}")
    for d in (0, 4, 9, 14, 19, 24, 29):
        print(f"{d+1:>4} {acc['debt'][d]/seeds:>7,.0f} {acc['cash'][d]/seeds:>7,.0f} "
              f"{acc['case'][d]/seeds:>5.1f} {acc['rep'][d]/seeds:>4.0f} "
              f"{acc['pool'][d]/seeds:>5.1f}")


def raid_roi(trials: int) -> None:
    """Success, injury and evidence rates per objective under random play."""
    for objective in data.RAID_OBJECTIVES:
        success = injuries = 0
        haul_value = case_delta = 0.0
        for seed in range(trials):
            rng = random.Random(seed)
            st = new_state()
            market.roll_prices(st, rng)
            crew = st.employees[:3]
            for e in crew:
                e.hired = e.aware = True
            before_stash = dict(st.shop_stash)
            before_case = st.case
            plan = {"rival": "vinnie", "objective": objective,
                    "team": list(crew), "armed": False}
            raids.run_raid(st, plan, BotConsole(random.Random(seed)), rng)
            r = st.rivals["vinnie"]
            ok = ((objective == "steal_stock"
                   and sum(st.shop_stash.values()) > sum(before_stash.values()))
                  or (objective == "ledger" and r.ledger_stolen)
                  or (objective == "sabotage" and r.ovens_wrecked_days > 0))
            success += ok
            injuries += sum(1 for e in crew if e.injured_days)
            case_delta += st.case - before_case
            if ok and objective == "steal_stock":
                haul_value += sum(
                    (st.shop_stash.get(g, 0) - before_stash.get(g, 0))
                    * data.GOODS[g]["base"] for g in data.GOODS)
        line = (f"  {objective:<12} success {100*success//trials}%  "
                f"injured/run {injuries/trials:.2f}  case +{case_delta/trials:.1f}")
        if objective == "steal_stock":
            line += f"  avg haul ${haul_value/max(success, 1):,.0f}"
        print(line)

    # Repeat-raid decline: three consecutive steal_stock jobs on one target.
    # Primary metric is EXPECTED dollars per attempt (failures included) —
    # success rate alone can mislead when successful hauls grow richer.
    n_repeat = trials
    hauls = [0.0, 0.0, 0.0]
    succ = [0, 0, 0]
    for seed in range(n_repeat):
        rng = random.Random(seed)
        st = new_state()
        market.roll_prices(st, rng)
        st.warehouse = {}                     # storage isn't the confound here
        crew = st.employees[:3]
        for e in crew:
            e.hired = e.aware = True
        for attempt in range(3):
            def stock_value(s):
                total = sum(u * data.GOODS[g]["base"]
                            for g, u in s.shop_stash.items())
                return total + sum(u * data.GOODS[g]["base"]
                                   for g, u in (s.warehouse or {}).items())
            before = stock_value(st)
            plan = {"rival": "vinnie", "objective": "steal_stock",
                    "team": [e for e in crew if e.available], "armed": False,
                    "wagon_free": True}
            if not plan["team"]:
                break
            raids.run_raid(st, plan, BotConsole(random.Random(seed * 3 + attempt)),
                           rng)
            gained = stock_value(st) - before
            hauls[attempt] += gained
            succ[attempt] += gained > 0
            for e in crew:
                e.injured_days = 0
    print(f"  repeat steal_stock on one target ({n_repeat} trials):")
    for i in range(3):
        print(f"    attempt {i+1}: success {100*succ[i]//n_repeat}%  "
              f"expected ${hauls[i]/n_repeat:,.0f}/attempt  "
              f"(${hauls[i]/max(succ[i],1):,.0f} per success)")


def events(seeds: int) -> None:
    """Does an event firing in days 1-10 shift the payoff rate?"""
    orig = market.draw_events
    seen: dict = {}

    def spy(state, rng):
        orig(state, rng)
        if state.day <= 10:
            for ev in state.events:
                seen.setdefault(ev.spec["id"], state.day)

    market.draw_events = spy
    runs = []
    base_wins = 0
    try:
        for seed in range(seeds):
            seen = {}
            globals()["seen"] = seen
            s = run(seed, GreedyBot(random.Random(seed)))
            win = s.debt_paid_day is not None
            base_wins += win
            runs.append((set(seen), win))
    finally:
        market.draw_events = orig
    print(f"baseline payoff: {base_wins}/{seeds}")
    counts: dict = defaultdict(lambda: [0, 0])
    for evs, win in runs:
        for eid in evs:
            counts[eid][0] += 1
            counts[eid][1] += win
    for eid in sorted(counts):
        n, w = counts[eid]
        wo_n, wo_w = seeds - n, base_wins - w
        print(f"  {eid:<20} n={n:<4} with {100*w//max(n,1):>3}%  "
              f"without {100*wo_w//max(wo_n,1):>3}%")


def fork(seeds: int) -> None:
    """P1b acceptance rows (§2.7): sit-down reachability for the
    unmodified market bot; the Quiet Sale's close/revert discipline; the
    careful-vs-careless valuation study; forced-branch crash-freedom.
    Thresholds are falsification bars, not tuning targets."""
    sale_on = GameConfig(fork_enabled=True,
                         enabled_branches=frozenset({"quiet_sale"}))
    fork_only = GameConfig(fork_enabled=True)

    # ── criterion 2 (rev. 7): reachability, measured completely ──
    from extra_toppings import sitdown as sd
    opened = 0
    full_tables = 0
    absent_calendar = 0
    absent_case = 0
    payoff_days = []
    for seed in range(seeds):
        s = run(seed, MarketBot(random.Random(seed)), config=fork_only)
        if s.act != 2 or s.sitdown_snapshot is None:
            continue
        opened += 1
        payoff_days.append(s.sitdown_snapshot.payoff_day)
        verdicts = sd.evaluate_chairs(s.sitdown_snapshot, s.evidence)
        missing = [v for v in verdicts if not v.available]
        if not missing:
            full_tables += 1
        else:
            absent_calendar += sum(1 for v in missing
                                   if v.blocker == "calendar")
            absent_case += sum(1 for v in missing if v.blocker == "case")
    print(f"reachability: market bot reaches an open sit-down in "
          f"{opened}/{seeds} seeds ({opened / seeds:.0%}; bar ≥ 55%)")
    if opened:
        payoff_days.sort()
        med = payoff_days[len(payoff_days) // 2]
        q3 = payoff_days[(3 * len(payoff_days)) // 4]
        print(f"  full tables: {full_tables}/{opened} of open sit-downs "
              f"({full_tables / opened:.0%}); absent chairs: "
              f"{absent_calendar} calendar-gated, {absent_case} case-gated")

        def chairs_at(payoff_day):
            from extra_toppings.models import SitdownSnapshot
            vs = sd.evaluate_chairs(SitdownSnapshot(payoff_day, 0.0, 0), [])
            return "".join("+" if v.available else "-"
                           for v in vs if v.chair != "stand_pat")
        print(f"  payoff days: median {med} (chairs {chairs_at(med)}), "
              f"75th pct {q3} (chairs {chairs_at(q3)}); boundaries: "
              + ", ".join(f"day {d}:{chairs_at(d)}"
                          for d in (20, 21, 22, 23, 25, 26)))

    # ── criterion 3: forced-branch chaos completes ───────────────
    class ChaosSale(BotConsole):
        def scene_menu(self, namespace, prompt, options):
            if prompt == "Your chair:" and not getattr(self, "_t", False):
                self._t = True
                return 3
            return len(options) - 1
    crashes = 0
    for seed in range(seeds):
        s = run(seed, ChaosSale(random.Random(seed)), config=sale_on)
        if s.game_over is None:
            crashes += 1
    print(f"crash-freedom: forced-sale chaos completes {seeds - crashes}/"
          f"{seeds} runs")

    # ── criterion 4, escrow rows ─────────────────────────────────
    def escrow_run(bot_cls, seed):
        bot = bot_cls(random.Random(seed))
        s = run(seed, bot, config=sale_on)
        # Entry is latched by the bot's own transcript sniffing — a
        # day-one collapse reverts before the first night hook would see
        # the branch, so state inspection alone undercounts.
        entered = getattr(bot, "_entered_escrow", False) \
            or s.branch == "quiet_sale"
        sold = s.game_over == "sold"
        on_schedule = (not sold) or (
            s.day == s.sitdown_snapshot.payoff_day + 1 + escrow.DILIGENCE_DAYS)
        return {"entered": entered, "sold": sold,
                "on_schedule": on_schedule,
                # The dollar comparison uses the final broker mark before
                # severance (rev. 7 ruling): walking money rewards
                # retaining illicit assets and punishes burning cash.
                "mark": s.branch_state.escrow_mark if sold else None,
                "tier": escrow.sale_tier(s) if sold else None,
                "dirty_locked": sold and (s.dirty + s.warehouse_cash)
                > escrow.DIRTY_TOLERANCE}

    rows = {}
    rates = {}
    for name, cls in (("careful", EscrowBot), ("sloppy", SloppyEscrowBot),
                      ("keeps-stash", KeepsStashBot)):
        entered = closed = off_schedule = 0
        tiers: Counter = Counter()
        per_seed = {}
        for seed in range(seeds):
            r = escrow_run(cls, seed)
            per_seed[seed] = r
            if r["entered"]:
                entered += 1
                if r["sold"]:
                    closed += 1
                    tiers[r["tier"]] += 1
                if not r["on_schedule"]:
                    off_schedule += 1
        rows[name] = per_seed
        rates[name] = closed / entered if entered else 0.0
        bar = "bar ≥ 70%" if name == "careful" else \
            "ablation" if name == "keeps-stash" else "valuation control"
        print(f"{name}: entered {entered}/{seeds}, closed {closed} "
              f"({rates[name]:.0%} of entered; {bar}), off-schedule "
              f"{off_schedule} (bar 0), tiers {dict(tiers)}")
    print(f"ablation drop: careful {rates['careful']:.0%} → keeps-stash "
          f"{rates['keeps-stash']:.0%} "
          f"({(rates['careful'] - rates['keeps-stash']) * 100:.0f} points; "
          f"bar ≥ 20)")

    # Matched seeds where BOTH policies closed: the valuation must be
    # decision-sensitive, not formula-implied.
    matched = [s for s in range(seeds)
               if rows["careful"][s]["sold"] and rows["sloppy"][s]["sold"]]
    if matched:
        diffs = [rows["careful"][s]["mark"]
                 - rows["sloppy"][s]["mark"] for s in matched]
        flips = sum(1 for s in matched
                    if rows["careful"][s]["tier"] != rows["sloppy"][s]["tier"])
        print(f"valuation: {len(matched)} matched closes; careful-minus-"
              f"sloppy median mark ${statistics.median(diffs):,.0f} "
              f"(bar ≥ $1,000); tier flips {flips}/{len(matched)} "
              f"({flips / len(matched):.0%}; bar ≥ 40%, unconditioned)")
        locked = [s for s in matched if rows["careful"][s]["dirty_locked"]
                  and rows["sloppy"][s]["dirty_locked"]]
        print(f"  cash-locked at kept-the-trade in both runs: "
              f"{len(locked)} (diagnostic only — the bar stays "
              f"unconditioned)")
    else:
        print("valuation: no matched closes — study inconclusive")

    _fork_straight(seeds)
    _fork_war(seeds)


def _display_case(state) -> float:
    """The ledger-transparency oracle (§2.7 criterion 4, closed-form
    per rev. 12): an INDEPENDENT recomputation of what the visible
    records display — raw sum, less relief = min(total halvable,
    max(0, raw − 10)), floor-bound displays exactly 10 — certifying
    the CONTRACT rather than repeating the allocator's loop (the
    rev. 11 oracle mirrored the allocator's break and certified its
    own defect). Protection is re-derived from first principles:
    hired, aware, morale ≥ 5, unsettled, and NOT under arrest.
    Deliberately reimplemented here rather than imported, the way the
    golden harness reimplements the legacy projection."""
    settled = set(state.branch_state.settled_witnesses) \
        if state.branch_state is not None else set()
    protected = {e.key for e in state.employees
                 if e.hired and e.aware and e.morale >= 5
                 and not e.arrested and e.key not in settled}
    total = 0.0
    for r in state.evidence:
        total += r.magnitude
    halvable = 0.0
    for r in state.evidence:
        if r.kind == "witness" and r.source in protected:
            halvable += r.magnitude * 0.5
    allowance = total - 10.0
    if halvable > 0 and allowance > 0:
        if halvable >= allowance:
            return 10.0
        total -= halvable
    return max(0.0, min(100.0, total))


def _redemption_state():
    """THE frozen redemption reference entry (rev. 10 item 8): a
    §3.1-shaped month standing at the sit-down morning with Case 31 —
    an immune seizure, the routine hum, a flagged over-ceiling record,
    the informant's tip, and Marcus departed knowing everything,
    hostile until settled. A harness-owned, predeclared literal (like
    the frozen scene schema): the redemption cohort runs THIS entry
    across world seeds, so the original ΔCase bars test what they
    always meant — whether a file with something to redeem actually
    falls."""
    from extra_toppings.models import Evidence, SitdownSnapshot, new_state
    state = new_state()
    state.debt = 0
    state.debt_paid_day = 13
    state.day = 14
    state.clean = 2500
    state.dirty = 1200
    state.shop.reputation = 40.0
    state.shop.ingredients = 40
    state.shop_stash = {"oregano": 8, "mushrooms": 6}
    marcus = next(e for e in state.employees if e.key == "e3")
    marcus.aware = True
    marcus.hired = False
    marcus.morale = 3
    state.evidence = [
        Evidence(day=5, magnitude=10.0, kind="physical",
                 why="product seized in a traffic stop"),
        *[Evidence(day=7, magnitude=0.5, kind="paper", why="")
          for _ in range(6)],
        Evidence(day=9, magnitude=8.0, kind="paper",
                 why="the register claimed $3,000 beyond any plausible "
                     "night's sales"),
        Evidence(day=10, magnitude=4.0, kind="paper",
                 why="an informant's tip put your shop in a file"),
        Evidence(day=11, magnitude=6.0, kind="witness",
                 why="Marcus Webb walked out knowing everything",
                 source="e3"),
    ]
    # 10 + 3 + 8 + 4 + 6 = 31, the §3.1 number.
    state.sitdown_snapshot = SitdownSnapshot(
        payoff_day=13, case_at_lockup=31.0,
        evidence_count_at_lockup=len(state.evidence))
    return state


def _fork_straight(seeds: int) -> None:
    """P2 acceptance rows (§2.7 criterion 4 straight rows + criterion
    5): covert-share collapse, the first falling Case, the earned-exit
    band, the no-remediation ablation, forced-branch crash-freedom, and
    the nightly ledger-transparency and floor assertions."""
    straight_on = GameConfig(fork_enabled=True,
                             enabled_branches=frozenset({"straight"}))

    # ── criterion 3: forced-straight chaos completes ─────────────
    class ChaosStraight(BotConsole):
        def scene_menu(self, namespace, prompt, options):
            if prompt == "Your chair:" and not getattr(self, "_t", False):
                self._t = True
                return 0
            return len(options) - 1
    crashes = 0
    for seed in range(seeds):
        s = run(seed, ChaosStraight(random.Random(seed)), config=straight_on)
        if s.game_over is None:
            crashes += 1
    print(f"crash-freedom: forced-straight chaos completes "
          f"{seeds - crashes}/{seeds} runs")

    # ── criteria 4 and 5: the branch bots ────────────────────────
    def straight_run(bot_cls, seed, state_factory=None):
        bot = bot_cls(random.Random(seed))
        nights = []
        ledger_bad = floor_bad = 0

        def on_night(state, streams):
            nonlocal ledger_bad, floor_bad
            if state.branch != "straight" or state.branch_state is None:
                return
            if state.case != _display_case(state):
                ledger_bad += 1
            if state.branch_state.remediation_used > 0 \
                    and state.case < 10.0:
                floor_bad += 1
            # night() has already advanced the calendar: the completed
            # day is state.day - 1, and legit_revenue_today is its.
            nights.append({"day": state.day - 1,
                           "legit": state.legit_revenue_today})

        s = run(seed, bot, config=straight_on, on_night=on_night,
                state=state_factory() if state_factory else None)
        entered = getattr(bot, "_entered_straight", False) \
            or s.branch == "straight"
        if not entered:
            return {"entered": False}
        fork_day = s.sitdown_snapshot.payoff_day + 1
        covert = sum(take for day, take in bot.covert_by_day.items()
                     if day >= fork_day + 2)
        legit = sum(n["legit"] for n in nights
                    if n["day"] >= fork_day + 2)
        count = s.sitdown_snapshot.evidence_count_at_lockup
        post = s.evidence[count:]
        return {"entered": True, "ending": s.game_over,
                "lockup": s.sitdown_snapshot.case_at_lockup,
                "delta_case": s.case - s.sitdown_snapshot.case_at_lockup,
                "post_accrual": sum(r.magnitude for r in post),
                "remediation_used": s.branch_state.remediation_used
                if s.branch_state else 0.0,
                "settled": len(s.branch_state.settled_witnesses)
                if s.branch_state else 0,
                "covert": covert, "legit": legit,
                "ledger_bad": ledger_bad, "floor_bad": floor_bad}

    # The cohort contract, encoded (rev. 11 item 4): which metrics BIND
    # in which cohort. Everything still prints; nothing nonbinding is
    # ever labeled as a bar.
    NATURAL_SPEC = {"band": True, "delta": False, "below": False,
                    "covert": True, "tag": ""}
    REDEMPTION_SPEC = {"band": False, "delta": True, "below": True,
                       "covert": False, "tag": ""}
    DIAGNOSTIC_SPEC = {"band": False, "delta": False, "below": False,
                       "covert": False, "tag": " [diagnostic]"}

    def straight_rows(pairs, spec, state_factory=None):
        rates = {}
        per_seed = {}
        band_note = ("band 25–70%" if spec["band"]
                     else "reported — no band binds this cohort")
        delta_note = ("bar ≤ −5" if spec["delta"] else "reported")
        below_note = ("bar ≥ 60%" if spec["below"] else "reported")
        covert_note = ("bar < 5%" if spec["covert"] else "reported")
        tag = spec["tag"]
        for name, cls in pairs:
            entered = 0
            endings: Counter = Counter()
            deltas, lockups, used, accrued = [], [], [], []
            settled = 0
            covert = legit = 0
            ledger_bad = floor_bad = 0
            per_seed[name] = {}
            for seed in range(seeds):
                r = straight_run(cls, seed, state_factory)
                per_seed[name][seed] = r
                if not r["entered"]:
                    continue
                entered += 1
                endings[r["ending"]] += 1
                deltas.append(r["delta_case"])
                lockups.append(r["lockup"])
                used.append(r["remediation_used"])
                accrued.append(r["post_accrual"])
                settled += r["settled"]
                covert += r["covert"]
                legit += r["legit"]
                ledger_bad += r["ledger_bad"]
                floor_bad += r["floor_bad"]
            rates[name] = endings["straight_exit"] / entered \
                if entered else 0.0
            below = sum(1 for d in deltas if d < 0)
            share = covert / (covert + legit) if covert + legit else 0.0
            print(f"{name}{tag}: entered {entered}/{seeds}, "
                  f"endings {dict(endings)}")
            print(f"  earned exits {endings['straight_exit']}/{entered} "
                  f"({rates[name]:.0%}; {band_note})")
            if deltas:
                print(f"  ΔCase fork→end: median "
                      f"{statistics.median(deltas):+.1f} ({delta_note}); "
                      f"strictly below fork-day in {below}/{len(deltas)} "
                      f"({below / len(deltas):.0%}; {below_note})")
                print(f"  decomposition: lockup Case median "
                      f"{statistics.median(lockups):.1f} "
                      f"(≥20 in {sum(1 for c in lockups if c >= 20)}"
                      f"/{len(lockups)}); post-fork accrual median "
                      f"+{statistics.median(accrued):.1f}; paid "
                      f"remediation median {statistics.median(used):.1f} "
                      f"of the 25 cap; settlements {settled}")
                hot = [d for c, d in zip(lockups, deltas) if c >= 20]
                if hot:
                    print(f"  diagnostic (entries at lockup ≥ 20 only — "
                          f"the bars stay unconditioned): median ΔCase "
                          f"{statistics.median(hot):+.1f}, below fork-day "
                          f"{sum(1 for d in hot if d < 0)}/{len(hot)}")
            print(f"  covert revenue share after fork+2: ${covert:,} of "
                  f"${covert + legit:,} ({share:.1%}; {covert_note})")
            print(f"  ledger transparency: {ledger_bad} bad nights "
                  f"(bar 0); floor: {floor_bad} sub-floor remediated "
                  f"nights (bar 0)")
        return rates, per_seed

    print("— natural-entry cohort (the unmodified smart-bot baseline, "
          "rev. 10 item 8) —")
    rates, per_seed = straight_rows(
        (("straight", StraightBot),
         ("no-remediation", NoRemediationBot)), NATURAL_SPEC)
    print(f"natural ablation (reported, not a bar in this cohort): "
          f"straight {rates['straight']:.0%} → no-remediation "
          f"{rates['no-remediation']:.0%} "
          f"({(rates['straight'] - rates['no-remediation']) * 100:.0f} "
          f"points)")
    # The natural cohort's paired bar (rev. 10): the same month,
    # remediated vs not, seed by seed.
    matched = [s for s in range(seeds)
               if per_seed["straight"][s]["entered"]
               and per_seed["no-remediation"][s]["entered"]]
    if matched:
        diffs = [per_seed["straight"][s]["delta_case"]
                 - per_seed["no-remediation"][s]["delta_case"]
                 for s in matched]
        helped = sum(1 for d in diffs if d < 0)
        print(f"natural paired bar: remediation left the file lower in "
              f"{helped}/{len(matched)} matched entries "
              f"({helped / len(matched):.0%}; bar ≥ 60%); "
              f"remediated-minus-unremediated ΔCase median "
              f"{statistics.median(diffs):+.1f}")

    # ── the redemption cohort (rev. 10 item 8) ───────────────────
    print("— redemption cohort (the frozen §3.1 reference entry, "
          "Case 31, across world seeds; the original ΔCase letter "
          "binds here) —")
    red_rates, red_seed = straight_rows(
        (("redemption", StraightBot),
         ("redemption-no-remediation", NoRemediationBot)),
        REDEMPTION_SPEC, state_factory=_redemption_state)
    print(f"redemption ablation drop: "
          f"{red_rates['redemption']:.0%} → "
          f"{red_rates['redemption-no-remediation']:.0%} "
          f"({(red_rates['redemption'] - red_rates['redemption-no-remediation']) * 100:.0f} points; bar ≥ 20)")
    # Rev. 11: the review's suggested single-verb diagnostics — the
    # combined control is guaranteed to fail its hostile-witness term,
    # so these separate what each verb is worth. Not bars.
    print("— redemption single-verb diagnostics (rev. 11; not bars) —")
    straight_rows((("counsel-only", CounselOnlyBot),
                   ("settlement-only", SettlementOnlyBot)),
                  DIAGNOSTIC_SPEC, state_factory=_redemption_state)

    # ── diagnostic: the same branch policy over a dirty month ────
    # The §3.1 vignette enters the fork at Case 31; the market bot's
    # median entry is far colder. This variant plays a crime-heavy
    # Act I (over-ceiling washes, read-in crew, night jobs), then the
    # identical branch policy — separating "the mechanics can't lower
    # the file" from "this baseline brings nothing to lower."
    class DirtyMonthStraightBot(StraightBot):
        launder_all = True
        do_raids = True
        cover_stops = 2
        debt_float = 2500
        MENU_PREFS: ClassVar = list(CrimeHeavyBot.MENU_PREFS)
        AVOID: ClassVar = [a for a in CrimeHeavyBot.AVOID
                           if a not in ("Improvements", "Talk to a rival",
                                        "Market board")]

    class DirtyMonthNoRemediation(DirtyMonthStraightBot):
        use_counsel = False
        use_settlements = False

    print("— dirty-month diagnostic (crime-heavy Act I, same branch "
          "policy; §3.1's entry profile; not bars) —")
    dirty_rates, _ = straight_rows(
        (("dirty-month", DirtyMonthStraightBot),
         ("dirty-no-remediation", DirtyMonthNoRemediation)),
        DIAGNOSTIC_SPEC)
    print(f"dirty-month ablation drop [diagnostic]: "
          f"{dirty_rates['dirty-month']:.0%} → "
          f"{dirty_rates['dirty-no-remediation']:.0%} "
          f"({(dirty_rates['dirty-month'] - dirty_rates['dirty-no-remediation']) * 100:.0f} points)")


def _fork_war(seeds: int) -> None:
    """P3 acceptance rows (§2.7 war rows as amended by rev. 14):
    median end strength, the gross-accrual evidence share, the
    per-campaign applied-damage channel mix, the branch-good band,
    three ablations, forced-war chaos, and the nightly reconciliation
    and ledger-transparency oracles — plus the raid-pricing decline
    curve re-verified at war cadence."""
    war_on = GameConfig(fork_enabled=True,
                        enabled_branches=frozenset({"war"}))

    print("— the Harbor War (§2.7 war rows, rev. 14 amendments) —")

    # ── criterion 3: forced-war chaos completes ──────────────────
    class ChaosWar(BotConsole):
        def scene_menu(self, namespace, prompt, options):
            if prompt == "Your chair:" and not getattr(self, "_t", False):
                self._t = True
                return 2
            return len(options) - 1
    crashes = 0
    for seed in range(seeds):
        s = run(seed, ChaosWar(random.Random(seed)), config=war_on)
        if s.game_over is None:
            crashes += 1
    print(f"crash-freedom: forced-war chaos completes "
          f"{seeds - crashes}/{seeds} runs")

    def war_run(bot_cls, seed):
        import hashlib
        import json as _json
        from extra_toppings import save as _save
        bot = bot_cls(random.Random(seed))
        recon_bad = ledger_bad = 0
        gross: Counter = Counter()
        seen = {"n": None, "pre": None}
        amber_nights = {"n": 0}
        # The pacing letter's exposure ledger (rev. 16 item 5) and the
        # exposure-matched heat probe (item 7), both read at night:
        # each incoming raid telegraph is one 0→armed transition of a
        # rival's warning; injury exposure is crew-nights spent hurt;
        # turf units are the day's sales on live-campaign turf.
        prev_warn: dict = {}
        exposure = {"retal": 0, "injury": 0}

        def on_night(state, streams):
            nonlocal recon_bad, ledger_bad
            if state.branch is None:
                # The entry fingerprint (rev. 15): every branch
                # ablation must reach the fork from a state-hash-
                # identical month — the last pre-branch night's full
                # state is the fingerprint the fleets must share.
                seen["pre"] = hashlib.md5(_json.dumps(
                    _save.state_to_dict(state),
                    sort_keys=True).encode()).hexdigest()
            if state.branch != "war" or state.branch_state is None:
                return
            for dk in data.DISTRICTS:
                from extra_toppings.models import district_heat_policy
                if district_heat_policy(state, dk).band != "cool":
                    amber_nights["n"] += 1
            for k, rv in state.rivals.items():
                if prev_warn.get(k, 0) == 0 and rv.raid_warning > 0:
                    exposure["retal"] += 1
                prev_warn[k] = rv.raid_warning
            exposure["injury"] += sum(
                1 for e in state.hired() if e.injured_days > 0)
            if seen["n"] is None:
                # First war night: everything before the lock-up count
                # is pre-fork by construction (the scene adds nothing).
                seen["n"] = state.sitdown_snapshot.evidence_count_at_lockup
            # The reconciliation oracle: campaign starting strength
            # minus current strength equals its records, exactly.
            for c in state.branch_state.campaigns:
                spent = sum(dr.hundredths for dr in c.damage)
                if round(state.rivals[c.rival_key].strength * 100) \
                        != c.starting_hundredths - spent:
                    recon_bad += 1
            if state.case != _display_case(state):
                ledger_bad += 1

        s = run(seed, bot, config=war_on, on_night=on_night)
        entered = getattr(bot, "_entered_war", False) or s.branch == "war"
        if not entered or not s.branch_state or not s.branch_state.campaigns:
            return {"entered": False, "pre_hash": seen["pre"]}
        camps = s.branch_state.campaigns
        first = camps[0]
        ratio = (round(s.rivals[first.rival_key].strength * 100)
                 / first.starting_hundredths)
        broken = [c for c in camps if c.broken_day is not None]
        mixes = []
        for c in broken:
            spent: Counter = Counter()
            for dr in c.damage:
                spent[dr.channel] += dr.hundredths
            total = sum(spent.values())
            mixes.append({ch: n / total for ch, n in spent.items()})
        agg: Counter = Counter()
        for c in camps:
            for dr in c.damage:
                agg[dr.channel] += dr.hundredths
        # Post-fork accrual read from the IMMUTABLE accrued field at
        # the end of the run (rev. 16 item 1) — remediation can no
        # longer make the denominator lie. Suspicion top-ups are
        # remediation bookkeeping, excluded from both sums.
        count = s.sitdown_snapshot.evidence_count_at_lockup
        post = [r for r in s.evidence[count:] if r.kind != "suspicion"]
        for r in post:
            gross[r.kind] += r.accrued
            if r.kind == "witness" and not r.source:
                gross["witness_ext"] += r.accrued
        pp = gross.get("pattern", 0.0) + gross.get("physical", 0.0)
        g_total = sum(v for k, v in gross.items() if k != "witness_ext")
        immune = pp + gross.get("legacy", 0.0) + gross.get("witness_ext",
                                                           0.0)
        # The three evidence quantities from the ONE canonical ledger
        # view (rev. 17 item 5): gross accrued, permanent residue
        # after contests and settlements, live effective contribution
        # after retention protection.
        from extra_toppings import evidence as ev_mod
        q = ev_mod.ledger_quantities(s, start=count)
        lockup_case = s.sitdown_snapshot.case_at_lockup
        good = s.game_over in war_mod.GOOD_ENDINGS
        corner_h = sum(dr.hundredths for c in camps for dr in c.damage
                       if dr.channel == "corners")
        # The TYPED attempt ledger (rev. 18 item 3): every post-fork
        # outgoing job by its day — the first war night included, the
        # denominator honest about scrubs, crews and actual damage.
        attempts = [e for e in s.raid_log if e.day >= first.declared_day]
        ran = [e for e in attempts if e.outcome != "scrubbed"]
        # Route exposure at EXECUTION time (rev. 18 item 4): the typed
        # route records carry the band the route actually ran under —
        # an exposure is a route that executed on live target turf
        # past cool, nothing else counts.
        contested = [r for r in s.route_log if r.contested]
        exposed = [r for r in contested if r.heat_band != "cool"]
        return {"entered": True, "ending": s.game_over, "ratio": ratio,
                "broken": len(broken), "mixes": mixes, "agg": agg,
                "pp_share": pp / g_total if g_total else None,
                "immune_share": immune / g_total if g_total else None,
                "gross": dict(gross), "g_total": g_total,
                "residue_share": (q["residue"] / q["accrued"]
                                  if q["accrued"] else None),
                "live_share": (q["effective"] / q["accrued"]
                               if q["accrued"] else None),
                "above_fork": s.case > lockup_case,
                "second_front": len(camps) >= 2,
                "salvage_collected": sum(
                    1 for c in camps if c.salvage_day is not None),
                "attempts": len(attempts), "ran": len(ran),
                "scrubbed": len(attempts) - len(ran),
                "attempt_damage": sum(e.damage_h for e in ran) / 100,
                "crew_nights": sum(e.crew for e in ran),
                "committed_crew_nights": sum(e.crew for e in attempts),
                "good": good, "recon_bad": recon_bad,
                "ledger_bad": ledger_bad, "pre_hash": seen["pre"],
                "amber_nights": amber_nights["n"],
                "corner_damage": corner_h / 100,
                "jobs_damage": agg.get("jobs", 0) / 100,
                "retal_raids": exposure["retal"],
                "injury_nights": exposure["injury"],
                "turf_units": sum(r.units_sold for r in contested),
                "turf_amber": len(exposed),
                "exposed_units": sum(r.units_sold for r in exposed),
                "exposed_corner": sum(r.corner_damage_h
                                      for r in exposed) / 100,
                "war_pay": s.branch_state.war_pay_paid,
                "short": s.branch_state.war_pay_short_nights}

    def war_rows(name, cls, note):
        entered = 0
        endings: Counter = Counter()
        ratios, pp_shares = [], []
        goods = 0
        mix_worst = []
        agg: Counter = Counter()
        recon_bad = ledger_bad = 0
        pay_tot = short_tot = 0
        kind_shares: dict = defaultdict(list)
        jobs_ran = []
        scrub_tot = 0
        per_seed = {}
        amber_tot = 0
        corner_tot: list = []
        residue_sh: list = []
        live_sh: list = []
        above_fork = second_fronts = salvage_n = second_caps = 0
        for seed in range(seeds):
            r = war_run(cls, seed)
            per_seed[seed] = r
            if not r["entered"]:
                continue
            amber_tot += r["amber_nights"]
            corner_tot.append(r["corner_damage"])
            entered += 1
            endings[r["ending"]] += 1
            ratios.append(r["ratio"])
            if r["pp_share"] is not None:
                pp_shares.append(r["pp_share"])
                kind_shares["immune"].append(r["immune_share"])
                for kind in ("pattern", "physical", "paper", "witness",
                             "witness_ext"):
                    kind_shares[kind].append(
                        r["gross"].get(kind, 0.0) / r["g_total"])
            if r["residue_share"] is not None:
                residue_sh.append(r["residue_share"])
                live_sh.append(r["live_share"])
            above_fork += r["above_fork"]
            second_fronts += r["second_front"]
            salvage_n += r["salvage_collected"]
            second_caps += r["broken"] >= 2
            jobs_ran.append(r["ran"])
            scrub_tot += r["scrubbed"]
            goods += r["good"]
            for m in r["mixes"]:
                mix_worst.append(max(m.values()))
            agg.update(r["agg"])
            recon_bad += r["recon_bad"]
            ledger_bad += r["ledger_bad"]
            pay_tot += r["war_pay"]
            short_tot += r["short"]
        rate = goods / entered if entered else 0.0
        print(f"{name}: entered {entered}/{seeds}, endings {dict(endings)}"
              f"  ({note})")
        if not entered:
            return rate
        print(f"  branch-good (target broken by day 30) {goods}/{entered} "
              f"({rate:.0%})")
        print(f"  median end strength vs fork-day "
              f"{statistics.median(ratios):.0%}")
        if residue_sh:
            # The three quantities, one canonical view (rev. 17 item
            # 5): gross accrued is the denominator; the PERMANENT
            # residue after contests and settlements carries the
            # rev. 16 bar (reversible dormancy is not remediation);
            # the live effective contribution is reported beside it.
            print(f"  remediation resistance: median "
                  f"{statistics.median(residue_sh):.0%} of post-fork "
                  f"ACCRUED evidence survives as PERMANENT residue "
                  f"(bar ≥ 50%); live effective after retention relief "
                  f"median {statistics.median(live_sh):.0%} [reported]; "
                  f"Case above fork-day despite remediation in "
                  f"{above_fork}/{entered} "
                  f"({above_fork / entered:.0%}; bar ≥ 60%)")
        if pp_shares:
            print(f"  pattern+physical share of gross accrual "
                  f"[decomposition, on accrued values]: median "
                  f"{statistics.median(pp_shares):.0%}")
            kinds = " / ".join(
                f"{k} {statistics.median(v):.0%}"
                for k, v in kind_shares.items() if v and k != "immune")
            print(f"  gross accrual by kind, median shares "
                  f"[decomposition]: {kinds}")
        print(f"  the second front [longitudinal]: declared in "
              f"{second_fronts}/{entered}, salvage collected "
              f"{salvage_n}, double captures {second_caps}, syndicate "
              f"endings {endings.get('syndicate', 0)}")
        if jobs_ran:
            print(f"  post-fork jobs run: median "
                  f"{statistics.median(jobs_ran):.0f}, scrubbed "
                  f"{scrub_tot} across the fleet [decomposition, from "
                  f"the attempt ledger]")
        if mix_worst:
            over = sum(1 for w in mix_worst if w > 0.60)
            print(f"  channel mix: worst single-channel share of applied "
                  f"damage per broken campaign, median "
                  f"{statistics.median(mix_worst):.0%}, max "
                  f"{max(mix_worst):.0%}; campaigns over 60%: {over}")
        total = sum(agg.values())
        if total:
            mix = " / ".join(f"{ch} {n / total:.0%}"
                             for ch, n in sorted(agg.items()))
            print(f"  aggregate mix [diagnostic]: {mix}")
        print(f"  war pay paid ${pay_tot:,} across the fleet; "
              f"{short_tot} short nights")
        print(f"  reconciliation oracle: {recon_bad} bad nights (bar 0); "
              f"ledger transparency: {ledger_bad} bad nights (bar 0)")
        return rate, per_seed, amber_tot, corner_tot

    mixed, war_seed, war_amber, war_corner = war_rows(
        "war", WarBot, "the mixed campaign — bars bind here")
    fleets = {
        "raid-only": war_rows("raid-only", RaidOnlyBot,
                              "ablation: no proactive non-job channel"),
        "cooldown": war_rows("cooldown", CooldownRaiderBot,
                             "ablation: raids on cooldown ignoring "
                             "alertness"),
        "neglect": war_rows("neglect", NeglectWarBot,
                            "ablation: no cover, no pantry"),
    }
    # Ablation entry identity (rev. 15): every fleet reaches the fork
    # from the same month, seed by seed — pre-fork state hash AND the
    # entered flag must agree with the mixed bot's.
    divergent = 0
    for name, (_r, per_seed, _a, _c) in fleets.items():
        for seed in range(seeds):
            a, b = war_seed[seed], per_seed[seed]
            if a["entered"] != b["entered"] \
                    or a["pre_hash"] != b["pre_hash"]:
                divergent += 1
    print(f"ablation entry identity: {divergent} divergent "
          f"(fleet, seed) pairs (bar 0)")
    raid_only = fleets["raid-only"][0]
    cooldown = fleets["cooldown"][0]
    neglect = fleets["neglect"][0]
    print(f"raid-only trails mixed: {mixed:.0%} → {raid_only:.0%} "
          f"({(mixed - raid_only) * 100:.0f} points; bar ≥ 15)")
    print(f"restaurant-neglect, branch-good [decomposition — the bar "
          f"moved to the empire letter, rev. 17 item 7]: "
          f"{mixed:.0%} → {neglect:.0%} "
          f"({(mixed - neglect) * 100:.0f} points)")

    # The empire letter (rev. 17 item 7), binding at 500 seeds: a
    # hollow restaurant can win one street fight, but it cannot
    # sustain control of the city — the maintained restaurant must
    # beat neglect in UNCONDITIONAL Syndicate-ending rate by ≥ 15
    # points. Conversion, Burned Out, payroll failures and witness
    # accrual ship as decomposition per fleet above.
    def _synd_rate(per):
        ent = [r for r in per.values() if r["entered"]]
        return (sum(1 for r in ent if r["ending"] == "syndicate")
                / len(ent)) if ent else 0.0
    m_synd = _synd_rate(war_seed)
    n_synd = _synd_rate(fleets["neglect"][1])
    print(f"the empire letter [binding at 500 seeds]: unconditional "
          f"Syndicate rate — maintained {m_synd:.0%} vs neglect "
          f"{n_synd:.0%} ({(m_synd - n_synd) * 100:.0f} points; "
          f"bar ≥ 15)")

    # The pacing rows (rev. 18 item 3): the fleet comparison is a
    # PAIRED OBSERVATIONAL DECOMPOSITION — the policies share only
    # entry state and diverge after — reported under exact names:
    # executed-job efficiency, executed person-night efficiency, and
    # planned/committed efficiency (scrubs in the denominator). The
    # CAUSAL claim lives in the fixed-opportunity experiment below;
    # the 500-seed outcome bar keeps the last word.
    med = statistics.median
    cool_seed = fleets["cooldown"][1]
    per_job: dict = {"paced": [], "cooldown": []}
    per_pn: dict = {"paced": [], "cooldown": []}
    per_cm: dict = {"paced": [], "cooldown": []}
    retal: dict = {"paced": [], "cooldown": []}
    injury: dict = {"paced": [], "cooldown": []}
    for seed in range(seeds):
        pair = {"paced": war_seed[seed], "cooldown": cool_seed[seed]}
        if not all(r["entered"] for r in pair.values()):
            continue
        for label, r in pair.items():
            if r["ran"]:
                per_job[label].append(r["attempt_damage"] / r["ran"])
            if r["crew_nights"]:
                per_pn[label].append(r["attempt_damage"]
                                     / r["crew_nights"])
            if r["committed_crew_nights"]:
                per_cm[label].append(r["attempt_damage"]
                                     / r["committed_crew_nights"])
            retal[label].append(r["retal_raids"])
            injury[label].append(r["injury_nights"])
    if per_job["paced"] and per_job["cooldown"]:
        print(f"pacing, paired observational decomposition "
              f"[entry-identical seeds, then divergent play]: "
              f"executed-job efficiency — paced "
              f"{med(per_job['paced']):.1f} vs cooldown "
              f"{med(per_job['cooldown']):.1f} strength/job; executed "
              f"person-night efficiency — {med(per_pn['paced']):.1f} "
              f"vs {med(per_pn['cooldown']):.1f}; planned/committed "
              f"person-night efficiency (scrubs in the denominator) — "
              f"{med(per_cm['paced']):.1f} vs "
              f"{med(per_cm['cooldown']):.1f}; retaliation telegraphs "
              f"per war — {med(retal['paced']):g} vs "
              f"{med(retal['cooldown']):g}; injured-crew nights per "
              f"war — {med(injury['paced']):g} vs "
              f"{med(injury['cooldown']):g}")
    _pacing_fixed_opportunity(trials=800)
    trail = "holds" if mixed >= cooldown else "TRAILS"
    print(f"the full policy vs cooldown [binding at 500 seeds]: "
          f"{mixed:.0%} vs {cooldown:.0%} — must not trail ({trail})")

    # The causal heat report (rev. 15): the same mixed fleet with the
    # district teeth neutralized — heat's contribution measured, not
    # asserted by unit test. Diagnostic; the teeth constants restore
    # before anything else runs.
    from extra_toppings import models as _models
    saved = (_models.HEAT_AMBER, _models.HEAT_RED)
    try:
        _models.HEAT_AMBER = _models.HEAT_RED = 10 ** 9
        off_rate, off_seed, off_amber, off_corner = war_rows(
            "war-no-heat-teeth", WarBot,
            "diagnostic: heat policy off — the causal report")
    finally:
        _models.HEAT_AMBER, _models.HEAT_RED = saved
    print(f"causal heat report [diagnostic]: teeth ON — "
          f"{war_amber} amber/red district-nights across the fleet, "
          f"median corner damage {med(war_corner) if war_corner else 0:g}, "
          f"branch-good {mixed:.0%}; teeth OFF — {off_amber} exposure "
          f"nights, median corner damage "
          f"{med(off_corner) if off_corner else 0:g}, branch-good "
          f"{off_rate:.0%}")
    # Exposure-matched (rev. 16 item 7, sampled at EXECUTION time per
    # rev. 18 item 4): the same seeds paired ON/OFF, restricted to
    # wars where a route ACTUALLY EXECUTED on live target turf under
    # amber/red — the typed route records carry the band the wagon
    # ran under, so no cooled-off or route-less hot night counts.
    exp = [(war_seed[s], off_seed[s]) for s in range(seeds)
           if war_seed[s]["entered"] and off_seed[s]["entered"]
           and war_seed[s]["turf_amber"] > 0]
    if exp:
        n_exposed = sum(a["turf_amber"] for a, _ in exp)
        print(f"heat, exposure-matched [{len(exp)} wars with "
              f"{n_exposed} routes executed on live turf past cool, "
              f"paired ON/OFF]: target-turf units sold "
              f"{med([a['turf_units'] for a, _ in exp]):g} vs "
              f"{med([b['turf_units'] for _, b in exp]):g}; units on "
              f"the exposed routes themselves (ON arm) "
              f"{med([a['exposed_units'] for a, _ in exp]):g}; corner "
              f"damage {med([a['corner_damage'] for a, _ in exp]):g} vs "
              f"{med([b['corner_damage'] for _, b in exp]):g} — the "
              f"burned neighborhood must cost custom (ON at or below "
              f"OFF)")
    else:
        print("heat, exposure-matched: no routes executed on live "
              "turf past cool at this depth — the controlled probe "
              "below carries the causal claim; heat stays a local "
              "route tax")

    _heat_exposure_probe(trials=400)
    _raid_decline_at_war_cadence(trials=2000)


def _heat_exposure_probe(trials: int = 400) -> None:
    """Rev. 16 item 7's controlled arm: one route night on the live
    target's turf — same shop, same cargo, same draws, and the SAME
    55-point heat in both arms; the only difference is whether the
    policy's teeth read that heat as amber. The legacy risk channel
    cancels exactly (risk reads the heat VALUE, equal in both arms),
    so what's left is the customer-pool coupling: halved stops and a
    halved effective corner cap. Diagnostic patching, like the causal
    report — the teeth constants restore before anything else runs."""
    from extra_toppings import models as _models
    from extra_toppings import routes as _routes
    from extra_toppings.models import BranchState, set_relation
    from extra_toppings.ui import Console

    class _Sell(Console):
        """Rides along, sells every stop, plays every stop cool."""
        def __init__(self):
            super().__init__()
            self.quiet = True

        def say(self, text=""):
            pass

        def bullet(self, text):
            pass

        def menu(self, prompt, options):
            return 0

    dk = "meadows"                 # the target's BIG turf: stops bind
    target = data.DISTRICTS[dk]["rival"]

    def night(seed, teeth):
        saved = (_models.HEAT_AMBER, _models.HEAT_RED)
        if not teeth:
            _models.HEAT_AMBER = _models.HEAT_RED = 10 ** 9
        try:
            state = new_state()
            state.day, state.act = 15, 2
            state.debt, state.debt_paid_day = 0, 14
            state.branch = "war"
            state.branch_state = BranchState.war(
                war_target=target, declared_day=14,
                starting_strength=state.rivals[target].strength)
            set_relation(state, target,
                         min(state.rivals[target].relation,
                             _models.VENDETTA_RELATION))
            market.roll_prices(state, random.Random(9000 + seed))
            state.districts[dk].heat = 55.0
            driver = next(e for e in state.employees if e.hired)
            # A LEGAL manifest (rev. 17 item 3): 24 units of bulk-1
            # goods fill the 24-slot wagon exactly — validated by the
            # same RouteManifest the game refuses illegal loads with.
            plan = {"district": dk, "driver": driver,
                    "cargo": {"mushrooms": 12, "hot_honey": 12},
                    "legit": 0, "ride_along": True}
            _routes.RouteManifest.of_plan(plan)
            report = _routes.resolve_route(state, plan, _Sell(),
                                           random.Random(seed))
            camp = state.branch_state.campaigns[0]
            corner = sum(dr.hundredths for dr in camp.damage
                         if dr.channel == "corners") / 100
            return report["sold"], corner
        finally:
            _models.HEAT_AMBER, _models.HEAT_RED = saved

    on_sold, on_corner, off_sold, off_corner = [], [], [], []
    for seed in range(trials):
        sold, corner = night(seed, True)
        on_sold.append(sold)
        on_corner.append(corner)
        sold, corner = night(seed, False)
        off_sold.append(sold)
        off_corner.append(corner)
    m = statistics.mean
    print(f"heat, controlled [one route night on {dk}, heat 55 in "
          f"BOTH arms, {trials} paired trials]: units sold "
          f"{m(on_sold):.1f} amber vs {m(off_sold):.1f} cool-read; "
          f"corner damage {m(on_corner):.2f} vs {m(off_corner):.2f} — "
          f"the halved customer pool must cost custom and cap the "
          f"corner take")


def _pacing_mech_rng(seed: int, day: int) -> random.Random:
    """Raid-MECHANICS dice for one calendar night — a pure function
    of (seed, day, channel), so skipping a night cannot shift any
    later night's dice (rev. 19 item 3)."""
    return random.Random(f"{seed}/{day}/mech")


def _pacing_bot_rng(seed: int, day: int) -> random.Random:
    """Decision dice for one calendar night — same keying."""
    return random.Random(f"{seed}/{day}/bot")


PACING_HORIZON = 12
PACING_START_DAY = 15


def _pacing_rollout(seed: int, policy) -> tuple:
    """One arm of the fixed-opportunity experiment: a declared-war
    state built from `seed`, rolled over the fixed horizon.
    `policy(night_index, rival)` says whether to attempt tonight.
    Ordering mirrors production's night exactly: the raid (if any)
    runs first, then THE canonical quiet-night alertness transition
    (models.alertness_decay_tick — a raid tonight blocks tonight's
    decay, rev. 19 item 3). Returns (total damage, attempts,
    injury-days, committed person-nights)."""
    from extra_toppings.models import (BranchState, VENDETTA_RELATION,
                                       alertness_decay_tick,
                                       set_relation)
    rng_world = random.Random(seed)
    st = new_state()
    market.roll_prices(st, rng_world)
    st.warehouse = {}
    st.day = PACING_START_DAY
    st.debt = 0
    st.debt_paid_day = PACING_START_DAY - 1
    st.act = 2
    st.branch = "war"
    st.branch_state = BranchState.war(
        war_target="vinnie", declared_day=PACING_START_DAY,
        starting_strength=st.rivals["vinnie"].strength)
    set_relation(st, "vinnie", min(st.rivals["vinnie"].relation,
                                   VENDETTA_RELATION))
    crew = st.employees[:3]
    for e in crew:
        e.hired = e.aware = True
    rival = st.rivals["vinnie"]
    start_h = round(rival.strength * 100)
    attempts = injury_days = person_nights = 0
    for night in range(PACING_HORIZON):
        day = PACING_START_DAY + night
        st.day = day
        team = [e for e in crew if e.available]
        if team and rival.alive and policy(night, rival):
            plan = {"rival": "vinnie", "objective": "steal_stock",
                    "team": team, "armed": False,
                    "wagon_free": True, "table_warned": True}
            person_nights += len(team)
            raids.run_raid(st, plan,
                           BotConsole(_pacing_bot_rng(seed, day)),
                           _pacing_mech_rng(seed, day))
            attempts += 1
        alertness_decay_tick(rival, day)     # production's ordering
        for e in crew:
            if e.injured_days > 0:
                injury_days += 1
                e.injured_days -= 1
    damage = (start_h - round(rival.strength * 100)) / 100
    return damage, attempts, injury_days, person_nights


def _pacing_fixed_opportunity(trials: int = 800) -> None:
    """The CAUSAL pacing experiment (rev. 18 item 3; paired IN FACT
    per rev. 19 item 3): both arms start from the IDENTICAL
    declared-war state and every calendar night carries its own
    decision and mechanics dice, keyed by (seed, day, channel) — a
    night the paced arm skips cannot shift any later night's dice.
    The alertness transition is the production function itself.
    Attack-side only: retaliation is not simulated; the injury
    ledger prices the fights the jobs themselves buy. The paired
    difference carries the causal claim; the 500-seed outcome bar
    remains the arbiter of the whole trade."""
    def paced(night, rival):
        return rival.alertness < 4.0         # the security word

    def grind(night, rival):
        return True

    rows: dict = {"paced": [], "grind": []}
    for seed in range(trials):
        rows["paced"].append(_pacing_rollout(seed, paced))
        rows["grind"].append(_pacing_rollout(seed, grind))

    def mean_se(vals):
        m = statistics.fmean(vals)
        se = (statistics.stdev(vals) / (len(vals) ** 0.5)
              if len(vals) > 1 else 0.0)
        return m, se

    p_d = [r[0] for r in rows["paced"]]
    g_d = [r[0] for r in rows["grind"]]
    paired = [a - b for a, b in zip(p_d, g_d)]
    pm, pse = mean_se(p_d)
    gm, gse = mean_se(g_d)
    dm, dse = mean_se(paired)
    p_eff = (sum(p_d) / max(1, sum(r[3] for r in rows["paced"])))
    g_eff = (sum(g_d) / max(1, sum(r[3] for r in rows["grind"])))
    print(f"pacing, fixed-opportunity [CAUSAL: state-matched arms, "
          f"calendar-keyed dice, {trials} paired trials, "
          f"{PACING_HORIZON}-night horizon]: total applied strength "
          f"damage — window-paced {pm:.1f}±{pse:.1f} vs every-night "
          f"{gm:.1f}±{gse:.1f} (paired Δ {dm:+.1f}±{dse:.1f}); per "
          f"committed person-night — {p_eff:.2f} vs {g_eff:.2f}; jobs "
          f"attempted "
          f"{statistics.fmean(r[1] for r in rows['paced']):.1f} vs "
          f"{statistics.fmean(r[1] for r in rows['grind']):.1f}; "
          f"injured-crew days "
          f"{statistics.fmean(r[2] for r in rows['paced']):.1f} vs "
          f"{statistics.fmean(r[2] for r in rows['grind']):.1f} "
          f"[attack-side only; the 500-seed outcome bar is the "
          f"arbiter of the whole trade]")


def _raid_decline_at_war_cadence(trials: int = 2000) -> None:
    """The §7 P3 gate's last row: the alertness decline curve
    re-verified AT WAR CADENCE — the same three-job probe as the
    `raids` study, seated in a declared war, paced like the war bot
    actually raids. ONE propagated trial count (rev. 15: the round-10
    'drift' was a 300-vs-2,000 comparison, retracted), 2,000 being
    round 5's recorded depth, with paired per-attempt uncertainty."""
    from extra_toppings.models import BranchState, VENDETTA_RELATION
    from extra_toppings.models import set_relation

    def probe(spacing_nights):
        # The raid_roi decline probe's exact setup — same crew, same
        # storage removal, same stock-value metric, same per-attempt
        # bot seeds — seated in a declared war.
        values: list = [[], [], []]
        succ = [0, 0, 0]
        for seed in range(trials):
            rng = random.Random(seed)
            st = new_state()
            market.roll_prices(st, rng)
            st.warehouse = {}
            st.day = 15
            st.debt = 0
            st.debt_paid_day = 14
            st.act = 2
            st.branch = "war"
            st.branch_state = BranchState.war(
                war_target="vinnie", declared_day=15,
                starting_strength=st.rivals["vinnie"].strength)
            set_relation(st, "vinnie",
                         min(st.rivals["vinnie"].relation,
                             VENDETTA_RELATION))
            crew = st.employees[:3]
            for e in crew:
                e.hired = e.aware = True
            rival = st.rivals["vinnie"]
            for attempt in range(3):
                if attempt:
                    # Legal calendar (rev. 20 item 3): quiet nights sit
                    # strictly BETWEEN attempts, and every attempt takes
                    # a fresh day — the decay count per gap is unchanged
                    # (the canonical tick is blocked on raid nights), so
                    # the alertness arithmetic and the curve hold.
                    from extra_toppings.models import alertness_decay_tick
                    for _ in range(spacing_nights):
                        st.day += 1
                        alertness_decay_tick(rival, st.day)
                    st.day += 1
                def stock_value(s):
                    total = sum(u * data.GOODS[g]["base"]
                                for g, u in s.shop_stash.items())
                    return total + sum(u * data.GOODS[g]["base"]
                                       for g, u in (s.warehouse or {}).items())
                before = stock_value(st)
                plan = {"rival": "vinnie", "objective": "steal_stock",
                        "team": [e for e in crew if e.available],
                        "armed": False, "wagon_free": True}
                if not plan["team"]:
                    break
                raids.run_raid(
                    st, plan, BotConsole(random.Random(seed * 3 + attempt)),
                    rng)
                gained = stock_value(st) - before
                values[attempt].append(gained)
                succ[attempt] += gained > 0
                for e in crew:
                    e.injured_days = 0
        return values, succ

    def mean_se(vals):
        m = statistics.fmean(vals)
        se = (statistics.stdev(vals) / (len(vals) ** 0.5)
              if len(vals) > 1 else 0.0)
        return m, se

    curves = {}
    for spacing, label in ((0, "consecutive (the round-5 comparison)"),
                           (2, "war cadence (two quiet nights between)")):
        values, succ = probe(spacing)
        curves[spacing] = values
        row = " → ".join("${:,.0f}±{:.0f}".format(*mean_se(values[i]))
                         for i in range(3))
        rates = " / ".join(f"{succ[i] / trials:.0%}" for i in range(3))
        print(f"raid decline at war posture ({trials} trials), {label}: "
              f"expected $/attempt {row} (success {rates})")
    # Paired uncertainty: same seeds, spacing 2 minus spacing 0.
    diffs = []
    for i in range(3):
        paired = [b - a for a, b in zip(curves[0][i], curves[2][i])]
        diffs.append("+${:,.0f}±{:.0f}".format(*mean_se(paired)))
    print(f"  pacing's paired repayment per attempt: {' / '.join(diffs)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("experiment", choices=["sweep", "grid", "policy",
                                           "trajectory", "raids", "events",
                                           "fork", "all"])
    ap.add_argument("--seeds", type=int, default=None)
    ap.add_argument("--trials", type=int, default=300)
    args = ap.parse_args()
    n = args.seeds
    studies = [
        ("sweep", lambda: sweep(n or 150)),
        ("grid", lambda: grid(n or 40)),
        ("policy", lambda: policy(n or 60)),
        ("trajectory", lambda: trajectory(n or 40)),
        ("raids", lambda: raid_roi(args.trials)),
        ("events", lambda: events(n or 150)),
        ("fork", lambda: fork(n or 150)),
    ]
    for name, study in studies:
        if args.experiment in (name, "all"):
            print(f"== {name} ==")
            study()


if __name__ == "__main__":
    main()
