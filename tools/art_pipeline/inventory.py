"""PNG inventory: dimensions, color counts, alpha hardness, hashes."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from PIL import Image


def inventory_png(path: str | Path) -> dict[str, Any]:
    """Report a PNG's geometry, color usage, alpha values, and sha256."""
    path = Path(path)
    data = path.read_bytes()
    with Image.open(path) as im:
        rgba = im.convert("RGBA")
        colors = rgba.getcolors(maxcolors=rgba.width * rgba.height)
        assert colors is not None
        alpha_values = sorted({c[1][3] for c in colors})
        opaque = [c for c in colors if c[1][3] == 255]
        return {
            "path": str(path),
            "width": im.width,
            "height": im.height,
            "mode": im.mode,
            "unique_rgba_colors": len(colors),
            "opaque_colors": len(opaque),
            "alpha_values": alpha_values,
            "hard_alpha": set(alpha_values) <= {0, 255},
            "sha256": hashlib.sha256(data).hexdigest(),
        }


def inventory_dir(directory: str | Path) -> list[dict[str, Any]]:
    """Inventory every PNG directly inside `directory`, sorted by name."""
    return [
        inventory_png(p) for p in sorted(Path(directory).glob("*.png"))
    ]
