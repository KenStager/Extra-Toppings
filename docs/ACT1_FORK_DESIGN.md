# The Act I fork — design for review

**Status: paper design only. No game code changes accompany this document.**
It goes to human review first; implementation is not authorized until the
critique cycle completes.

**The problem.** Paying Carmine ends the game's central pressure around day
12–15 (`docs/FINDINGS.md`: the market bot's median healthy payday is day 12),
and the back half of the month goes flat. The agreed direction is that debt
payoff should trigger a deliberate fork — *"Act I is over; choose what this
empire becomes"* — not an arbitrary second debt.

**Canon.** This fork is not new invention; it is the canon's own structure
arriving on schedule. The original pitch names the acts ("Act I: The hustle.
One shop, one car and a debt due in thirty days" → "Act II: The operation.
… the first additional branch. Rivals begin treating the player as a
territorial threat") and insists that "winning should mean securing an exit,
not simply filling a progress bar," listing the exits this fork offers:
build a legitimate franchise and abandon the trade; eliminate or absorb the
other syndicates; sell the entire operation and disappear
(`docs/canon/00-original-pitch.md`). The north-star brief's ten invariants
(`docs/canon/01-north-star-brief.md`) are treated as the acceptance bar
throughout; §2.8 maps the design against them, and §2.8 also lists the one
deviation this design would record in `docs/canon/README.md`.

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

- **Trigger:** deterministic, telegraphed one morning in advance (the fruit
  basket night), gated by calendar and Case (§2.1).
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

**Which chairs are at the table** (each gate is stated in-scene when it
fails — an empty chair is explained, never silent):

| Chair | Needs | Withheld when |
| --- | --- | --- |
| The Straight Path (clean exit) | `R ≥ 5` | too few days: "you can't launder a reputation in a weekend" |
| Carmine's Partner (second branch) | `R ≥ 10`, Case < 70 | calendar: "no time to build anything now"; Case: "nobody invests in a burning building" — he sends a nephew instead of coming |
| The Harbor War (territory) | `R ≥ 8` | calendar: "wars outlive months" |
| The Quiet Sale (escrow) | `R ≥ 5`, Case < 85 | Case ≥ 85: "any buyer's diligence would subpoena itself" |
| Stand pat | always | — |

**Edge cases the assignment names, answered concretely:**

- **Early payoff (day 7).** Sit-down day 8, `R = 23`. All chairs present.
  Carmine is impressed and says so; his offer improves at the margin (first
  points payment deferred one cycle, §2.4.2) — a reward for excellence, not
  a different game.
- **Late payoff (day 25).** Sit-down day 26, `R = 5`. Only the Straight
  Path, the Quiet Sale, and stand-pat are on the table, and the scene says
  why. This is honest: paying late means Act I consumed your month. Payoff
  on day 27+ (`R ≤ 4`): no sit-down at all — a single line of Carmine's
  respect, then the existing endgame. The current epilogue already grades
  that run.
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
| Straight Path | Leave the trade; by day 30 be a real restaurant nobody can touch | Income collapses to pizza margins while payroll still carries every witness | The network: routes, raids, and the supplier are gone for good; rivals stop fearing you |
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
- **paper** — financial: over-ceiling laundering (≤ 20/incident), the 0.5
  routine-discrepancy ticks (aggregated into one rolling "routine
  discrepancies" record), frozen-deposit reviews.
- **physical** — seizures and scenes: traffic-stop seizures, walk-through
  finds, the owner photographed by the wagon, bodies, gunfire, brawls.
- **pattern** — the raid handwriting premium, and only that.

**Counterplay verbs (Act II unlocks, all branches; load-bearing in the
Straight Path):**

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
at 25 points, and the Case never displays below 10 once it has ever exceeded
10. The climate cools; it does not un-happen.

### 2.4 The branches

Each branch below is specified as: goal · unlocks · pressure replacing the
debt · how each existing system carries forward (all eight: clean money,
dirty money, the Case, heat, rivals, raids, reputation/demand/pantry,
staff) · failure states and endings.

#### 2.4.1 The Straight Path (clean exit)

**Goal (checked at day 30):** contraband stock zero everywhere; dirty cash
≤ $200; Case ≤ 45 after remediation; reputation ≥ 45; no *hostile unsettled
witness* (a departed aware employee with morale < 5 and no settlement).

**Unlocks:** counsel and settlements (§2.3) as the core verbs; **Disposal**
replaces "Plan tonight's route" in the morning menu; **Advertising** (clean
spend, $300 → demand/reputation lift over following days — canon's clean-money
list has waited for this) appears in Improvements.

**The disposal problem** — remaining stash must go, three ways, priced like
everything else in this game: (1) *fire-sale to Sal's people* — one meeting,
bulk, 40% of book value, +8 Sal relation, small witness-evidence risk if
observed; (2) *run it down yourself* — full price, full route risk, and the
wagon stays warm (the temptation option; each run is normal Act I rules);
(3) *burn it* — zero return, zero risk, and Tony watches you do it.

**Pressure replacing the debt:** income collapses to pizza margins while the
payroll still carries every read-in name — you dare not fire what you can't
afford to keep (firing an aware employee is +6 Case *witness* evidence,
already in the game; now it's the whole game). Rivals smell retreat:
Vinnie's coupon blitzes and poaching intensify against a shop that no longer
scares anyone (aggression multiplier while you hold no stash), and Sal —
politely — offers to buy your coded-customer book, the branch's standing
temptation. An active feud must be settled to exit: tribute, deterrence, or
one last pre-exit raid that restarts the pattern clock.

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

**Failure states / endings:** *"The Legitimate Exit (earned)"* — goal met;
the existing rarest-pie ending, upgraded text acknowledging what it cost.
*"Almost Out"* (new) — day 30 with stock and dirty zeroed but Case 46–99:
you're clean and they're still watching; bittersweet. *Clean insolvency*
(payroll unmet with no stock and no dirty ≥ 2 consecutive days) → the
existing "broke" oven-went-cold ending with branch flavor: the cover
business couldn't cover the cover-up. Case 100 remains arrest, any day.

#### 2.4.2 Carmine's Partner (the second branch)

**Goal (day 30):** both shops open, points current, Case < 100 — graded on
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

**Failure states / endings:** *"The Operation (two ovens)"* — goal met;
upgraded operation-holds text, explicit Act III hook. *"Foreclosure"* (new)
— two missed points payments: Carmine protects his investment; he takes the
second shop, the wagons, and the month's dignity — the kneecaps ending's
polite cousin, and the run ends. Arrest at Case 100 carries branch flavor:
he is embarrassed, and the epilogue implies what that means.

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
alertness/security word, your crew's health, and turf status per district.
Existing raid objectives become campaign moves with stated roles: sabotage
is tempo (their ovens down = their cover gone = their routes naked), stock
theft is attrition plus a market shortage, the ledger is the political
weapon (spending it to the law converts *your* leverage into *their*
prosecution — one big Case-free strike, consumable, already priced by PR
#3's "leverage used is leverage gone").

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

**Failure states / endings:** *"The Harbor Is Yours"* (new) — target broken;
graded by what's left of you. *"The Syndicate"* — both broken (existing
ending, earned properly). *"Burned Out"* (new failure) — a successful rival
raid landing while the shop is already damaged (`damage_days > 0`) destroys
it: the war came home. Telegraphed twice over — warnings exist and damage is
visible — so it is always a risk knowingly accepted (invariant 7).
*"Won the War, Lost the Verdict"* (new) — Case reaches 100 after the target
falls: they arrest you at the victory party. Distinct text because the
player earned both outcomes.

#### 2.4.4 The Quiet Sale (escrow week)

**Not a quit button — a hold-steady game.** The buyer (Sal's straw man if
Sal lives and relation ≥ 0; an out-of-town operator otherwise) opens with a
marked price and four days of diligence; closing is the fifth morning. The
run ends at closing — this branch is 5 days long by design.

**The mark:** illustrative formula — base $3,000 + reputation × $140 +
50% of upgrade spend; discounts: −$45 × Case, −20% if any rival is at
relation ≤ −50 or has a live raid warning. The mark is recomputed each
diligence morning and shown with its terms (invariant 8: the player sees
exactly what their month is worth and why).

**Diligence days:** each day is an incident check the player plays through
the normal loop. Laundering during escrow is off (the books are being
*read*); contraband on premises at any walk-through, a rival raid landing,
a staff walkout — each is an incident: reprice (−10 to −25%) or, twice,
collapse. The stash must therefore go — fire-sale, or quietly to the
warehouse, because **the buyer buys the restaurant, not the lease on the
rusted rolling door**: warehouse cash and anything in it walk away with
you, unlaundered and epilogue-flavored. Staff learn on day 2 and the
severance line-items are the humane-versus-cheap choice the epilogue
remembers. On the fifth morning: sign, or walk away — walking keeps the
shop, loses the buyer forever, and drops to stand-pat with a bruised crew.

**Systems carry-forward (compressed by design):** *Clean/dirty*: clean
accumulates into the settlement; dirty must be hidden or burned — the one
week the two ledgers *cannot* touch. *Case*: pure price (−$45/point) — no
time to lawyer it. *Heat*: raises walk-through odds, i.e. incident odds.
*Rivals*: a last extortion when word gets out; war discount live. *Raids*:
incoming only; an incident. *Reputation/demand*: the single biggest price
input — the branch retroactively rewards having run a real restaurant.
*Staff*: severance, and whether Rosa hears it from you or from the buyer's
walkthrough.

**Failure states / endings:** *"Sold"* (new), in three tiers by total
walk-away (settlement + clean + warehouse cash): ≥ $25k *sold well*;
$10–25k *a modest ending*, which is what this chair honestly is; < $10k
*the fire sale*. *Collapse* (two incidents) → stand-pat with reputation
−8 and the buyer gone. Case 100 during escrow → arrested, with the
cruelest timing in the game.

#### 2.4.5 Stand pat

Today's game, verbatim: same loop, same endings, same flat back half —
preserved deliberately as the control group (§2.7) and the guarantee of no
regression. The morning header notes what you turned down, once.

### 2.5 Endings inventory after the fork

Existing seven: arrested, kneecaps (unreachable post-payoff — debt is
zero), broke, survived × 4 grades — all retained; stand-pat reaches them
exactly as today. New: Almost Out; Foreclosure; The Harbor Is Yours; Burned
Out; Won the War, Lost the Verdict; Sold (×3 tiers, one ending with graded
text); upgraded texts (not new logic) for the earned Legitimate Exit, The
Operation (two ovens), and The Syndicate. Net: six new ending IDs, three
upgraded texts. `_check_endings` grows branch goal checks; the epilogue
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

1. **Act I is untouched.** Pre-fork metrics (payoff rate, Case at payoff,
   arrest rate) match current main within the 150-seed confidence band —
   the market bot's 61–62% payoff must reproduce. The fork triggers only
   after payoff, so any drift is a bug by definition.
2. **Reachability.** The unmodified market bot reaches an open sit-down in
   ≥ 55% of seeds; at typical payoff states every chair is present in
   ≥ 90% of open sit-downs (the gates of §2.1 should bite on outliers, not
   the median run).
3. **Crash-freedom.** Chaos-monkey (`--auto`) forced down each branch × 150
   seeds completes every run; full unittest/ruff/mypy suite green.
4. **Divergence.** Four branch bots (minimal per-branch policies over the
   existing smart bot). Measured over post-fork days only:
   - *Straight Path bot:* covert revenue share < 5% after fork+2; median
     Case slope ≤ 0 (the first negative Case slope in the game's history —
     the headline regression that §2.3 works).
   - *War bot:* ≥ 4 raids; median target strength at end ≤ 50% of its
     fork-day value; pattern+physical evidence ≥ 50% of post-fork Case
     growth.
   - *Partner bot:* combined legit revenue ≥ 1.5× the stand-pat control's
     by fork+8; points paid on schedule in ≥ 80% of runs.
   - *Escrow bot:* run ends ≤ fork+5 in ≥ 95% of runs; closing price
     correlates negatively with Case across seeds (ρ ≤ −0.4) — the
     price-wears-your-scars claim, tested.
   - *Pairwise:* each branch bot's post-fork action mix (fraction of days
     with a route / a raid / neither) differs from every other branch's by
     ≥ 0.25 in at least one component.
5. **Stakes are real (ablations).** Each branch bot's branch-good ending
   rate lands in a 25–70% band (no auto-win, no hopeless chair), and
   removing the branch's stated counterplay drops it by ≥ 20 points:
   a Straight Path bot that never settles witnesses or retains counsel; a
   War bot that raids on cooldown ignoring alertness; a Partner bot that
   pays points from pizza margins only; an Escrow bot that keeps stash on
   premises. If an ablation *doesn't* hurt, the pressure is decorative and
   the branch fails review.
6. **The control stands.** Stand-pat runs reproduce the current endings
   distribution within noise.

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
sit-down is telegraphed a night ahead, every gate is explained, war raids
keep the 2-night warning, Burned Out requires two visible prior states;
(8) explainable outcomes — the mark's terms, the chairs' gates, and the
evidence ledger are all shown; (9) legal/illegal tension — points must be
earned dirty, exits must be earned clean, neither side goes passive;
(10) dual-use — counsel enforces the ceiling it protects you from,
advertising grows the cover you may be dismantling, the second shop doubles
both laundering and exposure.

**One deviation to record in `docs/canon/README.md` if approved:** *Act II
compressed into the original thirty days.* Canon's acts read as open-ended;
this design keeps `DEBT_DUE_DAY = 30` as the campaign end for every branch
(§6.1 argues why, and what would change it later). The escrow branch also
ends runs early — a smaller note under the same entry.

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
  (routes, raids, the supplier van). The morning menu is visibly different:
  "Plan tonight's route" is now **Disposal**. First decision: 22 units
  across two stashes. You fire-sale the warehouse oregano to Sal's man (40%
  of book, +8 Sal relation) and keep the mushrooms for a decision you're
  not ready to make. Night: retain counsel ($150/day) — the over-ceiling
  flag is first in the queue.
- **D15.** NEWS: concert in the Meadows — hot honey prices climbing. The
  temptation offer lands in its own voice: a Meadows contact wants your
  mushrooms at 1.6× book. Refuse (free) or run it (full Act I route rules,
  and the exit stops being clean). Marcus corners you by the walk-in —
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
  witnesses content. Twelve days to make reputation 45 on margherita alone.

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
  success +3 Case). Ovens down 4 days: his cover is gone, his routes are
  naked. Heat Meadows 30 → 42. His answer telegraphs by morning:
  unfamiliar cars, twice.
- **D16.** The counter-raid warning counts down; the defense choice is the
  old screen with new stakes (war-scaled crew). You empty the stash into
  the wagon and let them find crumbs — damage days 2, and the war board
  logs it: *his move spent, shop limping.* Sal raises an "insurance" offer:
  $800/week to stay a merchant. Decline, and remember the Case has a
  second author now.
- **D17.** Tempo push: Rosa runs product into the Meadows while his cover
  is down — his corner customers take your number. Meadows heat 42 → 51:
  the war board colors the district amber — *take it hot and you take
  ash.* Angelo's knuckles heal; Marcus asks if this is forever.
- **D18.** Second job: the warehouse, security now *hardened* (alertness
  4.7 — your sabotage taught him). Quiet odds visibly worse (−0.19); the
  pattern premium warning reads +4. It goes loud in the cage; Angelo takes
  a bad one — out 3 days. Haul: 9 units, strength 58 → 46. Case 31 → 39,
  all of it pattern and physical — **nothing on that number ever comes
  off.** The war board's bottom line becomes the branch: *strength 46,
  Case 39, twelve days.*

### 3.4 The Quiet Sale, days 14–18

- **D14.** The broker's card, itemized: base $3,000 + rep 24 × $140 +
  upgrades $1,850 × 0.5 = $6,285; less Case 31 × $45 = −$1,395; less 20%
  (Vinnie at −45) = **mark: $3,912.** Terms: four diligence days, marked
  each morning, incidents reprice, two incidents end it, closing morning
  five. The number is an insult and a mirror. You sign the diligence
  letter anyway — or stand pat now and keep the sandbox.
- **D15.** Diligence day 1. The register must be boring: laundering is off
  all week. The stash *must* vanish — fire-sale the mushrooms to Sal's man
  and truck the oregano to the warehouse at dusk, because the buyer buys
  the restaurant, not the lease on the rolling door. Walk-through odds at
  heat 22 are the morning's arithmetic. Mark drifts +$130 on a clean day.
- **D16.** Word reaches Vinnie: a note under the door — $1,200 or "the
  buyer learns what he's buying." Pay quietly from dirty (unrecorded,
  price holds) or refuse and bank on the raid telegraph running past
  closing. You pay. Bee figures out what the man in the good suit was
  measuring; morale −1, and she asks what happens to *them*.
