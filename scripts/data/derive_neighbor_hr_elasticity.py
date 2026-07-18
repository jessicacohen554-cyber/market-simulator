"""Fit each neighbor's FORWARD gas-price-elastic implied heat rate from measured LMP.

The reference-price interface (:mod:`market_sim.data.neighbor_price`) prices each
seam as ``(henry_hub + gas_basis) x heat_rate x load_shape``. For BACKCAST years
the heat rate is the neighbor's OWN measured annual-mean LMP-implied ratio
(``hr_by_year``); for FORECAST years it previously fell back to a single flat
``marginal_heat_rate`` — a multi-year mean that under-prices the seam when gas is
dear and over-prices wind-set neighbors in the same years (the gap documented in
``docs/forecast-methodology-gaps-2026-06.md`` G11).

This script derives the forward replacement: a **gas-price-elastic implied HR**.
A neighbor's realized annual-mean LMP is, to first order, affine in delivered
gas::

    LMP[year] ~= hr_phys x gas[year] + hr_adder

where ``hr_phys`` (MMBtu/MWh) is the gas-proportional price-setting heat rate and
``hr_adder`` ($/MWh) the roughly fixed non-gas component (congestion, scarcity,
non-gas marginal units). The effective implied HR is then ``hr_phys + hr_adder /
gas``, which eases toward ``hr_phys`` as gas rises — a wind-set neighbor (small
``hr_phys``, large ``hr_adder``) barely lifts its LMP when gas spikes, exactly as
the measured SPP 2025 ratio collapsed to 7.7.

The two coefficients are an ordinary least-squares fit of the neighbor's OWN
measured ``(gas, LMP)`` points (``actual_lmp_hourly_<ISO>.parquet`` divided only
by the load-shape convexity ``K`` so the constructed ANNUAL MEAN, not just the
baseload, matches). This is a measured neighbor price-formation input (claude.md
rule #12); it NEVER reads the ISO's own interchange (rule #11) — the derivation
sees only the neighbor's price and the Henry Hub trajectory.

The script also prints a forward-skill table: for each measured year it compares
the FLAT mean, the ELASTIC formula, and the measured realization of the implied
HR, so you can confirm the elastic forward fallback tracks the dear-gas / cheap-
gas years the flat mean misses. Run::

    python scripts/data/derive_neighbor_hr_elasticity.py --iso MISO

and paste the emitted ``hr_gas_elastic=(...)`` coefficients into the
``_HR_GAS_ELASTIC`` map in ``market_sim.data.neighbor_price``.
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
# marginal_heat_rate and gets no elasticity fit.
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


def _neighbor_points(
    neighbor, lmp_iso: str, years: list[int]
) -> tuple[np.ndarray, np.ndarray] | None:
    """Return the neighbor's measured ``(gas, mean_LMP / K)`` points for the fit.

    ``K = mean(load_shape ** exponent)`` divides out the convexity inflation of
    the load-shape multiplier so the affine fit targets the constructed ANNUAL
    MEAN (which the seam reproduces), not just the baseload. ``None`` when no
    usable measured year resolves.
    """
    gas_pts: list[float] = []
    price_pts: list[float] = []
    for year in years:
        measured = _measured_mean_lmp(lmp_iso, year)
        shaped = neighbor_load_shape(neighbor, year, _HOURS)
        if measured is None or shaped is None:
            continue
        k = float(np.nanmean(shaped[0]))  # shape already exponentiated
        gas_pts.append(neighbor_gas_price(neighbor, year))
        price_pts.append(measured / k)
    if len(gas_pts) < 2:
        return None
    return np.array(gas_pts), np.array(price_pts)


def derive(iso: str, years: list[int]) -> dict[str, tuple[float, float]]:
    """Return ``{neighbor_name: (hr_phys, hr_adder)}`` fit to measured neighbor LMP."""
    out: dict[str, tuple[float, float]] = {}
    for neighbor in INTERFACE_NEIGHBORS.get(iso, []):
        lmp_iso = _NEIGHBOR_LMP_ISO.get(neighbor.name)
        if lmp_iso is None:
            continue
        pts = _neighbor_points(neighbor, lmp_iso, years)
        if pts is None:
            continue
        gas, price = pts
        # Affine LMP = hr_phys * gas + hr_adder (least squares, slope = hr_phys).
        hr_phys, hr_adder = np.polyfit(gas, price, 1)
        out[neighbor.name] = (round(float(hr_phys), 2), round(float(hr_adder), 2))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    table = derive(args.iso, args.years)
    print(f"# Derived gas-elastic neighbor heat rates for {args.iso}")
    print("# Paste the hr_gas_elastic=(hr_phys, hr_adder) tuple per neighbor.\n")
    for neighbor in INTERFACE_NEIGHBORS.get(args.iso, []):
        if neighbor.name not in table:
            continue
        hr_phys, hr_adder = table[neighbor.name]
        flat = neighbor.marginal_heat_rate
        print(f"    {neighbor.name}: hr_gas_elastic=({hr_phys}, {hr_adder})")
        print(
            f"      forward implied HR(gas) = {hr_phys} + {hr_adder}/gas   (flat {flat})"
        )
        # Forward-skill table: flat vs elastic vs measured implied HR per year.
        print("      year   gas   measHR  flatHR  elastHR  |flat-meas|  |elast-meas|")
        for year in args.years:
            measured = _measured_mean_lmp(_NEIGHBOR_LMP_ISO[neighbor.name], year)
            shaped = neighbor_load_shape(neighbor, year, _HOURS)
            if measured is None or shaped is None:
                continue
            k = float(np.nanmean(shaped[0]))
            gas = neighbor_gas_price(neighbor, year)
            meas_hr = measured / (gas * k)
            elast_hr = hr_phys + hr_adder / gas
            print(
                f"      {year}  {gas:5.2f}  {meas_hr:6.2f}  {flat:6.2f}  "
                f"{elast_hr:6.2f}     {abs(flat - meas_hr):6.2f}       "
                f"{abs(elast_hr - meas_hr):6.2f}"
            )
        print()


if __name__ == "__main__":
    main()
