# Experiment 11 — Portraits: The Close-Up Register (2026-08-10)

Status: **round 1 measured (Carmine, Sal); Carmine FAILED identity;
validator contract DRAFTED from measurements, not ratified. AWAITING
the board.**

## Purpose and method (user-approved direction)

Bust portraits for dialogue surfaces — a NEW asset class. Identity by
ancestry: the input image IS the approved 32px sprite, so every
portrait's provenance chains to a board-approved identity.

Path: MCP `create_portrait_character` (pro), direction
`character_to_portrait`, view `low top-down`, `result_size` 64, fixed
seed, one call per character. 64 was interrogated and held before
spending: 2× world density (the classic dialogue-bust ratio), 18% of
the 640×360 screen, and no Retina argument exists — the canvas
integer-scales as a unit, and showing a 128 source at 64 logical would
be resampling, which the pipeline forbids. 128/160 would be a separate
full-screen asset class needing its own brief.

**Cost law, measured:** the vendor charged **25 generations per call**,
not the 20 the tool schema's table claims for result_size 64. Balance
deltas confirm exactly 25×2 for round 1. The schema is wrong; the
measured number is recorded in provenance and rules planning.

**No prompt surface exists.** The tool accepts image / direction /
view / result_size / seed ONLY — no prompt, no negatives, no palette
forcing. Every counter-tool the character recipe relies on (heritage
words, anime negatives, palette strips) is unavailable here. The only
levers are the input image and the seed. This is a structural
difference from every prior generation surface and shapes the failure
mode below.

## Round 1 results (2 calls, 50 generations, seeds 11001/11011)

**Sal s11011 — STRONG.** The padrone survived the close-up: receding
silver hair, lined warm face, cream shirt under the dark waistcoat,
oxblood pin at the collar. Warm register held. One drift, flagged not
hidden: the sprite's silver **mustache** became a full white **beard**
— the known facial-hair drift mode, here with no negative-prompt
surface to counter it. Whether the beard is accepted (it reads
handsome, elder-host) or re-rolled is the board's call.

**Carmine s11001 — REJECT (session judgment; the board rules).**
Identity did not survive:

1. Reads young and androgynous — the gaunt elder lender is gone.
2. **Two gold hoop earrings** appeared — Lena's identity tell, and a
   reserved-identity violation in spirit (gold belongs to Carmine only
   as the 1px tiepin). The strip-spending law has a portrait analog:
   the model spent the sprite's tiny gold mass as jewelry.
3. An invented **light-blue eye-band/visor** (#86BECD) plus a vertical
   blue streak down the face — a blue register on a civilian face
   (not case blue #3854DA, but adjacent in feel; nothing in the
   sprite licenses it).
4. The carbon-ink coat rendered as purple-navy (#4A426F/#2A2342) with
   a gold button.

Cause analysis: with no prompt/negative surface, the pro model reads
the 32px sprite alone; Carmine's sprite is the most abstract figure in
the cast (thin ink column, minimal face pixels), so the model's priors
filled the vacuum. Sal's sprite carries more facial information
(silver hair mass, mustache pixels, waistcoat blocking) and survived.
Prediction recorded before spending again: **portrait fidelity scales
with how much identity information the 32px face actually carries.**

## Palette finding (both outputs)

Both portraits are 64×64, hard alpha {0,255}, and **exactly 32 opaque
colors** — the pro surface quantizes to its own internal style. The
palettes are NOT the game's chips (Sal near-misses; Carmine's purples
are simply foreign). Board question, not session doctrine: do
portraits get their own close-up palette register (a recorded
per-portrait palette, validated for register-law compliance — warm for
family, ink for pressure, case blue never on civilians), or must they
be curated/quantized toward game chips? The 32-color count itself is a
vendor-conformance canary, never quality evidence.

## Draft validator contract (from measurement — NOT ratified)

Calibration before doctrine (the E06 lesson): two samples license a
draft, not thresholds. Proposed `validate_portrait`:

1. Size exactly 64×64, RGBA, hard alpha {0, 255}. (Measured: both.)
2. Opaque coverage within a measured band — round 1 measured 57% and
   60%; the floor is DEFERRED until more portraits exist. Recorded
   band, no invented threshold.
3. Reserved-register mechanics (exact-color, testable): case blue
   #3854DA never present; gold pixels only for characters who own a
   gold tell.
4. Identity facts are BOARD JUDGMENT against the E09 brief (hair
   shape/color, facial hair, garment class, accent, age) — recorded
   per portrait as a checklist in provenance, not automated.
5. Palette register: pending the board's ruling above.

## Open at the board

1. Carmine re-roll (seed change is the only lever; 25 gens/attempt) —
   or hold Carmine until a better counter-tool exists (e.g. feeding a
   curated, more face-legible input variant).
2. Sal: accept the beard or re-roll.
3. Third portrait: the user's pick (session recommends Tony or Bee).
4. Palette-register ruling (own register vs curation toward chips).
5. Spend ledger observation, flagged: 50 generations were debited
   between this session's first balance read (4583 remaining) and the
   pre-submission read (4533) with no generation activity from this
   session in between — unexplained; the vendor balance is the only
   authority for MCP-side spend and the gap is recorded, not smoothed.
