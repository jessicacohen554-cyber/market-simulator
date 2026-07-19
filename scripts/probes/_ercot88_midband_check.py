"""ERCOT-88 mid-band probe gates: C3a level guard + zero-spurious check.

The §6.2 probe-cadence analyzer (charter §9,
``docs/handoffs/ercot-residual-midband-formation-lane-2026-07.md``) — the
ERCOT-86 analyzer convention re-implemented for the fast-start pool probes.
Given a PROBE bundle and its BASE bundle (the same recipe without the pool
gate) it reports, per year:

* **C3a level guard** — the annual demand-weighted mean of the system
  ``price`` column (pass P1; the column already carries every price overlay)
  vs the actual RT mean, base vs probe. The probe fails the guard if its
  |annual residual| degrades materially vs base.
* **Mid-band fill** — at the actual RT $150-500 hours: how many the model
  prices in-band (formed), model p50/p90 at those hours, and the mean hourly
  residual — base vs probe.
* **Zero-spurious check** — model-in-band hours where actual RT < $150: the
  probe must add ZERO such hours vs base.

Read-only: consumes ``<bundle>/system.parquet`` and the committed actual RT
parquet; solves nothing, registers nothing.

Usage::

    python scripts/probes/_ercot88_midband_check.py \
        --probe results/calibration/probe_dir --base results/calibration/base_dir \
        --years 2024
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

ACTUAL_LMP = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
MID_BAND = (150.0, 500.0)  # the ERCOT-86/87/88 moderate-tightness band, $/MWh


def eff_price(bundle: Path, year: int) -> np.ndarray:
    """Hourly demand-weighted system price (pass P1) for ``year``."""
    df = pd.read_parquet(bundle / "system.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    if df.empty:
        raise SystemExit(f"{bundle}: no P1 rows for {year}")
    w = df["price"] * df["demand"]
    num = w.groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    return (num / den).reindex(range(int(df["hour"].max()) + 1)).to_numpy(float)


def year_stats(model: np.ndarray, actual: pd.DataFrame, year: int) -> dict:
    """Level + mid-band occupancy stats for one year."""
    act = actual[actual["year"] == year].set_index("hour")["rt"]
    hours = np.intersect1d(act.index.to_numpy(int), np.arange(len(model)))
    a = act.reindex(hours).to_numpy(float)
    m = model[hours]
    mb = (a >= MID_BAND[0]) & (a <= MID_BAND[1])
    spur = (m >= MID_BAND[0]) & (m <= MID_BAND[1]) & (a < MID_BAND[0])
    formed = (m[mb] >= MID_BAND[0]) & (m[mb] <= MID_BAND[1])
    return {
        "mean_model": float(m.mean()),
        "mean_actual": float(a.mean()),
        "resid_pct": float((m.mean() - a.mean()) / a.mean() * 100.0),
        "mb_hours_actual": int(mb.sum()),
        "mb_formed": int(formed.sum()),
        "mb_model_p50": float(np.median(m[mb])) if mb.any() else None,
        "mb_model_p90": float(np.quantile(m[mb], 0.9)) if mb.any() else None,
        "mb_resid_mean": float((m[mb] - a[mb]).mean()) if mb.any() else None,
        "spurious": int(spur.sum()),
    }


def main() -> None:
    """Run the base-vs-probe mid-band gate report."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe", type=Path, required=True)
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2024])
    args = ap.parse_args()

    actual = pd.read_parquet(ACTUAL_LMP)
    for y in args.years:
        b = year_stats(eff_price(args.base, y), actual, y)
        p = year_stats(eff_price(args.probe, y), actual, y)
        print(f"\n=== {y} (base -> probe) ===")
        print(
            f"C3a mean: model {b['mean_model']:.2f} -> {p['mean_model']:.2f} "
            f"vs RT {b['mean_actual']:.2f} "
            f"(resid {b['resid_pct']:+.1f}% -> {p['resid_pct']:+.1f}%)"
        )
        print(
            f"mid-band ({b['mb_hours_actual']} actual hrs): formed "
            f"{b['mb_formed']} -> {p['mb_formed']}; "
            f"p50 {b['mb_model_p50']:.0f} -> {p['mb_model_p50']:.0f}; "
            f"p90 {b['mb_model_p90']:.0f} -> {p['mb_model_p90']:.0f}; "
            f"resid {b['mb_resid_mean']:+.2f} -> {p['mb_resid_mean']:+.2f}"
        )
        d_spur = p["spurious"] - b["spurious"]
        print(
            f"spurious (model in-band, actual <$150): {b['spurious']} -> "
            f"{p['spurious']}  (delta {d_spur:+d}; gate requires <= 0)"
        )
        print(
            "GATES: "
            + (
                "C3a "
                + (
                    "HELD"
                    if abs(p["resid_pct"]) <= abs(b["resid_pct"]) + 1.0
                    else "DEGRADED"
                )
            )
            + "; spurious "
            + ("HELD" if d_spur <= 0 else "TRIPPED")
        )


if __name__ == "__main__":
    main()
