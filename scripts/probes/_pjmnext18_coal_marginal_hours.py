"""PJM-NEXT-18 card 1b (zero LP): in the hours the keeper's COAL sets the price, where is PJM's?

Reads the keeper's committed per-unit layer ``pjmnext16_A_span/hourly/unit_marginal_<y>.parquet``
(rule 15, the slim ``marginal`` flag). A "coal-set hour" is an hour whose marginal
weight (1/n per marginal unit) is >= 0.5 on COAL_* classes. For those hours, compares
the marginal coal offer and the model load-weighted P1 price with the actual RT price
and the delivered-gas-implied cost of an efficient CC (6.5 x delivered gas, NEXT-12).

If real prices in coal-set hours sit BELOW the model's coal offer, real PJM cleared
those hours on something cheaper than the model's coal (the low-end price-floor
object); if they sit AT or above it, the model's coal is priced right and the issue is
how often coal reaches the margin.

Run: ``python3 scripts/probes/_pjmnext18_coal_marginal_hours.py``
Writes ``results/phase0/pjm/_pjmnext18_coal_marginal_hours.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts/probes"))
import _pjmnext14_lowend_lp as L  # noqa: E402
from scripts.data.derive_pjm_offer_surface import _pjm_fuel_daily  # noqa: E402

HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
OUT = REPO / "results/phase0/pjm/_pjmnext18_coal_marginal_hours.json"
T = 8760
#: Share of an hour's marginal weight on coal for it to count as coal-set.
COAL_SET_WEIGHT = 0.5


def main() -> None:
    """Coal-set-hour census for 2019-2025; write the JSON artifact."""
    res: dict = {}
    act = pd.read_parquet(L.ACTUAL)
    fuel = _pjm_fuel_daily()
    for y in range(2019, 2026):
        cols = ["plant_group", "hour", "mc", "marginal", "pass"]
        u = pd.read_parquet(HOURLY / f"unit_marginal_{y}.parquet", columns=cols)
        m = u[(u.marginal == 1) & (u["pass"].astype(str) == "P1") & (u.hour < T)].copy()
        m["coal"] = m.plant_group.astype(str).str.startswith("COAL")
        m["w"] = 1.0 / m.groupby("hour").hour.transform("size")
        cw = m[m.coal].groupby("hour").w.sum()
        hrs = cw[cw >= COAL_SET_WEIGHT].index.to_numpy()
        coal_mc = m[m.coal].groupby("hour").mc.median().reindex(hrs).to_numpy()
        rt = act[act.year == y].sort_values("hour").rt.to_numpy()[:T]
        days = pd.date_range(f"{y}-01-01", periods=T, freq="h").normalize()
        g = fuel.reindex(days).to_numpy(float)
        s = pd.read_parquet(HOURLY / f"system_{y}.parquet")
        s = s[(s["pass"].astype(str) == "P1") & (s.hour < T)]
        s = s[s.zone.astype(str) != "PJM_external"]
        lw = (s.price * s.demand).groupby(s.hour).sum() / s.demand.groupby(s.hour).sum()
        lw = lw.reindex(range(T)).to_numpy()
        res[str(y)] = {
            "coal_set_hours": int(len(hrs)),
            "coal_set_share_of_year": round(len(hrs) / T, 3),
            "median_coal_marginal_offer": round(float(np.median(coal_mc)), 2),
            "median_model_lw_price": round(float(np.median(lw[hrs])), 2),
            "median_actual_rt": round(float(np.median(rt[hrs])), 2),
            "median_efficient_cc_cost": round(float(np.median(6.5 * g[hrs])), 2),
            "share_actual_below_coal_offer": round(
                float(np.mean(rt[hrs] < coal_mc)), 3
            ),
        }
        print(y, res[str(y)])
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
