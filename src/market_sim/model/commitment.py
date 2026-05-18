"""Startup-cost bid markup and heuristic CC/CT unit commitment.

This module supports the three-solve dispatch calibration architecture:

* :func:`compute_monthly_markup` measures average run lengths per month from
  a base-cost (P0) dispatch and turns them into a monthly startup
  amortization markup (``startup_cost / run_length``). The markup is added to
  base marginal cost to form the *bid* marginal cost used in the P1 solve, so
  clearing prices reflect cycling costs.

* :func:`compute_commitment` screens CC/CT commitment using P1 clearing
  prices against *base* marginal cost (fuel + VOM, no markup). Generators
  earn the clearing price but their actual cost is the base MC, so the margin
  is ``P1_price - base_MC``. A run must clear an IRR hurdle on its startup
  cost to justify a physical start.

* :func:`apply_commitment_with_coal_pin` zeros CC/CT availability in
  decommitted hours while pinning coal dispatch to its P1 levels — the
  commitment screen only tunes the CC vs CT split, never coal.

Coal is never commitment-screened: EIA-930 confirms ERCOT coal runs all
8,760 hours, cycling output level via its take-or-pay tranches rather than
starting and stopping.
"""

from __future__ import annotations

import calendar

import numpy as np

from market_sim.config.constants import (
    CC_COMMITMENT_PARAMS,
    CC_STARTUP_PARAMS,
    CT_COMMITMENT_PARAMS,
    CT_STARTUP_PARAMS,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays, Generator


COMMITMENT_PARAMS_BY_FUEL: dict[str, list] = {
    "gas_cc": CC_COMMITMENT_PARAMS,
    "gas_ct": CT_COMMITMENT_PARAMS,
}

STARTUP_PARAMS_BY_FUEL: dict[str, list] = {
    "gas_cc": CC_STARTUP_PARAMS,
    "gas_ct": CT_STARTUP_PARAMS,
}


def find_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """Return ``(start, end)`` pairs of consecutive ``True`` segments.

    ``end`` is exclusive, so a run spans ``mask[start:end]`` and its length
    is ``end - start``. An all-``False`` mask yields an empty list.
    """
    mask = np.asarray(mask, dtype=bool)
    if mask.size == 0:
        return []
    # Pad with False on both ends so every run has a rising and a falling
    # edge; the diff then marks starts (+1) and ends (-1).
    edges = np.diff(np.concatenate(([0], mask.astype(np.int8), [0])))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)
    return [(int(s), int(e)) for s, e in zip(starts, ends)]


def _merge_runs(
    runs: list[tuple[int, int]], min_down_hours: float
) -> list[tuple[int, int]]:
    """Merge accepted runs whose idle gap is shorter than ``min_down_hours``.

    Bridging a short gap keeps the unit idling at minimum generation rather
    than paying a second startup, so the gap hours become committed too.
    """
    if not runs:
        return []
    runs = sorted(runs)
    merged = [runs[0]]
    for start, end in runs[1:]:
        prev_start, prev_end = merged[-1]
        if start - prev_end < min_down_hours:
            merged[-1] = (prev_start, end)
        else:
            merged.append((start, end))
    return merged


def _commitment_params(
    fuel_type: str, heat_rate: float
) -> dict[str, float] | None:
    """Return startup/min-run params for a generator, or ``None`` to skip.

    ``None`` means the generator is never commitment-screened (always
    committed): coal, nuclear and every non-thermal fuel. The fuel's
    parameter table is keyed by ascending heat-rate cutoff; the first row
    whose cutoff exceeds ``heat_rate`` applies.
    """
    table = COMMITMENT_PARAMS_BY_FUEL.get(fuel_type)
    if table is None:
        return None
    for cutoff, params in table:
        if heat_rate < cutoff:
            return params
    return table[-1][1]


