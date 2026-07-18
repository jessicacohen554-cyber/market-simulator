# Weather-year pool widening — per-ISO coverage note (2026-07)

**What this is.** The data-intake companion to
`docs/handoffs/probability-bounds-plan-2026-07.md` §2.1, which flagged the
3-draw `WEATHER_YEAR_POOL` (2023-2025) as "thin" and "intaking more pre-2022
weather years is a cheap widening — separate data-intake task." This is that
task: which ISO-years actually landed, which were skipped, and why.

**Scope.** Weather-year sampling is a forecast-ensemble input (weather load
shape + VRE capacity factor), never a new backcast year — no bench actuals, no
scoring, nothing registered on the backcast dashboard. Candidate years are
2019-2021 only: EIA-930 hourly coverage begins mid-2018 (2019 is the first
clean full year), and 2022 / H1-2026 are under the rule-22 holdout quarantine
(no data intake of any kind until each ISO's calibration-complete marker
exists).

## Method

A year is added to an ISO's pool only after it passes **both**:

1. `market_sim.data.eia_loader._eia_hourly_frame(<BA>, year)` returns a clean,
   gap-free 8760-row local-calendar series (the same strict check every
   existing backcast year must pass) — checked against
   `data/raw/eia-930-hourly/<BA> hourly.parquet`.
2. `market_sim.data.renewables.load_renewable_profiles(iso, year, ...)`
   resolves both wind and solar end-to-end with no exception — this catches
   an ISO whose BA under-reports one fuel and silently needs a fallback
   dataset that doesn't cover the candidate year.

