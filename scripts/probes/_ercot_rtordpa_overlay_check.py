"""Track-2 verification for the regime-gated RTORDPA price overlay.

Reads an overlaid bundle's ``system.parquet`` (which carries both the overlaid
``price`` and the raw ``rtordpa_overlay`` audit column), and for each year:

  * reconstructs the BASE price (price - rtordpa_overlay) and reports the
    base→overlay lift on the demand-weighted average and the h>$200 / h>$500
    tail vs actual RTSPP — the gate that 2023's tail lifts toward actual while
    2024/25 stay near-inert;
  * NO-DOUBLE-COUNT check: the model's endogenous co-opt adder (``reserve_price``
    ≈ RTORPA) is compared against the MEASURED ``rtorpa`` and ``rtordpa`` — the
    overlay adds the distinct reliability-deployment series, not a second copy
    of the ORDC online adder the co-opt already prices.

No LP solve, no network.

Usage:
    python scripts/probes/_ercot_rtordpa_overlay_check.py results/calibration/<bundle>
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
ORDC = "data/raw/ercot/ercot_{y}_ordc_reserves_hourly.parquet"
YEARS = (2023, 2024, 2025)


def _sys_year(sysf: pd.DataFrame, year: int, col: str) -> np.ndarray | None:
    sy = sysf[sysf.year == year]
    if sy.empty or col not in sy.columns:
        return None
    sy = sy[sy["pass"] == sorted(sy["pass"].unique())[-1]]
    val = sy.pivot_table(index="hour", columns="zone", values=col).to_numpy()
    dem = sy.pivot_table(index="hour", columns="zone", values="demand").to_numpy()
    return (val * dem).sum(1) / dem.sum(1)


def main(argv: list[str]) -> int:
    bundle = Path(argv[0])
    sysf = pd.read_parquet(bundle / "system.parquet")
    has_overlay = "rtordpa_overlay" in sysf.columns
    actual = pd.read_parquet(ACTUAL)
    print(f"################ {bundle} ################")
    print(f"rtordpa_overlay column present: {has_overlay}\n")
    for y in YEARS:
        over = _sys_year(sysf, y, "price")
        if over is None:
            continue
        ov = _sys_year(sysf, y, "rtordpa_overlay")
        rp = _sys_year(sysf, y, "reserve_price")
        base = over - (ov if ov is not None else 0.0)
        a = actual[actual.year == y]["rt"].to_numpy(dtype=float)
        n = min(len(over), len(a))
        b, o, a = base[:n], over[:n], a[:n]
        fin = np.isfinite(a)
        ordc = pd.read_parquet(REPO / ORDC.format(y=y))
        rtorpa = ordc["rtorpa"].to_numpy()[:n]
        rtordpa = ordc["rtordpa"].to_numpy()[:n]
        print(f"=== {y} ===")
        print(
            f"  avg  base {np.nanmean(b):6.2f} -> overlay {np.nanmean(o):6.2f}"
            f"  (actual {a[fin].mean():6.2f})   overlay adds "
            f"{np.nanmean(o) - np.nanmean(b):+.2f}/h"
        )
        print(
            f"  h>$200  base {int((b > 200).sum()):3d} -> overlay "
            f"{int((o > 200).sum()):3d}  (actual {int((a[fin] > 200).sum())})"
            f"   |  h>$500 base {int((b > 500).sum()):3d} -> "
            f"{int((o > 500).sum()):3d}  (actual {int((a[fin] > 500).sum())})"
        )
        if rp is not None:
            rp = rp[:n]
            print(
                "  no-double-count: model reserve_price (endogenous ORDC adder) "
                f"mean {np.nanmean(rp):.2f} vs measured rtorpa {np.nanmean(rtorpa):.2f}"
                f" | overlaid rtordpa mean {np.nanmean(rtordpa):.3f} "
                f"(distinct series, h>$50 {int((np.nan_to_num(rtordpa) > 50).sum())})"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
