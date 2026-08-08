"""Game orchestration: the 30-day run and its endings."""

from . import data, phases, sitdown
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
        on_night=None, config: GameConfig | None = None) -> State:
    """`on_night(state, streams)` is an observation hook for the analysis
    harness — called after each completed day, it must not mutate.
    `config` is the immutable engine configuration; None means the
    defaults (fork off)."""
    config = config if config is not None else GameConfig()
    streams = Streams(seed)
    state = new_state()
    con.say(INTRO)
    con.pause()

    last_day = min(max_days or data.DEBT_DUE_DAY, data.DEBT_DUE_DAY)
    while state.day <= last_day and not state.game_over:
        # The sit-down fires on state alone (a pending snapshot resumes
        # whatever the launch flags say); config only shapes which chairs
        # are actionable inside the scene.
        if sitdown.due(state):
            sitdown.run_scene(state, con, config)
        plans = phases.morning(state, con, streams)
        report = phases.service(state, plans, con, streams)
        phases.night(state, plans, report, con, streams, config)

        if state.debt > 0:
            state.debt = int(state.debt * (1 + data.DEBT_RATE))
        _check_endings(state)
        if on_night is not None:
            on_night(state, streams)

    if not state.game_over:
        state.game_over = "survived" if state.debt <= 0 else "kneecaps"
    epilogue(state, con)
    return state


def _check_endings(state: State) -> None:
    if state.game_over:
        return
    if state.case >= 100:
        state.game_over = "arrested"
    elif state.clean <= 0 and state.dirty <= 0 and state.warehouse_cash <= 0 \
            and not state.shop_stash and state.shop.ingredients <= 0 \
            and state.debt > data.START_DEBT * 2:
        state.game_over = "broke"


def epilogue(state: State, con: Console) -> None:
    con.header("EPILOGUE")
    net = state.net_worth()
    con.say(f"  Day {min(state.day, data.DEBT_DUE_DAY)}. "
            f"Net position {money(net)} | laundered {money(state.total_laundered)} "
            f"| case file {state.case:.0f}/100")

    e = state.game_over
    if e == "arrested":
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
    elif e == "broke":
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
