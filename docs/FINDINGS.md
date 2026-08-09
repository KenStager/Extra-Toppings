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

## Round 5 — issue #4 closed: the noise-timeout regression (P0 opens)

The raid regression logged in issue #4 during the PR #3 review is fixed,
as the first item of the Act I fork's P0 phase (the fork design itself is
`docs/ACT1_FORK_DESIGN.md`, merged as the decision record via PR #6):

- **Early timeouts no longer pay.** `run_raid`'s `noise >= 1.0` branch
  broke the room loop without marking the job failed, so a crew caught by
  the lights mid-building still received the objective. Timing out with
  rooms still ahead is now a failed extraction — abort consequences
  (+1 alertness, heat, relation), no objective, no job counted, no
  pattern premium. Crossing the threshold in the *final* room remains a
  loud success: the clean-exit pricing (+5 witness Case) covers it, so
  the noisy-completion path is not dead code.
- **The premium display matches the premium.** `:.0f` rendered the 4.5
  pattern premium as "~4" (Python rounds ties to even); the planning
  warning and the incurred announcement now print the exact figure.
- Regression tests drive the actual player path (`TestNoiseTimeout`,
  `TestPatternDisplayHonesty`: scripted room-loop play, all-rush crews,
  seed scans). All three fail on the pre-fix engine — verified by
  reverting the fix and rerunning.

Measured impact at 2,000 trials (round-4 protocol):

```
attempt 1: success 19%  expected $752/attempt  ($3,827 per success)
attempt 2: success 16%  expected $556/attempt  ($3,309 per success)
attempt 3: success 13%  expected $413/attempt  ($3,037 per success)
```

This lands exactly on the curve the issue #4 review predicted for the fix
($752 → $556 → $413) and supersedes round 4's $781 → $597 → $438, which
is now known to have been inflated by bug-awarded timeouts — roughly one
to two points of "success" per attempt were crews the lights had already
caught. The 150-seed sweep is unmoved: market 62% (Case μ26, rep 20),
greedy 58%, crime-heavy 21%, cautious 33%, pizza-first 0%.

(Tooling note: ruff 0.15 flags E702 on the experiment runner's one-line
dispatch statements; the dispatcher was reshaped with no behavior
change.)

## Round 6 — P0 foundation: the engine rebuilt under a proof of stillness

The Act I fork's P0 phase (design: `docs/ACT1_FORK_DESIGN.md` §2.3, §5)
rebuilt the engine's foundations with a standing proof that Act I did not
move:

- **Equivalence harness** (`python3 -m analysis.equivalence generate|check`):
  before any refactor landed, 150 seeds × 2 bot profiles (random chaos
  bot, greedy strategy bot) were recorded nightly from the untouched
  engine into `analysis/golden_act1.json` — a legacy projection of state
  in the save-v2 shape, digests of the four shared persistent RNG
  streams, the bot's total prompt count, and the ending.
- **The rebuild**: `case_flags` → typed `Evidence` records (witness /
  paper / physical / pattern / legacy) with `state.case` derived as
  their clamped sum; arrest latches inside `add_case` the moment the sum
  reaches 100, irrevocably; `State.shop`/`shop_stash` → compat
  properties over a `State.shops` collection (a list of one until the
  Partner branch); save v3 with backward migration of v2 payloads
  (annotation records + one carrier record reproduce the scalar Case
  exactly); three fork-era RNG streams (`sitdown`/`brokers`/`war`)
  reserved and provably undrawn.
- **Result: 300/300 recorded runs identical** after the rebuild, on all
  three surfaces, plus every schema-semantics test in
  `tests/test_p0_foundation.py` (92 tests total, ruff/mypy clean).
- One deliberate deviation from the design's letter: routine 0.5-Case
  ticks are stored as individual records rather than one rolling record.
  Storage-level aggregation would reorder floating-point addition and
  break bit-exact identity with the old running total; the future
  evidence-ledger UI aggregates them at display time instead.

The gate holds for everything that follows: no fork content lands unless
`analysis.equivalence check` stays at 300/300 for pre-fork play.

### Round 6 correction (re-review)

Independent re-review on Python 3.12 falsified the first 300/300 claim:
`state.case` used built-in `sum()`, and 3.12 moved float summation to
compensated (Neumaier) summation — 15 of 300 runs diverged from the
sequential goldens (a fold of 61.50000000000001 sums compensated to
61.5). Fixed with an explicit left-to-right fold, regression-tested with
a concrete divergent sequence, and the gate now reproduces at **300/300
on Python 3.11, 3.12 and 3.13**. The same pass hardened the rest of the
gate per review:

- **Action replay is a decision trace, not a prompt count.** The golden
  record now digests every interaction — menu prompt, options and chosen
  index; amount prompt, bounds, default and answer; confirmation and
  result, in order. Two runs can no longer pass by answering the same
  *number* of prompts. Goldens were regenerated from the pristine
  pre-refactor engine (a worktree at `3d79d17` with only the harness and
  the observation hook injected).
- **Evidence taxonomy corrected at the remediation boundary.** The
  solo-driver route arrest is classified *physical*: the record is
  dominated by seizure and arrest-report evidence, which the design
  declares permanently immune — a witness classification would have let
  a future settlement soften it. Witness records now carry stable
  `Employee.key` sources instead of display names.
- **Arrest precedence matches §2.5.** The latch now *overrides* a
  simultaneous lower-priority ending rather than deferring to it — Case
  100 beats a success set moments earlier, tested.
