"""The Quiet Sale's escrow week (design §2.4.4): a hold-steady game.

The sit-down day is diligence day 1 — the buyer's man walks the shop
that same afternoon; days 2–4 follow; closing is the morning of fork+4,
and the run ends at closing. The mark is recomputed each diligence
morning from visible inputs and moves ONLY when they move: reputation,
Case, the war clause, incidents. Diligence never pays for waiting; it
only charges for slipping.

All escrow randomness (walk-through odds, incident repricing, the
off-site truck) draws from the reserved `brokers` stream, and only
after the player has actually taken the chair — a stand-pat run leaves
the stream provably fresh (§2.7).
"""

from dataclasses import dataclass

from . import data, models
from .models import (REPRICE_MAX_PCT, REPRICE_MIN_PCT, SEVERANCE_PER_HEAD,
                     BranchState, State, validate_branch_state)
from .rng import Streams
from .ui import Console, money

SCENE_NAMESPACE = "sitdown"      # closing decisions share the scene channel

BASE_PRICE = 3000
REP_PRICE = 140                  # $/reputation point
UPGRADE_RECOVERY = 0.5           # cents on the upgrade dollar
CASE_DISCOUNT = 45               # $/Case point — pure price, no lawyering
WAR_CLAUSE = 0.20                # any rival at relation <= -50 or a live raid
WAR_RELATION = -50.0
INCIDENT_LIMIT = 2               # the second incident collapses the deal
OFFSITE_RISK = 0.20              # the truck at the rolling door, per move
DIRTY_TOLERANCE = 200            # unlaundered cash a clean close may carry
DILIGENCE_DAYS = 4               # closing is the morning after day 4
TIER_WELL = 25_000
TIER_MODEST = 10_000


def _bs(state: State) -> BranchState:
    """The live escrow ledger; callers guarantee the branch is active."""
    if state.branch_state is None:
        raise ValueError("escrow called outside the quiet_sale branch")
    return state.branch_state


def sitdown_day(state: State) -> int:
    if state.sitdown_snapshot is None:
        raise ValueError("escrow without a sit-down snapshot")
    return state.sitdown_snapshot.payoff_day + 1


def diligence_day(state: State) -> int:
    """1 on the sit-down day itself; closing morning is day 5."""
    return state.day - sitdown_day(state) + 1


def war_clause_armed(state: State) -> bool:
    return any(r.alive and (r.relation <= WAR_RELATION or r.raid_warning > 0)
               for r in state.rivals.values())


def upgrade_spend(state: State) -> int:
    return sum(data.UPGRADES[k]["cost"] for k in state.shop.upgrades)


@dataclass(frozen=True)
class MarkBreakdown:
    """THE valuation card (rev. 7): one immutable view holding every
    priced term and the final mark. The renderer consumes this and
    nothing else, and the displayed dollar terms sum exactly to the
    displayed mark. Rounding policy, applied once per term: each term
    is the raw input times its rate, rounded to the nearest whole
    dollar (Python round); the raw subtotal clamps to zero BEFORE any
    percentage deduction (rev. 8 — a discount against a negative
    subtotal is a credit, and the card must never show one), with the
    floor carried explicitly; the war clause and incident repricing
    round against the clamped running subtotal and are never negative.
    No int() truncation anywhere — the card's arithmetic IS the mark's
    arithmetic."""
    reputation: float
    case: float
    upgrade_spend: int
    rep_term: int
    upgrade_term: int
    case_term: int
    war_armed: bool
    war_term: int
    incident_discount_pct: int    # whole points — the canonical unit
    incident_term: int
    floored: bool
    final: int


