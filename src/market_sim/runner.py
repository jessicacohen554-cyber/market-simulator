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

from market_sim.config.constants import END_YEAR, START_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from market_sim.data.eia_loader import load_demand
from market_sim.data.fleet import (
    assemble_mc,
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)
from market_sim.data.fuel import resolve_fuel_prices
from market_sim.data.renewables import load_renewable_profiles
from market_sim.model.capacity import evolve_fleet
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.storage import build_default_storage, storage_units_to_arrays
from market_sim.model.transmission import (
    build_incidence_matrix,
    build_wecc_import_generators,
    get_ttc_array,
)
from market_sim.policy.carbon import resolve_carbon_price
from market_sim.policy.ira import compute_dispatch_credits
from market_sim.results.cache import is_cached, load_result, save_result
from market_sim.results.outputs import FleetContext

logger = logging.getLogger(__name__)


def _scale_demand(base_demand: np.ndarray, config: ScenarioConfig, year: int) -> np.ndarray:
    """Scale weather-year demand to a simulation year by demand growth.

    The weather-year shape from EIA-930 is compounded at
    ``config.demand_growth_rate`` for every year past :data:`START_YEAR`.
    """
    growth = (1.0 + config.demand_growth_rate) ** (year - START_YEAR)
    return base_demand * growth


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
    base_demand = load_demand(iso, config.weather_year, iso_config)
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        iso, config.weather_year, iso_config, config
    )
    incidence = build_incidence_matrix(iso_config.links, zone_names)
    ttc = get_ttc_array(iso_config.links)
    storage = storage_units_to_arrays(
        build_default_storage(iso_config, config), zone_names
    )
    # CAISO models the rest of the WECC as import pseudo-generators that
    # ride along with the dispatch fleet but never evolve.
    wecc_generators = build_wecc_import_generators() if iso == "CAISO" else []

    fleet = None
    loss_tracker: dict[str, int] = {}
    prior_results = None

    for year in range(START_YEAR, END_YEAR + 1):
        year_start = time.perf_counter()

        if fleet is None:
            # First year: no EIA-860 vintage yet, so the base fleet falls
            # back to the deterministic synthetic fleet inside the loader.
            fleet = load_fleet_from_csv(iso, iso_config)
        else:
            fleet, loss_tracker, renewable_additions = evolve_fleet(
                fleet, prior_results, year, config, loss_tracker
            )
            # New wind/solar grow the zonal capacity pools that bound the
            # W[z,t] and S[z,t] dispatch variables -- they are not added as
            # flat-availability thermal generators.
            for zone_name, additions in renewable_additions.items():
                z_idx = zone_names.index(zone_name)
                wind_cap[z_idx] += additions.get("wind", 0.0)
                solar_cap[z_idx] += additions.get("solar", 0.0)

        dispatch_fleet = fleet + wecc_generators
        fleet_arrays = generators_to_fleet_arrays(
            dispatch_fleet, zone_names, hours=config.hours
        )

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
            result = solve_dispatch(
                fleet_arrays,
                year_demand,
                wind_cf,
                wind_cap,
                solar_cf,
                solar_cap,
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
                T=config.hours,
            )
            context = FleetContext.from_arrays(
                fleet_arrays, wind_cf, wind_cap, solar_cf, solar_cap,
                storage.energy_cap,
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
