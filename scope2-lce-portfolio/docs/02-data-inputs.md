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

CSV or Parquet, one row per (iso, hour). This is the **market-sim BAU output**;
export it to this schema (the export step / vintage selection is PS-08).

| column | type | required |
|---|---|---|
| `hour` | int 0–8759 | yes |
| `iso` | str | yes |
| `lmp` | float ($/MWh) | yes |

The tool reads exactly 8760 rows for the requested ISO (`cli.load_lmp`).

## Capacity-factor profiles

Currently synthetic (`profiles.build_cf_matrix`) — deterministic diurnal solar,
wind with multi-day calm spells, flat firm-clean. Real per-ISO/zone shapes are
wired later by copying the market-sim renewable-shape logic into
`src/lce_portfolio/vendored/` (PP-03). The function signature
`build_cf_matrix(resources, iso, year)` is the single seam to swap; nothing
downstream changes.

## Resource-cost table

`data/lcoe/resource_costs.csv` — one row per resource.

| column | meaning |
|---|---|
| `resource` | unique name |
| `category` | `generation` or `storage` |
| `cost_basis` | `lcoe_mwh` (generation) or `fixed_mwyr` (storage) |
| `cost_low/mid/high` | cost at the three sensitivities |
| `cf_assumed` | placeholder CF used to annualize LCOE (generation) |
| `vom` | $/MWh variable O&M |
| `duration_h`, `rte` | storage energy/power hours and round-trip efficiency |
| `cap_max_default_mw` | default build cap (override per-run in config) |
| `active_minimal` | `1` = included in the minimal example |
| `notes` | provenance / caveats |

Cost conversion (`resources.load_resource_arrays`):
- `lcoe_mwh`: `fixed_mwyr = lcoe · cf_assumed · 8760` (pay-for-capacity; a unit
  running at its assumed CF recovers exactly its LCOE).
- `fixed_mwyr`: used directly (all-in annualized $/MW-yr at the listed duration).

The seed numbers are ATB-ballpark and **must be refined** — that's PS-01 (generation)
and PS-03 (storage).

## Outputs

Written by `outputs.write_outputs` under `--out-dir`:
- `<iso>_frontier.parquet` — one row per setpoint: `matching_pct`,
  `premium_per_mwh`, `net_cost`, `bau_cost`, `shadow_price`, `status`.
- `<iso>_build_mix.parquet` — long form: `setpoint`, `resource`, `build_mw`.
