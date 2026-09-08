#!/usr/bin/env python3
"""miso-243 SCREEN GATE — evaluate the four pre-registered STRUCTURAL STOP-only gates.

Every bar is quoted from
``results/calibration/ADDENDUM-miso243-my-own-p2-leg-failed-and-the-screen-year-is-2024-2026-09-07.md``
section 3, which was pushed BEFORE the repair was applied to the tree and BEFORE
the screen solve was launched. **No bar is computed here; each is a literal.**

Control = the keeper's COMMITTED bundle (G-CTRL form 4; the G-DRIFT audit in
PREREG section 0c classified every hunk INERT, so no control solve is spent).

The gates may KILL the arm; they may never promote it, and none of them is the
target residual.

Usage:
    python3 scripts/probes/_miso243_screen_gates.py <screen-bundle> <year>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/miso233_sppseam_K"
CAL = REPO / "results/calibration"

# ---- ADDENDUM section 3 bars, fixed ex ante, quoted as literals ----
DQ_HAT_MW = -107.65  # P-4, model basis, 2024
G3_LO, G3_HI = 0.25, 4.0  # the factor-4 window
G2A_RATIO_BAR = 4.0  # sum |d class| / |d import|
G2B_SERVED_PCT = 0.5  # total served energy, %
G1_MUSTTAKE_PCT = 0.5  # wind + solar + nuclear + hydro, %
MUST_TAKE = ("wind", "solar", "nuclear", "hydro")


def _class_energy(bundle: Path, year: int) -> pd.Series:
    """Annual P1 energy (MWh) per class from a bundle's hourly sidecar."""
    f = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    f = f[f["pass"] == "P1"]
    return f.groupby("klass", observed=True)["mw"].sum().astype(float)


def _import_mean(bundle: Path, year: int) -> float:
    """Mean of the net ``import`` class (MW)."""
    f = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    f = f[(f["pass"] == "P1") & (f["klass"] == "import")]
    return float(f["mw"].mean())


def _system(bundle: Path, year: int) -> pd.DataFrame:
    f = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    return f[f["pass"] == "P1"]


def main() -> None:
    """Evaluate G-1, G-2', G-3 and report; G-4 is run separately by its own script."""
    arm = Path(sys.argv[1])
    year = int(sys.argv[2])
    out = {
        "probe": "miso-243 screen gate (2024)",
        "arm_bundle": str(arm),
        "control": "results/calibration/miso233_sppseam_K (COMMITTED, G-CTRL form 4)",
        "year": year,
        "bars_source": (
            "ADDENDUM-miso243-my-own-p2-leg-failed-and-the-screen-year-is-2024"
            "-2026-09-07.md section 3, pushed before the solve"
        ),
        "gates": {},
    }

    ka, aa = _class_energy(KEEPER, year), _class_energy(arm, year)
    classes = sorted(set(ka.index) | set(aa.index))
    d = {c: float(aa.get(c, 0.0) - ka.get(c, 0.0)) for c in classes}

    ks, asy = _system(KEEPER, year), _system(arm, year)
    k_slack, a_slack = float(ks["slack"].sum()), float(asy["slack"].sum())
    k_dump, a_dump = float(ks["dump"].sum()), float(asy["dump"].sum())

    # ---- G-1 CONFINEMENT ----
    mt = {}
    mt_ok = True
    for c in MUST_TAKE:
        base = float(ka.get(c, 0.0))
        pct = 100.0 * (float(aa.get(c, 0.0)) - base) / base if base else 0.0
        mt[c] = round(pct, 4)
        mt_ok &= abs(pct) <= G1_MUSTTAKE_PCT
    slack_ok = a_slack <= k_slack * (1 + 1e-6) + 1e-6
    dump_ok = a_dump <= k_dump * (1 + 1e-6) + 1e-6
    out["gates"]["G_1_confinement"] = {
        "slack_mwh_keeper": k_slack,
        "slack_mwh_arm": a_slack,
        "dump_mwh_keeper": k_dump,
        "dump_mwh_arm": a_dump,
        "must_take_pct_change": mt,
        "bar": f"slack/dump not above keeper; must-take within {G1_MUSTTAKE_PCT}%",
        "PASS": bool(slack_ok and dump_ok and mt_ok),
    }

    # ---- G-2'(a) DISPLACEMENT + G-2'(b) SCALE ----
    d_import = d.get("import", 0.0)
    sum_abs_gen = sum(abs(v) for c, v in d.items() if c != "import")
    ratio = sum_abs_gen / abs(d_import) if d_import else float("inf")
    served_k = float(ka.sum())
    served_a = float(aa.sum())
    served_pct = 100.0 * (served_a - served_k) / served_k if served_k else 0.0
    out["gates"]["G_2a_displacement"] = {
        "delta_import_mwh": round(d_import, 1),
        "sum_abs_delta_generation_mwh": round(sum_abs_gen, 1),
        "ratio": round(ratio, 4),
        "bar": f"<= {G2A_RATIO_BAR}",
        "PASS": bool(ratio <= G2A_RATIO_BAR),
    }
    out["gates"]["G_2b_scale"] = {
        "served_energy_pct_change": round(served_pct, 5),
        "bar": f"<= {G2B_SERVED_PCT}%",
        "PASS": bool(abs(served_pct) <= G2B_SERVED_PCT),
    }

    # ---- G-3 DIRECTION & ORDER OF MAGNITUDE ----
    dq = _import_mean(arm, year) - _import_mean(KEEPER, year)
    ratio3 = dq / DQ_HAT_MW if DQ_HAT_MW else float("nan")
    sign_ok = (dq < 0) == (DQ_HAT_MW < 0) and dq != 0.0
    win_ok = G3_LO <= ratio3 <= G3_HI
    out["gates"]["G_3_direction_and_magnitude"] = {
        "dq_hat_mw": DQ_HAT_MW,
        "dq_solved_mw": round(dq, 3),
        "ratio_solved_over_hat": round(ratio3, 4),
        "window": [
            round(G3_LO * DQ_HAT_MW, 2),
            round(G3_HI * DQ_HAT_MW, 2),
        ],
        "sign_matches": bool(sign_ok),
        "in_window": bool(win_ok),
        "bar": f"sign match AND {G3_LO} <= ratio <= {G3_HI}",
        "PASS": bool(sign_ok and win_ok),
    }

    # ---- REPORTED, NEVER GATED ----
    out["reported_never_gated"] = {
        "per_class_delta_mwh": {c: round(v, 1) for c, v in sorted(d.items())},
        "note": (
            "Every criterion band, the measured-price decile slope and the "
            "system interchange ratio are REPORTED elsewhere and are NOT gates "
            "here (PREREG section 3 / ADDENDUM section 3)."
        ),
    }

    gated = [k for k in out["gates"] if not out["gates"][k]["PASS"]]
    out["FAILED_GATES"] = gated
    out["ALL_GATES_PASS_EXCEPT_G4"] = not gated
    p = CAL / "_miso243_screen_gates.json"
    p.write_text(json.dumps(out, indent=1))
    print(json.dumps(out["gates"], indent=1))
    print("FAILED:", gated or "NONE (G-4 evaluated separately)")


if __name__ == "__main__":
    main()
