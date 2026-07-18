"""Build per-zone MISO wind SHAPE profiles from MERRA-2 reanalysis wind speed.

MISO wind capacity spans regions with materially different wind regimes: the
upper-plains **North** (MN/ND/SD/IA) is dominated by the Great-Plains nocturnal
low-level jet — a pronounced overnight wind maximum and a strong winter peak —
while the lower-Midwest **Central** (WI/MI/IL/IN/KY) and the Entergy **South**
(AR/LA/MS/E.TX) have a flatter, more afternoon-weighted regime. The model used
ONE EIA-930 MISO-wide hourly wind profile for all three zones (scaled only by
EIA-860 capacity share), which is wrong for the inter-zone shape. This script
builds a distinct hourly wind SHAPE for each of the three model zones.

Method (forward-admissible per CLAUDE.md rule #11 — a reproducible physical
input that regenerates for any year and responds to changed conditions):

  1. Assign every EIA-860 operable MISO wind plant online by the target year to
     its model zone (the same zone_assignment geography as the fleet/solar
     path) and keep the largest plants by nameplate per zone as representative
     sample points (capacity-weighted).
  2. Pull MERRA-2 reanalysis 50 m wind speed (NASA POWER hourly ``WS50M``) at
     each sample point for the model's UTC clock.
  3. Extrapolate to the plant's EIA-860 turbine hub height with the standard
     1/7-power-law wind-shear profile, then run the speed through a generic
     IEC-class onshore turbine power curve to get an hourly capacity factor.
  4. Capacity-weight the sample-point CFs into one hourly SHAPE per zone, on the
     model's fixed non-leap 8760-hour clock (aligned hour-for-hour to the
     EIA-930 ``MISO hourly`` series the dispatch reconciles against).

Only the *relative inter-zone shape* is used downstream: market_sim.data.
renewables reconciles these shapes to the measured EIA-930 MISO-wide series so
the capacity-weighted system total and annual energy are preserved exactly
(see ``_redistribute_preserving_total``). The absolute CF level here is
irrelevant — this is a SHAPE, never a level pinned to actuals.

NASA POWER is queried in UTC and mapped onto the model clock via the very
``UTC time`` column the renewable loader uses (``_eia_hourly_frame_filled``),
so the shape lines up with ``cf_profile`` hour-for-hour with no timezone guess.

Source:
    NASA POWER (Prediction Of Worldwide Energy Resources), hourly ``WS50M``
    (10/50 m wind speed) from the MERRA-2 reanalysis:
    https://power.larc.nasa.gov/api/temporal/hourly/point
    EIA-860 wind operable schedule (plant locations, hub heights).

Run:
    python scripts/data/build_miso_wind_shape.py [--years 2023 2024 2025]
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
    MISO_WIND_SHAPE_DIR,
    active_eia860_dir,
)
from market_sim.data.eia_loader import _eia_hourly_frame_filled  # noqa: E402
from market_sim.data.zone_assignment import build_zone_lookup  # noqa: E402

ISO = "MISO"
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
# matters, so a single representative exponent is sufficient.
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


def model_utc_index(year: int) -> pd.DatetimeIndex | None:
    """Return the UTC timestamp of each model hour for ``year``.

    Reuses the renewable loader's clock (``_eia_hourly_frame_filled`` for the
    MISO BA): row ``k`` of the returned index is the UTC time of model hour
    ``k`` on the fixed non-leap 8760-hour clock, so a wind shape keyed on these
    timestamps lines up hour-for-hour with the EIA-930 MISO ``cf_profile``.

    Returns ``None`` when the MISO hourly extract for the year is unavailable.
    """
    frame = _eia_hourly_frame_filled(ISO, year)
    if frame is None or "UTC time" not in frame.columns or len(frame) != HOURS_PER_YEAR:
        return None
    return pd.DatetimeIndex(pd.to_datetime(frame["UTC time"]))


def load_wind_sample_points(
    year: int, zone_names: list[str]
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

    zone_lookup = build_zone_lookup(ISO)
    wind["zone"] = wind["Plant Code"].map(lambda c: zone_lookup.get(int(c)))
    wind = wind.dropna(subset=["lat", "lon", "cap", "zone"])
    wind = wind[wind["cap"] > 0.0]

    out: dict[str, list[tuple[float, float, float, float]]] = {
        z: [] for z in zone_names
    }
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


def build_year(year: int, zone_names: list[str]) -> pd.DataFrame | None:
    """Assemble the per-zone wind-shape frame for one year, or ``None``."""
    utc_index = model_utc_index(year)
    if utc_index is None:
        print(f"SKIP {year}: no MISO hourly UTC clock (EIA-930 extract missing).")
        return None
    points = load_wind_sample_points(year, zone_names)
    data: dict[str, np.ndarray] = {
        _WIND_SHAPE_HOUR_COLUMN: np.arange(HOURS_PER_YEAR, dtype="int64")
    }
    empty_zones: list[str] = []
    for zone in zone_names:
        n_pts = len(points[zone])
        print(f"  {zone}: {n_pts} sample point(s)")
        shape = build_zone_shape(points[zone], utc_index, year)
        if shape is None:
            # A zone with no operable wind plants (e.g. MISO-South / Entergy has
            # negligible wind) gets a placeholder shape: the renewable loader
            # weights each zone by its December wind capacity, so a ~0-capacity
            # zone's shape contributes nothing to the reconciled aggregate. The
            # placeholder (cross-zone mean, filled after the populated zones)
            # only keeps the column finite.
            empty_zones.append(zone)
            continue
        data[zone] = shape
    populated = [z for z in zone_names if z not in empty_zones]
    if not populated:
        print(f"SKIP {year}: no MISO zone has operable wind plants.")
        return None
    mean_shape = np.mean([data[z] for z in populated], axis=0)
    for zone in empty_zones:
        data[zone] = mean_shape
    return pd.DataFrame(data)


def print_validation(year: int, df: pd.DataFrame, zone_names: list[str]) -> None:
    """Print the mean CF and a coarse diurnal signature per zone."""
    print(f"\n=== MISO {year} per-zone wind SHAPE (relative CF) ===")
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


def main() -> None:
    """Build every requested year's MISO per-zone wind-shape parquet."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, nargs="+", default=list(DEFAULT_YEARS))
    args = parser.parse_args()

    zone_names = get_iso_config(ISO).zone_names
    MISO_WIND_SHAPE_DIR.mkdir(parents=True, exist_ok=True)
    for year in args.years:
        print(f"\nBuilding MISO wind shape for {year}...")
        df = build_year(year, zone_names)
        if df is None:
            continue
        print_validation(year, df, zone_names)
        table = pa.Table.from_pandas(df, preserve_index=False)
        table = table.replace_schema_metadata(
            {
                "source": (
                    "NASA POWER hourly WS50M (MERRA-2 reanalysis) at EIA-860 "
                    "MISO wind-plant locations, hub-height-extrapolated through "
                    "a generic IEC-class onshore turbine power curve"
                ),
                "description": (
                    "Per-zone relative hourly wind capacity-factor SHAPE for "
                    "MISO's three model zones on the fixed non-leap 8760-hour "
                    "clock. Used only for the inter-zone split; reconciled to "
                    "the EIA-930 MISO-wide series (level not pinned to actuals)."
                ),
                "year": str(year),
            }
        )
        out_file = MISO_WIND_SHAPE_DIR / f"{ISO.lower()}_{year}_wind_zone_shape.parquet"
        pq.write_table(table, out_file)
        print(
            f"Wrote {out_file.relative_to(REPO_ROOT)} "
            f"({out_file.stat().st_size / 1024:.1f} KiB)"
        )


if __name__ == "__main__":
    sys.exit(main())
