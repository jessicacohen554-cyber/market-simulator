"""Capacity expansion and retirement modeling.

Part 1: fleet retirements. Three mechanisms remove generators between
simulation years:

* **Confirmed exits** (:func:`apply_confirmed_exits`) -- units bound by an
  enforceable public instrument (consent decree, statute, RTO deactivation
  acceptance, regulatory order, RMR end) force-retire (or derate a plant-binned
  tranche) at the instrument date, any fuel, bypassing the reliability floor.
  Read from the confirmed-retirements registry
  (:func:`market_sim.data.confirmed_retirements.load_confirmed_exits`); GATED on
  ``confirmed_exits_enabled`` (default on, flipped 2026-07-05) and forecast-mode
  only. This is the
  ONLY exogenous fossil exit channel — an announced fossil date does not force
  an exit (below).
* **Announced retirements** (:func:`apply_announced_retirements`) -- units with a
  scheduled EIA-860 ``retirement_year``. By default
  (``forecast_fossil_retirement_economic``) **fossil** units (coal/gas/oil) are
  exempt: an announced fossil date is an announcement, not a certainty, so their
  phaseout is left to the economic screen below and the forecast stays
  condition-responsive — for the whole fossil fleet this step is a **default
  no-op**. Non-fossil units (nuclear, hydro, renewables, storage) honor their
  announced date within the EIA-860 data horizon; beyond it a non-fossil date is
  honored only if the unit is in the confirmed registry, so speculative
  end-of-life placeholders stop force-retiring (the horizon gate activates with
  the confirmed channel).
* **Economic retirements** -- thermal units whose attainable (pro-forma)
  inframarginal margin -- per-hour ``max(0, price - mc, reserve price)`` on
  available capacity, the same construction as the Potomac SOM net-revenue
  tables -- fails to cover their going-forward fixed cost for a
  fuel-type-specific number of consecutive years are retired, least
  efficient first within each fuel class. Coal faces a shorter loss window
  and a higher effective fixed cost than gas, and a system-wide reliability
  floor prevents thermal capacity from being stripped below the reserve
  margin.

Part 2: capacity additions. New generators enter the fleet via two
mechanisms, costed with Wright's-Law learning curves and IRA credits:

* **Known additions** -- units with a planned ``online_year`` are
  activated when the simulation reaches that year.
* **Economic new entry** -- candidate technologies whose expected revenue
  exceeds their levelized cost are built, subject to an annual
  interconnection-queue cap, highest-margin technology first. Clean
  technologies also see the prior year's REC price (the RPS constraint's
  shadow price) added to their expected revenue.

The renewable portfolio standard is no longer a force-build here: it is
enforced as an LP constraint in dispatch, and its shadow price drives
clean builds through the economic new-entry screen above.

A CCS retrofit step also runs each year, converting existing gas CC units
to ``gas_cc_ccs`` when the economics clear. :func:`evolve_fleet` chains all
the mechanisms into one year-step.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from itertools import groupby

import numpy as np

from market_sim.config.constants import (
    ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
    ADEQUACY_EXTERNAL_TIE_FIRM_MW,
    CCUS_PARAMS,
    CO2_RATES,
    DEFAULT_MARKET_DESIGN,
    EFORD,
    GEOTHERMAL_PARAMS,
    GLOBAL_ANNUAL_DEPLOYMENT_GW,
    HEAT_RATE_BINS,
    HOURS_PER_YEAR,
    HYDROGEN_TURBINE_PARAMS,
    MARKET_DESIGN,
    NEW_ENTRY_COSTS,
    NONFOSSIL_ANNOUNCED_HORIZON_YEARS,
    NOX_RATES,
    OFFSHORE_WIND_PARAMS,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO,
    QUEUE_CAP_GW,
    QUEUE_CAP_PER_TECH_GW,
    RENEWABLE_CAPACITY_CREDIT,
    RENEWABLE_CAPACITY_CREDIT_BY_ISO,
    STORAGE_DEPLOYMENT_CEILING_MW,
    STORAGE_ELCC_DILUTION_CEILING_RATIO_BY_ISO,
    STORAGE_ELCC_DILUTION_REFERENCE_MW_BY_ISO,
    THERMAL_ACCREDITATION_BASIS_BY_ISO,
    VOM,
    WRIGHT_REFERENCE_GW,
)
from market_sim.config.capacity_area_crosswalk import aggregate_by_zone
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.reserve_config import (
    QUICK_START_FUEL_TYPES,
    RESERVE_FUEL_TYPES,
)
from market_sim.config.scenarios import ScenarioConfig, resolve_new_entry_costs
from market_sim.data import capacity_deliverability as capdel
from market_sim.model.ancillary import as_revenue_per_mw_yr
from market_sim.data.confirmed_retirements import ConfirmedExit
from market_sim.data.fleet import (
    EIA860_OPERABLE_VINTAGE,
    FleetArrays,
    Generator,
    aggregate_fleet,
)
from market_sim.data.hydrogen import compute_h2_fuel_cost
from market_sim.data.renewables import get_renewable_zone
from market_sim.model.dispatch import DispatchResult
from market_sim.policy.ira import (
    apply_ira_credits_to_lcoe,
    ccus_45q_credit_per_mwh,
    h2_45v_credit_per_mmbtu,
    section_45u_credit_per_mwh,
)
from market_sim.policy.eac import get_eac_price_for_new_entry

logger = logging.getLogger(__name__)

# Fuel classes treated as dispatchable thermal capacity for economic
# retirement, mapped to their ScenarioConfig fixed-O&M field ($/kW-yr).
_THERMAL_FOM: dict[str, str] = {
    "gas_cc": "fixed_om_gas_cc",
    "gas_ct": "fixed_om_gas_ct",
    "gas_st": "fixed_om_gas_st",
    "gas_cc_ccs": "fixed_om_gas_cc_ccs",
    "coal": "fixed_om_coal",
    "oil": "fixed_om_oil",
    "nuclear": "fixed_om_nuclear",
}

# Fuel classes that count toward the clean-energy share. This is a
# clean-*accounting* basis (``compute_clean_share``), NOT an RPS-eligibility
# list: nuclear and hydro are clean but are not renewable and do not satisfy a
# Renewable Portfolio Standard, so they must not be credited the RPS shadow
# price (see ``_RPS_ELIGIBLE_FUELS``).
_CLEAN_FUELS: frozenset[str] = frozenset({"wind", "solar", "nuclear", "hydro"})

# Fuel classes eligible to satisfy a Renewable Portfolio Standard and therefore
# to earn the endogenous RPS shadow price (REC dual) in the capacity screens.
# CX-6a (capacity-economics plan 2026-07 §6.5(a)): an RPS is a *renewable*
# standard -- existing nuclear and hydro are clean but not RPS-eligible, so they
# are excluded here. Nuclear's zero-emission support flows separately through
# ``eac_price_nuclear`` (ZEC/CES), never the RPS dual. This set matches the
# new-entry screen's ``_RENEWABLE_NEW_FUELS`` (already wind/solar only); the
# split fixes the retirement screen, which previously credited via _CLEAN_FUELS.
_RPS_ELIGIBLE_FUELS: frozenset[str] = frozenset({"wind", "solar"})

# Firm clean (non-VRE) capacity fuels. The reliability floor no longer nets
# these out at nameplate — its accreditation rebuild routes every resource
# (hydro included) through accredited_firm_capacity_mw at its UCAP/capacity-
# credit value (capacity-economics plan 2026-07 §3.2). The constant is retained
# only as the evolution ledger's ``firm_clean_mw`` reporting basis
# (runner.py); it no longer participates in any retirement/adequacy decision.
_FIRM_CLEAN_FUELS: tuple[str, ...] = ("hydro",)

# Per-fuel ScenarioConfig field names for the consecutive-loss threshold.
_RETIREMENT_YEARS: dict[str, str] = {
    "coal": "retirement_years_coal",
    "gas_ct": "retirement_years_gas_ct",
    "gas_cc": "retirement_years_gas_cc",
    "gas_st": "retirement_years_gas_st",
    "gas_cc_ccs": "retirement_years_gas_cc_ccs",
    "oil": "retirement_years_oil",
    "nuclear": "retirement_years_nuclear",
}

# Per-fuel ScenarioConfig field names for the effective-FOM multiplier.
_FOM_MULTIPLIER: dict[str, str] = {
    "coal": "retirement_fom_multiplier_coal",
    "gas_ct": "retirement_fom_multiplier_gas_ct",
    "gas_cc": "retirement_fom_multiplier_gas_cc",
    "gas_st": "retirement_fom_multiplier_gas_st",
    "gas_cc_ccs": "retirement_fom_multiplier_gas_cc_ccs",
    "oil": "retirement_fom_multiplier_oil",
    "nuclear": "retirement_fom_multiplier_nuclear",
}

# Assumed total thermal-plant operating life (years), used to estimate a
# unit's remaining useful life when screening CCS retrofit candidates.
# Source: NREL ATB 2024 -- typical gas combined-cycle book life.
_THERMAL_PLANT_LIFE_YEARS: int = 40

# Zone that hosts economic new entry and the adequacy backstop, per ISO.
# The default is the ISO's largest-load-share zone; MISO is pinned because at
# the six-zone refinement the largest share flipped to MISO-South (0.2711) —
# an unacceptable default for what is overwhelmingly a Midwest build pipeline.
# MISO-Illinois is the central Midwest wheel-through zone, so a default-sited
# build distorts the congestion topology least (scope doc §5 item 12).
_NEW_ENTRY_DEFAULT_ZONE: dict[str, str] = {"MISO": "MISO-Illinois"}


def _default_build_zone(iso_config) -> str:
    """Return the default zone for new entry / adequacy-backstop builds."""
    pinned = _NEW_ENTRY_DEFAULT_ZONE.get(iso_config.name)
    if pinned is not None:
        return pinned
    return max(iso_config.zones, key=lambda z: z.load_share).name


# Placeholder capacity factor for screening CCS retrofit economics -- a
# representative mid-merit combined-cycle duty cycle.
# TODO: use each unit's actual prior-year capacity factor once per-generator
# dispatch is threaded through (it is available in the prior-year result).
# Source: engineering judgment -- mid-merit gas CC.
_RETROFIT_SCREEN_CF: float = 0.55


def compute_attribute_revenue(
    fuel_type: str,
    generation_mwh: float,
    eac_price: float,
    rps_shadow_price: float = 0.0,
) -> float:
    """Return annual attribute revenue for a single unit.

    The resource earns ONE attribute payment per MWh -- the higher of the
    exogenous EAC price or the endogenous RPS shadow price. These do NOT
    stack. The attribute certificate is sold to whichever market clears
    higher.

    Args:
        fuel_type: Generator fuel type string.
        generation_mwh: Annual generation in MWh.
        eac_price: Exogenous EAC price for this resource type ($/MWh).
        rps_shadow_price: Endogenous RPS constraint dual from prior year ($/MWh).

    Returns:
        Annual attribute revenue in $.
    """
    effective_attribute_price = max(eac_price, rps_shadow_price)
    return effective_attribute_price * generation_mwh


# Fossil fuel types whose forecast phaseout is governed by the economic-
# retirement screen, not by a hardcoded announced date. An EIA-860 "planned
# retirement" for a coal/gas/oil unit is an *announcement*; in a forecast the
# actual exit should respond to economics (the unit may close earlier if it
# loses money, or run longer if it stays in-merit), so honoring the announced
# date would override the very mechanism that makes the forecast condition-
# responsive. Non-fossil units (nuclear, hydro, wind, solar, storage) keep
# retiring on their announced EIA-860 date — those exits are policy/contract/
# end-of-life events with no economic-screen analogue.
_FOSSIL_FUELS: frozenset[str] = frozenset(
    {"coal", "gas_ct", "gas_cc", "gas_st", "gas_cc_ccs", "oil"}
)


def _confirmed_effective_year(exit_: ConfirmedExit) -> int:
    """Return the first simulation year a confirmed exit takes effect.

    Annual-grain convention (mirroring the additions pipeline): a unit is out
    from ``exit_year`` when its instrument specifies a first-half month
    (``exit_month <= 6``) or no month at all, else from ``exit_year + 1``
    (majority-of-year rule). Month-precise forecast exits via the COD ramp are a
    v2 follow-up (plan §5.1).
    """
    if exit_.exit_month is not None and exit_.exit_month > 6:
        return exit_.exit_year + 1
    return exit_.exit_year


def _unit_generator_id(gen: Generator) -> str | None:
    """Return a unit-grain generator's EIA generator ID, or ``None``.

    The EIA-860 loader builds ``unit_id = f"{plant_code}_{generator_id}"``
    (:func:`market_sim.data.fleet.load_fleet_from_csv`), so the suffix after the
    plant-code prefix is the generator ID. Returns ``None`` for a generator whose
    ``unit_id`` does not carry the prefix (a synthesized/aggregated unit), which
    the confirmed-exit matcher treats as plant-binned (derate, not unit drop).
    """
    prefix = f"{int(gen.plant_code)}_"
    if gen.plant_code and gen.unit_id.startswith(prefix):
        return gen.unit_id[len(prefix) :]
    return None


# MW below which a derated plant-binned generator is dropped entirely.
_CONFIRMED_EXIT_MW_EPS: float = 1e-6


def apply_confirmed_exits(
    fleet: list[Generator],
    year: int,
    exits: list[ConfirmedExit],
    apply_backlog: bool = False,
) -> list[Generator]:
    """Return the fleet with confirmed (binding-instrument) exits applied.

    Step 0 of the forecast capacity evolution (:func:`evolve_fleet`) and the
    first simulated year (:func:`market_sim.data.fleet.build_base_fleet`), run
    BEFORE the announced-date step and the economic screen. Each confirmed exit
    (an enforceable public instrument — consent decree, statute, RTO
    deactivation acceptance, regulatory order, RMR end) force-retires its unit at
    the instrument date, **bypassing the reliability floor** (a decree does not