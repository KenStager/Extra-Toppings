"""The street-block laws: derivations, code assets, grounding.

Experiment 16 (art_specs/experiment_16_street.md): the hybrid ruling
— Godot builds maps, Omega donates composition and artwork, PixelLab
renders bespoke native-32 pieces. This module carries the LAWS that
loop earned, as pure functions; the composition itself ships as data
(`street_block_staging.json` beside the private assets). The ramps
here entered as INTERIM picks under the union rule; decision 2
(ratified 2026-08-11) made them Old Harbor's register verbatim and
derived the other districts from them — see DISTRICT_REGISTERS.

Laws carried, with the round that paid for each:
- A2 blob autotiles hide their seamless fill in the inner 8x8
  quadrants of rows 1-2 (v2's striped road).
- Donor SOURCE GEOMETRY that contradicts the flat-on grammar is
  repaired by column-stamp, never by recolor rules (v13's kiosk:
  116 black outline pixels no fill rule could touch).
- Glass is its own recolor channel; near-neutral bright fascia
  pixels flatten to ONE wall tone; sign rows are exempt (v13).
- Every placed object casts a CONTENT-BBOX contact shadow — canvas
  bounds float (v8's wagon).
"""

from __future__ import annotations

from PIL import Image, ImageDraw

RGB = tuple[int, int, int]
Box = tuple[int, int, int, int]  # x0, y0, x1, y1 inclusive

# Recorded interim ramps (union rule; decision 2 ratifies) — dark to light.
ASPHALT_RAMP: list[RGB] = [(41, 38, 34), (46, 42, 38), (50, 46, 41), (54, 49, 44)]
WALK_RAMP: list[RGB] = [(94, 86, 74), (140, 129, 112), (166, 154, 134), (186, 174, 152)]
GLASS_RAMP: list[RGB] = [(46, 42, 38), (58, 53, 47), (74, 68, 58), (92, 84, 72)]
FLANK_RAMP: list[RGB] = [
    (52, 44, 38), (96, 82, 68), (150, 132, 110), (198, 182, 156), (228, 216, 192),
]
SLATE_RAMP: list[RGB] = [(46, 51, 58), (74, 82, 92), (108, 118, 130), (158, 168, 178)]
OXBLOOD_RAMP: list[RGB] = [(84, 32, 28), (122, 44, 38), (158, 62, 50), (196, 96, 74)]
WELL_METALS: list[RGB] = [(58, 54, 48), (76, 70, 62), (94, 87, 76), (112, 104, 90)]

# Citywide curb concrete, censused verbatim from approved curb s16102
# (dark to light: base shadow, face, transition/joint, wear speckle,
# top surface). Curb corners and vertical strips continue THESE tones
# — infrastructure reads constant across districts (the flagged
# decision-2 judgment: streets change register, road furniture does
# not).
CURB_TONES: list[RGB] = [
    (58, 54, 46), (107, 99, 85), (143, 133, 112), (179, 167, 143), (201, 188, 164),
]
# Crosswalk bars are the paint system's pale voice (period white
# against the center line's worn ochre). Exact-color disjoint from
# every register value, curb tone, and reserved identity color —
# verified by test.
CROSSWALK_PAINT: RGB = (208, 196, 168)


def pixel_drop_worn(x: int, y: int) -> bool:
    """The recorded pixel-drop wear hash: (x*13 + y*7) % 11 == 0.

    First paid for on Vinnie's flaking letters; the single authority
    for deterministic paint/surface loss. Nothing is hand-random.
    """
    return (x * 13 + y * 7) % 11 == 0


def a2_blob_fill(sheet: Image.Image, bx: int, by: int) -> Image.Image:
    """Seamless 16px fill from a blob-style A2 autotile block at (bx, by).

    This pack's A2 blocks (32x48) draw isolated rounded blobs; the only
    seamless surface is the four inner 8x8 quadrants of rows 1-2.
    """
    src = sheet.convert("RGBA")
    out = Image.new("RGBA", (16, 16))
    out.paste(src.crop((bx + 8, by + 24, bx + 16, by + 32)), (0, 0))
    out.paste(src.crop((bx + 16, by + 24, bx + 24, by + 32)), (8, 0))
    out.paste(src.crop((bx + 8, by + 32, bx + 16, by + 40)), (0, 8))
    out.paste(src.crop((bx + 16, by + 32, bx + 24, by + 40)), (8, 8))
    return out


