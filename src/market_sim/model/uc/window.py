"""One rolling window of the MILP unit-commitment stage.

The window LP is the production dispatch LP (``model/lp``, untouched) built on
a ``[t0, t1)`` slice of every hourly input — :func:`slice_window_inputs` —
plus, on the HiGHS handle the :class:`~market_sim.model.lp.model.DispatchModel`
owns, the commitment columns and rows this module adds
(:class:`UcWindowModel`): per integer cluster ``c`` and window hour ``t`` an
integer ``u[c,t]`` (units online, ``0..n_c``) and continuous ``v[c,t]`` /
``w[c,t]`` (units started / stopped), the output-coupling rows, the logic
row, the Rajan–Takriti min-up / min-down rows and the boundary edits of
DESIGN section 2 (``docs/records/governance/uc-milp-2026-10/DESIGN-uc-milp-
engine-2026-10-03.md``). Every row family is assembled from index arithmetic
over all clusters and hours at once (rule 2: no Python loop over hours).

What the window cannot carry (declared, DESIGN section 2.1): the annual and
monthly budget families are dropped and their generators pinned to the P0
dispatch (``uc_boundary_mode = "p0_targets"``); the posture family is refused
upstream; a hydraulic cascade (``hydro_cascade``) is refused here because its
lagged upstream terms wrap cyclically at the window edge and the slim P0
extract carries no pond levels to pin them to (DESIGN section 8).
"""

from __future__ import annotations

import dataclasses
import time
from dataclasses import dataclass

import highspy
import numpy as np
import scipy.sparse as sp

from market_sim.data.fleet import FleetArrays
from market_sim.model.lp.costs import build_cost_vector
from market_sim.model.lp.model import DispatchModel
from market_sim.model.uc.params import (
    UC_PREFIX_OFF_MARGIN_USD_PER_MWH,
    UC_PREFIX_ON_LOAD_FRAC,
    UcClusterParams,
    units_needed_for_floor,
)

#: Dispatch kwargs the window DROPS: annual / monthly budget families whose
#: rows cannot be sliced (DESIGN section 2.1). Their generators are pinned to
#: the P0 dispatch instead (:data:`BUDGET_GEN_IDX_KEYS`).
BUDGET_KWARGS: frozenset[str] = frozenset(
    {
        "hydro_monthly_energy",
        "hydro_month_index",
        "hydro_gen_idx",
        "hydro_monthly_min",
        "hydro_period_hours",
        "oil_monthly_budget",
        "oil_gen_idx",
        "oil_month_index",
        "oil_gen_hour_coeff",
        "oil_group_index",
        "coal_monthly_budget",
        "coal_gen_idx",
        "coal_month_index",
        "coal_gen_hour_coeff",
        "coal_group_index",
        "coal_plant_budget",
        "coal_plant_gen_idx",
        "coal_plant_month_index",
        "coal_plant_gen_hour_coeff",
        "coal_plant_group_index",
        "coal_plant_floor",
        "coal_plant_floor_price",
        "import_node_gen_idx",
        "import_node_monthly_lo",
        "import_node_monthly_hi",
        "import_node_month_index",
        "hydro_envelope_gen_idx",
        "hydro_envelope_mw",
        "hydro_envelope_storage_idx",
        "storage_daily_cycle_hours",
        "storage_alloc_batt_idx",
        "storage_alloc_share",
        "storage_alloc_da_frac",
        "mass_cap_coeffs",
        "mass_cap_rhs",
        "mass_cap_labels",
        "rps_target",
        "rps_acp_price",
        "rps_eligible_fuels",
        "rps_region_zone_mask",
        "rps_region_obligation_frac",
        "rps_region_acp_price",
        "clean_region_zone_mask",
        "clean_region_obligation_frac",
        "clean_region_acp_price",
        "clean_region_fuels",
    }
)

#: Generator-index kwargs of the dropped families: every row they name is
#: pinned to its P0 dispatch inside the window.
BUDGET_GEN_IDX_KEYS: tuple[str, ...] = (
    "hydro_gen_idx",
    "oil_gen_idx",
    "coal_gen_idx",
    "coal_plant_gen_idx",
    "import_node_gen_idx",
    "hydro_envelope_gen_idx",
)

#: Kwargs the window refuses (a stack rule 19 forbids, or a coupling the
#: window cannot pin): the posture family and the hydraulic cascade.
REFUSED_KWARGS: tuple[str, ...] = (
    "posture_gen_idx",
    "reserve_posture_pools",
    "hydro_cascade",
)


