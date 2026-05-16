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
    """Reduce a technology's LCOE by IRA investment credits.

    Used for new-entry economics, separate from the dispatch-side
    :func:`compute_dispatch_credits`. The wind PTC is a production credit
    that lowers effective levelized cost by a flat $/MWh amount; the solar
    and storage ITC is a capital credit, modeled here as scaling the
    capex-driven LCOE by ``(1 - ira_itc_solar)``. Both credits phase out
    after ``config.ira_expiry_year``.

    Args:
        tech_type: Candidate technology, e.g. ``"wind"``, ``"solar"``,
            ``"storage"`` or ``"gas_cc"``.
        lcoe: Pre-credit levelized cost of energy in $/MWh.
        year: Simulation year, compared against the IRA expiry year.
        config: Scenario config supplying credit magnitudes and expiry.

    Returns:
        The IRA-adjusted LCOE in $/MWh. Unchanged for technologies with no
        applicable credit, or once the credits have expired.
    """
    if year > config.ira_expiry_year:
        return lcoe
    if tech_type == "wind":
        return lcoe - config.ira_ptc_wind
    if tech_type in ("solar", "storage"):
        return lcoe * (1.0 - config.ira_itc_solar)
    return lcoe
