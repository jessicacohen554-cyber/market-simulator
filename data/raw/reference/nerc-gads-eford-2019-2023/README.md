# NERC GADS Generating Unit Statistical Brochure — 2019-2023 (EFOR/EFORd by class)

Source for `GAS_AVAILABILITY_FACTOR` (`constants.py`) and the existing `EFORD` dict
(`constants.py`), which the header comment already cited as "NERC GADS" without a
retrievable table on disk (scalar-remediation batch B-XISO-1 / audit C-18, 2026-07-05).

## Provenance

- **Publisher:** NERC (North American Electric Reliability Corporation), Reliability
  Assessment & Performance Analysis (RAPA) program, Generating Availability Data System
  (GADS).
- **Document:** "Generating Unit Statistical Brochure 3 — 2019-2023 — Units Reporting
  Events" (5-year rolling class-average statistics; NERC-wide, not region-specific — see
  Scope below).
- **URL:** https://www.nerc.com/globalassets/programs/rapa/gads/conventional/generating-unit-statistical-brochure-3-2019-2023---units-reporting-events.xlsx
- **Landing page:** https://www.nerc.com/programs/reliability-assessment--performance-analysis/generating-availability-data-system/gads-conventional/generating-unit-statistical-brochures
- **Retrieved:** 2026-07-05, via `curl` through the environment's configured proxy
  (`GET` returned HTTP 200, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`,
  48,438 bytes; the brochure numbering ("Brochure 3") and Start/End=2019/2023 columns in
  the sheet itself confirm the vintage matches `constants.py`'s existing "NERC GADS
  2019-2023" citation).
- **License/access:** Public NERC statistical brochure, no login/paywall; publicly
  citable per NERC's own GADS reporting-instructions documents (`gads_dri_2024.pdf`
  etc.), which describe the brochures as the public output of the mandatory GADS
  reporting program.

## Extraction

`nerc_gads_eford_2019-2023.csv` is the brochure's single data sheet, columns reduced to
`Generator Catagory/Classification, Start, End, # Units, Unit-Years, NMC, FOR, EFOR,
EFORd` (dropped: the ~45 intermediate hour/event/rate columns not needed here — SH, RSH,
FOH, POH, MOH, weighted variants WSF/WAF/... etc.; see the source brochure for the full
NERC column set and Appendix F of the GADS Data Reporting Instructions for every
column's definition). Rows where NERC suppressed the value for n≤3 reporting units
(marked `*` in the source) are dropped rather than kept as a literal asterisk string.
All percentages are NERC's native units (percent, not fraction) — e.g. `EFORd=10.92`
means 10.92%.

Re-run to reproduce:
```
curl -sSL -A "Mozilla/5.0" \
  "https://www.nerc.com/globalassets/programs/rapa/gads/conventional/generating-unit-statistical-brochure-3-2019-2023---units-reporting-events.xlsx" \
  -o brochure_2019_2023.xlsx
# then extract Sheet1 columns listed above with openpyxl/pandas.
```

## Scope — NERC does not publish a per-ISO/regional breakdown

The brochure is a **NERC-wide** (all Regional Entities combined) table, keyed only by
generator category/technology (Combined Cycle, Gas Turbine, Fossil Gas/Oil/Coal Primary
by nameplate-size band) and fuel — **not** by NERC Region, RTO/ISO, or utility. This is
the entire public GADS statistical-brochure product; NERC does not publish an
ISO-specific EFOR/EFORd cut in this series. See `docs/parameter-citations.md` and the
`GAS_AVAILABILITY_FACTOR` comment in `constants.py` for how this shapes the disposition
of the per-ISO scalar (rule-14 misalignment: the published data's boundary — NERC-wide —
does not match the model's per-ISO parameterization, so a single NERC-wide figure is
used for every ISO rather than inventing an unsupported per-ISO split).

## Relevant rows for gas-fired availability

| Category | EFORd (%) | 1 − EFORd |
|---|---|---|
| GAS TURBINE, All Sizes | 10.33 | 0.8967 |
| GAS TURBINE, 50 Plus MW | 9.39 | 0.9061 |
| COMBINED CYCLE, All Sizes | 4.71 | 0.9529 |
| FOSSIL Gas Primary, All Sizes | 13.44 | 0.8656 |
| FOSSIL Oil/Gas Primary, All Sizes | 13.63 | 0.8637 |

`FOSSIL Gas Primary, All Sizes` (combustion turbines + combined cycle + gas steam,
pooled by fuel rather than split by prime-mover) is the closest published match to the
model's single-scalar `GAS_AVAILABILITY_FACTOR` concept ("gas-fired generation
availability... by ISO"); `constants.py`'s separate per-technology `EFORD` dict
(`gas_cc`/`gas_ct`/`gas_st`) already draws on the technology-split rows above (compare
`gas_cc=0.05` vs. published Combined Cycle EFORd 4.71%, and `gas_ct=0.06`/`gas_st=0.07`
vs. the Gas Turbine/Gas Primary rows) — see the boundary note in `constants.py` next to
`GAS_AVAILABILITY_FACTOR` for the double-counting analysis between the two.
