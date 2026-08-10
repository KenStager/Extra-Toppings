# Experiment 06 — Wear Decals and the Sparse-Canvas Question (2026-08-10)

Status: **COMPLETE — deterministic candidates AWAITING USER APPROVAL;
generation declined on measured quality (see Results).**

## Question and theme role

Question (named, per standing rule): can pixflux produce a SPARSE
overlay — a mostly-transparent canvas with scattered marks — or does
it treat every canvas as an object to fill? Theme role: the wear layer
is where "thirty years of oven warmth" becomes visible — grease
shadows under the oven, scuffed thresholds, flour dust behind the
counter. Wear is story, not noise.

Prediction (recorded before running): pixflux fills the canvas or
coalesces the marks into a single object — the whole prop recipe
(single silhouette, no_background) points that way. Decals are
expected to end up mostly/entirely deterministic.

## Decal contract (validator addition, not a relaxation of the prop one)

A decal is a different KIND of asset; it gets its own contract
(`validate_decal`), exactly as the portraits note anticipated for UI.
Checks: expected size (32×32 default), hard binary alpha, palette
adherence, transparent corners, no canvas-edge runs beyond 4 px
(decals live in the tile interior), and COVERAGE within
[0.02, 0.50] of the canvas — a decal that covers more than half the
tile is a floor variant, not an overlay; one under 2% is invisible at
device scale. Deliberately absent: single_silhouette (multi-blob is
the medium), garbage-speck check (specks are the point), min bbox.
Refuses, never repairs, as always.

## Step 0 — deterministic wear (0 generations)

`tools/art_pipeline/wear.py`, seeded `random.Random` only, colors from
the legal Omega-native warm ramp and chips:

- `grease_stain`: drifting-disk blob accumulation; interior `#680828`,
  rim `#B1552E` — a 2-tier ramp, honoring the recorded lesson (shift
  ramps, never collapse to one color).
- `scuff_marks`: 3–5 short strokes in `#4E6472` with `#303B5A` cores —
  threshold scuffs.
- `flour_dust`: scattered 1–2 px specks, `#FBFBE8` with `#CBD7CC`
  minority — kitchen-side dusting.

All construction stays ≥2 px inside the canvas (corner/edge rules by
construction). Candidates ship with in-context previews composited on
approved floors — a decal is only judgeable in context.

## Step 1 — the probe (≤3 generations, then stop)

Three pixflux seeds, 32×32, sparse-marks prompt, forced wear-palette
strip, `no_background`. Measured: opaque coverage fraction +
`validate_decal` verdict. KILL CRITERION (fixed now): if all three
probes land coverage > 0.50 or fail hard-alpha/palette, the generation
branch for decals is CLOSED and decals are deterministic by policy —
the cheap disproof the queue asked for.

## Results — recorded after execution (same day)

Step 0: all three builders hold the decal contract across a 150-build
seed sweep (50 seeds × 3 families, zero failures) after two honest
contract catches during development — the first scuff draft measured
1.5% coverage (under the visibility floor) and the first flour draft
dipped to 1.7% at seed 2; both were fixed in the BUILDER, never the
contract. Six candidates (2 per family) with in-context floor
composites are under `candidates/` and `review/`.

Step 1, measured: **the prediction was WRONG, and the branch still
loses.** Pixflux CAN leave a canvas sparse — coverage 0.012 / 0.038 /
0.037, nowhere near the 0.50 kill line, and the forced palette held.
The kill criterion did NOT trigger. But all three probes fail the
contract anyway: s3101 under the 2% visibility floor, s3102/s3103 run
marks off the canvas edges and corners (composability violations), and
at the board the marks read as scattered cold static, not as wear with
a story. The deterministic set beats them on every axis while costing
nothing.

RULING RECORDED: wear decals are DETERMINISTIC BY POLICY — grounded in
measured quality comparison, not the kill criterion. The capability
note stands for the record: pixflux respects "mostly empty canvas"
prompts at 32×32, which may matter someday for a different asset
class; edge discipline is what it cannot promise. Spend: 3
generations, ledgered, provenance v2 with measured coverage in each
record.
