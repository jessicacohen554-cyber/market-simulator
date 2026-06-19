"""Before/after on CAISO 2024 monthly + hour-of-day LMP for as_reserve_formula.

System price = mean-across-zones of system.parquet price, grouped by hour
(mirrors run_calibration_full's [3] price-level diagnostic). Confirms the
evening tail lifts toward rt_mon while the midday floor is unchanged.
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

YEAR = 2024
RT_MON = json.load(open("data/raw/_validation-source/actual_lmp.json"))["CAISO"]["2024"][
    "rt_mon"
]


def sys_hourly(run_dir: str) -> np.ndarray:
    df = pd.read_parquet(f"{run_dir}/system.parquet")
    df = df[df["year"] == YEAR]
    # Keep the final pass (P2 if present) so we read the converged prices.
    passes = list(df["pass"].unique())
    final = "P2" if "P2" in passes else sorted(passes)[-1]
    df = df[df["pass"] == final]
    return df.groupby("hour")["price"].mean().sort_index().to_numpy()


def month_index(n: int) -> np.ndarray:
    # Non-leap 8760 clock: map each hour to its calendar month 0..11.
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    idx = np.concatenate([np.full(d * 24, m) for m, d in enumerate(days)])
    return idx[:n]


def hour_of_day(n: int) -> np.ndarray:
    return np.arange(n) % 24


def main(base: str, on: str) -> None:
    pb, po = sys_hourly(base), sys_hourly(on)
    n = min(len(pb), len(po))
    pb, po = pb[:n], po[:n]
    mi, hod = month_index(n), hour_of_day(n)

    print("=== CAISO 2024 monthly mean LMP ($/MWh) ===")
    print(f"{'mon':>3} {'rt_mon':>8} {'base':>8} {'formula':>8} {'d':>7}")
    for m in range(12):
        mask = mi == m
        b, o = pb[mask].mean(), po[mask].mean()
        print(f"{m+1:>3} {RT_MON[m]:8.2f} {b:8.2f} {o:8.2f} {o-b:+7.2f}")
    print(f"{'ann':>3} {np.mean(RT_MON):8.2f} {pb.mean():8.2f} "
          f"{po.mean():8.2f} {po.mean()-pb.mean():+7.2f}")

    def err(p):
        return np.mean([abs(p[mi == m].mean() - RT_MON[m]) for m in range(12)])
    print(f"\nMAE vs rt_mon  base {err(pb):.2f}  formula {err(po):.2f}")
    print(f"max LMP        base {pb.max():.2f}  formula {po.max():.2f}")

    print("\n=== hour-of-day mean LMP ($/MWh): midday floor vs evening tail ===")
    print(f"{'hr':>3} {'base':>8} {'formula':>8} {'d':>7}")
    for h in range(24):
        mask = hod == h
        b, o = pb[mask].mean(), po[mask].mean()
        tag = ""
        if 10 <= h <= 15:
            tag = "  <- midday floor"
        if 17 <= h <= 21:
            tag = "  <- evening tail"
        print(f"{h:>3} {b:8.2f} {o:8.2f} {o-b:+7.2f}{tag}")
    midday = (hod >= 10) & (hod <= 15)
    evening = (hod >= 17) & (hod <= 21)
    print(f"\nmidday  (hr10-15) base {pb[midday].mean():.2f}  "
          f"formula {po[midday].mean():.2f}  d {po[midday].mean()-pb[midday].mean():+.2f}")
    print(f"evening (hr17-21) base {pb[evening].mean():.2f}  "
          f"formula {po[evening].mean():.2f}  d {po[evening].mean()-pb[evening].mean():+.2f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
