"""Capacity expansion and retirement modeling.

Part 1: fleet retirements. Three mechanisms remove generators between
simulation years:

* **Known retirements** -- units with a scheduled ``retirement_year`` are
  dropped once the simulation reaches that year.
* **Economic retirements** -- thermal units whose energy revenue fails to
  cover their going-forward fixed cost for several consecutive years are
  retired, least efficient first within each fuel class.
* **Sigmoid retirements** -- a clean-energy-share-driven attrition curve
  retires a fraction of the fossil fleet, accelerating as clean share
  crosses the configured midpoint.
"""

from __future__ import annotations

import math

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays, Generator
from market_sim.model.dispatch import DispatchResult

# Fuel classes treated as dispatchable thermal capacity for economic
# retirement, mapped to their ScenarioConfig fixed-O&M field ($/kW-yr).
_THERMAL_FOM: dict[str, str] = {
    "gas_cc": "fixed_om_gas_cc",
    "gas_ct": "fixed_om_gas_ct",
    "coal": "fixed_om_coal",
}

# Fuel classes that count toward the clean-energy share.
_CLEAN_FUELS: frozenset[str] = frozenset({"wind", "solar", "nuclear", "hydro"})

# Order in which fossil fuel classes face sigmoid-driven attrition.
_SIGMOID_ORDER: tuple[str, ...] = ("coal", "gas_ct", "gas_cc")


def apply_known_retirements(fleet: list[Generator], year: int) -> list[Generator]:
    """Return the fleet with scheduled retirements removed.

    A generator retires once the simulation year reaches its
    ``retirement_year``; units with no scheduled year are always kept.

    Args:
        fleet: The current generator fleet.
        year: The simulation year being evaluated.

    Returns:
        A new list excluding generators whose ``retirement_year`` is set
        and not later than ``year``.
    """
    return [
        g for g in fleet
        if g.retirement_year is None or g.retirement_year > year
    ]


def compute_clean_share(fleet: list[Generator]) -> float:
    """Return the clean-capacity fraction of the fleet.

    Clean capacity is the summed ``pmax_mw`` of wind, solar, nuclear and
    hydro units, divided by the total fleet ``pmax_mw``. An empty fleet
    (zero total capacity) yields ``0.0``.
    """
    total = sum(g.pmax_mw for g in fleet)
    if total <= 0.0:
        return 0.0
    clean = sum(g.pmax_mw for g in fleet if g.fuel_type in _CLEAN_FUELS)
    return clean / total


def apply_economic_retirements(
    fleet: list[Generator],
    fleet_arrays: FleetArrays,
    dispatch_result: DispatchResult,
    prices: np.ndarray,
    config: ScenarioConfig,
    consecutive_loss_years: dict[str, int],
) -> tuple[list[Generator], dict[str, int]]:
    """Retire thermal units that persistently fail to cover fixed cost.

    For each thermal generator the annual energy revenue is compared with
    its going-forward fixed cost::

        net_revenue        = sum_t price[zone, t] * dispatch[g, t]
        going_forward_cost = fixed_om_per_kw_yr * pmax_mw * 1000

    A year in which ``net_revenue < going_forward_cost`` increments the
    unit's consecutive-loss counter; a profitable year resets it to zero.
    Once the counter reaches ``config.retirement_consecutive_years`` the
    unit retires. When multiple units in the same fuel class retire, the
    highest heat-rate (least efficient) units go first.

    Args:
        fleet: The current generator fleet.
        fleet_arrays: Vectorized fleet aligned with ``dispatch_result``;
            supplies each generator's row index and zone index.
        dispatch_result: Solved dispatch whose ``dispatch`` array is
            ``(n_gen, T)`` thermal generation in MW.
        prices: Zonal energy prices of shape ``(n_zones, T)`` in $/MWh.
        config: Scenario config supplying fixed-O&M rates and the
            consecutive-loss threshold.
        consecutive_loss_years: Per-unit loss counters keyed by
            ``unit_id``; not mutated in place.

    Returns:
        Tuple ``(survivors, loss_years)`` -- the fleet with retired units
        removed, and the updated loss-counter dict (retired units dropped).
    """
    prices = np.asarray(prices, dtype=float)
    dispatch = np.asarray(dispatch_result.dispatch, dtype=float)
    idx_of = {uid: i for i, uid in enumerate(fleet_arrays.unit_ids)}
    loss_years = dict(consecutive_loss_years)

    eligible: list[Generator] = []
    for g in fleet:
        fom_field = _THERMAL_FOM.get(g.fuel_type)
        if fom_field is None:
            continue
        i = idx_of.get(g.unit_id)
        if i is None:
            continue

        zone = int(fleet_arrays.zone_idx[i])
        net_revenue = float(np.dot(prices[zone], dispatch[i]))
        going_forward_cost = getattr(config, fom_field) * g.pmax_mw * 1000.0

        if net_revenue < going_forward_cost:
            loss_years[g.unit_id] = loss_years.get(g.unit_id, 0) + 1
        else:
            loss_years[g.unit_id] = 0

        if loss_years[g.unit_id] >= config.retirement_consecutive_years:
            eligible.append(g)

    # Within each fuel class, retire the least efficient units first.
    eligible.sort(key=lambda g: (g.fuel_type, -g.heat_rate))
    retired = {g.unit_id for g in eligible}

    survivors = [g for g in fleet if g.unit_id not in retired]
    for uid in retired:
        loss_years.pop(uid, None)
    return survivors, loss_years


def apply_sigmoid_retirement(
    fleet: list[Generator],
    clean_share: float,
    config: ScenarioConfig,
) -> list[Generator]:
    """Retire a sigmoid-weighted fraction of the fossil fleet.

    The retirement fraction follows a logistic curve in clean share::

        fraction = 1 / (1 + exp(-steepness * (clean_share - midpoint)))

    That fraction of capacity is removed from each fossil class in turn --
    coal, then ``gas_ct``, then ``gas_cc`` -- retiring the least efficient
    (highest heat-rate) units first until the retired capacity reaches the
    class target.

    Args:
        fleet: The current generator fleet.
        clean_share: Clean-capacity fraction driving the logistic curve.
        config: Scenario config supplying ``sigmoid_steepness`` and
            ``sigmoid_midpoint``.

    Returns:
        A new list with the sigmoid-retired fossil units removed.
    """
    fraction = 1.0 / (
        1.0
        + math.exp(
            -config.sigmoid_steepness * (clean_share - config.sigmoid_midpoint)
        )
    )

    survivors = list(fleet)
    for fuel in _SIGMOID_ORDER:
        class_units = [g for g in survivors if g.fuel_type == fuel]
        class_capacity = sum(g.pmax_mw for g in class_units)
        if class_capacity <= 0.0:
            continue

        target = fraction * class_capacity
        # Least efficient first: highest heat rate retires soonest.
        ordered = sorted(class_units, key=lambda g: g.heat_rate, reverse=True)

        retired: set[str] = set()
        removed = 0.0
        for g in ordered:
            if removed >= target:
                break
            retired.add(g.unit_id)
            removed += g.pmax_mw

        survivors = [g for g in survivors if g.unit_id not in retired]

    return survivors
