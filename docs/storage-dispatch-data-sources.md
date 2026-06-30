# Public Storage Dispatch Data Sources by ISO

**Date:** 2026-06-30
**Purpose:** Inventory of publicly available data that can fill storage dispatch
calibration gaps (C5b throughput, C5c dispatch shape).

---

## Cross-ISO: EIA-930 (Primary Source)

EIA Form 930 reports hourly net generation by energy source for each balancing
authority. In 2024Q3 EIA added granular storage breakout columns (`NG: BAT` for
battery, `NG: PS` for pumped storage), replacing the legacy fold-into-`OTH`.

**Current extract coverage** (`data/raw/eia-930-hourly/`):

| BA code | ISO   | NG: BAT | NG: PS | Notes |
|---------|-------|---------|--------|-------|
| ERCO    | ERCOT | 2025+ (99%), 2024 partial (19%) | — | No PS column; ERCOT has no utility-scale PS |
| CISO    | CAISO | **Not in extract** | **Not in extract** | Extract predates 2024Q3 split; re-extract needed |
| PJM     | PJM   | **Not in extract** | **Not in extract** | Same — re-extract from EIA API will pick up BAT/PS |
| MISO    | MISO  | 2025 (96%), ≤2024 null | — | No PS column in extract |
| ISNE    | NEISO | 2025 (100%), 2024 partial (15%) | 2025 (100%), 2024 partial (15%) | Both techs present |
| NYIS    | NYISO | **Not in extract** | **Not in extract** | Re-extract needed |

**Action:** Re-extract CISO, PJM, and NYIS from EIA-930 API to pick up the
2024Q3+ BAT/PS columns. The existing loader (`eia_loader.load_eia_hourly_benchmark`)
already reads `NG: BAT` and `NG: PS` when present — once the parquet files carry
those columns, C5b/C5c automatically un-SKIP.

**API access:** https://www.eia.gov/electricity/gridmonitor/about
**PUDL mirror:** https://docs.catalyst.coop/pudl/en/stable/data_sources/eia930.html

---

## Per-ISO Supplementary Sources

### ERCOT

| Source | Resolution | Content | URL |
|--------|-----------|---------|-----|
| **Fuel Mix Report** | 15-min settlement intervals | Actual generation by fuel type incl. battery storage. Annual ZIP (2007–2025). | https://www.ercot.com/gridinfo/generation |
| **Energy Storage Resources Dashboard** | 5-min real-time | Total charging, discharging, and net output (telemetered). | https://www.ercot.com/gridmktinfo/dashboards/energystorageresources |
| **60-Day SCED Disclosure** | Per-unit, 5-min | Individual resource SCED dispatch points (requires portal login). | Portal via https://www.ercot.com/gridmktinfo |

**Best for calibration:** Fuel Mix Report — downloadable CSV, 15-min, full
year. Finer than EIA-930 (hourly) and already ISO-aggregate. Can validate both
C5b throughput and C5c monthly shape.

### CAISO

| Source | Resolution | Content | URL |
|--------|-----------|---------|-----|
| **Daily Energy Storage Report** | Hourly | Bid-in capacity, awards, SOC, AS procurement for storage + hybrids. CSV data files posted quarterly (Jan 2023–present). | https://www.caiso.com/library/daily-energy-storage-reports |
| **2024 data CSV download** | Hourly | Raw data for 2023-01 through 2024-09. | https://www.caiso.com/library/2024-data-for-daily-energy-storage-reports |
| **Today's Outlook** | 5-min | Real-time supply by source incl. batteries. | https://www.caiso.com/todays-outlook |
| **Annual Battery Storage Report** | Annual summary | Capacity, cycling, curtailment, market metrics. | https://www.caiso.com/documents/2024-special-report-on-battery-storage-may-29-2025.pdf |

**Best for calibration:** Daily Energy Storage Report CSV — hourly charge/
discharge/SOC by resource type. The richest public storage dataset of any ISO.
Can fill the gap until the EIA-930 re-extract provides CISO BAT/PS columns.

### PJM

| Source | Resolution | Content | URL |
|--------|-----------|---------|-----|
| **Data Miner 2 — Generation by Fuel Type** | Hourly (posted hourly, 15 min lag) | Fuel mix of generation resources incl. “Storage” category. API and manual query. | https://dataminer2.pjm.com/feed/gen_by_fuel |
| **Data Miner 2 API** | Programmatic | REST API, free PJM account required, 6 req/min for non-members. | https://www.pjm.com/markets-and-operations/etools/data-miner-2 |
| **State of the Market Report** | Annual/quarterly | Storage utilization and market metrics. | https://www.monitoringanalytics.com/ |

