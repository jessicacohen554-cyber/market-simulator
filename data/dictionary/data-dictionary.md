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
per-datatype curation scripts (`scripts/data/curate_*.py`, added per session), each
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

| datatype | ERCOT | CAISO | PJM | MISO | NYISO | NEISO | SPP | SOCO |
|---|---|---|---|---|---|---|---|---|
| lmp | — | — | — | — | — | — | — | — |
| lmp-components | — | — | — | — | — | — | — | — |
| load | — | — | — | — | — | — | — | — |
| demand-profile | — | — | — | — | — | — | — | — |
| ancillary-services | — | — | — | — | — | — | — | — |
| energy-offers | — | — | — | — | — | — | — | — |
| dam-public-bids | — | — | — | — | — | — | — | — |
| generation | — | — | — | — | — | — | — | — |
| renewables | — | — | — | — | — | — | — | — |
| validation | — | — | — | — | — | — | — | — |
| fuel-basis | — | — | — | — | — | — | — | — |
| fuel-zonal-hub | — | — | — | — | — | — | — | — |
| unit-outage-events | — | — | — | — | — | — | — | — |
| partial-outages | — | — | — | — | — | — | — | — |
| capacity-deliverability | — | — | — | — | — | — | — | — |
| confirmed-retirements | — | — | — | — | — | — | — | — |
| nuclear-license-status | — | — | — | — | — | — | — | — |
| gtc-limits | — | — | — | — | — | — | — | — |
| transfer-interface-limits | — | — | — | — | — | — | — | — |
| transmission-expansion | — | — | — | — | — | — | — | — |
| ramp-capability | — | — | — | — | — | — | — | — |
| winter-fuel-inventory | — | — | — | — | — | — | — | — |
| chp-btm-share | — | — | — | — | — | — | — | — |
| nyiso-downstate-gas | — | — | — | — | — | — | — | — |
| ercot-wtx-congestion | — | — | — | — | — | — | — | — |
| nyiso-renewable-curtailment | — | — | — | — | — | — | — | — |
| nyiso-renewable-curtailment-monthly | — | — | — | — | — | — | — | — |
| nyiso-reserve-requirements | — | — | — | — | — | — | — | — |
| nyiso-operating-events | — | — | — | — | — | — | — | — |
| nyiso-interface-flows | — | — | — | — | — | — | — | — |
| nyiso-som-hub-fuel-annual | — | — | — | — | — | — | — | — |
| reserve-requirements | — | — | — | — | — | — | — | — |
| som-competitive-conduct | — | — | — | — | — | — | — | — |
| capacity-market-demand-curve | — | — | — | — | — | — | — | — |
| capacity-market-auction-price | — | — | — | — | — | — | — | — |
| capacity-market-auction-supply | — | — | — | — | — | — | — | — |
| capacity-market-elcc | — | — | — | — | — | — | — | — |
| transfer-constraint-binding | — | — | — | — | — | — | — | — |
| maxgen-events | — | — | — | — | — | — | — | — |
| storage-as-awards | — | — | — | — | — | — | — | — |
| capacity-market-avoidable-cost-rate | — | — | — | — | — | — | — | — |
| benchmark-corridor | — | — | — | — | — | — | — | — |
| hydro-plant-modes | — | — | — | — | — | — | — | — |
| miso-m2m-flowgates | — | — | — | — | — | — | — | — |
| gas-ofo-events | — | — | — | — | — | — | — | — |
| ps-water-state | — | — | — | — | — | — | — | — |
| ra-import-allocations | — | — | — | — | — | — | — | — |
| load-forecast | — | — | — | — | — | — | — | — |

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
| wecc-west-supply | — | n/a |
| zonal-shares | per-ISO via directory partitioning | n/a |
| weather | per-ISO via directory partitioning | n/a |
| egrid | national (EPA eGRID, by vintage year) | n/a |
| pjm-outages | — | n/a |
| rggi-co2-budgets | — | n/a |
| carb-cap-schedule | — | n/a |
| coal-basin-price | national/regional (EIA Annual Coal Report, by producing region) | n/a |
| coal-mining-ppi | national (BLS PPI, coal) | n/a |
| coal-stocks | national (EIA-923 Schedule 2, by plant) | n/a |
| coal-receipts | national (EIA-923 Page 5, by plant) | n/a |
| carbon-auction-results | — | n/a |
| eia-aeo-fuel-prices | — | n/a |
| ira-credit-parameters | — | n/a |
| nrel-atb | — | n/a |
| uranium-marketing-price | — | n/a |

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

## lmp-components

Per-node LMP component decomposition (energy / congestion / loss) from an ISO's
published ex-post price reports — kept separate from `lmp` (the cross-ISO
benchmark contract): this is the derive source for the MISO marginal
delivery-factor (loss) surface and for congestion-vs-loss decomposition
validation. Schema:
[`schema/lmp-components.schema.yaml`](schema/lmp-components.schema.yaml).

- **Keys:** `iso`, `market`, `node`, `interval_start_utc`
- **Reconciles:** MISO daily all-node market reports
  (`YYYYMMDD_da_expost_lmp.csv` / RT equivalents) onto one tidy row per (node,
  market, interval) carrying the lmp/mec/mcc/mlc split; first (and so far only)
  registered ISO: MISO.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO code (MISO; other ISOs register their own modules). |
| `market` | `string` | `none` | no | Market run — "da" (day-ahead ex-post) or "rt" (real-time final), matching the sibling MISO market-report datatype vocabulary (transfer-constraint-binding). |
| `node` | `string` | `none` | no | Pricing node exactly as posted (e.g. "MINN.HUB"). Current MISO holding covers the eight named trading hubs (scope decision D6). |
| `node_type` | `string` | `none` | yes | Source node-type column as posted ("Hub" for the hub set). |
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC start of the hour (hour-beginning). Source hours are hour-ending 1-24 in EST year-round (UTC-5 fixed, no DST), so UTC = market date + (HE-1) hours + 5 hours. |
| `interval_start_est` | `datetime64[ns]` | `local_timestamp` | yes | EST hour-beginning wall clock as posted (informational; UTC is authoritative for joins). MISO market time is EST year-round. |
| `lmp_usd_per_mwh` | `float64` | `usd_per_mwh` | yes | Total locational marginal price as posted (blank source cells stay null — values are verbatim, never imputed). |
| `mcc_usd_per_mwh` | `float64` | `usd_per_mwh` | yes | Marginal congestion component (MCC) as posted. |
| `mlc_usd_per_mwh` | `float64` | `usd_per_mwh` | yes | Marginal loss component (MLC) as posted. |

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

- **Keys:** `iso`, `market`, `unit_code`, `interval_start_utc`, `step_idx`
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
| `iso` | `string` | `none` | no | ISO the offer was submitted into — "PJM" or "MISO". |
| `market` | `string` | `none` | no | Market the offer set belongs to — "DA" (day-ahead) or "RT" (real-time). PJM's DataMiner2 feed is the RT effective offer set, so PJM rows are always "RT"; MISO publishes both books as separate daily files. DA and RT are SEPARATE INSTRUMENTS and must never be averaged together. |
| `unit_code` | `string` | `none` | no | Anonymised unit identifier assigned by the ISO. PJM: base64-encoded, ROTATED ANNUALLY — codes are NOT comparable across calendar years. MISO: the masked ``Unit Code``, PERSISTENT across days and years (miso-136 measured 92–99 % overlap across 2023↔2024↔2025), so per-unit longitudinal statistics are meaningful for MISO but not for PJM. |
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
| `region` | `string` | `none` | yes | MISO market Region the unit sits in — "North", "Central" or "South" (MISO ``Region``). The only locational attribute the masked corpus publishes; it is a market region, NOT a model zone, and no zone crosswalk is asserted from it. |
| `economic_flag` | `bool` | `none` | yes | MISO ``Economic Flag`` — the unit declared itself economically dispatchable for the hour. |
| `emergency_flag` | `bool` | `none` | yes | MISO ``Emergency Flag`` — emergency range offered for the hour. |
| `must_run_flag` | `bool` | `none` | yes | MISO ``Must Run Flag`` — the unit declared a must-run commitment status for the hour. A declaration, not an outcome. |
| `unit_available_flag` | `bool` | `none` | yes | MISO ``Unit Available Flag`` — the unit declared itself available to the market for the hour. |
| `self_scheduled_mw` | `float64` | `mw` | yes | MISO ``Self Scheduled MW`` — MW the participant self-scheduled (price taker) for the hour. A submitted quantity, not an award. |
| `emergency_max_mw` | `float64` | `mw` | yes | MISO ``Emergency Max`` — declared emergency upper limit (MW). |
| `emergency_min_mw` | `float64` | `mw` | yes | MISO ``Emergency Min`` — declared emergency lower limit (MW). |
| `curtailment_offer_price_usd_per_mwh` | `float64` | `usd_per_mwh` | yes | MISO ``Curtailment Offer Price`` — the price at which a dispatchable intermittent / demand resource offers curtailment ($/MWh). |
| `min_energy_storage_level_mwh` | `float64` | `mwh` | yes | MISO ``MinEnergyStorageLevel`` — declared minimum state-of-charge for an electric storage resource (MWh). Populated for storage rows only, and therefore also serves as the storage-row screen. |
| `max_energy_storage_level_mwh` | `float64` | `mwh` | yes | MISO ``MaxEnergyStorageLevel`` — declared maximum SOC (MWh). |

## dam-public-bids

ISO day-ahead-market public bid data (as-submitted energy bid curves per
scheduling resource), published with the ISO's own masking/lag policy — the
measured offer-surface source. Schema:
[`schema/dam-public-bids.schema.yaml`](schema/dam-public-bids.schema.yaml).

- **Keys:** `iso`, `trade_date`, `resource_seq`, `product`,
  `interval_start_utc`, `row_kind`, `step_idx`
- **Reconciles:** CAISO OASIS Public Bid Data GroupZip archives (one zip per
  DAM trade date, 90-day publication lag) onto one tidy row per (resource,
  OPERATING HOUR, product, bid segment) — the raw disclosure is
  run-length-encoded over hours and every parser expands its ranges before
  assigning step_idx (caiso-152); first (and so far only) registered ISO:
  CAISO.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO whose DAM produced the bid ("CAISO"). |
