"""R-ERCOT-9 phase 0: measured 2023 DAM top-of-curve offer prices by resource type (zero LP).

For online, curve-submitting resources in Aug-2023 HE15-HE20, reports the price
at which each resource's submitted DAM energy curve reaches 90 % / 100 % of its
curve MW (the top tranche), summarised by ERCOT Resource Type. Compared in the
FINDING with the keeper's 2023 carve-out peak-tranche offer levels.

Usage: ``python3 scripts/probes/_r_ercot9_dam_top_offer.py``.
Record: ``docs/handoffs/FINDING-r-ercot-9-2023-scarcity-2026-09-27.md``.
"""

import numpy as np
import pandas as pd

d = pd.read_parquet(
    "data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2023_Jul-Sep.parquet"
)
d = d[d["Delivery Date"].str.startswith("08/") & d["Hour Ending"].between(15, 20)]
mw = d[[f"QSE submitted Curve-MW{i}" for i in range(1, 11)]].to_numpy(float)
pr = d[[f"QSE submitted Curve-Price{i}" for i in range(1, 11)]].to_numpy(float)
top = np.nanmax(mw, axis=1)
ok = np.isfinite(top) & (top > 0)
d, mw, pr, top = d[ok], mw[ok], pr[ok], top[ok]


def price_at(frac):
    tgt = top * frac
    out = np.full(len(d), np.nan)
    for i in range(10):
        hit = np.isnan(out) & np.isfinite(mw[:, i]) & (mw[:, i] >= tgt - 1e-6)
        out[hit] = pr[hit, i]
    return out


d = d.assign(p90=price_at(0.90), p100=price_at(1.0), topmw=top)
g = d.groupby("Resource Type")
t = g.agg(
    n=("p100", "size"),
    mw=("topmw", "median"),
    p90_med=("p90", "median"),
    p100_med=("p100", "median"),
    p100_p75=("p100", lambda x: np.nanpercentile(x, 75)),
)
# MW-weighted share of the top 10 % of curve offered >= $1,000
d["hi"] = (d.p100 >= 1000) * d.topmw * 0.10
t["share_top10pct_ge_1k"] = (g.hi.sum() / (g.topmw.sum() * 0.10)).round(2)
print(t.sort_values("mw", ascending=False).round(0).to_string())
