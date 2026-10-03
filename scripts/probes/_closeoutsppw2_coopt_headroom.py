"""Zero-LP re-measure of SPP-96 T2 (energy_reserve_coopt reach) on the current SPP keeper.

Lane closeout-SPP-w2. The `energy_reserve_coopt` cell is I on SPP-96's T2 (0-11 bind hours/yr on
keeper spp94). Since then the keeper took SPP-106/107 MMU offer-side unavailability and the W0
settlement, both of which move thermal availability, so the headroom is re-read here from the
committed `unit_marginal_<year>` sidecar of `closeout_spp_nuc_span` (no fleet rebuild, no LP):
headroom_t = sum over RESERVE_FUEL_TYPES rows of (cap_mw - mw), the same construction as SPP-96 T2,
against SPP's measured cleared up-reserve MW (regup+spin+supp+rampup+uncup). Bar: SPP-96 PRECOMMIT
§4(a), >= 88 bind hours in a year. Output: results/phase0/spp/_closeoutsppw2_coopt_headroom.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.model.reserves.spec import RESERVE_FUEL_TYPES  # noqa: E402

BUNDLE = REPO / "results/calibration/closeout_spp_nuc_span"
UP_PRODUCTS = ("regup", "spin", "supp", "rampup", "uncup")
BIND_BAR_HOURS = 88


def main() -> None:
    """Per year: eligible headroom vs measured cleared up-reserve, bind hours and margins."""
    orc = pd.read_parquet(
        REPO / "data/raw/_validation-source/spp_rtbm_or_cleared_hourly.parquet"
    )
    out = {}
    for year in range(2019, 2026):
        um = pd.read_parquet(
            BUNDLE / f"hourly/unit_marginal_{year}.parquet",
            columns=["fuel", "hour", "mw", "cap_mw"],
        )
        um = um[um["fuel"].astype(str).isin(RESERVE_FUEL_TYPES)]
        h = (
            (um["cap_mw"] - um["mw"])
            .groupby(um["hour"])
            .sum()
            .reindex(range(8760))
            .fillna(0.0)
            .values
        )
        o = orc[orc.year == year].set_index("hour").reindex(range(8760))
        req = o[list(UP_PRODUCTS)].fillna(0.0).sum(axis=1).values
        has = o["regup"].notna().values
        short = (h < req) & has
        out[year] = {
            "eligible_fuels": sorted(um["fuel"].astype(str).unique()),
            "req_hours": int(has.sum()),
            "req_median_mw": round(float(np.median(req[has]))),
            "headroom_min_mw": round(float(h.min())),
            "headroom_p1_mw": round(float(np.percentile(h, 1))),
            "headroom_median_mw": round(float(np.median(h))),
            "bind_hours": int(short.sum()),
            "hours_headroom_under_2x_req": int(((h < 2 * req) & has).sum()),
            "max_shortfall_mw": round(float((req - h)[has].max()), 1),
        }
        print(year, out[year], flush=True)
    rec = {
        "bundle": BUNDLE.name,
        "bar_bind_hours": BIND_BAR_HOURS,
        "years": out,
        "clears_bar": any(v["bind_hours"] >= BIND_BAR_HOURS for v in out.values()),
    }
    p = REPO / "results/phase0/spp/_closeoutsppw2_coopt_headroom.json"
    p.write_text(json.dumps(rec, indent=1))
    print("clears_bar:", rec["clears_bar"])


if __name__ == "__main__":
    main()
