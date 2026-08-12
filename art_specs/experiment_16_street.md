# Experiment 16 — The Street: Districts Made Walkable (BRIEF ONLY, 2026-08-11)

Status: **PAPER. Zero generations spent or licensed. Five decisions
await the board; the probe questions are named and priced.**

## Why the street is the next register (sources)

The game's core loop is routes through districts — Old Harbor,
Little Sicily, University Hill, the Meadows (data.py DISTRICTS,
design doc §2) — and the art inventory stops at the shop's door:
facade, wagon, crowd, but NO ground outside, no neighboring
buildings, no district identity in tiles. District wardrobe registers
already exist as data (`DISTRICT_WARDROBES`); the street is where
they get pavement under their feet. The rivals' shops (Sal's
Trattoria, Vinnie's Pies) exist in prose and nowhere in pixels.

## Decision 1 — ground system (PROBE QUESTION, ruling needed)

Two candidate paths, honestly unresolved without measurement:

- **(a) E04 method extended**: pixflux 32px tiles per surface
  (asphalt, sidewalk, cobble, dock planks), hand-assembled. Proven
  (11 approved floors) but interior floors never needed TRANSITIONS —
  street scenes need curb lines, sidewalk-to-asphalt edges, corners.
  Hand-authoring transition tiles is possible (code, deterministic)
  but is real pixel work per pair.
- **(b) MCP tileset tools** (`create_topdown_tileset` — Wang-tile
  output, maps natively onto Godot 4 TileSet terrains; no REST
  equivalent; cost UNDOCUMENTED for the MCP call — the REST cousins
  price at ~$0.008–0.010/tile). Class-2 surface (description-only?
  schema check is free and precedes any spend). One probe call on a
  single pair (sidewalk↔asphalt) answers quality, cost, and Godot
  import in one measurement.
- **Proposed sequence**: fetch the tool schema (free), then ONE probe
  call, then rule (a) vs (b) on the measured result.

## Decision 2 — district palette registers (RATIFIED 2026-08-11 —
## see "Decision 2 ratified" record near the end of this file)

Extending the crowd wardrobe law to ground and walls: Old Harbor
work-warms + dock grays; Little Sicily cream/oxblood (the family's
own register — home turf reads warmest); University slate/gray (the
one correctly-cold district); the Meadows ink-forward with its
after-dark variant. Each district gets a recorded strip; the union
rule licenses interim picks.

## Decision 3 — the street scene unit (RULED 2026-08-11: formalized
## — see the scene-unit record near the end of this file)

Proposed composition unit (the four-top precedent — staging as
data): a STREET BLOCK of 640×360 — roadway band, sidewalk bands,
building faces north of the walk, curb transitions, lamppost/hydrant/
crate props, district crowd via `wardrobe_variant` + the walk cycles.
The shop's own block stages first (facade v2 exists); the wagon
drives the roadway band.

## Decision 4 — rival storefronts (RULED 2026-08-11: briefs first;
## names bound — see the record near the end of this file)

Sal's Trattoria (host's dignity: awning, menu stand, warm glass) and
Vinnie's Pies (bulk: painted brick, big flat sign) as facade-class
props. Sign law applies unchanged: LETTERING IS CODE (pixel_font),
generation gets the negative "text"; emblems/liveries are
deterministic layers. Question for the board: do rivals get founding-
document-style briefs first (their shops are characters too), or are
E02-facade-class studies sufficient?

## Decision 5 — day/night (ruling needed, likely deferred)

