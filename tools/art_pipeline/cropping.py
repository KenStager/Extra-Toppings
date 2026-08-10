"""Exact pixel-coordinate crops. Never resamples."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def crop_px(image: Image.Image, x: int, y: int, width: int, height: int) -> Image.Image:
    """Crop an exact pixel rectangle; refuses out-of-bounds requests."""
    if width <= 0 or height <= 0:
        raise ValueError(f"crop size must be positive, got {width}x{height}")
    if x < 0 or y < 0 or x + width > image.width or y + height > image.height:
        raise ValueError(
            f"crop ({x},{y},{width},{height}) exceeds image {image.width}x{image.height}"
        )
    return image.crop((x, y, x + width, y + height))


def crop_cells(
    image: Image.Image,
    col0: int,
    row0: int,
    col1: int,
    row1: int,
    cell: int = 16,
) -> Image.Image:
    """Crop an inclusive (col,row)..(col,row) rectangle of `cell`-px tiles.

    Coordinates are zero-based, matching the OMEGA_MAP visual grids.
    """
    if col1 < col0 or row1 < row0:
        raise ValueError("cell rectangle must be ordered (col0<=col1, row0<=row1)")
    return crop_px(
        image,
        col0 * cell,
        row0 * cell,
        (col1 - col0 + 1) * cell,
        (row1 - row0 + 1) * cell,
    )


def load_rgba(path: str | Path) -> Image.Image:
    """Open a PNG and normalize to RGBA without touching pixel geometry."""
    with Image.open(path) as im:
        return im.convert("RGBA")
