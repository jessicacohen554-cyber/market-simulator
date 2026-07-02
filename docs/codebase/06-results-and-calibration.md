# 6. Results, Caching & Calibration

Source: `src/market_sim/results/`. Covers result persistence (Parquet caching and
serialization), derived outputs (emissions, plant financials, annual summaries),
and the backcast calibration diagnostics.

## 6.1 Parquet caching (`cache.py`)

One Parquet per scenario-year under `results/{iso}/{cache_key}/`, where
`cache_key = ScenarioConfig.cache_key()` is a deterministic hash of the config.

| File | Contents |
|------|----------|
| `year_{year}.parquet` | final dispatch (P2 if commitment enabled, else P1) |
| `year_{year}_p1.parquet` | the pre-commitment P1 result (only when commitment runs) |
| `config.yaml` | the full scenario config, written once |

Key functions: `get_cache_path(...)`, `is_cached(...)` (the check-before-run
gate), `save_result(...)`, `load_result(...)`, `load_fleet_context(...)`. The
runner calls `is_cached()` before solving and loads the cached result if present,
skipping the LP entirely.

## 6.2 Result serialization (`outputs.py`)

Extends `DispatchResult` with Parquet I/O. Hourly `(n_entity, T)` arrays are stored
as list-valued columns (transposed to `(T,)` of `list[float]`): `dispatch, wind,
solar, slack, dump, price`, plus optional `storage_charge/discharge/soc, flows,
emissions`. Scalars and dimensions live in schema metadata
(`market_sim` JSON: objective, status, T, n_gen, n_zones, rps_shadow_price, …).

`FleetContext` (frozen dataclass) is the per-generator/resource metadata needed to
aggregate results without re-deriving the fleet: `fuel_types, pmax_mw,
emission_rate, heat_rates, zones, unit_ids, plant_groups`, plus resource scalars
(`wind_cap_mw, solar_cap_mw, *_potential_mwh, storage_energy_cap_mwh`). Built at
solve time via `FleetContext.from_arrays(...)` and stored in the
`market_sim_fleet` metadata key. `to_parquet` / `from_parquet` round-trip the
result (reconstruction uses zero-copy numpy buffers).

## 6.3 Emissions (`emissions.py`)

- `compute_emissions(dispatch, emission_rates)` → `(T,)` hourly CO2 =
  `(dispatch · rates[:,None]).sum(axis=0)`.
- `compute_nox(dispatch, nox_rates)` → same for NOx.
- `compute_must_run_emissions(...)` reconstructs CHP behind-the-meter generation
  (removed from the LP before solve). Backcast: `total (EIA-923 per class) − grid
  dispatched (LP)`. Forecast: `nameplate × pct_mr × 8760 × must_run_cf`. Keying off
  per-class totals avoids over-attributing one class's generation to another at
  multi-class plants.

## 6.4 Plant financials (`plant_financials.py`)

Disaggregates bin-level LP dispatch to individual EIA plants and computes per-plant
P&L using each plant's **own** heat rate (so a less-efficient plant in the same
bin earns lower margin). Capital is sunk — only going-forward O&M + variable costs.

- `build_plant_bin_map(...)` → `PlantBinAssignment` per generator.
- `disaggregate_dispatch(...)` → per-plant-hour dispatch (pro-rata by capacity, or
  merit-order most-efficient-first).
- `compute_plant_hourly_financials(...)` → revenue, fuel/VOM/carbon/NOx costs,
  gross margin, emissions per plant-hour.
- `compute_plant_annual_summary(...)` → CF, spark spread, FOM, net operating
  income, discounted NPV.
- `compute_company_summary(...)` → ownership-scaled rollup to parent companies
  (scales money/MWh by `percent_owned`).
- `compute_trajectory_npv(...)` → multi-year NPV / cumulative generation / CO2.

## 6.5 Annual export (`export.py`)

`export_scenario_json(cache_key, iso, output_dir)` loads all years' cached
Parquets + fleet contexts, aggregates each via `_summarize_year` into a compact
JSON (< 2 MB). Per-year summary: `generation_twh` (by fuel), `emissions_mt`,
`avg_price`, `peak_price`, `curtailment_twh`, `capacity_gw` (by fuel),
`storage_cycles`. `real_to_nominal(...)` inflates real-2026 dollars to nominal by
year.

## 6.6 Calibration diagnostics (`calibration.py`)

Backcast validation against published benchmarks, four ordered diagnostics
(diagnostic 1's failure usually explains 2–4):

| # | Diagnostic | Function | Benchmark | Tolerance |
|---|-----------|----------|-----------|-----------|
| 1 | generation mix | `check_generation_mix` | `{fuel: TWh}` | ±5% per fuel |
| 2 | price duration curve | `check_price_duration_curve` | hourly prices (P10/P50/P90/mean) | ±5% |
| 3 | average price | (derived) | `$/MWh` | ±5% |
| 4 | capacity factors | `check_cf_band_occupancy` | per-fuel CF | ±5% |

Authority sources: **EIA-923** (Schedule-5 net generation) for dispatchable
classes; **EIA-930** (hourly grid generation) for variable renewables — except
NYISO solar, which uses EIA-923 because behind-the-meter solar is invisible to grid
telemetry. `run_calibration_check(...)` loads a cached year, runs all four, and
returns a `CalibrationReport` (`DiagnosticResult` per check; passes iff no FAIL,
skips allowed).

## 6.7 The dashboard (project workflow)

Per project rules, every completed backcast run — keeper *or* rejected probe — is
registered on the deployable results dashboard in the same session it is produced.
The committed deliverable is the per-run bundle under
`results/calibration/<name>/` plus the dashboard sidecar files
(`frontend/data/backcast/registry/<id>.json`, `runs/<id>.js`, changed `bench/`).
The dashboard itself is the codebase-site pages —
`docs/codebase-site/backcast-runs.html` (run explorer) and
`docs/codebase-site/calibration-status.html` (all-ISO keeper summary); their
data (`manifest.js` etc.) is rebuilt at deploy. Use the `calibration-report`
skill / `scripts/dashboard_add_run.py` then `build_manifest.py`. (See
`CLAUDE.md` rules #13–#14.)
</content>
