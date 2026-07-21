"""Forecast ensemble: many input draws, one probability distribution.

Two member axes share one runner. The **weather-year ensemble** (the original)
runs the *same* forecast scenario once per historical weather year, varying only
``ScenarioConfig.weather_year`` over the ISO's verified pool
(:func:`market_sim.config.constants.weather_year_pool`), to expose the
weather risk a single pinned shape hides. The **multivariate uncertainty
sampler** (PB-2, ``docs/handoffs/probability-bounds-plan-2026-07.md`` §2)
generalises that member axis: each member is a correlated draw over gas price,
load growth, tech cost, weather year, hydro year and policy bundle
(:mod:`market_sim.uncertainty`), so the ensemble reports a genuine *parametric
probability band* rather than a three-point weather range.

Every draw is an admissible forecast input -- it regenerates for a forward year
and responds to changed conditions -- not a measured outcome fed back to the
model, so this is methodological robustness, not a CLAUDE.md rule-11/13
violation. See ``docs/forecast-methodology-gaps-2026-06.md`` G13.

The members are independent solves with no cross-dependency, so they run in
parallel (CLAUDE.md rule 16) across worker processes -- capped by default at
``min(2, cpu_count - 1)`` because a forecast member on a per-plant ISO uses
several GB (rule 12): more than two concurrent 25-year forecast solves OOMs.
Each member caches under its own ``cache_key`` (the config hash includes every
sampled field), so re-running an ensemble re-uses any member already on disk and
an interrupted batch resumes for free.

The bands (§4.1 ``bands.parquet``) use numpy's Hyndman-Fan type-7 quantile with
a bootstrap CI and the member count attached to every published quantile
(§2.4), replacing the legacy three-point ``ddof=0`` distribution -- which is
kept only for the backwards-compatible weather-year JSON path.
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from multiprocessing import cpu_count
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import END_YEAR, START_YEAR, weather_year_pool
from market_sim.config.scenarios import ScenarioConfig
from market_sim.results import cache
from market_sim.results.export import _summarize_year
from market_sim.structural_prior import (
    STRUCTURAL_LAYER,
    StructuralPrior,
    convolve,
)
from market_sim.uncertainty import (
    DrawSet,
    UncertaintySpec,
    draw_to_config,
    sample_draws,
)

logger = logging.getLogger(__name__)

# Scalar per-year metrics from ``_summarize_year`` to build a distribution over.
# ``emissions_mt`` leads: it is the headline the probability band wraps (§4.1).
# ``clean_share`` / ``negative_price_hours`` are the W2-B CES-reporting
# additions (national-ces-eac-premium plan §5.4) — strictly additive rows in
# metrics.parquet / bands.parquet; every pre-existing metric is untouched.
_SCALAR_METRICS: tuple[str, ...] = (
    "emissions_mt",
    "avg_price",
    "peak_price",
    "curtailment_twh",
    "storage_cycles",
    "clean_share",
    "negative_price_hours",
)

# Published band quantiles (§2.4). PB-2 emits the parametric layer only; the
# structural prior (parametric_plus_structural) and scenario envelope are
# PB-3/PB-0.
_BAND_QUANTILES: tuple[float, ...] = (0.1, 0.5, 0.9)
_PARAMETRIC_LAYER: str = "parametric"
# Default worker cap for forecast members (rule 12); see the module docstring.
_MAX_FORECAST_WORKERS: int = 2


def weather_ensemble_configs(
    base_config: ScenarioConfig,
    weather_years: list[int] | None = None,
) -> dict[int, ScenarioConfig]:
    """Expand a base forecast config into one config per weather draw.

    Args:
        base_config: The forecast scenario to run under every weather draw.
            Every field except ``weather_year`` is held fixed.
        weather_years: Weather years to draw over. Defaults to
            ``base_config.iso``'s verified pool (see
            :func:`market_sim.config.constants.weather_year_pool`). Must be
            non-empty and distinct.

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
        list(weather_year_pool(base_config.iso))
        if weather_years is None
        else [int(y) for y in weather_years]
    )
    if not years:
        raise ValueError("weather_years must be non-empty")
    if len(set(years)) != len(years):
        raise ValueError(f"weather_years must be distinct, got {years!r}")
    return {y: base_config.with_overrides(weather_year=y) for y in sorted(years)}


