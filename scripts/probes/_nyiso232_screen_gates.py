"""nyiso-232 SCREEN GATES — written and committed BEFORE the arm's numbers exist.

Scores the five STOP gates pre-registered in
``results/calibration/PRECOMMIT-nyiso232-st-gas-deleak.md`` §6 for the 2022 screen
of ``nyiso_st_gas_econ_bands_deleaked``, against the designated keeper's committed
2022 leg as the control (rule 29 ``[R-SCREEN]`` (b) form 4; the G-DRIFT audit in
PRECOMMIT §4 found every changed hunk INERT for NYISO).

Rule 29: a screen MAY KILL AN ARM; IT MAY NEVER PROMOTE ONE. No gate here reads the
target residual, and none is re-cut after the fact.

Usage: ``python3 scripts/probes/_nyiso232_screen_gates.py <arm-bundle-dir>``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

CTL = Path("results/calibration/nyiso231_anchor_span")
YEAR = 2022

#: PRECOMMIT §3 / §5, all fixed before the solve.
PREDICTED_ST_GAS_ROWS = 44
INMERIT_WIDENING_TWH = 1.574  # the pre-solve ceiling on the ST_GAS energy rise
DEMAND_TOL_TWH = 1e-4
NONTARGET_LOADBEARING = ("sysvol", "price_mean", "price_shape")
#: Already FAILING on the control in 2022, so they cannot flip PASS -> FAIL.
ALREADY_FAILING_2022 = {("fuelmix", "CC_REGULAR"), ("price_shape", None)}


def _p1(bundle: Path, name: str) -> pd.DataFrame:
    d = pd.read_parquet(bundle / "hourly" / f"{name}_{YEAR}.parquet")
    return d[d["pass"] == "P1"]


def _system(bundle: Path) -> dict:
    s = _p1(bundle, "system")
    lw = float((s.price * s.demand).sum() / s.demand.sum())
    return {
        "lw_price": lw,
        "mean_price": float(s.groupby("hour").price.mean().mean()),
        "served_twh": float(s.demand.sum()) / 1e6,
        "dump_mwh": float(s.dump.sum()),
        "slack_mwh": float(s.slack.sum()),
        "hours_gt_300": int(
            (
                s.groupby("hour").apply(
                    lambda d: float((d.price * d.demand).sum() / d.demand.sum()),
                    include_groups=False,
                )
                > 300
            ).sum()
        ),
    }


def _class_twh(bundle: Path) -> dict[str, float]:
    c = _p1(bundle, "class_hourly")
    return {str(k): float(v) / 1e6 for k, v in c.groupby("klass").mw.sum().items()}


def _st_gas_rows(bundle: Path) -> int:
    b = _p1(bundle, "class_band_hourly")
    return int(b[b.klass == "ST_GAS"].band.nunique() * 11)  # 11 NYISO ST_GAS plants


def main() -> None:
    arm = Path(sys.argv[1])
    res: dict[str, dict] = {}

    sys_c, sys_a = _system(CTL), _system(arm)
    cls_c, cls_a = _class_twh(CTL), _class_twh(arm)
    iso_load = sys_c["served_twh"]

    # --- G-CONFINE ------------------------------------------------------
    moves = {
        k: cls_a.get(k, 0.0) - cls_c.get(k, 0.0)
        for k in set(cls_c) | set(cls_a)
        if k != "ST_GAS"
    }
    worst = max(moves.items(), key=lambda kv: abs(kv[1])) if moves else ("-", 0.0)
    res["G-CONFINE"] = {
        "verdict": "PASS" if abs(worst[1]) <= 0.005 * iso_load else "STOP",
        "worst_nonST_GAS_class": worst[0],
        "worst_move_TWh": worst[1],
        "budget_TWh": 0.005 * iso_load,
        "all_moves_TWh": {k: round(v, 4) for k, v in sorted(moves.items())},
    }

    # --- G-DEMAND (served demand ONLY; never class-hours, never non-gas mc) ---
    dd = abs(sys_a["served_twh"] - sys_c["served_twh"])
    res["G-DEMAND"] = {
        "verdict": "PASS"
        if (
            dd <= DEMAND_TOL_TWH
            and sys_a["dump_mwh"] == 0.0
            and sys_a["slack_mwh"] == 0.0
        )
        else "STOP",
        "served_ctl_TWh": sys_c["served_twh"],
        "served_arm_TWh": sys_a["served_twh"],
        "delta_TWh": dd,
        "dump_MWh": sys_a["dump_mwh"],
        "slack_MWh": sys_a["slack_mwh"],
    }

    # --- G-MAGNITUDE ----------------------------------------------------
    st = cls_a.get("ST_GAS", 0.0) - cls_c.get("ST_GAS", 0.0)
    res["G-MAGNITUDE"] = {
        "verdict": "PASS" if (st > 0 and st <= INMERIT_WIDENING_TWH) else "STOP",
        "ST_GAS_ctl_TWh": cls_c.get("ST_GAS"),
        "ST_GAS_arm_TWh": cls_a.get("ST_GAS"),
        "delta_TWh": st,
        "presolve_ceiling_TWh": INMERIT_WIDENING_TWH,
    }

    # --- G-ROWS ---------------------------------------------------------
    n = _st_gas_rows(arm)
    res["G-ROWS"] = {
        "verdict": "PASS" if n == PREDICTED_ST_GAS_ROWS else "STOP",
        "st_gas_rows_arm": n,
        "predicted": PREDICTED_ST_GAS_ROWS,
        "bands_arm": sorted(
            _p1(arm, "class_band_hourly")
            .pipe(lambda d: d[d.klass == "ST_GAS"])
            .band.unique()
            .tolist()
        ),
    }

    # --- G-NONTARGET ----------------------------------------------------
    # Scored from calibration_verdict.py --json on BOTH legs; a criterion that
    # already FAILS on the control cannot flip.
    res["G-NONTARGET"] = {
        "verdict": "SCORED-SEPARATELY",
        "note": "run calibration_verdict.py --json on the arm and "
        "compare the 2022 records against the control's",
    }

    res["_system"] = {"ctl": sys_c, "arm": sys_a}
    res["_class_TWh"] = {"ctl": cls_c, "arm": cls_a}

    stops = [
        k for k, v in res.items() if isinstance(v, dict) and v.get("verdict") == "STOP"
    ]
    res["_SCREEN"] = "STOP" if stops else "CLEARS (pending G-NONTARGET)"

    print(json.dumps(res, indent=1, default=float))
    Path("results/calibration/_nyiso232_screen_gates.json").write_text(
        json.dumps(res, indent=1, default=float)
    )
    print(f"\nSCREEN: {res['_SCREEN']}" + (f"  stopped by {stops}" if stops else ""))


if __name__ == "__main__":
    main()
