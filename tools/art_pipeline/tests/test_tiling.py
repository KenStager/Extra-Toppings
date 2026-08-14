import unittest

from PIL import Image

from tools.art_pipeline.tiling import (
    eventlessness,
    mirror_fold,
    seam_report_columns,
    seam_report_rows,
    tiled_preview,
)


def uniform(color=(100, 100, 100, 255), size=16) -> Image.Image:
    return Image.new("RGBA", (size, size), color)


class SeamScoring(unittest.TestCase):
    def test_uniform_tile_has_perfect_seam(self) -> None:
        rep = seam_report_columns(uniform())
        self.assertEqual(rep.seam_diff_frac, 0.0)
        self.assertEqual(rep.percentile(), 0.0)

    def test_checkerboard_wraps_perfectly(self) -> None:
        im = Image.new("RGBA", (16, 16))
        for y in range(16):
            for x in range(16):
                on = (x // 2 + y // 2) % 2 == 0
                im.putpixel((x, y), (200, 200, 200, 255) if on else (60, 60, 60, 255))
        col, row = seam_report_columns(im), seam_report_rows(im)
        # the wrap seam behaves exactly like an interior 2px-block boundary
        self.assertLessEqual(col.percentile(), 0.6)
        self.assertLessEqual(row.percentile(), 0.6)

    def test_edge_stripe_breaks_the_wrap(self) -> None:
        im = uniform()
        for y in range(16):
            im.putpixel((0, y), (255, 0, 0, 255))  # bright line at x=0 only
        rep = seam_report_columns(im)
        self.assertEqual(rep.seam_diff_frac, 1.0)
        self.assertGreater(rep.percentile(), 0.9)

    def test_mirror_fold_is_self_tiling(self) -> None:
        quad = Image.new("RGBA", (8, 8))
        for y in range(8):
            for x in range(8):
                quad.putpixel((x, y), (x * 20 % 256, y * 30 % 256, 90, 255))
        tile = mirror_fold(quad)
        self.assertEqual(tile.size, (16, 16))
        self.assertEqual(seam_report_columns(tile).seam_diff_frac, 0.0)
        self.assertEqual(seam_report_rows(tile).seam_diff_frac, 0.0)


class Eventlessness(unittest.TestCase):
    def test_uniform_is_calm_but_one_giant_blob(self) -> None:
        scores = eventlessness(uniform())
        self.assertEqual(scores["largest_blob_frac"], 1.0)
        self.assertEqual(scores["max_local_contrast"], 0.0)

    def test_single_bright_feature_scores_high_contrast(self) -> None:
        im = uniform()
        im.putpixel((8, 8), (255, 255, 255, 255))
        self.assertGreater(eventlessness(im)["max_local_contrast"], 100)


class Preview(unittest.TestCase):
    def test_tiled_preview_dimensions(self) -> None:
        self.assertEqual(tiled_preview(uniform(), 3).size, (48, 48))


if __name__ == "__main__":
    unittest.main()
