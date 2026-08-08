# Extra Toppings

Build a neighborhood pizza empire. Use its delivery network to control the
city's underground market. Keep the food good, the books believable and the
rival shops afraid.

A turn-based strategy game in the tradition of **Dope Wars** crossed with
**Fast Food Tycoon** — except the pizza shop isn't a menu skin, it's the
actual machinery of the criminal operation: its cash flow, delivery routes,
employees, storage and customer traffic all create both opportunity and
exposure.

This is the **first playable vertical slice**: pure-Python, no dependencies,
runs in any terminal.

## Quick start

```
git clone https://github.com/KenStager/Extra-Toppings.git
cd Extra-Toppings
python3 -m extra_toppings --seed 24
```

That's the whole install: Python 3.10+ and a terminal. Every choice is a
numbered menu — type the number, press enter. Pressing enter alone takes
the suggested default on amount prompts. A full 30-day run takes about
15–25 minutes.

Recommended first seeds:

| Seed | Character |
| --- | --- |
| `--seed 24` | Forgiving opening — quiet law, clear market signals |
| `--seed 39` | Knife-edge — big early temptation, hot second half |
| `--seed 8`  | Hostile — a jackpot-shaped trap; restraint required |

Other ways to run it:

```
python3 -m extra_toppings                        # unseeded (random) run
python3 -m extra_toppings --auto --smart --verbose   # watch a bot play
python3 -m extra_toppings.bench --seeds 60       # strategy benchmark
python3 -m analysis.experiments all              # deep-analysis studies
python3 -m unittest discover -s tests            # test suite
```

Deep-simulation results and their history live in `docs/FINDINGS.md`;
every table there is reproducible with `analysis/experiments.py`.

## The setup

Your uncle Enzo ran DiNapoli's Pizza on the edge of Old Harbor for thirty
years. He died owing Carmine "Uncle Carmine" Rossi **$15,000**, and the debt
— like the shop, the delivery wagon and two loyal employees — is now yours.
Carmine gave you thirty days. He was very polite about it.

The pizza is good. The margins are not. But a delivery wagon goes everywhere,
nobody looks twice at a pizza box, and this city is hungry for more than a
margherita.

## The daily rhythm

Time advances when you commit to things, not on a clock.

**Morning — prepare.** Read the paper (city events move both markets), hear
rumors about prices in districts you haven't visited, take or skip the
supplier's cash-only offer, set kitchen policy, manage staff, buy
improvements, and plan tonight's route — and, eventually, tonight's raid.

**Service — operate.** The shop runs on policy, not on you cooking each pie.
The dispatch board mixes real orders with coded ones. A route of twenty
pizzas and three concealed drops is safe but slow; a route that's mostly
product is efficient and looks exactly like what it is. Ride along yourself
and every drop and traffic stop is played out; send a driver alone and you
find out how their night went when they do or don't come back.

**Night — settle accounts.** Count clean and dirty money separately. The
register can only absorb dirty cash **in proportion to the day's believable
sales** — wash more and a spreadsheet somewhere notices. Pay staff, rent, and
Carmine (he prefers unmarked bills). Move stash between the shop and the
warehouse. Talk to rivals. Then the city advances: prices shift, rivals act,
and the Case gets thicker or thinner.

## The systems in the slice

Everything from the design pitch's "first playable version" checklist:

| System | In the slice |
| --- | --- |
| One customizable pizzeria | Quality/pricing policy, five upgrades, reputation, kitchen capacity |
| Four districts | Old Harbor, University Hill, Little Sicily, The Meadows — each with traffic, underground demand, patrol pressure and turf |
| Four contraband categories | Extra Oregano, Special Mushrooms, Hot Honey, White Truffle Powder |
| Two meaningful rivals | Sal (great food, quiet knives) and Vinnie (terrible food, loud ones) — with memory, telegraphed raids and an escalation ladder |
| Eight named employees | Four stats, a personality trait each, morale, injuries, arrests. Reading someone in gains a courier and creates a witness |
| One delivery vehicle | Enzo's wagon: 24 cargo slots shared between pizzas and product |
| Thirty-day debt deadline | $15,000 compounding daily. Carmine fronts a starving shop groceries — onto the debt |
| Dynamic prices and events | Concerts, seizures, crackdowns, festivals, heat waves; overselling a district depresses its price |
| Clean and dirty accounting | Two ledgers; laundering capped by believable revenue; dirty cash exists physically and can be stolen or seized |
| One warehouse | Rentable, bulk storage, off-site cash stash — and one more address to defend |
| Three raid objectives, one layout system | Steal their stock, photograph their ledger, wreck their ovens — the same room-by-room system resolves their raids on you |

Two layers of law: **Heat** is local weather (rises with sloppy routes,
decays overnight), **the Case** is climate — persistent evidence that only
accumulates: seized ledgers, arrested drivers who knew things, register
tapes claiming $4,000 on a rainy Tuesday. At 100, they come at 6 a.m. with
a warrant.

## Endings

Paying Carmine is survival, not victory. How you stand on day thirty decides
the epilogue: the legitimate exit, the syndicate, the operation that holds,
debt-free-dead-broke-dangerous — or kneecaps, cold ovens, and the Case
closing on you.

## Development

```
python3 -m unittest discover -s tests     # full suite
python3 -m extra_toppings --auto 30       # chaos-monkey run (crash test)
python3 -m extra_toppings --auto --smart  # heuristic bot (balance probe)
```

The tests assert the design's central bet both ways: a random player
completes 30 days without breaking the engine, and a simple sensible
strategy beats the debt on some seeds but not all — the deadline still
bites.

### Layout

```
extra_toppings/
  data.py      # all static content: districts, goods, people, rivals, events
  models.py    # game state dataclasses
  market.py    # prices, events, rumors, oversell depression
  shop.py      # the legitimate restaurant simulation
  routes.py    # delivery routes, covert drops, traffic stops
  raids.py     # tactical night jobs, offense and defense
  rivals.py    # rival AI: escalation, poaching, extortion, tribute
  phases.py    # morning / service / night orchestration
  game.py      # the 30-day run and endings
  bot.py       # GreedyBot (balance probe)
  ui.py        # console front end + random bot
```

### Not in the slice (on purpose)

Open-world driving, multiplayer, manual pizza-cooking minigames, additional
branches, act II/III progression. The slice exists to answer one question:
*does running the pizzeria make the underground trading more interesting,
and does the underground operation make every restaurant decision more
dangerous?*
