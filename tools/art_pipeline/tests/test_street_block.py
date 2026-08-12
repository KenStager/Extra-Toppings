"""street_block law tests — synthetic images only, no private assets."""

from __future__ import annotations

import unittest

from PIL import Image

from tools.art_pipeline.street_block import (
    AFTER_DARK_VARIANTS,
    ASPHALT_RAMP,
    CROSSWALK_PAINT,
    CURB_TONES,
    DISTRICT_REGISTERS,
    FLANK_RAMP,
    GLASS_RAMP,
    SLATE_RAMP,
    WALK_RAMP,
    WELL_METALS,
    a2_blob_fill,
    column_stamp,
    crosswalk_paint,
    crosswalk_paint_vertical,
    curb_corner_anchor,
    curb_vertical_strip,
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


class StreetKitTests(unittest.TestCase):
    """Curb corners + crosswalk: the kit pieces and their wear laws."""

    def test_crosswalk_is_deterministic(self) -> None:
        a = crosswalk_paint(120)
        b = crosswalk_paint(120)
        self.assertEqual(list(a.getdata()), list(b.getdata()))

    def test_crosswalk_is_paint_only_with_binary_alpha(self) -> None:
        im = crosswalk_paint(120)
        seen = {im.getpixel((x, y)) for y in range(im.height) for x in range(im.width)}
        self.assertLessEqual(
            seen, {(*CROSSWALK_PAINT, 255), (0, 0, 0, 0)}
        )

    def test_crosswalk_lays_only_whole_centered_bars(self) -> None:
        # depth 120 at pitch 16 -> 7 whole bars centered: rows 8..111
        im = crosswalk_paint(120, corridor=40, stripe=8, gap=8)
        painted_rows = {
            y for y in range(im.height)
            if any(im.getpixel((x, y))[3] for x in range(im.width))
        }
        self.assertEqual(min(painted_rows), 8)
        self.assertEqual(max(painted_rows), 111)
        self.assertEqual(len(painted_rows), 7 * 8)

    def test_crosswalk_wear_obeys_the_recorded_paint_rule(self) -> None:
        from tools.art_pipeline.street_block import paint_wear_drop

        im = crosswalk_paint(120)
        for y in range(8, 16):                   # first bar, base 4% + edges
            pct = 10 if y in (8, 15) else 4
            for x in range(im.width):
                expected = 0 if paint_wear_drop(x, y, pct) else 255
                self.assertEqual(im.getpixel((x, y))[3], expected, (x, y))

    def test_crosswalk_wheel_bands_wear_hardest(self) -> None:
        worn = crosswalk_paint(120, wheel_bands=((40, 120),))
        fresh = crosswalk_paint(120)

        def paint_px(im, y0, y1):
            return sum(
                1 for y in range(y0, y1) for x in range(im.width)
                if im.getpixel((x, y))[3]
            )

        self.assertEqual(paint_px(worn, 0, 40), paint_px(fresh, 0, 40))
        self.assertLess(paint_px(worn, 40, 120), paint_px(fresh, 40, 120) * 0.85)

    def test_vertical_crosswalk_is_the_transpose(self) -> None:
        h = crosswalk_paint(96, corridor=32)
        v = crosswalk_paint_vertical(96, corridor=32)
        self.assertEqual(v.size, (96, 32))
        self.assertEqual(
            h.getpixel((5, 20)), v.getpixel((20, 5))
        )

    def test_vertical_strip_palette_is_citywide_curb_concrete(self) -> None:
        strip = curb_vertical_strip(64)
        seen = {
            strip.getpixel((x, y))[:3]
            for y in range(strip.height) for x in range(strip.width)
        }
        self.assertLessEqual(seen, set(CURB_TONES))

    def test_vertical_strip_road_edge_faces_the_named_side(self) -> None:
        east = curb_vertical_strip(32, road_side="east")
        west = curb_vertical_strip(32, road_side="west")
        self.assertEqual(east.getpixel((9, 5))[:3], CURB_TONES[0])
        self.assertEqual(east.getpixel((0, 5))[:3], CURB_TONES[4])
        self.assertEqual(west.getpixel((0, 5))[:3], CURB_TONES[0])
        with self.assertRaisesRegex(ValueError, "road_side"):
            curb_vertical_strip(32, road_side="north")

    def test_corner_anchor_contract(self) -> None:
        se = curb_corner_anchor("se")
        self.assertEqual(se.size, (32, 32))
        seen = {
            se.getpixel((x, y))
            for y in range(32) for x in range(32)
        }
        opaque = {c[:3] for c in seen if c[3] == 255}
        self.assertLessEqual(opaque, set(CURB_TONES))
        self.assertIn((0, 0, 0, 0), seen)                    # walk + road alpha
        # walk interior transparent, road corner transparent, band opaque
        self.assertEqual(se.getpixel((5, 5))[3], 0)
        self.assertEqual(se.getpixel((31, 31))[3], 0)
        self.assertEqual(se.getpixel((5, 24))[3], 255)

    def test_corner_anchor_sw_is_the_mirror(self) -> None:
        se, sw = curb_corner_anchor("se"), curb_corner_anchor("sw")
        self.assertEqual(se.getpixel((0, 20)), sw.getpixel((31, 20)))
        with self.assertRaisesRegex(ValueError, "orientation"):
            curb_corner_anchor("ne")

    def test_kit_constants_disjoint_from_registers_and_reserved(self) -> None:
        # The citywide-infrastructure ruling as exact colors: crosswalk
        # paint and curb concrete never collide with a register value
        # (night maps are exact-color passes; a shared value would let
        # a district shift catch the infrastructure).
        infra = set(CURB_TONES) | {CROSSWALK_PAINT, (168, 152, 118), (190, 158, 74)}
        self.assertEqual(len(infra), 8)                      # all distinct
        for name, register in DISTRICT_REGISTERS.items():
            for surface, ramp in register.items():
                hits = [tone for tone in ramp if tone in infra]
                self.assertEqual(hits, [], f"{name}/{surface}")
        self.assertFalse(infra & set(WELL_METALS))
        self.assertFalse(infra & set(SLATE_RAMP))


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


def _lawful_staging() -> dict:
    """Minimal lawful scene-unit instance (synthetic, decision 3 shape)."""
    return {
        "schema_version": 3,
        "district": "old_harbor",
        "bands": {
            "upper_stories": [0, 56], "buildings": [56, 152], "walk": [152, 208],
            "curb": [208, 224], "road_parking": [224, 264], "road_travel": [264, 344],
            "far_curb_line": [344, 348], "far_walk": [348, 360],
        },
        "wall_line_base_y": 172,
        "curb_line_base_y": 214,
        "slots": [
            {"id": "flank_left", "span": [0, 127], "business": "a"},
            {"id": "center", "span": [128, 384], "business": "b"},
        ],
        "doorways": [[294, 319]],
        "props": {
            "bench": {"line": "wall", "span": [392, 451]},
            "hydrant": {"line": "curb", "span": [360, 375]},
        },
    }


class SceneStagingValidatorTests(unittest.TestCase):
    """Decision 3: the unit's laws refuse, never repair."""

    def test_lawful_instance_passes(self) -> None:
        from tools.art_pipeline.street_block import validate_scene_staging

        validate_scene_staging(_lawful_staging())

    def _refuses(self, mutate, fragment: str) -> None:
        from tools.art_pipeline.street_block import validate_scene_staging

        data = _lawful_staging()
        mutate(data)
        with self.assertRaisesRegex(ValueError, fragment):
            validate_scene_staging(data)

    def test_v2_files_are_refused_not_migrated(self) -> None:
        self._refuses(lambda d: d.update(schema_version=2), "schema_version")

    def test_band_gap_refused(self) -> None:
        self._refuses(lambda d: d["bands"].update(curb=[210, 224]), "gap or overlap")

    def test_band_coverage_refused(self) -> None:
        self._refuses(lambda d: d["bands"].update(far_walk=[348, 356]), "0..360")

    def test_attachment_lines_must_sit_in_their_bands(self) -> None:
        self._refuses(lambda d: d.update(wall_line_base_y=210), "wall_line_base_y")
        self._refuses(lambda d: d.update(curb_line_base_y=204), "curb_line_base_y")

    def test_unknown_district_refused(self) -> None:
        self._refuses(lambda d: d.update(district="uptown"), "unknown district")

    def test_overlapping_slots_refused(self) -> None:
        self._refuses(
            lambda d: d["slots"].append({"id": "x", "span": [100, 200], "business": "c"}),
            "overlap",
        )

    def test_doorway_outside_slots_refused(self) -> None:
        self._refuses(lambda d: d["doorways"].append([500, 520]), "no slot")

    def test_wall_prop_on_doorway_refused(self) -> None:
        self._refuses(
            lambda d: d["props"].update(crate={"line": "wall", "span": [300, 330]}),
            "blocks doorway",
        )

    def test_wall_and_curb_props_cannot_share_an_x_slot(self) -> None:
        self._refuses(
            lambda d: d["props"].update(crate={"line": "wall", "span": [350, 370]}),
            "share an x-slot",
        )

    def test_lawful_crosswalk_block_passes(self) -> None:
        from tools.art_pipeline.street_block import validate_scene_staging

        data = _lawful_staging()
        data["crosswalk"] = {"x": [280, 320]}
        validate_scene_staging(data)

    def test_crosswalk_out_of_scene_refused(self) -> None:
        self._refuses(
            lambda d: d.update(crosswalk={"x": [620, 660]}), "out of scene"
        )

    def test_crosswalk_narrower_than_a_figure_refused(self) -> None:
        self._refuses(
            lambda d: d.update(crosswalk={"x": [280, 300]}), "narrower"
        )

    def test_crosswalk_bad_pitch_refused(self) -> None:
        self._refuses(
            lambda d: d.update(crosswalk={"x": [280, 320], "stripe": 0}),
            "must be positive",
        )


class DistrictRegisterTests(unittest.TestCase):
    """Decision 2 laws (ratified 2026-08-11) over DISTRICT_REGISTERS."""

    DISTRICTS = ("old_harbor", "little_sicily", "university", "meadows")
    TIER_COUNTS = {"road": 4, "walk": 4, "storefront": 5, "accent": 4}

    def test_every_district_has_fixed_tier_counts(self) -> None:
        self.assertEqual(tuple(DISTRICT_REGISTERS), self.DISTRICTS)
        for name, register in DISTRICT_REGISTERS.items():
            self.assertEqual(
                {s: len(r) for s, r in register.items()}, self.TIER_COUNTS, name
            )

    def test_old_harbor_ratifies_the_block_proven_ramps_by_reference(self) -> None:
        oh = DISTRICT_REGISTERS["old_harbor"]
        self.assertIs(oh["road"], ASPHALT_RAMP)
        self.assertIs(oh["walk"], WALK_RAMP)
        self.assertIs(oh["storefront"], FLANK_RAMP)
        # The ratified values themselves, pinned verbatim (the interim
        # picks recorded in e16_recolor_derivations.json).
        self.assertEqual(
            oh["road"], [(41, 38, 34), (46, 42, 38), (50, 46, 41), (54, 49, 44)]
        )
        self.assertEqual(
            oh["walk"],
            [(94, 86, 74), (140, 129, 112), (166, 154, 134), (186, 174, 152)],
        )

    def test_register_values_pairwise_distinct_within_a_district(self) -> None:
        for name, register in DISTRICT_REGISTERS.items():
            values = [tone for ramp in register.values() for tone in ramp]
            self.assertEqual(len(values), 17, name)
            self.assertEqual(len(set(values)), 17, name)

    def test_no_register_value_is_a_cast_wardrobe_vehicle_or_well_tone(self) -> None:
        # Night maps (decision 5) are exact-color passes over composed
        # scenes: a shared value would let a surface shift catch a
        # bystander, a parked sedan, or a tree-well grate.
        from tools.art_pipeline.recolor import (
            BOTTOM_TARGETS,
            HAIR_TARGETS,
            RESERVED_TARGETS,
            SKIN_SHIFT,
            TOP_TARGETS,
        )

        forbidden: set[tuple[int, int, int]] = set()
        for rgba in RESERVED_TARGETS:
            forbidden.add(rgba[:3])
        for targets in (TOP_TARGETS, BOTTOM_TARGETS, HAIR_TARGETS):
            forbidden.update(rgba[:3] for rgba in targets.values())
        for src, dst in SKIN_SHIFT.items():
            forbidden.update((src[:3], dst[:3]))
        forbidden.update(SLATE_RAMP)
        forbidden.update(WELL_METALS)
        for name, register in DISTRICT_REGISTERS.items():
            for surface, ramp in register.items():
                hits = [tone for tone in ramp if tone in forbidden]
                self.assertEqual(hits, [], f"{name}/{surface}")

    def test_flat_road_law_holds_citywide(self) -> None:
        for name, register in DISTRICT_REGISTERS.items():
            road = register["road"]
            lums = [0.3 * r + 0.59 * g + 0.11 * b for r, g, b in road]
            self.assertEqual(lums, sorted(lums), name)
            for lo, hi in zip(lums, lums[1:]):
                self.assertLessEqual(hi - lo, 6.0, name)

    def test_register_mapping_is_bijective_and_apply_safe(self) -> None:
        from tools.art_pipeline.recolor import apply_mapping
        from tools.art_pipeline.street_block import register_mapping

        for to_district in self.DISTRICTS:
            for surface in self.TIER_COUNTS:
                mapping = register_mapping(surface, to_district)
                self.assertEqual(len(mapping), self.TIER_COUNTS[surface])
                # apply_mapping's collapse refusal must accept every
                # register move; a 1x1 canvas keeps the check cheap.
                out = apply_mapping(_flat(1, 1, (*ASPHALT_RAMP[0], 255)), mapping)
                self.assertEqual(out.size, (1, 1))

    def test_after_dark_slots_exist_and_are_unruled(self) -> None:
        self.assertEqual(set(AFTER_DARK_VARIANTS), set(DISTRICT_REGISTERS))
        self.assertTrue(all(v is None for v in AFTER_DARK_VARIANTS.values()))


if __name__ == "__main__":
    unittest.main()
