"""SPP-73 M4: can SPP's P0->P1 run-length pricing bite? Zero LP.

Pre-registered in ``docs/handoffs/PRECOMMIT-spp-73-commitment-reach-2026-09-22.md`` §5.
Rebuilds the rung bundle's fleet for one year (``fleet_only``, no LP) and counts the
thermal rows carrying any commitment parameter, then evaluates the P1 startup markup
``compute_monthly_markup`` would add on an arbitrary dispatch (all rows on at pmax): if
every ``startup_cost_per_mw`` is zero the markup is identically zero whatever P0 did.

Usage: ``uv run python scripts/probes/_spp73_commitment_params_census.py --year 2020 --out <json>``
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter

import numpy as np

from market_sim.config.paths import REPO_ROOT
from market_sim.model.commitment import compute_monthly_markup


def main() -> None:
    """Rebuild one rung year's fleet and census its commitment parameters."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    bundle = (
        REPO_ROOT
        / "results/calibration"
        / ("spp71_ensemble_rung" if args.year <= 2022 else "spp71_ensemble_span")
    )
    state, _ = reconstruct_bundle_fleet(bundle, args.year, verbose=False)
    fleet, fa, cfg = state["fleet"], state["fleet_arrays"], state["config"]
    thermal = [
        g for g in fleet if g.fuel_type not in ("wind", "solar", "hydro", "nuclear")
    ]
    cnt = {
        "n_rows": len(fleet),
        "n_thermal_rows": len(thermal),
        "startup_cost_per_mw_gt0": sum(
            1 for g in thermal if float(getattr(g, "startup_cost_per_mw", 0) or 0) > 0
        ),
        "min_run_hours_gt0": sum(
            1 for g in thermal if float(getattr(g, "min_run_hours", 0) or 0) > 0
        ),
        "min_down_hours_gt0": sum(
            1 for g in thermal if float(getattr(g, "min_down_hours", 0) or 0) > 0
        ),
        "is_campd_bin_rows": sum(
            1 for g in thermal if getattr(g, "is_campd_bin", False)
        ),
        "class_commitment_overrides": getattr(cfg, "class_commitment_overrides", None),
        "gas_st_startup_cost": getattr(cfg, "gas_st_startup_cost", None),
        "rows_by_group": dict(Counter(g.plant_group for g in thermal)),
    }
    # Per (fuel, class, tranche band) breakdown of the rows carrying any parameter
    brk: dict[str, dict] = {}
    for i, g in enumerate(fleet):
        su = float(getattr(g, "startup_cost_per_mw", 0) or 0)
        mr = float(getattr(g, "min_run_hours", 0) or 0)
        if su <= 0 and mr <= 0:
            continue
        band = str(getattr(g, "unit_id", "")).split("_")[-1]
        k = f"{g.fuel_type}|{g.plant_group}|{band}"
        b = brk.setdefault(
            k,
            {
                "rows": 0,
                "pmax_mw": 0.0,
                "startup": set(),
                "min_run": set(),
                "min_down": set(),
            },
        )
        b["rows"] += 1
        b["pmax_mw"] += float(fa.pmax[i])
        b["startup"].add(su)
        b["min_run"].add(mr)
        b["min_down"].add(float(getattr(g, "min_down_hours", 0) or 0))
    cnt["breakdown"] = {
        k: {
            **v,
            "startup": sorted(v["startup"]),
            "min_run": sorted(v["min_run"]),
            "min_down": sorted(v["min_down"]),
        }
        for k, v in brk.items()
    }
    T = cfg.hours
    probe_dispatch = np.repeat(np.asarray(fa.pmax, dtype=float)[:, None], T, axis=1)
    mk = compute_monthly_markup(
        fleet,
        fa,
        probe_dispatch,
        T,
        gas_st_season_spread=cfg.gas_st_startup_spread,
        gas_st_startup_cost=getattr(cfg, "gas_st_startup_cost", False),
        chp_startup_covered=getattr(cfg, "chp_startup_covered", False),
        coal_warm_committed=getattr(cfg, "coal_warm_committed", False),
    )
    cnt["markup_abs_max"] = float(np.abs(mk).max())
    cnt["markup_nonzero_rows"] = int((np.abs(mk).max(axis=1) > 0).sum())
    print(json.dumps(cnt, indent=1, default=str))
    with open(args.out, "w") as f:
        json.dump(cnt, f, indent=1, default=str)


if __name__ == "__main__":
    main()
