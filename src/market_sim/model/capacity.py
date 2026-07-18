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

import numpy as np

from market_sim.config.constants import (
    ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
    ADEQUACY_EXTERNAL_TIE_FIRM_MW,
    CCUS_PARAMS,
    CO2_RATES,
    DEFAULT_MARKET_DESIGN,
    EFORD,
    FORECAST_POOL_REQUIREMENT_BY_ISO,
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
    RENEWABLE_ELCC_CURVES_BY_ISO,
    STORAGE_DEPLOYMENT_CEILING_MW,
    STORAGE_ELCC_DILUTION_CEILING_RATIO_BY_ISO,
    STORAGE_ELCC_DILUTION_REFERENCE_MW_BY_ISO,
    THERMAL_ACCREDITATION_BASIS_BY_ISO,
    THERMAL_ELCC_CLASS_RATING_BY_ISO,
    VOM,
    WRIGHT_REFERENCE_GW,
    evaluate_renewable_elcc_curve,
)
from market_sim.config.capacity_area_crosswalk import aggregate_by_zone
from market_sim.config.entry_config import (
    ENTRY_COD_LAG_DEFAULT_YEARS,
    ENTRY_COD_LAG_YEARS,
)
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
from market_sim.policy.federal_ces import (
    effective_eac_price_for_tech,
    effective_eac_price_for_unit,
)
from market_sim.policy.ira import (
    apply_ira_credits_to_lcoe,
    ccus_45q_credit_per_mwh,
    h2_45v_credit_per_mmbtu,
    section_45u_credit_per_mwh,
)

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

# Per-fuel ScenarioConfig field names for the consecutive-loss threshold
# (LEGACY rule only — retirement_rule="legacy").
_RETIREMENT_YEARS: dict[str, str] = {
    "coal": "retirement_years_coal",
    "gas_ct": "retirement_years_gas_ct",
    "gas_cc": "retirement_years_gas_cc",
    "gas_st": "retirement_years_gas_st",
    "gas_cc_ccs": "retirement_years_gas_cc_ccs",
    "oil": "retirement_years_oil",
    "nuclear": "retirement_years_nuclear",
}

# Per-fuel ScenarioConfig field names for the decision→deactivation EXECUTION
# lag (R-NEW pipeline rule — retirement_rule="pipeline"). Identification:
# RC-0B §a.3 measured EIA-860 announced-to-deactivation lag medians
# (ff-retirement-rule-redesign-2026-07.md §5); see the field docstrings.
_RETIREMENT_EXECUTION_LAG: dict[str, str] = {
    "coal": "retirement_execution_lag_coal",
    "gas_ct": "retirement_execution_lag_gas_ct",
    "gas_cc": "retirement_execution_lag_gas_cc",
    "gas_st": "retirement_execution_lag_gas_st",
    "gas_cc_ccs": "retirement_execution_lag_gas_cc_ccs",
    "oil": "retirement_execution_lag_oil",
    "nuclear": "retirement_execution_lag_nuclear",
}


