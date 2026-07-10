# NEISO (ISO-NE) measured hourly reserve requirements

Source: ISO Express > Operations Reports > **Hourly Reserve Requirements**
(report tree `ancillary-hourly-rr`):
<https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/ancillary-hourly-rr>

CSV export endpoint (requires the report page's `isox_token` session cookie):

    https://www.iso-ne.com/transform/csv/hourlyrequirements?start=YYYYMMDD&end=YYYYMMDD

Per hour (local hour-ending) and reserve location, the report publishes the
**as-enforced** Ten-Minute Spinning / Ten-Minute / TOTAL (30-minute) reserve
requirement MW — the ISO-NE analogue of the NYISO issue-#1344 Ask-B measured
requirement series, and the condition-varying requirement input for
`ScenarioConfig.neiso_dynamic_reserve_requirements` (the LP energy+reserve
co-optimization, `reserve_config._neiso_design`). Measured reserve **prices**
are the validation target and are never stored here (CLAUDE.md rule 13).

Locations (ISO-NE Web Services reserve-location vocabulary): `7000=ROS`
(system-wide requirement — the row the model consumes), `7001=SWCT`,
`7002=CT`, `7003=NEMABSTN` (local reserve zones; 30-minute total only).

## Layout

    requirements_<start:YYYYMMDD>_<end:YYYYMMDD>.csv   # 15-day windows, year-scoped

The window CSVs are **gitignored** (75 files for 2023-2025 — the
NYISO-archive push-limit precedent). Regenerate byte-equivalent files (modulo
the report-generated timestamp line) with the committed downloader:

    python scripts/fetch_neiso_reserve_requirements.py --years 2023 2024 2025

Then curate into `data/clean/reserve-requirements/NEISO/<year>/`:

    python scripts/curate_reserve_requirements.py --isos NEISO

Coverage policy: train years 2023-2025 only (CLAUDE.md rule 22 — no
out-of-training intake without explicit owner authorization).

DATA NEEDED: none for 2023-2025 (fully downloadable from the public report).
