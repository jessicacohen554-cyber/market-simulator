"""pjm-125 no-LP pre-check: can constraining perfect-foresight commitment tighten PJM's reserve balance?

`docs/FINDING-pjm120-c3a-extreme-tail-depth-2026-07.md` §7 framing **1**:
"whether perfect-foresight all-online commitment should be constrained before
the reserve bound is read". pjm-124 closed framing 2 (scoping the ``ramp10``
deliverability bound); this probe adjudicates its commitment-side analogue.

WHY THIS IS NOT JUST pjm-124 AGAIN. Framing 2 attacked ONE of the two
constraint families the per-gen co-opt imposes — the per-pool ramp bound
``R[r] <= SUM ramp10 x availability``. Framing 1 attacks the OTHER: the joint
``SUM P + R <= SUM cap`` capacity row, which today counts EVERY member's
capacity, committed or not. `docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md`
§B.4 states the premise: "pjm-81/82 proved the perfect-foresight LP holds
~2.7-3.1x the real online reserve at near-zero cost". A 2.7-3.1x surplus is a
materially better prospect than framing 2's measured ~10x, so the two must be
measured separately (rule 19) rather than assumed to share a verdict.

THE COMMITMENT-INVARIANT FLOOR. Whatever a commitment constraint does — a
posture screen, a no-foresight commitment, a decommitment pass — it cannot
remove **offline fast-start** capacity from the Primary balance: Primary =
Synchronized + Non-Synchronized, and Non-Sync reserve IS offline
10-min-startable iron (Manual 11 sec 4.2, the pjm-124 result). So fast-start
members supply reserve in EITHER commitment state, and they are bounded by both
families at once:

    F_ramp(t) = SUM over FAST members of ramp10 x availability(t)   [ramp bound]
    F_head(t) = SUM over FAST members of cap x availability(t)
                - D_fast(t)                                        [joint row]

    S_floor(t) = max(0, min(F_ramp(t), F_head(t)))   <=  reserve supply, ALWAYS

``D_fast`` is the dispatch attributable to fast members, taken from the keeper's
own committed P1 class-hourly sidecar and deliberately OVER-attributed (a
class's whole production is charged to its fast members, capped at their
capacity), which biases ``S_floor`` DOWN — in the mechanism's favour.

``S_floor`` is invariant to every commitment mechanism, so if it stays well
above the requirement, framing 1 is closed without knowing which commitment
constraint was meant. This is the same logic pjm-124 used, applied to both
constraint families instead of one.

PRE-REGISTERED KILL CRITERIA (written and committed before the probe was run;
framing 1 is REFUTED if K1 fails, and no solve is spent).

  K1 MAGNITUDE — decisive. Bands identical to pjm-124's so the two framings are
     directly comparable, evaluated on ``S_floor`` (the most generous possible
     accounting of what a commitment constraint can remove):
       * PASS  — worth one A/B solve: annual-mean ``S_floor <= 3 x R`` AND
         ``S_floor <= 2 x R`` in at least 50 hours inside the tightest net-load
         quartile.
       * PARTIAL — ``S_floor`` falls >= 50% below the keeper's effective supply
         bound but stays above 2 x R in the tight bin. Frontier evidence; NO
         solve.
       * KILL — ``S_floor`` stays above 3 x R without that 50% narrowing. No
         commitment constraint can make the balance bind. NO solve.
     PARTIAL and KILL as worded overlap; PARTIAL is the more specific band and
     takes precedence. Both carry the same consequence (NO solve), so the
     precedence changes only how much the label reports, never the decision.

  K2 TIGHT-BIN BITE — a mechanism that cannot bite where the residual lives is
     inert whatever its annual mean does. The maximally-constrained effective
     supply bound must sit at least 10 pp below the keeper's own effective bound
     **in the tightest net-load quartile**. (pjm-124 measured framing 2's tight-
     bin bite at 8-10%, i.e. below this line.) Failing K2 while passing K1 would
     be a level effect, not a commitment mechanism (rule 1).

  K3 ADMISSIBILITY (rule 13) — every quantity must be derivable from fleet
     physics plus the model's own dispatch. The measured PJM series is read for
     the REQUIREMENT only (published Manual 13), and the measured SR+REG target
     is reported as a DIAGNOSTIC comparison, never as an input to any arm.

REPORTED, NOT GATED: which constraint family actually binds the keeper's
reserve today (``min(ramp bound, joint headroom)``), and whether pjm-82's
2.7-3.1x premise still reproduces on the current keeper. Both are new
measurements for the frontier ledger regardless of the verdict.

Pure diagnostic, no LP. Usage:

    python scripts/probes/pjm125_commitment_constraint_precheck.py \
        results/calibration/pjm121_ccbelt --year 2025 \
        --json-out results/calibration/pjm125_precheck_2025.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
# REPO itself must be on the path so ``scripts.lib.clean_io`` resolves as a
# package — without it the data/clean readers silently fall back and the
# measured overlays (east interface cut, ramp capability) refuse to load.
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from pjm124_ramp10_scope_precheck import (  # noqa: E402
    class_hourly_mw,
    dispatch_implied_online_mw,
    member_klass,
    member_ramp,
    net_load_bins,
    plant_online_physics,
)

#: K1 bands — identical to pjm-124's, so the two framings compare directly.
K1_PASS_MEAN_REQ_MULTIPLE = 3.0
K1_PASS_TIGHT_REQ_MULTIPLE = 2.0
K1_PASS_TIGHT_MIN_HOURS = 50
K1_PARTIAL_MIN_REDUCTION_FRAC = 0.50

#: K2 band: minimum tight-quartile bite, in percentage points.
K2_MIN_TIGHT_BITE_PP = 10.0

#: pjm-82's measured online reserve target (SR + REG), GW. Diagnostic only —
#: never an input to any arm (K3). Source: docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md
#: §B.4, "pjm-81/82 proved the perfect-foresight LP holds ~2.7-3.1x the real
#: online reserve at near-zero cost", against a measured SR+REG of ~3.0-3.3 GW.
PJM82_MEASURED_ONLINE_TARGET_GW = (3.0, 3.3)
PJM82_MEASURED_SURPLUS_MULTIPLE = (2.66, 3.14)


def member_cap(fleet_arrays, gen_idx):
    """Return the ``(n_members, T)`` availability-scaled capacity.

    The quantity the per-gen co-opt's joint ``SUM P + R <= SUM cap`` row sums.

    Args:
        fleet_arrays: The reconstructed keeper ``FleetArrays``.
        gen_idx: Member row indices from ``pjm_pergen_structure``.

    Returns:
        ``(n_members, T)`` MW.
    """
    pmax = np.asarray(fleet_arrays.pmax, dtype=float)[gen_idx]
    avail = np.asarray(fleet_arrays.availability, dtype=float)[gen_idx]
    return pmax[:, np.newaxis] * avail


def attributed_dispatch(labels, cap_t, sel, klass_mw, hours):
    """Return the ``(T,)`` dispatch attributable to the ``sel`` members.

    Class dispatch is charged to the selected members up to their own capacity.
    Used two ways, each biased in the direction that is CONSERVATIVE for the
    mechanism under test: charging a class's whole production to its fast
    members shrinks their headroom (a smaller ``S_floor``), and charging it to
    the eligible members shrinks the keeper's own headroom.

    Args:
        labels: ``(n_members,)`` class labels.
        cap_t: ``(n_members, T)`` availability-scaled capacity.
        sel: ``(n_members,)`` bool selection.
        klass_mw: ``{klass: (T,) MW}`` committed P1 class dispatch.
        hours: Hour count.

    Returns:
        ``(T,)`` MW.
    """
    out = np.zeros(hours, dtype=float)
    for kl, dispatch in klass_mw.items():
        rows = sel & (labels == kl)
        if not rows.any():
            continue
        out += np.minimum(dispatch[:hours], cap_t[rows].sum(axis=0))
    return out


def main() -> int:
    """Compute the arms, evaluate K1-K3, print and persist the verdict."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, meta = reconstruct_bundle_fleet(args.bundle, args.year)
    fa = state["fleet_arrays"]
    hours = int(meta["hours"])
    if getattr(fa, "ramp10", None) is None:
        raise SystemExit(
            "the reconstructed fleet carries no ramp10 — the reserve co-opt is "
            "not engaged and every arm below would be meaningless"
        )

    from market_sim.model.reserves.spec import pjm_pergen_structure
    from market_sim.results.scarcity import load_pjm_measured_reserve_requirement

    gen_idx, _col, n_r = pjm_pergen_structure(fa)
    group_of, grp_fast, _elig = plant_online_physics(fa)
    fast = grp_fast[group_of[gen_idx]]
    nonfast = ~fast
    ramp_t = member_ramp(fa, gen_idx)[:, :hours]
    cap_t = member_cap(fa, gen_idx)[:, :hours]
    labels = member_klass(fa)[gen_idx]

    req = load_pjm_measured_reserve_requirement(args.year, hours)
    if req is None:
        raise SystemExit(
            f"no measured PJM Primary requirement for {args.year} — the K1 "
            "bands are stated as multiples of it and cannot be evaluated"
        )
    R = float(np.mean(req))

    klass_mw = class_hourly_mw(args.bundle, args.year, hours)
    if not klass_mw:
        raise SystemExit(
            "the bundle carries no class_hourly sidecar — the joint-row arms "
            "need the keeper's own committed P1 dispatch"
        )
    D_fast = attributed_dispatch(labels, cap_t, fast, klass_mw, hours)
    D_elig = attributed_dispatch(
        labels, cap_t, np.ones_like(fast, dtype=bool), klass_mw, hours
    )

    # ---- the keeper's own effective supply bound --------------------------
    ramp_bound = ramp_t.sum(axis=0)
    head_bound = np.maximum(cap_t.sum(axis=0) - D_elig, 0.0)
    keeper_eff = np.minimum(ramp_bound, head_bound)

    # ---- the commitment-invariant floor -----------------------------------
    F_ramp = ramp_t[fast].sum(axis=0)
    F_head = np.maximum(cap_t[fast].sum(axis=0) - D_fast, 0.0)
    S_floor = np.maximum(np.minimum(F_ramp, F_head), 0.0)

    # ---- the maximally-constrained effective bound (for K2) ---------------
    # Committed set = every fast member (offline fast still backs Non-Sync) plus
    # the ramp-minimal non-fast set covering non-fast production. Its ramp is
    # F_ramp + DISP; its capacity is the fast capacity plus that minimal set's,
    # whose headroom above its own production is zero in the worst case.
    DISP = dispatch_implied_online_mw(fa, gen_idx, ramp_t, nonfast, klass_mw)
    constrained_eff = np.minimum(F_ramp + DISP, F_head)

    print(
        f"\nPJM {args.year}: {n_r} pools / {gen_idx.size} members; "
        f"{int(fast.sum())} fast-start "
        f"({fa.pmax[gen_idx][fast].sum() / 1e3:.1f} GW nameplate)"
    )
    print(f"  measured Primary requirement R (RTO): mean {R / 1e3:.2f} GW")
    print("  -- which family binds the keeper today --")
    print(f"     ramp bound        mean {ramp_bound.mean() / 1e3:7.2f} GW")
    print(f"     joint headroom    mean {head_bound.mean() / 1e3:7.2f} GW")
    print(
        f"     effective         mean {keeper_eff.mean() / 1e3:7.2f} GW  "
        f"= {keeper_eff.mean() / R:.1f}x R   "
        f"(ramp binds {100 * (ramp_bound <= head_bound).mean():.0f}% of hours)"
    )
    print("  -- the commitment-invariant floor --")
    print(f"     F_ramp (fast)     mean {F_ramp.mean() / 1e3:7.2f} GW")
    print(f"     F_head (fast)     mean {F_head.mean() / 1e3:7.2f} GW")
    print(
        f"     S_floor           mean {S_floor.mean() / 1e3:7.2f} GW  "
        f"= {S_floor.mean() / R:.1f}x R"
    )

    # ---- K1 ---------------------------------------------------------------
    hour_bin, _net = net_load_bins(state, hours)
    tight = hour_bin == hour_bin.max()
    tight_under = int((S_floor[tight] <= K1_PASS_TIGHT_REQ_MULTIPLE * R).sum())
    mean_multiple = float(S_floor.mean() / R)
    reduction = 1.0 - float(S_floor.mean() / keeper_eff.mean())
    k1_pass = (
        mean_multiple <= K1_PASS_MEAN_REQ_MULTIPLE
        and tight_under >= K1_PASS_TIGHT_MIN_HOURS
    )
    # Band precedence. The pre-registered PARTIAL and KILL descriptions overlap
    # (a floor can both "stay above 3 x R" and "fall >= 50% below the keeper's
    # effective bound"). PARTIAL is the MORE SPECIFIC band, so it takes
    # precedence when its condition holds. This cannot flatter the mechanism:
    # PARTIAL and KILL carry the SAME operational consequence (NO solve), so the
    # precedence changes only how much the label reports, never the decision.
    if k1_pass:
        k1 = "PASS"
    elif reduction >= K1_PARTIAL_MIN_REDUCTION_FRAC:
        k1 = "PARTIAL"
    else:
        k1 = "KILL"

    # ---- K2 ---------------------------------------------------------------
    bite_pp = {}
    for b in range(int(hour_bin.max()) + 1):
        sel = hour_bin == b
        bite_pp[b] = 100.0 * (
            1.0 - float(constrained_eff[sel].mean() / keeper_eff[sel].mean())
        )
    tight_bite = bite_pp[max(bite_pp)]
    k2 = (
        "PASS"
        if tight_bite >= K2_MIN_TIGHT_BITE_PP
        else "KILL (inert where it matters)"
    )

    k3 = "PASS (fleet physics + model dispatch only)"

    # ---- pjm-82 reproduction (diagnostic, not gated) ----------------------
    lo, hi = PJM82_MEASURED_ONLINE_TARGET_GW
    print("  -- pjm-82 premise, on the CURRENT keeper (diagnostic, not gated) --")
    print(
        f"     effective supply / measured SR+REG target "
        f"({lo}-{hi} GW): {keeper_eff.mean() / (hi * 1e3):.1f}-"
        f"{keeper_eff.mean() / (lo * 1e3):.1f}x   "
        f"(pjm-82 recorded {PJM82_MEASURED_SURPLUS_MULTIPLE[0]}-"
        f"{PJM82_MEASURED_SURPLUS_MULTIPLE[1]}x)"
    )
    print(
        "     tight-quartile bite (slack -> tight): "
        + ", ".join(f"bin{b} {bite_pp[b]:.1f}%" for b in sorted(bite_pp))
    )
    print(
        f"     tight-bin hours with S_floor <= {K1_PASS_TIGHT_REQ_MULTIPLE:.0f}x R: "
        f"{tight_under} of {int(tight.sum())}"
    )
    print(
        f"\n  K1 MAGNITUDE      {k1}   (mean S_floor = {mean_multiple:.1f}x R; "
        f"reduction vs keeper effective {100 * reduction:.1f}%)"
    )
    print(f"  K2 TIGHT-BIN BITE {k2}   ({tight_bite:.1f} pp)")
    print(f"  K3 ADMISSIBILITY  {k3}")
    verdict = "SOLVE" if (k1 == "PASS" and k2 == "PASS") else "NO SOLVE"
    print(f"\n  VERDICT: {verdict}\n")

    report = {
        "probe": "pjm125_commitment_constraint_precheck",
        "bundle": str(args.bundle),
        "year": args.year,
        "pools": int(n_r),
        "members": int(gen_idx.size),
        "fast_members": int(fast.sum()),
        "requirement_rto_mean_mw": R,
        "arms_mean_mw": {
            "ramp_bound": float(ramp_bound.mean()),
            "joint_headroom": float(head_bound.mean()),
            "keeper_effective": float(keeper_eff.mean()),
            "F_ramp_fast": float(F_ramp.mean()),
            "F_head_fast": float(F_head.mean()),
            "S_floor": float(S_floor.mean()),
            "constrained_effective": float(constrained_eff.mean()),
        },
        "ramp_binds_frac_hours": float((ramp_bound <= head_bound).mean()),
        "keeper_effective_over_req": float(keeper_eff.mean() / R),
        "s_floor_over_req_mean": mean_multiple,
        "reduction_vs_keeper_effective": reduction,
        "tight_bite_pp_by_bin": {str(b): bite_pp[b] for b in sorted(bite_pp)},
        "tight_bin_hours_under_2x_req": tight_under,
        "tight_bin_hours": int(tight.sum()),
        "pjm82_reproduction_multiple_range": [
            float(keeper_eff.mean() / (hi * 1e3)),
            float(keeper_eff.mean() / (lo * 1e3)),
        ],
        "k1": k1,
        "k2": k2,
        "k3": k3,
        "verdict": verdict,
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2))
        print(f"  wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
