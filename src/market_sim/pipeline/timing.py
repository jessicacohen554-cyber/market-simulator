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

**Sub-instrumentation (refactor plan §7-H4).** ``results_write`` was one merged
window, which could not say whether the phase is parquet-bound or
frame/scoring-bound. Callers may now pass ``results_write_parts`` — an *ordered*
``{component: seconds}`` mapping summing to ``results_write`` — which is
appended as a trailing ``(results_write: a=…s b=…s)`` clause. The six original
fields keep their exact spelling, order and position, and ``results_write``
remains their sum, so every existing parse of the line is unaffected; the
component names are each orchestrator's own (the two write very different
things), while the *line* stays a single owned format.

**``markup`` sub-instrumentation (PERF-B session 2).** ``markup`` is not a
measured phase at all — both orchestrators compute it as the RESIDUAL
``energy_solve - build - solve_p0 - solve_p1``, so it absorbs every non-solve,
non-build cost of ``pipeline.solve.run_energy_solve`` (both passes' objective
assembly and solution marshalling, ``compute_monthly_markup``, the P0→P1 seam,
the basis seam, and one whole matrix build whenever P1 cold-rebuilds). Callers
may now pass ``markup_parts`` on the same contract as ``results_write_parts``:
an *ordered* ``{component: seconds}`` mapping summing to ``markup``, rendered
as a ``(markup: a=…s b=…s)`` clause. It is emitted **before** the
``results_write`` clause so a parser anchored on ``(results_write:`` — or one
reading that clause to end-of-line — keeps working, and the six frozen fields
are again untouched.
"""

from __future__ import annotations

import logging

# The frozen format string the baseline doc parses. Defined once so the two
# orchestrators cannot drift; changing it changes a parsed wire format. The
# optional %s tail carries the results_write breakdown (empty string when the
# caller passes no parts), so the six frozen fields never move.
_PHASE_TIMING_FMT = (
    "year %d phase timing: data_prep=%.1fs solve_p0=%.1fs "
    "markup=%.1fs solve_p1=%.1fs results_write=%.1fs total=%.1fs%s%s"
)
_CACHED_TIMING_FMT = "year %d phase timing: data_prep=%.1fs cached=True total=%.1fs"


def format_phase_parts(label: str, parts: "dict[str, float] | None") -> str:
    """Return a trailing ``(<label>: a=…s b=…s)`` clause, or ``""``.

    The one renderer both sub-instrumentation clauses use, so they cannot drift
    in spelling or number format.

    Args:
        label: The phase the breakdown decomposes (``"markup"`` /
            ``"results_write"``) — it names the clause.
        parts: Ordered ``{component: seconds}`` breakdown of that phase (the
            components must sum to it), or ``None`` for no breakdown.

    Returns:
        The formatted clause with a leading space, or the empty string when
        ``parts`` is empty/``None``.
    """
    if not parts:
        return ""
    body = " ".join(f"{name}={seconds:.1f}s" for name, seconds in parts.items())
    return f" ({label}: {body})"


def format_results_write_parts(parts: "dict[str, float] | None") -> str:
    """Return the trailing ``(results_write: a=…s b=…s)`` clause, or ``""``.

    Args:
        parts: Ordered ``{component: seconds}`` breakdown of ``results_write``
            (the components must sum to it), or ``None`` for no breakdown.

    Returns:
        The formatted clause with a leading space, or the empty string when
        ``parts`` is empty/``None`` — in which case the emitted line is
        byte-identical to the pre-sub-instrumentation format.
    """
    return format_phase_parts("results_write", parts)


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
    results_write_parts: "dict[str, float] | None" = None,
    markup_parts: "dict[str, float] | None" = None,
) -> None:
    """Emit the frozen per-year phase-timing line for a solved (non-cached) year.

    The six leading fields are byte-identical to the inline ``logger.info(...)``
    both orchestrators previously carried; a ``results_write_parts`` breakdown
    is appended after them (see the module docstring). Logs through the caller's
    ``logger`` so the module name prefix is unchanged.

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
        results_write_parts: Optional ordered ``{component: seconds}``
            breakdown of ``results_write``; the components are the caller's own
            and must sum to ``results_write``.
        markup_parts: Optional ordered ``{component: seconds}`` breakdown of
            the residual ``markup`` phase (see the module docstring); rendered
            BEFORE the ``results_write`` clause.
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
        format_phase_parts("markup", markup_parts),
        format_results_write_parts(results_write_parts),
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
