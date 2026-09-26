"""neiso-119 phase 0 (d), zero LP: where does the keeper's 2019 +$3.27/MWh C3a bias live?

Joins the keeper's committed ``hourly/system_2019.parquet`` (P1 zonal prices, demand)
and ``hourly/class_hourly_2019.parquet`` to the committed actual hourly RT hub LMP
(``actual_lmp_hourly_NEISO.parquet``), system load-weighted on MODEL demand (the C3a
basis). Writes ``phase0_price_2019.json`` next to itself.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
B = REPO / "results/calibration/neiso118_span/hourly"
Y = int(sys.argv[1]) if len(sys.argv) > 1 else 2019


def main() -> None:
    s = pd.read_parquet(B / f"system_{Y}.parquet")
    s = s[s["pass"] == "P1"]
    g = s.groupby("hour")
    d = g["demand"].sum()
    p = (s["price"] * s["demand"]).groupby(s["hour"]).sum() / d
    a = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet"
    )
    a = a[a.year == Y].set_index("hour")["rt"].reindex(d.index)
    ts = pd.Timestamp(f"{Y}-01-01") + pd.to_timedelta(d.index, unit="h")
    df = pd.DataFrame(
        {"m": p.values, "a": a.values, "d": d.values, "mon": ts.month, "hod": ts.hour}
    )
    df = df.dropna()

    def lw(x):
        return float((x * df.loc[x.index, "d"]).sum() / df.loc[x.index, "d"].sum())

    tot = {"model": lw(df.m), "actual": lw(df.a)}
    W = df.d.sum()
    mon = []
    for m, x in df.groupby("mon"):
        w = x.d.sum()
        mm, aa = (x.m * x.d).sum() / w, (x.a * x.d).sum() / w
        mon.append(
            {
                "month": int(m),
                "model": round(mm, 2),
                "actual": round(aa, 2),
                "bias": round(mm - aa, 2),
                "contrib_$": round((mm - aa) * w / W, 3),
            }
        )
    hod = []
    for h, x in df.groupby("hod"):
        w = x.d.sum()
        mm, aa = (x.m * x.d).sum() / w, (x.a * x.d).sum() / w
        hod.append(
            {
                "hod": int(h),
                "model": round(mm, 2),
                "actual": round(aa, 2),
                "contrib_$": round((mm - aa) * w / W, 3),
            }
        )
    # price-level buckets by actual price: where is the bias (floor-level hours vs peaks)?
    bins = [-1e9, 20, 25, 30, 40, 60, 100, 1e9]
    df["ab"] = pd.cut(df.a, bins)
    buck = []
    for b, x in df.groupby("ab", observed=True):
        w = x.d.sum()
        buck.append(
            {
                "actual_bucket": str(b),
                "hours": int(len(x)),
                "model": round((x.m * x.d).sum() / w, 2),
                "actual": round((x.a * x.d).sum() / w, 2),
                "contrib_$": round(((x.m - x.a) * x.d).sum() / W, 3),
            }
        )

    def q(v):
        return {
            k: round(float(np.percentile(v, k)), 2)
            for k in (5, 10, 25, 50, 75, 90, 95, 99)
        }

    out = {
        "year": Y,
        "total": {k: round(v, 3) for k, v in tot.items()},
        "months": mon,
        "hod": hod,
        "actual_price_buckets": buck,
        "pct_model": q(df.m),
        "pct_actual": q(df.a),
    }
    Path(__file__).with_name(f"phase0_price_{Y}.json").write_text(
        json.dumps(out, indent=1)
    )
    print(
        json.dumps({k: out[k] for k in ("total", "pct_model", "pct_actual")}, indent=0)
    )
    for r in mon:
        print(r)
    for r in buck:
        print(r)


if __name__ == "__main__":
    main()
