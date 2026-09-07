"""Build per-zone SPP wind SHAPE profiles from MERRA-2 reanalysis wind speed.

SPP's wind fleet is the largest of any US ISO relative to its load, and it is
split almost exactly in half by the North/South seam: EIA-860 operable capacity
is 17.7 GW across 135 plants in **SPP-North** and 17.8 GW across 119 plants in
**SPP-South** (2025 vintage; the 35.5 GW total reconciles with SPP's own
published 35,934 MW of registered wind nameplate at end-2025,
``data/raw/spp-hsl/spp_wind_curtailment_annual.csv``). Those two halves sit in
*different wind regimes*: the northern High Plains (NE / KS / the Dakotas via
WAUE) and the southern Oklahoma / Texas-Panhandle fleet (OKGE / SPS / WFEC /
CSWS territory) sit at different distances from the core of the Great-Plains
nocturnal low-level jet, and they do NOT peak at the same hour.

**Measured, and worth stating because it runs the opposite way to the MISO
intuition:** the SOUTH is the nocturnal zone, not the north. This builder's own
night(00-06)/afternoon(12-18) ratios come out

    SPP-South   1.04 (2023)   1.06 (2024)   1.03 (2025)   -> overnight-weighted
    SPP-North   0.97 (2023)   0.96 (2024)   0.91 (2025)   -> afternoon-weighted

which is what the meteorology says once you look rather than assume: the LLJ's
climatological core sits over Oklahoma / Kansas / the Texas Panhandle, i.e. over
SPP-SOUTH, and weakens northward into Nebraska and the Dakotas. (In MISO the
north/south contrast points the other way because MISO-North *is* the upper
Plains and MISO-South is the Gulf.) Applying ONE EIA-930 SWPP-wide hourly wind
profile to both zones averages the two together, so the model holds wind in the
wrong zone at the wrong hour and the North<->South link binds at the wrong
times. This script builds a distinct hourly wind SHAPE for each of the two model
zones.

Method (forward-admissible per CLAUDE.md rule 13 ``[R-MEASURED]`` — a
reproducible physical input that regenerates for any year and responds to
changed conditions):

  1. Assign every EIA-860 operable SPP wind plant online by the target year to
     its model zone (the same ``zone_assignment`` geography as the fleet/solar
     path) and keep the largest plants by nameplate per zone as representative
     sample points (capacity-weighted).
  2. Pull MERRA-2 reanalysis 50 m wind speed (NASA POWER hourly ``WS50M``) at
     each sample point for the model's UTC clock.
  3. Extrapolate to the plant's EIA-860 turbine hub height with the standard
     1/7-power-law wind-shear profile, then run the speed through a generic
     IEC-class onshore turbine power curve to get an hourly capacity factor.
  4. Capacity-weight the sample-point CFs into one hourly SHAPE per zone, on the
     model's fixed non-leap 8760-hour clock (aligned hour-for-hour to the
     EIA-930 ``SWPP hourly`` series the dispatch reconciles against).

**Only the relative inter-zone shape is used downstream, and THE LEVEL IS NEVER
PINNED TO ACTUALS.** ``market_sim.data.renewables`` reconciles these shapes to
the measured SWPP-wide series so the capacity-weighted system total and annual
energy are preserved exactly (``_redistribute_preserving_total``). The absolute
CF level this script prints is a diagnostic only — nothing downstream reads it,
and no constant here is fitted to it.

SPP additionally publishes its OWN delivered wind at 5-minute resolution
(``data/raw/spp-genmix/GenMix_<year>.csv``, ``Wind Market`` + ``Wind Self``),
which is a stricter reconciliation target than the EIA-930 aggregate. The
``--reconcile`` flag scores the built shape against it — hourly correlation, the
diurnal profile and the seasonal profile — and PRINTS the result without
changing a single value in the parquet. That separation is the point: the
reconciliation is a *check on the shape*, never a channel through which the
measured series could set it (rule 1 ``[R-STRUCT]`` / rule 13 ``[R-MEASURED]``).

NASA POWER is queried in UTC and mapped onto the model clock via the very
``UTC time`` column the renewable loader uses (``_eia_hourly_frame_filled`` for
BA code ``SWPP``), so the shape lines up with ``cf_profile`` hour-for-hour with
no timezone guess.

Source:
    NASA POWER (Prediction Of Worldwide Energy Resources), hourly ``WS50M``
    (50 m wind speed) from the MERRA-2 reanalysis:
    https://power.larc.nasa.gov/api/temporal/hourly/point
    EIA-860 wind operable schedule (plant locations, hub heights).
    SPP Integrated Marketplace public generation mix (reconciliation target
    only): data/raw/spp-genmix/README.md.

Provenance note: this builder is a deliberate clone of
``scripts/data/build_miso_wind_shape.py`` (lane SPP-32's charter,
docs/multi-iso/spp-addition-plan-2026-09.md §5 row SPP-32). The physics
constants, the power curve and the parquet schema are identical by intent — a
different shear exponent or power curve for SPP would be an unmotivated
per-ISO degree of freedom (rule 21 ``[R-DOF]``). What is genuinely SPP's is the
zone geography, the SWPP clock, and the GenMix reconciliation leg. Folding the
two builders into one ISO-generic script is a consolidation routed to SPP-DESK
in ``docs/handoffs/FINDING-spp-32-2026-09-07.md`` — it would edit MISO's file,
which this lane does not own.

Run:
    python scripts/data/build_spp_wind_shape.py [--years 2023 2024 2025]
    python scripts/data/build_spp_wind_shape.py --reconcile
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import (  # noqa: E402
    RAW_DATA_DIR,
    active_eia860_dir,
    wind_shape_dir,
)
from market_sim.data.eia_loader import _eia_hourly_frame_filled  # noqa: E402
from market_sim.data.fleet import ISO_TO_BA_CODE  # noqa: E402
from market_sim.data.zone_assignment import build_zone_lookup  # noqa: E402

ISO = "SPP"
DEFAULT_YEARS = (2023, 2024, 2025)

# Hour-index column of the per-year wind-shape parquet (mirrors the
# ``_WIND_SHAPE_HOUR_COLUMN`` the renewable loader reads).
_WIND_SHAPE_HOUR_COLUMN = "hour"

# Representative wind sample points per zone: the largest plants by nameplate
# capacity. A handful of points captures the zone's spatial wind smoothing
# without an unbounded number of NASA POWER calls; the per-point CFs are
# capacity-weighted into the zone shape.
_SAMPLES_PER_ZONE: int = 6

# --- Wind-shear extrapolation (50 m reanalysis -> turbine hub height) --------
# Power-law profile v_h = v_ref * (h / h_ref) ** alpha. alpha = 1/7 (~0.143) is
# the standard neutral-stability onshore shear exponent (Hellmann / "1/7th power
# law", e.g. Manwell et al., "Wind Energy Explained"). Only the relative shape
# matters, so a single representative exponent is sufficient. Identical to the
# MISO/ERCOT builder by intent — see the module docstring's provenance note.
_SHEAR_EXPONENT: float = 1.0 / 7.0
_REANALYSIS_HEIGHT_M: float = 50.0  # NASA POWER WS50M reference height
_DEFAULT_HUB_HEIGHT_M: float = 90.0  # modern onshore hub when EIA-860 is blank
_FEET_TO_M: float = 0.3048

# --- Generic IEC-class onshore turbine power curve ---------------------------
# Piecewise standard model: zero below cut-in, cubic ramp from cut-in to rated
# (P ~ v^3 in the rising region), flat at rated to cut-out, zero above cut-out.
# Representative onshore values (IEC class II); only the shape is used.
_CUT_IN_MS: float = 3.0
_RATED_MS: float = 12.0
_CUT_OUT_MS: float = 25.0

_NASA_POWER_URL: str = "https://power.larc.nasa.gov/api/temporal/hourly/point"
_NASA_PARAMETER: str = "WS50M"
_REQUEST_TIMEOUT_S: int = 120
_MAX_RETRIES: int = 4

# --- SPP GenMix reconciliation leg (diagnostic only) -------------------------
# SPP's public Integrated Marketplace generation mix, 5-minute, UTC-stamped
# ("GMT MKT Interval"). Delivered wind is the SUM of the market-dispatched and
# self-scheduled columns — SPP splits every fuel that way and neither half alone
# is the fleet's output.
_GENMIX_DIR: Path = RAW_DATA_DIR / "spp-genmix"
_GENMIX_TIME_COLUMN: str = "GMT MKT Interval"
_GENMIX_WIND_COLUMNS: tuple[str, str] = ("Wind Market", "Wind Self")


def power_curve_cf(speed_ms: np.ndarray) -> np.ndarray:
    """Convert hub-height wind speed (m/s) to a turbine capacity factor in [0,1].

    Applies the generic piecewise IEC-class onshore power curve: zero below
    :data:`_CUT_IN_MS`, a cubic (``v**3``) ramp from cut-in to :data:`_RATED_MS`,
    rated output between rated and :data:`_CUT_OUT_MS`, and zero above cut-out.

    Args:
        speed_ms: Hub-height wind speed (m/s), any shape.

    Returns:
        Capacity factor in ``[0, 1]``, same shape as ``speed_ms``.
    """
    v = np.asarray(speed_ms, dtype=float)
    cf = np.zeros_like(v)
    ramp = (v >= _CUT_IN_MS) & (v < _RATED_MS)
    cf[ramp] = (v[ramp] ** 3 - _CUT_IN_MS**3) / (_RATED_MS**3 - _CUT_IN_MS**3)
    cf[(v >= _RATED_MS) & (v <= _CUT_OUT_MS)] = 1.0
    return np.clip(cf, 0.0, 1.0)


def hub_height_speed(speed_50m: np.ndarray, hub_height_m: float) -> np.ndarray:
    """Extrapolate 50 m reanalysis wind speed to a turbine hub height.

    Uses the 1/7-power-law shear profile (:data:`_SHEAR_EXPONENT`).

    Args:
        speed_50m: 50 m wind speed (m/s).
        hub_height_m: Turbine hub height (m).

    Returns:
        Estimated hub-height wind speed (m/s).
    """
    factor = (hub_height_m / _REANALYSIS_HEIGHT_M) ** _SHEAR_EXPONENT
    return np.asarray(speed_50m, dtype=float) * factor


def model_utc_index(year: int, iso: str = ISO) -> pd.DatetimeIndex | None:
    """Return the UTC timestamp of each model hour for ``year``.

    Reuses the renewable loader's clock (``_eia_hourly_frame_filled`` for the
    ISO's BA): row ``k`` of the returned index is the UTC time of model hour
    ``k`` on the fixed non-leap 8760-hour clock, so a wind shape keyed on these
    timestamps lines up hour-for-hour with the EIA-930 ``cf_profile``.

    Args:
        year: Model calibration year.
        iso: ISO whose EIA-930 hourly extract supplies the clock.

    Returns:
        ``DatetimeIndex`` of length ``HOURS_PER_YEAR``, or ``None`` when the
        ISO's hourly extract for the year is unavailable.
    """
    # The extract is keyed by EIA-930 BA code, not ISO name (SPP -> SWPP), so
    # resolve through the shared crosswalk rather than passing the ISO name.
    frame = _eia_hourly_frame_filled(ISO_TO_BA_CODE.get(iso.upper(), iso), year)
    if frame is None or "UTC time" not in frame.columns or len(frame) != HOURS_PER_YEAR:
        return None
    return pd.DatetimeIndex(pd.to_datetime(frame["UTC time"]))


def load_wind_sample_points(
    year: int, zone_names: list[str], iso: str = ISO
) -> dict[str, list[tuple[float, float, float, float]]]:
    """Return representative wind sample points per model zone.

    Reads the EIA-860 wind operable schedule, keeps plants online by ``year``,
    assigns each to a model zone, joins plant lat/lon, and returns the largest
    :data:`_SAMPLES_PER_ZONE` plants by nameplate per zone as
    ``(lat, lon, nameplate_mw, hub_height_m)`` tuples (capacity-weighted
    downstream). Hub height comes from EIA-860 ``Turbine Hub Height (Feet)``,
    falling back to :data:`_DEFAULT_HUB_HEIGHT_M` when blank.

    Args:
        year: Calibration year; only plants online by its end are kept.
        zone_names: Ordered model-zone names.
        iso: ISO whose zone lookup assigns each plant.

    Returns:
        ``{zone_name: [(lat, lon, cap_mw, hub_m), ...]}``.
    """
    eia_dir = active_eia860_dir()
    wind = pd.read_parquet(eia_dir / "eia860_wind_operable.parquet")
    wind = wind[wind["Status"].astype(str).str.strip().str.upper() == "OP"]
    op_year = pd.to_numeric(wind["Operating Year"], errors="coerce")
    wind = wind[~(op_year > year)].copy()

    plants = (
        pd.read_parquet(eia_dir / "eia860_plant.parquet")[
            ["Plant Code", "Latitude", "Longitude"]
        ]
        .drop_duplicates("Plant Code")
        .set_index("Plant Code")
    )
    wind["lat"] = pd.to_numeric(
        wind["Plant Code"].map(plants["Latitude"]), errors="coerce"
    )
    wind["lon"] = pd.to_numeric(
        wind["Plant Code"].map(plants["Longitude"]), errors="coerce"
    )
    wind["cap"] = pd.to_numeric(wind["Nameplate Capacity (MW)"], errors="coerce")
    hub_ft = pd.to_numeric(wind["Turbine Hub Height (Feet)"], errors="coerce")
    wind["hub_m"] = (hub_ft * _FEET_TO_M).fillna(_DEFAULT_HUB_HEIGHT_M)

    zone_lookup = build_zone_lookup(iso)
    wind["zone"] = wind["Plant Code"].map(lambda c: zone_lookup.get(int(c)))
    wind = wind.dropna(subset=["lat", "lon", "cap", "zone"])
    wind = wind[wind["cap"] > 0.0]

    out: dict[str, list[tuple[float, float, float, float]]] = {z: [] for z in zone_names}
    # Aggregate to one row per plant (sum generator nameplate; first coords/hub).
    by_plant = wind.groupby("Plant Code").agg(
        lat=("lat", "first"),
        lon=("lon", "first"),
        cap=("cap", "sum"),
        hub_m=("hub_m", "first"),
        zone=("zone", "first"),
    )
    for zone in zone_names:
        zp = by_plant[by_plant["zone"] == zone].nlargest(_SAMPLES_PER_ZONE, "cap")
        out[zone] = [
            (float(r.lat), float(r.lon), float(r.cap), float(r.hub_m))
            for r in zp.itertuples()
        ]
    return out


def fetch_nasa_power_ws50m(lat: float, lon: float, year: int) -> pd.Series:
    """Fetch hourly 50 m wind speed (m/s) at a point for the model's UTC year.

    Queries NASA POWER (MERRA-2) hourly ``WS50M`` in UTC over a window that
    covers the model's UTC clock for ``year`` (the local year straddles two UTC
    years), with bounded retries on transient HTTP errors.

    Args:
        lat: Latitude (deg N).
        lon: Longitude (deg E, negative for the western hemisphere).
        year: Model calibration year.

    Returns:
        A pandas Series indexed by UTC ``Timestamp`` of 50 m wind speed (m/s).

    Raises:
        RuntimeError: if the request fails after :data:`_MAX_RETRIES` attempts.
    """
    params = {
        "parameters": _NASA_PARAMETER,
        "community": "RE",
        "latitude": f"{lat:.4f}",
        "longitude": f"{lon:.4f}",
        "start": f"{year}0101",
        "end": f"{year + 1}0101",
        "format": "JSON",
        "time-standard": "UTC",
    }
    last_err: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = requests.get(
                _NASA_POWER_URL, params=params, timeout=_REQUEST_TIMEOUT_S
            )
            resp.raise_for_status()
            block = resp.json()["properties"]["parameter"][_NASA_PARAMETER]
            idx = pd.to_datetime(list(block.keys()), format="%Y%m%d%H")
            vals = np.array(list(block.values()), dtype=float)
            # NASA POWER fills no-data with -999; treat as missing.
            vals[vals <= -900.0] = np.nan
            return pd.Series(vals, index=idx).sort_index()
        except Exception as exc:  # noqa: BLE001 — bounded retry then re-raise
            last_err = exc
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"NASA POWER fetch failed for ({lat},{lon},{year}): {last_err}")


def build_zone_shape(
    samples: list[tuple[float, float, float, float]],
    utc_index: pd.DatetimeIndex,
    year: int,
) -> np.ndarray | None:
    """Return one zone's hourly wind CF SHAPE on the model clock, or ``None``.

    For each capacity-weighted sample point, fetches 50 m wind speed, lifts it
    to hub height, applies the turbine power curve, and reindexes onto the
    model's UTC hours; the per-point CFs are then capacity-weighted into the
    zone shape. Returns ``None`` when the zone has no sample points.

    Args:
        samples: ``(lat, lon, cap_mw, hub_m)`` representative points.
        utc_index: UTC timestamp per model hour (length ``HOURS_PER_YEAR``).
        year: Model calibration year.

    Returns:
        A ``(HOURS_PER_YEAR,)`` relative wind CF SHAPE, or ``None``.
    """
    if not samples:
        return None
    acc = np.zeros(HOURS_PER_YEAR, dtype=float)
    wsum = 0.0
    for lat, lon, cap, hub_m in samples:
        speed = fetch_nasa_power_ws50m(lat, lon, year)
        speed = speed.reindex(utc_index).interpolate().bfill().ffill()
        cf = power_curve_cf(hub_height_speed(speed.to_numpy(), hub_m))
        acc += cap * cf
        wsum += cap
    return acc / wsum if wsum > 0.0 else None


def build_year(year: int, zone_names: list[str], iso: str = ISO) -> pd.DataFrame | None:
    """Assemble the per-zone wind-shape frame for one year, or ``None``.

    Args:
        year: Model calibration year.
        zone_names: Ordered model-zone names.
        iso: ISO being built.

    Returns:
        Frame with an ``hour`` column and one relative-SHAPE column per zone,
        or ``None`` when the clock or the wind fleet is unavailable.
    """
    utc_index = model_utc_index(year, iso)
    if utc_index is None:
        print(f"SKIP {year}: no {iso} hourly UTC clock (EIA-930 extract missing).")
        return None
    points = load_wind_sample_points(year, zone_names, iso)
    data: dict[str, np.ndarray] = {
        _WIND_SHAPE_HOUR_COLUMN: np.arange(HOURS_PER_YEAR, dtype="int64")
    }
    empty_zones: list[str] = []
    for zone in zone_names:
        n_pts = len(points[zone])
        print(f"  {zone}: {n_pts} sample point(s)")
        shape = build_zone_shape(points[zone], utc_index, year)
        if shape is None:
            # A zone with no operable wind plants gets a placeholder shape: the
            # renewable loader weights each zone by its December wind capacity,
            # so a ~0-capacity zone's shape contributes nothing to the
            # reconciled aggregate. The placeholder (cross-zone mean, filled
            # after the populated zones) only keeps the column finite. Both SPP
            # zones carry ~17.7 GW, so this branch is not expected to fire for
            # SPP; it is kept so the builder degrades the same way MISO's does.
            empty_zones.append(zone)
            continue
        data[zone] = shape
    populated = [z for z in zone_names if z not in empty_zones]
    if not populated:
        print(f"SKIP {year}: no {iso} zone has operable wind plants.")
        return None
    mean_shape = np.mean([data[z] for z in populated], axis=0)
    for zone in empty_zones:
        data[zone] = mean_shape
    return pd.DataFrame(data)


def print_validation(
    year: int, df: pd.DataFrame, zone_names: list[str], iso: str = ISO
) -> None:
    """Print the mean CF and a coarse diurnal signature per zone.

    Args:
        year: Model calibration year.
        df: The per-zone wind-shape frame.
        zone_names: Ordered model-zone names.
        iso: ISO being built.
    """
    print(f"\n=== {iso} {year} per-zone wind SHAPE (relative CF) ===")
    hour_of_day = np.arange(HOURS_PER_YEAR) % 24
    for zone in zone_names:
        cf = df[zone].to_numpy()
        night = cf[(hour_of_day >= 0) & (hour_of_day < 6)].mean()
        afternoon = cf[(hour_of_day >= 12) & (hour_of_day < 18)].mean()
        print(
            f"  {zone:<13} mean={cf.mean():.3f}  "
            f"night(00-06)={night:.3f}  afternoon(12-18)={afternoon:.3f}  "
            f"night/aft={night / afternoon:.2f}"
        )


def load_genmix_wind_hourly(year: int, iso: str = ISO) -> np.ndarray | None:
    """Return SPP's own delivered wind (MW) on the model's 8760 clock, or ``None``.

    Reads ``data/raw/spp-genmix/GenMix_<year>.csv`` — SPP's public Integrated
    Marketplace generation mix at 5-minute resolution, UTC-stamped — sums the
    market-dispatched and self-scheduled wind columns
    (:data:`_GENMIX_WIND_COLUMNS`; neither half alone is the fleet's output),
    and averages the 5-minute intervals into the model's hourly UTC clock
    (:func:`model_utc_index`).

    This is the RECONCILIATION TARGET ONLY. Nothing in the built parquet is
    scaled, shifted or otherwise touched by it — see :func:`reconcile_year` and
    the module docstring.

    Args:
        year: Model calibration year.
        iso: ISO whose clock indexes the result.

    Returns:
        ``(HOURS_PER_YEAR,)`` delivered wind MW, or ``None`` when the GenMix
        file or the ISO clock is unavailable.
    """
    path = _GENMIX_DIR / f"GenMix_{year}.csv"
    if not path.exists():
        return None
    utc_index = model_utc_index(year, iso)
    if utc_index is None:
        return None
    raw = pd.read_csv(path)
    raw.columns = [str(c).strip() for c in raw.columns]
    missing = [c for c in (_GENMIX_TIME_COLUMN, *_GENMIX_WIND_COLUMNS) if c not in raw]
    if missing:
        print(f"  GenMix {year}: missing column(s) {missing}; reconciliation skipped.")
        return None
    ts = pd.to_datetime(raw[_GENMIX_TIME_COLUMN], utc=True, errors="coerce")
    wind = sum(
        pd.to_numeric(raw[c], errors="coerce").fillna(0.0) for c in _GENMIX_WIND_COLUMNS
    )
    frame = pd.DataFrame({"ts": ts.dt.tz_localize(None), "mw": wind}).dropna(
        subset=["ts"]
    )
    # 5-minute intervals -> hourly mean, then onto the model's UTC hours.
    hourly = frame.set_index("ts")["mw"].resample("1h").mean()
    return hourly.reindex(utc_index).to_numpy(dtype=float)


def reconcile_year(
    year: int, df: pd.DataFrame, zone_names: list[str], iso: str = ISO
) -> dict[str, float] | None:
    """Score the built SHAPE against SPP's own delivered wind, and print it.

    Builds the capacity-weighted ISO-wide shape implied by the per-zone shapes
    and compares it to the GenMix delivered series
    (:func:`load_genmix_wind_hourly`) on three axes that a *shape* — as opposed
    to a level — is answerable for:

    * **hourly correlation** over all covered hours;
    * **diurnal profile correlation** (24 hour-of-day means);
    * **seasonal profile correlation** (12 monthly means).

    Both series are normalised to unit mean before comparison, so the score is
    invariant to level by construction. THAT IS THE POINT: the level is never
    pinned (rule 13 ``[R-MEASURED]``), the renewable loader reconciles it
    downstream, and this function only reports whether the shape moves when
    SPP's own metered wind moves.

    A caveat this function states rather than hides: GenMix is *delivered*
    wind, i.e. net of the ~10%/yr SPP curtails
    (``data/raw/spp-hsl/spp_wind_curtailment_annual.csv``), while the built
    shape is an uncurtailed potential. Correlation is therefore the right
    statistic and a level ratio would not be.

    Args:
        year: Model calibration year.
        df: The per-zone wind-shape frame.
        zone_names: Ordered model-zone names.
        iso: ISO being reconciled.

    Returns:
        ``{"hourly_r": .., "diurnal_r": .., "seasonal_r": .., "hours": ..}``,
        or ``None`` when the GenMix series is unavailable.
    """
    measured = load_genmix_wind_hourly(year, iso)
    if measured is None:
        print(f"  GenMix {year}: not available; reconciliation skipped.")
        return None
    points = load_wind_sample_points(year, zone_names, iso)
    weights = np.array(
        [sum(p[2] for p in points[z]) for z in zone_names], dtype=float
    )
    if weights.sum() <= 0.0:
        return None
    modelled = (df[zone_names].to_numpy(dtype=float) * weights).sum(axis=1) / (
        weights.sum()
    )
    ok = np.isfinite(measured) & np.isfinite(modelled)
    if ok.sum() < 24 or measured[ok].sum() <= 0.0:
        return None
    a = modelled[ok] / modelled[ok].mean()
    b = measured[ok] / measured[ok].mean()
    hourly_r = float(np.corrcoef(a, b)[0, 1])

    hod = (np.arange(HOURS_PER_YEAR) % 24)[ok]
    diurnal_a = np.array([a[hod == h].mean() for h in range(24)])
    diurnal_b = np.array([b[hod == h].mean() for h in range(24)])
    diurnal_r = float(np.corrcoef(diurnal_a, diurnal_b)[0, 1])

    month = _month_of_hour()[ok]
    seas_a = np.array([a[month == m].mean() for m in range(12)])
    seas_b = np.array([b[month == m].mean() for m in range(12)])
    seasonal_r = float(np.corrcoef(seas_a, seas_b)[0, 1])

    print(
        f"\n=== {iso} {year} SHAPE vs SPP GenMix delivered wind "
        f"(level NOT pinned; unit-mean normalised) ==="
    )
    print(f"  hours compared      : {int(ok.sum())}")
    print(f"  hourly correlation  : {hourly_r:.4f}")
    print(f"  diurnal (24h) corr  : {diurnal_r:.4f}")
    print(f"  seasonal (12m) corr : {seasonal_r:.4f}")
    return {
        "hourly_r": hourly_r,
        "diurnal_r": diurnal_r,
        "seasonal_r": seasonal_r,
        "hours": float(ok.sum()),
    }


def _month_of_hour() -> np.ndarray:
    """Return the 0-based calendar month of each hour on the non-leap clock.

    Returns:
        ``(HOURS_PER_YEAR,)`` int array of month indices ``0..11``.
    """
    days = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
    return np.repeat(np.arange(12), days * 24)


def main() -> None:
    """Build every requested year's per-zone wind-shape parquet for an ISO."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, nargs="+", default=list(DEFAULT_YEARS))
    parser.add_argument(
        "--iso",
        default=ISO,
        help="ISO to build (default SPP). Must be registered in "
        "market_sim.config.paths.WIND_SHAPE_DIRS.",
    )
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="Also score each built shape against SPP's own GenMix delivered "
        "wind and print the result. Diagnostic only — it changes no value in "
        "the parquet.",
    )
    args = parser.parse_args()
    iso = args.iso.upper()

    out_dir = wind_shape_dir(iso)
    if out_dir is None:
        parser.error(
            f"{iso} has no wind-shape directory registered "
            f"(market_sim.config.paths.WIND_SHAPE_DIRS)"
        )
    zone_names = get_iso_config(iso).zone_names
    out_dir.mkdir(parents=True, exist_ok=True)
    for year in args.years:
        print(f"\nBuilding {iso} wind shape for {year}...")
        df = build_year(year, zone_names, iso)
        if df is None:
            continue
        print_validation(year, df, zone_names, iso)
        if args.reconcile:
            reconcile_year(year, df, zone_names, iso)
        table = pa.Table.from_pandas(df, preserve_index=False)
        table = table.replace_schema_metadata(
            {
                "source": (
                    "NASA POWER hourly WS50M (MERRA-2 reanalysis) at EIA-860 "
                    f"{iso} wind-plant locations, hub-height-extrapolated "
                    "through a generic IEC-class onshore turbine power curve"
                ),
                "description": (
                    "Per-zone relative hourly wind capacity-factor SHAPE for "
                    f"{iso}'s model zones on the fixed non-leap 8760-hour "
                    "clock. Used only for the inter-zone split; reconciled to "
                    f"the EIA-930 {iso}-wide series (level not pinned to actuals)."
                ),
                "year": str(year),
            }
        )
        out_file = out_dir / f"{iso.lower()}_{year}_wind_zone_shape.parquet"
        pq.write_table(table, out_file)
        print(
            f"Wrote {out_file.relative_to(REPO_ROOT)} "
            f"({out_file.stat().st_size / 1024:.1f} KiB)"
        )


if __name__ == "__main__":
    sys.exit(main())
