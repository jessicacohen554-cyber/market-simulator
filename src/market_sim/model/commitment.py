"""Heuristic unit commitment via post-LP price-based screening.

Analyzes dispatch prices from a first-pass LP solve to decide which hours
each gas CC generator would commit (start up), based on whether the run's
net revenue covers the startup cost. A second LP pass then enforces those
commitment decisions by zeroing availability in decommitted hours.

This approximates integer commitment without MIP or commercial solvers.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.constants import CC_COMMITMENT_PARAMS
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays, Generator


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


def _commitment_params(heat_rate: float) -> dict[str, float]:
    """Return the startup/min-run params for a CC of the given heat rate.

    :data:`CC_COMMITMENT_PARAMS` is keyed by ascending heat-rate cutoff;
    the first row whose cutoff exceeds ``heat_rate`` applies.
    """
    for cutoff, params in CC_COMMITMENT_PARAMS:
        if heat_rate < cutoff:
            return params
    return CC_COMMITMENT_PARAMS[-1][1]


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


def compute_commitment(
    prices: np.ndarray,          # (n_zones, T) from Pass 1
    mc: np.ndarray,              # (n_gen, T) marginal cost array
    generators: list[Generator],  # fleet list aligned with mc rows
    fleet_arrays: FleetArrays,   # for zone_idx
    config: ScenarioConfig,      # for commitment parameters
) -> np.ndarray:
    """Return ``(n_gen, T)`` boolean mask: ``True`` = committed, ``False`` = off.

    For each gas CC generator:
    1. Compute hourly margin = price[zone] - MC
    2. Find runs of consecutive positive-margin hours
    3. Filter: run must be >= min_run hours
    4. Filter: total run margin must cover startup cost ($/MW)
    5. Merge runs separated by < min_down hours (cheaper to stay on)
    6. All other fuel types return True for all hours (always committed)
    """
    del config  # commitment parameters come from CC_COMMITMENT_PARAMS
    mc = np.asarray(mc, dtype=float)
    prices = np.asarray(prices, dtype=float)
    n_gen, T = mc.shape

    committed = np.ones((n_gen, T), dtype=bool)
    for g, gen in enumerate(generators):
        if gen.fuel_type != "gas_cc":
            continue  # coal (must-run) and CTs (peakers) are always committed

        params = _commitment_params(float(fleet_arrays.heat_rate[g]))
        zone = int(fleet_arrays.zone_idx[g])
        margin = prices[zone, :] - mc[g, :]

        accepted: list[tuple[int, int]] = []
        for start, end in find_runs(margin > 0.0):
            if (end - start) < params["min_run_hours"]:
                continue  # too short to justify a startup
            if margin[start:end].sum() < params["startup_per_mw"]:
                continue  # run revenue does not cover the startup cost
            accepted.append((start, end))

        mask = np.zeros(T, dtype=bool)
        for start, end in _merge_runs(accepted, params["min_down_hours"]):
            mask[start:end] = True
        committed[g, :] = mask

    return committed


def apply_commitment(
    fleet_arrays: FleetArrays,
    committed: np.ndarray,       # (n_gen, T) boolean
) -> FleetArrays:
    """Return a new FleetArrays with availability zeroed in decommitted hours."""
    avail = fleet_arrays.availability.copy()
    for g in range(fleet_arrays.n_gen):
        avail[g, ~committed[g, :]] = 0.0
    return FleetArrays(
        pmax=fleet_arrays.pmax, pmin=fleet_arrays.pmin,
        heat_rate=fleet_arrays.heat_rate, vom=fleet_arrays.vom,
        emission_rate=fleet_arrays.emission_rate, nox_rate=fleet_arrays.nox_rate,
        zone_idx=fleet_arrays.zone_idx, fuel_type_idx=fleet_arrays.fuel_type_idx,
        availability=avail, unit_ids=fleet_arrays.unit_ids,
        efficiency_bin=fleet_arrays.efficiency_bin,
    )
