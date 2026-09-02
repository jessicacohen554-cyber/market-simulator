"""Derive the CAISO import SPOT rung capacities from the measured TOTAL envelope.

The SUCCESSOR estimator specified by ``FINDING-caiso233-import-depth-derivation
-2026-09-01.md`` §F, pre-registered by ``PRECOMMIT-caiso234-import-total-envelope
-2026-09-02.md`` **before this script was executed**. It closes the same object
that script's predecessor failed on: the last uncited limb of
``interchange.spec.IMPORT_TRANCHES["CAISO"]`` -- the four SPOT rung depths that
``scripts/probes/_caiso186os_dof_repair.py`` labels ``RESIDUAL (static, no cited
primary source)`` --

    PNW_midC 1,800 / DSW_CCGT 1,800 / DSW_CT 2,200 / WECC_scarcity 3,000
    = 8,800 MW of bare literals, invariant across 2023-2025.

(``PNW_hydro_base`` and ``DSW_solar_PV``, the ``CAISO_FIRM_IMPORT_TRANCHES`` pair,
are MEASURED per-year -- DMM RA import capacity x published MIC corridor share --
and are held FIXED. Rule 1 [R-STRUCT]: a grounded quantity is never re-opened to
move a residual.)

WHY THIS IS THE SECOND ESTIMATOR, AND WHAT THAT COSTS
-----------------------------------------------------
``scripts/data/derive_caiso_import_depths.py`` (caiso-233) ported the NEISO
estimator directly -- per-corridor p98 with the MIC firm block carved out of each
corridor, scarcity as p99.9-minus-summed-rungs -- and FAILED both pre-registered
gates (per-rung CV 0.253 / 0.550 vs a 0.20 bar; LOYO 40.1 / 491.7 / 57.9 % vs a
25 % bar). Its stop condition fired and no LP was built. That estimator is
DO-NOT-REDO (FINDING-caiso233 §F4).

Its FINDING decomposed the failure and specified this successor BEFORE any of the
successor's numbers existed (§F items 1-3). Two facts must travel with every use
of this script:

  * The per-year TOTAL percentiles were already published in caiso-233's
    committed ``_caiso233_import_depth_decomp.json``, so the YEAR-STABILITY gate
    below is FORESEEN and carries little evidential weight. The load-bearing gate
    is LOYO, which is computed on POOLED two-year samples and is therefore not a
    function of anything already committed.
  * The gated object MOVED after a failure (per-rung -> total). That is a weaker
    test. ``--report`` publishes the stricter per-rung diagnostics anyway, at full
    magnitude, so a reader may apply caiso-233's own bar to this ladder.

The budget is TWO estimators. There is no third (PRECOMMIT §0.6).

METHODOLOGY -- gate the TOTAL, place the rungs by convention
------------------------------------------------------------
GATED OBJECT (PRECOMMIT §2) -- two direct statistics of the TOTAL corridor
net-import distribution, with NO firm carve-out anywhere inside them::

    routine_total     = p98  ( TOTAL net import )
    scarcity_interval = p99.9( TOTAL ) - p98( TOTAL )
    ladder_total      = routine_total + scarcity_interval  =  p99.9( TOTAL )

The two construction changes vs caiso-233, and why each is there:

  1. NO PER-CORRIDOR FIRM CARVE-OUT (§F1). The DMM RA x MIC firm measurement moved
     1,072 -> 1,566 MW (PNW) and 1,251 -> 1,805 MW (DSW) across three years, a CV
     of ~0.16 -- FOUR TIMES the measured depth's own 0.042 -- and its 2025 entry
     is a carried-forward 2024 figure (a declared open data gap). The NEISO
     precedent carves out Highgate's published converter rating, a CONSTANT;
     CAISO's analogue is a moving annual measurement with its own error. Letting
     the firm block sit INSIDE the derived total keeps that error out of the
     gated statistic.
  2. SCARCITY IS AN INTERVAL, NEVER A RESIDUE (§F2). The residue form
     p99.9(total) - sum(marginal p98) is a 2.0-10.3 % remainder of a ~9 GW
     minuend: CV 0.056 and 0.025 inputs produce a CV 0.547 output, a 9.8x
     amplification. It also double-counts the simultaneity gap, since the sum of
     marginal p98s exceeds the p98 of the TOTAL by 969 / 1,126 / 514 MW at a
     pooled hourly corridor correlation of r = +0.484.

PLACEMENT CONVENTION (PRECOMMIT §4) -- ZERO free parameters, fixed before
execution, and NOT the gated object::

    w_c            = p98_pooled(c) / sum_c p98_pooled(c)      # pro-rata weights
    routine_c      = routine_total * w_c
    spot_routine_c = max(0, routine_c - firm_c)               # firm held fixed
    rung           = spot_routine_c / n_spot_rungs(c)         # equal MW
    WECC_scarcity  = scarcity_interval                        # on its own node

The pro-rata weights are the reconciliation of the two MARGINAL corridor depths to
the coherent TOTAL -- i.e. the direct fix for the simultaneity gap named above,
not a chosen allocation. The equal-MW within-corridor split is the NYISO/NEISO
rung convention (``derive_nyiso_import_tranches.py``; ``NYISO_CT_base``/``_peak``):
the split point is fixed by the convention, never chosen. Capacities round to
5 MW (``_round_cap``). PRICES ARE UNCHANGED -- this is a capacity-limb derivation
only; the price Q-Q route is DO-NOT-REDO (failed LOYO at 30.5 %, caiso-86b).

The derivation is POOLED 2023-2025 -> ONE static ladder, the convention the
incumbent entry already uses; the FIRM rows of every by-year entry keep their
measured per-year values.

Why EIA-930 is admissible here, though it was rejected for the FIRM limb
------------------------------------------------------------------------
The ``IMPORT_TRANCHES`` provenance block records a boundary caveat (rule 14):
"EIA-930 net corridor flows cannot size a gross firm block (their low percentiles
are negative: midday solar exports net against firm imports)". That objection is
about the LOW tail and does not transfer to a limb built entirely from the HIGH
tail. caiso-233 §C1a made it checkable rather than assumed: negative-hour shares
are 51/38/31 % (PNW), 5.8/5.4/4.9 % (DSW), 14/11/9 % (total), while every p98 and
p99.9 this script uses is strongly positive. ``--report`` re-prints the signs.

Estimation-stage honesty gates (run BEFORE any solve)
-----------------------------------------------------
Held to the SAME bar the price limb was held to and failed
(``derive_caiso_import_tranches.py``: ``CV_MAX`` 0.20 / ``LOYO_MAX`` 0.25, both
imported from that file so this session cannot set them):

  * YEAR-STABILITY: CV across 2023-2025 of EACH gated component <= CV_MAX.
    (FORESEEN -- see above.)
  * LOYO: derive both components on the pooled other two years, predict the
    held-out year's own values; worst relative error <= LOYO_MAX. (UNSEEN.)

If either FAILS the script prints FAIL, the caller files the FINDING and does NOT
solve, and the DOF escalates to the owner as a standing item. Softening the bar,
re-scoping the gated object to whichever component passes, or reaching for a third
estimator would each be a rule-13 [R-MEASURED] act.

Rule 23 [R-FROZEN-DERIVE]: re-derive ONLY when the EIA-930 CISO interchange
extract extends -- never because a backcast residual moved.

Usage:
    python scripts/data/derive_caiso_import_total_envelope.py            # gates
    python scripts/data/derive_caiso_import_total_envelope.py --report   # + §5
    python scripts/data/derive_caiso_import_total_envelope.py --json PATH
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_caiso_import_depths import (  # noqa: E402
    CAP_PCTL,
    ROUND_MW,
    SCARCITY_PCTL,
    SCARCITY_RUNG,
    _round_cap,
    firm_by_corridor,
)
from derive_caiso_import_tranches import (  # noqa: E402
    CV_MAX,
    LOYO_MAX,
    YEARS,
    corridor_net_import,
)

from market_sim.model.interchange.caiso import (  # noqa: E402
    CAISO_FIRM_IMPORT_TRANCHES,
)
from market_sim.model.interchange.spec import IMPORT_TRANCHES_BY_YEAR  # noqa: E402

CORRIDORS = ("WECC_PNW", "WECC_DSW")

# Which model rungs are the SPOT (derived) limb of each corridor, cheapest-first.
# Identical to derive_caiso_import_depths.CORRIDOR_SPOT_RUNGS -- the ladder's
# rung inventory and node placement are unchanged; only the DEPTHS are derived.
CORRIDOR_SPOT_RUNGS = {
    "WECC_PNW": ("PNW_midC",),
    "WECC_DSW": ("DSW_CCGT", "DSW_CT"),
}

# The two components of the GATED object (PRECOMMIT §2). Named here so the gate
# loop, the LOYO loop and the JSON all iterate the same fixed pair.
GATED = ("routine_total", "scarcity_interval")


def corridor_total(net, years) -> dict[str, np.ndarray]:
    """Return {corridor: flow, 'TOTAL': flow} pooled over ``years`` (finite only)."""
    out: dict[str, np.ndarray] = {}
    stacked = None
    for c in CORRIDORS:
        flow = np.concatenate([net.loc[y][c].to_numpy() for y in years])
        out[c] = flow
        stacked = flow if stacked is None else stacked + flow
    out["TOTAL"] = stacked
    return {k: v[np.isfinite(v)] for k, v in out.items()}


def derive_envelope(net, years) -> dict[str, float]:
    """Derive the GATED total-envelope components from the pooled ``years`` sample.

    Returns ``{"routine_total", "scarcity_interval", "ladder_total"}`` in MW. No
    firm block and no per-corridor carve-out enters any of these (PRECOMMIT §2).
    """
    flows = corridor_total(net, list(years))
    routine = float(np.percentile(flows["TOTAL"], CAP_PCTL))
    emergency = float(np.percentile(flows["TOTAL"], SCARCITY_PCTL))
    return {
        "routine_total": routine,
        "scarcity_interval": emergency - routine,
        "ladder_total": emergency,
    }


def place_rungs(net, years) -> tuple[dict[str, float], dict[str, float]]:
    """Place the SPOT rungs inside the derived total by the §4 convention.

    ZERO free parameters: pro-rata corridor weights off the same measured p98s,
    the fixed per-year MIC firm blocks held out of the spot limb, and an equal-MW
    within-corridor split. Returns ``(rungs_mw, diagnostics)``.
    """
    years = list(years)
    env = derive_envelope(net, years)
    flows = corridor_total(net, years)

    marginal = {c: float(np.percentile(flows[c], CAP_PCTL)) for c in CORRIDORS}
    marginal_sum = sum(marginal.values())
    weights = {c: marginal[c] / marginal_sum for c in CORRIDORS}
    firm = {
        c: float(np.mean([firm_by_corridor(y)[c] for y in years])) for c in CORRIDORS
    }

    rungs: dict[str, float] = {}
    diag: dict[str, float] = dict(env)
    for c in CORRIDORS:
        routine_c = env["routine_total"] * weights[c]
        spot_c = max(0.0, routine_c - firm[c])
        share = _round_cap(spot_c / len(CORRIDOR_SPOT_RUNGS[c]))
        for name in CORRIDOR_SPOT_RUNGS[c]:
            rungs[name] = share
        diag[f"{c}_p{CAP_PCTL:g}_marginal"] = marginal[c]
        diag[f"{c}_weight"] = weights[c]
        diag[f"{c}_routine_alloc"] = routine_c
        diag[f"{c}_firm"] = firm[c]
        diag[f"{c}_spot_routine"] = spot_c
    diag["marginal_p98_sum"] = marginal_sum
    diag["simultaneity_gap"] = marginal_sum - env["routine_total"]
    rungs[SCARCITY_RUNG] = _round_cap(max(0.0, env["scarcity_interval"]))
    return rungs, diag


def cv(vals) -> float:
    """Coefficient of variation of a small sample (population sd / mean)."""
    v = np.asarray(list(vals), dtype=float)
    m = float(np.nanmean(v))
    return float(np.nanstd(v) / m) if m else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--report", action="store_true", help="print the §5 ungated diagnostics"
    )
    ap.add_argument("--json", type=Path, help="write the derived ladder to PATH")
    args = ap.parse_args()

    net = corridor_net_import()
    names = [
        *CORRIDOR_SPOT_RUNGS["WECC_PNW"],
        *CORRIDOR_SPOT_RUNGS["WECC_DSW"],
        SCARCITY_RUNG,
    ]
    incumbent = {
        n: c
        for n, c, _ in IMPORT_TRANCHES_BY_YEAR["CAISO"][2025]
        if n not in CAISO_FIRM_IMPORT_TRANCHES
    }

    per_year_env = {y: derive_envelope(net, [y]) for y in YEARS}
    pooled_env = derive_envelope(net, YEARS)
    per_year_rungs = {}
    per_year_diag = {}
    for y in YEARS:
        per_year_rungs[y], per_year_diag[y] = place_rungs(net, [y])
    pooled_rungs, pooled_diag = place_rungs(net, YEARS)

    # --- GATE 1: year-stability of the GATED components ---------------------
    print("=== caiso-234: CAISO import TOTAL-envelope derivation ===")
    print(
        f"    routine = p{CAP_PCTL:g}(TOTAL); scarcity = p{SCARCITY_PCTL:g} - p{CAP_PCTL:g}"
    )
    print("\n--- GATED OBJECT: the TOTAL import envelope (MW) ---")
    print(
        "component".ljust(20)
        + "".join(f"{y:>10}" for y in YEARS)
        + "    pooled      CV   gate"
    )
    stability_ok = True
    cvs = {}
    for comp in (*GATED, "ladder_total"):
        vals = [per_year_env[y][comp] for y in YEARS]
        c = cv(vals)
        cvs[comp] = c
        gated = comp in GATED
        ok = bool(np.isfinite(c) and c <= CV_MAX)
        if gated:
            stability_ok = stability_ok and ok
        mark = ("ok" if ok else "FAIL") if gated else "(reported)"
        row = comp.ljust(20) + "".join(f"{v:>10,.0f}" for v in vals)
        print(f"{row}{pooled_env[comp]:>10,.0f}   {c:>5.3f}   {mark}")

    # --- GATE 2: LOYO on the GATED components -------------------------------
    print(
        f"\n--- LOYO (derive on 2 years pooled, predict the held-out year; bar {LOYO_MAX:.0%}) ---"
    )
    loyo_ok = True
    loyo = {}
    for held in YEARS:
        train = [y for y in YEARS if y != held]
        pred = derive_envelope(net, train)
        act = per_year_env[held]
        errs = {}
        for comp in GATED:
            denom = abs(act[comp]) if act[comp] else float("nan")
            errs[comp] = abs(pred[comp] - act[comp]) / denom if denom else float("nan")
        worst_comp = max(errs, key=lambda k: np.nan_to_num(errs[k], nan=-1.0))
        worst = errs[worst_comp]
        ok = bool(np.isfinite(worst) and worst <= LOYO_MAX)
        loyo_ok = loyo_ok and ok
        loyo[held] = {"errors": errs, "worst_component": worst_comp, "worst": worst}
        detail = "  ".join(f"{c}={errs[c]:.1%}" for c in GATED)
        print(
            f"  hold {held}: worst {worst:>6.1%} ({worst_comp})   {'ok' if ok else 'FAIL'}"
        )
        print(f"            {detail}")

    verdict = "PASS" if (stability_ok and loyo_ok) else "FAIL"

    # --- The delivered ladder (placement convention, §4) --------------------
    print("\n--- DELIVERED static SPOT ladder (pooled 2023-2025, §4 placement) ---")
    print("rung".ljust(16) + "  derived  incumbent      delta")
    for nm in names:
        d = pooled_rungs[nm]
        i = incumbent[nm]
        print(f"{nm.ljust(16)}{d:>9,.0f}{i:>11,.0f}{d - i:>+11,.0f}")
    dt, it = sum(pooled_rungs.values()), sum(incumbent.values())
    print(f"{'TOTAL SPOT'.ljust(16)}{dt:>9,.0f}{it:>11,.0f}{dt - it:>+11,.0f}")

    # --- §5: reported at full magnitude, NOT gated --------------------------
    per_rung_cv = {nm: cv([per_year_rungs[y][nm] for y in YEARS]) for nm in names}
    per_rung_loyo = {}
    for held in YEARS:
        train = [y for y in YEARS if y != held]
        pred, _ = place_rungs(net, train)
        act = per_year_rungs[held]
        errs = {}
        for nm in names:
            denom = act[nm] if act[nm] else float("nan")
            errs[nm] = abs(pred[nm] - act[nm]) / denom if denom else float("nan")
        worst_nm = max(errs, key=lambda k: np.nan_to_num(errs[k], nan=-1.0))
        per_rung_loyo[held] = {
            "errors": errs,
            "worst_rung": worst_nm,
            "worst": errs[worst_nm],
        }

    if args.report:
        print(
            "\n=== §5 REPORTED, NOT GATED (caiso-233's own per-rung bar, applied here) ==="
        )
        print(
            "rung".ljust(16) + "".join(f"{y:>10}" for y in YEARS) + "    pooled      CV"
        )
        for nm in names:
            vals = [per_year_rungs[y][nm] for y in YEARS]
            row = nm.ljust(16) + "".join(f"{v:>10,.0f}" for v in vals)
            print(f"{row}{pooled_rungs[nm]:>10,.0f}   {per_rung_cv[nm]:>5.3f}")
        for held in YEARS:
            r = per_rung_loyo[held]
            detail = "  ".join(f"{nm}={r['errors'][nm]:.1%}" for nm in names)
            print(
                f"  per-rung LOYO hold {held}: worst {r['worst']:.1%} ({r['worst_rung']})"
            )
            print(f"            {detail}")
        print("\n=== corridor weights, firm blocks and the simultaneity gap ===")
        for y in (*YEARS, "pooled"):
            d = pooled_diag if y == "pooled" else per_year_diag[y]
            keys = [k for k in d if k.endswith(("_weight", "_firm", "_spot_routine"))]
            print(f"  {y}: " + "  ".join(f"{k}={d[k]:,.3f}" for k in sorted(keys)))
            print(
                f"        marginal_p98_sum={d['marginal_p98_sum']:,.0f}  "
                f"simultaneity_gap={d['simultaneity_gap']:,.0f}"
            )
        print(
            "\n=== rule-14 EIA-930 sign check (every gated percentile must be > 0) ==="
        )
        for y in YEARS:
            flows = corridor_total(net, [y])
            bits = []
            for k in (*CORRIDORS, "TOTAL"):
                a = flows[k]
                bits.append(
                    f"{k}: p98={np.percentile(a, CAP_PCTL):,.0f} "
                    f"p99.9={np.percentile(a, SCARCITY_PCTL):,.0f} "
                    f"neg={100 * (a < 0).mean():.1f}%"
                )
            print(f"  {y}: " + " | ".join(bits))

    print(
        f"\n=== GATES: year-stability {'ok' if stability_ok else 'FAIL'} | "
        f"LOYO {'ok' if loyo_ok else 'FAIL'} => {verdict} ==="
    )
    if verdict == "FAIL":
        print(
            "Do NOT solve. File the FINDING and escalate the DOF to the owner as a\n"
            "standing item. The estimator budget is SPENT (PRECOMMIT §0.6): do not\n"
            "soften a bar, re-scope the gated object, or try a third estimator."
        )

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "session": "caiso-234",
                    "precommit": (
                        "results/calibration/"
                        "PRECOMMIT-caiso234-import-total-envelope-2026-09-02.md"
                    ),
                    "method": {
                        "gated_object": list(GATED),
                        "cap_pctl": CAP_PCTL,
                        "scarcity_pctl": SCARCITY_PCTL,
                        "cv_max": CV_MAX,
                        "loyo_max": LOYO_MAX,
                        "round_mw": ROUND_MW,
                        "specified_by": (
                            "FINDING-caiso233-import-depth-derivation-2026-09-01.md §F"
                        ),
                        "placement": (
                            "pro-rata corridor weights on p98 share; firm held fixed; "
                            "equal-MW within-corridor split; scarcity = p99.9 - p98"
                        ),
                    },
                    "gated": {
                        "per_year": {str(y): per_year_env[y] for y in YEARS},
                        "pooled": pooled_env,
                        "cv": cvs,
                        "year_stability": stability_ok,
                        "loyo": {
                            str(k): {
                                "worst": v["worst"],
                                "worst_component": v["worst_component"],
                                "errors": v["errors"],
                            }
                            for k, v in loyo.items()
                        },
                        "loyo_ok": loyo_ok,
                        "verdict": verdict,
                    },
                    "delivered": {
                        "pooled_rungs": pooled_rungs,
                        "incumbent_2025": incumbent,
                        "per_year_rungs": {str(y): per_year_rungs[y] for y in YEARS},
                    },
                    "reported_not_gated": {
                        "per_rung_cv": per_rung_cv,
                        "per_rung_loyo": {
                            str(k): {
                                "worst": v["worst"],
                                "worst_rung": v["worst_rung"],
                                "errors": v["errors"],
                            }
                            for k, v in per_rung_loyo.items()
                        },
                    },
                    "diagnostics": {
                        **{str(y): per_year_diag[y] for y in YEARS},
                        "pooled": pooled_diag,
                    },
                },
                indent=1,
                default=float,
            )
        )
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