def luminance_ramp(image: Image.Image, ramp: list[RGB]) -> Image.Image:
    """Map every opaque pixel onto `ramp` by luminance; alpha preserved."""
    out = image.convert("RGBA").copy()
    n = len(ramp)
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = out.getpixel((x, y))
            if a == 0:
                continue
            lum = 0.3 * r + 0.59 * g + 0.11 * b
            out.putpixel((x, y), (*ramp[min(n - 1, int(lum / 256 * n))], a))
    return out


def recolor_family(
    image: Image.Image,
    ramp: list[RGB],
    member: "callable[[int, int, int], bool]",
) -> Image.Image:
    """Luminance-map ONLY pixels where `member(r, g, b)` holds.

    The family gate is verified against a census before trusting it in
    a curation pass (the Bee v8 lesson) — this helper just applies it.
    """
    out = image.convert("RGBA").copy()
    n = len(ramp)
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = out.getpixel((x, y))
            if a and member(r, g, b):
                lum = 0.3 * r + 0.59 * g + 0.11 * b
                out.putpixel((x, y), (*ramp[min(n - 1, int(lum / 256 * n))], a))
    return out


def flank_recolor(image: Image.Image, sign_rows: int) -> Image.Image:
    """Donor storefront into the register — three rules, each naming its
    cluster: blue family -> dark glass (shine one step up); near-neutral
    BRIGHT body pixels (fascia speculars) -> ONE wall tone; the rest ->
    the wall ramp. Rows above `sign_rows` are exempt from flattening so
    lettering survives.
    """
    out = image.convert("RGBA").copy()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = out.getpixel((x, y))
            if a == 0:
                continue
            lum = 0.3 * r + 0.59 * g + 0.11 * b
            if b > r + 15 and b > 90:
                gi = 0 if lum < 170 else (1 if lum < 215 else 2)
                out.putpixel((x, y), (*GLASS_RAMP[gi], a))
            elif y >= sign_rows and lum > 190 and max(r, g, b) - min(r, g, b) < 30:
                out.putpixel((x, y), (*FLANK_RAMP[3], a))
            else:
                out.putpixel((x, y), (*FLANK_RAMP[min(4, int(lum / 256 * 5))], a))
    return out


def column_stamp(image: Image.Image, box: Box, ref_x: int) -> Image.Image:
    """Replace `box` with the reference column's rows — the repair for
    donor geometry the flat-on grammar cannot keep (slanted panes,
    perspective roofs). Recolor rules cannot erase drawn outlines;
    this can.
    """
    out = image.convert("RGBA").copy()
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        ref = out.getpixel((ref_x, y))
        for x in range(x0, x1 + 1):
            out.putpixel((x, y), ref)
    return out


def desaturate_warm(image: Image.Image, k: float = 0.22) -> Image.Image:
    """Blend toward gray by `k` with a slight warm bias — the donor-prop
    pass that knocks RPG saturation without repainting identity.
    """
    out = image.convert("RGBA").copy()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = out.getpixel((x, y))
            if a == 0:
                continue
            gray = 0.3 * r + 0.59 * g + 0.11 * b
            out.putpixel((x, y), (
                min(int(r * (1 - k) + gray * k + 6), 255),
                min(int(g * (1 - k) + gray * k + 2), 255),
                min(int(b * (1 - k) + gray * k), 255),
                a,
            ))
    return out


def tree_well(width: int = 58, height: int = 22) -> Image.Image:
    """Grated tree well, flush with the walk — code, because a well is a
    regular form. Drawn UNDER the trunk; sized so a root flare cannot
    swallow it (v8's 44px well vanished behind s16401).
    """
    im = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, width - 1, height - 1], fill=(44, 36, 28, 255),
                outline=(*WELL_METALS[0], 255))
    d.rectangle([2, 2, width - 3, height - 3], outline=(*WELL_METALS[2], 255))
    for gx in range(6, width - 4, 8):
        d.line([gx, 3, gx, height - 4], fill=(*WELL_METALS[1], 255))
    return im