- **D17.** Staff day. Severance line-items on the closing sheet: $300 a
  name, or nothing and the epilogue remembers. The critic tours — one last
  gourmet service lifts rep 24 → 27; the mark reprices +$420. A squad car
  slows, doesn't stop. The walk-in holds flour and receipts.
- **D18.** Closing morning: final mark $4,610. Sign — settlement + clean
  $1,900 + warehouse cash $800 and the oregano out the back gate = a
  walk-away just under $8k: **the fire sale tier**, priced exactly by the
  Case and the feud you're leaving unpaid. Or tear it up: buyer gone
  forever, shop yours, twelve flat days of stand-pat left, and Rosa saw
  the suit too.

### 3.5 Why these are different games

| Branch | Core loop | Screens it alone has | The clock | A misplay looks like |
| --- | --- | --- | --- | --- |
| Straight Path | dispose / defend people / polish the shop | Disposal, counsel's queue, exit readout | Case & rep vs. day 30 | firing a witness to save wages |
| Carmine's Partner | staff two addresses / earn points dirty | site cards, shop-2 block, points card | every 5th night | paying points from pizza margins |
| Harbor War | tempo strikes / defend / pace alertness | war board, capture log | strength vs. Case | raiding on cooldown into *hardened* |
| Quiet Sale | hold steady / hide everything / price the exit | broker's mark, diligence sheet | 4 marked days | one walk-through with stash on site |

