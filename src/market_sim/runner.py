"""Command-line entry point and multi-year orchestration for simulations.

A *run* advances one :class:`~market_sim.config.scenarios.ScenarioConfig`
for one ISO across every simulation year, evolving the fleet, solving the
hourly economic dispatch and caching each year's result. A *sweep* expands
a :class:`~market_sim.config.scenarios.SweepDefinition` into many configs
and runs them in parallel.
"""

from __future__ import annotations

import argparse
import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from multiprocessing import cpu_count

import numpy as np

from market_sim.config.constants import (
    END_YEAR,
    HISTORIC_OUTAGE_OVERLAY_BY_ISO,
    START_YEAR,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import (
    ScenarioConfig,
    SweepDefinition,
    resolve_demand_growth_rate,
    resolve_policy_bundle,
)
from market_sim.data.eia_loader import load_demand
from market_sim.data.fleet import (
    Generator,
    apply_coal_tranches,
    assemble_mc,
    build_base_fleet,
    build_dispatch_fleet,
    generators_to_fleet_arrays,
    load_or_synthesize_bins,
    load_planned_additions,
    load_retired_within_window,
)
from market_sim.data.fuel import (
    apply_coal_supply_pricing,
    resolve_annual_gas_price,
    resolve_fuel_prices,
)
from market_sim.data.renewables import (
    inject_offshore_wind_availability,
    load_renewable_profiles,
)
from market_sim.model.capacity import (
    CumulativeDeployment,
    deliverability_headroom_by_zone,
    evolve_fleet,
)
from market_sim.model.commitment import (
    apply_commitment_with_coal_pin,
    as_adequacy_commit,
    compute_commitment,
    compute_monthly_markup,
    reserve_adequacy_commit,
)
from market_sim.model.dispatch import DispatchModel, solve_dispatch
from market_sim.model.ancillary import (
    realized_storage_as_revenue_per_mw_yr,
    realized_thermal_as_revenue_per_mw_yr_by_fuel,
)
from market_sim.model.storage import (
    _elcc_for_duration,
    apply_storage_new_entry,
    build_default_storage,
    load_eia860_pumped_storage,
    storage_cap_profiles,
    storage_units_to_arrays,
)
from market_sim.config.interchange_config import (
    INTERFACE_NEIGHBORS,
    build_interchange_fleet,
    get_interchange_spec,
)
from market_sim.model.transmission import (
    build_incidence_matrix,
    build_interface_groups,
    get_link_bidirectional_array,
    extend_with_import_node,
    get_ttc_array,
    wecc_border_carbon_adder,
)
from market_sim.policy.carbon import resolve_carbon_price
from market_sim.policy.constraints import get_active_policy_constraints
from market_sim.policy.ira import compute_dispatch_credits
from market_sim.policy.eac import apply_eac_to_mc, compute_eac_dispatch_credits
from market_sim.policy.rps import get_rps_target
from market_sim.results.cache import is_cached, load_result, save_result
from market_sim.results.emissions import compute_must_run_emissions, measured_class_cf
from market_sim.results.outputs import FleetContext
from market_sim.results.scarcity import (
    effective_reliability_deployment_mw,
    ercot_as_aware_unit_value,
    nyiso_spin_eligible,
    nyiso_spin_requirement_mw,
    reserve_headroom,
    scarcity_prices,
)

logger = logging.getLogger(__name__)


def _chp_measured_co2_inputs(
    config: ScenarioConfig, iso: str, year: int
) -> tuple[dict[int, float], dict[str, float]]:
    """Return ``(measured_rate_by_plant, class_cf_by_group)`` for CHP must-run.

    Resolves the EM-7 (plan §5 R5) consistency inputs so the behind-the-meter
    must-run reconstruction books CO2 at the **same measured rate its grid
    tranches use** and sizes the forecast fallback with a measured CHP class
    capacity factor instead of the flat 0.85. The rate source mirrors the grid's
    (``fleet.apply_plant_emission_rates*``): the mode-aware v2 artifact when
    ``use_plant_emission_rates_v2`` is on, else the legacy pooled artifact when
    ``use_plant_emission_rates`` is on, else empty (caller keeps the fuel-class
    default) — so BTM and grid CO2 intensity always agree. The class CF is drawn
    from the v2 steam-load history independently of the rate source (empty until
    the v2 artifact carries ``steam_load_klbh_sum``), so the caller falls back to
    the flat ``must_run_cf`` when it is unavailable.
    """
    from pathlib import Path

    import pandas as pd

    from market_sim.data.emission_rates import fuel_class, measured_plant_rates

    by_plant: dict[int, float] = {}
    class_cf: dict[str, float] = {}

    if getattr(config, "use_plant_emission_rates_v2", False):
        path = Path(config.plant_emission_rates_v2_path)
        if path.exists():
            v2 = pd.read_parquet(path)
            v2 = v2[v2["iso"].astype(str) == str(iso)]
            if not v2.empty:
                # Same mode-aware (plant, fuel-class) rate the grid tranches book.
                rate_map = measured_plant_rates(v2, iso, int(year), str(config.mode))
                by_plant = {int(pid): rate for (pid, _fc), rate in rate_map.items()}
                # A plant whose CEMS units span classes: the must-run tranche is
                # gas, so prefer the gas-class rate when present.
                for (pid, fc), rate in rate_map.items():
                    if fc == fuel_class("gas"):
                        by_plant[int(pid)] = rate
                class_cf = measured_class_cf(v2)
    elif getattr(config, "use_plant_emission_rates", False):
        from market_sim.data.fleet import _plant_emission_rate_map

        path = Path(config.plant_emission_rates_path)
        if path.exists():
            # Legacy pooled artifact books the same (co2, nox, so2) tonnes/MWh the
            # grid tranches use; mixed plants are excluded from it (Parish), so
            # they fall through to the fuel-class default on both sides.
            by_plant = {
                int(pid): co2
                for pid, (co2, _nox, _so2) in _plant_emission_rate_map(
                    str(path)
                ).items()
            }
        # Class CF still comes from v2 history when the artifact carries it.
        v2_path = Path(config.plant_emission_rates_v2_path)
        if v2_path.exists():
            v2 = pd.read_parquet(v2_path)
            v2 = v2[v2["iso"].astype(str) == str(iso)]
            if not v2.empty:
                class_cf = measured_class_cf(v2)

    return by_plant, class_cf


def _get_growth_rate(config: ScenarioConfig, year: int) -> float:
    """Return the demand growth rate for a given year.

    Delegates to :func:`market_sim.config.scenarios.resolve_demand_growth_rate`,
    which also honors the PB-1 ``demand_growth_percentile`` sampler lever;
    at its neutral 0.5 default this is identical to the plain
    ``demand_growth_path`` lookup this function used to do directly.
    """
    return resolve_demand_growth_rate(config, year)


def _scale_demand(
    base_demand: np.ndarray, config: ScenarioConfig, year: int
) -> np.ndarray:
    """Scale weather-year demand to the target year using compound growth.

    ``base_demand`` is the *weather year's* actual hourly load, so growth
    compounds from ``config.weather_year`` -- not from the first simulated
    year. Compounding from START_YEAR silently dropped the growth between
    the weather year and the simulation start (e.g. 2024 actuals presented
    as 2026 demand), an error that then propagated through every forecast
    year. A backcast (``year == weather_year``) still gets a factor of 1.
    """
    factor = 1.0
    for y in range(config.weather_year, year):
        factor *= 1.0 + _get_growth_rate(config, y)
    return base_demand * factor


def run_scenario_iso(config: ScenarioConfig, iso: str) -> str:
    """Run every simulation year for one scenario and one ISO, sequentially.

    For each year from :data:`START_YEAR` to :data:`END_YEAR` the fleet is
    evolved from the prior year (or built fresh in the first year), the
    hourly economic dispatch is solved, and the result is cached. A year
    whose result is already cached is loaded and skipped, so re-running a
    scenario does no redundant solving.

    Args:
        config: The scenario configuration to run.
        iso: ISO identifier, e.g. ``"ERCOT"`` or ``"CAISO"``. When it
            differs from ``config.iso`` the config's ISO is overridden so
            every downstream lookup stays consistent.

    Returns:
        The scenario's deterministic ``cache_key``.
    """
    iso = iso.upper()
    if config.iso != iso:
        config = config.with_overrides(iso=iso)

    # Resolve the PB-1 policy_bundle lever to its underlying fields (rule 24:
    # config-build time, no hidden state) before cache_key/run_config capture
    # the config -- a no-op for the neutral "current" default.
    config = resolve_policy_bundle(config)

    iso_config = get_iso_config(iso)
    # Apply ISO-level scenario defaults (e.g. CAISO negative_renewable_offers)
    # for fields the caller has not explicitly set.
    if iso_config.default_scenario_overrides:
        defaults = ScenarioConfig()
        overrides_to_apply = {
            k: v
            for k, v in iso_config.default_scenario_overrides.items()
            if getattr(config, k) == getattr(defaults, k)
        }
        if overrides_to_apply:
            config = config.with_overrides(**overrides_to_apply)

    cache_key = config.cache_key()

    logger.info(
        "run_scenario_iso start: iso=%s cache_key=%s config=%s",
        iso,
        cache_key,
        asdict(config),
    )
    if config.commitment_enabled:
        logger.warning(
            "P2 commitment is a legacy feature; prefer energy_reserve_coopt "
            "for unit commitment pricing."
        )
    # Interconnected ISOs with a configured import node (CAISO's WECC node,
    # PJM's external node) model their neighbors as priced import tranches
    # plus export sinks: pseudo-generators that ride along with the dispatch
    # fleet but never evolve. PJM's external zone is appended to the topology
    # here; CAISO's is baked in. CAISO import tranches carry the CA
    border_carbon = (
        wecc_border_carbon_adder(resolve_carbon_price(config, START_YEAR))
        if iso == "CAISO"
        else 0.0
    )
    interchange_spec = get_interchange_spec(config, iso)
    import_generators = build_interchange_fleet(interchange_spec, border_carbon)
    if import_generators:
        iso_config = extend_with_import_node(iso_config)
    # Part A of capacity_deliverability_limits: replace the calibrated
    # simultaneous-import scalar with the ISO's published per-area SEAM import
    # limit (CAISO branch-group MIC → WECC_import). No-op when the flag is off,
    # the ISO has no seam import_limit, or the data is absent.
    if config.capacity_deliverability_limits:
        from market_sim.config.capacity_area_crosswalk import aggregate_by_zone
        from market_sim.config.interchange_config import IMPORT_ZONE
        from market_sim.data import capacity_deliverability as capdel
        from market_sim.model.transmission import apply_deliverability_seam_limit

        _dy = capdel.resolve_delivery_year(iso, START_YEAR)
        _season = capdel.resolve_season(iso)
        _imp_area = capdel.import_limit_by_area(iso, _dy, _season)
        _imp_types = capdel.area_types_by_area(iso, _dy, _season, "import_limit")
        _imp_by_zone, _ = aggregate_by_zone(iso, _imp_area, _imp_types)
        _import_zone = IMPORT_ZONE.get(iso)
        _seam_mw = _imp_by_zone.get(_import_zone) if _import_zone else None
        if _seam_mw:
            iso_config = apply_deliverability_seam_limit(iso_config, iso, _seam_mw)
            logger.info(
                "%s: capacity_deliverability_limits — seam import cap set to "
                "%.0f MW (summed per-area import_limit)",
                iso,
                _seam_mw,
            )
    zone_names = iso_config.zone_names

    # Weather-year inputs are fixed across the run; load them once. The CF
    # profiles (wind_cf, solar_cf) are resource-driven and stay fixed, but
    # wind_cap and solar_cap are mutable: capacity evolution grows them each
    # year as new renewables are built.
    # When the priced node is active it serves the interchange, so the
    # measured schedule stays out of demand (it would double-count the
    # export); forward years have no measured schedule anyway.
    # Year-matched EIA-860 vintage (backcast scenario knob): point the fleet /
    # storage / renewable / COD-map loaders at data/raw/eia-860/
    # vintage_<year>/ when requested, else the canonical 2025ER snapshot. The
    # weather-year inputs are fixed across the run, so the vintage is set once
    # here, before any load. None (forecast, or no committed vintage dir) resets
    # to the canonical snapshot. See config.paths.set_eia860_vintage.
    from market_sim.config.paths import set_eia860_vintage

    set_eia860_vintage(
        config.eia860_vintage_year if config.mode == "backcast" else None
    )
    base_demand = load_demand(
        iso,
        config.weather_year,
        iso_config,
        td_loss_factor=config.td_loss_factor,
        include_interchange=not import_generators,
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        iso, config.weather_year, iso_config, config
    )
    # Trim profiles to config.hours when running a sub-annual horizon.
    if config.hours < base_demand.shape[1]:
        base_demand = base_demand[:, : config.hours]
        wind_cf = wind_cf[:, : config.hours]
        solar_cf = solar_cf[:, : config.hours]
    incidence = build_incidence_matrix(iso_config.links, zone_names)
    ttc = get_ttc_array(iso_config.links)
    # Aggregate interface limits (CAISO simultaneous WECC import cap): resolved
    # once to flow-column groups; empty for ISOs without an interface_limits
    # entry, so the LP is identical there.
    interface_groups = build_interface_groups(
        iso_config.links, iso_config.interface_limits
    )

    fleet = None
    loss_tracker: dict[str, int] = {}
    prior_results = None

    # Load the CAMPD operational bins once when enabled. The same bin frame
    # builds the dispatch fleet and drives the CHP must-run post-processing.
    # The per-plant binning path is taken by any ISO with a bin artifact
    # (CAMPD_BINNING_ISOS); ISOs without one always fall back
    # to the legacy aggregate_fleet path regardless of ``use_campd_bins``.
    #
    # ERCOT reads its curated per-plant bin sheet
    # (``config.campd_bins_path``); its base fleet is built once from the start
    # year so its bins take the EIA-923 dominant class for that year (a curated
    # bin can't drift), then carry forward through the projection. The other
    # CAMPD ISOs have no curated sheet, so the SAME per-plant bins frame is
    # synthesized from the EIA-860 fleet plus the ISO's CAMPD-derived
    # ``thermal_tranches_<ISO>.csv`` (committed / coal must-run / CC peaking)
    # via ``fleet_to_bins`` -- giving them ERCOT's smoothed rising offer curve
    # and per-plant tranches. An ISO whose synthesis yields no thermal bins
    # (no artifact) falls through to the legacy path. Both branches --
    # and the post-load fallback when the artifact is missing -- live in
    # ``load_or_synthesize_bins``.
    # Within-window plant exits (the backcast mirror of planned additions):
    # whole plants that retired mid-window are absent from the single recent
    # operable snapshot, so they are injected into the base fleet and the COD
    # ramp ages each out by its real retirement month. Backcast-mode only — a
    # forecast must not carry an already-retired unit. Loaded before the bins
    # are synthesized so the retirees are binned with the rest of the fleet.
    retired_within_window: list[Generator] = []
    if config.mode == "backcast":
        retired_within_window = load_retired_within_window(iso, iso_config)

    campd_bins = load_or_synthesize_bins(config, iso, iso_config, retired_within_window)

    # Storage is managed across years like the generation fleet: the base
    # year starts from the deployment-pace fleet, later years grow via the
    # economic new-entry screen.
    storage_units = build_default_storage(iso_config, config)

    # Pumped storage is existing installed capacity (EIA-860 prime mover ``PS``,
    # ~20 GW nationally) with no new build, so the parameterized battery builder
    # never includes it. Prepend the EIA-860 PS fleet to the storage list once,
    # before the new-entry screen -- PS is fixed existing capacity and does not
    # participate in the endogenous battery-growth screen (it persists across
    # years because ``apply_storage_new_entry`` preserves existing units). Per
    # CLAUDE.md rule #12, EIA-860 installed capacity is a physical asset
    # registry, admissible as a forward input in any year.
    ps_units = load_eia860_pumped_storage(iso, START_YEAR, config=config)
    if ps_units:
        storage_units = ps_units + storage_units
        logger.info(
            "%s %d: %d pumped-storage units (%.0f MW) from EIA-860",
            iso,
            START_YEAR,
            len(ps_units),
            sum(u.power_cap_mw for u in ps_units),
        )

    # Known additions (methodology spec §5.4): EIA-860 planned /
    # under-construction thermal units, deterministic through the data
    # horizon. Loaded once; units come online in their EIA-860 effective
    # year via evolve_fleet step 3 (or the first-year fleet below for units
    # already due). Forecast-mode only: a backcast solves a historical year
    # whose fleet snapshot already reflects what was actually built.
    planned_additions: list[Generator] = []
    if config.mode == "forecast":
        planned_additions = load_planned_additions(iso, iso_config)
        if planned_additions:
            logger.info(
                "loaded %d planned EIA-860 additions (%.0f MW, %d-%d)",
                len(planned_additions),
                sum(g.pmax_mw for g in planned_additions),
                min(g.online_year for g in planned_additions),
                max(g.online_year for g in planned_additions),
            )

    # Global cumulative deployment drives the Wright's-Law learning curves.
    # It starts from the reference-year installed base and advances one year
    # of worldwide deployment (plus this ISO's local builds) every year.
    cumulative = CumulativeDeployment.initial()

    for year in range(START_YEAR, END_YEAR + 1):
        year_start = time.perf_counter()
        renewable_additions: dict[str, dict[str, float]] = {}
        retrofit_log: list[dict] = []

        if fleet is None:
            # First year: build the base fleet. With CAMPD binning the fleet
            # comes from the operational bin assignments (base + peak
            # generators per bin); otherwise the EIA-860 fleet is collapsed
            # into equal-width efficiency-bin representatives. Either way the
            # collapse happens before the LP -- the dominant solve-time win.
            fleet = build_base_fleet(
                campd_bins,
                iso,
                iso_config,
                zone_names,
                config,
                retired_within_window,
                planned_additions,
                year,
            )
        else:
            # The RPS shadow price from the prior year's dispatch raises the
            # expected revenue of clean technologies in the new-entry screen.
            prior_rps_shadow = 0.0
            if prior_results is not None and prior_results.get("rps_shadow_price"):
                prior_rps_shadow = prior_results["rps_shadow_price"]
            # Gas price and carbon price for the year feed the new-entry
            # screen so gas CC is charged its expected variable fuel cost.
            # The annual (seasonality-free) delivered gas price keeps
            # capacity evolution aligned with hourly dispatch fuel costs.
            gas_price_year = resolve_annual_gas_price(config, year)
            carbon_price_year = resolve_carbon_price(config, year)
            fleet, loss_tracker, renewable_additions, retrofit_log = evolve_fleet(
                fleet,
                prior_results,
                year,
                config,
                loss_tracker,
                rps_shadow_price=prior_rps_shadow,
                cumulative=cumulative,
                gas_price_per_mmbtu=gas_price_year,
                carbon_price=carbon_price_year,
                eac_price_ccs=config.eac_price_gas_cc_ccs,
            )
            if retrofit_log:
                avg_savings = sum(
                    r["annual_net_savings_per_mw"] for r in retrofit_log
                ) / len(retrofit_log)
                logger.info(
                    "Year %d: %d CCS retrofits, %.0f $/MW-yr avg savings",
                    year,
                    len(retrofit_log),
                    avg_savings,
                )
            # New wind/solar grow the zonal capacity pools that bound the
            # W[z,t] and S[z,t] dispatch variables -- they are not added as
            # flat-availability thermal generators.
            for zone_name, additions in renewable_additions.items():
                z_idx = zone_names.index(zone_name)
                wind_cap[z_idx] += additions.get("wind", 0.0)
                solar_cap[z_idx] += additions.get("solar", 0.0)

        # Storage grows endogenously: year 2026 uses the base fleet, and
        # 2027+ screens arbitrage revenue against cost on prior-year prices.
        prior_storage_ids = {u.unit_id for u in storage_units}
        if prior_results is not None:
            # Locational deliverability headroom for the storage capacity-value
            # gate (no-op unless capacity_deliverability_limits is on). Uses the
            # current thermal fleet plus the zonal renewable pools; existing
            # storage firm is left out so the screen sizes the *marginal* build
            # against the non-storage deliverable capacity.
            storage_headroom: dict[str, float] = {}
            if config.capacity_deliverability_limits:
                wind_by_zone = {z: float(wind_cap[i]) for i, z in enumerate(zone_names)}
                solar_by_zone = {
                    z: float(solar_cap[i]) for i, z in enumerate(zone_names)
                }
                storage_headroom = deliverability_headroom_by_zone(
                    iso,
                    year,
                    fleet,
                    config,
                    wind_pool_by_zone=wind_by_zone,
                    solar_pool_by_zone=solar_by_zone,
                )
            storage_units = apply_storage_new_entry(
                storage_units,
                prior_results["prices"],
                year,
                config,
                iso,
                cumulative=cumulative,
                deliverability_headroom=storage_headroom,
                endogenous_as_revenue_per_mw_yr=prior_results.get(
                    "storage_as_revenue_per_mw_yr"
                ),
            )
        storage = storage_units_to_arrays(storage_units, zone_names)

        if getattr(config, "storage_vintage_ramp", False):
            power_cap_2d, energy_cap_2d = storage_cap_profiles(
                storage_units, storage, config.hours
            )
            if power_cap_2d is not storage.power_cap:
                storage.power_cap = power_cap_2d
                storage.energy_cap = energy_cap_2d
                logger.info(
                    "%s %d: storage vintage ramp applied — %d units with mid-year COD",
                    iso,
                    year,
                    int((power_cap_2d != power_cap_2d[:, :1]).any(axis=1).sum()),
                )

        # Advance global cumulative deployment by one year, folding in this
        # ISO's local builds (GW) so the learning curves see them next year.
        local_builds: dict[str, float] = {}
        for zone_adds in renewable_additions.values():
            for fuel, mw in zone_adds.items():
                local_builds[fuel] = local_builds.get(fuel, 0.0) + mw / 1000.0
        for g in fleet:
            if g.online_year == year and g.fuel_type in (
                "gas_cc",
                "nuclear",
                "gas_cc_ccs",
            ):
                local_builds[g.fuel_type] = (
                    local_builds.get(g.fuel_type, 0.0) + g.pmax_mw / 1000.0
                )
        # Attribute new storage builds to each tech's own learning curve
        # (li-ion durations share the "li_ion" curve; iron-air / flow / CAES
        # each have their own) so non-li-ion durations actually learn.
        for u in storage_units:
            if u.unit_id in prior_storage_ids:
                continue
            ref_key = "li_ion" if "li_ion" in u.tech_name else u.tech_name
            local_builds[ref_key] = (
                local_builds.get(ref_key, 0.0) + u.power_cap_mw / 1000.0
            )
        cumulative.advance_year(local_builds)

        # Assemble this year's LP-ready dispatch fleet from the persistent
        # ``fleet``: coal (and optionally gas) take-or-pay tranching --
        # CAMPD per-plant fuel fractions when ``campd_bins`` is active, else
        # the legacy split_coal_tranches/split_gas_tranches -- plus
        # energy-limited hydro and the CAMPD plant-specific emission-rate
        # overrides. dispatch_fleet is transient; the persistent ``fleet``
        # (un-split, no hydro) carries to next year.
        dispatch_fleet, fuel_fracs, hydro_gen_idx, hydro_monthly_energy = (
            build_dispatch_fleet(
                fleet, campd_bins, import_generators, iso, year, zone_names, config
            )
        )
        # Resolve the historic (facility-summed) outage overlay per ISO. The
        # facility overlay is the primary layer only for facility-summed ISOs
        # (ERCOT); ISOs whose unit-level file is the complete CAMPD-derived
        # source (e.g. PJM) disable it so the two layers don't double-count.
        # An explicit config flag still applies for ISOs absent from the
        # registry. The resolved value is threaded into the fleet-array build
        # (the sole consumer) without mutating the run's recorded config, so
        # ERCOT's default (overlay True) passes the original config unchanged.
        outage_overlay = HISTORIC_OUTAGE_OVERLAY_BY_ISO.get(
            iso, config.historic_outage_overlay
        )
        fleet_config = (
            config
            if outage_overlay == config.historic_outage_overlay
            else replace(config, historic_outage_overlay=outage_overlay)
        )
        fleet_arrays = generators_to_fleet_arrays(
            dispatch_fleet,
            zone_names,
            hours=config.hours,
            iso=iso,
            config=fleet_config,
            load_shape=base_demand.sum(axis=0),
            year=year,
        )
        # Replace flat offshore-wind availability with a derived hourly
        # profile; must run after fleet-array build and before dispatch.
        inject_offshore_wind_availability(fleet_arrays, wind_cf, config, iso)

        year_demand = _scale_demand(base_demand, config, year)
        peak_demand = float(year_demand.sum(axis=0).max())

        # Net-load-indexed reliability-drag min-gen floors (gas-ST boiler +
        # CT_PEAKER simple-cycle), the forecast-path mirror of the calibration
        # script. Each floors a tranche's per-hour min generation by a curve
        # rising with system net-load (load - wind - solar) — the operational
        # proxy for the reserve tightness ERCOT RUC keys off — over which the LP
        # dispatches economically. Both functions modify fleet_arrays.min_gen in
        # place and are no-ops when their flag is off. Net-load uses the same
        # LP-served convention as the calibration path.
        if getattr(config, "gas_st_netload_drag", False) or getattr(
            config, "ct_netload_drag", False
        ):
            net_load = (
                year_demand.sum(axis=0)
                - (solar_cap[:, None] * solar_cf).sum(axis=0)
                - (wind_cap[:, None] * wind_cf).sum(axis=0)
            )
            if getattr(config, "gas_st_netload_drag", False):
                from market_sim.data.fleet import apply_gas_st_netload_drag_floor

                if apply_gas_st_netload_drag_floor(
                    fleet_arrays, dispatch_fleet, net_load, config
                ):
                    logger.info(
                        "%s %d: ST_GAS net-load reliability-drag floor applied "
                        "(frac = clip(%.5f*netGW %+0.4f, 0, %.2f); net-load "
                        "mean %.0f / max %.0f MW)",
                        iso,
                        year,
                        config.gas_st_drag_slope_per_gw,
                        config.gas_st_drag_intercept,
                        config.gas_st_drag_cap,
                        float(net_load.mean()),
                        float(net_load.max()),
                    )
            if getattr(config, "ct_netload_drag", False):
                from market_sim.data.fleet import apply_ct_netload_drag_floor

                if apply_ct_netload_drag_floor(
                    fleet_arrays, dispatch_fleet, net_load, config
                ):
                    logger.info(
                        "%s %d: CT_PEAKER net-load reliability-drag floor "
                        "applied (frac = clip(%.5f*netGW %+0.4f, 0, %.2f) in "
                        "ramp %dh-%dh)",
                        iso,
                        year,
                        config.ct_drag_slope_per_gw,
                        config.ct_drag_intercept,
                        config.ct_drag_cap,
                        config.ct_drag_ramp_start,
                        config.ct_drag_ramp_end,
                    )

        fuel_prices = resolve_fuel_prices(config, fleet_arrays, year)
        # Reprice CAMPD coal bins by plant fuel supply (mine-mouth
        # lignite vs PRB by rail); no-op for the legacy fleet.
        apply_coal_supply_pricing(fuel_prices, dispatch_fleet, config, year)
        carbon_price = resolve_carbon_price(config, year)
        # Full variable cost: fuel + VOM + carbon + NOx + SO2 -- computed
        # even on cached years because next year's economic retirement
        # screen nets it against price (inframarginal margin, not gross
        # revenue). Deliberately excludes the EAC discount (attribute
        # revenue is credited separately in the screen -- using both would
        # double-count) and the take-or-pay tranche discount (sunk fuel is
        # avoidable on a retirement horizon, where contracts lapse).
        mc_cost = assemble_mc(
            fleet_arrays,
            fuel_prices,
            carbon_price,
            config.nox_price,
            so2=(fleet_arrays.so2_rate, config.so2_price),
        )

        if is_cached(iso, cache_key, year):
            result = load_result(iso, cache_key, year)
            logger.info(
                "year %d: cached, skipped (%.3fs)",
                year,
                time.perf_counter() - year_start,
            )
        else:
            wind_mc, solar_mc = compute_dispatch_credits(config, year)
            # Base marginal cost: the full variable cost above, then
            # exogenous EACs, then the coal take-or-pay tranche discount.
            # This is the generators' bid basis — no startup-cost markup.
            mc_base = mc_cost.copy()
            # Exogenous EACs shift the cost vector: per-generator EACs
            # lower per-generator MC, wind/solar EACs lower their dispatch
            # adders, and the storage EAC credits discharge. The EAC is real
            # bidding behavior; it does not stack with the RPS shadow price
            # in capacity economics (each MWh sells one attribute, once).
            apply_eac_to_mc(mc_base, fleet_arrays, config)
            # Coal tranche 1 bids at VOM only (its fuel is sunk under the
            # take-or-pay contract); higher tranches pass through more fuel.
            apply_coal_tranches(
                mc_base, dispatch_fleet, fleet_arrays, fuel_fracs, fuel_prices
            )
            if interchange_spec.use_reference_price:
                from market_sim.model.transmission import (
                    inject_reference_price_firm_export,
                    inject_reference_price_mc,
                )

                if inject_reference_price_mc(
                    fleet_arrays, mc_base, iso, year, config.gas_price_path
                ):
                    logger.info(
                        "%s %d: reference-price interface — %d neighbor seams "
                        "priced from gas x heat-rate x load-shape "
                        "(hurdle in $/MWh)",
                        iso,
                        year,
                        len(INTERFACE_NEIGHBORS.get(iso, [])),
                    )
                if inject_reference_price_firm_export(fleet_arrays, iso, year):
                    logger.info(
                        "%s %d: firm scheduled-export floor applied "
                        "(must-flow seam base)",
                        iso,
                        year,
                    )
            if interchange_spec.firm_imports:
                from market_sim.model.transmission import inject_miso_firm_imports

                if inject_miso_firm_imports(fleet_arrays, iso, year):
                    logger.info(
                        "%s %d: Manitoba firm-hydro import baseload floored "
                        "(must-flow)",
                        iso,
                        year,
                    )
            wind_eac, solar_eac, storage_eac = compute_eac_dispatch_credits(config)
            wind_mc -= wind_eac
            solar_mc -= solar_eac
            if getattr(config, "negative_renewable_offers", False):
                from market_sim.policy.eac import apply_negative_renewable_offer_floor

                wind_mc, solar_mc = apply_negative_renewable_offer_floor(
                    wind_mc, solar_mc, config
                )
            import_node_recon = None
            if (
                interchange_spec.monthly_reconciliation is not None
                and import_generators
            ):
                from market_sim.model.transmission import (
                    build_import_node_reconciliation,
                )

                import_node_recon = build_import_node_reconciliation(
                    fleet_arrays,
                    iso,
                    year,
                    mode="forecast",
                    forward_net_import_twh=getattr(
                        config, "nyiso_forward_net_import_twh", None
                    ),
                    system_demand=year_demand,
                )
                if import_node_recon is not None:
                    node_idx, recon_lo, recon_hi = import_node_recon
                    logger.info(
                        "%s %d: priced import node reconciled to the neighbor's "
                        "forecast net position — %d node rows, annual band "
                        "[%.2f, %.2f] TWh",
                        iso,
                        year,
                        int(node_idx.size),
                        recon_lo.sum() / 1e6,
                        recon_hi.sum() / 1e6,
                    )
            # The RPS is enforced as an LP constraint when enabled; its dual
            # is the RPS shadow price returned in the dispatch result.
            rps_target = None
            if config.rps_enabled:
                rps_target = get_rps_target(iso, year)
            # CAISO solar deliverability derate (Lever D): reduce the solar CF
            # ceiling by the forward solar-penetration signal so the LP sees
            # the local-network congestion the reduced 3-zone topology misses.
            # When caiso_solar_endogenous_spill is on, the CF derate is SKIPPED:
            # the LP gets the full solar potential and curtails endogenously
            # (solar becomes marginal in oversupply, crashing the dual to
            # solar_mc instead of pinning at gas MC).
            year_solar_cf = solar_cf
            _endogenous_spill = getattr(config, "caiso_solar_endogenous_spill", False)
            if (
                iso == "CAISO"
                and getattr(config, "caiso_solar_deliverability", False)
                and not _endogenous_spill
            ):
                from market_sim.model.transmission import (
                    caiso_solar_deliverability_derate,
                )

                _sol_derate = caiso_solar_deliverability_derate(
                    config.weather_year,
                    solar_cf.shape[1],
                    float(getattr(config, "caiso_solar_deliverability_k", 0.15)),
                    float(getattr(config, "caiso_solar_deliverability_floor", 0.50)),
                )
                if _sol_derate is not None:
                    year_solar_cf = solar_cf * _sol_derate[None, :]
                    hod = np.arange(len(_sol_derate)) % 24
                    mid = (hod >= 9) & (hod <= 15)
                    logger.info(
                        "CAISO %d: solar deliverability derate (Lever D) — "
                        "midday mean %.3f (≈ %.1f%% curtailment headroom)",
                        year,
                        float(np.mean(_sol_derate[mid])),
                        100.0 * (1.0 - float(np.mean(_sol_derate[mid]))),
                    )
            elif iso == "CAISO" and _endogenous_spill:
                logger.info(
                    "CAISO %d: endogenous solar spill — full solar potential "
                    "passed to LP (no pre-LP CF derate); solar sets the midday "
                    "dual when curtailed",
                    year,
                )
            dispatch_kwargs = dict(
                wind_cf=wind_cf,
                wind_cap=wind_cap,
                solar_cf=year_solar_cf,
                solar_cap=solar_cap,
                # Load-shed penalty = the ISO's own energy bid cap, not the
                # ERCOT-flavored ScenarioConfig default ($5,000). Each ISOConfig
                # carries its real cap (NYISO/CAISO/MISO/PJM $2,000 per FERC
                # Order 831; ERCOT $5,000), so scarcity hours price at the cap
                # the market actually clears against instead of a uniform $5k.
                voll=iso_config.voll,
                incidence=incidence,
                ttc=ttc,
                interface_groups=interface_groups or None,
                # One-way links (MISO's RDT directional pair) floor their flow
                # at 0; all-True for every other ISO (byte-identical bounds).
                link_bidirectional=get_link_bidirectional_array(iso_config.links),
                storage_power_cap=storage.power_cap,
                storage_energy_cap=storage.energy_cap,
                storage_zone_idx=storage.zone_idx,
                eta_chg=storage.eta_chg,
                eta_dis=storage.eta_dis,
                wind_mc=wind_mc,
                solar_mc=solar_mc,
                storage_discharge_eac=storage_eac,
                storage_discharge_cost=storage.vom,
                rps_target=rps_target,
                # Bound storage foresight to within-day arbitrage when the
                # config asks for it (methodology spec §1.3); previously
                # only the backcast script honored this flag.
                storage_daily_cycle_hours=(
                    24 if config.storage_daily_cycling else None
                ),
                # Conventional-hydro monthly energy budget: constrains each
                # hydro plant's monthly generation to its (climatology) budget
                # while letting the LP choose when within the month to generate.
                # Both None (the default) when the ISO has no hydro plants.
                hydro_gen_idx=hydro_gen_idx,
                hydro_monthly_energy=hydro_monthly_energy,
                T=config.hours,
            )
            # Priced import-node monthly net-interchange band (NYISO forecast
            # reconciliation, built above). Part of the LP feasible region (same
            # for P0/P1), so it warm-starts cleanly. No keys (identical LP)
            # unless the reconciliation was built above.
            if import_node_recon is not None:
                node_idx, recon_lo, recon_hi = import_node_recon
                dispatch_kwargs.update(
                    import_node_gen_idx=node_idx,
                    import_node_monthly_lo=recon_lo,
                    import_node_monthly_hi=recon_hi,
                )
            # Emissions mass-cap rows (policy constraint path, gated). When
            # mass_cap_enabled and a power-sector CO2 budget is configured for
            # the ISO's program/year, bound in-region fossil emissions; each
            # cap's per-generator coefficient is m_zone[zone_idx]·emission_rate.
            # Default off → no specs → identical LP. The row dual is surfaced as
            # DispatchResult.co2_cap_price (a power-sector, no-bank scenario
            # allowance price — plan §2/§8, not the RGGI/CARB market price).
            mass_caps = get_active_policy_constraints(config, year)
            if mass_caps:
                cap_coeffs = np.vstack(
                    [
                        spec.membership[fleet_arrays.zone_idx]
                        * fleet_arrays.emission_rate
                        for spec in mass_caps
                    ]
                )
                dispatch_kwargs.update(
                    mass_cap_coeffs=cap_coeffs,
                    mass_cap_rhs=np.array(
                        [spec.cap_tons for spec in mass_caps], dtype=float
                    ),
                    mass_cap_labels=[spec.label for spec in mass_caps],
                )
            # Plant-group hourly ramp envelopes (config.ramp_limits, GATED
            # default off): CAMPD-measured trajectory bounds per plant group
            # per hour transition. Mirrors the run_calibration.py hook so the
            # forecast and backcast paths share the mechanism (forecast
            # parity, design doc §4). No-op (identical LP) when off or when
            # the ISO has no committed envelope artifact.
            if getattr(config, "ramp_limits", False):
                from market_sim.data.fleet import build_ramp_groups

                ramp_groups = build_ramp_groups(fleet_arrays, iso)
                if ramp_groups is not None:
                    r_gen_idx, r_group_col, r_up, r_dn = ramp_groups
                    dispatch_kwargs.update(
                        ramp_gen_idx=r_gen_idx,
                        ramp_group_col=r_group_col,
                        ramp_up_mw=r_up,
                        ramp_dn_mw=r_dn,
                    )
                    logger.info(
                        "%s %d: ramp envelopes on %d plant groups (%d member tranches)",
                        iso,
                        year,
                        r_up.size,
                        r_gen_idx.size,
                    )
            # Local-capacity (LCR-area) minimum-generation rows
            # (config.local_capacity_constraints, GATED default off): the
            # published-study load-pocket relaxation (design doc §3). Same
            # forecast-parity mirror of the run_calibration.py hook; the RHS
            # scales with this year's zonal load shape, so the mechanism
            # regenerates forward natively. No-op when off or when the ISO
            # has no covered areas / membership crosswalk.
            if getattr(config, "local_capacity_constraints", False):
                from market_sim.data.local_capacity import (
                    build_local_capacity_specs,
                )

                lcr_specs, _lcr_meta = build_local_capacity_specs(
                    iso,
                    year,
                    fleet_arrays.plant_code,
                    fleet_arrays.pmax,
                    fleet_arrays.availability,
                    zone_names,
                    year_demand,
                    storage.zone_idx,
                    storage.power_cap,
                )
                if lcr_specs:
                    dispatch_kwargs.update(local_capacity_specs=lcr_specs)
            # Energy + operating-reserve co-optimization (multi-ISO, gated):
            # the ISO's reserve demand curve enters the LP as reserve balance
            # rows so the reserve clearing price lifts the energy LMP
            # endogenously. Config-driven: see reserve_config.py.
            if getattr(config, "energy_reserve_coopt", False) and iso != "CAISO":
                from market_sim.config.reserve_config import (
                    build_reserve_dispatch_kwargs,
                    get_reserve_design,
                )

                design = get_reserve_design(
                    config,
                    fleet_arrays,
                    config.hours,
                    zone_names,
                    system_load=year_demand.sum(axis=0),
                    wind_gen=(wind_cap[:, None] * wind_cf).sum(axis=0),
                    solar_gen=(solar_cap[:, None] * year_solar_cf).sum(axis=0),
                    sim_year=year,
                )
                dispatch_kwargs.update(build_reserve_dispatch_kwargs(design))
                if iso == "PJM" and design.supply_cap is not None:
                    elig_1d = (
                        design.eligible[0]
                        if design.eligible.ndim == 2
                        else design.eligible
                    )
                    logger.info(
                        "PJM reserve-supply cap ON: deliverable 10-min ramp, mean cap "
                        "%d MW (vs ~%d MW total eligible headroom)",
                        int(design.supply_cap.mean()),
                        int(
                            (fleet_arrays.pmax[:, None] * fleet_arrays.availability)[
                                elig_1d
                            ]
                            .sum(axis=0)
                            .mean()
                        ),
                    )
                if iso == "PJM" and design.online_gated is not None:
                    logger.info(
                        "PJM reserve online-gating ON: ρ=%.2f", design.online_rho
                    )
                if iso == "PJM" and design.pergen_gen_idx is not None:
                    logger.info(
                        "PJM PER-GEN reserve co-opt ON: %d R columns / %d "
                        "member units (eligible, ramp10>0; Σ ramp10 %.1f GW), "
                        "%d balance families (%s)",
                        int(design.pergen_ramp10.size),
                        int(design.pergen_gen_idx.size),
                        float(design.pergen_ramp10.sum()) / 1e3,
                        len(design.families),
                        ", ".join(f.name for f in design.families),
                    )
            # P0 and P1 solve the *same* LP -- identical constraint matrix and
            # bounds -- and differ only in the objective (P1 = base MC + startup
            # markup). Build the model once and warm-start P1 from P0's optimal
            # basis (changeColsCost in place): this skips the second matrix build
            # and converges in far fewer simplex iterations, the ~5x the
            # calibration path already banks. The LP optimum is basis-
            # independent, so prices and generation are unchanged. Set
            # MARKET_SIM_WARMSTART=0 to fall back to two independent cold solves.
            _warm = os.environ.get("MARKET_SIM_WARMSTART", "1") != "0"
            model = (
                DispatchModel(fleet_arrays, year_demand, **dispatch_kwargs)
                if _warm
                else None
            )
            # P0: solve with base MC to extract per-month run lengths.
            if _warm:
                r0 = model.solve(mc=mc_base)
            else:
                r0 = solve_dispatch(
                    fleet_arrays, year_demand, mc=mc_base, **dispatch_kwargs
                )
            # P1: solve with bid MC = base MC + monthly startup amortization,
            # so clearing prices reflect CC/CT cycling costs.
            markup = compute_monthly_markup(
                dispatch_fleet, fleet_arrays, r0.dispatch, config.hours
            )
            mc_bid = mc_base + markup
            if _warm:
                p1_result = model.solve(mc=mc_bid)
            else:
                p1_result = solve_dispatch(
                    fleet_arrays, year_demand, mc=mc_bid, **dispatch_kwargs
                )
            context = FleetContext.from_arrays(
                fleet_arrays,
                iso_config,
                wind_cf,
                wind_cap,
                year_solar_cf,
                solar_cap,
                storage.energy_cap,
            )
            result = p1_result

            # === LEGACY: P2 Commitment Screen ===
            # P2 (optional): screen CC/CT commitment on P1 clearing prices
            # against base MC, pin coal to its P1 dispatch, and re-solve.
            # Both datasets are kept: the P1 dispatch as year_{year}_p1, the
            # final result (P2 here) as the primary year_{year}. With
            # commitment disabled only P1 is solved and it is the primary.
            # AS-aware commitment (ERCOT, gated): value a unit's AS revenue when
            # screening commitment so the units a tight month keeps online FOR AS
            # stay committed and the P2 co-opt headroom reflects realistic online
            # capacity (the phantom-headroom fix, Finding 1 / G1). Triggers a P2
            # pass even with commitment_enabled off; ERCOT + multi-product co-opt
            # only.
            as_aware = (
                getattr(config, "ercot_as_aware_commitment", False)
                and iso == "ERCOT"
                and getattr(config, "energy_reserve_coopt", False)
            )
            caiso_ra = getattr(config, "caiso_ra_mustoffer", False) and iso == "CAISO"
            if config.commitment_enabled or as_aware or caiso_ra:
                save_result(
                    p1_result,
                    config,
                    iso,
                    year,
                    context=context,
                    pass_label="p1",
                )
                # AS revenue estimate from the model's OWN P1 reserve dual
                # (never the measured MCPC) — None for the energy-only screen.
                as_value = (
                    ercot_as_aware_unit_value(
                        fleet_arrays,
                        p1_result.dispatch,
                        p1_result.reserve_price_by_family,
                        config.hours,
                    )
                    if as_aware
                    else None
                )
                committed = compute_commitment(
                    p1_result.prices,
                    mc_base,
                    dispatch_fleet,
                    fleet_arrays,
                    config,
                    storage_charge=p1_result.storage_charge,
                    storage_discharge=p1_result.storage_discharge,
                    storage_zone_idx=storage.zone_idx,
                    demand=year_demand,
                    as_value=as_value,
                )
                # NYISO path B (commitment-gated synchronised reserve): the
                # energy-economic screen decommits NYC quick-start peakers that
                # aren't needed for energy, so they can no longer back the
                # locational spinning family and the >$300 tail never fires.
                # Force-commit the cheapest-startup NYC quick-start units until
                # their committed capacity covers the MEASURED NYC spinning
                # requirement (NYISO_SPIN_FRACTION x NYC 10-min total = 250 MW),
                # so the P2 class-1 NYC headroom row equals Sum_online(pmax - P)
                # and the family binds endogenously in genuinely tight hours
                # (docs/handoffs/nyiso-downstate-reserve-incidence-2026-06.md,
                # "Path B"). NYISO-only behind the default-off flag.
                if (
                    getattr(config, "nyiso_synchronised_reserve", False)
                    and iso == "NYISO"
                ):
                    spin_eligible = nyiso_spin_eligible(fleet_arrays, zone_names)
                    committed = reserve_adequacy_commit(
                        committed,
                        fleet_arrays,
                        dispatch_fleet,
                        spin_eligible,
                        requirement_mw=nyiso_spin_requirement_mw(config),
                        headroom_frac=config.nyiso_spin_headroom_frac,
                    )
                # AS-adequacy floor + commitment-state-aware reserve headroom
                # (ERCOT AS-aware only) — mirror of the calibration path
                # (scripts/run_calibration._commitment_pass): re-commit the
                # cheapest eligible units until committed online headroom
                # covers the procured AS, then re-scope the P2 headroom rows
                # (online CTs join the fast pool via P2 availability; offline
                # quick-start capacity backs Non-Spin only via the extra cap).
                dispatch_kwargs_p2 = dispatch_kwargs
                if as_aware and "reserve_headroom_eligible" in dispatch_kwargs:
                    from market_sim.config.reserve_config import (
                        ercot_commitment_headroom_overrides,
                    )

                    dk = dispatch_kwargs
                    req_fam = np.atleast_2d(
                        np.asarray(dk["reserve_requirement"], dtype=float)
                    )
                    hp = np.atleast_2d(
                        np.asarray(dk["reserve_headroom_products"], dtype=bool)
                    )
                    fam_class = np.asarray(
                        dk.get("reserve_balance_class", np.arange(req_fam.shape[0])),
                        dtype=int,
                    )
                    req_by_class = np.zeros(
                        (hp.shape[1], req_fam.shape[1]), dtype=float
                    )
                    # All-class families (reserve_class -1, the ERCOT lumped
                    # ORDC total-reserve curve) are a demand on the aggregate,
                    # not one product's procurement — exclude them from the
                    # per-product adequacy requirement (a -1 would otherwise
                    # silently index the last product).
                    prod_fam = fam_class >= 0
                    np.add.at(req_by_class, fam_class[prod_fam], req_fam[prod_fam])
                    committed = as_adequacy_commit(
                        committed,
                        fleet_arrays,
                        dispatch_fleet,
                        dk["reserve_headroom_eligible"],
                        dk["reserve_headroom_products"],
                        req_by_class,
                        p1_result.dispatch,
                        headroom_frac=float(
                            getattr(config, "ercot_as_adequacy_frac", 1.0)
                        ),
                    )
                    dispatch_kwargs_p2 = {
                        **dk,
                        **ercot_commitment_headroom_overrides(
                            fleet_arrays, committed, dk["reserve_headroom_eligible"]
                        ),
                    }
                fleet_arrays_p2 = apply_commitment_with_coal_pin(
                    fleet_arrays,
                    committed,
                    p1_result.dispatch,
                    dispatch_fleet,
                    screen_coal=config.commitment_screen_coal,
                    couple_peak=as_aware,
                )
                result = solve_dispatch(
                    fleet_arrays_p2, year_demand, mc=mc_bid, **dispatch_kwargs_p2
                )
            # === END LEGACY: P2 Commitment Screen ===
            save_result(result, config, iso, year, context=context)
            logger.info(
                "year %d: solved and cached (%.3fs)",
                year,
                time.perf_counter() - year_start,
            )

        # CHP must-run post-processing: non-coal must-run capacity is
        # removed from the LP (the CHP units serve host industrial steam,
        # not the grid), so add its generation and emissions back here
        # for asset-level emissions trajectories.
        if campd_bins is not None:
            # EM-7 (plan §5 R5): book BTM CO2 at the plant's measured v2 rate
            # (matching its grid tranches) and size the fallback with a measured
            # CHP class CF instead of the flat must_run_cf.
            mr_rates, mr_class_cf = _chp_measured_co2_inputs(config, iso, year)
            mr = compute_must_run_emissions(
                campd_bins,
                year,
                config.must_run_cf,
                measured_rate_by_plant=mr_rates,
                class_cf_by_group=mr_class_cf,
            )
            if not mr.empty:
                logger.info(
                    "year %d: CHP must-run post-processing -- %d bins, "
                    "%.0f GWh, %.0f kt CO2 (asset-level, outside the LP)",
                    year,
                    len(mr),
                    mr["mr_gen_mwh"].sum() / 1000.0,
                    mr["mr_co2_tons"].sum() / 1000.0,
                )

        # ORDC scarcity overlay (post-solve; ERCOT's energy-only design,
        # generalized to any ISO via scarcity_price_overlay): the published
        # reserve-scarcity adder is computed from this year's solved
        # headroom and added to the prices next year's capacity economics
        # see — economic retirement, new entry and CCS retrofit screens
        # (capacity.evolve_fleet) — so peakers and storage earn scarcity
        # revenue instead of bare LP duals. Raw duals structurally carry no
        # scarcity rent in a perfect-foresight LP with zero unserved energy,
        # which over-retires dispatchables and under-builds. Dispatch,
        # volumes, emissions and persisted results are untouched.
        # scarcity_price_overlay defaults True for ERCOT (energy-only; see
        # ISOConfig.default_scenario_overrides) and False elsewhere —
        # capacity-market ISOs recover fixed cost through capacity-market
        # revenue (capacity_revenue_per_mw_yr) instead, no adder there.
        # When co-optimization is on the energy LMP (result.prices) already
        # carries the scarcity lift via the reserve clearing price, so the
        # post-solve adder is skipped to avoid double-counting.
        econ_prices = result.prices
        if (
            config.scarcity_pricing_enabled
            and config.scarcity_price_overlay
            and not getattr(config, "energy_reserve_coopt", False)
        ):
            ren_headroom = (
                wind_cf * np.asarray(wind_cap)[:, None]
                + solar_cf * np.asarray(solar_cap)[:, None]
                - result.wind_dispatched
                - result.solar_dispatched
            ).sum(axis=0)
            # Online/offline reserve split (results.scarcity): only responsive
            # capacity backs the ORDC curve — a cold slow-start unit the
            # perfect-foresight LP left idle is NOT real-time reserve. This is
            # the market-design-grounded replacement for the fitted flat RTORDPA
            # offset (the offset stays addable, default 0, as an explicit probe;
            # NOT netting the AS plan — ERCOT's RTOLCAP already counts online
            # AS-held capacity as reserve, so subtracting it double-counts).
            r_online, r_offline = reserve_headroom(
                fleet_arrays,
                result.dispatch,
                storage.power_cap,
                result.storage_charge,
                result.storage_discharge,
                effective_reliability_deployment_mw(year, config),
                renewable_headroom=ren_headroom,
            )
            d_tot = year_demand.sum(axis=0)
            lam = np.where(
                d_tot > 0,
                (result.prices * year_demand).sum(axis=0)
                / np.where(d_tot > 0, d_tot, 1.0),
                result.prices.mean(axis=0),
            )
            adder = scarcity_prices(
                config, year, r_online + r_offline, lam, reserves_online_mw=r_online
            )["scarcity_adder"]
            econ_prices = result.prices + adder[None, :]
            logger.info(
                "year %d: ORDC scarcity adder for capacity economics — "
                "mean $%.2f/MWh, >$10 in %d h, max $%.0f",
                year,
                float(adder.mean()),
                int((adder > 10).sum()),
                float(adder.max()),
            )

        prior_results = {
            "fleet_arrays": fleet_arrays,
            "dispatch_result": result,
            "prices": econ_prices,
            "peak_demand": peak_demand,
            "planned_additions": planned_additions,
            "mc_cost": mc_cost,
            "rps_shadow_price": result.rps_shadow_price or 0.0,
            "retrofit_log": retrofit_log,
            # AS-eligible (storage) fleet power for the AS-revenue saturation
            # in next year's capacity screens (capacity.evolve_fleet).
            "storage_power_mw": float(sum(storage.power_cap))
            if storage.power_cap.ndim == 1
            else float(storage.power_cap.sum(axis=0).max()),
            # Storage AS revenue DERIVED from this year's co-opt reserve duals
            # (the endogenous analogue of the exogenous as_revenue rate) — fed
            # to next year's storage entry screen so exactly one mechanism
            # prices storage AS under ercot_storage_as_endogenous (rule 19).
            # 0.0 when the co-opt did not price reserve this year.
            "storage_as_revenue_per_mw_yr": realized_storage_as_revenue_per_mw_yr(
                result.reserve_price_by_family,
                result.reserve_dispatch,
                result.storage_charge,
                result.storage_discharge,
                storage.power_cap,
                storage.zone_idx,
                len(zone_names),
            )
            if getattr(config, "ercot_storage_as_endogenous", False)
            else 0.0,
            # Per-fuel thermal AS revenue DERIVED from this year's co-opt reserve
            # duals (the endogenous analogue of the exogenous flat as_revenue rate)
            # — fed to next year's retirement/new-entry screens so exactly one
            # mechanism prices thermal AS under ercot_thermal_as_endogenous
            # (rule 19). Empty dict when the co-opt did not price reserve this year.
            "thermal_as_revenue_per_mw_yr": (
                realized_thermal_as_revenue_per_mw_yr_by_fuel(
                    fleet_arrays,
                    result.dispatch,
                    result.reserve_price_by_family,
                    config.hours,
                )
                if (
                    getattr(config, "ercot_thermal_as_endogenous", False)
                    and iso == "ERCOT"
                )
                else None
            ),
            # Renewable-pool and accredited-storage-firm capacity for next
            # year's reserve-margin adequacy backstop.
            "wind_cap_mw": float(np.sum(wind_cap)),
            "solar_cap_mw": float(np.sum(solar_cap)),
            "storage_firm_mw": float(
                sum(
                    u.power_cap_mw
                    * _elcc_for_duration(
                        u.energy_cap_mwh / u.power_cap_mw if u.power_cap_mw > 0 else 0.0
                    )
                    for u in storage_units
                )
            ),
        }

    logger.info("run_scenario_iso done: iso=%s cache_key=%s", iso, cache_key)
    return cache_key


def _run_pair(pair: tuple[ScenarioConfig, str]) -> str:
    """Run one ``(config, iso)`` pair; the worker entry point for sweeps."""
    config, iso = pair
    return run_scenario_iso(config, iso)


def run_sweep(sweep_def: SweepDefinition, workers: int | None = None) -> list[str]:
    """Expand a sweep into configs and run every ``(config, iso)`` pair.

    Args:
        sweep_def: The sweep definition to expand.
        workers: Number of worker processes. Defaults to ``cpu_count - 1``.
            With a single worker the pairs run in-process (no subprocess
            overhead).

    Returns:
        The list of cache keys, one per ``(config, iso)`` pair.
    """
    configs = sweep_def.generate()
    pairs = [(config, config.iso) for config in configs]

    if workers is None:
        workers = max(1, cpu_count() - 1)

    logger.info(
        "run_sweep start: %d (config, iso) pairs across %d worker(s)",
        len(pairs),
        workers,
    )

    if workers == 1:
        return [_run_pair(pair) for pair in pairs]

    with ProcessPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(_run_pair, pairs))


