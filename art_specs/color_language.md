# Extra Toppings — Whole-Game Color Language v0.1

**Status:** recommended working baseline for the first visual scene studies  
**Scope:** environment art, narrative artifacts, UI semantics, districts, rivals, time of day, the Sit-Down, and post-payoff paths  
**Foundation:** Omega Modern native 16 px artwork

## The decision

The game’s visual thesis should be:

> **Thirty years of oven warmth against thirty days of carbon-paper pressure.**

More specifically: flour dust, old tile, sauce, red vinyl, oven light, newsprint, warehouse brick, harbor steel, carbon copies, and ledgers. DiNapoli’s is an ordinary local institution whose legitimate machinery—pizza boxes, delivery tags, supplier forms, registers, employees, storage, and the wagon—also runs the underground operation.

The illegal layer should therefore **not** introduce a separate black-and-red “crime palette.” Its tension comes from changing the meaning of familiar materials.

No new colors are needed for v0.1. The 11 shortlisted donor sheets in the candidate atlas already contain the entire language. The 13-color atmosphere core below accounts for **77.9% of their opaque pixels**—319,907 of 410,832—so mood can come from disciplined selection and scene balance rather than wholesale recoloring.

That measurement covers exactly `tileA5_inside`, `tileB_inside1` through `tileB_inside5`, `tileB_town`, `tileB_tech`, and `tileC_town2` through `tileC_town4` at native 1× resolution. It is not a claim about every sheet in Omega.

This is a **semantic environment and interface palette**, not a hard global indexed palette. Character skin and hair, portraits, cutscenes, and special props may use additional Omega-native colors. “No new colors” means the first scene experiments do not need invented swatches; it is not a permanent prohibition if later authored work proves a real gap.

## 1. Atmosphere core

These colors are the default material vocabulary and should supply the majority of ordinary and daytime scenes. Native dark extensions such as Harbor Night and Warm Black may displace them after hours. This is a compositional rule, not a per-scene quota.

| Token | Hex | Role |
|---|---:|---|
| Sprite Black | `#000000` | Existing exterior sprite silhouettes and the deepest separations; avoid as a broad UI field |
| Carbon Ink | `#303B5A` | Text, internal shadows, paperwork ink, suits, dark panels |
| Dock Steel | `#4E6472` | Asphalt, stainless fixtures, machinery, rainy streets |
| Harbor Patina | `#6C8C88` | Oxidized metal, old tile, muted glass, cover/laundering language |
| Concrete | `#9D9C9C` | Sidewalks, utility surfaces, disabled or exhausted states |
| Tile Fog | `#CBD7CC` | Cool light surfaces, old appliances, institutional paper |
| Flour | `#FBFBE8` | Cleanest highlight, menu surface, light text |
| Oxblood | `#680828` | Warm shadow, vinyl, leather, heritage, serious conversation |
| Harbor Brick | `#B1552E` | Brick, cooked surfaces, worn wood, dock rust |
| Crust / Rust | `#C68239` | Pizza crust, wood, cardboard, warm metal |
| Kraft | `#D4A068` | Boxes, supplier slips, shadowed paper |
| Oven Paper | `#F8D088` | Lamplight, aged forms, warm wall and food highlights |
| Newsprint | `#F8F8C0` | Newspapers, receipts, menus, dough highlights |

The core deliberately makes food and city materials rhyme: crust becomes rust, cheese becomes streetlight, flour becomes newsprint, sauce becomes vinyl and red pencil, and harbor teal becomes old tile and laundering paperwork.

## 2. Supporting native ramps

Use one local ramp to identify a district, system, character, or authored event. High-chroma peaks should remain small and localized rather than becoming environmental washes; exact coverage depends on the scene.

| Ramp | Native colors | Use |
|---|---|---|
| Sauce / consequence | `#680828 → #A81031 → #FF2B3C → #FF8A7B` | Heritage red through critical escalation |
| Cheese / brass | `#DFBB02 → #FFE976` | Food, honest opportunity, candlelight, restrained reward |
| Cold / electric | `#303B5A → #3854DA → #4E7BF0 → #4FAAFF → #75E2EF` | Case, police, screens, refrigeration, rain and glass |
| Grounded green | `#156444 → #158541 → #92D598` | Clean books, tradition, herbs, stability |
| Nightlife | `#303B5A → #9659A5 → #CE9EDA → #E2C7E9` | Meadows, intrigue, velvet, reflected club light |

