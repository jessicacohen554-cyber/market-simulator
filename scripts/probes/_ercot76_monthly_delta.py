"""Monthly lw-basis price deltas (model - actual) for probe bundles.

The ERCOT-73/76/77 adjudication companion: per bundle-year, the monthly
demand-weighted settled price minus the committed bench ``rt_lw_mon``
(the payload lw basis — same construction as ``_ercot63_c3_proxy``).

Usage::

    uv run python scripts/probes/_ercot76_monthly_delta.py BUNDLE [BUNDLE ...] \
        --year 2024
"""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles", nargs="+")
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()

    bench = json.loads(
        gzip.open(
            REPO / f"frontend/data/backcast/bench/ERCOT/{args.year}.json.gz"
        ).read()
    )["bench"]["avgLMP"]
    act = np.array(
        [v if v is not None else np.nan for v in bench["rt_lw_mon"]], dtype=float
    )
    month_of_hour = pd.date_range(
        f"{args.year}-01-01", periods=8760, freq="h"
    ).month.to_numpy()

    print(f"{'bundle':32s} " + " ".join(f"{m:>6d}" for m in range(1, 13)))
    print(f"{'actual rt_lw_mon':32s} " + " ".join(f"{v:6.1f}" for v in act))
    for name in args.bundles:
        b = REPO / "results" / "calibration" / name
        df = pd.read_parquet(b / "system.parquet")
        df = df[(df["pass"] == "P1") & (df["year"] == args.year)].copy()
        df["month"] = month_of_hour[df["hour"].to_numpy()]
        g = df.groupby("month").apply(
            lambda d: (d["price"] * d["demand"]).sum() / d["demand"].sum(),
            include_groups=False,
        )
        model_mon = g.reindex(range(1, 13)).to_numpy(dtype=float)
        delta = model_mon - act
        print(f"{name:32s} " + " ".join(f"{v:+6.1f}" for v in delta))


if __name__ == "__main__":
    main()
