"""NYISO-NEXT-14 phase 0 (ZERO LP): where the keeper's C3a miss sits, and why.

Reads only committed artifacts: the keeper's hourly sidecars
(``results/calibration/nyisonext13_{span,2021}/hourly``), the load-weighted RT bench
(``frontend/data/backcast/bench/NYISO/<y>.json.gz``), the zonal RT table
(``data/raw/_validation-source/actual_lmp.json``), the EIA-923 hydro bench, and the
``nyiso-interface-flows`` clean partition (MIS P-32 postings). Writes
``results/phase0/nyiso/_nyisonext14_phase0.json``.

Blocks:
* ``c3a_by_zone``: model vs measured RT zonal mean, and C3a if Upstate_West alone were exact.
* ``upstate_pin``: hours Upstate_West clears at the pooled NYISO_external price, at <= $1.40,
  and <= $0.
* ``hydro``: model hydro vs the EIA-923 bench (spill proxy).
* ``cutset``: measured TOTAL EAST and CENTRAL EAST flow vs the model's link cap
  (NYISO_INTERFACE_TTC_BY_MONTH), and a least-squares read of the non-CE leg
  (TOTAL EAST - CENTRAL EAST) on the external schedules (is it an external-tie
  sum, coefficient ~1, or an internal path?).
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(REPO / "src")]

from market_sim.config.constants import NYISO_INTERFACE_TTC_BY_MONTH  # noqa: E402
from scripts.lib.clean_io import read_clean  # noqa: E402

CAL = REPO / "results" / "calibration"
BUN = {2021: "nyisonext13_2021"} | {y: "nyisonext13_span" for y in (2022, 2023, 2024, 2025)}
EXT = ("NYISO_external", "NYISO_NE_AC")
LINK = ("Upstate_West", "Capital_Hudson")
DC = ["SCH - PJM_HTP", "SCH - PJM_VFT", "SCH - PJM_NEPTUNE", "SCH - NPX_CSC", "SCH - NPX_1385"]
OUT = CAL.parent / "phase0" / "nyiso" / "_nyisonext14_phase0.json"


def _sys(y: int) -> pd.DataFrame:
    s = pd.read_parquet(CAL / BUN[y] / "hourly" / f"system_{y}.parquet")
    return s[s["pass"] == "P1"]


def year_block(y: int) -> dict:
    """All phase-0 numbers for one year."""
    zt = json.load(open(REPO / "data/raw/_validation-source/actual_lmp.json"))["NYISO"][str(y)]
    bench = json.load(gzip.open(REPO / f"frontend/data/backcast/bench/NYISO/{y}.json.gz"))["bench"]
    s = _sys(y)
    z = s[~s.zone.isin(EXT)]
    lw = float(np.average(z.price, weights=z.demand))
    rt_lw = float(bench["avgLMP"]["rt_lw"])
    zones = {}
    for name, g in z.groupby("zone", observed=True):
        zones[str(name)] = {
            "model": round(float(np.average(g.price, weights=g.demand)), 2),
            "rt": zt["zones"][str(name)]["rt"],
            "twh": round(float(g.demand.sum()) / 1e6, 2),
        }
    uw = z[z.zone == "Upstate_West"]
    share = float(uw.demand.sum() / z.demand.sum())
    cf = lw + share * (zones["Upstate_West"]["rt"] - zones["Upstate_West"]["model"])
    up = uw.set_index("hour").price
    ext = s[s.zone == "NYISO_external"].set_index("hour").price
    ch = s[s.zone == "Capital_Hudson"].set_index("hour").price
    c = pd.read_parquet(CAL / BUN[y] / "hourly" / f"class_hourly_{y}.parquet")
    c = c[c["pass"] == "P1"].groupby("klass", observed=True).mw.sum() / 1e6

    f = read_clean("nyiso-interface-flows", iso="NYISO", year=y)
    f["lh"] = pd.to_datetime(f.interval_start_local).dt.floor("h")
    p = f.groupby(["lh", "interface"]).flow_mw.mean().unstack().dropna()
    non = p["TOTAL EAST"] - p["CENTRAL EAST - VC"]
    cap = np.asarray(NYISO_INTERFACE_TTC_BY_MONTH[y][LINK])[p.index.month - 1]
    X = pd.DataFrame(
        {
            "const": 1.0,
            "NE_AC": p["SCH - NE - NY"],
            "PJ_AC": p["SCH - PJ - NY"],
            "DC_downstate": p[DC].sum(axis=1),
            "HQ": p["SCH - HQ - NY"],
            "OH": p["SCH - OH - NY"],
            "MOSES_SOUTH": p["MOSES SOUTH"],
        }
    )
    b, *_ = np.linalg.lstsq(X.values, non.values, rcond=None)
    r2 = 1 - ((non.values - X.values @ b) ** 2).sum() / ((non - non.mean()) ** 2).sum()
    return {
        "c3a": {
            "rt_lw": rt_lw,
            "model_lw": round(lw, 2),
            "pct": round(100 * (lw / rt_lw - 1), 1),
            "pct_if_upstate_exact": round(100 * (cf / rt_lw - 1), 1),
            "upstate_load_share": round(share, 3),
        },
        "zones": zones,
        "upstate_pin": {
            "h_eq_pooled_node": int((abs(up - ext) < 0.5).sum()),
            "h_le_1p40": int((up <= 1.401).sum()),
            "h_le_0": int((up <= 0).sum()),
            "h_below_capital_minus_5": int((up < ch - 5).sum()),
            "median": round(float(up.median()), 2),
        },
        "hydro": {
            "model_twh": round(float(c["hydro"]), 2),
            "eia923_twh": round(float(bench["classFull"]["hydro"]), 2),
            "import_model_twh": round(float(c["import"]), 2),
        },
        "cutset": {
            "model_link_cap_mean_mw": round(float(cap.mean()), 0),
            "total_east_flow_mean_mw": round(float(p["TOTAL EAST"].mean()), 0),
            "central_east_flow_mean_mw": round(float(p["CENTRAL EAST - VC"].mean()), 0),
            "share_h_total_east_above_model_cap": round(float((p["TOTAL EAST"] > cap).mean()), 3),
            "non_ce_mean_mw": round(float(non.mean()), 0),
            "non_ce_regression_r2": round(float(r2), 2),
            "non_ce_regression_coef": {k: round(float(v), 2) for k, v in zip(X.columns, b)},
        },
    }


def main() -> None:
    """Compute every year and write the JSON record."""
    out = {str(y): year_block(y) for y in range(2021, 2026)}
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    for y, d in out.items():
        print(y, d["c3a"], d["upstate_pin"], d["hydro"], d["cutset"]["share_h_total_east_above_model_cap"])


if __name__ == "__main__":
    main()
