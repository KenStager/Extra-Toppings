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
| Harbor War | Break a rival and take their trade | War pay, injuries, and a Case built mostly from evidence no verb can touch (rev. 14) | Peace with the target: their relation locks at vendetta; no truce, ever |
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

**The grade is two questions, not one** (rev. 23 item 1). Arrears
decides *which terminal* the run reaches — `operation` or
`on_the_hook` — and the tycoon half decides *how good an `operation`
is*. Keeping Carmine current while running two hollow fronts must not
read as a win: that would let the branch be completed by paying a man,
which is the exact opposite of the north star's question. So
`operation` carries explicit **operational tiers** derived from
combined net and shop 2's reputation, and one canonical **Partner
grading view** owns that arithmetic and every consumer of it — the
status card, the ending text, the epilogue, the bot studies and the
human-play report all read the same view, so a tier can never mean one
thing on screen and another in FINDINGS.

**The two terms, exactly** (rev. 24 item 1). *Combined net* extends the
existing `State.net_worth` authority to the shops collection rather
than inventing a second definition of money: clean + dirty +
warehouse cash + every open shop's stash at book value + warehouse
stock − debt, **minus current arrears**. Three exclusions are
deliberate and stated so nobody has to guess: **Carmine's capital is
equity, not a liability** — no principal is ever repayable, so it is
never subtracted; **upgrades, build-out and the wagons are not
assets** — `net_worth` counts no fixed capital today and this changes
nothing; and inventories count at book, exactly as they already do.
*Shop 2's reputation* is that address's own meter, read directly.

**The tiers, ordered `hollow` < `working` < `healthy`, as an AND-gate.**
`healthy` requires **both** terms independently — money must never
compensate for a dead restaurant, which is the whole point of the
branch; `working` is exactly one term met; `hollow` is neither.
Because `working` can be reached from either side, its text has two
arms — the money without the room, and the room without the money —
since those are different stories and the epilogue should say which.
Placeholder thresholds (§6.3, movable only by recorded ruling):
**combined net strictly greater than $8,000** — not a new number but
the game's existing one-shop "the operation holds" bar promoted from
its literal to a named home, **comparison and value both unchanged**
(rev. 25 item 2: an earlier draft wrote "≥ $8,000" while calling it
unchanged, and at exactly $8,000 that flips the outcome — the
existing contract is `>` and stays `>`); and **shop 2 reputation ≥ 35**,
which sits above the ~20 it opens at (so it must be earned, never
merely inherited) and below the 50 the home shop starts from (so it
is reachable inside the month). P4b's first study reports both
distributions so the bars move on measurement rather than taste.

**The card shows its work**: each term's current value, the
requirement it is measured against, and the resulting tier — the
player can always see which half of the hybrid is failing, which is
what makes the grade steerable rather than a verdict at the end.

**The deal:** Carmine fronts $20,000 (breakdown: build-out $9k, permits
$1.5k — clean, permits are paperwork — used second wagon $2.5k, opening
float $3k, reserve $4k). **The capital is never a spendable $20,000
deposit** (rev. 22 item 8): accepting the deal commits $13,000 —
build-out, permits and the wagon — atomically, to Carmine's own
contractor, in the same transaction that creates the second address;
only the $7,000 float and reserve enter clean cash. Nothing about the
build is left to hope that later spending consumes the right money.
The obligation is **points, not debt**: $2,500 to Carmine every 5 days,
unmarked bills preferred, forever. No amount pays him off; it is equity.
Early payoff (≤ day 10) defers the first points cycle by one — his
compliment.

**Points keep two separate books** (rev. 22 item 7), because "two
misses, consecutive or not" and "one payment currently outstanding" are
different facts and one counter cannot carry both. *Arrears* is what is
owed right now; a *strike* is a miss that happened and never unhappens.
A missed $2,500 stays owed: the next cycle's bill is prior arrears +
the new $2,500 + a $500 vig. Paying that bill clears the arrears and
leaves the strike standing, so the second strike — at any later cycle,
consecutive or not — forecloses. Day-30 grading reads **arrears**: zero
is The Operation, nonzero (necessarily carrying the one strike) is On
the Hook.

**Site selection** (the branch's first screen): any district but Old
Harbor. University Hill — volume, students, no owner; Little Sicily —
reputation country, Sal's turf; The Meadows — the best covert demand in the
city, Vinnie's floor. Opening on a rival's turf is a commercial declaration
(steep relation hit, their counterplay intensifies there); the safe pick is
a real choice, not the only one.

**Pressure replacing the debt:** the points clock (miss one: a warning,
the amount stays owed, and $500 vig rides the next bill; miss two —
consecutive or not: foreclosure, §below), double payroll, double rent,
and **the roster does not double**: eight employees, two addresses,
one-person-one-job. The wagon count is two and both wagons run real
routes — honest or covert, simultaneously, one per address per night
(rev. 22 items 1 and 4; the cover-only second wagon proposed in rev. 21
was rejected, and the letter below was always the stronger reading).
Read-in drivers are however many you've made: a second covert route
needs a second person you trust with your life, and that person is the
branch's central mechanical payoff, not a convenience. Two
believable-revenue
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
physically); tribute demands can now name either address. *Raids*:
**raid grammar, objectives and RNG remain unchanged; logistics become
addressed** (rev. 23 item 2 — "yours unchanged" was false the moment
inventory became address-local, since a raid crew must now come back
to *somewhere*). A
raid takes a named wagon or goes on foot, and it names its return shop;
the haul is placed at that destination and nowhere else. Theirs may
target the softer of your two shops — defense is now an allocation
question. **That promise is operationalized, not implied**
(rev. 22 item 5): one address-target authority chooses which address a
rival moves against, a telegraphed raid **persists the address it
named** so a save cannot retarget it mid-warning, and every
consequence lands on the named shop — coupons, guards, damage days,
stash seizure, reputation loss, the heat it raises, and the law's
searches alike. Staff assigned to an address are that address's defense
allocation. *Inventory is local and never teleports* (rev. 22 item 9):
every purchase, improvement, storage move and route names an address;
pantry, stash and upgrades belong to their shop; warehouse transfers
name a source and a destination; there is no free shop-to-shop
transfer. Clean and dirty cash stay global — one till for the operator,
an abstraction stated here rather than left to be inferred.
*Reputation/demand/pantry* run **per shop**: shop
2 opens at reputation ~20 with its district's traffic and its own pantry;
neglect at either address strips that address's cover (the FINDINGS chain,
now twice). *Staff*: the branch's binding constraint — assignments per
shop, a named manager for shop 2 (an aware employee; their loyalty is now
load-bearing), familiarity resets in the new district, and poaching one
roster across two addresses is how rivals fight you here.

