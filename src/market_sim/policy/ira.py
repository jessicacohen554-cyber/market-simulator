"""Inflation Reduction Act policy incentives."""

from market_sim.config.scenarios import ScenarioConfig

# IRA §45V clean hydrogen production tax credit. Paid per kilogram of clean
# hydrogen produced; converted to a $/MMBtu fuel-cost reduction using the
# lower heating value of hydrogen. Source: IRA §45V.
H2_45V_CREDIT_PER_KG: float = 3.0  # $/kg, top-tier green-H2 rate
H2_LHV_MMBTU_PER_KG: float = 0.1137  # MMBtu per kg H2 (lower heating value)

# IRA §45Q carbon sequestration credit for CO2 captured and stored.
# Source: IRA §45Q.
CCUS_45Q_CREDIT_PER_TON: float = 85.0  # $/tCO2 geologically stored

# IRA §45U zero-emission (existing) nuclear production tax credit. Base
# credit 0.3 cents/kWh, multiplied 5x for facilities meeting prevailing
# wage requirements — this module assumes the prevailing-wage rate
# throughout (the same convention already used for the wind PTC's
# ``ira_ptc_wind``, which is likewise the wage-compliant rate, not the
# unmultiplied base). Source: 26 U.S.C. §45U(a),(d)(1); triangulated in
# data/raw/policy/ira-credit-parameters/ira-credit-parameters.csv.
SECTION_45U_BASE_CREDIT_CENTS_PER_KWH: float = 0.3
SECTION_45U_PREVAILING_WAGE_MULTIPLIER: float = 5.0
SECTION_45U_CREDIT_CENTS_PER_KWH: float = (
    SECTION_45U_BASE_CREDIT_CENTS_PER_KWH * SECTION_45U_PREVAILING_WAGE_MULTIPLIER
)  # 1.5 cents/kWh = $15/MWh

