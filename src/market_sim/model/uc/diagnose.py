"""Zero-LP diagnosis of a built UC window (what an infeasible window reports).

:func:`diagnose_window` reads the model HiGHS holds for a
:class:`~market_sim.model.uc.window.UcWindowModel` and checks every row by
interval arithmetic over its column bounds — a row whose minimum activity
already exceeds its upper bound (or whose maximum activity cannot reach its
lower bound) is an a-priori contradiction, named by row family and
``(cluster, hour)``. It also reports the two consistency facts the rolling
state carries: carried starts within one min-up above the plant's unit count,
and floor needs above the units the carried min-down leaves. The report rides
on :class:`~market_sim.model.uc.window.UcWindowInfeasible` and, when the bench
harness asks for a dump, lands beside the written model
(``scripts/lib/uc_bench.py``). Nothing here is read by a solve.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import highspy
import numpy as np
import scipy.sparse as sp

if TYPE_CHECKING:  # pragma: no cover
    from market_sim.model.uc.window import UcWindowModel

#: Row families appended by ``UcWindowModel._add_uc_rows``, in order; the
#: ``mlf`` family exists only when some integer cluster carries ``mlf > 0``.
_UC_FAMILIES = ("ceiling", "mlf_floor", "logic", "min_up", "min_down")

#: Bound magnitude HiGHS reports for an infinite bound.
_HIGHS_INF = 1e29

#: Activity slack below which a bound contradiction is a rounding artefact.
_TOL = 1e-6


def highs_lp_arrays(
    h: highspy.Highs,
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """``(A, col_lower, col_upper, row_lower, row_upper)`` of the model ``h`` holds."""
    lp = h.getLp()
    a = lp.a_matrix_
    start = np.asarray(a.start_, dtype=np.int64)
    index = np.asarray(a.index_, dtype=np.int64)
    value = np.asarray(a.value_, dtype=float)
    n_row, n_col = int(lp.num_row_), int(lp.num_col_)
    if a.format_ == highspy.MatrixFormat.kRowwise:
        A = sp.csr_matrix((value, index, start), shape=(n_row, n_col))
    else:
        A = sp.csc_matrix((value, index, start), shape=(n_row, n_col)).tocsr()

    def _f(x):
        x = np.asarray(x, dtype=float)
        x = np.where(x <= -_HIGHS_INF, -np.inf, x)
        return np.where(x >= _HIGHS_INF, np.inf, x)

    return A, _f(lp.col_lower_), _f(lp.col_upper_), _f(lp.row_lower_), _f(lp.row_upper_)


def row_activity_bounds(
    A: sp.csr_matrix, col_lower: np.ndarray, col_upper: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Minimum and maximum activity of every row over the column bounds."""
    Ap = A.maximum(0)
    An = A.minimum(0)
    lo_f = np.where(np.isfinite(col_lower), col_lower, 0.0)
    hi_f = np.where(np.isfinite(col_upper), col_upper, 0.0)
    mn = Ap @ lo_f + An @ hi_f
    mx = Ap @ hi_f + An @ lo_f
    lo_inf = (~np.isfinite(col_lower)).astype(float)
    hi_inf = (~np.isfinite(col_upper)).astype(float)
    mn = np.where((Ap @ lo_inf + An @ hi_inf) > 0, -np.inf, mn)
    mx = np.where((Ap @ hi_inf + An @ lo_inf) > 0, np.inf, mx)
    return mn, mx


def cluster_rows(
    window: "UcWindowModel", mask: np.ndarray, max_examples: int, **cells
) -> list[dict]:
    """One entry per integer cluster with a flagged ``(k, hour)`` cell in ``mask``.

    Names the plant (``plant_code``, ``family``, ``n``, ``dt_h``, ``ut_h``),
    whether any member is a budget row pinned to P0 inside the window
    (``pinned_members``), the flagged hours (up to ``max_examples``) and, per
    keyword in ``cells`` (an ``(n_int, T_w)`` array), its values there — so an
    infeasible window's exception says WHICH plant and hours collide.
    """
    p, k_all = window.params, window.int_idx
    pinned = set(np.asarray(getattr(window, "pinned_gens", []), dtype=int).tolist())
    out = []
    for k in np.flatnonzero(mask.any(axis=1))[:max_examples]:
        c = int(k_all[k])
        hours = np.flatnonzero(mask[k])[:max_examples]
        members = p.member_gen[p.member_cluster == c]
        row = {
            "k": int(k),
            "plant_code": int(p.plant_code[c]),
            "family": str(p.family[c]),
            "n": int(p.n_units[c]),
            "dt_h": int(p.dt_h[c]),
            "ut_h": int(p.ut_h[c]),
            "pinned_members": int(sum(int(g) in pinned for g in members)),
            "members": int(members.size),
            "hours": [int(h) for h in hours],
        }
        for name, arr in cells.items():
            row[name] = [float(arr[k, h]) for h in hours]
        out.append(row)
    return out


