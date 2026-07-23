"""ERCOT-99: re-analyze the cached model offer curve with the correct thermal
clearing point (total generation minus the separate wind/solar LP variables).

Reads scratch/ercot99_offer_2023.npz (from ercot99_model_offer_curve) + the
keeper sidecar.  No solve.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/ercot98_np6_hsl_fullspan"


def main() -> int:
    d = np.load(REPO / "scratch/ercot99_offer_2023.npz", allow_pickle=True)
    mc_bid = d["mc_bid"]           # (n_gen, n_missed)
    adj = d["adj"]                 # surface markup, same shape
    deliv = d["deliverable"]       # pmax*avail, same shape
    cls = d["cls"].astype(str)
    midx = d["midx"]
    hub = d["hub"]; total = d["total"]; rt = d["rt"]

    ch = pd.read_parquet(BUNDLE / "hourly/class_hourly_2023.parquet")
    ch = ch[ch["pass"] == "P1"]
    kl = ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum").fillna(0.0)
    ws = (kl["wind"] + kl["solar"]).reindex(range(8760)).to_numpy()[midx]
    clr = total - ws   # thermal+hydro clearing MW (matches the generator stack)

    n = mc_bid.shape[1]
    marg, marg_cls, below200, cushion, repriced = [], [], [], [], []
    # supply-curve shape: MW offered in price bands, and MW between margin and wall
    band_edges = [0, 50, 100, 200, 500, 1000, 5001]
    band_mw = np.zeros(len(band_edges) - 1)
    mw_marg_to_200, mw_200_to_500, mw_500_to_wall = [], [], []
    for j in range(n):
        off = mc_bid[:, j]; cap = deliv[:, j]
        order = np.argsort(off, kind="stable")
        off_s, cap_s = off[order], cap[order]
        cum = np.cumsum(cap_s)
        k = min(int(np.searchsorted(cum, clr[j])), len(off_s) - 1)
        marg.append(off_s[k]); marg_cls.append(cls[order][k])
        below200.append(cap_s[off_s < 200].sum())
        m = off_s[k]
        cushion.append(cap_s[(off_s >= m) & (off_s < 200)].sum())
        repriced.append(cap[adj[:, j] > 0].sum())
        for b in range(len(band_edges) - 1):
            band_mw[b] += cap_s[(off_s >= band_edges[b]) & (off_s < band_edges[b+1])].sum()
        # capacity ABOVE the margin in price bands (the offers between the clearing
        # point and the wall — what has to be crossed / repriced to lift price)
        above = off_s >= m
        mw_marg_to_200.append(cap_s[above & (off_s < 200)].sum())
        mw_200_to_500.append(cap_s[above & (off_s >= 200) & (off_s < 500)].sum())
        mw_500_to_wall.append(cap_s[above & (off_s >= 500)].sum())
    marg = np.array(marg)
    print(f"[cross-check] reconstructed marginal offer p50 ${np.median(marg):.1f} "
          f"mean ${marg.mean():.1f} vs sidecar hub p50 ${np.median(hub):.1f} "
          f"mean ${hub.mean():.1f}")
    print(f"[cross-check] |recon - hub| p50 ${np.median(np.abs(marg-hub)):.1f} "
          f"p90 ${np.percentile(np.abs(marg-hub),90):.1f}")
    print(f"\n[depth] over {n} missed hours (mean):")
    print(f"    thermal clearing MW              : {clr.mean():8.0f}")
    print(f"    deliverable MW offered < $200    : {np.mean(below200):8.0f}")
    print(f"    cushion MW [margin, $200)        : {np.mean(cushion):8.0f}"
          f"  <- cheap capacity above the margin, below $200")
    print(f"    MW offered [margin, $200)        : {np.mean(mw_marg_to_200):8.0f}")
    print(f"    MW offered [$200, $500)          : {np.mean(mw_200_to_500):8.0f}")
    print(f"    MW offered [$500, wall]          : {np.mean(mw_500_to_wall):8.0f}")
    print(f"    MW the surface repriced (>0)     : {np.mean(repriced):8.0f}")
    print(f"    marginal tranche class mix       : {pd.Series(marg_cls).value_counts().to_dict()}")
    print(f"\n[supply-curve shape] total deliverable MW by offer band (mean/hr over missed):")
    for b in range(len(band_edges) - 1):
        print(f"    ${band_edges[b]:4d}-{band_edges[b+1]:5d}: {band_mw[b]/n:8.0f} MW")

    # marginal-tranche within-plant position: is the margin below the cleared-share
    # boundary (unfloored) or above it?  Report tranche suffix mix at the margin.
    tr = d["tranche"].astype(str)
    marg_tr = []
    for j in range(n):
        off = mc_bid[:, j]; order = np.argsort(off, kind="stable")
        cap_s = deliv[:, j][order]; cum = np.cumsum(cap_s)
        k = min(int(np.searchsorted(cum, clr[j])), len(order) - 1)
        marg_tr.append(tr[order][k])
    print(f"\n[margin tranche suffix] {pd.Series(marg_tr).value_counts().head(10).to_dict()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
