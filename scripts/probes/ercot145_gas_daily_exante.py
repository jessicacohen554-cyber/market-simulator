"""ERCOT-145b ex-ante (no LP) — the `gas_daily_shape` item-4 A/B evidence.

Reproduces the two Phase-1 numbers the precommit
(``docs/PRECOMMIT-ercot145-gas-daily-shape-2026-07-31.md`` §1c) fixes before
the solve:

1. The measured HH daily factor magnitude per year
   (``fuel.hubs.gas_daily_shape_factors`` — the exact series the armed solve
   multiplies in, mean-preserving per month by construction).
2. The within-month correlation of the keeper's DAILY price residual
   (actual − model, demand-weighted hub) with the daily factor — the honest
   ex-ante signal, recorded weak-to-mixed (2023 nil, 2024 slightly adverse,
   2025 positive) so no later reader mistakes a fit gain for the lane's
   justification (the arm is a rule-14 input-correctness A/B).

Usage::

    python scripts/probes/ercot145_gas_daily_exante.py \
        --bundle results/calibration/ercot144_perplant_arm
"""

from __future__ import annotations

import argparse
import calendar
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.fuel.hubs import gas_daily_shape_factors  # noqa: E402


def main() -> None:
    """Print factor magnitudes and residual-vs-factor correlations per year."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--bundle",
        default="results/calibration/ercot144_perplant_arm",
        help="keeper bundle directory (hourly/ sidecars)",
    )
    args = ap.parse_args()
    bundle = Path(args.bundle)
    act = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    mb = np.cumsum([0] + [calendar.monthrange(2023, m)[1] for m in range(1, 13)])

    for year in (2023, 2024, 2025):
        f = gas_daily_shape_factors(year, 8760)
        daily = f[::24]
        print(
            f"\n=== {year}: factor std {daily.std():.3f}  min {daily.min():.3f}"
            f"  max {daily.max():.3f}  days>1.25x {(daily > 1.25).sum()}"
            f"  days<0.8x {(daily < 0.8).sum()}"
        )
        sy = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
        sy = sy[sy["pass"] == "P1"]
        g = sy.groupby("hour")
        hub = g.apply(
            lambda x: np.average(x["price"], weights=np.maximum(x["demand"], 1e-9))
        )
        a = act[act["year"] == year].set_index("hour")["rt"].reindex(hub.index)
        df = pd.DataFrame({"model": hub, "act": a}).dropna()
        df["day"] = df.index // 24
        dd = df.groupby("day").mean()
        dd["fac"] = daily[: len(dd)]
        dd["resid"] = dd["act"] - dd["model"]
        dd["mon"] = np.searchsorted(mb, dd.index, side="right") - 1
        dm = dd.groupby("mon")[["resid", "fac"]].transform("mean")
        r = np.corrcoef(dd.resid - dm.resid, dd.fac - dm.fac)[0, 1]
        print(f"  within-month corr(daily resid, factor): {r:+.3f}")
        for mon in (0, 1, 10, 11):
            s = dd[dd.mon == mon]
            c = (
                np.corrcoef(s.resid, s.fac)[0, 1]
                if s.fac.std() > 1e-9
                else float("nan")
            )
            print(
                f"   mon {mon + 1:2d}: fac {s.fac.min():.2f}-{s.fac.max():.2f}"
                f"  resid mean {s.resid.mean():+.1f}  corr {c:+.2f}"
            )


if __name__ == "__main__":
    main()
