# Experiment 11 — Portraits: The Close-Up Register (2026-08-10)

Status: **THREE PORTRAITS APPROVED (Sal, Carmine s11104, Bee s11123)
and the PORTRAIT RECIPE RATIFIED (2026-08-10 board): brief-in-words
prompt + approved-sprite head init@70 (or recorded rooted intermediate
@110) + standing negatives, pixflux 64px, view side, ~1 gen/attempt.
Curation queue (carmine purple irises, bee lens tint) recorded, NOT
ruled — approved portraits are approved AS-IS.**

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
(2026-08-10 docs pass: the contradiction is confirmed against the
live schema text — "16/32/48/64 = 20 generations (1K)" — with no
documented mechanism that reaches 25 at 64px. Escalation to vendor
support recommended, alongside the unexplained 50-gen debit below.)

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

## Board rulings (2026-08-10, round 1)

1. **Sal APPROVED as-is** — the beard drift accepted ("dignified elder
   host"); `approved/sal_portrait64.png` with approval record.
2. **Carmine: re-roll seeds now** (executed as round 2 below).
3. **Third portrait: Bee** (executed in round 2).
4. **Palette law RATIFIED: own close-up register.** Portraits keep
   their generated palettes, validated for register law only (warm for
   family, ink for pressure, case blue never on a civilian). No
   quantize toward game chips.

## Round 2 results (3 calls, 75 generations — measured 25×3 exactly)

**Carmine s11002 (re-roll A): MISS.** The invented jewelry and visor
died (14 gold px = a plausible collar clasp, zero blue) — but the age
drifted young again. A composed young man in a navy coat is not the
lender.

**Carmine s11003 (re-roll B): MISS, closer.** The age landed — lined
elder, silver sweep — but the model invented an EYE PATCH and a
rust-brown stain, and the coat became a v-neck sweater. Right decade,
wrong movie.

**Bee s11021: CATASTROPHIC MISS.** Her deep skin ramp rendered as
blue-ink alien skin with blank white eyes and an invented segmented
metal collar. The question this call was asked — does the pro surface
respect a deeper skin ramp from sprite ancestry alone — is answered:
NO. The surface mapped dark skin into its ink register. This is the
ghost failure's close-up cousin, and with no prompt surface there is
no negative to counter it.

**Finding (5 calls, 125 generations):** the seed-luck hypothesis is
dead. Four identity failures in five calls, each inventing a different
accessory (visor, earrings, eyepatch, collar). The promptless pro
surface amplifies exactly the information the input sprite carries:
Sal (max facial info — hair mass, mustache pixels, waistcoat blocking)
succeeded; Carmine (abstract ink column) and Bee (deep skin at 32px)
gave the model's priors a vacuum, and the priors filled it. Portrait
fidelity scales with input face information — now confirmed across
three characters, not predicted from one.

## Method pivot PROPOSED (flagged loudly; no spend until ruled)

Drop the promptless tool for the remaining cast. Generate busts
directly via the proven CHARACTER RECIPE on the ordinary image
surface (pixflux/pro): hand-blocked 64px bust anchor (hair shape and
color, facial hair, brow, jaw, deliberate skin ramp — the E09 recipe
at portrait scale), init@~140, written-heritage prompts, the standing
negatives ("anime, manga, chibi, big eyes, glossy hair, ghost, pale
white face, washed out") plus per-character age/clean-shaven words.
Every counter-tool the cast recipe earned applies again, and pixflux
at 64px costs ~1 generation per attempt against 25 for the promptless
tool. The promptless surface stays recorded as viable ONLY for
high-info sprites (it produced Sal). Identity-by-ancestry weakens to
identity-by-anchor — the same standard the approved cast itself met.

## Round 3 — the user's ruled method, first attempt (4 gens)

The board superseded the session's hand-blocked-anchor proposal with a
better formulation: **prompt for how we ENVISION the character
(the E09 brief in words), using the signed-off sprite as a ROUGH
STARTING POINT.** Ancestry stays pixel-derived with no hand-invention:
the init is a recorded deterministic head crop of the approved sprite
(top 16 opaque rows, opaque-column crop, square pad, NN ×4 to 64).

Result, honestly: **direction right, knob wrong.** All four outputs
(carmine s11101/11102, bee s11121/11122) kept the init's 4×4 block
structure — init@120 treated the NN blowup as structure to preserve,
so effective detail stayed ~16px. Blocky heads, not busts. But two
questions died in the same 4 gens: Bee's skin came back BROWN (the
prompt counters the blue-alien mode) and Carmine's tiepin and silver
register appeared. The prompt surface works; the init strength was
calibrated for real anchors, not for blown-up crops.

## Round 4 — strength correction + controls (4 gens): CONVERGED

1. **carmine s11103, head-init@70:** true bust — gaunt lined elder,
   silver sweep, dark coat, oxblood tie. Drift: a small gray mustache
   (unlicensed by the brief) and a tie where the brief says tiepin.
2. **carmine s11104, pro-elder-init@110 (labeled experiment: init =
   round-2 s11003, itself generated from the approved sprite — the
   ancestry chain is fully recorded and rooted in approved pixels):**
   the strongest Carmine yet — wild silver hair, deep frown, black
   coat, the eyepatch negated away. Two purple iris pixels are
   curation-class.
3. **bee s11123, head-init@70:** deep brown skin, legible wire
   glasses (the tell that failed three sprite generations reads at
   64px!), black bob, cream cardigan. Drifts: bob vs the brief's
   short crop; rose-tinted lens pixels; reads young.
4. **bee s11124, no-init control:** afro, tan cardigan, and a GOLD
   NECKLACE — the jewelry negative failed AND gold is reserved. The
   control proves the init earns its place: s11123 is measurably
   closer to the sprite identity (hair class, cardigan color, no
   invented jewelry).

Measured (all four): 64×64, hard alpha, coverage 41–59%, 42–85 free
colors (no palette forcing was applied; the own-register ruling
stands). Cost: 1 generation per attempt, REST-ledgered — against 25
promptless. Eight total generations to converge, versus 125 spent
learning the promptless surface's limits.

**PORTRAIT RECIPE (ratification candidate):** envisioned-character
prompt (E09 brief in words, heritage plain) + approved-sprite head
init at strength ~70 (or a recorded rooted intermediate at ~110) +
standing negatives + per-character counter-terms, pixflux 64px,
view "side", medium shading/detail. The promptless pro tool remains
recorded as viable only for high-info sprites (Sal).

## Open at the board (after round 4)

1. Carmine pick: s11104 (session recommends) vs s11103 vs re-roll.
2. Bee pick: s11123 (session recommends) vs re-roll (crop-hair
   counter-words, lens-tint negatives).
3. Ratify the PORTRAIT RECIPE above for the remaining cast.
4. Curation queue if picked: s11104 purple irises; s11123 lens tint.
5. Spend ledger observation, flagged: 50 generations were debited
   between this session's first balance read (4583 remaining) and the
   pre-submission read (4533) with no generation activity from this
   session in between — unexplained; the vendor balance is the only
   authority for MCP-side spend and the gap is recorded, not smoothed.

## The roster round (2026-08-11, ruled arc: 10 gens)

The remaining eight cast under the RATIFIED recipe, one seed each +
two targeted re-rolls. First-seed keepers: tony (balding, mustache,
chain — the cook exactly), rosa, lena (hoops licensed — hers),
vinnie; acceptable with drift flagged: marcus (neater than
"unfinished"), sammy (jacket drifted hoodie — slightly off-period).
Misses re-rolled with sharpened counters: angelo (skin darker than
his olive sprite + blank eyes; re-roll s11252 improved the face,
skin still browner than the sprite — flagged, the board judges) and
priya (loose hair; re-roll s11262 pulled it back; hair reads
gray-streaked and older than the bio — flagged).

Curation queue executed as leaf-asset revisions (candidates, not
swapped into approved/ without the word): carmine's 2 violet iris
pixels found at their MEASURED rows and inked (two earlier hunts
missed — one global, one stopped a row short; lesson: measure the
target's rows, not the assumed zone); bee's lens tint required THREE
passes — a global color hunt mottled her face (REJECTED, the booth
polarity lesson extended: color hunts are REGION-SCOPED), the
frame-derived region worked. Side effect shown honestly: bee's rosy
cheek-dots paled with the lenses.

Sprite-side queue items (bee wire glasses, rosa eyes, sammy ankles)
NOT executed: each edits an approved identity source that anchors
rotations, walks, and idles — a cascade of 30+ frames plus frame-0
anchors per character. Deferred to an explicitly-ruled pass with the
cascade priced, rather than quietly de-anchoring the motion canon.

AWAITING the board: the ten-portrait roster (8 picks + carmine/bee
curation swaps), and the angelo-skin / priya-age judgment calls.

## Angelo's eyes (2026-08-11, user board reflection; 0 gens)

The board approved angelo s11252 but flagged the plain white eyes.
The zoom found the true cause: pupils EXISTED (2px each, rows 23-24)
but a full row of white sclera sat beneath them — the under-white is
what read as wide startled blankness, the opposite of heavy-lidded
calm. Fix: 4px recorded curation extending each pupil one row down
into the under-sclera band, corner glints kept. The gaze now reads
direct and settled. `angelo_portrait64_curated` supersedes the raw
seed as the approval candidate.

## Vinnie's scale (2026-08-11, user board question; 1 gen)

"Why does Vinnie seem so small?" Measured cause: the head-init
recipe's FLOOR-division integer scaling. Portrait mass tracks init
mass almost exactly (tony 70%->71%, priya 100%->100%), and Vinnie —
the hulk class, head sunk into wide shoulders — produced a WIDE crop
whose floor factor left the init at 34% of canvas -> portrait at
37%. The recipe punished exactly the character whose build should
crowd the frame: the game's biggest man got its smallest portrait.

RECIPE AMENDMENT: hulk-class (wide-crop) characters use
FILL-AND-CLIP inits — ceil-factor NN scale, overflow clipped at the
canvas edge; a hulk may bleed off his own frame. s11272 regenerated
from the v2 init: coverage 55%, shoulders spanning edge to edge,
the menace restored. Supersedes s11271 at the board.

## Bee's "weird things" (2026-08-11, user board; 0 gens)

The board asked why Bee had weird marks around her eyes, and the
answer was the session's own v2 curation: the frame-derived region
box was polluted by her black bob (dark-pixel detection can't tell
hair from glasses), stretched to rows 12-31, and BLEACHED HER CHEEK
BLUSH into gray-green smudges. The per-row rose census separates the
features cleanly — lens tint lives at rows 23-27, blush at rows
30-33 — and curation v3 recolors the lens band only (34px), starting
from the approved original so the blush survives. Lesson appended to
the region-scoping law: derive regions from the TARGET FEATURE's own
census, never from a proxy detector another feature can pollute.
