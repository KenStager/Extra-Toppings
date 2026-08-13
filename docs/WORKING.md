# Working agreements and verification runbook

This file is the engineering-contract half of the project's process
memory: the standing workflow, what the identity gates prove, and the
engine invariants. The session protocol — the review relay, the
GitHub rules and the runbook commands — lives in `CLAUDE.md`; the
design half is `docs/ACT1_FORK_DESIGN.md` (with its §8 revision
record) and the measurement half is `docs/FINDINGS.md`. When these
files and a newer instruction disagree, the newer instruction wins —
then update the file.

## The standing workflow

Implement → verify (tests + ruff + mypy + BOTH identity gates) → rerun
the relevant `analysis/experiments.py` studies → update
`docs/FINDINGS.md` honestly → commit with detailed messages → push →
PR when ready for review → **merge only on explicit approval**.

- **Honesty is load-bearing.** FINDINGS has recorded retractions and
  criterion misses (rounds 2, 4, 6; round 8 corrections 1–6) and every
  one of them was valued. A measured miss is reported with its
  decomposition, never tuned away quietly. If a §2.7 bar fails, the
  question "is this the bots, the mechanics, or the criterion?" goes
  to review with the data — design constants are changed only on a
  recorded ruling (§8).
- **Bots are instruments, never tuning targets.** Human play on seeds
  24 (forgiving) / 39 (knife-edge) / 8 (hostile) remains the test of
  fun. Branch bots are minimal policies over the *market* bot (the
  "smart bot" §2.7 names).
- **When you fix a bug, prove the test fails on the broken code**
  (`git stash push extra_toppings/` → run the new tests → expect
  failures → `git stash pop`). Regressions drive the ACTUAL player
  paths: scripted consoles through the real `morning()` / `service()`
  / `night()` / scene code, seed scans to reach real stochastic
  events — never hand-built states where a real path exists.
- **Design changes are recorded before implementation** when they come
  from a review ruling: the §8 entry lands as its own commit first.
  Deviations from the design's letter are argued and recorded (§8, and
  `docs/canon/README.md` for canon-level deviations).

## The review protocol

Moved to `CLAUDE.md` (single home). Everything below is written to
survive that reviewer.

## Verification runbook

The commands and the Python-version rule moved to `CLAUDE.md`'s
runbook (single home). What the gates prove:

- **Gate 1 (golden):** 150 seeds × 2 bots replayed flag-off against
  `analysis/golden_act1.json`. Its version, generating commit,
  predecessor hash, reason and file hash are pinned by
  `ACTIVE_BASELINE` in `analysis/equivalence.py`, which is the
  canonical provenance — read it there rather than restating a commit
  here, because a copy of that census goes stale the first time the
  baseline is regenerated (it already had). Three surfaces nightly:
  the save-v2 legacy projection,
  the four shared RNG streams (fork streams provably undrawn), and the
  digest of the complete decision trace — every menu/ask_int/confirm
  PROMPT STRING verbatim. **Never regenerate the goldens for
  transcript-only or fork-side work.** Transcript additions must be
  `con.say`/`con.bullet` only on flag-off paths; existing prompt
  strings are golden.
- **Gate 2 (paired stand-pat, §2.7 criterion 6):** flag-on stand-pat
  vs flag-off, per seed: game trace equal event for event (full lists,
  not digests), nightly projection + shared streams + ending exact,
  fork streams undrawn — plus the existence oracle (a sit-down must
  occur exactly where the flag-off timeline owes one, derived from
  debt_paid_day/day/ending, never from fork code) and the **frozen
  scene schema** (`STANDPAT_SCENE`, versioned, literal in
  `analysis/equivalence.py`, never imported from `sitdown.py`).
  Changing any stand-pat scene prompt/option/order/answer is a
  deliberate act that lands with a schema version bump. Current
  expected count: **79** sit-downs held across the 300 paired runs
  (82 until the P3.5 decoy correction, which changed flag-off
  timelines and so changed how many runs are owed a table; the gate
  derives both sides, so it moved together and stayed 300/300).
