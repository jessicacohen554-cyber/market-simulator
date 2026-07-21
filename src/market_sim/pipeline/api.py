"""Public orchestration facade for the shared solve pipeline.

This module is the supported, stable entry point for driving a full
multi-year scenario solve programmatically (refactor-consolidation plan
§5, orchestrator-unification lane). Scripts and library code should
import from here rather than reaching into ``market_sim.runner``'s
private surface (``_run_pair``) or binding to the orchestrator module
directly:

- :func:`run_scenario` — run every simulation year for one
  ``(config, iso)`` and return the scenario's deterministic cache key.
- :func:`run_pair` — the picklable, module-level worker entry point for
  process-pool fan-outs (sweeps, ensembles, PB-5 matrix slices). It is a
  plain top-level function, so :mod:`pickle` serializes it by reference
  (``market_sim.pipeline.api.run_pair``) and any ``ProcessPoolExecutor``
  / ``multiprocessing`` map can ship it to workers.

Both functions delegate to :func:`market_sim.runner.run_scenario_iso`
**resolved at call time** (a lazy attribute lookup on the module), so
test patches of ``market_sim.runner.run_scenario_iso`` intercept calls
made through this facade exactly as they intercept direct calls — the
facade adds no second patch point to maintain.

The on-disk contract of a completed run (pinned by
``tests/test_pipeline_api.py``): each solved year is cached at
``results/{iso}/{cache_key}/year_{year}.parquet`` with the full config
written once as ``config.yaml`` alongside, and a per-year capacity
evolution ledger at ``evolution_{year}.json``
(:mod:`market_sim.results.cache`, :mod:`market_sim.results.evolution_ledger`).

The imports of :mod:`market_sim.runner` are deliberately lazy
(function-scope): ``runner`` module-level-imports the pipeline package's
submodules, so a module-level import here would create an import-time
cycle (guarded by ``tests/test_persisted_identity.py``'s AST check).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type-only import, no runtime cycle
    from market_sim.config.scenarios import ScenarioConfig

__all__ = ["run_scenario", "run_pair"]


def run_scenario(config: "ScenarioConfig", iso: str) -> str:
    """Run every simulation year for one scenario and one ISO.

    Thin public facade over :func:`market_sim.runner.run_scenario_iso`
    (the forecast orchestrator's year loop: per-year fleet build/evolve,
    P0/P1 dispatch solve, caching, capacity evolution).

    Args:
        config: The scenario configuration to run.
        iso: ISO identifier, e.g. ``"ERCOT"``. When it differs from
            ``config.iso`` the config's ISO is overridden downstream.

    Returns:
        The scenario's deterministic ``cache_key``. Results land at
        ``results/{iso}/{cache_key}/year_{year}.parquet`` (+
        ``config.yaml``, ``evolution_{year}.json``).
    """
    from market_sim import runner

    return runner.run_scenario_iso(config, iso)


def run_pair(pair: "tuple[ScenarioConfig, str]") -> str:
    """Run one ``(config, iso)`` pair; the picklable worker entry point.

    Public successor of ``market_sim.runner._run_pair`` for sweep /
    ensemble / matrix fan-outs: a module-level function, picklable by
    reference, safe to hand to ``ProcessPoolExecutor.map``.

    Args:
        pair: ``(config, iso)`` tuple, as produced by sweep expansion.

    Returns:
        The pair's deterministic ``cache_key`` (see :func:`run_scenario`).
    """
    config, iso = pair
    from market_sim import runner

    return runner.run_scenario_iso(config, iso)
