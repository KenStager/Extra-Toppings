# Experiment 05 — The Pizza Oven and the Variant Mechanism (2026-08-10)

Status: **Cycle B complete; oven + states AWAITING USER APPROVAL.**

## The asset (user reflection honored)

The previously curated "oven" was honestly a residential range (its
donor is the apartment stove). DiNapoli's hero appliance is a
**commercial double-deck pizza oven at 64×64** (2×2 tiles — 64×32
read counter-height and squat in dollhouse perspective; the wall
appliance needs a vertical face plus top). No donor exists in Omega —
this is the first fully original hero asset: hand-blocked anchor,
pixflux pool (seeds 2001–2003), winner s2002 (steel body, oxblood
mouths, restrained gold trim; s2003 rejected as noisier under the
theme guard; s2001 failed single_silhouette). Quantize: 0 pixels.
The old range asset is relabeled kitchen_range and stays useful.

## The variant mechanism, settled

Full MCP object lifecycle exercised: curated oven as style image →
`create_1_direction_object` (16-candidate review pack; frame [0] a
near-match to ours) → `select_object_frames` → completed object id →
`create_object_state` "lit". Measured localization: 100% of mouth
pixels changed, but 64% outside too — **create_object_state is NOT
pixel-preserving**, matching every other edit surface at this vendor.
The difference: its outside changes are COHERENT relighting (warm
cast, heat shimmer), and the lit oven visually reads as the same
oven, lit — the game's core warmth image. RULING: variant states go
through create_object_state, judged at the review board by visual
coherence (same object, changed condition), never by pixel
preservation. Registry ids are derived caches; the local PNG remains
canon. Theme note for approval: the lit mouths read slightly
open-flame where a deck oven glows; one state re-roll available.

## Pro style_copy leak test (distant pair: pizza → oven)

`create_image_pro`, canon pizza as style image, style_copy
[color_palette, outline] only, seed 4001, 16 candidates generated,
4 returned. **No identity leak** — the bitforge pathology (object
BECOMES the style subject) did not occur; 2/4 clean ovens, 2/4 with
semantically coherent pizza-context additions (pizza in mouth, peel).
However Pro's output drifts in perspective (true angled 3/4 depth vs
our flat dollhouse frontal) and mood (cool modern steel vs oven
warmth). RULING: Pro is a specialist for ideation and leak-safe
style transfer across distant objects, but its output requires
theme-conforming rework before production; the pixflux + hand-blocked
anchor recipe remains the default. The theme guard outranks the leak
metric.

Spend: ~3 pixflux + ~20 (registry pack) + state + 20 (Pro) ≈ 45–50
credits this cycle, all ledgered; every batch carries its question and
theme role in provenance.

## Resolution (2026-08-10): oven APPROVED — cold + lit (flames)

User approved the oven pair: `oven_deck_64_cold` and `oven_deck_64_lit`
(the original create_object_state flames) into approved/. The
deterministic "warm glow" midpoint was REJECTED with a recorded
lesson: it mapped every flame-core pixel to one orange, collapsing the
fire's internal ramp — flat and lifeless. Deterministic tone edits
must SHIFT colors along a ramp (each tier one step down), never
collapse tiers to a single value. The ember variant (which kept
ramp structure) remains on file unapproved. Vendor state re-rolls
remain flaky on repeated states; the approved lit came from the first,
successful call. Floors: sky/cream checker approved
(`floor_checker_sky_cream_32`, contrast 92.8 — the boldest blue inside
the envelope).
