"""The slim window: an exact reduction of the window MILP before HiGHS sees it.

Lane UC-SLIM (2026-10-10; owner ruling "Try 'slim window' first"). HiGHS's MIP
presolve is 70 % of the UC stage on SPP 2020 (803 s of 1,144 s; 2.2 s per
window) and removes 63 % of each window's columns and 37 % of its rows
(FINDING-ucmilp-speed-window-solve-profile-2026-10-09.md section 4.2). The
zero-LP census of this lane (FINDING-ucmilp-slim-window-2026-10-10.md section
1) splits that 63 % in two: the bound-fixed columns — pinned budget units,
zero-availability units, zero-CF renewable hours, commitment columns a floor
or a carried history pins, and what forcing and singleton rows then fix —
are 15 % of the columns and cost HiGHS almost nothing; the bulk, 48 %, are
PARALLEL columns (HiGHS rule "Parallel rows and columns"): generator ``P``
columns in the same zone-balance row with the same offer, which HiGHS merges
only after a full first presolve pass over all of them. This module does
both before HiGHS, EXACTLY and vectorized over the whole model (rule 2):

1. **fixed column** — ``lower == upper`` (exact equality): the column leaves
   the model, ``a_ij * x_j`` moves into every row's bounds and ``c_j * x_j``
   into the objective offset;
2. **forcing row** — a row whose maximum activity over the column bounds
   equals its lower bound (or minimum equals upper): every feasible point has
   every column of the row at the bound that attains it, so they are fixed;
3. **singleton row** — one unfixed column: a bound on that column, tightened
   onto it and the row dropped (a tightening that would cross the column's
   bounds is not applied — the row stays, HiGHS decides);
4. **redundant row** — activity range inside the row bounds: never binds,
   dropped; a row emptied by the fixings is dropped when its shifted bounds
   admit zero;
5. **parallel columns** — continuous columns with the SAME column of ``A``
   (same rows, same coefficients, exact equality) and the SAME cost are one
   slim column whose bounds are the members' sums. Any value of the slim
   column within those bounds splits into feasible member values and every
   split costs the same, so the slim model's feasible set is the exact
   projection of the full one and its optimum the full optimum. The split
   :meth:`SlimReduction.expand` returns is deterministic (members filled in
   index order above their lower bounds); the full window's optimum is as
   indifferent to it as the stage is (a member's dispatch feeds the next
   window's warm start and its ramp-group sum, both split-invariant).

Every reduction is a statement about the feasible set that holds for the LP
relaxation and the MILP alike, never an optimality argument (dominated
columns, probing, doubleton substitution are left to HiGHS). A contradiction
met on the way (a row no bound setting satisfies, two forcing rows that
disagree, an emptied row that admits no zero) is NOT diagnosed here:
:func:`reduce_lp` returns ``None`` and the window solves on the full model,
so the existing infeasibility report
(:class:`~market_sim.model.uc.window.UcWindowInfeasible`,
:func:`~market_sim.model.uc.diagnose.diagnose_window`) is what fires.

The slim model goes to a fresh HiGHS handle (:func:`slim_handle`); the full
handle stays untouched for the diagnosis, relaxation and dump paths.
:meth:`SlimReduction.restrict` carries a full column vector (the
``setSolution`` warm start) into the slim space and
:meth:`SlimReduction.expand` brings a slim solution back with the fixed
values reinserted and the merged columns split, so the extracted ``P`` /
``u`` / ``v`` / ``w`` / SOC and the full ``col_value`` the next window
warm-starts from are the full window's.
"""

from __future__ import annotations

from dataclasses import dataclass

import highspy
import numpy as np
import scipy.sparse as sp

from market_sim.model.uc.diagnose import highs_lp_arrays

#: Passes of the fixpoint loop (each pass is one vectorized sweep over the
#: whole model; a window reaches its fixpoint in three or four — the loop
#: also stops on the first pass that changes nothing).
MAX_PASSES = 12

#: Slack below which an emptied row's shifted bounds are read as admitting
#: zero. A row the fixed columns satisfy exactly in real arithmetic can carry
#: a float residual of this order from the shift; it is two decades below
#: HiGHS's primal feasibility tolerance (1e-7), so the row the solver sees is
#: the row it would accept.
EMPTY_ROW_TOL = 1e-9

