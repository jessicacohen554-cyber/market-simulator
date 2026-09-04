"""Fleet retirements: confirmed exits, announced dates, the economic screen.

Steps 0, 1 and 3 of the one-pass capacity evolution
(:func:`market_sim.model.capacity_evolution.evolve.evolve_fleet`; spec §5.1),
split out of the former ``model/capacity.py`` god-module (W-D4, 2026-07-21;
refactor-consolidation plan §5 item 4). Three mechanisms remove generators
between simulation years:

* **Confirmed exits** (:func:`apply_confirmed_exits`) -- units bound by an
  enforceable public instrument (consent decree, statute, RTO deactivation
  acceptance, regulatory order, RMR end) force-retire (or derate a plant-binned
  tranche) at the instrument date, any fuel, bypassing the reliability floor.
  GATED on ``confirmed_exits_enabled`` (default on) and forecast-mode only; the
  INSTRUMENT-BOUND exogenous fossil exit channel (it was the only one until
  owner ruling Q30, 2026-09-03, added the owner-filed-date limb below).
* **Announced retirements** (:func:`apply_announced_retirements`) -- units with
  a scheduled EIA-860 ``retirement_year``. Fossil units are a no-op ON THIS
  ROUTE (``forecast_fossil_retirement_economic``); non-fossil dates are honored
  within the EIA-860 data horizon. Since owner ruling Q30 the owner-filed
  FOSSIL dates enter as limb 1b of the same step under
  ``fossil_announced_exits_enabled`` (default on, capx D42/D44), riding the
  confirmed channel's own matcher/derate machinery; the economic screen below
  then decides the residual UNDATED fossil fleet (rule 19 [R-ONE-MECH]:
  a plant carrying a pending filed date is exempt from the screen).
* **Economic retirements** (:func:`apply_economic_retirements`) -- thermal
  units whose attainable (pro-forma) inframarginal margin fails to cover their
  going-forward fixed cost for a fuel-type-specific number of consecutive
  years, least efficient first, with the accredited reliability floor
  (:func:`_apply_reliability_floor`) and its ``floor_retention_log``
  attribution.

This module also carries the shared capacity-market / accreditation /
adequacy-requirement helpers every screen prices through
(:func:`capacity_revenue_per_mw_yr`, :func:`thermal_accreditation_fraction`,
:func:`resolve_adequacy_requirement_mw`, :func:`deliverability_headroom_by_zone`
-- rule 19: one seam for all three screens). The full pre-split surface stays
importable from ``market_sim.model.capacity`` (the facade; see the package
``__init__``).
"""

from __future__ import annotations

import logging
import math

import numpy as np

from market_sim.config.constants import (
    ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
    ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO,
    ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO,
    DEFAULT_MARKET_DESIGN,
    DEMAND_RESPONSE_SUPPLY_HOLD_LAST_RATIO_BY_ISO,
    DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO,
    FORECAST_POOL_REQUIREMENT_BY_ISO,
    FORECAST_POOL_REQUIREMENT_PRE_REFORM_BY_ISO,
    MARKET_DESIGN,
    NET_ICR_HOLD_LAST_RATIO_BY_ISO,
    NET_ICR_REQUIREMENT_MW_BY_ISO,
    NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO,
    NYCA_ICAP_UCAP_TRANSLATION_BY_ISO,
    NYCA_IRM_ADOPTED_BY_ISO,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO,
    RENEWABLE_CAPACITY_CREDIT,
    RENEWABLE_CAPACITY_CREDIT_BY_ISO,
    RENEWABLE_ELCC_CURVES_BY_ISO,
    RENEWABLE_NQC_CURVES_BY_ISO,
    STORAGE_DEPLOYMENT_CEILING_MW,
    STORAGE_ELCC_DILUTION_CEILING_RATIO_BY_ISO,
    STORAGE_ELCC_DILUTION_REFERENCE_MW_BY_ISO,
    THERMAL_ACCREDITATION_BASIS_BY_ISO,
    THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO,
    THERMAL_ELCC_CLASS_RATING_BY_ISO,
    evaluate_renewable_elcc_curve,
)
from market_sim.config.capacity_area_crosswalk import aggregate_by_zone
from market_sim.config.reserve_config import (
    QUICK_START_FUEL_TYPES,
    RESERVE_FUEL_TYPES,
)
from market_sim.config.scenarios import ScenarioConfig, resolve_demand_growth_rate
from market_sim.data import capacity_deliverability as capdel
from market_sim.model.ancillary import as_revenue_per_mw_yr
from market_sim.data.confirmed_retirements import ConfirmedExit
from market_sim.data.fleet import (
    FleetArrays,
    Generator,
)
from market_sim.model.dispatch import DispatchResult
from market_sim.policy.clean_tiers import clean_credit_for_zone
from market_sim.policy.federal_ces import eac_price_components_for_unit
from market_sim.policy.ira import section_45u_credit_per_mwh
from market_sim.policy.rps import rps_credit_for_zone

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
# these out at nameplate — its accreditation rebuild routes the resources it
# SEES through accredited_firm_capacity_mw at their UCAP/capacity-credit value
# (capacity-economics plan 2026-07 §3.2). Hydro DOES now reach that ledger:
# FFR-1C (2026-07-31, closing forecast-readiness audit FR-3) added the
# ``_hydro_firm_mw`` POOL term, crediting the model's own dispatched hydro
# nameplate at the ISO's published accreditation factor. The persistent evolved
# fleet still never contains hydro (the runner carries it only in the transient
# dispatch fleet), so the pool — not this constant — is what carries it.
#
# This constant is retained ONLY as the evolution ledger's reporting basis for
# any hydro that DID reach the persistent fleet; runner.py sums it alongside the
# modelled pool as of FFR-3B (2026-08-02, closing FFR-1C finding F-5). Before
# that the ledger's ``firm_clean_mw`` was structurally 0 for every ISO and year.
# It participates in no retirement/adequacy decision.
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


def _apply_exit_throughput_cap(
    due: list[Generator], state: dict[str, int], cap_mw: float
) -> tuple[list[Generator], list[Generator]]:
    """Split the year's due exits into (executing, deferred) at the MW cap.

    The exit half of the deactivation queue (``ScenarioConfig.exit_rate_limits``;
    owner decision D-8, 2026-08-03 —
    ``docs/handoffs/ffr-owner-sitting-2026-08-02.md`` Addendum F.1). The
    execution lag models the queue's LATENCY; this models its THROUGHPUT. D-8
    ruled them two mechanisms for rule 19 ``[R-ONE-MECH]`` purposes, on
    FFR-3C §1.2's measurement that a per-fuel constant lag is a rigid
    time-shift operator — it translates an exit wave without spreading it, so
    wave width stays at exactly one year however many units fail.

    **Strict FIFO, because that is what a deactivation queue is.** Requests are
    processed oldest-decision-first (``state[unit_id]``, the decided year),
    tie-broken by the caller's existing deterministic ``(fuel_type,
    -heat_rate)`` order, and the year stops at the first unit that would not
    fit. The remaining headroom is deliberately NOT backfilled with a smaller
    later unit: reordering the queue to pack the year is an optimisation a real
    RTO deactivation queue does not perform, and it would make exit
    composition depend on unit size rather than on request date.

    The head of the queue is always admitted even when it alone exceeds the
    cap. Without that, a unit larger than the ISO's whole annual throughput
    could never leave — the cap would silently become an immortality rule
    rather than a rate limit.

    Deferred units are NOT un-decided: the caller leaves them in
    ``pipeline_state``, so they re-present at the head of next year's queue
    through the identical "execution deferred, re-latched next year" path the
    reliability floor already uses (pipeline component 5). No second deferral
    mechanism is introduced (rule 19).

    Args:
        due: The year's due exits, in the caller's deterministic order.
        state: Pipeline state ``unit_id -> decided_year``, read for the FIFO
            key; not mutated.
        cap_mw: The year's throughput budget in MW.

    Returns:
        ``(executing, deferred)``, both preserving the caller's input order so
        the ledger and the floor's eligible iteration stay deterministic.
    """
    queue = sorted(due, key=lambda g: (state[g.unit_id], g.fuel_type, -g.heat_rate))
    admitted: set[str] = set()
    admitted_mw = 0.0
    for g in queue:
        mw = float(g.pmax_mw)
        if admitted and admitted_mw + mw > cap_mw:
            break  # year's throughput exhausted; the rest wait their turn
        admitted.add(g.unit_id)
        admitted_mw += mw
    return (
        [g for g in due if g.unit_id in admitted],
        [g for g in due if g.unit_id not in admitted],
    )


