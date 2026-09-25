"""SPP-79 phase 0 (zero LP): where the 2019-2021 C3a over-level lives.

Decomposes the keeper's load-weighted mean-price error, per year, into the
contribution of three RT-price buckets (low side RT <= $10, ordinary hours
$10 < RT < p67, upper tercile RT >= p67, split at p99), and reports the
upper tercile's implied market heat rate against Henry Hub. Reads only the
committed keeper hourlies (``results/calibration/rspp_span/hourly``) and
the committed actual LMP; solves nothing.

Record: docs/handoffs/FINDING-spp-79-c3a-is-a-cancellation-2026-09-25.md.
Note the demand weight here is the model's zonal demand, not the scorer's
bench ``rt_lw`` basis, so the annual error differs from the registered C3a
by a few points; the bucket split is the finding, not the level.
"""

from __future__ import annotations

import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

BUNDLE = "results/calibration/rspp_span/hourly"
YEARS = range(2019, 2026)


def load_year(y: int, lmp: pd.DataFrame) -> pd.DataFrame:
    """Return hourly demand-weighted model price, RT actual and month for ``y``."""
    s = pd.read_parquet(f"{BUNDLE}/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    d = s.groupby("hour").demand.sum()
    m = (s.price * s.demand).groupby(s.hour).sum() / d
    rt = lmp[lmp.year == y].set_index("hour").rt.reindex(d.index)
    mon = (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(d.index, unit="h")).month
    return pd.DataFrame({"d": d.values, "m": m.values, "rt": rt.values, "mon": mon}).dropna()


def main() -> None:
    """Print the bucket decomposition and the upper-tercile heat-rate table."""
    lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet")
    hh = pd.read_csv(RAW_DATA_DIR / "gas-prices/henry_hub_monthly.csv")
    rows = []
    for y in YEARS:
        full = load_year(y, lmp)
        h = hh[hh.year == y].price_usd_mmbtu.mean()
        for tag, df in (("all", full), ("exFeb", full[full.mon != 2])):
            D = df.d.sum()
            A = (df.d * df.rt).sum() / D
            M = (df.d * df.m).sum() / D
            q67, q99 = df.rt.quantile([0.67, 0.99])

            def contrib(mask):
                return 100 * (df.d * (df.m - df.rt))[mask].sum() / D / A

            up = df[(df.rt >= q67) & (df.rt < q99)]
            rows.append(
                {
                    "year": y, "sub": tag, "err_pct": 100 * (M / A - 1),
                    "low_le10": contrib(df.rt <= 10),
                    "ordinary": contrib((df.rt > 10) & (df.rt < q67)),
                    "upper_p67_p99": contrib((df.rt >= q67) & (df.rt < q99)),
                    "top1pct": contrib(df.rt >= q99),
                    "up_rt": up.rt.mean(), "up_model": up.m.mean(),
                    "up_rt_hr": up.rt.mean() / h, "up_model_hr": up.m.mean() / h,
                }
            )
    print(pd.DataFrame(rows).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
