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
from extra_toppings.bot import (BOTS, CrimeHeavyBot, EscrowBot, GreedyBot,
                                KeepsStashBot, MarketBot, NoRemediationBot,
                                SloppyEscrowBot, StraightBot)
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


def _display_case(state) -> float:
    """The ledger-transparency oracle (§2.7 criterion 4, context-aware
    per rev. 10): an INDEPENDENT recomputation of what the visible
    records display — the raw left-to-right sum, less the derived
    retention relief (protected sources from the live roster, halvings
    allocated in ledger order within raw-total-minus-floor, subtracted
    in that same order), clamped. Deliberately reimplemented here
    rather than imported, the way the golden harness reimplements the
    legacy projection."""
    settled = set(state.branch_state.settled_witnesses) \
        if state.branch_state is not None else set()
    protected = {e.key for e in state.employees
                 if e.hired and e.aware and e.morale >= 5
                 and e.key not in settled}
    total = 0.0
    for r in state.evidence:
        total += r.magnitude
    display = total
    if protected and total > 10.0:
        allowance = total - 10.0
        acc = 0.0
        for r in state.evidence:
            if r.kind == "witness" and r.source in protected:
                cut = r.magnitude * 0.5
                if acc + cut <= allowance:
                    acc += cut
                    display -= cut
                else:
                    break
    return max(0.0, min(100.0, display))


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
    def straight_run(bot_cls, seed):
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

        s = run(seed, bot, config=straight_on, on_night=on_night)
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

    def straight_rows(pairs, label_suffix=""):
        rates = {}
        per_seed = {}
        for name, cls in pairs:
            entered = 0
            endings: Counter = Counter()
            deltas, lockups, used, accrued = [], [], [], []
            settled = 0
            covert = legit = 0
            ledger_bad = floor_bad = 0
            per_seed[name] = {}
            for seed in range(seeds):
                r = straight_run(cls, seed)
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
            print(f"{name}{label_suffix}: entered {entered}/{seeds}, "
                  f"endings {dict(endings)}")
            print(f"  earned exits {endings['straight_exit']}/{entered} "
                  f"({rates[name]:.0%}; band 25–70%)")
            if deltas:
                print(f"  ΔCase fork→end: median "
                      f"{statistics.median(deltas):+.1f} (bar ≤ −5); "
                      f"strictly below fork-day in {below}/{len(deltas)} "
                      f"({below / len(deltas):.0%}; bar ≥ 60%)")
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
                  f"${covert + legit:,} ({share:.1%}; bar < 5%)")
            print(f"  ledger transparency: {ledger_bad} bad nights "
                  f"(bar 0); floor: {floor_bad} sub-floor remediated "
                  f"nights (bar 0)")
        return rates, per_seed

    rates, per_seed = straight_rows((("straight", StraightBot),
                                     ("no-remediation", NoRemediationBot)))
    print(f"ablation drop: straight {rates['straight']:.0%} → "
          f"no-remediation {rates['no-remediation']:.0%} "
          f"({(rates['straight'] - rates['no-remediation']) * 100:.0f} "
          f"points; bar ≥ 20)")
    # The falling-Case claim as a matched-seed difference: the same
    # month, remediated vs not — reported alongside the absolute bar.
    matched = [s for s in range(seeds)
               if per_seed["straight"][s]["entered"]
               and per_seed["no-remediation"][s]["entered"]]
    if matched:
        diffs = [per_seed["straight"][s]["delta_case"]
                 - per_seed["no-remediation"][s]["delta_case"]
                 for s in matched]
        helped = sum(1 for d in diffs if d < 0)
        print(f"matched counterfactual: {len(matched)} paired entries; "
              f"remediated-minus-unremediated ΔCase median "
              f"{statistics.median(diffs):+.1f}; remediation left the "
              f"file lower in {helped}/{len(matched)} "
              f"({helped / len(matched):.0%}) — diagnostic, not a bar")

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
        remediates = False

    print("— dirty-month diagnostic (crime-heavy Act I, same branch "
          "policy; §3.1's entry profile) —")
    dirty_rates, _ = straight_rows(
        (("dirty-month", DirtyMonthStraightBot),
         ("dirty-no-remediation", DirtyMonthNoRemediation)))
    print(f"dirty-month ablation drop: {dirty_rates['dirty-month']:.0%} → "
          f"{dirty_rates['dirty-no-remediation']:.0%} "
          f"({(dirty_rates['dirty-month'] - dirty_rates['dirty-no-remediation']) * 100:.0f} points)")


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
