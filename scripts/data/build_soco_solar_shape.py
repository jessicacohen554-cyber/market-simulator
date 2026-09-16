#!/usr/bin/env python
"""Build per-zone SOCO solar shapes from MEASURED all-sky irradiance at each plant.

SOCO is the first registered region whose per-zone SOLAR split is load-bearing
and whose zones are separated mostly by LONGITUDE rather than latitude, and
that combination is exactly what the repo's existing solar-zone path cannot
represent. ``renewables._solar_zone_clearsky_shapes`` (CAISO) builds a
CLEAR-SKY plane-of-array series from each zone's latitude and EIA-860 tracking
mix, and its own docstring records that longitude and the equation of time are
**deliberately omitted** because "a constant timing offset shared by all zones
cancels". For CAISO's north-south stack that is true. For SOCO it is false by
construction: the three zones' capacity-weighted centroids sit at

    SOCO_MS -89.16 E   SOCO_AL -86.35 E   SOCO_GA -83.63 E     (2025 vintage)

— a **5.53 degree** east-west span, i.e. **22.1 minutes** of solar time between
Georgia and Mississippi, while their latitudes differ by 0.68 deg (a few minutes
of daylength). Applying one latitude-keyed clear-sky shape to all three would
put every zone's solar peak in the same model hour, which is the one thing the
geography says is wrong.

So this builder reads the resource instead of modelling it: hourly **all-sky**
direct-normal and diffuse irradiance from NASA POWER at **every** operable SOCO
solar plant's own coordinates, transposed onto each generator's own plane by
the same three tracking-class geometries the repo already uses, and
capacity-weighted into the three model zones. Landed 2026-09-16 by lane
**SOCO-32** (``docs/multi-iso/soco-addition-plan-2026-09.md`` §5 row SOCO-32;
FINDING ``docs/handoffs/FINDING-soco-32-2026-09-16.md``).

**SOLAR, not wind, and that is not an omission.** SOCO's EIA-860 operable fleet
carries **zero** wind generators and EIA-930's ``SOCO`` extract reports ``NG:
WND`` as null in every hour of 2023-2025, so there is no wind series to shape;
a wind-shape builder here would divide by zero. Solar is 5.8-6.0 GW and
8.4 / 10.1 / 10.0 TWh a year.

It costs FEWER free parameters than the clear-sky path, not more
--------------------------------------------------------------
Rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``: this construction **removes** two of
the physics constants ``_clearsky_poa_by_tech`` needs and adds none.

* the Meinel clear-sky beam attenuation (``_CLEARSKY_TRANSMITTANCE`` 0.7,
  ``_CLEARSKY_AM_EXPONENT`` 0.678) is replaced by the measured DNI;
* the parametric isotropic diffuse (``_DIFFUSE_FRACTION`` 0.10) is replaced by
  the measured diffuse series;
* the fixed-tilt array angle is the plant's **own filed** EIA-860 ``Tilt
  Angle`` / ``Azimuth Angle`` wherever EIA publishes one — which is **100 % of
  fixed-tilt nameplate MW in all three zones** — instead of the
  tilt-equals-latitude, due-south convention. That convention survives only as
  the fallback for a row EIA leaves blank.

What stays shared, deliberately, is the tracking-class **geometry**: the ideal
horizontal N-S single-axis identity ``cos(AOI) = sqrt(cos^2 z + cos^2 d *
sin^2 w)``, the dual-axis ``cos(AOI) = 1``, and the general tilted-surface
cosine — the same forms ``renewables._clearsky_poa_by_tech`` applies. A
different tracker convention for SOCO alone would be an unmotivated per-ISO
degree of freedom (rule 25 ``[R-ISO-SCOPE]``), and nothing about SOCO's
geography motivates one.

Two second-order effects are omitted, with the measurement that makes them
second-order stated rather than asserted:

* **inverter clipping** — the zones' capacity-weighted DC:AC ratios are
  1.367 (AL) / 1.382 (GA) / 1.401 (MS), a 2.5 % spread, so clipping flattens
  all three midday peaks by very nearly the same amount and the downstream
  reconciliation (``renewables._redistribute_preserving_total``) preserves the
  ISO aggregate exactly in every hour regardless;
* **the cell-temperature derate and the ground-reflected POA term** — both
  need a coefficient this builder would otherwise have to invent (a
  temperature coefficient, an albedo), and both are common-mode across three
  zones inside one climate at ~20 deg of tilt.

The construction, stated so it can be checked
---------------------------------------------
For each model zone ``z``, year ``y`` and model hour ``t``::

    shape_z(t) = SUM_g  MW_g * POA_g(t)  /  SUM_g MW_g          (g in zone z)

    POA_g(t)   = DNI_p(t) * max(0, cos AOI_g(t))
               + DIFF_p(t) * (1 + cos beta_g(t)) / 2

1. **Every operable solar generator, never a subsample.** The fleet is the
   EIA-860 solar operable schedule filtered to plants the ruled SOCO zone
   lookup (``zone_assignment.build_zone_lookup('SOCO')``, the FIPS-state
   partition of card S3) admits, online by the end of ``y``. Each generator
   carries its own tracking class and its own tilt; a plant with two
   differently-mounted generators contributes two rows.
2. **The irradiance is measured at the plant, in UTC.** NASA POWER hourly
   ``ALLSKY_SFC_SW_DNI`` and ``ALLSKY_SFC_SW_DIFF`` (MERRA-2 / CERES-assimilated
   all-sky) at the plant's EIA-860 coordinates. POWER stamps each value
   HOUR-BEGINNING in UTC; the model's clock (``wind_shape.model_utc_index``,
   the renewable loader's own ``UTC time`` column) is HOUR-ENDING, so each
   POWER hour ``H`` lands on model hour ``H + 1 h``. That +1 h is not assumed:
   ``--reconcile`` re-derives it by correlating the built footprint shape
   against the measured EIA-930 ``NG: SUN`` series over -3..+3 h and prints the
   peak, the same falsifiable alignment test SOCO-11 used for the load join.
3. **The sun position carries longitude and the equation of time** (NOAA Solar
   Calculator / Spencer 1971 Fourier series), evaluated at each hour's
   midpoint. This is the one place this builder is deliberately *more* precise
   than ``_clearsky_geometry``, and §"why" above is the reason.
4. **Nothing is pinned to an actual.** The shapes are RELATIVE: ``renewables``
   divides by the capacity-weighted mean and preserves the measured EIA-930
   ISO-wide series exactly in every hour, so this file can move WHICH ZONE
   holds the solar and can never move the ISO's solar energy (rule 13
   ``[R-MEASURED]``, rule 1 ``[R-STRUCT]``). ``--reconcile`` scores the built
   shape against EIA-930 and PRINTS the result without changing a value.

Why the region needs it at all (measured, and it is not marginal)
----------------------------------------------------------------
Energy-weighted mean hour-of-day of solar output on SOCO's Central clock, and
the tracking mix that drives the second effect (2025 vintage):

    SOCO_GA   81.3 % single-axis / 14.3 % fixed / 4.4 % dual   centroid -83.63 E
    SOCO_AL   69.7 % / 30.3 % / 0 %                            centroid -86.35 E
    SOCO_MS   84.2 % / 15.8 % / 0 %                            centroid -89.16 E

Georgia holds 83 % of the fleet and sits furthest east, so its output peaks
EARLIEST on the shared clock; Alabama carries twice Georgia's fixed-tilt share,
so its shape is the peakiest of the three. The measured per-year statistics
this builder prints are in the FINDING.

Source:
    NASA POWER (Prediction Of Worldwide Energy Resources), hourly
    ``ALLSKY_SFC_SW_DNI`` / ``ALLSKY_SFC_SW_DIFF`` / ``ALLSKY_SFC_SW_DWN``:
    https://power.larc.nasa.gov/api/temporal/hourly/point
    EIA-860 solar operable schedule (locations, tracking flags, tilt, azimuth).
    EIA-930 ``SOCO`` hourly ``NG: SUN`` (reconciliation target only).

Run:
    python scripts/data/build_soco_solar_shape.py [--years 2023 2024 2025]
    python scripts/data/build_soco_solar_shape.py --reconcile
    python scripts/data/build_soco_solar_shape.py --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import (  # noqa: E402
    CLEAN_DIR,
    RAW_DATA_DIR,
    active_eia860_dir,
)
from market_sim.data.eia_loader import _eia_hourly_frame_filled  # noqa: E402
from market_sim.data.zone_assignment import build_zone_lookup  # noqa: E402
from scripts.lib.wind_shape import model_utc_index  # noqa: E402

logger = logging.getLogger(__name__)

ISO = "SOCO"
DEFAULT_YEARS: tuple[int, ...] = (2023, 2024, 2025)
HOUR_COLUMN = "hour"

# Output directory and filename stem. The stem mirrors what
# ``renewables._wind_zone_reanalysis_shapes`` composes for wind
# (``<iso>_<year>_wind_zone_shape.parquet``) so the solar reader needs no new
# naming rule, and it matches the NWPP-33 solar pair already on disk.
SOLAR_SHAPE_DIR: Path = RAW_DATA_DIR / "soco-solar-shape"
FILE_STEM = "solar_zone_shape"

# --- NASA POWER ------------------------------------------------------------
NASA_POWER_URL: str = "https://power.larc.nasa.gov/api/temporal/hourly/point"
# Direct-normal and diffuse are what a plane-of-array transposition needs; GHI
# is pulled alongside at no extra request cost as the closure check
# (GHI ~= DNI*cos z + DIFF), which is how a bad coordinate or a corrupt block
# announces itself.
NASA_PARAMETERS: tuple[str, str, str] = (
    "ALLSKY_SFC_SW_DNI",
    "ALLSKY_SFC_SW_DIFF",
    "ALLSKY_SFC_SW_DWN",
)
REQUEST_TIMEOUT_S: int = 120
MAX_RETRIES: int = 4
# NASA POWER fills no-data with -999.
NODATA_FLOOR: float = -900.0

# Memo for the irradiance fetch, mirroring ``wind_shape.REANALYSIS_CACHE_DIR``:
# the whole fleet is queried (not a subsample), so a rebuild is hundreds of
# point-years and the memo makes a re-run cheap. It lives under CLEAN_DIR, the
# repo's home for DERIVED, disposable, gitignored artifacts, and it is
# policy-free — a cold run and a warm run produce byte-identical output.
IRRADIANCE_CACHE_DIR: Path = CLEAN_DIR / "solar-shape-irradiance"

# --- Geometry --------------------------------------------------------------
# EIA-860 solar tracking flags, in the precedence order
# ``renewables._SOLAR_TRACKING_FLAGS`` already uses: a generator is attributed
# to the first flag it sets.
TRACKING_FLAGS: tuple[tuple[str, str], ...] = (
    ("Single-Axis Tracking?", "single_axis"),
    ("Fixed Tilt?", "fixed"),
    ("Dual-Axis Tracking?", "dual_axis"),
)

# Fallback array geometry for a FIXED-TILT row EIA leaves blank. It is the
# convention ``renewables._clearsky_poa_by_tech`` already applies — array tilted
# at the site latitude, facing due south — reused rather than re-chosen (rule 21
# ``[R-DOF]``). Measured at this lane: EIA publishes a tilt for 100 % of
# fixed-tilt nameplate MW in every SOCO zone, so the fallback never fires on the
# committed fleet; it exists for a future vintage that files a blank.
FALLBACK_SURFACE_AZIMUTH_DEG: float = 180.0

# Below this cosine the sun is at or under the horizon and POA is zeroed. The
# same guard ``_clearsky_geometry`` applies, for the same reason (the
# transposition divides nothing here, but a grazing-incidence DNI term is
# numerically meaningless).
COS_ZENITH_FLOOR: float = 0.0


def solar_position(
    lat_deg: float, lon_deg: float, times_utc: pd.DatetimeIndex
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(cos_zenith, solar_azimuth_deg)`` at one point for each hour.

    Standard NOAA Solar Calculator formulation (Spencer 1971 Fourier series for
    the declination and the equation of time), evaluated at the INSTANT each
    stamp names — minutes and seconds included, so the function is exact for
    any grid. The builder passes hour-beginning stamps shifted by +30 minutes,
    which is the mid-hour convention ``renewables._clearsky_geometry`` uses;
    doing that shift at the call site rather than inside here is what keeps this
    function honest on a sub-hourly grid (a test walks a 1-minute grid and
    measures the east-west offset directly).

    Unlike ``_clearsky_geometry`` this one carries **longitude and the equation
    of time**, which is the whole reason this builder exists (module
    docstring): SOCO's zones are separated east-west, so a shared timing offset
    does not cancel between them.

    Args:
        lat_deg: Latitude, degrees north.
        lon_deg: Longitude, degrees east (negative west).
        times_utc: UTC stamps of the instants to evaluate.

    Returns:
        ``(cos_zenith, azimuth)`` arrays of ``len(times_utc)``; azimuth is
        degrees clockwise from true north. ``cos_zenith`` is negative when the
        sun is below the horizon (callers clip).
    """
    idx = pd.DatetimeIndex(times_utc)
    doy = idx.dayofyear.to_numpy(dtype=float)
    hour_utc = (
        idx.hour.to_numpy(dtype=float)
        + idx.minute.to_numpy(dtype=float) / 60.0
        + idx.second.to_numpy(dtype=float) / 3600.0
    )

    gamma = 2.0 * np.pi / 365.0 * (doy - 1.0 + (hour_utc - 12.0) / 24.0)
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * np.cos(gamma)
        - 0.032077 * np.sin(gamma)
        - 0.014615 * np.cos(2.0 * gamma)
        - 0.040849 * np.sin(2.0 * gamma)
    )
    decl = (
        0.006918
        - 0.399912 * np.cos(gamma)
        + 0.070257 * np.sin(gamma)
        - 0.006758 * np.cos(2.0 * gamma)
        + 0.000907 * np.sin(2.0 * gamma)
        - 0.002697 * np.cos(3.0 * gamma)
        + 0.001480 * np.sin(3.0 * gamma)
    )
    # True solar time (minutes) at the point, then the hour angle about noon.
    tst = np.mod(hour_utc * 60.0 + eqtime + 4.0 * lon_deg, 1440.0)
    hour_angle = np.deg2rad(tst / 4.0 - 180.0)

    phi = np.deg2rad(lat_deg)
    cos_zen = np.sin(phi) * np.sin(decl) + np.cos(phi) * np.cos(decl) * np.cos(
        hour_angle
    )
    cos_zen = np.clip(cos_zen, -1.0, 1.0)
    zen = np.arccos(cos_zen)
    sin_zen = np.sin(zen)
    # Azimuth from north, resolved by the sign of the hour angle (morning sun
    # east of north). The 1e-9 floor guards the exact-zenith singularity, which
    # never occurs at SOCO latitudes but would otherwise divide by zero.
    cos_az = (np.sin(decl) - np.sin(phi) * cos_zen) / (
        np.cos(phi) * np.maximum(sin_zen, 1.0e-9)
    )
    azimuth = np.rad2deg(np.arccos(np.clip(cos_az, -1.0, 1.0)))
    azimuth = np.where(hour_angle > 0.0, 360.0 - azimuth, azimuth)
    return cos_zen, azimuth


