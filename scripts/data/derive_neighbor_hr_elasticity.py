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

THE ANCHORS ARE PER ISO (lane soco-98, 2026-10-01, repairing FINDING-soco-33
§7 R-1). This script used to resolve each neighbour through a GLOBAL name map
(``MISO``/``NYISO``/``PJM``/``SPP``) and exit 0 with an empty table for any
ISO whose neighbours it did not name — every SPP and SOCO seam. It now reads
the SAME per-ISO anchor map as ``derive_neighbor_hr_by_year.py``
(:data:`NEIGHBOR_LMP_ANCHORS`, both anchor kinds), so the fit and the
per-year table can never anchor one seam to two different series; an ISO with
no map FAILS, a declared anchor with no measured year FAILS, and an
unanchored neighbour is PRINTED, never silently dropped.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
from derive_neighbor_hr_by_year import (
    NEIGHBOR_LMP_ANCHORS,
    Anchor,
    _measured_mean_lmp,
    unanchored,
)

from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
from market_sim.data.neighbor_price import neighbor_gas_price, neighbor_load_shape

_HOURS = 8760


def _neighbor_points(
    neighbor, anchor: Anchor, years: list[int]
) -> tuple[np.ndarray, np.ndarray, list[int]] | None:
    """Return the neighbor's measured ``(gas, mean_price / K)`` points for the fit.

    ``K = mean(load_shape ** exponent)`` divides out the convexity inflation of
    the load-shape multiplier so the affine fit targets the constructed ANNUAL
    MEAN (which the seam reproduces), not just the baseload. A year with no
    measured anchor or no load shape is left out; ``None`` when fewer than two
    usable years resolve. The third element lists the years used.
    """
    gas_pts: list[float] = []
    price_pts: list[float] = []
    used: list[int] = []
    for year in years:
        measured = _measured_mean_lmp(anchor, year)
        shaped = neighbor_load_shape(neighbor, year, _HOURS)
        if measured is None or shaped is None:
            continue
        k = float(np.nanmean(shaped[0]))  # shape already exponentiated
        gas_pts.append(neighbor_gas_price(neighbor, year))
        price_pts.append(measured / k)
        used.append(year)
    if len(gas_pts) < 2:
        return None
    return np.array(gas_pts), np.array(price_pts), used


def derive(iso: str, years: list[int]) -> dict[str, tuple[float, float]]:
    """Return ``{neighbor_name: (hr_phys, hr_adder)}`` fit to measured neighbor prices.

    Raises:
        KeyError: ``iso`` has no anchor map in :data:`NEIGHBOR_LMP_ANCHORS`.
        FileNotFoundError: a declared anchor resolves fewer than two usable
            ``(gas, price)`` points over ``years``.
    """
    if iso not in NEIGHBOR_LMP_ANCHORS:
        raise KeyError(
            f"{iso}: no neighbour anchor map registered in NEIGHBOR_LMP_ANCHORS"
        )
    anchors = NEIGHBOR_LMP_ANCHORS[iso]
    out: dict[str, tuple[float, float]] = {}
    for neighbor in INTERFACE_NEIGHBORS.get(iso, []):
        anchor = anchors.get(neighbor.name)
        if anchor is None:
            continue
        pts = _neighbor_points(neighbor, anchor, years)
        if pts is None:
            raise FileNotFoundError(
                f"{iso}/{neighbor.name}: declared anchor resolves fewer than two "
                f"measured years with a load shape in {years}"
            )
        gas, price, _used = pts
        # Affine price = hr_phys * gas + hr_adder (least squares, slope = hr_phys).
        hr_phys, hr_adder = np.polyfit(gas, price, 1)
        out[neighbor.name] = (round(float(hr_phys), 2), round(float(hr_adder), 2))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    iso = args.iso.upper()
    try:
        table = derive(iso, args.years)
    except (KeyError, FileNotFoundError) as exc:
        sys.exit(f"derive_neighbor_hr_elasticity: {exc}")
    print(f"# Derived gas-elastic neighbor heat rates for {iso}")
    print("# Paste the hr_gas_elastic=(hr_phys, hr_adder) tuple per neighbor.\n")
    for neighbor in INTERFACE_NEIGHBORS.get(iso, []):
        if neighbor.name not in table:
            continue
        hr_phys, hr_adder = table[neighbor.name]
        flat = neighbor.marginal_heat_rate
        anchor = NEIGHBOR_LMP_ANCHORS[iso][neighbor.name]
        gas_pts, price_pts, used = _neighbor_points(neighbor, anchor, args.years)
        fitted = hr_phys * gas_pts + hr_adder
        ss_res = float(np.sum((price_pts - fitted) ** 2))
        ss_tot = float(np.sum((price_pts - price_pts.mean()) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        print(f"    {neighbor.name}: hr_gas_elastic=({hr_phys}, {hr_adder})")
        print(
            f"      forward implied HR(gas) = {hr_phys} + {hr_adder}/gas   (flat {flat})"
            f"   n={len(used)} r2={r2:.3f}"
        )
        # Forward-skill table: flat vs elastic vs measured implied HR per year.
        print("      year   gas   measHR  flatHR  elastHR  |flat-meas|  |elast-meas|")
        for year, gas, price in zip(used, gas_pts, price_pts):
            meas_hr = price / gas
            elast_hr = hr_phys + hr_adder / gas
            print(
                f"      {year}  {gas:5.2f}  {meas_hr:6.2f}  {flat:6.2f}  "
                f"{elast_hr:6.2f}     {abs(flat - meas_hr):6.2f}       "
                f"{abs(elast_hr - meas_hr):6.2f}"
            )
        print()
    for name in unanchored(iso):
        print(f"# {name}: no measured anchor registered — no elasticity fit")


if __name__ == "__main__":
    main()