def build_mark(state: State) -> MarkBreakdown:
    rep = state.shop.reputation
    case = state.case
    spend = upgrade_spend(state)
    rep_term = round(rep * REP_PRICE)
    upgrade_term = round(spend * UPGRADE_RECOVERY)
    case_term = round(case * CASE_DISCOUNT)
    raw_subtotal = BASE_PRICE + rep_term + upgrade_term - case_term
    floored = raw_subtotal < 0
    subtotal = max(0, raw_subtotal)
    war_armed = war_clause_armed(state)
    war_term = round(subtotal * WAR_CLAUSE) if war_armed else 0
    after_war = subtotal - war_term
    pct = _bs(state).escrow_discount_pct
    # The division by 100 happens HERE, once, inside a term that rounds
    # to whole dollars — never at storage time (rev. 8 completion).
    incident_term = round(after_war * pct / 100) if pct else 0
    final = max(0, after_war - incident_term)
    return MarkBreakdown(
        reputation=rep, case=case, upgrade_spend=spend,
        rep_term=rep_term, upgrade_term=upgrade_term, case_term=case_term,
        war_armed=war_armed, war_term=war_term,
        incident_discount_pct=pct, incident_term=incident_term,
        floored=floored, final=final)


def compute_mark(state: State) -> int:
    return build_mark(state).final


def _show_card(state: State, con: Console) -> None:
    """Renders the MarkBreakdown and nothing else — every displayed
    dollar figure comes from the view, and they sum to the mark."""
    card = build_mark(state)
    con.say(f"  The broker's card, itemized: base {money(BASE_PRICE)} + "
            f"rep {card.reputation:.1f} x {money(REP_PRICE)} = "
            f"{money(card.rep_term)} + upgrades "
            f"{money(card.upgrade_spend)} x 50% = "
            f"{money(card.upgrade_term)}; less Case {card.case:.1f} x "
            f"{money(CASE_DISCOUNT)} = {money(card.case_term)}.")
    if card.war_armed:
        con.say(f"  The war clause is ARMED: -20% = -{money(card.war_term)} "
                f"while a rival sits at vendetta or circles the block.")
    else:
        con.say("  One clause sits dormant and visible: -20% if any rival "
                "reaches vendetta or a raid telegraph goes live.")
    if card.floored:
        con.say("  The additions never reach the deductions: subtotal "
                "below zero; the mark floors at $0.")
    if card.incident_discount_pct:
        con.say(f"  Incident repricing to date: "
                f"-{card.incident_discount_pct}% = "
                f"-{money(card.incident_term)}.")
    con.say(f"  MARK: {money(card.final)}. Terms: re-marked each "
            f"morning; incidents reprice -{REPRICE_MIN_PCT} to "
            f"-{REPRICE_MAX_PCT}%; a second incident "
            f"ends it; closing on the morning of day "
            f"{sitdown_day(state) + DILIGENCE_DAYS}.")
    # The classification, projected before anyone signs anything: the
    # exact tolerance and where the close lands as things stand.
    held = state.dirty + state.warehouse_cash
    stock = state.stash_bulk(state.shop_stash) + (
        state.stash_bulk(state.warehouse) if state.warehouse else 0)
    verdict = ("Sold the shop, kept the trade — capped at the modest tier"
               if stock > 0 or held > DIRTY_TOLERANCE
               else "a clean close")
    con.say(f"  The buyer's ledger test: unlaundered cash anywhere "
            f"{money(held)} against a {money(DIRTY_TOLERANCE)} tolerance; "
            f"product anywhere {stock} bulk. As it stands this closes as: "
            f"{verdict}.")


