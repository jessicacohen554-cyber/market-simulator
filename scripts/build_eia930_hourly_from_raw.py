#!/usr/bin/env python3
"""Build the wide ``<BA> hourly`` parquet from the local EIA-930 long extracts.

``scripts/fetch_eia930_hourly.py`` pulls the region-data (D/DF/NG/TI) and
fuel-type series straight from ``api.eia.gov`` — but the managed environment's
allowlist blocks that host. When the long-format API extracts have already been
downloaded into ``data/raw/eia-930/<BA>_region.parquet`` and
``<BA>_fueltype.parquet`` (the same rows the API would return, tidy form), this
script assembles the exact wide schema ``data/eia_loader.py`` reads **offline**,
so a refreshed raw drop can be promoted to the hourly extract without network.

It mirrors ``fetch_eia930_hourly.build`` column-for-column: region ``type``
codes map D->Demand, DF->Demand forecast, NG->Net generation, TI->Total
interchange; fuel ``fueltype`` codes become ``NG: <code>``; ``period`` is the
UTC hour-ending stamp, and ``Local time`` / ``Local date`` / ``Hour`` are the
BA-timezone conversion the loader filters a calendar year on.

    python scripts/build_eia930_hourly_from_raw.py --ba NYIS
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
RAW_DIR = REPO / "data" / "raw" / "eia-930"
OUT_DIR = REPO / "data" / "raw" / "eia-930-hourly"

BA_TIMEZONE: dict[str, str] = {
    "NYIS": "America/New_York",
    "ISNE": "America/New_York",
    "PJM": "America/New_York",
    "MISO": "America/Chicago",
    "SWPP": "America/Chicago",
    "ERCO": "America/Chicago",
    "CISO": "America/Los_Angeles",
}

REGION_TYPES: dict[str, str] = {
    "D": "Demand",
    "DF": "Demand forecast",
    "NG": "Net generation",
    "TI": "Total interchange",
}


def _pivot(path: Path, key: str) -> pd.DataFrame:
    """Pivot a tidy ``period x <key>`` long frame to one column per code."""
    df = pd.read_parquet(path)
    df["value_mwh"] = pd.to_numeric(df["value_mwh"], errors="coerce")
    df["period"] = pd.to_datetime(df["period"], utc=True)
    # Duplicate (period, code) rows can appear across overlapping API pulls;
    # the last write wins, matching a fresh single pull.
    df = df.drop_duplicates(subset=["period", key], keep="last")
    return df.pivot(index="period", columns=key, values="value_mwh")


def build(ba: str) -> pd.DataFrame:
    """Assemble the wide hourly frame in the loader's schema for one BA."""
    region = _pivot(RAW_DIR / f"{ba}_region.parquet", "type").rename(
        columns=REGION_TYPES
    )
    fuel = _pivot(RAW_DIR / f"{ba}_fueltype.parquet", "fueltype")
    fuel = fuel.rename(columns={c: f"NG: {c}" for c in fuel.columns})
    frame = region.join(fuel, how="outer").sort_index()

    tz = BA_TIMEZONE.get(ba, "America/New_York")
    utc = pd.DatetimeIndex(frame.index)
    local = utc.tz_convert(tz)
    out = frame.reset_index(drop=True)
    out.insert(0, "UTC time", utc.tz_localize(None))
    out.insert(1, "Local date", local.tz_localize(None).normalize())
    out.insert(2, "Hour", local.hour)
    out.insert(3, "Local time", local.tz_localize(None))

    ng_cols = sorted(c for c in out.columns if c.startswith("NG: "))
    lead = [
        "UTC time",
        "Local date",
        "Hour",
        "Local time",
        "Demand forecast",
        "Demand",
        "Net generation",
        "Total interchange",
    ]
    return out[[c for c in lead if c in out.columns] + ng_cols]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ba", required=True, help="EIA-930 BA code, e.g. NYIS")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    frame = build(args.ba)
    out = args.out or OUT_DIR / f"{args.ba} hourly.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out, index=False)

    span = f"{frame['Local date'].min().date()}..{frame['Local date'].max().date()}"
    fuels = [c for c in frame.columns if c.startswith("NG: ")]
    print(f"wrote {out} — {len(frame):,} hourly rows ({span})")
    print(f"  fuels: {', '.join(fuels)}")


if __name__ == "__main__":
    main()
