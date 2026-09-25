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
**The floor is a FORMAT CHANGEOVER, not a retention cutoff — MISO's pre-2023
record is fully public in a DIFFERENT REPORT FAMILY** (found 2026-09-13, miso-256):

- DA: `https://docs.misoenergy.org/marketreports/{YYYYMM}_da_pr_xls.zip`
- RT: `https://docs.misoenergy.org/marketreports/{YYYYMM}_rt_pr_xls.zip`

Monthly zips of per-day `.xls` pricing reports, each holding an `HE 01`-`HE 24`
block for MISO System plus the eight named hubs. They are the EXACT MIRROR of the
daily family above: **200 for 2015-2022, 404 from 2023-01** where the daily files
are 404 below 2023-01-01 and 200 above it. Between the two the public record is
unbroken, and no credential is needed for either.

Two conventions matter, both handled in `fetch_miso_hub_lmp.py`:

1. **The RT member is named for its PUBLISH date**, so it carries the PRIOR day's
   market (`20220615_rt_pr.xls` -> `Market Date: 06/14/2022`) and the last market
   day of each month ships in the NEXT month's zip. The fetcher keys on each
   sheet's own `Market Date:` header and probes the following month, so neither
   is a special case. Keying on the filename instead mis-dates every RT row by a
   day and drops 12 days a year.
2. **This family publishes LMP only** — no MCC/MLC decomposition. That is complete
   for every consumer here: `derive_miso_hub_lmp` selects `value == "LMP"`.
   An hour published as exactly `0.0` at all eight hubs at once is the report's
   missing-data marker and is staged BLANK, never as a zero price.

**Verified against the credentialed route, not assumed.** Over 2022-06, the one
month both families cover on disk, the monthly route reproduces the committed
API-sourced staging **exactly on DA (5,760/5,760 hub-hours, max diff $0.0000)**
and **5,721/5,760 (99.32%) on RT**, the 39 exceptions being the five all-hub-zero
slots described above.

Found via the source-URL table of Zenodo deposit `10.5281/zenodo.17676746`
(CC-BY-4.0), whose MISO series was pulled from this family in November 2020.
Three prior route audits (miso-252, miso-254, miso-256) swept the DAILY and
annual `*_HIST` naming spaces only and concluded the pre-2023 record was
unrecoverable. It was not — they searched two families and the data was in a third.

The MISO Data Exchange Pricing API (`https://apim.misoenergy.org/pricing/v1`,
subscription-key auth via `MISO_PRICING_API_KEY`) remains wired as the LAST
resort — verified byte-identical against the static CSV on an overlapping day
(2023-01-03 DA, ARKANSAS.HUB, all three LMP/MCC/MLC rows) — but **is no longer
needed for any year in 2015-2022**.

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

**2020 and 2021 ARE NOW STAGED** (2026-09-13, miso-256) from the monthly
`*_pr_xls.zip` family documented above, with **no credential**. Day coverage:
2020 DA 366/366, 2020 RT 366/366, 2021 RT 365/365, 2021 DA **364/365** — MISO's
own October-2021 DA archive holds 30 members covering Oct 1-31 *minus the 28th*,
a gap in the publisher's archive rather than in the fetch.

**2019 IS NOW STAGED** (2026-09-24, R-MISO — the owner's 2019-2025 backcast span,
`AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.3.3) from the same monthly
family, no credential: `fetch_miso_hub_lmp.py --years 2019` → DA 365/365, RT 365/365
(2,920 hub-day rows each, 53 chunks per market). Reduced by `derive_miso_hub_lmp.py
--years 2019` + `build_miso_lmp_reference.py --years 2019`; every other year's rows
preserved byte-for-byte (merge contract).

This supersedes the previous statement here that the two years "cannot be staged
without the key", and the claim in
`docs/FINDING-miso254-lmp-2020-2021-route-audit-2026-09-12.md` that
`MISO_PRICING_API_KEY` is "the single unblocker" — that finding's route audit is
sound for the two families it swept and its unblock chain (§4) is still the right
recipe; it simply did not reach this third family.

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
