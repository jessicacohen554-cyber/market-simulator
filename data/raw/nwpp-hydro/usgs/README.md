# USGS daily discharge — Columbia mainstem and lower-river tributaries (NWPP-50)

Independent streamgage record used by **NWPP-50** to test the NWPP-36 side-inflow gate
(`docs/handoffs/FINDING-nwpp-50-2026-09-24.md`). Diagnostic input only: nothing in `src/` reads it.

## File

`nwpp_usgs_daily_discharge.csv`, long form: `site_no, site_name, date, discharge_cfs, qualifiers`.
It holds 7 sites × 1,096 days (2023-01-01 → 2025-12-31). The file is the USGS NWIS daily-value
JSON flattened as-is, with no filling and no rescaling. `qualifiers` are USGS codes: `A` approved,
`P` provisional, `R` revised, `e` estimated.

| site | name | role in the balance |
|---|---|---|
| 14105700 | Columbia R at The Dalles, OR | mainstem gauge just below The Dalles Dam |
| 12472800 | Columbia R below Priest Rapids Dam, WA | mainstem gauge just below Priest Rapids |
| 14103000 | Deschutes R at Moody, OR | tributary entering between John Day and The Dalles |
| 14048000 | John Day R at McDonald Ferry, OR | tributary entering the John Day pool |
| 14033500 | Umatilla R near Umatilla, OR | tributary entering the John Day pool |
| 12510500 | Yakima R at Kiona, WA | tributary entering the McNary pool |
| 14018500 | Walla Walla R near Touchet, WA | tributary entering the McNary pool |

## Re-fetch (pulled 2026-09-24)

    https://waterservices.usgs.gov/nwis/dv/?format=json&sites=14105700,12472800,14103000,14048000,12510500,14033500,14018500&parameterCd=00060&statCd=00003&startDT=2023-01-01&endDT=2025-12-31

`SHA256SUMS.txt` records this pull. Provisional (`P`) values can be revised later, so a re-fetch
may differ slightly.
