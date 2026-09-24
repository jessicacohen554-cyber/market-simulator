# RESULT — neiso-113: NEISO bench parts regenerated on the repaired EIA-923 builder (zero LP)

**Question.** Does any drift since the NEISO keeper `2026-09-22-hydro-5-neiso-ror`
(bundle `hydro5_neiso_ror_span`, solved at `fda9ece3`, 2020–2025) require a re-solve?

## 1. G-DRIFT (rule 29 (b)) — `fda9ece3..40f4ed7a`, solve path

| commit / hunk | verdict | reason |
|---|---|---|
| `79aa52c5` `coal_fuel_inventory_plant_grain` (miso-268; `rows.py`, `spec.py`, `coal_fuel_inventory.py`) | INERT | new flag, default off, absent from keeper recipe |
| `4263d602` `campd_dark_unit_year_windows` (soco-61; `outages.py`, `arrays.py`, `resolved_inputs.py`) | INERT | default off; `-perunitdark-` extract exists for SOCO only |
| `329e2026` `nwpp_grid_carried_wind_served` (`envelopes.py`, `demand.py`) | INERT | default off; NWPP branch only |
| `4b66bc2d` `demand_balance_screen` (`demand.py`) | INERT | default off, absent from keeper recipe (NEISO is in its BA map) |
| SOCO constants + `solve_surface_declared` entry (`3c5a8967`, `f560408f`) | INERT | SOCO-keyed only; NEISO surface entries unchanged |
| `49c898c7` ruff format | INERT | AST-identical |
| `ad42fe43` EIA-923 benchmark builder (dual-fuel oil re-attribution two-sided, runs first; pre-COD months not backfilled) | **BENCHMARK** | post-LP; moves the actuals, not the solve |

No LIVE hunk ⇒ **no re-solve**. The hydro-5 PRECOMMIT already pinned
`WARMSTART_XYEAR=0` / `P1_BASIS_SEED=0` (rule 36).

## 2. Bench refresh (miso-267 recipe, same instruments)

`check_bench_freshness --iso NEISO` before: **6 / 6 STALE**. Steps on a scratch copy of
the bundle: `_miso257_bench_rebuild.py` (dispatch pinned to committed plant keys) →
`run_calibration_full.py --rebuild-benchmark` (only `eia923` re-pointed,
`f55df779267d → b40ccb9aeb97`; eia930 / campd hashes unchanged) →
`_miso267_bench_refresh.py` corrected gate **PASS all six years** (key set + identity
fields identical) → `--write`. After: **0 STALE**. `audit_keepers --iso NEISO` PASS
(after `build_status.py --iso NEISO`); registry/payload parity OK.

## 3. Keeper re-scored (`_miso267_rescore.py`, same model side)

| | committed parts | regenerated parts |
|---|---|---|
| full span 2020–2025 | CALIBRATED, 8 / target 7 / ledgered 1 / fails 0 | **identical** |
| train 2023–2025 | CALIBRATED | **identical** |
| status flips | — | **0** (11 records move) |

| record | actual before → after (TWh) | model − actual |
|---|---|---|
| C1 2022 ST_GAS | 0.302 → 0.212 | −0.07 → +0.02 |
| C1 2024 CT_PEAKER | 0.655 → 0.591 | +0.19 → +0.26 |
| C1 2022 CT_PEAKER | 0.640 → 0.639 | +1.31 (unchanged) |
| C2 gas 2022 / 2023 / 2024 | 53.44→53.35 / 54.37→54.36 / 58.76→58.69 | all in band |
| others (CC_REGULAR 2020/22/23, CT_PEAKER 2023) | ≤ 0.002 | — |

Matches miso-267's census for NEISO (max |Δ classFull| 0.085, 2022 ST_GAS). The run
payload's `volErr` heatmap (display only, not scored) still reflects the old frames.

**Record is this doc; no bundle, no solve, no promotion question.**
