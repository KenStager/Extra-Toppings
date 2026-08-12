"""Carmine's Partner: the site, the deal, and the address it builds.

§2.4.2's branch. Carmine fronts $20,000, of which $13,000 is committed
the moment the deal is struck — to his own contractor, in the same
transaction that creates the second address and its wagon — and only
the float and the reserve ever reach the player's clean cash. The
capital is never a spendable deposit, and nothing about the build is
left to hope that later spending consumes the right money.

This module owns P4b.1b: the site cards, the atomic transaction, and
the points schedule it starts. The lifecycle it hands the world to
(construction, opening, capabilities) is `models`'; the branch's
pressure, grade and endings are later PRs'.
"""

from . import data, evidence, models
from .models import BranchState, Shop, State, Wagon
from .ui import Console, money

# ── the deal, itemized (§2.4.2) ──────────────────────────────────
# The parts are canonical and the sums are DERIVED, so the two can
# never drift: an itemization that does not add up to what Carmine
# said he was fronting is a defect, and it fails at import rather
# than in a scene.
FRONTED = 20_000
BUILD_OUT = 9_000       # committed — his contractor, his schedule
PERMITS = 1_500         # committed — paperwork, and paperwork is clean
SECOND_WAGON = 2_500    # committed — the used second wagon
OPENING_FLOAT = 3_000   # reaches clean cash
RESERVE = 4_000         # reaches clean cash

COMMITTED = BUILD_OUT + PERMITS + SECOND_WAGON      # $13,000
TO_CLEAN = OPENING_FLOAT + RESERVE                  # $7,000
if COMMITTED + TO_CLEAN != FRONTED:                 # import-time check
    raise RuntimeError("the Partner itemization does not add up to "
                       "what Carmine fronts")

# ── the site cards (§2.4.2; rev. 31 item 2) ──────────────────────
# THE order, written out: safe to dangerous — University Hill (no
# owner), Little Sicily (Sal's), The Meadows (Vinnie's). It is
# EXPLICIT rather than derived from `data.DISTRICTS` because
# deriving it would make an unrelated dictionary's insertion order
# the story's authority: someone adding a district, or tidying that
# table, would silently reshuffle the cards a player reads.
#
# What derivation was protecting — "any district but Old Harbor",
# spelled once — is kept as an import-time SET check instead. The
# set is the rule and the sequence is the telling, and the two
# cannot drift apart without the module refusing to load.
#
# The order decides what a player READS and nothing a study
# measures: the Partner bot and every ablation name their district
# by identity, never by index (rev. 31 item 2).
SITE_DISTRICTS = ("university", "little_sicily", "meadows")
# COVERAGE **and** UNIQUENESS, because set equality alone accepts a
# repeated card: `(…, "meadows", "meadows")` covers exactly the same
# districts and would offer the player Vinnie's floor twice, with the
# second copy answering to a different menu index. Equal lengths is
# the other half of the check.
if set(SITE_DISTRICTS) != set(data.DISTRICTS) - {data.HOME_DISTRICT} \
        or len(SITE_DISTRICTS) != len(set(SITE_DISTRICTS)):
    raise RuntimeError(
        "the Partner site cards must be each eligible district exactly "
        "once — §2.4.2 offers any district but the founding one")

# Opening on an owned district is a commercial declaration: the
# existing relation authority takes the hit, at one recorded number.
TURF_RELATION_DELTA = -25.0

# THE points cadence and prices live in `models` — validation prices
# bills from them too, and two homes for a number both a scene and a
# validator read is exactly the drift this project refuses. Named
# here only so this module reads in its own language.
POINTS_CYCLE_DAYS = models.POINTS_CYCLE_DAYS
POINTS_PER_CYCLE = models.POINTS_PER_CYCLE
POINTS_VIG = models.POINTS_VIG
# The early-payoff compliment defers the FIRST cycle by one whole
# cycle, not by one day (rev. 31 item 3). Bound to the model's
# constant, not re-typed as another 10 — a second literal here is
# how the deal and the validator come to disagree about the same
# compliment.
EARLY_PAYOFF_DAY = models.EARLY_PAYOFF_DAY