#: Why the last :func:`reduce_lp` call stood down (``None`` when it did not):
#: one of ``"bounds_crossed"``, ``"row_unsatisfiable"``, ``"forcing_infinite"``,
#: ``"forcing_disagree"``, ``"empty_row_violated"`` plus the worst violation —
#: surfaced per window in ``uc_solve_log`` (``windows[].slim.stand_down``).
LAST_STAND_DOWN: dict | None = None


def _stand_down(reason: str, **detail) -> None:
    """Record why the reduction returns ``None`` (see :data:`LAST_STAND_DOWN`)."""
    global LAST_STAND_DOWN
    LAST_STAND_DOWN = {"reason": reason, **{k: float(v) for k, v in detail.items()}}
    return None


#: Relative slack below which a row's activity range is NOT read as a
#: contradiction. ``mx`` / ``mn`` are float sums of bound products; a row the
#: bounds satisfy exactly in real arithmetic can miss its own bound by a few
#: ulp (SPP 2020: 4e-15 on one row of every April and October window, which
#: sent 43 windows of the first L3 shard back to the full model). Within this
#: slack nothing is forced or dropped either (those tests stay exact
#: equalities), the row simply stays for HiGHS; beyond it the full model is
#: infeasible and the reduction stands down so the existing report fires.
ROW_TOL = 1e-9

#: Columns with more nonzeros than this are never merged (the parallel-column
#: key is a fixed-width padded array; a window's continuous columns carry a
#: handful of entries — balance, reserve, ramp, coupling rows).
MERGE_MAX_NNZ = 64


@dataclass(frozen=True)
class SlimReduction:
    """The exact reduction of one window model (see the module docstring).

    Attributes:
        n_col / n_row: Dimensions of the full model.
        col_map: ``(n_col,)`` slim column of each full column (``-1`` for a
            fixed one); several full columns map to one slim column when they
            are parallel.
        n_slim_cols: Columns of the slim model.
        fixed_cols / fixed_values: ``(n_fixed,)`` the columns removed and
            their values.
        kept_rows: ``(n_slim_rows,)`` full-model row indices kept, ascending.
        col_cost / col_lower / col_upper: The slim columns' cost and bounds
            (singleton-tightened member bounds, summed over parallel members).
        row_lower / row_upper: The kept rows' bounds, the fixed columns'
            contributions shifted out.
        member_lower / member_upper: The kept full columns' (tightened)
            bounds, in ``kept_cols`` order — what :meth:`expand` splits
            a merged value against.
        offset: ``sum(cost[fixed] * fixed_values)`` — the objective constant.
        passes: Fixpoint passes run.
        counts: How many columns and rows each reduction took (the census the
            FINDING reports and ``uc_solve_log`` carries per window).
    """

    n_col: int
    n_row: int
    col_map: np.ndarray
    n_slim_cols: int
    fixed_cols: np.ndarray
    fixed_values: np.ndarray
    kept_rows: np.ndarray
    col_cost: np.ndarray
    col_lower: np.ndarray
    col_upper: np.ndarray
    row_lower: np.ndarray
    row_upper: np.ndarray
    member_lower: np.ndarray
    member_upper: np.ndarray
    offset: float
    passes: int
    counts: dict

    @property
    def n_slim_rows(self) -> int:
        """Rows of the slim model."""
        return int(self.kept_rows.size)

    @property
    def kept_cols(self) -> np.ndarray:
        """Full-model columns that survive (fixed ones excluded), ascending."""
        return np.flatnonzero(self.col_map >= 0)

    def restrict(self, x_full: np.ndarray) -> np.ndarray:
        """A full column vector in the slim space (fixed entries dropped, parallel members summed)."""
        x = np.asarray(x_full, dtype=float)
        kept = self.kept_cols
        return np.bincount(
            self.col_map[kept], weights=x[kept], minlength=self.n_slim_cols
        )

    def expand(self, x_slim: np.ndarray) -> np.ndarray:
        """A slim column vector back in the full space.

        Fixed columns take their values; a slim column with one member hands
        it its value; a merged column is split among its members in index
        order — each member at its lower bound, the remainder filled member
        by member up to its upper bound (a feasible split exists whenever
        the slim value lies within the slim bounds; a solver-tolerance excess
        lands on the last member).
        """
        xs = np.asarray(x_slim, dtype=float)
        out = np.empty(self.n_col, dtype=float)
        out[self.fixed_cols] = self.fixed_values
        kept = self.kept_cols
        g = self.col_map[kept]
        size = np.bincount(g, minlength=self.n_slim_cols)
        single = size[g] == 1
        out[kept[single]] = xs[g[single]]
        multi = ~single
        if multi.any():
            m_cols = kept[multi]
            m_g = g[multi]
            lo = np.where(
                np.isfinite(self.member_lower[multi]), self.member_lower[multi], 0.0
            )
            cap = self.member_upper[multi] - lo
            order = np.lexsort((m_cols, m_g))
            m_cols, m_g, lo, cap = m_cols[order], m_g[order], lo[order], cap[order]
            starts = np.flatnonzero(np.concatenate([[True], m_g[1:] != m_g[:-1]]))
            sizes = np.diff(np.append(starts, m_g.size))
            resid = xs[m_g[starts]] - np.add.reduceat(lo, starts)
            resid_m = np.repeat(resid, sizes)
            cum_before = np.cumsum(cap) - cap
            before = cum_before - np.repeat(cum_before[starts], sizes)
            take = np.clip(resid_m - before, 0.0, cap)
            last = np.append(starts[1:], m_g.size) - 1
            take[last] += resid - np.add.reduceat(take, starts)
            out[m_cols] = lo + take
        return out

    def slim_index(self, full_cols: np.ndarray) -> np.ndarray:
        """Slim column of each full column in ``full_cols`` (``-1`` for a fixed one)."""
        return self.col_map[np.asarray(full_cols, dtype=np.int64)]


