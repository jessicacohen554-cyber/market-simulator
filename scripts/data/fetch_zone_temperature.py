"""Fetch + load-weight NOAA GHCN-Daily zonal TMAX/TMIN for every ISO model zone.

A single generic replacement for the per-ISO ``fetch_*`` halves of the legacy
``derive_*_reliability_floor.py`` scripts. Reads the checked-in station-weight
table ``data/raw/reference/iso_zone_weather_stations.csv`` (one row per
``iso,zone,station_id,weight,station_name``), pulls each station's daily
temperature record from the NOAA GHCN-Daily **access CSV** endpoint, load-weights
TMAX and TMIN per (zone, date) by the station weights, and writes the canonical
per-ISO zonal daily series ``data/raw/<iso_lower>-weather/<iso_lower>_zone_temp_daily.csv``
with columns ``date,zone,tmax_c,tmin_c`` (matching the existing MISO file).

GHCN-Daily TMAX/TMIN are recorded in tenths of a degree Celsius, so they are
divided by 10 to recover degrees Celsius (the canonical schema unit).

The raw per-station pulls are cached under
``data/raw/<iso_lower>-weather/_ghcn_cache/<station>.csv`` on fetch; ``--no-fetch``
re-derives the zonal series purely from that cache (offline / CI). Forecast years
pin a weather year, so the same zonal series regenerates from a pinned year
(CLAUDE.md #10) and responds to changed weather — an admissible physical input.

Usage:
    python scripts/data/fetch_zone_temperature.py --iso ALL
    python scripts/data/fetch_zone_temperature.py --iso ERCOT PJM --start 2023 --end 2025
    python scripts/data/fetch_zone_temperature.py --iso ALL --no-fetch
"""

from __future__ import annotations

import argparse
import logging
import subprocess

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR, REFERENCE_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("fetch_zone_temperature")

# Checked-in station-weight table: iso,zone,station_id,weight,station_name.
STATION_TABLE = REFERENCE_DIR / "iso_zone_weather_stations.csv"

# NOAA GHCN-Daily per-station "access" CSV (full daily record, all data types).
# Confirmed reachable through the agent proxy (HTTP 200). One file per station.
_GHCN_ACCESS_URL = (
    "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily"
    "/access/{station}.csv"
)

# GHCN-Daily records TMAX/TMIN in tenths of a degree Celsius.
_GHCN_TENTHS_PER_DEGREE = 10.0


def _iso_weather_dir(iso: str) -> "object":
    """Return the per-ISO weather directory ``data/raw/<iso_lower>-weather/``."""
    return RAW_DIR / f"{iso.lower()}-weather"


def _cache_path(iso: str, station: str) -> "object":
    """Return the cached raw per-station CSV path for an ISO."""
    return _iso_weather_dir(iso) / "_ghcn_cache" / f"{station}.csv"


def load_station_table() -> pd.DataFrame:
    """Load the checked-in (iso, zone, station_id, weight, station_name) table."""
    if not STATION_TABLE.exists():
        raise FileNotFoundError(f"station table not found: {STATION_TABLE}")
    df = pd.read_csv(STATION_TABLE, dtype={"station_id": str})
    df["iso"] = df["iso"].str.upper()
    return df


