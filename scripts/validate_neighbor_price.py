"""Validate the reference-price interface against measured data — no LP.

Step (1) of the reference-price interface (model-methodology-spec §8.3): before
the neighbor price is wired into the dispatch LP, this script checks the pure
construction in :mod:`market_sim.data.neighbor_price` against three measured
benchmarks on the backcast, so the mechanism is vetted on its own terms:

1. **Price level + shape** — for any neighbor that is itself a modeled ISO with
   an actual hourly LMP on file (e.g. PJM's NYISO neighbor), the constructed
   reference price is compared to the real neighbor LMP (mean, and Pearson
   correlation of the hourly shape).
2. **Seam direction** — the sign of the ISO↔neighbor price spread is turned
   into an import/export/hold call (the hurdle dead-band) and scored against the
   measured EIA-930 net interchange (export-positive): the share of hours the
   spread calls the flow direction correctly, plus the correlation of the spread
   with the measured net export.
3. **Like-for-like vs actual-LMP framing** — the spread is reported both ways:
   the ISO's *own* reference price vs the neighbor's (the marginal-cost
   comparison the LP dual will make), and the ISO's *actual* LMP vs the
   neighbor's (the realized-price comparison).

Nothing here is tuned; the script only reports. A poor score is a structural
finding to surface, not a residual to fit (claude.md rule #1).

Usage:
    python scripts/validate_neighbor_price.py --iso PJM --years 2023 2024 2025
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    GAS_BASIS_DIFFERENTIAL,
    INTERFACE_NEIGHBORS,
    NeighborInterface,
)
from market_sim.data.eia_loader import _eia930_net_interchange
from market_sim.data.neighbor_price import (
    interface_reference_prices,
    neighbor_reference_price,
    seam_flow_direction,
)

HOURS = 8760
_LMP_DIR = Path(__file__).resolve().parents[1] / "inputs" / "calibration"

# EIA-930 BA code for each ISO's own net interchange (export-positive).
_ISO_BA = {"PJM": "PJM", "CAISO": "CISO", "NYISO": "NYIS", "NEISO": "ISNE"}
# Neighbor name -> modeled-ISO LMP file stem, when the neighbor's real hourly
# LMP is on file (so the constructed price can be checked against it directly).
_NEIGHBOR_LMP_ISO = {"NYISO": "NYISO"}


def _actual_lmp(iso: str, year: int) -> np.ndarray | None:
    """Return the ISO's clean actual RT LMP for ``year`` (or ``None``)."""
    path = _LMP_DIR / f"actual_lmp_hourly_{iso}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    s = df[df["year"] == year].sort_values("hour")["rt"]
    if len(s) != HOURS:
        return None
    return s.interpolate().bfill().ffill().to_numpy(dtype=float)


def _own_reference_price(iso: str, year: int) -> np.ndarray | None:
    """Return the ISO's *own* reference price, built like a neighbor's.

    Uses the ISO's gas basis, the shared marginal heat rate, and the ISO's own
    load shape — the gas-marginal cost the LP dual approximates. ``None`` when
    the ISO's gas basis or load extract is unavailable.
    """
    basis = GAS_BASIS_DIFFERENTIAL.get(iso)
    if basis is None:
        return None
    hr = INTERFACE_NEIGHBORS.get(iso, [NeighborInterface(
        name="", ba_code="", gas_basis=0.0, marginal_heat_rate=7.5,
        hurdle=3.0, interface_limit_mw=1.0, border_zones=())])[0].marginal_heat_rate
    self_spec = NeighborInterface(
        name=f"{iso}_self", ba_code=iso, gas_basis=basis,
        marginal_heat_rate=hr, hurdle=3.0, interface_limit_mw=1.0,
        border_zones=(),
    )
    priced = neighbor_reference_price(self_spec, year, HOURS)
    return priced[0] if priced is not None else None


def _direction_score(
    iso_price: np.ndarray, neighbor_price: np.ndarray,
    hurdle: float, net_export: np.ndarray,
) -> tuple[float, float, float, float]:
    """Return (export-share measured, predicted, hit-rate, spread-corr)."""
    direction = seam_flow_direction(iso_price, neighbor_price, hurdle)
    meas_export = net_export > 0.0
    pred_export = direction < 0.0  # -1 = export
    hit = float((pred_export == meas_export).mean())
    spread = iso_price - neighbor_price
    corr = float(np.corrcoef(spread, -net_export)[0, 1])
    return float(meas_export.mean()), float(pred_export.mean()), hit, corr


def validate(iso: str, years: list[int]) -> None:
    """Print the reference-price validation report for ``iso`` over ``years``."""
    neighbors = INTERFACE_NEIGHBORS.get(iso, [])
    if not neighbors:
        print(f"No neighbor registry for {iso}.")
        return
    hurdle = neighbors[0].hurdle  # uniform across the registry today
    ba = _ISO_BA.get(iso)
    print(f"\n=== Reference-price validation: {iso} "
          f"(hurdle ${hurdle:.0f}/MWh) ===")

    for year in years:
        res = interface_reference_prices(iso, year, HOURS)
        agg = res.aggregate()
        if agg is None:
            print(f"\n{year}: no neighbor prices resolved "
                  f"(missing {res.missing}).")
            continue
        print(f"\n--- {year} ---")
        print(f"resolved: {list(res.per_neighbor)}  missing: {res.missing}")

        # 1. Per-neighbor price level + shape vs actual neighbor LMP.
        for name, price in res.per_neighbor.items():
            line = (f"  {name:10s} ba={res.ba_used[name]:5s} "
                    f"mean ${price.mean():6.2f}")
            lmp_iso = _NEIGHBOR_LMP_ISO.get(name)
            actual = _actual_lmp(lmp_iso, year) if lmp_iso else None
            if actual is not None:
                corr = float(np.corrcoef(price, actual)[0, 1])
                line += (f"  | actual {name} LMP ${actual.mean():6.2f} "
                         f"shape-corr {corr:+.2f}")
            print(line)

        # 2 & 3. Seam direction vs measured net interchange, both framings.
        net_export = _eia930_net_interchange(ba, year) if ba else None
        if net_export is None:
            print("  (no measured net interchange — skipping direction score)")
            continue
        iso_actual = _actual_lmp(iso, year)
        iso_ref = _own_reference_price(iso, year)
        print(f"  measured net export: mean {net_export.mean():7.1f} MW  "
              f"({net_export.sum() / 1e6:+.2f} TWh)  "
              f"export-hours {float((net_export > 0).mean()):.2f}")
        for label, iso_price in (("actual-LMP", iso_actual),
                                 ("own-ref", iso_ref)):
            if iso_price is None:
                continue
            mexp, pexp, hit, corr = _direction_score(
                iso_price, agg, hurdle, net_export)
            print(f"    [{label:10s}] {iso} mean ${iso_price.mean():6.2f} "
                  f"vs neigh ${agg.mean():6.2f}  "
                  f"pred export-share {pexp:.2f}  dir hit-rate {hit:.2f}  "
                  f"corr(spread,-netexp) {corr:+.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", default="PJM")
    parser.add_argument("--years", type=int, nargs="+",
                        default=[2023, 2024, 2025])
    args = parser.parse_args()
    validate(args.iso, args.years)


if __name__ == "__main__":
    main()
