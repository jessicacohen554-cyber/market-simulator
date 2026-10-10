"""The UC stage at the P0 -> P1 seam (``unit_commitment_milp``): hook, markup zeroing, artifacts.

:func:`prepare_uc_stage` is called once by ``pipeline.solve.run_energy_solve``
(its one gated hunk) after the P1 markup is computed. It builds the cluster
struct-of-arrays, zeroes the amortized start markup on the integer clusters
(rule 19: their start and no-load are paid once, in the UC objective) and
installs the ``p1_fleet_prep`` hook. When the hook fires — after the full P1
bid is assembled — it runs the rolling windows (``model/uc``), stitches the
schedule, writes the stage artifacts and returns the P1 fleet with the
schedule as per-unit-hour bounds (DESIGN section 2.5):

* **ceiling** ``availability[g,t] * u[c,t] / n_c`` on every member of an
  integer cluster (the online share of the cluster's capacity);
* **floor** ``mlf_c * pbar_c * u[c,t]`` allocated to the members in proportion
  to their available capacity, composed through
  :func:`market_sim.pipeline.commitment._bridge_floored_fleet` under
  ``MECH_UC_SCHEDULE`` — the same maximum-composition tail every commitment
  bridge uses, so a floor exists only where the UC put a unit online.

An empty integer set (G-EMPTY) runs no MILP: the markup is returned as the
same object and the hook returns the upstream hook's result unchanged.

Artifacts are handed to the persisting orchestrators through
:func:`take_uc_artifacts` (the pass-timing-log drain pattern) and written by
:func:`write_uc_artifacts` INTO THE BUNDLE — ``hourly/uc_schedule_<y>.parquet``,
``hourly/uc_uplift_<y>.parquet`` (post-P1, from the P1 result the orchestrator
holds) and ``uc_solve_log_<y>.json`` at the bundle root — by the two-line
drain in ``scripts/run_calibration_full.py`` (backcast) and
``src/market_sim/runner.py`` (forecast), both under
``if config.unit_commitment_milp`` (UC-DESK review of DESIGN b974d2c9, point
3: a sidecar outside the bundle breaks rule 34). Monthly checkpoints (plan
E9) are scratch, never a sidecar: ``results/uc-checkpoints/<ISO>/<year>/``.
"""

from __future__ import annotations

import dataclasses
import logging
import resource
import time
from collections import deque
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pandas as pd  # noqa: F401  (type annotations of UcArtifacts)

from market_sim.config.paths import RESULTS_ROOT
from market_sim.data.fleet import FleetArrays
from market_sim.data.floor_mechanisms import MECH_UC_SCHEDULE
from market_sim.model.uc.params import (
    UcClusterParams,
    build_uc_cluster_params,
    params_log_rows,
    units_needed_for_floor,
    units_online_from_dispatch,
    units_online_profile,
)
from market_sim.model.uc.schedule import (
    UcSchedule,
    month_boundaries,
    write_schedule_parquet,
    write_solve_log,
)
from market_sim.model.uc.solve import (
    PHASE_KEYS,
    UcSolveOptions,
    solve_options_from_config,
    solve_window,
)
from market_sim.model.uc.window import (
    UcWindowModel,
    prefix_bounds,
    slice_window_inputs,
    window_fleet,
)
from market_sim.pipeline.commitment import _bridge_floored_fleet

logger = logging.getLogger(__name__)

#: Engine version stamped in every ``uc_solve_log`` (bumped on a formulation change).
#: uc-1.1: carried min-up / min-down history inside the Rajan–Takriti rows and
#: the look-ahead min-down guard (FINDING-ucmilp-1-fix-window-infeasibility-2026-10-04).
#: uc-1.2: the floor unit need is the one row (a) implies (``pbar * a`` per unit)
#: and the guard reads it on the window's own pinned fleet
#: (FINDING-ucmilp-fix2-floor-mindown-2026-10-10).
UC_ENGINE_VERSION = "uc-1.2"

#: The most recent stage objects (one per year solved in this process), for a
#: harness that writes the post-P1 uplift sidecar; drained by :func:`take_uc_stages`.
_STAGES: "deque[UcStage]" = deque(maxlen=8)


def take_uc_stages() -> list["UcStage"]:
    """Drain and return the stage objects run since the last call."""
    out = list(_STAGES)
    _STAGES.clear()
    return out


