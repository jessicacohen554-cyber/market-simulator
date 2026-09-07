"""miso-242 D-EDGE — split the Q-Q identity's two edges. REPORTED, GATED NOWHERE.

Declared in ``results/calibration/ADDENDUM-miso242-the-edge-decomposition-2026-09-07.md``
and pushed BEFORE it was run. It carries NO bar, NO decision rule and NO verdict, and it
cannot move Q-A's, Q-B's, Q-C's, Q-D's or Q-E's outcome -- all five are published in that
addendum's section 1 before this file is executed.

Q-A measures the SUM of the two edges of the dead band. The Q-Q estimator equates each edge
separately::

    delta_1^import = quantile( spread , 1 - P(flow > +mid_1) )
    delta_1^export = quantile( spread ,     P(flow < -mid_1) )

so ON THE DERIVE'S OWN SPREAD each exceedance should equal its own target. This splits the
Q-A residual into those two components and adds a TIE CENSUS, because ``np.quantile`` cannot
place a threshold at a nominal exceedance when the sample is heavily tied.

Rule 23 [R-FROZEN-DERIVE]: nothing here re-derives anything. The committed ladder is READ.

Usage: python3 scripts/probes/_miso242_edge_decomposition_addendum.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

OUT = REPO / "results/calibration/_miso242_edge_decomposition_addendum.json"
YEARS = (2023, 2024, 2025)


def main() -> int:
    """Compute the per-edge decomposition and the tie census. No gate, no verdict."""
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.interchange.spec import (
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
    )

    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()
    hub_col = dm.SPP_ANCHOR_HUB
    work_all = g_all.join(dm.load_spp_hub_da(), how="left")
    specs = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}

    report = {
        "probe": "miso-242 D-EDGE — the two edges of the Q-Q identity, split",
        "addendum": (
            "results/calibration/ADDENDUM-miso242-the-edge-decomposition-2026-09-07.md"
        ),
        "status": "REPORTED, GATED NOWHERE — no bar, no decision rule, no verdict",
        "zero_lp": True,
        "years": {},
    }

    for year in YEARS:
        wy = work_all.loc[year]
        out = {}
        for seam, anchor_col in (("SPP", hub_col), ("PJM", "pjm_border")):
            lad = (
                MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"]
                if seam == "SPP"
                else MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]
            )
            d_i = float(lad["import"][0])
            d_e = float(lad["export"][0])
            mid1 = 0.5 * float(specs[seam].interface_limit_mw) / SEAM_FLOW_TRANCHES
            sub = wy.dropna(subset=[anchor_col, "da", seam])
            da_d = sub["da"].to_numpy(float)
            an_d = sub[anchor_col].to_numpy(float)
            spread = da_d - an_d
            flow = sub[seam].to_numpy(float)

            # Each edge in the leg's OWN operand form (the first addendum's repair).
            p_spread_gt_imp = float(((da_d - an_d) > d_i).mean())
            p_spread_lt_exp = float((da_d < (an_d + d_e)).mean())
            p_flow_gt = float((flow > mid1).mean())
            p_flow_lt = float((flow < -mid1).mean())

            out[seam] = {
                "delta_1_import": d_i,
                "delta_1_export": d_e,
                "mid1_mw": mid1,
                "n_rows_R_D": int(len(sub)),
                "import_edge": {
                    "P_spread_gt_delta": round(p_spread_gt_imp, 4),
                    "P_flow_gt_mid1_target": round(p_flow_gt, 4),
                    "signed_residual": round(p_spread_gt_imp - p_flow_gt, 4),
                },
                "export_edge": {
                    "P_spread_lt_delta": round(p_spread_lt_exp, 4),
                    "P_flow_lt_neg_mid1_target": round(p_flow_lt, 4),
                    "signed_residual": round(p_spread_lt_exp - p_flow_lt, 4),
                },
                "tie_census": {
                    "rows_spread_exactly_on_import_threshold": int(
                        ((da_d - an_d) == d_i).sum()
                    ),
                    "rows_price_exactly_on_export_threshold": int(
                        (da_d == (an_d + d_e)).sum()
                    ),
                    "n_distinct_spread_values": int(np.unique(spread).size),
                    "n_distinct_flow_values": int(np.unique(flow).size),
                    "rows_flow_exactly_on_mid1": int(
                        ((flow == mid1) | (flow == -mid1)).sum()
                    ),
                },
                "quantile_recheck": {
                    "quantile_at_1_minus_P_flow_gt": round(
                        float(np.quantile(spread, 1.0 - p_flow_gt)), 4
                    ),
                    "quantile_at_P_flow_lt": round(
                        float(np.quantile(spread, p_flow_lt)), 4
                    ),
                },
            }
        report["years"][str(year)] = out

    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
