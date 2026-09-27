"""SPP-93 census stage 1 (ZERO LP): dump the keeper's per-unit LP inputs for one year.

Rebuilds ``results/calibration/spp86_arm_span``'s fleet for ``--year`` with no LP
(``reconstruct_bundle_fleet``; one interpreter per year because it holds per-process caches). Writes,
for every LP unit:
- ``pmax``, the hourly availability, class, plant code and N/S zone;
- the zonal demand;
- the wind and solar potential by N/S zone (the C-3 control side).

Stage 2 (``_spp93_census.py``) relabels units West/East by ``data/raw/reference/spp_plant_reserve_zone.csv``.
Record: docs/handoffs/PRECOMMIT-spp-93-west-east-2026-09-27.md §3-§4.

Usage: ``python scripts/probes/_spp93_census_dump.py --year 2022 --out-dir <dir> [--west-east]``
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

BUNDLE = REPO / "results/calibration/spp86_arm_span"


def main() -> int:
    """Rebuild one year and dump its per-unit and per-zone inputs."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--west-east", action="store_true",
                    help="arm ScenarioConfig.spp_zone_partition='west_east' on the keeper recipe")
    a = ap.parse_args()
    if a.west_east:
        import json

        from scripts.lib.bundle_fleet import bundle_gas_price, full_run_year_kwargs
        from scripts.replay_keeper import derived_run_year_inputs
        from scripts.run_calibration import run_year

        meta = json.loads((BUNDLE / "meta.json").read_text())
        kw = full_run_year_kwargs(meta)
        kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), "spp_zone_partition": "west_east"}
        state = run_year(a.year, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, a.year),
                         **kw, **derived_run_year_inputs(BUNDLE, a.year))
        assert state["config"].spp_zone_partition == "west_east"
    else:
        from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

        state, _ = reconstruct_bundle_fleet(BUNDLE, a.year, verbose=False)
    zone_names = list(state["iso_config"].zone_names)
    fa = state["fleet_arrays"]
    n = len(np.asarray(fa.pmax))
    avail = np.broadcast_to(np.asarray(fa.availability, float).reshape(n, -1), (n, 8760))
    extra = {}
    for k in ("demand", "wind_cf", "wind_cap", "solar_cf", "solar_cap", "storage"):
        if k in state and state[k] is not None:
            try:
                extra[k] = np.asarray(state[k], float)
            except (TypeError, ValueError):
                pass
    a.out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        a.out_dir / f"census_{'we_' if a.west_east else ''}{a.year}.npz",
        pmax=np.asarray(fa.pmax, float), avail=avail.astype(np.float32),
        klass=np.asarray(fa.plant_group).astype(str), unit_ids=np.asarray(fa.unit_ids).astype(str), codes=np.asarray(fa.plant_code).astype(int),
        zone_idx=np.asarray(fa.zone_idx if hasattr(fa, "zone_idx") else fa.zone, dtype=object).astype(str),
        zones=np.asarray(zone_names), **extra,
    )
    print(a.year, n, "units; zones", zone_names)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