def _build_parser() -> argparse.ArgumentParser:
    """Return the ``market-sim`` argument parser with its subcommands."""
    parser = argparse.ArgumentParser(
        prog="market-sim",
        description="Electricity market dispatch and policy simulator.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a single scenario.")
    run_parser.add_argument(
        "--config", required=True, help="Path to a scenario YAML file."
    )
    run_parser.add_argument(
        "--iso",
        default=None,
        help="ISO to run; defaults to the config's own ISO.",
    )

    sweep_parser = subparsers.add_parser("sweep", help="Run a parameter sweep.")
    sweep_parser.add_argument(
        "--sweep", required=True, help="Path to a sweep YAML file."
    )
    sweep_parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Worker processes; defaults to cpu_count - 1.",
    )

    ensemble_parser = subparsers.add_parser(
        "ensemble",
        help="Run a forecast over multiple weather years and report the distribution.",
    )
    ensemble_parser.add_argument(
        "--config", required=True, help="Path to a forecast scenario YAML file."
    )
    ensemble_parser.add_argument(
        "--iso",
        default=None,
        help="ISO to run; defaults to the config's own ISO.",
    )
    ensemble_parser.add_argument(
        "--weather-years",
        type=int,
        nargs="+",
        default=None,
        help="Weather years to draw over; defaults to WEATHER_YEAR_POOL.",
    )
    ensemble_parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Worker processes; defaults to cpu_count - 1.",
    )
    ensemble_parser.add_argument(
        "--out",
        default=None,
        help="Path to write the ensemble distribution JSON; skipped if omitted.",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``market-sim`` console script.

    Args:
        argv: Argument vector to parse. Defaults to ``sys.argv[1:]``.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _build_parser().parse_args(argv)

    if args.command == "run":
        config = ScenarioConfig.from_yaml(args.config)
        iso = args.iso or config.iso
        run_scenario_iso(config, iso)
    elif args.command == "sweep":
        run_sweep(SweepDefinition.from_yaml(args.sweep), args.workers)
    elif args.command == "ensemble":
        from market_sim.ensemble import export_ensemble_json, run_weather_ensemble

        config = ScenarioConfig.from_yaml(args.config)
        iso = args.iso or config.iso
        members = run_weather_ensemble(config, iso, args.weather_years, args.workers)
        if args.out:
            export_ensemble_json(members, iso, args.out)


if __name__ == "__main__":
    main()