Same engine, four verbs sets, four clocks, four ways to lose. The
walkthroughs share exactly one screen: the sit-down.

---

## 4. Risk register

| # | Risk | Class | L | I | Mitigation |
| --- | --- | --- | --- | --- | --- |
| R1 | Content dilution: four thin branches instead of one deep game — the canon's own warning ("do not solve lack of depth by adding content") | design | M | H | Branches reuse existing systems ~90%; only Escrow adds a wholly new loop and it is 5 days long; phased delivery (§7) ships one branch at a time behind studies |
| R2 | Evidence remediation becomes a slider — the Case's money-doctrine twin broken | design | M | H | Typed kinds with physical/pattern immune; 25-point cap; floor of 10; regression: Act I replay produces identical Case totals |
| R3 | Hard fork reads as railroading / "pick your DLC" | design | M | M | State-dependent chairs, explained gates, stand-pat null branch, temptation offers keeping other lives visible |
| R4 | Branch balance unknowable on paper; a chair dominates or is hopeless | design | H | M | §2.7 bands (25–70%) + ablations are falsification bars before human tuning; bots stay instruments |
| R5 | Straight Path is boring (no routes, no raids) | design | M | H | Disposal pricing, temptation offers, witness economy, rival siege, advertising race — verified by the ablation: if skipping its verbs doesn't hurt, it *is* boring and fails review |
| R6 | Multi-shop refactor blast radius: demand/cover/laundering pipeline is `HOME_DISTRICT`-hardcoded and invariant-tested | tech | H | H | Ship Partner branch **last** (§7); parameterize `shop.py` by district behind the existing tests first; War-branch capture deliberately does *not* reuse multi-shop (§6.4) |
| R7 | Save v3 churn and determinism across branches | tech | M | M | Field-completeness guard already forces coverage; new persistent streams (`sitdown`, `brokers`, `war`) keep world channels untouched; no player-facing saves exist yet (`save.py` docstring), so no migration burden |
| R8 | Issue #4 (noise-timeout awards objectives) poisons the War branch economy | tech | H | H | Hard prerequisite: fix + regression through the actual raid path before War work starts (§7 P0) |
| R9 | Ending combinatorics: 6 new IDs × branch flavors bloat `epilogue` | tech | L | M | One dispatcher arm per branch; graded text inside one ending ID where possible (Sold tiers) |
| R10 | Bot fleet cost: 4 branch bots + ablations + control ≈ 10 conditions × 150 seeds per study round | tech | M | M | Branch bots are thin policies over the existing smart bot; post-fork days only; `fork` study runs branches independently |
| R11 | Late-payoff players never see Act II and call it missing content | product | M | L | The scene says why the chairs are empty; FINDINGS shows median payoff is day 12–15, so the median player forks |
| R12 | Escrow's 5-day runs skew aggregate stats (net worth, arrests) if pooled naively | tech | M | L | Report per-branch tables; never pool across branches in FINDINGS |

