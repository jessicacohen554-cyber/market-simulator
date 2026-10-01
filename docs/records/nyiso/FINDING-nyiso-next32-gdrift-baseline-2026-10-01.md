# FINDING — NYISO-NEXT-32 G-DRIFT baseline: HEAD is INERT on the keeper's backcast path (zero LP)

**Lane:** NYISO-NEXT-32 · **Date:** 2026-10-01 · **LP solves:** 0
**Keeper:** `2026-10-01-nyisonext21-astoria-hr-span` (+ folded 2021), `git_sha` `fdc41f36`
**HEAD audited:** `origin/main` `7a65272a` (165 commits after the keeper sha)
**Probe:** `scripts/probes/nyisonext32_gdrift_ast.py` · **JSON:** `results/phase0/nyiso/_nyisonext32_gdrift_ast.json`

## Result

No hunk between `fdc41f36` and `7a65272a` changes the NYISO keeper's backcast solve.
A lever armed on this keeper needs no control solve (rule 29 (b)); the committed
`nyisonext21_*` bundles stay the control.

## Instruments

| Check | Keeper `fdc41f36` | HEAD `7a65272a` | Verdict |
|---|---|---|---|
| `surface_rows("NYISO")` | 228 rows, `50e8e6cf8632` | 228 rows, `50e8e6cf8632` | identical by value |
| `ScenarioConfig` defaults | 939 fields | 946 fields | 7 added, all default `False`; none named in the keeper's `run_config.json`. The 6 "changed" are repo-root paths and frozenset repr order (artefacts) |
| `constants.py` by value | 339 | 340 | added `ERCOT_LCAP_WINDOWS_BY_YEAR`; `ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR` changed (ERCOT-only); `CAMPD_BINNING_ISOS`, `RGGI_MEMBER_STATES_BY_YEAR` are set-order artefacts |
| NYISO `default_scenario_overrides` | — | — | identical |
| Numeric stack | highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3 (bundle meta) | same (pins moved from `>=` to `==` at the resolved versions) | identical |

AST classification (docstrings stripped, then string literals blanked) of the 154
changed `.py` files under `src/`, `scripts/lib/`, `scripts/run_calibration*.py`:

| Class | Files | Verdict |
|---|---|---|
| identical AST | 121 | INERT: comments, docstrings, formatting, `docs/` path moves |
| strings only | 2 | INERT: `reserve_requirements.py`, `import_nodes.py` doc-path strings in messages |
| added | 6 | INERT: not imported on the NYISO path (`spp_mmu_unavailability`, `unit_marginal` sidecar writer, CAISO transfer limits, lane/census helpers) |
| code | 25 | INERT-with-reason, below |

## The 25 code-level files

| Hunk family | Files | Why INERT for the keeper |
|---|---|---|
| NYISO NEXT-23/25/26 levers | `fuel/hubs.py`, `fuel/basis/nyiso.py`, `interchange/nyiso.py`, `runner.py`, `run_calibration.py`, `scenarios.py`, `solve_surface_declared.py` | gated on `nyiso_gas_flow_date` / `nyiso_gas_daily_print_level` / `nyiso_li_tsl_all_hours`, all default `False`, absent from the keeper recipe; the off branch is byte-identical |
| ERCOT effective SWCAP / published ORDC | `lp/__init__.py`, `lp/costs.py`, `lp/model.py`, `pipeline/kwargs.py`, `pipeline/solve.py`, `reserves/spec.py`, `results/scarcity.py`, `constants.py`, `run_calibration*.py` | gated on `iso == "ERCOT"` and `ercot_swcap_effective_hourly` / `ercot_ordc_published_curve`; new LP args default `None` → static broadcast; `obd_half_shift` default `False` |
| SPP MMU offer unavailability | `fleet/arrays.py`, `paths.py` | `_spp_mmu_armed` requires `iso == "SPP"` |
| PJM CC conduct window | `fleet/arrays.py`, `campd_bins.py` | `cc_mustrun_conduct_window` default `False` |
| NWPP per-unit fuel-split deletion | `campd_bins.py` | keeper arms `campd_per_unit_attribution` but `campd_unit_fuel_split: false`; that branch returns the same value as before (only the armed-together case now raises) |
| SOCO FERC-714 neighbour lambda | `ferc714.py` | SOCO-only loader |
| Post-solve / tooling | `run_calibration_full.py` (`unit_marginal` sidecar, ERCOT adder trim), `bench_stamp.py`, `forecast_parity_registry.py`, `topscoped_encode.py`, `transfer_interface_limits/` | write-side or non-NYISO; no LP input |

## Not covered

LP construction is a reading of the hunks above, not a rebuild: no `fleet_only`
array-identity rebuild was run (it needs `data/clean`). The surface-hash identity
plus every gate reading `False` on the keeper recipe makes that redundant here.
Re-run the probe at the solve sha of any future arm (`--base fdc41f36 --head <sha>`).

## Lane state

Queue owner-blocked (cards 1–6 unruled). No lever proposed; no PRECOMMIT.

## Delta, NYISO-NEXT-33: `7a65272a` → `9209f610` (zero LP)

Same probe (`--base 7a65272a --head 9209f610`). Two commits touch the backcast path:
`d3e16f23` (R-CAISO-31) and `2eac46ec` (soco-98).

| Class | Files | Why INERT for the keeper |
|---|---|---|
| added | `scripts/lib/storage_soc_bounds/{__init__,caiso}.py` | imported only by `scripts/data/curate_storage_soc_bounds.py` (CAISO data intake); not on any solve path |
| code | `src/market_sim/model/interchange/spec.py` (`INTERFACE_NEIGHBORS`) | adds/edits `hr_by_year` on the six `SOCO_*` neighbour entries only; `INTERFACE_NEIGHBORS["NYISO"]` repr hash `dc937b598926` at both shas |

`surface_rows("NYISO")`: 228 rows, hash `50e8e6cf8632` at both shas (unchanged
from the `fdc41f36` baseline). HEAD remains INERT on the keeper's backcast path.
