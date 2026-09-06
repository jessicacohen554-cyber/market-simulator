"""miso-225 phase 0 (C) — would repricing the PJM seam on the NEIGHBOUR's own LMP move the cheap import bands at all?

The owner ruled (2026-09-06) the D-2 5(i) seam object admissible in ONE form:
imports offered at the **exporting market's own measured price** rather than at
MISO's own DA-hub quantiles, so an import's merit position depends on the
neighbour's supply cost — the real driver — instead of on the model's own price.

The defect the repair is aimed at is measured (miso-224 §4.2): in the real
sub-$20 MISO hours the keeper imports 3.23 GW and the bare-hub arm 1.45 GW
against an EIA-930 measured 4.89 GW.  For a fixed price ladder cleared
economically, that deficit can only close if the CHEAP import bands get CHEAPER.

So this is the arm's own pre-solve gate (rule 29 clause 0), and it is answerable
with no LP at all: derive the SAME Q-Q duration-coupled ladder twice, once on the
MISO hub DA (the incumbent anchor) and once on the PJM western-border DA (the
neighbour), and read the cheap bands.  If the neighbour anchor does not lower
them, the mechanism cannot do what it is being built to do and the arm never
reaches a solve.

Zero-LP.  Rule 22 ``[R-HOLDOUT]``: 2023-2025 only.  Writes
``_miso225_seam_neighbour.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data.derive_miso_seam_ladders import (  # noqa: E402
    load_joined,
    qq_export,
    qq_import,
)

OUT = REPO / "results/calibration/_miso225_seam_neighbour.json"
YEARS = (2023, 2024, 2025)


def main() -> int:
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    joined = load_joined()
    spec = {s.name: s for s in INTERFACE_NEIGHBORS["MISO"]}["PJM"]
    step = spec.interface_limit_mw / SEAM_FLOW_TRANCHES
    mids = (np.arange(SEAM_FLOW_TRANCHES) + 0.5) * step

    rec: dict[str, object] = {
        "probe": "miso-225 phase 0 C - neighbour-anchored PJM seam ladder vs the incumbent MISO-hub anchor",
        "seam": "PJM",
        "interface_limit_mw": float(spec.interface_limit_mw),
        "band_midpoints_mw": [float(m) for m in mids],
        "by_year": {},
    }
    for year in YEARS:
        g = joined.loc[year].dropna(subset=["da", "pjm_border", "PJM"])
        da = g["da"].to_numpy(float)
        nb = g["pjm_border"].to_numpy(float)
        flow = g["PJM"].to_numpy(float)
        inc = [qq_import(da, flow, m) for m in mids]
        neigh = [qq_import(nb, flow, m) for m in mids]
        # The hours the defect lives in: MISO clearing below $20.
        cheap = da < 20.0
        rec["by_year"][str(year)] = {
            "n_hours": int(len(g)),
            "anchor_means": {"miso_hub_da": float(da.mean()), "pjm_border": float(nb.mean())},
            "import_ladder_incumbent": [round(p, 2) for p in inc],
            "import_ladder_neighbour": [round(p, 2) for p in neigh],
            "delta_band": [round(n - i, 2) for n, i in zip(neigh, inc)],
            "cheapest_band_delta": round(neigh[0] - inc[0], 2),
            "mean_delta_bands_1_4": round(float(np.mean(np.array(neigh[:4]) - np.array(inc[:4]))), 2),
            "in_miso_cheap_hours": {
                "n": int(cheap.sum()),
                "miso_da_mean": round(float(da[cheap].mean()), 2),
                "pjm_border_mean": round(float(nb[cheap].mean()), 2),
                "neighbour_cheaper_share": round(float((nb[cheap] < da[cheap]).mean()), 3),
                "measured_import_mean_mw": round(float(flow[cheap].mean()), 0),
                "measured_import_mean_all_mw": round(float(flow.mean()), 0),
            },
            # Does the neighbour's price actually decouple from MISO's?  If the
            # two series move together the repair is cosmetic whatever the levels.
            "corr_neighbour_vs_miso": round(float(np.corrcoef(nb, da)[0, 1]), 3),
        }
    OUT.write_text(json.dumps(rec, indent=1))
    for year, r in rec["by_year"].items():
        c = r["in_miso_cheap_hours"]
        print(
            f"{year}: anchors MISO ${r['anchor_means']['miso_hub_da']:.2f} / PJM ${r['anchor_means']['pjm_border']:.2f}"
            f"  corr {r['corr_neighbour_vs_miso']}"
        )
        print(f"   incumbent bands {r['import_ladder_incumbent']}")
        print(f"   neighbour bands {r['import_ladder_neighbour']}")
        print(f"   delta           {r['delta_band']}   (bands 1-4 mean {r['mean_delta_bands_1_4']:+})")
        print(
            f"   MISO<$20 hours n={c['n']}: MISO ${c['miso_da_mean']} vs PJM ${c['pjm_border_mean']}, "
            f"PJM cheaper in {100 * c['neighbour_cheaper_share']:.1f}% of them; measured import "
            f"{c['measured_import_mean_mw']} MW (all hours {c['measured_import_mean_all_mw']})"
        )
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
