import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.art_pipeline.palettes import (
    extract_palette,
    from_hex,
    merge_palettes,
    save_palette_image,
    to_hex,
)

RED = (200, 40, 40, 255)
CREAM = (240, 230, 200, 255)
DARK = (60, 30, 40, 255)


def swatched() -> Image.Image:
    im = Image.new("RGBA", (8, 4), (0, 0, 0, 0))
    px = im.load()
    for x in range(6):
        px[x, 0] = CREAM  # 6 cream
    for x in range(4):
        px[x, 1] = RED  # 4 red
    for x in range(2):
        px[x, 2] = DARK  # 2 dark
    px[7, 3] = (10, 10, 10, 128)  # soft alpha must be excluded
    return im


class PaletteExtraction(unittest.TestCase):
    def test_frequency_order_and_alpha_exclusion(self) -> None:
        self.assertEqual(extract_palette(swatched()), [CREAM, RED, DARK])

    def test_hex_round_trip(self) -> None:
        self.assertEqual(to_hex(RED), "#c82828")
        self.assertEqual(from_hex("#c82828"), RED)

    def test_merge_preserves_order_without_duplicates(self) -> None:
        merged = merge_palettes([CREAM, RED], [RED, DARK])
        self.assertEqual(merged, [CREAM, RED, DARK])

    def test_palette_image_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "palette.png"
            save_palette_image([CREAM, RED, DARK], path, swatch=4)
            with Image.open(path) as strip:
                self.assertEqual(strip.size, (12, 4))
                self.assertEqual(set(extract_palette(strip)), {CREAM, RED, DARK})


if __name__ == "__main__":
    unittest.main()
