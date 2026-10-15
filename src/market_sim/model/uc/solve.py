"""The HiGHS MILP call for one UC window (integrality, gap, time limit, warm start, phase profile).

Options come from the registry (``uc_mip_rel_gap``, ``uc_window_time_limit_s``,
``uc_solver_preset``) through :class:`UcSolveOptions`
(:func:`solve_options_from_config`); the thread count is the solve container's
``MARKET_SIM_HIGHS_THREADS`` pin, read exactly where
:class:`~market_sim.model.lp.model.DispatchModel` reads it (the window model
inherits that handle), unless a bench arm asks for another count
(:attr:`UcSolveOptions.threads`, a harness argument).

**Solver path (plan E3/E5/E6/E7 as measured by lane UC-SPEED, 2026-10-09).** The
per-window wall is HiGHS's own work on the 36-hour MILP, not the model build
(SPP 2020 L1: build 0.04 s, MILP 4.2 s; the production P1 slice of the same
hours solves in 0.04 s). Measured on SPP 2020, January, 31 windows (the
profile shard, FINDING-ucmilp-speed-window-solve-profile-2026-10-09.md): of
160 s of ``run()``, MIP presolve 79 s, the LP-free feasibility jump 11 s, the
root LP 15 s and the post-root tail (rounding, central rounding, sub-MIP,
root restart with its second presolve) 53 s; every window solved at the root.
Presolve PAYS for itself — off, the root LP costs 67 s and the tail 80 s — so
it stays on. :data:`UC_SOLVER_PRESETS` names the two solver paths the
registry admits: ``highs_default`` (engine uc-1.1: presolve on, every HiGHS
heuristic and the root restart at its default) and ``lean`` (presolve on, the
feasibility jump off, the root restart off; since uc-1.8 the LP heuristics —
RINS / RENS / root reduced cost — ON: with the uc-1.6 reserve u-gate the node
LPs stop landing integral and the sub-MIP heuristics are the window's only
source of a good incumbent, FINDING-ucmilp-fix9-gated-window-slowdown-2026-10-15).
A preset
changes the solver's PATH, never the feasible set or the objective: for the
same window problem the optimum it returns is the same to ``uc_mip_rel_gap``
(the paired equivalence gate of the FINDING; a within-gap tie taken
differently in one window changes every later window's inputs, so the rolling
schedule hash is not the gate). A MIP root LP takes no user basis (measured:
identical iteration counts with and without ``setBasis``), so plan E3's
"basis carry" cannot reach it; the carried incumbent (``setSolution``) is the
warm start that exists and is kept (off: +8 % wall).

**Phase profile.** Every solve subscribes to HiGHS's log callback with a
timestamp per line and parses the MIP log into :data:`PHASE_KEYS`
(:func:`parse_highs_mip_log`): seconds in setup / presolve, the LP-free
heuristics before the root LP, the root LP itself, the post-root tail
(rounding, cuts, LP heuristics, branching) and the solving report, plus the
LP iteration split and the incumbent sources. The stage writes it per window
into ``uc_solve_log`` (``windows[].phase``) and sums it in ``summary``.

Outcomes (DESIGN section 2.4): ``Optimal`` and a gap-tolerance stop are the
solution; a time-limit stop WITH an incumbent is accepted and counted; a
window with no feasible incumbent raises :class:`UcWindowInfeasible` (an
engine defect, never a tuning invitation — GATESPEC section 5). Before it
raises, :func:`solve_window` names the window, re-solves the LP relaxation
on the same handle (row/bound contradiction vs integrality) and attaches the
zero-LP :func:`~market_sim.model.uc.diagnose.diagnose_window` report; with
``UcSolveOptions.debug_dump_dir`` set — a bench-harness argument, never a
registry field or an environment knob — it also writes the model, the
carried state and the report there.
"""

from __future__ import annotations

import dataclasses
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import highspy
import numpy as np

from market_sim.model.uc.diagnose import diagnose_window
from market_sim.model.uc.window import UcWindowInfeasible, UcWindowModel, WindowResult

#: HiGHS ``primal_solution_status`` value meaning a feasible primal point exists.
_PRIMAL_FEASIBLE = 2

