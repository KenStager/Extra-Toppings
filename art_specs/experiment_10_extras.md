# Experiment 10 — Extras: Anonymity as a Design Target (2026-08-10)

Status: **4 base picks + 12 recolor variants AWAITING USER APPROVAL;
recolor.py codification follows approval.**

Design law and separation rule: experiment_09_cast.md "extras
program" section (user ruling: extras never share a body with the
named cast; zone-unique coloring for maskless recolors; legible
anonymity — no accents, no tells, common silhouettes).

## Results (10 generations: 4 bases × 2 seeds + 2 man re-rolls)

All 10 pass the character contract (kid at a (8,14) floor — a child
is short; number checked against the pick, per the invented-threshold
lesson). The strip-spending law was violated by the session AGAIN and
is owned again: cream sat in the shared strip with no cream mass in
any anchor, and ghosted three faces (man s10002, woman s10011, elder
s10021 — a featureless white blob). The correction (cream subtracted)
fixed the man in one re-roll pair. The law now has three confirmations
across two experiments; it is not a suggestion.

PICKS (provisional): man s10003 (clean everyman; s10004 grew horn
tufts — rejected), woman s10012, elder s10022 (the standout — silver,
stooped, warmly lined), kid s10031. Kid carries a REAL zone violation:
the model gave him hair-colored shoes, so a hair swap would tint
them; recorded fix is a 4-px deterministic shoe-swap to black at
approval time (curation, recorded). Zone-uniqueness measured per
candidate and recorded in provenance.

12 demo variants (3 per base: hair/top swaps within legal ramps) on
`review/extras_final_board.png` — every variant is a recorded mapping,
zero generations. On approval: recolor.py enters the pipeline with
tests (global swaps + optional region masks + a zone-uniqueness
checker), and the approved variant roster becomes data, not code.

Tier note: account upgraded to 10 concurrent background jobs
(2026-08-10); batch drivers may widen from the 8-job pacing.

## Approval and codification (2026-08-10, user's proceed)

Four bases APPROVED into `approved/` (kid with the recorded 3-row
shoe curation). Measured zone report drove the roster design: man and
elder hair colors are globally zone-unique on the approved bases
(global swaps legal); woman and kid are NOT (hem pixels / body
shading measured), so their hair swaps are head-region-scoped in the
roster data. `recolor.py` is pipeline code (mapping application with
optional region, ramp-collapse refusal, zone-uniqueness checker, the
12-variant roster as data; 6 tests — suite 73). Every variant is a
recorded mapping; the roster renders deterministically from approved
bases into `roster/`.

## Taxonomy v2 — extras as the simulation made visible (2026-08-10)

User directive: extras are a MAJOR system; refine the approach. The
reflection reframes them: extras are not wallpaper, they are game
state rendered — traffic multipliers are crowd density, district
identity is who walks there, heat is uniforms on the street, the
after-dark register is who is out at night. Refinements adopted:

1. **Anonymous individuals, legible types.** The anonymity law
   gains a clause: extras carry NO individual tells but MUST carry
   their TYPE tell at costume level. Type-classes and their district
   homes: civilian (everywhere; the 4 approved bases), student
   (University Hill), dockworker (Old Harbor), patrol officer (heat,
   any district), night crowd (the Meadows; recolor-class — dark
   tops on civilian bases), seated customer (shop interiors — a
   genuinely new silhouette class). Festival/churchgoer variants
   wait for the Little Sicily scene work.
2. **Institutional blue gets its job.** The patrol officer wears
   case blue `#3854DA` — the reserved institutional register used
   for exactly its chartered purpose: heat made visible. FLAGGED for
   the board: first use of case blue on a person.
3. **Reserved-identity rule (testable).** Extras may never wear the
   named cast's identity features: heat-red hair (Lena), a
   full-cream chef field (Priya), the long-coat silhouette
   (Carmine), gold anywhere (Tony's chain, Carmine's tiepin),
   oxblood knuckle/tape marks (Angelo). Enforced by a unit test over
   the roster data, not by memory.
4. **The variant space is composable**: base × skin ramp × hair ×
   top, every combination a recorded mapping. Skin swaps use whole
   ramps (all three are legal), verified against measured skin
   zones per base. Names encode the recipe
   (`man.skin_m.hair_ink.top_gray`).
