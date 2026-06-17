"""Forecast-grade neighbor reference prices for the interchange seam.

This is step (1) of the reference-price interface (model-methodology-spec
§8.3): a pure, ISO-agnostic construction of each neighboring balancing
authority's hourly energy price, plus the ISO↔neighbor spread that drives
seam flow. No LP is touched here — the module is a self-contained data layer
that can be validated against the measured net-interchange *before* it is
wired into dispatch (see :mod:`scripts.validate_neighbor_price`).

The fitted ``IMPORT_TRANCHES`` / ``EXPORT_TRANCHES`` it is meant to replace
price each seam block at a constant tuned to the ISO's net-interchange
duration curve. That is a backcast fit — re-fitted per year, blind to
neighbor fundamentals. Here the neighbor's price is built from forward
drivers instead:

    neighbor_price[h] = (henry_hub[year] + gas_basis) x marginal_heat_rate
                        x load_shape(neighbor_load[h])

* ``henry_hub[year]`` and ``gas_basis`` give the neighbor's *delivered* gas
  price — the same Henry Hub trajectory the ISO's own gas burn prices off,
  shifted by the neighbor hub's basis.
* ``marginal_heat_rate`` (~7.5 MMBtu/MWh) is the neighbor's price-setting
  gas unit; gas x HR is the baseload marginal energy cost.
* ``load_shape`` is the neighbor's own normalized hourly load raised to a
  convexity exponent (default 1.0 = mean-preserving, parameter-free), so the
  price rises in the neighbor's tight hours and falls in its slack hours
  exactly as climbing/descending its offer stack would.

Every term is a forecast input or a physically-pinned constant; nothing is
tuned to the net-MWh target. The seam then clears on the spread against the
ISO's own price, with a hurdle dead-band and the real interface limit:

    import when ISO_price > neighbor_price + hurdle
    export when ISO_price < neighbor_price - hurdle
    |flow| <= interface_limit_mw

Each neighbor in :data:`~market_sim.config.constants.INTERFACE_NEIGHBORS`
prices individually when its EIA-930 load extract (or a proxy) is present;
neighbors with neither fold into a capacity-weighted aggregate. So the seam
is neighbor-resolved where the data supports it and gracefully aggregate
where it does not — add a neighbor's extract later and it lights up
individually with no code change.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from market_sim.config.constants import (
    HENRY_HUB_TRAJECTORIES,
    INTERFACE_NEIGHBORS,
    NeighborInterface,
)
from market_sim.data.eia_loader import _eia_hourly_frame_filled


def neighbor_gas_price(
    neighbor: NeighborInterface, year: int, gas_scenario: str = "mid"
) -> float:
    """Return the neighbor's delivered gas price ($/MMBtu) for ``year``.

    Henry Hub annual average for ``year`` (from
    :data:`~market_sim.config.constants.HENRY_HUB_TRAJECTORIES`, which carries
    the historical values for backcast years identically across scenarios)
    shifted by the neighbor hub's basis. Mirrors the ISO's own gas pricing so
    a neighbor and its bordering ISO see the same Henry Hub level.

    Args:
        neighbor: The seam specification.
        year: Calendar year.
        gas_scenario: Henry Hub trajectory key (``"low"``/``"mid"``/``"high"``);
            backcast years are identical across keys.

    Returns:
        Delivered gas price in $/MMBtu.

    Raises:
        KeyError: if ``gas_scenario`` or ``year`` is not in the trajectory.
    """
    henry_hub = HENRY_HUB_TRAJECTORIES[gas_scenario][year]
    return henry_hub + neighbor.gas_basis


def neighbor_load_shape(
    neighbor: NeighborInterface, year: int, hours: int
) -> tuple[np.ndarray, str] | None:
    """Return the neighbor's normalized hourly load shape and the BA used.

    The shape is ``(load[h] / mean(load)) ** load_shape_exponent`` — a
    dimensionless multiplier whose mean is 1.0 at the default exponent 1.0, so
    multiplying the baseload gas-times-heat-rate price by it preserves the
    annual-average price while tracking the neighbor's hourly tightness. The
    load series is the EIA-930 ``Demand`` column for ``neighbor.ba_code``;
    when that extract is absent the ``proxy_ba`` series stands in (the seam
    still prices individually, just on a one-step-removed load shape).

    Args:
        neighbor: The seam specification.
        year: Calendar year.
        hours: Expected length of the series (the model's 8760 clock).

    Returns:
        ``(shape, ba_used)`` where ``shape`` is the ``(hours,)`` multiplier
        and ``ba_used`` is the BA code whose load produced it (the primary or
        the proxy), or ``None`` when neither extract yields a usable series.
    """
    for ba in (neighbor.ba_code, neighbor.proxy_ba):
        if ba is None:
            continue
        frame = _eia_hourly_frame_filled(ba, year)
        if frame is None or "Demand" not in frame.columns:
            continue
        load = (
            frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
        )
        if load.shape[0] != hours or np.isnan(load).any():
            continue
        mean_load = float(load.mean())
        if mean_load <= 0.0:
            continue
        shape = (load / mean_load) ** neighbor.load_shape_exponent
        return shape, ba
    return None


def neighbor_reference_price(
    neighbor: NeighborInterface,
    year: int,
    hours: int,
    gas_scenario: str = "mid",
) -> tuple[np.ndarray, str] | None:
    """Return the neighbor's hourly reference price ($/MWh) and the BA used.

    ``gas x heat_rate x load_shape`` — the forecast-native construction
    described in the module docstring. Returns ``None`` (no individual price)
    when the neighbor has no resolvable load shape, leaving it to fold into
    the aggregate.

    Args:
        neighbor: The seam specification.
        year: Calendar year.
        hours: Length of the hourly series.
        gas_scenario: Henry Hub trajectory key.

    Returns:
        ``(price, ba_used)`` or ``None``.
    """
    shaped = neighbor_load_shape(neighbor, year, hours)
    if shaped is None:
        return None
    shape, ba_used = shaped
    baseload = neighbor_gas_price(neighbor, year, gas_scenario)
    baseload *= neighbor.marginal_heat_rate
    return baseload * shape, ba_used


@dataclass
class InterfacePrices:
    """Resolved per-neighbor reference prices for one ISO-year seam.

    Attributes:
        iso: ISO identifier.
        year: Calendar year.
        hours: Length of each price series.
        per_neighbor: ``name -> (hours,) $/MWh`` for every neighbor that
            resolved an individual price (own extract or proxy).
        ba_used: ``name -> BA code`` the price shape was built from.
        missing: Neighbor names that resolved no load shape at all (folded
            into the aggregate).
    """

    iso: str
    year: int
    hours: int
    per_neighbor: dict[str, np.ndarray] = field(default_factory=dict)
    ba_used: dict[str, str] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)

    def aggregate(self) -> np.ndarray | None:
        """Return the interface-capacity-weighted blend of neighbor prices.

        A single ``(hours,)`` price for the seam as one external node — the
        representation the current single-bubble topology uses and the
        fallback for any neighbor without an individual price. Each resolved
        neighbor is weighted by its ``interface_limit_mw`` (its share of the
        seam's transfer capability). Returns ``None`` when no neighbor
        resolved a price.
        """
        if not self.per_neighbor:
            return None
        specs = {n.name: n for n in INTERFACE_NEIGHBORS.get(self.iso, [])}
        total = np.zeros(self.hours, dtype=float)
        weight_sum = 0.0
        for name, price in self.per_neighbor.items():
            w = specs[name].interface_limit_mw if name in specs else 1.0
            total += w * price
            weight_sum += w
        return total / weight_sum if weight_sum > 0.0 else None


def interface_reference_prices(
    iso: str, year: int, hours: int, gas_scenario: str = "mid"
) -> InterfacePrices:
    """Return the reference price for every neighbor of ``iso`` in ``year``.

    Iterates :data:`~market_sim.config.constants.INTERFACE_NEIGHBORS` for the
    ISO, building each neighbor's individual price where its load shape
    resolves and recording the rest as ``missing``. An ISO absent from the
    registry yields an empty result (byte-identical no-op for un-onboarded
    ISOs).

    Args:
        iso: ISO identifier, e.g. ``"PJM"``.
        year: Calendar year.
        hours: Length of the hourly series (the model's 8760 clock).
        gas_scenario: Henry Hub trajectory key.

    Returns:
        An :class:`InterfacePrices` aggregating the per-neighbor results.
    """
    result = InterfacePrices(iso=iso, year=year, hours=hours)
    for neighbor in INTERFACE_NEIGHBORS.get(iso, []):
        priced = neighbor_reference_price(neighbor, year, hours, gas_scenario)
        if priced is None:
            result.missing.append(neighbor.name)
            continue
        price, ba_used = priced
        result.per_neighbor[neighbor.name] = price
        result.ba_used[neighbor.name] = ba_used
    return result


def seam_flow_direction(
    iso_price: np.ndarray,
    neighbor_price: np.ndarray,
    hurdle: float,
) -> np.ndarray:
    """Return the seam's flow direction per hour from the price spread.

    The hurdle dead-band rule: the ISO imports (+1, draws from the neighbor)
    when its own price exceeds the neighbor price by more than ``hurdle``,
    exports (-1, sells to the neighbor) when its price is below the neighbor
    by more than ``hurdle``, and holds (0) inside the band. The sign matches
    :func:`market_sim.data.eia_loader._eia930_net_interchange` (export
    positive) once negated — exports are sales, so a -1 here is a positive net
    export. Pure, vectorized, no LP.

    Args:
        iso_price: ``(hours,)`` ISO internal price ($/MWh).
        neighbor_price: ``(hours,)`` neighbor reference price ($/MWh).
        hurdle: $/MWh dead-band half-width.

    Returns:
        ``(hours,)`` array of -1 (export), 0 (hold), +1 (import).
    """
    spread = iso_price - neighbor_price
    direction = np.zeros_like(spread)
    direction[spread > hurdle] = 1.0
    direction[spread < -hurdle] = -1.0
    return direction
