"""Shared helpers of the MILP-UC wallclock ladder (GATESPEC section 3; plan section 4).

The capture seam (:func:`capture_year`) is the ``bench_cold_solve.py`` idea
moved one level up: a keeper recipe is replayed through
``replay_keeper.build_kwargs`` → ``run_calibration_full.solve_and_persist``,
and ``run_calibration.run_year``'s call to ``pipeline.solve.run_energy_solve``
is spied. With ``solve=False`` the spy records the LP inputs (fleet,
``FleetArrays``, demand, ``mc_base``, dispatch kwargs, config) and aborts —
ZERO LP, the slow test's source. With ``solve=True`` it lets the production
solve run and records the P0 result and the final P1 bid as well — one
P0 + P1 of the ISO-year, what a bench shard pays for rungs L1 and L2.

Rungs:

* :func:`rung_l1` — one window (hours ``0 .. W+L``): (a) the MILP, (b) its
  LP relaxation, (c) the production P1 slice; the integrality gap and the
  dispatch / start / price deltas.
* :func:`rung_l2` — the rolling stage over the given months with arms
  (warm start on/off, pre-fixing on/off, threads) and the schedule hash per arm.
* :func:`rung_l3` — the full stage through ``replay_keeper.py --set
  unit_commitment_milp=true`` on one year; the wall row from the bundle and
  the ``uc_solve_log``.
* :func:`wall_table` — the GATESPEC section 6.1 printer.

Nothing here changes a default or writes under ``results/calibration``; a
rung writes JSON under its ``--out``.
"""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import pickle
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))


class CaptureAbort(Exception):
    """Raised inside the spy to stop the orchestrator after the inputs are captured."""


