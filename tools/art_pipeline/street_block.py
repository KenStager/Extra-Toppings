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