def uc_checkpoint_dir(iso: str, year: int, root: Path | None = None) -> Path:
    """``results/uc-checkpoints/<ISO>/<year>/`` — scratch for the monthly checkpoints (E9)."""
    return (
        Path(root or RESULTS_ROOT)
        / "uc-checkpoints"
        / str(iso).upper()
        / str(int(year))
    )


@dataclasses.dataclass(frozen=True)
class UcArtifacts:
    """One year's UC artifacts as the orchestrator receives them.

    Attributes:
        year: The solve year.
        schedule: The ``uc_schedule`` frame (cluster x hour, long).
        uplift: The ``uc_uplift`` frame (cluster x day) or ``None`` when no P1
            result was handed to :func:`take_uc_artifacts`.
        log: The ``uc_solve_log`` dict.
    """

    year: int
    schedule: "pd.DataFrame"
    uplift: "pd.DataFrame | None"
    log: dict


def take_uc_artifacts(p1_result=None) -> list[UcArtifacts]:
    """Drain the stages run since the last call into :class:`UcArtifacts`.

    ``p1_result`` (the scored P1 :class:`DispatchResult`, when the caller has
    it) prices the make-whole frame; without it ``uplift`` is ``None``.
    """
    out = []
    for stage in take_uc_stages():
        out.append(stage.artifacts(p1_result))
    return out


def write_uc_artifacts(
    run_dir: Path,
    year: int,
    artifacts: list[UcArtifacts],
    hourly_subdir: str | None = "hourly",
) -> list[Path]:
    """Write the artifacts of ``year`` into a bundle (the two-line drain's second line).

    ``hourly/uc_schedule_<y>.parquet`` and ``hourly/uc_uplift_<y>.parquet``
    (``hourly_subdir=None`` writes them beside the result parquet, the
    forecast cache layout) and ``uc_solve_log_<y>.json`` at ``run_dir``.
    """
    run_dir = Path(run_dir)
    paths: list[Path] = []
    for art in artifacts:
        if int(art.year) != int(year):
            continue
        hourly = run_dir / hourly_subdir if hourly_subdir else run_dir
        hourly.mkdir(parents=True, exist_ok=True)
        paths.append(
            write_schedule_parquet(art.schedule, hourly / f"uc_schedule_{year}.parquet")
        )
        if art.uplift is not None:
            up = hourly / f"uc_uplift_{year}.parquet"
            art.uplift.to_parquet(up, index=False)
            paths.append(up)
        paths.append(write_solve_log(art.log, run_dir / f"uc_solve_log_{year}.json"))
    return paths


