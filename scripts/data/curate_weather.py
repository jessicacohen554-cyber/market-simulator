"""Curate daily weather observations from per-ISO raw weather files.

Reads each ISO's raw weather CSV file(s) from ``data/raw/{iso}-weather/``
using the same parsing logic as the legacy weather functions in
``src/market_sim/data/eia_loader.py``, and writes one clean Parquet per
``(iso, year)`` through the frozen ``scripts/lib/clean_io.write_clean`` seam.

Output schema: ``data/dictionary/schema/weather.schema.yaml``
  - Long format: one row per (date, zone).
  - ``date``   — calendar date (datetime64[ns], tz-naive local).
  - ``zone``   — model zone name or sentinel ('_load_weighted', '_downstate').
  - ``tmax_c`` — daily max temperature in deg C (float64, non-nullable).
  - ``tmin_c`` — daily min temperature in deg C (float64, nullable).

Sentinel zone names written by this script:
  ``'_load_weighted'`` — ISO-level load-weighted temperature aggregate (CAISO
                         and NEISO; sourced from their *_load_weighted_*_daily
                         files).
  ``'_downstate'``     — NYISO NYC-metro (Central Park/LaGuardia/JFK) aggregate;
                         sourced from nyiso_downstate_tmax_daily.csv.

Output path (via clean_path): ``data/clean/weather/<ISO>/weather_<year>.parquet``

Supported ISOs: ERCOT, CAISO, PJM, MISO, NYISO, NEISO

Usage
-----
  python scripts/data/curate_weather.py --iso ERCOT --year 2023
  python scripts/data/curate_weather.py --iso CAISO --year 2023 2024 2025
  python scripts/data/curate_weather.py --iso NYISO --year 2023 2024 2025
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR
from scripts.lib.clean_io import write_clean

logger = logging.getLogger(__name__)

# Root for all ISO weather directories.
_WEATHER_RAW_ROOT: Path = RAW_DIR


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_zone_temp(path: Path, year: int) -> pd.DataFrame | None:
    """Read a ``date,zone,tmax_c[,tmin_c]`` CSV and return a normalised frame.

    Beyond the base ``path``, also reads any year-partitioned supplementary
    files alongside it (``<stem>_<year|yearQn>.csv``, e.g.
    ``ercot_zone_temp_daily_2022.csv`` or ``..._2026q1.csv``) so a calendar
    range can be extended without rewriting the (already-committed) base
    file's full history. Filters to ``year``, adds ``tmin_c`` (NaN) when
    absent, gap-fills tmax_c per-zone via ffill/bfill, and returns a
    ``(date, zone, tmax_c, tmin_c)`` DataFrame. Returns ``None`` when no
    source file is present or none covers rows for ``year``.
    """
    supplements = sorted(path.parent.glob(f"{path.stem}_*.csv"))
    parts = [p for p in [path, *supplements] if p.exists()]
    if not parts:
        logger.warning("weather file not found (%s); skipping", path)
        return None
    df = pd.concat(
        (pd.read_csv(p, parse_dates=["date"]) for p in parts), ignore_index=True
    ).drop_duplicates(subset=["date", "zone"])
    df = df[df["date"].dt.year == year].copy()
    if df.empty:
        logger.warning("%s has no data for %d; skipping", path.name, year)
        return None
    df["tmax_c"] = pd.to_numeric(df["tmax_c"], errors="coerce")
    if "tmin_c" in df.columns:
        df["tmin_c"] = pd.to_numeric(df["tmin_c"], errors="coerce")
    else:
        df["tmin_c"] = np.nan
    # Gap-fill tmax_c per zone so no null values remain in the clean file.
    if "zone" in df.columns:
        df["tmax_c"] = (
            df.sort_values(["zone", "date"])
            .groupby("zone", group_keys=False)["tmax_c"]
            .transform(lambda s: s.ffill().bfill())
        )
    else:
        df["tmax_c"] = df["tmax_c"].ffill().bfill()
    return df[["date", "zone", "tmax_c", "tmin_c"]].reset_index(drop=True)


def _read_no_zone_temp(
    path: Path, year: int, zone: str, *, has_tmin: bool
) -> pd.DataFrame | None:
    """Read a ``date,tmax_c[,tmin_c]`` CSV (no zone column) and assign sentinel.

    Returns a ``(date, zone, tmax_c, tmin_c)`` DataFrame with zone set to
    ``zone`` (a sentinel such as ``'_load_weighted'`` or ``'_downstate'``).
    Returns ``None`` when the file is absent or covers no rows for ``year``.
    """
    if not path.exists():
        logger.warning("weather file not found (%s); skipping", path)
        return None
    df = pd.read_csv(path, parse_dates=["date"])
    df = df[df["date"].dt.year == year].copy()
    if df.empty:
        logger.warning("%s has no data for %d; skipping", path.name, year)
        return None
    df["zone"] = zone
    df["tmax_c"] = pd.to_numeric(df["tmax_c"], errors="coerce")
    df["tmax_c"] = df["tmax_c"].ffill().bfill()
    if has_tmin and "tmin_c" in df.columns:
        df["tmin_c"] = pd.to_numeric(df["tmin_c"], errors="coerce")
    else:
        df["tmin_c"] = np.nan
    return df[["date", "zone", "tmax_c", "tmin_c"]].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Per-ISO parse functions
# ---------------------------------------------------------------------------


def parse_ercot_weather(year: int) -> pd.DataFrame | None:
    """Parse ERCOT per-zone daily weather CSV -> ``(date, zone, tmax_c, tmin_c)``.

    Reads ``data/raw/ercot-weather/ercot_zone_temp_daily.csv``
    (schema ``date,zone,tmax_c,tmin_c``) and returns one row per (date, zone)
    for ``year``.  Returns ``None`` when the file is absent.
    """
    path = _WEATHER_RAW_ROOT / "ercot-weather" / "ercot_zone_temp_daily.csv"
    return _read_zone_temp(path, year)


def parse_caiso_weather(year: int) -> pd.DataFrame | None:
    """Parse CAISO per-zone + load-weighted weather -> ``(date, zone, tmax_c, tmin_c)``.

    Reads:
      - ``caiso_zone_temp_daily.csv`` (date, zone, tmax_c, tmin_c) — per
        trading-hub zone (NP15, SP15, ZP26).
      - ``caiso_load_weighted_tmax_daily.csv`` (date, tmax_c) — ISO-level
        load-weighted TMAX aggregate, written as zone ``'_load_weighted'`` with
        tmin_c NaN.

    Returns the concatenated frame, or ``None`` when both files are absent.
    """
    parts: list[pd.DataFrame] = []

    zone_path = _WEATHER_RAW_ROOT / "caiso-weather" / "caiso_zone_temp_daily.csv"
    df_zone = _read_zone_temp(zone_path, year)
    if df_zone is not None:
        parts.append(df_zone)

    lw_path = _WEATHER_RAW_ROOT / "caiso-weather" / "caiso_load_weighted_tmax_daily.csv"
    df_lw = _read_no_zone_temp(lw_path, year, zone="_load_weighted", has_tmin=False)
    if df_lw is not None:
        parts.append(df_lw)

    if not parts:
        return None
    return pd.concat(parts, ignore_index=True)


def parse_pjm_weather(year: int) -> pd.DataFrame | None:
    """Parse PJM per-zone daily weather CSV -> ``(date, zone, tmax_c, tmin_c)``.

    Reads ``data/raw/pjm-weather/pjm_zone_temp_daily.csv``
    (schema ``date,zone,tmax_c,tmin_c``) and returns one row per (date, zone)
    for ``year``.  Returns ``None`` when the file is absent.
    """
    path = _WEATHER_RAW_ROOT / "pjm-weather" / "pjm_zone_temp_daily.csv"
    return _read_zone_temp(path, year)


def parse_miso_weather(year: int) -> pd.DataFrame | None:
    """Parse MISO per-zone daily weather CSV -> ``(date, zone, tmax_c, tmin_c)``.

    Reads ``data/raw/miso-weather/miso_zone_temp_daily.csv``
    (schema ``date,zone,tmax_c,tmin_c``) and returns one row per (date, zone)
    for ``year``.  Returns ``None`` when the file is absent.
    """
    path = _WEATHER_RAW_ROOT / "miso-weather" / "miso_zone_temp_daily.csv"
    return _read_zone_temp(path, year)


def parse_nyiso_weather(year: int) -> pd.DataFrame | None:
    """Parse NYISO per-zone + downstate weather -> ``(date, zone, tmax_c, tmin_c)``.

    Reads:
      - ``nyiso_zone_temp_daily.csv`` (date, zone, tmax_c, tmin_c) — per model
        zone (Capital_Hudson, Long_Island, NYC, Upstate_NY, Rest_of_State).
      - ``nyiso_downstate_tmax_daily.csv`` (date, tmax_c) — NYC-metro aggregate
        (Central Park / LaGuardia / JFK mean), written as zone ``'_downstate'``
        with tmin_c NaN.

    Note: ``nyiso_zone_tmax_daily.csv`` (TMAX-only per-zone legacy file) is not
    separately included because ``nyiso_zone_temp_daily.csv`` covers the same
    zones with both TMAX and TMIN.

    Returns the concatenated frame, or ``None`` when both files are absent.
    """
    parts: list[pd.DataFrame] = []

    zone_path = _WEATHER_RAW_ROOT / "nyiso-weather" / "nyiso_zone_temp_daily.csv"
    df_zone = _read_zone_temp(zone_path, year)
    if df_zone is not None:
        parts.append(df_zone)

    ds_path = _WEATHER_RAW_ROOT / "nyiso-weather" / "nyiso_downstate_tmax_daily.csv"
    df_ds = _read_no_zone_temp(ds_path, year, zone="_downstate", has_tmin=False)
    if df_ds is not None:
        parts.append(df_ds)

    if not parts:
        return None
    return pd.concat(parts, ignore_index=True)


def parse_neiso_weather(year: int) -> pd.DataFrame | None:
    """Parse NEISO per-zone + load-weighted weather -> ``(date, zone, tmax_c, tmin_c)``.

    Reads:
      - ``neiso_zone_temp_daily.csv`` (date, zone, tmax_c, tmin_c) — per model
        zone (Boston, Hartford, Portland, Rest_of_NE).
      - ``neiso_load_weighted_temp_daily.csv`` (date, tmax_c, tmin_c) — ISO-level
        load-weighted aggregate (Boston-Logan / Providence / Hartford-Bradley /
        Portland-ME / Concord-NH / Burlington-VT), written as zone
        ``'_load_weighted'``.

    Returns the concatenated frame, or ``None`` when both files are absent.
    """
    parts: list[pd.DataFrame] = []

    zone_path = _WEATHER_RAW_ROOT / "neiso-weather" / "neiso_zone_temp_daily.csv"
    df_zone = _read_zone_temp(zone_path, year)
    if df_zone is not None:
        parts.append(df_zone)

    lw_path = _WEATHER_RAW_ROOT / "neiso-weather" / "neiso_load_weighted_temp_daily.csv"
    df_lw = _read_no_zone_temp(lw_path, year, zone="_load_weighted", has_tmin=True)
    if df_lw is not None:
        parts.append(df_lw)

    if not parts:
        return None
    return pd.concat(parts, ignore_index=True)


# ---------------------------------------------------------------------------
# Dispatch table: iso -> parse function
# ---------------------------------------------------------------------------
_PARSE_FUNCS: dict[str, object] = {
    "ERCOT": parse_ercot_weather,
    "CAISO": parse_caiso_weather,
    "PJM": parse_pjm_weather,
    "MISO": parse_miso_weather,
    "NYISO": parse_nyiso_weather,
    "NEISO": parse_neiso_weather,
}


# ---------------------------------------------------------------------------
# Public curation entry points
# ---------------------------------------------------------------------------


def curate_iso_year(iso: str, year: int) -> Path | None:
    """Parse raw weather files and write a clean weather Parquet for one ISO-year.

    Returns the path written, or ``None`` if all raw source files are absent.
    """
    iso = iso.upper()
    parse_fn = _PARSE_FUNCS.get(iso)
    if parse_fn is None:
        logger.error("No weather parser registered for ISO %s", iso)
        return None

    df = parse_fn(year)
    if df is None:
        return None

    # Enforce schema dtypes before writing.
    df["date"] = pd.to_datetime(df["date"])
    df["zone"] = df["zone"].astype("string")
    df["tmax_c"] = df["tmax_c"].astype("float64")
    df["tmin_c"] = df["tmin_c"].astype("float64")

    path = write_clean(
        df,
        "weather",
        iso=iso,
        year=year,
        source=str(_WEATHER_RAW_ROOT / f"{iso.lower()}-weather"),
    )
    print(f"  wrote {iso} {year}: {len(df):>6,} rows -> {path}")
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Curate per-ISO daily weather from raw NOAA/GHCN CSV files."""
    parser = argparse.ArgumentParser(
        description="Curate per-ISO daily weather observations from raw CSV files."
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
        print(f"\nweather curation complete: {len(written)} file(s) written.")
    else:
        print("\nweather curation complete: no files written (raw data absent?).")
        sys.exit(1)


if __name__ == "__main__":
    main()
