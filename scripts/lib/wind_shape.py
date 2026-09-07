"""ISO-agnostic per-zone wind SHAPE construction (the shared rule, expressed once).

Both per-ISO wind-shape builders — ``scripts/data/build_miso_wind_shape.py``
(which also serves ERCOT via ``--iso ERCOT``) and
``scripts/data/build_spp_wind_shape.py`` — are thin ISO wrappers around the
construction implemented
here: the reanalysis fetch, the shear extrapolation, the turbine power curve,
the per-zone fleet load and the assembly of one hourly capacity-factor series
per model zone on the model's fixed non-leap 8760-hour clock.

**This module contains no ISO name, no per-ISO constant and no ISO branch.**
Every ISO-specific quantity — the zone set, the plant set, the capacities, the
hub heights and the clock — is resolved from that ISO's own registry entry and
its own EIA-860 rows, so no ISO's number can reach another (CLAUDE.md rule 25
``[R-ISO-SCOPE]``). The physics constants are shared *by intent*: a different
shear exponent or power curve per ISO would be an unmotivated per-ISO degree of
freedom (rule 21 ``[R-DOF]``).

The level rule — R-LEVEL (SPP-48, owner ruling P17)
---------------------------------------------------
For model zone ``z`` and year ``Y``::

    SHAPE_z(t) = Σ_{i ∈ F_z(Y)} cap_i · cf_i(t) / Σ_{i ∈ F_z(Y)} cap_i

where ``F_z(Y)`` is **every** EIA-860 operable wind plant assigned to zone ``z``
and online by year ``Y``. ``SHAPE_z`` is therefore, by definition, the zone's
capacity-weighted fleet capacity factor.

**Why the whole fleet and not a sample.** The consumer
(``market_sim.data.renewables._redistribute_preserving_total``) splits the
measured system wind MW ``M(t)`` across zones in proportion to
``cap_z · ramp_z(t) · SHAPE_z(t)``. That share is invariant to a *common*
rescaling of all zones' shapes but **not** to a *per-zone* one, so what the
builder owes downstream is an estimator of each zone's true fleet capacity
factor **on one common absolute scale** — not a shape defined up to an
arbitrary per-zone constant. The former construction kept only the six largest
plants per zone, whose capacity-weighted mean carries a per-zone level bias
(a small and unequal share of each zone's capacity, sited on the zone's best
resource, and newer hence taller-hubbed) that is identified by nothing measured
— an undeclared per-zone free parameter multiplying the split (rules 21
``[R-DOF]`` / 24 ``[R-REGISTRY]``). Its sharpest symptom is that it is not
partition-consistent: ``top-6(A) ∪ top-6(B) ≠ top-6(A ∪ B)``, so re-cutting one
zone's boundary moved every *other* zone's weight at an identical system total
(measured: ``docs/handoffs/FINDING-spp-54-2026-09-07.md`` §4.2 C-4 — SPP-North
+1.38 / +1.47 / +1.91 TWh from a boundary change that touched only the south).

R-LEVEL removes that parameter rather than re-identifying it, and it is
**partition-consistent by construction**: with ``C_z = Σ_{i∈z} cap_i``, zones
``A`` and ``B`` partitioning an old zone ``C`` over the same plant set satisfy

    C_A·SHAPE_A(t) + C_B·SHAPE_B(t) = C_C·SHAPE_C(t)      (every hour, exactly)

so a boundary change can no longer move any other zone's redistribution weight.
Forward-admissibility (rule 13 ``[R-MEASURED]``) is strengthened, not weakened:
the rule regenerates for any year from the plant set at that year's information
vintage and responds to new siting, new hub heights and retirements — which the
six-site rule did only when the change happened to fall inside the six largest.

Source:
    NASA POWER (Prediction Of Worldwide Energy Resources), hourly ``WS50M``
    (50 m wind speed) from the MERRA-2 reanalysis:
    https://power.larc.nasa.gov/api/temporal/hourly/point
    EIA-860 wind operable schedule (plant locations, hub heights, nameplate).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.paths import CLEAN_DIR, active_eia860_dir  # noqa: E402
from market_sim.data.eia_loader import _eia_hourly_frame_filled  # noqa: E402
from market_sim.data.fleet import ISO_TO_BA_CODE  # noqa: E402
from market_sim.data.zone_assignment import build_zone_lookup  # noqa: E402

# Hour-index column of a per-year wind-shape parquet (mirrors the
# ``_WIND_SHAPE_HOUR_COLUMN`` the renewable loader reads).
WIND_SHAPE_HOUR_COLUMN: str = "hour"

# --- Wind-shear extrapolation (50 m reanalysis -> turbine hub height) --------
# Power-law profile v_h = v_ref * (h / h_ref) ** alpha. alpha = 1/7 (~0.143) is
# the standard neutral-stability onshore shear exponent (Hellmann / "1/7th power
# law", e.g. Manwell et al., "Wind Energy Explained").
SHEAR_EXPONENT: float = 1.0 / 7.0
REANALYSIS_HEIGHT_M: float = 50.0  # NASA POWER WS50M reference height
DEFAULT_HUB_HEIGHT_M: float = 90.0  # modern onshore hub when EIA-860 is blank
FEET_TO_M: float = 0.3048

# --- Generic IEC-class onshore turbine power curve ---------------------------
# Piecewise standard model: zero below cut-in, cubic ramp from cut-in to rated
# (P ~ v^3 in the rising region), flat at rated to cut-out, zero above cut-out.
# Representative onshore values (IEC class II).
CUT_IN_MS: float = 3.0
RATED_MS: float = 12.0
CUT_OUT_MS: float = 25.0

NASA_POWER_URL: str = "https://power.larc.nasa.gov/api/temporal/hourly/point"
NASA_PARAMETER: str = "WS50M"
REQUEST_TIMEOUT_S: int = 120
MAX_RETRIES: int = 4

# Memo for the reanalysis fetch. R-LEVEL queries every plant in the fleet
# rather than six per zone, so a rebuild is hundreds of point-years; the memo
# makes a re-run cheap. It lives under CLEAN_DIR, the repo's home for DERIVED,
# disposable, gitignored artifacts, and it is policy-free: a cold run and a warm
# run produce byte-identical output (asserted by test).
REANALYSIS_CACHE_DIR: Path = CLEAN_DIR / "wind-shape-reanalysis"


def power_curve_cf(speed_ms: np.ndarray) -> np.ndarray:
    """Convert hub-height wind speed (m/s) to a turbine capacity factor in [0,1].

    Applies the generic piecewise IEC-class onshore power curve: zero below
    :data:`CUT_IN_MS`, a cubic (``v**3``) ramp from cut-in to :data:`RATED_MS`,
    rated output between rated and :data:`CUT_OUT_MS`, and zero above cut-out.

    Args:
        speed_ms: Hub-height wind speed (m/s), any shape.

    Returns:
        Capacity factor in ``[0, 1]``, same shape as ``speed_ms``.
    """
    v = np.asarray(speed_ms, dtype=float)
    cf = np.zeros_like(v)
    ramp = (v >= CUT_IN_MS) & (v < RATED_MS)
    cf[ramp] = (v[ramp] ** 3 - CUT_IN_MS**3) / (RATED_MS**3 - CUT_IN_MS**3)
    cf[(v >= RATED_MS) & (v <= CUT_OUT_MS)] = 1.0
    return np.clip(cf, 0.0, 1.0)


def hub_height_speed(speed_50m: np.ndarray, hub_height_m: float) -> np.ndarray:
    """Extrapolate 50 m reanalysis wind speed to a turbine hub height.

    Uses the 1/7-power-law shear profile (:data:`SHEAR_EXPONENT`).

    Args:
        speed_50m: 50 m wind speed (m/s).
        hub_height_m: Turbine hub height (m).

    Returns:
        Estimated hub-height wind speed (m/s).
    """
    factor = (hub_height_m / REANALYSIS_HEIGHT_M) ** SHEAR_EXPONENT
    return np.asarray(speed_50m, dtype=float) * factor


def model_utc_index(year: int, iso: str) -> pd.DatetimeIndex | None:
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
    # The extract is keyed by EIA-930 BA code, not ISO name (SPP -> SWPP,
    # ERCOT -> ERCO, CAISO -> CISO), so resolve through the shared crosswalk
    # rather than passing the ISO name through.
    frame = _eia_hourly_frame_filled(ISO_TO_BA_CODE.get(iso.upper(), iso), year)
    if frame is None or "UTC time" not in frame.columns or len(frame) != HOURS_PER_YEAR:
        return None
    return pd.DatetimeIndex(pd.to_datetime(frame["UTC time"]))


def load_zone_wind_fleet(
    year: int, zone_names: list[str], iso: str
) -> dict[str, list[tuple[float, float, float, float]]]:
    """Return **every** operable wind plant of each model zone (R-LEVEL).

    Reads the EIA-860 wind operable schedule, keeps plants online by ``year``,
    assigns each to a model zone, joins plant lat/lon, aggregates generators to
    one row per plant, and returns ``(lat, lon, nameplate_mw, hub_height_m)``
    for **the whole zone's fleet** — no subsample and no size selection, which
    is what makes :func:`build_zone_shape` the zone's capacity-weighted fleet
    capacity factor and makes the construction partition-consistent (module
    docstring, R-LEVEL). Hub height comes from EIA-860 ``Turbine Hub Height
    (Feet)``, falling back to :data:`DEFAULT_HUB_HEIGHT_M` when blank.

    Args:
        year: Calibration year; only plants online by its end are kept.
        zone_names: Ordered model-zone names.
        iso: ISO whose zone lookup assigns each plant.

    Returns:
        ``{zone_name: [(lat, lon, cap_mw, hub_m), ...]}``, one entry per plant,
        ordered by descending nameplate so a log line reads sensibly.
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
    wind["hub_m"] = (hub_ft * FEET_TO_M).fillna(DEFAULT_HUB_HEIGHT_M)

    zone_lookup = build_zone_lookup(iso)
    wind["zone"] = wind["Plant Code"].map(lambda c: zone_lookup.get(int(c)))
    wind = wind.dropna(subset=["lat", "lon", "cap", "zone"])
    wind = wind[wind["cap"] > 0.0]

    # Aggregate to one row per plant (sum generator nameplate; first coords/hub).
    by_plant = wind.groupby("Plant Code").agg(
        lat=("lat", "first"),
        lon=("lon", "first"),
        cap=("cap", "sum"),
        hub_m=("hub_m", "first"),
        zone=("zone", "first"),
    )
    out: dict[str, list[tuple[float, float, float, float]]] = {
        z: [] for z in zone_names
    }
    for zone in zone_names:
        zp = by_plant[by_plant["zone"] == zone].sort_values("cap", ascending=False)
        out[zone] = [
            (float(r.lat), float(r.lon), float(r.cap), float(r.hub_m))
            for r in zp.itertuples()
        ]
    return out


