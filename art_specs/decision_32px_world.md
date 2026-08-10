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

## Engine scorecard (empirical, through Experiment 03 — 49 generations)

What we have actually experienced, recorded before the round-2
documentation research so the data and the docs stay separable:

| Dimension | pixflux | bitforge | inpaint |
| --- | --- | --- | --- |
| Cells won | Canon pizza (12), facade body, all 3 boxes, chair family, oven, counter | pizza 15 (exp01 1st pick), slice (canon-adjacent) | none |
| Composition at 32px+ | Strong with init anchor | Adequate | — |
| Canvas limit | 400px/axis (only single-shot facade path) | 200px/axis | 200px/axis |
| Style transfer | n/a (no style image) | LEAKS CONTENT across objects (box→pizza); only safe same-object | — |
| Style-size constraint | n/a | style_image must equal output size (undocumented) | — |
| Unmasked-pixel preservation | n/a | n/a | FAILED twice (re-renders canvas) |
| Palette discipline (forced) | Perfect (0 off-palette, every asset) | Perfect | untested post-failure |
| Cost per unit | identical | identical | identical |

Standing policy pending research round 2: **pixflux is the default
engine at 32×32** (composition + canvas headroom + family cohesion via
palette/prompt/anchor); bitforge is reserved for same-object style
variants and canon-adjacent props; REST inpaint is avoided. Open
questions sent to the documentation researcher: model lineage, the
MCP-only `create_image_pro` (selective style_copy could fix the
content-leak problem), style-object registry, newer inpaint variants,
tileability support, rotation/animation surfaces for later phases.

## Research capsule, round 2 (2026-08-10, documented facts only)

From the documentation researcher (citations in the session record;
tool catalog: api.pixellab.ai/mcp/docs):

- **Model surface is four, not two.** Beyond REST pixflux/bitforge,
  two MCP-only generators exist: Pixen (larger canvas) and **Pro**
  (`create_image_pro`: 512×512 max, returns multiple candidates per
  call, 20–40 generation-credits each, up to 4 labeled reference
  images with per-image usage notes, and `style_copy` — selective
  copying of only color_palette/outline/detail/shading). Whether
  style_copy avoids bitforge's content leakage is undocumented.
- **Style-object registry (MCP-only):** a completed 8-direction
  object (`create_8_direction_object`, 32–168px) becomes reusable via
  `style_object_id`. Candidate mechanism for canon-anchored family
  work; untested.
- **Positioning per PixelLab's own docs:** pixflux is "the most
  general model… for most things" (min 32², max 400² tier-gated);
  bitforge is the style-reference tool for small/medium images. They
  are parallel tools, not a lineage; no quality ranking exists.
- **Inpaint v3 / pixpatch v2** are named only in the Aseprite plugin
  nav; REST/MCP expose a single older inpaint. Plausibly explains our
  two REST inpaint failures; unconfirmed.
- **No seamless-wrap tile support exists anywhere.** PixelLab's tile
  tools are Wang/autotile edge-matching sets (`create_topdown_tileset`
  etc., MCP-only). True self-tiling floors are undocumented territory
  — our experiment must carry its own wrap-seam validation.
- **No model versioning, no changelog, no pinning.** Silent weight
  drift under fixed seed+params is undetectable via PixelLab; a
  local fixed regression set is the only defense.
- **Pricing:** pixflux ≈ bitforge ≈ $0.007/gen at 32×32 — cost is not
  a model differentiator at our scale. Pro is ~20–40× per image but
  multi-candidate.
- **Animation (future):** skeleton tools bless only square 16/32/64
  sizes; 32×64 walk frames are unblessed. Character identity-transfer
  rotation is documented as less reliable than object rotation.
- **MCP attach:** `claude mcp add pixellab https://api.pixellab.ai/mcp
  -t http -H "Authorization: Bearer <token>"` + session restart; async
  review/select workflows (`select_object_frames`).

## MCP surface: live-tested (2026-08-10)

The pipeline now speaks MCP directly (`tools/art_pipeline/mcp_client.py`
— JSON-RPC over streamable HTTP, stdlib only, same credential
resolution as REST, no Claude Code attachment or config-file
credential needed). Live findings:

