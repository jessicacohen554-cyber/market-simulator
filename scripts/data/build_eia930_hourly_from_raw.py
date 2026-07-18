#!/usr/bin/env python3
"""Build the wide ``<BA> hourly`` parquet from the local EIA-930 long extracts.

``scripts/data/fetch_eia930_hourly.py`` pulls the region-data (D/DF/NG/TI) and
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

    python scripts/data/build_eia930_hourly_from_raw.py --ba NYIS
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from convert_eia930 import _build_time_columns, _ordered_fuel_columns

REPO = Path(__file__).resolve().parent.parent.parent
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


def _long_files(ba: str, kind: str) -> list[Path]:
    """All long extracts for one BA/kind: base file + year-suffixed siblings.

    The original 2023-2025 uploads live as ``<BA>_<kind>.parquet`` (some at the
    ``data/raw`` top level, some under ``data/raw/eia-930/``); raw is immutable,
    so later years land beside them as NEW ``<BA>_<kind>_<year>.parquet`` files
    (``scripts/data/fetch_eia930_long.py``). The wide extract is built from the
    union.
    """
    roots = (RAW_DIR, RAW_DIR.parent)
    files = [p for root in roots for p in sorted(root.glob(f"{ba}_{kind}*.parquet"))]
    if not files:
        raise FileNotFoundError(f"no {ba}_{kind}*.parquet under {roots}")
    return files


def _pivot(paths: list[Path], key: str) -> pd.DataFrame:
    """Pivot tidy ``period x <key>`` long frames to one column per code."""
    df = pd.concat([pd.read_parquet(p) for p in paths], ignore_index=True)
    df["value_mwh"] = pd.to_numeric(df["value_mwh"], errors="coerce")
    df["period"] = pd.to_datetime(df["period"], utc=True)
    # Duplicate (period, code) rows can appear across overlapping API pulls;
    # the last write wins, matching a fresh single pull.
    df = df.drop_duplicates(subset=["period", key], keep="last")
    return df.pivot(index="period", columns=key, values="value_mwh")


def build(ba: str) -> pd.DataFrame:
    """Assemble the wide hourly frame in the loader's schema for one BA."""
    region = _pivot(_long_files(ba, "region"), "type").rename(columns=REGION_TYPES)
    fuel = _pivot(_long_files(ba, "fueltype"), "fueltype")
    fuel = fuel.rename(columns={c: f"NG: {c}" for c in fuel.columns})
    frame = region.join(fuel, how="outer").sort_index()

    tz = BA_TIMEZONE.get(ba, "America/New_York")
    period = frame.index.to_series().reset_index(drop=True)
    out = frame.reset_index(drop=True)
    # EIA hour-ending time columns (Hour 1..24/25, local midnight dated to the
    # previous day) via the shared converter helper — the convention of the EIA
    # Grid Monitor exports and of the committed ERCO/PJM/CISO/MISO/ISNE
    # extracts. (The NYIS extract predates this and carries clock hours 0..23;
    # the loader tolerates both, but new builds use hour-ending.)
    time_df = _build_time_columns(period, tz)
    for i, col in enumerate(time_df.columns):
        out.insert(i, col, time_df[col])

    fuel_codes = [c[len("NG: ") :] for c in out.columns if c.startswith("NG: ")]
    ng_cols = _ordered_fuel_columns(fuel_codes)
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
    value_cols = [c for c in lead[4:] if c in out.columns] + ng_cols
    # float32 values, matching the committed extracts (convert_eia930).
    out[value_cols] = out[value_cols].astype("float32")
    return out[lead[:4] + value_cols]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ba", required=True, help="EIA-930 BA code, e.g. NYIS")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument(
        "--append-only",
        action="store_true",
        help="keep every existing row of the output byte-identical and append "
        "only rows AFTER its last UTC hour (for extending a hand-curated "
        "extract, e.g. the 54-column Grid Monitor 'ERCO hourly', whose extra "
        "columns the long extracts don't carry — they stay NaN on new rows)",
    )
    args = ap.parse_args()

    frame = build(args.ba)
    out = args.out or OUT_DIR / f"{args.ba} hourly.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.append_only and out.exists():
        existing = pd.read_parquet(out)
        last = existing["UTC time"].max()
        new_rows = frame[frame["UTC time"] > last]
        added = new_rows.reindex(columns=existing.columns).astype(
            existing.dtypes.to_dict()
        )
        frame = pd.concat([existing, added], ignore_index=True)
        print(f"append-only: kept {len(existing):,} rows, added {len(added):,}")
    frame.to_parquet(out, index=False)

    span = f"{frame['Local date'].min().date()}..{frame['Local date'].max().date()}"
    fuels = [c for c in frame.columns if c.startswith("NG: ")]
    print(f"wrote {out} — {len(frame):,} hourly rows ({span})")
    print(f"  fuels: {', '.join(fuels)}")


if __name__ == "__main__":
    main()
