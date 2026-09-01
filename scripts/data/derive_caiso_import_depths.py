"""Derive the CAISO WECC-corridor import rung CAPACITIES from measured seam depth.

The capacity-limb companion to ``scripts/data/derive_caiso_import_tranches.py``
(which re-derives PRICES only, by its own docstring). This script closes the LAST
uncited limb of ``interchange.spec.IMPORT_TRANCHES["CAISO"]``: the four SPOT rung
depths, which the caiso-186 DOF census labels ``RESIDUAL (static, no cited
primary source)`` and which no derive script has ever produced --

    PNW_midC 1,800 / DSW_CCGT 1,800 / DSW_CT 2,200 / WECC_scarcity 3,000
    = 8,800 MW of bare literals, invariant across 2023-2025.

(The other two rungs -- ``PNW_hydro_base`` and ``DSW_solar_PV``, the
``caiso.CAISO_FIRM_IMPORT_TRANCHES`` pair -- are already MEASURED and per-year:
DMM RA import capacity x the published Maximum Import Capability corridor share.
They are held FIXED here. Only the ungrounded limb is derived, per rule 1
[R-STRUCT] -- a grounded quantity is never re-opened to move a residual.)

Methodology -- per-corridor measured depth (the NEISO precedent, ported)
-----------------------------------------------------------------------
Four of five sibling ISOs closed this same gap (G-26 / issue #1350 / audit C-6);
CAISO is the only one left on bare literals. ``derive_neiso_import_tranches.py``
sizes each seam's routine rung at the p98 of that seam's measured import-positive
flow ("the deepest sustained deliveries, clipping single-hour spikes") and the
scarcity rung at the p99.9 of TOTAL import beyond the routine sum. This script
applies that identification to CAISO's corridor topology:

    routine_depth(corridor) = p98( measured corridor net import )
    spot_depth(corridor)    = routine_depth(corridor) - firm(corridor)
    scarcity                = p99.9( measured TOTAL net import ) - sum(routine)

with the FIRM block carved out of its corridor's p98 exactly as NEISO carves
Highgate's published converter rating out of the HQ seam's p98 -- the published
rating sizes the baseload rung, the measured depth sizes the economic remainder.

The DSW spot remainder splits into its two thermal rungs (``DSW_CCGT``,
``DSW_CT``) as EQUAL blocks -- the NEISO ``NYISO_CT_base``/``NYISO_CT_peak``
convention and the NYISO ladder's equal-MW rung design. Equal blocks add ZERO
free parameters: the split point is fixed by the convention, not chosen.

Why EIA-930 is admissible here, though it was rejected for the FIRM limb
----------------------------------------------------------------------
The ``IMPORT_TRANCHES`` provenance block records a boundary caveat (rule 14):
"EIA-930 net corridor flows cannot size a gross firm block (their low percentiles
are negative: midday solar exports net against firm imports)". That objection is
specific to the FIRM limb and does NOT transfer to the spot limb, for the reason
it gives: it is a statement about the LOW tail of the net-flow distribution. The
spot rungs are by construction the depth ABOVE the firm base -- the high tail --
where a net measurement and a gross measurement coincide (CAISO does not
simultaneously import 8 GW and export on the same corridor). The script reports
the sign of every percentile it uses so the caveat stays checkable rather than
assumed (see ``--report``).

Estimation-stage honesty gates (run BEFORE any solve; caiso-81/83 precedent)
---------------------------------------------------------------------------
Held to the SAME bar the PRICE limb failed (``derive_caiso_import_tranches.py``:
CV 0.20 / LOYO 0.25; the price ladder failed LOYO at 30.5 % and was not solved):

  * YEAR-STABILITY: each derived rung's coefficient of variation across
    2023-2025 must be <= ``CV_MAX``. A revealed market structure, not a
    per-year fit.
  * LOYO: derive on two years, predict the held-out year's depths; the held-out
    relative error must stay within ``LOYO_MAX``.

If either gate FAILS the script prints FAIL, the caller files the FINDING and
does NOT solve. Softening the bar to manufacture a pass would be a rule-13 act.

Rule 23 [R-FROZEN-DERIVE]: re-derive ONLY when the EIA-930 CISO interchange
extract extends -- never because a backcast residual moved.

Usage:
    python scripts/data/derive_caiso_import_depths.py            # gates + ladder
    python scripts/data/derive_caiso_import_depths.py --report   # + diagnostics
    python scripts/data/derive_caiso_import_depths.py --json PATH
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

from derive_caiso_import_tranches import YEARS, corridor_net_import  # noqa: E402

from market_sim.model.interchange.caiso import (  # noqa: E402
    CAISO_FIRM_IMPORT_TRANCHES,
)
from market_sim.model.interchange.spec import IMPORT_TRANCHES_BY_YEAR  # noqa: E402

# --- Fixed derivation structure (frozen; re-derive only on source update) ---

# Routine per-corridor depth percentile. NEISO precedent (CAP_PCTL = 98.0):
# "the routinely deliverable depth (p98 ~ the deepest sustained deliveries,
# clipping single-hour spikes)". Identical value, identical role.
CAP_PCTL = 98.0

# Emergency-depth percentile for the scarcity rung, on TOTAL net import.
# NEISO precedent (SCARCITY_PCTL = 99.9), identical value, identical role.
SCARCITY_PCTL = 99.9

# Which model rungs are the SPOT (derived) limb of each corridor, cheapest-first.
# The FIRM rung of each corridor is held at its measured MIC value and carved out
# of that corridor's routine depth.
CORRIDOR_SPOT_RUNGS = {
    "WECC_PNW": ("PNW_midC",),
    "WECC_DSW": ("DSW_CCGT", "DSW_CT"),
}
SCARCITY_RUNG = "WECC_scarcity"

# Honesty-gate thresholds -- the SAME bar the price limb was held to and failed
# (derive_caiso_import_tranches.py CV_MAX / LOYO_MAX). Not softenable.
CV_MAX = 0.20
LOYO_MAX = 0.25

# Rung capacities round to 5 MW (NEISO `_round_cap`).
ROUND_MW = 5.0


def _round_cap(mw: float) -> float:
    """Round a rung capacity to the nearest 5 MW (NEISO convention)."""
    return float(round(mw / ROUND_MW) * ROUND_MW)


def firm_by_corridor(year: int) -> dict[str, float]:
    """Measured MIC firm block per corridor for ``year`` (held fixed, not derived).

    Reads the committed per-year ladder so the carve-out tracks the DMM RA x MIC
    measurement rather than restating it.
    """
    rungs = IMPORT_TRANCHES_BY_YEAR["CAISO"][year]
    firm = {n: c for n, c, _ in rungs if n in CAISO_FIRM_IMPORT_TRANCHES}
    return {
        "WECC_PNW": firm["PNW_hydro_base"],
        "WECC_DSW": firm["DSW_solar_PV"],
    }


def derive_depths(net, years) -> tuple[dict[str, float], dict[str, float]]:
    """Derive {rung: capacity_mw} from the pooled measured sample over ``years``.

    Returns ``(depths, diagnostics)``. ``net`` is the dense (year, hour) corridor
    net-import frame from :func:`derive_caiso_import_tranches.corridor_net_import`.
    """
    years = list(years)
    diag: dict[str, float] = {}
    depths: dict[str, float] = {}

    # Firm carve-out: the capacity-weighted mean over the pooled years, so a
    # pooled derivation carves the same block its pooled sample actually carried.
    firm = {
        c: float(np.mean([firm_by_corridor(y)[c] for y in years]))
        for c in CORRIDOR_SPOT_RUNGS
    }

    total = None
    routine_sum = 0.0
    for corridor, spot_rungs in CORRIDOR_SPOT_RUNGS.items():
        flow = np.concatenate([net.loc[y][corridor].to_numpy() for y in years])
        flow = flow[np.isfinite(flow)]
        routine = float(np.percentile(flow, CAP_PCTL))
        diag[f"{corridor}_p{CAP_PCTL:g}"] = routine
        diag[f"{corridor}_firm"] = firm[corridor]
        spot_total = max(0.0, routine - firm[corridor])
        share = _round_cap(spot_total / len(spot_rungs))
        for name in spot_rungs:
            depths[name] = share
        routine_sum += firm[corridor] + share * len(spot_rungs)

        stacked = np.stack(
            [net.loc[y][corridor].to_numpy() for y in years]
        )  # (year, hour)
        total = stacked if total is None else total + stacked

    tot = total.reshape(-1)
    tot = tot[np.isfinite(tot)]
    emergency = float(np.percentile(tot, SCARCITY_PCTL))
    diag[f"total_p{SCARCITY_PCTL:g}"] = emergency
    diag["routine_sum"] = routine_sum
    depths[SCARCITY_RUNG] = _round_cap(max(0.0, emergency - routine_sum))
    return depths, diag


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", action="store_true", help="print diagnostics")
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

    per_year = {}
    diags = {}
    for y in YEARS:
        per_year[y], diags[y] = derive_depths(net, [y])
    pooled, pooled_diag = derive_depths(net, YEARS)

    print("=== CAISO import SPOT depths, derived from measured corridor depth ===")
    print(
        f"    routine p{CAP_PCTL:g} per corridor; scarcity p{SCARCITY_PCTL:g} of total"
    )
    hdr = "rung".ljust(15) + "".join(f"{y:>9}" for y in YEARS)
    print(hdr + "   pooled   incumbent      CV   gate")
    stability_ok = True
    cvs = {}
    for nm in names:
        vals = np.array([per_year[y][nm] for y in YEARS], dtype=float)
        mean = float(np.nanmean(vals))
        cv = float(np.nanstd(vals) / mean) if mean else float("nan")
        cvs[nm] = cv
        ok = bool(np.isfinite(cv) and cv <= CV_MAX)
        stability_ok = stability_ok and ok
        row = nm.ljust(15) + "".join(f"{v:>9.0f}" for v in vals)
        print(
            f"{row}{pooled[nm]:>9.0f}{incumbent[nm]:>12.0f}   {cv:>5.3f}   "
            f"{'ok' if ok else 'FAIL'}"
        )
    print(
        f"{'TOTAL':<15}"
        + "".join(f"{sum(per_year[y].values()):>9.0f}" for y in YEARS)
        + f"{sum(pooled.values()):>9.0f}{sum(incumbent.values()):>12.0f}"
    )

    print(
        f"\n=== LOYO (derive on 2 years, predict the held-out year; bar {LOYO_MAX:.0%}) ==="
    )
    loyo_ok = True
    loyo = {}
    for held in YEARS:
        train = [y for y in YEARS if y != held]
        pred, _ = derive_depths(net, train)
        act = per_year[held]
        errs = {}
        for nm in names:
            denom = act[nm] if act[nm] else float("nan")
            errs[nm] = abs(pred[nm] - act[nm]) / denom if denom else float("nan")
        worst_nm = max(errs, key=lambda k: np.nan_to_num(errs[k], nan=-1))
        worst = errs[worst_nm]
        ok = bool(np.isfinite(worst) and worst <= LOYO_MAX)
        loyo_ok = loyo_ok and ok
        loyo[held] = {"errors": errs, "worst_rung": worst_nm, "worst": worst}
        detail = "  ".join(f"{nm}={errs[nm]:.1%}" for nm in names)
        print(
            f"  hold {held}: worst {worst:.1%} ({worst_nm})   "
            f"{'ok' if ok else 'FAIL'}\n            {detail}"
        )

    if args.report:
        print(
            "\n=== diagnostics (percentile signs; the rule-14 EIA-930 caveat check) ==="
        )
        for y in (*YEARS, "pooled"):
            d = pooled_diag if y == "pooled" else diags[y]
            bits = "  ".join(f"{k}={v:,.0f}" for k, v in d.items())
            print(f"  {y}: {bits}")

    verdict = "PASS" if (stability_ok and loyo_ok) else "FAIL"
    print(
        f"\n=== GATES: year-stability {'ok' if stability_ok else 'FAIL'} | "
        f"LOYO {'ok' if loyo_ok else 'FAIL'} => {verdict} ==="
    )
    if verdict == "FAIL":
        print("Do NOT solve. File the FINDING (derive-first discipline, rule 13).")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "method": {
                        "cap_pctl": CAP_PCTL,
                        "scarcity_pctl": SCARCITY_PCTL,
                        "cv_max": CV_MAX,
                        "loyo_max": LOYO_MAX,
                        "round_mw": ROUND_MW,
                        "precedent": "scripts/data/derive_neiso_import_tranches.py",
                    },
                    "per_year": {str(y): per_year[y] for y in YEARS},
                    "pooled": pooled,
                    "incumbent_2025": incumbent,
                    "diagnostics": {
                        **{str(y): diags[y] for y in YEARS},
                        "pooled": pooled_diag,
                    },
                    "gates": {
                        "cv": cvs,
                        "year_stability": stability_ok,
                        "loyo": {
                            str(k): {
                                "worst": v["worst"],
                                "worst_rung": v["worst_rung"],
                                "errors": v["errors"],
                            }
                            for k, v in loyo.items()
                        },
                        "loyo_ok": loyo_ok,
                        "verdict": verdict,
                    },
                },
                indent=1,
                default=float,
            )
        )
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
