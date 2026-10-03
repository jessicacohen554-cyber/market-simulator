"""Close-out CAISO-2, step 2 (ZERO LP): C3c model tail count on the RT-covered window.

For every (ISO, year) whose committed RT tail reference (``tail/actual_tail.json``)
covers < 100 % of the hours, count the keeper's model tail hours (max-over-zones
P1 dual > the ISO threshold, ``render_calibration_html._tail_hours``) on all
8,760 hours and on the RT-covered hours only (the like-for-like mask C3a's
month-coverage gate and ``_monthly_mae`` already apply), beside the actual RT
count. Reads the keeper bundles' committed ``hourly/system_<y>.parquet`` and
``data/raw/_validation-source/actual_lmp_hourly_<ISO>.parquet``.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_2_c3c_window.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TAIL = json.loads((ROOT / "frontend/data/backcast/tail/actual_tail.json").read_text())
KEEPER_BUNDLE = {
    "CAISO": "closeout_caiso_w1_a2_span",
    "MISO": "w0_miso_span",
    "SPP": "w0_sppr_span",
}


def main() -> None:
    """Print the windowed census for every partially-covered scored ISO-year."""
    for iso, years in TAIL["isos"].items():
        thr = TAIL["thresholds"][iso]
        for y, r in years.items():
            if r["rt_coverage"] >= 1.0 or int(y) >= 2026 or iso not in KEEPER_BUNDLE:
                continue
            sysf = (
                ROOT
                / "results/calibration"
                / KEEPER_BUNDLE[iso]
                / f"hourly/system_{y}.parquet"
            )
            if not sysf.exists():
                print(iso, y, "no keeper system sidecar")
                continue
            s = pd.read_parquet(sysf, columns=["zone", "hour", "price"])
            pmax = s.groupby("hour").price.max().reindex(range(8760)).to_numpy()
            a = pd.read_parquet(
                ROOT / f"data/raw/_validation-source/actual_lmp_hourly_{iso}.parquet"
            )
            a = a[a.year == int(y)].set_index("hour").rt.reindex(range(8760)).to_numpy()
            cov = ~np.isnan(a)
            m = pmax > thr
            print(
                json.dumps(
                    {
                        "iso": iso,
                        "year": int(y),
                        "threshold": thr,
                        "rt_coverage": round(float(cov.mean()), 3),
                        "model_all_hours": int(m.sum()),
                        "model_on_rt_hours": int((m & cov).sum()),
                        "model_off_rt_hours": int((m & ~cov).sum()),
                        "actual_rt": int((np.nan_to_num(a, nan=-np.inf) > thr).sum()),
                        "first_rt_hour": int(np.argmax(cov)),
                    }
                )
            )


if __name__ == "__main__":
    main()
