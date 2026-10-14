"""UC-1-FIX-6 repro readings for one SPP bundle-year (zero LP).

Usage: uv run python <script> <bundle_dir> <year>
Prints JSON: P1 class TWh, C3a (score_price_mean on the bundle's own zone
block), C3b (score_bundle_price_shape), C8 ST_GAS forced share (D2 summary),
CT_PEAKER marginal hours, unserved MWh, uplift share, mean reserve price, and
committed headroom at the top-100 load hours (UC bundles: integer members'
cap_mw - mw from unit_marginal, as UC-DIAG peak_headroom.py; no-UC bundles:
units with mw > 0).
"""

import json
import sys
from pathlib import Path

sys.path[:0] = [".", "src"]
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import calibration_verdict as cv  # noqa: E402
from scripts import score_bundle_price_shape as sbp  # noqa: E402

b, y = Path(sys.argv[1]), int(sys.argv[2])
h = b / "hourly"
out: dict = {"bundle": b.name, "year": y}
ch = pd.read_parquet(h / f"class_hourly_{y}.parquet")
ch = ch[ch["pass"] == "P1"]
out["twh"] = {
    k: round(float(v) / 1e6, 3)
    for k, v in ch.groupby("klass", observed=True).mw.sum().items()
    if k in ("CC_REGULAR", "ST_GAS", "CT_PEAKER", "COAL_PRB", "COAL_LIGNITE")
}
lmp = sbp.zone_lmp_block(b, y)
for z in lmp.values():
    pairs = [(p, d) for p, d in zip(z["pMon"], z["dMon"]) if p is not None]
    z["d"] = sum(d for _, d in pairs)
    z["p"] = sum(p * d for p, d in pairs) / z["d"]
bench = sbp.bench_year("SPP", y)
c3a = cv.score_price_mean(y, {"lmp": lmp}, bench, "SPP")
out["C3a"] = c3a.get("magnitude")
out["C3b"] = round(float(sbp.score_year(b, "SPP", y)["value"]), 3) if "value" in sbp.score_year(b, "SPP", y) else sbp.score_year(b, "SPP", y).get("magnitude")
leg = json.loads((b / "legitimacy_diagnostics.json").read_text())
c8 = [
    r
    for r in leg.get("diagnostics", {}).get("D2", {}).get("summary", [])
    if int(r.get("year", -1)) == y and r.get("class") == "ST_GAS"
]
out["C8_ST_GAS"] = round(100 * float(c8[0]["forced_share"]), 1) if c8 else None
s = pd.read_parquet(h / f"system_{y}.parquet")
s = s[s["pass"] == "P1"]
out["unserved_mwh"] = round(float(s.slack.sum()), 1)
out["reserve_price_mean"] = round(float(s.reserve_price.mean()), 2) if "reserve_price" in s else None
dem = s.groupby("hour").demand.sum()
pk = set(dem.sort_values().index[-100:])
um = pd.read_parquet(h / f"unit_marginal_{y}.parquet")
um = um[um["pass"] == "P1"] if "pass" in um else um
g = um.plant_group.astype(str)
out["ct_marginal_hours"] = int(um[(g == "CT_PEAKER") & (um.marginal > 0)].hour.nunique())
up = h / f"uc_uplift_{y}.parquet"
if up.exists():
    u = pd.read_parquet(up)
    rev = float((s.price * s.demand).sum())
    out["uplift_pct"] = round(100 * float(u.uplift_usd.sum()) / rev, 2)
pk_um = um[um.hour.isin(pk)].copy()
pk_um["head"] = pk_um.cap_mw - pk_um.mw
sched = h / f"uc_schedule_{y}.parquet"
head = {}
for k in ("CC_REGULAR", "ST_GAS"):
    x = pk_um[pk_um.plant_group.astype(str) == k]
    if sched.exists():
        cls = pd.read_parquet(sched)[["plant_code", "uc_class"]].drop_duplicates()
        fam = {"CC_REGULAR": "cc", "ST_GAS": "st_gas"}[k]
        ints = set(cls[cls.uc_class == fam].plant_code)
        x = x[x.plant_code.isin(ints)]
        on = x
    else:
        on = x[x.mw > 1e-6]
    per_h = on.groupby("hour")[["cap_mw", "mw", "head"]].sum()
    head[k] = {
        "online_gw": round(float(per_h.cap_mw.mean()) / 1e3, 2),
        "headroom_mw": round(float(per_h["head"].mean()), 0),
    }
out["top100_committed"] = head
print(json.dumps(out))
