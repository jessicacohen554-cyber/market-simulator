"""Shared solve-core package for the forecast and backcast orchestrators.

This package is the destination of the orchestrator-unification plan
(``docs/handoffs/orchestrator-unification-plan-2026-07.md``): the per-year
LP solve — today duplicated near-verbatim in ``runner.py`` (forecast) and
``scripts/run_calibration.py`` (backcast) — migrates here stage by stage so
both orchestrators call one shared core.

**Stage 1 (this commit) delivers only the typed contract objects**, no solve
code yet:

- :class:`~market_sim.pipeline.spec.DispatchSpec` — a frozen bundle of the base
  ``dispatch_kwargs`` the LP builder consumes, with ``to_dispatch_kwargs()``.
- :class:`~market_sim.pipeline.spec.ReserveSpec` — a typed wrapper over the dict
  ``reserve_config.build_reserve_dispatch_kwargs`` returns, with ``merge_into()``.
- :class:`~market_sim.pipeline.prior.PriorYearResults` — a typed replacement for
  the untyped cross-year ``prior_results`` dict threaded through ``runner.py``'s
  year loop (audit AR-2). Dict-style ``.get`` / ``__getitem__`` shims keep every
  existing reader working during the migration.
- :class:`~market_sim.pipeline.result.YearSolveResult` — a placeholder for the
  shared core's return type, populated in Stages 3-4.

None of these change any solved number; Stage 1 is pure typing + scaffolding.

**Stage 2 adds ``kwargs.py``** — the shared base ``dispatch_kwargs`` assembly
(:func:`~market_sim.pipeline.kwargs.build_base_dispatch_kwargs`) and the reserve
co-optimization wrapper (:func:`~market_sim.pipeline.kwargs.apply_reserve_coopt`)
— now called by both orchestrators. The remaining solve modules (``solve.py``,
``commitment.py``, ``backcast_config.py``, ``overlays.py``) land in later
stages — see the plan §5.
"""

from __future__ import annotations

from market_sim.pipeline.kwargs import apply_reserve_coopt, build_base_dispatch_kwargs
from market_sim.pipeline.prior import PriorYearResults
from market_sim.pipeline.result import YearSolveResult
from market_sim.pipeline.spec import UNSET, DispatchSpec, ReserveSpec

__all__ = [
    "DispatchSpec",
    "ReserveSpec",
    "UNSET",
    "PriorYearResults",
    "YearSolveResult",
    "build_base_dispatch_kwargs",
    "apply_reserve_coopt",
]
