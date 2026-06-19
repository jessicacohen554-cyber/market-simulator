# Data dictionary

The canonical contract for the curated `data/clean` tree. Every clean datatype
has exactly one schema under [`schema/`](schema/) (`<datatype>.schema.yaml`)
declaring its canonical columns — name, dtype, unit, nullability — and its key
columns. All curation sessions write through the shared
[`scripts/lib/clean_io.py`](../../scripts/lib/clean_io.py) `write_clean(...)`
seam, which validates against these schemas before writing Parquet and embeds
the schema version + source provenance in each file.

**Conventions (enforced by `clean_io`):**

- Columns are `lower_snake_case`.
- Time is tz-aware **UTC** in `interval_start_utc`; an optional tz-naive
  wall-clock `interval_start_local` may accompany it (UTC is authoritative).
- Standard keys: `iso`, `zone`, `node`, `plant_id`, `unit_id`, `year`,
  `month`, `hour`.
- Units are explicit in column names: `*_mw`, `*_mwh`, `price_*_usd_per_mwh`,
  `*_usd_per_mw` (AS capacity), `*_usd_per_mmbtu` (fuel), `*_kg` (emissions).

> **This file is generated — do not hand-edit.** Per-column tables are rendered
> from the schema YAMLs and the coverage matrix from the provenance metadata
> embedded in `data/clean`. To change a column, edit its schema YAML (or
> recurate the data) and run `python scripts/render_data_dictionary.py`. The
> test `tests/test_data_dictionary_sync.py` guards that the committed file
> matches a fresh render.

## Regenerate from raw

The clean tree is derived and disposable; it is rebuilt from `data/raw` by the
per-datatype curation scripts (`scripts/curate_*.py`, added per session), each
calling `clean_io.write_clean(df, datatype, ...)`. To regenerate everything run
`python scripts/regenerate_clean.py`; to verify an existing file round-trips
against its embedded schema, call `clean_io.validate_clean(path)`. Raw inputs
are described in [`../README.md`](../README.md) and are never modified in place.

## ISO coverage matrix

Built from the `market_sim.*` provenance metadata embedded in `data/clean`
(regenerate the tree with `python scripts/regenerate_clean.py`). Each cell is
the span of calendar years curated for that datatype and ISO; `—` means none is
curated. Markets (DAM/RTM) are aggregated here — see each datatype's section
for the market split.

| datatype | ERCOT | CAISO | PJM | MISO | SPP | NYISO | NEISO |
|---|---|---|---|---|---|---|---|
| lmp | — | 2023–2025 | 2023–2025 | — | — | 2023–2025 | 2023–2025 |
| load | 2015–2026 | 2023–2026 | 2023–2025 | 2023–2025 | 2015–2026 | 2023–2026 | 2015–2026 |
| ancillary-services | 2025–2026 | — | 2023–2026 | — | — | 2023–2026 | — |
| generation | 2018–2026 | 2023–2025 | 2022–2026 | 2023–2025 | 2018–2026 | 2018–2026 | 2018–2026 |
| renewables | 2023 | 2023–2024 | — | — | — | — | — |
| validation | 2021–2025 | 2023–2025 | 2021–2025 | — | — | 2023–2025 | 2023–2025 |

### National / ISO-agnostic datatypes

Not partitioned by ISO (no `iso` in their `data/clean` provenance); coverage is
national. `n/a` marks datatypes with no year partition (a single current
snapshot).

| datatype | scope | years |
|---|---|---|
| emissions | CAMPD/CEMS, by plant and unit | 2023–2025 |
| outages | derived (CAMPD downtime + curated ERCOT lists) | 2023–2026 |
| fleet | EIA-860 / eGRID / master registry | 2023–2025 |
| fuel-prices | national hubs (Henry Hub) | n/a |
| reference | crosswalks / lookups (ISO-agnostic) | n/a |

---

## lmp

Locational marginal prices and components. Schema:
[`schema/lmp.schema.yaml`](schema/lmp.schema.yaml).

- **Keys:** `iso`, `market`, `node`, `interval_start_utc`
- **Reconciles:** CAISO `LMP/MCC/MCE/MCL/MGHG`, PJM `DA_LMP/RT_LMP`, NYISO LBMP
  components, ERCOT settlement-point price, NEISO SMD hub LMP — into one total
  `lmp_usd_per_mwh` plus energy/congestion/loss/ghg components, with DA vs RT
  carried in the `market` key.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC start of the settlement interval (hour beginning). |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Optional wall-clock local interval start in the ISO's prevailing zone (informational; UTC is authoritative for joins). |