class UcWindowInfeasible(RuntimeError):
    """A window returned no feasible commitment (GATESPEC section 5 kill)."""


def _slice_obj(obj, t0: int, t1: int, T: int):
    """Slice every array whose last axis is the year's ``T`` to ``[t0, t1)``.

    Recurses into tuples, lists, dicts and dataclasses; scalars, ``None`` and
    arrays with no ``T`` axis pass through unchanged.
    """
    if isinstance(obj, np.ndarray):
        if obj.ndim >= 1 and obj.shape[-1] == T:
            return np.ascontiguousarray(obj[..., t0:t1])
        return obj
    if isinstance(obj, tuple):
        return tuple(_slice_obj(x, t0, t1, T) for x in obj)
    if isinstance(obj, list):
        return [_slice_obj(x, t0, t1, T) for x in obj]
    if isinstance(obj, dict):
        return {k: _slice_obj(v, t0, t1, T) for k, v in obj.items()}
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.replace(
            obj,
            **{
                f.name: _slice_obj(getattr(obj, f.name), t0, t1, T)
                for f in dataclasses.fields(obj)
            },
        )
    return obj


@dataclass(frozen=True)
class WindowInputs:
    """The sliced inputs of one window.

    Attributes:
        fleet: The window ``FleetArrays`` (hourly fields sliced; budget rows
            pinned to P0).
        demand: ``(n_zones, T_w)``.
        kwargs: The window dispatch kwargs (budget families dropped).
        pinned_gens: ``(n_pinned,)`` fleet rows pinned to their P0 dispatch.
    """

    fleet: FleetArrays
    demand: np.ndarray
    kwargs: dict
    pinned_gens: np.ndarray


def slice_window_inputs(
    fleet: FleetArrays,
    demand: np.ndarray,
    dispatch_kwargs: dict,
    t0: int,
    t1: int,
    p0_dispatch: np.ndarray | None = None,
) -> WindowInputs:
    """Build the window inputs from the year's (DESIGN section 2.1).

    Args:
        fleet: The year's fleet.
        demand: ``(n_zones, T)``.
        dispatch_kwargs: The assembled year kwargs.
        t0, t1: The window's hour range.
        p0_dispatch: ``(n_gen, T)`` P0 dispatch; the budget-governed rows are
            pinned to it (``None`` only in tests that pass no budget family).

    Raises:
        ValueError: A refused kwarg is present (:data:`REFUSED_KWARGS`).
    """
    T = int(demand.shape[1])
    for key in REFUSED_KWARGS:
        if dispatch_kwargs.get(key) is not None:
            raise ValueError(
                f"unit_commitment_milp cannot build a window with {key!r} armed "
                "(the posture family is refused by rule 19; the hydraulic cascade's "
                "lagged cyclic terms cannot be pinned at a window edge — DESIGN "
                "section 8 R5)"
            )
    pinned = set()
    for key in BUDGET_GEN_IDX_KEYS:
        val = dispatch_kwargs.get(key)
        if val is not None:
            pinned.update(int(g) for g in np.asarray(val, dtype=int).ravel())
    pinned_gens = np.array(sorted(pinned), dtype=int)
    kwargs_w = {
        k: _slice_obj(v, t0, t1, T)
        for k, v in dispatch_kwargs.items()
        if k not in BUDGET_KWARGS and k != "T"
    }
    fleet_w = _slice_obj(fleet, t0, t1, T)
    if pinned_gens.size:
        if p0_dispatch is None:
            raise ValueError(
                "budget-governed generators need the P0 dispatch to pin to"
            )
        p_pin = np.maximum(
            np.asarray(p0_dispatch, dtype=float)[pinned_gens, t0:t1], 0.0
        )
        pmax = np.asarray(fleet_w.pmax, dtype=float)[pinned_gens]
        avail = np.array(fleet_w.availability, dtype=float, copy=True)
        with np.errstate(invalid="ignore", divide="ignore"):
            frac = np.where(pmax[:, None] > 0.0, p_pin / pmax[:, None], 0.0)
        avail[pinned_gens, :] = np.clip(frac, 0.0, 1.0)
        base = (
            np.array(fleet_w.min_gen, dtype=float, copy=True)
            if fleet_w.min_gen is not None
            else np.broadcast_to(
                np.asarray(fleet_w.pmin, dtype=float)[:, None], avail.shape
            ).copy()
        )
        base[pinned_gens, :] = np.minimum(p_pin, pmax[:, None] * avail[pinned_gens, :])
        fleet_w = dataclasses.replace(fleet_w, availability=avail, min_gen=base)
    return WindowInputs(
        fleet=fleet_w,
        demand=np.ascontiguousarray(demand[:, t0:t1]),
        kwargs=kwargs_w,
        pinned_gens=pinned_gens,
    )