def _cache_path(lat: float, lon: float, year: int, cache_dir: Path) -> Path:
    """Return the memo file for one reanalysis point-year.

    The key is the rounded coordinate pair and the year — exactly the arguments
    the NASA POWER request is built from (:func:`fetch_nasa_power_ws50m` sends
    ``{lat,lon:.4f}``), so two calls that would send an identical request share
    a memo entry and no two distinct requests can collide.

    Args:
        lat: Latitude (deg N).
        lon: Longitude (deg E, negative west).
        year: Model calibration year.
        cache_dir: Memo root.

    Returns:
        The parquet path for this point-year.
    """
    key = f"{lat:.4f}_{lon:.4f}_{year}"
    digest = hashlib.sha256(key.encode()).hexdigest()[:16]
    return cache_dir / str(year) / f"ws50m_{digest}.parquet"


def fetch_nasa_power_ws50m(
    lat: float, lon: float, year: int, cache_dir: Path | None = REANALYSIS_CACHE_DIR
) -> pd.Series:
    """Fetch hourly 50 m wind speed (m/s) at a point for the model's UTC year.

    Queries NASA POWER (MERRA-2) hourly ``WS50M`` in UTC over a window that
    covers the model's UTC clock for ``year`` (the local year straddles two UTC
    years), with bounded retries on transient HTTP errors. When ``cache_dir`` is
    given the series is memoised there (:data:`REANALYSIS_CACHE_DIR`); the memo
    changes no value, so a cold and a warm run agree exactly.

    Args:
        lat: Latitude (deg N).
        lon: Longitude (deg E, negative for the western hemisphere).
        year: Model calibration year.
        cache_dir: Memo root, or ``None`` to always hit the API.

    Returns:
        A pandas Series indexed by UTC ``Timestamp`` of 50 m wind speed (m/s).

    Raises:
        RuntimeError: if the request fails after :data:`MAX_RETRIES` attempts.
    """
    path = None
    if cache_dir is not None:
        path = _cache_path(lat, lon, year, Path(cache_dir))
        if path.exists():
            cached = pd.read_parquet(path)
            # Rebuild the index from the raw values, not from the named column,
            # so a warm read is indistinguishable from a cold one (P7).
            return pd.Series(
                cached["ws50m"].to_numpy(dtype=float),
                index=pd.DatetimeIndex(cached["utc"].to_numpy()),
            ).sort_index()

    params = {
        "parameters": NASA_PARAMETER,
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
            block = resp.json()["properties"]["parameter"][NASA_PARAMETER]
            idx = pd.to_datetime(list(block.keys()), format="%Y%m%d%H")
            vals = np.array(list(block.values()), dtype=float)
            # NASA POWER fills no-data with -999; treat as missing.
            vals[vals <= -900.0] = np.nan
            series = pd.Series(vals, index=idx).sort_index()
            if path is not None:
                path.parent.mkdir(parents=True, exist_ok=True)
                pd.DataFrame(
                    {"utc": series.index, "ws50m": series.to_numpy(dtype=float)}
                ).to_parquet(path, index=False)
            return series
        except Exception as exc:  # noqa: BLE001 — bounded retry then re-raise
            last_err = exc
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"NASA POWER fetch failed for ({lat},{lon},{year}): {last_err}")


