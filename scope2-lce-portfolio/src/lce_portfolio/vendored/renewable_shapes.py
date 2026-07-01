"""Vendored renewable capacity-factor shape logic (copied from market_sim).

=============================================================================
VENDORING HEADER (keep current — see ``vendored/README.md``)
-----------------------------------------------------------------------------
WHAT was copied:
  * ``derive_cf_profile`` — turns a normalized EIA-930 hourly generation
    distribution (sums ~1.0 over the year) into an hourly capacity-factor
    series whose annual mean equals a target average CF, clipped to [0, 1].
  * ``derive_offshore_wind_profile`` — derives an hourly offshore-wind CF
    series from an onshore-wind CF series (centered rolling-mean smoothing +
    minimum-CF floor + rescale to a higher target mean).
  * ``_CF_MIN`` / ``_CF_MAX`` — the physical CF bounds [0, 1].

  NOT copied (deliberately out of scope for a single-node tool): the EIA-860
  zone-share distribution (``_distribute_by_eia860``), the HSL / uncurtailed-
  potential machinery, clear-sky solar geometry, MERRA-2 wind reshaping, and
  every ``market_sim`` import those pull in. The single-node reconciliation
  primitive :func:`capacity_weighted_collapse` below is *original* to this
  tool (it is NOT a verbatim copy — see its own note) and expresses the
  ADR-0011 zonal->ISO capacity-weighting rule directly.

FROM (upstream file):
  src/market_sim/data/renewables.py
    - derive_cf_profile          @ lines 807-826
    - derive_offshore_wind_profile @ lines 1770-1807
  src/market_sim/config/constants.py
    - OFFSHORE_WIND_SMOOTHING_HOURS (6), OFFSHORE_WIND_MIN_CF (0.08)

UPSTREAM COMMIT at copy time (``git rev-parse HEAD``):
  2012b2fdbb42eaafaab43931d9851445c333b123

HOW to re-sync:
  1. ``git -C <market-sim-root> rev-parse HEAD`` and diff the two functions
     above against the current ``renewables.py`` / ``constants.py``.
  2. Re-copy the bodies verbatim if they changed; keep the local adaptations:
     (a) ``HOURS_PER_YEAR`` is a plain argument here (default 8760) instead of
         an imported constant, and (b) the module has no ``market_sim`` import.
  3. Bump the UPSTREAM COMMIT line above to the new HEAD.
=============================================================================

These functions are pure (numpy in, numpy out), deterministic, and vectorized
— no per-hour Python loops, no filesystem or ``market_sim`` dependency — so the
tool stays 100% standalone.
"""

from __future__ import annotations

import numpy as np

# Capacity factors are physically bounded to the closed interval [0, 1].
# (Vendored verbatim from market_sim.data.renewables._CF_MIN / _CF_MAX.)
_CF_MIN: float = 0.0
_CF_MAX: float = 1.0

# Non-leap model year (matches ``lce_portfolio.config.HOURS_PER_YEAR`` and the
# upstream ``market_sim.config.constants.HOURS_PER_YEAR``). Kept as a default
# argument rather than an import so this module has no cross-package coupling.
_HOURS_PER_YEAR: int = 8760

# Offshore-wind derivation parameters, vendored from
# market_sim.config.constants (NREL ATB 2024 / Musial et al. 2022).
OFFSHORE_WIND_SMOOTHING_HOURS: int = 6  # rolling-mean window (ocean fetch)
OFFSHORE_WIND_MIN_CF: float = 0.08  # min hourly CF — offshore rarely near zero


def derive_cf_profile(
    generation_values: np.ndarray,
    avg_cf: float,
    hours_per_year: int = _HOURS_PER_YEAR,
) -> np.ndarray:
    """Convert an EIA generation distribution into an hourly CF profile.

    The EIA-930 ``value`` series is a probability distribution summing to
    ~1.0 over the year. Scaling it by the annual-average capacity factor and
    by ``hours_per_year`` rescales the distribution so that its hourly mean
    equals ``avg_cf``. The result is clipped to the physical CF bounds
    ``[0, 1]`` to guard against rounding noise and high-output outliers.

    (Vendored from ``market_sim.data.renewables.derive_cf_profile``; the only
    change is that ``hours_per_year`` is an explicit argument rather than an
    imported constant.)

    Args:
        generation_values: A ``(hours_per_year,)`` array of normalized EIA
            generation values for one ISO/year/fuel group.
        avg_cf: Annual-average capacity factor of the fleet (fraction).
        hours_per_year: Hour count the distribution spans (default 8760).

    Returns:
        A ``(hours_per_year,)`` array of hourly capacity factors in ``[0, 1]``.
    """
    cf = generation_values * avg_cf * hours_per_year
    return np.clip(cf, _CF_MIN, _CF_MAX)


