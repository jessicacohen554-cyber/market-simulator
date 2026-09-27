"""NYISO-NEXT-6 G-2 / G-3 / G-4 (ZERO LP): each arm leg vs the keeper's committed hourlies.

G-2: Long Island load-weighted P1 price (arm - keeper) >= 0 every year.
G-3: no C1 class-year moves > 0.35 TWh; |d total energy| <= 0.05 TWh (plus the
     determination check, done separately with calibration_verdict).
G-4 (reported): system load-weighted P1 price move.
Record: results/calibration/_nyisonext6_gates.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEP = {
    2021: "nyisonext3_2021",
    **{y: "nyisonext3_span" for y in (2022, 2023, 2024, 2025)},
}


def _sys(b: str, y: int) -> pd.DataFrame:
    s = pd.read_parquet(REPO / f"results/calibration/{b}/hourly/system_{y}.parquet")
    return s[s["pass"] == "P1"]


def _cls(b: str, y: int) -> pd.Series:
    c = pd.read_parquet(
        REPO / f"results/calibration/{b}/hourly/class_hourly_{y}.parquet"
    )
    if "pass" in c.columns:
        c = c[c["pass"] == "P1"]
    return c.groupby("klass")["mw"].sum() / 1e6


def year(y: int) -> dict:
    """Gate values for one year."""
    k, a = _sys(KEEP[y], y), _sys(f"nyisonext6_{y}", y)
    out = {}
    for tag, m in (
        ("LI", lambda d: d.zone == "Long_Island"),
        ("system", lambda d: d.zone == d.zone),
    ):
        pk = (k[m(k)].price * k[m(k)].demand).sum() / k[m(k)].demand.sum()
        pa = (a[m(a)].price * a[m(a)].demand).sum() / a[m(a)].demand.sum()
        out[f"{tag}_lw_price"] = {
            "keeper": round(pk, 3),
            "arm": round(pa, 3),
            "delta": round(pa - pk, 3),
        }
    ck, ca = _cls(KEEP[y], y), _cls(f"nyisonext6_{y}", y)
    d = ca.reindex(ck.index.union(ca.index), fill_value=0) - ck.reindex(
        ck.index.union(ca.index), fill_value=0
    )
    out["class_twh_delta"] = {
        i: round(float(v), 4) for i, v in d.items() if abs(v) >= 0.001
    }
    out["max_abs_class_delta_twh"] = round(float(d.abs().max()), 4)
    out["total_energy_delta_twh"] = round(float(ca.sum() - ck.sum()), 4)
    out["G2_pass"] = bool(out["LI_lw_price"]["delta"] >= -1e-9)
    out["G3_energy_pass"] = bool(
        out["max_abs_class_delta_twh"] <= 0.35
        and abs(out["total_energy_delta_twh"]) <= 0.05
    )
    return out


if __name__ == "__main__":
    ys = [int(x) for x in sys.argv[1:]] or [2021, 2022, 2023, 2024, 2025]
    res = {y: year(y) for y in ys}
    p = REPO / "results/calibration/_nyisonext6_gates.json"
    old = json.loads(p.read_text()) if p.exists() else {}
    old.update({str(y): v for y, v in res.items()})
    p.write_text(json.dumps(old, indent=1))
    print(json.dumps(res, indent=1))
