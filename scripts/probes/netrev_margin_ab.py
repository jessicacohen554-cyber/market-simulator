"""Gas-offer net-revenue margin A/B probe (any ISO) — base vs margin vs actual.

Generalizes the neiso-61 A/B probe (scripts/probes/neiso61_netrev_margin_ab.py)
to any ISO: compares the same-HEAD replay arms of the gas-offer net-revenue
margin charter (design doc
``docs/handoffs/gas-offer-net-revenue-margin-design-2026-07.md``) against the
measured actual LMP series (``data/raw/_validation-source/
actual_lmp_hourly_<ISO>.parquet``), per year:

* C3a: system mean price (model vs actual), signed % error,
* C3b: price duration-curve NRMSE (sorted model vs sorted actual / actual mean)
  — the shape metric the mechanism targets,
* the duration-band table (hours banded by the ACTUAL price, hour-matched
  model means / gap) — the bulk/tail rotation signature.

Reads only committed bundle hourlies (``hourly/system_<year>.parquet``) + the
validation-source actuals; no solve. RT is the scored actual (``--actual da``
for the DA cross-check).

Usage::

    python scripts/probes/netrev_margin_ab.py --iso CAISO \
        --base caiso_netrev_base --margin caiso_netrev_margin --years 2024
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BANDS = [(-np.inf, 40.0), (40.0, 80.0), (80.0, 150.0), (150.0, 300.0), (300.0, np.inf)]
BAND_LABELS = ["<40", "40-80", "80-150", "150-300", ">300"]


def actual_hourly(iso: str, year: int, kind: str) -> np.ndarray:
    """(8760,) measured LMP (rt|da) from the validation-source parquet."""
    a = pd.read_parquet(
        REPO / "data/raw/_validation-source" / f"actual_lmp_hourly_{iso}.parquet"
    )
    a = a[a.year == year].sort_values("hour")
    return np.nan_to_num(a[kind].to_numpy(dtype=float))[:8760]


def model_system_hourly(bundle: str, year: int) -> np.ndarray:
    """Zone-mean hourly system price from a bundle's committed sidecar."""
    df = pd.read_parquet(
        REPO / "results/calibration" / bundle / "hourly" / f"system_{year}.parquet"
    )
    return df.groupby("hour")["price"].mean().sort_index().to_numpy(dtype=float)


def c3b_nrmse(model: np.ndarray, actual: np.ndarray) -> float:
    """Price-duration-curve NRMSE: RMSE of sorted(model) vs sorted(actual) / mean."""
    m = np.sort(model)[::-1]
    a = np.sort(actual)[::-1]
    return float(np.sqrt(np.mean((m - a) ** 2)) / a.mean())


def main() -> None:
    """Print the per-year A/B means, C3b NRMSE, and duration-band tables."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--iso", required=True)
    ap.add_argument("--base", required=True, help="BASE arm bundle name")
    ap.add_argument("--margin", required=True, help="MARGIN arm bundle name")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--actual", choices=["rt", "da"], default="rt")
    args = ap.parse_args()

    arms = {"BASE": args.base, "MARGIN": args.margin}
    for year in args.years:
        actual = actual_hourly(args.iso, year, args.actual)
        series = {k: model_system_hourly(b, year) for k, b in arms.items()}
        n = min(len(actual), *(len(s) for s in series.values()))
        actual = actual[:n]
        am = actual.mean()
        print(f"\n=== {args.iso} {year} ===  actual {args.actual.upper()} mean {am:7.2f}")
        for k in arms:
            s = series[k][:n]
            c3a = 100.0 * (s.mean() - am) / am
            print(
                f"  {k:7s} mean {s.mean():7.2f}  C3a {c3a:+6.1f}%  "
                f"C3b(dur-NRMSE) {c3b_nrmse(s, actual):.4f}"
            )
        # duration bands (hours banded by the ACTUAL price, hour-matched means)
        hdr = f"  {'band':>8s} {'hours':>6s} {'actual':>8s}"
        for k in arms:
            hdr += f" {k:>16s}"
        print(hdr + "   (hour-matched model mean / gap)")
        for (lo, hi), label in zip(BANDS, BAND_LABELS):
            mask = (actual >= lo) & (actual < hi)
            if not mask.any():
                continue
            row = f"  {label:>8s} {int(mask.sum()):6d} {actual[mask].mean():8.1f}"
            for k in arms:
                m = series[k][:n][mask].mean()
                row += f" {m:7.1f}({m - actual[mask].mean():+6.1f})"
            print(row)


if __name__ == "__main__":
    main()