def first_points_due(shop: Shop, payoff_day: int) -> int:
    """THE first due day, read from the address's PERSISTED
    acceptance day (rev. 31 item 3).

    Never from a separately reconstructed date: a second spelling of
    when the deal was struck is the two-homes-for-one-date defect
    §2.4.2 forbids, and it would drift the moment either spelling
    moved. Paying the debt early buys one whole cycle of grace —
    Carmine's compliment, made arithmetic."""
    if shop.acceptance_day is None:
        raise ValueError("the founding address strikes no deal — the "
                         "points schedule starts from a recorded "
                         "acceptance day")
    # DELEGATED, not re-derived (P4b.2 review). This wrapper exists
    # only to speak in `Shop`; the arithmetic is the model's, which
    # is the same one `validate_points_schedule` prices the anchor
    # from. A local copy of the formula was exactly the drift the
    # hoist was supposed to end, sitting one function below the
    # comment that claimed it had.
    return models.first_points_due(shop.acceptance_day, payoff_day)


def site_label(district: str) -> str:
    """A site card as the player reads it: the district by its label,
    what it is good for, and who answers for it."""
    spec = data.DISTRICTS[district]
    owner = spec["rival"]
    who = (f"{data.RIVALS[owner]['short']}'s turf — opening here is a "
           f"declaration" if owner else "no owner — the safe pick")
    return f"{spec['label']} — {spec['flavor']} ({who})"


def _preflight(state: State, district: str) -> int:
    """Everything that can refuse the deal, asked BEFORE a single
    field moves, returning the payoff day the schedule reads.

    It binds the SCENE, not merely a plausible state: the deal is
    struck at the table on the morning after the debt died, and the
    room it builds is the SECOND one. A caller handing in a district
    and a day is not evidence that either happened."""
    if district not in data.DISTRICTS:
        raise ValueError(f"unknown district {district!r}")
    if district == data.HOME_DISTRICT:
        raise ValueError(
            f"the second shop does not open in {district!r} — the "
            f"founding district is not a site (§2.4.2)")
    if district not in SITE_DISTRICTS:            # belt: the card set
        raise ValueError(f"{district!r} is not a site card")
    if state.branch is not None:
        raise ValueError(
            f"a chair is already taken ({state.branch!r}) — the deal "
            f"is struck once, at the table")
    # THE payoff day comes from the PERSISTED snapshot, never from a
    # caller (review): a loose argument is a second spelling of when
    # the debt died, and the points schedule would then rest on
    # whatever a call site believed rather than on what the run
    # recorded.
    snap = state.sitdown_snapshot
    if snap is None:
        raise ValueError(
            "no sit-down snapshot — the deal is struck at the table, "
            "and the table is what records the payoff day")
    if state.day != snap.payoff_day + 1:
        raise ValueError(
            f"the deal is struck on the sit-down morning, day "
            f"{snap.payoff_day + 1}; this state stands on day "
            f"{state.day}")
    # THE CHAIR MUST ACTUALLY BE OPEN (P4b.1b review). Standing in
    # the right room on the right morning is not the same as being
    # offered the deal: a payoff at R below Partner's calendar gate,
    # or a file over its Case gate, leaves this chair EMPTY — and a
    # direct call could otherwise build a valid, loadable Partner
    # branch that the scene would never have seated.
    #
    # The verdict is CONSUMED from the canonical evaluator, never
    # respelled here: MIN_R and CASE_GATE live in `sitdown`, and a
    # second copy of either would be free to disagree with the chair
    # the player was shown. Imported inside the function because
    # `sitdown` imports this module to reach the deal — the same
    # deferred-import shape the war chair already uses.
    from . import sitdown
    verdict = next(v for v in sitdown.evaluate_chairs(snap, state.evidence)
                   if v.chair == "partner")
    if not verdict.available:
        raise ValueError(
            f"Carmine's chair is empty — {verdict.reason} (the "
            f"{verdict.blocker} gate: required "
            f"{verdict.requirement:g}, had {verdict.actual:g})")
    # The pre-deal world has exactly one address. Building the
    # "second" room onto a world that already has two would mint a
    # third and call it the branch's shop.
    if len(state.shops) != 1:
        raise ValueError(
            f"the deal builds the SECOND room; this world already "
            f"keeps {len(state.shops)} addresses")
    return snap.payoff_day


