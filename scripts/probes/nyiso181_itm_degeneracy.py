"""nyiso-181 — is the un-dispatched in-the-money ``ST_GAS`` signature LP degeneracy?

Adjudicates the stronger of the two carriers nyiso-180 §12.3 handed forward for
the re-posed object, on the LP's **own reduced cost** — the first direct
measurement available, because
``results/calibration/*/hourly/unit_hourly_*.parquet`` is gitignored
(``.gitignore:541``) and no committed NYISO bundle carries it.

Every gate, tolerance and verdict below is fixed in
``results/calibration/PREREG-nyiso181-itm-degeneracy.md`` §2, committed together
with this file and before either was run.

The instrument is the generation column's stationarity identity

    red_cost[g,t] = mc[g,t] - price[zone(g),t] + sum_r a(r,g) * y_r
    omega[g,t]   := red_cost[g,t] - (mc[g,t] - price[zone(g),t])

so ``omega`` is exactly the net rent every NON-energy row charges that
unit-hour, and a column at its LOWER bound with ``red_cost ~ 0`` is
**dual-degenerate**: the LP is indifferent to dispatching it, an alternative
optimal basis does dispatch it, and the objective is unchanged. That is the
precise LP meaning of "degeneracy at a price plateau", and it is the thing
``mc <= price`` cannot see.

The population, the in-the-money test and the year loop are IMPORTED from
``nyiso180_unit_dispatch_adjudication`` rather than re-derived, so the two
sessions provably measure the same object (PREREG §0.1).

Usage:
    python scripts/probes/nyiso181_itm_degeneracy.py <bundle> [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.probes.nyiso180_unit_dispatch_adjudication import (  # noqa: E402
    YEARS,
    _class_mask,
    _fmt,
    _load_year,
)

# The reported sensitivity ladder. ONLY the $1.00 rung decides (PREREG §2 G-D);
# it is INHERITED from the parallel lane's already-committed ITM_EPS_STRICT and
# is fixed before measurement so no rung can be chosen after seeing the answer.
EPS_LADDER = (0.01, 0.10, 1.00, 5.00)
EPS_DECIDE = 1.00

# PREREG §2 bars, fixed before measurement.
DSHARE_BAR = 0.50
PSHARE_BAR = 0.50


def analyse_year(df: pd.DataFrame, year: int) -> dict:
    """G-D / G-P / G-S / G-L for one year on the ``ST_GAS`` population."""
    cls = df[_class_mask(df)]
    if cls.empty:
        raise SystemExit(f"{year}: ST_GAS population is empty — class test is wrong")

    mc = cls["mc"].to_numpy(dtype=float)
    price = cls["price"].to_numpy(dtype=float)
    rc = cls["red_cost"].to_numpy(dtype=float)
    mw = cls["mw"].to_numpy(dtype=float)
    cap = cls["cap_mw"].to_numpy(dtype=float)
    hour = cls["hour"].to_numpy()
    omega = rc - (mc - price)

    # The object, on nyiso-179's own in-the-money definition (inherited).
    itm = mc <= price
    unrun = np.where(itm, np.maximum(cap - mw, 0.0), 0.0)
    U = float(unrun.sum())
    if U <= 0:
        raise SystemExit(f"{year}: no in-the-money un-run MW — the object is absent")

    # --- G-D: the degenerate share, over the reported ladder ---------------
    ladder = {
        f"{eps:.2f}": _fmt(float(unrun[np.abs(rc) <= eps].sum()) / U)
        for eps in EPS_LADDER
    }
    deg = np.abs(rc) <= EPS_DECIDE
    dshare = float(unrun[deg].sum()) / U

    # --- G-P: within the degenerate MW, plateau vs a charged row -----------
    deg_mw = float(unrun[deg].sum())
    plateau = deg & (np.abs(omega) <= EPS_DECIDE)
    charged = deg & (np.abs(omega) > EPS_DECIDE)
    pshare = (float(unrun[plateau].sum()) / deg_mw) if deg_mw > 0 else None

    # --- G-S: the successor statistic — MW genuinely held off by a row -----
    held_off = itm & (rc > EPS_DECIDE)
    u_strict = float(unrun[held_off].sum())

    # --- G-L: the level -----------------------------------------------------
    n_hours = int(pd.Series(hour).nunique())
    near = np.abs(mc - price) <= EPS_DECIDE
    plateau_cap_by_hour = (
        pd.Series(np.where(near, cap, 0.0)).groupby(pd.Series(hour)).sum()
    )
    unrun_by_hour = pd.Series(unrun).groupby(pd.Series(hour)).sum()

    return {
        "year": year,
        "class_unit_hours": int(len(cls)),
        "n_units": int(cls["unit_id"].nunique()),
        "hours": n_hours,
        "object": {
            "itm_unrun_mwh": _fmt(U),
            "itm_unrun_twh": _fmt(U / 1e6),
            "mean_itm_unrun_mw": _fmt(U / n_hours) if n_hours else None,
        },
        "G_D_degeneracy": {
            "ladder_dshare_by_eps": ladder,
            "deciding_eps": EPS_DECIDE,
            "dshare_at_deciding_eps": _fmt(dshare),
            "bar": DSHARE_BAR,
            "PASS": bool(dshare >= DSHARE_BAR),
        },
        "G_P_plateau_vs_charged": {
            "degenerate_mwh": _fmt(deg_mw),
            "plateau_mwh": _fmt(float(unrun[plateau].sum())),
            "charged_mwh": _fmt(float(unrun[charged].sum())),
            "pshare": _fmt(pshare),
            "bar": PSHARE_BAR,
            "PASS": bool(pshare is not None and pshare >= PSHARE_BAR),
            "omega_p50_on_charged": (
                _fmt(float(np.median(omega[charged]))) if charged.any() else None
            ),
            "omega_p95_abs_on_charged": (
                _fmt(float(np.percentile(np.abs(omega[charged]), 95)))
                if charged.any()
                else None
            ),
        },
        "G_S_successor_statistic": {
            "u_strict_mwh": _fmt(u_strict),
            "u_strict_twh": _fmt(u_strict / 1e6),
            "mean_u_strict_mw": _fmt(u_strict / n_hours) if n_hours else None,
            "share_of_published_object": _fmt(u_strict / U),
        },
        "G_L_level": {
            "mean_plateau_cap_mw": _fmt(float(plateau_cap_by_hour.mean())),
            "mean_itm_unrun_mw": _fmt(float(unrun_by_hour.mean())),
            "ratio_plateau_cap_over_unrun": _fmt(
                float(plateau_cap_by_hour.mean() / unrun_by_hour.mean())
                if unrun_by_hour.mean() > 0
                else None
            ),
        },
    }


def _verdicts(years: dict) -> dict:
    """PREREG §2's verdict words, computed from the per-year gate results."""
    scored = [v for v in years.values() if v.get("class_unit_hours")]
    if not scored:
        return {"G_D": "NOT MEASURED", "G_P": "NOT MEASURED"}
    d = [v["G_D_degeneracy"]["PASS"] for v in scored]
    p = [v["G_P_plateau_vs_charged"]["PASS"] for v in scored]
    if all(d):
        gd = "DEGENERACY-CARRIES"
    elif any(d):
        gd = "DEGENERACY-PARTIAL"
    else:
        gd = "DEGENERACY-REFUTED"
    return {
        "G_D": gd,
        "G_P": "PLATEAU" if all(p) else "CHARGED",
        "years_scored": len(scored),
    }