## 5. What the engine must change

Ordered roughly by blast radius, smallest first:

1. **`raids.py`** — fix issue #4 (the "Time's up" break must mark the job
   failed, not fall through to `_payoff`; plus the ties-to-even display nit
   on the pattern premium). Prerequisite for everything raid-adjacent.
2. **`models.py`** — `State.act`, `State.branch`, `State.branch_state`
   (typed per-branch dataclass, not a loose dict — save completeness must
   see its fields); `case_flags` → typed evidence records with magnitudes;
   `state.case` becomes derived (sum, clamped) with the Act I-identity
   regression of §2.3.
3. **`save.py`** — `SAVE_VERSION = 3`; evidence records, act/branch state,
   new RNG streams. No migration path needed yet (engine-layer only), but
   say so in the version bump commit.
4. **`rng.py`** — persistent streams `sitdown`, `brokers`, `war` (player-
   facing dice); world channels untouched so every Act I study reproduces.
5. **`game.py`** — `run()` loop: the sit-down hook after night when
   `debt == 0 and act == 1`; escrow's early termination (a run may now end
   before `last_day`); `_check_endings` branch goals; `broke` condition
   rework (its `debt > START_DEBT * 2` clause is unreachable post-payoff —
   clean insolvency needs its own test); `epilogue` branch arms.
