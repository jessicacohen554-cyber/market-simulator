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

:func:`evolve_fleet` chains all four mechanisms into one year-step.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from market_sim.config.constants import (
    CO2_RATES,
    EFORD,
    GLOBAL_ANNUAL_DEPLOYMENT_GW,
    HEAT_RATE_BINS,
    HOURS_PER_YEAR,
    NEW_ENTRY_COSTS,
    QUEUE_CAP_GW,
    QUEUE_CAP_PER_TECH_GW,
    VOM,
    WRIGHT_REFERENCE_GW,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays, Generator
from market_sim.data.renewables import get_renewable_zone
from market_sim.model.dispatch import DispatchResult

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
_NEW_ENTRY_TECHS: tuple[str, ...] = ("wind", "solar", "gas_cc", "nuclear")

# Fuels whose new builds increment the zonal wind_cap/solar_cap pools (and
# the W[z,t]/S[z,t] dispatch variables) rather than entering as thermal
# Generator objects. Variable-output renewables must follow a CF profile.
_RENEWABLE_NEW_FUELS: frozenset[str] = frozenset({"wind", "solar"})


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
    supplied. Fixed O&M is added and the total is spread over expected
    annual generation.

    IRA credits enter at the right layer: the solar investment tax credit
    discounts ``capex_per_kw`` before annualization, so it never touches
    fixed O&M; the wind production tax credit is subtracted from the final
    $/MWh, as a per-MWh credit should be.

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

    # IRA ITC: reduce capex before annualization, so the credit applies only
    # to the capital component and never discounts fixed O&M.
    if year <= config.ira_expiry_year and tech_type == "solar":
        capex_per_kw *= 1.0 - config.ira_itc_solar

    crf = _capital_recovery_factor(config.discount_rate, costs["lifetime_yr"])
    annual_cost_per_kw = capex_per_kw * crf + costs["fom_per_kw_yr"]
    # Annual generation per kW of capacity, expressed in MWh.
    annual_mwh_per_kw = HOURS_PER_YEAR * costs["base_cf"] / 1000.0
    lcoe = annual_cost_per_kw / annual_mwh_per_kw

    # Wind PTC: a per-MWh production credit, correctly subtracted post-hoc.
    if tech_type == "wind" and year <= config.ira_expiry_year:
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

    # Nuclear carries no fuel cost (fuel is embedded in FOM) and runs as a
    # must-run baseload unit; it has no heat-rate bin to assign above.
    if tech_type == "nuclear":
        kwargs["is_must_run"] = True
        kwargs["vom"] = VOM.get("nuclear", 2.5)
        kwargs["eford"] = EFORD.get("nuclear", 0.03)

    return Generator(**kwargs)


def apply_economic_new_entry(
    fleet: list[Generator],
    prices: np.ndarray,
    year: int,
    config: ScenarioConfig,
    iso: str,
    rec_price: float = 0.0,
    cumulative: CumulativeDeployment | None = None,
    gas_price_per_mmbtu: float = 0.0,
    carbon_price: float = 0.0,
) -> tuple[list[Generator], dict[str, dict[str, float]]]:
    """Build new capacity for technologies that clear their LCOE.

    For each candidate technology the expected annual revenue per MW is
    compared with its annualized levelized cost. Clean technologies (wind
    and solar) additionally earn ``rec_price`` per MWh generated -- the
    prior year's RPS shadow price -- so a binding RPS lifts their expected
    revenue and pulls more of them across the LCOE hurdle. Profitable
    technologies are ranked by margin and built in priority order, highest
    margin first. Two caps bind independently:

    * each technology builds at most its per-tech cap from
      :data:`QUEUE_CAP_PER_TECH_GW`, and
    * the total across all technologies builds at most the ISO-level
      cap :data:`QUEUE_CAP_GW`.

    The highest-margin technology draws on the shared ISO budget first;
    once that budget is exhausted no further technologies are built.

    Thermal new entry (``gas_cc`` and ``nuclear``) is appended to the
    returned fleet as a :class:`Generator`. Wind and solar are *not*:
    variable-output renewables must follow a capacity-factor profile, so
    their build MW is routed to the zonal ``wind_cap`` / ``solar_cap``
    pools (the bounds of the ``W[z,t]`` and ``S[z,t]`` dispatch variables)
    rather than entering as flat-availability thermal units.

    Args:
        fleet: The current generator fleet.
        prices: Hourly zonal energy prices in $/MWh from the prior solve.
        year: Simulation year.
        config: Scenario config.
        iso: ISO identifier, supplying the queue caps and build zone.
        rec_price: Prior year's RPS shadow price in $/MWh, added to the
            expected revenue of wind and solar candidates.
        cumulative: Global cumulative deployment, used to discount each
            candidate's capex along its Wright's-Law learning curve.
        gas_price_per_mmbtu: Delivered gas price, used to charge gas CC
            new entry its expected variable fuel cost.
        carbon_price: Carbon price in $/tCO2, used to charge thermal new
            entry its expected carbon cost.

    Returns:
        Tuple ``(fleet, renewable_additions)`` -- the fleet with entering
        thermal generators appended, and a ``{zone: {fuel: mw}}`` dict of
        wind/solar build MW to fold into the zonal renewable capacity.
    """
    iso_config = get_iso_config(iso)
    queue_budget_mw = QUEUE_CAP_GW[iso_config.name] * 1000.0
    per_tech_cap_gw = QUEUE_CAP_PER_TECH_GW.get(iso_config.name, {})
    zone = max(iso_config.zones, key=lambda z: z.load_share).name

    margins: list[tuple[float, str]] = []
    for tech in _NEW_ENTRY_TECHS:
        base_cf = NEW_ENTRY_COSTS[tech]["base_cf"]
        cum_gw = cumulative.get(tech) if cumulative else None
        lcoe = compute_lcoe(tech, year, config, cumulative_gw=cum_gw)
        effective_revenue = estimate_expected_revenue(prices, base_cf)
        # A binding RPS pays clean technologies a REC premium on every MWh
        # generated, raising their expected revenue.
        if tech in _RENEWABLE_NEW_FUELS:
            effective_revenue += rec_price * base_cf * HOURS_PER_YEAR
        annual_cost = lcoe * HOURS_PER_YEAR * base_cf

        # Thermal candidates also burn fuel: a gas CC earns margin only
        # when the clearing price clears its marginal cost, so charge it
        # the expected variable cost (fuel, VOM, carbon) of a best-in-class
        # new unit. Without this, gas CC builds regardless of fuel price.
        if tech in _THERMAL_FOM:
            heat_rate_bins = HEAT_RATE_BINS.get(tech, {})
            best_hr = min(heat_rate_bins.values()) if heat_rate_bins else 0.0
            co2_bins = CO2_RATES.get(tech, {})
            best_co2 = min(co2_bins.values()) if co2_bins else 0.0
            var_cost = (
                best_hr * gas_price_per_mmbtu
                + VOM.get(tech, 0.0)
                + best_co2 * carbon_price
            )
            annual_cost += var_cost * base_cf * HOURS_PER_YEAR

        margin = effective_revenue - annual_cost
        if margin > 0.0:
            margins.append((margin, tech))

    margins.sort(reverse=True)

    new_fleet = list(fleet)
    renewable_additions: dict[str, dict[str, float]] = {}
    remaining = queue_budget_mw
    for seq, (_, tech) in enumerate(margins):
        if remaining <= 0.0:
            break
        # Each tech is capped by its own queue limit and by what is left
        # of the shared ISO budget; both caps bind independently.
        tech_cap_mw = per_tech_cap_gw.get(tech, 0.0) * 1000.0
        build_mw = min(tech_cap_mw, remaining)
        if build_mw <= 0.0:
            continue
        remaining -= build_mw
        if tech in _RENEWABLE_NEW_FUELS:
            target_zone = get_renewable_zone(iso_config.name, tech)
            zone_acc = renewable_additions.setdefault(target_zone, {})
            zone_acc[tech] = zone_acc.get(tech, 0.0) + build_mw
        else:
            new_fleet.append(_make_new_generator(tech, build_mw, zone, year, seq))

    return new_fleet, renewable_additions


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
    rec_price: float = 0.0,
    cumulative: CumulativeDeployment | None = None,
    gas_price_per_mmbtu: float = 0.0,
    carbon_price: float = 0.0,
) -> tuple[list[Generator], dict[str, int], dict[str, dict[str, float]]]:
    """Advance the fleet by one simulation year.

    The four capacity mechanisms are applied in a fixed order:

    1. known retirements,
    2. economic retirements,
    3. known additions (planned units with ``online_year == year``),
    4. economic new entry (generation).

    The renewable portfolio standard is not applied here -- it is enforced
    as an LP constraint in dispatch, and its shadow price (``rec_price``)
    feeds the economic new-entry screen so clean builds are economics-
    driven. Storage new entry is handled separately in the runner.

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
        rec_price: Prior year's RPS shadow price in $/MWh, passed to the
            economic new-entry screen as additional clean-energy revenue.
        cumulative: Global cumulative deployment, passed to the new-entry
            screen so candidate capex follows a Wright's-Law learning curve.
        gas_price_per_mmbtu: Delivered gas price for the year, passed to
            the new-entry screen to cost gas CC variable fuel.
        carbon_price: Carbon price in $/tCO2 for the year, passed to the
            new-entry screen to cost thermal carbon emissions.

    Returns:
        Tuple ``(fleet, loss_tracker, renewable_additions)`` after all
        mechanisms are applied. ``renewable_additions`` is a ``{zone:
        {"wind": mw, "solar": mw}}`` dict of new wind/solar capacity built
        this year; the caller folds it into the zonal ``wind_cap`` /
        ``solar_cap`` pools that bound the ``W[z,t]`` / ``S[z,t]`` dispatch
        variables.
    """
    loss_tracker = dict(loss_tracker)
    renewable_additions: dict[str, dict[str, float]] = {}

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

    # 4. Economic new entry (needs a price signal). Clean technologies see
    # the prior year's REC price as additional expected revenue.
    if prices is not None:
        fleet, entry_additions = apply_economic_new_entry(
            fleet, prices, year, config, config.iso,
            rec_price=rec_price,
            cumulative=cumulative,
            gas_price_per_mmbtu=gas_price_per_mmbtu,
            carbon_price=carbon_price,
        )
        _merge_renewable_additions(renewable_additions, entry_additions)

    return fleet, loss_tracker, renewable_additions
