"""Game orchestration: the 30-day run and its endings."""

from . import data, escrow, models, phases, sitdown, straight, war
from .config import GameConfig
from .models import State, new_state
from .rng import Streams
from .ui import Console, money

INTRO = """
Your uncle Enzo ran DiNapoli's Pizza on the edge of Old Harbor for thirty
years. Last month he died owing Carmine "Uncle Carmine" Rossi fifteen
thousand dollars, and the debt — like the shop, the wagon, the recipes and
two loyal employees — is now yours.

Carmine gave you thirty days. He was very polite about it.

The pizza is good. The margins are not. But a delivery wagon goes
everywhere, nobody looks twice at a pizza box, and this city is hungry
for more than a margherita.

Keep the food good. Keep the books believable. Keep the rivals afraid.
"""


def run(seed: int | None, con: Console, max_days: int | None = None,
        on_night=None, config: GameConfig | None = None,
        state: State | None = None) -> State:
    """`on_night(state, streams)` is an observation hook for the analysis
    harness — called after each completed day, it must not mutate.
    `config` is the immutable engine configuration; None means the
    defaults (fork off). `state` lets the harness inject a prepared
    starting state (the rev. 10 redemption cohort runs a frozen
    reference entry through this one loop rather than a drifted copy);
    None — every ordinary caller — starts a fresh game."""
    config = config if config is not None else GameConfig()
    streams = Streams(seed)
    state = new_state() if state is None else state
    con.say(INTRO)
    con.pause()

    last_day = min(max_days or data.DEBT_DUE_DAY, data.DEBT_DUE_DAY)
    while state.day <= last_day and not state.game_over:
        # The sit-down fires on state alone (a pending snapshot resumes
        # whatever the launch flags say); config only shapes which chairs
        # are actionable inside the scene.
        if sitdown.due(state):
            sitdown.run_scene(state, con, config)
        if state.branch == "quiet_sale" and not state.game_over:
            # The escrow week: the broker's card each diligence morning,
            # the closing on the morning after day four. Signing is the
            # one success that ends a run early (§2.5 precedence 3).
            escrow.diligence_morning(state, con, streams)
            if state.game_over:
                break
        plans = phases.morning(state, con, streams)
        report = phases.service(state, plans, con, streams)
        phases.night(state, plans, report, con, streams, config)

        if state.debt > 0:
            state.debt = int(state.debt * (1 + data.DEBT_RATE))
        _check_endings(state)
        if on_night is not None:
            on_night(state, streams)

    if not state.game_over:
        if state.branch == "straight":
            # §2.5 precedence 5: the branch's own day-30 matrix.
            state.game_over = straight.grade(state)
        elif state.branch == "war":
            # Campaign-count matrix (rev. 14 item 9); both broken lands
            # on the existing Syndicate text through "survived".
            state.game_over = war.grade(state)
        else:
            state.game_over = "survived" if state.debt <= 0 else "kneecaps"
    epilogue(state, con)
    return state


def _check_endings(state: State) -> None:
    if state.game_over:
        return
    if state.case >= 100:
        state.game_over = "arrested"
    elif state.clean <= 0 and state.dirty <= 0 and state.warehouse_cash <= 0 \
            and not any(sh.stash for sh in state.shops) \
            and all(sh.ingredients <= 0 for sh in state.shops) \
            and state.debt > data.START_DEBT * 2:
        state.game_over = "broke"


