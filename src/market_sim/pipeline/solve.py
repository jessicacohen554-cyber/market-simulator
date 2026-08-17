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
ordering) and leaves ``xyear_warmstart=None``, so its gate stays the
``MARKET_SIM_WARMSTART_XYEAR`` env var the calibration CLIs default ON.

The forecast front-end (``runner.run_scenario_iso``) threads a cache only when
``ScenarioConfig.forecast_xyear_warmstart`` is armed, and passes that same flag
as ``xyear_warmstart`` so the forecast's cross-year behavior is a registry field
rather than an env-var knob (rule 24 [R-REGISTRY]). It is default-OFF, so the
forecast path is cold-only unless a config arms it. The historical blocker — the
≤0.0033% marginal-tie reshuffle being read by the per-unit economic retirement
screen, which could tip a retire/keep decision and change the *next* year's
fleet — was closed by wave 4C: the screen now prices the attainable pro-forma
margin and credits attribute revenue on attainable in-merit generation, so it is
a function of prices, ``mc`` and capacity only
(``tests/test_forecast_warmstart_tie_invariance.py``,
``docs/cross-year-warmstart.md``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import numpy as np

from market_sim.model.commitment import compute_monthly_markup
from market_sim.model.dispatch import DispatchModel, solve_dispatch
from market_sim.model.lp.inplace_floor import (
    availability_feeds_rows,
    refloor_thermal_inplace,
)
from market_sim.pipeline.basis_cache import persist_year_basis, seed_year1_basis

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
        p1_fleet_arrays: The ``FleetArrays`` P1 actually solved on. Identical to
            the input ``fleet_arrays`` on every ordinary path; when a
            ``p1_fleet_prep`` hook injects a floor (the P1-native CAISO RA
            must-offer bridge), this is the floored fleet the scored P1 saw, so
            the caller persists its ``min_gen`` as the P1 pass's floors.
    """

    r0: "DispatchResult"
    p1: "DispatchResult"
    mc_bid: np.ndarray
    markup: np.ndarray
    p1_fleet_arrays: "FleetArrays"


def apply_bid_max_target(mc_bid: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Reconcile a P1 bid with a measured bid LEVEL — ``max``, never ``+``.

    The one arithmetic the P1 bid-max seam performs, factored out so the
    "never additive" contract is a testable property rather than an inline
    expression. A row-hour carrying a positive ``target`` clears at whichever
    of the two is higher; a non-positive (or non-finite) target is a no-op, so
    an uncovered row-hour keeps the bid the rest of the stack produced.

    This is the rule-19 reconciliation the PJM CT_FAST reprice needs: the
    pjm-103 start-cost amortization keeps ownership wherever it already prices
    the row above the measured corpus, and the measured level binds only where
    the model is cheaper. Adding the two instead is the pjm-101/102 stacking
    that over-expressed (CT -12 TWh).

    Args:
        mc_bid: ``(n_gen, T)`` P1 bid after the markup and every additive
            adjustment.
        target: ``(n_gen, T)`` measured bid level; ``<= 0`` / non-finite
            entries are no-ops.

    Returns:
        A new ``(n_gen, T)`` bid array; ``mc_bid`` is not mutated.
    """
    binding = np.isfinite(target) & (target > 0.0)
    return np.where(binding, np.maximum(mc_bid, target), mc_bid)


def run_energy_solve(
    fleet,
    fleet_arrays: "FleetArrays",
    demand: np.ndarray,
    mc_base: np.ndarray,
    dispatch_kwargs: dict,
    config,
    *,
    xyear_cache: Optional[list] = None,
    xyear_warmstart: Optional[bool] = None,
    p1_fleet_prep=None,
    p1_kwargs_prep=None,
    mc_bid_adjust: Optional[np.ndarray] = None,
    p1_bid_adjust_prep=None,
    p1_bid_max_target: Optional[np.ndarray] = None,
    startup_run_ratio_t: Optional[np.ndarray] = None,
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
            exported basis (backcast year loop; the forecast year loop when
            ``ScenarioConfig.forecast_xyear_warmstart`` is armed). ``None``
            disables both the cross-year apply and the export — see module
            docstring.
        xyear_warmstart: Optional explicit cross-year warm-start gate. ``None``
            (every backcast caller) defers to ``MARKET_SIM_WARMSTART_XYEAR``,
            exactly as before. A bool is the CALLER's authoritative decision and
            overrides the env var — the forecast front-end passes
            ``ScenarioConfig.forecast_xyear_warmstart`` so the forecast's
            cross-year behavior is a registry field (rule 24 [R-REGISTRY]) and
            never an env-var knob. Passing a bool also bypasses the persisted
            year-1 basis NPZ cache (``pipeline.basis_cache``): that cache is
            keyed ``(iso, weather_year, hours)``, which does not distinguish a
            forecast's sim-years, so seeding a forecast horizon from it would
            make a run depend on what solved before it. An explicitly-gated
            caller therefore warm-starts only from bases produced INSIDE its own
            run.
        p1_fleet_prep: Optional callable ``(r0) -> Optional[FleetArrays]`` invoked
            after P0 solves. When it returns a ``FleetArrays`` the P1 solve uses
            that (floored) fleet instead of the input one — the P1-native CAISO RA
            must-offer bridge injects its ``min_gen`` floor here, detected from the
            P0 dispatch. The floor is only a P-block column-bound change: with
            ``MARKET_SIM_P1_FLOOR_INPLACE=1`` P1 mutates those bounds on the live
            P0 model (``lp.inplace_floor.refloor_thermal_inplace``) and warm-solves
            from the P0 basis; by default (or when the model declines the in-place
            edit) P1 cold-rebuilds on the floored fleet. Either way P1 clears the
            same floored LP — the two differ only by marginal-tie reshuffle (the
            shipped warm-start neutrality standard). Every other path (hook
            ``None`` or returning ``None``) is byte-identical, warm start included.
        p1_bid_max_target: Optional ``(n_gen, T)`` measured bid LEVEL applied
            as ``mc_bid = max(mc_bid, target)`` AFTER the startup markup and
            every additive bid adjustment — the PJM CT_FAST measured reprice
            (``pjm_ct_measured_max_reprice``), a rule-19 reconciliation with
            the start-cost amortization rather than a second additive
            mechanism. Entries <= 0 are no-ops; ``None`` (every flag-off
            path) is byte-identical.
        startup_run_ratio_t: Optional ``(T,)`` condition-keyed amortization
            horizon ratio (``tranche_startup_conditional_runs`` v4), passed
            through to ``compute_monthly_markup`` — the fast-start measured
            run ceiling scales per hour by the hour's net-load-percentile
            band ratio. ``None`` (every flag-off / non-artifact path) keeps
            the v3 markup byte-identical.
        p1_kwargs_prep: Optional callable ``(r0, p1_fleet_arrays) ->
            Optional[dict]`` invoked after ``p1_fleet_prep`` resolves. A returned
            dict is merged over ``dispatch_kwargs`` for the P1 solve only — the
            PJM commitment-scoped reserve supply (path B) recomputes its
            deliverable ``reserve_supply_cap`` on the masked fleet here. Like a
            fleet replacement, a kwargs override precludes the warm-start basis
            reuse (the LP rows change), so that P1 is a cold solve; ``None`` (or
            a hook returning ``None``/empty) is byte-identical.

    Returns:
        :class:`EnergySolveResult` with the P0/P1 results, the bid MC, and the
        ``FleetArrays`` P1 solved on.
    """
    _warm = os.environ.get("MARKET_SIM_WARMSTART", "1") != "0"
    model = DispatchModel(fleet_arrays, demand, **dispatch_kwargs) if _warm else None
    # Cross-year gate: an explicit ``xyear_warmstart`` bool is the caller's own
    # decision and wins; ``None`` (every backcast caller) keeps the env default,
    # so the backcast path is byte-identical to before.
    if xyear_warmstart is None:
        _xwarm = _warm and os.environ.get("MARKET_SIM_WARMSTART_XYEAR", "0") != "0"
    else:
        _xwarm = _warm and bool(xyear_warmstart)
    # Persisted year-1 basis cache key (plan §7 H2). backcast_config pins
    # config.iso/weather_year/hours to the solved (ISO, year, T). An
    # explicitly-gated caller (the forecast) opts OUT of the disk cache: its
    # key carries no sim-year, so a 25-year forecast horizon would seed every
    # year from whatever solved last for that (iso, weather_year, T) and one
    # run's basis would leak into the next. In-run cross-year warm start is
    # unaffected; only the cross-INVOCATION seed/persist is skipped.
    _disk_basis_cache = xyear_warmstart is None
    _basis_key = (
        getattr(config, "iso", ""),
        getattr(config, "weather_year", 0),
        getattr(config, "hours", 0),
    )
    # Seed an empty cross-year cache from the newest basis persisted for this
    # ISO-year so the P0 below warm-starts instead of solving cold (year-1, or
    # the first fresh year after a --reuse-solved gap). A no-op when the holder
    # is None (forecast) / non-empty (in-run warm) / the gate is off
    # (goldens/replay); opportunistic and basis-neutral — apply_cross_year_basis
    # remaps/repairs and falls back cold, so a stale seed costs iterations only.
    if _disk_basis_cache:
        seed_year1_basis(xyear_cache, *_basis_key)
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
        run_ratio_t=startup_run_ratio_t,
    )
    mc_bid = mc_base + markup
    # P1-only bid adjustment (ERCOT condition-responsive offer surface): an additive
    # (n_gen, T) markup applied to the P1 clearing objective ONLY — never to the P0
    # base cost — so the surface reprices the gas peak-band scarcity wall in the
    # clearing price without perturbing P0 run lengths (and thus the startup-
    # amortization coupling). None (every non-ERCOT / flag-off path) is byte-identical.
    if mc_bid_adjust is not None:
        mc_bid = mc_bid + mc_bid_adjust
    # P0-conditioned P1-only bid adjustment (ERCOT low-curve leg): the hook reads
    # the P0 solution — the model's own commitment discovery — and returns an
    # additive (n_gen, T) adjustment for the P1 clearing objective (e.g. the
    # committed-unit LSL markdown gated to plant-hours the plant runs in P0, the
    # CAISO-RA/PJM-path-B forward-regenerating construction). Objective-only:
    # the warm-start basis reuse is unaffected. None (every flag-off path) is
    # byte-identical.
    if p1_bid_adjust_prep is not None:
        _extra_bid_adjust = p1_bid_adjust_prep(r0)
        if _extra_bid_adjust is not None:
            mc_bid = mc_bid + _extra_bid_adjust
    # P1-only bid MAX seam (PJM CT_FAST measured reprice): an (n_gen, T) measured
    # bid LEVEL that RECONCILES with — never adds to — everything above it. The
    # bid becomes max(bid, target), so a row already priced above the measured
    # corpus by its startup amortization keeps that price and the measured level
    # binds only where the model is cheaper (rule 19: replacement, not stacking —
    # the pjm-101/102 failure was exactly this level applied additively against
    # mc_base alone). Deliberately LAST, after the markup and both additive
    # adjustments, so "the full P1 bid" is what the max() is taken against.
    # Zero/absent entries are no-ops; None (every flag-off path) is byte-identical.
    if p1_bid_max_target is not None:
        mc_bid = apply_bid_max_target(mc_bid, p1_bid_max_target)
    # P1-native floor injection (CAISO RA must-offer bridge, ERCOT gas
    # commitment bridge): the hook reads the P0 solution and returns a floored
    # fleet for the P1 clearing solve. The floor enters the LP only as the
    # thermal P-block column bounds (min_gen -> lower, pmax*availability ->
    # upper), so it can ride into P1 one of two ways:
    #   * IN-PLACE (opt-in: MARKET_SIM_P1_FLOOR_INPLACE=1) —
    #     ``lp.inplace_floor.refloor_thermal_inplace`` mutates the P[g,t] bounds on
    #     the LIVE P0 model (``changeColsBounds``) and P1 re-solves from the P0
    #     basis: the exact analogue of the ``changeColsCost`` P0->P1 re-cost.
    #     No second matrix build, so peak RSS stays ~one model. It DECLINES
    #     (falls back to cold) when the floored availability also feeds a
    #     ramp/co-opt row that a P-column edit can't reproduce.
    #   * COLD REBUILD (default; MARKET_SIM_P1_FLOOR_INPLACE unset/0) — build a
    #     second DispatchModel on the floored fleet and solve it cold. The
    #     pre-2026-07 behaviour, kept as the default so the byte-identity gate
    #     sees an unchanged default solve path (refactor-consolidation plan
    #     §7 H-1: the in-place path is a warm-start-class change validated by
    #     scripts/diagnostics/diff_warmstart_bundles.py, not by --mode byte; flipping the
    #     default is an owner cache-epoch decision on that tie-only evidence).
    # Either way P1 clears the SAME floored LP; the two paths differ only by
    # marginal-tie reshuffle (the shipped warm-start neutrality standard). The
    # ordinary path (hook None / no floor) keeps the warm start and is
    # byte-identical to before. The env toggle is a solve-path perf knob, not a
    # ScenarioConfig field, so it never enters ``cache_key``.
    p1_fleet_arrays = fleet_arrays
    if p1_fleet_prep is not None:
        replaced = p1_fleet_prep(r0)
        if replaced is not None:
            p1_fleet_arrays = replaced
    # P1-only kwargs overrides (e.g. the PJM path-B deliverable reserve-supply
    # cap recomputed on the masked fleet). ``None``/empty keeps the shared
    # kwargs object, preserving the warm-start identity check below.
    p1_dispatch_kwargs = dispatch_kwargs
    if p1_kwargs_prep is not None:
        overrides = p1_kwargs_prep(r0, p1_fleet_arrays)
        if overrides:
            p1_dispatch_kwargs = {**dispatch_kwargs, **overrides}
    _warm_p1 = (
        _warm
        and p1_fleet_arrays is fleet_arrays
        and p1_dispatch_kwargs is dispatch_kwargs
    )
    # In-place floor re-solve: applies only when the P1 change is a pure
    # floored-fleet swap (a live warm model, a replaced fleet, no kwargs
    # override). Mutate the P-block bounds on the live model and warm-solve;
    # if the toggle is off or the model declines the edit, fall through to the
    # cold rebuild below.
    _inplace_floored = False
    if (
        _warm
        and not _warm_p1
        and p1_fleet_arrays is not fleet_arrays
        and p1_dispatch_kwargs is dispatch_kwargs
        and os.environ.get("MARKET_SIM_P1_FLOOR_INPLACE", "0") != "0"
    ):
        _rgi = dispatch_kwargs.get("ramp_gen_idx")
        _avail_in_rows = availability_feeds_rows(
            model, _rgi is not None and np.asarray(_rgi).size > 0
        )
        _inplace_floored = refloor_thermal_inplace(
            model, p1_fleet_arrays, _avail_in_rows
        )
    if _warm_p1 or _inplace_floored:
        p1 = model.solve(mc=mc_bid)
    else:
        # Cold P1 on a replaced fleet / overridden kwargs / declined in-place
        # edit: export the cross-year basis from the P0 model FIRST (same value
        # as the post-P1 export below — the model last solved P0 either way),
        # then release the P0 LP + HiGHS workspace before building the second
        # DispatchModel, so peak RSS stays ~one model (the PJM zone-aggregate
        # co-opt alone peaks ~14.5 GB on the 15 GB calibration box).
        if _xwarm and xyear_cache is not None:
            basis = model.export_cross_year_basis()
            if basis is not None:
                xyear_cache[:] = [basis]
        model = None
        p1 = solve_dispatch(p1_fleet_arrays, demand, mc=mc_bid, **p1_dispatch_kwargs)

    # Hand this year's optimal basis to the next year's P0 (cross-year warm
    # start). Exported only when the cross-year gate is armed (`_xwarm`) —
    # its ONLY consumers are the next year's apply (same gate) and the
    # persisted year-1 NPZ cache (`basis_cache_enabled()`, the same gate
    # again; `persist_year_basis` no-ops on the empty holder). Under the
    # goldens/replay determinism env (MARKET_SIM_WARMSTART_XYEAR=0) the
    # export was stored and never read, at ~10-16 s/yr of pure `getBasis()`
    # enum materialization (13.2 M pybind objects) — PERF-B, perf-recheck
    # §2.7. Skipping it cannot touch the solve: the export runs after the
    # solves and only reads the model. An explicitly-gated forecast caller
    # still exports on its final horizon year (the year count is not
    # visible here) — one wasted export per run, accepted.
    if _xwarm and model is not None and xyear_cache is not None:
        basis = model.export_cross_year_basis()
        if basis is not None:
            xyear_cache[:] = [basis]

    # Persist this year's optimal basis to the disposable NPZ cache (plan §7 H2)
    # so the next calibrate-iterate run for this (iso, year, T) seeds a warm
    # year-1 P0. xyear_cache now holds this year's basis (both the warm-P1 and
    # cold-P1 paths above refresh it); persisting per-year is crash-safe. A
    # gate-OFF / None-holder is handled inside persist_year_basis, so the
    # goldens/replay env retains nothing and the solve stays byte-identical.
    if _disk_basis_cache:
        persist_year_basis(xyear_cache, *_basis_key)

    return EnergySolveResult(
        r0=r0, p1=p1, mc_bid=mc_bid, markup=markup, p1_fleet_arrays=p1_fleet_arrays
    )


__all__ = ["EnergySolveResult", "apply_bid_max_target", "run_energy_solve"]
