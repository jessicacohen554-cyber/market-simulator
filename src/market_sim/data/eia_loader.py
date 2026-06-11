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
# transmission zone (the seven-zone topology in iso_configs._ercot_config).
# ERCOT has no Panhandle weather zone, so the Panhandle model zone receives no
# load here (its share stays 0.0, matching the static config); the small Lubbock
# load it would hold sits inside the WEST weather zone and lands in the West
# model zone. The EAST weather zone is its own Northeast model zone (behind the
# NE_LOB export limit). The ERCOT system-total column is dropped. Mirrors the
# aggregation in scripts/derive_load_shares.py that seeded the load_share values.
_ERCOT_LOAD_ZONE_GROUPS: dict[str, str] = {
    "COAST": "Houston",
    "EAST": "Northeast", "NORTH": "North", "NCENT": "North",
    "SCENT": "South_Central",
    "SOUTH": "South",
    "FWEST": "West", "WEST": "West",
}

# CAISO TAC-area actual hourly load (upload U4: OASIS SLD_FCST with
# market_run_id=ACTUAL, monthly pulls) -> model zone weights. PG&E's TAC
# straddles Path 15, so it is split between NP15 and ZP26 with fixed weights
# that preserve the prior NP15:ZP26 = 0.43:0.07 ratio (no TAC boundary exists
# at Path 15 to measure the split; Tier 3 — calibration). SCE and SDG&E sit
# entirely south of Path 26 (SP15), as does the tiny VEA TAC (~80 MW, CAISO's
# southern-Nevada pocket). The "CA ISO-TAC" system-total rows are dropped and
# shares are normalized over the component TACs.
_CAISO_TAC_ZONE_WEIGHTS: dict[str, dict[str, float]] = {
    "PGE-TAC": {"NP15": 0.86, "ZP26": 0.14},
    "SCE-TAC": {"SP15": 1.0},
    "SDGE-TAC": {"SP15": 1.0},
    "VEA-TAC": {"SP15": 1.0},
}

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
    "A": "Upstate_West", "WEST": "Upstate_West",
    # Zone B — Genesee
    "B": "Upstate_West", "GENESE": "Upstate_West",
    # Zone C — Central
    "C": "Upstate_West", "CENTRL": "Upstate_West",
    # Zone D — North
    "D": "Upstate_West", "NORTH": "Upstate_West",
    # Zone E — Mohawk Valley
    "E": "Upstate_West", "MHK VL": "Upstate_West",
    # Zone F — Capital District
    "F": "Capital_Hudson", "CAPITL": "Capital_Hudson",
    # Zone G — Hudson Valley
    "G": "Capital_Hudson", "HUD VL": "Capital_Hudson",
    # Zone H — Millwood (Lower Hudson)
    "H": "Lower_Hudson", "MILLWD": "Lower_Hudson",
    # Zone I — Dunwoodie (Lower Hudson)
    "I": "Lower_Hudson", "DUNWOD": "Lower_Hudson",
    # Zone J — New York City
    "J": "NYC", "N.Y.C.": "NYC",
    # Zone K — Long Island
    "K": "Long_Island", "LONGIL": "Long_Island",
}

# Directory for NYISO zonal actual-load CSVs (upload U3). Absent until the
# user uploads NYISO OASIS "pal" actual-load files.
_NYISO_ZONAL_LOAD_DIR: Path = _ZONAL_LOAD_DIR / "NYISO"

# Minimum measured TAC hours to derive CAISO zonal shapes from a partial-year
# upload (U4 lands month by month); below this, fall back to static shares.
_CAISO_TAC_MIN_HOURS: int = 28 * 24

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

