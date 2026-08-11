# Experiment 07 — Status Plaques (OPEN/CLOSED) (2026-08-10)

Status: **candidates rendered, 0 generations — AWAITING USER APPROVAL.**

## Question and theme role

Question: none for the vendor — this is deterministic-layer work under
the frozen brand-geometry policy (lettering is code). Theme role: the
door state IS the thesis in miniature — the OPEN plaque is oven warmth
(oxblood enamel, cream lettering, gold trim), the CLOSED plaque is
carbon-paper pressure (carbon ink field, pale lettering, worn-gray
trim). One asset family, both registers.

## Contract

`branding.build_status_plaque(text, warm, canvas=(64, 32))` — plaque
auto-sizes to the text (5×7 font + 10 px enamel margin, height 16),
centered on a transparent 32-grid-aligned canvas so OPEN (33 px) and
CLOSED (45 px) ship on identical canvases. Cord holes at the top
corners. Chips only, hard alpha, black outline; oversized text REFUSES
(never shrinks or clips). Five tests pin determinism, state
difference, chip discipline, and the refusal.

## Candidates

`.private_art/experiment_07_signage/candidates/`:
`plaque_open_64x32.png`, `plaque_closed_64x32.png`; board at
`review/signage_board.png`. Both legible at native 1× on the board's
inset copies. No provenance records needed — no vendor call occurred;
git history of `branding.py` is the full provenance.

## Approval (2026-08-10, user board)

"Signage looks good" — both plaques approved into `approved/`.