def diligence_morning(state: State, con: Console, streams: Streams) -> None:
    """Runs before the regular morning while the sale is in escrow.
    Marks the price, narrates the week, and on day 5 holds the closing."""
    bs = _bs(state)
    dd = diligence_day(state)
    if dd > DILIGENCE_DAYS:
        _closing(state, con)
        return
    bs.diligence_day = dd
    old_mark = bs.escrow_mark
    bs.escrow_mark = compute_mark(state)
    con.header(f"ESCROW — diligence day {dd} of {DILIGENCE_DAYS}")
    _show_card(state, con)
    if old_mark and bs.escrow_mark != old_mark:
        con.say(f"  (Moved {money(bs.escrow_mark - old_mark)} since "
                f"yesterday — the card only moves when its inputs do.)")
    if dd == 2:
        # Staff learn what the man in the good suit was measuring.
        for e in state.hired():
            e.morale -= 1
        con.bullet("The crew figured out what the man in the good suit was "
                   "measuring. Nobody says anything. Morale dips; they're "
                   "waiting to hear what happens to THEM.")
    if state.stash_bulk(state.shop_stash) > 0:
        # §3.4's oregano question, every morning it still needs asking:
        # the wagon can only sell so much before the afternoon walk, the
        # warehouse is a 20% truck and a kept-the-trade close — or the
        # incinerator, which explains nothing to anybody.
        pick = con.menu(
            "The walk-in holds product, and his man walks every afternoon:",
            ["Burn it — ashes explain nothing",
             "Keep it — sell what the wagon carries, chance the rest"])
        if pick == 0:
            incinerate(state, con, stock=True)
        else:
            con.bullet("The walk-in still holds product. Anything his man "
                       "finds this afternoon is an incident.")


def walkthrough(state: State, con: Console, streams: Streams) -> None:
    """The buyer's man, every diligence afternoon. Day 1 he walks for
    certain; later days scale with the neighborhood's heat. Contraband
    on premises when he walks is an incident."""
    if state.game_over or state.branch != "quiet_sale":
        return
    dd = diligence_day(state)
    if not 1 <= dd <= DILIGENCE_DAYS:
        return
    rng = streams.brokers
    odds = 1.0 if dd == 1 else min(1.0, 0.5 + state.heat(
        data.HOME_DISTRICT) / 200)
    if rng.random() >= odds:
        con.bullet("No sign of the buyer's man today. The neighborhood "
                   "waits with you.")
        return
    if state.stash_bulk(state.shop_stash) > 0:
        con.bullet("The buyer's man lifts the walk-in latch and goes very "
                   "quiet. He photographs nothing. He doesn't have to.")
        record_incident(state, con, streams,
                        "contraband on premises at a walk-through")
    else:
        con.bullet("The buyer's man walks the shop, taps a deck stone, "
                   "nods once. Flour and receipts, exactly as promised.")


def record_incident(state: State, con: Console, streams: Streams,
                    why: str) -> None:
    """Reprice (−20..−35%, whole points — rev. 8) or, on the second
    incident, collapse."""
    if state.branch != "quiet_sale" or state.branch_state is None:
        return
    bs = _bs(state)
    bs.escrow_incidents += 1
    if bs.escrow_incidents >= INCIDENT_LIMIT:
        con.bullet(f"INCIDENT: {why} — the second. The buyer's counsel "
                   f"calls before dinner: the offer is withdrawn.")
        revert_to_standpat(state, con, collapsed=True)
        return
    cut_points = streams.brokers.randint(REPRICE_MIN_PCT, REPRICE_MAX_PCT)
    # Assignment, not accumulation: only the first incident ever
    # reprices — the second collapsed above, before any draw.
    bs.escrow_discount_pct = cut_points
    bs.escrow_mark = compute_mark(state)
    con.bullet(f"INCIDENT: {why}. The mark reprices -{cut_points}% to "
               f"{money(bs.escrow_mark)}. One more and the deal dies.")


def burn_assets(state: State, stock: bool = False,
                cash: int = 0) -> tuple[int, int]:
    """THE disposal effect (rev. 7, shared per rev. 9 item 9):
    destruction, never conversion. Nothing comes back — no clean cash,
    no Case relief, no value. Cash burns only from the till in hand:
    warehouse cash is physical and must be trucked back before it can
    meet the incinerator; warehouse stock likewise burns only after it
    comes home. Returns (units burned, dollars burned); narration
    belongs to the caller's branch."""
    units = 0
    if stock and state.stash_bulk(state.shop_stash) > 0:
        units = sum(u for u in state.shop_stash.values() if u > 0)
        state.shop_stash = {}
    burned = 0
    if cash > 0:
        burned = min(cash, state.dirty)
        state.dirty -= burned
    return units, burned


