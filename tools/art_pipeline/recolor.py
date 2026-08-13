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


# ---------------------------------------------------------------- skin axis
# One recorded ramp shift: every tier moves down one step. A second
# shift would collapse tiers (two sources onto #680828) — refused by
# apply_mapping — so the skin axis has exactly two values per base:
# native and shifted. Deeper complexions come from deep-skinned BASES
# (the kid), not from stacking shifts.
SKIN_SHIFT: dict[RGBA, RGBA] = _m({
    "#D4A068": "#C68239",
    "#C68239": "#B1552E",
    "#B1552E": "#680828",
})
# The man's hair shares #B1552E (measured); restore his hair rows after
# a skin shift so the shift touches skin, not hair.
SKIN_SHIFT_EXCLUDE: dict[str, Box] = {"extra_man": (0, 0, 31, 6)}


def apply_skin_shift(base_image: Image.Image, base_name: str) -> Image.Image:
    """Shift the base's skin ramp one step down, preserving excluded zones."""
    out = apply_mapping(base_image, SKIN_SHIFT)
    exclude = SKIN_SHIFT_EXCLUDE.get(base_name)
    if exclude:
        x0, y0, x1, y1 = exclude
        out.paste(base_image.convert("RGBA").crop((x0, y0, x1 + 1, y1 + 1)), (x0, y0))
    return out


# ------------------------------------------------- reserved identity rule
# The named cast's identity features (experiment_10_extras.md taxonomy
# v2): extras may never wear them. Case blue joined by user ruling
# (2026-08-10): it belongs to sworn institutions only — the cop base
# wears it BY GENERATION; no recolor mapping may ever produce it, so a
# civilian can never drift blue. Enforced by test over roster data.
RESERVED_TARGETS: frozenset[RGBA] = frozenset({
    from_hex("#FF8628"),  # Lena's heat hair
    from_hex("#FFE976"),  # gold (Tony's chain, Carmine's tiepin)
    from_hex("#3854DA"),  # case blue — sworn institutions only
})


def roster_respects_reservations() -> list[str]:
    """Variant names whose mappings hit a reserved target (empty = clean)."""
    violations = []
    for name, (_base, mapping, _region) in EXTRAS_VARIANTS.items():
        if any(target in RESERVED_TARGETS for target in mapping.values()):
            violations.append(name)
    return violations


# ------------------------------------------------ composable wardrobe
# Crowd wardrobe law (experiment_10_extras.md): the warm-cold axis
# governs crowds. Civilians skew warm; slate/ink are the minority;
# case blue never appears on a civilian. Recolors are exact-color
# operations with no generation involved, so garment swaps may target
# any legal color without ghost risk.
BASE_TOP = from_hex("#4E6472")     # every base's top zone color
BASE_BOTTOM = from_hex("#303B5A")  # every base's bottom zone color
TOP_TARGETS: dict[str, RGBA] = {
    "slate": from_hex("#4E6472"), "ink": from_hex("#303B5A"),
    "gray": from_hex("#9D9C9C"), "pale": from_hex("#CBD7CC"),
    "cream": from_hex("#FBFBE8"), "burgundy": from_hex("#680828"),
    "oxblood": from_hex("#A81031"),
    # The gray-undertone tints (board ruling 2026-08-12 session H:
    # "slight variation... still the seemingly grey undertones" — the
    # UH strip read as everyone-the-same). Near-gray, saturation held
    # to channel deltas <= 22; exact-color disjoint from every register
    # tier, curb tone, well metal, slate ramp, crosswalk paint and
    # reserved identity color (verified at introduction).
    "heather": from_hex("#969AA6"),   # cool blue-gray
    "sage": from_hex("#929A8E"),      # gray-green
    "oat": from_hex("#ACA496"),       # warm oatmeal-gray
}
BOTTOM_TARGETS: dict[str, RGBA] = {
    "ink": from_hex("#303B5A"), "slate": from_hex("#4E6472"),
    "burgundy": from_hex("#680828"), "gray": from_hex("#9D9C9C"),
}
HAIR_TARGETS: dict[str, RGBA] = {
    "brown": from_hex("#680828"), "ink": from_hex("#303B5A"),
    "sandy": from_hex("#C68239"), "gray": from_hex("#9D9C9C"),
    "black": from_hex("#000000"),
}
# District wardrobe registers: which top colors a district's crowd
# draws from (data, not doctrine — scenes may override deliberately).
DISTRICT_WARDROBES: dict[str, list[str]] = {
    "old_harbor": ["cream", "burgundy", "gray", "pale", "slate"],
    "little_sicily": ["cream", "oxblood", "pale", "burgundy"],
    "university": ["slate", "gray", "ink", "pale", "heather", "sage", "oat"],
    "meadows": ["ink", "burgundy", "slate", "oxblood"],
}


def wardrobe_variant(
    base_image: Image.Image,
    base_name: str,
    top: str | None = None,
    bottom: str | None = None,
    hair: str | None = None,
    skin_shift: bool = False,
) -> Image.Image:
    """Compose a crowd figure: skin first, then hair, then garments.

    Skin-first ordering means a warm garment target can never be
    caught by the skin shift. Hair swaps use the measured per-base
    scoping; the reserved-identity rule applies to every axis.
    """
    for axis, choice in (("top", top), ("bottom", bottom), ("hair", hair)):
        targets = {"top": TOP_TARGETS, "bottom": BOTTOM_TARGETS, "hair": HAIR_TARGETS}[axis]
        if choice is not None and targets[choice] in RESERVED_TARGETS:
            raise ValueError(f"{axis}={choice} is a reserved cast identity color")
    out = base_image.convert("RGBA")
    if skin_shift:
        out = apply_skin_shift(out, base_name)
    if hair is not None:
        hair_src = from_hex("#9D9C9C") if base_name == "extra_elder" else from_hex("#680828")
        region = MAN_HAIR_REGION if base_name == "extra_man" else HEAD_REGION
        if HAIR_TARGETS[hair] != hair_src:
            mapping = {hair_src: HAIR_TARGETS[hair]}
            if base_name == "extra_man":
                mapping[from_hex("#B1552E")] = HAIR_TARGETS[hair]  # collapse OK? no —
                # the man's 2-tier hair maps dark tier to the target and
                # highlight tier one step lighter when one exists.
                lighter = {"ink": "slate", "brown": "sandy", "black": "ink",
                           "sandy": "gray", "gray": "pale"}
                mapping[from_hex("#B1552E")] = (
                    TOP_TARGETS.get(lighter[hair]) or HAIR_TARGETS.get(lighter[hair])
                    or from_hex("#9D9C9C")
                )
            out = apply_mapping(out, mapping, region=region)
    if top is not None and TOP_TARGETS[top] != BASE_TOP:
        out = apply_mapping(out, {BASE_TOP: TOP_TARGETS[top]})
    if bottom is not None and BOTTOM_TARGETS[bottom] != BASE_BOTTOM:
        out = apply_mapping(out, {BASE_BOTTOM: BOTTOM_TARGETS[bottom]})
    return out
