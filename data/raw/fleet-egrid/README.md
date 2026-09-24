# fleet-egrid — raw

`egrid<year>_data*.xlsx` (2018–2024) — EPA eGRID (Emissions & Generation
Resource Integrated Database) plant-sheet workbooks, one per release vintage.

**Source:** EPA eGRID, public domain — see `docs/data-licensing.md` §1.

**Regeneration: no fetch script in this checkout — download by URL.** The
workbooks were downloaded from EPA's eGRID pages; the 2018–2021 set came from
the *historical* archive (<https://www.epa.gov/egrid/historical-egrid-data>),
2022–2024 from the current download page
(<https://www.epa.gov/egrid/download-data>). Exact URLs, matching the filenames
registered in `market_sim.data.egrid._EGRID_FILES` and
`scripts/data/curate_egrid.py::EGRID_FILES` — always the **latest revision** EPA
publishes for a vintage (`_v2` / `_rev2` where one exists), in **US units** (not
the `_metric` variants):

| vintage | file | URL |
|---|---|---|
| 2018 | `egrid2018_data_v2.xlsx` | `https://www.epa.gov/sites/default/files/2020-03/egrid2018_data_v2.xlsx` |
| 2019 | `egrid2019_data.xlsx` | `https://www.epa.gov/sites/default/files/2021-02/egrid2019_data.xlsx` |
| 2020 | `eGRID2020_Data_v2.xlsx` | `https://www.epa.gov/system/files/documents/2022-09/eGRID2020_Data_v2.xlsx` |
| 2021 | `eGRID2021_data.xlsx` | `https://www.epa.gov/system/files/documents/2023-01/eGRID2021_data.xlsx` |
| 2022 | `egrid2022_data.xlsx` | `https://www.epa.gov/system/files/documents/2024-01/egrid2022_data.xlsx` |
| 2023 | `egrid2023_data_rev2.xlsx` | `https://www.epa.gov/system/files/documents/2025-06/egrid2023_data_rev2.xlsx` |
| 2024 | `egrid2024_data.xlsx` | EPA eGRID download page (current release) |

2018–2021 were retrieved 2026-07-31 for the holdout-ladder data intake
(CLAUDE.md rule 22 `[R-HOLDOUT]`, owner-authorized); 2022 on 2026-07-04. Every
vintage carries the same `PLNT<YY>` sheet layout and the nine short-code columns
both consumers read, so no per-vintage parsing special case is needed.

**Regenerating the derived output:** `scripts/data/curate_egrid.py` reads each
vintage's `PLNT<YY>` sheet (skipping the long descriptive header row) and
writes one clean Parquet per vintage year, keeping the columns needed by
`market_sim.data.zone_assignment` (`ORISPL, LAT, LON, FIPSST, FIPSCNTY,
BACODE`) and `market_sim.data.egrid` (`ORISPL, PLFUELCT, PLNGENAN, PLCO2AN`).
`scripts/data/derive_fossil_co2_rates.py --years <years>` then assembles the
fleet-wide `fossil_co2_rates.parquet` fast-path artifact; its write is a
year-scoped merge, so a back-year run leaves the other years' rows untouched.

**Consumers:** `scripts/data/curate_egrid.py`, `scripts/data/curate_fleet.py`
(ISO enrichment via `BACODE`), `scripts/data/derive_fossil_co2_rates.py`.

**Heat-rate consumer (F1, 2026-09-24).** Every vintage is now read for plant
heat rates through ONE resolver, `market_sim.data.egrid.resolve_plant_heat_rates`
(year-matched vintage, nearest-vintage fallback, tie → earlier): the EIA-860
join (`scripts/data/process_eia860.py`), the boundary repair
(`data/fleet/eia860.py::_egrid_boundary_hr_repairs`, which reads the ACTIVE
table's own vintage) and the per-year CHP power-only derive. No solve-path
caller names a workbook or a `PLNT23` sheet any more.
