"""Nearest-neighbor enlargement for pixel-perfect previews."""

from __future__ import annotations

from PIL import Image


def enlarge(image: Image.Image, factor: int) -> Image.Image:
    """Integer nearest-neighbor upscale; refuses non-integer factors."""
    if factor < 1:
        raise ValueError(f"factor must be >= 1, got {factor}")
    return image.resize(
        (image.width * factor, image.height * factor), Image.Resampling.NEAREST
    )


def reduce_nearest(image: Image.Image, width: int, height: int) -> Image.Image:
    """Deterministic nearest-neighbor reduction (explicit, never concealed)."""
    return image.resize((width, height), Image.Resampling.NEAREST)
