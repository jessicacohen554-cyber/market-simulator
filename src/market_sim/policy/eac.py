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

The national CES federal EAC premium (``policy/federal_ces.py``, W2-A)
layers onto the same channels: when ``federal_ces_enabled`` the two
dispatch entry points below become year-aware and consume the effective
price ``max(legacy eac_price_*, premium × credit fraction)`` per unit /
per tech — still one certificate per MWh, sold once, and still no LP
rows. Disabled (the default), every path here is byte-identical legacy.
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
    mc: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int | None = None,
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

    Under the federal CES (``config.federal_ces_enabled``, W2-A plan
    §5.3) the subtraction becomes the year-aware effective price
    ``max(legacy eac_price_*, premium × credit fraction)`` per unit
    (:func:`market_sim.policy.federal_ces.effective_unit_eac_prices`) —
    one certificate per MWh, sold once, never a sum — which extends the
    credited set to every eligible fleet fuel (hydro, hydrogen turbines,
    and under ``cesa_ci`` the unabated gas CCs at or under the CI
    eligibility line). Hydro is monthly-budget constrained, so its lower
    bid is dispatch-inert (plan §5.3); the CES-disabled path below is
    byte-identical to the legacy behavior.

    Args:
        mc: Marginal cost array of shape ``(n_gen, T)``.
        fleet: Vectorized fleet arrays supplying ``fuel_type_idx`` (and,
            for cesa_ci crediting, ``emission_rate``).
        config: Scenario config supplying the exogenous EAC prices.
        year: Simulation year for the federal CES premium path. Required
            when ``federal_ces_enabled``; legacy (CES-off) callers may
            omit it.

    Returns:
        The same ``mc`` array, modified in place.
    """
    if config.federal_ces_enabled:
        # Local import: policy.federal_ces imports from this module, so
        # the reverse edge must stay function-local (same pattern as the
        # runner's negative-offer-floor import).
        from market_sim.policy.federal_ces import effective_unit_eac_prices

        effective = effective_unit_eac_prices(config, fleet, year)
        mc -= effective[:, None]
        return mc

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
    year: int | None = None,
) -> tuple[float, float, float]:
    """Return the ``(wind, solar, storage)`` exogenous EAC prices in $/MWh.

    These feed the dispatch as adders to ``wind_mc`` / ``solar_mc`` and as
    the storage discharge credit, separate from the per-generator ``mc``.
    Offshore wind and geothermal are not in this tuple -- they enter the
    fleet as generators and take their EAC via ``apply_eac_to_mc``.

    Under the federal CES (``config.federal_ces_enabled``, W2-A plan
    §5.3) each element becomes ``max(legacy eac_price_*, premium × credit
    fraction)`` for the year — wind/solar credit at 1.0 (when eligible)
    and storage only under ``federal_ces_storage_eligible`` (owner D5
    default: off — discharge creates no new attribute). The CES-disabled
    path is byte-identical to the legacy behavior.

    Args:
        config: Scenario config supplying the exogenous EAC prices.
        year: Simulation year for the federal CES premium path. Required
            when ``federal_ces_enabled``; legacy (CES-off) callers may
            omit it.
    """
    if config.federal_ces_enabled:
        # Local import: policy.federal_ces imports from this module (see
        # apply_eac_to_mc).
        from market_sim.policy.federal_ces import (
            premium_for_year,
            tech_credit_fraction,
        )

        premium = premium_for_year(config, year)
        return (
            max(config.eac_price_wind, premium * tech_credit_fraction(config, "wind")),
            max(
                config.eac_price_solar, premium * tech_credit_fraction(config, "solar")
            ),
            max(
                config.eac_price_storage,
                premium * tech_credit_fraction(config, "storage"),
            ),
        )
    return (
        config.eac_price_wind,
        config.eac_price_solar,
        config.eac_price_storage,
    )


def apply_negative_renewable_offer_floor(
    wind_mc: np.ndarray | float,
    solar_mc: np.ndarray | float,
    config: ScenarioConfig,
) -> tuple[np.ndarray | float, np.ndarray | float]:
    """Floor the wind/solar dispatch offers at the negative keep-running value.

    When ``config.negative_renewable_offers`` is on, each renewable's dispatch
    offer is driven to at most ``-config.renewable_keep_running_value`` $/MWh —
    the REC / PTC value a renewable on a PPA forgoes if curtailed, so it bids
    below $0 to keep producing. In the oversupply (long) hours where the
    marginal resource is curtailed wind/solar, the energy-balance dual then
    clears negative, reproducing CAISO's negative midday LMPs; the existing $0
    export/curtailment sink still floors any surplus that can be exported, so
    the negative price only appears once that sink is exhausted (true forced
    curtailment).

    The floor is the MORE-negative of the existing offer and the keep-running
    value (an element-wise ``min``), so a wind offer already carrying the
    federal PTC (e.g. ``-26``) is left untouched — no double-count — while
    solar, whose dispatch offer is ``$0`` (it earns the ITC, not the PTC), is
    carried negative by the REC value.

    When the flag is off this is an exact identity (byte-identical baseline).

    Args:
        wind_mc: Wind dispatch offer in $/MWh; scalar or ``(n_zones, T)``.
        solar_mc: Solar dispatch offer in $/MWh; scalar or ``(n_zones, T)``.
        config: Scenario config supplying the flag and the keep-running value.

    Returns:
        The ``(wind_mc, solar_mc)`` offers after applying the floor.
    """
    if not config.negative_renewable_offers:
        return wind_mc, solar_mc
    floor = -config.renewable_keep_running_value
    return np.minimum(wind_mc, floor), np.minimum(solar_mc, floor)


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
