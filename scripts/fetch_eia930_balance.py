#!/usr/bin/env python3
"""Fetch an EIA-930 six-month BALANCE bulk file and land it as parquet.

Downloads one ``EIA930_BALANCE_<YEAR>_<Jan_Jun|Jul_Dec>.csv`` from the EIA
Hourly Electric Grid Monitor bulk archive
(https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/) and writes
``data/raw/eia-930/EIA930_BALANCE_<YEAR>_<half>.parquet`` in the exact schema
of the committed 2023-2025 siblings (all BAs, 44 columns: string keys/times,
float64 values). Raw is immutable: an existing output is never overwritten
unless ``--force``.

Usage:
    python scripts/fetch_eia930_balance.py --year 2022 --half Jan_Jun
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "data" / "raw" / "eia-930"
URL = "https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/{name}.csv"

_STRING_COLS = (
    "Balancing Authority",
    "Data Date",
    "Local Time at End of Hour",
    "UTC Time at End of Hour",
    "Region",
)
_INT_COLS = ("Hour Number",)


def fetch(year: int, half: str, force: bool) -> Path:
    """Download + convert one six-month BALANCE file; verify vs a sibling."""
    name = f"EIA930_BALANCE_{year}_{half}"
    out = OUT_DIR / f"{name}.parquet"
    if out.exists() and not force:
        print(f"  {out.name} already exists; skipping (--force to rebuild)")
        return out

    url = URL.format(name=name)
    print(f"  GET {url}")
    tmp = out.with_suffix(".csv.part")
    with urllib.request.urlopen(url, timeout=600) as resp, tmp.open("wb") as fh:
        while True:
            block = resp.read(1 << 22)
            if not block:
                break
            fh.write(block)

    # Match the committed siblings byte-for-byte: string keys/times (the CSV's
    # thousands-separated numerics parsed to float64), int64 hour number.
    df = pd.read_csv(tmp, thousands=",", dtype={c: "object" for c in _STRING_COLS})
    tmp.unlink()
    for c in _STRING_COLS:
        df[c] = df[c].astype(str).astype(object)
    for c in _INT_COLS:
        df[c] = pd.to_numeric(df[c]).astype("int64")
    for c in df.columns:
        if c not in _STRING_COLS + _INT_COLS:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    # EIA revamped the 930 fuel taxonomy mid-2024 (hydro/PS split, solar/wind
    # by integrated storage, geothermal, storage categories): the committed
    # archive is mixed — 2023..2024H1 carry the legacy 44 columns, 2024H2+
    # the 65-column taxonomy — and EIA serves each archived half-year in its
    # original format. Verify against a sibling of the SAME taxonomy.
    is_new = any("Excluding Pumped" in c for c in df.columns)
    siblings = [
        p
        for p in sorted(OUT_DIR.glob("EIA930_BALANCE_*.parquet"))
        if p != out
        and any("Excluding Pumped" in n for n in pq.read_schema(p).names) == is_new
    ]
    if not siblings:
        raise FileNotFoundError(
            "no committed BALANCE sibling of the same taxonomy to verify against"
        )
    ref = pq.read_schema(siblings[-1])

    # EIA didn't publish a per-fuel breakdown for every BA until partway
    # through 2018 (confirmed against the raw 2018 Jan_Jun archive: it has
    # only the demand/net-generation/interchange columns, none of the
    # "Net Generation (MW) from <fuel>" columns the 2019+ archive carries).
    # A column absent from the SOURCE (not just renamed) is a real reporting
    # gap, not something to fabricate — reindex it in as NaN rather than
    # erroring, matching the existing GEO/BAT-fold-to-OTH NaN convention in
    # extend_eia930_hourly_from_balance.py.
    missing = [c for c in ref.names if c not in df.columns]
    if missing:
        print(
            f"  NOTE: source lacks {len(missing)} column(s) present in the "
            f"reference taxonomy (real EIA reporting gap, filled NaN): "
            f"{missing}"
        )
    df = df.reindex(columns=ref.names)
    for c in missing:
        df[c] = df[c].astype("float64")
    df.to_parquet(out, index=False)
    got = pq.read_schema(out)
    ref_cols = list(zip(ref.names, (str(t) for t in ref.types)))
    got_cols = list(zip(got.names, (str(t) for t in got.types)))
    if ref_cols != got_cols:
        out.unlink()
        raise AssertionError(
            f"{out.name}: schema mismatch vs {siblings[-1].name}:\n"
            f"  ref: {ref_cols}\n  got: {got_cols}"
        )
    n_ba = df["Balancing Authority"].nunique()
    print(
        f"  OK {out.name}: {len(df):,} rows, {n_ba} BAs, "
        f"{df['Data Date'].min()}..{df['Data Date'].max()}, schema == sibling"
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--half", choices=("Jan_Jun", "Jul_Dec"), required=True)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    fetch(args.year, args.half, args.force)


if __name__ == "__main__":
    sys.exit(main())
