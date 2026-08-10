# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Extra Toppings: a terminal pizza-shop crime sim in pure Python 3.10+,
zero runtime dependencies. This file is the session protocol — how a
session orients, works with the reviewer, verifies, and uses git. It
POINTS AT the project's authorities and duplicates none of them; where
it disagrees with them, they win and this file gets fixed.

## Read first, in this order

1. `docs/WORKING.md` — the engineering contract: the standing
   workflow, what the identity gates prove, the engine invariants.
2. `docs/ACT1_FORK_DESIGN.md` — THE design authority. §8 is the
   numbered revision record; the latest revisions plus §7
   (implementation phasing) define what is being built now and which
   gate character each PR carries. §2.7 holds the acceptance criteria.
3. `docs/FINDINGS.md` — every measurement taken, including
   retractions and missed criteria.

`docs/canon/` holds the founding documents, verbatim and never
edited; canon-level deviations are argued and recorded there, never
assumed.

Current position and expected verification numbers live in §7/§8 and
the most recent merged PR's evidence table — deliberately not here,
where a stale copy would read as current.

## The review protocol (Codex relay)

An independent reviewer (Codex) reviews all work; the user relays
messages verbatim in both directions. The reviewer independently
reproduces everything — exact arithmetic, per-seed determinism,
cross-version behavior, doctored save payloads — and returns
findings; expect one or more correction passes per PR. History says
the reviewer finds the thing you decided was probably fine.

- Rulings land before mechanics harden. When a review says "hold":
  correct and return — never argue past it or ship around it.
- Flag judgment calls LOUDLY rather than deciding them quietly: what
  you propose, why, and which PR it blocks. The reviewer rules; you
  record.
- Verify factual claims against the tree (cite file:line) before
  recording them. A ruling recorded on a wrong premise costs a round.
- Report unflattering results exactly as measured; misses are
  decomposed honestly in FINDINGS, never tuned away.
- Write replies with enough specificity that the reviewer can
  re-derive every claim: exact numbers, file/function names, what was
  pinned and where.
- End every work package with a relay-ready summary: what was ruled,
  what was built, exact numbers, what's flagged, what awaits their
  word.
- When wrong, correct plainly and move on. Several of the strongest
  commits in this repo are records of errors.

## GitHub protocol

- Develop on a feature branch; `git push -u origin <branch>`. After a
  merge, recreate it from origin/main (`git checkout -B <branch>
  origin/main`); force-with-lease push is fine when the branch held
  only merged history; rebase forward any unmerged commits.
- PAPER FIRST: any design change is a §8 revision in
  `docs/ACT1_FORK_DESIGN.md`, committed and pushed BEFORE
  implementation, amending the canonical sections too (§2.4.2, §7, …),
  not only §8. Design-only PRs are normal and expected.
- NO PR until the user says so. NO merge without explicit approval
  naming the exact head SHA. NO activation of an unreleased branch
  without explicit word.
- Sequential implementation PRs are never stacked: each is based on
  the previously MERGED one, so a failure stays attributable to one
  boundary (§7).
- Commit messages are long and explanatory — what the defect was,
  what was measured, what the fix contracts. Read `git log` for the
  house style. Merge commits: "Merge PR #N: title".
- Every commit ends with exactly this footer, and NO model name or
  model ID ever appears in a commit message, PR title/body, code
  comment, or any pushed artifact:

      Co-Authored-By: Claude <noreply@anthropic.com>
      Claude-Session: <this session's identifier>

- PR bodies carry the completion-evidence table: test counts per
  Python version, ruff/mypy, both gates, battery hashes, golden hash,
  and the regression-proof numbers.

## Non-negotiables (full statements: WORKING.md and the design doc)

- SINGLE AUTHORITIES: one home per concept; constants never
  respelled. Two writable sources for one fact is the defect class
  most often caught here.
- Validation REFUSES, never repairs; binds at transitions AND at
  save/load. Migration is licensed by field ABSENCE, never by
  falsiness — a present-but-malformed value refuses.
- Regression pins prove pre-fix failure: `git stash push
  extra_toppings/` → run the new tests → show the failures → `git
  stash pop` → record the count. Pins that pass both ways are
  reported as added coverage, not as proof.
- Tests drive REAL player paths (scripted consoles through the actual
  morning/service/night/scene code), never hand-built states where a
  real path exists.
- Flag-off and stand-pat surfaces are frozen: bit-identical by
  construction. The golden is NEVER regenerated except as a recorded,
  sanctioned ruling; its provenance is `ACTIVE_BASELINE` in
  `analysis/equivalence.py`.
- Bots and probes are instruments, never tuning targets.

## Verification runbook

The gates must pass on Python 3.11, 3.12 AND 3.13 (rev. 27 item 8) —
both identity gates on all three. Expected values are the
completion-evidence table of the most recent merged PR; golden
provenance is `ACTIVE_BASELINE`; gate semantics are WORKING.md's.

```
python3 -m unittest discover -s tests -q
ruff check .
mypy extra_toppings analysis
python3 -m analysis.equivalence check          # gate 1: flag-off golden
python3 -m analysis.equivalence standpat       # gate 2: paired stand-pat
shasum -a 256 analysis/golden_act1.json        # against ACTIVE_BASELINE
python3 -m analysis.experiments fork --seeds 150   # battery; also --seeds 500
```

Refactor-class PRs (identity / behaviour-equivalence character — see
§7 for which PRs carry it) additionally require all merged batteries
byte-identical at both depths (150 and 500 seeds).

Dev tooling: `pip install -e ".[dev]"`. The ruff pin (0.15.x) is
deliberate; bumping it is its own commit with whatever fixes the new
version demands.
