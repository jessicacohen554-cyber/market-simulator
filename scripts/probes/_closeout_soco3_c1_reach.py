"""closeout-SOCO-3 zero-LP C1 reach of the owner's mechanism at full magnitude (upper bounds, no LP).

Edits the keeper payload's per-class model energy (gmModel) and re-scores C1 with the scorer's own score_fuelmix:
- blanket: every SOCO coal MW available in the keeper (sum cap_mw, P1) runs (sunk fuel, offer = VOM);
- budget: coal floored per plant-month at the contracted-MMBtu energy (census_plant_month.csv; same-year
  conversion, illustrative only).
Added coal displaces CC_REGULAR one-for-one (most favourable case for the CC bar). Years 2019-2024 (stocks end 2024).
"""

import base64
import gzip
import json
import re
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import calibration_verdict as cv  # noqa: E402

OUT = REPO / "docs/records/soco/closeout-soco-3"
KEEPER = REPO / "results/calibration/closeout_soco_2_span/hourly"
PRB = {6002, 6073, 6124, 6257}
t = (
    REPO / "frontend/data/backcast/runs/2026-10-03-closeout-soco-2-nuclear.js"
).read_text()
P = json.loads(
    gzip.decompress(base64.b64decode(re.search(r'="([A-Za-z0-9+/=]+)"', t).group(1)))
)
pm = pd.read_csv(OUT / "census_plant_month.csv")
ratio = (pm.c_t / pm.burn_t.where(pm.burn_t >= 1e4)).clip(lower=0, upper=2.0)
pm["budget"] = (pm.actual_mwh * ratio).fillna(0.0)
pm["d_budget"] = np.maximum(pm.model_mwh, pm.budget) - pm.model_mwh
KEYS = ["CC_REGULAR", "COAL_BIT", "COAL_PRB", "ST_GAS", "CT_PEAKER"]
rows = []
for y in range(2019, 2025):
    yb = json.load(gzip.open(REPO / f"frontend/data/backcast/bench/SOCO/{y}.json.gz"))[
        "bench"
    ]
    u = pd.read_parquet(
        KEEPER / f"unit_marginal_{y}.parquet",
        columns=["pass", "plant_code", "plant_group", "cap_mw", "mw"],
    )
    u = u[(u["pass"] == "P1") & u.plant_group.str.startswith("COAL")]
    blank = u.groupby("plant_code").cap_mw.sum() - u.groupby("plant_code").mw.sum()
    bud = pm[pm.year == y].groupby("plant").d_budget.sum()
    for form, d in (("keeper", None), ("blanket", blank), ("budget", bud)):
        yp = json.loads(json.dumps(P["years"][str(y)]))
        if d is not None:
            prb = d[d.index.isin(PRB)].sum() / 1e6
            bit = d[~d.index.isin(PRB)].sum() / 1e6
            gm = yp["gmModel"]
            gm["COAL_PRB"] = gm.get("COAL_PRB", 0) + prb
            gm["COAL_BIT"] = gm.get("COAL_BIT", 0) + bit
            gm["CC_REGULAR"] = gm["CC_REGULAR"] - (prb + bit)
        c1 = {r["key"]: r for r in cv.score_fuelmix(y, yp, yb, iso="SOCO")}
        for k in KEYS:
            r = c1.get(k)
            if r:
                rows.append(
                    dict(
                        year=y,
                        form=form,
                        cls=k,
                        status=r.get("status"),
                        share_pp=r.get("share_pp"),
                        model=r.get("model"),
                        actual=r.get("actual"),
                        detail={kk: r[kk] for kk in r if kk not in ("key",)},
                    )
                )
df = pd.DataFrame(rows)
df.drop(columns="detail").to_csv(OUT / "c1_reach.csv", index=False)
print(df[df.year == 2019].iloc[0].detail)
print(
    df.drop(columns="detail")
    .pivot_table(
        index=["year", "cls"], columns="form", values="status", aggfunc="first"
    )
    .to_string()
)
