"""EIA-930 measured-actuals benchmark loaders for :mod:`market_sim.data.eia930`.

The per-fuel hourly benchmark series the calibration report scores against
(``load_eia_hourly_benchmark`` and the ERCOT-specific fossil / nuclear /
renewable / battery / other readers), plus the normalized generation-profile
distributions. Split out of ``data/eia_loader.py`` as pure code motion (W-D2,
2026-07-20).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR

from .frames import (
    DATA_DIR,
    _GENERATION_PROFILES_FILE,
    _ISO_LOCAL_TZ,
    _ISO_TO_HOURLY_BA,
    _eia_hourly_frame_filled,
    _eia_hourly_path,
    _ercot_hourly_frame,
    _filter_iso_year,
    _read_clean_iso_year,
    _use_clean,
)


# Clean ``generation`` fuel bucket -> model benchmark series name, restricted to
# the buckets that map 1:1 onto a single EIA-930 ``NG: <CODE>`` column (and so
# equal the raw benchmark within tolerance). The storage family (clean ``storage``
# folds EIA BAT/PS/UES/...; the benchmark keeps ``battery`` / ``pumped_storage``
# split) and the catch-all ``other`` / ``geothermal`` buckets aggregate
# differently and are deliberately not overridden from clean here.
_CLEAN_GEN_FUEL_TO_BENCHMARK: dict[str, str] = {
    "coal": "coal",
    "gas": "gas",
    "nuclear": "nuclear",
    "hydro": "hydro",
    "solar": "solar",
    "wind": "wind",
    "oil": "oil",
}


def _clean_generation_by_fuel(iso: str, year: int) -> dict[str, np.ndarray] | None:
    """Return clean-backed per-fuel hourly generation (MW), keyed by benchmark name.

    Reshapes the long-form clean ``generation`` (one row per ``(zone, fuel,
    hour)``) into the wide per-fuel arrays the model benchmark expects, summing
    the clean zones per ``(fuel, hour)`` and placing each fuel on the model's
    8760-hour clock. Only the buckets that map 1:1 onto a single EIA-930 fuel
    column (:data:`_CLEAN_GEN_FUEL_TO_BENCHMARK`) are returned. Per-fuel NaN
    holes are gap-filled exactly as :func:`load_eia_hourly_benchmark` does.
    Returns ``None`` when the ISO is unsupported, the partition is absent, or the
    reconstructed grid is not a clean full year.
    """
    if iso not in _ISO_LOCAL_TZ:
        return None
    rows = _read_clean_iso_year("generation", iso, year)
    if rows is None:
        return None
    wide = rows.pivot_table(
        index="interval_start_utc",
        columns="fuel",
        values="generation_mw",
        aggfunc="sum",
    ).sort_index()
    if wide.shape[0] != HOURS_PER_YEAR:
        return None
    out: dict[str, np.ndarray] = {}
    for clean_fuel, bench_name in _CLEAN_GEN_FUEL_TO_BENCHMARK.items():
        if clean_fuel not in wide.columns:
            continue
        series = wide[clean_fuel].interpolate().bfill().ffill().to_numpy(dtype=float)
        if np.isnan(series).any():
            continue
        out[bench_name] = series
    return out or None


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


# EIA-930 ``<BA> hourly`` per-fuel net-generation columns, mapped to the
# model's benchmark series names. Gas is the whole gas fleet (CC + CT + ST),
# the counterpart to the model's summed gas dispatch. The storage rows are
# *net* series (positive = discharging, negative = charging) and only appear
# in extract vintages whose BA reports the EIA-930 storage split (``BAT`` /
# ``PS`` fuel codes; the current CISO extract predates the split and folds
# batteries into the legacy ``OTH`` category) — absent columns are skipped
# below, so the battery benchmark wires itself in automatically once a
# regenerated extract carries them.
_EIA930_BENCHMARK_COLUMNS: tuple[tuple[str, str], ...] = (
    ("coal", "NG: COL"),
    ("gas", "NG: NG"),
    ("nuclear", "NG: NUC"),
    ("wind", "NG: WND"),
    ("solar", "NG: SUN"),
    ("oil", "NG: OIL"),
    ("hydro", "NG: WAT"),
    # "Other Fuel Sources" (geothermal / biomass / process gas reported outside
    # the NG: NG aggregate). Threaded through so the per-class benchmark can tell
    # how much geothermal+biomass a BA correctly reports here vs silently folds
    # into its "Natural Gas" cell — the partial-fold-in deflation in
    # render_calibration_html.reconcile_vintage_classes (generalizes the CAISO
    # allowlist to MISO and any other partial-fold BA).
    ("other", "NG: OTH"),
    ("battery", "NG: BAT"),
    ("pumped_storage", "NG: PS"),
)

# Storage net-generation series (battery / pumped storage) are the only EIA-930
# fuel rows a BA *begins reporting partway through* a year: the BAT/PS breakout
# is added to a BA's filing on a specific month (e.g. ISNE first reports NG: PS
# in Nov 2024 — Jan–Oct are blank), so a year can carry only a few months of
# data. Unlike the always-reported thermal/VRE rows, a partial storage series is
# NOT a full-year observation: summing it gives a 2-month throughput that would
# read as a spurious annual under/over-count against the model's full 8760 hours.
# A storage series whose raw coverage falls below this fraction is therefore
# treated as not-yet-reporting for the year and dropped (the C5b throughput
# criterion then stays SKIPPED rather than scoring a partial vintage). This is a
# coverage gate on the *measured input*, not a residual-tuned knob; it
# generalises the existing all-NaN guard (a fully-blank series, e.g. ISNE PS
# 2023, is the coverage=0 limit of the same rule).
_STORAGE_BENCHMARK_SERIES: frozenset[str] = frozenset({"battery", "pumped_storage"})
_STORAGE_MIN_COVERAGE_FRAC: float = 0.5


def _pad_to_year(series: np.ndarray) -> np.ndarray:
    """Return ``series`` coerced to exactly ``HOURS_PER_YEAR`` samples.

    Longer series are truncated; shorter ones (an EIA-930 BA-year with a few
    missing hours, e.g. PJM 2023) are edge-padded with the series mean so the
    annual total scales to a full year rather than carrying a gap.
    """
    series = np.asarray(series, dtype=float)
    if series.shape[0] >= HOURS_PER_YEAR:
        return series[:HOURS_PER_YEAR]
    pad = np.full(HOURS_PER_YEAR - series.shape[0], float(series.mean()))
    return np.concatenate([series, pad])


def load_eia_hourly_benchmark(iso: str, year: int) -> dict[str, np.ndarray] | None:
    """Return the EIA-930 hourly benchmark series for any ISO's BA, full year.

    Generalizes the ERCOT-only :func:`load_ercot_fossil_gen` /
    :func:`load_ercot_nuclear_gen` / :func:`load_ercot_renewable_gen` trio to
    every ISO with a per-BA ``<BA> hourly`` extract (see
    :data:`_ISO_TO_HOURLY_BA`). Returns the per-fuel net generation plus the
    actual net generation and net interchange, each as a ``(HOURS_PER_YEAR,)``
    array. Unlike the strict :func:`_eia_hourly_frame`, a BA-year a few hours
    short of 8760 (e.g. PJM 2023) is padded to a full year rather than
    rejected, so the delivered fuel-mix and interchange benchmark is still
    available for the calibration report.

    EIA's interchange sign convention is positive = net export.

    Returns ``None`` when the ISO is unmapped, the file is missing, or the
    year has no rows.
    """
    ba_code = _ISO_TO_HOURLY_BA.get(iso)
    if ba_code is None:
        return None
    path = _eia_hourly_path(ba_code)
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    local = df["Local date"]
    df = df[
        (local.dt.year == year) & ~((local.dt.month == 2) & (local.dt.day == 29))
    ].sort_values("UTC time")
    if df.empty:
        return None

    out: dict[str, np.ndarray] = {}
    for name, column in _EIA930_BENCHMARK_COLUMNS:
        if column not in df.columns:
            continue
        # Storage breakout series can be reported for only part of the year
        # (the BA added BAT/PS to its filing mid-year); a sub-threshold raw
        # coverage means the series is not a full-year observation, so drop it
        # rather than interpolate a few months across the whole year.
        if name in _STORAGE_BENCHMARK_SERIES:
            coverage = 1.0 - float(df[column].isna().mean())
            if coverage < _STORAGE_MIN_COVERAGE_FRAC:
                continue
        series = df[column].interpolate().bfill().ffill()
        if series.isna().any():
            continue
        out[name] = _pad_to_year(series.to_numpy(dtype=float))

    if "Net generation" in df.columns:
        net_gen = df["Net generation"].interpolate().bfill().ffill()
        if not net_gen.isna().any():
            out["net_gen"] = _pad_to_year(net_gen.to_numpy(dtype=float))
    if "Total interchange" in df.columns:
        interchange = df["Total interchange"].interpolate().bfill().ffill()
        if not interchange.isna().any():
            out["interchange"] = _pad_to_year(interchange.to_numpy(dtype=float))

    # Clean-data seam (gated, default OFF): override the per-fuel generation
    # with the curated clean ``generation`` dataset for the 1:1-mapped fuels
    # (parity-checked in tests). The aggregate ``net_gen`` / ``interchange`` and
    # any non-overridden fuels keep their raw values.
    if _use_clean():
        clean_fuels = _clean_generation_by_fuel(iso, year)
        if clean_fuels:
            out.update(clean_fuels)
    return out or None


def load_eia_hourly_renewable_gen(iso: str, year: int) -> dict[str, np.ndarray] | None:
    """Return hourly wind/solar net generation (MW) for an ISO's EIA-930 BA.

    Resolves the ISO to its EIA-930 BA code (see :data:`_ISO_TO_HOURLY_BA`)
    and reads the per-BA wide ``<BA> hourly`` extract — the same chronological
    source as the demand and interchange series — so renewable profiles share
    the calibration's time index. Each present series is gap-filled (linear
    interpolation, then back/forward fill) like the ERCOT renewable path.
    Small calendar holes in the extract itself (PJM's missing first hour and
    fall-back day) are bridged by :func:`_eia_hourly_frame_filled`, so a
    BA-year a day short of 8760 still yields a measured profile instead of
    silently falling back to the normalized EIA-930 distribution shape.

    Returns ``{"wind": ..., "solar": ...}`` of ``(HOURS_PER_YEAR,)`` arrays for
    whichever of the two fuels the BA reports with a usable full-year series,
    or ``None`` when the ISO is unmapped, the file/year is unavailable, or
    neither fuel is usable.
    """
    ba_code = _ISO_TO_HOURLY_BA.get(iso)
    if ba_code is None:
        return None
    frame = _eia_hourly_frame_filled(ba_code, year)
    if frame is None:
        return None
    out: dict[str, np.ndarray] = {}
    for fuel, column in (("wind", "NG: WND"), ("solar", "NG: SUN")):
        if column not in frame.columns:
            continue
        series = frame[column].interpolate().bfill().ffill()
        if series.isna().any():
            continue
        out[fuel] = series.to_numpy(dtype=float)
    return out or None


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


def load_ercot_nuclear_gen(year: int) -> np.ndarray | None:
    """Return ERCOT hourly nuclear net generation (MW) for a year.

    Reads the EIA-930 ``ERCO hourly`` ``NG: NUC`` series on the same
    chronological clock as the demand, renewable and fossil series.
    Returns a ``(HOURS_PER_YEAR,)`` array, or ``None`` when the file,
    the year, or the column is unavailable.
    """
    frame = _ercot_hourly_frame(year)
    if frame is None or "NG: NUC" not in frame.columns:
        return None
    series = frame["NG: NUC"].interpolate().bfill().ffill()
    if series.isna().any():
        return None
    return series.to_numpy(dtype=float)


def load_ercot_other_gen(year: int) -> np.ndarray | None:
    """Return ERCOT hourly "Other Fuel Sources" net generation (MW) for a year.

    Reads the EIA-930 ``ERCO hourly`` ``NG: OTH`` series on the same
    chronological clock as the other benchmark series. Threaded into the
    calibration bundle so the benchmark can tell how much other/biomass
    generation ERCO reports OUTSIDE its "Natural Gas" cell: since the
    Nov-2024 EIA-930 storage breakout moved battery discharge out of OTH
    (into BAT/UES), ERCO's Other series carries roughly biomass alone
    (~0.26 TWh in 2025) while EIA-923 books ~1.1 TWh of OTHER + biomass grid
    generation — the balance sits inside ``NG: NG``. Carrying the measured
    Other series lets the gas fold-in deflation subtract only the
    genuinely-folded portion (``render_calibration_html._gas_foldin_deflation``
    and the C2 family fallback in ``calibration_verdict.score_sysvol``)
    instead of scoring the model's gas fleet against gas + other. Returns
    ``None`` when the file, the year, or the column is unavailable.
    """
    frame = _ercot_hourly_frame(year)
    if frame is None or "NG: OTH" not in frame.columns:
        return None
    series = frame["NG: OTH"].interpolate().bfill().ffill()
    if series.isna().any():
        return None
    return series.to_numpy(dtype=float)


def load_ercot_battery_gen(year: int) -> dict[str, np.ndarray] | None:
    """Return ERCOT hourly battery discharge and charge (MW) for a year.

    Reads the EIA-930 ``ERCO hourly`` battery series on the same
    chronological clock as the other benchmark series: ``NG: BAT`` carries
    the fleet's net discharge and ``NG: UES`` (unspecified energy storage)
    its net charge as negative MW. The two are folded into non-negative
    ``{"battery_discharge": ..., "battery_charge": ...}`` arrays of
    ``(HOURS_PER_YEAR,)``.

    Unlike the fossil/nuclear loaders, hours the BA had not yet begun
    reporting (ERCOT's battery series starts mid-2024) are kept as NaN
    rather than gap-filled or rejected, so a partial-coverage year still
    yields a benchmark over its reported window. Returns ``None`` when the
    file, the year, or both battery columns are unavailable.
    """
    frame = _ercot_hourly_frame(year)
    if frame is None:
        return None
    cols = [c for c in ("NG: BAT", "NG: UES") if c in frame.columns]
    if not cols:
        return None
    # BAT (discharge) and UES (charge) can be nonzero in the same hour, so
    # positive/negative MW are folded per column — never netted across them.
    values = frame[cols].to_numpy(dtype=float)
    if np.isnan(values).all():
        return None
    discharge = np.nansum(np.clip(values, 0.0, None), axis=1)
    charge = np.nansum(np.clip(-values, 0.0, None), axis=1)
    unreported = np.isnan(values).all(axis=1)
    discharge[unreported] = np.nan
    charge[unreported] = np.nan
    return {"battery_discharge": discharge, "battery_charge": charge}


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
