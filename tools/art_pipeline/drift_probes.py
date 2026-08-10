"""The four session-start drift probes, as committed pipeline code.

Protocol (decision_32px_world.md): the harness runs FIRST in any
session that will spend generations; Tier C freezes generation. The
probe parameters were previously session-script archaeology — every
resume reconstructed them from calibration provenance. This module is
now the single authority for what the probes ARE; drift.py remains the
authority for how verdicts are judged.

All four probes force the Experiment-01 working palette strip
(`experiment_01/palettes/working_palette_pizza.png`) as `color_image`
— identified empirically: every calibration baseline's colors are a
subset of that strip. Input images live under the private root and are
attached at call time; provenance records never carry image payloads.
"""

from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from PIL import Image

from tools.art_pipeline.drift import ProbeVerdict, append_log, judge_probe
from tools.art_pipeline.palettes import from_hex
from tools.art_pipeline.pixellab_client import (
    generate_bitforge,
    generate_pixflux,
    image_to_b64,
)
from tools.art_pipeline.provenance import attach_hashes, write_record

NEGATIVE_PROP = (
    "second object, extra slice, duplicate, multiple items, cropped, cut off, "
    "floating fragment, disconnected piece, background, table, text, shadow, "
    "antialiasing, blur"
)
COMMON = {
    "detail": "low detail",
    "image_size": {"height": 32, "width": 32},
    "isometric": False,
    "no_background": True,
    "outline": "single color outline",
    "shading": "flat shading",
    "view": "low top-down",
}
PALETTE_STRIP = "experiment_01/palettes/working_palette_pizza.png"
PALETTE_JSON = "experiment_01/palettes/working_palette_pizza.json"

# Image-valued param name -> private-root-relative source path. Attached
# at call time, stripped before provenance (images never enter records).
IMAGE_PARAM_KEYS = ("init_image", "style_image", "color_image")


@dataclass(frozen=True)
class ProbeSpec:
    name: str
    engine: str  # "pixflux" | "bitforge"
    params: dict[str, Any]
    image_params: dict[str, str] = field(default_factory=dict)


PROBES: tuple[ProbeSpec, ...] = (
    ProbeSpec(
        name="probe_canon_pizza",
        engine="pixflux",
        params={
            **COMMON,
            "description": (
                "a single whole pepperoni pizza in a round steel pizza pan, one "
                "object, centered, pixel art map prop, seen slightly from above"
            ),
            "negative_description": NEGATIVE_PROP,
            "seed": 204,
            "text_guidance_scale": 8.0,
        },
        image_params={"color_image": PALETTE_STRIP},
    ),
    ProbeSpec(
        name="probe_box_open",
        engine="pixflux",
        params={
            **COMMON,
            "description": (
                "open cardboard pizza box with a whole pepperoni pizza inside, "
                "lid folded open, single object, centered, pixel art map prop, "
                "seen slightly from above"
            ),
            "negative_description": NEGATIVE_PROP,
            "seed": 602,
            "text_guidance_scale": 8.5,
            "init_image_strength": 150,
        },
        image_params={
            "init_image": "experiment_03/anchors/box_open_anchor.png",
            "color_image": PALETTE_STRIP,
        },
    ),
    ProbeSpec(
        name="probe_slice_bitforge",
        engine="bitforge",
        params={
            **COMMON,
            "description": (
                "single slice of pepperoni pizza, triangular wedge with browned "
                "crust edge and melted cheese, single object, centered, pixel "
                "art map prop, seen slightly from above"
            ),
            "negative_description": NEGATIVE_PROP,
            "seed": 601,
            "text_guidance_scale": 8.5,
            "init_image_strength": 150,
            "style_strength": 55,
        },
        image_params={
            "init_image": "experiment_03/anchors/pizza_slice_anchor.png",
            "style_image": "experiment_01/approved/pizza_whole_32_canon.png",
            "color_image": PALETTE_STRIP,
        },
    ),
    ProbeSpec(
        name="probe_palette_canary",
        engine="pixflux",
        params={
            **COMMON,
            "description": (
                "a pile of colorful toys, rainbow colors, many bright colors"
            ),
            "negative_description": "antialiasing, blur",
            "seed": 904,
            "text_guidance_scale": 8.0,
        },
        image_params={"color_image": PALETTE_STRIP},
    ),
)

