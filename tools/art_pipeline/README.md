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
| `palettes.py` | Palette extraction, hex round-trip, forced-palette strips |
| `previews.py` | Integer nearest-neighbor enlarge / explicit NN reduce |
| `validation.py` | Candidate contract checks — refuses, never repairs |
| `contact_sheets.py` | Labeled review boards with pass/fail markers |
| `provenance.py` | Credential-free JSON generation records |
| `pixellab_client.py` | Thin stdlib client for the PixelLab REST API |

## Running the tests

```
python3 -m unittest discover -s tools/art_pipeline/tests -t .
```

Requires Pillow (`pip install Pillow`); deliberately not added to the game's
dependency set — the game itself remains zero-dependency.

## PixelLab operation choice

`generate-image-bitforge` is the selected operation: it is the only endpoint
combining a style reference image, a forced palette (`color_image`),
transparent output (`no_background`), init images, seeds, and direct 16×16
output (documented as a preferred size). `pixflux` has a 32×32 minimum and
no style image; the remote MCP wraps these same endpoints but cannot be
attached to a running session and offers no byte-exact file handling, so the
REST API is used directly.