def _default_workers(workers: int | None) -> int:
    """Resolve the worker count, capping the default at two (rule 12).

    A forecast member is a 25-year sequential solve using several GB on a
    per-plant ISO, so the ensemble default is ``min(2, cpu_count - 1)`` (never
    below 1) -- more than two concurrent members OOMs. An explicit ``workers``
    is honoured as given (the caller owns that risk).
    """
    if workers is not None:
        return workers
    return max(1, min(_MAX_FORECAST_WORKERS, cpu_count() - 1))


def _run_configs(configs: dict, iso: str, workers: int | None) -> dict:
    """Run every ``(config, iso)`` member and return ``{member_id: cache_key}``.

    Shared core of the weather-year and sampler ensembles: members are
    independent and run in parallel across worker processes (rule 16), or
    in-process when ``workers == 1``. A member already cached is loaded inside
    ``run_scenario_iso`` and not re-solved.

    Args:
        configs: Map of member id (weather-year int or draw-id str) to its
            :class:`ScenarioConfig`.
        iso: ISO identifier all members run for.
        workers: Worker processes; see :func:`_default_workers` for the default.

    Returns:
        A dict mapping each member id to the ``cache_key`` of its run, in the
        input order.
    """
    # Local import avoids a module-load cycle: runner imports this module for
    # its CLI subcommand, and this calls back into runner only at run time.
    from market_sim.runner import _run_pair

    workers = _default_workers(workers)
    member_ids = list(configs)
    pairs = [(configs[m], iso) for m in member_ids]

    logger.info(
        "ensemble run start: iso=%s members=%d workers=%d",
        iso,
        len(pairs),
        workers,
    )

    if workers == 1:
        keys = [_run_pair(pair) for pair in pairs]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            keys = list(executor.map(_run_pair, pairs))

    return dict(zip(member_ids, keys))


def run_weather_ensemble(
    base_config: ScenarioConfig,
    iso: str | None = None,
    weather_years: list[int] | None = None,
    workers: int | None = None,
) -> dict[int, str]:
    """Run one forecast per weather draw and return each member's cache key.

    A thin backwards-compatible wrapper over :func:`_run_configs`: the member
    axis is the weather year and the returned keys are keyed by weather-year int
    (the sampler path, :func:`run_ensemble`, keys by draw-id string instead).

    Args:
        base_config: The forecast scenario to run under every weather draw.
        iso: ISO identifier; defaults to ``base_config.iso``.
        weather_years: Weather years to draw over (see
            :func:`weather_ensemble_configs`).
        workers: Worker processes. Defaults to ``min(2, cpu_count - 1)`` (rule
            12); ``1`` runs the members in-process with no subprocess overhead.

    Returns:
        A dict mapping each weather year to the ``cache_key`` of its run.
    """
    iso = (iso or base_config.iso).upper()
    configs = weather_ensemble_configs(base_config, weather_years)
    return _run_configs(configs, iso, workers)


def sample_ensemble_configs(
    base_config: ScenarioConfig, spec: UncertaintySpec
) -> tuple[dict[str, ScenarioConfig], DrawSet]:
    """Expand a base forecast config into one config per sampled draw (§2.5).

    Draws ``spec.n`` correlated members (:func:`sample_draws`) and maps each to a
    :class:`ScenarioConfig` via the PB-1 levers (:func:`draw_to_config`). The
    :class:`DrawSet` is returned alongside so its sampler metadata (seed, LHS
    matrix, correlation matrices) can be written to ``ensemble_meta.json``.

    Args:
        base_config: The forecast scenario every draw perturbs.
        spec: The uncertainty specification.

    Returns:
        A ``(configs, drawset)`` pair, where ``configs`` maps each draw-id to
        its config in draw order.

    Raises:
        ValueError: When ``base_config`` is not in forecast mode (raised by
            :func:`draw_to_config`).
    """
    drawset = sample_draws(spec)
    configs = {d.draw_id: draw_to_config(base_config, d) for d in drawset}
    return configs, drawset


