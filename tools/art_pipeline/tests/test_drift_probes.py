"""The probe specs are the committed authority — pin what they say."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.art_pipeline.drift import ProbeVerdict
from tools.art_pipeline.drift_probes import (
    IMAGE_PARAM_KEYS,
    PALETTE_STRIP,
    PROBES,
    build_call_params,
    provenance_params,
    worst_tier,
)


class ProbeSpecContract(unittest.TestCase):
    def test_four_probes_with_calibration_identities(self):
        by_name = {p.name: p for p in PROBES}
        self.assertEqual(len(PROBES), 4)
        self.assertEqual(by_name["probe_canon_pizza"].params["seed"], 204)
        self.assertEqual(by_name["probe_box_open"].params["seed"], 602)
        self.assertEqual(by_name["probe_slice_bitforge"].params["seed"], 601)
        self.assertEqual(by_name["probe_palette_canary"].params["seed"], 904)
        self.assertEqual(by_name["probe_slice_bitforge"].engine, "bitforge")
        for name in ("probe_canon_pizza", "probe_box_open", "probe_palette_canary"):
            self.assertEqual(by_name[name].engine, "pixflux")

    def test_every_probe_forces_the_working_palette_strip(self):
        for spec in PROBES:
            self.assertEqual(spec.image_params.get("color_image"), PALETTE_STRIP)

    def test_init_and_style_probes_carry_their_strengths(self):
        by_name = {p.name: p for p in PROBES}
        box = by_name["probe_box_open"]
        self.assertEqual(box.params["init_image_strength"], 150)
        self.assertIn("init_image", box.image_params)
        slice_ = by_name["probe_slice_bitforge"]
        self.assertEqual(slice_.params["init_image_strength"], 150)
        self.assertEqual(slice_.params["style_strength"], 55)
        self.assertIn("style_image", slice_.image_params)

    def test_image_payloads_never_reach_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for spec in PROBES:
                for rel in spec.image_params.values():
                    target = root / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if not target.exists():
                        Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(target)
            for spec in PROBES:
                params = build_call_params(spec, root)
                for key in spec.image_params:
                    self.assertEqual(params[key]["type"], "base64")
                recorded = provenance_params(params)
                for key in IMAGE_PARAM_KEYS:
                    self.assertNotIn(key, recorded)
                self.assertEqual(recorded["seed"], spec.params["seed"])

    def test_worst_tier_orders_c_over_b_over_a(self):
        def verdict(tier):
            return ProbeVerdict(tier, tier == "A", 0.0, 0.0, True)

        self.assertEqual(worst_tier({"a": verdict("A"), "b": verdict("B")}), "B")
        self.assertEqual(
            worst_tier({"a": verdict("A"), "b": verdict("B"), "c": verdict("C")}), "C"
        )
        self.assertEqual(worst_tier({"a": verdict("A")}), "A")


if __name__ == "__main__":
    unittest.main()
