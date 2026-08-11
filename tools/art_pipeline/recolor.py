"""Recorded recolors: extras variants as data, never as new generations.

Experiment 10 (art_specs/experiment_10_extras.md): extras are
dedicated anonymous bases plus recorded color mappings. A recolor is
an unconditional, pixel-local construction step — same legal family
as the floor recolors and the brand layer. Ramps shift, never
collapse (the recorded oven lesson): a mapping that sends two source
colors to one target is refused.

Zone-unique bases make global swaps safe; `check_zone_unique`
verifies the assumption instead of trusting it, and region-scoped
application exists for the exceptions.
"""

from __future__ import annotations

from PIL import Image

from tools.art_pipeline.palettes import RGBA, from_hex

Box = tuple[int, int, int, int]  # x0, y0, x1, y1 inclusive


def apply_mapping(
    image: Image.Image,
    mapping: dict[RGBA, RGBA],
    region: Box | None = None,
) -> Image.Image:
    """Exact-color swap; scoped to `region` when given.

    Refuses a tier-collapsing mapping (two sources onto one target).
    """
    targets = list(mapping.values())
    if len(set(targets)) != len(targets):
        raise ValueError("mapping collapses ramp tiers onto one color")
    out = image.convert("RGBA").copy()
    x0, y0, x1, y1 = region if region else (0, 0, out.width - 1, out.height - 1)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            p = out.getpixel((x, y))
            if p in mapping:
                out.putpixel((x, y), mapping[p])
    return out


def check_zone_unique(image: Image.Image, color: RGBA, box: Box) -> bool:
    """True when `color` appears ONLY inside `box` (its zone)."""
    rgba = image.convert("RGBA")
    x0, y0, x1, y1 = box
    for y in range(rgba.height):
        for x in range(rgba.width):
            if rgba.getpixel((x, y)) == color and not (
                x0 <= x <= x1 and y0 <= y <= y1
            ):
                return False
    return True


def _m(pairs: dict[str, str]) -> dict[RGBA, RGBA]:
    return {from_hex(a): from_hex(b) for a, b in pairs.items()}


# The extras roster: variant name -> (base, recorded mapping, region|None).
# Hair zone color is #680828 on man/woman/kid bases, #9D9C9C on the elder;
# the top zone is #4E6472 on every base. The kid base is NOT globally
# zone-unique (his #680828 doubles as shading below the head — measured,
# recorded in the E10 spec), so his hair swaps are region-scoped to the
# head rows; everyone else's mappings are global.
HEAD_REGION: Box = (0, 0, 31, 16)
MAN_HAIR_REGION: Box = (0, 0, 31, 6)  # face starts row 7; his hair is 2-tier
EXTRAS_VARIANTS: dict[str, tuple[str, dict[RGBA, RGBA], Box | None]] = {
    # Hair swaps are region-scoped everywhere it's measured necessary; the
    # man's hair is a 2-tier ramp (#680828 + #B1552E highlight), so his
    # swaps shift both tiers — ramps shift, never collapse.
    "man_ink_hair": ("extra_man", _m({"#680828": "#303B5A", "#B1552E": "#4E6472"}), MAN_HAIR_REGION),
    "man_sandy_hair": ("extra_man", _m({"#680828": "#C68239", "#B1552E": "#D4A068"}), MAN_HAIR_REGION),
    "man_ink_top": ("extra_man", _m({"#4E6472": "#303B5A"}), None),
    "elder_ink_hair": ("extra_elder", _m({"#9D9C9C": "#303B5A"}), None),
    "elder_burgundy_top": ("extra_elder", _m({"#4E6472": "#680828"}), None),
    "elder_ink_top": ("extra_elder", _m({"#4E6472": "#303B5A"}), None),
    "woman_ink_hair": ("extra_woman", _m({"#680828": "#303B5A"}), HEAD_REGION),
    "woman_sandy_hair": ("extra_woman", _m({"#680828": "#C68239"}), HEAD_REGION),
    "woman_ink_top": ("extra_woman", _m({"#4E6472": "#303B5A"}), None),
    "kid_ink_hair": ("extra_kid", _m({"#680828": "#303B5A"}), HEAD_REGION),
    "kid_sandy_hair": ("extra_kid", _m({"#680828": "#C68239"}), HEAD_REGION),
    "kid_ink_top": ("extra_kid", _m({"#4E6472": "#303B5A"}), None),
}


def build_variant(base_image: Image.Image, variant: str) -> Image.Image:
    """Build a roster variant from its base image."""
    _, mapping, region = EXTRAS_VARIANTS[variant]
    return apply_mapping(base_image, mapping, region=region)
