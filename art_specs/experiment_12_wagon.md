# Experiment 12 — The Delivery Wagon (BRIEF ONLY, 2026-08-10)

Status: **PAPER. Zero generations spent or licensed. Every decision
below is presented for the user's ruling; nothing here is doctrine
until ruled.**

## Why the wagon matters (sources)

The wagon is core mechanics, not dressing: routes sell what the wagon
carries (`VEHICLE_CARGO = 24`, data.py:280), raids and escrow
reference it, the owner rides along, and the opening of game.py names
it in the same breath as the shop, the recipes, and the debt. It is
also the registry ruling's anticipated case (decision doc: the
style-object registry was rejected-for-now EXCEPT for "genuinely
multi-directional subjects (employee, vehicle), after a leak test,
and then only as a derived cache").

The game's own word is **wagon** — game.py, escrow.py, bot.py never
say van or truck. The art must not contradict the text.

## Decision 1 — era and silhouette (RULING NEEDED)

Old Harbor is a 1960s-class East-coast port town. Options:

- **(a) Panel van, 1950s–60s** (recommended): rounded-nose panel van
  (Metro-van class). Period-correct, box-bodied enough that "wagon"
  still reads honestly, and the flat side panels are the natural
  canvas for DiNapoli's livery. Thirty years of oven warmth implies
  the family bought it decades ago — a well-kept older vehicle is
  itself a story fact.
- **(b) Step van / bread truck**: taller, flatter, maximum livery
  surface; reads more "fleet", less "family".
- **(c) Literal horse-or-hand wagon**: takes "wagon" at its word;
  period-wrong for the 1960s and contradicted by routes/raids pacing.

## Decision 2 — footprint (measured, RULING NEEDED)

Measured against the approved world: figures are 32px/1 tile; the
facade is 256×96 (8 tiles wide, doorway ≈32px high). Pixel-art
convention compresses vehicles relative to people, and a van that
dwarfs the facade would be wrong beside it. Proposed: side-view body
≈ **80×44px** (2.5 tiles long, door-and-a-bit tall — a real ~4.5m van
at the world's compression), on a **96×96 generation canvas** (square,
inside the 8-rotation pipeline's 32–168 limit, headroom for
diagonals). The 64×32-class canvas from the original question is too
small once the van must read beside a 32px driver.

## Decision 3 — direction count (RULING NEEDED)

Streets and routes are tile-cardinal; movement needs N/S/E/W only.
Proposal: generate all 8 (the vendor pipeline's native output),
validate all 8 under the prop contract, but approve the **4 cardinals
as movement canon** and hold the diagonals as scene-dressing
candidates (ride-along beauty shots) pending their own board. This
costs nothing extra — the 8-direction pipeline renders all angles in
one job — and avoids blessing frames the game doesn't need yet.

## Decision 4 — branding (RULING NEEDED, but the law is settled)

DiNapoli's livery follows the sign rules: **brand lettering is CODE**
(pixel_font/branding.py), never generation — generation invents
letterforms and the negative "text" stays in every prompt. The livery
is a deterministic brand layer applied post-approval to the side
views (east/west), same policy family as the facade sign and the
recorded-curation precedent. Emblem reuse: the existing emblem_D
at wagon scale, measured, not assumed to fit.

## Decision 5 — generation path (RULING NEEDED)

- **(a) `create_8_direction_object`** (20–40 gens/call, size ≤168,
  view low top-down, accepts `reference_image_base64`): one call
  yields all 8 directions with vendor-enforced cross-direction
  consistency. RISK, measured this session on the portrait surface:
  the tool has **no negative-prompt surface** (params: description,
  reference, style only), and E11 proved promptless surfaces let
  priors fill every vacuum. Counter: a hand-blocked side-view anchor
  as `reference_image_base64` (the E09 anchor discipline) plus a
  description carrying era words.
- **(b) pixflux per direction** (proven surface, full negatives,
  ~1 gen/attempt): 4 hand-blocked anchors (side L/R can mirror-flip
  only if the livery layer is applied AFTER mirroring — lettering
  must never mirror), init@140. Cheap iteration, but cross-direction
  consistency is entirely on our anchors.
- **Proposed sequence**: pixflux SIDE-VIEW study first (2–3 gens, the
  cheap surface, negatives available) to converge silhouette and
  palette with the board; THEN one `create_8_direction_object` call
  seeded with the approved side view as reference. The study de-risks
  the expensive promptless call — the E11 lesson applied in advance.

## Registry position (per the standing ruling)

If path (a) runs, the resulting object_id is recorded as **derived
cache only** (character_ids.json precedent); local curated PNGs are
canon. The leak test the ruling requires: before any style_object_id
reuse, generate one unrelated probe object against the registered
wagon style and measure for content leakage; refusal to run the test
means refusal to reuse the id.

## Palette and validator (contract sketch, calibration before doctrine)

Body register: the family's warm chips (cream body, oxblood accents)
with worn-gray underbody — the wagon belongs to the shop family, not
the pressure register; case blue is impossible by law. Validator:
prop contract at the chosen canvas (single silhouette per direction,
hard alpha, palette legality after curation quantize), thresholds
measured from the first real outputs, not invented here.

## Cost envelope (for the ruling, not spent)

Side-view study ~3 gens (pixflux, ledgered) + one 8-direction call
20–40 gens (MCP-side, vendor balance authority) + re-rolls at the
board's discretion. Balance at writing: 4,483 generations remaining
before this brief; the idle pass and probes since spent MCP-side (see
E09/E11 records).

## STOP

Nothing below this line exists. No generation, no anchor pixels, no
livery mock until the user rules on decisions 1–5.