@dataclass
class WindowState:
    """The state the previous window hands to the next (DESIGN section 2.2).

    Attributes:
        u_prev: ``(n_int,)`` units online in the hour before ``t0``.
        v_hist / w_hist: ``(n_int, H)`` starts / stops in the ``H`` hours
            before ``t0`` (last column = hour ``t0 - 1``).
        soc_prev: ``(n_storage,)`` SOC in the hour before ``t0`` or ``None``.
        p_prev: ``(n_gen,)`` dispatch in the hour before ``t0`` or ``None``.
        avail_prev: ``(n_gen,)`` availability in the hour before ``t0``.
    """

    u_prev: np.ndarray
    v_hist: np.ndarray
    w_hist: np.ndarray
    soc_prev: np.ndarray | None
    p_prev: np.ndarray | None
    avail_prev: np.ndarray | None


@dataclass(frozen=True)
class WindowResult:
    """What one solved window returns."""

    u: np.ndarray  # (n_int, T_w) int
    v: np.ndarray
    w: np.ndarray
    dispatch: np.ndarray  # (n_gen, T_w)
    storage_soc: np.ndarray | None  # (n_storage, T_w)
    col_value: np.ndarray  # the full MILP column vector (warm start source)
    objective: float
    status: str
    gap: float
    nodes: int
    time_limit_hit: bool
    milp_s: float
    build_s: float
    integers: int
    columns: int
    rows: int
    fixed_on: int
    fixed_off: int
    warm_accepted: bool = False


def _state_cyclic_rows(
    h: highspy.Highs, first_cols: np.ndarray, last_cols: np.ndarray
) -> np.ndarray:
    """The cyclic balance row of each state column pair ``(first, last)``.

    The production builders write the hour-0 balance with ``+1`` on the
    state's hour-0 column and ``-1`` on its hour-``T-1`` column (the SOC block
    of ``rows.build_constraints``). The row is located on the LP HiGHS holds,
    so no builder internals are assumed beyond those two coefficients.
    """
    lp = h.getLp()
    a = lp.a_matrix_
    start = np.asarray(a.start_, dtype=np.int64)
    index = np.asarray(a.index_, dtype=np.int64)
    value = np.asarray(a.value_, dtype=float)
    out = np.full(first_cols.size, -1, dtype=np.int64)
    for i, (c0, c1) in enumerate(zip(first_cols, last_cols)):
        rows1 = index[start[c1] : start[c1 + 1]]
        vals1 = value[start[c1] : start[c1 + 1]]
        rows0 = index[start[c0] : start[c0 + 1]]
        vals0 = value[start[c0] : start[c0 + 1]]
        cand = set(rows1[vals1 < 0.0].tolist()) & set(rows0[vals0 > 0.0].tolist())
        if len(cand) != 1:
            raise RuntimeError(
                f"could not locate the cyclic state row for columns ({c0}, {c1}): "
                f"{sorted(cand)}"
            )
        out[i] = cand.pop()
    return out