def build_zone_shape(
    fleet: list[tuple[float, float, float, float]],
    utc_index: pd.DatetimeIndex,
    year: int,
    cache_dir: Path | None = REANALYSIS_CACHE_DIR,
) -> np.ndarray | None:
    """Return one zone's hourly wind CF on the model clock, or ``None``.

    Implements R-LEVEL over the zone's whole fleet: for each plant, fetches
    50 m wind speed, lifts it to that plant's hub height, applies the turbine
    power curve, reindexes onto the model's UTC hours, and capacity-weights the
    per-plant CFs. With ``fleet`` the zone's complete plant list (as
    :func:`load_zone_wind_fleet` returns it) the result *is* the zone's
    capacity-weighted fleet capacity factor.

    Args:
        fleet: ``(lat, lon, cap_mw, hub_m)`` for every plant in the zone.
        utc_index: UTC timestamp per model hour (length ``HOURS_PER_YEAR``).
        year: Model calibration year.
        cache_dir: Reanalysis memo root, or ``None`` to always hit the API.

    Returns:
        A ``(HOURS_PER_YEAR,)`` hourly capacity factor, or ``None`` when the
        zone has no operable wind plant.
    """
    if not fleet:
        return None
    acc = np.zeros(HOURS_PER_YEAR, dtype=float)
    wsum = 0.0
    for lat, lon, cap, hub_m in fleet:
        speed = fetch_nasa_power_ws50m(lat, lon, year, cache_dir=cache_dir)
        speed = speed.reindex(utc_index).interpolate().bfill().ffill()
        cf = power_curve_cf(hub_height_speed(speed.to_numpy(), hub_m))
        acc += cap * cf
        wsum += cap
    return acc / wsum if wsum > 0.0 else None


