"""Deterministic wear decals: grease, scuffs, flour dust.

Experiment 06 (art_specs/experiment_06_decals.md): the wear layer is
where thirty years of oven warmth becomes visible. Every builder is a
pure function of its seed (`random.Random` only), stays >=2 px inside
the canvas so the decal contract holds by construction, and uses only
chips or Omega-native ramp colors already legal in the world. The
grease stain keeps a 2-tier ramp (interior + rim) — the recorded
lesson: tone is a ramp to shift, never a tier to collapse.
"""

from __future__ import annotations

import random

from PIL import Image

from tools.art_pipeline.palettes import RGBA, from_hex

GREASE_CORE = from_hex("#680828")
GREASE_RIM = from_hex("#B1552E")
SCUFF = from_hex("#4E6472")
SCUFF_CORE = from_hex("#303B5A")
FLOUR = from_hex("#FBFBE8")
FLOUR_SHADE = from_hex("#CBD7CC")

MARGIN = 2  # decals live in the tile interior


def _blank(size: int) -> Image.Image:
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def _in_bounds(size: int, x: int, y: int) -> bool:
    return MARGIN <= x < size - MARGIN and MARGIN <= y < size - MARGIN


def grease_stain(seed: int, size: int = 32) -> Image.Image:
    """Blob of drifting disks; interior dark, rim lighter (2-tier ramp)."""
    rng = random.Random(seed)
    filled: set[tuple[int, int]] = set()
    cx = cy = size // 2
    for _ in range(rng.randint(4, 6)):
        radius = rng.randint(2, 4)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    x, y = cx + dx, cy + dy
                    if _in_bounds(size, x, y):
                        filled.add((x, y))
        cx += rng.randint(-3, 3)
        cy += rng.randint(-3, 3)
        cx = max(MARGIN + 3, min(size - MARGIN - 4, cx))
        cy = max(MARGIN + 3, min(size - MARGIN - 4, cy))
    out = _blank(size)
    for x, y in filled:
        neighbors = sum(
            (x + dx, y + dy) in filled
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if (dx, dy) != (0, 0)
        )
        out.putpixel((x, y), GREASE_CORE if neighbors == 8 else GREASE_RIM)
    return out


def scuff_marks(seed: int, size: int = 32) -> Image.Image:
    """3-5 short diagonal strokes; slate with ink cores."""
    rng = random.Random(seed)
    out = _blank(size)
    for _ in range(rng.randint(4, 6)):
        x = rng.randint(MARGIN + 1, size - MARGIN - 9)
        y = rng.randint(MARGIN + 3, size - MARGIN - 9)
        dx, dy = rng.choice(((1, 1), (1, -1), (1, 0)))
        length = rng.randint(5, 8)
        for i in range(length):
            px, py = x + i * dx, y + i * dy
            if _in_bounds(size, px, py):
                color = SCUFF_CORE if 0 < i < length - 1 and i % 2 == 0 else SCUFF
                out.putpixel((px, py), color)
        # Skids come in pairs: a shorter parallel mark two rows down.
        if rng.random() < 0.7:
            for i in range(1, length - 1):
                px, py = x + i * dx, y + i * dy + 2
                if _in_bounds(size, px, py):
                    out.putpixel((px, py), SCUFF)
    return out


def flour_dust(seed: int, size: int = 32) -> Image.Image:
    """Scattered 1-2 px specks; cream with a pale minority."""
    rng = random.Random(seed)
    out = _blank(size)
    for _ in range(rng.randint(18, 26)):
        x = rng.randint(MARGIN, size - MARGIN - 2)
        y = rng.randint(MARGIN, size - MARGIN - 2)
        color: RGBA = FLOUR if rng.random() < 0.7 else FLOUR_SHADE
        out.putpixel((x, y), color)
        if rng.random() < 0.4:
            out.putpixel((x + 1, y), color)
        if rng.random() < 0.25:
            out.putpixel((x, y + 1), color)
    return out


def composite_on_tile(tile: Image.Image, decal: Image.Image) -> Image.Image:
    """Decal over a floor tile — the only way a decal is judgeable."""
    out = tile.convert("RGBA").copy()
    out.alpha_composite(decal)
    return out
