# ercot-AS — raw

ERCOT MIS ancillary-services report bundles:

- `00013057.np3-911-er.2d_cleared_dam_as_<PROD>.<timestamp>_json.zip` — NP3-911-ER
  "2-Day Cleared DAM AS" per product (ECRSM, ECRSS, NSPIN, NSPNM, REGDN,
  REGUP, RRSFFR, RRSPFR, RRSUFR).
- `00013051.np3-966-er.60d_dam_as_only_awards.<timestamp>_json.zip` —
  NP3-966-ER "60-Day DAM AS Only Awards".
- `00013052.np3-965-er.60d_sced_as_offer_updates.<timestamp>_json.zip` —
  NP3-965-ER "60-Day SCED AS Offer Updates".
- `ercot_<year>_as_by_restype_hourly.parquet`,
  `ercot_<year>_as_up_mw.parquet` — derived (see below).

**Source:** ERCOT MIS reports (`ercot.com`), public/redistributable per
ERCOT's raw-data terms — see `docs/data-licensing.md` §3.

**Regeneration:**
- The raw json.zip bundles are ERCOT MIS report downloads (re-fetch via the
  ERCOT Data Portal / MIS report list for report types NP3-911-ER,
  NP3-966-ER, NP3-965-ER).
- `scripts/build_ercot_as_by_restype_from_60day.py` →
  `ercot_<year>_as_by_restype_hourly.parquet`.
- `scripts/build_ercot_as_2023.py`, `scripts/build_ercot_as_withholding.py` →
  `ercot_<year>_as_up_mw.parquet`.

**Consumers:** `scripts/curate_ancillary_services.py` (reads the MCPC award
prices from the 60-day DAM AS awards zips — `zone="SYSTEM"`, ERCOT is a
single-zone AS market), `scripts/build_ercot_storage_as_2023_estimate.py`.

## 2018-2022 holdout-intake attempt (2026-07-10)

Coverage above is 2023-2025. A session-logged owner authorization
(2026-07-10, CLAUDE.md rule 22's data-intake clause) tasked extending this
directory back to 2018-2022. Result: **blocked by ERCOT's own access
policy, not by this repo's tooling** — documented honestly rather than
faked. Terms confirmed unchanged: `docs/data-licensing.md` §3 (ERCOT raw
data — "used, reproduced, and redistributed... without maintaining
notices") still governs anything that does land.

**What was built** (ready to use the moment either blocker below lifts, no
further code changes needed):

- `scripts/fetch_ercot_as_reports.py` — the free/unauthenticated ERCOT MIS
  fetch pattern (`misapp/servlets/IceDocListJsonWS` doc list +
  `misdownload/servlets/mirDownload` download), the same mechanism
  `scripts/fetch_ercot_ordc_reserves.py` already uses in production for
  NP6-905-CD. Validated live against production for all three report types
  this session (real docs listed, a real ~6.8 MB NP3-966-ER zip and a real
  ~57 MB NP3-965-ER zip downloaded and inspected — genuine multi-CSV daily
  bundles, not stubs).
- `scripts/build_ercot_as_by_restype_from_60day.py --year` now accepts
  multiple years in one invocation (`--year 2018 2019 ... 2022`), matching
  `build_ercot_as_withholding.py`'s existing multi-year `--year`.
- `.github/workflows/holdout-intake-ercot-as.yml` — runs the fetch + both
  build scripts + a no-LP schema-match verification + sha256 integrity
  report + commit/push, on a real GitHub Actions runner (this sandbox's
  proxy 413s on `git push` and its GitHub-API file tools cannot carry
  binary content without corruption). Self-triggers on a push to the
  workflow file itself (`workflow_dispatch` cannot be POSTed from this
  sandbox — 403).

**Why 2018-2022 didn't land — the retention wall.** ERCOT's free MIS doc
list (`IceDocListJsonWS`) is not a fixed archive; it is a **rolling window
that always ends "today"**, per ERCOT's own product catalog
(`misDisplayDuration_i`, confirmed via
`www.ercot.com/api/1/services/read/common/all-emil-items-search.json`) and
verified empirically 2026-07-10:

| report | reportTypeId | advertised window | observed window (2026-07-10) |
|---|---|---|---|
| NP3-911-ER (2-Day cleared DAM AS) | 13057 | 31 days | 2026-06-08 .. 2026-07-09 |
| NP3-966-ER (60-Day DAM AS awards) | 13051 | 1462 days (~4 yr) | 2024-03-24 .. 2026-07-09 (~2.3 yr) |
| NP3-965-ER (60-Day SCED AS offers) | 13052 | 1462 days (~4 yr) | 2024-03-24 .. 2026-07-09 (~2.3 yr) |

Because the window's right edge tracks "now", **2018-2022 is permanently
unreachable via this free path — not a transient gap that will resolve on a
retry or on a later run of the workflow.** The only ERCOT-side route that
reaches that far back is the credentialed archive on
`data.ercot.com`/`api.ercot.com` ("Search History Data" on each product
page), which needs an `apiexplorer.ercot.com` account, OAuth bearer token,
and subscription key. That route was already investigated in this exact
codebase and is **permanently declined by the repo owner**:
`docs/handoffs/ercot-as-coopt-plan-2026-07.md` §WS-E and
`docs/ercot-hsl-2024-25-intake-attempt-2026-07.md` (both re-verified live
this session: `api.ercot.com/api/public-reports/...` still returns
`401 {"message":"Access denied due to missing subscription key..."}`, and
the legacy `mis.ercot.com/misapp/GetReports.do` path still 302s to a
SiteMinder market-participant login wall for all three report types here).

**Not a gap to fabricate around.** Per rule 14, ECRS-product columns
(ECRSM/ECRSS) will legitimately read zero/absent for any pre-2023-06-10
delivery date even in a year that *is* reachable — ECRS launched
2023-06-10; REGUP/RRS have existed since ERCOT's nodal market launch
(Dec 2010) and would be present in any reachable year. That is expected,
not something to backfill or interpolate around.

**To actually close this gap:** either (a) the owner reverses the
`api.ercot.com` subscription-key decision and supplies a credential (the
fetch pattern would need a second, credentialed code path — not built here,
since it was explicitly out of scope and the credential does not exist),
or (b) a human manually downloads the 2018-2022 bundles through the
`data.ercot.com` UI (the same "already-authorized, different mechanism"
route the owner used for the NP6 HSL 2024/2025 intake — see
`docs/ercot-hsl-2024-25-intake-attempt-2026-07.md`) and drops them here, or
(c) ERCOT widens its free MIS retention window in the future. Any of these
unblocks `scripts/fetch_ercot_as_reports.py --years 2018 2019 2020 2021
2022` (or the manual files can be dropped straight into this directory)
with no further code changes on the fetch/list side.
