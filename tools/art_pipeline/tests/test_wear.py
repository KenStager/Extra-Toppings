"""Wear decals satisfy their own contract by construction."""

import unittest

from PIL import Image

from tools.art_pipeline import wear
from tools.art_pipeline.validation import coverage_fraction, validate_decal

WEAR_PALETTE = [
    wear.GREASE_CORE,
    wear.GREASE_RIM,
    wear.SCUFF,
    wear.SCUFF_CORE,
    wear.FLOUR,
    wear.FLOUR_SHADE,
]
BUILDERS = (wear.grease_stain, wear.scuff_marks, wear.flour_dust)


class WearBuilders(unittest.TestCase):
    def test_deterministic_per_seed(self):
        for builder in BUILDERS:
            a, b = builder(7), builder(7)
            self.assertEqual(list(a.getdata()), list(b.getdata()), builder.__name__)
            c = builder(8)
            self.assertNotEqual(list(a.getdata()), list(c.getdata()), builder.__name__)

    def test_every_builder_passes_the_decal_contract(self):
        for builder in BUILDERS:
            for seed in (1, 7, 42):
                decal = builder(seed)
                result = validate_decal(decal, WEAR_PALETTE)
                self.assertTrue(
                    result.passed, f"{builder.__name__}({seed}): {result.notes}"
                )

    def test_grease_keeps_a_two_tier_ramp(self):
        colors = {c for _, c in wear.grease_stain(3).getcolors(2048) if c[3] == 255}
        self.assertIn(wear.GREASE_RIM, colors)  # rim always exists

    def test_margin_by_construction(self):
        for builder in BUILDERS:
            decal = builder(11)
            rgba = decal.convert("RGBA")
            for i in range(32):
                for x, y in ((i, 0), (i, 31), (0, i), (31, i), (i, 1), (1, i)):
                    self.assertEqual(rgba.getpixel((x, y))[3], 0)

    def test_decal_contract_refuses_a_full_canvas(self):
        full = Image.new("RGBA", (32, 32), wear.GREASE_CORE)
        result = validate_decal(full, WEAR_PALETTE)
        self.assertFalse(result.passed)
        self.assertFalse(result.checks["coverage_band"])
        self.assertFalse(result.checks["transparent_corners"])

    def test_coverage_fraction_math(self):
        im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        for x in range(16):
            im.putpixel((x, 0), (255, 0, 0, 255))
        self.assertAlmostEqual(coverage_fraction(im), 16 / 1024)


if __name__ == "__main__":
    unittest.main()
