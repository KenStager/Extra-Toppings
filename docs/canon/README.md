# Design canon

This directory preserves the founding documents of Extra Toppings,
verbatim, as the project's source of truth:

- [`00-original-pitch.md`](00-original-pitch.md) — the original design
  pitch: the three feelings (temptation, ownership, paranoia), the
  Dope Wars × Fast Food Tycoon mechanic mapping, the day structure, the
  clean/dirty money doctrine, employees-as-characters, rivals, raids,
  Heat vs. the Case, the three-act progression, the endgames, and the
  first-playable-version checklist.
- [`01-north-star-brief.md`](01-north-star-brief.md) — the follow-up
  directive: the north-star experience, the central question ("How much
  of my real pizza business am I willing to risk for this opportunity?"),
  the **ten nonnegotiable design invariants**, the prototype scope
  discipline, and the technical expectations.

The texts are canon and are not edited. Design work cites them; when a
change conflicts with them, either the change is wrong or the deviation is
argued explicitly and recorded here.

## How canon binds the codebase

The invariant list in the north-star brief is the standing acceptance bar.
Current enforcement:

| Canon requirement | Where it lives now |
| --- | --- |
| Shared route capacity (legit + covert) | `routes.plan_route` wagon slots; `TestSharedCapacity`, `TestSharedKitchenCapacity` |
| Shop is a functional business, not a wash-front | Demand pipeline (`shop.roll_demand`/`recompute_demand`), quality-locked pantry, cover drawn only from real delivery orders; `TestRealCover`, `TestDemandPolicyIntegrity`, `TestQualityIdentity` |
| Legit success ⇄ criminal consequence coupling | reputation → demand → cover → route safety chain; raid damage throttles the kitchen and therefore cover |
| Dirty money never silently becomes clean | `TestMoneySeparation`, `TestChunkedLaundering` |
| Laundering ceiling from actual performance | `legit_revenue_today` + cumulative nightly allowance; `TestLaundering`, `TestCompleteLegitLedger` |
| Telegraphed rival violence | 2-night raid warnings; `TestTelegraphedRaids` |
| Failed raids are defined and recoverable | `TestRecoverableFailure` |
| Determinism per seed + decisions; save/reload fidelity | `rng.Streams` (action-independent world channels), save v2; `TestDeterminism`, `TestSaveCompleteness` |
| Raids priced by the simulation, not free combat | alertness, pattern evidence, carry/storage limits, consumable ledger; `tests/test_raid_pricing.py` |
| Dual-use upgrades | `data.UPGRADES` (every entry states both edges) |

## Recorded deviations from canon (argued, accepted in review)

- **Slice size.** The north-star brief asked for a 7-day graybox with three
  districts, three commodities and one rival. The implemented slice
  follows the original pitch's larger checklist instead (30 days, four
  districts, four goods, two rivals, eight employees) — it was built first
  and accepted through review as the working baseline. The brief's scope
  discipline ("do not solve lack of depth by adding content") still
  governs all new work.
- **Loan shark takes dirty cash.** Canon assigns debt to clean-money uses
  implicitly; simulation proved the game unwinnable when Carmine required
  clean bills, and a loan shark preferring unmarked cash is truer to
  genre. The laundering ceiling still gates payroll, rent and upgrades.
- **First raid larger than briefed.** Three objectives and room-by-room
  play shipped in the slice rather than the single-objective minimal raid.
  The committed architectural direction — the player's own restaurant
  layout becoming the tactical map — is preserved but not yet implemented.
- **Debug panel** from the technical expectations is not yet implemented;
  observability currently comes from `--verbose` transcripts,
  `analysis/experiments.py`, and the versioned findings log.

Everything measured against this canon — four rounds of studies, defects
found and fixed, claims retracted — is chronicled in
[`docs/FINDINGS.md`](../FINDINGS.md).
