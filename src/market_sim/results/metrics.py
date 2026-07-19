"""Canonical fit metrics shared by the calibration scorers and derive scripts.

One home for the handful of goodness-of-fit statistics the calibration/scoring
toolchain computes over and over — the audit found ~6 copies scattered across
the runners, the HTML renderer, and the derive scripts. Keeping one definition
each means every consumer scores on the same arithmetic.

Stdlib + numpy only (no intra-package imports), so this stays a leaf of the
import graph and is safe to import from anywhere, including plain scripts.

Note: :mod:`market_sim.results.calibration` keeps its own ``_pearson_r``
(``np.corrcoef``-based, used by :func:`check_hourly_dispatch_correlation`) and
its inline NRMSE; those are a *different* numerical path and are deliberately
not merged here (doing so would perturb their output at the ULP level). The
functions below are the manual/streaming forms the *runners and derives* share.
"""

from __future__ import annotations

import numpy as np

__all__ = ["pearson_r", "nrmse", "mae", "pct_diff"]

# Values below this magnitude are treated as zero (shared with
# results.calibration, which pins the same tolerance).
_ZERO_TOL: float = 1e-9


def pearson_r(model: np.ndarray, observed: np.ndarray) -> float:
    """Return the Pearson correlation of two equal-length series.

    Computed directly from the centred cross- and auto-products; returns
    ``nan`` when either series is constant (zero denominator).
    """
    m = model - model.mean()
    o = observed - observed.mean()
    denom = float(np.sqrt((m * m).sum() * (o * o).sum()))
    return float((m * o).sum() / denom) if denom > 0.0 else float("nan")


def nrmse(model: np.ndarray, observed: np.ndarray) -> float:
    """Return RMSE divided by mean observed — a unitless dispersion metric.

    Returns ``nan`` when mean observed is non-positive (no scale to normalise
    against).
    """
    rmse = float(np.sqrt(((model - observed) ** 2).mean()))
    denom = float(observed.mean())
    return rmse / denom if denom > 0.0 else float("nan")


def mae(
    model: np.ndarray, actual: np.ndarray, weights: np.ndarray | None = None
) -> float:
    """Weighted mean absolute error, NaNs dropped.

    Rows where either series is non-finite are excluded; ``weights`` defaults to
    uniform. The weights are applied only over the surviving (finite) rows.
    """
    ok = np.isfinite(model) & np.isfinite(actual)
    if weights is None:
        weights = np.ones_like(model)
    w = weights[ok]
    return float(np.sum(np.abs(model[ok] - actual[ok]) * w) / w.sum())


def pct_diff(model: float, benchmark: float) -> float:
    """Return the signed fractional difference ``(model - benchmark) / benchmark``.

    When the benchmark is zero, returns ``0.0`` if the model is also zero and
    ``inf`` otherwise, so a quantity the benchmark expects absent but the model
    produces always fails.
    """
    if abs(benchmark) < _ZERO_TOL:
        return 0.0 if abs(model) < _ZERO_TOL else float("inf")
    return (model - benchmark) / benchmark
