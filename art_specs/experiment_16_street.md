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

## The Meadows assembled: a nightlife district switched off
## (2026-08-11 session C cont.; board: "Reflect on the meadows...
## Utilize sequential thinking"; 8-step reflection, 0 gens)

THE REFLECTION (sequential, recorded in full in the session; the
verdict): the block said "generic quiet street" where the canon
says "clubs, concert halls, money that comes out after dark"
(data.py:71; underground 1.5 = the city's highest; luxury-good
bias; stadium events). The Meadows' theme position: the district
where WARMTH IS A COMMODITY, sold after dark - and by day the
commodity is locked in its packaging. Not University's
institutional cold: a warm district SWITCHED OFF. The club-violet
law already encodes this ("money-adjacent, never glamorous"), and
the reservation of warm neon for the cast makes the unlit state a
legal requirement, not just a mood.

THE DRESSING (all data + code, zero gens; staging carries every
parameter, the composer reads them):
- WEST FLANK = A SHUTTERED CLUB: dark marquee with UNLIT bulb dots,
  dead-neon zigzag blade sign in accent darks (NO NAME BOUND -
  naming awaits the board; the blade takes code lettering the day
  it is named), chained + padlocked double door (the district's
  second padlock - the Meadows locks up by day), poster cases with
  abstract no-text posters (one fresh violet field). FLAGGED
  JUDGMENTS: the club door is recorded NOT-A-DOORWAY pending
  naming; the posters pull the grime/decal class forward.
- UPPER BAND, Meadows variant (meadows_upper_band): 7 blinds-drawn
  / 2 dark / 1 boarded (warm plank tiers - the warm-through-cold
  echo) / 2 sky-catch - the district census in one band.
- EAST FLANK: poster case + a boarded window; morning-after litter
  at both corners (interim bags); the lamppost moved to the club's
  door (night infrastructure stands where the night business is);
  the tree east. Composition collisions caught by law and by eye:
  the validator refused the first bags placement (x-slot exclusion),
  the tree initially hid the entire club front, the docker stood in
  the tree bed - all corrected in data.
- COMPOSER extension regression-proven: Moretti's board still
  renders BYTE-IDENTICAL (dressing machinery is inert where staging
  carries none).

review/vinnies_block_v2.png supersedes v1 (A/B at the board).
Session C spend unchanged: 97; expected balance ~4,130.

## The club named: THE ORCHID (2026-08-11 session C cont.; board:
## "Work to determine a name"; 0 gens)

