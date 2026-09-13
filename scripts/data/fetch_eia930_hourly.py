#!/usr/bin/env python3
"""Fetch EIA-930 hourly Grid Monitor data and write the wide ``<BA> hourly``
parquet that ``data/eia_loader.py`` reads.

The hourly extracts in ``data/eia_hourly/`` were originally hand-uploaded; this
script makes the pull reproducible. It mirrors the EIA-API convention used by
``fetch_eia860.py`` (``EIA_API_KEY`` env var or ``.env`` fallback) and emits the
exact column schema the loader expects:

    UTC time, Local time, Local date, Demand, Net generation, Total interchange,
    NG: COL, NG: NG, NG: NUC, NG: OIL, NG: WAT, NG: SUN, NG: WND, NG: BAT,
    NG: PS, NG: OTH, ...   (one ``NG: <code>`` per fuel type EIA reports)

The demand / net-generation / total-interchange series come from the RTO
``region-data`` endpoint (types D / NG / TI); the per-fuel net generation comes
from ``fuel-type-data``. ``period`` is UTC hour-ending, matching the Grid
Monitor; ``Local time`` / ``Local date`` are the BA-timezone conversion used to
restrict a frame to a local calendar year.

Run locally (the managed environment's allowlist blocks api.eia.gov):

    python scripts/data/fetch_eia930_hourly.py --ba NYIS --start 2023-01-01 \
        --end 2025-12-31

Then upload the refreshed ``data/eia_hourly/NYIS hourly.parquet``.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.env_keys import get_api_key  # noqa: E402

REGION_URL = "https://api.eia.gov/v2/electricity/rto/region-data/data/"
FUEL_URL = "https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "eia_hourly"
PAGE_SIZE = 5000  # EIA API v2 max rows per request

# BA local timezone — used to convert the UTC ``period`` to the ``Local time`` /
# ``Local date`` columns the loader filters a calendar year on.
BA_TIMEZONE: dict[str, str] = {
    "NYIS": "America/New_York",
    "ISNE": "America/New_York",
    "PJM": "America/New_York",
    "MISO": "America/Chicago",
    "SWPP": "America/Chicago",
    "ERCO": "America/Chicago",
    "CISO": "America/Los_Angeles",
    # SOCO spans two civil zones — Alabama and Mississippi Power are Central,
    # Georgia Power is Eastern — but EIA stamps the BA on ONE clock, and that
    # clock is Central. MEASURED (soco-11, 2026-09-13), not assumed, on two
    # independent sources that agree:
    #   * the committed ``data/raw/eia-930-hourly/SOCO hourly.parquet`` carries
    #     exactly two UTC-minus-local offsets, 6 h (9,171 rows) and 5 h (17,133
    #     rows), switching on the US DST dates — i.e. CST/CDT, never EST/EDT;
    #   * all four Southern FERC Form 714 respondents (Alabama Power 2, Georgia
    #     Power 183, Mississippi Power 184, Southern company 142) report
    #     ``timezone = America/Chicago`` in PUDL's ETL of the form.
    # Georgia Power's own operating clock is Eastern; this key is the BA's
    # reporting clock, which is what this product is stamped on. Every SOCO
    # series downstream must adopt Central for that reason.
    "SOCO": "America/Chicago",
}

# region-data ``type`` code -> output column name.
REGION_TYPES: dict[str, str] = {
    "D": "Demand",
    "NG": "Net generation",
    "TI": "Total interchange",
}


def _api_key() -> str:
    """Resolve the EIA API key from the environment or the repo ``.env``."""
    return get_api_key(
        "EIA_API_KEY", hint="free at https://www.eia.gov/opendata/register.php"
    )


_RATE_LIMIT_BACKOFFS_S = (15, 30, 60, 120, 240)  # DEMO_KEY throttles bursts


def _fetch(url: str, params: dict, key: str) -> list[dict]:
    """Page through an EIA API v2 data endpoint, returning all rows.

    ``DEMO_KEY`` enforces a tight burst rate limit that a single multi-page
    pull can trip on its own (not just across separate script invocations),
    so a 429 retries with backoff rather than failing the whole pull.
    """
    rows: list[dict] = []
    offset = 0
    while True:
        page = dict(params, api_key=key, offset=offset, length=PAGE_SIZE)
        for backoff in (*_RATE_LIMIT_BACKOFFS_S, None):
            resp = requests.get(url, params=page, timeout=120)
            if resp.status_code != 429:
                break
            if backoff is None:
                resp.raise_for_status()
            time.sleep(backoff)
        resp.raise_for_status()
        data = resp.json()["response"]["data"]
        rows.extend(data)
        if len(data) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE


def _region_frame(ba: str, start: str, end: str, key: str) -> pd.DataFrame:
    """Demand / net-generation / total-interchange wide frame, indexed by UTC."""
    params = {
        "frequency": "hourly",
        "data[0]": "value",
        "facets[respondent][]": ba,
        "start": f"{start}T00",
        "end": f"{end}T23",
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
    }
    df = pd.DataFrame(_fetch(REGION_URL, params, key))
    df = df[df["type"].isin(REGION_TYPES)].copy()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    wide = df.pivot_table(index="period", columns="type", values="value")
    return wide.rename(columns=REGION_TYPES)


def _fuel_frame(ba: str, start: str, end: str, key: str) -> pd.DataFrame:
    """Per-fuel net generation wide frame (``NG: <code>``), indexed by UTC."""
    params = {
        "frequency": "hourly",
        "data[0]": "value",
        "facets[respondent][]": ba,
        "start": f"{start}T00",
        "end": f"{end}T23",
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
    }
    df = pd.DataFrame(_fetch(FUEL_URL, params, key))
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    wide = df.pivot_table(index="period", columns="fueltype", values="value")
    return wide.rename(columns={c: f"NG: {c}" for c in wide.columns})


def build(ba: str, start: str, end: str) -> pd.DataFrame:
    """Assemble the wide hourly frame in the loader's schema for one BA."""
    key = _api_key()
    region = _region_frame(ba, start, end, key)
    fuel = _fuel_frame(ba, start, end, key)
    frame = region.join(fuel, how="outer").sort_index()

    tz = BA_TIMEZONE.get(ba, "America/New_York")
    utc = pd.to_datetime(frame.index, utc=True)
    local = utc.tz_convert(tz)
    out = frame.reset_index(drop=True)
    out.insert(0, "UTC time", utc.tz_localize(None))
    out.insert(1, "Local time", local.tz_localize(None))
    out.insert(2, "Local date", local.tz_localize(None).normalize())
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ba", required=True, help="EIA-930 BA code, e.g. NYIS")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD (inclusive)")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output parquet (default: data/eia_hourly/<BA> hourly.parquet)",
    )
    args = ap.parse_args()

    frame = build(args.ba, args.start, args.end)
    out = args.out or OUTPUT_DIR / f"{args.ba} hourly.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out, index=False)

    span = f"{frame['Local date'].min().date()}..{frame['Local date'].max().date()}"
    fuels = [c for c in frame.columns if c.startswith("NG: ")]
    print(f"wrote {out} — {len(frame):,} hourly rows ({span})")
    print(f"  columns: Demand, Net generation, Total interchange + {len(fuels)} fuels")
    print(f"  fuels: {', '.join(sorted(fuels))}")


if __name__ == "__main__":
    main()