@dataclass
class YearCapture:
    """The LP inputs (and, with ``solve=True``, the P0/P1 results) of one ISO-year."""

    iso: str
    year: int
    bundle: str
    fleet: list
    fleet_arrays: Any
    demand: np.ndarray
    mc_base: np.ndarray
    dispatch_kwargs: dict
    config: Any
    hooks: dict
    r0: Any = None
    mc_bid: np.ndarray | None = None
    p1: Any = None
    wall_s: float | None = None

    def save(self, path: Path) -> Path:
        """Pickle the capture without its ``hooks``.

        The P1 hooks are closures (e.g. an ERCOT gas-bridge ``_fleet_prep``
        defined inside its builder) that pickle cannot serialize; no rung
        reads them (``_stage`` hands the UC stage no upstream prep), so the
        saved capture carries ``hooks={}`` and loads with the same rungs.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump(
                dataclasses.replace(self, hooks={}),
                fh,
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        return path

    @staticmethod
    def load(path: Path) -> "YearCapture":
        with open(path, "rb") as fh:
            return pickle.load(fh)


def keeper_bundle(iso: str) -> Path:
    """The designated keeper bundle of ``iso`` (``frontend/data/backcast/keepers``)."""
    shard = json.loads(
        (REPO / "frontend/data/backcast/keepers" / f"{iso.upper()}.json").read_text()
    )
    reg = json.loads(
        (
            REPO / "frontend/data/backcast/registry" / f"{shard['keeper']}.json"
        ).read_text()
    )
    return REPO / reg["bundle"]


def _solve_kwargs(
    bundle: Path, year: int, out_dir: Path, overrides: dict | None
) -> dict:
    """The keeper recipe as ``solve_and_persist`` kwargs for one year (replay_keeper's route)."""
    from scripts import replay_keeper as rk
    from scripts import run_calibration_full as rcf

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [int(year)]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(out_dir)
    rk.enforce_single_recipe_partition(meta, kwargs["years"], kwargs)
    rk.apply_config_overlay(
        kwargs, rk.flipped_default_overlay(bundle, kwargs["years"], meta)
    )
    # Both channels, as replay_keeper's --set loop: a key that is also an
    # explicit solve_and_persist kwarg (e.g. ercot_gas_commitment_bridge, which
    # the ERCOT keeper's meta carries) is re-stomped by the meta's value when
    # it rides prb_overrides alone (the ERCOT-65 defect class).
    solve_params = set(inspect.signature(rcf.solve_and_persist).parameters)
    for key, val in (overrides or {}).items():
        if key in solve_params:
            kwargs[key] = val
        kwargs.setdefault("prb_overrides", {})
        kwargs["prb_overrides"][key] = val
    rcf.enforce_legacy_p2_kwargs(kwargs, False)
    kwargs.setdefault("note", "uc-bench capture (never registered)")
    return kwargs


def capture_year(
    iso: str,
    year: int,
    out_dir: Path,
    *,
    solve: bool,
    bundle: Path | None = None,
    overrides: dict | None = None,
) -> YearCapture:
    """Capture one ISO-year's LP inputs (and results when ``solve``) from its keeper recipe.

    Pins the goldens' determinism env (``replay_keeper.pin_determinism_env``).
    ``solve=False`` runs ZERO LP: the spy raises :class:`CaptureAbort` once
    ``run_energy_solve`` is entered, which ``solve_and_persist`` propagates.
    """
    from scripts import replay_keeper as rk
    from scripts import run_calibration as rc
    from scripts import run_calibration_full as rcf

    rk.pin_determinism_env()
    bundle = Path(bundle) if bundle is not None else keeper_bundle(iso)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    kwargs = _solve_kwargs(bundle, year, out_dir / "replay", overrides)
    real = rc.run_energy_solve
    box: dict = {}

    def spy(fleet, fleet_arrays, demand, mc_base, dispatch_kwargs, config, **kw):
        box.update(
            fleet=fleet,
            fleet_arrays=fleet_arrays,
            demand=np.asarray(demand),
            mc_base=np.asarray(mc_base),
            dispatch_kwargs=dict(dispatch_kwargs),
            config=config,
            hooks={
                k: v
                for k, v in kw.items()
                if k.startswith("p1_") or k == "mc_bid_adjust"
            },
        )
        if not solve:
            raise CaptureAbort()
        t0 = time.perf_counter()
        res = real(fleet, fleet_arrays, demand, mc_base, dispatch_kwargs, config, **kw)
        box.update(
            r0=res.r0,
            mc_bid=np.asarray(res.mc_bid),
            p1=res.p1,
            wall_s=time.perf_counter() - t0,
        )
        return res

    rc.run_energy_solve = spy
    try:
        try:
            rcf.solve_and_persist(**kwargs)
        except CaptureAbort:
            pass
    finally:
        rc.run_energy_solve = real
    if "fleet_arrays" not in box:
        raise RuntimeError(
            "the orchestrator never reached run_energy_solve — nothing captured"
        )
    return YearCapture(iso=iso.upper(), year=int(year), bundle=str(bundle), **box)


# --------------------------------------------------------------------------- #
# Rungs                                                                        #
# --------------------------------------------------------------------------- #
def _stage(cap: YearCapture, config, r0, mc_bid, checkpoint_root: Path):
    """A :class:`UcStage` over a capture (P1 bid = the captured bid, or the base cost)."""
    from market_sim.pipeline.uc import UcStage

    bid = np.asarray(mc_bid if mc_bid is not None else cap.mc_base, dtype=float)
    return UcStage(
        config,
        cap.fleet_arrays,
        cap.demand,
        cap.dispatch_kwargs,
        cap.mc_base,
        r0,
        None,
        lambda: bid,
        checkpoint_root=checkpoint_root,
    )


def _armed_config(cap: YearCapture, **uc_fields):
    """The captured config with the UC gate armed (validation runs)."""
    return cap.config.with_overrides(unit_commitment_milp=True, **uc_fields)


def _relaxation_as_p0(cap: YearCapture, t0: int, t1: int):
    """A P0 stand-in for a solve-less capture: the window LP itself (no UC rows)."""
    from market_sim.model.lp.model import DispatchModel
    from market_sim.model.uc.window import slice_window_inputs

    inputs = slice_window_inputs(
        cap.fleet_arrays,
        cap.demand,
        cap.dispatch_kwargs,
        t0,
        t1,
        None,
        free_budget_units=True,
    )
    model = DispatchModel(inputs.fleet, inputs.demand, **inputs.kwargs)
    res = model.solve(mc=cap.mc_base[:, t0:t1], full_extract=False)
    T = cap.demand.shape[1]

    class _R0:
        dispatch = np.zeros((cap.fleet_arrays.n_gen, T))
        prices = np.zeros((cap.demand.shape[0], T))
        storage_soc = None

    r0 = _R0()
    r0.dispatch[:, t0:t1] = res.dispatch
    r0.prices[:, t0:t1] = res.prices
    if res.storage_soc is not None:
        r0.storage_soc = np.zeros((res.storage_soc.shape[0], T))
        r0.storage_soc[:, t0:t1] = res.storage_soc
    if getattr(res, "flows", None) is not None:
        r0.flows = np.zeros((res.flows.shape[0], T))
        r0.flows[:, t0:t1] = res.flows
    return r0


def rung_l1(
    cap: YearCapture, out_dir: Path, dump_dir: Path | None = None, **uc_fields
) -> dict:
    """L1: one window — MILP (a), LP relaxation (b), the production P1 slice (c).

    ``dump_dir`` (``bench_uc_ladder.py --dump-dir``) is handed to
    :class:`UcSolveOptions` so an infeasible window writes its model, state
    and zero-LP diagnosis there — a harness argument, never a registry field.
    The window is built exactly as the production stage builds its first one
    (the carried P0 state, the look-ahead floor need for the guard rows).
    """
    from market_sim.model.lp.model import DispatchModel
    from market_sim.model.uc.params import units_needed_for_floor, units_online_profile
    from market_sim.model.uc.solve import solve_options_from_config, solve_window
    from market_sim.model.uc.window import UcWindowModel, slice_window_inputs

    cfg = _armed_config(cap, **uc_fields)
    W, L = int(cfg.uc_window_hours), int(cfg.uc_lookahead_hours)
    t0, t1 = 0, min(W + L, cap.demand.shape[1])
    r0 = cap.r0 if cap.r0 is not None else _relaxation_as_p0(cap, t0, t1)
    stage = _stage(cap, cfg, r0, cap.mc_bid, Path(out_dir) / "uc")
    p, k = stage.params, stage.int_idx
    p0 = np.asarray(r0.dispatch, dtype=float)
    inputs = slice_window_inputs(
        cap.fleet_arrays,
        cap.demand,
        cap.dispatch_kwargs,
        t0,
        t1,
        p0,
        p0_flows=getattr(r0, "flows", None),
    )
    bid = np.asarray(cap.mc_bid if cap.mc_bid is not None else cap.mc_base, dtype=float)
    mc_w = bid.copy()
    mc_w[p.integer_member_gens, :] = cap.mc_base[p.integer_member_gens, :]
    noload = p.noload_cost_per_unit_h(cap.fleet_arrays, cap.mc_base)[k]
    T = cap.demand.shape[1]
    sched_state = stage_state(
        stage, cap.fleet_arrays, p0, getattr(r0, "storage_soc", None), T
    )
    soc_t = (
        None
        if getattr(r0, "storage_soc", None) is None
        else np.asarray(r0.storage_soc)[:, t1 - 1]
    )
    guard_reach = int(p.dt_h[k].max()) - 1 if k.size else 0
    floor_ahead = units_needed_for_floor(
        p, cap.fleet_arrays, t1, min(t1 + guard_reach, T)
    )[k]
    opts = solve_options_from_config(
        cfg, debug_dump_dir=None if dump_dir is None else Path(dump_dir)
    )
    out: dict[str, Any] = {
        "iso": cap.iso,
        "year": cap.year,
        "t0": t0,
        "t1": t1,
        "integer_clusters": int(k.size),
    }

    def _build():
        return UcWindowModel(
            inputs,
            p,
            mc_w[:, t0:t1],
            noload[:, t0:t1],
            sched_state,
            soc_terminal=soc_t,
            floor_need_ahead=floor_ahead,
        )

    # (a) MILP
    w = _build()
    warm = w.warm_start_vector(
        None, W, p0[:, t0:t1], units_online_profile(p, p0[:, t0:t1])[k]
    )
    a = solve_window(w, opts, warm, window_index=0, t0=t0, t1=t1)
    out["milp"] = _window_stats(a)
    out["milp"]["guard_rows"] = int(w._n_guard_rows)
    out["rss_gb"] = _peak_rss_gb()
    # (b) LP relaxation
    w2 = _build()
    b = solve_window(w2, opts, relax=True, window_index=0, t0=t0, t1=t1)
    out["relaxation"] = _window_stats(b)
    out["integrality_gap"] = float(a.objective - b.objective)
    # (c) the production P1 slice (no UC rows, the P1 bid)
    model = DispatchModel(inputs.fleet, inputs.demand, **inputs.kwargs)
    tp = time.perf_counter()
    c = model.solve(mc=bid[:, t0:t1], full_extract=False)
    out["p1_slice"] = {
        "solve_s": time.perf_counter() - tp,
        "objective": float(c.objective_value),
    }
    int_rows = p.integer_member_gens
    committed_a = float(a.dispatch[int_rows].sum())
    committed_c = float(c.dispatch[int_rows].sum())
    out["delta_committed_energy_mwh"] = committed_a - committed_c
    out["milp_starts"] = int(a.v.sum())
    out["p1_slice_starts"] = int(_starts_from_dispatch(c.dispatch[int_rows]))
    out["trough_price_milp_vs_p1"] = _trough_prices(a, c, inputs)
    _write_json(Path(out_dir) / "l1.json", out)
    return out


def stage_state(stage, fleet_arrays, p0_dispatch, p0_soc, T):
    """The first-window :class:`WindowState` the stage would build (hour T-1, cyclic)."""
    from market_sim.model.uc.params import units_online_from_dispatch
    from market_sim.model.uc.schedule import UcSchedule

    p, k = stage.params, stage.int_idx
    hist = int(max(int(p.ut_h[k].max()), int(p.dt_h[k].max())) - 1) if k.size else 0
    sched = UcSchedule(p, T, hist)
    u_init = units_online_from_dispatch(p, np.asarray(p0_dispatch)[:, T - 1])[k]
    return sched.state_for(
        0,
        fleet_arrays,
        u_init,
        np.asarray(p0_dispatch)[:, T - 1],
        None if p0_soc is None else np.asarray(p0_soc)[:, T - 1],
    )


#: L2 arms: name -> (ScenarioConfig overrides, UcSolveOptions overrides, note).
#: Every arm but ``wide`` is a solver-PATH arm: run PAIRED against ``base``
#: (each window takes the base run's carried state, so it is the same problem;
#: ``UcStage.run(pin=...)``) its per-window objective delta and kept-``u``
#: agreement are the equivalence evidence. ``wide`` re-declares the horizon
#: (plan E2: 48 + 24 h) and so changes the optimum — a wall measurement only,
#: run rolling and excluded from the equivalence summary.
L2_ARMS: dict[str, tuple[dict, dict, str]] = {
    "warm": ({}, {"warm_start": False}, "no setSolution incumbent (E3 off)"),
    "prefix": ({"uc_prefixing": True}, {}, "reachability pre-fixing on (E5)"),
    "threads": ({}, {"threads": 4}, "4 HiGHS threads, parallel on (E7)"),
    "legacy": ({"uc_solver_preset": "highs_default"}, {}, "the uc-1.1 solver path"),
    "lean": ({"uc_solver_preset": "lean"}, {}, "the lean solver path"),
    "presolve": ({}, {"presolve": "off"}, "MIP presolve off"),
    "fj": ({}, {"feasibility_jump": False}, "feasibility-jump heuristic off"),
    "lpheur": (
        {},
        {"lp_heuristics": False},
        "RINS/RENS/root-reduced-cost off, effort 0",
    ),
    "symmetry": ({}, {"symmetry": False}, "symmetry detection off"),
    "restart": ({}, {"restart": False}, "root restarts off"),
    "probelift": (
        {},
        {"extra_highs_options": (("mip_lifting_for_probing", 0),)},
        "HiGHS mip_lifting_for_probing=0 on the default path (presolve cost probe)",
    ),
    "rulelog": (
        {},
        {
            "extra_highs_options": (("presolve_rule_logging", True),),
            "raw_log_dir": "RAW",
        },
        "default path + presolve rule logging; raw HiGHS log of the first two windows kept",
    ),
    "wide": (
        {"uc_window_hours": 48, "uc_lookahead_hours": 24},
        {},
        "E2 horizon 48 + 24 h (optimum-changing; wall only, rolling)",
    ),
    # Lane UC-SLIM: the slim window (model/uc/slim.py). ``noslim`` is the
    # uc-1.1 full-model path against a ``base`` that runs at the registry
    # default (slim on); ``slim`` arms it explicitly for a base run at
    # ``--set uc_slim_window=false``. ``slim_noprobe`` is a MEASUREMENT arm
    # only (HiGHS presolve_rule_off bit 15 = probing, the costliest rule left
    # on the slim model): a solver-path change, never a registry value.
    "noslim": (
        {"uc_slim_window": False},
        {},
        "every window on the full model (slim off)",
    ),
    "slim": (
        {"uc_slim_window": True},
        {},
        "the slim window (exact reduction before HiGHS)",
    ),
    "slim_noprobe": (
        {"uc_slim_window": True},
        {"extra_highs_options": (("presolve_rule_off", 1 << 15),)},
        "slim window + HiGHS probing off (measurement only)",
    ),
}

#: Arms whose schedule may legitimately differ from ``base`` beyond the gap.
_OPTIMUM_CHANGING_ARMS = frozenset({"wide"})


def _reset_highs_scheduler() -> None:
    """Reset HiGHS's process-global scheduler (its thread count is fixed at the first solve)."""
    import highspy

    highspy.Highs.resetGlobalScheduler(True)


def _month_stats(wins: list[dict]) -> dict:
    """Distribution / phase sums of one month's windows (``stage.log['windows']``)."""
    from market_sim.pipeline.uc import phase_sums, slim_sums

    milp = np.array([w["milp_s"] for w in wins])
    nodes = np.array([w["nodes"] for w in wins])
    paired = [w.get("paired") for w in wins]
    return {
        "windows": len(wins),
        "milp_s_sum": float(milp.sum()),
        "milp_s_p50": float(np.percentile(milp, 50)),
        "milp_s_p95": float(np.percentile(milp, 95)),
        "milp_s_max": float(milp.max()),
        "build_s_sum": float(sum(w["build_s"] for w in wins)),
        "nodes_p50": float(np.percentile(nodes, 50)),
        "nodes_p95": float(np.percentile(nodes, 95)),
        "zero_node_share": float(np.mean(nodes == 0)),
        "time_limit_hits": int(sum(w["time_limit_hit"] for w in wins)),
        "fixed_on": int(sum(w["fixed_on"] for w in wins)),
        "fixed_off": int(sum(w["fixed_off"] for w in wins)),
        "gap_max": float(max(w["gap"] for w in wins)),
        "phase_sums": phase_sums(wins),
        "slim_sums": slim_sums(wins),
        "objectives": [float(w["objective"]) for w in wins],
        "window_t0": [int(w["t0"]) for w in wins],
        "paired": (
            {
                "u_kept_equal_windows": int(
                    sum(1 for q in paired if q and q["u_kept_equal"])
                ),
                "u_cells_differ_total": int(
                    sum(q["u_cells_differ"] for q in paired if q)
                ),
            }
            if all(paired)
            else None
        ),
    }


def _equivalence(base_m: dict, arm_m: dict, rel_gap: float) -> dict:
    """Per-window objective deltas of an arm against ``base`` (same month).

    Exact only for a PAIRED arm (same window problems); for a rolling arm the
    deltas are confounded by state divergence after the first within-gap tie
    and ``paired`` reads ``None``.
    """
    ob = np.asarray(base_m["objectives"], dtype=float)
    oa = np.asarray(arm_m["objectives"], dtype=float)
    if ob.shape != oa.shape or not np.array_equal(
        base_m["window_t0"], arm_m["window_t0"]
    ):
        return {"comparable": False}
    scale = np.maximum(np.abs(ob), 1.0)
    rel = np.abs(oa - ob) / scale
    out = {
        "comparable": True,
        "paired": arm_m.get("paired"),
        "schedule_hash_equal": arm_m["schedule_hash"] == base_m["schedule_hash"],
        "max_rel_obj_delta": float(rel.max()) if rel.size else 0.0,
        "windows_beyond_gap": int(np.sum(rel > rel_gap)),
        "windows_obj_differ": int(np.sum(rel > 1e-9)),
        "arm_minus_base_obj_sum": float(np.sum(oa - ob)),
    }
    return out


def rung_l2(
    cap: YearCapture,
    out_dir: Path,
    months: tuple[int, ...] = (1, 7),
    arms: tuple[str, ...] = ("warm", "prefix"),
    paired: bool = True,
    dump_dir: Path | None = None,
    **uc_fields,
) -> dict:
    """L2: rolling windows over ``months`` per arm; distributions, phase sums, equivalence.

    ``dump_dir`` (``bench_uc_ladder.py --dump-dir``) is handed to every arm's
    :class:`UcSolveOptions`: an infeasible window writes its model, carried
    state and zero-LP diagnosis there, and the raised
    :class:`~market_sim.model.uc.window.UcWindowInfeasible` (window, plants,
    hours) is also written to ``<out_dir>/l2_infeasible.json`` before it
    propagates — a harness argument, never a registry field.

    ``arms`` names :data:`L2_ARMS` entries; ``base`` (the registry defaults
    plus ``uc_fields``) always runs first, rolling, recording its handed-over
    states. With ``paired`` (the default) every solver-path arm then solves
    the base run's exact window problems (``UcStage.run(pin=...)``), so the
    ``equivalence`` block's per-window objective deltas and kept-``u``
    agreement are exact; ``paired=False`` runs every arm rolling (its
    schedule hash is then the only comparison, confounded after the first
    within-gap tie). Optimum-changing arms (``wide``) always run rolling.
    """
    import dataclasses as _dc

    from market_sim.model.uc.schedule import month_boundaries
    from market_sim.model.uc.window import UcWindowInfeasible

    if cap.r0 is None:
        raise RuntimeError(
            "rung L2 needs a solved capture (capture_year(..., solve=True))"
        )
    unknown = [a for a in arms if a not in L2_ARMS]
    if unknown:
        raise SystemExit(f"unknown L2 arm(s) {unknown}; known: {sorted(L2_ARMS)}")
    ends = month_boundaries(cap.demand.shape[1])
    starts = np.concatenate([[0], ends[:-1]])
    arm_specs: list[tuple[str, dict, dict, str]] = [
        ("base", {}, {}, "registry defaults")
    ]
    arm_specs += [(a, *L2_ARMS[a]) for a in arms]
    out: dict[str, Any] = {
        "iso": cap.iso,
        "year": cap.year,
        "months": list(months),
        "paired": bool(paired),
        "capture_wall_s": cap.wall_s,
        "arms": {},
    }
    base_cfg = _armed_config(cap, **uc_fields)
    rel_gap = float(base_cfg.uc_mip_rel_gap)
    base_scheds: dict[int, Any] = {}
    for name, cfg_over, solve_over, note in arm_specs:
        solve_over = dict(solve_over)
        if solve_over.get("raw_log_dir") == "RAW":
            solve_over["raw_log_dir"] = Path(out_dir) / "highs_logs" / name
        threads_arm = int(solve_over.get("threads", 0)) > 0
        pin_this = paired and name != "base" and name not in _OPTIMUM_CHANGING_ARMS
        if threads_arm:
            _reset_highs_scheduler()
        try:
            cfg = _armed_config(cap, **{**uc_fields, **cfg_over})
            stage = _stage(cap, cfg, cap.r0, cap.mc_bid, Path(out_dir) / "uc" / name)
            if dump_dir is not None:
                solve_over.setdefault("debug_dump_dir", Path(dump_dir) / name)
            if solve_over:
                stage.options = _dc.replace(stage.options, **solve_over)
            per_month = []
            for m in months:
                t0, t1 = int(starts[m - 1]), int(ends[m - 1])
                tm = time.perf_counter()
                try:
                    sched = stage.run(
                        cap.fleet_arrays,
                        np.asarray(cap.mc_bid),
                        t_start=t0,
                        t_end=t1,
                        write=False,
                        record_states=(name == "base"),
                        pin=base_scheds[m] if pin_this else None,
                    )
                except UcWindowInfeasible as exc:
                    _write_json(
                        Path(out_dir) / "l2_infeasible.json",
                        {
                            "arm": name,
                            "month": m,
                            "message": str(exc),
                            "window_index": exc.window_index,
                            "t0": exc.t0,
                            "t1": exc.t1,
                            "relaxation_status": exc.relaxation_status,
                            "diagnosis": exc.diagnosis,
                        },
                    )
                    raise
                wall = time.perf_counter() - tm
                if name == "base":
                    base_scheds[m] = sched
                stats = _month_stats(stage.log["windows"])
                stats.update(
                    {
                        "month": m,
                        "wall_s": wall,
                        "paired_run": bool(pin_this),
                        "schedule_hash": hashlib.sha256(
                            np.ascontiguousarray(sched.u[:, t0:t1]).tobytes()
                        ).hexdigest()[:16],
                    }
                )
                per_month.append(stats)
            out["arms"][name] = {
                "note": note,
                "config": cfg_over,
                "solve": {
                    k: str(v) if isinstance(v, Path) else v
                    for k, v in solve_over.items()
                },
                "solver_path": stage.options.solver_path(),
                "months": per_month,
                "wall_s_total": float(sum(m["wall_s"] for m in per_month)),
                "rss_gb": _peak_rss_gb(),
            }
            # A shard near its budget keeps every finished arm (rule 32 stop rule).
            _write_json(Path(out_dir) / "l2_partial.json", out)
        finally:
            if threads_arm:
                _reset_highs_scheduler()
    base = out["arms"]["base"]
    base_hashes = [m["schedule_hash"] for m in base["months"]]
    out["schedule_equal_across_arms"] = {
        name: [m["schedule_hash"] for m in arm["months"]] == base_hashes
        for name, arm in out["arms"].items()
    }
    out["equivalence"] = {
        name: {
            "optimum_changing_arm": name in _OPTIMUM_CHANGING_ARMS,
            "paired": bool(arm["months"][0].get("paired_run")),
            "months": [
                _equivalence(bm, am, rel_gap)
                for bm, am in zip(base["months"], arm["months"])
            ],
        }
        for name, arm in out["arms"].items()
        if name != "base"
    }
    out["profile_table"] = l2_profile_table(out)
    _write_json(Path(out_dir) / "l2.json", out)
    (Path(out_dir) / "l2_profile.md").write_text(out["profile_table"] + "\n")
    return out


_PROFILE_COLS = (
    ("wall_s_total", "wall s"),
    ("milp_s_sum", "MILP Σ s"),
    ("setup_s", "setup Σ"),
    ("presolve_s", "presolve Σ"),
    ("pre_root_heur_s", "pre-root heur Σ"),
    ("root_lp_s", "root LP Σ"),
    ("tail_s", "tail Σ"),
    ("lp_build_s", "LP build Σ"),
    ("uc_build_s", "UC build Σ"),
    ("set_solution_s", "setSolution Σ"),
    ("extract_s", "extract Σ"),
    ("slim_s", "slim Σ"),
    ("solved_columns_mean", "solved cols"),
    ("lp_iters", "LP iters Σ"),
    ("lp_iters_heur", "heur iters Σ"),
    ("warm_feasible_windows", "warm feasible"),
)


def l2_profile_table(res: dict) -> str:
    """The per-arm profile table (markdown) of an L2 result: seconds summed over the months.

    The three equivalence columns read, for a PAIRED arm, the windows whose
    kept ``u`` equals the base run's (of all windows), the largest relative
    objective delta on the same window problem and the windows beyond the gap;
    for a rolling arm they read the schedule-hash equality instead and the
    deltas are confounded (marked ``~``).
    """
    head = [
        "arm",
        "windows",
        "nodes p50/p95",
        "gap max",
        "u = base",
        "max rel Δobj",
        "> gap",
    ]
    head += [c[1] for c in _PROFILE_COLS]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for name, arm in res["arms"].items():
        months = arm["months"]
        sums: dict[str, float] = {}
        for m in months:
            for key, _ in _PROFILE_COLS:
                if key == "wall_s_total":
                    continue
                if key == "solved_columns_mean":
                    vals = sums.setdefault("_solved_cols", [])
                    vals.append(float(m.get("slim_sums", {}).get(key, 0.0) or 0.0))
                    continue
                src = m["phase_sums"] if key in m["phase_sums"] else m
                sums[key] = sums.get(key, 0.0) + float(src.get(key, 0.0) or 0.0)
        if "_solved_cols" in sums:
            sums["solved_columns_mean"] = float(np.mean(sums.pop("_solved_cols")))
        sums["wall_s_total"] = arm["wall_s_total"]
        eq = res.get("equivalence", {}).get(name, {})
        eqm = [e for e in eq.get("months", []) if e.get("comparable")]
        is_paired = bool(eq.get("paired"))
        n_win = sum(m["windows"] for m in months)
        max_rel = max((e.get("max_rel_obj_delta", 0.0) for e in eqm), default=0.0)
        beyond = sum(e.get("windows_beyond_gap", 0) for e in eqm)
        if name == "base":
            ucol, dcol, gcol = "—", "—", "—"
        elif is_paired:
            same = sum(
                (e.get("paired") or {}).get("u_kept_equal_windows", 0) for e in eqm
            )
            ucol, dcol, gcol = f"{same}/{n_win}", f"{max_rel:.1e}", str(beyond)
        else:
            ucol = f"hash {res['schedule_equal_across_arms'].get(name)}"
            dcol, gcol = f"~{max_rel:.1e}", f"~{beyond}"
        row = [
            name,
            str(n_win),
            f"{np.median([m['nodes_p50'] for m in months]):.0f}/{max(m['nodes_p95'] for m in months):.0f}",
            f"{max(m['gap_max'] for m in months):.1e}",
            ucol,
            dcol,
            gcol,
        ]
        for key, _ in _PROFILE_COLS:
            v = sums.get(key, 0.0)
            row.append(
                f"{v:.0f}"
                if key.endswith("iters")
                or key in ("warm_feasible_windows", "solved_columns_mean")
                else f"{v:.1f}"
            )
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def rung_l3(
    iso: str,
    year: int,
    out_dir: Path,
    bundle: Path | None = None,
    baseline_s: float | None = None,
    overrides: dict | None = None,
) -> dict:
    """L3: the full stage through ``replay_keeper.py --set unit_commitment_milp=true``."""
    bundle = Path(bundle) if bundle is not None else keeper_bundle(iso)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_dir = out_dir / "bundle"
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "replay_keeper.py"),
        str(bundle),
        "--years",
        str(year),
        "--out-dir",
        str(run_dir),
        "--set",
        "unit_commitment_milp=true",
        "--note",
        "uc-ladder L3 (never registered)",
    ]
    for key, val in (overrides or {}).items():
        cmd += ["--set", f"{key}={json.dumps(val)}"]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    wall = time.perf_counter() - t0
    (out_dir / "l3_stdout.txt").write_text(proc.stdout[-200000:])
    (out_dir / "l3_stderr.txt").write_text(proc.stderr[-200000:])
    if proc.returncode != 0:
        raise RuntimeError(
            f"replay_keeper exited {proc.returncode}; see {out_dir / 'l3_stderr.txt'}"
        )
    log_path = run_dir / f"uc_solve_log_{year}.json"
    log = json.loads(log_path.read_text()) if log_path.is_file() else {}
    summ = log.get("summary", {})
    phases = parse_phase_timing_line(proc.stdout + proc.stderr, year)
    p0_s = phases.get("solve_p0")
    p1_s = phases.get("solve_p1")
    own_baseline = (p0_s + p1_s) if p0_s is not None and p1_s is not None else None
    # The denominator: the caller's --baseline-s when given, else the shard's
    # own P0 + P1 (the UC-2-SPP PRECOMMIT section 5 proxy: P0 is the unchanged
    # LP and P1 differs only by bounds). ``total_s`` is the year's phase-timing
    # total (P0 + markup/UC + P1 + results write), not the subprocess wall.
    denom = baseline_s if baseline_s else own_baseline
    total_year = phases.get("total", wall)
    row = {
        "iso_year": f"{iso.upper()} {year}",
        "baseline_s": denom,
        "baseline_source": "--baseline-s" if baseline_s else "own solve_p0 + solve_p1",
        "p0_s": p0_s,
        "p1_s": p1_s,
        "markup_s": phases.get("markup"),
        "subprocess_wall_s": wall,
        "total_s": total_year,
        "uc_sum_s": summ.get("uc_total_s"),
        "uc_windows": summ.get("n_windows"),
        "uc_mean_s": summ.get("milp_s_mean"),
        "uc_p95_s": summ.get("milp_s_p95"),
        "ratio": (total_year / denom) if denom else None,
        "phase_sums": summ.get("phase_sums"),
        "solver_path": log.get("engine", {}).get("solver_path"),
        "integers_per_window": log.get("engine", {}).get("integers_per_window"),
        "slim_sums": summ.get("slim_sums"),
        "uc_slim_window": log.get("engine", {}).get("fields", {}).get("uc_slim_window"),
        "nodes_p50": summ.get("nodes_p50"),
        "nodes_p95": summ.get("nodes_p95"),
        "gap_p95": summ.get("gap_p95"),
        "time_limit_hits": summ.get("time_limit_hits"),
        "peak_rss_gb": summ.get("peak_rss_gb"),
        "uc_solve_log": str(log_path),
        "bundle": str(run_dir),
    }
    _write_json(out_dir / "l3.json", row)
    return row


