"""neiso-61 A/B probe: gas-offer net-revenue margin vs keeper-recipe base.

Compares the two same-HEAD replay arms of the gas-offer net-revenue margin
charter (design doc
``docs/handoffs/gas-offer-net-revenue-margin-design-2026-07.md``) against the
neiso-60 keeper and the measured ISO-NE SMD RT hub series, per year:

* system mean price (model vs actual, and vs the keeper's committed hourlies
  — the same-box drift control), and
* the 2022-holdout duration-band table (hours banded by the ACTUAL RT price,
  hour-matched model means) — the bulk/tail rotation signature the mechanism
  targets, evaluated in-sample so the LOYO evidence is per-year and
  parameter-free.

Reads only committed bundle hourlies + the raw SMD workbooks; no solve.

Usage::

    python scripts/probes/neiso61_netrev_margin_ab.py \
        --bundles neiso59_reaudit_corrected_outages neiso61_netrev_base \
                  neiso61_netrev_margin \
        --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SMD_DIR = REPO / "data/raw/lmp-data/NEISO"
BANDS = [(-np.inf, 40.0), (40.0, 80.0), (80.0, 150.0), (150.0, 300.0), (300.0, np.inf)]
BAND_LABELS = ["<40", "40-80", "80-150", "150-300", ">300"]


def actual_rt_hourly(year: int) -> np.ndarray:
    """ISO-NE INTERNAL_HUB hourly RT LMP, Feb-29 dropped in leap years."""
    path = SMD_DIR / f"{year}_smd_hourly.xlsx"
    xl = pd.ExcelFile(path)
    sheet = next(
        s for s in xl.sheet_names if "INTERNAL" in s.upper() or "ISO NE CA" in s.upper()
    )
    df = xl.parse(sheet)
    date_col = next(c for c in df.columns if "date" in str(c).lower())
    rt_col = next(c for c in df.columns if str(c).upper().startswith("RT_LMP"))
    df = df[[date_col, rt_col]].dropna()
    dates = pd.to_datetime(df[date_col])
    df = df[~((dates.dt.month == 2) & (dates.dt.day == 29))]
    return df[rt_col].to_numpy(dtype=float)[:8760]


def model_system_hourly(bundle: str, year: int) -> np.ndarray:
    """Zone-mean hourly system price from a bundle's committed sidecar."""
    df = pd.read_parquet(
        REPO / "results/calibration" / bundle / "hourly" / f"system_{year}.parquet"
    )
    return df.groupby("hour")["price"].mean().sort_index().to_numpy(dtype=float)


def main() -> None:
    """Print the per-year A/B means and duration-band tables."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--bundles", nargs="+", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()

    for year in args.years:
        actual = actual_rt_hourly(year)
        series = {b: model_system_hourly(b, year) for b in args.bundles}
        n = min(len(actual), *(len(s) for s in series.values()))
        actual = actual[:n]
        print(f"\n=== {year} ===  actual RT mean {actual.mean():7.2f}")
        for b in args.bundles:
            print(f"  {b:34s} model mean {series[b][:n].mean():7.2f}")
        hdr = f"  {'band':>8s} {'hours':>6s} {'actual':>8s}"
        for b in args.bundles:
            hdr += f" {b[:18]:>19s}"
        print(hdr + "   (hour-matched model means / gap)")
        for (lo, hi), label in zip(BANDS, BAND_LABELS):
            mask = (actual >= lo) & (actual < hi)
            if not mask.any():
                continue
            row = f"  {label:>8s} {int(mask.sum()):6d} {actual[mask].mean():8.1f}"
            for b in args.bundles:
                m = series[b][:n][mask].mean()
                row += f" {m:9.1f} ({m - actual[mask].mean():+7.1f})"
            print(row)


if __name__ == "__main__":
    main()