def run_ensemble(
    configs: dict[str, ScenarioConfig],
    iso: str | None = None,
    workers: int | None = None,
) -> dict[str, str]:
    """Run every sampled member and return each draw's cache key (§2.5).

    The sampler counterpart of :func:`run_weather_ensemble`: members are keyed
    by draw-id string and run through the shared :func:`_run_configs` core.

    Args:
        configs: Map of draw-id to its :class:`ScenarioConfig` (from
            :func:`sample_ensemble_configs`).
        iso: ISO identifier; defaults to the first config's ISO.
        workers: Worker processes. Defaults to ``min(2, cpu_count - 1)``.

    Returns:
        A dict mapping each draw-id to the ``cache_key`` of its run.

    Raises:
        ValueError: When ``configs`` is empty.
    """
    if not configs:
        raise ValueError("configs must be non-empty")
    iso = (iso or next(iter(configs.values())).iso).upper()
    return _run_configs(configs, iso, workers)


def _member_config(iso: str, cache_key: str) -> "ScenarioConfig | None":
    """Load one cached member's config, or ``None`` when it is absent.

    The config feeds ``_summarize_year``'s CES crediting rule for the
    ``clean_share`` metric (W2-B). Runner-written caches always carry a
    ``config.yaml``; a hand-built fixture cache may not, and then the
    summary falls back to the default crediting — the same metric values,
    never an error.
    """
    config_path = cache.get_config_path(iso, cache_key, START_YEAR)
    if not config_path.exists():
        return None
    return ScenarioConfig.from_yaml(config_path)


def _config_year_range(config: "ScenarioConfig | None") -> tuple[int, int]:
    """Return the ``(start, end)`` forecast years a config was solved over.

    Mirrors ``runner.evolve_fleet``: ``config.start_year`` / ``end_year`` when
    set, else the module :data:`START_YEAR` / :data:`END_YEAR` default (the full
    2026-2050 horizon). A ``None`` config (a hand-built fixture cache carrying no
    ``config.yaml``) also defers to the module default. At the default horizon
    this is byte-identical to the pre-horizon-aware behaviour.

    The band aggregation MUST use this rather than the module constants directly:
    a member solved over a narrower T1 window (e.g. 2026-2030) has no cached
    result past its ``end_year``, so iterating the module 2026-2050 would raise
    ``FileNotFoundError`` on the first unsolved year.
    """
    start = (
        config.start_year
        if config is not None and config.start_year is not None
        else START_YEAR
    )
    end = (
        config.end_year
        if config is not None and config.end_year is not None
        else END_YEAR
    )
    return start, end


def _members_year_range(members: dict, iso: str) -> tuple[int, int]:
    """Resolve the solved-year range from the members' own cached configs.

    Ensemble members share the base config's horizon (the sampler and weather
    overrides never touch ``start_year`` / ``end_year``), so the first member
    that carries a config fixes the range for the whole ensemble. Falls back to
    the module full-horizon default when no member cache carries a config.
    """
    for key in members.values():
        config = _member_config(iso, key)
        if config is not None:
            return _config_year_range(config)
    return START_YEAR, END_YEAR


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

    # Aggregate over the members' own solved horizon, not the module 2026-2050
    # default: a T1-window ensemble (e.g. 2026-2030) has no cache past its
    # end_year (see :func:`_config_year_range`).
    start_year, end_year = _members_year_range(members, iso)

    # Per-member, per-year summaries reusing the canonical export aggregation.
    per_member: dict[int, dict[str, dict]] = {}
    for wy, key in members.items():
        config = _member_config(iso, key)
        years: dict[str, dict] = {}
        for year in range(start_year, end_year + 1):
            result = cache.load_result(iso, key, year)
            context = cache.load_fleet_context(iso, key, year)
            years[str(year)] = _summarize_year(result, context, config)
        per_member[wy] = years

    distribution: dict[str, dict] = {}
    for year in range(start_year, end_year + 1):
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


