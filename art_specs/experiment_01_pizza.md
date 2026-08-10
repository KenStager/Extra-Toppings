# Experiment 01 — Whole-Pizza Prop (PixelLab vs. Omega Modern)

Status: **tooling complete; PAUSED before generation** (2026-08-10).
The visual identity landed as `art_specs/color_language.md` (v0.1,
verified: 77.9% coverage measurement and spot-checked contrast ratios
reproduce exactly); the working palette below is reconciled to it as
v0.2. Generation awaits the user's explicit go. No PixelLab calls have
been made and the full attempt/cost allowance is unspent. This file is
the single non-secret authority for the experiment; all licensed pixels
live under gitignored `.private_art/` and are never committed.

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
