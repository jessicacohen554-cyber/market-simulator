"""closeout-NEISO wave 1: cross-check the EIA NE Dashboard Algonquin series against the NGWU (NGI) narrative prints.

Tests the date basis: does the dashboard's label date equal the NGI trade date (lag 0) or the next business
day (lag 1, flow-day reading)? Writes agt_dashboard_vs_ngwu.json beside this script.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

GAS = Path("data/raw/gas-prices")
dash = pd.read_csv(GAS / "algonquin_citygate_daily_eia_ne_dashboard.csv", parse_dates=["snapshot_date", "label_date"])
dash = dash.sort_values("snapshot_date").drop_duplicates("label_date", keep="last").set_index("label_date")[
    "algonquin_citygate_usd_mmbtu"
]
ngwu = pd.read_csv(GAS / "algonquin_citygate_daily.csv", parse_dates=["date"])
ngwu = ngwu[(ngwu.date.dt.year >= 2019) & (ngwu.date.dt.year <= 2025)]
out = {}
for lag in (0, 1):
    d = ngwu.assign(key=ngwu.date + pd.offsets.BDay(lag)).merge(dash.rename("dash"), left_on="key", right_index=True)
    err = (d.dash - d.algonquin_citygate_usd_mmbtu).abs()
    out[f"lag_{lag}_business_days"] = {
        "pairs": int(len(d)),
        "median_abs_diff": round(float(err.median()), 3),
        "share_within_5pct": round(float((err <= 0.05 * d.algonquin_citygate_usd_mmbtu.abs()).mean()), 3),
        "corr": round(float(np.corrcoef(d.dash, d.algonquin_citygate_usd_mmbtu)[0, 1]), 4),
        "largest_misses": d.assign(err=err).nlargest(5, "err")[["date", "algonquin_citygate_usd_mmbtu", "key", "dash"]]
        .astype(str).values.tolist(),
    }
out["dashboard_rows_by_year"] = {int(k): int(v) for k, v in dash.groupby(dash.index.year).size().items()}
Path(__file__).with_name("agt_dashboard_vs_ngwu.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
