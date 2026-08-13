"""The interior scene unit — the street template's indoor sibling.

Paper: art_specs/experiment_16_street.md, "THE HORIZON — THE
SERVICE-COUNTER INTERIOR" (2026-08-12 session H). The unit carries
the street grammar verbatim — flat-on, native 32, content-bottom
anchoring, painter order by base row, staging AS DATA — and this
module holds the unit's INVARIANT laws, exactly as street_block.py
holds the street's. Validation REFUSES, never repairs.

The six-band row law (the street's eight-band analog): ceiling /
back_wall / wall_base / work_floor / counter_run / customer_floor,
contiguous from row 0, summing to 360. Two attachment lines: the
WALL LINE (fixtures that belong to the building — oven, prep, box
stacks — base inside the work-floor band) and the COUNTER LINE (the
indoor curb: the service boundary; counter pieces anchor here, staff
north of it, customers south). The core loop's geometry is DATA:
the entry corridor, the ordered queue slots, and the counter PASS
GAP are first-class staging fields, and the validator refuses a
scene whose loop cannot physically run — the crosswalk-corridor
refusal, indoors.
"""
from __future__ import annotations

INTERIOR_BANDS: tuple[str, ...] = (
    "ceiling", "back_wall", "wall_base",
    "work_floor", "counter_run", "customer_floor",
)
SCENE_WIDTH = 640
SCENE_HEIGHT = 360
KNOWN_FLOORS = frozenset({
    "floor_terracotta", "floor_checker_cream", "floor_parquet",
})
DECAL_TYPES = frozenset({"flour", "cut"})
OVEN_STATES = frozenset({"lit", "cold"})
# Minimum clear width for a 32px figure to pass (content width, not
# canvas): the pass gap, the entry corridor and queue spacing all
# hold this bar so the loop can physically run.
FIGURE_CLEAR = 24
QUEUE_SPACING_MIN = 20

# ---------------------------------------------- the interior scale law
# Ruled 2026-08-12 (session H, the too-small reckoning): ARCHITECTURE
# runs dollhouse-big (bands, walls - the street's 96px storefronts);
# INTERACTIVE FIXTURES track the person. Anchors, all measured: the
# 30px person canon, the E15 table convergence (1.07x, WITH sitters),
# the vehicle lane law (~1:1 cars), the street's ~1.3x doors. Content
# heights, not canvases; the census runs at PICK time (with the
# alpha-hole census) before any prop enters a final/ set.
PERSON_CONTENT_H = 30
FIXTURE_SCALE_MAX = {
    # class -> max lawful content height as a multiple of the person
    "upright": 1.5,     # doors, cabinets, machines, cans, ovens
    "deep_top": 1.4,    # counters, tables (foreshortened-top inflation)
    "hand_prop": 0.6,   # registers, pies, phones - things hands use
}


def fixture_scale_verdict(content_h: int, kind: str) -> str:
    """OK or OVERSIZED under the interior scale law."""
    limit = FIXTURE_SCALE_MAX[kind] * PERSON_CONTENT_H
    return "OK" if content_h <= limit else "OVERSIZED"


def _spans_overlap(a, b) -> bool:
    return not (a[1] < b[0] or b[1] < a[0])


def _span_ok(span) -> bool:
    return (isinstance(span, (list, tuple)) and len(span) == 2
            and all(isinstance(v, int) for v in span)
            and 0 <= span[0] < span[1] <= SCENE_WIDTH)


