# Simulation findings

Reproduce any table with the versioned harness:

```
python3 -m analysis.experiments all          # or: sweep/grid/policy/trajectory/raids/events
```

Baseline for round 1 is the frozen vertical slice (`v0.1-vertical-slice`,
commit `5982646`). Round 2 is the System Integrity pass. Bots are
instruments, not targets: nothing was tuned to make them win.

## Round 1 — the frozen slice (pre-integrity fixes)

150 seeds per strategy, 30-day runs:

| Strategy | Payoff | Arrests | Case μ | Rep μ | Notes |
| --- | --- | --- | --- | --- | --- |
| greedy | 52% | 1% | 46 | 2 | dominant; median payday day 15 |
| cautious | 17% | 0% | 29 | 2 | loses slowly to interest |
| pizza-first | 0% | 0% | 7 | 25 | straight business cannot beat the debt |
| crime-heavy | 23% | 17% | 58 | 5 | wins fast or gets caught |
| random | 0% | 0% | 8 | 3 | chaos-monkey floor |

Key round-1 findings (details in PR #1 discussion):

1. Interior optimum in cargo-vs-cover (¾ load + 4–8 cover beat the extremes).
2. Laundering discipline was the strongest law lever (1% vs 21% arrests).
3. Ride-along dominated delegation ~3.5× (35% vs 10% payoff).
4. Quiet unarmed raids were nearly free money (~$4.8k haul, ≈0 Case).
5. Runs were decided by ~day 15; the deadline week held no drama.
6. Founding staff walked in ~65% of greedy runs, invisibly.
7. Heat never bound a mobile player; the Case did all disciplining.
8. Only 2 of 8 city events measurably moved outcomes for non-news play.

### Integrity defects found in review (all fixed in round 2)

- **Chunked-laundering exploit**: each `_launder` call was checked against
  the full ceiling, so five $1k chunks generated a quarter of the evidence
  of one $5k lump. The allowance is now cumulative per night
  (`tests/test_integrity.py::TestChunkedLaundering`).
- **Incomplete legit ledger**: route pizza revenue reached clean cash but
  not the believable-sales ceiling. All honest revenue now feeds
  `legit_revenue_today` (`TestCompleteLegitLedger`).
- **Phantom cover**: cover stops were conjured from ingredients alone. Cover
  now comes only from a delivery-order pool derived from real demand
  (reputation, policy, events, coupons) (`TestRealCover`).
- **Missing action economy**: one employee could drive the route and raid
  the same night; a driver arrested at dusk still raided at midnight;
  ride-along busts had no owner consequence and never arrested the driver.
  All four closed (`TestAssignments`, owner exposure in `routes._bust`).
- **Permanent coupon damage**: a rival's coupon blitz subtracted permanent
  reputation; it now suppresses demand for 3 days (`TestCouponIsTemporary`).
- **Shared RNG stream**: any decision shifted the whole world's dice. Split
  into per-day derived world channels (events, prices, rumors, supplier,
  demand, law) and persistent player streams (routes, rivals, raids, staff).
  The event schedule is now provably action-independent
  (`test_world_is_action_independent`).

## Round 2 — after the System Integrity pass

Same protocol, plus the new market-aware speculator bot (reads rumors, news
and price boards from the same text a human sees; routes toward expected
margin; holds inventory when numbers are poor).

150 seeds per strategy:

| Strategy | Payoff | Arrests | Case μ | Rep μ | Net med | Driver arrests |
| --- | --- | --- | --- | --- | --- | --- |
| **market** | **52%** | 0% | **24** | **24** | **+$2,116** | 40 |
| greedy | 45% | 2% | 55 | 6 | −$3,889 | 123 |
| cautious | 19% | 1% | 44 | 7 | −$10,182 | 74 |
| crime-heavy | 16% | 4% | 44 | 10 | −$20,307 | 77 |
| pizza-first | 0% | 0% | 7 | 39 | −$30,856 | 0 |
| random | 0% | 0% | 10 | 3 | −$46,130 | 3 |

What changed materially, as predicted:

1. **Intelligence beats aggression now.** The market bot matches greedy's
   old payoff with half the Case, a living restaurant (rep 24 vs 6), the
   earliest healthy payday (median day 12) and the only positive median
   net. The Dope Wars information game — rumors, news, price memory — is
   finally the winning game, and it wins *quietly*.
2. **Strip-mining degrades.** Greedy fell 52% → 45% with Case up 9 points:
   a neglected shop now loses its delivery pool, which strips its cover,
   which raises suspicion. The causal chain
   staff → reputation → demand → cover → safety is live.
3. **Delegation is a tradeoff, not a dominance.** Matched pairs: boss rides
   18% payoff / Case 39 vs driver alone 11% / Case 18 (was 35% vs 10%).
   Ride-along busts can now arrest the driver and put the owner in the
   file; familiarity and driving skill lift solo routes. Gap: 3.5× → 1.6×,
   with a real quiet-vs-profitable choice underneath.
4. **The laundering lever survived its exploit fix.** Discipline vs
   launder-everything: 3% vs 23% arrests at equal payoff — the choice is
   now purely risk-priced, and chunking no longer evades it.
5. **Zero-cover routes get people arrested** (10% arrests at low
   cargo/no cover in the grid). The cargo optimum flattened into a band —
   "at least half a load, with real cover" — rather than a single magic
   number, which is the healthier shape.

## Round 2 revision — review of the integrity pass found three more defects

Independent review of the first round-2 numbers found three further
integrity problems, all fixed and regression-tested:

- **Stale-demand price switch**: demand was rolled against morning policy,
  but service charged whatever the menu said by then — alternating
  cheap/gourmet sold gourmet tickets to a cheap-sized crowd. Demand is now
  a deterministic function of policy times a once-rolled daily shock, and
  recomputes whenever policy changes (`TestDemandPolicyIntegrity`).
- **Delivery orders bypassed kitchen capacity**: a 60-cap kitchen could
  produce 72 pizzas (60 counter + 12 route). Route production now comes
  out of the same oven capacity, so the second oven, raid damage, cooks
  and ingredients genuinely gate criminal cover
  (`TestSharedKitchenCapacity`).
- **Route planning mutated live state**: planning then cancelling
  destroyed stash and ingredients; repeated replanning stranded stock.
  Plans are now intentions; resources commit once, at service start
  (`TestTransactionalPlanning`). Resignations also now follow a
  confront → one-management-window → walk sequence
  (`TestResignationFlow`).

The third bug had been silently draining inventory from *bot* runs on
every replan, which means the provisional round-2 numbers were biased
low across the board. Final numbers, same protocol (150 seeds):

| Strategy | Payoff | Arrests | Case μ | Rep μ | Net med | Driver arrests |
| --- | --- | --- | --- | --- | --- | --- |
| **market** | **61%** | 1% | **26** | 21 | **+$6,940** | 40 |
| greedy | 58% | 8% | 58 | 7 | +$6,683 | 139 |
| cautious | 32% | 1% | 42 | 6 | −$8,192 | 80 |
| crime-heavy | 23% | 8% | 44 | 9 | −$19,388 | 77 |
| pizza-first | 0% | 0% | 7 | 34 | −$31,442 | 0 |

Revised readings:

1. **The headline survives and sharpens.** Market-aware play now leads
   outright (61% vs 58%) while carrying less than half greedy's Case,
   an eighth of its arrest rate, and triple its reputation. Blind
   aggression can match the payoff only by absorbing dramatically more
   prosecution risk.
2. **Intermediate loads with real cover outperform extremes.** (An
   earlier draft froze "¾ load peaks at 67%" from a 40-seed grid; at 150
   seeds the cell leader is not stable, so the durable claim is the band,
   not a point — see the round-3 grid below.) The full-wagon and
   zero-cover edges now cost real arrests either way.
3. **Delegation tradeoff holds after the fixes**: boss rides 23% payoff /
   Case 38 vs driver alone 16% / Case 19 (~1.4×, with the quiet-route
   discount intact).
4. **Laundering discipline still buys safety, not income**: 11% vs 41%
   arrests at equal payoff.
5. Pizza-first remains 0% — the structural temptation is untouched by
   any of the integrity work.

## Round 3 — five edge cases against the fixes themselves

A further review pass reproduced five defects, three of which weakened
the round-2 fixes. All are closed with regressions through the actual
player paths (`tests/test_integrity.py`, round-3 classes):

- **A raise didn't always answer the confrontation**: +2 morale from 1
  left the employee critical and still walking. The real raise path now
  clears `resignation_pending` and lifts morale out of the critical band
  (`TestRaiseAnswersConfrontation`, driven through the staff menu).
- **Route drivers weren't live-revalidated**: a driver fired after
  planning still drove. `_commit_route` now scrubs the route — committing
  nothing — if the driver is unavailable (`TestDriverRevalidation`).
- **Ingredient-quality arbitrage**: buy 40 cheap orders for $120, flip
  policy to gourmet, serve them at gourmet tickets. Stock now keeps the
  quality it was bought at (`Shop.pantry_quality`); mixing grades drags
  the pantry to the lower one, and the kitchen cooks — and gets
  reviewed — as what's actually in the walk-in. The scam still "works"
  for a day; the reputation engine now prices it (`TestQualityIdentity`).
- **New effects lost a day**: coupon blitzes and raid damage created at
  night were immediately aged by the end-of-night tick. Effects that
  served today now age at close, before tonight creates new ones — a
  3-day blitz suppresses three full service days (`TestEffectDurations`).
- **Save v2 omitted `demand_shock`**: a reload silently reset the day's
  demand luck. The field is serialized, and a completeness test now
  asserts every `State` dataclass field appears in the save, so future
  fields can't be forgotten (`TestSaveCompleteness`).

Final study on the corrected engine (150 seeds; bots don't exploit any
of the five closed paths, so the headline is expected to hold — and does):

| Strategy | Payoff | Arrests | Case μ | Rep μ | Net med |
| --- | --- | --- | --- | --- | --- |
| **market** | **61%** (91/150) | 1% | **26** | 20 | **+$6,559** |
| greedy | 58% (87/150) | 9% | 60 | 7 | +$6,392 |
| cautious | 33% | 1% | 42 | 6 | −$8,050 |
| crime-heavy | 22% | 6% | 44 | 8 | −$19,541 |
| pizza-first | 0% | 0% | 7 | 33 | −$32,536 |

150-seed cargo × cover grid (payoff% / arrest% / mean Case), corrected
engine:

```
         cover= 0 cover= 4 cover= 8 cover=12
cf=0.25   26/ 6/55  35/ 0/45  40/ 1/43  44/ 1/41
cf=0.5    37/10/59  56/ 4/55  58/ 4/53  60/ 1/51
cf=0.75   48/11/62  54/ 4/60  52/ 3/57  57/ 3/57
cf=1.0    47/ 8/59  54/ 9/61  58/ 9/60  56/ 8/59
```

The durable claims at this power: **intermediate-to-full loads with real
cover form a broad ~52–60% plateau whose cell leader is not stable**
(half-load + full cover led this run at 60%; do not freeze a point
optimum); the zero-cover column is uniformly the arrest column
(6–11%); and within every row, more cover monotonically buys down the
Case. Context — heat, events, driver, district — should be what moves
the ideal split, not a memorized ratio.

## Round 4 — raid pricing (design pass, post-merge)

Raids stop being an ATM. Five mechanisms, all tested
(`tests/test_raid_pricing.py`):

- **Target alertness** (`Rival.alertness`, 0–10): every attempt teaches
  them (+1 fail/abort, +2 success); guards multiply and sharpen with it,
  shelves thin, and it decays only slowly (~1 point per 3 quiet days).
  At alertness 4+ the game says so: "They've been expecting somebody."
- **Pattern evidence**: each successful job after the first adds Case
  (1.5 × prior jobs, capped at 8) — even ghosts leave handwriting. A
  ten-raid spree now costs ~54 Case on pattern alone.
- **Physical carry limits**: 8 bulk per crew member with the wagon,
  4 without — and the wagon is a contested resource: if it runs tonight's
  route, the raid crew carries duffel bags.
- **Storage bottleneck**: stolen stock must fit the shop stash, then the
  warehouse if rented; the rest stays in their alley.
- **Consumable ledger**: leaning on a stolen ledger spends it.
- **Decoy cap**: the empty-the-stash defense protects exactly one
  wagonload; overflow is found and taken.

### Round 4 correction (review)

The first cut of this pass had three defects: alertness raised guard
*drama* without touching the quiet-action odds that decide success;
cheap-goods-first loading let thinner shelves yield *richer* successful
hauls (expected $/attempt was flat at ~$250 across repeats at 5,000
trials); alertness decayed on the raid night itself; and downed crew
still carried full loads. All fixed:

- Alertness now directly penalizes Slip-past and quiet-takedown odds
  (−0.04/point), and crews load the expensive shelves first — which is
  exactly what an alerted target locks down hardest.
- Decay skips any rival hit that same day (`Rival.last_raided_day`).
- Extraction capacity counts the crew that reaches the door, not the
  crew that walked in.
- Security level ("sleepy / wary / hardened / fortress") shows in the
  target menu; the pattern premium is warned before committing and
  announced the moment it lands.

Measured at 2,000 trials (`analysis/experiments.py raids --trials 2000`;
primary metric is expected $ per attempt, failures included):

```
attempt 1: success 20%  expected $781/attempt  ($3,799 per success)
attempt 2: success 18%  expected $597/attempt  ($3,288 per success)
attempt 3: success 14%  expected $438/attempt  ($3,002 per success)
```

Both components decline monotonically. Note the honest correction: an
earlier draft claimed a −79% single-job haul cut, but that number was an
artifact of the naive loading order. With rational value-first loading, a
*first* job against a sleepy target pays ~$3.8k when it succeeds
(~$0.8k expected) — the anti-ATM pricing comes from the decline curve,
the pattern Case (~54 across a ten-job spree), hardening, and injuries,
not from making the first job worthless. Ledger/sabotage — leverage and
tempo plays, not loot — are intentionally unchanged. The 150-seed sweep
is unmoved (market 62%, greedy 58%, crime-heavy 21%): the pricing is
contained to raids.

## Still open (carried to the next design pass)

- The midgame still resolves around day 12–15; the payoff-triggered
  Act I fork (leave the trade / expand with Carmine / press rivals /
  cash out) is the agreed direction.
- Heat still under-binds relative to the Case; needs local teeth without
  becoming a second global meter.
- Event responsiveness beyond payday/heat-wave is now *provable* with the
  market bot (it reads the news); a dedicated study should measure whether
  exploiting port-seizure/concert pricing separates skilled play.
- Founder-staff attrition remains high across strategies; resignation
  warnings now precede departures, but retention still needs a reason to
  spend money on people.
