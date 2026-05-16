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
