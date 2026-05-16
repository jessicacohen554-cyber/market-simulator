"""Carbon pricing and emissions policy."""

from __future__ import annotations

from market_sim.config.constants import CARBON_PRICE_PATHS
from market_sim.config.scenarios import ScenarioConfig


def resolve_carbon_price(config: ScenarioConfig, year: int) -> float:
    """Resolve the carbon price for a given year.

    If ``config.carbon_price`` is nonzero, return it directly (flat
    trajectory). If ``config.carbon_price`` is 0 and
    ``config.gas_price_path`` names a carbon path in
    :data:`CARBON_PRICE_PATHS`, interpolate from that path: the trajectory
    is defined at a few knot years, intermediate years are linearly
    interpolated, and years outside the knot range take the nearest
    endpoint value. Otherwise return ``0.0``.

    Args:
        config: Scenario config supplying the flat carbon price and the
            gas/carbon path name.
        year: Simulation year.

    Returns:
        The carbon price in $/tCO2.
    """
    if config.carbon_price != 0:
        return float(config.carbon_price)

    path = CARBON_PRICE_PATHS.get(config.gas_price_path)
    if path is None:
        return 0.0

    knots = sorted(path)
    if year <= knots[0]:
        return float(path[knots[0]])
    if year >= knots[-1]:
        return float(path[knots[-1]])

    for lo, hi in zip(knots, knots[1:]):
        if lo <= year <= hi:
            frac = (year - lo) / (hi - lo)
            return float(path[lo] + frac * (path[hi] - path[lo]))
    return float(path[knots[-1]])
