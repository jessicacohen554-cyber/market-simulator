"""ERCOT-99 reach-gap diagnostic: where do the missed tail hours sit vs the
offer-surface's firing bins, and what is the model clearing there?

The keeper's offer surfaces fire by net-load percentile bin:
  * conditional PEAK surface  — edges (0.80, 0.90, 0.97) → bin 3 = >=p97 (the
    263 h/yr the log reports it binds);
  * cleared-share / RT econ floors — edges (0.25,0.50,0.70,0.80,0.90,0.97) →
    7 bins, fires progressively as net-load rises.

Charter step 2: are the missed hours even inside the top bin?  The bin edges are
ANNUAL percentiles, so an August-only wall dilutes across the year.  This probe
reconstructs the SAME net-load the solve bins on (system demand - wind - solar,
on the fleet clock) from the keeper's committed sidecars, assigns each hour its
two bins, and reports — over the MISSED tail hours — the bin distribution and the
model's clearing price by bin.  If the missed hours fall below the surface's
firing bin, the wall is never repriced there (a bin-conditioning problem); if
they sit in the firing bin yet the model still clears cheap, the wall is repriced
but never marginal (a depth problem).  No LP solve.

Net-load caveat: the solve bins on renewable POTENTIAL (cf x cap); the sidecar
carries model DISPATCH.  They differ only where renewables are curtailed — i.e.
LOW-net-load hours — so the top percentile thresholds and every tail hour's bin
are faithful (validated: the p97 bin count reproduces the logged 263 h).

Usage:
    python -m scripts.probes.ercot99_reach_gap \\
        [--bundle results/calibration/ercot98_np6_hsl_fullspan] [--year 2023]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

TAIL_THRESHOLD = 200.0
COND_EDGES = (0.80, 0.90, 0.97)  # ercot_offer_surface_conditional (peak rungs)
CS_EDGES = (0.25, 0.50, 0.70, 0.80, 0.90, 0.97)  # cleared-share / RT (econ rows)


def _sidecar(bundle: Path, year: int):
    sysdf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    p1 = sysdf[sysdf["pass"] == "P1"]
    price = p1.pivot(index="hour", columns="zone", values="price")
    demand = p1.pivot(index="hour", columns="zone", values="demand")
    hub = (price * demand).sum(axis=1) / demand.sum(axis=1)
    dem = demand.sum(axis=1)
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    klass = ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum").fillna(0.0)
    net_load = dem - klass.get("wind", 0.0) - klass.get("solar", 0.0)
    return hub.reindex(range(8760)), dem.reindex(range(8760)), net_load.reindex(range(8760)), klass


def _bins(net_load: np.ndarray, edges: tuple[float, ...]) -> np.ndarray:
    thr = np.quantile(net_load, edges)
    return np.searchsorted(thr, net_load, side="right")


def _actual_rt(year: int) -> np.ndarray:
    lmp = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet")
    return lmp[lmp["year"] == year].set_index("hour")["rt"].reindex(range(8760)).to_numpy()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ercot99_reach_gap")
    ap.add_argument("--bundle", default="results/calibration/ercot98_np6_hsl_fullspan")
    ap.add_argument("--year", type=int, default=2023)
    args = ap.parse_args(argv)
    bundle = REPO / args.bundle
    year = args.year

    hub, dem, net_load, klass = _sidecar(bundle, year)
    hub, dem, nl = hub.to_numpy(), dem.to_numpy(), net_load.to_numpy()
    rt = _actual_rt(year)

    cond_bin = _bins(nl, COND_EDGES)
    cs_bin = _bins(nl, CS_EDGES)
    n_p97 = int((cond_bin == len(COND_EDGES)).sum())
    print(f"[validate] p97 (cond bin {len(COND_EDGES)}) count = {n_p97} h "
          f"(surface logs 'tightest bin binds ~263/8760')")

    tail = rt > TAIL_THRESHOLD
    missed = tail & (hub <= TAIL_THRESHOLD)
    caught = tail & (hub > TAIL_THRESHOLD)
    print(f"[set] tail {int(tail.sum())} | missed {int(missed.sum())} | caught {int(caught.sum())}")

    print("\n[cond bins] missed-hour distribution over the PEAK-surface bins "
          "(bin 3 = >=p97, the only bin that reprices peak rungs):")
    for b in range(len(COND_EDGES) + 1):
        m = int((missed & (cond_bin == b)).sum())
        c = int((caught & (cond_bin == b)).sum())
        lab = {0: "<p80", 1: "p80-90", 2: "p90-97", 3: ">=p97"}[b]
        if m or c:
            hubmean = float(np.nanmean(hub[missed & (cond_bin == b)])) if m else float("nan")
            print(f"    bin {b} ({lab:7s}): missed {m:3d} | caught {c:3d} | model hub@missed ${hubmean:6.1f}")

    print("\n[cs bins] missed-hour distribution over the CLEARED-SHARE/RT bins "
          "(econ-row floors, finer grain):")
    for b in range(len(CS_EDGES) + 1):
        m = int((missed & (cs_bin == b)).sum())
        c = int((caught & (cs_bin == b)).sum())
        lab = {0: "<p25", 1: "p25-50", 2: "p50-70", 3: "p70-80", 4: "p80-90", 5: "p90-97", 6: ">=p97"}[b]
        if m or c:
            hubmean = float(np.nanmean(hub[missed & (cs_bin == b)])) if m else float("nan")
            print(f"    bin {b} ({lab:7s}): missed {m:3d} | caught {c:3d} | model hub@missed ${hubmean:6.1f}")

    # Model clearing-price distribution at the missed hours — how far below $200?
    hm = hub[missed]
    print(f"\n[clearing] model hub at the {int(missed.sum())} missed hours: "
          f"p10 ${np.nanpercentile(hm,10):.0f} p50 ${np.nanpercentile(hm,50):.0f} "
          f"p90 ${np.nanpercentile(hm,90):.0f} max ${np.nanmax(hm):.0f}")
    for lo, hi in [(0, 50), (50, 100), (100, 150), (150, 200)]:
        n = int(((hm >= lo) & (hm < hi)).sum())
        print(f"    ${lo:3d}-{hi:3d}: {n:3d} missed hours ({n/max(1,len(hm)):4.0%})")

    # Where the missed hours sit vs the caught hours in net-load percentile.
    pct = (np.argsort(np.argsort(nl)) / (len(nl) - 1))  # empirical percentile rank
    print(f"\n[netload pct] missed hours: p10 {np.nanpercentile(pct[missed],10):.3f} "
          f"p50 {np.nanpercentile(pct[missed],50):.3f} p90 {np.nanpercentile(pct[missed],90):.3f}")
    print(f"[netload pct] caught hours: p10 {np.nanpercentile(pct[caught],10):.3f} "
          f"p50 {np.nanpercentile(pct[caught],50):.3f} p90 {np.nanpercentile(pct[caught],90):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