Reserve `#06C245`, `#51F040`, and `#D438CA` for tiny signals or lighting pulses. They should never become broad environmental fills.

## 3. Semantic colors

### The shop and immediate danger must use different reds

- **DiNapoli’s identity:** `#680828` shadow, `#A81031` main sauce red, `#FFE976` cheese lettering, `#FBFBE8` highlight.
- **Critical danger:** `#FF2B3C`, reserved for a raid in progress, serious injury, warrant, irreversible failure, or comparable immediate threat.

The current canon distinguishes two identities:

- **DiNapoli’s Pizza** is the in-world shop and storefront. Its identity should use the deeper sauce red.
- **Extra Toppings** is the game title. Its title treatment may echo DiNapoli’s sauce-and-cheese language, but it should not automatically replace the shop name on the façade.

Putting “Extra Toppings” on the storefront would therefore be a deliberate canon change or a future shop-renaming feature, not merely logo placement. Neither identity should use critical red as a broad brand color.

### Heat and Case are opposites

| System | Colors | Behavior |
|---|---|---|
| **Heat** | `#FF8628` with `#FFE976` peak | Warm, volatile, local, able to cool overnight; use flicker or a broken-edge icon |
| **Case** | `#3854DA`, `#4E7BF0`, `#75E2EF` | Cold, segmented, institutional, persistent; use a file-tab or stacked-record icon |
| **Critical** | `#FF2B3C` | A rare interruption when a threat becomes immediate |

This reflects the actual mechanic: **Heat is weather; the Case is climate.** Red should not mean “law” in general.

### Required surface pairings

Semantic colors are marks and fills, not automatic text colors.

| Role | Light surface | Dark surface |
|---|---|---|
| Case | `#3854DA` on Flour is about **5.82:1**; reserve `#4E7BF0` for larger marks | `#75E2EF` on Carbon Ink is about **7.31:1** |
| Heat | Use a Carbon Ink label beside the orange mark | `#FF8628` on Carbon Ink is about **4.58:1** |
| Critical | Use `#FF2B3C` as a black-outlined symbol with a neutral label, not a paragraph color | The same black outline and Flour label apply |
| Clean money | `#156444` on Flour is about **6.83:1** | `#92D598` on Carbon Ink is about **6.42:1** |
| Laundering | Use `#6C8C88` as the receipt-loop fill with Carbon Ink text | Use the teal icon with Flour text; do not set small copy in teal |

### Money and laundering

| State | Colors | Required non-color cue |
|---|---|---|
| Clean money | `#156444 → #92D598` | Square bill/register icon and orderly frame |
| Dirty money | `#C68239 → #C9A76D` | Stained bill or clipped frame |
| Laundering / cover | `#6C8C88` | Receipt-loop icon connecting the two ledgers |

Do not encode clean versus dirty money by hue alone. Labels, icons, and geometry must remain readable in grayscale.

## 4. The daily visual rhythm

| Phase | Balance | Mood |
|---|---|---|
| **Morning** | Newsprint, flour, harbor patina, steel, restrained brick | Broad and ordinary; the paper and supplier forms make the city legible |
| **Service** | Warmest material balance; brick, crust, tile, food and district accents | DiNapoli’s feels worth saving; legitimate trade is not a thin disguise |
| **Dispatch / ride-along** | District materials, pizza boxes, vehicle interior, streets and traffic-stop hardware | Routes can occur under varied lighting; they should not automatically become night-noir scenes |
| **Night accounting** | Warm-black and carbon surroundings; isolated newsprint, oxblood, kraft and ledger green | The shop becomes a pool of oven and desk light |
| **High Case / crackdown** | Institutional gray, navy, blue and cyan occupy more space | Warmth is displaced, not erased; crisis red stays rare |

Do not darken the whole game mechanically as day 30 approaches. Pressure should accumulate through carbon copies, debt and supplier paper, ledgers, rivals, colder official documents, patrol hardware, sealed notices, tighter compositions, and less warm breathing room.

## 5. Event modulation

Events rebalance local materials rather than applying full-screen color filters.

