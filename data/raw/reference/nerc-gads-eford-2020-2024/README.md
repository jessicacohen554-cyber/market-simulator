# NERC GADS Generating Unit Statistical Brochure — 2020-2024 (EFOR/EFORd by class)

The most recent 5-year-rolling GADS brochure NERC has published, supplementing
`nerc-gads-eford-2019-2023` and reaching the current edge of the model's 2018-2026 span
(the newest fleet-performance snapshot available; NERC has not yet published a rolling
window or annual brochure including 2025). Collected alongside
`nerc-gads-eford-annual-2018-2024` and `nerc-gads-eford-2018-2022` to close the
data-register gap "NERC GADS EFORd (2019-2023 only, no 2018/2024+)" (2026-07-08).

## Provenance

- **Publisher:** NERC (North American Electric Reliability Corporation), RAPA/GADS.
- **Document:** "Generating Unit Statistical Brochure 3 — 2020-2024 — Unit Reporting
  Events" (5-year rolling class-average statistics; NERC-wide, not region-specific).
- **URL:** https://www.nerc.com/globalassets/programs/rapa/gads/reports/generating-unit-statistical-brochure-3-2020-2024---unit-reporting-events.xlsx
- **Landing page:** https://www.nerc.com/programs/reliability-assessment--performance-analysis/generating-availability-data-system/gads-conventional/generating-unit-statistical-brochures
- **Retrieved:** 2026-07-08, via `curl` through the environment's configured proxy (`GET`
  returned HTTP 200, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`,
  44,295 bytes; Start/End=2020/2024 columns in the sheet confirm the vintage — this is
  the newest 5-year rolling brochure on NERC's site as of the retrieval date, checked
  against the full asset list on the landing page).
- **License/access:** Public NERC statistical brochure, no login/paywall — same basis as
  `nerc-gads-eford-2019-2023`.

## Extraction

`nerc_gads_eford_2020-2024.csv` uses the identical column reduction and suppression
handling as `nerc-gads-eford-2019-2023`: `Generator Catagory/Classification, Start, End,
# Units, Unit-Years, NMC, FOR, EFOR, EFORd`; rows NERC suppressed (n≤3 reporting units,
marked `*`) are dropped. All percentages are NERC's native units.

Re-run to reproduce:
```
curl -sSL -A "Mozilla/5.0" \
  "https://www.nerc.com/globalassets/programs/rapa/gads/reports/generating-unit-statistical-brochure-3-2020-2024---unit-reporting-events.xlsx" \
  -o brochure_2020_2024.xlsx
# then extract Sheet1 columns listed above with openpyxl/pandas.
```

## Scope

Same NERC-wide-only scope as `nerc-gads-eford-2019-2023` — see that README for the full
scope note and the rule-14 misalignment discussion in `constants.py`/`docs/parameter-citations.md`.

## Relevant rows for gas-fired availability

| Category | EFORd (%) | 1 − EFORd |
|---|---|---|
| GAS TURBINE, All Sizes | 9.85 | 0.9015 |
| COMBINED CYCLE, All Sizes | 4.91 | 0.9509 |
| FOSSIL Gas Primary, All Sizes | 14.26 | 0.8574 |
| FOSSIL Oil/Gas Primary, All Sizes | 14.30 | 0.8570 |

This is currently the best available "recent fleet" GADS benchmark (newest published
5-year pool). Compare to `2019-2023` (Gas Turbine 10.33 / Combined Cycle 4.71 / Gas
Primary 13.44) and `2018-2022` (10.50 / 4.43 / 12.60) — the pooled Gas Primary EFORd
rises each time the window rolls forward, tracking the annual series in
`nerc-gads-eford-annual-2018-2024`.
