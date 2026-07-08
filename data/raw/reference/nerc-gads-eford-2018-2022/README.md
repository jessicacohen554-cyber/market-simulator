# NERC GADS Generating Unit Statistical Brochure — 2018-2022 (EFOR/EFORd by class)

A second 5-year-rolling GADS brochure window, supplementing `nerc-gads-eford-2019-2023`
and extending pooled coverage one year earlier (to 2018) — the earliest edge of the
model's 2018-2026 span. Collected alongside `nerc-gads-eford-annual-2018-2024` and
`nerc-gads-eford-2020-2024` to close the data-register gap "NERC GADS EFORd (2019-2023
only, no 2018/2024+)" (2026-07-08).

## Provenance

- **Publisher:** NERC (North American Electric Reliability Corporation), RAPA/GADS.
- **Document:** "Generating Unit Statistical Brochure 3 — 2018-2022 — Units Reporting
  Events" (5-year rolling class-average statistics; NERC-wide, not region-specific).
- **URL:** https://www.nerc.com/globalassets/programs/rapa/gads/reports/generating-unit-statistical-brochure-3---2018-2022---units-reporting-events.xlsx
- **Landing page:** https://www.nerc.com/programs/reliability-assessment--performance-analysis/generating-availability-data-system/gads-conventional/generating-unit-statistical-brochures
- **Retrieved:** 2026-07-08, via `curl` through the environment's configured proxy (`GET`
  returned HTTP 200, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`,
  43,402 bytes; Start/End=2018/2022 columns in the sheet confirm the vintage).
- **License/access:** Public NERC statistical brochure, no login/paywall — same basis as
  `nerc-gads-eford-2019-2023`.

## Extraction

`nerc_gads_eford_2018-2022.csv` uses the identical column reduction and suppression
handling as `nerc-gads-eford-2019-2023`: `Generator Catagory/Classification, Start, End,
# Units, Unit-Years, NMC, FOR, EFOR, EFORd`; rows NERC suppressed (n≤3 reporting units,
marked `*`) are dropped. All percentages are NERC's native units.

Re-run to reproduce:
```
curl -sSL -A "Mozilla/5.0" \
  "https://www.nerc.com/globalassets/programs/rapa/gads/reports/generating-unit-statistical-brochure-3---2018-2022---units-reporting-events.xlsx" \
  -o brochure_2018_2022.xlsx
# then extract Sheet1 columns listed above with openpyxl/pandas.
```

## Scope

Same NERC-wide-only scope as `nerc-gads-eford-2019-2023` — see that README for the full
scope note and the rule-14 misalignment discussion in `constants.py`/`docs/parameter-citations.md`.

## Relevant rows for gas-fired availability

| Category | EFORd (%) | 1 − EFORd |
|---|---|---|
| GAS TURBINE, All Sizes | 10.50 | 0.8950 |
| COMBINED CYCLE, All Sizes | 4.43 | 0.9557 |
| FOSSIL Gas Primary, All Sizes | 12.60 | 0.8740 |
| FOSSIL Oil/Gas Primary, All Sizes | 12.82 | 0.8718 |

Compare to the `2019-2023` window (Gas Turbine 10.33 / Combined Cycle 4.71 / Gas Primary
13.44) and the `2020-2024` window (9.85 / 4.91 / 14.26): shifting the pool one year
earlier (dropping 2023, adding 2018) lowers pooled Gas Primary EFORd — consistent with
the annual series in `nerc-gads-eford-annual-2018-2024`, which shows Gas Primary EFORd
rising fairly steadily from 11.5% (2018) to 17.0% (2024).
