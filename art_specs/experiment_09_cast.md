# Experiment 09 — The Cast: Memorable at Thirty-Two Pixels (2026-08-10)

Status: **design paper first; generation follows on the same day
(user directive: "make them memorable"). Candidates AWAIT the board.**

## Sources (single authorities for who these people ARE)

`extra_toppings/data.py` EMPLOYEE_POOL (stats, traits, wages, bios),
RIVALS (Sal, Vinnie — style text), and `docs/ACT1_FORK_DESIGN.md`
(Carmine's scenes: the corner table, the fruit basket, the nephew;
staff moments: Bee rechecking the till, Tony watching the oven door,
Marcus cornered by the walk-in). The art invents NOTHING about
character; it translates recorded character into silhouette.

## The design language (how memorability works at 32px)

1. **Silhouette first.** At one tile, memory is outline: build,
   posture, headwear. No two cast members share a silhouette class.
2. **One accent, one story detail.** Each character gets at most one
   accent color and one prop/costume tell (≤4 px). More is noise —
   twice the resolution, not twice the visual noise.
3. **The warm↔cold axis is the loyalty axis.** The shop family wears
   the warm register (cream, dough-tan, oxblood). Pressure wears
   carbon ink and slate. Carmine — the debt made flesh — is the
   coldest figure in the game; institutional blues stay reserved for
   institutions, so even he gets ink/slate, not case blue. Marcus,
   the staffer who talks to detectives, carries ONE slate tell.
