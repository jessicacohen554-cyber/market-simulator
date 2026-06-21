"""Decompose the ERCOT 2023 LMP scarcity tail across three drivers.

Usage: uv run python scripts/probes/_ercot_2023_decomp.py

Reads three single-year 2023 ERCOT bundles (system.parquet) and the actual
RTSPP, all on the demand-weighted hourly system price (co-opt LMP, already
scarcity-inclusive), and attributes the 2023 tail across:

  (a) physical missing-derate  = run132 keeper  -> run134 (ccsteam coupling)
  (b) reserve-accounting over-fire = run134 -> run134 + measured-2023 credit
  (c) residual out-of-market administrative = (run134+credit) -> actual

The run132 keeper number is taken from the registered dashboard run (the
storage-AS keeper, 2023 byte-identical to run131). The run134 baseline and the
+credit probe are freshly solved here (single-year 2023). All four series are
compared on the same demand-weighted metric.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
ACTUAL = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "_validation-source"
    / "actual_lmp_hourly_ERCOT.parquet"
)
YEAR = 2023


def model_series(bundle: str) -> tuple[np.ndarray, np.ndarray]:
    """Demand-weighted hourly model price and total demand (P1, year 2023)."""
    sy = pd.read_parquet(ROOT / bundle / "system.parquet")
    if "pass" in sy.columns and (sy["pass"] == "P1").any():
        sy = sy[sy["pass"] == "P1"]
    g = sy[sy["year"] == YEAR].copy()
    num = (g["price"] * g["demand"]).groupby(g["hour"]).sum()
    den = g["demand"].groupby(g["hour"]).sum()
    p = (num / den.replace(0, np.nan)).sort_index()
    return p.to_numpy(float), den.sort_index().to_numpy(float)


def summarize(name: str, p: np.ndarray, w: np.ndarray) -> dict:
    wn = w / w.sum()
    return {
        "name": name,
        "mean": float((p * wn).sum()),
        ">200": int((p > 200).sum()),
        ">500": int((p > 500).sum()),
        ">1000": int((p > 1000).sum()),
        "p": p,
    }


def main() -> None:
    base_bundle = sys.argv[1] if len(sys.argv) > 1 else "_decomp_2023_base"
    cred_bundle = sys.argv[2] if len(sys.argv) > 2 else "_decomp_2023_credit"

    p_base, dem = model_series(base_bundle)
    p_cred, _ = model_series(cred_bundle)
    adf = pd.read_parquet(ACTUAL)
    act = adf[adf["year"] == YEAR].sort_values("hour")["rt"].to_numpy(float)

    n = min(len(p_base), len(p_cred), len(act), len(dem))
    p_base, p_cred, act, dem = p_base[:n], p_cred[:n], act[:n], dem[:n]
    # actual RTSPP carries a few NaN hours; drop them from all series consistently
    ok = ~np.isnan(act)
    p_base, p_cred, act, dem = p_base[ok], p_cred[ok], act[ok], dem[ok]
    w = dem

    rows = [
        summarize("run134 baseline (ccsteam, no 2023 credit)", p_base, w),
        summarize("run134 + measured-2023 storage-AS credit", p_cred, w),
        summarize("actual RTSPP", act, w),
    ]

    print(f"=== ERCOT {YEAR} decomposition (demand-weighted system price) ===")
    print(f"{'series':<46}{'mean':>8}{'>200':>7}{'>500':>7}{'>1000':>7}")
    for r in rows:
        print(
            f"{r['name']:<46}{r['mean']:>8.1f}{r['>200']:>7d}"
            f"{r['>500']:>7d}{r['>1000']:>7d}"
        )
    print()

    b, c, a = rows[0], rows[1], rows[2]
    print("--- 2023 tail attribution (vs actual 181/104 >200/>500) ---")
    print(
        f"(b) reserve over-fire removed by credit: "
        f"mean {b['mean']:.1f} -> {c['mean']:.1f} ({c['mean'] - b['mean']:+.1f}); "
        f">200 {b['>200']} -> {c['>200']} ({c['>200'] - b['>200']:+d}); "
        f">500 {b['>500']} -> {c['>500']} ({c['>500'] - b['>500']:+d})"
    )
    print(
        f"(c) residual out-of-market (credit -> actual): "
        f"mean {c['mean']:.1f} vs {a['mean']:.1f} ({a['mean'] - c['mean']:+.1f}); "
        f">200 {c['>200']} vs {a['>200']} ({a['>200'] - c['>200']:+d}); "
        f">500 {c['>500']} vs {a['>500']} ({a['>500'] - c['>500']:+d})"
    )


if __name__ == "__main__":
    main()
