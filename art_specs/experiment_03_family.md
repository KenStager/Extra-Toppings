# Experiment 03 — The Pizza Family (2026-08-10)

Status: **generated, curated, AWAITING USER APPROVAL.**

Question: does the pipeline extend an approved asset into a cohesive
family? Four objects — slice, closed box, open box, box stack — all
32×32, anchored to the approved canon (`pizza_whole_32_canon.png`),
under the Experiment 01 v0.2 12-color palette.

Method (all lessons applied): hand-blocked init anchors WITH ≥2px
transparent margins (the Experiment 01 clipping fix) at strength 150;
two arms per object — bitforge with canon as `style_image` (32×32
style = 32×32 output) vs pixflux with palette+prompt only; validator
v2 at 32px (bbox ≥14, edge run ≤8, single silhouette). 8 calls,
**8/8 passed validation on the first attempt** — the pipeline's
cleanest batch.

## The lesson that matters

**bitforge's style anchor leaks CONTENT, not just style.** With canon
as style image, the closed box was generated as a round pizza and the
stack caught pepperoni contamination; only the slice — the object
semantically closest to the anchor — benefited. Ruling: style-image
anchoring is for same-object variants; cross-object family cohesion
comes from shared palette + prompt + init anchor (pixflux).

## Selections

| Asset | Winner | Note |
| --- | --- | --- |
| pizza_slice | bitforge (seed 601) | Carries canon's pepperoni density; pixflux wedge read plain-cheese |
| box_closed | pixflux (seed 602) | Bitforge arm became a pizza — rejected |
| box_open | pixflux (seed 602) | Correct lid/base/pizza composition |
| box_stack | pixflux (seed 602) | Bitforge arm pepperoni-contaminated — rejected |

Curation: quantize changed **0 pixels on all four** (running total:
8/8 curated assets across experiments at zero palette cleanup).
Deterministic oxblood "D" stamps (5×7 font, ink offset) applied to the
three box lids post-curation — brand geometry stays code. All four
re-validated PASS after stamping. Board:
`.private_art/experiment_03/review/family_final_board.png`.

Spend: 8 calls this experiment; 49 charged generations total across
all experiments; balance has displayed $10.00 throughout.

On approval, the four curated assets move to
`.private_art/experiment_03/approved/` and the family becomes the
reference exemplar for prop-family workflows (grease overlays, oven
states, signage variants are the recorded next candidates).
