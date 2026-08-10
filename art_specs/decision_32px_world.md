# Decision: Genuine 32×32 World Art (2026-08-10)

User ruling. Extra Toppings adopts a native **32×32 tile target** for
pixel-world locations. Omega Modern (16×16 native) becomes a donor
library — visual and compositional foundation, not production
resolution. Omega VX sheets are exact 2× enlargements (verified for
`tileC_town4` via `scale_equivalence.csv`) and serve as positional
scaffolding only; they are never presented as newly detailed 32×32 art.

Governing rule: **twice the resolution, not twice the visual noise.**
Thesis: *thirty years of oven warmth against thirty days of
carbon-paper pressure.* Avoid: cyberpunk/neon-noir, overt mob/gun/drug
imagery, Italian-restaurant clichés, micro-detail, vector smoothness,
gradients/antialiasing/translucent fringes, red-for-every-danger.
Preserve Omega's silhouettes, hard edges, compact ramps, 3/4 dollhouse
readability, at-a-glance object function.

## Experiment palette (directive chips, verbatim)

`#000000` outline · `#303B5A` carbon/midnight ink · `#4E6472` harbor
slate · `#9D9C9C` worn gray · `#CBD7CC` cool pale neutral · `#FBFBE8`
flour/newsprint cream · `#C68239` crust/toasted wood · `#A81031`
oxblood · `#FF2B3C` critical red · `#FFE976` oven/cheese gold ·
`#FF8628` heat orange · `#3854DA` case blue · `#75E2EF` institutional
cyan. Assets select small local ramps; warm dominates DiNapoli's
world; cold blues/cyan are controlled institutional signals.

FLAGGED deltas vs `color_language.md` v0.1, for reconciliation in a
future color-language revision (directive is authoritative for this
experiment): (1) the token "Oxblood" now names `#A81031` (v0.1 named
`#680828` Oxblood and `#A81031` "main sauce red"); (2) `#680828`,
`#B1552E`, `#D4A068`, `#F8D088`, `#F8F8C0`, `#6C8C88` are absent from
the chip list (still legal as Omega-native local-ramp colors where a
donor uses them); (3) black `#000000` is promoted to the named outline
(v0.1: black for external silhouettes, hue-shifted internal shadows —
compatible).

## Canonical identity

Restaurant: **DiNapoli's Pizza** (never "Extra Toppings" on the
façade — that is the game title). Identity: established East Coast
neighborhood pizzeria; oxblood enamel sign, cream lettering, oven-gold
trim, hard midnight/carbon offset; simple pizza-pan "D" emblem;
friendly and legitimate at first glance; no chef mascot, flag motif,
mob reference, or ornate script. Generated lettering is reference
only — final `DINAPOLI'S` text is redrawn deterministically. Targets
at the new resolution: sign 128×16 → **256×32**; emblem 16×16 →
**32×32**.

## Vertical slice (Experiment 02)

Primary façade test — donor `tileC_town4.png` cells (0..7, 5..7)
(coordinates confirmed against the OMEGA_MAP grid: FOOD/DINER band row
5, storefront rows 6–7; 128×48 native). Produce: native donor crop,
exact 2× scaffold (256×96), genuine PixelLab 32px-class redraw,
palette-constrained curated version, deterministic-sign version,
in-context 640×360 landscape preview, and a 50% preview proving
Omega-class readability. Footprint and collision implications
preserved unless a documented reason requires otherwise.

Supporting object test after façade coherence: one floor/wall
junction, one oven/appliance, one service counter, one table/chair
family, one branded prop — only enough to test generalization; no
full-sheet conversion. Note: `pizza_whole_12` and `pizza_whole_21`
were generated at genuine 32×32 (originals preserved un-reduced), so
the branded-prop slot already has candidates under the new target.

Technical contract for production candidates: dimensions divisible by
32; nearest-neighbor scaling only; binary alpha (no fringe); readable
at 50%; aligned to the 32px grid; palette-disciplined; clear donor
relationship; Godot 4 TileSet-compatible. No game refactor or
coordinate migration yet; any Godot preview is an isolated 640×360
scene.

Decision gate before any bulk conversion: (1) does 32×32 materially
improve story-bearing detail; (2) still Omega-related; (3) readable at
phone-landscape size; (4) palette consistent across generations;
(5) cleanup burden reasonable; (6) repeatable without drift.

## First-pass results (2026-08-10)

Ten charged calls (2 full-scaffold probes, 3 blank-sign sweep, 1
interpolation, 4 inpaint halves), all provenanced under
`.private_art/experiment_02/`. API limits discovered empirically:
bitforge AND inpaint cap at 200px per axis (uncharged 422s); pixflux
accepts 256×96 (400px cap) — so pixflux is currently the only
single-shot path for multi-tile facades.

