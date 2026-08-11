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

## Decision 2 — district palette registers (ruling needed)

Extending the crowd wardrobe law to ground and walls: Old Harbor
work-warms + dock grays; Little Sicily cream/oxblood (the family's
own register — home turf reads warmest); University slate/gray (the
one correctly-cold district); the Meadows ink-forward with its
after-dark variant. Each district gets a recorded strip; the union
rule licenses interim picks.

## Decision 3 — the street scene unit (ruling needed)

Proposed composition unit (the four-top precedent — staging as
data): a STREET BLOCK of 640×360 — roadway band, sidewalk bands,
building faces north of the walk, curb transitions, lamppost/hydrant/
crate props, district crowd via `wardrobe_variant` + the walk cycles.
The shop's own block stages first (facade v2 exists); the wagon
drives the roadway band.

## Decision 4 — rival storefronts (ruling needed)

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
