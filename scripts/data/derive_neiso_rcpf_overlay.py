"""Derive the NEISO (ISO-NE) RCPF scarcity-price overlay for a solved bundle.

Post-solve only: reads a persisted NEISO calibration bundle (dispatch +
system parquets), reconstructs the hourly fleet availability the LP solved
against (same config, same outage overlay — no LP is re-solved), computes
the hourly reserve headroom and applies ISO-NE's Reserve Constraint Penalty
Factor demand curve (market_sim.results.rcpf with constants.NEISO_RCPF_PRODUCTS).
Volumes, dispatch parquets and emissions are untouched; the overlay is written
as a separate ``scarcity.parquet`` series next to the energy-only LMP.

The ISO-NE analogue of scripts/data/derive_nyiso_rcpf_overlay.py — same market
design (a stacked reserve-demand-curve adder), same reserve definition
(dispatchable thermal + storage headroom; curtailed renewables do NOT count),
same post-solve / LP-untouched contract. ISO-NE differs only in the product
table (TMSR / total-10-min / total-30-min, sourced ISO-NE tariff RCPFs) and in
recovering fixed cost through the Forward Capacity Market, so the overlay owns
the price TAIL only: it is $0 whenever reserves clear the requirement, which is
essentially every hour of the calm 2023-25 backcast. The lever exists for
forward / scarcity scenarios where reserves tighten, not to move the backcast.

System-wide only (the pool-wide RCPF). ISO-NE's local reserve zones
(NEMA/Boston, CT, SWCT; $250/MWh TMOR) need per-zone headroom and are a
locational follow-up, exactly as for NYISO.

Usage:
    python scripts/data/derive_neiso_rcpf_overlay.py results/calibration/neiso_monthly_keeper
        [--years 2023 2024 2025] [--tag scenarioX] [--rebuild-availability]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

sys.path.insert(0, str(REPO / "scripts" / "data"))
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.results.rcpf import (  # noqa: E402
    rcpf_product_prices,
    resolve_rcpf_products,
)

# The reserve fleet, availability reconstruction, storage headroom, system
# price and reporting helpers are market-design-agnostic — ISO-NE's reserve
# fuels (gas + oil) are the same set NYISO uses — so reuse them directly
# rather than fork a second copy.
from derive_nyiso_rcpf_overlay import (  # noqa: E402
    _demand_weights,
    _dist,
    _final_pass,
    _mae,
    _storage_headroom,
    _system_lambda,
    build_availability,
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--years", nargs="+", type=int, default=None)
    ap.add_argument(
        "--tag", default=None, help="write scarcity_<tag>.parquet (scenario runs)"
    )
    ap.add_argument("--rebuild-availability", action="store_true")
    args = ap.parse_args()

    bundle = args.bundle.resolve()
    meta = json.loads((bundle / "meta.json").read_text())
    if meta["iso"] != "NEISO":
        raise SystemExit("NEISO RCPF scarcity overlay is NEISO-only")
    years = args.years or meta["years"]
    hours = meta["hours"]
    pass_label = _final_pass(meta.get("passes", ["P1"]))

    config = ScenarioConfig(iso="NEISO", mode="backcast", neiso_rcpf_enabled=True)
    products = resolve_rcpf_products(config)
    print(f"bundle {bundle.name}: years {years}, reported pass {pass_label}")
    print("ISO-NE RCPF products (name, requirement_MW, critical_MW, max_$/MWh):")
    for prod in products:
        print(
            f"  {prod[0]}: req {prod[1]:,.0f}  crit {prod[2]:,.0f}  max ${prod[3]:,.0f}"
        )

    avail = build_availability(
        bundle, years, meta, pass_label, force=args.rebuild_availability
    )

    frames = []
    for year in years:
        a = avail[avail["year"] == year]
        cap_t = a["storage_power_cap_mw"].to_numpy(float)
        reserves = (
            a["thermal_avail_mw"].to_numpy(float)
            - a["thermal_dispatch_mw"].to_numpy(float)
            + _storage_headroom(bundle, year, hours, pass_label, cap_t)
        )
        pp = rcpf_product_prices(reserves, config)
        adder = pp["adder"]
        lam = _system_lambda(bundle, year, hours, pass_label)

        frame = {
            "year": np.int16(year),
            "hour": np.arange(hours, dtype=np.int32),
            "reserves_mw": reserves.astype(np.float32),
            "scarcity_adder": adder.astype(np.float32),
            "lmp": lam.astype(np.float32),
            "lmp_scarcity": (lam + adder).astype(np.float32),
        }
        for prod in products:
            frame[f"price_{prod[0]}"] = pp[prod[0]].astype(np.float32)
        frames.append(pd.DataFrame(frame))

        w = _demand_weights(bundle, year, hours, pass_label)
        print(
            f"\n{year}: adder>$1 in {int((adder > 1).sum())} h, >$50 in "
            f"{int((adder > 50).sum())} h, >$200 in "
            f"{int((adder > 200).sum())} h, max ${adder.max():,.0f}; "
            f"mean ${adder.mean():.2f}"
        )
        print(
            f"  reserves (MW) p1/p5/p50 = "
            f"{np.percentile(reserves, [1, 5, 50]).round(0)}  "
            f"(min req {products[-1][1]:,.0f})"
        )
        md0, md1 = _dist(lam), _dist(lam + adder)
        cols = ["min", "p50", "p95", "p99", "max"]
        print("  model price ($/MWh)    " + "  ".join(f"{c:>7}" for c in cols))
        print("    energy-only          " + "  ".join(f"{md0[c]:7.0f}" for c in cols))
        print("    + RCPF scarcity      " + "  ".join(f"{md1[c]:7.0f}" for c in cols))
        # Demand-weighted mean price shift the overlay introduces (the body of
        # the distribution must be untouched: this should be ~0 in the calm
        # backcast and only grows in tight forward scenarios).
        shift = _mae(lam + adder, lam, w)
        print(f"  dw-mean |price shift| from overlay: ${shift:.3f}/MWh")

    out = pd.concat(frames, ignore_index=True)
    name = f"scarcity_{args.tag}.parquet" if args.tag else "scarcity.parquet"
    out.to_parquet(bundle / name, index=False)
    print(f"\nwrote {bundle / name}")


if __name__ == "__main__":
    main()
