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
