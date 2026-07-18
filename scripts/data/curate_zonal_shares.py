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

Supported ISOs: ERCOT, CAISO, PJM, MISO, NYISO, NEISO

Usage
-----
  python scripts/data/curate_zonal_shares.py --iso ERCOT --year 2023
  python scripts/data/curate_zonal_shares.py --iso PJM --year 2023 2024 2025
  python scripts/data/curate_zonal_shares.py --iso MISO --year 2023
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
    df = pd.read_csv(path, usecols=["datetime_beginning_ept", "zone", "mw"])
    df = df[df["zone"] != "RTO"].copy()
    df["mzone"] = df["zone"].map(_PJM_LOAD_ZONE_GROUPS)
    if df["mzone"].isna().any():
        missing = sorted(df.loc[df["mzone"].isna(), "zone"].unique())
        logger.warning("PJM load zones not mapped to a model zone: %s", missing)
        df = df.dropna(subset=["mzone"])
    ts = pd.to_datetime(df["datetime_beginning_ept"], format="mixed", errors="coerce")
    file_year = int(ts.dt.year.mode().iat[0])
    if file_year != year:
        logger.warning(
            "PJM%d_hrl_load_metered.csv actually contains %d data; using its "
            "zonal *shape* against %d system demand",
            year,
            file_year,
            year,
        )
    keep = ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df, ts = df[keep], ts[keep]
    return _hourly_shares_from_groups(
        df["mzone"], _hours_of_year(ts), df["mw"], zone_names
    )


def parse_ercot_shares(year: int, zone_names: list[str]) -> np.ndarray | None:
    """Parse ERCOT native-load XLSX -> ``(n_zones, HOURS_PER_YEAR)`` shares.

    Reads ``data/raw/zone-specific-demand/ERCOT_Native_Load_{year}.xlsx``
    (NP3-565-CD), maps the eight weather zones to the model transmission zones,
    and normalises each hour to fractions summing to 1.0.  Returns ``None``
    when the file is absent.
    """
    path = ZONE_DEMAND_DIR / f"ERCOT_Native_Load_{year}.xlsx"
    if not path.exists():
        logger.warning("ERCOT native-load file not found (%s); skipping", path)
        return None
    df = pd.read_excel(path)
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

    Reads the combined multi-year file
    ``data/raw/zone-specific-demand/MISO/miso_subba_demand_2023-2025.csv``,
    filters to ``year``, maps the six sub-BAs to the three model zones, and
    normalises each hour.  The UTC ``period`` column is mapped to the model's
    local hour-of-year via the MISO hourly frame so zonal shapes index the
    same wall-clock hour as renewable CF.  Returns ``None`` when the file (or
    the MISO hourly frame) is absent.
    """
    path = ZONE_DEMAND_DIR / "MISO" / "miso_subba_demand_2023-2025.csv"
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
    return _hourly_shares_from_groups(
        mzone, long["hoy"].to_numpy(), long["mw"], zone_names
    )


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
# Dispatch table: iso -> parse function
# ---------------------------------------------------------------------------
_PARSE_FUNCS = {
    "ERCOT": parse_ercot_shares,
    "CAISO": parse_caiso_shares,
    "PJM": parse_pjm_shares,
    "MISO": parse_miso_shares,
    "NYISO": parse_nyiso_shares,
    "NEISO": parse_neiso_shares,
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
