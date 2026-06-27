"""Compare acute/tail scarcity incidence across solved ERCOT bundles.

For each bundle/year: demand-weighted annual model LMP, the May 8/24/26 acute
days, and tail incidence (count of hours above $200 / $1000, and the share of
annual demand-weighted $ they carry). Lets us check the forward-requirement run
(162) holds the same acute/tail behaviour as the measured-requirement run (159).

Usage: python scripts/probes/_eval_acute_tail.py <bundle_dir> [<bundle_dir> ...]
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/user/market-simulator")


def _md(hours):
    base = pd.date_range("2023-01-01", periods=hours, freq="h")
    return base.month.to_numpy(), base.day.to_numpy()


def _model_dem(bundle, year, hours):
    sy = pd.read_parquet(bundle / "system.parquet")
    sy = sy[sy["year"] == year]
    if "pass" in sy.columns:
        nonp1 = [p for p in sy["pass"].unique() if str(p).upper() != "P1"]
        if nonp1:
            sy = sy[sy["pass"].isin(nonp1)]
    g = (
        sy.assign(pd_=sy["price"] * sy["demand"])
        .groupby("hour")
        .agg(pd_=("pd_", "sum"), d=("demand", "sum"))
    )
    model = np.full(hours, np.nan)
    dem = np.full(hours, np.nan)
    model[g.index.to_numpy()] = np.where(g["d"] > 0, g["pd_"] / g["d"], np.nan)
    dem[g.index.to_numpy()] = g["d"].to_numpy()
    return model, dem


def _dw(x, w, sel):
    s = sel & np.isfinite(x) & np.isfinite(w)
    return float(np.average(x[s], weights=w[s])) if s.any() else float("nan")


def main():
    bundles = [Path(b) for b in sys.argv[1:]]
    years = [2023, 2024, 2025]
    hours = 8760
    month, day = _md(hours)
    acute = (month == 5) & np.isin(day, [8, 24, 26])
    for bundle in bundles:
        print(f"\n=== {bundle.name} ===")
        print(
            f"{'yr':>4} {'annual':>7} {'acute':>7} "
            f"{'h>200':>6} {'h>1k':>5} {'$>200%':>7}"
        )
        for year in years:
            model, dem = _model_dem(bundle, year, hours)
            fin = np.isfinite(model) & np.isfinite(dem)
            tot_dollar = float(np.nansum(model[fin] * dem[fin]))
            hi = fin & (model > 200)
            hi_dollar = float(np.nansum(model[hi] * dem[hi]))
            print(
                f"{year:>4} {_dw(model, dem, np.ones(hours, bool)):>7.2f} "
                f"{_dw(model, dem, acute):>7.2f} "
                f"{int(hi.sum()):>6} {int((fin & (model > 1000)).sum()):>5} "
                f"{100 * hi_dollar / tot_dollar if tot_dollar else 0:>6.1f}%"
            )


if __name__ == "__main__":
    main()
