#!/usr/bin/env python3
"""hydro-2 (ZERO LP): arm-vs-control hydro shape statistics per year, PJM.

Reads ``hourly/class_hourly_<y>.parquet`` from each arm leg and from the
committed keeper bundle that is its control (rule 29(b) form 4), and prints
the PRECOMMIT-hydro-2 §6 gate statistics: annual hydro TWh (G2), hours below
1 MW, p05/p50/p95, the share of each month's hydro energy in that month's
top-decile system-load hours (flat fleet = 0.10), and the arm/control ratio of
the within-month SD of daily hydro energy.

Usage: python3 scripts/probes/hydro2_pjm_readout.py 2024 [2025 ...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CAL = ROOT / "results" / "calibration"


def control_for(year: int) -> Path:
    """Committed keeper bundle carrying ``year`` (the form-4 control)."""
    name = "pjm_h16_coalgrain_touchpoint" if year <= 2022 else "pjm_h16_coalgrain_span"
    return CAL / name


def hydro_and_load(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray]:
    """P1 hourly hydro MW and system load MW for one year of one bundle."""
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"].astype(str) == "P1"]
    hy = ch[ch.klass.astype(str).str.lower() == "hydro"].sort_values("hour").mw.to_numpy()
    sysf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    col = next(c for c in ("demand", "load", "demand_mw", "load_mw") if c in sysf.columns)
    load = sysf.groupby("hour")[col].sum().sort_index().to_numpy()
    return hy, load


def stats(hy: np.ndarray, load: np.ndarray, year: int) -> dict:
    """Gate statistics for one hourly hydro series."""
    idx = pd.date_range(f"{year}-01-01", periods=len(hy), freq="h")
    df = pd.DataFrame({"hy": hy, "load": load[: len(hy)]}, index=idx)
    top = []
    for _, g in df.groupby(df.index.month):
        thr = g.load.quantile(0.9)
        top.append(g.hy[g.load >= thr].sum() / max(g.hy.sum(), 1e-9))
    daily = df.hy.resample("D").sum()
    sd = daily.groupby(daily.index.month).std().mean()
    return {
        "twh": float(hy.sum()) / 1e6,
        "hrs_lt1": int((hy < 1.0).sum()),
        "p05": float(np.percentile(hy, 5)),
        "p50": float(np.percentile(hy, 50)),
        "p95": float(np.percentile(hy, 95)),
        "topdec": float(np.mean(top)),
        "daily_sd": float(sd),
    }


def main() -> None:
    """Print one arm-vs-control row block per requested year."""
    out = {}
    for y in [int(a) for a in sys.argv[1:]]:
        arm = stats(*hydro_and_load(CAL / f"hydro2_pjm_ror_{y}", y), y)
        ctl = stats(*hydro_and_load(control_for(y), y), y)
        out[y] = {"control": ctl, "arm": arm,
                  "g2_pct": 100 * (arm["twh"] - ctl["twh"]) / ctl["twh"],
                  "sd_ratio": arm["daily_sd"] / ctl["daily_sd"]}
        print(f"\n{y}  {'stat':10s} {'control':>10s} {'arm':>10s}")
        for k in ("twh", "hrs_lt1", "p05", "p50", "p95", "topdec"):
            print(f"      {k:10s} {ctl[k]:10.4f} {arm[k]:10.4f}")
        print(f"      G2 {out[y]['g2_pct']:+.4f} %   daily-SD ratio {out[y]['sd_ratio']:.4f}")
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
