# ERCOT NP6 HSL upload drop zone

This directory holds ERCOT's own published wind/solar power-production
reports (NP4-732-CD / NP4-742-CD wind, NP4-737-CD / NP4-745-CD solar — the
"NP6" HSL family) that `scripts/build_ercot_hsl.py` scans and aggregates. See
that script's module docstring for the report-family/column details.

**2024 and 2025 are now fully covered (24/24 fuel-months each).** Landed
2026-07-06 via manual download from ERCOT's Data Access Portal (the owner
registered an `apiexplorer.ercot.com` account and pulled the monthly
archives by hand — the credentialed API-key path documented as permanently
closed in `docs/handoffs/ercot-as-coopt-plan-2026-07.md` §WS-E was never
re-attempted programmatically; this is a manual upload, not a script
re-opening that gate).

- `2024/` — NP4-737 solar for all 12 months; NP4-732 wind for 10 months plus
  NP4-742 (wind-by-geography variant — carries the identical
  `ACTUAL_SYSTEM_WIDE`/`COP_HSL_SYSTEM_WIDE` system total columns, just with
  extra regional breakdown this builder discards) for September.
- `2025/` — NP4-737 solar and NP4-732 wind for all 12 months.
- `unused-redundant/` — one solar-by-geography file (NP4-745, Nov 2024) not
  fed to the builder: NP4-737 already covers that month, and blending two
  independent measurements of the same system total via the builder's
  groupby-mean would just add noise, not information. Kept for reference,
  not deleted.

**Archive shape:** each monthly ZIP is a ZIP of ZIPs — ERCOT posts a new
rolling-window report roughly hourly, so one outer monthly archive holds
~700 per-posting ZIPs, each containing exactly one CSV. `_read_csvs` in
`scripts/build_ercot_hsl.py` recurses to arbitrary depth to handle this (a
flat zip-of-CSVs still works identically).

**Cited known-bad ERCOT source window:** 2024-08-20 through 08-23 (96
hours) carries physically-impossible system-wide wind AND solar
actual+HSL values in every report vintage that covers those hours (e.g.
`ACTUAL_LZ_WEST` wind = 276,466 MW on 2024-08-23 HE1) — a defect in
ERCOT's own published file, confirmed present identically across every
later repost of the rolling window, not an artifact of this repo's
parsing. `_KNOWN_BAD_NP6_WINDOWS` in `scripts/build_ercot_hsl.py` excludes
exactly this cited window (nulled, then linearly interpolated from the
clean Aug 19 / Aug 24 endpoints) — a narrow, documented exception that
does not weaken the general >24h incomplete-upload guard for any other
window, year, or future upload.

**Cross-check vs EIA-923** (`scripts/build_ercot_hsl.py`'s validation
printout): wind lands within ±0.2% both years. Solar runs +17.1% (2024) /
+21.0% (2025) above the EIA-923 reference — consistent in direction each
year, so read as a real scope difference between ERCOT's system-wide total
and what EIA-923 captures (plausibly ERCOT-only small/behind-the-meter
solar resources not separately reported to EIA-923), not a parsing defect;
carried as-is per the "prefer measured over estimate" rule rather than
adjusted to fit.

To rebuild: `python scripts/build_ercot_hsl.py --year 2024 2025`.
