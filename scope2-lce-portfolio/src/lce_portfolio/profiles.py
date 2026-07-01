"""Hourly capacity-factor (CF) profiles for generation resources.

Produces an ``(n_res, T)`` CF matrix in ``[0, 1]`` for the active resources.
Storage resources carry a zero CF row (their availability is governed by SOC
dynamics, not a CF ceiling).

The minimal build ships *synthetic* shapes — a deterministic diurnal solar
curve, an anti-correlated wind series, and flat baseload for firm clean — so the
LP runs end-to-end without external data. Real ISO/zone shapes are wired later by
copying the market-sim renewable-shape logic into
:mod:`lce_portfolio.vendored` (see ``docs/prompt-packs/PP-03-cf-profiles.md``);
this module's :func:`build_cf_matrix` is the single seam to swap.
"""

from __future__ import annotations

import numpy as np

from lce_portfolio.config import HOURS_PER_YEAR
from lce_portfolio.resources import ResourceArrays

# Deterministic synthetic shapes: no Date.now / RNG seeding surprises, so runs
# and tests are reproducible. Keyed by resource name; anything not listed and
# non-storage falls back to a flat profile at its assumed capacity factor.
_DIURNAL_HOURS = np.arange(HOURS_PER_YEAR) % 24


def _solar_shape() -> np.ndarray:
    """Deterministic diurnal solar CF: a clipped sinusoid peaking at midday."""
    # Daylight bump centered on hour 13, zero at night.
    bump = np.sin((_DIURNAL_HOURS - 6) / 12.0 * np.pi)
    shape = np.clip(bump, 0.0, None)
    # Mild seasonal envelope (summer stronger) via day-of-year.
    doy = np.arange(HOURS_PER_YEAR) // 24
    seasonal = 0.85 + 0.15 * np.sin((doy - 80) / 365.0 * 2 * np.pi)
    return shape * seasonal


def _wind_shape() -> np.ndarray:
    """Deterministic wind CF: anti-correlated with solar, with multi-day lulls.

    A synoptic (~weekly) weather cycle that drops to near zero produces genuine
    calm spells, so covering trough hours requires storage or over-build — which
    is what makes the matching-vs-premium frontier non-trivial (and pulls storage
    into the mix at higher premiums). Real ISO shapes replace this via the
    vendored loader.
    """
    hours = np.arange(HOURS_PER_YEAR)
    diurnal = 0.6 + 0.4 * np.cos((_DIURNAL_HOURS - 6) / 12.0 * np.pi)
    doy = hours // 24
    seasonal = 0.9 + 0.2 * np.sin((doy - 300) / 365.0 * 2 * np.pi)  # windier winter
    # Synoptic weather cycle in [0,1] that bottoms out (calm spells) ~every 6.5 d.
    synoptic = np.clip(np.sin(hours / (24 * 6.5) * 2 * np.pi) + 0.15, 0.0, None)
    return np.clip(diurnal * seasonal * synoptic, 0.0, 1.5)


def _normalize_to_cf(shape: np.ndarray, target_cf: float) -> np.ndarray:
    """Scale a non-negative shape so its annual mean equals ``target_cf``."""
    mean = shape.mean()
    if mean <= 0:
        return np.full_like(shape, target_cf)
    return np.clip(shape * (target_cf / mean), 0.0, 1.0)


def build_cf_matrix(resources: ResourceArrays, iso: str, year: int) -> np.ndarray:
    """Return the ``(n_res, T)`` hourly CF matrix for ``resources``.

    Synthetic shapes normalized to each resource's ``cf_assumed`` annual mean.
    Storage rows are zero. ``iso``/``year`` are accepted for signature
    compatibility with the future vendored real-profile loader.
    """
    T = HOURS_PER_YEAR
    cf = np.zeros((resources.n_res, T), dtype=float)
    for r, name in enumerate(resources.names):
        if resources.is_storage[r]:
            continue
        target = resources.cf_assumed[r]
        if name == "solar_pv":
            cf[r] = _normalize_to_cf(_solar_shape(), target)
        elif name in ("onshore_wind", "offshore_wind"):
            cf[r] = _normalize_to_cf(_wind_shape(), target)
        else:
            # Firm clean (nuclear, geothermal, hydro placeholder): flat at CF.
            cf[r] = np.full(T, min(target, 1.0))
    return cf
