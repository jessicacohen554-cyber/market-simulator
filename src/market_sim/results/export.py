"""Export of cached simulation results to compact frontend JSON.

A cached run is 25 yearly Parquet files of hour-by-hour dispatch; the
frontend only needs annual headline numbers. :func:`export_scenario_json`
loads every year, aggregates each to a small annual summary, and writes one
JSON file well under 2 MB.

The Parquet files store dispatch quantities but not the fleet that produced
them. Fuel-level breakdowns therefore require the per-year fleet, which is
recovered by replaying the deterministic fleet evolution from
:mod:`market_sim.runner` -- given the scenario config the evolution is
reproducible exactly, so no re-solving is needed.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

import numpy as np

from market_sim.config.constants import END_YEAR, START_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia_loader import load_demand
from market_sim.data.fleet import generators_to_fleet_arrays, load_fleet_from_csv
from market_sim.data.renewables import load_renewable_profiles
from market_sim.model.capacity import evolve_fleet
from market_sim.model.storage import build_default_storage, storage_units_to_arrays
from market_sim.model.transmission import build_wecc_import_generators
from market_sim.results import cache
from market_sim.results.emissions import compute_emissions

logger = logging.getLogger(__name__)

# Hard ceiling on a single exported scenario file.
MAX_FILE_BYTES: int = 2 * 1024 * 1024

# MWh -> TWh and MW -> GW conversion divisors.
_MWH_PER_TWH: float = 1e6
_MW_PER_GW: float = 1e3


def compute_curtailment(
    potential: np.ndarray, dispatched: np.ndarray
) -> np.ndarray:
    """Return curtailed energy as available potential minus dispatched output.

    Args:
        potential: Available generation, e.g. ``capacity_factor * capacity``.
        dispatched: Generation actually dispatched, same shape as
            ``potential``.

    Returns:
        Curtailment ``potential - dispatched``, same shape. It is
        non-negative whenever ``dispatched`` honors ``potential`` as an
        upper bound, which the dispatch LP always enforces.
    """
    return np.asarray(potential, dtype=float) - np.asarray(dispatched, dtype=float)


def _summarize_year(
    result,
    dispatch_fleet: list,
    emission_rates: np.ndarray,
    wind_curtail: np.ndarray,
    solar_curtail: np.ndarray,
    wind_cap_mw: float,
    solar_cap_mw: float,
    energy_cap_mwh: float,
) -> dict:
    """Aggregate one year's hourly dispatch into an annual summary dict."""
    dispatch = result.dispatch

    generation_twh: dict[str, float] = {}
    capacity_gw: dict[str, float] = {}
    for g, gen in enumerate(dispatch_fleet):
        fuel = gen.fuel_type
        generation_twh[fuel] = (
            generation_twh.get(fuel, 0.0) + float(dispatch[g].sum()) / _MWH_PER_TWH
        )
        capacity_gw[fuel] = (
            capacity_gw.get(fuel, 0.0) + gen.pmax_mw / _MW_PER_GW
        )

    # Zonal capacity-factor wind and solar are modeled outside the thermal
    # fleet, so fold their dispatched energy and nameplate in separately.
    generation_twh["wind"] = (
        generation_twh.get("wind", 0.0)
        + float(result.wind_dispatched.sum()) / _MWH_PER_TWH
    )
    generation_twh["solar"] = (
        generation_twh.get("solar", 0.0)
        + float(result.solar_dispatched.sum()) / _MWH_PER_TWH
    )
    capacity_gw["wind"] = capacity_gw.get("wind", 0.0) + wind_cap_mw / _MW_PER_GW
    capacity_gw["solar"] = capacity_gw.get("solar", 0.0) + solar_cap_mw / _MW_PER_GW

    emissions_t = float(compute_emissions(dispatch, emission_rates).sum())

    curtailment_twh = (
        float(wind_curtail.sum()) + float(solar_curtail.sum())
    ) / _MWH_PER_TWH

    storage_cycles = 0.0
    if result.storage_discharge is not None and energy_cap_mwh > 0.0:
        storage_cycles = float(result.storage_discharge.sum()) / energy_cap_mwh

    return {
        "generation_twh": {k: round(v, 4) for k, v in generation_twh.items()},
        "emissions_mt": round(emissions_t / 1e6, 4),
        "avg_price": round(float(result.prices.mean()), 2),
        "peak_price": round(float(result.prices.max()), 2),
        "curtailment_twh": round(max(curtailment_twh, 0.0), 4),
        "capacity_gw": {k: round(v, 3) for k, v in capacity_gw.items()},
        "storage_cycles": round(storage_cycles, 2),
    }


