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

> **Per-column detail is auto-filled in W5** from the schema YAMLs. The tables
> below are skeletons: one section per datatype with its purpose, keys and the
> ISO×year coverage matrix. Do not hand-maintain per-column rows here — edit the
> schema YAML and let W5 regenerate.

## Regenerate from raw

The clean tree is derived and disposable; it is rebuilt from `data/raw` by the
per-datatype curation scripts (`scripts/curate_*.py`, added per session), each
calling `clean_io.write_clean(df, datatype, ...)`. To regenerate a datatype,
re-run its curation script; to verify an existing file round-trips against its
embedded schema, call `clean_io.validate_clean(path)`. Raw inputs are described
in [`../README.md`](../README.md) and are never modified in place.

## ISO coverage matrix

Legend: ✓ available · — not applicable / not collected · _(blank)_ to be
confirmed during curation. Years shown are the backcast window; extend as raw
data lands.

| datatype | ERCOT | CAISO | PJM | MISO | SPP | NYISO | NEISO | years |
|---|---|---|---|---|---|---|---|---|
| lmp | | ✓ | ✓ | | | ✓ | ✓ | 2023–2025 |
| load | | ✓ | | | | ✓ | | 2023–2025 |
| ancillary-services | ✓ | ✓ | ✓ | | | ✓ | | 2023–2025 |
| generation | | ✓ | ✓ | | | | | 2022–2025 |
| renewables | ✓ | ✓ | | | | | | 2023–2025 |
| emissions | national (CAMPD, by plant/unit) | 2023–2025 |
| outages | derived from emissions + curated lists | 2023 |
| validation | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 2023–2025 |
| fleet | national (EIA-860 / eGRID / registry) | 2023–2025 |
| fuel-prices | national hubs (Henry Hub + citygate/basis) | 2023–2025 |
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

_Per-column table: W5._

## load

Hourly demand and forecast by zone. Schema:
[`schema/load.schema.yaml`](schema/load.schema.yaml).

- **Keys:** `iso`, `zone`, `interval_start_utc`
- **Reconciles:** CAISO TAC-area `mw`, NYISO `Load`, EIA-930 `Demand` /
  `Demand forecast` — into `load_mw`, `load_forecast_mw`, optional `net_load_mw`.

_Per-column table: W5._

## ancillary-services

AS clearing prices and cleared quantities. Schema:
[`schema/ancillary-services.schema.yaml`](schema/ancillary-services.schema.yaml).

- **Keys:** `iso`, `zone`, `market`, `interval_start_utc`
- **Reconciles:** NYISO `spin_10/nonsync_10/op_30/reg_cap`, PJM long
  `ancillary_service/value`, ERCOT `REGUP/REGDN/RRS/ECRS/NSPIN`, CAISO
  `RU/RD/SR/NR` — onto a common product taxonomy (reg up/down, spin, nonspin,
  30-min supplemental), prices in `$/MW`.

_Per-column table: W5._

## generation

Generation by fuel (long form). Schema:
[`schema/generation.schema.yaml`](schema/generation.schema.yaml).

- **Keys:** `iso`, `zone`, `fuel`, `interval_start_utc`
- **Reconciles:** EIA-930 wide `NG: *` fuel columns (unpivoted), PJM
  `fuel_type/mw/is_renewable`, CAISO technology buckets.

_Per-column table: W5._

## renewables

Renewable output, availability (HSL) and curtailment. Schema:
[`schema/renewables.schema.yaml`](schema/renewables.schema.yaml).

- **Keys:** `iso`, `zone`, `fuel`, `interval_start_utc`
- **Reconciles:** CAISO/ERCOT HSL `wind_gen_mw/wind_hsl_mw/solar_*` (unpivoted),
  CAISO curtailment — into `generation_mw`, `hsl_mw`, `curtailment_mw`.

_Per-column table: W5._

## emissions

Hourly CEMS/CAMPD emissions by plant/unit. Schema:
[`schema/emissions.schema.yaml`](schema/emissions.schema.yaml).

- **Keys:** `plant_id`, `unit_id`, `interval_start_utc`
- **Reconciles:** CAMPD facility- and unit-level `co2Mass/noxMass/so2Mass/
  heatInput/grossLoad` — masses standardized to `*_kg`, heat input to MMBtu.

_Per-column table: W5._

## outages

Generator outages / available capacity. Schema:
[`schema/outages.schema.yaml`](schema/outages.schema.yaml).

- **Keys:** `plant_id`, `unit_id`, `interval_start_utc`
- **Reconciles:** CAMPD-derived downtime, ERCOT curated unit-outage lists —
  into `outage_mw` / `available_mw`.

_Per-column table: W5._

## validation

Calibration/validation reference targets (tidy long form). Schema:
[`schema/validation.schema.yaml`](schema/validation.schema.yaml).

- **Keys:** `iso`, `zone`, `year`, `month`, `fuel`, `metric`
- **Reconciles:** heterogeneous `_validation-source` benchmark files (renewable
  capacity, generation, emissions, price) into `(dimensions → metric, value,
  unit)`.

_Per-column table: W5._

## fleet

Generator fleet registry. Schema:
[`schema/fleet.schema.yaml`](schema/fleet.schema.yaml).

- **Keys:** `plant_id`, `unit_id`
- **Reconciles:** EIA-860 (`Plant Code`, `Generator ID`, `Nameplate Capacity
  (MW)`, …), master plant registry, eGRID — into snake_case + unit-suffixed
  columns.

_Per-column table: W5._

## fuel-prices

Delivered fuel price benchmarks. Schema:
[`schema/fuel-prices.schema.yaml`](schema/fuel-prices.schema.yaml).

- **Keys:** `fuel`, `hub`, `interval_start_utc`
- **Reconciles:** Henry Hub daily `price_usd_mmbtu`, citygate/basis benchmarks —
  into `price_usd_per_mmbtu` by `fuel`/`hub`.

_Per-column table: W5._

## reference

Crosswalk / lookup tables (heterogeneous). Schema:
[`schema/reference.schema.yaml`](schema/reference.schema.yaml).

- **Keys:** `key` (+ `plant_id`/`iso`/`zone`/`node` when applicable)
- **Reconciles:** master plant registry, bin assignments, zone/node crosswalks —
  conventions enforced, table-specific columns permitted.

_Per-column table: W5._
