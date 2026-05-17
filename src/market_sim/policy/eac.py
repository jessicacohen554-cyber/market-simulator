"""Exogenous Environmental Attribute Credit (EAC) prices by resource type.

EAC is the umbrella term for the policy- or market-set clean-energy
payments a generator earns per MWh, distinct from the energy price. It
covers RECs for wind and solar, Zero Emission Credits (ZECs) for
nuclear, clean-energy credits for CCS-equipped gas (45Q-linked),
offshore-wind ORECs, clean-firm credits for geothermal, and emerging
storage-discharge incentives.

These prices are Tier 1 scenario parameters and are *exogenous* values
fixed by the scenario, distinct from the *endogenous* RPS shadow price
recovered as the dual of the RPS LP constraint in dispatch. The two do
NOT stack: each MWh of clean generation produces one attribute
certificate, sold once to whichever buyer clears higher. In dispatch,
the exogenous EAC reduces marginal cost (real bidding behavior); in
capacity evolution, attribute revenue uses ``max(eac, rps_shadow)``.
Setting every ``eac_price_*`` to ``0.0`` (the default) leaves all
behavior unchanged.

EACs only shift the dispatch cost vector and the capacity-economics
revenue terms; they add no LP constraint rows.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays

# Fuel type -> ScenarioConfig field carrying its exogenous EAC price.
_EAC_PRICE_FIELDS: dict[str, str] = {
    "nuclear": "eac_price_nuclear",
    "wind": "eac_price_wind",
    "solar": "eac_price_solar",
    "storage": "eac_price_storage",
    "gas_cc_ccs": "eac_price_gas_cc_ccs",
    "offshore_wind": "eac_price_offshore_wind",
    "geothermal": "eac_price_geothermal",
}


def apply_eac_to_mc(
    mc: np.ndarray, fleet: FleetArrays, config: ScenarioConfig
) -> np.ndarray:
    """Subtract per-generator EACs from the dispatch marginal cost.

    Nuclear, CCS-equipped gas (``gas_cc_ccs``), geothermal and offshore
    wind generators have their exogenous EAC subtracted from marginal
    cost -- an EAC makes the resource willing to bid lower, exactly as a
    production credit would. ``mc`` is modified in place and also
    returned. Offshore wind already has MC=0, so its EAC drives MC
    negative, meaning the LP dispatches it even at negative energy
    prices (down to ``-eac_price_offshore_wind``), same as onshore wind
    under a PTC. Onshore wind and solar EACs are handled separately via
    ``compute_eac_dispatch_credits`` because they ride the per-zone
    ``wind_mc`` / ``solar_mc`` adders, not the per-generator ``mc``.

    Args:
        mc: Marginal cost array of shape ``(n_gen, T)``.
        fleet: Vectorized fleet arrays supplying ``fuel_type_idx``.
        config: Scenario config supplying the exogenous EAC prices.

    Returns:
        The same ``mc`` array, modified in place.
    """
    fuel_idx = np.asarray(fleet.fuel_type_idx)
    if config.eac_price_nuclear > 0.0:
        nuclear = fuel_idx == FUEL_TYPE_MAP["nuclear"]
        mc[nuclear] -= config.eac_price_nuclear
    if config.eac_price_gas_cc_ccs > 0.0:
        ccs_mask = fuel_idx == FUEL_TYPE_MAP["gas_cc_ccs"]
        mc[ccs_mask] -= config.eac_price_gas_cc_ccs
    if config.eac_price_geothermal > 0.0:
        geo_mask = fuel_idx == FUEL_TYPE_MAP["geothermal"]
        mc[geo_mask] -= config.eac_price_geothermal
    if config.eac_price_offshore_wind > 0.0:
        ow_mask = fuel_idx == FUEL_TYPE_MAP["offshore_wind"]
        mc[ow_mask] -= config.eac_price_offshore_wind
    return mc


def compute_eac_dispatch_credits(
    config: ScenarioConfig,
) -> tuple[float, float, float]:
    """Return the ``(wind, solar, storage)`` exogenous EAC prices in $/MWh.

    These feed the dispatch as adders to ``wind_mc`` / ``solar_mc`` and as
    the storage discharge credit, separate from the per-generator ``mc``.
    Offshore wind and geothermal are not in this tuple -- they enter the
    fleet as generators and take their EAC via ``apply_eac_to_mc``.
    """
    return (
        config.eac_price_wind,
        config.eac_price_solar,
        config.eac_price_storage,
    )


def get_eac_price_for_new_entry(tech: str, config: ScenarioConfig) -> float:
    """Return the exogenous EAC price in $/MWh for a resource type.

    Maps a fuel type or candidate technology to its matching
    ``eac_price_*`` field. Used to raise the expected revenue of new
    builds and to credit economic-retirement revenue; the caller takes
    ``max()`` of this and the endogenous RPS shadow price (the two do
    not stack).

    Args:
        tech: Fuel type or candidate technology name.
        config: Scenario config supplying the exogenous EAC prices.

    Returns:
        The EAC price in $/MWh; ``0.0`` for resources with no EAC.
    """
    field = _EAC_PRICE_FIELDS.get(tech)
    if field is None:
        return 0.0
    return getattr(config, field)