def build_year(
    year: int,
    zone_names: list[str],
    iso: str,
    cache_dir: Path | None = REANALYSIS_CACHE_DIR,
) -> pd.DataFrame | None:
    """Assemble the per-zone wind-shape frame for one year, or ``None``.

    Args:
        year: Model calibration year.
        zone_names: Ordered model-zone names.
        iso: ISO being built.
        cache_dir: Reanalysis memo root, or ``None`` to always hit the API.

    Returns:
        Frame with a :data:`WIND_SHAPE_HOUR_COLUMN` column and one hourly-CF
        column per zone, or ``None`` when the clock or the wind fleet is
        unavailable.
    """
    utc_index = model_utc_index(year, iso)
    if utc_index is None:
        print(f"SKIP {year}: no {iso} hourly UTC clock (EIA-930 extract missing).")
        return None
    fleets = load_zone_wind_fleet(year, zone_names, iso)
    data: dict[str, np.ndarray] = {
        WIND_SHAPE_HOUR_COLUMN: np.arange(HOURS_PER_YEAR, dtype="int64")
    }
    empty_zones: list[str] = []
    for zone in zone_names:
        fleet = fleets[zone]
        print(
            f"  {zone}: {len(fleet)} plant(s), "
            f"{sum(p[2] for p in fleet):,.1f} MW operable"
        )
        shape = build_zone_shape(fleet, utc_index, year, cache_dir=cache_dir)
        if shape is None:
            # A zone with no operable wind plants gets a placeholder shape: the
            # renewable loader weights each zone by its December wind capacity,
            # so a ~0-capacity zone's shape contributes nothing to the
            # reconciled aggregate. The placeholder (cross-zone mean, filled
            # after the populated zones) only keeps the column finite.
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
    year: int, df: pd.DataFrame, zone_names: list[str], iso: str
) -> None:
    """Print each zone's fleet capacity factor and a coarse diurnal signature.

    Under R-LEVEL the printed ``mean`` is the zone's capacity-weighted fleet
    capacity factor — a real measured quantity that the redistribution reads,
    not a free-floating diagnostic.

    Args:
        year: Model calibration year.
        df: The per-zone wind-shape frame.
        zone_names: Ordered model-zone names.
        iso: ISO being built.
    """
    print(
        f"\n=== {iso} {year} per-zone wind capacity factor (R-LEVEL, whole fleet) ==="
    )
    hour_of_day = np.arange(HOURS_PER_YEAR) % 24
    for zone in zone_names:
        cf = df[zone].to_numpy()
        night = cf[(hour_of_day >= 0) & (hour_of_day < 6)].mean()
        afternoon = cf[(hour_of_day >= 12) & (hour_of_day < 18)].mean()
        print(
            f"  {zone:<15} mean={cf.mean():.3f}  "
            f"night(00-06)={night:.3f}  afternoon(12-18)={afternoon:.3f}  "
            f"night/aft={night / afternoon:.2f}"
        )


