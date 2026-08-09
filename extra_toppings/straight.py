"""The Straight Path (design §2.4.1, scope per §8 revision 9): wind the
trade down, counsel the file down, settle the witnesses, and be a real
restaurant by day 30.

The branch's verbs live here; phases.py calls in for its branch-gated
mornings and nights, sitdown.py for the commit scene. Randomness (rev. 9
item 1): temptation-offer arrival and terms are world dice on the
per-day "straight" channel; the meeting dice — fire-sale and temptation
observation — draw the reserved persistent `straight` stream, first
drawn only after the chair is taken. Disposal runs are routes and draw
the routes stream under full Act I rules.

The crime clock: a disposal run (when it actually rolls), a fire-sale
meeting, an accepted temptation offer and washing past the ceiling
reset `last_crime_day`. Tribute, truce money, settlements, burning and
under-ceiling washing never do — being extorted is victimhood, not
trade.
"""

import random

from . import data, escrow, evidence, models
from .models import BranchState, State
from .rng import Streams
from .ui import Console, money

# Goal terms (§2.4.1), checked at day 30.
GOAL_CASE = 45.0
GOAL_REP = 45.0
GOAL_DIRTY = 200            # unlaundered cash anywhere, at most
CLEAN_DAYS_REQUIRED = 5
LIQUIDATION_DEADLINE = 25   # the last day a crime still leaves 5 clean days
HOSTILE_MORALE = 5          # a departed aware witness below this is hostile
# §2.1's vendetta band: an open feud. Rebound to THE canonical home
# (rev. 13 item 5) — same value, one spelling.
FEUD_RELATION = models.VENDETTA_RELATION

# Disposal pricing (rev. 2 item 4, rev. 9 items 6 and 9).
FIRE_SALE_RATE = 0.40           # of base book value
FIRE_SALE_RELATION = 8.0        # Sal appreciates the business
FIRE_SALE_WITNESS_RISK = 0.20   # someone watches the truck load
FIRE_SALE_WITNESS_EVIDENCE = 3.0
DISPOSAL_HAIRCUT_LO = 0.60      # a seller without a network now
DISPOSAL_HAIRCUT_HI = 0.75

# Temptation offers (rev. 9 item 7): new trade, not disposal.
TEMPTATION_CHANCE = 0.30
TEMPTATION_MULT_LO = 1.4
TEMPTATION_MULT_HI = 1.7
TEMPTATION_WITNESS_RISK = 0.15
TEMPTATION_WITNESS_EVIDENCE = 3.0

# Advertising (rev. 9 item 8) — canon's clean-money list, finally.
AD_COST = 300
AD_DAYS = 4
AD_REP_PER_NIGHT = 2.0
AD_DEMAND_MULT = 1.15

# The siege (rev. 9 item 13).
RETREAT_AGGRESSION = 1.5
# Rebound to THE shared insolvency contract (rev. 15 item 3) — same
# value, one home, every active branch.
INSOLVENT_NIGHTS = models.INSOLVENT_NIGHTS


def live(state: State) -> BranchState:
    """The branch's live ledger; callers guarantee the branch is
    active. Public so phases.py narrows through one accessor."""
    if state.branch_state is None:
        raise ValueError("straight verbs called outside the branch")
    return state.branch_state


def sitdown_day(state: State) -> int:
    if state.sitdown_snapshot is None:
        raise ValueError("the Straight Path without a sit-down snapshot")
    return state.sitdown_snapshot.payoff_day + 1


def crime_committed(state: State) -> None:
    """Reset the clean-days clock. The caller narrates the crime; this
    just moves the hand."""
    live(state).last_crime_day = state.day


def clean_days(state: State, as_of: int | None = None) -> int:
    """Completed clean days as of `as_of` (default: today, evaluated at
    night while the day is still current). With no post-fork crime the
    count runs from the sit-down morning itself — clean day one."""
    day = state.day if as_of is None else as_of
    last = live(state).last_crime_day
    if last is None:
        return day - sitdown_day(state) + 1
    return day - last


def hostile_witnesses(state: State) -> list:
    """Departed aware employees below morale 5 with no settlement —
    the goal term's exact letter (§2.4.1), read through the one
    witness-relationship authority (rev. 11 item 2)."""
    from .models import witness_status
    return [e for e in state.employees
            if e.aware and not e.hired and e.morale < HOSTILE_MORALE
            and witness_status(state, e.key) != "settled"]