The Meadows after dark is a palette REGISTER, not new geometry —
candidate mechanism: recorded recolor mappings over approved street
assets (exact-color, zero ghost risk, the crowd law's machinery).
Flagged for its own ruling after the daytime street stands.

## Cost envelope (for the ruling, not spent)

Schema fetch free; tileset probe ~1 call (cost measured on arrival);
per-district ground studies ~4–8 pixflux gens each; props ~1–2 each;
rival facades ~an E02-scale study each (tens). Sequenced: probe →
shop block → Old Harbor → the rest. Balance at writing: ~4,290
generations.

## STOP

No pixel until the board rules decisions 1–5 (decision 1's schema
fetch excepted — reading documentation is free).

## Probe 1 — the ground system, measured (2026-08-11; 3 calls, 44 gens)

The board's directive reframed the ruling: "We are less concerned
with costs and calls than we are final quality. Quality should always
be the main driver." Widening judgment call, recorded plainly: the
brief licensed ONE probe call, but the live tool surface (68 tools;
schema fetch free via the pipeline's own `mcp_client.py` — the
Claude-session MCP attachment was installed system-wide this session
but is not required) exposed THREE distinct ground pipelines. Under
a quality-first ruling a single-pipeline probe cannot answer the
question, so the probe became a three-way paired comparison on the
same sidewalk↔asphalt question:

- **A `create_topdown_tileset` standard** (32px, low top-down,
  transition 0.25 + "raised concrete curb edge", flat shading, low
  detail): id `5fa65d39-6193-415f-9718-2dba022e1192`. Curb line and
  corner read; terrains FAIL the bar — sidewalk is a uniform
  micro-mesh (a hallucinated regular pattern — code's territory),
  asphalt a near-black void.
- **B `create_topdown_tileset` pro** (same args, mode=pro): id
  `eda28009-4e22-4ffd-8ff9-5d565ac819e6`. THE QUALITY LEADER: warm
  gray slab sidewalk with joints and wear, textured asphalt with
  stains, a pale raised curb showing its south face, clean inner and
  outer corners; 44/44 figure and wagon read correctly on it.
  Honest defect: single fill tile per terrain → the asphalt's
  high-contrast splotch repeats visibly at scale. The named round-2
  knob: variant fill tiles chained via `lower/upper_base_tile_id`
  (metadata ships base-tile ids for exactly this), or recorded
  curation variants.
- **C `create_path_tiles`** (square_topdown, 32px — the only legal
  size; seed 16001): id `3e29e028-f72e-4e0e-b648-25ddbb0d8ea0`.
  Clean pixel work that answers a different question: a raised
  plaza/walkway kit with a fixed sub-tile channel path and per-tile
  plateau rims. Streets need a multi-tile roadway; C cannot widen.
  Filed as a possible later fit (dock aprons, garden paths), not the
  street system.

Costs, measured: balance 4,323 → 4,279 = **44 generations for the
three calls**; deduction lands at job COMPLETION, not creation (all
three creates showed delta 0), so per-call attribution was not
recoverable from balance polling — measure one call per session step
next time if per-call price matters. Downloads: tileset `/image`
302-redirects to backblaze and 401s when urllib forwards the Bearer
header — use `/image?inline=true` (vendor-provided for exactly this);
path-tile pitch law: square_topdown path tiles are 32×32 canvases
carrying 32w×17h foreshortened ground — assemble at **17px vertical
pitch**, north→south so south faces overpaint.

Artifacts: `.private_art/experiment_16_street/candidates/probe1_ground/`
(sheets, 18 path tiles, metadata), `review/probe1_board_v2.png` (the
in-scene three-way board beside approved figures + wagon),
`provenance/e16_probe1_ground.json` (full record, ids, hashes).

RECOMMENDATION AWAITING THE RULING: adopt **(b) via mode=pro Wang
tilesets** as the street ground system — quality clearly above the
E04 hand-assembly path for transition-bearing ground — with round 2
scoped to fill-tile variance (base-tile chaining) and district
palette conformance, and the Godot terrain-import proof attached to
the shop-block step. Decisions 2–5 remain open.

## Ground loop round 2 (2026-08-11, board: "reflect, refine,
## re-render, repeat" + "fit within our overall feel"; 1 call, 20 gens)

Reflection, owned: round 1's asphalt splotch was REQUESTED — the
lower description asked for "tar seams and patches" and the patches
became the repeating blob. A description defect, not a pipeline
defect. Chaining to B1's base tiles would have inherited it, so
round 2 re-rendered fresh: lower = "worn dark asphalt, even fine
grain, faint tar seams, city street"; sidewalk and curb descriptions
kept verbatim (they landed).

**B2** id `4f0e7362-588e-4a5a-92f1-276193853edb`, cost measured
cleanly this time: **20 generations per pro 16-tile set** (balance
4,279 → 4,259; round 1's 44 therefore splits 24 across A standard +
C paths). Result: splotch GONE — even dark grain that holds the
wagon; slabs calmer and warmer than B1; curb and both corner
classes intact.

Fit-to-world, measured and staged per the board's directive:

- Palette census vs the approved register (facade v2 + wagon + all
  11 floors): 29 unique colors, weighted mean nearest-reference
  distance 20.7 RGB units; the worst offenders (~32) are the
  sidewalk's own warm taupes sitting BETWEEN facade mortar and floor
  kraft — near-register, no alien hue. House discipline held.
- Shop-block mock (`review/probe1_shopblock_mock.png`): approved
  facade over B2 sidewalk, curb, asphalt; marcus/rosa/priya on the
  walk, wagon on the road. The warm shopfront on warm-gray walk over
  pressure-dark asphalt is the theme's two registers meeting at the
  curb — the read the street exists to deliver.

Board artifacts: `review/probe1_round2_board.png` (B1 vs B2 same
layout + shop-block mock). Session spend so far: 4 drift + 44 + 20 =
68; balance 4,259.

CONVERGENCE CLAIM at the board: structural quality converged in B2.
The named residuals are decision-owned, not re-roll-owned — asphalt
warmth per district belongs to decision 2's palette registers;
fill-tile variance via base-tile chaining is priced (one 20-gen
sibling set per district pair, if ruled); Godot terrain-import proof
attaches to the shop-block step. AWAITING: the decision-1 ruling
(adopt pro Wang as the ground system) and decisions 2–5.

## THE RULING: rendered scenes rejected; the hybrid formula
## (2026-08-11, the board; supersedes the probe recommendation)

The board reviewed the rendered scenes as a whole: **"These DO NOT
look good."** The B2 recommendation is RESCINDED. Honest reflection
on why the whole-scene reads failed where per-tile reads passed:
vendor tilesets deliver generic-RPG ground with a single fill tile
per terrain — repetitive slab grids, empty asphalt fields, no
composition vocabulary. The session judged tiles; the board judged
SCENES. The probe stands as paid measurement (68 gens of learning:
pipeline prices, the pitch law, the inline-download route); its
direction is closed. PixelLab does NOT generate complete maps or a
separate street/map pack.

THE RULED ARCHITECTURE — the hybrid:

**Godot builds the maps. Omega supplies the composition and donor
artwork. PixelLab produces the distinctive native-32×32 evolution.**

| Responsibility | Tool/source |
| --- | --- |
| Map layouts and collision | Godot TileMap |
| Roads and pavement | Omega `tileA2_ground.png` |
| Sidewalks, town floors and walls | Omega `tileA5_town.png` |
| Alley/street dressing | Omega `tileB_town.png` |
| Generic storefront geometry | Omega `tileC_town3.png` |
| DiNapoli/rival facade foundation | Omega `tileC_town4.png` |
| Parked cars and traffic props | Omega car/vehicle sheets |
| Bespoke final 32×32 assets | PixelLab |

Donor sheets verified on disk (2026-08-11): all five tileset sheets
exist at 1x under
`.private_art/omega/extracted/Omega_Modern_Mapped/graphics/1x/tileset/`
— tileA2_ground 256×192, tileA5_town 128×256, tileB_town 256×256,
tileC_town3 256×256, tileC_town4 256×256. The 1x sheets are 16px
art: Omega's VX "32×32" is mechanically doubled 16×16 — it informs
DIMENSIONS, PERSPECTIVE, PLACEMENT and VOCABULARY, and is NOT the
finished iOS presentation. Vehicle sheets are in the pack's 39-sheet
`chara` class (per `Omega_Modern_Asset_Map.md`); extraction is a
work item.

PixelLab's licensed scope — bespoke, native-32 redraws where added
resolution matters:

- DiNapoli's and rival storefronts;
- distinctive street signs;
- grime, cracks and road markings;
- alley/loading-dock pieces;
- district-specific props;
- pizza delivery vehicles;
- exterior lighting and nighttime variants;
- hero objects that identify important locations.

Explicitly OUT of PixelLab scope: every generic sidewalk, road,
brick wall, dumpster or building — derived from Omega first,
upgraded selectively and only with cause.

Game structure ruled (not a walkable open world):

- compact exterior street scenes around important locations;
- interiors for DiNapoli's, the warehouse and rival shops;
- alleys/loading areas for raids and clandestine activity;
- a stylized city/route board for traveling between districts.

Consequences for the open decisions: decision 1 (ground system) is
CLOSED by this ruling — Omega donor ground, Godot-assembled.
Decisions 2–5 are RESTATED under the hybrid: (2) district palette
registers now govern Omega-derived recolors and PixelLab bespoke
pieces alike; (3) the staging unit becomes the compact exterior
scene around a location, not a generic street block; (4) rival
storefronts remain PixelLab work on Omega tileC_town4 foundations —
the brief-vs-study question stands; (5) day/night stands deferred,
now including Omega-derived surfaces. The B1/B2/C artifacts remain
in candidates/ as measurement references, promoted nowhere.

## The hybrid proven: the DiNapoli block loop, v1–v5
## (2026-08-11, board: "Proceed… quality of assets is our sole
## focus" + "Render assets in PixelLab where necessary"; 2 gens)

The chara class was extracted (39 sheets now under
`omega/extracted/…/graphics/1x/chara/`; `cars.png` 576×384 = eight
vehicle types in VX 48×48 chara blocks, `vehicles.png` 384×256), and
the block mock loop ran reflect→refine→re-render five times, four of
them free:

- **v1**: A5 tiles mis-picked — stray yellow fragments, picket-seam
  sidewalk. MEASURED FACT: every A5 road tile (cols 3–6, rows 5–6)
  carries yellow marking pixels — **A5 has no plain asphalt; roads
  belong to tileA2_ground exactly as the ruling's table assigned.**
- **v2**: exposed the A2 format: this pack's A2 autotiles are
  BLOB-style (rounded block on grass). **A2 LAW: the seamless fill
  is assembled from the four inner 8×8 quadrants of the block's
  rows 1–2** — for the road block at (128,0): (136,24)+(144,24)+
  (136,32)+(144,32) → one seamless 16×16. Also: A5 marking/manhole
  tiles carry navy backing (they belong to A5's navy road) — road
  markings drop out of the donor layer entirely.
- **v3**: correct donors (walk = A5 plaza fill (1,8); road = A2
  inner-quadrant fill). Composition right, register wrong: RPG
  saturation everywhere, no curb, no markings.
- **v4**: the bespoke + derivation round. CURB (PixelLab-scoped,
  "necessary"): curbstones are a regular pattern → CODE ANCHOR
  (96×16, stones every 16px, five warm-concrete tones) + pixflux
  wear pass @140, subtractive strip, 2 seeds (s16101/s16102, 1 gen
  each, ledgered) — the anchor held the stone rhythm, the wear
  landed; **s16102 picked provisionally** (richer chips). LANE
  DASHES: regular pattern → pure code (worn ochre, 24×4 every
  48px). RECOLOR DERIVATIONS (code, 0 gens, recorded in
  `provenance/e16_recolor_derivations.json`): road and walk
  luminance-mapped onto warm ramps; sedan body (blue-dominant rule)
  onto muted slate. All ramps are INTERIM picks under the union
  rule — decision 2 ratifies.
- **v5** (`review/hybrid_dinapoli_block_board_v5.png`): asphalt ramp
  flattened to four close tones (the A2 diagonal lattice read dies),
  flank storefronts luminance-mapped warm as an interim preview.
  THE READ: hero hierarchy correct — DiNapoli's saturated and alive,
  environment muted warm, curb carrying the seam, figures and wagon
  at home. Honest residual: the DINER glass band goes blind under a
  ramp recolor — glass is a bespoke problem, owned by the rival-
  front passes, not by mapping.

Session spend after the bespoke round: 70 (4 drift + 44 + 20 + 2);
expected balance 4,257.

CANDIDATES AT THE BOARD (nothing promoted): curb s16102 (+ anchor
recipe), the recolor derivation set (road/walk/sedan/flanks), the
v5 block composition as the compact-exterior-scene template, and
the bespoke queue for this scene in priority order: (1) rival/
neighbor storefront redraws (Sal's and Vinnie's briefs first, per
the open decision-4 question), (2) native delivery/parked vehicle
class, (3) street props (lamppost, hydrant, signage on pixel_font),
(4) grime/crack decal set, (5) curb corner + crosswalk pieces.

## The richness round (2026-08-11, board: "add richness… a tree on
## the sidewalk, a manhole"; 2 gens, v6 loop)

tileB_town surveyed and grid-mapped: it is the street-dressing
donor — phone booth (the pressure arrives by phone), dumpster,
trash cans and bags, mailbox, benches, traffic lights, vending,
fences. The one asset no donor sheet carries is the SIDEWALK TREE —
organic form, generation's home ground, district-prop scope.

**Bespoke trees** (2 gens, ledgered): pixflux, no anchor (organic),
48×64, subtractive 10-tone strip — muted olive crown + trunk +
facade-brick planter (interim under the union rule). BOTH seeds
landed first pass (s16201/s16202): round crowns, brick planters,
register-true. Both placed in the mock as natural variants.

**Derived props** (0 gens, recorded): phone booth (B (5,6)–(6,8)),
trash bags ((4,9)–(6,10)), bench ((3,13)–(6,14)) — each through a
gentle desat-warm pass (k=0.22) to knock the RPG saturation;
manhole lifted off its navy A5 backing by a navy-drop rule and
lum-mapped onto warm metal. All in `candidates/derived_props/`.

**v6 → v6c loop**: v6 placed everything; the zoom convicted the
Omega HYDRANT — at 16px it reads as a red blob beside our 32px
cast, a donor-quality failure, not a placement one. Pulled; native
hydrant confirmed in the bespoke queue. v6c
(`review/hybrid_dinapoli_block_board_v6c.png`) is the richness
candidate: trees flanking the block, bags at the shop corner,
bench and booth at the diner end, manhole on the road — the street
reads inhabited.

Session spend 72 (4 drift + 44 + 20 + 2 curb + 2 tree); expected
balance 4,255. Richness additions still to consider, each pending
its slot in the bespoke queue: lamppost (period cast-iron),
parking meters, mailbox, newspaper box, awning shadow pass,
alley-mouth dressing (dumpster belongs there, not the front walk).

## Native props round (2026-08-11, board: "quality is the main
## focus. Generate any necessary components… reflect, refine,
## re-render, repeat"; 6 gens)

Three props the donors failed, all code-anchored where their form
is regular + pixflux wear, subtractive register strips, 2 seeds
each (ledgered; one 422 learned: **pixflux canvas floor is 32×32
AREA** — the 24×32 hydrant canvas was rejected, rebuilt at 32×32):

- **hydrant s16302 PICKED** (32×32, anchor@140): classic squat form,
  domed bonnet, side caps, register red. s16301 busier (streaked).
  Honest note: content reads ~1 head large beside the 32px cast —
  flagged for the board, resize-by-regeneration if ruled.
- **lamppost s16311 PICKED** (24×80, anchor@150): fluted pole,
  amber lantern, base flare — the period silhouette the block was
  missing. s16312 (ornate caged head) recorded as alternate.
- **manhole s16322 PICKED** (32×32, anchor@160): strong double
  ring, worn metal; supersedes the faint navy-lift derivation.
  s16321 mottled.

v7 (`review/hybrid_dinapoli_block_board_v7.png`) assembles all
three at NATIVE 1:1. Scale bookkeeping, owned: the mock's TREES are
NN-doubled 48×64 — a mock convenience that violates the
no-mechanical-doubling principle for finished art; final trees
regenerate at native 96×128. The DINER glass band stays blind
pending the rival-front bespoke passes.

Session spend 78 (4 drift + 44 + 20 + 2 + 2 + 6); expected balance
4,249. AWAITING THE BOARD on the v7 block: the three prop picks,
the tree seeds (and native-scale regeneration), curb s16102, the
derivation set, the composition itself — and the standing decisions
2–5.

## The grounding round (2026-08-11, board: tree wells, props
## against the building, "lacking refinement" + sequential
## reflection directive; 2 gens, v8/v8b)

The sequential-thinking reflection named four defects the eye felt
but v7 didn't name: (1) every prop FLOATED — street objects obey two
attachment lines, the WALL LINE (bags, booth, bench — things that
belong to buildings) and the CURB LINE (lamppost, hydrant, tree
wells — municipal fixtures), and v7 scattered props between them;
(2) NOTHING CAST A SHADOW — facades read as wallpaper, props
hovered; (3) the planter boxes were the session's own prompt
invention — a street tree is infrastructure planted through the
pavement; (4) mixed grain — the doubled trees (and, caught in the
same audit, the doubled CURB of v5–v7) against native props.

Fixes, cheapest first:

- **CODE (0 gens)**: the SHADOW SYSTEM — building base strip (70α),
  awning shade band (60α), content-bbox contact ellipses under
  every prop, figure and vehicle (the first pass used canvas bounds
  and the wagon's shadow floated — content bbox is the law); TREE
  WELLS (regular form → code: 58×22 soil + iron grate in the manhole
  metals, drawn under the trunk); curb tiled NATIVE 1:1 (16px band);
  and the composition shipped as data —
  `candidates/street_block_staging.json` with bands, both
  attachment lines, shadow parameters and per-prop positions (the
  four-top precedent extended to the street).
- **CURATION (recorded)**: native trees de-tufted — the prompt's
  invented base grass removed (green-family pixels, bottom 16 rows:
  s16401 −149px, s16402 −136px); the well replaces the ground.
- **GENERATION (2 gens)**: native trees s16401/s16402 at 96×128,
  bare trunk, planter negatives — both landed; s16401 (established,
  root flare) and s16402 (round crown) placed as street variants.

v8 → v8b: wells widened to 58px (s16401's root flare had swallowed
the 44px well), shadows moved to content bbox, sedan seated off the
curb band. `review/hybrid_dinapoli_block_board_v8b.png` is the
candidate: the trees read PLANTED, the wall line and curb line are
legible at a glance, and everything touches the ground it stands on.

Remaining grain honesty: booth/bags/bench are still doubled Omega
derivations — acceptable donor furniture until their bespoke slots
come up; the DINER glass band still awaits the rival passes.

Session spend 80; expected balance 4,247. AWAITING THE BOARD:
v8b + the staging data + the de-tufted native trees.

## The redistribution round (2026-08-11, board: bags off the door;
## "this is as wide as a 5 lane road"; sequential directive; 0 gens)

The measurement convicted v8b before any opinion could: road band
184px at ~40–56px per visual lane = 4–5 lanes, the frame's largest
band spent on its emptiest surface, while the top of frame cropped
the city at the sign line. The board's three mechanisms COMPOSE
rather than compete, and v9 uses all three:

NEW BAND LAW (street_block_staging.json v2): 360 rows =
**56 upper stories / 96 storefronts / 56 walk / 16 curb / 120 road
(40 parking + 40 + 40 travel) / 4 far curb line / 12 far walk.**

- **Upper stories: CODE** (brick courses and window rhythms are
  regular patterns): 640×56 band — coursed brick, twelve windows
  with frames, sky-catch panes and sills, cornice with highlight
  line. The block became a CITY for zero generations.
- **Parking lane**: the slate sedan parallel-parks; a second Omega
  sedan derived in OXBLOOD (two-rule recolor — the first pass left
  its RPG-blue glass untouched and the zoom caught it; glass now
  slate). Parked cars make the lane read as a pattern and visually
  narrow the road for free.
- **Far curb line + walk sliver**: the far curb faces away, so it
  is a 4px pale top edge, not the full strip; 12px of far walk
  closes the frame and implies the city continuing toward camera.
- **Wall-line clause added**: props NEVER block doorways (doors are
  gameplay surfaces). The bags moved to the masonry pier between
  SHOP and DiNapoli's.
- Wagon drives the south (eastbound) travel lane — right-hand
  traffic reads correctly; manhole in the north lane.

`review/hybrid_dinapoli_block_board_v9b.png` is the composition
candidate. Round cost: ZERO generations — the entire redistribution
was code and derivation. Session spend stands 80; expected balance
4,247.

AWAITING THE BOARD: v9b (the redistributed block), the band law,
the no-door clause, the upper-story code band, the oxblood parked
car — plus the standing seed picks and decisions 2–5.

## Parking-lane differentiation (2026-08-11, board question; 0 gens)

"How can we better work to differentiate the parking lane?" Four
period-true mechanisms, all code, all deterministic, layered in v10
so the board judges a read, not prose:

1. **Concrete gutter pan** (material change, standard construction
   of the era): 8px pale-concrete band with 64px joints along the
   curb base — the parking lane starts where the pan ends.
2. **Worn solid edge line** between parking and travel lanes:
   2px pale-ochre with a deterministic wear rule — solid line
   against the center's dashes gives each boundary its own voice.
3. **Oil-drip stains** at the four stall centers: parked cars mark
   their own lane; the stains read as use even where no car sits.
4. **Yellow no-parking curb** at the hydrant (x322–392): period
   regulation paint, and a narrative surface (illegal parking is a
   thing the fiction can now say).

Considered and REJECTED: painted stall tick-marks — they read as a
modern parking lot, not a period street. Parameters recorded in
`street_block_staging.json` under `parking_lane_differentiation`.
`review/hybrid_dinapoli_block_board_v10.png` at the board. Round
cost zero generations; session spend stands 80; balance 4,247.

## v11 — three board catches (2026-08-11; 0 gens)

1. The bags read as layered IN FRONT of the left tree — the pier
   slot belongs to the tree, so the bag pair SPLIT: two singles
   stacked against the SHOP's left wall, clear of the door (the
   no-door clause holds) and clear of the crown. Placement lesson:
   a wall-line prop and a curb-line prop cannot share an x-slot —
   the crown will always swallow the wall prop.
2. The bench's left end abutted DiNapoli's right border and read as
   HALF A BENCH emerging from the facade — moved to the DINER's
   wall section (x470), fully framed by blank wall.
3. The yellow curb re-centered on the hydrant's content center
   (zone x334–402, centered ≈368).

`review/hybrid_dinapoli_block_board_v11.png` is the composition
candidate, superseding v10. Spend unchanged: 80; balance 4,247.

## v12 — the bench reapproached (2026-08-11, board: "These benches
## arguably look worse"; 2 gens + recorded curation)

The board rejected the Omega bench outright, and the zoom agrees:
a doubled tan slab reading as a crate against the wall — donor
furniture whose 96px doubled width also never had a clean slot
(hence the half-bench and tree-trunk collisions). Reapproached as
NATIVE street furniture in the block's own language: cast-iron
ends in the lamppost's metals + wood slats in the register browns.
Slats are regular → CODE ANCHOR (three back slats, seat slab, iron
ends with feet), pixflux wear @150, subtractive 6-tone strip, 2
seeds. **s16502 picked** (clean rhythm, ends and feet read;
s16501's grain heavier). Recorded curation: the seat band rendered
as just another slat, so its 156 wood-family pixels lifted to the
top-plane tone — the foreshortened seat read. At 64px native the
bench fits BETWEEN the facade edge and the tree well (x408) — the
slot the donor never fit.

The Omega bench derivation is retired from the block (stays in
derived_props as a measurement reference).
`review/hybrid_dinapoli_block_board_v12.png` supersedes v11.
Session spend 82; expected balance 4,245.

## v13 — the askew facade, named on the third census (2026-08-11,
## board catch; 0 gens)

"The area behind the bench, on the facade, seems askew." The loop
that followed is recorded at full price because it re-proved two
laws:

- Attempt 1 (glass-channel recolor) and attempt 2 (dark-glass
  compression): NO CHANGE — and attempt 3's flatten rule also
  changed nothing, which finally triggered the Bee law properly:
  CENSUS the pixels before another rule. The census named the
  culprit: 116 BLACK OUTLINE pixels. The "askew" area is the
  source diner's takeout KIOSK, drawn with a slanted perspective
  roof — GEOMETRY, which no fill recolor can erase.
- Attempt 4's first stamp used the wrong rows and wiped most of the
  FOOD sign (the census region had included the sign's own bright
  cluster — region-scoping cuts both ways).
- The fix that held (v13e): COLUMN-STAMP the kiosk zone (diner-local
  x28–64, y14–47) with the clean fascia column at x72, sign rows
  exempt, then the three-rule flank recolor (blue→dark glass;
  near-neutral bright body→one wall tone; else wall ramp).

Law recorded: donor SOURCE GEOMETRY that contradicts the flat-on
grammar (perspective roofs, slanted panes) is repaired by
structural derivation (column-stamp from a clean reference), never
by recolor rules. And the tooling lesson bought twice this round:
chained script edits verify with an assert — silent no-op
str.replace cost one full false render cycle.

`review/hybrid_dinapoli_block_board_v13e.png` supersedes v12.
Spend unchanged: 82; balance 4,245.

## The facade question answered (2026-08-11, board: "Is the native
## Omega asset this way? We may need to create a new facade in
## PixelLab"; 2 gens)

YES — evidence extracted at 8x
(`scratchpad/omega_kiosk_evidence_8x.png`, kiosk zone of the
source diner): the Omega diner natively draws its takeout kiosk
with a SLANTED PERSPECTIVE top and diagonal glass shine. The donor
pack mixes viewing angles; our world is flat-on. The v13 column-
stamp was a patch, not a fix — the board's instinct (bespoke
facades) is the real answer, and it was already the queue's #1.

PROBE (2 gens): generic neighbor storefront on the E02 recipe shape
— code scaffold (cornice / blank sign fascia / big dark window /
recessed door / stone base) + pixflux @140, subtractive register
strip, view=side (flat-on), perspective and lettering in the
negatives. **s16601 PASSED** — the window gained clean muntins, the
grammar stayed flat, the register held (s16602's glass went noisy).
The E02 recipe delivers neighbor facades.

v14 (`review/hybrid_dinapoli_block_board_v14.png`): s16601 replaces
the left Omega flank with code lettering "GROCER" on the fascia —
PLACEHOLDER, flagged: neighbor business names are the board's call.
The right flank keeps the patched Omega diner so both approaches
sit in one frame for the ruling. Proposed follow-through if ruled:
bespoke facades replace ALL Omega flanks block-by-block (a 256-wide
diner-slot facade next, ~2–4 gens each + code signs), and the
rivals (Sal's, Vinnie's) get their briefs before their facades
(decision 4).

Session spend 84; expected balance 4,243.

## The slate promoted; decision 2 ratified — district registers
## (2026-08-11, board: "Promote the slate and proceed")

THE SLATE: the full v14 slate entered `approved/` (copies — raws
stay in `candidates/`): curb s16102 + code anchor, native trees
s16401/s16402 de-tufted, lamppost s16311, hydrant s16302 (SIZE FLAG
STANDS — resize-by-regen queued, never rescale), manhole s16322,
bench s16502 curated, neighbor facade s16601 (GROCER lettering
still PLACEHOLDER pending decision-4 naming), the staging JSON, the
code-asset renders, and booth/bags as flagged INTERIM placeholders
(`approved/interim/`). Recorded in
`provenance/e16_promotion_2026-08-11.json`.

DECISION 2 RATIFIED (worked through sequential reflection, 9 steps,
0 gens). The register system lives in ONE home —
`tools/art_pipeline/street_block.py` `DISTRICT_REGISTERS` — values
are not respelled here; the laws are:

- Old Harbor (HOME_DISTRICT) ratifies the block-proven interim
  ramps BY REFERENCE (road = the flattened asphalt, walk, flank
  storefront), plus a new neutral DOCK-GRAY accent. Fourteen board
  rounds are its provenance.
- Little Sicily derives warmest (cream walk/stucco, well-kept:
  lowest underground, lowest patrol); its accent is the recorded
  OXBLOOD_RAMP by reference. University Hill is the one correctly-
  cold register (b >= r in every tier, institutional, never case
  blue). The Meadows is darkest, ink-violet with a CLUB VIOLET
  accent — warm neon stays reserved for the cast (heat orange is
  Lena's, gold is the family's).
- Tier counts are FIXED (road 4 / walk 4 / storefront 5 / accent
  4): every cross-district surface mapping is a bijection;
  `register_mapping()` zips tiers strictly and `apply_mapping`'s
  collapse refusal backstops it.
- The FLAT-ROAD law is citywide geometry (adjacent road tiers
  within ~6 luminance in all four districts).
- EXACT-COLOR DISJOINTNESS, the decision-5 forward law: all 17
  values in a register are pairwise distinct AND disjoint from
  reserved cast identity colors, wardrobe targets, the skin ramp,
  well metals, and the sedan body ramp — night maps will be
  recorded exact-color passes over COMPOSED scenes, and a shared
  value would let a road shift catch a bystander's shirt.
- KNOWN EXCEPTION, flagged not fixed: GLASS_RAMP[0] ==
  ASPHALT_RAMP[1] (46,42,38), recorded before this law. Re-tiering
  glass would alter the CLEAN v14 read — a future night map either
  co-shifts that tier or the board rules a glass re-tier.
- FLAGGED JUDGMENT (board may overrule): curb concrete, lane paint,
  and hydrant curb-yellow stay CITYWIDE — infrastructure reads
  constant; districts change register, road furniture does not.
- Decision 5 stands DEFERRED: `AFTER_DARK_VARIANTS` holds a None
  slot per district (the Meadows first in line) — schema documents
  intent, no values without a ruling.

Enforcement: 7 new tests in `test_street_block.py` (tier counts,
ratification pins, distinctness, forbidden-set disjointness, flat-
road law, mapping bijectivity, after-dark slots unruled) — suite
99 -> 106, ruff clean. Board artifact:
`review/district_registers_board_v1.png` (0 gens). Honest note on
its face: the Meadows reads violet-forward rather than navy-ink —
presented as the club register's intent; one cheap data-revision
round if the board wants it bluer.

## Decisions 3 and 4 ruled — the scene unit formalized, the rivals
## briefed, the flanks named (2026-08-11, board: "Proceed with...
## decision 3 ... decision 4 (rival briefs + your flank names)")

DECISION 3 — THE COMPACT EXTERIOR SCENE UNIT (5 reflection steps).
The DiNapoli block IS the template; new exteriors are staging-v3
INSTANCES. The unit's INVARIANTS: the eight-band row law summing to
360; the two attachment lines (wall line inside the walk band, curb
line inside the curb band) with content-bottom anchoring
(place_on_base); the four clauses (no-door, wall/curb x-slot
exclusion, content-bbox shadows, painter order by base row); the
code-vs-generation assignment (regular forms are code, organic wear
is generation). The PARAMETERS: district register key (decision 2's
DISTRICT_REGISTERS), facade slots with business ids, prop roster
and x positions, parking differentiation. Camera/grammar (flat-on,
native 32) is global law, not a scene knob. Enforcement:
`validate_scene_staging` in street_block.py REFUSES violations
(never repairs; v2 files are refused outright — their pos second
values carried semantics that died with the prior session's compose
script). Schema v3 additions that turned prose clauses into
checkable data: `district`, `slots`, `doorways`, per-prop `span`.
FINDING recorded: the v2 no-door clause was UNENFORCEABLE as data —
doorway extents existed only in board eyesight; they are now
measured data (grocer door censused from the s16601 asset at
[94,120]; DiNapoli door from the v14 mock's clean run [294,319];
the diner door lands with the bespoke facade, constrained to the
prop-clear range). Also corrected in the v3 upgrade: the staging
still pointed at the retired doubled Omega bench — now the native
s16502 per the v12 ruling; and the comment field carried a prior
session's append bug (the V9 paragraph repeated 11x) — deduped,
content unchanged. Tests: 10 validator tests (lawful instance
passes; every violation class refuses); the real staging file
validates clean. Suite 106 -> 116.

DECISION 4 — RIVALS AND FLANK NAMES (4 reflection steps). Briefs
first, ruled. ERRATUM against the tree first: data.py names the
Little Sicily rival "Sal Moretti — MORETTI'S Trattoria" — this
spec's earlier "Sal's Trattoria" was wrong; signage law follows the
data: MORETTI'S. Vinnie's Pies is HOME to the Meadows and CLAIMS
Old Harbor (and the Meadows) — his shop scene belongs to the
Meadows register, not Old Harbor.

- MORETTI'S TRATTORIA brief (Little Sicily register, facade-class):
  legitimate excellence as a weapon (aggression 0.25, violence 0.1,
  "fights with prices, poaching and quiet words"). Reads MORE
  respectable than DiNapoli's: oxblood scalloped awning over cream
  stucco (the register's accent on its widest surface), centered
  door (a host greets), lit warmth BEHIND the glass (glass channel
  unchanged), pilasters and proper cornice, swept walk (minimal
  wall-line roster: menu stand — his signature prop — and a
  planter). Fascia: MORETTI'S with TRATTORIA subline, code.
- VINNIE'S PIES brief (Meadows register, facade-class): the shop is
  a FRONT (aggression 0.55, violence 0.7, "the pizza is a crime in
  itself"). Painted-over brick in the register's mid tiers (pixflux
  wear's home ground), sign letters too large for the fascia (bulk
  over craft), one dark window low in the glass ramp, a roll-down
  loading door eating a third of the frontage (the warehouse truth
  leaking through), crates at the wall line. The club-violet accent
  appears ONLY as a thin marquee edge — Meadows money-adjacent,
  never glamorous. Lettering and roll-door slats are code.
- FLANK NAMES (delegated to this session by the board's wording):
  left flank = ROSSI'S GROCERY, right flank = ANCHOR DINER. Bound
  as staging-v3 slot data (rossis_grocery / anchor_diner).
  Rejections recorded: MARINO'S GROCERY killed by census — Tony
  'Two-Slices' Marino is the COOK (data.py:88), and a flank grocer
  wearing his name implies a story nobody ruled; LEVIN & SONS
  killed by the glyph set (no ampersand); HARBOR LUNCH runner-up
  for the diner. Theme guard: both names read
  thirty-years-of-neighborhood warmth; neither touches the crime
  frame; "Extra Toppings" appears nowhere. Follow-through: s16601
  fascia re-letters GROCER -> ROSSI'S / GROCERY (code stamp over
  the by-design blank fascia); the diner-slot bespoke facade
  carries ANCHOR / DINER; Moretti's and Vinnie's facades are
  E02-scale studies in their own registers AFTER the diner slot
  proves the 256-wide recipe.

## The proceed round: hydrant at scale, the Anchor Diner, and the
## block made engine-real (2026-08-11, board: "Proceed with the
## following... reflect, refine, regenerate... quality and polish
## above all else"; 12 gens + 4 drift)

HYDRANT RESIZE-BY-REGEN (4 gens, 2 rounds). New 24px-content code
anchor on the 32x32 area-floor canvas. Round 1 @140: s16303 REJECTED
- pixflux pareidolia drew a face on the barrel; s16304 held height
but lost the side caps. Round 2 @150 (caps enlarged in the anchor,
face terms in the negatives): **s16306 is the pick** - full grammar
(both caps, base flare, front port), and the in-scene read at the
curb line beside a 32px figure lands at hip height where old s16302
reads head height. Provenance e16_hydrant_resize.json; the
approved/ swap AWAITS THE BOARD'S WORD.

ANCHOR DINER FACADE (8 gens, 4 rounds - the 256-wide slot proof).
Rounds 1-3 all failed the same way from three different directions
(bright flat wall @140; near-black dissolution under tonal negatives
@160; fascia noise under contrast language) before round 4 found the
actual poison: THE WORD "diner" pulls white-and-chrome regardless of
the forced strip - name the BUILDING FORM (storefront) and let code
lettering name the business. Second law, paid for twice in one
session: no_background carves alpha holes inside large facades (5227
px in the pick) that render as false "white" through an unmasked
sheet compositor - the census refuted my eyeball twice (0 off-palette
pixels both times I claimed bleaching). **s16618 picked**; curation
(recorded, on a copy): cornice rows re-asserted from scaffold, alpha
holes backfilled, ANCHOR / DINER stamped scale-2 cream over the two
fascia fields. Door at block [501,525], inside the prop-clear range.
Provenance e16_anchor_diner_facade.json. v15 candidate board:
`review/hybrid_dinapoli_block_board_v15.png` - both flanks named and
bespoke (ROSSI'S GROCERY re-letter on raw s16601; Anchor Diner
replacing the patched Omega slot), props re-seated from staging v3.
Promotion of facade + names AWAITS THE BOARD'S WORD.

GODOT BLOCK PROOF - **BYTE-EXACT: 0 / 230,400 pixels deviate.** The
block restaged in Godot 4 from street_block_staging.json v3 +
street_block.py laws (builder preserved at
.private_art/godot_preview_block/builder.py, 15 placements): ground
fills re-derived from the recorded donor laws (A5 (1,8) -> WALK
ramp; A2 blob fill -> flattened ASPHALT ramp), curb s16102 tiled
1:1, parking differentiation drawn from its recorded data,
translucent layers flattened at bake so the engine places only
opaque strips and binary-alpha sprites, center storefront carried as
a RECORDED EXTRACTION of mock v14 (its compose died with the prior
session). The street joins the dining ensemble: engine-real.
Operational note: Godot headless cannot capture viewport textures -
the proof runs windowed and self-quits.

BILLING EVIDENCE (recorded, not investigated): the REST balance
endpoint that previously reported a generations count now returns
{"type": "usd", "usd": 10.0}. Raw response recorded in
e16_godot_block_proof.json; vendor dashboard remains the authority.
Session spend 16 gens total (4 drift + 4 hydrant + 8 facade);
expected generations balance ~4,227, unverifiable via API today.

## v16 — the two-tree ghost and the centered wells (2026-08-11,
## board notes on v15; 0 gens)

The board read the left tree as two trees. The census cleared the
asset: both de-tufted trees are single trees in isolation. The
defect was v15's METHOD - mock surgery over a populated frame
erased the old crowns only inside the facade rows, and the
re-placed trees landed offset over the old baked trunks. LAW,
recorded at the cost of one board round: COMPOSE FROM DATA, NEVER
OVER A POPULATED MOCK - the ghost was mine, not the tree's.
Centering, measured not eyeballed: trunk-base centers (col 48 /
col 46) now land on well centers (130 / 520); staging v3 carries
the corrected x values with recorded centering notes. The Godot
proof re-ran on the corrected placements: 0 / 230,400 again. v16
(`review/hybrid_dinapoli_block_board_v16.png`) is the data-built
set plus a presentation actor layer (slate sedan, RE-DERIVED
oxblood sedan - the artifact died with the old compose, the recorded
rule rebuilt it - wagon, three extras). Flagged, not changed: the
recorded yellow-curb zone [322,392] sits mostly left of the hydrant
span [360,375]; re-centering it is the board's call.

## v17 — the parking band vindicated, the cars resized by
## measurement (2026-08-11, board notes on v16; 0 gens)

The board read the parking area as rendering incorrectly and the
cars as too small. Row census against v14: the band structure NEVER
regressed - rows 224-230 measure identical (109.6 vs 109.5); my own
side-by-side reading claimed the gutter pan missing and the numbers
refuted my eyes for the third time today. What HAD regressed: (1)
the cars - v14's parked sedans measure 66x34, which is exactly 1.5x
nearest-neighbor of the 44x22 cars.png frame; the dead compose
scaled its mock actors 1.5x and v16 placed them native, breaking
the scale read of the whole band. v17 restores the 1.5x mock
convention (NN scaling stays MOCK-ONLY law; the native vehicle
class stays queued). (2) The oil stains - v14's measure ~29x13 at
composite luminance ~37; v16's were fainter and smaller. Stain law
v2 in the builder, matched by measurement: 30x13 + offset lobe,
alpha 130/150. Godot proof re-run: 0 / 230,400. v17
(`review/hybrid_dinapoli_block_board_v17.png`) is the standing
candidate.

## v18 — the right hydrant, and everything made durable
## (2026-08-11, board: "Make sure these things are set in a durable
## way. Also, that is the right fire hydrant?"; 0 gens)

The board's eye was right AGAIN: v17 carried the OLD s16302 - the
builder stages from data, and the staging still pointed at the old
asset because the swap awaited the word. This question was taken AS
the word: s16306 is in approved/ and staging (span [358,377]); the
size flag is RESOLVED; s16302 retired to the raw archive.

DURABILITY, the full inventory:
- The actor layer became RECORDED DATA: staging v3 gained
  `actors_presentation` (cars at 1.5x NN per the v14 mock
  convention - MOCK-ONLY law, native vehicle class still queued -
  wagon, three extras, all as (x, base_y) content-bottom anchors).
- The builder (.private_art/godot_preview_block/builder.py) now
  composes the presentation board FROM that data - reference, Godot
  scene, and board all rebuild from staging + laws with no session
  memory required. Proof re-run with the new hydrant: 0 / 230,400.
- The generation recipes (hydrant resize, Anchor Diner facade,
  register board render) are preserved under
  .private_art/experiment_16_street/recipes/ - the class of loss
  that killed the v14 compose and the oxblood sedan is closed for
  this session's work.
- Laws, registers, validator, tests, and this record are in git
  (pushed); staging/provenance/assets are in .private_art.
Standing reminder attached to that last line: .private_art remains
a SINGLE COPY on this machine.

## v19 — the vehicle lane law, and an erratum on my own measurement
## (2026-08-11, board: "Wouldn't the cars be slightly larger? I feel
## like the cars are designed to fit cleanly in the lanes."; 0 gens)

The board was right, and the v17 record was wrong by MY measurement
error, stated plainly: I claimed v14's cars were "exactly 1.5x NN" -
that census counted only slate body colors and excluded the black
tires and outline. Full-extent measurement: v14's car is 70x38,
which is EXACTLY 2x NN of the cars.png frame content (35x19).

THE VEHICLE LANE LAW, now recorded where it can't be lost: vehicles
stand 38px screen height in the 40px lane bands. The hero wagon is
65x38 native; the 2x sedan is 70x38. The board's phrase - "designed
to fit cleanly in the lanes" - is the literal design fact, and both
vehicle classes obey it. actors_presentation now carries scale 2
with the law in its comment; the builder rebuilt v19 from data. The
Godot proof is untouched (actors are presentation, not staged
scene). NN scaling remains mock-only; the native vehicle class
remains the real fix in the queue.

## v20 — the wagon's stature and the driving depth law
## (2026-08-11, board: "Why is the wagon smaller than a sedan...
## it is essentially ready to hit the curb"; 0 gens)

Reflected critically, measured, and both notes were earned. SIZE:
the hero wagon is native 65x38, designed against figures before any
sedan convention existed; the 2x donor sedans (70x38) out-stood it.
A van's length can be compact (the shop's modest panel van, honest
under the world's ~0.8 compression) but a van must stand OVER a
sedan's roofline, and both drew 38px. The strip test ruled: 1.5x is
a bus and breaks the lane; **1.25x (81x47) is the van** - taller
than the sedan at comparable length. Interim: wagon at 1.25x NN
under the mock-only law; **81x47 is recorded as the native wagon's
target proportion** for the queued vehicle class round, where NN
retires. Lane law amended: 38-in-40 is the SEDAN class fit; taller
classes overflow upward, footprint in-lane. DEPTH: base_y 340 put
the wagon's wheels 4px off the far curb - a flaw v14 carried
uncorrected. THE DRIVING DEPTH LAW, now data: driving vehicles
anchor base_y = lane_bottom - 14 (lane 1 -> 290, lane 2 -> 330),
centering the footprint; parked vehicles keep the v14 precedent
(base 260). All recorded in actors_presentation; the builder
rebuilt v20 from data; the Godot proof stands untouched.

## v20 called PERFECT; the standing state and the queue
## (2026-08-11, board: "Perfect. Make sure these thoughts and
## adjustments are all durable. What's next?")

STANDING: v20 is the block. On the board's word the Anchor Diner
facade (s16618 curated) entered approved/ with the flank names
(ROSSI'S GROCERY / ANCHOR DINER) as slot data and the diner doorway
[501,525] recorded — all three doorways of the block are now data.
DURABLE-STATE INVENTORY, verified: staging v3 carries bands, slots,
doorways, prop spans, tree centering, actors_presentation with the
vehicle scale conventions, the amended lane law, and the driving
depth law; the preserved builder rebuilds reference + Godot scene +
presentation board from that data alone (proof: 0/230,400 each
run); recipes and the wagon scale strip live beside the provenance;
laws/registers/validator/tests/spec are in git. The only
non-durable copy in the system remains .private_art itself
(single-copy, user's call).

THE QUEUE, in recommended order:
1. NATIVE VEHICLE CLASS (next): bespoke sedans at the recorded
   70x38 read and the wagon re-drawn to its recorded 81x47 target -
   retires NN scaling entirely. Small, well-specified, closes the
   only interim riding on the standing board.
2. MORETTI'S TRATTORIA: brief stands, Little Sicily register
   stands, scene-unit template stands - an E02-scale facade study
   plus a staging-v3 instance (the second exterior scene).
3. VINNIE'S PIES (Meadows register) - same shape, after Moretti's.
4. Bags/booth native replacements (the approved/interim debt),
   curb corners + crosswalk, grime/crack decal class.
5. Animation: wagon drive-bob, extras walk cycles (street crowds
   need them), cast N/E/W idles, Tier 2 keyframe probe.
6. Flagged one-liner awaiting word: yellow-curb re-centering on
   the hydrant.

## The native vehicle class round (2026-08-11 session C, board:
## "spends and gens are not an issue. Our sole focus is quality";
## 30 gens + 4 drift)

Session C opened per protocol (fresh worktree at 644d29b, 116 tests,
ruff clean, drift 4/4 pass - Tier B overall, the bitforge probe Tier
A byte-identical). The queue's #1 ran eight rounds; the ladder of
failures is the record's real payload:

- **The 2x-scaffold path is measured DEAD for props.** Sedan anchored
  on the 2x NN of the approved mock frame: size-exact, zero
  off-strip, and 98.5-100% uniform 2x2 blocks at EVERY strength
  (140/120/100) - a doubled anchor teaches the model 2px grain, and a
  small simple object (unlike the E02 facades) invites no new form to
  break the grid. Upscaled copies, rejected by the governing rule.
- **A finished native-grain anchor is returned unchanged** (code
  sedan, 2.0-6.1% across @140-@80): the model treats it as done. A
  CRUDE mass-only anchor is ALSO returned unchanged (3 colors) - the
  hydrant precedent's invention does not fire on vehicles at all.
- **The code-drawn sedan path was closed by the board on quality**
  ("These cars do NOT look good"), after a live catch mid-round: the
  v5 code sedan read as "a car with essentially two front ends" -
  symmetric overhangs, mirrored bumpers/lights, centered cabin. v7
  fixed direction (rear-biased cabin, diagonal A-pillar, long hood)
  but the closure stands: hand-drawn vehicles are below the world's
  generated-asset bar.
- **Free generation + PERIOD PROPORTION LANGUAGE is the winning
  recipe.** Free pixflux draws genuinely modeled period cars; probes
  measured description-vocabulary moving the stand height: 65x30
  ("chunky toy proportions"), 72x34 ("fills the frame" - buys height,
  pays in noise), 68x29, 50x21. The picks are board-quality period
  vehicles, all 0 off-strip under forced strips.
- **Colorways are native generations, never recolors**: the
  positional tier-map that worked on code bodies turned a generated
  pale-heavy coupe patchy-rust in-scene. Re-briefing the model under
  a recolored strip (OXBLOOD_RAMP + slate glass) delivered a true
  oxblood coupe first pass.
- **The wagon redraw landed round 1**: the hero's own approved pixels
  resized to the recorded 81x47 target as anchor @150 -> genuine
  native redraws (35-38% changed); s16711 picked, then curated on a
  copy (anchor-guided alpha backfill 26px; the generated emblem blob
  cleared and the canon build_emblem(12) pan-D stamped - brand
  geometry is code, recipes/wagon_curation.py).

THE FLEET AT THE BOARD (candidates, nothing promoted): slate sedan
s16731 (65x30), oxblood fastback coupe s16742 (76x33), gray pickup
s16746 (66x28), hero wagon s16711 curated (81x47). In-scene board
review/native_vehicles_inscene_v3.png; provenance
e16_native_vehicles.json (params, censuses, sha256s); all nine
generation/curation scripts preserved under recipes/.

AWAITING THE RULING - the lane law: the recorded sedan class
(38-in-40, derived from the 2x NN donor read) conflicts with the
model's natural full-length proportion (28-34 stand), and every
38-forcing path measured worse (upscaled copies, chunk toys, or
noise). RECOMMENDATION: amend the sedan class to full-length
footprint (63-76) at the measured 28-34 stand, driving depth
recentered per vehicle height; the van/wagon class keeps its recorded
overflow-upward law (the wagon at 81x47 correctly stands over every
car). NN scaling retires from the standing board the moment the fleet
is ruled in. Session C spend: 34 gens (4 drift + 30 vehicles);
expected balance ~4,193, ledger-verified (30/30 seeds accounted), API
balance still USD-anomalous.

## The vehicle loop: theme, era, aspect (2026-08-11 session C cont.;
## board: "Critically reflect... Begin a loop... correct aspect" +
## "This is the 90s" + "squished"; 32 gens, rounds 9-13)

The critical reflection, owned in full: the first fleet carried
realistic automobile aspect (2.2-2.4:1) and miniature-model noise
into a dollhouse world whose approved vehicle reads are 1.7-1.84:1 -
and my amend-the-law recommendation tried to move the world toward
the model. WITHDRAWN. Worse: every brief said "1940s" - an era I
inferred from the cast-iron lamppost. The board's correction landed
mid-loop: THE GAME IS SET IN THE 1990s; the street carries 70s/80s/
90s iron. All 40s briefs were off-theme. The family wagon's rounded
old-van read SURVIVES on theme grounds: a thirty-year-old shop runs
a thirty-year-old van; the street modernizes around it.

THE REPAIR MECHANISM, isolated and proven (the round's law): an
anchor made of good pixels resized NON-INTEGER reads as damaged
pixel art, and pixflux repairs it into native grain AT THE GIVEN
PROPORTION (17-31% redraw, aspect held exactly) - where every clean
anchor (doubled, hand-drawn, or mass-only) returns unchanged and
free generation reverts to realistic proportion. This is why the
wagon worked in round 1 and nothing else did.

The loop then bracketed the world's car aspect from both ends: the
model's natural era stands (23-28) read too low; the full lane-law
stretch (38-40 stands) the board called SQUISHED on boxy era bodies.
Round 12 rendered the middle (stands 30-33) and round 13 closed the
residual defects by deterministic SOURCE cleanup + rerender (the
coupe's front cream mush -> red rule, 23 px; the hatch's roof spike
erased, 4 px) - artifacts survive the repair pass, so they are
removed from the source, never patched on the output.

THE 90s FLEET (candidates, nothing promoted): boxy 80s sedan s16781
(70x30, slate), 70s hardtop coupe s16792 (72x30, oxblood), 90s
hatchback s16794 (56x31, worn gray), 80s pickup s16787 (66x33,
gray), the family wagon s16711 curated (81x47). All 0 off-strip.
In-scene: review/native_vehicles_inscene_v5.png. AWAITING THE
RULING: the world's car aspect, presented as an in-scene sedan
ladder (stands 25 / 30 / 36) - the fleet is rendered at the middle;
the lane law amends to whatever the board's eye picks, and the
staging/builder/Godot-proof update follows. Loop spend 32; session
total 66; expected balance ~4,161 (ledger-verified).

## The fleet locked; Moretti's opened (2026-08-11 session C cont.;
## board: "The cars all look great. Lock them down and proceed";
## 8 gens this stretch)

THE LOCK-DOWN, verified end to end:
- The five picks entered approved/ as vehicle_sedan80_slate /
  vehicle_coupe70_oxblood / vehicle_hatch90_gray / vehicle_pickup80_
  gray / vehicle_wagon_native (sha256s in
  e16_vehicle_promotion_2026-08-11.json; raws stay in candidates/).
- THE ASPECT IS RULED: the middle of the measured bracket - car
  classes stand 30-33; the van class (wagon 81x47) keeps overflow-
  upward. The 38-in-40 sedan convention and the lane_bottom-14 depth
  formula are SUPERSEDED (both were 2x-NN-era derivations); recorded
  driving depths stay base_y 290 (lane 1) / 330 (lane 2), parked 260.
- NN SCALING IS RETIRED: actors_presentation rewritten - five native
  vehicles at scale 1 plus the extras; the amended vehicle law and
  the 1990s era law live in its comment. validate_scene_staging
  passes.
- The builder rebuilt board v21 from the staging data alone;
  reference_python.png is BYTE-IDENTICAL to the v20 proof reference
  (sha 4b75b757...), so the staged scene is untouched and the
  standing 0/230,400 Godot proof holds without a re-run.

MORETTI'S TRATTORIA opened (queue #2; brief and register stand).
Three measured rounds, recorded honestly:
- r1 (2 gens, @140, code scaffold): the scaffold returned nearly
  unchanged - the same over-finished-anchor refusal the vehicles
  taught, now proven on facades. Alpha holes backfilled per the law.
- r2 (4 gens, @130/@140, coarse scaffold + repair break): NO-OP.
  Finding worth the spend: THE REPAIR BREAK FIRES ON DETAILED PIXELS
  ONLY - flat scaffold rectangles have no grain to break. The two
  mechanisms do not compose on empty geometry.
- r3 (2 gens, @120, donor scaffold): the right engine, mis-fed. The
  tileC_town4 classical building was column-recomposed to center the
  door, lum-mapped to the LS ramp - but my slice choice carried no
  storefront glass (arch slots, a sliver of doorway), so it reads as
  wainscot, not a trattoria front, and the model repaired trivially
  (4.7/16.7%). NEXT ROUND, papered: re-source from the sheet's SHOP /
  display-glass bands (rows 0-4 - real storefront glass for the
  display language to light), same door-centering composition, same
  LS mapping. Awning, MORETTI'S/TRATTORIA lettering and the menu
  stand remain code, composited after the body is picked.

Session C spend: 74 (4 drift + 62 vehicles + 8 Moretti's); expected
balance ~4,153; ledger consistent. Recipes r1-r3 preserved.

## Moretti's: the display mechanism found, the front branded
## (2026-08-11 session C cont.; board: "Perfect. How do we proceed?"
## -> the loop continued; 14 gens, rounds 4-8)

The study's paid-for laws, in the order they were bought:

- **r4-r5**: the display-glass donor composed correctly (mirrored
  bays; the doorway CENSUSED to (14,17)-(34,40) after an eyeballed
  crop caught shelving - measure before pixels, again), and a new
  protocol point: THE SCAFFOLD IS JUDGED WITH EYES BEFORE ANY SPEND.
  Register guard applied in composition: donor cyan glass (reserved
  institutional signal) never reaches the model unmapped... yet both
  rounds still returned grain-only (7-14%).
- **r6 - THE RAW-IN LAW** (the study's key): a scaffold PRE-MAPPED to
  the final register reads as tonally done, and the model politely
  grains it. Fed RAW donor color under the forced LS strip, it
  repainted 76.5% into the register. E02's facades always worked this
  way; the pre-map was my own invention and it was the blocker.
  Corollary: alpha backfill uses the register-mapped scaffold, never
  the raw one.
- **r7 - CONTENT-PRESERVED**: donor bay content that is pictures and
  hanging signs stays pictures and hanging signs, display language
  notwithstanding. Generation refines what shapes suggest; it does
  not transmute categories.
- **r8 - LANDED**: crude code-drawn goods (bottle silhouettes on
  shelf lines, loaf ellipses) in raw color refined into lit
  wine-bottle shelves in both seeds. **s16862 is the body pick.**
- **Brand layer (code, 0 gens)**: fascia field + MORETTI'S (scale-2
  cream, shadowed) + oxblood scalloped awning (striped OX tiers,
  scallop pitch 19) + TRATTORIA subline.
  `candidates/morettis/morettis_branded_v1.png` is the study
  candidate at the board - NOT promoted.

Flagged residuals for the next pass: awning drop shadow onto the
glass (the grounding law says nothing floats), the door-top notch
(source cleanup, not output patch), the menu stand (wall-line prop,
his signature), and the staging-v3 scene instance - the second
compact exterior and the template's first real test. Provenance:
e16_morettis_facade_study.json. Session C spend 88 (4 drift + 62
vehicles + 22 Moretti's); expected balance ~4,139, ledger-verified.

## The glass ruling: B2 stands (2026-08-11 session C cont.; board:
## "Move forward with B2"; 0 gens - all code)

The glass question ("no blue glass, just this sepia tone?") was
answered by census before opinion: DiNapoli's approved facade v2
glazes COOL - sky-catch (117,226,239), harbor slate (78,100,114),
midnight (48,59,90) - and all three bespoke fronts had drifted
sepia against the canon (zero blue-dominant pixels in the diner and
Rossi's). LAW RECORDED: glazing catches cool sky light in facade
v2's exact vocabulary; the institutional-cyan reservation governs
SIGNAGE AND SIGNALS, not window glass - the over-application was
this session's own invention. Corollary discovered en route: v1's
tall awning hid nearly all the glass and was the monotone read's
second cause.

B2 RULED IN and refined (all deterministic): one sky-catch glint
per bay; 1px mullion at the shelf boundary; the door-notch
intrusions blacked (280 px); awning shortened with its grounding
drop shadow. The MENU STAND - the brief's signature prop - is code
(18x24 easel board, oxblood header, chalk menu lines; the first
draft read as a traffic cone at 3x and was redrawn). The brief's
roster is complete: cream stucco, centered door, lit displays
behind cool glass, oxblood scalloped awning, MORETTI'S/TRATTORIA
code lettering, menu stand at the threshold.
`candidates/morettis/morettis_front_with_stand.png` is the standing
candidate - NOT promoted; promotion rides with the staging-v3 scene
instance, which is next. STILL FLAGGED, awaiting explicit word: the
matching cool-glass pass on the approved Anchor Diner and Rossi's
fronts (block coherence argues for it; they are approved assets).

Addendum to the glass ruling (same day, board catch): the "strange
lighter blue flanking the door" was inherited sky-catch remnants -
generation shine kept by a lazy keep-leftmost rule, plus transom
fragments between scallops. LAW, small but real: GLINTS ARE DRAWN,
NOT INHERITED - all 53 remnant cyan px stripped to slate; one
deliberate 2px diagonal shine per bay at symmetric positions.
morettis_branded_v2c is the standing candidate body.

## Moretti's promoted; the template's second instance stands
## (2026-08-11 session C cont.; board: "Promote morettis_front_with_
## stand then oroceed" [sic]; 0 gens - all code and data)

THE PROMOTION, with one data-law judgment flagged loudly: the scene
unit stages props as DATA (painter order, contact shadows and the
no-door clause all live in staging), so "morettis_front_with_stand"
entered approved/ as ITS COMPOSITION - morettis_facade.png (the
B2c body) + morettis_menu_stand.png (the wall-line prop) +
morettis_front_reference.png (the board-approved combined read,
kept as reference). Provenance:
e16_morettis_promotion_2026-08-11.json.

THE SCENE INSTANCE - decision 3's template generalized for the
first time. approved/morettis_block_staging.json (schema v3,
validate_scene_staging PASS): the eight-band law and both
attachment lines carried unchanged; district = little_sicily;
Moretti's in the center slot [184,439] with its doorway RECORDED
as data [298,326] (facade-local extents + slot origin); the menu
stand at the wall line [334,351], clear of the door - the walk is
SWEPT per the brief (no bags, no clutter). The composer
(recipes/morettis_block_compose.py) builds the block from staging
+ street laws alone: the DECISION-2 MACHINERY FIRED FOR REAL -
register_mapping('walk'/'road' -> little_sicily) over the recorded
OH fills, exact-color, collapse-refused; curb/lamppost/hydrant/
trees/wells citywide per the infrastructure ruling; yellow curb as
the template's translucent 6px regulation band (first draft drew
it opaque-flat - the template's recorded schema was restored and
the staging aligned to it); the LS street story in the actor
layer: the oxblood coupe parked at the rival's door.
review/morettis_block_v1.png is the scene candidate.

INTERIM, flagged in the staging comment: plain code flank walls
(LS neighbor briefs pending), OH-wardrobe extras (LS
wardrobe_variant renders pending), upper-story band lum-mapped
onto the LS storefront ramp. Honest read note for the board: the
LS road register shows the A2 lattice more strongly than OH's
darker asphalt - one cheap data revision (tighten the LS road
tiers) if the board wants it calmer. The block's own Godot proof
rides with its promotion, when ruled.

## Vinnie's Pies opened: the front that says it quietly
## (2026-08-11 session C cont.; board: "The v1 is clean enough to
## proceed"; 4 gens, 2 rounds)

Moretti's block v1 ACCEPTED as clean enough - the LS road lattice
stands as rendered (its data-revision option stays available), and
queue #3 opened on the proven chain. Vinnie's donor is
tileC_town3 - the industrial sheet, first use: the corrugated
shutter (16,6)-(58,31) measures 42 native wide = EXACTLY the
brief's third-of-frontage on the 128 slot; tan storefront band
donates wall, service door and (r1's lesson) nothing else.

Round 1 proved the chain transfers (register repaint into Meadows'
violet-grays landed first try) and paid for three scaffold
defects: my brick courses were drawn double-scale and read as
blocks; the donor-cyan window got negated into pale wall - the
content-preserved law cuts BOTH ways, so a window that must stay
dark is DRAWN dark in the scaffold; and the donor wall slice
carried hanging pilaster caps. Round 2 fixed all three: s16874 is
the body pick (kept worn slat texture), 0 off-strip, backfilled
from the Meadows-mapped scaffold.

Brand layers, all code: the roll-door slats crisped (slats are
code, per the brief); VINNIE'S PIES at scale 3 spanning 216 of the
256 fascia - bulk over craft, whitewash over painted brick; and
the club-violet accent's ONLY appearance, a 2px marquee edge under
the fascia (drawn first, letters over it - a layer-order catch).
`candidates/vinnies/vinnies_branded_v1.png` is the study candidate
at the board - NOT promoted. Next on the board's word: the crates
prop and the Meadows block staging-v3 instance on the
Moretti's-proven chain. Session C spend 92, ledger-verified (4 drift + 62 vehicles +
22 Moretti's + 4 Vinnie's); expected balance ~4,135.

## Vinnie's loop: neglect made lawful (2026-08-11 session C cont.;
## board: "Reflect, refine, and rerender. Start a loop. Critically
## analyze against our vision and overall theme"; 5 gens, r3-r4)

The critical analysis convicted v1 on theme: the wall read as clean
PANELING when the brief's whole story is the cheap paint job with
the truth ghosting through; the openings floated (no reveals, no
sills); the shutter was too clean and too bright for a building
nobody maintains; the values sat too high for the ink-forward
Meadows; and every brand element was crisp where neglect should
show. r3 rebuilt the scaffold as a painted wall with brick FLAKE
REVEALS - and the register made the theme literal: raw brick under
the forced strip can only land in the warm GLASS tiers, so OLD
WARMTH LEAKS THROUGH THE COLD PAINT. Values sank on positive-dark
language ("dim ink toned" - tonal negatives stay banned). r4 paid
for the flake edges (content-preserved keeps rectangle edges;
jagged deterministic insets fixed it) and pre-darkened the donor
shutter 45%. s16879 is the body pick.

NEGLECT AS DETERMINISTIC RULES (the loop's law): wear on brand
geometry stays code - the slats and the club-violet marquee edge
draw through the street's recorded worn-edge rule; the oversized
letters flake by a pixel-drop hash; a padlock sits at the shutter
base. Nothing is hand-random; everything reproduces.
`vinnies_branded_v2.png` supersedes v1 at the board (A/B
presented). Session C spend 97, ledger-verified (4 drift + 62
vehicles + 22 Moretti's + 9 Vinnie's); expected balance ~4,130.

## Vinnie's promoted; the third instance; ONE composer for the city
## (2026-08-11 session C cont.; board: "Proceed with v2"; 0 gens)

vinnies_facade.png entered approved/ (v2 lineage recorded). The
Meadows block became the template's THIRD instance
(vinnies_block_staging.json, validator PASS): the service doorway
[248,276] is data, the roll door [352,434] is recorded as
cargo-not-doorway, and the roster is deliberately GRIM - one tree,
one docker, the gray pickup at the loading door, crates at the wall
line. The crates are the interim class (bags/booth precedent:
donor, desat-warm, 2x) and paid one composition lesson on arrival:
the first 2+1 stack read as person-and-a-half bulk beside a 40px
extra and was reduced to a waist-high row before presentation.

TOOLING PROMOTED BY REGRESSION: the Moretti's composer generalized
into recipes/block_compose.py - district register, slot facade
assets and every placement read from staging data; any staging-v3
file composes through one script. The refactor is proven, not
assumed: it reproduces the Moretti's board BYTE-IDENTICALLY (the
staging gained its slot 'asset' key as the composer's contract).
Three districts now render from three data files and one law
script. review/vinnies_block_v1.png at the board. Session C spend
unchanged at 97; expected balance ~4,130.
