# Working agreements and verification runbook

Everything in this file has, until now, lived in session handoff
prompts. It is the process half of the project's memory; the design
half is `docs/ACT1_FORK_DESIGN.md` (with its §8 revision record) and
the measurement half is `docs/FINDINGS.md`. When this file and a
session prompt disagree, the newer instruction wins — then update this
file.

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

The user relays messages verbatim between the implementing session and
an external reviewer (ChatGPT). The reviewer independently reproduces
everything — exact arithmetic, per-seed determinism, cross-version
behavior, doctored save payloads — and returns findings; expect one or
more correction passes per PR. Write replies to the reviewer with
enough specificity that they can re-derive every claim (exact numbers,
file/function names, what was pinned and where). Flag judgment calls
proactively; the reviewer rules on them. History says the reviewer
finds the thing you decided was probably fine.

## Verification runbook

Python 3.11, 3.12 and 3.13 are all installed; the gates must pass on
**3.11 AND 3.12** (3.13 is run as a bonus and has always agreed).

```
python3 -m unittest discover -s tests          # full suite
ruff check extra_toppings tests analysis       # ruff is PINNED 0.15.x
mypy extra_toppings analysis --ignore-missing-imports
python3 -m analysis.equivalence check          # gate 1: flag-off golden
python3 -m analysis.equivalence standpat       # gate 2: paired stand-pat
python3 -m analysis.experiments fork           # §2.7 branch battery (150)
python3 -m analysis.experiments fork --seeds 500   # confirmation ensemble
```

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

- Develop on the session's designated branch, recreated from
  `origin/main` after each merge (`git checkout -B <branch>
  origin/main`; force-with-lease push is fine when it held only merged
  history; rebase forward any unmerged commits — precedent: the
  ruff-pin commit 283f06d, and this file's own commit).
- Merge commits follow "Merge pull request #N: title". PRs restate the
  full verification evidence; merge only on explicit approval relayed
  by the user.
- The dev-tooling pin (`pip install -e ".[dev]"`, ruff 0.15.x) is
  deliberate; bumping it is its own commit with whatever fixes the new
  version demands.