def open_feuds(state: State) -> list[str]:
    return [k for k, r in state.rivals.items()
            if r.alive and (r.raid_warning > 0 or r.relation <= FEUD_RELATION)]


def failed_terms(state: State, as_of: int | None = None) -> list[str]:
    """Every non-Case goal term that currently fails, named in player
    language — the epilogue prints these verbatim (invariant 8). The
    Case term is graded separately: it decides earned versus Almost
    Out, not Half Measures."""
    failed = []
    units = state.total_stock_units()
    if units > 0:
        failed.append(f"contraband still on hand ({units} units)")
    held = state.unlaundered_total()
    if held > GOAL_DIRTY:
        failed.append(f"unlaundered cash at {money(held)} against the "
                      f"{money(GOAL_DIRTY)} line")
    if state.shop.reputation < GOAL_REP:
        failed.append(f"reputation {state.shop.reputation:.0f} against "
                      f"the {GOAL_REP:.0f} a real restaurant needs")
    hostile = hostile_witnesses(state)
    if hostile:
        names = ", ".join(e.name for e in hostile)
        failed.append(f"a hostile unsettled witness ({names})")
    feuds = open_feuds(state)
    if feuds:
        names = ", ".join(data.RIVALS[k]["short"] for k in feuds)
        failed.append(f"an open feud ({names})")
    days = clean_days(state, as_of=as_of)
    if days < CLEAN_DAYS_REQUIRED:
        failed.append(f"a crime inside the final stretch (clean days "
                      f"{days} of {CLEAN_DAYS_REQUIRED})")
    return failed


def grade(state: State) -> str:
    """The §2.5 day-30 matrix: every term met → the earned Legitimate
    Exit; everything met except Case 46–99 → Almost Out; any other term
    failed → Half Measures. Called at the calendar boundary, so the
    clean-days clock reads day 30."""
    if failed_terms(state, as_of=data.DEBT_DUE_DAY):
        return "half_measures"
    return "straight_exit" if state.case <= GOAL_CASE else "almost_out"


# ── the commit scene's coda ───────────────────────────────────────

def entry_scene(state: State, con: Console) -> None:
    """The book burning (§3.1 D14): what just became impossible, and
    what little remains. Transcript only — the BranchState was already
    validated and assigned by the scene."""
    con.header("THE STRAIGHT PATH — the book burns")
    con.say("  The coded-customer list goes into the pizza oven a page at "
            "a time. Carmine watches it catch and says nothing at all.")
    con.say("  What just became impossible: the supplier's van, the coded "
            "order board, the night jobs. The wheel is over.")
    con.say(f"  What little remains: disposal runs left: "
            f"{live(state).disposal_runs_left} — counted, priced at a "
            f"haircut, and each one a crime on the clock.")
    con.say(f"  The exit is graded on day {data.DEBT_DUE_DAY}: stock zero "
            f"everywhere, dirty at most {money(GOAL_DIRTY)}, the file at "
            f"or under {GOAL_CASE:.0f}, reputation {GOAL_REP:.0f} or "
            f"better, no hostile unsettled witness, no open feud, and "
            f"{CLEAN_DAYS_REQUIRED} clean days at the end — all "
            f"liquidation by day {LIQUIDATION_DEADLINE}.")
    con.say("  Counsel and settlements are on the table now. Advertising "
            "too. The trade is not — except the three runs, the "
            "fire-sale channel, and whoever comes to the back door.")


# ── mornings ──────────────────────────────────────────────────────

def morning_lines(state: State, con: Console) -> None:
    bs = live(state)
    days = clean_days(state)
    con.say(f"  The exit: disposal runs left {bs.disposal_runs_left} · "
            f"clean days {days} of {CLEAN_DAYS_REQUIRED} · all "
            f"liquidation by day {LIQUIDATION_DEADLINE}.")
    if state.total_stock_units() > 0 and state.day > LIQUIDATION_DEADLINE:
        con.say("  The calendar has passed the liquidation line — product "
                "still on hand can only burn now, or fail the exit.")


