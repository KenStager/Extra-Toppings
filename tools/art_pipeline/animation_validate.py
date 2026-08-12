"""Animation-frame validators — the Phase A probe's measured
contracts as law code (E16 animation slate, 2026-08-12).

The probe's central finding, now the exactness definition: vendor
animation returns endpoint frames COMPOSITE-exact, not file-exact —
the alpha mask and every visible pixel's RGB are preserved, while
RGB under fully-transparent pixels is re-encoded. A naive full-array
diff therefore reads ~66% changed on a byte-identical composite;
`composite_exact` is the instrument that cleared it. Validators
refuse (return the defect), never repair.
"""
from __future__ import annotations

from PIL import Image

RGB = tuple[int, int, int]


def composite_exact(a: Image.Image, b: Image.Image) -> bool:
    """True when the two frames composite identically: same size,
    equal alpha masks, and equal RGB on every pixel visible in
    either. RGB under mutual full transparency is ignored — that is
    the vendor's re-encoding territory, invisible once composited.
    """
    if a.size != b.size:
        return False
    pa = a.convert("RGBA").load()
    pb = b.convert("RGBA").load()
    for y in range(a.height):
        for x in range(a.width):
            ra, ga, ba, aa = pa[x, y]
            rb, gb, bb, ab = pb[x, y]
            if aa != ab:
                return False
            if aa == 0:
                continue
            if (ra, ga, ba) != (rb, gb, bb):
                return False
    return True


def binary_alpha(frame: Image.Image) -> bool:
    """Every alpha value is 0 or 255 (the sprite contract)."""
    return set(frame.convert("RGBA").getdata(3)) <= {0, 255}


def off_palette_count(frame: Image.Image, palette: set[RGB]) -> int:
    """Visible pixels whose RGB is outside `palette`. For
    interpolation clips pass the UNION of both endpoints' palettes —
    the probe's single-palette census false-alarmed on the seated
    end frame.
    """
    im = frame.convert("RGBA")
    return sum(
        1
        for r, g, b, a in im.getdata()
        if a > 0 and (r, g, b) not in palette
    )


def visible_palette(frame: Image.Image) -> set[RGB]:
    """The frame's own visible-pixel palette (census helper)."""
    return {
        (r, g, b) for r, g, b, a in frame.convert("RGBA").getdata() if a > 0
    }


def baseline_rows(frames: list[Image.Image]) -> list[int]:
    """Bottom-most visible row per frame; a walking figure's feet
    stay on the baseline (the probe measured row 31 across all
    frames, bob <= 1px). Empty frames refuse as -1.
    """
    rows = []
    for f in frames:
        bbox = f.convert("RGBA").getbbox()
        rows.append(bbox[3] - 1 if bbox else -1)
    return rows


def frame_delta(a: Image.Image, b: Image.Image) -> int:
    """Composite difference in visible pixels — the loop-continuity
    metric's unit (compare last->first against the inter-frame mean;
    a cycle that ends far from its start does not loop).
    """
    pa = a.convert("RGBA").load()
    pb = b.convert("RGBA").load()
    n = 0
    for y in range(a.height):
        for x in range(a.width):
            ra, ga, ba, aa = pa[x, y]
            rb, gb, bb, ab = pb[x, y]
            if aa == 0 and ab == 0:
                continue
            if aa != ab or (ra, ga, ba) != (rb, gb, bb):
                n += 1
    return n


ANIMATION_KINDS = {"walk", "seated_idle"}


def validate_animation_manifest(manifest: dict, root) -> None:
    """Refuse a malformed animation manifest — never repair.

    The durable-asset contract (2026-08-12): every clip records its
    pose, its frame files with sha256s, its playback law (frame 0 is
    the pose, the loop plays loop_start..loop_end), and its mirror
    law. Binding checks re-hash the files and re-run the frame-0
    composite-exactness instrument.
    """
    import hashlib
    from pathlib import Path

    root = Path(root)
    if manifest.get("schema_version") != 1:
        raise ValueError("unknown manifest schema_version")
    clips = manifest.get("clips")
    if not isinstance(clips, dict) or not clips:
        raise ValueError("manifest has no clips")
    for cid, clip in clips.items():
        if clip.get("kind") not in ANIMATION_KINDS:
            raise ValueError(f"{cid}: unknown kind {clip.get('kind')!r}")
        if clip.get("kind") == "walk" and not isinstance(
                clip.get("mirror_east"), bool):
            raise ValueError(f"{cid}: walk clips must state mirror_east")
        frames = clip.get("frames", [])
        if len(frames) < 2:
            raise ValueError(f"{cid}: fewer than two frames")
        pb = clip.get("playback", {})
        if not (1 <= pb.get("loop_start", 0) <= pb.get("loop_end", -1)
                < len(frames)):
            raise ValueError(f"{cid}: playback loop out of range")
        if pb.get("duration_ms", 0) <= 0:
            raise ValueError(f"{cid}: duration_ms must be positive")
        hashes = clip.get("sha256", {})
        for rel in [clip.get("pose")] + frames:
            p = root / rel
            if not p.exists():
                raise ValueError(f"{cid}: missing file {rel}")
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if hashes.get(rel) != digest:
                raise ValueError(f"{cid}: sha256 mismatch for {rel}")
        pose = Image.open(root / clip["pose"]).convert("RGBA")
        f0 = Image.open(root / frames[0]).convert("RGBA")
        if not composite_exact(pose, f0):
            raise ValueError(f"{cid}: frame 0 is not the pose (frame-0-is-ours law)")
        for rel in frames:
            if not binary_alpha(Image.open(root / rel).convert("RGBA")):
                raise ValueError(f"{cid}: non-binary alpha in {rel}")
