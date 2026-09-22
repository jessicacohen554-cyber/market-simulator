"""SPP-71 — PRE-SOLVE VERIFICATION of the ensemble coal synchronization floor.

ZERO LP.  Rebuilds keeper 14's own fleet through the sanctioned ``fleet_only``
reconstruction (control), then re-implements BOTH placements of the coal
synchronization floor from the same primitives:

* **window** (today) — ``pmin_p`` on the top ``round(frac_p x 8760)`` hours by
  the window series, 0 elsewhere;
* **ensemble** (the arm) — ``pmin_p x frac_p`` in every hour;

both clipped to ``pmax_p x availability_p(t)`` exactly as ``_compose_min_gen_
floors`` clips them.  The reimplementation is VALIDATED against the bundle's own
realised ``fleet_arrays.min_gen`` on the coal rows before either result is
quoted — a counterfactual is only trustworthy where the instrument reproduces
the incumbent (the ``_spp70_meritorder_counterfactual`` discipline).

What it answers that the aggregate sizing cannot: the LP applies the floor PER
PLANT and clips per plant, so the realised fleet floor is at or below the
nominal ``sum(pmin x online_frac)``; and whether the two placements really do
spend the same measured annual synchronized MWh, which is the claim the
construction rests on.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.probes._spp71_phase0 import BUNDLES  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=[2025])
    ap.add_argument(
        "--npz-out",
        type=Path,
        default=None,
        help="Write the realised hourly window/ensemble fleet floors per year, "
        "so the sizing probe can predict from the REALISED floor rather than "
        "the nominal sum(pmin x frac).",
    )
    args = ap.parse_args()
    series: dict[str, np.ndarray] = {}

    from market_sim.data.fleet.withholding import _COAL_SYNC_FORCE_ALL
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    print(
        f"{'yr':>5} {'posture':>10} {'min MW':>9} {'p01 MW':>9} {'p05 MW':>9} "
        f"{'mean MW':>9} {'max MW':>9} {'TWh':>9}"
    )
    for y in args.years:
        bundle = REPO / "results" / "calibration" / BUNDLES[y]
        state, _meta = reconstruct_bundle_fleet(bundle, y, verbose=False)
        fa = state["fleet_arrays"]
        gens = list(state["fleet"])
        T = np.asarray(fa.min_gen).shape[1]

        pmax = np.asarray(fa.pmax, dtype=float)
        avail = np.asarray(fa.availability, dtype=float)
        if avail.ndim == 1:
            avail = np.broadcast_to(avail[:, None], (len(pmax), T))
        cap = pmax[:, None] * avail

        # The shared window series the coal block ranks on: system load.
        demand = np.asarray(state["demand"], dtype=float)
        load_shape = demand.sum(axis=0) if demand.ndim == 2 else demand
        load_rank = np.argsort(-load_shape, kind="stable")

        win = np.zeros((len(gens), T))
        ens = np.zeros((len(gens), T))
        n_coal = 0
        for i, g in enumerate(gens):
            pmin_mw = float(getattr(g, "coal_sync_pmin_mw", 0.0) or 0.0)
            if pmin_mw <= 0.0:
                continue
            frac = float(getattr(g, "coal_sync_online_frac", 1.0) or 0.0)
            if frac <= 0.0:
                continue
            n_coal += 1
            if frac >= _COAL_SYNC_FORCE_ALL:
                win[i, :] = pmin_mw
            else:
                k = int(round(frac * T))
                if k > 0:
                    win[i, load_rank[:k]] = pmin_mw
            ens[i, :] = pmin_mw * min(frac, 1.0)

        win = np.minimum(win, cap)
        ens = np.minimum(ens, cap)

        # --- validate the reimplementation against the bundle's own floor ----
        mech = np.asarray(fa.min_gen_mechanism)
        realised = np.asarray(fa.min_gen, dtype=float)
        coal_rows = np.array(
            [float(getattr(g, "coal_sync_pmin_mw", 0.0) or 0.0) > 0.0 for g in gens]
        )
        r_sum = realised[coal_rows].sum(axis=0)
        w_sum = win[coal_rows].sum(axis=0)
        resid = np.abs(r_sum - w_sum)
        print(
            f"\n--- {y}: {n_coal} coal rows carry a synchronization Pmin; "
            f"instrument vs bundle min_gen on those rows: "
            f"max |Δ| {resid.max():.1f} MW, mean |Δ| {resid.mean():.1f} MW, "
            f"r {np.corrcoef(r_sum, w_sum)[0, 1]:+.4f} "
            f"(mech ids present: {sorted(set(mech[coal_rows].ravel().tolist()))})"
        )

        e_sum = ens[coal_rows].sum(axis=0)
        for label, v in (("window", w_sum), ("ENSEMBLE", e_sum)):
            print(
                f"{y:>5} {label:>10} {v.min():>9.1f} {np.percentile(v, 1):>9.1f} "
                f"{np.percentile(v, 5):>9.1f} {v.mean():>9.1f} {v.max():>9.1f} "
                f"{v.sum() / 1e6:>9.4f}"
            )
        print(
            f"{y:>5} {'DELTA':>10} {e_sum.min() - w_sum.min():>9.1f} "
            f"{np.percentile(e_sum, 1) - np.percentile(w_sum, 1):>9.1f} "
            f"{np.percentile(e_sum, 5) - np.percentile(w_sum, 5):>9.1f} "
            f"{e_sum.mean() - w_sum.mean():>9.1f} {e_sum.max() - w_sum.max():>9.1f} "
            f"{(e_sum.sum() - w_sum.sum()) / 1e6:>9.4f}"
        )
        print(
            f"      same measured annual MWh? ensemble/window = "
            f"{e_sum.sum() / w_sum.sum():.4f}  (1.000 = placement only)"
        )
        series[f"window_{y}"] = w_sum
        series[f"ensemble_{y}"] = e_sum

    if args.npz_out:
        np.savez(args.npz_out, **series)
        print(f"\nwrote {args.npz_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
