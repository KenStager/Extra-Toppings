# Experiment 09 — The Cast: Memorable at Thirty-Two Pixels (2026-08-10)

Status: **design paper first; generation follows on the same day
(user directive: "make them memorable"). Candidates AWAIT the board.**

## Sources (single authorities for who these people ARE)

`extra_toppings/data.py` EMPLOYEE_POOL (stats, traits, wages, bios),
RIVALS (Sal, Vinnie — style text), and `docs/ACT1_FORK_DESIGN.md`
(Carmine's scenes: the corner table, the fruit basket, the nephew;
staff moments: Bee rechecking the till, Tony watching the oven door,
Marcus cornered by the walk-in). The art invents NOTHING about
character; it translates recorded character into silhouette.

## The design language (how memorability works at 32px)

1. **Silhouette first.** At one tile, memory is outline: build,
   posture, headwear. No two cast members share a silhouette class.
2. **One accent, one story detail.** Each character gets at most one
   accent color and one prop/costume tell (≤4 px). More is noise —
   twice the resolution, not twice the visual noise.
3. **The warm↔cold axis is the loyalty axis.** The shop family wears
   the warm register (cream, dough-tan, oxblood). Pressure wears
   carbon ink and slate. Carmine — the debt made flesh — is the
   coldest figure in the game; institutional blues stay reserved for
   institutions, so even he gets ink/slate, not case blue. Marcus,
   the staffer who talks to detectives, carries ONE slate tell.
4. **Skin ramps.** Two ramps, both from already-legal colors:
   dough-tan (#D4A068/#C68239/#B1552E) and a deeper ramp
   (#C68239 base where mid, or #B1552E base/#680828 shadow) for a
   mixed-city cast — Old Harbor is a port town. FLAGGED for the
   color-language revision: a purpose-built pair of skin ramps is the
   right long-term home; the union rule licenses these interim picks.
5. **Menace without cliché** (theme guard): no guns, no fedora-and-
   tommy-gun mob costume. Vinnie's menace is bulk and stains; Sal's
   is politeness; Carmine's is tailoring. Angelo is dignity, not
   cartoon thug — he did four years and never said a name.

## The briefs

**Staff (warm register):**

- **Rosa Delgado** — driver, principled, twenty years zero accidents.
  Compact and square; hair in a practical bun (ink); slate work
  jacket over warm shirt; upright, feet planted. Accent: cream scarf.
  Read: the person you trust with the wagon.
- **Tony "Two-Slices" Marino** — cook, greedy, best dough hands.
  The WIDEST staff silhouette: round torso, thick forearms, white tee
  + apron, flour dust at the hem. Accent: 2 px gold chain — the greed
  tell, counting other people's money out loud. Read: dough and
  appetite.
- **Beatrice "Bee" Okafor** — counter, observant, ex-shipping-books.
  Slim, straight-backed, deeper skin ramp; round 2 px pale glasses
  glint — THE observant tell; cardigan in pale over cream; pencil
  line at the ear. Read: she has already noticed.
- **Marcus Webb** — driver, reckless, University dropout, low
  loyalty. Tall-thin slouch, hands-in-pockets block, messy hair; one
  SLATE jacket tell on a warm base (the cold streak that talks to
  detectives). Read: fast, unfinished, leaving.
- **Lena Kowalski** — counter, connected, a guy in every district.
  Mid build, heat-orange headscarf (the market-warmth accent, the
  only staffer carrying #FF8628), small hoop earrings; mid-gesture
  posture. Read: the rumor arriving.
- **Sammy Fetch** — driver, indebted, owes Carmine too, sweats.
  SMALLEST silhouette: hunched, cap pulled low (ink), oversized
  borrowed jacket (worn gray); muted everything. Read: trying not to
  be seen.
- **Angelo Ricci** — muscle, known to police, unshakeable nerve.
  Widest SHOULDERS (v-taper, not round like Tony), no-neck block,
  undershirt cream + suspender lines, rolled sleeves, knuckle-tape
  pixels at the fists. Accent: oxblood tape. Read: quiet, immovable.
- **Priya Nair** — cook, ambitious, two-star kitchen, "thinks this
  place is beneath her. It is." PRISTINE double-breasted chef coat —
  the brightest, flattest cream field in the cast (cleanliness as
  contempt); perfect vertical posture, chin up (head sits 1 px
  higher); oxblood neckerchief. Read: too good for this place, and
  correct.

**Antagonists & patron:**

- **Sal Moretti** — Moretti's Trattoria. The restaurateur's dignity:
  silver-gray hair (worn gray), dark waistcoat over cream shirt,
  towel folded over the forearm, slight welcoming lean. Accent:
  oxblood tie. Fights with prices and quiet words — the silhouette
  must read HOST, never heavy.
- **Vinnie "The Oven" Barzetti** — Vinnie's Pies. The HULK class:
  bigger than Angelo, head sunk into shoulders, stained apron (sauce
  stains in oxblood — the shop's own colors turned menacing), heat
  undershirt, burn-dark forearms. The pizza is a crime in itself.
- **Carmine** — the lender. LONG-COAT class, the only one: thin
  vertical figure, carbon-ink coat to the shins, pale gloves, silver
  temple; single 1 px gold tiepin — the only gold he needs. The
  espresso, the fruit basket, the nephew: pressure with manners.
  Coldest palette in the cast, deliberately colder than the rivals.

**Existing "DiNapoli Employee v1"** (E08) is hereby RECAST as the
generic extra/new-hire template, not a named character — the named
cast replaces it on screen wherever the roster is shown.

## Method

Per-character hand-blocked anchors (the silhouette IS the anchor —
build/posture/headwear blocked by hand per brief), per-character
palette strips (chips ∪ ramps ∪ single accent), pixflux init@120,
2-seed pools, character validator ((8,18) floor; Tony/Angelo/Vinnie
widen, Sammy may sit near the floor — measured, not assumed), boards
in role groups. Rotations/walks for approved picks reuse the proven
E08 v3 path (1 gen create + 4 gen walk each) in a later phase, after
the board rules on identity.

Budget this phase: 11 characters × 2 seeds = 22 generations.
Question: does the anchor-silhouette method produce distinct,
memorable, on-bio identities across a full cast? Theme role: the
whole warm↔cold axis, person by person.
