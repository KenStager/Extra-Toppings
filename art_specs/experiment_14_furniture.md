# Experiment 14 — Furniture Rework: The E02 Trio Reaches the Contract (2026-08-10)

Status: **RULED (user board 2026-08-10, "Proceed" with two
corrections): counter_main, counter_end, chair_a, chair_b APPROVED
(judgment call flagged in their records: approved by
proceed-with-no-objection, reversible). kitchen_range REJECTED —
"we have already built our pizza deck": the shop cooks in the
approved E05 deck oven; a household range is off-register for a
pizzeria. And the board confirmed what the rework found — "those
tables don't look like tables" because they never were: the E02
sprite was always two chairs, so the shop has NO TABLE ASSET while
the design doc stages Carmine at "the corner table." A table study
opens as E15.**

## What the measurements found

The curated-unapproved E02 trio (counter 128×64, kitchen range 32×64,
"chair family" 64×64) was measured under the prop contract and failed
for reasons that are all DETERMINISTICALLY fixable:

- The "chair family" is TWO CHAIRS on one canvas — `single_silhouette`
  fails by construction, and the game composites its own chairs (the
  seated-extras pick criterion), so it needs single chairs anyway.
- The counter is likewise two segments (main run + end cap) plus
  ~55 stray cold pixels (slate/gray/pale specks on warm wood) and
  edge clipping.
- The range carries a genuinely floating 24×2 bar above the body and
  clips both side edges.

## The rework (recorded recipes, no generation)

Every piece is a crop + margin re-canvas + deterministic cleanup,
recipe in provenance:

| Piece | Canvas | Fixes | Result |
| --- | --- | --- | --- |
| counter_main | 96×64 | split, margins, 36px majority-neighbor despeck | PASS |
| counter_end | 48×64 | split, margins, 18px despeck | PASS |
| kitchen_range | 40×64 | floating bar dropped, margins, 2px fill | PASS |
| chair_a | 32×48 | split, margins | PASS |
| chair_b | 32×48 | split, margins | PASS |

Despeck is majority-neighbor fill over an enumerated stray set
(#303B5A #4E6472 #9D9C9C #CBD7CC #FBFBE8 #FF8628) — deterministic,
recorded, re-runnable. The chairs needed zero pixel edits.

## Open at the board

1. Approve the five v2 pieces (unblocks the FURNISHED ensemble scene
   and seated extras on real chairs).
2. Register question, honest: the range's steel register is COLD
   (slate/gray by generation, an appliance argument exists) — accept
   as the one cold object in a warm kitchen, or queue a warm-accent
   curation pass as its own recorded revision.
3. The original combined sprites remain in `curated/` untouched —
   the v2 pieces are new artifacts, not edits to old ones.
