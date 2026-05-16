"""Capacity expansion and retirement modeling.

Part 1: fleet retirements. Two mechanisms remove generators between
simulation years:

* **Known retirements** -- units with a scheduled ``retirement_year`` are
  dropped once the simulation reaches that year.
* **Economic retirements** -- thermal units whose energy revenue fails to
  cover their going-forward fixed cost for a fuel-type-specific number of
  consecutive years are retired, least efficient first within each fuel
  class. Coal faces a shorter loss window and a higher effective fixed
  cost than gas, and a system-wide reliability floor prevents thermal
  capacity from being stripped below the reserve margin.

Part 2: capacity additions. New generators enter the fleet via three
mechanisms, costed with Wright's-Law learning curves and IRA credits:

* **Known additions** -- units with a planned ``online_year`` are
  activated when the simulation reaches that year.
* **Economic new entry** -- candidate technologies whose expected revenue
  exceeds their levelized cost are built, subject to an annual
  interconnection-queue cap, highest-margin technology first.
* **RPS mandates** -- when the clean-energy share falls below an ISO's
  renewable portfolio standard, the cheapest clean technology is
  force-built to close the gap.

:func:`evolve_fleet` chains all five mechanisms into one year-step.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.constants import (
    CO2_RATES,
    HEAT_RATE_BINS,
    HOURS_PER_YEAR,
    NEW_ENTRY_COSTS,
    QUEUE_CAP_GW,
    VOM,
    WRIGHT_REFERENCE_GW,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays, Generator
from market_sim.model.dispatch import DispatchResult
from market_sim.policy.ira import apply_ira_credits_to_lcoe
from market_sim.policy.rps import get_rps_target

# Fuel classes treated as dispatchable thermal capacity for economic
# retirement, mapped to their ScenarioConfig fixed-O&M field ($/kW-yr).
_THERMAL_FOM: dict[str, str] = {
    "gas_cc": "fixed_om_gas_cc",
    "gas_ct": "fixed_om_gas_ct",
    "coal": "fixed_om_coal",
}

# Fuel classes that count toward the clean-energy share.
_CLEAN_FUELS: frozenset[str] = frozenset({"wind", "solar", "nuclear", "hydro"})

# Fuel classes whose firm capacity backs the reliability floor.
_FIRM_CLEAN_FUELS: tuple[str, ...] = ("nuclear", "hydro")

# Per-fuel ScenarioConfig field names for the consecutive-loss threshold.
_RETIREMENT_YEARS: dict[str, str] = {
    "coal": "retirement_years_coal",
    "gas_ct": "retirement_years_gas_ct",
    "gas_cc": "retirement_years_gas_cc",
}

# Per-fuel ScenarioConfig field names for the effective-FOM multiplier.
_FOM_MULTIPLIER: dict[str, str] = {
    "coal": "retirement_fom_multiplier_coal",
    "gas_ct": "retirement_fom_multiplier_gas_ct",
    "gas_cc": "retirement_fom_multiplier_gas_cc",
}


def apply_known_retirements(fleet: list[Generator], year: int) -> list[Generator]:
    """Return the fleet with scheduled retirements removed.

    A generator retires once the simulation year reaches its
    ``retirement_year``; units with no scheduled year are always kept.

    Args:
        fleet: The current generator fleet.
        year: The simulation year being evaluated.

    Returns:
        A new list excluding generators whose ``retirement_year`` is set
        and not later than ``year``.
    """
    return [
        g for g in fleet
        if g.retirement_year is None or g.retirement_year > year
    ]


def compute_clean_share(fleet: list[Generator]) -> float:
    """Return the clean-capacity fraction of the fleet.

    Clean capacity is the summed ``pmax_mw`` of wind, solar, nuclear and
    hydro units, divided by the total fleet ``pmax_mw``. An empty fleet
    (zero total capacity) yields ``0.0``.

    This is a reporting/RPS utility -- it informs :func:`apply_rps_mandate`
    and downstream metrics, and does not drive any retirement decision.
    """
    total = sum(g.pmax_mw for g in fleet)
    if total <= 0.0:
        return 0.0
    clean = sum(g.pmax_mw for g in fleet if g.fuel_type in _CLEAN_FUELS)
    return clean / total


def apply_economic_retirements(
    fleet: list[Generator],
    fleet_arrays: FleetArrays,
    dispatch_result: DispatchResult,
    prices: np.ndarray,
    config: ScenarioConfig,
    consecutive_loss_years: dict[str, int],
    peak_demand: float,
) -> tuple[list[Generator], dict[str, int]]:
    """Retire thermal units that persistently fail to cover fixed cost.

    For each thermal generator the annual energy revenue is compared with
    its going-forward fixed cost::

        net_revenue        = sum_t price[zone, t] * dispatch[g, t]
        going_forward_cost = fixed_om_per_kw_yr * fom_multiplier
                             * pmax_mw * 1000

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

    Returns:
        Tuple ``(survivors, loss_years)`` -- the fleet with retired units
        removed, and the updated loss-counter dict (retired units dropped).
    """
    prices = np.asarray(prices, dtype=float)
    dispatch = np.asarray(dispatch_result.dispatch, dtype=float)
    idx_of = {uid: i for i, uid in enumerate(fleet_arrays.unit_ids)}
    loss_years = dict(consecutive_loss_years)

    eligible: list[Generator] = []
    for g in fleet:
        fom_field = _THERMAL_FOM.get(g.fuel_type)
        if fom_field is None:
            continue
        i = idx_of.get(g.unit_id)
        if i is None:
            continue

        zone = int(fleet_arrays.zone_idx[i])
        net_revenue = float(np.dot(prices[zone], dispatch[i]))

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
    firm_clean = sum(
        g.pmax_mw for g in fleet if g.fuel_type in _FIRM_CLEAN_FUELS
    )
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
    return survivors, loss_years


# --- Part 2: capacity additions -------------------------------------------

# Candidate technologies considered for economic new entry.
_NEW_ENTRY_TECHS: tuple[str, ...] = ("wind", "solar", "gas_cc")


def wright_cost(
    base_cost: float,
    cumulative_gw: float,
    reference_gw: float,
    learning_rate: float,
) -> float:
    """Return a Wright's-Law learning-adjusted unit cost.

    Cost falls as cumulative deployment grows relative to a reference::

        cost = base_cost * (cumulative_gw / reference_gw) ** (-learning_rate)

    At the reference level the cost is unchanged; doubling cumulative
    capacity multiplies cost by ``2 ** (-learning_rate)``.

    Args:
        base_cost: Cost at the reference deployment level.
        cumulative_gw: Cumulative installed capacity, GW.
        reference_gw: Reference cumulative capacity, GW.
        learning_rate: Learning-curve exponent (``0`` disables learning).

    Returns:
        The learning-adjusted cost. Returns ``base_cost`` unchanged when
        either capacity figure is non-positive.
    """
    if cumulative_gw <= 0.0 or reference_gw <= 0.0:
        return base_cost
    return base_cost * (cumulative_gw / reference_gw) ** (-learning_rate)


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
    ``config.discount_rate`` and the technology lifetime, optionally
    discounted by a Wright's-Law learning curve when ``cumulative_gw`` is
    supplied. Fixed O&M is added, the total is spread over expected annual
    generation, and IRA investment credits are applied.

    Args:
        tech_type: Technology key into :data:`NEW_ENTRY_COSTS`.
        year: Simulation year, used for IRA credit expiry.
        config: Scenario config supplying the discount rate.
        cumulative_gw: Cumulative global deployment, GW. When ``None`` no
            learning adjustment is applied.

    Returns:
        The IRA-adjusted LCOE in $/MWh.
    """
    costs = NEW_ENTRY_COSTS[tech_type]
    capex_per_kw = costs["capex_per_kw"]

    reference_gw = WRIGHT_REFERENCE_GW.get(tech_type)
    if cumulative_gw is not None and reference_gw is not None:
        capex_per_kw = wright_cost(
            capex_per_kw, cumulative_gw, reference_gw, costs["learning_rate"]
        )

    crf = _capital_recovery_factor(config.discount_rate, costs["lifetime_yr"])
    annual_cost_per_kw = capex_per_kw * crf + costs["fom_per_kw_yr"]
    # Annual generation per kW of capacity, expressed in MWh.
    annual_mwh_per_kw = HOURS_PER_YEAR * costs["base_cf"] / 1000.0
    lcoe = annual_cost_per_kw / annual_mwh_per_kw

    return apply_ira_credits_to_lcoe(tech_type, lcoe, year, config)


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
    tech_type: str, pmax_mw: float, zone: str, year: int, seq: int
) -> Generator:
    """Build a new ``Generator`` for an entering block of capacity.

    Thermal technologies are assigned the most efficient heat-rate bin --
    a freshly built unit is best-in-class -- along with the matching CO2
    rate and variable O&M.
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
        kwargs["vom"] = VOM.get(tech_type, 0.0)

    return Generator(**kwargs)


def _primary_zone(iso: str) -> str:
    """Return the highest-load-share zone name of an ISO."""
    iso_config = get_iso_config(iso)
    return max(iso_config.zones, key=lambda z: z.load_share).name


def apply_economic_new_entry(
    fleet: list[Generator],
    prices: np.ndarray,
    year: int,
    config: ScenarioConfig,
    iso: str,
) -> list[Generator]:
    """Build new capacity for technologies that clear their LCOE.

    For each candidate technology the expected annual revenue per MW is
    compared with its annualized levelized cost. Profitable technologies
    are ranked by margin and built in priority order, drawing on a shared
    annual interconnection-queue budget (:data:`QUEUE_CAP_GW`); the
    highest-margin technology consumes the queue first.

    Args:
        fleet: The current generator fleet.
        prices: Hourly zonal energy prices in $/MWh from the prior solve.
        year: Simulation year.
        config: Scenario config.
        iso: ISO identifier, supplying the queue cap and build zone.

    Returns:
        A new list with the entering generators appended.
    """
    iso_config = get_iso_config(iso)
    queue_budget_mw = QUEUE_CAP_GW[iso_config.name] * 1000.0
    zone = max(iso_config.zones, key=lambda z: z.load_share).name

    margins: list[tuple[float, str]] = []
    for tech in _NEW_ENTRY_TECHS:
        base_cf = NEW_ENTRY_COSTS[tech]["base_cf"]
        lcoe = compute_lcoe(tech, year, config)
        revenue = estimate_expected_revenue(prices, base_cf)
        annual_cost = lcoe * HOURS_PER_YEAR * base_cf
        margin = revenue - annual_cost
        if margin > 0.0:
            margins.append((margin, tech))

    margins.sort(reverse=True)

    new_fleet = list(fleet)
    remaining = queue_budget_mw
    for seq, (_, tech) in enumerate(margins):
        if remaining <= 0.0:
            break
        build_mw = remaining  # priority order: top margin takes the queue
        remaining -= build_mw
        new_fleet.append(_make_new_generator(tech, build_mw, zone, year, seq))

    return new_fleet


def apply_rps_mandate(
    fleet: list[Generator], year: int, config: ScenarioConfig
) -> list[Generator]:
    """Force-build clean capacity to meet an ISO renewable portfolio standard.

    When the fleet's clean share falls below the ISO's RPS target for the
    year, the cheapest clean technology (by LCOE) is built in the quantity
    needed to lift the clean share to the target. ISOs with no RPS, or a
    fleet already meeting the target, are left unchanged.

    Args:
        fleet: The current generator fleet.
        year: Simulation year.
        config: Scenario config supplying the ISO and discount rate.

    Returns:
        A new list with the mandated clean capacity appended, if any.
    """
    target = get_rps_target(config.iso, year)
    if target is None:
        return list(fleet)

    share = compute_clean_share(fleet)
    if share >= target:
        return list(fleet)

    total_cap = sum(g.pmax_mw for g in fleet)
    clean_cap = sum(g.pmax_mw for g in fleet if g.fuel_type in _CLEAN_FUELS)

    # Capacity X to add so (clean_cap + X) / (total_cap + X) >= target.
    # A target of 1.0 is unreachable while fossil capacity remains, so the
    # divisor is clamped to keep the build finite.
    effective_target = min(target, 0.999)
    gap_mw = (effective_target * total_cap - clean_cap) / (1.0 - effective_target)
    if gap_mw <= 0.0:
        return list(fleet)

    clean_techs = [t for t in NEW_ENTRY_COSTS if t in _CLEAN_FUELS]
    cheapest = min(clean_techs, key=lambda t: compute_lcoe(t, year, config))

    new_fleet = list(fleet)
    new_fleet.append(
        _make_new_generator(cheapest, gap_mw, _primary_zone(config.iso), year, 0)
    )
    return new_fleet


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
) -> tuple[list[Generator], dict[str, int]]:
    """Advance the fleet by one simulation year.

    The five capacity mechanisms are applied in a fixed order:

    1. known retirements,
    2. economic retirements,
    3. known additions (planned units with ``online_year == year``),
    4. economic new entry,
    5. RPS mandates.

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

    Returns:
        Tuple ``(fleet, loss_tracker)`` after all mechanisms are applied.
    """
    loss_tracker = dict(loss_tracker)

    fleet_arrays = _prior_attr(prior_results, "fleet_arrays")
    dispatch_result = _prior_attr(prior_results, "dispatch_result")
    prices = _prior_attr(prior_results, "prices")
    peak_demand = float(_prior_attr(prior_results, "peak_demand", 0.0) or 0.0)
    planned = _prior_attr(prior_results, "planned_additions", []) or []

    # 1. Known retirements.
    fleet = apply_known_retirements(fleet, year)

    # 2. Economic retirements (needs the prior-year dispatch).
    if (
        fleet_arrays is not None
        and dispatch_result is not None
        and prices is not None
    ):
        fleet, loss_tracker = apply_economic_retirements(
            fleet, fleet_arrays, dispatch_result, prices, config,
            loss_tracker, peak_demand,
        )

    # 3. Known additions: planned units coming online this year.
    fleet = fleet + [g for g in planned if g.online_year == year]

    # 4. Economic new entry (needs a price signal).
    if prices is not None:
        fleet = apply_economic_new_entry(fleet, prices, year, config, config.iso)

    # 5. RPS mandates.
    fleet = apply_rps_mandate(fleet, year, config)

    return fleet, loss_tracker
