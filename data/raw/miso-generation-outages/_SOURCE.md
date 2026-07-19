# MISO generation-outage / capacity-availability record

**Source:** MISO Multiday Operating Margin Forecast Report, `OUTAGE` sheet
`https://docs.misoenergy.org/marketreports/YYYYMMDD_mom.xlsx` (public, no auth).

**Publisher:** Midcontinent Independent System Operator (MISO).

**What it is:** MISO's own bookkeeping of generation capacity offline, in MW,
by operating region (North / Central / South; `MISO` = the system total =
North+Central+South) and by cause type (Derated / Forced / Planned /
Unplanned). Each daily file carries a 7-day-ahead forecast block and a
30-day-look-back *estimated* (actual) block. Aggregate grain only -- no unit or
fuel-class identity (the public report does not disclose it).

**Files (committed, text — the in-repo source of truth):**
- `miso_outages_estimated_<year>.csv` -- the settled 30-day-look-back actuals
  (the backcast intake), one compact **wide** file per calendar year: an
  `interval_date` column + one `<Region>_<CauseType>` column per region×cause,
  integer MW. `outage_mw` is the most-settled estimate (from the latest file
  whose look-back window still covered the day). CSV rather than parquet because
  this repo's web-session push path is API-only (text) and cannot carry a binary
  parquet blob; the wide layout keeps each year ~34 KB.

**Files (local, efficient — gitignored; regenerate with this script):**
- `miso_generation_outages_estimated.parquet` -- the same actuals in long form
  with un-rounded MW + `publish_date` provenance.
- `miso_generation_outages_forecast.parquet` -- the 7-day-ahead forecast block
  (one row per publish_date, region, cause_type, interval_date); forward signal.

**Coverage built:** 2023-01-01 -> 2026-07-18 (187 source
files). MISO does not publish `_mom.xlsx` before 2023-01-01 (2018-2022 dates
404), so the record cannot extend earlier.

**Rebuild:** `python scripts/data/fetch_miso_outages.py --allow-out-of-train`

**MISO disclaimer (verbatim from the report):** "MISO MAKES NO REPRESENTATIONS
OR WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, WITH RESPECT TO THE ACCURACY OR
ADEQUACY OF THE INFORMATION CONTAINED HEREIN." The data is provided by MISO for
informational purposes; see MISO's website terms of use.
