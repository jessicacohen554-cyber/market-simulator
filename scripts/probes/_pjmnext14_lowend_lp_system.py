"""PJM-NEXT-14 card 1, system grain: the LP's marginal thermal units per HOUR, low-end vs all.

Companion to ``_pjmnext14_lowend_lp.py``. Zonal P1 prices differ by more than $1 in 97 % of
2020 hours, so most zones take their price across a link and a zone-hour usually holds no
marginal unit of its own. This view pools the marginal set per hour instead: an interior
unit (``0.5 MW`` off both bounds) with ``|red_cost| <= 0.01`` from the replay bundle's
``hourly/unit_hourly_<y>.parquet``, each weighted ``1/n`` within its hour.

Run: ``python3 scripts/probes/_pjmnext14_lowend_lp_system.py <bundle_dir> <year>``
Writes ``results/calibration/_pjmnext14_lowend_lp_<y>_system.json``.
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


def main() -> None:
    """Pool the marginal set per hour and summarise by low-end definition."""
    bundle, y = Path(sys.argv[1]), int(sys.argv[2])
    cols = ["unit_id", "plant_group", "hour", "mw", "cap_mw", "mc", "red_cost"]
    u = pd.read_parquet(bundle / f"hourly/unit_hourly_{y}.parquet", columns=cols)
    u = u[u.hour < 8760]
    m = u[
        (u.mw > L.TOL_MW)
        & (u.mw < u.cap_mw - L.TOL_MW)
        & (u.red_cost.abs() <= L.TOL_RC)
    ].copy()
    m["kind"] = m.unit_id.astype(str).map(L._kind)
    m["cls"] = m.plant_group.astype(str)
    m["w"] = 1.0 / m.groupby("hour").unit_id.transform("size")
    act = pd.read_parquet(L.ACTUAL)
    rt = act[act.year == y].sort_values("hour").rt.to_numpy()[:8760]
    days = pd.date_range(f"{y}-01-01", periods=8760, freq="h").normalize()
    g = _pjm_fuel_daily().reindex(days).to_numpy(float)
    s = pd.read_parquet(bundle / f"hourly/system_{y}.parquet")
    s = s[(s["pass"].astype(str) == "P1") & (s.hour < 8760)]
    lw = (s.price * s.demand).groupby(s.hour).sum() / s.demand.groupby(s.hour).sum()
    lw = lw.reindex(range(8760)).to_numpy()
    res: dict = {"year": y}
    masks = {"all": np.ones(8760, bool), "low_delivered": rt < L.LOW_HR * g}
    for name, mask in masks.items():
        hs = np.where(mask)[0]
        mm, n = m[m.hour.isin(hs)], len(hs)
        by_ck = (mm.groupby(["cls", "kind"]).w.sum() / n).sort_values(ascending=False)
        res[name] = {
            "hours": int(n),
            "hours_with_marginal_thermal": round(mm.hour.nunique() / n, 3),
            "by_class": {
                k: round(float(v), 3)
                for k, v in (mm.groupby("cls").w.sum() / n)
                .sort_values(ascending=False)
                .head(8)
                .items()
            },
            "by_class_kind": {
                f"{a}:{b}": round(float(v), 3) for (a, b), v in by_ck.head(10).items()
            },
            "median_marginal_mc": round(float(mm.mc.median()), 2),
            "median_marginal_mc_over_delivered_gas": round(
                float((mm.mc / g[mm.hour.to_numpy()]).median()), 2
            ),
            "median_lw_model_price": round(float(np.median(lw[hs])), 2),
            "median_actual_rt": round(float(np.median(rt[hs])), 2),
            "median_actual_rt_over_delivered_gas": round(
                float(np.median(rt[hs] / g[hs])), 2
            ),
        }
    out = REPO / f"results/calibration/_pjmnext14_lowend_lp_{y}_system.json"
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