def incinerate(state: State, con: Console, stock: bool = False,
               cash: int = 0) -> None:
    """The escrow surface over the shared burn effect: the week's one
    rule is that the two ledgers cannot touch, so what cannot be shown
    gets burned."""
    units, burned = burn_assets(state, stock=stock, cash=cash)
    if units:
        con.say(f"  {units} units go into the incinerator behind the "
                f"bakery before ten. It smells like money for an hour, "
                f"and then it smells like a clean close.")
    if cash > 0:
        con.say(f"  {money(burned)} in unwashable bills goes into the same "
                f"fire, a brick at a time. It buys nothing, launders "
                f"nothing, and answers no subpoena — which is the point.")


def burn_cash_action(state: State, con: Console) -> None:
    """The settle-menu surface during escrow: laundering is replaced by
    disposal — the menu never advertises an allowance it will refuse."""
    if state.dirty <= 0:
        con.say("  No dirty cash on hand. (Warehouse cash must be trucked "
                "back before it can burn.)")
        return
    amt = con.ask_int(
        f"Burn how much? (dirty {money(state.dirty)}; the buyer's ledger "
        f"test tolerates {money(DIRTY_TOLERANCE)})",
        0, state.dirty, 0)
    if amt <= 0:
        con.say("  The bills go back in the bag. The tolerance is "
                f"{money(DIRTY_TOLERANCE)}, and the card remembers.")
        return
    incinerate(state, con, cash=amt)


def offsite_move_risk(state: State, con: Console, streams: Streams) -> None:
    """Moving stock to the warehouse mid-diligence: a truck at a rolling
    door while the buyer's man watches the neighborhood — 20% per move."""
    if state.branch != "quiet_sale" or state.game_over:
        return
    if streams.brokers.random() < OFFSITE_RISK:
        record_incident(state, con, streams,
                        "a loaded truck at the rolling door after dark")
    else:
        con.say("  The truck rolls at dusk and nobody writes anything down.")


def revert_to_standpat(state: State, con: Console, collapsed: bool) -> None:
    """Collapse and walk-away are NOT endings (§2.5): both revert to
    stand-pat with the buyer gone forever."""
    state.branch = "stand_pat"
    state.branch_state = None
    validate_branch_state(state.branch, state.branch_state)
    if collapsed:
        state.shop.reputation = max(0.0, state.shop.reputation - 8)
        con.say("  Word gets around: the sale fell through and nobody says "
                "why. The crew is bruised; the shop is yours; the buyer "
                "buys elsewhere. (Reputation -8.)")
    else:
        con.say("  You keep the shop and the life. The buyer's car doesn't "
                "slow down on this block again.")


