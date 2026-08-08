# North-star brief and design invariants (canon)

> **Provenance:** the second founding document, issued after the original
> pitch with the instruction to treat the pitch as product vision rather
> than an implementation order. Reproduced verbatim as canon. The ten
> nonnegotiable invariants below are the standing acceptance bar for every
> change to the game; most are now enforced directly by the test suite
> (see [`docs/canon/README.md`](README.md) for the mapping).

---

Treat the previous brief as the product vision, not as an instruction to
implement every described feature immediately.

Act as both lead gameplay-systems designer and technical director. Your job
is to turn the concept into the smallest playable prototype capable of
proving whether the hybrid is actually fun.

## North-star experience

The player should feel proud of the pizza shop they are building, tempted
by the speed and profitability of the underground market, and increasingly
worried that the criminal operation will destroy the legitimate business
they now care about.

The central question behind nearly every decision should be:

**"How much of my real pizza business am I willing to risk for this
opportunity?"**

## Nonnegotiable design invariants

1. The pizza business and underground business must share constrained
   resources: drivers, vehicles, time, storage, property, employees and
   cash flow.
2. The pizza shop must be a genuinely functional business, not a passive
   laundering interface.
3. Legitimate success must create criminal opportunity. Criminal activity
   must create legitimate operational consequences.
4. The fast loop should preserve Dope Wars: volatile markets, limited
   capacity, incomplete information, debt pressure and the temptation to
   make one more run.
5. The long loop should preserve Fast Food Tycoon: persistent branches,
   employees, recipes, competitors, territorial expansion, sabotage and
   raids.
6. Raids must emerge from the economic and territorial simulation. They
   cannot be disconnected combat missions.
7. Rival actions and police attention must be telegraphed enough to permit
   counterplay. Severe losses should usually result from a risk the player
   knowingly accepted.
8. The player must understand why an outcome occurred. Avoid unexplained
   random punishment.
9. The legal and illegal businesses must remain in tension. Neither should
   become a solved passive system that merely feeds the other.
10. Nearly every major upgrade should carry a dual use or tradeoff.

## First prototype

Build a 15–25 minute graybox run covering seven in-game days.

Include only:

- One functioning pizzeria.
- Three city districts.
- Three underground commodities.
- One player vehicle.
- One or two named employees.
- One meaningful rival operator.
- Clean money, dirty money and debt.
- Legitimate and covert deliveries sharing the same route capacity.
- District prices that change through visible events.
- A laundering ceiling based on actual restaurant revenue.
- Heat and persistent evidence as separate concepts.
- One restaurant upgrade with both legitimate and criminal utility.
- One minimal tactical raid using a graybox restaurant or warehouse layout.
- One possible retaliatory action from the rival.
- A complete win, loss or survival outcome on day seven.

The prototype does not need attractive art. It needs enough interface
clarity to expose the decisions.

## Core daily state machine

Implement the run around four explicit phases:

1. Morning intelligence and planning.
2. Restaurant service and route dispatch.
3. Delivery resolution and street encounters.
4. Night accounting, storage, upgrades and criminal actions.

Time should advance through committed actions and shifts, not through an
uncontrollable continuous clock.

## The first tactical raid

Keep the initial raid extremely small:

- One fixed location.
- One attacker team.
- One or two defenders.
- One objective, such as stealing a stash or ledger.
- Basic movement, visibility, noise and escape.
- A short time limit.
- Consequences that feed directly back into the economy.

Do not build a complete combat game yet. The purpose is to test whether
attacking a physical business feels like a natural extension of the tycoon
simulation.

The layout used for the legitimate restaurant should eventually become the
tactical layout used during raids. Preserve that architectural direction
even if the first implementation uses a simplified location.

## Explicitly out of scope

Do not currently build:

- An open-world city.
- Manual driving.
- Multiplayer.
- Multiple cities.
- A large campaign.
- Final art or animation.
- A full recipe-placement editor.
- Detailed cooking mechanics.
- Large weapon catalogs.
- Complex tactical enemy AI.
- Procedural city generation.
- Extensive dialogue or narrative content.
- A complete employee-relationship simulation.
- More commodities, districts or upgrades than the prototype needs.

Do not solve lack of depth by adding content. First prove that the shared
systems produce hard decisions.

## Technical expectations

Inspect the existing repository and preserve its conventions unless there
is a concrete reason not to.

Design the simulation so that it is:

- Deterministic when given a seed.
- Separated from rendering and interface code.
- Data-driven for commodities, districts, events, employees and upgrades.
- Saveable and reloadable without changing outcomes.
- Observable through a detailed event log.
- Testable without manually operating the UI.
- Equipped with a debug panel showing prices, heat, evidence, rival state
  and economic calculations.

Create invariant tests confirming that:

- Legitimate and covert deliveries consume the same capacity.
- Dirty money cannot silently become clean money.
- Laundering capacity derives from actual legitimate performance.
- Market events affect the stated districts and commodities.
- Criminal activity can damage restaurant performance.
- Restaurant investments can alter criminal opportunity or risk.
- Failed raids produce defined, recoverable consequences.
- The same seed and decisions produce the same result.

Include a simple headless simulation runner so the seven-day economy can be
exercised across many seeds. Use it to identify runaway profits,
unavoidable bankruptcy, dominant strategies and events that do not
materially affect player decisions.

## Before substantial implementation

Produce concise project documentation containing:

1. Your restatement of the game's core promise.
2. The seven-day prototype specification.
3. The primary game-state model.
4. The daily action/state flow.
5. The shared-resource economy.
6. The rival decision model.
7. The raid-to-economy consequence model.
8. A risk register identifying the hardest design and technical
   uncertainties.
9. A list of assumptions and unresolved product decisions.
10. A phased implementation plan with acceptance criteria.

Make recommendations for unresolved decisions. Do not block progress on
reversible choices, but surface any decision that would materially
constrain the final game.

The first milestone is successful only if a player faces at least three
genuine cross-system decisions—for example, sacrificing pizza delivery
quality for covert capacity, exposing a valuable employee to danger, or
leaving the restaurant under-defended to raid a rival.

At the end, report what the prototype demonstrates, what remains unproven
and which mechanics should be cut, changed or expanded next.
