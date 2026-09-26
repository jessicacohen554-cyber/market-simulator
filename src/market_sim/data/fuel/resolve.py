"""Top-level delivered fuel-price resolution (:func:`resolve_fuel_prices`).

The orchestrator of the fuel package: annual trajectories -> measured monthly
overlays -> daily shapes -> the per-ISO zonal gas-basis appliers -> dual-fuel
oil parity. Split out of ``data/fuel.py`` (W-D3; refactor-consolidation plan
§5 item 3) as pure code motion, apart from one documented conversion: the five
sequential per-ISO ``apply_<iso>_zonal_gas_basis`` calls became a consumption
of the :data:`market_sim.data.fuel.basis.ZONAL_BASIS_APPLIERS` registry in
:data:`~market_sim.data.fuel.basis.ZONAL_BASIS_ORDER`. Behaviour is identical:
every applier self-gates on ``config.iso`` (at most one fires per run) and the
MISO winter-citygate overlay still runs before the MISO zonal basis — the only
ordering constraint among them, since all intervening appliers are other-ISO
no-ops. The registry is read through the package namespace at call time
(:func:`._shared._pkg_ns`), so replacing an entry on the facade intercepts the
dispatch exactly as patching the old module-global function name did.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.constants import (
    BIOMASS_PRICE_PER_MMBTU,
    COAL_PRICE_BASE,
    COAL_PRICE_ESCALATION,
    OIL_PRICE_PER_MMBTU,
    START_YEAR,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays
from market_sim.data.hydrogen import compute_h2_fuel_cost

from ._shared import (
    _BIOMASS_FUEL_IDX,
    _COAL_FUEL_IDX,
    _GAS_FUEL_IDX,
    _HYDROGEN_FUEL_IDX,
    _NUCLEAR_FUEL_IDX,
    _OIL_FUEL_IDX,
    _expand_monthly_to_hourly,
    _pkg_ns,
)
from .basis import (
    ZONAL_BASIS_ORDER,
    apply_miso_gas_marginal_commodity,
    apply_miso_winter_citygate_daily,
)
from .dual_fuel import apply_dual_fuel_pricing
from .hubs import apply_hub_basis_overlay, gas_daily_shape_factors
from .plant_prices import apply_plant_monthly_fuel_prices
from .trajectories import (
    gas_seasonal_shape,
    resolve_annual_coal_price,
    resolve_annual_gas_price,
    resolve_annual_oil_price,
    resolve_nuclear_fuel_price,
)


def resolve_fuel_prices(
    config: ScenarioConfig,
    fleet: FleetArrays,
    year: int,
    apply_monthly: bool = True,
) -> np.ndarray:
    """Return the ``(n_gen, T)`` delivered fuel price array for the fleet.

    Pricing model:

      1. **Gas** units pay the AEO Henry Hub trajectory plus the ISO basis
         differential (:func:`resolve_annual_gas_price`), optionally shaped
         by the monthly seasonality factors when ``config.gas_seasonality``
         is set — the *same* price for every gas unit in the ISO that year.
         Per-plant EIA-923 monthly gas costs are applied only when
         ``config.gas_plant_monthly_fuel_pricing`` is set (off by default).
      2. **Coal** units pay :data:`COAL_PRICE_BASE` escalated to ``year``:
         in forecast mode via the AEO2025 real-growth ratio
         (:func:`resolve_annual_coal_price`); in backcast mode via the flat
         :data:`COAL_PRICE_ESCALATION` rate (unchanged), then (historical
         years, ``coal_plant_monthly_pricing`` on) overwritten by each
         plant's own measured EIA-923 monthly delivered cost where reported.
         Months with no reported cost keep the trajectory.

    Hydrogen turbines (``hydrogen_ct``, ``hydrogen_ccgt``) pay the
    derived hydrogen fuel cost from
    :func:`market_sim.data.hydrogen.compute_h2_fuel_cost`. Oil units
    (``oil``) pay the AEO2025 oil-price trajectory in forecast mode
    (:func:`resolve_annual_oil_price`) or the flat delivered price
    (:data:`~market_sim.config.constants.OIL_PRICE_PER_MMBTU`) in backcast
    mode. Biomass units (``biomass``) pay the flat delivered biomass fuel cost
    (:data:`~market_sim.config.constants.BIOMASS_PRICE_PER_MMBTU`) in BOTH
    modes -- held flat because EIA/AEO publishes no forward biomass price (NEMS
    models biomass via supply curves, verified against the AEO2026 API; see
    docs/handoffs/biomass-fuel-price-audit-2026-07.md). Nuclear
    units (``nuclear``) pay the EIA-uranium-marketing-derived fuel-cycle cost
    (:func:`resolve_nuclear_fuel_price`) in both modes. All other generators
    (wind, solar, hydro, imports) carry a zero fuel price.

    When ``config.dual_fuel_switching`` is set (and ``apply_monthly`` is
    True), EIA-860 oil/gas switch-capable gas units are finally capped at
    the delivered oil price per hour (:func:`apply_dual_fuel_pricing`), so
    their marginal cost is ``min(gas_mc, oil_mc)``.

    The same code path runs both backcasts and forward projections. The
    F923 plant-monthly overlay (:func:`apply_plant_monthly_fuel_prices`)
    is mode-gated to backcast (plus the capacity hindcast — see the
    overlay's docstring): a forecast-mode run keeps the trajectory-based
    default for every plant even when the F923 parquet carries measured
    rows for the solve year, which it does now that H1-2026 receipts are
    intaken (rule 22 / spec §1.7; G11 / W2-E).

    Args:
        config: Scenario configuration supplying ``iso``, ``gas_price_path``,
            ``gas_seasonality`` and ``hours``.
        fleet: Vectorized fleet attributes; ``fuel_type_idx`` selects each
            generator's fuel and ``plant_code`` keys the F923 lookup.
        year: Calendar year for which to resolve prices.

    Returns:
        A ``(n_gen, T)`` array of delivered fuel prices ($/MMBtu), where
        ``T`` is ``config.hours``.
    """
    T = config.hours
    delivered_annual = resolve_annual_gas_price(config, year)
    if config.gas_seasonality:
        gas_price_hourly = delivered_annual * gas_seasonal_shape(config, year, T)
    else:
        gas_price_hourly = np.full(T, delivered_annual)
    # Backcast: measured ISO-month delivered gas (EIA-923 volume-weighted)
    # replaces the trajectory + generic seasonal shape month-by-month, so
    # real winter events (PJM Jan-2024 at $5+/MMBtu) reach the merit order.
    # Months with no receipts keep the shaped trajectory value.
    if getattr(config, "gas_monthly_actuals", False):
        measured = _pkg_ns().iso_monthly_gas_prices(config, year)
        if measured is not None:
            hourly_measured = _expand_monthly_to_hourly(
                np.asarray(measured, dtype=float), T
            )
            gas_price_hourly = np.where(
                np.isnan(hourly_measured), gas_price_hourly, hourly_measured
            )

    # Measured monthly delivered LEVEL (EIA N3045 state series, blended by
    # this ISO's gas-capacity footprint). REPLACES the level set above — the
    # annual trajectory x generic shape, or the EIA-923 ISO-month receipts —
    # never stacks on it (rule 19 [R-ONE-MECH]); the measured constrained-hub
    # index below still supersedes it in the months it covers, since a hub
    # index is the marginal unit's own opportunity cost while this is an
    # average delivered cost across the state. Inert (byte-identical) when the
    # flag is off or the year is inadmissible. See
    # market_sim.data.fuel.electric_power.
    if getattr(config, "gas_electric_power_monthly_level", False):
        ep_level = _pkg_ns().iso_electric_power_monthly_level(config.iso, year)
        if ep_level is not None:
            gas_price_hourly = _expand_monthly_to_hourly(
                np.asarray(ep_level, dtype=float), T
            )

    # Daily Henry Hub within-month shape: the monthly level above is correct
    # (trajectory / measured ISO-month), and this multiplies in the real
    # day-to-day commodity swing the marginal gas unit's bid would track,
    # mean-preserving per month so the annual gas burn is unchanged. This is
    # the gas price the gas units actually bid at, so it is shaped here (the
    # coal-sigmoid reference in _gas_series is shaped identically).
    if getattr(config, "gas_daily_shape", False):
        gas_price_hourly = gas_price_hourly * gas_daily_shape_factors(year, T)

    if config.mode == "forecast":
        # Forecast years track the AEO2025 national coal-price REAL GROWTH
        # applied to the ISO's own delivered-cost anchor (resolve_annual_coal_price)
        # rather than the flat, uncited COAL_PRICE_ESCALATION rate.
        coal_price = resolve_annual_coal_price(config, year)
    else:
        # Backcast: unchanged flat-escalation fallback (superseded within the
        # backcast window by the EIA-923 monthly overwrite pass below for any
        # plant/month with reported delivered cost).
        coal_price = COAL_PRICE_BASE[config.iso] * (1.0 + COAL_PRICE_ESCALATION) ** (
            year - START_YEAR
        )

    fuel_type_idx = fleet.fuel_type_idx
    fuel_prices = np.zeros((fleet.n_gen, T), dtype=float)
    fuel_prices[np.isin(fuel_type_idx, _GAS_FUEL_IDX)] = gas_price_hourly
    fuel_prices[fuel_type_idx == _COAL_FUEL_IDX] = coal_price

    # Oil (distillate/residual) and biomass burn at a flat delivered cost in
    # backcast (oil sits far above gas — peaker economics — and any measured
    # EIA-923 receipts take precedence via the dual-fuel pass below); forecast
    # years use the AEO2025 delivered-oil trajectory. Biomass has no commodity
    # trajectory or F923 plant-monthly override at all -- EIA/AEO publishes no
    # forward biomass price (NEMS uses biomass supply curves), so it is held
    # flat like nuclear fuel (docs/handoffs/biomass-fuel-price-audit-2026-07.md).
    oil_price = (
        resolve_annual_oil_price(config, year)
        if config.mode == "forecast"
        else OIL_PRICE_PER_MMBTU
    )
    fuel_prices[fuel_type_idx == _OIL_FUEL_IDX] = oil_price
    fuel_prices[fuel_type_idx == _BIOMASS_FUEL_IDX] = BIOMASS_PRICE_PER_MMBTU

    # Nuclear burns a real, priced fuel (EIA-uranium-marketing-derived
    # fuel-cycle cost) in both backcast and forecast — not the non-fuel-burning
    # $0 default (D2 fix).
    fuel_prices[fuel_type_idx == _NUCLEAR_FUEL_IDX] = resolve_nuclear_fuel_price(
        config, year
    )

    # Hydrogen turbines burn green H2 whose cost is derived from renewable
    # LCOE and electrolyzer efficiency rather than a commodity market.
    if np.any(np.isin(fuel_type_idx, _HYDROGEN_FUEL_IDX)):
        h2_price = compute_h2_fuel_cost(year, config, config.iso)
        fuel_prices[np.isin(fuel_type_idx, _HYDROGEN_FUEL_IDX)] = h2_price

    # Callers that set a coal-supply base (lignite/PRB) before the monthly
    # overwrite pass apply_monthly=False and call
    # apply_plant_monthly_fuel_prices themselves afterwards, so the actual
    # EIA-923 monthly cost takes precedence over the supply-class base —
    # then the hub-basis overlay (the measured constrained-hub spot
    # supersedes plant receipts in covered months), and finally the
    # dual-fuel min, which must see the final gas price so oil parity caps
    # the blown-out winter hub price.
    if apply_monthly:
        # The overlay returns the mask of cells it WROTE (own print or nearby
        # pool). The MISO applier below consumes it under
        # ``miso_zonal_gas_basis_skip_923_priced`` (miso-213, rule 19): a
        # print-derived cell already carries the regional delivered premium,
        # so the zonal increment is not layered on top of it.
        print_cells = apply_plant_monthly_fuel_prices(fuel_prices, fleet, config, year)
        apply_hub_basis_overlay(fuel_prices, fleet, config, year)
        # MISO winter fuel security: in Dec/Jan/Feb, swap the national HH
        # gas_daily_shape for the measured Chicago Citygate daily shape on the
        # Chicago-hub zones' gas units (miso-72). BEFORE the MISO zonal basis so
        # it acts on level×national_shape (the additive zonal spread lands
        # un-shaped) and BEFORE dual-fuel so oil parity still caps any winter
        # blowout. (Moved ahead of the registry walk in the W-D3 split: every
        # applier between its old position and the MISO zonal basis is an
        # other-ISO no-op for a MISO run, so the mutation sequence is identical.)
        # miso-224: gas at MARGINAL commodity (measured daily hub spot per zone)
        # instead of the EIA-923 AVERAGE delivered print. Off by default and
        # byte-identical off. When armed it supersedes (rule 19, never stacks):
        # the winter Chicago SHAPE overlay below (the daily series already
        # carries level AND shape) and the mean-zero zonal increment (the
        # written mask joins the print-derived mask the MISO applier skips).
        spot_cells = apply_miso_gas_marginal_commodity(fuel_prices, fleet, config, year)
        if spot_cells is None:
            apply_miso_winter_citygate_daily(fuel_prices, fleet, config, year)
        else:
            print_cells = (
                spot_cells if print_cells is None else (print_cells | spot_cells)
            )
        # Per-ISO zonal gas basis: walk the ZONAL_BASIS_APPLIERS registry in
        # ZONAL_BASIS_ORDER. Each applier self-gates on config.iso + its own
        # config flag, so at most one fires per run and the walk reproduces the
        # pre-split call sequence byte-for-byte (see basis/__init__.py). All
        # appliers run before dual-fuel so oil parity still caps any winter
        # blowout. Read through the package namespace so replacing an entry on
        # the facade intercepts the dispatch (pre-split patch semantics).
        appliers = _pkg_ns().ZONAL_BASIS_APPLIERS
        # Only the MISO applier takes the print-derived-cell mask, and only
        # the flag makes it consume it (rule 25: the mechanism is MISO's; the
        # other appliers' signatures are untouched and the walk is unchanged
        # for every other ISO and for a flag-off MISO run).
        skip_for_miso = (
            print_cells
            if config.iso == "MISO"
            and (
                getattr(config, "miso_zonal_gas_basis_skip_923_priced", False)
                or spot_cells is not None
            )
            else None
        )
        # PJM-NEXT-2: PJM's own twin of the miso-213 scope, consumed only under
        # its own flag (rule 25: no MISO verdict transfers; flag off => None).
        skip_for_pjm = (
            print_cells
            if config.iso == "PJM"
            and getattr(config, "pjm_zonal_gas_basis_skip_923_priced", False)
            else None
        )
        for iso_name in ZONAL_BASIS_ORDER:
            if iso_name == "MISO" and skip_for_miso is not None:
                appliers[iso_name](
                    fuel_prices, fleet, config, year, skip_cells=skip_for_miso
                )
            elif iso_name == "PJM" and skip_for_pjm is not None:
                appliers[iso_name](
                    fuel_prices, fleet, config, year, skip_cells=skip_for_pjm
                )
            else:
                appliers[iso_name](fuel_prices, fleet, config, year)
        apply_dual_fuel_pricing(fuel_prices, fleet, config, year)

    return fuel_prices
