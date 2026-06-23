# MISO per-zone wind SHAPE — sources

Per-zone relative hourly wind capacity-factor SHAPE for MISO's three model
zones (North / Central / South), one parquet per backcast year:
`miso_<year>_wind_zone_shape.parquet`. Columns: `hour` (0..8759) + one
relative-CF column per model zone, on the fixed non-leap 8760-hour clock.

## Source (forward-admissible per CLAUDE.md #11)

- **NASA POWER**, hourly `WS50M` (50 m wind speed), MERRA-2 reanalysis:
  `https://power.larc.nasa.gov/api/temporal/hourly/point` (keyless).
  A reanalysis wind field regenerates for any year and responds to changed
  conditions, so it is a reproducible physical input, not an outcome pinned to
  actuals. It enters only as a relative SHAPE.
- **EIA-860** wind operable schedule — plant locations (zone assignment) and
  turbine hub heights (shear extrapolation).
- **EIA-930** `MISO hourly` extract — supplies the UTC clock the shape is
  aligned to and the ISO-wide aggregate the shape is reconciled against.

## Method

1. Assign EIA-860 operable MISO wind plants online by the target year to model
   zones (`zone_assignment` geography); keep the 6 largest by nameplate per
   zone as capacity-weighted sample points. MISO-South has ~0 operable wind, so
   its shape is a placeholder (cross-zone mean) weighted by ~0 capacity
   downstream.
2. Fetch hourly `WS50M` at each point; lift to the plant's hub height with the
   1/7-power-law shear; run through a generic IEC-class onshore turbine power
   curve (cut-in 3, rated 12, cut-out 25 m/s).
3. Capacity-weight per-point CFs into one zone SHAPE on the model clock.

Only the *inter-zone* shape is used; `market_sim.data.renewables` reconciles it
to the EIA-930 MISO-wide series (system total and annual energy preserved).

## Reproduce

```bash
.venv/bin/python scripts/build_miso_wind_shape.py --years 2023 2024 2025
```
