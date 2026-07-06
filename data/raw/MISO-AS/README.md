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

**Licensing note:** MISO's own terms pages return HTTP 403 to automated
fetch and have not been manually verified — redistribution status is
**unclear**, not cleared. See `docs/data-licensing.md` §7 (MISO). Do not
assume redistribution permission pending a manual terms-page check.

**Consumers:** `scripts/report_miso_posture_gate.py` (honesty gate — level +
event-day direction, never the price-tail residual per rules 1/13),
`scripts/run_calibration_full.py`.
