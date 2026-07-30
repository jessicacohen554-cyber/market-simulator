"""ERCOT-140 pre-registered guard probe (precommit §4 — the decision inputs).

Scores the ercot140 arm against the ercot139 keeper on the THREE
pre-registered gates fixed in
``docs/PRECOMMIT-ercot140-coal-peak-offer-2026-07-30.md`` §4/§5, on a
matched basis (both bundles' ``hourly/system_<year>.parquet`` P1
demand-weighted hub series vs the committed hourly RT actuals):

1. **Zero-spurious** (ERCOT-89/91): the count of hours where the model
   settles >$200 while the RT actual is ≤$200 must not increase over the
   keeper's own count in any year.
2. **C3a level guard**: no year's mean-price residual may degrade (move
   away from actual) or cross above 0 % (over-fire).
3. **Crossing-band no-regress / C1 coal**: coal TWh must not increase vs
   the keeper in any year, and must DECREASE in all three (the structural
   target + the extrapolation/LOYO gate: 3/3 or reject).

Matched-basis note: the demand-weighted system-parquet hub reproduces the
official 2023 C3c count within 1 hour (46 vs 47) — the guard compares the
SAME construction across the two bundles, so the delta is exact even where
the level is one hour off the official scorer's hub. The official rubric
(C-gates) comes from ``calibration_verdict`` at registration, never from
this probe.

Usage::

    python scripts/probes/ercot140_guard_probe.py \
        [--keeper results/calibration/ercot139_cc_committed_arm] \
        [--arm results/calibration/ercot140_coal_peak_arm]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

ACTUALS = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
YEARS = (2023, 2024, 2025)
TAIL = 200.0


def _hub(bundle: Path, year: int) -> np.ndarray:
    """P1 demand-weighted hub price per hour from the bundle's system parquet."""
    df = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    p1 = df[df["pass"] == "P1"]
    w = p1["price"] * p1["demand"]
    hub = w.groupby(p1["hour"]).sum() / p1.groupby("hour")["demand"].sum()
    return hub.sort_index().to_numpy()


def _coal_twh(bundle: Path, year: int) -> float:
    """Coal class annual TWh (P1) from the bundle's class hourly parquet."""
    df = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    coal = df[
        (df["pass"] == "P1") & df["klass"].astype(str).str.startswith("COAL")
    ]
    return float(coal["mw"].sum()) / 1e6


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument(
        "--keeper", default="results/calibration/ercot139_cc_committed_arm"
    )
    ap.add_argument("--arm", default="results/calibration/ercot140_coal_peak_arm")
    args = ap.parse_args()
    keeper, arm = Path(args.keeper), Path(args.arm)

    act = pd.read_parquet(ACTUALS)
    fails: list[str] = []
    print(
        f"{'year':>4} {'spur_k':>6} {'spur_a':>6} {'Δspur':>5} "
        f"{'C3a_k%':>8} {'C3a_a%':>8} {'coal_k':>7} {'coal_a':>7} {'Δcoal':>7}"
    )
    for y in YEARS:
        rt = act[act["year"] == y].sort_values("hour")["rt"].to_numpy()
        hk, ha = _hub(keeper, y), _hub(arm, y)
        n = min(len(rt), len(hk), len(ha))
        rt, hk, ha = rt[:n], hk[:n], ha[:n]
        spur_k = int(((hk > TAIL) & (rt <= TAIL)).sum())
        spur_a = int(((ha > TAIL) & (rt <= TAIL)).sum())
        c3a_k = 100.0 * (hk.mean() - rt.mean()) / rt.mean()
        c3a_a = 100.0 * (ha.mean() - rt.mean()) / rt.mean()
        ck, ca = _coal_twh(keeper, y), _coal_twh(arm, y)
        print(
            f"{y:>4} {spur_k:>6} {spur_a:>6} {spur_a - spur_k:>5} "
            f"{c3a_k:>8.2f} {c3a_a:>8.2f} {ck:>7.2f} {ca:>7.2f} {ca - ck:>7.3f}"
        )
        if spur_a > spur_k:
            fails.append(f"{y}: spurious tail +{spur_a - spur_k} (gate: 0)")
        if abs(c3a_a) > abs(c3a_k) + 1e-9:
            fails.append(f"{y}: C3a degrades {c3a_k:.2f}% -> {c3a_a:.2f}%")
        if c3a_a > 0.0:
            fails.append(f"{y}: C3a overshoots past 0 ({c3a_a:.2f}%)")
        if ca > ck + 1e-9:
            fails.append(f"{y}: coal TWh increases {ck:.2f} -> {ca:.2f}")
        if ca >= ck - 1e-9:
            fails.append(f"{y}: coal TWh does not improve (LOYO 3/3 gate)")
    print()
    if fails:
        print("GUARD BREACH (precommit §4/§5 case 1 or 3):")
        for f in fails:
            print("  -", f)
        raise SystemExit(1)
    print("ALL GUARDS PASS (precommit §5 case 2 territory — owner surfacing)")


if __name__ == "__main__":
    main()
