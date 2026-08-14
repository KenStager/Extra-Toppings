import unittest

from PIL import Image

from tools.art_pipeline.contact_sheets import SheetEntry, build_sheet
from tools.art_pipeline.previews import enlarge, reduce_nearest


def tile(color: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", (16, 16), color)


class ContactSheetAssembly(unittest.TestCase):
    def test_enlarge_is_nearest_neighbor(self) -> None:
        im = Image.new("RGBA", (2, 1))
        im.putpixel((0, 0), (255, 0, 0, 255))
        im.putpixel((1, 0), (0, 0, 255, 255))
        big = enlarge(im, 8)
        self.assertEqual(big.size, (16, 8))
        self.assertEqual(big.getpixel((7, 7)), (255, 0, 0, 255))
        self.assertEqual(big.getpixel((8, 0)), (0, 0, 255, 255))

    def test_reduce_nearest_is_deterministic(self) -> None:
        src = enlarge(tile((10, 200, 30, 255)), 2)
        small = reduce_nearest(src, 16, 16)
        self.assertEqual(small.size, (16, 16))
        self.assertEqual(small.getpixel((5, 5)), (10, 200, 30, 255))

    def test_sheet_layout_and_labels(self) -> None:
        entries = [
            SheetEntry("pizza_whole_01", tile((200, 40, 40, 255)), status="PASS"),
            SheetEntry("pizza_whole_02", tile((240, 230, 200, 255)), status="FAIL"),
            SheetEntry("pizza_whole_03", tile((60, 30, 40, 255))),
        ]
        sheet = build_sheet(entries, scale=4, columns=2, title="review")
        self.assertEqual(sheet.mode, "RGBA")
        # 2 columns x 2 rows of (16*4 + 2*12)-wide cells plus outer padding
        self.assertEqual(sheet.width, 2 * (16 * 4 + 24) + 24)
        self.assertGreater(sheet.height, 2 * (16 * 4))

    def test_empty_sheet_refused(self) -> None:
        with self.assertRaises(ValueError):
            build_sheet([])


if __name__ == "__main__":
    unittest.main()
