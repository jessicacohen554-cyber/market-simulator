"""Inflation Reduction Act policy incentives."""

from market_sim.config.scenarios import ScenarioConfig


def compute_dispatch_credits(config: ScenarioConfig, year: int) -> tuple[float, float]:
    """Return (wind_mc, solar_mc) dispatch cost adders in $/MWh.

    Wind PTC: -config.ira_ptc_wind $/MWh (negative = willing to pay to generate).
    Solar ITC: does not affect dispatch marginal cost (capital cost reduction only).
    Credits expire after config.ira_expiry_year.

    Returns:
        Tuple of (wind_mc, solar_mc). wind_mc is negative when PTC active, 0 otherwise.
        solar_mc is always 0 (ITC is a capital credit, not a production credit).
    """
    if year > config.ira_expiry_year:
        return 0.0, 0.0
    wind_mc = -config.ira_ptc_wind  # PTC makes wind willing to bid negative
    solar_mc = 0.0  # ITC reduces capex, doesn't affect dispatch MC
    return wind_mc, solar_mc


def apply_ira_credits_to_lcoe(
    tech_type: str, lcoe: float, year: int, config: ScenarioConfig
) -> float:
    """Reduce a technology's LCOE by the IRA wind production tax credit.

    The wind PTC is a production credit that lowers effective levelized
    cost by a flat $/MWh amount, so it is correctly applied post-hoc to a
    finished LCOE. The solar and storage ITC is a capital credit and is
    *not* handled here: applying it to a finished LCOE would wrongly
    discount the fixed-O&M component too, so it is instead applied to
    capex inside :func:`market_sim.model.capacity.compute_lcoe` and
    :func:`market_sim.model.storage.compute_storage_annual_cost`. The PTC
    phases out after ``config.ira_expiry_year``.

    Args:
        tech_type: Candidate technology, e.g. ``"wind"``, ``"solar"`` or
            ``"gas_cc"``.
        lcoe: Pre-credit levelized cost of energy in $/MWh.
        year: Simulation year, compared against the IRA expiry year.
        config: Scenario config supplying credit magnitudes and expiry.

    Returns:
        The IRA-adjusted LCOE in $/MWh. Unchanged for non-wind technologies
        and once the wind PTC has expired.
    """
    if year > config.ira_expiry_year:
        return lcoe
    if tech_type == "wind":
        return lcoe - config.ira_ptc_wind
    return lcoe
