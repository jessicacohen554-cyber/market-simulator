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

# IRA §45U zero-emission (existing) nuclear production tax credit.
#
# STATUTORY ORDERING — the 5x multiplies the NET credit, not the rate.
# §45U(a) is itself a net quantity: "the amount by which (1) the product of
# (A) 0.3 cents, multiplied by (B) the kilowatt hours ... exceeds (2) the
# reduction amount for such taxable year". §45U(d)(1) then multiplies "the
# amount of the credit determined under SUBSECTION (a) ... by 5" for a
# facility meeting the prevailing-wage requirements. The 5x operand is
# therefore the post-phase-down amount:
#
#     §45U (cents/kWh) = 5 x max(0, R_year - 0.16 x max(0, GR - T_year))
#
# i.e. $15/MWh below the threshold, dying at GR = T_year + R_year / 0.16
# ($43.75/MWh at the nominal amounts). This module previously folded the 5x
# into the 0.3-cent rate and then subtracted an UNMULTIPLIED reduction,
# which left the phase-down slope 5x too shallow (0.16 vs 0.80 $/$) and
# pushed the zero-out price out to $118.75/MWh — finding F-1 of
# docs/handoffs/d28-45u-composition-memo-2026-08-08.md §1.1/§4, corroborated
# there against the primary text and an independent industry worked example.
# This module assumes the prevailing-wage rate throughout (the same
# convention already used for the wind PTC's ``ira_ptc_wind``, which is
# likewise the wage-compliant rate, not the unmultiplied base).
# Source: 26 U.S.C. §45U(a)(1)(A), (d)(1); triangulated in
# data/raw/policy/ira-credit-parameters/ira-credit-parameters.csv.
SECTION_45U_BASE_CREDIT_CENTS_PER_KWH: float = 0.3  # §45U(a)(1)(A)
SECTION_45U_PREVAILING_WAGE_MULTIPLIER: float = 5.0  # §45U(d)(1), applied to the NET

# §45U(b)(2)(A) reduction amount: the LESSER of (i) the (a)(1) amount or
# (ii) 16 percent of the excess of the facility's gross receipts from
# electricity sold over the product of 2.5 cents and those kWh. The
# "lesser of" is what floors the credit at zero. Dividing through by kWh
# gives the per-unit form used below. Sources: 26 U.S.C.
# §45U(b)(2)(A)(ii) (the 16 percent) and §45U(b)(2)(A)(ii)(II)(aa) (the
# 2.5 cents).
SECTION_45U_GROSS_RECEIPTS_THRESHOLD_CENTS_PER_KWH: float = 2.5
SECTION_45U_PHASE_DOWN_RATE: float = 0.16

# §45U(c)(1)-(2) inflation adjustment, base calendar year 2023: the
# (a)(1)(A) 0.3-cent amount and the (b)(2)(A)(ii)(II)(aa) 2.5-cent amount
# "shall each be adjusted by multiplying such amount by the inflation
# adjustment factor ... for the calendar year in which the sale occurs",
# the first rounded to the nearest 0.05 cent and the second to the nearest
# 0.1 cent. Values below are the applicable amounts AS PRINTED in the IRS
# notices — not our own arithmetic from the published factor:
#   2024 — no §45U notice published. The 2024 factor is
#          deflator(2023)/deflator(2023) = 1.0000 under the construction
#          both notices below use, so the statutory nominal amounts stand
#          unadjusted; the pair is taken from the constants above rather
#          than restated.
#   2025 — Notice 2025-37 (IRB 2025-30), factor 1.0242 (GDP implicit price
#          deflator 2024 = 125.234 over 2023 = 122.273). Printed: the
#          §45U(a)(1)(A) amount is "0.3 cents (0.3 cents (or $0.003) x
#          1.0242, then rounded to the nearest multiple of 0.05 cent)" and
#          the §45U(b)(2)(A)(ii)(II)(aa) amount is "2.6 cents (2.5 cents
#          (or $0.025) x 1.0242, then rounded to the nearest multiple of
#          0.1 cent)".
#   2026 — Notice 2026-41 (IRB 2026-29, 2026-07-13) §3.01, factor 1.0539
#          (deflator 2025 = 128.986 over 2023 = 122.39). Printed amounts
#          read from the bulletin text: §45U(a)(1)(A) "0.3 cents",
#          §45U(b)(2)(A)(ii)(II)(aa) "2.6 cents".
# Years beyond the last published notice HOLD the last published pair, and
# years before the first hold the first. That is deterministic and adds no
# degree of freedom (rule 21 [R-DOF]): no factor is published for a forward
# year, and extrapolating an escalator would be a tuned forward assumption
# with no primary source. Holding is one-sided conservative — a frozen
# threshold understates T_year and so understates the credit.
SECTION_45U_APPLICABLE_AMOUNTS_CENTS_PER_KWH: dict[int, tuple[float, float]] = {
    2024: (
        SECTION_45U_BASE_CREDIT_CENTS_PER_KWH,
        SECTION_45U_GROSS_RECEIPTS_THRESHOLD_CENTS_PER_KWH,
    ),
    2025: (0.3, 2.6),
    2026: (0.3, 2.6),
}


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