def plane_of_array(
    dni: np.ndarray,
    diffuse: np.ndarray,
    cos_zen: np.ndarray,
    sun_azimuth_deg: np.ndarray,
    tech: str,
    tilt_deg: float,
    surface_azimuth_deg: float,
) -> np.ndarray:
    """Transpose measured DNI/diffuse onto one generator's plane of array.

    The three tracking classes use the geometry
    :func:`~market_sim.data.renewables._clearsky_poa_by_tech` already applies —
    reused, not re-chosen (rule 21 ``[R-DOF]``) — with the clear-sky beam and
    the parametric diffuse swapped for the measured series:

    * ``fixed`` — a static tilted plane at ``tilt_deg`` facing
      ``surface_azimuth_deg``, the generator's own filed EIA-860 geometry;
    * ``single_axis`` — the ideal horizontal N-S tracker identity
      ``cos(AOI) = sqrt(cos^2 z + cos^2 d sin^2 w)``, evaluated here in its
      equivalent point form ``sqrt(cos^2 z + (sin z * sin(az - 180))^2)`` so it
      uses the same true sun position the rest of this module does. Its
      instantaneous plane tilt follows from ``cos(beta) = cos(z)/cos(AOI)``, so
      the tracker's sky-view factor is derived rather than assumed. No
      backtracking and no rotation limit, exactly as the shared model has it;
    * ``dual_axis`` — the plane is normal to the sun, ``cos(AOI) = 1``, and its
      tilt is the zenith angle.

    The diffuse term is the isotropic-sky transposition
    ``DIFF * (1 + cos beta) / 2`` (Liu & Jordan 1960). The ground-reflected
    term is omitted — it needs an albedo this builder would have to invent, and
    it is common-mode across three zones of one climate at ~20 deg of tilt.

    Args:
        dni: Hourly direct-normal irradiance (Wh/m^2).
        diffuse: Hourly diffuse horizontal irradiance (Wh/m^2).
        cos_zen: Cosine of the solar zenith angle.
        sun_azimuth_deg: Solar azimuth, degrees clockwise from north.
        tech: ``"single_axis"``, ``"fixed"`` or ``"dual_axis"``.
        tilt_deg: Fixed-tilt array tilt (ignored by the tracking classes).
        surface_azimuth_deg: Fixed-tilt array azimuth (ignored by the trackers).

    Returns:
        Hourly plane-of-array irradiance (Wh/m^2), zero when the sun is down.
    """
    sun_up = cos_zen > COS_ZENITH_FLOOR
    sin_zen = np.sqrt(np.maximum(1.0 - cos_zen**2, 0.0))

    if tech == "dual_axis":
        cos_aoi = np.ones_like(cos_zen)
        cos_tilt = cos_zen  # plane normal to the sun => tilt == zenith angle
    elif tech == "single_axis":
        # Horizontal N-S axis: the plane rotates about north-south, so only the
        # east-west component of the sun vector drives the rotation.
        east_west = sin_zen * np.sin(np.deg2rad(sun_azimuth_deg - 180.0))
        cos_aoi = np.sqrt(cos_zen**2 + east_west**2)
        cos_tilt = np.divide(
            cos_zen, cos_aoi, out=np.ones_like(cos_zen), where=cos_aoi > 1.0e-9
        )
    else:
        beta = np.deg2rad(tilt_deg)
        cos_aoi = cos_zen * np.cos(beta) + sin_zen * np.sin(beta) * np.cos(
            np.deg2rad(sun_azimuth_deg - surface_azimuth_deg)
        )
        cos_tilt = np.full_like(cos_zen, np.cos(beta))

    beam = np.asarray(dni, dtype=float) * np.maximum(cos_aoi, 0.0)
    sky = np.asarray(diffuse, dtype=float) * (1.0 + cos_tilt) / 2.0
    return np.where(sun_up, beam + sky, 0.0)


