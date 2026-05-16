"""Fuel price and carbon price resolution.

Resolves per-generator delivered fuel prices ($/MMBtu) and the scenario
carbon and NOx prices into the forms consumed by marginal-cost assembly
(see :func:`market_sim.data.fleet.assemble_mc`).
"""

from __future__ import annotations

import numpy as np

from market_sim.config.constants import (
    COAL_PRICE_BASE,
    GAS_PRICE_BASE,
    GAS_PRICE_ESCALATION,
    START_YEAR,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays

# Fuel-type integer codes (from FUEL_TYPE_MAP) that burn natural gas and
# therefore pay the escalated gas price.
_GAS_FUEL_IDX: tuple[int, int] = (FUEL_TYPE_MAP["gas_cc"], FUEL_TYPE_MAP["gas_ct"])

# Fuel-type integer code for coal-fired units, which pay the coal price.
_COAL_FUEL_IDX: int = FUEL_TYPE_MAP["coal"]

# Fuel price ($/MMBtu) for non-fuel-burning units (e.g. wind, solar, nuclear,
# hydro, imports), which carry no commodity fuel cost in this model.
_ZERO_FUEL_PRICE: float = 0.0


def resolve_fuel_prices(
    config: ScenarioConfig, fleet: FleetArrays, year: int
) -> np.ndarray:
    """Return the ``(n_gen, T)`` delivered fuel price array for the fleet.

    Natural-gas units (``gas_cc`` and ``gas_ct``) pay a gas price taken from
    :data:`GAS_PRICE_BASE` for the scenario's ISO and gas price path, escalated
    at :data:`GAS_PRICE_ESCALATION` per year from :data:`START_YEAR`::

        price = base * (1 + GAS_PRICE_ESCALATION) ** (year - START_YEAR)

    Coal units pay the flat :data:`COAL_PRICE_BASE` price for the ISO. All
    other generators carry a zero fuel price. Generator types are identified
    via ``fleet.fuel_type_idx``.

    Args:
        config: Scenario configuration supplying ``iso``, ``gas_price_path``
            and ``hours``.
        fleet: Vectorized fleet attributes; ``fuel_type_idx`` selects each
            generator's fuel.
        year: Calendar year for which to resolve prices, used for gas
            escalation.

    Returns:
        A ``(n_gen, T)`` array of delivered fuel prices ($/MMBtu), where
        ``T`` is ``config.hours``, broadcastable for marginal-cost assembly.
    """
    gas_base = GAS_PRICE_BASE[config.iso][config.gas_price_path]
    gas_price = gas_base * (1.0 + GAS_PRICE_ESCALATION) ** (year - START_YEAR)
    coal_price = COAL_PRICE_BASE[config.iso]

    fuel_type_idx = fleet.fuel_type_idx
    per_gen_price = np.full(fleet.n_gen, _ZERO_FUEL_PRICE, dtype=float)
    per_gen_price[np.isin(fuel_type_idx, _GAS_FUEL_IDX)] = gas_price
    per_gen_price[fuel_type_idx == _COAL_FUEL_IDX] = coal_price

    return np.broadcast_to(
        per_gen_price[:, np.newaxis], (fleet.n_gen, config.hours)
    ).copy()


def resolve_carbon_price(config: ScenarioConfig, year: int) -> float:
    """Return the carbon price ($/tCO2) for the given scenario and year.

    The carbon price is currently a flat scalar carried on the config; the
    ``year`` argument is accepted so callers can later resolve a year-varying
    trajectory without changing the signature.

    Args:
        config: Scenario configuration supplying ``carbon_price``.
        year: Calendar year for which to resolve the price.

    Returns:
        The carbon price in $/tCO2.
    """
    return config.carbon_price


def resolve_nox_price(config: ScenarioConfig) -> float:
    """Return the NOx price ($/ton NOx) for the given scenario.

    Args:
        config: Scenario configuration supplying ``nox_price``.

    Returns:
        The NOx price in $/ton NOx.
    """
    return config.nox_price