def derive_offshore_wind_profile(
    onshore_wind_cf: np.ndarray,
    target_avg_cf: float,
    smoothing_hours: int = OFFSHORE_WIND_SMOOTHING_HOURS,
    min_cf: float = OFFSHORE_WIND_MIN_CF,
) -> np.ndarray:
    """Derive an hourly offshore-wind CF profile from the onshore-wind profile.

    Offshore wind differs from onshore in three physical ways captured here:
    1. Less gusty — ocean fetch smooths out rapid variations. Applied as a
       centered rolling-mean window of ``smoothing_hours`` (default 6h).
    2. Rarely zero — there is almost always some wind offshore. Applied as a
       floor of ``min_cf`` (default 0.08).
    3. Higher average CF — stronger, more consistent resource. The smoothed
       and floored profile is rescaled so its mean matches ``target_avg_cf``.

    (Vendored verbatim from
    ``market_sim.data.renewables.derive_offshore_wind_profile``.)

    Args:
        onshore_wind_cf: ``(T,)`` hourly onshore-wind CF profile for the ISO.
        target_avg_cf: Desired annual-average CF for offshore wind.
        smoothing_hours: Rolling-mean window width in hours. Larger values
            produce a smoother (less variable) profile. Default 6.
        min_cf: Minimum hourly CF floor — offshore rarely drops to zero.
            Default 0.08 (~8% of rated). Source: NREL offshore wind studies.

    Returns:
        ``(T,)`` hourly offshore-wind CF profile, clipped to ``[0, 1]``.
    """
    kernel = np.ones(smoothing_hours, dtype=float) / smoothing_hours
    smoothed = np.convolve(onshore_wind_cf, kernel, mode="same")
    floored = np.maximum(smoothed, min_cf)
    rescaled = floored * (target_avg_cf / floored.mean())
    return np.clip(rescaled, _CF_MIN, _CF_MAX)


def capacity_weighted_collapse(
    zonal_cf: np.ndarray,
    zonal_cap_mw: np.ndarray,
) -> np.ndarray:
    """Collapse per-zone hourly CF shapes into one ISO-wide CF series.

    This is the ADR-0011 zonal->ISO reconciliation rule for a **single-node**
    tool: a resource's ISO-wide hourly capacity factor is the capacity-weighted
    average of its zonal CF shapes, with weights equal to each zone's installed
    (or buildable) nameplate capacity for that resource. Capacity-weighting is
    the physically correct aggregation because a zone with more MW contributes
    proportionally more energy to the ISO total at every hour::

        cf_iso[t] = Σ_z cap_mw[z] * cf_zonal[z, t] / Σ_z cap_mw[z]

    This is **original** to this tool, not a verbatim upstream copy. Upstream
    ``market_sim`` goes the other direction — it *distributes* an ISO-wide
    measured shape onto zones by EIA-860 capacity share
    (``_distribute_by_eia860``) — and its reconciliation preserves the ISO total
    exactly. Collapsing back with the same capacity weights is the inverse and
    recovers the ISO aggregate, which is why the single-node tool can consume
    the EIA-930 ISO-wide distribution directly (see ``scripts/build_profiles.py``
    and the note there). This helper exists so that *when* independent per-zone
    shapes are supplied (e.g. CAISO solar or MISO wind, which upstream reshapes
    per zone), they collapse deterministically to one node.

    Limitation (single-node tool): collapsing to one ISO node discards all
    intra-ISO diversity — a zone that is calm while another is windy averages
    out, so the ISO profile is smoother than any single site. This is the
    documented price of the single-aggregated-node model (PLAN.md §2).

    Args:
        zonal_cf: ``(n_zones, T)`` per-zone hourly CF in ``[0, 1]``.
        zonal_cap_mw: ``(n_zones,)`` installed/buildable capacity per zone (MW).
            If the total is non-positive, falls back to a simple (unweighted)
            mean across zones.

    Returns:
        ``(T,)`` ISO-wide hourly CF, clipped to ``[0, 1]``.

    Raises:
        ValueError: if the shapes are inconsistent (``zonal_cf`` not 2-D, or a
            weight per zone is not supplied).
    """
    zonal_cf = np.asarray(zonal_cf, dtype=float)
    zonal_cap_mw = np.asarray(zonal_cap_mw, dtype=float)
    if zonal_cf.ndim != 2:
        raise ValueError(f"zonal_cf must be (n_zones, T), got shape {zonal_cf.shape}")
    if zonal_cap_mw.shape != (zonal_cf.shape[0],):
        raise ValueError(
            f"zonal_cap_mw must be (n_zones,)={(zonal_cf.shape[0],)}, "
            f"got {zonal_cap_mw.shape}"
        )
    total = float(zonal_cap_mw.sum())
    if total <= 0.0:
        # No capacity weights available -> simple mean (documented fallback).
        collapsed = zonal_cf.mean(axis=0)
    else:
        weights = zonal_cap_mw / total
        collapsed = weights @ zonal_cf
    return np.clip(collapsed, _CF_MIN, _CF_MAX)