def prefix_bounds(
    params: UcClusterParams,
    int_idx: np.ndarray,
    avail: np.ndarray,
    p0_dispatch_w: np.ndarray,
    p0_prices_w: np.ndarray,
    mc_base_w: np.ndarray,
    zone_idx: np.ndarray,
    noload_w: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Plan-E5 reachability pre-fixing (DESIGN section 2.3), conservative.

    Returns ``(fix_on, fix_off)`` boolean ``(n_int,)`` masks. Fix-ON: the
    cluster's P0 output is at or above ``UC_PREFIX_ON_LOAD_FRAC`` of its
    available capacity in every window hour AND its P0 inframarginal rent
    over the window covers a full restart plus the window's no-load. Fix-OFF:
    its anchor's base cost exceeds the window's maximum P0 dual at its zone by
    ``UC_PREFIX_OFF_MARGIN_USD_PER_MWH`` in every hour AND P0 ran it at zero.
    """
    n_int = int_idx.size
    T_w = avail.shape[1]
    cap = params.pbar_mw[int_idx] * params.n_units[int_idx]
    p0 = np.zeros((params.n_clusters, T_w))
    np.add.at(
        p0,
        params.member_cluster,
        np.asarray(p0_dispatch_w, dtype=float)[params.member_gen, :],
    )
    p0 = p0[int_idx]
    mc_anchor = np.asarray(mc_base_w, dtype=float)[params.anchor_gen[int_idx], :]
    zones = np.asarray(zone_idx, dtype=int)[params.anchor_gen[int_idx]]
    lam = np.asarray(p0_prices_w, dtype=float)[zones, :]
    rent = np.sum(np.maximum(lam - mc_anchor, 0.0) * p0, axis=1)
    restart = (
        params.su_per_mw[int_idx] * cap
        + np.sum(noload_w, axis=1) * params.n_units[int_idx]
    )
    avail_cap = cap[:, None] * avail
    full = np.all(p0 >= UC_PREFIX_ON_LOAD_FRAC * avail_cap - 1e-6, axis=1) & np.all(
        avail_cap > 0.0, axis=1
    )
    fix_on = full & (rent >= restart)
    idle = np.all(p0 <= 1e-6, axis=1)
    out_of_merit = np.all(
        mc_anchor >= lam.max(axis=1, keepdims=True) + UC_PREFIX_OFF_MARGIN_USD_PER_MWH,
        axis=1,
    )
    fix_off = idle & out_of_merit
    assert n_int == fix_on.size
    return fix_on, fix_off


class UcWindowModel:
    """The window MILP: the sliced production LP plus the commitment blocks.

    Args:
        inputs: :func:`slice_window_inputs` output.
        params: The cluster struct-of-arrays.
        mc_w: ``(n_gen, T_w)`` objective costs for the window (integer
            clusters at base cost, everything else at the P1 bid).
        noload_w: ``(n_int, T_w)`` no-load $/h per unit of each integer cluster.
        state: The carried :class:`WindowState`.
        soc_terminal: ``(n_storage,)`` one-sided terminal SOC lower bound
            (P0's level at ``t1 - 1``) or ``None``.
        fix_on / fix_off: optional ``(n_int,)`` pre-fixing masks.
    """

    def __init__(
        self,
        inputs: WindowInputs,
        params: UcClusterParams,
        mc_w: np.ndarray,
        noload_w: np.ndarray,
        state: WindowState,
        soc_terminal: np.ndarray | None = None,
        fix_on: np.ndarray | None = None,
        fix_off: np.ndarray | None = None,
    ) -> None:
        t_build = time.perf_counter()
        self.params = params
        self.int_idx = params.integer_clusters
        self.n_int = int(self.int_idx.size)
        self.model = DispatchModel(inputs.fleet, inputs.demand, **inputs.kwargs)
        self.h: highspy.Highs = self.model._h
        self.layout = self.model.layout
        self.T_w = int(self.layout.T)
        self.n_lp = int(self.layout.total_columns)
        self.fleet = inputs.fleet
        self._install_lp_cost(np.asarray(mc_w, dtype=float))
        self.U0 = self.n_lp
        self.V0 = self.U0 + self.n_int * self.T_w
        self.W0 = self.V0 + self.n_int * self.T_w
        self.n_total = self.W0 + self.n_int * self.T_w
        self.fixed_on = 0
        self.fixed_off = 0
        self._n_uc_rows = 0
        if self.n_int:
            self._add_uc_columns(noload_w, state, fix_on, fix_off)
            self._add_uc_rows(state)
            self._set_integrality()
        self._pin_state_rows(state, soc_terminal)
        self._add_ramp_boundary_rows(inputs, state)
        self.build_s = time.perf_counter() - t_build

    # ----------------------------------------------------------------- build
    def _install_lp_cost(self, mc_w: np.ndarray) -> None:
        """The production cost vector on the LP columns (mirrors ``DispatchModel.solve``)."""
        m = self.model
        min_injectable_mc = None
        if m.dump_cost_full_offer_domain:
            injectable = np.asarray(m.fleet.pmax, dtype=float) > 0.0
            if injectable.any():
                min_injectable_mc = float(mc_w.min(axis=1)[injectable].min())
        cost = build_cost_vector(
            self.layout,
            mc_w,
            m.voll,
            wind_mc=m.wind_mc,
            solar_mc=m.solar_mc,
            storage_discharge_eac=m.storage_discharge_eac,
            storage_discharge_cost=m.storage_discharge_cost,
            ordc_penalties=m.ordc_penalties,
            ordc_penalty_hour_scale=m.ordc_penalty_hour_scale,
            posture_startup_cost=m._posture_startup,
            rps_acp_price=(
                m.rps_region_acp_price
                if m.rps_region_acp_price is not None
                else (m.rps_acp_price or 0.0)
            ),
            link_flow_cost=m.link_flow_cost,
            slack_cost=m.slack_cost,
            min_injectable_mc=min_injectable_mc,
            dis_tranche_arm_idx=m.dis_tranche_arm_idx,
            dis_tranche_price=m.dis_tranche_price,
            coal_take_price=m.coal_plant_floor_price,
        )
        self.h.changeColsCost(
            self.n_lp,
            np.arange(self.n_lp, dtype=np.int32),
            np.asarray(cost, dtype=float),
        )
        self.lp_cost = np.asarray(cost, dtype=float)

    def u_col(self, k, t):
        """Column of ``u`` for integer-local cluster ``k`` (array ok) in hour ``t``."""
        return self.U0 + np.asarray(t) * self.n_int + np.asarray(k)

    def v_col(self, k, t):
        """Column of ``v`` (starts)."""
        return self.V0 + np.asarray(t) * self.n_int + np.asarray(k)

    def w_col(self, k, t):
        """Column of ``w`` (stops)."""
        return self.W0 + np.asarray(t) * self.n_int + np.asarray(k)

    def _carry_bounds(self, state: WindowState) -> tuple[np.ndarray, np.ndarray]:
        """Min-up / min-down carry as ``u`` column bounds (DESIGN section 2.2)."""
        p = self.params
        k = self.int_idx
        T_w, n_int = self.T_w, self.n_int
        n = p.n_units[k]
        lb = np.zeros((n_int, T_w))
        ub = np.broadcast_to(n[:, None], (n_int, T_w)).astype(float).copy()
        H = state.v_hist.shape[1] if state.v_hist.size else 0
        if H:
            # csum[k, m] = units started / stopped in the last m hours before t0.
            csum_v = np.concatenate(
                [np.zeros((n_int, 1)), np.cumsum(state.v_hist[:, ::-1], axis=1)], axis=1
            )
            csum_w = np.concatenate(
                [np.zeros((n_int, 1)), np.cumsum(state.w_hist[:, ::-1], axis=1)], axis=1
            )
            tau = np.arange(T_w)[None, :]
            m_up = np.clip(p.ut_h[k][:, None] - 1 - tau, 0, H)
            m_dn = np.clip(p.dt_h[k][:, None] - 1 - tau, 0, H)
            lb = np.maximum(lb, np.take_along_axis(csum_v, m_up, axis=1))
            ub = np.minimum(ub, n[:, None] - np.take_along_axis(csum_w, m_dn, axis=1))
        return lb, ub

    def _add_uc_columns(self, noload_w, state, fix_on, fix_off) -> None:
        p = self.params
        k = self.int_idx
        T_w, n_int = self.T_w, self.n_int
        n = p.n_units[k].astype(float)
        lb, ub = self._carry_bounds(state)
        floor_need = units_needed_for_floor(p, self.fleet.min_gen, 0, T_w)[k].astype(
            float
        )
        lb = np.maximum(lb, floor_need)
        if fix_on is not None and fix_on.any():
            lb[fix_on, :] = np.maximum(lb[fix_on, :], n[fix_on][:, None])
            self.fixed_on = int(fix_on.sum())
        if fix_off is not None and fix_off.any():
            ub[fix_off, :] = np.minimum(ub[fix_off, :], lb[fix_off, :])
            self.fixed_off = int(fix_off.sum())
        ub = np.maximum(ub, lb)  # a carry can never make a window infeasible by itself
        # Hour-major layout: column U0 + t*n_int + k  <->  array[k, t].T
        u_lb, u_ub = lb.T.ravel(), ub.T.ravel()
        u_cost = np.asarray(noload_w, dtype=float).T.ravel()
        vw_ub = np.broadcast_to(n[None, :], (T_w, n_int)).ravel()
        v_cost = np.broadcast_to(
            (p.su_per_mw[k] * p.pbar_mw[k])[None, :], (T_w, n_int)
        ).ravel()
        n_new = 3 * n_int * T_w
        costs = np.concatenate([u_cost, v_cost, np.zeros(n_int * T_w)])
        lower = np.concatenate([u_lb, np.zeros(n_int * T_w), np.zeros(n_int * T_w)])
        upper = np.concatenate([u_ub, vw_ub, vw_ub])
        empty_i = np.array([], dtype=np.int32)
        self.h.addCols(
            n_new,
            costs,
            lower,
            upper,
            0,
            np.zeros(n_new, dtype=np.int32),
            empty_i,
            np.array([], dtype=float),
        )
        self.u_lower, self.u_upper = lb, ub

    def _add_uc_rows(self, state: WindowState) -> None:
        p = self.params
        k_all = self.int_idx
        T_w, n_int, vph = self.T_w, self.n_int, self.layout.vars_per_hour
        a = p.cluster_availability(self.fleet)[k_all]  # (n_int, T_w)
        pbar = p.pbar_mw[k_all]
        mlf = p.mlf[k_all]
        n = p.n_units[k_all].astype(float)
        int_local = np.full(p.n_clusters, -1)
        int_local[k_all] = np.arange(n_int)
        mem_mask = int_local[p.member_cluster] >= 0
        mem_gen = p.member_gen[mem_mask]
        mem_k = int_local[p.member_cluster[mem_mask]]
        t = np.arange(T_w)
        kk, tt = np.meshgrid(np.arange(n_int), t, indexing="ij")  # (n_int, T_w)
        row_ct = (tt * n_int + kk).ravel()  # row within a (n_int*T_w) block
        rows, cols, data, lo, hi = [], [], [], [], []
        off = 0

        def _block(r, c, d, lower, upper, size):
            nonlocal off
            rows.append(np.asarray(r) + off)
            cols.append(np.asarray(c))
            data.append(np.asarray(d, dtype=float))
            lo.append(np.asarray(lower, dtype=float))
            hi.append(np.asarray(upper, dtype=float))
            off += size

        # Member P columns per (k, t): (n_members, T_w)
        mem_rows = (t[None, :] * n_int + mem_k[:, None]).ravel()
        mem_cols = (t[None, :] * vph + self.layout._p_off + mem_gen[:, None]).ravel()
        size = n_int * T_w
        # (a) sum P - pbar*a*u <= 0
        _block(
            np.concatenate([mem_rows, row_ct]),
            np.concatenate([mem_cols, self.u_col(kk, tt).ravel()]),
            np.concatenate([np.ones(mem_rows.size), -(pbar[:, None] * a).ravel()]),
            np.full(size, -np.inf),
            np.zeros(size),
            size,
        )
        # (b) sum P - mlf*pbar*a*u >= 0 (clusters with a positive mlf only)
        has_mlf = mlf > 0.0
        if has_mlf.any():
            keep_ct = has_mlf[kk.ravel()]
            keep_m = has_mlf[mem_k][:, None].repeat(T_w, axis=1).ravel()
            _block(
                np.concatenate([mem_rows[keep_m], row_ct[keep_ct]]),
                np.concatenate([mem_cols[keep_m], self.u_col(kk, tt).ravel()[keep_ct]]),
                np.concatenate(
                    [
                        np.ones(int(keep_m.sum())),
                        -((mlf * pbar)[:, None] * a).ravel()[keep_ct],
                    ]
                ),
                np.zeros(size),
                np.full(size, np.inf),
                size,
            )
        # (c) logic: u_t - u_{t-1} - v_t + w_t = 0 ; t = 0 uses the carried u_prev.
        kk1, tt1 = kk[:, 1:], tt[:, 1:]
        r_logic = row_ct
        _block(
            np.concatenate([r_logic, (tt1 * n_int + kk1).ravel(), r_logic, r_logic]),
            np.concatenate(
                [
                    self.u_col(kk, tt).ravel(),
                    self.u_col(kk1, tt1 - 1).ravel(),
                    self.v_col(kk, tt).ravel(),
                    self.w_col(kk, tt).ravel(),
                ]
            ),
            np.concatenate(
                [np.ones(size), -np.ones(kk1.size), -np.ones(size), np.ones(size)]
            ),
            np.where(tt == 0, state.u_prev[:, None], 0.0).T.ravel(),
            np.where(tt == 0, state.u_prev[:, None], 0.0).T.ravel(),
            size,
        )
        # (d)/(e) Rajan–Takriti with the sums clipped to the window.
        for widths, col_fn, sign_u, rhs in (
            (p.ut_h[k_all], self.v_col, -1.0, np.zeros(size)),
            (p.dt_h[k_all], self.w_col, 1.0, np.tile(n, T_w)),
        ):
            L = int(min(max(int(widths.max()), 1), T_w))
            lag = np.arange(L)
            j = tt[:, :, None] - lag[None, None, :]  # (n_int, T_w, L)
            valid = (j >= 0) & (lag[None, None, :] < widths[:, None, None])
            r = np.broadcast_to((tt * n_int + kk)[:, :, None], j.shape)[valid]
            c = col_fn(np.broadcast_to(kk[:, :, None], j.shape)[valid], j[valid])
            _block(
                np.concatenate([r, row_ct]),
                np.concatenate([c, self.u_col(kk, tt).ravel()]),
                np.concatenate([np.ones(r.size), np.full(size, sign_u)]),
                np.full(size, -np.inf),
                rhs,
                size,
            )
        A = sp.coo_matrix(
            (np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
            shape=(off, self.n_total),
        ).tocsr()
        lower = np.concatenate(lo)
        upper = np.concatenate(hi)
        self._append_rows(A, lower, upper)
        self._n_uc_rows = int(off)

    def _append_rows(
        self, A: sp.csr_matrix, lower: np.ndarray, upper: np.ndarray
    ) -> None:
        inf = highspy.kHighsInf
        lower = np.where(np.isinf(lower), -inf, lower)
        upper = np.where(np.isinf(upper), inf, upper)
        self.h.addRows(
            int(A.shape[0]),
            np.asarray(lower, dtype=float),
            np.asarray(upper, dtype=float),
            int(A.nnz),
            np.asarray(A.indptr[:-1], dtype=np.int32),
            np.asarray(A.indices, dtype=np.int32),
            np.asarray(A.data, dtype=float),
        )

    def _set_integrality(self) -> None:
        idx = np.arange(self.U0, self.V0, dtype=np.int32)
        self.h.changeColsIntegrality(
            int(idx.size), idx, [highspy.HighsVarType.kInteger] * int(idx.size)
        )

    def _pin_state_rows(
        self, state: WindowState, soc_terminal: np.ndarray | None
    ) -> None:
        """SOC boundary: init from the carried state, one-sided terminal at P0's."""
        n_s = self.layout.n_storage
        if n_s == 0:
            return
        lay = self.layout
        first = np.array([lay.soc_col(s, 0) for s in range(n_s)], dtype=np.int64)
        last = np.array(
            [lay.soc_col(s, self.T_w - 1) for s in range(n_s)], dtype=np.int64
        )
        if state.soc_prev is not None:
            rows = _state_cyclic_rows(self.h, first, last)
            lp = self.h.getLp()
            a = lp.a_matrix_
            start = np.asarray(a.start_, dtype=np.int64)
            index = np.asarray(a.index_, dtype=np.int64)
            value = np.asarray(a.value_, dtype=float)
            for s in range(n_s):
                r = int(rows[s])
                sel = index[start[last[s]] : start[last[s] + 1]] == r
                coef = float(value[start[last[s]] : start[last[s] + 1]][sel][0])
                self.h.changeCoeff(r, int(last[s]), 0.0)
                rhs = -coef * float(state.soc_prev[s])
                self.h.changeRowsBounds(
                    1, np.array([r], dtype=np.int32), np.array([rhs]), np.array([rhs])
                )
        if soc_terminal is not None:
            lp = self.h.getLp()
            cur_lo = np.asarray(lp.col_lower_, dtype=float)[last]
            cur_hi = np.asarray(lp.col_upper_, dtype=float)[last]
            new_lo = np.minimum(
                np.maximum(cur_lo, np.asarray(soc_terminal, dtype=float)), cur_hi
            )
            self.h.changeColsBounds(
                int(last.size), last.astype(np.int32), new_lo, cur_hi
            )

    def _add_ramp_boundary_rows(self, inputs: WindowInputs, state: WindowState) -> None:
        """The ``t0`` ramp transition against the previous hour's dispatch."""
        kw = inputs.kwargs
        gidx = kw.get("ramp_gen_idx")
        if gidx is None or state.p_prev is None or kw.get("ramp_up_mw") is None:
            return
        gidx = np.asarray(gidx, dtype=int)
        gcol = np.asarray(kw["ramp_group_col"], dtype=int)
        ru = np.asarray(kw["ramp_up_mw"], dtype=float)
        rd = np.asarray(kw["ramp_dn_mw"], dtype=float)
        n_groups = ru.size
        pmax = np.asarray(self.fleet.pmax, dtype=float)
        cap_now = np.zeros(n_groups)
        cap_prev = np.zeros(n_groups)
        p_prev = np.zeros(n_groups)
        avail_prev = (
            np.asarray(state.avail_prev, dtype=float)
            if state.avail_prev is not None
            else np.asarray(self.fleet.availability, dtype=float)[:, 0]
        )
        np.add.at(
            cap_now,
            gcol,
            pmax[gidx] * np.asarray(self.fleet.availability, dtype=float)[gidx, 0],
        )
        np.add.at(cap_prev, gcol, pmax[gidx] * avail_prev[gidx])
        np.add.at(p_prev, gcol, np.asarray(state.p_prev, dtype=float)[gidx])
        dcap = cap_now - cap_prev
        upper = p_prev + ru + np.maximum(0.0, dcap)
        lower = p_prev - rd - np.maximum(0.0, -dcap)
        A = sp.coo_matrix(
            (np.ones(gidx.size), (gcol, self.layout._p_off + gidx)),
            shape=(n_groups, self.n_total),
        ).tocsr()
        self._append_rows(A, lower, upper)

    # ----------------------------------------------------------------- warm
    def warm_start_vector(
        self,
        prev: WindowResult | None,
        shift: int,
        p0_slice: np.ndarray,
        u_guess: np.ndarray,
    ) -> np.ndarray:
        """A full column vector for ``setSolution`` (DESIGN section 2.3).

        Hours the previous window also covered take its incumbent shifted by
        ``shift``; the new tail takes P0's thermal dispatch and ``u_guess``
        (``(n_int, T_w)`` units implied by P0), with ``v``/``w`` from the
        differences of ``u``. Blocks the stage does not know are left at zero
        and repaired by HiGHS.
        """
        T_w, n_int, vph = self.T_w, self.n_int, self.layout.vars_per_hour
        x = np.zeros(self.n_total)
        lp = x[: self.n_lp].reshape(T_w, vph)
        lp[:, self.layout._p_off : self.layout._w_off] = np.asarray(
            p0_slice, dtype=float
        ).T
        u = np.asarray(u_guess, dtype=float).copy()
        if prev is not None and shift < prev.col_value.shape[0]:
            prev_lp = prev.col_value[: prev.dispatch.shape[1] * vph].reshape(-1, vph)
            n_over = min(prev_lp.shape[0] - shift, T_w)
            if n_over > 0:
                lp[:n_over, :] = prev_lp[shift : shift + n_over, :]
                u[:, :n_over] = prev.u[:, shift : shift + n_over]
        if n_int:
            u = np.clip(np.round(u), self.u_lower, self.u_upper)
            du = np.diff(np.concatenate([u[:, :1], u], axis=1), axis=1)
            v = np.maximum(du, 0.0)
            w = np.maximum(-du, 0.0)
            x[self.U0 : self.V0] = u.T.ravel()
            x[self.V0 : self.W0] = v.T.ravel()
            x[self.W0 :] = w.T.ravel()
        return x

    # ---------------------------------------------------------------- result
    def extract(self, col_value: np.ndarray, **stats) -> WindowResult:
        """Package a HiGHS column vector as a :class:`WindowResult`."""
        T_w, n_int, vph = self.T_w, self.n_int, self.layout.vars_per_hour
        x = np.asarray(col_value, dtype=float)
        block = x[: self.n_lp].reshape(T_w, vph)
        dispatch = np.ascontiguousarray(
            block[:, self.layout._p_off : self.layout._w_off].T
        )
        soc = (
            np.ascontiguousarray(
                block[:, self.layout._soc_off : self.layout._flow_off].T
            )
            if self.layout.n_storage
            else None
        )
        if n_int:
            u = np.rint(x[self.U0 : self.V0].reshape(T_w, n_int).T).astype(int)
            v = np.rint(x[self.V0 : self.W0].reshape(T_w, n_int).T).astype(int)
            w = np.rint(x[self.W0 :].reshape(T_w, n_int).T).astype(int)
        else:
            u = v = w = np.zeros((0, T_w), dtype=int)
        return WindowResult(
            u=u,
            v=v,
            w=w,
            dispatch=dispatch,
            storage_soc=soc,
            col_value=x,
            integers=int(n_int * T_w),
            columns=int(self.n_total),
            rows=int(self.h.getNumRow()),
            fixed_on=self.fixed_on,
            fixed_off=self.fixed_off,
            build_s=self.build_s,
            **stats,
        )
