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
from collections import Counter, defaultdict
from typing import ClassVar

from extra_toppings import data, market, phases, raids
from extra_toppings.bot import BOTS, CrimeHeavyBot, GreedyBot
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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("experiment", choices=["sweep", "grid", "policy",
                                           "trajectory", "raids", "events", "all"])
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
    ]
    for name, study in studies:
        if args.experiment in (name, "all"):
            print(f"== {name} ==")
            study()


if __name__ == "__main__":
    main()
