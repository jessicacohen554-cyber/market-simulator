"""SPP-75 part B: rung fleet membership per plant (fleet_only rebuild, no LP).

One interpreter per year (``reconstruct_bundle_fleet`` is lru_cached). Writes, per model
unit row, plant code / class / zone / pmax / min-gen share, so part A can test
PRECOMMIT-spp-75 §2 (iii) (CAMPD gas plants absent or mis-classed in the model fleet).

Usage: ``uv run python scripts/probes/_spp75_fleet_membership.py --year 2020 --out <json>``
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np

from market_sim.config.paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))

RUNG = "hydro5_spp_floor_rung"


def main() -> None:
    """Rebuild the rung fleet for one year and dump per-unit membership."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, _ = reconstruct_bundle_fleet(
        REPO_ROOT / "results/calibration" / RUNG, a.year, verbose=False
    )
    fa = state["fleet_arrays"]
    n = len(fa.unit_ids)
    pmin = fa.pmin
    rows = []
    for i in range(n):
        rows.append(
            {
                "unit": str(fa.unit_ids[i]),
                "plant": int(fa.plant_code[i]) if fa.plant_code[i] is not None else -1,
                "klass": str(fa.plant_group[i]),
                "zone": int(fa.zone_idx[i]),
                "pmax": float(fa.pmax[i]),
                "pmin": float(np.asarray(pmin)[i]),
            }
        )
    with open(a.out, "w") as f:
        json.dump(rows, f)
    print(a.year, n, "rows")


if __name__ == "__main__":
    main()
