# Experiment 06 — Wear Decals and the Sparse-Canvas Question (2026-08-10)

Status: **RULING REVERSED AT THE BOARD (see the correction below the
Results) — generation branch REOPENED; step 2 (window-cut fields)
proposed, awaiting the user's word.**

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

## CORRECTION — ruling reversed at the board (same day, user's eye)

The user reviewed the boards and overruled the paragraph above: some
of the FAILED probes look better than the PASSES. Re-examination at
6× in context confirms it, and the record must own three errors:

1. **The probes' organic irregularity is the quality.** s3102/s3103
   (~38 opaque px of clustered ink/slate) drift and clump the way
   tracked-in grime actually does. The deterministic grease blob
   (134 px, saturated 2-tone) reads as a PROP — a cartoon puddle that
   shouts on a layer that should murmur; the scuff strokes read as
   procedural glyphs. The session's own builders were judged by a
   contract written to match what those builders produce — the
   instrument judging its maker.
2. **min_coverage = 0.02 was an invented threshold** — precisely the
   a-priori-threshold error Experiment 04's calibration lesson exists
   to prevent, and it refused s3101 (1.2%) which still reads in
   context. The floor is hereby DROPPED from the contract pending a
   calibrated replacement; visibility is a board judgment.
3. **The session's board verdict ("cold static") was hasty** — made
   against the dark sheet background with the validator's FAIL in
   mind, not against the in-context panels. The metric-relabeling
   ruling (R3) warned about exactly this substitution.

What SURVIVES the reversal: the edge/corner discipline (a composited
decal must not clip; but the fix is construction, not vendor
obedience) and the flour-dust deterministic family (it read fine).

STEP 2 (proposed, awaiting the user's word, ~3–4 generations):
generate sparse wear FIELDS at 96×96 (one ink-scuff register, one
warm-grease register via a warm strip), then window-cut multiple
clean 32×32 interiors per field — the tileability-step-1 trick;
window-cutting is an unconditional construction step, so edge
discipline holds by construction while the vendor's organic texture
is kept. Candidates judged at the board like everything else.

## Step 2 results (2026-08-10, 4 generations)

User said proceed. Two registers × two seeds at 96×96:

- **Ink register (seeds 3201/3202): both fields came back COMPLETELY
  EMPTY** — 0.000 coverage, the model left the whole canvas
  transparent. New capability datum: the sparse prompt can collapse
  to nothing at field scale; sparseness is uncontrolled in BOTH
  directions. Recorded, 2 generations spent on the measurement.
- **Warm register (seeds 3301/3302): both usable** (1.0%/2.2% field
  coverage). Window-cutting (stride 4, decal contract + ≥2
  components, top 3 non-overlapping per field) yielded SIX
  contract-clean candidates. The s3302 cuts are the standouts —
  clustered dark-warm stains with satellite specks (13/8/6
  components), asymmetric, story-bearing; exactly the organic
  quality the board preferred over the deterministic blobs. All six
  pass validate_decal as cut, zero pixel edits (`post_processing:
  unconditional window crop` in each provenance record).

Candidates `decal_cut_warm_*` and board `review/decal_board_step2.png`
await the user's picks alongside the deterministic flour family. The
ink register's grime niche (thresholds, entryways) remains open — a
re-prompt with less aggressive emptiness language is the obvious next
probe if the board wants cold-register dirt.

## Board round (2026-08-10): "looks great," one issue — investigated

User: the decal seems to end up BEHIND the checkerboard. Measured:
compositing is correct — all 48 opaque decal pixels sit on top of
the composite byte-for-byte, and the decal (luminance 40/108) is
darker than both checker tones (156/210); proof board
`review/checker_contrast_proof.png` dims everything except the decal.
The read is figure-ground: a crisp periodic checker grid reads as
figure, so an irregular sparse stain interleaves and reads as ground.
COMPOSITION GUIDANCE (recorded like the terracotta note): sparse
speckle decals belong on field floors (plank/parquet/tile_warm);
checker floors take only the denser contiguous-blob decals, judged
in context. Formal approval of the six warm cuts + flour family
awaits the user's word now that the issue is explained.

## Full approval (2026-08-10, user board)

"E06, full approval" — the six warm window-cut decals and both flour
decals moved to `approved/` with the composition guidance recorded in
each approval record. Eight production wear decals total; the wear
layer ships.