def shape_table_metadata(iso: str, year: int) -> dict[str, str]:
    """Return the parquet schema metadata for one ISO-year's wind shape.

    Args:
        iso: ISO being built.
        year: Model calibration year.

    Returns:
        The ``{key: value}`` metadata block, JSON-safe strings throughout.
    """
    return {
        "source": (
            "NASA POWER hourly WS50M (MERRA-2 reanalysis) at the coordinates of "
            f"EVERY EIA-860 operable {iso} wind plant, hub-height-extrapolated "
            "through a generic IEC-class onshore turbine power curve"
        ),
        "description": (
            f"Per-zone hourly wind capacity factor for {iso}'s model zones on "
            "the fixed non-leap 8760-hour clock, each zone's series the "
            "capacity-weighted mean over its WHOLE operable fleet (R-LEVEL, "
            "owner ruling P17, 2026-09-07). Used for the inter-zone split; the "
            "system total is reconciled to the measured EIA-930 ISO-wide "
            "series, and no level is pinned to an actual."
        ),
        "level_rule": "R-LEVEL: capacity-weighted over every operable plant in the zone",
        "year": str(year),
        "shared_rule": json.dumps(
            {
                "module": "scripts/lib/wind_shape.py",
                "shear_exponent": SHEAR_EXPONENT,
                "reanalysis_height_m": REANALYSIS_HEIGHT_M,
                "cut_in_ms": CUT_IN_MS,
                "rated_ms": RATED_MS,
                "cut_out_ms": CUT_OUT_MS,
            }
        ),
    }