6. **`phases.py`** — morning header shows the branch goal line instead of
   the Carmine line; branch verb injection (Disposal, counsel, settlements,
   advertising, war board, diligence sheet); night ticks (points due, war
   pay, escrow marks). The debt-interest guard already handles payoff.
7. **`rivals.py`** — war posture (vendetta lock, aggression multiplier,
   side-picking by disposition, insurance offers); capture-on-strength-0
   effects for the War branch (district underground transfer).
8. **`shop.py`** — the big one, deferred to the Partner branch phase:
   parameterize demand/ceiling/shift by (shop, district) instead of the
   module-level `HOME_DISTRICT`; `State.shop` grows a sibling. Every canon
   invariant test on the pipeline must pass parameterized before shop 2
   exists.
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
3. **Case remediation bounds** (25-point cap, floor 10, counsel −60% on
   paper, settlements −50% on witnesses). *Recommend: adopt as placeholders
   and let the §2.7 ablation studies move them.* The structure (typed,
   bounded, physical/pattern immune) is the decision; the constants are
   tuning.
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

- **P0** — issue #4 fix; typed evidence refactor with the Act I-identity
  regression; save v3. No player-visible change; every existing study
  reproduces. *Gate: FINDINGS round-5 baseline identical to round 4.*
- **P1** — sit-down + stand-pat + the Quiet Sale (the cheapest complete
  branch: proves trigger, chair gating, early termination, one new ending
  family). *Gate: criteria 1–3 + escrow rows of 4–5.*
- **P2** — the Straight Path (counsel, settlements, disposal, advertising).
  *Gate: the negative-Case-slope study and its ablation.*
- **P3** — the Harbor War (war posture, war board, capture-lite).
  *Gate: war rows of 4–5; raid-pricing decline curve re-verified at war
  cadence.*
- **P4** — Carmine's Partner (multi-shop refactor last, alone in its
  phase). *Gate: full §2.7 battery + human play on seeds 24/39/8, written
  up honestly in FINDINGS.*

Each phase ends with the standing workflow: tests + ruff + mypy, the
relevant studies rerun, FINDINGS updated (including retractions if the
paper design's claims don't survive contact), commit, push, review.
