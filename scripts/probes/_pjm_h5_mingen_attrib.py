"""pjm-h5 (ZERO LP): attribute the coal `committed` min_gen floor to its mechanism.

The card's load-bearing premise is that PJM's coal `committed` band is UNFLOORED,
so re-pricing it moves dispatch. `assembly.py`'s two per-tranche floor seams
cannot reach it (`sync_floor` is mustrun/sync only; `cc_floor` gates on
`group in {CC_REGULAR, ST_GAS}`), yet the composed `min_gen` array carries a
small non-zero floor there. This probe reads the parallel
`min_gen_mechanism` id array (`data/floor_mechanisms.py`) and says WHICH
mechanism put it there — the rule 19 ``[R-ONE-MECH]`` question.

Run: ``python3 scripts/probes/_pjm_h5_mingen_attrib.py 2020``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REPO = Path(__file__).resolve().parents[2]
BUNDLE_FOR_YEAR = {
    2020: "pjm_d4_4_TP",
    2021: "pjm_d4_4_TP",
    2022: "pjm_d4_4_TP",
    2023: "pjm_d4_4_A",
    2024: "pjm_d4_4_A",
    2025: "pjm_d4_4_A",
}


def main() -> None:
    from market_sim.data.floor_mechanisms import MECH_NAMES
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    names = dict(MECH_NAMES)

    for y in [int(a) for a in sys.argv[1:]] or [2020]:
        bundle = REPO / "results/calibration" / BUNDLE_FOR_YEAR[y]
        meta = json.loads((bundle / "meta.json").read_text())
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(bundle, y))
        kw["pjm_da_virtual_bids"] = False
        out = run_year(
            y, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )
        fa, fleet = out["fleet_arrays"], out["fleet"]
        mg = np.asarray(fa.min_gen)
        mech = np.asarray(getattr(fa, "min_gen_mechanism", None))
        print(f"\n===== {y} =====")
        if mech is None or mech.shape != mg.shape:
            print("  no min_gen_mechanism array aligned to min_gen")
            continue
        idx = [
            i
            for i, g in enumerate(fleet)
            if g.fuel_type == "coal"
            and g.unit_id.rsplit("_", 1)[-1].startswith("committed")
        ]
        sub_mg, sub_me = mg[idx], mech[idx]
        tot = float(sub_mg.sum())
        print(f"  coal `committed`: {len(idx)} tranches, floored {tot:,.0f} MWh")
        for m in sorted(np.unique(sub_me)):
            sel = sub_me == m
            mwh = float(sub_mg[sel].sum())
            if mwh <= 0 and m == 0:
                continue
            label = names.get(int(m), f"id {int(m)}")
            print(
                f"     mech {int(m):>3} {label:<34}"
                f"{mwh:>14,.0f} MWh  {100.0 * mwh / tot if tot else 0:>6.2f}%"
                f"  cells {int(sel.sum()):,}"
            )


if __name__ == "__main__":
    main()
