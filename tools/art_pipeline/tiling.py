"""Tileability instruments: wrap-seam scoring and eventlessness.

Godot's TileMapLayer repeats discrete cells, so a single floor tile
must be edge-compatible with itself. Two failure modes, measured
separately: (a) seam discontinuity — the wrap edge differs more than
the tile's interior does; (b) periodicity salience — a high-contrast
feature repeating every tile reads as wallpaper. Thresholds are
CALIBRATED on donor tiles known to tile; they are never invented.
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


def _luma(px: tuple[int, int, int, int]) -> float:
    return 0.2126 * px[0] + 0.7152 * px[1] + 0.0722 * px[2]


def _column_pair_stats(im: Image.Image, x0: int, x1: int) -> tuple[float, float]:
    """(fraction of rows differing, mean |luma delta|) between two columns."""
    diff = 0
    luma_sum = 0.0
    for y in range(im.height):
        a, b = im.getpixel((x0, y)), im.getpixel((x1, y))
        if a != b:
            diff += 1
        luma_sum += abs(_luma(a) - _luma(b))
    return diff / im.height, luma_sum / im.height


def _row_pair_stats(im: Image.Image, y0: int, y1: int) -> tuple[float, float]:
    diff = 0
    luma_sum = 0.0
    for x in range(im.width):
        a, b = im.getpixel((x, y0)), im.getpixel((x, y1))
        if a != b:
            diff += 1
        luma_sum += abs(_luma(a) - _luma(b))
    return diff / im.width, luma_sum / im.width


@dataclass
class SeamReport:
    seam_diff_frac: float
    seam_luma: float
    interior_diff_fracs: list[float]
    interior_lumas: list[float]

    def percentile(self) -> float:
        """Fraction of interior pairs the seam is WORSE than (0 = best)."""
        worse_than = sum(
            1 for d, lu in zip(self.interior_diff_fracs, self.interior_lumas)
            if (self.seam_diff_frac, self.seam_luma) > (d, lu)
        )
        return worse_than / len(self.interior_diff_fracs)


def seam_report_columns(tile: Image.Image) -> SeamReport:
    """Compare the wrap seam (last column -> first column) against every
    interior adjacent-column pair."""
    im = tile.convert("RGBA")
    seam = _column_pair_stats(im, im.width - 1, 0)
    interior = [_column_pair_stats(im, x, x + 1) for x in range(im.width - 1)]
    return SeamReport(seam[0], seam[1], [d for d, _ in interior], [lu for _, lu in interior])


def seam_report_rows(tile: Image.Image) -> SeamReport:
    im = tile.convert("RGBA")
    seam = _row_pair_stats(im, im.height - 1, 0)
    interior = [_row_pair_stats(im, y, y + 1) for y in range(im.height - 1)]
    return SeamReport(seam[0], seam[1], [d for d, _ in interior], [lu for _, lu in interior])


def eventlessness(tile: Image.Image) -> dict[str, float]:
    """(b)-mode scores: largest same-color blob fraction and max local
    3x3 contrast. Lower contrast and moderate blob sizes read as calm
    floor; a single dominant high-contrast feature reads as wallpaper."""
    im = tile.convert("RGBA")
    width, height = im.size
    seen = [[False] * width for _ in range(height)]
    largest = 0
    for sy in range(height):
        for sx in range(width):
            if seen[sy][sx]:
                continue
            color = im.getpixel((sx, sy))
            stack, area = [(sx, sy)], 0
            seen[sy][sx] = True
            while stack:
                x, y = stack.pop()
                area += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = (x + dx) % width, (y + dy) % height  # toroidal
                    if not seen[ny][nx] and im.getpixel((nx, ny)) == color:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            largest = max(largest, area)
    max_contrast = 0.0
    for cy in range(height):
        for cx in range(width):
            lumas = [
                _luma(im.getpixel(((cx + dx) % width, (cy + dy) % height)))
                for dy in (-1, 0, 1) for dx in (-1, 0, 1)
            ]
            max_contrast = max(max_contrast, max(lumas) - min(lumas))
    return {
        "largest_blob_frac": largest / (width * height),
        "max_local_contrast": max_contrast,
    }


def tiled_preview(tile: Image.Image, repeat: int = 3) -> Image.Image:
    """repeat x repeat grid for the eyeball check."""
    out = Image.new("RGBA", (tile.width * repeat, tile.height * repeat))
    for gy in range(repeat):
        for gx in range(repeat):
            out.paste(tile, (gx * tile.width, gy * tile.height))
    return out


def mirror_fold(quadrant: Image.Image) -> Image.Image:
    """Self-tiling by construction: mirror a quadrant into a full tile."""
    from PIL import ImageOps
    w, h = quadrant.size
    out = Image.new("RGBA", (w * 2, h * 2))
    out.paste(quadrant, (0, 0))
    out.paste(ImageOps.mirror(quadrant), (w, 0))
    out.paste(ImageOps.flip(quadrant), (0, h))
    out.paste(ImageOps.mirror(ImageOps.flip(quadrant)), (w, h))
    return out