def _execution_lag_years(config: ScenarioConfig, fuel_type: str) -> int:
    """Return the R-NEW decision→deactivation execution lag for one fuel.

    ``gas_cc_ccs`` inherits ``retirement_execution_lag_gas_cc`` when its own
    field is ``None`` (no CCS retirement exists anywhere — RC-0B §a.4; the
    inheritance is the memo-§5 open-DOF disposition, not a tunable).
    """
    field_name = _RETIREMENT_EXECUTION_LAG[fuel_type]
    lag = getattr(config, field_name)
    if lag is None and fuel_type == "gas_cc_ccs":
        lag = getattr(config, "retirement_execution_lag_gas_cc")
    return int(lag)


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
    care about the model's reserve margin) and any fuel exemption. Superseded
    rows never reach here (the loader drops them), so a counter-instrument (RMR,
    202(c)) correctly reverts the unit to the economic screen.

    A confirmed exit is a discrete, once-at-its-date event, never a recurring
    per-year filter. ``fleet`` threads forward mutated through the runner's
    year loop, so re-selecting an already-applied row from ``exits`` every year
    would re-derate the same MW repeatedly (a plant-binned exit's remaining
    tranche has no memory of which rows already reduced it). Two call sites
    coordinate the once-only semantics via ``apply_backlog``:

    * ``apply_backlog=True`` (:func:`market_sim.data.fleet.build_base_fleet`,
      the first simulated year only): selects every exit with
      ``effective_year <= year`` — the pre-start backlog, applied exactly once
      as the fleet is built, since a unit confirmed to exit before or in the
      first simulated year can never reach :func:`evolve_fleet`.
    * ``apply_backlog=False`` (the default, :func:`evolve_fleet`, every later
      year): selects only exits with ``effective_year == year`` — the row
      newly effective this year — so a row already applied (in the backlog or
      a prior year) is never re-selected.

    Matching (plan §5.1):

    * **Unit-grain** generators (raw EIA-860 units, ``unit_id`` =
      ``"{plant_code}_{generator_id}"``) are dropped when their generator ID is
      confirmed to exit this year.
    * **Plant-binned** generators (ERCOT CAMPD bins / synthesized tranche plants,
      ``is_campd_bin`` or an unparseable ``unit_id``) are **derated**: the plant's
      binned MW is scaled by ``(binned_mw - exit_mw) / binned_mw`` — pmax/pmin and
      the MW-valued tranche floors scale proportionally, dropping a tranche when
      its remaining MW ≤ ε. The residual heat-rate composition shift (the exiting
      unit is usually the worst) is accepted second-order error. Because each
      row is now selected exactly once (never re-summed against an
      already-shrunk denominator), a plant with multiple rows landing in
      different years derates correctly year over year.

    The economic screen still sees a confirmed unit in the years before its date,
    so a sustained-loss unit can exit earlier (``min(economic, confirmed_date)``);
    the confirmed date is a latest-exit ceiling, not a floor (rule 19: exogenous
    legal exit vs endogenous economic exit are distinct phenomena).

    Args:
        fleet: The fleet entering the year.
        year: The simulation year being entered.
        exits: Confirmed exits for this ISO
            (:func:`market_sim.data.confirmed_retirements.load_confirmed_exits`).
        apply_backlog: When ``True``, select every exit effective at or before
            ``year`` (the pre-start backlog, first-simulated-year use only).
            When ``False`` (default), select only exits effective exactly in
            ``year`` — the once-only per-year event semantics.

    Returns:
        A new fleet list with confirmed exits removed / derated. Byte-identical
        to ``fleet`` when no exit is effective this year.
    """
    if apply_backlog:
        effective = [e for e in exits if _confirmed_effective_year(e) <= year]
    else:
        effective = [e for e in exits if _confirmed_effective_year(e) == year]
    if not effective:
        return list(fleet)

    exit_mw_by_plant: dict[int, float] = {}
    exit_gids_by_plant: dict[int, set[str]] = {}
    exit_month_by_plant: dict[int, int | None] = {}
    for e in effective:
        exit_mw_by_plant[e.plant_id] = exit_mw_by_plant.get(e.plant_id, 0.0) + (
            e.mw or 0.0
        )
        exit_gids_by_plant.setdefault(e.plant_id, set()).add(str(e.generator_id))
        # Track the earliest exit_month (in case multiple units exit in different months).
        if e.plant_id not in exit_month_by_plant:
            exit_month_by_plant[e.plant_id] = e.exit_month
        elif e.exit_month is not None and (
            exit_month_by_plant[e.plant_id] is None
            or e.exit_month < exit_month_by_plant[e.plant_id]
        ):
            exit_month_by_plant[e.plant_id] = e.exit_month

    # Per exit-plant total binned MW (the derate denominator), computed once.
    binned_mw_by_plant: dict[int, float] = {}
    for g in fleet:
        pc = int(g.plant_code)
        if pc in exit_mw_by_plant and _is_confirmed_binned(g):
            binned_mw_by_plant[pc] = binned_mw_by_plant.get(pc, 0.0) + g.pmax_mw

    kept: list[Generator] = []
    for g in fleet:
        pc = int(g.plant_code)
        if pc not in exit_mw_by_plant:
            kept.append(g)
            continue
        if _is_confirmed_binned(g):
            binned_mw = binned_mw_by_plant.get(pc, 0.0)
            exit_mw = exit_mw_by_plant[pc]
            if binned_mw <= 0.0 or exit_mw <= 0.0:
                # No usable MW to derate against (registry left capacity_mw
                # blank): keep the tranche rather than over-retire the plant.
                if exit_mw <= 0.0:
                    logger.warning(
                        "confirmed-exit: plant %d has no capacity_mw to derate "
                        "binned tranches; kept intact",
                        pc,
                    )
                kept.append(g)
                continue
            # Calculate derate factor, accounting for month-level precision.
            # If exit_month <= 6 and we're applying in the exit year, compute
            # annual-average: available for exit_month months, retired for the rest.
            exit_month = exit_month_by_plant.get(pc)
            if (
                exit_month is not None
                and exit_month <= 6
                and _confirmed_effective_year(
                    ConfirmedExit(
                        plant_id=pc,
                        generator_id="",
                        exit_year=year,
                        exit_month=exit_month,
                    )
                )
                == year
            ):
                # Annual-average derate accounting for month-level precision:
                # exit_month months at full capacity + (12 - exit_month) months at reduced capacity
                months_retired = 12 - exit_month
                reduced_factor = max(0.0, (binned_mw - exit_mw) / binned_mw)
                factor = (exit_month / 12.0) * 1.0 + (
                    months_retired / 12.0
                ) * reduced_factor
            else:
                # Full-year derate (exit_month > 6 effective next year, or no exit_month).
                factor = max(0.0, (binned_mw - exit_mw) / binned_mw)
            derated = _derate_generator(g, factor)
            if derated.pmax_mw > _CONFIRMED_EXIT_MW_EPS:
                kept.append(derated)
            # else: fully retired by the confirmed exit (dropped).
        else:
            gid = _unit_generator_id(g)
            if gid is not None and gid in exit_gids_by_plant[pc]:
                continue  # unit-grain confirmed exit: drop
            kept.append(g)
    return kept


def _is_confirmed_binned(gen: Generator) -> bool:
    """Whether a confirmed exit derates (vs unit-drops) this generator.

    A CAMPD/synthesized bin (``is_campd_bin``) or any generator whose
    ``unit_id`` is not the raw ``"{plant_code}_{generator_id}"`` form is treated
    as plant-binned: the confirmed exit derates its MW rather than dropping a
    single unit.
    """
    return gen.is_campd_bin or _unit_generator_id(gen) is None


def _derate_generator(gen: Generator, factor: float) -> Generator:
    """Return a copy of ``gen`` with its MW-valued fields scaled by ``factor``.

    Scales the capacity and every MW-denominated floor (pmax, pmin, bin
    nameplate, CHP steam floor, coal-sync floor) so a plant-binned generator
    shrinks by the confirmed-exit fraction while its per-unit rates, fractions
    and commitment parameters (heat rate, must-run %, min-run/down) are
    unchanged.
    """
    return gen.model_copy(
        update={
            "pmax_mw": gen.pmax_mw * factor,
            "pmin_mw": gen.pmin_mw * factor,
            "bin_nameplate_mw": gen.bin_nameplate_mw * factor,
            "chp_grid_pmin_mw": gen.chp_grid_pmin_mw * factor,
            "coal_sync_pmin_mw": gen.coal_sync_pmin_mw * factor,
        }
    )


def apply_announced_retirements(
    fleet: list[Generator],
    year: int,
    fossil_economic: bool = True,
    *,
    vintage: int = EIA860_OPERABLE_VINTAGE,
    horizon_years: int | None = None,
    confirmed_plant_codes: frozenset[int] = frozenset(),
    reversed_plant_codes: frozenset[int] = frozenset(),
) -> list[Generator]:
    """Return the fleet with ANNOUNCED (EIA-860 date) retirements applied.

    A generator retires once the simulation year reaches its
    ``retirement_year``; units with no scheduled year are always kept. This is
    the *announced* channel — an EIA-860 self-reported planned date, not a
    binding instrument (that is the confirmed channel,
    :func:`apply_confirmed_exits`, which runs first).

    **Fossil default no-op (RC-3).** When ``fossil_economic`` is ``True`` (the
    forecast default), units of a :data:`_FOSSIL_FUELS` type are **exempt** from
    this date-based retirement: an announced fossil date is an announcement, not
    a certainty, so their phaseout is left to the economic-retirement screen
    (:func:`apply_economic_retirements`) and the exogenous fossil exit channel is
    the confirmed registry. For the whole fossil fleet this step is a default
    no-op. Set ``fossil_economic=False`` to honor every scheduled fossil date
    (the legacy behaviour).

    **Non-fossil data-horizon gate (RC-5).** A non-fossil announced date
    (nuclear/hydro/renewables/storage) is honored deterministically only within
    the EIA-860 data horizon: ``retirement_year <= vintage + horizon_years``.
    Beyond the horizon the date is honored **only if** the unit's plant is in
    ``confirmed_plant_codes`` (a binding instrument in the confirmed registry);
    otherwise it is ignored, so speculative 2040-2072 hydro-relicense / solar-EOL
    placeholders stop force-retiring and far-dated nuclear announcements fall to
    the economic screen. ``horizon_years=None`` (the default and the legacy
    behaviour) disables the gate — every non-fossil announced date is honored, as
    before the confirmed-retirement channel existed.

    Args:
        fleet: The current generator fleet.
        year: The simulation year being evaluated.
        fossil_economic: When ``True``, fossil units ignore their scheduled
            ``retirement_year`` (economic screen governs them).
        vintage: EIA-860 operable-snapshot vintage the horizon is measured from.
        horizon_years: Data-horizon width for honoring non-fossil announced
            dates; ``None`` disables the gate (honor all non-fossil dates).
        confirmed_plant_codes: Plant codes carrying a binding instrument in the
            confirmed registry — a beyond-horizon non-fossil date is honored only
            for these.
        reversed_plant_codes: Plant codes whose announced retirement was
            **reversed** by a public counter-instrument (every registry row
            superseded, none live —
            :func:`market_sim.data.confirmed_retirements.load_announced_reversal_plants`).
            Their announced dates are ignored, any fuel: the date the vintage
            EIA-860 carries records a cancelled plan (Byron/Dresden's 2021
            dates reversed by IL CEJA), so executing it false-retires a
            running plant. The unit stays with the economic screen (and the
            confirmed channel, should a new instrument land).

    Returns:
        A new list excluding generators whose announced retirement is honored
        this year.
    """
    keep: list[Generator] = []
    for g in fleet:
        r = g.retirement_year
        if r is None or r > year:
            keep.append(g)
            continue
        if int(g.plant_code) in reversed_plant_codes:
            # Retirement-reversal supersession: a counter-instrument (statute,
            # RMR, 202(c), withdrawal) cancelled this plant's announced exit —
            # the date is stale vintage data, not a plan. Economic screen
            # governs.
            keep.append(g)
            continue
        is_fossil = g.fuel_type in _FOSSIL_FUELS
        if fossil_economic and is_fossil:
            keep.append(g)  # economic screen governs fossil phaseout (no-op)
            continue
        if not is_fossil and horizon_years is not None:
            within_horizon = r <= vintage + horizon_years
            confirmed = int(g.plant_code) in confirmed_plant_codes
            if not within_horizon and not confirmed:
                keep.append(g)  # beyond-horizon speculative placeholder: ignore
                continue
        # Honor the announced date: unit is dropped.
    return keep


def compute_clean_share(
    fleet: list[Generator],
    renewable_cap_mw: float = 0.0,
) -> float:
    """Return the clean-capacity fraction of the fleet.

    Clean capacity includes wind, solar, nuclear and hydro Generators
    in the fleet PLUS any separately-tracked renewable capacity from
    the zonal wind_cap/solar_cap pools.
    """
    total = sum(g.pmax_mw for g in fleet) + renewable_cap_mw
    if total <= 0.0:
        return 0.0
    clean = sum(g.pmax_mw for g in fleet if g.fuel_type in _CLEAN_FUELS)
    clean += renewable_cap_mw
    return clean / total


def _dispatch_rows(gen: Generator, idx_of: dict[str, int]) -> list[int]:
    """Return the fleet-array row indices for a generator.

    Most generators occupy a single dispatch row. Coal bins are split into
    take-or-pay tranches (``{unit_id}_t1``..``_t3``) before dispatch, so a
    coal generator maps to all its tranche rows; revenue is summed over them.
    """
    direct = idx_of.get(gen.unit_id)
    if direct is not None:
        return [direct]
    if gen.fuel_type == "coal":
        return [
            idx_of[key] for t in (1, 2, 3) if (key := f"{gen.unit_id}_t{t}") in idx_of
        ]
    return []


def capacity_revenue_per_mw_yr(
    iso: str,
    fuel_type: str,
    eford: float,
    config: ScenarioConfig | None = None,
    reserve_position: float | None = None,
    year: int | None = None,
) -> float:
    """Return the resource-adequacy capacity payment in $/MW-yr (Module M1).

    In a capacity-market ISO a thermal unit earns a payment on its
    accredited capacity *outside* the energy market, which can keep it
    solvent even on a negative energy margin. The payment is the shared
    per-firm-MW capacity price (rule 19 — one seam for all three screens)
    times the unit's **basis-resolved accreditation fraction** — the SAME
    resolver the adequacy ledger prices the unit's firm MW through
    (:func:`thermal_accreditation_fraction`), so the ledger and the payment
    can never diverge (R4, accreditation-basis memo 2026-07-12 §4.2)::

        $/MW-yr = capacity_price_per_firm_mw_yr(...) * accreditation_fraction

    The accreditation fraction is the ISO's own published basis: ``1 - EFORd``
    (UCAP, the default for NYISO/ISO-NE/MISO), the published ELCC class rating
    (PJM's 2025/26 CIFP reform — replaces the hardcoded ``1 - EFORd`` this
    call used before R4), or nameplate (ERCOT's seasonal-rating basis, though
    ERCOT is energy-only so it never reaches the payment). Because it is the
    ledger's own resolver, a class differential (e.g. PJM gas-CT 0.60 vs its
    0.94 UCAP) is now paid on the same basis it is counted on.

    The price itself is :meth:`MarketDesign.capacity_price_per_firm_mw_yr`,
    which is the flat net-CONE (default) or — when the clearing gate resolves
    ON for this ISO (:func:`resolve_capacity_market_clearing`: the per-ISO
    ``capacity_market_clearing_by_iso`` row when present, else the scalar
    ``capacity_market_clearing``), the ISO has a published demand curve, and
    ``reserve_position`` (accredited firm ÷ requirement) is supplied — the
    CR-1 sloped-curve price ``VRR(reserve_position) × net_cone_curve``.
    ``iso`` and ``year`` are threaded into the seam so the per-ISO gate and
    the per-delivery-year vintage anchor (RC-1B items 1/2,
    :func:`resolve_demand_curve_vintage`) govern inside the curve branch; both
    are consulted ONLY there, so every gate-off path — and passing neither
    ``config`` nor ``reserve_position`` — reproduces the pre-CR-1 fixed price
    byte-identically.

    Energy-only ISOs (ERCOT, and any ISO absent from the registry) have
    ``capacity_market = False`` and earn zero here in both modes, so their
    retirement and new-entry economics are unchanged.
    """
    design = MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN)
    price = design.capacity_price_per_firm_mw_yr(
        config, reserve_position, iso=iso, year=year
    )
    if price <= 0.0:
        return 0.0
    accredited = max(0.0, thermal_accreditation_fraction(fuel_type, eford, iso))
    return price * accredited


# A zone whose deliverable firm capacity exceeds its locational requirement by
# more than this fraction is treated as RA-saturated (the marginal capacity
# payment there collapses). Small positive band so a zone sitting exactly at its
# requirement still earns the full capacity payment. Structural gate, not a
# fitted lever — see ScenarioConfig.capacity_deliverability_limits.
_DELIVERABILITY_LONG_BAND: float = 0.0


def deliverability_headroom_by_zone(
    iso: str,
    year: int,
    fleet: list[Generator],
    config: ScenarioConfig,
    wind_pool_by_zone: dict[str, float] | None = None,
    solar_pool_by_zone: dict[str, float] | None = None,
    storage_firm_by_zone: dict[str, float] | None = None,
) -> dict[str, float]:
    """Return ``{zone: deliverable_firm_MW - requirement_MW}`` per model zone.

    The locational adequacy signal behind
    ``config.capacity_deliverability_limits``. For each model zone that carries a
    published capacity *requirement* (crosswalked from the ISO's LDA/LRZ/
    locality/local-area rows), the deliverable firm capacity is the accredited
    (ELCC/UCAP) capacity physically in the zone plus the crosswalked
    *import_limit* into it. A positive headroom means the zone is **long** (RA
    already met, so the next unit's capacity payment should collapse); a negative
    headroom means the zone is **short** (locational need).

    Returns an empty dict — a total no-op — when the flag is off, the ISO has no
    clean partition, or no zone carries a requirement, so callers gate cleanly.

    Args:
        iso: Model ISO name.
        year: Model calendar year (resolved to the ISO's delivery-year label).
        fleet: Current generator fleet; each unit's zone and accreditation
            (``RENEWABLE_CAPACITY_CREDIT`` or ``1 - EFORd``) feed the firm sum.
        config: Scenario config (the flag lives here).
        wind_pool_by_zone, solar_pool_by_zone: Zonal renewable pool MW (bounds of
            the ``W``/``S`` dispatch variables), credited at their capacity
            credit. Optional.
        storage_firm_by_zone: Pre-accredited storage ELCC MW per zone. Optional.

    Returns:
        ``{zone: headroom_MW}`` over the zones that carry a requirement.
    """
    if not config.capacity_deliverability_limits:
        return {}
    delivery_year = capdel.resolve_delivery_year(iso, year)
    season = capdel.resolve_season(iso)
    req_area = capdel.requirement_by_area(iso, delivery_year, season)
    if not req_area:
        return {}
    imp_area = capdel.import_limit_by_area(iso, delivery_year, season)
    req_types = capdel.area_types_by_area(iso, delivery_year, season, "requirement")
    imp_types = capdel.area_types_by_area(iso, delivery_year, season, "import_limit")

    req_by_zone, _ = aggregate_by_zone(iso, req_area, req_types)
    imp_by_zone, _ = aggregate_by_zone(iso, imp_area, imp_types)

    # Accredited firm capacity physically in each zone, from the fleet plus the
    # zonal renewable pools and any pre-accredited storage ELCC.
    firm_by_zone: dict[str, float] = {}
    for g in fleet:
        credit = RENEWABLE_CAPACITY_CREDIT.get(g.fuel_type)
        accredited = g.pmax_mw * (
            credit if credit is not None else 1.0 - float(g.eford)
        )
        firm_by_zone[g.zone] = firm_by_zone.get(g.zone, 0.0) + accredited
    for zone, mw in (wind_pool_by_zone or {}).items():
        firm_by_zone[zone] = (
            firm_by_zone.get(zone, 0.0) + mw * RENEWABLE_CAPACITY_CREDIT["wind"]
        )
    for zone, mw in (solar_pool_by_zone or {}).items():
        firm_by_zone[zone] = (
            firm_by_zone.get(zone, 0.0) + mw * RENEWABLE_CAPACITY_CREDIT["solar"]
        )
    for zone, mw in (storage_firm_by_zone or {}).items():
        firm_by_zone[zone] = firm_by_zone.get(zone, 0.0) + mw

    headroom: dict[str, float] = {}
    for zone, requirement in req_by_zone.items():
        deliverable = firm_by_zone.get(zone, 0.0) + imp_by_zone.get(zone, 0.0)
        headroom[zone] = deliverable - requirement
    return headroom


def _zone_is_long(headroom: dict[str, float] | None, zone: str) -> bool:
    """Whether ``zone`` is RA-saturated (deliverable clears requirement).

    ``None``/empty headroom (flag off or no data) is never long, so the capacity
    payment is untouched — the gate is a strict no-op unless the mechanism is on
    and the zone actually carries a satisfied requirement.
    """
    if not headroom or zone not in headroom:
        return False
    requirement_scale = abs(headroom[zone]) + 1.0
    return headroom[zone] > _DELIVERABILITY_LONG_BAND * requirement_scale


def resolve_planning_reserve_margin(config: ScenarioConfig, iso: str) -> float:
    """Return the planning reserve margin shared by the floor and the backstop.

    One requirement, two verbs (capacity-economics plan 2026-07 §3.2): the
    retirement reliability floor ("don't retire below") and the reserve-margin
    build backstop ("build up to") test the same published adequacy target.
    ``config.planning_reserve_margin_override`` (a registered sensitivity
    lever) takes precedence; otherwise the ISO's published PRM from
    :data:`PLANNING_RESERVE_MARGIN_BY_ISO`, falling back to the
    ``config.planning_reserve_margin`` scalar for ISOs absent from the
    registry.
    """
    if config.planning_reserve_margin_override is not None:
        return float(config.planning_reserve_margin_override)
    return PLANNING_RESERVE_MARGIN_BY_ISO.get(iso, config.planning_reserve_margin)


def _storage_portfolio_elcc_dilution(existing_storage_mw: float, iso: str) -> float:
    """Return the portfolio-accreditation ELCC dilution factor for storage.

    The CDR's own reported fleet-average BESS ELCC compresses as storage
    penetration grows (ERCOT accreditation audit 2026-07-06 §3: "60% -> 46%
    by 2030 as penetration triples"), a phenomenon the per-duration
    ``STORAGE_ELCC_BY_DURATION`` table (a fixed duration -> credit curve)
    cannot express on its own. The model has exactly two cited (penetration,
    ELCC) data points — today's validated level
    (:data:`STORAGE_ELCC_DILUTION_REFERENCE_MW_BY_ISO`, factor 1.0, "close at
    fleet level today") and the CDR's own ratio at full deployment-ceiling
    penetration (:data:`STORAGE_ELCC_DILUTION_CEILING_RATIO_BY_ISO`,
    46 %/60.2 %) — so the dilution is a straight LINE between them, not a
    fitted curve: no exponent is invented, and no intermediate MW is guessed
    for "2030". Below the reference MW the factor is clamped at 1.0 (no
    bonus for less storage than today); at or above the ceiling it is
    clamped at the CDR ratio. ISOs absent from either registry return 1.0
    (byte-identical, conservative default).
    """
    reference_mw = STORAGE_ELCC_DILUTION_REFERENCE_MW_BY_ISO.get(iso)
    ceiling_ratio = STORAGE_ELCC_DILUTION_CEILING_RATIO_BY_ISO.get(iso)
    ceiling_mw = STORAGE_DEPLOYMENT_CEILING_MW.get(iso, 0.0)
    if reference_mw is None or ceiling_ratio is None or ceiling_mw <= reference_mw:
        return 1.0
    existing_storage_mw = max(0.0, existing_storage_mw)
    if existing_storage_mw <= reference_mw:
        return 1.0
    if existing_storage_mw >= ceiling_mw:
        return ceiling_ratio
    span_fraction = (existing_storage_mw - reference_mw) / (ceiling_mw - reference_mw)
    return 1.0 - (1.0 - ceiling_ratio) * span_fraction


def resolve_forecast_pool_requirement(iso: str, year: int | None) -> float | None:
    """Return the ISO's published Forecast Pool Requirement for ``year``, or None.

    PJM (post-CIFP) publishes a Forecast Pool Requirement (FPR) — the
    reliability requirement stated on its OWN UCAP basis as a fraction of
    forecast peak load, with the reserve margin AND the ICAP->UCAP conversion
    already folded in (FPR = (1 + IRM) x Reference-Resource Accredited-UCAP
    factor). Resolves ``year`` to the ISO's delivery-year label
    (:func:`capdel.resolve_delivery_year`) and returns the published FPR from
    :data:`FORECAST_POOL_REQUIREMENT_BY_ISO` for that exact delivery year, or
    ``None`` when the ISO/year has no published FPR (caller falls back to the
    ``(1 + PRM) x ratio`` construction). ``year=None`` returns ``None`` so a
    caller that cannot resolve a delivery year keeps the fallback path
    byte-identically (R2, accreditation-basis memo 2026-07-12 §4.2).
    """
    if year is None:
        return None
    table = FORECAST_POOL_REQUIREMENT_BY_ISO.get(iso)
    if not table:
        return None
    return table.get(capdel.resolve_delivery_year(iso, year))


def resolve_adequacy_requirement_mw(
    config: ScenarioConfig, iso: str, peak_demand_mw: float, year: int | None = None
) -> float:
    """Return the firm-capacity requirement shared by the floor and backstop.

    Two constructions, in preference order (R2, accreditation-basis memo
    2026-07-12 §4.2 — "resolve the requirement from the published FPR of the
    matching delivery year; fall back to ``(1 + PRM) x ratio`` otherwise"):

    1. **Published Forecast Pool Requirement.** When ``year`` resolves to a
       delivery year the ISO publishes an FPR for
       (:func:`resolve_forecast_pool_requirement`), the requirement is
       ``firm_peak x FPR`` — the ISO's own UCAP-basis requirement, with the
       reserve margin and the ICAP->UCAP conversion already folded into the
       one published number. This is literally the ISO's own construction
       (devintages the mixed-vintage ``1.178 x 0.7699 = 0.907`` composite the
       fallback builds onto the published 2026/2027 FPR ``0.9170``).
    2. **Fallback ``firm peak x (1 + PRM_iso) x icap_to_ucap_ratio_iso``**
       (byte-identical to the pre-R2 behaviour) for any ISO/year without a
       published FPR. The ``icap_to_ucap_ratio`` factor (stage-5 §6 ICAP/UCAP
       pairing audit, 2026-07-06) corrects a basis mismatch for ISOs whose
       registered PRM is stated on INSTALLED capacity (PJM's IRM, MISO's
       ICAP-basis PRM) while :func:`accredited_firm_capacity_mw` counts their
       thermal fleet at UCAP; it is each ISO's own published ICAP<->UCAP
       conversion (:data:`PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO`),
       defaulting to 1.0 for ISOs absent from that registry.

    In both constructions the firm peak nets the ISO's demand-response
    capacity products out of the gross peak
    (:data:`ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO`; ISOs absent net
    nothing). For ERCOT the netting IS the ISO's own construction (the CDR's
    "Firm Peak Load"); for PJM — whose own construct counts DR as supply-side
    UCAP — the registry value is reconciled so the netting reproduces PJM's
    supply-side counting exactly under the published-FPR path (rule 14; see
    the registry's citation comment).
    One requirement, two verbs (capacity-economics plan §3.2) — both adequacy
    mechanisms call this. ``year=None`` keeps the fallback path, so a caller
    that does not thread a year is byte-identical to the pre-R2 behaviour.
    """
    dr_fraction = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO.get(iso, 0.0)
    firm_peak_mw = peak_demand_mw * (1.0 - dr_fraction)
    fpr = resolve_forecast_pool_requirement(iso, year)
    if fpr is not None:
        return firm_peak_mw * fpr
    icap_to_ucap_ratio = PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO.get(iso, 1.0)
    return (
        firm_peak_mw
        * (1.0 + resolve_planning_reserve_margin(config, iso))
        * icap_to_ucap_ratio
    )


def thermal_accreditation_fraction(
    fuel_type: str, eford: float, iso: str | None
) -> float:
    """Firm fraction of nameplate one dispatchable unit accredits, on the ISO's basis.

    The ONE thermal-accreditation resolver (rule 19): the adequacy ledger
    (:func:`_thermal_firm_mw`), the CR-1 reserve position, and the per-unit
    capacity payment (:func:`capacity_revenue_per_mw_yr`) all price a unit's
    firm fraction through this single function, so the ledger and the payment
    can never diverge by construction. Three published bases
    (:data:`THERMAL_ACCREDITATION_BASIS_BY_ISO`):

    * ``"seasonal_rating"`` (ERCOT CDR): nameplate, no forced-outage derate
      — returns ``1.0`` (outage risk lives in the target margin).
    * ``"claimed_capability"`` (ISO-NE FCM): the 5-yr median Seasonal Claimed
      Capability (Qualified Capacity), no forced-outage derate — returns
      ``1.0`` (outage risk is priced ex post through Pay-for-Performance, not
      the accredited MW). Numerically identical to ``"seasonal_rating"`` but a
      distinct basis by design — the *reason* differs (R5b).
    * ``"elcc_class_rating"`` (PJM's 2025/26 CIFP reform): the unit's
      published ELCC class rating
      (:data:`THERMAL_ELCC_CLASS_RATING_BY_ISO`), falling back to UCAP for a
      fuel class the ISO does not publish (rule 25 neutral fallback).
    * default / absent (``"ucap"``): ``1 - EFORd``.

    ``iso=None`` keeps the legacy UCAP basis byte-identically.
    """
    basis = THERMAL_ACCREDITATION_BASIS_BY_ISO.get(iso or "")
    if basis == "seasonal_rating":
        return 1.0
    if basis == "claimed_capability":
        # ISO-NE Qualified Capacity is the SCC median with no (1-EFORd) derate;
        # forced-outage risk is priced ex post via Pay-for-Performance, not the
        # accredited MW (R5b, pairing-adjudication 2026-07-15 §1). Class-agnostic
        # — QC is a per-unit SCC median, so there is no fuel-class ELCC table.
        return 1.0
    if basis == "elcc_class_rating":
        rating = THERMAL_ELCC_CLASS_RATING_BY_ISO.get(iso or "", {}).get(fuel_type)
        if rating is not None:
            return float(rating)
    return 1.0 - float(eford)


def _thermal_firm_mw(g: Generator, iso: str | None) -> float:
    """Firm MW one dispatchable unit contributes to the adequacy ledger.

    ``pmax`` times the unit's basis-resolved accreditation fraction
    (:func:`thermal_accreditation_fraction` —
    :data:`THERMAL_ACCREDITATION_BASIS_BY_ISO`). ``iso=None`` keeps the legacy
    UCAP basis.
    """
    return float(g.pmax_mw) * thermal_accreditation_fraction(g.fuel_type, g.eford, iso)


def _renewable_credit(fuel_type: str, iso: str | None) -> float | None:
    """Resolve a VRE/hydro capacity credit, per-ISO override first.

    Returns ``None`` for fuels that are not credit-accredited (thermal),
    mirroring ``RENEWABLE_CAPACITY_CREDIT.get``. An ISO with a published
    accreditation (:data:`RENEWABLE_CAPACITY_CREDIT_BY_ISO`) wins over the
    generic fallback for exactly the fuels it publishes. This is the
    POINT-basis ladder — the penetration-indexed curve layer sits above it
    in :func:`resolve_renewable_capacity_credit`.
    """
    if iso is not None:
        override = RENEWABLE_CAPACITY_CREDIT_BY_ISO.get(iso)
        if override is not None and fuel_type in override:
            return override[fuel_type]
    return RENEWABLE_CAPACITY_CREDIT.get(fuel_type)


def resolve_renewable_capacity_credit(
    fuel_type: str,
    iso: str | None,
    installed_mw: float | None = None,
    peak_demand_mw: float | None = None,
    curves_enabled: bool = False,
) -> float | None:
    """Resolve one VRE class's adequacy capacity credit (CR-3.1 ladder).

    The ONE resolver every adequacy consumer prices VRE accreditation
    through (rule 19): :func:`accredited_firm_capacity_mw` and, through it,
    the retirement reliability floor, the reserve-margin backstop and the
    CR-1 reserve position all move together. Resolution ladder:

    1. **Published penetration-indexed ELCC curve**
       (:data:`RENEWABLE_ELCC_CURVES_BY_ISO`, gate
       ``ScenarioConfig.renewable_elcc_curves``) evaluated at the model's
       own installed share — ``installed_mw`` is the class's ISO-wide
       nameplate (pools + fleet units), ``peak_demand_mw`` the system peak
       for pct-of-peak curves. The credit therefore falls (or moves) as the
       MODEL builds, regenerating forward with zero fitted parameters
       (rule 13).
    2. **Published single-point per-ISO override**
       (:data:`RENEWABLE_CAPACITY_CREDIT_BY_ISO` — ERCOT's CDR basis).
    3. **Generic flat fallback** (:data:`RENEWABLE_CAPACITY_CREDIT`) for
       ISOs/classes with no published accreditation (cited neutral
       fallback, rule 25 spirit).

    ``curves_enabled=False`` (the frozen-penetration byte-compat mode) or a
    curve whose axis quantity is unavailable falls through to steps 2-3,
    reproducing the pre-CR-3.1 behaviour byte-identically. Returns ``None``
    for fuels that are not credit-accredited (thermal), mirroring
    ``RENEWABLE_CAPACITY_CREDIT.get``.
    """
    if curves_enabled and iso is not None:
        curve = RENEWABLE_ELCC_CURVES_BY_ISO.get(iso, {}).get(fuel_type)
        if curve is not None:
            credit = evaluate_renewable_elcc_curve(curve, installed_mw, peak_demand_mw)
            if credit is not None:
                return credit
    return _renewable_credit(fuel_type, iso)


def _floor_retention_merit(
    config: ScenarioConfig, g: Generator
) -> tuple[float, float, float]:
    """Return the reliability-floor retention sort key for one eligible unit.

    Cheapest firm adequacy first: annual going-forward cost per firm MW (the
    ISO's accreditation basis — UCAP by default, seasonal rating where the
    ISO's published convention says so, ``_thermal_firm_mw``), tie-broken by
    CO2 emission rate ascending so equal-cost adequacy is bought from the
    cleaner unit (the heat-rate key this replaces retained coal over gas),
    then by heat rate ascending so a within-fuel tie (per-fuel FOM and CO2
    rates make same-fuel units identical on the first two keys)
    deterministically retains the most efficient unit. All three keys are
    physical unit attributes — no tunables (plan §3.2).
    """
    fom_field = _THERMAL_FOM[g.fuel_type]
    multiplier = getattr(config, _FOM_MULTIPLIER.get(g.fuel_type, ""), 1.0)
    going_forward_cost = getattr(config, fom_field) * multiplier * g.pmax_mw * 1000.0
    firm_mw = _thermal_firm_mw(g, config.iso)
    cost_per_firm_mw = going_forward_cost / firm_mw if firm_mw > 0.0 else math.inf
    return (cost_per_firm_mw, float(g.emission_rate_co2), float(g.heat_rate))


def _apply_reliability_floor(
    fleet: list[Generator],
    eligible: list[Generator],
    retired: set[str],
    loss_years: dict[str, int],
    config: ScenarioConfig,
    peak_demand: float,
    wind_pool_mw: float,
    solar_pool_mw: float,
    storage_firm_mw: float,
    deliverability_headroom: dict[str, float] | None,
    year: int | None,
) -> list[dict]:
    """Un-retire eligible units until accredited firm capacity clears the PRM.

    The retirement-side verb of the shared adequacy requirement (plan §3.2):
    :func:`resolve_adequacy_requirement_mw` (firm peak × (1 + PRM_iso), on
    the ISO's own published counting convention) tested against
    :func:`accredited_firm_capacity_mw` of the surviving fleet plus the zonal
    renewable pools and pre-accredited storage ELCC — the same ledger the
    step-6 build backstop uses, replacing the old raw-nameplate /
    hydro-netting test. Only *un-retires* (mutates ``retired`` in place); it
    never retires anything. Retention order is
    :func:`_floor_retention_merit` ($/firm-MW-yr ascending, CO2 tie-break).
    Units in RA-saturated zones (``deliverability_headroom`` long — only
    populated under ``capacity_deliverability_limits``) are exempt from
    retention: a zone already clearing its locational requirement does not
    buy adequacy there.

    Returns the floor-retention attribution log (rule 20 analogue): one dict
    per retained unit with the unit's identity, firm value, cost and CO2 rate,
    so floor-retained MW is measurable per run instead of argued. The
    ``ucap_mw`` field carries the unit's firm MW on the ISO's accreditation
    basis (equal to nameplate for seasonal-rating ISOs).

    Market-design fidelity gate (``config.market_design_retirement_floor``,
    GATED default off — fom-scarcity stage 5 §1): when on, an ISO explicitly
    registered energy-only (``MARKET_DESIGN[iso].capacity_market == False``,
    ERCOT) skips the floor entirely — the real energy-only market has no
    reliability floor; an under-remunerated unit exits and adequacy expresses
    as ORDC-priced scarcity revenue that retains the marginal survivor. ISOs
    with a capacity market keep the floor (their design really does procure to
    the requirement), and ISOs absent from :data:`MARKET_DESIGN` keep it too
    (conservative fallback — the registry default withholds capacity
    *revenue* for unknown ISOs, which must not double as asserting their
    market design). The default-off reserve-margin build backstop is
    unaffected and remains the modeling-safety valve.
    """
    if peak_demand <= 0.0:
        return []
    if getattr(config, "market_design_retirement_floor", False):
        design = MARKET_DESIGN.get(config.iso)
        if design is not None and not design.capacity_market:
            return []
    requirement_mw = resolve_adequacy_requirement_mw(
        config, config.iso, peak_demand, year
    )
    survivors = [g for g in fleet if g.unit_id not in retired]
    accredited_mw = accredited_firm_capacity_mw(
        survivors,
        wind_pool_mw,
        solar_pool_mw,
        storage_firm_mw,
        iso=config.iso,
        peak_demand_mw=peak_demand,
        elcc_curves_enabled=config.renewable_elcc_curves,
    )
    retention_log: list[dict] = []
    if accredited_mw >= requirement_mw:
        return retention_log
    for g in sorted(eligible, key=lambda g: _floor_retention_merit(config, g)):
        if accredited_mw >= requirement_mw:
            break
        if g.unit_id not in retired:
            continue
        if _zone_is_long(deliverability_headroom, g.zone):
            continue  # RA-saturated zone: no adequacy value in retaining here
        retired.discard(g.unit_id)
        firm_mw = _thermal_firm_mw(g, config.iso)
        accredited_mw += firm_mw
        cost_per_firm_mw, co2_rate, _hr = _floor_retention_merit(config, g)
        retention_log.append(
            {
                "year": year,
                "unit_id": g.unit_id,
                "fuel_type": g.fuel_type,
                "pmax_mw": float(g.pmax_mw),
                "ucap_mw": float(firm_mw),
                "going_forward_cost": float(cost_per_firm_mw * firm_mw),
                "co2_rate": float(co2_rate),
                "loss_years": int(loss_years.get(g.unit_id, 0)),
            }
        )
    return retention_log


def _apply_pipeline_retirements(
    fleet: list[Generator],
    margins: list[tuple["Generator", float, float]],
    pipeline_state: dict[str, int],
    config: ScenarioConfig,
    peak_demand: float,
    wind_pool_mw: float,
    solar_pool_mw: float,
    storage_firm_mw: float,
    deliverability_headroom: dict[str, float] | None,
    year: int,
    event_sink: dict | None,
) -> tuple[list[Generator], dict[str, int], list[dict]]:
    """R-NEW decision/execution retirement pipeline (``retirement_rule="pipeline"``).

    The FF-0C §3.6 composite rule (owner D1 = Option B, 2026-07-17;
    ``docs/handoffs/ff-retirement-rule-redesign-2026-07.md``), replacing the
    legacy per-fuel consecutive-loss counters whose threshold inversion
    RC-1A-D1 measured. Six components, zero newly tuned parameters:

    1. **Uniform decision.** A unit whose attainable margin fails the
       identical ``net_revenue < going_forward_cost`` bar at ONE annual
       screen becomes DECIDED (decision persistence D = 0, an open DOF held
       by parsimony — the flat-expectation degenerate NPV form, §3.1). No
       per-fuel decision threshold exists.
    2. **Joint pipeline-entry competition.** All newly failing units across
       ALL fuels compete in the same year, considered worst-first by margin
       depth ($/kW-yr shortfall, §3.3). Admission is capped by the EXISTING
       accredited-adequacy requirement evaluated on the schedule of pending
       exits: :func:`_apply_reliability_floor` (the floor's own machinery
       and cheapest-firm-adequacy metric) retains candidates until the
       scheduled post-pipeline firm capacity clears the shared PRM
       requirement. Removes the D1 defects 2 and 3 (the cross-fuel race and
       the fuel-partitioned eligible set).
    3. **Soft latch.** A pipelined unit is re-screened annually and leaves
       the pipeline ONLY by re-clearing the same bar (economic recovery; the
       policy-rescue reversal channel stays the confirmed registry's). No
       band, no new parameter — one good year no longer erases the distress
       history unless it actually restores viability.
    4. **Execution after the identified lag.** A unit still pipelined at
       ``decided_year + L_f`` deactivates then (``L_f`` = the RC-0B §a.3
       measured per-fuel announcement→deactivation medians,
       ``retirement_execution_lag_*``). It dispatches normally until then,
       as real announced-but-operating units do. ``decided_year`` is the
       LOSS year (the year whose dispatch failed = ``year - 1`` at screen
       time), so a persistent-loss coal cohort (L=3) is decided end of loss
       year ``y`` and gone at the start of ``y + 3`` — byte-equivalent
       timing to the adopted legacy D1=3 counter.
    5. **Reliability floor at execution, unchanged.** The realized-year
       backstop: a floor-retained due unit stays online AND stays pipelined
       (execution deferred, re-latched next year).
    6. **Ledger attribution.** ``event_sink["pipeline_events"]`` records
       decided / re_confirmed / reversed / entry_capped / executed rows with
       years, so recall/false-retire scoring sees the decision and the
       execution separately.

    ``pipeline_state`` maps ``unit_id -> decided_year`` and is threaded
    through the same cross-year seam as the legacy loss counters (the
    ``consecutive_loss_years`` dict); it is not mutated in place. Stale ids
    (units that left the fleet through another channel) are inert and are
    pruned when the unit is gone.

    Returns ``(survivors, pipeline_state, floor_retention_log)`` with the
    same contract as the legacy branch of
    :func:`apply_economic_retirements`.
    """
    state = dict(pipeline_state)
    events: list[dict] = []
    fleet_ids = {g.unit_id for g in fleet}
    # Prune ids that left the fleet via another channel (confirmed exit,
    # retrofit rename, re-aggregation): nothing to execute or reverse.
    for uid in [u for u in state if u not in fleet_ids]:
        state.pop(uid)

    def _event(kind: str, g: Generator, decided: int | None) -> dict:
        row = {
            "event": kind,
            "unit_id": g.unit_id,
            "fuel": g.fuel_type,
            "mw": float(g.pmax_mw),
            "year": int(year),
        }
        if decided is not None:
            row["decided_year"] = int(decided)
            row["execute_year"] = int(decided) + _execution_lag_years(
                config, g.fuel_type
            )
        return row

    # --- Soft latch (component 3): re-screen every pipelined unit at the
    # same bar; a unit that re-clears it leaves the pipeline (reversed).
    candidates: list[tuple[Generator, float]] = []  # (unit, depth $/kW-yr)
    for g, net_revenue, going_forward_cost in margins:
        failing = net_revenue < going_forward_cost
        if g.unit_id in state:
            if failing:
                events.append(_event("re_confirmed", g, state[g.unit_id]))
            else:
                events.append(_event("reversed", g, state.pop(g.unit_id)))
        elif failing:
            depth = (
                (going_forward_cost - net_revenue) / (g.pmax_mw * 1000.0)
                if g.pmax_mw > 0.0
                else 0.0
            )
            candidates.append((g, depth))

    # --- Joint entry competition (components 1-2): worst-first margin depth,
    # deterministic tie-break on unit_id. The uniform decision bar has already
    # fired above; admission is capped by the scheduled-adequacy requirement.
    candidates.sort(key=lambda item: (-item[1], item[0].unit_id))
    new_units = [g for g, _depth in candidates]
    depth_of = {g.unit_id: d for g, d in candidates}
    # Scheduled-exit set: everything pending plus every new candidate; the
    # floor machinery (cheapest-firm-adequacy retention, the EXISTING metric)
    # un-admits new candidates until the scheduled post-pipeline accredited
    # firm capacity clears the shared PRM requirement. Pending units admitted
    # in prior years are not re-litigated here — the realized-year floor
    # below remains their backstop.
    scheduled: set[str] = set(state) | {g.unit_id for g in new_units}
    _apply_reliability_floor(
        fleet,
        new_units,
        scheduled,
        state,
        config,
        peak_demand,
        wind_pool_mw,
        solar_pool_mw,
        storage_firm_mw,
        deliverability_headroom,
        year,
    )
    decided_year = year - 1  # the loss year whose dispatch failed this screen
    for g in new_units:
        if g.unit_id in scheduled:
            state[g.unit_id] = decided_year
            events.append(_event("decided", g, decided_year))
        else:
            row = _event("entry_capped", g, None)
            row["depth_usd_per_kw_yr"] = float(depth_of[g.unit_id])
            events.append(row)

    # --- Execution (component 4): every unit still pipelined at
    # decided_year + L_f deactivates now, then the realized-year reliability
    # floor (component 5, unchanged machinery) retains cheapest-firm-adequacy
    # first. Floor-retained units stay pipelined (execution deferred).
    unit_of = {g.unit_id: g for g in fleet}
    due = [
        unit_of[uid]
        for uid in state
        if year >= state[uid] + _execution_lag_years(config, unit_of[uid].fuel_type)
    ]
    # Deterministic order for the floor's eligible iteration and the ledger.
    due.sort(key=lambda g: (g.fuel_type, -g.heat_rate))
    retired = {g.unit_id for g in due}
    floor_retention_log = _apply_reliability_floor(
        fleet,
        due,
        retired,
        state,
        config,
        peak_demand,
        wind_pool_mw,
        solar_pool_mw,
        storage_firm_mw,
        deliverability_headroom,
        year,
    )
    for g in due:
        if g.unit_id in retired:
            events.append(_event("executed", g, state[g.unit_id]))

    survivors = [g for g in fleet if g.unit_id not in retired]
    for uid in retired:
        state.pop(uid, None)

    if retired:
        logger.info(
            "year %d: R-NEW pipeline executed %d exit(s), %.0f MW "
            "(%d pending, %d entry-capped, %d reversed)",
            year,
            len(retired),
            sum(float(g.pmax_mw) for g in due if g.unit_id in retired),
            len(state),
            sum(1 for e in events if e["event"] == "entry_capped"),
            sum(1 for e in events if e["event"] == "reversed"),
        )
    if event_sink is not None:
        event_sink["pipeline_events"] = events
        event_sink["retired"] = [
            {"unit_id": g.unit_id, "fuel": g.fuel_type, "mw": float(g.pmax_mw)}
            for g in due
            if g.unit_id in retired
        ]
        event_sink["floor_retained"] = [
            {"unit_id": g.unit_id, "fuel": g.fuel_type, "mw": float(g.pmax_mw)}
            for g in due
            if g.unit_id not in retired
        ]
    return survivors, state, floor_retention_log
