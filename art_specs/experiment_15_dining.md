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
