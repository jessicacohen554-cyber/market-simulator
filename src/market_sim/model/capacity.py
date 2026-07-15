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
    which is the flat net-CONE (default) or — when
    ``config.capacity_market_clearing`` is on, the ISO has a published demand
    curve, and ``reserve_position`` (accredited firm ÷ requirement) is supplied
    — the CR-1 sloped-curve price ``VRR(reserve_position) × net_cone_curve``.
    Passing neither ``config`` nor ``reserve_position`` reproduces the pre-CR-1
    fixed price byte-identically.

    Energy-only ISOs (ERCOT, and any ISO absent from the registry) have
    ``capacity_market = False`` and earn zero here in both modes, so their
    retirement and new-entry economics are unchanged.
    """
    design = MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN)
    price = design.capacity_price_per_firm_mw_yr(config, reserve_position)
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

    In both constructions the firm peak nets the ISO's load-side capacity
    products out of the gross peak when the ISO's own adequacy construction
    does (ERCOT's CDR "Firm Peak Load" —
    :data:`ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO`; ISOs absent net nothing).
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


def _apply_staged_thinning_cap(
    eligible: list[Generator],
    retired: set[str],
    config: ScenarioConfig,
    year: int | None,
    event_sink: dict | None,
) -> list[Generator]:
    """Cap each fuel class's economic exits to a per-year MW budget.

    A staged-retirement RATE cap (G-30 first-wave fix, GATED
    ``config.staged_oversupply_thinning``, default off). When enabled, at most
    ``config.staged_thinning_max_gw_per_year`` GW of any single fuel class may
    retire in one simulation year; the least-efficient (highest-heat-rate)
    eligible units go first (``eligible`` is pre-sorted ``(fuel, -heat_rate)``),
    and once a class's budget is spent the remaining eligible units of that
    class are **deferred** — removed from ``retired`` so they survive this year
    — and re-screened next year with their loss counters intact.

    This is not a price floor or an adder: it does not touch any unit's margin
    or the underlying retire/keep decision, only how many exits of one fuel
    class a single year may realize (RTO deactivation-notice / RMR / coal
    contract-wind-down lead time — a fleet does not exit 14 GW of one fuel in a
    calendar year). Its purpose (rule 1/11) is to spread a large single-year
    over-supply exit across years so a later year — with a fleet the LP regime
    can price as scarce (in-year ORDC overlay or lookahead pro-forma) — makes
    the retain/exit call on the survivors. It mirrors
    ``ccs_retrofit_max_gw_per_year``'s throughput logic.

    Mutates ``retired`` in place (discards deferred unit ids) and records the
    deferrals under ``event_sink["staged_deferred"]`` when a sink is supplied.

    Returns:
        The list of deferred generators (empty when the gate is off or no
        class exceeds its budget).
    """
    if not config.staged_oversupply_thinning:
        return []
    budget_mw = float(config.staged_thinning_max_gw_per_year) * 1000.0
    if budget_mw <= 0.0:
        return []
    deferred: list[Generator] = []
    # ``eligible`` is sorted by (fuel_type, -heat_rate), so groupby(fuel_type)
    # yields each class least-efficient-first with no re-sort.
    for _fuel, group in groupby(eligible, key=lambda g: g.fuel_type):
        spent_mw = 0.0
        for g in group:
            if spent_mw >= budget_mw:
                retired.discard(g.unit_id)
                deferred.append(g)
            else:
                spent_mw += float(g.pmax_mw)
    if deferred:
        logger.info(
            "staged thinning (year %s): deferred %d units (%.0f MW) past the "
            "%.1f GW/fuel/yr exit budget",
            year,
            len(deferred),
            sum(float(g.pmax_mw) for g in deferred),
            config.staged_thinning_max_gw_per_year,
        )
        if event_sink is not None:
            event_sink["staged_deferred"] = [
                {"unit_id": g.unit_id, "fuel": g.fuel_type, "mw": float(g.pmax_mw)}
                for g in deferred
            ]
    return deferred


def apply_economic_retirements(
    fleet: list[Generator],
    fleet_arrays: FleetArrays,
    dispatch_result: DispatchResult,
    prices: np.ndarray,
    config: ScenarioConfig,
    consecutive_loss_years: dict[str, int],
    peak_demand: float,
    rps_shadow_price: float = 0.0,
    mc: np.ndarray | None = None,
    storage_power_mw: float = 0.0,
    deliverability_headroom: dict[str, float] | None = None,
    thermal_as_revenue_per_mw_yr: dict[str, float] | None = None,
    wind_pool_mw: float = 0.0,
    solar_pool_mw: float = 0.0,
    storage_firm_mw: float = 0.0,
    year: int | None = None,
    event_sink: dict | None = None,
    reserve_price_signal: np.ndarray | None = None,
    reserve_price_signal_slow: np.ndarray | None = None,
    reserve_position: float | None = None,
) -> tuple[list[Generator], dict[str, int], list[dict]]:
    """Retire thermal units that persistently fail to cover fixed cost.

    For each thermal generator the annual **attainable** (pro-forma)
    inframarginal margin is compared with its going-forward fixed cost
    (capacity-economics plan 2026-07 §5 step 2)::

        net_revenue        = sum_t max(0, price[zone, t] - mc[g, t], r[g, t])
                             * pmax[g] * availability[g, t]
        going_forward_cost = fixed_om_per_kw_yr * fom_multiplier
                             * pmax_mw * 1000

    where ``r[g, t]`` is the unit's reserve-price signal (0 when absent).
    The margin is the unit's optimal response to the screen's own price
    signal — the price-duration pro-forma the Potomac SOM net-revenue
    tables are built from, and the same basis the thermal new-entry screen
    already uses — rather than the prior LP's realized dispatch. The two
    diverge exactly where the screens' scarcity revenue lives: the
    post-solve ORDC adder lifts ``prices`` in hours the pre-adder LP left
    an out-of-merit peaker idle, so a realized-dispatch margin credits a
    peaker none of the scarcity rent the signal carries. Structural fix,
    zero fitted parameters; SOM is the external validity check, never a
    target (rule 1).

    ``mc`` is the unit's *full* variable cost (fuel + VOM + emission
    prices), not its bid: take-or-pay coal tranches bid below fuel cost in
    dispatch because the fuel is sunk within the contract year, but on a
    retirement horizon the contract lapses, so fuel is avoidable and counts
    against the margin. When ``mc`` is ``None`` the screen degrades to the
    legacy gross-energy-revenue-on-dispatch comparison, which overstates
    margins and under-retires -- callers should always supply ``mc``.

    A year in which ``net_revenue < going_forward_cost`` increments the
    unit's consecutive-loss counter; a profitable year resets it to zero.
    Once the counter reaches the unit's fuel-type retirement threshold the
    unit retires. Both the threshold and the fixed-cost multiplier are
    fuel-type-aware: coal exits faster (one loss year) and carries a
    higher effective fixed cost than gas, while modern ``gas_cc`` units
    are given the longest grace period. Fuel types without a specific
    override fall back to ``config.retirement_consecutive_years`` and a
    multiplier of ``1.0``.

    When multiple units in the same fuel class retire, the highest
    heat-rate (least efficient) units go first. A system-wide reliability
    floor then caps total retirements on the accredited (UCAP/ELCC) basis:
    if retiring every eligible unit would leave
    :func:`accredited_firm_capacity_mw` (surviving fleet at ``1 - EFORd`` /
    capacity credit, plus the wind/solar pools and pre-accredited storage
    ELCC) below ``peak_demand × (1 + PRM_iso)`` — the same
    :data:`PLANNING_RESERVE_MARGIN_BY_ISO` requirement the build backstop
    tests — eligible units are un-retired cheapest-firm-adequacy-first
    ($/firm-MW-yr, CO2 tie-break) until the requirement clears. Every floor
    retention is recorded in the returned attribution log. Under
    ``config.market_design_retirement_floor`` (GATED default off) the floor
    is skipped for ISOs explicitly registered energy-only in
    :data:`MARKET_DESIGN` (ERCOT) — see :func:`_apply_reliability_floor`.

    Args:
        fleet: The current generator fleet.
        fleet_arrays: Vectorized fleet aligned with ``dispatch_result``;
            supplies each generator's row index and zone index.
        dispatch_result: Solved dispatch whose ``dispatch`` array is
            ``(n_gen, T)`` thermal generation in MW.
        prices: Zonal energy prices of shape ``(n_zones, T)`` in $/MWh.
        config: Scenario config supplying fixed-O&M rates, per-fuel
            retirement thresholds and multipliers, and the reserve margin.
        consecutive_loss_years: Per-unit loss counters keyed by
            ``unit_id``; not mutated in place.
        peak_demand: Peak net demand in MW, used to size the reliability
            floor below which thermal capacity is not retired.
        rps_shadow_price: Prior year's RPS constraint dual in $/MWh. Only
            credited to RPS-eligible (clean) fuels, and never stacked with
            an exogenous EAC -- the higher of the two is taken.
        mc: Full variable cost aligned row-for-row with
            ``dispatch_result.dispatch``, shape ``(n_gen, T)`` in $/MWh.
            ``None`` falls back to gross-revenue screening (see above).
        storage_power_mw: AS-eligible (storage) fleet power in MW, the
            saturation driver for the exogenous AS credit.
        deliverability_headroom: Per-zone deliverable-capacity headroom for
            the locational RA gate (no-op when empty/off).
        thermal_as_revenue_per_mw_yr: ``{fuel_type: $/MW-yr}`` AS credit
            derived from the co-opt's reserve duals under
            ``ercot_thermal_as_endogenous`` (rule 19). When supplied it
            REPLACES the exogenous ``as_revenue_per_mw_yr`` for thermal —
            exactly one mechanism prices thermal AS. ``None`` (the default,
            flag off) keeps the exogenous flat rate.
        wind_pool_mw, solar_pool_mw: Zonal renewable-pool nameplate MW
            (bounds of the ``W``/``S`` dispatch variables), credited at
            :data:`RENEWABLE_CAPACITY_CREDIT` in the reliability floor's
            accredited sum. Default 0.0 keeps a conservative
            (thermal-and-fleet-only) floor.
        storage_firm_mw: Pre-accredited storage ELCC MW counted toward the
            floor requirement. Default 0.0 (conservative).
        year: Simulation year, stamped on floor-retention log rows and used
            to evaluate the IRA §45U existing-nuclear PTC expiry
            (``config.ira_45u_last_year``). ``None`` (legacy callers) skips
            the §45U nuclear credit.
        event_sink: Optional dict populated in place with the retirement
            attribution the evolution ledger needs (CX-3): ``"retired"`` (the
            units actually retired) and ``"floor_retained"`` (units the
            economic screen wanted out but the reliability floor kept online).
            Each entry is ``{"unit_id","fuel","mw"}``. ``None`` records
            nothing. Does not affect the retirement decision.
        reserve_price_signal: Hourly ``(T,)`` reserve price in $/MWh for
            synchronized reserve-eligible units — the co-opt's own binding
            reserve dual (under ``ercot_thermal_as_endogenous``) or the
            post-solve ORDC scarcity adder (RTORPA/RTOFFPA: ERCOT pays
            real-time reserves the same ORDC price, Nodal Protocols
            §6.5.7.5). Each reserve-eligible unit's hourly value becomes
            ``max(0, price - mc, r)`` — energy or reserve, never both on
            the same MW. When supplied it is the SOLE thermal AS pricing
            (rule 19): both the annual endogenous per-fuel rate and the
            exogenous flat rate are suppressed. ``None`` (default) keeps
            the legacy annual AS credits. Requires ``mc``.
        reserve_price_signal_slow: Hourly ``(T,)`` reserve price for the
            offline-capable quick-start tier (gas_ct/oil — Non-Spin only,
            mirroring the co-opt's headroom cascade).
        reserve_position: System accredited reserve position (accredited firm ÷
            requirement) for the CR-1 sloped capacity demand curve. ``None``
            (default) or ``capacity_market_clearing`` off keeps the fixed
            net-CONE capacity payment (byte-identical); when supplied and the
            gate is on, the capacity payment slides along the ISO's published
            demand curve.

    Returns:
        Tuple ``(survivors, loss_years, floor_retention_log)`` -- the fleet
        with retired units removed, the updated loss-counter dict (retired
        units dropped), and one attribution dict per unit the reliability
        floor un-retired this year.
    """
    prices = np.asarray(prices, dtype=float)
    dispatch = np.asarray(dispatch_result.dispatch, dtype=float)
    if mc is None:
        logger.warning(
            "apply_economic_retirements: no marginal-cost array supplied; "
            "screening on gross energy revenue, which under-retires"
        )
    else:
        mc = np.asarray(mc, dtype=float)
    # Availability-derated capacity per row, (n_gen, T) — the MW the pro-forma
    # margin can sell in each hour. Falls back to flat pmax when the arrays
    # carry no availability (older callers).
    availability = getattr(fleet_arrays, "availability", None)
    if availability is None:
        availability = np.ones_like(dispatch)
    cap_mw = np.asarray(fleet_arrays.pmax, dtype=float)[:, None] * np.asarray(
        availability, dtype=float
    )
    idx_of = {uid: i for i, uid in enumerate(fleet_arrays.unit_ids)}
    loss_years = dict(consecutive_loss_years)

    # Diagnostic-only revenue-stack accumulator (no decision effect): per-fuel
    # capacity-weighted screen net revenue vs going-forward cost, both in
    # $/kW-yr. Emitted once per screen call for the FOM+scarcity joint protocol
    # revenue-side audit (docs/handoffs/fom-scarcity-joint-protocol; rule 1 — the
    # revenue side must be identified against its own external observable, the
    # Potomac ERCOT SOM net-revenue tables, never tuned to the retirement pace).
    _screen_stack: dict[str, list[tuple[float, float, float]]] = {}

    eligible: list[Generator] = []
    for g in fleet:
        fom_field = _THERMAL_FOM.get(g.fuel_type)
        if fom_field is None:
            continue
        rows = _dispatch_rows(g, idx_of)
        if not rows:
            continue

        zone = int(fleet_arrays.zone_idx[rows[0]])
        # Reserve tier for this unit (plan §5 step 2): synchronized units see
        # the all-products signal; offline-capable quick-starts (gas_ct/oil)
        # only the Non-Spin tier; non-reserve fuels none. Requires mc — the
        # legacy gross-revenue fallback has no cost basis to arbitrage
        # against, so it keeps the legacy path wholesale.
        r_row: np.ndarray | None = None
        if (
            mc is not None
            and reserve_price_signal is not None
            and g.fuel_type in RESERVE_FUEL_TYPES
        ):
            r_row = (
                reserve_price_signal_slow
                if g.fuel_type in QUICK_START_FUEL_TYPES
                else reserve_price_signal
            )
            if r_row is None:
                r_row = np.zeros_like(reserve_price_signal)
        # Attainable (pro-forma) inframarginal margin: the unit's per-hour
        # best use against the screen's own price signal —
        # max(0, price - mc, reserve price) x available capacity. Realized
        # LP dispatch is NOT the basis: the signal includes the post-solve
        # ORDC adder the dispatch never saw, so a realized-dispatch margin
        # structurally misses the scarcity rent (the Potomac SOM net-revenue
        # construction is this same pro-forma). Gross revenue alone would
        # let a unit "cover" fixed cost with money it spent on fuel.
        if mc is None:
            net_revenue = float(sum(np.dot(prices[zone], dispatch[i]) for i in rows))
        else:
            net_revenue = 0.0
            for i in rows:
                hourly_value = np.maximum(prices[zone] - mc[i], 0.0)
                if r_row is not None:
                    hourly_value = np.maximum(hourly_value, r_row)
                net_revenue += float(np.dot(hourly_value, cap_mw[i]))

        # The attribute payment -- the higher of the exogenous EAC and the
        # endogenous RPS shadow price, never their sum -- adds revenue
        # beyond the energy market, keeping units that energy prices alone
        # would not. The RPS shadow price is credited only to RPS-eligible
        # (renewable) fuels -- wind/solar -- never to nuclear or hydro, which
        # are clean but not renewable (CX-6a, plan §6.5(a)). Nuclear retention
        # support instead flows through eac_price (ZEC/CES).
        annual_gen_mwh = float(sum(np.sum(dispatch[i]) for i in rows))
        eac_price = get_eac_price_for_new_entry(g.fuel_type, config)
        # IRA §45U existing-nuclear PTC: a per-MWh production credit on the
        # unit's realized output that supports nuclear retention exactly like
        # eac_price_nuclear (ZEC/CES) — so it enters the SAME attribute-revenue
        # seam, NEVER stacked with it (rule 19, one mechanism per phenomenon).
        # We fold it into eac_price via max(), then compute_attribute_revenue's
        # own max(eac_price, rps) yields max(§45U, eac_price_nuclear) for the
        # (nuclear, rps=0) case. The credit's gross-receipts phase-down keys on
        # the unit's own average realized energy price (this year's
        # generation-weighted zonal price), and it expires after
        # config.ira_45u_last_year. Nuclear only; needs a simulation year to
        # evaluate the expiry (None on legacy callers -> no §45U). Source:
        # 26 U.S.C. §45U; see policy.ira.section_45u_credit_per_mwh.
        if g.fuel_type == "nuclear" and year is not None and annual_gen_mwh > 0.0:
            gross_energy_revenue = float(
                sum(np.dot(prices[zone], dispatch[i]) for i in rows)
            )
            avg_realized_price = gross_energy_revenue / annual_gen_mwh
            eac_price = max(
                eac_price,
                section_45u_credit_per_mwh(year, avg_realized_price, config),
            )
        rps_for_unit = rps_shadow_price if g.fuel_type in _RPS_ELIGIBLE_FUELS else 0.0
        net_revenue += compute_attribute_revenue(
            g.fuel_type, annual_gen_mwh, eac_price, rps_for_unit
        )

        # Resource-adequacy capacity payment (Module M1): in PJM/NYISO/
        # ISO-NE/CAISO a unit earns a capacity revenue stream that can cover
        # fixed cost even when energy margin is negative, so omitting it
        # over-retires thermal capacity there. Zero in energy-only ERCOT.
        # Locational gate: when capacity_deliverability_limits is on, a unit in a
        # zone already long on deliverable firm capacity vs its requirement earns
        # NO capacity payment (RA saturated there), so surplus in a long zone
        # retires as it should while short zones keep their units.
        if not _zone_is_long(deliverability_headroom, g.zone):
            net_revenue += g.pmax_mw * capacity_revenue_per_mw_yr(
                config.iso, g.fuel_type, g.eford, config, reserve_position
            )

        # ERCOT ancillary-service revenue (Reg/RRS/ECRS/Non-Spin): a real
        # income stream the energy-only LP cannot produce. Exactly one
        # mechanism prices it (rule 19), in precedence order:
        #  1. the hourly reserve-price signal (screen_reserve_value_enabled)
        #     — already folded into the pro-forma margin above as
        #     max(energy, reserve) per hour, so NO annual credit stacks on
        #     top of it;
        #  2. else under ercot_thermal_as_endogenous the co-opt duals supply
        #     an annual per-fuel derived rate (thermal_as_revenue_per_mw_yr)
        #     and the exogenous flat rate is suppressed;
        #  3. else the exogenous flat rate (as_revenue_enabled, ERCOT only,
        #     saturating on the storage fleet) is the sole credit.
        if mc is not None and reserve_price_signal is not None:
            pass  # hourly max(energy, reserve) above is the sole AS pricing
        elif thermal_as_revenue_per_mw_yr is not None:
            net_revenue += g.pmax_mw * thermal_as_revenue_per_mw_yr.get(
                g.fuel_type, 0.0
            )
        else:
            net_revenue += g.pmax_mw * as_revenue_per_mw_yr(
                g.fuel_type, storage_power_mw, config
            )

        threshold = getattr(
            config,
            _RETIREMENT_YEARS.get(g.fuel_type, ""),
            config.retirement_consecutive_years,
        )
        multiplier = getattr(config, _FOM_MULTIPLIER.get(g.fuel_type, ""), 1.0)
        going_forward_cost = (
            getattr(config, fom_field) * multiplier * g.pmax_mw * 1000.0
        )

        # Diagnostic accumulation only — does not affect the retire decision.
        if g.pmax_mw > 0.0:
            _screen_stack.setdefault(g.fuel_type, []).append(
                (
                    net_revenue / (g.pmax_mw * 1000.0),  # $/kW-yr revenue stack
                    getattr(config, fom_field) * multiplier,  # $/kW-yr bar
                    g.pmax_mw,
                )
            )

        if net_revenue < going_forward_cost:
            loss_years[g.unit_id] = loss_years.get(g.unit_id, 0) + 1
        else:
            loss_years[g.unit_id] = 0

        if loss_years[g.unit_id] >= threshold:
            eligible.append(g)

    # Revenue-side audit line (diagnostic): capacity-weighted screen net
    # revenue and going-forward bar per fuel class, for the FOM+scarcity joint
    # protocol. Compared against the Potomac ERCOT SOM CT/CC net-revenue tables,
    # never used to tune FOM (rule 1).
    for _fuel, _rows in sorted(_screen_stack.items()):
        _cap = sum(r[2] for r in _rows)
        if _cap <= 0.0:
            continue
        _rev = sum(r[0] * r[2] for r in _rows) / _cap
        _bar = sum(r[1] * r[2] for r in _rows) / _cap
        logger.info(
            "screen revenue stack [%s]: net_rev=%.1f $/kW-yr, "
            "going_forward_bar=%.1f $/kW-yr, cap=%.0f MW, n=%d",
            _fuel,
            _rev,
            _bar,
            _cap,
            len(_rows),
        )

    # Within each fuel class, retire the least efficient units first.
    eligible.sort(key=lambda g: (g.fuel_type, -g.heat_rate))
    retired = {g.unit_id for g in eligible}

    # Staged over-supply thinning (G-30 first-wave fix, GATED default off): cap
    # each fuel class's exits to a per-year MW budget so a large single-year
    # wave spreads across years the LP regime can price. A RATE cap, not a
    # floor — the retain/exit margin is untouched; deferred units keep their
    # loss counters and re-screen next year (see the config-field docstring).
    # Applied BEFORE the reliability floor so the two un-retire sets stay
    # distinct (staged = lead-time deferral; floor = adequacy retention).
    staged_deferred = _apply_staged_thinning_cap(
        eligible, retired, config, year, event_sink
    )
    staged_ids = {g.unit_id for g in staged_deferred}

    # Reliability floor (accredited basis, plan §3.2): never strip the
    # system's accredited firm capacity below the shared PRM requirement.
    floor_retention_log = _apply_reliability_floor(
        fleet,
        eligible,
        retired,
        loss_years,
        config,
        peak_demand,
        wind_pool_mw,
        solar_pool_mw,
        storage_firm_mw,
        deliverability_headroom,
        year,
    )

    survivors = [g for g in fleet if g.unit_id not in retired]
    for uid in retired:
        loss_years.pop(uid, None)

    # Ledger attribution: the units actually retired, and the units the
    # economic screen flagged (``eligible``) but the reliability floor kept
    # online (CX-3). ``eligible`` minus ``retired`` is exactly the floor set
    # (``_apply_reliability_floor`` discards un-retained units from ``retired``
    # in place), so this stays consistent with ``floor_retention_log``.
    if event_sink is not None:
        event_sink["retired"] = [
            {"unit_id": g.unit_id, "fuel": g.fuel_type, "mw": float(g.pmax_mw)}
            for g in eligible
            if g.unit_id in retired
        ]
        event_sink["floor_retained"] = [
            {"unit_id": g.unit_id, "fuel": g.fuel_type, "mw": float(g.pmax_mw)}
            for g in eligible
            if g.unit_id not in retired and g.unit_id not in staged_ids
        ]

    return survivors, loss_years, floor_retention_log


# --- Part 2: capacity additions -------------------------------------------

# Classic candidate technologies considered for economic new entry. These
# are costed from NEW_ENTRY_COSTS; emerging technologies are handled
# separately (see _EMERGING_AVAILABLE_YEAR below).
_NEW_ENTRY_TECHS: tuple[str, ...] = (
    "wind",
    "solar",
    "gas_cc",
    "gas_ct",
    "nuclear_smr",
)

# Fuels whose new builds increment the zonal wind_cap/solar_cap pools (and
# the W[z,t]/S[z,t] dispatch variables) rather than entering as thermal
# Generator objects. Variable-output renewables must follow a CF profile.
# Offshore wind is NOT here: it enters as a zero-MC Generator (Option A).
_RENEWABLE_NEW_FUELS: frozenset[str] = frozenset({"wind", "solar"})

# Emerging-technology candidates, mapped to the ScenarioConfig field that
# names the calendar year each first becomes available for new entry.
_EMERGING_AVAILABLE_YEAR: dict[str, str] = {
    "hydrogen_ct": "h2_available_year",
    "hydrogen_ccgt": "h2_available_year",
    "gas_cc_ccs": "ccs_available_year",
    "geothermal": "egs_available_year",
    "offshore_wind": "offshore_wind_available_year",
}

# Technologies that share another technology's per-tech interconnection
# queue cap. Hydrogen turbines and CCUS reuse the gas-turbine supply chain
# and queue, so they draw on the shared ``gas_cc`` per-tech cap.
_QUEUE_CAP_GROUP: dict[str, str] = {
    "hydrogen_ct": "gas_cc",
    "hydrogen_ccgt": "gas_cc",
    "gas_cc_ccs": "gas_cc",
    "nuclear_smr": "nuclear",
    "nuclear_large": "nuclear",
}

# Assumed capacity factor for screening each emerging technology in the
# economic new-entry LCOE comparison. Hydrogen turbines run as peakers /
# mid-merit units; geothermal and offshore wind use their resource CFs.
_EMERGING_SCREEN_CF: dict[str, float] = {
    "hydrogen_ct": 0.10,  # simple-cycle H2 peaker duty cycle
    "hydrogen_ccgt": 0.45,  # combined-cycle H2 mid-merit duty cycle
}


def _offshore_wind_params(iso: str, config: ScenarioConfig) -> dict:
    """Return the offshore-wind cost/performance parameters for an ISO.

    CAISO is served by deep-water floating turbines; other ISOs default to
    fixed-bottom. ``config.offshore_wind_cf_override`` replaces the base
    capacity factor when set.
    """
    key = "floating" if iso == "CAISO" else "fixed_bottom"
    params = dict(OFFSHORE_WIND_PARAMS[key])
    if config.offshore_wind_cf_override is not None:
        params["base_cf"] = config.offshore_wind_cf_override
    return params


def _emerging_screen_cf(tech: str, iso: str, config: ScenarioConfig) -> float:
    """Return the capacity factor used to screen an emerging technology."""
    if tech in _EMERGING_SCREEN_CF:
        return _EMERGING_SCREEN_CF[tech]
    if tech == "gas_cc_ccs":
        return NEW_ENTRY_COSTS["gas_cc"]["base_cf"]
    if tech == "geothermal":
        return GEOTHERMAL_PARAMS["egs"]["capacity_factor"]
    if tech == "offshore_wind":
        return _offshore_wind_params(iso, config)["base_cf"]
    raise KeyError(f"no screen capacity factor for emerging tech {tech!r}")


def _new_entry_candidates(year: int, config: ScenarioConfig, iso: str) -> list[str]:
    """Return the technologies eligible for economic new entry this year.

    The four classic technologies are always eligible. Each emerging
    technology joins the pool only once the simulation year reaches its
    configured availability year; offshore wind additionally enters only
    in ISOs listed in ``config.offshore_wind_eligible_isos``.
    """
    candidates = list(_NEW_ENTRY_TECHS)
    for tech, year_field in _EMERGING_AVAILABLE_YEAR.items():
        if year < getattr(config, year_field):
            continue
        if tech == "offshore_wind" and iso not in config.offshore_wind_eligible_isos:
            continue
        candidates.append(tech)
    return candidates


def _emerging_lcoe(
    tech: str,
    year: int,
    config: ScenarioConfig,
    iso: str,
    cf: float,
    gas_price_per_mmbtu: float,
    carbon_price: float,
) -> float:
    """Return the levelized cost of energy for an emerging technology.

    Capital is annualized with a capital recovery factor from
    ``config.real_discount_rate`` and the technology lifetime, spread over
    annual generation at the screening capacity factor. Variable cost is
    technology-specific:

    * **Hydrogen turbines** burn derived hydrogen fuel; the IRA §45V credit
      lowers the effective fuel cost.
    * **CCUS** burns natural gas at a penalized heat rate, pays a VOM
      adder, a captured-CO2 transport cost and a residual-emissions carbon
      cost, and earns the IRA §45Q credit as a variable-cost offset.
    * **Geothermal** has zero fuel cost and earns the zero-emission
      production tax credit (treated like wind).
    * **Offshore wind** has zero fuel cost.

    Args:
        tech: Emerging technology key.
        year: Simulation year (IRA credit expiry).
        config: Scenario config.
        iso: ISO identifier (selects the offshore-wind resource class).
        cf: Screening capacity factor.
        gas_price_per_mmbtu: Delivered gas price, used by CCUS.
        carbon_price: Carbon price in $/tCO2, used by CCUS residual cost.

    Returns:
        The IRA-adjusted LCOE in $/MWh.
    """
    annual_mwh_per_kw = HOURS_PER_YEAR * cf / 1000.0

    if tech in ("hydrogen_ct", "hydrogen_ccgt"):
        key = "h2_ct" if tech == "hydrogen_ct" else "h2_ccgt"
        params = HYDROGEN_TURBINE_PARAMS[key]
        crf = _capital_recovery_factor(config.real_discount_rate, params["lifetime_yr"])
        fixed = params["capex_kw"] * crf + params["fom_kw_yr"]
        h2_cost = compute_h2_fuel_cost(year, config, iso)
        h2_cost = max(0.0, h2_cost - h2_45v_credit_per_mmbtu(year, config))
        variable = params["heat_rate"] * h2_cost + params["vom"]
        return fixed / annual_mwh_per_kw + variable

    if tech == "gas_cc_ccs":
        ccs = CCUS_PARAMS["gas_cc_ccs_90"]
        crf = _capital_recovery_factor(config.real_discount_rate, ccs["lifetime_yr"])
        fixed = ccs["capex_kw"] * crf + ccs["fom_kw_yr"]
        base_hr = min(HEAT_RATE_BINS["gas_cc"].values())
        base_co2 = min(CO2_RATES["gas_cc"].values())
        captured = base_co2 * config.ccs_capture_rate
        residual = base_co2 * (1.0 - config.ccs_capture_rate)
        variable = (
            base_hr * ccs["heat_rate_penalty"] * gas_price_per_mmbtu
            + VOM["gas_cc"]
            + ccs["vom_adder"]
            + captured * config.co2_transport_storage_cost
            + residual * carbon_price
            - ccus_45q_credit_per_mwh(captured, year, config)
        )
        return fixed / annual_mwh_per_kw + variable

    if tech == "geothermal":
        egs = GEOTHERMAL_PARAMS["egs"]
        crf = _capital_recovery_factor(config.real_discount_rate, egs["lifetime_yr"])
        fixed = egs["capex_kw"] * crf + egs["fom_kw_yr"]
        lcoe = fixed / annual_mwh_per_kw + egs["vom"]
        return apply_ira_credits_to_lcoe("geothermal", lcoe, year, config)

    if tech == "offshore_wind":
        params = _offshore_wind_params(iso, config)
        crf = _capital_recovery_factor(config.real_discount_rate, params["lifetime_yr"])
        fixed = params["capex_kw"] * crf + params["fom_kw_yr"]
        return fixed / annual_mwh_per_kw

    raise KeyError(f"unknown emerging technology {tech!r}")


@dataclass
class CumulativeDeployment:
    """Tracks global cumulative installed capacity (GW) per technology.

    Initialized from WRIGHT_REFERENCE_GW (the base-year global stock),
    then incremented each year by GLOBAL_ANNUAL_DEPLOYMENT_GW plus
    any local ISO builds. The local ISO contribution is small relative
    to global deployment but included for consistency.
    """

    capacities: dict[str, float]

    @classmethod
    def initial(cls) -> "CumulativeDeployment":
        """Start from the reference year global installed base."""
        return cls(capacities=dict(WRIGHT_REFERENCE_GW))

    def advance_year(self, local_builds_gw: dict[str, float] | None = None) -> None:
        """Increment cumulative capacities by one year of global deployment.

        Args:
            local_builds_gw: Additional GW built locally this year, by tech.
                Merged into the global total. Keys should match
                WRIGHT_REFERENCE_GW keys.
        """
        for tech, annual_gw in GLOBAL_ANNUAL_DEPLOYMENT_GW.items():
            self.capacities[tech] = self.capacities.get(tech, 0.0) + annual_gw
        if local_builds_gw:
            for tech, gw in local_builds_gw.items():
                self.capacities[tech] = self.capacities.get(tech, 0.0) + gw

    def get(self, tech: str) -> float | None:
        """Return cumulative GW for a technology, or None if not tracked."""
        return self.capacities.get(tech)

    def add(self, tech: str, gw: float) -> None:
        """Add deployed GW to a technology's cumulative total.

        Used for off-cycle deployment that does not flow through
        :meth:`advance_year` -- notably CCS retrofits, which expand the
        global capture-equipment experience base just like a new build.
        """
        self.capacities[tech] = self.capacities.get(tech, 0.0) + gw


def _merge_renewable_additions(
    target: dict[str, dict[str, float]],
    source: dict[str, dict[str, float]],
) -> None:
    """Accumulate ``source`` renewable build MW into ``target`` in place.

    Both dicts are keyed ``{zone: {fuel: mw}}``; overlapping zone/fuel pairs
    have their megawatts summed.
    """
    for zone, by_fuel in source.items():
        zone_acc = target.setdefault(zone, {})
        for fuel, mw in by_fuel.items():
            zone_acc[fuel] = zone_acc.get(fuel, 0.0) + mw


def wright_cost(
    base_cost: float,
    cumulative_gw: float,
    reference_gw: float,
    learning_rate: float,
) -> float:
    """Return a Wright's-Law learning-adjusted unit cost.

    Cost falls as cumulative deployment grows relative to a reference::

        exponent = -log2(1 - learning_rate)
        cost = base_cost * (cumulative_gw / reference_gw) ** (-exponent)

    At the reference level the cost is unchanged; doubling cumulative
    capacity multiplies cost by exactly ``(1 - learning_rate)`` -- the
    standard "X% cost reduction per doubling" convention the learning
    rates in :data:`NEW_ENTRY_COSTS` are documented in, and the same
    formula the CCS retrofit path uses.

    Args:
        base_cost: Cost at the reference deployment level.
        cumulative_gw: Cumulative installed capacity, GW.
        reference_gw: Reference cumulative capacity, GW.
        learning_rate: Fractional cost reduction per doubling of
            cumulative capacity (``0`` disables learning).

    Returns:
        The learning-adjusted cost. Returns ``base_cost`` unchanged when
        either capacity figure is non-positive.
    """
    if cumulative_gw <= 0.0 or reference_gw <= 0.0 or learning_rate <= 0.0:
        return base_cost
    exponent = -math.log2(1.0 - learning_rate)
    return base_cost * (cumulative_gw / reference_gw) ** (-exponent)


def _capital_recovery_factor(rate: float, lifetime_yr: float) -> float:
    """Return the capital recovery factor for a given rate and lifetime."""
    if rate <= 0.0:
        return 1.0 / lifetime_yr
    growth = (1.0 + rate) ** lifetime_yr
    return rate * growth / (growth - 1.0)


def compute_lcoe(
    tech_type: str,
    year: int,
    config: ScenarioConfig,
    cumulative_gw: float | None = None,
) -> float:
    """Return the levelized cost of energy for a candidate technology.

    Capital cost is annualized with a capital recovery factor derived from
    ``config.real_discount_rate`` and the technology lifetime, optionally
    discounted by a Wright's-Law learning curve when ``cumulative_gw`` is
    supplied. Fixed O&M is added and the total is spread over expected
    annual generation.

    IRA credits enter at the right layer: the solar investment tax credit
    discounts ``capex_per_kw`` before annualization, so it never touches
    fixed O&M; the wind production tax credit is subtracted from the final
    $/MWh, as a per-MWh credit should be.

    Args:
        tech_type: Technology key into :data:`NEW_ENTRY_COSTS`.
        year: Simulation year, used for IRA credit expiry.
        config: Scenario config supplying the discount rate and the PB-1
            tech-cost lever (``tech_cost_path``/``tech_cost_percentile``).
        cumulative_gw: Cumulative global deployment, GW. When ``None`` no
            learning adjustment is applied.

    Returns:
        The IRA-adjusted LCOE in $/MWh.
    """
    costs = resolve_new_entry_costs(config)[tech_type]
    capex_per_kw = costs["capex_per_kw"]

    reference_gw = WRIGHT_REFERENCE_GW.get(tech_type)
    if cumulative_gw is not None and reference_gw is not None:
        capex_per_kw = wright_cost(
            capex_per_kw, cumulative_gw, reference_gw, costs["learning_rate"]
        )

    # IRA ITC: reduce capex before annualization.
    # Wind/solar: cliff cutoff. Other clean: graduated phaseout.
    if tech_type == "solar":
        if year <= config.ira_wind_solar_last_year:
            capex_per_kw *= 1.0 - config.ira_itc_solar

    crf = _capital_recovery_factor(config.real_discount_rate, costs["lifetime_yr"])
    annual_cost_per_kw = capex_per_kw * crf + costs["fom_per_kw_yr"]
    # Annual generation per kW of capacity, expressed in MWh.
    annual_mwh_per_kw = HOURS_PER_YEAR * costs["base_cf"] / 1000.0
    lcoe = annual_cost_per_kw / annual_mwh_per_kw

    # Wind PTC: a per-MWh production credit, correctly subtracted post-hoc.
    if tech_type == "wind":
        if year <= config.ira_wind_solar_last_year:
            lcoe -= config.ira_ptc_wind

    return lcoe


def estimate_expected_revenue(
    prices: np.ndarray, cf: float | np.ndarray, hours: int = HOURS_PER_YEAR
) -> float:
    """Return expected annual energy revenue per MW of capacity.

    Revenue is the price duration curve weighted by the capacity factor. A
    scalar ``cf`` is applied flatly to the mean price; an hourly ``cf``
    array is dotted hour-by-hour against prices.

    Args:
        prices: Hourly energy prices in $/MWh; any shape, flattened.
        cf: Capacity factor, scalar or hourly array.
        hours: Hours in the revenue year.

    Returns:
        Expected revenue in $/MW-yr.
    """
    prices = np.asarray(prices, dtype=float).ravel()
    if prices.size == 0:
        return 0.0

    cf_arr = np.asarray(cf, dtype=float)
    if cf_arr.ndim == 0:
        return float(cf_arr) * float(prices.mean()) * hours

    cf_arr = cf_arr.ravel()
    n = min(prices.size, cf_arr.size)
    hourly = prices[:n] * cf_arr[:n]
    return float(hourly.mean() * hours)


def _make_new_generator(
    tech_type: str,
    pmax_mw: float,
    zone: str,
    year: int,
    seq: int,
    config: ScenarioConfig,
    iso: str,
) -> Generator:
    """Build a new ``Generator`` for an entering block of capacity.

    Classic thermal technologies are assigned the most efficient heat-rate
    bin -- a freshly built unit is best-in-class -- along with the matching
    CO2 rate and variable O&M. Emerging technologies enter as Generators
    using the existing LP variable structure:

    * **Hydrogen turbines** carry their heat rate, VOM and NOx rate from
      :data:`HYDROGEN_TURBINE_PARAMS`; the fuel price is resolved at
      dispatch time from the derived hydrogen cost.
    * **CCUS** is a gas CC variant: a penalized heat rate, a VOM that folds
      in the (constant) captured-CO2 transport cost, and a reduced emission
      rate reflecting the capture rate. Its residual CO2 then pays the
      carbon price through standard marginal-cost assembly.
    * **Geothermal** is a zero-fuel dispatchable unit with a turn-down
      floor at ``config.egs_pmin_fraction`` of rated capacity.
    * **Offshore wind** enters as a zero-MC Generator with only a
      mechanical forced-outage rate; its hourly availability profile is
      injected later by ``inject_offshore_wind_availability`` in the runner.
    """
    unit_id = f"{tech_type}_new_{year}_{seq}"
    kwargs: dict = {
        "unit_id": unit_id,
        "name": unit_id,
        "zone": zone,
        "fuel_type": tech_type,
        "pmax_mw": pmax_mw,
        "online_year": year,
    }

    bins = HEAT_RATE_BINS.get(tech_type)
    if bins is not None:
        best_bin = min(bins, key=bins.get)
        kwargs["efficiency_bin"] = best_bin
        kwargs["heat_rate"] = bins[best_bin]
        kwargs["emission_rate_co2"] = CO2_RATES[tech_type][best_bin]
        kwargs["vom"] = VOM[tech_type]

    # Nuclear carries no fuel cost (fuel is embedded in FOM) and runs as a
    # must-run baseload unit; it has no heat-rate bin to assign above. The
    # cost-tier key (nuclear_smr/nuclear_large) is kept in the unit_id for
    # tracking, but fuel_type collapses to "nuclear" so dispatch, emissions
    # and retirement logic treat all reactors identically.
    if tech_type in ("nuclear_smr", "nuclear_large"):
        kwargs["fuel_type"] = "nuclear"
        kwargs["is_must_run"] = True
        kwargs["vom"] = VOM["nuclear"]
        kwargs["eford"] = EFORD["nuclear"]

    if tech_type in ("hydrogen_ct", "hydrogen_ccgt"):
        key = "h2_ct" if tech_type == "hydrogen_ct" else "h2_ccgt"
        params = HYDROGEN_TURBINE_PARAMS[key]
        kwargs["heat_rate"] = params["heat_rate"]
        kwargs["vom"] = params["vom"]
        kwargs["emission_rate_co2"] = params["emission_rate_co2"]
        kwargs["nox_rate"] = params["nox_rate"]
        kwargs["eford"] = params["eford"]

    elif tech_type == "gas_cc_ccs":
        ccs = CCUS_PARAMS["gas_cc_ccs_90"]
        base_hr = min(HEAT_RATE_BINS["gas_cc"].values())
        base_co2 = min(CO2_RATES["gas_cc"].values())
        captured = base_co2 * config.ccs_capture_rate
        kwargs["efficiency_bin"] = "h_class"
        kwargs["heat_rate"] = base_hr * ccs["heat_rate_penalty"]
        kwargs["emission_rate_co2"] = base_co2 * (1.0 - config.ccs_capture_rate)
        # The captured-CO2 transport+storage cost is a constant $/MWh, so it
        # folds into VOM; the residual emissions still pay the carbon price.
        kwargs["vom"] = (
            VOM["gas_cc"]
            + ccs["vom_adder"]
            + captured * config.co2_transport_storage_cost
        )
        kwargs["nox_rate"] = NOX_RATES.get("gas_cc", 0.0)
        kwargs["eford"] = EFORD["gas_cc"]

    elif tech_type == "geothermal":
        egs = GEOTHERMAL_PARAMS["egs"]
        kwargs["heat_rate"] = egs["heat_rate"]
        kwargs["vom"] = egs["vom"]
        kwargs["emission_rate_co2"] = egs["emission_rate_co2"]
        kwargs["nox_rate"] = egs["nox_rate"]
        kwargs["eford"] = egs["eford"]
        kwargs["pmin_mw"] = pmax_mw * config.egs_pmin_fraction

    elif tech_type == "offshore_wind":
        kwargs["heat_rate"] = 0.0
        kwargs["vom"] = 0.0
        kwargs["emission_rate_co2"] = 0.0
        # Hourly availability set by inject_offshore_wind_availability in the
        # runner; eford here is only the mechanical forced outage rate.
        kwargs["eford"] = 0.05

    return Generator(**kwargs)


def apply_economic_new_entry(
    fleet: list[Generator],
    prices: np.ndarray,
    year: int,
    config: ScenarioConfig,
    iso: str,
    rps_shadow_price: float = 0.0,
    cumulative: CumulativeDeployment | None = None,
    gas_price_per_mmbtu: float = 0.0,
    carbon_price: float = 0.0,
    storage_power_mw: float = 0.0,
    deliverability_headroom: dict[str, float] | None = None,
    thermal_as_revenue_per_mw_yr: dict[str, float] | None = None,
    reserve_price_signal: np.ndarray | None = None,
    reserve_price_signal_slow: np.ndarray | None = None,
    zone_names: list[str] | None = None,
    wind_cf: np.ndarray | None = None,
    solar_cf: np.ndarray | None = None,
    reserve_position: float | None = None,
    screen_ledger: list[dict] | None = None,
) -> tuple[list[Generator], dict[str, dict[str, float]]]:
    """Build new capacity for technologies that clear their LCOE.

    For each candidate technology the expected annual revenue per MW is
    compared with its annualized levelized cost. Clean technologies
    additionally earn an attribute payment per MWh generated -- the higher
    of the exogenous EAC and the prior year's RPS shadow price, never
    their sum -- so either a binding RPS or an EAC lifts their expected
    revenue and pulls more of them across the LCOE hurdle. Profitable
    technologies are ranked by margin and built in priority order, highest
    margin first. Two caps bind independently:

    * each technology builds at most its per-tech cap from
      :data:`QUEUE_CAP_PER_TECH_GW`, and
    * the total across all technologies builds at most the ISO-level
      cap :data:`QUEUE_CAP_GW`.

    The highest-margin technology draws on the shared ISO budget first;
    once that budget is exhausted no further technologies are built.

    Emerging technologies (hydrogen turbines, CCUS, enhanced geothermal,
    offshore wind) join the candidate pool once the simulation year
    reaches their configured availability year. Hydrogen turbines and CCUS
    share the ``gas_cc`` per-tech queue cap; geothermal and offshore wind
    have their own. Offshore wind enters only in eligible ISOs.

    Thermal new entry (``gas_cc``, ``nuclear_smr``, the hydrogen turbines,
    CCUS, geothermal and offshore wind) is appended to the returned fleet
    as a :class:`Generator`. Wind and solar are *not*: variable-output
    renewables must follow a capacity-factor profile, so their build MW is
    routed to the zonal ``wind_cap`` / ``solar_cap`` pools (the bounds of
    the ``W[z,t]`` and ``S[z,t]`` dispatch variables) rather than entering
    as flat-availability thermal units.

    Args:
        fleet: The current generator fleet.
        prices: Hourly zonal energy prices in $/MWh from the prior solve.
        year: Simulation year.
        config: Scenario config.
        iso: ISO identifier, supplying the queue caps and build zone.
        rps_shadow_price: Prior year's RPS shadow price in $/MWh. Credited
            to RPS-eligible renewables as an attribute payment, taken as
            the max of it and the exogenous EAC (the two do not stack).
        cumulative: Global cumulative deployment, used to discount each
            candidate's capex along its Wright's-Law learning curve.
        gas_price_per_mmbtu: Delivered gas price, used to charge gas CC
            new entry its expected variable fuel cost.
        carbon_price: Carbon price in $/tCO2, used to charge thermal new
            entry its expected carbon cost.
        storage_power_mw: AS-eligible (storage) fleet power in MW, the
            saturation driver for the exogenous AS credit.
        deliverability_headroom: Per-zone deliverable-capacity headroom for
            the locational RA gate (no-op when empty/off).
        thermal_as_revenue_per_mw_yr: ``{fuel_type: $/MW-yr}`` AS credit
            derived from the co-opt's reserve duals under
            ``ercot_thermal_as_endogenous`` (rule 19). When supplied it
            REPLACES the exogenous ``as_revenue_per_mw_yr`` for thermal
            candidates. ``None`` (the default, flag off) keeps the exogenous
            flat rate.
        reserve_price_signal: Hourly ``(T,)`` reserve price for synchronized
            reserve-eligible candidates (plan §5 step 2). A thermal
            candidate's hourly value becomes ``max(0, price - vc, r)`` —
            energy or reserve, never both on the same MW — and it is then
            the SOLE thermal AS pricing (rule 19: the annual endogenous and
            exogenous credits are suppressed). ``None`` keeps the legacy
            price-duration integral + annual AS credit.
        reserve_price_signal_slow: Hourly ``(T,)`` reserve price for the
            offline-capable quick-start tier (gas_ct — Non-Spin only).
        zone_names: Model zone ordering of the rows of ``prices`` /
            ``wind_cf`` / ``solar_cf``, so a VRE candidate's build zone can
            be indexed.
        wind_cf, solar_cf: Zonal hourly CF profiles ``(n_zones, T)``. When
            available, a wind/solar candidate's expected revenue is its
            build zone's hourly CF dotted against that zone's prices — the
            candidate's actual capture shape, including its share of
            scarcity-priced hours — instead of the shape-blind flat mean
            (plan §6 CX-6c). ``None`` keeps the scalar base-CF screen.
        reserve_position: System accredited reserve position for the CR-1
            sloped capacity demand curve (see
            :func:`capacity_reserve_position`). ``None`` / gate off keeps the
            fixed net-CONE capacity payment thermal entry sees (byte-identical);
            when supplied and ``capacity_market_clearing`` is on, the capacity
            payment for a new thermal unit slides along the ISO's demand curve.
        screen_ledger: Optional diagnostic sink (RC-0C / BLK-8). When a list is
            supplied, one fully-decomposed row per *candidate* technology (every
            candidate screened, not just the ones that clear) is appended:
            the revenue terms (``energy``/``attribute``/``capacity`` $/MW-yr),
            the cost terms (base/Wright/post-ITC capex, CRF, FOM, annualized
            fixed cost), the capacity factor used, the profitability margin, and
            the queue-cap binding state / MW actually built. **Diagnostic only —
            it has no effect on the retire/build decision** (nothing reads it
            back); ``None`` (the default) records nothing and is byte-identical
            to the pre-instrumentation path. Wired from ``evolve_fleet`` under
            ``ScenarioConfig.entry_screen_diagnostics`` (default off) so the
            per-candidate entry economics land in ``evolution_<year>.json``.

    Returns:
        Tuple ``(fleet, renewable_additions)`` -- the fleet with entering
        thermal generators appended, and a ``{zone: {fuel: mw}}`` dict of
        wind/solar build MW to fold into the zonal renewable capacity.
    """
    # RC-0C diagnostic accumulator: {tech: row}. Populated only when a
    # ``screen_ledger`` sink is supplied; every read below is guarded by
    # ``_diag`` so the decision path is untouched when diagnostics are off.
    _diag = screen_ledger is not None
    _rows: dict[str, dict] = {}
    iso_config = get_iso_config(iso)
    # Fail loudly when an ISO lacks queue-cap data: a silent default of
    # zero would suppress all new entry and quietly break every forecast.
    if iso_config.name not in QUEUE_CAP_GW:
        raise KeyError(
            f"QUEUE_CAP_GW has no entry for {iso_config.name!r}; economic "
            "new entry cannot run. Add the ISO's annual interconnection-"
            "queue cap to config/constants.py."
        )
    if iso_config.name not in QUEUE_CAP_PER_TECH_GW:
        raise KeyError(
            f"QUEUE_CAP_PER_TECH_GW has no entry for {iso_config.name!r}; "
            "every per-tech cap would default to zero and no capacity "
            "would ever build. Add the ISO's per-technology queue caps to "
            "config/constants.py."
        )
    queue_budget_mw = QUEUE_CAP_GW[iso_config.name] * 1000.0
    per_tech_cap_gw = QUEUE_CAP_PER_TECH_GW[iso_config.name]
    zone = _default_build_zone(iso_config)
    # Locational gate: new thermal built into a zone already long on deliverable
    # firm capacity vs its requirement earns no capacity payment (RA saturated
    # there), so new entry is not pulled forward where the zone is already
    # adequate. No-op unless capacity_deliverability_limits is on.
    build_zone_long = _zone_is_long(deliverability_headroom, zone)

    margins: list[tuple[float, str]] = []
    for tech in _new_entry_candidates(year, config, iso_config.name):
        # Emerging technologies are costed through their own LCOE path.
        if tech in _EMERGING_AVAILABLE_YEAR:
            cf = _emerging_screen_cf(tech, iso_config.name, config)
            lcoe = _emerging_lcoe(
                tech,
                year,
                config,
                iso_config.name,
                cf,
                gas_price_per_mmbtu,
                carbon_price,
            )
            revenue = estimate_expected_revenue(prices, cf)
            # Emerging clean resources also earn an attribute payment: the
            # higher of their exogenous EAC and the RPS shadow price.
            rps_for_tech = rps_shadow_price if tech in _RENEWABLE_NEW_FUELS else 0.0
            effective_attribute_price = max(
                get_eac_price_for_new_entry(tech, config), rps_for_tech
            )
            attribute_rev = 0.0
            if effective_attribute_price > 0.0:
                attribute_rev = effective_attribute_price * cf * HOURS_PER_YEAR
                revenue += attribute_rev
            annual_cost_emerging = lcoe * HOURS_PER_YEAR * cf
            margin = revenue - annual_cost_emerging
            if margin > 0.0:
                margins.append((margin, tech))
            if _diag:
                _rows[tech] = {
                    "tech": tech,
                    "kind": "emerging",
                    "cf_screen": float(cf),
                    "energy_revenue_per_mw_yr": float(revenue - attribute_rev),
                    "attribute_revenue_per_mw_yr": float(attribute_rev),
                    "attribute_price": float(effective_attribute_price),
                    "capacity_revenue_per_mw_yr": 0.0,
                    "lcoe_per_mwh": float(lcoe),
                    "annual_cost_per_mw_yr": float(annual_cost_emerging),
                    "total_revenue_per_mw_yr": float(revenue),
                    "margin_per_mw_yr": float(margin),
                    "profitable": bool(margin > 0.0),
                }
            continue

        base_cf = NEW_ENTRY_COSTS[tech]["base_cf"]
        cum_gw = cumulative.get(tech) if cumulative else None

        if tech in _THERMAL_FOM:
            # Dispatchable thermal (gas_cc, gas_ct): a price-taking unit runs
            # only when the clearing price clears its marginal cost, so its
            # expected energy margin is the price-duration integral
            # sum_t max(price_t - var_cost, 0) per MW -- which counts the
            # scarcity-tail hours where a peaker earns the bulk of its margin.
            # Compared against the unit's annualized FIXED cost (capex annuity
            # + FOM), this is the net-revenue-vs-CONE test. The old flat
            # base_cf x mean(price) understated peakers ~severalfold by
            # ignoring the price shape.
            heat_rate_bins = HEAT_RATE_BINS.get(tech, {})
            best_hr = min(heat_rate_bins.values()) if heat_rate_bins else 0.0
            co2_bins = CO2_RATES.get(tech, {})
            best_co2 = min(co2_bins.values()) if co2_bins else 0.0
            var_cost = (
                best_hr * gas_price_per_mmbtu + VOM[tech] + best_co2 * carbon_price
            )
            price_hourly = (
                np.asarray(prices, dtype=float).mean(axis=0)
                if np.asarray(prices).ndim > 1
                else np.asarray(prices, dtype=float)
            )
            # Reserve tier (plan §5 step 2): a candidate's hourly value is its
            # best use — energy margin or the reserve price, never both on
            # the same MW. A new CT is an offline-capable quick-start
            # (Non-Spin tier); a new CC is synchronized (all products).
            r_tech: np.ndarray | None = None
            if reserve_price_signal is not None and tech in RESERVE_FUEL_TYPES:
                r_tech = (
                    reserve_price_signal_slow
                    if tech in QUICK_START_FUEL_TYPES
                    else reserve_price_signal
                )
                if r_tech is None:
                    r_tech = np.zeros_like(reserve_price_signal)
            hourly_value = np.maximum(price_hourly - var_cost, 0.0)
            if r_tech is not None:
                n = min(hourly_value.size, r_tech.size)
                hourly_value = np.maximum(hourly_value[:n], r_tech[:n])
            energy_margin = float(hourly_value.sum())
            # Annualized fixed cost ($/MW-yr): Wright-adjusted capex annuity +
            # FOM. Thermal carries no IRA ITC/PTC, so this is the clean CONE.
            costs = resolve_new_entry_costs(config)[tech]
            capex_per_kw = costs["capex_per_kw"]
            ref_gw = WRIGHT_REFERENCE_GW.get(tech)
            if cum_gw is not None and ref_gw is not None:
                capex_per_kw = wright_cost(
                    capex_per_kw, cum_gw, ref_gw, costs["learning_rate"]
                )
            crf = _capital_recovery_factor(
                config.real_discount_rate, costs["lifetime_yr"]
            )
            fixed_cost = (capex_per_kw * crf + costs["fom_per_kw_yr"]) * 1000.0
            # Module M1 capacity payment (0 in ERCOT) + ERCOT AS revenue, the
            # same streams credited in the retirement screen above.
            capacity_payment = (
                0.0
                if build_zone_long
                else capacity_revenue_per_mw_yr(
                    iso_config.name, tech, EFORD[tech], config, reserve_position
                )
            )
            # AS credit — exactly one mechanism prices thermal AS (rule 19):
            # the hourly reserve signal (already folded into energy_margin as
            # max(energy, reserve)) suppresses both annual credits; else the
            # per-fuel co-opt rate under ercot_thermal_as_endogenous; else
            # the exogenous flat rate.
            if r_tech is not None:
                as_credit = 0.0  # hourly max above is the sole AS pricing
            elif thermal_as_revenue_per_mw_yr is not None:
                as_credit = thermal_as_revenue_per_mw_yr.get(tech, 0.0)
            else:
                as_credit = as_revenue_per_mw_yr(tech, storage_power_mw, config)
            effective_revenue = energy_margin + capacity_payment + as_credit
            margin = effective_revenue - fixed_cost
            if margin > 0.0:
                margins.append((margin, tech))
            if _diag:
                _rows[tech] = {
                    "tech": tech,
                    "kind": "thermal",
                    "energy_revenue_per_mw_yr": float(energy_margin),
                    "attribute_revenue_per_mw_yr": 0.0,
                    "capacity_revenue_per_mw_yr": float(capacity_payment),
                    "as_credit_per_mw_yr": float(as_credit),
                    "var_cost_per_mwh": float(var_cost),
                    "capex_base_per_kw": float(costs["capex_per_kw"]),
                    "capex_wright_per_kw": float(capex_per_kw),
                    "capex_after_credit_per_kw": float(capex_per_kw),
                    "crf": float(crf),
                    "fom_per_kw_yr": float(costs["fom_per_kw_yr"]),
                    "cumulative_gw": (float(cum_gw) if cum_gw is not None else None),
                    "annual_cost_per_mw_yr": float(fixed_cost),
                    "total_revenue_per_mw_yr": float(effective_revenue),
                    "margin_per_mw_yr": float(margin),
                    "profitable": bool(margin > 0.0),
                }
            continue

        # Non-dispatchable / must-run candidates (wind, solar, nuclear_smr):
        # value the CF-shaped output at the expected price and net the
        # levelized cost; clean attributes (EAC or RPS shadow price, the
        # higher, never stacked) lift RPS-eligible renewables.
        lcoe = compute_lcoe(tech, year, config, cumulative_gw=cum_gw)
        # Shape-aware VRE revenue (plan §6 CX-6c): value the candidate's
        # build zone's hourly CF against THAT zone's prices, so solar sees
        # its own value cannibalization and wind its diurnal/seasonal
        # capture rate — including each one's actual share of the
        # scarcity-priced hours the flat mean smears across the year. Falls
        # back to the scalar base-CF screen when profiles/zone ordering are
        # unavailable (older callers) or the build zone has no resource.
        cf_profile: np.ndarray | None = None
        prices_for_rev: np.ndarray = prices
        if tech in _RENEWABLE_NEW_FUELS and zone_names:
            cf_zonal = wind_cf if tech == "wind" else solar_cf
            target_zone = get_renewable_zone(iso_config.name, tech)
            prices_arr = np.asarray(prices, dtype=float)
            if (
                cf_zonal is not None
                and target_zone in zone_names
                and prices_arr.ndim == 2
            ):
                zi = zone_names.index(target_zone)
                cf_arr = np.asarray(cf_zonal, dtype=float)
                if (
                    cf_arr.ndim == 2
                    and zi < cf_arr.shape[0]
                    and zi < prices_arr.shape[0]
                    and float(cf_arr[zi].max()) > 0.0
                ):
                    cf_profile = cf_arr[zi]
                    prices_for_rev = prices_arr[zi]
        if cf_profile is not None:
            effective_revenue = estimate_expected_revenue(prices_for_rev, cf_profile)
            cf_expected = float(cf_profile.mean())
        else:
            effective_revenue = estimate_expected_revenue(prices, base_cf)
            cf_expected = base_cf
        rps_for_tech = rps_shadow_price if tech in _RENEWABLE_NEW_FUELS else 0.0
        effective_attribute_price = max(
            get_eac_price_for_new_entry(tech, config), rps_for_tech
        )
        if effective_attribute_price > 0.0:
            effective_revenue += (
                effective_attribute_price * cf_expected * HOURS_PER_YEAR
            )
        # lcoe uses base_cf internally, so lcoe x hours x base_cf is the
        # CF-independent annualized fixed cost in $/MW-yr — it stays on
        # base_cf even when the revenue side uses the zonal profile.
        annual_cost = lcoe * HOURS_PER_YEAR * base_cf
        energy_only_rev = effective_revenue - (
            effective_attribute_price * cf_expected * HOURS_PER_YEAR
            if effective_attribute_price > 0.0
            else 0.0
        )
        margin = effective_revenue - annual_cost
        if margin > 0.0:
            margins.append((margin, tech))
        if _diag:
            # Re-derive the capex decomposition with the SAME helpers
            # compute_lcoe uses (no drift): base -> Wright -> ITC. VRE earns
            # no capacity payment here (BLK-7 / term c) — recorded as an
            # explicit 0.0 so the zero is measured, not inferred.
            _costs = resolve_new_entry_costs(config)[tech]
            _capex_base = _costs["capex_per_kw"]
            _capex_wright = _capex_base
            _ref_gw = WRIGHT_REFERENCE_GW.get(tech)
            if cum_gw is not None and _ref_gw is not None:
                _capex_wright = wright_cost(
                    _capex_base, cum_gw, _ref_gw, _costs["learning_rate"]
                )
            _capex_after_itc = _capex_wright
            if tech == "solar" and year <= config.ira_wind_solar_last_year:
                _capex_after_itc = _capex_wright * (1.0 - config.ira_itc_solar)
            _crf = _capital_recovery_factor(
                config.real_discount_rate, _costs["lifetime_yr"]
            )
            _rows[tech] = {
                "tech": tech,
                "kind": "vre" if tech in _RENEWABLE_NEW_FUELS else "must_run",
                "cf_base": float(base_cf),
                "cf_expected": float(cf_expected),
                "cf_shape_aware": bool(cf_profile is not None),
                "energy_revenue_per_mw_yr": float(energy_only_rev),
                "attribute_revenue_per_mw_yr": float(
                    effective_revenue - energy_only_rev
                ),
                "attribute_price": float(effective_attribute_price),
                "rps_shadow_price": float(rps_shadow_price),
                "capacity_revenue_per_mw_yr": 0.0,
                "capex_base_per_kw": float(_capex_base),
                "capex_wright_per_kw": float(_capex_wright),
                "capex_after_credit_per_kw": float(_capex_after_itc),
                "itc_solar": float(
                    config.ira_itc_solar
                    if tech == "solar" and year <= config.ira_wind_solar_last_year
                    else 0.0
                ),
                "ptc_wind": float(
                    config.ira_ptc_wind
                    if tech == "wind" and year <= config.ira_wind_solar_last_year
                    else 0.0
                ),
                "crf": float(_crf),
                "fom_per_kw_yr": float(_costs["fom_per_kw_yr"]),
                "cumulative_gw": (float(cum_gw) if cum_gw is not None else None),
                "lcoe_per_mwh": float(lcoe),
                "annual_cost_per_mw_yr": float(annual_cost),
                "total_revenue_per_mw_yr": float(effective_revenue),
                "margin_per_mw_yr": float(margin),
                "profitable": bool(margin > 0.0),
            }

    margins.sort(reverse=True)

    new_fleet = list(fleet)
    renewable_additions: dict[str, dict[str, float]] = {}
    remaining = queue_budget_mw
    # Per-tech queue caps are tracked per cap group: hydrogen turbines and
    # CCUS share the ``gas_cc`` group, so their builds compete for one cap.
    group_remaining: dict[str, float] = {}
    for seq, (_, tech) in enumerate(margins):
        if remaining <= 0.0:
            if _diag and tech in _rows:
                _rows[tech]["build_mw"] = 0.0
                _rows[tech]["binding_cap"] = "iso_budget_exhausted"
            continue
        # Each tech is capped by its (possibly shared) per-tech queue limit
        # and by what is left of the shared ISO budget; both bind.
        group = _QUEUE_CAP_GROUP.get(tech, tech)
        if group not in group_remaining:
            group_remaining[group] = per_tech_cap_gw.get(group, 0.0) * 1000.0
        build_mw = min(group_remaining[group], remaining)
        if build_mw <= 0.0:
            if _diag and tech in _rows:
                _rows[tech]["build_mw"] = 0.0
                _rows[tech]["binding_cap"] = "per_tech_cap_zero"
            continue
        remaining -= build_mw
        group_remaining[group] -= build_mw
        if _diag and tech in _rows:
            _rows[tech]["build_mw"] = float(build_mw)
            _rows[tech]["binding_cap"] = (
                "per_tech_cap"
                if build_mw >= per_tech_cap_gw.get(group, 0.0) * 1000.0 - 1e-6
                else "iso_budget"
            )
        if tech in _RENEWABLE_NEW_FUELS:
            target_zone = get_renewable_zone(iso_config.name, tech)
            zone_acc = renewable_additions.setdefault(target_zone, {})
            zone_acc[tech] = zone_acc.get(tech, 0.0) + build_mw
        else:
            new_fleet.append(
                _make_new_generator(
                    tech, build_mw, zone, year, seq, config, iso_config.name
                )
            )

    if _diag:
        # Unprofitable candidates never enter the margins loop; record their
        # zero build and the ISO-level caps once per row, then flush.
        for tech, row in _rows.items():
            row.setdefault("build_mw", 0.0)
            row.setdefault(
                "binding_cap", "unprofitable" if not row["profitable"] else "none"
            )
            row["queue_budget_gw"] = float(queue_budget_mw / 1000.0)
            row["per_tech_cap_gw"] = float(
                per_tech_cap_gw.get(_QUEUE_CAP_GROUP.get(tech, tech), 0.0)
            )
        screen_ledger.extend(_rows[t] for _, t in margins if t in _rows)
        screen_ledger.extend(
            row for tech, row in _rows.items() if not any(tech == t for _, t in margins)
        )

    return new_fleet, renewable_additions


def _renewable_nameplate_by_fuel(
    fleet: list[Generator],
    wind_pool_mw: float,
    solar_pool_mw: float,
    iso: str | None,
) -> dict[str, float]:
    """ISO-wide installed nameplate MW per credit-accredited class.

    The penetration axis for the published ELCC curves (rule 13 — the
    model's own installed share): each class's zonal pool plus any fleet
    units carrying a credit-bearing fuel type. One computation shared by
    :func:`accredited_firm_capacity_mw` and
    :func:`renewable_credits_applied` so the ledger and its diagnostics can
    never disagree on the penetration basis.
    """
    nameplate_by_fuel: dict[str, float] = {
        "wind": float(wind_pool_mw),
        "solar": float(solar_pool_mw),
    }
    for g in fleet:
        if (
            g.fuel_type in RENEWABLE_CAPACITY_CREDIT
            or g.fuel_type in RENEWABLE_ELCC_CURVES_BY_ISO.get(iso or "", {})
        ):
            nameplate_by_fuel[g.fuel_type] = nameplate_by_fuel.get(
                g.fuel_type, 0.0
            ) + float(g.pmax_mw)
    return nameplate_by_fuel


def renewable_credits_applied(
    fleet: list[Generator],
    wind_pool_mw: float,
    solar_pool_mw: float,
    iso: str | None,
    peak_demand_mw: float | None = None,
    elcc_curves_enabled: bool = False,
) -> dict[str, float]:
    """Resolved wind/solar credits on the ledger's exact basis (diagnostic).

    The same resolution :func:`accredited_firm_capacity_mw` applies —
    same nameplate computation, same ladder — surfaced so the evolution
    ledger can record the credit each class actually earned this year
    (the CR-3.1 penetration response made observable per run, e.g. for the
    capacity-hindcast before/after diagnostic).
    """
    nameplate_by_fuel = _renewable_nameplate_by_fuel(
        fleet, wind_pool_mw, solar_pool_mw, iso
    )
    out: dict[str, float] = {}
    for fuel_type in ("wind", "solar"):
        credit = resolve_renewable_capacity_credit(
            fuel_type,
            iso,
            installed_mw=nameplate_by_fuel.get(fuel_type),
            peak_demand_mw=peak_demand_mw,
            curves_enabled=elcc_curves_enabled,
        )
        if credit is not None:
            out[fuel_type] = float(credit)
    return out


def accredited_firm_capacity_mw(
    fleet: list[Generator],
    wind_pool_mw: float = 0.0,
    solar_pool_mw: float = 0.0,
    storage_firm_mw: float = 0.0,
    iso: str | None = None,
    peak_demand_mw: float | None = None,
    elcc_curves_enabled: bool = False,
) -> float:
    """Return the system's accredited firm (ELCC/UCAP) capacity in MW.

    Each resource contributes the firm fraction of its nameplate it can be
    relied on for at the system peak, on the ISO's own published counting
    convention when ``iso`` is given: thermal at ``1 - EFORd`` (UCAP) or at
    its seasonal rating (:func:`_thermal_firm_mw` /
    :data:`THERMAL_ACCREDITATION_BASIS_BY_ISO` — ERCOT's CDR basis),
    variable renewables at their capacity credit
    (:func:`resolve_renewable_capacity_credit` — penetration-indexed
    published ELCC curve when ``elcc_curves_enabled``, per-ISO point
    override, generic :data:`RENEWABLE_CAPACITY_CREDIT` fallback), storage
    at its duration-dependent ELCC (passed in pre-accredited as
    ``storage_firm_mw``, since the ELCC helper lives in the storage module),
    plus any asynchronous-tie firm import the ISO's ledger counts but the
    model topology lacks (:data:`ADEQUACY_EXTERNAL_TIE_FIRM_MW`). Wind/solar
    held in the zonal pools (not Generators) are passed as ``wind_pool_mw``
    / ``solar_pool_mw``.

    For the CR-3.1 curves each credit-accredited class's penetration is its
    ISO-WIDE installed nameplate — the zonal pool plus any fleet units of
    that fuel — against ``peak_demand_mw``, both the model's own quantities
    (rule 13). One credit per class per call: every MW of a class is
    accredited at the same class rating, exactly the ISOs' own class-rating
    construction. ``iso=None`` reproduces the legacy generic basis
    byte-identically (UCAP thermal, generic credits, no tie MW), and
    ``elcc_curves_enabled=False`` (or an unavailable axis quantity) is the
    frozen-penetration byte-compat mode — the pre-CR-3.1 point basis.
    """
    nameplate_by_fuel = _renewable_nameplate_by_fuel(
        fleet, wind_pool_mw, solar_pool_mw, iso
    )

    def _credit(fuel_type: str) -> float | None:
        return resolve_renewable_capacity_credit(
            fuel_type,
            iso,
            installed_mw=nameplate_by_fuel.get(fuel_type),
            peak_demand_mw=peak_demand_mw,
            curves_enabled=elcc_curves_enabled,
        )

    firm = float(storage_firm_mw)
    firm += wind_pool_mw * (_credit("wind") or 0.0)
    firm += solar_pool_mw * (_credit("solar") or 0.0)
    if iso is not None:
        firm += ADEQUACY_EXTERNAL_TIE_FIRM_MW.get(iso, 0.0)
    for g in fleet:
        credit = _credit(g.fuel_type)
        if credit is not None:
            firm += g.pmax_mw * credit
        else:
            firm += _thermal_firm_mw(g, iso)
    return firm


def capacity_reserve_position(
    fleet: list[Generator],
    wind_pool_mw: float,
    solar_pool_mw: float,
    storage_firm_mw: float,
    config: ScenarioConfig,
    iso: str,
    peak_demand_mw: float,
    year: int | None = None,
) -> float | None:
    """Return the system's accredited reserve position for the CR-1 curve.

    ``accredited_firm_capacity_mw / resolve_adequacy_requirement_mw`` — the
    SAME accreditation ledger and the SAME requirement the retirement
    reliability floor and the reserve-margin backstop already compute (one
    requirement, one basis, rule 19), so the sloped-demand-curve position feeds
    the three capacity screens off a signal consistent with the adequacy
    mechanisms it sits beside. A value of ``1.0`` means the accredited fleet is
    exactly at the requirement (curve pays net-CONE); ``> 1.0`` is long (price
    slides toward zero), ``< 1.0`` is short (price rises toward the cap).

    ``year`` is threaded to the requirement resolver so a published Forecast
    Pool Requirement of the matching delivery year devintages the position's
    denominator (R2); ``None`` keeps the fallback ``(1 + PRM) x ratio``.

    Returns ``None`` when the peak or the requirement is non-positive, so the
    caller (and ``MarketDesign.capacity_price_per_firm_mw_yr``) cleanly falls
    back to the fixed price. Consumed only when
    ``config.capacity_market_clearing`` is on; the runner computes it once on
    the entering-year fleet and threads the one value into all three screens.
    """
    if peak_demand_mw <= 0.0:
        return None
    requirement_mw = resolve_adequacy_requirement_mw(config, iso, peak_demand_mw, year)
    if requirement_mw <= 0.0:
        return None
    accredited_mw = accredited_firm_capacity_mw(
        fleet,
        wind_pool_mw,
        solar_pool_mw,
        storage_firm_mw,
        iso=iso,
        peak_demand_mw=peak_demand_mw,
        elcc_curves_enabled=config.renewable_elcc_curves,
    )
    return accredited_mw / requirement_mw


def resolve_reserve_margin_build_enabled(config: ScenarioConfig, iso: str) -> bool:
    """Resolve whether the reserve-margin adequacy backstop fires for ``iso``.

    Market-design-dependent resolution (G-41, PJM hindcast I7 decision
    2026-07-06 — owner-approved market-design-dependent variant). The
    ``ScenarioConfig.reserve_margin_build_enabled`` field is tri-state:

    * ``True`` / ``False`` — explicit override, honoured verbatim (rule 21: the
      knob lands in ``run_config.json`` and a scenario can force it either way).
    * ``None`` (default) — resolve per market design: ON when the ISO's design
      procures capacity to an adequacy requirement
      (``MARKET_DESIGN[iso].capacity_market`` — PJM/MISO/NYISO/NEISO/CAISO; the
      LP analogue of RPM's absolute-IRM procurement), OFF for energy-only ERCOT
      and for ISOs absent from :data:`MARKET_DESIGN` (conservative — the real
      energy-only market has no absolute reliability floor: an under-remunerated
      unit exits and ORDC/scarcity prices the resulting adequacy, so a
      force-build backstop would manufacture firm MW the market never procures,
      rule 1).

    Energy-only ERCOT and any ``None``-default forecast on an unknown ISO
    resolve OFF, so the pre-G-41 default-off behaviour is byte-identical there;
    the capacity-market ISOs are where the backstop newly engages by default.

    Args:
        config: Scenario config carrying the tri-state override field.
        iso: ISO identifier.

    Returns:
        ``True`` if the backstop should fire, else ``False``.
    """
    override = config.reserve_margin_build_enabled
    if override is not None:
        return bool(override)
    design = MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN)
    return bool(design.capacity_market)


def apply_reserve_margin_build(
    fleet: list[Generator],
    firm_capacity_mw: float,
    peak_demand_mw: float,
    year: int,
    config: ScenarioConfig,
    iso: str,
) -> tuple[list[Generator], float]:
    """Force-build firm capacity to meet the planning reserve margin.

    The structural adequacy backstop (ReEDS/NEMS/CDR): after the economic
    new-entry screen, if accredited firm capacity is below the shared
    requirement (:func:`resolve_adequacy_requirement_mw` — firm peak x
    (1 + PRM) on the ISO's own counting convention) the residual gap is
    filled with the cheapest firm dispatchable resource (a ``gas_ct``
    peaker), so adequacy holds even when under-priced energy/scarcity
    revenue would otherwise under-build. The economic screen still owns the
    profitable build; this only covers the shortfall.

    Sized on nameplate (the gap is a firm-MW gap, so nameplate =
    gap / (1 - EFORd_gas_ct) for UCAP-basis ISOs, gap itself for
    seasonal-rating ISOs). The build is capped at the ISO's annual
    interconnection-queue throughput so a single year cannot add unbounded
    capacity. Returns ``(fleet, built_mw)``; a no-op (built 0) when disabled,
    when the margin is already met, or when the queue cap is exhausted.
    """
    if not resolve_reserve_margin_build_enabled(config, iso) or peak_demand_mw <= 0.0:
        return fleet, 0.0
    # Shared requirement resolution (one requirement, two verbs — plan §3.2):
    # the same firm-peak x (1 + PRM) construction the retirement reliability
    # floor uses, on the ISO's own counting convention.
    required = resolve_adequacy_requirement_mw(config, iso, peak_demand_mw, year)
    firm_gap = required - firm_capacity_mw
    if firm_gap <= 0.0:
        return fleet, 0.0

    # Nameplate needed to close a firm-MW gap, on the ISO's accreditation
    # basis: seasonal-rating ISOs count the new CT at nameplate; UCAP ISOs
    # derate it by EFORd.
    if THERMAL_ACCREDITATION_BASIS_BY_ISO.get(iso) == "seasonal_rating":
        credit = 1.0
    else:
        credit = 1.0 - EFORD["gas_ct"]
    nameplate_needed = firm_gap / credit if credit > 0.0 else firm_gap
    iso_config = get_iso_config(iso)
    queue_cap_mw = QUEUE_CAP_GW.get(iso_config.name, 0.0) * 1000.0
    build_mw = (
        min(nameplate_needed, queue_cap_mw) if queue_cap_mw > 0.0 else nameplate_needed
    )
    if build_mw <= 0.0:
        return fleet, 0.0

    zone = _default_build_zone(iso_config)
    unit = _make_new_generator(
        "gas_ct", build_mw, zone, year, 0, config, iso_config.name
    )
    unit.unit_id = f"gas_ct_adequacy_{year}"
    unit.name = unit.unit_id
    return fleet + [unit], build_mw


def _adjust_retrofit_capex(base_capex_kw: float, cumulative_gw: float | None) -> float:
    """Apply Wright's Law to CCS retrofit capex.

    Uses the same learning rate and reference GW as new-build CCS --
    the capture equipment manufacturing base is shared.

    Args:
        base_capex_kw: Base retrofit capex in $/kW (from config).
        cumulative_gw: Current cumulative global CCS deployment in GW.

    Returns:
        Adjusted retrofit capex in $/kW.
    """
    if cumulative_gw is None or cumulative_gw <= 0:
        return base_capex_kw

    ccs_params = NEW_ENTRY_COSTS.get("gas_cc_ccs", {})
    lr = ccs_params.get("learning_rate", 0.10)
    ref_gw = WRIGHT_REFERENCE_GW.get("gas_cc_ccs", 2.0)

    if cumulative_gw <= ref_gw:
        return base_capex_kw

    return wright_cost(base_capex_kw, cumulative_gw, ref_gw, lr)


def apply_ccs_retrofit(
    fleet: list[Generator],
    prices: np.ndarray,
    year: int,
    config: ScenarioConfig,
    iso: str,
    gas_price_per_mmbtu: float,
    carbon_price: float,
    eac_price_ccs: float = 0.0,
    cumulative: CumulativeDeployment | None = None,
) -> tuple[list[Generator], list[dict]]:
    """Screen existing gas CC units for CCS retrofit economics.

    A retrofit converts a ``gas_cc`` generator to ``gas_cc_ccs`` in place.
    The unit keeps its zone, capacity and ``unit_id`` but gets:

    * ``heat_rate *= (1 + config.ccs_retrofit_hr_penalty)`` -- the retrofit
      heat rate is *derived* from the source unit's heat rate, never a fixed
      bin, so an efficient host stays efficient after capture,
    * ``vom += config.ccs_retrofit_vom_adder``,
    * ``emission_rate_co2 *= (1 - config.ccs_retrofit_capture_rate)``,
    * ``fuel_type`` changes to ``"gas_cc_ccs"``.

    A unit retrofits when the simple payback of the retrofit capex is shorter
    than its remaining useful life. Annual net savings per MW are::

        carbon_avoided = (old_er - new_er) * carbon_price * cf * 8760
        eac_revenue    = eac_price_ccs * cf * 8760
        margin_loss    = (new_hr - old_hr) * gas_price * cf * 8760
        vom_increase   = vom_adder * cf * 8760
        annual_net_savings = carbon_avoided + eac_revenue
                             - margin_loss - vom_increase

    Units younger than ``config.ccs_retrofit_min_remaining_life`` years from
    end of life are skipped, candidates are ranked shortest-payback first
    (efficient hosts win), and retrofits are applied up to the annual
    throughput cap ``config.ccs_retrofit_max_gw_per_year``.

    Args:
        fleet: Current generator fleet.
        prices: ``(n_zones, T)`` zonal price array from the prior year.
            Reserved for a future per-unit capacity-factor estimate; the
            current screen uses a representative capacity factor.
        year: Current simulation year.
        config: Scenario configuration.
        iso: ISO identifier (reserved for future per-ISO calibration).
        gas_price_per_mmbtu: Resolved gas price for this year.
        carbon_price: Resolved carbon price for this year ($/ton CO2).
        eac_price_ccs: EAC price for CCS resources ($/MWh).
        cumulative: Global cumulative deployment tracker. When supplied,
            the retrofit capex follows the shared CCS Wright's-Law learning
            curve, and the retrofitted GW is added back to the tracker --
            a retrofit grows the capture-equipment experience base.

    Returns:
        Tuple ``(updated_fleet, retrofit_log)`` where ``retrofit_log`` is a
        list of dicts recording each retrofit decision for diagnostics.
    """
    if year < config.ccs_retrofit_available_year:
        return fleet, []

    hours = float(HOURS_PER_YEAR)
    cf = _RETROFIT_SCREEN_CF
    # The capture island is the same equipment whether bolted onto an
    # existing plant or built new, so retrofit capex shares the new-build
    # CCS learning curve.
    adjusted_capex_kw = _adjust_retrofit_capex(
        config.ccs_retrofit_capex_kw,
        cumulative.get("gas_cc_ccs") if cumulative else None,
    )
    retrofit_capex_per_mw = adjusted_capex_kw * 1000.0

    candidates: list[tuple[float, Generator, dict]] = []
    for gen in fleet:
        if gen.fuel_type != "gas_cc":
            continue
        # Skip units near end of life -- a short remaining life cannot pay
        # back the retrofit capex.
        age = year - gen.online_year
        remaining_life = max(0, _THERMAL_PLANT_LIFE_YEARS - age)
        if remaining_life < config.ccs_retrofit_min_remaining_life:
            continue

        old_hr = gen.heat_rate
        new_hr = old_hr * (1.0 + config.ccs_retrofit_hr_penalty)
        old_er = gen.emission_rate_co2
        new_er = old_er * (1.0 - config.ccs_retrofit_capture_rate)

        # Annual economics per MW of capacity.
        carbon_avoided = (old_er - new_er) * carbon_price * cf * hours
        eac_revenue = eac_price_ccs * cf * hours
        margin_loss = (new_hr - old_hr) * gas_price_per_mmbtu * cf * hours
        vom_increase = config.ccs_retrofit_vom_adder * cf * hours
        annual_net_savings = carbon_avoided + eac_revenue - margin_loss - vom_increase
        if annual_net_savings <= 0.0:
            continue

        payback_years = retrofit_capex_per_mw / annual_net_savings
        if payback_years >= remaining_life:
            continue

        candidates.append(
            (
                payback_years,
                gen,
                {
                    "unit_id": gen.unit_id,
                    "zone": gen.zone,
                    "old_hr": old_hr,
                    "new_hr": new_hr,
                    "old_emission_rate": old_er,
                    "new_emission_rate": new_er,
                    "annual_net_savings_per_mw": annual_net_savings,
                    "payback_years": payback_years,
                    "carbon_price": carbon_price,
                },
            )
        )

    # Shortest payback first -- the best-economics (most efficient) hosts win.
    candidates.sort(key=lambda item: item[0])

    cap_mw = config.ccs_retrofit_max_gw_per_year * 1000.0
    retrofitted_mw = 0.0
    retrofit_log: list[dict] = []
    for _payback, gen, log_entry in candidates:
        if retrofitted_mw + gen.pmax_mw > cap_mw:
            continue
        # Convert the generator in place -- a retrofit is irreversible.
        gen.heat_rate = gen.heat_rate * (1.0 + config.ccs_retrofit_hr_penalty)
        gen.vom = gen.vom + config.ccs_retrofit_vom_adder
        gen.emission_rate_co2 = gen.emission_rate_co2 * (
            1.0 - config.ccs_retrofit_capture_rate
        )
        gen.fuel_type = "gas_cc_ccs"
        retrofitted_mw += gen.pmax_mw
        retrofit_log.append(log_entry)

    # A retrofit adds to the global CCS manufacturing experience base just
    # like a new build, so feed the retrofitted GW back into the tracker.
    if retrofitted_mw > 0.0 and cumulative is not None:
        cumulative.add("gas_cc_ccs", retrofitted_mw / 1000.0)

    return fleet, retrofit_log


def _prior_attr(prior_results: object, name: str, default: object = None) -> object:
    """Read ``name`` from ``prior_results``, which may be a dict or object."""
    if prior_results is None:
        return default
    if isinstance(prior_results, dict):
        return prior_results.get(name, default)
    return getattr(prior_results, name, default)


def evolve_fleet(
    fleet: list[Generator],
    prior_results: object,
    year: int,
    config: ScenarioConfig,
    loss_tracker: dict[str, int],
    rps_shadow_price: float = 0.0,
    cumulative: CumulativeDeployment | None = None,
    gas_price_per_mmbtu: float = 0.0,
    carbon_price: float = 0.0,
    eac_price_ccs: float = 0.0,
    events: dict | None = None,
    confirmed_exits: list[ConfirmedExit] | None = None,
    peak_demand_next: float | None = None,
    announced_reversal_plants: frozenset[int] = frozenset(),
    reserve_position: float | None = None,
) -> tuple[
    list[Generator],
    dict[str, int],
    dict[str, dict[str, float]],
    list[dict],
    list[dict],
]:
    """Advance the fleet by one simulation year.

    The capacity mechanisms are applied in a fixed order:

    0. confirmed exits (exogenous, any fuel, instrument-bound; gated on
       ``config.confirmed_exits_enabled``, default on),
    1. announced retirements (non-fossil within the data horizon only; announced
       fossil dates are a default no-op — the exogenous fossil channel is step 0),
    2. economic retirements,
    3. known additions (planned units with ``online_year == year``),
    4. CCS retrofits (convert existing gas CC units to ``gas_cc_ccs``),
    5. economic new entry (generation).

    Retrofits run before new entry so a retrofitted CC displaces some of the
    need for new-build CCS: the new-entry screen then sees the updated fleet.

    The reshaped fleet is then re-aggregated into efficiency-bin
    representative units, keeping the next LP solve at ~36 thermal columns.
    When ``config.heat_rate_bin_count`` is set, the re-aggregation uses that
    many equal-width heat-rate bins instead of the predefined vintage bins.

    The renewable portfolio standard is not applied here -- it is enforced
    as an LP constraint in dispatch, and its shadow price
    (``rps_shadow_price``) feeds the economic retirement and new-entry
    screens so clean builds are economics-driven. Storage new entry is
    handled separately in the runner.

    Steps that depend on a price signal -- economic retirements and
    economic new entry -- are skipped when ``prior_results`` carries no
    dispatch outcome (e.g. the first simulated year).

    Args:
        fleet: The fleet at the start of the year.
        prior_results: Prior-year outcome, a dict or object that may expose
            ``fleet_arrays``, ``dispatch_result``, ``prices``,
            ``peak_demand`` and ``planned_additions``. ``None`` skips all
            price-driven steps.
        year: The simulation year being entered.
        config: Scenario config.
        loss_tracker: Per-unit consecutive-loss counters; not mutated in
            place.
        rps_shadow_price: Prior year's RPS shadow price in $/MWh, passed to
            the economic retirement and new-entry screens as the endogenous
            attribute payment (taken as max with the exogenous EAC).
        cumulative: Global cumulative deployment, passed to the new-entry
            screen so candidate capex follows a Wright's-Law learning curve.
        gas_price_per_mmbtu: Delivered gas price for the year, passed to
            the new-entry screen to cost gas CC variable fuel.
        carbon_price: Carbon price in $/tCO2 for the year, passed to the
            new-entry screen to cost thermal carbon emissions and to the
            CCS retrofit screen.
        eac_price_ccs: EAC price for CCS resources in $/MWh, passed to the
            CCS retrofit screen as additional per-MWh revenue.
        events: Optional dict (see
            :func:`market_sim.results.evolution_ledger.new_events`) populated
            in place with the per-year capacity events — retirements
            (known/economic), reliability-floor-retained units, thermal
            additions (planned/economic/reserve_backstop), CCS retrofits,
            renewable additions, and the fleet-by-fuel totals before/after.
            ``None`` records nothing and leaves the solve path byte-identical.
        peak_demand_next: The ENTERING year's known peak demand in MW
            (deterministic from the demand path — plan §2.3 component 1).
            When supplied it replaces the prior-year ``peak_demand`` in the
            peak-anchored adequacy mechanisms (the retirement reliability
            floor and the reserve-margin backstop), deleting their one-year
            bookkeeping lag. ``None`` keeps the prior-year peak.
        announced_reversal_plants: Plant codes whose announced retirement
            was reversed by a public counter-instrument (registry rows all
            superseded) — step 1 ignores their stale EIA-860 dates
            (:func:`apply_announced_retirements`'s ``reversed_plant_codes``).
            Independent of ``confirmed_exits_enabled``: honoring a documented
            reversal is a data correction, not an exit injection.
        reserve_position: System accredited reserve position (accredited firm ÷
            requirement) for the CR-1 sloped capacity demand curve, computed
            once on the entering fleet by the runner (see
            :func:`capacity_reserve_position`) and threaded verbatim into BOTH
            the retirement and thermal-entry screens so all screens share one
            requirement and one basis (rule 19). ``None`` (default) /
            ``capacity_market_clearing`` off keeps the fixed net-CONE capacity
            payment — byte-identical to the pre-CR-1 path.

    Returns:
        Tuple ``(fleet, loss_tracker, renewable_additions, retrofit_log,
        floor_retention_log)`` after all mechanisms are applied.
        ``renewable_additions`` is a ``{zone: {"wind": mw, "solar": mw}}``
        dict of new wind/solar capacity built this year; the caller folds it
        into the zonal ``wind_cap`` / ``solar_cap`` pools that bound the
        ``W[z,t]`` / ``S[z,t]`` dispatch variables. ``retrofit_log`` is the
        list of CCS retrofit decision dicts recorded this year.
        ``floor_retention_log`` is the retirement reliability floor's
        attribution log — one dict per unit the floor un-retired this year
        (persisted per-year by the runner as ``floor_retentions``).
    """
    loss_tracker = dict(loss_tracker)
    renewable_additions: dict[str, dict[str, float]] = {}
    floor_retention_log: list[dict] = []

    # Ledger bookkeeping: snapshot the entering fleet so each mechanism's
    # additions/retirements can be attributed by a before/after diff. No-op
    # (and zero cost beyond a dict build) when ``events`` is None.
    _rec = events is not None
    if _rec:
        from market_sim.results.evolution_ledger import fleet_totals_by_fuel

        events["fleet_by_fuel_before"] = fleet_totals_by_fuel(fleet)

    fleet_arrays = _prior_attr(prior_results, "fleet_arrays")
    dispatch_result = _prior_attr(prior_results, "dispatch_result")
    prices = _prior_attr(prior_results, "prices")
    # Capacity-screen price signal (plan §2.2-§2.3): the EWMA-blended and/or
    # lookahead-repriced series replaces raw prices in the retirement,
    # CCS-retrofit and new-entry screens. At the runner defaults it IS the
    # same econ_prices array (byte-identical); bare-dict callers without the
    # key fall back to prices.
    price_signal = _prior_attr(prior_results, "price_signal", None)
    if price_signal is not None:
        prices = price_signal
    peak_demand = float(_prior_attr(prior_results, "peak_demand", 0.0) or 0.0)
    # Peak used by the peak-anchored adequacy mechanisms (floor + backstop):
    # the entering year's known peak when the runner supplies it (plan §2.3
    # component 1 — deletes a pure one-year bookkeeping lag), else the
    # prior-year peak (legacy behaviour, e.g. older callers/tests).
    peak_demand_used = (
        float(peak_demand_next)
        if peak_demand_next is not None and peak_demand_next > 0.0
        else peak_demand
    )
    planned = _prior_attr(prior_results, "planned_additions", []) or []
    mc_cost = _prior_attr(prior_results, "mc_cost")
    # AS-eligible (storage) fleet power, the AS-revenue saturation driver.
    storage_power_mw = float(_prior_attr(prior_results, "storage_power_mw", 0.0) or 0.0)
    # Prior-year renewable pools and accredited storage ELCC: the reliability
    # floor (step 2) and the adequacy backstop (step 6) test the same
    # accredited-firm-capacity ledger (plan §3.2), so both read these.
    wind_pool_mw = float(_prior_attr(prior_results, "wind_cap_mw", 0.0) or 0.0)
    solar_pool_mw = float(_prior_attr(prior_results, "solar_cap_mw", 0.0) or 0.0)
    # Portfolio ELCC dilution (accreditation audit §3 follow-up): the
    # pre-accredited storage_firm_mw the runner computed carries no
    # penetration term, so it is diluted here — the point evolve_fleet
    # consumes it — rather than in runner.py, whose own persisted ledger
    # value stays undiluted (a parallel lane's file; see
    # _storage_portfolio_elcc_dilution docstring).
    storage_firm_mw = float(_prior_attr(prior_results, "storage_firm_mw", 0.0) or 0.0)
    storage_firm_mw *= _storage_portfolio_elcc_dilution(storage_power_mw, config.iso)
    # Per-fuel thermal AS credit DERIVED from the prior-year co-opt reserve duals,
    # populated by the runner only under ercot_thermal_as_endogenous. When present
    # the retirement/new-entry screens use it in place of the exogenous flat AS
    # rate so exactly one mechanism prices thermal AS (rule 19); None keeps the
    # exogenous rate (byte-identical default).
    thermal_as_revenue_per_mw_yr = (
        _prior_attr(prior_results, "thermal_as_revenue_per_mw_yr", None)
        if getattr(config, "ercot_thermal_as_endogenous", False)
        else None
    )
    # Hourly reserve-price signal (plan §5 step 2, screen_reserve_value_enabled):
    # the retirement and thermal new-entry screens value each reserve-eligible
    # unit's per-hour best use max(energy margin, reserve price). When present
    # it is the sole thermal AS pricing (rule 19) — see the screens' docstrings.
    reserve_price_signal = None
    reserve_price_signal_slow = None
    if getattr(config, "screen_reserve_value_enabled", True):
        reserve_price_signal = _prior_attr(prior_results, "reserve_price_signal", None)
        reserve_price_signal_slow = _prior_attr(
            prior_results, "reserve_price_signal_slow", None
        )
    # Zonal hourly CF profiles + zone ordering for the shape-aware VRE
    # new-entry revenue (plan §6 CX-6c); None falls back to the scalar screen.
    screen_zone_names = _prior_attr(prior_results, "zone_names", None)
    screen_wind_cf = _prior_attr(prior_results, "wind_cf", None)
    screen_solar_cf = _prior_attr(prior_results, "solar_cf", None)

    # Snapshot the entering fleet so the events recorder can attribute every
    # unit removed by the confirmed (step 0) and announced (step 1) channels.
    _pre_known = {g.unit_id: g for g in fleet} if _rec else None

    # 0. Confirmed exits (exogenous, instrument-bound, any fuel). GATED on
    #    confirmed_exits_enabled (default on, flipped 2026-07-05): when off, no-op
    #    and the announced/economic channels are byte-identical to before this
    #    channel existed. Runs first so the post-exit fleet is what the floor and the
    #    new-entry screen see (scarcity from a confirmed exit feeds next year's
    #    entry signal). Bypasses the reliability floor by construction.
    #    NOTE: matching is by plant_code. A unit that survives the end-of-year
    #    re-aggregation with its plant identity intact — a unit-grain unit (raw
    #    EIA-860 unit that passes through, e.g. an oil unit carrying an announced
    #    date) or a first-year exit in build_base_fleet — is matched in its exit
    #    year. Plant-binned coal/gas tranches (is_campd_bin) also keep their
    #    plant_code: aggregate_fleet passes them through un-aggregated (G-28 fix),
    #    so a confirmed exit effective any number of years into a CAMPD forecast
    #    is matched at the same per-plant grain the base year solves. (Before the
    #    fix these tranches were merged into vintage efficiency bins after the
    #    base year, dropping plant_code, and an exit 2+ years out went unmatched.)
    #    ``apply_backlog`` defaults to False here (unlike build_base_fleet's
    #    True): only the row newly effective in THIS year is selected, so a
    #    row already applied in the pre-start backlog or a prior year's
    #    evolve_fleet call is never re-selected against an already-shrunk
    #    fleet (the double-derate bug fixed 2026-07-05 — a confirmed exit is a
    #    once-at-its-date event, not a recurring per-year filter).
    confirmed_exits = confirmed_exits or []
    confirmed_channel_on = getattr(config, "confirmed_exits_enabled", False) and bool(
        confirmed_exits
    )
    if confirmed_channel_on:
        fleet = apply_confirmed_exits(fleet, year, confirmed_exits)

    # 1. Announced (EIA-860 date) retirements. Fossil units are a default no-op
    #    (their phaseout is economic, step 2; the exogenous fossil channel is
    #    step 0). Non-fossil announced dates are honored within the EIA-860 data
    #    horizon; beyond it, only when the unit is in the confirmed registry (the
    #    horizon gate activates with the confirmed channel — off = honor all
    #    non-fossil dates, as before). config.forecast_fossil_retirement_economic
    #    toggles the fossil exemption.
    horizon_years = NONFOSSIL_ANNOUNCED_HORIZON_YEARS if confirmed_channel_on else None
    confirmed_plant_codes = (
        frozenset(e.plant_id for e in confirmed_exits)
        if confirmed_channel_on
        else frozenset()
    )
    fleet = apply_announced_retirements(
        fleet,
        year,
        fossil_economic=getattr(config, "forecast_fossil_retirement_economic", True),
        horizon_years=horizon_years,
        confirmed_plant_codes=confirmed_plant_codes,
        reversed_plant_codes=announced_reversal_plants,
    )
    if _rec:
        _survived = {g.unit_id for g in fleet}
        events["retirements"].extend(
            {
                "unit_id": g.unit_id,
                "fuel": g.fuel_type,
                "mw": float(g.pmax_mw),
                "reason": "known",
            }
            for uid, g in _pre_known.items()
            if uid not in _survived
        )

    # Locational deliverability headroom per zone (empty no-op unless
    # capacity_deliverability_limits is on and the ISO has clean data). Prior-
    # year renewable pools / storage ELCC are ISO totals; distribute them across
    # zones by load_share so the firm-capacity sum is zonal. Computed once on the
    # entering fleet and shared by the retirement and new-entry screens.
    deliverability_headroom: dict[str, float] = {}
    if config.capacity_deliverability_limits:
        iso_config = get_iso_config(config.iso)
        wind_total = float(_prior_attr(prior_results, "wind_cap_mw", 0.0) or 0.0)
        solar_total = float(_prior_attr(prior_results, "solar_cap_mw", 0.0) or 0.0)
        storage_total = float(_prior_attr(prior_results, "storage_firm_mw", 0.0) or 0.0)
        wind_by_zone = {z.name: wind_total * z.load_share for z in iso_config.zones}
        solar_by_zone = {z.name: solar_total * z.load_share for z in iso_config.zones}
        storage_by_zone = {
            z.name: storage_total * z.load_share for z in iso_config.zones
        }
        deliverability_headroom = deliverability_headroom_by_zone(
            config.iso,
            year,
            fleet,
            config,
            wind_pool_by_zone=wind_by_zone,
            solar_pool_by_zone=solar_by_zone,
            storage_firm_by_zone=storage_by_zone,
        )

    # 2. Economic retirements (needs the prior-year dispatch).
    if fleet_arrays is not None and dispatch_result is not None and prices is not None:
        _econ_sink: dict = {} if _rec else None
        fleet, loss_tracker, floor_retention_log = apply_economic_retirements(
            fleet,
            fleet_arrays,
            dispatch_result,
            prices,
            config,
            loss_tracker,
            peak_demand_used,
            rps_shadow_price=rps_shadow_price,
            mc=mc_cost,
            storage_power_mw=storage_power_mw,
            deliverability_headroom=deliverability_headroom,
            thermal_as_revenue_per_mw_yr=thermal_as_revenue_per_mw_yr,
            wind_pool_mw=wind_pool_mw,
            solar_pool_mw=solar_pool_mw,
            storage_firm_mw=storage_firm_mw,
            year=year,
            event_sink=_econ_sink,
            reserve_price_signal=reserve_price_signal,
            reserve_price_signal_slow=reserve_price_signal_slow,
            reserve_position=reserve_position,
        )
        if _rec:
            events["retirements"].extend(
                {**e, "reason": "economic"} for e in _econ_sink.get("retired", [])
            )
            events["floor_retained"].extend(_econ_sink.get("floor_retained", []))
        if floor_retention_log:
            logger.info(
                "year %d: reliability floor retained %d unit(s), %.0f MW "
                "(%.0f MW UCAP) against the PRM requirement",
                year,
                len(floor_retention_log),
                sum(r["pmax_mw"] for r in floor_retention_log),
                sum(r["ucap_mw"] for r in floor_retention_log),
            )

    # 3. Known additions: planned units coming online this year.
    _planned_now = [g for g in planned if g.online_year == year]
    fleet = fleet + _planned_now
    if _rec:
        events["thermal_additions"].extend(
            {
                "unit_id": g.unit_id,
                "fuel": g.fuel_type,
                "mw": float(g.pmax_mw),
                "zone": g.zone,
                "source": "planned",
                # Planned units come from the EIA-860 pipeline; their unit_id
                # encodes the source plant (``planned_<plant>_<gen>``), so it is
                # the traceable id when the plant_id field is unset.
                "eia860_id": getattr(g, "plant_id", None) or g.unit_id,
            }
            for g in _planned_now
        )

    # 4. CCS retrofits: convert existing gas CC units to gas_cc_ccs. Runs
    # before new entry so retrofits displace some new-build CCS demand.
    _pre_ccs = {g.unit_id: g.fuel_type for g in fleet} if _rec else None
    fleet, retrofit_log = apply_ccs_retrofit(
        fleet,
        prices,
        year,
        config,
        config.iso,
        gas_price_per_mmbtu=gas_price_per_mmbtu,
        carbon_price=carbon_price,
        eac_price_ccs=eac_price_ccs,
        cumulative=cumulative,
    )
    if _rec:
        # A CCS retrofit is a fuel shift (gas_cc → gas_cc_ccs) on the same
        # unit_id, not a new column. Detect by comparing fuel_type before/after.
        _post_ccs = {g.unit_id: g for g in fleet}
        events["ccs_retrofits"].extend(
            {
                "unit_id": uid,
                "mw": float(_post_ccs[uid].pmax_mw),
                "from_fuel": _pre_ccs[uid],
                "to_fuel": _post_ccs[uid].fuel_type,
            }
            for uid in _pre_ccs
            if uid in _post_ccs and _post_ccs[uid].fuel_type != _pre_ccs[uid]
        )

    # 5. Economic new entry (needs a price signal). Clean technologies see
    # the prior year's RPS shadow price as additional expected revenue.
    _pre_entry_ids = {g.unit_id for g in fleet} if _rec else None
    # RC-0C entry-screen diagnostic sink (GATED entry_screen_diagnostics,
    # default off): a per-candidate decomposition ledger with no decision
    # effect, persisted into the year's evolution ledger by the runner.
    _screen_ledger: list[dict] | None = (
        [] if getattr(config, "entry_screen_diagnostics", False) else None
    )
    if prices is not None:
        fleet, entry_additions = apply_economic_new_entry(
            fleet,
            prices,
            year,
            config,
            config.iso,
            rps_shadow_price=rps_shadow_price,
            cumulative=cumulative,
            gas_price_per_mmbtu=gas_price_per_mmbtu,
            carbon_price=carbon_price,
            storage_power_mw=storage_power_mw,
            deliverability_headroom=deliverability_headroom,
            thermal_as_revenue_per_mw_yr=thermal_as_revenue_per_mw_yr,
            reserve_price_signal=reserve_price_signal,
            reserve_price_signal_slow=reserve_price_signal_slow,
            zone_names=screen_zone_names,
            wind_cf=screen_wind_cf,
            solar_cf=screen_solar_cf,
            reserve_position=reserve_position,
            screen_ledger=_screen_ledger,
        )
        _merge_renewable_additions(renewable_additions, entry_additions)
    if _rec and _screen_ledger is not None:
        events["entry_screen_diagnostics"] = _screen_ledger
    if _rec:
        _new_ids = {g.unit_id for g in fleet} - _pre_entry_ids
        events["thermal_additions"].extend(
            {
                "unit_id": g.unit_id,
                "fuel": g.fuel_type,
                "mw": float(g.pmax_mw),
                "zone": g.zone,
                "source": "economic",
                "eia860_id": None,
            }
            for g in fleet
            if g.unit_id in _new_ids
        )

    # 6. Reserve-margin adequacy backstop: force-build firm capacity if the
    # economic screen left the system below its planning reserve margin
    # against the entering year's known peak (prior-year peak when the runner
    # did not supply it). Firm capacity nets the thermal fleet (UCAP) and the
    # prior-year renewable pools / storage (threaded via prior_results).
    # No-op unless the backstop resolves on (G-41 market-design resolution:
    # capacity-market ISOs default-on, energy-only ERCOT off, explicit override
    # wins — resolve_reserve_margin_build_enabled).
    if (
        resolve_reserve_margin_build_enabled(config, config.iso)
        and peak_demand_used > 0.0
    ):
        firm_mw = accredited_firm_capacity_mw(
            fleet,
            wind_pool_mw,
            solar_pool_mw,
            storage_firm_mw,
            iso=config.iso,
            peak_demand_mw=peak_demand_used,
            elcc_curves_enabled=config.renewable_elcc_curves,
        )
        _pre_backstop_ids = {g.unit_id for g in fleet} if _rec else None
        fleet, adequacy_mw = apply_reserve_margin_build(
            fleet, firm_mw, peak_demand_used, year, config, config.iso
        )
        if _rec and adequacy_mw > 0.0:
            events["thermal_additions"].extend(
                {
                    "unit_id": g.unit_id,
                    "fuel": g.fuel_type,
                    "mw": float(g.pmax_mw),
                    "zone": g.zone,
                    "source": "reserve_backstop",
                    "eia860_id": None,
                }
                for g in fleet
                if g.unit_id not in _pre_backstop_ids
            )
        if adequacy_mw > 0.0:
            # Same per-ISO resolution as apply_reserve_margin_build so the
            # logged margin reflects the value actually used.
            resolved_margin = resolve_planning_reserve_margin(config, config.iso)
            logger.info(
                "year %d: reserve-margin backstop built %.0f MW gas_ct "
                "(firm %.0f MW vs peak %.0f MW x %.3f margin)",
                year,
                adequacy_mw,
                firm_mw,
                peak_demand_used,
                1.0 + resolved_margin,
            )

    if _rec:
        # Fleet totals BEFORE aggregation: aggregate_fleet rebins into
        # representative units but conserves MW per fuel, so the capacity
        # accounting is identical either way; record the physical fleet.
        events["fleet_by_fuel_after"] = fleet_totals_by_fuel(fleet)
        # Renewable pool builds (flattened from the {zone: {tech: mw}} dict).
        events["renewable_additions"] = [
            {"zone": zone, "tech": tech, "mw": float(mw)}
            for zone, techs in renewable_additions.items()
            for tech, mw in techs.items()
            if mw
        ]

    # Retirements, retrofits and new entry have reshaped the fleet;
    # re-collapse it into efficiency-bin representatives so the next LP solve
    # gets ~36 thermal columns rather than one per physical unit.
    fleet = aggregate_fleet(fleet, n_bins=config.heat_rate_bin_count)

    return fleet, loss_tracker, renewable_additions, retrofit_log, floor_retention_log
