# EIA-930 per-BA wide hourly extracts

One `<BA> hourly.parquet` per EIA-930 balancing authority (built by
`scripts/convert_eia930.py` / refreshable via `scripts/fetch_eia930_hourly.py`).
Columns: `UTC time`, `Local time`, `Local date`, `Demand`, `Demand forecast`,
`Net generation`, `Total interchange`, and one `NG: <code>` column per fuel type
the BA reports. Consumed by `src/market_sim/data/eia_loader.py`
(`_eia_hourly_frame*`, `load_demand`, `load_eia_hourly_renewable_gen`, …) and
`src/market_sim/data/renewables.py` (`load_renewable_profiles`).

## Coverage on disk (checked 2026-07-08)

| BA | ISO | Span |
|---|---|---|
| ERCO | ERCOT | 2015-07-01 .. 2026-06-30 |
| ISNE | NEISO | 2015-07-01 .. 2026-05-20 |
| NYIS | NYISO | 2015-07-01 .. 2026-06-13 |
| SWPP | — (SPP, not a modeled ISO) | 2015-07-01 .. 2026-05-20 |
| PJM | PJM | 2018-01-01 .. 2026-06-30 (2019-2021 backfilled 2026-07-06; 2018 backfilled 2026-07-08) |
| CISO | CAISO | 2018-01-01 .. 2026-06-30 (2019-2021 backfilled 2026-07-06; 2018 + H1-2026 landed 2026-07-08) |
| MISO | MISO | 2018-01-01 .. 2026-06-30 (2019-2021 backfilled 2026-07-06; 2018 + H1-2026 landed 2026-07-08) |
| SOCO | — (Southern Co, not a modeled ISO) | 2022-12-31 .. 2025-12-31 |
| FLA | — (Florida, not a modeled ISO) | 2022-12-31 .. 2025-01-31 |

2018 H1 (Jan-Jun) carries demand/net-generation/total-interchange only — EIA-930
per-fuel reporting hadn't started yet for any of these three BAs (`NG: *` columns
are all `NaN`, a real reporting gap, not a fabricated split); PJM's per-fuel
reporting itself only ramps up gradually across 2018 H2 (0% of hours in
Jul/Aug, ~40% in Sep, 100% from October on) — a genuine phased-rollout
artifact of the source, not a processing bug.

## 2019-2021 CAISO / PJM / MISO backfill (2026-07-06)

The 2026-07 weather-year pool widening
(`docs/handoffs/probability-bounds-plan-2026-07.md` §2.1,
`docs/weather-pool-coverage-2026-07.md`) originally added 2019-2021 only to
ERCOT/NEISO (NYISO got 2021 only) because CAISO/PJM/MISO had no raw coverage
that far back. Extending them via `scripts/fetch_eia930_hourly.py` (EIA API
v2, `api.eia.gov`) was believed blocked by this sandbox's network allowlist
at the time (no `EIA_API_KEY` was configured in that session) — **that has
since changed: a working `EIA_API_KEY` is now present in the repo's `.env`,
and `api.eia.gov` is directly reachable (confirmed 2026-07-08). The note
below about the BALANCE bulk archive as a workaround is kept for the
2019-2021 wide-hourly backfill (still the right tool for folding years into
the wide extract), but the API itself is no longer assumed unreachable —
see the 2026-07-08 section.**

The six-month **BALANCE bulk archive**
(`www.eia.gov/electricity/gridmonitor/sixMonthFiles/`, a different host,
already used by `scripts/fetch_eia930_balance.py` for 2022+), which carries
the same demand + fuel-type generation series back to 2019. 2019-2021 were
fetched into `data/raw/eia-930/EIA930_BALANCE_{year}_{half}.parquet` and
folded into `CISO`/`PJM`/`MISO hourly.parquet` here via
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

## 2018 backfill + H1-2026 extension + 2022/H1-2026 long-form intake (2026-07-08)

CLAUDE.md rule 22 was amended 2026-07-06 (Option 2,
`docs/handoffs/holdout-policy-memo-2026-07.md` §(e)) to split **data intake**
for any out-of-training year (2018, 2019, ≤2021, 2022, H1-2026) — allowed any
time, any ISO, under explicit session-logged owner authorization, validated
no-LP only — from **solve/score/registration**, which stays fully quarantined
until the ISO's `calibration-complete` marker exists. Under that authorization
(logged in `frontend/data/backcast/calibration-complete.json`'s `intake_log`),
this session:

- **Backfilled 2018** for PJM/CISO/MISO via the BALANCE bulk archive
  (`extend_eia930_hourly_from_balance.py --year 2018`, generalized from the
  2019-2021 pass to take `--year`/`--half`). 2018 H1 has no per-fuel columns
  in EIA's own source at all (see the coverage table note above); the script
  was fixed so a source year genuinely missing fuel-type columns reindexes
  them in as `NaN` (`fetch_eia930_balance.py`) instead of erroring, and so the
  `NG: OTH` fold no longer fabricates a `0` when every "other"-bucket source
  column is absent for an hour (it previously always did, via an
  unconditional `.fillna(0.0)` — a real bug, now fixed for both the legacy
  and the mid-2024-revamped BALANCE taxonomies).
- **Extended CISO/MISO through H1-2026** by folding the already-fetched
  `EIA930_BALANCE_2026_Jan_Jun.parquet` (new 65-column taxonomy) into the wide
  extracts. The extend script now maps Geothermal/Battery Storage 1:1 into
  `NG: GEO`/`NG: BAT` when the target extract carries that column (CISO has
  `NG: GEO`, MISO has `NG: BAT`), and sums the hydro/solar/wind
  pumped-storage/battery-integration splits back into the one `NG: WAT` /
  `NG: SUN` / `NG: WND` code the legacy taxonomy uses.
- **Intook CAISO/MISO 2022 and H1-2026 fuel-type/region long-form data**
  (`data/raw/eia-930/{CISO,MISO}_{fueltype,region}_{2022,2026}.parquet`) via
  `scripts/fetch_eia930_long.py` against the now-reachable `api.eia.gov`,
  matching the schema of the existing ERCO/PJM 2022/2026 siblings exactly.

All of the above is byte-identity-verified against the pre-existing
2019-2025 rows (0 mismatched cells) — no-LP intake per rule 22, not a solve
or a score.
