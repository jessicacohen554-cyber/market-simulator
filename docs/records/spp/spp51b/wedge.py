"""SPP-51b phase 0.2b (ZERO LP): the reach of the SPP-49 R-5 Permian cohort on the
mid-load margin -- the fuel-basis refinement's own arithmetic ceiling.

Reports the cohort's share of the near-price marginal MW and the mid-load $/MWh that
would come out if its ENTIRE fuel bill went to ZERO.  That is not a proposal -- it is
the most extreme value any reference change on those plants could reach, so falling
short of the gap kills the channel without arguing about the right reference.

The P1 startup-markup half of the wedge attribution lives in ``stack.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).parent))

OUT = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "e7ea1db8-8d13-5aa9-9561-fc9c88bbd737/scratchpad/spp51b"
)
YEARS = (2023, 2024, 2025)
TOL = 0.25
# SPP-49 R-5 / SPP-46 §0.2: the Permian-connected cohort whose own F923 prints the
# screen replaced with the TX state blend, and which R-5 says may price at Waha.
PERMIAN = {58835, 56326, 55065, 3482, 6193}


def main() -> None:
    from prices import model_price, actual_rt

    for year in YEARS:
        a = np.load(OUT / f"head_arrays_{year}.npz")
        rows = pd.read_csv(OUT / f"head_rows_{year}.csv")
        mc, av, pmax = a["mc_base"], a["availability"], a["pmax"]
        hr, fuel = a["heat_rate"], a["fuel_prices"]
        dem = a["demand"]
        T = mc.shape[1]
        price = model_price("2026-09-08-spp-50-rebaseline", year)[:T]
        act = actual_rt(year)[:T]
        load = (dem.sum(axis=0) if dem.ndim == 2 else dem)[:T]
        availmw = pmax[:, None] * (av if av.ndim == 2 else av[None, :])
        pc = rows["plant_code"].to_numpy()
        isperm = np.isin(pc, list(PERMIAN))

        ok = np.isfinite(price) & np.isfinite(act) & np.isfinite(load)
        pct = np.full(T, np.nan)
        pct[ok] = pd.Series(load[ok]).rank(pct=True).to_numpy() * 100.0
        mid = np.where(ok & (pct >= 25) & (pct < 75))[0]
        near = np.abs(mc[:, mid] - price[mid][None, :]) <= TOL
        w = (near * availmw[:, mid]).sum(axis=1)
        tot = w.sum()

        mp = float(np.average(price[mid], weights=load[mid]))
        ap = float(np.average(act[mid], weights=load[mid]))
        gap = mp - ap

        print(f"\n================ {year} — mid-load 25-75 pct ================")
        print(
            f"  model ${mp:.2f}  actual ${ap:.2f}   gap ${gap:+.2f}/MWh ({100 * gap / ap:+.1f} %)"
        )
        print("  [A] SPP-49 R-5 Permian cohort reach on the mid-load margin:")
        print(
            f"      share of near-price marginal MW           {100 * w[isperm].sum() / tot:6.2f} %"
        )
        print(
            f"      cohort MW in fleet                        {pmax[isperm].sum():8,.0f} MW "
            f"of {pmax.sum():,.0f}"
        )
        # upper bound: zero out the whole cohort's fuel cost and re-price the margin
        f_now = float(
            (near * availmw[:, mid] * fuel[:, mid]).sum()
            / (near * availmw[:, mid]).sum()
        )
        hr_w = float(np.average(hr, weights=w))
        wperm = w[isperm].sum() / tot
        # the most extreme admissible basis move: the cohort's gas to $0 (not a
        # proposal -- the arithmetic ceiling of a fuel-basis refinement on it)
        print(
            f"      mid-load $/MWh removable if the WHOLE cohort's fuel went to ZERO: "
            f"${wperm * hr_w * f_now:.2f}  (need ${gap:.2f})"
        )


if __name__ == "__main__":
    main()
