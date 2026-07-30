"""ERCOT-141 pre-registered guard probe (precommit §4 — the decision inputs).

Scores the ercot141 online-hours-floor arm against the ercot140 keeper on the
gates fixed in ``docs/PRECOMMIT-ercot141-cc-committed-lsl-floor-2026-07-30.md``
§4/§5, on a matched basis: both bundles' ``hourly/system_<year>.parquet`` P1
demand-weighted hub series vs the committed hourly RT actuals, and both
bundles' ``hourly/class_hourly_<year>.parquet`` for class volumes. The
``_hub`` / class-TWh constructions are the ERCOT-140 probe's verbatim, so the
two probes are directly comparable and the keeper→arm delta is exact.

The gates scored here (the precommit's §4 guards 2 and 4, plus the §3
predictions as reported context):

* **Guard 2 — zero-spurious** (the ERCOT-89/91 gate): the count of hours where
  the model settles >$200 while the RT actual is ≤$200 must not increase over
  the keeper's own count in any year.
* **Guard 2 — C3a no-overshoot**: C3a must not cross above +0 % in any year.
  This arm pushes C3a UP by construction, so overshooting is its natural
  failure mode and is a pre-registered ORDINARY REJECTION.
* **Guard 4 — C3c no-drain**: the model's >$200 count must not fall materially
  below the keeper's (47/6/0 vs RT actual 181/53/31). The ERCOT-118/119 drain
  channel was cheap-CC-in-merit; this arm PINS the cheap block, so a drain
  falsifies the ERCOT-139 §4.1 story outright.
* **Reported, not gated here**: C3a direction and the trough counts
  (prediction 1/2), and the CC/coal volume shift (prediction 4). Guard 1 (C8
  forced share) is scored from the bundle's own
  ``legitimacy_diagnostics.json``; guard 3 (C1/C2) from the official
  ``calibration_verdict`` rubric at registration — never from this probe.

Usage::

    python scripts/probes/ercot141_guard_probe.py \
        [--keeper results/calibration/ercot140_coal_peak_arm] \
        [--arm results/calibration/ercot141_online_hours_arm]
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
# A C3c fall this large (relative to the keeper's own count) is the ERCOT-118/119
# drain signature rather than solver noise — the precommit's "materially" made
# concrete before the numbers are seen.
C3C_DRAIN_FRAC = 0.20


def _hub(bundle: Path, year: int) -> np.ndarray:
    """P1 demand-weighted hub price per hour from the bundle's system parquet."""
    df = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    p1 = df[df["pass"] == "P1"]
    w = p1["price"] * p1["demand"]
    hub = w.groupby(p1["hour"]).sum() / p1.groupby("hour")["demand"].sum()
    return hub.sort_index().to_numpy()


def _class_twh(bundle: Path, year: int, prefix: str) -> float:
    """Annual P1 TWh for classes whose name starts with ``prefix``."""
    df = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    sel = df[(df["pass"] == "P1") & df["klass"].astype(str).str.startswith(prefix)]
    return float(sel["mw"].sum()) / 1e6


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--keeper", default="results/calibration/ercot140_coal_peak_arm")
    ap.add_argument("--arm", default="results/calibration/ercot141_online_hours_arm")
    args = ap.parse_args()
    keeper, arm = Path(args.keeper), Path(args.arm)

    act = pd.read_parquet(ACTUALS)
    fails: list[str] = []

    print("GUARD 2 (zero-spurious + C3a no-overshoot) / GUARD 4 (C3c no-drain)")
    print(
        f"{'year':>4} {'spur_k':>6} {'spur_a':>6} {'Δspur':>6} "
        f"{'C3a_k%':>8} {'C3a_a%':>8} {'C3c_k':>6} {'C3c_a':>6} {'C3c_rt':>7}"
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
        tail_k = int((hk > TAIL).sum())
        tail_a = int((ha > TAIL).sum())
        tail_rt = int((rt > TAIL).sum())
        print(
            f"{y:>4} {spur_k:>6} {spur_a:>6} {spur_a - spur_k:>6} "
            f"{c3a_k:>8.2f} {c3a_a:>8.2f} {tail_k:>6} {tail_a:>6} {tail_rt:>7}"
        )
        if spur_a > spur_k:
            fails.append(f"{y}: spurious tail +{spur_a - spur_k} (gate: 0)")
        if c3a_a > 0.0:
            fails.append(f"{y}: C3a overshoots past 0 ({c3a_a:.2f}%)")
        if tail_a < tail_k * (1.0 - C3C_DRAIN_FRAC) - 1e-9:
            fails.append(
                f"{y}: C3c drains {tail_k} -> {tail_a} "
                f"(>{C3C_DRAIN_FRAC:.0%} fall — the 118/119 signature)"
            )

    print("\nPREDICTIONS 1/2 (C3a direction, trough counts) — reported, not gated")
    print(
        f"{'year':>4} {'<$10_k':>7} {'<$10_a':>7} {'<$10rt':>7} "
        f"{'<$15_k':>7} {'<$15_a':>7} {'<$15rt':>7} {'C3aΔpp':>8}"
    )
    for y in YEARS:
        rt = act[act["year"] == y].sort_values("hour")["rt"].to_numpy()
        hk, ha = _hub(keeper, y), _hub(arm, y)
        n = min(len(rt), len(hk), len(ha))
        rt, hk, ha = rt[:n], hk[:n], ha[:n]
        c3a_k = 100.0 * (hk.mean() - rt.mean()) / rt.mean()
        c3a_a = 100.0 * (ha.mean() - rt.mean()) / rt.mean()
        print(
            f"{y:>4} {int((hk < 10).sum()):>7} {int((ha < 10).sum()):>7} "
            f"{int((rt < 10).sum()):>7} {int((hk < 15).sum()):>7} "
            f"{int((ha < 15).sum()):>7} {int((rt < 15).sum()):>7} "
            f"{c3a_a - c3a_k:>+8.2f}"
        )

    print("\nPREDICTION 4 (volume shift) — reported, not gated")
    print(f"{'year':>4} {'coal_k':>7} {'coal_a':>7} {'Δcoal':>7} {'cc_k':>7} {'cc_a':>7} {'Δcc':>7}")
    for y in YEARS:
        ck, ca = _class_twh(keeper, y, "COAL"), _class_twh(arm, y, "COAL")
        gk, ga = _class_twh(keeper, y, "CC_REGULAR"), _class_twh(arm, y, "CC_REGULAR")
        print(
            f"{y:>4} {ck:>7.2f} {ca:>7.2f} {ca - ck:>+7.3f} "
            f"{gk:>7.2f} {ga:>7.2f} {ga - gk:>+7.3f}"
        )

    print()
    if fails:
        print("GUARD BREACH (precommit §5 case 2 — ORDINARY REJECTION):")
        for f in fails:
            print("  -", f)
        raise SystemExit(1)
    print("GUARDS 2 & 4 PASS (precommit §5 case 3/4 territory — C8/C1/C2 decide)")


if __name__ == "__main__":
    main()
