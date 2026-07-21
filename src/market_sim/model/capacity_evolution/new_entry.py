"""Economic new entry: candidate techs, learning curves, LCOE, expected revenue.

Step 5 of the one-pass capacity evolution
(:func:`market_sim.model.capacity_evolution.evolve.evolve_fleet`; spec §5.1),
split out of the former ``model/capacity.py`` god-module (W-D4, 2026-07-21;
refactor-consolidation plan §5 item 4). Candidate technologies whose expected
revenue exceeds their levelized cost are built, subject to an annual
interconnection-queue cap, highest-margin technology first — costed with
Wright's-Law learning curves (:func:`wright_cost`, :func:`compute_lcoe`) and
IRA credits. Clean technologies also see the prior year's REC price (the RPS
constraint's shadow price) added to their expected revenue; the RPS itself is
an LP constraint, never a force-build.

Also home to :class:`CumulativeDeployment` (the cross-year Wright's-Law
deployment tracker) and :func:`_make_new_generator` (the shared new-unit
factory the adequacy backstop and known-additions steps reuse).

``apply_economic_new_entry`` resolves ``estimate_expected_revenue`` through
the package namespace at call time (:func:`_pkg_ns`), so the historical
``mock.patch("market_sim.model.capacity.estimate_expected_revenue")`` target
keeps intercepting it. The full pre-split surface stays importable from
``market_sim.model.capacity`` (the facade; see the package ``__init__``).
"""

