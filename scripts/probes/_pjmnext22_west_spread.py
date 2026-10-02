"""PJM-NEXT-22 card 1c (zero LP): does the keeper reproduce PJM's west-minus-RTO price spread?

Card 1b found actual western zonal RT (AEP, APS) sat $2-4 below PJM-RTO in 2025, against ~0
in 2021 and 2024. The keeper's western coal is valued at its own zone dual. If the model's
west-minus-system spread misses an actual discount in the over-run years, western coal is
over-valued there by a congestion term, which would be year-specific.

Per year with a complete zonal RT year on disk, per model zone, over all hours and over the
hours the keeper's western coal runs (coal-MW weighted):

- actual spread: zonal RT (simple mean of the zone's pnodes) - PJM-RTO, median and mean;
- model spread: the zone's P1 dual - the keeper's load-weighted system price, median and mean.

Hour axis: fixed EST, Feb 29 dropped (``_pjmnext22_coal_zonal_margin.zonal_rt``).
Writes ``results/phase0/pjm/_pjmnext22_west_spread.json``.
Run: ``python3 scripts/probes/_pjmnext22_west_spread.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
from _pjmnext22_coal_zonal_margin import T, zonal_rt  # noqa: E402

HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
OUT = REPO / "results/phase0/pjm/_pjmnext22_west_spread.json"
ZONES = (
    "PJM_AEP_Ohio",
    "PJM_West_APS",
    "PJM_ComEd",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_SWMAAC",
)


def _wmed(x: np.ndarray, w: np.ndarray) -> float:
    """Weighted median."""
    o = np.argsort(x)
    c = np.cumsum(w[o])
    return float(x[o][np.searchsorted(c, 0.5 * c[-1])])


def year(y: int) -> dict | None:
    """One year's model vs actual zone spreads."""
    zr = zonal_rt(y)
    if zr is None:
        return None
    zz, rto = zr
    s = pd.read_parquet(
        HOURLY / f"system_{y}.parquet", columns=["zone", "hour", "price", "demand"]
    )
    s = s[(s.hour < T) & (s.zone.astype(str) != "PJM_external")]
    s["zone"] = s.zone.astype(str)
    s["pd"] = s.price * s.demand
    g = s.groupby("hour")[["pd", "demand"]].sum()
    msys = (g.pd / g.demand).reindex(range(T)).to_numpy()
    mz = s.pivot(index="zone", columns="hour", values="price").reindex(columns=range(T))
    u = pd.read_parquet(
        HOURLY / f"unit_marginal_{y}.parquet",
        columns=["plant_group", "zone", "hour", "mw"],
    )
    u = u[u.plant_group.astype(str).str.startswith("COAL") & (u.hour < T)]
    u["zone"] = u.zone.astype(str)
    cw = u.groupby(["zone", "hour"]).mw.sum()
    res = {}
    for z in ZONES:
        if z not in zz.index or z not in mz.index:
            continue
        a = zz.loc[z].to_numpy() - rto
        m = mz.loc[z].to_numpy() - msys
        w = cw.get(z, pd.Series(dtype=float)).reindex(range(T)).fillna(0.0).to_numpy()
        r = {
            "actual_median": round(float(np.median(a)), 2),
            "model_median": round(float(np.median(m)), 2),
            "actual_mean": round(float(np.mean(a)), 2),
            "model_mean": round(float(np.mean(m)), 2),
        }
        if w.sum() > 0:
            r["coal_twh"] = round(float(w.sum()) / 1e6, 1)
            r["actual_coalw_median"] = round(_wmed(a, w), 2)
            r["model_coalw_median"] = round(_wmed(m, w), 2)
            r["actual_coalw_mean"] = round(float((a * w).sum() / w.sum()), 2)
            r["model_coalw_mean"] = round(float((m * w).sum() / w.sum()), 2)
        res[z] = r
    res["system"] = {
        "model_minus_rto_median": round(float(np.median(msys - rto)), 2),
        "model_minus_rto_mean": round(float(np.mean(msys - rto)), 2),
    }
    return res


def main() -> None:
    """Every year with zonal data."""
    out: dict = {
        "what": "PJM-NEXT-22 card 1c: zone-minus-system spread, model vs actual. ZERO LP."
    }
    for y in range(2019, 2026):
        r = year(y)
        if r is None:
            continue
        out[str(y)] = r
        print(y, "system", r["system"])
        for z in ("PJM_AEP_Ohio", "PJM_West_APS"):
            print("   ", z, r.get(z))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
