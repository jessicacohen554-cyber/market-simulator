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

| datatype | ERCOT | CAISO | PJM | MISO | NYISO | NEISO |
|---|---|---|---|---|---|---|
| lmp | — | — | — | — | — | — |
| load | — | — | — | — | — | — |
| demand-profile | 2021–2025 | 2021–2025 | 2021–2025 | 2021–2025 | 2021–2025 | 2021–2025 |
| ancillary-services | — | — | — | — | — | — |
| energy-offers | — | — | — | — | — | — |
| generation | — | — | — | — | — | — |
| renewables | — | — | — | — | — | — |
| validation | — | — | — | — | — | — |
| fuel-basis | — | — | — | — | — | — |
| fuel-zonal-hub | — | — | — | — | — | — |
| unit-outage-events | — | — | — | — | — | — |
| partial-outages | — | — | — | — | — | — |
| capacity-deliverability | — | — | — | — | — | — |
| confirmed-retirements | — | — | — | — | — | — |
| gtc-limits | — | — | — | — | — | — |
| ramp-capability | — | — | — | — | — | — |
| winter-fuel-inventory | — | — | — | — | — | — |
| chp-btm-share | — | — | — | — | — | — |
| ramp-capability | — | — | — | — | — | — |

### National / ISO-agnostic datatypes

Not partitioned by ISO (no `iso` in their `data/clean` provenance); coverage is
national. `n/a` marks datatypes with no year partition (a single current
snapshot).

| datatype | scope | years |
|---|---|---|
| emissions | CAMPD/CEMS, by plant and unit | n/a |
| emissions-unit-annual | — | n/a |
| outages | derived (CAMPD downtime + curated ERCOT lists) | n/a |
| fleet | EIA-860 / eGRID / master registry | n/a |
| fuel-prices | national hubs (Henry Hub) | n/a |
| fuel-hub-monthly | national (Henry Hub monthly) | n/a |
| fuel-ercot-ep-gas | ERCOT / TX electric-power consumers | n/a |
| fuel-takeorpay | ERCOT plants (EIA-923 Schedule-5) | n/a |
| reference | crosswalks / lookups (ISO-agnostic) | n/a |
| border-lmp | neighbor-border hubs (WECC intertie, PJM_WEST) | n/a |
| zonal-shares | per-ISO via directory partitioning | n/a |
| weather | per-ISO via directory partitioning | n/a |
| egrid | national (EPA eGRID, by vintage year) | n/a |
| rggi-co2-budgets | — | n/a |
| carb-cap-schedule | — | n/a |

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
| `iso` | `string` | `none` | no | ISO/RTO code (ERCOT, CAISO, PJM, MISO, NYISO, NEISO). |
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

## demand-profile

Repaired legacy EIA-930 per-ISO system-total hourly demand (hour-of-year clock,
no zone breakdown). Schema:
[`schema/demand-profile.schema.yaml`](schema/demand-profile.schema.yaml).

- **Keys:** `iso`, `year`, `hour`
- **Reconciles:** The raw `eia_demand_profiles.parquet` extract's `raw_mw` /
  `normalized`, repaired via a physical-bounds screen (value <= 0, or > 5x the
  (iso, year) series median) plus linear interpolation -- the sole demand
  source `eia_loader.load_demand` falls back to for any (iso, year) with no
  dedicated per-BA hourly extract (every PJM year; CAISO/MISO 2021-2022).
  `repaired` flags the corrected hours.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO code (as carried by the raw extract; includes SPP, not a modeled ISO). |