5. **Extras walk later** via the proven v3 path, per approved base,
   when street scenes need them.

## Type-class results (2026-08-10, 10 generations, 10/10 PASS)

Provisional picks: cop s10102 (peaked cap + duty belt — instantly a
beat cop; s10101 read mall-guard), student s10111 (scarf/sweater
clean), docker s10122 (broader build), seated_a s10132 and seated_b
s10141 — both CHAIR-FREE, the pick criterion the other seeds failed
by baking chairs into the sprite (the game composites its own
chairs). The cop wears case blue: FIRST use of the institutional
register on a person, awaiting the board's ruling alongside the
picks. The seated posture survived generation — a genuinely new
silhouette class at zero extra process cost.

Skin axis + reserved-identity rule codified in recolor.py (skin ramp
shifts one step, double-shift refused as ramp collapse; man's hair
excluded by measured region; RESERVED_TARGETS test keeps heat hair
and gold off every extras mapping — suite 77). Crowd demo:
`review/crowd_demo.png`, 16 distinct passers-by from the 4 civilian
bases at zero generations.

## Crowd wardrobe law (2026-08-10, user board finding)

The user judged the crowd demo's clothes too similar — and the
reflection found a thematic bug underneath: 14 of 16 figures wore
slate, so the crowd read COLD. Slate/ink is the pressure register;
the demo accidentally dressed the neighborhood in carbon-paper
colors. Root cause: generation-time strip subtraction (correct, it
protects faces) starved the BASES of wardrobe variety, and the
roster's swap targets never widened to compensate — even though
recolors are exact-color operations with ZERO ghost risk and may
map into any legal color.

LAW ADOPTED: the warm↔cold axis applies to CROWDS. Default civilian
wardrobe skews warm (cream, pale, tan, rust, burgundy, oxblood);
slate/ink are the minority; case blue never appears on a civilian.
District wardrobe registers ship as DATA (`DISTRICT_WARDROBES`):
Old Harbor work-warms, Little Sicily Sunday cream/oxblood,
University slate/gray (the one place cold-leaning is correct),
Meadows after-dark inks. The enumerated variant roster is superseded
by a composable builder (`wardrobe_variant`: base × skin × hair ×
top × bottom, ordering fixed skin-first so garment swaps into
warm tones never collide with the skin shift), with the
reserved-identity test still standing over every composition.

## Rulings (2026-08-10, user board)

1. **Case blue on the cop: APPROVED.** Codified as sworn-institution-
   only: `#3854DA` joined RESERVED_TARGETS, so no recolor mapping can
   ever put it on a civilian; the cop wears it by generation.
2. **All five type-class picks APPROVED** into `approved/` (cop
   s10102, student s10111, docker s10122, seated s10132/s10141).

## Seated-direction bases (2026-08-11, user ruling: proceed; 4 gens)

Anonymous customers at faced four-tops need back and profile seated
bases (approved seated extras are south-facing only). E10 recipe,
code-blocked zone-color anchors, init@140, 2 seeds each: all four
PASS mechanically, and all four FAILED the recolorability pick
criterion on measurement — **zone collapse**: the "slate shirt"
rendered ink everywhere (top zone 0–13px), merging shirt and
trousers into one color. The fix was the kid-shoe precedent,
region-scoped deterministic zone repair: ink→slate within measured
torso boxes (back s10202: 107px; profile s10212: 46px), zones
verified separated after (109/22 and 59/33). West-facing profile
derived by mirror (extras carry no marks).

Picks: `extra_seated_back_final` (s10202 — hair zone present, honest
back read), `extra_seated_profile_final` (s10212 — lean-in posture),
`extra_seated_profile_west_final` (mirror). Sign-off render
delivered: two four-tops seated under the crowd wardrobe law (warm
tops via exact-color swaps on the repaired zones, slate minority).
AWAITING the board's sign-off on chairs + seated bases together.

Lesson: zone compliance is MEASURED at pick time, never assumed —
generation collapsed the zones even with zone-colored anchors at
init@140, and only the census caught it.
