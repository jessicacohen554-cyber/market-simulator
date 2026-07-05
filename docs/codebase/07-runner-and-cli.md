# 7. Runner, CLI & Orchestration

Source: `src/market_sim/runner.py`, `ensemble.py`, `__main__.py`, and
`scripts/run_calibration_full.py`. This page documents how a run is invoked and
how `run_scenario_iso` drives the year loop end to end.

## 7.1 Entry points

| Invocation | Dispatches to |
|------------|---------------|
| `python -m market_sim …` | `__main__.py` → `runner.main()` |
| `market-sim …` (console script, declared in `pyproject.toml`) | `runner.main()` |
| `uv run market-sim …` | same, in the locked uv environment |
| `./run-simulator.sh` | bootstraps `.venv`, launches `tools/launcher.py` (web UI at `http://127.0.0.1:8765/`) |
| `python scripts/run_calibration_full.py …` | the backcast calibration harness |

## 7.2 The `market-sim` CLI

`_build_parser()` (runner.py:1056) defines three subcommands; `main()` (line 1119)
dispatches them.

### `run` — single scenario

```bash
market-sim run --config <scenario.yaml> [--iso ERCOT]
```

Loads a `ScenarioConfig` from YAML, runs every simulation year
(`START_YEAR=2026` → `END_YEAR=2050`) for one ISO via `run_scenario_iso(config,
iso)`, and returns the deterministic `cache_key`. `--iso` overrides the config's
own ISO.

### `sweep` — parameter sweep

```bash
market-sim sweep --sweep <sweep.yaml> [--workers N]
```

Expands a `SweepDefinition` into many `(config, iso)` pairs and runs them across
worker processes (default `cpu_count − 1`). Separate invocations have no
dependency, so this is the parallelism unit — *within* each invocation, years
still run sequentially.

### `ensemble` — weather-year distribution

```bash
market-sim ensemble --config <scenario.yaml> [--iso ISO] \
    [--weather-years 2023 2024 2025] [--workers N] [--out dist.json]
```

Runs the same forecast once per weather draw (varying only `weather_year`,
defaulting to the ISO's verified pool — `weather_year_pool(iso)`; ERCOT/NEISO
get `(2019, 2020, 2021, 2023, 2024, 2025)`, NYISO gets `(2021, 2023, 2024,
2025)`, CAISO/PJM/MISO keep the `WEATHER_YEAR_POOL = (2023, 2024, 2025)`
fallback — see `docs/weather-pool-coverage-2026-07.md`), then reports the
cross-draw distribution of each metric. Implemented in `ensemble.py`:
`weather_ensemble_configs` (one config per year, all else fixed) →
`run_weather_ensemble` (parallel, each member caches under its own key) →
`summarize_ensemble` (mean/std/min/p10/p50/p90/max per year per metric) →
`export_ensemble_json`.

## 7.3 `run_scenario_iso` — the orchestrator

`run_scenario_iso(config, iso) -> str` (runner.py:137) is the core loop. Returns
the `cache_key`.

**One-time setup** (before the year loop):
- `get_iso_config(iso)` → topology; extend with import/export generators if the
  ISO has a priced seam (CAISO/PJM).
- Load weather-fixed inputs once: `base_demand` (zonal hourly load),
  `wind_cf/wind_cap/solar_cf/solar_cap`, transmission incidence matrix + TTC +
  interface groups.
- Load CAMPD bins (if `use_campd_bins`), planned additions (forecast only),
  initialize the global `CumulativeDeployment`.

**Per-year loop** (`for year in range(START_YEAR, END_YEAR+1)`, sequential):

1. **Fleet** — year 1 builds the base fleet (CAMPD bins → `bins_to_fleet`, or
   aggregate EIA-860); years 2+ call `evolve_fleet(...)` and fold renewable
   additions into the zonal `wind_cap`/`solar_cap` pools, then advance cumulative
   deployment.
2. **Demand** — `_scale_demand(base_demand, config, year)` compounds growth from
   `config.weather_year` to the target year.
3. **Dispatch fleet** — split coal tranches, apply plant emission rates, resolve
   the historic outage overlay, `generators_to_fleet_arrays(...)` → `FleetArrays`,
   inject offshore-wind profiles.
