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
    ``config.ira_h2_45v_last_year``.

    Args:
        year: Simulation year, compared against the §45V cutoff.
        config: Scenario config supplying the §45V last eligible year.

    Returns:
        The §45V credit in $/MMBtu, or ``0.0`` once it has expired.
    """
    if year > config.ira_h2_45v_last_year:
        return 0.0
    return H2_45V_CREDIT_PER_KG / H2_LHV_MMBTU_PER_KG


def ccus_45q_credit_per_mwh(
    co2_captured_per_mwh: float, year: int, config: ScenarioConfig
) -> float:
    """Return the IRA §45Q CCUS credit as a $/MWh variable-cost offset.

    The credit pays :data:`CCUS_45Q_CREDIT_PER_TON` per tonne of CO2
    captured and stored; multiplying by the per-MWh captured CO2 rate
    gives a $/MWh offset. The credit phases out after
    ``config.ira_ccus_45q_last_year``.

    Args:
        co2_captured_per_mwh: Tonnes of CO2 captured per MWh generated.
        year: Simulation year, compared against the §45Q cutoff.
        config: Scenario config supplying the §45Q last eligible year.

    Returns:
        The §45Q credit in $/MWh, or ``0.0`` once it has expired.
    """
    if year > config.ira_ccus_45q_last_year:
        return 0.0
    return CCUS_45Q_CREDIT_PER_TON * co2_captured_per_mwh


def compute_dispatch_credits(config: ScenarioConfig, year: int) -> tuple[float, float]:
    """Return (wind_mc, solar_mc) dispatch cost adders in $/MWh.

    Wind PTC active through config.ira_wind_solar_last_year. Solar ITC
    does not affect dispatch MC. Credits are binary for wind/solar: full
    value or zero (the OBBBA cliff, not a graduated phaseout).
    """
    if year > config.ira_wind_solar_last_year:
        return 0.0, 0.0
    wind_mc = -config.ira_ptc_wind
    solar_mc = 0.0
    return wind_mc, solar_mc


def ira_phaseout_fraction(year: int, config: ScenarioConfig) -> float:
    """Return the IRA credit fraction for non-wind/solar clean tech.

    100% through ira_other_clean_last_full_year, then linear ramp to 0%
    by ira_other_clean_phaseout_end.
    """
    if year <= config.ira_other_clean_last_full_year:
        return 1.0
    if year >= config.ira_other_clean_phaseout_end:
        return 0.0
    span = config.ira_other_clean_phaseout_end - config.ira_other_clean_last_full_year
    elapsed = year - config.ira_other_clean_last_full_year
    return max(0.0, 1.0 - elapsed / span)


def apply_ira_credits_to_lcoe(
    tech_type: str, lcoe: float, year: int, config: ScenarioConfig
) -> float:
    """Reduce LCOE by the applicable IRA credit.

    Wind PTC: full value through ira_wind_solar_last_year, then zero.
    Geothermal PTC: graduated phaseout per ira_phaseout_fraction.
    Solar ITC: handled in compute_lcoe (capex reduction), not here.
    """
    if tech_type == "wind":
        if year > config.ira_wind_solar_last_year:
            return lcoe
        return lcoe - config.ira_ptc_wind
    if tech_type == "geothermal":
        frac = ira_phaseout_fraction(year, config)
        if frac <= 0.0:
            return lcoe
        return lcoe - config.ira_ptc_wind * frac
    return lcoe