- **65 tools** (docs undersold it). Directly relevant to the game's
  asset roadmap: `create_object_state`/`create_character_state`
  (variant states — oven glow, sign OPEN/CLOSED),
  `create_topdown_tileset` + `create_building_kit` (floors/walls),
  `create_ui_asset` (panels for newspapers/menus/ledgers),
  `create_portrait_character` (employee sprite ↔ portrait),
  `create_font`, `edit_image`, `create_image_pro`/`pixen`, object
  registry with tags, and an `inpaint_image` claiming "keeping
  everything else pixel-identical" — a stronger contract than REST
  /inpaint; scheduled for a controlled retest before any policy
  change.
- **Billing solved:** the account is a Tier 1 subscription with 2000
  generation credits/month — 69 used to date (includes the user's own
  web-creator sessions), cash balance $10.00 untouched. All spend
  reporting to date stands; the effective cost of our 50 charged
  calls was subscription credits, not cash.
- MCP generation tools are async (job id → poll `get_image`/`get_*`);
  `get_image` takes `job_id`. Smoke test passed end-to-end (32×32
  pixflux via MCP, seed 701, saved under experiment_03/raw/).

## Adopt-now rulings from the synthesis pass (2026-08-10)

The sequential-thinking synthesis audited the tree and found three
single-authority defects, now fixed: (1) pixflux — the 10-of-12-cell
winner — had no codified call path; `generate_pixflux()` now exists
beside `generate_bitforge()`, each carrying its policy role in its
docstring; (2) the pipeline README named bitforge as "the selected
operation" — corrected to point at this document's scorecard as the
single authority; (3) provenance schema v2 is defined in
`provenance.py` (`V2_REQUIRED`, `missing_v2_fields`, `attach_hashes`):
replayable params, output/input artifact sha256s, engine id,
validator_version, and a `donor_derived` flag that doubles as the
ship-time IP audit index. The REST client now retries transient
failures (never 4xx) and appends every charged call to a local spend
ledger (`PIXELLAB_SPEND_LEDGER`) so our record cannot silently diverge
from the vendor's.

Future MCP attachment ruling (P6): if the MCP is ever attached to a
Claude session, the bearer goes in via env expansion
(`Authorization: Bearer ${PIXELLAB_API_KEY}`, user scope, launched
with the var sourced from the Keychain) — never a literal token in
config, and any `.mcp.json` goes into `.git/info/exclude`. For
pipeline work, `mcp_client.py` already reaches the MCP surface with
no attachment at all, which remains the preferred path.

FLAGGED FOR USER (P5, licensing): generation inputs derived from Omega
donors (crops, scaffolds) make the outputs derivative works of a paid
asset pack whose included README carries no license text, and PixelLab's
ToS treatment of uploaded reference material has not been read. Before
the asset base grows large, the Omega purchase license and PixelLab ToS
should be read and the ruling recorded here. `donor_derived` in
provenance v2 indexes exactly which shipped assets would be affected.

## Final engine policy and process rulings (synthesis part 2, 2026-08-10)

**Engine matrix (adopted):** pixflux (REST) is the default for every
32×32-class prop/object/body — init anchor ≥2px margin, strength 120
(bodies) / 150–170 (donor-faithful), forced palette, 2–3 seed pool.
bitforge (REST) is narrow: same-object style variants only, style
image exactly output-sized. Cross-object family cohesion NEVER uses a
bitforge style image (proven leak). Brand geometry: code, frozen.
Masked edits: none (REST inpaint frozen out; MCP inpaint_image awaits
the P10 byte-exactness test). Pixen: deferred, trigger = first real
>400px single-shot need. Pro + style_copy: experiment-first, trigger =
first incoherent MIXED-family board (Exp-03's 8/8 was a semantically
close family and does not retire this trigger).

**Style-object registry: rejected for now.** A whole pizza has no
meaningful eight directions; a remote registered object would be a
second, unversioned, undiffable copy of canon on a vendor with no
changelog; and the registry rides the same style machinery that
leaked. Local PNG stays canon. Revisit only for genuinely
multi-directional subjects (employee, vehicle), after a leak test, and
then only as a derived cache.

**MCP: two-channel policy.** REST = production channel; MCP =
exploration + tileset channel (create_topdown_tileset /
create_path_tiles / create_building_kit have no REST equivalent and
map natively onto Godot 4 TileSet terrains). The invariant preventing
two authorities: nothing enters approved/ by ANY channel without
passing validate_candidate and writing a provenance v2 record — the
gate is the validator, not the transport.