# ---------------------------------------------------------------------------
# Multivariate-sampler ensemble (PB-2): metrics, bands, and output surface.
# The §4.1 output schema is the contract PB-3 (structural prior) and PB-4
# (fan-chart page) build against, so the column sets below are frozen.
# ---------------------------------------------------------------------------

_FUEL_METRIC_PREFIX: str = "generation_twh:"


def _member_metric_values(
    members: dict[str, str],
    iso: str,
    year_range: tuple[int, int] | None = None,
) -> dict[int, dict[str, list[float]]]:
    """Load every sampled member and index metric values by year then metric.

    Args:
        members: Map of draw-id to ``cache_key`` (from :func:`run_ensemble`).
        iso: ISO identifier the members were run for.
        year_range: The ``(start, end)`` forecast years to aggregate over,
            inclusive. Pass the base config's range (:func:`_config_year_range`)
            so a T1-window ensemble is read over the horizon it was actually
            solved for; ``None`` resolves it from the members' own cached configs
            (:func:`_members_year_range`), falling back to the module 2026-2050
            default. Reading past a member's ``end_year`` would raise
            ``FileNotFoundError`` on the first unsolved year.

    Returns:
        ``values[year][metric]`` = list of that metric's value across members,
        in ``members`` iteration (draw) order. Metrics are the scalar
        :data:`_SCALAR_METRICS` plus one ``generation_twh:<fuel>`` per fuel; a
        fuel absent from a member contributes 0.0 TWh for that draw.

    Raises:
        FileNotFoundError: When a member's cached result is missing.
    """
    start_year, end_year = year_range or _members_year_range(members, iso)
    # Per (draw, year) summary, then transpose to year -> metric -> [values].
    summaries: dict[str, dict[int, dict]] = {}
    fuels: set[str] = set()
    for draw_id, key in members.items():
        config = _member_config(iso, key)
        by_year: dict[int, dict] = {}
        for year in range(start_year, end_year + 1):
            result = cache.load_result(iso, key, year)
            context = cache.load_fleet_context(iso, key, year)
            summary = _summarize_year(result, context, config)
            by_year[year] = summary
            fuels.update(summary.get("generation_twh", {}))
        summaries[draw_id] = by_year

    metrics = list(_SCALAR_METRICS) + [
        f"{_FUEL_METRIC_PREFIX}{fuel}" for fuel in sorted(fuels)
    ]
    values: dict[int, dict[str, list[float]]] = {}
    for year in range(start_year, end_year + 1):
        per_metric: dict[str, list[float]] = {m: [] for m in metrics}
        for draw_id in members:
            summary = summaries[draw_id][year]
            for metric in _SCALAR_METRICS:
                per_metric[metric].append(float(summary.get(metric, 0.0)))
            gen = summary.get("generation_twh", {})
            for fuel in sorted(fuels):
                per_metric[f"{_FUEL_METRIC_PREFIX}{fuel}"].append(
                    float(gen.get(fuel, 0.0))
                )
        values[year] = per_metric
    return values


def _hf7_quantile(values: np.ndarray, q: float) -> float:
    """Return the ``q`` quantile via numpy's Hyndman-Fan type-7 estimator.

    Type 7 is ``numpy.quantile``'s default (``method="linear"``): linear
    interpolation between the two order statistics bracketing ``q``. This is the
    estimator the audit prescribed to replace the old three-point/``ddof=0``
    percentile logic (plan §2.4); ``n`` is always reported alongside so the
    sampling noise in the estimate is visible.
    """
    return float(np.quantile(values, q, method="linear"))


