"""closeout-SOCO-3 zero-LP reach of the owner's mechanism at full magnitude (upper bounds, no LP).

Two forms, both read off census_plant_month.csv (written by _closeout_soco3_takeorpay_census.py):
- (i) blanket sunk-fuel offer: every SOCO coal MW available in the keeper prices at VOM, so coal runs to its
  keeper availability (sum cap_mw) - an upper bound on coal energy.
- (ii) contract-coal energy budget: per plant-month, energy up to the contracted MMBtu (EIA-923 Page 5 C/NC/T)
  converted at the plant-month's own burn-to-generation ratio is priced at VOM; the model's coal is floored at
  that budget. The conversion reads same-year generation, so (ii) is illustrative only (rule 13 answer key).
In both, the added coal displaces CC_REGULAR one-for-one (the most favourable case for the CC bar).
"""

from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs/records/soco/closeout-soco-3"
KEEPER = REPO / "results/calibration/closeout_soco_2_span/hourly"
# keeper C1 inputs (FINDING-closeout-soco-2 §0 and the keeper's metrics): model total gen, bench total gen, CC model/bench TWh
pm = pd.read_csv(OUT / "census_plant_month.csv")
pm = pm[pm.year <= 2024]  # Page-2 stocks end 2024
ratio = (pm.c_t / pm.burn_t.where(pm.burn_t >= 1e4)).clip(
    lower=0, upper=2.0
)  # guard: months with <10 kt burn, ratio capped at 2
pm["budget_mwh"] = (pm.actual_mwh * ratio).fillna(0.0)
pm["floored_mwh"] = np.maximum(pm.model_mwh, pm.budget_mwh)
rows = []
for y, g in pm.groupby("year"):
    u = pd.read_parquet(
        KEEPER / f"unit_marginal_{y}.parquet",
        columns=["pass", "plant_group", "cap_mw", "mw"],
    )
    u = u[(u["pass"] == "P1") & u.plant_group.str.startswith("COAL")]
    rows.append(
        dict(
            year=y,
            coal_model=g.model_mwh.sum() / 1e6,
            coal_actual=g.actual_mwh.sum() / 1e6,
            coal_avail=u.cap_mw.sum() / 1e6,
            coal_budget_floor=g.floored_mwh.sum() / 1e6,
            over_actual_plant_months=int(
                ((g.budget_mwh > 1.1 * g.actual_mwh) & (g.actual_mwh > 1e4)).sum()
            ),
        )
    )
r = pd.DataFrame(rows)
r["d_blanket"] = r.coal_avail - r.coal_model
r["d_budget"] = r.coal_budget_floor - r.coal_model
r.round(2).to_csv(OUT / "budget_reach.csv", index=False)
print(r.round(2).to_string(index=False))
