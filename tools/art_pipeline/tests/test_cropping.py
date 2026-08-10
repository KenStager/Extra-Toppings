import unittest

from PIL import Image

from tools.art_pipeline.cropping import crop_cells, crop_px


def checkerboard(width: int, height: int) -> Image.Image:
    im = Image.new("RGBA", (width, height))
    px = im.load()
    for y in range(height):
        for x in range(width):
            px[x, y] = (x % 256, y % 256, (x * y) % 256, 255)
    return im


class CropGeometry(unittest.TestCase):
    def test_exact_pixel_crop_no_resampling(self) -> None:
        src = checkerboard(64, 48)
        crop = crop_px(src, 5, 7, 10, 9)
        self.assertEqual(crop.size, (10, 9))
        for y in range(9):
            for x in range(10):
                self.assertEqual(crop.getpixel((x, y)), src.getpixel((x + 5, y + 7)))

    def test_cell_crop_matches_pixel_math(self) -> None:
        src = checkerboard(256, 256)
        crop = crop_cells(src, 12, 5, 15, 6, cell=16)
        self.assertEqual(crop.size, (64, 32))
        self.assertEqual(crop.getpixel((0, 0)), src.getpixel((192, 80)))
        self.assertEqual(crop.getpixel((63, 31)), src.getpixel((255, 111)))

    def test_out_of_bounds_refused(self) -> None:
        src = checkerboard(32, 32)
        with self.assertRaises(ValueError):
            crop_px(src, 20, 0, 16, 16)
        with self.assertRaises(ValueError):
            crop_px(src, -1, 0, 8, 8)
        with self.assertRaises(ValueError):
            crop_cells(src, 1, 1, 0, 1)


if __name__ == "__main__":
    unittest.main()