def fetch_station_record(iso: str, station: str, no_fetch: bool) -> pd.DataFrame:
    """Return one station's daily ``date,TMAX,TMIN`` frame (degrees Celsius).

    On a network fetch the raw access CSV is cached under the ISO's
    ``_ghcn_cache/`` so ``--no-fetch`` can re-derive offline. With ``no_fetch``
    the cached CSV is read instead of hitting the network. TMAX/TMIN are converted
    from GHCN tenths-degC to degrees Celsius.
    """
    cache = _cache_path(iso, station)
    if no_fetch:
        if not cache.exists():
            raise FileNotFoundError(
                f"--no-fetch but no cache for {iso} {station}: {cache}"
            )
        raw = pd.read_csv(cache, low_memory=False)
    else:
        url = _GHCN_ACCESS_URL.format(station=station)
        log.info("fetching %s %s", iso, station)
        cache.parent.mkdir(parents=True, exist_ok=True)
        # Use curl (preconfigured for the agent proxy). Streaming the large
        # access CSV directly through urllib/pandas intermittently truncates
        # (IncompleteRead) behind the proxy; curl with --retry is robust.
        result = subprocess.run(
            ["curl", "-sS", "--fail", "--retry", "3", "-o", str(cache), url],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not cache.exists():
            raise ValueError(
                f"{iso} {station}: curl fetch failed ({result.stderr.strip()})"
            )
        raw = pd.read_csv(cache, low_memory=False)

    cols = set(raw.columns)
    if "TMAX" not in cols or "TMIN" not in cols:
        raise ValueError(f"{iso} {station}: CSV missing TMAX/TMIN columns")
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(raw["DATE"], errors="coerce")
    out["TMAX"] = pd.to_numeric(raw["TMAX"], errors="coerce") / _GHCN_TENTHS_PER_DEGREE
    out["TMIN"] = pd.to_numeric(raw["TMIN"], errors="coerce") / _GHCN_TENTHS_PER_DEGREE
    return out.dropna(subset=["date"])


def derive_iso_zone_temps(
    iso: str, table: pd.DataFrame, start: int, end: int, no_fetch: bool
) -> pd.DataFrame:
    """Build the load-weighted per-zone daily ``date,zone,tmax_c,tmin_c`` frame.

    For each zone the per-station daily TMAX/TMIN are combined with a weighted
    mean over the available (non-missing) stations on each date, so a single
    missing station does not blank the zone-day. Restricted to ``start..end``
    (inclusive years).
    """
    iso_rows = table[table["iso"] == iso.upper()]
    if iso_rows.empty:
        raise ValueError(f"no stations registered for ISO {iso}")

    zone_frames: list[pd.DataFrame] = []
    for zone, grp in iso_rows.groupby("zone", sort=False):
        # Stack every station's daily record with its weight (long form), then
        # take a weighted mean per date over the stations that reported.
        parts: list[pd.DataFrame] = []
        for row in grp.itertuples(index=False):
            rec = fetch_station_record(iso, row.station_id, no_fetch)
            rec = rec[
                (rec["date"].dt.year >= start) & (rec["date"].dt.year <= end)
            ].copy()
            rec["w"] = float(row.weight)
            parts.append(rec)
        stacked = pd.concat(parts, ignore_index=True)

        def _wmean(g: pd.DataFrame, col: str) -> float:
            """Weighted mean over stations reporting ``col`` on a date."""
            v, w = g[col], g["w"]
            m = v.notna()
            return float((v[m] * w[m]).sum() / w[m].sum()) if m.any() else np.nan

        daily = stacked.groupby("date").apply(
            lambda g: pd.Series(
                {"tmax_c": _wmean(g, "TMAX"), "tmin_c": _wmean(g, "TMIN")}
            )
        )
        zf = daily.reset_index()
        zf["zone"] = zone
        zone_frames.append(zf[["date", "zone", "tmax_c", "tmin_c"]])

    out = pd.concat(zone_frames, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    return out.sort_values(["zone", "date"]).reset_index(drop=True)


def write_iso_zone_temps(iso: str, frame: pd.DataFrame) -> "object":
    """Write the per-ISO zonal daily temp CSV; return the path written."""
    out_path = _iso_weather_dir(iso) / f"{iso.lower()}_zone_temp_daily.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out_path, index=False)
    log.info(
        "wrote %d zone-days (%d zones) -> %s",
        len(frame),
        frame["zone"].nunique(),
        out_path,
    )
    return out_path


def main() -> None:
    """CLI: fetch/derive the canonical per-zone daily temperature series per ISO."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--iso",
        nargs="+",
        required=True,
        help="ISO list (e.g. ERCOT PJM CAISO) or ALL for every registered ISO.",
    )
    ap.add_argument("--start", type=int, default=2023, help="First calendar year.")
    ap.add_argument("--end", type=int, default=2025, help="Last calendar year.")
    ap.add_argument(
        "--no-fetch",
        action="store_true",
        help="Re-derive from the cached raw station pulls (no NOAA network call).",
    )
    args = ap.parse_args()

    table = load_station_table()
    if [s.upper() for s in args.iso] == ["ALL"]:
        isos = list(dict.fromkeys(table["iso"]))
    else:
        isos = [s.upper() for s in args.iso]

    for iso in isos:
        try:
            frame = derive_iso_zone_temps(
                iso, table, args.start, args.end, args.no_fetch
            )
            write_iso_zone_temps(iso, frame)
        except (FileNotFoundError, ValueError) as exc:
            log.error("%s: %s", iso, exc)


if __name__ == "__main__":
    main()
