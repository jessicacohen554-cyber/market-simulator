#!/usr/bin/env python3
"""Fetch the EIA-930 BA-to-BA hourly net interchange (``TI`` family) for one BA.

Produces the exact long-form schema of the existing extracts in
``data/raw/eia-930-interchange/`` (``CISO interchange hourly.parquet``,
``MISO interchange hourly.parquet``):

* ``diba`` (category) — the directly-interconnected balancing authority.
* ``mw`` (float32) — net interchange, EIA sign convention: positive = the
  fetched BA exports to the DIBA.
* ``local_time`` (datetime64[us], naive) — hour-ending timestamp on the BA's
  local clock (the UTC period converted to the BA timezone), spanning the
  requested local calendar years, e.g. 2023-01-01 01:00 .. 2026-01-01 00:00
  for ``--years 2023 2024 2025``.

The CISO/MISO siblings were manual pulls (their README documented this route
as the regeneration path); this script makes the pull reproducible and adds
new BAs (e.g. ISNE for the NEISO per-seam import-tranche calibration: DIBAs
HQT, NBSO, NYIS). Raw data is immutable: an existing output file is never
overwritten unless ``--force`` is passed.

Usage:
    EIA_API_KEY=... python scripts/data/fetch_eia930_interchange.py --ba ISNE \
        --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Reuse the paging + key resolution + BA-timezone map of the wide-extract
# fetcher (same EIA API v2).
sys.path.insert(0, str(Path(__file__).parent))
from fetch_eia930_hourly import BA_TIMEZONE, _api_key, _fetch

INTERCHANGE_URL = "https://api.eia.gov/v2/electricity/rto/interchange-data/data/"
OUT_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "raw"
    / "eia-930-interchange"
)


def fetch_interchange(ba: str, years: list[int], key: str) -> pd.DataFrame:
    """Return the per-DIBA hourly net interchange for ``ba``'s local ``years``.

    Fetches ``facets[fromba]=ba`` from the EIA v2 ``interchange-data`` route
    (one row per UTC period per DIBA), converts the UTC hour-ending period to
    the BA's local clock, and trims to the hour-ending local span
    ``(Jan 1 00:00 of years[0], Jan 1 00:00 of years[-1]+1]``.
    """
    tz = BA_TIMEZONE.get(ba, "America/New_York")
    lo = pd.Timestamp(f"{years[0]}-01-01 00:00", tz=tz)
    hi = pd.Timestamp(f"{years[-1] + 1}-01-01 00:00", tz=tz)
    params = {
        "frequency": "hourly",
        "data[0]": "value",
        "facets[fromba][]": ba,
        # UTC bounds enveloping the local span (hour-ending periods).
        "start": lo.tz_convert("UTC").strftime("%Y-%m-%dT%H"),
        "end": hi.tz_convert("UTC").strftime("%Y-%m-%dT%H"),
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
    }
    df = pd.DataFrame(_fetch(INTERCHANGE_URL, params, key))
    if df.empty:
        sys.exit(f"no interchange rows returned for {ba}")
    utc = pd.to_datetime(df["period"], utc=True)
    local = utc.dt.tz_convert(tz)
    out = pd.DataFrame(
        {
            "diba": df["toba"].astype("category"),
            "mw": pd.to_numeric(df["value"], errors="coerce").astype("float32"),
            "local_time": local.dt.tz_localize(None).astype("datetime64[us]"),
        }
    )
    keep = (local > lo) & (local <= hi)
    out = out[keep.to_numpy()]
    return out.sort_values(["local_time", "diba"], kind="stable").reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ba", required=True, help="EIA-930 BA code, e.g. ISNE")
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025],
        help="Local calendar years to cover (default 2023 2024 2025).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output parquet (default data/raw/eia-930-interchange/"
        "'<BA> interchange hourly.parquet').",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing output file (raw data is otherwise "
        "immutable — refuse to clobber).",
    )
    args = ap.parse_args()

    out = args.out or OUT_DIR / f"{args.ba} interchange hourly.parquet"
    if out.exists() and not args.force:
        sys.exit(f"{out} exists — pass --force to overwrite (data/raw is immutable).")

    frame = fetch_interchange(args.ba, sorted(args.years), _api_key())
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out, index=False)
    span = f"{frame['local_time'].min()}..{frame['local_time'].max()}"
    dibas = ", ".join(sorted(frame["diba"].cat.categories))
    print(f"wrote {out} — {len(frame):,} rows ({span}; DIBAs: {dibas})")


if __name__ == "__main__":
    main()
