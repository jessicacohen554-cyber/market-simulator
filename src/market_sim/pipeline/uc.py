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
* **floor** ``mlf_c * pbar_c * a_c[t] * u[c,t]`` (the window's row (b), on the
  window fleet's availability) filled into the members in MERIT
  ORDER of the P1 offer (:func:`merit_floor_allocation`: cheapest member-hour
  first, each up to its ceiling, the remainder carried to the next), composed
  through :func:`market_sim.pipeline.commitment._bridge_floored_fleet` under
  ``MECH_UC_SCHEDULE`` — the same maximum-composition tail every commitment
  bridge uses, so a floor exists only where the UC put a unit online. A
  CAMPD-binned plant's members are offer tranches of the same physical units,
  whose minimum stable output is produced by the lowest-cost segment first
  (FINDING-ucmilp-fix4-floor-merit-2026-10-10, defect 6).

A second stage of the same year (ERCOT's adaptive-expectation pass 2) whose
inputs digest identically to the previous stage's (:func:`uc_input_digest`)
reuses that stage's schedule instead of re-solving the windows: the windows
are a deterministic function of exactly those inputs.

The same digest certifies a committed bundle's DA schedule across runs when
the run opts in (``uc_da_schedule_reuse_bundle``, owner ruling R15): the
schedule is read from that leg's ``uc_schedule`` instead of re-solving.

The reliability-commitment (RUC) pass (``uc_reliability_commitment``, owner
ruling R12; DESIGN-ucmilp-ruc-stage-2026-10-16 section 2) runs AFTER the
scored-P1 candidate ("P1a"): :meth:`UcStage.reliability_commitment` screens
P1a at zero LP for hours with energy slack or a reserve shortfall, re-solves
those days' windows add-only (``u >= u_DA``) against the RUC load basis on a
commitment-cost objective, sweeps forward until the carried state rejoins the
DA schedule, and returns the P1 fleet for "P1b" through the same MECH 28
bounds. No trigger: P1a is final and nothing else changes.

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
import hashlib
import logging
import resource
import time
from collections import deque
from pathlib import Path
from typing import Callable, Optional, Sequence

import numpy as np
import pandas as pd
import scipy.sparse as sp

from market_sim.config.constants import (
    STORAGE_TIEBREAKER_EPSILON,
    VLR_GROUP_MIN_COMMITTED_UNITS,
)
from market_sim.config.paths import RESULTS_ROOT
from market_sim.data.commitment_demand import CommitmentDemand, commitment_demand
from market_sim.data.fleet import FleetArrays
from market_sim.data.floor_mechanisms import MECH_UC_SCHEDULE
from market_sim.data.vlr_pocket_groups import load_vlr_pocket_groups
from market_sim.model.uc.params import (
    UcClusterParams,
    build_uc_cluster_params,
    demote_budget_pinned,
    params_log_rows,
    units_needed_for_floor,
    units_online_from_dispatch,
    units_online_profile,
)
from market_sim.model.uc.pocket import PocketRequirement, build_pocket_requirement
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
    WindowResult,
    budget_pinned_gens,
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
#: (FINDING-ucmilp-fix2-floor-mindown-2026-10-10); a cluster whose members are
#: all budget-pinned carries no integer (UC-DESK ruling, option (a)).
#: uc-1.4: the P1 floor is the window's row (b) floor ``mlf * pbar * a * u``
#: (availability-weighted, on the window fleet), not ``mlf * pbar * u``.
#: uc-1.3: the P1 floor fills a cluster's members in merit order of the P1
#: offer, capped at each member's ceiling (FINDING-ucmilp-fix4-floor-merit-2026-10-10);
#: a stage whose inputs digest identically to the previous stage's reuses its schedule.
#: uc-1.5: integer clusters' UC energy (and the uplift cost side) on the
#: incremental basis — the average-rate offer less the no-load heat it carries
#: per MWh at full output — so the explicit no-load is paid once
#: (FINDING-ucmilp-fix5-cost-basis-2026-10-14).
#: uc-1.6: an integer cluster member's share of every reserve headroom row the
#: window carries is its committed capacity ``pmax * a * u / n``, not
#: ``pmax * a`` (``window.reserve_headroom_u_terms``;
#: FINDING-ucmilp-fix6-reserve-headroom-2026-10-14). A no-op without
#: reserve co-optimization.
#: uc-1.7: the window balances against the COMMITMENT DEMAND
#: (``uc_commitment_demand_source``; ``data/commitment_demand.py``; owner
#: ruling UC-DESK r13): the P1 demand at "actual" (the uc-1.6 windows, the same
#: object), the measured EIA-930 day-ahead forecast mapped to zones at
#: "da_forecast". P1 still clears on actual load (rule 4). The same version
#: carries the VLR load-pocket commitment rows (``vlr_pocket_commitment``,
#: lane UC-MISO-VLR, #7263; default off, no row when off) and the SPP
#: synchronized-reserve restriction of the windows' reserve classes to the
#: integer members (``spp_spinning_reserve_share``, lane UC-SPP-SPIN, #7261;
#: default off, no override when off). Lane UC-1-FIX-8 maps the "da_forecast"
#: increment onto the runtime zone rows by name (interchange rows get none)
#: without a bump: wherever uc-1.7 built a schedule the runtime zones were the
#: configured zones and the commitment demand is bit-identical; everywhere
#: else uc-1.7 raised before any schedule existed.
#: uc-1.8 (lane UC-1-FIX-9, UC-DESK ruling 2026-10-15): the ``lean`` solver
#: path runs HiGHS's LP-based heuristics (``model/uc/solve.py::
#: UC_SOLVER_PRESETS``). A solver-path change only: the window model, its
#: integer feasible set, the gap and the time limit are unchanged; a window's
#: optimum moves at most within ``uc_mip_rel_gap``. The version and the solve
#: options both enter :func:`uc_input_digest`, so no uc-1.7 schedule is reused.
#: uc-1.9 (lane UC-RUC-BUILD, owner ruling R12, 2026-10-16): the
#: reliability-commitment pass (``uc_reliability_commitment``, default off;
#: :meth:`UcStage.reliability_commitment`) and the R15 DA-schedule reuse across
#: runs (``uc_da_schedule_reuse_bundle``). The DA windows are unchanged, so the
#: input digest keeps hashing :data:`UC_DA_DIGEST_VERSION`.
UC_ENGINE_VERSION = "uc-1.9"

#: The engine version the DA-window problem last changed at, hashed into
#: :func:`uc_input_digest` in place of :data:`UC_ENGINE_VERSION`: uc-1.9 added a
#: pass AFTER the DA windows and left their problem, solver path and options
#: untouched, so a uc-1.8 DA schedule of the same inputs is the same schedule
#: (the certificate the R15 cross-run reuse rests on). Bump it with any change
#: to what the DA windows solve.
UC_DA_DIGEST_VERSION = "uc-1.8"

#: ``uc_*`` fields read only AFTER the DA windows (the RUC pass) or naming
#: where a DA schedule may be read from: excluded from :func:`uc_input_digest`,
#: which certifies the DA problem alone.
UC_DIGEST_EXCLUDED_FIELDS: frozenset[str] = frozenset(
    {
        "uc_reliability_commitment",
        "uc_ruc_load_basis",
        "uc_da_schedule_reuse_bundle",
    }
)

#: The most recent stage objects (one per year solved in this process), for a
#: harness that writes the post-P1 uplift sidecar; drained by :func:`take_uc_stages`.
_STAGES: "deque[UcStage]" = deque(maxlen=8)


#: The last solved stage's schedule, keyed by its input digest (one slot): a
#: later stage of the same process with the same digest reuses it. Holds the
#: schedule, the log and the no-load array only (``n_int x T`` each).
_LAST_SOLVED: dict = {}


def _digest_update(h, obj, opaque: list[str]) -> None:
    """Feed ``obj`` into hash ``h`` by value (arrays by dtype, shape and bytes).

    Containers and dataclasses recurse; a scipy sparse matrix is fed by value
    (CSR ``data`` / ``indices`` / ``indptr`` / shape). Any other type has no
    by-value encoding: it is named in ``opaque`` and the caller FORFEITS reuse
    (a ``repr`` need not distinguish two different objects, so it can never
    certify equal inputs).
    """
    if obj is None or isinstance(obj, (bool, int, float, str, np.generic)):
        h.update(f"{type(obj).__name__}:{obj!r};".encode())
    elif isinstance(obj, np.ndarray):
        a = np.ascontiguousarray(obj)
        h.update(f"nd:{a.dtype.str}:{a.shape};".encode())
        if a.dtype == object:
            for x in a.ravel():
                _digest_update(h, x, opaque)
        else:
            h.update(a.view(np.uint8).ravel() if a.size else b"")
    elif isinstance(obj, dict):
        h.update(f"dict:{len(obj)};".encode())
        for key in sorted(obj, key=repr):
            _digest_update(h, key, opaque)
            _digest_update(h, obj[key], opaque)
    elif isinstance(obj, (list, tuple)):
        h.update(f"{type(obj).__name__}:{len(obj)};".encode())
        for x in obj:
            _digest_update(h, x, opaque)
    elif isinstance(obj, (set, frozenset)):
        _digest_update(h, sorted(obj, key=repr), opaque)
    elif dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        h.update(f"dc:{type(obj).__name__};".encode())
        for f in dataclasses.fields(obj):
            _digest_update(h, f.name, opaque)
            _digest_update(h, getattr(obj, f.name), opaque)
    elif sp.issparse(obj):
        m = sp.csr_matrix(obj)
        h.update(f"sp:{m.dtype.str}:{m.shape};".encode())
        for a in (m.data, m.indices, m.indptr):
            _digest_update(h, np.asarray(a), opaque)
    elif isinstance(obj, (pd.DataFrame, pd.Series, pd.Index)):
        h.update(f"pd:{type(obj).__name__}:{obj.shape};".encode())
        _digest_update(h, [str(c) for c in getattr(obj, "columns", [])], opaque)
        h.update(pd.util.hash_pandas_object(obj, index=True).to_numpy().tobytes())
    else:
        opaque.append(type(obj).__name__)
        h.update(f"opaque:{type(obj).__name__}:{obj!r};".encode())


def uc_input_digest(
    stage: "UcStage", fleet_in: FleetArrays, mc_bid: np.ndarray
) -> tuple[str, list[str]]:
    """``(hex digest, opaque type names)`` of everything :meth:`UcStage.run` reads.

    The DA-window version (:data:`UC_DA_DIGEST_VERSION`), the ISO / year /
    horizon, every ``uc_*`` config field the DA windows read (all but
    :data:`UC_DIGEST_EXCLUDED_FIELDS`),
    the solve options, the cluster parameters, the year fleet and the hooked
    P1 fleet, demand and the commitment demand, the dispatch kwargs,
    ``mc_base``, the final P1 bid and
    the P0 dispatch / storage SOC / prices / flows. Two stages with equal
    digests build the same windows from the same state, so the second may take
    the first's schedule.
    """
    h = hashlib.blake2b(digest_size=32)
    opaque: list[str] = []
    cfg = stage.config
    uc_fields = {
        name: getattr(cfg, name)
        for name in sorted(dir(cfg))
        if name.startswith("uc_")
        and name not in UC_DIGEST_EXCLUDED_FIELDS
        and not callable(getattr(cfg, name, None))
    }
    r0 = stage.r0
    for part in (
        UC_DA_DIGEST_VERSION,
        stage.iso,
        stage.year,
        stage.T,
        stage.W,
        stage.L,
        stage.prefixing,
        stage.slim,
        # The pocket requirement is not a ``uc_*`` field: hash it by value when
        # armed (absent off, so a gate-off digest is unchanged).
        *(() if stage.pocket is None else (stage.pocket,)),
        uc_fields,
        repr(stage.options),
        stage.params,
        stage.fleet_arrays,
        fleet_in,
        stage.demand,
        stage.commit.demand,
        stage.dispatch_kwargs,
        stage.mc_base,
        np.asarray(mc_bid, dtype=float),
        np.asarray(r0.dispatch, dtype=float),
        getattr(r0, "storage_soc", None),
        np.asarray(r0.prices, dtype=float),
        getattr(r0, "flows", None),
    ):
        _digest_update(h, part, opaque)
    return h.hexdigest(), sorted(set(opaque))


def merit_floor_allocation(
    member_k: np.ndarray,
    member_gen: np.ndarray,
    cluster_floor: np.ndarray,
    cap: np.ndarray,
    mc: np.ndarray,
) -> np.ndarray:
    """``(n_mem, T)`` member floors: each cluster's floor filled in merit order.

    Per cluster-hour the members are ranked by ascending ``mc`` (the P1 offer
    the LP sees for that member-hour; ties by fleet row ``member_gen``), and
    the floor is poured into them in that order, each up to its ``cap`` (the
    member's ceiling, ``pmax * availability * u / n``), the remainder carried
    to the next member. A floor above the cluster's summed ceiling is filled to
    the ceiling and the rest dropped (no member is floored above what the
    schedule left it). Vectorised: one ``lexsort`` per hour axis and a cumsum
    over a ``(T, n_int, M)`` block, ``M`` = the most members any cluster has
    (no loop over hours or members).

    Args:
        member_k: ``(n_mem,)`` local integer-cluster index of each member.
        member_gen: ``(n_mem,)`` fleet row of each member (the tie-break).
        cluster_floor: ``(n_int, T)`` cluster floor MW.
        cap: ``(n_mem, T)`` member ceiling MW (non-negative).
        mc: ``(n_mem, T)`` member P1 offer $/MWh.
    """
    member_k = np.asarray(member_k, dtype=int)
    n_mem = int(member_k.size)
    T = int(np.asarray(cluster_floor).shape[1])
    if n_mem == 0:
        return np.zeros((0, T))
    cap_t = np.maximum(np.asarray(cap, dtype=float), 0.0).T  # (T, n_mem)
    mc_t = np.asarray(mc, dtype=float).T
    k_b = np.broadcast_to(member_k, (T, n_mem))
    g_b = np.broadcast_to(np.asarray(member_gen, dtype=int), (T, n_mem))
    # Primary key the cluster, so a cluster occupies the same sorted span in
    # every hour; then ascending offer; then fleet row.
    order = np.lexsort((g_b, mc_t, k_b), axis=-1)  # (T, n_mem)
    ks = np.sort(member_k, kind="stable")  # cluster of each sorted slot
    n_int = int(np.asarray(cluster_floor).shape[0])
    start = np.searchsorted(ks, np.arange(n_int), side="left")
    pos = np.arange(n_mem) - start[ks]  # slot within its cluster
    M = int(pos.max()) + 1
    cap_s = np.take_along_axis(cap_t, order, axis=1)  # (T, n_mem)
    block = np.zeros((T, n_int, M))
    block[:, ks, pos] = cap_s
    filled_before = (np.cumsum(block, axis=2) - block)[:, ks, pos]  # (T, n_mem)
    floor_s = np.asarray(cluster_floor, dtype=float).T[:, ks]
    alloc_s = np.clip(floor_s - filled_before, 0.0, cap_s)
    alloc_t = np.empty_like(alloc_s)
    np.put_along_axis(alloc_t, order, alloc_s, axis=1)
    return alloc_t.T


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


def lp_feasibility_tolerance() -> float:
    """HiGHS's own ``primal_feasibility_tolerance`` (the LP's, never a new constant).

    The P1 LP runs at the solver default (``model/lp/model.py`` sets no
    tolerance), so the RUC trigger reads the same value from a fresh handle:
    a slack or shortfall at or below it is solver round-off, not a shortfall.
    """
    import highspy

    out = highspy.Highs().getOptionValue("primal_feasibility_tolerance")
    return float(out[1] if isinstance(out, tuple) else out)


def ruc_trigger_hours(p1a, tol: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(trigger, slack_mw, shortfall_mw)`` — the zero-LP RUC screen of P1a.

    ``trigger[t]``: the hour's energy slack (summed over zones) or its largest
    reserve-family ORDC shortfall exceeds ``tol``. Families are not summed
    (a synchronized family is nested in its contingency family; DESIGN
    section 3.1 note 1). No reserve co-optimization: slack alone.
    """
    slack = np.asarray(p1a.slack, dtype=float).sum(axis=0)
    fam = getattr(p1a, "reserve_shortfall_by_family", None)
    short = (
        np.zeros_like(slack)
        if fam is None or np.asarray(fam).size == 0
        else np.asarray(fam, dtype=float).max(axis=1)
    )
    return (slack > tol) | (short > tol), slack, short


def ruc_load_basis_demand(stage: "UcStage") -> np.ndarray:
    """``(n_zones, T)`` demand the RUC windows commit against (``uc_ruc_load_basis``).

    "actual": the P1 demand the stage was handed (realised load; the declared
    upper bound of an intraday basis, DESIGN section 2.2). A measured intraday
    basis enters here with its intake (lane UC-DF-AUDIT); the config refuses
    any other value until then (``UC_RUC_LOAD_BASES``).
    """
    basis = str(getattr(stage.config, "uc_ruc_load_basis", "actual"))
    if basis == "actual":
        return stage.demand
    raise ValueError(f"uc_ruc_load_basis {basis!r} has no loader")


class UcStage:
    """One year's UC stage: parameters, the hook, the schedule and its log.

    Args:
        config: ScenarioConfig (reads the ``uc_*`` fields, ``iso``,
            ``weather_year``, ``hours``).
        fleet_arrays: The year's dispatch fleet.
        demand: ``(n_zones, T)`` P1 demand. The windows balance against the
            commitment demand built from it
            (:func:`~market_sim.data.commitment_demand.commitment_demand`,
            ``uc_commitment_demand_source``); at "actual" that is ``demand``.
        dispatch_kwargs: The assembled LP kwargs.
        mc_base: ``(n_gen, T)`` base cost.
        r0: The P0 result (dispatch, prices, storage SOC).
        upstream_prep: The ``p1_fleet_prep`` the orchestrator composed before
            the stage (``None`` when nothing else floors the P1 fleet).
        bid_getter: Callable returning the FINAL P1 bid ``(n_gen, T)`` when the
            hook fires (late-bound: the bid is assembled after the stage is
            prepared).
        checkpoint_root: Override of ``RESULTS_ROOT`` for the scratch checkpoints (tests).
        zone_names: The solve's runtime zone list (``demand``'s row order,
            interchange zones included); the "da_forecast" commitment demand
            maps its increment onto these rows by name (lane UC-1-FIX-8).
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
        zone_names: Sequence[str] | None = None,
    ) -> None:
        self.config = config
        self.iso = str(getattr(config, "iso", ""))
        self.year = int(getattr(config, "weather_year", 0) or 0)
        self.T = int(getattr(config, "hours", demand.shape[1]))
        self.fleet_arrays = fleet_arrays
        self.demand = demand
        #: What the windows commit against (``uc_commitment_demand_source``).
        self.commit: CommitmentDemand = commitment_demand(config, demand, zone_names)
        self.dispatch_kwargs = dispatch_kwargs
        self.mc_base = np.asarray(mc_base, dtype=float)
        self.r0 = r0
        self.upstream_prep = upstream_prep
        self.bid_getter = bid_getter
        self.checkpoint_dir = uc_checkpoint_dir(self.iso, self.year, checkpoint_root)
        gate_params = build_uc_cluster_params(fleet_arrays, self.iso)
        #: Integer clusters the E1 gate admits, before the budget-pin demotion.
        self.integer_gate_size = int(gate_params.integer.sum())
        # A cluster whose members are all pinned to P0 by a dropped budget
        # family carries no integer: its commitment is the identity's
        # (``demote_budget_pinned``, rule 19).
        self.params: UcClusterParams
        self.params, self.pinned_demoted = demote_budget_pinned(
            gate_params, budget_pinned_gens(dispatch_kwargs)
        )
        self.int_idx = self.params.integer_clusters
        # Synchronized reserve classes (SPP spinning share): restricted to the
        # integer members for the windows and P1 (P0 keeps the design as built).
        #: P1 kwargs overrides the stage owns (``{}`` = none; see solve.py).
        self.p1_kwargs_overrides: dict = synchronized_reserve_overrides(
            dispatch_kwargs, self.params
        )
        if self.p1_kwargs_overrides:
            self.dispatch_kwargs = {**dispatch_kwargs, **self.p1_kwargs_overrides}
        self.schedule: UcSchedule | None = None
        #: The DA schedule when the RUC pass replaced :attr:`schedule` (else ``None``).
        self.schedule_da: UcSchedule | None = None
        #: The RUC pass is armed (``uc_reliability_commitment``).
        self.ruc_armed = bool(getattr(config, "uc_reliability_commitment", False))
        #: The P1 bid the schedule was solved on (the merit order of the floor).
        self.mc_bid: np.ndarray | None = None
        self.log: dict = {}
        self.ran = False
        self.W = int(config.uc_window_hours)
        self.L = int(config.uc_lookahead_hours)
        self.options: UcSolveOptions = solve_options_from_config(config)
        self.prefixing = bool(getattr(config, "uc_prefixing", False))
        self.slim = bool(getattr(config, "uc_slim_window", False))
        #: The VLR load-pocket requirement (``vlr_pocket_commitment``), built
        #: on the post-demotion params so a demoted cluster carries no row.
        self.pocket: PocketRequirement | None = None
        if bool(getattr(config, "vlr_pocket_commitment", False)):
            self.pocket = build_pocket_requirement(
                self.params,
                load_vlr_pocket_groups(self.iso),
                VLR_GROUP_MIN_COMMITTED_UNITS,
            )
            logger.info(
                "VLR pocket requirement: %d set(s) %s; unmatched groups %s",
                self.pocket.n_sets,
                list(self.pocket.labels),
                list(self.pocket.unmatched),
            )
        logger.info(
            "UC stage prepared: %d clusters, %d integer (%d fleet rows; %d "
            "all-budget-pinned clusters left to their budget identity), W=%d L=%d",
            self.params.n_clusters,
            int(self.int_idx.size),
            int(self.params.integer_member_gens.size),
            int(self.pinned_demoted.size),
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
        self.mc_bid = mc_bid
        t0 = time.perf_counter()
        digest, opaque = uc_input_digest(self, fleet_in, mc_bid)
        digest_s = time.perf_counter() - t0
        # An input with no by-value encoding cannot certify equality: no reuse.
        prior = None if opaque else _LAST_SOLVED.get(digest)
        reuse_bundle = str(getattr(self.config, "uc_da_schedule_reuse_bundle", "") or "")
        if prior is not None:
            self.adopt(prior, fleet_in, digest, digest_s)
        elif reuse_bundle:
            self.adopt_committed(Path(reuse_bundle), fleet_in, digest, opaque, digest_s)
            _LAST_SOLVED.clear()
            _LAST_SOLVED[digest] = {
                "schedule": self.schedule,
                "log": self.log,
                "noload_full": self.noload_full,
            }
        else:
            self.run(fleet_in, mc_bid)
            _LAST_SOLVED.clear()
            _LAST_SOLVED[digest] = {
                "schedule": self.schedule,
                "log": self.log,
                "noload_full": self.noload_full,
            }
        self.log["engine"]["input_digest"] = digest
        self.log["engine"]["input_digest_opaque_types"] = opaque
        self.log["engine"]["input_digest_s"] = round(digest_s, 3)
        return self.inject(fleet_in)

    def adopt(
        self, prior: dict, fleet_in: FleetArrays, digest: str, digest_s: float
    ) -> None:
        """Take a previous stage's schedule (equal input digest) instead of solving.

        The log is the solving stage's, with ``engine.reused_schedule`` set and
        ``summary.uc_total_s`` the digest time (the windows were not re-solved).
        """
        import copy

        self.schedule = prior["schedule"]
        self.noload_full = prior["noload_full"]
        self.log = copy.deepcopy(prior["log"])
        # A previous stage's RUC block belongs to that stage's P1a.
        self.log.pop("ruc", None)
        self.log["engine"]["reused_schedule"] = {
            "input_digest": digest,
            "solved_uc_total_s": self.log["summary"].get("uc_total_s"),
        }
        self.log["summary"]["uc_total_s"] = round(digest_s, 3)
        self.ran = True
        self.fleet_in = fleet_in
        _STAGES.append(self)
        logger.info(
            "UC stage: inputs identical to the previous stage (digest %s), "
            "schedule reused; %d windows not re-solved",
            digest[:12],
            int(self.log["summary"]["n_windows"]),
        )

    def adopt_committed(
        self,
        bundle: Path,
        fleet_in: FleetArrays,
        digest: str,
        opaque: list[str],
        digest_s: float,
    ) -> None:
        """Take a committed leg's DA schedule (owner ruling R15) when the digests match.

        Reads ``<bundle>/uc_solve_log_<y>.json`` and
        ``<bundle>/hourly/uc_schedule_<y>.parquet``. Raises — never a silent
        re-solve — when this run's digest has an opaque part (it cannot certify
        equality), the year's files are absent, or the recorded
        ``engine.input_digest`` differs from this run's: the run opted in to
        reuse, so a mismatch is a recipe difference the operator must see.
        The log is the committed leg's, with ``engine.version`` / ``fields``
        re-stamped to this run and ``engine.reused_schedule`` naming the source.
        """
        import copy
        import json

        bundle = Path(bundle)
        log_path = bundle / f"uc_solve_log_{self.year}.json"
        sched_path = bundle / "hourly" / f"uc_schedule_{self.year}.parquet"
        if opaque:
            raise ValueError(
                "uc_da_schedule_reuse_bundle: this run's UC input digest has "
                f"opaque parts {opaque}; it cannot certify equal inputs"
            )
        if not log_path.is_file() or not sched_path.is_file():
            raise FileNotFoundError(
                f"uc_da_schedule_reuse_bundle: {bundle} has no committed DA "
                f"schedule for {self.year} ({log_path.name}, {sched_path.name})"
            )
        committed = json.loads(log_path.read_text())
        recorded = (committed.get("engine") or {}).get("input_digest")
        if recorded != digest:
            raise ValueError(
                "uc_da_schedule_reuse_bundle: the committed leg's UC input digest "
                f"{recorded} != this run's {digest} ({log_path}); the DA problem "
                "differs, so its schedule cannot be reused"
            )
        p = self.params
        k = self.int_idx
        hist = int(max(int(p.ut_h[k].max()), int(p.dt_h[k].max())) - 1) if k.size else 0
        self.schedule = UcSchedule.from_frame(
            p, self.T, hist, pd.read_parquet(sched_path)
        )
        self.noload_full = p.noload_cost_per_unit_h(fleet_in, self.mc_base)[k]
        self.log = copy.deepcopy(committed)
        self.log.pop("ruc", None)
        solved_version = self.log["engine"].get("version")
        fresh = self._log([], self.schedule, partial=False)["engine"]
        self.log["engine"]["version"] = UC_ENGINE_VERSION
        self.log["engine"]["fields"] = fresh["fields"]
        self.log["engine"]["reused_schedule"] = {
            "source": "committed_bundle",
            "bundle": str(bundle),
            "input_digest": digest,
            "solved_engine_version": solved_version,
            "solved_uc_total_s": self.log["summary"].get("uc_total_s"),
        }
        self.log["summary"]["uc_total_s"] = round(digest_s, 3)
        self.ran = True
        self.fleet_in = fleet_in
        _STAGES.append(self)
        logger.info(
            "UC stage: DA schedule read from committed bundle %s (digest %s, "
            "solved at %s); windows not re-solved",
            bundle,
            digest[:12],
            solved_version,
        )

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
        self.mc_bid = mc_bid
        t_stage = time.perf_counter()
        int_rows = p.integer_member_gens
        # Integer clusters: base cost on the incremental basis (the explicit
        # no-load below is the only place the no-load heat is paid, rule 19;
        # UcClusterParams.incremental_energy_cost). Every other row: the P1 bid.
        mc_uc = p.incremental_energy_cost(fleet_in, self.mc_base)
        mc_w_full = mc_bid.copy()
        mc_w_full[int_rows, :] = mc_uc[int_rows, :]
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
                self.commit.demand,
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
                    mc_uc[:, t0:t1],
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
                pocket=self.pocket,
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
                    "reserve_gated_rows": int(window.n_reserve_gated_rows),
                    "pocket_rows": int(window._n_pocket_rows),
                    "pocket_sets_skipped": int(window.pocket_sets_skipped),
                    "slim": {
                        "reduced": window.slim is not None,
                        "columns": int(result.slim_columns),
                        "rows": int(result.slim_rows),
                        **(result.slim_counts or {}),
                    },
                    "paired": paired,
                }
            )
            logger.info(
                "UC window %d [%d, %d): %s, MILP %.2f s, %d nodes, gap %.2e%s",
                len(windows) - 1,
                t0,
                t1,
                result.status,
                result.milp_s,
                int(result.nodes),
                float(result.gap),
                ", time limit" if result.time_limit_hit else "",
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
                    "uc_commitment_demand_source": str(
                        getattr(c, "uc_commitment_demand_source", "actual")
                    ),
                    "vlr_pocket_commitment": bool(
                        getattr(c, "vlr_pocket_commitment", False)
                    ),
                    "uc_reliability_commitment": bool(
                        getattr(c, "uc_reliability_commitment", False)
                    ),
                    "uc_ruc_load_basis": str(
                        getattr(c, "uc_ruc_load_basis", "actual")
                    ),
                    "uc_da_schedule_reuse_bundle": str(
                        getattr(c, "uc_da_schedule_reuse_bundle", "")
                    ),
                },
                "commitment_demand": self.commit.log_row(self.demand),
                "solver_path": self.options.solver_path(),
                "threads": int(self.options.threads),
                "n_clusters": int(self.params.n_clusters),
                "integer_set_size": int(self.int_idx.size),
                "integer_gate_size": int(self.integer_gate_size),
                "integer_demoted_budget_pinned": [
                    int(self.params.plant_code[c]) for c in self.pinned_demoted
                ],
                "integer_fleet_rows": int(self.params.integer_member_gens.size),
                "integers_per_window": int(self.int_idx.size * (self.W + self.L)),
                "kept_until": int(sched.kept_until),
                "reused_schedule": None,
                "vlr_pocket": None
                if self.pocket is None
                else {
                    "min_units_per_group": int(VLR_GROUP_MIN_COMMITTED_UNITS),
                    "sets": self.pocket.log_rows(self.params),
                    "unmatched_groups": list(self.pocket.unmatched),
                },
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

    # ---------------------------------------------------------------- RUC
    def reliability_commitment(self, p1a) -> FleetArrays | None:
        """The RUC pass (DESIGN-ucmilp-ruc-stage-2026-10-16 section 2.1): ``None`` or the P1b fleet.

        Screens ``p1a`` (zero LP, :func:`ruc_trigger_hours`). No trigger hour:
        returns ``None`` — P1a is the scored P1 and nothing the stage holds
        changes. Otherwise re-solves the windows of the triggered days with
        the existing :class:`~market_sim.model.uc.window.UcWindowModel` on the
        same ``W + L`` slice, changed in exactly four places:

        * demand = the RUC load basis (:func:`ruc_load_basis_demand`);
        * ``u >= u_DA`` (add-only; the look-ahead guard also reads ``u_DA``
          past the horizon, so no stop strands a DA unit);
        * every dispatch column costs the rule-9 epsilon
          (``STORAGE_TIEBREAKER_EPSILON``): energy cost leaves the decision;
        * a unit-hour online costs no-load plus minimum-load energy
          ``mlf * pbar * a * max(mc_uc, 0)`` at the anchor (start cost
          unchanged; a negative energy cost is floored at zero so the pass
          never commits for economics);

        P1's penalties (VOLL, the reserve demand curves) are the window LP's
        own and unchanged. The sweep runs forward from each triggered day and
        stops once the carried state (``u``, start / stop history over the
        longest min-up / min-down) equals the DA schedule's and the next day is
        not triggered. The first window of an episode carries P1a's dispatch
        and storage level at ``t0 - 1`` (the realised state; the DA pass keeps
        no per-window state); later windows carry their predecessor's. No
        pre-fixing (an economic heuristic on the DA objective). The final
        schedule replaces :attr:`schedule` (the DA one is kept in
        :attr:`schedule_da`) and is injected exactly as the DA one is.
        """
        if not self.ruc_armed or self.int_idx.size == 0 or self.schedule is None:
            return None
        t_ruc = time.perf_counter()
        tol = lp_feasibility_tolerance()
        trig, slack, short = ruc_trigger_hours(p1a, tol)
        W, L, T = self.W, self.L, self.T
        starts = sorted({int(h) // W * W for h in np.flatnonzero(trig)})
        block: dict = {
            "load_basis": str(getattr(self.config, "uc_ruc_load_basis", "actual")),
            "trigger_tolerance": tol,
            "trigger_hours": int(trig.sum()),
            "trigger_hours_slack": int((slack > tol).sum()),
            "trigger_hours_reserve": int((short > tol).sum()),
            "trigger_days": [int(t0 // W) for t0 in starts],
            "p1a_slack_mwh": round(float(slack.sum()), 3),
            "p1a_max_need_mw": round(float((slack + short).max(initial=0.0)), 3),
        }
        self.log["ruc"] = block
        if not starts:
            block.update({"episodes": 0, "n_windows": 0, "ruc_total_s": 0.0})
            logger.info("RUC: no trigger hour in P1a; P1a is final")
            return None
        p = self.params
        k = self.int_idx
        fleet_in = self.fleet_in
        da = self.schedule
        final = da.copy()
        demand = ruc_load_basis_demand(self)
        r0 = self.r0
        p0_dispatch = np.asarray(r0.dispatch, dtype=float)
        p0_soc = getattr(r0, "storage_soc", None)
        p1_dispatch = np.asarray(p1a.dispatch, dtype=float)
        p1_soc = getattr(p1a, "storage_soc", None)
        n_gen = int(np.asarray(fleet_in.pmax).size)
        mc_uc = p.incremental_energy_cost(fleet_in, self.mc_base)
        guard_reach = int(p.dt_h[k].max()) - 1
        hist = da.H
        t_init = T - 1
        u_init = units_online_from_dispatch(p, p0_dispatch[:, t_init])[k]
        windows: list[dict] = []
        episodes: list[list[int]] = []
        start_set = set(starts)
        prev: WindowResult | None = None
        t0 = starts[0]
        new_episode = True
        while t0 < T:
            t1 = min(t0 + W + L, T)
            if new_episode:
                episodes.append([int(t0), int(t0)])
                prev = None
                if t0 > 0:
                    # The realised (P1a) state the episode starts from.
                    final.kept_until = t0
                    final.dispatch_prev = p1_dispatch[:, t0 - 1].copy()
                    final.soc_prev = (
                        None
                        if p1_soc is None
                        else np.asarray(p1_soc, dtype=float)[:, t0 - 1].copy()
                    )
            state = final.state_for(
                t0,
                fleet_in,
                u_init,
                p0_dispatch[:, t_init],
                None if p0_soc is None else np.asarray(p0_soc, dtype=float)[:, t_init],
            )
            inputs = slice_window_inputs(
                fleet_in,
                demand,
                self.dispatch_kwargs,
                t0,
                t1,
                p0_dispatch,
                p0_flows=getattr(r0, "flows", None),
            )
            a = p.cluster_availability(inputs.fleet)[k]  # (n_int, T_w)
            # Minimum-load energy cost per unit-hour, never negative: a
            # negative commitment cost would make the RUC commit for energy
            # economics, which is the DA pass's job, not for reliability.
            minload = (p.mlf[k] * p.pbar_mw[k])[:, None] * a * np.maximum(
                mc_uc[p.anchor_gen[k], t0:t1], 0.0
            )
            u_da = da.u[:, t0:t1].astype(float)
            ahead = self._floor_need_ahead(
                fleet_in, p0_dispatch, t1, min(t1 + guard_reach, T)
            )
            if ahead is not None:
                ahead = np.maximum(ahead, da.u[:, t1 : t1 + ahead.shape[1]])
            window = UcWindowModel(
                inputs,
                p,
                np.full((n_gen, t1 - t0), STORAGE_TIEBREAKER_EPSILON),
                self.noload_full[:, t0:t1] + minload,
                state,
                soc_terminal=None
                if p0_soc is None
                else np.asarray(p0_soc, dtype=float)[:, t1 - 1],
                floor_need_ahead=ahead,
                slim=self.slim,
                pocket=self.pocket,
                u_floor=u_da,
            )
            warm = window.warm_start_vector(
                prev, W, p1_dispatch[:, t0:t1], u_da
            )
            result = solve_window(
                window,
                self.options,
                warm,
                window_index=len(windows),
                t0=int(t0),
                t1=int(t1),
            )
            kept_to = final.keep(result, t0, W)
            windows.append(
                {
                    "w": len(windows),
                    "t0": int(t0),
                    "t1": int(t1),
                    "triggered": int(t0) in start_set,
                    "milp_s": round(result.milp_s, 4),
                    "build_s": round(result.build_s, 4),
                    "nodes": int(result.nodes),
                    "gap": float(result.gap),
                    "status": result.status,
                    "time_limit_hit": bool(result.time_limit_hit),
                    "objective": float(result.objective),
                    "added_unit_hours": int(
                        (final.u[:, t0:kept_to] - da.u[:, t0:kept_to]).sum()
                    ),
                }
            )
            logger.info(
                "RUC window %d [%d, %d)%s: %s, MILP %.2f s, +%d unit-h",
                len(windows) - 1,
                t0,
                t1,
                " (triggered)" if int(t0) in start_set else " (sweep)",
                result.status,
                result.milp_s,
                windows[-1]["added_unit_hours"],
            )
            episodes[-1][1] = int(kept_to)
            prev = result
            rejoined = kept_to >= T or (
                np.array_equal(final.u[:, kept_to - 1], da.u[:, kept_to - 1])
                and np.array_equal(
                    final.v[:, max(0, kept_to - hist) : kept_to],
                    da.v[:, max(0, kept_to - hist) : kept_to],
                )
                and np.array_equal(
                    final.w[:, max(0, kept_to - hist) : kept_to],
                    da.w[:, max(0, kept_to - hist) : kept_to],
                )
            )
            if kept_to in start_set or not rejoined:
                t0 = kept_to
                new_episode = False
                continue
            later = [s0 for s0 in starts if s0 > kept_to]
            if not later:
                break
            t0 = later[0]
            new_episode = True
        final.kept_until = T
        added = final.u.astype(int) - da.u.astype(int)
        if (added < 0).any():
            raise RuntimeError(
                "RUC de-committed a DA unit (u_final < u_DA); the add-only "
                "bound did not hold"
            )
        swept = np.zeros(T, dtype=bool)
        for e0, e1 in episodes:
            swept[e0:e1] = True
        fleet_w, _ = window_fleet(fleet_in, self.dispatch_kwargs, 0, T, p0_dispatch)
        a_year = p.cluster_availability(fleet_w)[k]
        added_floor = (p.mlf[k] * p.pbar_mw[k])[:, None] * a_year * added
        fam = p.family[k].astype(str)
        milp = [w["milp_s"] for w in windows]
        block.update(
            {
                "episodes": len(episodes),
                "swept_hours": [[int(e0), int(e1)] for e0, e1 in episodes],
                "n_windows": len(windows),
                "windows": windows,
                "time_limit_hits": int(sum(w["time_limit_hit"] for w in windows)),
                "milp_s_sum": round(float(sum(milp)), 3),
                "added_unit_hours": int(added.sum()),
                "added_unit_hours_by_class": {
                    c: int(added[fam == c].sum()) for c in sorted(set(fam))
                },
                "added_floor_mwh": round(float(added_floor.sum()), 3),
                "added_floor_mwh_by_class": {
                    c: round(float(added_floor[fam == c].sum()), 3)
                    for c in sorted(set(fam))
                },
                "added_floor_mwh_outside_swept": round(
                    float(added_floor[:, ~swept].sum()), 3
                ),
                "add_only": True,
            }
        )
        self.schedule_da = da
        self.schedule = final
        block["ruc_total_s"] = round(time.perf_counter() - t_ruc, 3)
        logger.info(
            "RUC done: %d trigger h on %d days, %d episode(s), %d windows, "
            "+%d unit-h, +%.1f MWh floor, %.1f s",
            block["trigger_hours"],
            len(starts),
            len(episodes),
            len(windows),
            block["added_unit_hours"],
            block["added_floor_mwh"],
            block["ruc_total_s"],
        )
        return self.inject(fleet_in)

    # ---------------------------------------------------------- injection
    def floor_and_ceiling(
        self, fleet_in: FleetArrays, mc: np.ndarray | None = None
    ) -> tuple[np.ndarray, np.ndarray]:
        """``(floor, availability)`` the schedule implies on the P1 fleet rows.

        Ceiling: the member's availability scaled by ``u / n_c``. Floor:
        ``mlf_c * pbar_c * a_c[t] * u[c,t]`` — exactly the floor the window's
        row (b) enforced, with ``a_c`` the cluster availability on
        :func:`~market_sim.model.uc.window.window_fleet` of the year (the
        pinned, hour-local fleet every window builds its rows on;
        FINDING-ucmilp-fix4-floor-merit-2026-10-10 §6.1) — filled into the
        cluster's members in merit order of ``mc`` (the final P1 bid; default
        the bid the hook read), each up to its ceiling
        ``pmax * availability * u / n_c`` (:func:`merit_floor_allocation`).
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
        mc = self.mc_bid if mc is None else mc
        u = np.maximum(sched.u.astype(float), 0.0)  # (n_int, T)
        int_local = np.full(p.n_clusters, -1)
        int_local[k] = np.arange(k.size)
        mem_mask = int_local[p.member_cluster] >= 0
        mem_gen = p.member_gen[mem_mask]
        mem_k = int_local[p.member_cluster[mem_mask]]
        pmax = np.asarray(fleet_in.pmax, dtype=float)
        frac = u / p.n_units[k][:, None]  # (n_int, T)
        avail[mem_gen, :] = avail[mem_gen, :] * frac[mem_k]
        cap = (
            pmax[mem_gen][:, None] * avail[mem_gen, :]
        )  # (n_mem, T), after the ceiling
        fleet_w, _ = window_fleet(
            fleet_in, self.dispatch_kwargs, 0, T, np.asarray(self.r0.dispatch)
        )
        a = p.cluster_availability(fleet_w)[k]  # (n_int, T), row (b)'s a
        cluster_floor = (p.mlf[k] * p.pbar_mw[k])[:, None] * a * u  # (n_int, T)
        floor[mem_gen, :] = merit_floor_allocation(
            mem_k,
            mem_gen,
            cluster_floor,
            cap,
            np.asarray(mc, dtype=float)[mem_gen, :],
        )
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
                self.params.incremental_energy_cost(fleet_in, self.mc_base),
                noload,
                self.year,
            )
            if self.ruc_armed:
                uplift = ruc_uplift_columns(
                    uplift,
                    self.params,
                    self.schedule,
                    self.schedule_da if self.schedule_da is not None else self.schedule,
                    noload,
                )
        return UcArtifacts(
            year=self.year, schedule=schedule, uplift=uplift, log=self.log
        )


def ruc_uplift_columns(
    uplift: pd.DataFrame,
    params: UcClusterParams,
    final: UcSchedule,
    da: UcSchedule,
    noload_per_unit: np.ndarray,
) -> pd.DataFrame:
    """Add the RUC make-whole columns to the ``uc_uplift`` frame (cluster x day).

    ``ruc_added_units`` = unit-hours the RUC added over the DA schedule;
    ``ruc_noload_usd`` = their no-load; ``ruc_start_usd`` = the start cost of
    the final schedule less the DA schedule's (net, per cluster-day: a start
    the RUC moved to an earlier day counts there and is credited where the DA
    start was dropped). Zero everywhere in a year the RUC did not touch.
    Reported, never priced (rule 4).
    """
    k = params.integer_clusters
    n_int, T = final.u.shape
    n_days = int(np.ceil(T / 24))

    def _by_day(x: np.ndarray) -> np.ndarray:
        pad = n_days * 24 - T
        xp = np.concatenate([x, np.zeros((n_int, pad))], axis=1) if pad else x
        return xp.reshape(n_int, n_days, 24).sum(axis=2).ravel()

    du = final.u.astype(float) - da.u.astype(float)
    dv = final.v.astype(float) - da.v.astype(float)
    su = (params.su_per_mw[k] * params.pbar_mw[k])[:, None]
    out = uplift.copy()
    out["ruc_added_units"] = _by_day(du)
    out["ruc_start_usd"] = _by_day(su * dv)
    out["ruc_noload_usd"] = _by_day(np.asarray(noload_per_unit, dtype=float) * du)
    return out


def synchronized_reserve_overrides(
    dispatch_kwargs: dict, params: UcClusterParams
) -> dict:
    """Restrict every SYNCHRONIZED reserve class to the integer-cluster members.

    A synchronized class (``reserve_synchronized``; SPP's Spinning share,
    ``spp_spinning_reserve_share``) may count only capacity that is online.
    The UC stage is the one place a commitment state exists: an integer
    member's headroom in the window is ``pmax * a * u / n``
    (:func:`~market_sim.model.uc.window.reserve_headroom_u_terms`) and in P1
    its availability is the schedule's ``a * u / n``. Every other member
    (a fast-start cluster, a budget-pinned demoted cluster, a non-cluster
    row) has no commitment state here, so it is dropped from the class:
    its offline capacity must not count, and the LP cannot tell it online.

    Returns:
        ``{"reserve_eligible": <restricted mask>}`` when the kwargs carry a
        synchronized class, else ``{}`` (the stage then holds the caller's
        dict itself, byte-identical).
    """
    sync = dispatch_kwargs.get("reserve_synchronized")
    elig = dispatch_kwargs.get("reserve_eligible")
    if (
        sync is None
        or elig is None
        or dispatch_kwargs.get("reserve_requirement") is None
    ):
        return {}
    sync = np.asarray(sync, dtype=bool)
    if not sync.any():
        return {}
    elig2d = np.atleast_2d(np.asarray(elig, dtype=bool))
    if elig2d.shape[0] != sync.size:
        raise ValueError(
            f"reserve_synchronized has {sync.size} classes, reserve_eligible "
            f"{elig2d.shape[0]}"
        )
    is_int = np.zeros(elig2d.shape[1], dtype=bool)
    is_int[params.integer_member_gens] = True
    out = elig2d.copy()
    out[sync] &= is_int
    logger.info(
        "UC synchronized reserve: class(es) %s restricted to integer members "
        "(%d of %d eligible rows kept)",
        np.flatnonzero(sync).tolist(),
        int(out[sync].sum()),
        int(elig2d[sync].sum()),
    )
    return {"reserve_eligible": out}


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
    zone_names: Sequence[str] | None = None,
) -> UcStage:
    """Build the year's :class:`UcStage` (the one call ``run_energy_solve`` makes).

    ``fleet`` (the ``list[Generator]``) is accepted for signature parity with
    the other seam builders and unused: every parameter is read from
    ``fleet_arrays`` and the frozen derive (rule 6). ``zone_names`` is the
    solve's runtime zone list (:class:`UcStage`).
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
        zone_names=zone_names,
    )
