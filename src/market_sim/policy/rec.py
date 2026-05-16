"""Exogenous Renewable Energy Credit (REC) prices by resource type.

These RECs are Tier 1 scenario parameters representing policy- or
market-set clean-energy payments: state Zero Emission Credits for
nuclear, tradable RECs for wind and solar, 45Q-style credits for
CCS-equipped gas, and emerging storage-discharge incentives.

They are *exogenous* values fixed by the scenario, distinct from the
*endogenous* REC price recovered as the dual of the RPS LP constraint
in dispatch. The two stack: a generator can earn both the exogenous
REC set here and the endogenous RPS shadow price, and these also stack
with IRA credits. Setting every ``rec_price_*`` to ``0.0`` (the
default) leaves all behavior unchanged.

RECs only shift the dispatch cost vector and the capacity-economics
revenue terms; they add no LP constraint rows.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays

# Fuel type -> ScenarioConfig field carrying its exogenous REC price.
_REC_PRICE_FIELDS: dict[str, str] = {
    "nuclear": "rec_price_nuclear",
    "gas_cc": "rec_price_gas_cc",
    "wind": "rec_price_wind",
    "solar": "rec_price_solar",
    "storage": "rec_price_storage",
}


def apply_rec_to_mc(
    mc: np.ndarray, fleet: FleetArrays, config: ScenarioConfig
) -> np.ndarray:
    """Subtract thermal-resource RECs from the dispatch marginal cost.

    Nuclear generators have ``rec_price_nuclear`` subtracted from their
    marginal cost and ``gas_cc`` generators have ``rec_price_gas_cc``
    subtracted -- a REC makes the resource willing to bid lower, exactly
    as a production credit would. ``mc`` is modified in place and also
    returned. Wind and solar RECs are handled separately via
    ``compute_rec_dispatch_credits`` because they ride the per-zone
    ``wind_mc`` / ``solar_mc`` adders, not the per-generator ``mc``.

    Args:
        mc: Marginal cost array of shape ``(n_gen, T)``.
        fleet: Vectorized fleet arrays supplying ``fuel_type_idx``.
        config: Scenario config supplying the exogenous REC prices.

    Returns:
        The same ``mc`` array, modified in place.
    """
    fuel_idx = np.asarray(fleet.fuel_type_idx)
    nuclear = fuel_idx == FUEL_TYPE_MAP["nuclear"]
    gas_cc = fuel_idx == FUEL_TYPE_MAP["gas_cc"]
    mc[nuclear] -= config.rec_price_nuclear
    mc[gas_cc] -= config.rec_price_gas_cc
    return mc


def compute_rec_dispatch_credits(
    config: ScenarioConfig,
) -> tuple[float, float, float]:
    """Return the ``(wind, solar, storage)`` exogenous REC prices in $/MWh.

    These feed the dispatch as adders to ``wind_mc`` / ``solar_mc`` and as
    the storage discharge credit, separate from the per-generator ``mc``.
    """
    return (
        config.rec_price_wind,
        config.rec_price_solar,
        config.rec_price_storage,
    )


def compute_rec_revenue_per_mw(
    fuel_type: str,
    generation_mwh: float,
    pmax_mw: float,
    config: ScenarioConfig,
) -> float:
    """Return a generator's annual exogenous REC revenue in dollars.

    The REC price for ``fuel_type`` is multiplied by its annual
    generation. Used to credit economic-retirement revenue so that, for
    example, a nuclear plant earning a Zero Emission Credit is not
    retired when energy prices alone fail to cover fixed O&M.

    Args:
        fuel_type: Generator fuel type, e.g. ``"nuclear"`` or ``"gas_cc"``.
        generation_mwh: Annual generation in MWh.
        pmax_mw: Generator nameplate capacity in MW (unused; kept so the
            signature can carry per-MW REC variants in the future).
        config: Scenario config supplying the exogenous REC prices.

    Returns:
        Annual REC revenue in dollars; ``0.0`` for fuel types with no REC.
    """
    field = _REC_PRICE_FIELDS.get(fuel_type)
    if field is None:
        return 0.0
    return getattr(config, field) * generation_mwh


def get_rec_price_for_new_entry(tech: str, config: ScenarioConfig) -> float:
    """Return the exogenous REC price in $/MWh for a new-entry technology.

    Maps a candidate technology (``"wind"``, ``"solar"`` or ``"gas_cc"``)
    to its matching ``rec_price_*`` field. Used to raise the expected
    revenue of new builds; stacks with the endogenous RPS shadow price.

    Args:
        tech: Candidate technology name.
        config: Scenario config supplying the exogenous REC prices.

    Returns:
        The REC price in $/MWh; ``0.0`` for technologies with no REC.
    """
    field = _REC_PRICE_FIELDS.get(tech)
    if field is None:
        return 0.0
    return getattr(config, field)
