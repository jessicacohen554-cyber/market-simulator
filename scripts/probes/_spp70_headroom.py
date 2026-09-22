"""SPP-70 — is the model's price low because the stack is exhausted, or because
the price never climbs it?  ZERO LP.

Rebuilds the LP's own hourly offer array (``mc_base``) and hourly availability
through the sanctioned ``fleet_only`` reconstruction, joins it to the SAME
bundle's committed P1 system prices, and reports per hour how much thermal
capacity was available ABOVE the clearing price (the headroom the LP declined
to use) versus how much was exhausted below it.

An exhausted stack in the peak hours means the model is capacity-short and the
missing tail is a scarcity object.  Large headroom in the peak hours means the
stack is never climbed and the missing tail is an above-marginal-cost object
(congestion rent, markup, opportunity cost) that no offer-curve band can reach.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

BUNDLES = {
    2019: "spp67_yearown_rung",
    2020: "spp67_yearown_rung",
    2021: "spp67_yearown_rung",
    2022: "spp67_yearown_rung",
    2023: "spp67_yearown_span",
    2024: "spp67_yearown_span",
    2025: "spp67_yearown_span",
}
THERMAL_PREFIXES = ("COAL", "CC_", "CT_", "ST_")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()
    y = args.year
    bundle = REPO / "results/calibration" / BUNDLES[y]

    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet
    from scripts.run_calibration_full import _coal_supply_class

    state, _meta = reconstruct_bundle_fleet(bundle, y, verbose=False)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)  # (n_gen, T)
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    if avail.ndim == 1:
        avail = np.broadcast_to(avail[:, None], mc.shape)

    groups = fa.plant_group
    codes = np.asarray(fa.plant_code)
    klass = []
    for i in range(len(fa.unit_ids)):
        g = str(groups[i]) if groups is not None else ""
        klass.append(_coal_supply_class(int(codes[i])) if g == "COAL" else g)
    th = np.array([str(k).startswith(THERMAL_PREFIXES) for k in klass])

    mc, cap = mc[th], (pmax[:, None] * avail)[th]
    T = mc.shape[1]

    s = pd.read_parquet(bundle / "hourly" / f"system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    price = (
        s.groupby("hour")
        .apply(
            lambda g: np.average(g["price"], weights=g["demand"]), include_groups=False
        )
        .reindex(range(T))
        .to_numpy()
    )
    load = s.groupby("hour")["demand"].sum().reindex(range(T)).to_numpy()

    above = (mc > price[None, :]) * cap  # MW offered above the clearing price
    hr_above = above.sum(axis=0) / 1000.0  # GW
    hr_total = cap.sum(axis=0) / 1000.0

    order = np.argsort(-load)
    print(
        f"\n=== SPP {y} — headroom above the clearing price (bundle {BUNDLES[y]}) ==="
    )
    print(
        f"{'hour set':<22} {'n':>6} {'load GW':>8} {'price $':>8} "
        f"{'thermal avail GW':>17} {'GW above price':>15} {'% above':>8}"
    )
    for name, idx in (
        ("top 10 load hours", order[:10]),
        ("top 100 load hours", order[:100]),
        ("top 500 load hours", order[:500]),
        ("all hours", np.arange(T)),
    ):
        print(
            f"{name:<22} {len(idx):>6} {load[idx].mean() / 1000:>8.2f} {price[idx].mean():>8.2f} "
            f"{hr_total[idx].mean():>17.2f} {hr_above[idx].mean():>15.2f} "
            f"{100 * hr_above[idx].mean() / hr_total[idx].mean():>7.1f}%"
        )
    print(
        f"\nminimum headroom in ANY hour: {hr_above.min():.2f} GW "
        f"(hour {int(np.argmin(hr_above))}, price ${price[int(np.argmin(hr_above))]:.2f}, "
        f"load {load[int(np.argmin(hr_above))] / 1000:.2f} GW)"
    )
    print(f"hours with < 1 GW of headroom: {(hr_above < 1.0).sum()} of {T}")
    print(
        f"max thermal offer in the whole year: ${mc.max():.2f}/MWh ; "
        f"max clearing price ${np.nanmax(price):.2f}/MWh"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
