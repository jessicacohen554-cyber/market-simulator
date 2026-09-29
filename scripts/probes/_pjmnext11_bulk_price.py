"""PJM-NEXT-11 audit (b) (zero LP): what sets the model's bulk (p10-p90) price, and is it too dear?

Model = the keeper's committed ``hourly/system_<y>.parquet`` P1 price and marginal emission rate,
load-weighted across zones per hour. Actual = PJM RT (the C3a bench kind), from
``data/raw/_validation-source/actual_lmp_hourly_PJM.parquet``. Both are divided by the SAME daily
delivered gas series (``derive_pjm_offer_surface._pjm_fuel_daily``, HH daily + PJM basis), so the
implied heat rate ``price / gas`` compares the two price levels with gas taken out.

The model's marginal emission rate (t/MWh) in its own bulk hours is banded into the fuel class it
implies: >= 0.85 coal, 0.45-0.85 gas steam/CT, 0.30-0.45 gas CC, < 0.30 other.
Writes ``results/calibration/_pjmnext11_bulk_price.json``.
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
from scripts.data.derive_pjm_offer_surface import _pjm_fuel_daily  # noqa: E402

BUNDLE = REPO / "results/calibration/pjmnext8_xf_span"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
OUT = REPO / "results/calibration/_pjmnext11_bulk_price.json"
QS = (0.10, 0.25, 0.50, 0.75, 0.90)
MER_BANDS = {"coal": (0.85, 9.0), "gas_st_ct": (0.45, 0.85), "gas_cc": (0.30, 0.45)}


def model_series(y: int) -> pd.DataFrame:
    """Hourly load-weighted P1 price and marginal emission rate."""
    d = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
    d = d[d["pass"] == "P1"]
    d = d.assign(pw=d.price * d.demand, ew=d.marginal_emission_rate * d.demand)
    g = d.groupby("hour")[["pw", "ew", "demand"]].sum().sort_index()
    return pd.DataFrame({"price": g.pw / g.demand, "mer": g.ew / g.demand})


def main() -> None:
    """Implied-HR quantiles and marginal-class shares per year."""
    act = pd.read_parquet(ACTUAL)
    gas = _pjm_fuel_daily()
    out = {}
    for y in range(2019, 2026):
        m = model_series(y)
        n = len(m)
        a = act[act.year == y].sort_values("hour").rt.to_numpy()[:n]
        days = pd.date_range(f"{y}-01-01", periods=n, freq="h").normalize()
        g = gas.reindex(days).to_numpy(float)
        hr_m, hr_a = m.price.to_numpy() / g, a / g
        lo, hi = np.quantile(m.price, [0.10, 0.90])
        bulk = (m.price >= lo) & (m.price <= hi)
        mer = m.mer[bulk]
        shares = {
            k: round(float(((mer >= b0) & (mer < b1)).mean()), 3)
            for k, (b0, b1) in MER_BANDS.items()
        }
        shares["other"] = round(1 - sum(shares.values()), 3)
        rec = {
            "gas_mean": round(float(np.nanmean(g)), 2),
            "implied_hr_model": {
                f"p{int(q * 100)}": round(float(np.nanquantile(hr_m, q)), 2) for q in QS
            },
            "implied_hr_actual": {
                f"p{int(q * 100)}": round(float(np.nanquantile(hr_a, q)), 2) for q in QS
            },
            "bulk_marginal_class_share_model": shares,
            "bulk_mer_mean_model": round(float(mer.mean()), 3),
        }
        out[str(y)] = rec
        print(y, rec, flush=True)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
