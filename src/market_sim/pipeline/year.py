"""Shared per-year solve body for the forecast and backcast orchestrators.

Orchestrator-unification lane (refactor-consolidation plan §5): after Stages
2-6 shared the *called* seams (base kwargs, reserve co-opt, P0/P1 solve, P2
commitment, interchange, fleet build), the calling sequence itself — the
gated dispatch-kwargs add-on blocks, the reserve/commitment-posture wiring,
the four P1-native prep hooks, the energy solve, and the post-solve fleet /
context bookkeeping — was still duplicated near-verbatim in ``runner.py``
(forecast) and ``scripts/run_calibration.py::run_year`` (backcast).
:func:`run_year_solve` is that sequence, hoisted statement-for-statement.

**Preserved asymmetries** (each an explicit keyword, defaulted to the
forecast-neutral value):

* ``xyear_cache`` — the backcast threads its year-loop cache; the forecast
  front-end passes a literal ``None`` so cross-year warm-start can never
  reach the forecast trajectory (``tests/test_xyear_warmstart_default.py``
  statically asserts the runner call site; plan §8).
* ``mc_bid_adjust`` / ``lowcurve_bid_adjust_prep`` / ``startup_run_ratio_t``
  — the backcast's measured offer-surface machinery; ``None`` on the
  forecast (byte-identical to the pre-extraction omitted kwargs, whose
  ``run_energy_solve`` defaults are ``None``).
* ``ra_renewable_potential_mw`` — the backcast passes the year's renewable
  potential into the CAISO RA bridge; the forecast historically omitted it
  (the hook's default). Preserved as-is; reconciling it is a rule-14 open
  item, not a refactor decision.
* ``floorscoped_markdown_fn`` — each front-end builds its own closure from
  its own fuel-price/net-load locals; the hook wiring is shared here.

Measured backcast overlays never enter this module: they are applied by the
backcast front-end to ``dispatch_kwargs`` / the fleet *before* this call
(storage AS floors, maxgen tier slack, TTC overlays), so the forecast cannot
reach them (CLAUDE.md rule 13).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import numpy as np

from market_sim.model.dispatch import DispatchResult  # noqa: F401  (typing/docs)
from market_sim.pipeline.commitment import (
    build_caiso_ra_p1_prep,
    build_caiso_reserve_p1_prep,
    build_ercot_gas_bridge_p1_preps,
    build_pjm_reserve_p1_prep,
)
from market_sim.pipeline.kwargs import (
    apply_ercot_commitment_posture,
    apply_reserve_coopt,
)
from market_sim.pipeline.solve import EnergySolveResult, run_energy_solve
from market_sim.policy.constraints import build_mass_cap_dispatch_kwargs
from market_sim.results.outputs import FleetContext

if TYPE_CHECKING:  # pragma: no cover - typing only
    from market_sim.data.fleet import FleetArrays

logger = logging.getLogger(__name__)

__all__ = ["YearSolveOutput", "run_year_solve"]


@dataclass
class YearSolveOutput:
    """What the shared per-year solve hands back to a front-end.

    Attributes:
        energy_solve: The full :class:`EnergySolveResult` (r0/p1/mc_bid/markup
            + the P1 fleet seam).
        result: The P1 dispatch result — THE scored pass (CLAUDE.md
            "Dispatch & Commitment").
        mc_bid: The P1 bid-cost matrix (base + amortized startup markup).
        fleet_arrays: The fleet P1 actually solved on — the RA/bridge-floored
            fleet when a P1-native prep fired, else the input fleet unchanged.
        context: ``FleetContext`` built from that P1 fleet.
        reserve_design: The co-opt's resolved reserve design (``None`` when
            the co-opt is off / CAISO-excluded) — the backcast's post-solve
            ORDC machinery reads it.
        t_solve_start: ``time.perf_counter()`` immediately before the energy
            solve (after the prep hooks were built).
        t_solve_end: ``time.perf_counter()`` immediately after.
    """

    energy_solve: EnergySolveResult
    result: "DispatchResult"
    mc_bid: np.ndarray
    fleet_arrays: "FleetArrays"
    context: FleetContext
    reserve_design: object | None
    t_solve_start: float
    t_solve_end: float


def run_year_solve(
    fleet,
    fleet_arrays: "FleetArrays",
    demand: np.ndarray,
    mc_base: np.ndarray,
    dispatch_kwargs: dict,
    config,
    *,
    iso: str,
    year: int,
    iso_config,
    zone_names,
    wind_cf: np.ndarray,
    wind_cap: np.ndarray,
    solar_cf: np.ndarray,
    solar_cap: np.ndarray,
    storage_zone_idx,
    storage_power_cap,
    storage_energy_cap,
    storage_tech_names,
    hydro_gen_idx,
    xyear_cache: Optional[list],
    ra_renewable_potential_mw: Optional[np.ndarray] = None,
    floorscoped_markdown_fn=None,
    mc_bid_adjust: Optional[np.ndarray] = None,
    lowcurve_bid_adjust_prep=None,
    startup_run_ratio_t: Optional[np.ndarray] = None,
) -> YearSolveOutput:
    """Run the shared per-year body: gated kwargs add-ons → reserve co-opt →
    P1-native prep hooks → P0/P1 energy solve → P1 fleet/context bookkeeping.

    ``dispatch_kwargs`` arrives with the base assembly (and any mode-specific
    extras the front-end merged first) and is extended IN PLACE — the same
    dict the caller passed keeps flowing into its P2/persistence seams.

    Args:
        fleet: The dispatch fleet (``list[Generator]``), row-aligned with
            ``fleet_arrays``.
        fleet_arrays: The vectorized fleet the LP consumes.
        demand: ``(n_zones, T)`` zonal demand.
        mc_base: ``(n_gen, T)`` base marginal cost.
        dispatch_kwargs: The base dispatch kwargs (mutated in place).
        config: The resolved ``ScenarioConfig``.
        iso: ISO name (uppercase).
        year: Simulation year.
        iso_config: The finalized ISO topology.
        zone_names: The solve's runtime zone list.
        wind_cf: ``(n_zones, T)`` wind capacity factors.
        wind_cap: ``(n_zones,)`` wind capacity.
        solar_cf: ``(n_zones, T)`` solar capacity factors (the year's
            deliverability-adjusted profile on either path).
        solar_cap: ``(n_zones,)`` solar capacity.
        storage_zone_idx: Storage zone index array.
        storage_power_cap: Storage power caps — the backcast may pass a
            measured-capability re-based copy, the forecast the builder's.
        storage_energy_cap: Storage energy caps (context construction).
        storage_tech_names: Storage tech names (pumped-storage detection for
            the hydro envelope).
        hydro_gen_idx: Hydro unit indices (``None``/empty → no hydro blocks).
        xyear_cache: Cross-year warm-start cache — the backcast's year-loop
            list, or ``None`` (forecast: ALWAYS ``None``, see module docstring).
        ra_renewable_potential_mw: Backcast-only CAISO RA-bridge input.
        floorscoped_markdown_fn: ERCOT-64 floor-scoped LSL markdown closure.
        mc_bid_adjust: Backcast measured offer-surface bid adder.
        lowcurve_bid_adjust_prep: Backcast v2 lowcurve bid hook (mutually
            exclusive with the ERCOT bridge bid hook — rule 19, enforced at
            ``build_ercot_gas_bridge_p1_preps``).
        startup_run_ratio_t: Backcast startup-run-ratio series for the markup.

    Returns:
        A :class:`YearSolveOutput`; ``dispatch_kwargs`` has been extended in
        place with every gated add-on that fired.
    """
    # Emissions mass-cap rows (policy constraint path, gated; G-29): shared
    # seam for both orchestrators. Default off -> {} -> no dispatch_kwargs
    # change, identical LP. See docs/handoffs/emissions-mass-cap-plan-2026-07.md.
    dispatch_kwargs.update(
        build_mass_cap_dispatch_kwargs(config, year, zone_names, fleet_arrays)
    )

    # Plant-group hourly ramp envelopes (config.ramp_limits, GATED default
    # off): CAMPD-measured trajectory bounds per plant group per hour
    # transition (model/dispatch._build_ramp_rows; design
    # docs/ramp-locational-design-2026-07.md §1). One body, both orchestrators
    # (forecast parity, design §4). No-op (identical LP) when off or when the
    # ISO has no committed envelope artifact.
    if getattr(config, "ramp_limits", False):
        from market_sim.data.fleet import build_ramp_groups

        ramp_groups = build_ramp_groups(fleet_arrays, iso)
        if ramp_groups is not None:
            r_gen_idx, r_group_col, r_up, r_dn = ramp_groups
            dispatch_kwargs.update(
                ramp_gen_idx=r_gen_idx,
                ramp_group_col=r_group_col,
                ramp_up_mw=r_up,
                ramp_dn_mw=r_dn,
            )
            logger.info(
                "%s %d: ramp envelopes on %d plant groups (%d member tranches)",
                iso,
                year,
                r_up.size,
                r_gen_idx.size,
            )

    # Local-capacity (LCR-area) minimum-generation rows
    # (config.local_capacity_constraints, GATED default off): published-study
    # load-pocket relaxation (design §3), RHS from the LCR report parameters
    # scaled by this year's zonal load shape. One body, both orchestrators.
    # No-op when off or the ISO has no covered areas / crosswalk.
    if getattr(config, "local_capacity_constraints", False):
        from market_sim.data.local_capacity import build_local_capacity_specs

        lcr_specs, _lcr_meta = build_local_capacity_specs(
            iso,
            year,
            fleet_arrays.plant_code,
            fleet_arrays.pmax,
            fleet_arrays.availability,
            zone_names,
            demand,
            storage_zone_idx,
            storage_power_cap,
        )
        if lcr_specs:
            dispatch_kwargs.update(local_capacity_specs=lcr_specs)

    # Hydro hourly deliverability envelope (config.hydro_dispatch_envelope,
    # GATED default off): fleet-wide hourly ceiling at the measured
    # per-(month x hod) percentile of EIA-930 NG:WAT — bounds the budget LP's
    # perfect-foresight hoarding of the monthly hydro energy into the top
    # price hours (caiso-72 STEP-2; FINDING-caiso72-step0). One body, both
    # orchestrators (a forecast year falls back to the pooled climatology
    # envelope inside the loader). No-op (identical LP) when off, no hydro
    # fleet, or no measured series.
    if (
        getattr(config, "hydro_dispatch_envelope", False)
        and hydro_gen_idx is not None
        and len(hydro_gen_idx)
    ):
        from market_sim.data.eia_loader import measured_hydro_hourly_envelope

        env = measured_hydro_hourly_envelope(iso, year, config.hours)
        if env is not None:
            # Feasibility guard: never cap below the fleet's own hourly lower
            # bounds (min_gen floors / pmin).
            h_idx = np.asarray(hydro_gen_idx, dtype=int)
            if getattr(fleet_arrays, "min_gen", None) is not None:
                lo = fleet_arrays.min_gen[h_idx, : config.hours].sum(axis=0)
            else:
                lo = np.full(config.hours, fleet_arrays.pmin[h_idx].sum())
            env = np.maximum(env, lo)
            # CISO's NG:WAT includes pumped-storage net output (no separate
            # PS series), so the capped model quantity includes PS net
            # discharge — like-for-like with the measured envelope.
            ps_idx = np.flatnonzero(
                np.char.startswith(np.asarray(storage_tech_names, dtype=str), "pumped")
            )
            dispatch_kwargs.update(
                hydro_envelope_gen_idx=h_idx,
                hydro_envelope_mw=env,
                hydro_envelope_storage_idx=(ps_idx if ps_idx.size else None),
            )
            logger.info(
                "%s %d: hydro deliverability envelope on %d units "
                "(evening p95 %.0f MW)",
                iso,
                year,
                h_idx.size,
                float(np.quantile(env, 0.95)),
            )

    # Energy+reserve co-optimization: the shared pipeline wrapper (Stage 2) —
    # per-ISO reserve designs live in config/reserve_config.py; the wrapper
    # owns the gate (energy_reserve_coopt, CAISO excluded), the forward-driver
    # threading, the merge, and the logging. sim_year=year is value-identical
    # on the backcast (weather_year == year under the pin; every sim_year
    # consumer falls back to weather_year).
    reserve_design = apply_reserve_coopt(
        dispatch_kwargs,
        config,
        fleet_arrays,
        config.hours,
        zone_names,
        system_load=demand.sum(axis=0),
        wind_gen=(wind_cap[:, None] * wind_cf).sum(axis=0),
        solar_gen=(solar_cap[:, None] * solar_cf).sum(axis=0),
        sim_year=year,
    )
    # ERCOT standalone energy-only commitment-posture (reserve-decoupled;
    # docs/handoffs/ercot-commitment-thinness-2026-07.md). No-op /
    # byte-identical for every non-ERCOT run and default-off ERCOT.
    apply_ercot_commitment_posture(dispatch_kwargs, config, fleet_arrays)

    # P1-native CAISO RA must-offer bridge (P2 archived — CLAUDE.md: P0/P1
    # only): floor the merchant gas CC/CT fleet from the P0 run pattern before
    # the P1 clearing solve, so the scored P1 carries the RA structure. None
    # for every non-CAISO / non-RA run (byte-identical).
    ra_p1_prep = build_caiso_ra_p1_prep(
        config,
        iso,
        fleet,
        fleet_arrays,
        mc_base,
        renewable_potential_mw=ra_renewable_potential_mw,
    )
    # P1-native ERCOT gas commitment bridge (ERCOT-63): committed-state floor
    # on merchant gas-CC from the P0 run pattern — the ISO-exclusive sibling
    # of the CAISO hook. (None, None) for every non-ERCOT / gate-off run
    # (byte-identical). ERCOT-64 floor-scoped committed-LSL markdown: the
    # measured LSL bid on exactly the bridge's floored plant-hours — the bid
    # hook shares the bridge's ONE floor computation.
    ercot_bridge_prep, ercot_bridge_bid_prep = build_ercot_gas_bridge_p1_preps(
        config,
        iso,
        fleet,
        fleet_arrays,
        mc_base,
        floorscoped_markdown_fn=floorscoped_markdown_fn,
    )
    # P1-native PJM commitment-scoped reserve supply (path B, G-20b): fa_p2-
    # style availability mask from the P0 run pattern + the deliverable supply
    # cap recomputed on the masked fleet. (None, None) for every non-PJM /
    # gate-off run (byte-identical); ISO-exclusive with the CAISO hook, so at
    # most one fleet prep is ever non-None. Forward-regenerating by
    # construction — the commitment state is the model's own P0 solve.
    pjm_fleet_prep, pjm_kwargs_prep = build_pjm_reserve_p1_prep(
        config, iso, fleet_arrays
    )
    # P1-native CAISO online-scoped reserve split (caiso_reserve_online_scoped):
    # the kwargs hook recomputes the (2*n_r, T) spin/non-spin product-split
    # ramp caps from the P0 run pattern — SPIN scoped to online iron, NONSPIN
    # to offline fast-start. None for every non-CAISO / gate-off run
    # (byte-identical); ISO-exclusive with the PJM kwargs hook. Composes with
    # the CAISO RA-bridge fleet hook.
    caiso_reserve_kwargs_prep = build_caiso_reserve_p1_prep(config, iso, fleet_arrays)

    t_solve_start = time.perf_counter()
    energy_solve = run_energy_solve(
        fleet,
        fleet_arrays,
        demand,
        mc_base,
        dispatch_kwargs,
        config,
        xyear_cache=xyear_cache,
        p1_fleet_prep=ra_p1_prep or ercot_bridge_prep or pjm_fleet_prep,
        p1_kwargs_prep=pjm_kwargs_prep or caiso_reserve_kwargs_prep,
        mc_bid_adjust=mc_bid_adjust,
        # The v2 lowcurve and the ERCOT-64 floor-scoped bid hooks are mutually
        # exclusive (rule 19, enforced at build_ercot_gas_bridge_p1_preps), so
        # at most one is non-None here.
        p1_bid_adjust_prep=lowcurve_bid_adjust_prep or ercot_bridge_bid_prep,
        startup_run_ratio_t=startup_run_ratio_t,
    )
    t_solve_end = time.perf_counter()
    result = energy_solve.p1
    mc_bid = energy_solve.mc_bid
    # The fleet P1 actually solved on — the RA/bridge-floored fleet when a
    # prep fired, else the input fleet unchanged. Persist ITS min_gen as the
    # P1 pass's floors and expose it downstream (D-2 forced-energy
    # attribution).
    fleet_arrays = energy_solve.p1_fleet_arrays
    context = FleetContext.from_arrays(
        fleet_arrays,
        iso_config,
        wind_cf,
        wind_cap,
        solar_cf,
        solar_cap,
        storage_energy_cap,
    )
    return YearSolveOutput(
        energy_solve=energy_solve,
        result=result,
        mc_bid=mc_bid,
        fleet_arrays=fleet_arrays,
        context=context,
        reserve_design=reserve_design,
        t_solve_start=t_solve_start,
        t_solve_end=t_solve_end,
    )
