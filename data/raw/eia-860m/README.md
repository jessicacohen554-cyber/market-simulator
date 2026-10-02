# eia-860m — raw (EIA-860M monthly generator inventory)

**What it is.** Form EIA-860M, "Monthly Update to the Annual Electric Generator
Report": the inventory of operating, planned, retired and canceled generators
as of a given month. Landed 2026-10-02 (closeout plan W0, audit §F row 2) as a
**forecast-only layer**: a backcast year reads its own annual Final vintage under
`data/raw/eia-860/vintage_<Y>/` and never this store (audit spec E.2). EIA's own
caveat applies — 860M capacities "are best estimates … not capacity commitments"
and "will be corrected without explanation in subsequent month's inventory" — so
it is never a capacity basis of record, only the in-year COD / retirement
supplement for months after the latest annual Final.

**Files.** One parquet per workbook sheet (Puerto Rico sheets omitted; the Google /
Bing map link columns and the footer note rows dropped; every other column verbatim):

| file | sheet | rows |
|---|---|---|
| `august_generator2026.operating.parquet` | Operating | 28,377 |
| `august_generator2026.planned.parquet` | Planned | 2,311 |
| `august_generator2026.retired.parquet` | Retired | 7,324 |
| `august_generator2026.canceled.parquet` | Canceled or Postponed | 1,741 |

**Source.** `https://www.eia.gov/electricity/data/eia860m/xls/august_generator2026.xlsx`
(inventory as of August 2026, released 2026-09-24; next release 2026-10-23). Public
domain. The workbook itself is not committed (re-fetchable from EIA's permanent
monthly archive); its sha256 is the first line of `SHA256SUMS.txt`.

**Regeneration.** Download the workbook, then (pandas, header row 3 of each sheet):
drop rows whose `Plant ID` is non-numeric, drop the two map-link columns, write each
sheet to parquet with the naming above; record the sha256 of the workbook and of each
parquet in `SHA256SUMS.txt`. A later month lands as its own `<month>_generator<year>.*`
set beside this one; nothing is overwritten.

**Consumers.** None yet. The intended consumer is the forecast base-year fleet
(audit E.2: "860M is layered on the latest Final in the forecast base year, tagged
`monthly_update`, never in a backcast").
