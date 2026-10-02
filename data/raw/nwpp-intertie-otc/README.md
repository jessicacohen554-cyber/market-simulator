# BPA OPI intertie loadings and operating limits (COI and BC Intertie)

Intake: NWPP-NEXT-22 (2026-10-02), for the NWPP seam headroom key `nwpp_seam_measured_limits`.

## What it is

BPA Transmission's Operations Information page "BPA Paths - OPI Interties & Flowgates"
(<https://transmission.bpa.gov/Business/Operations/Paths/>) archives one spreadsheet per intertie and calendar
month. Each spreadsheet holds 15-minute rows, and each row is the 15-minute average of 2-second SCADA data.

| path | intertie | columns as published (SCADA PI point) | sign |
|---|---|---|---|
| `AC` | AC Intertie (COI, California-Oregon) | Actual (36918), N-S TTC (163420), S-N TTC (163421), Loop Flow COI + Path 66 (52476) | actual + = to California; S-N TTC published negative |
| `BC` | BC Intertie (Path 3, West + East) | Actual (36885), S-N TTC (163470), N-S TTC (163469) | actual + = south to north (to BC); N-S TTC published negative |

The Notes sheet defines TTC as the intertie's **operating limit**, the system operating limit BPA monitors
against. It moves with outages and system conditions, and it is stated "not considering Intertie Ownership".

- For COI, the TTC is the whole Path 66 (all owners, including COTP). The share CAISO schedules against is
  CAISO OASIS `MALIN500_ISL` + `CASCADE_ITC` (`data/raw/caiso-trns-usage`). Over 2023-06-19 to 2025 that share
  is 0.667 of this limit at the median, in both directions.
- For the BC Intertie, the BPAT-to-BCHA measured interchange matches this path's actual loading. For example,
  2023 averaged 1,087 MW here against 1,082 MW on the EIA-930 BPAT-BCHA leg.

## Files

- `bpa_intertie_otc_<year>.parquet`: **committed**, one per calendar year of the published `Date/Period Ending`
  stamp. The layout is long, with columns `path` (`AC` / `BC`), `ts_end_local` (Pacific prevailing time, naive,
  period-ending as published), `actual_mw`, `ns_ttc_mw`, `sn_ttc_mw` and `loop_mw` (`AC` only). Values and signs
  are exactly as published. `bpa_intertie_otc_2026.parquet` holds only the period ending
  2026-01-01 00:00, which is the last quarter-hour of 2025.
- `SHA256SUMS.txt`: the identity record of the committed parquets.
- `windows/`: the monthly source spreadsheets, staged by the fetcher. **Gitignored.**

## Source and re-fetch

`https://transmission.bpa.gov/Business/Operations/Paths/Monthly.aspx?Type=Intertie&ReportID=<AC|BC>&ReportName=<AC|BC>`
lists every monthly file, for example
`https://transmission.bpa.gov/BUSINESS/Operations/Paths/Interties/monthly/AC/2019/AC_2019-07.xls`.
Files from 2023 onwards are `.xls`, and some later months are `.xlsx`.

```
python scripts/data/fetch_bpa_intertie_otc.py --years 2019 2020 2021 2022 2023 2024 2025   # stage
python scripts/data/fetch_bpa_intertie_otc.py --fold                                        # -> parquets
```

Fetched 2026-10-02. The archive starts in 1996. A year outside 2019–2025 is fetched only when a lane needs it.

## Curation

These files are curated into the `transfer-interface-limits` clean datatype as the `NWPP` partition (spec
`scripts/lib/transfer_interface_limits/nwpp.py`). The series are `"<COI|BC>|<NS|SN>|OTC"`, on NWPP's fixed-PST
non-leap 8760 clock, and `transfer_mw` carries the actual loading.

## Admissibility (rules 13 and 14)

An operating transfer limit is a physical operating condition, the same kind of input as an outage window. It
regenerates for any year from the same feed and responds to outages and re-ratings. Its forward analogue is the
seasonal path rating. The `actual_mw` loading is a measured outcome and is used only as a diagnostic, never as an
input or a target.

DATA NEEDED: none for 2019–2025.