def upper_story_band(width: int = 640, height: int = 56) -> Image.Image:
    """Brick upper stories with a window rhythm and cornice — code,
    because brick courses and window grids are regular patterns. The
    band that turned the block into a city (v9) for zero generations.
    """
    brick, brick_d, mortar = (96, 82, 68), (84, 70, 58), (108, 94, 78)
    glass, glass_hi = (52, 48, 42), (74, 70, 62)
    frame, sill, cornice = (198, 182, 156), (150, 132, 110), (52, 44, 38)
    band = Image.new("RGBA", (width, height), (*brick, 255))
    d = ImageDraw.Draw(band)
    for y in range(0, height, 6):
        d.line([0, y, width, y], fill=mortar)
        off = 12 if (y // 6) % 2 else 0
        for x in range(off, width, 24):
            d.line([x, y, x, min(y + 5, height - 1)], fill=brick_d)
    for wx in range(24, width - 16, 48):
        d.rectangle([wx, 14, wx + 17, 43], fill=glass, outline=frame)
        d.line([wx + 9, 15, wx + 9, 42], fill=frame)
        d.line([wx + 1, 28, wx + 16, 28], fill=frame)
        d.rectangle([wx + 2, 16, wx + 7, 26], fill=glass_hi)
        d.rectangle([wx - 1, 44, wx + 18, 46], fill=sill)
    d.rectangle([0, height - 5, width, height - 1], fill=cornice)
    d.line([0, height - 6, width, height - 6], fill=frame)
    return band


def worn_edge_line(image: Image.Image, y: int, color: RGB = (168, 152, 118)) -> None:
    """2px solid lane-edge line with the deterministic wear rule
    ((x*7+3) % 23 in {0,1} -> gap). Solid against the center dashes:
    each boundary gets its own voice. Mutates `image` in place.
    """
    for x in range(image.width):
        if (x * 7 + 3) % 23 not in (0, 1):
            for dy in range(2):
                image.putpixel((x, y + dy), (*color, 255))


def paint_wear_drop(x: int, y: int, pct: int) -> bool:
    """The crosswalk's recorded wear rule: drop the paint pixel where a
    white-mixing hash of (x, y) falls under `pct` percent.

    Recorded 2026-08-11 with a negative result worth keeping: the
    letter-scale pixel-drop hash ((x*13+y*7)%11) lays its drops on
    slope -13/7 diagonals, which read as moire on 8px-tall zebra bars,
    and the worn-edge column rule eats the same columns of every bar.
    Paint wear at bar scale needs spatially WHITE loss — still fully
    deterministic, never hand-random.
    """
    h = ((x * 73856093) ^ (y * 19349663)) & 0x7FFFFFFF
    return h % 100 < pct


def crosswalk_paint(
    road_depth: int,
    corridor: int = 40,
    stripe: int = 8,
    gap: int = 8,
    wheel_bands: tuple[tuple[int, int], ...] = (),
) -> Image.Image:
    """Worn zebra paint layer for a crossing over a HORIZONTAL road.

    Continental bars parallel to traffic (aerial-true), stacked
    curb-to-curb at `stripe`+`gap` pitch; only whole bars are laid,
    centered with margins (paint crews do not paint half a bar into a
    gutter). Paint-only alpha: the district's road shows through gaps
    and wear — paint is citywide, ground is register.

    Wear is the recorded `paint_wear_drop` rule, graded by physics
    (grades tuned by eye 2026-08-11 against B/C variants and recorded
    here as law): 4% base loss, 30% inside `wheel_bands` (local row
    spans where the travel lanes' tires cross — the bars in wheel
    paths wear to fragments while bars between lanes survive), +6 on
    each bar's edge rows where paint chips first. Deterministic by
    construction; byte-equal on every call.
    """
    im = Image.new("RGBA", (corridor, road_depth), (0, 0, 0, 0))
    pitch = stripe + gap
    bars = max((road_depth - 8 + gap) // pitch, 1)   # >=4px margin each end
    y = (road_depth - (bars * stripe + (bars - 1) * gap)) // 2
    for _ in range(bars):
        for yy in range(y, y + stripe):
            in_wheels = any(b0 <= yy < b1 for b0, b1 in wheel_bands)
            edge_row = yy in (y, y + stripe - 1)
            pct = (30 if in_wheels else 4) + (6 if edge_row else 0)
            for x in range(corridor):
                if paint_wear_drop(x, yy, pct):
                    continue
                im.putpixel((x, yy), (*CROSSWALK_PAINT, 255))
        y += pitch
    return im


def crosswalk_paint_vertical(
    road_width: int,
    corridor: int = 40,
    stripe: int = 8,
    gap: int = 8,
    wheel_bands: tuple[tuple[int, int], ...] = (),
) -> Image.Image:
    """The same crossing over a VERTICAL (north-south) road: bars run
    vertical (still parallel to traffic), stacked west-to-east;
    `wheel_bands` are local COLUMN spans after the transpose. One wear
    authority, two orientations.
    """
    return crosswalk_paint(road_width, corridor, stripe, gap, wheel_bands).transpose(
        Image.Transpose.TRANSPOSE
    )


def far_line_tone(walk_ramp: "list[RGB]") -> "RGB":
    """The far curb line's single voice (ruled 2026-08-12, session F,
    under the board's delegation - the A/B record is in the spec).

    From this camera the far edge reads as the shadow seam at the
    curb's foot: dark asphalt, this line, then the lit walk behind -
    the hero's fourteen-round ratified read. The line is WALK TIER 2
    of the scene's own register; the far walk band stays each
    renderer's walk fill. This closed the oldest two-authorities
    smell (builder hardcoded OH walk[1]; the composer hardcoded LS
    cream citywide - which put a Little Sicily line on the Meadows'
    violet-gray far street until this law).
    """
    return walk_ramp[1]


def curb_vertical_strip(
    height: int, width: int = 10, road_side: str = "east"
) -> Image.Image:
    """Curb along a north-south street edge — top surface only (the
    flat-on grammar shows south faces; a side-on curb has none). Pale
    field in s16102's top-surface tones, stone joints on the 16px
    rhythm, a 2px dark road edge with a 1px transition; wear speckle
    by the recorded pixel-drop hash. `road_side` names which edge the
    road touches.
    """
    if road_side not in ("east", "west"):
        raise ValueError(f"road_side must be east or west, got {road_side!r}")
    base, face, joint, speckle, pale = CURB_TONES
    im = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for y in range(height):
        for x in range(width):
            if x >= width - 2:
                col = base
            elif x == width - 3:
                col = joint
            elif y % 16 == 15:
                col = joint
            elif pixel_drop_worn(x, y):
                col = speckle
            else:
                col = pale
            im.putpixel((x, y), (*col, 255))
    if road_side == "west":
        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return im


def curb_cut(corridor: int, band_height: int = 16) -> Image.Image:
    """Curb-cut apron across a crossing corridor (board note 2026-08-12:
    crossings get curb cuts — period-true; ramps predate the thirty
    days and the ADA made them law in 1990).

    Overlays the 16px south-facing curb band: the face and base drop
    out across the cut and a sloped apron (speckle tone) meets the
    road through a softened lip; 4px triangular wings step the full
    face down at each side. s16102 anatomy rows; wear by the recorded
    pixel-drop hash. Deterministic, opaque, CURB_TONES only.
    """
    base, face, joint, speckle, pale = CURB_TONES
    im = Image.new("RGBA", (corridor, band_height), (0, 0, 0, 0))
    for y in range(band_height):
        for x in range(corridor):
            if y <= 6:
                col = speckle if pixel_drop_worn(x, y) else pale
            elif y == 7:
                col = speckle                       # softened shoulder
            else:
                d = min(x, corridor - 1 - x)        # wing distance
                if d < 4 and y >= 8 + 2 * d:
                    col = face if y <= 12 else base  # the face steps down
                elif y <= 13:
                    col = joint if pixel_drop_worn(x, y) else speckle  # apron
                elif y == 14:
                    col = joint
                else:
                    col = face                      # soft lip, not full shadow
            im.putpixel((x, y), (*col, 255))
    return im


def curb_vertical_cut(
    corridor: int, width: int = 10, road_side: str = "east"
) -> Image.Image:
    """The cut for a side-street curb strip: across the corridor the
    2px dark road edge opens into apron tones, with 2px wings stepping
    the edge back at each end. Same anatomy as curb_vertical_strip.
    """
    if road_side not in ("east", "west"):
        raise ValueError(f"road_side must be east or west, got {road_side!r}")
    base, face, joint, speckle, pale = CURB_TONES
    im = Image.new("RGBA", (width, corridor), (0, 0, 0, 0))
    for y in range(corridor):
        d = min(y, corridor - 1 - y)
        for x in range(width):
            if x < width - 3:
                col = speckle if pixel_drop_worn(x, y) else pale
            elif x == width - 3:
                col = speckle
            elif d == 0 or (d == 1 and x == width - 1):
                col = base                          # wing: edge steps back
            else:
                col = joint if pixel_drop_worn(x, y) else speckle
            im.putpixel((x, y), (*col, 255))
    if road_side == "west":
        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return im


def curb_corner_anchor(orientation: str = "se") -> Image.Image:
    """32x32 code anchor for a curb corner return — the crude form the
    pixflux wear pass textures (the s16102 recipe carried around a
    corner). 'se': the block WEST of a cross street — the south-facing
    band enters from the west and wraps north up the east edge; 'sw'
    is the mirror for the block east of the cross street. Anchors are
    code and may mirror; each orientation buys its own generation
    seeds, so no generated wear is ever a mirror twin.

    Anatomy censused from s16102 (rows: 7 pale / 1 transition /
    5 face / 3 base shadow; joints every 16px); the return arc sweeps
    the dark contour and face around the outer corner, tapering the
    face to nothing as the edge turns from south-facing to east-facing.
    """
    import math

    if orientation not in ("se", "sw"):
        raise ValueError(f"orientation must be se or sw, got {orientation!r}")
    base, face, joint, _speckle, pale = CURB_TONES
    size, ccx, ccy, radius = 32, 25.5, 25.5, 6.0
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for y in range(size):
        for x in range(size):
            in_band, in_strip = y >= 16, x >= 22
            if not (in_band or in_strip):
                continue                       # walk interior shows through
            qx, qy = x - ccx, y - ccy
            if qx > 0 and qy > 0:              # the return arc
                dist = math.hypot(qx, qy)
                if dist > radius:
                    continue                   # road beyond the arc
                depth = radius - dist
                c = math.cos(math.atan2(qx, qy))
                base_span = 2.0 + c
                if depth < base_span:
                    col = base
                elif depth < base_span + 5.0 * c:
                    col = face
                elif depth < base_span + 5.0 * c + 1.0:
                    col = joint
                else:
                    col = pale
            elif qx <= 0 and in_band:          # straight south band
                r = y - 16
                col = (pale if r <= 6 else joint if r == 7
                       else face if r <= 12 else base)
                if r <= 6 and x % 16 == 15:
                    col = joint
            else:                              # straight east strip
                depth = 31 - x
                col = base if depth <= 1 else joint if depth == 2 else pale
                if depth > 2 and y % 16 == 15:
                    col = joint
            im.putpixel((x, y), (*col, 255))
    if orientation == "sw":
        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return im


def asphalt_field(w: int, h: int, ramp: "list[RGB] | None" = None) -> Image.Image:
    """Aperiodic asphalt: the board's 2026-08-12 note ("the road now
    feels brick") convicted the A2 donor fill's diagonal lattice, and
    the hybrid ruling licenses selective upgrade with cause.

    A full-band field, not a tile: tier-1 base with white-mix hash
    speckle in the other tiers (dark pores 8%, mid grain 8%, pale
    flecks 1.5%), so there is NO period to read — aperiodicity by
    construction, deterministic in world coordinates, register-aware
    via `ramp` (defaults to Old Harbor's ASPHALT_RAMP; districts pass
    their own road ramp).
    """
    tones = ramp or ASPHALT_RAMP
    im = Image.new("RGBA", (w, h), (*tones[1], 255))
    for y in range(h):
        for x in range(w):
            hsh = ((x * 73856093) ^ (y * 19349663)) & 0x7FFFFFFF
            r = hsh % 1000
            if r < 80:
                im.putpixel((x, y), (*tones[0], 255))
            elif r < 160:
                im.putpixel((x, y), (*tones[2], 255))
            elif r < 175:
                im.putpixel((x, y), (*tones[3], 255))
    return im


# ------------------------------------------------- the decal class
# Grime, cracks and patches are TRANSLUCENT overlays — the class the
# oil stains, contact shadows and yellow curb founded: alpha layers
# flattened into the ground at bake, so they darken any district's
# register without minting new exact colors (decision 5 stays safe).
# District grading is placement data, guided by the recorded law:
# the Meadows dirtiest, Old Harbor moderate, Little Sicily swept,
# University pristine. Nothing is hand-random: every irregularity
# derives from paint_wear_drop-class hashes of the decal's own data.


def asphalt_patch(w: int, h: int, variant: int = 0) -> Image.Image:
    """A patched-asphalt decal: the road crew's newer tar reads darker.

    Translucent black fill with a heavier tar seam; corner nibbles by
    the recorded hash keep the rectangle honest (patches are cut by
    hand, not by CAD). Deterministic in (w, h, variant).
    """
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([1, 1, w - 2, h - 2], fill=(10, 9, 8, 56))
    d.rectangle([1, 1, w - 2, h - 2], outline=(8, 7, 6, 118))
    for cx, cy in ((0, 0), (w - 3, 0), (0, h - 3), (w - 3, h - 3)):
        if paint_wear_drop(cx + variant * 7, cy + variant * 11, 55):
            d.rectangle([cx, cy, cx + 2, cy + 2], fill=(0, 0, 0, 0))
    return im


def grime_stain(w: int, h: int, variant: int = 0) -> Image.Image:
    """A grime-stain decal: 2-3 lobed translucent darkening, the oil
    stains' geometry generalized. Deterministic in (w, h, variant).
    """
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, h // 4, w - 1, h - 1], fill=(14, 12, 10, 62))
    lx = (variant * 37) % max(w // 2, 1)
    d.ellipse([lx, 0, lx + w // 2, h // 2 + 1], fill=(14, 12, 10, 48))
    if variant % 2:
        d.ellipse([w // 3, h // 3, w - 1, h - 1], fill=(10, 9, 8, 44))
    return im


def wall_streak(h: int, w: int = 5) -> Image.Image:
    """A weather streak for wall bases and sill lines: two nested
    translucent columns, heavier at the top where the water starts.
    """
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([1, 0, w - 2, h - 1], fill=(12, 11, 10, 36))
    d.rectangle([w // 2 - 1, 0, w // 2, h // 3], fill=(12, 11, 10, 60))
    return im


def crack_to_decal(image: Image.Image, max_alpha: int = 150) -> Image.Image:
    """Curation law for generated cracks: shape from generation, tone
    from law. Maps every opaque pixel to translucent BLACK with alpha
    from darkness (darker source -> stronger crack), so the decal
    joins the translucent class and lands on any register.
    """
    src = image.convert("RGBA")
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = src.getpixel((x, y))
            if a == 0:
                continue
            lum = 0.3 * r + 0.59 * g + 0.11 * b
            alpha = int(max_alpha * (1.0 - lum / 255.0))
            if alpha > 24:                      # faint pixels drop out
                out.putpixel((x, y), (0, 0, 0, alpha))
    return out


def place_with_contact_shadow(
    canvas: Image.Image,
    sprite: Image.Image,
    x: int,
    y: int,
    shadow_halfwidth: int | None,
    alpha: int = 70,
) -> Image.Image:
    """Paste `sprite` with a contact ellipse under its CONTENT bbox.

    Canvas-bounds shadows float (the v8 wagon) — the ellipse anchors to
    the sprite's opaque extent, never its canvas.
    """
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    if shadow_halfwidth:
        bbox = sprite.getbbox()
        if bbox:
            d = ImageDraw.Draw(layer)
            cx = x + (bbox[0] + bbox[2]) // 2
            cy = y + bbox[3] - 2
            d.ellipse(
                [cx - shadow_halfwidth, cy - 3, cx + shadow_halfwidth, cy + 3],
                fill=(0, 0, 0, alpha),
            )
    layer.paste(sprite, (x, y), sprite)
    return Image.alpha_composite(canvas.convert("RGBA"), layer)


def place_on_base(
    canvas: Image.Image,
    sprite: Image.Image,
    x: int,
    base_y: int,
    shadow_halfwidth: int | None,
) -> Image.Image:
    """Place so the sprite's content BOTTOM sits on `base_y` — the
    attachment-line placement (wall line / curb line are base rows).
    """
    bbox = sprite.getbbox()
    bottom = bbox[3] if bbox else sprite.height
    return place_with_contact_shadow(
        canvas, sprite, x, base_y - bottom, shadow_halfwidth
    )


# ------------------------------------------------- district registers
# Decision 2, ratified 2026-08-11: the crowd wardrobe law extended to
# ground and walls. Old Harbor (HOME_DISTRICT — the shop sits at its
# edge) inherits the block-proven ramps BY REFERENCE, plus a dock-gray
# accent; the other three derive tier-to-tier. Laws the values obey,
# enforced by test:
# - Tier counts are fixed (road 4 / walk 4 / storefront 5 / accent 4),
#   so every cross-district surface mapping is a bijection and
#   `recolor.apply_mapping` can never refuse it as a collapse.
# - The FLAT-ROAD law is citywide: adjacent road tiers stay within ~6
#   luminance in every district (the A2 lattice-kill is geometry, not
#   an Old Harbor mood).
# - Exact-color disjointness: within a register all 17 values are
#   pairwise distinct, and no register value equals a reserved cast
#   identity color, a wardrobe target, a skin-ramp tone, a well metal,
#   or a sedan body tone — decision 5's night maps will be recorded
#   exact-color passes over COMPOSED scenes, and a shared value would
#   let a road shift catch a bystander's shirt or a parked car.
#   KNOWN EXCEPTION, flagged not fixed: GLASS_RAMP[0] == ASPHALT_RAMP[1]
#   (46, 42, 38) — recorded before this law; re-tiering glass would
#   alter the CLEAN v14 read, so it stays a board call.
# - Curb concrete, lane paint, and hydrant curb-yellow are CITYWIDE
#   infrastructure, not register surfaces (flagged judgment: streets
#   change register, road furniture does not).
# Accents carry the district's name-color: Old Harbor dock gray,
# Little Sicily oxblood (the recorded OXBLOOD_RAMP, by reference),
# University slate-teal (NOT the sedan's SLATE_RAMP), the Meadows
# club violet — warm neon stays reserved for the cast.
DOCK_GRAY_RAMP: list[RGB] = [(70, 72, 72), (104, 106, 105), (138, 140, 138), (176, 178, 175)]
DISTRICT_REGISTERS: dict[str, dict[str, list[RGB]]] = {
    "old_harbor": {
        "road": ASPHALT_RAMP,
        "walk": WALK_RAMP,
        "storefront": FLANK_RAMP,
        "accent": DOCK_GRAY_RAMP,
    },
    "little_sicily": {
        "road": [(43, 39, 33), (48, 43, 37), (52, 47, 40), (56, 51, 43)],
        "walk": [(104, 94, 76), (152, 140, 116), (182, 168, 140), (206, 192, 162)],
        "storefront": [
            (56, 46, 36), (102, 86, 66), (158, 138, 108), (206, 188, 152), (236, 222, 192),
        ],
        "accent": OXBLOOD_RAMP,
    },
    "university": {
        "road": [(36, 37, 42), (41, 42, 47), (45, 46, 52), (49, 50, 57)],
        "walk": [(88, 90, 96), (130, 134, 142), (158, 162, 170), (180, 184, 192)],
        "storefront": [
            (46, 48, 56), (86, 90, 100), (132, 138, 150), (178, 184, 196), (212, 218, 228),
        ],
        "accent": [(56, 72, 84), (90, 110, 124), (124, 144, 158), (168, 186, 198)],
    },
    "meadows": {
        "road": [(33, 34, 44), (38, 39, 50), (42, 43, 55), (46, 47, 60)],
        "walk": [(84, 82, 96), (120, 118, 136), (146, 144, 162), (168, 166, 184)],
        "storefront": [
            (42, 40, 56), (76, 74, 96), (116, 114, 138), (160, 158, 184), (200, 198, 220),
        ],
        "accent": [(96, 40, 88), (134, 58, 120), (172, 80, 152), (206, 120, 184)],
    },
}
# Decision 5 stands DEFERRED: night is a register-level recorded
# recolor over these values (the disjointness law exists for it), the
# Meadows first in line. The slot documents intent; None means no
# ruling has happened.
AFTER_DARK_VARIANTS: dict[str, None] = {name: None for name in DISTRICT_REGISTERS}


# ------------------------------------------------- scene-unit validation
# Decision 3 (2026-08-11): the DiNapoli block is THE compact exterior
# scene unit; new scenes are staging-v3 instances of it, and this
# validator holds the unit's INVARIANT laws. Validation REFUSES, never
# repairs (the engine's doctrine). The laws it can check are the ones
# recorded AS DATA — which is the point of schema v3: doorways and
# prop spans became data precisely so the no-door and x-slot clauses
# stopped living in prose and board eyesight alone.
SCENE_WIDTH = 640
SCENE_HEIGHT = 360
PROP_LINES = frozenset({"wall", "curb", "road"})


def _spans_overlap(a: "tuple[int, int] | list[int]", b: "tuple[int, int] | list[int]") -> bool:
    return not (a[1] < b[0] or b[1] < a[0])


def validate_scene_staging(data: dict) -> None:
    """Refuse a scene staging dict that breaks the scene-unit laws.

    Raises ValueError naming the first violation; returns None on a
    lawful instance. Only schema v3 is accepted — v2 files predate the
    unit's formalization and carry placement semantics that died with
    their compose scripts.
    """
    if data.get("schema_version") != 3:
        raise ValueError("staging schema_version must be 3")
    for key in ("district", "bands", "wall_line_base_y", "curb_line_base_y",
                "slots", "doorways", "props"):
        if key not in data:
            raise ValueError(f"staging is missing required field {key!r}")
    if data["district"] not in DISTRICT_REGISTERS:
        raise ValueError(f"unknown district {data['district']!r}")
    bands = data["bands"]
    spans = sorted(bands.values(), key=lambda s: s[0])
    if spans[0][0] != 0 or spans[-1][1] != SCENE_HEIGHT:
        raise ValueError("bands must cover rows 0..360")
    for prev, cur in zip(spans, spans[1:]):
        if prev[1] != cur[0]:
            raise ValueError(f"band gap or overlap at row {prev[1]}")
    walk, curb = bands["walk"], bands["curb"]
    if not walk[0] <= data["wall_line_base_y"] < walk[1]:
        raise ValueError("wall_line_base_y must sit inside the walk band")
    if not curb[0] <= data["curb_line_base_y"] < curb[1]:
        raise ValueError("curb_line_base_y must sit inside the curb band")
    slots = data["slots"]
    ids = [s["id"] for s in slots]
    if len(set(ids)) != len(ids):
        raise ValueError("slot ids must be unique")
    for slot in slots:
        x0, x1 = slot["span"]
        if not (0 <= x0 <= x1 < SCENE_WIDTH):
            raise ValueError(f"slot {slot['id']!r} span out of scene")
    for a in range(len(slots)):
        for b in range(a + 1, len(slots)):
            if _spans_overlap(slots[a]["span"], slots[b]["span"]):
                raise ValueError(
                    f"slots {slots[a]['id']!r} and {slots[b]['id']!r} overlap"
                )
    for door in data["doorways"]:
        if not any(s["span"][0] <= door[0] and door[1] <= s["span"][1] for s in slots):
            raise ValueError(f"doorway {door} lies in no slot")
    by_line: dict[str, list[tuple[str, list[int]]]] = {"wall": [], "curb": [], "road": []}
    for name, prop in data["props"].items():
        if prop["line"] not in PROP_LINES:
            raise ValueError(f"prop {name!r} has unknown line {prop['line']!r}")
        x0, x1 = prop["span"]
        if not (0 <= x0 <= x1 < SCENE_WIDTH):
            raise ValueError(f"prop {name!r} span out of scene")
        by_line[prop["line"]].append((name, prop["span"]))
    for name, span in by_line["wall"]:
        for door in data["doorways"]:
            if _spans_overlap(span, door):
                raise ValueError(f"wall prop {name!r} blocks doorway {door}")
    for wname, wspan in by_line["wall"]:
        for cname, cspan in by_line["curb"]:
            if _spans_overlap(wspan, cspan):
                raise ValueError(
                    f"wall prop {wname!r} and curb prop {cname!r} share an x-slot"
                )
    DECAL_TYPES = {"patch", "stain", "crack"}   # ground decals; wall
    # streaks touch approved facade art and await their own ruling
    for i, decal in enumerate(data.get("decals", [])):
        if decal.get("type") not in DECAL_TYPES:
            raise ValueError(f"decal {i} has unknown type {decal.get('type')!r}")
        if not (0 <= decal["x"] < SCENE_WIDTH and 0 <= decal["y"] < SCENE_HEIGHT):
            raise ValueError(f"decal {i} origin out of scene")
        if decal["type"] == "patch":
            road = (data["bands"].get("road_parking", data["bands"].get("road")))
            road_top = road[0]
            road_bot = data["bands"].get("road_travel", road)[1]
            if not (road_top <= decal["y"] < road_bot):
                raise ValueError(f"decal {i}: patches are road-only")
    crosswalk = data.get("crosswalk")
    if crosswalk is not None:
        x0, x1 = crosswalk["x"]
        if not (0 <= x0 < x1 < SCENE_WIDTH):
            raise ValueError("crosswalk x span out of scene")
        if x1 - x0 + 1 < 24:
            raise ValueError("crosswalk corridor narrower than a figure")
        for key in ("stripe", "gap"):
            if key in crosswalk and crosswalk[key] <= 0:
                raise ValueError(f"crosswalk {key} must be positive")


def register_mapping(
    surface: str, to_district: str, from_district: str = "old_harbor"
) -> dict[tuple[int, int, int, int], tuple[int, int, int, int]]:
    """Exact-color mapping that moves one surface between registers.

    Tier-to-tier by construction (`strict` refuses tier-count drift);
    feed the result to `recolor.apply_mapping`, whose collapse refusal
    backstops the distinctness law.
    """
    src = DISTRICT_REGISTERS[from_district][surface]
    dst = DISTRICT_REGISTERS[to_district][surface]
    return {(*s, 255): (*d, 255) for s, d in zip(src, dst, strict=True)}
