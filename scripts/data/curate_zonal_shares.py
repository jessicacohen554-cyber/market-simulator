"""Curate zonal load share fractions from per-ISO raw demand files.

Reads each ISO's raw hourly load file(s) from ``data/raw/zone-specific-demand/``
using the same parsing logic as the legacy ``*_zonal_load_shares()`` functions in
``src/market_sim/data/eia_loader.py``, and writes one clean Parquet per
``(iso, year)`` through the frozen ``scripts/lib/clean_io.write_clean`` seam.

Output schema: ``data/dictionary/schema/zonal-shares.schema.yaml``
  - Long format: one row per (hour, zone).
  - ``hour``  — integer 0..8759 on the fixed non-leap 8760-hour clock.
  - ``zone``  — model zone name matching ISOConfig.zone_names.
  - ``share`` — fraction of system load (0.0–1.0; sums to ≈1.0 per hour).

Output path (via clean_path): ``data/clean/zonal-shares/<ISO>/zonal-shares_<year>.parquet``

Supported ISOs: ERCOT, CAISO, PJM, MISO, NYISO, NEISO, SPP, NWPP

Usage
-----
  python scripts/data/curate_zonal_shares.py --iso ERCOT --year 2023
  python scripts/data/curate_zonal_shares.py --iso PJM --year 2023 2024 2025
  python scripts/data/curate_zonal_shares.py --iso MISO --year 2023
  python scripts/data/curate_zonal_shares.py --iso SPP --year 2023 2024 2025
  python scripts/data/curate_zonal_shares.py --iso NWPP --year 2023 2024 2025
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Put the repo root on sys.path so the ``scripts`` package imports below resolve
# when this script is run directly (``python scripts/data/curate_zonal_shares.py``).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import ZONE_DEMAND_DIR
from market_sim.data.eia_loader import (
    _CAISO_TAC_MIN_HOURS,
    _CAISO_TAC_ZONE_WEIGHTS,
    _ERCOT_LOAD_ZONE_GROUPS,
    _MISO_SUBBA_ZONE_GROUPS,
    _MONTH_START_HOUR,
    _NEISO_LOAD_ZONE_GROUPS,
    _NYISO_LOAD_ZONE_GROUPS,
    _PJM_LOAD_ZONE_GROUPS,
    _eia_hourly_frame_filled,
    _hourly_shares_from_groups,
    _hours_of_year,
    _miso_utc_to_local_hoy,
)
from scripts.lib.clean_io import write_clean

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _shares_to_long(shares: np.ndarray, zone_names: list[str]) -> pd.DataFrame:
    """Convert a ``(n_zones, HOURS_PER_YEAR)`` share matrix to long format.

    Returns a DataFrame with columns ``hour`` (int64), ``zone`` (string), and
    ``share`` (float64) — one row per (hour, zone) pair, ordered by hour then
    zone.
    """
    n_z = len(zone_names)
    T = HOURS_PER_YEAR
    hour_col = np.repeat(np.arange(T, dtype=np.int64), n_z)
    zone_col = np.tile(zone_names, T)
    share_col = shares.T.ravel().astype(np.float64)
    return pd.DataFrame({"hour": hour_col, "zone": zone_col, "share": share_col})


# ---------------------------------------------------------------------------
# Per-ISO parse functions (same logic as the retired *_zonal_load_shares()
# functions in eia_loader.py).  All paths are derived from ZONE_DEMAND_DIR so
# tests can patch this module-level name to redirect to a temp directory.
# ---------------------------------------------------------------------------


def parse_pjm_shares(year: int, zone_names: list[str]) -> np.ndarray | None:
    """Parse PJM metered-load CSV -> ``(n_zones, HOURS_PER_YEAR)`` shares.

    Reads ``data/raw/zone-specific-demand/PJM{year}_hrl_load_metered.csv``,
    maps the 20 real transmission zones to 8 model zones, and normalises each
    hour to fractions summing to 1.0.  Returns ``None`` when the file is
    absent.
    """
    path = ZONE_DEMAND_DIR / f"PJM{year}_hrl_load_metered.csv"
    if not path.exists():
        logger.warning("PJM zonal metered-load file not found (%s); skipping", path)
        return None
    df = pd.read_csv(path, usecols=["datetime_beginning_utc", "zone", "mw"])
    df = df[df["zone"] != "RTO"].copy()
    df["mzone"] = df["zone"].map(_PJM_LOAD_ZONE_GROUPS)
    if df["mzone"].isna().any():
        missing = sorted(df.loc[df["mzone"].isna(), "zone"].unique())
        logger.warning("PJM load zones not mapped to a model zone: %s", missing)
        df = df.dropna(subset=["mzone"])
    # Index on PJM's absolute UTC stamp converted to the model's fixed-EST 8760
    # clock (Etc/GMT+5, no DST) — the prevailing datetime_beginning_ept stamp
    # places the DST-months rows one hour late against demand and the EIA-930
    # series. Byte-identical outside DST, exactly one hour earlier inside. See
    # docs/handoffs/debug-b-pjm-input-clock-charter-2026-08.md §3.
    ts = (
        pd.to_datetime(df["datetime_beginning_utc"], format="mixed", errors="coerce")
        .dt.tz_localize("UTC")
        .dt.tz_convert("Etc/GMT+5")
        .dt.tz_localize(None)
    )
    file_year = int(ts.dt.year.mode().iat[0])
    if file_year != year:
        logger.warning(
            "PJM%d_hrl_load_metered.csv actually contains %d data; using its "
            "zonal *shape* against %d system demand",
            year,
            file_year,
            year,
        )
    keep = ts.notna() & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df, ts = df[keep], ts[keep]
    return _hourly_shares_from_groups(
        df["mzone"], _hours_of_year(ts), df["mw"], zone_names
    )


def parse_ercot_shares(year: int, zone_names: list[str]) -> np.ndarray | None:
    """Parse an ERCOT native-load workbook -> ``(n_zones, HOURS_PER_YEAR)`` shares.

    Reads ``data/raw/zone-specific-demand/ERCOT_Native_Load_{year}.{xlsx,csv}``
    (NP3-565-CD), maps the eight weather zones to the model transmission zones,
    and normalises each hour to fractions summing to 1.0.  Returns ``None``
    when no file is present for the year.

    **Container, not content (ercot-253).** ERCOT publishes the same NP3-565-CD
    report as a workbook in some years and a CSV in others — 2023-2025 are
    ``.xlsx``, the back years 2018-2021 (and 2026) are ``.csv``, with identical
    columns, identical ``MM/DD/YYYY HH:MM`` hour-ending stamps and identical
    weather-zone MW.  The only schema drift is the header spelling of the
    timestamp column (``HourEnding`` in 2018-2020, ``Hour Ending`` elsewhere),
    normalised below.  ``.xlsx`` is tried FIRST so every year that has one -
    all three training years - resolves exactly as before and the parse is
    byte-identical there (rule 23 ``[R-FROZEN-DERIVE]``: no measured value
    moves).  Extending the reader to the CSV container is a rule-14
    ``[R-ACCURATE]`` completeness fix, zero DOF: without it a back-year solve
    silently drops to the static per-zone ``load_share`` and loses every
    ERCOT zone's measured diurnal shape, which is measured data being held
    out - forbidden by rule 22 ``[R-HOLDOUT]`` ("what is held out is the
    SCORE, never the DATA").
    """
    xlsx = ZONE_DEMAND_DIR / f"ERCOT_Native_Load_{year}.xlsx"
    csv = ZONE_DEMAND_DIR / f"ERCOT_Native_Load_{year}.csv"
    if xlsx.exists():
        path, df = xlsx, pd.read_excel(xlsx)
    elif csv.exists():
        path, df = csv, pd.read_csv(csv)
    else:
        logger.warning("ERCOT native-load file not found (%s); skipping", xlsx)
        return None
    # Header spelling drift across publication vintages; the column itself,
    # its format and its values are unchanged.
    df = df.rename(columns={"HourEnding": "Hour Ending"})
    he = df["Hour Ending"].astype(str).str.split(" ", n=1, expand=True)
    date = pd.to_datetime(he[0], format="mixed", dayfirst=False)
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
    wz_cols = [c for c in _ERCOT_LOAD_ZONE_GROUPS if c in df.columns]
    missing_cols = sorted(set(_ERCOT_LOAD_ZONE_GROUPS) - set(df.columns))
    if missing_cols:
        logger.warning(
            "ERCOT native-load weather zones absent from %s: %s",
            path.name,
            missing_cols,
        )
    mzone = pd.concat(
        [pd.Series([_ERCOT_LOAD_ZONE_GROUPS[c]] * len(df)) for c in wz_cols],
        ignore_index=True,
    )
    hoy_long = np.tile(hoy, len(wz_cols))
    mw = pd.concat([df[c].reset_index(drop=True) for c in wz_cols], ignore_index=True)
    return _hourly_shares_from_groups(mzone, hoy_long, mw, zone_names)


def parse_caiso_shares(year: int, zone_names: list[str]) -> np.ndarray | None:
    """Parse CAISO TAC-area CSV -> ``(n_zones, HOURS_PER_YEAR)`` shares.

    Reads ``data/raw/zone-specific-demand/CAISO/CAISO_tac_load_hourly_{year}.csv``
    (upload U4: OASIS SLD_FCST with market_run_id=ACTUAL), maps the four TAC
    areas to the three trading-hub zones via weighted splits, and normalises
    each hour.  Partial-year coverage uses sample-average shares for uncovered
    hours.  Returns ``None`` when the file is absent or covers fewer than
    ``_CAISO_TAC_MIN_HOURS`` measured hours.
    """
    path = ZONE_DEMAND_DIR / "CAISO" / f"CAISO_tac_load_hourly_{year}.csv"
    if not path.exists():
        logger.warning("CAISO TAC-area load file not found (%s); skipping", path)
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
            "CAISO TAC-area load file for %d has no data after filtering; skipping",
            year,
        )
        return None
    hoy = np.array(_MONTH_START_HOUR)[ts.month - 1] + (ts.day - 1) * 24 + ts.hour
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
            "CAISO TAC-area load for %d covers only %d hours (< %d required); skipping",
            year,
            n_covered,
            _CAISO_TAC_MIN_HOURS,
        )
        return None
    shares = np.empty_like(grid)
    shares[:, covered] = grid[:, covered] / col_tot[covered]
    if n_covered < HOURS_PER_YEAR:
        mean_share = grid[:, covered].sum(axis=1) / col_tot[covered].sum()
        shares[:, ~covered] = mean_share[:, None]
        logger.warning(
            "CAISO TAC-area load for %d covers %d/%d hours; uncovered hours "
            "use the sample-average zone shares",
            year,
            n_covered,
            HOURS_PER_YEAR,
        )
    return shares


def parse_miso_shares(year: int, zone_names: list[str]) -> np.ndarray | None:
    """Parse MISO EIA-930 sub-BA CSV -> ``(n_zones, HOURS_PER_YEAR)`` shares.

    Reads the sub-BA staging for ``year``, maps the six sub-BAs to the model
    zones, and normalises each hour.  The UTC ``period`` column is mapped to
    the model's local hour-of-year via the MISO hourly frame so zonal shapes
    index the same wall-clock hour as renewable CF.  Returns ``None`` when no
    staging covers the year (or the MISO hourly frame is absent).

    PER-YEAR FILE FIRST (miso-251, 2026-09-10).  This read used to be
    HARDCODED to the combined ``miso_subba_demand_2023-2025.csv``, which meant
    every year outside 2023-2025 fell through to the partial-coverage guard
    below and silently dispatched on FLAT SAMPLE-AVERAGE zone shares — even
    though ``data/raw/zone-specific-demand/MISO/`` has carried full-year
    per-year files (2018-2022, 2026, same schema, ~8,757 periods x 6 sub-BAs)
    since the 2026-07-31 holdout intake.  Found by the miso-251 2022
    touchpoint, whose solve logged "covers 2022 only partially (7/8760 hours)"
    while ``miso_subba_demand_2022.csv`` sat on disk complete: total demand was
    right (EIA-930 metered) but its allocation across the six zones was a flat
    average, a DIFFERENT demand basis than the 2023-2025 training years get,
    which reaches congestion, zonal price formation and therefore C3a/C3b/C4.
    Rule 14 ``[R-ACCURATE]``: the accurate input wins, and an estimate must not
    stand in for data the repo already holds.

    2023/2024/2025 have NO per-year file, so they resolve to the combined file
    exactly as before and every committed keeper is byte-identical.
    """
    miso_dir = ZONE_DEMAND_DIR / "MISO"
    per_year = miso_dir / f"miso_subba_demand_{int(year)}.csv"
    combined = miso_dir / "miso_subba_demand_2023-2025.csv"
    path = per_year if per_year.exists() else combined
    if not path.exists():
        logger.warning("MISO sub-BA load file not found (%s); skipping", path)
        return None
    df = pd.read_csv(path, usecols=["period", "subba", "value"], dtype={"subba": str})
    df = df[df["subba"].isin(_MISO_SUBBA_ZONE_GROUPS)].copy()
    period_utc = pd.to_datetime(df["period"], format="%Y-%m-%dT%H", errors="coerce")
    hoy_local = _miso_utc_to_local_hoy(period_utc, year)
    if hoy_local is None:
        logger.warning("MISO hourly frame unavailable for %d; skipping", year)
        return None
    keep = ~df.duplicated(subset=["period", "subba"], keep="first")
    keep &= hoy_local.notna().to_numpy()
    df, hoy_local = df[keep], hoy_local[keep]
    if df.empty:
        logger.warning("MISO sub-BA load file has no rows for %d; skipping", year)
        return None
    df = df.assign(
        hoy=hoy_local.to_numpy(dtype=int),
        mw=pd.to_numeric(df["value"], errors="coerce"),
    )
    wide = (
        df.pivot_table(index="hoy", columns="subba", values="mw", aggfunc="first")
        .sort_index()
        .ffill()
        .bfill()
    )
    long = (
        wide.reset_index()
        .melt(id_vars="hoy", var_name="subba", value_name="mw")
        .dropna(subset=["mw"])
    )
    mzone = long["subba"].map(_MISO_SUBBA_ZONE_GROUPS)
    shares = _hourly_shares_from_groups(
        mzone, long["hoy"].to_numpy(), long["mw"], zone_names
    )
    # A staging spans only the years it was pulled for. For any other year the
    # UTC->local mapping still lands a handful of rows —
    # January 1st's first UTC hours belong to the previous local year — and the
    # `df.empty` guard above does not catch that: a 7-hour year sails through
    # and returns shares that are NaN for the other 8,753 hours, which
    # propagates straight into `load_demand`'s zonal allocation. Require the
    # assembled series to cover the year; anything short is an uncovered year,
    # handled exactly like a missing file (caller falls back to the
    # sample-average shares).
    if shares is None or np.isnan(shares).any():
        logger.warning(
            "MISO sub-BA load file covers %d only partially (%d/%d hours); skipping",
            year,
            0 if shares is None else int((~np.isnan(shares[0])).sum()),
            HOURS_PER_YEAR,
        )
        return None
    return shares


def parse_nyiso_shares(year: int, zone_names: list[str]) -> np.ndarray | None:
    """Parse NYISO pal actual-load CSV -> ``(n_zones, HOURS_PER_YEAR)`` shares.

    Reads ``data/raw/zone-specific-demand/NYISO/NYISO_load_actuals_{year}.csv``
    (upload U3: OASIS "pal" actual-load endpoint), maps the eleven NYISO
    settlement zones (A–K) to the five model zones, and normalises each hour.
    Returns ``None`` when the file is absent.
    """
    path = ZONE_DEMAND_DIR / "NYISO" / f"NYISO_load_actuals_{year}.csv"
    if not path.exists():
        logger.warning("NYISO zonal load file not found (%s); skipping", path)
        return None
    df = pd.read_csv(path)
    ts_col = next(
        (
            c
            for c in df.columns
            if c.lower().replace(" ", "_")
            in ("time_stamp", "timestamp", "datetime", "date_time")
        ),
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
            "NYISO zonal load file is missing expected columns; skipping",
        )
        return None
    ts = pd.to_datetime(df[ts_col], errors="coerce")
    if ts.dt.tz is not None:
        ts = ts.dt.tz_convert("America/New_York")
    else:
        ts = ts.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
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
            "NYISO zonal load file has no %d data after filtering; skipping", year
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
        logger.warning("NYISO load zones not mapped to a model zone: %s", missing)
        df = df[~unmapped]
        hoy = hoy[~unmapped.to_numpy()]
    mw = pd.to_numeric(df[load_col], errors="coerce").to_numpy(dtype=float)
    return _hourly_shares_from_groups(df["_mzone"], hoy, pd.Series(mw), zone_names)


def parse_neiso_shares(year: int, zone_names: list[str]) -> np.ndarray | None:
    """Parse ISO-NE SMD hourly load CSV -> ``(n_zones, HOURS_PER_YEAR)`` shares.

    Reads ``data/raw/zone-specific-demand/NEISO/NEISO_load_hourly_{year}.csv``
    (upload U3: ISO-NE hourly load-zone NEL file, SMD wide format), maps the
    eight ISO-NE load zones to the four model zones, and normalises each hour.
    Returns ``None`` when the file is absent.
    """
    path = ZONE_DEMAND_DIR / "NEISO" / f"NEISO_load_hourly_{year}.csv"
    if not path.exists():
        logger.warning("NEISO zonal load file not found (%s); skipping", path)
        return None
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    date_col = next((c for c in df.columns if c.upper().startswith("DATE")), None)
    he_col = next(
        (c for c in df.columns if "HOUR" in c.upper() and "END" in c.upper()), None
    )
    if date_col is None or he_col is None:
        logger.warning(
            "NEISO zonal load file %s missing Date / Hour Ending columns; skipping",
            path.name,
        )
        return None
    date = pd.to_datetime(df[date_col], format="mixed", errors="coerce")
    hour_ending = pd.to_numeric(df[he_col], errors="coerce")
    valid_he = hour_ending.notna() & (hour_ending >= 1) & (hour_ending <= 24)
    df = df[valid_he].copy()
    date = date[valid_he].reset_index(drop=True)
    hour_of_day = (hour_ending[valid_he].astype(int) - 1).to_numpy()
    month = date.dt.month.to_numpy()
    day = date.dt.day.to_numpy()
    keep = ~((month == 2) & (day == 29))
    df = df[keep]
    month, day, hour_of_day = month[keep], day[keep], hour_of_day[keep]
    hoy = np.array(_MONTH_START_HOUR)[month - 1] + (day - 1) * 24 + hour_of_day
    zone_cols = [c for c in _NEISO_LOAD_ZONE_GROUPS if c in df.columns]
    missing_cols = sorted(set(_NEISO_LOAD_ZONE_GROUPS) - set(df.columns))
    if missing_cols:
        logger.warning("NEISO load zones absent from %s: %s", path.name, missing_cols)
    if not zone_cols:
        logger.warning(
            "NEISO zonal load file %s has no recognised zone columns; skipping",
            path.name,
        )
        return None
    mzone = pd.concat(
        [pd.Series([_NEISO_LOAD_ZONE_GROUPS[c]] * len(df)) for c in zone_cols],
        ignore_index=True,
    )
    hoy_long = np.tile(hoy, len(zone_cols))
    mw = pd.concat(
        [
            pd.to_numeric(df[c], errors="coerce").reset_index(drop=True)
            for c in zone_cols
        ],
        ignore_index=True,
    )
    return _hourly_shares_from_groups(mzone, hoy_long, mw, zone_names)


# ---------------------------------------------------------------------------
# SPP (added 2026-09-07 by lane SPP-32; plan §5 row SPP-32)
#
# Placement note, stated once here rather than repeated below: MISO's crosswalk
# and its UTC->local helper live in ``market_sim.data.eia930.zonal_shares`` (the
# ``eia_loader`` re-export imported above).  SPP's live HERE instead, because
# lane SPP-32's charter owns this script and not that module, and this script is
# the single source both the clean-curation path and the raw fallback read
# (``eia930.zonal_shares._zonal_shares_from_raw`` imports ``_PARSE_FUNCS`` from
# here), so nothing downstream can tell the difference.  Folding the two ISOs'
# crosswalks back together is a consolidation routed to SPP-DESK in
# ``docs/handoffs/FINDING-spp-32-2026-09-07.md``, not a defect in either.
# ---------------------------------------------------------------------------

# EIA-930 SPP sub-BA -> model zone.  EIA-930 reports SWPP hourly demand at
# exactly the 17 sub-BAs below, and SPP's own settlement-location registry
# (``data/raw/spp-planning/SL_to_Pnode_to_Zone_with_Area.csv``) carries the same
# 17 tokens as ``NODE_AREA`` values, matching 1:1 by name with an empty
# unmatched set — so no crosswalk table stands between the demand series and
# SPP's own areas (FINDING-spp-14-2026-09-06.md §8.2, which counts the
# settlement locations per area).
#
# The North/South partition is the SPP-20 P1 zone grouping, owner-ruled r#5 and
# carried by ``iso_configs._spp_config``; this dict is that ruling written on
# the sub-BA tokens, not an independent judgement by this script
# (FINDING-spp-20-2026-09-06.md).  It follows SPP's own legacy seam: the
# Integrated-System / Nebraska-and-Dakotas footprint plus the
# Missouri/Kansas members in the North, and the Oklahoma / Texas-Panhandle /
# western-Arkansas members in the South.
#
# EDE (Empire District Electric, Joplin MO) is the one member whose side is
# worth stating explicitly, because SPP's *reserve*-zone registry does not
# settle it: EDE's 25 settlement locations sit wholly in RESZONE 4, and RESZONE
# 4 straddles the seam (it also holds OKGE, CSWS, GRDA, SPS and WFEC, all
# South).  The reserve zones are therefore not the North/South key and cannot
# decide EDE.  EDE lands NORTH on the ruling, and the ruling agrees with EDE's
# geography and interconnection: Empire District is a southwest-Missouri utility
# whose load sits north-east of the seam alongside MPS / KCPL / INDN / KACY /
# SPRM, the other Missouri-Kansas members, all North.  Nothing here re-decides
# it; the paragraph exists so a reader does not have to reconstruct why RESZONE
# 4 membership is not evidence to the contrary.
_SPP_SUBBA_ZONE_GROUPS: dict[str, str] = {
    # --- North (12 sub-BAs): Nebraska / Dakotas / Missouri / Kansas ----------
    "EDE": "SPP-North",  # Empire District Electric (MO) — see the note above
    "INDN": "SPP-North",  # Independence Power & Light (MO)
    "KACY": "SPP-North",  # Kansas City Board of Public Utilities (KS)
    "KCPL": "SPP-North",  # Kansas City Power & Light (MO/KS)
    "LES": "SPP-North",  # Lincoln Electric System (NE)
    "MPS": "SPP-North",  # KCP&L Greater Missouri Operations (MO)
    "NPPD": "SPP-North",  # Nebraska Public Power District (NE)
    "OPPD": "SPP-North",  # Omaha Public Power District (NE)
    "SECI": "SPP-North",  # Sunflower Electric (KS)
    "SPRM": "SPP-North",  # City of Springfield (MO)
    "WAUE": "SPP-North",  # WAPA Upper Great Plains East (ND/SD/MN)
    "WR": "SPP-North",  # Westar Energy (KS)
    # --- South (5 sub-BAs): Oklahoma / Texas Panhandle / western Arkansas ----
    "CSWS": "SPP-South",  # AEP West (OK/AR/LA/TX)
    "GRDA": "SPP-South",  # Grand River Dam Authority (OK)
    "OKGE": "SPP-South",  # Oklahoma Gas and Electric (OK)
    "SPS": "SPP-South",  # Southwestern Public Service (TX Panhandle / NM)
    "WFEC": "SPP-South",  # Western Farmers Electric Cooperative (OK)
}


def _spp_utc_to_local_hoy(period_utc: pd.Series, year: int) -> pd.Series | None:
    """Map UTC timestamps to SPP local hour-of-year on the renewable clock.

    The same construction as :func:`_miso_utc_to_local_hoy`, against SPP's own
    EIA-930 hourly extract (BA code ``SWPP``): the SPP sub-BA demand CSV stamps
    its ``period`` in UTC, while the renewable CF and the system demand these
    shares are multiplied into live on SPP local wall-clock time.  Frame row
    ``k`` is local hour-of-year ``k`` (Feb 29 already dropped, DST handled by
    the extract), so inverting the frame's own ``UTC time`` column lands each
    share at the wall-clock hour the renewables use.  The offset is derived
    from the clock itself — no IANA-zone or fixed-offset assumption — so it
    stays valid for any year that ships a frame.  Periods outside the local
    year's UTC window map to NaN and the caller drops them.

    Args:
        period_utc: UTC timestamps parsed from the sub-BA CSV's ``period``.
        year: Calendar year whose SWPP frame supplies the clock.

    Returns:
        Float hour-of-year per input row (NaN outside the year), or ``None``
        when the SWPP hourly extract for ``year`` is unavailable.
    """
    frame = _eia_hourly_frame_filled("SWPP", year)
    if frame is None:
        return None
    # frame row k == model local hour-of-year k; invert UTC time -> k.
    utc_index = pd.DatetimeIndex(pd.to_datetime(frame["UTC time"]))
    hoy_of_utc = pd.Series(np.arange(len(frame), dtype=float), index=utc_index)
    hoy_of_utc = hoy_of_utc[~hoy_of_utc.index.duplicated(keep="first")]
    return period_utc.map(hoy_of_utc)


def parse_spp_shares(year: int, zone_names: list[str]) -> np.ndarray | None:
    """Parse SPP EIA-930 sub-BA CSV -> ``(n_zones, HOURS_PER_YEAR)`` shares.

    Reads the combined multi-year file
    ``data/raw/zone-specific-demand/SPP/spp_subba_demand_2023-2025.csv`` (and
    the per-year back-files ``spp_subba_demand_<year>.csv`` that lane SPP-15
    landed for 2019-2022), filters to ``year``, maps the 17 sub-BAs to the two
    model zones via :data:`_SPP_SUBBA_ZONE_GROUPS`, and normalises each hour.
    The UTC ``period`` column is mapped to the model's local hour-of-year
    through SPP's own hourly frame (:func:`_spp_utc_to_local_hoy`) so zonal
    shapes index the same wall-clock hour as renewable CF.

    The 17 sub-BAs are the whole of what EIA-930 reports under ``SWPP``, and
    their hourly sum reconciles to the ``SWPP`` system demand these shares are
    applied to (measured: annual sums within 0.03% for 2023-2025), so the
    share basis and the demand basis are the same footprint.  SPP's western
    RESZONE-21 members WACM / PRPA / WAUW carry no sub-BA token
    (FINDING-spp-14 §8.2 item 3) — but EIA-930 does not report them under
    ``SWPP`` either, so they are absent from BOTH sides of the ratio and their
    absence here is consistency, not a gap.

    Returns ``None`` when the raw file is absent, when SPP's hourly frame for
    the year is unavailable, or when the assembled series does not cover the
    year.
    """
    spp_dir = ZONE_DEMAND_DIR / "SPP"
    # Prefer the per-year back-file when one exists (SPP-15 landed 2019-2022
    # that way); otherwise the combined 2023-2025 export.
    path = spp_dir / f"spp_subba_demand_{year}.csv"
    if not path.exists():
        path = spp_dir / "spp_subba_demand_2023-2025.csv"
    if not path.exists():
        logger.warning("SPP sub-BA load file not found (%s); skipping", path)
        return None
    df = pd.read_csv(path, usecols=["period", "subba", "value"], dtype={"subba": str})
    df = df[df["subba"].isin(_SPP_SUBBA_ZONE_GROUPS)].copy()
    period_utc = pd.to_datetime(df["period"], format="%Y-%m-%dT%H", errors="coerce")
    hoy_local = _spp_utc_to_local_hoy(period_utc, year)
    if hoy_local is None:
        logger.warning("SPP hourly frame unavailable for %d; skipping", year)
        return None
    keep = ~df.duplicated(subset=["period", "subba"], keep="first")
    keep &= hoy_local.notna().to_numpy()
    df, hoy_local = df[keep], hoy_local[keep]
    if df.empty:
        logger.warning("SPP sub-BA load file has no rows for %d; skipping", year)
        return None
    df = df.assign(
        hoy=hoy_local.to_numpy(dtype=int),
        mw=pd.to_numeric(df["value"], errors="coerce"),
    )
    wide = (
        df.pivot_table(index="hoy", columns="subba", values="mw", aggfunc="first")
        .sort_index()
        .ffill()
        .bfill()
    )
    long = (
        wide.reset_index()
        .melt(id_vars="hoy", var_name="subba", value_name="mw")
        .dropna(subset=["mw"])
    )
    mzone = long["subba"].map(_SPP_SUBBA_ZONE_GROUPS)
    shares = _hourly_shares_from_groups(
        mzone, long["hoy"].to_numpy(), long["mw"], zone_names
    )
    # Same guard as the MISO parser: the multi-year export spans only the years
    # it was pulled for, and for any other year the UTC->local mapping still
    # lands a handful of rows (Jan 1st's first UTC hours belong to the previous
    # local year), which the ``df.empty`` check above does not catch.  A short
    # year would otherwise return shares that are NaN for the rest of the clock
    # and propagate straight into ``load_demand``'s zonal allocation.
    if shares is None or np.isnan(shares).any():
        logger.warning(
            "SPP sub-BA load file covers %d only partially (%d/%d hours); skipping",
            year,
            0 if shares is None else int((~np.isnan(shares[0])).sum()),
            HOURS_PER_YEAR,
        )
        return None
    return shares


# ---------------------------------------------------------------------------
# NWPP — a POOL of seventeen balancing authorities, so the zonal shares are a
# REGROUP of the same per-BA series the pool's own system demand is summed
# from, not a separate sub-BA product (there is none: EIA-930 publishes no
# sub-BA series for any of the 17, plan §2.5 / gate G18, which is exactly why
# a zone may not split a BA).  Landed 2026-09-14 by lane NWPP-33.
# ---------------------------------------------------------------------------


def parse_nwpp_shares(year: int, zone_names: list[str]) -> np.ndarray | None:
    """Regroup the NWPP pool's member demand into ``(n_zones, 8760)`` shares.

    NWPP is the repo's only POOL region: its system demand is already the
    UTC-joined sum of seventeen per-BA EIA-930 extracts
    (``eia930.frames._pool_hourly_frame``).  Every model zone is a whole-BA
    group (owner ruling N5; ``zone_assignment._NWPP_BA_ZONES``), so the zonal
    shares are that same sum taken in five parts instead of one — a REGROUP of
    the identical arithmetic, not a second data source.  Three consequences,
    all measured by this lane (``docs/handoffs/FINDING-nwpp-33-2026-09-14.md``):

    * **The shares are exact, not approximate.**  Because the numerator parts
      and the denominator come from one pass over one set of arrays, the
      per-zone sum reproduces the pool frame's own ``Demand`` column to
      **0.0 MW** in every hour of 2023, 2024 and 2025 — verified in
      :mod:`tests.curation.test_curate_zonal_shares_nwpp`.  No other ISO's
      parser can say that: each of them ratios one published series against a
      differently-sourced system total.
    * **The demand convention is NOT optional and is inherited, not restated**
      (NWPP-10 §1.3 / audit §4.4).  Each member is read on
      ``Demand (Adjusted)`` — which repairs all 30 artifact hours of 2023-2025
      — and passed through the exact-zero dropout screen (17 NEVP hours of
      2025).  ``_screen_demand_spikes`` is deliberately NOT applied: its
      2.5 x median bar flags 54 REAL CHPD hours of 12-16 January 2024, a
      documented cold snap holding CHPD's annual peak (583 MW, peak/median
      2.83) and the whole NWPP-NW zone's 2024 annual peak (21,560 MW at
      2024-01-13 19:00 UTC), on which EIA's own ``Adjusted`` column is
      byte-identical to raw.  Deleting them would be a rule-14 ``[R-ACCURATE]``
      violation by construction.  This function re-uses
      :func:`~market_sim.data.eia930.frames._pool_member_frames` and the pool
      builder's own screening rather than re-implementing it, so the convention
      cannot drift between the system total and its parts (rule 19
      ``[R-ONE-MECH]``).
    * **The clock is the pool clock.**  ``_pool_member_frames`` re-indexes every
      member onto the ``_POOL_CLOCK_BA`` (BPAT) Pacific local year by a pure UTC
      join, so the three Mountain members (NWMT, PACE, WAUW) land on the Pacific
      hour that is the same physical hour, and row ``k`` here is the same
      positional hour ``k`` the system demand and the renewable CF use
      (card N6 / gate G19: UTC is the canonical key, local time is provenance).

    The two generation-only members (AVRN, GRID) carry null demand in all
    26,304 hours and enter their zones as exactly 0.0, so they move no share;
    their GENERATION still lands in NWPP-NW / NWPP-OR through the same zone map
    (that is the supply side, and it is not this function's business).

    Nothing is padded, interpolated or rescaled beyond the two repairs the pool
    builder already performs (rule 13 ``[R-MEASURED]``).

    Args:
        year: Calendar year.
        zone_names: Model zone names in the caller's expected order.

    Returns:
        A ``(n_zones, HOURS_PER_YEAR)`` share array whose columns sum to 1.0,
        or ``None`` when any member extract for ``year`` is unavailable (a pool
        is never served from a subset).
    """
    from market_sim.data.eia930.demand import _screen_demand_dropouts
    from market_sim.data.eia930.frames import (
        _POOL_GENERATION_ONLY_BAS,
        _pool_member_frames,
    )
    from market_sim.data.zone_assignment import _NWPP_BA_ZONES

    members = _pool_member_frames("NWPP", year)
    if members is None:
        logger.warning("NWPP pool member frames unavailable for %d; skipping", year)
        return None

    index = {zone: i for i, zone in enumerate(zone_names)}
    demand = np.zeros((len(zone_names), HOURS_PER_YEAR), dtype=float)
    for ba, frame in members.items():
        zone = _NWPP_BA_ZONES.get(ba)
        if zone is None or zone not in index:
            # A member whose ruled zone is not in the caller's list cannot be
            # dropped silently: its load would vanish from the denominator.
            logger.warning("NWPP member %s maps outside %s; skipping", ba, zone_names)
            return None
        series = frame["Demand (Adjusted)"].to_numpy(dtype=float)
        if ba in _POOL_GENERATION_ONLY_BAS or np.isnan(series).all():
            continue  # generation-only BA: exactly 0.0 load, every hour
        series = pd.Series(series).interpolate().bfill().ffill().to_numpy(dtype=float)
        demand[index[zone]] += _screen_demand_dropouts(series, ba_code=ba, year=year)

    total = demand.sum(axis=0)
    if not np.isfinite(total).all() or (total <= 0.0).any():
        logger.warning("NWPP %d: non-positive footprint demand hour(s); skipping", year)
        return None
    return demand / total


# ---------------------------------------------------------------------------
# Dispatch table: iso -> parse function
# ---------------------------------------------------------------------------
_PARSE_FUNCS = {
    "ERCOT": parse_ercot_shares,
    "CAISO": parse_caiso_shares,
    "PJM": parse_pjm_shares,
    "MISO": parse_miso_shares,
    "NYISO": parse_nyiso_shares,
    "NEISO": parse_neiso_shares,
    "SPP": parse_spp_shares,
    "NWPP": parse_nwpp_shares,
}


# ---------------------------------------------------------------------------
# Public curation entry points
# ---------------------------------------------------------------------------


def curate_iso_year(iso: str, year: int) -> Path | None:
    """Parse raw load data and write a clean zonal-shares Parquet for one ISO-year.

    Returns the path written, or ``None`` if the raw source file is absent.
    """
    iso_config = get_iso_config(iso)
    zone_names = iso_config.zone_names
    parse_fn = _PARSE_FUNCS.get(iso)
    if parse_fn is None:
        logger.error("No zonal-shares parser registered for ISO %s", iso)
        return None
    shares = parse_fn(year, zone_names)
    if shares is None:
        return None
    df = _shares_to_long(shares, zone_names)
    df["hour"] = df["hour"].astype("int64")
    df["zone"] = df["zone"].astype("string")
    df["share"] = df["share"].astype("float64")
    path = write_clean(
        df,
        "zonal-shares",
        iso=iso,
        year=year,
        source=str(ZONE_DEMAND_DIR),
    )
    print(f"  wrote {iso} {year}: {len(df):>7,} rows -> {path}")
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Curate per-ISO zonal load shares from raw demand files."""
    parser = argparse.ArgumentParser(
        description="Curate per-ISO zonal load share fractions from raw demand files."
    )
    parser.add_argument(
        "--iso",
        required=True,
        choices=sorted(_PARSE_FUNCS),
        help="ISO to curate.",
    )
    parser.add_argument(
        "--year",
        required=True,
        type=int,
        nargs="+",
        help="Calendar year(s) to curate.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    written: list[Path] = []
    for year in args.year:
        path = curate_iso_year(args.iso, year)
        if path is not None:
            written.append(path)

    if written:
        print(f"\nzonal-shares curation complete: {len(written)} file(s) written.")
    else:
        print("\nzonal-shares curation complete: no files written (raw data absent?).")
        sys.exit(1)


if __name__ == "__main__":
    main()