def diagnose_window(window: "UcWindowModel", max_examples: int = 12) -> dict:
    """The zero-LP report of ``window`` (see the module docstring).

    Returns a JSON-serialisable dict: ``rows`` / ``columns``; ``bad_column_
    bounds`` (``lower > upper``); ``contradictory_rows`` by family with up to
    ``max_examples`` ``(cluster, hour)`` pairs each (``cluster`` is the
    integer-local index ``k``; production rows are listed by row index);
    ``history_starts_above_n`` and ``floor_above_min_down`` cell counts, and
    the plants behind them (:func:`cluster_rows`):
    ``clusters_floor_above_min_down`` (floor need above ``n`` less the carried
    min-down), ``clusters_ceiling_contradiction`` (row (a) contradicted) and
    ``clusters_history_starts_above_n``.
    """
    A, cl, cu, rl, ru = highs_lp_arrays(window.h)
    mn, mx = row_activity_bounds(A, cl, cu)
    bad_cols = np.flatnonzero(cl > cu + _TOL)
    bad_rows = np.union1d(
        np.flatnonzero(mn > ru + _TOL), np.flatnonzero(mx < rl - _TOL)
    )
    n_int, T_w = window.n_int, window.T_w
    size = n_int * T_w
    n_rows = int(A.shape[0])
    n_pocket = int(getattr(window, "_n_pocket_rows", 0))
    n_selfc = int(getattr(window, "_n_selfcommit_rows", 0))
    n_prod = n_rows - window._n_uc_rows - n_pocket - n_selfc - window._n_ramp_rows
    has_mlf = bool(n_int) and bool((window.params.mlf[window.int_idx] > 0.0).any())
    families = [f for f in _UC_FAMILIES if f != "mlf_floor" or has_mlf]
    n_family_rows = len(families) * size
    by_family: dict[str, list] = {}
    for r in bad_rows.tolist():
        if r < n_prod:
            by_family.setdefault("production", []).append(int(r))
            continue
        off = r - n_prod
        if off < n_family_rows:
            fam = families[off // size]
            local = off % size
            by_family.setdefault(fam, []).append(
                (int(local % n_int), int(local // n_int))
            )
        elif off < window._n_uc_rows:
            by_family.setdefault("min_down_guard", []).append(int(off - n_family_rows))
        elif off < window._n_uc_rows + n_pocket:
            by_family.setdefault("vlr_pocket", []).append(int(off - window._n_uc_rows))
        elif off < window._n_uc_rows + n_pocket + n_selfc:
            by_family.setdefault("selfcommit", []).append(
                int(off - window._n_uc_rows - n_pocket)
            )
        else:
            by_family.setdefault("ramp_boundary", []).append(int(r))
    report = {
        "rows": n_rows,
        "columns": int(A.shape[1]),
        "integer_clusters": n_int,
        "bad_column_bounds": int(bad_cols.size),
        "contradictory_rows": {
            fam: {"count": len(v), "examples": v[:max_examples]}
            for fam, v in by_family.items()
        },
        "contradictory_rows_total": int(bad_rows.size),
    }
    if n_int:
        n = window.params.n_units[window.int_idx].astype(float)[:, None]
        above = window.hist_v > n + _TOL
        collide = window.u_lower > (n - window.hist_w) + _TOL
        report["history_starts_above_n"] = int(above.sum())
        report["floor_above_min_down"] = int(collide.sum())
        report["clusters_floor_above_min_down"] = cluster_rows(
            window,
            collide,
            max_examples,
            u_lower=window.u_lower,
            n_minus_hist_w=n - window.hist_w,
        )
        ceiling = by_family.get("ceiling", [])
        ceil_mask = np.zeros_like(collide)
        for kk, tt in ceiling:
            ceil_mask[kk, tt] = True
        report["clusters_ceiling_contradiction"] = cluster_rows(
            window, ceil_mask, max_examples, u_upper=window.u_upper
        )
        report["clusters_history_starts_above_n"] = [
            {
                "k": int(k),
                "plant_code": int(window.params.plant_code[window.int_idx[k]]),
                "n": int(n[k, 0]),
                "ut_h": int(window.params.ut_h[window.int_idx[k]]),
                "max_hist_starts": float(window.hist_v[k].max()),
            }
            for k in np.flatnonzero(above.any(axis=1))[:max_examples]
        ]
    return report
