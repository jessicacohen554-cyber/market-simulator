# ERCOT per-zone wind SHAPE — sources

Per-zone relative hourly wind capacity-factor SHAPE for ERCOT's seven model
zones, one parquet per backcast year: `ercot_<year>_wind_zone_shape.parquet`.
Columns: `hour` (0..8759) + one relative-CF column per model zone, on the fixed
non-leap 8760-hour clock.

## Why ERCOT needs one

ERCOT's wind fleet spans two materially different wind regimes that peak at
**different hours of the day**:

* the **West / Panhandle** CREZ corridor rides the Great-Plains nocturnal
  low-level jet — an overnight maximum; and
* the **South / Coastal** fleet rides the Gulf **sea breeze** — an afternoon
  maximum.

Measured night(00–06)/afternoon(12–18) ratio from this dataset:

| zone | 2023 | 2024 | 2025 |
|---|---|---|---|
| West | 1.16 | 1.15 | 1.13 |
| North | 1.17 | 1.14 | 1.08 |
| Panhandle | 1.04 | 1.13 | 1.06 |
| Houston | 1.01 | 0.95 | 1.00 |
| South | **0.89** | **0.84** | **0.84** |

The model currently applies ONE EIA-930 ERCOT-wide hourly wind profile to every
zone (scaled only by EIA-860 capacity share), which averages a night-peaking
corridor and an afternoon-peaking coast into a single shape.

## Source (forward-admissible per CLAUDE.md #11)

- **NASA POWER**, hourly `WS50M` (50 m wind speed), MERRA-2 reanalysis:
  `https://power.larc.nasa.gov/api/temporal/hourly/point` (keyless).
  A reanalysis wind field regenerates for any year and responds to changed
  conditions, so it is a reproducible physical input, not an outcome pinned to
  actuals. It enters only as a relative SHAPE.
- **EIA-860** wind operable schedule — plant locations (zone assignment) and
  turbine hub heights (shear extrapolation).
- **EIA-930** `ERCO hourly` extract — supplies the UTC clock the shape is
  aligned to and the ISO-wide aggregate the shape is reconciled against. (The
  extract is keyed by BA code, `ERCOT -> ERCO`, via `fleet.ISO_TO_BA_CODE`.)

## Method

1. Assign EIA-860 operable ERCOT wind plants online by the target year to model
   zones (`zone_assignment` geography); keep the 6 largest by nameplate per
   zone as capacity-weighted sample points. Plant counts by zone: West 89,
   South 44, North 40, Panhandle 33, Houston 2, South_Central 2. **Northeast
   has no operable wind** and takes the documented placeholder (cross-zone
   mean), weighted by ~0 capacity downstream; South_Central resolved 0 sample
   points in 2023–2024 and 2 in 2025.
2. Fetch hourly `WS50M` at each point; lift to the plant's hub height with the
   1/7-power-law shear; run through a generic IEC-class onshore turbine power
   curve (cut-in 3, rated 12, cut-out 25 m/s).
3. Capacity-weight per-point CFs into one zone SHAPE on the model clock.

Only the *inter-zone* shape is used; `market_sim.data.renewables` reconciles it
to the EIA-930 ERCOT-wide series via `_redistribute_preserving_total`, which
preserves the capacity-weighted system total **exactly, every hour**. Annual
wind energy and the ISO-wide series are therefore unchanged by construction —
this dataset can only move *which zone* holds the wind in a given hour.

## Reproduce

```bash
python scripts/data/build_miso_wind_shape.py --iso ERCOT --years 2023 2024 2025
```
