"""Caching of intermediate and final simulation results.

A cached run lives in ``results/{iso}/{cache_key}/`` where ``cache_key`` is
the deterministic hash of the :class:`~market_sim.config.scenarios.ScenarioConfig`
that produced it. Each weather year's final dispatch is one
``year_{year}.parquet`` file, and the full config is written once as
``config.yaml`` alongside it.

When the two-pass commitment screen runs, the year also keeps a separate
``year_{year}_p1.parquet`` holding the Pass 1 (pre-commitment) dispatch, so
both the P1 and the final P2 datasets are available. ``year_{year}.parquet``
always holds the final result — P2 when commitment is enabled, P1 when it is
off — so every existing reader is unaffected by the extra P1 file.

Cache-key staleness (cache-epoch policy)
----------------------------------------
The cache directory is keyed on ``ScenarioConfig.cache_key()``, which hashes
``asdict(config)`` — so a change that alters a solve's *output* but is **not** a
``ScenarioConfig`` field (a bug fix in the LP builder, a new mechanism gated by
an env var, a change to a measured input basis) does NOT move the key, and a
pre-change ``results/{iso}/{key}/`` bundle would be silently re-used. The
project's cache-epoch policy (refactor-consolidation plan §7 H, compat clause 2)
governs this: a behavior-changing PR must either express the change as a
``ScenarioConfig`` field (so the key moves) or bump the documented cache epoch
and purge/segregate the affected caches. A pure byte-identical refactor needs
neither. This module never auto-invalidates on epoch; that is the operator's
responsibility per that policy.
"""

from contextlib import contextmanager
from pathlib import Path

import numpy as np

from market_sim.config import paths
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.dispatch import DispatchResult
from market_sim.results.outputs import FleetContext, read_fleet_context

# Root directory under which all cached results are stored. Sourced from the
# central path registry (:data:`market_sim.config.paths.RESULTS_ROOT`,
# ``DATA_ROOT/results``) rather than a cwd-relative ``Path("results")`` so the
# results tree does not silently fork when the process runs outside the repo
# root. Kept as a mutable module attribute: tests (and a handful of scripts)
# redirect it to a temporary directory — prefer the :func:`cache_root`
# contextmanager over hand-rolling a save/set/restore dance.
CACHE_ROOT = paths.RESULTS_ROOT

_CONFIG_FILENAME = "config.yaml"


@contextmanager
def cache_root(root: "Path | str"):
    """Temporarily redirect :data:`CACHE_ROOT` to ``root``, restoring on exit.

    Absorbs the save/set/restore dance repeated across the result-export and
    reference-solve scripts (``export_results``, ``run_full_horizon``,
    ``ff_readiness_battery``, ...): ``prior = cache.CACHE_ROOT; cache.CACHE_ROOT
    = tmp; try: ...; finally: cache.CACHE_ROOT = prior``. The restore runs even
    if the body raises, so a redirected cache never leaks into a later solve in
    the same process (which would read/write the wrong tree).

    Args:
        root: The directory to point the cache at for the duration of the block.

    Yields:
        The resolved :class:`~pathlib.Path` the cache now points at.
    """
    global CACHE_ROOT
    prior = CACHE_ROOT
    CACHE_ROOT = Path(root)
    try:
        yield CACHE_ROOT
    finally:
        CACHE_ROOT = prior


def get_cache_path(
    iso: str, cache_key: str, year: int, pass_label: str | None = None
) -> Path:
    """Return the Parquet path for one cached scenario-year.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        cache_key: Deterministic config hash from ``ScenarioConfig.cache_key``.
        year: Weather/simulation year.
        pass_label: Solve-pass tag. ``None`` is the final-result file
            ``year_{year}.parquet``; ``"p1"`` is the Pass 1 dataset
            ``year_{year}_p1.parquet`` kept when the commitment screen runs.

    Returns:
        Path ``results/{iso}/{cache_key}/year_{year}[_{pass_label}].parquet``.
    """
    suffix = "" if pass_label is None else f"_{pass_label}"
    return CACHE_ROOT / iso / cache_key / f"year_{year}{suffix}.parquet"


def get_config_path(iso: str, cache_key: str, year: int) -> Path:
    """Return the ``config.yaml`` path sitting beside a cached scenario."""
    return get_cache_path(iso, cache_key, year).parent / _CONFIG_FILENAME


def is_cached(
    iso: str, cache_key: str, year: int, pass_label: str | None = None
) -> bool:
    """Return whether a cached result exists for this scenario-year.

    ``pass_label`` selects which solve pass to check; ``None`` is the
    final-result file (see :func:`get_cache_path`).
    """
    return get_cache_path(iso, cache_key, year, pass_label).exists()


def save_result(
    result: DispatchResult,
    config: ScenarioConfig,
    iso: str,
    year: int,
    context: FleetContext | None = None,
    pass_label: str | None = None,
    demand: "np.ndarray | None" = None,
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
        pass_label: Solve-pass tag (see :func:`get_cache_path`). ``None``
            writes the final-result file; ``"p1"`` writes the Pass 1
            dataset.
        demand: Optional ``(n_zones, T)`` served demand, stored so the
            forecast-invariant checker can verify the energy balance.

    Returns:
        The Parquet path written.
    """
    cache_key = config.cache_key()
    path = get_cache_path(iso, cache_key, year, pass_label)
    path.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(path, context=context, demand=demand)
    config.to_yaml_full(path.parent / _CONFIG_FILENAME)
    return path


def load_result(
    iso: str, cache_key: str, year: int, pass_label: str | None = None
) -> DispatchResult:
    """Load a cached dispatch result.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        cache_key: Deterministic config hash from ``ScenarioConfig.cache_key``.
        year: Weather/simulation year.
        pass_label: Solve-pass tag (see :func:`get_cache_path`). ``None``
            loads the final-result file; ``"p1"`` loads the Pass 1 dataset.

    Returns:
        The cached :class:`DispatchResult`.

    Raises:
        FileNotFoundError: When no cached result exists for this scenario-year.
    """
    path = get_cache_path(iso, cache_key, year, pass_label)
    if not path.exists():
        raise FileNotFoundError(
            f"no cached result for iso={iso} cache_key={cache_key} "
            f"year={year} pass={pass_label} (expected {path})"
        )
    return DispatchResult.from_parquet(path)


def load_fleet_context(
    iso: str, cache_key: str, year: int, pass_label: str | None = None
) -> FleetContext:
    """Load the fleet context stored alongside a cached dispatch result.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        cache_key: Deterministic config hash from ``ScenarioConfig.cache_key``.
        year: Weather/simulation year.
        pass_label: Solve-pass tag (see :func:`get_cache_path`).

    Returns:
        The cached :class:`~market_sim.results.outputs.FleetContext`.

    Raises:
        FileNotFoundError: When no cached result exists for this scenario-year.
        ValueError: When the cached result carries no fleet context.
    """
    path = get_cache_path(iso, cache_key, year, pass_label)
    if not path.exists():
        raise FileNotFoundError(
            f"no cached result for iso={iso} cache_key={cache_key} "
            f"year={year} (expected {path})"
        )
    return read_fleet_context(path)
