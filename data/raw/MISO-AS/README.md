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