Determined per the flank-naming precedent - candidates censused
against the tree, the theme guard and the glyph set, rejections
recorded. THE ORCHID: the club-violet accent IS orchid violet, so
the name binds the district's accent color to a place the way
oxblood binds to Moretti's awning and gold to the family; an orchid
is hothouse warmth sold as luxury - the Meadows' thesis in one
flower. Rejected: EMPIRE (killed by the tree - it is the game's own
tagline word), SAVOY (real-ballroom referent too strong), ONYX
(black where the district is violet), PALACE (generic), VELVET
(lounge-cliche drift). Bound as slot data (business the_orchid);
the blade sign carries the name as stacked DEAD-NEON letters in the
accent's unlit tiers; the marquee carries THE ORCHID as a pale
letterboard strip (changeable letters read by day - period-true).
The door stays chained and NOT-A-DOORWAY: named is not open; the
flag rides until the club becomes a gameplay surface. Composer
extension regression-proven again (Moretti's byte-identical).
review/vinnies_block_v3.png supersedes v2. Spend unchanged: 97.

## The Orchid rebalanced; the interim debt retired to candidates
## (2026-08-11 session C cont.; board: "The neon orchid is larger
## than the main name. Work to rebalance... Be purposeful with this
## work. This is critical refinement"; 8 gens)

REBALANCE (0 gens, data): the marquee is now the name's home - THE
(small) over ORCHID at letterboard scale 2 on a taller marquee, one
bulb-row collision caught and fixed by a data nudge; the blade
tightened to fixed-pitch stacked letters and reads as the vertical
echo. Composer takes text_lines/pitch from staging.

THE INTERIM DEBT, run purposefully - one prop at a time, anchors
judged by eyes before any spend (the first crate anchor read as
striped solid boxes, the booth as a vending machine, and both were
being resized non-integer by lazy math; both were redrawn on exact
canvases before a single generation):
- BAGS (organic, tree precedent): both seeds landed; s16901 picked -
  soft slate folds, cinched tops, tidy enough for the hero block and
  grim enough for the Meadows.
- CRATES: round 1 FAILED and paid for a law - my dark plank GAPS
  invited the model to open the crates into empty lattice frames.
  CRATES ARRIVE CLOSED: solid faces with thin seams. Round 2's
  s16913 picked (dark-seamed X-braces echoing the shutter).
- BOOTH (the pressure's own furniture - the calls arrive by phone):
  s16921 picked at 12% wear over the v2 anchor - and it retires the
  interim booth's institutional-BLUE register violation, the
  doubled Omega's loudest wrong note on the hero block.
All picks 0 off-strip. In-scene interim-vs-native A/Bs presented;
the proof reference is UNTOUCHED - the staging swaps (hero block
bags/booth, Vinnie's crates), the builder re-run and the byte-check
await the board's word. Session C spend 105, ledger-verified;
expected balance ~4,122.

## The natives promoted; the proof re-run and an incident recorded
## (2026-08-11 session C cont.; board: "1.) Approved 2.) Approved.
## Proceed"; 0 gens)

bags_native / crates_native / booth_native entered approved/
(sha256s in e16_native_props_promotion_2026-08-11.json); the hero
block and Vinnie's stagings swapped to them (validators PASS; the
crates moved to x435 to clear the tree's curb slot - the x-slot law
holds even during promotions). The interim assets are retired to
the archive; NO staging references doubled Omega props anymore -
the donor-grain debt on the standing boards is CLOSED.

THE PROOF INCIDENT, recorded at full price: the first v22 capture
deviated 3,107/230,400 - almost exactly the two new sprites' area.
My first hypothesis (partial-alpha fringes violating the
binary-alpha contract) was REFUTED by census: all three natives are
alpha-binary. The actual cause was operational: Godot's runner does
not re-import changed source PNGs, so the capture rendered stale
textures. OPERATIONAL LAW, now standing beside "headless cannot
capture": after ANY asset change, `godot --headless --import
--path .` BEFORE the windowed capture run. After re-import:
**0 / 230,400.** The reference hash changes BY DESIGN (the staged
scene changed by sanctioned ruling); the new sha and its provenance
are recorded. Moretti's block still composes byte-identical -
untouched by any of this, as it should be.

Boards: hybrid_dinapoli_block_board_v22 (the hero block, all-native
props), vinnies_block_v5 (native crates and bags). Session C spend
unchanged at 105; expected balance ~4,122.

## The street kit: curb corners + crosswalk (2026-08-11 session D;
## drift 4/4 Tier B; 4 gens + 4 drift)

Queue item "curb corners + crosswalk" ran to candidates on the
recorded assignment: paint is a regular form -> CODE with a recorded
wear rule; concrete wear is organic -> the s16102 recipe (code
anchor + pixflux wear @140 under the citywide strip). New law homes
in street_block.py, all test-pinned (suite 116 -> 131, ruff clean):

- **CURB_TONES** — s16102's five concrete tones censused verbatim
  (anatomy measured: 7 pale / 1 transition / 5 face / 3 base rows,
  joints at x=15 mod 16, top-surface speckle 8.5%) and recorded as
  the single citywide curb authority.
- **CROSSWALK_PAINT (208,196,168)** — the paint system's pale voice
  against the center line's worn ochre; exact-color disjoint from
  every register value, curb tone, reserved identity color, well
  metal and slate tone (pinned by test).
- **paint_wear_drop + crosswalk_paint(_vertical)** — worn zebra
  bars, whole and centered, wear graded by physics: 4% base, 30%
  in wheel bands, +6 on bar edge rows. NEGATIVE RESULT RECORDED:
  the letter-scale pixel-drop hash ((x*13+y*7)%11) lays drops on
  slope -13/7 diagonals that read as moire on 8px bars, and the
  worn-edge column rule eats the same columns of every bar —
  paint wear at bar scale needs spatially WHITE loss (a new mixing
  hash, recorded; grades tuned by eye against B/C variants).
  pixel_drop_worn kept its authority for letter-scale flaking and
  got a named home in street_block.py.
- **curb_vertical_strip** — the flat-on grammar's side-street curb:
  top surface only (no south face), 16px stone rhythm, 2px dark
  road edge; both road_side orientations.
- **curb_corner_anchor** — 32x32 return-arc anchors (radius-6 outer
  contour, face tapering by cos theta from south-facing to
  east-facing, s16102 anatomy); se/sw mirrors as CODE; each
  orientation buys its OWN seeds so generated wear is never a
  mirror twin.
- **validate_scene_staging** accepts an optional `crosswalk` staging
  block and refuses out-of-scene spans, corridors narrower than a
  figure, and non-positive pitch.

THE WEAR ROUND (4 gens, s16931-16934, anchors eyes-judged in
context BEFORE spend): all four returned 0 off-strip with 37-42%
changed — the wear pass fired (wagon-band change rates), the arc
geometry held, and the texture family-matches s16102 at the seam
with no pop. PICKS: **se s16931** (cleanest contour; the pale
tongue at the arc reads as a worn curbstone catching light) and
**sw s16933** (its equal in the mirror orientation); s16932
alternate; s16934 rejected on top-surface crack noise. Provenance
e16_curb_corner_wear.json (params, seeds, hashes, usage).

IN-SCENE PROOFS, nothing promoted:
- **Hero block v23 CANDIDATE** (candidates/street_block_staging_
  v23_crosswalk.json): mid-block crossing on DiNapoli's doorway
  (corridor [286,325] centered on the door), wheel bands derived
  from the recorded driving depths (lane 1 base 290 -> local rows
  60-70; lane 2 base 330 -> 100-110); center dashes and the worn
  edge line break at the corridor (wear phase stays
  world-anchored). The builder gained staging-path + board-version
  parameters and the crosswalk law (inert without the staging key —
  proven: the approved re-bake is BYTE-IDENTICAL, reference sha
  9a556b33... and board v22 sha unchanged). **Godot proof on the
  candidate: 0 / 230,400** (import law observed); the approved
  scene then re-baked and re-proven **0 / 230,400** — the standing
  state is untouched.
- **Corner diorama** (review/street_kit_corner_diorama_v1.png,
  recipes/kit_corner_diorama.py, 0 gens): a 400x360 half-frame
  intersection from law code + approved assets — both corner picks
  at their returns, vertical strips to the horizon, BOTH crosswalk
  orientations (vertical bars over the cross street with lane-
  column wheel bands), far-line breaks, lamppost, sedan
  approaching, two extras mid-crossing. One reflection round paid:
  v1's walk columns stopped at the cornice line and the rows above
  read as black voids — cross-street sidewalks and curbs run to
  the horizon with the road.

FLAGGED FOR THE BOARD, loudly:
1. **The mid-block crossing is a placement judgment.** A marked
   crossing's natural home is a corner; the 640 hero block cannot
   stage an intersection without facade surgery (shorten a flank
   facade by regeneration, widen the scene, or give corners their
   own scene instances). The diorama shows the corner-true
   composition; v23 shows the zero-surgery in-scene read. The
   board rules which (or neither) proceeds to promotion.
2. **Far-curb-line color is a two-authorities smell**: the hero
   builder draws it in WALK tier 2 (140,129,112) while
   block_compose draws (206,192,162). Both are recorded renders;
   unifying changes bytes somewhere — the board's call which voice
   wins. The diorama used the builder's.
3. Corner promotion would also record the placement law: corner
   pieces sit on the 16px stone grid (joints assume x = 0 mod 16
   placement).
4. Composer/builder session-path defaults were dead (prior
   scratchpads); both now parameterized via ART_WORKTREE with this
   session's default. Composer regression after the change:
   Moretti's AND Vinnie's boards both **0 pixels differ**.

Session D spend: 8 (4 drift + 4 corners), ledger-verified;
expected balance ~4,114 (API still USD-anomalous; vendor dashboard
remains the authority).

## Board notes on the kit round: traffic direction + curb cuts
## (2026-08-12; 0 gens — all code and data)

The board accepted the kit boards ("looks great") with two catches,
both real, both now law:

1. **"Both lanes seem to be flowing the same way."** Measured true,
   and the root recorded: ALL FIVE fleet assets natively face LEFT,
   and the actor layer placed them unmirrored — so both travel lanes
   read westbound (v20's "right-hand traffic reads correctly" claim
   did not survive this census). THE TRAFFIC-DIRECTION LAW, now in
   the staging comment: lane 1 (north travel lane) is westbound and
   takes native facing; lane 2 (south) is eastbound and takes
   `flip: true` (builder support added). THE WAGON NEVER MIRRORS —
   the pan-D emblem is brand geometry — so the wagon always drives
   lane 1 westbound; the pickup (no lettering) mirrors into lane 2.
   actors_presentation updated (wagon x330 base 290; pickup flipped,
   x190 base 330); the staged scene is untouched (reference sha
   9a556b33... unchanged after re-bake; board v22b supersedes v22's
   actor read). The diorama gained opposing traffic the same way.
2. **"We should have curb cuts for crosswalks."** Period-true (ramps
   predate the thirty days; the ADA made them law in 1990). New law
   code, test-pinned (suite 131 -> 134): `curb_cut` — the 16px
   band's face and base drop out across the corridor into a sloped
   speckle-tone apron with 4px triangular wing steps, s16102 anatomy,
   pixel-drop wear; `curb_vertical_cut` — the side-street strip's
   2px dark edge opens the same way, both orientations. The builder
   draws the cut at any staged crossing corridor, softens the far
   curb line to the ramp tone, and CLIPS the yellow regulation zone
   clear of the apron (paint never runs onto a ramp).

COMPOSITION LESSON, paid in one render: the diorama's v1 corridors
overlapped the corner returns once the cuts made the overlap
visible (H-corridor [102,141] vs corner [110,142]; V-rows [164,204]
vs strip stubs from 192). Real intersections put the ramp flush
BEFORE the return: H-corridor moved to [70,109], V-rows to
[152,192], lamppost cleared off the apron. RECORDED AS PART OF THE
KIT'S PLACEMENT LAW: crossing corridors never overlap a corner
return; they end where the return begins.

PROOFS RE-RUN: v23 candidate (now with cut + clipped yellow +
corrected actors) Godot **0 / 230,400**; approved scene re-baked
and re-proven **0 / 230,400**, reference sha unchanged. Spend this
pass: 0 gens; session D total stands at 8.

## The kit promoted; the decal class opened (2026-08-12, board:
## "I agree with your suggestions. Proceed"; 2 gens)

THE PROMOTIONS, on the board's word:
- Corner picks **se s16931 / sw s16933** entered approved/ (sha256s
  in e16_corner_promotion_2026-08-12.json; raws stay in
  candidates/curb_corners/). The kit placement law rides with them:
  corners sit on the 16px stone grid; crossing corridors never
  overlap a return.
- **The crosswalk entered the hero block**: approved/street_block_
  staging.json carries the crossing (DiNapoli's doorway alignment,
  recorded wheel bands, curb cut, clipped yellow zone); the v23
  candidate file is RETIRED (one writable authority). The staged
  scene changed by sanctioned ruling: reference sha 9a556b33... ->
  **bc8c1e0a...**, recorded in e16_crosswalk_promotion_2026-08-12
  .json; Godot proof **0/230,400**; board v23 supersedes v22b.

QUEUE #2 OPENED — THE GRIME/CRACK DECAL CLASS. Design ruling
recorded before pixels: decals are TRANSLUCENT overlays, the class
the oil stains / contact shadows / yellow curb founded — alpha
layers flattened at bake that darken any district register without
minting new exact colors (decision 5 stays safe). District grading
is PLACEMENT DATA under a recorded law: the Meadows dirtiest, Old
Harbor moderate, Little Sicily swept, University pristine.

- CODE (street_block.py, suite 137 -> 141 with validator rules):
  `asphalt_patch` (tar seam + hash corner nibbles; ROAD-ONLY,
  validator-enforced), `grime_stain` (the oil-stain geometry
  generalized), `wall_streak` (drawn but NOT staged — streaks land
  on approved facade art and await their own ruling),
  `crack_to_decal` (the curation law: luminance -> black alpha).
- THE CRACK PROBE (2 gens, s16951/s16952, provenance
  e16_crack_probe.json): **free generation at decal scale fills the
  canvas** (100% opaque texture field — refused, measured) while a
  crude 2px code polyline @120 refined into a genuine hairline
  branching crack at 7% opaque. LAW: cracks are SHAPE-FROM-
  GENERATION, TONE-FROM-LAW — polyline anchor, repair pass,
  crack_to_decal conversion; the one decal lands on every district
  road (OH + Meadows swatches proven).
- Staging schema: optional `decals` list ({type, x, y, w, h,
  variant} or crack + asset); validator refuses unknown types,
  out-of-scene origins, off-road patches.
- IN-SCENE: hero **v24 CANDIDATE** (candidates/street_block_
  staging_v24_decals.json) — the Old Harbor MODERATE roster: two
  patches (one per lane), the frost-heave crack by the manhole, two
  stains. Builder decal support proven inert (approved re-bake
  byte-identical at bc8c1e0a...); **v24 Godot proof 0/230,400**;
  approved v23 restored and re-proven 0/230,400.

AWAITING THE BOARD: the v24 decal roster (and with it the class'
read at "moderate"); the far-curb-line color flag STILL OPEN (needs
an explicit winner named — the flag's two voices are recorded
above); then the Meadows/LS rosters, more crack anchors (each its
own seed), and the wall-streak ruling. Session D+E spend: 10 gens
total (4 drift + 4 corners + 2 crack probe); expected balance
~4,112, ledger-verified.

## The road de-bricked; the manhole laid flat (2026-08-12, board:
## "the road now feels brick... regenerate the manhole to better fit
## the view"; 2 gens)

Both notes measured real and fixed candidate-first:

1. **THE ROAD.** The A2 donor fill's diagonal lattice reads as
   brickwork — always latent (the LS lattice note, v5's
   flatten-the-ramp round), surfaced now because the pale crossing
   sits beside it. The hybrid ruling's selective-upgrade-with-cause
   clause fires: **asphalt_field** (street_block.py, test-pinned:
   deterministic, register-bound, provably no 16px period) — a
   full-band aperiodic field, tier-1 base with white-mix hash
   speckle (dark pores 8% / mid grain 8% / pale flecks 1.5%),
   register-aware via the ramp parameter so every district inherits
   it on promotion. The builder takes it as a STAGING PARAMETER
   (`road_fill`: "a2_donor" default | "asphalt_field") — the
   approved scene re-bakes byte-identical (bc8c1e0a...), the A/B
   swatch shows the lattice dead. District composer adoption rides
   with promotion.
2. **THE MANHOLE.** s16322 is a flat-on circle on a foreshortened
   ground. Resize-by-regen on the repair mechanism: the approved
   cover's OWN pixels squashed non-integer 26x26 -> 26x19 (the
   ground compression), pixflux @150 under its censused 3-tone
   strip, 2 seeds (s16961/s16962, both 0 off-strip, 63/66% genuine
   redraw at the GIVEN proportion). **s16961 picked** (clean
   concentric double ring; s16962's rim breaks, stray fleck).
   y_top unchanged — old and new content centers match. Provenance
   e16_manhole_regen.json.

IN-SCENE: hero **v25 CANDIDATE** (candidates/street_block_staging_
v25_road_manhole.json = the v24 decal roster + asphalt_field +
manhole s16961). **Godot proof 0/230,400**; approved v23 restored
and re-proven **0/230,400**, reference sha unchanged. The read: the
brick is gone, the pressure-dark asphalt strengthens the thesis
contrast at the curb, the decals and vehicles pop, and the cover
finally LIES on the road.

Suite 141 -> 143. AWAITING THE BOARD: v25 (which now carries v24's
decal roster — one word can rule the stack); the far-line flag;
then the district-composer adoption of asphalt_field, Meadows/LS
decal rosters, wall-streak ruling. Session spend: 12 gens total
(4 drift + 4 corners + 2 crack + 2 manhole); expected balance
~4,110, ledger-verified.

## The v25 stack promoted; the field goes citywide (2026-08-12,
## board: "Approved! Proceed"; 0 gens)

THE PROMOTION (provenance e16_v25_promotion_2026-08-12.json):
- approved/street_block_staging.json IS the v25 stack — the OH
  moderate decal roster, road_fill = asphalt_field, and the
  elliptical manhole (s16961 into approved/; s16322 retired — the
  flat-on-circle era ends). Candidate files retired; one authority.
- Hero reference sha, by sanctioned ruling: bc8c1e0a... ->
  **5d19e406...**; Godot proof **0/230,400**. Board v25 stands.
- DISTRICT ADOPTION: block_compose draws asphalt_field through each
  district's own road ramp (+ decal and flip support, both inert
  where staging carries none). By-design diffs measured and
  CONFINED TO ROAD ROWS 232-343: Moretti's v1->v2 64,850 px,
  Vinnie's v5->v6 66,228 px (+ the sedan flip). The diorama
  re-rendered on the law fill.
- THE AUDIT THE PROMOTION SURFACED: the district blocks' actor
  layers predated the traffic-direction law. Moretti's is lawful
  (two parked, pickup lane-1 native-west); Vinnie's lane-2 sedan
  drove eastbound facing west — flip:true recorded. Moretti's
  re-render after the composer flip change: BYTE-IDENTICAL
  (07d73638...), the inertness proof.

The Meadows road in its own ramp is the promotion's best read: ink
asphalt, no lattice, the switched-off district finally standing on
the right ground.

STANDING FLAGS: far-curb-line color (still needs a named winner);
wall streaks (facade dressing ruling); LS road-lattice data
revision is RETIRED AS MOOT (the lattice itself is gone). NEXT IN
QUEUE: Meadows/LS decal rosters (grading law: dirtiest/swept),
more crack anchors, then the animation slate and University Hill.
Session spend stands at 12 gens; expected balance ~4,110.

## The grading law's first cross-district test: Meadows dirtiest,
## Little Sicily swept (2026-08-12 session F; drift 4/4 Tier B; 0
## roster gens)

Session F opened per protocol (fresh worktree at 0beee46, 143 tests,
ruff clean, drift 4/4 Tier B). The queue's head ran data-only, with
the composer regression run FIRST: both approved stagings reproduce
their standing boards from this worktree BYTE-IDENTICALLY (Moretti's
v2, Vinnie's v6) before any candidate was authored.

AUDIT CATCH before the rosters: both district stagings still staged
the RETIRED flat-circle manhole s16322 - the v25 promotion ended the
flat-on-circle era on the hero only. The elliptical swap rides in
both candidates as data (asset + content-span; base_y unchanged -
content-bottom anchoring absorbs the shorter ellipse; spans
re-derived from the s16961 bbox: Vinnie's [483,508], Moretti's
[303,328]).

THE ROSTERS (candidates, validator PASS both):
- **Vinnie's v7** (candidates/vinnies_block_staging_v7_decals.json),
  MEADOWS DIRTIEST: three patches (two reading as one utility dig
  crossing parking+lane 1, one lane-2 repair), the frost crack west
  in lane 1 (the s16952 decal, hero's crack reused at a different
  lane and position), loading-door drips at the pickup stall, gutter
  grime under the club lamppost, a lane-2 drip trail east. Census:
  2,706 px changed vs v6, confined to road rows 228-334.
- **Moretti's v3** (candidates/morettis_block_staging_v3_decals
  .json), LITTLE SICILY SWEPT: ONE faint gutter mark east of the
  parked sedan - the district's cleanliness IS the read; the host
  sweeps his walk. Census: 498 px vs v2 (150 stain + 348 manhole).

THE CRITIQUE PASS PAID (the loop, before the board saw anything):
1. **The walk stain failed.** The dirtiest roster's first draft put
   a morning-after spill on the walk at the club corner; at 5x the
   grime_stain lobes read as a raised gray MOUND on the pale walk -
   the same function that lies flat on dark asphalt turns its lobe
   structure into highlight-and-shadow on light ground. PULLED and
   recorded in the staging comment: a walk-scale spill needs its own
   decal law (flat, wet-edged), flagged beside wall_streak's pending
   facade-dressing ruling - surface-specific decals need their
   surface's read proven.
2. **The drip trail sat in the manhole's column** (x480 vs cover
   483-508) and read as seepage stuck to the cover - moved east to
   x545, clear of it.

Cross-scene honesty, flagged: the crack decal is the SAME s16952
shape the hero carries (different lane/position). One or two new
polyline anchors (~1-2 gens each, own seeds, crack_to_decal) buy
true variety; priced, awaiting appetite.

A/B boards at the board: ab_vinnies_v6_v7, ab_morettis_v2_v3 (2x,
standing over candidate). AWAITING THE BOARD: both rosters, the
manhole audit swap (all three scenes then elliptical), the walk-
spill flag, the crack-variety option - and the standing far-line
and wall-streak flags. Session F spend: 4 gens (drift only);
expected balance ~4,106.

## Moretti's gets real neighbors; the Meadows gets its own crack
## (2026-08-12 session F cont.; board: "Gens are of no concern,
## quality is the sole focus. Generate any necessary assets. Also, I
## notice Moretti's has no real neighbors"; 10 gens)

CRACK VARIETY (2 gens, recipe crack_variety_r1.py): two NEW polyline
topologies through the proven chain - a Y-BIFURCATION (s16971, 6.8%
opaque) and a STEPPED cold-joint (s16972, 5.5%), each anchor its own
drawing and seed, anchors eyes-judged distinct against s16952 before
spend. In-scene on the Meadows ink both read as true hairlines.
**s16971 swapped into the Vinnie's v7 roster** - the Meadows carries
its own fracture, not the hero's shape; s16972 recorded as variety
stock for future rosters.

LS NEIGHBORS (8 gens, 2 rounds) - the flagged INTERIM plain flanks
become real businesses. NAMES, delegated picks per the flank-naming
precedent (rejections recorded): west = **PALERMO BAKERY**
(place-name; Sicily's capital in Little Sicily; CARUSO'S killed as
real-person referent, RICCI'S killed by the tree - Angelo Ricci is
the muscle, MARINO'S killed once already); east = **DE LUCA BARBER
SHOP** (where the long memories get traded; FIGARO'S killed as
real-opera referent, ROMANO'S runner-up). Briefs: prosperous-modest,
NO awnings (the oxblood scallop stays Moretti's signature); bakery =
display window of loaves on wooden shelves (the r8 code-goods
route); barber = dark glass over a pale cafe curtain (the content-
preserved law: what must stay dark is DRAWN dark), blank pier
reserved for the CODE pole.

- **r1 FAILED on quality, recorded**: no_background carved the
  ENTIRE flat stucco shell into alpha (11,183/12,290 px, hole
  geometry identical across seeds) - the walls came back as pure
  backfill with zero generated texture. The Moretti's-r2 lesson in a
  new coat: flat scaffold rectangles give the engine nothing to fire
  on.
- **r2 LANDED** (seeds 17003/17004 bakery, 17013/17014 barber, @120,
  no_background=False): crude stucco mottle + sills/lintels/reveals
  in raw color gave the repair its bite; full-canvas bboxes, 0
  off-strip all four, 83-84% repaint into the LS register. THE
  MOTTLE PAID A LAW FORWARD: the first draft's (x*13+y*7)%97 hash
  read as DIAGONAL RAIN at 3x - the zebra-bar moire family
  resurfacing at stucco scale, caught by eyes BEFORE spend and
  redrawn on the white-mixing hash. Picks: **bakery s17004** (17003:
  stray fascia flecks), **barber s17014** (17013: black door-edge
  notch).
- **Brand layers (code, 0 gens)**: PALERMO/BAKERY + DE LUCA/BARBER
  SHOP lettering (first draft's subline collided with the scale-2
  descenders - fascia is 22px, main y8 + sub y23 exactly fills it);
  sky-catch glints per bay (drawn, never inherited); the barber pole
  as striped code in register red + cream, no case blue - and the
  pole's first draft sat on the WEST pier inside tree_b's crown
  x-slot (the v11 lesson swallows wall content), moved to the east
  pier where it stands clear.

IN-SCENE: **morettis_block_v4 CANDIDATE** (candidates/morettis_block
_staging_v4_neighbors.json, validator PASS) = the v3 swept-roster
stack + named slot assets + BOTH new doorways as data (bakery
[118,154], barber [566,602]). Census v3->v4: 21,626 px confined to
buildings rows 56-151, ZERO pixels in Moretti's center span. Honest
flags: the loaves read register-cream (the strip carries no crust
gold - an accent-tier round is priced if the board wants golden
crust); upper band stays the recorded lum-mapped INTERIM; LS
wardrobe extras still pending.

Provenance e16_ls_neighbors_2026-08-12.json (params, seeds, sha256s,
both failure records). AWAITING THE BOARD: the Moretti's v4 stack
(neighbors + swept roster + manhole), the Vinnie's v7 stack
(dirtiest roster + own crack + manhole), the loaf-crust option, and
the standing far-line/wall-streak flags. Session F spend: 14 gens
(4 drift + 2 cracks + 8 neighbors); expected balance ~4,096,
ledger-verified.

## Both stacks promoted: the districts wear their grading, Moretti's
## keeps company (2026-08-12 session F cont.; board: "Approved all
## around"; 0 gens)

THE PROMOTION (provenance e16_ls_district_promotion_2026-08-12
.json): approved/morettis_block_staging.json IS the v4 stack -
PALERMO BAKERY and DE LUCA BARBER SHOP as slot assets (facades
copied into approved/, sha256s recorded; raws stay in candidates/),
both new doorways as data, the LS SWEPT roster, the elliptical
manhole. approved/vinnies_block_staging.json IS the v7 stack - the
MEADOWS DIRTIEST roster with its own Y-split crack s16971, the
elliptical manhole. s16322 is now retired from EVERY staging - the
flat-on-circle era ends citywide. Candidate staging files retired;
one writable authority. Byte-checks: both approved stagings
re-render BYTE-IDENTICAL to the board-approved v4/v7 boards.
Standing boards: morettis_block_v4, vinnies_block_v7. The grading
law now reads across three districts on approved data: Old Harbor
moderate (hero), Little Sicily swept, the Meadows dirtiest -
University's pristine slot stays empty until its block exists.

Deliberately NOT treated as ruled by "all around": the far-curb-line
flag (still needs a NAMED winner between the builder's (140,129,112)
and the composer's (206,192,162)), the wall-streak facade ruling,
and the loaf-crust accent-tier round (priced, 2 gens) - each awaits
its own explicit word.

Session F totals: 14 gens (4 drift + 2 cracks + 8 neighbors);
expected balance ~4,096, ledger-verified.

## The animation slate designed (2026-08-12 session F cont.; board:
## "sitting animations, an animated door opening, queueing in line,
## grabbing pizza, etc... utilize sequential thinking"; 10-step
## reflection, 0 gens - paper before probe)

THE MECHANISM LAW (the slate's load-bearing cut) - every animation
ask classifies into one of three classes before any spend:
- **(A) CHARACTER LOOPS** (walk, idle, seated fidget, working
  loops): generated pixel cycles, animate_image/v3 class, gated by
  the keyframe probe. ~1 gen per 32x32 8-frame cycle.
- **(B) PROP STATE-CHANGES** (hinged doors, the roll shutter, wagon
  doors): few-frame transitions between KNOWN states. REGULAR
  TRANSFORMATIONS ARE CODE - a hinged leaf foreshortening into its
  dark reveal, slats vanishing behind a lintel - drawn from the
  facades' own pixels, deterministic. Generation only where the
  code read fails at 1x.
- **(C) SCENE CHOREOGRAPHY** (queueing, walking to the counter,
  driving, delivery dashes): ENGINE STAGING over class-A loops -
  positions over time in Godot. ZERO new pixels. Queueing in line
  = spaced idle loops + one walk + slot advance; it was never a
  pixel problem.

HELD-PROP LAW (grabbing pizza, carrying crates, answering the
phone): every held-prop interaction decomposes FIRST into [static
holding-pose variant] + [engine translation of the prop sprite];
a generated interaction loop is bought only where that decomposition
visibly fails at 1x. The animation-scale echo of "regular forms are
code." Held-prop generation is undocumented vendor-side (docs
addendum item 2) - our decomposition stands on our own measurements.

RECLASSIFICATIONS against the standing queue, flagged:
- **Wagon drive-bob -> engine staging** (wheel rotation is invisible
  at 6px; a 1px y-oscillation is a Godot transform). Optional
  2-frame suspension squash ONLY if the transform bob reads
  mechanical.
- **Cast N/E/W idles -> the interiors round** (street scenes are
  flat-on S-facing; direction poses belong where directions exist).

DIRECTION + MIRROR LAW (proposed, awaiting the probe's evidence):
street walkers need E/W PROFILES; extras carry no brand geometry,
and 32px asymmetries sit below read threshold, so CROWD EXTRAS
MIRROR (one west walk buys east free). CAST and anything lettered
never mirrors (the wagon's law). Whether animate_image can turn a
front-facing sprite into a walking profile is a probe question, not
an assumption.

THE INSTRUMENT LIST (law code with tests when the class opens -
animation_validate.py): frame-0 byte-exact; END-FRAME byte-exact on
interpolation calls; per-frame palette census vs the sprite's own
palette (animate_image exposes NO forced-strip surface - palette
conformance is POST-VALIDATION, a recorded contract difference from
pixflux); per-frame binary alpha; content-bbox stability (feet on
baseline, bob <= 2px); loop continuity (last->first delta vs
inter-frame mean); determinism (same seed, repeat call).

THE SLATE, phased - each phase presents boards, nothing enters
approved/ without the word:
- **PHASE A - probes (~3 gens)**: A1 keyframe probe (extra_man_cream
  32x32, "walking, side view, facing left", 8 frames: measures
  frame-0 exactness, palette drift, alpha, profile synthesis,
  determinism via one same-seed repeat); A2 interpolation probe
  (standing->seated, 4 frames: measures BOTH-endpoint exactness).
- **PHASE B - street life (~6-10 gens, gated on A)**: west-profile
  walk cycles for the walking extras, mirrored east; seated idles
  a/b (the four-top breathes).
- **PHASE C - shop life (~4-8 gens)**: Tony's oven loop (the theme's
  signature animation - thirty years of oven warmth IS Tony at the
  oven), Bee's counter idle, holding-pose variants (box hand-off,
  phone), talking loop if cheap.
- **PHASE D - code (0 gens, any time)**: DiNapoli door-open frame
  strip (the door-class proof at the board), Vinnie's shutter roll,
  phone-ring blink. Door-gap interiors get a 2-3 tier warm sliver
  per district register, exact-color (decision 5 stays safe).
- **PHASE E - deferred by existing rulings**: Orchid marquee chase
  (decision 5), night variants, cast direction poses (interiors),
  the REST skeleton path (only if v3 text guidance disappoints).

## Phase A measured; the far-line flag gets its A/B (2026-08-12
## session F cont.; ~3 gens MCP-estimated)

THE KEYFRAME PROBE (animation_probe_r1.py; animate_image via the
pipeline's mcp_client; subject extra_man_cream 32x32; 2 same-seed
walk calls + 1 interpolation call):

1. **FRAME-0 IS COMPOSITE-EXACT, NOT FILE-EXACT** - the probe's
   payload. Alpha mask EQUAL, alpha stays binary, every VISIBLE
   pixel's RGB EQUAL; but RGB under fully-transparent pixels is
   re-encoded (66% of canvas differs at file level, 0 visible px).
   Same for the interpolation END frame. The validator law: frame
   exactness = alpha-mask equality + visible-RGB equality. The
   first naive diff read "66% changed" and the refined instrument
   cleared it - census over eyeball, at frame scale.
2. **DETERMINISM CONFIRMED**: same seed, same params -> all frames
   byte-identical across two calls. Provenance-safe.
3. **PALETTE HOLDS within curation reach**: walk frames carry 1-6
   stray px each (no strip surface exists on animate_image;
   post-validation quantize is the contract). Interpolation calls
   need a UNION-of-endpoints census (the seated end frame wears its
   own palette - the single-palette instrument false-alarmed).
4. **BASELINE STABLE**: feet on row 31 in all 9 frames; bob <= 1px.
5. **PROFILE SYNTHESIS REFUTED as action text**: "walking, side
   view, facing left" from a front-facing start spends its frames
   TURNING, not striding. LAW: cycles animate the START POSE's
   facing - direction is POSE WORK, not action text. Phase B
   therefore buys west-profile pose variants per extra FIRST, then
   cycles from those poses. (The A2 morph also confirms: real
   sit-downs need same-character seated pose variants as endpoints;
   interpolating across characters swaps identity mid-flight, as
   expected for a contract probe.)
6. **MCP retrieval law**: get_image inlines only the first 4 frames;
   the full set downloads per-index from
   /mcp/images/<job>/download?index=N (direct Bearer works - no
   redirect trap on this endpoint). Spend accounting for MCP
   animation calls has no ledger hook; ~3 gens estimated by the
   32x32x8 pixel budget, vendor dashboard the authority (the
   probe-1 situation, unchanged).

VERDICT: Tier 2 is VIABLE. Phase B (street life) proceeds pose-
variants-first on the board's word.

THE FAR-LINE A/B (0 gens; census first - and it caught my own
premise): the flag as recorded UNDERSTATED the difference. The
builder draws a STEPPED read - line (140,129,112) = OH walk tier 2
under a paler far walk (186,174,152) = tier 4; the composer draws
line AND far walk in one uniform pale (206,192,162) = walk tier 4 -
no edge at all. (The v9 record's phrase "pale top edge" never
matched the builder's actual pixel - the two-authorities smell was
also a paper-vs-pixels drift.) Same-frame A/B built by exact-color
swap (farline_ab.png). RECOMMENDATION: name the BUILDER'S stepped
read, recorded as TIER LAW - far curb line = walk[1], far walk =
walk[3], register-aware so every district inherits its own tones.
Hero is already lawful (NO re-bake, reference sha untouched);
the district composer re-bakes Moretti's/Vinnie's as recorded
by-design diffs confined to rows 344-359. AWAITING THE NAMED
WINNER.

University Hill (item 3) opens next round, paper first: location
proposal + neighbor briefs before any staging file.

## The deferral round: the far line ruled and derived, the gate
## probed, the debts paid (2026-08-12 session F cont.; board: "Pause
## now to reflect. I defer to you. Proceed as you best see fit";
## 6-step reflection, 2 gens)

Decisions taken UNDER DELEGATION, recorded loudly and cheap to
reverse:

1. **THE FAR-LINE RULING: the stepped read wins.** The line is the
   shadow seam at the far curb's foot - dark asphalt, the seam, the
   lit walk behind; the hero's fourteen-round ratified read, and the
   A/B's most legible frame. Now LAW: `far_line_tone(walk_ramp) =
   walk[1]` in street_block.py, test-pinned (hero value + register-
   awareness + darker-than-walk-top articulation). BOTH renderers
   DERIVE from it - the smell was never color, it was two hardcoded
   voices with no shared home. Proofs: hero re-baked under the
   derived law BYTE-IDENTICAL (reference sha 5d19e406... unchanged -
   the law captured the ratified read exactly); districts re-baked
   as by-design diffs of EXACTLY rows 344-347 (2,560 px each) -
   boards morettis_block_v5 / vinnies_block_v8 supersede. THE CATCH
   THE DERIVATION SURFACED: the composer's hardcode was LS cream
   CITYWIDE - the Meadows' violet-gray far street wore a Little
   Sicily line until this law; it now speaks (120,118,136), its own
   walk[1].
2. **The instruments became law code**: animation_validate.py
   (composite_exact - the probe's 66% false alarm as a pinned test;
   binary_alpha; union-palette census - the a2 lesson pinned;
   baseline_rows; frame_delta) + test_animation_validate.py. Suite
   145 -> 151, ruff clean.
3. **PHASE B GATE PROBED (2 gens, profile_pose_probe.py)**: anchored
   @100 REFUSED (8% grain, still front-facing - the clean-anchor
   refusal holds for figures at low strength); FREE generation under
   the sprite's own 6-color strip LANDED a true left profile
   (correctly narrower, hair/sweater right, 0 off-strip). One
   defect, curation-scale: the strip's burgundy landed on the
   trousers ("gray trousers" in the desc lost) - region-scoped
   exact-color reassignment is the recorded fix. VERDICT: the free
   route is the pose recipe; the 7-extra batch rides next round,
   cycles after poses.
4. **Probe provenance written** (e16_animation_probe_2026-08-12
   .json: job ids, params, verdicts, 23 frame hashes) - the billing
   history says job ids matter.
5. **THE SINGLE-COPY DEBT, STOPGAPPED**: .private_art (58M, now
   holding every promoted asset and record) tarred to
   ~/Desktop/Projects/Extra-Toppings-backups/private_art_2026-08-12_
   session-F.tar.gz (35M, 3,778 files) - a second copy on the SAME
   disk converts one deletion from zero into two, and is NOT a
   backup; the off-machine copy remains the user's call, re-flagged.

Session F spend: 16 gens ledgered (4 drift + 2 cracks + 8 neighbors
+ 2 profile poses) + ~3 MCP-estimated (no ledger hook); expected
balance ~4,091 by estimate.

## Phase B run: the crowds get their legs (2026-08-12 session F
## cont.; board: "Perfect, proceed"; 24 gens ledgered + 9 MCP
## estimate rows)

THE POSE CAMPAIGN (16 gens, three rounds + squash fallbacks - the
full ladder recorded in recipes profile_pose_batch{,_r2}.py):
- r1 (12 gens, free route, own-palette strips, garments named from
  the census sheet): women LANDED (s17211/s17221, stature lawful);
  docker/cop FAILED on garment coverage; elder/kid FAILED ON
  STATURE (24->30, 23->31) - the free route pulls figures to fill
  the canvas, and "32x32 sprite" language feeds it.
- r2 (8 gens, proportion + coverage language, canvas phrase
  dropped): docker s17234 and cop s17244 PICKED at source stature.
  The elder came back STOOPED and right - CARRYING A CANE in both
  seeds: my own "cane-free" in the description planted the token
  (the negation lesson, paid again in a new form). The kid refused
  smallness twice - proportion language moved vehicles but not
  children.
- r3 (3 gens): elder re-rolled cane-less (word absent, negatives
  armed) - still tall; SQUASH+REPAIR (the wagon/manhole mechanism)
  landed BOTH stature failures exactly: kid h24 (s17265 via the
  s17263 body squashed non-integer to source stature, repair @150),
  elder h24 (s17257 via s17256). THE LAW EXTENDS: the repair
  mechanism holds proportion for FIGURES too - stature that
  language cannot buy, the squash buys deterministically.
- Curation (recorded, censused): man_cream trousers 50 px burgundy
  -> gray (the gate probe's known drift); kid hair 50 px + fringe/
  shorts 17 px navy -> black. FINAL SET: seven west profiles
  staged (candidates/profile_poses/final/), all 0 off-strip, all
  within 1 px of source stature. Mirror law buys east free.

THE CYCLES (9 MCP jobs: 7 walks x 8 frames from the west poses +
2 seated idles x 4): submitted async - and the 10-job concurrency
belief became a MEASURED FACT (rate limit at 10/10; the batch
recipe now submits under the cap). Validated by the law module:
- frame-0 composite-exact 8/8... except the kid at ONE PIXEL - the
  n=3 probe said exact, the n=9 batch found the violation. LAW
  AMENDED: frame 0 is ALWAYS OURS - the stored pose replaces the
  vendor's frame-0 copy at bake; the class is neutralized.
- binary alpha 9/9 clips; baselines stable (29-30); off-palette
  drift 0-25 px/frame, ALL near-tone blends - curation-quantized
  to the union palettes (159 px total across all clips; frame 0
  restored verbatim; curated/ set is the candidate).
- Loop seams (delta last->first vs inter-frame mean): clean on the
  women/kid/seated, ~2x on man_cream/docker/seated_b - flagged for
  the eyes pass at speed; playback order is f1..f8 looping (frame
  0 is the standing pose, not part of the cycle).
EYES VERDICTS: man_cream, elder (a genuinely stooped shuffle),
docker, kid and both seated idles READ; woman_burgundy grows
waist-length hair mid-cycle (flag - one re-roll candidate);
woman_pale FADES to all-navy (identity fail - re-roll next round).
THE COP JOB sits at 46% with a static ETA (~30 min) - recorded
PENDING, possibly the stalled-job class; re-polled next round,
re-queued if dead. Provenance: jobs.json + ledger estimate rows
(mcp_estimate kind - the MCP surface has no ledger hook; two job
ids were lost to a poll timeout and are marked as such).

Session F totals: 40 gens ledgered (4 drift + 2 cracks + 8
neighbors + 2 profile probe + 24 pose campaign... [16 poses + 8
r2]) + ~12 MCP-estimated (3 probe + 9 cycles); expected balance
~4,055 by estimate; vendor dashboard the authority. AWAITING THE
BOARD: the pose set + cycle candidates (strips and GIFs
presented), the woman_pale/woman_burgundy re-roll word, the cop
resolution; University Hill paper next.

## The durability round: the animation class made rebuildable
## (2026-08-12 session F cont.; board: "establish a lasting pipeline
## and durable assets"; 3 MCP re-rolls)

THE SET COMPLETED: the stalled cop job resolved as FAILED
vendor-side ("Generation timed out" - the dead-job class measured;
whether it charged joins the billing evidence) and re-queued
(s17331, landed); woman_burgundy re-rolled clean (s17322 - the hair
holds); woman_pale re-rolled (s17321) and still weakest - ROOT
CAUSE IS THE POSE (s17221's pale top is barely present; the cycle
inherits what the pose lacks). Flagged: re-pose with coverage
language next round, then re-cycle. Rejected raws preserved under
rejected/ before every re-download. 8 of 9 clips read.

DURABILITY, the actual deliverables:
1. **The finishing recipes** (pose_finishing.py, cycle_finishing.py)
   - every inline curation from the Phase B loop now rebuilds
   final/ and curated/ from raws DETERMINISTICALLY; both proven
   byte-identical on re-run. The class of loss that killed the v14
   compose cannot reach this work.
2. **THE ANIMATION MANIFEST** (build_animation_manifest.py ->
   animation_manifest.json, 9 clips): pose + frames + sha256 per
   file + playback law (frame 0 is the pose; loop plays 1..n-1 at
   120ms) + mirror law + per-clip provenance (jobs, seeds, re-roll
   notes, the two ids lost to the poll timeout marked as such).
3. **validate_animation_manifest** in animation_validate.py: REFUSES
   unknown kinds, missing mirror law, out-of-range loops, sha
   mismatches, missing files, non-binary alpha, and frame-0-not-
   the-pose (re-runs the composite-exactness instrument at binding
   - the validator IS the frame-0 law's enforcement). Test-pinned;
   suite 151 -> 153, ruff clean.
The engine story: Godot consumes the manifest (frames as
AnimatedSprite2D at duration_ms, flip_h for east); static-frame
import fidelity rides on the block proof's precedent (same import
pipeline, binary alpha); a living walking-extra scene demo is the
next round's presentation piece, not a fidelity gap.

Promotion shape ON THE WORD: manifest + curated frames + poses
enter approved/animations/ as one unit (validator binding at
promotion, per the transitions law); woman_pale rides flagged or
holds back - the board's call.

Session F totals: 40 gens ledgered + ~15 MCP-estimated (12 prior +
3 re-rolls); expected balance ~4,052 by estimate; dashboard the
authority.

## University Hill: the paper (2026-08-12 session F cont.; location
## proposal + neighbor briefs, 0 gens - AWAITING THE RULING)

THE DATA GROUNDS THE LOCATION (data.py): University Hill is
"students, all-nighters, cash-poor and hungry" - the city's HIGHEST
traffic (1.3), second-highest underground (1.4), no rival, truffle
bias 0.5 against oregano 1.4 / mushrooms 1.3. The district that
orders the most pizza and pays the least per pie. PROPOSAL: the
block anchors THE CAMPUS-GATE STRIP - the late-night commercial
face where the university meets the city, DiNapoli's highest-volume
delivery zone. Scene role: delivery destination; the street that is
awake at 2am.

SLOTS AND NAMES (censused against the tree and the glyph set;
rejections recorded):
- CENTER: **CAMPUS BOOKS** (the institutional anchor - a university
  bookstore; tall pale-slate front, stacked spines in the windows
  via the code-goods route, the register's cold voice at its
  fullest). Rejected: THE STACKS (reads as a bar), HILLSIDE BOOKS
  (place-name collides with no district name - weaker than the
  plain institutional read).
- WEST FLANK: **COMMON GROUNDS** (coffee house - the all-nighters'
  fuel; the block's one warm-adjacent note, kept modest: warm light
  BEHIND cool glass per the glass law, chalkboard menu as code).
  Rejected: THE PERCOLATOR (gadget-cute against the theme).
- EAST FLANK: **QUICK COPY** (copy shop - deeply 1990s campus:
  fluorescent pale glass, taped posters in the window tying into
  the decal class's poster lineage). Rejected: COPY KING (crown
  iconography implies an emblem nobody ruled).
DRESSING LAWS: no awnings (Moretti's signature stays his);
UNIVERSITY DECAL ROSTER = decals: [] RECORDED (pristine BY DESIGN,
not unconsidered - the grading law's fourth reading); the accent
slate-cyan stays off signage per the institutional-cyan
reservation... the register's own accent tiers carry the trim.
Extras: the kid and man_cream walk here naturally; a student
wardrobe variant is the crowd round's future item, not this
block's blocker.

BUILD SHAPE when ruled: staging-v3 instance + the generic composer
(0 new mechanisms); facades = the LS-neighbor recipe chain
(textured scaffold, no_background=False, register strip, @120, 2
seeds each, ~6 gens); Godot proof rides with promotion per
precedent. AWAITING: the location ruling and the three names.

## Promoted; the street proven alive; the set completed
## (2026-08-12 session F cont.; board: "Proceed"; 4 gens + 1 MCP)

THE PROMOTION (provenance e16_animation_promotion_2026-08-12.json):
approved/animations/ is the single home - 8 clips (6 walks + 2
seated idles), poses + curated frames + the manifest with
approved-relative paths, re-hashed and VALIDATOR-BOUND at promotion.
WOMAN_PALE HELD BACK by delegated call, stated plainly: promoting a
known-weak identity contradicts quality-first.

THE HOLD PAID OFF - her arc completed the full loop: re-pose with
coverage language (s17223: the blouse landed at 21% of visible px -
and the strip's pale ALSO claimed her face and h32 canvas-fill);
squash+repair to h28 with face guidance (s17225); curation 8 face
px pale -> skin (recorded in pose_finishing.py - the recipe rebuilds
her too); cycle v2 (s17323/job a3459f38) - the blouse HOLDS across
all frames, validators clean (f0 exact, alpha binary, baseline 30
flat, loop 115 vs mean 56). 9/9 clips now read. Her pose + clip are
CANDIDATES at the board - one word joins her to approved/animations.

THE STREET PROVEN ALIVE, engine-real: a new capture project
(godot_preview_anim/, main.gd driving poses DETERMINISTICALLY -
one capture per posed frame, no timers) played two PROMOTED cycles
on the staged hero block: man_cream westbound native-facing, the
elder eastbound via flip_h (the mirror law in the engine's own
hands). 16 live viewport captures -> street_alive_demo.gif. The
crowds are no longer statues, and the proof is Godot's, not the
compositor's.

UNIVERSITY HILL PAPER is above, awaiting the location ruling and
the three names (CAMPUS BOOKS / COMMON GROUNDS / QUICK COPY).

Session F totals: 44 gens ledgered + ~16 MCP-estimated; expected
balance ~4,047 by estimate; dashboard the authority.

## "Is her walk convincing?" - measured, no, then made so
## (2026-08-12 session F cont.; board question; 1 MCP gen)

The board's question exposed a grading gloss, owned plainly: my
"the blouse holds" verdict graded IDENTITY and glossed MOTION. The
measurement answered the actual question:

THE STRIDE METRIC (new instrument - foot-spread oscillation: the
x-extent of the bottom 3 content rows per frame; a truestride
alternates contact/passing/contact): man_cream oscillates range 8,
woman_burgundy range 7 - and woman_pale's v2 cycle measured RANGE
3, feet never separating. She GLID with shimmer; motion-zone census
agreed (legs 31% vs the others' 40-41%). And the skirt excuse died
by comparison: woman_burgundy wears the same long skirt and
strides.

THE FIX (1 gen, seed 17324, job 5cdfcabe...): the probe's law
applied - ACTION TEXT DRIVES MOTION CHARACTER - so the action
named the gait explicitly ("long visible strides, feet stepping
far apart, legs swinging, skirt swaying with each step"). v3
measured: oscillation RANGE 8 (equal to man_cream, the set's
best), loop seam improved (1.4x vs the glide's 2.1x), validators
clean, identity intact. Eyes agree: the skirt breaks into stride,
the back foot trails. The glide cycle is preserved in rejected/.

LAW NOTED for the module when Phase C opens: the stride metric
joins animation_validate as a measured helper - walks are GAIT-
CENSUSED before the eyes pass, not after the board asks.

Session F: 44 gens ledgered + ~18 MCP-estimated; expected balance
~4,045 by estimate. Her pose + v3 cycle are the CANDIDATES.

## Woman_pale joins; the stride metric becomes law; University Hill
## stands (2026-08-12 session F cont.; board: "Great work. Proceed";
## 6 gens)

WOMAN_PALE PROMOTED on the word: approved/animations is 9/9 clips.
One catch paid before it settled: the first re-promotion carried
STALE PROVENANCE (v2's seed/job under v3's frames - the re-hash
was correct, the story wasn't); the manifest builder's record was
corrected to describe the actual frames (v3 s17324, both rejects
noted) and the promotion re-run. THE STRIDE METRIC IS LAW:
stride_range() in animation_validate with the glide-vs-stride
test pinned (suite 153 -> 155) - walks are gait-censused before
the eyes pass from Phase C on.

UNIVERSITY HILL BUILT on the papered ruling (6 gens, recipes
uh_facades_r1 / uh_brand): all three fronts LANDED ROUND 1 on the
accumulated laws - textured shells, white-mix mottle, coverage
descriptions, no_background=False, 0 off-strip all six seeds,
88-96% repaint. Picks: campus_books s17401 (17402: edge
artifacts), common_grounds s17411, quick_copy s17421. Brand layers
code: three signs, the chalkboard easel prop, and A GLINT-LAW
REFINEMENT recorded: sky-catch lands on DARK glass only - the copy
shop's fluorescent window is lit from within and outshines any
reflection.

THE STAGING (candidates/university_block_staging.json, validator
PASS) paid two laws forward in one authoring pass:
1. The chalkboard's first placement sat in the lamppost's curb
   x-slot and validate_scene_staging REFUSED it - the law caught
   what the eye placed; moved to the door's east pier.
2. The first draft invented a COOL UH gutter pan and yellow curb;
   the cross-staging census caught the infrastructure violation -
   curb concrete, lane paint and hydrant yellow are CITYWIDE (the
   flagged ruling stands); constants restored, verified in pixels.
The roster is decals: [] BY DESIGN - the grading law now reads
across all four districts: Meadows dirtiest / OH moderate / LS
swept / UNIVERSITY PRISTINE. university_block_v1 is the scene
candidate; its Godot proof rides with promotion per precedent.

Session F: 50 gens ledgered + ~18 MCP-estimated; expected balance
~4,039 by estimate; suite 155; ruff clean.

## The signage differentiated: three sign technologies (2026-08-12
## session F cont.; board: "Differentiate some of the signage in
## University Hill"; 0 gens - all code)

The board's catch was real: all three fronts wore ONE sign voice
(scale-2 cream over ink shadow, identical layout) - three
businesses, one sign shop. The house's own precedents differentiate
by SIGN TECHNOLOGY, not just words (Vinnie's bulk scale-3, the
Orchid's blade + letterboard, Moretti's awning subline) - applied
in the cold register, uh_brand.py rebuilt:
- **CAMPUS BOOKS = CARVED STONE**: dark incised letters (storefront
  tier 2) with a pale top-edge highlight, NO drop shadow - the
  inscription reads cut into the masonry; plus a stacked **BOOKS
  blade** on the east pier (the Orchid's blade precedent) in accent
  cyan on a dark board - the block's silhouette breaks.
- **COMMON GROUNDS = PAINTED BOARD**: a dark sign board behind
  cream letters with a code steaming-cup pictogram; COFFEE subline
  in accent cyan (first pass sank into the fascia - ink shadow
  restored its edge).
- **QUICK COPY = 90s TWO-TONE CHANNEL**: QUICK in accent tier 3,
  COPY in cream (the first pass used tier 4 and the zoom read it
  as near-cream - one tier darker bought the contrast).
The accent slate-cyan is signage's LAWFUL home - the institutional-
cyan reservation explicitly governs signage and signals. Census:
v1->v2 diff 6,179 px confined to rows 62-138 (fascia + blade).
university_block_v2 supersedes v1 as the scene candidate.

## The reflection: good direction, bad implementation - THE
## SIGN-SURFACE LAW (2026-08-12 session F cont.; board's catch;
## 0 gens, 4-step reflection)

The board approved the three-technology direction and rejected the
execution, and the reflection found the root in one sentence: I
differentiated the LETTERS but left them raw on noisy generated
masonry. Every strong sign in this project already sat on its own
surface (DiNapoli's red board, Vinnie's whitewash field, the
Orchid's marquee) - UH's mottled fascia was the first NOISY wall
the lettering ever landed on, which is why the failure appeared
here first. Element verdicts, owned: the grounds board was fitted
edge-to-edge with no margins (a black bar, not a mounted sign);
the cup pictogram at 9px was below the readable-icon threshold (a
smudge); the "carved" top-edge-peek read as ghosting/double-strike,
on speckle that ate its contrast; the two-tone sat raw on the same
noise; the blade letters touched their frame.

**THE SIGN-SURFACE LAW, recorded: A SIGN IS A SURFACE PLUS LETTERS
- lettering never lands raw on generated wall texture. Every sign
is a smooth code surface first (board, frieze, panel), THEN its
letter treatment.**

v3 (all code): CAMPUS BOOKS = inset dressed-stone FRIEZE
(architrave rules) with the name carved DEBOSSED (dark letters,
pale +1+1 shadow - light catching the lower cut face); the
TEXTBOOKS subline died in round 2 of the reflection (two lines
never fit a 22px band at these scales - it slid off the frieze;
the blade and the spine windows carry the rest). COMMON GROUNDS =
a properly MOUNTED board (inset, wall visible above and below),
the name alone (cup and subline killed). QUICK COPY = the 90s BOX
SIGN - a bright panel echoing its fluorescent window, QUICK in
accent tier 2 + COPY in ink ON the panel (subline killed; the
poster window carries the utility read). Blade widened, letters
gapped. Census v2->v3 confined to the fascia band.
university_block_v3 supersedes v2 as the scene candidate.

## University Hill promoted; THE DISTRICT GODOT PROOF closes a
## standing debt (2026-08-12 session F cont.; board: "Great work.
## Proceed"; 0 gens)

THE PROMOTION (provenance e16_university_promotion_2026-08-12
.json): the three facades + the chalkboard entered approved/ with
sha256s; approved/university_block_staging.json IS the v3 stack
(slot paths re-pointed, validator PASS, candidate retired);
re-render from the approved staging BYTE-IDENTICAL to the
board-approved v3.

THE DEBT, named and closed: the Godot proof was promised at
Moretti's promotion ("rides with its promotion") and never ran -
the promise had gone unpaid through THREE district promotions. This
round built the proof generically and ran it on all three:
- compose() extracted from the composer (staged-only switch,
  behavior-identical - triple board regression BYTE-IDENTICAL);
- a SPRITE SINK: props become engine sprites, their contact shadows
  stay flattened in the base (the hero's bake law). The first
  export FAILED ITS OWN SELF-CHECK and the pixel arithmetic found
  why: shadows landing UNDER the tree-well grates - which forced
  the right design call: WELLS ARE GROUND, not standing sprites
  (an iron grate lies IN the pavement); routed to the base, the
  law's paint order is preserved exactly;
- the self-check law: the layered export must equal the law render
  byte-exactly BEFORE anything is exported;
- a generic godot_preview_district project (one main.gd reading
  layout.json; district named in district.txt).
**RESULTS: Moretti's 0/230,400; Vinnie's 0/230,400; University
0/230,400 (re-run from the APPROVED staging after promotion).**
Every district block is now engine-real under the same standard as
the hero.

Session F: 50 gens ledgered + ~18 MCP-estimated; expected balance
~4,039 by estimate; suite 155; ruff clean.

## Session G opens: drift Tier B, and a correction to session F's
## suite count (2026-08-12 session G; 4 drift gens)

DRIFT HARNESS (session_G_street_shelf, run session_2026-08-12_G):
probe_canon_pizza Tier B diff=0.0967 histL1=0.0420; probe_box_open
Tier B diff=0.1230 histL1=0.0625; probe_slice_bitforge Tier A
byte-identical; probe_palette_canary Tier B diff=0.2061
histL1=0.0898; all validators pass. OVERALL Tier B - clear to
generate.

CORRECTION, owned: session F recorded "suite 155" (twice above, and
"153 -> 155" at the stride pin). The committed head 546e876 runs
**154**. Decomposed against the tree: the stride-pin commit aaa70eb
added exactly ONE test (test_glide_vs_stride); its parent d2ee031
runs 153, aaa70eb and 546e876 run 154; no test file changed after
aaa70eb. The 155 was a miscount at recording time, not a lost test.
The three "155" records above stand as written - this entry is the
correction. The suite of record at session G open: **154 tests, OK;
ruff clean.**

## Street shelf (a): the cool-glass pass on Anchor Diner + Rossi's -
## candidates + A/B (2026-08-12 session G; board ruling: shelf first;
## 0 gens - all code)

The glass ruling's standing flag is paid, candidate-first
(recipes/streetshelf_coolglass_ab.py; provenance
e16_streetshelf_coolglass.json). Mapping in facade v2's exact
vocabulary, no new tones: zone-scoped glass FIELD (46,42,38) ->
MIDNIGHT (48,59,90) - these are dark unlit fronts, so the darkest
cool tone carries the field where Moretti's lit displays took slate;
the hero stays the block's most alive glass. GLINTS DRAWN, NOT
INHERITED: one sky-catch streak per bay in Moretti's censused 18px
form (diner panes 3/3 symmetric at +52 from each window origin;
Rossi's lower-left pane).

CONTENT-PRESERVED judgments, flagged for the ruling:
- the diner's (74,68,58) blobs are interior pendant-lamp silhouettes
  - KEPT warm (warmth behind cool glass, the Moretti's read);
- Rossi's (74,68,58) inside the window IS its muntin grid (cols
  25/66, row 50, censused) - frame structure, never mapped;
- DOORS untouched (Moretti's precedent mapped bays only) - the
  diner's dark door glass stays sepia pending its own word.

NUMBERS: diner 5,025 field px mapped + 36 glint px (diff exactly
5,025, zones only; palette gains only MID+SKY); Rossi's 3,112 + 18
(diff 3,112, zones only). IN-SCENE, composed from data: a PATCHED
BUILDER COPY (facade paths -> candidates, PROJ -> scratch - the
standing proof project untouched, its reference verified 5d19e406...
before comparing) rebuilt the block; diff vs the standing reference
7,787 px, all inside the 8,137-px facade zone footprint (350
occluded by staged props). The in-scene A/B is the payload: the
flanks stop reading as dead sepia voids beside DiNapoli's sky-lit
displays; three fronts share one glazing family; the hero keeps its
dominance.

FLAGGED alongside, found during the pass:
1. **Builder read-path smell**: builder.py loads the diner from
   candidates/bespoke_facades/ (line 207), not approved/ - the
   copies are byte-identical TODAY (both e0274b76...), so it is
   latent, but the read path should be approved/; the one-line
   re-point rides with the promotion re-bake if this pass is ruled
   in.
2. **The upper-story band stays sepia code glass** - out of this
   ruling's scope, but after this pass it is the block's only warm
   glazing; extending the cool law to the band is its own small
   round (re-bakes every district block) if the board wants it.

AWAITING THE WORD: the two candidates (promotion = approved/ swap +
hero re-bake + Godot proof + reference-sha change recorded
by-design), the two content judgments, the door question, and the
two flags. Boards: coolglass_ab_diner, coolglass_ab_neighbor,
coolglass_inscene_{mock,board}. Session G spend: 4 gens (drift
only).

## Cool-glass PROMOTED; Rossi's gets its groceries (2026-08-12
## session G cont.; board: "Proceed! Looks great. Maybe some
## groceries in the window though?"; 2 gens)

THE PROMOTION (provenance e16_coolglass_promotion_2026-08-12.json):
both cool-glass facades entered approved/ (diner 300d2f1a...,
neighbor e934fc1a...; sepia raws preserved in candidates/
bespoke_facades/, byte-verified before the swap). The builder
read-path smell CLOSED: builder.py diner load re-pointed
candidates/ -> approved/. Hero re-baked; the promoted reference is
BYTE-IDENTICAL to the candidate in-scene run the board approved
(0 px diff) - reference sha 5d19e406... -> **74dbdea2...** by
sanctioned ruling. **GODOT PROOF 0/230,400** (import law observed;
the Godot binary lives at ~/Applications/Godot.app, not
/Applications - recorded for the next session). Board v26 stands.
The content judgments ride as ruled with the approval (lamp blobs
warm, muntins unmapped, doors sepia); the upper-band flag stays
open.

THE GROCERIES (board's ask; the Moretti's-r8 code-goods chain,
recipes rossis_groceries_r1.py + _finish.py, provenance
e16_rossis_groceries.json):
- SCAFFOLD (eyes-judged before spend): crude code goods in raw
  color on the SEPIA raw (raw-in law) - can pyramid with red label
  bands, CLOSED crates (the interim-debt law: solid faces, thin
  seams), burlap sacks, shelf board; goods fill the BOTTOM pane row
  only. Strip mints NOTHING: the facade's 6 tones + brick red
  (124,66,52) + cream (198,182,156), both long-standing block
  colors.
- GENERATION (2 gens, s17501/s17502, @120): both 0 off-strip, and
  the change CONCENTRATED where it should - 665/797 and 701/835
  changed px inside the goods zone (not the grain-refusal class:
  the model refined the goods). **s17501 PICKED** - its crates keep
  the red on the can labels; s17502's brick-red crates compete.
- THE CENSUS REFUTED MY EYEBALL TWICE IN ONE ROUND, recorded: (1)
  I graded s17501's crates "muted gray-brown" - region census says
  (96,82,68)+seams with ZERO field px; (2) I then read the final's
  crates as "gone navy" - the navy was the mapped GLASS behind and
  between them, which is correct behavior. Census over eyeball, at
  goods scale.
- FINISHING (deterministic): the generation grained ~123 wall px
  outside the window (the confinement assert caught it) -> SURGICAL
  COMPOSITION: approved cool-glass base + the generation's WINDOW
  ZONE only; 1,803 remaining field px -> midnight; the glint
  re-lands in the clear TOP pane (30,47) (goods claimed the old
  lower-left position); muntin grid asserted intact; palette
  asserted <= strip + the two cool tones.
- IN-SCENE (patched builder in scratch): diff vs the promoted
  reference 1,426 px, ZERO outside the window footprint. The read:
  Rossi's stops being an empty dark front - the stock reads at 1x,
  the shop looks occupied, the glass above stays cool.

candidates/rossis_groceries/groceries_s17501_coolglass.png is the
CANDIDATE - nothing promoted; promotion = approved swap + hero
re-bake + Godot proof + by-design sha change, on the word. Boards:
rossis_groceries_ab, rossis_groceries_inscene_ab. Session G spend:
6 gens (4 drift + 2 groceries); expected balance ~4,033 by
estimate; dashboard the authority.

## The window survey: every district's glass graded (2026-08-12
## session G cont.; board question: "Do any of the other windows in
## any of the districts need props for polish?"; 0 gens - survey
## only)

Every window on all four blocks censused and eyes-graded
(review/window_survey_2026-08-12.png shows the offenders).

DRESSED, no action: DiNapoli's (sky-lit displays); Moretti's (lit
shelves + glints); PALERMO's loaves (content EXISTS - the queued
loaf-crust round is an accent fix, not a dressing fix); DE LUCA
(cafe curtain + pole tell the story; a chair silhouette is optional
and recommended AGAINST); CAMPUS BOOKS (spine windows read);
QUICK COPY (taped posters, deeply 90s); the Orchid (poster cases,
letterboard, blade); Meadows east flank (boarded BY DESIGN); upper
bands (the Meadows census by design; LS band is already the queued
lum-map interim - curtain/shade variety can ride that round).

NEEDING POLISH, priced, in priority order:
1. **COMMON GROUNDS (UH) - the weakest window standing**: the
   "warm light behind cool glass" intent landed as a FLAT
   warm-brown void ((92,84,72) + sepia dark, one glint, zero
   content). The code-goods chain fits exactly: counter/cup-shelf/
   pastry-case silhouettes in raw color, repair pass, ~2 gens.
2. **ANCHOR DINER (OH)**: two wide midnight bands carry only the
   lamp silhouettes - the largest empty glass on the hero block.
   Period dressing: cafe HALF-CURTAIN band (code - the De Luca
   precedent) + counter items via code-goods (~2 gens; a
   curtains-only code round costs 0 and can be judged first).
3. **VINNIE'S (Meadows) - a defect against its own brief, not a
   dressing ask**: the brief says "one dark window low in the
   GLASS RAMP"; the standing pixels are PURE BLACK holes ((0,0,0)
   1,801 px + (20,18,24) 511). The emptiness is thematic and
   STAYS; the fix is code-only (0 gens): lift the openings to the
   Meadows glass-ramp low tier with a faint frame so they read as
   dark glass, not missing pixels.

AWAITING THE WORD on: which of 1-3 proceed (each candidate-first
with A/B per the standing method), the loaf-crust round's slot
unchanged - AND the Rossi's grocery candidate above still awaits
its own explicit word. Spend unchanged: 6 gens.
