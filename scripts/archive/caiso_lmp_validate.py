"""Held-out hourly-LMP validation for the CAISO body-overprice campaign.

Task-spec convention (distinct from analyze_lmp_residual.py, which uses the
P1 pass and the RT actual): the model hourly price is the load-weighted
``price`` across zones from ``system.parquet`` filtered to ``pass=='P2'``,
grouped by hour; the actual is the ``da`` column of
``data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet`` for the
8760-hr overlap of the requested year.

Reports headline (mean / p50 / p95), the residual (model-actual) decomposed
by hour-of-day and by month, and the negative-tail guardrail (neg and <=$5
precision/recall). The residual decomposition is the point: it localizes
WHERE the body overprice lives.

Usage:
    python scripts/archive/caiso_lmp_validate.py BUNDLE_DIR [--year 2024]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
VAL = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_CAISO.parquet"

_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START = tuple(int(sum(_DAYS_IN_MONTH[:m]) * 24) for m in range(13))
_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def _month_of_hour(h: np.ndarray) -> np.ndarray:
    return np.searchsorted(_MONTH_START, h, side="right").clip(1, 12)


def model_price(bundle: Path, year: int) -> pd.DataFrame:
    """Load-weighted P2 system price by hour for ``year``."""
    sy = pd.read_parquet(bundle / "system.parquet")
    sy = sy[(sy["pass"] == "P2") & (sy["year"] == year)]
    if sy.empty:
        raise SystemExit(f"no P2 rows for {year} in {bundle}")
    sy = sy.assign(pd_=sy["price"] * sy["demand"])
    g = sy.groupby("hour", observed=True).agg(
        pd_=("pd_", "sum"), d=("demand", "sum"), p=("price", "mean")
    )
    price = np.where(g["d"] > 0, g["pd_"] / g["d"], g["p"])
    return g.assign(price=price).reset_index()[["hour", "price"]]


def _guardrail(model: np.ndarray, actual: np.ndarray, thr: float, name: str) -> str:
    mp = model <= thr
    ap = actual <= thr
    tp = int((mp & ap).sum())
    prec = tp / mp.sum() if mp.sum() else float("nan")
    rec = tp / ap.sum() if ap.sum() else float("nan")
    return (
        f"  {name:<8} model {int(mp.sum()):4d}  actual {int(ap.sum()):4d}  "
        f"precision {prec:5.1%}  recall {rec:5.1%}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()

    m = model_price(args.bundle, args.year)
    av = pd.read_parquet(VAL)
    av = av[av["year"] == args.year].sort_values("hour")

    model = np.full(8760, np.nan)
    model[m["hour"].to_numpy()] = m["price"].to_numpy(float)
    actual = np.full(8760, np.nan)
    actual[av["hour"].to_numpy()] = av["da"].to_numpy(float)
    hours = np.arange(8760)
    ok = np.isfinite(model) & np.isfinite(actual)
    model, actual, hours = model[ok], actual[ok], hours[ok]
    resid = model - actual

    print(f"\n=== CAISO {args.year}  {args.bundle.name}  (n={len(model)}) ===")
    print(
        f"  model   mean {model.mean():6.2f}  p50 {np.percentile(model, 50):6.2f}"
        f"  p95 {np.percentile(model, 95):6.2f}"
    )
    print(
        f"  actual  mean {actual.mean():6.2f}  p50 {np.percentile(actual, 50):6.2f}"
        f"  p95 {np.percentile(actual, 95):6.2f}"
    )
    print(
        f"  residual mean {resid.mean():+6.2f}  p50 "
        f"{np.percentile(model, 50) - np.percentile(actual, 50):+6.2f}  p95 "
        f"{np.percentile(model, 95) - np.percentile(actual, 95):+6.2f}"
    )

    print("\n  negative-tail guardrail:")
    print(_guardrail(model, actual, -0.0001, "neg<0"))
    print(_guardrail(model, actual, 5.0, "<=$5"))

    print("\n  residual by hour-of-day:")
    hod = hours % 24
    for h in range(24):
        s = hod == h
        print(
            f"    h{h:02d}  model {model[s].mean():6.2f}  actual "
            f"{actual[s].mean():6.2f}  resid {resid[s].mean():+6.2f}"
        )

    print("\n  residual by month:")
    mon = _month_of_hour(hours)
    for mm in range(1, 13):
        s = mon == mm
        if not s.any():
            continue
        print(
            f"    {_MONTHS[mm - 1]}  model {model[s].mean():6.2f}  actual "
            f"{actual[s].mean():6.2f}  resid {resid[s].mean():+6.2f}  "
            f"(n={int(s.sum())})"
        )


if __name__ == "__main__":
    main()
