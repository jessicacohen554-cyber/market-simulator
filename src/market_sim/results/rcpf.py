"""NYISO RCPF scarcity-pricing overlay (post-solve reserve-demand-curve adder).

NYISO prices real-time scarcity through its Reserve Constraint Penalty
Factors (RCPF), not an ERCOT-style ORDC/LOLP curve (``results.scarcity``).
When dispatchable headroom drops below an operating-reserve requirement,
NYISO's stepped reserve demand curve sets the reserve clearing price, and
through energy/reserve co-optimization that shadow price flows into the
LBMP. The reserve products are *nested* — 10-minute spinning is a subset of
10-minute total, which is a subset of 30-minute total — so in a deepening
shortage the penalties STACK into the energy price. That stacking is how
NYISO RT LMP reaches the high hundreds / low thousands ($1,147/MWh max in
2023) off a ~$2,000/MWh energy offer cap, a tail a perfect-foresight energy
LP cannot produce (its duals carry no reserve-shortage rent).

This overlay is a *post-solve* price adder, exactly like the ERCOT ORDC
overlay: the LP is untouched (volumes, dispatch, emissions identical with
the overlay on or off), and the adder is computed from the solved hourly
reserve headroom and written next to the energy-only LMP. It owns the price
TAIL only — it is zero whenever reserves clear the requirement, which is
the vast majority of hours, so it lifts the scarcity tail without touching
the body of the price distribution.

Model mapping (documented approximations):

* Reserves R = dispatchable thermal available capacity (incl. the outage
  overlay/derates) minus thermal dispatch, plus storage headroom (power cap
  - discharge + charge). Curtailed renewables do NOT count (unlike ERCOT's
  telemetry convention) — NYISO operating reserves come from dispatchable
  resources and responsive load, not wind/solar headroom.
* Every product sees the same system reserve R. The model has no per-unit
  ramp-rate / on-line state, so it cannot split 10-minute-capable from
  30-minute-capable headroom; treating all dispatchable headroom as
  eligible to every product is conservative (it over-states 10-minute
  capability) and only matters in already-critical hours. The nesting is
  carried by the requirements: a shortfall deep enough to breach the
  10-minute requirement is, by construction, also short of the 30-minute
  requirement, so the curves stack.
* The reserve demand curve for each product is linearised between its
  published anchors (requirement MW -> $0, critical MW -> max penalty): a
  piecewise-linear stand-in for the published stepped curve. The anchors
  trace to the NYISO tariff (see constants.NYISO_RCPF_PRODUCTS); nothing is
  fitted to LMP residuals.

The system-wide products, requirements and penalty maxima are
``constants.NYISO_RCPF_PRODUCTS`` (overridable per ScenarioConfig); the
system-wide adder (:func:`rcpf_adder`) matches the NYCA-hub RT price.

NYISO's reserve market is also LOCATIONAL: nested reserve regions (East ⊃
SENY ⊃ NYC, all nested in NYCA) each carry their own requirement and demand
curve over the resources physically inside the region, so a downstate
shortage stacks region penalties into the *zonal* LBMP even when the system
is long on reserves. :func:`locational_zone_adders` evaluates those regional
curves on per-model-zone reserve headroom (``constants.NYISO_RCPF_LOCATIONAL``)
and returns a per-zone adder that the overlay stacks onto each zone's price
on top of the system-wide NYCA tier. This is how the model reproduces the
measured upstate→NYC reserve-price cascade and the downstate scarcity tail
the NYCA-aggregate energy LP cannot see.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.reserve_config import (
    NEISO_RCPF_PRODUCTS,
    NYISO_RCPF_LOCATIONAL,
    NYISO_RCPF_PRODUCTS,
)


def reserve_demand_price(
    reserves_mw: np.ndarray,
    requirement_mw: float,
    critical_mw: float,
    max_penalty: float,
) -> np.ndarray:
    """Reserve demand-curve price ($/MWh) for one product at each hour.

    Piecewise-linear NYISO reserve demand curve:

        price = 0                                          if R >= requirement
              = max_penalty * (requirement - R)
                            / (requirement - critical)     if critical < R < requirement
              = max_penalty                                if R <= critical

    Args:
        reserves_mw: Hourly reserve headroom available to the product (MW).
        requirement_mw: Reserve requirement (MW); the curve is $0 at/above it.
        critical_mw: Reserve level (MW) at/below which the maximum penalty
            applies. Must be < ``requirement_mw``.
        max_penalty: Maximum reserve shadow price ($/MWh).

    Returns:
        ``(T,)`` array of demand-curve prices in $/MWh, >= 0.
    """
    r = np.asarray(reserves_mw, dtype=float)
    span = requirement_mw - critical_mw
    if span <= 0:
        raise ValueError(
            f"requirement_mw ({requirement_mw}) must exceed critical_mw ({critical_mw})"
        )
    frac = np.clip((requirement_mw - r) / span, 0.0, 1.0)
    return frac * max_penalty


def resolve_rcpf_products(
    config,
) -> tuple[tuple[str, float, float, float], ...]:
    """Return the RCPF product table for a config (override or default).

    ISO-aware: NEISO uses the ISO-NE reserve products
    (``constants.NEISO_RCPF_PRODUCTS``, overridable via ``neiso_rcpf_products``);
    every other ISO uses the NYISO table (the original behaviour). Both default
    tables follow the same nested-product, piecewise-linear convention.
    """
    if getattr(config, "iso", None) == "NEISO":
        products = getattr(config, "neiso_rcpf_products", None)
        return tuple(products) if products else NEISO_RCPF_PRODUCTS
    products = getattr(config, "nyiso_rcpf_products", None)
    return tuple(products) if products else NYISO_RCPF_PRODUCTS


def rcpf_adder(
    reserves_mw: np.ndarray,
    config=None,
    products: "tuple[tuple[str, float, float, float], ...] | None" = None,
) -> np.ndarray:
    """Hourly NYISO RCPF energy adder ($/MWh) from solved reserve headroom.

    The adder is the sum of the reserve demand-curve prices of the nested
    operating-reserve products (constants.NYISO_RCPF_PRODUCTS, or a config
    / explicit override). Every product sees the same system reserve R; the
    nesting that makes the penalties stack is carried by the requirements.

    Args:
        reserves_mw: Hourly system reserve headroom (MW).
        config: Optional ScenarioConfig (supplies ``nyiso_rcpf_products``).
        products: Optional explicit product table, overriding both.

    Returns:
        ``(T,)`` adder array in $/MWh, >= 0.
    """
    if products is None:
        products = (
            resolve_rcpf_products(config) if config is not None else NYISO_RCPF_PRODUCTS
        )
    r = np.asarray(reserves_mw, dtype=float)
    adder = np.zeros_like(r)
    for _name, requirement, critical, max_penalty in products:
        adder = adder + reserve_demand_price(r, requirement, critical, max_penalty)
    return adder


def rcpf_product_prices(
    reserves_mw: np.ndarray,
    config=None,
    products: "tuple[tuple[str, float, float, float], ...] | None" = None,
) -> dict[str, np.ndarray]:
    """Per-product reserve demand-curve prices, keyed by product name.

    The summed series (the energy adder) is under key ``"adder"``. Useful
    for the overlay report (which product is driving a scarcity hour).
    """
    if products is None:
        products = (
            resolve_rcpf_products(config) if config is not None else NYISO_RCPF_PRODUCTS
        )
    r = np.asarray(reserves_mw, dtype=float)
    out: dict[str, np.ndarray] = {}
    total = np.zeros_like(r)
    for name, requirement, critical, max_penalty in products:
        p = reserve_demand_price(r, requirement, critical, max_penalty)
        out[name] = p
        total = total + p
    out["adder"] = total
    return out


def resolve_rcpf_locational(config) -> dict:
    """Return the locational reserve-region table for a config (override or default)."""
    regions = getattr(config, "nyiso_rcpf_locational", None)
    return regions if regions else NYISO_RCPF_LOCATIONAL


def locational_zone_adders(
    zone_reserves: "dict[str, np.ndarray]",
    config=None,
    regions: "dict | None" = None,
) -> dict[str, np.ndarray]:
    """Per-model-zone locational RCPF adder ($/MWh) from per-zone headroom.

    NYISO's nested reserve regions (East ⊃ SENY ⊃ NYC, all nested in NYCA)
    each carry a reserve requirement and demand curve over the resources
    *physically located inside the region*. A model zone's locational adder
    is the sum of the demand-curve prices of every region that contains the
    zone, each evaluated on that region's reserve headroom (the sum of its
    member zones' headroom). This reproduces the measured per-zone reserve
    cascade (constants.NYISO_RCPF_LOCATIONAL): upstate zones carry no
    locational adder, the downstate pocket stacks East + SENY + NYC.

    The system-wide NYCA tier (``NYISO_RCPF_PRODUCTS`` / ``rcpf_adder``) is
    NOT included here — it is added to every zone separately, on top of these
    locational adders, by the overlay.

    Args:
        zone_reserves: ``{model_zone_name: (T,) reserve headroom MW}``. A
            zone absent from the mapping contributes 0 MW to any region it
            belongs to (and receives a 0 adder if it appears in no region).
        config: Optional ScenarioConfig (supplies ``nyiso_rcpf_locational``).
        regions: Optional explicit region table, overriding both.

    Returns:
        ``{model_zone_name: (T,) adder}`` for every zone in ``zone_reserves``,
        in $/MWh, >= 0.
    """
    if regions is None:
        regions = (
            resolve_rcpf_locational(config)
            if config is not None
            else NYISO_RCPF_LOCATIONAL
        )
    zr = {z: np.asarray(r, dtype=float) for z, r in zone_reserves.items()}
    shape = next(iter(zr.values())).shape if zr else (0,)
    adders = {z: np.zeros(shape) for z in zr}
    for region in regions.values():
        products = tuple(region.get("products", ()))
        members = [z for z in region["zones"] if z in zr]
        if not products or not members:
            continue
        region_reserve = sum(zr[z] for z in members)
        region_adder = rcpf_adder(region_reserve, products=products)
        for z in members:
            adders[z] = adders[z] + region_adder
    return adders
