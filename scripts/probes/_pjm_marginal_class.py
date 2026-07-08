"""DIAGNOSTIC: marginal-unit class + LMP tail at PJM top summer price hours.

Reads a solved bundle's P1 dispatch and reports, for the top-N summer LMP hours
of each year: the system LMP, and the highest-merit-rank class with mw>0 (the
price-setting class). If the margin sits at mid-merit CC_REGULAR rather than a
peaker / duct-firing / oil / slack tranche, the fleet is too loose to climb into
scarcity. Throwaway.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# merit rank (low = cheap baseload, high = peaking/scarcity)
_RANK = {
    "nuclear": 0,
    "hydro": 1,
    "solar": 1,
    "wind": 1,
    "biomass": 1,
    "import": 1,
    "COAL_PRB": 2,
    "COAL_WC": 2,
    "COAL_BIT": 3,
    "CC_CHP": 4,
    "CC_REGULAR": 4,
    "ST_CHP": 5,
    "ST_GAS": 5,
    "CT_CHP": 6,
    "CT_PEAKER": 6,
    "oil": 7,
    "OTHER": 5,
}


def _system_lmp(df: pd.DataFrame) -> pd.DataFrame:
    """Demand(mw)-weighted system LMP per hour."""
    g = df.groupby("hour").apply(
        lambda x: np.average(x["lmp"], weights=np.maximum(x["mw"], 1e-6)),
        include_groups=False,
    )
    return g.rename("sys_lmp").reset_index()


def _run(bundle: Path, year: int, n: int = 50) -> None:
    p = bundle / "dispatch" / f"{year}_P1.parquet"
    if not p.exists():
        print(f"  {year}: no dispatch parquet yet")
        return
    df = pd.read_parquet(p, columns=["klass", "unit_id", "mw", "hour", "lmp"])
    # system LMP per hour = max zone LMP (the scarcity-relevant price)
    sys_lmp = df.groupby("hour")["lmp"].max()
    month = pd.date_range(
        f"{year}-01-01", periods=len(sys_lmp), freq="h"
    ).month.to_numpy()
    summer = np.isin(month, (6, 7, 8, 9))
    lmp = sys_lmp.to_numpy()
    order = np.argsort(np.where(summer, lmp, -1))[::-1][:n]
    print(f"\n==== PJM {year}: top-{n} SUMMER LMP hours ====")
    print(
        f"  LMP tail: max={lmp[order].max():.1f} min-of-top{n}={lmp[order].min():.1f} "
        f"mean={lmp[order].mean():.1f}  hours>200={int((lmp[summer] > 200).sum())} "
        f"hours>100={int((lmp[summer] > 100).sum())}"
    )
    # marginal class at those hours = highest-rank class with mw>0
    run = df[df["mw"] > 1.0].copy()
    run["rank"] = run["klass"].map(_RANK).fillna(5)
    top_set = set(order.tolist())
    sub = run[run["hour"].isin(top_set)]
    marg = sub.loc[sub.groupby("hour")["rank"].idxmax()]
    vc = marg["klass"].value_counts()
    print(f"  marginal (highest-merit-rank running) class across those {n} hours:")
    for k, c in vc.items():
        print(f"      {k:12s} {c:3d} hrs")
    # duct/peak tranche presence
    peak_tranche = sub[sub["unit_id"].str.contains("peak", case=False, na=False)]
    print(
        f"  peak/duct-tranche MWh in those hours: {peak_tranche['mw'].sum() / 1e3:.1f} GWh "
        f"({peak_tranche['hour'].nunique()} of {n} hrs have any)"
    )


def main() -> int:
    bundle = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("results/calibration/pjm91_ambient_derate")
    )
    years = [int(a) for a in sys.argv[2:]] or [2023, 2024, 2025]
    for y in years:
        _run(bundle, y)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