# ISO-NE 8 load zones -> 4 model transmission zones.
# North: ME + NH + VT; Central: WCMASS + SEMASS + RI; Boston: NEMA; Connecticut: CT.
# ISO-NE publishes zone names in two styles:
#   state/region codes (CT, ME, NH, RI, VT, NEMA, SEMASS, WCMASS) — SMD CSVs
#   hub-prefixed (.H.NEMA, .H.SEMASS, .H.WCMASS) — older API feeds
# Both forms are accepted. HQ_import is a priced-import node with no load share.
_NEISO_LOAD_ZONE_GROUPS: dict[str, str] = {
    "ME": "North", "NH": "North", "VT": "North",
    "NEMA": "Boston", ".H.NEMA": "Boston",
    "SEMASS": "Central", ".H.SEMASS": "Central",
    "WCMASS": "Central", ".H.WCMASS": "Central",
    "RI": "Central",
    "CT": "Connecticut",
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
    utc_end = utc[-1] + (
        pd.Timestamp(year=year, month=12, day=31, hour=23) - loc[-1]
    )
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
    demand = (
        frame["Demand"].interpolate().bfill().ffill()
        .to_numpy(dtype=float)
    )
    interchange = (
        frame["Total interchange"].interpolate().bfill().ffill()
        .to_numpy(dtype=float)
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
    rows (same rationale as CAISO). Isolated missing meter hours are
    interpolated.

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
    ("battery", "NG: BAT"),
    ("pumped_storage", "NG: PS"),
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


def caiso_zonal_load_shares(
    year: int, zone_names: list[str]
) -> np.ndarray | None:
    """Return ``(n_zones, HOURS_PER_YEAR)`` hourly CAISO load shares, or ``None``.

    Reads CAISO's TAC-area actual hourly load (upload U4: OASIS ``SLD_FCST``
    with ``market_run_id=ACTUAL``; ``CAISO_tac_load_hourly_<year>.csv``) and
    maps the TAC areas onto the three trading-hub zones via
    :data:`_CAISO_TAC_ZONE_WEIGHTS` — PGE-TAC split 0.86/0.14 between NP15
    and ZP26, SCE + SDG&E + VEA to SP15 — returning each model zone's
    hour-by-hour fraction of system load. The caller multiplies these
    time-varying shares by the EIA-930 system demand total, so the system
    level stays tied to the CISO demand series while zones get measured
    shapes. The ``WECC_import`` node is absent from the weights and keeps an
    all-zero row.

    U4 arrives in monthly OASIS pulls, so the file may cover only part of the
    year. Hours inside the measured window get their measured shares; hours
    outside it (and any DST spring-forward gap) carry the sample-average zone
    shares, so the matrix always partitions every hour. Fewer than
    :data:`_CAISO_TAC_MIN_HOURS` measured hours — or a missing file — returns
    ``None`` and the caller falls back to the static per-zone ``load_share``
    (itself derived from this data via ``scripts/derive_load_shares.py``).
    Refresh path: complete the U4 monthly pulls for 2023–2025.

    Timestamps are UTC interval starts; they are converted to Pacific local
    time and placed on the model's fixed non-leap 8760-hour clock (Feb 29
    dropped). Overlapping OASIS pulls duplicate rows verbatim; duplicates are
    dropped on ``(tac_area, interval_start_gmt)``.
    """
    path = _ZONAL_LOAD_DIR / "CAISO" / f"CAISO_tac_load_hourly_{year}.csv"
    if not path.exists():
        logger.warning(
            "CAISO TAC-area load file not found (%s); using static "
            "load_share split", path,
        )
        return None
    df = pd.read_csv(path, parse_dates=["interval_start_gmt"])
    df = df[df["tac_area"].isin(_CAISO_TAC_ZONE_WEIGHTS)]
    df = df.drop_duplicates(subset=["tac_area", "interval_start_gmt"])
    ts = (
        pd.DatetimeIndex(df["interval_start_gmt"])
        .tz_convert("America/Los_Angeles")
        .tz_localize(None)
    )
    keep = (ts.year == year) & ~((ts.month == 2) & (ts.day == 29))
    df, ts = df[keep], ts[keep]
    if df.empty:
        logger.warning(
            "CAISO TAC-area load file %s has no %d rows; using static "
            "load_share split", path.name, year,
        )
        return None
    hoy = (
        np.array(_MONTH_START_HOUR)[ts.month - 1]
        + (ts.day - 1) * 24
        + ts.hour
    )
    zone_idx = {z: i for i, z in enumerate(zone_names)}
    grid = np.zeros((len(zone_names), HOURS_PER_YEAR), dtype=float)
    mw = df["mw"].to_numpy(dtype=float)
    tac = df["tac_area"].to_numpy()
    for tac_name, weights in _CAISO_TAC_ZONE_WEIGHTS.items():
        sel = (tac == tac_name) & ~np.isnan(mw)
        if not sel.any():
            continue
        for zone, weight in weights.items():
            np.add.at(grid[zone_idx[zone]], hoy[sel], weight * mw[sel])
    col_tot = grid.sum(axis=0)
    covered = col_tot > 0.0
    n_covered = int(covered.sum())
    if n_covered < _CAISO_TAC_MIN_HOURS:
        logger.warning(
            "CAISO TAC-area load for %d covers only %d hours "
            "(< %d required); using static load_share split",
            year, n_covered, _CAISO_TAC_MIN_HOURS,
        )
        return None
    shares = np.empty_like(grid)
    shares[:, covered] = grid[:, covered] / col_tot[covered]
    if n_covered < HOURS_PER_YEAR:
        mean_share = grid[:, covered].sum(axis=1) / col_tot[covered].sum()
        shares[:, ~covered] = mean_share[:, None]
        logger.warning(
            "CAISO TAC-area load for %d covers %d/%d hours; uncovered hours "
            "use the sample-average zone shares (refresh: complete the U4 "
            "monthly OASIS pulls)",
            year, n_covered, HOURS_PER_YEAR,
        )
    return shares


def nyiso_zonal_load_shares(
    year: int, zone_names: list[str]
) -> np.ndarray | None:
    """Return ``(n_zones, HOURS_PER_YEAR)`` hourly NYISO load shares, or ``None``.

    Reads NYISO actual zonal hourly load (upload U3: NYISO OASIS ``pal``
    actual-load CSV, ``NYISO_load_actuals_<year>.csv``) and maps the eleven
    settlement zones (A–K) onto the five model zones via
    :data:`_NYISO_LOAD_ZONE_GROUPS`, returning each model zone's hour-by-hour
    fraction of system load. The caller multiplies these time-varying shares by
    the EIA-930 NYIS system demand total, so each zone gets its own measured
    shape — the heavily loaded downstate NYC (J) and Long Island (K) pockets
    peak at different hours than cheap upstate generation — while the system
    level stays tied to the existing demand series.

    **Expected CSV format (upload U3):** ``NYISO_load_actuals_<year>.csv``
    under ``inputs/raw-data/zone-specific-demand/NYISO/``, with columns
    ``Time Stamp`` (Eastern local, hour-beginning), ``Name`` (NYISO zone name
    CAPITL/CENTRL/… or letter A–K), and ``Load`` (MW). Files are sourced from
    the NYISO OASIS "pal" actual-load endpoint (hourly integrated, all eleven
    zones, 2023–2025).

    Returns ``None`` when the file is absent so the caller falls back to the
    static Gold-Book load shares in :func:`_nyiso_config` (Tier 3 —
    calibration). Refresh path: upload NYISO OASIS pal actual-load CSVs for
    2023–2025 as ``NYISO_load_actuals_<year>.csv`` (see upload manifest U3).

    Timestamps are Eastern local time (America/New_York); they are placed on
    the model's fixed non-leap 8760-hour clock (Feb 29 dropped). Any
    spring-forward DST gap is back-filled from the previous hour.
    """
    path = _NYISO_ZONAL_LOAD_DIR / f"NYISO_load_actuals_{year}.csv"
    if not path.exists():
        logger.warning(
            "NYISO zonal load file not found (%s); using static load_share "
            "split (Tier 3 — upload U3 to refresh)", path,
        )
        return None
    df = pd.read_csv(path)
    # Flexible column detection: NYISO OASIS downloads use "Time Stamp" for
    # the timestamp and "Name" for the zone; tolerate minor naming variants.
    ts_col = next(
        (c for c in df.columns if c.lower().replace(" ", "_") in
         ("time_stamp", "timestamp", "datetime", "date_time")),
        None,
    )
    zone_col = next(
        (c for c in df.columns if c.lower() in ("name", "zone", "zone_name")),
        None,
    )
    load_col = next(
        (c for c in df.columns if c.lower() in ("load", "mw", "load_mw")),
        None,
    )
    if ts_col is None or zone_col is None or load_col is None:
        logger.warning(
            "NYISO zonal load file %s is missing expected columns "
            "(need timestamp, zone-name, and MW load); using static shares",
            path.name,
        )
        return None
    ts = pd.to_datetime(df[ts_col], errors="coerce")
    # NYISO OASIS timestamps are Eastern local (tz-naive). If the file carries
    # tz-aware UTC timestamps (uncommon), convert to Eastern first.
    if ts.dt.tz is not None:
        ts = ts.dt.tz_convert("America/New_York")
    else:
        ts = ts.dt.tz_localize("America/New_York", ambiguous="NaT",
                               nonexistent="NaT")
    ts_local = ts.dt.tz_localize(None)
    keep = (
        (ts_local.dt.year == year)
        & ts_local.notna()
        & ~((ts_local.dt.month == 2) & (ts_local.dt.day == 29))
    )
    df = df[keep].copy()
    ts_local = ts_local[keep]
    if df.empty:
        logger.warning(
            "NYISO zonal load file %s has no %d data after filtering; "
            "using static shares", path.name, year,
        )
        return None
    hoy = (
        np.array(_MONTH_START_HOUR)[ts_local.dt.month.to_numpy() - 1]
        + (ts_local.dt.day.to_numpy() - 1) * 24
        + ts_local.dt.hour.to_numpy()
    )
    df["_mzone"] = df[zone_col].astype(str).str.strip().map(_NYISO_LOAD_ZONE_GROUPS)
    unmapped = df["_mzone"].isna()
    if unmapped.any():
        missing = sorted(df.loc[unmapped, zone_col].unique())
        logger.warning(
            "NYISO load zones not mapped to a model zone: %s", missing
        )
        df = df[~unmapped]
        hoy = hoy[~unmapped.to_numpy()]
    mw = pd.to_numeric(df[load_col], errors="coerce").to_numpy(dtype=float)
    return _hourly_shares_from_groups(df["_mzone"], hoy, pd.Series(mw), zone_names)


def neiso_zonal_load_shares(
    year: int, zone_names: list[str]
) -> np.ndarray | None:
    """Return ``(n_zones, HOURS_PER_YEAR)`` hourly NEISO load shares, or ``None``.

    Reads the ISO-NE hourly load-zone net energy for load (upload U3:
    ``inputs/raw-data/zone-specific-demand/NEISO/NEISO_load_hourly_{year}.csv``)
    and maps the eight ISO-NE load zones onto the four model zones via
    :data:`_NEISO_LOAD_ZONE_GROUPS`:

    - **North**: ME + NH + VT
    - **Central**: WCMASS + SEMASS + RI
    - **Boston**: NEMA (the NEMA/Boston load pocket)
    - **Connecticut**: CT

    ``HQ_import`` is a priced-import node and keeps an all-zero row. The
    caller multiplies these time-varying shares by the EIA-930 ISNE system
    demand total, giving each zone its own measured hourly shape rather than
    a single system curve scaled by a static share.

    **Net-load convention (playbook §8.1):** ISO-NE demand is metered at
    the transmission level and is already net of behind-the-meter PV
    (material in MA/CT). Backcasts model only front-of-meter resources.

    Expected CSV format (ISO-NE SMD wide): ``Date`` (MM/DD/YYYY),
    ``Hour Ending`` (1–24), then zone columns (CT, ME, NH, RI, VT, NEMA,
    SEMASS, WCMASS). The ``.H.NEMA`` / ``.H.SEMASS`` / ``.H.WCMASS``
    hub-prefixed variants are also accepted. The DST fall-back 25th hour
    and Feb 29 of a leap year are dropped; the spring-forward gap is
    back-filled from the previous hour.

    Returns ``None`` when the file is absent so the caller falls back to
    the static per-zone ``load_share`` (the current RSP-seeded
    0.20/0.30/0.21/0.29 split). **Refresh path (U3):** upload the ISO-NE
    hourly load-zone NEL file for 2023–2025 to
    ``inputs/raw-data/zone-specific-demand/NEISO/`` and run
    ``scripts/derive_load_shares.py neiso`` to re-derive the annual shares
    and replace the static Tier-3 values.
    """
    path = _ZONAL_LOAD_DIR / "NEISO" / f"NEISO_load_hourly_{year}.csv"
    if not path.exists():
        logger.warning(
            "NEISO zonal load file not found (%s); using static "
            "load_share split. Refresh path: upload U3 (ISO-NE hourly_load "
            "SMD CSV for %d) to inputs/raw-data/zone-specific-demand/NEISO/",
            path, year,
        )
        return None
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    date_col = next(
        (c for c in df.columns if c.upper().startswith("DATE")), None
    )
    he_col = next(
        (c for c in df.columns
         if "HOUR" in c.upper() and "END" in c.upper()), None
    )
    if date_col is None or he_col is None:
        logger.warning(
            "NEISO zonal load file %s missing Date / Hour Ending columns; "
            "using static load_share split", path.name,
        )
        return None
    date = pd.to_datetime(df[date_col], format="mixed", errors="coerce")
    hour_ending = pd.to_numeric(df[he_col], errors="coerce")
    # HE 1 = midnight–1am → hour_of_day 0; HE 24 = 11pm–midnight → 23.
    # Skip HE 25 (DST fall-back extra hour).
    valid_he = hour_ending.notna() & (hour_ending >= 1) & (hour_ending <= 24)
    df = df[valid_he].copy()
    date = date[valid_he].reset_index(drop=True)
    hour_of_day = (hour_ending[valid_he].astype(int) - 1).to_numpy()
    month = date.dt.month.to_numpy()
    day = date.dt.day.to_numpy()
    keep = ~((month == 2) & (day == 29))
    df = df[keep]
    month, day, hour_of_day = month[keep], day[keep], hour_of_day[keep]
    hoy = (
        np.array(_MONTH_START_HOUR)[month - 1]
        + (day - 1) * 24
        + hour_of_day
    )
    zone_cols = [c for c in _NEISO_LOAD_ZONE_GROUPS if c in df.columns]
    missing_cols = sorted(set(_NEISO_LOAD_ZONE_GROUPS) - set(df.columns))
    if missing_cols:
        logger.warning(
            "NEISO load zones absent from %s: %s", path.name, missing_cols,
        )
    if not zone_cols:
        logger.warning(
            "NEISO zonal load file %s has no recognised zone columns; "
            "using static load_share split", path.name,
        )
        return None
    mzone = pd.concat(
        [pd.Series([_NEISO_LOAD_ZONE_GROUPS[c]] * len(df)) for c in zone_cols],
        ignore_index=True,
    )
    hoy_long = np.tile(hoy, len(zone_cols))
    mw = pd.concat(
        [pd.to_numeric(df[c], errors="coerce").reset_index(drop=True)
         for c in zone_cols],
        ignore_index=True,
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


# PJM tie line -> the model border zone it interconnects, so the net export is
# drawn out of the zone that physically carries it (vs. spread system-wide).
# NYISO/NYC cables sit on the EMAAC border; the MISO-west/upper-Midwest ties on
# ComEd; the Indiana/Ohio/Kentucky ties on AEP-Ohio; Michigan on ATSI; the
# Carolinas/Duke/TVA ties on Dominion. Tier 3 (calibration) — approximate
# pending PJM's authoritative tie-to-zone assignment.
_PJM_TIE_ZONE: dict[str, str] = {
    "NYIS": "PJM_EMAAC", "NEPT": "PJM_EMAAC", "HUDS": "PJM_EMAAC",
    "LIND": "PJM_EMAAC",
    "AMIL": "PJM_ComEd", "ALTE": "PJM_ComEd", "ALTW": "PJM_ComEd",
    "CWLP": "PJM_ComEd", "MEC": "PJM_ComEd", "WEC": "PJM_ComEd",
    "MDU": "PJM_ComEd", "LAGN": "PJM_ComEd",
    "CIN": "PJM_AEP_Ohio", "IPL": "PJM_AEP_Ohio", "NIPS": "PJM_AEP_Ohio",
    "SIGE": "PJM_AEP_Ohio", "LGEE": "PJM_AEP_Ohio", "OVEC": "PJM_AEP_Ohio",
    "MECS": "PJM_ATSI",
    "CPLE": "PJM_Dominion", "CPLW": "PJM_Dominion", "DUK": "PJM_Dominion",
    "TVA": "PJM_Dominion",
}
# Border zone that absorbs any tie not in the map above (keeps total export
# conserved). ComEd is the largest western export interface.
_PJM_TIE_ZONE_DEFAULT: str = "PJM_ComEd"


def pjm_zonal_interchange(
    year: int, zone_names: list[str]
) -> np.ndarray | None:
    """Return PJM's hourly net export by model zone (``(n_zones, T)``, MW).

    Like :func:`pjm_net_interchange`, but attributes each tie's net export to
    the border zone it interconnects (:data:`_PJM_TIE_ZONE`) instead of
    spreading the system total across all zones by load share. So the export
    is drawn out of the zones that physically carry it (ComEd/AEP to the
    Midwest, EMAAC to NYISO, Dominion to the Carolinas), sharpening the
    inter-zone congestion. Row order matches ``zone_names``; the column sum
    equals :func:`pjm_net_interchange`. ``None`` when the file is absent.
    """
    path = (
        _PJM_INTERCHANGE_DIR
        / f"PJM_{year}_import_export_act_sch_interchange.csv"
    )
    if not path.exists():
        return None
    df = pd.read_csv(
        path, usecols=["datetime_beginning_ept", "tie_line", "actual_flow"]
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
    zone_idx = {z: i for i, z in enumerate(zone_names)}
    out = np.zeros((len(zone_names), HOURS_PER_YEAR), dtype=float)
    flow = df["actual_flow"].to_numpy(dtype=float)
    tie_zone = df["tie_line"].map(
        lambda t: _PJM_TIE_ZONE.get(str(t), _PJM_TIE_ZONE_DEFAULT)
    ).to_numpy()
    valid = (hoy >= 0) & (hoy < HOURS_PER_YEAR) & ~np.isnan(flow)
    for z, i in zone_idx.items():
        sel = valid & (tie_zone == z)
        if sel.any():
            np.add.at(out[i], hoy[sel], -flow[sel])  # export-positive
    return out


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
    NYISO, demand comes from the EIA-930 ``NYIS hourly`` extract with **no**
    interchange netting — imports are a calibrated priced node (P9 /
    playbook §8.2; see :func:`_load_nyiso_hourly_demand`); the series is net
    load, already net of behind-the-meter PV/storage/DER (playbook §8.1;
    NY's BTM wedge is smaller than CAISO's but growing downstate). For
    NEISO, demand comes from the EIA-930 ``ISNE hourly`` extract with no
    interchange netting — HQ imports are supply, modeled by the ``HQ_import``
    node (see :func:`_load_neiso_hourly_demand`; the series is net of
    behind-the-meter PV, material in MA/CT, per the playbook §8.1 convention).
    Other ISOs use the demand-profiles parquet alone, with no interchange.

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
    if raw_mw is None:
        profiles = pd.read_parquet(data_dir / _DEMAND_PROFILES_FILE)
        subset = _filter_iso_year(profiles, iso, year).sort_values("hour")
        assert len(subset) == HOURS_PER_YEAR, (
            f"Expected {HOURS_PER_YEAR} hours for {iso} {year}, "
            f"got {len(subset)}"
        )
        raw_mw = subset["raw_mw"].to_numpy(dtype=float)

    assert not np.isnan(raw_mw).any(), f"NaN demand for {iso} {year}"
    assert raw_mw.max() > 0.0, f"Non-positive peak demand for {iso} {year}"

    if not include_interchange:
        interchange = np.zeros(HOURS_PER_YEAR, dtype=float)

    # PJM's import/export "node": add its measured net export to the demand the
    # internal fleet must serve (the demand-profiles ``raw_mw`` is internal
    # load; PJM is a large net exporter, so without this the fleet under-
    # generates by the export and mis-attributes the missing gas to coal). The
    # ERCOT path already carries interchange from its EIA-930 extract.
    # Prefer the per-border-zone attribution (export drawn from the zone that
    # carries the tie) over a system-wide spread; fall back to the scalar.
    zone_interchange = None
    if iso == "PJM" and include_interchange:
        zone_interchange = pjm_zonal_interchange(year, iso_config.zone_names)
        if zone_interchange is not None:
            logger.info(
                "PJM net interchange applied for %d: %+.0f MW avg "
                "(export-positive, per border zone)",
                year, float(zone_interchange.sum(axis=0).mean()),
            )
        else:
            pjm_ix = pjm_net_interchange(year)
            if pjm_ix is not None:
                interchange = pjm_ix

    # PJM, ERCOT, CAISO, NYISO, and NEISO allocate demand by each zone's own
    # measured hourly shape (from the PJM metered-load / ERCOT native-load /
    # CAISO TAC-area / NYISO pal actual-load / ISO-NE SMD files) when
    # available, so zones peak at different times; every other ISO (and these
    # five without their file) uses the static per-zone share broadcast across
    # hours. Both are (n_zones, T) weight matrices summing to 1.0 down each
    # hour, so the rest of the math is identical.
    if iso == "PJM":
        zonal_shares = pjm_zonal_load_shares(year, iso_config.zone_names)
    elif iso == "ERCOT":
        zonal_shares = ercot_zonal_load_shares(year, iso_config.zone_names)
    elif iso == "CAISO":
        zonal_shares = caiso_zonal_load_shares(year, iso_config.zone_names)
    elif iso == "NYISO":
        zonal_shares = nyiso_zonal_load_shares(year, iso_config.zone_names)
    elif iso == "NEISO":
        zonal_shares = neiso_zonal_load_shares(year, iso_config.zone_names)
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
