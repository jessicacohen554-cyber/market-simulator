# MISO-AS — raw

MISO ancillary-services market report data — the measured ASM series behind
the MISO scarcity-posture honesty gate
(`docs/multi-iso/miso-scarcity-posture-design-2026-07.md` §A/§B):

- `asm_damcp_zonal_<year>.parquet` / `asm_rtmcp_zonal_<year>.parquet`
  (2023–2025) — day-ahead ex-ante / real-time final zonal ancillary-service
  market clearing prices (MCP). Columns: `date, zone, product, he01..he24`
  (Hour-Ending 1–24, Eastern Standard Time year-round — MISO market reports
  never observe DST). Deduplicated to one row per (zone, product); the
  source files repeat the zone price for every pnode in the zone plus a
  market-wide block, both dropped.
- `asm_rt_cleared_mw_<year>.parquet` (2023–2025) — hourly Region × product
  cleared reserve MW, aggregated from MISO's masked-unit real-time
  cleared-offers report: `cleared_mw` = sum over units of mean(MW1..MW12)
  per 5-minute interval. Columns: `date, hour_end_est, region, product,
  cleared_mw`. Region is North/Central/South; product is reg/spin/supp/str.

**Source:** MISO Market Reports (`docs.misoenergy.org/marketreports/`),
one-file-per-day DA/RT MCP CSVs and RT cleared-offers zips — MISO publishes
no annual archives, so this data is staged as yearly rollups.

**Regeneration:** `scripts/fetch_miso_asm.py --years 2023 2024 2025`
(`--datasets mcp` to fetch only the MCP files). Fetches day-by-day from the
URLs above with retries; a 404 means the report was never published for
that day and is skipped, not treated as an error.

**2022 is confirmed ungettable — do not re-attempt.** Investigated
2026-07-09: all three report endpoints 404 for every day of 2022
(1,095/1,095 requests), a genuine `BlobNotFound` from MISO's Azure blob
storage, while the identical URL pattern is HTTP 200 from 2023-01-01
onward. This is a rolling retention purge, not a naming change — a
2021-08-14 `asm_rt_co.zip` that Wayback Machine had crawled as HTTP 200 in
March 2024 is now also 404 live, confirming MISO ages out old daily
report files. Ruled out: 5 legacy report-name variants, a consolidated
annual `_HIST` rollup (the pattern MISO uses elsewhere), and Wayback
Machine archive recovery (zero captures for any of the three report types
in 2022). MISO's Data Exchange API doesn't help either — it needs
registration we don't have, and per MISO's own FAQ it draws on the same
retention-limited live store; historical data beyond that requires a
manual Help Center/ITOC request, not an automatable fetch. Full
investigation: `docs/data-register-2026-07.md` "Ancillary services /
reserves" section.

**Licensing note:** MISO's own terms pages return HTTP 403 to automated
fetch and have not been manually verified — redistribution status is
**unclear**, not cleared. See `docs/data-licensing.md` §7 (MISO). Do not
assume redistribution permission pending a manual terms-page check.

**Consumers:** `scripts/report_miso_posture_gate.py` (honesty gate — level +
event-day direction, never the price-tail residual per rules 1/13),
`scripts/run_calibration_full.py`.

## 2018-2021 + H1-2026 holdout intake (2026-07-10 session)

Data-intake-only extension under CLAUDE.md rule 22 (session-logged owner
authorization, 2026-07-10) — no solve/score, no LP. Scope: MISO AS market
data only, **2022 excluded** (settled, see above; not re-attempted).

**2018-2021 also appear ungettable — same failure mode as 2022, not yet
exhaustively confirmed.** This session spot-checked (small samples, no bulk
download) the identical URL pattern used by `fetch_miso_asm.py` against both
year boundaries and mid-year dates for 2018-2022 (`20180101`, `20181231`,
`20190101`, `20191231`, `20200101`, `20201231`, `20210101`, `20211231`,
`20220101`, `20221231`, plus `20190615`) across all three report endpoints
(`asm_exante_damcp`, `asm_rtmcp_final`, `asm_rt_co`), and additionally tried
10 legacy report-name variants (`asm_damcp`, `asm_rtmcp`, `asm_da_mcp`,
`da_expost_mcp`, `rt_co`, `asm_co`, etc.) for 2019-06-15. **Every single
request 404'd** — the same Azure `BlobNotFound`/`ResourceNotFound` signature
as the confirmed-2022 purge — while `20230101` and `20250101` control checks
on the same pattern both return HTTP 200. MISO's Market Report Archives page
and Data Exchange API doc (`cdn.misoenergy.org/.../MISO Data Exchange
Information...pdf`) were also checked from this sandbox; both dead-end the
same way already documented for 2022 (403 on the archives page; the Data
Exchange API needs registration this session doesn't have and is itself
retention-limited per its own FAQ). Wayback Machine (`web.archive.org`) is
blocked by this sandbox's egress policy, so it was not re-checked here — the
2022 investigation already found zero Wayback captures for any of the three
report types in 2022, and there is no reason to expect 2018-2021 fared
better on a purge that is evidently rolling forward from an even earlier
date, not 2022-specific.

This is a **spot-check**, not the exhaustive 1,095/1,095-request count the
2022 finding above has — the holdout-intake workflow
(`.github/workflows/holdout-intake-miso-as.yml`) still attempts the full
daily fetch for 2018-2021 on a GitHub Actions runner (different network path)
as the authoritative confirmation, since the fetch script treats a 404 as
skip-not-error and the cost is a few minutes of CI time either way.
`scripts/fetch_miso_asm.py` was hardened (2026-07-10) so that a year with zero
published days writes **no file** rather than a schema-broken zero-column
parquet — so if the CI run confirms zero rows for 2018-2021, no misleading
artifact lands, and these years should be added to the confirmed-ungettable
list above in a follow-up commit rather than re-investigated.

**H1-2026 coverage, format-validated, no drift found.** Sampled
`2026-01-15`, `2026-06-30`, and the boundary around today (session date
2026-07-10) for both MCP files and the RT cleared-offers zip; all three
report formats (columns, delimiters, `HE 1..HE 24` header layout, the
`RegMW1..12`/`SpinMW1..12`/`SuppMW1..12`/`STRMW1..12` cleared-offer columns)
match the 2023-2025 files byte-for-byte in structure — `fetch_miso_asm.py`
needs no format-branch change, just the arbitrary `--years` it already
accepts. Realistic cutoffs observed this session (both will move forward as
more of 2026 posts):

- **MCP (DA ex-ante / RT final zonal prices):** HTTP 200 through
  `2026-07-09` (the day before this session's date) — posts almost live.
- **RT cleared-offers MW (`asm_rt_co`):** HTTP 200 through `2026-04-10`,
  HTTP 404 from `2026-04-11` on — a ~3-month publish lag as of this session,
  in the same ballpark as the script's documented "~4-month lag" (lag varies
  week to week; this is a point-in-time observation, not a hard boundary).
  `asm_rt_cleared_mw_2026.parquet` will therefore cover materially fewer
  months than the two MCP files for the same year — expected, not a bug.
