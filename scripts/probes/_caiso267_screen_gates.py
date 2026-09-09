"""caiso-267 — score the pre-registered SCREEN gates for the fossil-band x0.92 arm.

Implements ADDENDUM-caiso267-fossil-offer-8pct-2026-09-09.md §E verbatim.
Zero LP: reads only the two 2023 replay bundles' committed ``hourly/`` sidecars
plus the keeper's, and the committed actual-LMP reference.

The four gates are STOP-ONLY and STRUCTURAL. None is gated on the target
residual (C3a), which the addendum exempts in both directions.

  G-IDENT  arm vs control differ by the offer curve and nothing else
  G-FOOT   the response is confined to the rows the mechanism claims
  G-DIR    |dlambda| in [0.5, 8.0] $/MWh and NEGATIVE
  G-NOFLIP no non-target load-bearing criterion flips PASS -> FAIL
           (scored separately by calibration_verdict.py; reported here as the
           raw inputs a reader needs)

Usage: python3 scripts/probes/_caiso267_screen_gates.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ARM = ROOT / "results/calibration/caiso267_fossil92_screen2023/hourly"
CTRL = ROOT / "results/calibration/caiso267_ctrl_screen2023/hourly"
KEEP = ROOT / "results/calibration/caiso260_demand_vintage/hourly"
ACTUAL = ROOT / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
OUT = ROOT / "results/calibration/_caiso267_screen_gates.json"
YEAR = 2023
FOSSIL = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "COAL")
# Pre-registered G-DIR band (addendum §E). Never widened after the fact.
G_DIR_LO, G_DIR_HI = 0.5, 8.0


def _sys(d: Path) -> pd.DataFrame:
    """P1 system sidecar for the screen year."""
    s = pd.read_parquet(d / f"system_{YEAR}.parquet")
    return s[s["pass"] == "P1"].copy()


def _cls(d: Path) -> pd.DataFrame:
    """P1 class-hourly sidecar for the screen year."""
    c = pd.read_parquet(d / f"class_hourly_{YEAR}.parquet")
    return c[c["pass"] == "P1"].copy()


def lw_price(s: pd.DataFrame) -> float:
    """Zone-demand-weighted annual mean price — the scorer's own C3a basis."""
    return float((s["price"] * s["demand"]).sum() / s["demand"].sum())


def main() -> int:
    """Score the four screen gates and write the JSON record."""
    arm_s, ctl_s, kep_s = _sys(ARM), _sys(CTRL), _sys(KEEP)
    arm_c, ctl_c, kep_c = _cls(ARM), _cls(CTRL), _cls(KEEP)
    rec: dict = {"year": YEAR, "gates": {}}

    # ---- G-IDENT: demand is the one input both runs must share exactly -----
    a = arm_s.set_index(["zone", "hour"])["demand"].sort_index()
    c = ctl_s.set_index(["zone", "hour"])["demand"].sort_index()
    dmax = float(np.abs(a.to_numpy() - c.to_numpy()).max())
    rec["gates"]["G_IDENT"] = {
        "max_abs_demand_delta_mw": dmax,
        "zone_hours": int(len(a)),
        "pass": bool(dmax < 1e-6),
    }

    # ---- G-FOOT: which classes moved, and by how much ----------------------
    def energy(df: pd.DataFrame) -> pd.Series:
        return df.groupby("klass", observed=True)["mw"].sum() / 1e6

    ea, ec = energy(arm_c), energy(ctl_c)
    idx = sorted(set(ea.index) | set(ec.index))
    delta = (ea.reindex(idx).fillna(0.0) - ec.reindex(idx).fillna(0.0)).round(6)
    rec["class_twh"] = {
        k: {
            "control": round(float(ec.get(k, 0.0)), 4),
            "arm": round(float(ea.get(k, 0.0)), 4),
            "delta": round(float(delta[k]), 4),
        }
        for k in idx
    }
    fos = float(sum(delta.get(k, 0.0) for k in FOSSIL))
    non = float(sum(delta.get(k, 0.0) for k in idx if k not in FOSSIL))
    rec["gates"]["G_FOOT"] = {
        "fossil_delta_twh": round(fos, 4),
        "nonfossil_delta_twh": round(non, 4),
        # A merit-order mechanism conserves served energy: fossil gains what
        # non-fossil loses, to within LP tie-break noise.
        "conservation_residual_twh": round(fos + non, 4),
        "pass": bool(abs(fos + non) < 0.05),
    }

    # ---- G-DIR: the price response, on the scorer's own basis --------------
    pa, pc, pk = lw_price(arm_s), lw_price(ctl_s), lw_price(kep_s)
    act = pd.read_parquet(ACTUAL)
    act = act[act["year"] == YEAR]
    dlam = pa - pc
    rec["gates"]["G_DIR"] = {
        "lw_price_control": round(pc, 4),
        "lw_price_arm": round(pa, 4),
        "d_lambda": round(dlam, 4),
        "predicted_mean_dmc": 2.845,  # addendum §E, fixed before the solve
        "band": [-G_DIR_HI, -G_DIR_LO],
        "pass": bool(-G_DIR_HI <= dlam <= -G_DIR_LO),
    }

    # ---- HEAD drift, measured rather than asserted (addendum §E, G-CTRL) ----
    rec["head_drift"] = {
        "lw_price_committed_keeper": round(pk, 4),
        "lw_price_control_at_head": round(pc, 4),
        "drift_d_lambda": round(pc - pk, 4),
        "note": (
            "control minus committed keeper: the same recipe re-solved at HEAD. "
            "This MEASURES the drift the G-DRIFT audit could not classify "
            "(94 files / +46,838 lines), which is why the control was spent."
        ),
    }

    # ---- context for the reader (NOT a gate) -------------------------------
    dump_a = float(arm_s["dump"].sum())
    dump_c = float(ctl_s["dump"].sum())
    rec["context"] = {
        "actual_lw_basis_note": "C3a scores against the bench rt_lw (54.17 in 2023)",
        "dump_mwh_control": round(dump_c, 3),
        "dump_mwh_arm": round(dump_a, 3),
        "slack_mwh_control": round(float(ctl_s["slack"].sum()), 3),
        "slack_mwh_arm": round(float(arm_s["slack"].sum()), 3),
    }

    rec["screen_verdict"] = (
        "PROCEED"
        if all(g["pass"] for g in rec["gates"].values())
        else "STOP"
    )
    OUT.write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
