#!/usr/bin/env python3
"""C3c 2022 as PRECISION and RECALL, never a bare count (nyiso-228 §4b).

The reporting rule this implements, inherited and binding: the nyiso-228 control's
2022 tail is 8 hours above $300 that ALL fall on 31 May, against the market's 101
hours in Jan / Feb / Dec / Aug -- **zero overlap, 0 % precision, 0 % recall**. So a
count moving 8 -> 20 need not contain one real scarcity hour, and a count moving
8 -> 0 is not a regression. Every C3c number this lane quotes carries precision and
recall against the market's own hours.

Usage::

    python3 scripts/probes/nyiso229_c3c_precision_recall.py \\
        --bundle results/calibration/nyiso229_arm_y2022 [--threshold 300]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ACTUAL = Path("data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet")


def actual_tail(year: int, threshold: float, leg: str = "rt") -> np.ndarray:
    """Hour indices where the MEASURED price exceeds ``threshold``."""
    a = pd.read_parquet(ACTUAL)
    a = a[a.year == year].sort_values("hour")
    return a.loc[a[leg] > threshold, "hour"].to_numpy()


def model_tail(bundle: Path, year: int, threshold: float) -> np.ndarray:
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    if "pass" in s.columns:
        s = s[s["pass"] == "P1"]
    lw = s.groupby("hour").apply(
        lambda d: float(np.average(d.price, weights=d.demand.clip(lower=1e-9))),
        include_groups=False,
    )
    return lw.index[lw > threshold].to_numpy()


def score(bundle: Path, year: int, threshold: float) -> dict:
    m, a = model_tail(bundle, year, threshold), actual_tail(year, threshold)
    hit = np.intersect1d(m, a)
    prec = float(len(hit) / len(m)) if len(m) else float("nan")
    rec = float(len(hit) / len(a)) if len(a) else float("nan")
    months = pd.to_datetime(f"{year}-01-01") + pd.to_timedelta(a, unit="h")
    mmonths = pd.to_datetime(f"{year}-01-01") + pd.to_timedelta(m, unit="h")
    return {
        "year": year,
        "threshold": threshold,
        "model_hours": int(len(m)),
        "actual_hours": int(len(a)),
        "overlap_hours": int(len(hit)),
        "precision": prec,
        "recall": rec,
        "actual_by_month": {
            int(k): int(v) for k, v in pd.Series(months.month).value_counts().sort_index().items()
        },
        "model_by_month": {
            int(k): int(v) for k, v in pd.Series(mmonths.month).value_counts().sort_index().items()
        },
        "model_by_day": {
            str(k): int(v)
            for k, v in pd.Series(mmonths.date).value_counts().sort_index().items()
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True, type=Path)
    ap.add_argument("--year", type=int, default=2022)
    ap.add_argument("--threshold", type=float, nargs="+", default=[150.0, 200.0, 300.0])
    args = ap.parse_args()
    out = [score(args.bundle, args.year, t) for t in args.threshold]
    print(json.dumps(out, indent=2))
    print("\nA COUNT IS NOT A RESULT. At 0 % precision a rising count contains no")
    print("real scarcity hour, and a falling count is not a regression (nyiso-228 §4b).")


if __name__ == "__main__":
    main()