class _Undo:
    """Everything the commit below touches, remembered — so a
    postcondition failure is not a half-built branch.

    Preflight alone does not make a transaction atomic (review): the
    world-level validators run AFTER the records exist, and an
    exception there would otherwise leave an address standing on a
    state that has already spent Carmine's money and started his
    clock. Either the deal commits AND validates, or nothing moved."""

    def __init__(self, state: State) -> None:
        self.shops = len(state.shops)
        self.wagons = len(state.wagons)
        self.clean = state.clean
        self.branch = state.branch
        self.branch_state = state.branch_state
        self.act = state.act
        # Every relation, not only the owner's: cheap, exact, and it
        # cannot be wrong about which rival the delta reached.
        self.relations = {k: r.relation for k, r in state.rivals.items()}

    def restore(self, state: State) -> None:
        del state.shops[self.shops:]
        del state.wagons[self.wagons:]
        state.clean = self.clean
        state.branch = self.branch
        state.branch_state = self.branch_state
        state.act = self.act
        for key, relation in self.relations.items():
            state.rivals[key].relation = relation


def accept_deal(state: State, district: str) -> Shop:
    """THE atomic capital transaction (§2.4.2): the address, its
    wagon, the committed capital and the points clock, in one act.

    Both identities are minted ONCE, here, and nowhere else in
    production (rev. 31 item 1) — minting reserves nothing, so a
    second caller would be handed the same key and would overwrite
    the first record. Both records are built LOCALLY, the whole
    transaction is preflighted, and only then does anything reach
    the state — and if the world-level validators refuse what was
    built, every field goes back.

    The $13,000 never passes through the player's cash: it is
    committed to Carmine's contractor, which is what makes the
    capital equity rather than a deposit that might be spent on
    something else. Only the float and the reserve arrive."""
    payoff_day = _preflight(state, district)
    # Minted once, together — an address and its wagon arrive in the
    # same transaction (§2.4.2), and `validate_addresses` refuses an
    # address that keeps no wagon.
    shop_key = models.mint_shop_key(state)
    wagon_key = models.mint_wagon_key(state)
    # Built LOCALLY: nothing below is in the world yet. The initial
    # state is §2.4.2's, exactly — reputation 20, standard pantry,
    # ZERO ingredients unless purchased, empty stash, no upgrades, no
    # order book — and the dates are the lifecycle's (rev. 29 item 4):
    # accepted today, opening two mornings from now.
    shop = Shop(key=shop_key, district=district, reputation=20.0,
                quality="standard", price="standard",
                pantry_quality="standard", ingredients=0, stash={},
                upgrades=set(), demand_today=0, delivery_pool=0,
                legit_revenue_today=0,
                acceptance_day=state.day,
                opening_day=state.day + models.CONSTRUCTION_DAYS,
                # THE INITIAL VACANCY (rev. 30 item 2, rev. 34 item
                # 2): the post is empty from the moment the deal is
                # struck, and construction provides its one
                # appointment opportunity. This is the address's
                # STARTING STATE, not a transition out of a staffed
                # post — nothing vacated here, so nothing calls
                # `vacate_manager`. The player is offered the post
                # while the site is being built; a shop that opens
                # unmanaged runs under Carmine's nephew from its
                # first service.
                manager_post=models.ManagerPost(
                    vacancy_day=state.day, opportunity="pending"))
    wagon = Wagon(key=wagon_key, shop_key=shop_key)
    branch_state = BranchState.partner(
        points_due_day=first_points_due(shop, payoff_day))
    models.validate_branch_state("partner", branch_state)

    # ── commit, once, and undo entirely if the world refuses it ───
    undo = _Undo(state)
    try:
        state.shops.append(shop)
        state.wagons.append(wagon)
        state.clean += TO_CLEAN
        state.branch_state = branch_state
        state.branch = "partner"
        state.act = 2
        # A commercial declaration, priced through the existing
        # relation authority at one recorded number — and never
        # against a rival who is already dead, because a corpse
        # mounts no counterplay.
        owner = data.DISTRICTS[district]["rival"]
        if owner and state.rivals[owner].alive:
            models.adjust_relation(state, owner, TURF_RELATION_DELTA)
        # The postcondition of the whole act: what was just built is
        # a world the persistence boundary would accept.
        models.validate_cross_state(state)
    except Exception:
        undo.restore(state)
        raise
    return shop


