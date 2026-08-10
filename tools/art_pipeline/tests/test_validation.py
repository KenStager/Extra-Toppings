import unittest

from PIL import Image

from tools.art_pipeline.validation import validate_candidate

PALETTE = [
    (60, 30, 40, 255),  # outline
    (240, 230, 200, 255),  # cheese
    (200, 40, 40, 255),  # tomato
]


def good_candidate() -> Image.Image:
    """A 12x12 filled disc-ish blob centered on a 16x16 transparent canvas."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = im.load()
    for y in range(2, 14):
        for x in range(2, 14):
            on_border = x in (2, 13) or y in (2, 13)
            px[x, y] = PALETTE[0] if on_border else PALETTE[1]
    px[8, 8] = PALETTE[2]
    return im


class CandidateValidation(unittest.TestCase):
    def test_good_candidate_passes_every_check(self) -> None:
        result = validate_candidate(good_candidate(), PALETTE)
        self.assertTrue(result.passed, result.notes)

    def test_wrong_size_fails(self) -> None:
        result = validate_candidate(good_candidate().crop((0, 0, 15, 16)), PALETTE)
        self.assertFalse(result.checks["dimensions"])

    def test_soft_alpha_fails(self) -> None:
        im = good_candidate()
        im.putpixel((8, 9), (200, 40, 40, 120))
        self.assertFalse(validate_candidate(im, PALETTE).checks["hard_alpha"])

    def test_off_palette_color_fails(self) -> None:
        im = good_candidate()
        im.putpixel((8, 9), (1, 255, 1, 255))
        result = validate_candidate(im, PALETTE)
        self.assertFalse(result.checks["palette_adherence"])
        self.assertIn("#01ff01", " ".join(result.notes))

    def test_garbage_speck_fails(self) -> None:
        im = good_candidate()
        im.putpixel((0, 15), PALETTE[2])  # lone corner speck
        result = validate_candidate(im, PALETTE)
        self.assertFalse(result.checks["no_garbage_pixels"])
        self.assertFalse(result.checks["transparent_corners"])
        self.assertFalse(result.checks["single_silhouette"])

    def test_large_satellite_fails_single_silhouette(self) -> None:
        im = good_candidate()
        # 3x1 blob on row 0: row 1 stays clear, so it is NOT 8-connected to
        # the main block starting at (2,2); area 3 passes the speck check.
        for x in range(3):
            im.putpixel((x, 0), PALETTE[1])
        result = validate_candidate(im, PALETTE)
        self.assertTrue(result.checks["no_garbage_pixels"])
        self.assertFalse(result.checks["single_silhouette"])

    def test_connected_prop_passes_single_silhouette(self) -> None:
        result = validate_candidate(good_candidate(), PALETTE)
        self.assertTrue(result.checks["single_silhouette"])

    def test_edge_clipping_fails(self) -> None:
        im = good_candidate()
        for x in range(3, 13):
            im.putpixel((x, 0), PALETTE[0])  # long run on top edge
        self.assertFalse(validate_candidate(im, PALETTE).checks["no_clipping"])

    def test_fully_transparent_fails(self) -> None:
        empty = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        result = validate_candidate(empty, PALETTE)
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()


class RectangularBboxMinimum(unittest.TestCase):
    """Character contract: min_bbox may be a (width, height) pair."""

    def _figure(self, w: int, h: int) -> Image.Image:
        im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        for y in range(4, 4 + h):
            for x in range(12, 12 + w):
                im.putpixel((x, y), (168, 16, 49, 255))
        return im

    def test_tall_narrow_figure_passes_pair_but_fails_square(self):
        from tools.art_pipeline.validation import validate_candidate
        palette = [(168, 16, 49, 255)]
        figure = self._figure(10, 24)
        pair = validate_candidate(
            figure, palette, expected_size=(32, 32), min_bbox=(8, 18)
        )
        self.assertTrue(pair.checks["bounding_box"])
        square = validate_candidate(
            figure, palette, expected_size=(32, 32), min_bbox=14
        )
        self.assertFalse(square.checks["bounding_box"])

    def test_pair_minimum_still_refuses_a_squat_figure(self):
        from tools.art_pipeline.validation import validate_candidate
        palette = [(168, 16, 49, 255)]
        squat = self._figure(10, 12)
        result = validate_candidate(
            squat, palette, expected_size=(32, 32), min_bbox=(8, 18)
        )
        self.assertFalse(result.checks["bounding_box"])