#: The solver paths ``uc_solver_preset`` admits (``scenarios.UC_SOLVER_PRESET_NAMES``
#: lists the same names; ``tests/unit/model/uc/test_solve_presets.py`` holds
#: them equal). Each maps to the :class:`UcSolveOptions` solver-path fields.
#:
#: ``highs_default`` — engine uc-1.1's path: MIP presolve on (``solve_window``
#: set it explicitly), every HiGHS heuristic at its shipped default.
#: ``lean`` — presolve ON (it pays for itself: off, the root LP costs 4.5x),
#: the feasibility-jump heuristic off (11 s of 160 s, never the incumbent),
#: the root restart off (its second presolve is a third of the post-root
#: tail); symmetry detection stays on (off: +3 %). Composition fixed by the
#: UC-SPEED profile shard (SPP 2020, January, 31 windows):
#: FINDING-ucmilp-speed-window-solve-profile-2026-10-09.md section 2.
#: uc-1.8 (lane UC-1-FIX-9, UC-DESK ruling 2026-10-15): the LP-based
#: heuristics (RINS / RENS / root reduced cost; ``mip_heuristic_effort`` at
#: HiGHS's 0.05) are ON in ``lean``. UC-SPEED turned them off for -6 % on
#: ungated windows; under the uc-1.6 reserve u-gate a fractional ``u`` buys
#: reserve headroom, node LPs stop landing integral, and without the sub-MIP
#: incumbents the tree stalls at the root rounding (NEISO 2023 w12: bound
#: within 0.08 % of the optimum at the 600 s limit, incumbent +1.0 %). The
#: gap, time limit and model are unchanged
#: (FINDING-ucmilp-fix9-gated-window-slowdown-2026-10-15.md).
UC_SOLVER_PRESETS: dict[str, dict] = {
    "highs_default": dict(
        presolve="on",
        feasibility_jump=True,
        lp_heuristics=True,
        symmetry=True,
        restart=True,
    ),
    "lean": dict(
        presolve="on",
        feasibility_jump=False,
        lp_heuristics=True,
        symmetry=True,
        restart=False,
    ),
}

#: How many windows a ``raw_log_dir`` harness run dumps the raw HiGHS log for.
RAW_LOG_WINDOWS = 2

#: Keys of the per-window phase profile (seconds unless named otherwise).
PHASE_KEYS: tuple[str, ...] = (
    "setup_s",  # run() entry -> "Solving MIP model with" (user-solution check, repair LP, presolve)
    "presolve_s",  # "Presolving model" -> "Solving MIP model with" (0 when presolve is off)
    "pre_root_heur_s",  # header -> the last table row before the root LP finished (LP-free heuristics)
    "root_lp_s",  # -> the first table row with LP iterations (the root relaxation)
    "tail_s",  # root done -> "Solving report" (rounding, cuts, LP heuristics, branching)
    "report_s",  # "Solving report" -> run() return
    "lp_iters",  # total simplex iterations of the MIP
    "lp_iters_sep",  # of which cut separation
    "lp_iters_heur",  # of which heuristics
    "lp_iters_strong",  # of which strong branching
    "repair_lps",  # user-solution repair LPs HiGHS ran
    "warm_feasible",  # 1 when the user solution entered as an incumbent ("X" row), else 0
    "incumbent_src",  # the table's source letters in order, e.g. "JR"
)

_RE_TABLE_ROW = re.compile(
    r"^\s*([A-Za-z]?)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+%|-)\s+(\S+)\s+(\S+)\s+(\S+)\s+"
    r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)s"
)
_RE_LP_ITERS = re.compile(r"LP iterations\s+(\d+)")
_RE_ITER_PART = re.compile(r"^\s*(\d+)\s+\((strong br\.|separation|heuristics)\)")
_RE_REPAIR = re.compile(r"Repair LPs\s+(\d+)")


