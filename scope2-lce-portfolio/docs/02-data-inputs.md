# 02 — Data Inputs (intake contract)

Three inputs: a **load** file, an **LMP** file, and the **resource-cost** table.
All hours are integer indices `0…8759` (a single representative non-leap year).

## Load intake

CSV or Parquet, long form. Facility-level and multi-ISO are allowed; the tool
aggregates to one hourly vector per ISO (`intake.aggregate_by_hour_iso`).

| column | type | required | notes |
|---|---|---|---|
| `hour` | int 0–8759 | yes | hour index within the year |
| `iso` | str | yes | ISO the row belongs to |
| `load_mwh` | float | yes | consumption in that hour |
| `facility` | str | no | summed away by aggregation |

Load growth: `config.load_growth_rate` and `load_growth_years` apply a compound
multiplier `(1+rate)^years` (shape-preserving). Shape-shifting growth is a PS-07
decision.

## LMP (BAU wholesale prices)

CSV or Parquet, one row per (iso, hour). This is the **market-sim BAU output** for the
modeled year, selected at forecast-year vintage (ADR 0011); the tool does not apply price
escalation.

| column | type | required | notes |
|---|---|---|---|
| `hour` | int 0–8759 | yes | hour index within the year (local standard time) |
| `iso` | str | yes | ISO the row belongs to |
| `lmp` | float ($/MWh) | yes | wholesale price |

The tool reads exactly 8760 rows for the requested ISO; missing hours are a hard error,
not a zero-fill. Every ISO must cover the full `0..8759` calendar.

## Capacity-factor profiles

Real per-ISO Parquet files under `data/profiles/<ISO>_<year>.parquet` (long form:
`hour` [0–8759], `resource` [solar_pv/onshore_wind/offshore_wind], `cf` [0–1]).
Built by `scripts/build_profiles.py` from the market simulator's EIA-930 data using
vendored renewable-shape logic (`src/lce_portfolio/vendored/renewable_shapes.py`);
see the script's docstring for usage and ISO-wide (system-metered) reconciliation details.

If a profile file is missing, `profiles.build_cf_matrix` warns and falls back to synthetic
(deterministic diurnal solar, wind with multi-day calm spells, flat firm-clean), so runs
never hard-fail on absent data. The function signature `build_cf_matrix(resources, iso, year)`
is the single seam to swap real and synthetic shapes; nothing downstream changes.

## Resource-cost table

`data/lcoe/resource_costs.csv` — one row per resource. Three **cost bases** (ADRs 0004/0006/0008):

**capex_fixed** — generation and fixed-duration Li-ion storage. Overnight capex ($/kW) from
NREL ATB 2024 is annualized with a capital-recovery factor (CRF) and added to FOM to give
`fixed_mwyr` ($/MW-yr).

| column | meaning |
|---|---|
| `resource` | unique name |
| `category` | `generation` or `storage` |
| `cost_basis` | `capex_fixed` |
| `capex_kw_low/mid/high` | overnight capex ($/kW) at low/mid/high ATB variant |
| `fom_kw_yr` | fixed O&M ($/kW-yr) |
| `cost_low/mid/high` | annualized fixed cost ($/MW-yr) = CRF × capex + fom (computed) |
| `cf_assumed` | placeholder CF for annualization (generation) |
| `vom` | $/MWh variable O&M |
| `duration_h`, `rte` | fixed storage duration (h) and round-trip efficiency |
| `life_yr` | asset life (years) for CRF calculation |
| `cap_max_default_mw` | default build cap |
| `active_minimal` | `1` = included in the minimal example |

**split_storage** — LDES and hydrogen. Power ($/kW) and energy ($/kWh) capex are annualized
separately so the LP can size power and energy independently within `[duration_min_h, duration_max_h]`.

| column | meaning |
|---|---|
| `capex_power_kw_low/mid/high` | electrolyzer/turbine/PCS capex ($/kW) |
| `capex_energy_kwh_low/mid/high` | storage vessel/tank capex ($/kWh) |
| `fom_power_kw_yr`, `fom_energy_kwh_yr` | separate O&M ($/kW-yr, $/kWh-yr) |
| `cost_low/mid/high` | (reserved; computed per solve) |
| `duration_min_h`, `duration_max_h` | bounds (hours) |
| `vom` | $/MWh variable O&M |
| `rte` | round-trip efficiency |

**ppa_mwh** — existing nuclear/hydro. Going-forward, per-MWh PPA cost plus a clean-attribute
premium. Fixed cost is zero; the effective VOM is `cost + eac_premium_mwh`.

| column | meaning |
|---|---|
| `cost_low/mid/high` | going-forward energy cost ($/MWh) |
| `eac_premium_mwh` | clean-attribute premium ($/MWh) |
| `von` | (set to cost + eac_premium for dispatch) |
| `cap_min/max_mw` | contractable fleet share |

All low/mid/high sensitivities use NREL ATB 2024 Advanced/Moderate/Conservative variants.
The CRF is `r(1+r)^n / ((1+r)^n - 1)` with `r = config.discount_rate` and `n = life_yr`.

## Outputs

Written by `outputs.write_outputs` under `--out-dir`:
- `<iso>_frontier.parquet` — one row per setpoint: `matching_pct`, `premium_per_mwh`,
  `net_cost`, `bau_cost`, `shadow_price`, `status`, `residual_co2_tons`, `total_load_mwh`,
  `grid_buy_mwh`, `surplus_mwh`, `surplus_revenue`, `capital_cost` (ADR 0007).
- `<iso>_build_mix.parquet` — long form: `setpoint`, `resource`, `build_mw`, `build_energy_mwh`
  (energy columns present only for split-storage resources).
