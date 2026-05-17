"""Inflation Reduction Act policy incentives."""

from market_sim.config.scenarios import ScenarioConfig

# IRA §45V clean hydrogen production tax credit. Paid per kilogram of clean
# hydrogen produced; converted to a $/MMBtu fuel-cost reduction using the
# lower heating value of hydrogen. Source: IRA §45V.
H2_45V_CREDIT_PER_KG: float = 3.0      # $/kg, top-tier green-H2 rate
H2_LHV_MMBTU_PER_KG: float = 0.1137    # MMBtu per kg H2 (lower heating value)

# IRA §45Q carbon sequestration credit for CO2 captured and stored.
# Source: IRA §45Q.
CCUS_45Q_CREDIT_PER_TON: float = 85.0  # $/tCO2 geologically stored


def h2_45v_credit_per_mmbtu(year: int, config: ScenarioConfig) -> float:
    """Return the IRA §45V hydrogen credit as a $/MMBtu fuel-cost reduction.

    The credit is paid per kilogram of clean hydrogen; dividing by the
    lower heating value converts it to the $/MMBtu basis used for the
    hydrogen turbine fuel cost. The credit phases out after
    ``config.ira_expiry_year``.

    Args:
        year: Simulation year, compared against the IRA expiry year.
        config: Scenario config supplying the expiry year.

    Returns:
        The §45V credit in $/MMBtu, or ``0.0`` once it has expired.
    """
    if year > config.ira_expiry_year:
        return 0.0
    return H2_45V_CREDIT_PER_KG / H2_LHV_MMBTU_PER_KG


def ccus_45q_credit_per_mwh(
    co2_captured_per_mwh: float, year: int, config: ScenarioConfig
) -> float:
    """Return the IRA §45Q CCUS credit as a $/MWh variable-cost offset.

    The credit pays :data:`CCUS_45Q_CREDIT_PER_TON` per tonne of CO2
    captured and stored; multiplying by the per-MWh captured CO2 rate
    gives a $/MWh offset. The credit phases out after
    ``config.ira_expiry_year``.

    Args:
        co2_captured_per_mwh: Tonnes of CO2 captured per MWh generated.
        year: Simulation year, compared against the IRA expiry year.
        config: Scenario config supplying the expiry year.

    Returns:
        The §45Q credit in $/MWh, or ``0.0`` once it has expired.
    """
    if year > config.ira_expiry_year:
        return 0.0
    return CCUS_45Q_CREDIT_PER_TON * co2_captured_per_mwh


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
    finished LCOE. Enhanced geothermal earns the same zero-emission
    production credit and is treated identically to wind here. The solar
    and storage ITC is a capital credit and is
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
    if tech_type in ("wind", "geothermal"):
        return lcoe - config.ira_ptc_wind
    return lcoe
