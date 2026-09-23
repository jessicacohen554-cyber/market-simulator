"""SPP-73 M4 (continued): the worst-case ceiling of SPP's P0->P1 start-up channel. Zero LP.

Pre-registered context: ``docs/handoffs/PRECOMMIT-spp-73-commitment-reach-2026-09-22.md`` §5.
The P1 markup is ``startup_cost_per_mw / mean P0 run length`` (``commitment.compute_monthly_markup``),
so its largest possible value on any row is ``startup_cost_per_mw`` (a one-hour run). Per rung
year, rebuild the fleet (``fleet_only``) and report, in the RT top-88 hours, the highest P1 bid
any AVAILABLE row could carry under that worst case — whole fleet and gas only — against the
measured RT price. Forks one interpreter for all four years; ``reconstruct_bundle_fleet`` is
called once per year.

Usage: ``uv run python scripts/probes/_spp73_startup_ceiling.py --out <json>``
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, REPO_ROOT

N_TOP = 88  # SPP-72 hour set (PRECOMMIT §1)
GAS = ("gas_cc", "gas_ct", "gas_st")


def main() -> None:
    """Worst-case (one-hour-run) P1 bid ceiling in the RT top-88 hours, 2019-2022."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    out = {}
    for y in (2019, 2020, 2021, 2022):
        st, _ = reconstruct_bundle_fleet(
            REPO_ROOT / "results/calibration/spp71_ensemble_rung", y, verbose=False
        )
        fleet, fa, mc = st["fleet"], st["fleet_arrays"], np.asarray(st["mc_base"])
        su = np.array([float(getattr(g, "startup_cost_per_mw", 0) or 0) for g in fleet])
        avail = np.asarray(fa.pmax)[:, None] * np.asarray(fa.availability)
        gas = np.array([g.fuel_type in GAS for g in fleet])
        ceil = mc + su[:, None]
        ok = avail > 1e-6
        rt = lmp[lmp["year"] == y].sort_values("hour")["rt"].to_numpy(float)
        top = np.argsort(-np.where(np.isfinite(rt), rt, -np.inf), kind="stable")[:N_TOP]
        hmax = np.where(ok, ceil, -np.inf).max(axis=0)
        hmax_gas = np.where(ok & gas[:, None], ceil, -np.inf).max(axis=0)
        out[y] = {
            "rt_top_median": float(np.median(rt[top])),
            "max_bid_ceiling_top_median": float(np.median(hmax[top])),
            "max_gas_bid_ceiling_top_median": float(np.median(hmax_gas[top])),
            "mc_base_max_gas_top_median": float(
                np.median(np.where(ok & gas[:, None], mc, -np.inf).max(axis=0)[top])
            ),
            "top_hours_rt_above_fleet_ceiling": int((rt[top] > hmax[top]).sum()),
            "top_hours_rt_above_gas_ceiling": int((rt[top] > hmax_gas[top]).sum()),
            "max_startup_per_mw": float(su.max()),
        }
        print(y, out[y], flush=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
