"""Candidate validation. Reports failures; never repairs them."""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image

from tools.art_pipeline.palettes import RGBA, to_hex


@dataclass
class ValidationResult:
    checks: dict[str, bool] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(self.checks.values())

    def record(self, name: str, ok: bool, note: str = "") -> None:
        self.checks[name] = ok
        if note and not ok:
            self.notes.append(f"{name}: {note}")


def _opaque_mask(rgba: Image.Image) -> list[list[bool]]:
    alpha = rgba.getchannel("A")
    px = alpha.load()
    return [
        [px[x, y] == 255 for x in range(rgba.width)] for y in range(rgba.height)
    ]


def _components(mask: list[list[bool]]) -> list[int]:
    """Areas of 8-connected opaque components, largest first."""
    height, width = len(mask), len(mask[0])
    seen = [[False] * width for _ in range(height)]
    areas: list[int] = []
    for sy in range(height):
        for sx in range(width):
            if not mask[sy][sx] or seen[sy][sx]:
                continue
            stack, area = [(sx, sy)], 0
            seen[sy][sx] = True
            while stack:
                x, y = stack.pop()
                area += 1
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            if mask[ny][nx] and not seen[ny][nx]:
                                seen[ny][nx] = True
                                stack.append((nx, ny))
            areas.append(area)
    return sorted(areas, reverse=True)


def validate_candidate(
    image: Image.Image,
    palette: list[RGBA],
    expected_size: tuple[int, int] = (16, 16),
    min_bbox: int = 9,
    max_edge_run: int = 4,
) -> ValidationResult:
    """Validate one final candidate against the experiment contract.

    Checks dimensions, transparency support, hard alpha, transparent
    corners, palette adherence, bounding-box compactness, canvas
    clipping, and disconnected garbage pixels.
    """
    result = ValidationResult()
    rgba = image.convert("RGBA")

    result.record(
        "dimensions",
        (rgba.width, rgba.height) == expected_size,
        f"got {rgba.width}x{rgba.height}, expected {expected_size[0]}x{expected_size[1]}",
    )
    result.record(
        "transparency_support",
        image.mode in ("RGBA", "LA", "PA") or "transparency" in image.info,
        f"mode {image.mode} has no alpha",
    )

    colors = rgba.getcolors(maxcolors=rgba.width * rgba.height)
    assert colors is not None
    alpha_values = {c[1][3] for c in colors}
    result.record(
        "hard_alpha",
        alpha_values <= {0, 255},
        f"soft alpha values present: {sorted(alpha_values - {0, 255})[:8]}",
    )

    corners = [
        rgba.getpixel((x, y))
        for x in (0, rgba.width - 1)
        for y in (0, rgba.height - 1)
    ]
    result.record(
        "transparent_corners",
        all(isinstance(c, tuple) and c[3] == 0 for c in corners),
        "one or more canvas corners are opaque",
    )

    allowed = {c[:3] for c in palette}
    off_palette = sorted(
        {c[1][:3] for c in colors if c[1][3] == 255 and c[1][:3] not in allowed}
    )
    result.record(
        "palette_adherence",
        not off_palette,
        f"{len(off_palette)} off-palette colors: "
        + ", ".join(to_hex((r, g, b, 255)) for r, g, b in off_palette[:8]),
    )

    mask = _opaque_mask(rgba)
    xs = [x for row in mask for x, on in enumerate(row) if on]
    ys = [y for y, row in enumerate(mask) for on in row if on]
    if not xs:
        result.record("bounding_box", False, "image is fully transparent")
        result.record("no_clipping", False, "no opaque pixels")
        result.record("no_garbage_pixels", False, "no opaque pixels")
        return result
    bbox_w, bbox_h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    result.record(
        "bounding_box",
        bbox_w >= min_bbox and bbox_h >= min_bbox,
        f"opaque bbox {bbox_w}x{bbox_h} smaller than {min_bbox}px minimum",
    )

    edges = {
        "top": sum(mask[0]),
        "bottom": sum(mask[-1]),
        "left": sum(row[0] for row in mask),
        "right": sum(row[-1] for row in mask),
    }
    runs = {k: v for k, v in edges.items() if v > max_edge_run}
    result.record(
        "no_clipping",
        not runs,
        f"long opaque runs on canvas edge suggest clipping: {runs}",
    )

    areas = _components(mask)
    garbage = [a for a in areas[1:] if a < 3]
    result.record(
        "no_garbage_pixels",
        not garbage,
        f"{len(garbage)} disconnected specks (areas {garbage[:8]})",
    )
    return result
