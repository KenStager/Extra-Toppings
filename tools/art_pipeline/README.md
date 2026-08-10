# art_pipeline

Reusable tooling for AI-assisted visual asset experiments (Experiment 01:
whole-pizza prop). Pure Python + Pillow; no other dependencies.

## Boundary rules

- **Nothing licensed lives here.** Omega Modern originals, crops, palettes,
  candidates, and contact sheets live under the repo-root `.private_art/`
  tree, which is gitignored. This package holds code, tests, and blank
  specifications only.
- **No credentials.** The PixelLab token is resolved from
  `PIXELLAB_API_KEY`, then a file named by `PIXELLAB_API_KEY_FILE`, then
  the macOS Keychain item `pixellab-api` (the durable home:
  `security add-generic-password -a "$USER" -s pixellab-api -w`). It is
  held in memory, sent only as the Authorization header, and redacted
  from error text. Provenance records are scrubbed of any
  credential-shaped field before writing.

## Modules

| Module | Purpose |
| --- | --- |
| `inventory.py` | PNG dimensions, color counts, alpha hardness, sha256 |
| `cropping.py` | Exact pixel/cell crops, never resampled |
| `palettes.py` | Palette extraction, forced-palette strips, curation quantize |
| `previews.py` | Integer nearest-neighbor enlarge / explicit NN reduce |
| `validation.py` | Candidate contract checks — refuses, never repairs |
| `contact_sheets.py` | Labeled review boards with pass/fail markers |
| `provenance.py` | Credential-free JSON records; schema v2 with artifact hashes |
| `pixellab_client.py` | Stdlib REST client: retry, spend ledger, both engines |
| `mcp_client.py` | Stdlib JSON-RPC client for the MCP-only tool surface |
| `pixel_font.py` | Deterministic 5×7 caps font (brand lettering is code) |
| `branding.py` | DiNapoli's sign / emblem / awning builders |

## Running the tests

```
python3 -m unittest discover -s tools/art_pipeline/tests -t .
```

Requires Pillow (`pip install Pillow`); deliberately not added to the game's
dependency set — the game itself remains zero-dependency.

## Engine policy (single authority: `art_specs/decision_32px_world.md`)

**pixflux is the default engine** — general-purpose, up to 400px/axis,
and the empirical winner of most cells across every experiment (see the
engine scorecard in the decision doc). **bitforge is niche**: same-object
style variants and canon-adjacent props only — its `style_image` leaks
content across object types, caps at 200px/axis, and must exactly equal
the output size. REST `/inpaint` is avoided (does not preserve unmasked
pixels); MCP `inpaint_image` documents a stronger contract and awaits a
controlled retest. The MCP-only surface (Pro/Pixen models, object
registry, tilesets, UI assets) is reached via `mcp_client.py` — direct
JSON-RPC, no Claude-session attachment, no credential in config.

An earlier revision of this section named bitforge as the selected
operation; that reflected the 16×16 era before the 32×32 decision and
the 49-generation scorecard, and was corrected as a single-authority
defect. History lives in git; the decision doc rules.
