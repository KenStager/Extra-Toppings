"""Pins for the interior scene unit's laws (THE HORIZON paper).

One lawful staging passes; every violation class refuses. The
fixture mirrors the DiNapoli instance's shape without depending on
any asset file — the validator is pure data law.
"""
import copy
import unittest

from tools.art_pipeline.interior_scene import validate_interior_staging


def lawful() -> dict:
    return {
        "schema_version": 1,
        "bands": {
            "ceiling": [0, 48], "back_wall": [48, 152],
            "wall_base": [152, 160], "work_floor": [160, 224],
            "counter_run": [224, 240], "customer_floor": [240, 360],
        },
        "wall_line_base_y": 176,
        "counter_line_base_y": 240,
        "floors": {"work": "floor_terracotta",
                   "customer": "floor_checker_cream"},
        "counter": {
            "pieces": [{"asset": "counter_main", "span": [232, 327]},
                       {"asset": "counter_end", "span": [328, 375]}],
            "pass_gap": [376, 408],
        },
        "fixtures": {
            "oven": {"asset": "oven", "span": [40, 103], "line": "wall"},
            "boxes": {"asset": "box_stack", "span": [120, 151], "line": "wall"},
        },
        "corridors": {
            "entry": [440, 480],
            "queue_slots": [[300, 268], [304, 296], [308, 324]],
        },
        "furniture": {
            "fourtop": {"unit": "fourtop", "span": [96, 176], "base_y": 320},
        },
        "decals": [{"type": "flour", "asset": "decal_flour_a",
                    "x": 96, "y": 200}],
        "states": {
            "service": {"oven_state": "lit",
                        "actors": [{"asset": "cast_tony", "x": 56,
                                    "base_y": 208}]},
            "night": {"oven_state": "cold", "actors": []},
        },
    }


class InteriorLaws(unittest.TestCase):
    def test_lawful_instance_passes(self):
        self.assertEqual(validate_interior_staging(lawful()), [])

    def _refused(self, mutate, needle):
        s = copy.deepcopy(lawful())
        mutate(s)
        errs = validate_interior_staging(s)
        self.assertTrue(any(needle in e for e in errs), errs)

    def test_bands_must_sum_to_360(self):
        self._refused(lambda s: s["bands"].update(
            {"customer_floor": [240, 352]}), "must end at 360")

    def test_bands_must_be_contiguous(self):
        self._refused(lambda s: s["bands"].update(
            {"work_floor": [164, 224]}), "contiguous")

    def test_wall_line_lives_in_work_floor(self):
        self._refused(lambda s: s.update(wall_line_base_y=100),
                      "wall_line_base_y")

    def test_counter_line_lives_in_counter_run(self):
        self._refused(lambda s: s.update(counter_line_base_y=300),
                      "counter_line_base_y")

    def test_floor_must_be_known(self):
        self._refused(lambda s: s["floors"].update(work="floor_lava"),
                      "known floor")

    def test_counter_pieces_may_not_overlap(self):
        self._refused(lambda s: s["counter"]["pieces"].append(
            {"asset": "counter_main", "span": [300, 340]}), "overlap")

    def test_pass_gap_is_wide_enough(self):
        self._refused(lambda s: s["counter"].update(pass_gap=[376, 390]),
                      "pass_gap")

    def test_pass_gap_never_covered(self):
        self._refused(lambda s: s["counter"]["pieces"].append(
            {"asset": "counter_end", "span": [370, 400]}),
            "covered by a counter piece")

    def test_wall_fixtures_exclude_x_slots(self):
        self._refused(lambda s: s["fixtures"].update(
            prep={"asset": "prep", "span": [90, 130], "line": "wall"}),
            "overlaps another wall fixture")

    def test_wall_mounted_may_share_a_floor_fixture_slot(self):
        s = copy.deepcopy(lawful())
        s["fixtures"]["hood"] = {"asset": "hood", "span": [40, 103],
                                 "line": "wall_mounted", "y_top": 60}
        self.assertEqual(validate_interior_staging(s), [])

    def test_wall_mounted_needs_y_top_above_work_floor(self):
        self._refused(lambda s: s["fixtures"].update(
            hood={"asset": "hood", "span": [40, 103],
                  "line": "wall_mounted", "y_top": 200}),
            "y_top above the work floor")

    def test_mounted_fixtures_exclude_their_own_slots(self):
        def mutate(s):
            s["fixtures"]["hood"] = {"asset": "hood", "span": [40, 103],
                                     "line": "wall_mounted", "y_top": 60}
            s["fixtures"]["shelf"] = {"asset": "shelf", "span": [90, 140],
                                      "line": "wall_mounted", "y_top": 70}
        self._refused(mutate, "overlaps another mounted fixture")

    def test_entry_corridor_is_figure_wide(self):
        self._refused(lambda s: s["corridors"].update(entry=[440, 450]),
                      "entry corridor")

    def test_queue_marches_south(self):
        self._refused(lambda s: s["corridors"].update(
            queue_slots=[[300, 268], [304, 260]]), "south of the previous")

    def test_queue_slots_keep_spacing(self):
        self._refused(lambda s: s["corridors"].update(
            queue_slots=[[300, 268], [304, 280]]), "closer than")

    def test_furniture_never_blocks_entry(self):
        self._refused(lambda s: s["furniture"].update(
            booth={"unit": "booth_bay", "span": [430, 500], "base_y": 320}),
            "blocks the entry corridor")

    def test_furniture_never_swallows_queue(self):
        self._refused(lambda s: s["furniture"].update(
            booth={"unit": "booth_bay", "span": [280, 340], "base_y": 300}),
            "swallows queue slot")

    def test_decals_live_on_the_work_floor(self):
        self._refused(lambda s: s["decals"].append(
            {"type": "flour", "asset": "decal_flour_b", "x": 300, "y": 300}),
            "work floor only")

    def test_service_state_required(self):
        self._refused(lambda s: s["states"].pop("service"),
                      "must include 'service'")

    def test_oven_state_is_lit_or_cold(self):
        self._refused(lambda s: s["states"]["night"].update(
            oven_state="warm"), "lit or cold")


if __name__ == "__main__":
    unittest.main()


class InteriorScaleLaw(unittest.TestCase):
    """Pins for the scale law (session H reckoning): the recorded
    pre-batch heights REFUSE, the scaled set's heights pass."""

    def test_scaled_set_is_lawful(self):
        from tools.art_pipeline.interior_scene import fixture_scale_verdict
        for h, kind in [(37, "deep_top"), (44, "upright"), (40, "upright"),
                        (34, "upright"), (39, "upright"), (22, "upright"),
                        (31, "deep_top"), (20, "upright"), (28, "upright"),
                        (40, "deep_top")]:  # makeline, measured lawful
            self.assertEqual(fixture_scale_verdict(h, kind), "OK", (h, kind))

    def test_the_oversized_class_refuses(self):
        from tools.art_pipeline.interior_scene import fixture_scale_verdict
        for h, kind in [(56, "deep_top"), (100, "upright"), (61, "upright"),
                        (60, "upright"), (56, "upright"),
                        (26, "hand_prop"), (24, "hand_prop")]:
            self.assertEqual(fixture_scale_verdict(h, kind), "OVERSIZED",
                             (h, kind))

    def test_person_canon_is_thirty(self):
        from tools.art_pipeline.interior_scene import PERSON_CONTENT_H
        self.assertEqual(PERSON_CONTENT_H, 30)