def parse_phase_timing_line(text: str, year: int) -> dict:
    """The ``log_year_phase_timing`` fields of ``year`` from an orchestrator's log text.

    Returns ``{}`` when the line is absent (a cached year prints a different line).
    """
    import re

    pat = re.compile(
        rf"year {int(year)} phase timing: data_prep=([\d.]+)s solve_p0=([\d.]+)s "
        rf"markup=([\d.]+)s solve_p1=([\d.]+)s results_write=([\d.]+)s total=([\d.]+)s"
    )
    m = pat.search(text)
    if not m:
        return {}
    keys = ("data_prep", "solve_p0", "markup", "solve_p1", "results_write", "total")
    return {k: float(v) for k, v in zip(keys, m.groups())}


# --------------------------------------------------------------------------- #
# Reporting                                                                    #
# --------------------------------------------------------------------------- #
WALL_COLUMNS = (
    "ISO-year",
    "baseline P0+P1 s",
    "P0 s",
    "UC Σ s (windows, mean, p95 MILP s)",
    "P1 s",
    "total s",
    "ratio",
    "integers/window",
    "nodes p50/p95",
    "gap p95",
    "time-limit hits",
    "peak RSS GB",
)


def wall_table(rows: list[dict]) -> str:
    """The GATESPEC section 6.1 wall table (markdown) from L3 rows."""

    def f(x, nd=1):
        return "—" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))

    lines = ["| " + " | ".join(WALL_COLUMNS) + " |", "|" + "---|" * len(WALL_COLUMNS)]
    for r in rows:
        uc = f"{f(r.get('uc_sum_s'))} ({r.get('uc_windows')}, {f(r.get('uc_mean_s'), 2)}, {f(r.get('uc_p95_s'), 2)})"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(r.get("iso_year")),
                    f(r.get("baseline_s")),
                    f(r.get("p0_s")),
                    uc,
                    f(r.get("p1_s")),
                    f(r.get("total_s")),
                    f(r.get("ratio"), 2),
                    f(r.get("integers_per_window")),
                    f"{f(r.get('nodes_p50'))}/{f(r.get('nodes_p95'))}",
                    f(r.get("gap_p95"), 5),
                    f(r.get("time_limit_hits")),
                    f(r.get("peak_rss_gb"), 2),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _window_stats(res) -> dict:
    return {
        "build_s": res.build_s,
        "milp_s": res.milp_s,
        "nodes": int(res.nodes),
        "gap": float(res.gap),
        "status": res.status,
        "objective": float(res.objective),
        "integers": int(res.integers),
        "columns": int(res.columns),
        "rows": int(res.rows),
        "time_limit_hit": bool(res.time_limit_hit),
        "starts": int(res.v.sum()) if res.v.size else 0,
        "warm_accepted": bool(res.warm_accepted),
    }


def _starts_from_dispatch(d: np.ndarray) -> int:
    on = d > 1e-6
    return int(np.sum(on[:, 1:] & ~on[:, :-1]))


def _trough_prices(a, c, inputs) -> dict:
    """Mean P1-slice price in its lowest-tercile hours vs the MILP window's LP-fixed price proxy."""
    pc = np.asarray(c.prices, dtype=float)
    thresh = np.percentile(pc, 33.3)
    return {
        "p1_slice_lower_tercile_mean": float(pc[pc <= thresh].mean()),
        "note": "the MILP prices nothing (rule 4); the trough reading is scored on the L3 P1 bundle",
    }


def _peak_rss_gb() -> float:
    import resource

    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024**2)


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=_json_default))


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return str(o)
