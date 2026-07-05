"""Capacity expansion and retirement modeling.

Part 1: fleet retirements. Two mechanisms remove generators between
simulation years:

* **Known retirements** -- units with a scheduled ``retirement_year`` are
  dropped once the simulation reaches that year. By default
  (``forecast_fossil_retirement_economic``) **fossil** units (coal/gas/oil)
  are exempt: their announced retirement is treated as an announcement, not a
  certainty, so their phaseout is left to the economic screen below and the
  forecast stays condition-responsive. Non-fossil units (nuclear, hydro,
  renewables, storage) always honor their announced EIA-860 date.
* **Economic retirements** -- thermal units whose energy revenue fails to
  cover their going-forward fixed cost for a fuel-type-specific number of
  consecutive years are retired, least efficient first within each fuel
  class. Coal faces a shorter loss window and a higher effective fixed
  cost than gas, and a system-wide reliability floor prevents thermal
  capacity from being stripped below the reserve margin.

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
    NOX_RATES,
    OFFSHORE_WIND_PARAMS,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    QUEUE_CAP_GW,
    QUEUE_CAP_PER_TECH_GW,
    RENEWABLE_CAPACITY_CREDIT,
    VOM,
    WRIGHT_REFERENCE_GW,
)
from market_sim.config.capacity_area_crosswalk import aggregate_by_zone
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig, resolve_new_entry_costs
from market_sim.data import capacity_deliverability as capdel
from market_sim.model.ancillary import as_revenue_per_mw_yr
from market_sim.data.fleet import FleetArrays, Generator, aggregate_fleet
from market_sim.data.hydrogen import compute_h2_fuel_cost
from market_sim.data.renewables import get_renewable_zone
from market_sim.model.dispatch import DispatchResult
from market_sim.policy.ira import (
    apply_ira_credits_to_lcoe,
    ccus_45q_credit_per_mwh,
    h2_45v_credit_per_mmbtu,
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

# Fuel classes that count toward the clean-energy share.
_CLEAN_FUELS: frozenset[str] = frozenset({"wind", "solar", "nuclear", "hydro"})

# Fuel classes whose firm capacity backs the reliability floor as
# always-present (not retirement-screened) baseload. Nuclear is NOT here: it
# is now an economically-retirement-eligible thermal resource (_THERMAL_FOM),
# so it is counted in the retained-thermal sum the floor protects rather than
# pre-subtracted from peak. Only hydro (never screened) backs the floor.
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


def apply_known_retirements(
    fleet: list[Generator], year: int, fossil_economic: bool = True
) -> list[Generator]:
    """Return the fleet with scheduled (date-based) retirements removed.

    A generator retires once the simulation year reaches its
    ``retirement_year``; units with no scheduled year are always kept.

    When ``fossil_economic`` is ``True`` (the forecast default), units of a
    :data:`_FOSSIL_FUELS` type are **exempt** from this date-based retirement —
    their phaseout is left to the economic-retirement screen
    (:func:`apply_economic_retirements`) so the forecast retires fossil capacity
    on economics rather than on an announced date. Non-fossil units (nuclear,
    hydro, renewables, storage) always honor their announced EIA-860 retirement
    date. Set ``fossil_economic=False`` to honor every scheduled retirement
    regardless of fuel (the legacy behaviour).

    Args:
        fleet: The current generator fleet.
        year: The simulation year being evaluated.
        fossil_economic: When ``True``, fossil units ignore their scheduled
            ``retirement_year`` (economic screen governs them).

    Returns:
        A new list excluding generators whose ``retirement_year`` is set
        and not later than ``year`` (fossil units kept when
        ``fossil_economic``).
    """
    keep: list[Generator] = []
    for g in fleet:
        if g.retirement_year is None or g.retirement_year > year:
            keep.append(g)
        elif fossil_economic and g.fuel_type in _FOSSIL_FUELS:
            keep.append(g)  # economic screen governs fossil phaseout
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


def capacity_revenue_per_mw_yr(iso: str, eford: float) -> float:
    """Return the resource-adequacy capacity payment in $/MW-yr (Module M1).

    In a capacity-market ISO a thermal unit earns a payment on its
    qualifying (UCAP) capacity *outside* the energy market, which can keep
    it solvent even on a negative energy margin. This monetizes the per-ISO
    net-CONE from :data:`MARKET_DESIGN` against the unit's UCAP, approximated
    as ``1 - EFORd`` (PJM/NYISO/ISO-NE accredit roughly on unforced
    capacity)::

        $/MW-yr = net_cone_per_kw_yr * 1000 * (1 - eford)

    Energy-only ISOs (ERCOT, and any ISO absent from the registry) have
    ``capacity_market = False`` and earn zero here, so their retirement and
    new-entry economics are unchanged. The capacity price is exogenous and
    citable (the net-CONE anchor), mirroring how EAC revenue already enters;
    BRA/auction clearing prices can refine it later.
    """
    design = MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN)
    if not design.capacity_market or design.net_cone_per_kw_yr <= 0.0:
        return 0.0
    ucap = max(0.0, 1.0 - float(eford))
    return design.net_cone_per_kw_yr * 1000.0 * ucap


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
    event_sink: dict | None = None,
) -> tuple[list[Generator], dict[str, int]]:
    """Retire thermal units that persistently fail to cover fixed cost.

    For each thermal generator the annual inframarginal energy margin is
    compared with its going-forward fixed cost::

        net_revenue        = sum_t (price[zone, t] - mc[g, t]) * dispatch[g, t]
        going_forward_cost = fixed_om_per_kw_yr * fom_multiplier
                             * pmax_mw * 1000

    ``mc`` is the unit's *full* variable cost (fuel + VOM + emission
    prices), not its bid: take-or-pay coal tranches bid below fuel cost in
    dispatch because the fuel is sunk within the contract year, but on a
    retirement horizon the contract lapses, so fuel is avoidable and counts
    against the margin. When ``mc`` is ``None`` the screen degrades to
    comparing gross energy revenue against fixed cost, which overstates
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
    floor then caps total retirements: if retiring every eligible unit
    would leave thermal capacity below ``(peak_demand - firm_clean) *
    (1 + retirement_reserve_margin)``, the most efficient eligible units
    are kept online until the floor is satisfied.

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
        event_sink: Optional dict populated in place with the retirement
            attribution the evolution ledger needs (CX-3): ``"retired"`` (the
            units actually retired) and ``"floor_retained"`` (units the
            economic screen wanted out but the reliability floor kept online).
            Each entry is ``{"unit_id","fuel","mw"}``. ``None`` records
            nothing. Does not affect the retirement decision.

    Returns:
        Tuple ``(survivors, loss_years)`` -- the fleet with retired units
        removed, and the updated loss-counter dict (retired units dropped).
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
    idx_of = {uid: i for i, uid in enumerate(fleet_arrays.unit_ids)}
    loss_years = dict(consecutive_loss_years)

    eligible: list[Generator] = []
    for g in fleet:
        fom_field = _THERMAL_FOM.get(g.fuel_type)
        if fom_field is None:
            continue
        rows = _dispatch_rows(g, idx_of)
        if not rows:
            continue

        zone = int(fleet_arrays.zone_idx[rows[0]])
        # Inframarginal energy margin: (price - variable cost) x dispatch.
        # Gross revenue alone would let a unit "cover" fixed cost with
        # money it spent on fuel.
        if mc is None:
            net_revenue = float(sum(np.dot(prices[zone], dispatch[i]) for i in rows))
        else:
            net_revenue = float(
                sum(np.dot(prices[zone] - mc[i], dispatch[i]) for i in rows)
            )

        # The attribute payment -- the higher of the exogenous EAC and the
        # endogenous RPS shadow price, never their sum -- adds revenue
        # beyond the energy market, keeping units that energy prices alone
        # would not. The RPS shadow price is credited only to RPS-eligible
        # clean fuels.
        annual_gen_mwh = float(sum(np.sum(dispatch[i]) for i in rows))
        eac_price = get_eac_price_for_new_entry(g.fuel_type, config)
        rps_for_unit = rps_shadow_price if g.fuel_type in _CLEAN_FUELS else 0.0
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
            net_revenue += g.pmax_mw * capacity_revenue_per_mw_yr(config.iso, g.eford)

        # ERCOT ancillary-service revenue (Reg/RRS/ECRS/Non-Spin): a real
        # income stream the energy-only LP cannot produce. Zero unless
        # config.as_revenue_enabled (ERCOT only); saturates on the storage
        # fleet. Omitting it makes tail thermal under-earn and over-retire.
        # Exactly one mechanism prices it (rule 19): under
        # ercot_thermal_as_endogenous the co-opt duals supply a per-fuel derived
        # rate (thermal_as_revenue_per_mw_yr) and the exogenous flat rate is
        # suppressed; otherwise the exogenous rate is the sole credit.
        if thermal_as_revenue_per_mw_yr is not None:
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

        if net_revenue < going_forward_cost:
            loss_years[g.unit_id] = loss_years.get(g.unit_id, 0) + 1
        else:
            loss_years[g.unit_id] = 0

        if loss_years[g.unit_id] >= threshold:
            eligible.append(g)

    # Within each fuel class, retire the least efficient units first.
    eligible.sort(key=lambda g: (g.fuel_type, -g.heat_rate))
    retired = {g.unit_id for g in eligible}

    # Reliability floor: never strip thermal capacity below the reserve
    # margin over peak net demand, net of firm clean (nuclear/hydro).
    firm_clean = sum(g.pmax_mw for g in fleet if g.fuel_type in _FIRM_CLEAN_FUELS)
    floor = (peak_demand - firm_clean) * (1.0 + config.retirement_reserve_margin)
    thermal_after = sum(
        g.pmax_mw
        for g in fleet
        if g.fuel_type in _THERMAL_FOM and g.unit_id not in retired
    )
    if thermal_after < floor:
        # Keep the most efficient eligible units (lowest heat rate) online
        # until thermal capacity clears the floor.
        for g in sorted(eligible, key=lambda g: g.heat_rate):
            if thermal_after >= floor:
                break
            retired.discard(g.unit_id)
            thermal_after += g.pmax_mw

    survivors = [g for g in fleet if g.unit_id not in retired]
    for uid in retired:
        loss_years.pop(uid, None)

    # Ledger attribution: the units actually retired, and the units the
    # economic screen flagged (``eligible``) but the reliability floor kept
    # online (CX-3). ``eligible`` minus ``retired`` is exactly the floor set.
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

    return survivors, loss_years


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

    Returns:
        Tuple ``(fleet, renewable_additions)`` -- the fleet with entering
        thermal generators appended, and a ``{zone: {fuel: mw}}`` dict of
        wind/solar build MW to fold into the zonal renewable capacity.
    """
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
            if effective_attribute_price > 0.0:
                revenue += effective_attribute_price * cf * HOURS_PER_YEAR
            margin = revenue - lcoe * HOURS_PER_YEAR * cf
            if margin > 0.0:
                margins.append((margin, tech))
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
            energy_margin = float(np.maximum(price_hourly - var_cost, 0.0).sum())
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
                else capacity_revenue_per_mw_yr(iso_config.name, EFORD[tech])
            )
            # AS credit: derived per-fuel co-opt rate under
            # ercot_thermal_as_endogenous (rule 19), else the exogenous flat rate.
            # Exactly one prices thermal AS.
            if thermal_as_revenue_per_mw_yr is not None:
                as_credit = thermal_as_revenue_per_mw_yr.get(tech, 0.0)
            else:
                as_credit = as_revenue_per_mw_yr(tech, storage_power_mw, config)
            effective_revenue = energy_margin + capacity_payment + as_credit
            margin = effective_revenue - fixed_cost
            if margin > 0.0:
                margins.append((margin, tech))
            continue

        # Non-dispatchable / must-run candidates (wind, solar, nuclear_smr):
        # value the CF-shaped output at the expected price and net the
        # levelized cost; clean attributes (EAC or RPS shadow price, the
        # higher, never stacked) lift RPS-eligible renewables.
        lcoe = compute_lcoe(tech, year, config, cumulative_gw=cum_gw)
        effective_revenue = estimate_expected_revenue(prices, base_cf)
        rps_for_tech = rps_shadow_price if tech in _RENEWABLE_NEW_FUELS else 0.0
        effective_attribute_price = max(
            get_eac_price_for_new_entry(tech, config), rps_for_tech
        )
        if effective_attribute_price > 0.0:
            effective_revenue += effective_attribute_price * base_cf * HOURS_PER_YEAR
        annual_cost = lcoe * HOURS_PER_YEAR * base_cf
        margin = effective_revenue - annual_cost
        if margin > 0.0:
            margins.append((margin, tech))

    margins.sort(reverse=True)

    new_fleet = list(fleet)
    renewable_additions: dict[str, dict[str, float]] = {}
    remaining = queue_budget_mw
    # Per-tech queue caps are tracked per cap group: hydrogen turbines and
    # CCUS share the ``gas_cc`` group, so their builds compete for one cap.
    group_remaining: dict[str, float] = {}
    for seq, (_, tech) in enumerate(margins):
        if remaining <= 0.0:
            break
        # Each tech is capped by its (possibly shared) per-tech queue limit
        # and by what is left of the shared ISO budget; both bind.
        group = _QUEUE_CAP_GROUP.get(tech, tech)
        if group not in group_remaining:
            group_remaining[group] = per_tech_cap_gw.get(group, 0.0) * 1000.0
        build_mw = min(group_remaining[group], remaining)
        if build_mw <= 0.0:
            continue
        remaining -= build_mw
        group_remaining[group] -= build_mw
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

    return new_fleet, renewable_additions


def accredited_firm_capacity_mw(
    fleet: list[Generator],
    wind_pool_mw: float = 0.0,
    solar_pool_mw: float = 0.0,
    storage_firm_mw: float = 0.0,
) -> float:
    """Return the system's accredited firm (ELCC/UCAP) capacity in MW.

    Each resource contributes the firm fraction of its nameplate it can be
    relied on for at the system peak: thermal at ``1 - EFORd`` (UCAP),
    variable renewables at their capacity credit
    (:data:`RENEWABLE_CAPACITY_CREDIT`), storage at its
    duration-dependent ELCC (passed in pre-accredited as ``storage_firm_mw``,
    since the ELCC helper lives in the storage module). Wind/solar held in
    the zonal pools (not Generators) are passed as ``wind_pool_mw`` /
    ``solar_pool_mw``.
    """
    firm = float(storage_firm_mw)
    firm += wind_pool_mw * RENEWABLE_CAPACITY_CREDIT["wind"]
    firm += solar_pool_mw * RENEWABLE_CAPACITY_CREDIT["solar"]
    for g in fleet:
        credit = RENEWABLE_CAPACITY_CREDIT.get(g.fuel_type)
        if credit is not None:
            firm += g.pmax_mw * credit
        else:
            firm += g.pmax_mw * (1.0 - float(g.eford))
    return firm


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
    new-entry screen, if accredited firm capacity is below
    ``peak_demand * (1 + planning_reserve_margin)`` the residual gap is
    filled with the cheapest firm dispatchable resource (a ``gas_ct``
    peaker), so adequacy holds even when under-priced energy/scarcity
    revenue would otherwise under-build. The economic screen still owns the
    profitable build; this only covers the shortfall.

    Sized on nameplate (the gap is a firm-MW gap, so nameplate =
    gap / (1 - EFORd_gas_ct)). The build is capped at the ISO's annual
    interconnection-queue throughput so a single year cannot add unbounded
    capacity. Returns ``(fleet, built_mw)``; a no-op (built 0) when disabled,
    when the margin is already met, or when the queue cap is exhausted.
    """
    if not config.reserve_margin_build_enabled or peak_demand_mw <= 0.0:
        return fleet, 0.0
    # Per-ISO target leads; an explicit ScenarioConfig.planning_reserve_margin
    # still overrides it for ISOs absent from the registry (fallback scalar).
    reserve_margin = PLANNING_RESERVE_MARGIN_BY_ISO.get(
        iso, config.planning_reserve_margin
    )
    required = peak_demand_mw * (1.0 + reserve_margin)
    firm_gap = required - firm_capacity_mw
    if firm_gap <= 0.0:
        return fleet, 0.0

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
) -> tuple[list[Generator], dict[str, int], dict[str, dict[str, float]], list[dict]]:
    """Advance the fleet by one simulation year.

    The five capacity mechanisms are applied in a fixed order:

    1. known retirements,
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

    Returns:
        Tuple ``(fleet, loss_tracker, renewable_additions, retrofit_log)``
        after all mechanisms are applied. ``renewable_additions`` is a
        ``{zone: {"wind": mw, "solar": mw}}`` dict of new wind/solar capacity
        built this year; the caller folds it into the zonal ``wind_cap`` /
        ``solar_cap`` pools that bound the ``W[z,t]`` / ``S[z,t]`` dispatch
        variables. ``retrofit_log`` is the list of CCS retrofit decision
        dicts recorded this year.
    """
    loss_tracker = dict(loss_tracker)
    renewable_additions: dict[str, dict[str, float]] = {}

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
    peak_demand = float(_prior_attr(prior_results, "peak_demand", 0.0) or 0.0)
    planned = _prior_attr(prior_results, "planned_additions", []) or []
    mc_cost = _prior_attr(prior_results, "mc_cost")
    # AS-eligible (storage) fleet power, the AS-revenue saturation driver.
    storage_power_mw = float(_prior_attr(prior_results, "storage_power_mw", 0.0) or 0.0)
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

    # 1. Known retirements. Fossil units are exempt by default (their phaseout is
    #    economic, step 2); non-fossil units retire on their announced EIA-860
    #    date. config.forecast_fossil_retirement_economic toggles this.
    _pre_known = {g.unit_id: g for g in fleet} if _rec else None
    fleet = apply_known_retirements(
        fleet,
        year,
        fossil_economic=getattr(config, "forecast_fossil_retirement_economic", True),
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
        fleet, loss_tracker = apply_economic_retirements(
            fleet,
            fleet_arrays,
            dispatch_result,
            prices,
            config,
            loss_tracker,
            peak_demand,
            rps_shadow_price=rps_shadow_price,
            mc=mc_cost,
            storage_power_mw=storage_power_mw,
            deliverability_headroom=deliverability_headroom,
            thermal_as_revenue_per_mw_yr=thermal_as_revenue_per_mw_yr,
            event_sink=_econ_sink,
        )
        if _rec:
            events["retirements"].extend(
                {**e, "reason": "economic"} for e in _econ_sink.get("retired", [])
            )
            events["floor_retained"].extend(_econ_sink.get("floor_retained", []))

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
        )
        _merge_renewable_additions(renewable_additions, entry_additions)
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
    # against the (prior-year, build-ahead-of-need) peak. Firm capacity nets
    # the thermal fleet (UCAP) and the prior-year renewable pools / storage
    # (threaded via prior_results). No-op unless reserve_margin_build_enabled.
    if config.reserve_margin_build_enabled and peak_demand > 0.0:
        wind_pool_mw = float(_prior_attr(prior_results, "wind_cap_mw", 0.0) or 0.0)
        solar_pool_mw = float(_prior_attr(prior_results, "solar_cap_mw", 0.0) or 0.0)
        storage_firm_mw = float(
            _prior_attr(prior_results, "storage_firm_mw", 0.0) or 0.0
        )
        firm_mw = accredited_firm_capacity_mw(
            fleet, wind_pool_mw, solar_pool_mw, storage_firm_mw
        )
        _pre_backstop_ids = {g.unit_id for g in fleet} if _rec else None
        fleet, adequacy_mw = apply_reserve_margin_build(
            fleet, firm_mw, peak_demand, year, config, config.iso
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
            resolved_margin = PLANNING_RESERVE_MARGIN_BY_ISO.get(
                config.iso, config.planning_reserve_margin
            )
            logger.info(
                "year %d: reserve-margin backstop built %.0f MW gas_ct "
                "(firm %.0f MW vs peak %.0f MW x %.3f margin)",
                year,
                adequacy_mw,
                firm_mw,
                peak_demand,
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

    return fleet, loss_tracker, renewable_additions, retrofit_log
