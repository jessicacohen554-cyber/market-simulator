"""Session helper: compare the measured-DAM-offer run to the baseline.

Usage: python scripts/_dam_offer_compare.py <dam_bundle> <baseline_bundle>

Prints the three gate metrics for the offer-curve swap:
  1. Monthly LMP MAE per year ($/MWh) -- model demand-weighted system price vs
     the actual ERCOT RTSPP (data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet),
     for both bundles. The energy+reserve co-opt price already carries the
     reserve lift, so the model 'price' is the RTSPP analogue.
  2. High-price tail: hours > $200 and > $500 per year (model demand-weighted
     system price), both bundles + the actual RTSPP, to confirm the offers don't
     blow up (or collapse) the ~224/140 co-opt tail.
  3. Per-class generation TWh per year (delegated to _session_score's grid-
     delivered class table), DAM vs baseline vs EIA-923 bench.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / "results" / "calibration"
ACTUAL = (Path(__file__).resolve().parents[1] / "inputs" / "calibration"
          / "actual_lmp_hourly_ERCOT.parquet")

# Month boundaries in hours (non-leap), cumulative, for hour -> month.
_MONTH_HOURS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_CUM = np.cumsum([0] + [h * 24 for h in _MONTH_HOURS])


def system_hourly_price(bundle: str) -> dict[int, np.ndarray]:
    """Demand-weighted system price per hour, per year, P1 pass."""
    sy = pd.read_parquet(ROOT / bundle / "system.parquet")
    if "pass" in sy.columns and (sy["pass"] == "P1").any():
        sy = sy[sy["pass"] == "P1"]
    out: dict[int, np.ndarray] = {}
    for year, yg in sy.groupby("year"):
        g = yg.copy()
        num = (g["price"] * g["demand"]).groupby(g["hour"]).sum()
        den = g["demand"].groupby(g["hour"]).sum()
        p = (num / den.replace(0, np.nan)).sort_index()
        out[int(year)] = p.to_numpy(float)
    return out


def actual_rt() -> dict[int, np.ndarray]:
    df = pd.read_parquet(ACTUAL)
    return {int(y): g.sort_values("hour")["rt"].to_numpy(float)
            for y, g in df.groupby("year")}


def monthly_means(hourly: np.ndarray, weights: np.ndarray | None = None) -> np.ndarray:
    h = np.arange(len(hourly))
    midx = np.clip(np.searchsorted(_CUM, h, side="right") - 1, 0, 11)
    out = np.full(12, np.nan)
    for m in range(12):
        sel = midx == m
        if sel.any():
            v = hourly[sel]
            w = weights[sel] if weights is not None else None
            ok = np.isfinite(v)
            if ok.any():
                out[m] = (np.average(v[ok], weights=(w[ok] if w is not None else None)))
    return out


def main() -> None:
    dam, base = sys.argv[1], sys.argv[2]
    mp = {"DAM": system_hourly_price(dam), "BASE": system_hourly_price(base)}
    act = actual_rt()
    years = sorted(set(mp["DAM"]) & set(act))

    print("=== [1] Monthly LMP MAE vs actual RTSPP ($/MWh; 12-month) ===")
    print(f"{'year':>6} {'BASE_MAE':>9} {'DAM_MAE':>9} {'BASE_avg':>9} "
          f"{'DAM_avg':>9} {'ACT_avg':>9}")
    for y in years:
        a_mon = monthly_means(act[y])
        avgs = {}
        maes = {}
        for tag in ("BASE", "DAM"):
            if y not in mp[tag]:
                maes[tag] = float("nan")
                avgs[tag] = float("nan")
                continue
            m_mon = monthly_means(mp[tag][y])
            n = min(len(m_mon), len(a_mon))
            maes[tag] = float(np.nanmean(np.abs(m_mon[:n] - a_mon[:n])))
            avgs[tag] = float(np.nanmean(m_mon))
        print(f"{y:>6} {maes['BASE']:>9.2f} {maes['DAM']:>9.2f} "
              f"{avgs['BASE']:>9.2f} {avgs['DAM']:>9.2f} {np.nanmean(a_mon):>9.2f}")

    print("\n=== [2] High-price tail: hours > $200 / > $500 ===")
    print(f"{'year':>6} | {'BASE >200':>9} {'>500':>6} | {'DAM >200':>9} "
          f"{'>500':>6} | {'ACT >200':>9} {'>500':>6}")
    for y in years:
        def tail(arr):
            v = arr[np.isfinite(arr)]
            return int((v > 200).sum()), int((v > 500).sum())
        b2, b5 = tail(mp["BASE"][y]) if y in mp["BASE"] else (-1, -1)
        d2, d5 = tail(mp["DAM"][y])
        a2, a5 = tail(act[y])
        print(f"{y:>6} | {b2:>9} {b5:>6} | {d2:>9} {d5:>6} | {a2:>9} {a5:>6}")

    print("\n=== [3] Per-class generation TWh (DAM vs BASE vs EIA-923) ===")
    try:
        from scripts._session_score import class_table
    except Exception:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from scripts._session_score import class_table
    td = class_table(dam).rename(columns={"model": "DAM"})
    tb = class_table(base).rename(columns={"model": "BASE"})
    t = td.merge(tb[["year", "class", "BASE"]], on=["year", "class"])
    t["bench"] = t["bench"].round(2)
    t["DAM"] = t["DAM"].round(2)
    t["BASE"] = t["BASE"].round(2)
    t["DAM-BASE"] = (t["DAM"] - t["BASE"]).round(2)
    t["DAM_%err"] = ((t["DAM"] / t["bench"] - 1) * 100).round(1)
    t["BASE_%err"] = ((t["BASE"] / t["bench"] - 1) * 100).round(1)
    for y in sorted(t["year"].unique()):
        print(f"\n== {y} ==")
        print(t[t["year"] == y][["class", "bench", "BASE", "DAM", "DAM-BASE",
                                 "BASE_%err", "DAM_%err"]].to_string(index=False))


if __name__ == "__main__":
    main()