4. **Marginal cost** — resolve fuel prices, coal supply-curve repricing,
   `assemble_mc(...)`. Computed even on cached years (feeds next year's retirement
   screen).
5. **Cache check** — `is_cached(...)` → `load_result(...)` and skip the solve.
6. **P0** — solve at base MC (discover run lengths).
7. **P1** — `compute_monthly_markup`, `mc_bid = mc_base + markup`, apply EAC/PTC,
   RPS constraint, optional reserve co-optimization; warm-start from P0. **Sets
   prices.**
8. **P2** — optional commitment screen + re-solve (saves P1 as `_p1`).
9. **Post-solve** — CHP must-run reconstruction (CAMPD bins), ORDC scarcity
   overlay (ERCOT energy-only, skipped if co-opt on); add the scarcity adder to
   `econ_prices` for next year's economics only.
10. **Persist & feed forward** — `save_result(...)`; build `prior_results`
    (prices, RPS shadow, peak demand, dispatch, capacities, cumulative
    deployment) for the next `evolve_fleet`.

## 7.4 Calibration harness (`scripts/run_calibration_full.py`)

The backcast entry point used to produce dashboard runs.

```bash
python scripts/run_calibration_full.py --iso ERCOT --year 2023 2024 2025 [--commitment]
```

Selected flags (`argparse` at line 4201):

| Flag | Default | Meaning |
|------|---------|---------|
| `--iso` | `ERCOT` | ERCOT runs the full plant-level diagnostic; other ISOs run energy-only |
| `--year` | `2023 2024` | one or more backcast years (multi-year ISOs solve all years in one bundle) |
| `--hours` | 8760 | dispatch horizon (smaller for smoke tests) |
| `--commitment` | off | run the P2 commitment pass after P1; both persisted |
| `--no-coal-p2` | off | pin coal to P1 dispatch in P2 |
| `--coal-prb-sigmoid` / `--no-coal-prb-sigmoid` | on | gas-keyed PRB passthrough sigmoid |
| `--outage-source` | `historic` | `historic` overlays measured ERCOT outages; `statistical` uses WEFOR/POF |

It solves each year sequentially, writes a timestamped bundle under
`results/calibration/<iso>/<timestamp>/` (per-generator hourly dispatch, system
prices, EIA-930/EIA-923 benchmarks, `meta.json`), and computes the comparison
report. Per the project's calibration rules, multi-year ISOs (CAISO/PJM/NEISO/
NYISO) must solve **all** scorable years in a single `--year` invocation — a
single-year keeper is not allowed.

## 7.5 Year and horizon constants

From `config/constants.py`: `START_YEAR = 2026`, `END_YEAR = 2050`,
`HOURS_PER_YEAR = 8760`, `WEATHER_YEAR_POOL = (2023, 2024, 2025)` (cross-ISO
fallback) and `WEATHER_YEAR_POOL_BY_ISO` / `weather_year_pool(iso)` (per-ISO
verified pool, widened 2026-07 — see `docs/weather-pool-coverage-2026-07.md`).
The model always solves the full non-leap 8760-hour calendar (Feb 29 dropped).

## 7.6 Example invocations

```bash
# Forecast a single scenario
market-sim run --config scenarios/ercot_base.yaml

# Run a generic scenario against a different ISO
market-sim run --config scenarios/generic.yaml --iso CAISO

# Parameter sweep across 8 workers
market-sim sweep --sweep sweeps/capacity_sensitivity.yaml --workers 8

# Weather-year ensemble with a distribution JSON
market-sim ensemble --config scenarios/ercot_base.yaml \
    --weather-years 2023 2024 2025 --out results/ensemble_dist.json

# Backcast all scorable years for PJM (energy-only)
python scripts/run_calibration_full.py --iso PJM --year 2023 2024 2025

# Concurrent independent backcasts (separate --out-dir, no dependency)
python scripts/run_calibration_full.py --iso PJM   --year 2023 2024 2025 &
python scripts/run_calibration_full.py --iso CAISO --year 2023 2024 2025 &
```
</content>
