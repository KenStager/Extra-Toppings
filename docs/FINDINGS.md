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

## Still open (carried to the next design pass)

- Raids remain under-priced (target hardening, pattern evidence, carry
  limits, single-use ledger leverage are designed but deferred by scope).
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
