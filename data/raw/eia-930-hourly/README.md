# EIA-930 per-BA wide hourly extracts

One `<BA> hourly.parquet` per EIA-930 balancing authority (built by
`scripts/convert_eia930.py` / refreshable via `scripts/fetch_eia930_hourly.py`).
Columns: `UTC time`, `Local time`, `Local date`, `Demand`, `Demand forecast`,
`Net generation`, `Total interchange`, and one `NG: <code>` column per fuel type
the BA reports. Consumed by `src/market_sim/data/eia_loader.py`
(`_eia_hourly_frame*`, `load_demand`, `load_eia_hourly_renewable_gen`, …) and
`src/market_sim/data/renewables.py` (`load_renewable_profiles`).

## Coverage on disk (checked 2026-07-05)

| BA | ISO | Span |
|---|---|---|
| ERCO | ERCOT | 2015-07-01 .. 2026-06-30 |
| ISNE | NEISO | 2015-07-01 .. 2026-05-20 |
| NYIS | NYISO | 2015-07-01 .. 2026-06-13 |
| SWPP | — (SPP, not a modeled ISO) | 2015-07-01 .. 2026-05-20 |
| PJM | PJM | 2021-12-31 .. 2026-06-30 |
| CISO | CAISO | 2022-12-31 .. 2025-12-31 |
| MISO | MISO | 2022-12-31 .. 2025-12-31 |
| SOCO | — (Southern Co, not a modeled ISO) | 2022-12-31 .. 2025-12-31 |
| FLA | — (Florida, not a modeled ISO) | 2022-12-31 .. 2025-01-31 |

## DATA NEEDED: CAISO / PJM / MISO, 2019-2021

The 2026-07 weather-year pool widening
(`docs/handoffs/probability-bounds-plan-2026-07.md` §2.1,
`docs/weather-pool-coverage-2026-07.md`) added 2019-2021 to the ERCOT/NEISO
forecast-ensemble weather-year pool (NYISO got 2021 only — see the coverage
note) using the years already present above. CAISO, PJM and MISO have no raw
coverage that far back and stay on the 2023-2025 window until `CISO`/`PJM`/
`MISO hourly.parquet` are extended.

**Blocked in the managed sandbox, 2026-07-05.** Extending them requires
`scripts/fetch_eia930_hourly.py` against the EIA API v2
(`api.eia.gov/v2/electricity/rto/...`), which returns HTTP 403 from this
environment's network allowlist (confirmed by direct `curl`; no
`EIA_API_KEY` is configured here either). The script's own docstring already
notes it must be run locally. To land the years once run locally:

```bash
python scripts/fetch_eia930_hourly.py --ba CISO --start 2019-01-01 --end 2021-12-31
python scripts/fetch_eia930_hourly.py --ba PJM  --start 2019-01-01 --end 2021-12-31
python scripts/fetch_eia930_hourly.py --ba MISO --start 2019-01-01 --end 2021-12-31
```

then upload the refreshed `<BA> hourly.parquet` files here (they must be
merged with the existing 2022+ rows, not overwritten — see the script's
`--out` flag) and add the verified years to
`constants.WEATHER_YEAR_POOL_BY_ISO["CAISO"|"PJM"|"MISO"]` following the same
end-to-end verification method documented in
`docs/weather-pool-coverage-2026-07.md` (a clean 8760-hour demand series AND
`market_sim.data.renewables.load_renewable_profiles` resolving with no
exception — PJM/CAISO/MISO's fallback coverage floors haven't been checked
past what ERCOT/NEISO/NYISO needed).

2022 and H1-2026 must **not** be fetched for any BA under the rule-22 holdout
quarantine (`CLAUDE.md`), regardless of ISO, until that ISO's
calibration-complete marker exists.
