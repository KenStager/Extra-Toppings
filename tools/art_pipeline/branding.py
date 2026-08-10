"""Deterministic DiNapoli's brand geometry: sign, emblem, awning.

Policy (decision_32px_world.md): brand geometry is code, never
generated — mask-inpainting proved unreliable and lettering must stay
pixel-exact. Colors default to the directive chips.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from tools.art_pipeline.palettes import from_hex
from tools.art_pipeline.pixel_font import draw_text, text_width

BLACK = from_hex("#000000")
INK = from_hex("#303B5A")
GRAY = from_hex("#9D9C9C")
PALE = from_hex("#CBD7CC")
CREAM = from_hex("#FBFBE8")
OXBLOOD = from_hex("#A81031")
GOLD = from_hex("#FFE976")
HEAT = from_hex("#FF8628")

PLAQUE_HEIGHT = 16


def build_status_plaque(
    text: str,
    warm: bool,
    canvas: tuple[int, int] = (64, 32),
) -> Image.Image:
    """Door/window status plaque, centered on a transparent canvas.

    Warm state (OPEN): oxblood enamel, cream lettering, gold trim —
    oven warmth. Cold state (CLOSED): carbon ink, pale lettering, gray
    trim — carbon-paper pressure. Canvas defaults to 64x32 so the
    asset stays 32-grid aligned regardless of text length.
    """
    field_color = OXBLOOD if warm else INK
    trim = GOLD if warm else GRAY
    face = CREAM if warm else PALE
    shadow = INK if warm else BLACK

    tw = text_width(text, 1)
    pw = tw + 10
    if pw > canvas[0] or PLAQUE_HEIGHT > canvas[1]:
        raise ValueError(f"plaque {pw}x{PLAQUE_HEIGHT} exceeds canvas {canvas}")
    out = Image.new("RGBA", canvas, (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    x0 = (canvas[0] - pw) // 2
    y0 = (canvas[1] - PLAQUE_HEIGHT) // 2
    d.rounded_rectangle(
        (x0, y0, x0 + pw - 1, y0 + PLAQUE_HEIGHT - 1),
        radius=3, fill=field_color, outline=BLACK,
    )
    d.rounded_rectangle(
        (x0 + 2, y0 + 2, x0 + pw - 3, y0 + PLAQUE_HEIGHT - 3),
        radius=2, outline=trim,
    )
    # Cord holes at the plaque's top corners, inside the trim line.
    out.putpixel((x0 + 3, y0 + 3), BLACK)
    out.putpixel((x0 + pw - 4, y0 + 3), BLACK)
    draw_text(out, text, x0 + 5, y0 + (PLAQUE_HEIGHT - 7) // 2 + 1, 1, face, shadow)
    return out


def build_emblem(size: int = 32) -> Image.Image:
    """Pizza-pan 'D' emblem: steel pan, cream pie field, oxblood D."""
    em = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(em)
    m = max(1, size // 16)
    d.ellipse((0, m, size - 1, size - 1 - m), fill=GRAY, outline=BLACK)
    d.ellipse((m, 2 * m, size - 1 - m, size - 1 - 2 * m), outline=PALE)
    d.ellipse((2 * m, 3 * m, size - 1 - 2 * m, size - 1 - 3 * m),
              fill=CREAM, outline=GOLD)
    scale = max(1, size // 16)
    tx = (size - 5 * scale) // 2
    ty = (size - 7 * scale) // 2 + 1
    draw_text(em, "D", tx, ty, scale, OXBLOOD, INK)
    for fx, fy in ((0.28, 0.32), (0.70, 0.40), (0.36, 0.68), (0.64, 0.72)):
        px, py = int(size * fx), int(size * fy)
        if em.getpixel((px, py)) == CREAM:
            em.putpixel((px, py), OXBLOOD)
    return em


def build_sign(
    width: int = 256,
    height: int = 32,
    text: str = "DINAPOLI'S",
    with_emblem: bool = True,
) -> Image.Image:
    """Oxblood enamel sign: gold trim, cream lettering, ink offset."""
    sign = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(sign)
    d.rounded_rectangle((0, 0, width - 1, height - 1), radius=4,
                        fill=OXBLOOD, outline=BLACK)
    d.rounded_rectangle((2, 2, width - 3, height - 3), radius=3, outline=GOLD)
    x0 = 8
    if with_emblem:
        em = build_emblem(height - 8)
        sign.alpha_composite(em, (x0, 4))
        x0 += height - 8 + 4
    scale = max(1, (height - 12) // 7)
    tw = text_width(text, scale)
    tx = x0 + max(0, (width - x0 - 8 - tw) // 2)
    ty = (height - 7 * scale) // 2
    draw_text(sign, text, tx, ty, scale, CREAM, INK)
    return sign


def apply_awning(
    image: Image.Image,
    y0: int,
    y1: int,
    stripe: int = 8,
    scallop_depth: int = 2,
) -> Image.Image:
    """Composite a striped scalloped canopy across rows y0..y1-1."""
    out = image.copy()
    profile = [scallop_depth, 1] + [0] * (stripe - 4) + [1, scallop_depth]
    for x in range(out.width):
        fill = HEAT if (x // stripe) % 2 == 0 else CREAM
        depth = profile[x % stripe]
        for y in range(y0, y1):
            if y >= y1 - depth:
                out.putpixel((x, y), (0, 0, 0, 0))
            else:
                out.putpixel((x, y), fill)
        out.putpixel((x, y0), BLACK)
        if out.getpixel((x, y1))[3] == 255:
            out.putpixel((x, y1), INK)
    return out