# §45U(b)(2) gross-receipts phase-down: the credit is reduced (not below
# zero) by 16% of the amount by which the facility's average per-MWh sale
# price of electricity exceeds 2.5 cents/kWh. Source: 26 U.S.C. §45U(b)(2).
SECTION_45U_GROSS_RECEIPTS_THRESHOLD_CENTS_PER_KWH: float = 2.5
SECTION_45U_PHASE_DOWN_RATE: float = 0.16


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
    gives a $/MWh offset. ``config.ira_ccus_45q_last_year`` is an
    ELIGIBILITY deadline evaluated at the project's commit year (the
    begin-construction-before-2033 proxy, 26 U.S.C. §45Q(d)(1)): pass the
    build/retrofit year, and a project committed in an eligible year earns
    the full rate. The statutory **12-year credit window from
    placed-in-service** (§45Q(a)(3)-(4)) is NOT applied here — callers
    annualize this per-MWh rate over
    ``min(config.ira_45q_credit_window_years, asset life)`` themselves
    (the CCS retrofit screen's windowed payback and the new-build CCS
    LCOE levelization, ``model/capacity.py``), so the deadline never
    truncates an already-earned credit stream.

    Args:
        co2_captured_per_mwh: Tonnes of CO2 captured per MWh generated.
        year: The project's commit (build/retrofit) year, compared against
            the §45Q eligibility deadline.
        config: Scenario config supplying the §45Q last eligible year.

    Returns:
        The §45Q credit in $/MWh, or ``0.0`` for projects committed past
        the eligibility deadline.
    """
    if year > config.ira_ccus_45q_last_year:
        return 0.0
    return CCUS_45Q_CREDIT_PER_TON * co2_captured_per_mwh


def section_45u_credit_per_mwh(
    year: int, avg_price_per_mwh: float, config: ScenarioConfig
) -> float:
    """Return the IRA §45U existing-nuclear PTC as a $/MWh revenue credit.

    §45U pays :data:`SECTION_45U_CREDIT_CENTS_PER_KWH` per kWh, reduced —
    never below zero — by :data:`SECTION_45U_PHASE_DOWN_RATE` of the amount
    by which the unit's own average realized energy-market price (the
    statute's "gross receipts" basis) exceeds
    :data:`SECTION_45U_GROSS_RECEIPTS_THRESHOLD_CENTS_PER_KWH`. This is the
    nuclear retirement screen's revenue input, not a dispatch-cost adder —
    §45U is a per-MWh production credit paid on realized output, so it
    enters the same attribute-revenue seam as ``eac_price_nuclear``/the RPS
    shadow price (the caller takes ``max()``; see
    ``model.capacity.apply_economic_retirements``). The credit expires
    after ``config.ira_45u_last_year``.

    Args:
        year: Simulation year, compared against the §45U expiry year.
        avg_price_per_mwh: The unit's average realized energy-market price
            in $/MWh, used as the "gross receipts" phase-down basis.
        config: Scenario config supplying the §45U expiry year.

    Returns:
        The §45U credit in $/MWh, or ``0.0`` once expired or fully phased
        down by the gross-receipts test.
    """
    if year > config.ira_45u_last_year:
        return 0.0
    avg_price_cents_per_kwh = avg_price_per_mwh / 10.0  # $/MWh -> cents/kWh
    excess = max(
        0.0,
        avg_price_cents_per_kwh - SECTION_45U_GROSS_RECEIPTS_THRESHOLD_CENTS_PER_KWH,
    )
    reduction = SECTION_45U_PHASE_DOWN_RATE * excess
    credit_cents_per_kwh = max(0.0, SECTION_45U_CREDIT_CENTS_PER_KWH - reduction)
    return credit_cents_per_kwh * 10.0  # cents/kWh -> $/MWh


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


def wind_ptc_vintage_dispatch_offer(
    iso: str,
    year: int,
    zone_names: list[str],
    config: ScenarioConfig,
    hours: int,
):
    """Return the vintage-scoped ``(n_zones, hours)`` wind dispatch offer.

    The PTC-window-scoped replacement for the flat
    ``-config.ira_ptc_wind`` wind offer from
    :func:`compute_dispatch_credits`, gated by
    ``config.wind_ptc_vintage_offers`` (the caller checks the gate; this
    function only builds the array)::

        offer[z, t] = -PTC_statutory(year) x eligible_share[z, month(t)]

    * ``eligible_share`` is the measured per-zone-month share of online
      wind nameplate capacity inside its 10-year federal §45 window
      (EIA-860 vintages via
      :func:`market_sim.data.renewables.wind_ptc_eligible_monthly_share`).
      The capacity-weighted blend is the same first-moment zonal
      aggregation the model applies to demand and CF: a single LP wind
      column per zone cannot carry the fleet's true two-step {-PTC, ~$0}
      bid stack, so the zone bids its fleet's mean keep-running value.
      (The two-step limitation is recorded at the ScenarioConfig field.)
    * ``PTC_statutory`` is the IRS-published inflation-adjusted §45 credit
      for the production year
      (:data:`market_sim.config.constants.WIND_PTC_STATUTORY_USD_PER_MWH`),
      falling back to the flat ``config.ira_ptc_wind`` for years outside
      the published table (forward years).
    * Past the ``config.ira_wind_solar_last_year`` cliff the flat path
      already zeroes the credit; this function mirrors that gate and
      returns ``None`` (in-window vintages earning past the cliff is a
      known conservatism inherited from the existing convention, not
      re-adjudicated here).

    Returns ``None`` when the share data is unavailable or the credit has
    expired — callers keep the flat unscoped offer.
    """
    if year > config.ira_wind_solar_last_year:
        return None
    from market_sim.config.constants import WIND_PTC_STATUTORY_USD_PER_MWH
    from market_sim.data.fleet import _hour_to_month_index
    from market_sim.data.renewables import wind_ptc_eligible_monthly_share

    share = wind_ptc_eligible_monthly_share(iso, zone_names, year)
    if share is None:
        return None
    ptc = WIND_PTC_STATUTORY_USD_PER_MWH.get(year, config.ira_ptc_wind)
    month_idx = _hour_to_month_index(hours)
    return -ptc * share[:, month_idx]


def ira_phaseout_fraction(year: int, config: ScenarioConfig) -> float:
    """Return the IRA §45Y/§48E credit fraction for non-wind/solar clean tech.

    The tech-neutral OBBBA phase-down for facilities other than wind/solar
    (storage, nuclear, geothermal, hydropower) is a construction-begin-year
    STEP schedule, not a continuous ramp: 100% through
    ``ira_other_clean_last_full_year``, 75% through
    ``ira_other_clean_75pct_year``, 50% through
    ``ira_other_clean_50pct_year``, 0% from ``ira_other_clean_phaseout_end``
    on. The model uses a generator's build/entry year as the
    construction-begin-year proxy. Source: 26 U.S.C. §45Y/§48E, triangulated
    (not a direct primary-text read — see the confidence note in
    data/raw/policy/ira-credit-parameters/README.md) in
    data/raw/policy/ira-credit-parameters/ira-credit-parameters.csv.

    This REPLACES the module's previous continuous 5-step-implied linear
    ramp (2028 full / 2033 zero, an undocumented estimate that predates this
    statute citation) with the statute-triangulated 2033/2034/2035/2036
    100/75/50/0% step schedule — a real default-behavior change for any
    scenario relying on the prior defaults (CLAUDE.md rule 24: prefer the
    cited statute reading over the earlier undocumented guess).
    """
    if year <= config.ira_other_clean_last_full_year:
        return 1.0
    if year <= config.ira_other_clean_75pct_year:
        return 0.75
    if year <= config.ira_other_clean_50pct_year:
        return 0.50
    return 0.0


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
