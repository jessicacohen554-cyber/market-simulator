# miso-wind-shape — raw

`miso_<year>_wind_zone_shape.parquet` (2018–2025) — per-zone hourly wind
shape for MISO, built from reanalysis wind speed + fleet siting.

**Source and full method: see `SOURCES.md` in this directory** — NASA
POWER hourly WS50M (50 m wind speed, MERRA-2 reanalysis,
`https://power.larc.nasa.gov/api/temporal/hourly/point`, keyless), combined
with EIA-860 wind-plant siting and EIA-930 MISO generation for
reconciliation. NASA POWER data is public domain (NASA open-data policy).

**Regeneration:** `python scripts/data/build_miso_wind_shape.py --years 2023 2024 2025`.
2018–2022 were built 2026-07-31 under the rule-22 holdout DATA-INTAKE channel
(owner-authorized, `frontend/data/backcast/calibration-complete.json` `intake_log`;
no solve, no score — MISO holds no marker). **2026 is not buildable**: the shape is
placed on the model's full-8760 UTC clock via `eia_loader._eia_hourly_frame_filled`,
which returns `None` for a half year (H1-2026 is 4,344 h) — rebuild once the 2026
EIA-930 extract completes.

**Consumer:** `src/market_sim/data/renewables.py` (MISO wind-shape loader).
