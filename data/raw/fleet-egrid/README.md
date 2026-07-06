# fleet-egrid — raw

`egrid<year>_data.xlsx` (2022–2024) — EPA eGRID (Emissions & Generation
Resource Integrated Database) plant-sheet workbooks, one per release vintage.

**Source:** EPA eGRID, public domain — see `docs/data-licensing.md` §1.

**Regeneration: hand-assembled — no fetch script in this checkout.** No
`fetch_*.py` script targets this directory; the workbooks were downloaded
manually from EPA's eGRID download page
(<https://www.epa.gov/egrid/download-data>) for each release year.

**Regenerating the derived output:** `scripts/curate_egrid.py` reads each
vintage's `PLNT<YY>` sheet (skipping the long descriptive header row) and
writes one clean Parquet per vintage year, keeping the columns needed by
`market_sim.data.zone_assignment` (`ORISPL, LAT, LON, FIPSST, FIPSCNTY,
BACODE`) and `market_sim.data.egrid` (`ORISPL, PLFUELCT, PLNGENAN, PLCO2AN`).

**Consumers:** `scripts/curate_egrid.py`, `scripts/curate_fleet.py` (ISO
enrichment via `BACODE`).