| Event | Modulation |
|---|---|
| **Meadows concert** | Deep navy and restrained plum with marquee amber; cyan or magenta appears only as a small stage-light peak |
| **Port seizure** | Old Harbor rust and patina recede beneath steel, official paper and cold inspection tabs; red appears only on a sealed notice if the event escalates |
| **Campus crackdown** | Official gray-blue forms, barriers and patrol hardware intrude into University Hill’s coral/ivory all-nighter palette |
| **Heat wave** | Bleach toward Flour, Kraft and Tile Fog with tired yellow and shallower cool shadows; do **not** use the orange Heat-mechanic treatment |
| **Saint Rosalia festival** | The warmest communal state: Flour, Oxblood, basil green and candle gold; criminal tension remains concealed beneath clean festival light |
| **Warehouse robbery** | Broken steel, Kraft tags, Harbor Brick and displaced inventory; Critical red appears only if the player is in immediate danger |
| **Dockworker payday** | Old Harbor patina, denim-like steel, brick and amber window light become temporarily richer |
| **Food critic** | Unusually clean Flour, Tile Fog, polished steel and honest sauce red; scrutiny comes from cleanliness, not police blue |

The weather event and the law mechanic must never be confused: **heat-wave weather bleaches the world; mechanical Heat uses the orange diamond and broken-edge language.**

## 6. District accents

District colors belong on signs, flyers, map borders, props, lighting, and local materials—not on generic status states.

| District | Accent set | Character |
|---|---|---|
| **Old Harbor** | `#152653`, `#6C8C88`, `#B1552E`, `#F8D088`; tiny `#75E2EF` reflections | Docks, loading doors, wet steel, brick, payday window light; the visual foundation of the game |
| **University Hill** | `#FBFBE8`, `#FF8A7B`, `#B7C0E6`; tiny `#4FAAFF` screen peaks | Ivory and poster coral carry the map identity; muted collegiate indigo, vending machines and screens support the all-nighter mood without borrowing the Case color |
| **Little Sicily** | `#680828`, `#156444`, `#FFE976`, `#FBFBE8` | Family tables, parish stone, wine, basil, candlelight, Saint Rosalia banners |
| **The Meadows** | `#152653`, `#9659A5`, `#75E2EF`, `#DFBB02` | Concert posters, velvet, marquee light, clubs and money after dark without cyberpunk saturation |

## 7. People and rivals

- **Carmine:** warm black, carbon ink, money green, muted brass, immaculate flour. He should feel like debt made polite and contractual, not a costume gangster.
- **Sal:** near-black, oxblood, bottle green, brass, ivory. His excellent restaurant and quiet control should create less visual noise than anyone else.
- **Vinnie:** black with the pack’s cheap peak colors—`#FF8A7B`, `#FF8628`, and `#FFF719`—plus dingy gray. His pizzeria language is deliberately too loud and slightly wrong without borrowing Critical red.

## 8. Narrative artifacts

| Surface | Palette |
|---|---|
| Morning newspaper | `#F8F8C0` or `#DFDED2` paper, `#303B5A` ink, slate photos, `#A81031` spot headline only |
| Menu / supplier sheet | Flour or newsprint, shop sauce, cheese, crust, carbon ink |
| Clean ledger | Newsprint paper, formal navy rules, grounded green confirmation |
| Dirty ledger | Kraft paper, oxblood rules, grease/rust marks, irregular annotations |
| Police / Case material | Tile fog or official gray paper, carbon ink, blue rules, cyan evidence tabs, critical-red stamp only at escalation |
| Underworld note | Kraft, carbon copy blue, grease brown, dried oxblood—never theatrical black paper with bright red type |

## 9. The Sit-Down

The payoff-triggered Sit-Down is the game’s central visual fork and should have a dedicated composition:

- **Carmine’s restaurant before lunch:** immaculate Flour/ivory, Oxblood upholstery, Carbon Ink, muted brass and espresso brown. Rival cars remain visible outside when a vendetta or warned raid is active.
- **The table:** four offer chairs plus “the one you came in with” for stand-pat. The room itself does not become a rainbow of branch colors.
- **Seated offer:** one small branch-colored place card, napkin or folder identifies each chair.
- **Unavailable offer:** a physically empty Concrete/Tile Fog chair carries its calendar or Case reason. Do not merely gray out a menu label.
- **Frozen versus live Case:** the closing-time ledger and the live morning file appear as two materially distinct documents—warm Newsprint/Oxblood versus cool official paper/Case blue—so the offer calculation and present danger cannot be mistaken for the same state.
- **Stand pat:** keeps the existing DiNapoli’s/Old Harbor balance. Choosing it clears every offer accent rather than introducing a fifth branch palette.

