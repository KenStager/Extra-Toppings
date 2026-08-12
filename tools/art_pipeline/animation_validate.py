"""Animation-frame validators — the Phase A probe's measured
contracts as law code (E16 animation slate, 2026-08-12).

The probe's central finding, now the exactness definition: vendor
animation returns endpoint frames COMPOSITE-exact, not file-exact —
the alpha mask and every visible pixel's RGB are preserved, while
RGB under fully-transparent pixels is re-encoded. A naive full-array
diff therefore reads ~66% changed on a byte-identical composite;
`composite_exact` is the instrument that cleared it. Validators
refuse (return the defect), never repair.
"""
from __future__ import annotations

from PIL import Image

RGB = tuple[int, int, int]


def composite_exact(a: Image.Image, b: Image.Image) -> bool:
    """True when the two frames composite identically: same size,
    equal alpha masks, and equal RGB on every pixel visible in
    either. RGB under mutual full transparency is ignored — that is
    the vendor's re-encoding territory, invisible once composited.
    """
    if a.size != b.size:
        return False
    pa = a.convert("RGBA").load()
    pb = b.convert("RGBA").load()
    for y in range(a.height):
        for x in range(a.width):
            ra, ga, ba, aa = pa[x, y]
            rb, gb, bb, ab = pb[x, y]
            if aa != ab:
                return False
            if aa == 0:
                continue
            if (ra, ga, ba) != (rb, gb, bb):
                return False
    return True


def binary_alpha(frame: Image.Image) -> bool:
    """Every alpha value is 0 or 255 (the sprite contract)."""
    return set(frame.convert("RGBA").getdata(3)) <= {0, 255}


def off_palette_count(frame: Image.Image, palette: set[RGB]) -> int:
    """Visible pixels whose RGB is outside `palette`. For
    interpolation clips pass the UNION of both endpoints' palettes —
    the probe's single-palette census false-alarmed on the seated
    end frame.
    """
    im = frame.convert("RGBA")
    return sum(
        1
        for r, g, b, a in im.getdata()
        if a > 0 and (r, g, b) not in palette
    )


def visible_palette(frame: Image.Image) -> set[RGB]:
    """The frame's own visible-pixel palette (census helper)."""
    return {
        (r, g, b) for r, g, b, a in frame.convert("RGBA").getdata() if a > 0
    }


def baseline_rows(frames: list[Image.Image]) -> list[int]:
    """Bottom-most visible row per frame; a walking figure's feet
    stay on the baseline (the probe measured row 31 across all
    frames, bob <= 1px). Empty frames refuse as -1.
    """
    rows = []
    for f in frames:
        bbox = f.convert("RGBA").getbbox()
        rows.append(bbox[3] - 1 if bbox else -1)
    return rows


def frame_delta(a: Image.Image, b: Image.Image) -> int:
    """Composite difference in visible pixels — the loop-continuity
    metric's unit (compare last->first against the inter-frame mean;
    a cycle that ends far from its start does not loop).
    """
    pa = a.convert("RGBA").load()
    pb = b.convert("RGBA").load()
    n = 0
    for y in range(a.height):
        for x in range(a.width):
            ra, ga, ba, aa = pa[x, y]
            rb, gb, bb, ab = pb[x, y]
            if aa == 0 and ab == 0:
                continue
            if aa != ab or (ra, ga, ba) != (rb, gb, bb):
                n += 1
    return n