- **Save v3 finished rather than half-final.** Typed `BranchState`
  (fields per the design's branch specs) persists on `State`, and
  demand / delivery pool / legitimate revenue moved into `Shop` — the
  second shop and the fork arrive as data, not as another migration.

## Round 7 — the fork learns to speak: §2.1 telegraphs, transcript only

The pre-payoff telegraph channels of the fork design
(`docs/ACT1_FORK_DESIGN.md` §2.1) are in — the last item of the §7 P0
scope. The player now learns the rules of the sit-down table while the
debt still exists, through four channels plus one pre-action warning,
and the engine provably did not move underneath them:

- **Payment remarks** (`_pay_debt`): every non-trivial partial payment
  (≥ $500) draws a line from Carmine keyed to trajectory — big
  (≥ START_DEBT/4) × early (day ≤ 15) quadrants, deterministic in day
  and amount because the channel is not allowed an RNG draw. Big-and-
  early carries the design's canonical line ("A man who pays early is a
  man worth backing. We should talk when this is done.").
- **Calendar warnings**: with the debt alive, day 20 carries the
  buyer-losing-interest warning (attributed to Lena when a connected
  employee is on staff, to "a regular" otherwise — the `rumor_sheet`
  convention) and day 24 turns explicit: settle by tomorrow night or
  the table will be empty. Unconditional on their days; world facts.
- **Case-60 warning**: prints the morning after the Case first reaches
  60 with the debt alive. Once-only with **no stored flag** — evidence
  records carry their day, so "first prefix-sum ≥ 60 landed on day D"
  is derived on the fly (same left-to-right fold as `State.case`, so
  "crossed" agrees bit-for-bit with the meter) and the line prints only
  when `day == D + 1`. Nothing persists, so saves and traces are
  untouched.
- **Carmine's ledger clause**: the morning debt line gains "…and he has
  opinions about what comes after" once the debt is below half of
  START_DEBT.
- **Same-night threshold warning** (`_launder`): when payoff is in
  reach (on-hand cash ≥ debt) and an over-ceiling wash *could* push the
  Case past a gate (60/70/85 — max evidence `min(20, over/400)` from
  washing everything), a warning prints BEFORE the amount prompt. This
  is §2.7's second arm of the Case-gate disjunction: a gate may slam
  the same night it is crossed only if the act that crossed it warned
  first.

Constraint and proof: golden decision traces digest every
menu/ask_int/confirm prompt string verbatim, so all telegraph lines are
`say`/`bullet` output only — no new prompts, no edits to existing
prompt strings (the same-night warning is a printed line *before* the
launder prompt, not a change to it), no state mutation, no RNG draw.
`analysis.equivalence check` reproduces **300/300 on Python 3.11, 3.12
and 3.13** with the lines in place. 19 transcript tests
(`tests/test_telegraphs.py`) drive the actual `morning()`/`night()`
phase code with scripted consoles and pin every channel's trigger, its
negative space (wrong day, settled debt, cold case, wash that fits the
books), and the before-the-prompt ordering of the same-night warning.
Full suite 114 tests green on 3.11 and 3.12; ruff (0.15.x pin) and mypy
clean. No sweep rerun: by the equivalence gate the studies' inputs are
bit-identical, so round 6's headline numbers stand unchanged.

### Round 7 correction (review)

Independent review of the first telegraph pass found one blocking
coverage gap and one specification seam; both are fixed, and the design
document carries the corrections as revision 3 (§8).

- **Same-night Case protection covered only laundering.** The reviewer
  reproduced, through the real route and night phases: Case 55, debt
  $1,000 with payoff cash on hand, a full-cargo ride-along, a police
  bust (+8, +6 resistance, +6 owner-in-vehicle, +0.3/unit) to Case 81,
  payoff that night — Carmine's Partner withheld tomorrow with neither
  §2.7 warning arm satisfied. Fixed by generalizing the pre-action
  surface to every evidence-capable player act committed while payoff
  is in reach (`State.payoff_in_reach`: debt alive, on-hand ≥ debt):
  the wash keeps its exact arithmetic; contraband routes and raids warn
  at plan time unconditionally in the window (their accrual depends on
  in-act outcomes, so the superset is by construction, and both plans
  can still be cancelled); firing an aware employee warns before the
  selection menu exactly when the Case is within its fixed 6 points of
  a gate. The reviewer's exact scenario is now a regression driven
  through `plan_route` → `service` → `night` with a seed scan to an
  actual gate-crossing bust plus same-night payoff
  (`TestRouteCrossingThenPayoff`), and the three new surfaces were
  proven to fail on the pre-fix engine (3 failures at 4278f51).
- **Post-payoff accrual could re-shape the table.** `rival_phase` and
  `_law_phase` run after `_pay_debt` but before the sit-down morning,
  so the world's own dice could close a chair after the payoff decision
  with no telegraph possible. Resolved on paper for P1 (no sit-down
  code exists yet): the design now specifies an **eligibility
  snapshot** — chairs freeze at the moment the debt reaches zero;
  later evidence still counts toward the Case and arrest at 100 still
  outranks the fork, but the table cannot change retroactively (§2.1
  rev. 3). World events remain the named residue: non-acts get no
  pre-action warning, and the §2.7 criterion now carries the explicit
  third arm (snapshot + the scene naming the closing record) instead of
  claiming coverage it cannot have.
- **"At least two days" was arithmetically false at the boundary.**
  Payoff day 21 → R = 9 withholds the Partner chair; the day-20 warning
  preceded it by one calendar day, and the tests required silence on
  day 19. The criterion was the error, not the beats: restated as "the
  warning morning strictly precedes the payoff day — at least two
  playable decision days including the warning day," which day 20
  satisfies at the Partner (21) and War (23) boundaries and day 24 at
  the no-sit-down cliff (26). Encoded as
  `TestCalendarCriterionArithmetic`, including the reviewer's day-21
  case.

After the correction: 123 tests green on 3.11 and 3.12, ruff/mypy
clean, equivalence re-verified at **300/300 on 3.11, 3.12 and 3.13** —
the broadened warnings are still say-lines only; no prompt, state or
RNG surface moved.

### Round 7 correction 2 (re-review)

The re-review confirmed the ride-along regression and the calendar
correction, and found one new blocker plus one boundary the first
correction left uncovered. Design revision 4 (§8) records all of it.

- **The payment-time snapshot rewarded action ordering.** Rev. 3 froze
  chair eligibility inside `_pay_debt` — and explicitly protected a
  post-payment over-wash. The reviewer reproduced the exploit through
  the real night ordering: Case 65 → pay the final $1,000 → $10,000
  over-wash → Case 85, debt zero, no arrest, both Case-gated chairs
  preserved. The snapshot moves to **lock-up**: frozen when the player
  leaves the settle-accounts menu, after every discretionary account
  action, immediately before the rival and law phases — every voluntary
  act counts, only the world's after-hours dice are excluded. Two
  paired snapshot-integrity acceptance tests are now specified for P1
  (§2.7): pay → over-wash → lock up closes the chairs at 85; pay → lock
  up at 65 → forced world evidence to 85 leaves the offers standing,
  arrest at 100 excepted. Paper-only, like the snapshot itself — the
  binding tests land with the sit-down.
- **A route that funds the payoff warned nobody.** With on-hand cash
  short of the debt, the "one last run" that earns the final payoff
  money fell outside the on-hand-only window — a player act with no
  warning under any §2.7 arm. The route surface's reach test now counts
  tonight's plausible take: on-hand + 2 × demand × gourmet ticket +
  Σ units × district price × 1.5 ≥ debt, each term a supremum of its
  runtime counterpart (sale price tops out at a 1.2 offer roll × 1.25
  haggle; orders never exceed demand; no ticket beats gourmet; the
  doubling absorbs a morning policy change). Overestimating only warns
  early. Regression: cash $5, debt $2,000, twenty units aboard —
  `payoff_in_reach` false, warning fires anyway.
- **Raids re-measure at execution.** Service revenue can put payoff in
  reach between scheduling and the job, so `night()` rechecks
  immediately before `run_raid`; the plan records whether it already
  warned, so the line prints once. Regression drives the real morning
  and night: debt out of reach at planning, takings arrive, the warning
  appears before the NIGHT JOB header; and a plan-time warning is not
  repeated at execution. Both new positive regressions fail on the
  rev. 3 engine (2 failures at 06dea64).
- Wording aligned with the engine's transactional-planning semantics:
  plans are intentions committed at service, so the criterion reads
  "planned or taken," not "committed at plan time."

After correction 2: 126 tests green on 3.11 and 3.12, ruff/mypy clean,
equivalence re-verified at **300/300 on 3.11, 3.12 and 3.13**. The raid
plan dict gained a transient `table_warned` key — never saved, never
digested; prompts, state and RNG surfaces are untouched.

## Round 8 (opens with P1a) — the fork's skeleton, proven inert

P1 is split into two reviewable PRs (design §7 rev. 5): P1a is the
foundation — everything the Quiet Sale will stand on, landed and gated
before any branch mechanics exist. This round's body (the escrow
studies) arrives with P1b; what P1a contributes is the machinery and
its two gates.