def _peak_rss_gb() -> float:
    """Process peak resident set in GiB (``ru_maxrss`` is KiB on Linux)."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024**2)


#: Per-window phase keys summed into ``summary.phase_sums`` (seconds / counts);
#: the HiGHS phases (``solve.PHASE_KEYS`` minus the string source) plus the
#: stage's own timers around the solve.
PHASE_SUM_KEYS: tuple[str, ...] = tuple(
    k for k in PHASE_KEYS if k != "incumbent_src"
) + (
    "set_solution_s",
    "extract_s",
    "slim_s",
    "slice_s",
    "lp_build_s",
    "uc_build_s",
    "warm_vector_s",
    "solve_call_s",
    "keep_s",
    "window_s",
)


def phase_sums(windows: list[dict]) -> dict:
    """Sum each :data:`PHASE_SUM_KEYS` entry over ``windows[].phase`` (plus the incumbent-source histogram)."""
    out: dict = {}
    for key in PHASE_SUM_KEYS:
        vals = [float(w.get("phase", {}).get(key, 0.0) or 0.0) for w in windows]
        out[key] = round(float(sum(vals)), 3) if vals else 0.0
    hist: dict[str, int] = {}
    for w in windows:
        src = str(w.get("phase", {}).get("incumbent_src", "") or "")
        hist[src] = hist.get(src, 0) + 1
    out["incumbent_src_hist"] = hist
    out["warm_feasible_windows"] = int(
        sum(int(w.get("phase", {}).get("warm_feasible", 0) or 0) for w in windows)
    )
    return out


#: Per-window ``slim`` census keys summed into ``summary.slim_sums``.
SLIM_SUM_KEYS: tuple[str, ...] = (
    "cols_fixed_by_bounds",
    "cols_fixed_by_forcing",
    "cols_fixed_by_singleton",
    "cols_merged_parallel",
    "rows_dropped_redundant",
    "rows_dropped_singleton",
    "rows_dropped_empty",
)


def slim_sums(windows: list[dict]) -> dict:
    """Sum the slim census over ``windows[].slim`` (plus mean solved columns / rows and the windows reduced)."""
    out: dict = {k: 0 for k in SLIM_SUM_KEYS}
    reduced = [w for w in windows if w.get("slim") and w["slim"].get("reduced")]
    for w in reduced:
        for k in SLIM_SUM_KEYS:
            out[k] += int(w["slim"].get(k, 0) or 0)
    out["windows_reduced"] = len(reduced)
    out["solved_columns_mean"] = (
        round(
            float(np.mean([w["slim"]["columns"] for w in windows if w.get("slim")])), 1
        )
        if any(w.get("slim") for w in windows)
        else 0.0
    )
    out["solved_rows_mean"] = (
        round(float(np.mean([w["slim"]["rows"] for w in windows if w.get("slim")])), 1)
        if any(w.get("slim") for w in windows)
        else 0.0
    )
    return out


class UcStage:
    """One year's UC stage: parameters, the hook, the schedule and its log.

    Args:
        config: ScenarioConfig (reads the ``uc_*`` fields, ``iso``,
            ``weather_year``, ``hours``).
        fleet_arrays: The year's dispatch fleet.
        demand: ``(n_zones, T)``.
        dispatch_kwargs: The assembled LP kwargs.
        mc_base: ``(n_gen, T)`` base cost.
        r0: The P0 result (dispatch, prices, storage SOC).
        upstream_prep: The ``p1_fleet_prep`` the orchestrator composed before
            the stage (``None`` when nothing else floors the P1 fleet).
        bid_getter: Callable returning the FINAL P1 bid ``(n_gen, T)`` when the
            hook fires (late-bound: the bid is assembled after the stage is
            prepared).
        checkpoint_root: Override of ``RESULTS_ROOT`` for the scratch checkpoints (tests).
    """

    def __init__(
        self,
        config,
        fleet_arrays: FleetArrays,
        demand: np.ndarray,
        dispatch_kwargs: dict,
        mc_base: np.ndarray,
        r0,
        upstream_prep: Optional[Callable],
        bid_getter: Callable[[], np.ndarray],
        checkpoint_root: Path | None = None,
    ) -> None:
        self.config = config
        self.iso = str(getattr(config, "iso", ""))
        self.year = int(getattr(config, "weather_year", 0) or 0)
        self.T = int(getattr(config, "hours", demand.shape[1]))
        self.fleet_arrays = fleet_arrays
        self.demand = demand
        self.dispatch_kwargs = dispatch_kwargs
        self.mc_base = np.asarray(mc_base, dtype=float)
        self.r0 = r0
        self.upstream_prep = upstream_prep
        self.bid_getter = bid_getter
        self.checkpoint_dir = uc_checkpoint_dir(self.iso, self.year, checkpoint_root)
        self.params: UcClusterParams = build_uc_cluster_params(fleet_arrays, self.iso)
        self.int_idx = self.params.integer_clusters
        self.schedule: UcSchedule | None = None
        self.log: dict = {}
        self.ran = False
        self.W = int(config.uc_window_hours)
        self.L = int(config.uc_lookahead_hours)
        self.options: UcSolveOptions = solve_options_from_config(config)
        self.prefixing = bool(getattr(config, "uc_prefixing", False))
        self.slim = bool(getattr(config, "uc_slim_window", False))
        logger.info(
            "UC stage prepared: %d clusters, %d integer (%d fleet rows), W=%d L=%d",
            self.params.n_clusters,
            int(self.int_idx.size),
            int(self.params.integer_member_gens.size),
            self.W,
            self.L,
        )

    # ------------------------------------------------------------- markup
    def zero_markup(self, markup: np.ndarray) -> np.ndarray:
        """Zero the amortized P1 start markup on the integer clusters' rows.

        Returns ``markup`` itself (the same object) when the integer set is
        empty, so the empty-set path is byte-identical to the gate-off run.
        """
        rows = self.params.integer_member_gens
        if rows.size == 0:
            return markup
        out = np.array(markup, dtype=float, copy=True)
        out[rows, :] = 0.0
        return out

    # --------------------------------------------------------------- hook
    def p1_fleet_prep(self, r0) -> FleetArrays | None:
        """The ``p1_fleet_prep`` hook: upstream hook first, then the UC bounds."""
        base = self.upstream_prep(r0) if self.upstream_prep is not None else None
        if self.int_idx.size == 0:
            return base
        fleet_in = base if base is not None else self.fleet_arrays
        mc_bid = np.asarray(self.bid_getter(), dtype=float)
        self.run(fleet_in, mc_bid)
        return self.inject(fleet_in)

    # ---------------------------------------------------------------- run
    def run(
        self,
        fleet_in: FleetArrays,
        mc_bid: np.ndarray,
        t_start: int = 0,
        t_end: int | None = None,
        write: bool = True,
        record_states: bool = False,
        pin: UcSchedule | None = None,
    ) -> UcSchedule:
        """Solve the rolling windows over ``[t_start, t_end)`` and stitch the schedule.

        The production hook covers the whole year (``0 .. T``); the ladder's
        L2 rung solves one month at a time (``bench_uc_ladder.py``) and passes
        ``write=False`` (no checkpoint files). The first window's state comes from P0 at
        ``t_start - 1`` (cyclic for ``t_start == 0``, DESIGN section 2.2).

        ``record_states`` keeps each window's handed-over state on the
        schedule (``UcSchedule.prev_states``); ``pin`` makes this a PAIRED
        run (bench only): every window takes its carried state from ``pin``
        and the schedule advances along ``pin``, so each window is the same
        problem the pinned run solved and ``windows[].paired`` records this
        solver path's objective delta and kept-``u`` agreement against it.
        """
        t_end = self.T if t_end is None else min(int(t_end), self.T)
        t_init = (int(t_start) - 1) % self.T
        p = self.params
        k = self.int_idx
        T, W, L = self.T, self.W, self.L
        r0 = self.r0
        t_stage = time.perf_counter()
        int_rows = p.integer_member_gens
        mc_w_full = mc_bid.copy()
        mc_w_full[int_rows, :] = self.mc_base[int_rows, :]
        noload_full = p.noload_cost_per_unit_h(fleet_in, self.mc_base)[k]  # (n_int, T)
        self.noload_full = noload_full
        p0_dispatch = np.asarray(r0.dispatch, dtype=float)
        p0_soc = getattr(r0, "storage_soc", None)
        p0_prices = np.asarray(r0.prices, dtype=float)
        u_init = units_online_from_dispatch(p, p0_dispatch[:, t_init])[k]
        hist = int(max(int(p.ut_h[k].max()), int(p.dt_h[k].max())) - 1) if k.size else 0
        sched = UcSchedule(p, T, hist, record_states=record_states or pin is not None)
        if pin is not None and not pin.prev_states:
            raise ValueError("a paired run needs a pin built with record_states=True")
        # Each window's look-ahead guard rows read the floor unit needs of the
        # hours just past its horizon — up to the longest min-down minus one
        # hour — on the fleet a window covering those hours sees
        # (``window_fleet``: budget rows pinned to P0), never on the unpinned
        # year fleet (FINDING-ucmilp-fix2-floor-mindown-2026-10-10).
        guard_reach = int(p.dt_h[k].max()) - 1 if k.size else 0
        month_ends = month_boundaries(T)
        next_month = int(np.searchsorted(month_ends, t_start, side="right"))
        windows: list[dict] = []
        prev = None
        t0 = int(t_start)
        while t0 < t_end:
            t1 = min(t0 + W + L, T)
            t_w0 = time.perf_counter()
            inputs = slice_window_inputs(
                fleet_in,
                self.demand,
                self.dispatch_kwargs,
                t0,
                t1,
                p0_dispatch,
                p0_flows=getattr(r0, "flows", None),
            )
            state = (pin if pin is not None and t0 > t_start else sched).state_for(
                t0,
                fleet_in,
                u_init,
                p0_dispatch[:, t_init],
                None if p0_soc is None else np.asarray(p0_soc, dtype=float)[:, t_init],
            )
            soc_terminal = (
                None if p0_soc is None else np.asarray(p0_soc, dtype=float)[:, t1 - 1]
            )
            fix_on = fix_off = None
            if self.prefixing:
                fix_on, fix_off = prefix_bounds(
                    p,
                    k,
                    p.cluster_availability(inputs.fleet)[k],
                    p0_dispatch[:, t0:t1],
                    p0_prices[:, t0:t1],
                    self.mc_base[:, t0:t1],
                    np.asarray(fleet_in.zone_idx, dtype=int),
                    noload_full[:, t0:t1],
                )
            t_w1 = time.perf_counter()
            window = UcWindowModel(
                inputs,
                p,
                mc_w_full[:, t0:t1],
                noload_full[:, t0:t1],
                state,
                soc_terminal=soc_terminal,
                fix_on=fix_on,
                fix_off=fix_off,
                floor_need_ahead=self._floor_need_ahead(
                    fleet_in, p0_dispatch, t1, min(t1 + guard_reach, T)
                ),
                slim=self.slim,
            )
            t_w2 = time.perf_counter()
            warm = window.warm_start_vector(
                prev,
                W,
                p0_dispatch[:, t0:t1],
                units_online_profile(p, p0_dispatch[:, t0:t1])[k],
            )
            t_w3 = time.perf_counter()
            result = solve_window(
                window,
                self.options,
                warm,
                window_index=len(windows),
                t0=int(t0),
                t1=int(t1),
            )
            t_w4 = time.perf_counter()
            paired = None
            if pin is not None:
                kept_to = sched.keep_from(pin, t0, W)
                n_k = kept_to - t0
                paired = {
                    "u_kept_equal": bool(
                        np.array_equal(result.u[:, :n_k], pin.u[:, t0:kept_to])
                    ),
                    "u_cells_differ": int(
                        np.sum(result.u[:, :n_k] != pin.u[:, t0:kept_to])
                    ),
                }
            else:
                kept_to = sched.keep(result, t0, W)
            phase = dict(result.phase or {})
            phase.update(
                {
                    "slice_s": round(t_w1 - t_w0, 4),
                    "lp_build_s": round(result.lp_build_s, 4),
                    "uc_build_s": round(result.build_s - result.lp_build_s, 4),
                    "warm_vector_s": round(t_w3 - t_w2, 4),
                    "solve_call_s": round(t_w4 - t_w3, 4),
                    "keep_s": round(time.perf_counter() - t_w4, 4),
                    "window_s": round(time.perf_counter() - t_w0, 4),
                }
            )
            windows.append(
                {
                    "w": len(windows),
                    "t0": int(t0),
                    "t1": int(t1),
                    "build_s": round(result.build_s, 4),
                    "milp_s": round(result.milp_s, 4),
                    "phase": phase,
                    "nodes": int(result.nodes),
                    "gap": float(result.gap),
                    "status": result.status,
                    "time_limit_hit": bool(result.time_limit_hit),
                    "incumbent_warm": bool(result.warm_accepted),
                    "fixed_on": int(result.fixed_on),
                    "fixed_off": int(result.fixed_off),
                    "objective": float(result.objective),
                    "integers": int(result.integers),
                    "columns": int(result.columns),
                    "rows": int(result.rows),
                    "guard_rows": int(window._n_guard_rows),
                    "slim": {
                        "reduced": window.slim is not None,
                        "columns": int(result.slim_columns),
                        "rows": int(result.slim_rows),
                        **(result.slim_counts or {}),
                    },
                    "paired": paired,
                }
            )
            prev = result
            t0 = kept_to
            while next_month < len(month_ends) and kept_to >= month_ends[next_month]:
                next_month += 1
                if write and kept_to < T:
                    sched.checkpoint(
                        self.checkpoint_dir,
                        next_month,
                        self._log(windows, sched, partial=True),
                    )
        self.schedule = sched
        self.log = self._log(windows, sched, partial=False)
        self.log["summary"]["uc_total_s"] = round(time.perf_counter() - t_stage, 3)
        self.log["summary"]["peak_rss_gb"] = round(_peak_rss_gb(), 3)
        self.ran = True
        self.fleet_in = fleet_in
        _STAGES.append(self)
        logger.info(
            "UC stage done: %d windows, %.1f s, MILP mean %.2f s, nodes p50 %s, %d time-limit hits",
            len(windows),
            self.log["summary"]["uc_total_s"],
            self.log["summary"]["milp_s_mean"],
            self.log["summary"]["nodes_p50"],
            self.log["summary"]["time_limit_hits"],
        )
        return sched

    def _floor_need_ahead(
        self, fleet_in: FleetArrays, p0_dispatch: np.ndarray, h0: int, h1: int
    ) -> np.ndarray | None:
        """``(n_int, h1 - h0)`` floor unit needs past a window's horizon (zero LP).

        Computed on :func:`~market_sim.model.uc.window.window_fleet` of
        ``[h0, h1)`` — the same pinned availability and ``min_gen`` the window
        covering those hours builds its rows on — so the guard rows of one
        window and the bounds and rows of the next agree hour by hour.
        ``None`` when the range is empty (the year's last window).
        """
        if h1 <= h0:
            return None
        fleet_ahead, _ = window_fleet(
            fleet_in, self.dispatch_kwargs, h0, h1, p0_dispatch
        )
        return units_needed_for_floor(self.params, fleet_ahead, 0, h1 - h0)[
            self.int_idx
        ]

    def _log(self, windows: list[dict], sched: UcSchedule, partial: bool) -> dict:
        """Assemble the ``uc_solve_log`` dict (DESIGN section 4)."""
        c = self.config
        milp = np.array([w["milp_s"] for w in windows]) if windows else np.zeros(0)
        nodes = np.array([w["nodes"] for w in windows]) if windows else np.zeros(0)
        gaps = np.array([w["gap"] for w in windows]) if windows else np.zeros(0)
        return {
            "engine": {
                "version": UC_ENGINE_VERSION,
                "iso": self.iso,
                "year": self.year,
                "partial": bool(partial),
                "fields": {
                    "unit_commitment_milp": True,
                    "uc_window_hours": int(c.uc_window_hours),
                    "uc_lookahead_hours": int(c.uc_lookahead_hours),
                    "uc_mip_rel_gap": float(c.uc_mip_rel_gap),
                    "uc_window_time_limit_s": float(c.uc_window_time_limit_s),
                    "uc_integer_scope": str(c.uc_integer_scope),
                    "uc_noload_source": str(c.uc_noload_source),
                    "uc_boundary_mode": str(c.uc_boundary_mode),
                    "uc_prefixing": bool(getattr(c, "uc_prefixing", False)),
                    "uc_solver_preset": str(
                        getattr(c, "uc_solver_preset", "highs_default")
                    ),
                    "uc_slim_window": bool(getattr(c, "uc_slim_window", False)),
                },
                "solver_path": self.options.solver_path(),
                "threads": int(self.options.threads),
                "n_clusters": int(self.params.n_clusters),
                "integer_set_size": int(self.int_idx.size),
                "integer_fleet_rows": int(self.params.integer_member_gens.size),
                "integers_per_window": int(self.int_idx.size * (self.W + self.L)),
                "kept_until": int(sched.kept_until),
            },
            "clusters": params_log_rows(self.params),
            "windows": windows,
            "summary": {
                "n_windows": len(windows),
                "uc_total_s": None,
                "build_s_sum": round(float(sum(w["build_s"] for w in windows)), 3),
                "milp_s_sum": round(float(milp.sum()), 3) if milp.size else 0.0,
                "milp_s_mean": round(float(milp.mean()), 4) if milp.size else 0.0,
                "milp_s_p95": round(float(np.percentile(milp, 95)), 4)
                if milp.size
                else 0.0,
                "nodes_p50": float(np.percentile(nodes, 50)) if nodes.size else 0.0,
                "nodes_p95": float(np.percentile(nodes, 95)) if nodes.size else 0.0,
                "gap_p95": float(np.percentile(gaps[np.isfinite(gaps)], 95))
                if np.isfinite(gaps).any()
                else None,
                "time_limit_hits": int(sum(w["time_limit_hit"] for w in windows)),
                "windows_zero_nodes_share": float(np.mean(nodes == 0))
                if nodes.size
                else 0.0,
                "fixed_on_total": int(sum(w["fixed_on"] for w in windows)),
                "fixed_off_total": int(sum(w["fixed_off"] for w in windows)),
                "peak_rss_gb": None,
                "phase_sums": phase_sums(windows),
                "slim_sums": slim_sums(windows),
            },
        }

    # ---------------------------------------------------------- injection
    def floor_and_ceiling(self, fleet_in: FleetArrays) -> tuple[np.ndarray, np.ndarray]:
        """``(floor, availability)`` the schedule implies on the P1 fleet rows.

        Floor: ``mlf_c * pbar_c * u[c,t]`` split across the cluster's members
        in proportion to ``pmax * availability``; ceiling: the member's
        availability scaled by ``u / n_c``.
        """
        p = self.params
        k = self.int_idx
        sched = self.schedule
        if sched is None:
            raise RuntimeError("the UC stage has not run")
        n_gen, T = fleet_in.n_gen, self.T
        avail = np.array(fleet_in.availability, dtype=float, copy=True)
        floor = np.zeros((n_gen, T))
        if k.size == 0:
            return floor, avail
        u = np.maximum(sched.u.astype(float), 0.0)  # (n_int, T)
        int_local = np.full(p.n_clusters, -1)
        int_local[k] = np.arange(k.size)
        mem_mask = int_local[p.member_cluster] >= 0
        mem_gen = p.member_gen[mem_mask]
        mem_k = int_local[p.member_cluster[mem_mask]]
        pmax = np.asarray(fleet_in.pmax, dtype=float)
        share_num = pmax[mem_gen][:, None] * avail[mem_gen, :]  # (n_mem, T)
        share_den = np.zeros((k.size, T))
        np.add.at(share_den, mem_k, share_num)
        with np.errstate(invalid="ignore", divide="ignore"):
            share = np.where(share_den[mem_k] > 0.0, share_num / share_den[mem_k], 0.0)
        cluster_floor = (p.mlf[k] * p.pbar_mw[k])[:, None] * u  # (n_int, T)
        floor[mem_gen, :] = cluster_floor[mem_k] * share
        frac = u / p.n_units[k][:, None]  # (n_int, T)
        avail[mem_gen, :] = avail[mem_gen, :] * frac[mem_k]
        return floor, avail

    def inject(self, fleet_in: FleetArrays) -> FleetArrays:
        """The P1 fleet: ceiling applied, floor composed under ``MECH_UC_SCHEDULE``.

        The upstream floors are composed at their LP-EFFECTIVE level —
        ``min_gen`` clipped to ``pmax * availability`` of the fleet the stage
        was handed, the clip ``model.lp.bounds.build_variable_bounds`` applies
        to the P column in P0 — so the bridge tail's availability raise (which
        keeps a floor feasible) never re-opens a ceiling the schedule closed or
        lifts a floor P0 itself could not carry.
        """
        floor, avail = self.floor_and_ceiling(fleet_in)
        fields = {"availability": avail}
        if fleet_in.min_gen is not None:
            fields["min_gen"] = np.minimum(
                np.asarray(fleet_in.min_gen, dtype=float),
                np.asarray(fleet_in.pmax, dtype=float)[:, None]
                * np.asarray(fleet_in.availability, dtype=float),
            )
        capped = dataclasses.replace(fleet_in, **fields)
        return _bridge_floored_fleet(capped, floor, MECH_UC_SCHEDULE)

    # ---------------------------------------------------------- artifacts
    def artifacts(self, p1_result=None) -> UcArtifacts:
        """The year's :class:`UcArtifacts` (uplift priced when ``p1_result`` is given)."""
        if self.schedule is None:
            raise RuntimeError("the UC stage has not run")
        fleet_in = getattr(self, "fleet_in", self.fleet_arrays)
        noload = getattr(self, "noload_full", None)
        schedule = self.schedule.frame(fleet_in, self.year, noload)
        uplift = None
        if p1_result is not None and self.int_idx.size:
            from market_sim.model.uc.uplift import compute_uplift

            uplift = compute_uplift(
                self.params,
                self.schedule.u,
                self.schedule.v,
                np.asarray(p1_result.dispatch, dtype=float),
                np.asarray(p1_result.prices, dtype=float),
                np.asarray(fleet_in.zone_idx, dtype=int),
                self.mc_base,
                noload,
                self.year,
            )
        return UcArtifacts(
            year=self.year, schedule=schedule, uplift=uplift, log=self.log
        )


def prepare_uc_stage(
    config,
    fleet,
    fleet_arrays: FleetArrays,
    demand: np.ndarray,
    dispatch_kwargs: dict,
    mc_base: np.ndarray,
    r0,
    upstream_prep: Optional[Callable],
    bid_getter: Callable[[], np.ndarray],
) -> UcStage:
    """Build the year's :class:`UcStage` (the one call ``run_energy_solve`` makes).

    ``fleet`` (the ``list[Generator]``) is accepted for signature parity with
    the other seam builders and unused: every parameter is read from
    ``fleet_arrays`` and the frozen derive (rule 6).
    """
    return UcStage(
        config,
        fleet_arrays,
        demand,
        dispatch_kwargs,
        mc_base,
        r0,
        upstream_prep,
        bid_getter,
    )