@dataclass(frozen=True)
class UcSolveOptions:
    """Solver settings of one window (every registry-backed value a registry field).

    ``mip_rel_gap`` / ``time_limit_s`` come from ``uc_mip_rel_gap`` /
    ``uc_window_time_limit_s``; the solver-path fields (``presolve``,
    ``feasibility_jump``, ``lp_heuristics``, ``symmetry``, ``restart``) come
    from ``uc_solver_preset`` through :data:`UC_SOLVER_PRESETS`.

    The remaining fields are bench-harness arguments, never registry fields or
    environment knobs: ``warm_start`` (the L2 "warm off" arm; the carried
    incumbent cannot change the optimum), ``threads`` (the L2 "threads" arm,
    plan E7 — ``0`` inherits the handle's setting, i.e. the solve container's
    pin; a positive count is set on the window handle together with
    ``parallel=on``, and the harness resets HiGHS's process-global scheduler
    around the arm because HiGHS fixes the scheduler's thread count at the
    first solve in a process) and ``debug_dump_dir`` (a directory the bench
    harness passes so an infeasible window leaves its model and state behind).
    """

    mip_rel_gap: float
    time_limit_s: float
    presolve: str = "on"
    feasibility_jump: bool = True
    lp_heuristics: bool = True
    symmetry: bool = True
    restart: bool = True
    warm_start: bool = True
    threads: int = 0
    debug_dump_dir: Path | None = None
    #: Harness-only: extra HiGHS options applied LAST, for a measurement arm
    #: (e.g. ``(("mip_lifting_for_probing", 0),)``). Never a registry value.
    extra_highs_options: tuple[tuple[str, object], ...] = ()
    #: Harness-only: directory receiving the raw stamped HiGHS log of the
    #: first :data:`RAW_LOG_WINDOWS` windows (``window_<i>_highs.log``).
    raw_log_dir: Path | None = None

    def solver_path(self) -> dict:
        """The solver-path fields as a dict (what a preset sets)."""
        return dict(
            presolve=self.presolve,
            feasibility_jump=self.feasibility_jump,
            lp_heuristics=self.lp_heuristics,
            symmetry=self.symmetry,
            restart=self.restart,
        )


def solve_options_from_config(config, **harness) -> UcSolveOptions:
    """The window :class:`UcSolveOptions` of a ``ScenarioConfig`` (plus harness arguments).

    Reads ``uc_mip_rel_gap``, ``uc_window_time_limit_s`` and ``uc_solver_preset``
    (an unknown preset name is refused here as well as in the config
    validator). ``harness`` may set ``warm_start`` / ``threads`` /
    ``debug_dump_dir`` or override a single solver-path field for a bench arm.
    """
    preset = str(getattr(config, "uc_solver_preset", "highs_default"))
    if preset not in UC_SOLVER_PRESETS:
        raise ValueError(
            f"uc_solver_preset {preset!r} is not one of {sorted(UC_SOLVER_PRESETS)}"
        )
    return UcSolveOptions(
        mip_rel_gap=float(config.uc_mip_rel_gap),
        time_limit_s=float(config.uc_window_time_limit_s),
        **{**UC_SOLVER_PRESETS[preset], **harness},
    )


def apply_solver_options(h: highspy.Highs, options: UcSolveOptions) -> None:
    """Set the HiGHS options of one window run from ``options`` (idempotent)."""
    h.setOptionValue("mip_rel_gap", float(options.mip_rel_gap))
    h.setOptionValue("time_limit", float(options.time_limit_s))
    h.setOptionValue("presolve", str(options.presolve))
    h.setOptionValue(
        "mip_heuristic_run_feasibility_jump", bool(options.feasibility_jump)
    )
    if options.lp_heuristics:
        h.setOptionValue("mip_heuristic_effort", 0.05)  # HiGHS shipped default
        for name in (
            "mip_heuristic_run_rins",
            "mip_heuristic_run_rens",
            "mip_heuristic_run_root_reduced_cost",
        ):
            h.setOptionValue(name, True)
    else:
        h.setOptionValue("mip_heuristic_effort", 0.0)
        for name in (
            "mip_heuristic_run_rins",
            "mip_heuristic_run_rens",
            "mip_heuristic_run_root_reduced_cost",
        ):
            h.setOptionValue(name, False)
    h.setOptionValue("mip_detect_symmetry", bool(options.symmetry))
    h.setOptionValue("mip_allow_restart", bool(options.restart))
    if int(options.threads) > 0:
        h.setOptionValue("threads", int(options.threads))
        h.setOptionValue("parallel", "on")
    for name, value in options.extra_highs_options:
        h.setOptionValue(str(name), value)


