"""Derive per-backcast-year neighbor marginal heat rates from measured LMP.

The reference-price interface (``market_sim.data.neighbor_price``) prices each
PJM seam as ``(henry_hub + gas_basis) x marginal_heat_rate x load_shape``. The
registry carries ONE ``marginal_heat_rate`` per neighbor — a 3-year *mean* of
the neighbor's realized LMP / Henry-Hub ratio. Because the real ratio drifts
year to year (MISO 12.5 / 14.1 / 12.2 for 2023-25), the single mean over-prices
the neighbor in the dear-gas year and under-prices it in the cheap-gas year,
opening (closing) a fake export spread on the seam — the root of the PJM 2025
over-export / 2024 under-export.

This script re-anchors the heat rate PER YEAR to the neighbor's OWN measured
annual-mean realized LMP (``actual_lmp_hourly_<ISO>.parquet``) so the
constructed seam reference reproduces the neighbor's realized annual mean each
backcast year:

    HR[year] = measured_mean_LMP[year]
               / ((henry_hub[year] + gas_basis) x K[year])

where ``K[year] = mean(load_shape ** exponent)`` is the convexity inflation of
the load-shape multiplier (so the constructed ANNUAL MEAN, not just the
baseload, equals the measured mean). This is a measured neighbor price-formation
input (claude.md rule #12 — measured over estimate; the forward analogue is the
structural ``marginal_heat_rate``, used whenever a year has no measured LMP), it
is NOT tuned to PJM's net interchange (rule #11) — it never sees PJM's flow.

Only neighbors that are themselves modeled ISOs with a committed realized-LMP
product (MISO, NYISO) get a year table; the Carolinas (no organized market) keep
the structural estimate. Run::

    python scripts/data/derive_neighbor_hr_by_year.py --iso PJM

and paste the emitted ``INTERFACE_NEIGHBOR_HR_BY_YEAR`` block into constants.py.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from market_sim.config import paths
from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
from market_sim.data.neighbor_price import neighbor_gas_price, neighbor_load_shape

# Neighbor name -> the ISO code whose realized-LMP product anchors it. A neighbor
# absent here (no organized-market LMP, e.g. the Carolinas) keeps the structural
# marginal_heat_rate and gets no year table.
_NEIGHBOR_LMP_ISO: dict[str, str] = {
    "MISO": "MISO",
    "NYISO": "NYISO",
    "PJM": "PJM",
    "SPP": "SPP",
}

_HOURS = 8760


def _measured_mean_lmp(iso: str, year: int, run: str = "rt") -> float | None:
    """Return the neighbor's realized annual-mean LMP ($/MWh), or None if absent."""
    path = paths.CALIBRATION_DIR / f"actual_lmp_hourly_{iso}.parquet"
    if not path.is_file():
        return None
    df = pd.read_parquet(path)
    rows = df[df["year"] == year]
    if rows.empty or run not in rows.columns:
        return None
    return float(np.nanmean(rows[run].to_numpy(dtype=float)))


def derive(iso: str, years: list[int]) -> dict[str, dict[int, float]]:
    """Return ``{neighbor_name: {year: hr}}`` anchored to measured neighbor LMP."""
    out: dict[str, dict[int, float]] = {}
    for neighbor in INTERFACE_NEIGHBORS.get(iso, []):
        lmp_iso = _NEIGHBOR_LMP_ISO.get(neighbor.name)
        if lmp_iso is None:
            continue
        per_year: dict[int, float] = {}
        for year in years:
            measured = _measured_mean_lmp(lmp_iso, year)
            shaped = neighbor_load_shape(neighbor, year, _HOURS)
            if measured is None or shaped is None:
                continue
            k = float(np.nanmean(shaped[0] ** 1.0))  # shape already exponentiated
            gas = neighbor_gas_price(neighbor, year)
            hr = measured / (gas * k)
            per_year[year] = round(hr, 2)
        if per_year:
            out[neighbor.name] = per_year
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="PJM")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    table = derive(args.iso, args.years)
    print(f"# Derived measured-anchored neighbor heat rates for {args.iso}")
    for name, per_year in table.items():
        cur = next(
            n.marginal_heat_rate
            for n in INTERFACE_NEIGHBORS[args.iso]
            if n.name == name
        )
        cells = ", ".join(f"{y}: {hr}" for y, hr in sorted(per_year.items()))
        print(f'    "{name}": {{{cells}}},   # structural HR {cur}')


if __name__ == "__main__":
    main()
