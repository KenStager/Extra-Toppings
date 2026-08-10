# Experiment 01 — Whole-Pizza Prop (PixelLab vs. Omega Modern)

Status: **batch 1 generated and reviewed; AWAITING USER SELECTION**
(2026-08-10). The visual identity landed as `art_specs/color_language.md`
(v0.1, verified: 77.9% coverage measurement and spot-checked contrast
ratios reproduce exactly); the working palette below is reconciled to it
as v0.2. This file is the single non-secret authority for the
experiment; all licensed pixels live under gitignored `.private_art/`
and are never committed. Batch-1 results are recorded at the end of
this file.

## Objective

Determine whether PixelLab can produce a 16×16 whole-pepperoni-pizza prop
(on a round metal pan, transparent background) visually indistinguishable
from Omega Modern's food-service props. Bounded experiment: 8 candidates,
one optional refinement batch of ≤4, hard maximum 16 generation calls,
hard spend ceiling $2.

## Source references (verified)

Sheets verified as 256×256 RGBA, strictly binary alpha (0/255), compact
palettes (48 and 82 opaque colors). Native grid 16×16 confirmed. Cell
coordinates are zero-based `(col,row)` per the OMEGA_MAP grids.

| Crop | Sheet | Cells | Contents |
| --- | --- | --- | --- |
| `food_props` | `tileB_inside4.png` | (12,5)–(15,6) | Burger on tray, fries, burger+fries combo, drink+fries, drink cup, shake, cutting boards |
| `soda_fountain` | `tileB_inside4.png` | (14,7)–(15,8) | Soda fountain machine |
| `service_counter` | `tileB_inside4.png` | (10,8)–(13,9) | Orange service counters |
| `dishes_plates` | `tileB_inside3.png` | (1,1)–(5,1) | Metal canisters, oval plate, plate stack, square dish |
| `stove_steel` | `tileB_inside3.png` | (6,2)–(6,3) | Range/stove (steel grays) |

Perspective note (measured from the plate sprite): Omega draws round
tableware as a slightly flattened ellipse — the pizza disc must be an
ellipse a touch wider than tall, not a perfect circle. Highlights sit
upper-left; outlines are dark burgundy `#680828` (food) and navy
`#303b5a` (metal/tableware).

## Palettes

Reference palette: 20 colors (union of all five crops), stored privately
as `reference_palette.{png,json}`. Working palette for pizza + pan —
v0.2, 12 colors, reconciled to `color_language.md` and every value
verified present in the reference crops:

