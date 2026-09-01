"""caiso-233 §B/§C: decompose WHY the ported NEISO depth estimator fails its gates.

Measurement only -- no LP, no solve, no mechanism. Answers three questions the
raw gate table cannot:

  §B1  Are the MEASURED corridor depths themselves year-stable? (If yes, the
       object is measurable and the estimator is what fails.)
  §B2  How much of each derived rung's CV is INHERITED from the firm carve-out
       vs contributed by the measured depth?
  §B3  Is the scarcity rung's construction (p99.9(total) - sum of marginal p98s)
       a difference of large numbers, and is the sum of marginals even a
       coherent simultaneous depth?

Writes results/calibration/_caiso233_import_depth_decomp.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_caiso_import_depths import (  # noqa: E402
    CAP_PCTL,
    SCARCITY_PCTL,
    firm_by_corridor,
)
from derive_caiso_import_tranches import YEARS, corridor_net_import  # noqa: E402

OUT = REPO / "results" / "calibration" / "_caiso233_import_depth_decomp.json"


def cv(vals) -> float:
    v = np.asarray(list(vals), dtype=float)
    m = float(np.nanmean(v))
    return float(np.nanstd(v) / m) if m else float("nan")


def main() -> None:
    net = corridor_net_import()
    rep: dict = {"note": "measurement only; no LP, no solve, no mechanism"}

    flows = {
        y: {c: net.loc[y][c].to_numpy() for c in ("WECC_PNW", "WECC_DSW")}
        for y in YEARS
    }
    for y in YEARS:
        f = flows[y]
        f["TOTAL"] = f["WECC_PNW"] + f["WECC_DSW"]

    # --- B1: are the measured depths year-stable? -------------------------
    pct = {}
    for y in YEARS:
        pct[y] = {}
        for c in ("WECC_PNW", "WECC_DSW", "TOTAL"):
            a = flows[y][c]
            a = a[np.isfinite(a)]
            pct[y][c] = {
                "p50": float(np.percentile(a, 50)),
                "p95": float(np.percentile(a, 95)),
                "p98": float(np.percentile(a, CAP_PCTL)),
                "p99.9": float(np.percentile(a, SCARCITY_PCTL)),
                "max": float(a.max()),
                "frac_negative": float((a < 0).mean()),
            }
    rep["B1_measured_depth"] = {
        "per_year": pct,
        "cv_across_years": {
            c: {
                q: cv(pct[y][c][q] for y in YEARS)
                for q in ("p50", "p95", "p98", "p99.9")
            }
            for c in ("WECC_PNW", "WECC_DSW", "TOTAL")
        },
    }

    # --- B2: carve-out inheritance ----------------------------------------
    firm = {y: firm_by_corridor(y) for y in YEARS}
    b2 = {}
    for c, rung in (("WECC_PNW", "PNW_midC"), ("WECC_DSW", "DSW_CCGT/DSW_CT")):
        depth = [pct[y][c]["p98"] for y in YEARS]
        fm = [firm[y][c] for y in YEARS]
        diff = [d - f for d, f in zip(depth, fm)]
        b2[rung] = {
            "measured_p98": depth,
            "firm_carveout": fm,
            "spot_remainder": diff,
            "cv_measured_p98": cv(depth),
            "cv_firm": cv(fm),
            "cv_remainder": cv(diff),
            "amplification_vs_depth": cv(diff) / cv(depth)
            if cv(depth)
            else float("nan"),
            "depth_delta_23_to_25": depth[-1] - depth[0],
            "firm_delta_23_to_25": fm[-1] - fm[0],
            "codirectional": bool((depth[-1] - depth[0]) * (fm[-1] - fm[0]) > 0),
        }
    rep["B2_carveout_inheritance"] = b2

    # --- B3: scarcity as a difference of large numbers --------------------
    b3 = {}
    for y in YEARS:
        marg = pct[y]["WECC_PNW"]["p98"] + pct[y]["WECC_DSW"]["p98"]
        b3[str(y)] = {
            "sum_of_marginal_p98": marg,
            "p98_of_total": pct[y]["TOTAL"]["p98"],
            "simultaneity_gap": marg - pct[y]["TOTAL"]["p98"],
            "p99.9_of_total": pct[y]["TOTAL"]["p99.9"],
            "scarcity_remainder": pct[y]["TOTAL"]["p99.9"] - marg,
            "remainder_as_frac_of_minuend": (
                (pct[y]["TOTAL"]["p99.9"] - marg) / pct[y]["TOTAL"]["p99.9"]
            ),
        }
    rem = [b3[str(y)]["scarcity_remainder"] for y in YEARS]
    b3["cv_minuend_p99.9_total"] = cv(pct[y]["TOTAL"]["p99.9"] for y in YEARS)
    b3["cv_subtrahend_sum_marginals"] = cv(
        b3[str(y)]["sum_of_marginal_p98"] for y in YEARS
    )
    b3["cv_remainder"] = cv(rem)
    b3["amplification"] = b3["cv_remainder"] / max(
        b3["cv_minuend_p99.9_total"], b3["cv_subtrahend_sum_marginals"]
    )
    _pnw = np.concatenate([flows[y]["WECC_PNW"] for y in YEARS])
    _dsw = np.concatenate([flows[y]["WECC_DSW"] for y in YEARS])
    _m = np.isfinite(_pnw) & np.isfinite(_dsw)
    b3["corr_corridor_flows_pooled"] = float(np.corrcoef(_pnw[_m], _dsw[_m])[0, 1])
    b3["n_hours_pooled"] = int(_m.sum())
    rep["B3_scarcity_difference"] = b3

    # --- C: incumbent ladder vs measured envelope -------------------------
    inc_spot, inc_firm = 8800.0, {2023: 2323.0, 2024: 3371.0, 2025: 3371.0}
    rep["C_incumbent_vs_measured"] = {
        str(y): {
            "incumbent_total_ladder_mw": inc_spot + inc_firm[y],
            "incumbent_spot_mw": inc_spot,
            "measured_p98_total": pct[y]["TOTAL"]["p98"],
            "measured_p99.9_total": pct[y]["TOTAL"]["p99.9"],
            "measured_max_total": pct[y]["TOTAL"]["max"],
            "ladder_over_p99.9": inc_spot + inc_firm[y] - pct[y]["TOTAL"]["p99.9"],
        }
        for y in YEARS
    }

    OUT.write_text(json.dumps(rep, indent=1, default=float))

    print("=== B1  measured corridor depth, CV across 2023-2025 ===")
    for c in ("WECC_PNW", "WECC_DSW", "TOTAL"):
        d = rep["B1_measured_depth"]["cv_across_years"][c]
        print(
            f"  {c:<9} p50 {d['p50']:.3f}   p95 {d['p95']:.3f}   "
            f"p98 {d['p98']:.3f}   p99.9 {d['p99.9']:.3f}"
        )
    print("  negative-hour share (rule-14 caveat check, p98 is the HIGH tail):")
    for c in ("WECC_PNW", "WECC_DSW", "TOTAL"):
        fr = [pct[y][c]["frac_negative"] for y in YEARS]
        print(f"    {c:<9} " + "  ".join(f"{v:.1%}" for v in fr))

    print("\n=== B2  where each rung's instability comes from ===")
    for rung, d in b2.items():
        print(
            f"  {rung:<20} CV(measured p98)={d['cv_measured_p98']:.3f}  "
            f"CV(firm carve-out)={d['cv_firm']:.3f}  ->  CV(rung)={d['cv_remainder']:.3f}"
            f"   [{'co-directional, CANCELS' if d['codirectional'] else 'opposed, AMPLIFIES'}]"
        )

    print("\n=== B3  the scarcity rung is a difference of large numbers ===")
    for y in YEARS:
        d = b3[str(y)]
        print(
            f"  {y}: p99.9(total) {d['p99.9_of_total']:>8,.0f} - sum-of-marginal-p98 "
            f"{d['sum_of_marginal_p98']:>8,.0f} = {d['scarcity_remainder']:>7,.0f} MW "
            f"({d['remainder_as_frac_of_minuend']:.1%} of the minuend)"
        )
    print(
        f"  CV(minuend)={b3['cv_minuend_p99.9_total']:.3f}  "
        f"CV(subtrahend)={b3['cv_subtrahend_sum_marginals']:.3f}  "
        f"CV(remainder)={b3['cv_remainder']:.3f}  -> amplification {b3['amplification']:.1f}x"
    )
    print(
        "  simultaneity gap (sum-of-marginal-p98 MINUS p98-of-total): "
        + "  ".join(f"{y}={b3[str(y)]['simultaneity_gap']:,.0f}" for y in YEARS)
        + f"   corridor flow corr = {b3['corr_corridor_flows_pooled']:+.3f}"
    )

    print("\n=== C  incumbent ladder depth vs the measured envelope ===")
    for y in YEARS:
        d = rep["C_incumbent_vs_measured"][str(y)]
        print(
            f"  {y}: ladder {d['incumbent_total_ladder_mw']:>7,.0f} MW  vs  measured "
            f"p98 {d['measured_p98_total']:>7,.0f} / p99.9 {d['measured_p99.9_total']:>7,.0f} "
            f"/ max {d['measured_max_total']:>7,.0f}   (ladder - p99.9 = "
            f"{d['ladder_over_p99.9']:+,.0f})"
        )
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