def _cache_path(lat: float, lon: float, year: int, cache_dir: Path) -> Path:
    """Return the memo file for one irradiance point-year.

    The key is the rounded coordinate pair and the year — exactly the arguments
    the NASA POWER request is built from — so two calls that would send an
    identical request share a memo entry and no two distinct requests collide.
    """
    digest = hashlib.sha256(f"{lat:.4f}_{lon:.4f}_{year}".encode()).hexdigest()[:16]
    return cache_dir / str(year) / f"irr_{digest}.parquet"


def fetch_nasa_power_irradiance(
    lat: float,
    lon: float,
    year: int,
    cache_dir: Path | None = IRRADIANCE_CACHE_DIR,
) -> pd.DataFrame:
    """Fetch hourly all-sky irradiance at a point over the model's UTC year.

    Queries NASA POWER in UTC over a window that covers the model's UTC clock
    for ``year`` (SOCO's local year straddles two UTC years), with bounded
    retries on transient HTTP errors. Memoised under ``cache_dir``; the memo
    changes no value, so a cold and a warm run agree exactly.

    Args:
        lat: Latitude, degrees north.
        lon: Longitude, degrees east (negative west).
        year: Model calibration year.
        cache_dir: Memo root, or ``None`` to always hit the API.

    Returns:
        A DataFrame indexed by hour-beginning UTC ``Timestamp`` with one column
        per entry of :data:`NASA_PARAMETERS`.

    Raises:
        RuntimeError: if the request fails after :data:`MAX_RETRIES` attempts.
    """
    path = None
    if cache_dir is not None:
        path = _cache_path(lat, lon, year, Path(cache_dir))
        if path.exists():
            cached = pd.read_parquet(path)
            out = cached[list(NASA_PARAMETERS)].astype(float)
            out.index = pd.DatetimeIndex(cached["utc"].to_numpy())
            return out.sort_index()

    params = {
        "parameters": ",".join(NASA_PARAMETERS),
        "community": "RE",
        "latitude": f"{lat:.4f}",
        "longitude": f"{lon:.4f}",
        "start": f"{year}0101",
        "end": f"{year + 1}0101",
        "format": "JSON",
        "time-standard": "UTC",
    }
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(
                NASA_POWER_URL, params=params, timeout=REQUEST_TIMEOUT_S
            )
            resp.raise_for_status()
            block = resp.json()["properties"]["parameter"]
            frame = None
            for name in NASA_PARAMETERS:
                series = block[name]
                idx = pd.to_datetime(list(series.keys()), format="%Y%m%d%H")
                vals = np.array(list(series.values()), dtype=float)
                vals[vals <= NODATA_FLOOR] = np.nan
                col = pd.DataFrame({name: vals}, index=idx)
                frame = col if frame is None else frame.join(col, how="outer")
            frame = frame.sort_index()
            if path is not None:
                path.parent.mkdir(parents=True, exist_ok=True)
                out = frame.copy()
                out.insert(0, "utc", out.index)
                out.to_parquet(path, index=False)
            return frame
        except Exception as exc:  # noqa: BLE001 — bounded retry then re-raise
            last_err = exc
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(
        f"NASA POWER irradiance fetch failed for ({lat},{lon},{year}): {last_err}"
    )


