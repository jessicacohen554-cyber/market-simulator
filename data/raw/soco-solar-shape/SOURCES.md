# soco-solar-shape — SOURCES

Landed 2026-09-16 by lane **SOCO-32**. Every input below is public and keyless;
no credential was used and none is needed to regenerate.

## 1. NASA POWER hourly all-sky irradiance — the resource

| Field | Value |
|---|---|
| Endpoint | `https://power.larc.nasa.gov/api/temporal/hourly/point` |
| Parameters | `ALLSKY_SFC_SW_DNI` (direct normal), `ALLSKY_SFC_SW_DIFF` (diffuse horizontal), `ALLSKY_SFC_SW_DWN` (global horizontal, carried as a closure check) |
| Units | Wh/m² per hour |
| Community | `RE` |
| Time standard | `UTC`, stamped **hour-beginning** |
| Auth | none (keyless) |
| Licence | Public domain (NASA open-data policy) |
| Reached | 2026-09-16, HTTP 200; **482 point-years** fetched, one request each — 154 (2023) / 163 (2024) / 165 (2025) distinct plant coordinates, the fleet growing with vintage |

Queried once per (plant coordinate, year) over `start=<Y>0101` …
`end=<Y+1>0101`, a window that covers the model's UTC clock for the local year,
and memoised under `data/clean/solar-shape-irradiance/` (DERIVED, disposable,
gitignored — a cold run and a warm run produce byte-identical output).

`ALLSKY_*` is the **all-sky** family, i.e. it carries the actual cloud field,
which is half of why this beats a clear-sky model for a footprint whose zones
sit in different weather (`README.md`).

## 2. EIA-860 solar operable schedule — the fleet and its array geometry

Read from the active EIA-860 vintage
(`market_sim.config.paths.active_eia860_dir()`) — already committed, not
re-fetched by this lane:

| Field | Column | Used for |
|---|---|---|
| location | `eia860_plant.parquet` `Latitude` / `Longitude` | the NASA POWER query point and the sun position |
| capacity | `Nameplate Capacity (MW)` | the per-zone capacity weighting |
| vintage | `Operating Year` | only generators online by the end of the target year are included |
| mounting | `Single-Axis Tracking?` / `Fixed Tilt?` / `Dual-Axis Tracking?` | the tracking class, first flag set (the precedence `renewables._SOLAR_TRACKING_FLAGS` already uses) |
| array angle | `Tilt Angle`, `Azimuth Angle` | the fixed-tilt transposition, **as filed** |

Plants are assigned to a model zone by
`market_sim.data.zone_assignment.build_zone_lookup("SOCO")` — the card-S3
FIPS-state partition, the same geography the fleet, load and gas paths use, so a
plant cannot land in one zone here and another there. The one mis-filed
Massachusetts plant (67241) is rejected there, not here
(`docs/multi-iso/soco-data-audit.md` §2.6(a)).

**Measured coverage of the filed array geometry, 2025 vintage:** EIA publishes a
`Tilt Angle` for **100 % of fixed-tilt nameplate MW in all three zones**
(AL 212.5 MW / 6 rows, GA 747.2 MW / 50 rows, MS 50.0 MW / 1 row; median tilt
20.0° everywhere, mean azimuth 180–202°). The
tilt-equals-latitude / due-south fallback the builder carries therefore **never
fires on the committed fleet**; it exists only for a future vintage that files a
blank.

## 3. EIA-930 `SOCO` hourly — the clock, and the reconciliation target

* **Clock.** `scripts/lib/wind_shape.model_utc_index(year, "SOCO")` → the
  renewable loader's own `UTC time` column
  (`eia_loader._eia_hourly_frame_filled`), so model hour *k* here is model hour
  *k* everywhere else. SOCO's extract is on **Central** time, hour-**ending**
  (`docs/multi-iso/soco-data-audit.md` §3.4, gate G19); NASA POWER is
  hour-**beginning** UTC, so the builder lands POWER hour *H* on model hour
  *H* + 1 h. That offset is **verified, not assumed** — see `README.md`'s
  reconciliation table, where the correlation peaks sharply at shift **+0 h** in
  all three years.
* **Target.** The `NG: SUN` column, used by `--reconcile` **only**: it scores
  the built shape and prints the score. No value in the parquet depends on it
  (rule 1 `[R-STRUCT]` / rule 13 `[R-MEASURED]`). The downstream consumer
  reconciles the *level* to this same series through
  `renewables._redistribute_preserving_total`, which preserves the ISO-wide
  total exactly in every hour — the level is never set here.

## 4. Method, in one place

`scripts/data/build_soco_solar_shape.py`'s module docstring is the method of
record: the POA formula, the three tracking-class geometries (reused from
`renewables._clearsky_poa_by_tech` rather than re-chosen), the NOAA / Spencer
sun-position series, and the two second-order effects deliberately omitted with
the measurement that makes them second-order.

Free parameters introduced by this dataset: **none**. The construction removes
three constants the clear-sky path needs (`_CLEARSKY_TRANSMITTANCE`,
`_CLEARSKY_AM_EXPONENT`, `_DIFFUSE_FRACTION`) by measuring what they estimate,
and takes the array angles from the filing rather than from a convention.