**Best for calibration:** Data Miner 2 `gen_by_fuel` feed — hourly, includes
battery storage as a fuel type. Free API with PJM account. Fills the gap until
the EIA-930 re-extract provides PJM BAT/PS columns.

### MISO

| Source | Resolution | Content | URL |
|--------|-----------|---------|-----|
| **RT Data API** | Real-time (JSON) | Fuel mix incl. storage. Transitioned from static reports to API-only Sep 2024. | https://www.misoenergy.org/markets-and-operations/rtdataapis/ |
| **Market Reports archive** | Varies | Legacy fuel mix reports (pre-Sep 2024). | https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/ |
| **EIA Grid Monitor** | Hourly | MISO BA generation by source (EIA-930 frontend). | https://www.eia.gov/electricity/gridmonitor/dashboard/electric_overview/balancing_authority/MISO |
| **State of the Market Report 2024** | Annual | Capacity, dispatch, storage participation. | https://cdn.misoenergy.org/ |

**Best for calibration:** EIA-930 extract already has `NG: BAT` for 2025
(96% coverage). For 2024 and earlier, MISO's RT Data API is the fallback, but
the API format is JSON-only and requires scraping.

### NYISO

| Source | Resolution | Content | URL |
|--------|-----------|---------|-----|
| **P-63 Real-Time Fuel Mix** | 5-min (CSV) | Fuel mix by fuel type. Energy storage is in “Other Renewables” bucket (solar + storage + methane + refuse + wood). | http://mis.nyiso.com/public/P-63list.htm |
| **Real-Time Dashboard** | Real-time | Live fuel mix graphics incl. storage. | https://www.nyiso.com/real-time-dashboard |
| **Gold Book** | Annual | Load & capacity data incl. storage capacity by zone. | https://www.nyiso.com/load-capacity-data-report-gold-book- |
| **GridStatus (third party)** | 5-min | Structured NYISO fuel mix data. | https://www.gridstatus.io/datasets/nyiso_fuel_mix |

**Best for calibration:** P-63 CSV files are the primary source, but battery
storage is lumped into “Other Renewables” — not separately breakable. EIA-930
re-extract with BAT/PS columns is the better path. GridStatus may parse
storage separately.

### ISO-NE (NEISO)

| Source | Resolution | Content | URL |
|--------|-----------|---------|-----|
| **Net Energy and Peak Load by Source** | Annual/monthly | Generation by source incl. storage (2024 published Feb 2025, 2025 published Feb 2026). | https://isonewswire.com/2026/02/12/iso-ne-publishes-amounts-sources-of-electric-energy-used-to-meet-demand-in-2025/ |
| **Key Grid and Market Stats** | Summary | Annual stats. | https://www.iso-ne.com/about/key-stats |
| **2024 Assessment of ISO-NE Electricity Markets** | Annual | Market performance incl. ESR utilization. | https://www.iso-ne.com/static-assets/documents/100025/iso-ne-2024-emm-report-final.pdf |

**Best for calibration:** EIA-930 extract already has both `NG: BAT` and
`NG: PS` for 2025 (100% coverage). For 2024, only partial coverage (15%,
~Nov–Dec). ISO-NE's annual publications supplement but are not hourly.

---

## Recommended Actions

1. **Re-extract EIA-930** for CISO, PJM, and NYIS BAs from the EIA API (the
   2024Q3+ data has BAT/PS columns). The existing `eia_loader` code reads them
   automatically — this is a data refresh, not a code change.

2. **Download CAISO Daily Energy Storage Report CSVs** (2023–present) as a
   backup/validation source richer than EIA-930 (has SOC, AS, bid-in MW).

3. **Fetch PJM `gen_by_fuel` via Data Miner 2 API** for 2023–2025 hourly
   storage generation as backup until the EIA-930 re-extract.

4. **For NYISO:** wait for EIA-930 re-extract (P-63 lumps storage into
   “Other Renewables” and can’t be decomposed).

5. **ERCOT and NEISO** are already covered by the current EIA-930 extract
   for 2025; ERCOT Fuel Mix Report CSV provides 15-min data for deeper validation.
