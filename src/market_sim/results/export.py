"""Export of cached simulation results to compact frontend JSON.

A cached run is 25 yearly Parquet files of hour-by-hour dispatch; the
frontend only needs annual headline numbers. :func:`export_scenario_json`
loads every year, aggregates each to a small annual summary, and writes one
JSON file well under 2 MB.

Each Parquet file carries a :class:`~market_sim.results.outputs.FleetContext`
in its schema metadata -- the per-generator fuel types, capacities and
emission rates, plus resource scalars -- so the aggregation here is fully
self-contained and needs no access to the fleet or weather inputs.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

import numpy as np

from market_sim.config.constants import (
    END_YEAR,
    INFLATION_RATE,
    REAL_DOLLAR_BASE_YEAR,
    START_YEAR,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.results import cache
from market_sim.results.emissions import compute_emissions, compute_nox, compute_so2

logger = logging.getLogger(__name__)

# Hard ceiling on a single exported scenario file.
MAX_FILE_BYTES: int = 2 * 1024 * 1024

# MWh -> TWh and MW -> GW conversion divisors.
_MWH_PER_TWH: float = 1e6
_MW_PER_GW: float = 1e3


def real_to_nominal(
    values: np.ndarray,
    years: np.ndarray,
    inflation_rate: float = INFLATION_RATE,
    base_year: int = REAL_DOLLAR_BASE_YEAR,
) -> np.ndarray:
    """Convert real-dollar values to nominal using compound inflation.

    Anchor date is January 1 of base_year. Year 2026 values pass through
    unchanged. Year 2027+ values are inflated by (1 + r)^(year - base_year).

    values: array of prices/costs in real base-year dollars
    years: array of calendar years corresponding to values
    inflation_rate: annual inflation rate (e.g., 0.022 for 2.2%)
    base_year: year in which real = nominal (from constants.py)

    Returns nominal-dollar values: real * (1 + r)^(year - base_year)
    """
    deflator = (1.0 + inflation_rate) ** (years - base_year)
    return values * deflator


def compute_curtailment(potential, dispatched):
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


def _summarize_year(result, context) -> dict:
    """Aggregate one year's hourly dispatch into an annual summary dict.

    Args:
        result: The year's :class:`~market_sim.model.dispatch.DispatchResult`.
        context: The :class:`~market_sim.results.outputs.FleetContext`
            describing the fleet that produced ``result``.

    Returns:
        A dict of annual headline numbers for the year.
    """
    dispatch = result.dispatch
    gen_per_unit = dispatch.sum(axis=1)  # MWh per generator over the year

    generation_twh: dict[str, float] = {}
    capacity_gw: dict[str, float] = {}
    for g, fuel in enumerate(context.fuel_types):
        generation_twh[fuel] = (
            generation_twh.get(fuel, 0.0) + float(gen_per_unit[g]) / _MWH_PER_TWH
        )
        capacity_gw[fuel] = capacity_gw.get(fuel, 0.0) + context.pmax_mw[g] / _MW_PER_GW

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
    capacity_gw["wind"] = (
        capacity_gw.get("wind", 0.0) + context.wind_cap_mw / _MW_PER_GW
    )
    capacity_gw["solar"] = (
        capacity_gw.get("solar", 0.0) + context.solar_cap_mw / _MW_PER_GW
    )

    emissions_t = float(
        compute_emissions(dispatch, np.asarray(context.emission_rate)).sum()
    )
    # NOx/SO2 are secondary reporting pollutants (CO2 stays primary); older
    # cached contexts predate this wiring and carry empty rate lists.
    nox_tons = (
        float(compute_nox(dispatch, np.asarray(context.nox_rate)).sum())
        if context.nox_rate
        else 0.0
    )
    so2_tons = (
        float(compute_so2(dispatch, np.asarray(context.so2_rate)).sum())
        if context.so2_rate
        else 0.0
    )

    curtailed_mwh = float(
        compute_curtailment(context.wind_potential_mwh, result.wind_dispatched.sum())
        + compute_curtailment(
            context.solar_potential_mwh, result.solar_dispatched.sum()
        )
    )

    storage_cycles = 0.0
    if result.storage_discharge is not None and context.storage_energy_cap_mwh > 0.0:
        storage_cycles = (
            float(result.storage_discharge.sum()) / context.storage_energy_cap_mwh
        )

    return {
        "generation_twh": {k: round(v, 4) for k, v in generation_twh.items()},
        "emissions_mt": round(emissions_t / 1e6, 4),
        "nox_tonnes": round(nox_tons, 2),
        "so2_tonnes": round(so2_tons, 2),
        "avg_price": round(float(result.prices.mean()), 2),
        "peak_price": round(float(result.prices.max()), 2),
        "curtailment_twh": round(max(curtailed_mwh, 0.0) / _MWH_PER_TWH, 4),
        "capacity_gw": {k: round(v, 3) for k, v in capacity_gw.items()},
        "storage_cycles": round(storage_cycles, 2),
    }


def export_scenario_json(cache_key: str, iso: str, output_dir) -> Path:
    """Export one cached scenario to a compact annual-summary JSON file.

    Loads every simulation year's cached Parquet result and its fleet
    context, aggregates each to annual headline numbers, and writes
    ``{cache_key}.json`` to ``output_dir``.

    Args:
        cache_key: Deterministic config hash identifying the cached run.
        iso: ISO identifier, e.g. ``"ERCOT"``.
        output_dir: Directory to write the JSON file into; created if absent.

    Returns:
        The path of the written JSON file.

    Raises:
        FileNotFoundError: When a year's cached Parquet result is missing.
        ValueError: When a year's result carries no fleet context, or when
            the written file exceeds :data:`MAX_FILE_BYTES`.
    """
    iso = iso.upper()
    output_dir = Path(output_dir)

    config = ScenarioConfig.from_yaml(cache.get_config_path(iso, cache_key, START_YEAR))

    years: dict[str, dict] = {}
    for year in range(START_YEAR, END_YEAR + 1):
        result = cache.load_result(iso, cache_key, year)
        context = cache.load_fleet_context(iso, cache_key, year)
        years[str(year)] = _summarize_year(result, context)

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
            f"{out_path} is {size} bytes, exceeding the {MAX_FILE_BYTES}-byte limit"
        )
    logger.info("exported %s (%d bytes)", out_path, size)
    return out_path
