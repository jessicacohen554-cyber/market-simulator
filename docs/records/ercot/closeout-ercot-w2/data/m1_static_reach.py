"""Zero-LP static reach of the ERCOT vintage-membership supplement on C3a/C3b.

Per year, fit price as a monotone (PAVA) function of total reserve shortfall over
Jun-Sep keeper hours, shift each shortfall hour's shortfall down by eff*ADD MW
(added summer capability; Decker ST1/ST2 by their EIA-860 retirement months,
DeCordova CT1-4 all years) and shift its price by the fitted delta. Non-shortfall
hours unchanged (the units sit above the CC stack; merit effect ignored).
Run from the repo root; writes m1_static_reach.json next to this file.
"""

import base64
import gzip
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

BUNDLE = "results/calibration/closeout_ercot_l1_span/hourly/"
RUN_JS = "frontend/data/backcast/runs/2026-10-02-closeout-l1-coal-fuel.js"
OUT = Path(__file__).with_suffix(".json")


def pava_increasing(x, y):
    """Return (sorted x, non-decreasing least-squares fit of y on x)."""
    order = np.argsort(x)
    x = x[order]
    y = y[order].astype(float)
    vals, wts, starts = [], [], []
    for i, v in enumerate(y):
        vals.append(v)
        wts.append(1.0)
        starts.append(i)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            merged = (vals[-2] * wts[-2] + vals[-1] * wts[-1]) / (wts[-2] + wts[-1])
            weight = wts[-2] + wts[-1]
            vals.pop()
            wts.pop()
            starts.pop()
            vals[-1] = merged
            wts[-1] = weight
    fit = np.empty(len(y))
    bounds = starts + [len(y)]
    for k, v in enumerate(vals):
        fit[bounds[k] : bounds[k + 1]] = v
    return x, fit


def added_summer_mw(year, month):
    """Summer MW the supplement adds in (year, month), per EIA-860 retirements."""
    mw = 280  # DeCordova 8063 CT1-CT4
    if (year, month) < (2020, 10):
        mw += 320  # Decker Creek ST1
    if (year, month) < (2022, 3):
        mw += 404  # Decker Creek ST2
    return mw


def nrmse(model, actual):
    """Monthly NRMSE as scored by calibration_verdict._nrmse."""
    rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(model, actual)) / 12)
    return rmse / (sum(actual) / 12)


def weighted_mean(values, weights):
    """Weighted mean of two equal-length sequences."""
    return sum(v * w for v, w in zip(values, weights)) / sum(weights)


def main():
    """Compute the reach table for 2019-2025 and write it as JSON."""
    blob = re.search(r'="([^"]+)"', Path(RUN_JS).read_text()).group(1)
    run = json.loads(gzip.decompress(base64.b64decode(blob)))
    out = {}
    for year in range(2019, 2026):
        reserve = pd.read_parquet(BUNDLE + f"reserve_family_{year}.parquet")
        shortfall = reserve.groupby("hour").shortfall_mw.sum()
        system = pd.read_parquet(BUNDLE + f"system_{year}.parquet")
        system["pd"] = system.price * system.demand
        grouped = system.groupby("hour")
        demand = grouped.demand.sum()
        price = grouped.pd.sum() / demand
        month = (
            pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(price.index, "h")
        ).month
        df = pd.DataFrame(
            {"p": price, "sf": shortfall, "D": demand, "mo": month}
        ).fillna(0)
        summer = df[df.mo.isin([6, 7, 8, 9])]
        xs, fit = pava_increasing(summer.sf.values, summer.p.values)

        bench = json.load(
            gzip.open(f"frontend/data/backcast/bench/ERCOT/{year}.json.gz")
        )
        actual_mon = bench["bench"]["avgLMP"]["rt_lw_mon"]
        actual_lw = bench["bench"]["avgLMP"]["rt_lw"]
        lmp = run["years"][str(year)]["lmp"].values()
        model_mon = [
            weighted_mean([z["pMon"][k] for z in lmp], [z["dMon"][k] for z in lmp])
            for k in range(12)
        ]
        demand_mon = [sum(z["dMon"][k] for z in lmp) for k in range(12)]

        res = {}
        for eff in (0.5, 0.9):
            cf_mon = []
            for k in range(12):
                d = df[df.mo == k + 1]
                shifted = np.clip(d.sf - added_summer_mw(year, k + 1) * eff, 0, None)
                delta = np.where(
                    d.sf > 0, np.interp(shifted, xs, fit) - np.interp(d.sf, xs, fit), 0
                )
                cf_mon.append(model_mon[k] + (delta * d.D).sum() / d.D.sum())
            res[eff] = {
                "c3b": round(nrmse(cf_mon, actual_mon), 3),
                "c3a": round(
                    float(weighted_mean(cf_mon, demand_mon) / actual_lw - 1), 3
                ),
            }
        res["keeper"] = {
            "c3b": round(nrmse(model_mon, actual_mon), 3),
            "c3a": round(weighted_mean(model_mon, demand_mon) / actual_lw - 1, 3),
        }
        out[year] = res
        print(year, res)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
