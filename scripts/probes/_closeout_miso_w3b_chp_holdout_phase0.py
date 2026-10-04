#!/usr/bin/env python3
"""closeout-MISO-w3b phase 0 (ZERO LP): static reach of mustrun_chp_btm_holdout on the w3 probe.

Removes the chp=Y biomass/OTHER injection (``_eia923_frame`` row partition, monthly
energy spread flat within each month) as a negative must-run supply and walks the
w3 probe's own internal merit stack (``unit_marginal``) per hour: price response
and which classes pick up the energy. Static, so an upper bound on price.
Output: results/phase0/miso/_closeout_miso_w3b_chp_holdout_phase0.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import run_calibration_full as rc  # noqa: E402

LEG = "results/calibration/closeout_miso_w3_{y}/hourly"  # the w3 probe legs (control)
OUT = REPO / "results/phase0/miso/_closeout_miso_w3b_chp_holdout_phase0.json"
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MON = np.repeat(np.arange(12), np.array(DAYS) * 24)


def drop_mw(gen: pd.DataFrame, y: int) -> np.ndarray:
    """Hourly MW of chp=Y injected energy the holdout removes (flat within month)."""
    f = lambda d: d[d.klass.isin(rc._INJECTED_MUSTRUN_CLASSES)]  # noqa: E731
    cols = [f"m{i:02d}" for i in range(1, 13)]
    a = f(rc._eia923_frame(y, gen, "MISO", False))[cols].sum()
    b = f(rc._eia923_frame(y, gen, "MISO", True))[cols].sum()
    per_month = (a - b).to_numpy() / (np.array(DAYS) * 24)
    return per_month[MON]


def walk(u: pd.DataFrame, need: np.ndarray, price0: np.ndarray):
    """Raise supply by ``need`` MW per hour along the undispatched merit stack."""
    head = u[(u.cap_mw - u.mw) > 0.5].assign(room=lambda d: d.cap_mw - d.mw)
    head = head.sort_values(["hour", "mc"])
    newp = price0.copy()
    pick = {}
    for t, g in head.groupby("hour", sort=False):
        if need[t] <= 1:
            continue
        g = g[g.mc >= price0[t] - 1e-6]
        cum = g.room.to_numpy().cumsum()
        i = int(np.searchsorted(cum, need[t]))
        if i >= len(g):
            continue
        newp[t] = max(price0[t], float(g.mc.to_numpy()[i]))
        take = np.minimum(
            g.room.to_numpy(), np.maximum(need[t] - np.r_[0, cum[:-1]], 0)
        )
        for grp, mw in zip(g.plant_group.astype(str).to_numpy(), take):
            if mw > 0:
                pick[grp] = pick.get(grp, 0.0) + mw
    return newp, pick


def main() -> None:
    gen = rc.load_monthly_generation()
    res = {}
    for y in range(2019, 2026):
        s = pd.read_parquet(REPO / LEG.format(y=y) / f"system_{y}.parquet")
        s = s[(s["pass"] == "P1") & ~s.zone.str.startswith("MISO_external")]
        piv = s.pivot_table(index="hour", columns="zone", values="price")
        dem = s.pivot_table(index="hour", columns="zone", values="demand")
        load = dem.sum(axis=1).to_numpy()
        p0 = ((piv * dem).sum(axis=1) / dem.sum(axis=1)).to_numpy()
        u = pd.read_parquet(
            REPO / LEG.format(y=y) / f"unit_marginal_{y}.parquet",
            columns=["plant_group", "fuel", "zone", "hour", "mw", "cap_mw", "mc"],
        )
        u = u[
            (u.fuel != "import") & ~u.zone.astype(str).str.startswith("MISO_external")
        ]
        need = drop_mw(gen, y)
        p1, pick = walk(u, need, p0)
        lw = lambda x: float((x * load).sum() / load.sum())  # noqa: E731
        res[y] = {
            "drop_twh": round(float(need.sum()) / 1e6, 2),
            "dP_lw_static": round(lw(p1 - p0), 3),
            "p0_lw": round(lw(p0), 2),
            "pickup_twh": {
                k: round(v / 1e6, 2)
                for k, v in sorted(pick.items(), key=lambda kv: -kv[1])[:8]
            },
        }
        print(y, json.dumps(res[y]), flush=True)
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