- **The replay decision, made before the code.** The stand-pat identity
  contradiction (the sit-down is made of prompts, so a stand-pat run
  cannot both answer the scene and match a fork-off decision log
  byte-for-byte) is resolved by the rev. 5 two-trace contract:
  gameplay prompts keep their exact event shape in the game trace —
  `golden_act1.json` untouched — while sit-down decisions ride a
  namespaced `scene_menu` channel into a separate scene trace. The
  paired gate (`analysis.equivalence standpat`) demands the flag-on
  stand-pat game trace equal the flag-off trace **event for event, full
  lists compared**, plus exact nightly projection, shared streams,
  ending, undrawn fork streams, and a scene trace holding exactly one
  stand-pat selection and one confirmation. A subsequence comparison
  was rejected: it tolerates missing, duplicated or reordered gameplay
  prompts.
- **The flag is an argument, not an ambient.** Immutable
  `GameConfig(fork_enabled, enabled_branches)` passed explicitly; only
  the CLI reads the environment. It gates entry (the lock-up snapshot
  is captured only while on) and never continuation — a save with a
  pending snapshot or act 2 resumes correctly whatever the launch
  flags say.
- **The snapshot stores three primitives** (payoff day, Case at
  lock-up, evidence count at lock-up); R, verdicts, withholding prose
  and the gate-crossing record are derived by a pure evaluator — no
  second source of truth. Save-layer: additive, no version bump, older
  v3 payloads load None. The rev. 4 ordering exploit and the
  world-dice exclusion are both regression-tested through the real
  night phase.
- **The scene draws zero RNG and consumes zero bot decision RNG** —
  bots answer scene menus with a deterministic last-option handler
  (every scene menu keeps its progressing choice last), asserted by
  comparing bot RNG state before and after a real scene. All four
  chairs render with their true gate verdicts; unimplemented chairs
  carry a development-build marker outside the fiction and cannot be
  selected — never silently converted to stand-pat. An enabled branch
  without a commit path fails loudly.
- **BranchState grew constructors and ValueError validation** (dead
  fields at defaults, stand-pat means no BranchState, required fields
  per branch, mixed payloads refused) — enforced at branch transition
  and save-load, before any branch code exists to get it wrong.

Verification: 164 tests green on 3.11 and 3.12 (38 new in
`tests/test_p1_foundation.py`); ruff/mypy clean; flag-off golden gate
**300/300 on 3.11, 3.12 and 3.13** against the untouched goldens; the
new paired stand-pat gate **300/300 runs identical** (150 seeds × both
bot profiles, flag-on vs flag-off), with the sit-downs that fired held
to the exact scene contract.

### Round 8 correction (review)

Review of the P1a foundation falsified the paired gate's central claim
and found three more foundation defects; all four are fixed at the
root, recorded as design revision 6 (§8).

- **The paired gate proved equivalence, not existence.** The reviewer
  disabled `sitdown.due()` on a table-reaching run (greedy, seed 1) and
  every checked surface still passed — `_scene_contract([])` accepted
  the missing scene, and the "exact" checker accepted arbitrary prompt
  and option text. The gate now derives whether a scene is OWED from
  the flag-off nightly timeline alone (debt_paid_day, day, ending —
  world facts, no fork code) and requires expected == observed pair by
  pair; a fired scene must equal a frozen, versioned literal schema
  (namespace, prompt, complete ordered options, answer — hardcoded in
  the harness, never imported from the scene module, so drift fails
  like a drifted engine fails the goldens). Mutation regressions pin
  it: the disabled-due probe now fails the gate while every equivalence
  surface still matches, and missing/extra/reordered events and changed
  prompt/option/answer/namespace each fail a table-reaching pair.
  The ensemble independently reproduces **82 expected / 82 held**.