class _LogCollector:
    """Collects HiGHS log lines with a wall-clock stamp relative to ``run()`` entry."""

    def __init__(self) -> None:
        self.lines: list[tuple[float, str]] = []
        self.t0 = time.perf_counter()

    def __call__(self, event) -> None:
        self.lines.append((time.perf_counter() - self.t0, str(event.message)))


def parse_highs_mip_log(lines: list[tuple[float, str]], total_s: float) -> dict:
    """Phase seconds and counters from a stamped HiGHS MIP log (:data:`PHASE_KEYS`).

    ``lines`` are ``(seconds since run() entry, message)``; a message may hold
    several newline-separated log lines. ``total_s`` is the measured ``run()``
    wall, which the phases sum to (the report phase takes the remainder).
    """
    rows: list[tuple[float, str]] = []
    for t, msg in lines:
        for ln in str(msg).split("\n"):
            if ln.strip():
                rows.append((t, ln))
    t_presolve0 = t_header = t_report = None
    table: list[tuple[float, str, int]] = []  # (t, src, lp_iters)
    lp_iters = lp_sep = lp_heur = lp_strong = repair = 0
    for t, ln in rows:
        if ln.startswith("Presolving model") and t_presolve0 is None:
            t_presolve0 = t
        elif ln.startswith("Solving MIP model with") and t_header is None:
            t_header = t
        elif ln.startswith("Solving report") and t_report is None:
            t_report = t
        else:
            m = _RE_TABLE_ROW.match(ln)
            if m and t_header is not None and t_report is None:
                table.append((t, m.group(1), int(m.group(12))))
                continue
            m = _RE_LP_ITERS.search(ln)
            if m:
                lp_iters = int(m.group(1))
                continue
            m = _RE_ITER_PART.match(ln)
            if m and t_report is not None:
                n = int(m.group(1))
                if m.group(2) == "separation":
                    lp_sep = n
                elif m.group(2) == "heuristics":
                    lp_heur = n
                else:
                    lp_strong = n
                continue
            m = _RE_REPAIR.search(ln)
            if m:
                repair = int(m.group(1))
    t_header = t_header if t_header is not None else 0.0
    t_report = t_report if t_report is not None else float(total_s)
    presolve_s = max(0.0, t_header - t_presolve0) if t_presolve0 is not None else 0.0
    first_lp = next((i for i, r in enumerate(table) if r[2] > 0), None)
    if first_lp is None:
        pre_root = table[-1][0] - t_header if table else 0.0
        root_lp = max(0.0, t_report - t_header - pre_root)
        tail = 0.0
    else:
        t_before = table[first_lp - 1][0] if first_lp > 0 else t_header
        pre_root = max(0.0, t_before - t_header)
        root_lp = max(0.0, table[first_lp][0] - t_before)
        tail = max(0.0, t_report - table[first_lp][0])
    srcs = "".join(r[1] for r in table if r[1])
    return {
        "setup_s": round(max(0.0, t_header), 4),
        "presolve_s": round(presolve_s, 4),
        "pre_root_heur_s": round(pre_root, 4),
        "root_lp_s": round(root_lp, 4),
        "tail_s": round(tail, 4),
        "report_s": round(max(0.0, float(total_s) - t_report), 4),
        "lp_iters": lp_iters,
        "lp_iters_sep": lp_sep,
        "lp_iters_heur": lp_heur,
        "lp_iters_strong": lp_strong,
        "repair_lps": repair,
        "warm_feasible": int("X" in srcs),
        "incumbent_src": srcs,
    }


def _set_full_u_integrality(window: UcWindowModel, integer: bool) -> None:
    """Integrality of every ``u`` on the FULL handle (the diagnosis relaxation)."""
    u_idx = window.u_cols_full()
    if not u_idx.size:
        return
    kind = (
        highspy.HighsVarType.kInteger if integer else highspy.HighsVarType.kContinuous
    )
    window.h.changeColsIntegrality(int(u_idx.size), u_idx, [kind] * int(u_idx.size))


