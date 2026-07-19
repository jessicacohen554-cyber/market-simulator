"""Zonal net-export + thermal-miss-by-zone report for a calibration bundle.

Reads a bundle's dispatch/<year>_P1.parquet (model gen by zone/klass/hour),
system.parquet (zonal demand), and campd.parquet (actual per-plant net), maps
CAMPD plants to their ERCOT zone via the bin sheet, and prints:

  * zonal net export   = model gen by zone − model demand by zone (TWh)
  * thermal miss by zone = model thermal gen − CAMPD thermal, by zone (TWh)
  * CC_REGULAR miss by zone

Used to quantify the spatial reliability-deployment overlay's before/after. The
reusable ``THERMAL`` set and ``_zone_map`` helper live in
``scripts/lib/reldeploy_zonal_report.py``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from market_sim.config.paths import CAMPD_BINS_CSV, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.bundle_io import bundle_input_path  # noqa: E402
from scripts.lib.reldeploy_zonal_report import THERMAL, _zone_map  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle")
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--bins", default=str(CAMPD_BINS_CSV))
    args = ap.parse_args()
    bundle = Path(args.bundle)
    year = args.year
    zone_of, klass_of = _zone_map(Path(args.bins))

    disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    sysd = pd.read_parquet(bundle / "system.parquet")
    campd = pd.read_parquet(bundle_input_path(bundle, "campd"))
    sysd = sysd[(sysd["year"] == year) & (sysd["pass"] == "P1")]
    campd = campd[campd["year"] == year]

    # Model gen by zone (all classes) and demand by zone.
    gen_by_zone = disp.groupby("zone", observed=True)["mw"].sum() / 1e6
    dem_by_zone = sysd.groupby("zone", observed=True)["demand"].sum() / 1e6
    net_export = (gen_by_zone - dem_by_zone).sort_values()

    # Model thermal gen by zone.
    th = disp[disp["klass"].isin(THERMAL)]
    model_th = th.groupby("zone", observed=True)["mw"].sum() / 1e6
    model_cc = (
        disp[disp["klass"] == "CC_REGULAR"].groupby("zone", observed=True)["mw"].sum()
        / 1e6
    )

    # CAMPD thermal by zone (map plant -> zone/class via bin sheet; keep only
    # plants whose bin-sheet class is thermal).
    campd = campd.copy()
    campd["zone"] = campd["plant_id"].map(zone_of)
    campd["klass"] = campd["plant_id"].map(klass_of)
    campd_th = campd[campd["klass"].isin(THERMAL)]
    actual_th = campd_th.groupby("zone", observed=True)["net_mw"].sum() / 1e6
    campd_cc = campd[campd["klass"] == "CC_REGULAR"]
    actual_cc = campd_cc.groupby("zone", observed=True)["net_mw"].sum() / 1e6

    zones = ["North", "South_Central", "West", "Northeast", "Houston", "South"]
    print(f"\n=== {bundle.name}  year {year} ===")
    print(
        f"{'zone':>14} {'net_exp':>9} {'mdl_th':>8} {'act_th':>8} "
        f"{'th_miss':>8} {'cc_miss':>8}"
    )
    for z in zones:
        ne = net_export.get(z, float("nan"))
        mt = model_th.get(z, 0.0)
        at = actual_th.get(z, 0.0)
        mc = model_cc.get(z, 0.0)
        ac = actual_cc.get(z, 0.0)
        print(
            f"{z:>14} {ne:>9.1f} {mt:>8.1f} {at:>8.1f} {mt - at:>8.1f} {mc - ac:>8.1f}"
        )
    print(
        f"{'TOTAL thermal miss':>14} "
        f"{'':>9} {model_th.sum():>8.1f} {actual_th.sum():>8.1f} "
        f"{model_th.sum() - actual_th.sum():>8.1f}"
    )


if __name__ == "__main__":
    main()