def adjudication_status(report: dict) -> dict:
    """PREREG §4 S1: did an instrument check fail, withholding every verdict?

    ADDED AFTER THE GATES RAN, and additive only — the gate computation and
    every bar above are untouched (the nyiso-180 §8.1 discipline: the
    INSTRUMENT is repaired, no bar is moved). Without this block a reader of
    the JSON would take ``verdicts`` for the session's adjudication, which
    S1 withholds.

    I1 (replay identity) and I2/I3 (the parallel lane's §2.4 STOP and P-b) are
    read from the two committed instrument records rather than recomputed.
    """
    i1p = REPO / "results/calibration/_nyiso181_replay_identity.json"
    i23p = REPO / "results/calibration/_nyiso181_unit_dispatch_nyiso180gates.json"
    out: dict = {"I1": None, "I2": None, "I3": None}
    if i1p.exists():
        out["I1"] = bool(json.loads(i1p.read_text()).get("I1_PASS_ALL_YEARS"))
    if i23p.exists():
        yrs = json.loads(i23p.read_text()).get("years", {})
        out["I2"] = all(
            v["STOP_2_4_identity_does_not_close"]["share_of_class_unit_hours"] < 0.001
            for v in yrs.values()
            if "STOP_2_4_identity_does_not_close" in v
        )
        out["I3"] = all(
            v["P_b_price_is_the_dual"]["PASS"]
            for v in yrs.values()
            if "P_b_price_is_the_dual" in v
        )
        out["I3_per_year_mean_mc_minus_price"] = {
            y: v["P_b_price_is_the_dual"]["mean_mc_minus_price"]
            for y, v in yrs.items()
            if "P_b_price_is_the_dual" in v
        }
    fired = any(v is False for v in (out["I1"], out["I2"], out["I3"]))
    out["S1_FIRED"] = fired
    out["verdicts_are"] = "WITHHELD (PREREG §4 S1)" if fired else "ADJUDICATED"
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    bundle = args.bundle if args.bundle.is_absolute() else REPO / args.bundle
    report: dict = {"bundle": str(bundle.relative_to(REPO)), "years": {}}
    for year in YEARS:
        df = _load_year(bundle, year)
        if df is None:
            report["years"][str(year)] = {"available": False}
            continue
        report["years"][str(year)] = analyse_year(df, year)
    report["verdicts"] = _verdicts(report["years"])
    report["adjudication_status"] = adjudication_status(report)

    out = args.out or (REPO / "results/calibration/_nyiso181_itm_degeneracy.json")
    out.write_text(json.dumps(report, indent=2))
    json.dump(report, sys.stdout, indent=2)
    print(f"\n\nwrote {out}")


if __name__ == "__main__":
    main()
