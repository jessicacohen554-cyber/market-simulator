"""Diagnostic: where does the 2025 co-opt LMP overshoot live?

Usage: uv run python scripts/probes/_ercot_2025_adder_diag.py <bundle>

Uses the model demand-weighted system price (co-opt LMP, already scarcity-
inclusive) vs actual ERCOT RTSPP. Answers the handoff's first-hour questions:
  1. Is the +$11 annual-mean overshoot broad or concentrated in the tail?
     -> decompose the demand-weighted mean gap by model price band.
  2. In the hours the model prices >$200/>$500, what did actual RTSPP do?
  3. Month / hour-of-day distribution of the per-hour overshoot.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
ACTUAL = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "_validation-source"
    / "actual_lmp_hourly_ERCOT.parquet"
)

_MONTH_HOURS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_CUM = np.cumsum([0] + [h * 24 for h in _MONTH_HOURS])
_MONTHS = [
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


def model_price(bundle: str, year: int) -> tuple[np.ndarray, np.ndarray]:
    """Demand-weighted hourly model price and total demand for a year (P1)."""
    sy = pd.read_parquet(ROOT / bundle / "system.parquet")
    if "pass" in sy.columns and (sy["pass"] == "P1").any():
        sy = sy[sy["pass"] == "P1"]
    g = sy[sy["year"] == year].copy()
    num = (g["price"] * g["demand"]).groupby(g["hour"]).sum()
    den = g["demand"].groupby(g["hour"]).sum()
    p = (num / den.replace(0, np.nan)).sort_index()
    return p.to_numpy(float), den.sort_index().to_numpy(float)


def main() -> None:
    bundle = sys.argv[1]
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2025
    mp, dem = model_price(bundle, year)
    adf = pd.read_parquet(ACTUAL)
    act = adf[adf["year"] == year].sort_values("hour")["rt"].to_numpy(float)
    n = min(len(mp), len(act), len(dem))
    mp, act, dem = mp[:n], act[:n], dem[:n]
    w = dem / dem.sum()

    mean_m = float((mp * w).sum())
    mean_a = float((act * w).sum())
    print(f"=== {bundle}  year {year} ===")
    print(
        f"demand-weighted mean: model {mean_m:.2f}  actual {mean_a:.2f}  "
        f"gap {mean_m - mean_a:+.2f}"
    )
    print(
        f"tail hours  model >200 {int((mp > 200).sum())}  >500 {int((mp > 500).sum())}"
        f"   |  actual >200 {int((act > 200).sum())}  >500 {int((act > 500).sum())}"
    )
    print()

    # (1) decompose the demand-weighted mean gap by MODEL price band.
    print(
        "--- mean-gap decomposition by MODEL price band "
        "(contribution to demand-weighted mean, $/MWh) ---"
    )
    bands = [(-1e9, 50), (50, 100), (100, 200), (200, 500), (500, 1e9)]
    labels = ["<50", "50-100", "100-200", "200-500", ">500"]
    tot = 0.0
    for (lo, hi), lab in zip(bands, labels):
        sel = (mp >= lo) & (mp < hi)
        contr_m = float((mp[sel] * w[sel]).sum())
        contr_a = float((act[sel] * w[sel]).sum())
        nh = int(sel.sum())
        gap = contr_m - contr_a
        tot += gap
        am = act[sel].mean() if nh else 0.0
        print(
            f"  model {lab:>8}: {nh:5d} h  model {contr_m:6.2f}  "
            f"actual {contr_a:6.2f}  gap {gap:+6.2f}   (actual mean in band {am:7.1f})"
        )
    print(f"  {'sum gap':>14}: {tot:+.2f}")
    print()

    # (2) what did actual do in the model's scarcity hours?
    for thr in (200, 500):
        sel = mp > thr
        nh = int(sel.sum())
        if nh:
            print(f"--- {nh} hours model > ${thr}: actual RTSPP in those hours ---")
            a = act[sel]
            print(
                f"    actual mean {a.mean():.1f}  median {np.median(a):.1f}  "
                f"min {a.min():.1f}  max {a.max():.1f}  "
                f"| actual>{thr}: {int((a > thr).sum())}  actual<50: {int((a < 50).sum())}"
            )
    print()

    # (3) month x overshoot
    h = np.arange(n)
    midx = np.clip(np.searchsorted(_CUM, h, side="right") - 1, 0, 11)
    print("--- per-month: model vs actual demand-wtd mean, and tail hours ---")
    for m in range(12):
        s = midx == m
        if not s.any():
            continue
        ww = dem[s] / dem[s].sum()
        mm = (mp[s] * ww).sum()
        aa = (act[s] * ww).sum()
        print(
            f"  {_MONTHS[m]}: model {mm:6.1f}  actual {aa:6.1f}  gap {mm - aa:+6.1f}"
            f"   model>200 {int((mp[s] > 200).sum()):3d} >500 {int((mp[s] > 500).sum()):3d}"
            f" | act>200 {int((act[s] > 200).sum()):3d} >500 {int((act[s] > 500).sum()):3d}"
        )


if __name__ == "__main__":
    main()
