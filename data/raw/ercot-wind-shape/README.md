# ercot-wind-shape — raw

`ercot_<year>_wind_zone_shape.parquet` (2023–2025) — per-zone hourly wind
shape for ERCOT, built from reanalysis wind speed + fleet siting.

**Source and full method: see `SOURCES.md` in this directory** — NASA
POWER hourly WS50M (50 m wind speed, MERRA-2 reanalysis,
`https://power.larc.nasa.gov/api/temporal/hourly/point`, keyless), combined
with EIA-860 wind-plant siting and EIA-930 `ERCO hourly` for reconciliation.
NASA POWER data is public domain (NASA open-data policy).

**Regeneration:** `python scripts/data/build_miso_wind_shape.py --iso ERCOT --years 2023 2024 2025`.

**Consumer:** `src/market_sim/data/renewables.py` (per-zone wind-shape loader).

> **Status: INERT as of ERCOT-112 (2026-07-25).** `renewables._WIND_ZONE_SHAPE_ISOS`
> is still `frozenset({"MISO"})`, so ERCOT continues to use one ISO-wide wind
> profile and the ERCOT keeper is byte-unchanged by the presence of these files.
> Arming ERCOT is a keeper-affecting change and belongs to its own gated probe
> (ercot-113). See `results/calibration/FINDING-ercot112-wind-prereqs-2026-07-25.md`.