def section_45u_applicable_amounts_cents_per_kwh(year: int) -> tuple[float, float]:
    """Return the §45U(c)(1) inflation-adjusted amounts for a sale year.

    Looks up the calendar year's published applicable amounts in
    :data:`SECTION_45U_APPLICABLE_AMOUNTS_CENTS_PER_KWH` — the IRS-notice
    amounts for the §45U(a)(1)(A) credit rate and the
    §45U(b)(2)(A)(ii)(II)(aa) gross-receipts threshold. A year outside the
    published range holds the nearest published pair (the earliest for
    years before the table, the latest for years after it); see the table's
    own comment for why that is the zero-DOF choice rather than an
    extrapolated escalator.

    Args:
        year: Calendar year in which the sale occurs, per §45U(c)(1).

    Returns:
        ``(rate_cents_per_kwh, threshold_cents_per_kwh)`` for that year.
    """
    published = SECTION_45U_APPLICABLE_AMOUNTS_CENTS_PER_KWH
    if year in published:
        return published[year]
    if year < min(published):
        return published[min(published)]
    return published[max(published)]


def section_45u_credit_per_mwh(
    year: int, avg_price_per_mwh: float, config: ScenarioConfig
) -> float:
    """Return the IRA §45U existing-nuclear PTC as a $/MWh revenue credit.

    Implements the statutory ordering (26 U.S.C. §45U; module comment
    above). Writing ``R``/``T`` for the year's §45U(c)(1) inflation-adjusted
    rate and threshold from
    :func:`section_45u_applicable_amounts_cents_per_kwh` and ``GR`` for the
    per-kWh gross receipts::

        reduction = min(R, SECTION_45U_PHASE_DOWN_RATE x max(0, GR - T))
        credit    = SECTION_45U_PREVAILING_WAGE_MULTIPLIER x (R - reduction)

    The ``min(R, ...)`` is §45U(b)(2)(A)'s "lesser of", which is what floors
    the credit at zero; the 5x is §45U(d)(1) applied to the subsection-(a)
    net, NOT to the rate. At the nominal amounts that is $15/MWh below
    $25/MWh, phasing down at $0.80 per $1 of gross receipts and reaching
    zero at $43.75/MWh.

    This is the nuclear retirement screen's revenue input, not a
    dispatch-cost adder — §45U is a per-MWh production credit paid on
    realized output, so it enters the same attribute-revenue seam as
    ``eac_price_nuclear``/the RPS shadow price (the caller takes ``max()``;
    see ``model.capacity.apply_economic_retirements``). The credit expires
    after ``config.ira_45u_last_year``.

    Args:
        year: Simulation year. Compared against the §45U expiry year, and
            used as the sale calendar year for the §45U(c)(1) amounts.
        avg_price_per_mwh: The unit's average realized energy-market price
            in $/MWh, used as the "gross receipts" phase-down basis.
        config: Scenario config supplying the §45U expiry year.

    Returns:
        The §45U credit in $/MWh, or ``0.0`` once expired or fully phased
        down by the gross-receipts test.
    """
    if year > config.ira_45u_last_year:
        return 0.0
    rate_cents_per_kwh, threshold_cents_per_kwh = (
        section_45u_applicable_amounts_cents_per_kwh(year)
    )
    gross_receipts_cents_per_kwh = avg_price_per_mwh / 10.0  # $/MWh -> cents/kWh
    excess = max(0.0, gross_receipts_cents_per_kwh - threshold_cents_per_kwh)
    # §45U(b)(2)(A): the reduction is the LESSER of the (a)(1) amount or 16%
    # of the excess -- so the subsection-(a) net never goes below zero.
    reduction = min(rate_cents_per_kwh, SECTION_45U_PHASE_DOWN_RATE * excess)
    net_credit_cents_per_kwh = rate_cents_per_kwh - reduction  # the (a) amount
    # §45U(d)(1): 5x the amount determined under subsection (a).
    credit_cents_per_kwh = (
        SECTION_45U_PREVAILING_WAGE_MULTIPLIER * net_credit_cents_per_kwh
    )
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
    construction-begin-year proxy.

    Source: 26 U.S.C. §45Y(d)(2)-(3) and §48E(e)(2)-(3), read from the
    Office of the Law Revision Counsel US Code (uscode.house.gov, prelim
    edition) on 2026-07-31 — a DIRECT PRIMARY-TEXT read that supersedes the
    former triangulated-from-secondary-sources caveat (FFR-PB, FR-20 M2).
    §45Y(d)(2) sets 100%/75%/50%/0% for construction beginning in the
    first/second/third/any-subsequent calendar year following the
    "applicable year"; §45Y(d)(3), as amended by OBBBA (Pub. L. 119-21
    §70512(a)(2)), fixes that applicable year flatly at calendar year 2032,
    having struck the prior "later of 2032 or the <=25%-of-2022 electricity
    emissions year" determination. 2032 therefore yields exactly the
    2033/2034/2035/2036 breakpoints defaulted in ScenarioConfig. Values
    landed in data/raw/policy/ira-credit-parameters/ira-credit-parameters.csv;
    provenance narrative in that directory's README.md and
    docs/handoffs/ffr-pb-atb-statute-intake-2026-07-31.md.

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

    Wind PTC: eligible through ira_wind_solar_last_year, then zero. An
    eligible vintage's credit is levelized over min(the statutory 10-year
    §45 window, book life) — never credited for the plant's whole life —
    via :func:`~market_sim.model.capacity_evolution.new_entry.
    wind_ptc_levelized_per_mwh`, the single screen-side PTC computation
    site (FFR-4C, owner decision D-13).
    Geothermal PTC: graduated phaseout per ira_phaseout_fraction. KNOWN
    DEFECT, reported by FFR-4C and awaiting its own charter: this branch
    still credits the full unwindowed rate over book life, though the
    §45/§45Y 10-year credit period applies to geothermal too. Left as-is
    deliberately — D-13's scope is the wind PTC alone.
    Solar ITC: handled in compute_lcoe (capex reduction), not here.
    """
    if tech_type == "wind":
        if year > config.ira_wind_solar_last_year:
            return lcoe
        # Imported here to avoid a module-level cycle: capacity_evolution's
        # new_entry imports this module at top level (same pattern as
        # new_entry's own function-scope `.ccs` import for the §45Q window).
        from market_sim.model.capacity_evolution.new_entry import (
            wind_ptc_levelized_per_mwh,
        )

        return lcoe - wind_ptc_levelized_per_mwh(config)
    if tech_type == "geothermal":
        frac = ira_phaseout_fraction(year, config)
        if frac <= 0.0:
            return lcoe
        return lcoe - config.ira_ptc_wind * frac
    return lcoe
