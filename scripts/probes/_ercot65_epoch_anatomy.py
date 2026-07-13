"""ERCOT-65 negative-price epoch anatomy (rule-16 diagnostic; no LP solve).

Reads a probe bundle's ``system.parquet`` and answers the charter's
substrate questions about the negative/trough epochs:

* per-zone price-band occupancy — min, h < -$1, h < $0, h <= $0.01 (the
  "wind-marginal epoch" convention of diagnosis §8, which INCLUDES negative
  duals), h < $15 — i.e. where do the epochs form and at WHAT depth (the
  flat -$26 PTC bid, the scoped blend, or $0);
* the load-weighted system price in the SAME hours RT actually cleared
  negative (HB_HUBAVG rt < $0): how far from negative is the model when
  reality is below zero, and which zones are/aren't participating — the
  REACH question (charter trap #3);
* epoch breadth: for each model zonal-epoch hour (any zone <= $0.01), how
  many zones are simultaneously in the epoch (a system-long event prices
  every zone at the wind bid; a bottled-West event only West/Panhandle).

Usage::

    python scripts/probes/_ercot65_epoch_anatomy.py BUNDLE [BUNDLE ...] \
        [--year 2023]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]


def zone_prices(bundle: Path, year: int) -> pd.DataFrame:
    """Return an ``(8760, n_zones)`` wide price frame plus demand weights."""
    df = pd.read_parquet(bundle / "system.parquet")
    df = df[(df["pass"] == "P1") & (df["year"] == year)]
    return (
        df.pivot_table(index="hour", columns="zone", values="price").reindex(
            range(8760)
        ),
        df.pivot_table(index="hour", columns="zone", values="demand").reindex(
            range(8760)
        ),
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles", nargs="+")
    ap.add_argument("--year", type=int, default=2023)
    args = ap.parse_args()
    year = args.year

    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_zonal_ERCOT.parquet"
    )
    hub = lmp[(lmp["year"] == year) & (lmp["settlement_point"] == "HB_HUBAVG")]
    rt = hub.set_index("hour")["rt"].reindex(range(8760)).to_numpy()
    rt_neg = rt < 0.0
    print(
        f"RT HB_HUBAVG {year}: {int(rt_neg.sum())} negative lw-hours, "
        f"min {np.nanmin(rt):.1f}, {int((rt < 15).sum())} h < $15"
    )

    for name in args.bundles:
        bundle = REPO / "results" / "calibration" / name
        pz, dz = zone_prices(bundle, year)
        w = dz.fillna(0.0)
        lw = (pz * w).sum(axis=1) / w.sum(axis=1)
        lw = lw.to_numpy()

        print(f"\n== {name} ==")
        print(
            f"  lw: min {np.nanmin(lw):8.2f}  h<$0 {int((lw < 0).sum()):4d}  "
            f"h<$1 {int((lw < 1).sum()):4d}  h<$15 {int((lw < 15).sum()):4d}"
        )
        print("  -- per-zone bands --")
        for z in pz.columns:
            p = pz[z].to_numpy()
            print(
                f"   {z:<14} min {np.nanmin(p):8.2f}  h<-$1 {int((p < -1).sum()):4d}"
                f"  h<$0 {int((p < 0).sum()):4d}  h<=$0.01 {int((p <= 0.01).sum()):4d}"
                f"  h<$15 {int((p < 15).sum()):4d}"
            )

        # Depth histogram of the epoch hours (any zone <= $0.01): where do
        # the zonal duals actually sit — $0, the blend, or the full -PTC?
        epoch_mask = (pz <= 0.01).any(axis=1).to_numpy()
        vals = pz.to_numpy()[epoch_mask]
        vals = vals[vals <= 0.01]
        if vals.size:
            qs = np.percentile(vals, [0, 5, 25, 50, 75, 100])
            print(
                f"  epochs: {int(epoch_mask.sum())} zonal-epoch hours; dual "
                "quantiles in-epoch [min/p5/p25/p50/p75/max] "
                + " ".join(f"{q:7.2f}" for q in qs)
            )
            breadth = (pz.le(0.01).sum(axis=1))[epoch_mask]
            print(
                "  breadth (zones simultaneously <= $0.01): "
                f"mean {breadth.mean():.2f}, p90 {breadth.quantile(0.9):.0f}, "
                f"max {breadth.max():.0f} of {pz.shape[1]}"
            )
        else:
            print("  epochs: none")

        # The reach question: what does the model do in RT's negative hours?
        in_rt_neg = lw[rt_neg[: len(lw)]]
        if in_rt_neg.size:
            print(
                f"  model lw price in RT's {int(rt_neg.sum())} negative hours: "
                f"min {np.nanmin(in_rt_neg):.2f}  median {np.nanmedian(in_rt_neg):.2f}"
                f"  mean {np.nanmean(in_rt_neg):.2f}  "
                f"model<0 in {int((in_rt_neg < 0).sum())} of them"
            )


if __name__ == "__main__":
    main()
