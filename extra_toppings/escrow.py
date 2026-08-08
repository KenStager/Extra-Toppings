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

from . import data
from .models import BranchState, State, validate_branch_state
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
SEVERANCE_PER_HEAD = 300
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


def compute_mark(state: State) -> int:
    """The buyer's marked price, every term visible (invariant 8)."""
    gross = (BASE_PRICE + int(state.shop.reputation) * REP_PRICE
             + int(upgrade_spend(state) * UPGRADE_RECOVERY))
    marked = gross - int(state.case) * CASE_DISCOUNT
    if war_clause_armed(state):
        marked = int(marked * (1 - WAR_CLAUSE))
    marked = int(marked * (1 - _bs(state).escrow_discount))
    return max(0, marked)


def _show_card(state: State, con: Console) -> None:
    bs = _bs(state)
    gross = (BASE_PRICE + int(state.shop.reputation) * REP_PRICE
             + int(upgrade_spend(state) * UPGRADE_RECOVERY))
    con.say(f"  The broker's card, itemized: base {money(BASE_PRICE)} + "
            f"rep {state.shop.reputation:.0f} x {money(REP_PRICE)} + "
            f"upgrades {money(upgrade_spend(state))} x 50% = "
            f"{money(gross)} gross; less Case {state.case:.0f} x "
            f"{money(CASE_DISCOUNT)}.")
    if war_clause_armed(state):
        con.say("  The war clause is ARMED: -20% while a rival sits at "
                "vendetta or circles the block.")
    else:
        con.say("  One clause sits dormant and visible: -20% if any rival "
                "reaches vendetta or a raid telegraph goes live.")
    if bs.escrow_discount:
        con.say(f"  Incident repricing to date: "
                f"-{bs.escrow_discount * 100:.0f}%.")
    con.say(f"  MARK: {money(bs.escrow_mark)}. Terms: re-marked each "
            f"morning; incidents reprice -10 to -25%; a second incident "
            f"ends it; closing on the morning of day "
            f"{sitdown_day(state) + DILIGENCE_DAYS}.")


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
            ["Keep it — sell what the wagon carries, chance the rest",
             "Burn it — ashes explain nothing"])
        if pick == 1:
            units = sum(u for u in state.shop_stash.values() if u > 0)
            state.shop_stash = {}
            con.say(f"  {units} units go into the incinerator behind the "
                    f"bakery before ten. It smells like money for an hour, "
                    f"and then it smells like a clean close.")
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
    """Reprice (−10 to −25%) or, on the second incident, collapse."""
    if state.branch != "quiet_sale" or state.branch_state is None:
        return
    bs = _bs(state)
    bs.escrow_incidents += 1
    if bs.escrow_incidents >= INCIDENT_LIMIT:
        con.bullet(f"INCIDENT: {why} — the second. The buyer's counsel "
                   f"calls before dinner: the offer is withdrawn.")
        revert_to_standpat(state, con, collapsed=True)
        return
    cut = streams.brokers.uniform(0.10, 0.25)
    bs.escrow_discount += cut
    bs.escrow_mark = compute_mark(state)
    con.bullet(f"INCIDENT: {why}. The mark reprices -{cut * 100:.0f}% to "
               f"{money(bs.escrow_mark)}. One more and the deal dies.")


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
    """The closing morning — sign or walk. Signing is the only success
    that ends a run before day 30 (§2.5 precedence 3)."""
    bs = _bs(state)
    bs.escrow_mark = compute_mark(state)
    con.header("CLOSING MORNING — the buyer's counsel spreads the papers")
    _show_card(state, con)
    crew = state.hired()
    if crew:
        con.say(f"  Severance line-items on the closing sheet: "
                f"{money(SEVERANCE_PER_HEAD)} a name, {len(crew)} names — "
                f"or nothing, and they hear it from the buyer.")
    kept = _kept_the_trade(state)
    if kept:
        con.say("  What you keep decides what you sold: product or serious "
                "unlaundered cash still sits somewhere with your name on "
                "it. Close like this and the file stays open on YOU.")
    pick = con.scene_menu(
        SCENE_NAMESPACE,
        "Closing morning. The pen is on the table.",
        ["Tear it up — keep the shop, lose the buyer forever",
         "Sign — the week is over, and so is the run"])
    if pick == 0:
        revert_to_standpat(state, con, collapsed=False)
        return
    severance = 0
    if crew:
        sev = con.scene_menu(
            SCENE_NAMESPACE,
            "The crew's severance:",
            ["Nothing — they'll land somewhere",
         f"{money(SEVERANCE_PER_HEAD)} a name — they hear it from you"])
        if sev == 1:
            severance = SEVERANCE_PER_HEAD * len(crew)
        else:
            for e in crew:
                e.morale -= 2       # they hear it from the buyer
    state.clean += bs.escrow_mark - severance
    bs.escrow_mark = bs.escrow_mark - severance
    if severance:
        con.say(f"  {money(severance)} in envelopes, handed over by you, "
                f"before the ink. They hear it from you. It matters.")
    elif crew:
        con.say("  The crew reads about the sale on the buyer's schedule. "
                "The city is small; they'll remember whose name was on "
                "the envelope that never came.")
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