def entry_scene(state: State, shop: Shop, con: Console) -> None:
    """What the money did, and what the calendar now owes (§3.2 D14).
    Transcript only — the transaction above already committed."""
    spec = data.DISTRICTS[shop.district]
    bs = state.branch_state
    con.header("CARMINE'S PARTNER — the money moves before the coffee "
               "is cold")
    con.say(f"  {money(FRONTED)} fronted. {money(COMMITTED)} of it never "
            f"touches your hands: {money(BUILD_OUT)} build-out and "
            f"{money(SECOND_WAGON)} for a used second wagon to his own "
            f"contractor, {money(PERMITS)} of permits paid clean, "
            f"because paperwork is paperwork.")
    con.say(f"  {money(TO_CLEAN)} reaches your register — "
            f"{money(OPENING_FLOAT)} opening float and {money(RESERVE)} "
            f"reserve. That is the whole of it. There is no deposit to "
            f"spend twice.")
    con.say(f"  The site: {spec['label']}. Keys on day "
            f"{shop.acceptance_day}, doors open the morning of day "
            f"{shop.opening_day} — his contractor, his schedule, no "
            f"dice.")
    owner = spec["rival"]
    if owner and state.rivals[owner].alive:
        con.bullet(f"{data.RIVALS[owner]['short']} hears about it "
                   f"before the sign goes up. You have opened on his "
                   f"floor, and he will not treat that as commerce.")
    elif owner:
        con.bullet(f"The district answered to {data.RIVALS[owner]['short']} "
                   f"once. Nobody is left to mind.")
    else:
        con.bullet("Nobody owns the Hill. Sal notices anyway — he "
                   "notices everything — and does nothing about it.")
    if bs is not None:
        con.say(f"  The obligation is points, not debt: "
                f"{money(2_500)} every {POINTS_CYCLE_DAYS} days, "
                f"first on day {bs.points_due_day}, unmarked bills "
                f"preferred, forever. No amount pays him off. That is "
                f"what equity means when Carmine says it.")


# ── the points clock (§2.4.2; rev. 29 items 1 and 7) ─────────────

def ledger(state: State) -> models.PartnerLedgerView:
    """THE derived view, from the one history. Every consumer reads
    this — the night, the card, the grade, the epilogue and the
    studies — so a number can never mean one thing on screen and
    another in FINDINGS."""
    bs = state.branch_state
    if bs is None:
        raise ValueError("no branch state — the points clock belongs "
                         "to a seated chair")
    return models.partner_ledger(bs)


def night_obligation(state: State, con: Console) -> None:
    """Partner's night work: counsel first, then the points clock —
    the same order and the same machinery the war uses.

    Counsel runs BEFORE the early returns below, because it is
    nightly work and the points cycle is a five-day event: retaining
    counsel and then being charged nothing on the four nights between
    bills is precisely the half-join this fixes (P4b.2 review).
    Partner unlocks the counterplay verbs (rev. 29 item 7), and a
    branch that unlocks the menus without running their nightly cost
    has bought the player a lawyer who never sends an invoice."""
    evidence.counsel_nightly(state, con)
    night_points(state, con)


