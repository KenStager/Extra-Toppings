"""Pins for the animation validators — the Phase A probe's measured
contracts (composite-exactness, union-palette census, baseline)."""
from __future__ import annotations

import unittest

from PIL import Image

from tools.art_pipeline.animation_validate import (
    baseline_rows,
    binary_alpha,
    composite_exact,
    frame_delta,
    off_palette_count,
    visible_palette,
)


def sprite(body: tuple[int, int, int], under: tuple[int, int, int]) -> Image.Image:
    """4x4 test sprite: a 2x2 visible body, `under` as the RGB hidden
    beneath transparent pixels (the vendor re-encoding surface)."""
    im = Image.new("RGBA", (4, 4), (*under, 0))
    for y in (1, 2):
        for x in (1, 2):
            im.putpixel((x, y), (*body, 255))
    return im


class CompositeExactTests(unittest.TestCase):
    def test_transparent_rgb_reencoding_is_ignored(self) -> None:
        # the probe's 66% false alarm: same composite, different
        # hidden RGB — composite-exact by definition
        a = sprite((10, 20, 30), (0, 0, 0))
        b = sprite((10, 20, 30), (99, 99, 99))
        self.assertNotEqual(list(a.getdata()), list(b.getdata()))
        self.assertTrue(composite_exact(a, b))

    def test_visible_pixel_change_refuses(self) -> None:
        a = sprite((10, 20, 30), (0, 0, 0))
        b = sprite((10, 20, 31), (0, 0, 0))
        self.assertFalse(composite_exact(a, b))

    def test_alpha_mask_change_refuses(self) -> None:
        a = sprite((10, 20, 30), (0, 0, 0))
        b = sprite((10, 20, 30), (0, 0, 0))
        b.putpixel((3, 3), (10, 20, 30, 255))
        self.assertFalse(composite_exact(a, b))


class CensusTests(unittest.TestCase):
    def test_binary_alpha(self) -> None:
        a = sprite((10, 20, 30), (0, 0, 0))
        self.assertTrue(binary_alpha(a))
        a.putpixel((0, 0), (1, 2, 3, 128))
        self.assertFalse(binary_alpha(a))

    def test_union_palette_census(self) -> None:
        # the a2 lesson: an interpolation endpoint wears the OTHER
        # sprite's palette; the union census clears what the
        # single-palette census false-alarmed
        start = sprite((10, 20, 30), (0, 0, 0))
        end = sprite((200, 100, 50), (0, 0, 0))
        single = visible_palette(start)
        union = single | visible_palette(end)
        self.assertEqual(off_palette_count(end, single), 4)
        self.assertEqual(off_palette_count(end, union), 0)

    def test_baseline_and_delta(self) -> None:
        a = sprite((10, 20, 30), (0, 0, 0))
        b = sprite((10, 20, 30), (0, 0, 0))
        self.assertEqual(baseline_rows([a, b]), [2, 2])
        self.assertEqual(frame_delta(a, b), 0)
        b.putpixel((1, 1), (9, 9, 9, 255))
        self.assertEqual(frame_delta(a, b), 1)


if __name__ == "__main__":
    unittest.main()
