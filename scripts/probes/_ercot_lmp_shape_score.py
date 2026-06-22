"""Score an ERCOT backcast bundle's LMP shape against actual RTSPP.

Reports the forecast-trust metrics (NOT a monthly-shape RMSE to minimize): the
price DURATION CURVE percentiles, scarcity-hour frequency, annual mean, and the
monthly model-vs-actual path. Reads a solved bundle's ``system.parquet`` (per-
zone hourly price + demand) and demand-weights across zones to a single system
hourly price, compared to the measured RTSPP
(``data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`` column ``rt``).

Usage:
    python scripts/probes/_ercot_lmp_shape_score.py <bundle_dir> [<bundle_dir2> ...]

Each bundle is scored independently; pass several to eyeball a comparison
(e.g. the keeper next to a probe). No LP solve, no network.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ACTUAL = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
MONTHS = [
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
]
YEARS = (2023, 2024, 2025)


def system_hourly(sysf: pd.DataFrame, year: int) -> np.ndarray | None:
    """Demand-weighted system hourly price for ``year`` (last pass), or None."""
    sy = sysf[sysf.year == year]
    if sy.empty:
        return None
    sy = sy[sy["pass"] == sorted(sy["pass"].unique())[-1]]
    price = sy.pivot_table(index="hour", columns="zone", values="price").to_numpy()
    dem = sy.pivot_table(index="hour", columns="zone", values="demand").to_numpy()
    return (price * dem).sum(1) / dem.sum(1)


def actual_hourly(year: int) -> np.ndarray:
    a = pd.read_parquet(ACTUAL)
    return a[a.year == year]["rt"].to_numpy(dtype=float)


def month_index(year: int, n: int) -> pd.DatetimeIndex:
    clock = [
        t
        for t in pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
        if not (t.month == 2 and t.day == 29)  # fleet clock is non-leap
    ]
    return pd.DatetimeIndex(clock[:n])


def score_year(model: np.ndarray, actual: np.ndarray, year: int) -> None:
    n = min(len(model), len(actual))
    m, a = model[:n], actual[:n]
    fin = np.isfinite(m) & np.isfinite(a)
    avg_m = m[np.isfinite(m)].mean()
    avg_a = a[np.isfinite(a)].mean()
    mae = np.abs(m[fin] - a[fin]).mean()
    print(
        f"\n=== {year} ===  avg model {avg_m:.1f} / actual {avg_a:.1f}   "
        f"MAE {mae:.1f}   "
        f"h>$200 {int((m > 200).sum())}/{int((a[fin] > 200).sum())}   "
        f"h>$500 {int((m > 500).sum())}/{int((a[fin] > 500).sum())}  (model/actual)"
    )
    pcts = [50, 90, 95, 99, 99.9, 100]
    qm = np.percentile(m[np.isfinite(m)], pcts)
    qa = np.percentile(a[fin], pcts)
    hdr = "".join(f"{('P' + str(p)).replace('P100', 'max'):>9}" for p in pcts)
    print(f"  duration curve {hdr}")
    print("    model       " + "".join(f"{v:>9.1f}" for v in qm))
    print("    actual      " + "".join(f"{v:>9.1f}" for v in qa))
    idx = month_index(year, n)
    mm = pd.Series(m, index=idx).groupby(idx.month).mean()
    am = pd.Series(a, index=idx).groupby(idx.month).mean()
    print("  month " + "".join(f"{mo:>7}" for mo in MONTHS))
    print(
        "  mdl   " + "".join(f"{mm.get(i, float('nan')):>7.1f}" for i in range(1, 13))
    )
    print(
        "  act   " + "".join(f"{am.get(i, float('nan')):>7.1f}" for i in range(1, 13))
    )
    print(
        "  m-a   "
        + "".join(f"{mm.get(i, 0) - am.get(i, 0):>7.1f}" for i in range(1, 13))
    )


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    for bundle in argv:
        path = Path(bundle) / "system.parquet"
        if not path.exists():
            print(f"!! {bundle}: no system.parquet (re-solve the bundle first)")
            continue
        print(f"\n################ {bundle} ################")
        sysf = pd.read_parquet(path)
        for year in YEARS:
            model = system_hourly(sysf, year)
            if model is None:
                continue
            score_year(model, actual_hourly(year), year)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
