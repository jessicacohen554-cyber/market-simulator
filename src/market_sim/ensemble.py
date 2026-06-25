"""Weather-year forecast ensemble: many weather draws, one distribution.

A forecast pins a single representative historical weather year for its load
and VRE capacity-factor shapes (``ScenarioConfig.weather_year``;
``runner.run_scenario_iso`` loads demand and renewable profiles for that year
and then evolves the fleet across 2026-2050). Pinning one shape understates the
weather risk in any forecast headline number: a hot-summer draw and a
mild-summer draw produce materially different prices, emissions and curtailment
even with an identical fleet and fuel path.

This module runs the *same* forecast scenario once per weather draw — varying
only ``weather_year`` over :data:`WEATHER_YEAR_POOL` — and reports the
distribution of each annual metric across the draws. A weather draw is an
admissible forecast input (it would regenerate for a forward year and responds
to changed conditions), not a measured outcome fed back to the model, so this
is methodological robustness, not a CLAUDE.md #10 violation. See
``docs/forecast-methodology-gaps-2026-06.md`` G13.

The members are independent solves with no cross-dependency, so they run in
parallel (CLAUDE.md #16). Each member caches under its own ``cache_key`` (the
config hash includes ``weather_year``), so re-running an ensemble re-uses any
member already on disk.
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from multiprocessing import cpu_count
from pathlib import Path

import numpy as np

from market_sim.config.constants import END_YEAR, START_YEAR, WEATHER_YEAR_POOL
from market_sim.config.scenarios import ScenarioConfig
from market_sim.results import cache
from market_sim.results.export import _summarize_year

logger = logging.getLogger(__name__)

# Scalar per-year metrics from ``_summarize_year`` to build a distribution over.
_SCALAR_METRICS: tuple[str, ...] = (
    "avg_price",
    "peak_price",
    "emissions_mt",
    "curtailment_twh",
    "storage_cycles",
)


def weather_ensemble_configs(
    base_config: ScenarioConfig,
    weather_years: list[int] | None = None,
) -> dict[int, ScenarioConfig]:
    """Expand a base forecast config into one config per weather draw.

    Args:
        base_config: The forecast scenario to run under every weather draw.
            Every field except ``weather_year`` is held fixed.
        weather_years: Weather years to draw over. Defaults to the full
            :data:`WEATHER_YEAR_POOL`. Must be non-empty and distinct.

    Returns:
        A dict mapping each weather year to ``base_config`` with that
        ``weather_year`` override, ordered by ascending year.

    Raises:
        ValueError: When ``base_config`` is not in forecast mode, or when
            ``weather_years`` is empty or contains duplicates.
    """
    if base_config.mode != "forecast":
        raise ValueError(
            "the weather-year ensemble is a forecast tool; base config mode "
            f"must be 'forecast', got {base_config.mode!r}. A backcast pins a "
            "single historical year by design."
        )
    years = (
        list(WEATHER_YEAR_POOL)
        if weather_years is None
        else [int(y) for y in weather_years]
    )
    if not years:
        raise ValueError("weather_years must be non-empty")
    if len(set(years)) != len(years):
        raise ValueError(f"weather_years must be distinct, got {years!r}")
    return {y: base_config.with_overrides(weather_year=y) for y in sorted(years)}


def run_weather_ensemble(
    base_config: ScenarioConfig,
    iso: str | None = None,
    weather_years: list[int] | None = None,
    workers: int | None = None,
) -> dict[int, str]:
    """Run one forecast per weather draw and return each member's cache key.

    The members are independent and run in parallel across worker processes
    (CLAUDE.md #16). A member whose result is already cached is loaded inside
    ``run_scenario_iso`` and not re-solved.

    Args:
        base_config: The forecast scenario to run under every weather draw.
        iso: ISO identifier; defaults to ``base_config.iso``.
        weather_years: Weather years to draw over (see
            :func:`weather_ensemble_configs`).
        workers: Worker processes. Defaults to ``cpu_count - 1``; ``1`` runs
            the members in-process with no subprocess overhead.

    Returns:
        A dict mapping each weather year to the ``cache_key`` of its run.
    """
    # Local import avoids a module-load cycle: runner imports this module for
    # its CLI subcommand, and this calls back into runner only at run time.
    from market_sim.runner import _run_pair

    iso = (iso or base_config.iso).upper()
    configs = weather_ensemble_configs(base_config, weather_years)
    pairs = [(config, iso) for config in configs.values()]

    if workers is None:
        workers = max(1, cpu_count() - 1)

    logger.info(
        "run_weather_ensemble start: iso=%s weather_years=%s workers=%d",
        iso,
        list(configs),
        workers,
    )

    if workers == 1:
        keys = [_run_pair(pair) for pair in pairs]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            keys = list(executor.map(_run_pair, pairs))

    return dict(zip(configs.keys(), keys))


def _distribution(values: list[float]) -> dict[str, float]:
    """Return summary distribution statistics for a list of member values.

    With a small member count (the pool is three years today) the percentiles
    interpolate between the order statistics — this is the standard linear
    ``numpy.percentile`` behaviour and is reported as-is.

    Args:
        values: One value per ensemble member.

    Returns:
        A dict with ``mean``, ``std`` (population), ``min``, ``p10``, ``p50``,
        ``p90`` and ``max``.
    """
    arr = np.asarray(values, dtype=float)
    return {
        "mean": round(float(arr.mean()), 4),
        "std": round(float(arr.std(ddof=0)), 4),
        "min": round(float(arr.min()), 4),
        "p10": round(float(np.percentile(arr, 10)), 4),
        "p50": round(float(np.percentile(arr, 50)), 4),
        "p90": round(float(np.percentile(arr, 90)), 4),
        "max": round(float(arr.max()), 4),
    }


def _aggregate_year(member_summaries: dict[int, dict]) -> dict:
    """Aggregate one forecast year's per-member summaries into a distribution.

    Args:
        member_summaries: Map of weather year to that member's annual summary
            dict (the output of ``_summarize_year``).

    Returns:
        A dict with a distribution for each scalar metric and for each fuel's
        generation, plus the raw per-member summaries under ``by_member``.
    """
    out: dict = {}
    for metric in _SCALAR_METRICS:
        values = [s[metric] for s in member_summaries.values() if metric in s]
        if values:
            out[metric] = _distribution(values)

    # Generation by fuel: union of fuels seen across members, absent fuels
    # contribute zero TWh for that draw.
    fuels: set[str] = set()
    for summary in member_summaries.values():
        fuels.update(summary.get("generation_twh", {}))
    out["generation_twh"] = {
        fuel: _distribution(
            [
                s.get("generation_twh", {}).get(fuel, 0.0)
                for s in member_summaries.values()
            ]
        )
        for fuel in sorted(fuels)
    }

    out["by_member"] = {
        str(wy): member_summaries[wy] for wy in sorted(member_summaries)
    }
    return out


def summarize_ensemble(members: dict[int, str], iso: str) -> dict:
    """Load every member's cached run and build the cross-draw distribution.

    Args:
        members: Map of weather year to ``cache_key`` (the return value of
            :func:`run_weather_ensemble`).
        iso: ISO identifier the members were run for.

    Returns:
        A payload dict with the ISO, the weather years, the member cache keys,
        the shared base config (member config with ``weather_year`` dropped),
        and a per-forecast-year distribution under ``distribution``.

    Raises:
        FileNotFoundError: When a member's cached result is missing.
    """
    iso = iso.upper()
    if not members:
        raise ValueError("members must be non-empty")

    # Per-member, per-year summaries reusing the canonical export aggregation.
    per_member: dict[int, dict[str, dict]] = {}
    for wy, key in members.items():
        years: dict[str, dict] = {}
        for year in range(START_YEAR, END_YEAR + 1):
            result = cache.load_result(iso, key, year)
            context = cache.load_fleet_context(iso, key, year)
            years[str(year)] = _summarize_year(result, context)
        per_member[wy] = years

    distribution: dict[str, dict] = {}
    for year in range(START_YEAR, END_YEAR + 1):
        ys = str(year)
        distribution[ys] = _aggregate_year({wy: per_member[wy][ys] for wy in members})

    # The base config is shared across members; surface it without the draw.
    any_key = next(iter(members.values()))
    base = ScenarioConfig.from_yaml(cache.get_config_path(iso, any_key, START_YEAR))
    base_dict = asdict(base)
    base_dict.pop("weather_year", None)

    return {
        "iso": iso,
        "weather_years": sorted(members),
        "members": {str(wy): key for wy, key in members.items()},
        "base_config": base_dict,
        "distribution": distribution,
    }


def export_ensemble_json(
    members: dict[int, str],
    iso: str,
    out_path,
) -> Path:
    """Write the weather-year ensemble distribution to a JSON file.

    Args:
        members: Map of weather year to ``cache_key``.
        iso: ISO identifier.
        out_path: File path to write the distribution JSON to; parent
            directories are created.

    Returns:
        The path written.
    """
    payload = summarize_ensemble(members, iso)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, separators=(",", ":")))
    logger.info(
        "exported weather-year ensemble for %s (%d members) to %s",
        iso.upper(),
        len(members),
        out_path,
    )
    return out_path