def _finite(x: np.ndarray) -> np.ndarray:
    return np.isfinite(x)


def _assign_fixed(
    col_lower: np.ndarray,
    col_upper: np.ndarray,
    cols: np.ndarray,
    values: np.ndarray,
) -> bool:
    """Fix ``cols`` at ``values`` in place; ``False`` on a disagreement (contradiction).

    A column named twice must receive the same value (two forcing rows that
    disagree, or a forcing row against an already-fixed column) — otherwise
    the model is infeasible and the reduction stands down.
    """
    if cols.size == 0:
        return True
    order = np.argsort(cols, kind="stable")
    c, v = cols[order], values[order]
    first = np.concatenate([[True], c[1:] != c[:-1]])
    head = np.maximum.accumulate(np.where(first, np.arange(c.size), 0))
    tol = ROW_TOL * np.maximum(1.0, np.abs(v[head]))
    if not np.all(np.abs(v - v[head]) <= tol):
        return False
    cu, vu = c[first], v[first]
    tol = ROW_TOL * np.maximum(1.0, np.abs(vu))
    if np.any(vu < col_lower[cu] - tol) or np.any(vu > col_upper[cu] + tol):
        return False
    # a forced value is always one of the column's own bounds; keep it there
    vu = np.clip(vu, col_lower[cu], col_upper[cu])
    col_lower[cu] = vu
    col_upper[cu] = vu
    return True


def _row_violation(
    alive: np.ndarray, mn: np.ndarray, mx: np.ndarray, rl: np.ndarray, ru: np.ndarray
) -> np.ndarray:
    """Per-row contradiction beyond :data:`ROW_TOL` (``-inf`` for a dead or satisfiable row).

    A finite ``mx`` below ``rl`` (or ``mn`` above ``ru``) by more than
    ``ROW_TOL * max(1, |bound|, |activity|)`` is a row no bound setting
    satisfies; a miss inside that slack is float noise and is not a
    contradiction (nor a forcing or redundant row — those are exact).
    """
    with np.errstate(invalid="ignore"):
        scale_lo = np.maximum(1.0, np.maximum(np.abs(rl), np.abs(mx)))
        scale_hi = np.maximum(1.0, np.maximum(np.abs(ru), np.abs(mn)))
        v_lo = np.where(
            np.isfinite(mx) & np.isfinite(rl), (rl - mx) - ROW_TOL * scale_lo, -np.inf
        )
        v_hi = np.where(
            np.isfinite(mn) & np.isfinite(ru), (mn - ru) - ROW_TOL * scale_hi, -np.inf
        )
    return np.where(alive, np.maximum(v_lo, v_hi), -np.inf)


