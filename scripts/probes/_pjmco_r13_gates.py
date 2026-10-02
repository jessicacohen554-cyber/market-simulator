"""PJM close-out R-13: score the anchor-vintage arm's STOP gates S3/S4a/S4b (zero LP).

Gates fixed in ``docs/records/pjm/PRECOMMIT-pjm-closeout-r13-anchor-vintage-2026-10-02.md``
section 5 (and its post-W0 addendum), read here against the arm's per-year
bundles and the control keeper bundle ``results/calibration/w0_pjm_span``:

* S3  per-year median gas-tranche P1 ``mc`` delta (arm - control) has the
  predicted sign and lies in [0.5x, 2.0x] of the phase-0 prediction (years with
  |prediction| < $0.5: sign only if |delta| >= $0.1, else inert PASS).
* S4a every NON-gas unit's P1 ``mc`` identical arm vs control (max |delta| <= 1e-6).
* S4b (i) nuclear/wind/solar/hydro/biomass/OTHER each move < 1.0 % of energy;
  (ii) coal+ST_GAS+oil energy change opposite in sign to CC+CT in years with
  |shift| >= $1; (iii) >= 80 % of |dCOAL| in coal unit-hours whose control
  ``mc`` lies within |shift| + $2 of the control zonal price; (iv)
  |dCOAL| <= |dGAS| TWh.

Usage::

    python scripts/probes/_pjmco_r13_gates.py --arm-leg 2019=results/calibration/closeout_pjm_r13_2019 ...
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "results" / "calibration" / "w0_pjm_span"
PRED = ROOT / "results" / "phase0" / "pjm" / "_pjmco_r13_anchor_vintage_delta.json"
OUT = ROOT / "results" / "phase0" / "pjm" / "_pjmco_r13_gates.json"
GAS_FUELS = {"gas_cc", "gas_ct", "gas_st"}
NONGAS_FUELS = {"coal", "nuclear", "hydro", "oil"}
INVARIANT_CLASSES = ["nuclear", "wind", "solar", "hydro", "biomass", "OTHER"]
COAL_CLASSES = ["COAL_BIT", "COAL_PRB", "COAL_WC"]
DISPLACED = COAL_CLASSES + ["ST_GAS", "oil"]
GAS_DISPLACING = ["CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP"]
GAS_ALL = GAS_DISPLACING + ["ST_GAS", "ST_CHP"]


def _hourly(bundle: Path, name: str, year: int) -> pd.DataFrame:
    """Read one P1 hourly sidecar of a bundle."""
    df = pd.read_parquet(bundle / "hourly" / f"{name}_{year}.parquet")
    return df[df["pass"].astype(str) == "P1"] if "pass" in df.columns else df


def _class_twh(bundle: Path, year: int) -> pd.Series:
    """Annual TWh by class from ``class_hourly``."""
    d = _hourly(bundle, "class_hourly", year)
    return d.groupby("klass", observed=True)["mw"].sum() / 1e6


def score_year(year: int, arm: Path, shift: float) -> dict:
    """Score S3/S4a/S4b for one year."""
    cols = ["unit_id", "fuel", "zone", "hour", "mw", "mc"]
    a = _hourly(arm, "unit_marginal", year)[cols]
    c = _hourly(CONTROL, "unit_marginal", year)[cols]
    m = c.merge(a, on=["unit_id", "hour"], suffixes=("_c", "_a"), how="inner")
    m["fuel"] = m["fuel_c"].astype(str)
    m["dmc"] = m["mc_a"] - m["mc_c"]
    gas = m[m["fuel"].isin(GAS_FUELS)]
    med = float(gas.groupby("unit_id", observed=True)["dmc"].mean().median())
    if abs(shift) < 0.5:
        s3 = bool(abs(med) < 0.1 or np.sign(med) == np.sign(shift))
    else:
        s3 = bool(np.sign(med) == np.sign(shift) and 0.5 <= med / shift <= 2.0)
    nong = m[m["fuel"].isin(NONGAS_FUELS)]
    s4a_max = float(nong["dmc"].abs().max()) if len(nong) else 0.0

    tc, ta = _class_twh(CONTROL, year), _class_twh(arm, year)
    d = ta.reindex(tc.index.union(ta.index), fill_value=0) - tc.reindex(
        tc.index.union(ta.index), fill_value=0
    )
    inv = {
        k: (float(d.get(k, 0.0) / tc[k] * 100) if tc.get(k, 0) else 0.0)
        for k in INVARIANT_CLASSES
    }
    s4b_i = all(abs(v) < 1.0 for v in inv.values())
    d_disp = float(d.reindex(DISPLACED, fill_value=0).sum())
    d_gas = float(d.reindex(GAS_DISPLACING, fill_value=0).sum())
    s4b_ii = (
        True
        if abs(shift) < 1.0
        else bool(np.sign(d_disp) != np.sign(d_gas) or d_disp == 0)
    )
    coal = m[m["fuel"] == "coal"].copy()
    sysp = _hourly(CONTROL, "system", year)[["zone", "hour", "price"]]
    coal = coal.merge(
        sysp, left_on=["zone_c", "hour"], right_on=["zone", "hour"], how="left"
    )
    coal["dmw"] = (coal["mw_a"] - coal["mw_c"]).abs()
    band = (coal["mc_c"] - coal["price"]).abs() <= abs(shift) + 2.0
    tot = float(coal["dmw"].sum())
    frac = float(coal.loc[band, "dmw"].sum() / tot) if tot > 0 else 1.0
    d_coal = float(d.reindex(COAL_CLASSES, fill_value=0).sum())
    d_gas_all = float(d.reindex(GAS_ALL, fill_value=0).sum())
    return {
        "shift_pred": shift,
        "S3_median_gas_dmc": round(med, 3),
        "S3": s3,
        "S4a_max_nongas_dmc": s4a_max,
        "S4a": s4a_max <= 1e-6,
        "S4b_i_pct": {k: round(v, 3) for k, v in inv.items()},
        "S4b_i": s4b_i,
        "S4b_ii_d_displaced_twh": round(d_disp, 3),
        "S4b_ii_d_gas_cc_ct_twh": round(d_gas, 3),
        "S4b_ii": s4b_ii,
        "S4b_iii_flip_band_frac": round(frac, 3),
        "S4b_iii": frac >= 0.80,
        "S4b_iv_d_coal_twh": round(d_coal, 3),
        "S4b_iv_d_gas_twh": round(d_gas_all, 3),
        "S4b_iv": abs(d_coal) <= abs(d_gas_all),
        "class_delta_twh": {k: round(float(v), 3) for k, v in d.items() if v},
    }


def main() -> None:
    """Score every supplied arm leg and write the gate table."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--arm-leg", action="append", required=True, help="YEAR=PATH")
    args = ap.parse_args()
    pred = json.loads(PRED.read_text())["years"]
    out = {}
    for spec in args.arm_leg:
        y, p = spec.split("=", 1)
        r = score_year(
            int(y), ROOT / p, float(pred[y]["predicted_median_gas_offer_shift_usd_mwh"])
        )
        out[y] = r
        flags = {
            k: v
            for k, v in r.items()
            if k in ("S3", "S4a", "S4b_i", "S4b_ii", "S4b_iii", "S4b_iv")
        }
        print(y, flags)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