def export_scenario_json(cache_key: str, iso: str, output_dir) -> Path:
    """Export one cached scenario to a compact annual-summary JSON file.

    Loads every simulation year's cached Parquet result, aggregates each to
    annual headline numbers, and writes ``{cache_key}.json`` to
    ``output_dir``.

    Args:
        cache_key: Deterministic config hash identifying the cached run.
        iso: ISO identifier, e.g. ``"ERCOT"``.
        output_dir: Directory to write the JSON file into; created if absent.

    Returns:
        The path of the written JSON file.

    Raises:
        FileNotFoundError: When a year's cached Parquet result is missing.
        RuntimeError: When the replayed fleet does not match a cached
            result's generator count, indicating non-reproducible state.
        ValueError: When the written file exceeds :data:`MAX_FILE_BYTES`.
    """
    iso = iso.upper()
    output_dir = Path(output_dir)
    iso_config = get_iso_config(iso)
    zone_names = iso_config.zone_names

    config = ScenarioConfig.from_yaml(
        cache.get_config_path(iso, cache_key, START_YEAR)
    )

    # Weather-year inputs are fixed across the run, mirroring the runner.
    base_demand = load_demand(iso, config.weather_year, iso_config)
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        iso, config.weather_year, iso_config, config
    )
    wind_potential = wind_cf * wind_cap[:, None]
    solar_potential = solar_cf * solar_cap[:, None]
    wind_cap_mw = float(wind_cap.sum())
    solar_cap_mw = float(solar_cap.sum())

    storage = storage_units_to_arrays(
        build_default_storage(iso_config, config), zone_names
    )
    energy_cap_mwh = float(storage.energy_cap.sum())

    wecc_generators = (
        build_wecc_import_generators() if iso == "CAISO" else []
    )

    years: dict[str, dict] = {}
    fleet = None
    loss_tracker: dict[str, int] = {}
    prior_results = None

    for year in range(START_YEAR, END_YEAR + 1):
        if fleet is None:
            fleet = load_fleet_from_csv(iso, iso_config)
        else:
            fleet, loss_tracker = evolve_fleet(
                fleet, prior_results, year, config, loss_tracker
            )
        dispatch_fleet = fleet + wecc_generators
        fleet_arrays = generators_to_fleet_arrays(
            dispatch_fleet, zone_names, hours=config.hours
        )

        result = cache.load_result(iso, cache_key, year)
        if result.dispatch.shape[0] != fleet_arrays.n_gen:
            raise RuntimeError(
                f"replayed fleet for {iso}/{cache_key} year {year} has "
                f"{fleet_arrays.n_gen} generators but the cached result has "
                f"{result.dispatch.shape[0]}; fleet evolution is not "
                f"reproducible from the stored config"
            )

        year_demand = base_demand * (1.0 + config.demand_growth_rate) ** (
            year - START_YEAR
        )
        peak_demand = float(year_demand.sum(axis=0).max())

        years[str(year)] = _summarize_year(
            result,
            dispatch_fleet,
            fleet_arrays.emission_rate,
            compute_curtailment(wind_potential, result.wind_dispatched),
            compute_curtailment(solar_potential, result.solar_dispatched),
            wind_cap_mw,
            solar_cap_mw,
            energy_cap_mwh,
        )

        prior_results = {
            "fleet_arrays": fleet_arrays,
            "dispatch_result": result,
            "prices": result.prices,
            "peak_demand": peak_demand,
            "planned_additions": [],
        }

    payload = {
        "cache_key": cache_key,
        "iso": iso,
        "config": asdict(config),
        "years": years,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{cache_key}.json"
    out_path.write_text(json.dumps(payload, separators=(",", ":")))

    size = out_path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise ValueError(
            f"{out_path} is {size} bytes, exceeding the "
            f"{MAX_FILE_BYTES}-byte limit"
        )
    logger.info("exported %s (%d bytes)", out_path, size)
    return out_path