def _admission_cap_horizon(
    config: ScenarioConfig,
    scheduled: set[str],
    state: dict[str, int],
    decided_year: int,
    fleet: list[Generator],
    peak_demand: float,
    year: int,
) -> tuple[int, float]:
    """Return the (year, peak MW) the pipeline's admission cap is tested at.

    The G-31 cap-grain correction (FFR-3F task 1, chartered by owner decision
    D-8 / FFR-3C §6.3). The admission cap in
    :func:`_apply_pipeline_retirements` is a test on ONE counterfactual fleet:
    the current fleet with the WHOLE scheduled exit set removed at once. That
    fleet state is not realized at the decision ``year`` — it is realized at
    the LAST execution year in the schedule, ``max(decided_year + L_f)``, one
    to three years later. Testing it against the decision year's requirement
    measured the exits against a requirement they never land against (FFR-3C
    §1.2 G3: the cap saw a 2026 requirement of 21,990 MW while the exits it
    admitted landed against 2028's 24,244 MW — **+10.3 % of requirement the
    cap never saw**). This function returns the horizon that makes the two
    halves of the test consistent: the fleet-with-all-exits-gone is paired
    with the requirement at the year that fleet actually exists.

    Both inputs to :func:`resolve_adequacy_requirement_mw` move to that
    horizon, because both are year-dependent:

    * the **year**, which selects the ISO's published-FPR delivery year
      (:func:`resolve_forecast_pool_requirement`); and
    * the **peak** the requirement is a fraction of, projected from the
      entering year's peak by compounding the run's own demand-growth path
      (:func:`resolve_demand_growth_rate` — the identical per-year rate
      ``runner._scale_demand`` compounds to build each year's load).

    No new parameter enters: the horizon is a function of the per-fuel
    execution lags (``retirement_execution_lag_*``, already identified) and
    the growth path already driving demand, so it regenerates for any forward
    year and responds to changed conditions (rule 13 ``[R-MEASURED]``).

    Two deliberate limits, stated because they are silent otherwise:

    * The projection compounds growth only. ``runner.add_load_layers``
      relocates each additive load layer's energy onto its own shape *after*
      scaling and is jointly energy-invariant, so its effect on the peak is
      second-order and is not reproduced here; the growth path itself is
      DC- and electrification-inclusive.
    * The **fleet** side stays at the decision year — entry that commissions
      between decision and execution is not credited. That is the pre-existing
      grain of the cap and is out of this correction's scope; it biases the
      cap conservative (toward retaining), and it is recorded as an open item
      rather than silently closed.

    Args:
        config: Scenario config supplying the per-fuel execution lags and the
            demand-growth path.
        scheduled: Unit ids of the whole scheduled exit set (pending state
            plus this year's admitted candidates).
        state: Pipeline state ``unit_id -> decided_year`` for pending units.
        decided_year: The loss year stamped on units decided at this screen.
        fleet: The current fleet, supplying each scheduled unit's fuel type.
        peak_demand: The entering year's peak demand in MW.
        year: The screen (decision) year.

    Returns:
        ``(cap_year, cap_peak_demand_mw)``. With an empty schedule, or when
        every scheduled exit executes in ``year`` itself (all lags 1, the
        gas/oil case), this is exactly ``(year, peak_demand)`` — the
        pre-correction behaviour, unchanged.
    """
    fuel_of = {g.unit_id: g.fuel_type for g in fleet}
    cap_year = year
    for uid in scheduled:
        fuel_type = fuel_of.get(uid)
        if fuel_type is None:  # left the fleet through another channel
            continue
        execute_year = state.get(uid, decided_year) + _execution_lag_years(
            config, fuel_type
        )
        cap_year = max(cap_year, execute_year)
    cap_peak_demand = peak_demand
    for growth_year in range(year, cap_year):
        cap_peak_demand *= 1.0 + resolve_demand_growth_rate(config, growth_year)
    return cap_year, cap_peak_demand


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

    A confirmed exit is a discrete event with a fixed per-row MW removal
    schedule, never a recurring per-year filter. ``fleet`` threads forward
    mutated through the runner's year loop, so a row's MW must be removed
    exactly once across the run (a plant-binned exit's remaining tranche has
    no memory of which rows already reduced it). Each row's schedule
    (FFR-1A arm 2 / audit FR-2 — MW subtraction composes across years where
    factor-of-factor arithmetic cannot):

    * ``exit_month <= 6`` (effective in ``exit_year``): the effective year
      removes the annual-average share ``(12 − m)/12 × mw`` (the unit ran
      ``m`` months), and **the following year removes the remaining
      ``m/12 × mw``** — the completion leg. Before the completion leg a
      first-half exit froze at its annual-average factor forever (a unit
      legally gone by May kept ~5/12 of its MW through the horizon).
    * ``exit_month > 6`` or no month: the effective year (``exit_year + 1``
      for late-month rows, majority-of-year rule) removes the full ``mw``.
    * **Over-subscribed registry** (``Σ mw > binned_mw`` — the fleet
      under-represents the plant): the effective-year removal is apportioned
      by ``binned/Σmw`` so the year still lands on the annual-average of the
      plant's true start/end states (factor ``m/12`` for a whole-plant
      first-half exit — the pre-FFR-1A behaviour); the uncapped completion
      leg then floors the factor at 0, finishing the plant at
      ``max(0, binned − Σmw)``.

    Two call sites coordinate via ``apply_backlog``:

    * ``apply_backlog=True`` (:func:`market_sim.data.fleet.build_base_fleet`,
      the first simulated year only): a row effective THIS year starts its
      normal schedule (annual-average now, completion next year via
      :func:`evolve_fleet`); a row effective in an EARLIER, never-simulated
      year removes its **full** ``mw`` at once — by the first simulated year
      both schedule legs are already due, so no annual-average ghost survives
      the pre-start backlog.
    * ``apply_backlog=False`` (the default, :func:`evolve_fleet`, every later
      year): selects rows newly effective this year plus the completion legs
      of last year's first-half rows — a leg already applied (in the backlog
      or a prior year) is never re-selected.

    Matching (plan §5.1):

    * **Unit-grain** generators (raw EIA-860 units, ``unit_id`` =
      ``"{plant_code}_{generator_id}"``) are dropped whole when their
      generator ID is confirmed to exit this year (annual grain — no partial
      unit; completion legs never re-match a unit dropped at its effective
      year).
    * **Plant-binned** generators (ERCOT CAMPD bins / synthesized tranche plants,
      ``is_campd_bin`` or an unparseable ``unit_id``) are **derated**: the
      plant's binned MW is scaled by
      ``(binned_mw − mw_due_now) / binned_mw`` — pmax/pmin and the MW-valued
      tranche floors scale proportionally, dropping a tranche when its
      remaining MW ≤ ε. The residual heat-rate composition shift (the exiting
      unit is usually the worst) is accepted second-order error. A row that
      carries a ``fuel_type`` (the capx D42 announced fossil channel) derates
      only the plant's binned generators of THAT fuel when it has any — the
      cross-fuel bleed at a mixed-fuel plant is a composition error, not a
      second-order one; fuel-less rows keep the plant-wide derate. Because each
      row's schedule legs are each selected exactly once and remove absolute
      MW (never re-summed against an already-shrunk denominator), a plant
      with multiple rows landing in different years derates correctly year
      over year.

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
        to ``fleet`` when no exit leg is due this year.
    """
    if apply_backlog:
        current = [e for e in exits if _confirmed_effective_year(e) == year]
        # Rows effective before the first simulated year: BOTH schedule legs
        # are already due (the annual-average year was never simulated), so
        # the full registry MW is removed at once — otherwise a first-half
        # pre-start exit (V H Braunig, March 2025, in a 2026-start forecast)
        # would freeze at its annual-average factor forever (FR-2's backlog
        # variant).
        prior = [e for e in exits if _confirmed_effective_year(e) < year]
        completion: list[ConfirmedExit] = []
    else:
        current = [e for e in exits if _confirmed_effective_year(e) == year]
        prior = []
        # Completion legs (FFR-1A arm 2 / FR-2): last year's first-half rows
        # removed only their annual-average share; the remaining m/12 × mw is
        # due now. Derate-branch only — a unit-grain row dropped its whole
        # unit at the effective year, so there is nothing left to complete.
        completion = [
            e
            for e in exits
            if e.exit_month is not None
            and e.exit_month <= 6
            and _confirmed_effective_year(e) == year - 1
        ]
    if not current and not prior and not completion:
        return list(fleet)

    # Derate SCOPE (capx D42, the fossil announced-date channel): a row that
    # carries a ``fuel_type`` derates ONLY the plant's binned generators of
    # that fuel when the plant has any — a dated coal unit at a mixed-fuel
    # plant (Karn coal + gas steam, Schahfer coal + CTs) must not bleed its
    # MW onto the plant's gas bins, which is a cross-fuel COMPOSITION error,
    # not the accepted second-order heat-rate shift. A row without a fuel
    # (the confirmed registry's ``ConfirmedExit``) or whose fuel has no
    # binned generator at the plant keeps the plant-wide derate, so every
    # pre-D42 caller is byte-identical (the D42 plant-wide probe leg
    # measured the artifact at 0.8 GW of gas_ct/gas_st false positives).
    fuels_by_plant: dict[int, set[str]] = {}
    for g in fleet:
        if _is_confirmed_binned(g):
            fuels_by_plant.setdefault(int(g.plant_code), set()).add(g.fuel_type)

    def _scope(e: object) -> tuple[int, str | None]:
        pc = int(e.plant_id)
        f = getattr(e, "fuel_type", None)
        if f is not None and str(f) in fuels_by_plant.get(pc, set()):
            return (pc, str(f))
        return (pc, None)

    # Per (plant, scope) MW due for removal THIS year (the derate branch's
    # numerator), the registry MW behind it (warning + over-subscription
    # basis, current/prior rows only), the completion dues (kept separate —
    # they are never capped, see below), and the unit-grain generator IDs
    # dropping this year.
    remove_mw_by_key: dict[tuple[int, str | None], float] = {}
    raw_mw_by_key: dict[tuple[int, str | None], float] = {}
    completion_mw_by_key: dict[tuple[int, str | None], float] = {}
    exit_gids_by_plant: dict[int, set[str]] = {}
    for e in current:
        mw = e.mw or 0.0
        key = _scope(e)
        raw_mw_by_key[key] = raw_mw_by_key.get(key, 0.0) + mw
        if e.exit_month is not None and e.exit_month <= 6:
            # Annual-average leg: the unit ran exit_month months this year.
            due = mw * (12 - e.exit_month) / 12.0
        else:
            due = mw
        remove_mw_by_key[key] = remove_mw_by_key.get(key, 0.0) + due
        exit_gids_by_plant.setdefault(e.plant_id, set()).add(str(e.generator_id))
    for e in prior:
        mw = e.mw or 0.0
        key = _scope(e)
        raw_mw_by_key[key] = raw_mw_by_key.get(key, 0.0) + mw
        remove_mw_by_key[key] = remove_mw_by_key.get(key, 0.0) + mw
        exit_gids_by_plant.setdefault(e.plant_id, set()).add(str(e.generator_id))
    for e in completion:
        # No gid entry: the unit-grain drop happened at the effective year.
        due = (e.mw or 0.0) * e.exit_month / 12.0
        key = _scope(e)
        completion_mw_by_key[key] = completion_mw_by_key.get(key, 0.0) + due

    exit_keys = set(remove_mw_by_key) | set(completion_mw_by_key)
    exit_plants = {k[0] for k in exit_keys} | set(exit_gids_by_plant)

    # Per (plant, scope) total binned MW (the derate denominator), computed
    # once: the plant-wide key sums every binned generator of the plant, a
    # fuel-scoped key only those of that fuel.
    binned_mw_by_key: dict[tuple[int, str | None], float] = {}
    for g in fleet:
        pc = int(g.plant_code)
        if pc in exit_plants and _is_confirmed_binned(g):
            for key in ((pc, None), (pc, g.fuel_type)):
                if key in exit_keys:
                    binned_mw_by_key[key] = binned_mw_by_key.get(key, 0.0) + g.pmax_mw

    # Over-subscription cap: when the registry's exit MW exceeds the plant's
    # binned fleet MW (the fleet under-represents the plant — NEISO Merrimack
    # carries 108 MW against a 459.2 MW registry exit), apportion this year's
    # current/prior removal by binned/raw so a partial-year row's effective
    # year still lands on the annual-average of the plant's true start/end
    # states (factor m/12 when the whole plant exits) instead of bleeding the
    # over-subscription into the months the unit still ran. Completion legs
    # are added AFTER the cap, uncapped: next year the raw m/12 × mw due
    # meets the already-averaged remainder, the factor floors at 0, and the
    # plant correctly finishes at max(0, binned − mw).
    for key, raw in raw_mw_by_key.items():
        binned = binned_mw_by_key.get(key, 0.0)
        if raw > binned > 0.0:
            remove_mw_by_key[key] *= binned / raw
    for key, due in completion_mw_by_key.items():
        remove_mw_by_key[key] = remove_mw_by_key.get(key, 0.0) + due

    kept: list[Generator] = []
    for g in fleet:
        pc = int(g.plant_code)
        if pc not in exit_plants:
            kept.append(g)
            continue
        if _is_confirmed_binned(g):
            factor = 1.0
            touched = False
            for key in ((pc, None), (pc, g.fuel_type)):
                if key not in exit_keys:
                    continue
                touched = True
                binned_mw = binned_mw_by_key.get(key, 0.0)
                remove_mw = remove_mw_by_key.get(key, 0.0)
                if binned_mw <= 0.0 or remove_mw <= 0.0:
                    # No usable MW to derate against (registry left
                    # capacity_mw blank): keep the tranche rather than
                    # over-retire the plant. Warn only for a current/prior
                    # row's plant — a completion leg with no MW already
                    # warned at its effective year.
                    if key in raw_mw_by_key and raw_mw_by_key[key] <= 0.0:
                        logger.warning(
                            "confirmed-exit: plant %d has no capacity_mw to derate "
                            "binned tranches; kept intact",
                            pc,
                        )
                    continue
                factor *= max(0.0, (binned_mw - remove_mw) / binned_mw)
            if not touched:
                kept.append(g)  # the plant's exits are unit-grain drops only
                continue
            derated = _derate_generator(g, factor)
            if derated.pmax_mw > _CONFIRMED_EXIT_MW_EPS:
                kept.append(derated)
            # else: fully retired by the confirmed exit (dropped).
        else:
            gid = _unit_generator_id(g)
            if gid is not None and gid in exit_gids_by_plant.get(pc, set()):
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


def _exit_row_pending_after(exit_: object, year: int) -> bool:
    """Whether an exogenous exit row still has a leg due AFTER ``year``.

    A row is pending while its effective year is ahead, or while a first-half
    row's completion leg (:func:`apply_confirmed_exits`, the ``m/12 × mw``
    remainder removed the year after the effective year) is still due.
    """
    eff = _confirmed_effective_year(exit_)
    if eff > year:
        return True
    month = getattr(exit_, "exit_month", None)
    return month is not None and month <= 6 and eff == year


def dated_plant_unit_ids(
    fleet: list[Generator], exits: list, year: int
) -> frozenset[str]:
    """Unit ids that are EXOGENOUS to the economic screen in ``year`` because
    their plant carries a pending owner-filed exit row (capx D42, the rule-19
    reconciliation of the fossil announced-date channel).

    The filed date IS the owner's exit decision for that plant, so the screen
    decides only undated plants — no unit's exit is decided twice. Grain
    follows the matcher's (:func:`apply_confirmed_exits`): a UNIT-GRAIN
    generator is exempt iff its own generator ID carries a pending row; a
    PLANT-BINNED generator (``is_campd_bin`` / unparseable id) is exempt while
    ANY row of its plant is pending — the plant's residual configuration is
    the owner's post-retirement plan, and the derate lands on the bin as a
    whole. Once a plant's last row has completed, its survivors re-enter the
    screen as an undated residual plant. Empty when ``exits`` is empty.
    """
    if not exits:
        return frozenset()
    pending_gids: dict[int, set[str]] = {}
    for e in exits:
        if _exit_row_pending_after(e, year):
            pending_gids.setdefault(int(e.plant_id), set()).add(str(e.generator_id))
    if not pending_gids:
        return frozenset()
    out: set[str] = set()
    for g in fleet:
        pc = int(g.plant_code)
        gids = pending_gids.get(pc)
        if not gids:
            continue
        if _is_confirmed_binned(g):
            out.add(g.unit_id)
        else:
            gid = _unit_generator_id(g)
            if gid is not None and gid in gids:
                out.add(g.unit_id)
    return frozenset(out)


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
            # The minimum online configuration scales with the derated plant
            # for the same reason every other MW floor here does: a partially
            # retired plant carries proportionally less minimum load, and an
            # unscaled floor would force the shrunken unit above its own
            # capacity.
            "coal_min_config_pmin_mw": gen.coal_min_config_pmin_mw * factor,
        }
    )


def apply_announced_retirements(
    fleet: list[Generator],
    year: int,
    fossil_economic: bool = True,
    *,
    vintage: int | None = None,
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

    **Fossil no-op ON THIS ROUTE (RC-3).** When ``fossil_economic`` is ``True``
    (the forecast default), units of a :data:`_FOSSIL_FUELS` type are **exempt**
    from date-based retirement HERE. Set ``fossil_economic=False`` to honor
    every scheduled fossil date on this route (the legacy behaviour).

    That exemption is no longer the whole fossil-date posture. Owner ruling Q30
    (2026-09-03, capx D42/D44) arms ``fossil_announced_exits_enabled`` by
    default, so the owner-filed fossil dates DO retire units — as limb 1b of
    this same step 1, vintage-gated and reversal-checked, on the confirmed
    channel's matcher/derate machinery — and the economic screen
    (:func:`apply_economic_retirements`) decides the residual UNDATED fossil
    fleet. The superseded rationale for the exemption ("an announced fossil
    date is an announcement, not a certainty") was ruled a statement about
    PRECISION rather than admissibility; D42 measured that precision at 98.5 %
    of released MW at plant grain under the verified posture.

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
        vintage: EIA-860 operable-snapshot vintage the horizon is measured
            from. ``None`` (default) resolves the ACTIVE snapshot's vintage
            (:func:`market_sim.data.fleet.operable_vintage_year` — FH-1 leak
            fix): a vintage-seeded hindcast measures the announced horizon
            from ITS vintage (e.g. 2020 + 5), never the canonical 2025
            constant, which would honor dates the seed snapshot could not
            credibly bound. Non-vintage runs resolve to the constant,
            byte-identical.
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
    if vintage is None:
        # Resolve the ACTIVE snapshot's vintage (FH-1): the runner sets the
        # vintage dir once at startup (set_eia860_vintage), so a vintage-seeded
        # hindcast measures the announced horizon from its own seed year.
        from market_sim.data.fleet import operable_vintage_year

        vintage = operable_vintage_year()
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
    # capx D48: the payment is priced on the accreditation design of the
    # delivery year (config/year threaded; byte-identical unarmed).
    accredited = max(
        0.0, thermal_accreditation_fraction(fuel_type, eford, iso, config, year)
    )
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
    """Return the FPR governing ``iso``'s ``year`` (published, or held-last), or None.

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

    **HOLD-LAST-FPR — the declared convention beyond the published table**
    (owner signature card C-A, 2026-08-25,
    ``docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md`` §3.3/§5.1;
    implemented by capx lane S-5): a delivery year STRICTLY AFTER the ISO's
    last published FPR returns that last published value, never the stale
    fallback composite. Precedent: :func:`config.capacity_market.
    resolve_demand_curve_vintage` / :func:`forward_net_cone_anchor` declare
    exactly this forward-carry for the demand curve's own forward values
    ("year after the latest vintage HOLDS-LAST to it — the forward-carry a
    forecast uses"). Rationale, measured in
    ``docs/handoffs/FINDING-capx-d2b-i7-ledger-2026-08-25.md`` §5.2: the
    fallback composite's IRM half is two vintages stale against PJM's own
    rising series (2027/28 IRM 20.0 %; FPR 0.9170 → 0.9260 → 0.9401), so
    falling through to it dropped the requirement discontinuously by 3.18 %
    of peak at the 2028/29 → 2029/30 table edge — 5,492 MW at the 2030 peak.
    Hold-last is the LESS lenient reading and is superseded per delivery year
    the moment the ISO publishes that year's parameters (rule 23
    ``[R-FROZEN-DERIVE]``: intake on publication, never against a residual —
    PJM's 2029/30 checked unpublished as of 2026-08-30, BRA scheduled
    Dec 2026). Delivery years BEFORE the first published entry still return
    ``None`` (pre-CIFP years keep the fallback composite deliberately), as
    does an in-table gap: the convention extends the table's FORWARD edge
    only, so every in-table and pre-table year — every backcast year — is
    byte-identical.
    """
    if year is None:
        return None
    table = FORECAST_POOL_REQUIREMENT_BY_ISO.get(iso)
    if not table:
        return None
    label = capdel.resolve_delivery_year(iso, year)
    fpr = table.get(label)
    if fpr is not None:
        return fpr
    # HOLD-LAST-FPR (card C-A, 2026-08-25 — see docstring): strictly beyond
    # the last published delivery year, hold its FPR. Delivery-year labels
    # order by their leading start year (planning-year ISOs "YYYY/YYYY+1",
    # CAISO bare "YYYY" — same ``int(label[:4])`` parse as
    # ``forward_net_cone_anchor``'s vintage carry).
    last_label = max(table, key=lambda lbl: int(lbl[:4]))
    if int(label[:4]) > int(last_label[:4]):
        return table[last_label]
    return None


def accreditation_design_vintage_armed(
    config: ScenarioConfig | None, iso: str | None
) -> bool:
    """True when ``iso`` accredits on the design of each delivery year's own auction.

    The ONE gate predicate (rule 19) behind BOTH halves of the capx D48
    accreditation-design devintage (``FINDING-capx-d45-pjm-nyiso-curves-
    2026-09-03.md`` §2.3 item 1): the thermal basis resolver
    (:func:`resolve_thermal_accreditation_basis`) and the pre-reform
    requirement resolver (:func:`resolve_pre_reform_pool_requirement`)
    consult it, so the supply and requirement halves can never be
    devintaged apart (the mixed-basis ratio D45 §2.2 measured is exactly
    the failure mode a one-sided arm would reproduce). Requires BOTH the
    default-OFF ``ScenarioConfig.pjm_accreditation_design_vintage`` gate AND
    an entry for ``iso`` in
    :data:`THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO` (PJM alone —
    rule 25 ``[R-ISO-SCOPE]``: the flag armed on any other ISO's run is inert
    by construction). ``config=None`` / ``iso=None`` resolve False.
    """
    if config is None or iso is None:
        return False
    if not getattr(config, "pjm_accreditation_design_vintage", False):
        return False
    return iso in THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO


def _delivery_year_before(label: str, reform_label: str) -> bool:
    """True when delivery-year ``label`` starts strictly before ``reform_label``.

    Delivery-year labels order by their leading start year (planning-year
    ISOs ``"YYYY/YYYY+1"``, CAISO bare ``"YYYY"`` — the same ``int(label[:4])``
    parse :func:`resolve_forecast_pool_requirement`'s hold-last uses).
    """
    return int(label[:4]) < int(reform_label[:4])


def resolve_thermal_accreditation_basis(
    iso: str | None,
    config: ScenarioConfig | None = None,
    year: int | None = None,
) -> str | None:
    """Thermal accreditation basis for ``iso`` in ``year`` (registry, or devintaged).

    Returns the :data:`THERMAL_ACCREDITATION_BASIS_BY_ISO` entry (``None`` for
    an ISO absent from it — the UCAP default) unless the capx D48 devintage is
    armed (:func:`accreditation_design_vintage_armed`) and ``year`` resolves
    to a delivery year STRICTLY BEFORE the ISO's registered reform delivery
    year (:data:`THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO`), in
    which case it returns ``"ucap"`` — the ``1 − EFORd`` design the auction of
    that delivery year actually cleared on (PJM Manual 18 §4.2.1 pre-CIFP).
    From the reform delivery year onward the registry basis applies, exactly
    as the published design switched. ``year=None`` (a caller that cannot
    resolve a delivery year) keeps the registry basis, so every gate-off
    path and every year-less call is byte-identical to the pre-D48 resolver.
    """
    basis = THERMAL_ACCREDITATION_BASIS_BY_ISO.get(iso or "")
    if year is None or not accreditation_design_vintage_armed(config, iso):
        return basis
    reform_label = THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO[iso]
    label = capdel.resolve_delivery_year(iso, year)
    if _delivery_year_before(label, reform_label):
        return "ucap"
    return basis


def resolve_pre_reform_pool_requirement(
    config: ScenarioConfig | None, iso: str | None, year: int | None
) -> float | None:
    """Published PRE-REFORM FPR for ``iso``'s delivery year under the D48 arm, or None.

    The requirement half of the accreditation-design devintage (capx D48):
    when :func:`accreditation_design_vintage_armed` holds and ``year``
    resolves to a delivery year carried in
    :data:`FORECAST_POOL_REQUIREMENT_PRE_REFORM_BY_ISO` (PJM 2021/22–2024/25,
    the pre-CIFP ``(1 + IRM) × (1 − pool EFORd)`` FPRs the auctions cleared
    on), returns that FPR; the caller prices the requirement as
    ``firm_peak × FPR`` exactly as it does on the post-reform table. Every
    other case — unarmed, off-registry ISO, ``year=None``, a delivery year
    outside the pre-reform table (including every post-reform year, which the
    post-reform resolver owns) — returns ``None`` and the caller's existing
    ladder (published post-reform FPR → composite) runs byte-identically.
    NO hold-last: the pre-reform table has a hard END at the design switch,
    so nothing is ever carried forward from it.
    """
    if year is None or not accreditation_design_vintage_armed(config, iso):
        return None
    table = FORECAST_POOL_REQUIREMENT_PRE_REFORM_BY_ISO.get(iso or "")
    if not table:
        return None
    return table.get(capdel.resolve_delivery_year(iso, year))


def demand_response_supply_armed(
    config: ScenarioConfig | None, iso: str | None
) -> bool:
    """True when ``iso`` counts Demand Resources as adequacy SUPPLY, not a peak netting.

    The gate predicate behind the capx D48 DR-as-supply repair
    (``FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md`` §2.3 item 2):
    requires BOTH the default-OFF ``ScenarioConfig.pjm_demand_response_supply``
    gate AND an entry for ``iso`` in
    :data:`DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO` (PJM alone — rule 25).
    ``config=None`` / ``iso=None`` resolve False.
    """
    if config is None or iso is None:
        return False
    if not getattr(config, "pjm_demand_response_supply", False):
        return False
    return iso in DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO


def resolve_demand_response_supply_mw(
    config: ScenarioConfig | None,
    iso: str | None,
    year: int | None,
    gross_requirement_mw: float | None = None,
) -> float | None:
    """Published DR supply (accredited MW) counted for ``iso``'s delivery year, or None.

    The supply-side DR construction (capx D48 — see
    :data:`DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO`'s citation block). Resolution:

    1. Gate: :func:`demand_response_supply_armed` must hold and ``year`` must
       be given; otherwise ``None`` — the caller keeps the peak-netting form
       (:data:`ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO`) byte-identically.
    2. An in-table delivery year returns its ABSOLUTE published offered DR
       (UCAP MW) — the auction's own counted quantity.
    3. Strictly beyond the last published delivery year: HOLD-LAST (card
       C-A 2026-08-25) as the last delivery year's published DR-to-
       Reliability-Requirement RATIO
       (:data:`DEMAND_RESPONSE_SUPPLY_HOLD_LAST_RATIO_BY_ISO`) × the model's
       ``gross_requirement_mw`` (the UN-netted requirement, peak × FPR), so
       the held DR scales with load — the same construction the netting
       fraction uses. A caller that cannot supply the gross requirement
       (``None``) gets ``None`` (no MW is invented).
    4. Before the first published delivery year, or an in-table gap:
       ``None`` — the netting fallback, the PJM FPR convention.

    Two verbs, one quantity (rule 19): the SAME MW that
    :func:`~market_sim.model.capacity_evolution.adequacy.
    accredited_firm_capacity_mw` adds to the supply ledger is the reason
    :func:`resolve_adequacy_requirement_mw` stops netting the peak, so the
    position is stated on the auction's raw convention on both sides.
    """
    if year is None or not demand_response_supply_armed(config, iso):
        return None
    table = DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO.get(iso or "")
    if not table:
        return None
    label = capdel.resolve_delivery_year(iso, year)
    mw = table.get(label)
    if mw is not None:
        return float(mw)
    last_label = max(table, key=lambda lbl: int(lbl[:4]))
    if int(label[:4]) > int(last_label[:4]):
        ratio = DEMAND_RESPONSE_SUPPLY_HOLD_LAST_RATIO_BY_ISO.get(iso or "")
        if ratio is None or gross_requirement_mw is None:
            return None
        return float(gross_requirement_mw) * float(ratio)
    return None


def gross_adequacy_requirement_mw(
    config: ScenarioConfig, iso: str, peak_demand_mw: float, year: int | None = None
) -> float:
    """The UN-netted adequacy requirement (before any DR netting), in MW.

    The requirement ladder of :func:`resolve_adequacy_requirement_mw` applied
    to the GROSS peak: published pre-reform FPR under the D48 arm
    (:func:`resolve_pre_reform_pool_requirement`) → published post-reform /
    held-last FPR (:func:`resolve_forecast_pool_requirement`) → the
    ``(1 + PRM) × icap_to_ucap_ratio`` composite. Factored out so the D48
    DR-as-supply hold-last (:func:`resolve_demand_response_supply_mw`) can
    scale its held ratio by the same object the requirement is built on
    (rule 19). The NEISO Net ICR path is NOT here — it returns an absolute
    published MW, and :func:`resolve_adequacy_requirement_mw` consults it
    first, unchanged.
    """
    fpr = resolve_pre_reform_pool_requirement(config, iso, year)
    if fpr is None:
        fpr = resolve_forecast_pool_requirement(iso, year)
    if fpr is not None:
        return peak_demand_mw * fpr
    # capx D52 (NYISO, both GATED default-OFF): the requirement's PEAK is the
    # published ICAP-market forecast peak of the capability year when
    # ``nyiso_requirement_forecast_peak`` is armed and the year is in-table
    # (else ``peak_demand_mw`` is returned unchanged — the same float, so the
    # unarmed product below is byte-identical), and its FACTOR is the
    # capability year's adopted IRM × (1 − derate) when
    # ``nyiso_requirement_vintage_factors`` is armed (hold-last beyond the
    # table; None pre-table / unarmed → the composite below, unchanged).
    requirement_peak_mw = resolve_nyiso_requirement_peak_mw(
        config, iso, peak_demand_mw, year
    )
    vintage_factor = resolve_nyiso_requirement_factor(config, iso, year)
    if vintage_factor is not None:
        return requirement_peak_mw * vintage_factor
    icap_to_ucap_ratio = PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO.get(iso, 1.0)
    return (
        requirement_peak_mw
        * (1.0 + resolve_planning_reserve_margin(config, iso))
        * icap_to_ucap_ratio
    )


def net_icr_requirement_armed(config: ScenarioConfig | None, iso: str | None) -> bool:
    """True when ``iso`` prices adequacy on its published Net ICR series.

    The ONE gate predicate (rule 19) behind both halves of the capx D40 repair
    (``FINDING-capx-d33-neiso-position-2026-09-02.md`` §4 R-A / R-B): the
    requirement resolver (:func:`resolve_published_net_icr_mw`) and the CR-1
    position's curve-convention transform
    (:func:`~market_sim.model.capacity_evolution.adequacy.
    curve_convention_position`) consult it, so the two can never be armed
    apart. Requires BOTH the default-OFF ``ScenarioConfig.
    neiso_net_icr_requirement`` gate AND an entry for ``iso`` in
    :data:`NET_ICR_REQUIREMENT_MW_BY_ISO` (NEISO alone — rule 25
    ``[R-ISO-SCOPE]``: the flag armed on any other ISO's run is inert by
    construction). ``config=None`` / ``iso=None`` resolve False.
    """
    if config is None or iso is None:
        return False
    if not getattr(config, "neiso_net_icr_requirement", False):
        return False
    return iso in NET_ICR_REQUIREMENT_MW_BY_ISO


def resolve_published_net_icr_mw(
    config: ScenarioConfig | None,
    iso: str | None,
    peak_demand_mw: float,
    year: int | None,
) -> float | None:
    """Published Net ICR (MW, before DR netting) for ``iso``'s delivery year, or None.

    The NEISO analogue of :func:`resolve_forecast_pool_requirement` (capx D40,
    2026-09-02 — see :data:`NET_ICR_REQUIREMENT_MW_BY_ISO`'s citation block for
    the identification and the D33 measurement it repairs). Resolution, in
    order:

    1. Gate: :func:`net_icr_requirement_armed` must hold (the default-OFF
       ``neiso_net_icr_requirement`` flag AND a registry entry for the ISO);
       otherwise ``None`` — the caller keeps its composite, byte-identically.
    2. ``year`` maps to the Capacity Commitment Period that BEGINS in it
       (``"YYYY/YYYY+1"``; ISO-NE's CCP runs June–May, so model calendar
       ``2023`` prices against FCA 14's 2023/24 Net ICR — the same start-year
       labelling the FPR table uses for PJM's June-start delivery year). The
       label is built here rather than through
       ``capacity_deliverability.resolve_delivery_year`` because that helper
       keys its planning-year set on the clean-partition alias ``ISONE`` and
       returns a bare calendar label for the model name ``NEISO``.
    3. An in-table CCP returns its ABSOLUTE published Net ICR — the auction's
       own denominator; the model's peak drops out (D33 R-A shape (i)).
    4. Strictly beyond the last published CCP: HOLD-LAST (card C-A
       2026-08-25), realised as ``peak_demand_mw × NET_ICR_HOLD_LAST_RATIO``
       — the last CCP's published Net-ICR-to-50/50-peak ratio, so the held
       bar still scales with load (an absolute MW held over a 2028–2050
       horizon would fail the rule-13 forward test; see the registry
       comment). Superseded per CCP the moment the ISO publishes it.
    5. Before the first published CCP, or an in-table gap: ``None`` — the
       composite fallback, exactly the PJM convention (the table's FORWARD
       edge only is extended; a mid-table hole is a data problem hold-last
       must not paper over).

    The returned quantity is the RAW (gross-of-DR) requirement; the caller
    nets the ISO's DR fraction (which is defined as a fraction OF Net ICR)
    to obtain the firm-capacity bar the floor, backstop and CR-1 position
    test. ``year=None`` returns ``None`` (the composite path).
    """
    if year is None or not net_icr_requirement_armed(config, iso):
        return None
    table = NET_ICR_REQUIREMENT_MW_BY_ISO.get(iso or "")
    if not table:
        return None
    label = f"{int(year)}/{int(year) + 1}"
    net_icr = table.get(label)
    if net_icr is not None:
        return float(net_icr)
    last_label = max(table, key=lambda lbl: int(lbl[:4]))
    if int(year) > int(last_label[:4]):
        ratio = NET_ICR_HOLD_LAST_RATIO_BY_ISO.get(iso or "")
        if ratio is None:
            # A series with no published hold ratio has nothing lawful to
            # hold; fall through to the composite rather than freeze a MW.
            return None
        return float(peak_demand_mw) * float(ratio)
    return None


def nyiso_requirement_forecast_peak_armed(
    config: ScenarioConfig | None, iso: str | None
) -> bool:
    """True when ``iso`` prices its adequacy requirement on the PUBLISHED forecast peak.

    The gate predicate (rule 19) behind the capx D52 item-1 repair
    (``FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md`` §5.2.4 item 1):
    requires BOTH the default-OFF ``ScenarioConfig.nyiso_requirement_forecast_peak``
    gate AND an entry for ``iso`` in :data:`NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO`
    (NYISO alone — rule 25 ``[R-ISO-SCOPE]``: the flag armed on any other ISO's
    run is inert by construction). ``config=None`` / ``iso=None`` resolve False.
    """
    if config is None or iso is None:
        return False
    if not getattr(config, "nyiso_requirement_forecast_peak", False):
        return False
    return iso in NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO


def nyiso_requirement_vintage_factors_armed(
    config: ScenarioConfig | None, iso: str | None
) -> bool:
    """True when ``iso`` prices adequacy on the capability year's adopted IRM × (1 − derate).

    The gate predicate (rule 19) behind the capx D52 item-2 repair (D45 §5.2.4
    item 2, the D40 vintage axis on the NYISO composite): requires BOTH the
    default-OFF ``ScenarioConfig.nyiso_requirement_vintage_factors`` gate AND
    an entry for ``iso`` in BOTH :data:`NYCA_IRM_ADOPTED_BY_ISO` and
    :data:`NYCA_ICAP_UCAP_TRANSLATION_BY_ISO` (NYISO alone — rule 25).
    ``config=None`` / ``iso=None`` resolve False.
    """
    if config is None or iso is None:
        return False
    if not getattr(config, "nyiso_requirement_vintage_factors", False):
        return False
    return iso in NYCA_IRM_ADOPTED_BY_ISO and iso in NYCA_ICAP_UCAP_TRANSLATION_BY_ISO


def _nyiso_capability_year_label(year: int) -> str:
    """NYISO capability-year label (May Y – April Y+1) for model calendar ``year``.

    Built here as ``"YYYY/YYYY+1"`` for the same reason
    :func:`resolve_published_net_icr_mw` builds ISO-NE's CCP label itself: the
    model's summer peak (the adequacy test) falls inside the capability year
    that BEGINS in ``year``, so the row read for model year Y is the row every
    parameter of which was fixed before May 1, Y (the rule-13 information gate
    — see :data:`NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO`'s citation block).
    """
    return f"{int(year)}/{int(year) + 1}"


def resolve_nyiso_requirement_peak_mw(
    config: ScenarioConfig | None,
    iso: str | None,
    peak_demand_mw: float,
    year: int | None,
) -> float:
    """The peak (MW) the adequacy requirement is priced on — published or the model's.

    capx D52 item 1 (D45 §5.2.4): when :func:`nyiso_requirement_forecast_peak_armed`
    holds and ``year``'s capability year is in
    :data:`NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO`, return the PUBLISHED NYSRC
    ICAP-market forecast peak of that capability year — the peak the NYCA
    requirement was actually set on (Table D.2 column 1), so the requirement
    stops depending on the model's realized/growth-scaled peak in exactly the
    years the market's own requirement did not. Every other case — unarmed,
    off-registry, ``year=None``, a capability year outside the table (before
    it, or the forward horizon beyond it) — returns ``peak_demand_mw`` ITSELF
    (the same object, not a copy or a recomputation), so the caller's product
    is byte-identical. Deliberately NO hold-last: beyond the table the model's
    own peak IS the forward load forecast (the Gold Book analogue), and a held
    MW peak against a growing load would fail the rule-13 forward test.
    """
    if year is None or not nyiso_requirement_forecast_peak_armed(config, iso):
        return peak_demand_mw
    table = NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO.get(iso or "")
    if not table:
        return peak_demand_mw
    published = table.get(_nyiso_capability_year_label(year))
    if published is None:
        return peak_demand_mw
    return float(published)


def resolve_nyiso_requirement_factor(
    config: ScenarioConfig | None, iso: str | None, year: int | None
) -> float | None:
    """The capability year's adopted-IRM × (1 − derate) requirement factor, or None.

    capx D52 item 2 (D45 §5.2.4; the D40 per-vintage axis on the NYISO
    composite ``(1 + PRM) × icap_to_ucap_ratio``). Resolution, in order:

    1. Gate: :func:`nyiso_requirement_vintage_factors_armed` must hold and
       ``year`` must be given; otherwise ``None`` — the caller keeps the
       single-vintage composite byte-identically.
    2. An in-table capability year (both registries carry it) returns
       ``(1 + IRM_adopted) × (1 − derate)`` for THAT capability year — the
       published ``UCAP requirement ÷ forecast peak`` of Table D.2 (the two
       tables are asserted to carry the same capability years by test).
    3. Strictly beyond the last published capability year: HOLD-LAST (card
       C-A 2026-08-25) as the last published pair's ratio (2025/26:
       ``1.244 × 0.870``), so the held bar still scales with load exactly as
       the composite does — superseded per capability year on publication
       (rule 23).
    4. Before the first published capability year, or an in-table gap: ``None``
       (the composite fallback, the PJM/NEISO convention: the table's forward
       edge only is extended).
    """
    if year is None or not nyiso_requirement_vintage_factors_armed(config, iso):
        return None
    irm_table = NYCA_IRM_ADOPTED_BY_ISO.get(iso or "")
    derate_table = NYCA_ICAP_UCAP_TRANSLATION_BY_ISO.get(iso or "")
    if not irm_table or not derate_table:
        return None
    label = _nyiso_capability_year_label(year)
    irm, derate = irm_table.get(label), derate_table.get(label)
    if irm is not None and derate is not None:
        return (1.0 + float(irm)) * (1.0 - float(derate))
    last_label = max(set(irm_table) & set(derate_table), key=lambda lbl: int(lbl[:4]))
    if int(year) > int(last_label[:4]):
        return (1.0 + float(irm_table[last_label])) * (
            1.0 - float(derate_table[last_label])
        )
    return None


def resolve_adequacy_requirement_mw(
    config: ScenarioConfig, iso: str, peak_demand_mw: float, year: int | None = None
) -> float:
    """Return the firm-capacity requirement shared by the floor and backstop.

    Three constructions, in preference order (R2, accreditation-basis memo
    2026-07-12 §4.2 — "resolve the requirement from the published FPR of the
    matching delivery year; fall back to ``(1 + PRM) x ratio`` otherwise";
    extended by capx D40 with the ISO-NE Net ICR analogue):

    0. **Published Net ICR series (NEISO, GATED default-OFF).** When
       ``config.neiso_net_icr_requirement`` is armed and the ISO carries a
       :data:`NET_ICR_REQUIREMENT_MW_BY_ISO` entry
       (:func:`resolve_published_net_icr_mw`), the requirement is
       ``Net_ICR_ccp × (1 − dr_fraction)`` for an in-table delivery year — the
       auction's own absolute denominator, the model's peak dropping out — and
       ``peak × hold_ratio × (1 − dr_fraction)`` strictly beyond the last
       published CCP (card C-A hold-last, realised as the last CCP's
       published Net-ICR/peak ratio). Pre-table years and in-table gaps fall
       through. Repairs the single-vintage composite artifact D33 measured
       (+23.8 reserve-ratio points of requirement error in 2023). Off — the
       default — every NEISO solve is byte-identical to the two paths below.

    1. **Published Forecast Pool Requirement.** When ``year`` resolves to a
       delivery year the ISO publishes an FPR for
       (:func:`resolve_forecast_pool_requirement`), the requirement is
       ``firm_peak x FPR`` — the ISO's own UCAP-basis requirement, with the
       reserve margin and the ICAP->UCAP conversion already folded into the
       one published number. This is literally the ISO's own construction
       (devintages the mixed-vintage ``1.178 x 0.7699 = 0.907`` composite the
       fallback builds onto the published 2026/2027 FPR ``0.9170``). Beyond
       the ISO's LAST published FPR the resolver HOLDS-LAST (card C-A
       2026-08-25 — see its docstring), so a forecast horizon never falls off
       the published series onto the stale composite mid-horizon.
    2. **Fallback ``firm peak x (1 + PRM_iso) x icap_to_ucap_ratio_iso``**
       (byte-identical to the pre-R2 behaviour) for any ISO/year without a
       published or held-last FPR. The ``icap_to_ucap_ratio`` factor (stage-5 §6 ICAP/UCAP
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
    # capx D40: the published Net ICR path (gated; None whenever unarmed,
    # off-registry, pre-table, in-gap or year-less). The DR fraction is
    # defined as a share OF the Net ICR (registry citation), so netting it
    # from the published quantity reproduces ISO-NE's own DCR-CSO counting.
    net_icr_raw_mw = resolve_published_net_icr_mw(config, iso, peak_demand_mw, year)
    if net_icr_raw_mw is not None:
        return net_icr_raw_mw * (1.0 - dr_fraction)
    # capx D48: the gross (un-netted) requirement — pre-reform FPR under the
    # accreditation-design devintage, else the published/held-last FPR, else
    # the composite — factored out so the DR-as-supply hold-last can scale by
    # it. Netting the gross requirement by (1 − f) is algebraically identical
    # to netting the peak first (both paths are peak × (1 − f) × factor).
    gross_mw = gross_adequacy_requirement_mw(config, iso, peak_demand_mw, year)
    # capx D48 DR-as-supply: when the ISO's published DR is COUNTED on the
    # supply ledger for this delivery year (resolve_demand_response_supply_mw
    # returns a MW), the peak is NOT netted — the requirement is the auction's
    # own un-netted Reliability Requirement (PJM Manual 18 §3.4's VRR x-basis).
    # Unarmed / off-registry / pre-table / year-less → None → netting as before.
    if resolve_demand_response_supply_mw(config, iso, year, gross_mw) is not None:
        return gross_mw
    return gross_mw * (1.0 - dr_fraction)


def resolve_internal_supply_accounting_ratio(
    iso: str | None, config: ScenarioConfig | None = None
) -> float:
    """Ratio of the market's counted internal supply to the model's census ledger.

    The single resolver (rule 19) for the internal-supply accounting wedge
    (:data:`ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO` — see its
    citation block for the MISO identification, capx D31): applied to every
    INTERNAL contribution wherever firm capacity is summed toward the
    adequacy requirement — :func:`~market_sim.model.capacity_evolution.
    adequacy.accredited_firm_capacity_mw` (hence the CR-1 reserve position),
    :func:`_apply_reliability_floor`'s per-unit retention increments, and the
    build backstop's crediting of a new unit — so the position, the floor and
    the backstop stay on ONE basis. Deliberately NOT applied to per-unit
    capacity revenue (:func:`thermal_accreditation_fraction` is untouched):
    the aggregate wedge includes non-participants, while a unit that clears
    earns its own accredited revenue. ISOs absent from the registry — and
    ``iso=None`` — resolve the neutral 1.0 byte-identically.

    ``config`` (optional; ``None`` keeps the D31 registry byte-identically)
    carries the capx D51 gate ``adequacy_accounting_ratio_dated_net``: armed,
    an ISO with an entry in
    :data:`ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO` resolves
    that value — the SAME ratio re-identified on the fleet in the posture the
    run applies (net of the fossil-dates channel's exits, D49 §2.6) — at every
    one of the three call sites above, so the one-basis property is
    preserved; an ISO absent from the dated-net registry falls through to the
    D31 value even when armed (rule 25 [R-ISO-SCOPE]).
    """
    key = iso or ""
    if config is not None and getattr(
        config, "adequacy_accounting_ratio_dated_net", False
    ):
        dated = ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO.get(key)
        if dated is not None:
            return dated
    return ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO.get(key, 1.0)


def thermal_accreditation_fraction(
    fuel_type: str,
    eford: float,
    iso: str | None,
    config: ScenarioConfig | None = None,
    year: int | None = None,
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

    ``iso=None`` keeps the legacy UCAP basis byte-identically. ``config`` and
    ``year`` (both optional, default ``None``) thread the capx D48
    accreditation-design devintage through
    :func:`resolve_thermal_accreditation_basis`: armed, a delivery year
    before the ISO's reform date resolves ``"ucap"`` whatever the registry
    says; unarmed or year-less, the registry basis — byte-identical.
    """
    basis = resolve_thermal_accreditation_basis(iso, config, year)
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


def _thermal_firm_mw(
    g: Generator,
    iso: str | None,
    config: ScenarioConfig | None = None,
    year: int | None = None,
) -> float:
    """Firm MW one dispatchable unit contributes to the adequacy ledger.

    ``pmax`` times the unit's basis-resolved accreditation fraction
    (:func:`thermal_accreditation_fraction` —
    :data:`THERMAL_ACCREDITATION_BASIS_BY_ISO`, devintaged per delivery year
    under the capx D48 arm when ``config``/``year`` are threaded). ``iso=None``
    keeps the legacy UCAP basis.
    """
    return float(g.pmax_mw) * thermal_accreditation_fraction(
        g.fuel_type, g.eford, iso, config, year
    )


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
    nqc_curves_enabled: bool = False,
) -> float | None:
    """Resolve one VRE class's adequacy capacity credit (CR-3.1 ladder).

    The ONE resolver every adequacy consumer prices VRE accreditation
    through (rule 19): :func:`accredited_firm_capacity_mw` and, through it,
    the retirement reliability floor, the reserve-margin backstop and the
    CR-1 reserve position all move together. Resolution ladder:

    0. **Published class-average accreditation held behind its own gate**
       (:data:`RENEWABLE_NQC_CURVES_BY_ISO`, gate
       ``ScenarioConfig.caiso_nqc_accreditation`` — CAISO's CPUC/CAISO NQC
       technology factors, FFR-3P). Same registry shape and same evaluator as
       rung 1; it is a separate registry ONLY because the rung-1 gate ships
       default-ON and this arm must ship default-OFF pending an owner decision
       (rules 5/24). ``nqc_curves_enabled=False`` (the default) skips it
       entirely, so an unarmed run is byte-identical to the pre-FFR-3P ladder.
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
    if nqc_curves_enabled and iso is not None:
        nqc_curve = RENEWABLE_NQC_CURVES_BY_ISO.get(iso, {}).get(fuel_type)
        if nqc_curve is not None:
            credit = evaluate_renewable_elcc_curve(
                nqc_curve, installed_mw, peak_demand_mw
            )
            if credit is not None:
                return credit
    if curves_enabled and iso is not None:
        curve = RENEWABLE_ELCC_CURVES_BY_ISO.get(iso, {}).get(fuel_type)
        if curve is not None:
            credit = evaluate_renewable_elcc_curve(curve, installed_mw, peak_demand_mw)
            if credit is not None:
                return credit
    return _renewable_credit(fuel_type, iso)


def _floor_retention_merit(
    config: ScenarioConfig, g: Generator, year: int | None = None
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
    firm_mw = _thermal_firm_mw(g, config.iso, config, year)
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
    # Imported here to avoid a module-level cycle: adequacy.py imports the
    # shared adequacy-requirement / accreditation helpers from this module.
    from .adequacy import accredited_firm_capacity_mw

    accredited_mw = accredited_firm_capacity_mw(
        survivors,
        wind_pool_mw,
        solar_pool_mw,
        storage_firm_mw,
        iso=config.iso,
        peak_demand_mw=peak_demand,
        elcc_curves_enabled=config.renewable_elcc_curves,
        nqc_curves_enabled=config.caiso_nqc_accreditation,
        config=config,
        accreditation_year=year,
    )
    retention_log: list[dict] = []
    if accredited_mw >= requirement_mw:
        return retention_log
    for g in sorted(eligible, key=lambda g: _floor_retention_merit(config, g, year)):
        if accredited_mw >= requirement_mw:
            break
        if g.unit_id not in retired:
            continue
        if _zone_is_long(deliverability_headroom, g.zone):
            continue  # RA-saturated zone: no adequacy value in retaining here
        retired.discard(g.unit_id)
        # One basis with the aggregate test above (rule 19): the retained
        # unit's increment carries the same internal-supply accounting ratio
        # accredited_firm_capacity_mw applied to the ledger it adds to.
        firm_mw = _thermal_firm_mw(g, config.iso, config, year) * (
            resolve_internal_supply_accounting_ratio(config.iso, config)
        )
        accredited_mw += firm_mw
        cost_per_firm_mw, co2_rate, _hr = _floor_retention_merit(config, g, year)
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
    exit_rate_cap_mw: float | None,
    margin_detail: dict[str, dict[str, float | str]] | None = None,
    exogenous_exits: list | None = None,
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
       the fuel-partitioned eligible set). The cap is tested at the
       schedule's EXECUTION horizon, not the decision year
       (:func:`_admission_cap_horizon` — the G-31 cap-grain correction,
       FFR-3F/D-8): the counterfactual fleet it screens is realized when the
       last scheduled exit leaves, so the requirement is resolved at that
       year and that year's projected peak.
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
       execution separately. When the caller supplies ``margin_detail``
       (:func:`apply_economic_retirements` always does), every row also
       carries the FFR-5A bar decomposition — both bar sides, the per-leg
       revenue split and the screen-basis descriptors — so a ledger reader
       can attribute which leg moved a unit across the bar, and whether the
       bar was the same object between two screen years, without replaying
       the solve. Diagnostic only: rows record the decision, never shape it.

    ``exogenous_exits`` (capx D42, the fossil announced-date channel's
    rule-19 reconciliation; ``None``/empty is byte-identical): owner-filed
    exit rows still pending after this screen. The ADMISSION cap's
    counterfactual fleet nets every such row due by the cap horizon
    (:func:`apply_confirmed_exits` applied year by year from ``year + 1`` to
    ``cap_year``), so the floor's retention pool sees the dated units as
    scheduled exogenous exits: it can neither retain them (they are never in
    ``eligible`` — their plants are exempt from the screen upstream) nor
    over-admit other candidates against capacity that is leaving anyway. The
    realized-year EXECUTION floor is untouched: it tests the post-step-1
    fleet, from which this year's dated exits are already gone.

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
        # FFR-5A bar decomposition (diagnostic row fields; the decision this
        # row records was already made from net_revenue vs going_forward_cost
        # alone). Absent margin_detail (legacy callers/tests) rows are
        # byte-identical to the pre-enrichment schema.
        if margin_detail is not None:
            row.update(margin_detail.get(g.unit_id, {}))
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
    decided_year = year - 1  # the loss year whose dispatch failed this screen
    cap_year, cap_peak_demand = _admission_cap_horizon(
        config, scheduled, state, decided_year, fleet, peak_demand, year
    )
    # capx D42: the counterfactual the cap screens is the fleet at the cap
    # horizon, so every exogenous dated exit landing by then is netted out
    # of it (see the docstring). Empty ⇒ ``cap_fleet is fleet``.
    cap_fleet = fleet
    if exogenous_exits:
        for _y in range(year + 1, cap_year + 1):
            cap_fleet = apply_confirmed_exits(cap_fleet, _y, exogenous_exits)
    _apply_reliability_floor(
        cap_fleet,
        new_units,
        scheduled,
        state,
        config,
        cap_peak_demand,
        wind_pool_mw,
        solar_pool_mw,
        storage_firm_mw,
        deliverability_headroom,
        cap_year,
    )
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
    # --- Exit throughput (ScenarioConfig.exit_rate_limits; owner D-8). The
    # queue's SECOND property: the lag above set who is due, this bounds how
    # many MW may actually leave this year. Applied BEFORE the reliability
    # floor because the floor is the last-resort adequacy backstop and must
    # see the set that is genuinely leaving; a unit deferred here stays
    # pipelined and re-presents at the head of next year's queue.
    throughput_deferred: list[Generator] = []
    if exit_rate_cap_mw is not None and due:
        due, throughput_deferred = _apply_exit_throughput_cap(
            due, state, exit_rate_cap_mw
        )
        for g in throughput_deferred:
            events.append(_event("throughput_deferred", g, state[g.unit_id]))
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

    if retired or throughput_deferred:
        logger.info(
            "year %d: R-NEW pipeline executed %d exit(s), %.0f MW "
            "(%d pending, %d entry-capped, %d reversed, "
            "%d throughput-deferred / %.0f MW)",
            year,
            len(retired),
            sum(float(g.pmax_mw) for g in due if g.unit_id in retired),
            len(state),
            sum(1 for e in events if e["event"] == "entry_capped"),
            sum(1 for e in events if e["event"] == "reversed"),
            len(throughput_deferred),
            sum(float(g.pmax_mw) for g in throughput_deferred),
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
        # Kept distinct from floor_retained: a throughput deferral is a queue
        # rate limit, a floor retention is an adequacy backstop. Collapsing
        # them would make the D-2 mechanism attribution unreadable.
        event_sink["throughput_deferred"] = [
            {"unit_id": g.unit_id, "fuel": g.fuel_type, "mw": float(g.pmax_mw)}
            for g in throughput_deferred
        ]
    return survivors, state, floor_retention_log


def apply_economic_retirements(
    fleet: list[Generator],
    fleet_arrays: FleetArrays,
    dispatch_result: DispatchResult,
    prices: np.ndarray,
    config: ScenarioConfig,
    consecutive_loss_years: dict[str, int],
    peak_demand: float,
    rps_shadow_price: "float | np.ndarray" = 0.0,
    clean_attribute_price_by_fuel: "dict[str, np.ndarray] | None" = None,
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
    exempt_unit_ids: frozenset[str] = frozenset(),
    exit_rate_cap_mw: float | None = None,
    exogenous_exits: list | None = None,
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

    Attribute revenue (EAC / RPS / §45U) is credited on the matching
    **attainable in-merit generation** (``cap_mw * 1[price > mc]``) rather
    than realized dispatch, so the whole screen — energy margin and
    attribute term alike — is a function of prices, ``mc`` and capacity
    only. That makes the retire/keep decision invariant to the
    alternate-optima reshuffle among units tied at the marginal price
    (warm-start backlog #4; see ``docs/cross-year-warmstart.md``).

    ``mc`` is the unit's *full* variable cost (fuel + VOM + emission
    prices), not its bid: take-or-pay coal tranches bid below fuel cost in
    dispatch because the fuel is sunk within the contract year, but on a
    retirement horizon the contract lapses, so fuel is avoidable and counts
    against the margin. When ``mc`` is ``None`` the screen degrades to the
    legacy gross-energy-revenue-on-dispatch comparison, which overstates
    margins and under-retires -- callers should always supply ``mc``.

    How a failing screen becomes a realized exit is selected by
    ``config.retirement_rule`` (FF-1A):

    * ``"legacy"`` (default): a year in which
      ``net_revenue < going_forward_cost`` increments the unit's
      consecutive-loss counter; a profitable year resets it to zero. Once
      the counter reaches the unit's per-fuel ``retirement_years_*``
      threshold the unit retires. Fuel types without a specific override
      fall back to ``config.retirement_consecutive_years``. Byte-identical
      to every committed run.
    * ``"pipeline"``: the R-NEW decision/execution split
      (:func:`_apply_pipeline_retirements`) — uniform one-screen decision,
      joint adequacy-capped cross-fuel pipeline entry, soft annual
      re-confirmation latch, and deactivation after the measured per-fuel
      ``retirement_execution_lag_*``. Under this rule the
      ``consecutive_loss_years`` dict threads the pipeline state
      (``unit_id -> decided_year``) through the same cross-year seam.

    The fixed-cost multiplier is fuel-type-aware under both rules (coal
    carries a higher effective fixed cost than gas — regulatory/ESG risk);
    fuels without an override use a multiplier of ``1.0``.

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
        rps_shadow_price: Prior year's RPS constraint dual in $/MWh — a
            scalar (legacy single ISO-wide row) or a per-zone ``(n_zones,)``
            vector (K-row compliance-region grain, FFR-7B Arm 2), resolved
            at each unit's zone via ``policy.rps.rps_credit_for_zone``. Only
            credited to RPS-eligible (clean) fuels, and never stacked with
            an exogenous EAC -- the higher of the two is taken.
        clean_attribute_price_by_fuel: Prior year's clean-tier row duals
            mapped to per-(fuel, zone) credits (FFR-7B Arm 3,
            ``policy.clean_tiers.clean_credit_by_fuel``) — the first LP
            attribute channel that pays nuclear/hydro. Enters the SAME
            max() attribute doctrine, never a sum. ``None`` (family off)
            is byte-identical.
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
        exempt_unit_ids: Unit ids excluded from this year's screen entirely
            (no margin evaluation, no counter change). Also carries, under
            ``config.fossil_announced_exits_enabled`` (capx D42), the units
            whose plant holds a pending owner-filed exit row
            (:func:`dated_plant_unit_ids`) — exogenous to the screen by the
            rule-19 reconciliation. Used by
            :func:`evolve_fleet` for units CCS-retrofitted THIS year (W2-C
            joint choice): the just-converted unit's prior-year ``mc`` rows
            price its old unabated cost basis, so screening it in the same
            instant it spent the retrofit capex would be incoherent — it
            re-enters the screen as ``gas_cc_ccs`` next year on its own
            post-retrofit dispatch. Default empty ⇒ byte-identical.
        exit_rate_cap_mw: The year's deactivation-throughput budget in MW
        exogenous_exits: capx D42 — pending owner-filed fossil exit rows the
            R-NEW admission cap nets from its counterfactual fleet (see
            :func:`_apply_pipeline_retirements`). ``None`` is byte-identical;
            the legacy rule ignores it (its floor tests the realized fleet).
            (``ScenarioConfig.exit_rate_limits``; owner decision D-8), or
            ``None`` for no cap. Pipeline rule only. Bounds how many MW of
            DUE exits actually execute this year, strict-FIFO by decided
            year; the remainder stays pipelined and re-presents next year.
            The execution lag and this cap are the latency and throughput of
            ONE queue and cannot double-count — the lag sets who is due, the
            cap sets how much of the due set is processed (rule 19; see
            :func:`_apply_exit_throughput_cap`). ``None`` (default) is
            byte-identical.

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

    # Per-unit screen margins, shared by both decision rules: the uniform
    # net_revenue vs going_forward_cost comparison is computed once here;
    # the rules differ only in how a failing screen becomes a realized exit.
    margins: list[tuple[Generator, float, float]] = []
    # FFR-5A ledger enrichment: per-unit decomposition of both sides of the
    # bar, merged onto that unit's pipeline_events rows (pipeline rule only).
    # Diagnostic row fields, no decision effect (rule 24: not a tunable).
    margin_detail: dict[str, dict[str, float | str]] = {}
    for g in fleet:
        if g.unit_id in exempt_unit_ids:
            # CCS-retrofitted this year (W2-C): decision already made; the
            # unit re-enters the screen as gas_cc_ccs next year.
            continue
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
        # Per-leg accumulators for the FFR-5A ledger enrichment (diagnostic
        # row fields on pipeline_events; no decision effect, no tunable —
        # rule 24 untouched): the energy-only pro-forma and the increment the
        # reserve fold adds, so a ledger reader can attribute WHICH leg moved
        # a unit across the bar without replaying the solve.
        energy_margin_usd = 0.0
        reserve_uplift_usd = 0.0
        if mc is None:
            net_revenue = float(sum(np.dot(prices[zone], dispatch[i]) for i in rows))
            energy_margin_usd = net_revenue
        else:
            net_revenue = 0.0
            for i in rows:
                base_value = np.maximum(prices[zone] - mc[i], 0.0)
                energy_margin_usd += float(np.dot(base_value, cap_mw[i]))
                hourly_value = base_value
                if r_row is not None:
                    hourly_value = np.maximum(hourly_value, r_row)
                net_revenue += float(np.dot(hourly_value, cap_mw[i]))
            reserve_uplift_usd = net_revenue - energy_margin_usd

        # The attribute payment -- the higher of the exogenous EAC and the
        # endogenous RPS shadow price, never their sum -- adds revenue
        # beyond the energy market, keeping units that energy prices alone
        # would not. The RPS shadow price is credited only to RPS-eligible
        # (renewable) fuels -- wind/solar -- never to nuclear or hydro, which
        # are clean but not renewable (CX-6a, plan §6.5(a)). Nuclear retention
        # support instead flows through eac_price (ZEC/CES).
        # Credited on ATTAINABLE in-merit generation, never realized dispatch
        # (warm-start backlog #4, docs/cross-year-warmstart.md "Why the forecast
        # path is not wired"): the MW the unit could sell in the hours its own
        # cost basis clears the price, ``cap_mw x 1[price > mc]``. Cross-year
        # warm start splits units tied AT the marginal price differently between
        # alternate optima — the LP is genuinely indifferent (objective, every
        # zonal price and total generation stay bit-identical) — so a realized
        # reader lets a wall-clock lever tip a retire/keep decision and change
        # the next year's fleet. The attainable quantity is a function of
        # prices/mc/capacity alone, so the screen is invariant to any tie split.
        # This is the SAME cap_mw / rows / zone the attainable net_revenue loop
        # above already builds — one notion of capacity, availability-derated
        # (rule 19, one mechanism per phenomenon). In-merit is the energy test
        # ``price > mc``, not the reserve leg: EAC/RPS/§45U are per-MWh credits
        # on energy produced, and a unit holding reserve is not generating.
        if mc is None:
            # Legacy gross-revenue fallback (warned above): with no cost basis
            # there is no in-merit test to define, so the deprecated path keeps
            # its realized reader rather than inventing a second capacity notion.
            credited_mw_rows = [dispatch[i] for i in rows]
        else:
            credited_mw_rows = [
                np.where(prices[zone] > mc[i], cap_mw[i], 0.0) for i in rows
            ]
        annual_gen_mwh = float(sum(np.sum(row_mw) for row_mw in credited_mw_rows))
        # Effective attribute price (W2-A plan §5.3): max(legacy per-fuel
        # eac_price_*, federal CES premium × the UNIT's credit fraction) —
        # unit-level so that under cesa_ci a credited unabated gas_cc (or an
        # abated unit's actual residual CI) earns its own fraction on its
        # own CO2 rate. Exactly the legacy value when the CES is disabled.
        # Taken as its two LEGS rather than the fold, because §45U's
        # gross-receipts test below puts them on opposite branches of
        # §45U(b)(2)(B) (D-28; see the §45U block). The fold itself — and so
        # every attribute price this screen credits — is unchanged.
        state_eac_price, federal_ces_price = eac_price_components_for_unit(
            config, g.fuel_type, g.emission_rate_co2, year
        )
        eac_price = max(state_eac_price, federal_ces_price)
        # RPS credit resolved at the UNIT's zone under the K-row
        # compliance-region grain (FFR-7B Arm 2 / FFR-6B §3.2): a scalar
        # passes through; a per-zone vector indexes by the unit's own zone,
        # so a unit outside every region's eligibility geography earns 0 —
        # never a broadcast of another region's dual.
        rps_for_unit = (
            rps_credit_for_zone(rps_shadow_price, zone)
            if g.fuel_type in _RPS_ELIGIBLE_FUELS
            else 0.0
        )
        # Clean-tier credit (FFR-7B Arm 3, FFR-6B §6.4): the clean row's
        # dual enters the EXISTING max() attribute doctrine — for nuclear
        # and hydro this is the first LP row that pays them at all — never
        # a sum: one certificate, sold to whichever attribute market clears
        # higher. Fuel- AND zone-resolved (a gas_cc_ccs unit in MISO-West
        # earns nothing from MN's row, whose carbon-free definition
        # excludes CCS gas). §45U COMPOSITION IS SETTLED (owner decision
        # D-28 option A, docs/handoffs/d28-45u-composition-memo-2026-08-08.md
        # §5): §45U left this max() and now composes with its winner below,
        # so the clean dual's §45U arming blocker is CLOSED. FFR-6B §6.4
        # row 3 is discharged; arming miso_clean_tier_rows is a separate
        # charter on its own per-ISO evidence (rule 25).
        clean_for_unit = clean_credit_for_zone(
            clean_attribute_price_by_fuel, g.fuel_type, zone
        )
        attribute_revenue_usd = compute_attribute_revenue(
            g.fuel_type, annual_gen_mwh, eac_price, max(rps_for_unit, clean_for_unit)
        )
        net_revenue += attribute_revenue_usd

        # IRA §45U existing-nuclear PTC (26 U.S.C. §45U; owner decision D-28
        # option A, memo §1.3/§3.2/§5). §45U is NOT an attribute buyer, so it
        # no longer competes inside the max() above. There are two distinct
        # phenomena, and rule 19 [R-ONE-MECH] wants one mechanism for each:
        #   1. "who buys this MWh's clean attribute" — one certificate, several
        #      competing buyers (state EAC contract, federal CES premium, RPS
        #      row, clean-tier row), resolved by the max() above, UNCHANGED;
        #   2. "what does Treasury pay this reactor for a zero-emission MWh" —
        #      §45U, which carries its OWN statutory anti-double-dip keyed to
        #      phenomenon 1's outcome. That is §45U(b)(2)(B), and it has two
        #      branches, both of which cap total support:
        #      (i)   default — a zero-emission-credit-program payment is INSIDE
        #            the gross-receipts base, so each $1 of attribute costs
        #            0.80 $ of credit (16 % x the (d)(1) 5x). Pays D + §45U(P+D).
        #      (iii) exclusion — where the state program itself nets the full
        #            federal credit out of its own payment, the payment leaves
        #            the base and the state tops the unit up to its own target.
        #            Pays max(D, §45U(P)).
        # Branch assignment, per instrument (memo §1.3, §5):
        #   * state_eac_price (eac_price_nuclear, documented as the NY ZEC /
        #     IL carbon-mitigation-credit design — a target net of the unit's
        #     other revenue) is a genuine branch-(iii) netting contract;
        #   * the federal CES premium, the RPS dual and the Arm-3 clean-tier
        #     dual are LSE-paid compliance certificates with no federal-credit
        #     offset anywhere in them — branch (i).
        # The unit sells ONE certificate, so it takes whichever route pays more;
        # each route's total is monotone in its own price, so the winner within
        # branch (i) is still that branch's max(). Both route totals are >= the
        # attribute price already credited above, so the increment added here is
        # the credit net of any branch-(iii) clawback, never a second attribute.
        # Nuclear only; needs a simulation year to evaluate the expiry after
        # config.ira_45u_last_year (None on legacy callers -> no §45U). See
        # policy.ira.section_45u_credit_per_mwh.
        #
        # Backlog-#4 adjudication — the phase-down basis is ATTAINABLE on
        # BOTH sides of the ratio, not just the denominator:
        #  (a) Tie-invariance is NOT provable for the realized ratio. A ratio of
        #      two realized quantities can be tie-invariant, but this one is not:
        #      a marginal-tie reshuffle moves realized MW BETWEEN HOURS carrying
        #      different prices, so the generation-weighted average
        #      sum_t(p_t*d_t) / sum_t(d_t) shifts even though every p_t and the
        #      LP objective are bit-identical. It is invariant only in the
        #      special case where all reshuffled hours share one price, which is
        #      not the general case — so a realized §45U basis would re-open
        #      exactly the channel this fix closes.
        #  (b) The statutory reading is preserved, not abandoned. §45U's basis is
        #      gross receipts from electricity sold divided by MWh sold — an
        #      average SALE PRICE — and this whole screen is the Potomac SOM
        #      pro-forma, in which the unit sells its attainable in-merit output.
        #      Taking numerator and denominator from that same attainable
        #      quantity keeps the ratio a true $/MWh average price; mixing bases
        #      (realized receipts over attainable MWh) would be a meaningless
        #      ratio, understating the price and overpaying the credit.
        # The attribute price added to gross receipts under branch (i) rides the
        # SAME attainable MWh (it is a per-MWh certificate price on exactly the
        # output the ratio's denominator counts), so the basis stays one notion
        # of quantity throughout.
        if g.fuel_type == "nuclear" and year is not None and annual_gen_mwh > 0.0:
            gross_energy_revenue = float(
                sum(np.dot(prices[zone], row_mw) for row_mw in credited_mw_rows)
            )
            avg_energy_price = gross_energy_revenue / annual_gen_mwh
            # Branch (i): certificate price inside the gross-receipts base.
            branch_i_price = max(federal_ces_price, rps_for_unit, clean_for_unit)
            branch_i_total = branch_i_price + section_45u_credit_per_mwh(
                year, avg_energy_price + branch_i_price, config
            )
            # Branch (iii): the state contract nets the credit out, so the pair
            # pays the contract, topped up only where the credit is worth more.
            branch_iii_total = max(
                state_eac_price,
                section_45u_credit_per_mwh(year, avg_energy_price, config),
            )
            attribute_price = max(eac_price, rps_for_unit, clean_for_unit)
            section_45u_usd = (
                max(branch_i_total, branch_iii_total) - attribute_price
            ) * annual_gen_mwh
            net_revenue += section_45u_usd

        # Resource-adequacy capacity payment (Module M1): in PJM/NYISO/
        # ISO-NE/CAISO a unit earns a capacity revenue stream that can cover
        # fixed cost even when energy margin is negative, so omitting it
        # over-retires thermal capacity there. Zero in energy-only ERCOT.
        # Locational gate: when capacity_deliverability_limits is on, a unit in a
        # zone already long on deliverable firm capacity vs its requirement earns
        # NO capacity payment (RA saturated there), so surplus in a long zone
        # retires as it should while short zones keep their units.
        capacity_revenue_usd = 0.0
        if not _zone_is_long(deliverability_headroom, g.zone):
            capacity_revenue_usd = g.pmax_mw * capacity_revenue_per_mw_yr(
                config.iso, g.fuel_type, g.eford, config, reserve_position, year
            )
            net_revenue += capacity_revenue_usd

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
        as_annual_credit_usd = 0.0
        if mc is not None and reserve_price_signal is not None:
            # hourly max(energy, reserve) above is the sole AS pricing
            as_pricing = "hourly_signal"
        elif thermal_as_revenue_per_mw_yr is not None:
            as_pricing = "endogenous_annual"
            as_annual_credit_usd = g.pmax_mw * thermal_as_revenue_per_mw_yr.get(
                g.fuel_type, 0.0
            )
            net_revenue += as_annual_credit_usd
        else:
            as_pricing = "exogenous_flat"
            as_annual_credit_usd = g.pmax_mw * as_revenue_per_mw_yr(
                g.fuel_type, storage_power_mw, config
            )
            net_revenue += as_annual_credit_usd

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

        margins.append((g, net_revenue, going_forward_cost))

        # FFR-5A bar decomposition, attached to this unit's pipeline_events
        # rows by _apply_pipeline_retirements (diagnostic only — the decision
        # above consumed net_revenue/going_forward_cost and is already made).
        # Basis descriptors record WHAT price/cost/availability object this
        # screen consumed, so a year-over-year ledger diff can distinguish a
        # genuine economic move from a basis drift between screen years.
        _row_pmax = np.asarray([float(fleet_arrays.pmax[i]) for i in rows], dtype=float)
        _pmax_total = float(_row_pmax.sum())
        detail: dict[str, float | str] = {
            "net_revenue_usd": float(net_revenue),
            "going_forward_cost_usd": float(going_forward_cost),
            "energy_margin_usd": float(energy_margin_usd),
            "reserve_uplift_usd": float(reserve_uplift_usd),
            "attribute_revenue_usd": float(attribute_revenue_usd),
            "capacity_revenue_usd": float(capacity_revenue_usd),
            "as_annual_credit_usd": float(as_annual_credit_usd),
            "as_pricing": as_pricing,
            "screen_price_mean_usd_mwh": float(np.mean(prices[zone])),
            "screen_price_max_usd_mwh": float(np.max(prices[zone])),
            "reserve_signal_mean_usd_mwh": (
                float(np.mean(r_row)) if r_row is not None else 0.0
            ),
            "availability_mean": (
                float(
                    sum(
                        float(_row_pmax[k]) * float(np.mean(availability[i]))
                        for k, i in enumerate(rows)
                    )
                    / _pmax_total
                )
                if _pmax_total > 0.0
                else 0.0
            ),
        }
        if mc is not None and _pmax_total > 0.0:
            detail["mc_mean_usd_mwh"] = float(
                sum(
                    float(_row_pmax[k]) * float(np.mean(mc[i]))
                    for k, i in enumerate(rows)
                )
                / _pmax_total
            )
        margin_detail[g.unit_id] = detail

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

    # --- Decision rule branch (FF-1A). Both rules consumed the identical
    # per-unit margins above; retirement_rule selects how a failing screen
    # becomes a realized exit. "pipeline" is the R-NEW decision/execution
    # split (see _apply_pipeline_retirements); "legacy" (default) is the
    # per-fuel consecutive-loss counter, byte-identical to every committed
    # run.
    if getattr(config, "retirement_rule", "legacy") == "pipeline":
        if year is None:
            raise ValueError(
                "retirement_rule='pipeline' requires a simulation year "
                "(the decision/execution pipeline is dated)"
            )
        return _apply_pipeline_retirements(
            fleet,
            margins,
            loss_years,
            config,
            peak_demand,
            wind_pool_mw,
            solar_pool_mw,
            storage_firm_mw,
            deliverability_headroom,
            year,
            event_sink,
            exit_rate_cap_mw,
            margin_detail=margin_detail,
            exogenous_exits=exogenous_exits,
        )

    # Legacy rule: a failing year increments the unit's consecutive-loss
    # counter (a profitable year resets it); the counter reaching the
    # per-fuel retirement_years_* threshold makes the unit exit-eligible.
    eligible: list[Generator] = []
    for g, net_revenue, going_forward_cost in margins:
        threshold = getattr(
            config,
            _RETIREMENT_YEARS.get(g.fuel_type, ""),
            config.retirement_consecutive_years,
        )
        if net_revenue < going_forward_cost:
            loss_years[g.unit_id] = loss_years.get(g.unit_id, 0) + 1
        else:
            loss_years[g.unit_id] = 0

        if loss_years[g.unit_id] >= threshold:
            eligible.append(g)

    # Within each fuel class, retire the least efficient units first.
    eligible.sort(key=lambda g: (g.fuel_type, -g.heat_rate))
    retired = {g.unit_id for g in eligible}

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
            if g.unit_id not in retired
        ]
    return survivors, loss_years, floor_retention_log
