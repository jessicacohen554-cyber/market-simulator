# RESULT — miso-279: ST_GAS rows for gas-steam bins the tranche window never measured. Zero status flips; ST_GAS closer every year; PROMOTED.

```
LANE     : miso-279 (owner pick 2026-09-27, lever card "A: add missing gas-steam rows (Recommended)")
PREREG   : docs/records/miso/PRECOMMIT-miso279-stgas-span-coverage-2026-09-27.md (pin 47d3f872)
PHASE 0  : docs/records/miso/FINDING-miso279-stgas-span-coverage-2026-09-27.md
OUTGOING : 2026-09-27-miso-278-fuelsplit (miso278_span) — pruned (rule 35)
KEEPER   : 2026-09-27-miso-279-stcov (results/calibration/miso279_span, 2019-2025)
DELTA    : campd_st_gas_span_coverage = true (sub-gate of the keeper's campd_unit_fuel_split). DOF +0
CONTROL  : keeper bundle (G-DRIFT 257d3c6f..47d3f872: all non-delta hunks INERT; rule 29(b) form 4)
VERDICT  : full span NOT-YET (fuelmix, price_mean, price_shape — the keeper's same three); train 2023-2025 CALIBRATED
```

## 1. Legs

Seven single-year shards pinned to `47d3f872`. Every leg verified in the parent: recipe = keeper + exactly
`campd_st_gas_span_coverage`; the solve read the four pinned `-fuelsplit-stcov-` companions. 17 files each including
`dispatch/<Y>_P1.parquet`. All shard sessions archived. The first 2022 shard idled after backgrounding its solve and
pushed ~2 h late; a relaunch started meanwhile was stopped and archived unused.

| year | leg commit (provenance) | ST_GAS Δ TWh | LW internal price keeper → arm $/MWh |
|---|---|---:|---|
| 2019 | `94b6c493` | +0.198 | 27.929 → 27.914 |
| 2020 | `a2aac701` | +0.284 | 24.585 → 24.562 |
| 2021 | `e53e4fb4` | +0.246 | 37.144 → 37.080 |
| 2022 | `a0d0bd50` | +0.213 | 58.507 → 58.440 |
| 2023 | `1afd0925` | +0.165 | 32.716 → 32.698 |
| 2024 | `8e10558d` | +0.020 | 30.759 → 30.757 |
| 2025 | `0ba3d1cc` | +0.010 | 41.633 → 41.630 |

Realized ST_GAS energy is ~25–35 % of the floor footprint in 2019–2020 (+0.84 / +0.79 TWh of floor): the new floors
displace the plants' own above-floor dispatch as well as other classes.

## 2. Gates (live scorer) — zero criterion-year status flips

| criterion-year | keeper miso-278 | miso-279 |
|---|---|---|
| **C1 ST_GAS 2019** (band ±8.00) | −8.203 TWh FAIL | **−8.003 TWh FAIL** |
| C1 ST_GAS 2020 / 2021 / 2022 / 2023 / 2024 | −6.62 / −5.49 / −5.36 / −0.44 / −1.94 | −6.32 / −5.23 / −5.14 / −0.28 / −1.94 |
| C3a 2022 | −15.7 % FAIL | −15.8 % FAIL |
| C3b 2021 | 0.254 FAIL | 0.254 FAIL |
| C8 ST_GAS forced share 2019 / 2020 / 2023 | 21.9 / 17.0 / 13.0 % | 23.9 / 18.6 / 13.6 % (cap 30 %) |
| legitimacy D-1/D-2/D-4 FAIL rows | 8 | 8 (same set) |
| determination | NOT-YET (3) | NOT-YET (3) |

C1 ST_GAS 2019 misses its band by 3 GWh. That is reported at full magnitude and is not a reason to adjust anything
(rule 1): the lever was chosen and built on source coverage, before the solve.

## 3. Reading

- A correct source-coverage repair (rules 14/23): eight gas-steam bins that had no measured row now carry one derived
  from their own CEMS. ST_GAS moves the right way in every scored year; nothing regresses; no legitimacy finding appears.
- As sized in phase 0, it reaches a small part of the 2019 gap. What remains is (i) floored South steam dispatched below
  actual on economics in a $2.5-gas year, and (ii) MISO-South VLR commitment the model does not represent
  (`scuc_load_pocket_commitment` = `·`; needs MISO's published VLR record, a data ask).
- Teche 1400's pooled window (online_frac 0.327) floors ~0.27 TWh in 2023 against 0.18 TWh CEMS; the D-4 conduct rider
  skips 1400 (benchmark CT-only CEMS flag), so it is not scored as a finding. Stated, not hidden.

## 4. Where the bytes are

The composite `miso279_span` (slim bundle incl. `hourly/`, attestation with a `miso279` block, regenerated diagnostics,
stamped partition passing `--check`), its registry sidecar and payload are on `main` with this lane's PR. Per-year leg
dirs are parent-local and gitignored; the SHAs above are provenance only (rule 33(d)). A re-solve of any leg costs
~15–35 min (2022 ~100 min).

## 5. Promotion

Promoted on the owner's ruling ("Promote (Recommended)"). Year set (rule 35(b)): outgoing {2019–2025}, incoming
{2019–2025}, covered. `audit_keepers --iso MISO` passes after the prune.