| `year` | `int64` | `none` | no | Calendar year. |
| `hour` | `int64` | `none` | no | Hour-of-year index, 0..8759 (the raw source's own clock). |
| `raw_mw` | `float64` | `mw` | no | System-total demand for the hour, MW; repaired where physically impossible. |
| `normalized` | `float64` | `none` | yes | raw_mw as a fraction of the (iso, year) annual total, recomputed from the repaired series. |
| `repaired` | `bool` | `none` | no | True when this hour failed the physical-bounds screen and was interpolated. |

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

## energy-offers

PJM Real-Time effective energy offer curves (long step form). Schema:
[`schema/energy-offers.schema.yaml`](schema/energy-offers.schema.yaml).

- **Keys:** `iso`, `unit_code`, `interval_start_utc`, `step_idx`
- **Reconciles:** PJM DataMiner2 `energy_market_offers` wide
  `mw1..mw20`/`bid1..bid20` breakpoints (plus daily `avg_ecomin`/`avg_ecomax`,
  no-load and hot/cold/inter start costs) — pivoted to one row per (`unit_code`
  × operating-hour × `step_idx`) with `step_mw` / `step_price_usd_per_mwh`.
  PJM-only; unit identity is anonymised and rotated annually (not joinable
  across calendar years).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC start of the operating hour the offer applies to (hour-beginning; maps to DataMiner2 ``bid_datetime_beginning_utc``). |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Wall-clock EPT (Eastern Prevailing Time) equivalent of ``interval_start_utc`` — informational; UTC is authoritative for joins. Maps to DataMiner2 ``bid_datetime_beginning_ept``. |
| `iso` | `string` | `none` | no | Always "PJM" for this feed. |
| `unit_code` | `string` | `none` | no | Anonymised, base64-encoded unit identifier assigned by PJM (DataMiner2 ``unit_code``). Rotated annually — codes are NOT comparable across calendar years. |
| `bid_slope_flag` | `bool` | `none` | yes | True: bid curve is piecewise-linear (MW/price breakpoints connected by straight lines; MC rises continuously between steps). False: bid curve is a step function (constant $/MWh across each MW block). DataMiner2 ``bid_slope_flag``. |
| `step_idx` | `int64` | `none` | no | 1-based index of this MW/price breakpoint in the unit's offer curve for this hour. Derived by the curate script from the wide API columns ``mw1``/``bid1`` through ``mw20``/``bid20``; null breakpoints are dropped so ``step_idx`` may not be contiguous. |
| `step_mw` | `float64` | `mw` | no | MW breakpoint value for this step — the MW level at which the corresponding ``step_price_usd_per_mwh`` applies. Maps to DataMiner2 ``mwN`` columns (N = step_idx). |
| `step_price_usd_per_mwh` | `float64` | `usd_per_mwh` | no | Energy offer price for this MW step in $/MWh. Maps to DataMiner2 ``bidN`` columns (N = step_idx). PJM's energy offer cap is $2,000/MWh (cost-based cap); must-run offers may be negative. |
| `ecomin_mw` | `float64` | `mw` | yes | Average Economic Minimum (MW) for the unit for the operating day. DataMiner2 ``avg_ecomin``. Repeated on every step row for the same (unit_code, interval_start_utc) tuple. |
| `ecomax_mw` | `float64` | `mw` | yes | Average Economic Maximum (MW) for the unit for the operating day. DataMiner2 ``avg_ecomax``. Repeated on every step row for the same (unit_code, interval_start_utc) tuple. |
| `no_load_cost_usd_per_h` | `float64` | `usd_per_h` | yes | No-load cost ($/h) — the fixed cost component associated with keeping a unit online regardless of MW output. DataMiner2 ``no_load_cost``. |
| `hot_start_cost_usd` | `float64` | `usd` | yes | Hot start cost ($) — startup cost after a short outage (unit is still warm). DataMiner2 ``hot_start_cost``. |
| `cold_start_cost_usd` | `float64` | `usd` | yes | Cold start cost ($) — startup cost after an extended outage (unit is fully cold). DataMiner2 ``cold_start_cost``. |
| `inter_start_cost_usd` | `float64` | `usd` | yes | Intermediate start cost ($) — between hot and cold. DataMiner2 ``inter_start_cost``. |
| `max_daily_starts` | `float64` | `none` | yes | Maximum number of starts the unit can make in a day. DataMiner2 ``max_daily_starts``. |
| `min_runtime_h` | `float64` | `h` | yes | Minimum continuous runtime (hours) once the unit is committed. DataMiner2 ``min_runtime``. |

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

## emissions-unit-annual

Annual unit-level CAMPD roll-up (one row per plant/unit/year) — the forward
per-plant CO2-rate estimator's input. Schema:
[`schema/emissions-unit-annual.schema.yaml`](schema/emissions-unit-annual.schema.yaml).

- **Keys:** `plant_id`, `unit_id`, `year`
- **Reconciles:** The hourly unit-level CAMPD extracts
  (`data/raw/campd-unit-level`) rolled up to annual `gross_mwh`, `heat_mmbtu`,
  `co2/nox/so2_kg` (kg), `op_hours`, `starts`, plus `co2_source` / `mw_source`
  provenance flags. Curated by `curate_emissions_unit_annual.py`; the
  quarantined 2022/H1-2026 years are hard-skipped (rule 22).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `state` | `string` | `none` | no | CAMPD stateCode of the facility. |
| `plant_id` | `int64` | `none` | no | Plant / facility identifier (CAMPD facilityId). |
| `unit_id` | `string` | `none` | no | Generating-unit identifier (CAMPD unitId). "ALL" for facility-grain rows so the key stays non-null. |
| `year` | `int64` | `none` | no | Calendar year of the roll-up. |
| `primary_fuel` | `string` | `none` | yes | CAMPD primaryFuelInfo (primary fuel type), where reported. |
| `unit_type` | `string` | `none` | yes | CAMPD unitType (boiler / combustion turbine / …), where reported. |
| `gross_mwh` | `float64` | `mwh` | no | Annual sum of hourly gross load (MWh gross). |
| `steam_load_klbh_sum` | `float64` | `klb` | yes | Annual sum of hourly steam load (1000 lb/hr) — CHP host process steam, a proxy for cogeneration heat export. |
| `co2_kg` | `float64` | `kg` | no | Annual CO2 mass (kg), backfilled for unmonitored hours per co2_source. |
| `nox_kg` | `float64` | `kg` | yes | Annual NOx mass (kg). |
| `so2_kg` | `float64` | `kg` | yes | Annual SO2 mass (kg). |
| `heat_mmbtu` | `float64` | `mmbtu` | no | Annual heat input (MMBtu). |
| `op_hours` | `int64` | `hours` | no | Hours with gross load > 0 (operating hours). |
| `starts` | `int64` | `none` | no | Count of off->on transitions (gross_mw crossing 1 MW, campd._ONLINE_MW / _startup_factors convention) on a gap-filled hourly clock. |
| `co2_source` | `string` | `none` | no | CO2 provenance: "measured" (CO2 reported for ~all heat), "partial_backfill" (scaled up to full heat at the unit's own measured intensity), or "heat_backfilled" (no CO2 reported; EPA gas default factor on heat). |
| `mw_source` | `string` | `none` | no | Gross-MW provenance: "measured" (real gross-load readings present) or "heat_proxy" (unit reported heat but no gross load — CHP/steam host). |

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

## fuel-hub-monthly

Monthly Henry Hub spot averages (EIA RNGWHHDm). Schema:
[`schema/fuel-hub-monthly.schema.yaml`](schema/fuel-hub-monthly.schema.yaml).

- **Keys:** `fuel`, `hub`, `year`, `month`
- **Reconciles:** `henry_hub_monthly.csv` `price_usd_mmbtu` — into
  `price_usd_per_mmbtu` keyed by `fuel`/`hub`/`year`/`month`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `fuel` | `string` | `none` | no | Fuel type (gas, coal, oil). |
| `hub` | `string` | `none` | no | Pricing hub / region (e.g. henry_hub). |
| `year` | `int64` | `none` | no | Calendar year. |
| `month` | `int64` | `none` | no | Calendar month (1–12). |
| `price_usd_per_mmbtu` | `float64` | `usd_per_mmbtu` | no | Monthly average delivered fuel price in $/MMBtu. |

## fuel-basis

Per-ISO monthly gas basis vs Henry Hub (winter hub overlay). Schema:
[`schema/fuel-basis.schema.yaml`](schema/fuel-basis.schema.yaml).

- **Keys:** `iso`, `year`, `month`, `hub`
- **Reconciles:** `gas_basis_by_iso_month.csv` `basis_usd_mmbtu` (Algonquin for
  NEISO, Transco Z6/Iroquois for NYISO when filled) — `source` column stripped;
  keyed by `iso`/`year`/`month`/`hub`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/market region (ERCOT, CAISO, PJM, MISO, NYISO, NEISO). |
| `year` | `int64` | `none` | no | Calendar year. |
| `month` | `int64` | `none` | no | Calendar month (1–12). |
| `hub` | `string` | `none` | no | Pipeline trading-hub name (e.g. Algonquin Citygate, Transco Z6 NY). |
| `basis_usd_mmbtu` | `float64` | `usd_per_mmbtu` | no | Basis vs Henry Hub in $/MMBtu (positive = above HH, negative = below). Measured from pipeline-hub spot or EIA citygate proxy. |

## fuel-zonal-hub

Per-ISO zonal gas-hub annual prices/basis. Schema:
[`schema/fuel-zonal-hub.schema.yaml`](schema/fuel-zonal-hub.schema.yaml).

- **Keys:** `iso`, `zone`, `year`, `hub`
- **Reconciles:** ERCOT/PJM/MISO `basis_vs_hh_usd_mmbtu`; NYISO absolute
  `hub_usd_mmbtu`; ERCOT West `neg_day_freq` — keyed by
  `iso`/`zone`/`year`/`hub`, ISO-partitioned by directory.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/market region (ERCOT, NYISO, PJM, MISO). |
| `zone` | `string` | `none` | no | Model zone name. |
| `year` | `int64` | `none` | no | Calendar year. |
| `hub` | `string` | `none` | no | Pipeline hub name for this zone (e.g. Waha, Iroquois Z2, Chicago Citygate). |
| `basis_vs_hh_usd_mmbtu` | `float64` | `usd_per_mmbtu` | yes | Annual average basis vs Henry Hub ($/MMBtu). Present for ERCOT, PJM, MISO; absent for NYISO (which uses hub_usd_mmbtu instead). |
| `hub_usd_mmbtu` | `float64` | `usd_per_mmbtu` | yes | Annual average absolute hub price ($/MMBtu). Present for NYISO only; absent for ISOs that record basis_vs_hh_usd_mmbtu instead. |
| `neg_day_freq` | `float64` | `fraction` | yes | Fraction of the year the hub spot price was negative (0.0–1.0). Populated for ERCOT West/Panhandle (Waha hub) only; absent elsewhere. |

## fuel-ercot-ep-gas

Monthly EIA N3045TX3 TX delivered-to-electric-power gas price ($/Mcf). Schema:
[`schema/fuel-ercot-ep-gas.schema.yaml`](schema/fuel-ercot-ep-gas.schema.yaml).

- **Keys:** `year`, `month`
- **Reconciles:** `ercot_electric_power_gas_price.csv` `price_usd_mcf` —
  `source` column stripped; keyed by `year`/`month`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `year` | `int64` | `none` | no | Calendar year. |
| `month` | `int64` | `none` | no | Calendar month (1–12). |
| `price_usd_mcf` | `float64` | `usd_per_mcf` | no | Monthly average price of natural gas delivered to TX electric-power consumers ($/Mcf; multiply by 1/1.036 MMBtu/Mcf to convert to $/MMBtu). |

## fuel-takeorpay

ERCOT per-plant EIA-923 gas spot vs contract share. Schema:
[`schema/fuel-takeorpay.schema.yaml`](schema/fuel-takeorpay.schema.yaml).

- **Keys:** `plant_code`
- **Reconciles:** `gas_takeorpay_ERCOT.csv` — retains `plant_code`,
  `spot_share`, `total_mmbtu`; strips `contract_share`, `n_receipts`, `source`,
  `breakdown`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `plant_code` | `int64` | `none` | no | EIA plant code (integer, matches fleet plant_id). |
| `spot_share` | `float64` | `fraction` | no | Fraction of annual natural-gas purchases at spot prices (0.0–1.0). The complement (1 - spot_share) is firm-contracted and insulated from hub-price swings. |
| `total_mmbtu` | `float64` | `mmbtu` | no | Total annual gas volume in MMBtu. Used as the MMBtu weight when aggregating per-plant spot shares to model zones. |

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

## border-lmp

Measured neighbor-border hourly Day-Ahead LMP. Schema:
[`schema/border-lmp.schema.yaml`](schema/border-lmp.schema.yaml).

- **Keys:** `year`, `hour`, `hub`
- **Reconciles:** CAISO OASIS WECC intertie LMP (MALIN, PALOVRDE), PJM hub LMP
  (CHICAGO GEN / AEP GEN / ATSI GEN equal-weight mean for MISO PJM_WEST) — on
  the model's fixed non-leap 8760-hour local-year calendar, dense `price` (NaN
  for gaps).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `year` | `int64` | `none` | no | Calendar year of the price observation. |
| `hour` | `int64` | `none` | no | Hour-of-year index [0..8759] on the model's fixed non-leap local-time calendar (Pacific for CAISO, Central for MISO). Feb 29 is excluded; DST spring-forward gap interpolated (limit=2). |
| `hub` | `string` | `none` | no | Border hub identifier. CAISO: MALIN (COI/PDCI PNW scheduling point), PALOVRDE (Path-46 desert-SW scheduling point). MISO: PJM_WEST (equal-weight mean of CHICAGO GEN / AEP GEN / ATSI GEN hubs). |
| `price` | `float64` | `usd_per_mwh` | yes | Day-Ahead total LMP ($/MWh). CAISO: energy + congestion + loss (MCE+MCC+MCL), GHG excluded (re-added per-tranche by the injector). MISO/PJM: total_lmp_da (energy + congestion + loss). NaN for hours with no data (OASIS retention gap, missing source). |

## zonal-shares

Hourly zonal load share fractions (per ISO, per year). Schema:
[`schema/zonal-shares.schema.yaml`](schema/zonal-shares.schema.yaml).

- **Keys:** `hour`, `zone`
- **Reconciles:** PJM metered-load CSV (20 real zones → 8 model zones), ERCOT
  native-load XLSX (8 weather zones → 6 model zones), CAISO TAC-area CSV (4
  areas → 3 trading-hub zones), MISO EIA-930 sub-BA CSV (6 sub-BAs → 3 model
  zones), NYISO pal CSV (11 settlement zones → 5 model zones), NEISO SMD wide
  CSV (8 load zones → 4 model zones) — into `share` fractions summing to ≈1.0
  per hour, long format `(hour, zone, share)`. Files are ISO-partitioned by
  directory path (`data/clean/zonal-shares/<ISO>/`).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `hour` | `int64` | `none` | no | Hour of year on the fixed non-leap 8760-hour clock (0 = first hour of Jan 1, 8759 = last hour of Dec 31, Feb 29 excluded for leap years). |
| `zone` | `string` | `none` | no | Model zone name matching the ISO's ISOConfig.zone_names. Each ISO-year file contains one row per (hour, zone) pair for every zone in the ISO topology. |
| `share` | `float64` | `fraction` | no | Fraction of system load allocated to this zone for this hour (0.0–1.0). Shares sum to ≈1.0 across all zones for each hour (tolerance ±1e-9). |

## weather

Daily maximum and minimum temperature by model zone. Schema:
[`schema/weather.schema.yaml`](schema/weather.schema.yaml).

- **Keys:** `date`, `zone`
- **Reconciles:** Per-ISO NOAA GHCN-Daily TMAX/TMIN CSVs (zone-level files plus
  load-weighted ISO aggregates for CAISO and NEISO, NYC-metro aggregate for
  NYISO) — into one `(date, zone, tmax_c, tmin_c)` row per zone per calendar
  day. Sentinel zones: `_load_weighted` (CAISO, NEISO ISO-level aggregate),
  `_downstate` (NYISO NYC-metro). Files are ISO-partitioned by directory path
  (`data/clean/weather/<ISO>/`).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `date` | `datetime64[ns]` | `none` | no | Calendar date of the observation (tz-naive local date). One row per zone per calendar day, with Feb 29 included when present in the raw archive. |
| `zone` | `string` | `none` | no | Model zone name (matching ISOConfig.zone_names) or a sentinel: '_load_weighted' for an ISO-level load-weighted temperature aggregate, '_downstate' for the NYISO NYC-metro (Central Park / LaGuardia / JFK) aggregate. |
| `tmax_c` | `float64` | `deg_c` | no | Daily maximum temperature in degrees Celsius (NOAA GHCN-Daily TMAX, load-weighted over the zone's representative stations). Gap-filled via forward-fill then back-fill in the curate step so no null values remain. |
| `tmin_c` | `float64` | `deg_c` | yes | Daily minimum temperature in degrees Celsius (NOAA GHCN-Daily TMIN). Null for zones curated from TMAX-only source files (CAISO '_load_weighted', NYISO '_downstate', and NYISO per-zone TMAX-only series). |

## egrid

eGRID plant-level extract (location, BA, fuel/CO2 columns). Schema:
[`schema/egrid.schema.yaml`](schema/egrid.schema.yaml).

- **Keys:** `plant_id`
- **Reconciles:** EPA eGRID workbook plant sheet (`PLNT<YY>`)
  `ORISPL/LAT/LON/FIPSST/FIPSCNTY/BACODE/PLFUELCT/PLNGENAN/PLCO2AN` — the union
  of what `zone_assignment.py` (geography) and `egrid.py` (fossil CO2 rate)
  each need, unfiltered, one file per eGRID vintage year.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `plant_id` | `int64` | `none` | no | ORIS plant code (eGRID ORISPL). |
| `lat` | `float64` | `degrees` | yes | Plant latitude (eGRID LAT). |
| `lon` | `float64` | `degrees` | yes | Plant longitude (eGRID LON). |
| `fips_state` | `int64` | `none` | yes | FIPS state code (eGRID FIPSST). |
| `fips_county` | `int64` | `none` | yes | FIPS county code (eGRID FIPSCNTY). |
| `ba_code` | `string` | `none` | yes | Balancing-authority code (eGRID BACODE). |
| `fuel_cat` | `string` | `none` | yes | Plant primary fuel category (eGRID PLFUELCT). |
| `net_mwh` | `float64` | `mwh` | yes | Plant annual net generation (eGRID PLNGENAN). |
| `co2_tons` | `float64` | `short_tons` | yes | Plant annual CO2 mass, short tons (eGRID PLCO2AN). |

## unit-outage-events

Per-unit CAMPD outage events (one row per detected window). Schema:
[`schema/unit-outage-events.schema.yaml`](schema/unit-outage-events.schema.yaml).

- **Keys:** `iso`, `plant_id`, `unit_id`, `outage_start`
- **Reconciles:** `campd-unit-outages.csv` (ERCOT) /
  `campd-unit-outages-<ISO>.csv` (CAISO/MISO/NEISO/NYISO/PJM) — event grain
  (not hourly-expanded), `iso` stamped at curation.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO the unit is assigned to (stamped at curation). |
| `plant_id` | `int64` | `none` | no | Plant / facility identifier (CAMPD facility_id). |
| `unit_id` | `string` | `none` | no | Generating-unit identifier. |
| `facility_name` | `string` | `none` | yes | Plant / facility name. |
| `unit_capacity_mw` | `float64` | `mw` | yes | The unit's own capacity, the outage's offline MW basis. |
| `plant_capacity_mw` | `float64` | `mw` | yes | The plant's total capacity (denominator for the unit's share). |
| `unit_pct_of_plant` | `float64` | `pct` | yes | unit_capacity_mw as a percent of plant_capacity_mw. |
| `plant_group` | `string` | `none` | yes | Model dispatch-class / asset-group tag (e.g. COAL, CC_REGULAR). |
| `capacity_source` | `string` | `none` | yes | Provenance of unit_capacity_mw (e.g. eia_exact, plant_share). |
| `outage_start` | `datetime64[ns]` | `local_timestamp` | no | Outage window start (tz-naive, CAMPD local reporting clock). |
| `outage_end` | `datetime64[ns]` | `local_timestamp` | no | Outage window end (tz-naive, CAMPD local reporting clock). |
| `duration_days` | `float64` | `days` | yes | Detected outage span in days. |
| `peer_units_online` | `int64` | `none` | yes | Count of the plant's other units still online during the outage. |
| `total_units_at_plant` | `int64` | `none` | yes | Total unit count at the plant. |

## partial-outages

Per-plant CAMPD CF-ceiling partial-outage derate windows. Schema:
[`schema/partial-outages.schema.yaml`](schema/partial-outages.schema.yaml).

- **Keys:** `iso`, `plant_id`, `outage_start`
- **Reconciles:** `campd-partial-outages.csv` (ERCOT) — a multiplicative
  availability `derate_factor` per detected window, `iso` stamped at curation.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO the plant is assigned to (stamped at curation). |
| `plant_id` | `int64` | `none` | no | Plant identifier (CAMPD oris_code). |
| `plant_name` | `string` | `none` | yes | Plant name. |
| `plant_group` | `string` | `none` | yes | Model dispatch-class / asset-group tag. |
| `year` | `int64` | `none` | no | Calendar year the window was detected in. |
| `outage_start` | `datetime64[ns]` | `local_timestamp` | no | Derate window start (tz-naive, CAMPD local reporting clock). |
| `outage_stop` | `datetime64[ns]` | `local_timestamp` | no | Derate window end (tz-naive, CAMPD local reporting clock). |
| `derate_factor` | `float64` | `frac` | no | Multiplicative availability factor during the window (0-1). |

## capacity-deliverability

Per-capacity-area locational capacity requirements and import/export transfer
limits by delivery period. Schema:
[`schema/capacity-deliverability.schema.yaml`](schema/capacity-deliverability.schema.yaml).

- **Keys:** `iso`, `area`, `delivery_year`, `season`, `metric`
- **Reconciles:** PJM CETO/CETL, MISO LRR/LCR/CIL/CEL/ZIA/PRMR, NYISO
  ICAP-req/LCR%/Bulk-Power-Transmission-Limit/IRM, ISO-NE LSR/MCL/interface
  import limit/ICR, CAISO LCR `Capacity Needed`/Maximum Import Capability/PRM —
  onto one canonical metric vocabulary (`requirement`, `import_limit`,
  `export_limit`, `local_clearing_requirement`, `import_ability`,
  `system_requirement`), long form keyed by `(iso, area, delivery_year, season,
  metric)`. ERCOT is excluded (energy-only, no capacity market). See
  [`docs/capacity-deliverability-wiring.md`](../../docs/capacity-deliverability-wiring.md)
  for how the model consumes it (area→zone crosswalk, gated
  `capacity_deliverability_limits`).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO publishing the value (PJM, MISO, NYISO, ISONE, CAISO). |
| `area` | `string` | `none` | no | Capacity area the value applies to — an LDA (PJM), Local Resource Zone (MISO), locality (NYISO), capacity zone (ISO-NE), local capacity area or intertie/branch group (CAISO), or the system/RTO label for system rows. |
| `area_type` | `string` | `none` | no | Kind of area: one of lda \| lrz \| locality \| capacity_zone \| local_area \| branch_group \| rto \| zone (a model/transmission-zone aggregate row, e.g. the CAISO SP26 zonal peak_load that denominates the local-capacity area load share). |
| `delivery_year` | `string` | `none` | no | Delivery/planning/capability/commitment year the value governs, as a label. Planning-year ISOs use "2025/2026" (June/May, May/April, or June/May per ISO); CAISO uses the calendar study year, e.g. "2025". |
| `season` | `string` | `none` | no | Season the value applies to: annual \| summer \| fall \| winter \| spring. Only MISO (seasonal since PY2023-24) uses the four seasons; all other ISOs use "annual". |
| `metric` | `string` | `none` | no | Canonical metric: requirement \| local_clearing_requirement \| import_limit \| export_limit \| import_ability \| system_requirement \| peak_load. (requirement is the CETO analog; import_limit is the CETL analog; peak_load is the area/zone peak-demand forecast published in the same study as the requirement — CAISO LCT "Load+Losses+Pumps" and Table 3.2-1 — pairing with requirement so import_cap = peak_load - requirement sits on one consistent boundary.) |
| `value_mw` | `float64` | `mw` | yes | The value in MW. Null when the ISO publishes this metric only as a ratio. |
| `value_pu` | `float64` | `ratio` | yes | Ratio-form value as a decimal fraction (e.g. 0.810 for an 81.0% LCR or a 1.148 LRR per-unit-of-peak). Null for pure-MW metrics. |
| `source_doc` | `string` | `none` | yes | Authoritative source document (URL or short citation) the value was read from. |
| `source_page` | `string` | `none` | yes | Page / table locator within source_doc. |

## confirmed-retirements

Binding-instrument retirement registry: units whose exit is bound by an
enforceable public instrument, with the instrument's date and full provenance.
Schema:
[`schema/confirmed-retirements.schema.yaml`](schema/confirmed-retirements.schema.yaml).

- **Keys:** `iso`, `plant_id`, `generator_id`, `instrument_id`
- **Reconciles:** PJM deactivation acceptances, MISO Attachment Y approvals,
  NYISO deactivation notices, ISO-NE cleared de-list bids, CAISO SWRCB/CPUC
  orders, ERCOT NSO acceptances, and cross-ISO federal consent decrees / state
  statutes — onto one long frame keyed by `(iso, plant_id, generator_id,
  instrument_id)` with a closed `confirmation_class` vocabulary
  (`rto_deactivation`, `consent_decree`, `statute`, `regulatory_order`,
  `rmr_end`). ANNOUNCED-only retirements (EIA-860 planned dates, IRP/press
  announcements) do NOT belong here — they stay with the economic-retirement
  screen. Superseded rows (a counter-instrument suspends the exit) are kept for
  audit and ignored by the loader. Consumed forecast-forward only by
  `data.confirmed_retirements.load_confirmed_exits` →
  `model.capacity.apply_confirmed_exits` (GATED `confirmed_exits_enabled`,
  default off).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO the unit belongs to (ERCOT/CAISO/PJM/MISO/NYISO/NEISO). |
| `plant_id` | `int64` | `none` | no | EIA plant code (joins the EIA-860 fleet spine). |
| `generator_id` | `string` | `none` | no | EIA-860 generator ID within the plant. |
| `unit_name` | `string` | `none` | yes | Human-readable plant/unit label for review. |
| `capacity_mw` | `float64` | `mw` | yes | Nameplate MW cross-check against EIA-860 (mismatch >5% fails curation). |
| `exit_year` | `int64` | `year` | no | Calendar year the instrument requires the unit offline. |
| `exit_month` | `int64` | `month` | yes | Month (1-12) within exit_year where the instrument specifies one. |
| `confirmation_class` | `string` | `none` | no | One of rto_deactivation \| consent_decree \| statute \| regulatory_order \| rmr_end. Vocabulary is closed; announced/intended is deliberately NOT a member. |
| `instrument_id` | `string` | `none` | no | Short stable slug for the instrument (e.g. pjm-deact-2027-xyz |
| `instrument` | `string` | `none` | no | Full citation — docket/case number |
| `instrument_date` | `datetime64[ns]` | `none` | yes | Date the instrument became binding. |
| `superseded` | `bool` | `none` | no | True when a counter-instrument (RMR |
| `superseding_instrument` | `string` | `none` | yes | Citation of the counter-instrument when superseded. |
| `source_url` | `string` | `none` | no | Authoritative URL of the instrument or the RTO posting row. |
| `source_doc` | `string` | `none` | yes | Document title / page reference within source_url. |
| `accessed` | `datetime64[ns]` | `none` | no | Date the source was last re-queried (the intake vintage stamp). |
| `notes` | `string` | `none` | yes | Free-text context (e.g. partial-plant scope |

## gtc-limits

Measured ERCOT Generic Transmission Constraint hourly limits (stability-limited
export interfaces). Schema:
[`schema/gtc-limits.schema.yaml`](schema/gtc-limits.schema.yaml).

- **Keys:** `iso`, `gtc`, `hour`
- **Reconciles:** ERCOT NP6-86-CD SCED shadow-price / binding-constraint CSVs
  (~5-min) — filtered to GTC rows (empty `FromStation`) and aggregated to the
  fixed non-leap 8760-hour ERCOT-local clock as per-(gtc, hour) mean/min
  enforced limit, active/binding interval counts, and mean positive shadow
  price. Sparse: a row exists only for hours the constraint was in SCED's
  active set. ERCOT-only (published physical transfer limits, rule #13/#14
  admissible).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO code (currently ERCOT). |
| `gtc` | `string` | `none` | no | Constraint name exactly as published in the NP6-86 ConstraintName field (e.g. PNHNDL, WESTEX, NE_LOB, VALEXP). Names follow ERCOT's own GTC vocabulary for the archive's era; the model-side link crosswalk (constants.ERCOT_GTC_LINK_MAP) maps the representable ones. |
| `hour` | `int64` | `hour_index` | no | Index 0-8759 on the fixed non-leap 8760-hour ERCOT-local clock (Feb 29 dropped) — the model's dispatch clock. |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Wall-clock local start of the hour (naive, ERCOT local). |
| `limit_mean_mw` | `float64` | `mw` | no | Mean enforced Limit (MW) over the hour's active SCED intervals. |
| `limit_min_mw` | `float64` | `mw` | no | Minimum enforced Limit (MW) over the hour's active intervals. |
| `n_active` | `int64` | `count` | no | Number of distinct SCED executions in the hour where the constraint was in the active set (nominal cadence 12/hour; the DST fall-back clock hour can carry up to 24). |
| `n_binding` | `int64` | `count` | no | Number of those executions where the constraint was binding (ShadowPrice > 0). |
| `shadow_price_mean` | `float64` | `usd_per_mwh` | yes | Mean ShadowPrice over the hour's binding intervals; null when the constraint was active but never binding that hour. |

## ramp-capability

Measured per-plant 10-minute ramp / fast-start capability inputs for the
reserve co-optimization. Schema:
[`schema/ramp-capability.schema.yaml`](schema/ramp-capability.schema.yaml).

- **Keys:** `iso`, `plant_code`
- **Reconciles:** EIA-860 Schedule 3.1 "Time from Cold Shutdown to Full Load"
  (the "10M" fast-start flag, summed to `fast_start_mw` over
  `thermal_nameplate_mw`) and EPA CAMPD CEMS hourly plant gross load
  (`ramp_up_1h_mw` max observed 1-hour increase, `observed_pmax_mw` max
  observed load) pooled over `vintage_span` 2023-2025 — into one measured
  ceiling on the 10-minute reserve-deliverability bound (`FleetArrays.ramp10`),
  never the 10-minute quantity itself. Never intake 2022/H1-2026 (rule 22).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO whose fleet the plant belongs to (EIA-860 balancing-authority scoping via the per-ISO spec, e.g. PJM, MISO). |
| `plant_code` | `int64` | `none` | no | EIA plant code (ORISPL; CAMPD facilityId). |
| `fast_start_mw` | `float64` | `mw` | yes | Sum of nameplate capacity over the plant's operable thermal generators whose EIA-860 "Time from Cold Shutdown to Full Load" is "10M" (full load within 10 minutes). Null when the plant has no EIA-860 thermal rows (CEMS-only row). |
| `thermal_nameplate_mw` | `float64` | `mw` | yes | Sum of nameplate capacity over the plant's operable thermal generators (combustion/steam prime movers, nuclear excluded). The fast-start share denominator. Null when the plant has no EIA-860 thermal rows. |
| `ramp_up_1h_mw` | `float64` | `mw` | yes | Maximum observed 1-hour increase in plant-level CEMS gross load (units summed per hour; offline unit-hours count as 0 MW; diffs spanning non-consecutive timestamps excluded), pooled over vintage_span. Null when the plant has no CAMPD coverage. |
| `observed_pmax_mw` | `float64` | `mw` | yes | Maximum observed plant-level CEMS gross load over vintage_span (the measured capacity basis guarding stale nameplate against derates). Null when the plant has no CAMPD coverage. |
| `hours_observed` | `int64` | `hours` | no | Count of plant-hours with CEMS coverage pooled over vintage_span (0 for an EIA-860-only row). The model-side loader requires a minimum (market_sim.data.ramp_capability.MIN_OBSERVED_HOURS) before the envelope is trusted. |
| `vintage_span` | `string` | `none` | no | CAMPD vintages pooled for the envelope, e.g. "2023-2025". Holdout periods (2022, 2026) are excluded by construction (CLAUDE.md rule 22). |
| `source_doc` | `string` | `none` | yes | Authoritative source citation for the row's inputs. |

## winter-fuel-inventory

Forward-derivable oil-burn budget drivers for the winter fuel-constrained fleet
(Nov–Mar seasonal scarcity). Schema:
[`schema/winter-fuel-inventory.schema.yaml`](schema/winter-fuel-inventory.schema.yaml).

- **Keys:** `iso`, `entity`, `entity_type`, `season`, `delivery_year`, `metric`
- **Reconciles:** EIA-860 per-plant `Net Winter Capacity with Oil (MW)`
  (multifuel) and `Firing Rate Using Petroleum` (boiler design) — derived
  programmatically — unioned with hand-curated ISO-NE study/program figures
  (OFSA 2018 tank autonomy / fill rate / LNG caps; Winter Reliability Program
  oil-inventory targets; Mystic retention) onto one tidy `(entity, entity_type,
  season, metric, value, unit)` frame. Physical/logistics INPUTS only — never
  measured burn/delivery outcomes (F923 receipts are excluded by design).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO the row applies to (e.g. ISONE). |
| `entity` | `string` | `none` | no | Identifier the value is defined on: an EIA-860 plant code (as a string) for per-plant rows, a program name (e.g. "Mystic_COS", "WRP_2017_18") for program rows, a fuel-class label (e.g. "OIL_STEAM", "DUAL_FUEL_GAS") for fleet-class rows, or an ISO/system label for system-wide study rows. |
| `entity_type` | `string` | `none` | no | Granularity of entity: one of plant \| fleet \| fuel_class \| program \| system. |
| `plant_code` | `int64` | `none` | yes | EIA-860 plant code when entity_type=plant (also parseable from entity); null for fleet/program/system rows. |
| `season` | `string` | `none` | no | Season the value governs: winter (the Nov-Mar fuel-security horizon) or annual (year-round physical attributes such as tank capacity / firing rate that are not season-specific). |
| `delivery_year` | `string` | `none` | no | Vintage / study / winter label the value governs, as a label: an EIA-860 data vintage ("2023"), a winter season ("2017/2018"), or a study year ("2018" for the OFSA). System/study assumptions that are not year-keyed use the source's publication year. |
| `metric` | `string` | `none` | no | Canonical metric. Physical/logistics vocabulary: tank_capacity (on-site oil storage capacity, in bbl/mmbtu or days of autonomy), start_fill (assumed start-of-season oil inventory), delivery_rate (oil re-supply cap in bbl/mmbtu per day or tank fills per winter, or LNG injection in bcf per day), annual_run_limit (permit/environmental annual oil-run cap, days/yr), firing_rate (max physical petroleum burn rate, EIA-860 boiler), oil_limb_capacity (dual-fuel unit's net capacity when burning oil, EIA-860 multifuel), oil_fleet_capacity (fleet/class oil-capable MW from a study), winter_program_capacity (MW retained under a winter-reliability / retention program), season_days (length of the budget horizon), winter_program_member (membership flag in a winter-reliability / retention program; value=1.0, unit=flag). |
| `value` | `float64` | `none` | no | The numeric value, in the units named by the unit column. |
| `unit` | `string` | `none` | no | Physical unit of value: one of mw \| bbl \| bbl_per_hr \| bbl_per_day \| mmbtu \| mmbtu_per_day \| fills_per_season \| bcf_per_day \| days \| flag. The metric<->unit pairing is checked by the curation tidy-validator. |
| `fuel_kind` | `string` | `none` | yes | Oil grade / fuel the row refers to when relevant: distillate (No. 2) \| residual (No. 6) \| oil (unspecified/blended) \| lng \| dual_fuel. Null for fuel-agnostic rows (season_days, program membership). |
| `source_doc` | `string` | `none` | yes | Authoritative source: EIA-860 table + vintage for per-plant rows; the ISO-NE study title/URL for fleet/system rows; the program filing for program rows. |
| `source_page` | `string` | `none` | yes | Page / table / figure locator within source_doc. |

## rggi-co2-budgets

RGGI regional/per-state CO2 allowance budgets and the price-control-band
trigger-price schedule. Schema:
[`schema/rggi-co2-budgets.schema.yaml`](schema/rggi-co2-budgets.schema.yaml).

- **Keys:** `state`, `budget_year`, `metric`
- **Reconciles:** RGGI, Inc. Allowance Distribution tables (regional +
  per-member-state annual budgets, short tons) and the 2017 Model Rule Cost
  Containment Reserve / Emissions Containment Reserve / minimum-reserve trigger
  prices onto one tidy `(state, budget_year, metric, value, unit)` frame. The
  budget feeds the optional power-sector mass-cap row (a scenario, no-bank
  instrument — NOT the RGGI market price); the trigger prices feed the
  projected forecast allowance-price band. Never intake 2022/H1-2026 (rule 22).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `state` | `string` | `none` | no | Two-letter postal code of the RGGI member state (e.g. NY, CT, MA, ME, NH, RI, VT, MD, DE, NJ, VA), or the literal RGGI for the regional aggregate. |
| `budget_year` | `int64` | `year` | no | Allowance control-period calendar year the value applies to. |
| `metric` | `string` | `none` | no | One of allowance_budget \| ccr_trigger_price \| ecr_trigger_price \| minimum_reserve_price. |
| `value` | `float64` | `mixed` | no | The quantity — short tons for allowance_budget, $/short ton for the three price metrics (see the unit column). |
| `unit` | `string` | `none` | no | Unit of value — short_tons or usd_per_short_ton. |
| `source_doc` | `string` | `none` | no | Authoritative RGGI, Inc. document the value is drawn from. |
| `source_page` | `string` | `none` | yes | Table/section/page reference within source_doc. |

## carb-cap-schedule

CARB cap-and-trade annual allowance budget and Auction Reserve floor-price
schedule. Schema:
[`schema/carb-cap-schedule.schema.yaml`](schema/carb-cap-schedule.schema.yaml).

- **Keys:** `budget_year`, `metric`
- **Reconciles:** CARB Cap-and-Trade Regulation §95841 annual allowance budgets
  (MMT CO2e) and the §95911(c) Auction Reserve (floor) price with its 5% + CPI
  escalation onto one tidy `(budget_year, metric, value, unit)` frame. The
  budget feeds the optional power-sector mass-cap row (a scenario, no-bank
  instrument — NOT the CARB market price); the floor escalator feeds the
  projected forecast allowance price for CAISO. Never intake 2022/H1-2026 (rule
  22).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `budget_year` | `int64` | `year` | no | Budget calendar year the value applies to. |
| `metric` | `string` | `none` | no | One of allowance_budget \| auction_reserve_price. |
| `value` | `float64` | `mixed` | no | The quantity — MMT CO2e for allowance_budget, $/tonne for auction_reserve_price (see the unit column). |
| `unit` | `string` | `none` | no | Unit of value — mmt_co2e or usd_per_tonne. |
| `source_doc` | `string` | `none` | no | Authoritative CARB document the value is drawn from. |
| `source_page` | `string` | `none` | yes | Section/table/page reference within source_doc. |

## chp-btm-share

Measured per-plant CHP behind-the-meter host self-supply share (replaces the
sector-keyed chp_btm_pct default for forecast years). Schema:
[`schema/chp-btm-share.schema.yaml`](schema/chp-btm-share.schema.yaml).

- **Keys:** `iso`, `plant_id`, `plant_group`
- **Reconciles:** The committed `plant_emission_rates_v2` (CAMPD CEMS grid-net
  generation, steam-reporting units only) and `eia923_monthly_generation`
  (EIA-923 Page-1 net class generation) processed-legacy artifacts — into one
  `btm_share = (eia923_net_mwh - campd_net_mwh) / eia923_net_mwh` per (iso,
  plant, CHP class), pooled across every available non-quarantined year.
  Consumed by `market_sim.data.chp.measured_btm_share_by_plant` for
  forecast-year CHP must-run sizing only; the backcast `_btm_frame` path is
  untouched. Never intake 2022/H1-2026 (rule 22).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO the plant is assigned to (a border-state plant may appear under more than one). |
| `plant_id` | `int64` | `none` | no | EIA plant code (CAMPD facilityId / EIA-923 Plant Id). |
| `plant_group` | `string` | `none` | no | Model CHP class — CC_CHP, CT_CHP or ST_CHP. |
| `eia923_net_mwh` | `float64` | `mwh` | no | Summed EIA-923 Page-1 net generation for this plant/class across every year pooled into the share (gross minus station service; includes host self-consumption). |
| `campd_net_mwh` | `float64` | `mwh` | no | Summed CAMPD CEMS grid-net generation for this plant/class across the same pooled years, restricted to steam-reporting units (net of parasitic/station-service load via the v2 emission-rate artifact). |
| `btm_share` | `float64` | `ratio` | no | (eia923_net_mwh - campd_net_mwh) / eia923_net_mwh, clipped to [0, 1]. |
| `steam_load_klbh_sum` | `float64` | `klb` | no | Summed CAMPD steam load (1000 lb/hr) across the plant/class's steam-reporting units and pooled years — the CHP signature evidencing the plant is a genuine cogen, kept for audit. |
| `n_years` | `int64` | `none` | no | Count of distinct years pooled into this row's totals. |
| `first_year` | `int64` | `none` | no | Earliest calendar year contributing to this row. |
| `last_year` | `int64` | `none` | no | Latest calendar year contributing to this row. |

## ramp-capability

Measured per-plant 10-minute ramp / fast-start capability inputs for the
per-generator reserve co-optimization. Schema:
[`schema/ramp-capability.schema.yaml`](schema/ramp-capability.schema.yaml).

- **Keys:** `iso`, `plant_code`
- **Reconciles:** EIA-860 Schedule 3.1 `Time from Cold Shutdown to Full Load`
  (the `10M` fast-start category → `fast_start_mw` over the plant's thermal
  nameplate `thermal_nameplate_mw`) and EPA CAMPD CEMS hourly unit gross load
  (the maximum observed 1-hour plant-level up-ramp → `ramp_up_1h_mw`, plus
  `observed_pmax_mw` and `hours_observed`) — reconciled per plant (EIA plant
  code = CAMPD facilityId) onto one tidy frame, pooled 2023-2025 (holdouts
  excluded, rule 22). Per-ISO scoping is the balancing-authority spec in
  `scripts/lib/ramp_capability/<iso>.py` (PJM, MISO, CAISO). Consumed as the
  measured ceiling on the class-rate estimate feeding `FleetArrays.ramp10`, the
  10-minute reserve-deliverability bound.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO whose fleet the plant belongs to (EIA-860 balancing-authority scoping via the per-ISO spec, e.g. PJM, MISO). |
| `plant_code` | `int64` | `none` | no | EIA plant code (ORISPL; CAMPD facilityId). |
| `fast_start_mw` | `float64` | `mw` | yes | Sum of nameplate capacity over the plant's operable thermal generators whose EIA-860 "Time from Cold Shutdown to Full Load" is "10M" (full load within 10 minutes). Null when the plant has no EIA-860 thermal rows (CEMS-only row). |
| `thermal_nameplate_mw` | `float64` | `mw` | yes | Sum of nameplate capacity over the plant's operable thermal generators (combustion/steam prime movers, nuclear excluded). The fast-start share denominator. Null when the plant has no EIA-860 thermal rows. |
| `ramp_up_1h_mw` | `float64` | `mw` | yes | Maximum observed 1-hour increase in plant-level CEMS gross load (units summed per hour; offline unit-hours count as 0 MW; diffs spanning non-consecutive timestamps excluded), pooled over vintage_span. Null when the plant has no CAMPD coverage. |
| `observed_pmax_mw` | `float64` | `mw` | yes | Maximum observed plant-level CEMS gross load over vintage_span (the measured capacity basis guarding stale nameplate against derates). Null when the plant has no CAMPD coverage. |
| `hours_observed` | `int64` | `hours` | no | Count of plant-hours with CEMS coverage pooled over vintage_span (0 for an EIA-860-only row). The model-side loader requires a minimum (market_sim.data.ramp_capability.MIN_OBSERVED_HOURS) before the envelope is trusted. |
| `vintage_span` | `string` | `none` | no | CAMPD vintages pooled for the envelope, e.g. "2023-2025". Holdout periods (2022, 2026) are excluded by construction (CLAUDE.md rule 22). |
| `source_doc` | `string` | `none` | yes | Authoritative source citation for the row's inputs. |
