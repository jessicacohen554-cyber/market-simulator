# NERC GADS Generating Unit Statistical Brochure — annual, 2018-2024 (EFOR/EFORd by class)

Extends the `nerc-gads-eford-2019-2023` (Brochure 3, 5-year rolling pool) intake with
**per-year** class-average EFOR/EFORd, covering every calendar year NERC has published a
"Units Reporting Events" brochure for. Collected to close the `docs/data-register-2026-07.md`
gap flagged as "NERC GADS EFORd (2019-2023 only, no 2018/2024+)" and to give a year-keyed
benchmark across the model's full 2018-2026 span (data-collection task, 2026-07-08).

## Provenance

- **Publisher:** NERC (North American Electric Reliability Corporation), Reliability
  Assessment & Performance Analysis (RAPA) program, Generating Availability Data System
  (GADS).
- **Document series:** "<Year> Generating Unit Statistical Brochure -- Units Reporting
  Events" (NERC "Brochure 1" — single calendar-year class-average statistics;
  NERC-wide, not region-specific — see Scope below).
- **Landing page:** https://www.nerc.com/programs/reliability-assessment--performance-analysis/generating-availability-data-system/gads-conventional/generating-unit-statistical-brochures
- **Retrieved:** 2026-07-08, via `curl` through the environment's configured proxy (all
  nine `GET`s returned HTTP 200, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`).
- **License/access:** Public NERC statistical brochure, no login/paywall, same basis as
  the existing `nerc-gads-eford-2019-2023` intake.
- **Source URLs (one xlsx per year):**
  - 2018: https://www.nerc.com/globalassets/programs/rapa/gads/conventional/generating-unit-statistical-brochure-1-2018---units-reporting-events.xlsx
  - 2019: https://www.nerc.com/globalassets/programs/rapa/gads/reports/generating-unit-statistical-brochure-1-2019---units-reporting-events.xlsx
  - 2020: https://www.nerc.com/globalassets/programs/rapa/gads/conventional/generating-unit-statistical-brochure-1-2020---units-reporting-events.xlsx
  - 2021: https://www.nerc.com/globalassets/programs/rapa/gads/conventional/generating-unit-statistical-brochure-1-2021-units-reporting-events.xlsx
  - 2022: https://www.nerc.com/globalassets/programs/rapa/gads/conventional/generating-unit-statistical-brochure-1---2022---units-reporting-events.xlsx
  - 2023: https://www.nerc.com/globalassets/programs/rapa/gads/conventional/generating-unit-statistical-brochure-1-2023---units-reporting-events.xlsx
  - 2024: https://www.nerc.com/globalassets/programs/rapa/gads/reports/generating-unit-statistical-brochure-1--2024---units-reporting-events.xlsx

**2025 and H1-2026 do not exist yet.** Checked the landing page's rendered asset list
(2026-07-08) for any `*2025*`/`*2026*` brochure link — none found. NERC's annual
brochures lag by roughly 6+ months after year-end, so a 2025 vintage is not expected
until later in 2026.

## Extraction

`nerc_gads_eford_annual_2018-2024.csv` combines all seven years into one table, reduced
to the same columns as `nerc-gads-eford-2019-2023`: `Generator Catagory/Classification,
Start, End, # Units, Unit-Years, NMC, FOR, EFOR, EFORd` (`Start == End == <year>` for
every row here, since each source brochure is single-year). Suppressed rows (n≤3
reporting units) are dropped rather than kept as a literal placeholder string.

**Two source layouts, reconciled to one schema:**
- **2020-2024** use the same flat single-header-row layout as the `2019-2023` rolling
  brochure (`Generator Catagory/Classification` already combines category + size band;
  `NMC` = average nameplate MW is present).
- **2018-2019** use NERC's older multi-row-header layout (category and nameplate/size
  band are separate columns; a "MW Trb/Gen Nameplate" header sits over the size-band
  column instead of a numeric NMC average). For these two years `Generator
  Catagory/Classification` is reconstructed by concatenating the category + size-band
  cells (matching the later years' string format, e.g. `FOSSIL  All Fuel Types    All
  Sizes`), and `NMC` is left blank — the older layout does not publish a numeric average
  nameplate-MW column, only the size-band label already folded into the classification
  string. Suppressed cells in this layout are marked `****` rather than `*`; both markers
  are treated as suppressed and dropped.

All percentages are NERC's native units (percent, not fraction) — e.g. `EFORd=10.1`
means 10.1%.

Re-run to reproduce: fetch each URL above with `curl -sSL -A "Mozilla/5.0" <url> -o
<year>.xlsx`, then extract with `openpyxl` — new-layout years by header-name lookup on
row 0, 2018/2019 by fixed column offsets (category=col1, size band=col2, #Units=col4,
Unit-Years=col6, FOR=col24, EFOR=col26, EFORd=col28; data starts row 10).

## Scope — NERC does not publish a per-ISO/regional breakdown

Same NERC-wide-only scope as `nerc-gads-eford-2019-2023`: no NERC Region/RTO/ISO/utility
cut exists in this brochure series, only generator category/technology by nameplate-size
band. See that intake's README and `docs/parameter-citations.md` for how this shapes
the model's use of GADS-sourced availability figures (rule-14 misalignment: one
NERC-wide figure applies across all ISOs).

## Year-over-year trend for gas-fired availability (EFORd, %, All Sizes)

| Category | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|
| GAS TURBINE | 11.23 | 11.66 | 10.05 | 8.42 | 11.21 | 10.45 | 9.03 |
| COMBINED CYCLE | 3.64 | 3.69 | 4.26 | 5.07 | 5.71 | 5.02 | 4.51 |
| FOSSIL Gas Primary | 11.47 | 13.84 | 12.45 | 12.81 | 13.93 | 15.63 | 16.97 |
| FOSSIL Oil/Gas Primary | 11.39 | 13.93 | 13.19 | 13.04 | 13.95 | 15.35 | 16.37 |

Combined-cycle EFORd trends up modestly since 2020 (fleet aging / higher cycling
duty); combustion-turbine EFORd is noisier year-to-year (smaller reporting population).
The pooled `FOSSIL Gas Primary`/`Oil/Gas Primary` rows show a clearer multi-year rise
2020→2024, consistent with an aging steam-turbine-heavy gas fleet. This per-year table
is a benchmark for any future trailing-window forward-availability estimator (the same
shape as `CO2_RATE_TRAILING_WINDOW_YEARS` in `constants.py`); no such estimator exists
yet — see `docs/calibration-log.md`'s 2026-07-05 B-XISO-1 entry, which found the
existing `GAS_AVAILABILITY_FACTOR` scalar is dead code (0% materiality), and left open
issue #1349 on whether/how to wire GADS-sourced availability into the LP.
