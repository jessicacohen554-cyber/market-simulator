# caiso-outlook-fuelsource — raw

CAISO "Today's Outlook" historical system fuel mix, 5-minute grain, one
gzipped CSV per calendar year.

| file | content |
|---|---|
| `fuelsource_<year>.csv.gz` | every 5-minute row of every day of `<year>` as CAISO published it, a `date` column prepended, header lower-snake-cased: `date, time, solar, wind, geothermal, biomass, biogas, small_hydro, coal, nuclear, natural_gas, large_hydro, batteries, imports, other` (MW, Pacific prevailing wall clock) |
| `SHA256SUMS.txt` | identity record of the yearly payloads |

**Source (primary, ISO-native):** `https://www.caiso.com/outlook/history/<YYYYMMDD>/fuelsource.csv`
(one file per day). **Fetcher / re-fetch command:**
`python scripts/data/fetch_caiso_outlook_fuelsource.py --years 2019 2020 2021`.
No value is altered; only the header case is normalised (the source itself
spells "Natural gas"/"Natural Gas" and "Large hydro"/"Large Hydro" on different
days). Gzip `mtime=0`, so a re-fetch of unchanged data is byte-identical.

## Why it is here

EIA-930 CISO `NG: WAT` (conventional hydro) is **missing** (NaN) from
2019-10-01 through 2020-08-24, including in EIA's own `(Adjusted)`/`(Imputed)`
columns, and `Net generation` omits hydro in those hours because it is the sum
of the reported fuel cells. `large_hydro + small_hydro` from this series is the
measured source that repairs both at the EIA-930 frame seam
(`src/market_sim/data/eia930/caiso_hydro_backfill.py`), which feeds the
measured hydro budget, the hydro envelope/min-flow levels and the CAISO
supply-consistent demand artifact.

**Validation (2019, the overlap before the hole):** EIA-930 `NG: WAT` =
0.9965 × Outlook hydro over 6,557 common hours; every month Jan–Sep within
±0.5 %; mean |Δ| 87 MW; hourly r 0.94. Clock alignment is measured on the
sharper series — grouping by UTC hour-beginning matches EIA-930's row stamp at
lag 0 for solar (r 0.970), gas (0.986) and nuclear (1.000).

Coverage: 2019, 2020, 2021 (the backcast years with the hole or adjacent to
it). No file is committed for 2022+, which is what keeps every 2022–2025 frame
byte-identical.

Full intake record: `docs/handoffs/i-caiso/INTAKE-i-caiso-2019-2021-2026-09-24.md`.