def temptation_offer(state: State, rng: random.Random) -> dict | None:
    """The morning's temptation, drawn from the per-day world channel:
    someone still wants what you're leaving behind."""
    held = sorted(g for g, u in state.shop_stash.items() if u > 0)
    if not held or rng.random() >= TEMPTATION_CHANCE:
        return None
    good = rng.choice(held)
    price = max(5, int(data.GOODS[good]["base"]
                       * rng.uniform(TEMPTATION_MULT_LO, TEMPTATION_MULT_HI)))
    dk = rng.choice(sorted(data.DISTRICTS))
    return {"good": good, "price": price, "district": dk}


def temptation_card(state: State, offer: dict, con: Console) -> None:
    g = data.GOODS[offer["good"]]
    where = data.DISTRICTS[offer["district"]]["label"]
    con.bullet(f"TEMPTATION: a {where} contact wants your {g['label']} at "
               f"{money(offer['price'])}/unit — the card says what it is: "
               f"new trade at full margin, not disposal. Taking it resets "
               f"your clean days and spends no disposal run.")


def take_temptation(state: State, offer: dict, con: Console,
                    streams: Streams) -> bool:
    """Answer the back door. Returns True when the offer is consumed
    (sold or finally declined)."""
    good = offer["good"]
    have = state.shop_stash.get(good, 0)
    if have <= 0:
        con.say("  Nothing left to sell them. The contact shrugs and goes.")
        return True
    label = data.GOODS[good]["label"]
    n = con.ask_int(f"Sell how many {label} at {money(offer['price'])}? "
                    f"(new trade — the clean-days clock resets)",
                    0, have, 0)
    if n <= 0:
        con.say("  You send them away. The clock keeps its count.")
        return True
    state.shop_stash[good] = have - n
    take = offer["price"] * n
    state.dirty += take
    crime_committed(state)
    con.say(f"  The contact pays {money(take)} dirty at the back door. "
            f"Old life, full margin — and the clean days start over.")
    if streams.straight.random() < TEMPTATION_WITNESS_RISK:
        state.add_case(TEMPTATION_WITNESS_EVIDENCE,
                       "a regular watched the handoff at the back door",
                       kind="witness")
        con.bullet("A regular at the counter watches the whole handoff "
                   "and pays very close attention to their coffee.")
    return True


def fire_sale(state: State, con: Console, streams: Streams) -> bool:
    """One meeting a day with Sal's people: bulk, 40% of book, his
    truck at your door — shop and warehouse stock alike (§3.1 D14).
    Returns True when a meeting actually happened (units moved)."""
    sal = state.rivals.get("sal")
    if sal is None or not sal.alive:
        con.say("  Sal's people aren't answering anyone's calls anymore.")
        return False
    if state.total_stock_units() <= 0:
        con.say("  Nothing left to sell. The channel stays open; the "
                "shelves are bare.")
        return False
    sold_units = 0
    take = 0
    for stash_name, stash in (("shop", state.shop_stash),
                              ("warehouse", state.warehouse or {})):
        for good in sorted(stash):
            have = stash.get(good, 0)
            if have <= 0:
                continue
            unit_price = max(1, int(data.GOODS[good]["base"]
                                    * FIRE_SALE_RATE))
            # Default 0: an exhausted script must never liquidate
            # assets (the rev. 7 safe-fallback contract).
            n = con.ask_int(
                f"Hand over {data.GOODS[good]['label']} from the "
                f"{stash_name}? ({money(unit_price)}/unit, have {have})",
                0, have, 0)
            if n > 0:
                stash[good] = have - n
                sold_units += n
                take += unit_price * n
    if sold_units <= 0:
        con.say("  Sal's man waits by the empty truck, then leaves. No "
                "meeting, no crime, no money.")
        return False
    state.dirty += take
    models.set_relation(state, "sal",
                        min(100.0, sal.relation + FIRE_SALE_RELATION))
    crime_committed(state)
    con.say(f"  Sal's man pays {money(take)} dirty for {sold_units} units "
            f"at forty cents on the book. His truck does the driving; "
            f"your clean days start over.")
    if streams.straight.random() < FIRE_SALE_WITNESS_RISK:
        state.add_case(FIRE_SALE_WITNESS_EVIDENCE,
                       "someone watched Sal's truck load at your door",
                       kind="witness")
        con.bullet("Across the street, a curtain moves twice while the "
                   "crates go up the ramp.")
    return True


