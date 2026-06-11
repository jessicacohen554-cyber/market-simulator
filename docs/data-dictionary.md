# Data Dictionary

This document describes the on-disk schema of a cached simulation result.

Each cached scenario-year is one Parquet file at
`results/{iso}/{cache_key}/year_{year}.parquet`, written by
`market_sim.results.outputs.to_parquet`. The full `ScenarioConfig` that
produced it is stored once per scenario as `config.yaml` in the same
directory.

## Row model

The table has **one row per simulated hour** (8760 rows for a full year).
Every dispatch quantity is time-indexed, so each column other than `hour`
is **list-valued**: a single cell holds that hour's vector across the
relevant entities (generators, zones, storage units, or transmission
links). Entity order within a list matches the dispatch model's variable
layout and is stable across all rows and all year files of a scenario.

## Columns

| Column | Type | Per-entity | Unit | Range | Description |
|---|---|---|---|---|---|
| `hour` | `int32` | — | hour index | `0` – `8759` | Hour of the simulated year. |
| `dispatch` | `list<float64>` | generator | MW | `pmin` – `pmax × availability` | Thermal generation per generator. |
| `wind` | `list<float64>` | zone | MW | `0` – `wind_cf × wind_cap` | Dispatched wind per zone. |
| `solar` | `list<float64>` | zone | MW | `0` – `solar_cf × solar_cap` | Dispatched solar per zone. |
| `slack` | `list<float64>` | zone | MW | `≥ 0` | Unserved load per zone (load shedding). |
| `dump` | `list<float64>` | zone | MW | `≥ 0` | Overgeneration absorbed (curtailed) per zone. |
| `price` | `list<float64>` | zone | $/MWh | `0` – `voll` | Zonal energy price (energy-balance dual). |
| `storage_charge` | `list<float64>` | storage unit | MW | `0` – `power_cap` | Storage charging power. Optional. |
| `storage_discharge` | `list<float64>` | storage unit | MW | `0` – `power_cap` | Storage discharging power. Optional. |
| `storage_soc` | `list<float64>` | storage unit | MWh | `0` – `energy_cap` | Storage state of charge. Optional. |
| `flows` | `list<float64>` | link | MW | `-ttc` – `ttc` | Transmission link flow; sign gives direction. Optional. |
| `emissions` | `list<float64>` | generator | tCO2 | `≥ 0` | CO2 emitted per generator per hour. Optional. |

**Optional columns** are omitted entirely from the file when their source
array is absent: the storage columns when the scenario has no storage
units, `flows` when it has no transmission links, and `emissions` until it
is populated by downstream emissions accounting.

## Schema metadata

Scalar fields and array dimensions are stored in the Parquet schema
metadata under the key `market_sim` as a JSON object, so a saved result
reconstructs exactly.

| Key | Type | Description |
|---|---|---|
| `objective_value` | float | Optimal LP objective (total system cost, $). |
| `status` | string | HiGHS model-status string, e.g. `Optimal`. |
| `build_time` | float | Seconds spent assembling and loading the model. |
| `solve_time` | float | Seconds spent inside the solver. |
| `T` | int | Number of hours (rows) in the table. |
| `n_gen` | int | Number of generators (length of each `dispatch` list). |
| `n_zones` | int | Number of zones (length of each `price` list). |
| `has_storage` | bool | Whether the storage columns are present. |
| `has_flows` | bool | Whether the `flows` column is present. |
| `has_emissions` | bool | Whether the `emissions` column is present. |

## Fleet context metadata

A second JSON object is stored under the key `market_sim_fleet`, holding
the fleet and resource attributes that produced the result. It lets an
aggregated export attribute dispatch to fuels and compute emissions and
curtailment without re-deriving the fleet. The three per-generator lists
are aligned with the generator axis of the `dispatch` column and have
length `n_gen`. This object is absent for results written without a fleet
context.

| Key | Type | Unit | Description |
|---|---|---|---|
| `fuel_types` | list of string | — | Fuel type of each generator. |
| `pmax_mw` | list of float | MW | Nameplate capacity of each generator. |
| `emission_rate` | list of float | tCO2/MWh | CO2 rate of each generator. |
| `wind_cap_mw` | float | MW | Total installed wind capacity. |
| `solar_cap_mw` | float | MW | Total installed solar capacity. |
| `wind_potential_mwh` | float | MWh | Annual available wind energy (capacity factor × capacity, summed over zones and hours). |
| `solar_potential_mwh` | float | MWh | Annual available solar energy. |
| `storage_energy_cap_mwh` | float | MWh | Total storage energy capacity. |

## Demand input conventions (EIA-930)

The hourly system demand behind every cached result comes from EIA-930
balancing-authority data (`market_sim.data.eia_loader.load_demand`). Two
conventions apply to all ISOs and are baked into backcast calibration:

- **Generation-side accounting.** EIA-930 demand satisfies
  `Demand + Interchange = Net Generation`, so the series is already at the
  generation level. Backcasts therefore run with `td_loss_factor = 0.0` —
  no T&D gross-up — so the grid demand target equals actual grid net
  generation and behind-the-meter CHP self-supply stays off-grid (the
  ERCOT convention; see `ScenarioConfig.td_loss_factor`).
- **Net-load convention** (backcast playbook §8.1). EIA-930 demand is
  metered at the transmission level and is **net of behind-the-meter
  PV/storage/DER**. Backcasts model **only ISO-metered, front-of-meter
  resources** as supply; a BTM solar profile must never be added on the
  supply side against net demand (double counting). **CAISO is the
  extreme case: its demand series is net of ~15+ GW of BTM PV**, so much
  of the duck-curve shaping lives inside the demand series itself — that
  is correct and self-consistent for backcasts. This is the convention
  note every future ISO addition copies.

Per-ISO specifics:

| ISO | System series | Interchange handling | Zonal allocation |
|---|---|---|---|
| ERCOT | `data/eia_hourly/ERCO hourly.parquet` | DC-tie net interchange folded into demand | Measured hourly weather-zone shapes (NP3-565-CD native load) |
| PJM | demand-profiles parquet | Measured tie-line net export added per border zone | Measured hourly transmission-zone shapes (metered-load files) |
| CAISO | `data/eia_hourly/CISO hourly.parquet` | **None** — imports are supply via the `WECC_import` node's priced pseudo-generators | Measured hourly TAC-area shapes (upload U4, OASIS `SLD_FCST` ACTUAL) where covered; static measured shares (NP15 0.3969 / ZP26 0.0646 / SP15 0.5385, Jan-2023 sample) elsewhere. PGE-TAC splits 0.86/0.14 onto NP15/ZP26; SCE+SDGE+VEA map to SP15. Refresh: complete the U4 monthly pulls 2023–2025. |
| others | demand-profiles parquet | none | static per-zone `load_share` |
