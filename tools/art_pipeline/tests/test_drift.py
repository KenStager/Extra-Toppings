import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.art_pipeline.drift import (
    calibrate_band,
    diff_fraction,
    histogram_l1,
    judge_probe,
)

PALETTE = [(60, 30, 40, 255), (240, 230, 200, 255), (200, 40, 40, 255)]


def blob(tweak: int = 0) -> Image.Image:
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for y in range(4, 28):
        for x in range(4, 28):
            border = x in (4, 27) or y in (4, 27)
            im.putpixel((x, y), PALETTE[0] if border else PALETTE[1])
    if tweak:
        for i in range(tweak):
            im.putpixel((6 + i, 6), PALETTE[2])
    return im


class DriftMetrics(unittest.TestCase):
    def test_identical_images_zero_metrics(self) -> None:
        self.assertEqual(diff_fraction(blob(), blob()), 0.0)
        self.assertEqual(histogram_l1(blob(), blob()), 0.0)

    def test_small_change_measured_proportionally(self) -> None:
        frac = diff_fraction(blob(), blob(tweak=4))
        self.assertAlmostEqual(frac, 4 / 1024)


class Verdicts(unittest.TestCase):
    def _paths(self, tmp: str, a: Image.Image, b: Image.Image) -> tuple[Path, Path]:
        pa, pb = Path(tmp) / "a.png", Path(tmp) / "b.png"
        a.save(pa)
        b.save(pb)
        return pa, pb

    def test_tier_a_on_identical_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pa, pb = self._paths(tmp, blob(), blob())
            v = judge_probe(pa, pb, PALETTE, 0.1, 0.05)
            self.assertEqual(v.tier, "A")

    def test_tier_b_within_band(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pa, pb = self._paths(tmp, blob(), blob(tweak=4))
            v = judge_probe(pa, pb, PALETTE, max_diff_frac=0.1, max_hist_l1=0.05)
            self.assertEqual(v.tier, "B")

    def test_tier_c_beyond_band(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pa, pb = self._paths(tmp, blob(), blob(tweak=4))
            v = judge_probe(pa, pb, PALETTE, max_diff_frac=0.001, max_hist_l1=0.0001)
            self.assertEqual(v.tier, "C")

    def test_tier_c_on_offpalette_even_inside_band(self) -> None:
        rogue = blob()
        rogue.putpixel((10, 10), (1, 255, 1, 255))  # off-palette pixel
        with tempfile.TemporaryDirectory() as tmp:
            pa, pb = self._paths(tmp, blob(), rogue)
            v = judge_probe(pa, pb, PALETTE, max_diff_frac=0.5, max_hist_l1=0.5)
            self.assertEqual(v.tier, "C")
            self.assertFalse(v.validator_passed)


class Calibration(unittest.TestCase):
    def test_band_is_max_pairwise_exact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dirs = []
            for i, tweak in enumerate((0, 2, 6)):
                d = Path(tmp) / f"run{i}"
                d.mkdir()
                blob(tweak=tweak).save(d / "probe.png")
                dirs.append(d)
            band = calibrate_band(dirs, ["probe"])
            self.assertAlmostEqual(band["max_diff_frac"], 6 / 1024)


if __name__ == "__main__":
    unittest.main()
