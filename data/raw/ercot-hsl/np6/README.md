# ERCOT NP6 HSL upload drop zone

This directory holds ERCOT's own published wind/solar power-production
reports (NP4-732-CD / NP4-742-CD wind, NP4-737-CD / NP4-745-CD solar — the
"NP6" HSL family) that `scripts/data/build_ercot_hsl.py` scans and
aggregates. See that script's module docstring for the report-family/column
details.

**All three backcast years are now fully covered (24/24 fuel-months
each).** 2024/2025 landed 2026-07-06, 2023 landed 2026-07-22 — both via
manual download from ERCOT's Data Access Portal (the owner registered an
`apiexplorer.ercot.com` account and pulled the monthly archives by hand —
the credentialed API-key path documented as permanently closed in
`docs/handoffs/ercot-as-coopt-plan-2026-07.md` §WS-E was never re-attempted
programmatically; these are manual uploads, not a script re-opening that
gate).

- `2023/` — the by-geographical-region variants for all 12 months of both
  fuels: NP4-742 wind (regions Panhandle/Coastal/South/West/North) and
  NP4-745 solar (regions CenterWest/NorthWest/FarWest/FarEast/SouthEast/
  CenterEast). The GEO family carries the system-wide actual GEN and COP
  HSL columns (no telemetered actual-HSL column exists in this family), so
  the 2023 system-wide `hsl_mw` is COP-based. Superseded the UMass 2023
  fallback on landing.
- `2024/` — NP4-737 solar for all 12 months; NP4-732 wind for 10 months plus
  NP4-742 (wind GEO variant — identical system total columns plus the
  regional breakdown) for September.
- `2025/` — NP4-737 solar and NP4-732 wind for all 12 months.
- `unused-redundant/` — one solar-by-geography file (NP4-745, Nov 2024) not
  fed to the SYSTEM-wide builder: NP4-737 already covers that month, and
  blending two independent measurements of the same system total via the
  builder's groupby-mean would just add noise, not information. The ZONAL
  sidecar pass does read it (region rows only — the primary files carry no
  solar regions for that month), via `_ZONAL_EXTRA_DIRS` in
  `scripts/data/build_ercot_hsl.py`.

Per-region columns in any upload (the GEO families above, plus the
NP4-732 wind load-zone columns `LZ_SOUTH_HOUSTON`/`LZ_WEST`/`LZ_NORTH`
present 2024/2025) additionally feed the per-year **zonal sidecar**
`../ercot_<year>_hsl_zonal_hourly.parquet` — see `../README.md`.

**Archive shape:** each monthly ZIP is a ZIP of ZIPs — ERCOT posts a new
rolling-window report roughly hourly, so one outer monthly archive holds
~700 per-posting ZIPs, each containing exactly one CSV. `_read_csvs` in
`scripts/data/build_ercot_hsl.py` recurses to arbitrary depth to handle this (a
flat zip-of-CSVs still works identically).

**Cited known-bad ERCOT source window:** 2024-08-20 through 08-23 (96
hours) carries physically-impossible system-wide wind AND solar
actual+HSL values in every report vintage that covers those hours (e.g.
`ACTUAL_LZ_WEST` wind = 276,466 MW on 2024-08-23 HE1) — a defect in
ERCOT's own published file, confirmed present identically across every
later repost of the rolling window, not an artifact of this repo's
parsing. `_KNOWN_BAD_NP6_WINDOWS` in `scripts/data/build_ercot_hsl.py`
excludes exactly this cited window (nulled, then refilled from the measured
EIA-930 hourly delivered series with HSL = GEN — no fabricated curtailment
headroom; in the zonal sidecar, which has no per-region EIA-930 analogue,
the window simply stays NaN) — a narrow, documented exception that does not
weaken the general >24h incomplete-upload guard for any other window, year,
or future upload.

**Cross-check vs EIA-923** (`scripts/data/build_ercot_hsl.py`'s validation
printout): wind lands within ±0.3% all three years. Solar runs +13.7%
(2023) / +17.1% (2024) / +21.0% (2025) above the EIA-923 reference —
consistent in direction each year, so read as a real scope difference
between ERCOT's system-wide total and what EIA-923 captures (plausibly
ERCOT-only small/behind-the-meter solar resources not separately reported
to EIA-923), not a parsing defect; carried as-is per the "prefer measured
over estimate" rule rather than adjusted to fit. The authoritative
consistency check is EIA-930 (the loader's reconciliation reference and
the demand clock's system of record): NP6 solar matches EIA-930 ERCO
delivered to 0.03% in 2023 (31.88 vs 31.87 TWh) and exactly in 2024
(47.70 vs 47.68), so the NP6 series and the model's demand/renewables
plumbing agree.

To rebuild: `python scripts/data/build_ercot_hsl.py --year 2023 2024 2025`
(`--zonal-only` refreshes just the zonal sidecars).
