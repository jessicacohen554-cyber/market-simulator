"""SPP-103 phase 0 (zero LP): what a price fix paired with the SPP-102 posture must carry.

Splits the posture's price effect (SPP-102 arm minus the keeper
``2026-09-28-spp-100-chp-scope``) and the arm's own C3a error into three RT
buckets per year (low side RT <= $10, ordinary $10 < RT < p67, upper tercile
RT >= p67), with SPP-79's construction. Reads the keeper's committed hourlies
(``results/calibration/spp100_arm_span/hourly``), the SPP-102 leg hourlies
(fetched by the parent from the legs named in the SPP-102 RESULT §5 into
``ARM_DIR``) and the committed actual LMP; solves nothing.

The demand weight is the model's zonal demand, so the level differs from the
registered C3a by a few points (SPP-79's note); the bucket split is the
object. Record: docs/handoffs/DESIGN-spp-103-pair-posture-price-fix-2026-09-29.md.
"""

from __future__ import annotations

import os
import sys

import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

KEEPER = "results/calibration/spp100_arm_span/hourly"
ARM_DIR = os.environ.get("SPP103_ARM_DIR", "")
YEARS = range(2019, 2026)


def weighted(path: str) -> pd.DataFrame:
    """Return hourly demand and demand-weighted P1 price from a system parquet."""
    s = pd.read_parquet(path)
    s = s[s["pass"] == "P1"]
    d = s.groupby("hour").demand.sum()
    m = (s.price * s.demand).groupby(s.hour).sum() / d
    return pd.DataFrame({"d": d, "m": m})


def main() -> None:
    """Print the per-year, per-bucket table of keeper error, arm error and posture delta."""
    if not ARM_DIR:
        sys.exit("set SPP103_ARM_DIR to the directory holding arm_system_<year>.parquet")
    lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet")
    rows = []
    for y in YEARS:
        k = weighted(f"{KEEPER}/system_{y}.parquet")
        a = weighted(f"{ARM_DIR}/arm_system_{y}.parquet")
        df = k.rename(columns={"m": "k"}).join(a.m.rename("a"))
        df["rt"] = lmp[lmp.year == y].set_index("hour").rt.reindex(df.index)
        df = df.dropna()
        D = df.d.sum()
        A = (df.d * df.rt).sum() / D
        q67 = df.rt.quantile(0.67)
        buckets = {"low": df.rt <= 10, "ord": (df.rt > 10) & (df.rt < q67), "up": df.rt >= q67}
        r = {"year": y, "rt_mean": A,
             "keeper_err_pct": 100 * ((df.d * df.k).sum() / D / A - 1),
             "arm_err_pct": 100 * ((df.d * df.a).sum() / D / A - 1),
             "dP_posture": (df.d * (df.a - df.k)).sum() / D}
        for b, msk in buckets.items():
            r[f"dP_{b}"] = (df.d * (df.a - df.k))[msk].sum() / D
            r[f"armerr_{b}_pct"] = 100 * (df.d * (df.a - df.rt))[msk].sum() / D / A
        rows.append(r)
    print(pd.DataFrame(rows).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