| `iso` | `string` | `none` | no | ISO/RTO code (ERCOT, CAISO, PJM, MISO, SPP, NYISO, NEISO). |
| `market` | `string` | `none` | no | Market run — "DAM" (day-ahead) or "RTM" (real-time). |
| `node` | `string` | `none` | no | Pricing node / settlement point / hub identifier. Use the ISO's native node id; zone-level series use the zone name here. |
| `zone` | `string` | `none` | yes | Load/reporting zone the node rolls up to, when known. |
| `lmp_usd_per_mwh` | `float64` | `usd_per_mwh` | no | Total locational marginal price (CAISO LMP, PJM DA/RT_LMP, NYISO LBMP). |
| `energy_usd_per_mwh` | `float64` | `usd_per_mwh` | yes | System energy (marginal energy) component — CAISO MCE. |
| `congestion_usd_per_mwh` | `float64` | `usd_per_mwh` | yes | Marginal congestion component — CAISO MCC, NYISO MCC. |
| `loss_usd_per_mwh` | `float64` | `usd_per_mwh` | yes | Marginal loss component — CAISO MCL, NYISO MCL. |
| `ghg_usd_per_mwh` | `float64` | `usd_per_mwh` | yes | Greenhouse-gas adder component — CAISO MGHG (other ISOs null). |

## load

Hourly demand and forecast by zone. Schema:
[`schema/load.schema.yaml`](schema/load.schema.yaml).

- **Keys:** `iso`, `zone`, `interval_start_utc`
- **Reconciles:** CAISO TAC-area `mw`, NYISO `Load`, EIA-930 `Demand` / `Demand
  forecast` — into `load_mw`, `load_forecast_mw`, optional `net_load_mw`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC start of the hour. |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Optional wall-clock local hour start in the ISO's prevailing zone. |
| `iso` | `string` | `none` | no | ISO/RTO code. |
| `zone` | `string` | `none` | no | Load zone / TAC area / balancing authority the load is reported for. |
| `load_mw` | `float64` | `mw` | no | Actual metered load for the hour (CAISO mw, NYISO Load, EIA-930 Demand). |
| `load_forecast_mw` | `float64` | `mw` | yes | Day-ahead / short-term load forecast (CAISO forecast LOAD_TYPE, EIA Demand forecast). |
| `net_load_mw` | `float64` | `mw` | yes | Net load — load minus wind and solar output, when derivable. |

## ancillary-services

AS clearing prices and cleared quantities. Schema:
[`schema/ancillary-services.schema.yaml`](schema/ancillary-services.schema.yaml).

- **Keys:** `iso`, `zone`, `market`, `interval_start_utc`
- **Reconciles:** NYISO `spin_10/nonsync_10/op_30/reg_cap`, PJM long
  `ancillary_service/value`, ERCOT `REGUP/REGDN/RRS/ECRS/NSPIN`, CAISO
  `RU/RD/SR/NR` — onto a common product taxonomy (reg up/down, spin, nonspin,
  30-min supplemental), prices in `$/MW`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC start of the hour. |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Optional wall-clock local hour start. |
| `iso` | `string` | `none` | no | ISO/RTO code. |
| `zone` | `string` | `none` | no | AS reserve zone / region (use "SYSTEM" for system-wide products). |
| `market` | `string` | `none` | no | Market run — "DAM" (day-ahead) or "RTM" (real-time). |
| `reg_up_price_usd_per_mw` | `float64` | `usd_per_mw` | yes | Regulation-up (and combined regulation capacity) clearing price. |
| `reg_down_price_usd_per_mw` | `float64` | `usd_per_mw` | yes | Regulation-down clearing price. |
| `spin_price_usd_per_mw` | `float64` | `usd_per_mw` | yes | Spinning / 10-minute synchronized reserve clearing price. |
| `nonspin_price_usd_per_mw` | `float64` | `usd_per_mw` | yes | Non-spinning / 10-minute non-synchronized reserve clearing price. |
| `supp_30min_price_usd_per_mw` | `float64` | `usd_per_mw` | yes | 30-minute operating / supplemental reserve (incl. ERCOT ECRS) clearing price. |
| `reg_up_mw` | `float64` | `mw` | yes | Cleared regulation-up requirement. |
| `reg_down_mw` | `float64` | `mw` | yes | Cleared regulation-down requirement. |
| `spin_mw` | `float64` | `mw` | yes | Cleared spinning / synchronized reserve. |
| `nonspin_mw` | `float64` | `mw` | yes | Cleared non-spinning reserve. |
| `supp_30min_mw` | `float64` | `mw` | yes | Cleared 30-minute supplemental reserve. |

## generation

Generation by fuel (long form). Schema:
[`schema/generation.schema.yaml`](schema/generation.schema.yaml).

