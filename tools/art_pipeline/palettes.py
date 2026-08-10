"""Palette extraction and palette-image construction for forced palettes."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

RGBA = tuple[int, int, int, int]


def extract_palette(image: Image.Image) -> list[RGBA]:
    """Unique fully-opaque colors, most frequent first (ties: darker first)."""
    rgba = image.convert("RGBA")
    colors = rgba.getcolors(maxcolors=rgba.width * rgba.height)
    assert colors is not None
    opaque = [(count, color) for count, color in colors if color[3] == 255]
    opaque.sort(key=lambda item: (-item[0], sum(item[1][:3]), item[1]))
    return [color for _, color in opaque]


def merge_palettes(*palettes: list[RGBA]) -> list[RGBA]:
    """Union of palettes preserving first-seen order."""
    merged: list[RGBA] = []
    for palette in palettes:
        for color in palette:
            if color not in merged:
                merged.append(color)
    return merged


def to_hex(color: RGBA) -> str:
    return "#{:02x}{:02x}{:02x}".format(*color[:3])


def from_hex(value: str) -> RGBA:
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), 255)


def save_palette_image(colors: list[RGBA], path: str | Path, swatch: int = 8) -> None:
    """Write a one-row swatch strip PNG (the PixelLab `color_image` format)."""
    if not colors:
        raise ValueError("palette is empty")
    strip = Image.new("RGBA", (swatch * len(colors), swatch))
    for i, color in enumerate(colors):
        strip.paste(color, (i * swatch, 0, (i + 1) * swatch, swatch))
    strip.save(path)
