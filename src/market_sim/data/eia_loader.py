"""Loaders for EIA-930 hourly demand and generation series.

Reads the EIA-930 parquet extracts shipped under ``data/raw/eia-930``
and shapes them for the dispatch model: hourly ISO demand is allocated to
zones by each zone's load share, and generation profiles are returned as
normalized per-fuel distributions.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import CAISO_TAC_ZONE_WEIGHTS, HOURS_PER_YEAR
from market_sim.config.interchange_config import CAISO_IMPORT_TRANCHE_HUB
from market_sim.config.iso_configs import ISOConfig, get_iso_config
from market_sim.config.paths import (
    CALIBRATION_DIR,
    EIA_930_DIR,
    EIA_HOURLY_DIR,
    ISO_TRANSMISSION_DIR,
    RAW_DIR,
    ZONE_DEMAND_DIR,
)

logger = logging.getLogger(__name__)

# Default location of the EIA-930 parquet extracts (from the central registry).
DATA_DIR: Path = EIA_930_DIR

# PJM (metered, 20 transmission zones) and ERCOT (NP3-565-CD native load, 8
# weather zones) both publish per-zone hourly load here, one file per year.
# Used to give each model zone its *own* hourly load shape (zones peak at
# different times) instead of a single system shape scaled by a static share.
_ZONAL_LOAD_DIR: Path = ZONE_DEMAND_DIR
# Back-compat alias (PJM-specific name) for any external importer.
_PJM_ZONAL_LOAD_DIR: Path = _ZONAL_LOAD_DIR

# ERCOT weather-zone column (in ERCOT_Native_Load_<year>.xlsx) -> model
# transmission zone (the seven-zone topology in iso_configs._ercot_config).
# ERCOT has no Panhandle weather zone, so the Panhandle model zone receives no
# load here (its share stays 0.0, matching the static config); the small Lubbock
# load it would hold sits inside the WEST weather zone and lands in the West
# model zone. The EAST weather zone is its own Northeast model zone (behind the
# NE_LOB export limit). The ERCOT system-total column is dropped. Mirrors the
# aggregation in scripts/derive_load_shares.py that seeded the load_share values.
_ERCOT_LOAD_ZONE_GROUPS: dict[str, str] = {
    "COAST": "Houston",
    "EAST": "Northeast",
    "NORTH": "North",
    "NCENT": "North",
    "SCENT": "South_Central",
    "SOUTH": "South",
    "FWEST": "West",
    "WEST": "West",
}

# CAISO TAC-area actual hourly load (upload U4: OASIS SLD_FCST with
# market_run_id=ACTUAL, monthly pulls) -> model zone weights. The "CA ISO-TAC"
# system-total rows are dropped and shares are normalized over the component
# TACs. Weights themselves now live in constants.CAISO_TAC_ZONE_WEIGHTS.
_CAISO_TAC_ZONE_WEIGHTS: dict[str, dict[str, float]] = CAISO_TAC_ZONE_WEIGHTS

# NYISO settlement zone (OASIS "pal" actual-load zone names) -> model
# transmission zone. Maps the eleven NYISO load zones (A–K) onto the five
# model zones that aggregate them along the binding downstate-import interfaces
# (Central-East / Total-East cutset, UPNY-SENY, Dunwoodie-South, Long Island
# import). Both the single-letter form (A–K) and the OASIS PTID-name form are
# accepted so the parser handles whichever column the upload carries.
#
# Aggregation: A+B+C+D+E → Upstate_West  (cheap upstate generation belt)
#              F+G        → Capital_Hudson (Capital District + Hudson Valley)
#              H+I        → Lower_Hudson   (Millwood + Dunwoodie pocket)
#              J          → NYC            (New York City)
#              K          → Long_Island    (Long Island / LIPA territory)
_NYISO_LOAD_ZONE_GROUPS: dict[str, str] = {
    # Zone A — West (Niagara frontier)
    "A": "Upstate_West",
    "WEST": "Upstate_West",
    # Zone B — Genesee
    "B": "Upstate_West",
    "GENESE": "Upstate_West",
    # Zone C — Central
    "C": "Upstate_West",
    "CENTRL": "Upstate_West",
    # Zone D — North
    "D": "Upstate_West",
    "NORTH": "Upstate_West",
    # Zone E — Mohawk Valley
    "E": "Upstate_West",
    "MHK VL": "Upstate_West",
    # Zone F — Capital District
    "F": "Capital_Hudson",
    "CAPITL": "Capital_Hudson",
    # Zone G — Hudson Valley
    "G": "Capital_Hudson",
    "HUD VL": "Capital_Hudson",
    # Zone H — Millwood (Lower Hudson)
    "H": "Lower_Hudson",
    "MILLWD": "Lower_Hudson",
    # Zone I — Dunwoodie (Lower Hudson)
    "I": "Lower_Hudson",
    "DUNWOD": "Lower_Hudson",
    # Zone J — New York City
    "J": "NYC",
    "N.Y.C.": "NYC",
    # Zone K — Long Island
    "K": "Long_Island",
    "LONGIL": "Long_Island",
}

# Directory for NYISO zonal actual-load CSVs (upload U3). Absent until the
# user uploads NYISO OASIS "pal" actual-load files.
_NYISO_ZONAL_LOAD_DIR: Path = _ZONAL_LOAD_DIR / "NYISO"

# ISO-NE SMD load zone -> model transmission zone. Maps the eight ISO-NE load
# zones onto the four model zones (North = ME+NH+VT, Central = WCMASS+SEMASS+RI,
# Boston = NEMA, Connecticut = CT). The ``.H.<zone>`` hub-prefixed column
# variants the SMD downloads sometimes carry are accepted alongside the bare
# names. ``HQ_import`` is a priced node, not a load zone, so it is absent here.
_NEISO_LOAD_ZONE_GROUPS: dict[str, str] = {
    "ME": "North",
    "NH": "North",
    "VT": "North",
    "NEMA": "Boston",
    ".H.NEMA": "Boston",
    "SEMASS": "Central",
    ".H.SEMASS": "Central",
    "WCMASS": "Central",
    ".H.WCMASS": "Central",
    "RI": "Central",
    "CT": "Connecticut",
}

# Minimum measured TAC hours to derive CAISO zonal shapes from a partial-year
# upload (U4 lands month by month); below this, fall back to static shares.
_CAISO_TAC_MIN_HOURS: int = 28 * 24

# PJM's hourly actual tie-line interchange (import/export) lives here, one file
# per year. Used to add PJM's net export to the demand the internal fleet must
# serve, closing the energy-only model's largest structural gap (PJM is a large
# net exporter, ~40 TWh in 2023).
_PJM_INTERCHANGE_DIR: Path = ISO_TRANSMISSION_DIR

# Real PJM transmission zone -> model zone (the eight-zone aggregation in
# iso_configs._pjm_config). ``RTO`` is the system total and is dropped.
_PJM_LOAD_ZONE_GROUPS: dict[str, str] = {
    "CE": "PJM_ComEd",
    "AEP": "PJM_AEP_Ohio",
    "DAY": "PJM_AEP_Ohio",
    "DEOK": "PJM_AEP_Ohio",
    "OVEC": "PJM_AEP_Ohio",
    "ATSI": "PJM_ATSI",
    "AP": "PJM_West_APS",
    "DUQ": "PJM_West_APS",
    "PL": "PJM_Central_PA",
    "PN": "PJM_Central_PA",
    "ME": "PJM_Central_PA",
    "EKPC": "PJM_Central_PA",
    "DOM": "PJM_Dominion",
    "PS": "PJM_EMAAC",
    "JC": "PJM_EMAAC",
    "PE": "PJM_EMAAC",
    "DPL": "PJM_EMAAC",
    "AE": "PJM_EMAAC",
    "RECO": "PJM_EMAAC",
    "BC": "PJM_SWMAAC",
    "PEP": "PJM_SWMAAC",
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

# ISOs whose clean ``load`` dataset reconstructs the *system* demand series the
# model uses today (the EIA-930 ``<BA> hourly`` Demand, summed over the clean
# zones). Restricted to the ISOs whose model demand already comes from that same
# ``<BA> hourly`` extract: CAISO/NYISO read native zonal feeds into clean (a
# different series from the CISO/NYIS BA demand the model serves), MISO serves
# the ``MISO hourly`` extract directly (its clean feed is not rebuilt onto the
# local clock; see :data:`_ISO_LOCAL_TZ`), and PJM/SPP serve the demand-profiles
# parquet, so their clean override is left off to avoid silently swapping the
# source under the flag.
_CLEAN_DEMAND_ISOS: frozenset[str] = frozenset({"ERCOT", "NEISO"})

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


def _clean_system_demand(iso: str, year: int) -> np.ndarray | None:
    """Return the clean-backed system demand (MW) on the model clock, or ``None``.

    Sums the clean ``load`` zones per hour into the ISO-wide system series the
    raw demand path produces. Returns ``None`` (caller falls back to the raw
    extract) when the ISO is unsupported, the clean partition is absent, or the
    reconstructed series is not a clean, gap-free full year — matching the strict
    8760-hour requirement of :func:`_eia_hourly_frame`.
    """
    if iso not in _CLEAN_DEMAND_ISOS:
        return None
    rows = _read_clean_iso_year("load", iso, year)
    if rows is None:
        return None
    system = (
        rows.groupby("interval_start_utc", as_index=False)["load_mw"]
        .sum()
        .sort_values("interval_start_utc")
    )
    mw = system["load_mw"].to_numpy(dtype=float)
    if mw.shape[0] != HOURS_PER_YEAR or np.isnan(mw).any():
        return None
    return mw


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
    loc = pd.DatetimeIndex(df["Local time"])
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


def measured_monthly_hydro(iso: str, year: int) -> np.ndarray | None:
    """Return EIA-930 measured conventional-hydro net generation by month.

    Twelve-entry vector (MWh, index 0 = January) of the ISO's BA ``NG: WAT``
    (water = conventional hydro) summed by local calendar month for ``year``.
    Pumped storage (``NG: PS``) is deliberately excluded — it is a storage
    resource, not inflow hydro. Returns ``None`` when the ISO has no per-BA
    hourly extract, the year is not a clean 8760-hour series, the ``NG: WAT``
    column is absent, or the year's hydro is all-zero/missing.

    Used to repin an incomplete-EIA-923 hydro budget to its measured monthly
    total — see :func:`market_sim.data.hydro.load_hydro_budget`
    ``monthly_target_mwh``.
    """
    ba = _ISO_TO_HOURLY_BA.get(iso)
    if ba is None:
        return None
    # Use the gap-filling frame, not the strict 8760 one: this helper exists to
    # repin an *incomplete* EIA-923 vintage (notably 2025), and the current-year
    # EIA-930 extract is itself often a few hours short of a clean local year
    # (CISO 2025 is 8751 local-year rows). The strict loader rejects that and
    # the repin silently no-ops on the very year it is meant to fix; the filled
    # loader bridges the <=72h hole. The inserted gap rows carry NaT dates and
    # NaN NG: WAT, so the per-month nansum below ignores them.
    frame = _eia_hourly_frame_filled(ba, year)
    if frame is None or "NG: WAT" not in frame.columns:
        return None
    months = frame["Local date"].dt.month.to_numpy()
    wat = pd.to_numeric(frame["NG: WAT"], errors="coerce").to_numpy()
    out = np.array([np.nansum(wat[months == m]) for m in range(1, 13)], dtype=float)
    return out if out.sum() > 0.0 else None


def climatological_monthly_hydro(
    iso: str, years: "tuple[int, ...] | list[int] | None" = None
) -> np.ndarray | None:
    """Return the normal-water-year monthly hydro climatology (MWh).

    Twelve-entry vector (index 0 = January) of the per-month mean of the
    measured EIA-930 ``NG: WAT`` (conventional hydro) net generation across
    ``years`` — the forecast analogue of :func:`measured_monthly_hydro`. A
    single historical year is a particular wet/dry draw; averaging several
    years gives a *normal water year* the forecast hydro budget level can be
    built from, then scaled by a wet/dry scenario lever
    (:func:`market_sim.data.hydro.forecast_monthly_hydro`). Years the ISO does
    not cover (no per-BA extract, not a usable hydro year) are skipped, so a
    short extract still yields a climatology from whatever years are present.

    Args:
        iso: ISO identifier, e.g. ``"CAISO"``.
        years: Historical years to average. ``None`` (default) uses
            :data:`market_sim.config.constants.HYDRO_CLIMATOLOGY_YEARS`.

    Returns:
        The ``(12,)`` mean monthly hydro net generation in MWh, or ``None``
        when no year in the window has usable measured hydro for ``iso``.
    """
    if years is None:
        from market_sim.config.constants import HYDRO_CLIMATOLOGY_YEARS

        years = HYDRO_CLIMATOLOGY_YEARS
    monthly = [measured_monthly_hydro(iso, int(y)) for y in years]
    monthly = [m for m in monthly if m is not None]
    if not monthly:
        return None
    return np.vstack(monthly).mean(axis=0)


def measured_interchange_envelope(
    iso: str, year: int, hours: int, percentile: float = 90.0
) -> tuple[np.ndarray, np.ndarray] | None:
    """Return the measured month×hour-of-day net-import/export envelope (MW).

    The priced-interchange node clears a near-constant schedule because its
    tranche capacities are available every hour. Real CAISO interchange instead
    follows a strong diurnal/seasonal duck: it imports overnight (PNW hydro /
    desert-SW gas) and **exports** the midday solar glut. This returns, per hour
    of the run horizon, the ``percentile`` of measured EIA-930 ``Total
    interchange`` for that hour's (month, hour-of-day) bucket, split into the
    net-import and net-export envelopes (EIA sign: positive = net export):

        import_cap[t] = P_pctile( max(0, -interchange) | month(t), hod(t) )
        export_cap[t] = P_pctile( max(0, +interchange) | month(t), hod(t) )

    The caller scales the node's import-tranche availability and export-sink
    floor by these envelopes (relative to the static tranche totals), so the
    node can only import up to roughly its historical capability in that
    period and can export the midday surplus — the price still clears in merit
    order *within* the envelope, so this adds the measured temporal shape
    without pinning the flow or introducing any fitted constant. ``percentile``
    near the top of the distribution (default 90) keeps headroom above the
    median so price, not the cap, sets the typical hour.

    Returns ``(import_cap, export_cap)``, each ``(hours,)`` MW, or ``None`` when
    the ISO has no BA hourly extract or the year is not covered (a forecast
    year), in which case the caller leaves the static node unshaped.
    """
    ba = _ISO_TO_HOURLY_BA.get(iso)
    if ba is None:
        return None
    frame = _eia_hourly_frame_filled(ba, year)
    if frame is None or "Total interchange" not in frame.columns:
        return None
    local = pd.DatetimeIndex(frame["Local time"])
    month = local.month.to_numpy(dtype=float)
    hod = local.hour.to_numpy(dtype=float)
    ti = pd.to_numeric(frame["Total interchange"], errors="coerce").to_numpy()
    imp = np.where(np.isfinite(ti), np.clip(-ti, 0.0, None), np.nan)
    exp = np.where(np.isfinite(ti), np.clip(ti, 0.0, None), np.nan)

    # Per (month, hour-of-day) bucket percentile. Empty buckets stay 0.
    imp_tab = np.zeros((12, 24))
    exp_tab = np.zeros((12, 24))
    for m in range(1, 13):
        for h in range(24):
            sel = (month == m) & (hod == h)
            if not sel.any():
                continue
            ii = imp[sel]
            ee = exp[sel]
            ii = ii[np.isfinite(ii)]
            ee = ee[np.isfinite(ee)]
            if ii.size:
                imp_tab[m - 1, h] = np.percentile(ii, percentile)
            if ee.size:
                exp_tab[m - 1, h] = np.percentile(ee, percentile)

    # Map the (month, hod) tables onto the run horizon. Row 0 of the dispatch
    # is the first local hour of the year (see _eia_hourly_frame), so a plain
    # local clock reproduces that index.
    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    rm = clock.month.to_numpy() - 1
    rh = clock.hour.to_numpy()
    return imp_tab[rm, rh], exp_tab[rm, rh]


def measured_gas_floor_profile(
    iso: str, year: int, hours: int, percentile: float = 50.0
) -> np.ndarray | None:
    """Return the measured month×hour-of-day EIA-930 ``NG: NG`` profile (MW).

    For each hour of the run horizon, the ``percentile`` of measured EIA-930
    natural-gas net generation (``NG: NG``) for that hour's (month,
    hour-of-day) bucket. Used as the magnitude of the CAISO Resource-Adequacy
    must-offer minimum-commitment floor (see
    :func:`market_sim.model.transmission.inject_caiso_gas_commitment_floor`):
    holding the gas fleet online midday at (a fraction of) this measured
    profile makes the model *long* midday, so its surplus exports/curtails at
    ~$0 — reproducing CAISO's collapsed spring-midday LMP.

    The (month, hour-of-day) bucketing follows
    :func:`measured_interchange_envelope`: a measured diurnal/seasonal shape
    with no fitted constant, robust to leap-year / missing hours (gap rows
    carry NaN ``NG: NG`` and drop out of each bucket). The median (default
    percentile) is the *typical* gas level RA commitment holds the fleet at;
    the caller scales it by ``config.caiso_gas_floor_frac``.

    Note ``NG: NG`` is the EIA-930 gas figure, which for CISO silently absorbs
    geothermal/biomass (EIA-930 reports neither for CISO); that inflation is
    irrelevant here — this profile shapes a *floor*, not a benchmark, and gas
    generation is still validated against EIA-923, not this series.

    Returns ``(hours,)`` MW, or ``None`` when the ISO has no BA hourly extract,
    the ``NG: NG`` column is absent, or the year is uncovered (a forecast
    year), in which case the caller leaves the fleet unfloored (byte-identical).
    """
    ba = _ISO_TO_HOURLY_BA.get(iso)
    if ba is None:
        return None
    frame = _eia_hourly_frame_filled(ba, year)
    if frame is None or "NG: NG" not in frame.columns:
        return None
    local = pd.DatetimeIndex(frame["Local time"])
    month = local.month.to_numpy(dtype=float)
    hod = local.hour.to_numpy(dtype=float)
    ng = pd.to_numeric(frame["NG: NG"], errors="coerce").to_numpy()

    tab = np.zeros((12, 24))
    for m in range(1, 13):
        for h in range(24):
            sel = (month == m) & (hod == h)
            v = ng[sel]
            v = v[np.isfinite(v)]
            if v.size:
                tab[m - 1, h] = np.percentile(v, percentile)

    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    rm = clock.month.to_numpy() - 1
    rh = clock.hour.to_numpy()
    out = tab[rm, rh]
    return out if np.any(out > 0.0) else None


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

    # Standard per-zone file: {iso}_zone_temp_daily.csv
    path = RAW_DIR / f"{iso_l}-weather" / f"{iso_l}_zone_temp_daily.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["date"])
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
    (produced by ``scripts/curate_weather.py``), filtered to *zone* when given.
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


# CAISO priced-import tranche -> WECC neighbor hub whose measured intertie LMP is
# the tranche's real delivered energy cost. The PNW blocks (firm hydro + Mid-C
# shoulder) clear against the Malin / COI-PDCI ties; the desert-SW blocks (solar +
# Palo Verde nuclear, then SW gas) clear against the Palo Verde / Path-46 ties.
# WECC_scarcity (west-wide peak economy energy) also tracks Palo Verde at its peak.
# Single source of truth lives in constants (CAISO_IMPORT_TRANCHE_HUB) so this
# loader and the per-hub builder/injector (transmission.py) cannot drift apart.
_CAISO_IMPORT_TRANCHE_HUB: dict[str, str] = CAISO_IMPORT_TRANCHE_HUB


def measured_import_hub_prices(
    iso: str, year: int, hours: int
) -> dict[str, np.ndarray] | None:
    """Return each CAISO import tranche's measured hourly neighbor-hub price.

    Reads the measured WECC intertie scheduling-point LMP
    (``wecc_intertie_lmp_hourly_<ISO>.parquet`` under the calibration source
    dir: columns ``year``, ``hour`` [0..hours-1, local calendar], ``hub``
    [``MALIN`` / ``PALOVRDE``], ``price`` [$/MWh, the delivered nodal LMP =
    energy + congestion + loss (MCE+MCC+MCL) of the CAISO intertie LMP, GHG
    component excluded]) and maps each hub to the import tranches it prices via
    :data:`_CAISO_IMPORT_TRANCHE_HUB`. The congestion/loss components are what
    make MALIN (PNW) and PALOVRDE (desert-SW) differ (the energy component alone
    is system-wide identical at every WECC node).

    These are the *actual delivered energy cost of the imported power* — the
    neighbor hub's own marginal price at the CA border, which crashes in the
    spring PNW runoff (the real reason CAISO Apr/May RT is ~$11-14) and can go
    negative in the desert-SW solar glut (the real reason CAISO has ~870
    negative-price hours). They replace the static, bundle-fitted ladder in
    ``IMPORT_TRANCHES["CAISO"]`` when ``config.caiso_import_hub_prices`` is on;
    see :func:`market_sim.model.transmission.inject_caiso_import_hub_prices`.
    The price is the delivered nodal LMP (energy+congestion+loss, GHG excluded);
    the per-tranche CARB border carbon is re-added by the injector (so a clean
    hydro/solar tranche still pays none), matching the static-ladder carbon
    treatment.

    Returns ``{tranche_name: (hours,) $/MWh}`` for every tranche whose hub has a
    measured series, or ``None`` when the ISO is not CAISO, the parquet is
    absent (forecast years / before the OASIS fetch lands), or the year is
    uncovered — in which case the caller keeps the static ladder (byte-identical).
    """
    if iso.upper() != "CAISO":
        return None
    path = CALIBRATION_DIR / f"wecc_intertie_lmp_hourly_{iso.upper()}.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    frame = frame[frame["year"] == year]
    if frame.empty:
        return None

    out: dict[str, np.ndarray] = {}
    for hub, sub in frame.groupby("hub"):
        series = sub.sort_values("hour")
        # Interpolate the isolated DST spring-forward gap (1 interior NaN on the
        # fixed non-leap calendar that every hourly series carries); ``limit=2``
        # leaves a genuine multi-week gap (2023 Jan-Feb, aged out of OASIS
        # retention) NaN for the reference-formula fill below.
        price = (
            pd.to_numeric(series["price"], errors="coerce")
            .interpolate(limit=2)
            .to_numpy(dtype=float)
        )
        if price.shape[0] < hours:
            continue  # incomplete hub series — leave its tranches on the ladder
        price = price[:hours].copy()
        gap = ~np.isfinite(price)
        if gap.any():
            # Hybrid gap-fill for a bulk retention gap (2023 Jan-Feb: ~1.4k
            # hours aged out of OASIS before the fetch): fill the missing hours
            # with the corridor's FORWARD reference price ((HH + basis) × HR ×
            # neighbor load-shape) — the sanctioned forward-native analogue of
            # this measured series (rule #14: a reconciled fill of real data
            # over discarding ten measured months). Bounded to ≤25% of the
            # year so a mostly-missing series still falls back to the ladder;
            # the filled hours are the same hours absent from the actual-LMP
            # benchmark, so C3 price scoring never reads the filled values.
            if gap.mean() > 0.25:
                continue
            from market_sim.config.interchange_config import (
                CAISO_PER_HUB_NEIGHBORS,
            )
            from market_sim.data.neighbor_price import caiso_hub_reference_price

            spec = next(
                (s for s in CAISO_PER_HUB_NEIGHBORS.values() if s.hub == hub),
                None,
            )
            ref = (
                caiso_hub_reference_price(spec, year, hours)
                if spec is not None
                else None
            )
            if ref is None or not np.all(np.isfinite(ref[gap])):
                continue  # no forward fill available — leave on the ladder
            price[gap] = ref[gap]
        for tranche, mapped_hub in _CAISO_IMPORT_TRANCHE_HUB.items():
            if mapped_hub == hub:
                out[tranche] = price
    return out or None


def measured_miso_pjm_border_prices(
    iso: str, year: int, hours: int
) -> np.ndarray | None:
    """Return measured hourly PJM border-hub DA LMP for MISO's PJM import seam.

    Reads ``pjm_border_lmp_hourly_MISO.parquet`` (columns ``year``, ``hour``
    [0..8759, MISO Central-time calendar], ``hub`` [``PJM_WEST``], ``price``
    [$/MWh, DA total LMP = energy + congestion + loss]) built by
    ``scripts/build_pjm_border_lmp_miso.py`` from PJM Data Miner hub exports.
    ``PJM_WEST`` is the equal-weight mean of the three MISO-facing PJM gen hubs
    (CHICAGO GEN / AEP GEN / ATSI GEN), the same border decomposition the
    ``MISO_PJM_BORDER_HR_BY_YEAR`` derivation uses.

    Returns ``(hours,)`` array of $/MWh, or ``None`` when the ISO is not MISO,
    the parquet is absent, or the year is uncovered — in which case the caller
    keeps the gas × HR ladder (byte-identical).
    """
    if iso.upper() != "MISO":
        return None
    path = CALIBRATION_DIR / "pjm_border_lmp_hourly_MISO.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    frame = frame[(frame["year"] == year) & (frame["hub"] == "PJM_WEST")]
    if frame.empty:
        return None
    series = frame.sort_values("hour")
    price = (
        pd.to_numeric(series["price"], errors="coerce")
        .interpolate(limit=2)
        .to_numpy(dtype=float)
    )
    if price.shape[0] < hours or not np.all(np.isfinite(price[:hours])):
        return None
    return price[:hours]


def measured_corridor_flow_envelope(
    iso: str,
    year: int,
    hours: int,
    percentile: float | None = None,
    direction: str = "import",
) -> dict[str, np.ndarray] | None:
    """Return each CAISO import corridor's measured net-import deliverability cap.

    For each WECC import corridor (``WECC_PNW`` = COI/Path-66 into NP15,
    ``WECC_DSW`` = Path-46/WOR into SP15), returns the per-hour ceiling on net
    import (MW), built as the per-(month × hour-of-day) ``percentile`` of the
    MEASURED net import on that corridor from EIA-930 BA-to-BA interchange
    (``data/raw/eia-930-interchange/CISO interchange hourly.parquet``; columns
    ``diba``, ``mw`` [EIA sign: + = CISO exports to the DIBA], ``local_time``).
    Each CISO↔DIBA pair is summed into its corridor via
    :data:`~market_sim.config.interchange_config.CAISO_CORRIDOR_DIBA`, then
    ``net_import = -sum(interchange over the corridor's DIBAs)``.

    This is an ATC proxy: the corridor's *deliverable* transfer ceiling (the
    physical line rating net of parallel commitments and the neighbor's own
    diurnal length), which collapses midday when the desert-SW / Pacific-NW are
    themselves long on solar. The caller applies it as a one-sided hourly upper
    bound on the corridor link's import-direction flow, so the LP still clears
    its merit order *below* the ceiling — a capability limit, not a flow pinned
    to the residual (rule #12). ``percentile`` defaults to
    :data:`~market_sim.config.interchange_config.CAISO_CORRIDOR_FLOW_PERCENTILE` (95).

    Hours are mapped onto the model's fixed non-leap calendar
    (:func:`~market_sim.data.fleet._hour_to_month_index` for the month, ``hour %
    24`` for the hour-of-day), the same calendar the LP and the hydro budgets
    use, so the cap aligns hour-for-hour with the dispatch.

    Returns ``{corridor_zone: (hours,) MW}`` for both corridors, or ``None`` when
    the ISO is not CAISO, the parquet is absent, or the year is uncovered (a
    forecast year) — in which case the caller leaves the corridors uncapped
    (byte-identical).

    With ``direction="export"`` the same machinery instead returns each
    corridor's measured net-*export* deliverability ceiling (the per-(month ×
    hour-of-day) ``percentile`` of measured net export = −net import, clipped at
    0). It is the symmetric counterpart of the import ceiling: just as the import
    ATC collapses midday when the WECC neighbors are long on solar, the export
    ATC collapses in the evening ramp when the neighbors are themselves short
    (their own peak), so a corridor that reliably net-imports in an evening
    (month, hod) bucket caps export there at ~0 — forbidding the LP's unphysical
    evening wheel-out of cheap CA gas. Like the import ceiling it is a smoothed
    capability envelope the LP clears *below*, not the hourly residual flow
    (rule #12). Applied as the reverse-direction floor of the corridor's
    asymmetric interface group (see
    :func:`~market_sim.model.transmission.build_caiso_corridor_flow_groups`).
    """
    if direction not in ("import", "export"):
        raise ValueError(f"direction must be 'import' or 'export', got {direction!r}")
    if iso.upper() != "CAISO":
        return None
    from market_sim.config.interchange_config import (
        CAISO_CORRIDOR_DIBA,
        CAISO_CORRIDOR_FLOW_PERCENTILE,
    )
    from market_sim.data.fleet import _hour_to_month_index

    pct = CAISO_CORRIDOR_FLOW_PERCENTILE if percentile is None else float(percentile)
    path = RAW_DIR / "eia-930-interchange" / "CISO interchange hourly.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    local = pd.DatetimeIndex(frame["local_time"])
    frame = frame[local.year == year]
    if frame.empty:
        return None
    local = pd.DatetimeIndex(frame["local_time"])
    corridor = frame["diba"].astype(str).map(CAISO_CORRIDOR_DIBA)
    work = pd.DataFrame(
        {
            "corridor": corridor.to_numpy(),
            "month": local.month.to_numpy(),
            "hod": local.hour.to_numpy(),
            "ts": local.to_numpy(),
            "mw": pd.to_numeric(frame["mw"], errors="coerce").to_numpy(),
        }
    ).dropna(subset=["corridor", "mw"])
    # Net import per corridor per timestamp = -sum(interchange over its DIBAs).
    per_ts = work.groupby(["corridor", "ts", "month", "hod"], observed=True)["mw"].sum()
    per_ts = (-per_ts).reset_index(name="net_import")

    rm = _hour_to_month_index(hours) + 1  # 1-based month per model hour
    rh = np.arange(hours) % 24
    out: dict[str, np.ndarray] = {}
    for zone in ("WECC_PNW", "WECC_DSW"):
        sub = per_ts[per_ts["corridor"] == zone]
        if sub.empty:
            continue
        tab = np.full((12, 24), np.nan)
        for (m, h), g in sub.groupby(["month", "hod"], observed=True):
            vals = g["net_import"].to_numpy()
            if direction == "export":
                vals = -vals  # net export = -net import; p95 export deliverability
            tab[m - 1, h] = np.percentile(vals, pct)
        # Fill any empty (month, hod) bucket with that month's max over hours
        # (a conservative ceiling), then the global max, so the cap is always
        # finite and never tighter than a populated neighbour.
        for m in range(12):
            row = tab[m]
            if np.all(np.isnan(row)):
                continue
            tab[m] = np.where(np.isnan(row), np.nanmax(row), row)
        if np.any(np.isnan(tab)):
            tab = np.where(np.isnan(tab), np.nanmax(tab), tab)
        # Clip at 0: the cap bounds net flow in ``direction``; a (month, hod)
        # bucket whose p95 is negative (the corridor reliably runs the OTHER way
        # then — e.g. import p95 < 0 where the PNW corridor net-exports midday, or
        # export p95 < 0 where a corridor net-imports the evening ramp) caps that
        # direction at zero, never forcing the reverse flow.
        out[zone] = np.clip(tab[rm - 1, rh], 0.0, None)
    return out or None


def caiso_solar_fraction(year: int, hours: int) -> np.ndarray | None:
    """Return CISO's hourly solar penetration (solar / demand) on the LP clock.

    A forward driver for the CAISO corridor ATC derate
    (:func:`market_sim.model.transmission.forward_corridor_atc_envelope`): the
    region's midday solar share, which collapses the deliverable WECC import
    transfer (the desert-SW / Pacific-NW are themselves long on solar midday).
    Built from the EIA-930 CISO extract (``NG: SUN`` / ``Demand``) on the model's
    local 8760 clock, so it aligns hour-for-hour with the dispatch. The desert-SW
    shares CAISO's solar resource and time zone, so the CISO share proxies the
    corridor's midday saturation; it responds to a changed forecast solar build,
    unlike the measured corridor flow.

    Returns a ``(hours,)`` fraction clipped to ``[0, 1]``, or ``None`` when the
    CISO extract is absent / too short (a forecast year with no extract — the
    caller then leaves the corridor uncapped).
    """
    frame = _eia_hourly_frame_filled("CISO", year)
    if frame is None or "Demand" not in frame.columns:
        return None
    demand = pd.to_numeric(frame["Demand"], errors="coerce")
    solar = pd.to_numeric(frame.get("NG: SUN"), errors="coerce").fillna(0.0)
    demand = demand.interpolate().bfill().ffill().to_numpy(dtype=float)
    solar = solar.to_numpy(dtype=float)
    if demand.shape[0] < hours or np.isnan(demand).any():
        return None
    demand = demand[:hours]
    solar = solar[:hours]
    with np.errstate(divide="ignore", invalid="ignore"):
        frac = np.where(demand > 0.0, solar / demand, 0.0)
    return np.clip(np.nan_to_num(frac, nan=0.0), 0.0, 1.0)


def measured_seam_import_envelope(
    iso: str,
    year: int,
    hours: int,
    percentile: float | None = None,
    direction: str = "import",
) -> dict[str, np.ndarray] | None:
    """Return each priced seam's measured net-import deliverability cap (MW).

    The MISO analogue of :func:`measured_corridor_flow_envelope`. For each
    reference-price seam in :data:`~market_sim.config.interchange_config.MISO_SEAM_DIBA`
    (``PJM`` / ``SPP`` / ``South``), returns the per-hour ceiling on net import
    (MW), built as the per-(month × hour-of-day) ``percentile`` of the MEASURED
    net import summed over that seam's EIA-930 Directly-Interconnected BAs
    (``data/raw/eia-930-interchange/<BA> interchange hourly.parquet``; columns
    ``diba``, ``mw`` [EIA sign: + = ISO exports to the DIBA], ``local_time``).
    Each seam's net import is ``−sum(mw over its DIBAs)`` per timestamp.

    This is a transfer-capability / ATC proxy: the seam's *deliverable* net
    import in that period — congestion- and firm-rights-limited below the
    nameplate interface rating, and naturally near zero (or capped to zero) on a
    seam the ISO actually net-exports over (SPP, South). The caller applies it as
    a one-sided hourly upper bound on that seam's import bands, so the LP still
    clears its merit order *below* the ceiling and the export direction stays
    economic — a capability limit, not a flow pinned to the residual (claude.md
    rules #1/#12). ``percentile`` defaults to
    :data:`~market_sim.config.constants.MISO_SEAM_FLOW_PERCENTILE` (90).

    Hours map onto the model's fixed non-leap calendar
    (:func:`~market_sim.data.fleet._hour_to_month_index` for the month, ``hour %
    24`` for the hour-of-day), the same calendar the LP uses, so the cap aligns
    hour-for-hour with the dispatch. Leap-day samples fold into their (month,
    hour-of-day) buckets and never reach the dispatch clock.

    Returns ``{seam_name: (hours,) MW}`` for every seam with measured data, or
    ``None`` when the ISO has no seam-DIBA map, the parquet is absent, or the
    year is uncovered (a forecast year) — in which case the caller leaves the
    seams uncapped (byte-identical).

    With ``direction="export"`` the same machinery instead returns each seam's
    measured net-*export* deliverability ceiling (the per-(month × hour-of-day)
    ``percentile`` of measured net export = −net import, clipped at 0). It is the
    symmetric counterpart of the import ceiling: just as the import cap clips a
    net-importing seam, the export ceiling caps a seam's deliverable net export —
    so the eastern PJM seam (which MISO reliably net-*imports* over) caps export
    at ~0, forbidding the LP's unphysical export of cheap MISO coal back over the
    PJM border, while the southern (TVA) and SPP seams keep their measured ~GW of
    export headroom. Like the import ceiling it is a smoothed capability envelope
    the LP clears *below*, not the hourly residual flow (rules #1/#12). Applied
    by :func:`~market_sim.model.transmission.inject_miso_seam_flow_limit` as the
    reverse-direction floor (raised ``min_gen`` lower bound) on each seam's
    negative-output export bands.
    """
    if direction not in ("import", "export"):
        raise ValueError(f"direction must be 'import' or 'export', got {direction!r}")
    from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE
    from market_sim.config.interchange_config import MISO_SEAM_DIBA
    from market_sim.data.fleet import _hour_to_month_index

    seam_diba = {"MISO": MISO_SEAM_DIBA}.get(iso.upper())
    if not seam_diba:
        return None
    pct = MISO_SEAM_FLOW_PERCENTILE if percentile is None else float(percentile)
    ba = _ISO_TO_HOURLY_BA.get(iso.upper())
    if ba is None:
        return None
    path = RAW_DIR / "eia-930-interchange" / f"{ba} interchange hourly.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    local = pd.DatetimeIndex(frame["local_time"])
    frame = frame[local.year == year]
    if frame.empty:
        return None
    local = pd.DatetimeIndex(frame["local_time"])
    # Map each DIBA to its seam; rows whose DIBA is in no seam (e.g. MHEB, the
    # firm-hydro block) drop out.
    diba_to_seam = {d: s for s, dibas in seam_diba.items() for d in dibas}
    seam = frame["diba"].astype(str).map(diba_to_seam)
    work = pd.DataFrame(
        {
            "seam": seam.to_numpy(),
            "month": local.month.to_numpy(),
            "hod": local.hour.to_numpy(),
            "ts": local.to_numpy(),
            "mw": pd.to_numeric(frame["mw"], errors="coerce").to_numpy(),
        }
    ).dropna(subset=["seam", "mw"])
    # Net import per seam per timestamp = −sum(interchange over its DIBAs).
    per_ts = work.groupby(["seam", "ts", "month", "hod"], observed=True)["mw"].sum()
    per_ts = (-per_ts).reset_index(name="net_import")

    rm = _hour_to_month_index(hours) + 1  # 1-based month per model hour
    rh = np.arange(hours) % 24
    out: dict[str, np.ndarray] = {}
    for name in seam_diba:
        sub = per_ts[per_ts["seam"] == name]
        if sub.empty:
            continue
        tab = np.full((12, 24), np.nan)
        for (m, h), g in sub.groupby(["month", "hod"], observed=True):
            vals = g["net_import"].to_numpy()
            if direction == "export":
                vals = -vals  # net export = -net import; pXX export deliverability
            tab[m - 1, h] = np.percentile(vals, pct)
        # Fill any empty (month, hod) bucket with that month's max over hours,
        # then the global max, so the cap is always finite.
        for m in range(12):
            row = tab[m]
            if np.all(np.isnan(row)):
                continue
            tab[m] = np.where(np.isnan(row), np.nanmax(row), row)
        if np.any(np.isnan(tab)):
            tab = np.where(np.isnan(tab), np.nanmax(tab), tab)
        # Clip at 0: the cap bounds net flow in ``direction``; a bucket whose pXX
        # is negative (the seam reliably runs the OTHER way then — net import on a
        # net-exporting seam, or net export on the net-importing PJM seam) caps
        # that direction at zero, never forcing the reverse flow. The opposite
        # direction is left to the priced seam's own economics.
        out[name] = np.clip(tab[rm - 1, rh], 0.0, None)
    return out or None


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
    # Interpolate isolated missing meter hours (e.g. 2025 has 48 NaN demand
    # hours). Falling back to the demand-profiles parquet here is NOT
    # equivalent: that series is hour-shifted relative to this frame, which
    # desynchronizes demand from the wind/solar/benchmark series read off the
    # same rows (the 2025 backcast served its evening demand peak ~2h after
    # sunset, manufacturing scarcity).
    demand = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
    interchange = (
        frame["Total interchange"].interpolate().bfill().ffill().to_numpy(dtype=float)
    )
    if np.isnan(demand).any() or np.isnan(interchange).any():
        return None
    return demand, interchange


def _load_caiso_hourly_demand(year: int) -> np.ndarray | None:
    """Return CAISO hourly metered demand (MW) for a year, or ``None``.

    Reads the EIA-930 ``CISO hourly`` extract so demand shares the
    chronological clock of the wind/solar/benchmark series read off the same
    rows (the ERCOT precedent: the demand-profiles parquet is hour-shifted
    relative to this frame, which desynchronizes demand from the renewable
    series — fatal for CAISO's duck curve). Isolated missing meter hours are
    interpolated.

    **Net-load convention (playbook §8.1):** this series is metered at the
    transmission level and is already net of CAISO's ~15+ GW of
    behind-the-meter PV; backcasts model only front-of-meter resources
    against it. Unlike ERCOT, the BA's net interchange is *not* folded into
    demand here: CAISO imports are modeled as supply by the ``WECC_import``
    node's priced pseudo-generators
    (:func:`market_sim.model.transmission.build_wecc_import_generators`), so
    netting interchange into demand would double count them.

    Returns ``None`` when no usable full-year frame is available, signaling
    the caller to fall back to the per-ISO demand-profiles parquet.
    """
    frame = _eia_hourly_frame_filled("CISO", year)
    if frame is None:
        return None
    demand = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
    if np.isnan(demand).any():
        return None
    return demand


def _load_nyiso_hourly_demand(year: int) -> np.ndarray | None:
    """Return NYISO hourly metered demand (MW) for a year, or ``None``.

    Reads the EIA-930 ``NYIS hourly`` extract so demand shares the
    chronological clock of the wind/solar/benchmark series read off the same
    rows (the ERCOT/CAISO precedent: the demand-profiles parquet is
    hour-shifted relative to this frame). Isolated missing meter hours are
    interpolated.

    **Net-load convention (playbook §8.1):** this series is metered at the
    transmission level and is already net of behind-the-meter PV/storage/DER.
    Backcasts model only front-of-meter resources against it. NY's BTM wedge
    is smaller than CAISO's (~15+ GW) but growing downstate — document per
    backcast year. Unlike ERCOT, net interchange is *not* folded into demand
    here: NYISO imports are modeled as a calibrated priced node (P9 /
    playbook §8.2), so netting interchange into demand would double count them.

    Returns ``None`` when no usable full-year frame is available, signaling
    the caller to fall back to the per-ISO demand-profiles parquet.
    """
    frame = _eia_hourly_frame_filled("NYIS", year)
    if frame is None:
        return None
    demand = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
    if np.isnan(demand).any():
        return None
    return demand


def _load_neiso_hourly_demand(year: int) -> np.ndarray | None:
    """Return NEISO hourly metered demand (MW) for a year, or ``None``.

    Reads the EIA-930 ``ISNE hourly`` extract so demand shares the
    chronological clock of the wind/solar/benchmark series read off the same
    rows (same rationale as CAISO/NYISO). Isolated missing meter hours are
    interpolated. This keeps demand aligned with the measured net-interchange
    schedule (:func:`neiso_net_interchange`) drawn from the same ISNE frame.

    **Net-load convention (playbook §8.1):** EIA-930 ISNE demand is metered
    at the transmission level and is already net of behind-the-meter PV
    (material in MA/CT). Backcasts model only front-of-meter resources
    against it; do not add a BTM solar profile on the supply side.

    Returns ``None`` when no usable full-year frame is available, signaling
    the caller to fall back to the per-ISO demand-profiles parquet.
    """
    frame = _eia_hourly_frame_filled("ISNE", year)
    if frame is None:
        return None
    demand = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
    if np.isnan(demand).any():
        return None
    return demand


def _load_miso_hourly_demand(year: int) -> np.ndarray | None:
    """Return MISO hourly metered demand (MW) for a year, or ``None``.

    Reads the EIA-930 ``MISO hourly`` extract's ``Demand`` column off the same
    :func:`_eia_hourly_frame_filled` frame the MISO renewable CF series are
    drawn from, so demand shares the renewables' chronological clock (row k =
    local hour k of the year). The per-ISO demand-profiles parquet, by contrast,
    stamps MISO on UTC (its row 0 is the first *UTC* hour), which lags the local
    renewable/Demand clock by ~5h (CDT) to ~6h (CST). Sourcing both demand and
    renewables off this one frame removes that offset by construction — no tz
    assumption, the frame's own ``Local time`` column fixes the clock and DST.
    MISO is therefore handled here rather than via the clean-demand override
    (its clean feed is not reconstructed onto the local clock; see
    :data:`_ISO_LOCAL_TZ`). Isolated missing meter hours are interpolated.

    The level is unchanged from the demand-profiles series (same EIA-930 MISO
    BA Demand: identical annual energy and peak); only the hour alignment moves.

    Returns ``None`` when no usable full-year frame is available, signaling the
    caller to fall back to the per-ISO demand-profiles parquet.
    """
    frame = _eia_hourly_frame_filled("MISO", year)
    if frame is None:
        return None
    demand = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
    if np.isnan(demand).any():
        return None
    return demand


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


def load_zonal_shares(iso: str, year: int, zone_names: list[str]) -> np.ndarray | None:
    """Load zonal load share fractions from clean Parquet.

    Reads the curated ``zonal-shares`` dataset produced by
    ``scripts/curate_zonal_shares.py`` and returns a
    ``(n_zones, HOURS_PER_YEAR)`` array of hourly fractional load shares, where
    each column sums to 1.0 across zones. Returns ``None`` when the clean
    Parquet has not been curated yet (the caller falls back to the static
    per-zone ``load_share``).

    Args:
        iso: ISO code (e.g. ``"ERCOT"``).
        year: Calendar year.
        zone_names: Model zone names in the order the caller expects (must
            match the zones written by the curation script).

    Returns:
        ``(n_zones, HOURS_PER_YEAR)`` float64 array, or ``None`` if the clean
        Parquet for this ISO-year is absent.
    """
    seam = _read_clean_seam()
    if seam is None:
        return None
    read_clean, clean_exists = seam
    if not clean_exists("zonal-shares", iso=iso, year=year):
        return None
    try:
        df = read_clean("zonal-shares", iso=iso, year=year, validate=False)
    except Exception as exc:
        logger.warning("zonal-shares read failed for %s %d: %s", iso, year, exc)
        return None
    pivot = df.pivot(index="hour", columns="zone", values="share")
    pivot = pivot.reindex(columns=zone_names, fill_value=0.0)
    shares = pivot.to_numpy(dtype=float).T
    # Stale-parquet guard: the reindex fills a missing zone column with 0.0,
    # so a renamed zone silently gets ZERO load from a parquet curated under
    # the old names (the exact hazard of the MISO 3→6-zone rename). A zone
    # that legitimately carries no load (ERCOT Panhandle, import nodes) has
    # static load_share == 0; any zone with a positive static share must have
    # a live column, so an all-zero row there is a hard error, never a silent
    # degradation.
    from market_sim.config.iso_configs import get_iso_config

    static_share = {z.name: z.load_share for z in get_iso_config(iso).zones}
    dead = [
        z
        for i, z in enumerate(zone_names)
        if static_share.get(z, 0.0) > 0.0 and not np.any(shares[i])
    ]
    if dead:
        raise ValueError(
            f"zonal-shares parquet for {iso} {year} has all-zero shares for "
            f"load-carrying zone(s) {dead} — stale parquet curated under old "
            "zone names? Re-run scripts/curate_zonal_shares.py."
        )
    return shares


# EIA-930 MISO sub-BA -> model zone. EIA-930 reports MISO sub-BA hourly demand
# at exactly six LRZ-group partitions, and the six model zones are drawn as
# exactly those groups — a 1:1 map, the finest partition with fully measured
# hourly load (docs/multi-iso/miso-zonal-refinement-scope.md §1). The fleet
# partition (zone_assignment._MISO_STATE_ZONES) shares identical whole-state
# sub-BA-union boundaries. Source: EIA-930 region-sub-ba-data, parent=MISO;
# crosswalk per docs/multi-iso/miso-data-audit.md Item 2.
_MISO_SUBBA_ZONE_GROUPS: dict[str, str] = {
    "0001": "MISO-West",  # LRZ 1: MN, ND, SD, MT (wind belt)
    "0035": "MISO-Plains",  # LRZ 3+5: IA, MO (Iowa wind-export corridor)
    "0004": "MISO-Illinois",  # LRZ 4: IL (Ameren wheel-through zone)
    "0006": "MISO-Indiana",  # LRZ 6: IN, KY (load-east anchor)
    "0027": "MISO-East",  # LRZ 2+7: WI, MI (Michigan import pocket + WUMS)
    "8910": "MISO-South",  # LRZ 8+9+10: AR, LA, MS, E. TX (RDT-separated)
}


def _miso_utc_to_local_hoy(period_utc: pd.Series, year: int) -> pd.Series | None:
    """Map UTC timestamps to MISO local hour-of-year on the renewable clock.

    The MISO sub-BA demand CSV stamps its ``period`` in UTC, but the renewable
    CF and system demand the zonal shares are multiplied into live on MISO local
    wall-clock time (the EIA-930 ``MISO hourly`` extract's ``Local time``). To
    keep all three on one clock, each UTC period is mapped through the hourly
    frame's *own* ``UTC time`` -> row-index correspondence: frame row k is local
    hour-of-year k (Feb 29 already dropped, DST handled by the extract), so the
    returned index lands the share at the same wall-clock hour the renewables
    use. This derives the offset from the clock itself — no IANA-zone or
    fixed-offset assumption — and stays valid for any forward year that ships a
    frame. Periods outside the local-year UTC window map to NaN (the caller
    drops them). Returns ``None`` when the MISO frame is unavailable.
    """
    frame = _eia_hourly_frame_filled("MISO", year)
    if frame is None:
        return None
    # frame row k == model local hour-of-year k; invert UTC time -> k.
    utc_index = pd.DatetimeIndex(frame["UTC time"])
    hoy_of_utc = pd.Series(np.arange(len(frame), dtype=float), index=utc_index)
    hoy_of_utc = hoy_of_utc[~hoy_of_utc.index.duplicated(keep="first")]
    return period_utc.map(hoy_of_utc)


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
    path = _PJM_INTERCHANGE_DIR / f"PJM_{year}_import_export_act_sch_interchange.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, usecols=["datetime_beginning_ept", "actual_flow"])
    ts = pd.to_datetime(df["datetime_beginning_ept"], format="mixed", errors="coerce")
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


# PJM tie line -> the model border zone it interconnects, so the net export is
# drawn out of the zone that physically carries it (vs. spread system-wide).
# NYISO/NYC cables sit on the EMAAC border; the MISO-west/upper-Midwest ties on
# ComEd; the Indiana/Ohio/Kentucky ties on AEP-Ohio; Michigan on ATSI; the
# Carolinas/Duke/TVA ties on Dominion. Tier 3 (calibration) — approximate
# pending PJM's authoritative tie-to-zone assignment.
_PJM_TIE_ZONE: dict[str, str] = {
    "NYIS": "PJM_EMAAC",
    "NEPT": "PJM_EMAAC",
    "HUDS": "PJM_EMAAC",
    "LIND": "PJM_EMAAC",
    "AMIL": "PJM_ComEd",
    "ALTE": "PJM_ComEd",
    "ALTW": "PJM_ComEd",
    "CWLP": "PJM_ComEd",
    "MEC": "PJM_ComEd",
    "WEC": "PJM_ComEd",
    "MDU": "PJM_ComEd",
    "LAGN": "PJM_ComEd",
    "CIN": "PJM_AEP_Ohio",
    "IPL": "PJM_AEP_Ohio",
    "NIPS": "PJM_AEP_Ohio",
    "SIGE": "PJM_AEP_Ohio",
    "LGEE": "PJM_AEP_Ohio",
    "OVEC": "PJM_AEP_Ohio",
    "MECS": "PJM_ATSI",
    "CPLE": "PJM_Dominion",
    "CPLW": "PJM_Dominion",
    "DUK": "PJM_Dominion",
    "TVA": "PJM_Dominion",
}
# Border zone that absorbs any tie not in the map above (keeps total export
# conserved). ComEd is the largest western export interface.
_PJM_TIE_ZONE_DEFAULT: str = "PJM_ComEd"


def pjm_zonal_interchange(year: int, zone_names: list[str]) -> np.ndarray | None:
    """Return PJM's hourly net export by model zone (``(n_zones, T)``, MW).

    Like :func:`pjm_net_interchange`, but attributes each tie's net export to
    the border zone it interconnects (:data:`_PJM_TIE_ZONE`) instead of
    spreading the system total across all zones by load share. So the export
    is drawn out of the zones that physically carry it (ComEd/AEP to the
    Midwest, EMAAC to NYISO, Dominion to the Carolinas), sharpening the
    inter-zone congestion. Row order matches ``zone_names``; the column sum
    equals :func:`pjm_net_interchange`. ``None`` when the file is absent.
    """
    path = _PJM_INTERCHANGE_DIR / f"PJM_{year}_import_export_act_sch_interchange.csv"
    if not path.exists():
        return None
    df = pd.read_csv(
        path, usecols=["datetime_beginning_ept", "tie_line", "actual_flow"]
    )
    ts = pd.to_datetime(df["datetime_beginning_ept"], format="mixed", errors="coerce")
    keep = ts.notna() & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df, ts = df[keep], ts[keep]
    hoy = (
        np.array(_MONTH_START_HOUR)[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )
    zone_idx = {z: i for i, z in enumerate(zone_names)}
    out = np.zeros((len(zone_names), HOURS_PER_YEAR), dtype=float)
    flow = df["actual_flow"].to_numpy(dtype=float)
    tie_zone = (
        df["tie_line"]
        .map(lambda t: _PJM_TIE_ZONE.get(str(t), _PJM_TIE_ZONE_DEFAULT))
        .to_numpy()
    )
    valid = (hoy >= 0) & (hoy < HOURS_PER_YEAR) & ~np.isnan(flow)
    for z, i in zone_idx.items():
        sel = valid & (tie_zone == z)
        if sel.any():
            np.add.at(out[i], hoy[sel], -flow[sel])  # export-positive
    return out


def pjm_zonal_interchange_envelope(
    year: int, zone_names: list[str], hours: int, percentile: float = 95.0
) -> tuple[np.ndarray, np.ndarray] | None:
    """Return PJM's per-border (month×hod) import/export interchange envelope (MW).

    The per-border-zone analogue of :func:`measured_interchange_envelope` (CAISO),
    built from :func:`pjm_zonal_interchange` (the measured per-tie net export
    attributed to the model border zone it physically interconnects). For each
    border zone and each hour of the run horizon, the ``percentile`` of measured
    net interchange in that hour's (month, hour-of-day) bucket, split into the
    import and export directions (``pjm_zonal_interchange`` is export-positive):

        import_cap[z, t] = P_pctile( max(0, -interchange) | z, month(t), hod(t) )
        export_cap[z, t] = P_pctile( max(0, +interchange) | z, month(t), hod(t) )

    The caller (:func:`market_sim.model.transmission.build_pjm_external_flow_groups`)
    caps each ``PJM_external→border`` link's signed flow asymmetrically — import
    (positive flow, hub→border) at ``import_cap`` and export (negative flow,
    border→hub) at ``export_cap`` — so the priced external node delivers only
    roughly its historical per-border capability in each period rather than ~30 GW
    uncongested in every hour. The dominant direction keeps a generous high-
    percentile ceiling the LP clears below; the minor direction (EMAAC import,
    Dominion export, the interior zones with no tie) collapses toward ~0. A
    measured capability envelope with no fitted constant (rule #12), the price
    still clearing in merit order within it.

    Returns ``(import_cap, export_cap)``, each ``(n_zones, hours)`` MW with row
    order matching ``zone_names``, or ``None`` when the measured tie file is
    absent (a forecast year), in which case the caller leaves the node uncapped.
    """
    zonal = pjm_zonal_interchange(year, zone_names)
    if zonal is None:
        return None
    src_hours = zonal.shape[1]
    src_clock = pd.date_range(f"{year}-01-01", periods=src_hours, freq="h")
    s_month = src_clock.month.to_numpy()
    s_hod = src_clock.hour.to_numpy()
    n = len(zone_names)
    imp_tab = np.zeros((n, 12, 24))
    exp_tab = np.zeros((n, 12, 24))
    for zi in range(n):
        e = zonal[zi]
        imp = np.clip(-e, 0.0, None)  # import into PJM at this border
        exp = np.clip(e, 0.0, None)  # export out of PJM at this border
        for m in range(1, 13):
            for h in range(24):
                sel = (s_month == m) & (s_hod == h)
                if not sel.any():
                    continue
                imp_tab[zi, m - 1, h] = np.percentile(imp[sel], percentile)
                exp_tab[zi, m - 1, h] = np.percentile(exp[sel], percentile)
    # Map the (month, hod) tables onto the run horizon (row 0 = first local hour).
    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    rm = clock.month.to_numpy() - 1
    rh = clock.hour.to_numpy()
    import_cap = imp_tab[:, rm, rh]
    export_cap = exp_tab[:, rm, rh]
    return import_cap, export_cap


def _eia930_net_interchange(ba_code: str, year: int) -> np.ndarray | None:
    """Return a BA's hourly net export (MW, export-positive), or ``None``.

    Reads the EIA-930 ``<BA> hourly`` extract's ``Total interchange`` column
    for ``year`` on the model's fixed non-leap 8760-hour clock (the same frame
    the demand series is drawn from, so interchange stays aligned to demand).
    EIA's sign convention is **already** the one :func:`load_demand` expects —
    positive = net export (raises what the internal fleet must serve), negative
    = net import (lowers it) — so the column is returned as-is, with **no** sign
    flip (unlike :func:`pjm_net_interchange`, which negates PJM's
    import-positive tie-line file). Small calendar holes are interpolated.

    Returns ``None`` when the file, the year, or the ``Total interchange``
    column is unavailable, so the caller falls back to zero interchange.
    """
    frame = _eia_hourly_frame_filled(ba_code, year)
    if frame is None or "Total interchange" not in frame.columns:
        return None
    interchange = (
        frame["Total interchange"].interpolate().bfill().ffill().to_numpy(dtype=float)
    )
    if np.isnan(interchange).any() or interchange.shape[0] != HOURS_PER_YEAR:
        return None
    return interchange


def nyiso_net_interchange(year: int) -> np.ndarray | None:
    """Return NYISO's hourly net export (MW, export-positive), or ``None``.

    Sources the measured net interchange from the EIA-930 ``NYIS hourly``
    extract's ``Total interchange`` column (see :func:`_eia930_net_interchange`
    for the sign convention). NYISO is a steady ~16%-of-load net importer (2023:
    −23.45 TWh), so the series is predominantly negative and serving it reduces
    the residual the in-state fleet must generate — the import wedge that would
    otherwise be mis-attributed to internal gas (P9 / playbook §8.2). Mirrors
    :func:`pjm_net_interchange`'s shape; ``None`` when the year is unavailable.
    """
    return _eia930_net_interchange("NYIS", year)


def nyiso_forward_net_import_monthly(
    year: int,
    forward_net_import_twh: dict[int, float] | float | None,
    system_demand: np.ndarray | None = None,
) -> np.ndarray | None:
    """Return NYISO's FORECAST monthly net import (MWh, import-positive), or ``None``.

    The forward analogue of the measured backcast band target
    (:func:`nyiso_net_interchange`). In a forecast there is no measured EIA-930
    schedule to reconcile against, so the band target is the **neighbor's
    forecast net position** supplied by the caller as an annual NYISO net
    *import* in TWh (positive = net import) — derived externally from the
    PJM / Hydro-Québec / Ontario / ISO-NE forward export outlooks
    (NYISO Gold Book imports, neighbor capacity-expansion / interface
    schedules), NOT from any NYISO output. The annual total is shaped to the
    twelve monthly targets by the forecast **load distribution** when
    ``system_demand`` is supplied (imports track load, so the band responds to
    changed conditions — the forward-reproducibility test, CLAUDE.md rule #12),
    else split evenly by each month's hour count.

    Returns ``None`` (band relaxes to the bare priced-seam economics) when no
    forecast is supplied for ``year`` — either ``forward_net_import_twh`` is
    ``None`` or, when it is a per-year mapping, ``year`` is absent from it.

    Args:
        year: Forecast calendar year keying the supplied trajectory.
        forward_net_import_twh: Forecast NYISO annual net import (TWh,
            import-positive). A ``dict[year -> TWh]`` is looked up by ``year``;
            a bare ``float`` is used for every year; ``None`` relaxes the band.
        system_demand: Optional hourly system demand, shape ``(T,)`` or
            ``(n_zones, T)`` (summed over zones), used to weight the monthly
            split. ``None`` falls back to an hour-count (near-flat) split.

    Returns:
        Monthly net-import targets in MWh, shape ``(n_months,)``, or ``None``.
    """
    if forward_net_import_twh is None:
        return None
    if isinstance(forward_net_import_twh, dict):
        annual_twh = forward_net_import_twh.get(year)
        if annual_twh is None:
            annual_twh = forward_net_import_twh.get(str(year))
    else:
        annual_twh = float(forward_net_import_twh)
    if annual_twh is None:
        return None

    from market_sim.data.fleet import _hour_to_month_index

    annual_mwh = float(annual_twh) * 1.0e6  # TWh -> MWh
    month_index = _hour_to_month_index(HOURS_PER_YEAR)
    n_months = int(month_index.max()) + 1

    if system_demand is not None:
        demand = np.asarray(system_demand, dtype=float)
        if demand.ndim == 2:
            demand = demand.sum(axis=0)
        demand = demand.reshape(-1)[:HOURS_PER_YEAR]
        weight = np.zeros(n_months, dtype=float)
        np.add.at(weight, month_index[: demand.size], demand)
    else:
        weight = np.zeros(n_months, dtype=float)
        np.add.at(weight, month_index, np.ones(HOURS_PER_YEAR))

    total = weight.sum()
    if total <= 0.0:
        return None
    return annual_mwh * (weight / total)


def neiso_net_interchange(year: int) -> np.ndarray | None:
    """Return NEISO's hourly net export (MW, export-positive), or ``None``.

    Sources the measured net interchange from the EIA-930 ``ISNE hourly``
    extract's ``Total interchange`` column (see :func:`_eia930_net_interchange`
    for the sign convention). ISO-NE is a steady ~9%-of-load net importer (2024:
    −10.30 TWh — the HQ Phase II + New Brunswick + NYISO wedge), so serving the
    series reduces the residual the internal fleet must generate (P9 / playbook
    §8.2). Mirrors :func:`pjm_net_interchange`'s shape; ``None`` when the year
    is unavailable.
    """
    return _eia930_net_interchange("ISNE", year)


# ISOs whose measured net interchange is served as a system-wide scalar
# schedule (spread across zones by load share), as opposed to PJM's per-border-
# zone tie attribution or ERCOT's demand-aligned DC-tie series. CAISO is
# deliberately excluded — its imports are supply modeled by the WECC_import
# node, not netted into demand (playbook §8.1); ERCOT is islanded and carries
# its DC ties through its own EIA-930 extract.
_SCALAR_INTERCHANGE_ISOS: dict[str, Callable[[int], np.ndarray | None]] = {
    "NYISO": nyiso_net_interchange,
    "NEISO": neiso_net_interchange,
}


def load_demand(
    iso: str,
    year: int,
    iso_config: ISOConfig | None = None,
    td_loss_factor: float = 0.0,
    data_dir: Path = DATA_DIR,
    include_interchange: bool = True,
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
    generates internal load *plus* the ~40 TWh PJM actually exported. For
    CAISO, demand comes from the EIA-930 ``CISO hourly`` extract with **no**
    interchange netting — imports are supply, modeled by the ``WECC_import``
    node (see :func:`_load_caiso_hourly_demand`; the series is net load,
    already net of ~15+ GW BTM PV, per the playbook §8.1 convention). For
    NYISO and NEISO, demand comes from the EIA-930 ``NYIS hourly`` / ``ISNE
    hourly`` extracts (see :func:`_load_nyiso_hourly_demand` /
    :func:`_load_neiso_hourly_demand`), combined by default with the measured
    EIA-930 net-interchange schedule from :func:`nyiso_net_interchange` /
    :func:`neiso_net_interchange` — both are
    steady net importers, so serving the measured (predominantly import) wedge
    lowers what the in-state fleet must generate instead of over-filling with
    internal gas (P9 / playbook §8.2). The priced import node remains the
    forward mechanism, used under ``--priced-interchange`` (where
    ``include_interchange`` is ``False`` so the wedge is not double counted).
    The demand series is net load, already net of behind-the-meter
    PV/storage/DER (playbook §8.1). Other ISOs use the demand-profiles parquet
    alone, with no interchange.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Calendar year to load.
        iso_config: Topology configuration supplying zone load shares. If
            ``None``, it is fetched via :func:`get_iso_config`.
        td_loss_factor: T&D losses as a fraction of metered load. The
            allocated demand is scaled by ``1 + td_loss_factor``. Defaults
            to ``0.0`` (no gross-up).
        data_dir: Directory containing the EIA-930 parquet extracts.
        include_interchange: When ``False``, the measured net-interchange
            schedule is left out of the returned demand (PJM tie-line
            export; ERCOT DC ties). Callers serving interchange through the
            priced import/export node instead
            (:func:`market_sim.model.transmission.build_import_generators`)
            must disable it here so the export is not counted twice.

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
    raw_mw: np.ndarray | None = None
    if iso == "ERCOT":
        ercot_hourly = _load_ercot_hourly(year)
        if ercot_hourly is not None:
            raw_mw, interchange = ercot_hourly
    elif iso == "CAISO":
        raw_mw = _load_caiso_hourly_demand(year)
    elif iso == "NYISO":
        raw_mw = _load_nyiso_hourly_demand(year)
    elif iso == "NEISO":
        raw_mw = _load_neiso_hourly_demand(year)
    elif iso == "MISO":
        # Source MISO system demand off the same hourly frame as its renewables
        # so demand[t] and renewable_cf[t] refer to the same wall-clock hour;
        # the demand-profiles fallback below is on UTC and lags the local
        # renewable clock by ~5-6h (see :func:`_load_miso_hourly_demand`).
        raw_mw = _load_miso_hourly_demand(year)
    # Clean-data seam (gated, default OFF): source the system demand from the
    # curated clean ``load`` dataset for the ISOs whose clean feed reconstructs
    # the raw EIA-930 series exactly (parity-checked in tests). Only the demand
    # magnitude is swapped; the interchange / zonal-share / loss logic below is
    # unchanged. A missing or incomplete clean partition returns ``None`` and
    # leaves the raw series (or the profiles-parquet fallback) in place.
    if _use_clean():
        clean_mw = _clean_system_demand(iso, year)
        if clean_mw is not None:
            raw_mw = clean_mw
    if raw_mw is None:
        profiles = pd.read_parquet(data_dir / _DEMAND_PROFILES_FILE)
        subset = _filter_iso_year(profiles, iso, year).sort_values("hour")
        assert len(subset) == HOURS_PER_YEAR, (
            f"Expected {HOURS_PER_YEAR} hours for {iso} {year}, got {len(subset)}"
        )
        raw_mw = subset["raw_mw"].to_numpy(dtype=float)

    assert not np.isnan(raw_mw).any(), f"NaN demand for {iso} {year}"
    assert raw_mw.max() > 0.0, f"Non-positive peak demand for {iso} {year}"

    if not include_interchange:
        interchange = np.zeros(HOURS_PER_YEAR, dtype=float)

    # Measured net interchange as an import/export "node": add the BA's net
    # export to the demand the internal fleet must serve (the ``raw_mw`` is
    # internal load). PJM is a large net exporter (without this the fleet
    # under-generates by the export and mis-attributes the missing gas to
    # coal); NYISO/NEISO are steady net importers (a negative schedule, which
    # lowers the residual the in-state fleet serves so the import wedge is not
    # over-generated as internal gas). The ERCOT path already carries
    # interchange from its EIA-930 extract. PJM prefers the per-border-zone
    # attribution (export drawn from the zone that carries the tie) over a
    # system-wide spread, falling back to the scalar; NYISO/NEISO use the
    # scalar spread by load share.
    zone_interchange = None
    if iso == "PJM" and include_interchange:
        zone_interchange = pjm_zonal_interchange(year, iso_config.zone_names)
        if zone_interchange is not None:
            logger.info(
                "PJM net interchange applied for %d: %+.0f MW avg "
                "(export-positive, per border zone)",
                year,
                float(zone_interchange.sum(axis=0).mean()),
            )
        else:
            pjm_ix = pjm_net_interchange(year)
            if pjm_ix is not None:
                interchange = pjm_ix
    elif iso in _SCALAR_INTERCHANGE_ISOS and include_interchange:
        # NYISO/NEISO are steady net importers (HQ, NYISO/PJM/IESO, NB ties).
        # Serve the *measured* EIA-930 net-interchange schedule so the import
        # wedge displaces internal gas instead of being over-generated in-state
        # (P9 / playbook §8.2; the priced node is the forward mechanism, used
        # under --priced-interchange where include_interchange is False). No
        # per-zone tie attribution yet, so the scalar is spread by load share.
        measured_ix = _SCALAR_INTERCHANGE_ISOS[iso](year)
        if measured_ix is not None:
            interchange = measured_ix
            logger.info(
                "%s net interchange applied for %d: %+.0f MW avg "
                "(export-positive, measured EIA-930)",
                iso,
                year,
                float(measured_ix.mean()),
            )

    # PJM, ERCOT, CAISO, NYISO, NEISO and MISO allocate demand by each zone's
    # own measured hourly shape (from the PJM metered-load / ERCOT native-load /
    # CAISO TAC-area / NYISO pal / ISO-NE SMD / MISO sub-BA demand files) when
    # available, so zones peak at different times; every other ISO (and these
    # six without their file) uses the static per-zone share broadcast across
    # hours. Both are (n_zones, T) weight matrices summing to 1.0 down each
    # hour, so the rest of the math is identical.
    zonal_shares = load_zonal_shares(iso, year, iso_config.zone_names)
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
    # Net interchange displaces internal generation: a net import (negative)
    # lowers what the fleet must serve, a net export raises it. Interchange is
    # a transmission-level flow, so it is not loss-grossed. PJM uses per-zone
    # attribution (export at its border zone); everything else spreads the
    # scalar by the same weights as demand.
    if zone_interchange is not None:
        demand += zone_interchange
    else:
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
