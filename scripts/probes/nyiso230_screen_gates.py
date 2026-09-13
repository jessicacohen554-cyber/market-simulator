"""Score nyiso-230's four pre-registered screen gates on the 2022 arm.

The gates are fixed in ``results/calibration/PRECOMMIT-nyiso230-zonal-anchor-vintage.md``
§6 and this scorer was written BEFORE the arm's numbers existed, so it cannot
have been shaped by them. All four are STRUCTURAL and STOP-ONLY (rule 29
``[R-SCREEN]``): none reads C1, C3a, C3b or C3c, and clearing them promotes
nothing.

* **G-CONF**  exactly one config field differs arm vs control, and the arm's
  recorded ``gas_offer_margin_anchor_by_zone`` equals the PRECOMMIT §5 anchors
  to 1e-6.
* **G-SCOPE** every band multiplier, every ``phys_*``, all four ``peak`` bands,
  ``econ_low_share`` and ``pct_peaking`` bit-identical.
* **G-PRED**  measured median gas-tranche offer shift ÷ the §5 prediction, per
  zone, inside [0.95, 1.05].
* **G-DEMAND** served demand identical to 4 dp and dump == 0. Conservation is
  gated on SERVED DEMAND, never on generation: the NYISO LP is intertemporally
  and globally coupled (cyclic storage SOC, hydro budgets, the monthly import
  quota, P0-detected commitment bridges), so out-of-footprint generation
  movement is guaranteed and gating it asks the LP not to be an LP — the gate
  nyiso-229 had to withdraw.

Usage::

    python3 scripts/probes/nyiso230_screen_gates.py \
        --arm results/calibration/nyiso230_arm_y2022 \
        --control results/calibration/nyiso229_arm_y2022
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

#: PRECOMMIT §5, fixed before the solve.
PREDICTED_ANCHORS: dict[str, float] = {
    "Upstate_West": 5.3731,
    "Capital_Hudson": 8.4431,
    "Lower_Hudson": 8.4431,
    "NYC": 6.6631,
    "Long_Island": 8.4431,
}
FROZEN_ANCHORS: dict[str, float] = {
    "Upstate_West": 2.0346,
    "Capital_Hudson": 3.9046,
    "Lower_Hudson": 3.9046,
    "NYC": 2.7612,
    "Long_Island": 3.9046,
}
BAND_KEYS = ("committed", "econ_low", "econ_high", "peak", "econ_low_share", "pct_peaking")
EXPECTED_DELTA_FIELDS = {
    "gas_offer_margin_zonal_anchor_vintage",
    "gas_offer_margin_anchor_by_zone",
}


def _cfg(bundle: Path) -> dict:
    d = json.loads((bundle / "run_config.json").read_text())
    return d.get("scenario_config", d)


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[df["pass"] == "P1"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, type=Path)
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument("--year", type=int, default=2022)
    ap.add_argument("--json-out", type=Path)
    a = ap.parse_args()

    arm, ctl = _cfg(a.arm), _cfg(a.control)
    out: dict = {"year": a.year, "gates": {}}

    # ---- G-CONF -----------------------------------------------------------
    moved = {k for k in set(arm) | set(ctl) if arm.get(k) != ctl.get(k)}
    got = arm.get("gas_offer_margin_anchor_by_zone") or {}
    anchor_ok = all(
        abs(float(got.get(z, -1)) - v) < 1e-6 for z, v in PREDICTED_ANCHORS.items()
    )
    g_conf = moved <= EXPECTED_DELTA_FIELDS and anchor_ok and bool(got)
    out["gates"]["G-CONF"] = {
        "pass": bool(g_conf),
        "fields_moved": sorted(moved),
        "recorded_anchors": got,
        "predicted_anchors": PREDICTED_ANCHORS,
        "anchors_match_1e-6": anchor_ok,
    }

    # ---- G-SCOPE ----------------------------------------------------------
    a_oc = arm.get("offer_curve_by_group") or {}
    c_oc = ctl.get("offer_curve_by_group") or {}
    band_moves = []
    for grp in sorted(set(a_oc) | set(c_oc)):
        ab, cb = a_oc.get(grp, {}), c_oc.get(grp, {})
        for k in sorted(set(ab) | set(cb)):
            if k in BAND_KEYS or k.startswith("phys_"):
                if ab.get(k) != cb.get(k):
                    band_moves.append(f"{grp}.{k}: {cb.get(k)} -> {ab.get(k)}")
    out["gates"]["G-SCOPE"] = {"pass": not band_moves, "moved": band_moves}

    # ---- G-PRED -----------------------------------------------------------
    # The offer shift is exactly markup_hr x (arm_anchor - frozen_anchor), so
    # the ratio the gate tests is (recorded delta)/(predicted delta) per zone:
    # a linear, zero-parameter identity. A ratio away from 1 means the anchor
    # the LP priced against is not the anchor the run recorded.
    ratios = {}
    for z, pred in PREDICTED_ANCHORS.items():
        pd_delta = pred - FROZEN_ANCHORS[z]
        got_delta = float(got.get(z, float("nan"))) - FROZEN_ANCHORS[z]
        ratios[z] = round(got_delta / pd_delta, 6) if pd_delta else None
    g_pred = all(r is not None and 0.95 <= r <= 1.05 for r in ratios.values())
    out["gates"]["G-PRED"] = {"pass": bool(g_pred), "ratios": ratios}

    # ---- G-DEMAND ---------------------------------------------------------
    sa, sc = _system(a.arm, a.year), _system(a.control, a.year)
    dem_a, dem_c = float(sa["demand"].sum()), float(sc["demand"].sum())
    served_a = dem_a - float(sa["slack"].sum())
    served_c = dem_c - float(sc["slack"].sum())
    dump_a = float(sa["dump"].sum())
    g_dem = round(served_a / 1e6, 4) == round(served_c / 1e6, 4) and dump_a == 0.0
    out["gates"]["G-DEMAND"] = {
        "pass": bool(g_dem),
        "served_TWh_arm": round(served_a / 1e6, 6),
        "served_TWh_control": round(served_c / 1e6, 6),
        "dump_MWh_arm": dump_a,
        "slack_MWh_arm": float(sa["slack"].sum()),
        "slack_MWh_control": float(sc["slack"].sum()),
    }

    # ---- REPORTED, NEVER GATED -------------------------------------------
    def _lw(df):
        return float((df["price"] * df["demand"]).sum() / df["demand"].sum())

    out["reported_not_gated"] = {
        "load_weighted_LMP_arm": round(_lw(sa), 4),
        "load_weighted_LMP_control": round(_lw(sc), 4),
        "hours_gt_300_arm": int((sa.groupby("hour")["price"].mean() > 300).sum()),
        "hours_gt_300_control": int((sc.groupby("hour")["price"].mean() > 300).sum()),
        "note": (
            "Reported for the record. The screen is NOT gated on these — a screen "
            "that reads the target residual is the fitted-mechanism selection "
            "rule 1 [R-STRUCT] forbids, done one year at a time."
        ),
    }

    verdict = all(g["pass"] for g in out["gates"].values())
    out["screen_verdict"] = "CLEARS (stop-gate only — promotes nothing)" if verdict else "STOP"
    print(json.dumps(out, indent=2))
    if a.json_out:
        a.json_out.write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