from __future__ import annotations

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
    QUEUE_CAP_GW,
    QUEUE_CAP_PER_TECH_GW,
    VOM,
    WRIGHT_REFERENCE_GW,
)
from market_sim.config.entry_config import (
    ENTRY_COD_LAG_DEFAULT_YEARS,
    ENTRY_COD_LAG_YEARS,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.reserve_config import (
    QUICK_START_FUEL_TYPES,
    RESERVE_FUEL_TYPES,
)
from market_sim.config.scenarios import (
    ScenarioConfig,
    resolve_new_entry_costs,
    resolve_real_discount_rate,
)
from market_sim.model.ancillary import as_revenue_per_mw_yr
from market_sim.data.fleet import Generator
from market_sim.data.hydrogen import compute_h2_fuel_cost
from market_sim.data.renewables import get_renewable_zone
from market_sim.policy.federal_ces import effective_eac_price_for_tech
from market_sim.policy.ira import (
    apply_ira_credits_to_lcoe,
    ccus_45q_credit_per_mwh,
    h2_45v_credit_per_mmbtu,
)

from .retirements import (
    _THERMAL_FOM,
    _default_build_zone,
    _zone_is_long,
    capacity_revenue_per_mw_yr,
    resolve_renewable_capacity_credit,
)


def _pkg_ns():
    """Return the shared package namespace (:mod:`market_sim.model.capacity_evolution`).

    The ``capacity`` facade aliases itself to this package, so every
    historical ``mock.patch("market_sim.model.capacity.<name>")`` (and
    probe-style ``capacity.<name> = wrapped``) lands on the package
    namespace. ``apply_economic_new_entry`` resolves
    ``estimate_expected_revenue`` through it at call time so those patches
    keep intercepting the lookups, exactly as the pre-split module-global
    reads behaved.
    """
    from market_sim.model import capacity_evolution

    return capacity_evolution


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
        crf = _capital_recovery_factor(
            resolve_real_discount_rate(config, tech), params["lifetime_yr"]
        )
        fixed = params["capex_kw"] * crf + params["fom_kw_yr"]
        h2_cost = compute_h2_fuel_cost(year, config, iso)
        h2_cost = max(0.0, h2_cost - h2_45v_credit_per_mmbtu(year, config))
        variable = params["heat_rate"] * h2_cost + params["vom"]
        return fixed / annual_mwh_per_kw + variable

    if tech == "gas_cc_ccs":
        ccs = CCUS_PARAMS["gas_cc_ccs_90"]
        rate = resolve_real_discount_rate(config, tech)
        crf = _capital_recovery_factor(rate, ccs["lifetime_yr"])
        fixed = ccs["capex_kw"] * crf + ccs["fom_kw_yr"]
        base_hr = min(HEAT_RATE_BINS["gas_cc"].values())
        base_co2 = min(CO2_RATES["gas_cc"].values())
        captured = base_co2 * config.ccs_capture_rate
        residual = base_co2 * (1.0 - config.ccs_capture_rate)
        # §45Q levelization over the credit window (W2-C, plan §11 Q2): the
        # credit runs min(config.ira_45q_credit_window_years, book life)
        # years from placed-in-service, so its $/MWh value is levelized over
        # the full life at the screen's own discount rate —
        # PV(window annuity)/PV(life annuity) = CRF(life)/CRF(window). None
        # (indefinite extension) and an expired credit both leave the rate
        # unscaled. This REPLACES the former un-windowed treatment, raising
        # the effective new-build CCS LCOE (a deliberate behavior change:
        # crediting 12 statutory years over a 30-year life, not 30).
        q45 = ccus_45q_credit_per_mwh(captured, year, config)
        if q45 > 0.0:
            # Imported here to avoid a module-level cycle: ccs.py imports
            # wright_cost/CumulativeDeployment from this module.
            from .ccs import _ccs_45q_window_years

            window_years = _ccs_45q_window_years(config, float(ccs["lifetime_yr"]))
            q45 *= crf / _capital_recovery_factor(rate, window_years)
        variable = (
            base_hr * ccs["heat_rate_penalty"] * gas_price_per_mmbtu
            + VOM["gas_cc"]
            + ccs["vom_adder"]
            + captured * config.co2_transport_storage_cost
            + residual * carbon_price
            - q45
        )
        return fixed / annual_mwh_per_kw + variable

    if tech == "geothermal":
        egs = GEOTHERMAL_PARAMS["egs"]
        crf = _capital_recovery_factor(
            resolve_real_discount_rate(config, tech), egs["lifetime_yr"]
        )
        fixed = egs["capex_kw"] * crf + egs["fom_kw_yr"]
        lcoe = fixed / annual_mwh_per_kw + egs["vom"]
        return apply_ira_credits_to_lcoe("geothermal", lcoe, year, config)

    if tech == "offshore_wind":
        params = _offshore_wind_params(iso, config)
        crf = _capital_recovery_factor(
            resolve_real_discount_rate(config, tech), params["lifetime_yr"]
        )
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

    crf = _capital_recovery_factor(
        resolve_real_discount_rate(config, tech_type), costs["lifetime_yr"]
    )
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
    wind_pool_mw: float = 0.0,
    solar_pool_mw: float = 0.0,
    peak_demand_mw: float = 0.0,
    entry_rate_caps_mw: dict[str, float] | None = None,
    entry_pipeline: list[dict] | None = None,
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
        wind_pool_mw, solar_pool_mw: ISO-wide zonal-pool nameplate MW, the
            penetration axis of the VRE adequacy-credit resolver for the
            FF-2A VRE capacity payment (``entry_vre_capacity_revenue``).
        peak_demand_mw: System peak for pct-of-peak ELCC curves (same use).
        entry_rate_caps_mw: ``{tech: MW}`` current-year growth-ladder caps
            (``entry_rate_limits`` — ENTRY_GROWTH_LIMIT_MULTIPLE × the tech's
            prior-max annual build, resolved by the runner). When supplied,
            each listed tech's build this year is additionally capped at its
            ladder value; techs absent from the dict carry no ladder cap
            (rule 25 neutral fallback). ``None`` (default) is byte-identical.
        entry_pipeline: Cross-year pending-entry queue (mutated in place;
            ``entry_commissioning_lag``). Rows not yet commissioned are
            netted against the per-tech queue caps (the developer's view of
            the queue), and — when the lag gate is on — this year's cleared
            builds are APPENDED as ``{tech, mw, zone, decision_year,
            cod_year, seq, kind}`` rows instead of materializing;
            ``evolve_fleet`` commissions rows at their ``cod_year``.
            ``None`` (default) keeps in-year commissioning byte-identically.

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

    # FF-2A item 1 (BLK-7 / term c): ELCC-accredited VRE capacity revenue.
    # Gate resolved once; the class nameplate ledger (pools + fleet units) is
    # the SAME penetration axis accredited_firm_capacity_mw feeds the adequacy
    # resolver (rule 19 — one resolver, one axis).
    _vre_capacity_on = bool(getattr(config, "entry_vre_capacity_revenue", False))
    _vre_nameplate: dict[str, float] = {}
    if _vre_capacity_on:
        # Imported here to avoid a module-level cycle: adequacy.py imports
        # _make_new_generator from this module.
        from .adequacy import _renewable_nameplate_by_fuel

        _vre_nameplate = _renewable_nameplate_by_fuel(
            fleet, wind_pool_mw, solar_pool_mw, iso_config.name
        )

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
            revenue = _pkg_ns().estimate_expected_revenue(prices, cf)
            # Emerging clean resources also earn an attribute payment: the
            # highest single buyer among the legacy exogenous EAC, the
            # federal CES premium × tech credit fraction (W2-A plan §5.3 —
            # this is what lets hydrogen_ct/hydrogen_ccgt and gas_cc_ccs
            # candidates earn the premium), and the RPS shadow price.
            rps_for_tech = rps_shadow_price if tech in _RENEWABLE_NEW_FUELS else 0.0
            effective_attribute_price = max(
                effective_eac_price_for_tech(config, tech, year), rps_for_tech
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
                resolve_real_discount_rate(config, tech), costs["lifetime_yr"]
            )
            fixed_cost = (capex_per_kw * crf + costs["fom_per_kw_yr"]) * 1000.0
            # Module M1 capacity payment (0 in ERCOT) + ERCOT AS revenue, the
            # same streams credited in the retirement screen above.
            capacity_payment = (
                0.0
                if build_zone_long
                else capacity_revenue_per_mw_yr(
                    iso_config.name, tech, EFORD[tech], config, reserve_position, year
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
            effective_revenue = _pkg_ns().estimate_expected_revenue(
                prices_for_rev, cf_profile
            )
            cf_expected = float(cf_profile.mean())
        else:
            effective_revenue = _pkg_ns().estimate_expected_revenue(prices, base_cf)
            cf_expected = base_cf
        # Attribute payment: the highest single buyer among the legacy
        # exogenous EAC, the federal CES premium × tech credit fraction
        # (W2-A plan §5.3 — this is what lets a nuclear_smr candidate earn
        # the premium), and the RPS shadow price — never a sum.
        rps_for_tech = rps_shadow_price if tech in _RENEWABLE_NEW_FUELS else 0.0
        effective_attribute_price = max(
            effective_eac_price_for_tech(config, tech, year), rps_for_tech
        )
        if effective_attribute_price > 0.0:
            effective_revenue += (
                effective_attribute_price * cf_expected * HOURS_PER_YEAR
            )
        # FF-2A item 1 (BLK-7 / term c, gated entry_vre_capacity_revenue):
        # wind/solar entry earns the resource-adequacy capacity payment on its
        # accredited fraction — the SAME per-firm-MW price seam thermal entry
        # uses (fixed net-CONE, or the CR-1 sloped curve at reserve_position
        # when the clearing gate is armed) times the class credit from the ONE
        # adequacy resolver (penetration-indexed published ELCC curve under
        # renewable_elcc_curves, evaluated at the model's own installed
        # nameplate — rule 19: the payment can never diverge from the ledger).
        # Energy-only ISOs price capacity at zero, so this is structurally a
        # no-op there; an RA-saturated build zone collapses the payment, the
        # same locational gate the thermal branch applies.
        vre_capacity_payment = 0.0
        if _vre_capacity_on and tech in _RENEWABLE_NEW_FUELS:
            ra_zone = get_renewable_zone(iso_config.name, tech)
            if not _zone_is_long(deliverability_headroom, ra_zone):
                design = MARKET_DESIGN.get(iso_config.name, DEFAULT_MARKET_DESIGN)
                firm_price = design.capacity_price_per_firm_mw_yr(
                    config, reserve_position, iso=iso_config.name, year=year
                )
                if firm_price > 0.0:
                    credit = resolve_renewable_capacity_credit(
                        tech,
                        iso_config.name,
                        installed_mw=_vre_nameplate.get(tech),
                        peak_demand_mw=(
                            peak_demand_mw if peak_demand_mw > 0.0 else None
                        ),
                        curves_enabled=config.renewable_elcc_curves,
                    )
                    vre_capacity_payment = firm_price * float(credit or 0.0)
            effective_revenue += vre_capacity_payment
        # lcoe uses base_cf internally, so lcoe x hours x base_cf is the
        # CF-independent annualized fixed cost in $/MW-yr — it stays on
        # base_cf even when the revenue side uses the zonal profile.
        annual_cost = lcoe * HOURS_PER_YEAR * base_cf
        _attr_rev = (
            effective_attribute_price * cf_expected * HOURS_PER_YEAR
            if effective_attribute_price > 0.0
            else 0.0
        )
        energy_only_rev = effective_revenue - _attr_rev - vre_capacity_payment
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
                resolve_real_discount_rate(config, tech), _costs["lifetime_yr"]
            )
            _rows[tech] = {
                "tech": tech,
                "kind": "vre" if tech in _RENEWABLE_NEW_FUELS else "must_run",
                "cf_base": float(base_cf),
                "cf_expected": float(cf_expected),
                "cf_shape_aware": bool(cf_profile is not None),
                "energy_revenue_per_mw_yr": float(energy_only_rev),
                "attribute_revenue_per_mw_yr": float(_attr_rev),
                "attribute_price": float(effective_attribute_price),
                "rps_shadow_price": float(rps_shadow_price),
                # Measured VRE capacity payment (BLK-7): $0 unless the
                # entry_vre_capacity_revenue gate is armed in a capacity-
                # market ISO.
                "capacity_revenue_per_mw_yr": float(vre_capacity_payment),
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
    # FF-2A pending-queue netting (entry_commissioning_lag): decided-but-not-
    # yet-commissioned MW occupy the same physical queue the caps measure, so
    # they are netted from this decision year's per-tech / ladder budgets —
    # the developer's view of the queue, and what stops the same deficit being
    # re-decided every year of the lag (pipeline-stuffing cobweb).
    _pending_by_tech: dict[str, float] = {}
    if entry_pipeline:
        for _row in entry_pipeline:
            _pending_by_tech[_row["tech"]] = _pending_by_tech.get(
                _row["tech"], 0.0
            ) + float(_row["mw"])
    # FF-2A growth-ladder budgets (entry_rate_limits): per TECH, not group —
    # the measured throughput seed is tech-grain. Absent tech ⇒ no ladder cap.
    _ladder_remaining: dict[str, float] = {}
    _lag_on = bool(getattr(config, "entry_commissioning_lag", False)) and (
        entry_pipeline is not None
    )
    for seq, (_, tech) in enumerate(margins):
        if remaining <= 0.0:
            if _diag and tech in _rows:
                _rows[tech]["build_mw"] = 0.0
                _rows[tech]["binding_cap"] = "iso_budget_exhausted"
            continue
        # Each tech is capped by its (possibly shared) per-tech queue limit
        # and by what is left of the shared ISO budget; both bind. The
        # growth ladder and the pending queue (when armed) bind on top.
        group = _QUEUE_CAP_GROUP.get(tech, tech)
        if group not in group_remaining:
            group_remaining[group] = max(
                0.0,
                per_tech_cap_gw.get(group, 0.0) * 1000.0
                - _pending_by_tech.get(tech, 0.0),
            )
        build_mw = min(group_remaining[group], remaining)
        _cap_label = None
        if entry_rate_caps_mw is not None and tech in entry_rate_caps_mw:
            if tech not in _ladder_remaining:
                _ladder_remaining[tech] = max(
                    0.0,
                    float(entry_rate_caps_mw[tech]) - _pending_by_tech.get(tech, 0.0),
                )
            if _ladder_remaining[tech] < build_mw:
                build_mw = _ladder_remaining[tech]
                _cap_label = "growth_ladder"
        if build_mw <= 0.0:
            if _diag and tech in _rows:
                _rows[tech]["build_mw"] = 0.0
                _rows[tech]["binding_cap"] = _cap_label or "per_tech_cap_zero"
            continue
        remaining -= build_mw
        group_remaining[group] -= build_mw
        if tech in _ladder_remaining:
            _ladder_remaining[tech] -= build_mw
        if _diag and tech in _rows:
            _rows[tech]["build_mw"] = float(build_mw)
            _rows[tech]["binding_cap"] = _cap_label or (
                "per_tech_cap"
                if build_mw >= per_tech_cap_gw.get(group, 0.0) * 1000.0 - 1e-6
                else "iso_budget"
            )
        # Commissioning: in-year (byte-identical default), or deferred to the
        # measured clearance→COD lag (entry_commissioning_lag) — the decision
        # is booked as a pending-pipeline row that evolve_fleet commissions at
        # cod_year, with both years carried into the evolution ledger.
        _cod_lag = (
            ENTRY_COD_LAG_YEARS.get(tech, ENTRY_COD_LAG_DEFAULT_YEARS) if _lag_on else 0
        )
        if tech in _RENEWABLE_NEW_FUELS:
            target_zone = get_renewable_zone(iso_config.name, tech)
            if _cod_lag > 0:
                entry_pipeline.append(
                    {
                        "tech": tech,
                        "mw": float(build_mw),
                        "zone": target_zone,
                        "decision_year": int(year),
                        "cod_year": int(year) + _cod_lag,
                        "seq": int(seq),
                        "kind": "vre",
                    }
                )
            else:
                zone_acc = renewable_additions.setdefault(target_zone, {})
                zone_acc[tech] = zone_acc.get(tech, 0.0) + build_mw
        else:
            if _cod_lag > 0:
                entry_pipeline.append(
                    {
                        "tech": tech,
                        "mw": float(build_mw),
                        "zone": zone,
                        "decision_year": int(year),
                        "cod_year": int(year) + _cod_lag,
                        "seq": int(seq),
                        "kind": "thermal",
                    }
                )
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