The winning recipe: blank the brand band in the 2× scaffold → pixflux
init strength ~120 (tg 9) for a genuine redraw → forced palette (13
chips ∪ donor colors) → deterministic brand layer (sign, awning,
emblem) composited over. Init ≥250 produces upscaled-copy output
(rejected by the governing rule); init 120 produced genuinely new
story-bearing form: brick coursing, stone base, and window displays
with readable goods. Curation quantize changed ZERO of 24,576 pixels —
the forced palette held perfectly, as it did across all 22 Experiment
01 generations.

Negative results, preserved: (1) window-display inpainting over the
structure-faithful i250 failed — the color-derived glass mask was too
fragmented to compose displays (windows went dark); (2) awning
inpainting over i120 failed — the endpoint did not faithfully preserve
unmasked parapet pixels. Consequence: brand geometry (sign, awning,
emblem) is DETERMINISTIC by policy, generated pixels are body texture
only. The 5×7 pixel font (D,I,N,A,P,O,L,S,'), 256×32 enamel sign, and
32×32 pan-D emblem are code, not generations.

Gate answers: (1) story-bearing detail — YES (displays, coursing,
stone base vs the donor's flat stripes); (2) Omega-related — footprint
and dollhouse read preserved, body texture drifts warmer/mercantile;
the deterministic awning restores the diner identity; 50% preview
sits comfortably at Omega scale; (3) phone readability — sign legible
at 100% and 50%, 640×360 scene clean; (4) palette consistency —
emphatic yes (0 off-palette pixels, twice measured); (5) cleanup
burden — LOW for palette/alpha (zero), MODERATE for composition
(seed/strength lottery: ~7 calls to one great body; failed surgeries
cost 6 calls of learning); (6) repeatability — recipe is written and
parameterized; the lottery means selection pools remain the plan.

Recommendation: PROCEED at 32×32 with this recipe. Known follow-ups:
window displays should be prompted pizza-specific (boxes, pizzas,
bottles) rather than general goods; the emblem D wants one more
iteration at 32px; supporting-object test is next (pizza_whole_12/21
originals already satisfy the branded-prop slot at genuine 32×32).
Spend to date across both experiments: 32 charged generation units;
balance has displayed $10.00 throughout (est ≤ $0.30 total).

## Reflect–revise–repeat pass (2026-08-10, same day)

Phase A — the deterministic layer is now pipeline code
(`pixel_font.py` full A–Z/0–9 5×7 set, `branding.py` sign/emblem/
awning builders, `palettes.quantize_to_palette`), 29 tests, ruff
clean. The facade and all future branding run through these functions,
not scripts.

Phase B — facade body revision with pizza-specific display prompts,
three seeds at the proven pixflux init@120 cell. Seed 402 selected:
display windows show pizzas on pans, bottles, and warm wood; seed 403
REJECTED on palette semantics (it used Critical `#FF2B3C` as shop
material — the reservation is enforced in review, not just documented).
Final `facade_v2_final_branded.png` = s402 + deterministic awning +
sign, quantize changed 0 px.

Phase C — supporting objects via the same recipe (donor crop → 2×
scaffold → pixflux init sweep → quantize): oven 32×64 (tileB_inside3
(6,2..3), i170), service counter 128×64 (tileB_inside4 (10..13,8..9),
i170 — i120's weathering read as noise and was rejected under the
governing rule), and a chair family 64×64 (tileB_inside2 (0..1,9..10),
i120 — recorded honestly: the crop was mislabeled "table" but the
donor cells are chairs; the generated red-checkered upholstery is a
keeper). Quantize changed 0 px on ALL of them — palette discipline is
now 4/4 assets at zero cleanup.

Canonical prop: `pizza_whole_12_orig32` and `pizza_whole_21_orig32`
both PASS full validation at native 32×32 (expected_size 32, bbox ≥18,
edge run ≤8). Both sit on the family board
(`review/family_board_v2.png`) beside the facade, oven, counter,
chairs, and the deterministic emblem; the scene preview
(`preview/scene_v2_640x360.png`) shows the branded facade in the
640×360 viewport. User choice between 12 and 21 still open.

Spend: 41 charged generations across all passes; balance has displayed
$10.00 throughout (est ≤ $0.31). The repeatable recipe, now stable:
donor cells → 2× scaffold (blank any brand bands) → pixflux init@120
(bodies) or 150–170 (objects wanting donor fidelity) → forced palette
(chips ∪ donor) → quantize check (expect 0) → deterministic brand
layer → 50% readability check → family board.
