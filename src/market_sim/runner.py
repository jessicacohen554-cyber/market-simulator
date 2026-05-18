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
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from multiprocessing import cpu_count

import numpy as np

from market_sim.config.constants import (
    DEMAND_GROWTH_RATES,
    DEMAND_GROWTH_TRANSITION_YEAR,
    END_YEAR,
    START_YEAR,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from market_sim.data.eia_loader import load_demand
from market_sim.data.fleet import (
    aggregate_fleet,
    apply_coal_sunk_cost,
    assemble_mc,
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)
from market_sim.data.cycling import apply_cycling_adders
from market_sim.data.fuel import resolve_annual_gas_price, resolve_fuel_prices
from market_sim.data.renewables import (
    inject_offshore_wind_availability,
    load_renewable_profiles,
)
from market_sim.model.capacity import CumulativeDeployment, evolve_fleet
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.storage import (
    apply_storage_new_entry,
    build_default_storage,
    storage_units_to_arrays,
)
from market_sim.model.transmission import (
    build_incidence_matrix,
    build_wecc_import_generators,
    get_ttc_array,
)
from market_sim.policy.carbon import resolve_carbon_price
from market_sim.policy.ira import compute_dispatch_credits
from market_sim.policy.eac import apply_eac_to_mc, compute_eac_dispatch_credits
from market_sim.policy.rps import get_rps_target
from market_sim.results.cache import is_cached, load_result, save_result
from market_sim.results.outputs import FleetContext

logger = logging.getLogger(__name__)


def _get_growth_rate(config: ScenarioConfig, year: int) -> float:
    """Return the demand growth rate for a given year."""
    iso_rates = DEMAND_GROWTH_RATES.get(config.iso, {})
    path_rates = iso_rates.get(config.demand_growth_path, None)
    if path_rates is None or not isinstance(path_rates, dict):
        return config.demand_growth_rate
    if year <= DEMAND_GROWTH_TRANSITION_YEAR:
        return path_rates["near"]
    return path_rates["long"]


def _scale_demand(
    base_demand: np.ndarray, config: ScenarioConfig, year: int
) -> np.ndarray:
    """Scale base-year demand to the target year using compound growth."""
    factor = 1.0
    for y in range(START_YEAR, year):
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
    cache_key = config.cache_key()

    logger.info(
        "run_scenario_iso start: iso=%s cache_key=%s config=%s",
        iso, cache_key, asdict(config),
    )

    iso_config = get_iso_config(iso)
    zone_names = iso_config.zone_names

    # Weather-year inputs are fixed across the run; load them once. The CF
    # profiles (wind_cf, solar_cf) are resource-driven and stay fixed, but
    # wind_cap and solar_cap are mutable: capacity evolution grows them each
    # year as new renewables are built.
    base_demand = load_demand(
        iso, config.weather_year, iso_config,
        td_loss_factor=config.td_loss_factor,
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        iso, config.weather_year, iso_config, config
    )
    # Trim profiles to config.hours when running a sub-annual horizon.
    if config.hours < base_demand.shape[1]:
        base_demand = base_demand[:, :config.hours]
        wind_cf = wind_cf[:, :config.hours]
        solar_cf = solar_cf[:, :config.hours]
    incidence = build_incidence_matrix(iso_config.links, zone_names)
    ttc = get_ttc_array(iso_config.links)
    # CAISO models the rest of the WECC as import pseudo-generators that
    # ride along with the dispatch fleet but never evolve.
    wecc_generators = build_wecc_import_generators() if iso == "CAISO" else []

    fleet = None
    loss_tracker: dict[str, int] = {}
    prior_results = None

    # Storage is managed across years like the generation fleet: the base
    # year starts from the deployment-pace fleet, later years grow via the
    # economic new-entry screen.
    storage_units = build_default_storage(iso_config, config)

    # Global cumulative deployment drives the Wright's-Law learning curves.
    # It starts from the reference-year installed base and advances one year
    # of worldwide deployment (plus this ISO's local builds) every year.
    cumulative = CumulativeDeployment.initial()

    for year in range(START_YEAR, END_YEAR + 1):
        year_start = time.perf_counter()
        renewable_additions: dict[str, dict[str, float]] = {}
        retrofit_log: list[dict] = []

        if fleet is None:
            # First year: load the base fleet from EIA-860 and collapse
            # individual units into efficiency-bin representatives before
            # they ever reach the LP -- the dominant solve-time win.
            fleet = aggregate_fleet(
                load_fleet_from_csv(iso, iso_config),
                n_bins=config.heat_rate_bin_count,
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
                fleet, prior_results, year, config, loss_tracker,
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
                    year, len(retrofit_log), avg_savings,
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
        prior_storage_mw = sum(u.power_cap_mw for u in storage_units)
        if prior_results is not None:
            storage_units = apply_storage_new_entry(
                storage_units, prior_results["prices"], year, config, iso,
                cumulative=cumulative,
            )
        storage = storage_units_to_arrays(storage_units, zone_names)

        # Advance global cumulative deployment by one year, folding in this
        # ISO's local builds (GW) so the learning curves see them next year.
        local_builds: dict[str, float] = {}
        for zone_adds in renewable_additions.values():
            for fuel, mw in zone_adds.items():
                local_builds[fuel] = local_builds.get(fuel, 0.0) + mw / 1000.0
        for g in fleet:
            if g.online_year == year and g.fuel_type in (
                "gas_cc", "nuclear", "gas_cc_ccs"
            ):
                local_builds[g.fuel_type] = (
                    local_builds.get(g.fuel_type, 0.0) + g.pmax_mw / 1000.0
                )
        new_storage_mw = (
            sum(u.power_cap_mw for u in storage_units) - prior_storage_mw
        )
        if new_storage_mw > 0:
            local_builds["li_ion"] = (
                local_builds.get("li_ion", 0.0) + new_storage_mw / 1000.0
            )
        cumulative.advance_year(local_builds)

        dispatch_fleet = fleet + wecc_generators
        fleet_arrays = generators_to_fleet_arrays(
            dispatch_fleet, zone_names, hours=config.hours, iso=iso,
            config=config,
        )
        # Replace flat offshore-wind availability with a derived hourly
        # profile; must run after fleet-array build and before dispatch.
        inject_offshore_wind_availability(fleet_arrays, wind_cf, config, iso)

        year_demand = _scale_demand(base_demand, config, year)
        peak_demand = float(year_demand.sum(axis=0).max())

        if is_cached(iso, cache_key, year):
            result = load_result(iso, cache_key, year)
            logger.info(
                "year %d: cached, skipped (%.3fs)",
                year, time.perf_counter() - year_start,
            )
        else:
            fuel_prices = resolve_fuel_prices(config, fleet_arrays, year)
            carbon_price = resolve_carbon_price(config, year)
            wind_mc, solar_mc = compute_dispatch_credits(config, year)
            mc = assemble_mc(
                fleet_arrays, fuel_prices, carbon_price, config.nox_price
            )
            # Fold per-bin thermal cycling cost adders into the merit order
            # before any EAC adjustment (both are additive $/MWh shifts).
            mc = apply_cycling_adders(mc, dispatch_fleet, fleet_arrays, config)
            # Exogenous EACs shift the cost vector: per-generator EACs
            # lower per-generator MC, wind/solar EACs lower their dispatch
            # adders, and the storage EAC credits discharge. The EAC is real
            # bidding behavior; it does not stack with the RPS shadow price
            # in capacity economics (each MWh sells one attribute, once).
            apply_eac_to_mc(mc, fleet_arrays, config)
            # Coal bids below full fuel cost: take-or-pay fuel contracts
            # make the contracted fuel sunk regardless of dispatch.
            mc = apply_coal_sunk_cost(
                mc, fleet_arrays, dispatch_fleet, fuel_prices, config
            )
            wind_eac, solar_eac, storage_eac = compute_eac_dispatch_credits(config)
            wind_mc -= wind_eac
            solar_mc -= solar_eac
            # The RPS is enforced as an LP constraint when enabled; its dual
            # is the RPS shadow price returned in the dispatch result.
            rps_target = None
            if config.rps_enabled:
                rps_target = get_rps_target(iso, year)
            dispatch_kwargs = dict(
                wind_cf=wind_cf,
                wind_cap=wind_cap,
                solar_cf=solar_cf,
                solar_cap=solar_cap,
                mc=mc,
                voll=config.voll,
                incidence=incidence,
                ttc=ttc,
                storage_power_cap=storage.power_cap,
                storage_energy_cap=storage.energy_cap,
                storage_zone_idx=storage.zone_idx,
                eta_chg=storage.eta_chg,
                eta_dis=storage.eta_dis,
                wind_mc=wind_mc,
                solar_mc=solar_mc,
                storage_discharge_eac=storage_eac,
                rps_target=rps_target,
                T=config.hours,
            )
            result = solve_dispatch(fleet_arrays, year_demand, **dispatch_kwargs)

            # Optional 2-pass commitment: screen Pass-1 prices to decommit
            # gas CC hours that cannot cover startup cost, then re-solve so
            # CTs and coal fill the gaps. Pass 2 replaces Pass 1 for caching.
            if config.commitment_enabled:
                from market_sim.model.commitment import (
                    apply_commitment,
                    compute_commitment,
                )

                committed = compute_commitment(
                    result.prices,
                    mc,
                    dispatch_fleet,
                    fleet_arrays,
                    config,
                    demand=year_demand,
                    wind_dispatched=result.wind_dispatched,
                    solar_dispatched=result.solar_dispatched,
                )
                fleet_arrays_p2 = apply_commitment(
                    fleet_arrays, committed, dispatch_fleet,
                    p1_dispatch=result.dispatch,
                )
                result = solve_dispatch(
                    fleet_arrays_p2, year_demand, **dispatch_kwargs
                )
            context = FleetContext.from_arrays(
                fleet_arrays, iso_config, wind_cf, wind_cap, solar_cf,
                solar_cap, storage.energy_cap,
            )
            save_result(result, config, iso, year, context=context)
            logger.info(
                "year %d: solved and cached (%.3fs)",
                year, time.perf_counter() - year_start,
            )

        prior_results = {
            "fleet_arrays": fleet_arrays,
            "dispatch_result": result,
            "prices": result.prices,
            "peak_demand": peak_demand,
            "planned_additions": [],
            "rps_shadow_price": result.rps_shadow_price or 0.0,
            "retrofit_log": retrofit_log,
        }

    logger.info("run_scenario_iso done: iso=%s cache_key=%s", iso, cache_key)
    return cache_key


def _run_pair(pair: tuple[ScenarioConfig, str]) -> str:
    """Run one ``(config, iso)`` pair; the worker entry point for sweeps."""
    config, iso = pair
    return run_scenario_iso(config, iso)


def run_sweep(
    sweep_def: SweepDefinition, workers: int | None = None
) -> list[str]:
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
        len(pairs), workers,
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
        "--iso", default=None,
        help="ISO to run; defaults to the config's own ISO.",
    )

    sweep_parser = subparsers.add_parser(
        "sweep", help="Run a parameter sweep."
    )
    sweep_parser.add_argument(
        "--sweep", required=True, help="Path to a sweep YAML file."
    )
    sweep_parser.add_argument(
        "--workers", type=int, default=None,
        help="Worker processes; defaults to cpu_count - 1.",
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


if __name__ == "__main__":
    main()
