"""Recolors are recorded, deterministic, and refuse ramp collapse."""

import unittest

from PIL import Image

from tools.art_pipeline.palettes import from_hex
from tools.art_pipeline.recolor import (
    EXTRAS_VARIANTS,
    apply_mapping,
    build_variant,
    check_zone_unique,
)

A = from_hex("#680828")
B = from_hex("#4E6472")
C = from_hex("#303B5A")
D = from_hex("#9D9C9C")


def sprite() -> Image.Image:
    im = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    for x in range(2, 6):
        im.putpixel((x, 1), A)  # "hair" zone rows 0-2
        im.putpixel((x, 4), B)  # "top" zone rows 3-6
    return im


class RecolorTests(unittest.TestCase):
    def test_global_swap_is_exact_and_deterministic(self):
        out1 = apply_mapping(sprite(), {A: C})
        out2 = apply_mapping(sprite(), {A: C})
        self.assertEqual(list(out1.getdata()), list(out2.getdata()))
        self.assertEqual(out1.getpixel((2, 1)), C)
        self.assertEqual(out1.getpixel((2, 4)), B)  # untouched zone

    def test_region_scoped_swap_stays_in_region(self):
        out = apply_mapping(sprite(), {A: C}, region=(0, 3, 7, 7))
        self.assertEqual(out.getpixel((2, 1)), A)  # outside region: unchanged

    def test_ramp_collapse_refused(self):
        with self.assertRaises(ValueError):
            apply_mapping(sprite(), {A: C, B: C})

    def test_zone_uniqueness_check(self):
        im = sprite()
        self.assertTrue(check_zone_unique(im, A, (0, 0, 7, 2)))
        im.putpixel((0, 7), A)  # violation outside the zone
        self.assertFalse(check_zone_unique(im, A, (0, 0, 7, 2)))

    def test_roster_variants_are_well_formed(self):
        bases = {"extra_man", "extra_woman", "extra_elder", "extra_kid"}
        for name, (base, mapping, _region) in EXTRAS_VARIANTS.items():
            self.assertIn(base, bases, name)
            self.assertTrue(mapping, name)
            targets = list(mapping.values())
            self.assertEqual(len(set(targets)), len(targets), name)

    def test_build_variant_applies_roster_mapping(self):
        out = build_variant(sprite(), "man_ink_top")
        self.assertEqual(out.getpixel((2, 4)), C)


if __name__ == "__main__":
    unittest.main()


class SkinAxisAndReservations(unittest.TestCase):
    def test_skin_shift_moves_every_tier_one_step(self):
        from tools.art_pipeline.recolor import SKIN_SHIFT, apply_mapping
        im = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
        im.putpixel((0, 0), from_hex("#D4A068"))
        im.putpixel((1, 0), from_hex("#C68239"))
        im.putpixel((2, 0), from_hex("#B1552E"))
        out = apply_mapping(im, SKIN_SHIFT)
        self.assertEqual(out.getpixel((0, 0)), from_hex("#C68239"))
        self.assertEqual(out.getpixel((1, 0)), from_hex("#B1552E"))
        self.assertEqual(out.getpixel((2, 0)), from_hex("#680828"))

    def test_skin_shift_excludes_man_hair(self):
        from tools.art_pipeline.recolor import apply_skin_shift
        im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        im.putpixel((5, 2), from_hex("#B1552E"))   # hair highlight row
        im.putpixel((5, 20), from_hex("#B1552E"))  # hand
        out = apply_skin_shift(im, "extra_man")
        self.assertEqual(out.getpixel((5, 2)), from_hex("#B1552E"))   # preserved
        self.assertEqual(out.getpixel((5, 20)), from_hex("#680828"))  # shifted

    def test_double_shift_refused_as_ramp_collapse(self):
        from tools.art_pipeline.recolor import SKIN_SHIFT, apply_mapping
        double = {src: SKIN_SHIFT.get(dst, dst) for src, dst in SKIN_SHIFT.items()}
        with self.assertRaises(ValueError):
            apply_mapping(sprite(), double)

    def test_roster_respects_reserved_identity(self):
        from tools.art_pipeline.recolor import roster_respects_reservations
        self.assertEqual(roster_respects_reservations(), [])
