"""Shared solve-core package for the forecast and backcast orchestrators.

This package is the destination of the orchestrator-unification plan
(``docs/handoffs/orchestrator-unification-plan-2026-07.md``): the per-year
LP solve — today duplicated near-verbatim in ``runner.py`` (forecast) and
``scripts/run_calibration.py`` (backcast) — migrates here stage by stage so
both orchestrators call one shared core.

**Stage 1 (this commit) delivers only the typed contract objects**, no solve
code yet:

- :class:`~market_sim.pipeline.spec.DispatchSpec` — a frozen bundle of the base
  ``dispatch_kwargs`` the LP builder consumes, with ``to_dispatch_kwargs()``.
- :class:`~market_sim.pipeline.spec.ReserveSpec` — a typed wrapper over the dict
  ``reserve_config.build_reserve_dispatch_kwargs`` returns, with ``merge_into()``.
- :class:`~market_sim.pipeline.prior.PriorYearResults` — a typed replacement for
  the untyped cross-year ``prior_results`` dict threaded through ``runner.py``'s
  year loop (audit AR-2). Dict-style ``.get`` / ``__getitem__`` shims keep every
  existing reader working during the migration.

None of these change any solved number; Stage 1 is pure typing + scaffolding.

**Stage 2 adds ``kwargs.py``** — the shared base ``dispatch_kwargs`` assembly
(:func:`~market_sim.pipeline.kwargs.build_base_dispatch_kwargs`) and the reserve
co-optimization wrapper (:func:`~market_sim.pipeline.kwargs.apply_reserve_coopt`)
— now called by both orchestrators.

**Stage 3 adds ``solve.py``** — the shared P0/P1 energy solve
(:func:`~market_sim.pipeline.solve.run_energy_solve`: base-cost P0, monthly
startup markup, bid-cost P1, intra-year warm start, and the cross-year
warm-start cache seam) — both orchestrators call it.

**Stage 4 adds ``commitment.py``** — the shared P2 commitment pass
(:func:`~market_sim.pipeline.commitment.run_commitment_pass`: CAISO RA
must-offer bridge, NYISO path B, ERCOT AS-aware screen + AS-adequacy floor +
WS1 headroom overrides, economic commitment screen + coal pin) — both
orchestrators call it.

**Stage 7 adds ``backcast_config.py``** — :func:`~market_sim.pipeline.
backcast_config.backcast_config`, the per-year backcast ``ScenarioConfig``
builder (ex-``scripts/run_calibration.py::_calibration_config``), imported
by both ``run_calibration.py`` and ``run_calibration_full.py``.
"""

from __future__ import annotations

from market_sim.pipeline.api import run_pair, run_scenario
from market_sim.pipeline.backcast_config import backcast_config
from market_sim.pipeline.commitment import (
    build_caiso_ra_p1_prep,
    build_caiso_reserve_p1_prep,
    build_ercot_gas_bridge_p1_prep,
    build_ercot_gas_bridge_p1_preps,
    build_miso_coal_night_floor_p1_prep,
    build_nyiso_gas_bridge_p1_prep,
    build_soco_gas_st_campaign_p1_prep,
    build_spp_gas_bridge_p1_prep,
    build_pjm_reserve_p1_prep,
    caiso_ra_p1_floor_fleet,
    ercot_gas_bridge_p1_floor_fleet,
    pjm_commitment_scoped_reserve_fleet,
    run_commitment_pass,
)
from market_sim.pipeline.kwargs import (
    apply_ercot_commitment_posture,
    apply_reserve_coopt,
    build_base_dispatch_kwargs,
    resolve_hydro_cascade,
    resolve_hydro_period_hours,
)
from market_sim.pipeline.persist import write_run_config
from market_sim.pipeline.prior import PriorYearResults
from market_sim.pipeline.reference import henry_hub_actual, load_reference
from market_sim.pipeline.solve import (
    EnergySolveResult,
    apply_bid_max_target,
    reset_pass_timing_log,
    run_energy_solve,
    take_pass_timing_log,
)
from market_sim.pipeline.spec import UNSET, DispatchSpec, ReserveSpec
from market_sim.pipeline.ttc import (
    apply_iso_monthly_ttc,
    apply_iso_year_ttc,
    apply_ttc_overrides,
    build_transmission_base,
)
from market_sim.pipeline.year import YearSolveOutput, run_year_solve

__all__ = [
    "run_scenario",
    "run_pair",
    "DispatchSpec",
    "ReserveSpec",
    "UNSET",
    "PriorYearResults",
    "EnergySolveResult",
    "build_base_dispatch_kwargs",
    "resolve_hydro_cascade",
    "resolve_hydro_period_hours",
    "apply_reserve_coopt",
    "apply_ercot_commitment_posture",
    "apply_bid_max_target",
    "reset_pass_timing_log",
    "run_energy_solve",
    "take_pass_timing_log",
    "run_commitment_pass",
    "build_caiso_ra_p1_prep",
    "build_caiso_reserve_p1_prep",
    "build_ercot_gas_bridge_p1_prep",
    "build_ercot_gas_bridge_p1_preps",
    "build_miso_coal_night_floor_p1_prep",
    "build_nyiso_gas_bridge_p1_prep",
    "build_soco_gas_st_campaign_p1_prep",
    "build_spp_gas_bridge_p1_prep",
    "build_pjm_reserve_p1_prep",
    "caiso_ra_p1_floor_fleet",
    "ercot_gas_bridge_p1_floor_fleet",
    "pjm_commitment_scoped_reserve_fleet",
    "backcast_config",
    "build_transmission_base",
    "apply_ttc_overrides",
    "apply_iso_year_ttc",
    "apply_iso_monthly_ttc",
    "YearSolveOutput",
    "run_year_solve",
    "write_run_config",
    "load_reference",
    "henry_hub_actual",
]
