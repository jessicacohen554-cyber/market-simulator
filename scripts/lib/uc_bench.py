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
import json
import os
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
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump(self, fh, protocol=pickle.HIGHEST_PROTOCOL)
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
    for key, val in (overrides or {}).items():
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
    from market_sim.model.uc.solve import UcSolveOptions, solve_window
    from market_sim.model.uc.window import UcWindowModel, slice_window_inputs

    cfg = _armed_config(cap, **uc_fields)
    W, L = int(cfg.uc_window_hours), int(cfg.uc_lookahead_hours)
    t0, t1 = 0, min(W + L, cap.demand.shape[1])
    r0 = cap.r0 if cap.r0 is not None else _relaxation_as_p0(cap, t0, t1)
    stage = _stage(cap, cfg, r0, cap.mc_bid, Path(out_dir) / "uc")
    p, k = stage.params, stage.int_idx
    p0 = np.asarray(r0.dispatch, dtype=float)
    inputs = slice_window_inputs(
        cap.fleet_arrays, cap.demand, cap.dispatch_kwargs, t0, t1, p0
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
    opts = UcSolveOptions(
        mip_rel_gap=float(cfg.uc_mip_rel_gap),
        time_limit_s=float(cfg.uc_window_time_limit_s),
        debug_dump_dir=None if dump_dir is None else Path(dump_dir),
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


def rung_l2(
    cap: YearCapture,
    out_dir: Path,
    months: tuple[int, ...] = (1, 7),
    arms: tuple[str, ...] = ("warm", "prefix"),
    **uc_fields,
) -> dict:
    """L2: rolling windows over ``months`` per arm; distributions and schedule hashes."""
    from market_sim.model.uc.schedule import month_boundaries

    if cap.r0 is None:
        raise RuntimeError(
            "rung L2 needs a solved capture (capture_year(..., solve=True))"
        )
    ends = month_boundaries(cap.demand.shape[1])
    starts = np.concatenate([[0], ends[:-1]])
    arm_specs: list[tuple[str, dict, dict]] = [("base", {}, {})]
    if "warm" in arms:
        arm_specs.append(("warm_off", {}, {"warm_start": False}))
    if "prefix" in arms:
        arm_specs.append(("prefix_on", {"uc_prefixing": True}, {}))
    if "threads" in arms:
        arm_specs.append(("threads_4", {}, {"threads": "4"}))
    out: dict[str, Any] = {
        "iso": cap.iso,
        "year": cap.year,
        "months": list(months),
        "arms": {},
    }
    for name, cfg_over, solve_over in arm_specs:
        prev_threads = os.environ.get("MARKET_SIM_HIGHS_THREADS")
        if "threads" in solve_over:
            os.environ["MARKET_SIM_HIGHS_THREADS"] = solve_over["threads"]
        try:
            cfg = _armed_config(cap, **{**uc_fields, **cfg_over})
            stage = _stage(cap, cfg, cap.r0, cap.mc_bid, Path(out_dir) / "uc" / name)
            if "warm_start" in solve_over:
                stage.options = dataclasses.replace(
                    stage.options, warm_start=solve_over["warm_start"]
                )
            per_month = []
            hashes = []
            for m in months:
                t0, t1 = int(starts[m - 1]), int(ends[m - 1])
                tm = time.perf_counter()
                sched = stage.run(
                    cap.fleet_arrays,
                    np.asarray(cap.mc_bid),
                    t_start=t0,
                    t_end=t1,
                    write=False,
                )
                wall = time.perf_counter() - tm
                wins = stage.log["windows"]
                milp = np.array([w["milp_s"] for w in wins])
                nodes = np.array([w["nodes"] for w in wins])
                hashes.append(
                    hashlib.sha256(
                        np.ascontiguousarray(sched.u[:, t0:t1]).tobytes()
                    ).hexdigest()[:16]
                )
                per_month.append(
                    {
                        "month": m,
                        "windows": len(wins),
                        "wall_s": wall,
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
                        "schedule_hash": hashes[-1],
                    }
                )
            out["arms"][name] = {
                "config": cfg_over,
                "solve": solve_over,
                "months": per_month,
                "rss_gb": _peak_rss_gb(),
            }
        finally:
            if "threads" in solve_over:
                if prev_threads is None:
                    os.environ.pop("MARKET_SIM_HIGHS_THREADS", None)
                else:
                    os.environ["MARKET_SIM_HIGHS_THREADS"] = prev_threads
    base_hashes = [m["schedule_hash"] for m in out["arms"]["base"]["months"]]
    out["schedule_equal_across_arms"] = {
        name: [m["schedule_hash"] for m in arm["months"]] == base_hashes
        for name, arm in out["arms"].items()
    }
    _write_json(Path(out_dir) / "l2.json", out)
    return out


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
    row = {
        "iso_year": f"{iso.upper()} {year}",
        "baseline_s": baseline_s,
        "total_s": wall,
        "uc_sum_s": summ.get("uc_total_s"),
        "uc_windows": summ.get("n_windows"),
        "uc_mean_s": summ.get("milp_s_mean"),
        "uc_p95_s": summ.get("milp_s_p95"),
        "ratio": (wall / baseline_s) if baseline_s else None,
        "integers_per_window": log.get("engine", {}).get("integers_per_window"),
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
