# Experiment 08 — Characters: Research, Rulings, and the Phased Path (2026-08-10)

Status: **paper only — no generation. Research complete; path proposed;
AWAITING USER RULING before phase 1.**

## Research capsule (documentation researcher, same day; citations in
## the session record — api.pixellab.ai/mcp/docs, /v1/openapi.json,
## pixellab.ai/docs/tools/*, /pixellab-api)

Character-relevant surface, documented:

- **`create_character`** (MCP): text → 4/8-direction sprite set;
  modes standard (1 gen!) / v3 (2–9) / pro (20–40); takes an optional
  south-facing `reference_image` (max 256²) and `style_character_id`;
  MCP text says size 32–256. **Contradiction #2 (unresolved):** the
  v2 marketing page lists create-character-with-4/8-directions at
  48×48/64×64 ONLY. Whether size=32 is accepted is a 1-gen measurement.
- **`animate_character`** (MCP): template mode 1 gen/direction
  (walk/idle/attack templates; only 4 template names appear in web
  docs: Walk, Thrust, Running, Cast spell); v3 ~1–8; pro 20–40/dir;
  4–16 frames (even); `keep_first_frame` default true — frame[0] can
  remain our canonical standing pose.
- **Skeleton path**: estimate-skeleton auto-rigs (keypoints are NOT
  hand-supplied unless we want to adjust); template skeleton library
  exists; REST v1 animate-with-skeleton takes exactly 3 keypoint
  frames → returns 4 frames. Canvases SQUARE-ONLY everywhere:
  16/32/64/128/256.
- **Canvas blessing confirmed**: every character/animation tool is
  hard-gated to square 16/32/64/128/256. The ONLY non-square output
  in the entire documentation is `create-instant-character` at 32×40 —
  experimental AND Tier 2 (we are Tier 1). 32×64 walk frames remain
  unblessed vendor-wide; R5 stands confirmed.
- **`create_portrait_character`** (MCP): BIDIRECTIONAL sprite↔portrait
  conversion from a supplied image — the documented identity bridge.
  Result sizes are an enum 16/32/48/64/128/160; 20 gens (25 at the 2K
  sizes). No portrait-expression tool exists; the mood enum
  (neutral/happy/angry/sad/surprised) lives only on the viseme path.
- **Talking portraits**: create_vocal_animation (viseme sets) +
  `get_lip_sync` (FREE lookup: spritesheet + frame timings) — the
  in-engine mechanism for dialogue mouth animation in Godot. Later.
- **Cutscenes: no surface exists.** No tool composites an existing
  character into a scene (only reference/style-image passing); no
  cutscene/illustration workflow documented anywhere; max canvases
  pixflux 400 / pixen 512 / pro 512; create-map (scene tool) is
  400px at Tier 2+ only. Pro's perspective/mood drift is already
  measured off-theme for us (Exp 05).
- **`/rotate`** (REST v1): 16/32/64/128 square, all-8-directions from
  one south sprite; docs say characters are its PRIMARY trained case
  (**contradiction #6** vs our earlier note that character rotation
  is less reliable — plausibly two different code paths; measurable).
- Six size/capability contradictions across MCP text, OpenAPI spec,
  web docs, and the v2 marketing page are recorded in the session
  research report; the two that matter to us (#2 sizes, #6 rotation
  reliability) are resolved EMPIRICALLY by cheap probes below, never
  by trusting one page over another.

## Rulings proposed (await the user's word)

1. **Sprite canvas: 32×32.** One tile, grid-aligned, Omega scale at
   2×, blessed by every animation tool, and the small-canvas frame
   bonus applies (32px → 16-frame ceiling in the pro table). 32×64 is
   unblessed vendor-wide (confirmed); 32×40 is experimental Tier-2;
   48×48 breaks grid alignment. R5 is closed by this ruling.
2. **Portrait canvas: 64×64**, generated FROM the approved sprite via
   the character_to_portrait bridge (identity by ancestry, not by
   hope). Displayed 2× = 128px in the 640×360 viewport. Portraits get
   their OWN validator contract (P15 anticipated this): bust may touch
   the bottom edge, bbox LARGE, transparent background, hard alpha,
   palette incl. skin ramp. 128/160 rejected (cost tier + micro-detail
   risk contra the governing rule).
3. **Skin ramp: reuse the legal dough-tan ramp** — #D4A068 base,
   #C68239 mid, #B1552E shadow — no new palette authority created. A
   dedicated skin ramp is a color_language revision the board can
   order later; flag stays open.
4. **Character validator variant**: prop rules except bbox — a 32px
   person is tall-narrow, so bbox_h ≥ 18 and bbox_w ≥ 8 replace the
   square min_bbox 14. (The invented-threshold lesson from Exp 06
   applies: these numbers get checked against the first board-passed
   sprite and adjusted to measurement, not doctrine.)
5. **Cutscenes are in-engine compositions.** Approved world assets +
   sprites + portraits + deterministic text over 640×360, with
   pixflux ≤400px backdrops through the standard recipe only when a
   scene needs a set we don't own. Vendor illustration is DEFERRED
   behind a named trigger: the first scene the in-engine composer
   genuinely cannot stage. (Grounds: no vendor cutscene surface, no
   character-into-scene mechanism, Pro measured off-theme.)
6. **Local PNG stays canon**; character_id / animation outputs are
   derived caches (the registry ruling's anticipated employee case).
   If create_character enters production use it becomes a permanent
   drift-probe row per P15 (standard mode: 1 gen/run).

## The phased path (each phase gates at the board)

- **Phase 1 (~3 gens): canonical south-facing employee** via the
  proven recipe — hand-blocked 32×32 anchor (≥2px margin), pixflux
  init@120, forced palette strip (chips ∪ dough-tan ramp), 3-seed
  pool, board picks identity. Theme authority stays local. Theme
  role: the employee is the first face of thirty years of oven warmth.
- **Phase 2 (1–2 gens): direction set** — create_character standard,
  reference = the approved sprite, n_directions=4, size=32. Measures
  contradiction #2 for free. Kill criterion: two failed identity/theme
  boards close the registry path. Fallbacks pre-named: (a) REST
  /rotate at blessed 32 (also measures contradiction #6), (b)
  per-direction hand-blocked anchors through the house recipe.
- **Phase 3 (~4 gens): walk cycle** — animate_character template
  walk, 4 directions, low frame count (4–6), keep_first_frame so
  frame[0] stays the canonical pose. Every frame saved immediately
  (vendor flakiness lesson), validated under the character contract,
  frames become canon PNGs.
- **Phase 4 (20 gens, optional, explicit user call): portrait** via
  character_to_portrait at 64. New portrait validator contract lands
  WITH this phase, not after it.
- Later, behind named triggers: idle/action templates, states
  (create_character_state), visemes + get_lip_sync talking portraits,
  8-direction upgrade.

Budget to a walking employee: ~8–9 generations; +20 with the
portrait. Every phase names its question; unspent allowance remains
the healthy state.
