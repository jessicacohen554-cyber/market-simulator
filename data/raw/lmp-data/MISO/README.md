# MISO named-trading-hub RT/DA hourly LMPs (scope decision D6)

Compact stagings of MISO's daily all-node market reports, filtered to the
**eight named trading hubs** (ARKANSAS.HUB, ILLINOIS.HUB, INDIANA.HUB,
LOUISIANA.HUB, MICHIGAN.HUB, MINN.HUB, MS.HUB, TEXAS.HUB) -- the measured
per-hub validation series behind the MISO zonal-spread gate
(docs/multi-iso/miso-zonal-refinement-scope.md §7 gate 2).

Gzip CSV(s) for 2023-2025, plain-text CSV chunks for 2022+, both written by
`scripts/fetch_miso_hub_lmp.py`:

    miso_hub_lmp_<year>_<da|rt>.csv.gz              (2023-2025, one file/year, gzip)
    miso_hub_lmp_<year>_<da|rt>_p<NN>.csv            (2022+, ~7-day chunks, plain text)
    columns: date,node,type,value,he01..he24

2023-2025 predate the chunk split and ship as one gzip file per (year,
market). 2022 onward ships as ~7-day plain-text chunks instead (NN = 01,
02, ... -- 53 chunks/year, last one short): this repo's git-push rule
requires committing over the GitHub API (`push_files`), whose `content`
field is committed **verbatim** as the file's bytes with no decode step, so
gzip binary can't survive it -- and base64-encoding the gzip bytes first
doesn't help either, since the base64 *text* just gets committed as the
file's literal content (discovered 2026-07-09, corrupting the first 13
chunks pushed that way). Plain, uncompressed CSV is valid UTF-8 and survives
`content` unmodified, so 2022+ ships uncompressed; ~7-day windows
(~25-29KB/chunk, ~169 lines) keep each chunk comfortably under both the
Read-tool truncation cap and push_files' practical size limit (a ~10-day/
~40KB first pass still overran the Read cap as plain text -- denser in
tokens than the old base64-gzip encoding was). `scripts/derive_miso_hub_lmp.py`
reads either layout (`_staged_paths`: prefers the legacy gzip yearly file if
present, else globs the plain-text `_p??` chunks).

Rows are **verbatim** from the source (LMP, MCC and MLC rows per hub; hourly
values untouched); the only additions are the filter to the eight hubs and
the leading `date` column (the source carries the date in a file header
line, not per row) -- the same source-subset pattern as the ERCOT
`DAMLZHBSPP_*.zip` holdings one directory up.

## Authoritative source

MISO Market Reports, one file per day, all nodes (no annual archives exist):

- DA ex-post: `https://docs.misoenergy.org/marketreports/YYYYMMDD_da_expost_lmp.csv`
- RT final:   `https://docs.misoenergy.org/marketreports/YYYYMMDD_rt_lmp_final.csv`

`docs.misoenergy.org` only retains a rolling ~3.5-year window of these daily
files (verified 2026-07-09: 2022-12-31 → 404, 2023-01-01 → 200, for both
reports). For a year that has aged off -- 2022 -- `fetch_miso_hub_lmp.py` falls
back to the MISO Data Exchange Pricing API
(`https://apim.misoenergy.org/pricing/v1`, subscription-key auth via
`MISO_PRICING_API_KEY`), verified byte-identical against the static CSV on an
overlapping day (2023-01-03 DA, ARKANSAS.HUB, all three LMP/MCC/MLC rows).

All hours are **hour-ending 1–24, Eastern Standard Time year-round** (each
file's header states "All Hours-Ending are Eastern Standard Time (EST)" -- no
DST duplication or gap).

## Downstream

`scripts/derive_miso_hub_lmp.py` reduces these stagings to the zone-resolved
validation parquet
`data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`
(hub → zone: MINN→MISO-West, ILLINOIS→MISO-Illinois, INDIANA→MISO-Indiana,
MICHIGAN→MISO-East, ARKANSAS/LOUISIANA/TEXAS/MS→MISO-South; **MISO-Plains has
no hub** -- consumers use the documented MINN+ILLINOIS hub-mean proxy).
`scripts/build_miso_lmp_reference.py` then adds the per-zone `zones` sub-dict
to the MISO block of `actual_lmp.json`, and
`scripts/report_miso_zonal_gates.py` scores gate 2 (zonal spread sign and
magnitude) against these actuals.

Staged years: 2022 (validation holdout, ~7-day plain-text chunks), 2023, 2024, 2025 (RT + DA, gzip).
