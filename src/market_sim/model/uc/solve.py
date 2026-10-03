"""The HiGHS MILP call for one UC window (integrality, gap, time limit, warm start).

Options come from the registry (``uc_mip_rel_gap``, ``uc_window_time_limit_s``)
through :class:`UcSolveOptions`; the thread count is the solve container's
``MARKET_SIM_HIGHS_THREADS`` pin, read exactly where
:class:`~market_sim.model.lp.model.DispatchModel` reads it (the window model
inherits that handle). Presolve is left at HiGHS's default for a MIP: the
annual LP's ``presolve=off`` reasoning (a 22-30 M column dispatch LP that
presolve barely reduces) does not transfer to a 100 k column MIP.

Outcomes (DESIGN section 2.4): ``Optimal`` and a gap-tolerance stop are the
solution; a time-limit stop WITH an incumbent is accepted and counted; a
window with no feasible incumbent raises :class:`UcWindowInfeasible` (an
engine defect, never a tuning invitation — GATESPEC section 5).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import highspy
import numpy as np

from market_sim.model.uc.window import UcWindowInfeasible, UcWindowModel, WindowResult

#: HiGHS ``primal_solution_status`` value meaning a feasible primal point exists.
_PRIMAL_FEASIBLE = 2


@dataclass(frozen=True)
class UcSolveOptions:
    """Solver settings of one window (every value a registry field)."""

    mip_rel_gap: float
    time_limit_s: float
    warm_start: bool = True


def solve_window(
    window: UcWindowModel,
    options: UcSolveOptions,
    warm_values: np.ndarray | None = None,
    relax: bool = False,
) -> WindowResult:
    """Solve one window and return its :class:`WindowResult`.

    Args:
        window: The built window model.
        options: Gap / time limit / warm-start flag.
        warm_values: Optional full column vector for ``setSolution``.
        relax: Solve the LP relaxation instead (ladder rung L1 (b)): every
            ``u`` column is made continuous for this call and restored after.
    """
    h = window.h
    h.setOptionValue("output_flag", False)
    h.setOptionValue("presolve", "on")
    h.setOptionValue("mip_rel_gap", float(options.mip_rel_gap))
    h.setOptionValue("time_limit", float(options.time_limit_s))
    n_u = window.V0 - window.U0
    u_idx = np.arange(window.U0, window.V0, dtype=np.int32)
    if relax and n_u:
        h.changeColsIntegrality(n_u, u_idx, [highspy.HighsVarType.kContinuous] * n_u)
    warm = False
    if options.warm_start and warm_values is not None and not relax:
        sol = highspy.HighsSolution()
        sol.col_value = [float(x) for x in np.asarray(warm_values, dtype=float)]
        sol.value_valid = True
        warm = h.setSolution(sol) == highspy.HighsStatus.kOk
    t0 = time.perf_counter()
    h.run()
    milp_s = time.perf_counter() - t0
    status = h.getModelStatus()
    status_str = h.modelStatusToString(status)
    _, primal = h.getInfoValue("primal_solution_status")
    feasible = int(primal) == _PRIMAL_FEASIBLE
    time_limit_hit = status == highspy.HighsModelStatus.kTimeLimit
    if status != highspy.HighsModelStatus.kOptimal and not (
        time_limit_hit and feasible
    ):
        raise UcWindowInfeasible(
            f"UC window solve ended {status_str} with "
            f"{'a' if feasible else 'no'} feasible incumbent "
            f"({window.n_total} columns, {window.h.getNumRow()} rows, "
            f"{window.n_int} integer clusters)"
        )
    info = h.getInfo()
    sol = h.getSolution()
    col_value = np.asarray(sol.col_value, dtype=float)
    if relax and n_u:
        h.changeColsIntegrality(n_u, u_idx, [highspy.HighsVarType.kInteger] * n_u)
    gap = float(info.mip_gap) if n_u and not relax else 0.0
    nodes = int(info.mip_node_count) if n_u and not relax else 0
    return window.extract(
        col_value,
        objective=float(info.objective_function_value),
        status=status_str,
        gap=gap if np.isfinite(gap) else float("inf"),
        nodes=nodes,
        time_limit_hit=bool(time_limit_hit),
        milp_s=milp_s,
        warm_accepted=warm,
    )
