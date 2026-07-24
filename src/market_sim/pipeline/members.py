"""Shared, worker-capped member fan-out for the parallel runners.

Sweeps, weather/sampler ensembles, the scenario matrix and the PB-5 slice
drivers all do the same thing: expand a set of scenarios into ``(config, iso)``
pairs and solve them across a process pool (each member is an independent
solve, CLAUDE.md rule 16). Before this module that pool-open dance was
copy-pasted into ``runner.run_sweep``, ``ensemble._run_configs`` and
``matrix.run_matrix`` — and ``run_sweep``'s copy defaulted to
``cpu_count() - 1`` workers, **uncapped**, which is a rule-12 violation: a
forecast member on a per-plant ISO uses several GB, so more than ~2 concurrent
members OOMs. This module is the single home for that fan-out, with the rule-12
cap **enforced** by default.

Two entry points, one core:

- :func:`run_pairs` — the core: run a list of ``(config, iso)`` pairs (each
  pair may carry its *own* ISO, as a cross-ISO sweep does) and return the cache
  keys in pair order.
- :func:`run_member_configs` — the ``{member_id: config}`` / single-ISO
  convenience the ensembles and the matrix use; returns ``{member_id:
  cache_key}``.

``stride`` (an ``(offset, step)`` pair) runs only the strided subset
``items[offset::step]`` — the primitive the PB-5 slice drivers implement by
hand (``drawset.draws[offset::stride]``) so two invocations partition the member
set with zero overlap. The worker entry point :func:`run_pair` is re-exported
from :mod:`market_sim.pipeline.api` (the picklable, module-level function a
``ProcessPoolExecutor`` ships to workers by reference).

Worker-count policy (preserves each caller's historical contract):

- ``workers=None`` resolves to ``max(1, min(cap, cpu_count() - 1))`` — the
  rule-12 default cap (``cap`` defaults to 2). This is the fix for
  ``run_sweep``'s uncapped default.
- an explicit ``workers`` is **honoured as given** (the caller owns that risk,
  matching ``ensemble._default_workers``). Callers that want an explicit value
  hard-capped (``matrix.run_matrix``) clamp it themselves *before* delegating.
- ``workers == 1`` runs the members in-process, no subprocess overhead.
"""

from __future__ import annotations

import logging
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from typing import TYPE_CHECKING

# The picklable, module-level worker entry point, re-exported so callers have a
# single import home for the member fan-out surface.
from market_sim.pipeline.api import run_pair

if TYPE_CHECKING:  # pragma: no cover - type-only import
    from market_sim.config.scenarios import ScenarioConfig

logger = logging.getLogger(__name__)

__all__ = ["run_pair", "run_pairs", "run_member_configs", "DEFAULT_MEMBER_CAP"]

# The default rule-12 concurrency cap for member fan-outs (a per-plant forecast
# member is GB-scale; more than two concurrent OOMs a typical box).
DEFAULT_MEMBER_CAP: int = 2


def resolve_workers(workers: "int | None", cap: int) -> int:
    """Resolve the worker count under the cap.

    ``None`` -> ``max(1, min(cap, cpu_count() - 1))`` (the rule-12 default cap);
    an explicit value is honoured as given (never silently raised, never — at
    this layer — clamped). Callers wanting an explicit value hard-capped clamp
    it before calling.
    """
    if workers is None:
        return max(1, min(cap, cpu_count() - 1))
    return workers


def _select(pairs: list, stride: "tuple[int, int] | None") -> list:
    """Return the strided subset ``pairs[offset::step]`` (or all when ``None``)."""
    if stride is None:
        return list(pairs)
    offset, step = stride
    if step < 1:
        raise ValueError(f"stride step must be >= 1, got {step}")
    if offset < 0:
        raise ValueError(f"stride offset must be >= 0, got {offset}")
    return list(pairs)[offset::step]


def run_pairs(
    pairs: "list[tuple[ScenarioConfig, str]]",
    workers: "int | None" = None,
    cap: int = DEFAULT_MEMBER_CAP,
    stride: "tuple[int, int] | None" = None,
) -> list[str]:
    """Run ``(config, iso)`` pairs across a capped process pool; keys in order.

    The shared core both ``run_member_configs`` and ``runner.run_sweep`` reach.
    Each pair may carry its own ISO (a cross-ISO sweep). ``stride`` runs only the
    strided subset (see the module docstring).

    Args:
        pairs: The ``(config, iso)`` pairs to solve.
        workers: Worker processes; see :func:`resolve_workers`.
        cap: Rule-12 default cap (only bounds the ``workers=None`` default).
        stride: Optional ``(offset, step)`` to run a strided subset.

    Returns:
        The cache keys, one per solved pair, in the (possibly strided) pair
        order.
    """
    selected = _select(list(pairs), stride)
    if not selected:
        return []
    w = resolve_workers(workers, cap)
    logger.info(
        "member fan-out: %d pair(s) across %d worker(s)%s",
        len(selected),
        w,
        f" (stride {stride})" if stride is not None else "",
    )
    if w == 1:
        return [run_pair(pair) for pair in selected]
    with ProcessPoolExecutor(max_workers=w) as executor:
        return list(executor.map(run_pair, selected))


def run_member_configs(
    configs: "dict[object, ScenarioConfig]",
    iso: str,
    workers: "int | None" = None,
    cap: int = DEFAULT_MEMBER_CAP,
    stride: "tuple[int, int] | None" = None,
) -> dict:
    """Run one ISO's members and return ``{member_id: cache_key}``.

    The ``{member_id: config}`` / single-ISO convenience over :func:`run_pairs`
    used by the weather/sampler ensembles and the scenario matrix. Member order
    is preserved; a ``stride`` subset returns only that subset's ids.

    Args:
        configs: Map of member id (weather-year int, draw-id str, case name) to
            its :class:`ScenarioConfig`.
        iso: ISO identifier all members run for.
        workers: Worker processes; see :func:`resolve_workers`.
        cap: Rule-12 default cap (only bounds the ``workers=None`` default).
        stride: Optional ``(offset, step)`` to run a strided subset.

    Returns:
        ``{member_id: cache_key}`` for the (possibly strided) member subset, in
        input order.

    Raises:
        ValueError: When ``configs`` is empty.
    """
    if not configs:
        raise ValueError("configs must be non-empty")
    iso = iso.upper()
    items = _select(list(configs.items()), stride)
    if not items:
        return {}
    member_ids = [m for m, _ in items]
    pairs = [(config, iso) for _, config in items]
    # stride already applied to items; run the exact pair list.
    keys = run_pairs(pairs, workers=workers, cap=cap, stride=None)
    return dict(zip(member_ids, keys))
