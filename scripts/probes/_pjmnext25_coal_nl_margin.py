"""PJM-NEXT-25 card 1b (zero LP): does real coal output above its floor track net load or margin?

Within each coal plant-year, over the plant's online hours (real output > 5 % of its LP
capacity), loading = output / LP capacity is correlated with
- net load: the keeper's system demand minus its wind + solar output (an input-level
  series: measured load, VRE dispatched at or near its available output), and
- margin: actual zonal RT LMP (DataMiner2 zone pnodes, ``_pjmnext25_ct_location.zonal``)
  minus the plant's keeper offer, and the same on actual system RT.
Partial correlations (each controlling for the other) separate a load-following band
from a price-following one. The keeper's own output is scored the same way on its own
zonal price. Capacity-weighted means over plants with >= 1,000 online hours.

Writes ``results/phase0/pjm/_pjmnext25_coal_nl_margin.json``.
Run: ``python3 scripts/probes/_pjmnext25_coal_nl_margin.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
from _pjmnext24_loading_margin import ACTUAL, HOURLY, T, YEARS, plant_hours  # noqa: E402
from _pjmnext25_ct_location import zonal  # noqa: E402

OUT = REPO / "results/phase0/pjm/_pjmnext25_coal_nl_margin.json"
MIN_H = 1000


def pcorr(y: np.ndarray, x: np.ndarray, z: np.ndarray) -> float:
    """Partial correlation of y and x given z."""
    Z = np.c_[np.ones_like(z), z]
    ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
    rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
    return float(np.corrcoef(ry, rx)[0, 1])


def net_load(y: int) -> np.ndarray:
    """Keeper system demand minus wind + solar output (MW), hour of year."""
    s = pd.read_parquet(HOURLY / f"system_{y}.parquet")
    dem = s.groupby("hour").demand.sum().reindex(range(T)).to_numpy()
    c = pd.read_parquet(HOURLY / f"class_hourly_{y}.parquet")
    vre = c[c.klass.astype(str).str.upper().str.contains("WIND|SOLAR|PV")]
    v = vre.groupby("hour").mw.sum().reindex(range(T)).fillna(0.0).to_numpy()
    return dem - v


def stats(lv: np.ndarray, nl: np.ndarray, m: np.ndarray) -> dict:
    """Raw and partial correlations of loading with net load and margin."""
    return {
        "r_nl": float(np.corrcoef(lv, nl)[0, 1]),
        "r_m": float(np.corrcoef(lv, m)[0, 1]),
        "pr_nl": pcorr(lv, nl, m),
        "pr_m": pcorr(lv, m, nl),
    }


def main() -> None:
    """Every year with the zonal RT feed on disk."""
    act = pd.read_parquet(ACTUAL)
    res: dict = {"what": "PJM-NEXT-25 card 1b: coal loading vs net load and margin."}
    for y in YEARS:
        zrt = zonal(y, "rt_hrl_lmps")
        if zrt is None:
            print(y, "zonal RT missing", flush=True)
            continue
        nl = net_load(y)
        p = plant_hours(y, act)
        p = p[(p.k == "COAL") & (p.cap > 0)].copy()
        zi = {z: i for i, z in enumerate(zrt.index)}
        p = p[p.zone.isin(zi)]
        h = p.hour.to_numpy()
        p["m_zrt"] = zrt.to_numpy()[p.zone.map(zi).astype(int).to_numpy(), h] - p.offer
        p["nl"] = nl[h]
        recs = []
        for code, g in p.groupby("plant_code"):
            on = g[g.real > 0.05 * g.cap]
            if len(on) < MIN_H:
                continue
            lv = (on.real / on.cap).to_numpy()
            r = {"plant": int(code), "cap": float(g.cap.mean())}
            r["real_zrt"] = stats(lv, on.nl.to_numpy(), on.m_zrt.to_numpy())
            r["real_srt"] = stats(lv, on.nl.to_numpy(), on.m_rt.to_numpy())
            om = g[g.mw > 0.05 * g.cap]
            if len(om) >= MIN_H:
                r["model_own"] = stats(
                    (om.mw / om.cap).to_numpy(), om.nl.to_numpy(), om.m_pz.to_numpy()
                )
            recs.append(r)
        out = {"plants": len(recs)}
        for key in ("real_zrt", "real_srt", "model_own"):
            rr = [r for r in recs if key in r]
            w = np.array([r["cap"] for r in rr])
            out[key] = {
                s: round(float(np.average([r[key][s] for r in rr], weights=w)), 3)
                for s in ("r_nl", "r_m", "pr_nl", "pr_m")
            }
        res[str(y)] = out
        print(y, json.dumps(out), flush=True)
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
