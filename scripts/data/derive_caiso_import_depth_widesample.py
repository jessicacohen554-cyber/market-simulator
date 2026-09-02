"""Re-run the caiso-234 TOTAL-envelope estimator on the 2019-2025 measured sample.

caiso-235. **The estimator is NOT new.** This script executes
``scripts/data/derive_caiso_import_total_envelope.py`` -- the caiso-234
construction -- by IMPORTING its functions, with exactly ONE pre-registered
change: the pooled sample is widened from 2023-2025 to **2019-2025**. Gated
object, percentile constants, gate thresholds and the zero-DOF placement
convention are all unchanged and none is settable here.

Pre-registration: ``results/calibration/
PRECOMMIT-caiso235-import-depth-widesample-2026-09-02.md``, **pushed to origin
before this script was executed**.

THE OBJECT -- CAISO's last uncited DOF
--------------------------------------
The four ``interchange.spec.IMPORT_TRANCHES["CAISO"]`` SPOT rung depths, which
``scripts/probes/_caiso186os_dof_repair.py`` labels ``RESIDUAL (static, no cited
primary source)``::

    PNW_midC 1,800 / DSW_CCGT 1,800 / DSW_CT 2,200 / WECC_scarcity 3,000
    = 8,800 MW of bare literals, invariant across 2023-2025.

``PNW_hydro_base`` and ``DSW_solar_PV`` (the ``CAISO_FIRM_IMPORT_TRANCHES`` pair,
DMM RA import capacity x published MIC corridor share) are MEASURED per-year and
are held FIXED. Rule 1 [R-STRUCT]: a grounded quantity is never re-opened to move
a residual.

WHY A THIRD EXECUTION EXISTS, AND WHY IT IS NOT A THIRD ESTIMATOR
-----------------------------------------------------------------
Two pre-registered estimators have failed on the same object:

  * caiso-233 -- the NEISO port (per-corridor p98, firm carved out of each
    corridor, scarcity as a residue): CV 0.550, LOYO 491.7 %. DO-NOT-REDO.
  * caiso-234 -- the TOTAL envelope (this construction), on 2023-2025:
    G-STABILITY ok (CV 0.058 / 0.120) but **G-LOYO FAIL at 34.2 %** against a
    25 % bar, on the scarcity interval with 2024 held out.

FINDING-caiso234 §B diagnosed that failure as **SAMPLE LENGTH, not construction**:
``p99.9`` of an 8,759-hour year is fixed by its **9 highest hours**, and the
(p98, p99.9] band by 167 -- so the rung is a ~9-observation order statistic and
three years supply three of them. 2024's p98 sits within 0.9 % of 2023's and its
annual max is HIGHER, yet its p99.9 is 518 MW lower: the extreme tail's SHAPE
moves, not its level. With n = 3 a single atypical year is a third of the sample.

The owner charter for caiso-235 rules that a wider-sample re-run of the SAME
estimator is **not** the forbidden third construction (the two-estimator budget
was spent on two structurally DIFFERENT constructions), and that deriving over
2019-2025 EIA-930 seam flow is **data prep, not a holdout spend** (owner
clarification 2026-08-06: "WHAT IS HELD OUT IS THE SCORE, NEVER THE DATA ... Data
intake needs NO per-ISO/per-window authorization and no marker"). **If any part of
the construction changed, the budget rule would re-apply and this script would not
exist.** It does not: §2's gated object is computed by calling caiso-234's own
``derive_envelope``.

On seven years the p99.9 band rests on ~61 hours rather than 9, and LOYO gains
four folds (7 instead of 3), each trained on six years instead of two.

THE HOLDOUT LINE
----------------
No year outside 2023-2025 is SOLVED, SCORED or REGISTERED here, and **no model
output and no measured actual** from any such year is read -- EIA-930 corridor
net-flow percentiles only. **2026 is EXCLUDED**: the committed extract runs
2018-12-31 to 2026-06-30, and H1-2026 is LOCKED-TEST tier inside the active
holdout freeze's scope. The 2018 tail (88 stamps, a timezone artifact of the
2019-01-01 boundary) falls outside the programme's 2019-2025 working span and is
excluded by the same year filter.

GATED OBJECT (PRECOMMIT §2, unchanged -- imported, not re-implemented)
----------------------------------------------------------------------
::

    routine_total     = p98  ( TOTAL net import )
    scarcity_interval = p99.9( TOTAL ) - p98( TOTAL )
    ladder_total      = routine_total + scarcity_interval  =  p99.9( TOTAL )

No firm carve-out enters either component -- which is exactly why the GATES run
cleanly on seven years: the gated object has no dependence on any per-year
quantity unavailable before 2023.

PLACEMENT (PRECOMMIT §4, unchanged) AND THE ONE PRE-REGISTERED FORK
--------------------------------------------------------------------
Placement is the caiso-234 convention verbatim: pro-rata corridor weights on p98
share, firm rungs held FIXED, equal-MW within-corridor split, scarcity on its
incumbent PALOVRDE node, 5 MW rounding, prices untouched.

The fork the charter required to be decided in advance: the placement step
subtracts a per-year measured MIC firm block, but ``IMPORT_TRANCHES_BY_YEAR``
holds only 2023/2024/2025. **Option (a) was pre-registered and is implemented:**
``firm_c`` is the mean of the committed measured MIC blocks over
``FIRM_REFERENCE_YEARS = (2023, 2024, 2025)`` -- the same constant in every fold
and every per-year diagnostic, never a function of the sample years. Reasoning
(PRECOMMIT §4-FORK): extending the DMM RA x MIC intake back to 2019 would change
``firm_c``, i.e. re-open the GROUNDED half of the ladder to absorb a wider flow
sample -- rule 1 [R-STRUCT], and forbidden by the charter by name. The firm block
is also a different object with a different vintage: an annual CAISO regulatory
determination, not telemetry published on one basis for every year.

``--self-check`` runs the pre-registered FORK-CHECK: on the 2023-2025 sample this
placement must reproduce caiso-234's delivered pooled ladder EXACTLY (PNW_midC
1,065 / DSW_CCGT 2,100 / DSW_CT 2,100 / WECC_scarcity 1,795 = 7,060 MW), by
calling caiso-234's own ``place_rungs`` and diffing. If it does not, the fork is
not the neutral re-expression claimed and the session stops there.

HONESTY GATES (unchanged constants; NOT settable by this session)
------------------------------------------------------------------
Imported from ``derive_caiso_import_tranches.py`` (``CV_MAX`` 0.20 / ``LOYO_MAX``
0.25) -- the same bar the price limb was held to and failed at 30.5 %:

  * G-STABILITY: CV across the SEVEN years of EACH gated component <= 0.20.
    (Partly foreseen -- three of seven per-year values are already committed in
    ``_caiso234_import_total_envelope.json``; four are not.)
  * G-LOYO: derive on the pooled other SIX years, predict the held-out year;
    worst relative error <= 0.25 over SEVEN folds. (Unseen -- load-bearing.)

NEAR-MISS RULE (PRECOMMIT §3.1, pre-registered): a worst fold between 25 % and
30 % is a **FAIL**, not "essentially at the bar". Likewise a CV in (0.20, 0.25].

If either gate fails the caller files the FINDING and does NOT solve. Per
PRECOMMIT §6 that outcome is **TERMINAL**: seven years of measured seam flow is
the whole record, so a failure closes the object from DATA rather than from
effort, and the DOF returns to the owner as permanently declared. Do not soften a
bar, re-scope the gated object, admit whichever component passes, fall back to a
residual-tuned depth, or propose a further widening.

Rule 23 [R-FROZEN-DERIVE]: re-derive ONLY when the EIA-930 CISO interchange
extract extends -- never because a backcast residual moved.

Usage:
    python scripts/data/derive_caiso_import_depth_widesample.py
    python scripts/data/derive_caiso_import_depth_widesample.py --report
    python scripts/data/derive_caiso_import_depth_widesample.py --self-check
    python scripts/data/derive_caiso_import_depth_widesample.py --json PATH
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
from derive_caiso_import_total_envelope import (  # noqa: E402
    CORRIDORS,
    CORRIDOR_SPOT_RUNGS,
    GATED,
    corridor_total,
    cv,
    derive_envelope,
    place_rungs,
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

# THE ONE CHANGE (PRECOMMIT §2): the pooled sample. The programme's working span
# is 2019-2025 (CLAUDE.md rule 22); 2026 is LOCKED-TEST tier and excluded.
YEARS_WIDE: tuple[int, ...] = (2019, 2020, 2021, 2022, 2023, 2024, 2025)

# PRECOMMIT §4-FORK option (a): the placement's firm carve-out is the mean of the
# committed measured MIC blocks over these years, held CONSTANT across every
# sample year and every LOYO fold. IMPORT_TRANCHES_BY_YEAR["CAISO"] holds only
# these three, and extending that intake would re-open a GROUNDED rung to absorb
# a wider flow sample (rule 1 [R-STRUCT]).
FIRM_REFERENCE_YEARS: tuple[int, ...] = YEARS

# The caiso-234 delivered pooled ladder (FINDING-caiso234 §D), reproduced by the
# --self-check FORK-CHECK on the 2023-2025 sample.
CAISO234_POOLED_LADDER = {
    "PNW_midC": 1065.0,
    "DSW_CCGT": 2100.0,
    "DSW_CT": 2100.0,
    SCARCITY_RUNG: 1795.0,
}


def firm_reference() -> dict[str, float]:
    """The FIXED per-corridor MIC firm block used by the placement (§4-FORK (a)).

    The mean of the committed measured DMM RA x MIC blocks over
    :data:`FIRM_REFERENCE_YEARS`. Constant across sample years and LOYO folds --
    it is a separately-grounded quantity with its own vintage, never re-derived
    to fit a wider flow sample.
    """
    return {
        c: float(np.mean([firm_by_corridor(y)[c] for y in FIRM_REFERENCE_YEARS]))
        for c in CORRIDORS
    }


def place_rungs_wide(net, years) -> tuple[dict[str, float], dict[str, float]]:
    """Place the SPOT rungs inside the derived total by the §4 convention.

    Identical to :func:`derive_caiso_import_total_envelope.place_rungs` except
    that ``firm_c`` comes from :func:`firm_reference` (constant) rather than from
    the sample years -- the single pre-registered §4-FORK change, needed because
    the wider sample reaches years with no committed MIC block. Still ZERO free
    parameters. Returns ``(rungs_mw, diagnostics)``.
    """
    years = list(years)
    env = derive_envelope(net, years)
    flows = corridor_total(net, years)

    marginal = {c: float(np.percentile(flows[c], CAP_PCTL)) for c in CORRIDORS}
    marginal_sum = sum(marginal.values())
    weights = {c: marginal[c] / marginal_sum for c in CORRIDORS}
    firm = firm_reference()

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


def fork_check(net) -> tuple[bool, dict[str, dict[str, float]]]:
    """PRECOMMIT §4-FORK-CHECK: the fork must be neutral on the 2023-2025 sample.

    Runs caiso-234's OWN :func:`place_rungs` and this module's
    :func:`place_rungs_wide` on the same three-year sample and diffs them against
    each other and against the committed caiso-234 ladder. Any difference means
    the fork is not the neutral re-expression the PRECOMMIT claims.
    """
    ref, _ = place_rungs(net, YEARS)
    mine, _ = place_rungs_wide(net, YEARS)
    rows = {
        nm: {
            "caiso234_committed": CAISO234_POOLED_LADDER[nm],
            "caiso234_replayed": ref[nm],
            "caiso235_fork_a": mine[nm],
        }
        for nm in CAISO234_POOLED_LADDER
    }
    ok = all(
        r["caiso234_replayed"] == r["caiso235_fork_a"] == r["caiso234_committed"]
        for r in rows.values()
    )
    return ok, rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--report", action="store_true", help="print the §5 ungated diagnostics"
    )
    ap.add_argument(
        "--self-check",
        action="store_true",
        help="run the §4-FORK-CHECK against caiso-234 and exit",
    )
    ap.add_argument("--json", type=Path, help="write the derived ladder to PATH")
    args = ap.parse_args()

    net = corridor_net_import(YEARS_WIDE)
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

    # --- PRECOMMIT §4-FORK-CHECK (always run; it is cheap and load-bearing) ---
    fork_ok, fork_rows = fork_check(net)
    print("=== caiso-235: caiso-234 estimator, sample widened to 2019-2025 ===")
    print(
        f"    routine = p{CAP_PCTL:g}(TOTAL); scarcity = p{SCARCITY_PCTL:g} - p{CAP_PCTL:g}"
        f"   |   sample {YEARS_WIDE[0]}-{YEARS_WIDE[-1]} ({len(YEARS_WIDE)} years)"
    )
    print(
        "\n--- §4-FORK-CHECK: the firm-reference fork must be NEUTRAL on 2023-2025 ---"
    )
    print("rung".ljust(16) + " caiso234_cmt  caiso234_rpl  caiso235_fork")
    for nm in names:
        r = fork_rows[nm]
        print(
            f"{nm.ljust(16)}{r['caiso234_committed']:>13,.0f}"
            f"{r['caiso234_replayed']:>14,.0f}{r['caiso235_fork_a']:>15,.0f}"
        )
    print(f"  FORK-CHECK: {'ok' if fork_ok else 'MISMATCH'}")
    if not fork_ok:
        print(
            "\nSTOP. The §4-FORK is not the neutral re-expression the PRECOMMIT\n"
            "claims. Do not gate, do not place, do not solve -- report this."
        )
        sys.exit(1)
    if args.self_check:
        return

    per_year_env = {y: derive_envelope(net, [y]) for y in YEARS_WIDE}
    pooled_env = derive_envelope(net, YEARS_WIDE)
    per_year_rungs = {}
    per_year_diag = {}
    for y in YEARS_WIDE:
        per_year_rungs[y], per_year_diag[y] = place_rungs_wide(net, [y])
    pooled_rungs, pooled_diag = place_rungs_wide(net, YEARS_WIDE)

    # --- GATE 1: year-stability of the GATED components ---------------------
    print("\n--- GATED OBJECT: the TOTAL import envelope (MW) ---")
    print(
        "component".ljust(18)
        + "".join(f"{y:>9}" for y in YEARS_WIDE)
        + "   pooled      CV   gate"
    )
    stability_ok = True
    cvs = {}
    for comp in (*GATED, "ladder_total"):
        vals = [per_year_env[y][comp] for y in YEARS_WIDE]
        c = cv(vals)
        cvs[comp] = c
        gated = comp in GATED
        ok = bool(np.isfinite(c) and c <= CV_MAX)
        if gated:
            stability_ok = stability_ok and ok
        mark = ("ok" if ok else "FAIL") if gated else "(reported)"
        row = comp.ljust(18) + "".join(f"{v:>9,.0f}" for v in vals)
        print(f"{row}{pooled_env[comp]:>9,.0f}   {c:>5.3f}   {mark}")

    # --- GATE 2: LOYO on the GATED components, SEVEN folds ------------------
    print(
        f"\n--- LOYO (derive on the other {len(YEARS_WIDE) - 1} years pooled, predict "
        f"the held-out year; bar {LOYO_MAX:.0%}) ---"
    )
    loyo_ok = True
    loyo = {}
    for held in YEARS_WIDE:
        train = [y for y in YEARS_WIDE if y != held]
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
    print(
        f"\n--- DELIVERED static SPOT ladder (pooled {YEARS_WIDE[0]}-{YEARS_WIDE[-1]},"
        " §4 placement) ---"
    )
    print("rung".ljust(16) + "  derived  incumbent      delta")
    for nm in names:
        d = pooled_rungs[nm]
        i = incumbent[nm]
        print(f"{nm.ljust(16)}{d:>9,.0f}{i:>11,.0f}{d - i:>+11,.0f}")
    dt, it = sum(pooled_rungs.values()), sum(incumbent.values())
    print(f"{'TOTAL SPOT'.ljust(16)}{dt:>9,.0f}{it:>11,.0f}{dt - it:>+11,.0f}")

    # --- §5: reported at full magnitude, NOT gated --------------------------
    per_rung_cv = {nm: cv([per_year_rungs[y][nm] for y in YEARS_WIDE]) for nm in names}
    per_rung_loyo = {}
    for held in YEARS_WIDE:
        train = [y for y in YEARS_WIDE if y != held]
        pred, _ = place_rungs_wide(net, train)
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
            "rung".ljust(16)
            + "".join(f"{y:>9}" for y in YEARS_WIDE)
            + "   pooled      CV"
        )
        for nm in names:
            vals = [per_year_rungs[y][nm] for y in YEARS_WIDE]
            row = nm.ljust(16) + "".join(f"{v:>9,.0f}" for v in vals)
            print(f"{row}{pooled_rungs[nm]:>9,.0f}   {per_rung_cv[nm]:>5.3f}")
        for held in YEARS_WIDE:
            r = per_rung_loyo[held]
            detail = "  ".join(f"{nm}={r['errors'][nm]:.1%}" for nm in names)
            print(
                f"  per-rung LOYO hold {held}: worst {r['worst']:.1%} ({r['worst_rung']})"
            )
            print(f"            {detail}")
        print("\n=== corridor weights, firm blocks and the simultaneity gap ===")
        for y in (*YEARS_WIDE, "pooled"):
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
        for y in YEARS_WIDE:
            flows = corridor_total(net, [y])
            bits = []
            for k in (*CORRIDORS, "TOTAL"):
                a = flows[k]
                bits.append(
                    f"{k}: n={a.size} p98={np.percentile(a, CAP_PCTL):,.0f} "
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
            "Do NOT solve. File the FINDING. Per PRECOMMIT §6 this outcome is\n"
            "TERMINAL: seven years of measured seam flow is the whole record, so the\n"
            "object is closed from DATA, not from effort. Do not soften a bar,\n"
            "re-scope the gated object, admit whichever component passes, fall back\n"
            "to a residual-tuned depth, or propose a further widening. Return the DOF\n"
            "to the owner as permanently declared."
        )
    else:
        near = max(v["worst"] for v in loyo.values())
        print(
            f"    worst fold {near:.1%} vs the {LOYO_MAX:.0%} bar; worst gated CV "
            f"{max(cvs[c] for c in GATED):.3f} vs {CV_MAX:.2f}."
        )

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "session": "caiso-235",
                    "precommit": (
                        "results/calibration/"
                        "PRECOMMIT-caiso235-import-depth-widesample-2026-09-02.md"
                    ),
                    "method": {
                        "estimator": (
                            "caiso-234 TOTAL envelope, imported verbatim from "
                            "scripts/data/derive_caiso_import_total_envelope.py"
                        ),
                        "single_change": "pooled sample 2023-2025 -> 2019-2025",
                        "years": list(YEARS_WIDE),
                        "excluded": "2026 (LOCKED-TEST tier, active holdout freeze)",
                        "gated_object": list(GATED),
                        "cap_pctl": CAP_PCTL,
                        "scarcity_pctl": SCARCITY_PCTL,
                        "cv_max": CV_MAX,
                        "loyo_max": LOYO_MAX,
                        "round_mw": ROUND_MW,
                        "fork": (
                            "PRECOMMIT §4-FORK option (a): placement firm block = "
                            "mean of the committed measured MIC blocks over "
                            f"{list(FIRM_REFERENCE_YEARS)}, constant across sample "
                            "years and folds"
                        ),
                        "fork_check_ok": fork_ok,
                        "fork_check": fork_rows,
                    },
                    "gated": {
                        "per_year": {str(y): per_year_env[y] for y in YEARS_WIDE},
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
                        "per_year_rungs": {
                            str(y): per_year_rungs[y] for y in YEARS_WIDE
                        },
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
                        **{str(y): per_year_diag[y] for y in YEARS_WIDE},
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
