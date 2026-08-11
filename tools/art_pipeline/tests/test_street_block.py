"""street_block law tests — synthetic images only, no private assets."""

from __future__ import annotations

import unittest

from PIL import Image

from tools.art_pipeline.street_block import (
    FLANK_RAMP,
    GLASS_RAMP,
    WALK_RAMP,
    a2_blob_fill,
    column_stamp,
    desaturate_warm,
    flank_recolor,
    luminance_ramp,
    place_on_base,
    place_with_contact_shadow,
    recolor_family,
    tree_well,
    upper_story_band,
    worn_edge_line,
)


def _flat(w: int, h: int, color: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", (w, h), color)


class A2BlobFillTests(unittest.TestCase):
    def test_inner_quadrants_assemble_the_fill(self) -> None:
        sheet = _flat(32, 48, (0, 0, 0, 255))
        # paint each inner 8x8 quadrant a distinct color
        quads = {
            (8, 24): (10, 0, 0, 255), (16, 24): (0, 10, 0, 255),
            (8, 32): (0, 0, 10, 255), (16, 32): (10, 10, 0, 255),
        }
        for (qx, qy), color in quads.items():
            for y in range(qy, qy + 8):
                for x in range(qx, qx + 8):
                    sheet.putpixel((x, y), color)
        fill = a2_blob_fill(sheet, 0, 0)
        self.assertEqual(fill.size, (16, 16))
        self.assertEqual(fill.getpixel((0, 0)), quads[(8, 24)])
        self.assertEqual(fill.getpixel((15, 0)), quads[(16, 24)])
        self.assertEqual(fill.getpixel((0, 15)), quads[(8, 32)])
        self.assertEqual(fill.getpixel((15, 15)), quads[(16, 32)])


class RampTests(unittest.TestCase):
    def test_luminance_extremes_hit_ramp_ends(self) -> None:
        img = _flat(2, 1, (0, 0, 0, 255))
        img.putpixel((1, 0), (255, 255, 255, 255))
        out = luminance_ramp(img, WALK_RAMP)
        self.assertEqual(out.getpixel((0, 0))[:3], WALK_RAMP[0])
        self.assertEqual(out.getpixel((1, 0))[:3], WALK_RAMP[-1])

    def test_transparent_pixels_untouched(self) -> None:
        img = _flat(1, 1, (0, 0, 0, 0))
        out = luminance_ramp(img, WALK_RAMP)
        self.assertEqual(out.getpixel((0, 0)), (0, 0, 0, 0))

    def test_family_gate_scopes_the_recolor(self) -> None:
        img = _flat(2, 1, (200, 40, 40, 255))          # red family member
        img.putpixel((1, 0), (40, 200, 40, 255))       # non-member
        out = recolor_family(img, WALK_RAMP, lambda r, g, b: r > g)
        self.assertEqual(out.getpixel((1, 0)), (40, 200, 40, 255))
        self.assertNotEqual(out.getpixel((0, 0)), (200, 40, 40, 255))


class FlankRecolorTests(unittest.TestCase):
    def test_blue_family_becomes_dark_glass(self) -> None:
        img = _flat(1, 20, (100, 150, 255, 255))
        out = flank_recolor(img, sign_rows=0)
        self.assertIn(out.getpixel((0, 10))[:3], GLASS_RAMP)

    def test_bright_neutral_body_flattens_to_one_wall_tone(self) -> None:
        img = _flat(2, 20, (251, 251, 232, 255))       # fascia specular
        for y in range(20):
            img.putpixel((1, y), (157, 156, 156, 255))  # fascia body
        out = flank_recolor(img, sign_rows=0)
        self.assertEqual(out.getpixel((0, 10))[:3], FLANK_RAMP[3])

    def test_sign_rows_exempt_from_flattening(self) -> None:
        img = _flat(1, 20, (251, 251, 232, 255))
        out = flank_recolor(img, sign_rows=20)          # everything is sign
        self.assertEqual(out.getpixel((0, 0))[:3], FLANK_RAMP[4])


class ColumnStampTests(unittest.TestCase):
    def test_box_takes_reference_column_rows(self) -> None:
        img = _flat(8, 4, (1, 2, 3, 255))
        for y in range(4):
            img.putpixel((6, y), (50 + y, 0, 0, 255))   # reference column
        out = column_stamp(img, (1, 1, 4, 2), ref_x=6)
        self.assertEqual(out.getpixel((2, 1)), (51, 0, 0, 255))
        self.assertEqual(out.getpixel((4, 2)), (52, 0, 0, 255))
        self.assertEqual(out.getpixel((0, 0)), (1, 2, 3, 255))   # outside box
        self.assertEqual(out.getpixel((5, 3)), (1, 2, 3, 255))


class CodeAssetTests(unittest.TestCase):
    def test_tree_well_dimensions_and_grate(self) -> None:
        well = tree_well()
        self.assertEqual(well.size, (58, 22))
        self.assertEqual(well.getpixel((1, 1))[:3], (44, 36, 28))   # soil
        self.assertEqual(well.getpixel((6, 5))[:3], (76, 70, 62))   # grate rib

    def test_upper_story_band_shape_and_cornice(self) -> None:
        band = upper_story_band(width=96, height=56)
        self.assertEqual(band.size, (96, 56))
        self.assertEqual(band.getpixel((10, 53))[:3], (52, 44, 38))  # cornice

    def test_worn_edge_line_is_deterministic_with_gaps(self) -> None:
        a = _flat(64, 4, (0, 0, 0, 255))
        b = _flat(64, 4, (0, 0, 0, 255))
        worn_edge_line(a, 1)
        worn_edge_line(b, 1)
        self.assertEqual(list(a.getdata()), list(b.getdata()))
        row = [a.getpixel((x, 1))[:3] for x in range(64)]
        self.assertIn((168, 152, 118), row)                          # painted
        self.assertIn((0, 0, 0), row)                                # worn gap


class PlacementTests(unittest.TestCase):
    def _sprite(self) -> Image.Image:
        sprite = _flat(10, 10, (0, 0, 0, 0))
        for y in range(2, 8):
            for x in range(3, 7):
                sprite.putpixel((x, y), (200, 0, 0, 255))
        return sprite

    def test_contact_shadow_anchors_to_content_not_canvas(self) -> None:
        canvas = _flat(40, 40, (255, 255, 255, 255))
        out = place_with_contact_shadow(canvas, self._sprite(), 10, 10, 6)
        # content bottom row is sprite y=7 -> canvas y=17; shadow centre y=15..21
        under_content = out.getpixel((15, 18))
        below_canvas_bottom = out.getpixel((15, 22))
        self.assertLess(sum(under_content[:3]), 255 * 3)             # darkened
        self.assertEqual(below_canvas_bottom[:3], (255, 255, 255))   # untouched

    def test_place_on_base_seats_content_bottom_on_base_row(self) -> None:
        canvas = _flat(40, 40, (255, 255, 255, 255))
        out = place_on_base(canvas, self._sprite(), 10, 30, None)
        # content rows land at base_y-6 .. base_y-1
        self.assertEqual(out.getpixel((15, 29))[:3], (200, 0, 0))
        self.assertEqual(out.getpixel((15, 30))[:3], (255, 255, 255))


class DesaturateTests(unittest.TestCase):
    def test_saturation_drops_and_alpha_survives(self) -> None:
        img = _flat(1, 1, (255, 0, 0, 200))
        out = desaturate_warm(img)
        r, g, b, a = out.getpixel((0, 0))
        self.assertEqual(a, 200)
        self.assertLess(r - min(g, b), 255)                          # pulled toward gray
        self.assertGreater(g, 0)


if __name__ == "__main__":
    unittest.main()