def _bootstrap_ci(
    values: np.ndarray, q: float, rng: np.random.Generator, n_boot: int, ci: float
) -> tuple[float, float]:
    """Return a bootstrap confidence interval for the ``q`` quantile.

    Resamples the members with replacement ``n_boot`` times, recomputes the
    type-7 quantile on each resample, and returns the central ``ci`` interval of
    that bootstrap distribution -- the sampling-noise band §2.4 attaches to every
    published quantile. Degenerate (n < 2) collapses to the point estimate.

    Args:
        values: Member values for one (year, metric).
        q: Quantile in ``[0, 1]``.
        rng: Seeded generator (deterministic given the spec seed).
        n_boot: Bootstrap resample count.
        ci: Central interval width, e.g. 0.9 for a 90% CI.

    Returns:
        The ``(lo, hi)`` bounds of the CI.
    """
    if values.size < 2:
        point = _hf7_quantile(values, q) if values.size else float("nan")
        return point, point
    idx = rng.integers(0, values.size, size=(n_boot, values.size))
    boot = np.quantile(values[idx], q, method="linear", axis=1)
    tail = (1.0 - ci) / 2.0
    return float(np.quantile(boot, tail)), float(np.quantile(boot, 1.0 - tail))


def compute_bands(
    values: dict[int, dict[str, list[float]]],
    seed: int,
    quantiles: tuple[float, ...] = _BAND_QUANTILES,
    n_boot: int = 1000,
    ci: float = 0.9,
) -> list[dict]:
    """Compute the parametric-layer band rows from per-member metric values.

    For every (year, metric) and every quantile in ``quantiles`` produces one
    row with the type-7 point estimate, the member count ``n``, and a bootstrap
    CI (§2.4/§4.1). Only the ``parametric`` layer is produced here; the
    ``scenario_envelope`` (PB-0) and ``parametric_plus_structural`` (PB-3)
    layers are added by their own stages against this same schema.

    Args:
        values: ``values[year][metric]`` -> member values (from
            :func:`_member_metric_values`).
        seed: Bootstrap seed; deterministic given the sampler spec's seed.
        quantiles: Quantiles to publish.
        n_boot: Bootstrap resample count per quantile.
        ci: Bootstrap CI width.

    Returns:
        Band rows with keys ``year, metric, layer, quantile, value, n,
        bootstrap_lo, bootstrap_hi`` -- in a deterministic (year, metric,
        quantile) order so the bootstrap draws are reproducible.
    """
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    for year in sorted(values):
        for metric in values[year]:
            arr = np.asarray(values[year][metric], dtype=float)
            for q in quantiles:
                lo, hi = _bootstrap_ci(arr, q, rng, n_boot, ci)
                rows.append(
                    {
                        "year": year,
                        "metric": metric,
                        "layer": _PARAMETRIC_LAYER,
                        "quantile": q,
                        "value": _hf7_quantile(arr, q),
                        "n": int(arr.size),
                        "bootstrap_lo": lo,
                        "bootstrap_hi": hi,
                    }
                )
    return rows


def _values_from_metrics(metrics: pd.DataFrame) -> dict[int, dict[str, list[float]]]:
    """Rebuild the ``values[year][metric] -> members`` index from long metrics.

    Inverse of :func:`_metric_rows`: groups the long ``metrics.parquet`` rows
    back into per-(year, metric) member-value lists so bands can be recomputed
    from the committed metrics alone (plan §4.1's pure recompute).
    """
    values: dict[int, dict[str, list[float]]] = {}
    for year, ydf in metrics.groupby("year"):
        per_metric: dict[str, list[float]] = {}
        for metric, mdf in ydf.groupby("metric", sort=False):
            per_metric[str(metric)] = [float(v) for v in mdf["value"]]
        values[int(year)] = per_metric
    return values


def bands_from_metrics(
    metrics: pd.DataFrame,
    seed: int,
    iso: str | None = None,
    prior: StructuralPrior | None = None,
) -> pd.DataFrame:
    """Recompute ``bands.parquet`` from ``metrics.parquet`` + an optional prior.

    A pure function (no solves, no member reload): the parametric layer is
    recomputed from the long metrics, and when ``prior`` and ``iso`` are given
    the ``parametric_plus_structural`` emissions layer is convolved in and
    appended (plan §4.1 -- "bands recompute from metrics.parquet + the prior via
    a pure function"). Cheap, re-runnable and auditable separately from the
    solves; PB-4 rebuilds the published band this way without re-solving.

    Args:
        metrics: The long metrics frame (``draw_id, year, metric, value``).
        seed: Bootstrap/structural seed (the sampler spec's seed).
        iso: ISO for the structural layer; required when ``prior`` is given.
        prior: Optional fitted structural prior.

    Returns:
        A bands DataFrame with the frozen §4.1 schema.

    Raises:
        ValueError: When ``prior`` is given without ``iso``.
    """
    values = _values_from_metrics(metrics)
    rows = compute_bands(values, seed=seed)
    if prior is not None:
        if iso is None:
            raise ValueError("iso is required to convolve the structural prior")
        rows = rows + convolve(values, prior, iso, seed=seed)
    return pd.DataFrame(rows)