- **Frozen and live Case were conflated.** A snapshot at 20 with the
  live file at 32 rendered "20/100" and never mentioned 32 — the
  disagreement line fired only when chair availability changed. One
  canonical `SitdownView` now carries frozen Case + frozen verdicts +
  live Case + live band; every difference renders (20→32 with "the
  chairs were set at closing time"; 65→72 with "the offers stand"), and
  chairs still open at Case ≥ 85 are marked visibly dangerous in-scene.
  Blockers are structured (calendar/case/None + threshold + closing
  record) with calendar-first precedence pinned.
- **Scripted scene input failed open.** An empty ScriptedConsole chose
  the last option twice and irrevocably committed stand-pat — the
  documented safe-exhaustion contract inverted at the one place choices
  are permanent. `scene_menu` on ScriptedConsole now demands an
  explicit answer and raises `ScriptExhausted` before any mutation;
  pinned before chair selection and between selection and
  confirmation, with reload/replay verified. Progress-last remains the
  deterministic-bot policy only.
- **GameConfig immutability was cosmetic.** A caller-held mutable set
  could grow `enabled_branches` after construction. `__post_init__` now
  normalizes to a frozenset and rejects unknown branch ids, with branch
  identifiers sourced from one canonical definition
  (`models.BRANCH_ORDER`) shared by config, validation and the scene.

After the correction: 179 tests green on 3.11 and 3.12 (15 new);
ruff/mypy clean; flag-off golden 300/300 and paired stand-pat 300/300
with sit-downs expected 82 / held 82 on Python 3.11, 3.12 and 3.13.

### Round 8 correction 2 (the rendering boundary)

Re-review accepted the existence oracle, the exact schema, fail-closed
scripts, config immutability, canonical branch ids and calendar-first
precedence — and found the canonical-view fix incomplete at its
rendering boundary: `run_scene` still derived policy outside the view.
Three concrete symptoms, all confirmed: danger warnings keyed to the
frozen Case (frozen 65 → live 90 said "offers stand" but showed neither
the Straight nor the War warning); failed gates never stated their math
in-scene (a Case-72 Partner rejection never said "below 70", a day-21
rejection never said "needs ten; nine remain"); and `build_view`
reimplemented the Case fold that `State.case` owns — two copies of the
exact arithmetic the round-6 Python 3.12 failure came from.

Cut as one seam (design §8, rev. 6 completion): a single
`fold_case(evidence)` primitive in models.py is now the only Case
arithmetic, called by `State.case` and the view's live ledger alike —
bit-identity by construction, regression-tested on the 3.12-divergent
sequence (61.50000000000001 sequential vs 61.5 compensated) plus a
function-identity assertion. `SitdownView` is complete — frozen
eligibility, live risk, offers_would_change, and structured gate facts
(kind, requirement, actual, the chair's gate, reason, closing record) —
and the renderer consumes it exclusively: no re-evaluation, no gate
tables. Eligibility keys to the frozen Case only; present danger to the
live Case only. Failed gates render their math in player language.
All four review cases pinned, and proven failing on the pre-fix engine
(2 failures + 2 errors at 790ca40). The scene's prompts and options are
untouched, so scene schema v1 and the goldens both stand.

After correction 2: 183 tests green on 3.11 and 3.12; ruff/mypy clean;
flag-off golden 300/300 and paired stand-pat 300/300 with sit-downs
expected 82 / held 82 (schema v1) on Python 3.11, 3.12 and 3.13.

### Round 8 body — P1b: the Quiet Sale, measured

The escrow week is in (`extra_toppings/escrow.py` + the scene commit
path), behind the same flag, drawing the `brokers` stream only after
the chair is taken. All §2.7 numbers below reproduce via
`python3 -m analysis.experiments fork` (150 seeds; three escrow bots —
careful, sloppy-learner, and the keeps-stash ablation — built as
minimal policies over the greedy bot).

| Criterion | Bar | Measured | Verdict |
| --- | --- | --- | --- |
| Reachability (unmodified market bot, open sit-down) | ≥ 55% | 85/150 = 57% | pass |
| Crash-freedom (forced-sale chaos) | 150/150 | 150/150 | pass |
| Careful close rate (of entered) | ≥ 70% | 76/82 = 93% | pass |
| Closes exactly at fork+4 or reverts | always | 0 off-schedule | pass |
| Ablation drop (keeps-stash) | ≥ 20 pts | 93% → 10% (83 pts) | pass |
| Valuation, careful−sloppy median | ≥ $1,000 | $2,179 | pass |
| Valuation, tier flips | ≥ 40% | 10/52 = **19%** | **miss** |

The miss is a finding, not a tuning failure. Of the 52 matched closes,
31 are **cash-locked at kept-the-trade in both runs**: laundering is
off all week by design, so more than $200 of unlaundered cash at close
was decided before the fork — no escrow-week policy can flip those
tiers. Among the 21 unlocked pairs, flips run 10/21 = 48%, over the
bar. The criterion needs a review ruling (condition on
tier-controllable seeds, extend "careful" into pre-fork cash hygiene,
or give escrow a dirty-cash outlet); the design doc records the
question (§8, P1b notes).

Two mechanics findings from the same runs, reported in the deviation
record:

- **Without a burn action the branch was unplayable.** First contact:
  0% closes — every entered run collapsed on walk-through incidents,
  because a stash-heavy month cannot leave through a 24-bulk wagon
  before two incidents land. §3.4's "burn it for the clean close"
  became a real diligence-morning choice; careful closes went 0% →
  93% while the keeps-stash ablation stayed at 10% — the pressure is
  real, and now so is the counterplay.
- **The clean close is genuinely rare for a criminal month** — the
  careful bot's tiers split 49 kept-trade / 23 fire-sale / 4 modest,
  and *sold well* was never reached by any bot. That is the branch's
  thesis (the clean number must be EARNED by the month, not the week);
  whether it is fun is a human-play question for seeds 24/39/8, noted
  for the P4 pass.

Verification: 209 tests green on 3.11 and 3.12 (26 new in
`tests/test_quiet_sale.py`, driving the real scene, mornings, service
walk-throughs, night rules and closing); ruff/mypy clean; flag-off
golden 300/300 AND paired stand-pat 300/300 (expected 82 / held 82,
schema v1) on 3.11, 3.12 and 3.13 with all P1b code in the tree — the
fork stays provably inert unless entered.

### Round 8 correction 3 (review of P1b — design rev. 7)

Review ruled the tier-flip miss a **missing player verb**, not a
denominator problem, and found four further defects; all corrected,
with the flip bar itself still open — for a new, fully isolated reason.

- **The disposal verb exists now.** One primitive
  (`escrow.incinerate`) burns cash and contraband alike — destruction,
  never conversion. The night account menu is branch-aware (disposal
  replaces laundering during escrow instead of refusing after
  selection); warehouse cash must be trucked back before it can burn;
  the card shows the $200 tolerance and projected classification every
  morning. Effect measured: cash-locked matched pairs went **31 → 0**,
  kept-the-trade all but vanished from careful closes, and a clean
  close is reachable by burning (tested).
- **One valuation view.** `MarkBreakdown` replaced the card's two
  arithmetics (displayed rounded inputs vs computed truncated ones —
  the rep-24.9/Case-61.5 repro). Explicit rounding policy, renderer
  consumes the view only, displayed dollars sum exactly to the mark.
- **The closing is transactional.** The reviewer's Case-84.9/rep-5/
  $0-clean repro (−$600 cash, negative recorded mark) is a regression:
  humane severance appears on the sheet only when settlement plus
  clean funds it; nothing goes negative; `escrow_mark` stays the
  buyer's price; `severance_paid` persists and the epilogue
  acknowledges paid and unpaid. The transcript-only deviation is
  withdrawn.
- **Safe fallbacks restored.** The walk-in question's burn option
  moved off the last position (an exhausted script had burned seven
  oregano); every new escrow prompt is regression-pinned under an
  exhausted script with no assets destroyed.
- **Reachability measured completely, criterion revised on paper.**
  Full tables 74/85 = 87% of open sit-downs (reviewer: 88.2% at
  1,000 seeds), every absence calendar-gated, none case-gated; median
  payoff day 11 and 75th-percentile day 16 both seat full tables;
  boundary chair sets match the §2.1 table exactly (day 21 `+-++`,
  day 23 `+--+`, day 26 `----`). The flat 90% bar is recorded as
  falsified and criterion 2 now tests its thesis (§2.7 rev. 7).

**The flip bar, after the verb (150 seeds, market-bot-based escrow
bots — the "smart bot" the criterion names):** careful closes 93%,
ablation drop 85 points, valuation median mark delta $1,396 ≥ $1,000 —
and tier flips **17/60 = 28%** against the unconditioned 40% bar.
The cash-lock explanation is exhausted (0 locked pairs); the tier
population now straddles the boundary (careful: 40 fire / 39 modest);
what remains is arithmetic: a ~$1,400 escrow-week lever flips a
$10,000-wide tier boundary only for runs within a lever's width of it.
Supplying the verb moved flips 19% → 28% (18% → 28% after the
smart-bot rebase); the residual gap is a property of §2.4.4's declared
numbers — incident repricing depth (−10..−25%), the illustrative mark
formula's scale, and the $10k/$25k tier spacing — not of bot policy.
Raising any of the three is a design-constant decision recorded for
review, not taken unilaterally.

After correction 3: 223 tests green on 3.11 and 3.12 (14 new);
ruff/mypy clean; flag-off golden 300/300 and paired stand-pat 300/300
(expected 82 / held 82, schema v1) on 3.11, 3.12 and 3.13.

### Round 8 correction 4 (final review — the constants ruling, and green)

Review ruled on the §2.4.4 constants and named three last seams; the
design records it as revision 8, on paper before implementation.

- **The constants ruling.** Mark formula and $10k/$25k tiers stay;
  first-incident repricing rises from −10..−25% to **−20..−35%, drawn
  in whole percentage points** (the displayed rate is thereby exact);
  the second incident still collapses. The rationale is the review's:
  this lever prices the behavior under test — moving tier boundaries
  would relabel identical outcomes, and scaling the mark would revalue
  the chair against future branches.
- **Negative subtotals floor before deductions.** The rep-5/Case-84.9/
  war-armed/incident card had rendered "--$24"/"--$15" — percentage
  deductions against a negative subtotal becoming credits. The raw
  subtotal now clamps at zero first, the floor is carried in the
  MarkBreakdown and said out loud ("the mark floors at $0"), war and
  incident terms are provably non-negative, and the exact combination
  is pinned.
- **Severance is a real outcome, not an amount.** $0 had collapsed
  deliberate refusal, unaffordability, and an empty roster — a
  crewless close still eulogized "the crew." The closing persists
  pending/paid/declined/unaffordable/not_applicable with the amount
  and closing headcount; the epilogue drives from the outcome (four
  distinct texts, and silence for a crew that never was); every state
  round-trips; unknown outcomes are rejected at validation.
- **The careful policy keeps the permitted $200** (burn =
  dirty − tolerance), and the clean-close regression was repaired to
  land exactly at fork+4 with no manual clock-winding.

**The full §2.7 battery now passes, matching the reviewer's
counterfactual to the digit** (150 seeds): reachability 57% with full
tables at the median (day 11) and Q3 (day 16) payoff states and exact
boundary chair sets; crash-freedom 150/150; careful closes 79/85 = 93%,
0 off-schedule; ablation drop 84 points; valuation median mark delta
**$2,370**; tier flips **27/60 = 45%** against the unconditioned 40%
bar. The 500-seed confirmation: **81/188 = 43% flips, median mark
delta $2,444, careful closes 261 (93%), sloppy 189, ablation drop 85
points, 0 off-schedule, full tables at median day 10 and Q3 day 16,
crash-free 500/500** — against the reviewer's independent
counterfactual of 81/188 = 43.1% and $2,445: the same runs, reproduced
across implementations. Identity gates: flag-off golden 300/300 and
paired stand-pat 300/300 (expected 82 / held 82, schema v1) on 3.11,
3.12 and 3.13. 228 tests green.

### Round 8 correction 5 (re-review — two model contracts)

Re-review reproduced every number and found the rev. 8 implementation
exact in behavior but not in model; both corrections landed at the
root (design §8, revision 8 completion).

- **Integer points are the canonical unit.** `cut_points / 100` had
  re-introduced binary float at storage: real broker seeds 6 and 17
  stored 28 as 28.000000000000004 and 29 as 28.999999999999996 — and
  the exactness regression passed only because its one draw happened
  to be representable. `BranchState.escrow_discount_pct` now stores
  the integer; the division happens once inside the dollar-rounded
  term; pre-correction v3 payloads migrate on load; and all 16
  possible draws (20–35) are pinned with plain integer equality — no
  round(), no isclose(), through save round-trips and the rendered
  card alike.
- **The severance taxonomy is now a machine, not a label.** The review
  exhibited five contradictory rows the validator accepted (paid with
  no amount, paid with no crew, declined with money, not_applicable
  with a crew, pending with a headcount) — and a paid/None/2 save
  loaded silently into an epilogue that said nothing. The complete
  state machine binds at transition and load: pending carries nothing
  and never survives a sold run (the terminal invariant reads the
  run's game_over); paid means exactly rate × positive headcount;
  declined/unaffordable mean a positive headcount and zero paid;
  not_applicable means zero and zero. One canonical rate
  (`models.SEVERANCE_PER_HEAD`) prices validation, the closing sheet
  and the epilogue; the closing applies its outcome triple through one
  validated transition. All five exhibited rows are pinned as
  refusals, both directly and through doctored saves.

After correction 5: 235 tests green on 3.11 and 3.12 (7 new, 6 failing
on the pre-fix engine); ruff/mypy clean; flag-off golden 300/300 and
paired stand-pat 300/300 (expected 82 / held 82, schema v1) on 3.11,
3.12 and 3.13; both ensembles reproduce the correction-4 numbers
bit-for-bit — 150 seeds: flips 27/60 = 45%, median mark delta $2,370;
500 seeds: flips 81/188 = 43%, median $2,444 — the unit change is
behavior-preserving, now provably so at the model.

### Round 8 correction 6 (final re-review — the persistence half)

The severance machine was accepted; the canonical-percentage contract
was enforced only on the producer path. A doctored v3 payload accepted
0.28 back into the integer field, a fractional 29.5, a −10 that raised
the mark as a $1,000 credit, and an out-of-domain 200 — the original
representation defect could return through save-load. Fixed at the
model boundary (design §8, rev. 8 completion, item 3):

- `_validate_escrow_pricing` requires an actual integer (`type(x) is
  int`, so bools are refused too) in the ruled domain, tied to the
  incident count: zero incidents → zero discount; one incident → a
  permitted 20–35; two incidents cannot remain in an active sale.
- The repricing domain moved to its one canonical home
  (`models.REPRICE_MIN_PCT`/`MAX_PCT`); the escrow draw and the
  validator share it.
- Legacy float migration is the only conversion site, and its result
  passes through the same validator.
- The sole surviving first-incident discount is assigned, not
  accumulated.
- Malformed payloads (0.28, 29.5, −10, 200, True) and relationship
  violations (a repricing with no incident; two incidents active) are
  pinned through `state_from_dict`. Two tests that had set
  out-of-design-range values directly (15, 18) were corrected to legal
  states — the validator would now have caught them, which is the
  point.

After correction 6: 237 tests green on 3.11 and 3.12; ruff/mypy clean;
flag-off golden 300/300 and paired stand-pat 300/300 (expected 82 /
held 82, schema v1) on 3.11, 3.12 and 3.13; both ensembles unchanged —
150 seeds: flips 27/60 = 45%, median $2,370; 500 seeds: 81/188 = 43%,
median $2,444.

## Round 9 — P2: the Straight Path, and the file that had nothing to fall from

The clean-exit branch is in (`extra_toppings/straight.py` +
`evidence.py` + the scene commit path), behind the same flag, drawing
only its reserved dice: disposal runs ride the routes stream draw for
draw, temptation arrival is a per-day world channel, and the meeting
dice draw the new persistent `straight` stream — first drawn only
after the chair is taken (rev. 9 item 1, flagged for ruling). The
remediation machinery is the §2.3 letter under the rev. 9 arithmetic:
counsel contests flagged paper first and the routine hum as the one
rolling record; settlements halve a witness's records permanently and
settle a current witness OUT with no firing record; retention keeps a
content current witness's records dormant for free, reversibly; the
25-point cap binds the paid verbs and truncates out loud; the
institutional-suspicion record tops up in place by exactly the
difference, and displayed Case ≡ the visible ledger every night. The
shared prefix iterator the fold_case docstring owed since rev. 6 is
real (`models.case_prefix`), consumed by the fold, the Case-60
telegraph and the gate-crossing record.

All numbers below reproduce via `python3 -m analysis.experiments fork`
(150 seeds; StraightBot and its no-remediation ablation over the
market bot, the criterion's named baseline) and `--seeds 500`.

| Criterion (straight rows) | Bar | Measured | Verdict |
| --- | --- | --- | --- |
| Reachability (unchanged) | ≥ 55% | 85/150 = 57% | pass |
| Crash-freedom (forced-straight chaos) | 150/150 | 150/150 | pass |
| Covert revenue share after fork+2 | < 5% | $0 = 0.0% | pass |
| Earned-exit band | 25–70% | 40/85 = 47% | pass |
| Ledger transparency (nightly, both bots) | 0 bad | 0 | pass |
| Suspicion floor (once paid remediation exists) | never < 10 | 0 bad | pass |
| Median ΔCase fork→end | ≤ −5 | **+4.0** | **miss** |
| Case strictly below fork-day | ≥ 60% | 9/85 = **11%** | **miss** |
| Ablation drop (never settles / no counsel) | ≥ 20 pts | **0** | **miss** |
| Quiet Sale battery (all P2 code in tree) | round-8 rows | identical | pass |

The 500-seed confirmation: entered 280/500 (56%), earned exits 42%,
ΔCase median +4.5, strictly below 11%, covert 0.0%, ablation −1
point, crash-free 1000/1000 across both chaos fleets; the escrow rows
reproduce round 8 exactly (careful 93%, ablation 85 points, valuation
median $2,444, flips 81/188 = 43%).

**The three misses are one finding, and it is structural.** The
decomposition (printed by the harness, per row):

- **The file arrives cold.** Median lock-up Case at entry: 6.0 (150
  seeds), 5.5 (500) — BELOW the 10-point institutional floor, where
  the design says the file cannot fall at all. Only 16/85 entries
  (46/280) reach lock-up ≥ 20. The §3.1 exemplar walks in at Case 31;
  the named smart-bot baseline pays Carmine by day 10–11 and brings
  almost nothing to redeem. A bar demanding −5 from a median entry of
  6 is arithmetically unreachable regardless of mechanics.
- **The settlement verb has no lawful target the entire study.** The
  market bot reads nobody in, so no witness record it accrues carries
  an Employee source — settlements measured: 0 in 85 entries, 0 in
  280. What the siege books post-fork (median +4.6/+4.9) is largely
  the informant's tip and the patrolman's memory — witness-kind
  records with NO source, structurally as immune as physical. Whether
  those two P0-era call sites are mis-kinded is now a live design
  question (§8 P2 notes, item 3).
- **The mechanism itself works, measured three ways.** Matched-seed
  counterfactual: remediation leaves the file lower in 55/85 = 65%
  (172/280 = 61%) of paired entries, median −1.0. The dirty-month
  diagnostic (crime-heavy Act I, identical branch policy — the §3.1
  entry profile): settlements 39 (165 at 500 seeds), remediated
  ΔCase +3.2 against +12.5 unremediated — a nine-point pull — with
  the lockup ≥ 20 population at median −0.1 (−0.9 at 500) and 13/25
  (53/92) strictly below, against 0 without remediation; its
  ablation drop is 13–14 points. Every diagnostic is labeled in the
  harness and none conditions a bar.

So: not the bots (the policy exercises every verb the baseline's
month gives it), not the mechanics (the counterfactuals separate
cleanly), but a criterion whose premise — a redemption-shaped entry —
the named baseline almost never produces. Three resolutions are on
the table for review, none taken unilaterally: condition or restate
the bar (e.g. the matched-seed counterfactual IS the falling-Case
claim, unconditioned); re-base the straight rows on the dirty-month
profile the branch was written for; or strengthen the remediation
constants against the siege — a §6.3 constants decision that needs
its ruling recorded first. The source-less-witness taxonomy question
rides along.

**Consequence honored:** §7 lifts the Quiet Sale's flag when THIS
gate passes. It has not passed; no flag moved. The fork still
reaches no player until the ruling lands.

Verification: 305 tests green on 3.11 and 3.12 (68 new across
`tests/test_remediation.py` and `tests/test_straight_path.py`,
driving the real scene, mornings, commits, resolutions and nights);
ruff 0.15.x + mypy clean; flag-off golden 300/300 AND paired
stand-pat 300/300 (expected 82 / held 82, schema v1) on 3.11, 3.12
and 3.13 with all P2 code in the tree — the branch and its machinery
are provably inert unless entered.

### Round 9 correction (review — design rev. 10)

Review reproduced every round-9 number, accepted the branch's identity
and the randomness ownership, ruled on all four flagged questions —
and found two correctness defects and three design gaps; all corrected
at the root, recorded as design revision 10 before implementation.

- **The dormancy cache could lie at the worst moment.** The stored
  `Evidence.dormant` flag was reconciled nightly BEFORE the rival and
  law phases; the reviewer's repro — a protected 20-point record over
  30 physical, morale 5 → 4 after the reconciliation — read Case 40
  and graded `straight_exit` where the true file reads 50 and grades
  `almost_out`. Doctored saves could plant dormant records with
  nonexistent, departed or demoralized sources. The flag is GONE:
  retention protection is derived from the live roster inside one
  context-aware fold (`fold_case(evidence, dormant_sources)`, the set
  computed by `State.case` at every read), with halvings allocated in
  ledger order inside raw-total-minus-floor — so derived relief can
  never display the sum below the floor at all, and no phase ordering
  can stale it. The repro is pinned both ways, with the poach variant;
  `validate_cross_state` now binds ledger, roster, settlements and
  branch state as one payload (phantom witness sources, settlements
  naming nobody, and settlements naming the never-read-in are all
  refused).
- **The promised ledger is now visible.** One `EvidenceLedgerView`
  itemizes every record — kind, base and effective magnitude, source
  name, disposition, contest status — plus the meter (same fold, same
  context: identity by construction), the 25-point budget spent and
  left, the floor, and counsel's next target. "The case file
  (counsel's docket)" renders it from the branch morning menu; the
  renderer infers no rules. `models.remediation_disposition` is the
  one answer to what may touch a record; queue, verbs, docket and
  validation all consume it.
- **Settlements state both outcomes on every path.** The review's
  Marcus exhibit (cap spent, $360 paid, "what they know goes quiet
  for good", file unmoved) is pinned: the relational outcome and the
  evidentiary outcome are separate sentences — applied, truncated at
  the cap, cap-exhausted ("the engagement is settled; the evidence is
  not"), floor-bound, locked-in-free, or nothing-in-the-file.
- **The informant's tip is paper** (an intelligence report, not
  testimony — §2.3 amended) and counsel can argue it; the patrolman
  and the watchers stay witness records with external provenance,
  labeled immune in the docket. In round-9's 500-seed runs the tip
  was the dominant post-fork source-less accrual (286 records, 1,144
  points in typical entries) — reclassification moves it into
  counsel's reach, which shows up directly in the natural cohort's
  paired numbers below.
- **The burned book stays burned.** Route presentation is centralized
  and branch-aware (`routes._route_voice`): a disposal run speaks of
  cold buyers and one-use clearance contacts, never "coded orders on
  the board." Grammar, dice and option lists untouched; both voices
  pinned.

**The corrected gate (rev. 10 item 8: two cohorts, no constants moved,
no bar conditioned after the fact), 150 seeds, `--seeds 500` in
parentheses:**

| Cohort / row | Bar | Measured | Verdict |
| --- | --- | --- | --- |
| Natural: reachability | ≥ 55% | 57% (56%) | pass |
| Natural: earned-exit band | 25–70% | 48% (43%) | pass |
| Natural: covert share after fork+2 | < 5% | 0.0% (0.0%) | pass |
| Natural: paired — remediation leaves the file lower | ≥ 60% | 55/85 = 65% (172/280 = 61%) | pass |
| Natural: ledger + floor oracles, nightly | 0 bad | 0 (0) | pass |
| Redemption: median ΔCase fork→end | ≤ −5 | **−10.0** (−10.0) | **pass** |
| Redemption: Case strictly below entry | ≥ 60% | 148/150 = **99%** (497/500 = 99%) | **pass** |
| Redemption: ablation drop | ≥ 20 pts | **80** (76) | **pass** |
| Crash-freedom (both chaos fleets) | all | 300/300 (1000/1000) | pass |
| Quiet Sale battery (all P2 code in tree) | round-8 rows | identical | pass |

The redemption cohort is the frozen §3.1 reference entry (Case 31: an
immune seizure, the routine hum, a flagged over-ceiling record, the
informant's tip, and Marcus departed knowing everything), a
harness-owned predeclared literal entered through the real scene
across world seeds — `game.run` gained an injectable starting state so
the cohort runs the one real loop, not a drifted copy. Its earned-exit
rate reads 80% (76%) — above the 25–70 band, which per the ruling
binds the natural cohort; reported, not judged, and the reference
state was built to be redeemable. The natural cohort's absolute ΔCase
medians remain positive (+3.1 / +3.5) with the full decomposition
still printed — that is the cold-entry population the ruling
deliberately measures by the paired bar instead. The dirty-month
ecological confirmation moved with the taxonomy fix: lockup ≥ 20
entries now run median ΔCase −4.9 (−4.5) with 21/25 (73/92) strictly
below, ablation 17 (14) points.

Two notes for the re-review, flagged not judged: the natural paired
bar sits close to its floor at 500 seeds (61% against ≥ 60%), and the
redemption cohort has no band bar of its own — if review wants one,
it lands as a criterion amendment, not a tuning pass.

After the correction: 316 tests green on 3.11 and 3.12 (11 new);
ruff/mypy clean; flag-off golden 300/300 and paired stand-pat 300/300
(expected 82 / held 82, schema v1) on 3.11, 3.12 and 3.13; the escrow
ensembles reproduce round 8 to the digit at 150 and 500 seeds. The
Quiet Sale's flag remains down pending the re-review's explicit word.

### Round 9 correction 2 (re-review — the monotone ledger, design rev. 11)

Re-review reproduced every correction-1 number, accepted all eight
rev. 10 corrections in architecture, ruled on both flags (no criterion
amendment: the natural paired bar passes as written and must re-clear
after this fix; the redemption exit rate is not a failure and gets no
band) — and found the replacement ledger **non-monotone at the
floor**, plus a disposition authority still answering without the
state to know. Both fixed at the root, recorded as revision 11 on
paper first.

- **Case arithmetic is monotone again.** The all-or-nothing relief
  allocation moved the meter the wrong way at the boundary, both
  directions reproduced by review: one point of NEW paper dropped
  Case 15 → 10 (the bigger allowance let a too-big halving suddenly
  fit), and a −2.46 contest RAISED Case 10.1 → 13.6 (the shrunken
  allowance evicted it). `dormant_relief` now allocates per record
  and PARTIALLY at the boundary — cut = min(half the magnitude,
  allowance remaining) in ledger order — so total relief is exactly
  min(halvable, raw − floor) and the display can only move the way
  the design promises. All six ruled properties are pinned, the two
  repros among them: accrual never lowers, remediation never raises,
  losing protection never lowers, gaining it never raises, docket
  effective magnitudes sum to the meter, and floor-limited partial
  relief renders honestly ("loyalty holds part of it down; the floor
  limits the rest"). The fold, the docket, the settlement lock-in
  (free portion = tonight's actual cut; paid portion = the rest of
  the halving, cap-scaled per record) and the independent oracle all
  consume the one allocation contract.
- **The witness relationship has one authority, and the lifecycle is
  closed.** `models.witness_status` (settled / beyond_reach /
  protected / reachable) now feeds a context-aware
  `remediation_disposition`: a settled or arrested source no longer
  renders "a settlement can reach this" — the review's four repros
  are pinned. Per the ruling, **settled-out names never rehire on
  the Straight Path**: the real staff menu refuses them and a
  settled-and-hired payload is refused at load, alongside duplicate
  employee keys and witness testimony sourced to the never-read-in.
- **The docket keeps round 6's promise**: storage stays per-tick,
  the display rolls the routine hum into one line with its entry
  count and exact totals; the counsel status line says "cap
  exhausted" or "the floor holds" instead of naming a target no
  contest can reach.
- **The reporter tells the truth.** The cohort contract is an
  explicit spec: only binding numbers print as bars; the natural
  cohort's absolute ΔCase and the redemption cohort's exit rate
  print as reported; every dirty-month and single-verb line is
  tagged [diagnostic]. (The relabeling also surfaced a harness bug:
  the dirty-month ablation bot had kept remediating after its flag
  was renamed — fixed; its drop reads 13–14 points again.)

**The gate after the fold correction — the ruling's condition was
that the natural paired bar re-clear, and it does** (150 seeds,
`--seeds 500` in parentheses):

| Cohort / row | Bar | Measured | Verdict |
| --- | --- | --- | --- |
| Natural: reachability | ≥ 55% | 57% (56%) | pass |
| Natural: earned-exit band | 25–70% | 48% (43%) | pass |
| Natural: covert share after fork+2 | < 5% | 0.0% (0.0%) | pass |
| Natural: paired — remediation leaves the file lower | ≥ 60% | 55/85 = **65%** (172/280 = **61%**) | pass |
| Natural: ledger + floor oracles | 0 bad | 0 (0) | pass |
| Redemption: median ΔCase fork→end | ≤ −5 | −10.0 (−10.0) | pass |
| Redemption: strictly below entry | ≥ 60% | 99% (99%) | pass |
| Redemption: ablation drop | ≥ 20 pts | 80 (76) | pass |
| Crash-freedom (both fleets) | all | 300/300 (1000/1000) | pass |
| Quiet Sale battery | round-8 rows | identical | pass |

The single-verb diagnostics (not bars) say what each verb is worth:
counsel alone pulls the reference file −7.0 with 96–97% strictly
below but exits 0% — the hostile witness stays unsettled; settlements
alone exit 75–79% at ΔCase +2.0 — the goal term without the
arithmetic. The two verbs are load-bearing in different terms, which
is the §2.3 design working as written.

After correction 2: 327 tests green on 3.11 and 3.12 (11 new);
ruff/mypy clean; flag-off golden 300/300 and paired stand-pat 300/300
(expected 82 / held 82, schema v1) on 3.11, 3.12 and 3.13; the escrow
ensembles reproduce round 8 to the digit at both depths. No PR is
open and the Quiet Sale's flag stays down — both wait for the merge
disposition.

## Still open (carried to the next design pass)

- The payoff-triggered Act I fork: P0 and P1 are complete and merged
  (P0 foundation + telegraphs, rounds 6–7; P1a fork skeleton + P1b
  Quiet Sale, round 8 with corrections 1–6). **P2 — the Straight Path
  — is implemented, measured (round 9), and corrected twice under
  review (rev. 10, rev. 11: the monotone ledger and the closed
  witness lifecycle); its two-cohort gate passes with the natural
  paired bar re-cleared after the fold fix** (65%/61% against ≥ 60%;
  redemption −10.0 median, 99% strictly below, 76–80-point ablation).
  Awaiting the merge disposition; **the Quiet Sale's flag has NOT
  lifted and no PR is open** — both wait for the reviewer's explicit
  word. P3 (the Harbor War) stays paused until then.
- The Quiet Sale's human-play verdict is untaken: *sold well* was never
  reached by any bot (the clean number must be earned by the month, not
  the week — the branch's thesis). Whether that is fun is a seeds
  24/39/8 question, deferred to the P4 human-play pass.
- Heat still under-binds relative to the Case; needs local teeth without
  becoming a second global meter.
- Event responsiveness beyond payday/heat-wave is now *provable* with the
  market bot (it reads the news); a dedicated study should measure whether
  exploiting port-seizure/concert pricing separates skilled play.
- Founder-staff attrition remains high across strategies; resignation
  warnings now precede departures, but retention still needs a reason to
  spend money on people.