def burn_stock(state: State, con: Console) -> None:
    """The third disposal way: zero return, zero risk, no crime — and
    Tony watches you do it (§2.4.1)."""
    units, _ = escrow.burn_assets(state, stock=True)
    if units <= 0:
        con.say("  The walk-in holds flour and nothing else. Nothing to "
                "burn.")
    else:
        con.say(f"  {units} units go into the oven's back chamber in "
                f"paper-wrapped bricks. No return, no risk, no crime — "
                f"the clock doesn't move.")
        con.say("  Tony watches the door glow and wipes his hands on his "
                "apron for a long time.")
    if state.warehouse and any(u > 0 for u in state.warehouse.values()):
        con.say("  The warehouse still holds product — it has to come "
                "home (move stash, nights) before it can burn.")


# ── the case file & the paid verbs: shared homes ─────────────────
# The remediation UI moved to evidence.py (rev. 14 item 8): the
# machinery belongs to every branch the capability policy unlocks,
# and the war must not call Straight-specific wrappers. These names
# stay bound for this module's callers and tests.
show_case_file = evidence.show_case_file
counsel_label = evidence.counsel_label
toggle_counsel = evidence.toggle_counsel
settle_menu = evidence.settle_menu


def ad_label(state: State) -> str:
    left = live(state).ad_days_left
    running = f" (campaign running: {left} day(s) left)" if left else ""
    return (f"Advertising — {money(AD_COST)} clean. Four days of lift for "
            f"the order book and the name over the door.{running}")


def advertise(state: State, con: Console) -> None:
    from . import shop
    if state.clean < AD_COST:
        con.say("  Not with today's clean cash.")
        return
    state.clean -= AD_COST
    live(state).ad_days_left += AD_DAYS
    shop.recompute_demand(state)
    con.say(f"  {money(AD_COST)} buys four days of flyers, a radio spot "
            f"and the good half-page in the neighborhood weekly. Order "
            f"book now: ~{state.demand_today} customers.")


# ── nights ────────────────────────────────────────────────────────


def night_tick(state: State, con: Console, payroll_short: bool) -> None:
    """After the settle-accounts loop: counsel's nightly work, the
    advertising campaign, the dormancy reconciliation, and the
    clean-insolvency counter (rev. 9 item 11)."""
    if state.game_over:
        return
    bs = live(state)
    evidence.counsel_nightly(state, con)
    if bs.ad_days_left > 0:
        bs.ad_days_left -= 1
        state.shop.reputation = min(100.0,
                                    state.shop.reputation + AD_REP_PER_NIGHT)
        con.say(f"  The advertising works its shift: reputation "
                f"{state.shop.reputation:.0f}.")
    outcome = models.insolvency_tick(state, payroll_short)
    if outcome == "broke":
        con.say("  Two nights running: no payroll, no stock, no "
                "hidden dollar. The clean life has a rent too.")
    elif outcome == "warned":
        con.bullet("Payroll missed with nothing left to sell and "
                   "nothing left hidden. One more night like this "
                   "and the oven goes cold.")


def search_spook(state: State, con: Console) -> None:
    """A law-phase visit with nothing to find spooks a witness instead
    (§2.4.1): morale −1 for the first observant or aware employee on
    the roster. Deterministic — no dice, no stream."""
    watchers = [e for e in state.hired()
                if e.available and (e.aware or e.trait == "observant")]
    if not watchers:
        return
    e = watchers[0]
    e.morale -= 1
    con.bullet(f"{e.name} rechecks the till twice before locking it and "
               f"says nothing — searches attack people now, not stash.")


def exit_readout(state: State, con: Console) -> None:
    """§3.1 D18's night line: the whole exit, one row, every term."""
    if state.game_over:
        return
    hostile = hostile_witnesses(state)
    witnesses = ("witnesses content" if not hostile
                 else f"witnesses: {len(hostile)} hostile")
    feuds = open_feuds(state)
    feud = ("no feud" if not feuds
            else "feud: " + ", ".join(data.RIVALS[k]["short"]
                                      for k in feuds))
    con.say(f"  Exit readout: stock {state.total_stock_units()} · dirty "
            f"{money(state.unlaundered_total())} · Case {state.case:.0f} "
            f"· rep {state.shop.reputation:.0f} · {witnesses} · {feud} · "
            f"clean days {clean_days(state)} of {CLEAN_DAYS_REQUIRED}.")
