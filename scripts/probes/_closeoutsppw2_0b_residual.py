"""Zero-LP: CC/CT MW that still takes the flat SUMMER_CLASS_DERATE on the SPP keeper.

Lane closeout-SPP-w2, plan §3.4 row 0b. On the keeper recipe (spp_mmu_offer_unavailability on)
`arrays.py` skips the flat class derate on every `_mmu_fossil` row, so the double count the wave-1
FINDING measured survives only on CC/CT rows outside the MMU fossil set. This counts them per
vintage year with the loader the solve calls. Output: results/phase0/spp/_closeoutsppw2_0b_residual.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from market_sim.config.constants import SUMMER_CLASS_DERATE  # noqa: E402
from market_sim.config.paths import set_eia860_vintage  # noqa: E402
from market_sim.data.fleet.arrays import _mmu_fossil  # noqa: E402
from market_sim.data.fleet.eia860 import load_fleet_from_csv  # noqa: E402


def main() -> None:
    """Count derated CC/CT MW inside and outside the MMU fossil set, per year."""
    out = {}
    for year in range(2019, 2026):
        set_eia860_vintage(year)
        gens = load_fleet_from_csv("SPP", year=year)
        row = {
            "derate_classes_mw": 0.0,
            "non_mmu_mw": 0.0,
            "non_mmu_derate_mw": 0.0,
            "non_mmu_fuels": {},
        }
        for g in gens:
            d = SUMMER_CLASS_DERATE.get(g.plant_group)
            if not d:
                continue
            row["derate_classes_mw"] += g.pmax_mw
            if not _mmu_fossil(g):
                row["non_mmu_mw"] += g.pmax_mw
                row["non_mmu_derate_mw"] += g.pmax_mw * d
                row["non_mmu_fuels"][g.fuel_type] = (
                    row["non_mmu_fuels"].get(g.fuel_type, 0.0) + g.pmax_mw
                )
        out[year] = {
            k: (
                round(v, 1)
                if isinstance(v, float)
                else {f: round(m, 1) for f, m in v.items()}
            )
            for k, v in row.items()
        }
        print(year, out[year])
    p = Path("results/phase0/spp/_closeoutsppw2_0b_residual.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
