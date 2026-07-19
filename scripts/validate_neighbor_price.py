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
The ISO's own price is taken as its *actual* hourly LMP — the realized-price
comparison, and the best pre-LP proxy for the LP energy dual the wired-in seam
will clear against.

Nothing here is tuned to the net-MWh flow; the neighbor heat rates are anchored
to each neighbor's *own* realized LMP (claude.md rule #11). A residual is a
structural finding to surface, not something to fit away.

Usage:
    python scripts/validate_neighbor_price.py --iso PJM --years 2023 2024 2025
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
from market_sim.config.paths import CALIBRATION_DIR
from market_sim.data.eia_loader import _eia930_net_interchange
from market_sim.data.neighbor_price import (
    interface_reference_prices,
    seam_flow_direction,
)

HOURS = 8760
# Measured actual-LMP parquets live under the single W1 data root
# (paths.CALIBRATION_DIR = data/raw/_validation-source); the pre-W1
# ``inputs/calibration`` path was removed by the relocation.
_LMP_DIR = CALIBRATION_DIR

# EIA-930 BA code for each ISO's own net interchange (export-positive).
_ISO_BA = {"PJM": "PJM", "CAISO": "CISO", "NYISO": "NYIS", "NEISO": "ISNE"}
# Neighbor name -> modeled-ISO LMP file stem, when the neighbor's real hourly
# LMP is on file (so the constructed price can be checked against it directly).
_NEIGHBOR_LMP_ISO = {"NYISO": "NYISO"}


def _actual_lmp(iso: str, year: int) -> np.ndarray | None:
    """Return the ISO's clean actual RT LMP for ``year``.

    The measured LMP parquet is a *required* input for this validation gate: an
    absent file is a hard error, never a silent skip. (The pre-W1
    ``inputs/calibration`` dead path meant this always resolved to a missing
    file, so every comparison degraded to a no-op and the gate silently passed —
    fail loudly instead so a missing reference cannot hide a broken gate.)
    ``None`` is returned only when the file is present but its on-file series has
    the wrong length (a data-quality skip, distinct from an absent file).
    """
    path = _LMP_DIR / f"actual_lmp_hourly_{iso}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"measured actual-LMP file absent: {path} — required by "
            f"validate_neighbor_price for {iso}; build it with "
            f"scripts/data/derive_actual_lmp.py"
        )
    df = pd.read_parquet(path)
    s = df[df["year"] == year].sort_values("hour")["rt"]
    if len(s) != HOURS:
        return None
    return s.interpolate().bfill().ffill().to_numpy(dtype=float)


def _direction_score(
    iso_price: np.ndarray,
    neighbor_price: np.ndarray,
    hurdle: float,
    net_export: np.ndarray,
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
    print(f"\n=== Reference-price validation: {iso} (hurdle ${hurdle:.0f}/MWh) ===")

    for year in years:
        res = interface_reference_prices(iso, year, HOURS)
        agg = res.aggregate()
        if agg is None:
            print(f"\n{year}: no neighbor prices resolved (missing {res.missing}).")
            continue
        print(f"\n--- {year} ---")
        print(f"resolved: {list(res.per_neighbor)}  missing: {res.missing}")

        # 1. Per-neighbor price level + shape vs actual neighbor LMP.
        for name, price in res.per_neighbor.items():
            line = f"  {name:10s} ba={res.ba_used[name]:5s} mean ${price.mean():6.2f}"
            lmp_iso = _NEIGHBOR_LMP_ISO.get(name)
            actual = _actual_lmp(lmp_iso, year) if lmp_iso else None
            if actual is not None:
                corr = float(np.corrcoef(price, actual)[0, 1])
                line += (
                    f"  | actual {name} LMP ${actual.mean():6.2f} "
                    f"shape-corr {corr:+.2f}"
                )
            print(line)

        # 2 & 3. Seam direction vs measured net interchange, both framings.
        net_export = _eia930_net_interchange(ba, year) if ba else None
        if net_export is None:
            print("  (no measured net interchange — skipping direction score)")
            continue
        iso_actual = _actual_lmp(iso, year)
        print(
            f"  measured net export: mean {net_export.mean():7.1f} MW  "
            f"({net_export.sum() / 1e6:+.2f} TWh)  "
            f"export-hours {float((net_export > 0).mean()):.2f}"
        )
        if iso_actual is None:
            print("  (no actual ISO LMP — skipping direction score)")
            continue
        mexp, pexp, hit, corr = _direction_score(iso_actual, agg, hurdle, net_export)
        print(
            f"    [actual-LMP] {iso} mean ${iso_actual.mean():6.2f} "
            f"vs neigh ${agg.mean():6.2f}  "
            f"meas export-share {mexp:.2f}  pred {pexp:.2f}  "
            f"dir hit-rate {hit:.2f}  corr(spread,-netexp) {corr:+.2f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", default="PJM")
    parser.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = parser.parse_args()
    validate(args.iso, args.years)


if __name__ == "__main__":
    main()
