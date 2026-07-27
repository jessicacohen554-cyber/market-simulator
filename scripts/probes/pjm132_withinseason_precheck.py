"""pjm-132 Stage-1 no-LP pre-check: does the within-season surface carry a GRADIENT?

Charter: ``docs/handoffs/pjm-132-midcurve-reconditioning-charter-2026-07.md``
(committed before the re-derive ran). Authority: the owner's 2026-07-27
authorization of ``docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md``.

Stage 1 of memo §4, verbatim: re-derive both surfaces within-season, then
measure the NEW surface's MW-weighted bid delta on the keeper fleet
(reconstructed with no LP via ``scripts/lib/bundle_fleet.py``) before any solve
is spent.

PRE-REGISTERED KILL CRITERION (memo §4, the pjm-123 K1 criterion; inherited
verbatim, not re-scoped):

  **K1-GRADIENT.** The new surface's MW-weighted bid delta on the keeper fleet
  must be **larger in the tightest bin than in the slackest** — gradient
  ``bin3 − bin0 > 0`` — for the **armed floor scope**, in **at least 2 of the
  3 years**. A surface whose re-conditioning still moves the slack bins as much
  as the tight bin is not a dispersion lever, and **NO SOLVE IS SPENT**.

  Rationale (pjm-120/121/123): the C3a-2025 residual is a monotone dispersion
  COMPRESSION. Only a mechanism that WIDENS it can close the tight strata
  without re-inflating the 6,771 cheap hours already $4-10/MWh too high. A
  same-sign level shift either way is the refutation signature.

PRE-REGISTERED HONESTY BOUND (memo §4, reported to the owner BEFORE Stage 2 is
launched, not after): if the armed tight-bin floor rises by **less than
~$1/MWh MW-weighted**, the expected solve-level effect is within noise and that
is reported as such.

WHY NO STARTUP-MARKUP BRACKET IS NEEDED HERE. pjm-123 had to bracket
``compute_monthly_markup`` because it compared a composite against the keeper
across mechanisms. This probe compares the SAME mechanism under two surface
vintages: ``bid = mc_base + startup_markup + midcurve_markup``, and the first
two terms are identical in both arms, so the bid delta is EXACTLY the mid-curve
markup delta. The bracket would be two identical numbers.

REPORTING PARTITION, stated so the comparison is well-posed: the delta is
MW-weighted within the **keeper's own within-year** tightness bins. The
question K1 asks is "in the hours the keeper calls tight, does the new surface
raise bids more than in the hours it calls slack?", so the hour partition must
be held fixed across the two arms — it is the baseline's, not the arm's.

Usage:
    PYTHONPATH=. .venv/bin/python scripts/probes/pjm132_withinseason_precheck.py \
        results/calibration/pjm121_ccbelt --years 2023 2024 2025 \
        --json-out results/calibration/pjm132_withinseason_precheck.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]

#: K1 gradient must hold in at least this many of the solved years.
K1_MIN_YEARS = 2
#: Honesty bound: a tight-bin rise under this ($/MWh MW-weighted) is noise.
HONESTY_BOUND_USD = 1.0
#: The conditioning bin edges the family shares (never re-tuned here).
EDGES = (0.80, 0.90, 0.97)


def _sys_path() -> None:
    for p in (REPO, REPO / "scripts", REPO / "scripts" / "data", REPO / "src"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))


def _mw_weighted_by_bin(delta: np.ndarray, caps: np.ndarray, hour_bin: np.ndarray):
    """MW-weighted mean bid delta per net-load bin, $/MWh (pjm-123 convention)."""
    if caps.sum() <= 0:
        return {f"bin{b}": float("nan") for b in range(len(EDGES) + 1)}
    w = caps[:, None] / caps.sum()
    out = {}
    for b in range(len(EDGES) + 1):
        sel = hour_bin == b
        out[f"bin{b}"] = (
            float((delta[:, sel] * w).sum() / sel.sum()) if sel.any() else float("nan")
        )
    return out


def _year_row(
    bundle: Path, year: int, arm_a_path: str | None = None,
    arm_b_path: str | None = None,
) -> dict:
    """One year's arm-A vs arm-B mid-curve markup delta, binned and weighted."""
    from market_sim.data.fleet import build_pjm_offer_midcurve_conditional_markup
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, _meta = reconstruct_bundle_fleet(bundle, year)
    fa, fleet, cfg = state["fleet_arrays"], state["fleet"], state["config"]
    mc = np.asarray(state["mc_base"], dtype=float)
    hours = int(mc.shape[1])

    # The surface's own conditioning driver, exactly as the solve builds it.
    demand = np.asarray(state["demand"], dtype=float)
    net_load = demand.sum(axis=0)[:hours]
    for key, cap in (("solar_cf", "solar_cap"), ("wind_cf", "wind_cap")):
        cf, capacity = state.get(key), state.get(cap)
        if cf is not None and capacity is not None:
            net_load = net_load - (np.asarray(capacity)[:, None] * np.asarray(cf)).sum(
                axis=0
            )[:hours]

    # Reporting partition: the KEEPER's within-year bins, held fixed across arms.
    hour_bin = np.searchsorted(
        np.quantile(net_load, EDGES), net_load, side="right"
    )

    # Explicit arm paths (Stage-0 feasibility read, charter §7): both arms are
    # derived on the SAME year-restricted corpus so the conditioning change is
    # not confounded with year coverage. Unset = the normal Stage-1 resolution
    # (arm A the live within-year default, arm B the `_withinseason` vintage).
    cfg_a = cfg if arm_a_path is None else cfg.with_overrides(
        pjm_offer_midcurve_path=arm_a_path
    )
    cfg_b = cfg.with_overrides(pjm_offer_surface_within_season=True)
    if arm_b_path is not None:
        cfg_b = cfg_b.with_overrides(pjm_offer_midcurve_path=arm_b_path)
    arm_a = build_pjm_offer_midcurve_conditional_markup(
        fa, fleet, mc, net_load, cfg_a, year
    )
    arm_b = build_pjm_offer_midcurve_conditional_markup(
        fa, fleet, mc, net_load, cfg_b, year
    )
    if arm_a is None or arm_b is None:
        raise SystemExit(
            f"{year}: mid-curve markup is None for an arm "
            f"(A={arm_a is None}, B={arm_b is None}) — the keeper's floor "
            "scope must be armed for this probe to measure anything."
        )

    delta = np.asarray(arm_b, dtype=float) - np.asarray(arm_a, dtype=float)
    # Armed floor scope = the rows the mechanism actually prices in EITHER arm.
    touched = (np.asarray(arm_a) != 0.0).any(axis=1) | (
        np.asarray(arm_b) != 0.0
    ).any(axis=1)
    binned = _mw_weighted_by_bin(delta[touched], fa.pmax[touched], hour_bin)
    grad = binned[f"bin{len(EDGES)}"] - binned["bin0"]
    return {
        "year": year,
        "n_touched_rows": int(touched.sum()),
        "mw_wtd_delta_by_bin": binned,
        "gradient_bin3_minus_bin0": grad,
        "gradient_positive": bool(np.isfinite(grad) and grad > 0.0),
        "tight_bin_rise_usd": binned[f"bin{len(EDGES)}"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", help="keeper bundle (results/calibration/pjm121_ccbelt)")
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--json-out", default=None)
    ap.add_argument(
        "--arm-a-path",
        default=None,
        help="explicit within-YEAR surface JSON (charter §7 Stage-0 read)",
    )
    ap.add_argument(
        "--arm-b-path",
        default=None,
        help="explicit within-SEASON surface JSON (charter §7 Stage-0 read)",
    )
    args = ap.parse_args()

    _sys_path()
    bundle = Path(args.bundle)
    rows = [
        _year_row(bundle, y, args.arm_a_path, args.arm_b_path) for y in args.years
    ]

    n_pos = sum(1 for r in rows if r["gradient_positive"])
    tight_rises = [
        r["tight_bin_rise_usd"] for r in rows if np.isfinite(r["tight_bin_rise_usd"])
    ]
    out = {
        "bundle": str(bundle),
        "years": args.years,
        "rows": rows,
        "k1_gradient": {
            "years_with_positive_gradient": n_pos,
            "years_measured": len(rows),
            "required": K1_MIN_YEARS,
            # K1 is a 2-of-3 rule, so a run over fewer than 3 years can only
            # ever be PARTIAL — it cannot satisfy or refute the gate (charter
            # §7). Reporting "FAIL" there would misread a Stage-0 feasibility
            # read as a refutation.
            "verdict": (
                ("PASS" if n_pos >= K1_MIN_YEARS else "FAIL")
                if len(rows) >= 3
                else f"PARTIAL ({n_pos}/{len(rows)} measured year(s) positive; "
                f"{K1_MIN_YEARS} of 3 required for the gate)"
            ),
        },
        "honesty_bound": {
            "threshold_usd": HONESTY_BOUND_USD,
            "max_tight_bin_rise_usd": max(tight_rises) if tight_rises else float("nan"),
            "within_noise": bool(
                tight_rises and max(tight_rises) < HONESTY_BOUND_USD
            ),
        },
    }
    print(json.dumps(out, indent=2, default=str))
    if args.json_out:
        p = Path(args.json_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=2, default=str))
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