def _draw_rows(
    drawset: DrawSet,
    configs: dict[str, ScenarioConfig],
    members: dict[str, str],
) -> list[dict]:
    """Build the ``draws.parquet`` rows: sampled inputs + cache key + config hash.

    ``config_hash`` is the draw config's own hash (pre policy-bundle resolution);
    ``cache_key`` is the member's actual key returned by the runner (post
    resolution and ISO defaults) -- the two can differ, so both are recorded
    (§4.1).
    """
    rows: list[dict] = []
    for draw in drawset:
        rows.append(
            {
                "draw_id": draw.draw_id,
                "gas_price_factor": draw.gas_price_factor,
                "demand_growth_percentile": draw.demand_growth_percentile,
                "tech_cost_percentile": draw.tech_cost_percentile,
                "weather_year": draw.weather_year,
                "hydro_year": draw.hydro_year,
                "policy_bundle": draw.policy_bundle,
                "gas_z": draw.gas_z,
                "cache_key": members[draw.draw_id],
                "config_hash": configs[draw.draw_id].cache_key(),
            }
        )
    return rows


def _metric_rows(
    values: dict[int, dict[str, list[float]]], members: dict[str, str]
) -> list[dict]:
    """Build the long ``metrics.parquet`` rows (draw_id, year, metric, value).

    Emits ``emissions_mt`` first for each (draw, year) -- it is the headline the
    band wraps (§4.1) -- then the remaining scalars and per-fuel generation.
    """
    draw_ids = list(members)
    rows: list[dict] = []
    for year in sorted(values):
        per_metric = values[year]
        for pos, draw_id in enumerate(draw_ids):
            for metric in per_metric:  # insertion order: emissions_mt leads
                rows.append(
                    {
                        "draw_id": draw_id,
                        "year": year,
                        "metric": metric,
                        "value": per_metric[metric][pos],
                    }
                )
    return rows


