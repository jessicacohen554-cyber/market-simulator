#!/usr/bin/env python3
"""Fetch every counterparty's EIA-930 reported interchange WITH one BA.

The EIA-930 BA-to-BA interchange product carries each leg twice: once as
reported by the BA (``Balancing Authority = X, DIBA = Y``) and once as
reported by its counterparty (``Balancing Authority = Y, DIBA = X``). When a
BA's own submission is stale or absent (SWPP's per-neighbour legs are absent
in its frozen-snapshot hours, ``docs/records/spp/FINDING-spp-south-demand-
flatruns-2026-10-18.md`` §3), the counterparty-reported legs are the measured
replacement (owner ruling R22, UC-DESK r20).

This script streams EIA's keyless six-month bulk CSVs (the
``fetch_eia930_interchange.py --source bulk`` archive family) once and keeps
every row whose ``Directly Interconnected Balancing Authority`` is the target
BA, so a single pass covers all counterparties. Output (long form, one row per
reporting BA per hour):

* ``ba`` (category) — the reporting counterparty.
* ``mw`` (float32) — the counterparty's net interchange with the target BA,
  EIA sign: positive = the COUNTERPARTY exports to the target BA, so the
  target's counterparty-measured net export is ``-Σ mw``.
* ``utc_time`` (datetime64[us], naive UTC) — hour-ending UTC stamp (the bulk
  file's ``UTC Time at End of Hour``). UTC, not local: the counterparties sit
  on different clocks (Central, Mountain, Saskatchewan standard time).

The span is the hour-ending UTC window covering the requested local calendar
years on ``--tz`` (default ``America/Chicago``, SWPP's clock). Raw data is
immutable: an existing output is never overwritten without ``--force``.

Usage:
    python scripts/data/fetch_eia930_counterparty_interchange.py --diba SWPP \
        --years 2019 2020 2021 2022 2023 2024 2025
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.data.fetch_eia930_interchange import BULK_URL, OUT_DIR  # noqa: E402

_COLS = {
    "Balancing Authority": "ba",
    "Directly Interconnected Balancing Authority": "diba",
    "Interchange (MW)": "mw",
    "UTC Time at End of Hour": "utc_time",
}


def _halves(years: list[int]) -> list[tuple[int, str]]:
    """Return the six-month bulk files spanning ``years`` plus the next Jan-Jun.

    The next year's first half carries the local-year's last UTC hours
    (local 2025-12-31 18:00 CST is 2026-01-01 00:00 UTC).
    """
    out = [(y, h) for y in years for h in ("Jan_Jun", "Jul_Dec")]
    out.append((years[-1] + 1, "Jan_Jun"))
    return out


def fetch_counterparty_legs(diba: str, years: list[int], tz: str) -> pd.DataFrame:
    """Return every counterparty-reported leg with ``diba`` over local ``years``."""
    import requests

    lo = (
        pd.Timestamp(f"{years[0]}-01-01 00:00", tz=tz)
        .tz_convert("UTC")
        .tz_localize(None)
    )
    hi = (
        pd.Timestamp(f"{years[-1] + 1}-01-01 00:00", tz=tz)
        .tz_convert("UTC")
        .tz_localize(None)
    )
    frames: list[pd.DataFrame] = []
    for year, half in _halves(years):
        url = BULK_URL.format(year=year, half=half)
        with requests.get(url, stream=True, timeout=300) as resp:
            if resp.status_code != 200:
                print(f"  {year} {half}: HTTP {resp.status_code} — skipped")
                continue
            resp.raw.decode_content = True
            kept = 0
            for chunk in pd.read_csv(
                resp.raw, usecols=list(_COLS), dtype=str, chunksize=500_000
            ):
                chunk = chunk.rename(columns=_COLS)
                sel = chunk[chunk["diba"] == diba]
                if not sel.empty:
                    frames.append(sel.drop(columns=["diba"]))
                    kept += len(sel)
            print(f"  {year} {half}: {kept:,} rows reported against {diba}")
    if not frames:
        sys.exit(f"no counterparty rows returned for {diba}")
    raw = pd.concat(frames, ignore_index=True)
    out = pd.DataFrame(
        {
            "ba": raw["ba"].astype("category"),
            "mw": pd.to_numeric(
                raw["mw"].str.replace(",", "", regex=False), errors="coerce"
            ).astype("float32"),
            "utc_time": pd.to_datetime(
                raw["utc_time"], format="%m/%d/%Y %I:%M:%S %p"
            ).astype("datetime64[us]"),
        }
    )
    out = out[(out["utc_time"] > lo) & (out["utc_time"] <= hi)]
    out = out.drop_duplicates(["utc_time", "ba"], keep="first")
    return out.sort_values(["utc_time", "ba"], kind="stable").reset_index(drop=True)


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--diba", required=True, help="Target EIA-930 BA, e.g. SWPP")
    ap.add_argument("--years", nargs="+", type=int, required=True)
    ap.add_argument("--tz", default="America/Chicago", help="Target BA's clock")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    out = args.out or OUT_DIR / f"{args.diba} counterparty interchange hourly.parquet"
    if out.exists() and not args.force:
        sys.exit(f"{out} exists — pass --force to overwrite (data/raw is immutable)")
    frame = fetch_counterparty_legs(args.diba, sorted(args.years), args.tz)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out, index=False)
    print(f"wrote {out} ({len(frame):,} rows, {frame['ba'].nunique()} counterparties)")


if __name__ == "__main__":
    main()