def _relaxation_status(window: UcWindowModel) -> str:
    """Re-solve the window's LP relaxation on its FULL handle; restore integrality after."""
    _set_full_u_integrality(window, integer=False)
    try:
        window.h.clearSolver()
        window.h.run()
        return window.h.modelStatusToString(window.h.getModelStatus())
    finally:
        _set_full_u_integrality(window, integer=True)


def _dump_window(
    window: UcWindowModel,
    out_dir: Path,
    window_index: int | None,
    t0: int | None,
    report: dict,
    warm_values: np.ndarray | None,
) -> list[Path]:
    """Write ``window_<w>.mps``, ``window_<w>_state.npz`` and ``window_<w>_diagnosis.json``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"window_{window_index if window_index is not None else 'x'}"
    paths = [out_dir / f"{tag}.mps"]
    window.h.writeModel(str(paths[0]))
    p, k = window.params, window.int_idx
    paths.append(out_dir / f"{tag}_state.npz")
    np.savez_compressed(
        paths[-1],
        t0=-1 if t0 is None else int(t0),
        u_lower=window.u_lower,
        u_upper=window.u_upper,
        hist_v=window.hist_v,
        hist_w=window.hist_w,
        n_units=p.n_units[k],
        ut_h=p.ut_h[k],
        dt_h=p.dt_h[k],
        plant_code=p.plant_code[k],
        family=p.family[k].astype(str),
        warm=np.asarray([] if warm_values is None else warm_values, dtype=float),
    )
    paths.append(out_dir / f"{tag}_diagnosis.json")
    paths[-1].write_text(json.dumps(report, indent=1, default=str))
    return paths


def _plants_text(report: dict) -> str:
    """The plants the diagnosis names, as exception text (empty when none)."""
    parts = []
    for key, label in (
        ("clusters_floor_above_min_down", "floor above min-down"),
        ("clusters_ceiling_contradiction", "ceiling contradicted"),
        ("clusters_history_starts_above_n", "carried starts above n"),
    ):
        rows = report.get(key) or []
        if rows:
            parts.append(
                f"{label} at "
                + "; ".join(
                    f"plant {r['plant_code']} {r['family']} (n={r['n']}, "
                    f"dt={r.get('dt_h')}, pinned {r.get('pinned_members', 0)}/"
                    f"{r.get('members', 0)} members, hours {r.get('hours', [])})"
                    for r in rows
                )
            )
    return (" — " + " | ".join(parts)) if parts else ""


def solve_window(
    window: UcWindowModel,
    options: UcSolveOptions,
    warm_values: np.ndarray | None = None,
    relax: bool = False,
    window_index: int | None = None,
    t0: int | None = None,
    t1: int | None = None,
) -> WindowResult:
    """Solve one window and return its :class:`WindowResult` (phase profile attached).

    Args:
        window: The built window model.
        options: Gap / time limit / solver path (and the harness arguments).
        warm_values: Optional full column vector for ``setSolution``.
        relax: Solve the LP relaxation instead (ladder rung L1 (b)): every
            ``u`` column is made continuous for this call and restored after.
        window_index, t0, t1: The rolling window's index and hour range, for
            the :class:`UcWindowInfeasible` report (the stage passes them;
            a bare window test may not).

    Raises:
        UcWindowInfeasible: No feasible incumbent — with the window named,
            the LP relaxation's status and the zero-LP diagnosis attached.
    """
    # The handle that runs is the slim window's when the reduction applied
    # (``uc_slim_window``), else the full model's; every read of the
    # solution below comes back through ``window.from_solve_space``.
    h = window.h_solve
    # HiGHS's log is the phase profile's source: logging on, console off, the
    # lines collected by the callback with a wall-clock stamp each.
    h.setOptionValue("output_flag", True)
    h.setOptionValue("log_to_console", False)
    apply_solver_options(h, options)
    n_u = window.V0 - window.U0
    if relax and n_u:
        window.set_u_integrality(False)
    warm = False
    t_warm = time.perf_counter()
    if options.warm_start and warm_values is not None and not relax:
        sol = highspy.HighsSolution()
        sol.col_value = window.to_solve_space(warm_values).tolist()
        sol.value_valid = True
        warm = h.setSolution(sol) == highspy.HighsStatus.kOk
    set_solution_s = time.perf_counter() - t_warm
    collector = _LogCollector()
    h.cbLogging.subscribe(collector)
    t0_clock = time.perf_counter()
    collector.t0 = t0_clock
    try:
        h.run()
    finally:
        milp_s = time.perf_counter() - t0_clock
        try:
            h.cbLogging.unsubscribe(collector)
        except Exception:  # pragma: no cover - a profile hook never breaks a solve
            pass
    if (
        options.raw_log_dir is not None
        and window_index is not None
        and window_index < RAW_LOG_WINDOWS
    ):
        out = Path(options.raw_log_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"window_{window_index}_highs.log").write_text(
            "".join(f"[{t:8.3f}s] {m}" for t, m in collector.lines)
        )
    status = h.getModelStatus()
    status_str = h.modelStatusToString(status)
    _, primal = h.getInfoValue("primal_solution_status")
    feasible = int(primal) == _PRIMAL_FEASIBLE
    time_limit_hit = status == highspy.HighsModelStatus.kTimeLimit
    if status != highspy.HighsModelStatus.kOptimal and not (
        time_limit_hit and feasible
    ):
        if relax and n_u:
            window.set_u_integrality(True)
        report = diagnose_window(window)
        relaxation = status_str if relax else _relaxation_status(window)
        where = (f"window {window_index}" if window_index is not None else "window") + (
            f" [{t0}, {t1})" if t0 is not None and t1 is not None else ""
        )
        bad = report.get("contradictory_rows", {})
        summary = ", ".join(f"{fam}={v['count']}" for fam, v in bad.items()) or "none"
        if options.debug_dump_dir is not None:
            _dump_window(
                window, options.debug_dump_dir, window_index, t0, report, warm_values
            )
        raise UcWindowInfeasible(
            f"UC {where} solve ended {status_str} with "
            f"{'a' if feasible else 'no'} feasible incumbent "
            f"({window.n_total} columns, {window.h.getNumRow()} rows, "
            f"{window.n_int} integer clusters; solved as "
            f"{h.getNumCol()} x {h.getNumRow()}"
            f"{' slim' if window.slim is not None else ''}); "
            f"LP relaxation: {relaxation}; "
            f"a-priori contradictory rows: {summary}; "
            f"carried starts above n: {report.get('history_starts_above_n', 0)}; "
            f"floor above min-down: {report.get('floor_above_min_down', 0)}"
            f"{_plants_text(report)}",
            window_index=window_index,
            t0=t0,
            t1=t1,
            relaxation_status=relaxation,
            diagnosis=report,
        )
    t_extract = time.perf_counter()
    info = h.getInfo()
    sol = h.getSolution()
    col_value = window.from_solve_space(np.asarray(sol.col_value, dtype=float))
    if relax and n_u:
        window.set_u_integrality(True)
    gap = float(info.mip_gap) if n_u and not relax else 0.0
    nodes = int(info.mip_node_count) if n_u and not relax else 0
    phase = (
        parse_highs_mip_log(collector.lines, milp_s)
        if n_u and not relax
        else {k: (0 if k != "incumbent_src" else "") for k in PHASE_KEYS}
    )
    phase["set_solution_s"] = round(set_solution_s, 4)
    phase["slim_s"] = round(float(window.slim_s), 4)
    result = window.extract(
        col_value,
        objective=float(info.objective_function_value),
        status=status_str,
        gap=gap if np.isfinite(gap) else float("inf"),
        nodes=nodes,
        time_limit_hit=bool(time_limit_hit),
        milp_s=milp_s,
        warm_accepted=warm,
        phase=phase,
    )
    phase["extract_s"] = round(time.perf_counter() - t_extract, 4)
    return result


def options_for_arm(options: UcSolveOptions, **changes) -> UcSolveOptions:
    """A copy of ``options`` with the given fields replaced (the bench arms' helper)."""
    return dataclasses.replace(options, **changes)
