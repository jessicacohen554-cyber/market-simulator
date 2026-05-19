"""Fuel price and NOx price resolution.

Resolves per-generator delivered fuel prices ($/MMBtu) and the scenario
NOx price into the forms consumed by marginal-cost assembly
(see :func:`market_sim.data.fleet.assemble_mc`). Carbon-price resolution
lives in :mod:`market_sim.policy.carbon`.

Gas prices follow EIA Annual Energy Outlook Henry Hub trajectories
(:data:`HENRY_HUB_TRAJECTORIES`) selected by ``config.gas_price_path``,
plus a regional basis differential (:data:`GAS_BASIS_DIFFERENTIAL`) and an
optional monthly seasonality shape (:data:`GAS_MONTHLY_SEASONALITY`).
"""

from __future__ import annotations

import numpy as np

from market_sim.config.constants import (
    COAL_PRICE_BASE,
    COAL_PRICE_ESCALATION,
    END_YEAR,
    GAS_BASIS_DIFFERENTIAL,
    GAS_MONTHLY_SEASONALITY,
    HENRY_HUB_TRAJECTORIES,
    HOURS_PER_YEAR,
    INFLATION_RATE,
    START_YEAR,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.data.hydrogen import compute_h2_fuel_cost

# Fuel-type integer codes (from FUEL_TYPE_MAP) that burn natural gas and
# therefore pay the Henry Hub price. CCUS (``gas_cc_ccs``) burns the same
# natural gas as an unabated gas CC; ``gas_st`` is legacy gas steam.
_GAS_FUEL_IDX: tuple[int, ...] = (
    FUEL_TYPE_MAP["gas_cc"],
    FUEL_TYPE_MAP["gas_ct"],
    FUEL_TYPE_MAP["gas_cc_ccs"],
    FUEL_TYPE_MAP["gas_st"],
)

# Fuel-type integer code for coal-fired units, which pay the coal price.
_COAL_FUEL_IDX: int = FUEL_TYPE_MAP["coal"]

# Fuel-type integer codes for hydrogen turbines, whose fuel price is the
# derived hydrogen fuel cost (see :mod:`market_sim.data.hydrogen`).
_HYDROGEN_FUEL_IDX: tuple[int, int] = (
    FUEL_TYPE_MAP["hydrogen_ct"],
    FUEL_TYPE_MAP["hydrogen_ccgt"],
)

# Fuel price ($/MMBtu) for non-fuel-burning units (e.g. wind, solar, nuclear,
# hydro, imports), which carry no commodity fuel cost in this model.
_ZERO_FUEL_PRICE: float = 0.0

# Calendar days per month for a non-leap year (sums to 365 -> 8760 hours).
_DAYS_IN_MONTH: tuple[int, ...] = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def resolve_annual_gas_price(config: ScenarioConfig, year: int) -> float:
    """Return the delivered annual gas price ($/MMBtu) for the scenario year.

    The price is the AEO Henry Hub trajectory value for ``year`` and the
    scenario's ``gas_price_path``, plus the ISO's basis differential::

        delivered = HENRY_HUB_TRAJECTORIES[path][year] + basis

    Years beyond the trajectory's last entry are extrapolated using the
    final year-over-year growth rate. This annual (seasonality-free) price
    is the one capacity new-entry LCOE screening should charge gas units,
    so dispatch and capacity evolution see the same gas cost for a year.

    When ``config.gas_price_override`` is set the trajectory lookup is
    bypassed entirely: the override is treated as the measured Henry Hub
    price and the ISO basis differential is added to it, so a calibration
    backcast charges the year's actual delivered gas cost.

    Args:
        config: Scenario configuration supplying ``iso``,
            ``gas_price_path`` and an optional ``gas_price_override``.
        year: Calendar year to resolve.

    Returns:
        The delivered annual gas price in $/MMBtu.
    """
    basis = GAS_BASIS_DIFFERENTIAL.get(config.iso, 0.0)
    if config.gas_price_override is not None:
        return config.gas_price_override + basis

    trajectory = HENRY_HUB_TRAJECTORIES[config.gas_price_path]
    if year in trajectory:
        henry_hub = trajectory[year]
    else:
        # Extrapolate beyond the trajectory using the last growth rate.
        last_year = max(trajectory)
        annual_growth = trajectory[last_year] / trajectory[last_year - 1]
        henry_hub = trajectory[last_year] * annual_growth ** (year - last_year)

    return henry_hub + basis


def _seasonal_factors(hours: int) -> np.ndarray:
    """Return an ``(hours,)`` array of monthly gas seasonality multipliers.

    The 8760-hour year is filled month by month from
    :data:`GAS_MONTHLY_SEASONALITY`; a sub-annual horizon takes the leading
    slice. The 12-iteration loop is over months, not hours.
    """
    full_year = np.empty(HOURS_PER_YEAR)
    hour = 0
    for month in range(1, 13):
        hours_in_month = _DAYS_IN_MONTH[month - 1] * 24
        full_year[hour:hour + hours_in_month] = GAS_MONTHLY_SEASONALITY[month]
        hour += hours_in_month
    if hours <= HOURS_PER_YEAR:
        return full_year[:hours]
    # Multi-year horizons repeat the annual shape.
    reps = -(-hours // HOURS_PER_YEAR)
    return np.tile(full_year, reps)[:hours]


def resolve_fuel_prices(
    config: ScenarioConfig, fleet: FleetArrays, year: int
) -> np.ndarray:
    """Return the ``(n_gen, T)`` delivered fuel price array for the fleet.

    Natural-gas units (``gas_cc``, ``gas_ct`` and ``gas_cc_ccs``) pay the
    delivered Henry Hub price for the year (see
    :func:`resolve_annual_gas_price`), optionally shaped by the monthly
    seasonality factors :data:`GAS_MONTHLY_SEASONALITY` when
    ``config.gas_seasonality`` is set.

    Coal units pay the ISO's :data:`COAL_PRICE_BASE` price escalated from
    :data:`START_YEAR` at :data:`COAL_PRICE_ESCALATION` per year.
    Hydrogen turbines (``hydrogen_ct``, ``hydrogen_ccgt``) pay the derived
    hydrogen fuel cost from :func:`market_sim.data.hydrogen.compute_h2_fuel_cost`.
    All other generators carry a zero fuel price. Generator types are
    identified via ``fleet.fuel_type_idx``.

    Args:
        config: Scenario configuration supplying ``iso``, ``gas_price_path``,
            ``gas_seasonality`` and ``hours``.
        fleet: Vectorized fleet attributes; ``fuel_type_idx`` selects each
            generator's fuel.
        year: Calendar year for which to resolve prices.

    Returns:
        A ``(n_gen, T)`` array of delivered fuel prices ($/MMBtu), where
        ``T`` is ``config.hours``.
    """
    T = config.hours
    delivered_annual = resolve_annual_gas_price(config, year)
    if config.gas_seasonality:
        gas_price_hourly = delivered_annual * _seasonal_factors(T)
    else:
        gas_price_hourly = np.full(T, delivered_annual)

    coal_price = COAL_PRICE_BASE[config.iso] * (
        1.0 + COAL_PRICE_ESCALATION
    ) ** (year - START_YEAR)

    fuel_type_idx = fleet.fuel_type_idx
    fuel_prices = np.zeros((fleet.n_gen, T), dtype=float)
    fuel_prices[np.isin(fuel_type_idx, _GAS_FUEL_IDX)] = gas_price_hourly
    fuel_prices[fuel_type_idx == _COAL_FUEL_IDX] = coal_price

    # Hydrogen turbines burn green H2 whose cost is derived from renewable
    # LCOE and electrolyzer efficiency rather than a commodity market.
    if np.any(np.isin(fuel_type_idx, _HYDROGEN_FUEL_IDX)):
        h2_price = compute_h2_fuel_cost(year, config, config.iso)
        fuel_prices[np.isin(fuel_type_idx, _HYDROGEN_FUEL_IDX)] = h2_price

    return fuel_prices


# --- CAMPD coal delivered fuel cost ($/MMBtu), by year and supply type ------
# Mine-mouth lignite: $1.45 flat across 2023-2025, then escalates at general
# inflation through the modeling window. PRB-by-rail: measured delivered cost
# for 2023-2025; from 2026 a forward curve decomposes the 2023-2025 average
# into commodity (42%), diesel-driven rail freight (12%) and non-diesel rail
# freight (46%). The commodity component holds flat through 2030 then declines
# 1.5%/yr as coal demand falls; non-diesel rail escalates at inflation; the
# diesel-rail component is held at its 2025 level (the model carries no
# forward diesel price curve). Source: operator/EIA cost data, user calibration.
_LIGNITE_PRICE_2023_25: float = 1.45
_PRB_PRICE_CALIBRATION: dict[int, float] = {2023: 2.15, 2024: 2.00, 2025: 2.00}
_PRB_COMMODITY_SHARE: float = 0.42
_PRB_RAIL_DIESEL_SHARE: float = 0.12
_PRB_RAIL_NONDIESEL_SHARE: float = 0.46
_PRB_COMMODITY_DECLINE: float = 0.015      # annual, from 2031 as demand falls
_PRB_COMMODITY_FLAT_THROUGH: int = 2030


def _build_coal_price_trajectories() -> tuple[dict[int, float], dict[int, float]]:
    """Return ``(lignite, prb)`` delivered-cost dicts spanning 2023-END_YEAR."""
    lignite: dict[int, float] = {}
    prb: dict[int, float] = {}
    for y in (2023, 2024, 2025):
        lignite[y] = _LIGNITE_PRICE_2023_25
        prb[y] = _PRB_PRICE_CALIBRATION[y]

    avg_prb = sum(_PRB_PRICE_CALIBRATION.values()) / 3.0
    commodity_base = _PRB_COMMODITY_SHARE * avg_prb
    rail_diesel = _PRB_RAIL_DIESEL_SHARE * avg_prb        # held flat forward
    rail_nondiesel_base = _PRB_RAIL_NONDIESEL_SHARE * avg_prb
    for y in range(2026, END_YEAR + 1):
        lignite[y] = (
            _LIGNITE_PRICE_2023_25 * (1.0 + INFLATION_RATE) ** (y - 2025)
        )
        if y <= _PRB_COMMODITY_FLAT_THROUGH:
            commodity = commodity_base
        else:
            commodity = commodity_base * (1.0 - _PRB_COMMODITY_DECLINE) ** (
                y - _PRB_COMMODITY_FLAT_THROUGH
            )
        rail_nondiesel = (
            rail_nondiesel_base * (1.0 + INFLATION_RATE) ** (y - 2026)
        )
        prb[y] = commodity + rail_diesel + rail_nondiesel
    return lignite, prb


COAL_PRICE_LIGNITE_BY_YEAR, COAL_PRICE_PRB_BY_YEAR = (
    _build_coal_price_trajectories()
)


def apply_coal_supply_pricing(
    fuel_prices: np.ndarray,
    generators: list,
    config: ScenarioConfig,
    year: int,
) -> None:
    """Reprice CAMPD coal generators by their plant fuel-supply type.

    Mine-mouth lignite and PRB-by-rail generators bid at their per-year
    delivered fuel cost — :data:`COAL_PRICE_LIGNITE_BY_YEAR` and
    :data:`COAL_PRICE_PRB_BY_YEAR`. The PRB delivered cost is scaled by
    ``coal_prb_contract_passthrough``: take-or-pay rail/coal contracts
    leave much of the delivered tonnage sunk, so the marginal dispatch bid
    sits below delivered cost. Coal generators with no ``coal_supply`` tag
    (the legacy fleet, or an unmapped plant), or a run year outside the
    coal price trajectory, keep the generic price already in
    ``fuel_prices``.

    Mutates ``fuel_prices`` in place.

    Args:
        fuel_prices: The ``(n_gen, T)`` delivered fuel-price array to update,
            aligned row-for-row with ``generators``.
        generators: The dispatch fleet.
        config: Scenario configuration supplying ``coal_prb_contract_passthrough``.
        year: Calendar year, selecting the coal price trajectory entry.
    """
    lignite = COAL_PRICE_LIGNITE_BY_YEAR.get(year)
    prb_delivered = COAL_PRICE_PRB_BY_YEAR.get(year)
    if lignite is None or prb_delivered is None:
        return  # year outside the coal trajectory — keep the generic price

    price_by_supply = {
        "lignite": lignite,
        "prb": prb_delivered * config.coal_prb_contract_passthrough,
    }
    for g_idx, gen in enumerate(generators):
        price = price_by_supply.get(getattr(gen, "coal_supply", ""))
        if price is not None:
            fuel_prices[g_idx, :] = price


def resolve_nox_price(config: ScenarioConfig) -> float:
    """Return the NOx price ($/ton NOx) for the given scenario.

    Args:
        config: Scenario configuration supplying ``nox_price``.

    Returns:
        The NOx price in $/ton NOx.
    """
    return config.nox_price