ENGINES: dict[str, Callable[[dict[str, Any]], tuple[Image.Image, dict[str, Any]]]] = {
    "pixflux": generate_pixflux,
    "bitforge": generate_bitforge,
}
TIER_ORDER = {"A": 0, "B": 1, "C": 2}


def build_call_params(spec: ProbeSpec, private_root: str | Path) -> dict[str, Any]:
    """Replayable params plus base64 image inputs resolved from the private root."""
    params = dict(spec.params)
    for key, rel_path in spec.image_params.items():
        with Image.open(Path(private_root) / rel_path) as im:
            params[key] = image_to_b64(im.convert("RGBA"))
    return params


def provenance_params(params: dict[str, Any]) -> dict[str, Any]:
    """The record-safe view: every image payload stripped."""
    return {k: v for k, v in params.items() if k not in IMAGE_PARAM_KEYS}


def run_session_probes(
    private_root: str | Path,
    session_label: str,
    out_dirname: str,
) -> dict[str, ProbeVerdict]:
    """Run all probes, write provenance, judge against baseline, log verdicts."""
    private_root = Path(private_root)
    drift_dir = private_root / "drift"
    out_dir = drift_dir / out_dirname
    out_dir.mkdir(exist_ok=True)

    band = json.loads((drift_dir / "band.json").read_text())["band"]
    palette_hex = json.loads((private_root / PALETTE_JSON).read_text())
    palette = [from_hex(v) for v in palette_hex.values()]

    verdicts: dict[str, ProbeVerdict] = {}
    for spec in PROBES:
        image, meta = ENGINES[spec.engine](build_call_params(spec, private_root))
        out_path = out_dir / f"{spec.name}.png"
        image.save(out_path)
        record = {
            "asset": spec.name,
            "engine": f"{spec.engine} (REST v1)",
            "params": provenance_params(spec.params),
            "question_answered": (
                "drift harness: session-start probe before new spend"
            ),
            "theme_role": "instrument — drift probe, not a production asset",
            "seed": spec.params["seed"],
            "timestamp_utc": datetime.datetime.now(
                datetime.timezone.utc
            ).isoformat(timespec="seconds"),
            "usage": meta.get("usage"),
            "validator_version": 2,
            "donor_derived": False,
        }
        record = attach_hashes(record, {"output": out_path})
        write_record(record, out_dir / f"{spec.name}_provenance.json")
        verdicts[spec.name] = judge_probe(
            drift_dir / "baseline" / f"{spec.name}.png",
            out_path,
            palette,
            max_diff_frac=band["max_diff_frac"],
            max_hist_l1=band["max_hist_l1"],
        )

    append_log(
        drift_dir / "drift_log.jsonl",
        {
            "session": session_label,
            "run_dir": str(out_dir),
            "band_used": band,
            "verdicts": {
                name: {
                    "tier": v.tier,
                    "sha_equal": v.sha_equal,
                    "diff_frac": v.diff_frac,
                    "hist_l1": v.hist_l1,
                    "validator_passed": v.validator_passed,
                    "notes": v.notes,
                }
                for name, v in verdicts.items()
            },
        },
    )
    return verdicts


def worst_tier(verdicts: dict[str, ProbeVerdict]) -> str:
    return max((v.tier for v in verdicts.values()), key=TIER_ORDER.__getitem__)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", default=".private_art")
    parser.add_argument("--session", required=True, help="session label for the log")
    parser.add_argument("--out", required=True, help="run dirname under drift/")
    args = parser.parse_args(argv)
    verdicts = run_session_probes(args.private_root, args.session, args.out)
    for name, v in verdicts.items():
        print(
            f"{name}: Tier {v.tier}  diff={v.diff_frac:.4f}  "
            f"histL1={v.hist_l1:.4f}  "
            f"validator={'pass' if v.validator_passed else 'FAIL'}  {v.notes}"
        )
    tier = worst_tier(verdicts)
    frozen = tier == "C"
    print(
        f"OVERALL: Tier {tier} — "
        + ("FREEZE generation and investigate" if frozen else "clear to generate")
    )
    return 1 if frozen else 0


if __name__ == "__main__":
    raise SystemExit(main())
