# EIA-930 per-BA wide hourly extracts

One `<BA> hourly.parquet` per EIA-930 balancing authority (built by
`scripts/convert_eia930.py` / refreshable via `scripts/fetch_eia930_hourly.py`).
Columns: `UTC time`, `Local time`, `Local date`, `Demand`, `Demand forecast`,
`Net generation`, `Total interchange`, and one `NG: <code>` column per fuel type
the BA reports. Consumed by `src/market_sim/data/eia_loader.py`
(`_eia_hourly_frame*`, `load_demand`, `load_eia_hourly_renewable_gen`, …) and
`src/market_sim/data/renewables.py` (`load_renewable_profiles`).

## Coverage on disk (checked 2026-07-06)

| BA | ISO | Span |
|---|---|---|
| ERCO | ERCOT | 2015-07-01 .. 2026-06-30 |
| ISNE | NEISO | 2015-07-01 .. 2026-05-20 |
| NYIS | NYISO | 2015-07-01 .. 2026-06-13 |
| SWPP | — (SPP, not a modeled ISO) | 2015-07-01 .. 2026-05-20 |
| PJM | PJM | 2019-01-01 .. 2026-06-30 (2019-2021 backfilled 2026-07-06) |
| CISO | CAISO | 2019-01-01 .. 2025-12-31 (2019-2021 backfilled 2026-07-06) |
| MISO | MISO | 2019-01-01 .. 2025-12-31 (2019-2021 backfilled 2026-07-06) |
| SOCO | — (Southern Co, not a modeled ISO) | 2022-12-31 .. 2025-12-31 |
| FLA | — (Florida, not a modeled ISO) | 2022-12-31 .. 2025-01-31 |

## 2019-2021 CAISO / PJM / MISO backfill (2026-07-06)

The 2026-07 weather-year pool widening
(`docs/handoffs/probability-bounds-plan-2026-07.md` §2.1,
`docs/weather-pool-coverage-2026-07.md`) originally added 2019-2021 only to
ERCOT/NEISO (NYISO got 2021 only) because CAISO/PJM/MISO had no raw coverage
that far back, and extending them via `scripts/fetch_eia930_hourly.py`
(EIA API v2, `api.eia.gov`) is blocked by this sandbox's network allowlist
(confirmed by direct `curl`; still true — no `EIA_API_KEY` configured here
either).

That block doesn't apply to the six-month **BALANCE bulk archive**
(`www.eia.gov/electricity/gridmonitor/sixMonthFiles/`, a different host,
already used by `scripts/fetch_eia930_balance.py` for 2022+), which carries
the same demand + fuel-type generation series back to 2019. 2019-2021 were
fetched into `data/raw/eia-930/EIA930_BALANCE_{year}_{half}.parquet` and
folded into `CISO`/`PJM`/`MISO hourly.parquet` here via the new
`scripts/extend_eia930_hourly_from_balance.py` (never altering an
already-committed row — a UTC-time dedup keeps the pre-existing row on any
overlap, e.g. PJM's 2021/2022 boundary).

CAISO and MISO now resolve the full 2019-2021 span end-to-end (demand +
renewables); PJM's demand doesn't route through this extract at all (always
falls back to `eia_demand_profiles.parquet`, whose own floor is 2021), so
only 2021 landed in PJM's pool despite its renewables now resolving for
2019/2020 too. See `docs/weather-pool-coverage-2026-07.md`'s 2026-07-06
addendum for the full verification table and the geothermal/battery fidelity
caveat (the BALANCE bulk archive's legacy taxonomy doesn't split those out;
they fold into `NG: OTH` as `NaN`, not fabricated zero, for these three
years).

2022 and H1-2026 must **not** be fetched for any BA under the rule-22 holdout
quarantine (`CLAUDE.md`), regardless of ISO, until that ISO's
calibration-complete marker exists — the BALANCE bulk fetch above was
confined to 2019-2021 for exactly this reason.
