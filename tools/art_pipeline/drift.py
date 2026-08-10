"""Model-drift detection: fixed probes, three-tier verdict.

PixelLab has no model versioning and no changelog; the only defense is
a local baseline. Four probes re-run with exact historical params at
the START of any session that will spend generations. Verdicts:
Tier A (sha256 equal) = pinned; Tier B (within the calibrated
variance band and validator-clean) = note it; Tier C = FREEZE
generation and investigate. Thresholds come from same-day calibration
runs, never from invention (band values are stored EXACT — a rounded
copy of a calibration maximum re-fails the very art that defined it).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from tools.art_pipeline.palettes import RGBA
from tools.art_pipeline.provenance import file_sha256
from tools.art_pipeline.validation import validate_candidate


def diff_fraction(a: Image.Image, b: Image.Image) -> float:
    """Fraction of pixel positions whose RGBA differs (1.0 on size mismatch)."""
    if a.size != b.size:
        return 1.0
    ia, ib = a.convert("RGBA"), b.convert("RGBA")
    diff = sum(
        1
        for y in range(ia.height)
        for x in range(ia.width)
        if ia.getpixel((x, y)) != ib.getpixel((x, y))
    )
    return diff / (ia.width * ia.height)


def histogram_l1(a: Image.Image, b: Image.Image) -> float:
    """L1 distance between normalized color histograms, in [0, 1]."""
    def hist(im: Image.Image) -> dict[tuple[int, int, int, int], float]:
        rgba = im.convert("RGBA")
        colors = rgba.getcolors(rgba.width * rgba.height)
        total = rgba.width * rgba.height
        return {color: count / total for count, color in (colors or [])}

    ha, hb = hist(a), hist(b)
    keys = set(ha) | set(hb)
    return sum(abs(ha.get(k, 0.0) - hb.get(k, 0.0)) for k in keys) / 2


@dataclass
class ProbeVerdict:
    tier: str  # "A" | "B" | "C"
    sha_equal: bool
    diff_frac: float
    hist_l1: float
    validator_passed: bool
    notes: str = ""


def judge_probe(
    baseline_path: str | Path,
    current_path: str | Path,
    palette: list[RGBA],
    max_diff_frac: float,
    max_hist_l1: float,
    expected_size: tuple[int, int] = (32, 32),
    min_bbox: int = 14,
    max_edge_run: int = 8,
) -> ProbeVerdict:
    if file_sha256(baseline_path) == file_sha256(current_path):
        return ProbeVerdict("A", True, 0.0, 0.0, True, "byte-identical")
    with Image.open(baseline_path) as base_im, Image.open(current_path) as cur_im:
        base, cur = base_im.convert("RGBA"), cur_im.convert("RGBA")
        frac = diff_fraction(base, cur)
        l1 = histogram_l1(base, cur)
        result = validate_candidate(
            cur, palette, expected_size=expected_size,
            min_bbox=min_bbox, max_edge_run=max_edge_run,
        )
    if frac <= max_diff_frac and l1 <= max_hist_l1 and result.passed:
        return ProbeVerdict("B", False, frac, l1, True, "within calibrated variance")
    notes = "; ".join(result.notes) or (
        f"beyond band: diff {frac:.3f}>{max_diff_frac:.3f} or l1 {l1:.3f}>{max_hist_l1:.3f}"
    )
    return ProbeVerdict("C", False, frac, l1, result.passed, notes)


def calibrate_band(run_dirs: list[str | Path], probe_names: list[str]) -> dict[str, float]:
    """Max pairwise same-day variance across calibration runs — the exact
    observed ceiling, stored raw."""
    max_frac = 0.0
    max_l1 = 0.0
    for name in probe_names:
        images = [Image.open(Path(d) / f"{name}.png").convert("RGBA") for d in run_dirs]
        for i in range(len(images)):
            for j in range(i + 1, len(images)):
                max_frac = max(max_frac, diff_fraction(images[i], images[j]))
                max_l1 = max(max_l1, histogram_l1(images[i], images[j]))
        for im in images:
            im.close()
    return {"max_diff_frac": max_frac, "max_hist_l1": max_l1}


def append_log(log_path: str | Path, entry: dict) -> None:
    with open(log_path, "a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