def epilogue(state: State, con: Console) -> None:
    con.header("EPILOGUE")
    net = state.net_worth()
    con.say(f"  Day {min(state.day, data.DEBT_DUE_DAY)}. "
            f"Net position {money(net)} | laundered {money(state.total_laundered)} "
            f"| case file {state.case:.0f}/100")

    e = state.game_over
    if e == "sold":
        tier = escrow.sale_tier(state)
        total = escrow.walkaway_total(state)
        con.say(f"  Walking money: {money(total)} — settlement, cash, and "
                f"whatever left with you (stock at book value).")
        # The closing outcome is persisted state, and the epilogue
        # drives from the real discriminator (rev. 8) — refusal,
        # unaffordability and an empty roster are different stories.
        outcome = state.branch_state.severance_outcome \
            if state.branch_state is not None else "pending"
        amount = state.branch_state.severance_paid \
            if state.branch_state is not None else None
        if outcome == "paid" and amount:
            con.say(f"  The crew's envelopes — {money(amount)}, handed "
                    f"over before the ink — are the part of this sale "
                    f"nobody had to do. Around the harbor, that's the "
                    f"part they'll retell.")
        elif outcome == "declined":
            con.say("  No envelopes. The crew found out on the buyer's "
                    "schedule and scattered on their own dime. Around the "
                    "harbor, that's the part they'll retell.")
        elif outcome == "unaffordable":
            con.say("  There was nothing left for envelopes — the sale "
                    "barely covered the pen that signed it. The crew knows "
                    "the difference between broke and cheap; it helps, a "
                    "little.")
        # not_applicable: nobody was left to tell, and the epilogue does
        # not invent a crew to be sorry for.
        if tier == "kept_trade":
            con.say("""
  The bill of sale lists ovens, tables, a wagon, a name. It does not
  list what rode out the back gate, or the cash nobody ever washed.
  You didn't leave the life. You downsized it — and the Case stays
  open on you, wherever you land.
  ENDING: Sold the shop, kept the trade.""")
        elif tier == "well":
            con.say("""
  Papers signed, keys handed over, every drawer empty and every dollar
  explicable. The new owner keeps the recipes. Nobody keeps your name.
  Whatever this city remembers, it isn't yours to carry.
  ENDING: Sold — and sold well. The clean number, earned.""")
        elif tier == "modest":
            con.say("""
  It isn't a fortune. It was never going to be a fortune — the card
  told you every morning exactly what a month like yours is worth.
  It's enough to leave, and leaving was the point.
  ENDING: Sold — a modest ending, honestly priced.""")
        else:
            con.say("""
  The number on the check is barely worth the pen. A hot file, a thin
  reputation, a buyer who knew you had no other door — the fire sale
  is what a bad month looks like, notarized.
  ENDING: Sold — the fire sale.""")
    elif e == "straight_exit":
        con.say("""
  Day thirty. The walk-in holds flour, the ledger holds nothing it
  can't explain, and the lunch line goes out the door. You wound the
  wheel down with your own hands, paid for every silence honestly, and
  let the lawyers argue the rest into footnotes. Nobody does that.
  The city eventually forgets there was anything to remember — and
  forgetting cost you every dollar it looks like it didn't.
  ENDING: The Legitimate Exit — earned. The rarest pie on the menu.""")
    elif e == "almost_out":
        con.say(f"""
  Every term met but one: the file. Stock gone, money clean, people
  settled, feuds cold — and a case number that still opens when your
  name is typed ({state.case:.0f}, and the exit wanted
  {straight.GOAL_CASE:.0f}). Clean, and they're still watching.
  You got out. You'll spend a long time proving it.
  ENDING: Almost Out.""")
    elif e == "half_measures":
        con.say("""
  Day thirty. You left the trade — and never landed the exit. What
  failed, by name:""")
        for term in straight.failed_terms(state, as_of=data.DEBT_DUE_DAY):
            con.say(f"    · {term}")
        con.say("""
  Half in, half out — the most expensive place to stand.
  ENDING: Half Measures.""")
    elif e == "arrested":
        if state.branch == "war" and war.won_then_lost(state):
            # The §2.5 styling exception: the same terminal, a distinct
            # text arm — the capture transition completed before the
            # latch (rev. 14: transition ordering, never a calendar
            # coincidence).
            con.say("""
  You broke him. The district was learning your name for a new reason —
  and then they come at 6 a.m., politely, with a warrant that cites
  your own register tapes. You won the war. The verdict goes the other
  way. Both things stay true.
  ENDING: The Case closed — on you. (Won the war. Lost the verdict.)""")
        else:
            con.say("""
  They come at 6 a.m., politely, with a warrant that cites your own
  register tapes. The pizza was never the problem. The paperwork was.
  ENDING: The Case closed — on you.""")
    elif e == "kneecaps":
        con.say(f"""
  Day thirty. Carmine arrives with two nephews and a ledger of his own.
  You still owe {money(state.debt)}. The shop is his now; the recipes too.
  You keep your legs — a courtesy, he says, to your uncle.
  ENDING: The debt came due.""")
    elif e == "syndicate":
        # The ending renders from the campaign damage ledger (rev. 16
        # item 8): it names only the channels this player actually
        # used, and the prosecutor appears only when the prosecution
        # happened.
        used = {dr.channel for c in war.campaigns(state)
                for dr in c.damage}
        bits = [label for ch, label in (
            ("jobs", "night jobs"), ("corners", "corner routes"),
            ("ovens", "cold ovens"), ("defense", "a defended door"))
            if ch in used]
        if "ledger" in used:
            bits.append("a woman in a gray suit who thinks you're a "
                        "very lucky bystander"
                        if any(c.violence_raised
                               for c in war.campaigns(state))
                        else "a stolen ledger spent to the last page")
        how = ", ".join(bits[:-1]) + (" and " + bits[-1]
                                      if len(bits) > 1 else
                                      (bits[0] if bits else "patience"))
        con.say(f"""
  Moretti's is a mattress store now. Vinnie's is a parking lot. You
  declared both wars at a breakfast table and finished both before the
  month did — {how}. Every warmer bag in the
  city rides in one of your wagons.
  ENDING: The syndicate. Nothing moves without extra toppings.""")
    elif e == "burned_out":
        con.say("""
  They warned you twice — once with cars in the mirror, once with the
  boards already over the window. The second break-in finds a shop too
  hurt to save, and by morning there is nothing on the corner but smoke
  and a wagon with nowhere to park.
  ENDING: Burned Out. The war came home.""")
    elif e == "harbor_yours":
        fallen = war.broken_keys(state)[0]
        second = war.target_key(state)
        # The ACTUAL captured turf, derived and named (rev. 19 item
        # 5): Sal's fall captures Little Sicily; Vinnie's captures
        # Old Harbor and the Meadows — never one generic district.
        turf = [d["label"] for d in data.DISTRICTS.values()
                if d["rival"] == fallen]
        turf_s = " and ".join([", ".join(turf[:-1]), turf[-1]]
                              if len(turf) > 1 else turf)
        con.say(f"""
  Day thirty. {data.RIVALS[fallen]['label']} is a name on old menus.
  Their corners call your board, {turf_s} learned your number,
  and the harbor knows exactly one operation that matters.""")
        if second is not None:
            con.say(f"  The second war — {data.RIVALS[second]['short']}'s —"
                    f" has already begun. Victories don't retire you "
                    f"here; they promote you.")
        crew_standing = sum(1 for x in state.hired()
                            if not x.arrested and not x.injured_days)
        con.say(f"  What it cost is on the board too: Case "
                f"{state.case:.0f}/100, {crew_standing} of "
                f"{len(state.hired())} crew standing, and a shop that "
                f"{'kept its ovens' if not any(sh.damage_days for sh in state.shops) else 'is still limping'}.")
        con.say("  ENDING: The Harbor Is Yours.")
    elif e == "long_war":
        camp = war.campaigns(state)[-1] if war.campaigns(state) else None
        ratio = ""
        if camp is not None and state.rivals[camp.rival_key].alive:
            rv = state.rivals[camp.rival_key]
            ratio = (f" He stands at {rv.strength:g} of the "
                     f"{camp.starting_hundredths / 100:g} he started "
                     f"with;")
        con.say(f"""
  Day thirty. The war is not won and it is not over — there is no over
  anymore.{ratio} the truce door closed the morning you named him, and
  it does not reopen. The vendetta outlives the month, the ledger of
  damage outlives the vendetta, and the city settles in to watch.
  ENDING: A Long War. You chose a war that will outlive the month.""")
    elif e == models.FORECLOSURE_ENDING:
        misses = [c for c in state.branch_state.points_cycles
                  if not c.paid] if state.branch_state is not None else []
        when = f"on day {misses[-1].due_day}" if misses else "in the end"
        con.say(f"""
  Two misses. Carmine never said they had to be consecutive, and you
  heard what you wanted to hear. The second one came due {when}
  and the money was somewhere else: in a wall, in a wagon, in a
  man's pocket.
  His capital was never a loan and there was never a payoff number.
  You were an operator with two rooms. Now you are a man who used to
  have one.
  ENDING: Foreclosed — his money, his shop, his city.""")
    elif e == "broke":
        if state.branch == "straight":
            con.say("""
  Empty pantry, empty safe, empty dining room — and no wagon in the
  night to refill any of them, because you burned that book yourself.
  The cover business couldn't cover the cover-up.
  ENDING: The oven went cold. Going straight costs money too.""")
        else:
            con.say("""
  Empty pantry, empty safe, empty dining room. You lock the door from
  the outside and drop the key through the mail slot.
  ENDING: The oven went cold.""")
    else:  # survived — grade the exit
        rivals_alive = sum(1 for r in state.rivals.values() if r.alive)
        if state.case < 30 and net > 20000:
            con.say("""
  Debt cleared, books plausible, dining room full. On day thirty you cater
  the precinct's retirement party — and quietly stop taking coded orders.
  The city eventually forgets there was anything to remember.
  ENDING: The legitimate exit. The rarest pie on the menu.""")
        elif rivals_alive == 0:
            con.say("""
  Moretti's is a mattress store now. Vinnie's is a parking lot. Every
  warmer bag in the city rides in one of your wagons.
  ENDING: The syndicate. Nothing moves without extra toppings.""")
        elif net > 8000:
            con.say("""
  Carmine is paid. The shop turns a profit both ways. Rivals call before
  they cross the harbor. It isn't safe — it will never be safe — but it's
  yours, and tonight the ovens are warm.
  ENDING: The operation holds.""")
        else:
            con.say("""
  You made the last payment with the register still warm from the dinner
  rush. There's almost nothing left over — except the shop, the wagon,
  the crew, and everything you now know about this city after dark.
  ENDING: Debt-free, dead broke, dangerous.""")

    if state.case_flags:
        con.say("")
        con.say("  What the file said:")
        for line in state.case_flags[-6:]:
            con.say(f"    · {line}")
