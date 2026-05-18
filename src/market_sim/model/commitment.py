"""Heuristic unit commitment via post-LP price-based screening.

Extends commitment screening from CC-only to all thermal generators
(CC, CT, coal). Each fuel type has class-specific startup costs,
minimum run times, and minimum down times from NREL cycling cost data.

The commitment price signal includes a reserve-based ORDC scarcity
adder that represents ancillary service and ORDC revenue the
energy-only LP duals do not capture. Without this, LP prices
understate the revenue CCs/CTs earn during tight hours, causing
over-decommitment.

A startup run must clear an IRR hurdle: total margin over the run
must exceed startup_cost × (1 + irr). Operators won't commit wear
and tear on a start without adequate return.

Coal uses a rolling-average margin over a multi-day evaluation
window (config.coal_eval_window_hours) because coal operators make
multi-day commitment decisions, tolerating overnight price dips
within a profitable week.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

from market_sim.config.constants import (
    CC_COMMITMENT_PARAMS,
    COAL_COMMITMENT_PARAMS,
    CT_COMMITMENT_PARAMS,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays, Generator


COMMITMENT_PARAMS_BY_FUEL: dict[str, list] = {
    "gas_cc": CC_COMMITMENT_PARAMS,
    "gas_ct": CT_COMMITMENT_PARAMS,
    "coal": COAL_COMMITMENT_PARAMS,
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


def _commitment_params(fuel_type: str, heat_rate: float) -> dict[str, float] | None:
    """Return startup/min-run params for a generator, or ``None`` if non-thermal.

    The fuel's parameter table is keyed by ascending heat-rate cutoff; the
    first row whose cutoff exceeds ``heat_rate`` applies.
    """
    table = COMMITMENT_PARAMS_BY_FUEL.get(fuel_type)
    if table is None:
        return None
    for cutoff, params in table:
        if heat_rate < cutoff:
            return params
    return table[-1][1]


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


def compute_ordc(
    fleet_arrays: FleetArrays,
    demand: np.ndarray,           # (n_zones, T)
    wind_dispatched: np.ndarray,  # (n_zones, T)
    solar_dispatched: np.ndarray,  # (n_zones, T)
    voll: float,
    sigma_mw: float,
) -> np.ndarray:
    """Compute hourly ORDC scarcity adder from dispatch reserves.

    Uses a simplified ERCOT-style ORDC: adder = VOLL × Φ(-reserves/sigma)
    where Φ is the normal CDF and sigma represents net-load forecast error.

    Returns ``(n_zones, T)`` array — same system-wide ORDC broadcast to all
    zones.
    """
    thermal_avail = (
        fleet_arrays.pmax[:, None] * fleet_arrays.availability
    ).sum(axis=0)
    sys_demand = demand.sum(axis=0)
    renewable_gen = wind_dispatched.sum(axis=0) + solar_dispatched.sum(axis=0)
    reserves_mw = thermal_avail - (sys_demand - renewable_gen)

    lolp = norm.cdf(-reserves_mw / sigma_mw)
    ordc_system = np.minimum(voll * lolp, voll)

    n_zones = demand.shape[0]
    return np.broadcast_to(
        ordc_system[None, :], (n_zones, demand.shape[1])
    ).copy()


def compute_commitment(
    prices: np.ndarray,            # (n_zones, T) from Pass 1
    mc: np.ndarray,                # (n_gen, T) marginal cost array
    generators: list[Generator],   # fleet list aligned with mc rows
    fleet_arrays: FleetArrays,     # for zone_idx, pmax, availability
    config: ScenarioConfig,
    demand: np.ndarray,            # (n_zones, T) — needed for ORDC
    wind_dispatched: np.ndarray,   # (n_zones, T) — from Pass 1
    solar_dispatched: np.ndarray,  # (n_zones, T) — from Pass 1
) -> np.ndarray:
    """Return ``(n_gen, T)`` boolean mask: ``True`` = committed.

    For each thermal generator (CC, CT, coal):
    1. Compute hourly margin = (price + ORDC)[zone] - MC
    2. Find runs of positive-margin hours
       (coal: rolling-average positive margin over eval window)
    3. Filter: run length >= min_run_hours
    4. Filter: total run margin >= startup_cost × (1 + IRR)
    5. Merge runs separated by < min_down_hours
    6. Non-thermal generators (nuclear, hydro, wind, solar) always committed.
    """
    n_gen, T = mc.shape
    irr = config.commitment_irr_hurdle
    # Clamp the coal evaluation window to the horizon so the rolling-average
    # convolution stays well-defined on short test horizons.
    coal_window = min(config.coal_eval_window_hours, T)

    # Compute ORDC from Pass 1 reserves
    ordc = compute_ordc(
        fleet_arrays, demand, wind_dispatched, solar_dispatched,
        config.voll, config.commitment_ordc_sigma,
    )

    committed = np.ones((n_gen, T), dtype=bool)

    for g, gen in enumerate(generators):
        params = _commitment_params(
            gen.fuel_type, float(fleet_arrays.heat_rate[g])
        )
        if params is None:
            continue  # non-thermal: always committed

        zone = int(fleet_arrays.zone_idx[g])
        margin = prices[zone, :] + ordc[zone, :] - mc[g, :]
        hurdle = params["startup_per_mw"] * (1.0 + irr)

        if gen.fuel_type == "coal":
            # Coal: rolling-average margin over evaluation window.
            # Tolerates overnight dips if surrounding days are profitable.
            kernel = np.ones(coal_window) / coal_window
            effective_margin = np.convolve(margin, kernel, mode="same")
        else:
            effective_margin = margin

        accepted: list[tuple[int, int]] = []
        for start, end in find_runs(effective_margin > 0.0):
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


def apply_commitment(
    fleet_arrays: FleetArrays,
    committed: np.ndarray,         # (n_gen, T) boolean
) -> FleetArrays:
    """Return new FleetArrays with availability zeroed in decommitted hours.

    Also zeros pmin for any generator with decommitted hours, so coal's
    40% minimum generation constraint doesn't conflict with zero availability.
    """
    avail = fleet_arrays.availability.copy()
    pmin = fleet_arrays.pmin.copy()
    avail[~committed] = 0.0
    for g in range(fleet_arrays.n_gen):
        if (~committed[g]).any() and pmin[g] > 0:
            pmin[g] = 0.0

    return FleetArrays(
        pmax=fleet_arrays.pmax, pmin=pmin,
        heat_rate=fleet_arrays.heat_rate, vom=fleet_arrays.vom,
        emission_rate=fleet_arrays.emission_rate, nox_rate=fleet_arrays.nox_rate,
        zone_idx=fleet_arrays.zone_idx, fuel_type_idx=fleet_arrays.fuel_type_idx,
        availability=avail, unit_ids=fleet_arrays.unit_ids,
        efficiency_bin=fleet_arrays.efficiency_bin,
    )
