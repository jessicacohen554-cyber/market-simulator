"""Shared per-year phase-timing log line for both solve orchestrators.

The forecast orchestrator (``runner.run_scenario_iso``) and the backcast
orchestrator (``scripts/run_calibration_full.py::solve_and_persist``) each emit
one summary log line per solved year — ``data_prep / solve_p0 / markup /
solve_p1 / results_write / total`` — introduced with the wall-clock
instrumentation in PR #2137. ``docs/handoffs/wallclock-baseline-2026-07.md`` (and
every before/after wall-clock capture) **parses that exact line**, so its
format is a frozen wire contract: the two copies must never drift apart.

This module owns the one format string both call, so a future field addition or
rename happens in exactly one place. The helpers only format and log — each
orchestrator still computes its own phase durations (from ``energy_solve`` vs.
``p2_state['_timing']``) and passes them in.
"""

from __future__ import annotations

import logging

# The frozen format string the baseline doc parses. Defined once so the two
# orchestrators cannot drift; changing it changes a parsed wire format.
_PHASE_TIMING_FMT = (
    "year %d phase timing: data_prep=%.1fs solve_p0=%.1fs "
    "markup=%.1fs solve_p1=%.1fs results_write=%.1fs total=%.1fs"
)
_CACHED_TIMING_FMT = "year %d phase timing: data_prep=%.1fs cached=True total=%.1fs"


def log_year_phase_timing(
    logger: logging.Logger,
    year: int,
    *,
    data_prep: float,
    solve_p0: float,
    markup: float,
    solve_p1: float,
    results_write: float,
    total: float,
) -> None:
    """Emit the frozen per-year phase-timing line for a solved (non-cached) year.

    Byte-identical to the inline ``logger.info(...)`` both orchestrators
    previously carried. Logs through the caller's ``logger`` so the module name
    prefix is unchanged.

    Args:
        logger: The orchestrator's module logger (so the name prefix matches).
        year: The solved year.
        data_prep: Data-preparation seconds (the residual after the solve/write
            phases are subtracted from the year total).
        solve_p0: Base-cost P0 solve seconds.
        markup: Monthly-markup computation seconds.
        solve_p1: Bid-cost P1 solve seconds.
        results_write: Post-solve results-write seconds.
        total: Whole-year wall seconds.
    """
    logger.info(
        _PHASE_TIMING_FMT,
        year,
        data_prep,
        solve_p0,
        markup,
        solve_p1,
        results_write,
        total,
    )


def log_year_cached_timing(logger: logging.Logger, year: int, *, total: float) -> None:
    """Emit the frozen per-year timing line for a cache-hit year (no solve).

    The forecast orchestrator's cache-hit branch: ``data_prep`` and ``total``
    are the same whole-year wall (there was no solve), and ``cached=True``
    replaces the per-phase breakdown. Byte-identical to the inline line.

    Args:
        logger: The orchestrator's module logger.
        year: The cached year.
        total: Whole-year wall seconds (also reported as ``data_prep``).
    """
    logger.info(_CACHED_TIMING_FMT, year, total, total)
