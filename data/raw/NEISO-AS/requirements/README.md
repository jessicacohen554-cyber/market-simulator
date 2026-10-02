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

The window CSVs are **gitignored** (175 files for 2019-2025 — the
NYISO-archive push-limit precedent). Regenerate byte-equivalent files (modulo
the report-generated timestamp line) with the committed downloader:

    python scripts/data/fetch_neiso_reserve_requirements.py --years 2019 2020 2021 2022 2023 2024 2025

Then curate into `data/clean/reserve-requirements/NEISO/<year>/`:

    PYTHONPATH=. python scripts/data/curate_reserve_requirements.py --isos NEISO

Coverage (intaken 2026-10-02, closeout-NEISO wave 1; 175 windows 2019-2025,
regenerate with `--years 2019 2020 2021 2022 2023 2024 2025`, the new default):

| year | ROS hours published | curates? | note |
|---|---:|---|---|
| 2019 | 5,139 (from **2019-05-31**) | partial partition | the report **does not publish before 2019-05-31**: every Jan 1 - May 30 window returns a 256-byte header-only file. The loader refuses the partial year (< 8,760 h). |
| 2020 | 8,778 | **refused** | **2020-12-10 .. 12-17: 142 ROS hours publish `0, 0, 830`** (zero spin and ten-minute) — a publication outage, not a requirement; plus one duplicated row (2020-12-16 HE 11). The parser drops the duplicate and treats a zero ROS ten-minute value as a source hole; 149 holes > `MAX_GAP_HOURS` 72 → the year is refused (`[refuse]`), no partition. |
| 2021-2025 | full | yes | 2021-2025 partitions byte-identical before/after the 2026-10-02 parser change |

Spin fraction of the ten-minute requirement: 0.31 through mid-2022, 0.25 after
(measured, `docs/records/neiso/closeout-w1/reserve_requirement_recon.py`).

The ISO-NE **Morning Report** (`data/raw/neiso-operable-capacity/`) carries a daily
`total_operating_reserve_req_mw` and `largest_first_contingency_mw` for all of
2019, but it is a peak-hour planning quantity on a different basis (0.64-1.18x the
hourly ROS TOTAL, median 0.80-0.94 by year) and is **not** a fill for the missing
2019 months. How 2019 Jan-May and 2020 Dec 10-17 are represented when
`neiso_dynamic_reserve_requirements` is armed is an owner decision recorded in
`docs/records/neiso/closeout-w1/PRECOMMIT-closeout-neiso-scarcity-physics-2026-10-02.md`.

The former "train years 2023-2025 only" limit cited rule 22 `[R-HOLDOUT]`,
removed 2026-09-09.

DATA NEEDED: 2019-01-01..2019-05-30 and 2020-12-10..17 (ROS) are not published by
this report; no free alternative hourly source is known (ISO-NE Web Services needs an
account — not tried).