def validate_interior_staging(staging: dict) -> list[str]:
    """Every violated law, as strings; empty means lawful."""
    errs: list[str] = []
    if staging.get("schema_version") != 1:
        errs.append("schema_version must be 1")

    # ---- the six-band row law
    bands = staging.get("bands", {})
    if tuple(bands.keys()) != INTERIOR_BANDS:
        errs.append(f"bands must be exactly {INTERIOR_BANDS} in order")
        return errs  # nothing below is checkable without lawful bands
    cursor = 0
    for name in INTERIOR_BANDS:
        pair = bands[name]
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                or pair[0] != cursor or pair[1] <= pair[0]):
            errs.append(f"band {name} must be [start, end) contiguous from {cursor}")
            return errs
        cursor = pair[1]
    if cursor != SCENE_HEIGHT:
        errs.append(f"bands must end at {SCENE_HEIGHT}, got {cursor}")

    # ---- the two attachment lines
    wall_y = staging.get("wall_line_base_y")
    wf = bands["work_floor"]
    if not (isinstance(wall_y, int) and wf[0] <= wall_y < wf[1]):
        errs.append("wall_line_base_y must sit inside the work_floor band")
    counter_y = staging.get("counter_line_base_y")
    cr = bands["counter_run"]
    if not (isinstance(counter_y, int) and cr[0] <= counter_y <= cr[1]):
        errs.append("counter_line_base_y must sit inside the counter_run band")

    # ---- floors are data
    floors = staging.get("floors", {})
    for zone in ("work", "customer"):
        if floors.get(zone) not in KNOWN_FLOORS:
            errs.append(f"floors.{zone} must name a known floor")

    # ---- the counter run and its pass gap
    counter = staging.get("counter", {})
    pieces = counter.get("pieces", [])
    piece_spans = []
    for p in pieces:
        span = p.get("span")
        if not _span_ok(span):
            errs.append(f"counter piece span invalid: {span}")
            continue
        for prior in piece_spans:
            if _spans_overlap(span, prior):
                errs.append(f"counter pieces overlap at {span}")
        piece_spans.append(span)
    gap = counter.get("pass_gap")
    if not _span_ok(gap) or gap[1] - gap[0] < FIGURE_CLEAR:
        errs.append(f"pass_gap must be a span at least {FIGURE_CLEAR} wide")
    else:
        for span in piece_spans:
            if _spans_overlap(gap, span):
                errs.append("pass_gap is covered by a counter piece")

    # ---- fixtures: two classes (the pizza-shop build-out ruling,
    # 2026-08-12). "wall" stands on the wall line, x-slot exclusive
    # among floor fixtures; "wall_mounted" hangs on the wall (y_top
    # anchored above the work floor), x-slot exclusive among mounted
    # fixtures ONLY - a hood hangs above its oven, shelves above the
    # makeline, BY DESIGN.
    floor_spans: list = []
    mounted_spans: list = []
    for name, fx in staging.get("fixtures", {}).items():
        line = fx.get("line")
        span = fx.get("span")
        if not _span_ok(span):
            errs.append(f"fixture {name}: invalid span")
            continue
        if line == "wall":
            for prior in floor_spans:
                if _spans_overlap(span, prior):
                    errs.append(f"fixture {name}: overlaps another wall fixture")
            floor_spans.append(span)
        elif line == "wall_mounted":
            y_top = fx.get("y_top")
            if not (isinstance(y_top, int) and 0 <= y_top < wf[0]):
                errs.append(f"fixture {name}: wall_mounted needs y_top above "
                            "the work floor")
            for prior in mounted_spans:
                if _spans_overlap(span, prior):
                    errs.append(f"fixture {name}: overlaps another mounted fixture")
            mounted_spans.append(span)
        else:
            errs.append(f"fixture {name}: line must be wall or wall_mounted")

    # ---- corridors: the loop's geometry
    corridors = staging.get("corridors", {})
    entry = corridors.get("entry")
    if not _span_ok(entry) or entry[1] - entry[0] < FIGURE_CLEAR:
        errs.append(f"entry corridor must be a span at least {FIGURE_CLEAR} wide")
        entry = None
    slots = corridors.get("queue_slots", [])
    prev_y = counter_y if isinstance(counter_y, int) else 0
    for i, slot in enumerate(slots):
        if (not isinstance(slot, (list, tuple)) or len(slot) != 2
                or not all(isinstance(v, int) for v in slot)):
            errs.append(f"queue slot {i} malformed")
            continue
        x, y = slot
        if not (0 <= x < SCENE_WIDTH and 0 < y <= SCENE_HEIGHT):
            errs.append(f"queue slot {i} out of scene")
        if y <= prev_y:
            errs.append(f"queue slot {i} must stand south of the previous "
                        "slot (and slot 0 south of the counter line)")
        elif y - prev_y < QUEUE_SPACING_MIN and i > 0:
            errs.append(f"queue slot {i} closer than {QUEUE_SPACING_MIN}px "
                        "to the slot ahead")
        prev_y = y if isinstance(y, int) else prev_y

    # ---- customer furniture: never in the loop's way
    cf = bands["customer_floor"]
    for name, fu in staging.get("furniture", {}).items():
        span = fu.get("span")
        base_y = fu.get("base_y")
        if not _span_ok(span):
            errs.append(f"furniture {name}: invalid span")
            continue
        if not (isinstance(base_y, int) and cf[0] <= base_y < cf[1]):
            errs.append(f"furniture {name}: base_y must sit in customer_floor")
            continue
        if entry and _spans_overlap(span, entry):
            errs.append(f"furniture {name}: blocks the entry corridor")
        for i, slot in enumerate(slots):
            if (isinstance(slot, (list, tuple)) and len(slot) == 2
                    and span[0] <= slot[0] <= span[1]
                    and base_y - 40 <= slot[1] <= base_y):
                errs.append(f"furniture {name}: swallows queue slot {i}")

    # ---- decals: the work floor wears the flour (grading, indoors)
    for i, d in enumerate(staging.get("decals", [])):
        if d.get("type") not in DECAL_TYPES:
            errs.append(f"decal {i}: unknown type {d.get('type')!r}")
        y = d.get("y")
        if not (isinstance(y, int) and wf[0] <= y < wf[1]):
            errs.append(f"decal {i}: decals live on the work floor only")

    # ---- scene states: the loop as data
    states = staging.get("states", {})
    if "service" not in states:
        errs.append("states must include 'service'")
    for sname, st in states.items():
        if st.get("oven_state") not in OVEN_STATES:
            errs.append(f"state {sname}: oven_state must be lit or cold")
        for i, actor in enumerate(st.get("actors", [])):
            x, base_y = actor.get("x"), actor.get("base_y")
            if not (isinstance(x, int) and 0 <= x < SCENE_WIDTH
                    and isinstance(base_y, int) and 0 < base_y <= SCENE_HEIGHT):
                errs.append(f"state {sname}: actor {i} out of scene")
    return errs
