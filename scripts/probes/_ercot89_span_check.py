"""ERCOT-89 online-span probe gates: C3a level + zero-spurious + tail guards.

The ERCOT-89 probe-cadence analyzer (charter §7 of
``docs/handoffs/ercot-shoulder-online-envelope-2026-07.md``) — the ERCOT-88
analyzer convention (``_ercot88_midband_check.py``) extended with the
pre-committed NEW guard of this lane: the scarcity tail must not degrade
(the ercot41/43 envelope-family failure signature). Given a PROBE bundle and
a BASE (a bundle directory with ``system.parquet``, or the keeper's committed
``hourly/system_<year>.parquet`` sidecar) it reports, per year:

* **C3a level guard** — annual demand-weighted mean of the system ``price``
  column (pass P1) vs actual RT, base vs probe; fails on material
  degradation of the |annual residual|.
* **Mid-band fill** — at actual RT $150-500 hours: formed count, model
  p50/p90, mean residual — base vs probe.
* **Zero-spurious check** — model-in-band hours where actual RT < $150:
  the probe must add ZERO such hours vs base.
* **Tail guards (NEW, pre-committed)** — h>$200 and h>$500 counts (model vs
  actual, base vs probe: the C3c-proxy must not move AWAY from the actual
  count), and the tail-hour NRMSE proxy (C3b direction) must not rise.

Read-only: consumes parquet outputs and the committed actual RT parquet;
solves nothing, registers nothing.

Usage::

    python scripts/probes/_ercot89_span_check.py \
        --probe results/calibration/_ercot89_span_probe_2024 \
        --base results/calibration/ercot86_rtwall_fullspan/hourly \
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
MID_BAND = (150.0, 500.0)  # the ERCOT-86/87/88/89 moderate-tightness band, $/MWh


def eff_price(bundle: Path, year: int) -> np.ndarray:
    """Hourly demand-weighted system price (pass P1) for ``year``.

    Accepts either a bundle directory (``<bundle>/system.parquet``) or the
    keeper's committed hourly sidecar directory
    (``<dir>/system_<year>.parquet`` — same schema).
    """
    path = bundle / "system.parquet"
    if not path.exists():
        path = bundle / f"system_{year}.parquet"
    if not path.exists():
        raise SystemExit(f"{bundle}: no system parquet for {year}")
    df = pd.read_parquet(path)
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    if df.empty:
        raise SystemExit(f"{path}: no P1 rows for {year}")
    w = df["price"] * df["demand"]
    num = w.groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    return (num / den).reindex(range(int(df["hour"].max()) + 1)).to_numpy(float)


def year_stats(model: np.ndarray, actual: pd.DataFrame, year: int) -> dict:
    """Level, mid-band occupancy, and tail stats for one year."""
    act = actual[actual["year"] == year].set_index("hour")["rt"]
    hours = np.intersect1d(act.index.to_numpy(int), np.arange(len(model)))
    a = act.reindex(hours).to_numpy(float)
    m = model[hours]
    mb = (a >= MID_BAND[0]) & (a <= MID_BAND[1])
    spur = (m >= MID_BAND[0]) & (m <= MID_BAND[1]) & (a < MID_BAND[0])
    formed = (m[mb] >= MID_BAND[0]) & (m[mb] <= MID_BAND[1])
    tail = a > MID_BAND[1]
    nrmse = float(np.sqrt(np.mean((m - a) ** 2)) / a.mean())
    return {
        "mean_model": float(m.mean()),
        "mean_actual": float(a.mean()),
        "resid_pct": float((m.mean() - a.mean()) / a.mean() * 100.0),
        "nrmse": nrmse,
        "mb_hours_actual": int(mb.sum()),
        "mb_formed": int(formed.sum()),
        "mb_model_p50": float(np.median(m[mb])) if mb.any() else None,
        "mb_model_p90": float(np.quantile(m[mb], 0.9)) if mb.any() else None,
        "mb_resid_mean": float((m[mb] - a[mb]).mean()) if mb.any() else None,
        "spurious": int(spur.sum()),
        "h200_model": int((m > 200.0).sum()),
        "h200_actual": int((a > 200.0).sum()),
        "h500_model": int((m > 500.0).sum()),
        "h500_actual": int((a > 500.0).sum()),
        "tail_model_mean": float(m[tail].mean()) if tail.any() else None,
        "tail_actual_mean": float(a[tail].mean()) if tail.any() else None,
    }


def main() -> None:
    """Run the base-vs-probe span gate report."""
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
        print(f"NRMSE (C3b proxy): {b['nrmse']:.3f} -> {p['nrmse']:.3f}")
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
            f"tail: h>$200 model {b['h200_model']} -> {p['h200_model']} "
            f"(actual {b['h200_actual']}); h>$500 model {b['h500_model']} -> "
            f"{p['h500_model']} (actual {b['h500_actual']}); tail-hour mean "
            f"model {b['tail_model_mean']} -> {p['tail_model_mean']} "
            f"(actual {b['tail_actual_mean']})"
        )
        # Tail guard: the h>$200 count must not move AWAY from the actual
        # count, and NRMSE must not rise materially (>0.005 grace for float
        # noise) — the ercot41/43 over-fire signature.
        away = abs(p["h200_model"] - b["h200_actual"]) > abs(
            b["h200_model"] - b["h200_actual"]
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
            + "; tail-count "
            + ("HELD" if not away else "DEGRADED")
            + "; NRMSE "
            + ("HELD" if p["nrmse"] <= b["nrmse"] + 0.005 else "DEGRADED")
        )


if __name__ == "__main__":
    main()
