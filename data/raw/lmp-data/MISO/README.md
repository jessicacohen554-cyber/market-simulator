# MISO named-trading-hub RT/DA hourly LMPs (scope decision D6)

Compact stagings of MISO's daily all-node market reports, filtered to the
**eight named trading hubs** (ARKANSAS.HUB, ILLINOIS.HUB, INDIANA.HUB,
LOUISIANA.HUB, MICHIGAN.HUB, MINN.HUB, MS.HUB, TEXAS.HUB) — the measured
per-hub validation series behind the MISO zonal-spread gate
(docs/multi-iso/miso-zonal-refinement-scope.md §7 gate 2).

One gzip CSV per (year, market), written by `scripts/fetch_miso_hub_lmp.py`:

    miso_hub_lmp_<year>_<da|rt>.csv.gz
    columns: date,node,type,value,he01..he24

Rows are **verbatim** from the source files (LMP, MCC and MLC rows per hub;
hourly values untouched); the only additions are the filter to the eight hubs
and the leading `date` column (the source carries the date in a file header
line, not per row) — the same source-subset pattern as the ERCOT
`DAMLZHBSPP_*.zip` holdings one directory up.

## Authoritative source

MISO Market Reports, one file per day, all nodes (no annual archives exist):

- DA ex-post: `https://docs.misoenergy.org/marketreports/YYYYMMDD_da_expost_lmp.csv`
- RT final:   `https://docs.misoenergy.org/marketreports/YYYYMMDD_rt_lmp_final.csv`

All hours are **hour-ending 1–24, Eastern Standard Time year-round** (each
file's header states "All Hours-Ending are Eastern Standard Time (EST)" — no
DST duplication or gap).

## Downstream

`scripts/derive_miso_hub_lmp.py` reduces these stagings to the zone-resolved
validation parquet
`data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`
(hub → zone: MINN→MISO-West, ILLINOIS→MISO-Illinois, INDIANA→MISO-Indiana,
MICHIGAN→MISO-East, ARKANSAS/LOUISIANA/TEXAS/MS→MISO-South; **MISO-Plains has
no hub** — consumers use the documented MINN+ILLINOIS hub-mean proxy).
`scripts/build_miso_lmp_reference.py` then adds the per-zone `zones` sub-dict
to the MISO block of `actual_lmp.json`, and
`scripts/report_miso_zonal_gates.py` scores gate 2 (zonal spread sign and
magnitude) against these actuals.

Staged years: 2023, 2024, 2025 (RT + DA).
