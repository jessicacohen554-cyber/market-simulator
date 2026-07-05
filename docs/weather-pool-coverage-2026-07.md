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
| CAISO | CISO | 2022-12-31 .. 2025-12-31 | no raw data | no raw data | no raw data | unchanged `(2023, 2024, 2025)` |
| PJM | PJM | 2021-12-31 .. 2026-06-30 | no raw data | no raw data | no full year (1 day) | unchanged `(2023, 2024, 2025)` |
| MISO | MISO | 2022-12-31 .. 2025-12-31 | no raw data | no raw data | no raw data | unchanged `(2023, 2024, 2025)` |

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

### CAISO / PJM / MISO — why they were skipped entirely

Their `<BA> hourly` extracts simply don't reach back that far on disk (see
table). Fetching more history requires `scripts/fetch_eia930_hourly.py`
against the EIA API v2, which is **blocked in this managed sandbox**
(`api.eia.gov` returns HTTP 403; the script's own docstring already says
"Run locally — the managed environment's allowlist blocks api.eia.gov"). No
`EIA_API_KEY` is configured in this environment either. This is a
run-it-locally-and-upload task, not something this session could complete —
documented here as the concrete next step rather than silently left undone.

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

No solves were run and nothing was registered on the backcast dashboard.
