# Experiment 15 — Dining Furniture: Tables and Booths (2026-08-10/11)

Status: **LOOP CONVERGED after six rounds (22 generations + recorded
curations); candidates AWAIT the board. The user named these critical
theme pieces and directed the reflect/refine/re-render loop.**

## How it started: the pizza that was a table

The first table (round-cloth, free-prompted) PASSED the prop contract
in isolation and FAILED in the scene: its irregular red-on-cream
checks read as pepperoni — a giant pizza on a stand, in a pizza game.
Approval was rescinded by the board on in-scene review. Two laws came
out of the failure and governed the loop:

1. **In-scene reading is part of furniture acceptance.** Every round
   ends with a composite mock on real floor beside real figures.
2. **Regular patterns belong to code.** A checked cloth is a grid;
   grids are what generation does worst and anchors do best.

## The loop (each round: written reflection → refine → re-render)

- **Round 1 (4 gens):** code-built check-grid anchor at init@140 —
  the grid SURVIVED (pizza read dead); booth's unoutlined flat-band
  anchor dissolved. Lesson: **outline holds silhouette** (the table's
  rimmed anchor held; the booth's rimless one didn't).
- **Round B (4 gens):** two-plane perspective encoded in anchors.
  Table structure arrived (top + skirt), one seed invented a scalloped
  white hem worth stealing; booth tufting dots amplified into mottle
  (@150) and cabinet panels (@160). Session error owned: the palette
  strip was omitted this round; drift everywhere.
- **Round C (4 gens):** tufting abandoned for period-correct
  **channel-back** (resolution honesty: a 56×14 back cannot hold
  button tufting); fully-connected outline. Booth s15133 PASSED
  structurally (mottle residual); tables overdarkened — shading cloth
  with dark checks makes maroon furniture, not depth.
- **Round D (4 gens):** table brightened but the wood chip in the
  strip got SPENT ACROSS THE CLOTH — orange checks, the
  strip-spending law's fourth confirmation. Booth refine@70
  reinvented the object (garden bench, wooden hall bench): the @70
  knob requires the prompt to carry identity, and "booth bench"
  summons benches. Lesson: **@70 refines within an identity the
  prompt can name; it cannot defend one.**
- **Round E (2 gens + curation):** table split into GENERATED CLOTH
  (wood starved from the strip) + **CODE LEGS** (shoe-swap
  precedent) — s15151 landed: regular checks, pale-chip shading,
  fringe hem. Booth: back to s15133 + recorded isolated-pixel
  curation (21px).
- **Round F (0 gens):** in-scene mock exposed two misses: seat marks
  were OX-on-DARK (opposite polarity from the pass that hunted
  DARK-on-OX — curation must name its polarity), and the booth bay's
  lower bench needs its BACK to the camera. Fixes: polarity-corrected
  component cleanup (10px) and **booth_bench_rear** derived from the
  final bench's own rows (recorded recipe). The corrected mock reads
  as a true booth bay: customer seated between vinyl back and
  checked cloth.

## Candidates at the board

- `table_sq_s15151.png` (48×48): generated cloth + code legs.
  (s15152 alternate, smudged.)
- `booth_bench_final.png` (64×40): channel-back vinyl, south-facing.
- `booth_bench_rear.png` (64×24): derived rear view for north-facing
  bay placement.
- Composition guidance measured in the loop: the booth BAY
  (bench-table-bench, rear view on the camera side) is the unit
  scenes should stage.

## Standing lessons added to the recipe book

Outline holds silhouette; regular patterns to code; resolution
honesty for texture detail (channels, not buttons); @70 refines only
what the prompt can name; curation passes must name their polarity;
rear views of symmetric furniture are derivations, not generations.

## Proportion loop (2026-08-11, user board: "tables look amazing" + two
## corrections; 2 generations + recorded recipes)

The board approved the read and caught two facts, both confirmed by
tape measure before refining:

1. **The table was 146% of figure height** (figure 28px, table 41).
   Decomposed: the cloth alone is 89% — correct for pseudo-top-down
   (front face + foreshortened top) — but 16 rows of leg hung below a
   skirt that already drapes to ankle height, double-counting the
   table's height. Fix was pure recipe: ankle-gap legs (7px), total
   32px = **114% of figure** — what a table with a visible top should
   occupy. Zero generations; the legs were always code.
2. **The booth table was 38px wide against a 60px bench.** The bay
   variant is its own asset: wide legless cloth (booth tables hide
   their legs between benches), generated on the proven cloth recipe
   at 64×26 — s15162 picked (straight scalloped hem), its two
   invented caster-dots removed by recorded curation (8px);
   s15161's shaggy fringe recorded as the alternate. The corner
   drape-points that remain are cloth behaving like cloth; kept.

Final candidates: `table_sq_v2_s15151` (48×40, 114% proportion),
`booth_table_final` (64×26), `booth_bench_final` (64×40),
`booth_bench_rear` (64×24). The final mock seats two customers in a
bay whose table now spans the bench — the composition unit the
scenes will stage. AWAITING the board.