def _activity_from(
    Ap: sp.csr_matrix, An: sp.csr_matrix, cl: np.ndarray, cu: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Row activity bounds with the positive / negative parts of ``A`` precomputed."""
    lo_f = np.where(_finite(cl), cl, 0.0)
    hi_f = np.where(_finite(cu), cu, 0.0)
    mn = Ap @ lo_f + An @ hi_f
    mx = Ap @ hi_f + An @ lo_f
    lo_inf = (~_finite(cl)).astype(float)
    hi_inf = (~_finite(cu)).astype(float)
    mn = np.where((Ap @ lo_inf + An @ hi_inf) > 0, -np.inf, mn)
    mx = np.where((Ap @ hi_inf + An @ lo_inf) > 0, np.inf, mx)
    return mn, mx


def parallel_groups(
    A: sp.spmatrix, cost: np.ndarray, mergeable: np.ndarray
) -> np.ndarray:
    """Group id per column: columns with the same ``A`` column and cost share one.

    Exact (a lexicographic sort of the padded ``(nnz, cost, idx, val, ...)``
    key and an adjacent-row comparison — no hashing); a column not in
    ``mergeable``, or with more than :data:`MERGE_MAX_NNZ` entries, is a
    group of its own. Group ids run ``0 .. n_groups - 1`` in order of each
    group's first column.
    """
    A = sp.csc_matrix(A)
    A.sort_indices()
    n_col = A.shape[1]
    nnz = np.diff(A.indptr)
    cand = np.asarray(mergeable, dtype=bool) & (nnz <= MERGE_MAX_NNZ)
    leader = np.arange(n_col)  # each column's group leader (its first member)
    cols = np.flatnonzero(cand)
    if cols.size:
        width = int(nnz[cols].max())
        key = np.zeros((cols.size, 2 + 2 * width))
        key[:, 0] = nnz[cols]
        key[:, 1] = np.asarray(cost, dtype=float)[cols]
        if width:
            counts = nnz[cols]
            j_rep = np.repeat(np.arange(cols.size), counts)
            e = np.arange(int(counts.sum())) - np.repeat(
                np.cumsum(counts) - counts, counts
            )
            pos = np.repeat(A.indptr[cols], counts) + e
            key[j_rep, 2 + 2 * e] = A.indices[pos]
            key[j_rep, 3 + 2 * e] = A.data[pos]
        order = np.lexsort(key.T[::-1])
        ks = key[order]
        new = np.concatenate([[True], np.any(ks[1:] != ks[:-1], axis=1)])
        gid = np.cumsum(new) - 1
        group_leader = np.minimum.reduceat(cols[order], np.flatnonzero(new))
        leader[cols[order]] = group_leader[gid]
    _, inv = np.unique(leader, return_inverse=True)
    return np.asarray(inv).ravel().astype(np.int64)


def reduce_lp(
    A: sp.spmatrix,
    cost: np.ndarray,
    col_lower: np.ndarray,
    col_upper: np.ndarray,
    row_lower: np.ndarray,
    row_upper: np.ndarray,
    is_integer: np.ndarray | None = None,
    merge_parallel: bool = True,
    max_passes: int = MAX_PASSES,
) -> SlimReduction | None:
    """The exact reduction of ``(A, cost, bounds)`` (see the module docstring).

    Bounds use ``±inf`` for a free side; ``is_integer`` marks the integer
    columns (never merged). Returns ``None`` when the propagation meets a
    contradiction — the caller then solves the full model so HiGHS (and the
    existing diagnosis) report it.
    """
    A = sp.csr_matrix(A)
    A.eliminate_zeros()  # an explicit zero is no entry (the coupling rows write -pbar*a*u with a = 0)
    n_row, n_col = A.shape
    cost = np.asarray(cost, dtype=float)
    cl = np.array(col_lower, dtype=float, copy=True)
    cu = np.array(col_upper, dtype=float, copy=True)
    rl = np.asarray(row_lower, dtype=float)
    ru = np.asarray(row_upper, dtype=float)
    is_int = (
        np.zeros(n_col, dtype=bool)
        if is_integer is None
        else np.asarray(is_integer, dtype=bool)
    )
    global LAST_STAND_DOWN
    LAST_STAND_DOWN = None
    if np.any(cl > cu) or np.any(rl > ru):
        return _stand_down(
            "bounds_crossed",
            worst=max(
                float(np.max(cl - cu, initial=0.0)), float(np.max(rl - ru, initial=0.0))
            ),
        )
    Ap = A.maximum(0).tocsr()
    An = A.minimum(0).tocsr()
    pattern = A.copy()
    pattern.data = np.ones_like(pattern.data)
    alive = np.ones(n_row, dtype=bool)
    fixed = (cl == cu) & _finite(cl)
    counts = {
        "cols_fixed_by_bounds": int(fixed.sum()),
        "cols_fixed_by_forcing": 0,
        "cols_fixed_by_singleton": 0,
        "cols_merged_parallel": 0,
        "rows_dropped_redundant": 0,
        "rows_dropped_singleton": 0,
        "rows_dropped_empty": 0,
    }
    passes = 0
    changed = True
    while changed and passes < max_passes:
        passes += 1
        changed = False
        mn, mx = _activity_from(Ap, An, cl, cu)
        viol = _row_violation(alive, mn, mx, rl, ru)
        if np.any(viol > 0.0):
            return _stand_down("row_unsatisfiable", worst=viol.max(), pass_no=passes)
        # (4) redundant rows
        red = alive & (mn >= rl) & (mx <= ru)
        if red.any():
            alive &= ~red
            counts["rows_dropped_redundant"] += int(red.sum())
            changed = True
        # (2) forcing rows
        f_max = alive & _finite(rl) & (mx == rl)
        f_min = alive & _finite(ru) & (mn == ru)
        if f_max.any() or f_min.any():
            fcols, fvals = [], []
            for rows, at_max in ((f_max, True), (f_min, False)):
                if not rows.any():
                    continue
                B = A[np.flatnonzero(rows)].tocoo()
                keep = ~fixed[B.col]
                c = B.col[keep]
                pos = B.data[keep] > 0.0
                # at the row's max: a > 0 -> upper, a < 0 -> lower (reverse at its min)
                fcols.append(c)
                fvals.append(np.where(pos == at_max, cu[c], cl[c]))
            fcols = np.concatenate(fcols)
            fvals = np.concatenate(fvals)
            if fcols.size:
                if not np.all(_finite(fvals)):
                    return _stand_down("forcing_infinite", pass_no=passes)
                if not _assign_fixed(cl, cu, fcols, fvals):
                    return _stand_down("forcing_disagree", pass_no=passes)
                new_fixed = (cl == cu) & _finite(cl) & ~fixed
                counts["cols_fixed_by_forcing"] += int(new_fixed.sum())
                fixed |= new_fixed
                changed = True
        # (3) singleton rows: one unfixed column
        unfixed = (~fixed).astype(float)
        n_unfixed = pattern @ unfixed
        single = alive & (n_unfixed == 1.0)
        if single.any():
            rows = np.flatnonzero(single)
            B = A[rows].tocsr()
            fixed_part = B @ np.where(fixed, cl, 0.0)
            B = B.multiply(unfixed[None, :]).tocsr()
            B.eliminate_zeros()
            assert np.all(np.diff(B.indptr) == 1)
            c = B.indices.astype(np.int64)
            a = B.data
            lo_r = rl[rows] - fixed_part
            hi_r = ru[rows] - fixed_part
            with np.errstate(invalid="ignore", divide="ignore"):
                lo_x = np.where(a > 0.0, lo_r / a, hi_r / a)
                hi_x = np.where(a > 0.0, hi_r / a, lo_r / a)
            lo_x = np.where(np.isnan(lo_x), -np.inf, lo_x)
            hi_x = np.where(np.isnan(hi_x), np.inf, hi_x)
            new_lo = np.maximum(cl[c], lo_x)
            new_hi = np.minimum(cu[c], hi_x)
            ok = new_lo <= new_hi
            lo_c = np.array(cl, copy=True)
            hi_c = np.array(cu, copy=True)
            np.maximum.at(lo_c, c[ok], new_lo[ok])
            np.minimum.at(hi_c, c[ok], new_hi[ok])
            crossed = np.flatnonzero(lo_c > hi_c)
            if crossed.size:
                # singleton rows that disagree on a column: leave them to HiGHS
                ok &= ~np.isin(c, crossed)
                lo_c = np.array(cl, copy=True)
                hi_c = np.array(cu, copy=True)
                np.maximum.at(lo_c, c[ok], new_lo[ok])
                np.minimum.at(hi_c, c[ok], new_hi[ok])
            if ok.any():
                cl[:] = lo_c
                cu[:] = hi_c
                alive[rows[ok]] = False
                counts["rows_dropped_singleton"] += int(ok.sum())
                new_fixed = (cl == cu) & _finite(cl) & ~fixed
                counts["cols_fixed_by_singleton"] += int(new_fixed.sum())
                fixed |= new_fixed
                changed = True
    # final sweep: rows the last pass's fixings made redundant
    mn, mx = _activity_from(Ap, An, cl, cu)
    viol = _row_violation(alive, mn, mx, rl, ru)
    if np.any(viol > 0.0):
        return _stand_down("row_unsatisfiable", worst=viol.max(), pass_no=passes + 1)
    red = alive & (mn >= rl) & (mx <= ru)
    if red.any():
        alive &= ~red
        counts["rows_dropped_redundant"] += int(red.sum())
    kept_rows = np.flatnonzero(alive)
    fixed_cols = np.flatnonzero(fixed)
    kept_cols = np.flatnonzero(~fixed)
    fixed_values = cl[fixed_cols]
    shift = (
        A[kept_rows][:, fixed_cols] @ fixed_values
        if fixed_cols.size
        else np.zeros(kept_rows.size)
    )
    rl_k = rl[kept_rows] - shift
    ru_k = ru[kept_rows] - shift
    A_k = A[kept_rows][:, kept_cols].tocsr()
    empty = np.diff(A_k.indptr) == 0
    if empty.any():
        scale = np.maximum(1.0, np.abs(shift[empty]))
        if np.any(rl_k[empty] > EMPTY_ROW_TOL * scale) or np.any(
            ru_k[empty] < -EMPTY_ROW_TOL * scale
        ):
            return _stand_down(
                "empty_row_violated",
                worst=max(float(np.max(rl_k[empty])), float(-np.min(ru_k[empty]))),
            )
        counts["rows_dropped_empty"] = int(empty.sum())
        kept_rows = kept_rows[~empty]
        rl_k = rl_k[~empty]
        ru_k = ru_k[~empty]
        A_k = A_k[~empty]
    # (5) parallel continuous columns -> one slim column each
    col_map = np.full(n_col, -1, dtype=np.int64)
    if merge_parallel and kept_cols.size:
        grp = parallel_groups(A_k, cost[kept_cols], ~is_int[kept_cols])
    else:
        grp = np.arange(kept_cols.size, dtype=np.int64)
    col_map[kept_cols] = grp
    n_slim = int(grp.max()) + 1 if grp.size else 0
    counts["cols_merged_parallel"] = int(kept_cols.size - n_slim)
    lo_m = cl[kept_cols]
    hi_m = cu[kept_cols]
    first = np.unique(grp, return_index=True)[1]
    lo_fin, hi_fin = _finite(lo_m), _finite(hi_m)
    slim_lo = np.bincount(grp, weights=np.where(lo_fin, lo_m, 0.0), minlength=n_slim)
    slim_hi = np.bincount(grp, weights=np.where(hi_fin, hi_m, 0.0), minlength=n_slim)
    lo_inf = np.bincount(grp, weights=(~lo_fin).astype(float), minlength=n_slim) > 0
    hi_inf = np.bincount(grp, weights=(~hi_fin).astype(float), minlength=n_slim) > 0
    return SlimReduction(
        n_col=int(n_col),
        n_row=int(n_row),
        col_map=col_map,
        n_slim_cols=n_slim,
        fixed_cols=fixed_cols.astype(np.int64),
        fixed_values=fixed_values,
        kept_rows=kept_rows.astype(np.int64),
        col_cost=cost[kept_cols][first],
        col_lower=np.where(lo_inf, -np.inf, slim_lo),
        col_upper=np.where(hi_inf, np.inf, slim_hi),
        row_lower=rl_k,
        row_upper=ru_k,
        member_lower=lo_m,
        member_upper=hi_m,
        offset=float(cost[fixed_cols] @ fixed_values) if fixed_cols.size else 0.0,
        passes=passes,
        counts=counts,
    )


def slim_matrix(A_full: sp.spmatrix, red: SlimReduction) -> sp.csc_matrix:
    """The slim model's matrix: kept rows, one column per slim column.

    A merged group's members share their column of ``A``, so the group's
    first member's column IS the slim column.
    """
    kept = red.kept_cols
    first = np.unique(red.col_map[kept], return_index=True)[1]
    return sp.csc_matrix(A_full)[red.kept_rows, :][:, kept[first]].tocsc()


def reduce_handle(
    h: highspy.Highs,
    integer_cols: np.ndarray | None = None,
    merge_parallel: bool = True,
) -> SlimReduction | None:
    """:func:`reduce_lp` on the model ``h`` holds (bounds read as ``±inf``)."""
    return reduce_window(h, integer_cols, merge_parallel)[0]


def reduce_window(
    h: highspy.Highs,
    integer_cols: np.ndarray | None = None,
    merge_parallel: bool = True,
) -> tuple[SlimReduction | None, highspy.Highs | None]:
    """The reduction of the model ``h`` holds AND the slim handle, reading the model once.

    ``(None, None)`` when the reduction stands down (a contradiction).
    """
    A, cl, cu, rl, ru = highs_lp_arrays(h)
    cost = np.asarray(h.getLp().col_cost_, dtype=float)
    is_int = np.zeros(A.shape[1], dtype=bool)
    ints = (
        np.asarray(integer_cols, dtype=np.int64)
        if integer_cols is not None
        else np.zeros(0, dtype=np.int64)
    )
    is_int[ints] = True
    red = reduce_lp(A, cost, cl, cu, rl, ru, is_int, merge_parallel=merge_parallel)
    if red is None:
        return None, None
    return red, slim_handle(h, red, ints, A=A)


def slim_handle(
    h_full: highspy.Highs,
    red: SlimReduction,
    integer_cols: np.ndarray,
    A: sp.spmatrix | None = None,
) -> highspy.Highs:
    """A fresh HiGHS handle holding the slim model (options copied from ``h_full``).

    ``integer_cols`` are the FULL-model columns that are integer; the kept ones
    keep their integrality (an integer column is never merged). The objective
    offset carries the fixed columns' cost, so the handle reports the full
    window's objective (HiGHS includes the offset in
    ``objective_function_value`` and in the MIP bounds its gap is measured
    on — ``tests/unit/model/uc/test_slim.py``). ``A`` is the full matrix
    when the caller already read it (:func:`reduce_window` does).
    """
    if A is None:
        A, _, _, _, _ = highs_lp_arrays(h_full)
    lp_full = h_full.getLp()
    A_k = slim_matrix(A, red)
    inf = highspy.kHighsInf
    lp = highspy.HighsLp()
    lp.num_col_ = int(red.n_slim_cols)
    lp.num_row_ = int(red.n_slim_rows)
    lp.col_cost_ = np.asarray(red.col_cost, dtype=float)
    lp.col_lower_ = np.where(np.isinf(red.col_lower), -inf, red.col_lower)
    lp.col_upper_ = np.where(np.isinf(red.col_upper), inf, red.col_upper)
    lp.row_lower_ = np.where(np.isinf(red.row_lower), -inf, red.row_lower)
    lp.row_upper_ = np.where(np.isinf(red.row_upper), inf, red.row_upper)
    lp.offset_ = float(red.offset) + float(lp_full.offset_)
    lp.sense_ = lp_full.sense_
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = np.asarray(A_k.indptr, dtype=np.int32)
    lp.a_matrix_.index_ = np.asarray(A_k.indices, dtype=np.int32)
    lp.a_matrix_.value_ = np.asarray(A_k.data, dtype=float)
    is_int = np.zeros(red.n_col, dtype=bool)
    is_int[np.asarray(integer_cols, dtype=np.int64)] = True
    slim_int = np.zeros(red.n_slim_cols, dtype=bool)
    kept = red.kept_cols
    slim_int[red.col_map[kept][is_int[kept]]] = True
    lp.integrality_ = [
        highspy.HighsVarType.kInteger if i else highspy.HighsVarType.kContinuous
        for i in slim_int.tolist()
    ]
    h = highspy.Highs()
    h.passOptions(h_full.getOptions())
    status = h.passModel(lp)
    if status != highspy.HighsStatus.kOk:
        raise RuntimeError(f"slim window: passModel returned {status}")
    return h


def full_row_residuals(
    h_full: highspy.Highs, x_full: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """``(bound violation per column, bound violation per row)`` of ``x_full`` on the full model.

    The reinsertion check: a slim solution expanded back into the full index
    space must satisfy every full-model column and row bound (to the solver's
    own tolerance). Returns the positive part of each violation.
    """
    A, cl, cu, rl, ru = highs_lp_arrays(h_full)
    x = np.asarray(x_full, dtype=float)
    act = A @ x
    col_v = np.maximum(np.maximum(cl - x, x - cu), 0.0)
    row_v = np.maximum(np.maximum(rl - act, act - ru), 0.0)
    return col_v, row_v
