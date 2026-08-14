"""pjm-161 ex-ante: footprint of a REMOVE-ONLY, TOTAL-outage PJM availability cap.

WHY THIS IS NOT A RE-TEST OF THE pjm-145 `G` CELL. pjm-145 refused
`pjm_dam_availability` as built, on two measured grounds: (i) the overlay is
~entirely its RESTORE leg (restore 364/364/360 covered days, remove 0/0/5), and
(ii) 66-68 % of that restore is STRUCTURAL-ZERO RESURRECTION — units the finer
CAMPD record holds at zero, revived to lambda by the water-fill's `_flat`
branch. Both grounds attach to the restore direction.

This probe measures a DIFFERENT construction, on NEW evidence (pjm-161 Phase 0:
the CAMPD envelope is anti-correlated with net load at r = -0.68..-0.77 in
every year, and asserts its LOWEST outage of 2022 during Winter Storm Elliott,
15.6 GW against PJM's own published 31-41 GW):

  1. **TOTAL outages, not UNPLANNED.** `PJM_OUTAGE_DEFAULT_TYPES` is
     ("forced", "maintenance") — it EXCLUDES planned outages while the model's
     CAMPD envelope includes them. That definitional mismatch mechanically
     forces restore-on-every-day, which is pjm-145 ground (i). Comparing like
     with like (forced + maintenance + planned) removes it.
  2. **REMOVE-ONLY.** The cap never restores, so the `_flat` resurrection
     branch is unreachable and pjm-145 ground (ii) cannot arise by
     construction.

Together those make the mechanism an ERCOT-148/149-shaped EVENT CAP, which is
re-open route (3) named by pjm-145 itself.

Measured here, BEFORE any LP and before the flag is written:
  * how many class-days the remove-only cap would bind on, and how much MW it
    removes (is it inert? is it a bulldozer?);
  * the same figures for the pjm-145 (unplanned-only, bidirectional) form, so
    the two constructions are separated by measurement, not assertion;
  * that the restore leg is EXACTLY zero under remove-only.

No LP: `fleet_only=True` exits before the matrix builder.

Run:  PYTHONPATH=. uv run python scripts/probes/_pjm161_removeonly_exante.py
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

KEEPER = REPO / "results/calibration/pjm152_collapse_A"
OUT_PATH = REPO / "results/calibration/_pjm161_removeonly_exante.json"
YEARS = (2023, 2024, 2025)

ALL_TYPES = ("forced", "maintenance", "planned")
UNPLANNED = ("forced", "maintenance")


def _run_year_kwargs(meta: dict) -> dict:
    """Map the keeper meta onto ``run_calibration.run_year``'s signature.

    Same lossy-but-logged reconstruction ``_pjm145_damavail_exante`` used; both
    arms share one mapping so the arm-minus-control delta is exact.
    """
    from scripts.replay_keeper import build_kwargs
    from scripts.run_calibration import run_year

    solve_kwargs = build_kwargs(meta)
    params = set(inspect.signature(run_year).parameters)
    rename = {"commitment": "commitment_enabled", "screen_coal": "commitment_screen_coal"}
    skip = {"year", "iso", "hours", "gas_price", "ttc_overrides", "fleet_only"}
    kwargs, dropped = {}, []
    for k, v in solve_kwargs.items():
        k2 = rename.get(k, k)
        if k2 in params and k2 not in skip:
            kwargs[k2] = v
        else:
            dropped.append(k)
    print(f"[map] {len(kwargs)} kwargs bound; dropped: {len(dropped)}")
    return kwargs


def main() -> None:
    from market_sim.data.pjm_outages import (
        PJM_OUTAGE_COVERED_GROUPS,
        pjm_dam_availability_series,
    )
    from scripts.run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    base_kwargs = _run_year_kwargs(meta)
    gas_prices = meta.get("gas_prices", {})

    result: dict = {"years": {}}
    for yr in YEARS:
        gas = float(gas_prices.get(str(yr), gas_prices.get(yr, 0.0)))
        state = run_year(yr, "PJM", 8760, gas, {}, fleet_only=True, **base_kwargs)
        fa = state["fleet_arrays"]
        groups = np.array([str(g) for g in fa.plant_group])
        pmax = np.asarray(fa.pmax, dtype=float)
        av = np.asarray(fa.availability, dtype=float)
        n_days = av.shape[1] // 24

        targets = {
            "total": pjm_dam_availability_series(yr, outage_types=ALL_TYPES),
            "unplanned": pjm_dam_availability_series(yr, outage_types=UNPLANNED),
        }

        # BOUNDARY CHECK (the pjm-145 ground that survives into the remove
        # direction). PJM publishes ONE whole-fleet outage aggregate, but
        # pjm_dam_availability_series divides it by the model's FOSSIL-THERMAL
        # nameplate only, so any non-fossil outage MW in the published number is
        # attributed to fossil. Measure both sides in MW so the over-attribution
        # is a number, not an argument: the model's own asserted outage MW on
        # the covered (fossil) classes vs on everything else.
        cov_mask = np.isin(groups, sorted(PJM_OUTAGE_COVERED_GROUPS))
        ad_all = av[:, : n_days * 24].reshape(av.shape[0], n_days, 24).mean(axis=2)
        model_out_mw = ((1.0 - ad_all) * pmax[:, None])  # (n, days)
        model_out_cov = model_out_mw[cov_mask].sum(axis=0)
        model_out_noncov = model_out_mw[~cov_mask].sum(axis=0)
        from market_sim.data.pjm_outages import pjm_outage_mw_series

        pub_tot = pjm_outage_mw_series(yr, 8760, "PJM RTO", ALL_TYPES)
        pub_day = pub_tot[: n_days * 24].reshape(n_days, 24).mean(axis=1)
        fin = np.isfinite(pub_day)
        result.setdefault("boundary", {})[yr] = {
            "fossil_cap_MW": float(pmax[cov_mask].sum()),
            "nonfossil_cap_MW": float(pmax[~cov_mask].sum()),
            "model_out_MW_covered_mean": float(model_out_cov.mean()),
            "model_out_MW_noncovered_mean": float(model_out_noncov.mean()),
            "published_total_MW_mean": float(pub_day[fin].mean()),
            "published_minus_model_noncov_MW_mean": float(
                (pub_day[fin] - model_out_noncov[fin]).mean()
            ),
            "nonfossil_share_of_published_if_model_right": float(
                model_out_noncov[fin].mean() / max(pub_day[fin].mean(), 1.0)
            ),
        }

        yr_out: dict = {}
        for basis, meas in targets.items():
            bind_days = 0
            cover_days = 0
            removed_mw = np.zeros(n_days)
            restore_days = 0
            restore_mw = np.zeros(n_days)
            for cls in sorted(PJM_OUTAGE_COVERED_GROUPS):
                idx = np.flatnonzero(groups == cls)
                if idx.size == 0 or cls not in meas:
                    continue
                cap = pmax[idx]
                cap_sum = float(cap.sum())
                if cap_sum <= 0:
                    continue
                ad = av[idx, : n_days * 24].reshape(idx.size, n_days, 24).mean(axis=2)
                cur = (ad * cap[:, None]).sum(axis=0) / cap_sum  # (days,)
                t = meas[cls][: n_days * 24].reshape(n_days, 24).mean(axis=1)
                covered = np.isfinite(t)
                rem = covered & (t < cur)
                res = covered & (t >= cur)
                cover_days = max(cover_days, int(covered.sum()))
                bind_days = max(bind_days, int(rem.sum()))
                restore_days = max(restore_days, int(res.sum()))
                removed_mw += np.where(rem, (cur - t) * cap_sum, 0.0)
                restore_mw += np.where(res, (t - cur) * cap_sum, 0.0)
            yr_out[basis] = {
                "covered_days": cover_days,
                "remove_days": bind_days,
                "restore_days": restore_days,
                "removed_MW_mean_over_year": float(removed_mw.mean()),
                "removed_MW_mean_on_binding_days": float(
                    removed_mw[removed_mw > 0].mean() if (removed_mw > 0).any() else 0.0
                ),
                "removed_MW_max": float(removed_mw.max()),
                "would_restore_MW_mean": float(restore_mw.mean()),
            }
        result["years"][yr] = yr_out

    print()
    print("=" * 96)
    print("pjm-161 EX-ANTE — remove-only cap footprint, by outage-type basis (no LP)")
    print("=" * 96)
    hdr = f"{'year':>6} {'basis':>10} {'cov d':>6} {'REMOVE d':>9} {'restore d':>10} "
    hdr += f"{'rm MW/yr':>10} {'rm MW/bind d':>13} {'rm MW max':>10} {'(restore MW)':>13}"
    print(hdr)
    for yr, blk in result["years"].items():
        for basis, v in blk.items():
            print(
                f"{yr:>6} {basis:>10} {v['covered_days']:>6} {v['remove_days']:>9} "
                f"{v['restore_days']:>10} {v['removed_MW_mean_over_year']:>10,.0f} "
                f"{v['removed_MW_mean_on_binding_days']:>13,.0f} "
                f"{v['removed_MW_max']:>10,.0f} {v['would_restore_MW_mean']:>13,.0f}"
            )
    print()
    print("  REMOVE-ONLY arms the 'REMOVE d' column and discards 'restore d' entirely,")
    print("  so the pjm-145 `_flat` resurrection branch is unreachable by construction.")
    print()
    print("=" * 96)
    print("BOUNDARY — is the whole-fleet published aggregate safe to charge to fossil?")
    print("=" * 96)
    import pandas as pd

    b = pd.DataFrame(result["boundary"]).T
    print(b.T.to_string(float_format=lambda v: f"{v:,.3f}" if abs(v) < 10 else f"{v:,.0f}"))
    OUT_PATH.write_text(json.dumps(result, indent=1) + "\n")
    print(f"\nwrote {OUT_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    main()
