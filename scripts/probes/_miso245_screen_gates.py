"""miso-245 rule-29 SCREEN gates S-1 / S-2 / S-3 — STRUCTURAL and STOP-ONLY.

Bars declared, before the screen ran, in
``results/calibration/ADDENDUM-miso245-the-four-screen-gates-2026-09-08.md`` §1
and quoted here as LITERALS.  S-4 (no collateral flip) is the separate
``scripts/screen_collateral_gate.py``.

CONTROL = the keeper's COMMITTED bundle (rule 29 form 4; G-DRIFT
``a667073f..HEAD`` is EMPTY on the backcast solve path, so no control solve is
earned).  ARM = the screen bundle.

A REAL CONSTRAINT, stated in the addendum before these gates rather than
discovered after: the committed ``hourly/`` sidecars carry NO per-seam split,
only an aggregate net ``import`` class, so S-1 and S-2 are written on the
aggregate -- which is measurable -- and the pre-solve prediction is carried
onto it explicitly.

    S-1  PASS iff  0 <= delta(mean net import) <= 40 MW   (40 = 10 x |dq_hat|)
    S-2  PASS iff  #{h : |delta net import| > 1 MW} <= 860 (10 x the 86-hour
                   pre-solve footprint)
    S-3  PASS iff  (a) derive() reproduces the SOLVED ladder at exactly 0.00 on
                   all 192 entries, AND (b) the arm's run_config scenario_config
                   is identical to the keeper's on every field

None of these is a target residual: the correction HAS no target residual.  Any
STOP kills the arm and the remaining years are never spent.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

# ---- BARS, quoted as literals from the addendum ----------------------------
S1_LO_MW = 0.0
S1_HI_MW = 40.0
S2_HOURS = 860
S2_MW_EPS = 1.0
DQ_HAT_MW = 3.681507  # the pre-solve prediction, re-measured in-session
FOOTPRINT_HOURS = 86
KEEPER = REPO / "results/calibration/miso243_sppair_K"


def _net_import(bundle: Path, year: int) -> np.ndarray:
    """The aggregate net import class, P1, 8,760 hours, MW."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[(df["klass"] == "import") & (df["pass"] == "P1")].sort_values("hour")
    return df["mw"].to_numpy(dtype=float)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, help="the screen bundle directory")
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--out", default="results/calibration/_miso245_screen_gates.json")
    args = ap.parse_args()

    arm = Path(args.arm)
    year = int(args.year)
    rep: dict = {
        "probe": "miso-245 rule-29 screen gates S-1/S-2/S-3 (STRUCTURAL, STOP-only)",
        "addendum": (
            "results/calibration/ADDENDUM-miso245-the-four-screen-gates-2026-09-08.md §1"
        ),
        "control": "results/calibration/miso243_sppair_K (COMMITTED keeper bundle, form 4)",
        "arm": str(arm),
        "screen_year": year,
        "presolve": {"dq_hat_mw": DQ_HAT_MW, "footprint_hours": FOOTPRINT_HOURS},
        "bars": {
            "S1_lo_mw": S1_LO_MW,
            "S1_hi_mw": S1_HI_MW,
            "S2_max_changed_hours": S2_HOURS,
            "S2_mw_eps": S2_MW_EPS,
        },
        "gates": {},
    }

    ctl = _net_import(KEEPER, year)
    a = _net_import(arm, year)
    assert ctl.size == a.size == 8760, f"expected 8760 hours, got {ctl.size}/{a.size}"
    d = a - ctl
    dmean = float(d.mean())
    changed = int(np.count_nonzero(np.abs(d) > S2_MW_EPS))

    rep["gates"]["S1_direction_and_magnitude"] = {
        "control_mean_net_import_mw": round(float(ctl.mean()), 6),
        "arm_mean_net_import_mw": round(float(a.mean()), 6),
        "delta_mean_mw": round(dmean, 6),
        "delta_over_dq_hat": round(dmean / DQ_HAT_MW, 4),
        "bar": f"{S1_LO_MW} <= delta <= {S1_HI_MW}",
        "PASS": bool(S1_LO_MW <= dmean <= S1_HI_MW),
    }
    rep["gates"]["S2_footprint_confinement"] = {
        "hours_changed_gt_1mw": changed,
        "share_of_year": round(changed / 8760.0, 6),
        "presolve_footprint_hours": FOOTPRINT_HOURS,
        "bar": f"<= {S2_HOURS}",
        "PASS": bool(changed <= S2_HOURS),
    }
    # Reported beside the gates, never gated.
    rep["reported_delta_shape"] = {
        "max_abs_delta_mw": round(float(np.max(np.abs(d))), 6),
        "sum_delta_mwh": round(float(d.sum()), 3),
        "hours_positive": int(np.count_nonzero(d > S2_MW_EPS)),
        "hours_negative": int(np.count_nonzero(d < -S2_MW_EPS)),
    }

    # ---- S-3(a): the solved ladder IS derive()'s output --------------------
    script = REPO / "scripts/data/derive_miso_seam_ladders.py"
    spec = importlib.util.spec_from_file_location("_miso245_sg_derive", script)
    dm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dm)
    from market_sim.config.interchange_config import MISO_SEAM_LADDER_BY_YEAR

    g_all = dm.load_joined()
    worst = 0.0
    n_entries = 0
    for y, ladder in MISO_SEAM_LADDER_BY_YEAR.items():
        derived, _notes = dm.derive(g_all.loc[[y]])
        for seam, sides in ladder.items():
            for side in ("import", "export"):
                for k, committed in enumerate(sides[side]):
                    n_entries += 1
                    worst = max(
                        worst, abs(float(derived[seam][side][k]) - float(committed))
                    )

    # ---- S-3(b): the arm's scenario_config equals the keeper's -------------
    kc = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    ac = json.loads((arm / "run_config.json").read_text())["scenario_config"]
    diff = {
        k: {"keeper": kc.get(k), "arm": ac.get(k)}
        for k in sorted(set(kc) | set(ac))
        if kc.get(k) != ac.get(k)
    }
    rep["gates"]["S3_identity_and_clean_ab"] = {
        "a_derive_reproduces_solved_table": {
            "entries": n_entries,
            "max_abs_delta": round(worst, 9),
            "PASS": bool(n_entries == 192 and worst < 5e-9),
        },
        "b_scenario_config_identical": {
            "n_fields_keeper": len(kc),
            "n_fields_arm": len(ac),
            "differing_fields": diff,
            "PASS": bool(not diff),
        },
        "PASS": bool(n_entries == 192 and worst < 5e-9 and not diff),
    }

    stops = [k for k, v in rep["gates"].items() if not v["PASS"]]
    rep["STOPPED_BY"] = stops
    rep["S1_S2_S3_ALL_CLEAR"] = not stops
    Path(args.out).write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