def _startup_cost(fuel_type: str, heat_rate: float) -> float:
    """Return the ``$/MW`` startup cost for a generator, or ``0`` if none.

    Coal, nuclear and non-thermal fuels get no startup markup. The CC/CT
    tables are keyed by ascending heat-rate cutoff.
    """
    table = STARTUP_PARAMS_BY_FUEL.get(fuel_type)
    if table is None:
        return 0.0
    for cutoff, cost in table:
        if heat_rate < cutoff:
            return cost
    return table[-1][1]


def _month_bounds(T: int) -> list[tuple[int, int]]:
    """Return ``(start, end)`` hour bounds for each calendar month within ``T``.

    Uses a representative non-leap year (2023) so an 8760-hour horizon maps
    cleanly onto twelve months; a shorter horizon yields fewer bounds.
    """
    bounds: list[tuple[int, int]] = []
    hour = 0
    for month in range(1, 13):
        start = hour
        hour += calendar.monthrange(2023, month)[1] * 24
        if start >= T:
            break
        bounds.append((start, min(hour, T)))
    return bounds


def compute_monthly_markup(
    generators: list[Generator],
    fleet_arrays: FleetArrays,
    dispatch: np.ndarray,
    T: int,
) -> np.ndarray:
    """Compute the ``(n_gen, T)`` monthly startup-amortization markup.

    For each CC/CT generator, measure the average run length per calendar
    month from the base-cost (P0) ``dispatch`` and amortize the startup cost
    over it: ``markup = startup_cost / avg_run_length``. Longer summer runs
    give a lower per-MWh markup; shorter shoulder-month runs give a higher
    one. A generator counts as running in an hour when its dispatch exceeds
    5% of Pmax. Coal, nuclear and non-thermal fuels get zero markup.

    Args:
        generators: The dispatch fleet, aligned row-for-row with ``dispatch``.
        fleet_arrays: The vectorized fleet, for per-generator heat rate/Pmax.
        dispatch: The P0 dispatch result, shape ``(n_gen, T)``.
        T: Number of hours in the horizon.

    Returns:
        The markup array, shape ``(n_gen, T)``, in ``$/MWh``.
    """
    markup = np.zeros((len(generators), T))
    month_bounds = _month_bounds(T)

    for g, gen in enumerate(generators):
        startup = _startup_cost(gen.fuel_type, float(fleet_arrays.heat_rate[g]))
        if startup == 0.0:
            continue
        threshold = float(fleet_arrays.pmax[g]) * 0.05
        for h_start, h_end in month_bounds:
            runs = find_runs(dispatch[g, h_start:h_end] > threshold)
            avg_run = (
                float(np.mean([end - start for start, end in runs]))
                if runs
                else 0.0
            )
            markup[g, h_start:h_end] = startup / max(avg_run, 1.0)
    return markup


