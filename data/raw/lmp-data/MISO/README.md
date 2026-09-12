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

MISO Market Reports, one file per day, all nodes (no annual LMP archive exists — see the sweep below):

- DA ex-post: `https://docs.misoenergy.org/marketreports/YYYYMMDD_da_expost_lmp.csv`
- RT final:   `https://docs.misoenergy.org/marketreports/YYYYMMDD_rt_lmp_final.csv`

`docs.misoenergy.org` serves **no daily report before 2023-01-01**. The boundary
was first read as a rolling ~3.5-year window (2026-07-09: 2022-12-31 → 404,
2023-01-01 → 200) but it has not moved since: re-measured 2026-09-10 and again
**2026-09-12**, it is the same two dates, so it is a **FIXED floor**, not a
window that keeps eating years. (It is LMP-specific, not a site-wide cutoff: the
annual `*_HIST` archives of other report families do predate it -- `201912_dfal_
HIST_xls.zip` and `202012_dfal_HIST_xls.zip` are both live -- but a 144-URL sweep
of that family's naming space found **no LMP member for any pre-2023 year**. Full
route audit, including why the archive index and its Wayback mirror are both
unreachable from a session: `docs/FINDING-miso254-lmp-2020-2021-route-audit-2026-09-12.md`.)
For a year below the floor -- 2022, and 2018-2021 -- `fetch_miso_hub_lmp.py` falls
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

Staged years: 2022 (validation holdout, ~7-day plain-text chunks, INCOMPLETE -- see
below), 2023, 2024, 2025 (RT + DA, gzip), 2026 H1 (chunks).

**2020 and 2021 are NOT staged and cannot be staged without the key.** Both years sit
below the 2023-01-01 floor, so every route open to a session is closed; the two folded
validation rungs `2026-09-10-miso-251-tp2020` / `-tp2021` therefore score
C3a/C3b/C3c as **SKIPPED**. `MISO_PRICING_API_KEY` is the single unblocker and the
whole chain from key to re-scored rungs (no re-solve) is written out in
`docs/FINDING-miso254-lmp-2020-2021-route-audit-2026-09-12.md` §4. **Probe one day
before spending a year**: the Data Exchange portal documents no earliest date, so
whether the API itself retains 2020/2021 is unverified.

**Running the fetch for a below-floor year without the key now fails loudly** rather
than writing ~53 header-only chunk files per market that read as a staged year
(guard + tests added 2026-09-12: `tests/curation/test_fetch_miso_hub_lmp_staging.py`).
A chunk window with no staged day is skipped entirely, which is why 2022's short tail
shows as *absent* chunks (`p01..p49`) rather than empty ones.

## 2022 staging is INCOMPLETE (recorded 2026-07-31)

The 2022 chunk set stops short of the year:

    miso_hub_lmp_2022_da_p01..p49   -> 343/365 days   (missing 2022-12-10..12-31)
    miso_hub_lmp_2022_rt_p01..p45   -> 315/365 days   (missing 2022-11-12..12-31)

So the derived bench covers **94.0 % DA / 86.3 % RT** of 2022. January-October
is complete and real; November is DA-complete and RT-partial (36.5 %);
December is 29.0 % DA and effectively absent for RT (0.1 %, the single
year-boundary hour).

**It cannot be completed from `docs.misoenergy.org`** — 2022 sits entirely below
the 2023-01-01 floor (re-verified 2026-07-31: `20221215_da_expost_lmp.csv` ->
**404**, `20231215_...` -> 200; and again 2026-09-12). Finishing it needs the documented
fallback, the MISO Data Exchange Pricing API, which requires
`MISO_PRICING_API_KEY` (`fetch_miso_hub_lmp.py --years 2022 --markets rt da`).
The floor has not moved through 2026-09-12, so 2023 is not presently ageing off —
but it is a publisher's choice, not a guarantee, and MISO has said the market
reports will eventually be withdrawn in favour of the Data Exchange.

Because the downstream means are NaN-ignoring, the MISO block of
`actual_lmp.json` carries `da_cov` / `rt_cov` = `{annual, mon[12]}` so a
partially-covered month cannot be mistaken for a priced one (without it, 2022's
one December RT hour reads as a $22.82/MWh December RT price).

## H1-2026 staging (2026-07-31 rule-22 holdout intake)

`miso_hub_lmp_2026_{da,rt}_p01..p26` — 52 chunk files, **181/181 days each
market** (2026-01-01 .. 2026-06-30), 4,344 rows per market. Same source, same
chunk convention, same eight hubs as 2022; staged with
`fetch_miso_hub_lmp.py --years 2026 --through 2026-06-30`.

The `--through` bound is deliberate. `docs.misoenergy.org` publishes well past
June 30 (2026-07-30 was HTTP 200 at intake time), but the owner's rule-22
authorization names **H1-2026** — staging the later days would land data nobody
authorized. Extending to the rest of 2026 is a new authorization, not a re-run.

Downstream: `derive_miso_hub_lmp.py --years 2026` +
`build_miso_lmp_reference.py --years 2026` add the 2026 blocks to the system
and zonal parquets and to `actual_lmp.json` (DA $53.15 / RT $51.25,
`da_cov`/`rt_cov` annual **0.4958** — half-year coverage, Jul-Dec `null` in
`*_mon`). Both writers merge on year, so the 2022-2025 blocks stayed
byte-identical.