**Tileability experiment (staged, kill criterion fixed in advance):**
Step 0 (0 gens): build the seam scorer and CALIBRATE IT on Omega donor
floor cells known to tile — instruments are proven before they judge.
Step 0.5 (0 gens): if the donor floor tiles, recolour it
deterministically to the chips — floors may need no generation at all.
Step 1 (~6 gens): pixflux 96×96 field, cut the best-scoring 32×32
window (interior continuity is plausible; self-wrap is not).
Step 2 (0 gens): mirror-fold fallback — self-tiling by construction.
Step 3 (MCP): Wang tileset, the structural answer to periodicity
salience anyway. Hard cap 12 generations / one session, then Wang.
Metric: palette-aware seam-vs-interior-column comparison (roll by
16,16), plus an eventlessness score; thresholds set by donor
calibration, never invented. **Conditional seam-fix post-passes are
REFUSED** (validation refuses, never repairs); unconditional
construction steps (quantize, NN reduce, brand layer, mirror-fold)
remain legal.

**Drift harness (blocked on provenance v2 backfill for old records;
new records already v2):** 4 probes — canon pizza seed 204, box_open
seed 602 (init path), one bitforge same-object variant, one
forced-palette conformance canary — run as the FIRST act of any
session that will spend generations (event-triggered, not calendar).
Three-tier verdict: A sha-equal = pinned; B within variance band =
note; C validator flip / off-palette / beyond band = FREEZE and
investigate. Tier-B thresholds must be calibrated by three same-day
repeats before any number is written here. Approved PNGs are ours
forever — drift threatens future consistency only; canon is NEVER
regenerated to "refresh" it.

**Metric relabeling (R3):** palette_adherence and quantize-zero are
hereby a VENDOR-CONFORMANCE CANARY, not evidence of art quality or
cohesion — color_image forces the palette server-side, so these checks
verify the vendor honoured a hard constraint. The decisive properties
(silhouette at device scale, value separation, cross-family cohesion)
remain human judgments at the review board. Family-cohesion scoring,
if ever built, is diagnostic-only — never a gate, never a target.

**Named risks (beyond R1 licensing, flagged above):** R5 — animation
tools bless only square 16/32/64 canvases; choose the employee sprite
canvas BEFORE generating any character. R6 — no asset has yet been
imported into Godot on a real device (filtering off, integer scale,
3× retina); the 50% check is a proxy. An isolated Godot import test
belongs early in the next phase, not late.

## Rev. 2 amendments (synthesis final, 2026-08-10)

The synthesis revised itself against the live MCP findings; deltas to
the rulings above, superseding where stated:

- **Two-channel policy SUPERSEDED.** With `mcp_client.py` in the
  pipeline, MCP is not a second channel but another endpoint family
  behind the same client, the same `validate_candidate` gate, and the
  same provenance v2 writer. One key, one gate; the invariant stands:
  nothing enters approved/ by any transport without validation + v2
  provenance.
- **P7 guard rail (recorded verbatim in spirit):** a working
  `inpaint_image` does NOT reopen the brand-layer policy. Deterministic
  lettering is justified on its own merits — exactly reproducible,
  editable without regeneration, drift-immune, free, legible by
  construction at 32px. The inpaint failures were the occasion for the
  policy, not its justification. Inpaint, if verified, is confined to
  non-brand variant work.
- **Pro ceiling arithmetic:** 2000 credits/month ÷ 20–40 = 50–100 Pro
  images/month; a 200-asset game at 3 candidates each ≈ 6–12 months of
  allowance via Pro vs under a third of one month via pixflux. The
  subscription quantitatively forbids Pro-as-default while making it
  free to evaluate as a specialist.
- **Promoted to experiment-now (free under allowance):** (1) Pro
  `style_copy` leak test on a semantically DISTANT pair — with the
  licensing constraint that inputs must be hand-blocked/clean until the
  Omega EULA ruling lands; (2) `inpaint_image` byte-equality probe,
  then head-to-head vs `create_object_state` for variant states.
- **New risk R3 — the allowance erodes discipline.** Use-it-or-lose-it
  credits supply a dishonest reason to generate. Standing rule: EVERY
  generation batch names the question it answers, recorded in
  provenance. Unspent allowance is the normal, healthy state.
- **Tool discipline (P15):** of 65 MCP tools, bless few; every blessed
  tool is a permanent drift-harness row. Portraits/UI, when they
  arrive, get their own validator contract — 32×32 prop rules do not
  transfer.
