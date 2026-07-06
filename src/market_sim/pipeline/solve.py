"""Shared P0/P1 energy solve loop — one solve core for both orchestrators (Stage 3).

The P0 (base-cost) → monthly-startup-markup → P1 (bid-cost) solve sequence, the
intra-year warm start, and the cross-year warm-start seam were duplicated
near-verbatim in ``runner.py`` (forecast) and ``scripts/run_calibration.py``
(backcast) — orchestrator-unification plan §3.4. Stage 3 hoists the sequence
here; both orchestrators now call :func:`run_energy_solve`.

Solve semantics (unchanged, statement-for-statement):

- P0 and P1 solve the *same* LP — identical constraint matrix and bounds —
  and differ only in the objective (P1 = base MC + startup markup). So the
  model is built once and P1 warm-starts from P0's optimal basis
  (``changeColsCost`` in place): this skips the second matrix build and
  converges in ~8x fewer simplex iterations, cutting the P1 solve ~5x. It does
  not move annual generation or prices — validated plant-by-plant on ERCOT
  2023, where every plant's annual MWh and the zonal prices are unchanged; the
  only difference is sub-MW hourly reshuffling among units tied at the margin,
  which the LP is already indifferent to. Set ``MARKET_SIM_WARMSTART=0`` to
  fall back to two independent cold solves (e.g. for an A/B comparison or to
  isolate a solver issue).
- Cross-year warm-start (``MARKET_SIM_WARMSTART_XYEAR=1``, default off):
  adjacent years share zones, network and most units, so the prior year's
  optimal basis — carried in ``xyear_cache`` and remapped onto this year's
  fleet — is a strong warm start for the one remaining cold solve, P0. The LP
  optimum is basis-independent, so this only changes the solve path, never the
  cleared prices or generation.

Cross-year cache policy (plan §8): the backcast front-end threads its
``xyear_cache`` through (preserving today's behavior — the basis is exported
even when the flag is off, so a downstream A/B does not depend on call
ordering). The forecast front-end passes ``xyear_cache=None`` — cross-year
warm-start stays OFF on the forecast path because its ≤0.0033% marginal-tie
reshuffle is read by ``capacity.evolve_fleet``'s per-unit retirement screen and
can tip a retire/keep decision, changing the *next* year's fleet (measured in
``docs/cross-year-warmstart.md``). Wiring it forecast-side is blocked on making
the capacity screen basis-independent — see plan §8.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import numpy as np

from market_sim.model.commitment import compute_monthly_markup
from market_sim.model.dispatch import DispatchModel, solve_dispatch

if TYPE_CHECKING:
    from market_sim.data.fleet import FleetArrays
    from market_sim.model.dispatch import DispatchResult


@dataclass(frozen=True)
class EnergySolveResult:
    """What :func:`run_energy_solve` returns — the P0/P1 pair and the bid MC.

    Attributes:
        r0: The P0 (base-cost) result; its dispatch sets the per-month run
            lengths that size the startup amortization.
        p1: The P1 (bid-cost) result — THE main clearing solve (CLAUDE.md:
            the production/forecast path and what every keeper is scored on).
        mc_bid: ``mc_base + markup`` — the bid-cost objective P1 solved; the
            optional P2 commitment re-solve prices at this same MC.
        markup: The ``(n_gen, T)`` monthly startup-amortization markup.
    """

    r0: "DispatchResult"
    p1: "DispatchResult"
    mc_bid: np.ndarray
    markup: np.ndarray


def run_energy_solve(
    fleet,
    fleet_arrays: "FleetArrays",
    demand: np.ndarray,
    mc_base: np.ndarray,
    dispatch_kwargs: dict,
    config,
    *,
    xyear_cache: Optional[list] = None,
) -> EnergySolveResult:
    """Run the shared P0 → markup → P1 energy solve (both orchestrators).

    Args:
        fleet: The dispatch fleet (``list[Generator]``), aligned row-for-row
            with ``fleet_arrays`` — the run-length source for the markup.
        fleet_arrays: The vectorized fleet the LP consumes.
        demand: Zonal hourly demand ``(n_zones, T)``.
        mc_base: The ``(n_gen, T)`` base marginal cost (full variable cost +
            EACs + coal tranche discounts + interchange injections) — the P0
            objective and the P1 bid basis.
        dispatch_kwargs: The assembled LP kwargs
            (``pipeline.kwargs.build_base_dispatch_kwargs`` + the gated
            per-orchestrator updates + ``apply_reserve_coopt``).
        config: ScenarioConfig — supplies ``hours`` and the startup-markup
            behavior gates (``gas_st_startup_spread``, ``gas_st_startup_cost``,
            ``chp_startup_covered``, ``coal_warm_committed``; all default-off
            fields, so the forecast path — which never set them before — is
            unchanged at defaults and now honors them when a config sets them).
        xyear_cache: Optional single-element list carrying the prior year's
            exported basis (backcast year loop). ``None`` (forecast) disables
            both the cross-year apply and the export — see module docstring.

    Returns:
        :class:`EnergySolveResult` with the P0/P1 results and the bid MC.
    """
    _warm = os.environ.get("MARKET_SIM_WARMSTART", "1") != "0"
    model = DispatchModel(fleet_arrays, demand, **dispatch_kwargs) if _warm else None
    _xwarm = _warm and os.environ.get("MARKET_SIM_WARMSTART_XYEAR", "0") != "0"
    if _xwarm and xyear_cache is not None and xyear_cache:
        model.apply_cross_year_basis(xyear_cache[0])
    # P0: solve with base MC to extract per-month run lengths.
    if _warm:
        r0 = model.solve(mc=mc_base)
    else:
        r0 = solve_dispatch(fleet_arrays, demand, mc=mc_base, **dispatch_kwargs)
    # P1: solve with bid MC = base MC + monthly startup amortization, so
    # clearing prices reflect CC/CT cycling costs.
    markup = compute_monthly_markup(
        fleet,
        fleet_arrays,
        r0.dispatch,
        config.hours,
        gas_st_season_spread=config.gas_st_startup_spread,
        gas_st_startup_cost=getattr(config, "gas_st_startup_cost", False),
        chp_startup_covered=getattr(config, "chp_startup_covered", False),
        coal_warm_committed=getattr(config, "coal_warm_committed", False),
    )
    mc_bid = mc_base + markup
    if _warm:
        p1 = model.solve(mc=mc_bid)
    else:
        p1 = solve_dispatch(fleet_arrays, demand, mc=mc_bid, **dispatch_kwargs)

    # Hand this year's optimal basis to the next year's P0 (cross-year warm
    # start). Stored even when the flag is off so a downstream A/B does not
    # depend on call ordering; only consumed when MARKET_SIM_WARMSTART_XYEAR=1.
    if _warm and xyear_cache is not None:
        basis = model.export_cross_year_basis()
        if basis is not None:
            xyear_cache[:] = [basis]

    return EnergySolveResult(r0=r0, p1=p1, mc_bid=mc_bid, markup=markup)


__all__ = ["EnergySolveResult", "run_energy_solve"]
