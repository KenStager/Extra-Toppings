# Experiment 04 — Floors and the Tileability Instruments (2026-08-10)

Status: **step 0/0.5 COMPLETE at zero generation cost; five floor
candidates AWAITING USER APPROVAL.** Steps 1–3 (generation paths, Wang
fallback) remain available but may be unnecessary.

## Instruments (tools/art_pipeline/tiling.py, 7 tests)

Wrap-seam scoring (seam column/row vs interior adjacent-pair
distribution, palette-aware), toroidal eventlessness (largest blob,
max local 3×3 contrast), 3×3 tiled previews, and mirror-fold
construction. Calibrated on all 24 commercial floor cells of
tileA5_inside rows 0–2 before judging anything.

## Calibration lessons (each one would have corrupted results)

1. **A-priori thresholds were wrong:** commercial floors that tile
   perfectly score seam-diff up to 0.94 and percentile 0.8–0.9 —
   in a periodic floor the wrap seam IS a structural boundary. The
   invented "75th percentile" rule would have rejected Omega's own
   art. Band = "seam may tie, never exceed, the worst interior
   structural boundary."
2. **The band is scale-dependent:** NN-doubling doubles interior
   pairs but not boundary count; a 16px-calibrated band mis-fails
   32px candidates. Calibrate at candidate scale (28/31 at 32px).
3. **Store bands exact, never rounded:** a band rounded to 0.903
   re-failed the very donors that defined it at 0.90322…

## Step 0.5 result — floors need NO generation

2× NN + quantize to (13 chips ∪ donor colors) — both wrap-safe,
pixel-local, unconditional construction steps. The chips-ONLY recolor
was tried first and destroyed the wood floors (all 1024 px snapped;
browns → cheese gold), confirming the flagged chip-list gap; the
union rule (donor-native ramps are legal) is the floor policy.
Candidates, all zero generations, in
`.private_art/experiment_04_floors/candidates/`:

| Candidate | Donor cell | Verdict |
| --- | --- | --- |
| floor_plank | (1,1) | PASS |
| floor_parquet | (3,1) | PASS |
| floor_checker_cream | (0,2) | PASS |
| floor_tile_warm | (5,2) | PASS |
| floor_weave_tan | (6,0) | PASS |
| floor_smalltile | (2,2) | borderline (defines the contrast ceiling); excluded |

Cell (0,0) proved uniform (a non-candidate picked off a thumbnail —
donor cells get inventoried before selection next time).

## Drift harness (tools/art_pipeline/drift.py, 7 tests) — CALIBRATED

4 probes with exact historical params (canon pizza seed 204, box_open
seed 602, slice bitforge seed 601, palette canary seed 904); 3
same-day runs; baseline + exact band in `.private_art/drift/band.json`.

Measured: **same-day variance band = 0.2412 diff-fraction / 0.1064
hist-L1** — pixflux's "very similar" seeds move up to 24% of pixels
call-to-call. The synthesis's placeholder thresholds (10%/0.05) would
have false-alarmed permanently; calibration-before-doctrine vindicated
again. **probe_slice_bitforge is byte-identical across all runs AND
vs its historical output — bitforge is deterministic for this cell**
(a Tier-A pin), while pixflux probes judge against the band. Today's
runs sit inside the band vs historical outputs: no drift; the canary
held 0 off-palette colors in all runs under a maximal-temptation
rainbow prompt. Protocol: run the harness first in any session that
will spend generations; Tier C freezes generation.

Spend: 12 calibration generations + this experiment's 0. Ledger live
at `.private_art/drift/spend_ledger.jsonl`.
