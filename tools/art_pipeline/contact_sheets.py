"""Contact-sheet and review-board assembly."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw

from tools.art_pipeline.previews import enlarge

BACKGROUND = (34, 34, 40, 255)
PANEL = (48, 48, 56, 255)
TEXT = (230, 230, 230, 255)
PASS_COLOR = (80, 200, 120, 255)
FAIL_COLOR = (230, 80, 80, 255)


@dataclass
class SheetEntry:
    label: str
    image: Image.Image
    sublabel: str = ""
    status: str = ""  # "", "PASS", or "FAIL"


def build_sheet(
    entries: list[SheetEntry],
    scale: int = 8,
    columns: int = 4,
    pad: int = 12,
    show_native: bool = True,
    title: str = "",
) -> Image.Image:
    """Assemble labeled panels: enlarged preview plus optional native 1x copy."""
    if not entries:
        raise ValueError("no entries")
    cell_w = max(e.image.width * scale for e in entries) + 2 * pad
    text_h = 34
    native_h = (max(e.image.height for e in entries) + 6) if show_native else 0
    cell_h = max(e.image.height * scale for e in entries) + text_h + native_h + 2 * pad
    rows = (len(entries) + columns - 1) // columns
    title_h = 28 if title else 0
    sheet = Image.new(
        "RGBA", (columns * cell_w + 2 * pad, rows * cell_h + 2 * pad + title_h), BACKGROUND
    )
    draw = ImageDraw.Draw(sheet)
    if title:
        draw.text((pad, 8), title, fill=TEXT)
    for idx, entry in enumerate(entries):
        col, row = idx % columns, idx // columns
        x0 = pad + col * cell_w
        y0 = pad + title_h + row * cell_h
        draw.rectangle(
            (x0, y0, x0 + cell_w - 4, y0 + cell_h - 4), fill=PANEL
        )
        big = enlarge(entry.image, scale)
        sheet.alpha_composite(big, (x0 + pad, y0 + pad))
        if show_native:
            sheet.alpha_composite(
                entry.image, (x0 + pad, y0 + pad + big.height + 3)
            )
        ty = y0 + cell_h - text_h - 2
        draw.text((x0 + pad, ty), entry.label, fill=TEXT)
        if entry.sublabel:
            draw.text((x0 + pad, ty + 14), entry.sublabel, fill=TEXT)
        if entry.status:
            color = PASS_COLOR if entry.status == "PASS" else FAIL_COLOR
            draw.text(
                (x0 + cell_w - pad - 8 * len(entry.status), ty), entry.status, fill=color
            )
    return sheet
