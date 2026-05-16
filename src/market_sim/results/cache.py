"""Caching of intermediate and final simulation results.

A cached run lives in ``results/{iso}/{cache_key}/`` where ``cache_key`` is
the deterministic hash of the :class:`~market_sim.config.scenarios.ScenarioConfig`
that produced it. Each weather year is one ``year_{year}.parquet`` file, and
the full config is written once as ``config.yaml`` alongside it.
"""

from pathlib import Path

from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.dispatch import DispatchResult
from market_sim.results.outputs import FleetContext, read_fleet_context

# Root directory under which all cached results are stored. Exposed as a
# module attribute so tests can redirect it to a temporary directory.
CACHE_ROOT = Path("results")

_CONFIG_FILENAME = "config.yaml"


def get_cache_path(iso: str, cache_key: str, year: int) -> Path:
    """Return the Parquet path for one cached scenario-year.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        cache_key: Deterministic config hash from ``ScenarioConfig.cache_key``.
        year: Weather/simulation year.

    Returns:
        Path ``results/{iso}/{cache_key}/year_{year}.parquet``.
    """
    return CACHE_ROOT / iso / cache_key / f"year_{year}.parquet"


def get_config_path(iso: str, cache_key: str, year: int) -> Path:
    """Return the ``config.yaml`` path sitting beside a cached scenario."""
    return get_cache_path(iso, cache_key, year).parent / _CONFIG_FILENAME


def is_cached(iso: str, cache_key: str, year: int) -> bool:
    """Return whether a cached result exists for this scenario-year."""
    return get_cache_path(iso, cache_key, year).exists()


def save_result(
    result: DispatchResult,
    config: ScenarioConfig,
    iso: str,
    year: int,
    context: FleetContext | None = None,
) -> Path:
    """Persist a dispatch result and its config to the cache.

    Writes the result as Parquet and, if not already present, the full
    config as ``config.yaml`` in the same directory.

    Args:
        result: The solved dispatch result to cache.
        config: The scenario config that produced ``result``; its
            ``cache_key`` selects the cache directory.
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Weather/simulation year.
        context: Optional fleet context stored in the Parquet metadata so
            the result can be aggregated without re-deriving the fleet.

    Returns:
        The Parquet path written.
    """
    cache_key = config.cache_key()
    path = get_cache_path(iso, cache_key, year)
    path.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(path, context=context)
    config.to_yaml_full(path.parent / _CONFIG_FILENAME)
    return path


def load_result(iso: str, cache_key: str, year: int) -> DispatchResult:
    """Load a cached dispatch result.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        cache_key: Deterministic config hash from ``ScenarioConfig.cache_key``.
        year: Weather/simulation year.

    Returns:
        The cached :class:`DispatchResult`.

    Raises:
        FileNotFoundError: When no cached result exists for this scenario-year.
    """
    path = get_cache_path(iso, cache_key, year)
    if not path.exists():
        raise FileNotFoundError(
            f"no cached result for iso={iso} cache_key={cache_key} "
            f"year={year} (expected {path})"
        )
    return DispatchResult.from_parquet(path)


def load_fleet_context(iso: str, cache_key: str, year: int) -> FleetContext:
    """Load the fleet context stored alongside a cached dispatch result.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        cache_key: Deterministic config hash from ``ScenarioConfig.cache_key``.
        year: Weather/simulation year.

    Returns:
        The cached :class:`~market_sim.results.outputs.FleetContext`.

    Raises:
        FileNotFoundError: When no cached result exists for this scenario-year.
        ValueError: When the cached result carries no fleet context.
    """
    path = get_cache_path(iso, cache_key, year)
    if not path.exists():
        raise FileNotFoundError(
            f"no cached result for iso={iso} cache_key={cache_key} "
            f"year={year} (expected {path})"
        )
    return read_fleet_context(path)