- **Keys:** `iso`, `zone`, `fuel`, `interval_start_utc`
- **Reconciles:** EIA-930 wide `NG: *` fuel columns (unpivoted), PJM
  `fuel_type/mw/is_renewable`, CAISO technology buckets.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC start of the hour. |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Optional wall-clock local hour start. |
| `iso` | `string` | `none` | no | ISO/RTO code. |
| `zone` | `string` | `none` | no | Generation zone / balancing authority (use "SYSTEM" for ISO-wide totals). |
| `fuel` | `string` | `none` | no | Canonical fuel/technology bucket (coal, gas, nuclear, hydro, solar, wind, geothermal, oil, storage, other). |
| `generation_mw` | `float64` | `mw` | no | Average generation over the hour for this fuel. |
| `is_renewable` | `bool` | `none` | yes | Whether the fuel counts as renewable (PJM is_renewable flag, when provided). |

## renewables

Renewable output, availability (HSL) and curtailment. Schema:
[`schema/renewables.schema.yaml`](schema/renewables.schema.yaml).

- **Keys:** `iso`, `zone`, `fuel`, `interval_start_utc`
- **Reconciles:** CAISO/ERCOT HSL `wind_gen_mw/wind_hsl_mw/solar_*`
  (unpivoted), CAISO curtailment — into `generation_mw`, `hsl_mw`,
  `curtailment_mw`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC start of the hour. |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Optional wall-clock local hour start. |
| `iso` | `string` | `none` | no | ISO/RTO code. |
| `zone` | `string` | `none` | no | Reporting zone (use "SYSTEM" for ISO-wide totals). |
| `fuel` | `string` | `none` | no | Renewable fuel/technology (wind, solar, ...). |
| `generation_mw` | `float64` | `mw` | no | Actual renewable generation over the hour (*_gen_mw). |
| `hsl_mw` | `float64` | `mw` | yes | Available output / high sustainable limit (*_hsl_mw). |
| `curtailment_mw` | `float64` | `mw` | yes | Curtailed renewable energy (hsl_mw - generation_mw), when reported. |

## emissions

Hourly CEMS/CAMPD emissions by plant/unit. Schema:
[`schema/emissions.schema.yaml`](schema/emissions.schema.yaml).

- **Keys:** `plant_id`, `unit_id`, `interval_start_utc`
- **Reconciles:** CAMPD facility- and unit-level
  `co2Mass/noxMass/so2Mass/heatInput/grossLoad` — masses standardized to
  `*_kg`, heat input to MMBtu.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC start of the hour (from CAMPD date + hour). |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Optional wall-clock local hour start. |
| `iso` | `string` | `none` | yes | ISO/RTO the plant is assigned to, when mapped. |
| `plant_id` | `int64` | `none` | no | Plant / facility identifier (CAMPD facilityId). |
| `unit_id` | `string` | `none` | no | Generating-unit identifier (CAMPD unitId). Use "ALL" for facility-grain rows so the key stays non-null. |
| `gross_mw` | `float64` | `mw` | yes | Gross electrical load over the hour (CAMPD grossLoad). |
| `heat_input_mmbtu` | `float64` | `mmbtu` | yes | Heat input over the hour (CAMPD heatInput). |
| `co2_kg` | `float64` | `kg` | yes | CO2 mass emitted over the hour (CAMPD co2Mass, converted to kg). |
| `nox_kg` | `float64` | `kg` | yes | NOx mass emitted over the hour (CAMPD noxMass, converted to kg). |
| `so2_kg` | `float64` | `kg` | yes | SO2 mass emitted over the hour (CAMPD so2Mass, converted to kg). |

## outages

Generator outages / available capacity. Schema:
[`schema/outages.schema.yaml`](schema/outages.schema.yaml).

- **Keys:** `plant_id`, `unit_id`, `interval_start_utc`
- **Reconciles:** CAMPD-derived downtime, ERCOT curated unit-outage lists —
  into `outage_mw` / `available_mw`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC start of the outage interval. |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Optional wall-clock local interval start. |
| `iso` | `string` | `none` | yes | ISO/RTO the unit is assigned to, when mapped. |
| `plant_id` | `int64` | `none` | no | Plant / facility identifier. |
| `unit_id` | `string` | `none` | no | Generating-unit identifier (use "ALL" for plant-grain rows). |
| `outage_mw` | `float64` | `mw` | no | Capacity offline (unavailable) during the interval. |
| `available_mw` | `float64` | `mw` | yes | Capacity available during the interval (nameplate minus outage). |
| `outage_type` | `string` | `none` | yes | Outage classification (planned, forced, derate) when known. |

## validation

Calibration/validation reference targets (tidy long form). Schema:
[`schema/validation.schema.yaml`](schema/validation.schema.yaml).

