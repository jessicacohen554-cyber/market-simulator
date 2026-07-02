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

## Fossil-average CO₂ rate (residual carbon accounting)

CSV or Parquet, one row per (iso, hour). This is the **market-sim dispatch export** of
the hourly fossil-only average CO₂ intensity (tCO₂/MWh, attributional/location-based
accounting per ADR 0013), produced by `scripts/build_fossil_avg_co2_rate.py`. Residual
carbon in grid purchases is attributed at this rate; residual emissions from partial-capture
resources (gas CC+CCS) are tracked separately via per-resource intensity columns.

| column | type | required | notes |
|---|---|---|---|
| `hour` | int 0–8759 | yes | hour index within the year (local standard time) |
| `iso` | str | yes | ISO the row belongs to |
| `fossil_avg_co2_rate` | float (tCO₂/MWh) | yes | hourly fossil-only average rate (≥ 0) |

The tool reads exactly 8760 rows for the requested ISO; missing hours are a hard error.
Every ISO must cover the full `0..8759` calendar. Negative rates raise an error (the
fossil-only average is nonnegative by definition).

## Natural gas prices (gas CC+CCS fuel cost, ADR 0012)

CSV reference table, one row per ISO. Delivered natural gas prices ($/MMBtu) and basis
differential notes, matching the market simulator's forward-year fuel representation
(AEO reference Henry Hub plus ISO-specific basis — Waha discount for ERCOT, Algonquin
winter premium for NEISO, etc.). Used to compute fuel VOM for gas CC+CCS resources.

| column | type | required | notes |
|---|---|---|---|
| `iso` | str | yes | ISO identifier |
| `price_mmbtu` | float ($/MMBtu) | yes | delivered gas price |
| `basis` | str | no | basis differential description (Waha, Algonquin, etc.) |
| `notes` | str | no | vintage, source, caveats |

Example: ERCOT 2030 forward basis = Henry Hub ~$3.50/MMBtu − Waha discount ~$0.30
= ~$3.20/MMBtu delivered. `config.gas_price_mmbtu > 0` overrides this table per run.

## Capacity-factor profiles

Real per-ISO Parquet files under `data/profiles/<ISO>_<year>.parquet` (long form:
`hour` [0–8759], `resource` [solar_pv/onshore_wind/offshore_wind], `cf` [0–1]).
Built by `scripts/build_profiles.py` from the market simulator's EIA-930 data using
vendored renewable-shape logic (`src/lce_portfolio/vendored/renewable_shapes.py`);
see the script's docstring for usage and ISO-wide (system-metered) reconciliation details.
`data/profiles/` is gitignored (reproducible, disposable) — regenerate with
`scripts/build_profiles.py` after a fresh checkout.

Six-ISO mean CF (2024 vintage, the measured-shape year `scripts/build_profiles.py`
defaults to — independent of the modeled study year, see "Shape-year resolution"
below):

| ISO | solar_pv | onshore_wind | offshore_wind | offshore source |
|---|---|---|---|---|
| ERCOT | 0.270 | 0.349 | 0.450 | derived_from_onshore |
| CAISO | 0.279 | 0.300 | 0.450 | eia930_measured |
| PJM | 0.190 | 0.309 | 0.450 | eia930_measured |
| MISO | 0.220 | 0.340 | 0.450 | derived_from_onshore |
| NYISO | 0.150 | 0.258 | 0.450 | eia930_measured |
| NEISO | 0.150 | 0.299 | 0.450 | eia930_measured |

"derived_from_onshore" ISOs report no offshore-wind distribution in EIA-930, so the
offshore shape is smoothed/floored/rescaled from that ISO's own onshore shape
(`derive_offshore_wind_profile`) rather than measured — flagged in the profile's
`offshore_source` column.

If a profile file is missing, `profiles.build_cf_matrix` warns and falls back to synthetic
(deterministic diurnal solar, wind with multi-day calm spells, flat firm-clean), so runs
never hard-fail on absent data — **unless** the caller pinned `profile_shape_year`
(below), in which case a missing file is a hard error. The function signature
`build_cf_matrix(resources, iso, year, *, profiles_dir=None, required=False)` is the
single seam to swap real and synthetic shapes; nothing downstream changes.

### Shape-year resolution (`profile_shape_year`)

`PortfolioConfig.year` is the *modeled study year* (e.g. 2030) and typically has no
matching profile file — the real CF profiles are built for a specific measured
*weather year* (2024). Left to `year` alone, a real run would silently warn and fall
back to synthetic shapes, which is wrong for anything but a demo.

`PortfolioConfig.profile_shape_year: int | None = None` decouples the two:

- `None` (default) — unchanged prior behavior: `build_cf_matrix` is called with
  `year`, and a missing file warns and falls back to synthetic (the `SAMPLE` demo
  path is unaffected either way — it never touches disk).
- set (e.g. `2024`) — the profile file for *that* year is required; a missing file
  raises `FileNotFoundError` instead of substituting synthetic shapes. Wired through
  `cli.run_one_iso`, which resolves `shape_year = profile_shape_year or year` and
  passes `required=(profile_shape_year is not None)`.

`examples/run_real_sweep.py` always pins `profile_shape_year=2024` (the vintage
`scripts/build_profiles.py` builds by default) so a real sweep can never silently
run on synthetic shapes without the caller noticing.

## Reference load (ADR-ratification facility)

`data/reference/reference_load_100mw.csv` — a stylized 100 MW-average
data-center-style facility, generated by `scripts/make_reference_load.py`
(deterministic, no RNG). Long form: `hour, iso, load_mwh, facility`, the same
8760 shape (mild ±10% diurnal swing, cosine-shaped, trough at midnight/peak at
midday) replicated identically across all six ISOs.

**This is the reference case used to validate the tool's wiring for ADR
ratification — it is not customer data.** It exists so `examples/run_real_sweep.py`
has a documented, reproducible load to sweep against before any real facility
load is supplied; a real engagement replaces it with an actual facility load file
in the same schema (see "Load intake" above).

`data/reference/` is gitignored — the CSV is ~2 MB (52,560 rows: 6 ISOs × 8760
hours), over the repo's small-file commit guideline, so it is regenerated on
demand rather than committed (`examples/run_real_sweep.py` calls the generator
automatically if the file is absent; `scripts/make_reference_load.py` reproduces
it byte-for-byte on its own).

## Real-run entry point

`examples/run_real_sweep.py --iso <ISO> [--lmp <file>] [--year 2030]` wires the
reference load, the real per-ISO CF profiles (pinned to `profile_shape_year=2024`,
required — see above), and a BAU LMP file through the normal pipeline
(`cli.run_one_iso`). LMP resolution, in order: explicit `--lmp` > newest real
(non-`_dummy`) `bau_lmp_*.csv` in `data/inputs/` > newest existing `*_dummy.csv` >
generated on the spot via the market-sim side's `scripts/export_lce_lmp.py --dummy`
(subprocess; this tool still never imports `market_sim`). Any synthetic result
prints a loud `SYNTHETIC LMP` banner and is recorded in the run's
`<iso>_run_metadata.json` under `lmp_source`. The market simulator's BAU forecast
is on hold by stakeholder decision (`PLAN.md` §10) — this entry point never
triggers a solve; it only ever reads an existing LMP file or the dummy stub.

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