- **Scene menus obey progress-last:** deterministic bot handlers pick
  the last option, so every scene menu's last option must progress
  (stand pat / confirm / sign). `ScriptedConsole.scene_menu` fails
  closed (`ScriptExhausted`); ordinary gameplay menus keep safe
  fallbacks, so a menu's LAST option must never destroy assets.
- Both identity gates must hold **with all fork code in the tree** —
  the fork is provably inert unless entered. Branch-side prompts and
  behavior (gated on `state.branch`) may change freely; flag-off and
  stand-pat surfaces may not.
- **WHAT THE GATES AND BATTERIES DO NOT COVER: NARRATION.** They read
  decisions, prompt strings and projected state — `menu`, `ask_int`,
  `confirm` and `scene_menu` — and nothing that reaches the player
  through `con.say` or `con.bullet`. Prose has never been on the
  instrument. **Byte identity therefore does not certify epilogue or
  narrative output**, and a green board is not evidence that a player
  saw anything: narration needs DIRECT PINS on the lines themselves.
  Measured, not supposed — during P4b.4 a defect suppressed the
  ENTIRE ending text of **10 of 300** flag-off runs while gate 1 read
  300/300 identical, the golden hash held, and both fork batteries
  stayed byte-identical at 150 and 500 seeds (FINDINGS round 18
  correction pass 2). This is the gates' documented scope, not a gate
  defect — but it is the scope, and it cuts the other way too: the
  same blindness is what lets transcript-only `con.say`/`con.bullet`
  additions land on flag-off paths without regenerating a golden.

## Engine invariants worth re-reading before touching anything

- `models.fold_case` is the only full-ledger Case fold (3.12 moved
  `sum()` to compensated summation; bit-identity broke once already).
  Two purpose-specific prefix scans exist (`_case_first_crossed_60_day`
  in phases.py, `gate_crossing_record` in sitdown.py); if evidence
  remediation (P2) multiplies them, fold them into one shared prefix
  iterator before copies drift.
- Canonical single homes: branch ids (`models.BRANCH_ORDER` /
  `ACTIVE_BRANCHES`), severance rate (`models.SEVERANCE_PER_HEAD`),
  repricing domain (`models.REPRICE_MIN_PCT`/`MAX_PCT`). Validation,
  draws, sheets and epilogues all read these — never respell.
- `validate_branch_state(branch, branch_state, game_over=...)` binds at
  branch transition AND save-load: dead fields at defaults, per-branch
  required fields, the severance state machine (with the terminal
  sold-cannot-be-pending invariant), and the escrow pricing contract
  (integer points, incident-count relationship). Extend it whenever a
  branch grows state; malformed payloads are refused, not repaired.
- `GameConfig` is immutable, passed explicitly, never persisted; only
  the CLI reads the environment (`EXTRA_TOPPINGS_FORK=1`). The flag
  gates ENTRY only — saves are authoritative for continuation.
- `SitdownSnapshot` stores three primitives; everything else derives
  through the pure evaluator (`sitdown.evaluate_chairs`/`build_view`).
  Eligibility keys to the frozen Case; present danger to the live one.
- Reserved RNG streams: `brokers` draws only inside the Quiet Sale;
  `sitdown` and `war` remain provably undrawn until their phases claim
  them. The sit-down scene itself draws zero RNG and consumes zero bot
  decision RNG.
- Save schema: v3 + additive fields with `.get` defaults (no version
  bump needed for additive changes); v2 migrates forward; unknown
  versions refused. Legacy-unit conversions (e.g. the float discount)
  happen in exactly one place in `save.py` and feed the validators.

## Git

Moved to `CLAUDE.md`'s GitHub protocol (single home), including the
dev-tooling pin. Precedent for the branch-recreation rule: the
ruff-pin commit 283f06d.