- **Keys:** `iso`, `zone`, `year`, `month`, `fuel`, `metric`
- **Reconciles:** heterogeneous `_validation-source` benchmark files (renewable
  capacity, generation, emissions, price) into `(dimensions → metric, value,
  unit)`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO code. |
| `zone` | `string` | `none` | no | Zone the target applies to (use "SYSTEM" for ISO-wide totals). |
| `year` | `int64` | `year` | no | Calendar year of the reference value. |
| `month` | `int64` | `none` | no | Calendar month 1-12, or 0 for annual (non-monthly) targets. |
| `fuel` | `string` | `none` | no | Fuel/technology the metric applies to (use "ALL" when not fuel-specific). |
| `metric` | `string` | `none` | no | Named reference metric (e.g. capacity_mw, generation_mwh, co2_kg, avg_price_usd_per_mwh). |
| `value` | `float64` | `none` | no | Reference value; physical unit carried in the `unit` column. |
| `unit` | `string` | `none` | no | Unit of `value` (mw, mwh, kg, usd_per_mwh, ...). |
| `source` | `string` | `none` | yes | Provenance of the reference value (publisher / dataset). |

## fleet

Generator fleet registry. Schema:
[`schema/fleet.schema.yaml`](schema/fleet.schema.yaml).

- **Keys:** `plant_id`, `unit_id`
- **Reconciles:** EIA-860 (`Plant Code`, `Generator ID`, `Nameplate Capacity
  (MW)`, …), master plant registry, eGRID — into snake_case + unit-suffixed
  columns.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `plant_id` | `int64` | `none` | no | Plant code (EIA-860 "Plant Code" / registry plantid). |
| `unit_id` | `string` | `none` | no | Generator id (EIA-860 "Generator ID"); use "ALL" for plant-grain rows. |
| `iso` | `string` | `none` | yes | ISO/RTO the plant is assigned to, when mapped. |
| `zone` | `string` | `none` | yes | Zone within the ISO, when mapped. |
| `plant_name` | `string` | `none` | yes | Plant name. |
| `fuel` | `string` | `none` | yes | Canonical fuel/technology bucket (coal, gas, nuclear, ...). |
| `prime_mover` | `string` | `none` | yes | Prime mover code (EIA-860 Prime Mover). |
| `technology` | `string` | `none` | yes | Detailed technology description (EIA-860 Technology). |
| `nameplate_capacity_mw` | `float64` | `mw` | no | Nameplate capacity (EIA-860 "Nameplate Capacity (MW)"). |
| `summer_capacity_mw` | `float64` | `mw` | yes | Summer net capacity. |
| `winter_capacity_mw` | `float64` | `mw` | yes | Winter net capacity. |
| `energy_capacity_mwh` | `float64` | `mwh` | yes | Storage energy capacity (EIA-860 "Nameplate Energy Capacity (MWh)"). |
| `operating_year` | `int64` | `year` | yes | First operating / build year (EIA-860 "Operating Year" / registry year_built). |

## fuel-prices

Delivered fuel price benchmarks. Schema:
[`schema/fuel-prices.schema.yaml`](schema/fuel-prices.schema.yaml).

- **Keys:** `fuel`, `hub`, `interval_start_utc`
- **Reconciles:** Henry Hub daily `price_usd_mmbtu`, citygate/basis benchmarks
  — into `price_usd_per_mmbtu` by `fuel`/`hub`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC start of the price period (00:00 UTC of the date for daily series). |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Optional wall-clock local date/time. |
| `fuel` | `string` | `none` | no | Fuel type (gas, coal, oil). |
| `hub` | `string` | `none` | no | Pricing hub / region (e.g. henry_hub, socal_citygate). |
| `price_usd_per_mmbtu` | `float64` | `usd_per_mmbtu` | no | Delivered fuel price (henry_hub_daily price_usd_mmbtu). |

## reference

Crosswalk / lookup tables (heterogeneous). Schema:
[`schema/reference.schema.yaml`](schema/reference.schema.yaml).

- **Keys:** `key` (+ `plant_id`/`iso`/`zone`/`node` when applicable)
- **Reconciles:** master plant registry, bin assignments, zone/node crosswalks
  — conventions enforced, table-specific columns permitted.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `key` | `string` | `none` | no | Stable per-row identifier for the reference table. |
| `plant_id` | `int64` | `none` | yes | Plant code, when the table is plant-keyed. |
| `iso` | `string` | `none` | yes | ISO/RTO code, when applicable. |
| `zone` | `string` | `none` | yes | Zone, when applicable. |
| `node` | `string` | `none` | yes | Pricing node / settlement point, when applicable. |