def load_zone_solar_fleet(year: int, zone_names: list[str]) -> pd.DataFrame:
    """Return **every** operable SOCO solar generator with its geometry.

    Reads the EIA-860 solar operable schedule, keeps generators whose plant the
    ruled SOCO zone lookup admits (``zone_assignment.build_zone_lookup``, the
    card-S3 FIPS-state partition; the one mis-filed Massachusetts plant 67241 is
    rejected there, audit §2.6(a)) and that are online by the end of ``year``,
    and joins the plant's EIA-860 coordinates.

    One row per GENERATOR, not per plant: a plant that mounts one array on
    trackers and another on fixed tilt contributes both, each with its own
    geometry. No subsample and no size threshold — the same R-LEVEL discipline
    ``wind_shape.load_zone_wind_fleet`` states, and what makes the result the
    zone's capacity-weighted fleet shape.

    Args:
        year: Calibration year; only generators online by its end are kept.
        zone_names: Ordered model-zone names.

    Returns:
        A DataFrame with columns ``zone``, ``plant``, ``lat``, ``lon``, ``mw``,
        ``tech``, ``tilt_deg``, ``surface_azimuth_deg``.
    """
    # The vintage-aware accessor, not the canonical constant: a vintage-seeded
    # solve redirects it, and the shape must be built off the same snapshot the
    # fleet is (paths.active_eia860_dir / set_eia860_vintage).
    eia860_dir = active_eia860_dir()
    solar = pd.read_parquet(eia860_dir / "eia860_solar_operable.parquet")
    plants = pd.read_parquet(eia860_dir / "eia860_plant.parquet")[
        ["Plant Code", "Latitude", "Longitude"]
    ]
    lookup = build_zone_lookup(ISO)

    df = solar[solar["Plant Code"].isin(lookup)].copy()
    df["zone"] = df["Plant Code"].map(lookup)
    df = df[df["zone"].isin(zone_names)]

    online_year = pd.to_numeric(df["Operating Year"], errors="coerce")
    df = df[online_year.notna() & (online_year <= year)]

    df = df.merge(plants, on="Plant Code", how="left")
    df["lat"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["lon"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df["mw"] = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce")
    df = df[df["lat"].notna() & df["lon"].notna() & (df["mw"] > 0.0)]

    tech = pd.Series("fixed", index=df.index, dtype=object)
    assigned = pd.Series(False, index=df.index)
    for column, name in TRACKING_FLAGS:
        flag = df[column].astype(str).str.strip().str.upper().str.startswith("Y")
        tech = tech.where(assigned | ~flag, name)
        assigned |= flag
    df["tech"] = tech
    # A row that sets no tracking flag at all is a filing gap, not a technology:
    # it takes the fleet's own dominant mounting rather than a silent default,
    # and says so.
    if (~assigned).any():
        unflagged_mw = float(df.loc[~assigned, "mw"].sum())
        logger.warning(
            "%s %d: %d generator(s) / %.1f MW set no EIA-860 tracking flag; "
            "treated as fixed tilt",
            ISO,
            year,
            int((~assigned).sum()),
            unflagged_mw,
        )

    tilt = pd.to_numeric(df["Tilt Angle"], errors="coerce")
    azimuth = pd.to_numeric(df["Azimuth Angle"], errors="coerce")
    df["tilt_deg"] = tilt.where(tilt.notna(), df["lat"])
    df["surface_azimuth_deg"] = azimuth.where(
        azimuth.notna(), FALLBACK_SURFACE_AZIMUTH_DEG
    )
    return df[
        [
            "zone",
            "Plant Code",
            "lat",
            "lon",
            "mw",
            "tech",
            "tilt_deg",
            "surface_azimuth_deg",
        ]
    ].rename(columns={"Plant Code": "plant"})


def zone_shape_frame(
    year: int, zone_names: list[str], cache_dir: Path | None = IRRADIANCE_CACHE_DIR
) -> pd.DataFrame | None:
    """Build one year's per-zone hourly solar SHAPE table.

    Args:
        year: Calibration year.
        zone_names: Ordered model-zone names.
        cache_dir: Irradiance memo root, or ``None`` to always hit the API.

    Returns:
        A DataFrame with ``hour`` plus one float column per zone (8760 rows,
        hour-sorted), or ``None`` when the model clock for ``year`` or the
        fleet is unavailable.
    """
    utc_index = model_utc_index(year, ISO)
    if utc_index is None:
        logger.warning("%s %d: model UTC clock unavailable", ISO, year)
        return None
    fleet = load_zone_solar_fleet(year, zone_names)
    if fleet.empty:
        logger.warning("%s %d: no operable solar generators", ISO, year)
        return None

    index = {zone: i for i, zone in enumerate(zone_names)}
    weighted = np.zeros((len(zone_names), HOURS_PER_YEAR), dtype=float)
    capacity = np.zeros(len(zone_names), dtype=float)
    # One fetch and one sun position per distinct coordinate pair; generators
    # at the same plant differ only in the transposition.
    for (lat, lon), site in fleet.groupby(["lat", "lon"], sort=False):
        irradiance = fetch_nasa_power_irradiance(
            float(lat), float(lon), year, cache_dir=cache_dir
        )
        # POWER stamps hour-BEGINNING and the model clock is hour-ENDING, so
        # the value covering model hour k is the one stamped one hour earlier
        # (module docstring item 2; --reconcile re-derives the shift).
        # POWER stamps open the hour; the representative instant is its
        # midpoint, the same mid-hour convention the clear-sky path uses.
        cos_zen, sun_az = solar_position(
            float(lat), float(lon), irradiance.index + pd.Timedelta(minutes=30)
        )
        for tech_key, rows in site.groupby(
            ["tech", "tilt_deg", "surface_azimuth_deg"], sort=False
        ):
            tech, tilt_deg, surface_azimuth_deg = tech_key
            poa = plane_of_array(
                irradiance[NASA_PARAMETERS[0]].to_numpy(dtype=float),
                irradiance[NASA_PARAMETERS[1]].to_numpy(dtype=float),
                cos_zen,
                sun_az,
                str(tech),
                float(tilt_deg),
                float(surface_azimuth_deg),
            )
            series = pd.Series(poa, index=irradiance.index + pd.Timedelta(hours=1))
            aligned = series.reindex(utc_index).to_numpy(dtype=float)
            aligned = np.nan_to_num(aligned, nan=0.0, posinf=0.0, neginf=0.0)
            mw = float(rows["mw"].sum())
            zone = str(rows["zone"].iloc[0])
            weighted[index[zone]] += mw * aligned
            capacity[index[zone]] += mw

    live = capacity > 0.0
    if not live.any():
        logger.warning("%s %d: no zone carries solar capacity", ISO, year)
        return None
    shapes = np.zeros_like(weighted)
    shapes[live] = weighted[live] / capacity[live, None]

    out = pd.DataFrame({HOUR_COLUMN: np.arange(HOURS_PER_YEAR, dtype=np.int64)})
    for zone in zone_names:
        out[zone] = shapes[index[zone]]
    return out


def reconcile(year: int, shapes: pd.DataFrame, zone_names: list[str]) -> None:
    """Score the built shape against EIA-930 ``NG: SUN`` and PRINT the result.

    A CHECK, never a channel: no value in the parquet depends on anything this
    function reads (rule 1 ``[R-STRUCT]`` / rule 13 ``[R-MEASURED]``). It
    reports (a) the shift at which the footprint shape best correlates with the
    measured series — which is how the hour-beginning/hour-ending alignment is
    verified rather than assumed — and (b) the correlation and the
    energy-weighted mean hour-of-day on each side.

    Args:
        year: Calibration year.
        shapes: The built per-zone shape table.
        zone_names: Ordered model-zone names.
    """
    frame = _eia_hourly_frame_filled(ISO, year)
    if frame is None or "NG: SUN" not in frame.columns:
        print(f"  {year}: no EIA-930 NG: SUN series to reconcile against")
        return
    measured = np.nan_to_num(frame["NG: SUN"].to_numpy(dtype=float), nan=0.0)
    fleet = load_zone_solar_fleet(year, zone_names)
    weights = fleet.groupby("zone")["mw"].sum()
    footprint = sum(
        shapes[z].to_numpy(dtype=float) * float(weights.get(z, 0.0)) for z in zone_names
    )
    best = None
    for shift in range(-3, 4):
        rolled = np.roll(footprint, shift)
        r = float(np.corrcoef(rolled, measured)[0, 1])
        if best is None or r > best[1]:
            best = (shift, r)
        print(f"    shift {shift:+d} h: pearson r = {r:.4f}")
    hod = np.arange(HOURS_PER_YEAR) % 24
    built_hod = float((footprint * hod).sum() / footprint.sum())
    meas_hod = float((measured * hod).sum() / measured.sum())
    print(
        f"  {year}: best shift {best[0]:+d} h (r = {best[1]:.4f}); "
        f"energy-weighted mean hour-of-day built {built_hod:.2f} "
        f"vs measured {meas_hod:.2f}"
    )
    for zone in zone_names:
        series = shapes[zone].to_numpy(dtype=float)
        if series.sum() <= 0.0:
            continue
        print(
            f"      {zone}: mean CF-equivalent {series.mean():.1f} Wh/m2, "
            f"energy-weighted hour-of-day {(series * hod).sum() / series.sum():.2f}"
        )


def main(argv: list[str] | None = None) -> None:
    """Build (or report on) SOCO per-zone solar shape parquets."""
    parser = argparse.ArgumentParser(
        description="Build per-zone SOCO solar shapes from NASA POWER all-sky "
        "irradiance at each EIA-860 solar plant."
    )
    parser.add_argument(
        "--years", type=int, nargs="+", default=list(DEFAULT_YEARS), help="Years."
    )
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="Score the built shape against EIA-930 NG: SUN and print the result "
        "(changes no value).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and report without writing the parquet.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the irradiance memo and always hit NASA POWER.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    zone_names = get_iso_config(ISO).zone_names
    cache_dir = None if args.no_cache else IRRADIANCE_CACHE_DIR

    for year in args.years:
        shapes = zone_shape_frame(year, zone_names, cache_dir=cache_dir)
        if shapes is None:
            print(f"  {year}: skipped")
            continue
        fleet = load_zone_solar_fleet(year, zone_names)
        by_zone = fleet.groupby("zone").agg(n=("mw", "size"), mw=("mw", "sum"))
        print(
            f"  {year}: {len(fleet)} generator(s), "
            + ", ".join(
                f"{z} {by_zone.loc[z, 'mw']:.1f} MW / {int(by_zone.loc[z, 'n'])} gen"
                for z in zone_names
                if z in by_zone.index
            )
        )
        if args.reconcile:
            reconcile(year, shapes, zone_names)
        if args.dry_run:
            continue
        SOLAR_SHAPE_DIR.mkdir(parents=True, exist_ok=True)
        path = SOLAR_SHAPE_DIR / f"{ISO.lower()}_{year}_{FILE_STEM}.parquet"
        shapes.to_parquet(path, index=False)
        print(f"    wrote {path} ({len(shapes):,} rows)")


if __name__ == "__main__":
    main()
