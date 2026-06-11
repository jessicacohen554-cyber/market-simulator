"""Carbon pricing and emissions policy."""

from __future__ import annotations

from market_sim.config.constants import (
    CARBON_PRICE_PATHS,
    STATE_CARBON_PRICE_BY_ISO,
)
from market_sim.config.scenarios import ScenarioConfig


def state_carbon_price(config: ScenarioConfig, year: int) -> float | None:
    """Return the ISO's state carbon-program allowance price, or ``None``.

    Looks up :data:`STATE_CARBON_PRICE_BY_ISO` — the CA cap-and-trade
    (CARB) quarterly-auction settlement average for CAISO, and the RGGI
    quarterly-auction clearing-price average for NYISO and NEISO (all six
    New England states are RGGI members), 2023-2025 — so a backcast
    charges every in-state fossil unit the measured allowance cost without
    any per-scenario configuration. Returns ``None`` (caller falls through
    to the scenario carbon path) when ``config.state_carbon_pricing`` is
    off, the ISO has no registered program, or the year is outside the
    measured series (forward years need an allowance-price *trajectory*,
    which is deliberately not seeded here).

    Args:
        config: Scenario config supplying ``iso`` and the
            ``state_carbon_pricing`` toggle.
        year: Simulation year.

    Returns:
        The allowance price in $/tCO2, or ``None`` when not applicable.
    """
    if not getattr(config, "state_carbon_pricing", True):
        return None
    program = STATE_CARBON_PRICE_BY_ISO.get(config.iso)
    if program is None or year not in program:
        return None
    return float(program[year])


def resolve_carbon_price(config: ScenarioConfig, year: int) -> float:
    """Resolve the carbon price for a given year.

    If ``config.carbon_price`` is nonzero, return it directly (flat
    trajectory). If ``config.carbon_price`` is 0, the ISO's state
    carbon program is checked next (:func:`state_carbon_price` — CA
    cap-and-trade for CAISO backcast years). Otherwise, if
    ``config.carbon_price_path`` names a carbon path in
    :data:`CARBON_PRICE_PATHS`, interpolate from that path: the trajectory
    is defined at a few knot years, intermediate years are linearly
    interpolated, and years outside the knot range take the nearest
    endpoint value. Otherwise return ``0.0``.

    Args:
        config: Scenario config supplying the flat carbon price and the
            carbon path name.
        year: Simulation year.

    Returns:
        The carbon price in $/tCO2.
    """
    if config.carbon_price != 0:
        return float(config.carbon_price)

    state_price = state_carbon_price(config, year)
    if state_price is not None:
        return state_price

    path = CARBON_PRICE_PATHS.get(config.carbon_price_path)
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
