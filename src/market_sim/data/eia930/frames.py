"""Shared EIA-930 frame plumbing for :mod:`market_sim.data.eia930`.

Path constants, the non-leap hour-calendar anchor, the clean-data consumption
seam, and the per-BA ``<BA> hourly`` extract loaders that every other module
in the package (demand, envelopes, actuals, zonal shares) reads its frames
through. Split out of ``data/eia_loader.py`` as pure code motion (W-D2,
2026-07-20); the facade module aliases that historical import path to this
package, so the compatibility contract lives there.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import EIA_930_DIR, EIA_HOURLY_DIR, RAW_DIR

# The package keeps the pre-split logger name: logging config and the
# ``assertLogs("market_sim.data.eia_loader")`` assertions in the test suite
# key on it (the split is code motion, not a logging rename). Every module in
# the package shares this one logger.
logger = logging.getLogger("market_sim.data.eia_loader")


# Default location of the EIA-930 parquet extracts (from the central registry).
DATA_DIR: Path = EIA_930_DIR


# Cumulative hours before the first of each 1-based month, non-leap calendar,
# for mapping a (month, day, hour) to an hour-of-year index in [0, 8760).
_MONTH_START_HOUR: tuple[int, ...] = tuple(
    int(sum((31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[:m]) * 24)
    for m in range(12)
)

_DEMAND_PROFILES_FILE = "eia_demand_profiles.parquet"
_DEMAND_META_FILE = "eia_demand_meta.parquet"
_GENERATION_PROFILES_FILE = "eia_generation_profiles.parquet"


# Per-BA wide EIA-930 hourly extracts live here, one ``<BA> hourly.parquet``
# per balancing authority (built from the long uploads by
# scripts/data/convert_eia930.py). Unlike the per-ISO demand-profiles parquet,
# they carry the Total Interchange series (DC-tie imports/exports), used to
# net out interchange in load_demand. Re-exported from the central registry.

# Model ISO -> EIA-930 BA code for the per-BA wide hourly extract. An ISO
# with no entry here falls back to the demand-profiles parquet.
_ISO_TO_HOURLY_BA: dict[str, str] = {
    "ERCOT": "ERCO",
    "CAISO": "CISO",
    "PJM": "PJM",
    "NYISO": "NYIS",
    "MISO": "MISO",
    "NEISO": "ISNE",
}

# ERCOT extract path, kept as a named constant for the ERCOT-specific helpers.
_ERCO_HOURLY_FILE: Path = EIA_HOURLY_DIR / "ERCO hourly.parquet"

# Column names in the demand-meta parquet that make up the returned metadata.
_META_FIELDS = ("peak_mw", "min_mw", "avg_mw", "total_annual_mwh")


# ---------------------------------------------------------------------------
# Clean-data consumption seam (gated behind MARKET_SIM_USE_CLEAN, default OFF)
# ---------------------------------------------------------------------------
# The standardization contract curates the raw EIA-930 feeds into the canonical
# ``load`` / ``generation`` datatypes under ``data/clean`` (one Parquet per
# ``(iso, year)``), read back through the frozen ``scripts.lib.clean_io`` seam.
# When ``MARKET_SIM_USE_CLEAN`` is truthy these helpers source the system demand
# and per-fuel generation from that clean tree instead of the raw extracts; the
# default-OFF gate keeps every existing raw path byte-identical. Parity between
# the clean-backed and raw series is asserted in
# ``tests/test_consume_load_generation.py``.

# Truthy values for the opt-in environment flag.
_CLEAN_FLAG_TRUE = frozenset({"1", "true", "yes", "on"})

# IANA timezone per ISO whose clean feed is reconstructed onto the model's
# fixed non-leap local-year 8760 clock. The clean ``load`` feed for these BAs
# carries no local-time column, so the model clock is rebuilt from the tz-aware
# UTC timestamps via this zone (verified to reproduce each BA's parquet "Local
# time" exactly). MISO is intentionally absent: its EIA-930 extract stamps a
# fixed-offset local clock that no single IANA zone reproduces.
_ISO_LOCAL_TZ: dict[str, str] = {
    "CAISO": "America/Los_Angeles",
    "ERCOT": "America/Chicago",
    "NEISO": "America/New_York",
    "NYISO": "America/New_York",
}


def _use_clean() -> bool:
    """Whether the clean-data consumption seam is enabled (default OFF)."""
    return (
        os.environ.get("MARKET_SIM_USE_CLEAN", "").strip().lower() in _CLEAN_FLAG_TRUE
    )


def _read_clean_seam() -> (
    tuple[Callable[..., pd.DataFrame], Callable[..., bool]] | None
):
    """Return ``(read_clean, clean_exists)`` from the frozen seam, or ``None``.

    The seam lives under ``scripts/`` (not the installed model package), so the
    import is lazy and failure-tolerant: a missing module simply disables the
    clean path and the caller falls back to the raw extracts.
    """
    try:
        from scripts.lib.clean_io import clean_exists, read_clean
    except Exception:  # pragma: no cover - only when scripts/ is off sys.path
        logger.debug("scripts.lib.clean_io unavailable; using raw data paths")
        return None
    return read_clean, clean_exists


def _clean_local_year_rows(
    df: pd.DataFrame, iso: str, year: int
) -> pd.DataFrame | None:
    """Restrict a clean frame to the model's non-leap local-year rows, UTC-sorted.

    Mirrors :func:`_eia_hourly_frame`'s row selection (rows whose EIA-930 "Local
    date" falls in ``year``, local Feb 29 dropped, ordered by UTC) but rebuilt
    from the clean dataset's tz-aware ``interval_start_utc``. EIA-930 stamps
    hours as *hour-ending*, so a row belongs to the local date one hour before
    its (hour-ending) local timestamp; the hour-ending basis is applied before
    the year / Feb-29 filter. Returns ``None`` when the ISO has no known zone.
    """
    tz = _ISO_LOCAL_TZ.get(iso)
    if tz is None:
        return None
    utc = pd.DatetimeIndex(df["interval_start_utc"])
    local = utc.tz_convert(tz).tz_localize(None)
    hour_ending_date = local - pd.Timedelta(hours=1)
    keep = (hour_ending_date.year == year) & ~(
        (hour_ending_date.month == 2) & (hour_ending_date.day == 29)
    )
    out = df.loc[keep].copy()
    return out.sort_values("interval_start_utc")


def _read_clean_iso_year(datatype: str, iso: str, year: int) -> pd.DataFrame | None:
    """Read the clean ``datatype`` rows covering the model's local ``year``.

    A local year straddles two UTC-partitioned clean files (the BA's UTC offset
    pushes the year's tail hours into ``year + 1``), so both partitions are read
    when present and concatenated before the local-year window is cut out by
    :func:`_clean_local_year_rows`. Returns ``None`` when the seam is
    unavailable, no partition exists, or the ISO's clock cannot be rebuilt.
    """
    seam = _read_clean_seam()
    if seam is None:
        return None
    read_clean, clean_exists = seam
    frames = [
        read_clean(datatype, iso=iso, year=y, validate=False)
        for y in (year, year + 1)
        if clean_exists(datatype, iso=iso, year=y)
    ]
    if not frames:
        return None
    rows = _clean_local_year_rows(pd.concat(frames, ignore_index=True), iso, year)
    if rows is None or rows.empty:
        return None
    return rows


def _eia_hourly_path(ba_code: str) -> Path:
    """Return the path to the wide hourly extract for an EIA-930 BA code."""
    # Resolved through the shared package namespace at call time so tests
    # patching ``market_sim.data.eia_loader.EIA_HOURLY_DIR`` (the facade
    # aliases this package) keep redirecting the lookup, exactly as the
    # pre-split module-global read behaved.
    from market_sim.data import eia930 as _pkg

    return _pkg.EIA_HOURLY_DIR / f"{ba_code} hourly.parquet"


@lru_cache(maxsize=32)
def _eia_hourly_frame(ba_code: str, year: int) -> pd.DataFrame | None:
    """Return the EIA-930 ``<BA> hourly`` rows for one calendar year.

    The rows are restricted to ``year`` (by the BA's local date), sorted
    chronologically by UTC time, and reduced to a clean 8760-hour series —
    in a leap year Feb 29 is dropped. Row 0 is the first local hour of the
    year, matching the HSL parquet's index, so demand, interchange and
    renewable generation drawn from this frame all share one clock.

    Returns ``None`` when the file is missing or the year is not covered by a
    full 8760-hour series.
    """
    path = _eia_hourly_path(ba_code)
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    local = df["Local date"]
    df = df[
        (local.dt.year == year) & ~((local.dt.month == 2) & (local.dt.day == 29))
    ].sort_values("UTC time")
    if len(df) != HOURS_PER_YEAR:
        return None
    return df.reset_index(drop=True)


# Largest hole (hours) the gap-filling hourly frame will bridge. The PJM
# extract is missing its first local hour and the 2023-11-05 fall-back day
# (25 hours) plus a few scattered hours in 2024; anything bigger than a few
# days signals a structurally incomplete extract that should stay rejected
# rather than silently interpolated.
_HOURLY_FRAME_MAX_GAP: int = 72


@lru_cache(maxsize=32)
def _eia_hourly_frame_filled(ba_code: str, year: int) -> pd.DataFrame | None:
    """Return the BA-year hourly frame, bridging small gaps with NaN rows.

    Some extracts fall a few hours short of a clean local calendar year (PJM
    is missing its first local hour and the 2023-11-05 fall-back day), which
    the strict :func:`_eia_hourly_frame` rejects outright. This variant
    reindexes the present rows onto the complete hourly UTC clock for the
    local year — anchored from the first present row's ``Local time``, with a
    leap year's local Feb 29 dropped — so the missing hours come back as NaN
    rows for the caller to interpolate. Row k is local hour k of the year,
    the same clock as the strict frame.

    Returns ``None`` when the file is missing, the ``Local time`` anchor
    column is absent, more than :data:`_HOURLY_FRAME_MAX_GAP` hours are
    missing, or the reconstruction does not come out at exactly
    ``HOURS_PER_YEAR`` rows.
    """
    strict = _eia_hourly_frame(ba_code, year)
    if strict is not None:
        return strict
    path = _eia_hourly_path(ba_code)
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    if "Local time" not in df.columns:
        return None
    local = df["Local date"]
    df = df[local.dt.year == year].sort_values("UTC time")
    if len(df) < HOURS_PER_YEAR - _HOURLY_FRAME_MAX_GAP or df.empty:
        return None
    # Anchor the complete UTC clock on the local year boundaries: the first /
    # last present rows fix the UTC<->local offset at each end (both ends are
    # on standard time, so the offsets are exact even mid-DST).
    utc = pd.DatetimeIndex(df["UTC time"])
    # ``Local time`` is the HOUR-ENDING label (HE convention, uniform across
    # the per-BA extracts: the year's first interval [00:00, 01:00) is
    # stamped 01:00 / Hour 1). Row k of this frame must be local hour k
    # INTERVAL-BEGINNING to match the strict frame's positional clock, so
    # shift the stamps back one hour before anchoring. Without this the whole
    # reconstructed year lands one hour late — the CISO-2025 solar-profile
    # +1h shift (FINDING-caiso102, 2026-07-19; also hit PJM-2023/MISO-2025).
    loc = pd.DatetimeIndex(df["Local time"]) - pd.Timedelta(hours=1)
    utc_start = utc[0] - (loc[0] - pd.Timestamp(year=year, month=1, day=1))
    utc_end = utc[-1] + (pd.Timestamp(year=year, month=12, day=31, hour=23) - loc[-1])
    full = pd.date_range(utc_start, utc_end, freq="h")
    # Drop the local Feb 29 of a leap year; February is on standard time, so
    # the January 1st offset maps UTC to local exactly there.
    winter_offset = pd.Timestamp(year=year, month=1, day=1) - utc_start
    approx_local = full + winter_offset
    full = full[~((approx_local.month == 2) & (approx_local.day == 29))]
    if len(full) != HOURS_PER_YEAR:
        return None
    out = (
        df.drop_duplicates(subset="UTC time")
        .set_index("UTC time")
        .reindex(full)
        .reset_index()
        .rename(columns={"index": "UTC time"})
    )
    return out


# EIA-930 long-format (API) region ``type`` code -> wide extract column, for
# the measured NaN-window fill below (same map as scripts/data/convert_eia930.py).
_EIA930_LONG_REGION_COLUMNS: dict[str, str] = {
    "D": "Demand",
    "DF": "Demand forecast",
    "NG": "Net generation",
    "TI": "Total interchange",
}


def _fill_hourly_frame_from_long(frame: pd.DataFrame, ba_code: str) -> pd.DataFrame:
    """Fill a wide hourly frame's NaN hours from the BA's long API series.

    The hand-curated ``<BA> hourly`` extract can carry NaN windows where EIA's
    bulk download lagged — e.g. the ERCO extract's 48-hour 2025-12-04/05 hole,
    two real winter-peak days (measured demand tops 58.4 GW) that the
    per-loader linear interpolation would otherwise bridge as a flat ~48 GW
    valley, fabricating two days of demand and benchmark generation. The
    EIA-930 API long-format uploads of the SAME series
    (``<BA>_region.parquet`` / ``<BA>_fueltype.parquet``,
    ``scripts/data/fetch_eia930_long.py``) were fetched after EIA backfilled the
    window, so the measured hours exist on disk. Fill NaN hours from those
    measured series BEFORE the per-loader interpolation touches them — a
    measured-input repair that regenerates for any future gap (no per-window
    registry), never modifying the immutable extract on disk. Hours absent
    from BOTH sources stay NaN and fall through to the loaders'
    isolated-hour interpolation (or, for the battery series, their
    NaN-preserving not-yet-reporting semantics: the API carries no BAT/UES
    rows before a BA starts filing them, so the reindex leaves those NaN).
    """
    value_cols = [
        c
        for c in frame.columns
        if c in _EIA930_LONG_REGION_COLUMNS.values() or c.startswith("NG: ")
    ]
    if not frame[value_cols].isna().to_numpy().any():
        return frame
    # The extract's UTC clock is tz-naive; the API ``period`` is tz-aware UTC.
    utc = pd.DatetimeIndex(frame["UTC time"])
    if utc.tz is None:
        utc = utc.tz_localize("UTC")
    long_series: dict[str, pd.Series] = {}
    region_path = RAW_DIR / f"{ba_code}_region.parquet"
    if region_path.exists():
        piv = pd.read_parquet(region_path).pivot_table(
            index="period", columns="type", values="value_mwh", aggfunc="first"
        )
        for code, col in _EIA930_LONG_REGION_COLUMNS.items():
            if code in piv.columns:
                long_series[col] = piv[code]
    fuel_path = RAW_DIR / f"{ba_code}_fueltype.parquet"
    if fuel_path.exists():
        piv = pd.read_parquet(fuel_path).pivot_table(
            index="period", columns="fueltype", values="value_mwh", aggfunc="first"
        )
        for code in piv.columns:
            long_series[f"NG: {code}"] = piv[code]
    if not long_series:
        return frame
    frame = frame.copy()
    for col, series in long_series.items():
        if col not in frame.columns:
            continue
        vals = frame[col].to_numpy(dtype=float)
        gap = np.isnan(vals)
        if not gap.any():
            continue
        fill = series.reindex(utc).to_numpy(dtype=float)
        vals[gap] = fill[gap]
        frame[col] = vals
    return frame


@lru_cache(maxsize=8)
def _ercot_hourly_frame(year: int) -> pd.DataFrame | None:
    """Return the EIA-930 ``ERCO hourly`` rows for one calendar year.

    Thin ERCOT-specific wrapper over :func:`_eia_hourly_frame` for the
    demand/interchange, fossil and nuclear paths that are ERCOT-only today,
    with NaN windows filled from the measured long-format API series
    (:func:`_fill_hourly_frame_from_long`) so a multi-day extract hole is
    repaired with measured data rather than bridged by interpolation.
    ERCOT-only for now: other ISOs' committed benchmarks were rendered off
    the un-filled extracts, so generalizing the fill is a deliberate
    per-ISO re-render decision, not a silent side effect.
    """
    frame = _eia_hourly_frame("ERCO", year)
    if frame is None:
        return None
    return _fill_hourly_frame_from_long(frame, "ERCO")


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