Lesson added: proportion claims are MEASURED against the figure
(percent of figure height, decomposed into planes) before any
refinement is attempted — the number found the defect (legs) that
the impression ("too tall") could not localize.

## Booth-table height (2026-08-11, user board question; 0 gens)

"Should the booth table be slightly taller? We can see the
characters' knees." Measured answer: the SPRITE was never short — the
STAGING was low. A three-way test (table at bench-offset +32 / +26 /
+22) showed +32 exposes the knee band, +22 buries torsos and crowds
arms, and **+26 covers the lap exactly as a booth reads from this
camera**. The fix is a recorded composition parameter — the bay unit
now ships as data (`booth_bay_staging.json`: front bench +0, seated
row +6, table +26, rear bench +60), zero generations. Lesson
reinforced from the peel probe's canvas question: apparent asset
defects can be staging defects; test the free parameter first.

## The other side of the booth (2026-08-11, user board question; 2 gens
## spent learning, 0 gens on the answer)

"From the perspective we are trying to achieve, does this make
sense visually?" It did not, and the reflection says why: in low
top-down every object shows the camera its SOUTH face, and the south
bench's south face is the OUTSIDE of its backrest — plain shell, not
the sitting-side channel upholstery my derivation had reused. The
rear bench was wearing the wrong face.

Two generation attempts at a "booth back seen from behind" collapsed
(the prior has nothing there — near-empty render, then a skeletal
frame). The flat-panel law answered instead: the rear shell is CODE +
DERIVATION — oxblood top rim (the backrest's top surface), a wood
panel slice derived from the APPROVED COUNTER's own cabinetry
(unifying the dining room's woodwork for free), dark base, outline.
Six maroon specks inherited from the counter were removed by a
measured despeck — the census said 6, the corrected threshold removed
exactly 6; the first pass had hunted r>130 and found nothing, so the
polarity lesson gains a clause: name the RANGE, not just the side.

Head-peek staging ships in the bay data: a far-side customer drawn
before the rear bench shows a hair-top above the vinyl rim — the
detail that sells someone sitting there. `booth_bench_rear_final`
supersedes the v1 derivation; bay staging updated (rear at +52).

## The gap ruling (2026-08-11, user board; 0 gens)

"Should the table extend further south to close that gap?" The
perspective answers what the gap IS first: the band between table hem
and backrest rim is the far bench's hidden seat — floor may never
show there. The free-parameter law then closed it without touching
the sprite: a 3-way offset test (+52/+49/+47) showed +49 seals hem
to rim with the scallops intact and turns the far-side customer into
an eyes-over-the-table peek; +52 leaked floor; +47 buried the hem.
`booth_bay_staging.json` updated. The dining set's sprites are
unchanged — three consecutive board questions (proportion, far side,
gap) have now been answered for a total of 2 generations, everything
else measurement, code, derivation, and staging data.

## Promotion and the chair question (2026-08-11, user board)

"Promote this!" — the five-piece dining set entered `approved/`
(table_sq_48, booth_table_64, booth_bench_64, booth_bench_rear_64
with the donor flag via its counter-derived shell, booth_bay_staging).

"Let's work to make chairs that work" — reflection before pixels:
the E02 pair measures 157% of figure height (the table's proportion
crime, pre-committed) and reads parlor, not shop floor. They keep
their approval as PARLOR-CLASS props (a candidate for Carmine's
corner scene) and leave the dining rotation.

## Chairs round 1 (2 gens): the four-top

Design computed before generation: wood café frame + oxblood vinyl
pad (booth vinyl + counter wood = one dining language), target
content ~20-22px on a 32 canvas. Outlined code anchor (rails, pad
planes, legs), init@150, subtractive strip. Both seeds PASS; s15201
picked (82% of figure — landed the computed band); s15202's mid-rail
smeared.

Economy measured in the mock: a rail-back chair is front-back
symmetric with the pad visible through open rails, so ONE sprite
serves north and south facings — the four-top mock (table ringed by
four chairs, one sprite) reads instantly as the pizzeria dining
room. Honest note for the board: the east/west chairs use the same
frontal sprite (RPG convention); strict perspective wants profile
variants eventually — flagged as optional refinement, not a blocker.

## Chairs round 2 — the faced set (2026-08-11, user ruling; 4 gens)

The board rejected the symmetric-sprite economy: "the chairs are not
faced correctly. Side facing and south sides are critical." Ruled and
built: a four-facing chair set — N position = front view (s15201),
S position = back view (s15212 picked: straight verticals, pad
sliver through the rails; s15211's legs splayed), E/W = one profile
generated (s15221, cleanest silhouette) with its all-dark pad
CURATED to ox (44px, cross-facing pad consistency) and its mirror
DERIVED for the opposite wing (no marks; mirror legal). The faced
four-top mock seats the table correctly on all sides — every
backrest points away from the cloth.

Candidates: chair_south_s15201 (front view), chair_north_s15212
(back view), chair_west_final, chair_east_final. AWAITING the
board's chair ruling.
