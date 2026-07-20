"""Daily weather loaders for :mod:`market_sim.data.eia930`.

The unified clean-Parquet/raw-CSV weather reader and its hourly-broadcast
helpers (``load_weather`` / ``iso_zone_tmax`` / ``neiso_load_weighted_temp``),
consumed by the reliability-floor engine and the cold-weather gas derate.
Split out of ``data/eia_loader.py`` as pure code motion (W-D2, 2026-07-20).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR


# ---------------------------------------------------------------------------
# Unified weather loader (clean Parquet primary; raw CSV fallback)
# ---------------------------------------------------------------------------

# Per-ISO raw CSV paths for load-weighted aggregate zones (no zone column in
# the source file; written into clean Parquet under zone='_load_weighted').
_LW_RAW: dict[str, Path] = {
    "CAISO": RAW_DIR / "caiso-weather" / "caiso_load_weighted_tmax_daily.csv",
    "NEISO": RAW_DIR / "neiso-weather" / "neiso_load_weighted_temp_daily.csv",
}
# NYISO NYC-metro (Central Park / LaGuardia / JFK) aggregate; zone='_downstate'.
_DOWNSTATE_RAW: dict[str, Path] = {
    "NYISO": RAW_DIR / "nyiso-weather" / "nyiso_downstate_tmax_daily.csv",
}


def _load_weather_from_raw(
    iso: str, year: int, zone: str | None
) -> pd.DataFrame | None:
    """Read daily weather directly from raw CSV when clean Parquet is absent.

    Returns a ``(date, zone, tmax_c, tmin_c)`` DataFrame filtered to ``year``
    and optionally to ``zone``, or ``None`` when the raw file is absent or
    produces no matching rows.  Sentinel zone names redirect to their dedicated
    aggregate files: ``'_load_weighted'`` → the ISO-level load-weighted CSV;
    ``'_downstate'`` → the NYISO NYC-metro CSV.
    """
    iso_u = iso.upper()
    iso_l = iso.lower()

    if zone == "_load_weighted":
        path = _LW_RAW.get(iso_u)
        if path is None or not path.exists():
            return None
        df = pd.read_csv(path, parse_dates=["date"])
        df = df[df["date"].dt.year == year].copy()
        if df.empty:
            return None
        df["zone"] = "_load_weighted"
        df["tmax_c"] = pd.to_numeric(df["tmax_c"], errors="coerce")
        if "tmin_c" in df.columns:
            df["tmin_c"] = pd.to_numeric(df["tmin_c"], errors="coerce")
        else:
            df["tmin_c"] = np.nan
        return df[["date", "zone", "tmax_c", "tmin_c"]].reset_index(drop=True)

    if zone == "_downstate":
        path = _DOWNSTATE_RAW.get(iso_u)
        if path is None or not path.exists():
            return None
        df = pd.read_csv(path, parse_dates=["date"])
        df = df[df["date"].dt.year == year].copy()
        if df.empty:
            return None
        df["zone"] = "_downstate"
        df["tmax_c"] = pd.to_numeric(df["tmax_c"], errors="coerce")
        df["tmin_c"] = np.nan
        return df[["date", "zone", "tmax_c", "tmin_c"]].reset_index(drop=True)

    # Standard per-zone file: {iso}_zone_temp_daily.csv, plus any
    # year-partitioned supplements alongside it (<stem>_<year|yearQn>.csv,
    # e.g. ercot_zone_temp_daily_2021q1.csv) — the same supplement convention
    # scripts/data/curate_weather.py folds into the clean Parquet, so the raw
    # fallback covers the same calendar range as the curated tree (before
    # this, a year present only in a supplement silently returned None when
    # the clean tree was absent — e.g. ERCOT 2021, the Uri weather year the
    # correlated forced-outage derate reads).
    path = RAW_DIR / f"{iso_l}-weather" / f"{iso_l}_zone_temp_daily.csv"
    supplements = sorted(path.parent.glob(f"{path.stem}_*.csv"))
    parts = [p for p in [path, *supplements] if p.exists()]
    if not parts:
        return None
    df = pd.concat(
        (pd.read_csv(p, parse_dates=["date"]) for p in parts), ignore_index=True
    )
    if "zone" in df.columns:
        df = df.drop_duplicates(subset=["date", "zone"])
    df = df[df["date"].dt.year == year].copy()
    if zone is not None and "zone" in df.columns:
        df = df[df["zone"] == zone]
    if df.empty:
        return None
    df["tmax_c"] = pd.to_numeric(df["tmax_c"], errors="coerce")
    if "tmin_c" not in df.columns:
        df["tmin_c"] = np.nan
    else:
        df["tmin_c"] = pd.to_numeric(df["tmin_c"], errors="coerce")
    if "zone" not in df.columns:
        df["zone"] = zone or ""
    return df[["date", "zone", "tmax_c", "tmin_c"]].reset_index(drop=True)


def load_weather(iso: str, year: int, zone: str | None = None) -> pd.DataFrame | None:
    """Load daily weather for *iso*/*year*, preferring clean Parquet over raw CSV.

    Primary path reads ``data/clean/weather/<ISO>/weather_<year>.parquet``
    (produced by ``scripts/data/curate_weather.py``), filtered to *zone* when given.
    Falls back to the raw CSV files under ``data/raw/{iso}-weather/`` when the
    clean file is absent — byte-identical to the previous per-function behaviour.

    Args:
        iso: ISO identifier (e.g. ``"CAISO"``).
        year: Calendar year to load.
        zone: Model zone name, sentinel (``'_load_weighted'``, ``'_downstate'``),
            or ``None`` to return all zones.

    Returns:
        A ``(date, zone, tmax_c, tmin_c)`` DataFrame (one row per calendar day ×
        zone), or ``None`` when no data are available.  ``tmin_c`` may be all-NaN
        for TMAX-only sources (CAISO ``'_load_weighted'``, NYISO ``'_downstate'``).
    """
    from market_sim.config.paths import clean_path

    pq_path = clean_path("weather", iso=iso.upper(), year=year)
    if pq_path.is_file():
        df = pd.read_parquet(pq_path)
        if zone is not None:
            df = df[df["zone"] == zone]
        return df if not df.empty else None

    return _load_weather_from_raw(iso, year, zone)


def _broadcast_daily_to_hourly(
    df: pd.DataFrame, year: int, hours: int, col: str
) -> np.ndarray | None:
    """Broadcast a daily column to an hourly array via day-of-year lookup."""
    doy_val = dict(
        zip(
            df["date"].dt.dayofyear.to_numpy(),
            df[col].to_numpy(dtype=float),
        )
    )
    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    doy = clock.dayofyear.to_numpy()
    out = np.array([doy_val.get(int(d), np.nan) for d in doy], dtype=float)
    if not np.any(np.isfinite(out)):
        return None
    return pd.Series(out).ffill().bfill().to_numpy()


def iso_zone_tmax(
    iso: str, year: int, hours: int, zone: str | None = None
) -> tuple[np.ndarray, np.ndarray | None] | None:
    """Return daily ``(tmax, tmin)`` broadcast to hourly for a given ISO/zone.

    Generic temperature loader for the reliability-floor engine.  Reads the
    curated ``data/clean/weather/<ISO>/weather_<year>.parquet`` via
    :func:`load_weather`, filtered to *zone* and *year*, and broadcasts the
    daily TMAX/TMIN to the hourly run horizon via a day-of-year lookup with
    ``ffill``/``bfill`` gap fill.  Falls back to the raw
    ``data/raw/<iso>-weather/<iso>_zone_temp_daily.csv`` when the clean file is
    absent (byte-identical to the previous behaviour).

    Args:
        iso: ISO identifier (e.g. ``"CAISO"``).
        year: Calendar year to extract.
        hours: Number of run hours (typically 8760).
        zone: Model zone name. ``None`` leaves the frame unfiltered (the engine
            always passes a concrete zone in practice).

    Returns:
        ``(tmax, tmin)`` where each is ``(hours,)`` ndarray in deg C, or
        ``None`` when the weather source is missing, the zone/year is uncovered
        (e.g. a forecast year with no pinned weather), or TMAX cannot be built —
        so the caller leaves the fleet unfloored (byte-identical).  ``tmin`` is
        ``None`` when the source lacks a ``tmin_c`` column.
    """
    df = load_weather(iso, year, zone=zone)
    if df is None:
        return None
    tmax = _broadcast_daily_to_hourly(df, year, hours, "tmax_c")
    tmin = (
        _broadcast_daily_to_hourly(df, year, hours, "tmin_c")
        if "tmin_c" in df.columns and df["tmin_c"].notna().any()
        else None
    )
    return (tmax, tmin) if tmax is not None else None


def neiso_load_weighted_temp(
    year: int, hours: int
) -> tuple[np.ndarray, np.ndarray] | None:
    """Return load-weighted NEISO daily ``(tmax, tmin)`` (deg C) per run hour.

    Thin wrapper around :func:`load_weather` (``zone='_load_weighted'``) +
    :func:`_broadcast_daily_to_hourly`.  Called by
    :func:`market_sim.model.transmission.inject_cold_weather_gas_derate`; kept
    for backward compatibility with that caller.

    Returns ``(tmax, tmin)`` each ``(hours,)`` deg C, or ``None`` when the
    archived file is absent, the year is uncovered, or either temperature
    series has no valid data.
    """
    df = load_weather("NEISO", year, zone="_load_weighted")
    if df is None:
        return None
    tmax = _broadcast_daily_to_hourly(df, year, hours, "tmax_c")
    if tmax is None:
        return None
    tmin = (
        _broadcast_daily_to_hourly(df, year, hours, "tmin_c")
        if "tmin_c" in df.columns and df["tmin_c"].notna().any()
        else None
    )
    if tmin is None:
        return None
    return tmax, tmin