def night_points(state: State, con: Console) -> None:
    """The cycle that falls due tonight, if one does.

    THERE IS NO PARTIAL PAYMENT: the complete bill clears the cycle
    or the cycle records a miss, because a half-paid bill is a third
    state the day-30 grade has no arm for. A miss stays owed — the
    next bill is prior arrears plus the new points plus a $500 vig —
    and the strike it leaves never unhappens, so the SECOND strike
    forecloses at any later cycle, consecutive or not.

    The record is appended ONCE and frozen; nothing here writes an
    arrears or strike counter, because both are derived."""
    bs = state.branch_state
    if bs is None or bs.points_due_day is None:
        return
    # NOTHING FALLS DUE ON A FINISHED RUN. The phase loop already
    # skips branch ticks once `game_over` is set, but the precedence
    # §2.5 describes belongs to this authority too — `counsel_nightly`
    # checks the same thing for the same reason. Without it, calling
    # this on a latched night would append a cycle to a run the
    # arrest had already ended, and the ledger would record a bill
    # nobody was alive to owe.
    if state.game_over:
        return
    if state.day < bs.points_due_day:
        return
    # AN OVERDUE LIVE CURSOR IS A BUG, not a bill to catch up on
    # (P4b.2 review). A cycle is processed on the night it falls due;
    # arriving here a day late means a night was skipped somewhere,
    # and quietly billing it now would write a record dated for a day
    # the run had already left. Refused BEFORE anything is appended.
    if state.day > bs.points_due_day:
        raise ValueError(
            f"partner: day {bs.points_due_day} fell due and was never "
            f"processed; this night is day {state.day}")
    view = ledger(state)
    bill, vig = view.next_bill, view.next_vig
    # The cursor is not None here — `points_due_day` was checked at
    # the top, and the view's next due day derives from it or from
    # the history's last record. Narrowed with an ignore rather than
    # an `assert` (assertions vanish under optimized Python, and this
    # project refuses them) and rather than a guard that could never
    # fire.
    due: int = view.next_due_day        # type: ignore[assignment]
    paid = models.pay_dirty_first(state, bill)
    bs.points_cycles.append(models.PointsCycleRecord(
        due_day=due, bill=bill, vig=vig, paid=paid,
        paid_day=state.day if paid else None))
    # The cursor advances from the DUE DATE, never from tonight, so
    # the schedule cannot drift when a bill is met late.
    bs.points_due_day = due + POINTS_CYCLE_DAYS
    after = ledger(state)
    if paid:
        note = (" — arrears cleared, and the strike stays on the "
                "books" if vig else "")
        con.bullet(f"Points to Carmine: {money(bill)}, unmarked, "
                   f"street money first{note}. Next on day "
                   f"{bs.points_due_day}.")
        return
    if after.foreclosed:
        # The second strike ends the run TONIGHT (§2.4.2). The arrest
        # latch keeps precedence by construction: accrual sets
        # game_over first, and the branch night ticks only run on
        # live games.
        if state.game_over is None:
            state.game_over = models.FORECLOSURE_ENDING
        con.bullet(f"The bill was {money(bill)} and it did not get "
                   f"paid. Two misses. Carmine does not raise his "
                   f"voice; a man you have never met is behind the "
                   f"counter before the ovens are cold.")
        return
    con.bullet(f"You miss the points: {money(bill)} owed and unpaid. "
               f"It stays owed, it carries {money(POINTS_VIG)} of vig "
               f"onto the next bill, and Carmine remembers. Miss "
               f"again — any cycle, not just the next — and the shop "
               f"is his.")


def night_insolvency(state: State, con: Console,
                     payroll_short: bool) -> None:
    """The shared clean-insolvency transition, in Partner's voice
    (rev. 15 item 3, rev. 29 item 7): two shops fed from an empty
    till end the same way every empty till does."""
    outcome = models.insolvency_tick(state, payroll_short)
    if outcome == "broke":
        con.say("  Two nights running: no payroll, no stock, no hidden "
                "dollar. Two rooms, both dark, and neither of them "
                "yours by morning.")
    elif outcome == "warned":
        con.say("  Nothing in either till, nothing on either shelf. "
                "One more night like this and it is finished.")
