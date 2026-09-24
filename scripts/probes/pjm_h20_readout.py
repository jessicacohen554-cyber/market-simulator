"""pjm-h20 (ZERO LP): per-year readout of a Card C leg vs the keeper control.

G1/G2 of docs/PRECOMMIT-pjm-h20-card-c-cc-level-ct-max-2026-09-24.md §6: load-weighted
price vs actual, the error by actual-price region (bottom 50 % / p50-p95 / top 5 %),
the error in the CONTROL's CC-marginal hours (pjm-h18 classification, from the phase-0
JSON's bundle), and class P1 TWh for the C1 classes.

Usage: python3 scripts/probes/pjm_h20_readout.py 2020 2023 ...
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CAL = ROOT / "results" / "calibration"
CLASSES = ["CC_REGULAR", "CT_PEAKER", "COAL_BIT", "ST_GAS"]


def _control(year: int) -> Path:
    return CAL / ("pjm_h19_dbs_touchpoint" if year <= 2022 else "pjm_h19_dbs_span")


def _lw(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray]:
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[(s["pass"] == "P1") & (s.zone != "PJM_external")]
    g = s.assign(pdm=s.price * s.demand).groupby("hour")[["pdm", "demand"]].sum()
    return (g.pdm / g.demand).to_numpy(), g.demand.to_numpy()


def _classes(bundle: Path, year: int) -> dict:
    c = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"].groupby("klass").mw.sum() / 1e6
    return {k: round(float(c.get(k, 0.0)), 2) for k in CLASSES}


def main() -> None:
    """Print the readout per requested year."""
    act = pd.read_parquet(ROOT / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet")
    for y in map(int, sys.argv[1:]):
        pa, w = _lw(CAL / f"pjm_h20_cardc_{y}", y)
        pc, _ = _lw(_control(y), y)
        a = act[act.year == y].sort_values("hour").rt.to_numpy(float)[: len(w)]
        W = w.sum()
        print(f"== {y}  LW ctl {(pc * w).sum() / W:.2f}  arm {(pa * w).sum() / W:.2f}  actual {(a * w).sum() / W:.2f}")
        lo, top = a <= np.median(a), a >= np.quantile(a, 0.95)
        for nm, m in (("bottom50", lo), ("p50_p95", ~lo & ~top), ("top5", top)):
            ec = (((pc - a) * w)[m]).sum() / W
            ea = (((pa - a) * w)[m]).sum() / W
            print(f"   {nm:9s} err ctl {ec:+.2f}  arm {ea:+.2f}")
        print(f"   TWh ctl {_classes(_control(y), y)}\n   TWh arm {_classes(CAL / f'pjm_h20_cardc_{y}', y)}")


if __name__ == "__main__":
    main()
