"""Evaluate the ERCOT May-2024 greenlight gate for a solved bundle.

For each year: demand-weighted annual model LMP vs actual RTSPP, monthly MAE,
the May month demand-weighted model vs actual, the May 8/24/26 ACUTE days, and
the August month (the held-month check). Uses the FINAL (primary) pass prices —
the co-opt energy LMP already carries the reserve lift.

Usage: python scripts/probes/_eval_may_gate.py <bundle_dir> [year ...]
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/user/market-simulator")
CAL = REPO / "data" / "raw" / "_validation-source"


def _hour_to_md(hours):
    """Return (month, day) arrays for a non-leap 8760 clock."""
    base = pd.date_range("2023-01-01", periods=hours, freq="h")
    return base.month.to_numpy(), base.day.to_numpy()


def _actual_rt(year, hours):
    for cand in [
        CAL / "actual_lmp_hourly_ERCOT.parquet",
        REPO / "data" / "raw" / "calibration" / "actual_lmp_hourly_ERCOT.parquet",
    ]:
        if cand.exists():
            act = pd.read_parquet(cand)
            act = act[act["year"] == year]
            out = np.full(hours, np.nan)
            out[act["hour"].to_numpy()] = act["rt"].to_numpy()
            return out
    raise FileNotFoundError("actual_lmp_hourly_ERCOT.parquet not found")


def _model_and_demand(bundle, year, hours):
    sy = pd.read_parquet(bundle / "system.parquet")
    sy = sy[sy["year"] == year]
    # Final pass: prefer non-P1 rows (P2/primary) if a pass column exists.
    if "pass" in sy.columns:
        passes = set(sy["pass"].unique())
        final = [p for p in passes if str(p).upper() != "P1"]
        if final:
            sy = sy[sy["pass"].isin(final)]
    g = (
        sy.assign(pd_=sy["price"] * sy["demand"])
        .groupby("hour")
        .agg(pd_=("pd_", "sum"), d=("demand", "sum"), p=("price", "mean"))
    )
    lam = np.where(g["d"] > 0, g["pd_"] / g["d"], g["p"])
    model = np.full(hours, np.nan)
    dem = np.full(hours, np.nan)
    model[g.index.to_numpy()] = lam
    dem[g.index.to_numpy()] = g["d"].to_numpy()
    return model, dem


def _dw(x, w, sel):
    s = sel & np.isfinite(x) & np.isfinite(w)
    return float(np.average(x[s], weights=w[s])) if s.any() else np.nan


def _monthly_mae(model, rt, dem, month):
    diffs, wts = [], []
    for m in range(1, 13):
        sel = (month == m) & np.isfinite(rt) & np.isfinite(model)
        if not sel.any():
            continue
        mm = float(np.average(model[sel], weights=dem[sel]))
        diffs.append(abs(mm - float(np.nanmean(rt[sel]))))
        wts.append(float(dem[sel].sum()))
    return float(np.average(diffs, weights=wts)) if diffs else np.nan


def main():
    bundle = Path(sys.argv[1])
    years = [int(y) for y in sys.argv[2:]] or [2023, 2024, 2025]
    hours = 8760
    month, day = _hour_to_md(hours)
    acute = (month == 5) & np.isin(day, [8, 24, 26])
    may = month == 5
    aug = month == 8
    print(f"bundle: {bundle}")
    hdr = f"{'yr':>4} {'model':>7} {'actual':>7} {'MAE':>6} {'Mayμ':>7} {'MayAct':>7} {'acute':>7} {'Augμ':>7} {'AugAct':>7}"
    print(hdr)
    for year in years:
        model, dem = _model_and_demand(bundle, year, hours)
        rt = _actual_rt(year, hours)
        allsel = np.ones(hours, bool)
        row = (
            f"{year:>4} {_dw(model, dem, allsel):>7.2f} {_dw(rt, dem, allsel):>7.2f} "
            f"{_monthly_mae(model, rt, dem, month):>6.2f} "
            f"{_dw(model, dem, may):>7.2f} {_dw(rt, dem, may):>7.2f} "
            f"{_dw(model, dem, acute):>7.2f} "
            f"{_dw(model, dem, aug):>7.2f} {_dw(rt, dem, aug):>7.2f}"
        )
        print(row)


if __name__ == "__main__":
    main()
