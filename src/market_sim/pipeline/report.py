"""Shared report/metric helpers (ex-``scripts/run_calibration_full.py``).

Orchestrator-unification lane, Stage-D report half, first increment
(refactor-consolidation plan §5): the small numeric/formatting helpers the
calibration report family shares — the leap-unaware hour→month calendar
map, hourly→monthly aggregation, the fit metrics, and the aligned text
table — moved here verbatim. ``run_calibration_full.py`` keeps permanent
same-name ``_``-prefixed aliases (frozen exported surface). Subsequent
Stage-D increments move the ``_print_*`` family and ``report_run`` itself
on top of these helpers; each increment stays under the file-integrity
guard's shrink threshold or carries the ``intentional-shrink`` label.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "DAYS_IN_MONTH",
    "MONTH_NAMES",
    "hour_to_month",
    "hourly_to_monthly",
    "pearson_r",
    "nrmse",
    "print_table",
]

# Non-leap calendar (CLAUDE.md: full 8760 hours always).
DAYS_IN_MONTH: tuple[int, ...] = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

MONTH_NAMES: tuple[str, ...] = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def hour_to_month(hours: int) -> np.ndarray:
    """Return ``(hours,)`` mapping each hour to a 1-based month."""
    month = np.empty(hours, dtype=int)
    h = 0
    for m, days in enumerate(DAYS_IN_MONTH, start=1):
        end = min(h + days * 24, hours)
        month[h:end] = m
        h = end
        if h >= hours:
            break
    return month


def hourly_to_monthly(hourly_mw: np.ndarray) -> np.ndarray:
    """Return ``(12,) MWh`` for a length-8760 hourly MW array."""
    months = hour_to_month(hourly_mw.shape[0])
    return np.array([hourly_mw[months == m].sum() for m in range(1, 13)], dtype=float)


def pearson_r(model: np.ndarray, observed: np.ndarray) -> float:
    """Return the Pearson correlation of two equal-length series."""
    m = model - model.mean()
    o = observed - observed.mean()
    denom = float(np.sqrt((m * m).sum() * (o * o).sum()))
    return float((m * o).sum() / denom) if denom > 0.0 else float("nan")


def nrmse(model: np.ndarray, observed: np.ndarray) -> float:
    """Return RMSE divided by mean observed."""
    rmse = float(np.sqrt(((model - observed) ** 2).mean()))
    denom = float(observed.mean())
    return rmse / denom if denom > 0.0 else float("nan")


def print_table(rows: list[tuple]) -> None:
    """Print a column-aligned text table from a header + rows tuple list."""
    widths = [max(len(str(r[c])) for r in rows) for c in range(len(rows[0]))]
    for row in rows:
        cells = [str(row[c]).rjust(widths[c]) for c in range(len(row))]
        print("    " + "  ".join(cells))
