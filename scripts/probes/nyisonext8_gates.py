"""NYISO-NEXT-8 G-2 / G-4 (ZERO LP): each arm leg vs the keeper's committed hourlies.

G-2: annual import-class TWh (arm - keeper) <= +0.01 in 2021 and 2022, the years
     where all three keeper-live static rungs rise (PRECOMMIT sec. 6).
G-4 (reported): per-zone and system load-weighted P1 price move; class TWh moves;
     import-hour min/max.
Record: results/phase0/nyiso/_nyisonext8_gates.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEP = {
    2021: "nyisonext6_2021",
    **{y: "nyisonext6_span" for y in (2022, 2023, 2024, 2025)},
}
G2_YEARS = (2021, 2022)


def _sys(b: str, y: int) -> pd.DataFrame:
    s = pd.read_parquet(REPO / f"results/calibration/{b}/hourly/system_{y}.parquet")
    return s[s["pass"] == "P1"]


def _cls(b: str, y: int) -> pd.DataFrame:
    c = pd.read_parquet(
        REPO / f"results/calibration/{b}/hourly/class_hourly_{y}.parquet"
    )
    c["klass"] = c["klass"].astype(str)
    return c[c["pass"].astype(str) == "P1"]


def year(y: int, arm_bundle: str) -> dict:
    """Gate values for one year."""
    k, a = _sys(KEEP[y], y), _sys(arm_bundle, y)
    out: dict = {"lw_price_delta": {}}
    for z in sorted(k.zone.astype(str).unique()) + ["system"]:

        def lw(d: pd.DataFrame) -> float:
            d = d if z == "system" else d[d.zone.astype(str) == z]
            w = d.demand.sum()
            # the external node carries no load: report its plain mean price
            return float((d.price * d.demand).sum() / w if w else d.price.mean())

        out["lw_price_delta"][z] = round(lw(a) - lw(k), 3)
    ck, ca = _cls(KEEP[y], y), _cls(arm_bundle, y)
    tk, ta = ck.groupby("klass").mw.sum() / 1e6, ca.groupby("klass").mw.sum() / 1e6
    idx = tk.index.union(ta.index)
    d = ta.reindex(idx, fill_value=0) - tk.reindex(idx, fill_value=0)
    out["class_twh_delta"] = {
        i: round(float(v), 4) for i, v in d.items() if abs(v) >= 0.001
    }
    ik = ck[ck.klass == "import"].groupby("hour").mw.sum()
    ia = ca[ca.klass == "import"].groupby("hour").mw.sum()
    out["import_twh"] = {
        "keeper": round(float(ik.sum()) / 1e6, 4),
        "arm": round(float(ia.sum()) / 1e6, 4),
        "delta": round(float(ia.sum() - ik.sum()) / 1e6, 4),
    }
    out["import_mw_min_max_arm"] = [round(float(ia.min())), round(float(ia.max()))]
    out["total_energy_delta_twh"] = round(float(ta.sum() - tk.sum()), 4)
    if y in G2_YEARS:
        out["G2_pass"] = bool(out["import_twh"]["delta"] <= 0.01)
    return out


if __name__ == "__main__":
    ys = [int(x) for x in sys.argv[1:]] or [2021, 2022, 2023, 2024, 2025]
    res = {y: year(y, f"nyisonext8_{y}") for y in ys}
    p = REPO / "results/phase0/nyiso/_nyisonext8_gates.json"
    old = json.loads(p.read_text()) if p.exists() else {}
    old.update({str(y): v for y, v in res.items()})
    p.write_text(json.dumps(old, indent=1))
    print(json.dumps(res, indent=1))