| Role | Hex | Color-language token |
| --- | --- | --- |
| outline_burgundy | `#680828` | Oxblood (DiNapoli's shadow) |
| outline_navy | `#303b5a` | Carbon Ink |
| highlight_cream | `#fbfbe8` | Flour |
| cheese_pale | `#f8d088` | Oven Paper |
| cheese_gold | `#dfbb02` | Cheese ramp base |
| sauce_pepperoni | `#a81031` | DiNapoli's main sauce red |
| crust_light | `#c68239` | Crust / Rust |
| crust_dark | `#b1552e` | Harbor Brick |
| dough_tan | `#d4a068` | Kraft |
| pan_steel | `#9d9c9c` | Concrete |
| pan_shadow | `#4e6472` | Dock Steel |
| pan_silver | `#cbd7cc` | Tile Fog |

v0.1→v0.2 change, flagged for review: **`#ff2b3c` (tomato_red) was
removed.** The color language reserves `#FF2B3C` as Critical-danger
signal red and assigns DiNapoli's identity the deeper `#A81031` sauce
red — the shop's own product should read in the shop's sauce red, not
the crisis color. Known trade-off: Omega's neighboring burger/fries
props use the bright red, so candidates may read slightly darker than
shelf-mates; if the batch reads dull, the flagged alternative is
readmitting `#ff2b3c` as a small material accent (it remains
Omega-native and present in the reference crops), which would be a
recorded ruling, not a silent change. `#FFE976` (cheese peak) was
considered and deferred: it does not appear in the five reference crops
and the crops-only verification rule holds until a candidate proves the
cheese needs the brighter step.

## PixelLab operation (selected and why)

`POST /v1/generate-image-bitforge` — the only operation combining a style
reference image, a forced palette (`color_image`), transparent output
(`no_background`), init image, seed control, and direct 16×16 output
(docs name 16×16 among preferred sizes; max area 200×200). `pixflux` has
a 32×32 minimum area and no style image. The remote MCP
(`https://api.pixellab.ai/mcp`) wraps these same endpoints but cannot be
attached to a running session and returns images through model context
rather than as byte-exact files; the REST API is used directly via
`tools/art_pipeline/pixellab_client.py` (bearer token from environment
only). MCP remains an option for future interactive exploration via
`.mcp.json` with `${PIXELLAB_API_KEY}` expansion.

Auth verified via the free `/balance` endpoint. Only the focused style
collage (80×48, `style_collage.png`: food props + dishes rows) and the
13-swatch palette strip are ever uploaded — never full sheets.

## Generation plan (not yet executed)

All candidates: `image_size` 16×16, `no_background` true, `isometric`
false, `outline` "single color outline", `shading` "flat shading",
`detail` "low detail", `view` "low top-down", `style_image` =
`style_collage.png`, `color_image` = working palette strip, fixed seeds.

Description core: "one whole pepperoni pizza resting on a round metal
pan, RPG map object, seen slightly from above". Negative: "background,
table, plate, text, shadow, character, antialiasing, blur".

| Candidate | style_strength | text_guidance | seed |
| --- | --- | --- | --- |
| pizza_whole_01 | 30 | 8 | 101 |
| pizza_whole_02 | 50 | 8 | 102 |
| pizza_whole_03 | 50 | 8 | 103 |
| pizza_whole_04 | 65 | 8 | 104 |
| pizza_whole_05 | 65 | 8 | 105 |
| pizza_whole_06 | 80 | 8 | 106 |
| pizza_whole_07 | 50 | 11 | 107 |
| pizza_whole_08 | 65 | 11 | 108 |

Refinement levers reserved for the optional ≤4 batch: 32×32 generation
with explicit nearest-neighbor 16×16 reduction (originals preserved,
conversion never concealed), `coverage_percentage`, init-image seeding
from a hand-blocked silhouette.

## Validation contract (automated, refuses — never repairs)

Exact 16×16; RGBA transparency; strictly binary alpha; transparent
corners; zero off-palette opaque colors; opaque bbox ≥ 9px per axis; no
opaque run longer than 4px on any canvas edge; no disconnected specks
under 3px. Implemented in `tools/art_pipeline/validation.py`; malformed
generations are preserved and reported as failures.

## Review protocol

Review board: reference crops + all candidates at 8× nearest-neighbor and
native 1×, with identifiers and pass/fail markers; scored on pizza
readability, Omega-style compatibility, perspective, palette, silhouette,
and plausibility beside the burger/fries/drink props. Top three
recommended; nothing auto-approved. Approval of one candidate is required
before any further asset (slice, boxes, grime, oven, signage, employee,
portrait) is attempted.

## Batch 1 results (2026-08-10)

Executed exactly per the matrix above: 8 bitforge calls, all at direct
16×16 (no reduction path used). One additional call failed server-side
before generating (HTTP 500, uncharged): bitforge REQUIRES the style
image to match the output size, so the 80×48 collage was replaced by
the single 16×16 burger tile, sheet cell (12,5) — recorded here because
the public docs do not state this constraint. Usage: 8 generation
units; account balance read $10.00 both before and after the batch
(billing granularity is below the API's balance display). Elapsed
14–50s per call.

Automated validation: 01, 03, 04 PASS all checks; 02, 05, 06, 07, 08
FAIL exactly one check each — `no_clipping` (opaque edge runs of 6–8px;
threshold 4). Every candidate passed dimensions, hard alpha,
transparent corners, palette adherence (zero off-palette colors in all
eight — the forced palette worked perfectly), bbox, and the speck
check. Failures are preserved unrepaired in
`.private_art/experiment_01/candidates/`; provenance in
`.private_art/experiment_01/provenance/` (credential-free).

Visual scoring (boards:
`.private_art/experiment_01/review/review_board_batch1{,_ranked}.png`):

| Candidate | Verdict |
| --- | --- |
| 01 (s30) | PASS; clean disc, but reads pot-pie: no pepperoni, no pan — **3rd choice** |
| 02 (s50) | FAIL; gray hook artifact, clipped right |
| 03 (s50) | PASS; disconnected satellite blob, no pan or pepperoni |
| 04 (s65) | PASS; best overall — crusted disc, in-palette mottling, minor corner crumb — **1st choice** |
| 05 (s65) | FAIL; navy dome over dish, reads covered tray, clipped top |
| 06 (s80) | FAIL; coherence collapse into fragments at max style strength |
| 07 (s50 tg11) | FAIL; real pepperoni dots (best topping readability) but clipped + satellite disc |
| 08 (s65 tg11) | FAIL; best "pizza ON PAN" composition of the batch, but pan is navy not steel and it clips bottom/right |

Shared failure diagnosis: at 16×16 the model's weakness is
COMPOSITION, not style — palette, alpha, and outline behavior were
perfect across all eight, while centering/completeness failed in five.
Style strength 80 destroys coherence; 50–65 is the working band;
tg 11 improved topping semantics (07, 08) at the cost of framing.

Recommendation: 1st `pizza_whole_04`, 2nd `pizza_whole_08`, 3rd
`pizza_whole_01`. None auto-approved. If no candidate is accepted, the
diagnosis licenses the one refinement batch (≤4 calls, within budget):
generate at 32×32 with `coverage_percentage` ~75 and the plate tile
(3,1) as style reference, then explicit nearest-neighbor reduction to
16×16 with originals preserved — attacking composition while keeping
the proven palette discipline.

Pipeline limitations discovered: (1) bitforge style_image must equal
output size (undocumented); (2) the speck check only flags components
under 3px, so 03's larger satellite blob passed automated validation —
tightening this is a recorded candidate change for after the
experiment, not a mid-experiment edit; (3) PixelLab bills in
generation units whose USD value is below balance-display granularity,
so per-call cost is bounded (≤$0.00 visible delta) but not exactly
measurable from the API.

## Batch 2 + recon sweep results (2026-08-10, limits lifted by user)

The user lifted the 16-call/$2 caps for recon. Validator v2 (adds
`single_silhouette`: any disconnected component fails) applied from
batch 2 onward; batch-1 numbers stand as measured under v1 (under v2,
04 correctly fails on its pan-shard satellite — 23px, mostly
pan_steel, the forensic tell that "pizza resting on a round metal pan"
reads as TWO objects to the model).

Research (documented facts): bitforge pricing $0.0071–$0.00734 at
32×32; seeds give "very similar", NOT identical, results per
PixelLab's own docs; init_image_strength 1–999 default 300, "higher =
preserve more"; coverage_percentage documented only as "percentage of
canvas to cover"; the style_image-must-equal-output-size constraint is
confirmed absent from all official docs; MCP exposes purpose-built
object tools (create_1_direction_object, selective style_copy) as a
future option.

Batch 2 (4 arms, fused single-object prompt + anti-fragment negative):
09 bf@16+coverage85 FAIL (satellite); 10 bf@16+init150 FAIL
(satellite + corner); 11 bf@32→NN16 PASS; 12 px@32→NN16 PASS (best
pan). Sweep (10 calls at 32px): bf replicates 13 PASS / 14 FAIL
(bbox 8×8) / 15 PASS (pan retained); 16 style-65 PASS; 17 no-init
FAIL (satellite — the ablation that proves the init anchor suppresses
satellites); 18 init-300 FAIL (5px left clip inherited from the
anchor's own zero-margin ellipse — anchor fix recorded below); pixflux
19 FAIL (clip) / 20 PASS / 21 PASS / 22 init FAIL (clip).

### Recon conclusions (the durable process for future assets)

1. NEVER generate final-size 16×16 directly: 0/10 clean two-object
   compositions across both batches. Generate 32×32, reduce by
   deterministic nearest-neighbor, preserve originals.
2. Always anchor composition with a hand-blocked init silhouette at
   strength ~150; leave ≥1px transparent margin in the anchor (the
   init-300 clip came from the anchor touching edges — fix the anchor,
   then strength 200–300 becomes viable for pan retention).
3. bitforge (style path) preserves Omega texture language; pixflux
   composes containers (pan) better without a style image. Both hold
   the forced palette perfectly: 22/22 charged generations had zero
   off-palette colors.
4. Style strength 50–65 at 32px is safe; 80 collapses (batch 1).
5. Seeds are variance, not determinism — plan selection pools, not
   single shots.

### Final ranking (16×16 finals, validator v2)

1st `pizza_whole_15` (bitforge@32, seed 207) — pizza with steel pan
rim, pepperoni, single silhouette, full pass; the Omega-style path
delivering the complete brief. 2nd `pizza_whole_12` (pixflux@32, seed
204) — strongest pan composition. 3rd `pizza_whole_21` (pixflux@32,
seed 213). Polish path: `pizza_whole_18`'s pan rendering is the best
of all 22 but fails a 5px edge clip — regenerating with the
margin-fixed anchor is the designated cleanup if the user wants it.

Cost: 22 charged generation units total (batches 1+2+sweep); balance
displayed $10.00 throughout; estimated ≤$0.17 by published rates.
Awaiting user selection.
