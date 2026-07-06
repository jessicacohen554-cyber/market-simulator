# miso-wind-shape — raw

`miso_<year>_wind_zone_shape.parquet` (2023–2025) — per-zone hourly wind
shape for MISO, built from reanalysis wind speed + fleet siting.

**Source and full method: see `SOURCES.md` in this directory** — NASA
POWER hourly WS50M (50 m wind speed, MERRA-2 reanalysis,
`https://power.larc.nasa.gov/api/temporal/hourly/point`, keyless), combined
with EIA-860 wind-plant siting and EIA-930 MISO generation for
reconciliation. NASA POWER data is public domain (NASA open-data policy).

**Regeneration:** `python scripts/build_miso_wind_shape.py --years 2023 2024 2025`.

**Consumer:** `src/market_sim/data/renewables.py` (MISO wind-shape loader).