No new raw files were added — every landed year was already present in the
already-committed `data/raw/eia-930-hourly/*.parquet` (these extracts already
span back to 2015-07-01 for several BAs; only `WEATHER_YEAR_POOL` and its
consumers hadn't been widened to use it).

## Verified per-ISO coverage (checked 2026-07-05)

| ISO | BA | Raw hourly extract span | 2019 | 2020 | 2021 | Landed pool |
|---|---|---|---|---|---|---|
| ERCOT | ERCO | 2015-07-01 .. 2026-06-30 | pass | pass | pass | `(2019, 2020, 2021, 2023, 2024, 2025)` |
| NEISO | ISNE | 2015-07-01 .. 2026-05-20 | pass | pass | pass | `(2019, 2020, 2021, 2023, 2024, 2025)` |
| NYISO | NYIS | 2015-07-01 .. 2026-06-13 | **fail** (solar) | **fail** (solar) | pass | `(2021, 2023, 2024, 2025)` |
| CAISO | CISO | 2019-01-01 .. 2025-12-31 (2026-07-06 backfill) | pass | pass | pass | `(2019, 2020, 2021, 2023, 2024, 2025)` |
| PJM | PJM | 2019-01-01 .. 2026-06-30 (2026-07-06 backfill) | pass (renewables only) | pass (renewables only) | pass | `(2021, 2023, 2024, 2025)` |
| MISO | MISO | 2019-01-01 .. 2025-12-31 (2026-07-06 backfill) | pass | pass | pass | `(2019, 2020, 2021, 2023, 2024, 2025)` |

See "2026-07-06 update" below for how CAISO/PJM/MISO moved from "no raw data" to the rows above, and why PJM's 2019/2020 still don't land in its pool despite the hourly extract now covering them.

("pass" = both checks in Method above succeeded end-to-end with real repo data.)

### NYISO 2019/2020 — why they failed despite raw coverage existing

NYIS never separately reports solar generation over EIA-930 (`NG: SUN` is
all-zero in *every* year on file, including the already-supported 2023-2025),
so NYISO solar always falls back to the EIA-930 generation-**distribution**
parquet (`data/raw/eia-930/eia_generation_profiles.parquet`). That parquet's
own coverage floor is **2021** — it does not go back to 2019/2020 for any ISO.
So while NYISO's raw hourly demand extract does cover 2019/2020, the
renewables path raises (`ValueError: No EIA-930 data for ISO 'NYISO' in year
2019`). Only 2021 was added for NYISO; 2019/2020 stay out until the
distribution parquet is rebuilt further back (a separate, larger intake — that
parquet is a derived/reprocessed artifact, not a raw download, and rebuilding
it was out of scope here).

### CAISO / PJM / MISO — why they were originally skipped (resolved 2026-07-06)

Their `<BA> hourly` extracts didn't reach back that far on disk (see table).
Fetching more history via `scripts/data/fetch_eia930_hourly.py` needs the EIA API
v2, which is **blocked in this managed sandbox** (`api.eia.gov` returns HTTP
403; the script's own docstring already says "Run locally — the managed
environment's allowlist blocks api.eia.gov"), and no `EIA_API_KEY` is
configured here either. That part is still true today.

## 2026-07-06 update: BALANCE-bulk backfill unblocks CAISO/PJM/MISO

The API v2 host is blocked, but the EIA Hourly Electric Grid Monitor's
six-month **BALANCE bulk archive** (`www.eia.gov/electricity/gridmonitor/
sixMonthFiles/`, a different host) is reachable from this sandbox and carries
the same per-BA demand + fuel-type-generation series for every BA, back to
2019. `scripts/data/fetch_eia930_balance.py` already existed for the 2022+ files;
it was rerun for `--year {2019,2020,2021} --half {Jan_Jun,Jul_Dec}` (6 new
files, schema-verified against the committed 2023+ siblings).

A new script, `scripts/data/extend_eia930_hourly_from_balance.py`, folds those
bulk rows into the wide `<BA> hourly.parquet` extracts CISO/PJM/MISO already
had for 2022+, without touching a single already-committed row (a
UTC-time dedup always keeps the pre-existing row when the BALANCE bulk hour
and a committed hour collide, e.g. the 2021/2022 boundary for PJM).

**Fidelity caveat.** The BALANCE bulk archive's legacy (pre-mid-2024)
taxonomy doesn't break out geothermal or battery storage as their own fuel
columns, and reports hydro + pumped storage as one combined figure (matching
what CISO/PJM/MISO's existing extracts already do for hydro/PS, but not for
CAISO's geothermal or MISO's battery, which the existing API-sourced 2022+
rows do split out). The 2019-2021 rows fold geothermal/battery into `NG: OTH`
as `NaN` (never a fabricated 0) for the columns the target extract already
carries. This is immaterial to the weather-pool's own admission criteria —
`load_renewable_profiles` only reads `NG: WND` / `NG: SUN` — but would matter
to a future consumer of CAISO geothermal or MISO battery generation for these
specific years.

**Verification (both Method checks above, run 2026-07-06):**

| ISO | `_eia_hourly_frame` 8760 check | `load_renewable_profiles` end-to-end | `load_demand` end-to-end |
|---|---|---|---|
| CAISO 2019/2020/2021 | pass | pass | pass |
| MISO 2019/2020/2021 | pass | pass | pass |
| PJM 2019/2020/2021 | pass | pass | **2019/2020 fail, 2021 passes** |

PJM's demand never actually routes through the hourly extract —
`market_sim.data.eia_loader.load_demand`'s PJM branch always falls back to
`eia_demand_profiles.parquet` (see that function's docstring: "every PJM
year" uses the fallback), and that source's own floor is 2021 — the same
single-source-floor situation as NYISO's solar. So PJM's landed pool gains
only 2021, matching NYISO's precedent, even though its renewables now resolve
for 2019/2020 too. **Landed pools:** CAISO/MISO `(2019, 2020, 2021, 2023,
2024, 2025)`; PJM `(2021, 2023, 2024, 2025)`.

## What was NOT extended: the daily temperature/weather overlay

The per-ISO daily TMAX/TMIN CSVs under `data/raw/<iso>-weather/` (consumed by
`market_sim.data.eia_loader.load_weather` / `iso_zone_tmax`, feeding cold-
weather gas derates and reliability floors) cover **2023-2025 only, for every
ISO** — including ERCOT/NEISO/NYISO, whose EIA-930 hourly extracts go back
much further. These CSVs are hand-curated from NOAA station data with no
fetch script in this repo, and widening them was out of scope for this pass.

Practically: a weather-year draw of 2019/2020/2021 gets the real measured
load shape and VRE CF for that year, but **no** measured-temperature-driven
floor/derate for that year — `load_weather` returns `None` for an uncovered
year and every caller's documented fallback is "leave the fleet unfloored
(byte-identical)". This does not break a solve; it just means the physical
cold-snap mechanics (e.g., ERCOT winter gas derates) don't fire for those
draws specifically. Flagged here per the "honest labels" design constraint in
`docs/handoffs/probability-bounds-plan-2026-07.md` §0.5 — a future intake pass
should extend these CSVs to match if the weather-driven floor mechanics matter
for the widened years.

## The COVID-2020 anomaly

2020 is included (ERCOT, NEISO) as an admissible historical weather-year
input — it is a real, physically-grounded year like any other — but its
demand shape carries the well-documented COVID-19 load depression (EIA/FERC
2020 load-impact reporting: a multi-percent spring/summer reduction vs.
pre-pandemic trend, concentrated in commercial load). It is intentionally
**not** down-weighted or excluded by default (`configs/uncertainty_ercot.yaml`
keeps all six ERCOT pool years at uniform 1/6 weight) so that choice stays a
disclosed, client-adjustable judgment rather than a baked-in one — see the
comment on `discrete_weights.weather` in that file.

## What changed in code

- `src/market_sim/config/constants.py`: added `WEATHER_YEAR_POOL_BY_ISO`
  (per-ISO registry, cited per entry) and a `weather_year_pool(iso)` lookup
  helper. `WEATHER_YEAR_POOL` itself is unchanged (2023-2025) and now serves
  as the documented cross-ISO fallback for an ISO not in the registry.
- `src/market_sim/ensemble.py`: `weather_ensemble_configs` now defaults to
  `weather_year_pool(base_config.iso)` instead of the flat global pool, so
  ERCOT/NEISO/NYISO ensembles get the widened draw set automatically while
  CAISO/PJM/MISO are unaffected (byte-identical default behaviour).
- `configs/uncertainty_ercot.yaml`: the PB-2 sampler's `discrete_weights.weather`
  block widened to the six verified ERCOT years, uniform 1/6.
- Tests: `tests/test_eia_loader.py` (`TestWeatherPoolWidening`),
  `tests/test_renewables.py`
  (`test_ercot_2019_renewable_profiles_resolve_end_to_end`),
  `tests/test_ensemble.py` (per-ISO default-pool tests) exercise the new
  years and lock in the CAISO/PJM/MISO boundary.

**2026-07-06 addendum:**

- `data/raw/eia-930/EIA930_BALANCE_{2019,2020,2021}_{Jan_Jun,Jul_Dec}.parquet`:
  6 new raw files (`scripts/data/fetch_eia930_balance.py`, `www.eia.gov` bulk host).
- `scripts/data/extend_eia930_hourly_from_balance.py`: new script, folds the
  BALANCE bulk rows into `data/raw/eia-930-hourly/{CISO,PJM,MISO} hourly.parquet`
  back to 2019 without altering any already-committed row.
- `src/market_sim/config/constants.py`: `WEATHER_YEAR_POOL_BY_ISO["CAISO"]` and
  `["MISO"]` widened to `(2019, 2020, 2021, 2023, 2024, 2025)`;
  `["PJM"]` to `(2021, 2023, 2024, 2025)` (its demand source's own floor caps
  it at 2021 — see above).
- Tests: `tests/test_eia_loader.py` (CAISO/MISO/PJM cases added to
  `TestWeatherPoolWidening`), `tests/test_renewables.py`
  (`test_2026_07_06_balance_backfill_renewables_resolve_end_to_end`),
  `tests/test_ensemble.py` (`test_default_pool_is_per_iso` updated,
  `test_pjm_and_miso_default_pools` added).

No solves were run and nothing was registered on the backcast dashboard.
