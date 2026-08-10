import unittest

from PIL import Image

from tools.art_pipeline.branding import CREAM, HEAT, OXBLOOD, apply_awning, build_emblem, build_sign
from tools.art_pipeline.palettes import quantize_to_palette
from tools.art_pipeline.pixel_font import GLYPH_HEIGHT, GLYPHS, draw_text, text_width


class PixelFont(unittest.TestCase):
    def test_every_glyph_is_seven_rows_consistent_width(self) -> None:
        for ch, rows in GLYPHS.items():
            self.assertEqual(len(rows), GLYPH_HEIGHT, ch)
            self.assertEqual(len({len(r) for r in rows}), 1, ch)

    def test_text_width_math(self) -> None:
        self.assertEqual(text_width("D"), 5)
        self.assertEqual(text_width("DI"), 11)       # 5 + 1 + 5
        self.assertEqual(text_width("DI", scale=2), 22)
        self.assertEqual(text_width(""), 0)

    def test_draw_exact_pixels_and_shadow_under_face(self) -> None:
        im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        face, shadow = (255, 0, 0, 255), (0, 0, 255, 255)
        draw_text(im, "I", 2, 2, 1, face, shadow)
        self.assertEqual(im.getpixel((2, 2)), face)      # top-left of I
        self.assertEqual(im.getpixel((7, 9)), shadow)    # offset corner
        self.assertEqual(im.getpixel((4, 5)), face)      # stem center

    def test_unknown_glyph_refused(self) -> None:
        im = Image.new("RGBA", (8, 8))
        with self.assertRaises(KeyError):
            draw_text(im, "é", 0, 0, 1, (0, 0, 0, 255))


class Branding(unittest.TestCase):
    def test_sign_geometry_and_lettering_colors(self) -> None:
        sign = build_sign(256, 32, "DINAPOLI'S")
        self.assertEqual(sign.size, (256, 32))
        colors = {c for _, c in sign.getcolors(256 * 32)}
        self.assertIn(OXBLOOD, colors)
        self.assertIn(CREAM, colors)
        self.assertEqual(sign.getpixel((0, 0))[3], 0)    # rounded corner clear

    def test_emblem_round_trip_sizes(self) -> None:
        for size in (24, 32):
            em = build_emblem(size)
            self.assertEqual(em.size, (size, size))
            self.assertIn(OXBLOOD, {c for _, c in em.getcolors(size * size)})

    def test_awning_stripes_and_scallops(self) -> None:
        base = Image.new("RGBA", (32, 24), (10, 10, 10, 255))
        out = apply_awning(base, 4, 16, stripe=8)
        self.assertEqual(out.getpixel((2, 8)), HEAT)      # first stripe
        self.assertEqual(out.getpixel((10, 8)), CREAM)    # second stripe
        self.assertEqual(out.getpixel((0, 15))[3], 0)     # scallop notch
        self.assertEqual(base.getpixel((2, 8)), (10, 10, 10, 255))  # source untouched


class Quantize(unittest.TestCase):
    def test_snaps_offpalette_and_soft_alpha(self) -> None:
        pal = [(200, 40, 40, 255), (240, 230, 200, 255)]
        im = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
        im.putpixel((0, 0), (198, 44, 38, 255))    # near red -> snap
        im.putpixel((1, 0), (240, 230, 200, 255))  # exact -> untouched
        im.putpixel((0, 1), (240, 230, 200, 90))   # soft alpha -> clear
        out, changed = quantize_to_palette(im, pal)
        self.assertEqual(out.getpixel((0, 0)), (200, 40, 40, 255))
        self.assertEqual(out.getpixel((1, 0)), (240, 230, 200, 255))
        self.assertEqual(out.getpixel((0, 1)), (0, 0, 0, 0))
        self.assertEqual(changed, 2)

    def test_clean_image_reports_zero_changes(self) -> None:
        pal = [(200, 40, 40, 255)]
        im = Image.new("RGBA", (4, 4), (200, 40, 40, 255))
        _, changed = quantize_to_palette(im, pal)
        self.assertEqual(changed, 0)


if __name__ == "__main__":
    unittest.main()
