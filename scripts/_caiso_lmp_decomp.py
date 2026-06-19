#!/usr/bin/env python3
"""Decompose the CAISO model-vs-actual LMP error by month, hour-of-day and
marginal resource. Read-only analysis over a finished bundle. Not a keeper tool.

Usage: python scripts/_caiso_lmp_decomp.py results/calibration/<bundle> [--year 2024]
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
ACT = REPO / "data/raw/_validation-source/actual_lmp.json"
ACT_HOURLY = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"


def load_system_price(bundle: Path, year: int, pass_: str = "P2") -> pd.DataFrame:
    sysp = pd.read_parquet(bundle / "system.parquet")
    # filter to year + pass if those columns exist
    for col, val in (("year", year), ("pass", pass_)):
        if col in sysp.columns:
            sub = sysp[sysp[col] == val]
            if len(sub):
                sysp = sub
    return sysp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()
    b, yr = args.bundle, args.year

    sysp = load_system_price(b, yr)
    print("system.parquet cols:", list(sysp.columns))
    pcol = "lmp" if "lmp" in sysp.columns else ("price" if "price" in sysp.columns else None)
    dcol = "demand" if "demand" in sysp.columns else ("target" if "target" in sysp.columns else None)
    print("price col:", pcol, "demand col:", dcol, "rows:", len(sysp))

    # load-weighted system price by hour
    if dcol:
        g = sysp.groupby("hour").apply(
            lambda x: np.average(x[pcol], weights=x[dcol]) if x[dcol].sum() else x[pcol].mean())
        load_by_hour = sysp.groupby("hour")[dcol].sum()
    else:
        g = sysp.groupby("hour")[pcol].mean()
        load_by_hour = None
    model_h = g.sort_index().to_numpy()
    hours = g.sort_index().index.to_numpy()
    assert len(model_h) == 8760, f"got {len(model_h)} hours"

    # actuals
    act = json.load(open(ACT))["CAISO"][str(yr)]
    rt_mon = np.array(act["rt_mon"])
    rt_pct = act["rt_pct"]
    ah = pd.read_parquet(ACT_HOURLY)
    ah = ah[ah["year"] == yr].sort_values("hour")
    act_rt = ah["rt"].to_numpy()

    # month index (model uses local 8760 calendar; approx via hour//730 fallback)
    hours_per_month = [31,29,30,31,30,31,31,30,31,30,31,31]  # 2024 leap; sums 366? adjust
    # build month index over 8760 by day-of-year using non-leap mapping for hours align
    import calendar
    days = [31,29 if calendar.isleap(yr) else 28,31,30,31,30,31,31,30,31,30,31]
    midx = np.repeat(np.arange(12), [d*24 for d in days])[:8760]

    print(f"\n=== Annual (load-weighted system) ===")
    mmean = float(np.average(model_h, weights=load_by_hour.to_numpy()) if load_by_hour is not None else model_h.mean())
    print(f"model mean {mmean:6.2f} | actual rt mean {rt_mon.mean():6.2f} | resid {mmean-rt_mon.mean():+6.2f}")

    print(f"\n=== Monthly mean LMP (model vs actual rt_mon) ===")
    print(f"{'mon':>3} {'model':>7} {'actual':>7} {'resid':>7}")
    for m in range(12):
        mm = model_h[midx == m].mean()
        print(f"{m+1:>3} {mm:7.1f} {rt_mon[m]:7.1f} {mm-rt_mon[m]:+7.1f}")

    print(f"\n=== Hour-of-day mean LMP, by season (model | actual) ===")
    hod = hours % 24
    seasons = {"winter(DJF)":[11,0,1],"spring(MAM)":[2,3,4],"summer(JJA)":[5,6,7],"fall(SON)":[8,9,10]}
    act_hod_all = (act_rt % 1)  # placeholder
    for sname, mons in seasons.items():
        sel = np.isin(midx, mons)
        print(f"\n{sname}: hour  model  actual  resid")
        for h in range(0,24,2):
            hsel = sel & (hod == h)
            mm = model_h[hsel].mean()
            aa = act_rt[hsel].mean()
            print(f"   {h:2d}  {mm:6.1f}  {aa:6.1f}  {mm-aa:+6.1f}")

    print(f"\n=== Duration curve (model vs actual rt) ===")
    print(f"{'pct':>5} {'model':>8} {'actual':>8}")
    for p in [0,1,5,10,25,50,75,90,95,99,100]:
        mv = np.percentile(model_h, p)
        key = {0:'min',100:'max'}.get(p, f'p{p}')
        av = rt_pct.get(key, np.percentile(act_rt, p))
        print(f"{key:>5} {mv:8.1f} {av:8.1f}")

    # negative / low hours
    print(f"\nmodel hours <=0: {(model_h<=0).sum()} | <=5: {(model_h<=5).sum()} | actual rt <=0: {(act_rt<=0).sum()}")


if __name__ == "__main__":
    main()