def compute_commitment(
    p1_prices: np.ndarray,         # (n_zones, T) — from the P1 solve
    base_mc: np.ndarray,           # (n_gen, T) — fuel + VOM, NO markup
    generators: list[Generator],   # fleet list aligned with base_mc rows
    fleet_arrays: FleetArrays,     # for zone_idx, heat_rate
    config: ScenarioConfig,
) -> np.ndarray:
    """Return ``(n_gen, T)`` boolean mask: ``True`` = committed.

    For each CC/CT generator:

    1. Compute hourly margin = ``p1_price[zone] - base_mc``. The margin uses
       *base* MC, not bid MC: a generator earns the clearing price but its
       actual cost is fuel + VOM. Using bid MC would double-count the startup
       markup baked into clearing prices and over-decommit.
    2. Find runs of positive-margin hours.
    3. Drop runs shorter than ``min_run_hours``.
    4. Drop runs whose total margin is below ``startup_per_mw × (1 + IRR)``.
    5. Merge surviving runs separated by less than ``min_down_hours``.

    Coal, nuclear and non-thermal generators are never screened — they stay
    committed in every hour.

    Args:
        p1_prices: Zonal clearing prices from the P1 solve, ``(n_zones, T)``.
        base_mc: Base marginal cost (fuel + VOM, no markup), ``(n_gen, T)``.
        generators: The dispatch fleet, aligned with ``base_mc`` rows.
        fleet_arrays: The vectorized fleet, for ``zone_idx`` and heat rate.
        config: Scenario configuration supplying ``commitment_irr_hurdle``.

    Returns:
        The commitment mask, shape ``(n_gen, T)``.
    """
    n_gen, T = base_mc.shape
    irr = config.commitment_irr_hurdle
    committed = np.ones((n_gen, T), dtype=bool)

    for g, gen in enumerate(generators):
        params = _commitment_params(
            gen.fuel_type, float(fleet_arrays.heat_rate[g])
        )
        if params is None:
            continue  # coal, nuclear, non-thermal: always committed

        zone = int(fleet_arrays.zone_idx[g])
        margin = p1_prices[zone, :] - base_mc[g, :]
        hurdle = params["startup_per_mw"] * (1.0 + irr)

        accepted: list[tuple[int, int]] = []
        for start, end in find_runs(margin > 0.0):
            if (end - start) < params["min_run_hours"]:
                continue
            if float(margin[start:end].sum()) < hurdle:
                continue
            accepted.append((start, end))

        mask = np.zeros(T, dtype=bool)
        for start, end in _merge_runs(accepted, params["min_down_hours"]):
            mask[start:end] = True
        committed[g, :] = mask

    return committed


def apply_commitment_with_coal_pin(
    fleet_arrays: FleetArrays,
    committed: np.ndarray,          # (n_gen, T) boolean
    p1_dispatch: np.ndarray,        # (n_gen, T) from the P1 solve
    generators: list[Generator],    # fleet list aligned with committed rows
) -> FleetArrays:
    """Return new ``FleetArrays`` with the commitment screen applied.

    * Gas CC/CT: availability is zeroed in decommitted hours.
    * Coal: availability is pinned to reproduce the P1 coal dispatch
      (availability = P1 dispatch / Pmax, with a tiny floor), so coal never
      decommits and the P2 solve only tunes the CC vs CT split.
    * Nuclear, hydro and other fuels pass through unchanged, keeping their
      Pmin (nuclear stays must-run).

    Args:
        fleet_arrays: The P1 vectorized fleet.
        committed: The commitment mask from :func:`compute_commitment`.
        p1_dispatch: The P1 dispatch result, ``(n_gen, T)``.
        generators: The dispatch fleet, aligned with ``committed`` rows.

    Returns:
        A new ``FleetArrays`` with availability adjusted for P2.
    """
    avail = fleet_arrays.availability.copy()

    for g, gen in enumerate(generators):
        if gen.fuel_type == "coal":
            # Pin coal: availability ceiling = P1 dispatch fraction, so P2
            # coal reproduces P1 coal. A tiny floor avoids a numerical zero.
            p1_frac = np.clip(
                p1_dispatch[g, :] / max(float(fleet_arrays.pmax[g]), 1.0),
                0.0, 1.0,
            )
            avail[g, :] = np.maximum(p1_frac, 1e-6)
        elif gen.fuel_type in ("gas_cc", "gas_ct"):
            avail[g, ~committed[g]] = 0.0

    return FleetArrays(
        pmax=fleet_arrays.pmax, pmin=fleet_arrays.pmin.copy(),
        heat_rate=fleet_arrays.heat_rate, vom=fleet_arrays.vom,
        emission_rate=fleet_arrays.emission_rate, nox_rate=fleet_arrays.nox_rate,
        zone_idx=fleet_arrays.zone_idx, fuel_type_idx=fleet_arrays.fuel_type_idx,
        availability=avail, unit_ids=fleet_arrays.unit_ids,
        efficiency_bin=fleet_arrays.efficiency_bin,
    )