| `trade_date` | `datetime64[ns]` | `local_date` | no | DAM trade date (= operating date) as a tz-naive local calendar day (midnight-normalized). Maps to the OASIS STARTDATE field. |
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC start of the ONE operating hour the bid row applies to. Curve rows: SCH_BID_TIMEINTERVALSTART_GMT; self-schedule rows: TIMEINTERVALSTART_GMT — in both cases the raw range is expanded to one row per hour up to its matching STOP/END stamp (see the header), so this is an hour, never a multi-hour range start. |
| `resource_type` | `string` | `none` | no | OASIS RESOURCE_TYPE — GENERATOR, LOAD (participating load), or INTERTIE (import/export bid at a scheduling point). |
| `sc_seq` | `int64` | `none` | yes | Masked scheduling-coordinator sequence id (SCHEDULINGCOORDINATOR_SEQ). Informational; persistent. |
| `resource_seq` | `int64` | `none` | no | Masked resource sequence id (RESOURCEBID_SEQ). Persistent across days and years — the longitudinal join key for per-resource statistics. |
| `product` | `string` | `none` | no | OASIS MARKETPRODUCTTYPE — EN (energy), SR (spinning reserve), NR (non-spinning reserve), RU/RD (regulation up/down), RMU/RMD (regulation mileage up/down), RC (RUC availability), LFU/LFD (load-following up/down). |
| `row_kind` | `string` | `none` | no | "segment" for a priced bid-curve breakpoint; "self_sched" for a price-taker self-schedule quantity. |
| `step_idx` | `int64` | `none` | no | 1-based breakpoint index within the (resource_seq, product, interval_start_utc) bid curve, ordered by ascending segment_mw (file order for ties and for self-schedule rows). |
| `self_sched_mw` | `float64` | `mw` | yes | Self-scheduled (price-taker) MW for row_kind="self_sched" rows (OASIS SELFSCHEDMW); null on curve rows. |
| `segment_mw` | `float64` | `mw` | yes | Cumulative MW level (bid-curve x-axis, OASIS SCH_BID_XAXISDATA) at which segment_price_usd_per_mwh starts to apply; may be negative for withdrawal-capable resources. Null on self-schedule rows. |
| `segment_price_usd_per_mwh` | `float64` | `usd_per_mwh` | yes | Bid price for this breakpoint in $/MWh (OASIS SCH_BID_Y1AXISDATA). CAISO energy bid caps apply (-$150 floor / +$1,000 soft cap / +$2,000 hard cap). Null on self-schedule rows. |
| `curve_type` | `string` | `none` | yes | OASIS SCH_BID_CURVETYPE for curve rows (observed: BIDPRICE); null on self-schedule rows. |

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
| `hub` | `string` | `none` | no | Border hub identifier. CAISO: MALIN (COI/PDCI PNW scheduling point), PALOVRDE (Path-46 desert-SW scheduling point). MISO: PJM_WEST (equal-weight mean of CHICAGO GEN / AEP GEN / ATSI GEN hubs). NEISO: NYISO_HQ (NYISO "H Q" proxy bus — HQ's measured alternative- market price), NYISO_NPX (NYISO "NPX" proxy bus — the NY-side price at the NY-NE interface). |
| `price` | `float64` | `usd_per_mwh` | yes | Day-Ahead total LMP ($/MWh). CAISO: energy + congestion + loss (MCE+MCC+MCL), GHG excluded (re-added per-tranche by the injector). MISO/PJM: total_lmp_da (energy + congestion + loss). NEISO: NYISO zonal "LBMP ($/MWHr)" at the proxy buses. NaN for hours with no data (OASIS retention gap, missing source). |

## wecc-west-supply

WECC-West neighbor hourly balance (EIA-930 BALANCE Region NW + SW aggregate):
the measured hourly net position of the western interconnect outside CAISO —
demand, per-fuel generation and `net_export_mw` on the UTC clock — the
foundation of the co-optimized WECC_import node (caiso-110 lane). Schema:
[`schema/wecc-west-supply.schema.yaml`](schema/wecc-west-supply.schema.yaml).

- **Keys:** `interval_start_utc`
- **Reconciles:** EIA-930 BALANCE Region NW + SW hourly files onto one
  clock-neutral UTC-keyed row per hour; the LP wiring aligns UTC onto the CAISO
  model clock via the same map the corridor loaders use.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC start of the hour. |
| `demand_mw` | `float64` | `mw` | no | WECC-West aggregate demand (adjusted) over the hour. |
| `solar_mw` | `float64` | `mw` | no | WECC-West aggregate solar net generation (adjusted, all solar sub-types). |
| `wind_mw` | `float64` | `mw` | no | WECC-West aggregate wind net generation (adjusted, all wind sub-types). |
| `hydro_mw` | `float64` | `mw` | no | WECC-West aggregate hydro net generation (adjusted; incl. pumped storage where the source aggregates it). |
| `gas_mw` | `float64` | `mw` | yes | WECC-West aggregate natural-gas net generation (adjusted). |
| `coal_mw` | `float64` | `mw` | yes | WECC-West aggregate coal net generation (adjusted). |
| `nuclear_mw` | `float64` | `mw` | yes | WECC-West aggregate nuclear net generation (adjusted). |
| `net_generation_mw` | `float64` | `mw` | no | WECC-West aggregate total net generation (adjusted). |
| `net_export_mw` | `float64` | `mw` | no | Derived West net export = net_generation - demand (may be negative). The West's measured net interchange position — the quantity the co-optimized WECC_import zone (Option A) must reproduce. NOTE: renewables alone never exceed West demand (solar ~3-5 GW vs demand ~70 GW), so a "clean surplus over demand" is degenerately zero — the West's export to CAISO is a price/congestion outcome, not a renewable-surplus threshold (design §3). |

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
| `outage_start_hour` | `int64` | `none` | yes | OPTIONAL (caiso-183). Hour-of-day 0-23 of the window's first DETECTED outage hour. The detector works in hours but outage_start stores a date, so without this column a consumer must re-expand the window from 00:00 and asserts up to 23 h it never detected. Present only in extracts derived with derive_campd_unit_outages.py --hour-grain; consumers fall back to the day-granular reconstruction when it is absent, which is why it is nullable/optional rather than required. |
| `outage_end_hour` | `int64` | `none` | yes | OPTIONAL (caiso-183). Hour-of-day 0-23 of the window's LAST detected outage hour, inclusive — so the return-to-service instant is outage_end + (outage_end_hour + 1) hours. Absent means 23, i.e. the incumbent outage_end + 1 day. |
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

## pjm-outages

PJM generation-outage forecast by type and region (Data Miner 2
`gen_outages_by_type`): the daily-posted active/approved MW on outage for the
operating day + six days, split forced / maintenance / planned — PJM's
published DAM-horizon capacity-availability quantity. Schema:
[`schema/pjm-outages.schema.yaml`](schema/pjm-outages.schema.yaml).

- **Keys:** `forecast_execution_date`, `forecast_date`, `region`
- **Reconciles:** Data Miner 2 seven-day outage-by-type feeds onto one tidy row
  per (forecast_execution_date, forecast_date, region) — Mid Atlantic–Dominion,
  Western, and the PJM RTO total.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `forecast_execution_date` | `string` | `date` | no | Calendar date (EPT, YYYY-MM-DD) the outage forecast was posted by PJM. |
| `forecast_date` | `string` | `date` | no | Delivery date (EPT, YYYY-MM-DD) the outage MW pertains to. Equals forecast_execution_date on the current-day actual row (lead_days == 0). |
| `lead_days` | `int64` | `days` | no | forecast_date - forecast_execution_date, an integer 0..6. lead_days == 0 is the current-day actual outage; 1..6 are the forward scheduled-outage forecast for the seven-day horizon. |
| `region` | `string` | `none` | no | PJM outage region, closed vocabulary: "Mid Atlantic - Dominion", "Western", or "PJM RTO". The RTO total equals the two sub-regions summed (verified to <= 1 MW residual by the deriver). |
| `total_outages_mw` | `float64` | `mw` | no | Total active/approved MW on outage = planned + maintenance + forced (verified to sum by the deriver). Always >= 0. |
| `planned_outages_mw` | `float64` | `mw` | no | Scheduled (planned) outage MW -- dominated by scheduled nuclear refuel and fossil maintenance. Always >= 0. Excluded from the default availability transform to avoid double-counting the nuclear refuel the nuclear overlay already carries. |
| `maintenance_outages_mw` | `float64` | `mw` | yes | Maintenance outage MW. Carries occasional small negatives (a PJM reconciliation artifact where MW is reclassified between categories); preserved verbatim (rule 11) since the three components still sum to total. |
| `forced_outages_mw` | `float64` | `mw` | no | Forced (unplanned) outage MW. Always >= 0. With maintenance, the UNPLANNED component the default availability transform uses (the measured analogue of the statistical forced-outage / EFOR rate). |

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
| `metric` | `string` | `none` | no | Canonical metric: requirement \| local_clearing_requirement \| import_limit \| export_limit \| import_ability \| system_requirement \| peak_load \| transfer_security_limit. (requirement is the CETO analog; import_limit is the CETL analog; peak_load is the area/zone peak-demand forecast published in the same study as the requirement — CAISO LCT "Load+Losses+Pumps" and Table 3.2-1 — pairing with requirement so import_cap = peak_load - requirement sits on one consistent boundary. transfer_security_limit is the area boundary's N-1-1 transmission transfer capability BEFORE any capacity-market loss-of-source deduction: where an ISO publishes both, import_limit is the capacity-adequacy accounting term that a locational requirement is computed against, while transfer_security_limit is the transfer capability itself and is the one an hourly energy bound needs. NYISO Zone K is the reference case — import_limit 275 MW = transfer_security_limit 940 MW - 660 MW Neptune HVDC loss-of-source, from one table and its own footnote; see the nyiso raw README.) |
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
| `superseding_instrument_date` | `datetime64[ns]` | `none` | yes | Date the counter-instrument (superseding_instrument) became binding |
| `source_url` | `string` | `none` | no | Authoritative URL of the instrument or the RTO posting row. |
| `source_doc` | `string` | `none` | yes | Document title / page reference within source_url. |
| `accessed` | `datetime64[ns]` | `none` | no | Date the source was last re-queried (the intake vintage stamp). |
| `notes` | `string` | `none` | yes | Free-text context (e.g. partial-plant scope |

## nuclear-license-status

Nuclear fleet forward-lifetime registry: one row per operating (or
restart-pathway) reactor unit in the six modeled ISOs — NRC license expiration
and stage, SLR status/docket, announced uprates, restart pathways — the
forward-lifetime grounding for clean-firm supply. Schema:
[`schema/nuclear-license-status.schema.yaml`](schema/nuclear-license-status.schema.yaml).

- **Keys:** `iso`, `eia_plant_id`, `unit`
- **Reconciles:** NRC license/SLR dockets, licensee announcements and state
  instruments onto one unit-level registry; rows with a binding exit instrument
  live in `confirmed-retirements` and are cross-referenced, never duplicated.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO the unit belongs to (ERCOT/CAISO/PJM/MISO/NYISO/NEISO). |
| `plant_name` | `string` | `none` | no | EIA-860 plant name (human-readable; not the join key). |
| `unit` | `string` | `none` | no | EIA-860 generator ID within the plant (also the NRC unit number for nuclear; joins the fleet spine's generator_id). |
| `eia_plant_id` | `int64` | `none` | no | EIA plant code (joins the EIA-860 fleet spine and data/raw/reference/master-plant-registry.csv `plantid`). |
| `capacity_mw` | `float64` | `mw` | yes | Nameplate MW cross-check against EIA-860 (mismatch >5% fails curation) |
| `nrc_docket` | `string` | `none` | yes | NRC docket number (50-xxx) for the unit's operating license. |
| `license_issued_date` | `datetime64[ns]` | `none` | yes | Date the current (renewed |
| `current_license_expiry` | `datetime64[ns]` | `none` | yes | Current NRC operating-license EXPIRATION date (reflects any initial renewal or SLR already granted). The federal license ceiling — a state ceiling (e.g. CA SB 846 for Diablo Canyon) is captured in retirement_announcement / the confirmed-retirements registry |
| `license_stage` | `string` | `none` | no | One of original \| renewed_60 \| slr_granted_80. Closed vocabulary. `original` = still on the initial 40-yr license; `renewed_60` = initial license renewal granted (to 60 yr); `slr_granted_80` = Subsequent License Renewal granted (to 80 yr). |
| `license_instrument` | `string` | `none` | yes | Citation of the operating-license / renewal instrument (NRC renewed license number |
| `slr_status` | `string` | `none` | no | One of granted \| under_review \| announced_intent \| none. Closed vocabulary. `granted` implies license_stage slr_granted_80; `under_review` = SLR application docketed/accepted; `announced_intent` = licensee has publicly stated intent to file; `none` = no SLR pathway (the case closest to a confirmed license-expiry exit — see the design memo). |
| `slr_docket` | `string` | `none` | yes | NRC SLR application docket / ADAMS accession |
| `slr_instrument` | `string` | `none` | yes | Citation of the SLR instrument (application |
| `slr_instrument_date` | `datetime64[ns]` | `none` | yes | Date of the SLR instrument (application-accepted date for under_review; issuance date for granted). |
| `announced_uprate_mw` | `float64` | `mw` | yes | ANNOUNCED (not-yet-implemented / not-yet-in-nameplate) power uprate in MW-electric. Historical uprates already baked into `capacity_mw` are NOT recorded here (they are context in the methodology doc). Null when no forward uprate is announced. |
| `uprate_status` | `string` | `none` | yes | One of approved \| under_review \| announced_intent \| none |
| `uprate_instrument` | `string` | `none` | yes | Citation of the forward-uprate instrument (NRC amendment / application docket |
| `restart_status` | `string` | `none` | yes | One of returned \| in_progress \| planned \| none |
| `restart_target_year` | `int64` | `year` | yes | Target calendar year of return to service for a restart-pathway unit. Null when not a restart case or already returned. |
| `restart_instrument` | `string` | `none` | yes | Citation of the restart instrument (NRC reauthorization / power ascension approval |
| `retirement_announcement` | `string` | `none` | yes | Free-text note of any retirement announcement affecting this unit. If a BINDING exit instrument exists it lives in the confirmed-retirements registry — reference it via confirmed_retirement_ref; do NOT duplicate the row here. |
| `confirmed_retirement_ref` | `string` | `none` | yes | The `instrument_id` of the confirmed-retirements row that governs this unit's binding exit |
| `source_url` | `string` | `none` | no | Authoritative primary-source URL (NRC info-finder / license / SLR / uprate page |
| `source_doc` | `string` | `none` | yes | Document title / page reference within source_url. |
| `accessed` | `datetime64[ns]` | `none` | no | Date the sources were last re-queried (the intake vintage stamp). |
| `notes` | `string` | `none` | yes | Free-text context (restart detail |

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

## transfer-interface-limits

Measured hourly transmission-interface transfer limits (PJM Data Miner 2
transfer_limits_and_flows; pre/post-contingency kept as separate series).
Schema:
[`schema/transfer-interface-limits.schema.yaml`](schema/transfer-interface-limits.schema.yaml).

- **Keys:** `iso`, `interface`, `hour`
- **Reconciles:** UTC-keyed hourly interface rows onto the fixed non-leap
  8760-hour ISO-local model clock: Feb 29 dropped, the DST fall-back repeat
  merged by clock-hour group-by, the spring-forward hour filled from its
  neighbours and flagged (`n_source_rows = 0`). Dense — every (interface, hour)
  pair carries a row. The measured `transfer_mw` column is diagnostic only
  (crosswalk sanity checks), never a model input. Published operating-security
  limits, rule #13/#14 admissible; per-ISO specs in
  `scripts/lib/transfer_interface_limits/` (PJM first).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO code (currently PJM). |
| `interface` | `string` | `none` | no | Interface / transfer-limit-area name exactly as published by the source (e.g. "AP-South Post-Contingency", "AEP/DOM Post-Contingency", "Average Western"). The model-side link crosswalk (market_sim.data.transfer_interface_limits) maps the representable ones onto model links. |
| `hour` | `int64` | `hour_index` | no | Index 0-8759 on the fixed non-leap 8760-hour ISO-local clock (Feb 29 dropped) — the model's dispatch clock. |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Wall-clock local start of the hour (naive, ISO-local). |
| `limit_mw` | `float64` | `mw` | no | Enforced transfer limit (MW) for the interface over the local clock hour (mean of the source rows merged into the hour — one normally, two at the DST fall-back). Kept faithful to the source, including the rare zero/negative published values; the model-side consumer documents how those are reconciled onto link bounds. |
| `transfer_mw` | `float64` | `mw` | yes | Measured actual transfer (MW) across the interface over the hour (mean of merged source rows); null on the filled spring-forward hour. Diagnostic column for crosswalk sanity checks only — never a model input or target. |
| `n_source_rows` | `int64` | `count` | no | Source rows merged into the clock hour: 1 normally, 2 at the DST fall-back repeat, 0 for the spring-forward hour that never occurs locally (limit_mw filled from the neighbouring hours). |

## transmission-expansion

Committed transmission-expansion projects (binding-instrument registry): one
row per (project, affected model element), each bound by an enforceable public
instrument and mapped onto the reduced zonal topology as an ADDITIVE
transfer-capability delta (FF-G1; consumed by the gated forecast per-year apply
seam). Schema:
[`schema/transmission-expansion.schema.yaml`](schema/transmission-expansion.schema.yaml).

- **Keys:** `iso`, `row_id`
- **Reconciles:** ISO board / RTO plan approvals with cost allocation (MISO
  LRTP, CAISO TPP, PJM RTEP), state-regulator orders, signed contracts (NY Tier
  4, MA 83D) and energized projects onto per-ISO registry CSVs; roadmap/study
  projects stay watchlist-only in the raw README.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | Model ISO the affected element belongs to (ERCOT/CAISO/PJM/MISO/NYISO/NEISO). |
| `row_id` | `string` | `none` | no | Stable slug "<project_id>--<element>" unique per (project |
| `project_id` | `string` | `none` | no | Stable project slug shared by all of a project's rows (e.g. necec |
| `project_name` | `string` | `none` | no | Human-readable project name for review. |
| `sponsor` | `string` | `none` | yes | Developer / transmission owner(s). |
| `status_tier` | `string` | `none` | no | One of energized \| under_construction \| approved_funded. Vocabulary is closed; roadmap/planned is deliberately NOT a member. |
| `instrument` | `string` | `none` | no | Full citation of the binding instrument — approving body |
| `instrument_id` | `string` | `none` | yes | Short stable docket / plan-id slug where one exists (e.g. puct-55718 |
| `instrument_date` | `datetime64[ns]` | `none` | yes | Date the instrument became binding (board vote |
| `in_service_year` | `int64` | `year` | no | Calendar year the element's capability change is expected in service (projected COD; actual year for energized rows). |
| `in_service_month` | `int64` | `month` | yes | Month (1-12) within in_service_year where published. |
| `target_kind` | `string` | `none` | no | One of link \| interface \| import_tranche \| intra_zonal. link = a model TransferLink TTC delta; interface = a named InterfaceLimit cap delta; import_tranche = external supply-side capability into a zone (recorded |
| `from_zone` | `string` | `none` | yes | Model zone name — the link's from side (link rows); the containing zone (intra_zonal rows); null for interface/import_tranche. |
| `to_zone` | `string` | `none` | yes | Model zone name — the link's to side (link rows); the receiving zone (import_tranche rows); null otherwise. |
| `interface_name` | `string` | `none` | yes | InterfaceLimit.name the delta applies to (interface rows only |
| `delta_mw` | `float64` | `mw` | no | Transfer-capability increase in MW |
| `delta_mw_reverse` | `float64` | `mw` | yes | Reverse-direction delta where a source quantifies an asymmetric change (interface rows with reverse_cap_mw; one-way link pairs carry separate rows instead). Null = symmetric (link rows apply delta_mw to the link's symmetric ttc_mw). |
| `capacity_basis` | `string` | `none` | yes | What the published MW measures — one of thermal_rating \| interface_uplift \| converter_rating. A thermal_rating basis must carry a mapping_note reconciling line rating to interface-TTC uplift. |
| `mapping_confidence` | `string` | `none` | no | One of exact \| reconciled \| ambiguous — how directly the physical project maps onto the model element. |
| `mapping_note` | `string` | `none` | no | REQUIRED reconciliation note (CLAUDE.md rule 14) — which physical facilities |
| `superseded` | `bool` | `none` | no | True when a counter-instrument (cancellation |
| `superseding_instrument` | `string` | `none` | yes | Citation of the counter-instrument when superseded. |
| `superseding_instrument_date` | `datetime64[ns]` | `none` | yes | Date the counter-instrument became binding |
| `source_url` | `string` | `none` | no | Authoritative URL of the instrument |
| `source_doc` | `string` | `none` | yes | Document title / table / page reference within source_url. |
| `accessed` | `datetime64[ns]` | `none` | no | Date the source was last re-queried (the intake vintage stamp). |
| `notes` | `string` | `none` | yes | Free-text context (phasing |

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

## nyiso-downstate-gas

Daily downstate NYISO delivered-gas index, per zone, for the non-firm LM6000
CT-peaker fleet (NYC zone J + Long Island zone K). Schema:
[`schema/nyiso-downstate-gas.schema.yaml`](schema/nyiso-downstate-gas.schema.yaml).

- **Keys:** `iso`, `zone`, `date`
- **Reconciles:** The measured Transco Zone 6 NY pipeline-hub daily spot
  (`transco_z6_ny_daily.csv`, the peaker's own commodity), Henry Hub daily
  (`henry_hub_daily.csv`, provenance), and the measured monthly per-LDC
  non-firm transportation delivery rate
  (`nyiso_downstate_ldc_transport_monthly.csv`: KEDNY SC-22 for NYC, KEDLI
  SC-19 for Long Island) — into one daily series per zone `delivered_gas =
  transco_z6_ny_daily + ldc_transport_adder_month`, interpolated to every
  calendar day. Each component is a measured, forward-native market/tariff
  input (rule-13); nothing fitted to a residual. This v2 per-zone transport
  construction supersedes the v1 statewide EIA-citygate premium (the
  interruptible peakers are transport customers). Consumed by
  `market_sim.data.fuel.apply_nyiso_downstate_ct_gas_daily` to re-ground the
  downstate CT-peaker offer level.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO identifier (NYISO). |
| `zone` | `string` | `none` | no | Downstate model zone the delivered index applies to (NYC or Long_Island). |
| `date` | `datetime64[ns]` | `calendar_date` | no | Calendar day (every day in the covered year; non-trading days interpolated). |
| `henry_hub_usd_per_mmbtu` | `float64` | `usd_per_mmbtu` | no | EIA Henry Hub daily spot ($/MMBtu), interpolated to every calendar day (provenance component). |
| `transco_z6_ny_usd_per_mmbtu` | `float64` | `usd_per_mmbtu` | no | Measured Transco Zone 6 NY pipeline-hub daily spot ($/MMBtu), interpolated to every calendar day (the peaker's commodity index). |
| `ldc_transport_adder_usd_per_mmbtu` | `float64` | `usd_per_mmbtu` | no | Monthly LDC non-firm transportation delivery rate for the zone's LDC (KEDNY SC-22 / KEDLI SC-19, Tier 1, incl. delivery-rate adjustments), broadcast to each day of the month. |
| `delivered_gas_usd_per_mmbtu` | `float64` | `usd_per_mmbtu` | no | Downstate non-firm transport delivered-gas index = transco_z6_ny_usd_per_mmbtu + ldc_transport_adder_usd_per_mmbtu. |

## ercot-wtx-congestion

Measured ERCOT West Texas Export corridor transmission-congestion pressure
(hourly) — the VRE curtailment-share driver's shape source. Schema:
[`schema/ercot-wtx-congestion.schema.yaml`](schema/ercot-wtx-congestion.schema.yaml).

- **Keys:** `iso`, `hour`
- **Reconciles:** ERCOT NP6-86-CD SCED binding constraints geo-attributed to
  the West Texas Export wind corridor via ERCOT's authoritative Settlement
  Points List / electrical-bus load-zone mapping (NP4-160): a binding row
  counts when either station is in the LZ_WEST settlement zone or the
  constraint is the WESTEX/PNHNDL export GTC. Aggregated to the fixed non-leap
  8760-hour ERCOT-local clock as per-hour SCED-execution and West-binding
  counts, congestion fraction, interface-only fraction, and mean positive West
  shadow price (dense). ERCOT-only (measured congestion incidence, rule #13/#14
  admissible — never the reported curtailment volume).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO code (ERCOT). |
| `hour` | `int64` | `hour_index` | no | Index 0-8759 on the fixed non-leap 8760-hour ERCOT-local clock (Feb 29 dropped) — the model's dispatch clock. |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Wall-clock local start of the hour (naive, ERCOT local). |
| `n_intervals` | `int64` | `count` | no | Number of distinct SCED executions observed in the hour (nominal cadence ~12/hour; the DST fall-back clock hour can carry up to ~24). Zero-filled for hours with no SCED coverage in the archive. |
| `n_binding_west` | `int64` | `count` | no | Number of those executions with at least one binding (ShadowPrice > 0) West-corridor constraint (LZ_WEST-endpoint 138/345 kV element or the WESTEX/PNHNDL export GTC). |
| `congestion_frac` | `float64` | `fraction` | no | n_binding_west / n_intervals in [0,1] — the fraction of the hour's SCED executions with the West Texas Export corridor congested. The measured congestion-pressure intensity the curtailment-share driver's SHAPE is fit to. 0.0 when n_intervals is 0. |
| `interface_binding_frac` | `float64` | `fraction` | no | Fraction of the hour's executions with the aggregate WESTEX or PNHNDL export GTC binding — the interface-only component (already representable in the model's 8-zone TTC), reported for decomposition against the nodal tail. |
| `shadow_price_mean_west` | `float64` | `usd_per_mwh` | yes | Mean positive ShadowPrice over the hour's binding West-corridor constraints; null when none bound that hour. |
| `n_binding_family_d` | `int64` | `count` | no | Executions in the hour with at least one DAYTIME-family (D) corridor element binding — the solar-flood / daytime-export congestion family (measured hod peak h14-15; corr +0.775..+0.959 vs actual solar curtailment in every year 2023-2025). Excludes PNHNDL. |
| `n_binding_family_n` | `int64` | `count` | no | Executions in the hour with at least one OVERNIGHT-family (N) corridor element binding — the wind-export congestion tail that dominates the pooled union (measured hod peak h21-23; 0.70-0.77 of nodal binding weight). Excludes PNHNDL. |
| `n_binding_pnhndl` | `int64` | `count` | no | Executions in the hour with the PNHNDL Panhandle export GTC binding. Held out of the D/N split: the Panhandle interface's model-side owner (endogenous tie vs driver share) is a mechanism choice, not a family. |
| `congestion_frac_family_d` | `float64` | `fraction` | no | n_binding_family_d / n_intervals in [0,1]. 0.0 when n_intervals is 0. |
| `congestion_frac_family_n` | `float64` | `fraction` | no | n_binding_family_n / n_intervals in [0,1]. 0.0 when n_intervals is 0. |
| `congestion_frac_pnhndl` | `float64` | `fraction` | no | n_binding_pnhndl / n_intervals in [0,1] — the measured Panhandle export interface enforcement-incidence signal. 0.0 when n_intervals is 0. |

## nyiso-renewable-curtailment

NYISO's coarse annual NYCA-wide + 4-zone wind/FTM-solar curtailment aggregate —
a labeled diagnostic, not an hourly HSL series (NYISO publishes no per-plant
uncurtailed-potential data). Schema:
[`schema/nyiso-renewable-curtailment.schema.yaml`](schema/nyiso-renewable-curtailment.schema.yaml).

- **Keys:** `iso`, `resource_type`, `geographic_scope`, `year`
- **Reconciles:** Hand-transcribed from NYISO's annual NYCA Renewables
  presentation series (ICAPWG/MIWG decks, nyiso.com/reports-information):
  NYCA-wide annual curtailed GWh + percent-of-production for wind (2017-2025)
  and FTM solar (2022-2025), plus zonal (West/Central/North/Mohawk Valley)
  annual wind curtailed GWh for the years each deck reports its own current
  year (2020-2023, 2025 — no standalone 2024 deck was found). See
  `data/raw/nyiso-renewable-curtailment/README.md` for exact source URLs and
  documented gaps. Read by `market_sim.data.nyiso_renewable_curtailment`; not
  consumed by dispatch.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO identifier (NYISO). |
| `resource_type` | `string` | `none` | no | Curtailed resource type (wind, ftm_solar). |
| `geographic_scope` | `string` | `none` | no | NYCA (system-wide) or one of NYISO's curtailment-reporting zones (WEST, CENTRAL, NORTH, MOHAWK_VALLEY). Zonal rows are wind-only — FTM solar curtailment is reported NYCA-wide only. |
| `year` | `int64` | `none` | no | Calendar year. |
| `curtailed_energy_gwh` | `float64` | `gwh` | no | NYISO's estimated curtailed energy for the year, in GWh. |
| `curtailed_pct` | `float64` | `percent` | yes | Percent of potential production curtailed, as printed by the source. Only published for NYCA-wide rows; null for zonal rows and for FTM solar years the source didn't print a percent for (2022-2023). |
| `source_doc` | `string` | `none` | no | Source presentation filename (see raw README for the exact URL). |
| `source_page` | `string` | `none` | yes | Slide/page number(s) within source_doc the value was read from. |
| `notes` | `string` | `none` | yes | Source-printed annotations (e.g. a zone's driver footnote) or cross-check notes. |

## nyiso-renewable-curtailment-monthly

Monthly companion to `nyiso-renewable-curtailment`: NYCA-wide
percent-of-production (wind) and zonal curtailed GWh, by month. Schema:
[`schema/nyiso-renewable-curtailment-monthly.schema.yaml`](schema/nyiso-renewable-curtailment-monthly.schema.yaml).

- **Keys:** `iso`, `resource_type`, `geographic_scope`, `year`, `month`
- **Reconciles:** Same source decks as `nyiso-renewable-curtailment`: NYCA-wide
  monthly wind curtailment percent (2017-2025, cross-checked across overlapping
  decks) and zonal monthly curtailed GWh for the years with a published zonal
  breakdown (2020-2023, 2025). Read by
  `market_sim.data.nyiso_renewable_curtailment`; not consumed by dispatch.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO identifier (NYISO). |
| `resource_type` | `string` | `none` | no | Curtailed resource type (wind is the only one with monthly data published). |
| `geographic_scope` | `string` | `none` | no | NYCA (system-wide) or one of NYISO's curtailment-reporting zones (WEST, CENTRAL, NORTH, MOHAWK_VALLEY). |
| `year` | `int64` | `none` | no | Calendar year. |
| `month` | `int64` | `none` | no | Calendar month (1-12). |
| `curtailed_energy_gwh` | `float64` | `gwh` | yes | Zonal monthly estimated curtailed energy, in GWh. Null for NYCA-wide rows. |
| `curtailed_pct` | `float64` | `percent` | yes | NYCA-wide percent of that month's wind production curtailed. Null for zonal rows. |
| `source_doc` | `string` | `none` | no | Source presentation filename (see raw README for the exact URL). |
| `source_page` | `string` | `none` | yes | Slide/page number(s) within source_doc the value was read from. |

## coal-basin-price

EIA Annual Coal Report region/rank f.o.b.-mine coal price (annual, national).
Schema:
[`schema/coal-basin-price.schema.yaml`](schema/coal-basin-price.schema.yaml).

- **Keys:** `metric`, `region_id`, `market_type_id`, `coal_rank_id`, `year`
- **Reconciles:** EIA `coal/market-sales-price` (region x market-type, all
  ranks) and `coal/price-by-rank` (region x coal rank) tidied onto one
  `metric`-keyed frame, with an `ALL` sentinel on whichever dimension the other
  route doesn't carry. The free public-domain substitute for the
  S&P/Argus/McCloskey-paywalled daily basin spot indices — collected to give
  the coal-vs-gas passthrough sigmoids (issue #1347) a real coal commodity
  price to check their `floor`/`ceil`/`gas_mid` asymptotes against. Region ->
  ISO-plant crosswalk: `reference` datatype, `market=coal-region-crosswalk`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `metric` | `string` | `none` | no | Which EIA route this row came from: "market_sales_price" (region x market-type, all ranks) or "price_by_rank" (region x coal rank, all market types). |
| `region_id` | `string` | `none` | no | EIA stateRegionId — a two/three-letter state code (e.g. TX, WV) or a named producing region/aggregate (e.g. PRB = Powder River Basin, APC/APN/APS = Appalachia Central/Northern/Southern, ILL = Illinois Basin, UNT = Uinta Basin, ENC/WNC/WSC/ESC = Census-division aggregates). |
| `region_name` | `string` | `none` | no | Human-readable EIA region/state description. |
| `market_type_id` | `string` | `none` | no | EIA marketTypeId (CAP=captive, OM=open market, TOT=total) for metric="market_sales_price" rows; literal "ALL" for metric="price_by_rank" rows. |
| `coal_rank_id` | `string` | `none` | no | EIA coalRankId (BIT/SUB/LIG/ANT/TOT) for metric="price_by_rank" rows; literal "ALL" for metric="market_sales_price" rows. |
| `year` | `int64` | `none` | no | Calendar (ACR publication) year. |
| `price_usd_per_ton` | `float64` | `usd_per_short_ton` | no | Average sales price at the mine, dollars per short ton. |
| `sales_short_tons` | `float64` | `short_tons` | yes | Annual sales tonnage for this region/market-type/year (only populated for metric="market_sales_price"; null for metric="price_by_rank" rows, which EIA does not report tonnage for). |

## coal-mining-ppi

BLS Producer Price Index for coal (national, monthly). Schema:
[`schema/coal-mining-ppi.schema.yaml`](schema/coal-mining-ppi.schema.yaml).

- **Keys:** `series_id`, `year`, `month`
- **Reconciles:** BLS `WPU051` (PPI commodity Coal) and `PCU2121--2121--` (PPI
  industry Coal Mining, NAICS 2121) — a monthly elasticity/slope cross-check on
  the annual `coal-basin-price` region prices. No regional breakout exists in
  BLS PPI for coal (confirmed by probing candidate series ids).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `series_id` | `string` | `none` | no | BLS series id (WPU051 = PPI commodity Coal; PCU2121--2121-- = PPI industry Coal Mining, NAICS 2121). |
| `series_name` | `string` | `none` | no | Human-readable series description. |
| `year` | `int64` | `none` | no | Calendar year. |
| `month` | `int64` | `none` | no | Calendar month (1-12). |
| `index_value` | `float64` | `index_1982_100` | no | PPI index value (base period varies by series; BLS convention, unscaled — not a dollar price. Use month-over-month / year-over-year ratios for the slope/elasticity cross-check, not the level.). |

## coal-stocks

Plant-level month-ending coal stockpile by coal rank, in short tons (national;
ISO resolved at read time from the plant registry). Schema:
[`schema/coal-stocks.schema.yaml`](schema/coal-stocks.schema.yaml).

- **Keys:** `plant_id`, `energy_source`, `year`, `month`
- **Reconciles:** EIA-923 Schedule 2 ("Page 2 Coal Stocks Data") from the free
  annual bulk ZIP. Rule 13: a year-Y budget reads the December Y-1 opening
  stock only, never year Y's own stock path.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `plant_id` | `int64` | `none` | no | EIA plant code. Mirrors the fleet / emissions / outages schemas so the four join, and is the key the bench parts and plant registry use. |
| `energy_source` | `string` | `none` | no | EIA reported fuel type code for the coal rank held (BIT bituminous, SUB subbituminous, LIG lignite, WC waste coal, RC refined coal, SGC coal- derived synthesis gas). A plant holding two ranks reports two rows. |
| `year` | `int64` | `year` | no | Calendar year of the reported month-ending stock. |
| `month` | `int64` | `month` | no | Calendar month, 1-12, whose ENDING stock this row reports. |
| `ending_stock_tons` | `float64` | `short_tons` | no | Stock of this coal rank physically held at the plant at month end, in short tons. Zero is a real reported value (a plant that holds no coal of that rank), not a gap. |
| `plant_name` | `string` | `none` | yes | EIA plant name, carried for traceability only. |
| `plant_state` | `string` | `none` | yes | Two-letter state postal code of the plant. |
| `balancing_authority_code` | `string` | `none` | yes | EIA-reported balancing authority (e.g. MISO, PJM). Provenance only — ISO membership is resolved from the plant registry, not from this column, because BA code and modelled ISO zone disagree at several seams. |
| `nerc_region` | `string` | `none` | yes | NERC region as reported by EIA. |
| `eia_sector_number` | `int64` | `none` | yes | EIA sector (1 electric utility, 2 IPP non-CHP, 3 IPP CHP, 4/5 commercial, 6/7 industrial). Same field the PJM retirement-screen sector gate keys on. |
| `physical_unit_label` | `string` | `none` | yes | EIA's own unit label for the reported quantity, retained so a future non-short-ton vintage cannot be silently mis-scaled. |

## coal-receipts

Plant-level monthly coal receipts (deliveries to plant), receipt lots summed to
plant x rank x month x purchase type (national). Schema:
[`schema/coal-receipts.schema.yaml`](schema/coal-receipts.schema.yaml).

- **Keys:** `plant_id`, `energy_source`, `year`, `month`, `purchase_type`,
  `primary_transportation_mode`
- **Reconciles:** EIA-923 Page 5 ("Fuel Receipts and Costs"), coal subset.
  Supersedes the incomplete `quantity` column of the legacy
  eia923_monthly_fuel_costs extract for coal receipts. Rule 13: year Y's own
  receipts are an outcome, not a delivery rate.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `plant_id` | `int64` | `none` | no | EIA plant code. Mirrors the coal-stocks / fleet / emissions / outages schemas so they all join, and is the key the bench parts and the plant registry use. |
| `energy_source` | `string` | `none` | no | EIA reported fuel type code for the coal rank received (BIT bituminous, SUB subbituminous, LIG lignite, WC waste coal, RC refined coal, SGC coal-derived synthesis gas). Same vocabulary as coal-stocks, so receipts and stock join rank-for-rank. |
| `year` | `int64` | `year` | no | Calendar year the receipt was reported in. |
| `month` | `int64` | `month` | no | Calendar month, 1-12, the coal was received in. |
| `purchase_type` | `string` | `none` | no | EIA purchase type of the delivery - C contract, NC new contract, S spot, T tolling. Retained as a key column because a contracted-tonnage-only delivery rate (a forward instrument, rather than a realised spot outcome) is one of the admissible budget constructions and cannot be reconstructed once the categories are summed together. |
| `primary_transportation_mode` | `string` | `none` | no | EIA primary transportation mode (RR railroad, RV river, TR truck, CV conveyor, PL pipeline, GL Great Lakes, SP slurry pipeline, TC tramway, WT water unspecified, ...). Retained as a key column so a rail/logistics delivery-capacity construction stays available. Blank in the source becomes the sentinel "UNK" rather than null, so the column can carry a non-null key. |
| `quantity_tons` | `float64` | `short_tons` | no | Coal received in this month at this plant for this rank / purchase type / transport mode, in short tons, summed over the underlying receipt lots. Zero is a real reported value, not a gap. |
| `heat_content_mmbtu_per_ton` | `float64` | `mmbtu_per_short_ton` | yes | Quantity-weighted mean gross heat content of the coal received, MMBtu per short ton, over the lots summed into this row. This is what converts a tonnage budget into the MMBtu an LP energy-budget row is denominated in, so it is carried rather than assumed. Null where every underlying lot withheld it. |
| `fuel_cost_cents_per_mmbtu` | `float64` | `cents_per_mmbtu` | yes | Quantity-weighted mean delivered fuel cost, cents per MMBtu, as EIA reports it. Provenance/diagnostic only - delivered coal prices for the model come from the existing F923 fuel-price path, not from here. Null where every underlying lot withheld it (EIA withholds cost for non-regulated respondents, so this is null far more often than the quantity is). |
| `plant_name` | `string` | `none` | yes | EIA plant name, carried for traceability only. |
| `plant_state` | `string` | `none` | yes | Two-letter state postal code of the plant. |
| `balancing_authority_code` | `string` | `none` | yes | EIA-reported balancing authority (e.g. MISO, PJM). Provenance only - ISO membership is resolved from the plant registry, not from this column, because BA code and modelled ISO zone disagree at several seams. Absent in vintages before 2020. |

## nyiso-reserve-requirements

NYISO's published locational operating-reserve requirements by product x region
for each dated version of the Locational Reserve Requirements posting,
including the SENY 30-minute hourly step shape and Thunderstorm-Alert zeroing
flags (issue #1344 / Ask B3). Schema:
[`schema/nyiso-reserve-requirements.schema.yaml`](schema/nyiso-reserve-requirements.schema.yaml).

- **Keys:** `iso`, `version`, `region`, `product`, `period_label`, `hb_start`
- **Reconciles:** Hand-transcription of the dated LRR PDFs (versions
  v2016/v2019/v2020/v2021/v2026, bounded by nyiso.com document versions and
  Wayback snapshots, with sourced `effective_start` dates where a version
  changes mid-year) under `data/raw/NYISO-AS/requirements/`; see that README
  for the effective-date sources. Feeds the gated hourly
  `ReserveFamily.requirement` channel (`nyiso_dynamic_reserve_requirements`).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO identifier (NYISO). |
| `version` | `string` | `none` | no | Dated document version (v2016, v2019, v2020, v2021, v2026). The evidence columns are document-existence bounds; the in-force date the hourly derive switches on is effective_start where it is sourced. |
| `region` | `string` | `none` | no | Reserve region (NYCA, EAST, SENY, NYC, LI). |
| `zones` | `string` | `none` | no | NYISO load zones the region spans, as printed (e.g. G-K). |
| `product` | `string` | `none` | no | Reserve product (spin_10, total_10, total_30). |
| `period_label` | `string` | `none` | no | Intra-day applicability: "all" (all hours), "hb_range" (explicit hour-beginning window in hb_start/hb_end), or "on_peak"/"off_peak" (LI 30-minute rows; the boundary hours are not defined in the posting). |
| `hb_start` | `int64` | `hour_beginning` | yes | First hour-beginning (0-23, local) the row applies to; null for on/off-peak rows. |
| `hb_end` | `int64` | `hour_beginning` | yes | Last hour-beginning (inclusive) the row applies to; null for on/off-peak rows. |
| `requirement_mw` | `float64` | `mw` | no | Published requirement in MW (0 where the posting prints 0 MW). |
| `tsa_reduced_to_zero` | `bool` | `none` | no | True when the version's footnotes state the requirement is reduced to zero during Thunderstorm Alerts (v2021+: NYC total_10/total_30 and SENY total_30; v2020: SENY total_30 only). |
| `evidence_start` | `datetime64[ns]` | `date` | no | Earliest date the version is evidenced in force (Wayback snapshot or retrieval date). |
| `evidence_end` | `datetime64[ns]` | `date` | yes | Latest bound before the next version is evidenced; null for the current version. |
| `source_doc` | `string` | `none` | no | PDF filename under data/raw/NYISO-AS/requirements/locational-reserve-requirements/. |
| `notes` | `string` | `none` | yes | Transcription notes (footnote provenance, unverified effective-date bounds). |
| `effective_start` | `datetime64[ns]` | `date` | yes | Sourced date the version's requirements took effect in the market (start of that operating day). Null when no effective date has been sourced — the hourly derive then refuses any year in which the version would begin mid-year. |
| `effective_source` | `string` | `none` | yes | Citation for effective_start (FERC docket, NYISO notice, document version metadata). |

## nyiso-operating-events

Typed NYISO operating events (Thunderstorm Alert windows, system state, reserve
pick-ups, OOM reliability commitments, emergency transactions) parsed from the
public MIS message logs, 2018 through H1-2026 (Ask B2). Schema:
[`schema/nyiso-operating-events.schema.yaml`](schema/nyiso-operating-events.schema.yaml).

- **Keys:** `iso`, `source_dataset`, `seq`
- **Reconciles:** NYISO MIS P-35 Real-Time Events and P-25 Operational
  Announcements monthly archives, re-serialized per-year under
  `data/raw/NYISO-AS/requirements/` and parsed against a controlled template
  vocabulary (parse-only; unmatched messages stay in raw). Out-of-training
  years intaken under the 2026-07-10 owner authorization
  (`docs/out-of-sample-results-2026-07.md` §1.2).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO identifier (NYISO). |
| `source_dataset` | `string` | `none` | no | Originating MIS feed ("realtime_events" or "oper_messages"). |
| `seq` | `int64` | `none` | no | Stable per-dataset sequence number in source order (file, then row) — disambiguates same-minute events. |
| `timestamp_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | Event timestamp in UTC. Source stamps are Eastern prevailing wall-clock without an EDT/EST flag; the duplicated DST fall-back hour is resolved first-occurrence-as-EDT in source order. |
| `timestamp_local` | `datetime64[ns]` | `local_timestamp` | no | Eastern prevailing wall-clock stamp as printed (informational). |
| `event_type` | `string` | `none` | no | Controlled vocabulary: thunderstorm_alert, system_state, reserve_pickup, capacity_request, oom_commitment, emergency_transaction. |
| `action` | `string` | `none` | no | Event action. thunderstorm_alert: start/end; system_state: normal/alert/major_emergency; reserve_pickup: start/end; capacity_request: submitted; oom_commitment: requested/updated/removed; emergency_transaction: added/cut. |
| `start_of_day` | `bool` | `none` | no | True for start-of-day state carryover messages (state/TSA already in effect at 00:00) rather than a live transition. |
| `detail` | `string` | `none` | yes | Event subject: proxy bus for capacity_request, unit name for oom_commitment, counterparty for emergency_transaction; null otherwise. |
| `mw` | `float64` | `mw` | yes | MW quantity where the message carries one (emergency transactions). |
| `message` | `string` | `none` | no | Full original message text (verbatim). |
| `source_file` | `string` | `none` | no | Daily source CSV inside the MIS monthly archive the row came from. |

## nyiso-interface-flows

Hourly per-interface gross flows and posted limits for NYISO internal
interfaces and external ties, aggregated from the public 5-minute MIS posting
(Ask D1). Schema:
[`schema/nyiso-interface-flows.schema.yaml`](schema/nyiso-interface-flows.schema.yaml).

- **Keys:** `iso`, `interface`, `interval_start_utc`
- **Reconciles:** NYISO MIS P-32 ExternalLimitsFlows monthly archives, 5-min ->
  hourly (mean flow, most-binding limits; +/-9999 MW unbounded sentinels
  nulled), one partition per year 2018 through H1-2026 from
  `data/raw/NYISO/interface-flows/`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO identifier (NYISO). |
| `interface` | `string` | `none` | no | Interface name as posted (e.g. "CENTRAL EAST - VC", "SCH - HQ - NY"). |
| `point_id` | `int64` | `none` | no | NYISO point ID of the interface (stable numeric identifier). |
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC hour-beginning of the aggregated interval. |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Eastern prevailing wall-clock hour-beginning (informational). |
| `flow_mw` | `float64` | `mw` | no | Hourly mean of the 5-minute posted flow (positive = flow in the interface's defined direction). |
| `positive_limit_mw` | `float64` | `mw` | yes | Most-binding (minimum) posted positive limit across the hour's 5-minute intervals; null where the source posts the +/-9999 MW "unbounded" sentinel. |
| `negative_limit_mw` | `float64` | `mw` | yes | Most-binding (maximum, i.e. closest to zero) posted negative limit across the hour; null where the source posts the sentinel. |
| `n_intervals` | `int64` | `none` | no | Count of 5-minute observations aggregated (24 in the DST fall-back hour). 0 marks an interior source gap filled from the adjacent actual observation (owner instruction 2026-07-10; see the fetch script) — hours before an interface first exists are never invented. |

## nyiso-som-hub-fuel-annual

Annual average fuel index prices by hub serving New York (incl. Iroquois Zone
2) transcribed from the NYISO State of the Market reports (Ask C1 annual
floor). Schema:
[`schema/nyiso-som-hub-fuel-annual.schema.yaml`](schema/nyiso-som-hub-fuel-annual.schema.yaml).

- **Keys:** `iso`, `year`, `fuel`, `hub`
- **Reconciles:** SOM Figure A-6 annual tables across the
  2020/2022/2023/2024/2025 reports (overlapping years cross-check identically),
  2018-2025, from `data/raw/gas-prices/nyiso_som_hub_fuel_annual.csv`. The
  daily/monthly Z2 series remains Platts-licensed (open licence ask).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO identifier (NYISO). |
| `year` | `int64` | `none` | no | Calendar year the annual average covers. |
| `fuel` | `string` | `none` | no | Fuel family ("gas" or "oil"). |
| `hub` | `string` | `none` | no | Canonical hub/series code: TENNESSEE_Z6, IROQUOIS_Z2, TRANSCO_Z6_NY, TETCO_M3, TENN_Z4_200L (gas); ULSK, ULSD, FO6 (oil). |
| `price_usd_per_mmbtu` | `float64` | `usd_per_mmbtu` | no | Annual average index price as printed ($/MMBtu; excludes transport and local taxes). |
| `source_doc` | `string` | `none` | no | SOM report PDF filename under data/raw/NYISO/. |
| `source_page` | `int64` | `none` | no | PDF page number the table was read from. |

## reserve-requirements

Measured as-enforced hourly reserve requirements per reserve location and
product — the condition-varying requirement input for the in-LP energy+reserve
co-optimization (`<iso>_dynamic_reserve_requirements`). Schema:
[`schema/reserve-requirements.schema.yaml`](schema/reserve-requirements.schema.yaml).

- **Keys:** `iso`, `location`, `product`, `interval_start_utc`
- **Reconciles:** ISO-NE ISO Express 'Hourly Reserve Requirements'
  (ancillary-hourly-rr) 15-day window CSVs from
  `data/raw/NEISO-AS/requirements/` (gitignored; regenerated by
  `scripts/data/fetch_neiso_reserve_requirements.py`), hour-ending labels
  aligned to true UTC hours (DST-aware), bounded step-fill of single-hour
  publication holes. Locations ROS (system-wide — the model input),
  SWCT/CT/NEMABSTN (local, 30-min total only). Train years 2023-2025 only (rule
  22).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO identifier (NEISO; other ISOs register additively). |
| `location` | `string` | `none` | no | Reserve location label in the ISO's published vocabulary (NEISO: ROS = the system-wide requirement row, SWCT / CT / NEMABSTN = local reserve zones whose published series carries the 30-minute total only). |
| `location_id` | `int64` | `none` | no | ISO-native numeric location ID (NEISO 7000-7003). |
| `product` | `string` | `none` | no | Canonical reserve product: 10min_spin (NEISO Ten-Minute Spinning), 10min_total (Ten-Minute), 30min_total (TOTAL, the 30-minute requirement). |
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC hour-beginning of the requirement hour. |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Prevailing Eastern wall-clock hour-beginning (informational; the fall-back hour repeats its wall-clock stamp, the UTC key stays unique). |
| `requirement_mw` | `float64` | `mw` | no | Enforced requirement MW (>= 0). Local-zone rows publish 0 for the products they do not carry; zeros are kept as published. |

## som-competitive-conduct

Market-monitor competitive-conduct metrics (price-cost mark-up, output gap,
coal economic-offer vs must-run/self-commitment start shares) transcribed from
the Potomac Economics SOM reports and IMM quarterlies. Schema:
[`schema/som-competitive-conduct.schema.yaml`](schema/som-competitive-conduct.schema.yaml).

- **Keys:** `iso`, `year`, `period`, `fleet_segment`, `metric`
- **Reconciles:** MISO 2023/2024 SOM Table 7 + Competitive Assessment and the
  2025 IMM quarterly output-gap rows (train-window years only, rule 22), from
  `data/raw/som-competitive-conduct/som_competitive_conduct.csv`; PDFs under
  `data/raw/MISO/`. Other ISOs' SOM conduct sections extend the same tidy
  layout.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO identifier (MISO seeded; NYISO/ERCOT/NEISO extend). |
| `year` | `int64` | `none` | no | Market year the statistic describes (not the publication year). |
| `period` | `string` | `none` | no | Aggregation window within the year: "annual" for SOM full-year values, or the IMM quarterly-report season ("spring", "summer", "fall", "winter") for quarterly values. |
| `fleet_segment` | `string` | `none` | no | Fleet the metric describes: "system" (all suppliers), "coal_regulated" (SOM Table 7 "Regulated Utilities" coal rows), "coal_merchant" (SOM Table 7 "Merchants" coal rows), "new_gas_ct" / "new_gas_cc" (the ERCOT SOM Net Revenue Analysis hypothetical new-entrant proxies: CT 10.5 / CC 7.0 MMBtu/MWh heat rate, $4/MWh VOM, 10% outage rate), or "coal_existing" / "nuclear_existing" (the SOM existing-unit profitability discussions' cost benchmarks). SPP adds "coal" / "wind" (the SPP MMU's fuel-type marginal-resource markup averages); SPP-81 adds "gas_combined_cycle" / "gas_simple_cycle" / "other" for the marginal-technology shares. |
| `metric` | `string` | `none` | no | Metric code: "price_cost_markup" (simulated actual-offer vs reference-level SMP difference, fraction), "output_gap_share_of_load" (low-threshold monthly-average output gap as a fraction of load), "output_gap_low_threshold_mw" (low-threshold output gap, MW/hr), "starts" (coal unit commitments in the year), "starts_econ_offered_share" (fraction of starts offered economically / scheduled day-ahead), "starts_mustrun_profitable_share" / "starts_mustrun_unprofitable_share" (fraction of starts with must-run [self-commit] status, split by whether market revenues covered commitment + variable cost by the first full day), "net_revenue_usd_per_mwh" (net operating revenue of the segment's starts). ERCOT SOM net-revenue rows add: "net_revenue_usd_per_kw_yr" (single published value; "_min"/"_max" variants for locational ranges; "_houston"/"_west" variants for the named-zone values), "net_revenue_ex_uri_usd_per_kw_yr_min"/"_max" (the 2021 SOM's own published Winter-Storm-Uri counterfactual — what the year's net revenue "would have ranged" absent Uri; the monitor's number, not a derived one), "ecrs_effect_share_of_net_revenue" (share of 2023 net revenue the monitor attributes to ECRS price effects), "cone_usd_per_kw_yr_min"/"_max" (Potomac CONE estimates), "cone_planning_usd_per_kw_yr" / "cone_pnm_threshold_usd_per_kw_yr" (PUCT planning CONE vs legacy PNM-threshold CONE), "peaker_net_margin_usd_per_kw_yr", and existing-unit cost benchmarks "fixed_om_usd_per_kw_yr", "vom_usd_per_mwh", "fuel_cost_usd_per_mwh", "marginal_cost_usd_per_mwh", "total_generating_cost_usd_per_mwh". SPP MMU SOM rows (SPP-80, 2026-09-25) add: "offer_markup_{onpeak,offpeak}_usd_per_mwh" (MW-weighted average marginal-resource offer markup, market-based minus mitigated offer, $/MWh — a DIFFERENT construct from MISO's fractional "price_cost_markup"), "_exfeb_" variants (the 2021 SOM's own February-excluded averages), "_digitized_" variants (read from the SOM bar chart's average marker where the report prints no value — the note carries the bias correction), "offer_markup_usd_per_mwh" on the "coal"/"wind" segments, "congestion_payments_usd" (DA+RT congestion payments), "rt_scarcity_intervals" (five-minute RT intervals with any reserve scarcity), and "avg_{da,rt}_price_usd_per_mwh" (+ "_exfeb_"). SPP-81 (2026-09-25) adds "rt_marginal_interval_share_digitized" (share of RT intervals each technology segment was marginal, digitized from the SOM "Generation on the margin, real-time" bars, fraction) and "rt_implied_heat_rate" (the MMU's annual implied heat rate, btu_per_kwh), and "gas_hub_price_annual_avg" on the "panhandle_eastern" / "southern_star" / "henry_hub" segments (usd_per_mmbtu). |
| `value` | `float64` | `mixed` | no | Metric value; unit given by the unit column. |
| `unit` | `string` | `none` | no | One of "fraction", "count", "usd_per_mwh", "usd_per_kw_yr", "mw", "usd", "btu_per_kwh" (SPP MMU implied heat rate), "usd_per_mmbtu" (SPP MMU gas-hub averages); both added by SPP-81. |
| `source_doc` | `string` | `none` | no | Source report PDF filename under data/raw/MISO/ (or the ISO's raw dir). |
| `source_page` | `int64` | `none` | no | PDF page number (1-based, PDF pagination) the value was read from. |
| `note` | `string` | `none` | yes | Restatements, definitions, and caveats as printed in the source. |

## capacity-market-demand-curve

Published capacity-market demand-curve parameters — net-CONE, IRM, price cap,
and the sloped curve's own (x,y) points — per capacity-market ISO and delivery
year. The CR-1 mechanism input (rule-13-admissible published market-design
parameter). Schema:
[`schema/capacity-market-demand-curve.schema.yaml`](schema/capacity-market-demand-curve.schema.yaml).

- **Keys:** `iso`, `delivery_year`, `area`, `season`, `metric`, `point_index`
- **Reconciles:** PJM VRR curve + Net CONE + IRM (RPM BRA Planning Period
  Parameters), NYISO ICAP Demand Curves per locality (NYCA/NYC/LI/G-J), ISO-NE
  FCA Net CONE/ICR/Auction Starting Price/MRI, MISO seasonal PRA
  reliability-based demand curve + seasonal CONE, CAISO's documented CPM
  soft-offer-cap / CPUC RA report fixed-proxy — onto one canonical metric
  vocabulary (`net_cone`, `irm`, `price_cap`, `curve_point`, `soft_offer_cap`,
  `ra_report_price`). ERCOT excluded (energy-only). See
  `docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md` §3-4.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO publishing the value (PJM, NYISO, ISONE, MISO, CAISO). |
| `delivery_year` | `string` | `none` | no | Delivery/planning/capability year the parameter set governs, as a label (e.g. "2026/2027" for PJM/ISO-NE/MISO planning-year ISOs, "2025" for NYISO capability year or CAISO calendar year). Not a key on its own — see key_columns. |
| `area` | `string` | `none` | yes | Capacity area/locality the row applies to, for ISOs that publish locality-specific curves (NYISO NYCA/NYC/LI/G-J; MISO LRZ). Null (system- wide) for ISOs that publish one curve per delivery year (PJM RTO, ISO-NE system). CAISO repurposes this column to tag the RA product/ segment a scalar ra_report_price row represents (e.g. "system", "local", "flexible") since it has no locality curves of its own. |
| `season` | `string` | `none` | yes | Season the value applies to (MISO seasonal CONE/curve: summer \| fall \| winter \| spring). Null for ISOs/metrics that are annual-only. |
| `metric` | `string` | `none` | no | Canonical metric: net_cone \| gross_cone \| irm \| forecast_pool_requirement \| icap_ucap_translation_factor \| price_cap \| curve_point \| soft_offer_cap \| ra_report_price \| ra_mpb \| reliability_requirement \| reliability_requirement_frr_adj \| ee_addback \| curve_point_ucap \| icap_market_forecast_peak \| irm_adopted \| ucap_requirement. net_cone is the Net Cost of New Entry anchor (CONE minus inframarginal energy/AS rents); gross_cone is the pre-inframarginal-rent Cost of New Entry where an ISO publishes both as genuinely distinct quantities (e.g. MISO's per-LRZ gross CONE vs its two-subregion Net CONE); irm is the Installed Reserve Margin target (as published — MW or pct per value_unit); forecast_pool_requirement is PJM's published Forecast Pool Requirement (FPR) — the reliability requirement expressed in unforced-capacity (UCAP) terms as a fraction of forecast peak load (post-CIFP FPR = (1 + IRM) x Reference-Resource Accredited-UCAP factor), the ISO's own UCAP-basis requirement so the model need not re-derive it from IRM x a conversion ratio; icap_ucap_translation_factor is NYISO's NYCA-wide "translation factor" (Derate Factor) — the realized capacity-weighted forced-outage derate that converts the ICAP-basis NYCA Minimum Installed Capacity Requirement into the UCAP-basis requirement (ICAP Manual §2.5: UCAP_req = ICAP_req x (1 - translation_factor)), the NYISO analogue of PJM's forecast_pool_requirement pairing, carried as a decimal `fraction`; price_cap / price_floor are the curve's price ceiling/floor (as a multiple of net_cone or an absolute price, e.g. PJM's ICAP-basis cap/floor before UCAP conversion); curve_point is one (x,y) point on the sloped demand curve; soft_offer_cap, ra_report_price and ra_mpb are CAISO's documented fixed-proxy inputs (no centralized auction/curve) and they are three DIFFERENT KINDS of object, never interchangeable: soft_offer_cap is an administrative CEILING on what a CPM-designated resource may OFFER into CAISO's backstop, constructed from an EXISTING unit's going-forward fixed cost (so it contains no capex annuity by design and is not a price anyone is paid); ra_report_price is the CPUC RA Report's retrospective transacted weighted-average by RA product; ra_mpb is the CPUC's PCIA Resource Adequacy Market Price Benchmark — the volume-weighted average of ALL IOU/CCA/ESP RA transactions for a stated delivery year, issued every October under D.22-01-023 and unified into a SINGLE RA value (no system/local/flexible split) by D.25-06-049. ra_mpb is the only one of the three published on a FORWARD delivery year, which is what makes it rule-13-admissible as a forecast capacity-price anchor (it regenerates annually and responds to market conditions). CAISO tags the RA product segment in ``area`` (system \| local \| flexible \| unified); reliability_requirement / reliability_requirement_frr_adj are PJM's published RTO Reliability Requirement (UCAP MW) unadjusted and adjusted for FRR (the RPM-market requirement the VRR curve is drawn against); ISO-NE reuses bare reliability_requirement for its published Net ICR (QC MW — ICR minus HQICCs, the requirement the system-wide FCA demand curve is developed against; NEISO-RC-R R2 intake 2026-08-31, which also records each FCA's clearing outcome as a measured curve_point on that year's published curve — the auction clears ON the curve, verified exactly on the published FCA 11 table and FCA 13 tail segment); ee_addback is PJM's published EE Addback (UCAP MW) — the VRR point MW levels divided by (reliability_requirement_frr_adj + ee_addback) reproduce PJM's own Manual-18 pct_of_requirement fractions (verified <=0.1% for every 2021/2022-2025/2026 vintage, RC-1A 2026-07-16), which is how the pre-CIFP vintages' normalized curve shapes are derived; curve_point_ucap is the same VRR point in PJM's published absolute form (UCAP Level MW, UCAP Price $/MW-day) for a vintage whose curve_point rows already carry the Manual-18 pct basis, keeping the datatype key unique (2025/2026 — the workbook publishes the point prices the narrative PDF leaves formula-defined). |
| `point_index` | `int64` | `none` | yes | 0-based order of this point along the sloped demand curve, left (lowest reserve position) to right. Populated only for metric=curve_point; null for scalar metrics. |
| `x_value` | `float64` | `none` | yes | X-axis value for a curve_point row (reserve position, per x_unit). Null for scalar metrics. |
| `x_unit` | `string` | `none` | yes | Unit of x_value: pct_of_requirement (reserve margin as a fraction of the published reliability requirement) \| mw (absolute reserve MW) \| pct_of_irm. Null for scalar metrics. |
| `y_value` | `float64` | `none` | yes | For curve_point rows, the price at this point (per y_unit) — null when the ISO publishes the curve as a formula whose price at this x-position is not itself a standalone published number (e.g. PJM Manual 18's curve-point formula; the point's x_value still carries the shape). For scalar metrics, the metric's own value (per y_unit); null only when a source publishes a metric as a bound (e.g. ">X") that cannot be recorded as a clean number — such rows are omitted at intake rather than guessed. |
| `y_unit` | `string` | `none` | yes | Unit of y_value: usd_per_mw_day \| usd_per_mw_day_icap (PJM's pre-UCAP-conversion ICAP-basis cap/floor) \| usd_per_mw_yr \| usd_per_kw_month \| usd_per_kw_yr \| pct \| multiple_of_net_cone \| fraction_of_peak_ucap (the forecast_pool_requirement's UCAP-MW / forecast-peak-MW ratio) \| fraction (a dimensionless decimal as published, e.g. NYISO's icap_ucap_translation_factor 0.1321). |
| `vintage` | `string` | `none` | yes | The parameter set's own filing/adoption label and date (e.g. "2026/2027 RPM BRA Planning Period Parameters, filed 2025-XX-XX"), distinct from delivery_year (the period it governs). |
| `source_doc` | `string` | `none` | yes | Authoritative source document (URL or short citation) the value was read from. |
| `source_page` | `string` | `none` | yes | Page / table / sheet locator within source_doc. |

## capacity-market-auction-price

Published capacity-market auction/spot clearing-price history per ISO, delivery
years <= 2026/27 only. A VALIDATION OBSERVABLE (CR-2 / T3.1) — compared against
the model's implemented demand-curve mechanism, never pinned or fit to (rules
1/13). Schema:
[`schema/capacity-market-auction-price.schema.yaml`](schema/capacity-market-auction-price.schema.yaml).

- **Keys:** `iso`, `delivery_year`, `season`, `area`, `auction_round`
- **Reconciles:** PJM Base Residual Auction (RTO + LDA), NYISO monthly Spot
  Market Auction (NYCA + locality), ISO-NE Forward Capacity Auction (system +
  capacity zone), MISO Planning Resource Auction (per LRZ, seasonal from
  PY2025-26) — onto one canonical frame keyed on `(iso, delivery_year, season,
  area, auction_round)`. CAISO carries no centralized auction (expected empty);
  ERCOT excluded. Delivery-year cutoff enforced by `validate_tidy` in
  `scripts/lib/capacity_market_auction_price/__init__.py`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO publishing the value (PJM, NYISO, ISONE, MISO, CAISO). |
| `delivery_year` | `string` | `none` | no | Delivery/planning/capability year the auction covers, as a label (e.g. "2026/2027"). Restricted at intake to delivery years <= 2026/27. |
| `season` | `string` | `none` | no | Season the clearing price applies to: annual \| summer \| fall \| winter \| spring. Only MISO (seasonal since PY2025-26) and NYISO (summer/winter capability periods, where published separately) use non-annual seasons; all other ISOs use "annual". |
| `area` | `string` | `none` | no | Capacity area the price applies to — an LDA (PJM), Local Resource Zone (MISO), locality (NYISO), capacity zone (ISO-NE), or the system-wide label (RTO / NYCA / SYSTEM / MISO) for system rows. |
| `area_type` | `string` | `none` | no | Kind of area — one of lda \| lrz \| locality \| capacity_zone \| rto \| resource (CAISO's CPM backstop designates/clears at individual-resource granularity, not a zone) \| import_interface (an external tie that clears its own price, e.g. ISO-NE's New Brunswick interface). |
| `auction_round` | `string` | `none` | no | Canonical auction/product type: base_residual_auction (PJM) \| incremental_auction (PJM) \| spot (NYISO) \| forward_capacity_auction (ISO-NE) \| planning_resource_auction (MISO) \| cpm_backstop (CAISO, if any clears). |
| `clearing_price` | `float64` | `none` | yes | The published clearing price (per price_unit). Null only when the row exists solely to carry a cleared_mw value the source publishes without a price (rare); at least one of clearing_price / cleared_mw must be non-null (enforced by validate_tidy, not the writer's dtype check). |
| `price_unit` | `string` | `none` | yes | Unit of clearing_price — usd_per_mw_day \| usd_per_kw_month \| usd_per_kw_yr \| usd_per_mw_yr. |
| `cleared_mw` | `float64` | `mw` | yes | Total capacity cleared in this area/round, if published. Null when not stated. |
| `source_doc` | `string` | `none` | yes | Authoritative source document (URL or short citation) the value was read from. |
| `source_page` | `string` | `none` | yes | Page / table locator within source_doc. |

## capacity-market-auction-supply

Published capacity-auction supply-side QUANTITY accounting per ISO — offered
and cleared MW by planning-resource category plus the auction's own
requirement/commitment ledger rows (PRMR, FRAP, self-scheduled, committed) — by
planning year, season and area. The quantity half of the capacity-auction
record that capacity-market-auction-price carries the price half of. A
rule-13-admissible published ACCOUNTING-BASIS input (e.g. the wedge between a
census-accreditation ledger and the market's counted supply); the cleared rows
are validation observables. Never a quantity target. Schema:
[`schema/capacity-market-auction-supply.schema.yaml`](schema/capacity-market-auction-supply.schema.yaml).

- **Keys:** `iso`, `planning_year`, `season`, `area`, `metric`, `category`
- **Reconciles:** MISO PRA Results Postings — the "Seasonal Supply Offered and
  Cleared Comparison Trend" category tables (Generation / External Resources /
  Behind-the-Meter Generation / Demand Resources / Energy Efficiency, in ZRC)
  and the seasonal "PRA Results by Zone" System/subregion ledger rows (PRMR,
  Offer Submitted, FRAP, Self-Scheduled, Committed, in MW SAC) — onto one
  canonical frame keyed on `(iso, planning_year, season, area, metric,
  category)`. MISO to date (capx D31, 2026-09-02); per-ISO parsing lives in
  `scripts/lib/capacity_market_auction_supply/<iso>.py`.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO publishing the accounting (MISO PRA; PJM RPM BRA Demand Resource offered/cleared UCAP per delivery year since capx D48, 2026-09-04). |
| `planning_year` | `string` | `none` | no | Planning/delivery year label the auction governs, in the ISO's own convention (e.g. "2025-2026" for a MISO Planning Year; "2025/2026" for a PJM Delivery Year, matching the sibling demand-curve / auction-price datatypes). |
| `season` | `string` | `none` | yes | Season the row applies to (summer \| fall \| winter \| spring) for seasonally-cleared auctions (MISO PRA from PY2023-24); null for annual-only records. |
| `area` | `string` | `none` | no | Scope of the row: "System" for ISO-wide rows, a subregion label (MISO "North/Central" \| "South") for subregional ledger rows. |
| `metric` | `string` | `none` | no | Canonical metric. Category quantities: offered \| cleared (paired with a non-null category — the posting's "Offered (ZRC)" / "Cleared (ZRC)" columns). Requirement/commitment ledger rows (category null): prmr (the vertical-era single Planning Reserve Margin Requirement) \| initial_prmr \| final_prmr (the RBDC-era pair: pre-auction requirement and the cleared curve-intersection quantity) \| offer_submitted (total offers incl. FRAP) \| frap (Fixed Resource Adequacy Plan self-supply) \| self_scheduled \| non_ss_offer_cleared \| committed (offer cleared + FRAP — the auction's committed total). |
| `category` | `string` | `none` | yes | Planning-resource category for offered/cleared rows: generation \| external_resources \| behind_meter_generation \| demand_resources \| energy_efficiency \| total. Null for requirement/commitment ledger metrics. |
| `value_mw` | `float64` | `MW` | no | The row's quantity in MW (ZRC or SAC per unit). |
| `unit` | `string` | `none` | no | Quantity basis as the source labels it: mw_zrc (Zonal Resource Credits — the MISO category trend tables) \| mw_sac (MW Seasonal Accredited Capacity — the MISO zonal-results ledger rows) \| mw_ucap (PJM Unforced Capacity — the BRA reports' offered/cleared UCAP rows). Numerically the same accredited-MW basis; the label preserves the source's own terminology. |
| `vintage` | `string` | `none` | yes | The publishing document's own label/date (e.g. "PY2025-26 PRA Results Posting (05/29/2025, corrections)"), distinct from planning_year. |
| `source_doc` | `string` | `none` | yes | Authoritative source document (URL or citation) the value was read from. |
| `source_page` | `string` | `none` | yes | Page / table locator within source_doc. |

## capacity-market-elcc

Published Effective Load Carrying Capability / capacity-accreditation ratings
for wind/solar/storage — and, since PJM's 2025/26 CIFP reform extended ELCC
class ratings to thermal, thermal (nuclear, coal, gas CC/CT, diesel, steam) —
resource classes, by study vintage and — where an ISO publishes a genuine
marginal-ELCC study — installed-penetration level. The CR-3.1 input that will
replace the flat `RENEWABLE_CAPACITY_CREDIT` wind/solar constants, and the
supply-basis-extension input for the accreditation-basis adjudication (R3).
Schema:
[`schema/capacity-market-elcc.schema.yaml`](schema/capacity-market-elcc.schema.yaml).

- **Keys:** `iso`, `resource_class`, `study_vintage`, `penetration_pct`
- **Reconciles:** PJM ELCC Class Ratings (single current-fleet point per class,
  renewable/storage/DR + thermal), MISO wind/solar marginal ELCC by penetration
  (Accreditation Reform — the strongest public multi-point curve), NYISO
  ICAP/UCAP conversion factors (CATF), ISO-NE seasonal-claimed-capability /
  ELCC-based accreditation, CAISO/CPUC NQC + E3-authored incremental-ELCC
  studies — onto one canonical frame keyed on `(iso, resource_class,
  study_vintage, penetration_pct)`. ERCOT excluded.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO publishing the study (PJM, NYISO, ISONE, MISO, CAISO). |
| `resource_class` | `string` | `none` | no | Canonical resource class: wind \| solar \| wind_offshore \| hybrid_solar_storage \| storage_2hr \| storage_4hr \| storage_6hr \| storage_8hr \| storage_10hr \| storage_ldes (long-duration storage where the ISO study does not state a discrete hour duration) \| nuclear \| coal \| gas_cc \| gas_ct \| gas_ct_dual_fuel \| diesel \| oil_ct \| steam \| waste_to_energy \| other (ISO-native duration/class labels map onto the nearest storage_Nhr bucket; a class with no clean map uses "other" and documents the native label in source_page). Thermal classes (nuclear through waste_to_energy) are kept distinct per the rating ISO's own published class split rather than collapsed — e.g. PJM's Gas Combustion Turbine vs. …Dual Fuel, or Diesel Utility vs. Oil-Fired Combustion Turbine, carry materially different ratings within the same study_vintage and would otherwise collide against key_columns. |
| `study_vintage` | `string` | `none` | no | The study or filing year/label the rating applies to (e.g. "2026/2027" delivery year for an annual class-rating filing, or the ELCC study's own publication year for a standalone study). |
| `penetration_pct` | `float64` | `pct` | yes | Installed-penetration level this point is measured at (per penetration_unit), for ISOs that publish a genuine multi-point ELCC-vs-penetration curve. Null when the ISO publishes only a single current-fleet-average rating (documented as such in the raw README) — never back-filled with a guessed penetration level. |
| `penetration_unit` | `string` | `none` | yes | Basis of penetration_pct — pct_of_peak_load \| pct_of_installed_capacity \| installed_mw. Null when penetration_pct is null. |
| `elcc_pct` | `float64` | `pct` | yes | The ELCC / accreditation rating at this point, as a percent of nameplate (e.g. 43.7 for a wind class rated at 43.7% UCAP). Null only when a source publishes the rating in MW terms without a percent basis (rare); never guessed. |
| `elcc_type` | `string` | `none` | no | class_average (single current fleet-wide rating) \| marginal (rating of the next incremental MW at this penetration) \| incremental (rating of a discrete tranche added at this penetration — used interchangeably with marginal by some ISOs; recorded as published). |
| `source_doc` | `string` | `none` | yes | Authoritative source document (URL or short citation) the value was read from. |
| `source_page` | `string` | `none` | yes | Page / table locator within source_doc (also carries the zone/subregion label when the ISO publishes per-zone curves). |

## transfer-constraint-binding

Measured binding record (posted shadow prices + live demand-curve breakpoints)
for published inter-regional transfer constraints — MISO's RDT from the public
`{da,rt}_pbc` market reports. Schema:
[`schema/transfer-constraint-binding.schema.yaml`](schema/transfer-constraint-binding.schema.yaml).

- **Keys:** `iso`, `market`, `constraint`, `interval_start_utc`
- **Reconciles:** Verbatim per-day pbc rows (one row per constraint-interval
  with a nonzero preliminary shadow price; DA hourly, RT 5-minute; MISO market
  time = EST year-round) consolidated per (market, market-date year),
  directions normalized from the posted constraint names. Backcast VALIDATION
  series ONLY — when a constraint binds is a dispatch outcome, so this is never
  an LP input (rule #13); it anchors model-vs-measured RDT binding frequency,
  shadow depth, and violation incidence. The posted shadow is the pbc
  constraint's own dual; the RPE's additive $200 lands on subregional price
  separation and has no public record (2024 MISO SOM §II.E/§III.B). Per-ISO
  specs in `scripts/lib/transfer_constraint_binding/` (MISO first);
  train-window years only (rule #22 guard in the fetch script).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO identifier (MISO). |
| `market` | `string` | `none` | no | Market run — "da" (hourly) or "rt" (5-minute intervals). |
| `constraint` | `string` | `none` | no | Constraint name exactly as posted, e.g. "RDT_SO_MW (South_North)" / "RDT_MW_SO (North_South)". |
| `direction` | `string` | `none` | no | Normalized transfer direction parsed from the constraint name: "S_to_N" or "N_to_S". |
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC interval start. Source timestamps are MISO market time (EST, UTC-5 fixed year-round — the report's MARKET_HOUR_EST column); DA rows are hour-beginning (labels 00-23), RT rows are 5-minute interval starts. |
| `interval_start_est` | `datetime64[ns]` | `local_timestamp` | yes | Posted EST wall-clock interval start (informational). |
| `shadow_price_usd_mwh` | `float64` | `usd_per_mwh` | no | Preliminary shadow price exactly as posted (negative while binding; -40 marks the first TCDC step's plateau, i.e. flow in real violation within (100%, 102%] of the modeled limit). |
| `curvetype` | `string` | `none` | yes | Demand-curve type as posted (observed values — PERCENT). |
| `bp1_pct` | `float64` | `percent_of_modeled_limit` | yes | Demand-curve breakpoint 1 (percent of the modeled limit). |
| `pc1_usd_mwh` | `float64` | `usd_per_mwh` | yes | Demand-curve price at/above breakpoint 1. |
| `bp2_pct` | `float64` | `percent_of_modeled_limit` | yes | Demand-curve breakpoint 2. |
| `pc2_usd_mwh` | `float64` | `usd_per_mwh` | yes | Demand-curve price at/above breakpoint 2. |
| `bp3_pct` | `float64` | `percent_of_modeled_limit` | yes | Demand-curve breakpoint 3. |
| `pc3_usd_mwh` | `float64` | `usd_per_mwh` | yes | Demand-curve price at/above breakpoint 3. |
| `bp4_pct` | `float64` | `percent_of_modeled_limit` | yes | Demand-curve breakpoint 4 (DA posts a 999999 sentinel top). |
| `pc4_usd_mwh` | `float64` | `usd_per_mwh` | yes | Demand-curve price at/above breakpoint 4 (often blank). |
| `override` | `bool` | `none` | no | Operator override flag as posted (OVERRIDE column; 3 RT rows in 2023 carry it, coinciding with a $3,000 emergency curve variant). |
| `override_reason` | `string` | `none` | yes | Posted override REASON text (blank in almost all rows). |

## maxgen-events

Declared capacity-emergency event windows (the ISO's public emergency-procedure
ladder, MISO Max Gen family first) — the M-1 registry of the MISO
price-formation lane. Schema:
[`schema/maxgen-events.schema.yaml`](schema/maxgen-events.schema.yaml).

- **Keys:** `iso`, `level`, `region`, `start_utc`
- **Reconciles:** Hand-curated per-ISO rows transcribed from primary IMM/SOM
  documents (`data/raw/maxgen-events/<iso>/<iso>.csv`, endpoints in the ISO's
  operating time; MISO market time = EST year-round) converted to UTC via the
  per-ISO spec in `scripts/lib/maxgen_events/`. Rule-13 class: declared
  physical/market availability events (the CAMPD-outage-window overlay family;
  backcast/calibration only — a forecast year carries the class outage-rate
  machinery instead). F4 discipline: a window with no primary document is NOT a
  row — never reconstructed from prices or a residual; adjudicated absences
  (Jan-2024 Heather, Jan-2025 Enzo) live in the raw README. Scopes the M-2
  `unit_outage_maxgen_events` revealed-derate channel
  (docs/handoffs/miso-price-formation-design-2026-07.md).

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO that issued the declaration (MISO today; the ladder vocabulary is per-ISO via the intake registry). |
| `region` | `string` | `none` | no | Declared scope, canonical lowercase (footprint / midwest / south for MISO) -- exactly as the primary document scopes it, never inferred. |
| `level` | `string` | `none` | no | Declared ladder level, closed vocabulary -- capacity_advisory \| maxgen_alert \| maxgen_warning \| maxgen_event_step1 .. step5 (pre-2026 MISO ladder; MISO's 3-step simplification effective 2026-06-01, KA-01551, is a future vocabulary version). |
| `start_utc` | `datetime64[ns, UTC]` | `none` | no | Window start (UTC). Converted from the ISO's operating time (MISO market ops run on EST, UTC-5, year-round) by the curation parser. |
| `end_utc` | `datetime64[ns, UTC]` | `none` | no | Window end (UTC) -- the last declared instant. Day-precision declarations span the full declared day. |
| `declared_precision` | `string` | `none` | no | Coarsest endpoint precision the primary document states -- hour when both endpoints are declared to the minute/hour, day when either endpoint is only day-scoped (the row then spans the declared day(s); notes carry the detail). |
| `source_url` | `string` | `none` | no | Authoritative URL of the primary document declaring the window. |
| `source_doc` | `string` | `none` | no | Document title + page reference within source_url. |
| `accessed` | `datetime64[ns]` | `none` | no | Date the source was fetched/verified (intake vintage stamp). |
| `notes` | `string` | `none` | yes | Free-text context -- declared-hour caveats, emergency-pricing tier effects, related instruments outside the ladder. |

## carbon-auction-results

RGGI and CARB/Quebec cap-and-trade auction clearing-price history (2023-2025) —
a validation observable for model carbon-price trajectories, never fit to.
Schema:
[`schema/carbon-auction-results.schema.yaml`](schema/carbon-auction-results.schema.yaml).

- **Keys:** `program`, `year`, `quarter`
- **Reconciles:** Per-auction clearing prices (and allowance volumes where
  known) for RGGI's quarterly CO2 allowance auctions and the CARB/Quebec
  quarterly joint cap-and-trade auctions, transcribed from the programs'
  published auction-results postings.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `program` | `string` | `none` | no | RGGI or CARB (the CARB rows are the joint California-Quebec auction). |
| `year` | `int64` | `year` | no | Calendar year the auction was held. |
| `quarter` | `int64` | `none` | no | Calendar quarter (1-4) the auction was held in. |
| `auction_date` | `string` | `none` | yes | Exact auction date (ISO YYYY-MM-DD string), where confirmed by the source. Null when only the (year, quarter) is confirmed. |
| `auction_number` | `string` | `none` | yes | The program's own sequential auction number (e.g. RGGI "70", CARB "44th joint auction"), where explicitly confirmed by a source -- never inferred by arithmetic from neighboring auctions (CLAUDE.md: no value guessing). |
| `clearing_price` | `float64` | `mixed` | no | The settlement/clearing price, in the unit given by `price_unit`. |
| `price_unit` | `string` | `none` | no | usd_per_short_ton (RGGI) \| usd_per_tonne (CARB, metric tonne CO2e). |
| `allowances_sold` | `float64` | `none` | yes | Allowances sold at this auction, where known (populated for every RGGI row; not recovered for any CARB row during this intake). |
| `allowances_offered` | `float64` | `none` | yes | Allowances offered at this auction, where known. |
| `source_doc` | `string` | `none` | no | Authoritative document/page the value is drawn from. |
| `source_page` | `string` | `none` | yes | URL or section reference within source_doc. |

## eia-aeo-fuel-prices

EIA Annual Energy Outlook gas/coal/oil price trajectories (AEO2025, 2024-2050)
— the forecast-side fuel-price scenario anchor. Schema:
[`schema/eia-aeo-fuel-prices.schema.yaml`](schema/eia-aeo-fuel-prices.schema.yaml).

- **Keys:** `fuel`, `metric`, `region`, `scenario`, `year`
- **Reconciles:** AEO2025 Henry Hub natural gas, delivered-to-electric-power
  and minemouth coal (national + supply region), and oil (WTI crude,
  electric-power delivered distillate/residual) trajectories across the
  Reference / High and Low Oil-and-Gas-Supply cases, from the EIA AEO data
  tables.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `fuel` | `string` | `none` | no | One of gas \| coal \| oil. |
| `metric` | `string` | `none` | no | Which published AEO series within the fuel: henry_hub_spot (gas); wti_spot_crude \| electric_power_distillate \| electric_power_residual (oil); delivered_electric_power \| minemouth_average \| minemouth_by_region (coal). |
| `region` | `string` | `none` | no | "usa" for every national series, or an EIA coal supply-region code (appalachia \| east_of_mississippi \| interior \| west \| west_of_mississippi) for the minemouth_by_region metric (AEO Table 65). |
| `scenario` | `string` | `none` | no | AEO2025 scenario id: ref2025 (Reference -> model "mid" gas_price_path), highogs (High Oil and Gas Supply -> model "low", more supply/lower price), lowogs (Low Oil and Gas Supply -> model "high"). |
| `scenario_name` | `string` | `none` | no | Human-readable AEO scenario description, as returned by the API. |
| `year` | `int64` | `year` | no | Calendar year (AEO2025 covers 2024-2050). |
| `value` | `float64` | `mixed` | no | The price, in the unit given by the `unit` column. |
| `unit` | `string` | `none` | no | EIA's own unit string for this series, e.g. "2024 $/MMBtu", "2024 $/b", "2024 $/gal", "2024 $/st" — real (2024-dollar) terms throughout, never nominal. |
| `series_id` | `string` | `none` | no | EIA AEO API series identifier (exact-cell traceability). |
| `table_id` | `string` | `none` | no | EIA AEO table number the series belongs to (13, 12, 15, or 94). |
| `table_name` | `string` | `none` | no | Human-readable AEO table title, as returned by the API. |

## ira-credit-parameters

Post-OBBBA IRA credit statute parameters (45U, 45Y, 48E) — the policy inputs to
the IRA credit machinery in `policy/ira.py`. Schema:
[`schema/ira-credit-parameters.schema.yaml`](schema/ira-credit-parameters.schema.yaml).

- **Keys:** `statute_section`, `parameter`
- **Reconciles:** Section 45U / 45Y / 48E statute parameters as enacted,
  including the One Big Beautiful Bill Act (OBBBA, Pub. L. 119-21, 2025-07-04)
  amendments (FEOC restrictions, phase-out schedules), transcribed from the
  statute text with per-row citations.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `statute_section` | `string` | `none` | no | One of 45U \| 45Y \| 48E. |
| `parameter` | `string` | `none` | no | Snake_case parameter name within the section (e.g. base_credit_rate, phase_down_boc_year_75pct, wind_solar_placed_in_service_cutoff). See README for the full per-section parameter list. |
| `value` | `string` | `none` | no | The parameter's value as a string; parse per `value_type`. Kept as string (not split across typed columns) because this table deliberately mixes rates, dates, and booleans in one small hand-curated registry. |
| `value_type` | `string` | `none` | no | How to parse `value` -- numeric \| date (ISO YYYY-MM-DD) \| boolean. |
| `unit` | `string` | `none` | no | Unit for a numeric value (cents_per_kwh \| percent \| multiplier_x \| years \| year \| gCO2e_per_kwh), or the literal "date"/"boolean" for those value_types. |
| `notes` | `string` | `none` | yes | Free-text clarification of the parameter's meaning or scope. |
| `source_doc` | `string` | `none` | no | Authoritative statute citation or secondary-source document. |
| `source_page` | `string` | `none` | yes | Subsection/citation pinpoint within source_doc. |

## nrel-atb

NREL Annual Technology Baseline CAPEX / Fixed-O&M trajectories (ATB 2024,
versions v3.0.0 and v4.0.0, 2022-2050) — the new-entry cost surface for the
capacity-evolution screens. Schema:
[`schema/nrel-atb.schema.yaml`](schema/nrel-atb.schema.yaml).

- **Keys:** `atb_edition_year`, `atb_version`, `technology`, `techdetail`,
  `parameter`, `financial_case`, `tax_credit_case`, `cost_case`, `year`
- **Reconciles:** ATB 2024 trajectories for the technologies the model builds
  as new entry (wind, solar, gas CC/CT/CCS, nuclear SMR/large, utility battery
  storage at 5 durations) plus cross-reference technologies, from the published
  ATB workbook.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `atb_edition_year` | `int64` | `year` | no | ATB report edition/vintage (e.g. 2024 for this intake) -- NOT the projection year. Lets a future ATB 2025/2026 edition land as new rows without a schema change. |
| `atb_version` | `string` | `none` | no | NREL's point-release version of that edition, as published in the OEDI object path (e.g. "v3.0.0", "v4.0.0"). An ATB edition is re-released under a new version when NREL corrects or refreshes it, so edition-year ALONE does not identify a vintage: ATB 2024 exists as v2.0.0/v3.0.0/v4.0.0. Part of the key so successive versions of one edition coexist in this partition instead of colliding, and so a consumer pins the exact bytes it derived from (FFR-PB, 2026-07-31 -- v4.0.0 revised the Geothermal/DeepEGSFlash Moderate CAPEX and Fixed O&M trajectories relative to v3.0.0; see data/raw/nrel-atb/README.md). |
| `technology` | `string` | `none` | no | ATB's technology field (e.g. LandbasedWind, UtilityPV, Nuclear). |
| `techdetail` | `string` | `none` | no | ATB's resource-class / configuration detail within technology (e.g. Class4, "Nuclear - Large", "NG 2-on-1 Combined Cycle (F-Frame)", "4Hr Battery Storage"). |
| `display_name` | `string` | `none` | no | ATB's human-readable technology + techdetail label. |
| `parameter` | `string` | `none` | no | One of CAPEX \| Fixed O&M \| Variable O&M \| Heat Rate (ATB's core_metric_parameter, filtered to this subset). The parameter scope is PER TECHNOLOGY: every technology lands CAPEX and Fixed O&M; only NaturalGas_FE additionally lands Variable O&M and Heat Rate (capx D65-B, 2026-09-06 — see scripts/data/fetch_nrel_atb.py's EXTRA_PARAMETERS_BY_TECHNOLOGY for why). So a row set filtered to one parameter is not populated for every technology. |
| `financial_case` | `string` | `none` | no | ATB's core_metric_case. Only "Market" is landed (the market-financed view a capacity-expansion screen wants); ATB's "R&D" (program-cost) case is out of scope and never appears here. |
| `tax_credit_case` | `string` | `none` | yes | ATB's tax_credit_case tag (ITC \| PTC), where the technology carries one; null for technologies with neither (e.g. natural gas). Informational only -- verified during intake that CAPEX/Fixed O&M/etc. do not vary by this tag for a fixed (technology, techdetail, year, cost_case); it does not multiply row count. |
| `cost_case` | `string` | `none` | no | ATB's scenario field, renamed to avoid clashing with this model's own "scenario" concept: Advanced \| Moderate \| Conservative. Maps to this model's tech_cost_path lever ("low"/"mid"/"high" -> Advanced/Moderate/ Conservative respectively, matching TECH_COST_MULTIPLIERS' existing documented mapping in constants.py). |
| `is_default_class` | `bool` | `none` | no | Whether ATB flags this techdetail as the technology's own representative/ default resource class (its `default` column). Informational -- lets a consumer that only wants one row per technology filter on this. |
| `year` | `int64` | `year` | no | Calendar (projection) year, ATB's core_metric_variable (2022-2050). |
| `value` | `float64` | `mixed` | no | The metric's value, in the unit given by the `unit` column. |
| `unit` | `string` | `none` | no | Unit for `value`, by parameter (the raw ATBe.csv's own `units` column ships empty for every row -- confirmed during intake, not a fetch bug -- so this is an annotation applied during curation from ATB's public documentation/glossary convention, not extracted verbatim from the source file): CAPEX = "2022 $/kW", Fixed O&M = "2022 $/kW-yr", Variable O&M = "2022 $/MWh", Heat Rate = "MMBtu/MWh" (a physical quantity, so it carries no dollar year). ATB 2024's dollar year is 2022. VERIFIED 2026-07-31 (FFR-PB) by direct fetch of the ATB site's own 2024 electricity page, which states "Monetary values are in 2022$" -- this CLOSES the former "confirmed only via indexed/cached content, flagged for verification with browser access" caveat. The site moved to atb.nlr.gov on the lab's rename and that domain IS reachable here, unlike the proxy-blocked atb.nrel.gov the earlier intake tried (see data/raw/nrel-atb/README.md). |
| `source_doc` | `string` | `none` | no | Citation string for the row's own edition/version ("NREL ATB 2024 v3.0.0 electricity, OEDI data lake"; "NREL ATB 2024 v4.0.0 electricity, OEDI data lake"). |
| `source_page` | `string` | `none` | yes | The originating S3 object key (full traceability to the source file). |

## storage-as-awards

Measured ancillary-service MW AWARDED to the storage fleet — the
resource-type-resolved counterpart of `ancillary-services` and the measured
input for storage AS power-reservation mechanisms (rule 13's own worked
example). Schema:
[`schema/storage-as-awards.schema.yaml`](schema/storage-as-awards.schema.yaml).

- **Keys:** `iso`, `resource_class`, `market`, `product`, `interval_start_utc`
- **Reconciles:** Per-ISO storage AS award layouts (CAISO Daily Energy Storage
  Report, and siblings per the schema header) onto one tidy frame; awarded MW
  is capacity committed to reserves that cannot simultaneously offer energy
  arbitrage.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC start of the hour. |
| `interval_start_local` | `datetime64[ns]` | `local_timestamp` | yes | Prevailing local wall-clock hour start (informational). |
| `iso` | `string` | `none` | no | ISO/RTO code. |
| `resource_class` | `string` | `none` | no | Storage resource class holding the award — "battery" or "hybrid". |
| `market` | `string` | `none` | no | Market run — "DAM" (day-ahead; CAISO IFM) or "RTM" (real-time; CAISO RTPD, hourly-averaged). |
| `product` | `string` | `none` | no | AS product on the reconciled taxonomy — "reg_up", "reg_down", "spin", "nonspin". |
| `award_mw` | `float64` | `mw` | no | Hourly-mean awarded AS capacity held by the class, MW. |

## capacity-market-avoidable-cost-rate

Published default/generic Avoidable Cost Rate benchmarks by technology class —
the going-forward-cost identification source for the retirement/entry screens'
GFC construction. Schema:
[`schema/capacity-market-avoidable-cost-rate.schema.yaml`](schema/capacity-market-avoidable-cost-rate.schema.yaml).

- **Keys:** `iso`, `source_type`, `technology_class`, `capacity_bin`,
  `cost_component`, `vintage`
- **Reconciles:** PJM Tariff/Manual-18 default gross ACR tables
  (source_type=pjm_manual18_default) and Monitoring Analytics' independent SOM
  avoidable-cost benchmarks (source_type=monitoring_analytics_som) on one tidy
  frame.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO the benchmark applies to (PJM today; shape is ISO-agnostic so a future ISO's analogous published benchmark can be added additively). |
| `source_type` | `string` | `none` | no | Which publisher's benchmark this row carries: pjm_manual18_default (the RTO's own default/generic gross ACR table used in the Tariff/Manual 18 deactivation and must-offer-exception process) \| monitoring_analytics_som (the Independent Market Monitor's own avoidable-cost benchmark, State of the Market report — an independent, arm's-length estimate of the same concept, published separately from PJM's own default table). |
| `technology_class` | `string` | `none` | no | Native published technology/unit-type label (e.g. "Combined Cycle", "Combustion Turbine", "Steam Turbine - Coal", "Nuclear", "Diesel") — recorded as the source states it; no fixed controlled vocabulary (PJM's own class breakdown does not map 1:1 onto config/plant_taxonomy.py's dispatch fuel classes; document the source's own label exactly and leave the model-taxonomy mapping to a future wiring session). |
| `capacity_bin` | `string` | `none` | yes | Native unit-size bucket the rate applies to (e.g. "under 50 MW", "50-150 MW", "over 150 MW"), as published — fixed costs don't scale linearly with size so several PJM ACR tables bin by capacity. Null when the source publishes one rate per technology_class regardless of size. |
| `cost_component` | `string` | `none` | no | Canonical cost component: gross_acr (the total default Avoidable Cost Rate, the headline figure most sources publish) \| avoidable_capital_recovery (the avoidable-capital-investment-recovery subcomponent, where published separately) \| avoidable_fixed_om (avoidable fixed O&M subcomponent, where published separately) \| avoidable_variable_om (avoidable variable O&M subcomponent, where published separately) \| net_acr (gross ACR net of an assumed energy/AS margin offset, where a source publishes this distinct net figure rather than leaving the netting to the screen) \| reactive_offset (a published OUT-OF-MARKET revenue component the ISO's own capacity demand curve nets against gross ACR when it computes the reference resource's E&AS offset — PJM's Tariff Schedule 2 reactive component is the only member today; it belongs to this datatype because it is published in the same $/MW-yr going-forward frame and is netted against these same gross-ACR rows, not because it is itself a cost). |
| `value` | `float64` | `none` | no | The published rate, in the units given by `unit`. |
| `unit` | `string` | `none` | no | Unit of `value`: usd_per_mw_yr \| usd_per_kw_month \| usd_per_mw_day \| usd_per_kw_yr. |
| `vintage` | `string` | `none` | no | The publication's own filing/report label and effective date (e.g. "PJM Manual 18, Revision 62, effective 2025-12-17" or "2025 State of the Market Report for PJM, Volume 2, Section 9, published 2026-03-11"). |
| `source_doc` | `string` | `none` | yes | Authoritative source document (URL or short citation) the value was read from. |
| `source_page` | `string` | `none` | yes | Page / table / section locator within source_doc. |

## uranium-marketing-price

EIA Uranium Marketing Annual Report weighted-average uranium (U3O8e) and
enrichment-services (SWU) prices — the measured front-end-fuel-cycle basis for
a nuclear fuel cost (D2 gap). Schema:
[`schema/uranium-marketing-price.schema.yaml`](schema/uranium-marketing-price.schema.yaml).

- **Keys:** `metric`, `delivery_year`
- **Reconciles:** EIA UMAR price series as published; the $/MMBtu build-up
  (burnup/thermal-efficiency + conversion cost) is left to the consuming
  derivation (P-1D), cited to this data per rule 23.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `metric` | `string` | `none` | no | One of total_purchased_quantity (Table S1a "Total purchased", million lb U3O8e) \| total_purchased_price (Table S1b "Total purchased (weighted-average price)", $/lb U3O8e) \| enrichment_services_price (Table S2 "Average price (US$ per SWU)"). |
| `delivery_year` | `int64` | `year` | no | Calendar delivery year, 2002-2024. enrichment_services_price has no rows for 2002-2005 (the source report marks those years "not available", not zero -- omitted rather than a fabricated/null value). |
| `value` | `float64` | `mixed` | no | The quantity or price, in the unit given by the `unit` column. |
| `unit` | `string` | `none` | no | million_lb_u3o8e (quantity) \| usd_per_lb_u3o8e (uranium price, nominal $) \| usd_per_swu (enrichment price, nominal $). |
| `source_doc` | `string` | `none` | no | Authoritative EIA document the value is drawn from. |
| `source_page` | `string` | `none` | yes | Table reference within source_doc (e.g. "Table S1b"). |

## benchmark-corridor

External forecast-corridor anchors — 2030/2035/2040 capacity mix, energy mix,
and power-sector CO2 by ISO/region — for the FC-5 external-corridor context
check. Context only, never a fit target (rule 13). Schema:
[`schema/benchmark-corridor.schema.yaml`](schema/benchmark-corridor.schema.yaml).

- **Keys:** `source`, `iso`, `region`, `scenario`, `target_year`, `quantity`,
  `tech`
- **Reconciles:** EIA AEO2025 regional electricity tables (Table 54 + Table 56,
  fetched via the API), NREL Standard Scenarios, and ISO planning documents
  (ERCOT CDR, PJM Load Forecast, NYISO Gold Book, ISO-NE CELT, CAISO/CPUC
  IEPR/PSP, MISO futures — manual downloads) onto one tidy (source, iso,
  region, scenario, target_year, quantity, tech) frame with a canonical
  quantity/technology vocabulary. Per-ISO rows in one file (iso column key); an
  ISO total sums its region rows.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `source` | `string` | `none` | no | Controlled benchmark-source id — one per external outlook/vintage, e.g. AEO2025 \| StdScen2024 \| ERCOT_CDR_2025 \| PJM_LOAD_2026 \| PJM_RTEP_2024 \| NYISO_GOLDBOOK_2026 \| ISONE_CELT_2026 \| CAISO_IEPR_2025 \| CPUC_PSP_2024 \| MISO_FUTURES. A non-reference scenario of the same outlook takes its own source id (so `scenario` describes the case; `source` identifies the run). |
| `iso` | `string` | `none` | no | ISO/RTO the row maps onto: ERCOT \| PJM \| MISO \| NYISO \| NEISO \| CAISO, or "national" for a US/system anchor. For AEO2025 this is the ISO an EMM region crosswalks to (the footprints are approximate — see `note`). |
| `region` | `string` | `none` | no | The source's native geography label the value applies to: an AEO EMM region name (e.g. "Texas Reliability Entity", "PJM/East"), an ISO's own zone/area/system label, or "national". An ISO total for a multi-region source is the sum over that ISO's region rows. |
| `vintage` | `string` | `none` | no | Publication vintage of the source, YYYY or YYYY-MM (e.g. "2025-04" for AEO2025, "2024" for StdScen 2024, "2025-12" for the Dec-2025 ERCOT CDR). |
| `scenario` | `string` | `none` | no | The source's case/scenario label as a lower_snake token: reference \| mid \| protocol \| sb6 \| high \| low \| … . AEO2025's Reference case is "reference". |
| `target_year` | `int64` | `year` | no | Projection target year the value governs (e.g. 2030, 2035, 2040). |
| `quantity` | `string` | `none` | no | Canonical quantity (the FC-5 "metric" axis): capacity \| generation \| co2 \| peak_demand \| energy_demand \| reserve_margin. The first three are the outlook-style quantities (AEO, NREL Standard Scenarios); the last three are the ISO planning-document quantities — an ISO load forecast publishes peak MW and annual GWh rather than a capacity mix. All are extensive (region rows sum to an ISO total) EXCEPT `reserve_margin`, which is a RATIO: `iso_totals()` refuses to sum it across regions rather than returning a meaningless total. |
| `tech` | `string` | `none` | no | Canonical technology/fuel the value applies to, or an aggregate: coal \| gas \| gas_cc \| gas_ct \| gas_st \| oil \| nuclear \| hydro \| wind \| offshore_wind \| solar \| solar_thermal \| geothermal \| biomass \| municipal_waste \| storage \| pumped_storage \| hydrogen \| fuel_cells \| distributed_gen \| renewables \| other \| total. `renewables` is a source's renewable aggregate; `total` is a capacity/generation grand total or the system CO2 total. |
| `value` | `float64` | `mixed` | no | The projected value, in the units named by `unit`. Always a real primary-source number (rule 5); the table carries no placeholder rows. |
| `unit` | `string` | `none` | no | Unit of `value`: GW (capacity) \| TWh (generation; AEO BkWh billion-kWh is numerically identical to TWh) \| MMst_co2 (million short tons CO2) \| MW (peak_demand) \| GWh (energy_demand) \| fraction (reserve_margin) — or the source's own unit where it differs (recorded verbatim, no conversion). Units are NOT normalised across sources: an ISO publishing peak load in MW stays in MW, so a comparison must reconcile units explicitly rather than assuming a common basis. |
| `source_doc` | `string` | `none` | yes | Authoritative source document (URL or short citation) the value was read from. |
| `source_page` | `string` | `none` | yes | Locator within source_doc — an AEO API series id, a table+page reference, or a figure number. |
| `note` | `string` | `none` | yes | Boundary caveat or context note (e.g. the EMM-region-vs-ISO-footprint approximation, a case description, or a unit/aggregation reconciliation). |

## hydro-plant-modes

Per-plant conventional-hydro operational-mode classification (shapeable
reservoir/peaking vs run-of-river/canal) — the external classifier the
RoR-split dispatch mechanism (ScenarioConfig.hydro_ror_split, caiso-126)
consumes. Schema:
[`schema/hydro-plant-modes.schema.yaml`](schema/hydro-plant-modes.schema.yaml).

- **Keys:** `iso`, `plant_id`
- **Reconciles:** ORNL EHA FY2024 per-plant Mode labels (keyed to EIA plant id)
  completed for Mode-NaN plants by the documented HILARRI v4
  reservoir-association / canal-type / Corps-dam-ownership rules in
  scripts/data/curate_hydro_plant_modes.py — all categorical, no numeric
  threshold, frozen against residuals (rule 21). CAISO-only until another ISO's
  lane reviews the completion against its own labeled subset.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | Model ISO the plant's balancing authority maps to (e.g. CAISO). |
| `plant_id` | `int64` | `none` | no | EIA plant identification code (EHA EIA_PtID), the join key the hydro budget fleet (data.hydro.load_hydro_budget) is keyed by. |
| `eha_ptid` | `string` | `none` | no | ORNL EHA plant id(s) aggregated into this row ("\|"-joined when several EHA plants share one EIA plant id). |
| `plant_name` | `string` | `none` | no | EHA plant name (first, when several share the EIA id). |
| `ch_mw` | `float64` | `MW` | no | EHA conventional-hydro capacity (CH_MW summed over the EHA plants in the row). Provenance/QA only — the LP uses EIA-860 nameplate. |
| `mode` | `string` | `none` | yes | EHA operational Mode verbatim (Run-of-river, Canal/Conduit, Peaking, Intermediate Peaking, hybrids). Null when EHA leaves the plant unclassified and the completion rule decided the row. |
| `shapeable` | `bool` | `none` | no | True = reservoir/peaking class (the plant can shape output within its monthly energy budget); False = run-of-river/canal class (output follows inflow — the RoR-split mechanism dispatches it flat at budget[g,m]/hours[m]). |
| `method` | `string` | `none` | no | Which rule classified the row: eha_mode (EHA Mode present) \| hilarri_canal (HILARRI canal/conduit project type) \| corps_dam (dam owned/operated by the U.S. Army Corps of Engineers) \| hilarri_no_reservoir (no HILARRI reservoir association) \| hilarri_reservoir (reservoir-associated, operator-controlled) \| regulated_chain (listed in the ISO's registered regulated-chain table data/raw/<iso>-hydro/<iso>_hydro_chain.csv; shapeable, overrides the rest). |
| `fc_dock` | `string` | `none` | yes | FERC licence docket (EHA FC_Dock), provenance. |
| `dam_own` | `string` | `none` | yes | Dam owner at the plant's site (EHA Dam_Own), provenance for the corps_dam completion rule. |

## miso-m2m-flowgates

Hourly per-flowgate M2M/CMP coordination record for MISO's PJM and SPP seams —
both parties' RT shadow prices, market flows and Firm Flow Entitlements plus
settlement credits (miso-77 §2a; intake miso-176). Schema:
[`schema/miso-m2m-flowgates.schema.yaml`](schema/miso-m2m-flowgates.schema.yaml).

- **Keys:** `iso`, `flowgate_id`, `interval_start_utc`
- **Reconciles:** MISO's annual public M2M_Settlement_srw_YYYY.csv
  consolidations (hour-ending 1..24 labels on fixed-EST market time, converted
  to UTC hour starts; seam_rto derived as the non-MISO RTO of the
  monitoring/counterparty pair). Rule-13 line fixed in the schema header: FFE
  columns are input-class in kind (CMP market design); shadow price / market
  flow / credit columns are ANSWER-class — validation/diagnosis only, never a
  solve input.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | Publishing ISO whose settlement view this is (MISO). |
| `interval_start_utc` | `datetime64[ns, UTC]` | `utc_timestamp` | no | tz-aware UTC hour start. Source stamps are hour-ENDING labels 1..24 on MISO market time (EST, UTC-5 fixed year-round; HE 24 posted as "24:00:00"): hour-beginning EST = posted date + (HE-1) h, UTC = +5 h. |
| `interval_start_est` | `datetime64[ns]` | `local_timestamp` | no | EST wall-clock hour start (informational; MISO market time, fixed UTC-5, no DST — full 24-label days year-round in the source). |
| `flowgate_id` | `int64` | `none` | no | NERC flowgate ID exactly as posted. |
| `flowgate_name` | `string` | `none` | no | Flowgate description as posted (monitored element + contingency tokens; stable per ID within a year with rare mid-year renames). |
| `monitoring_rto` | `string` | `none` | no | Monitoring RTO as posted — MISO, PJM, SWPP, or "NO RTO" (a small transitional class, ~30-460 rows/year). |
| `cp_rto` | `string` | `none` | no | Counterparty RTO as posted (MISO when the monitoring RTO is the neighbour; PJM/SWPP when MISO or "NO RTO" monitors). |
| `seam_rto` | `string` | `none` | no | Derived seam key — the non-MISO RTO of the (monitoring, counterparty) pair: PJM or SWPP. This is the M2M seam the flowgate's coordination belongs to. |
| `miso_shadow_price_usd_mwh` | `float64` | `usd_per_mwh` | yes | MISO's RT shadow price on the flowgate (hourly settlement basis) as posted. ANSWER CLASS — validation only. |
| `miso_mkt_flow_mw` | `float64` | `mw` | yes | MISO's market flow on the flowgate (signed; negative = counter to the flowgate's defined direction). ANSWER CLASS — validation only. |
| `miso_ffe_mw` | `float64` | `mw` | yes | MISO's Firm Flow Entitlement on the flowgate (signed like market flow). CMP market-design quantity — input-class in kind. |
| `cp_shadow_price_usd_mwh` | `float64` | `usd_per_mwh` | yes | Counterparty RTO's shadow price on the flowgate (populated on both MISO-monitored and neighbour-monitored rows). ANSWER CLASS — validation only. |
| `cp_mkt_flow_mw` | `float64` | `mw` | yes | Counterparty RTO's market flow. Populated only on MISO-monitored rows; zero-filled by the source on neighbour-monitored rows. ANSWER CLASS — validation only. |
| `cp_ffe_mw` | `float64` | `mw` | yes | Counterparty RTO's Firm Flow Entitlement. Populated only on MISO-monitored rows; zero-filled on neighbour-monitored rows. Input-class in kind where populated. |
| `miso_credit_usd` | `float64` | `usd` | yes | MISO's hourly M2M settlement credit on the flowgate as posted. ANSWER CLASS — validation only. |
| `cp_credit_usd` | `float64` | `usd` | yes | Counterparty RTO's hourly M2M settlement credit as posted. ANSWER CLASS — validation only. |

## gas-ofo-events

Declared gas-pipeline Operational Flow Orders at event-day grain — the physical
gas-deliverability events behind winter gas-scarcity days (caiso-131 A3; intake
caiso-226). Schema:
[`schema/gas-ofo-events.schema.yaml`](schema/gas-ofo-events.schema.yaml).

- **Keys:** `iso`, `utility`, `gas_day`, `side`
- **Reconciles:** Each declaring utility's public event-history ledger,
  published as one year-column HTML table per side, onto one tidy `(iso,
  utility, gas_day, side)` frame carrying the published stage, the signed
  tolerance band (negative low / positive high) and the waived flag. CAISO =
  SoCalGas ENVOY low (2015–) and high (1997–) ledgers; PG&E and the other ISOs'
  pipeline analogues are `DATA NEEDED`. Rule-13 line: a declaration is a
  published PHYSICAL availability event with a forward analogue (same class as
  the CAMPD outage windows), so it is INPUT-class; it is never a fit target,
  and no threshold keyed to a price residual may be derived from it.
  INTAKE-ONLY — no mechanism consumes it.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO whose generation fleet burns gas delivered on the declaring utility's system (CAISO for SoCalGas). Stamped from the registry spec, not published by the utility. |
| `utility` | `string` | `none` | no | Declaring gas utility / balancing entity (SOCALGAS). One ISO may be served by several -- the column keeps them separable rather than collapsing them onto the ISO. |
| `gas_day` | `datetime64[ns]` | `local_date` | no | The gas day the order applies to, tz-naive date label as the utility publishes it. A SoCalGas gas day runs 07:00-07:00 Pacific, so it is a DATE LABEL and not a midnight-to-midnight electricity day; a consumer mapping it to operating hours must apply that offset itself. |
| `side` | `string` | `none` | no | 'low' (under-delivery penalized -- the winter gas-deliverability instrument) or 'high' (over-delivery penalized -- linepack surplus). |
| `stage` | `string` | `none` | yes | Published escalation stage as printed: '1', '2', '3', '3.1', '3.2', '3.3', '4', '5', or 'EFO' (an Emergency Flow Order -- a distinct Rule 23 instrument the utility prints in the same ledger, NOT an OFO stage, and deliberately left unranked here). NULL for the pre-staging high-OFO vintage (SoCalGas printed high OFOs without a stage before mid-2018). |
| `tolerance_pct` | `float64` | `pct` | no | Published daily imbalance tolerance band, SIGNED AS PUBLISHED: negative on the low side (e.g. -5 = deliveries may fall no more than 5 percent short of burn) and positive on the high side (e.g. 10). NOT monotone in `stage`: the two are set independently by the utility -- measured on the low ledger, the WIDEST bands sit at Stage 1 (min -18) while Stage 3.2 is uniformly -5 -- so a consumer must pick the dimension it actually means rather than assuming either one ranks the other. |
| `waived` | `bool` | `none` | no | True when the utility waived the gas day's noncompliance charges (the order was declared and then relieved). Published as a '(WAIVED)' suffix on the tolerance and a red cell in the ledger. A waived day is still a declared physical event; a consumer decides whether to count it. |
| `source_doc` | `string` | `none` | no | Filename of the immutable raw snapshot under data/raw/gas-ofo-events/<iso>/ the row was parsed from, so every row traces to the exact retrieved document. |

## ps-water-state

Measured hourly pumped-storage plant operations — generation/pumping energy,
powerhouse flows, and reservoir water state — from the operator's own published
records (caiso-201 Q2(a); intake caiso-227). Schema:
[`schema/ps-water-state.schema.yaml`](schema/ps-water-state.schema.yaml).

- **Keys:** `iso`, `plant`, `interval_end_local`
- **Reconciles:** Each plant's published operations record onto one tidy `(iso,
  plant, interval_end_local)` hourly frame. CAISO = the Helms Pumped Storage
  Project (FERC P-2735) Final License Application Appendix B1 hydrology
  workbook on public FERC eLibrary (accession 20240418-5301): PG&E HEC-DSS
  hourly series 2001-01-01..2022-09-30 — the public breach of the hourly PS
  water-state wall (FINDING-caiso141). Span limitation stated honestly: the
  record ends 2022-09-30 and does not cover the 2023–2025 training years; what
  it grounds is measured multi-year hourly conduct (rule-13 INPUT-class, the
  CAMPD-history analogy). Helms 2022-10→present, Eastwood, and the DWR CDEC
  share are `DATA NEEDED`. INTAKE-ONLY — no mechanism consumes it.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO whose footprint the plant serves (CAISO for Helms). Stamped from the registry spec, not published by the operator. |
| `plant` | `string` | `none` | no | Plant key, upper-case (HELMS). One row-set per plant so further plants (Eastwood, the DWR facilities) extend the frame without schema change. |
| `interval_end_local` | `datetime64[ns]` | `local_hour_ending` | no | Hour-ending timestamp on the operator's fixed-offset local standard clock, tz-naive, rounded to the hour (the source carries sub-second HEC-DSS float drift). The published series is gap-free on this clock — no DST insertions or deletions. |
| `generation_mwh` | `float64` | `MWh` | yes | Hourly generating-mode energy (HEC-DSS PER-CUM, so MWh over the hour = average MW). Zero when the plant is idle or pumping; null where the source prints a missing-value sentinel. |
| `pumping_mwh` | `float64` | `MWh` | yes | Hourly pumping-mode energy consumed (PER-CUM), published positive. Zero when not pumping; null on a missing-value sentinel. |
| `flow_generation_cfs` | `float64` | `cfs` | yes | Hourly average water flow through the powerhouse in generating mode (PER-AVER). Includes small non-generating releases in some hours (flow can be positive with zero generation). |
| `flow_pumping_cfs` | `float64` | `cfs` | yes | Hourly average water flow in pumping mode (PER-AVER), SIGNED AS PUBLISHED: the Helms record carries 276 negative hours (-795 .. -0.03 cfs, reverse-flow metering during mode changeover). An hour may carry both generation and pumping (mode changeover within the hour). |
| `upper_elevation_ft` | `float64` | `ft` | yes | Upper reservoir (Courtright) surface elevation, instantaneous at the hour stamp (INST-VAL). Null where the sensor record is missing — the 2001-2011 vintage publishes storage without elevation for long spans. |
| `upper_storage_af` | `float64` | `acre_ft` | yes | Upper reservoir (Courtright) storage, instantaneous (INST-VAL). |
| `lower_elevation_ft` | `float64` | `ft` | yes | Lower reservoir (Wishon) surface elevation, instantaneous. |
| `lower_storage_af` | `float64` | `acre_ft` | yes | Lower reservoir (Wishon) storage, instantaneous. |
| `source_doc` | `string` | `none` | no | Filename of the immutable raw snapshot under data/raw/ps-water-state/<iso>/ the row was parsed from, so every row traces to the exact retrieved document. |

## ra-import-allocations

Resource-adequacy IMPORT CAPABILITY HOLDINGS — the MW of RA import capability
each load-serving entity holds on each intertie branch group per RA year, from
the ISO's published annual allocation results (caiso-244 §5 form (i); intake
caiso-245). Schema:
[`schema/ra-import-allocations.schema.yaml`](schema/ra-import-allocations.schema.yaml).

- **Keys:** `iso`, `delivery_year`, `lse`, `branch_group`, `start_date`,
  `end_date`
- **Reconciles:** Each ISO's published holders table onto one tidy `(iso,
  delivery_year, lse, branch_group, start_date, end_date)` frame with the MW
  held. CAISO = the annual `Holders of Import Capability` workbook (caiso.com
  library/<year>-import-allocations), 2023–2025, 234–265 rows/yr over ~60 LSEs
  and ~35 branch groups; the companion `used on annual RA plans` and Step-6
  contractual workbooks are kept raw, not curated (ambiguous grain / subset).
  Rule-13 line: a published capability RIGHT that regenerates every July for
  the following RA year — INPUT-class, never a fit target; rule 14: an
  allocation is neither a schedule nor an energy flow. INTAKE-ONLY — the
  pre-registered firm-block re-split arm was stopped by its own rule (held
  north share within 5 points of the MIC share), so no mechanism consumes it.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | ISO/RTO code (CAISO). |
| `delivery_year` | `string` | `none` | no | The RA (calendar) year the allocation applies to, e.g. "2024". |
| `lse` | `string` | `none` | no | Load-serving entity scheduling-coordinator ID as published (e.g. LCE1, LPGE, LSCE, LANC). Not resolved to a name; the ISO publishes IDs. |
| `branch_group` | `string` | `none` | no | Intertie branch group as published (e.g. PALOVRDE_ITC, MALIN500_ISL, NOB_ITC, TRACY500_BG). The suffix (_ITC / _BG / _ISL / _MSL) is the ISO's own label variant and is kept verbatim; consumers map the stem. |
| `allocation_mw` | `float64` | `MW` | no | Import capability held (MW) for the effective window. |
| `start_date` | `datetime64[ns]` | `local_timestamp` | no | Start of the holding's effective window (Pacific, tz-naive as published). |
| `end_date` | `datetime64[ns]` | `local_timestamp` | no | End of the holding's effective window (Pacific, tz-naive as published). |
| `source_doc` | `string` | `none` | no | The published workbook the row was read from (caiso.com document URL). |

## load-forecast

Each ISO's PUBLISHED long-term load forecast — annual energy and seasonal peak
by scenario, plus the published data-centre / large-load, EV and
building-electrification decompositions (SCN-LOAD, owner ruling S4 / card D-4).
Schema: [`schema/load-forecast.schema.yaml`](schema/load-forecast.schema.yaml).

- **Keys:** `iso`, `edition`, `scenario`, `area`, `component`, `metric`,
  `basis`, `year`
- **Reconciles:** Six publishers that agree on almost nothing onto one tidy
  frame: ERCOT's LTLF (an hourly per-weather-zone component workbook plus two
  published cases, ERCOT Adjusted and TSP Provided), the CEC's California
  Energy Demand forms (per planning area, with Form 1.1c's two data-centre
  scenarios), PJM's per-zone monthly workbook and Table B-9b, the NYISO Gold
  Book's zone tables (I-1a, I-11b, I-13a, I-14), the ISO-NE CELT (sheets
  1.5.1/1.5.2/1.7) and MISO's chart-only LTLF deck. `scenario` is the model's
  canonical low/mid/high axis and `published_case` keeps the publisher's own
  label, so the mapping is auditable; `basis` is in the key because ISO-NE
  publishes a Gross and a Net row for every series. Rule-13 line: a
  forward-looking published INPUT that regenerates from the next vintage and
  responds to changed conditions, never a measured outcome and never a fit
  target — the historical rows a publication prints beside its forecast are
  carried only to anchor a CAGR on the publisher's own base year and are
  labelled `scenario="actual"`. CONSUMED by `constants.DEMAND_GROWTH_RATES`,
  `DATACENTER_ADDITIONS_MW`, `DATACENTER_ZONE_SHARE` and
  `ELECTRIFICATION_LAYERS`, which are derived from these rows rather than
  hand-transcribed.

| column | dtype | unit | nullable | description |
|---|---|---|---|---|
| `iso` | `string` | `none` | no | Model ISO label the forecast belongs to (ERCOT, CAISO, PJM, MISO, NYISO, NEISO). This is the PUBLISHER's footprint, which is not always the model's footprint -- CAISO rows are CEC planning areas, three of which (PGE, SCE, SDGE) sum to approximately the CAISO balancing authority while the statewide row does not; see data/raw/load-forecast/README.md. |
| `edition` | `string` | `none` | no | The publication edition the row was read from, as a short human label -- "2025 LTLF", "2026 LTLF", "CED 2025-2045", "Gold Book 2026", "CELT 2026". Part of the key so several vintages coexist. |
| `vintage` | `int64` | `year` | no | Calendar year the edition was published; the information cutoff for an as-of-vintage (hindcast) read, the same gate confirmed_retirements applies to instrument_date. |
| `scenario` | `string` | `none` | no | Canonical scenario axis: low \| mid \| high, matching ScenarioConfig.demand_growth_path / datacenter_load_path / electrification_path; plus "actual" for the historical rows a publication prints beside its forecast. An ISO that publishes only one forecast has only "mid" rows -- never a fabricated band. |
| `published_case` | `string` | `none` | no | The publisher's OWN case label, verbatim, so the mapping onto `scenario` is auditable: "ERCOT Adjusted", "TSP Provided", "Baseline", "Lower Demand", "Higher Demand", "Current Trajectory", "Planning Forecast", "Local Reliability Scenario", "Forecast Change Drivers", ... |
| `area` | `string` | `none` | no | Area the value applies to, in the PUBLISHER's own vocabulary: the ISO label for footprint rows, else a weather zone (ERCOT), transmission zone (PJM), NYCA zone (NYISO "Zone A".."Zone K"), state (ISO-NE), CEC planning area or agency (CAISO), or MISO region. Crosswalking onto model zones is the consumer's job (config/iso_configs.py owns those maps); this datatype never guesses one. |
| `area_type` | `string` | `none` | no | Kind of area: iso \| source_zone \| state \| agency \| region \| planning_area. `source_zone` means a zone in the publisher's own zonal vocabulary, which is NOT necessarily a model zone. |
| `component` | `string` | `none` | no | Which part of the forecast: total (the whole footprint/area forecast) \| base_economic \| data_center \| large_load \| ev \| heat_pump \| building_electrification \| solar_pv. `data_center` is used only where the publisher itself isolates data centres (the CEC's Form 1.1c); a publisher that reports the wider large-load category (ERCOT contracts + officer letters, PJM Table B-9b, NYISO Table I-14) uses `large_load`, and the DC share of it is the consumer's declared assumption, never folded in here. `building_electrification` is the wider end-use category NYISO publishes (space + water heating, cooking, other), of which `heat_pump` is ISO-NE's narrower published cut. |
| `metric` | `string` | `none` | no | energy_gwh \| summer_peak_mw \| winter_peak_mw \| annual_peak_mw \| stock_count. Peak metrics carry the publisher's own peak definition (coincident vs non-coincident, 50/50 vs 1-in-2); the per-ISO raw README states which, because they are NOT interchangeable across publishers. |
| `year` | `int64` | `year` | no | Forecast year the value applies to. For a winter-peak row spanning a season boundary ("2030/31") this is the FIRST year of the pair, so a winter row and the summer row it is published beside share one key. |
| `value` | `float64` | `mixed` | no | The value, in the units named by `unit`. |
| `unit` | `string` | `none` | no | gwh \| mw \| count. Consistent with `metric` by construction and validated. |
| `basis` | `string` | `none` | no | net \| gross \| unspecified -- whether the value is net of behind-the-meter DER (the convention the model's demand arrays use) or gross. Part of the KEY, because a publisher that reports both (ISO-NE's CELT prints a Gross and a Net row for every energy and peak series) would otherwise collide on it. "unspecified" is the honest label for a publication that does not draw the distinction at all -- never a silent default onto "net". |
| `source_doc` | `string` | `none` | no | The source document, as a repo path where the file is held under data/raw/ (including a gitignored corpus payload, which is still the provenance record) or a URL where it is not. |
| `source_page` | `string` | `none` | no | Locator within source_doc -- sheet name, table number and page, or slide number. For a value read from a chart's vector coordinates this says so explicitly, and the raw README records the printed number the read was validated against. |
