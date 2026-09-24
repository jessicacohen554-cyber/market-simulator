"""pjm-h19 (ZERO LP): G0 drift and G1 liveness readout, arm legs vs the keeper hourlies.

G0: class TWh and load-weighted mean price per year, arm vs control.
G1: served demand, slack and price at the repaired hours (2020 h5003/5031/5383, 2024 h7787).
Gates declared in docs/PRECOMMIT-pjm-h19-demand-balance-screen-2026-09-23.md §6.

Usage: python3 scripts/probes/pjm_h19_readout.py 2020 2023 ...
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CAL = ROOT / "results" / "calibration"
TARGETS = {2020: [5002, 5003, 5004, 5030, 5031, 5032, 5383], 2024: [7786, 7787, 7788]}


def _control(year: int) -> Path:
    return CAL / ("hydro2_pjm_ror_touchpoint" if year <= 2022 else "hydro2_pjm_ror_span")


def _sys(bundle: Path, year: int) -> pd.DataFrame:
    d = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return d[d["pass"] == "P1"]


def _summary(d: pd.DataFrame) -> tuple[pd.DataFrame, float, float]:
    by_h = d.groupby("hour").agg(demand=("demand", "sum"), slack=("slack", "sum"))
    w = d.assign(pw=d.price * d.demand).groupby("hour").pw.sum() / by_h.demand
    by_h["price"] = w
    lw = float((d.price * d.demand).sum() / d.demand.sum())
    return by_h, lw, float(d.slack.sum())


def main() -> None:
    """Print G0 and G1 per requested year."""
    for year in map(int, sys.argv[1:]):
        arm_h, arm_p, arm_s = _summary(_sys(CAL / f"pjm_h19_dbs_{year}", year))
        ctl_h, ctl_p, ctl_s = _summary(_sys(_control(year), year))
        ca = pd.read_parquet(CAL / f"pjm_h19_dbs_{year}" / "hourly" / f"class_hourly_{year}.parquet")
        cc = pd.read_parquet(_control(year) / "hourly" / f"class_hourly_{year}.parquet")
        print(f"== {year}  LW price ctl {ctl_p:.4f} arm {arm_p:.4f} d {arm_p - ctl_p:+.4f} | "
              f"slack MWh ctl {ctl_s:,.0f} arm {arm_s:,.0f} | demand TWh d {(arm_h.demand.sum() - ctl_h.demand.sum()) / 1e6:+.5f}")
        ta = ca[ca["pass"] == "P1"].groupby("klass").mw.sum()
        tc = cc[cc["pass"] == "P1"].groupby("klass").mw.sum()
        diff = ((ta.sub(tc, fill_value=0.0)) / 1e6).round(4)
        print("   class TWh d (arm-ctl), |d|>=1e-4:", {k: v for k, v in diff.items() if abs(v) >= 1e-4} or "none")
        for h in TARGETS.get(year, []):
            print(f"   h{h}: demand {ctl_h.demand[h]:,.0f} -> {arm_h.demand[h]:,.0f}  slack {ctl_h.slack[h]:,.0f} -> {arm_h.slack[h]:,.0f}  "
                  f"price {ctl_h.price[h]:.2f} -> {arm_h.price[h]:.2f}")


if __name__ == "__main__":
    main()
