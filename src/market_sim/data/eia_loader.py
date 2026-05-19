"""Loaders for EIA-930 hourly demand and generation series.

Reads the EIA-930 parquet extracts shipped under ``inputs/raw-data/eia-930``
and shapes them for the dispatch model: hourly ISO demand is allocated to
zones by each zone's load share, and generation profiles are returned as
normalized per-fuel distributions.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import ISOConfig, get_iso_config

# Default location of the EIA-930 parquet extracts, resolved relative to the
# repository root (this file lives at src/market_sim/data/eia_loader.py).
DATA_DIR: Path = Path(__file__).parents[3] / "inputs" / "raw-data" / "eia-930"

_DEMAND_PROFILES_FILE = "eia_demand_profiles.parquet"
_DEMAND_META_FILE = "eia_demand_meta.parquet"
_GENERATION_PROFILES_FILE = "eia_generation_profiles.parquet"

# EIA-930 hourly extract for the ERCOT balancing authority. Unlike the
# per-ISO demand-profiles parquet, it carries the Total Interchange series
# (DC-tie imports/exports), used to net out interchange in load_demand.
_ERCO_HOURLY_FILE: Path = (
    Path(__file__).parents[3] / "data" / "eia_hourly" / "ERCO hourly.parquet"
)

# Column names in the demand-meta parquet that make up the returned metadata.
_META_FIELDS = ("peak_mw", "min_mw", "avg_mw", "total_annual_mwh")


@lru_cache(maxsize=8)
def _ercot_hourly_frame(year: int) -> pd.DataFrame | None:
    """Return the EIA-930 ``ERCO hourly`` rows for one calendar year.

    The rows are restricted to ``year`` (by ERCOT-local date), sorted
    chronologically by UTC time, and reduced to a clean 8760-hour series —
    in a leap year Feb 29 is dropped. Row 0 is the first ERCOT-local hour
    of the year, matching the HSL parquet's index, so demand, interchange
    and renewable generation drawn from this frame all share one clock.

    Returns ``None`` when the file is missing or the year is not covered.
    """
    if not _ERCO_HOURLY_FILE.exists():
        return None
    df = pd.read_parquet(_ERCO_HOURLY_FILE)
    local = df["Local date"]
    df = df[
        (local.dt.year == year)
        & ~((local.dt.month == 2) & (local.dt.day == 29))
    ].sort_values("UTC time")
    if len(df) != HOURS_PER_YEAR:
        return None
    return df.reset_index(drop=True)


def _load_ercot_hourly(year: int) -> tuple[np.ndarray, np.ndarray] | None:
    """Return ERCOT hourly metered demand and net interchange for a year.

    Both series are read from the same chronological ``ERCO hourly`` rows,
    keeping interchange aligned to demand. EIA's interchange sign
    convention is positive = net export, negative = net import. Returns
    ``None`` when no full-year frame is available, signaling the caller to
    fall back to the per-ISO demand-profiles parquet (no interchange).
    """
    frame = _ercot_hourly_frame(year)
    if frame is None:
        return None
    demand = frame["Demand"].to_numpy(dtype=float)
    interchange = (
        frame["Total interchange"].interpolate().bfill().ffill()
        .to_numpy(dtype=float)
    )
    if np.isnan(demand).any() or np.isnan(interchange).any():
        return None
    return demand, interchange


def load_ercot_renewable_gen(year: int) -> dict[str, np.ndarray] | None:
    """Return ERCOT hourly wind and solar net generation (MW) for a year.

    Reads the EIA-930 ``ERCO hourly`` extract — the same chronological
    source as the demand and interchange series — so renewable profiles
    share the calibration's time index. Returns ``{"wind": ..., "solar":
    ...}`` of ``(HOURS_PER_YEAR,)`` arrays, or ``None`` when the file, the
    year, or the per-source generation columns are unavailable.
    """
    frame = _ercot_hourly_frame(year)
    if frame is None:
        return None
    out: dict[str, np.ndarray] = {}
    for fuel, column in (("wind", "NG: WND"), ("solar", "NG: SUN")):
        if column not in frame.columns:
            return None
        series = frame[column].interpolate().bfill().ffill()
        if series.isna().any():
            return None
        out[fuel] = series.to_numpy(dtype=float)
    return out


def load_ercot_fossil_gen(year: int) -> dict[str, np.ndarray] | None:
    """Return ERCOT hourly coal and natural-gas net generation (MW) for a year.

    Reads the EIA-930 ``ERCO hourly`` extract — the same chronological
    source as the demand and renewable series — so the fossil profiles
    share the calibration's time index. ``"gas"`` is the balancing
    authority's whole gas fleet (combined cycle, combustion turbine and
    steam together), the counterpart to the model's summed gas dispatch.
    Returns ``{"coal": ..., "gas": ...}`` of ``(HOURS_PER_YEAR,)`` arrays,
    or ``None`` when the file, the year, or the per-source columns are
    unavailable.
    """
    frame = _ercot_hourly_frame(year)
    if frame is None:
        return None
    out: dict[str, np.ndarray] = {}
    for fuel, column in (("coal", "NG: COL"), ("gas", "NG: NG")):
        if column not in frame.columns:
            return None
        series = frame[column].interpolate().bfill().ffill()
        if series.isna().any():
            return None
        out[fuel] = series.to_numpy(dtype=float)
    return out


def _filter_iso_year(df: pd.DataFrame, iso: str, year: int) -> pd.DataFrame:
    """Return the rows of ``df`` matching the given ISO and year.

    Args:
        df: A DataFrame with ``iso`` and ``year`` columns.
        iso: ISO identifier to select.
        year: Calendar year to select.

    Returns:
        The matching subset, with the row order preserved.

    Raises:
        ValueError: if no rows match the requested ISO and year.
    """
    subset = df[(df["iso"] == iso) & (df["year"] == year)]
    if subset.empty:
        raise ValueError(f"No EIA-930 data for ISO '{iso}' in year {year}")
    return subset


def load_demand(
    iso: str,
    year: int,
    iso_config: ISOConfig | None = None,
    td_loss_factor: float = 0.0,
    data_dir: Path = DATA_DIR,
) -> np.ndarray:
    """Load hourly ISO demand and allocate it across zones.

    The total ISO demand for ``(iso, year)`` is read from the demand-profiles
    parquet and split across the ISO's zones in proportion to each zone's
    ``load_share``. A zone with ``load_share == 0.0`` (such as CAISO's
    ``WECC_import`` import node) therefore receives an all-zero row.

    The EIA-930 series reports metered system load. When ``td_loss_factor``
    is positive, demand is grossed up to the generation level the fleet must
    actually serve (``demand × (1 + factor)``), since transmission and
    distribution losses sit between generation and the meter.

    For ERCOT, demand and DC-tie interchange are read together from the
    EIA-930 ``ERCO hourly`` extract: a net import lowers what the internal
    fleet must serve, a net export raises it. Other ISOs use the per-ISO
    demand-profiles parquet, which carries no interchange.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Calendar year to load.
        iso_config: Topology configuration supplying zone load shares. If
            ``None``, it is fetched via :func:`get_iso_config`.
        td_loss_factor: T&D losses as a fraction of metered load. The
            allocated demand is scaled by ``1 + td_loss_factor``. Defaults
            to ``0.0`` (no gross-up).
        data_dir: Directory containing the EIA-930 parquet extracts.

    Returns:
        A ``(n_zones, HOURS_PER_YEAR)`` array of zonal demand in MW, ordered
        to match ``iso_config.zones``.

    Raises:
        ValueError: if no data matches ``(iso, year)``.
        AssertionError: if the series is not a full year, contains NaN
            demand, or has a non-positive peak.
    """
    if iso_config is None:
        iso_config = get_iso_config(iso)

    interchange = np.zeros(HOURS_PER_YEAR, dtype=float)
    ercot_hourly = _load_ercot_hourly(year) if iso == "ERCOT" else None
    if ercot_hourly is not None:
        raw_mw, interchange = ercot_hourly
    else:
        profiles = pd.read_parquet(data_dir / _DEMAND_PROFILES_FILE)
        subset = _filter_iso_year(profiles, iso, year).sort_values("hour")
        assert len(subset) == HOURS_PER_YEAR, (
            f"Expected {HOURS_PER_YEAR} hours for {iso} {year}, "
            f"got {len(subset)}"
        )
        raw_mw = subset["raw_mw"].to_numpy(dtype=float)

    assert not np.isnan(raw_mw).any(), f"NaN demand for {iso} {year}"
    assert raw_mw.max() > 0.0, f"Non-positive peak demand for {iso} {year}"

    load_shares = np.array(
        [zone.load_share for zone in iso_config.zones], dtype=float
    )
    demand = load_shares[:, None] * raw_mw[None, :]
    if td_loss_factor > 0.0:
        demand *= 1.0 + td_loss_factor
    # Net DC-tie interchange displaces internal generation: a net import
    # (negative) lowers what the fleet must serve, a net export raises it.
    # Interchange is a transmission-level flow, so it is not loss-grossed.
    demand += load_shares[:, None] * interchange[None, :]
    return demand


def load_demand_meta(
    iso: str,
    year: int,
    data_dir: Path = DATA_DIR,
) -> dict:
    """Load summary demand statistics for an ISO and year.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Calendar year to load.
        data_dir: Directory containing the EIA-930 parquet extracts.

    Returns:
        A dict with keys ``peak_mw``, ``min_mw``, ``avg_mw`` and
        ``total_annual_mwh``.

    Raises:
        ValueError: if no data matches ``(iso, year)``.
    """
    meta = pd.read_parquet(data_dir / _DEMAND_META_FILE)
    row = _filter_iso_year(meta, iso, year).iloc[0]
    return {field: row[field] for field in _META_FIELDS}


def load_generation_profiles(
    iso: str,
    year: int,
    data_dir: Path = DATA_DIR,
) -> pd.DataFrame:
    """Load per-fuel hourly generation profiles for an ISO and year.

    The ``value`` column is a normalized distribution that sums to roughly
    1.0 over the hours of each ``(iso, year, fuel)`` group.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Calendar year to load.
        data_dir: Directory containing the EIA-930 parquet extracts.

    Returns:
        A DataFrame with columns ``iso``, ``year``, ``fuel``, ``hour`` and
        ``value`` for the requested ISO and year.

    Raises:
        ValueError: if no data matches ``(iso, year)``.
    """
    profiles = pd.read_parquet(data_dir / _GENERATION_PROFILES_FILE)
    return _filter_iso_year(profiles, iso, year)
