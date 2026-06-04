"""Loaders for EIA-930 hourly demand and generation series.

Reads the EIA-930 parquet extracts shipped under ``inputs/raw-data/eia-930``
and shapes them for the dispatch model: hourly ISO demand is allocated to
zones by each zone's load share, and generation profiles are returned as
normalized per-fuel distributions.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import ISOConfig, get_iso_config

logger = logging.getLogger(__name__)

# Default location of the EIA-930 parquet extracts, resolved relative to the
# repository root (this file lives at src/market_sim/data/eia_loader.py).
DATA_DIR: Path = Path(__file__).parents[3] / "inputs" / "raw-data" / "eia-930"

# PJM (metered, 20 transmission zones) and ERCOT (NP3-565-CD native load, 8
# weather zones) both publish per-zone hourly load here, one file per year.
# Used to give each model zone its *own* hourly load shape (zones peak at
# different times) instead of a single system shape scaled by a static share.
_ZONAL_LOAD_DIR: Path = (
    Path(__file__).parents[3] / "inputs" / "raw-data" / "zone-specific-demand"
)
# Back-compat alias (PJM-specific name) for any external importer.
_PJM_ZONAL_LOAD_DIR: Path = _ZONAL_LOAD_DIR

# ERCOT weather-zone column (in ERCOT_Native_Load_<year>.xlsx) -> model
# transmission zone (the six-zone topology in iso_configs._ercot_config). ERCOT
# has no Panhandle weather zone, so the Panhandle model zone receives no load
# here (its share stays 0.0, matching the static config); the small Lubbock load
# it would hold sits inside the WEST weather zone and lands in the West model
# zone. The ERCOT system-total column is dropped. Mirrors the aggregation in
# scripts/derive_load_shares.py that seeded the static load_share values.
_ERCOT_LOAD_ZONE_GROUPS: dict[str, str] = {
    "COAST": "Houston",
    "EAST": "North", "NORTH": "North", "NCENT": "North",
    "SCENT": "South_Central",
    "SOUTH": "South",
    "FWEST": "West", "WEST": "West",
}

# PJM's hourly actual tie-line interchange (import/export) lives here, one file
# per year. Used to add PJM's net export to the demand the internal fleet must
# serve, closing the energy-only model's largest structural gap (PJM is a large
# net exporter, ~40 TWh in 2023).
_PJM_INTERCHANGE_DIR: Path = (
    Path(__file__).parents[3] / "inputs" / "raw-data" / "iso-specific-transmission"
)

# Real PJM transmission zone -> model zone (the eight-zone aggregation in
# iso_configs._pjm_config). ``RTO`` is the system total and is dropped.
_PJM_LOAD_ZONE_GROUPS: dict[str, str] = {
    "CE": "PJM_ComEd",
    "AEP": "PJM_AEP_Ohio", "DAY": "PJM_AEP_Ohio", "DEOK": "PJM_AEP_Ohio",
    "OVEC": "PJM_AEP_Ohio",
    "ATSI": "PJM_ATSI",
    "AP": "PJM_West_APS", "DUQ": "PJM_West_APS",
    "PL": "PJM_Central_PA", "PN": "PJM_Central_PA", "ME": "PJM_Central_PA",
    "EKPC": "PJM_Central_PA",
    "DOM": "PJM_Dominion",
    "PS": "PJM_EMAAC", "JC": "PJM_EMAAC", "PE": "PJM_EMAAC",
    "DPL": "PJM_EMAAC", "AE": "PJM_EMAAC", "RECO": "PJM_EMAAC",
    "BC": "PJM_SWMAAC", "PEP": "PJM_SWMAAC",
}

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
# scripts/convert_eia930.py). Unlike the per-ISO demand-profiles parquet,
# they carry the Total Interchange series (DC-tie imports/exports), used to
# net out interchange in load_demand.
EIA_HOURLY_DIR: Path = Path(__file__).parents[3] / "data" / "eia_hourly"

# Model ISO -> EIA-930 BA code for the per-BA wide hourly extract. An ISO
# with no entry here falls back to the demand-profiles parquet.
_ISO_TO_HOURLY_BA: dict[str, str] = {
    "ERCOT": "ERCO",
    "CAISO": "CISO",
    "PJM": "PJM",
    "NYISO": "NYIS",
    "MISO": "MISO",
    "NEISO": "ISNE",
    "SPP": "SWPP",
}

# ERCOT extract path, kept as a named constant for the ERCOT-specific helpers.
_ERCO_HOURLY_FILE: Path = EIA_HOURLY_DIR / "ERCO hourly.parquet"

# Column names in the demand-meta parquet that make up the returned metadata.
_META_FIELDS = ("peak_mw", "min_mw", "avg_mw", "total_annual_mwh")


def _eia_hourly_path(ba_code: str) -> Path:
    """Return the path to the wide hourly extract for an EIA-930 BA code."""
    return EIA_HOURLY_DIR / f"{ba_code} hourly.parquet"


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
        (local.dt.year == year)
        & ~((local.dt.month == 2) & (local.dt.day == 29))
    ].sort_values("UTC time")
    if len(df) != HOURS_PER_YEAR:
        return None
    return df.reset_index(drop=True)


@lru_cache(maxsize=8)
def _ercot_hourly_frame(year: int) -> pd.DataFrame | None:
    """Return the EIA-930 ``ERCO hourly`` rows for one calendar year.

    Thin ERCOT-specific wrapper over :func:`_eia_hourly_frame` for the
    demand/interchange, fossil and nuclear paths that are ERCOT-only today.
    """
    return _eia_hourly_frame("ERCO", year)


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


# EIA-930 ``<BA> hourly`` per-fuel net-generation columns, mapped to the
# model's benchmark series names. Gas is the whole gas fleet (CC + CT + ST),
# the counterpart to the model's summed gas dispatch.
_EIA930_BENCHMARK_COLUMNS: tuple[tuple[str, str], ...] = (
    ("coal", "NG: COL"),
    ("gas", "NG: NG"),
    ("nuclear", "NG: NUC"),
    ("wind", "NG: WND"),
    ("solar", "NG: SUN"),
    ("oil", "NG: OIL"),
    ("hydro", "NG: WAT"),
)


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


def load_eia_hourly_benchmark(
    iso: str, year: int
) -> dict[str, np.ndarray] | None:
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
        (local.dt.year == year)
        & ~((local.dt.month == 2) & (local.dt.day == 29))
    ].sort_values("UTC time")
    if df.empty:
        return None

    out: dict[str, np.ndarray] = {}
    for name, column in _EIA930_BENCHMARK_COLUMNS:
        if column not in df.columns:
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
    return out or None


def load_eia_hourly_renewable_gen(
    iso: str, year: int
) -> dict[str, np.ndarray] | None:
    """Return hourly wind/solar net generation (MW) for an ISO's EIA-930 BA.

    Resolves the ISO to its EIA-930 BA code (see :data:`_ISO_TO_HOURLY_BA`)
    and reads the per-BA wide ``<BA> hourly`` extract — the same chronological
    source as the demand and interchange series — so renewable profiles share
    the calibration's time index. Each present series is gap-filled (linear
    interpolation, then back/forward fill) like the ERCOT renewable path.

    Returns ``{"wind": ..., "solar": ...}`` of ``(HOURS_PER_YEAR,)`` arrays for
    whichever of the two fuels the BA reports with a usable full-year series,
    or ``None`` when the ISO is unmapped, the file/year is unavailable, or
    neither fuel is usable.
    """
    ba_code = _ISO_TO_HOURLY_BA.get(iso)
    if ba_code is None:
        return None
    frame = _eia_hourly_frame(ba_code, year)
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


def _hours_of_year(ts: pd.Series) -> np.ndarray:
    """Map naive timestamps to an hour-of-year index on the non-leap clock.

    Feb 29 must already be removed by the caller; this returns indices into
    ``[0, HOURS_PER_YEAR)`` using the fixed non-leap month lengths.
    """
    return (
        np.array(_MONTH_START_HOUR)[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )


def _hourly_shares_from_groups(
    mzone: pd.Series, hoy: np.ndarray, mw: pd.Series, zone_names: list[str]
) -> np.ndarray:
    """Build a ``(n_zones, HOURS_PER_YEAR)`` hourly load-share matrix.

    Sums ``mw`` into a (model zone, hour-of-year) grid, back-fills any all-zero
    hour (e.g. a DST spring-forward gap) from the previous hour, and normalizes
    each hour to fractions summing to 1.0 across zones. Zones absent from the
    data (such as ERCOT's Panhandle) keep an all-zero row.
    """
    zone_idx = {z: i for i, z in enumerate(zone_names)}
    grid = np.zeros((len(zone_names), HOURS_PER_YEAR), dtype=float)
    grp = (
        pd.DataFrame({"mzone": mzone.to_numpy(), "hoy": hoy, "mw": mw.to_numpy()})
        .groupby(["mzone", "hoy"], observed=True)["mw"]
        .sum()
    )
    for (mz, h), v in grp.items():
        if mz in zone_idx and 0 <= h < HOURS_PER_YEAR:
            grid[zone_idx[mz], int(h)] = v
    col_tot = grid.sum(axis=0)
    for h in np.nonzero(col_tot == 0.0)[0]:
        grid[:, h] = grid[:, h - 1] if h > 0 else grid[:, h + 1]
        col_tot[h] = grid[:, h].sum()
    return grid / col_tot[None, :]


def pjm_zonal_load_shares(
    year: int, zone_names: list[str]
) -> np.ndarray | None:
    """Return ``(n_zones, HOURS_PER_YEAR)`` hourly PJM load shares, or ``None``.

    Reads PJM's hourly metered-load file for ``year``, aggregates the 20 real
    transmission zones into the eight model zones (:data:`_PJM_LOAD_ZONE_GROUPS`)
    and, for each hour, returns each model zone's fraction of system load. The
    caller multiplies these time-varying shares by the system demand total, so
    each zone gets its own measured shape (zones peak at different times) while
    the system level stays tied to the existing demand series.

    Returns ``None`` when the file is absent so the caller falls back to the
    static per-zone ``load_share``. The series is placed on the model's fixed
    non-leap 8760-hour clock (Feb 29 dropped); the lone DST spring-forward gap
    is back-filled from the previous hour.
    """
    path = _ZONAL_LOAD_DIR / f"PJM{year}_hrl_load_metered.csv"
    if not path.exists():
        logger.warning(
            "PJM zonal metered-load file not found (%s); using static "
            "load_share split", path,
        )
        return None
    df = pd.read_csv(path, usecols=["datetime_beginning_ept", "zone", "mw"])
    df = df[df["zone"] != "RTO"].copy()
    df["mzone"] = df["zone"].map(_PJM_LOAD_ZONE_GROUPS)
    if df["mzone"].isna().any():
        missing = sorted(df.loc[df["mzone"].isna(), "zone"].unique())
        logger.warning("PJM load zones not mapped to a model zone: %s", missing)
        df = df.dropna(subset=["mzone"])
    ts = pd.to_datetime(
        df["datetime_beginning_ept"], format="mixed", errors="coerce"
    )
    file_year = int(ts.dt.year.mode().iat[0])
    if file_year != year:
        logger.warning(
            "PJM%d_hrl_load_metered.csv actually contains %d data; using its "
            "zonal *shape* (stable year-to-year) against %d system demand",
            year, file_year, year,
        )
    keep = ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df, ts = df[keep], ts[keep]
    return _hourly_shares_from_groups(
        df["mzone"], _hours_of_year(ts), df["mw"], zone_names
    )


def ercot_zonal_load_shares(
    year: int, zone_names: list[str]
) -> np.ndarray | None:
    """Return ``(n_zones, HOURS_PER_YEAR)`` hourly ERCOT load shares, or ``None``.

    Reads ERCOT's hourly *Actual System Load by Weather Zone* (NP3-565-CD;
    ``ERCOT_Native_Load_<year>.xlsx``) and aggregates the eight weather zones
    onto the six model transmission zones (:data:`_ERCOT_LOAD_ZONE_GROUPS`),
    returning each model zone's hour-by-hour fraction of system load. The caller
    multiplies these time-varying shares by the EIA-930 system demand total, so
    each zone gets its own measured shape — the hot, wind-rich West and the
    coastal Houston load peak at different hours than North Central — while the
    system level stays tied to the existing EIA-930 demand series.

    This replaces the single ERCOT-wide demand curve (one shape scaled by a
    fixed per-zone ``load_share``) that previously fed every zone's demand.

    Returns ``None`` when the file is absent so the caller falls back to the
    static per-zone ``load_share``. The native-load file stamps each hour as
    "Hour Ending HH:00" (01..24 within the day, no DST gaps); the series is
    placed on the model's fixed non-leap 8760-hour clock (Feb 29 dropped).
    """
    path = _ZONAL_LOAD_DIR / f"ERCOT_Native_Load_{year}.xlsx"
    if not path.exists():
        logger.warning(
            "ERCOT native-load file not found (%s); using static load_share "
            "split", path,
        )
        return None
    df = pd.read_excel(path)
    # "Hour Ending" is "MM/DD/YYYY HH:00" with HH in 01..24; hour-ending HH is
    # hour-of-day HH-1 (01:00 -> 0, 24:00 -> 23, same calendar date).
    he = df["Hour Ending"].astype(str).str.split(" ", n=1, expand=True)
    date = pd.to_datetime(he[0], format="%m/%d/%Y")
    hour_of_day = he[1].str.slice(0, 2).astype(int) - 1
    month = date.dt.month.to_numpy()
    day = date.dt.day.to_numpy()
    keep = ~((month == 2) & (day == 29))
    df = df[keep]
    hoy = (
        np.array(_MONTH_START_HOUR)[month[keep] - 1]
        + (day[keep] - 1) * 24
        + hour_of_day.to_numpy()[keep]
    )
    # Melt the weather-zone columns into long form, mapping each to its model
    # zone; the ERCOT system-total column and any spare columns are dropped.
    wz_cols = [c for c in _ERCOT_LOAD_ZONE_GROUPS if c in df.columns]
    missing_cols = sorted(set(_ERCOT_LOAD_ZONE_GROUPS) - set(df.columns))
    if missing_cols:
        logger.warning(
            "ERCOT native-load weather zones absent from %s: %s",
            path.name, missing_cols,
        )
    mzone = pd.concat(
        [pd.Series([_ERCOT_LOAD_ZONE_GROUPS[c]] * len(df)) for c in wz_cols],
        ignore_index=True,
    )
    hoy_long = np.tile(hoy, len(wz_cols))
    mw = pd.concat(
        [df[c].reset_index(drop=True) for c in wz_cols], ignore_index=True
    )
    return _hourly_shares_from_groups(mzone, hoy_long, mw, zone_names)


def pjm_net_interchange(year: int) -> np.ndarray | None:
    """Return PJM's hourly net export (MW, export-positive), or ``None``.

    Reads PJM's actual tie-line interchange file for ``year``, sums
    ``actual_flow`` across all 22 ties each hour, and flips the sign so a net
    **export** is positive — the convention :func:`load_demand` expects for an
    interchange schedule (a net export raises the generation the internal fleet
    must serve; a net import lowers it). This is PJM's import/export "node",
    modeled as the *measured* schedule rather than a price-responsive offer,
    so a backcast reproduces the ~40 TWh (2023) the fleet actually exported
    instead of serving internal load alone.

    Returns ``None`` when the file is absent (e.g. forward years), so PJM falls
    back to zero interchange. The series is placed on the model's fixed non-leap
    8760-hour clock (Feb 29 dropped); the lone DST gap is back-filled.
    """
    path = (
        _PJM_INTERCHANGE_DIR
        / f"PJM_{year}_import_export_act_sch_interchange.csv"
    )
    if not path.exists():
        return None
    df = pd.read_csv(
        path, usecols=["datetime_beginning_ept", "actual_flow"]
    )
    ts = pd.to_datetime(
        df["datetime_beginning_ept"], format="mixed", errors="coerce"
    )
    keep = ts.notna() & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df, ts = df[keep], ts[keep]
    hoy = (
        np.array(_MONTH_START_HOUR)[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )
    # Sum actual flow across ties per hour-of-year; negate to export-positive.
    net = np.zeros(HOURS_PER_YEAR, dtype=float)
    counted = np.zeros(HOURS_PER_YEAR, dtype=bool)
    flow = df["actual_flow"].to_numpy(dtype=float)
    valid = (hoy >= 0) & (hoy < HOURS_PER_YEAR) & ~np.isnan(flow)
    np.add.at(net, hoy[valid], flow[valid])
    counted[hoy[valid]] = True
    export = -net
    # Back-fill any hour with no rows (the DST gap) from the previous hour.
    for h in np.nonzero(~counted)[0]:
        export[h] = export[h - 1] if h > 0 else 0.0
    return export


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
    fleet must serve, a net export raises it. For PJM, the internal-load
    demand-profiles series is combined with the measured tie-line net export
    from :func:`pjm_net_interchange` (PJM's import/export node), so the fleet
    generates internal load *plus* the ~40 TWh PJM actually exported. Other
    ISOs use the demand-profiles parquet alone, with no interchange.

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

    # PJM's import/export "node": add its measured net export to the demand the
    # internal fleet must serve (the demand-profiles ``raw_mw`` is internal
    # load; PJM is a large net exporter, so without this the fleet under-
    # generates by the export and mis-attributes the missing gas to coal). The
    # ERCOT path already carries interchange from its EIA-930 extract.
    if iso == "PJM":
        pjm_ix = pjm_net_interchange(year)
        if pjm_ix is not None:
            interchange = pjm_ix
            logger.info(
                "PJM net interchange applied for %d: %+.0f MW avg "
                "(export-positive)", year, float(pjm_ix.mean()),
            )

    # PJM and ERCOT allocate demand by each zone's own measured hourly shape
    # (from the PJM metered-load / ERCOT native-load files) when available, so
    # zones peak at different times; every other ISO (and these two without the
    # file) uses the static per-zone share broadcast across hours. Both are
    # (n_zones, T) weight matrices summing to 1.0 down each hour, so the rest of
    # the math is identical.
    if iso == "PJM":
        zonal_shares = pjm_zonal_load_shares(year, iso_config.zone_names)
    elif iso == "ERCOT":
        zonal_shares = ercot_zonal_load_shares(year, iso_config.zone_names)
    else:
        zonal_shares = None
    if zonal_shares is not None:
        weights = zonal_shares
    else:
        load_shares = np.array(
            [zone.load_share for zone in iso_config.zones], dtype=float
        )
        weights = np.broadcast_to(
            load_shares[:, None], (len(load_shares), HOURS_PER_YEAR)
        )
    demand = weights * raw_mw[None, :]
    if td_loss_factor > 0.0:
        demand *= 1.0 + td_loss_factor
    # Net DC-tie interchange displaces internal generation: a net import
    # (negative) lowers what the fleet must serve, a net export raises it.
    # Interchange is a transmission-level flow, so it is not loss-grossed.
    demand += weights * interchange[None, :]
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
