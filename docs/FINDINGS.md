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

## Still open (carried to the next design pass)

- The midgame still resolves around day 12–15. The payoff-triggered
  Act I fork is now fully designed and merged as the decision record
  (`docs/ACT1_FORK_DESIGN.md`, PR #6); implementation follows the phased
  plan there. P0 is now complete — foundation (round 6) plus the §2.1
  telegraph lines (round 7); P1 (the sit-down behind a feature flag) is
  next, on the reviewer's go.
- Heat still under-binds relative to the Case; needs local teeth without
  becoming a second global meter.
- Event responsiveness beyond payday/heat-wave is now *provable* with the
  market bot (it reads the news); a dedicated study should measure whether
  exploiting port-seizure/concert pricing separates skilled play.
- Founder-staff attrition remains high across strategies; resignation
  warnings now precede departures, but retention still needs a reason to
  spend money on people.