## 10. Post-payoff path modulation

Branches rebalance the same world instead of inventing new palettes.

| Branch | Accent set | Direction |
|---|---|---|
| **Straight Path** | `#FBFBE8`, `#CBD7CC`, `#303B5A`; small `#92D598` | Pizza warmth expands as supplier and coded-board colors disappear, while ash, counsel files, witness retention and payroll pressure prevent a simple clean-green victory look |
| **Quiet Sale** | `#6C8C88`, `#C9A76D`, `#DFDED2`; receding `#680828` | Four diligence days, inspection-white surfaces, buyer forms and the daily marked price steadily remove DiNapoli’s red from the frame |
| **Harbor War** | Base `#000000`, `#152653`, `#680828`, `#B1552E`; target overlay | The War Board inherits the named target: Sal adds controlled green/brass/ivory; Vinnie adds cheap salmon/orange/yellow. Critical `#FF2B3C` remains signal-only, never a broad war fill |
| **Carmine’s Partner** | `#0E0208`, `#680828`, `#156444`, `#C9A76D`, `#FBFBE8` | Controlled, polished, permanent machinery; provisional until the branch is authored |
| **Stand pat** | Existing DiNapoli’s and Old Harbor balance | No new palette; the shop and city remain what they were when every other chair clears |

Branch accents modulate scenes and artifacts. They must not color branch-choice labels as moral alignment or replace the universal status semantics above.

## 11. Pixel-art and readability rules

- Work at native 1× resolution on Omega’s 16×16 tile grid; multi-cell props, buildings and character frames keep their native dimensions.
- Use nearest-neighbor scaling and disable filtering only for Omega-derived raster art. High-resolution iOS interface text, newspapers, menus and other narrative typography should remain properly antialiased.
- Use 3–5 colors per material. Keep black for external silhouettes and hue-shift internal shadows.
- Do not place `#C9A76D` and `#D4A068` beside one another as consecutive shade steps; their luminance is too similar.
- Strong native text pairs include:
  - `#FBFBE8` on `#303B5A` — about **10.57:1**
  - `#FFE976` on `#680828` — about **10.38:1**
  - `#75E2EF` on `#303B5A` — about **7.31:1**
  - `#303B5A` on `#CBD7CC` — about **7.44:1**
- Avoid tiny text in `#FF2B3C` on `#680828` or `#DFBB02` on `#FBFBE8`; those pairs do not carry enough contrast.
- Every money, route, rival, Heat, and Case state needs a label plus an icon, shape, or pattern. Color is reinforcement, never the only carrier.
- Do not use native-1× pixel lettering for body copy on an iPhone. Keep text on opaque or nearly opaque backplates, scale pixel scenes by integer factors, and validate the smallest supported landscape device for reading and touch comfort.

## 12. Approval sequence

Treat this as the palette freeze for the first experiments, then validate it in four controlled studies:

1. **Midday DiNapoli’s storefront and dining room** — inherited warmth, Old Harbor context, restrained brand red.
2. **After-hours kitchen and two-ledger desk** — the legitimate and illicit layers sharing one material language.
3. **Dispatch / ride-along under active Heat and high Case** — district identity, Heat orange, official blue/cyan and event-only crisis red working together without forcing every route into dusk.
4. **The Sit-Down before lunch** — four place-card accents, empty blocked chairs, the closing ledger, the live file and stand-pat all reading inside one restrained restaurant palette.

Only after those studies read as one game should title and storefront identity exploration begin. The Extra Toppings title treatment and the DiNapoli’s storefront mark will then use proven subsets of the same world palette without being mistaken for one another.

## Repository grounding

This direction is based on the game’s current setup and mechanics: DiNapoli’s thirty-year history, the Old Harbor setting, the morning/service/night loop, four districts, two ledgers, local Heat versus persistent Case, the eight current city events, Sal and Vinnie’s contrasting operating styles, the Sit-Down’s four offers plus stand-pat, the Straight Path, Quiet Sale, Harbor War, and the planned Carmine’s Partner branch.
