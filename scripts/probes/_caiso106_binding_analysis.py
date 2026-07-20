"""CAISO-106 binding check: model evening/belly TOTAL net import vs the measured ceiling.

Reads the single-year (2024) keeper-recipe repro bundle (`caiso106_binding_2024`)
and compares the MODEL's total net import into CA (from `flows.parquet`, via the
`_caiso102_evening_merit.model_hourly` construction) against the MEASURED
net-load-conditioned exhaustion envelope (`_caiso106_intertie_elasticity`), per
window and per fixed net-load band. Answers the ask's go/no-go: does the model
over-import past the measured ceiling (so the M-EVE-EXH-1 ceiling would bind)?

Usage: .venv/bin/python scripts/probes/_caiso106_binding_analysis.py [bundle_dir]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _caiso102_evening_merit import model_hourly  # noqa: E402
from _caiso106_intertie_elasticity import (  # noqa: E402
    BELLY,
    EVENING,
    NL_BANDS_GW,
    _load,
)

YEAR = 2024
HOURS = 8760


def main() -> int:
    bundle = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else REPO / "results" / "calibration" / "caiso106_binding_2024"
    )
    if not bundle.exists():
        print(f"bundle not found: {bundle}")
        return 2

    meas = _load(YEAR)
    m = model_hourly(bundle, YEAR)
    model_imp = m["imports"]  # net imports into CA zones (MW), model clock
    meas_tot = meas["total"]  # measured EIA-930 corridor net import (MW)
    nl = meas["netload"]
    hod = np.arange(HOURS) % 24

    for wlabel, hods in (("EVENING", EVENING), ("BELLY", BELLY)):
        win = np.isin(hod, hods)
        okm = win & np.isfinite(model_imp)
        okmeas = win & np.isfinite(meas_tot)
        print(f"\n===== {wlabel} (hod {hods[0]}-{hods[-1]}) {YEAR} =====")
        print(
            f"  window mean: MODEL net import {model_imp[okm].mean():+6.0f} MW  vs  "
            f"MEASURED {meas_tot[okmeas].mean():+6.0f} MW  "
            f"(model p50 {np.percentile(model_imp[okm], 50):+.0f} / "
            f"p95 {np.percentile(model_imp[okm], 95):+.0f})"
        )
        print(
            "  by fixed net-load band:   MODEL mean | MEASURED p50 / p95 | binds vs p95?"
        )
        for lo, hi in NL_BANDS_GW:
            band = win & np.isfinite(nl) & (nl >= lo * 1e3) & (nl < hi * 1e3)
            bm = band & np.isfinite(model_imp)
            bmeas = band & np.isfinite(meas_tot)
            if bm.sum() < 20:
                continue
            mp = float(model_imp[bm].mean())
            p50 = (
                float(np.percentile(meas_tot[bmeas], 50))
                if bmeas.sum() >= 20
                else float("nan")
            )
            p95 = (
                float(np.percentile(meas_tot[bmeas], 95))
                if bmeas.sum() >= 20
                else float("nan")
            )
            binds = "BINDS" if (np.isfinite(p95) and mp > p95) else "slack"
            print(
                f"    [{lo:5.0f},{hi:4.0f})  n={int(bm.sum()):4d}  "
                f"MODEL {mp:+6.0f} | meas {p50:+6.0f} / {p95:+6.0f}  {binds}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