def _closing(state: State, con: Console) -> None:
    """The closing morning — sign or walk. Transactional (rev. 7): the
    whole transaction is computed and validated BEFORE anything
    mutates; humane severance is selectable only when settlement plus
    clean cash can fund it; cash and settlement never go negative;
    escrow_mark stays the buyer's price, never overwritten. Signing is
    the only success that ends a run before day 30 (§2.5 precedence 3)."""
    bs = _bs(state)
    bs.escrow_mark = compute_mark(state)
    con.header("CLOSING MORNING — the buyer's counsel spreads the papers")
    _show_card(state, con)
    crew = state.hired()
    severance_total = SEVERANCE_PER_HEAD * len(crew)
    affordable = state.clean + bs.escrow_mark >= severance_total
    if crew:
        con.say(f"  Severance line-items on the closing sheet: "
                f"{money(SEVERANCE_PER_HEAD)} a name, {len(crew)} names "
                f"({money(severance_total)}) — or nothing, and they hear "
                f"it from the buyer.")
        if not affordable:
            con.say(f"  The envelopes would take {money(severance_total)}; "
                    f"settlement plus the till holds "
                    f"{money(state.clean + bs.escrow_mark)}. There is no "
                    f"humane option on this sheet — only the honest "
                    f"admission that you can't afford one.")
    pick = con.scene_menu(
        SCENE_NAMESPACE,
        "Closing morning. The pen is on the table.",
        ["Tear it up — keep the shop, lose the buyer forever",
         "Sign — the week is over, and so is the run"])
    if pick == 0:
        revert_to_standpat(state, con, collapsed=False)
        return
    # Decide the full transaction before mutating anything — outcome
    # taxonomy per rev. 8: an amount alone collapses refusal,
    # unaffordability and an empty roster into one $0.
    severance = 0
    if not crew:
        outcome = "not_applicable"
    elif not affordable:
        outcome = "unaffordable"
    else:
        sev = con.scene_menu(
            SCENE_NAMESPACE,
            "The crew's severance:",
            ["Nothing — they'll land somewhere",
             f"{money(SEVERANCE_PER_HEAD)} a name — they hear it from you"])
        if sev == 1:
            outcome = "paid"
            severance = severance_total
        else:
            outcome = "declined"
    # Commit: one atomic application, invariants checked first.
    if severance > state.clean + bs.escrow_mark:
        raise ValueError("closing transaction would overdraw")   # unreachable
    state.clean = state.clean + bs.escrow_mark - severance
    # One validated transition (rev. 8 completion): the outcome triple
    # is applied together and checked against the full state machine —
    # with the terminal invariant — before the run is allowed to end.
    bs.severance_outcome = outcome
    bs.severance_paid = severance
    bs.closing_headcount = len(crew)
    validate_branch_state("quiet_sale", bs, game_over="sold")
    if outcome == "paid":
        con.say(f"  {money(severance)} in envelopes, handed over by you, "
                f"before the ink. They hear it from you. It matters.")
    elif outcome == "declined":
        con.say("  The crew reads about the sale on the buyer's schedule. "
                "The city is small; they'll remember whose name was on "
                "the envelope that never came.")
    elif outcome == "unaffordable":
        con.say("  There is nothing to put in envelopes. The crew can see "
                "the number on the sheet as well as you can.")
    state.game_over = "sold"
    con.say("  You sign every page. The keys feel lighter the moment they "
            "leave your hand.")


def _kept_the_trade(state: State) -> bool:
    """Closing while contraband or > $200 unlaundered cash sits anywhere —
    shop, wagon, or warehouse — reclassifies the ending (§2.4.4)."""
    stock = state.stash_bulk(state.shop_stash)
    if state.warehouse:
        stock += state.stash_bulk(state.warehouse)
    return stock > 0 or (state.dirty + state.warehouse_cash) > DIRTY_TOLERANCE


def walkaway_total(state: State) -> int:
    """Settlement + clean + whatever leaves with you, retained stock at
    base book value — exactly as net_worth() prices stock. The
    settlement is already in clean by signing time."""
    stock = sum(u * data.GOODS[g]["base"]
                for g, u in state.shop_stash.items())
    if state.warehouse:
        stock += sum(u * data.GOODS[g]["base"]
                     for g, u in state.warehouse.items())
    return state.clean + state.dirty + state.warehouse_cash + stock


def sale_tier(state: State) -> str:
    """'well' / 'modest' / 'fire' / 'kept_trade' — kept-the-trade caps
    at modest regardless of the number."""
    if _kept_the_trade(state):
        return "kept_trade"
    total = walkaway_total(state)
    if total >= TIER_WELL:
        return "well"
    if total >= TIER_MODEST:
        return "modest"
    return "fire"
def night_insolvency(state: State, con: Console,
                     payroll_short: bool) -> None:
    """The shared clean-insolvency transition in the escrow week's
    voice (rev. 16 item 3: "every active branch" includes the sale —
    a diligence week run on a till this empty ends before the buyer
    signs anything)."""
    outcome = models.insolvency_tick(state, payroll_short)
    if outcome == "broke":
        con.say("  Two nights running: no payroll, no stock, no hidden "
                "dollar — mid-diligence. The buyer's man finds the "
                "lights off and the crew gone; there is nothing left "
                "to sell him.")
    elif outcome == "warned":
        con.bullet("Payroll missed with nothing left to sell and "
                   "nothing hidden. A shop this empty won't survive to "
                   "its own closing.")

