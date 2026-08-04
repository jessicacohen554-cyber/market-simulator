"""ITEM 2 — decompose C3a's residual on the nyiso-125 keeper, scorer-side.

No solve. Reads the committed keeper bundle's ``hourly/system_<year>.parquet``
and the committed actual hourly RT series, and reproduces the scorer's C3a
load-weighted basis exactly (validated against the committed ``rt_lw`` bench
scalar) before splitting the residual by month, hour-of-day and zone.

Basis discipline (CLAUDE.md, five NYISO price bases are never blended): every
level quoted here is the scorer's ``rt_lw`` basis and nothing else.
Hour -> month uses the repo's fixed non-leap 8760 calendar.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.data.fleet import _hour_to_month_index  # noqa: E402

BUNDLE = REPO / "results/calibration/nyiso125_seam_A"
CONTROL = REPO / "results/calibration/nyiso125_control"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"


def model_frame(bundle: Path, year: int) -> pd.DataFrame:
    d = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return d[d["pass"] == "P1"].copy()


def actual_hourly(year: int) -> np.ndarray:
    a = pd.read_parquet(ACTUAL)
    a = a[a["year"] == year].sort_values("hour")
    return a["rt"].to_numpy(float)


def bench_rt_lw(year: int) -> tuple[float, list]:
    b = json.load(gzip.open(REPO / f"frontend/data/backcast/bench/NYISO/{year}.json.gz"))
    avg = b["bench"]["avgLMP"]
    return avg["rt_lw"], avg["rt_lw_mon"]


def wmean(p: np.ndarray, w: np.ndarray) -> float:
    return float(np.sum(p * w) / np.sum(w))


def main() -> None:
    for year in (2023, 2024, 2025):
        m = model_frame(BUNDLE, year)
        c = model_frame(CONTROL, year)
        act = actual_hourly(year)
        rt_lw, rt_lw_mon = bench_rt_lw(year)

        # system load-weighted model price per hour (the scorer's weights are
        # the same measured demand the model dispatches)
        piv_p = m.pivot_table(index="hour", columns="zone", values="price")
        piv_d = m.pivot_table(index="hour", columns="zone", values="demand")
        piv_pc = c.pivot_table(index="hour", columns="zone", values="price")
        hours = piv_p.index.to_numpy()
        P = piv_p.to_numpy(float)
        D = piv_d.to_numpy(float)
        PC = piv_pc.to_numpy(float)
        d_h = D.sum(axis=1)
        p_h = (P * D).sum(axis=1) / d_h           # model, load-weighted, hourly
        pc_h = (PC * D).sum(axis=1) / d_h
        a_h = act[: len(hours)]
        # the committed actual has interior gaps in 2025; mask to hours where
        # BOTH sides exist so every number below is a like-for-like pair.
        ok = np.isfinite(a_h) & np.isfinite(p_h)
        p_h, pc_h, a_h, d_h = p_h[ok], pc_h[ok], a_h[ok], d_h[ok]
        keep_h = np.arange(len(hours))[ok]
        print(f"   coverage: {ok.sum()}/{len(ok)} hours have a committed actual")

        model_lw = wmean(p_h, d_h)
        act_lw = wmean(a_h, d_h)
        print(f"\n{'='*72}\n{year}  keeper model rt-basis load-weighted "
              f"${model_lw:.2f}   actual reconstructed ${act_lw:.2f}   "
              f"committed bench rt_lw ${rt_lw:.2f}")
        print(f"   reconstruction check: {(act_lw/rt_lw-1)*100:+.2f}% vs committed bench")
        print(f"   C3a on committed bench: {(model_lw/rt_lw-1)*100:+.1f}%   "
              f"(control {(wmean(pc_h,d_h)/rt_lw-1)*100:+.1f}%)")

        mi = _hour_to_month_index(len(hours))[keep_h]
        gap_total = np.sum((p_h - a_h) * d_h)

        print("\n   -- by MONTH (contribution to the weighted residual) --")
        print("   mon  model$   actual$    gap$   share_of_signed_gap  load_share")
        for k in range(12):
            s = mi == k
            if not s.any():
                continue
            mp, ma = wmean(p_h[s], d_h[s]), wmean(a_h[s], d_h[s])
            contrib = np.sum((p_h[s] - a_h[s]) * d_h[s])
            print(f"   {k+1:>3}  {mp:7.2f} {ma:8.2f} {mp-ma:8.2f}"
                  f"      {contrib/gap_total*100:7.1f}%   "
                  f"{d_h[s].sum()/d_h.sum()*100:6.1f}%")

        hod = keep_h % 24
        print("\n   -- by HOUR-OF-DAY --")
        print("   hod  model$   actual$    gap$   share_of_signed_gap")
        for h in range(24):
            s = hod == h
            mp, ma = wmean(p_h[s], d_h[s]), wmean(a_h[s], d_h[s])
            contrib = np.sum((p_h[s] - a_h[s]) * d_h[s])
            print(f"   {h:>3}  {mp:7.2f} {ma:8.2f} {mp-ma:8.2f}      "
                  f"{contrib/gap_total*100:7.1f}%")

        print("\n   -- by ACTUAL-PRICE DECILE (where in the price distribution) --")
        q = np.quantile(a_h, np.linspace(0, 1, 11))
        print("   dec   act_range        model$   actual$    gap$   share")
        for i in range(10):
            lo, hi = q[i], q[i + 1]
            s = (a_h >= lo) & (a_h <= hi if i == 9 else a_h < hi)
            if not s.any():
                continue
            mp, ma = wmean(p_h[s], d_h[s]), wmean(a_h[s], d_h[s])
            contrib = np.sum((p_h[s] - a_h[s]) * d_h[s])
            print(f"   {i+1:>3}  {lo:7.1f}-{hi:7.1f} {mp:9.2f} {ma:9.2f} "
                  f"{mp-ma:8.2f} {contrib/gap_total*100:7.1f}%")

        print("\n   -- by ZONE (model side; zonal actual is not committed) --")
        for j, z in enumerate(piv_p.columns):
            print(f"   {z:<15} model ${wmean(P[:, j], D[:, j]):7.2f}   "
                  f"load share {D[:, j].sum()/D.sum()*100:5.1f}%   "
                  f"vs control ${wmean(PC[:, j], D[:, j]):7.2f}")


if __name__ == "__main__":
    main()
