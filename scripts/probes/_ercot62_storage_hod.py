"""ERCOT-62 free diagnostic (NOT a target): 2025 storage hour-of-day profile
vs the measured EIA-930 battery series, for any solved bundle.

The ERCOT-60 §7 window decomposition convention: evening up-ramp (17-20),
morning ramp (05-07), daytime (09-15), late night (21-23), plus annual
throughput and the hourly shape correlation ERCOT-59 tracked (0.807 keeper,
0.820 storage-deploy). Diagnostic only — the EIA-930 battery series is the
OUTCOME being validated (rule 13): never tune to it, never gate on it.

Usage::

    python scripts/probes/_ercot62_storage_hod.py --bundle <name> [--year 2025]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--year", type=int, default=2025)
    args = ap.parse_args()
    year = args.year

    from market_sim.data.eia_loader import load_ercot_battery_gen

    st = pd.read_parquet(
        REPO / "results" / "calibration" / args.bundle / "storage.parquet"
    )
    st = st[(st["pass"] == "P1") & (st["year"] == year)]
    dis = (
        st.groupby("hour")["discharge_mw"].sum().reindex(range(8760)).fillna(0.0)
    ).to_numpy()

    series = load_ercot_battery_gen(year)
    if series is None:
        raise SystemExit(f"no measured EIA-930 battery series for {year}")
    meas = np.asarray(series["battery_discharge"], dtype=float)[:8760]

    hod = np.arange(8760) % 24
    mp = np.array([np.nanmean(meas[hod == h]) for h in range(24)])
    dp = np.array([dis[hod == h].mean() for h in range(24)])

    print(f"== {args.bundle} {year}: storage discharge vs measured EIA-930 ==")
    print(
        f"annual: model {dis.sum() / 1e6:.2f} TWh vs measured "
        f"{np.nansum(meas) / 1e6:.2f} TWh (reported hours only)"
    )
    ok = np.isfinite(meas)
    r = np.corrcoef(dis[ok], meas[ok])[0, 1]
    print(f"hourly shape correlation r = {r:.3f}")
    print("window mean MW (model / measured):")
    for name, lo, hi in (
        ("morning 05-07", 5, 7),
        ("daytime 09-15", 9, 15),
        ("evening 17-20", 17, 20),
        ("late night 21-23", 21, 23),
    ):
        m = (np.arange(24) >= lo) & (np.arange(24) <= hi)
        print(f"  {name:<17} {dp[m].mean():8,.0f} / {mp[m].mean():8,.0f}")
    print("hod profile (model | measured):")
    for h in range(24):
        print(f"  {h:2d}: {dp[h]:8,.0f} | {mp[h]:8,.0f}")


if __name__ == "__main__":
    main()
