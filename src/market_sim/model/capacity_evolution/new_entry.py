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
    ENTRY_EXHAUSTION_TRANCHE_MW,
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
from market_sim.policy.clean_tiers import clean_credit_for_zone
from market_sim.policy.federal_ces import effective_eac_price_for_tech
from market_sim.policy.rps import rps_credit_for_zone
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


# Candidate-tech aliases for ATTRIBUTE (clean-tier) crediting: the clean
# qualifying sets are FUEL_TYPE_MAP names, so a nuclear candidate tech maps
# to its fleet fuel class. Every other tech name IS its fuel name.
_TECH_TO_ATTRIBUTE_FUEL: dict[str, str] = {
    "nuclear_smr": "nuclear",
    "nuclear_large": "nuclear",
}


def _clean_credit_for_tech(
    tech: str,
    iso_config,
    zone_names: list[str] | None,
    clean_attribute_price_by_fuel: "dict[str, np.ndarray] | None",
    zone_override: str | None = None,
) -> float:
    """Return a candidate tech's clean-tier attribute credit (FFR-7B Arm 3).

    Fuel- and zone-resolved through the ONE shared consumer helper
    (``policy.clean_tiers.clean_credit_for_zone``): VRE candidates at their
    ``get_renewable_zone`` build zone, thermal/emerging candidates at the
    ISO's default build zone (``_default_build_zone`` — the same siting the
    built Generator receives). 0.0 whenever the family is off, the fuel is
    in no region's qualifying set, or no zone context exists.
    """
    if not clean_attribute_price_by_fuel:
        return 0.0
    fuel = _TECH_TO_ATTRIBUTE_FUEL.get(tech, tech)
    if tech in _RENEWABLE_NEW_FUELS:
        zi = _candidate_zone_idx(
            tech, iso_config.name, zone_names, zone_override=zone_override
        )
    else:
        default_zone = _default_build_zone(iso_config)
        zi = (
            zone_names.index(default_zone)
            if zone_names and default_zone in zone_names
            else None
        )
    return clean_credit_for_zone(clean_attribute_price_by_fuel, fuel, zi)


