# The Act I fork — design for review

**Status: paper design only — revision 2, responding to design review.**
Review approved the hard-fork structure, the four chairs, stand-pat, and
the 30-day calendar as a v1 experiment, and required the corrections
recorded in §8 before implementation. No game code changes accompany this
document; the one independently authorized code change — the issue #4
raid-timeout fix — is deliberately kept out of this design-only branch.

**The problem.** Paying Carmine ends the game's central pressure around day
12–15 (`docs/FINDINGS.md`: the market bot's median healthy payday is day 12),
and the back half of the month goes flat. The agreed direction is that debt
payoff should trigger a deliberate fork — *"Act I is over; choose what this
empire becomes"* — not an arbitrary second debt.

**Canon.** This fork is grounded in canon, and one step beyond it. The
original pitch names the acts ("Act I: The hustle. One shop, one car and a
debt due in thirty days" → "Act II: The operation. … the first additional
branch. Rivals begin treating the player as a territorial threat") and
insists that "winning should mean securing an exit, not simply filling a
progress bar," listing the exits this fork offers: build a legitimate
franchise and abandon the trade; eliminate or absorb the other syndicates;
sell the entire operation and disappear
(`docs/canon/00-original-pitch.md`). What canon nowhere describes is a
hard, mutually exclusive choice scene — the Sit-Down is an
*interpretation* of that material, and is recorded as such (§2.8). The
north-star brief's ten invariants (`docs/canon/01-north-star-brief.md`)
are treated as the acceptance bar throughout; §2.8 maps the design against
them and lists the deviations this design would record in
`docs/canon/README.md`.

**Why this precedes heat and retention tuning.** Heat currently under-binds
and staff retention lacks a reason to spend money on people (FINDINGS, "Still
open"). What those systems must *become* depends on what the post-payoff game
is: a war campaign needs heat to be territorial denial; a divestment campaign
needs staff to be witnesses with feelings; an expansion campaign needs the
roster to be a genuinely scarce resource across two addresses. §2.6 derives
the requirements so the later tuning passes have a target.

---

## 1. Three competing fork structures

Three genuinely different shapes were considered for *how* the fork happens —
not three different branch lists. Each is sketched fully enough to be built.

### 1.1 Structure A — "The Sit-Down": a hard fork at a named scene

The night the last dollar reaches Carmine, he sends the fruit basket. The
next morning he sends a car. The morning phase opens with a one-time scene —
the sit-down — where the player is shown the chairs at the table: the paths
actually available to them given the calendar, the Case, and the state of
their feuds. Choosing one is explicit, informed, and irreversible. Each
branch re-arms the game with its own goal, its own pressure clock replacing
the debt, branch-specific verbs added to the existing day loop, and its own
endings. Declining every offer is itself a choice ("stand pat"): the game
continues exactly as it ships today, and the offers expire.

- **Trigger:** deterministic, telegraphed across Act I (payment remarks,
  calendar and Case warnings — §2.1), gated by calendar and Case.
- **Choice:** one screen, one decision, permanent. What each chair costs and
  what it forecloses is stated in the scene before committing (invariants 7
  and 8: telegraphed, explainable).
- **Endings:** each branch owns 2–3 endings; the existing seven remain
  reachable via stand-pat and as failure fallbacks.
- **Build cost:** one scene, per-branch goal checks and verbs, per-branch
  epilogues. The branches reuse the existing day loop and systems.
- **Verifiability:** excellent — a branch is a labeled state; a bot fleet
  can be forced down each branch and measured (§2.7).
- **Risk:** railroading. A menu of destinies can read as "pick your DLC."
  Mitigated by the chairs being state-dependent (the table reflects the run
  you actually had), by stand-pat, and by the branches being commitments to
  *pressures*, not scripts.

### 1.2 Structure B — "Standing Offers": a soft fork by accumulated commitment

No single scene. After payoff, three opportunity tracks open in the
background — a buyer is asking around about the shop; Carmine floats
expansion money through Sammy or a nephew; a rival's weakness becomes
visible. Each track has a fuse and escalating commitment steps (take the
buyer's lunch, take his diligence walk, take his deposit…). The player
drifts into a branch by doing branch-things; somewhere along each track a
step is explicitly marked as the point of no return.

- **Trigger:** payoff opens the tracks; nothing else announces itself.
- **Choice:** emergent, gradual, reversible until each track's marked step.
- **Endings:** as in A, keyed to whichever track completed.
- **Build cost:** highest — three concurrent offer state machines woven into
  morning/night, each needing telegraphy at every step, plus rules for
  tracks interfering (the buyer walks if you start a war mid-diligence).
- **Verifiability:** poor. Bots can straddle tracks; "which branch was this
  run?" becomes a classification problem instead of a fact. The acceptance
  criterion "branches genuinely play differently" is hard even to *state*.
- **Risk:** illegibility — exactly the failure mode invariant 8 forbids.
  Also quietly becomes "the same loop with more events," the outcome this
  assignment exists to avoid.

### 1.3 Structure C — "Postures": shared clock, reconfigured systems

Payoff unlocks a posture selector (legit / expand / war), switchable at
night. A posture is a set of system multipliers and permission changes:
legit posture disables routes and accelerates reputation; war posture
cheapens raids and angers rivals; expansion posture unlocks investment
sinks. The 30-day clock and the existing graded epilogue are untouched; the
epilogue reads the dominant posture.

- **Trigger:** payoff, silently.
- **Choice:** continuous, reversible — which is the problem.
- **Build cost:** lowest by far. No new scenes, no new endings.
- **Verifiability:** moderate (posture is labeled state), but the thing it
  verifies is weak — the branches share every screen and every verb.
- **Risk:** this is *literally* "the same loop with a different label."
  Reversibility removes weight: nothing is irrevocably lost, so nothing is
  chosen. It also leaves the flat back half flat — pressure comes only from
  whatever multipliers the posture applies, which is the arbitrary second
  debt wearing a hat.

### 1.4 Recommendation: Structure A, with two grafts

**Build the Sit-Down.** It is the only structure whose branches can be
*specified*, *telegraphed*, and *measured* — the three properties this
project's working method depends on. Its railroading risk is real but
mitigable; B's illegibility and C's weightlessness are structural.

Two grafts from the losers are worth keeping:

- From B: **temptation offers.** After choosing a branch, the world keeps
  making the *other* life visible — one-last-run offers land in the Straight
  Path, the buyer calls once more during a war. These are flavor-plus-bait
  (refusing is free; accepting has stated branch consequences, §2.4). They
  keep the Dope Wars temptation alive (invariant 4) inside branches that
  wind the trade down.
- From C: **stand-pat as the null branch.** Declining everything preserves
  today's game verbatim. It is the control group for every study in §2.7
  and the guarantee that the fork cannot make the game worse than main.

---

## 2. The Sit-Down: full specification

### 2.1 Trigger conditions and edge cases

**Base rule.** When `_pay_debt` drives the debt to zero (`debt_paid_day`
set), that night ends normally (fruit basket line, already in the game). The
next morning, before the regular morning menu, the sit-down scene runs —
once, ever. Define `R` = days remaining including the sit-down morning
(`R = 31 − sitdown_day`; payoff day 13 → sit-down day 14 → `R = 17`).

**Eligibility snapshot (rev. 3, placement corrected rev. 4).** Chair
eligibility is evaluated and frozen when the player **locks up** — on
leaving the settle-accounts menu on the night the debt reached zero —
after every discretionary account action, immediately before the rival
and law phases. A payment-time snapshot would reward action ordering
(pay the last dollar first, over-launder afterward at Case 65 → 85, and
keep both Case-gated chairs); a lock-up snapshot includes every
voluntary act in the reckoning, while still protecting the table from
the world's after-hours dice. Evidence accrued after lock-up (the rival
phase, the law phase) still joins the Case and can still end the run —
arrest at 100 outranks the fork, §2.5, and always wins the tie — but it
cannot close a chair retroactively: the table the player earned at
close of business is the table they sit at. Without this rule the
world's own dice could empty a chair after the payoff decision, with no
telegraph even possible — violating "an empty chair must be earned,
never retroactive." The scene renders from one canonical view carrying
BOTH ledgers (rev. 6): the frozen Case and chair verdicts the offers
were cut from, and the live morning Case with its band. **Every**
difference between them is rendered, whether or not a threshold moved —
a quiet 20 → 32 warming is shown ("the chairs were set at closing
time") exactly as a gate-crossing 65 → 72 is ("last night didn't help —
but the offers stand"). Chairs that remain open at a near-closed file
are visibly dangerous in-scene, per the edge cases above.

**Which chairs are at the table** (each gate is stated in-scene when it
fails — an empty chair is explained, never silent):

| Chair | Needs | Withheld when |
| --- | --- | --- |
| The Straight Path (clean exit) | `R ≥ 5` | too few days: "you can't launder a reputation in a weekend" |
| Carmine's Partner (second branch) | `R ≥ 10`, Case < 70 | calendar: "no time to build anything now"; Case: "nobody invests in a burning building" — he sends a nephew instead of coming |
| The Harbor War (territory) | `R ≥ 8` | calendar: "wars outlive months" |
| The Quiet Sale (escrow) | `R ≥ 5`, Case < 85 | Case ≥ 85: "any buyer's diligence would subpoena itself" |
| Stand pat | always | — |

**The fork is telegraphed before payoff — an empty chair must be earned,
never retroactive.** The player learns the rules of the table while the
debt still exists, through four channels (all transcript-only: no state
change, no RNG draw — §2.7 requires pre-fork runs to remain per-seed
identical to main):

- **Payment remarks.** Payments landing in `_pay_debt` draw lines from
  Carmine keyed to trajectory — pay big and early and he says what he's
  thinking ("A man who pays early is a man worth backing. We should talk
  when this is done."). The remark channel is how the player first hears
  that *finishing* is the beginning of something.
- **Calendar warnings.** If the debt is alive on day 20, the morning
  carries a warning in Lena's rumor voice: the man who was asking around
  about buying shops is losing interest; whatever you're going to be,
  you're already becoming it. On day 24 it turns explicit: pay by
  tomorrow night or the table will be empty — past day 25, whatever you
  are on day 30 is what you'll be. Both lines print unconditionally on
  their days; they are world facts, not chance.
- **Case warnings.** When the Case first crosses 60 with the debt alive,
  a line notes that investors and buyers read the papers too — naming the
  fact that a hot file narrows the table, with the exact thresholds
  disclosed by the sit-down scene itself.
- **Carmine's ledger.** Once the debt drops below half, the morning
  header's debt line gains a clause ("…and he has opinions about what
  comes after") — a standing pointer that payoff is a doorway, not just a
  finish line.

Verification hooks into §2.7, split by gate type because their timing
differs (criteria as amended by rev. 3).

*Calendar gates* are slow. The original "at least two days before
payoff" is arithmetically false at the boundary and was never
achievable with fixed warning days: payoff day 21 → sit-down day 22 →
`R = 9` withholds Carmine's Partner, and the day-20 warning preceded it
by one calendar day. The criterion is therefore: for every
calendar-withheld chair, the relevant warning morning strictly precedes
the payoff day — the player gets **at least two playable decision days
including the warning day** before the payoff that sealed the table.
The fixed beats stand (day 20 covers the Partner boundary at payoff 21
and the War boundary at payoff 23; day 24 covers the no-sit-down cliff
at payoff 26) and each satisfies the criterion at its own boundary.

*Case gates* can slam shut in a single night — a route bust or an
over-ceiling wash on payoff night can jump the Case from 55 past 70 —
so the requirement is disjunctive: either the Case-60 warning appeared
on an earlier morning, or the gate was crossed on payoff day by a
**player act whose own warning surface fired before the act ran**.
Laundering is not the only gate-closing act; every evidence-capable act
carries a pre-action surface while payoff is in reach (debt alive, and
on-hand cash ≥ debt, measured when the act is planned or taken — plans
are intentions, committed at service, so "plan time" is the scheduling
moment, and two acts re-measure later, below):

- *Over-ceiling wash*: warned before the amount prompt whenever the
  worst-case paper evidence (`min(20, over/400)` washing everything)
  could reach a gate — exact arithmetic, since the accrual formula is
  deterministic.
- *Contraband route* (scheduled in the morning, runs at service):
  warned at plan time, unconditionally in the window — what a route
  books (bust, resistance, owner-in-vehicle, seizure per unit) depends
  on the night, so the warning is a superset by construction. The plan
  can still be cancelled or replanned. **Window (rev. 4):** the route
  that earns the final payoff money is the natural "one last run," so
  this surface's reach test counts what tonight could plausibly bring
  in — `on-hand + 2 × demand × gourmet ticket + Σ units ×
  district price × 1.5` ≥ debt — each term a supremum of its runtime
  counterpart (a sale tops out at a 1.2 offer roll × the 1.25 haggle
  premium; shop orders never exceed demand, no ticket beats gourmet,
  and the doubling absorbs a later policy change re-forming the order
  book). Overestimating only ever warns early.
- *Raid* (scheduled in the morning, runs before the night's settling):
  warned at plan time, unconditionally in the window — pattern premium,
  gunfire, bodies and witnesses depend on choices made mid-job.
  **Recheck (rev. 4):** the day's takings can put payoff in reach after
  the job was scheduled, so eligibility is re-measured immediately
  before the job runs; the warning prints once — at plan time or at
  execution, whichever first finds the table at stake.
- *Firing an aware employee* (fixed 6-point witness record): warned
  before the selection menu exactly when the Case is within 6 of a gate
  — sharp, because the accrual is a known constant.

Two residues are named rather than papered over. **World events** (a
staff walkout, a detective visit, a walk-through, rival moves) are not
player acts and get no pre-action warning; a world-event crossing on
payoff day itself is answered by the eligibility snapshot (post-payment
events cannot close chairs at all) and, for pre-payment same-day
crossings, by the sit-down scene naming the specific record that closed
the chair — the acceptance criterion binds player acts. **In-act
stacking** (several evidence records inside one warned act) is covered
by that act's single warning: the warning is on the act, not the
record. In every case, the sit-down scene names the specific record
that closed each empty chair.

**Edge cases the assignment names, answered concretely:**

- **Early payoff (day 7).** Sit-down day 8, `R = 23`. All chairs present.
  Carmine is impressed and says so; his offer improves at the margin (first
  points payment deferred one cycle, §2.4.2) — a reward for excellence, not
  a different game.
- **Late payoff (day 25).** Sit-down day 26, `R = 5`. Only the Straight
  Path, the Quiet Sale, and stand-pat are on the table, and the scene says
  why. This is honest: paying late means Act I consumed your month. Payoff
  on day 26 or later (`R ≤ 4`, no chair could seat): no sit-down at all —
  a single line of Carmine's respect, then the existing endgame. The
  day-24 warning (above) told the player exactly where that line was. The
  current epilogue already grades that run.
- **Payoff while the Case is high.** Case ≥ 70 empties Carmine's chair;
  Case ≥ 85 empties the buyer's. The Straight Path remains available at any
  Case — it is the *natural* play at high Case — but §2.4.1's evidence
  arithmetic means a very hot player may be choosing a dignified way to
  lose. The scene shows the current Case band next to each chair (invariant
  8). The War chair also remains: declaring war at Case 85 is legal and
  near-suicidal, and the scene says so.
- **Payoff with rivals at war.** An active `raid_warning` or a vendetta-band
  relation (≤ −60) does not delay the sit-down — Vinnie's cars idle outside
  the restaurant where you meet Carmine. Consequences: the telegraphed raid
  still lands on schedule regardless of branch; the Quiet Sale applies its
  war discount and an actual raid during escrow is a repricing incident
  (§2.4.4); the Straight Path inherits the feud as its main obstacle — exit
  requires settling it (§2.4.1); declaring the Harbor War on a rival already
  at vendetta costs nothing extra (they started it).
- **Payoff and arrest the same night.** `_check_endings` runs before the
  next morning; if the Case closes the night you pay, the fork never opens.
  Endings always win ties.
- **`--max-days` shorter than the payoff day** (harness runs): unchanged —
  the fork simply never fires. Bench and analysis baselines for Act I are
  therefore untouched by construction.

**What choosing costs, globally.** Selecting any chair dismisses the others
permanently — the sit-down is one morning in one man's restaurant, and the
offers are live only while everyone is at the table. Stand-pat dismisses
them too (Carmine does not ask twice; the buyer buys elsewhere). The scene
states this before confirming.

### 2.2 What the player chooses — summary of the four chairs

Full branch specs are §2.4; this is the choice as the player sees it.

| Chair | The deal | The price | Irrevocably lost |
| --- | --- | --- | --- |
| Straight Path | Leave the trade; by day 30 be a real restaurant nobody can touch | Income collapses to pizza margins while payroll still carries every witness | The network: the supplier, the coded order board and raids are gone for good — three counted disposal runs are all that remains of the wheel; rivals stop fearing you |
| Carmine's Partner | His $20k opens your second shop; you run both | Points: $2,500 to Carmine every 5 days, forever — equity, not debt | Independence: no payoff clears him; exit and sale endings are off the board |
| Harbor War | Break a rival and take their trade | War pay, injuries, and a Case that only ratchets (pattern evidence never remediates) | Peace with the target: their relation locks at vendetta; no truce, ever |
| Quiet Sale | Four days of buyer diligence, then close at a marked price | The price wears every scar: Case, feuds, reputation | The shop, and with it the run — closing is an ending |
| Stand pat | Keep the sandbox exactly as it is today | The flat back half this fork exists to fix | All four offers |

### 2.3 The Case gets counterplay: typed evidence

**The problem, honestly.** The Case is monotone: no call site ever
subtracts. Inside the current month that is survivable arithmetic (a market
run reaches day 30 at Case ~26); over any longer campaign it is not — every
laundering action adds ≥ 0.5, every raid after the first adds a pattern
premium, so Case → 100 is a theorem, not a risk. Two of the four branches
break on this: the Straight Path is *about* redemption (a branch where your
score can only degrade is a countdown, not a campaign), and any future
calendar extension (§6.1) inherits the theorem. The assignment says solve or
scope; this design solves the minimum and scopes the rest.

**The move: Case becomes a sum, not a scalar.** `case_flags` (today: bare
strings) become typed evidence records: `{day, magnitude, kind, source}`,
with `state.case` derived as the clamped sum of magnitudes. Replaying Act I
produces identical totals (same magnitudes, same sum) — a cheap regression
proves the refactor is behavior-preserving before any counterplay lands.
Kinds, assigned at the existing `add_case` call sites:

- **witness** — attached to a person: walked out knowing everything (6),
  fired knowing everything (6), poached knowing everything (8), a long talk
  with a detective (10).
- **paper** — the file's documents: over-ceiling laundering
  (≤ 20/incident), the 0.5 routine-discrepancy ticks (aggregated into
  one rolling "routine discrepancies" record), frozen-deposit reviews,
  and intelligence in the file — the informant's tip is a report, not
  testimony (rev. 10 ruling).
- **physical** — seizures and scenes: traffic-stop seizures, walk-through
  finds, the owner photographed by the wagon, bodies, gunfire, brawls.
- **pattern** — the raid handwriting premium, and only that.

**Counterplay verbs (unlocked by the four active branches only — never in
stand-pat, which must remain a per-seed-identical control; load-bearing in
the Straight Path):**

- **Retain counsel** — $150/day, clean, from the Improvements menu. Every
  3rd retained day, the oldest *paper* record is contested: magnitude −60%.
  Dual use (invariant 10): a good lawyer needs the books to make sense —
  while retained, the believable ceiling is enforced with no over-ceiling
  option at all (the "wash more anyway" branch of `_launder` is simply not
  offered; counsel's office sees the tapes).
- **Settle a witness** — a night action targeting a *departed* aware
  employee: a one-time settlement (≈ 6× their daily wage) makes their
  records dormant (magnitude −50%, permanently). A *current* aware employee
  with morale ≥ 5 keeps their own records dormant for free — retention as
  case defense, which is precisely the money-to-people reason the retention
  work has been missing (§2.6).
- **Nothing touches physical or pattern evidence.** Ever. What the city saw,
  it saw.

**Bounds (so evidence laundering never becomes a slider — the money-doctrine
invariant has an evidence twin):** total remediation across a run is capped
at 25 points. The floor is not hidden arithmetic: whenever remediation
would take the sum below 10 — the first time and every later time — a
permanent **institutional suspicion** record ("they remember your name")
is written, or topped up, by exactly the difference, so the sum never
displays below 10 and always equals the records the player can read. That
ledger-transparency identity is asserted every night by every bot (§2.7).
The climate cools; it does not un-happen.

**Terminal semantics.** The moment the sum reaches 100 — at accrual time,
in whatever phase the day happens to be — prosecution latches: `game_over =
"arrested"`, immediately and irrevocably. Remediation is a dead letter after
the latch; no settlement, no counsel, no arithmetic un-arrests you. The
terminal check therefore lives in the evidence-accrual path itself, not in
the night's `_law_phase` sweep (§5), and it takes precedence over every
simultaneous success (§2.5).

### 2.4 The branches

Each branch below is specified as: goal · unlocks · pressure replacing the
debt · how each existing system carries forward (all eight: clean money,
dirty money, the Case, heat, rivals, raids, reputation/demand/pantry,
staff) · failure states and endings.

#### 2.4.1 The Straight Path (clean exit)

**Goal (checked at day 30):** contraband stock zero everywhere; dirty cash
≤ $200; Case ≤ 45 after remediation; reputation ≥ 45; no *hostile unsettled
witness* (a departed aware employee with morale < 5 and no settlement);
**no open feud** (no live raid warning, no rival at relation ≤ −60); and
**five clean days** — `days_since_last_crime ≥ 5`, where every criminal act
after the fork (a disposal run, a fire-sale meeting, an accepted temptation
offer, washing past the ceiling) resets the clock. Paying tribute does
*not* reset it — being extorted is victimhood, not trade. All liquidation
must therefore finish by day 25; the last week has to actually be clean.

**Unlocks:** counsel and settlements (§2.3) as the core verbs; **Disposal**
replaces "Plan tonight's route" in the morning menu; **Advertising** (clean
spend, $300 → demand/reputation lift over following days — canon's clean-money
list has waited for this) appears in Improvements.

**The disposal problem** — remaining stash must go, three ways, priced like
everything else in this game: (1) *fire-sale to Sal's people* — at most one
meeting a day, bulk, 40% of book value, +8 Sal relation, small
witness-evidence risk if observed; (2) **disposal runs** — a counted,
bounded remnant of the route system: **at most three per run, ever**, shown
in the morning menu as `disposal runs left: n`; they sell only stock held
at fork time (the supplier is gone and nothing restocks), at 60–75% of
board price (you are a seller without a network now), under full Act I
route rules and risks; (3) *burn it* — zero return, zero risk, no crime,
and Tony watches you do it. The first two are crimes and reset the
clean-days clock; burning never does. **Temptation offers are none of
these:** they are *new trade* at full margin — accepting one is ordinary
crime (clock reset, normal evidence exposure) and does not spend a disposal
run, because disposal is liquidation and a temptation offer is business.
The distinction is printed on the offer card itself.

**Pressure replacing the debt:** income collapses to pizza margins while the
payroll still carries every read-in name — you dare not fire what you can't
afford to keep (firing an aware employee is +6 Case *witness* evidence,
already in the game; now it's the whole game). Rivals smell retreat:
Vinnie's coupon blitzes and poaching intensify against a shop that no longer
scares anyone (aggression multiplier while you hold no stash), and Sal —
politely — offers to buy your coded-customer book, the branch's standing
temptation. An active feud must be settled to exit — and the raid verb is
gone, so the tools are civilian: tribute and truce (the existing
negotiation), the fire-sale channel's goodwill with Sal, and outlasting
Vinnie behind the guard upgrade and a defended door. A rival who cannot be
bought must be weathered; that risk is the price of this chair.

**Systems carry-forward:** *Clean money* becomes the only money; advertising,
counsel, settlements, and payroll all draw on it — clean insolvency is the
branch's economic failure. *Dirty money* is a liability to be washed down
under the (counsel-enforced) ceiling or forfeited in the epilogue
accounting. *The Case* is the scoreboard: paper contests and witness
settlements against a floor of whatever physical/pattern record Act I wrote.
*Heat* still draws walk-through searches — which now find nothing, but each
visit spooks a witness (morale −1 for one observant or aware employee:
searches attack the exit through people, not stash). *Rivals*: alertness
decays (you aren't raiding), relations drift by their disposition; Vinnie
exploits, Sal trades. *Raids*: gone as a verb; incoming raids remain fully
live — the defense game is now protecting a reputation, not a stash.
*Reputation/demand/pantry* graduate from cover-generator to victory
condition: the quality-locked pantry, the critic, and advertising decide
whether a legitimate restaurant exists by day 30. *Staff*: morale is case
defense (§2.3); raises, severance, and settlements are the branch's main
spend.

**Failure states / endings:** *"The Legitimate Exit (earned)"* — every
goal term met; the existing rarest-pie ending, upgraded text acknowledging
what it cost. *"Almost Out"* (new) — every term met except Case 46–99:
clean, and they're still watching; bittersweet. *"Half Measures"* (new) —
day 30 with any other term failed (stock remains, dirty > $200, a hostile
unsettled witness, an open feud, a crime inside the final five days, or
reputation < 45): you left the trade and never landed the exit; the
epilogue names the term that failed (invariant 8). *Clean insolvency*
(payroll unmet with no stock and no dirty ≥ 2 consecutive days) → the
existing "broke" oven-went-cold ending with branch flavor: the cover
business couldn't cover the cover-up. The Case latching at 100 remains
arrest, any moment (§2.3). Full matrix and precedence: §2.5.

#### 2.4.2 Carmine's Partner (the second branch)

**Goal (day 30):** points current, the Case never having latched — both
shops are open by the branch invariant declared below — graded on
combined net and the second shop's reputation. This is canon's Act II made
playable, and it deliberately ends the month *mid-story*: the ending text
points at Act III.

**The deal:** Carmine fronts $20,000 (illustrative breakdown: build-out
$9k, permits $1.5k — clean, permits are paperwork — used second wagon
$2.5k, opening float $3k, reserve $4k). The obligation is **points, not
debt**: $2,500 to Carmine every 5 days, unmarked bills preferred, forever.
No amount pays him off; it is equity. Early payoff (≤ day 10) defers the
first points cycle by one — his compliment.

**Site selection** (the branch's first screen): any district but Old
Harbor. University Hill — volume, students, no owner; Little Sicily —
reputation country, Sal's turf; The Meadows — the best covert demand in the
city, Vinnie's floor. Opening on a rival's turf is a commercial declaration
(steep relation hit, their counterplay intensifies there); the safe pick is
a real choice, not the only one.

**Pressure replacing the debt:** the points clock (miss one: a warning and
$500 vig added to the next; miss two — consecutive or not: foreclosure,
§below), double payroll, double rent, and **the roster does not double**:
eight employees, two addresses, one-person-one-job. The wagon count is two
but read-in drivers are however many you've made — a second covert route
needs a second person you trust with your life. Two believable-revenue
ceilings help launder, but points must be *earned*: pizza margins alone pay
Carmine by starving growth, which is the branch's trap — his money keeps
you criminal. (Canon, verbatim: "A second branch increases laundering
capacity and territory—but adds rent, payroll and another point of
exposure.")

**Systems carry-forward:** *Clean money* funds permits, build-out, double
payroll; *dirty money* has a standing buyer every fifth night. *The Case*
gains a new paper source — two registers, two tapes; counsel is affordable
here and busy. *Heat* becomes two-front: each shop's district heat gates
that shop's covert usefulness; the law phase watches both addresses.
*Rivals*: expansion reads as territorial threat (canon Act II) — the
neighbor of your chosen district responds in kind (Sal politically, Vinnie
physically); tribute demands can now name either address. *Raids*: yours
unchanged; theirs may target the softer of your two shops — defense is now
an allocation question. *Reputation/demand/pantry* run **per shop**: shop
2 opens at reputation ~20 with its district's traffic and its own pantry;
neglect at either address strips that address's cover (the FINDINGS chain,
now twice). *Staff*: the branch's binding constraint — assignments per
shop, a named manager for shop 2 (an aware employee; their loyalty is now
load-bearing), familiarity resets in the new district, and poaching one
roster across two addresses is how rivals fight you here.

**An invariant, declared and tested:** once funded, the second shop opens
and stays open. Construction is deterministic (the capital is escrowed
with Carmine's own contractor), raid damage limps a shop but never
shutters it, and no Partner-branch event can un-open an address — the only
ways to lose shop 2 are Foreclosure and arrest, both of which end the run.
"Both shops open" is therefore not a day-30 condition to check but an
invariant to test; the day-30 matrix reduces to the points ledger.

**Failure states / endings:** *"The Operation (two ovens)"* — day 30,
points current; upgraded operation-holds text, explicit Act III hook. *"On the Hook"* (new) — day 30 with exactly one missed payment
outstanding: both ovens burn, but the vig is compounding and Carmine owns
your schedule now; a survival ending graded below Two Ovens, whose Act III
hook reads very differently. *"Foreclosure"* (new) — a second missed
payment, whenever it happens (consecutive or not): Carmine protects his
investment; he takes the second shop, the wagons, and the month's dignity —
the kneecaps ending's polite cousin, and the run ends that night. Arrest at
Case 100 carries branch flavor: he is embarrassed, and the epilogue implies
what that means. Full matrix and precedence: §2.5.

#### 2.4.3 The Harbor War (press the rivals)

**Goal:** a declared target's strength ≤ 0 by day 30. Their district's
underground becomes yours: coded customers call your board (underground
multiplier and delivery-relevant covert demand in that district transfer),
salvage from their stockroom, and the ending upgrades. Breaking *both*
rivals earns the existing Syndicate ending, now reachable on purpose.

**Declaring:** at the sit-down (or later — see below), name one rival.
Their relation locks at vendetta forever; no truce, no tribute, no cannoli.
The other rival picks a lane by disposition: Sal profits — supplies both
sides, raises "insurance" offers, and occasionally tips the police (Case
pressure from a man who never throws a punch); Vinnie, if he is the
bystander, raids opportunistically. Declaring war on a rival already at
vendetta (≤ −60) costs nothing extra — they started it.

**Unlocks:** the **war board** — a morning readout of target strength,
alertness/security word, your crew's health, turf status per district, and
a running ledger of *where their strength went* (jobs / ovens / corners /
the law), so the mixed campaign is visible on screen, not implied in prose.

**How a rival organization actually breaks.** Raids alone must not be the
answer — that is the grinding alertness was built to prevent — so the
branch specifies four damage channels, every one flowing through the
existing simulation:

- **Jobs** (existing): stock theft −12 strength, sabotage −10, ledger
  theft −8 — priced exactly as PR #3 left them: alertness, pattern
  evidence, carry and storage.
- **Corners** (new): every unit you sell in a district the target owns
  diverts their income — strength −0.15 per unit that night, capped at
  −4/night (their corner customers are finite, and so is your wagon). All
  existing route pricing applies unchanged: heat, patrols, their watchers
  (relation already falls −0.4/unit), and the oversell glut that stops one
  corner from being farmed.
- **Ovens** (extends existing): wrecked ovens already bleed −2/day;
  *additionally*, with no cover for their own routes, their customers
  switch faster — corner diversion counts **double** (cap −8/night) while
  the outage lasts. Sabotage is now mechanically, not rhetorically, tempo:
  it opens the window in which routes do the damage.
- **The law** (new option on a stolen ledger): hand it to the woman in the
  gray suit instead of leaning with it — target strength −20, and their
  aggression halves for 4 days (they are busy with lawyers). It is *their*
  case, not yours — but a cornered organization comes back meaner: their
  violence factor rises permanently. Leaning (−15, +$2,000, consumable)
  remains the greedy alternative. Either way the leverage is spent.

Victory arithmetic at the reference save (Vinnie, strength 58): one stock
job (−12) and one sabotage (−10, plus ~−8 oven bleed over four days), ~45
corner units with half sold inside the outage window (≈ −10), and the
ledger to the law (−20) sum to −60 — past 58 with tactical jobs a minority
of the damage. That claim is not decoration; §2.7 tests it: in successful
war runs no single channel may exceed 60% of strength destroyed, and a
raid-only bot must trail the mixed bot by ≥ 15 points.

**Pressure replacing the debt:** war pay (read-in crew wage +$20/day while
at war — refusal routes through the existing payroll-short morale
machinery); injuries from PR #3's scuffles compound (a three-person crew
with two in bed is a lost tempo week); counter-raids arrive on the existing
telegraph but bigger and more often (aggression multiplier while at war);
and **the Case only ratchets here** — pattern evidence never remediates
(§2.3), so the branch's real clock is whether you can finish the war before
the file finishes you. Alertness economics (the $781 → $597 → $438 decline
curve, FINDINGS round 4) make raid-spam self-defeating by construction —
winning requires *pacing*, mixing routes-in-their-turf, sabotage windows,
and raids on the days their security word says sleepy.

**Systems carry-forward:** *Clean money* keeps the shop alive under
coupon-blitz siege — a war run that lets the restaurant die loses its
laundering, its cover, and then the war. *Dirty money* funds war pay and
tribute-to-the-bystander. *The Case* is the doomsday clock; the ledger
play is its one release valve (their case, not yours). *Heat* becomes
territorial denial: raiding a district spikes its heat (+12 today), which
suppresses *your* routes there — burn a neighborhood taking it and you've
taken ash; heat is finally load-bearing per district (§2.6). *Rivals*:
alertness, relation, telegraphs, tribute, poaching — every existing wheel,
spun to maximum, plus side-picking. *Raids*: the branch's spine —
**gated on the issue #4 fix** (the noise-timeout branch currently awards
objectives through a broken room loop; a war economy cannot sit on that
bug). *Reputation/demand/pantry*: raid damage halves the kitchen, which
halves cover, which endangers routes — the existing coupling becomes the
war's logistics problem. *Staff*: nerve decides scuffles, injuries rotate
the roster, morale sags under war pay disputes, and the bystander rival
poaches your tired people.

**Failure states / endings:** *"The Harbor Is Yours"* (new) — target broken
by day 30; graded by what's left of you. *"The Syndicate"* — both broken
(existing ending, earned properly). *"A Long War"* (new) — day 30 with the
target still standing: the vendetta is permanent, the truce option is gone
forever, and the epilogue grades the stalemate by the strength ratio and
what remains of your shop and crew — you chose a war that will outlive the
month. *"Burned Out"* (new failure) — a successful rival raid landing while
the shop is already damaged (`damage_days > 0`) destroys it: the war came
home. Telegraphed twice over — warnings exist and damage is visible — so it
is always a risk knowingly accepted (invariant 7). *"Won the War, Lost the
Verdict"* (new) — the Case latches on or after the day the target falls:
they arrest you at the victory party. Distinct text because the player
earned both outcomes. Full matrix and precedence: §2.5.

#### 2.4.4 The Quiet Sale (escrow week)

**Not a quit button — a hold-steady game.** The buyer (Sal's straw man if
Sal lives and relation ≥ 0; an out-of-town operator otherwise) is at the
sit-down's edge with a marked price. **The clock, precisely:** the sit-down
day is diligence day 1 — his man walks the shop that same afternoon;
diligence days 2–4 follow; closing is the morning of fork+4. Five days
counting the sit-down, and the run ends at closing.

**The mark:** illustrative formula — base $3,000 + reputation × $140 +
50% of upgrade spend; discounts: −$45 × Case, −20% if any rival is at
relation ≤ −50 or has a live raid warning. The mark is recomputed each
diligence morning and shown with its terms (invariant 8: the player sees
exactly what their month is worth and why), and it moves **only when its
inputs move** — reputation, Case, the war clause, incidents. There is no
passive daily drift: diligence never pays you for waiting, it only
charges you for slipping.

**Diligence days:** each day is an incident check the player plays through
the normal loop. Laundering during escrow is off (the books are being
*read*); contraband on premises at any walk-through, a rival raid landing,
a staff walkout — each is an incident: reprice (−20 to −35%, drawn in
whole percentage points — rev. 8 constants ruling) or, twice, collapse. The stash must go — but the warehouse is not a free answer.
Moving stock off-site mid-diligence is a truck at a rolling door while the
buyer's man watches the neighborhood: the move itself carries a one-time
20% incident risk, and warehouse rent keeps drawing dirty cash all week.
More fundamentally, **what you keep decides what you sold**: closing while
contraband or more than $200 of unlaundered cash sits anywhere — shop,
wagon, or warehouse — reclassifies the ending as *"Sold the shop, kept the
trade"*: capped at the modest tier no matter the number, and the epilogue
says plainly that the Case stays open on *you*, because you didn't leave
the life, you downsized it. Only a genuinely clean close — nothing held
anywhere, dirty ≤ $200 — can reach the *sold well* tier and the true
escape text. Staff learn on day 2 and the severance line-items are the
humane-versus-cheap choice the epilogue remembers. On the closing morning:
sign, or walk away — walking keeps the shop, loses the buyer forever, and
drops to stand-pat with a bruised crew.

**Systems carry-forward (compressed by design):** *Clean/dirty*: clean
accumulates into the settlement; dirty must be hidden or burned — the one
week the two ledgers *cannot* touch. *Case*: pure price (−$45/point) — no
time to lawyer it. *Heat*: raises walk-through odds, i.e. incident odds.
*Rivals*: a last extortion when word gets out; war discount live. *Raids*:
incoming only; an incident. *Reputation/demand*: the single biggest price
input — the branch retroactively rewards having run a real restaurant.
*Staff*: severance, and whether Rosa hears it from you or from the buyer's
walkthrough.

**Failure states / endings:** *"Sold"* (new), tiered by total walk-away
(settlement + clean + whatever leaves with you, with retained stock priced
at base book value — exactly as `net_worth()` already prices stock): ≥
$25k *sold well*;
$10–25k *a modest ending*, which is what this chair honestly is; < $10k
*the fire sale* — and any close that keeps contraband or dirty cash is
reclassified *"Sold the shop, kept the trade,"* capped at modest
regardless of the number. *Collapse* (two incidents) and *walk-away* at
closing are **not** endings: both revert to stand-pat (reputation −8 on a
collapse) with the buyer gone forever. The Case latching during escrow →
arrested, with the cruelest timing in the game. Full matrix and
precedence: §2.5.

#### 2.4.5 Stand pat

Today's game, verbatim: same loop, same endings, same flat back half —
preserved deliberately as the control group (§2.7) and the guarantee of no
regression. The morning header notes what you turned down, once.

### 2.5 Terminal states: matrices and precedence

**Global precedence**, applied wherever two terminals could fire together:

1. **Arrest latch** — checked at evidence-accrual time (§2.3); beats
   everything, including a same-day branch success. One styling
   exception: if the war target had already fallen when the latch fires,
   the arrest prints as *Won the War, Lost the Verdict* — the same
   terminal, a distinct text arm.
2. **Branch catastrophes** — Foreclosure (second missed payment, that
   night); Burned Out (successful raid on an already-damaged shop, that
   night).
3. **Branch early completion** — the escrow closing, the only success
   that ends a run before day 30.
4. **Economic failure** — clean insolvency (§2.4.1 definition; the
   existing `broke` condition is reworked, §5).
5. **Day-30 grading** — anything still standing is graded by its branch's
   matrix below.

**Per-branch day-30 matrices** — every cell named, nothing falls through:

| Branch | Condition at day 30 | Ending |
| --- | --- | --- |
| Straight | all goal terms met | The Legitimate Exit (earned) |
| Straight | all met except Case 46–99 | Almost Out |
| Straight | any other term failed | Half Measures (names the failed term) |
| Partner | points current | The Operation (two ovens) |
| Partner | one payment outstanding | On the Hook |
| War | target broken, the other rival still standing | The Harbor Is Yours |
| War | both rivals broken | The Syndicate |
| War | target still standing | A Long War |
| Sale | (never reaches day 30 in-branch) | closes at fork+4 or reverts |
| Stand-pat | as today | the existing survived grades |

Partner's second shop is open at day 30 by tested invariant (§2.4.2), so
its matrix is the points ledger alone — a third state cannot exist.
Pre-day-30 terminals: arrest (any branch, via the latch); Foreclosure
(Partner); Burned Out (War); clean insolvency (any branch — the Straight
Path is where it lives); the escrow close — Sold, in three tiers with the
*kept the trade* reclassification (§2.4.4). Escrow collapse and walk-away
are **not** terminals: they revert to stand-pat and the run continues to
day 30 under the stand-pat matrix.

**Inventory.** Existing seven retained (kneecaps unreachable post-payoff —
the debt is zero; stand-pat reaches all seven exactly as today). New IDs:
Almost Out, Half Measures, On the Hook, Foreclosure, The Harbor Is Yours,
A Long War, Burned Out, Sold (one ID with graded tiers and the
reclassification). Won the War, Lost the Verdict is a text arm of
arrested, not a new ID. Upgraded texts (not new logic): the earned
Legitimate Exit, The Operation (two ovens), The Syndicate. Net: eight new
ending IDs, one new arrest text arm, three upgraded texts.
`_check_endings` becomes the precedence ladder above; the epilogue
dispatcher grows one arm per branch.

### 2.6 What this fork demands of Heat and staff retention

The still-open tuning items now have targets instead of vibes:

- **Heat** must become *district-territorial*: the War branch needs
  "overheat a district and you cannot work it" to be true (it is half-true
  today — `_stop_risk` scales with district heat — but decay at a flat
  5/night under-binds); the Partner branch needs per-address heat to gate
  per-shop covert usefulness; the Straight Path needs heat to threaten
  *people* (searches spook witnesses) once there is no stash to find. None
  of this needs a new meter — it needs the existing district meters to have
  district consequences. Tuning pass follows the fork, as agreed.
- **Staff retention** needs exactly one new primitive, used by all four
  branches: **paid loyalty commitments** — settlements, hush payroll, war
  pay, severance, the shop-2 manager's stake. Every branch turns "spend
  money on people" into a survival input (case dormancy, war effectiveness,
  escrow price, second-shop viability). Retention tuning should build that
  primitive once, not four flavors of it.

### 2.7 Acceptance criteria — "the branches genuinely play differently," measurably

All criteria run on the existing protocol: 150 seeds per condition, the
versioned harness (`analysis/experiments.py` grows a `fork` study), results
into FINDINGS with the usual honesty rules. Bots remain instruments, not
tuning targets — thresholds below are falsification bars, and human play on
seeds 24/39/8 remains the test of fun.

1. **Act I is untouched — exactly, per seed.** Raw `state_to_dict` hashes
   cannot match across a save-version bump (v3 carries fields v2 never
   had), so equality is defined on three testable surfaces: (a) a
   **normalized legacy projection** — a harness function mapping v3 state
   onto the v2 field set (`shops[0]` flattened back to the old shop and
   stash fields, the evidence sum rendered as the old scalar Case, its
   records rendered as the old flag strings, v3-only fields dropped) —
   compared nightly against main, 150/150; (b) **RNG-stream equality** —
   every stream the two builds share serializes identically each night,
   and the new streams (`sitdown`, `brokers`, `war`) are provably undrawn
   pre-fork; (c) **action replay** — the bot's decision log is identical,
   and so is the ending. The §2.1 telegraph lines are the sole permitted
   transcript additions pre-fork, and they touch no state and draw no RNG.
2. **Reachability (revised rev. 7 — the 90% share was falsified and the
   criterion now tests its thesis).** The unmodified market bot reaches
   an open sit-down in ≥ 55% of seeds. The earlier "every chair present
   in ≥ 90% of open sit-downs" was measured at 87% over 150 seeds
   (88.2% over 1,000), with **every** absence an intentional calendar
   gate and none a Case gate — the flat share was at odds with the
   deliberate late-payoff gates, so the criterion is restated to test
   what it meant: **all four chairs must be present at the median and
   through the 75th-percentile payoff state** (measured: median payoff
   day 10, Q3 day 16 — both full tables), the **exact chair set at
   every documented boundary** (payoff 20/21/22/23/25/26) must match
   the §2.1 table, and the full-table share is **always reported**
   alongside, split by cause (calendar vs Case). Chair presence is
   measured on the complete computed offer set — the pure evaluator's
   verdicts — not on which menu entries are actionable in a given
   build (rev. 5). If ≥ 90% full tables ever becomes a product
   requirement, the branch calendars themselves must change — that is
   a design decision, not a harness one.
3. **Crash-freedom.** Chaos-monkey (`--auto`) forced down each branch × 150
   seeds completes every run; full unittest/ruff/mypy suite green.
4. **Divergence.** Four branch bots (minimal per-branch policies over the
   existing smart bot). Measured over post-fork days only:
   - *Straight Path bot (two cohorts, rev. 10):* the **natural-entry
     cohort** (the unmodified smart-bot baseline) holds covert revenue
     share < 5% after fork+2, the earned-exit band, and *remediation
     leaves the file lower than its unremediated twin in ≥ 60% of
     matched entries*; the **redemption cohort** (the frozen §3.1
     reference state, Case 31, entered through the real scene across
     world seeds) holds the original letter — **median ΔCase ≤ −5
     from fork day to end**, genuinely negative, with Case strictly
     below its fork-day value in ≥ 60% of runs: the first falling
     Case in the game's history, earned against the branch's own
     crime clock.
   - *War bot:* median target strength at end ≤ 50% of its fork-day value;
     pattern+physical evidence ≥ 50% of post-fork Case growth; **channel
     mix:** in successful runs no single damage channel (jobs / corners /
     ovens / the law) accounts for > 60% of strength destroyed; and a
     raid-only ablation bot trails the mixed bot's success rate by ≥ 15
     points — the anti-grind claim, tested directly.
   - *Partner bot:* combined legit revenue ≥ 1.5× the stand-pat control's
     by fork+8; points paid on schedule in ≥ 80% of runs.
   - *Escrow bot:* every in-branch run either closes exactly at fork+4 or
     reverts to stand-pat; closes in ≥ 70% of seeds. **Valuation is
     decision-sensitive, not formula-implied:** on matched seeds, a
     careful diligence policy (stash cleared before day 2,
     incident-averse choices) must beat a careless one by ≥ $1,000 at
     the median on the **final broker mark before severance** (rev. 7:
     walking money rewarded retaining illicit assets and punished
     burning cash), and flip the ending tier in ≥ 40% of matched seeds,
     unconditioned. (The earlier draft's price-vs-Case correlation is
     dropped: the pricing formula guarantees it, so it tested nothing.)
   - *Pairwise:* post-fork profile vectors with **eight components** —
     route-day %, raid-day %, covert $/day, legit $/day, staff spend
     $/day (wages + raises + settlements + war pay), remediation spend
     $/day, obligation outflow $/day (points + tribute), and
     incident/defense events per day — normalized per component across
     all runs; every branch pair must differ by ≥ 0.25 in at least **two**
     components.
   - *Ledger transparency:* every night, displayed Case equals the sum of
     visible evidence records (§2.3) — asserted by every bot in every run.
   - *Telegraphy, split by gate type (rev. 3):* for every
     calendar-withheld chair, the day-20/24 warning morning strictly
     preceded the payoff day (at least two playable decision days
     including the warning day); for every Case-withheld chair, either
     the Case-60 warning appeared on an earlier morning, or the
     transcript shows the same-night pre-action warning on the player
     act that crossed the threshold — wash, contraband route, raid, or
     aware-employee firing (§2.1) — or the crossing was a world event,
     in which case the eligibility snapshot and the scene's record-
     naming line must both be in evidence. No withheld chair may ever
     appear with none of the three.
   - *Snapshot integrity (rev. 4):* two paired scripted-console tests
     through the real night phase. (a) Pay the final dollar, then
     over-launder to Case 85, then lock up: the snapshot records 85 and
     both Case-gated chairs close — ordering buys nothing. (b) Pay and
     lock up at Case 65, then forced law/rival evidence to 85 before
     morning: the snapshot stays 65 and the offers stand — unless the
     Case reaches 100, in which case arrest wins and the fork never
     opens.
5. **Stakes are real (ablations).** Each branch bot's branch-good ending
   rate lands in a 25–70% band (no auto-win, no hopeless chair), and
   removing the branch's stated counterplay drops it by ≥ 20 points:
   a Straight Path bot that never settles witnesses or retains counsel; a
   War bot that raids on cooldown ignoring alertness; a Partner bot that
   pays points from pizza margins only; an Escrow bot that keeps stash on
   premises. If an ablation *doesn't* hurt, the pressure is decorative and
   the branch fails review.
6. **The control stands — exactly, per seed (two-trace contract,
   rev. 5).** For every seed, a flag-on stand-pat run and a flag-off run
   must match — not a matching distribution, the same runs. The earlier
   wording left a contradiction unresolved: the sit-down scene is made
   of prompts, so a stand-pat run cannot produce a byte-identical
   decision log while also answering the scene. The contract is
   **normalized exact equality over two channels**, not a subsequence
   test (a subsequence comparison would tolerate missing, duplicated or
   reordered gameplay prompts):
   - Ordinary gameplay prompts stay in the **game trace**, in the exact
     current event shape — no namespace field is added to existing
     entries, so `golden_act1.json` remains valid untouched. Sit-down
     decisions ride a separate console channel
     (`scene_menu(namespace, prompt, options)`, delegating to `menu()`
     everywhere except replay tooling) and land in a namespaced
     **scene trace**.
   - The flag-on stand-pat game trace must equal the flag-off game
     trace **exactly — event for event**, full lists compared, not
     merely by digest.
   - The scene trace is asserted independently: every event in the
     sit-down namespace, and exactly the permitted interaction — one
     chair selection choosing stand-pat and one confirmation, nothing
     else. A flag-off run's scene trace must be empty.
   - Ending, nightly legacy projection and shared RNG streams remain
     exact, per criterion 1; `sitdown`/`brokers`/`war` stay provably
     undrawn in stand-pat.
   - The scene consumes **no bot decision RNG**: bots answer scene
     prompts through a deterministic handler (the scene guarantees its
     last option always progresses), and the bot's RNG state is
     asserted identical immediately before and after the scene —
     otherwise the extra menu would shift every later bot choice even
     with the game streams untouched.
   - **Existence, not just equivalence (rev. 6).** The gate must fail
     when the sit-down is missing, not only when something else moved.
     Whether a scene is owed is derived from the FLAG-OFF nightly
     timeline alone — debt_paid_day, the day, and whether the run had
     ended — never from fork code or its snapshot; expected scenes must
     equal observed scenes, pair by pair. A fired scene is compared
     against a **frozen, versioned scene schema** — exact namespace,
     prompt, complete ordered options and answer, event for event,
     literal in the harness (never imported from the scene module, so
     drift fails the gate exactly as a drifted engine fails the
     goldens; changing the scene lands with a schema version bump).
     Mutation regressions pin the failure modes: a disabled scene, a
     missing/extra/reordered event, a changed prompt, option, answer or
     namespace must each fail a pair that reaches the table.

### 2.8 Canon and invariant compliance

Against the ten invariants (`01-north-star-brief.md`): (1) shared
resources — sharpened everywhere: two shops on one roster, wagon contested
three ways, war pay vs. payroll; (2) functional shop — the Straight Path
and the Quiet Sale make the restaurant the *goal*, not just the cover;
(3) coupling — each branch is a coupling turned into a campaign (raid
damage ↔ cover in the War; demand ↔ price in the Sale); (4) Dope Wars fast
loop — preserved in War/Partner; deliberately *wound down* in the Straight
Path with temptation offers keeping the pull alive (this is the canon
endgame "abandon the underground trade," so winding down is the point);
(5) tycoon long loop — the Partner branch is canon's Act II verbatim;
(6) raids emerge from the economy — war raids are campaign moves priced by
alertness/pattern/carry, not missions; (7) telegraphed counterplay — the
sit-down is telegraphed across Act I (§2.1), every gate is explained, war raids
keep the 2-night warning, Burned Out requires two visible prior states;
(8) explainable outcomes — the mark's terms, the chairs' gates, and the
evidence ledger are all shown; (9) legal/illegal tension — points must be
earned dirty, exits must be earned clean, neither side goes passive;
(10) dual-use — counsel enforces the ceiling it protects you from,
advertising grows the cover you may be dismantling, the second shop doubles
both laundering and exposure.

**Deviations to record in `docs/canon/README.md` if approved** (per its
standing rule: argued explicitly, recorded there):

1. *The Sit-Down is an interpretation of canon, not canon arriving.*
   Canon describes acts and exit-shaped endgames but nowhere a hard,
   mutually exclusive choice scene — the pitch's progression reads as
   continuous growth. The hard fork is a new reading, chosen for
   legibility, weight, and measurability (§1.4), and it is recorded as a
   reading rather than smuggled in as inevitability.
2. *Act II compressed into the original thirty days.* Canon's acts read
   as open-ended; this design keeps `DEBT_DUE_DAY = 30` as the campaign
   end for every branch (§6.1 argues why, and what would change it
   later).
3. *The Quiet Sale ends runs early* — a smaller note under the same
   entry.

---

## 3. The first five days of each branch

**The reference save** (one common baseline so divergence is visible; all
numbers illustrative but consistent with a median market-style run): final
payment of $3,900 lands on **day 13** at night. Day 14 morning: clean
$1,340 · dirty $610 · stash 6 Special Mushrooms + 4 Extra Oregano ·
warehouse rented (12 Extra Oregano, $800 cash) · reputation 24 · Case 31
(flags include one over-ceiling wash, Marcus's detective chat, a pattern
premium of 3) · heat: Old Harbor 22, University 15, Little Sicily 8,
Meadows 30 · staff: Rosa (driver, read in, morale 6, Meadows familiarity
4), Tony (cook, not read in, morale 5), Bee (counter, observant, not read
in, morale 6), Marcus (driver, read in, morale 4), Angelo (muscle, read in,
morale 7) · Vinnie: strength 58, relation −45, alertness 2.7 ("wary") ·
Sal: strength 60, relation −5, alertness 0. Sit-down day 14, `R = 17`: all
four chairs present.

**Day 14, all branches:** the sit-down. Espresso at Carmine's corner table.
Four chairs described with their gates, prices, and what each forecloses;
the Case band and calendar shown beside each. One choice, confirmed twice.

### 3.1 The Straight Path, days 14–18

- **D14.** After choosing: the book-burning scene — the coded-customer list
  goes in the pizza oven, and the screen lists what just became impossible
  (the supplier van, the coded order board, raids) and what little remains:
  `disposal runs left: 3`. The morning menu is visibly different: "Plan
  tonight's route" is now **Disposal**, and the clean-days clock says all
  liquidation must finish by day 25. First decision: 22 units across two
  stashes. You fire-sale the warehouse oregano to Sal's man (40% of book,
  +8 Sal relation, crime clock resets) and keep the mushrooms for a
  decision you're not ready to make. Night: retain counsel ($150/day) —
  the over-ceiling record is first in the queue.
- **D15.** NEWS: concert in the Meadows — hot honey prices climbing. The
  temptation offer lands in its own voice: a Meadows contact wants your
  mushrooms at 1.6× book — and the offer card says what it is: *new trade,
  not disposal.* Accepting resets the clean-days clock and spends no
  disposal run; a disposal run tonight would move the same mushrooms at
  0.7× board through strangers. Full margin under new evidence, a haircut
  under the old rules, or the oven. Marcus corners you by the walk-in —
  morale 4, read in, and no route work left for him. Settle him out
  ($540 severance, his records go dormant) or keep paying a driver with
  nothing to drive. You settle. Bee watches him go.
- **D16.** Counsel's third day: the over-ceiling record contested, −60% —
  **Case 31 → 27, the first time that number has ever gone down.** Vinnie
  papers the neighborhood with coupons; with no stash to raid he attacks
  the order book instead. You answer with the new Advertising action
  ($300 clean) and a gourmet pantry buy — the critic tour is rumored.
- **D17.** A squad car parks across the street; two officers stop in for a
  slice and look at everything. The walk-in holds flour. No flag — but Bee
  rechecks the till twice that night (morale −1): searches now attack
  people, not stash. The remaining mushrooms: burn them, or Sal's man
  again at 40%. Tony watches the oven door either way.
- **D18.** Payroll day math is the whole morning: counsel + advertising +
  five wages against pizza margins — clean $400 and falling. The exit
  readout (new night line): stock 0 · dirty $180 · Case 27 · rep 31 ·
  witnesses content · clean days 1 of the 5 the goal demands. Twelve days
  to make reputation 45 on margherita alone.

### 3.2 Carmine's Partner, days 14–18

- **D14.** Site selection screen — three district cards with traffic /
  underground / patrol / owner. University Hill: volume and no owner.
  Little Sicily: reputation country, Sal's porch. The Meadows: the best
  covert demand in the city, and Vinnie's floor. You take University Hill.
  The capital ledger posts: $20,000, itemized. Points card: $2,500 due day
  19, then every 5th day, unmarked preferred.
- **D15.** Permits ($1,500, clean — paperwork is always clean) and
  build-out begin. Staffing screen for two addresses: Rosa anchors Old
  Harbor; Marcus will drive University Hill — which means reading no one
  new in yet means shop 2 runs *straight* at first. Priya's résumé is on
  the counter (ambitious, two-star kitchen): shop 2 needs a cook.
- **D16.** Opening day. Shop 2's own morning block appears: reputation 20,
  University traffic, its own pantry (standard), its own order book — and
  its own believable ceiling, currently tiny. Carmine's nephew eats a free
  slice and looks at the register. First cross-shop decision: the second
  wagon exists, but a *covert* University route needs a read-in driver you
  don't have there.
- **D17.** Two-route morning: Rosa runs Meadows product (concert tail),
  Marcus runs University pizzas-only — cover building, no cargo. Sal's
  voice on the phone, friendly: expansion is noticed. A University
  crackdown rumor: patrol 15 would land on your new address. Points due in
  two days; dirty on hand $610.
- **D18.** The scramble the branch is about: $2,500 by tomorrow. Read
  Marcus into shop 2's real business tonight (a new witness, a new covert
  ceiling) or strip Old Harbor's route take and pay points from pizza
  margins, starving the build. You read Marcus in; his wage rises; the
  Case has a new name in it. Night ledger: two rents, seven wages, and a
  man who never sends invoices.

### 3.3 The Harbor War, days 14–18

- **D14.** You name Vinnie at the table; Carmine keeps eating. The **war
  board** replaces the market board's top panel: VINNIE — strength 58,
  security *wary*, ovens intact; SAL — posture *merchant* (sells to both
  sides, tips no one yet); your crew — Rosa 6/10 morale, Angelo fit,
  Marcus shaky; war pay +$20/day × 3 read-in names, effective tonight.
  Relation locks at vendetta: the tribute and truce options grey out
  permanently.
- **D15.** Opening move: sabotage — Angelo and Marcus wreck the ovens at
  Vinnie's Pies (security still *wary*; the pattern warning prints: next
  success +3 Case). Strength 58 → 48; ovens down 4 days — his cover is
  gone, his routes are naked, and the war board opens the window: *corner
  damage doubles while his ovens are cold.* Heat Meadows 30 → 42. His
  answer telegraphs by morning: unfamiliar cars, twice.
- **D16.** The counter-raid warning counts down; the defense choice is the
  old screen with new stakes (war-scaled crew). You empty the stash into
  the wagon and let them find crumbs — damage days 2, and the war board
  logs it: *his move spent, your shop limping, his ovens bleeding
  (strength 48 → 46).* Sal raises an "insurance" offer: $800/week to stay
  a merchant. Decline, and remember the Case has a second author now.
- **D17.** Tempo push: Rosa runs 12 units into the Meadows while his cover
  is down — his corner customers take your number, and the window doubles
  the damage: −4 strength tonight without a door being forced. Meadows
  heat 42 → 51: the war board colors the district amber — *take it hot and
  you take ash.* Angelo's knuckles heal; Marcus asks if this is forever.
- **D18.** The board's damage ledger reads *jobs 10, ovens 6, corners 4* —
  strength 38 before tonight. Second job: the warehouse, security now
  *hardened* (alertness 4.7 — your sabotage taught him). Quiet odds
  visibly worse (−0.19); the pattern premium warning reads +4. It goes
  loud in the cage; Angelo takes a bad one — out 3 days. Haul: 9 units,
  strength 38 → 26. Case 31 → 39, all of it pattern and physical —
  **nothing on that number ever comes off.** The bottom line becomes the
  branch: *strength 26, Case 39, twelve days* — and the alertness curve
  has already priced job three down to a bad bet; the rest of this war
  belongs to the corners and, maybe, the woman in the gray suit.

### 3.4 The Quiet Sale, days 14–18

- **D14 — diligence day 1.** The broker's card, itemized: base $3,000 +
  rep 24 × $140 = $3,360 + upgrades $1,850 × 0.5 = $925 → gross $7,285;
  less Case 31 × $45 = −$1,395 → **mark: $5,890.** One clause sits dormant
  and visible: −20% if any rival reaches relation ≤ −50 or a live raid
  warning — Vinnie is at −45, one bad night from arming it. Terms: marked
  each morning, incidents reprice −10 to −25%, two incidents end it,
  closing on the morning of day 18. His man walks the shop *this
  afternoon* — the mushrooms in the walk-in are an incident from hour one,
  so they go to Sal's man before noon. Or stand pat now and keep the
  sandbox.
- **D15 — diligence day 2.** The register must be boring: laundering is
  off all week. The oregano question: burn it for the clean close, or
  truck it to the warehouse at dusk — the truck at the rolling door is
  itself a 20% incident while the buyer's man watches the neighborhood,
  rent keeps drawing dirty cash, and the card says what off-site holdings
  make you: *a seller who kept the trade.* You send the truck anyway; the
  20% doesn't fire. Otherwise a clean day: the mark holds at $5,890.
- **D16 — diligence day 3.** Word reaches Vinnie: a note under the door —
  $1,200 or "the buyer learns what he's buying." Refusing risks the raid
  telegraph going live before closing, which arms the −20% clause — about
  −$1,200 on its own. You pay quietly from dirty; the price holds. Bee
  figures out what the man in the good suit was measuring; morale −1, and
  she asks what happens to *them*.
- **D17 — diligence day 4.** Staff day. Severance line-items on the
  closing sheet: $300 a name, or nothing and the epilogue remembers. The
  critic tours — one last gourmet service lifts rep 24 → 27; the mark
  reprices +$420 to $6,310. A squad car slows, doesn't stop. The walk-in
  holds flour and receipts.
- **D18 — closing morning.** Final mark $6,310. Sign: settlement + clean
  $1,900 + the warehouse's $800 + twelve units of oregano out the back
  gate at book value ($540, as the epilogue prices all retained stock) ≈
  $9,550 in walking money — and the ending card says what it cost:
  contraband and unlaundered cash left with you, so this is **"Sold the
  shop, kept the trade"** — capped at the modest tier, the file still open
  on your name. The clean close was worth less money and a better life;
  that arithmetic *is* the branch. Or tear it up: buyer gone forever, shop
  yours, twelve flat days of stand-pat left, and Rosa saw the suit too.

### 3.5 Why these are different games

| Branch | Core loop | Screens it alone has | The clock | A misplay looks like |
| --- | --- | --- | --- | --- |
| Straight Path | dispose / defend people / polish the shop | Disposal, counsel's queue, exit readout | Case & rep vs. day 30 | firing a witness to save wages |
| Carmine's Partner | staff two addresses / earn points dirty | site cards, shop-2 block, points card | every 5th night | paying points from pizza margins |
| Harbor War | tempo strikes / defend / pace alertness | war board, capture log | strength vs. Case | raiding on cooldown into *hardened* |
| Quiet Sale | hold steady / hide everything / price the exit | broker's mark, diligence sheet | 5 days, marked daily | one walk-through with stash on site |

Same engine, four verbs sets, four clocks, four ways to lose. The
walkthroughs share exactly one screen: the sit-down.

---

## 4. Risk register

| # | Risk | Class | L | I | Mitigation |
| --- | --- | --- | --- | --- | --- |
| R1 | Content dilution: four thin branches instead of one deep game — the canon's own warning ("do not solve lack of depth by adding content") | design | M | H | Branches reuse existing systems ~90%; only Escrow adds a wholly new loop and it is 5 days long; phased delivery (§7) ships one branch at a time behind studies |
| R2 | Evidence remediation becomes a slider — the Case's money-doctrine twin broken | design | M | H | Typed kinds with physical/pattern immune; 25-point cap; visible institutional-suspicion record instead of a hidden floor; arrest latches at accrual, irreversibly; regression: Act I replay produces identical Case totals |
| R3 | Hard fork reads as railroading / "pick your DLC" | design | M | M | State-dependent chairs, explained gates, stand-pat null branch, temptation offers keeping other lives visible |
| R4 | Branch balance unknowable on paper; a chair dominates or is hopeless | design | H | M | §2.7 bands (25–70%) + ablations are falsification bars before human tuning; bots stay instruments |
| R5 | Straight Path is boring (no routes, no raids) | design | M | H | Disposal pricing, temptation offers, witness economy, rival siege, advertising race — verified by the ablation: if skipping its verbs doesn't hurt, it *is* boring and fails review |
| R6 | Multi-shop refactor blast radius: demand/cover/laundering pipeline is `HOME_DISTRICT`-hardcoded and invariant-tested | tech | H | H | Ship Partner branch **last** (§7); refactor to a shop *collection* with shop-local state, schema landing in save v3 during P0 as a list of one (§5) so Act III adds elements, not migrations; War-branch capture deliberately does *not* reuse multi-shop (§6.4) |
| R7 | Save v3 churn and determinism across branches | tech | M | M | Field-completeness guard already forces coverage; new persistent streams (`sitdown`, `brokers`, `war`) keep world channels untouched; no player-facing saves exist yet (`save.py` docstring), so no migration burden |
| R8 | Issue #4 (noise-timeout awards objectives) poisons the War branch economy | tech | H | H | Hard prerequisite: fix + regression through the actual raid path before War work starts (§7 P0) |
| R9 | Ending combinatorics: 8 new IDs × branch flavors bloat `epilogue` | tech | L | M | One dispatcher arm per branch; graded text inside one ending ID where possible (Sold tiers, the Won-the-War arrest arm) |
| R10 | Bot fleet cost: 4 branch bots + ablations + control ≈ 10 conditions × 150 seeds per study round | tech | M | M | Branch bots are thin policies over the existing smart bot; post-fork days only; `fork` study runs branches independently |
| R11 | Late-payoff players never see Act II and call it missing content | product | M | L | The scene says why the chairs are empty; FINDINGS shows median payoff is day 12–15, so the median player forks |
| R12 | Escrow's 5-day runs skew aggregate stats (net worth, arrests) if pooled naively | tech | M | L | Report per-branch tables; never pool across branches in FINDINGS |
| R13 | War's economic channels turn raid grinding into route grinding | design | M | M | Per-night corner cap, the existing oversell glut, and turf heat already price repetition; the §2.7 channel-mix criterion (no channel > 60%) catches degenerate strategies in either direction |

## 5. What the engine must change

Ordered roughly by blast radius, smallest first:

1. **`raids.py`** — fix issue #4 (the "Time's up" break must mark the job
   failed, not fall through to `_payoff`; plus the ties-to-even display nit
   on the pattern premium). Prerequisite for everything raid-adjacent.
2. **`models.py`** — `State.act`, `State.branch`, `State.branch_state`
   (typed per-branch dataclass, not a loose dict — save completeness must
   see its fields); `case_flags` → typed evidence records with magnitudes,
   including the institutional-suspicion record (§2.3); `state.case`
   becomes derived (sum, clamped) with the Act I-identity regression of
   §2.3, and the arrest latch moves into the accrual path itself. **The
   shop becomes a collection now, not later:** `State.shops` — a list of
   `Shop` entries, each owning its district, pantry, stash (the top-level
   `shop_stash` moves inside), reputation, damage, upgrades and revenue
   ledger — written as a list of one throughout Act I. Hard-coding a
   second sibling field would schedule Act III's migration today.
3. **`save.py`** — `SAVE_VERSION = 3`; evidence records, act/branch state,
   the shops collection (a list of one until the Partner phase — shop 2
   then arrives as data, not as another version bump), new RNG streams. No
   migration path needed yet (engine-layer only), but say so in the
   version bump commit.
4. **`rng.py`** — persistent streams `sitdown`, `brokers`, `war` (player-
   facing dice); world channels untouched so every Act I study reproduces.
5. **`game.py`** — `run()` loop: the sit-down hook after night when
   `debt == 0 and act == 1`; escrow's early termination (a run may now end
   before `last_day`); `_check_endings` becomes the precedence ladder of
   §2.5, with the arrest latch already applied upstream at accrual time;
   `broke` condition rework (its `debt > START_DEBT * 2` clause is
   unreachable post-payoff — clean insolvency needs its own test);
   `epilogue` branch arms.
6. **`phases.py`** — morning header shows the branch goal line instead of
   the Carmine line; branch verb injection (Disposal, counsel, settlements,
   advertising, war board, diligence sheet); night ticks (points due, war
   pay, escrow marks). Pre-fork, the telegraph channel of §2.1: payment
   remarks in `_pay_debt`, the day-20/24 calendar warnings, the Case-60
   line, the ledger clause in the header — transcript-only, no state
   change, no RNG draw. The debt-interest guard already handles payoff.
7. **`rivals.py`** (with `routes.py`) — war posture (vendetta lock,
   aggression multiplier, side-picking by disposition, insurance offers);
   the economic-warfare channels of §2.4.3: corner diversion on route
   sales in owned turf, with the nightly cap and the oven-outage doubling,
   plus the ledger-to-the-law option; capture-on-strength-0 effects
   (district underground transfer).
8. **`shop.py`** — the big one, deferred to the Partner branch phase:
   every function takes a `Shop` entry from the collection instead of
   reading the module-level `HOME_DISTRICT` and a single `state.shop`;
   demand, ceiling, shift and reputation become shop-local. Every canon
   invariant test on the pipeline must pass parameterized before a second
   entry ever exists (the schema itself already landed in P0, items 2–3).
9. **`bot.py` / `bench.py` / `analysis/experiments.py`** — four branch
   policies, the `fork` study (divergence, ablations, control), per-branch
   FINDINGS tables.
10. **`docs/canon/README.md`** — record the accepted deviation (§2.8) when
    approved.
11. **New module `acts.py`** — the sit-down scene, chair gating, branch
    state constructors; keeps `game.py` from swallowing the fork.

## 6. Unresolved product decisions (with recommendations)

1. **Calendar: keep day 30, or extend per branch (e.g., Partner to day
   45)?** *Recommend: keep 30 for v1.* It preserves the game's identity
   ("a thirty-day debt deadline" is canon's Act I frame), keeps every
   study comparable, and the Partner branch ending mid-story is a feature
   — it points at Act III. Extension is save-compatible later; the typed-
   evidence work (§2.3) is what makes a longer calendar *possible* at all.
2. **Are the sit-down offers really once-only?** *Recommend: yes.* Expiry
   is what makes the choice a choice. The one softening worth considering
   later: the broker callable once from stand-pat at −20% — deferred, not
   designed.
3. **Constants throughout** (25-point remediation cap, the
   institutional-suspicion record at 10, counsel −60% on paper,
   settlements −50% on witnesses, three disposal runs, the corner-damage
   rate and caps). *Recommend: adopt as placeholders and let the §2.7
   ablation studies move them.* The structure (typed, bounded,
   physical/pattern immune, arrest latching at accrual) is the decision;
   the constants are tuning.
4. **Should War-branch capture grant the rival's shop as a second branch?**
   *Recommend: no in v1.* Capture transfers the district's underground
   only. Unifying capture with the Partner branch's multi-shop machinery is
   the right v2 — after that machinery exists and is tested (R6).
5. **Second-shop district: may the player open on a rival's turf?**
   *Recommend: yes* — with the stated commercial-war consequences. Removing
   the option would delete the branch's best dual-use decision.
6. **Points denomination** ($2,500/5 days, dirty preferred). *Recommend:
   adopt; verify against the Partner ablation* — the trap (his money keeps
   you criminal) only works if pizza margins alone genuinely starve growth.
7. **Can war be declared from stand-pat later** (outside the sit-down)?
   *Recommend: yes, as the one post-sit-down branch entry* — raids already
   exist there, and "the declaration changes the rules of engagement" is
   coherent at any date with `R ≥ 8`. Hold for v1.1 if it complicates the
   trigger tests.
8. **Escrow buyer identity** (Sal's straw man vs. out-of-towner) affecting
   price or only flavor. *Recommend: flavor only in v1;* a Sal-relation
   price kicker is a cheap v1.1 hook.

## 7. Suggested implementation phasing (post-review)

- **P0** — issue #4 fix (independently authorized by review, kept out of
  this design-only branch); typed evidence refactor with the Act I-identity
  regression and the accrual-time arrest latch; save v3 including the
  shops-collection schema (a list of one); the pre-payoff telegraph lines.
  Player-visible change: telegraph lines only; every existing study
  reproduces per seed. *Gate: FINDINGS round-5 baseline identical to
  round 4 — per-seed state hashes, not distributions.*
- **P1** — sit-down + stand-pat + the Quiet Sale **behind a feature flag**
  (the cheapest complete branch: proves trigger, chair gating, early
  termination, one new ending family — but Sale-versus-stand-pat does not
  validate the fork's central promise, so the flag stays down). *Gate:
  criteria 1–3 + escrow rows of 4–5, run flag-on in the harness.*
  **Split into two reviewable PRs (rev. 5):** *P1a* — the replay
  decision recorded, `GameConfig`, the unchanged flag-off golden gate,
  the two-channel paired harness (built before the scene),
  `SitdownSnapshot` with lock-up capture and migration default,
  `BranchState` constructors and validation, deterministic chair
  evaluation, scene rendering, and stand-pat; gate: flag-off golden
  300/300 plus flag-on stand-pat paired equality. *P1b* — after P1a's
  review: the Quiet Sale itself (brokers stream, diligence clock,
  valuation and incidents, early termination, endings), its bots,
  studies, and FINDINGS round 8's body.
- **P2** — the Straight Path (counsel, settlements, disposal runs,
  advertising). **The Sale flag lifts when this gate passes** — the fork
  reaches players only once at least two active branches exist. *Gate: the
  negative-ΔCase study and its ablation.*
- **P3** — the Harbor War (war posture, war board, capture-lite).
  *Gate: war rows of 4–5; raid-pricing decline curve re-verified at war
  cadence.*
- **P4** — Carmine's Partner (multi-shop refactor last, alone in its
  phase). *Gate: full §2.7 battery + human play on seeds 24/39/8, written
  up honestly in FINDINGS.*

Each phase ends with the standing workflow: tests + ruff + mypy, the
relevant studies rerun, FINDINGS updated (including retractions if the
paper design's claims don't survive contact), commit, push, review.

---

## 8. Revision record

**Revision 2** responds to the design review that approved the hard fork,
the four chairs, stand-pat, and the 30-day v1 calendar, and required nine
corrections before implementation:

1. *Fork knowledge arrived too late* → a pre-payoff telegraph channel:
   payment remarks, day-20/24 calendar warnings, the Case-60 line, the
   ledger clause — plus a transcript-verifiable warning-before-gate
   acceptance criterion (§2.1, §2.7).
2. *Case terminal semantics* → arrest latches at accrual time,
   irreversibly; counsel/settlements are active-branch unlocks only, so
   stand-pat stays a per-seed-identical control; the hidden floor became
   the visible institutional-suspicion record, with displayed Case ≡ the
   visible ledger asserted nightly (§2.3, §2.7).
3. *End-state coverage incomplete* → a global precedence ladder and
   exhaustive per-branch day-30 matrices; new endings Half Measures, On
   the Hook, and A Long War; simultaneous success/arrest resolved — arrest
   wins, with the Won-the-War text arm (§2.5).
4. *Straight Path contradictions* → the final-raid clause removed (feuds
   settle with civilian tools); disposal runs explicitly bounded (three,
   counted, liquidation-only, at a haircut); the goal gains open-feud and
   five-clean-days terms; temptation offers defined as new trade, distinct
   from disposal (§2.4.1).
5. *War's mixed strategy unimplemented on paper* → four named damage
   channels with numbers: corner diversion (−0.15/unit, −4/night cap),
   oven-outage doubling, ledger-to-the-law (−20, their case); victory
   arithmetic showing jobs as a minority of damage; channel-mix and
   raid-only-vs-mixed acceptance criteria (§2.4.3, §2.7).
6. *Quiet Sale arithmetic and clock wrong* → worked example corrected
   ($7,285 gross, $5,890 after Case; Vinnie's −45 shown as a dormant, not
   triggered, war clause); the five-day clock reconciled (sit-down day =
   diligence day 1, closing at fork+4); the walkthrough recalculated
   (§2.4.4, §3.4).
7. *Warehouse disposal dominant* → off-site moves cost an incident risk
   and rent; closing with contraband or dirty cash anywhere reclassifies
   the ending as "Sold the shop, kept the trade," capped at the modest
   tier with the file open (§2.4.4).
8. *Acceptance tests too permissive* → per-seed exact state-hash equality
   for pre-fork and stand-pat; median ΔCase ≤ −5 for the Straight Path;
   eight-component action-mix vectors with two-component separation; the
   tautological price–Case correlation replaced by matched-counterfactual
   and tier-flip tests (§2.7).
9. *Multi-shop architecture too narrow* → a `State.shops` collection with
   shop-local district, pantry, stash, reputation, damage, upgrades and
   revenue; the schema lands in save v3 during P0 as a list of one (§5).

Doctrine notes adopted: the hard, mutually exclusive Sit-Down is recorded
as an *interpretation* of canon rather than canon arriving (§2.8); the
Quiet Sale ships behind a feature flag until the Straight Path passes its
gate (§7).

**Merge-preparation pass** (same review cycle, pre-merge), responding to
the re-review of revision 2:

1. Raw `state_to_dict` hashes cannot match across a save-version bump, so
   the paired-run equality criteria were reformulated as three surfaces:
   normalized legacy projection, shared-RNG-stream equality (with the new
   streams provably undrawn), and action-replay + ending identity (§2.7
   criteria 1 and 6).
2. Telegraph verification split by gate type: calendar gates need two
   days' notice; Case gates — which can slam shut in one night — need
   either a prior Case-60 warning or a same-night pre-action warning on
   the act that crossed the threshold (§2.1, §2.7).
3. The Partner second shop is declared and tested as always-open (the
   only ways to lose it end the run), so "shops open" left the day-30
   matrix, which is now the points ledger alone — no third state can
   exist (§2.4.2, §2.5).
4. The Quiet Sale's unexplained $130 drift was removed — the mark moves
   only when its inputs move — and retained stock in walking money is
   priced at base book value, as `net_worth()` already prices stock; the
   walkthrough recomputed ($5,890 held → $6,310 after the critic →
   ≈ $9,550 walking) (§2.4.4, §3.4).

Cleanups from the same pass: R9's ending count corrected to eight; the
institutional-suspicion record now tops itself up on every sub-floor
remediation, keeping the displayed-Case ≡ visible-ledger identity exact.

**Revision 3** responds to the review of the telegraph implementation
(PR #9), which found one coverage gap and one specification seam:

1. *Same-night Case protection covered only laundering* → the pre-action
   warning generalizes to every evidence-capable player act committed
   while payoff is in reach: exact arithmetic for the wash, plan-time
   unconditional warnings for contraband routes and raids (their
   accrual depends on in-act outcomes, so the superset is by
   construction), a sharp within-6-of-a-gate warning before firing an
   aware employee. Reproduced through the real phases: a ride-along
   bust (8 + 6 resistance + 6 owner-in-vehicle + 0.3/unit) jumps the
   Case from 55 past 70 on payoff night with no §2.7 arm satisfied
   (§2.1).
2. *Post-payoff accrual could empty a chair retroactively* — the rival
   and law phases run after `_pay_debt` but before the sit-down morning
   → the eligibility snapshot: chairs are frozen at the moment the debt
   reaches zero; later evidence still counts toward the Case and arrest
   still outranks the fork, but the table cannot change after the
   payoff decision (§2.1).
3. *"At least two days" was false at the boundary* — payoff day 21
   withholds the Partner chair with the day-20 warning only one
   calendar day earlier → the criterion is restated as "the warning
   morning strictly precedes the payoff day: at least two playable
   decision days including the warning day," which the fixed day-20/24
   beats satisfy at every boundary (payoffs 21, 23 and 26); the beats
   themselves are unchanged (§2.1, §2.7).
4. *World events are named as a residue, not silently excluded* — no
   pre-action warning is possible for non-acts; pre-payment same-day
   world-event crossings are answered by the scene naming the closing
   record, post-payment ones by the snapshot; the §2.7 criterion gains
   the explicit third arm rather than claiming coverage it cannot have
   (§2.7).

**Revision 4** responds to the re-review of revision 3, which found the
snapshot exploitable and one warning window too narrow:

1. *A payment-time snapshot rewards action ordering* — pay the final
   dollar at Case 65, over-launder to 85 afterward, keep both
   Case-gated chairs, since rev. 3 explicitly protected post-payment
   washes → the snapshot moves to **lock-up**: frozen when the player
   leaves the settle-accounts menu, after every discretionary account
   action, immediately before the rival and law phases. Two paired
   snapshot-integrity acceptance tests added to §2.7: pay → over-wash →
   lock up closes the chairs at 85; pay → lock up at 65 → forced world
   evidence to 85 leaves the offers standing, arrest at 100 excepted
   (§2.1, §2.7).
2. *A route that funds the payoff warned nobody* — with on-hand cash
   short of the debt, the "one last run" that earns the final payoff
   money fell outside the warning window, leaving a player act with no
   earlier warning, no pre-action warning, and no world-event exemption
   → the route surface's reach test now counts tonight's plausible
   take, every term a supremum, documented in §2.1; overestimation only
   warns early (§2.1, §2.7).
3. *Raids re-measure at execution* — service revenue can put payoff in
   reach between scheduling and the job; eligibility is rechecked
   immediately before `run_raid`, printing the warning once (§2.1).
4. *Wording* — morning plans are intentions committed at service, so
   the criterion says "planned or taken," not "committed at plan time"
   (§2.1).

**Revision 5** records the P1 authorization decisions (P1a scope), made
before any fork code exists so the contracts precede the implementation:

1. *The stand-pat replay contradiction is resolved by normalized exact
   equality over two channels* — gameplay prompts keep their exact
   current event shape in the game trace (goldens untouched, no
   namespace field added to existing entries); sit-down decisions ride
   a separate namespaced `scene_menu` channel into a scene trace; the
   flag-on stand-pat game trace must equal the flag-off game trace
   event for event, with the scene trace independently asserted to
   contain exactly the permitted interaction. A subsequence comparison
   was considered and rejected as too permissive — it can tolerate
   missing, duplicated or reordered gameplay prompts (§2.7 criterion
   6).
2. *Bots answer the scene deterministically* — the scene handler
   consumes no bot decision RNG (asserted identical before and after
   the scene), and every scene menu's last option progresses so a
   deterministic last-option bot always completes the scene (§2.7).
3. *Flag architecture* — an immutable `GameConfig(fork_enabled,
   enabled_branches)` passed explicitly; the CLI may translate an
   environment variable, engine code never reads the environment; the
   config is not saved. The flag gates **entry** into the fork (the
   lock-up snapshot is captured only while it is on), never
   continuation: a save carrying a pending snapshot or `act == 2` is
   authoritative and resumes correctly whatever the launch
   configuration says — no save silently becomes unplayable after a
   flag rollback.
4. *Snapshot persistence carries primitives only* —
   `SitdownSnapshot(payoff_day, case_at_lockup,
   evidence_count_at_lockup)`; R, chair verdicts, withholding prose and
   the gate-crossing record are derived by a pure evaluator, never
   stored — one source of truth. Older v3 payloads load the field as
   None; no version bump.
5. *Chair visibility in partial builds* — all four chairs render with
   their actual gate verdicts; unimplemented chairs carry an explicit
   development-build marker outside the fiction, are not selectable,
   and never silently become stand-pat — an implementation limitation
   must not be converted into a permanent player decision. Criterion 2
   evaluates the complete computed offer set (§2.7).
6. *BranchState grows constructors and validation before any branch can
   be assigned* — per-chair constructors; `validate` raises ValueError
   (never assert — assertions vanish under optimized Python) at branch
   transition and save-load: dead fields at defaults, stand-pat implies
   no BranchState, active branches carry their required fields, mixed
   payloads rejected.
7. *P1 splits into P1a (foundation) and P1b (the Quiet Sale)* — §7.

**Revision 6** responds to the review of the P1a foundation (PR #10),
which found four contracts needing root-level correction:

1. *The paired gate could pass with the sit-down completely missing* —
   with `due()` disabled on a table-reaching run, every checked surface
   still passed, and the "exact" checker accepted wrong prompt and
   option text → the gate gains the existence check: expected scenes
   (derived purely from the flag-off timeline — debt_paid_day, day,
   ending) must equal observed scenes, and a fired scene must equal a
   frozen, versioned literal schema event for event. Mutation
   regressions cover a disabled scene, missing/extra/reordered events,
   and changed prompt/option/answer/namespace (§2.7 criterion 6).
2. *Frozen eligibility and the live Case were conflated* — the scene
   showed only the lock-up Case unless chair availability changed,
   though the design requires every disagreement visible → one
   canonical SitdownView (frozen Case + frozen verdicts + live Case +
   live band, with structured blockers: calendar/case/None, threshold,
   closing record), rendering any live/frozen difference even when no
   threshold moved, and marking open-but-dangerous chairs at Case ≥ 85
   (§2.1).
3. *Scripted scene input failed open* — an exhausted ScriptedConsole
   silently chose the last option twice and irrevocably committed
   stand-pat → scene_menu on ScriptedConsole requires an explicit
   answer and raises a dedicated ScriptExhausted before any mutation;
   progress-last remains the DETERMINISTIC BOT policy only, never a
   scripted fallback. Exhaustion pinned before chair selection and
   between selection and confirmation, with reload/replay verified
   (ui.py).
4. *GameConfig was not actually immutable* — a caller-held mutable set
   could grow enabled_branches after construction → normalized to
   frozenset in __post_init__, unknown branch identifiers rejected, and
   branch ids sourced from one canonical definition
   (models.BRANCH_ORDER / ACTIVE_BRANCHES) shared by config, validation
   and the scene.

Accepted judgment calls from the same review: 300 paired runs stand as
identity coverage (explicitly not the P1b reachability study);
calendar-first precedence when both gates fail, now encoded as the
structured primary blocker with a single prose reason; progress-last
stays a bot policy only.

**Revision 6 completion (the rendering boundary).** Re-review accepted
three of the four corrections outright and found the canonical-view fix
incomplete at its boundary: the renderer still derived policy outside
the view — danger warnings keyed to the FROZEN Case (a 65 → 90 morning
showed no Straight/War warnings), failed gates never stated their math
in-scene, and `build_view` carried a second copy of the Case fold (the
exact arithmetic the Python 3.12 summation failure came from). The seam
is now cut in one place:

1. One shared `fold_case(evidence)` primitive (models.py) is the only
   Case arithmetic — `State.case` and the view's live ledger both call
   it; the 3.12-divergent sequence regression asserts bit-identity
   through both paths and function identity itself.
2. `SitdownView` is complete: frozen eligibility, live risk
   (`live_danger`, keyed to the live Case), whether live conditions
   would alter the offers, and structured gate facts per chair — kind
   (calendar/case), requirement, actual, the chair's Case gate, reason,
   closing record.
3. The renderer consumes the view and nothing else — no re-evaluation,
   no reaching into gate tables.
4. Eligibility derives exclusively from the frozen Case; present danger
   exclusively from the live one.
5. Failed gates are stated in player language with their math: "needed
   10 days on the calendar; 9 remain" / "required a file below 70;
   yours read 72 when the books closed", plus the closing record.

Pinned: frozen 65 → live 90 (offers stand, both live-danger warnings
present); the Case-72 Partner rejection naming 70, 72 and the record;
the day-21 calendar rejection naming ten-needed/nine-remaining; the
shared fold on the 3.12-sensitive sequence.

**P1b implementation notes (pre-review).** The Quiet Sale landed with
three recorded deviations-with-argument and one measured criterion
miss, all awaiting review judgment:

1. *The incinerator is now an action.* §3.4's oregano question ("burn
   it for the clean close") had no mechanic — and without one the
   branch was unplayable: a stash-heavy month cannot leave through a
   24-bulk wagon before walk-throughs stack two incidents (measured:
   0% closes before the mechanic, 93% after, with the ablation still
   cratering at 10%). Each diligence morning with stock on premises
   asks: keep it and chance the walk, or burn it. In-branch prompt
   only; no identity surface moves.
2. *Severance is remembered by the closing transcript and the crew's
   morale* (the cheap choice costs −2 morale a head), not by a
   variant epilogue paragraph — a simplification to either bless or
   correct.
3. *No bespoke escrow extortion event.* §3.4's D16 note-under-the-door
   is carried by the existing machinery instead: rival extortion and
   raids continue during escrow, a landed raid is an incident, and the
   war clause visibly arms on a live telegraph or vendetta.
4. *The tier-flip bar misses as written, and the miss is a finding.*
   Careful-vs-sloppy tier flips run 19% (bar ≥ 40%) — but 31 of 52
   matched closes are cash-locked at kept-the-trade in BOTH runs:
   laundering is off all week by design, so > $200 of unlaundered cash
   at close is decided before the fork, and no escrow-week policy can
   flip those tiers. Among the 21 unlocked pairs, flips run 48% — over
   the bar. The criterion needs a ruling: condition it on
   tier-controllable seeds, extend "careful" to pre-fork cash hygiene,
   or give escrow a dirty-cash outlet. The dollar bar passes unhelped
   (careful-minus-sloppy median $2,179 ≥ $1,000).

**Revision 7** responds to the review of P1b (PR #11), which ruled on
the tier-flip question and found four further defects. The ruling: the
miss exposed a **missing player verb**, not a denominator problem — the
design says dirty cash must be "hidden or burned," and only contraband
could burn. Corrections:

1. *One escrow disposal primitive* (`escrow.incinerate`) now serves
   cash and contraband alike: destruction, never conversion — no clean
   cash back, no Case relief, no value. Exposed at the morning surface
   (the walk-in question) and the night account menu, which is now
   **branch-aware**: during escrow the menu offers "Burn dirty cash"
   instead of advertising a laundering allowance it would refuse after
   selection. Physicality preserved: warehouse cash must be trucked
   back before it can burn. The card shows the exact $200 tolerance and
   the projected closing classification every morning. The tier-flip
   bar stays **unconditioned at ≥ 40%**, tested on the original
   population with the missing verb supplied; the valuation dollar bar
   moves from total walking money (which rewards retaining illicit
   assets) to the **final broker mark before severance**.
2. *One valuation view* — the card had two sources of truth (displayed
   rounded inputs, computed truncated ones: rep 24.9 / Case 61.5
   printed "25 × $140 … 62 × $45" while computing with 24 and 61). An
   immutable `MarkBreakdown` now carries every priced term and the
   final mark under one explicit rounding policy (each term rounds
   once, nearest dollar; the war clause and incident repricing round
   against the running subtotal; final clamps at zero), the renderer
   consumes it exclusively, and the displayed dollars sum exactly.
3. *The closing is transactional* — the whole transaction validates
   before mutation; humane severance is on the sheet only when
   settlement plus clean can fund it (the reviewer's Case-84.9/rep-5/
   $0-clean repro produced −$600 cash and a negative recorded mark);
   cash and settlement never go negative; `escrow_mark` stays the
   buyer's price; the severance choice persists as closing outcome
   data (`BranchState.severance_paid`) and the epilogue acknowledges
   paid and unpaid alike. The transcript-only severance deviation is
   withdrawn.
4. *Ordinary escrow menus honor the safe-fallback contract* — the
   walk-in question's destructive option moved off the last position
   (an exhausted script was burning the whole stash), and regressions
   pin every new non-scene escrow prompt under an exhausted script:
   no assets destroyed.
5. *Reachability measured completely* — the harness now reports the
   full-table share, absence causes, chair sets at the median and
   75th-percentile payoff states, and the exact boundary sets; the 90%
   share is recorded as falsified (87% at 150 seeds, 88.2% at 1,000,
   all absences calendar-gated) and criterion 2 is restated to test
   its thesis (see the criterion text).

Deviation rulings from the same review: the incinerator action is
accepted, folded into the disposal primitive; the transcript-only
severance memory is rejected and replaced with persisted outcome data;
the absent bespoke D16 extortion is accepted (measured: in 82 careful
entries, 33 saw an escrow-time extortion, 28 a new raid telegraph, and
the war clause armed at some point in 40).

**Revision 8** records the final P1b review ruling and the last three
seams, made on paper before implementation:

1. *Constants ruling on the tier-flip bar.* The mark formula and the
   $10k/$25k ending thresholds stay unchanged; **first-incident
   repricing rises from −10..−25% to −20..−35%, drawn as whole
   percentage points** (the displayed rate is thereby exact); the
   second incident still collapses. Rationale: this lever changes the
   consequence of the behavior under test — moving tier boundaries
   would mostly relabel identical outcomes, and scaling the whole mark
   would change the chair's value against future branches. Reviewer
   counterfactual (with the careful bot retaining the permitted $200):
   150 seeds → 45% flips, median mark advantage $2,370; 500 seeds →
   43.1%, $2,445. Close behavior unchanged; only the price of a
   diligence breach becomes consequential.
2. *Negative valuation subtotals must not become credits.* At rep 5 /
   Case 84.9 with the war clause armed and an incident booked, the
   card rendered "--$24"/"--$15" — percentage deductions against a
   negative subtotal. The raw subtotal clamps to zero BEFORE
   percentage deductions, the floor is carried explicitly in the
   MarkBreakdown and rendered ("subtotal below zero; the mark floors
   at $0"), and war/incident terms are never negative. The exact
   combination is pinned.
3. *Severance outcome taxonomy.* A bare amount collapsed distinct
   outcomes (deliberate refusal, unaffordability, no crew) — a
   crewless close still printed "the crew found out." The closing
   persists a real discriminator — pending / paid / declined /
   unaffordable / not_applicable — alongside the amount and the
   closing headcount; the epilogue drives from the outcome; every
   state round-trips.
4. *The careful policy retains the permitted $200* — the buyer's
   tolerance is walking money, and burning it destroys value for
   nothing: the careful burn is max(0, dirty − tolerance).

**Revision 8 completion (model-level corrections).** Re-review found
the rev. 8 implementation exact in behavior but not in model:

1. *Whole-percentage storage was not whole* — `cut_points / 100` turned
   28 into 28.000000000000004 at storage time (real broker seeds 6 and
   17), silently violating the exactness the ruling bought. The
   canonical stored unit is now the **integer percentage point**
   (`escrow_discount_pct`); the division by 100 happens once, inside
   the dollar-rounded term, never at storage. Existing v3 payloads
   carrying the float migrate on load; all 16 possible draws (20–35)
   are exhaustively pinned with plain integer equality — no round(),
   no isclose().
2. *The severance discriminator was a label, not a machine* — rows
   like paid/None/2 and not_applicable/0/2 validated, and a
   contradictory save loaded silently. The complete state machine now
   binds at transition and load: pending → no amount, no headcount
   (and never on a sold run — the terminal invariant takes the run's
   game_over); paid → positive headcount and exactly rate × headcount;
   declined/unaffordable → positive headcount, zero paid;
   not_applicable → zero and zero. The rate itself has one canonical
   home (`models.SEVERANCE_PER_HEAD`), and the closing applies its
   outcome triple through one validated transition before the run is
   allowed to end. The review's five exhibited contradictions are
   pinned as refusals.
3. *The canonical-unit contract binds at the persistence boundary too*
   (final re-review) — the producer path was exact, but a doctored v3
   payload accepted 0.28 back into the integer field, a fractional
   29.5, a −10 that became a $1,000 credit, and an out-of-domain 200.
   Validation now requires an actual integer (bools refused) in the
   ruled 20–35 domain, tied to the incident count: no incident means
   zero, one incident means a permitted repricing, and two incidents
   cannot remain in an active sale (the second collapses it). The
   repricing domain moved to its one canonical home
   (`models.REPRICE_MIN_PCT`/`MAX_PCT`), legacy float migration is the
   only conversion site and feeds the same validator, and the sole
   surviving first-incident discount is assigned, not accumulated.
   Malformed payloads are pinned through `state_from_dict`.

**Revision 9** records the P2 authorization decisions (the Straight
Path scope), made on paper before implementation — the §2.4.1 letter
plus revision 2 item 4 is the spec; everywhere it is silent, the
resolution below is proposed and flagged for review. Constants are
placeholders in the §6.3 sense: structure is the decision, numbers are
tuning, and any §2.7 miss is reported with its decomposition, never
tuned away.

1. **Randomness (the reserved-streams question, flagged first).** The
   Straight Path draws no reserved stream: `sitdown` and `war` stay
   provably undrawn, `brokers` stays the Sale's. Disposal runs ARE
   routes — they draw the existing `routes` stream under full Act I
   route rules, with the seller-without-a-network haircut replacing
   the ordinary offer multiplier draw for draw (uniform 0.60–0.75
   where Act I drew 0.85–1.20 riding along and 0.90–1.05 solo), so a
   disposal run consumes exactly the dice an Act I route consumed.
   Temptation-offer arrival and terms are world facts and draw a
   per-day derived channel (`daily(day, "straight")` — pure in (seed,
   day), incapable of perturbing any persistent stream). Player-facing
   meeting dice — the fire-sale observation roll, the accepted-offer
   observation roll — draw a NEW persistent `straight` stream,
   mirroring brokers-for-the-Sale: reserved to the branch, drawn only
   after the chair is taken, provably fresh in stand-pat and Act I
   (both gates enforce it through the existing undrawn-streams
   surface, schema-additive like `brokers` was).
2. **The contest queue.** §2.3 prices counsel as "every 3rd retained
   day, the oldest *paper* record is contested: magnitude −60%", and
   §3.1 shows the over-ceiling record "first in the queue" even
   though routine 0.5 ticks predate it — while §2.3 itself calls the
   ticks "one rolling 'routine discrepancies' record". Resolution:
   counsel contests *flagged* paper records (non-empty why) oldest
   first, one contest each; the routine hum is contested once, as the
   single rolling record §2.3 says it is (every flagless tick reduced
   together, counted as one contest); when the queue is empty counsel
   keeps enforcing the ceiling and says there is nothing left worth
   arguing.
3. **The cap and the floor, exactly.** The 25-point cap binds the
   PAID verbs — contests and settlements — measured as points
   actually removed; an event whose full relief exceeds the remaining
   cap applies what room remains and the transcript says so. Free
   retention dormancy (a current aware employee at morale ≥ 5 keeps
   their own records dormant) is reversible — it lapses when morale
   slips or the person leaves — so it spends no permanent budget and
   is not counted against the cap. The floor: evidence-only verbs
   (contests, new dormancy) refuse to fire at or below Case 10 (the
   file is as cold as they will let it get, and the verbs say that
   rather than silently no-op); a settlement below the floor still
   signs — it buys the goal term and the witness's peace — but
   relieves no evidence, out loud. When an event lands the sum below
   10, the permanent
   institutional-suspicion record ("they remember your name") is
   written, or topped up in place, by exactly the difference — its
   own evidence kind (`suspicion`), permanently immune to every verb,
   so displayed Case ≡ the visible ledger holds at the floor too.
   Arrest at 100 latched at accrual outranks all of this; every
   remediation entry point is a no-op on a finished run.
4. **Settlement mechanics.** A settlement is the letter's permanent
   −50%: the target's witness-record magnitudes are halved by
   mutation, once, capped per item 3; the reversible dormancy flag is
   reserved for the retention case and reconciled nightly from the
   roster. Targets: any *departed* aware employee (the §2.3 case) and
   any *current* aware employee — §3.1 D15 settles Marcus out while
   he is still on payroll: he leaves settled, quietly, with **no**
   fired-knowing-everything record (severance instead of a witness —
   the §2.6 paid-loyalty primitive in embryo). Cost ≈ 6× current
   daily wage, clean cash only. `BranchState.settled_witnesses`
   persists the keys for the no-hostile-unsettled-witness goal term.
5. **Clean-days arithmetic.** `last_crime_day` None means no crime
   since the fork: clean days = day − sit-down day + 1 (the sit-down
   morning itself is clean day one); otherwise day − last_crime_day.
   The day-30 goal needs ≥ 5, so the R = 5 boundary fork can still
   earn the exit by staying clean throughout, and "all liquidation
   must finish by day 25" is exactly the theorem §2.4.1 states.
   Crimes: a disposal run (when it actually rolls, not when planned),
   a fire-sale meeting, an accepted temptation offer, washing past
   the ceiling. Tribute, truce money, settlements, burning and
   under-ceiling washing never reset the clock.
6. **Fire-sale terms.** One meeting a day; moves any chosen stock
   from either stash (Sal's people bring the truck — §3.1 D14 sells
   the warehouse oregano without an off-site step); 40% of base book
   value, paid dirty; +8 Sal relation; observed at 20% (the
   `straight` stream) for a +3 witness record. A crime.
7. **Temptation offers.** While stock remains, ~30% of mornings (the
   daily channel) a contact wants one held good at 1.4–1.7× base;
   the card states the distinction verbatim — *new trade at full
   margin, not disposal: accepting resets the clean-days clock and
   spends no disposal run.* Accepting sells from the shop stash,
   pays dirty, resets the clock, and is observed at 15% for +3
   witness. Declining costs nothing and is never punished.
8. **Advertising.** $300 clean buys a four-day campaign: +2
   reputation a night and +15% demand while it runs; buying again
   adds four more days. Canon's clean-money list finally gets its
   entry; counsel and advertising both live in Improvements.
9. **Verbs that leave.** The supplier van is gone in-branch — nothing
   restocks, so "disposal runs sell only stock held at fork time"
   holds by construction, with no fork-inventory bookkeeping to
   drift. "Plan a night job" leaves the morning menu (the raid verb
   is gone, rev. 2 item 4); "Plan tonight's route" becomes
   **Disposal** with the counted `runs left: n` in its label. The
   burn action reuses the P1b disposal primitive's effect (extracted
   as an effect-only helper; escrow keeps its exact narration, the
   Straight Path narrates Tony watching) — destruction, never
   conversion, no crime.
10. **Counsel.** $150/day, charged nightly alongside wages; a till
    that cannot fund it loses counsel that night, out loud. Every 3rd
    retained day contests per item 2. While retained, the wash prompt
    is capped at tonight's ceiling — the "wash more anyway" branch is
    simply not offered (§2.3 dual use).
11. **Clean insolvency.** A consecutive-night counter on BranchState:
    two consecutive nights with payroll short AND zero stock anywhere
    AND zero dirty anywhere → the existing broke ending, with the
    branch flavor §2.4.1 names (the cover business couldn't cover the
    cover-up). Precedence per §2.5 — arrest still outranks it.
12. **Ending ids.** `straight_exit` (the earned Legitimate Exit,
    upgraded text), `almost_out`, `half_measures` — graded at the
    day-30 boundary where stand-pat grades `survived`. Half Measures
    names every failed term, not just one (invariant 8).
13. **The siege.** Rivals smell retreat: each rival's nightly act
    chance ×1.5 while the branch holds no stash anywhere. Searches
    attack people: a law-phase squad-car visit costs one observant or
    aware employee 1 morale in-branch (the §2.4.1 line: searches
    attack the exit through people, not stash).
14. **Measurement.** Covert-revenue share is tallied from the same
    transcript a human reads (the `+$N dirty` lines), per day, by the
    study bot; the ΔCase baseline is `case_at_lockup` (the value the
    chair was priced at, stored and unambiguous); branch-good for the
    §2.7 band and ablation is the earned Legitimate Exit alone —
    Almost Out is a consolation, not a success. The ledger-
    transparency row asserts nightly that displayed Case equals an
    independently recomputed clamped sum of effective magnitudes, and
    that Case never reads below 10 once any paid remediation exists.
15. **The shared prefix iterator** (the fold_case docstring's debt)
    lands now, before remediation multiplies the scans:
    `models.case_prefix` yields the same left-to-right running total
    as `fold_case`, dormancy-aware; `fold_case`, the Case-60
    telegraph and the sit-down's gate-crossing record all consume it —
    one arithmetic, bit-identical flag-off, regression-pinned on the
    3.12-divergent sequence.
16. **Scope note.** Counsel, settlements and dormancy unlock for the
    Straight Path only in P2 — §2.3 grants them to all four active
    branches, and the machinery is branch-agnostic, but each later
    branch turns its verbs on in its own phase, under its own
    studies. Sal's standing offer to buy the coded-customer book
    stays prose for now (temptation offers carry the Dope Wars pull);
    if review wants it as a distinct mechanic it lands in a
    correction pass.

**P2 implementation notes (pre-review).** The branch landed whole and
its §2.7 rows ran; three bars miss structurally and the decomposition
goes to review with the data (FINDINGS round 9). Judgment calls made
in flight, recorded for ruling:

1. *A settlement below the floor signs but relieves nothing* — item
   3's blanket verb-refusal would have made the no-hostile-witness
   goal term unreachable at a cold file; the money buys the goal term
   and the witness's peace, the arithmetic stays where the floor put
   it, out loud. (Amended in item 3 before implementation.)
2. *The ΔCase bars miss for a structural reason, not a mechanical
   one.* The named smart-bot baseline enters the fork at a median
   lock-up Case of 6 — below the 10-point floor, where the file
   cannot fall at all — with nobody read in, so the settlement verb
   has no lawful target the entire study. The §3.1 exemplar enters at
   Case 31. Whether the criterion is conditioned, the baseline
   re-based, or the constants strengthened is a review decision;
   the diagnostics that separate the hypotheses (matched-seed
   counterfactual, the lockup ≥ 20 population, a dirty-month variant
   with its own ablation) ship in the harness, labeled, without
   conditioning any bar.
3. *Source-less witness records are structurally immune.* Two P0-era
   call sites book witness evidence attached to no employee (the
   informant's tip, the patrolman on the take); §2.3's taxonomy
   attaches witness records to persons and its settlement verb keys
   on Employee sources, so these records are as untouchable as
   physical — and they are the siege's main post-fork accrual.
   Intended pressure, or a mis-kinding to correct? Flagged, not
   changed: re-kinding alters remediation reach and needs the ruling
   first.
4. *The Quiet Sale's flag stays down.* §7's letter — the flag lifts
   when THIS gate passes — is honored over the phase boundary: with
   the ΔCase study missing its bars, no flag moves until the ruling
   lands.

**Revision 10** responds to the review of P2, which reproduced every
number, accepted the branch's identity and the randomness ownership,
ruled on all four flagged questions — and found two correctness
defects and three design gaps that block the PR. Recorded on paper
before the correction pass:

1. *Dormancy was cached derived state, and the cache could lie at the
   worst moment.* The stored `Evidence.dormant` flag was reconciled
   nightly BEFORE the rival and law phases; a poach or a
   morale-dropping search after the reconciliation left a protected
   record halved with its protection gone — reproduced: a dormant
   20-point record at morale 5→4 graded `straight_exit` where the
   true file reads `almost_out`. Doctored saves could also plant
   dormant records with nonexistent, departed or demoralized sources.
   The correction removes the stored flag entirely: **retention
   dormancy is derived, in one context-aware ledger calculation** —
   `fold_case(evidence, dormant_sources)` where the dormant set
   (hired ∧ aware ∧ morale ≥ 5 ∧ unsettled) is computed from the live
   roster at every read; `State.case` supplies the context, and no
   phase ordering can stale it. The floor keeps its letter inside the
   same calculation: halvings allocate in ledger order and stop at
   the first record whose relief would take the display below 10 —
   deterministic, pure, and identical arithmetic to the flag-off fold
   when the set is empty. The nightly reconciliation event is gone;
   the paid verbs keep their at-verb floor top-ups. Settling a
   currently-protected witness still locks the half in for free (the
   magnitude halves as the source leaves the protected set —
   effective weight unchanged, no cap charge).
2. *Cross-state validation.* Save-load now validates the ledger, the
   roster, the settled list and the branch state TOGETHER: witness
   sources must be empty (external) or a roster key;
   `settled_witnesses` must name existing, aware employees; the
   dormant-record payload class ceases to exist with the field.
3. *The evidence ledger becomes visible.* One `EvidenceLedgerView`
   itemizes every record — kind, base and effective magnitude, source
   name, disposition, contest status — plus the displayed total
   (identical, by construction, to the meter), the paid-cap budget
   spent and remaining, the floor, and counsel's next target. A
   "case file / counsel docket" screen in the branch morning renders
   the view and nothing else; the exit readout consumes the same
   total. The renderer infers no rules.
4. *One remediation disposition.* A single
   `models.remediation_disposition(record)` names what can touch each
   record — contestable / settleable / external-witness (immune) /
   immune / the suspicion record — and the contest queue, the
   settlement verb, the docket and validation all consume it; kind,
   provenance and UI cannot disagree.
5. *Taxonomy ruling applied.* The informant's tip is an intelligence
   report, not testimony: it becomes **paper** (contestable) at its
   call site, §2.3's paper list gaining the entry. The bribed
   patrolman, the regular at the handoff and the watcher at Sal's
   truck stay witness records with external provenance (empty
   source) — immune, and now labeled as such in the docket.
6. *Settlement is one result with two outcomes.* Every path —
   relief applied, truncated at the cap, floor-bound, cap-exhausted,
   or no attached records — states the relational outcome AND the
   evidentiary outcome. The below-floor ruling stands; cap
   exhaustion gets the same honesty ("the engagement is settled; the
   file is not").
7. *The disposal route stops resurrecting the burned book.* Route
   presentation is centralized and branch-aware: a disposal run
   speaks of cold buyers and one-use contacts, never "coded orders
   on the board." The route grammar, dice and prompts' option lists
   are unchanged; only the disposal-flagged voice differs.
8. *The Case bars split into two cohorts (the ruling on the round-9
   miss).* No constants move; no bar is conditioned after the fact.
   **Natural-entry cohort** — the unmodified market-bot baseline:
   keeps reachability, the earned-exit band, the covert-share
   collapse, crash-freedom and both oracles, and gains the paired
   bar *remediation leaves the file lower in ≥ 60% of matched
   entries*. **Redemption cohort** — a frozen, predeclared
   §3.1-shaped reference state (Case 31: an immune seizure, a
   flagged over-ceiling record, the routine hum, the informant's
   tip, and a hostile departed witness), entered through the real
   scene and run across world seeds: the original bars bind here —
   median ΔCase ≤ −5, Case strictly below entry in ≥ 60%, ablation
   drop ≥ 20 points. The dirty-month bot remains an ecological
   confirmation, not an acceptance fixture. The reference state is a
   harness-owned literal, like the frozen scene schema.

**Revision 11** responds to the re-review of revision 10, which
reproduced every number, accepted all eight corrections in
architecture — derived retention, the docket, honest settlements, the
tip's reclassification, external immunity, the disposal voice, the
two cohorts, the RNG ownership — and found the replacement ledger
non-monotone at the floor plus a disposition authority that still
disagrees with reality. Both rulings on the round-10 flags were
taken: no criterion amendment (the natural 61% passes as written and
must re-clear after this fold correction or it fails; the redemption
exit rate is not a failure and gets no band). Recorded on paper
before the correction pass:

1. *The relief allocation becomes per-record and partial — Case is
   monotone again.* The all-or-nothing allocation made the meter
   move the wrong way at the boundary, both directions reproduced by
   review: adding 1 point of paper dropped Case 15 → 10 (the new
   allowance let a previously-too-big halving fit), and a −2.46
   contest raised Case 10.1 → 13.6 (the shrunken allowance evicted
   it). The contract is now: allowance A = max(0, raw − 10); for
   each protected record in ledger order, cut_i = min(half the
   magnitude, A − relief already allocated); Case = clamp(raw −
   Σ cut). Total relief is therefore exactly min(total halvable, A),
   which is monotone in every direction the design promises:
   nonnegative accrual never lowers the Case, remediation never
   raises it, losing protection never lowers it, gaining protection
   never raises it. The boundary record's relief may be PARTIAL and
   renders honestly in the docket. The fold, the docket, the
   settlement lock-in (the free portion of a settlement is the cut
   the allocation was already giving; the paid portion is the rest
   of the halving) and the independent oracle all consume this one
   allocation. All six properties are pinned, including both review
   repros.
2. *One witness-relationship authority, and the lifecycle closes.*
   `remediation_disposition` gains the state it needed: a sourced
   witness record answers settled ("their peace is bought"), beyond
   reach (arrested — the statement is the state's), or settleable —
   and the docket, the settlement target list, hostile-witness
   grading, hiring eligibility and cross-state validation all read
   the same answer. The lifecycle exploit closes per the review's
   recommendation: **a settled-out employee cannot be rehired on the
   Straight Path** — the hiring pool refuses them in-branch, and a
   straight-branch payload carrying a settled name that is also
   hired is refused at load. Validation additionally requires unique
   employee keys and refuses employee-sourced witness testimony
   attached to someone never made aware.
3. *The docket honors round 6's aggregation promise.* Storage stays
   per-tick (float identity); the display groups the routine hum
   into one line carrying the entry count and exact base/effective
   totals. The counsel status line stops naming a next target that
   cannot be contested: cap exhausted and floor-bound states say so
   instead.
4. *The reporter tells the truth about which numbers bind.* The
   cohort contract moves into an explicit specification: the
   natural-entry cohort prints its band and paired bar as bars and
   its absolute ΔCase as reported context; the redemption cohort
   prints the original ΔCase letter as bars and its exit rate as
   reported context; every dirty-month line is labeled diagnostic.
   Counsel-only and settlement-only redemption runs are added as
   labeled diagnostics (the review's suggestion), not bars.