**An invariant, declared and tested — in three recorded phases**
(rev. 22 item 8, reconciling the invariant with §3.2's D14–D16, where
the shop is manifestly not yet serving customers). (1) *Accepted:* the
second `Shop` record exists from the moment the deal is struck — it is
created by the same atomic transaction that commits the $13,000, so
there is no window in which the branch is funded and the address does
not exist. (2) *Under construction:* it stands until its **recorded
opening day**, deterministically (Carmine's own contractor, no dice),
serving nothing, earning nothing, carrying no order book. (3) *Open:*
from the opening day onward it cannot close. Raid damage limps a shop
but never shutters it, and no Partner-branch event can un-open an
address — the only ways to lose shop 2 are Foreclosure and arrest, both
of which end the run. "Both shops open" is therefore not a day-30
condition to check but an invariant to test; the day-30 matrix reduces
to the points ledger alone.

**The manager, and the vacancy that is gameplay** (rev. 22 item 6).
Shop 2 runs under a named manager — an aware employee, their loyalty
load-bearing. But a manager can be arrested, poached, fired, or can
resign, and every one of those is legitimate play, so **a vacancy is a
valid state, never an invalid save**: the post empties (recorded as
such, with the day it emptied), the address stays open under Carmine's
nephew, and while it is vacant that shop runs at a reduced kitchen
capacity and a reduced believable ceiling. The player has a stated
window to appoint another qualified manager before the penalty bites
at its full weight; appointing one clears it. A validator that demanded
a living, hired, aware manager at all times would refuse saves the
player reached by playing the game correctly — the precise failure this
design forbids.

**Failure states / endings** — three explicit terminal ids, none of them
riding a generic fallthrough (rev. 22 item 3, on rev. 15's precedent):
*"The Operation (two ovens)"* (`operation`, **new id**, not an upgraded
`survived` text) — day 30, arrears zero; **graded into three texts by
the tier** (rev. 24 item 1): *healthy* is the operation-holds text with
an explicit Act III hook — two ovens, both of them real, and a partner
who will want more; *working* has two arms — money without a room (the
books are fat, the dining rooms are empty, and what you own is a
laundry with a pizza sign) and a room without money (both rooms are
loved, the tills are thin, and Carmine's schedule is the only thing
keeping you honest); *hollow* is the one that should sting — Carmine
is paid on time, and you own two addresses that are ash inside. All
three are `operation`; only the first is branch-good.
*"On the Hook"* (`on_the_hook`, new) — day 30
with arrears outstanding: both ovens burn, but the vig is compounding
and Carmine owns your schedule now; a survival ending graded below Two
Ovens, whose Act III hook reads very differently. *"Foreclosure"*
(`foreclosure`, new) — the second strike, whenever it happens
(consecutive or not): Carmine protects his investment; he takes the
second shop, the wagons, and the month's dignity — the kneecaps
ending's polite cousin, and the run ends that night. Arrest at
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
a running ledger of *where their strength went* (jobs / corners / ovens /
the ledger / defense — the five channels of the canonical damage ledger,
rev. 19), so the mixed campaign is visible on screen, not implied in
prose.

**How a rival organization actually breaks.** Raids alone must not be the
answer — that is the grinding alertness was built to prevent — so the
branch specifies five damage channels, every one flowing through the
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
- **Defense** (incidental): a repelled or landed counter-raid costs the
  attacker strength through the same authority — never a strategy you
  choose, always visible in the ledger (rev. 14: incidental damage is
  a channel because the reconciliation oracle counts every hundredth).

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
and **the Case's gross accrual only ratchets here** — a war month books
pattern, physical and external-witness evidence that no verb can touch
(§2.3), while eligible paper and employee testimony remediate exactly as
anywhere (rev. 14: the claim is the immune-heavy mix, not an absolute
meter) — so the branch's real clock is whether you can finish the war
before the file finishes you. Alertness economics (the $752 → $556 → $413 decline
curve, FINDINGS round 5 — round 4's $781 → $597 → $438 was inflated by the
issue-4 noise-timeout bug and superseded there; citation corrected rev. 13)
make raid-spam a TRADE, not a free lunch — the honest thesis, certified
at rev. 19's calendar-keyed experiment: grinding tries to buy tempo
with twice the attempts and nearly three times the injuries; it does
not outperform pacing (total damage statistically tied; efficiency
0.55 vs 0.32 per committed person-night). Pacing preserves crew and
improves damage efficiency, and must not worsen campaign outcomes
(the §2.7 outcome bar). Mixing
routes-in-their-turf, sabotage windows, and jobs on the days their
security word says sleepy is how a campaign spends people it wants to
keep.

**Systems carry-forward:** *Clean money* keeps the shop alive under
coupon-blitz siege — a war run that lets the restaurant die loses its
laundering, its cover, and then the war. *Dirty money* funds war pay and
tribute-to-the-bystander. *The Case* is the doomsday clock; the ledger
play is its one release valve (their case, not yours). *Heat* becomes
territorial denial: raiding a district spikes its heat (+12 today), which
suppresses *your* routes there — burn a neighborhood taking it and the
routes through it pay for it: heat is a LOCAL ROUTE TAX per district
(§2.6, amended rev. 17-19 — enforced and priced at planning and at the
route's own capacity and corner take; campaign-level load is unproven
and stays an honest finding, never asserted by this paper). *Rivals*:
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
   exception: if a campaign's capture transition had completed before
   the latch fired (transition ordering, never mere calendar-day
   equality — rev. 14), the arrest prints as *Won the War, Lost the
   Verdict* — the same terminal, a distinct text arm.
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
| Partner | arrears zero | The Operation (two ovens) — an explicit `operation` terminal (rev. 22 item 3), graded `hollow` / `working` / `healthy` by an AND-gate over combined net and shop 2's reputation through the one Partner grading view (rev. 23 item 1, specified rev. 24 item 1); only `healthy` is branch-good |
| Partner | arrears outstanding (necessarily one strike) | On the Hook |
| War | no rival broken | A Long War |
| War | one rival broken | The Harbor Is Yours (text variant when a second vendetta is open — rev. 14: a second war never erases the first victory) |
| War | both rivals broken | The Syndicate (an explicit `syndicate` terminal — rev. 15 overturned the no-new-id ruling: an outcome matrix must not depend on generic epilogue ordering) |
| Sale | (never reaches day 30 in-branch) | closes at fork+4 or reverts |
| Stand-pat | as today | the existing survived grades |

Partner's second shop is open at day 30 by tested invariant (§2.4.2), so
its matrix is the points ledger alone — a third state cannot exist, and
the terminal discriminator is **arrears**, not the strike count
(rev. 22 item 7): a player who missed once and paid the catch-up bill
reaches day 30 with one strike and zero arrears, and has earned The
Operation. Which *kind* of Operation is a second, independent question,
answered by the tiers of §2.4.2 — the terminal id is not the grade, and
"branch-good" in §2.7 means the healthy tier, never merely the id
(rev. 23 item 1).
Pre-day-30 terminals: arrest (any branch, via the latch); Foreclosure
(Partner); Burned Out (War); clean insolvency (any branch — the Straight
Path is where it lives); the escrow close — Sold, in three tiers with the
*kept the trade* reclassification (§2.4.4). Escrow collapse and walk-away
are **not** terminals: they revert to stand-pat and the run continues to
day 30 under the stand-pat matrix.

**Inventory** (restated rev. 22 item 3; the earlier count went stale the
moment rev. 15 promoted The Syndicate from an upgraded text to an
explicit id, and that promotion was never folded back into this line).
Existing seven retained (kneecaps unreachable post-payoff — the debt is
zero; stand-pat reaches all seven exactly as today). New IDs, **ten**:
Almost Out, Half Measures, On the Hook, Foreclosure, The Operation, The
Syndicate, The Harbor Is Yours, A Long War, Burned Out, Sold (one ID
with graded tiers and the reclassification). Won the War, Lost the
Verdict is a text arm of arrested, not a new ID. Upgraded text (not new
logic), **one**: the earned Legitimate Exit. Net: ten new ending IDs,
one new arrest text arm, one upgraded text. The governing rule, learned
twice: an outcome named in a day-30 matrix gets its own terminal id and
never depends on generic epilogue ordering.
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
   - *War bot (amended rev. 14; letters replaced rev. 16-18):* median
     target strength at end ≤ 50% of its fork-day value; **remediation
     resistance on true accruals** — the median share of post-fork
     ACCRUED evidence surviving as permanent residue ≥ 50%, and Case
     above its fork-day value despite remediation in ≥ 60% of wars
     (the retired pattern+physical kind-share ships as decomposition);
     **the pacing letters** — at 500 seeds the alertness-aware full
     policy must not trail the cooldown policy (the outcome bar), the
     fleet comparison reported as a paired observational decomposition
     under exact names (executed-job, executed person-night,
     planned/committed efficiency), and the causal claim carried by a
     state-matched fixed-opportunity experiment, calendar-keyed dice,
     reported as measured; **channel mix:** in successful runs no single damage
     channel (jobs / corners / ovens / ledger / defense) accounts for
     > 60% of **applied damage in the broken campaign** (aggregate mix
     across campaigns reported as a diagnostic); a raid-only ablation
     bot — one that takes no proactive non-job channel, incidental
     defense damage remaining visible in its ledger — trails the mixed
     bot's success rate by ≥ 15 points, the anti-grind claim tested
     directly; a **restaurant-neglect ablation** (no cover spend, no
     pantry care) trails the complete bot in **unconditional
     Syndicate-ending rate by ≥ 15 points, binding at 500 seeds**
     (rev. 17: a hollow restaurant can win one street fight but
     cannot sustain control of the city — the first-capture bar
     measured the wrong dramatic outcome; second-front-to-capture
     conversion, Burned Out, payroll failures and witness accrual are
     the reported decomposition), or the tycoon half is decorative
     and the branch fails review; and a nightly
     reconciliation oracle: each campaign's starting strength minus the
     rival's current strength equals its damage records exactly.
   - *Partner bot (letters made unambiguous, rev. 22 item 10):*
     **combined legit revenue** — both addresses, measured as
     *cumulative* legit revenue from the fork through fork+8, paired
     against the same seed's stand-pat control; the **median per-seed
     ratio must be ≥ 1.5**, and the absolute dollar difference is
     reported alongside so a ratio inflated by a tiny denominator
     cannot pass unnoticed. **Points on schedule** — defined as
     **zero missed cycles**, in ≥ 80% of entered runs that reach at
     least one due date (runs foreclosed, arrested or ended before a
     first due date are excluded from the denominator and reported
     separately, never silently dropped). The criterion-5 ablation is
     **no post-fork covert revenue** — a bot that runs no covert route
     and takes no dirty income after the fork — rather than the
     mechanically ambiguous "pays points from pizza margins only";
     dirty cash *inherited* from before the fork is reported as its
     own line, since a bot can pay early points from a pre-fork stash
     without ever committing a post-fork crime, and that is precisely
     the confound the old wording hid. **"Branch-good" for Partner
     means the healthy `operation` tier** (rev. 23 item 1), read from
     the one Partner grading view — never every run whose terminal id
     happens to be `operation`. The 25–70% band of criterion 5 is
     measured on that tier, and the id-level rate is reported beside
     it so the gap between "paid the man" and "built the business" is
     visible rather than hidden inside one number.
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
   a Straight Path bot that never settles witnesses or retains counsel;
   an Escrow bot that keeps stash on premises. **Partner carries two
   ablations, and they prove opposite halves of the hybrid** (rev. 23
   item 1): a bot that takes **no post-fork covert revenue** (rev. 22
   item 10, replacing "pays points from pizza margins only") proves the
   criminal half is load-bearing, and a matched **restaurant-neglect**
   bot — no cover spend, no pantry care, at either address — must
   reduce **healthy-`operation`** outcomes by **≥ 15 points, binding at
   500 seeds** (rev. 24 item 1 makes the bar binding rather than
   recommended: P4b needs an executable contract, and the constant
   still moves only through the recorded falsification workflow like
   every other), proving the tycoon
   half is load-bearing too. Neither substitutes for the other: without
   the neglect row a player could pay Carmine out of two hollow fronts
   and the branch would still pass its battery, which is precisely the
   failure this row exists to catch (the war's own
   restaurant-neglect row, rev. 17, is the precedent — the same
   hollow-restaurant question, asked of the other branch).
   (The war's cooldown ablation left this
   clause by ruling — rev. 16 retired its arbitrary 20-point magnitude
   and the pacing requirement lives in the §2.7 war letters above; the
   war's ≥ 20-class ablation is the raid-only and empire rows.) If an
   ablation *doesn't* hurt, the pressure is decorative and the branch
   fails review.
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
three ways, war pay vs. payroll (in Partner the wagon is contested *per
address* rather than globally — two wagons, but two addresses, distinct
drivers and at most one owner ride-along, so the scarcity moves to the
people rather than dissolving, rev. 22 item 1);
(2) functional shop — the Straight Path
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
  The capital ledger posts $20,000, itemized — and settles in the same
  breath (rev. 22 item 8): $13,000 goes straight to Carmine's
  contractor for build-out, permits and the wagon, the University Hill
  address exists from this moment as a shop under construction, and
  $7,000 in float and reserve lands in clean cash. You never hold his
  build money. Points card: $2,500 due day 19, then every 5th day,
  unmarked preferred.
- **D15.** Permits and build-out are already paid and under way; the
  contractor's schedule names the opening day, and nothing you do
  moves it. Staffing screen for two addresses: Rosa anchors Old
  Harbor; Marcus will drive University Hill — which means reading no one
  new in yet means shop 2 runs *straight* at first. Priya's résumé is on
  the counter (ambitious, two-star kitchen): shop 2 needs a cook.
- **D16.** The contractor's recorded opening day. Shop 2 stops being a
  building site and starts being a business: its own morning block
  appears — reputation 20, University traffic, its own pantry
  (standard), its own order book — and its own believable ceiling,
  currently tiny. From this morning it can never close again (§2.4.2's
  three phases). Carmine's nephew eats a free slice and looks at the
  register. First cross-shop decision: the second wagon exists, but a
  *covert* University route needs a read-in driver you don't have there.
- **D17.** Two-route morning — two wagons, two addresses, both routes
  real and both recorded (rev. 22 item 1): Rosa runs Meadows product
  (concert tail) out of Old Harbor, Marcus runs University pizzas — no
  cargo tonight, but a genuine route building genuine cover, not an
  exception carved out of the ledger. Distinct drivers, and you can
  ride along with only one of them. Sal's
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
  board** joins the market board's top panel (price intelligence stays —
  choosing profitable corner routes is the Dope Wars half, rev. 14): VINNIE — strength 58,
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
| R6 | Multi-shop refactor blast radius: demand/cover/laundering pipeline is `HOME_DISTRICT`-hardcoded and invariant-tested — and, measured in rev. 21–22, so are raids, rival actions, coupons, stash seizure and law searches | tech | H | H | Ship Partner branch **last** (§7); refactor to a shop *collection* with shop-local state, schema landing in save v3 during P0 as a list of one (§5) so Act III adds elements, not migrations — **the schema half of this landed and held**, leaving P4a a call-site and identity problem rather than a data-model one; P4a is its own behavior-neutral PR gated on identity across three Python versions and both battery depths (rev. 22 item 2); War-branch capture deliberately does *not* reuse multi-shop (§6.4) |
| R7 | Save v3 churn and determinism across branches | tech | M | M | Field-completeness guard already forces coverage; new persistent streams (`sitdown`, `brokers`, `war`) keep world channels untouched; no player-facing saves exist yet (`save.py` docstring), so no migration burden |
| R8 | Issue #4 (noise-timeout awards objectives) poisons the War branch economy | tech | H | H | Hard prerequisite: fix + regression through the actual raid path before War work starts (§7 P0) |
| R9 | Ending combinatorics: the new IDs × branch flavors bloat `epilogue` — count and census live in §2.5's terminal inventory, which is canonical and cited rather than restated here, so this row cannot drift out of step with it again (rev. 23 item 3; it had said "8" while §2.5 said ten) | tech | L | M | One dispatcher arm per branch; graded text inside one ending ID where possible (Sold tiers, the Partner operational tiers, the Won-the-War arrest arm) |
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
8. **The address-bound systems** — the big one, deferred to the Partner
   branch phase and **broader than `shop.py` alone** (rev. 22 item 2,
   on review's ruling). Shops and wagons first gain **stable identity
   keys** — list position is not an identity, and employee assignments,
   route origins, raid targets, storage locations and manager ownership
   all reference the key. Then every address-bound system is
   parameterized by it: `shop.py` (demand, ceiling, shift, reputation —
   today all reading `state.shop` and the module-level `HOME_DISTRICT`);
   inventory and storage (`STORAGE_LOCATIONS` is a two-string tuple
   today); routes and the night's service; upgrades; staff assignment;
   rent; rival actions; incoming raids; and the law's searches. Today
   `raids.py`, `rivals.py` and `phases.py` each hard-code DiNapoli's —
   damage, guard, stash seizure, reputation loss, coupons, the heat
   raised and the search swept all resolve against the one shop, and
   `Rival.raid_warning` is a bare countdown carrying no address at all.
   One **address-target authority** replaces those hard-codes, and a
   telegraphed raid persists the address it named.
   `RouteExecutionRecord` carries its origin shop; route chronology
   becomes ordered by day with uniqueness on (day, origin shop) —
   Partner permitting one route per
   address per day, every other branch one route in total, and raid
   chronology staying one per day. Every canon invariant test on the
   pipeline must pass parameterized before a second entry ever exists
   (the schema itself already landed in P0, items 2–3), and the whole
   pass is behavior-neutral while one shop exists.
9. **The vehicle boundary — one assignment authority for every wagon**
   (rev. 23 item 2). Today occupancy is a single global answer
   (`phases.wagon_job`/`wagon_used`, and the `wagon_free` /
   `wagon_taken` booleans threaded into `raids.plan_raid` and
   `war.plan_salvage`), and `models.place_haul(state, haul)` takes no
   destination at all — it fills the home stash, then the warehouse
   (models.py:1317). Under address-local inventory both are wrong: a
   raid haul would teleport to DiNapoli's whichever address the crew
   drove back to. One authority therefore owns every stable wagon
   across all four consumers — routes, outgoing raids, salvage, and
   the incoming-raid decoy — answering *which* wagons are free rather
   than *whether* the wagon is. `place_haul` takes an explicit
   destination. A raid names its wagon (or goes on foot) and its
   return shop. The decoy defense requires an actually free wagon and
   empties the **warned address's** stash — today it is offered
   unconditionally (raids.py:332) and can promise a wagon that is out
   on a route. Planning, commitment, execution and save-load all
   validate the same assignments, so a payload cannot describe a night
   the engine could not have run.
   **The authority is STATEFUL, not another derivation** (rev. 25
   item 1). Today `wagon_used(plans, service_report)` is a pure
   function of the morning's plans and the service report, so it
   cannot know about anything that happened later the same night —
   not the outgoing raid that just hauled with the wagon, and not a
   decoy that just used it. A night-assignment authority therefore
   holds state that **each executed consumer updates as it runs**, so
   the answer reflects every earlier event of the night rather than
   the morning's intentions.
   **This lands in two acts, because it cannot land in one** (rev. 24
   item 2). The single-wagon decoy correction changes what a released
   one-shop build offers on a menu, so it cannot sit inside a
   behavior-neutral P4a; it ships FIRST, as its own small correctness
   PR against the released game. Only then does P4a generalize the
   already-correct authority to multiple stable wagons with zero
   further behavior movement — and the typed atomic raid warning,
   addressed haul placement and the multi-wagon generalization all
   stay in P4a, since none of them moves single-shop behavior.
10. **`bot.py` / `bench.py` / `analysis/experiments.py`** — four branch
   policies, the `fork` study (divergence, ablations, control), per-branch
   FINDINGS tables.
11. **`docs/canon/README.md`** — record the accepted deviation (§2.8)
    when approved.
12. **New module `acts.py`** — the sit-down scene, chair gating, branch
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
- **P3.5 — the single-wagon decoy correction** (rev. 24 item 2), a
  small prerequisite correctness PR against the released one-shop
  game, landing BEFORE P4a because it deliberately moves existing
  behavior and therefore cannot ride inside a behavior-neutral
  refactor. Scope: one **stateful night-assignment authority**, updated
  by each executed consumer, that the incoming-raid decoy consults —
  the morning-derived boolean cannot answer it, because the decoy runs
  after the outgoing raid and once per arriving rival. *Gate:* six
  pinned cases (rev. 25 item 1) — departed route → decoy unavailable;
  departed salvage → unavailable, salvage scrubbed before departure →
  available; an executed outgoing raid that **took** the wagon →
  unavailable — that is a `steal_stock` raid whose crew departed,
  succeed or fail, while ledger and sabotage jobs go on foot and leave
  it free (rev. 26); an outgoing raid scrubbed before departure →
  available;
  the first decoy **reserves** the wagon so a second rival arriving the
  same night cannot reuse it; and fighting or paying tribute to the
  first rival consumes nothing, leaving it available to the second. An
  unavailable decoy is disabled **with its reason visible on the
  menu**, never silently absent. Plus: all three merged batteries rerun
  at both depths; and the flag-off golden **measured before it is
  touched** — the corrected path is either reached by the 300 golden
  runs or it is not, that count is reported, and regeneration happens
  only if it is reached, as its own recorded ruling with
  `ACTIVE_BASELINE` updated in the same act (revs. 17–18 precedent).
- **P4** — Carmine's Partner (multi-shop refactor last, alone in its
  phase). **P4a is three sequential PRs, each based on the previously
  merged one (rev. 27); P4b follows.** Stacked implementation PRs are
  forbidden — each merges and verifies before the next begins, so a
  failure is attributable to one boundary.
  - *P4a.1 — identity.* Stable `Shop`/wagon keys, the lookup
    authorities, save migration, uniqueness and reference validation,
    and the five one-shop aliases guarded through one
    `exactly_one_shop()` authority.
  - *P4a.2 — the address-local restaurant economy.*
    Inventory/storage, `shop.py`, upgrades, staff assignment,
    per-shop cook skill, rent, laundering ceilings, `net_worth` and
    `total_stock_units`.
  - *P4a.3 — the address-local night.* Routes and service,
    route-origin history, multi-wagon assignment, addressed haul
    placement, typed raid warnings, rival actions, incoming raids,
    coupons, damage, heat and law searches.

  All three are **behavior-neutral while one shop exists**. Because
  this is the first phase whose refactor touches the FLAG-OFF path,
  the gate is identity rather than a regression pin — there is no bug
  to fail on — and it binds at **every PR boundary**, not merely at
  the end: full tests, ruff and mypy, both identity gates 300/300 on
  **3.11, 3.12 AND 3.13**, and all three merged batteries
  byte-identical **at both depths (150 and 500)**. A moved transcript,
  RNG state, ending or study digit is a refactor defect, and **no
  golden regeneration is permitted anywhere in P4a**.

  **P4b — the branch itself, five sequential PRs (rev. 28), on the
  same never-stacked rule.**
  - *P4b.1 — the deal and the address.* Site selection, the atomic
    capital transaction, the second address and its wagon created
    together, the three declared phases and the recorded opening day —
    and the conversion of every `operating_shop` surface into an
    address-choosing one, in the same PR that first makes two
    addresses possible.
  - *P4b.2 — the points ledger.* The two books, the cycle and its
    vig, the early-payoff deferral, and the second-strike
    `foreclosure` that ends the run that night.
  - *P4b.3 — the manager, the vacancy and the two-front pressure.*
    Appointment, the vacancy as a valid state and its penalties, the
    address-targeting policy P4a deliberately left unruled, the
    neighbour's response to expansion, tribute naming an address.
  - *P4b.4 — the grade and the endings.* The one Partner grading
    view, the tiers, the card that shows its work, `operation` and
    `on_the_hook` with their texts, and the §2.5 matrix rows.
  - *P4b.5 — bots, battery and study.* The Partner bot, both
    ablations, the §2.7 letters measured, FINDINGS, and human play.

  Both identity gates and all three merged batteries stay binding at
  every P4b boundary as a **containment** check — P4b touches no
  flag-off and no stand-pat surface — and **the golden is not
  regenerated in P4b either**. *Gate: full §2.7 battery + human play
  on seeds 24/39/8, written up honestly in FINDINGS.* **Activation —
  adding `partner` to `RELEASED_BRANCHES` — is a separate sixth act
  on the reviewer's explicit word**, never a side effect of P4b.5.

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

**Revision 12** responds to the re-review of revision 11, which
approved the story and gameplay design, reproduced every number, and
found two remaining model-level blockers — the last pass before the
merge disposition, recorded on paper first. No balance constants or
criteria change; the existing gates rerun WITHOUT grandfathering the
prior results.

1. *Arrested witnesses stop receiving loyalty relief.* witness_status
   correctly answered beyond_reach, but dormant_sources re-derived
   protection independently (hired ∧ aware ∧ morale ∧ unsettled) and
   forgot the arrest — a real route bust arrests a driver WITHOUT
   taking them off payroll, so an arrested Rosa's records stayed
   halved while the docket said, in the same breath, that her loyalty
   holds the record down and that the statement is the state's. The
   root correction inverts the dependency: **protection is derived
   inside witness_status** (settled beats arrested beats protected
   beats reachable — one ordered matrix), and dormant_sources
   consumes only the employees whose status IS protected. The
   complete status matrix is pinned, plus a regression through the
   REAL route-arrest transition: the bust itself must raise the
   displayed Case the moment the cuffs close.
2. *The relief allocator honors its closed-form contract.* Two
   violations inside the accepted model: a legal zero-magnitude
   protected record made the allocator BREAK instead of skip
   (reducing a 0.6 record to 0 jumped the Case 10.6 → 20.3 as every
   later cut was abandoned), and sequential per-cut subtraction let a
   floor-bound display land one ulp under 10 (10.0 →
   9.999999999999998 on accrual). The contract is now closed-form:
   **relief = min(total halvable, max(0, raw − floor))**; a
   floor-bound display canonicalizes to EXACTLY the floor; ledger
   order survives only for allocating that relief across displayed
   records (skipping zero-halving records, breaking only when the
   allowance is exhausted). The harness oracle computes the closed
   form independently rather than repeating the allocator's loop —
   it certifies the contract, not the implementation. Property
   coverage moves from single named examples to deterministic
   GENERATED sweeps over accepted magnitudes including zero:
   monotone accrual, monotone remediation, monotone protection both
   ways, docket-sums-to-meter, and exact-10 floor binding.
3. *The path forward, per the ruling.* After this bounded correction:
   rerun both identity gates and both study depths; the natural
   paired bar must clear ≥ 60% fresh. If green, P2 opens as a PR;
   after merge, the Straight Path and the Quiet Sale activate
   together. No further design or tuning ruling is pending.

**Revision 13** records the P3 authorization decisions (the Harbor War
scope), made on paper before implementation — the §2.4.3 letter plus
revision 2 item 5's channel numbers is the spec; everywhere it is
silent, the resolution below is proposed and flagged, and rulings land
before mechanics harden. Constants are placeholders in the §6.3 sense
throughout: structure is the decision, numbers are tuning, and any
§2.7 miss is reported with its decomposition, never tuned away.

1. **Randomness (the reserved-streams question, flagged first —
   rev. 9 item 1 precedent).** War jobs ARE raids: they draw the
   existing `raids` stream draw for draw under PR #3's pricing,
   exactly as disposal runs ride `routes`. Corner diversion adds no
   dice at all — it is a deterministic function of units the route
   already sold, so the `routes` stream is untouched. Rival behavior
   at war (the target's aggression multiplier, the bystander's lane,
   counter-raids, Sal's tips) stays on the `rivals` stream — the
   in-branch draw sequence differs, which is branch-side by
   definition; both identity gates keep every stream provably fresh
   flag-off and stand-pat. Per-day world facts with nobody at the
   table — the insurance offer's arrival cadence and amount — ride
   `daily(day, "war")` derived channels, incapable of perturbing any
   persistent stream. The reserved persistent `war` stream is claimed
   for genuinely NEW player-facing war dice only, and P3 names
   exactly one: the capture salvage haul (item 10). Any further draw
   the implementation finds it wants goes back on paper first — the
   stream is not a grab bag.
2. **Target strength is the existing meter, and the killing blow is
   owed to a channel.** `Rival.strength` exists (seeded 60 Sal / 70
   Vinnie; jobs priced −12 stock / −10 sabotage / −8 ledger inside
   `raids._payoff`; the oven bleed −2/day floored at 1 in
   `rivals.py`). Adopted as the war's health bar, with two proposals:
   (a) the oven-bleed floor at 1 STANDS — passive attrition softens
   but never kills, so the finishing point must come from a job, a
   corner night, the law, or a defended counter-raid; "raids alone
   must not be the answer" stays honest at the last point of strength
   too; (b) the hardcoded job prices and the lean's −15 move to named
   canonical homes in `models` with values unchanged (the respell
   rule: the war board's ledger must read the same numbers the payoff
   writes).
3. **The damage ledger and the war board.** `BranchState` grows
   `damage_ledger` — every point of strength removed from the target
   after declaration, keyed by canonical channel:
   `models.WAR_CHANNELS = ("jobs", "corners", "ovens", "law",
   "defense")`. Defense — the existing −10 for repelling their raid —
   is a fifth source §2.4.3 never names; proposal: it is recorded and
   displayed honestly, and the §2.7 channel-mix bar (no single
   channel > 60% of strength destroyed) computes over ALL recorded
   channels, defense included — folding it into "jobs" would cook the
   very row it feeds. Flagged: counting five channels where the
   criterion names four is a clarification the reviewer owns. The war
   board itself is the §2.4.3 morning readout, replacing the market
   panel in-branch: target strength and security word (the existing
   `_security_word`), oven status, crew health and injuries, war-pay
   status, per-district heat with the item-8 colors, and the ledger —
   the mixed campaign visible on screen, not implied in prose. It is
   a readout, not a menu; every menu P3 adds keeps non-destructive
   last options with destructive options never last.
4. **The four channels adopt rev. 2 item 5's numbers verbatim, as
   placeholders.** *Corners:* the hook is the existing turf block in
   `routes.resolve_route` — today the sole consumer of
   `DISTRICTS[dk]["rival"]` (the −0.4/unit watcher relation penalty).
   In-branch, units sold in a district the target owns remove
   `min(CORNER_CAP, units × CORNER_RATE)` strength that night
   (`CORNER_RATE = 0.15`, `CORNER_CAP = 4.0`); while the target's
   ovens are wrecked, rate and cap double (−0.30/unit, cap −8) — the
   outage window §2.4.3 makes sabotage's tempo. Watchers, heat,
   patrols and the oversell glut all continue unchanged. *Ovens:* the
   existing −2/day bleed is unchanged and books to the "ovens"
   channel from declaration; the doubling window above is the new
   mechanic. *The law:* the stolen ledger gains its second spend —
   hand it to the woman in the gray suit: target strength
   −`LEDGER_LAW_STRENGTH` (20), their aggression halved for
   `LEDGER_LAW_CALM_DAYS` (4), their violence factor permanently
   ×`VIOLENCE_RISE` (1.5, placeholder); no money, no Case on you —
   it is their case. The existing lean (−15, +$2,000, consumable —
   already exactly as rev. 2 item 5 left it in `rivals.negotiate`)
   stays the greedy alternative; either spend consumes
   `ledger_stolen`. Proposed in-branch only: §2.4.3 frames the law
   option as a war move, so stand-pat and the other branches keep
   today's lean alone — flagged. *Jobs:* exactly as PR #3 left them.
   The per-rival war modifiers (aggression multiplier, calm window,
   raised violence) are DERIVED at `rival_phase` from `BranchState` —
   no new `Rival` fields, so the dead-fields doctrine holds and no
   save surface widens beyond the branch payload.
5. **The vendetta lock, and one canonical home for −60.** Declaring
   sets the target's relation to `min(relation, VENDETTA_RELATION)`
   and locks it: `rivals.negotiate` refuses the target permanently
   (no truce, no tribute relief, no cannoli — the options are gone,
   not greyed), and the nightly war tick clamps the target's relation
   to ≤ `VENDETTA_RELATION` so no scattered `relation +=` site can
   quietly thaw a vendetta. `models.VENDETTA_RELATION = −60.0`
   becomes the one home: `straight.FEUD_RELATION` rebinds to it and
   `sitdown.py`'s literal −60 reads it — values identical, so
   flag-off arithmetic and the frozen scene prose move not one byte.
   Escrow's `WAR_RELATION = −50.0` is NOT unified: it is the buyer's
   deliberately looser clause, ruled in rev. 8's constants pass —
   named here so a fourth spelling never appears. Declaring on a
   rival already at ≤ −60 costs nothing extra, exactly as §2.1 says:
   the lock and the clamp are the only mechanical price of vendetta,
   and that rival has already paid it.
6. **Side-picking is disposition, not dice.** The letter reads
   deterministic and stays that way — the bystander's lane is a
   function of who they are, and no RNG question arises. *Sal as
   bystander* (war on Vinnie): posture merchant — his aggression
   takes no war multiplier, and he raises insurance: a standing
   offer of `INSURANCE_RATE` ($800/week, §3.3's number) payable from
   dirty first; while paid he takes no hostile act, while declined
   his tip chance in the existing action roll triples, and a war-time
   Sal tip books `TIP_CASE` (3) as a *paper* record alongside its
   heat — an anonymous report in the file, contestable, per rev. 10's
   informant-tip taxonomy (flagged: §2.4.3 promises "Case pressure
   from a man who never throws a punch", and today's planted tip is
   heat-only; the paper record is the proposal). *Vinnie as
   bystander* (war on Sal): posture opportunist — no insurance; while
   your shop is damaged or any crew member is injured his act chance
   takes ×`OPPORTUNIST_MULT` (1.25) and the violent share of his roll
   rises — he raids opportunistically, exactly when you are weakest.
   Tribute to the bystander stays available and dirty-funded,
   unchanged.
7. **War pay is the paid-loyalty primitive's third face** — the same
   shape as settlements and severance, not a fourth flavor: one
   canonical constant (`models.WAR_PAY_PER_HEAD = 20`/night),
   affordability resolved before mutation, the refusal narrated
   never silent, the outcome persisted in `BranchState` and
   validated. It differs from the two clean-only faces in exactly
   one letter-assigned way, flagged as such: §2.4.3 says dirty money
   funds war pay, so the nightly charge (every hired, unarrested,
   read-in — aware — crew member) draws dirty first, then clean.
   A night that cannot cover it routes through the EXISTING
   payroll-short consequence — the same "people notice" line and the
   same roster-wide morale hit, not a new machine. Persisted:
   `war_pay_paid` (cumulative, the §2.7 staff-spend component reads
   it) and `war_pay_short_nights`. Refusing war pay is not offered
   as a menu choice — the refusal IS the short night, exactly as a
   short payroll already works.
8. **Heat grows district teeth — the §2.6 ruling comes due, and it
   lands branch-side.** Three named constants (placeholders):
   `HEAT_AMBER = 50.0`, `HEAT_RED = 80.0`, `HEAT_SLOW_DECAY = 3.0`.
   In-branch: (a) a district at heat ≥ AMBER halves covert appetite —
   route drops and per-stop want ×0.5, which the corner channel
   inherits: an overheated turf physically cannot deliver its cap —
   "burn a neighborhood taking it and you've taken ash" becomes
   arithmetic, since the raid's own +12 heat pushes the turf toward
   AMBER; (b) at ≥ RED, route planning refuses the district, with
   the reason stated on the menu (invariant 8) — nothing destructive,
   nothing silent; (c) nightly decay in a district at ≥ AMBER slows
   from 5 to `HEAT_SLOW_DECAY` — the city remembers where the
   trouble was. The flag-off decay literal 5 moves to
   `models.HEAT_DECAY` with its value untouched (bit-identical;
   gate-verified). Flagged loudly, twice: (i) scope — P3 turns the
   teeth on for the war branch only, each later branch adopting them
   in its own phase under its own studies (rev. 9 item 16
   precedent); the alternative (all active branches now) changes
   merged Straight/Sale behavior mid-flight and their batteries
   would have to re-clear — reviewer's call; (ii) the stand-pat
   control keeps today's flat 5 by construction, so the teeth are
   provably inert outside the fork.
9. **Counter-raids scale; Burned Out is defined precisely.** While
   at war the target's act chance takes ×`WAR_AGGRESSION` (1.5), the
   violent share of the action roll takes ×`WAR_VIOLENT` (1.5), and
   their raid's attack roll gains +`WAR_RAID_EDGE` (2.0) — bigger
   and more often, still on the existing 2–3-night telegraph
   (invariant 7 untouched). Burned Out: an incoming raid that LANDS
   — the fight lost, or the emptied-stash decoy taken — while
   `shop.damage_days > 0` at the moment it lands ends the run that
   night (`burned_out`, §2.5 precedence 2). Repelling averts it;
   tribute averts it; the two telegraphs are structural (the warning
   countdown plus damage already visible on screen). Flagged: the
   decoy counts as a landed raid under this definition — the shop
   was hit and took its two damage days; what saves you is repelling
   or averting, not misdirection. If the reviewer reads "successful
   raid" as fight-loss only, one clause moves.
10. **Capture-lite, per §6.4.** At target strength ≤ 0: the rival is
    broken (the existing `alive` property), the key joins
    `BranchState.captured`, and the district's underground — only
    that — transfers: route drops and per-stop want in the target's
    owned districts gain +`CAPTURE_UNDERGROUND` (0.5) to the
    underground factor, and the watcher penalty dies with the
    watcher. Salvage from their stockroom is a one-time haul drawn
    on the reserved `war` stream — priced like a stock-theft payoff
    (want roll, thinning at their terminal alertness, wagon carry
    rules), which is the stream's single P3 draw (item 1). No second
    shop (§6.4's recommendation adopted). Breaking BOTH rivals: the
    morning after the target falls, the war board offers a second
    declaration on the survivor — same vendetta lock, no new
    sit-down; the §2.5 Syndicate cell keys on both broken. Flagged:
    the second declaration is a §2.4.3 silence ("breaking both
    rivals earns the existing Syndicate ending, now reachable on
    purpose" implies a path but names none); the board offer is the
    proposal. Also flagged: today The Syndicate lives in the
    `survived` fallthrough keyed on `rivals_alive == 0` — the war
    matrix claims that cell with upgraded text and NO new id, and
    stand-pat keeps reaching the existing text exactly as today.
11. **Remediation in the war — rev. 9 item 16's question, answered
    on paper.** Proposal: counsel and settlements unlock in-branch,
    per §2.3's letter (the verbs belong to all four active
    branches). The reading: §2.4.3's "the Case only ratchets here —
    pattern evidence never remediates (§2.3)" cites the
    kind-immunity, not a verb lockout — a war month accrues pattern
    premiums, gunfire, bodies, seizures and external witnesses,
    almost all immune by taxonomy, so the file ratchets in practice
    with counsel retained; that is the §2.7 war row's own claim
    (the remediation-resistance letters, as replaced rev. 16-17). Turning the verbs
    off would also orphan the dual-use counsel ceiling and make
    retention dormancy — the §2.6 primitive war pay itself extends —
    dead in the one branch that pays people the most.
    `State.dormant_sources`' straight-only guard extends to war; the
    war bot retains counsel when it can afford it. FLAGGED LOUDLY:
    the letter genuinely reads both ways, and the war rows can pass
    under either; if the ruling is verbs-off, the guard stays
    straight-only and the bot drops counsel — nothing else moves.
12. **Terminals and endings.** New ids: `harbor_yours` (target
    broken, the other standing — graded by what's left of you),
    `long_war` (day 30, target standing: graded by the strength
    ratio and what remains of shop and crew; the epilogue says the
    vendetta outlives the month), `burned_out` (item 9, precedence
    2, set at incoming-raid resolution — before the broke check,
    after the accrual-time arrest latch which continues to outrank
    everything). The Syndicate: existing text upgraded, no new id
    (item 10). Won the War, Lost the Verdict: a text arm on
    `arrested` when the latch day ≥ `target_broken_day` — the same
    terminal, styled for the player who earned both outcomes, per
    §2.5's one styling exception. The epilogue dispatcher grows one
    war arm; `_check_endings` keeps its ladder shape.
13. **`BranchState` grows, and validation grows with it (the
    standing rule).** `_BRANCH_FIELDS["war"]` extends to:
    `damage_ledger`, `war_pay_paid`, `war_pay_short_nights`,
    `captured`, `second_declared_day`, `law_calm_until`,
    `violence_raised`, `insurance_paid_until`, `target_broken_day` —
    all defaulted, so the P1a constructor contract holds. A
    `_validate_war` arm joins the chain: `war_target` a real rival
    key distinct from any in `captured` until broken; `declared_day`
    ≥ 1; ledger keys ⊆ `WAR_CHANNELS` with finite, nonnegative
    values; day-ordering sane (declared ≤ broken ≤ second
    declaration). `validate_cross_state` binds the payload to the
    world: every captured rival dead in the same save,
    `target_broken_day` implies the target's strength ≤ 0, an
    insurance grant only from a living merchant bystander. Malformed
    payloads are refused, not repaired, with doctored-payload probes
    in the P2 style. Save stays v3: additive fields with `.get`
    defaults.
14. **The war bot, its ablations, and the gate.** `WarBot` is a thin
    policy over `MarketBot`, like its three siblings. Target:
    VINNIE, fixed for the study (the §3.3 exemplar; his two owned
    districts make the corner channel exercisable and his aggression
    makes the defense game real) — flagged as a study constant, not
    a product rule; the chair itself names either rival. Policy
    sketch: sabotage when security reads sleepy/wary to open the
    window; corner routes into target turf inside the window,
    avoiding RED districts; jobs only when the security word and
    cooldown say so (paced, never on cooldown alone); the ledger
    goes to the law, not the lean; war pay every night it can;
    counsel per item 11; tribute to the bystander when telegraphed;
    decoy defense when the stash is light. Ablations: `RaidOnlyBot`
    (jobs channel only — must trail the mixed bot's success rate by
    ≥ 15 points) and `CooldownRaiderBot` (raids on cooldown ignoring
    alertness — the pacing letters' comparison fleet, rev. 16-18).
    The gate is the §2.7 war letter, nothing softened: median end
    strength ≤ 50% of fork-day value; the remediation-resistance
    letters; channel mix ≤ 60% in successful runs; the branch-good
    band 25–70%; plus the standing rows — pairwise vectors, ledger
    transparency, telegraphy, crash-freedom (a `ChaosWar` fleet),
    reachability unchanged — and the raid-pricing decline curve
    re-verified at war cadence: the `raids` study's three-attempt
    probe rerun under war-branch conditions (war-scaled aggression,
    the bot's actual attempt spacing), reported beside the round-5
    numbers. The escrow and straight batteries rerun with all P3
    code in the tree and must reproduce to the digit — the new
    branch is provably inert outside its chair.
15. **Corrections folded in, for the record.** (a) §2.4.3's
    alertness-economics citation carried FINDINGS round 4's
    $781 → $597 → $438 — numbers round 5 superseded ($752 → $556 →
    $413) after the issue-4 fix showed round 4 inflated by
    bug-awarded successes; the body text is amended in this
    revision's commit. (b) The scene's commit path replaces exactly
    the war arm of the loud failure; `partner` keeps raising
    `NotImplementedError`, and the P1 probe test already probes
    partner — it moves to partner-only naturally, as recorded.
    (c) War does NOT join `RELEASED_BRANCHES` in P3's
    implementation: the gate passing opens the PR, and activation is
    its own reviewed commit after merge — the P2/activation
    precedent, kept.
16. **Held scope, confirmed.** No war declared from stand-pat
    (§6.7 stays v1.1); no second shop from capture (§6.4); no
    Straight/Sale constant moves; no flag-off or stand-pat surface
    moves — both identity gates on 3.11 AND 3.12 remain the standing
    bar, with the frozen scene schema at v1 (the war commit path is
    branch-side: a stand-pat run never reaches it).

**Revision 14** responds to the review of revision 13, which approved
the campaign arc and the branch's story outright, verified the
paper-only branch against merged main, ruled on every flagged
question — and found the proposed model structurally one-war-shaped:
revision 13 describes two sequential wars while proposing state,
accounting and endings that represent only one. Recorded on paper
before implementation; the corrections below are the review's rulings,
and the amended body text (§2.2, §2.4.3, §2.5, §2.7, §3.3) lands in
this revision's commit.

1. **Four story corrections.** (a) The war board AUGMENTS the market
   board, never replaces it — price intelligence is what makes a
   corner route a choice, and removing it would weaken the Dope Wars
   half (§3.3 D14 amended). (b) The ratchet thesis is restated:
   gross war evidence ratchets upward and most of it is immune by
   kind, but eligible paper and employee testimony remediate exactly
   as anywhere — "nothing ever comes off" was an absolute meter
   claim the design itself contradicts by enabling the verbs
   (§2.4.3 and the §2.2 row amended). (c) Sal's insurance cannot be
   both "standing $800/week" and randomly arriving: it is a
   predictable protection invoice — offered when the war starts,
   seven nights of coverage, renewable when it expires; fixed rate,
   no dice anywhere. (d) A second war never erases the first
   victory: one broken rival remains The Harbor Is Yours even with
   the second vendetta unfinished; the epilogue may add that the
   next war has begun (item 9).
2. **Campaigns are represented per rival.** The flat fields of
   rev. 13 item 13 — one target, one ledger, one broken day, one
   calm timer — cannot represent a second declaration without
   overwriting history. A typed **`WarCampaignState`** exists per
   declared rival, carrying at least: the rival key; declaration
   day and starting strength; broken day; the damage records; law
   calm / violence-escalation state; capture and salvage state; and
   whether the capture transition completed before the arrest latch.
   `BranchState` retains only genuinely branch-wide facts
   (cumulative war pay paid and shortfall among them), and no field
   duplicates what a campaign can derive — `captured` alongside a
   campaign's broken day was exactly that duplication, and it is
   gone.
3. **One rival-damage authority.** Strength is mutated directly
   today in raids, sabotage, oven bleed, ledger leverage and
   defense; writing ledger entries beside each subtraction would
   drift inevitably. Every strength change flows through one
   function that applies the correct passive floor, records the
   ACTUAL damage applied net of overkill, attributes it to the
   active campaign, detects capture exactly once, and preserves
   flag-off behavior bit for bit. Damage records are **append-only
   and typed**, never a mutable channel dict, and store **integer
   hundredths of a strength point** so 0.15/unit corner damage
   cannot recreate the project's floating-point scars. The
   canonical channels are `("jobs", "corners", "ovens", "ledger",
   "defense")` — **"ledger" covers both the prosecution and the
   existing greedy lean (−15)**: calling the channel "law" while
   silently omitting the lean would make the accounting false.
4. **One rival-policy view.** Rival behavior is a threshold ladder;
   multiplying "tip chance" or "violent share" inside it can make
   later rungs unreachable or push probabilities past one. One
   normalized policy view carries: act probability, action weights,
   raid attack modifier, insurance suppression, law calm, permanent
   violence escalation, and the opportunist modifiers — and the
   SAME view drives execution and any player-facing explanation. A
   factual premise of rev. 13 item 6 is corrected here: Sal's
   planted tip is NOT heat-only — `_plant` already books a 4-point
   paper record at 30% alongside the +12 heat. The war design
   deliberately modifies that existing behavior; the proposed extra
   3-point record is withdrawn (ruled: no, pending
   reconciliation). The vendetta lock likewise becomes a
   **relation-mutation authority**, not a nightly clamp — eventual
   consistency is not a lock.
5. **One territorial-demand view.** Heat suppression, event
   multipliers, base underground demand and capture bonuses meet in
   one route-market view consumed by interactive drops, automated
   routes, per-stop demand, the market display, and corner damage.
   The amber ambiguity in rev. 13 item 8 is resolved: **amber
   halves the district's total nightly sale capacity, applied once
   in the view** — never once per axis, which would quietly
   compound toward a quarter. War-only heat teeth for P3 are
   APPROVED, and the implementation must be one shared heat-policy
   authority, never scattered `branch == "war"` checks; RED is
   enforced at planning AND revalidated at service time.
6. **A typed incoming-raid result.** `incoming_raid` returns a bare
   boolean and mutates `damage_days` — checking Burned Out
   afterward would make every lost fight look "already damaged"
   because the raid itself just added the damage. The result now
   carries: landed / repelled / averted; damage immediately BEFORE
   impact; damage caused tonight; and defense damage dealt to the
   attacker (which the damage authority books to the `defense`
   channel). Burned Out reads the pre-impact value. The decoy
   counts as landed (ruled, as proposed) — and the defense screen
   must explicitly warn when a choice will end the run.
7. **Salvage is a physical pickup.** A rival can fall to a route, a
   prosecution, or a defended raid — an automatic stock-theft-style
   haul has no well-defined crew, wagon or capacity at that moment.
   Capture creates a **one-use salvage opportunity**: collecting it
   occupies the wagon and appropriate crew, obeys carry and storage
   limits, and is revalidated transactionally at execution. The
   `war` stream owns a **fixed, tested draw budget per capture
   pickup** — rev. 13's "exactly one draw in P3" is rejected: two
   captures imply two pickups, and stock-theft-style generation
   naturally draws more than once.
8. **Shared machinery, never parallel copies.** Remediation stays
   ON in the war (ruled — the reading of §2.3 stands, and the
   crew-versus-Case tradeoff is wanted). But war must not call
   Straight-specific wrappers or grow parallel twins: counsel
   availability, laundering enforcement, witness settlement,
   retention protection, validation and docket rendering answer to
   **one branch-capability policy**. War pay is **one transactional
   nightly obligation result**: base payroll and rent resolve
   first; if base wages fail, no war bonus is paid while ordinary
   wages bounce; war pay then draws dirty first, then clean;
   affordability is checked before mutation; one short night
   produces exactly ONE roster-wide morale penalty, never two; and
   the actual amount paid and the shortfall persist separately.
9. **Campaign scope, targeting, and the endings.** While a campaign
   is live, outgoing jobs target the declared rival only — attacking
   the bystander is a two-front-war mechanic, outside P3. A planned
   raid revalidates at night: the service route may have broken the
   target first. The second declaration is approved, one front at a
   time, and the offer STAYS AVAILABLE after the first capture — a
   standing war-board option, never a missable one-morning prompt.
   The §2.5 matrix becomes campaign-count based (body amended):
   zero rivals broken → A Long War; one broken → The Harbor Is
   Yours, with a text variant when a second vendetta is open; two
   broken → The Syndicate. *Won the War, Lost the Verdict* applies
   only when a capture transition completed BEFORE the arrest
   latch — transition ordering, never calendar-day equality (§2.5
   precedence text amended).
10. **The gate, amended before implementation (§2.7 body amended).**
    Pattern+physical is measured as a share of **gross post-fork
    evidence accrued**, not net Case growth after remediation.
    Channel mix computes from **actual applied damage, per
    campaign**, with the aggregate mix reported as a diagnostic.
    `RaidOnlyBot` is defined as taking no proactive non-job
    channel — incidental defense damage stays visible in its
    ledger. A **restaurant-neglect ablation** joins the battery: a
    no-cover/no-pantry war bot must trail the complete bot by ≥ 15
    success points, or the Fast Food Tycoon half is decorative and
    the branch fails review. A nightly reconciliation oracle
    asserts each campaign's starting strength minus current
    strength equals its damage records exactly (integer hundredths
    make exactness meaningful). Pinned regressions must cover:
    second-campaign save/load; overkill; a route that breaks the
    target before a planned raid runs; the pre-impact Burned Out
    state; arrest-before/after-capture ordering; and obligation
    atomicity. Both identity gates and the Straight/Sale batteries
    remain unchanged.
11. **Rulings recorded, for the table.** War RNG ownership approved
    with deterministic insurance and the per-pickup draw budget;
    the defense channel approved as fifth, measured on applied
    damage; remediation ON with the ratchet thesis rewritten;
    war-only heat through the shared policy authority; the decoy
    counts as landed, read pre-impact, with the fatal-choice
    warning; the second declaration approved as a standing offer;
    prosecutor option war-only; dirty-first war pay,
    transactionally; the oven floor at 1 stands; Vinnie stays the
    fixed study target; Sal's extra tip record withdrawn. With
    these contracts recorded, P3 implementation begins from a model
    that supports the whole campaign.

**Revision 15** responds to the review of the P3 implementation at
7b4e53a (FINDINGS round 10), which confirmed the mixed-war core —
the legible damage ledger, jobs a minority of the damage, the
raid-only collapse, the rival personalities, the campaign and
mutation authorities — and found seven blocking defects, "mostly at
system boundaries — the exact place where one-off patches would be
dangerous." Recorded on paper before the correction pass; every
correction below is the review's ruling.

1. **The declared target takes no tribute.** `incoming_raid` offered
   tribute from anyone — reproduced: Vinnie's raid averted for
   $1,500 the same week the declaration closed his tribute door
   forever. ONE incoming-raid policy: the declared target's raid
   offers no tribute at all; the bystander's still does; the WarBot
   pays only the bystander. Raid constants stay frozen until this
   lands — closing the escape hatch may itself re-price the
   cooldown grinder.
2. **Night assignments and physical storage get shared
   authorities.** Salvage shipped two regressions (both
   reproduced): a driver could take the pickup at service and the
   raid the same night, and the pickup stuffed 49 bulk into a
   40-bulk stash while ignoring the warehouse; a planned pickup
   also could not be cancelled. The structural fix, not another
   reserved= list: ONE NightAssignments authority owns employee and
   wagon reservations for routes, raids and salvage — planning and
   execution revalidate the same view; ONE haul-placement authority
   fills shop then warehouse then reports what stayed behind, and
   the raid payoff and the salvage pickup both consume it (the raid
   storage loop is extracted, never duplicated).
3. **Post-payoff economic failure exists in every active branch.**
   Clean insolvency was Straight-only scope (rev. 9 item 11); at
   war, three empty payroll-short nights left game_over None — and
   worse, Carmine still fronted groceries onto a PAID debt
   (reproduced: zero pantry, zero debt → 40 pantry, $300 debt).
   Corrections: Carmine's emergency credit exists only while the
   Act I debt is genuinely alive — gated for ACTIVE Act II branches
   (the sale loses mid-escrow fronting; recorded as an intentional
   battery-moving change); flag-off Act I and stand-pat keep the
   old behavior TO THE BYTE, because the golden and stand-pat
   surfaces are frozen and stand-pat is the control — the carve-out
   is stated here, not hidden. One shared post-payoff insolvency
   transition (two consecutive payroll-short nights with no stock
   and no dirty anywhere → broke) with one persistence contract,
   consumed by Straight and War alike; arrest keeps precedence.
   Straight and Sale batteries rerun and any movement is recorded,
   never grandfathered.
4. **The Syndicate becomes an explicit terminal (`syndicate`).**
   Grading two captures as generic "survived" let the epilogue's
   ordering print the legitimate-exit text over a two-capture war
   (reproduced: both rivals broken, Case 0, net > $20k). The
   earlier no-new-id ruling is OVERTURNED: the §2.5 cell now names
   its own id (body amended). Also corrected: RaidResult's
   damage_added reports the actual delta (damage 1 → 2 reported 2,
   not 1).
5. **The approved territorial route-market view gets built.** The
   calculation stayed split across resolve_route, the per-stop
   demand, corner_diversion and the display, and the market board
   never explained capture demand or amber capacity. The promised
   immutable view now drives the market display and route labels,
   automated and interactive capacity, per-stop demand, the capture
   bonus, the heat policy, and the corner terms — with flag-off
   arithmetic exact (the frozen expressions move INTO the view
   unchanged; every flag-off adjustment stays +0.0 / ×1.0 by
   construction).
6. **Insurance persistence completes.** Paying the invoice now
   cancels an outstanding Sal raid warning, with narration ("seven
   quiet nights" was a lie to a telegraphed raid); declaring on Sal
   clears any remaining coverage; cross-state validation requires
   paid insurance to belong to a living, undeclared-upon Sal — the
   impossible payload is refused.
7. **The law's calm is four rival phases, not five.** The spend
   lands before that night's rival phase and the inclusive
   day + 4 comparison suppressed five actions. The window is
   restated as a phase count and pinned by counting actual
   suppressed rival phases through real nights.

Rulings on the round-10 misses, verbatim in substance: the
pattern+physical bar stays FROZEN at ≥ 50 for the corrected-engine
rerun — no reclassifying employee testimony (it is narratively
correct), no artificially funded bot; if it still misses, the
thesis is revised toward actual remediation resistance, not the
taxonomy. The cooldown grinder remains blocking: no flat Case or
injury constant; first close the tribute and assignment escape
hatches, and only if grinding still wins does target alertness feed
ONE visible war-pressure policy — declining job impact and rising
target retaliation, so a failed attempt worsens the future
campaign instead of merely failing tonight. The neglect study is
INVALID as run: NeglectWarBot's cover_stops changed Act I (79 vs 76
entries, seven divergent entry seeds) and Carmine's grocery credit
subsidized it — every branch ablation must hold pre-fork state-hash
equality per seed, asserted by the harness, with paired outcomes
compared from identical entries (common-entry deltas read 14.9 at
150 / 24.6 at 500, dispositive only after isolation is repaired).
The raid-price "drift" is RETRACTED: round 5 ran 2,000 trials and
current code reproduces it exactly at that depth ($752 → $556 →
$413 consecutive; $752 → $675 → $607 at two quiet nights); the
probe propagates one trial count and reports paired uncertainty. A
causal heat report joins the study — amber/red exposures, lost
target-turf capacity, and corner damage with the heat policy on
versus off — because unit tests prove the formula exists, not that
heat became load-bearing.

The expected green after the pass: the full suite, lint and types;
both identity gates exact; Straight/Sale batteries unchanged except
where item 3 intentionally moves them, recorded; clean ablation
entry identity; the corrected 2,000-trial raid comparison; the war
gates rerun at 150 and 500; and no activation until the cooldown
criterion genuinely passes.

**Revision 16** responds to the re-review of the rev. 15 correction
pass at e0c5bef, which reproduced every reported number and gate,
accepted the fronting movement — and found four root contracts still
false and two core mechanics not yet load-bearing. Recorded on paper
before further work; the corrections below are the review's rulings.

1. **Evidence grows an immutable accrual.** The study's "gross"
   collector read records at the night hook, AFTER counsel and
   settlements had mutated them (reproduced: 10.0 of paper accrued,
   4.0 seen) — so the 46%/50% kind-share readings overestimate and
   cannot decide any criterion. Root fix: every record carries an
   immutable `accrued` magnitude beside the mutable effective one,
   written at accrual (and moved in lockstep by the suspicion
   record's top-ups, which are genuine accrual); validation binds
   `0 ≤ effective ≤ accrued` at the persistence boundary; migration
   loads absent `accrued` as the stored magnitude (pre-contest
   values are unrecoverable, said plainly); the study reads accrued
   values only.
2. **The night-assignment view owns commitment AND execution —
   really.** The night still recomputed
   `wagon_free = plans.get("route") is None`, ignoring salvage
   (reproduced: the pickup used the wagon at service and the raid
   got it back after dark). The expression is replaced by the one
   view, and the route/raid/salvage matrix is exhaustively pinned:
   one employee executes at most one job; route and salvage are
   mutually exclusive wagon owners; a raid gets the wagon only when
   neither committed job owns it; scrubbing one job produces one
   deterministic reassignment (a route scrubbed at commit frees the
   wagon for the raid's carry — the flag-off behavior; a pickup
   scrubbed at execution keeps its commitment — the wagon went out
   and came back empty).
3. **"Every active branch" includes the Quiet Sale.** Two empty
   payroll-short escrow nights left game_over None and validation
   accepted it. The sale gets the shared transition and the
   persistence invariant (insolvent_days joins its field set); its
   battery reruns and any movement is recorded. The
   narratively-tempting exemption is declined, per the ruling.
4. **The second campaign gets exercised, measured, and named.**
   Zero Syndicate endings across every fleet at both depths traced
   to two seams: the study still recognized the retired
   survived-plus-two-broken form instead of the `syndicate`
   terminal, and the bot carried one global broken flag plus a
   hardcoded "Vinnie's turf" — after declaring on Sal it stopped
   pursuing jobs and corners entirely. Corrections: terminal
   classification gets one canonical vocabulary (war.GOOD_ENDINGS,
   consumed by grade and the study); the bot derives its live
   target, its turf and its board state from the morning board
   each day (no stale globals); and the study adds longitudinal
   rows — second-front declarations, salvage collections, second
   captures, Syndicate endings.
5. **The cooldown criterion is replaced on paper — the pacing
   requirement stays, the arbitrary 20-point magnitude retires.**
   The raid-only row validates channel diversity, not pacing; a
   naive cooldown policy beating the paced one 55–36 means the
   player lesson is still "attack whenever physically possible."
   The new letter: (a) a controlled equal-opportunity comparison
   must show paced attacks produce better applied strength damage
   per committed crew-night and lower retaliation/injury exposure;
   (b) at 500 seeds the alertness-aware full policy must NOT trail
   the cooldown policy; (c) the war board shows the actual
   job-impact and retaliation multipliers, not adjectives. Per the
   ruling this needs a smarter expected-value pacing policy or a
   positive quiet-window benefit, not another slope tweak — the
   paced bot's two-night minimum gap (which forgoes open windows
   the world already priced) is replaced by window-rational
   raiding: full-price attacks whenever the security word says the
   window is open, waiting only when it is shut.
6. **The pattern+physical kind-share bar is replaced with actual
   remediation resistance** (measured on true accruals, item 1;
   the taxonomy is untouched — employee testimony is narratively
   correct): (i) the median share of post-fork ACCRUED evidence
   still effective at the ending, bar proposed ≥ 50% (permanent
   mutations only — reversible retention dormancy is not
   remediation and does not reduce "effective" here); (ii) the
   proportion of war runs ending with the Case above its fork-day
   value despite remediation, bar proposed ≥ 60%. Both proposed
   values are flagged for confirmation; the structure is the
   ruling's.
7. **Heat's consequence flows through the customer pool.** With
   teeth on/off the ending rates and corner-damage medians were
   identical — the −4/night corner cap masks the halved capacity.
   RouteMarket now applies the heat capacity multiplier to the
   EFFECTIVE corner cap (amber halves tonight's divertible
   custom, exactly as it halves the stops), heat stays war-local,
   and the study measures target-turf units and corner damage on
   exposure-matched seeds — never a noisy global ending-rate
   swing.
8. **The Syndicate epilogue renders from the damage ledger.** The
   ending named the prosecutor even for a player who never spent a
   ledger with the law; the text now names only the channels the
   campaigns actually used, with the gray-suit clause keyed to a
   prosecution (violence_raised), not to victory.

Verification expected after the pass: the standing green (suite,
lint, types, both identity gates exact), the Straight battery
unchanged, the Sale battery rerun after truthful insolvency with
movement recorded, ablation entry identity at zero, and the war
gates rerun at both depths under the replaced criteria. No
activation before the new pacing letter genuinely passes.

**Revision 17** responds to the re-review of the rev. 16 pass at
b4f4582, which independently confirmed every check and number —
and ruled that several instruments and one core product contract
encode the wrong model. The war's story is accepted; the
corrections below are the review's rulings, recorded before any
further implementation. Items 1–2 are CORE scope that precedes and
underlies P3; items 3–6 are the blocking P3 findings; item 7
replaces the neglect letter.

1. **The wagon gets one coherent inventory model: RouteManifest.**
   A player correctly reported that 12 Extra Oregano (bulk 2)
   silently fills all 24 slots and the planner's disappearing
   prompts make a full wagon look like the end of planning; review
   confirmed and found the deeper incoherence — the route
   calculations count FIVE incompatible quantities (capacity in
   bulk slots; pizzas against a hard-coded 12; coded stops by
   product categories; suspicion/lateness/heat by contraband
   units; corner damage by units sold). Rulings, verbatim in
   intent: the unexplained `min(12, …)` pizza cap is REMOVED — a
   pizza-only route with 24 real orders, ingredients and oven
   capacity loads 24 (README's "24 cargo slots shared between
   pizzas and product" was always the contract; the test calling
   12 "full pizza capacity" pinned a defect); if a stop-count
   limit is ever wanted it becomes a separate, NAMED route-time
   meter applied consistently to legitimate and covert stops, not
   a buried constant; ONE typed `RouteManifest` owns cargo bulk,
   pizza bulk, remaining capacity and validation; the sequential
   disappearing prompts are replaced by an editable manifest where
   every product stays visible — including disabled rows with
   their reasons; inventory displays read units × bulk each =
   bulk used at the shop, the warehouse and the wagon; and
   over-capacity manifests are REFUSED at commit and at
   resolution, never repaired and never merely prevented by UI.
2. **The golden trace is deliberately versioned afterward.** The
   flag-off golden has pinned the 12-pizza defect since P0;
   preserving a known player-facing defect is not equivalence.
   After the inventory correction lands with its own tests, the
   golden is regenerated ONCE, as a recorded, versioned act — the
   old checksum retired by name in FINDINGS, never silently — and
   the never-regenerate rule resumes over the new trace. This is
   the first and only sanctioned regeneration; the paired
   stand-pat gate must hold across the change.
3. **The heat probe must run a legal route.** The controlled
   probe's injected cargo was 52 slots in a 24-slot wagon
   (12 oregano = 24, 10 mushrooms, 8 honey, 10 pizzas) —
   `resolve_route` accepted the unchecked dictionary, which is
   itself the item-1 defect. The 15.8-vs-21.1 heat result is
   WITHDRAWN and reruns through a legal RouteManifest. The
   organic turf-units row is also contaminated: it read
   `sold_yesterday`, which successful stock raids overwrite with
   −8 shortage signals; actual route sales get their own result
   field and the study reads that.
4. **Outgoing raids get typed attempt records.** The pacing
   comparison reported 12.8 strength damage per "committed
   crew-night" when the strongest job applies at most 12 — the
   denominator was successful `raids_led`, with the baseline
   captured AFTER the first war night (a first-night success
   vanishes), and entry-identical seeds are not an equal-
   opportunity experiment once policies diverge. Root fix: an
   append-only attempt record per outgoing job —
   attempted/scrubbed/succeeded, crew committed, actual applied
   damage — measured as damage per attempted job-night or per
   person-night and NAMED as what it is; no honest-looking
   number from a dishonest denominator.
5. **"Still effective" measures the live ledger, not stored
   magnitude.** Review reproduced a legal record with accrued 20,
   Case and docket 10, harness "effective" 20 — the harness
   ignored live retention (loyalty) relief. The 98% claim is
   WITHDRAWN. The study reports three quantities from ONE
   canonical ledger view (the docket's own): gross accrued;
   permanent residue after contests and settlements; live
   effective contribution after retention protection.
6. **The night consults execution results, not morning
   intentions.** A salvage driver lost before service prints
   "scrubbed", draws nothing, collects nothing — and the
   untouched plan still reserves the wagon against the raid,
   though the wagon never departed. `run_salvage` returns a typed
   result (wagon_used / scrubbed / collected); the night's wagon
   question reads what actually happened.
7. **The neglect letter is replaced: the restaurant sustains the
   empire, not the street fight.** At 500 seeds neglect still
   breaks its first rival but records zero double captures and
   zero Syndicates — "a hollow restaurant can help win one street
   fight, but it cannot sustain control of the city" is the
   accepted hybrid thesis. New letter, binding at 500: the
   maintained restaurant beats neglect in UNCONDITIONAL
   Syndicate-ending rate by ≥ 15 points; second-front-to-capture
   conversion, Burned Out, payroll failures and witness accrual
   ship as decomposition. No constants are tuned to it. Heat may
   stand as a local route consequence if the legal-manifest rerun
   confirms it; its organic rarity remains an honest finding.

Sequencing, per the ruling: the inventory/route model (items 1–2)
is corrected first as its own core change with its own tests and
the versioned golden; the P3 instruments (items 3–6) rerun on top
of it; then the batteries rerun at both depths under item 7's
letter. No PR, no activation, before the instruments are honest.

**Revision 18** responds to the re-review of the rev. 17 pass at
844992a, which reproduced every check, approved the Harbor War's
story and macro-balance in principle — and found five remaining
ROOT contracts (not tuning). Recorded before implementation; no
balance constant moves in this pass.

1. **RouteManifest becomes the route's actual canonical
   inventory.** The rev. 17 planner built a manifest and then
   returned parallel cargo/legit dictionaries; commitment consumed
   the dictionary WITHOUT validating (reproduced: a 25-space plan
   committed — stash deducted, an ingredient burned — and only
   resolution raised); `of_plan` coerced `legit=True/1.5/"3"`
   through `int()`; and the revise walk offered
   `min(have + loaded, …)` when planned goods never leave the
   stash during planning (reproduced: 8 in the stash, load 8,
   revise, 12 offered, service silently clamped). Rulings: a typed
   `RoutePlan` CARRIES the manifest — no parallel dictionaries,
   ever; parsing is strict, no coercion, capacity fixed by the
   model; commitment validates BEFORE any state mutation, then
   produces the live, availability-revalidated committed manifest
   and applies its inventory transaction atomically; the revise
   bound is `min(have, loaded + free // bulk)`; pins cover
   malformed types, zero-mutation rejection of an illegal commit,
   and the 8→revise→12 repro.
2. **Storage gets ONE capacity authority.** Shop→warehouse
   transfer ignored WAREHOUSE_CAP (reproduced: 202/200), and
   capacity arithmetic lives in four places (supplier, storage,
   place_haul, routes). Rulings: one authority owns space used,
   destination capacity, units-that-fit, transactional
   transfer/placement, and the persistence validation; every
   inventory prompt consumes it and STATES WHY its bound exists
   ("Warehouse: 192/200 space used; 4 more units fit"); a short
   route-loading card teaches the shared wagon ("The wagon holds
   24 cargo-space units. Each pizza uses 1. Extra Oregano uses 2
   per unit."); and the UI uses ONE term — "space" — retiring the
   bulk/slots/wagon-space mixture.
3. **The raid-attempt ledger becomes typed and append-only in
   fact.** Rev. 17 appended a mutable dict as "failed" and edited
   it to "succeeded"; the save round-tripped
   `day="banana", crew=-7, damage_h=999999`. Rulings: a frozen,
   validated `RaidAttemptRecord`, constructed locally and appended
   EXACTLY ONCE after the outcome is known; scrubs book through
   the same authority; persistence refuses invalid days, rivals,
   outcomes, crew counts, damage, and inconsistent outcome/damage
   combinations. The study renames its rows to what they measure —
   executed-job and executed-person-night efficiency, with
   planned/committed efficiency reported separately where scrubs
   belong in the denominator — and the 8.7-vs-6.1 comparison is a
   PAIRED OBSERVATIONAL DECOMPOSITION, never again labeled
   "controlled": policies share only entry state and diverge. The
   causal pacing claim gets a genuinely state-matched
   fixed-opportunity experiment; the 500-seed "full policy must
   not trail" outcome bar stays. Until both stand, the pacing gate
   has not passed as written.
4. **The organic heat cohort samples at execution time.** The
   study read heat at the night hook — after rival moves, decay
   and the day increment — and counted hot turf whether or not a
   route ran there. Rulings: one typed route-execution record
   carries the execution-time district, heat band and capacity
   multiplier, sales and corner damage; the study counts an
   exposure ONLY when a route actually executed on live target
   turf under amber/red. The controlled legal-manifest probe
   stands. Heat's narrative claim is amended: a LOCAL ROUTE TAX,
   enforced and priced — "load-bearing" at campaign level is
   unproven until organic play demonstrates it.
5. **The golden's provenance must be true.** The active golden
   still described itself as the pre-P0 v2 baseline @ 3d79d17,
   engine untouched — false since the sanctioned regeneration.
   Rulings: the artifact carries an explicit version, generation
   commit, predecessor checksum and sanctioned-change reason, and
   the harness ASSERTS that metadata; the rev. 17 golden is a
   premature intermediate of the same sanctioned correction
   (generated before the inventory contract was finished) — the
   inventory model completes first, then the FINAL corrected
   baseline is established, once, with honest provenance.

Story ruling carried: the Harbor War is approved in principle
(distinct rivals, a legible five-channel campaign, raid-only
losing decisively, a real second front, the restaurant-to-empire
thesis strongly supported, healthy ending diversity). After these
five contracts close and both identity gates and the 150/500
batteries rerun, P3 can proceed to a PR review. The chair stays
unreleased until then.

**Revision 19** responds to the re-review of the rev. 18 pass at
8fdb243, which reproduced every check and the 150-seed battery,
confirmed the planner genuinely fixes the player's 12-unit wall —
and found four blocking root contracts plus one canonical
story/spec reconciliation. Recorded before implementation; no
balance constant moves and no feature expands.

1. **Storage becomes one SAFE authority.** The rev. 18 authority
   accepted impossible live inventory: `move_goods(..., True)`
   moved one unit; `1.5` created fractional stock; an unknown
   location ("bogus") silently ALIASED the warehouse; `place_haul`
   accepted booleans, floats and negatives; `space_used({"g": -2})`
   reported zero instead of refusing. Rulings: ONE shared
   inventory-map validator — exact integers (`type(x) is int`),
   known goods, no negatives — and explicit storage locations,
   consumed by `space_used`, `units_that_fit`, `move_goods`,
   `place_haul`, the rendering, and persistence. The vocabulary
   contract finishes: player-facing inventory says only "space" —
   the card's "cargo-space", escrow's "bulk", and README's "cargo
   slots"/"bulk storage" all align.
2. **The historical ledgers bind to the actual domains.** The
   typed records accepted impossible history: a 100-person crew
   (planning caps at three), damage 99.99 strength (the largest
   job begins at 12), cool@0.5 and amber@1.0 band/multiplier
   pairs, a successfully executed RED route (planning and commit
   both refuse red), 999 units from a 24-space wagon, contested
   turf at an ownerless district, corner damage past the −8
   mechanical cap, future-dated and reverse-ordered logs.
   Rulings: every field binds to its mechanical domain;
   band↔multiplier consistency is enforced (and preferably BY
   CONSTRUCTION from the authoritative RouteMarket view);
   cross-state validation adds chronology — no record post-dates
   the state's day, and each log's days are non-decreasing.
   Studies must be unable to invent combinations gameplay cannot
   produce.
3. **The fixed-opportunity experiment is paired in fact.** Only
   bot-choice RNG was keyed per night; raid-mechanics RNG was one
   persistent stream per arm, so a skipped night shifted every
   later night's dice — and the day was incremented before the
   decay guard, diverging from production's transition. The
   review's calendar-keyed diagnostic changed the conclusion
   substantially (damage approximately TIED, efficiency and
   injury advantages retained) — encouraging for the mechanic,
   and proof the published 11.4-vs-12.4 is not certified;
   WITHDRAWN. Rulings: extract the quiet-night alertness
   transition into one canonical home used by production and the
   experiment alike; key decision AND mechanics RNG by seed,
   calendar day and channel; pin that skipping one night cannot
   shift a later night's dice; rerun without tuning. The
   full-policy outcome bar stands and currently passes.
4. **The baseline contract is independent, not self-asserted.**
   `check()` only required nonempty metadata — a golden mutated
   to version −9, commit "banana", predecessor "garbage", seeds 1
   still passed. Rulings: the harness carries an ACTIVE-BASELINE
   contract of its own — exact version, generation commit,
   predecessor checksum, reason identifier, seeds, bots, and the
   active file's sha256 — asserted before any run comparison;
   mutation tests alter every field independently and require
   rejection.
5. **The canonical text describes the current rules.** The body
   still asserted the retired pattern+physical 50% bar, the
   retired 20-point cooldown drop, "winning requires pacing",
   campaign-load-bearing heat, and four damage channels. The
   canonical sections themselves are updated (not amended): the
   honest thesis — grinding buys tempo by spending bodies; pacing
   preserves crew and improves damage efficiency, and must not
   worsen campaign outcomes — replaces the retired claims; heat
   is a local route tax; the ledger has five channels. The
   "Harbor Is Yours" epilogue also derives and NAMES the actual
   captured turf (Sal's fall captures Little Sicily; Vinnie's
   captures Old Harbor and the Meadows) instead of one generic
   district.

After these corrections: both identity gates, the 150/500
batteries, and the corrected pacing experiment rerun; the war
chair stays unreleased; the new head returns for one final
review. No balance movement, no feature expansion.

**Revision 20** responds to the final-review hold at bdc52aa,
which accepted the pacing and independent-baseline contracts,
reproduced every number, and left two model-boundary contracts
open plus stale status prose. A bounded pass; no constants, no
mechanics, no features.

1. **Storage becomes transactionally safe.** Rev. 19 validated the
   REQUESTED quantity and destination but not the source inventory
   it mutated: a source holding True moved; 1.5 became 0.5 after a
   move; an unknown "fake" row mutated without refusal; place_haul
   added 40 mushrooms to the shop, then discovered an invalid
   warehouse and raised — leaving the partial mutation behind; an
   already-over-cap warehouse was accepted. Rulings: ONE
   storage-state preflight (map validity AND space_used ≤
   space_cap); move_goods preflights BOTH locations before any
   mutation; place_haul preflights every destination, computes the
   complete allocation locally, then commits once; any refusal
   leaves every stash byte-identical. Pins: invalid source maps,
   invalid and over-cap warehouses, the partial-placement repro.
2. **The ledgers validate the HISTORY they claim, not just their
   rows.** Reproduced: capacity_mult=True passed as cool 1.0
   (Boolean equality); amber accepted 800 corner hundredths though
   amber halves the ceiling to 400; a contested Old Harbor route
   loaded into an Act I state where no war ever existed; contested
   routes predating the declaration; a raid claiming 12 damage
   while the campaign records none; campaign jobs/corners damage
   with no matching execution records; duplicate records on one
   day despite one route and one raid per night. Ruling: a
   `validate_execution_history(state)` reconciliation — canonical
   multiplier TYPE (no Boolean satisfying float equality);
   strictly increasing log days; contested derived from the
   campaign's declared/broken interval; the heat-band-adjusted
   corner ceiling; successful raid damage reconciled against
   jobs-channel damage by day and rival, and route corner damage
   against corners-channel damage by day and rival — both
   directions. Test fixtures that fabricate impossible histories
   become legal-history helpers (one job per night, records
   booked, the calendar advanced).
3. **The war-cadence probe simulates legal history.** Its
   "consecutive" arm ran three jobs on one calendar day, and the
   cadence arm applied the second quiet tick on the next attack's
   own day. Corrected: each attempt takes a fresh calendar day;
   quiet nights sit strictly between. The alertness arithmetic and
   the reported curve are preserved (the decay count per gap is
   unchanged); only the simulated calendar becomes legal.
4. **The status prose tells the current truth.** The §2.4.3 thesis
   sentence now reads the certified numbers (tied damage, ~2×
   attempts, ~2.7× injured days); FINDINGS' "Still open" section
   states P3's CURRENT result in place of the stale three-miss
   status, without extending the archaeological chain.

After the pass: the unchanged gates and the batteries rerun; the
chair stays unreleased; the head returns for a short final review.

**Revision 21** records the P4 scope (Carmine's Partner — the last
unbuilt chair), made on paper before implementation, on the P3
precedent: the §2.4.2 and §3.2 letters plus the §2.7 partner letters
are the spec; everywhere they are silent the resolution below is
PROPOSED and flagged, and rulings land before mechanics harden.
Constants are §6.3 placeholders throughout: structure is the
decision, numbers are tuning, and any §2.7 miss is reported with its
decomposition, never tuned away. This revision is paper only — no
implementation accompanies it, and §7's P4 bullet is amended only
once item 2's split is ruled.

1. **Randomness — the reserved-streams question, flagged first
   (rev. 9 item 1 / rev. 13 item 1 precedent).** The stream tuple IS
   the save schema (`rng.PERSISTENT`, today eight names: `routes`,
   `rivals`, `raids`, `staff`, `sitdown`, `brokers`, `war`,
   `straight`), and **there is no reserved `partner` stream** — the
   fork's reservation predates this branch. Proposal: P4 claims NO
   new persistent stream. The branch's dice are of two kinds and both
   have zero-cost homes. (a) *Shop 2's honest trade* is a world fact
   with nobody at the table, so it rides a derived channel exactly as
   the market and demand rolls do — see item 3, where the proposal is
   that it draws no new dice at all. (b) *Site selection, build-out
   and the points clock are deterministic by the letter* — §2.4.2
   states construction is deterministic ("the capital is escrowed
   with Carmine's own contractor"), the points cadence is a calendar,
   and the site is a choice. If the implementation finds it wants a
   genuinely new player-facing die, it goes back on paper first, and
   the honest options are named now: grow `PERSISTENT` by one
   (forward-compatible — `Streams.from_dict` already keeps a missing
   stream's fresh seed-derived state, rng.py:48–57) or claim
   `sitdown`, the one reserved persistent stream still provably
   undrawn everywhere. **Flagged:** claiming `sitdown` would retire
   the equivalence harness's cleanest undrawn-stream assertion, so
   the recommendation is to grow the tuple if a die is ever needed,
   and to need none.
2. **The multi-shop foundation is its own reviewable PR, and it is a
   refactor of the FLAG-OFF path — a first for this arc.** Every
   prior phase added code provably inert unless entered; P4's
   foundation edits `shop.py`, whose six functions run on every
   flag-off night. Proposal: split P4 the way rev. 5 split P1.
   *P4a — the foundation, zero player-visible change:* `shop.py`'s
   functions take a `Shop` (today not one of the six does —
   `stock_pantry` shop.py:27, `recompute_demand` shop.py:48,
   `simulate_shift` shop.py:74, `believable_ceiling` shop.py:119 all
   re-derive `state.shop`, and `recompute_demand` shop.py:49 plus
   `simulate_shift` shop.py:107,109 additionally hardcode
   `data.HOME_DISTRICT`); `cooks_skill` (shop.py:14) becomes
   per-shop; rent, payroll and staff assignment learn the collection
   (items 6–7). *P4b — the branch itself:* site selection, the
   capital, the points clock, shop 2, endings, bots, study, FINDINGS.
   **The P4a bar, stated honestly:** the regression-pin doctrine
   cannot prove pre-fix failure for a pure refactor — there is no bug
   to fail on. The proof is instead identity: bit-identical by
   construction (preserved operation order, unchanged arithmetic),
   both gates 300/300 on 3.11 and 3.12, AND all three merged branch
   batteries byte-identical at 150 and 500 seeds. If P4a moves one
   study digit, the refactor is wrong and is reworked, not accepted
   with a note.
3. **The order book is already shop-local; the seam is the alias
   layer, and it should fail loudly rather than mean DiNapoli's.**
   The P0 investment paid off exactly as §5 item 2 promised: `Shop`
   already owns `district`, `stash`, `demand_today`, `delivery_pool`
   and `legit_revenue_today` (models.py:1457–1473), and `save.py`
   round-trips the collection in both directions (37–38, 105–109).
   What remains is a five-property alias layer on `State` —
   `shop`, `shop_stash`, `demand_today`, `delivery_pool`,
   `legit_revenue_today`, all hard-indexing `shops[0]`
   (models.py:1524–1558) — through which roughly ninety call sites
   funnel. Proposal: P4a does NOT silently leave them meaning "shop
   0". Each alias gains a guard that RAISES once `len(state.shops)
   > 1`, so any un-migrated site is found by a test rather than by a
   player quietly banking shop 2's takings in shop 1's till; the
   aliases are then retired as their callers are migrated. This is
   the codebase's own idiom — validation refuses, never repairs, and
   sitdown.py:396 already prefers a loud `NotImplementedError` to a
   quiet wrong answer. **Flagged:** the alternative (retire all five
   in one act) is a far larger single diff with no intermediate
   green; the guard is proposed because it makes the migration
   incremental AND provably complete.
4. **One city, one day's weather: the demand shock stays global.**
   `state.demand_shock` is a single float rolled once each morning
   (models.py:1514, `shop.roll_demand` shop.py:40). Proposal: it
   STAYS one roll for the city; each shop's order book is then
   deterministic in its own district traffic, reputation, price,
   upgrades and coupon state (`recompute_demand`'s existing factors),
   times that shared shock. This draws no new dice (item 1), changes
   no save field, and is defensible in fiction — one day's weather
   over one city. **Flagged:** the alternative (a per-shop shock)
   would need a derived channel per address and would make the two
   shops' luck independent; it is a fiction question as much as a
   mechanical one, and the reviewer owns it.
5. **THE BLOCKER, flagged loudest: two wagons collide with a merged
   validator, and this is not a tuning question.** §2.4.2 buys "a
   used second wagon" and §3.2's D17 shows a two-route morning. But
   `validate_execution_history` (models.py:914–941) enforces
   **strictly increasing days** on `route_log` and `raid_log` — "one
   job a night" — and refuses the payload at save-load otherwise
   (models.py:936–940). Two routes on one calendar day therefore do
   not merely need a second wagon; they make every save in the
   branch un-loadable, and that validator is what the war's damage
   reconciliation stands on (rev. 20 item 2). Proposal, which is
   exactly D17's letter: the branch runs **two wagons but at most ONE
   covert route per night** — the second wagon runs cover-only
   (pizzas, no cargo), producing legit revenue and delivery cover for
   its address and writing no `RouteExecutionRecord`. The
   one-covert-route-a-night rule, the record's keying and the war's
   reconciliation all stand untouched. **Flagged with its
   consequence stated:** if the reviewer wants D18's read-in second
   driver to buy a genuinely simultaneous second covert run, then
   `RouteExecutionRecord` must key by (day, wagon-or-shop) instead of
   day alone, `validate_execution_history`'s chronology clause must
   widen, and the war's by-(rival, day) reconciliation must be
   re-derived — a change to merged, gate-protected code that belongs
   in its own recorded act, not smuggled into P4b. The wagon itself
   is likewise a new concept, not a bigger number: there is no wagon
   object today, only `data.VEHICLE_CARGO = 24` and
   `RouteManifest.capacity` (routes.py:26–28), plus the
   one-job-a-night authorities `phases.wagon_job`/`wagon_used`
   (phases.py:39–58).
6. **Staff is the branch's binding constraint, and it needs the one
   field it lacks.** `Employee` (models.py:8–41) has no location:
   assignment today is transient, expressed only through the nightly
   `plans` dict and read by the single authority
   `phases.night_reserved` (phases.py:22–36). Proposal: employees
   gain one persisted assignment (the shop they work), defaulted to
   the home shop so every Act I payload is unchanged; "one person,
   one job" then means one assignment plus the existing nightly
   reservation, not a second scheduling system. Shop 2 requires a
   named **manager** — an aware employee, per §2.4.2, whose loyalty
   becomes load-bearing — persisted in `BranchState` and validated
   against the live roster (item 12). `cooks_skill` (shop.py:14–16),
   which today maxes over every hired cook in the game, becomes
   per-shop: a shop with no cook assigned bakes at the floor, which
   is what makes "the roster does not double" bite. Familiarity needs
   nothing — it is already a per-district dict (models.py:26), so it
   resets in the new district for free, exactly as §2.4.2 says.
7. **Rent and payroll learn to count addresses.** `_payroll_and_rent`
   (phases.py:972–991) charges `wages + data.RENT_PER_DAY` — a
   single flat 80 (data.py:276) that is NOT multiplied by
   `len(state.shops)`, and `Shop` carries no rent field. Proposal:
   rent becomes per-open-shop at the same constant (double rent =
   two addresses × 80), keeping one canonical home and never
   respelling it; payroll is already roster-wide and needs no change
   beyond the assignment of item 6. **Flagged:** whether shop 2's
   rent should scale with its district (University Hill costing more
   than The Meadows) is a §6.3 constants question the letter does not
   raise; the proposal is a flat second rent for v1, and district
   scaling is deferred, not designed. Partner must also adopt the
   shared insolvency contract — `"insolvent_days"` joins
   `_BRANCH_FIELDS["partner"]` and the branch narrates
   `models.insolvency_tick` in its own voice, the one-line adoption
   `quiet_sale` already made.
8. **Two ceilings, one dirty pile: the believable ceiling sums.**
   `shop.believable_ceiling(state, todays_legit)` (shop.py:117–120)
   is the closest thing to already-parameterized — it takes the legit
   figure as an argument and reads only `state.shop.upgrades` for the
   `books` bonus — and it has exactly one production caller
   (phases.py:875). Proposal: the nightly allowance becomes the SUM
   of each open shop's ceiling, computed from that shop's own
   `legit_revenue_today` and its own upgrades (so `books` is bought
   per address and helps only the address that has it). Laundering
   itself stays one action on one dirty pile — §2.4.2's "two
   believable-revenue ceilings help launder" is thereby arithmetic
   rather than prose, and the branch's trap survives: the ceiling
   grows only as fast as the second shop's HONEST trade does.
9. **The capital, its denomination, and the site.** $20,000 fronted,
   itemized per §2.4.2 (build-out $9k, permits $1.5k, wagon $2.5k,
   float $3k, reserve $4k) — one canonical breakdown constant, and
   the ledger is shown, because §2.4.2's numbers are illustrative and
   the player is owed the arithmetic (invariant 8). **Flagged: the
   letter never says which money Carmine's $20k IS.** Proposal: it
   arrives CLEAN — permits are paperwork and §2.4.2 assigns clean
   money to permits, build-out and double payroll — while the points
   go back dirty-first (item 10). That asymmetry IS the branch's
   trap, stated mechanically: his clean money in, your dirty money
   out, and only crime produces the dirty. Site selection is the
   branch's first screen: any district but Old Harbor, opening on a
   rival's turf costing a steep relation hit through the
   `adjust_relation` authority (never a scattered `relation +=`), and
   the safe pick remaining a real choice per §6.5.
10. **The points clock is an obligation, and it gets a state
    machine.** One canonical home for each constant
    (`POINTS_PER_CYCLE = 2500`, `POINTS_CYCLE_DAYS = 5`,
    `POINTS_VIG = 500` — §6.3 placeholders, §6.6 adopted), never
    respelled by the card, the ledger or the epilogue. The payment
    follows the paid-loyalty shape the codebase already uses five times:
    compute what is due, resolve affordability BEFORE any mutation,
    narrate the refusal rather than fail silently, persist the
    outcome, validate it. Dirty-first, like war pay and tribute
    (§2.4.2's "unmarked bills preferred"). The machine: current →
    one missed (a warning, and `POINTS_VIG` added to the next) → two
    missed, consecutive or not → **Foreclosure, that night**. Early
    payoff (≤ day 10) defers the first cycle by one, his compliment.
    Proposal: refusing to pay is not a menu option — the refusal IS
    the missed payment, exactly as a short payroll already works
    (phases.py:986–991). Since a fourth dirty-first site now exists,
    P4 is the moment to hoist the idiom into one authority rather
    than inline it a fourth time (compare `apply_rival_damage` and
    `adjust_relation`); flagged as a small refactor of merged code,
    to be ruled.
11. **Heat's per-address teeth — §2.6's second instalment, on the
    rev. 13 item 8 precedent.** `models.district_heat_policy`
    (models.py:324–337) is gated `if state.branch != "war"`, so the
    teeth are provably inert in every other branch and flag-off.
    Proposal: partner adopts the SAME teeth at the SAME constants by
    widening that gate to the branch — no retuning, no new meter.
    Per-address heat then costs nothing to build: each shop already
    carries its district, and district heat already exists, so "each
    shop's district heat gates that shop's covert usefulness"
    (§2.4.2) falls out of the existing meters exactly as §2.6 asked.
    **Explicitly NOT touched:** whether heat should be
    campaign-load-bearing rather than a local route tax remains the
    open §6.3 constants question; P4 neither answers it nor tunes
    toward it, and the partner rows will be reported at the current
    constants whatever they say.
12. **The always-open invariant is tested, not checked.** §2.4.2
    declares that once funded the second shop opens and stays open —
    construction deterministic, raid damage limping but never
    shuttering, no partner event able to un-open an address, the only
    losses being Foreclosure and arrest, both of which end the run.
    Proposal: this binds in `validate_cross_state` (models.py:884)
    as a payload invariant — a funded partner state with fewer than
    two shops is refused, as is a second shop outside the branch, a
    site district equal to `HOME_DISTRICT`, or a manager who is not
    an aware, hired employee — and the day-30 matrix therefore
    reduces to the points ledger alone, exactly as §2.5 says. A
    third day-30 state cannot exist, and the validator is what makes
    that a fact rather than a hope.
13. **Terminals — and one flag the P3 arc earned.** `Foreclosure` is
    a pre-day-30 catastrophe written where it happens, guarded
    against an already-latched ending, exactly as `escrow` writes
    `sold` and `phases` writes `burned_out`. The day-30 matrix comes
    from a new `partner.grade(state)` joining the dispatch in
    `game.py:65–74`, returning points-current or one-outstanding.
    **Flagged, on rev. 15's own precedent:** §2.5's inventory calls
    "The Operation (two ovens)" an UPGRADED text rather than a new
    id — but rev. 15 item 4 overturned exactly that reasoning for
    The Syndicate, ruling that an outcome matrix must not depend on
    generic epilogue ordering (a two-capture war was printing the
    legitimate-exit text). "The Operation" would ride the same
    generic `survived` fallthrough (game.py:284–308). The proposal
    is therefore an explicit `operation` terminal id alongside
    `on_the_hook` and `foreclosure` — three new ids, not two plus a
    hope — and the reviewer owns the overturn.
14. **`BranchState` grows, and validation grows with it.** Partner
    owns three fields today (`points_due_day`, `points_missed`,
    `vig_owed` — models.py:466) and has NO validation arm at all:
    `validate_branch_state` (models.py:530–539) dispatches only
    quiet_sale, straight and war, so partner's entire contract today
    is "`points_due_day` is not None". P4 adds the missing arm.
    `_BRANCH_FIELDS["partner"]` extends to carry the site district,
    the capital drawn, the manager key, the shop-2 opening day, the
    points paid and the shared `insolvent_days` — all defaulted, so
    the P1a constructor contract holds and `BranchState.partner()`
    stays a keyword-only classmethod. `_validate_partner` binds:
    site a real district and never `HOME_DISTRICT`; capital a
    non-negative int matching the itemized breakdown; `points_missed`
    in 0–1 unless the run ended in foreclosure (the terminal
    invariant, in the shape `_validate_severance` and
    `_validate_insolvency` already use); `vig_owed` an integer
    multiple of `POINTS_VIG`, non-negative, zero while nothing is
    missed; days ordered (funded ≤ opened ≤ first points due). Save
    stays v3 — additive fields with `.get` defaults, and the shops
    list already round-trips.
15. **Remediation in the partner branch.** `REMEDIATION_BRANCHES`
    (models.py:96) is the single branch-capability answer consumed by
    counsel availability, the laundering ceiling, settlements,
    retention protection, hiring refusals and cross-state validation.
    Proposal: partner JOINS it, per §2.3's letter that the verbs
    belong to the active branches, and because §2.4.2 says counsel
    "is affordable here and busy" in as many words. That also keeps
    counsel's dual-use edge live where it bites hardest — a retained
    lawyer enforces the believable ceiling across BOTH ceilings of
    item 8. The four remediation fields join
    `_BRANCH_FIELDS["partner"]` and nothing else moves.
16. **The bot, the ablation, and the gate — nothing softened.**
    `PartnerBot` is a thin policy over `MarketBot`, like its three
    siblings, latching on the branch's own entry header and reading
    the shop-2 block as its intelligence. The §2.7 letters stand
    exactly as recorded: **combined legit revenue ≥ 1.5× the
    stand-pat control's by fork+8; points paid on schedule in ≥ 80%
    of runs**; the criterion-5 ablation — a bot that pays points from
    pizza margins only — must drop the branch-good rate by **≥ 20
    points**, or the trap is decorative and the branch fails review.
    Plus the standing rows: the branch-good band 25–70%, ledger
    transparency asserted nightly, telegraphy, crash-freedom (a
    `ChaosPartner` fleet answering chair index 1, per `BRANCH_ORDER`),
    reachability unchanged, and the three merged batteries
    reproducing to the digit with all P4 code in the tree. P4 is also
    where **the full §2.7 battery finally runs**: the pairwise
    eight-component profile vectors across all four branches — six
    pairs, each required to differ by ≥ 0.25 in at least two
    components — which every prior round has carried forward as the
    P4 item, and for which the obligation-outflow component (points
    and tribute) only becomes non-trivial now. §7's P4 gate also
    names **human play on seeds 24/39/8**, the first branch to
    require it; the Quiet Sale's untaken human verdict rides along
    with it.
17. **Activation is held, and the loud fallthrough stays.** Partner
    does NOT join `RELEASED_BRANCHES` in P4's implementation: the
    gate passing opens the PR, and activation is its own reviewed
    commit after merge — the P2 and P3 precedent, now kept twice.
    When partner's commit path lands, `sitdown.py:396`'s
    `NotImplementedError` has no chair left to catch; it STAYS
    regardless, as the defensive invariant for any future chair, and
    the P1 probe test that pins it (tests/test_p1_foundation.py:361)
    is retargeted rather than deleted — a build must never be able to
    enable a chair that cannot commit.
18. **Held scope, confirmed.** No calendar extension (§6.1 keeps day
    30 for every branch); no second shop from war capture (§6.4
    stands, and item 5's wagon ruling is another reason not to
    unify); no war declared from stand-pat (§6.7 stays v1.1); no
    Straight/Sale/War constant moves; no §6.3 heat re-weighting
    (item 11); no flag-off or stand-pat surface moves — both identity
    gates on 3.11 AND 3.12 remain the standing bar, with the frozen
    scene schema at v1, and P4a is measured against them precisely
    because it is the first phase whose refactor touches the
    flag-off path at all.

**Revision 22** responds to the review of revision 21, which accepted
the Partner thesis — Carmine's legitimate-looking capital creates
scale while the recurring points force the player to keep earning
dirty — and returned three rulings plus seven structural corrections
before implementation. Revision 21 is preserved unedited so the review
effect stays visible; this revision amends the canonical sections
(§2.4.2, §2.5, §2.7, §2.8, §3.2, §4 R6, §5, §7) as well as recording
the rulings here. Still paper only: no implementation accompanies it,
and none begins until this corrected paper is reviewed.

**Every reviewer claim was reproduced in code before being recorded**,
per the standing rule. Three reproductions are worth stating because
they decide items 1 and 5: (a) a cargo-less route already writes a
`RouteExecutionRecord` — `routes.py:376–377`, `units_sold=0`,
`corner_damage_h=0` — so revision 21's "cover-only route writes no
record" would have contradicted both the ledger's behavior and its
claim that every executed route is recorded; (b) `raids.py`,
`rivals.py` and `phases.py` each hard-code DiNapoli's (damage, guard,
stash overflow and seizure, reputation loss and home heat at
raids.py:323–423; the coupon and the 12 points of home heat at
rivals.py:160,192; the damage/coupon tick-down at phases.py:797–800
and the search sweep reading only home heat and the home stash at
phases.py:1156–1170); (c) `Rival.raid_warning` is a bare integer
countdown (models.py:57) carrying no address at all, so a telegraphed
raid cannot today name — let alone persist — a target address.

1. **Two genuine simultaneous routes; the cover-only exception is
   withdrawn (ruling on rev. 21 item 5).** The second wagon and the
   second trusted driver are the branch's central mechanical payoff,
   not a convenience, and §2.4.2's own letter always said so ("a
   second covert route needs a second person you trust with your
   life"). Both wagons run real routes — honest or covert — and both
   are recorded. The chronology problem is solved by identity rather
   than by exemption (item 2): route chronology becomes ordered by
   day with uniqueness on **(day, origin shop)**, Partner permitting
   one route per address per night and every other branch exactly one
   in total, so the merged one-route-a-night behavior is preserved
   everywhere it exists today. Raid chronology stays strictly one per
   day. The planning model gains four rules: distinct drivers; at
   most one owner ride-along; local orders, pantry, ovens, stash and
   upgrades; and wagon availability resolved **per address** instead
   of the single global boolean `phases.wagon_job`/`wagon_used`
   express today.
2. **Stable identities for shops and wagons — list position is not an
   identity.** Every address gains a stable key, and employee
   assignments, route origins, raid targets, storage locations and
   manager ownership all reference the key rather than an index.
   `RouteExecutionRecord` carries its origin shop, which is what makes
   item 1's uniqueness clause expressible at all, and what keeps the
   war's by-(rival, day) reconciliation intact — a war route and a
   Partner route are then distinguishable by origin, not merely by
   date. Derived world dice keyed to an address key by that stable key
   too (item 6), so no roll depends on the order shops happen to sit
   in a list.
3. **P4a is approved and broadened (ruling on rev. 21 item 2).** The
   foundation is not `shop.py` alone: it parameterizes every
   address-bound system — inventory and storage, routes, service,
   upgrades, staff, rent, rival actions, incoming raids and law
   searches — and it stays behavior-neutral while one shop exists.
   Its gate is identity, because a pure refactor has no bug to fail
   on: both gates 300/300 on **3.11, 3.12 AND 3.13**, plus all three
   merged branch batteries byte-identical **at both depths**. §5
   item 8 and §7's P4 bullet are amended accordingly.
4. **The address-level threat model is operationalized.** One
   **address-target authority** decides which address a rival moves
   against — replacing the hard-codes catalogued above — and a
   telegraphed raid **persists the address it named**, so a save or
   reload cannot retarget a warning that is already on the board
   (today it could not even name one). Every consequence follows the
   named shop: coupons, guards, damage days, stash seizure,
   reputation loss, the heat raised, and the law's searches. Staff
   assigned to an address constitute that address's defense
   allocation, which is what makes "theirs may target the softer of
   your two shops" a decision rather than a line of prose.
5. **A vacant manager's post is valid gameplay, never an invalid
   save.** Revision 21 proposed validating that the manager is always
   a hired, aware employee; that would refuse saves the player
   reached by playing correctly, since a manager can be arrested,
   poached, fired or can resign. The persisted state is therefore a
   **vacancy** — no manager, plus the day the post emptied — and the
   address stays open under Carmine's nephew at a reduced kitchen
   capacity and reduced believable ceiling, with a stated window to
   appoint a qualified replacement before the penalty reaches full
   weight. The window's length and the penalty's size are §6.3
   placeholders, named on paper here **before** any validator is
   written, which is the point of the correction: the validator
   encodes a designed state machine rather than inventing one.
6. **Randomness, tightened.** No new persistent RNG stream is
   approved — `rng.PERSISTENT` is unchanged, and revision 21's
   proposal to claim none is upheld rather than merely permitted. The
   demand shock stays **citywide**, one roll for one day's weather
   (rev. 21 item 4, confirmed). Address-specific world rolls — critic
   visits, law checks and their kin — ride **derived daily channels
   keyed by the stable shop key** (item 2), never by list order, so
   no world fact depends on the sequence in which addresses were
   opened. This keeps the world action-independent, which is the
   invariant the whole equivalence harness rests on.
7. **Points keep two books, and the ledger is typed.** One
   `points_missed` counter cannot mean both "how many times this has
   happened" and "what is outstanding right now". The branch persists
   four facts — a **lifetime strike count**, **current arrears**, the
   **next due day**, and **cumulative points paid** — behind a typed,
   append-only **cycle ledger**, one record per cycle, in the shape
   the war's `DamageRecord` and the execution logs already use. The
   arithmetic: a missed $2,500 stays owed; the next bill is prior
   arrears + $2,500 + $500 vig; paying it clears arrears and leaves
   the strike; a second strike at any later cycle forecloses that
   night. Day-30 grading reads **arrears** — zero is `operation`,
   nonzero (necessarily one strike) is `on_the_hook` — so a player
   who missed once and caught up has earned the good ending, which is
   both the fairer reading and the one the ledger can prove.
8. **The capital transaction is atomic, and construction has three
   recorded phases.** Accepting the deal commits **$13,000** —
   build-out, permits and the wagon — in one transaction to Carmine's
   contractor, creating the second `Shop` record in the same breath;
   only the **$7,000** float and reserve enter clean cash. No
   spendable $20,000 is ever deposited in the hope that later
   spending consumes it correctly. The address then exists (accepted)
   → stands under deterministic construction until its **recorded
   opening day** → is open and cannot close except through a terminal
   outcome. That is what reconciles §3.2's D14–D16, where the shop is
   plainly not yet serving customers, with the always-open invariant:
   the invariant binds from the opening day, not from the signature.
9. **Inventory is local, and the cash abstraction is stated.** Every
   purchase, improvement, storage action and route names an address.
   Supplier purchases choose their delivery address; pantry, stash and
   upgrades stay local; warehouse transfers name a source and a
   destination shop; **no free shop-to-shop transfer** exists —
   goods move by wagon or they do not move. Clean and dirty cash
   remain global, and §2.4.2 now says so explicitly rather than
   leaving a reader to infer it: one operator, one pocket, two
   addresses.
10. **The Operation gets its own terminal (ruling on rev. 21
    item 13).** `operation` joins `on_the_hook` and `foreclosure` as
    an explicit id; no Partner outcome rides the generic `survived`
    ordering. §2.5's inventory is restated in the same act, and the
    restatement records that the old count was already stale: rev. 15
    promoted The Syndicate from an upgraded text to an explicit id
    and the inventory line was never updated. The corrected census is
    **ten new ids, one new arrest text arm, one upgraded text**, with
    the governing rule stated so it is not learned a third time — an
    outcome named in a day-30 matrix gets its own terminal id.
11. **Acceptance language made unambiguous (§2.7 amended).** Combined
    legit revenue is **cumulative** across both addresses from the
    fork through fork+8, paired per seed against the stand-pat
    control, with the **median per-seed ratio ≥ 1.5** and the
    absolute dollar difference reported beside it so a small
    denominator cannot manufacture a pass. "On schedule" means
    **zero missed cycles**, in ≥ 80% of entered runs that reach at
    least one due date, with excluded runs reported rather than
    silently dropped. The criterion-5 ablation becomes **no
    post-fork covert revenue**, with inherited pre-fork dirty cash
    reported as its own line — the old "pays from pizza margins
    only" was mechanically ambiguous and hid exactly that confound.
12. **What revision 21 carries forward unchanged**, having survived
    review: the alias-layer guard that raises rather than silently
    mean DiNapoli's (item 3 there — now the migration net for a
    broader P4a); the citywide demand shock; per-shop `cooks_skill`
    and the staff assignment field; rent counting addresses; the
    summed per-shop believable ceiling; heat's teeth extending to
    Partner at unchanged constants; Partner joining
    `REMEDIATION_BRANCHES`; the validation arm the branch has never
    had; activation held for its own reviewed commit after merge;
    and the loud `NotImplementedError` fallthrough retained with its
    probe retargeted rather than deleted.
13. **Held scope, confirmed.** Heat weighting (§6.3) and the Quiet
    Sale and war human-play verdicts stay explicitly outside
    Partner's scope. No calendar extension (§6.1); no second shop
    from war capture (§6.4); no war from stand-pat (§6.7); no
    Straight/Sale/War constant moves; no flag-off or stand-pat
    surface moves — both identity gates remain the standing bar, and
    P4a is measured against them on three Python versions precisely
    because it is the first refactor in this arc to touch the
    flag-off path at all.

**Revision 23** responds to the re-review of revision 22, which
accepted every earlier ruling and returned two blocking design
contracts plus one canonical cleanup. Revisions 21 and 22 are
preserved unedited; this revision amends §2.4.2, §2.5, §2.7, §4's R9
row and §5, and records the rulings here. Still paper only, and P4
implementation does not begin: the head returns for a short
re-review.

**Both blocking findings were reproduced in code before being
recorded.** For item 1 the conflict is between the design's own
sections: §2.4.2 grades Partner on "combined net and the second
shop's reputation", while §2.5's matrix reduced the whole exhaustive
outcome to arrears — so a player could reach `operation` by keeping
one man current while running two hollow fronts, and the §2.7 battery
would have certified it. For item 2: `models.place_haul(state, haul)`
takes no destination (models.py:1317) and fills the home stash then
the warehouse; both call sites pass none (raids.py:241, war.py:545);
occupancy is a single global answer (`phases.wagon_job`/`wagon_used`,
phases.py:39–58, threaded as the `wagon_free`/`wagon_taken` booleans
into raids.py:16–19 and war.py:463–473); and the decoy option "Empty
the stash into the wagon" is offered unconditionally (raids.py:332)
by a function that receives no wagon information at all, so it can
promise a wagon already out on a route.

1. **One canonical Partner grading view, and a tycoon half that is
   load-bearing.** Arrears still selects the terminal id — `operation`
   or `on_the_hook`, and no additional id is created. What changes is
   that `operation` is no longer a single outcome: it carries explicit
   **operational tiers** derived from combined net and shop 2's
   reputation. **The view owns the arithmetic** — one derivation
   feeding the status card, the ending text, the epilogue, the bot
   studies and the human-play report, in the shape `RouteMarket`,
   `HeatPolicy` and `MarkBreakdown` already establish, so a tier
   cannot mean one thing on screen and another in FINDINGS. **"Branch-
   good" is redefined to mean the healthy tier**, never every run
   whose id happens to be `operation`; the 25–70% band is measured on
   the tier, with the id-level rate reported beside it so the distance
   between "paid the man" and "built the business" stays visible.
   **A matched restaurant-neglect ablation** joins the battery — no
   cover spend, no pantry care, at either address — and must reduce
   healthy-`operation` outcomes materially, **binding at 500 seeds**,
   recommended bar **≥ 15 points**. It stands *beside* the
   no-post-fork-covert-revenue ablation, never instead of it: the two
   prove opposite halves of the hybrid, and the war's own
   restaurant-neglect row (rev. 17) is the precedent for asking the
   hollow-restaurant question of a branch that could otherwise win
   without a kitchen. Tier thresholds and the 15-point bar are §6.3
   tuning constants; the terms, the tiers, the view and the acceptance
   contract exist before any code.
2. **The vehicle boundary is ruled whole — raids included.** "Raids:
   yours unchanged" was false the moment inventory became
   address-local, because a crew must now return *somewhere*; the
   letter becomes **"raid grammar, objectives and RNG remain
   unchanged; logistics become addressed"**, which is exactly the
   scope: no objective, no die and no combat rule moves. **One
   assignment authority owns every stable wagon** across all four
   consumers — routes, outgoing raids, salvage, and the incoming-raid
   decoy — and answers *which* wagons are free rather than *whether*
   the wagon is, replacing the global boolean. A raid **selects a
   wagon or goes on foot and names its return shop**; `place_haul`
   takes that destination explicitly, so a haul can no longer land at
   DiNapoli's because that is where the function has always put
   things. The **decoy defense requires an actually free wagon** and
   empties the **warned address's** stash; with no wagon free the
   option is rendered **visibly disabled with its reason**, never
   silently absent — the standing menu rule. **Planning, commitment,
   execution and save-load validate the same assignments**, so a
   payload cannot describe a night the engine could not have run.
   Finally, the persisted warning becomes **one typed, atomically
   validated value carrying both the countdown and the target shop**,
   rather than two independently valid fields that can disagree —
   today `Rival.raid_warning` is a bare integer (models.py:57) with
   no address at all, so this is a new typed record in the shape of
   `RaidAttemptRecord` and `RouteExecutionRecord`, validated at
   construction.
3. **R9 stops carrying its own census.** The row said "8 new IDs"
   while §2.5 said ten — the same drift rev. 22 item 10 had just
   corrected once. Rather than change the number again, R9 now
   **cites §2.5's terminal inventory as canonical** and states no
   count of its own, so the two cannot diverge a third time. Its
   mitigation also picks up the Partner operational tiers as another
   instance of graded text inside one id.
4. **Held scope, unchanged.** Heat weighting (§6.3) and the Quiet
   Sale and war human-play verdicts stay outside Partner's scope. No
   calendar extension (§6.1); no second shop from war capture (§6.4);
   no war from stand-pat (§6.7); no Straight/Sale/War constant moves;
   no flag-off or stand-pat surface moves. P4a remains
   behavior-neutral with one shop and gated on identity across 3.11,
   3.12 and 3.13 plus all three merged batteries at both depths —
   and item 2's authority is squarely inside it, since the vehicle
   boundary must be addressed before a second address exists.

**Revision 24** responds to the re-review of revision 23, which
accepted the R9 canonical-reference fix and returned two contracts
that were not yet executable as written. Revisions 21–23 are
preserved unedited; this revision amends §2.4.2, §2.5, §2.7, §5 and
§7. Still paper only, and no P4 implementation begins.

1. **The Partner tiers, made executable.** Revision 23 named a
   "healthy" tier and specified none of what a builder would need, so
   it is specified here in full. *Vocabulary and ordering:* `hollow`
   < `working` < `healthy`. *The net term:* combined net **extends the
   existing `State.net_worth` authority** to the shops collection —
   clean + dirty + warehouse cash + every open shop's stash at book +
   warehouse stock − debt — **minus current arrears**, with three
   exclusions stated rather than left to inference: Carmine's capital
   is **equity and never subtracted** (no principal is repayable),
   upgrades, build-out and wagons are **not assets** (net_worth counts
   no fixed capital today and this changes nothing), and inventories
   count at book exactly as they already do. Note that `net_worth`
   reads `state.shop_stash` — the home shop alone — so it is itself
   one of P4a's address-bound call sites. *The restaurant term:* shop
   2's own reputation meter. *The gate:* **AND**, not a trade —
   `healthy` requires both terms independently, `working` is exactly
   one, `hollow` is neither. Money must not compensate for a dead
   restaurant, which is the branch's entire thesis. *Thresholds
   (§6.3 placeholders):* combined net **≥ $8,000**, which invents no
   number — it is the game's existing one-shop "the operation holds"
   bar (a literal in the `survived` grade today) promoted to a named
   home at unchanged value; and shop 2 reputation **≥ 35**, above the
   ~20 it opens at so it must be earned rather than inherited, and
   below the 50 the home shop starts from so it is reachable inside
   the month. P4b's first study reports both distributions so the
   bars move on measurement. *Texts:* three, and `working` carries
   two arms (money without a room; a room without money) because it
   is reachable from either side and the two are different stories —
   the Sold tiers and the Won-the-War arrest arm are the precedent
   for graded text inside one id. *The card shows its work:* each
   term's value, its requirement, and the resulting tier, so the
   player can see which half of the hybrid is failing while there is
   still time to steer. **§2.7's neglect bar becomes binding** at
   ≥ 15 points at 500 seeds rather than recommended — P4b needs an
   executable contract, and the constant still moves only through the
   recorded falsification workflow.
2. **P4a cannot both fix the decoy and be behavior-identical — the
   contradiction is conceded and sequenced away.** Revision 23
   asserted in one breath that P4a corrects the decoy's wagon
   question and that P4a moves no existing-branch surface. Those
   cannot both hold: the correction changes what a released one-shop
   build offers on a menu. The reproduction stands — `wagon_used`
   (phases.py:47–58) is consulted by the outgoing raid
   (phases.py:837) and ignored by `incoming_raid`, whose decoy option
   is built unconditionally (raids.py:332) by a function that
   receives no wagon information at all — and it is an
   assignment-integrity bug in **released** code, not a
   multi-shop problem. So it lands first, on its own: **P3.5, a small
   prerequisite correctness PR**, with three pinned cases — a
   departed wagon job disables the decoy **and says why on the menu**
   (never silently absent), a salvage scrubbed before departure
   leaves it available, and no wagon job planned leaves it available.
   One precision on the ruling's shorthand, since it decides a pin:
   **"scrubbed" is a salvage-only state** — `wagon_used` returns the
   salvage record's own answer, while a planned route always reads
   busy (phases.py:57), so there is no such thing as a scrubbed
   route to pin. *Golden policy:* all three merged batteries rerun at
   both depths, and the flag-off golden is **measured before it is
   touched** — how many of the 300 runs reach an incoming raid on a
   wagon-busy night is a number to report, not to assume — with
   regeneration happening only if the corrected path is genuinely
   reached, and then only as its own recorded ruling with
   `ACTIVE_BASELINE` updated in the same act (revs. 17–18 precedent).
   P4a then generalizes the already-correct authority to multiple
   stable wagons with zero further behavior movement, and keeps the
   typed atomic raid warning, the addressed haul placement and the
   multi-wagon generalization, none of which moves single-shop
   behavior.
3. **Held scope, unchanged.** Heat weighting (§6.3) and the Quiet
   Sale and war human-play verdicts stay outside Partner's scope. No
   calendar extension (§6.1); no second shop from war capture (§6.4);
   no war from stand-pat (§6.7); no Straight/Sale/War constant moves.
   P3.5 is the one deliberate exception to "no released-behavior
   movement" in this arc, it is scoped to a single menu question, and
   it is gated on measurement rather than on assumption.

**Revision 25** responds to the re-review of revision 24, which
cleared the tier system, the sequencing and the PR record, and
returned two exact seams. Narrow by disposition: it amends only the
threshold boundary and P3.5's execution cases (§2.4.2, §5 item 9,
§7's P3.5 bullet). Revisions 21–24 are preserved unedited. Still
paper only; no implementation begins.

1. **P3.5's wagon question is stateful, and its case list is
   complete.** Reproduced: the player's outgoing raid runs BEFORE the
   incoming ones (`raids.run_raid`, phases.py:844), and the arrivals
   are a **loop over every rival** with `raid_warning == 1`
   (phases.py:846–848), each calling `incoming_raid` independently —
   so both rivals can arrive on one night. Because
   `wagon_used(plans, service_report)` is a pure function of the
   morning's plans and the service report, it cannot see either
   event: not the raid that just hauled with the wagon, nor a decoy
   that just used it. Revision 24's three cases were therefore
   necessary but not sufficient. The correction is architectural
   rather than another case bolted on: **one night-assignment
   authority holding state that each executed consumer updates as it
   runs**, so the answer reflects everything that has already
   happened tonight instead of what was intended this morning. Six
   pinned cases: departed route → unavailable; departed salvage →
   unavailable, salvage scrubbed before departure → available; an
   executed outgoing raid that **took** the wagon → unavailable; an
   outgoing raid scrubbed before departure → available (that state
   already exists and is already recorded — the `scrubbed`
   `RaidAttemptRecord` written at phases.py:825–828 when the crew
   does not survive to nightfall); the first decoy **reserves** the
   wagon against a second arrival; and fighting or paying tribute
   consumes nothing, so the wagon survives the first raid for the
   second. **One flag, because it decides the third pin:** under
   today's mechanics only a `steal_stock` raid loads the wagon —
   `carry_bulk` is computed inside `if objective == "steal_stock"`
   (raids.py:220–223), while the `ledger` and sabotage objectives
   never touch it. Read as strict execution truth, a sabotage raid
   therefore leaves the wagon free, and that is how the pin is
   written. If the intent is that any executed raid consumes the
   wagon — the crew drove *something* — one clause moves, and the
   ruling is the reviewer's.
2. **The $8,000 comparison stays strictly greater.** Revision 24
   wrote "combined net ≥ $8,000" while calling the value unchanged.
   Both cannot be true: the existing one-shop grade is `net > 8000`
   (the `survived` arm in game.py), so at exactly $8,000 the
   inclusive form flips the outcome — a silent contract change
   dressed as a promotion to a named home. §2.4.2 now reads
   **strictly greater than $8,000**, comparison and value both
   preserved. The alternative — adopting the inclusive boundary as a
   deliberate change with its own pin — is declined: there is no
   design reason to move it, and an unremarked boundary shift is
   exactly the kind of drift this project pins against.
3. **Held scope, unchanged.** Nothing else in revisions 21–24 moves.
   Heat weighting (§6.3) and the Quiet Sale and war human-play
   verdicts stay outside Partner's scope; P3.5 remains the one
   deliberate released-behavior movement in this arc, still gated on
   measuring the golden before touching it.

**Revision 26** records the ruling on revision 25's one open flag,
taken on the approval of PR #16 (merged at d18f323) and before any
P3.5 code, per the standing paper-first rule. It amends §7's P3.5
bullet and nothing else.

1. **Only `steal_stock` consumes the wagon, and departure is what
   consumes it.** Ledger photography and sabotage stay on-foot,
   light-team jobs and leave the wagon available — which matches the
   mechanics as they already stand (`carry_bulk` is computed only
   inside the `steal_stock` branch, raids.py:220–223) and gives the
   three objectives a real logistical difference rather than an
   incidental one: a stock theft costs you the wagon for the night,
   a sabotage does not, and that is now a reason to pick one. For a
   stock theft the wagon is consumed **when the crew departs with
   it, regardless of whether the raid ultimately succeeds** — a
   repelled or bungled theft still took the wagon out — while a
   **pre-departure scrub leaves it free**, which is the same
   execution-truth line the salvage pickup already draws. The
   night-assignment authority therefore records the wagon as spent at
   departure, not at payoff, and the P3.5 pin for a failed
   stock-theft raid asserts the wagon is unavailable exactly as a
   successful one does.

**Revision 27** records the P4a authorization: the subdivision into
three sequential PRs, the `net_worth` ruling, and the boundaries the
refactor must not cross. Paper only, and the first commit of P4a.1.
It amends §7's P4 bullet; everything else here is new contract.

1. **Three sequential PRs, never stacked.** P4a.1 is identity —
   stable `Shop` and wagon keys, the lookup authorities, save
   migration, uniqueness and reference validation, and the five
   one-shop aliases guarded through one `exactly_one_shop()`
   authority. P4a.2 is the address-local restaurant economy —
   inventory and storage, `shop.py`, upgrades, staff assignment,
   per-shop cook skill, rent, laundering ceilings, `net_worth` and
   `total_stock_units`. P4a.3 is the address-local night — routes and
   service, route-origin history, multi-wagon assignment, addressed
   haul placement, typed raid warnings, rival actions, incoming
   raids, coupons, damage, heat and law searches. Each is based on
   the previously MERGED one and is verified before the next begins:
   failures stay attributable to a boundary, and reviews stay
   tractable.
2. **`net_worth` becomes the address-agnostic asset authority, and
   stays generic.** It sums every shop's stash plus the warehouse
   stock **exactly once** — the double-count is the thing to watch —
   with cash, warehouse cash, debt and the fixed-asset exclusions
   unchanged. It is NOT made branch-aware, and its inventory
   arithmetic is not duplicated anywhere: P4b's Partner grading view
   computes `combined_net = state.net_worth() - current_arrears` and
   owns nothing else about money. `total_stock_units()` carries the
   identical home-shop blind spot today and migrates in the same
   pass, so the two cannot drift apart.
3. **P4a is narratively invisible.** No new prompts, no new labels,
   no raw identity key ever reaching the player, and no branch
   behavior. The identity gates enforce this mechanically for
   flag-off and stand-pat; the rule extends to every branch surface
   as well, because a player-visible change smuggled into a refactor
   is a change nobody reviewed as a design decision.
4. **Targeting: P4a supplies the mechanism, P4b the policy.** The
   "softer of your two shops" rule (§2.4.2) is P4b's. P4a builds only
   the explicit targeting, its validation and its persistence, and
   with one shop the resolver returns that sole address — which is
   precisely why it can be behavior-neutral now and load-bearing
   later.
5. **The home shop keeps the legacy world channel.** Derived daily
   rolls for the home address stay on exactly the channel they use
   today; changing that channel would move the world and break
   identity by construction. Additional addresses may draw from
   channels derived from their stable key (rev. 22 item 6's rule that
   no roll depends on list order) — but those channels do not exist
   until a second address does.
6. **The compatibility aliases fail closed at BOTH ends.** The five
   `shops[0]` accessors must refuse zero shops as well as more than
   one — a state with no address is as malformed as a state with two
   the caller did not expect — and both refusals route through one
   `exactly_one_shop()` authority rather than five spellings. By the
   end of P4a.3 no production module consumes them; they are retained
   only where the legacy-equivalence projection genuinely requires
   them, which is the one place a "the shop" concept is still
   correct.
7. **No implicit home defaults in addressed operations.** Once an
   operation names an address, wagon, origin, destination or warning
   reference, an unknown or missing reference **fails closed** rather
   than falling back to the home shop. A silent default is how the
   pre-P3.5 haul placement put every stolen crate in DiNapoli's
   regardless of where the crew drove.
8. **The gate binds at every PR boundary.** Full tests, ruff and
   mypy, both identity gates 300/300 on 3.11, 3.12 AND 3.13, and all
   three merged batteries byte-identical at 150 AND 500 seeds — at
   each of the three merges, not once at the end. A moved
   transcript, RNG state, ending or study digit is a refactor defect
   to be fixed, never a result to be recorded. **No golden
   regeneration is permitted anywhere in P4a**: the baseline is the
   instrument here, and an instrument that moves with the thing it
   measures has stopped measuring.
9. **Held for P4b.** Manager vacancy, the construction window, the
   points ledger, site selection, the second shop itself, the
   targeting policy and the Partner story are all P4b, and none of
   them appears in P4a in any form.

**Revision 28** records the P4b scope: the subdivision into sequential
PRs, the work list assembled from the canon already ruled (§2.4.2,
§2.5, §2.7, §3.2, §5 item 8, §6), and the judgment calls that need
rulings before mechanics harden. Paper only; no P4b implementation
accompanies it. It amends §7's P4b clause and nothing else — every
other paragraph below is a proposal awaiting a ruling, not adopted
contract.

1. **P4b is five sequential PRs, never stacked**, on P4a's precedent
   (rev. 27 item 1): each based on the previously MERGED one and
   verified before the next begins, so a failure stays attributable
   to one boundary. *P4b.1 — the deal and the address:* site
   selection, the atomic capital transaction, the second address and
   its wagon created together, the three declared phases and the
   recorded opening day. *P4b.2 — the points ledger:* two books,
   the cycle and its vig, the early-payoff deferral, and the
   second-strike foreclosure that ends the run that night.
   *P4b.3 — the manager, the vacancy and the two-front pressure:*
   appointment, the vacancy as a valid state and its penalties, the
   address-targeting POLICY that P4a left unruled, the neighbour's
   response to expansion, and tribute naming an address. *P4b.4 —
   the grade and the endings:* the one Partner grading view, the
   tiers, the status card that shows its work, the two remaining
   terminal ids and their texts, and the §2.5 matrix rows.
   *P4b.5 — bots, battery and study:* the Partner bot, both
   ablations, the §2.7 letters measured, FINDINGS, and human play on
   seeds 24/39/8. **Activation — adding `partner` to
   `RELEASED_BRANCHES` — is a SIXTH act, separate and explicit**, on
   the Harbor War's precedent: it is the only change that moves what
   a player can take, and it happens on the reviewer's word alone,
   never as a side effect of the last implementation PR.

2. **The gate P4b inherits, and the one it does not.** P4a's gate was
   identity, because it touched the flag-off path. P4b touches no
   flag-off and no stand-pat surface, so **both identity gates stay
   binding at every PR boundary — 300/300 on 3.11, 3.12 AND 3.13,
   stand-pat holding its 79 sit-downs** — but they are now a
   *containment* check rather than the phase's proof: they say P4b
   stayed inside its branch, and they say nothing whatever about
   whether the branch works. The three merged batteries must also
   stay byte-identical at both depths for the same reason. What
   proves P4b is the §2.7 Partner battery, and it does not exist
   until P4b.5. **The golden is not regenerated in P4b either**; a
   moved digit is a containment failure, not a result.

3. **The chair is visible and untakeable throughout.** `sitdown.py`
   already prints an unreleased chair with a development-build
   marker and refuses to seat it (§2.1's rule that an implementation
   limitation must never become a permanent player decision), so
   every P4b PR before activation leaves the sit-down transcript and
   its 79-count exactly where they are. This is asserted, not
   assumed: the stand-pat gate is the assertion.

4. **JUDGMENT CALL — the points schema cannot carry two books
   today.** §2.4.2 (rev. 22 item 7) requires *arrears* (dollars owed
   right now) and a *strike* (a miss that happened and never
   unhappens) as separate facts, and day-30 grading reads arrears
   while foreclosure counts strikes. The live `BranchState` carries
   `points_missed` and `vig_owed`, and `points_missed` is exactly the
   one counter the ruling says cannot carry both. *Proposal:*
   `points_arrears` (dollars currently owed) and `points_strikes`
   (misses ever), with `vig_owed` retired into arrears — the next
   bill is prior arrears + $2,500 + $500 vig, so the vig is a term of
   the bill, not a second balance to reconcile against. No released
   save can carry a partner `BranchState`, so this is a schema
   correction rather than a migration; `_BRANCH_FIELDS["partner"]`
   moves with it. **Needs a ruling before P4b.2.**

5. **JUDGMENT CALL — "the softer of your two shops" needs an
   executable definition.** §2.4.2 promises rivals may target it and
   rev. 27 item 4 deliberately left the POLICY to P4b, with
   `raid_target` failing closed on two addresses in the meantime. The
   definition must be deterministic and must not reduce to list
   position, which is the defect stable keys exist to abolish.
   *Candidates:* lower reputation (the address the neighbourhood
   would miss least); fewer staff assigned (the thinnest defence
   allocation, which is what §2.4.2 calls the decision); lower
   district heat (the easiest approach); or a stated composite.
   *Proposal:* fewest assigned available staff, because §2.4.2 names
   defence allocation as the player's lever and a policy that ignores
   the lever makes the lever decorative — ties broken by lower
   reputation, then by stable key so the answer is total. **Needs a
   ruling before P4b.3.**

6. **JUDGMENT CALL — the wagon exists before the shop opens.** The
   $2,500 used wagon is inside the $13,000 committed atomically at
   acceptance, and P4a's `validate_addresses` refuses an address that
   keeps no wagon — so the second wagon must exist from acceptance,
   during construction, at an address that serves nothing. *Proposal:*
   it exists and is idle: a wagon kept at an unopened address is
   visible in the fleet and may not be claimed for any job, because
   the address it belongs to is not operating. The alternative —
   letting it run routes out of a building site — would make the
   construction window free capacity and contradict §3.2's D16, where
   the second route becomes possible only once the shop opens.
   **Needs a ruling before P4b.1.**

7. **JUDGMENT CALL — the opening day.** §2.4.2 requires a recorded
   opening day fixed deterministically by Carmine's contractor, with
   nothing the player does able to move it. §3.2 walks D14 accept →
   D16 open. *Proposal:* opening day = acceptance day + 2, stored on
   the address rather than derived, so a save cannot recompute a
   different one; a §6.3-class placeholder that the P4b.5 study may
   move. **Needs a ruling before P4b.1.**

8. **JUDGMENT CALL — the vacancy penalties are unnumbered.** §2.4.2
   (rev. 22 item 6) fixes the SHAPE — vacancy is a valid state,
   recorded with the day it emptied; the address stays open under
   Carmine's nephew at reduced kitchen capacity and a reduced
   believable ceiling; a stated window before the penalty bites at
   full weight; appointing clears it — and fixes no magnitudes.
   *Proposal:* adopt as §6.3-class placeholders, stated in one
   authority and moved only by the recorded falsification workflow,
   with P4b.5's first study reporting the distributions. The window
   length, the capacity reduction and the ceiling reduction are three
   separate numbers and should be named as three, not one. **Needs a
   ruling before P4b.3.**

9. **The surfaces that fail closed the moment shop 2 exists — and
   why that is the design working.** P4a routed every single-address
   surface through `operating_shop`, which refuses when there are
   two. The morning, service and night blocks, the Straight Path and
   the Quiet Sale therefore stop resolving an address the instant
   the Partner branch creates one, BY CONSTRUCTION. P4b.1 must
   convert those surfaces to address-choosing ones in the same PR
   that makes a second address possible — that is the whole point of
   having built the refusal — and the Straight Path, the Quiet Sale
   and the Harbor War must continue to resolve their single address
   through the same boundary, unchanged, because none of them can
   ever have two. This is the largest single piece of P4b.1 and is
   named here so it is scoped rather than discovered.

10. **Held open, and NOT tuned inside P4b.** The §6.3 heat-weight
    question and the human-play findings carried since round 10 stay
    open and untouched; rev. 27's rule that P4a neither answers nor
    tunes them extends to P4b's implementation PRs. P4b.5's study
    may REPORT distributions that bear on them — the two grading
    thresholds (combined net strictly greater than $8,000, shop 2
    reputation ≥ 35) explicitly must — but a constant moves only
    through the recorded falsification workflow, never because a
    battery looked better afterwards. §6.4's ruling stands: war
    capture does not reuse the multi-shop machinery in v1.
