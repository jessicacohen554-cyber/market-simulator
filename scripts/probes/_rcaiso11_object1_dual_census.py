"""R-CAISO-11 Object 1 (ZERO LP): what sets the level of the evening hydro dual.

R-CAISO-10 found model SP15_rest h17-22 below measured DAM TH_SP15 in every year
and middays above it; hydro is the partially-loaded setter in 30-55 % of evening
hours, so the evening price is hydro's monthly budget dual. This probe censuses the
three candidates the handoff names, per year, on the keeper's own per-year legs
(extracted from the R-CAISO-10 shard commits; gitignored, rule 31):

1. STORAGE -- is the battery fleet interior on SOC between the midday charge and
   the evening discharge (then the evening/midday price ratio is pinned near 1/eta)
   or energy/power bound (then the spread can open)? Reports the day-level SOC
   minimum after the evening, the share of days the fleet empties, and discharge
   at the observed fleet power max.
2. IMPORT LADDER -- the evening price in hours with no thermal setter vs the DSW hub.
3. RESERVE -- the evening reserve dual.

Plus the price-shape identity: daily evening-minus-midday spread, model vs DAM.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso11_object1_dual_census.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _rcaiso10_object2_price_setter import _dam_sp15  # noqa: E402

LEG = "results/calibration/rcaiso10_A_{y}"
OUT = Path("results/calibration/_rcaiso11/object1_dual_census.json")
T = 8760
D = T // 24
EVE = slice(17, 23)
MID = slice(8, 17)


def census(y: int) -> dict:
    """Per-year storage / reserve / spread census for SP15_rest."""
    leg = Path(LEG.format(y=y))
    s = pd.read_parquet(leg / f"hourly/system_{y}.parquet")
    sp = s[s.zone == "SP15_rest"].set_index("hour").reindex(range(T))
    price = sp.price.to_numpy()
    res = sp.reserve_price.to_numpy()
    dam = _dam_sp15(y)
    pday = price[: D * 24].reshape(D, 24)
    out = {
        "model_eve": round(float(np.nanmean(pday[:, EVE])), 1),
        "model_mid": round(float(np.nanmean(pday[:, MID])), 1),
        "model_spread_eve_minus_mid": round(
            float(np.nanmean(pday[:, EVE].mean(1) - pday[:, MID].mean(1))), 1
        ),
        "model_ratio_eve_over_mid_median": round(
            float(np.nanmedian(pday[:, EVE].mean(1) / np.maximum(pday[:, MID].mean(1), 1))), 2
        ),
        "reserve_price_eve": round(float(np.nanmean(res[: D * 24].reshape(D, 24)[:, EVE])), 2),
        "reserve_price_mid": round(float(np.nanmean(res[: D * 24].reshape(D, 24)[:, MID])), 2),
    }
    if dam is not None and np.isfinite(dam).sum() > 0.8 * T:
        dd = dam[: D * 24].reshape(D, 24)
        out["dam_eve"] = round(float(np.nanmean(dd[:, EVE])), 1)
        out["dam_mid"] = round(float(np.nanmean(dd[:, MID])), 1)
        out["dam_spread_eve_minus_mid"] = round(
            float(np.nanmean(dd[:, EVE].mean(1) - dd[:, MID].mean(1))), 1
        )
        out["dam_ratio_eve_over_mid_median"] = round(
            float(np.nanmedian(dd[:, EVE].mean(1) / np.maximum(dd[:, MID].mean(1), 1))), 2
        )
    st = pd.read_parquet(leg / f"hourly/storage_{y}.parquet")
    for tech, g in st.groupby("tech"):
        g = g.set_index("hour").reindex(range(T))
        soc = g.soc_mwh.to_numpy()[: D * 24].reshape(D, 24)
        cap = float(np.nanmax(g.energy_cap_mwh))
        dis = g.discharge_mw.to_numpy()[: D * 24].reshape(D, 24)
        chg = g.charge_mw.to_numpy()[: D * 24].reshape(D, 24)
        pmax = float(np.nanmax(dis))
        post = soc[:, 20:24].min(1) / cap  # SOC floor after the evening
        peak = soc[:, 12:19].max(1) / cap  # SOC ceiling at end of the solar charge
        out[f"storage_{tech}"] = {
            "energy_cap_mwh": round(cap),
            "obs_max_discharge_mw": round(pmax),
            "days_empty_after_eve_share": round(float((post < 0.02).mean()), 3),
            "days_full_before_eve_share": round(float((peak > 0.98).mean()), 3),
            "median_soc_floor_after_eve": round(float(np.median(post)), 3),
            "median_soc_ceiling_before_eve": round(float(np.median(peak)), 3),
            "eve_hours_at_power_max_share": round(float((dis[:, EVE] > 0.98 * pmax).mean()), 3),
            "eve_mean_discharge_mw": round(float(dis[:, EVE].mean())),
            "mid_mean_charge_mw": round(float(chg[:, MID].mean())),
            "daily_throughput_over_cap": round(float(dis.sum(1).mean() / cap), 2),
        }
    return out


def main() -> None:
    """Run the census over 2019-2025 and write the JSON."""
    res = {str(y): census(y) for y in range(2019, 2026)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