def _candidate_zone_idx(
    tech: str, iso: str, zone_names: list[str] | None, zone_override: str | None = None
) -> int | None:
    """Return a VRE candidate's build-zone LP index, or ``None`` unknown.

    The zone the K-row RPS credit is resolved at (FFR-7B Arm 2): the same
    ``get_renewable_zone`` target the shape-aware revenue screen and the RA
    payment already use — one notion of the candidate's location. ``None``
    (no zone ordering supplied, or the target zone is not in it) makes
    ``rps_credit_for_zone`` degrade to 0.0 for a vector credit — never a
    broadcast max. ``zone_override`` (capx D33 ``entry_vre_zone_selection``)
    substitutes the screen's resolved build zone for the single
    :data:`RENEWABLE_ZONE_ALLOCATION` bucket, so the credit is still read at
    exactly one notion of the candidate's location.
    """
    if not zone_names:
        return None
    target_zone = zone_override or get_renewable_zone(iso, tech)
    if target_zone in zone_names:
        return zone_names.index(target_zone)
    return None


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

    ``nuclear_smr`` stays in the classic tuple (its costing/queue-group
    plumbing is the classic path), but when ``config.smr_available_year``
    is set (FFR-9C R-b; GATED default-off = ``None`` = the shipped
    always-eligible posture) it joins the pool only from that year — the
    ``_EMERGING_AVAILABLE_YEAR`` gate, applied to a classic tech without
    relocating its costing. ATB costs new nuclear from 2030 only
    (constants.NEW_ENTRY_COSTS), so an armed run passes the ATB-cited 2030.
    """
    candidates = list(_NEW_ENTRY_TECHS)
    if config.smr_available_year is not None and year < config.smr_available_year:
        candidates.remove("nuclear_smr")
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


def wind_ptc_levelized_per_mwh(
    config: ScenarioConfig, life_override: float | None = None
) -> float:
    """Return the §45 wind PTC levelized over the plant's book life, in $/MWh.

    The statutory credit runs ``min(config.ira_ptc_credit_window_years, book
    life)`` years from placed-in-service — 10 years, 26 U.S.C.
    §45(a)(2)(A)(ii); §45Y(b)(1)(B) is identical for the tech-neutral
    successor — so its $/MWh value is levelized over the full book life at
    the screen's own discount rate: PV(window annuity)/PV(life annuity) =
    CRF(life)/CRF(window), exactly the construction the new-build CCS LCOE
    applies to the §45Q window (W2-C; rule 19 ``[R-ONE-MECH]`` — one
    levelization pattern, reused). ``None`` (the indefinite-extension /
    unwindowed-control scenario) leaves the rate unscaled, reproducing the
    pre-FFR-4C full-life crediting exactly.

    Eligibility is the CALLER's gate, unchanged: the
    ``ira_wind_solar_last_year`` OBBBA cliff decides *whether* a vintage
    earns the credit; this function only decides *how much* an earning
    vintage's credit is worth per levelized MWh. This is the single
    computation site for the screen-side wind PTC — ``compute_lcoe`` and
    ``policy.ira.apply_ira_credits_to_lcoe`` both delegate here. The
    dispatch-side PTC offer is a separate surface and does not use it.

    Args:
        config: Scenario config supplying the PTC rate, the credit window,
            the wind cost record (book life) and the discount rate.
        life_override: Cost-recovery period, yr, in place of the tech's book
            life. REPORTING-ONLY (see :func:`compute_lcoe`); ``None`` — the
            default every solve-path caller takes — reproduces the book-life
            levelization byte-for-byte.

    Returns:
        The levelized §45 credit in $/MWh of plant output.
    """
    costs = resolve_new_entry_costs(config)["wind"]
    rate = resolve_real_discount_rate(config, "wind")
    life = float(life_override if life_override is not None else costs["lifetime_yr"])
    window = config.ira_ptc_credit_window_years
    window_years = life if window is None else min(float(window), life)
    factor = _capital_recovery_factor(rate, life) / _capital_recovery_factor(
        rate, window_years
    )
    return config.ira_ptc_wind * factor


def compute_lcoe(
    tech_type: str,
    year: int,
    config: ScenarioConfig,
    cumulative_gw: float | None = None,
    cf_override: float | None = None,
    life_override: float | None = None,
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
        cf_override: Expected capacity factor in place of the tech's national
            ``base_cf``. REPORTING-ONLY (see below).
        life_override: Cost-recovery period, yr, in place of the tech's book
            life — it drives BOTH the capital-recovery factor and the wind
            PTC's levelization window, because they are the same period by
            construction. REPORTING-ONLY (see below).

    Returns:
        The IRA-adjusted LCOE in $/MWh.

    Note:
        ``cf_override``/``life_override`` exist for the MARGINAL-ABATEMENT
        REPORTING surface (``scripts/build_mac_sidecar.py``), which prices a
        project on its own grid's measured output over a contract-length
        recovery period rather than at ATB's national CF over book life. They
        are NOT a solve-path channel: no ``ScenarioConfig`` field reaches them,
        every capacity-evolution caller leaves both ``None``, and at ``None``
        this function is byte-identical to its pre-override form. Keeping them
        here rather than re-deriving the arithmetic in the reporting script is
        rule 19 ``[R-ONE-MECH]``: ONE LCOE construction, so the credit layering
        (ITC before annualization, PTC levelized after) cannot drift between
        the screen that builds plants and the page that prices their abatement.
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

    life = life_override if life_override is not None else costs["lifetime_yr"]
    cf = cf_override if cf_override is not None else costs["base_cf"]

    crf = _capital_recovery_factor(resolve_real_discount_rate(config, tech_type), life)
    annual_cost_per_kw = capex_per_kw * crf + costs["fom_per_kw_yr"]
    # Annual generation per kW of capacity, expressed in MWh.
    annual_mwh_per_kw = HOURS_PER_YEAR * cf / 1000.0
    lcoe = annual_cost_per_kw / annual_mwh_per_kw

    # Wind PTC: a per-MWh production credit, correctly subtracted post-hoc —
    # levelized over min(statutory window, book life), never credited for the
    # plant's whole life (FFR-4C, D-13; see wind_ptc_levelized_per_mwh).
    if tech_type == "wind":
        if year <= config.ira_wind_solar_last_year:
            lcoe -= wind_ptc_levelized_per_mwh(config, life_override=life_override)

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
        # capx D77: same stamp the retrofit screen applies, for the same reason
        # -- a unit's capture island is a property of the unit, so any consumer
        # that re-books a measured host rate over ``emission_rate_co2`` books
        # the capture with it. Inert on this path today (a newly built unit
        # carries ``plant_code = 0``, so the plant-keyed measured-rate
        # restoration never matches it), and set anyway so the invariant
        # "a captured unit declares its capture" holds for every CCS unit in
        # the fleet rather than only for retrofits.
        kwargs["ccs_capture_fraction"] = config.ccs_capture_rate
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


def pipeline_lookahead_units(
    entry_pipeline: list[dict] | None,
    through_year: int,
    config: ScenarioConfig,
    iso: str,
) -> tuple[list[Generator], dict[tuple[str, str], float]]:
    """Split the pending-entry pipeline into what is ONLINE by ``through_year``.

    The capacity screens' look-ahead pro-forma
    (:func:`market_sim.runner._lookahead_reprice_signal`) prices a future
    year's net load into the *current* fleet's merit stack, so a decision
    already committed to the ``entry_pipeline`` is invisible to it and the same
    opportunity is re-decided every lag year (FFR-4A §3.5 / E-2). This returns
    the pipeline's contribution to the priced year's supply, split by how each
    kind enters that pro-forma:

    * **thermal** rows become ``Generator`` objects via the SAME
      :func:`_make_new_generator` call ``evolve_fleet``'s step-4.5
      commissioning makes, so their heat rate, VOM, emission rate and forced-
      outage rate are the ones the unit will actually carry -- no second cost
      construction to drift (rule 19 ``[R-ONE-MECH]``);
    * **VRE** rows carry no Generator (they enter the model as zone renewable
      pools), so they are returned as ``{(zone, tech): mw}`` for the caller to
      value at that zone's own hourly capacity factor.

    A row is included iff ``cod_year <= through_year`` -- it is online in the
    year being priced. Rows still in construction are correctly absent: they
    set no price in that year. **Zero new tunables** (rule 24
    ``[R-REGISTRY]``): every quantity is a field the row already carries or a
    shipped constant.

    Args:
        entry_pipeline: The cross-year pending-entry queue, or ``None``. NOT
            mutated -- this is a read-only view.
        through_year: The year being priced; rows with a later COD are excluded.
        config: Scenario configuration (passed through to the generator build).
        iso: ISO identifier (passed through to the generator build).

    Returns:
        ``(thermal_units, vre_mw_by_zone_tech)``. Both are empty when the
        pipeline is empty or holds nothing online by ``through_year``.
    """
    units: list[Generator] = []
    vre_mw: dict[tuple[str, str], float] = {}
    for row in entry_pipeline or []:
        if int(row["cod_year"]) > int(through_year):
            continue
        if row.get("kind") == "vre":
            key = (row["zone"], row["tech"])
            vre_mw[key] = vre_mw.get(key, 0.0) + float(row["mw"])
            continue
        unit = _make_new_generator(
            row["tech"],
            float(row["mw"]),
            row["zone"],
            int(row["cod_year"]),
            int(row["seq"]),
            config,
            iso,
        )
        # Same id convention step 4.5 uses, so a pro-forma unit and the unit it
        # anticipates are traceable to one decision cohort.
        unit.unit_id = (
            f"{row['tech']}_new_{int(row['decision_year'])}"
            f"c{int(row['cod_year'])}_{int(row['seq'])}"
        )
        unit.name = unit.unit_id
        units.append(unit)
    return units, vre_mw


def apply_economic_new_entry(
    fleet: list[Generator],
    prices: np.ndarray,
    year: int,
    config: ScenarioConfig,
    iso: str,
    rps_shadow_price: "float | np.ndarray" = 0.0,
    clean_attribute_price_by_fuel: "dict[str, np.ndarray] | None" = None,
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
    procured_flow_mw: dict[str, float] | None = None,
    locality_prices_by_zone: dict[str, float] | None = None,
    locality_cost_ratio_by_zone: dict[str, float] | None = None,
    entry_reprice=None,
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
        rps_shadow_price: Prior year's RPS shadow price in $/MWh — a scalar
            (legacy single ISO-wide row) or a per-zone ``(n_zones,)`` vector
            (K-row compliance-region grain, FFR-7B Arm 2), resolved at each
            candidate's build zone via ``policy.rps.rps_credit_for_zone``.
            Credited to RPS-eligible renewables as an attribute payment,
            taken as the max of it and the exogenous EAC (the two do not
            stack).
        clean_attribute_price_by_fuel: Prior year's clean-tier row duals
            mapped to per-(fuel, zone) credits (FFR-7B Arm 3,
            ``policy.clean_tiers.clean_credit_by_fuel``). Enters the SAME
            max() as the EAC and RPS credits — never a sum. ``None``
            (family off) is byte-identical.
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
        procured_flow_mw: ``{tech: mw}`` commissioning THIS YEAR through the
            FFR-5E procurement channel (``vre_procurement_additions_enabled``),
            netted from the ISO budget and the per-tech queue cap so one
            physical queue is not spent twice (design §2.3(b)). A per-year
            FLOW against annual caps — never a cumulative stock, which is
            what would re-create FFR-4A's dimensional defect (§2.3(c)) — and
            independent of ``entry_pipeline_aware_signal``. ``None``
            (default, and always ``None`` while the gate is off) is
            byte-identical.
        locality_prices_by_zone: capx D59 (``locality_capacity_curves``) —
            ``{zone: locality capacity price $/firm-MW-yr}`` from
            :func:`~market_sim.model.capacity_evolution.retirements.
            locality_prices_by_zone`. A VRE candidate's RA payment is settled
            at max(NYCA, its sited zone's locality price) (ICAP Manual
            §5.15.2), and every thermal candidate is ALSO screened sited in
            each priced locality — that zone's own hourly LP prices, its
            settled capacity price and its published Gross-CONE cost ratio
            (``locality_cost_ratio_by_zone``) — and built where its margin is
            highest, a tie keeping the default zone (DESIGN §5.5). ``None`` /
            empty is byte-identical.
        locality_cost_ratio_by_zone: ``{zone: GrossCONE_locality / GrossCONE_NYCA}``
            of the delivery year's published vintage (capx D59); absent zones
            cost 1.0.
        entry_reprice: D11-R margin-exhaustion walk state
            (``runner._EntryRepriceWalk``, GATED ``entry_margin_exhaustion``).
            When supplied, the bang-bang allocation — each clearing tech
            builds ``min(per-tech room, ISO budget)`` — is REPLACED by the
            L-1b closure (``docs/FINDING-entry-signal-l1-2026-08.md`` §2):
            capacity is added in ``ENTRY_EXHAUSTION_TRANCHE_MW`` tranches to
            the best-margin candidate, the screen's own signal (and hourly
            reserve legs) are re-priced through the walk after every tranche,
            and the walk stops when no candidate's repriced margin clears
            zero or every cap binds — the SAME caps as the bang-bang path.
            The walk state is shared with the storage screen (which runs
            after this one). ``None`` (default) keeps the bang-bang loop
            byte-identically.

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
    # D11-R walk re-evaluation records: per candidate, the signal-dependent
    # revenue construction plus its signal-independent terms, so the walk can
    # recompute each margin at the repriced signal without re-running the
    # screen body (every non-price term is held exactly as screened).
    # Populated only when the walk is armed; empty otherwise.
    _walk = entry_reprice is not None
    _calc: dict[str, dict] = {}
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

    # capx D33 build-zone resolution (``entry_vre_zone_selection``, GATED
    # default-OFF ⇒ byte-identical). OFF: every economically-entered VRE MW is
    # sited in the single :data:`RENEWABLE_ZONE_ALLOCATION` bucket — a table
    # whose own docstring calls it the FALLBACK for ISOs with no plant-location
    # data, and which the procurement channel already bypasses by siting from
    # coordinates (``load_procured_vre_additions``, FFR-3V §4.4). ON: the
    # candidate is screened in every zone that has the resource and sited where
    # its own margin is highest — the developer's choice, over the zonal
    # machinery the screen ALREADY carries (per-zone CF profile, per-zone LP
    # price, the K-row zone-resolved REC/clean credit, the zonal RA gate). Cost
    # is zone-invariant, so argmax(revenue) IS argmax(margin). No free parameter
    # (rule 21) and nothing measured about the outcome enters (rule 13): the
    # eligibility masks are statute, the CFs and prices are the model's own.
    _zone_selection_on = bool(getattr(config, "entry_vre_zone_selection", False))
    _vre_zone_by_tech: dict[str, str] = {}
    # capx D59: the locality a thermal candidate was sited in by the locality
    # siting leg (absent ⇒ the default build zone, byte-identical).
    _thermal_zone_by_tech: dict[str, str] = {}

    def _vre_cap_payment(tech: str, ra_zone: str) -> float:
        """The RA capacity payment a VRE candidate earns sited in ``ra_zone``.

        The ONE construction of term c (rule 19): shared verbatim by the zone
        chooser below and the screen's own revenue build-up, so a candidate can
        never be ranked on one capacity payment and screened on another.
        """
        if not (_vre_capacity_on and tech in _RENEWABLE_NEW_FUELS):
            return 0.0
        if _zone_is_long(deliverability_headroom, ra_zone):
            return 0.0
        design = MARKET_DESIGN.get(iso_config.name, DEFAULT_MARKET_DESIGN)
        firm_price = design.capacity_price_per_firm_mw_yr(
            config, reserve_position, iso=iso_config.name, year=year
        )
        # capx D59: the sited zone's locality price, max-stacked on the NYCA
        # leg (ICAP Manual §5.15.2); None / absent zone is byte-identical.
        _lp = (locality_prices_by_zone or {}).get(ra_zone)
        if _lp is not None and design.capacity_market:
            firm_price = max(firm_price, float(_lp))
        if firm_price <= 0.0:
            return 0.0
        credit = resolve_renewable_capacity_credit(
            tech,
            iso_config.name,
            installed_mw=_vre_nameplate.get(tech),
            peak_demand_mw=(peak_demand_mw if peak_demand_mw > 0.0 else None),
            curves_enabled=config.renewable_elcc_curves,
            nqc_curves_enabled=config.caiso_nqc_accreditation,
            # capx D75-R: a VRE candidate is paid for the firm MW the delivery
            # year's own accreditation would credit it with — the same ladder
            # the adequacy ledger applies (rule 19), so a candidate can never
            # be screened on one accreditation and counted on another.
            config=config,
            year=year,
        )
        return firm_price * float(credit or 0.0)

    def _choose_vre_zone(tech: str, default_zone: str) -> str:
        """Return the highest-margin build zone for a VRE candidate.

        Ranks every zone whose CF profile carries resource on the SAME revenue
        construction the screen then applies (energy at that zone's own hourly
        prices and CF, the zone-resolved attribute credit, the zonal RA
        payment). Ties and any missing zonal input fall back to
        ``default_zone``, so the gate can never silently relocate a build on
        incomplete data.
        """
        cf_zonal = wind_cf if tech == "wind" else solar_cf
        if cf_zonal is None or not zone_names:
            return default_zone
        prices_arr = np.asarray(prices, dtype=float)
        cf_arr = np.asarray(cf_zonal, dtype=float)
        if prices_arr.ndim != 2 or cf_arr.ndim != 2:
            return default_zone

        def _zone_revenue(zi: int, zname: str) -> float | None:
            """Screened revenue for ``tech`` sited in one zone, or None."""
            if zi >= cf_arr.shape[0] or zi >= prices_arr.shape[0]:
                return None
            cf_z = cf_arr[zi]
            if float(cf_z.max()) <= 0.0:
                return None
            rev = _pkg_ns().estimate_expected_revenue(prices_arr[zi], cf_z)
            attr = max(
                effective_eac_price_for_tech(config, tech, year),
                rps_credit_for_zone(rps_shadow_price, zi),
                _clean_credit_for_tech(
                    tech,
                    iso_config,
                    zone_names,
                    clean_attribute_price_by_fuel,
                    zone_override=zname,
                ),
            )
            if attr > 0.0:
                rev += attr * float(cf_z.mean()) * HOURS_PER_YEAR
            return rev + _vre_cap_payment(tech, zname)

        # The incumbent is the allocation bucket, and it is displaced only by a
        # STRICTLY better zone: a tie — every zone identical, or a zone-blind
        # scalar REC dual — leaves the siting exactly where the gate-off path
        # puts it, so the gate can never relocate a build on no information.
        best_zone = default_zone
        best_rev = (
            _zone_revenue(zone_names.index(default_zone), default_zone)
            if default_zone in zone_names
            else None
        )
        for zi, zname in enumerate(zone_names):
            rev = _zone_revenue(zi, zname)
            if rev is None:
                continue
            if best_rev is None or rev > best_rev:
                best_rev, best_zone = rev, zname
        return best_zone

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
            # candidates earn the premium), and the RPS shadow price — the
            # latter resolved at the candidate's BUILD ZONE under the K-row
            # compliance-region grain (FFR-7B Arm 2: a scalar passes
            # through; a per-zone vector indexes by zone, so an ineligible
            # zone's candidate is never credited another region's dual).
            rps_for_tech = (
                rps_credit_for_zone(
                    rps_shadow_price,
                    _candidate_zone_idx(tech, iso_config.name, zone_names),
                )
                if tech in _RENEWABLE_NEW_FUELS
                else 0.0
            )
            # Clean-tier credit (FFR-7B Arm 3): enters the SAME max() —
            # this is what lets a hydrogen_ct/hydrogen_ccgt (MN carbon-free)
            # or gas_cc_ccs (MI clean) candidate earn a state clean dual —
            # never a sum (one certificate, FFR-6B §6.4).
            clean_for_tech = _clean_credit_for_tech(
                tech, iso_config, zone_names, clean_attribute_price_by_fuel
            )
            effective_attribute_price = max(
                effective_eac_price_for_tech(config, tech, year),
                rps_for_tech,
                clean_for_tech,
            )
            attribute_rev = 0.0
            if effective_attribute_price > 0.0:
                attribute_rev = effective_attribute_price * cf * HOURS_PER_YEAR
                revenue += attribute_rev
            annual_cost_emerging = lcoe * HOURS_PER_YEAR * cf
            margin = revenue - annual_cost_emerging
            if margin > 0.0:
                margins.append((margin, tech))
            if _walk:
                # Emerging techs are screened as flat-CF output at the mean
                # price; the walk re-evaluates on the same basis and their
                # tranches enter as flat CF-shaped net-load reduction (the
                # screen's own representation).
                _calc[tech] = {
                    "kind": "flat_cf",
                    "cf": float(cf),
                    "fixed_rev": float(attribute_rev),
                    "annual_cost": float(annual_cost_emerging),
                }
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
            # capx D59 (locality_capacity_curves): the same candidate screened
            # sited in each priced locality — that zone's own hourly LP prices
            # (the same reserve legs), the settled capacity price
            # max(NYCA, locality) through the ONE seam, and the annualized
            # fixed cost scaled by the published locality/NYCA Gross-CONE
            # ratio. Sited at the argmax margin; a tie keeps the default zone
            # (D33's discipline). Empty dicts ⇒ this block is skipped and the
            # default-zone screen is byte-identical.
            if locality_prices_by_zone and zone_names:
                _best_zone, _best = (
                    zone,
                    energy_margin + capacity_payment + as_credit - fixed_cost,
                )
                _prices_2d = np.asarray(prices, dtype=float)
                for _lz in sorted(locality_prices_by_zone):
                    if _lz == zone or _lz not in zone_names or _prices_2d.ndim != 2:
                        continue
                    _zi = zone_names.index(_lz)
                    if _zi >= _prices_2d.shape[0]:
                        continue
                    _hv = np.maximum(_prices_2d[_zi] - var_cost, 0.0)
                    if r_tech is not None:
                        _n = min(_hv.size, r_tech.size)
                        _hv = np.maximum(_hv[:_n], r_tech[:_n])
                    _em = float(_hv.sum())
                    _cp = (
                        0.0
                        if _zone_is_long(deliverability_headroom, _lz)
                        else capacity_revenue_per_mw_yr(
                            iso_config.name,
                            tech,
                            EFORD[tech],
                            config,
                            reserve_position,
                            year,
                            locality_price_per_firm_mw_yr=locality_prices_by_zone[_lz],
                        )
                    )
                    _fc = fixed_cost * float(
                        (locality_cost_ratio_by_zone or {}).get(_lz, 1.0)
                    )
                    _mz = _em + _cp + as_credit - _fc
                    if _mz > _best:
                        _best, _best_zone = _mz, _lz
                        energy_margin, capacity_payment, fixed_cost = _em, _cp, _fc
                if _best_zone != zone:
                    _thermal_zone_by_tech[tech] = _best_zone
            effective_revenue = energy_margin + capacity_payment + as_credit
            margin = effective_revenue - fixed_cost
            if margin > 0.0:
                margins.append((margin, tech))
            if _walk:
                # Dispatchable thermal: the walk re-evaluates the hourly
                # best-use integral max(price - vc, r) on the repriced signal
                # and repriced reserve legs; capacity payment, annual AS
                # credit and fixed cost are held exactly as screened. The
                # tranche increment is the probe's own: entrant variable cost
                # against EFORD-derated capacity into the merit stack.
                _calc[tech] = {
                    "kind": "thermal",
                    "var_cost": float(var_cost),
                    "reserve_tier": (
                        None
                        if r_tech is None
                        else ("slow" if tech in QUICK_START_FUEL_TYPES else "fast")
                    ),
                    "fixed_rev": float(capacity_payment + as_credit),
                    "annual_cost": float(fixed_cost),
                    "avail": float(1.0 - EFORD[tech]),
                }
            if _diag:
                _rows[tech] = {
                    "tech": tech,
                    "kind": "thermal",
                    "build_zone": _thermal_zone_by_tech.get(tech, zone),
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
        # The candidate's build zone, resolved ONCE and reused by every leg
        # below (revenue shape, REC/clean credit, RA payment, commissioning) —
        # the single notion of the candidate's location the K-row grain
        # requires. Default: the RENEWABLE_ZONE_ALLOCATION bucket.
        build_zone: str | None = None
        if tech in _RENEWABLE_NEW_FUELS:
            build_zone = get_renewable_zone(iso_config.name, tech)
            if _zone_selection_on:
                build_zone = _choose_vre_zone(tech, build_zone)
            _vre_zone_by_tech[tech] = build_zone
        if tech in _RENEWABLE_NEW_FUELS and zone_names:
            cf_zonal = wind_cf if tech == "wind" else solar_cf
            target_zone = build_zone
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
        # the premium), and the RPS shadow price — never a sum. The RPS
        # credit is resolved at the candidate's BUILD ZONE under the K-row
        # compliance-region grain (FFR-7B Arm 2 / FFR-6B §3.2: a broadcast
        # scalar would credit MISO-East's dual to an Arkansas candidate and
        # rebuild the defect the row grain fixed).
        rps_for_tech = (
            rps_credit_for_zone(
                rps_shadow_price,
                _candidate_zone_idx(
                    tech, iso_config.name, zone_names, zone_override=build_zone
                ),
            )
            if tech in _RENEWABLE_NEW_FUELS
            else 0.0
        )
        # Clean-tier credit (FFR-7B Arm 3): the SAME max() — this is what
        # lets a nuclear_smr candidate earn a state clean dual (the first LP
        # row that pays nuclear at all) — never a sum (FFR-6B §6.4).
        clean_for_tech = _clean_credit_for_tech(
            tech,
            iso_config,
            zone_names,
            clean_attribute_price_by_fuel,
            zone_override=build_zone,
        )
        effective_attribute_price = max(
            effective_eac_price_for_tech(config, tech, year),
            rps_for_tech,
            clean_for_tech,
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
            vre_capacity_payment = _vre_cap_payment(tech, build_zone)
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
        if _walk:
            # VRE / must-run: the walk re-values the screened CF basis (the
            # build zone's hourly profile, or the scalar base-CF fallback)
            # against the repriced signal; attribute and capacity payments
            # are held as screened (their CF term is signal-independent).
            # The tranche increment is the same CF basis as MW of CF-shaped
            # output into the net-load VRE term.
            _zi = None
            if cf_profile is not None and zone_names:
                _tz = build_zone or get_renewable_zone(iso_config.name, tech)
                _zi = zone_names.index(_tz) if _tz in zone_names else None
            _calc[tech] = {
                "kind": "vre_profile" if cf_profile is not None else "flat_cf",
                "cf": float(base_cf),
                "cf_profile": cf_profile,
                "zone_idx": _zi,
                "fixed_rev": float(_attr_rev + vre_capacity_payment),
                "annual_cost": float(annual_cost),
            }
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
                # The zone the candidate was screened and (if built) sited in —
                # the measurement that makes the single-bucket siting visible.
                "build_zone": build_zone,
                "cf_base": float(base_cf),
                "cf_expected": float(cf_expected),
                "cf_shape_aware": bool(cf_profile is not None),
                "energy_revenue_per_mw_yr": float(energy_only_rev),
                "attribute_revenue_per_mw_yr": float(_attr_rev),
                "attribute_price": float(effective_attribute_price),
                # Scalar dual recorded verbatim (legacy); under the K-row
                # grain the vector is recorded as the credit THIS tech's
                # build zone resolves to.
                "rps_shadow_price": float(
                    rps_shadow_price if np.ndim(rps_shadow_price) == 0 else rps_for_tech
                ),
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
                # The §45 credit the LCOE actually books: the nominal rate
                # above levelized over min(statutory window, book life) with
                # the SAME helper compute_lcoe uses (FFR-4C, no drift).
                "ptc_wind_levelized_per_mwh": float(
                    wind_ptc_levelized_per_mwh(config)
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
    # FFR-5E procurement-channel netting (design §2.3(b)). The real
    # interconnection queue has ONE throughput and both channels draw on it, so
    # MW the procurement channel commissions THIS YEAR is consumed from this
    # year's budgets before the merchant screen spends them. Without this the
    # model would build the committed pipeline AND a full economic ladder on
    # top of it — the double-count FFR-4A was chartered to remove.
    #
    # WHAT IS NETTED, AND WHY IT IS NOT FFR-4A's DEFECT UNDER A NEW NAME
    # (§2.3(c), the single most likely implementation error here): this nets
    # the MW COMMISSIONING IN THIS YEAR — a FLOW, GW/yr — from a flow cap.
    # Same units on both sides, no stock, no implied D <= C/L, no effect on
    # the ladder's K - L + 1 ratchet. It is therefore INDEPENDENT of
    # entry_pipeline_aware_signal, which relocates the netting of a pending
    # pipeline STOCK: deliberately NOT routed through ``_pending_netting_mw``
    # below, or arming that unrelated gate would silently switch this netting
    # off too. Neither mechanism is a precondition for the other.
    #
    # NOT capped by the ladder or the queue caps (§2.3(a)): for the same reason
    # a confirmed exit bypasses the reliability floor, the caps model the
    # queue's annual throughput and a row already IN the queue with an
    # effective year IS that throughput. Capping it would count one physical
    # constraint twice and could silently delete a project that verifiably
    # exists — hence the netting lands on the SCREEN's budgets, never on the
    # procured MW itself.
    _procured_netting_mw: dict[str, float] = dict(procured_flow_mw or {})
    remaining = max(0.0, queue_budget_mw - sum(_procured_netting_mw.values()))
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
    # FFR-5C entry_pipeline_aware_signal (GATED, default OFF ⇒ byte-identical):
    # armed, the anti-cobweb guard RELOCATES to the pro-forma price signal
    # (runner._lookahead_reprice_signal now prices the pending rows into its
    # merit stack), so the stock netting is dropped from BOTH flow caps below
    # and each binds as the GW/yr rate its own citation defines. The netting is
    # a stock (MW, no time denominator) subtracted from an annual flow: it caps
    # the long-run decision rate at C/L and, on the ladder, kills the ratchet
    # whenever K ≤ L — K−L+1 = 1 at the shipped (2, 2) in 24/24 ISO×tech cells
    # (FFR-4A §3.3/§5, docs/handoffs/ffr-4a-entry-ladder-2026-08-04.md). Rule 19
    # [R-ONE-MECH]: one mechanism per phenomenon — the guard moves, it is
    # neither deleted nor duplicated. ``_pending_by_tech`` itself stays
    # populated (it is the queue state, not the guard).
    _pending_netting_mw: dict[str, float] = (
        {}
        if getattr(config, "entry_pipeline_aware_signal", False)
        else _pending_by_tech
    )
    # FF-2A growth-ladder budgets (entry_rate_limits): per TECH, not group —
    # the measured throughput seed is tech-grain. Absent tech ⇒ no ladder cap.
    _ladder_remaining: dict[str, float] = {}
    _lag_on = bool(getattr(config, "entry_commissioning_lag", False)) and (
        entry_pipeline is not None
    )

    def _commission(tech: str, build_mw: float, seq: int) -> None:
        """Book one tech's cleared MW — pipeline row, generator, or VRE pool.

        Commissioning: in-year (byte-identical default), or deferred to the
        measured clearance→COD lag (entry_commissioning_lag) — the decision
        is booked as a pending-pipeline row that evolve_fleet commissions at
        cod_year, with both years carried into the evolution ledger. Shared
        verbatim by the bang-bang loop and the margin-exhaustion walk.
        """
        _cod_lag = (
            ENTRY_COD_LAG_YEARS.get(tech, ENTRY_COD_LAG_DEFAULT_YEARS) if _lag_on else 0
        )
        if tech in _RENEWABLE_NEW_FUELS:
            # The zone the screen actually valued this candidate in (capx D33);
            # identical to the RENEWABLE_ZONE_ALLOCATION bucket when the gate
            # is off, and the fallback for a tech that never reached the VRE
            # branch (no candidate row ⇒ nothing to commission).
            target_zone = _vre_zone_by_tech.get(tech) or get_renewable_zone(
                iso_config.name, tech
            )
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
                        "zone": _thermal_zone_by_tech.get(tech, zone),
                        "decision_year": int(year),
                        "cod_year": int(year) + _cod_lag,
                        "seq": int(seq),
                        "kind": "thermal",
                    }
                )
            else:
                new_fleet.append(
                    _make_new_generator(
                        tech,
                        build_mw,
                        _thermal_zone_by_tech.get(tech, zone),
                        year,
                        seq,
                        config,
                        iso_config.name,
                    )
                )

    def _init_group(tech: str) -> str:
        """Resolve/initialize a tech's (possibly shared) cap-group budget."""
        group = _QUEUE_CAP_GROUP.get(tech, tech)
        if group not in group_remaining:
            group_remaining[group] = max(
                0.0,
                per_tech_cap_gw.get(group, 0.0) * 1000.0
                - _pending_netting_mw.get(tech, 0.0)
                # FFR-5E: this year's procured commissioning flow (§2.3(b)).
                # wind/solar carry no _QUEUE_CAP_GROUP entry, so group == tech
                # and the tech-keyed flow maps 1:1 onto the group budget.
                - _procured_netting_mw.get(tech, 0.0),
            )
        return group

    def _init_ladder(tech: str) -> None:
        """Initialize a tech's growth-ladder budget (no-op when uncapped)."""
        if (
            entry_rate_caps_mw is not None
            and tech in entry_rate_caps_mw
            and tech not in _ladder_remaining
        ):
            _ladder_remaining[tech] = max(
                0.0,
                float(entry_rate_caps_mw[tech]) - _pending_netting_mw.get(tech, 0.0),
            )

    if entry_reprice is not None:
        # ------------------------------------------------------------------
        # D11-R margin-exhaustion walk (GATED entry_margin_exhaustion): the
        # L-1b closure, live. Rule 21 [R-DOF], in the precommit's words: the
        # volume rule is an equilibrium condition the model already contains
        # — build until the screen's OWN repriced margin is exhausted,
        # bounded by the SAME caps — never a tuned elasticity or damping
        # coefficient. Each tranche goes to the current best-margin
        # candidate; its physical increment enters the lookahead instrument
        # through the model's own seams (entry_reprice) and every margin is
        # re-evaluated on the repriced signal (and repriced hourly reserve
        # legs) before the next tranche. Stops when no candidate clears zero
        # or every cap binds. The final tranche may be partial so a cap
        # binds exactly where the bang-bang path's would (the probe's
        # quantization note, removed).
        # ------------------------------------------------------------------
        _prices0 = np.asarray(prices, dtype=float)
        _T = int(_prices0.shape[-1])
        # Identical to _prices0 at a fresh walk (the delta is zero before any
        # tranche); honors any state a caller committed before this screen.
        sig_walk = entry_reprice.signal(_prices0)
        _r_fast0 = (
            None
            if reserve_price_signal is None
            else np.asarray(reserve_price_signal, dtype=float)
        )
        _r_slow0 = (
            None
            if reserve_price_signal_slow is None
            else np.asarray(reserve_price_signal_slow, dtype=float)
        )
        r_fast_walk, r_slow_walk = _r_fast0, _r_slow0

        def _walk_room(tech: str) -> float:
            """Remaining buildable MW under every cap that binds this tech."""
            group = _init_group(tech)
            room = min(group_remaining[group], remaining)
            _init_ladder(tech)
            if tech in _ladder_remaining:
                room = min(room, _ladder_remaining[tech])
            return room

        def _walk_margin(tech: str) -> float:
            """The screen's own margin re-evaluated at the walk signal."""
            c = _calc[tech]
            if c["kind"] == "thermal":
                ph = sig_walk.mean(axis=0) if sig_walk.ndim > 1 else sig_walk
                hv = np.maximum(ph - c["var_cost"], 0.0)
                if c["reserve_tier"] is not None:
                    r_t = r_slow_walk if c["reserve_tier"] == "slow" else r_fast_walk
                    if r_t is None:
                        # Mirrors the screen: tier requested, leg absent.
                        r_t = np.zeros_like(hv)
                    n = min(hv.size, r_t.size)
                    hv = np.maximum(hv[:n], r_t[:n])
                return float(hv.sum()) + c["fixed_rev"] - c["annual_cost"]
            if c["kind"] == "vre_profile":
                zi = c["zone_idx"]
                pr = (
                    sig_walk[zi] if (zi is not None and sig_walk.ndim > 1) else sig_walk
                )
                rev = _pkg_ns().estimate_expected_revenue(pr, c["cf_profile"])
                return rev + c["fixed_rev"] - c["annual_cost"]
            rev = _pkg_ns().estimate_expected_revenue(sig_walk, c["cf"])
            return rev + c["fixed_rev"] - c["annual_cost"]

        walk_built: dict[str, float] = {}
        order_first: list[str] = []
        cand_techs = [t for _, t in margins if t in _calc]
        # Iteration bound derived from the budgets (never a step-count
        # choice): the ISO budget in whole tranches, plus one possible
        # partial tranche per candidate at each cap.
        _max_steps = (
            int(remaining // ENTRY_EXHAUSTION_TRANCHE_MW) + 2 * len(cand_techs) + 4
        )
        for _ in range(_max_steps):
            if remaining <= 0.0:
                break
            best_tech: str | None = None
            best_margin = 0.0
            for t in cand_techs:
                # 1e-6 MW: numerical guard against float-residue room (a
                # milliwatt is below any physical resolution, not a tunable).
                if _walk_room(t) <= 1e-6:
                    continue
                m = _walk_margin(t)
                if m > best_margin:
                    best_margin, best_tech = m, t
            if best_tech is None:
                break
            tranche = min(ENTRY_EXHAUSTION_TRANCHE_MW, _walk_room(best_tech))
            group = _QUEUE_CAP_GROUP.get(best_tech, best_tech)
            remaining -= tranche
            group_remaining[group] -= tranche
            if best_tech in _ladder_remaining:
                _ladder_remaining[best_tech] -= tranche
            walk_built[best_tech] = walk_built.get(best_tech, 0.0) + tranche
            if best_tech not in order_first:
                order_first.append(best_tech)
            c = _calc[best_tech]
            if c["kind"] == "thermal":
                entry_reprice.add_thermal(c["var_cost"], tranche, c["avail"])
            elif c["kind"] == "vre_profile":
                entry_reprice.add_net_load_reduction(
                    np.asarray(c["cf_profile"], dtype=float) * tranche
                )
            else:
                entry_reprice.add_net_load_reduction(
                    np.full(_T, c["cf"] * tranche, dtype=float)
                )
            sig_walk = entry_reprice.signal(_prices0)
            rd = np.asarray(entry_reprice.reserve_delta(), dtype=float)
            if _r_fast0 is not None:
                n = min(_r_fast0.size, rd.size)
                r_fast_walk = np.maximum(0.0, _r_fast0[:n] + rd[:n])
            if _r_slow0 is not None:
                n = min(_r_slow0.size, rd.size)
                r_slow_walk = np.maximum(0.0, _r_slow0[:n] + rd[:n])
        for seq, tech in enumerate(order_first):
            _commission(tech, walk_built[tech], seq)
        if _diag:
            for _, tech in margins:
                if tech not in _rows:
                    continue
                built = walk_built.get(tech, 0.0)
                _rows[tech]["build_mw"] = float(built)
                if built <= 0.0 and _walk_room(tech) <= 0.0:
                    _rows[tech]["binding_cap"] = "per_tech_cap_zero"
                elif _walk_room(tech) <= 0.0:
                    _rows[tech]["binding_cap"] = (
                        "iso_budget_exhausted" if remaining <= 0.0 else "per_tech_cap"
                    )
                else:
                    _rows[tech]["binding_cap"] = "margin_exhausted"
    else:
        for seq, (_, tech) in enumerate(margins):
            if remaining <= 0.0:
                if _diag and tech in _rows:
                    _rows[tech]["build_mw"] = 0.0
                    _rows[tech]["binding_cap"] = "iso_budget_exhausted"
                continue
            # Each tech is capped by its (possibly shared) per-tech queue
            # limit and by what is left of the shared ISO budget; both bind.
            # The growth ladder and the pending queue (when armed) bind on
            # top.
            group = _init_group(tech)
            build_mw = min(group_remaining[group], remaining)
            _cap_label = None
            _init_ladder(tech)
            if tech in _ladder_remaining and _ladder_remaining[tech] < build_mw:
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
            _commission(tech, build_mw, seq)

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
