"""nyiso-118: score the pre-registered gates for the SENY ORDC span arm.

Discharges the gate set in
``results/calibration/PREREG-nyiso118-seny-span-2026-08-03.md`` §6 against the
two bundles' COMMITTED artifacts. No solve is replayed.

THE INSTRUMENT SPLIT, stated because it is the point:

* ``hourly/reserve_family_<year>.parquet`` carries ``requirement_mw`` (the
  balance-row RHS — a pure INPUT) and ``dual`` / ``held_mw`` / ``shortfall_mw``
  (SOLVED co-optimization outputs). It does **not** carry the ORDC step-width
  vectors. So the parquet can discharge the requirement legs and the LP row
  identity, and it CANNOT discharge the width legs.
* The width legs (G1, G2b's width half, K-A, K-B, K-E) are therefore scored on
  the committed CONSTRUCTION artifact
  ``results/calibration/nyiso118_span_construction_probe.json`` plus each
  bundle's committed ``ordc_steps.log`` — never on a dual.

Gating a scope kill on ``dual`` or ``held_mw`` can only pass when the mechanism
does nothing (the nyiso-115 G2 error). Those are REPORTED here (G2d), not gated.

Byte-identity is float32 EXACT equality (``np.array_equal``). No tolerance is
used: the sidecar columns are float32 with spacing 7.6e-06-6.1e-05 MW, so a
1e-6 MW tolerance is unsatisfiable in principle (nyiso-116 G3/P4).

Run:
    PYTHONPATH=.:src python scripts/probes/_nyiso118_score_gates.py \\
        --control results/calibration/nyiso118_control \\
        --treatment results/calibration/nyiso118_seny_span \\
        --construction results/calibration/nyiso118_span_construction_probe.json \\
        --json-out results/calibration/nyiso118_gate_scores.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = (2023, 2024, 2025)
SENY = "seny_30min_total"
NYC_PAIR = ("nyc_10min_total", "nyc_30min_total")
LI30 = "li_30min_total"


def _fam(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"reserve_family_{year}.parquet")
    return df.sort_values(["pass", "family", "hour"], kind="mergesort").reset_index(
        drop=True
    )


def _sys(bundle: Path, year: int) -> pd.DataFrame:
    return pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", type=Path, required=True)
    ap.add_argument("--treatment", type=Path, required=True)
    ap.add_argument("--construction", type=Path, required=True)
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args()

    constr = json.loads(args.construction.read_text())
    out: dict = {
        "probe": "nyiso-118 pre-registered gate scoring",
        "prereg": "results/calibration/PREREG-nyiso118-seny-span-2026-08-03.md §6",
        "control": str(args.control),
        "treatment": str(args.treatment),
        "instrument_note": (
            "requirement legs + LP row identity from reserve_family parquet; "
            "WIDTH legs from the committed construction probe + ordc_steps.log "
            "(the parquet carries no width vectors); dual/held/shortfall "
            "REPORTED, never gated"
        ),
        "years": {},
        "gates": {},
        "kills": {},
    }

    g2a_ok, g2b_ok, g3_ok, g4_ok = True, True, True, True
    per_year: dict = {}

    for year in YEARS:
        c, t = _fam(args.control, year), _fam(args.treatment, year)
        assert list(c.columns) == list(t.columns)
        fams = sorted(set(c["family"].astype(str)))
        yr: dict = {"families": {}}

        for name in fams:
            cc = c[c["family"].astype(str) == name]
            tt = t[t["family"].astype(str) == name]
            req_c = cc["requirement_mw"].to_numpy()
            req_t = tt["requirement_mw"].to_numpy()
            same_req = bool(
                req_c.shape == req_t.shape and np.array_equal(req_c, req_t)
            )
            if not same_req:
                g2a_ok = False
                if name == LI30:
                    g2b_ok = False
            # G3: LP row identity, both arms
            for arm, df in (("control", cc), ("treatment", tt)):
                held = df["held_mw"].to_numpy(dtype=float)
                short = df["shortfall_mw"].to_numpy(dtype=float)
                req = df["requirement_mw"].to_numpy(dtype=float)
                if not bool((held + short >= req - 1e-3).all()):
                    g3_ok = False
            d_c = cc["dual"].to_numpy(dtype=float)
            d_t = tt["dual"].to_numpy(dtype=float)
            s_c = cc["shortfall_mw"].to_numpy(dtype=float)
            s_t = tt["shortfall_mw"].to_numpy(dtype=float)
            h_c = cc["held_mw"].to_numpy(dtype=float)
            h_t = tt["held_mw"].to_numpy(dtype=float)
            yr["families"][name] = {
                "requirement_identical": same_req,  # GATED (G2a/G2b/K-C)
                # REPORTED, NOT GATED (G2d) — solved co-optimization outputs.
                "dual_identical": bool(np.array_equal(d_c, d_t)),
                "max_abs_dual_delta": float(np.abs(d_c - d_t).max()),
                "hours_dual_pos_control": int((d_c > 0).sum()),
                "hours_dual_pos_treatment": int((d_t > 0).sum()),
                "max_dual_control": float(d_c.max()),
                "max_dual_treatment": float(d_t.max()),
                "max_abs_held_delta": float(np.abs(h_c - h_t).max()),
                "max_abs_shortfall_delta": float(np.abs(s_c - s_t).max()),
                "max_shortfall_control": float(s_c.max()),
                "max_shortfall_treatment": float(s_t.max()),
            }

        # G4: feasibility, both arms
        sc, st = _sys(args.control, year), _sys(args.treatment, year)
        feas = {
            "control_max_slack": float(sc["slack"].max()),
            "control_max_dump": float(sc["dump"].max()),
            "treatment_max_slack": float(st["slack"].max()),
            "treatment_max_dump": float(st["dump"].max()),
        }
        if max(feas.values()) > 1e-6:
            g4_ok = False
        yr["feasibility"] = feas
        per_year[str(year)] = yr

    out["years"] = per_year

    # ---- width legs: committed construction artifact + ordc_steps.log ----
    steps = {}
    for tag, b in (("control", args.control), ("treatment", args.treatment)):
        p = b / "ordc_steps.log"
        txt = p.read_text() if p.exists() else ""
        steps[tag] = [int(m) for m in re.findall(r"(\d+) ORDC steps", txt)]
    g2c_ok = bool(steps["control"] and steps["control"] == steps["treatment"])
    out["ordc_steps"] = {**steps, "identical": g2c_ok}

    cyears = constr["years"]
    li_widths_same = all(
        cyears[str(y)]["families"][LI30]["widths_identical"] for y in YEARS
    )
    li_req_same = all(
        cyears[str(y)]["families"][LI30]["requirement_identical"] for y in YEARS
    )
    li_pen_same = all(
        cyears[str(y)]["families"][LI30]["penalties_identical"] for y in YEARS
    )
    nyc_price_same = all(
        cyears[str(y)]["families"][n]["reachable_price_identical"]
        for y in YEARS
        for n in NYC_PAIR
    )
    seny_price_changed = all(
        not cyears[str(y)]["families"][SENY]["reachable_price_identical"]
        for y in YEARS
    )
    # G1 / K-E: the construction identity the flag exists to restore.
    seny_identity_off = [
        cyears[str(y)]["families"][SENY]["hours_totalwidth_ne_requirement_off"]
        for y in YEARS
    ]
    seny_identity_on = [
        cyears[str(y)]["families"][SENY]["hours_totalwidth_ne_requirement_on"]
        for y in YEARS
    ]
    g1_ok = all(v == 0 for v in seny_identity_on) and all(
        v > 0 for v in seny_identity_off
    )

    out["gates"] = {
        "G1_span_live_and_identity_restored": {
            "pass": bool(g1_ok),
            "seny_hours_totalwidth_ne_requirement_control": seny_identity_off,
            "seny_hours_totalwidth_ne_requirement_treatment": seny_identity_on,
            "seny_reachable_price_changed": bool(seny_price_changed),
            "source": "construction probe (widths are not in the sidecar)",
        },
        "G2a_scope_requirement_identity": {
            "pass": bool(g2a_ok),
            "claim": "every family's requirement_mw float32-EXACT between arms",
        },
        "G2b_li_no_double_apply": {
            "pass": bool(g2b_ok and li_widths_same and li_req_same and li_pen_same),
            "li_widths_identical": bool(li_widths_same),
            "li_requirement_identical": bool(li_req_same),
            "li_penalties_identical": bool(li_pen_same),
        },
        "G2c_ordc_step_count_unchanged": {"pass": g2c_ok, **steps},
        "G3_lp_row_identity": {"pass": bool(g3_ok)},
        "G4_no_feasibility_damage": {"pass": bool(g4_ok)},
    }
    out["kills"] = {
        "K_A_li_double_apply": {
            "fired": bool(not (li_widths_same and li_req_same and li_pen_same))
        },
        "K_B_frozen_nyc_disturbed": {"fired": bool(not nyc_price_same)},
        "K_C_scope_leak": {"fired": bool(not g2a_ok)},
        "K_D_feasibility_damage": {"fired": bool(not g4_ok)},
        "K_E_identity_not_restored": {"fired": bool(not all(v == 0 for v in seny_identity_on))},
    }
    out["all_gates_pass"] = all(g["pass"] for g in out["gates"].values())
    out["any_kill_fired"] = any(k["fired"] for k in out["kills"].values())

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(out, indent=2))

    for k, v in out["gates"].items():
        print(f"{'PASS' if v['pass'] else 'FAIL'}  {k}")
    for k, v in out["kills"].items():
        print(f"{'FIRED' if v['fired'] else 'ok   '} {k}")
    print(f"\nall_gates_pass={out['all_gates_pass']} any_kill={out['any_kill_fired']}")
    print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