def export_sampler_ensemble(
    base_config: ScenarioConfig,
    spec: UncertaintySpec,
    iso: str,
    members: dict[str, str],
    drawset: DrawSet,
    configs: dict[str, ScenarioConfig],
    out_dir,
    prior: StructuralPrior | None = None,
) -> dict[str, Path]:
    """Write the §4.1 output surface for a sampler ensemble.

    Emits, into ``out_dir``: ``draws.parquet`` (one row per draw: sampled
    inputs, cache key, config hash), ``metrics.parquet`` (long: draw_id, year,
    metric, value), ``bands.parquet`` (parametric-layer quantiles with n and
    bootstrap CI), and ``ensemble_meta.json`` (the spec, sampler metadata,
    member map, estimator note and dispatch-conditional label). The parquet
    schemas are the frozen PB-3/PB-4 contract.

    When ``prior`` is supplied the emissions band is additionally convolved with
    the D-7 structural-error prior (PB-3, :func:`structural_prior.convolve`): the
    ``parametric_plus_structural`` layer is appended to ``bands.parquet`` *next
    to* the untouched ``parametric`` rows (the point forecast never moves, rule
    13), and the prior's fit + the dispatch-conditional label land in
    ``ensemble_meta.json``.

    Args:
        base_config: The shared forecast base the draws perturb.
        spec: The uncertainty specification.
        iso: ISO identifier.
        members: Map of draw-id to ``cache_key`` (from :func:`run_ensemble`).
        drawset: The draws (carrying sampler metadata).
        configs: Map of draw-id to its :class:`ScenarioConfig`.
        out_dir: Directory to write the four files into; created if absent.
        prior: Optional fitted structural prior (PB-3). ``None`` emits the
            parametric layer only (PB-2's backwards-compatible surface).

    Returns:
        A dict mapping each artifact name to its written path.
    """
    iso = iso.upper()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Aggregate over the base config's solved horizon (authoritative -- the
    # draws share it), so a T1-window ensemble reads only its solved years.
    values = _member_metric_values(members, iso, _config_year_range(base_config))
    draws_path = out_dir / "draws.parquet"
    metrics_path = out_dir / "metrics.parquet"
    bands_path = out_dir / "bands.parquet"
    meta_path = out_dir / "ensemble_meta.json"

    pd.DataFrame(_draw_rows(drawset, configs, members)).to_parquet(
        draws_path, index=False
    )
    pd.DataFrame(_metric_rows(values, members)).to_parquet(metrics_path, index=False)

    # Parametric layer (PB-2) always; structural layer (PB-3) when a prior is
    # given. The two live side by side so the parametric-only band stays
    # inspectable and the headline P50 is the untouched parametric one (§4.1).
    band_rows = compute_bands(values, seed=spec.seed)
    layers = [_PARAMETRIC_LAYER]
    if prior is not None:
        band_rows = band_rows + convolve(values, prior, iso, seed=spec.seed)
        layers = layers + [STRUCTURAL_LAYER]
    pd.DataFrame(band_rows).to_parquet(bands_path, index=False)

    label = (
        "parametric probability band (PB-2); dispatch-conditional -- excludes "
        "the structural-error prior (PB-3) and the deterministic scenario "
        "envelope (PB-0), and excludes fleet-path structural error until PP-0.3"
    )
    if prior is not None:
        label = prior.label() + "; excludes the deterministic scenario envelope (PB-0)"

    meta = {
        "iso": iso,
        "base_config": asdict(base_config),
        "spec": spec._canonical(),
        "sampler": drawset.meta.as_dict(),
        "members": dict(members),
        "band_quantiles": list(_BAND_QUANTILES),
        "layers_present": layers,
        "quantile_estimator": (
            "numpy Hyndman-Fan type 7 (method='linear'); n reported per quantile; "
            "bootstrap 90% CI, 1000 resamples (plan §2.4)"
        ),
        "label": label,
    }
    if prior is not None:
        meta["structural_prior"] = prior.as_dict()
    meta_path.write_text(json.dumps(meta, separators=(",", ":"), default=str))

    logger.info(
        "exported sampler ensemble for %s (%d draws) to %s",
        iso,
        len(members),
        out_dir,
    )
    return {
        "draws": draws_path,
        "metrics": metrics_path,
        "bands": bands_path,
        "meta": meta_path,
    }


def run_sampler_ensemble(
    base_config: ScenarioConfig,
    spec: UncertaintySpec,
    iso: str | None = None,
    workers: int | None = None,
    out_dir=None,
    prior: StructuralPrior | None = None,
) -> dict[str, str]:
    """Sample, solve and export a multivariate-uncertainty ensemble (§2.5).

    End-to-end driver: expand ``spec`` into per-draw configs, run every member
    (cached members are re-used), and -- when ``out_dir`` is given -- write the
    §4.1 output surface.

    Args:
        base_config: The forecast scenario every draw perturbs.
        spec: The uncertainty specification.
        iso: ISO identifier; defaults to ``base_config.iso``.
        workers: Worker processes. Defaults to ``min(2, cpu_count - 1)``.
        out_dir: Directory for the output surface; skipped when ``None``.
        prior: Optional fitted structural prior (PB-3) folded into the emissions
            band when ``out_dir`` is written; ``None`` emits parametric only.

    Returns:
        A dict mapping each draw-id to the ``cache_key`` of its run.
    """
    iso = (iso or base_config.iso).upper()
    configs, drawset = sample_ensemble_configs(base_config, spec)
    members = run_ensemble(configs, iso, workers)
    if out_dir is not None:
        export_sampler_ensemble(
            base_config, spec, iso, members, drawset, configs, out_dir, prior=prior
        )
    return members
