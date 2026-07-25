"""pjm-120 diagnostic readout: where does the model lose the 2025 C3a residual?

Decomposes the model-vs-actual load-weighted mean LMP gap for a solved PJM
bundle by ACTUAL-price stratum, so the "extreme tail depth" hypothesis is
separated from the "shoulder-hour level" hypothesis on the same arithmetic the
C3a scorer uses (load-weighted system mean).

Usage:
    python pjm120_readout.py results/probes/pjm120_c3a_2025 --year 2025
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path("/home/user/market-simulator")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


def main() -> None:
    """Print the stratified decomposition of the C3a residual."""
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle")
    ap.add_argument("--year", type=int, default=2025)
    a = ap.parse_args()
    bundle, year = Path(a.bundle), a.year

    sy = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    # Demand-weighted system price per hour + total demand per hour.
    g = sy.groupby("hour")
    num = g.apply(
        lambda x: float(np.sum(x["price"] * x["demand"])), include_groups=False
    )
    den = g["demand"].sum()
    model = (num / den).rename("model")
    dem = den.rename("d")
    mmax = g["price"].max().rename("model_zmax")

    # Actual hourly RT (mean across nodes/zones), aligned by hour index.
    ap_ = pd.read_parquet(REPO / f"data/clean/lmp/PJM/RTM/lmp_{year}.parquet")
    ap_ = ap_[ap_["interval_start_local"].dt.year == year]
    act = ap_.groupby("interval_start_local")["lmp_usd_per_mwh"].mean()
    act = act.sort_index().to_numpy(float)
    n = min(len(act), len(model))
    df = pd.DataFrame(
        {
            "model": model.to_numpy(float)[:n],
            "actual": act[:n],
            "d": dem.to_numpy(float)[:n],
            "model_zmax": mmax.to_numpy(float)[:n],
        }
    )
    w = df["d"] / df["d"].sum()
    print(f"hours={n}  model_lw={float((df.model*w).sum()):.2f}  "
          f"actual_lw={float((df.actual*w).sum()):.2f}  "
          f"gap={float(((df.model-df.actual)*w).sum()):+.2f} $/MWh")
    print(f"model max={df.model.max():.0f} (any-zone {df.model_zmax.max():.0f})  "
          f"actual max={df.actual.max():.0f}")

    print("\n-- residual by ACTUAL-price stratum (load-weighted contribution) --")
    bins = [-1e9, 0, 25, 50, 100, 200, 376, 1e9]
    labs = ["<0", "0-25", "25-50", "50-100", "100-200", "200-376", ">376"]
    df["bin"] = pd.cut(df["actual"], bins=bins, labels=labs)
    rows = []
    for lab in labs:
        m = df["bin"] == lab
        if not m.any():
            continue
        contrib = float(((df.model[m] - df.actual[m]) * w[m]).sum())
        rows.append(
            f"{lab:>9s} | {int(m.sum()):5d} h | model {float((df.model[m]*w[m]).sum()/w[m].sum()):7.1f} "
            f"| actual {float((df.actual[m]*w[m]).sum()/w[m].sum()):7.1f} "
            f"| contributes {contrib:+7.3f} $/MWh"
        )
    print("\n".join(rows))

    print("\n-- top 15 actual hours --")
    t = df.sort_values("actual", ascending=False).head(15)
    for i, r in t.iterrows():
        print(f"  h{int(i):5d}  actual {r.actual:7.0f}  model {r.model:7.1f} "
              f"(any-zone {r.model_zmax:7.1f})")


if __name__ == "__main__":
    main()
