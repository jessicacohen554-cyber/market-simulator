"""PJM close-out R-13: reported C3a-style price readout, arm vs W0 keeper (zero LP).

The arm span cannot be registered (2021 unsolved; rule 16), so the rubric's
C3a is not scored. This reports, per solved year, the load-weighted system mean
price of the arm and of the control keeper ``w0_pjm_span`` against the
committed actual RT series (``actual_lmp_hourly_PJM.parquet``), as
(model - actual) / actual. Reported only; no gate reads it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ACT = ROOT / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
OUT = ROOT / "results/phase0/pjm/_pjmco_r13_c3a_readout.json"


def lw_mean(bundle: Path, year: int) -> float:
    """Load-weighted mean P1 price over internal zones."""
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[(s["pass"].astype(str) == "P1") & (s["zone"] != "PJM_external")]
    return float((s["price"] * s["demand"]).sum() / s["demand"].sum())


def main() -> None:
    """Write the per-year readout."""
    act = pd.read_parquet(ACT)
    out = {}
    for y in (2019, 2020, 2022, 2023, 2024, 2025):
        a = float(act.loc[act["year"] == y, "rt"].mean())
        arm = lw_mean(ROOT / f"results/calibration/closeout_pjm_r13_{y}", y)
        ctl = lw_mean(ROOT / "results/calibration/w0_pjm_span", y)
        out[y] = {
            "actual_rt_mean": round(a, 2),
            "keeper": round(ctl, 2),
            "arm": round(arm, 2),
            "keeper_err_pct": round((ctl - a) / a * 100, 1),
            "arm_err_pct": round((arm - a) / a * 100, 1),
        }
        print(y, out[y])
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