4. **Skin ramps.** Two ramps, both from already-legal colors:
   dough-tan (#D4A068/#C68239/#B1552E) and a deeper ramp
   (#C68239 base where mid, or #B1552E base/#680828 shadow) for a
   mixed-city cast — Old Harbor is a port town. FLAGGED for the
   color-language revision: a purpose-built pair of skin ramps is the
   right long-term home; the union rule licenses these interim picks.
5. **Menace without cliché** (theme guard): no guns, no fedora-and-
   tommy-gun mob costume. Vinnie's menace is bulk and stains; Sal's
   is politeness; Carmine's is tailoring. Angelo is dignity, not
   cartoon thug — he did four years and never said a name.

## The briefs

**Staff (warm register):**

- **Rosa Delgado** — driver, principled, twenty years zero accidents.
  Compact and square; hair in a practical bun (ink); slate work
  jacket over warm shirt; upright, feet planted. Accent: cream scarf.
  Read: the person you trust with the wagon.
- **Tony "Two-Slices" Marino** — cook, greedy, best dough hands.
  The WIDEST staff silhouette: round torso, thick forearms, white tee
  + apron, flour dust at the hem. Accent: 2 px gold chain — the greed
  tell, counting other people's money out loud. Read: dough and
  appetite.
- **Beatrice "Bee" Okafor** — counter, observant, ex-shipping-books.
  Slim, straight-backed, deeper skin ramp; round 2 px pale glasses
  glint — THE observant tell; cardigan in pale over cream; pencil
  line at the ear. Read: she has already noticed.
- **Marcus Webb** — driver, reckless, University dropout, low
  loyalty. Tall-thin slouch, hands-in-pockets block, messy hair; one
  SLATE jacket tell on a warm base (the cold streak that talks to
  detectives). Read: fast, unfinished, leaving.
- **Lena Kowalski** — counter, connected, a guy in every district.
  Mid build, heat-orange headscarf (the market-warmth accent, the
  only staffer carrying #FF8628), small hoop earrings; mid-gesture
  posture. Read: the rumor arriving.
- **Sammy Fetch** — driver, indebted, owes Carmine too, sweats.
  SMALLEST silhouette: hunched, cap pulled low (ink), oversized
  borrowed jacket (worn gray); muted everything. Read: trying not to
  be seen.
- **Angelo Ricci** — muscle, known to police, unshakeable nerve.
  Widest SHOULDERS (v-taper, not round like Tony), no-neck block,
  undershirt cream + suspender lines, rolled sleeves, knuckle-tape
  pixels at the fists. Accent: oxblood tape. Read: quiet, immovable.
- **Priya Nair** — cook, ambitious, two-star kitchen, "thinks this
  place is beneath her. It is." PRISTINE double-breasted chef coat —
  the brightest, flattest cream field in the cast (cleanliness as
  contempt); perfect vertical posture, chin up (head sits 1 px
  higher); oxblood neckerchief. Read: too good for this place, and
  correct.

**Antagonists & patron:**

- **Sal Moretti** — Moretti's Trattoria. The restaurateur's dignity:
  silver-gray hair (worn gray), dark waistcoat over cream shirt,
  towel folded over the forearm, slight welcoming lean. Accent:
  oxblood tie. Fights with prices and quiet words — the silhouette
  must read HOST, never heavy.
- **Vinnie "The Oven" Barzetti** — Vinnie's Pies. The HULK class:
  bigger than Angelo, head sunk into shoulders, stained apron (sauce
  stains in oxblood — the shop's own colors turned menacing), heat
  undershirt, burn-dark forearms. The pizza is a crime in itself.
- **Carmine** — the lender. LONG-COAT class, the only one: thin
  vertical figure, carbon-ink coat to the shins, pale gloves, silver
  temple; single 1 px gold tiepin — the only gold he needs. The
  espresso, the fruit basket, the nephew: pressure with manners.
  Coldest palette in the cast, deliberately colder than the rivals.

**Existing "DiNapoli Employee v1"** (E08) is hereby RECAST as the
generic extra/new-hire template, not a named character — the named
cast replaces it on screen wherever the roster is shown.

## Method

Per-character hand-blocked anchors (the silhouette IS the anchor —
build/posture/headwear blocked by hand per brief), per-character
palette strips (chips ∪ ramps ∪ single accent), pixflux init@120,
2-seed pools, character validator ((8,18) floor; Tony/Angelo/Vinnie
widen, Sammy may sit near the floor — measured, not assumed), boards
in role groups. Rotations/walks for approved picks reuse the proven
E08 v3 path (1 gen create + 4 gen walk each) in a later phase, after
the board rules on identity.

Budget this phase: 11 characters × 2 seeds = 22 generations.
Question: does the anchor-silhouette method produce distinct,
memorable, on-bio identities across a full cast? Theme role: the
whole warm↔cold axis, person by person.

## Results (same day, 22 generations, 22/22 PASS the character contract)

The anchor-silhouette method holds across a full cast: the lineup
(`review/cast_lineup.png`) shows eleven distinguishable people on the
shop floor at native scale — no shared silhouette class, and Carmine
reads as the single cold black column at the end of the row, exactly
what the design law ordered.

Provisional picks (user's board rules; per-character honesty notes):

| Character | Pick | Note |
| --- | --- | --- |
| Rosa | s9001 | s9002 REJECTED: grew a red beard — different person |
| Tony | s9011 | round + rosy; s9012 viable darker alt |
| Bee | s9022 | posture excellent; the glasses glint DID NOT survive in either seed — the 2 px tell is a candidate for recorded manual curation |
| Marcus | s9031 | messy + unfinished; s9032 too burglar-shady |
| Lena | s9042 | the heat headscarf became bright red HAIR in both seeds — accepted as the better tell (only redhead in the cast; the scarf was the art's invention, not the bio's) |
| Sammy | s9052 | cap-low hunch landed; s9051 lost the cap |
| Angelo | s9062 | stubble + wrapped hands, "four years upstate" read; s9061 too heroic |
| Priya | s9072 | deeper tone per brief, buttons crisp, vertical |
| Sal | s9081 | the lean welcoming bow; s9082 rounder padrone alt |
| Vinnie | s9092 | s9091 grew sunglasses — off-theme accessory |
| Carmine | s9101 | strikingly cold, coat rendered near-black; s9102 drifted priestly. The near-black raises a palette-semantics question for the board: outline-black as garment field is otherwise unused — keeping it makes Carmine literally the darkest thing in the game, which may be exactly right |

Recorded drift pattern worth keeping: 4-px-class accent tells (chain,
glint, tiepin) survive inconsistently at init@120; silhouette and
palette register survive reliably. Consequence for future briefs:
memorability must live in silhouette first (it does), and micro-tells
that matter can be restored by recorded deterministic curation after
the board picks — same policy family as the brand layer.

Spend: 22 generations, all provenanced. AWAITING the user's board:
confirm/override the eleven picks, rule on Bee's glasses curation and
Carmine's black, then approved picks proceed to the E08 v3
rotation+walk path (5 gens per character).

## Round 2 — breaking the JRPG prior (user board finding, same day)

The board found the round-1 cast reads homogeneously anime/Asian.
Cause analysis, owned in order of leverage: (1) the round-1 anchors
blocked BODIES carefully and FACES lazily — near-identical head
rectangles under a uniform ink-navy hair strip, so at init@120 the
model's JRPG-convention prior (the dominant pixel-art corpus) filled
in every face the same way; (2) init@120 is the invention setting —
wrong side of the authority balance when fighting a prior; (3) the
prompt "pixel art game character sprite" actively summons that
corpus, and heritage words the GAME ITSELF wrote (Delgado, Marino,
Okafor, Kowalski, Nair, Ricci — a port-town roster) were absent.

Round-2 method, recorded before running: anchors take the face back —
per-character hair SHAPE and COLOR (balding Tony, Sal's receding
silver + silver mustache, Marcus sandy, Bee's black crop, auburn
bun for Rosa), facial hair and brow blocks, jaw width, and deliberate
skin-ramp assignment across all three legal ramps (D4A068 light /
C68239 olive-mid / B1552E deep, shadows one step down). Init raised
to 140 (fidelity band — anchor authority over prior). Prompts carry
the bios' heritage plainly; negatives add "anime, manga, chibi, big
eyes, glossy hair". One seed per character (11 gens) proves the
method before any pool deepening. At 32px the honest levers are hair
shape, facial hair, and skin ramp — eyes are two pixels and carry
almost nothing.

## Round 2 results (13 generations: 11 + 2 targeted re-rolls)

The prior broke. The v1-vs-v2 board shows it side by side: Tony is
now a balding, mustached Italian-American cook with his hands on his
hips; Sal has the receding silver hair and silver mustache of a
padrone; Angelo is an olive-skinned buzzcut bruiser; Bee reads as a
Nigerian woman, Priya as an Indian chef, Rosa as a Latina driver
with an auburn bun. Carmine's coat came back carbon-ink rather than
pure black — resolving the round-1 palette-semantics question in
favor of ink without a ruling needed. 13/13 PASS the character
contract.

Honest misses, corrected in-round: the first v2 seeds aged Sammy
into a gray beard and left Marcus's face murky (facial-hair drift is
the residual failure mode once the anime prior is suppressed). Two
targeted re-rolls with explicit clean-shaven/age words and
beard-negatives landed both (s9532, s9552). Residual: Sammy carries
a small stray oxblood patch at the ear — 2 px curation candidate;
Bee's glasses read as a lighter eye-band rather than crisp wire
rounds — curation candidate as before.

METHOD RULING CANDIDATE (for the board): face-bearing anchors +
init@140 + written-heritage prompts + anime-register negatives is
the CHARACTER RECIPE, superseding the round-1 body-only anchors at
init@120. v2 provisional picks in candidates/*_provisional_v2.png:
rosa 9501, tony 9511, bee 9521, marcus 9532, lena 9541, sammy 9552,
angelo 9561, priya 9571, sal 9581, vinnie 9591, carmine 9601.

## Round 3 — the reflect/refine/re-render loop (user directive, 10 gens)

The board found residual figures reading "ghostly," and widened the
brief: memorability is the WHOLE figure, not the face. Three loop
rounds ran, each opening with a written reflection on the actual
pixels (zoom boards + head-region pale-pixel census in the session
record):

**Round A** (4 gens — lena/marcus/sammy/carmine): diagnosis was the
strip-spending law: at 32px the model spends every strip color
somewhere, and light neutrals (pale/cream/gray) land on FACES unless
the costume claims them in a large anchor mass. Fix: subtract light
neutrals from strips where the costume doesn't need them, block faces
fully in skin ramp, ground each figure with a midtone garment.
Results: Carmine fixed (warm gaunt, silver sweep — the vampire read
died; he keeps his dignity), Sammy fixed, Marcus de-ghosted but
GENERIC, Lena traded ghost for gold hands — the strip law struck the
accent color instead.

**Round B** (4 gens — lena/marcus/bee/rosa, whole-figure round):
Marcus SOLVED (big messy hair, open asymmetric jacket over gray tee,
oxblood sneakers — the dropout finally reads). Bee's LEDGER survives
and reads under her arm — blocked props at prop scale DO transfer;
her wire glasses failed generation for the third time and are now
provably a curation-class detail. Lena's cream blouse re-fed her
face. Rosa's strap exploded into oxblood patches — the law
generalized: ANY strip color beyond the figure's dominant masses gets
spent visibly; small accents need their exact mass claimed and every
competing color subtracted.

**Round C** (2 gens): Lena's blouse switched to oxblood so cream left
her strip entirely — clean, warm, red-haired, memorable. Rosa's strip
lost oxblood; the strap/satchel came back at intended scale — the
kitted veteran driver. Her eye area reads as driving glasses
(optional 2 px curation, arguably in character).

**LOOP CONVERGED.** Final picks: rosa v5_s9505, tony v2_s9511,
bee v4_s9524, marcus v4_s9534, lena v5_s9545, sammy v3_s9553,
angelo v2_s9561, priya v2_s9571, sal v2_s9581, vinnie v2_s9591,
carmine v3_s9603 (candidates/*_final.png; lineup
review/cast_lineup_final.png). Standing curation list (deterministic,
post-approval): Bee wire glasses, Rosa eye lighten (optional), Sammy
ankles (optional).

**Recipe addendum (standing):** strips are SUBTRACTIVE instruments —
start from the figure's dominant masses and add nothing that isn't
claimed by an anchor mass of the intended size. Light neutrals near
faces and loose accent colors are the two measured failure modes;
props survive when blocked at their real scale.

## Approval (2026-08-10, user board): ALL ELEVEN APPROVED

"Characters approved" — the eleven finals moved to `approved/` with
approval records pointing at their generation provenance. The
curation list (Bee's wire glasses, Rosa's eye-lighten, Sammy's
ankles) was NOT ruled on and stays open — approved sprites are
approved AS-IS; any curation would be a recorded revision needing
its own word. Rotation+walk phase (v3 reference + v3 walk,
keep_first_frame) launched for all eleven on approval, per the
committed path. Operational finding: Tier 1 allows 8 concurrent
background jobs; batch submissions must throttle.

## The extras program (2026-08-10, user ruling: approved, with separation)

The user approved extras-as-recolors with one binding constraint: NO
overlap with the core cast — extras never reuse a named character's
body. Dedicated extra BASES are generated for the purpose.

Design law, inverted from the cast's: extras are engineered for
LEGIBLE ANONYMITY — common silhouette classes, mid-value garments, no
accent color, no story tell. And for RECOLORABILITY: each base is
designed ZONE-UNIQUE — hair, top, and bottom each use a color that
appears nowhere else on that sprite, so recorded global color swaps
are safe without masks. Zone-uniqueness is verified per candidate and
is a pick criterion at the board (generation may violate it; the pick
must not).

Base roster (one tile each, E09 character recipe — face-bearing
anchors, init@140, ghost/anime negatives): adult man (average build),
adult woman (average build), elder (stooped, silver), kid (short,
~20 px figure — bbox floor still honored). 2 seeds each = 8
generations. Extras variants are then recorded recolor mappings in
provenance (`recolor.py`, codified with tests); the classic
crowd-sprite technique, kept inside palette law (ramps shift, never
collapse).

## Motion production results (2026-08-10)

All eleven approved characters have 8-direction rotations and
4-direction v3 walk cycles (keep_first_frame): 88/88 rotation frames
pass the character contract after per-character curation quantize
(max 42 px changed; each character curated against ITS OWN approved
palette), 234/240 walk frames pass. The six failures are flagged for
the board, not hidden: five are mid-stride limb separations of
5–13 px (single_silhouette is a PROP rule — whether it applies to
animation frames is an open contract question, the decal story
again) and three 1-px specks on Sammy's north walk are genuine
garbage, queued for recorded curation. Tony's first walk group
silently never rendered (the vendor job-flakiness pattern again —
resubmitted, 20/20 clean). OPERATIONAL GAP recorded: MCP-side
generations do NOT flow through the REST spend ledger; the vendor
balance is the only authority for them. Local curated PNGs are
canon; character ids remain derived caches.

## Idle pass (2026-08-10 session 2: 11 generations, 11/11 PASS)

Breathing idle, south, for all eleven — v3 `animate_character`,
frame_count 4, keep_first_frame, one job per character with phrasing
VARIED per character (the dedupe law; each phrase is also a small
character note: Sammy breathes "shallow and nervous", Carmine "only
the faintest calm breath"). Submitted in a 10-job wave + 1 (tier
cap), curated by the standing per-character palette quantize (raw
preserved in `idle_raw/`), validated under the ratified contract:
**11/11 cycles pass, 55/55 frames pass, 11/11 frame-0 identity
anchors hold against the curated rotations.** Quantize stayed in the
walk-phase band (max 48 px, rosa frame 1). Curated frames live in
`curated/<name>/idle_south_frame_00N.png` — canon, same as walks.

Operational note for the record: Backblaze frame URLs reject
urllib's default User-Agent (403) — a browser UA string is required;
the first download attempt of this pass failed on exactly that and
cost zero re-generations.

## Tony peel probe (2026-08-10 session 2: 1 generation, answered by failing)

The user's canvas question ("does the peel need 64×32?") was probed
with one v3 action on the existing Tony character ("sliding a pizza
into an oven with a long wooden peel", north, 4f). Measured: no frame
touches the 56×56 canvas edge (max bbox 40×28) — but the fit evidence
is WEAK because **the prop never rendered**. v3 produced billowing
white dough/smoke masses in Tony's hands that fragment into floating
pieces by frames 3–4; no peel, no pizza, and the later frames would
REFUSE under the ratified animation contract (multiple disconnected
components). Frames preserved in `peel_probe/`, deliberately
uncurated — this is a measurement record, not a candidate.

RULING IMPLIED, for the board to confirm: in-model prop-in-hand
animation is outside v3's competence at this scale. Hand-off moments
stage the CANON pizza asset on tiles; if a scene needs the peel it is
its own prop generation (E01-class, validated as a prop); character
animation stays body-motion-only. The 64×64 escalation question is
moot until a real peel prop exists to measure.

## Peel probe, reflected (2026-08-10 session 2): the conclusion was confounded

CORRECTION, owned plainly: the probe's conclusion overstated what was
measured. The v3 schema documents its own contract — action
descriptions should focus "on the movement or pose only … **avoid
environmental details like locations or objects**" — and the probe
prompt named three objects (pizza, oven, peel). The dough-smoke is
what the vendor said misuse would produce. One generation measured
PROMPT MISUSE, not competence; "prop-in-hand is outside v3's
competence" is retracted as unproven either way.

Second fact, from the full schema: **v3 accepts custom keyframes** —
`custom_start_frame` (overrides the starting pose, ≤256×256, single
direction) and `end_frame` (interpolation toward a target pose). A
prop-in-hand animation can therefore be ANCHORED FROM APPROVED PIXELS
instead of conjured from words. This also closes the user's original
canvas question properly: the start frame may be any size up to 256²,
so the needed canvas is measured deterministically at composite time,
free, before any generation.

### Path determination (presented for the ruling)

**Tier 1 — engine staging (recommended default, serves the game
now).** The peel becomes its own E01-class prop (side/three-quarter
views, ~2–3 gens + board). Pizza-on-peel is the CANON pizza
composited at a recorded offset — no second pizza is ever generated;
single authority holds. Scenes stage and tween the peel exactly as
the game already composites its own chairs (the standing precedent
from the seated-extras pick criterion). The design doc's actual
demand ("Tony watching the oven door") is a scene beat this covers
with zero new surface risk.

**Tier 2 — keyframe probe (optional, AFTER Tier 1's prop is
approved).** Composite the approved peel(+canon pizza) into Tony's
hands on his rot_north frame at recorded offsets — every pixel from
approved assets, curation-class provenance. Feed it as
`custom_start_frame` with a CONTRACT-COMPLIANT movement-only
description ("leaning forward, sliding both arms ahead"), 1 gen,
north only. Measure: does an anchored prop survive generated frames?
CONTRACT FLAG for the board either way: for prop-carrying cycles the
frame-0 identity anchor must be the recorded COMPOSITE, not the bare
rotation — a ruled amendment to validate_walk_cycle's anchor choice,
decided before the probe runs, not after.

Tier 1 needs no new law. Tier 2 waits for Tier 1's prop approval and
the anchor-law ruling. Neither spends until the board says so.

## Animation contract ratified (2026-08-10, user ruling)

The user adopted the animation-frame contract verbatim: same
size/alpha/palette rules as props; garbage specks (<4 px) refused;
up to two extra components allowed if each is ≥4 px (a limb, not a
speck); and the cycle-level identity anchor — frame 0 must
byte-equal the character's rotation sprite. Implemented as
`validate_animation_frame` + `validate_walk_cycle` (4 tests; suite
85). Results under the ratified contract: Sammy's speck frames took
recorded curation (3+1 orphan pixels removed, provenanced); his west
cycle exceeded the component limit and was re-rolled ONCE rather
than bending a day-old rule (the vendor deduplicates identical
action descriptions — a distinct description forces a fresh render;
operational note recorded). FINAL: 44/44 walk cycles pass, and
44/44 frame-0 identity anchors hold BYTE-EXACT across the cast —
keep_first_frame is now a verified contract, not a vendor promise.
