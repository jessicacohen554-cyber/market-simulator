"""One rolling window of the MILP unit-commitment stage.

The window LP is the production dispatch LP (``model/lp``, untouched) built on
a ``[t0, t1)`` slice of every hourly input — :func:`slice_window_inputs` —
plus, on the HiGHS handle the :class:`~market_sim.model.lp.model.DispatchModel`
owns, the commitment columns and rows this module adds
(:class:`UcWindowModel`): per integer cluster ``c`` and window hour ``t`` an
integer ``u[c,t]`` (units online, ``0..n_c``) and continuous ``v[c,t]`` /
``w[c,t]`` (units started / stopped), the output-coupling rows, the logic
row, the Rajan–Takriti min-up / min-down rows in rolling-horizon form (the
carried start / stop history on their right-hand side), the look-ahead
min-down guard rows and the boundary edits of DESIGN section 2
(``docs/records/governance/uc-milp-2026-10/DESIGN-uc-milp-engine-2026-10-03.md``,
section 2.2 as amended by FINDING-ucmilp-1-fix-window-infeasibility-2026-10-04).
Every row family is assembled from index arithmetic over all clusters and
hours at once (rule 2: no Python loop over hours).

What the window cannot carry (declared, DESIGN section 2.1): the annual and
monthly budget families are dropped and their generators pinned to the P0
dispatch (``uc_boundary_mode = "p0_targets"``); the posture family is refused
upstream; a hydraulic cascade (``hydro_cascade``) is refused here because its
lagged upstream terms wrap cyclically at the window edge and the slim P0
extract carries no pond levels to pin them to (DESIGN section 8).

Reserve headroom (uc-1.6, FINDING-ucmilp-fix6-reserve-headroom-2026-10-14):
where the sliced LP carries the ISO's reserve co-optimization, an integer
cluster member's share of every reserve headroom row is its COMMITTED
capacity, ``pmax * a * u / n``, not ``pmax * a`` (:func:`reserve_headroom_u_terms`)
— the ceiling the schedule later imposes on P1. The rows stay the production
rows (one reserve mechanism, rule 19); only their integer-member capacity
moves from the right-hand side onto ``u``.
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
from market_sim.model.uc.pocket import PocketRequirement
from market_sim.model.uc.selfcommit import SelfCommitRequirement
from market_sim.model.uc.slim import SlimReduction, reduce_window

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
        "import_link_band",
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


#: Round-off guard on ``n * a`` before the ceiling in the pocket rows'
#: available-unit count (a float availability of exactly k/n must read k units,
#: not k + 1).
_AVAIL_UNIT_TOL: float = 1e-9


class UcWindowInfeasible(RuntimeError):
    """A window returned no feasible commitment (GATESPEC section 5 kill).

    Attributes (``None`` where the caller gave no context):
        window_index / t0 / t1: Which rolling window failed and its hour range.
        relaxation_status: The HiGHS status of the window's LP relaxation,
            re-solved on the same handle after the MILP failed — separates a
            row/bound contradiction (relaxation infeasible too) from an
            integrality-only one.
        diagnosis: :func:`market_sim.model.uc.diagnose.diagnose_window`'s
            zero-LP report (bound propagation per row family, history and
            floor consistency).
    """

    def __init__(
        self,
        message: str,
        *,
        window_index: int | None = None,
        t0: int | None = None,
        t1: int | None = None,
        relaxation_status: str | None = None,
        diagnosis: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.window_index = window_index
        self.t0 = t0
        self.t1 = t1
        self.relaxation_status = relaxation_status
        self.diagnosis = diagnosis


def _slice_obj(obj, t0: int, t1: int, T: int):
    """Slice every array with a ``T`` axis (last, or leading for a 2-D
    time-major array) to ``[t0, t1)``.

    Hour-minor arrays ``(..., T)`` are the fleet and kwargs convention; the
    time-major ``(T, n_links)`` form is the per-hour transfer limit
    (``ttc`` / ``ttc_import``, ``lp/bounds.py``: an ISO with an hourly
    interface overlay, ERCOT's measured GTC and NYISO's seasonal TTC). Left
    unsliced it cannot broadcast into the window's ``(T_w, n_links)`` flow
    bounds (the UC-2-ERCOT L1 gate, 2026-10-10). Recurses into tuples, lists,
    dicts and dataclasses; scalars, ``None`` and arrays with no ``T`` axis pass
    through unchanged.
    """
    if isinstance(obj, np.ndarray):
        if obj.ndim >= 1 and obj.shape[-1] == T:
            return np.ascontiguousarray(obj[..., t0:t1])
        if obj.ndim == 2 and obj.shape[0] == T:
            return np.ascontiguousarray(obj[t0:t1, :])
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


def budget_pinned_gens(dispatch_kwargs: dict) -> np.ndarray:
    """Sorted fleet rows a dropped budget family names (:data:`BUDGET_GEN_IDX_KEYS`)."""
    pinned: set[int] = set()
    for key in BUDGET_GEN_IDX_KEYS:
        val = dispatch_kwargs.get(key)
        if val is not None:
            pinned.update(int(g) for g in np.asarray(val, dtype=int).ravel())
    return np.array(sorted(pinned), dtype=int)


def window_fleet(
    fleet: FleetArrays,
    dispatch_kwargs: dict,
    t0: int,
    t1: int,
    p0_dispatch: np.ndarray | None = None,
    free_budget_units: bool = False,
) -> tuple[FleetArrays, np.ndarray]:
    """The fleet a window over ``[t0, t1)`` sees, and the rows pinned to P0.

    The hourly fields are sliced and every row a dropped budget family names
    (:data:`BUDGET_GEN_IDX_KEYS`) is pinned to its P0 dispatch through its
    ``availability`` (``P0 / pmax``) and ``min_gen`` (``P0``). Every field is
    hour-local, so the fleet of ``[t0, t1)`` is the same hour by hour whatever
    window it belongs to: the look-ahead min-down guard reads its floor needs
    from this function too (``pipeline/uc.py``), never from the unpinned year
    fleet, so the guard sees exactly the floors and availability the next
    window's rows will hold (FINDING-ucmilp-fix2-floor-mindown-2026-10-10).
    ``free_budget_units`` leaves the rows unpinned (the bench P0 stand-in only).
    """
    T = int(np.asarray(fleet.availability).shape[-1])
    pinned_gens = budget_pinned_gens(dispatch_kwargs)
    fleet_w = _slice_obj(fleet, t0, t1, T)
    if pinned_gens.size and not free_budget_units:
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
    return fleet_w, pinned_gens


def slice_window_inputs(
    fleet: FleetArrays,
    demand: np.ndarray,
    dispatch_kwargs: dict,
    t0: int,
    t1: int,
    p0_dispatch: np.ndarray | None = None,
    free_budget_units: bool = False,
    p0_flows: np.ndarray | None = None,
) -> WindowInputs:
    """Build the window inputs from the year's (DESIGN section 2.1).

    Args:
        fleet: The year's fleet.
        demand: ``(n_zones, T)``.
        dispatch_kwargs: The assembled year kwargs.
        t0, t1: The window's hour range.
        p0_dispatch: ``(n_gen, T)`` P0 dispatch; the budget-governed rows are
            pinned to it (``None`` only in tests that pass no budget family).
        free_budget_units: Leave the budget-governed rows free within their
            availability instead of pinning them — the ladder's P0 stand-in
            (``uc_bench._relaxation_as_p0``) only; never the production hook.
        p0_flows: ``(n_links, T)`` P0 link flows. The monthly per-link import
            band (``import_link_band``, NYISO landing links) is a budget
            family like the import-node band: it is dropped and its links'
            flows are pinned to P0 over ``[t0, t1)`` (both bounds set to the
            P0 flow; a pinned link is marked bidirectional so a one-way floor
            cannot loosen the pin). Required when the band is armed.

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
    kwargs_w = {
        k: _slice_obj(v, t0, t1, T)
        for k, v in dispatch_kwargs.items()
        if k not in BUDGET_KWARGS and k != "T"
    }
    fleet_w, pinned_gens = window_fleet(
        fleet, dispatch_kwargs, t0, t1, p0_dispatch, free_budget_units
    )
    band = dispatch_kwargs.get("import_link_band")
    if band is not None and not free_budget_units:
        if p0_flows is None:
            raise ValueError(
                "the monthly import link band needs the P0 flows to pin to"
            )
        link_idx = np.asarray(band[0], dtype=int).ravel()
        f = np.asarray(p0_flows, dtype=float)[link_idx, t0:t1].T  # (T_w, n_band)
        T_w = t1 - t0
        ttc_w = np.asarray(kwargs_w["ttc"], dtype=float)
        n_links = ttc_w.shape[-1]
        ttc_w = np.array(np.broadcast_to(ttc_w, (T_w, n_links)), copy=True)
        imp = kwargs_w.get("ttc_import")
        imp_w = np.array(
            np.broadcast_to(
                np.asarray(ttc_w if imp is None else imp, dtype=float), (T_w, n_links)
            ),
            copy=True,
        )
        ttc_w[:, link_idx] = f
        imp_w[:, link_idx] = -f
        kwargs_w["ttc"] = ttc_w
        kwargs_w["ttc_import"] = imp_w
        bidir = kwargs_w.get("link_bidirectional")
        if bidir is not None:
            bidir = np.array(bidir, dtype=bool, copy=True)
            bidir[link_idx] = True
            kwargs_w["link_bidirectional"] = bidir
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
    #: Seconds of ``build_s`` spent constructing the sliced production
    #: ``DispatchModel`` (its matrix build and the HiGHS ``addCols`` /
    #: ``addRows``); the remainder is the UC columns, rows and boundary edits.
    lp_build_s: float = 0.0
    #: The HiGHS phase profile of the solve (``solve.PHASE_KEYS`` plus
    #: ``set_solution_s`` / ``extract_s``); ``None`` on a result a test builds
    #: without solving.
    phase: dict | None = None
    #: The slim window (``uc_slim_window``, ``model/uc/slim.py``): the
    #: columns and rows of the model HiGHS actually solved (equal to
    #: ``columns`` / ``rows`` when the window solved on the full model), the
    #: reduction census and the seconds the reduction took.
    slim_columns: int = 0
    slim_rows: int = 0
    slim_counts: dict | None = None
    slim_s: float = 0.0


def _lp_matrix_csc(h: highspy.Highs) -> sp.csc_matrix:
    """The constraint matrix HiGHS holds, as scipy CSC (whichever format HiGHS stores)."""
    lp = h.getLp()
    a = lp.a_matrix_
    start = np.asarray(a.start_, dtype=np.int64)
    index = np.asarray(a.index_, dtype=np.int64)
    value = np.asarray(a.value_, dtype=float)
    n_row, n_col = int(lp.num_row_), int(lp.num_col_)
    if a.format_ == highspy.MatrixFormat.kRowwise:
        return sp.csr_matrix((value, index, start), shape=(n_row, n_col)).tocsc()
    return sp.csc_matrix((value, index, start), shape=(n_row, n_col))


def _state_cyclic_rows(
    A: sp.csc_matrix, first_cols: np.ndarray, last_cols: np.ndarray
) -> np.ndarray:
    """The cyclic balance row of each state column pair ``(first, last)``.

    The production builders write the hour-0 balance with ``+1`` on the
    state's hour-0 column and ``-1`` on its hour-``T-1`` column (the SOC block
    of ``rows.build_constraints``). The row is located on the LP HiGHS holds
    (``A``), so no builder internals are assumed beyond those two coefficients.
    """
    out = np.full(first_cols.size, -1, dtype=np.int64)
    for i, (c0, c1) in enumerate(zip(first_cols, last_cols)):
        col1 = A.getcol(int(c1))
        col0 = A.getcol(int(c0))
        rows1 = col1.indices[col1.data < 0.0]
        rows0 = col0.indices[col0.data > 0.0]
        cand = set(rows1.tolist()) & set(rows0.tolist())
        if len(cand) != 1:
            raise RuntimeError(
                f"could not locate the cyclic state row for columns ({c0}, {c1}): "
                f"{sorted(cand)}"
            )
        out[i] = cand.pop()
    return out


def reserve_headroom_u_terms(
    model: DispatchModel,
    params: UcClusterParams,
    kwargs: dict,
    row0: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """The u-gate of the reserve headroom rows the sliced LP carries.

    Every capacity-anchored reserve headroom row of the production LP reads
    ``sum P + sum R (+ storage room) <= sum_{eligible g} pmax_g * a_g,t (+ ...)``
    (``lp/reserve_rows.py``: the zone-aggregate shared-headroom rows and the
    per-generator joint P+R pool rows), so an integer cluster at ``u = 0``
    still "carries" reserve on its whole available capacity. Inside the
    window that capacity is moved onto the cluster's ``u``: member ``g`` of
    integer cluster ``c`` contributes ``pmax_g * a_g,t * u_c,t / n_c`` to the
    row, the ceiling the schedule puts on P1 (``pipeline/uc.py``,
    ``availability * u / n``), so reserve on an integer member is
    ``r <= pmax * a * u / n - P``. At ``u = n`` the row is the production row
    unchanged.

    No product is exempt: an integer cluster is by construction NOT fast-start
    (:func:`~market_sim.model.uc.params.integer_gate`, the posture fast-start
    exemption inverted), and that exemption is exactly the set whose OFFLINE
    capacity the reserve specs credit for non-synchronized products (offline
    supplemental / non-spin; ``model.reserves.spec.POSTURE_FAST_START_*``).
    Non-integer members — fast-start or not a cluster — keep ``pmax * a``.
    Rows already P-gated (a legacy ``reserve_online_gated`` class, whose row
    has no capacity right-hand side) are left alone; the pergen per-column
    online-gated coupling rows are separate rows and are untouched.

    Args:
        model: The window's production ``DispatchModel`` (built, not solved).
        params: The cluster struct-of-arrays.
        kwargs: The window dispatch kwargs the model was built from (the
            reserve spec: eligibility, headroom rows, pergen pools).
        row0: Index of the first reserve row on the HiGHS handle (the reserve
            block is the LP's last ``model._n_reserve_rows`` rows).

    Returns:
        ``(rows, u_local, vals, rhs_rows, rhs_cut)``: the coefficient triplets
        of the ``u`` columns (``u_local`` = ``t * n_int + k``, the window's
        ``u`` block order; duplicates are summed by the caller's sparse
        assembly) and the per-row right-hand-side reduction (the integer
        member capacity the triplets now carry). All empty when the LP carries
        no reserve co-optimization or no integer member is reserve-eligible.
    """
    empty_i = np.zeros(0, dtype=np.int64)
    empty = (empty_i, empty_i, np.zeros(0), empty_i, np.zeros(0))
    lay = model.layout
    if not getattr(model, "_coopt", False) or lay.n_reserve == 0:
        return empty
    kw = kwargs
    k_all = params.integer_clusters
    n_int = int(k_all.size)
    if not n_int:
        return empty
    T = int(lay.T)
    fleet = model.fleet
    int_local = np.full(params.n_clusters, -1)
    int_local[k_all] = np.arange(n_int)
    is_int_mem = int_local[params.member_cluster] >= 0
    mem_gen = params.member_gen[is_int_mem]
    mem_k = int_local[params.member_cluster[is_int_mem]]
    k_of_gen = np.full(lay.n_gen, -1)
    k_of_gen[mem_gen] = mem_k
    n_units = params.n_units[k_all].astype(float)
    pmax = np.asarray(fleet.pmax, dtype=float)
    avail = np.asarray(fleet.availability, dtype=float)
    zone_idx = np.asarray(fleet.zone_idx, dtype=int)
    # (entry -> row within one hour of the headroom block, entry -> gen),
    # plus the hour stride of the block.
    pergen_gidx = kw.get("reserve_pergen_gen_idx")
    if pergen_gidx is not None:
        gidx = np.asarray(pergen_gidx, dtype=int)
        col = kw.get("reserve_pergen_col")
        col = np.arange(gidx.size) if col is None else np.asarray(col, dtype=int)
        n_pools = int(col.max()) + 1 if col.size else 0
        sel = k_of_gen[gidx] >= 0
        e_row, e_gen, stride = col[sel], gidx[sel], n_pools
    else:
        elig = kw.get("reserve_eligible")
        elig2d = np.atleast_2d(
            np.ones(lay.n_gen, dtype=bool)
            if elig is None
            else np.asarray(elig, dtype=bool)
        )
        n_classes = elig2d.shape[0]
        hr_prod = kw.get("reserve_headroom_products")
        if hr_prod is None:
            hr_elig = elig2d
            gated = kw.get("reserve_online_gated")
            gated = (
                np.zeros(n_classes, dtype=bool)
                if gated is None
                else np.asarray(gated, dtype=bool).reshape(n_classes)
            )
        else:
            hr_elig = np.atleast_2d(
                np.asarray(kw["reserve_headroom_eligible"], dtype=bool)
            )
            gated = np.zeros(hr_elig.shape[0], dtype=bool)
        n_zones = int(lay.n_zones)
        hh, gg = np.nonzero(hr_elig & ~gated[:, None])
        sel = k_of_gen[gg] >= 0
        hh, gg = hh[sel], gg[sel]
        e_row, e_gen, stride = (
            hh * n_zones + zone_idx[gg],
            gg,
            hr_elig.shape[0] * n_zones,
        )
    if not e_gen.size:
        return empty
    t = np.arange(T)
    cap = pmax[e_gen][:, None] * avail[e_gen, :T]  # (n_entries, T)
    rows = (row0 + t[None, :] * stride + e_row[:, None]).ravel()
    k_e = k_of_gen[e_gen]
    u_local = (t[None, :] * n_int + k_e[:, None]).ravel()
    vals = (-cap / n_units[k_e][:, None]).ravel()
    return rows, u_local, vals, rows, cap.ravel()


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
        slim: Build the slim window (``uc_slim_window``): the exact
            reduction of ``model/uc/slim.py`` on the full model, solved on
            its own handle (:attr:`h_solve`); the full handle (:attr:`h`)
            stays for the diagnosis, relaxation and dump paths. A reduction
            that meets a contradiction leaves the window on the full model.
        floor_need_ahead: ``(n_int, n_ahead)`` units the structural member
            floors need in the hours ``t1, t1 + 1, ...`` AFTER the window
            (:func:`~market_sim.model.uc.params.units_needed_for_floor` on
            the year fleet). Feeds the look-ahead min-down guard rows: a
            stop inside the window that would leave fewer units than a
            floor the window cannot see needs — before that unit's min-down
            expires — is refused here, so the next window never inherits a
            floor it cannot honour (FINDING-ucmilp-1-fix-window-infeasibility
            -2026-10-04 section 3). ``None`` adds no guard row (the year's
            last window, and tests without a floor).
        pocket: The VLR load-pocket requirement
            (``vlr_pocket_commitment``; :mod:`market_sim.model.uc.pocket`), or
            ``None`` for no pocket row (:meth:`_add_pocket_rows`).
        selfcommit: The Sector-1 ST_GAS self-commitment requirement on this
            window (``spp_selfcommit_sector1_st_gas``;
            :mod:`market_sim.model.uc.selfcommit`, already
            :meth:`~market_sim.model.uc.selfcommit.SelfCommitRequirement.sliced`
            to ``[t0, t1)``), or ``None`` for no row
            (:meth:`_add_selfcommit_rows`).
        u_floor: ``(n_int, T_w)`` add-only lower bound on ``u`` — the DA
            schedule a reliability-commitment (RUC) window may add to but
            never de-commit (``uc_reliability_commitment``; DESIGN-ucmilp-
            ruc-stage-2026-10-16 section 2.1). ``None`` (every DA window)
            adds no bound.
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
        floor_need_ahead: np.ndarray | None = None,
        slim: bool = False,
        pocket: PocketRequirement | None = None,
        u_floor: np.ndarray | None = None,
        selfcommit: SelfCommitRequirement | None = None,
    ) -> None:
        t_build = time.perf_counter()
        self.params = params
        self.int_idx = params.integer_clusters
        self.n_int = int(self.int_idx.size)
        self.model = DispatchModel(inputs.fleet, inputs.demand, **inputs.kwargs)
        self.lp_build_s = time.perf_counter() - t_build
        self.h: highspy.Highs = self.model._h
        self.layout = self.model.layout
        self.T_w = int(self.layout.T)
        self.n_lp = int(self.layout.total_columns)
        self.fleet = inputs.fleet
        #: Fleet rows a dropped budget family pinned to P0 (the diagnosis names them).
        self.pinned_gens = np.asarray(inputs.pinned_gens, dtype=int)
        self._install_lp_cost(np.asarray(mc_w, dtype=float))
        self.U0 = self.n_lp
        self.V0 = self.U0 + self.n_int * self.T_w
        self.W0 = self.V0 + self.n_int * self.T_w
        self.n_total = self.W0 + self.n_int * self.T_w
        self.fixed_on = 0
        self.fixed_off = 0
        #: Reserve headroom rows whose integer-member capacity moved onto ``u``
        #: (:func:`reserve_headroom_u_terms`; 0 when no reserve is co-optimized).
        self.n_reserve_gated_rows = 0
        self._n_uc_rows = 0
        self._n_guard_rows = 0
        self._n_ramp_rows = 0
        #: VLR pocket rows (``vlr_pocket_commitment``), after the UC rows.
        self._n_pocket_rows = 0
        #: Pocket sets with no integer cluster in this window (no row built).
        self.pocket_sets_skipped = 0
        #: Self-commitment rows (``spp_selfcommit_sector1_st_gas``), after the
        #: pocket rows.
        self._n_selfcommit_rows = 0
        #: Required cluster-hours the window relaxed below ``min_units``
        #: (outage, or a carried min-down) — rule 17's window relief, counted.
        self.selfcommit_relaxed_hours = 0
        self.hist_v = np.zeros((self.n_int, self.T_w))
        self.hist_w = np.zeros((self.n_int, self.T_w))
        if self.n_int:
            self.hist_v, self.hist_w = self._carry_history(state)
            self._add_uc_columns(
                noload_w, state, fix_on, fix_off, inputs.kwargs, u_floor
            )
            self._add_uc_rows(state, floor_need_ahead)
            self._add_pocket_rows(pocket)
            self._add_selfcommit_rows(selfcommit)
            self._set_integrality()
        self._pin_state_rows(state, soc_terminal)
        self._add_ramp_boundary_rows(inputs, state)
        self.build_s = time.perf_counter() - t_build
        #: The exact reduction the window solves on (``None``: the full model).
        self.slim: SlimReduction | None = None
        #: The handle :func:`~market_sim.model.uc.solve.solve_window` runs.
        self.h_solve: highspy.Highs = self.h
        self.slim_s = 0.0
        if slim:
            t_slim = time.perf_counter()
            red, h_slim = reduce_window(self.h, integer_cols=self.u_cols_full())
            if red is not None:
                self.h_solve = h_slim
                self.slim = red
            self.slim_s = time.perf_counter() - t_slim

    # ------------------------------------------------------------------ slim
    def u_cols_full(self) -> np.ndarray:
        """The ``u`` columns of the full model (``U0 .. V0``), int32."""
        return np.arange(self.U0, self.V0, dtype=np.int32)

    def u_cols_solve(self) -> np.ndarray:
        """The ``u`` columns of the model that solves (slim or full), int32.

        A ``u`` column the reduction fixed has no slim column and is absent.
        """
        full = self.u_cols_full()
        if self.slim is None:
            return full
        idx = self.slim.slim_index(full)
        return idx[idx >= 0].astype(np.int32)

    def set_u_integrality(self, integer: bool) -> None:
        """Make every ``u`` of the solving model integer or continuous (the relaxation rung)."""
        idx = self.u_cols_solve()
        if not idx.size:
            return
        kind = (
            highspy.HighsVarType.kInteger
            if integer
            else highspy.HighsVarType.kContinuous
        )
        self.h_solve.changeColsIntegrality(int(idx.size), idx, [kind] * int(idx.size))

    def to_solve_space(self, x_full: np.ndarray) -> np.ndarray:
        """A full column vector (the warm start) in the solving model's space."""
        x = np.asarray(x_full, dtype=float)
        return x if self.slim is None else self.slim.restrict(x)

    def from_solve_space(self, x_solve: np.ndarray) -> np.ndarray:
        """The solving model's column vector back in the full space (fixed values reinserted)."""
        x = np.asarray(x_solve, dtype=float)
        return x if self.slim is None else self.slim.expand(x)

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

    def _history_cumsum(self, hist: np.ndarray) -> np.ndarray:
        """``csum[k, m]`` = events of ``hist`` in the last ``m`` hours before ``t0``."""
        return np.concatenate(
            [np.zeros((self.n_int, 1)), np.cumsum(hist[:, ::-1], axis=1)], axis=1
        )

    def _carry_history(self, state: WindowState) -> tuple[np.ndarray, np.ndarray]:
        """The carried start / stop history each window hour still feels.

        ``hist_v[k, tau]`` = units of cluster ``k`` started in the last
        ``ut_k - 1 - tau`` hours before ``t0`` (still inside their min-up at
        window hour ``tau``); ``hist_w[k, tau]`` = units stopped in the last
        ``dt_k - 1 - tau`` hours (still inside their min-down). Both enter the
        Rajan–Takriti rows of :meth:`_add_uc_rows` as right-hand-side constants
        — the rolling-horizon form of the rows, in which the history and the
        window's own starts / stops are summed in ONE inequality. Carrying the
        history as a separate ``u`` column bound (the engine before
        FINDING-ucmilp-1-fix-window-infeasibility-2026-10-04) let a window stop
        a unit still inside its min-up whenever another unit's earlier start
        satisfied the bound on its own; the kept history then held more starts
        within one min-up than the plant has units, and a later window's bound
        exceeded ``n`` (SPP 2020, plants 2965 and 2817).
        """
        p = self.params
        k = self.int_idx
        T_w, n_int = self.T_w, self.n_int
        hist_v = np.zeros((n_int, T_w))
        hist_w = np.zeros((n_int, T_w))
        H = state.v_hist.shape[1] if state.v_hist.size else 0
        if H:
            csum_v = self._history_cumsum(state.v_hist)
            csum_w = self._history_cumsum(state.w_hist)
            tau = np.arange(T_w)[None, :]
            m_up = np.clip(p.ut_h[k][:, None] - 1 - tau, 0, H)
            m_dn = np.clip(p.dt_h[k][:, None] - 1 - tau, 0, H)
            hist_v = np.take_along_axis(csum_v, m_up, axis=1)
            hist_w = np.take_along_axis(csum_w, m_dn, axis=1)
        return hist_v, hist_w

    def _add_uc_columns(
        self, noload_w, state, fix_on, fix_off, kwargs=None, u_floor=None
    ) -> None:
        p = self.params
        k = self.int_idx
        T_w, n_int = self.T_w, self.n_int
        n = p.n_units[k].astype(float)
        # Column bounds: the structural floors (clipped exactly as the LP clips
        # the member P lower bounds) and the carried history. The history
        # bounds are implied by the rows below (a window with no start of its
        # own must still carry ``hist_v`` units) and only tighten the root
        # relaxation; the rows are the mechanism.
        floor_need = units_needed_for_floor(p, self.fleet, 0, T_w)[k].astype(float)
        lb = np.maximum(self.hist_v, floor_need)
        ub = n[:, None] - self.hist_w
        if fix_on is not None and fix_on.any():
            # Plan-E5 fix-ON: every unit NOT inside its min-down is online.
            lb[fix_on, :] = np.maximum(lb[fix_on, :], ub[fix_on, :])
            self.fixed_on = int(fix_on.sum())
        if fix_off is not None and fix_off.any():
            ub[fix_off, :] = np.minimum(ub[fix_off, :], lb[fix_off, :])
            self.fixed_off = int(fix_off.sum())
        if u_floor is not None:
            # RUC add-only: never fewer units than the DA schedule held.
            lb = np.maximum(lb, np.asarray(u_floor, dtype=float))
        # A floor can need more units than the carried min-down leaves (only
        # when the previous window had no look-ahead guard for it: the first
        # window, or a test state); the bound is widened so the contradiction
        # surfaces in the min-down ROW, where the diagnosis names it.
        ub = np.maximum(ub, lb)
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
        # Reserve headroom u-gate: the u columns enter the production reserve
        # headroom rows with -pmax*a/n per integer member, and those rows'
        # right-hand side drops the same member capacity (uc-1.6).
        n_row = int(self.h.getNumRow())
        r_rows, r_u, r_vals, rhs_rows, rhs_cut = reserve_headroom_u_terms(
            self.model, p, kwargs or {}, n_row - int(self.model._n_reserve_rows)
        )
        A_u = sp.csc_matrix((r_vals, (r_rows, r_u)), shape=(n_row, n_new))
        A_u.sum_duplicates()
        self.h.addCols(
            n_new,
            costs,
            lower,
            upper,
            int(A_u.nnz),
            np.asarray(A_u.indptr[:-1], dtype=np.int32),
            np.asarray(A_u.indices, dtype=np.int32),
            np.asarray(A_u.data, dtype=float),
        )
        if rhs_rows.size:
            cut = np.bincount(rhs_rows, weights=rhs_cut, minlength=n_row)
            touched = np.flatnonzero(cut > 0.0).astype(np.int32)
            lp = self.h.getLp()
            row_lo = np.asarray(lp.row_lower_, dtype=float)[touched]
            row_hi = np.asarray(lp.row_upper_, dtype=float)[touched]
            new_hi = row_hi - cut[touched]
            tol = 1e-6 * np.maximum(1.0, np.abs(row_hi))
            if np.any(new_hi < -tol):
                raise RuntimeError(
                    "reserve headroom u-gate: integer member capacity exceeds "
                    "the row's right-hand side (the reserve block is not where "
                    "the layout says)"
                )
            self.h.changeRowsBounds(
                int(touched.size), touched, row_lo, np.maximum(new_hi, 0.0)
            )
            self.n_reserve_gated_rows = int(touched.size)
        self.u_lower, self.u_upper = lb, ub

    def _add_uc_rows(
        self, state: WindowState, floor_need_ahead: np.ndarray | None = None
    ) -> None:
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
        # (d)/(e) Rajan–Takriti in rolling-horizon form: the window's own
        # starts / stops within the min-up / min-down reach of hour t, PLUS the
        # carried history still inside that reach (``hist_v`` / ``hist_w``,
        # constants on the right-hand side), in ONE row —
        #   (d)  sum_{lag<UT} v[t-lag] - u[t] <= -hist_v[t]
        #   (e)  sum_{lag<DT} w[t-lag] + u[t] <=  n - hist_w[t].
        for widths, col_fn, sign_u, rhs in (
            (p.ut_h[k_all], self.v_col, -1.0, (-self.hist_v).T.ravel()),
            (p.dt_h[k_all], self.w_col, 1.0, (n[:, None] - self.hist_w).T.ravel()),
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
        # (f) Look-ahead min-down guard: row (e) for the hours h = T_w + h'
        # AFTER the window, with u[h] replaced by its known lower bound (the
        # units the structural floors need there) —
        #   sum_{tau in window, h - tau < DT} w[tau] <= n - floor_need[h] - hist_w[h].
        # A stop the window takes is thereby never one a floor it cannot see
        # will need before the min-down expires; rows exist only where a floor
        # needs a unit and some window hour is within reach (h' < DT - 1).
        if floor_need_ahead is not None and floor_need_ahead.size:
            need = np.asarray(floor_need_ahead, dtype=float)
            n_ahead = int(need.shape[1])
            dt = p.dt_h[k_all].astype(int)
            hh = np.arange(n_ahead)
            kk2, hh2 = np.meshgrid(
                np.arange(n_int), hh, indexing="ij"
            )  # (n_int, n_ahead)
            live = (need > 0.0) & (hh2 < (dt[:, None] - 1))
            if live.any():
                L = int(min(int(dt.max()), T_w + n_ahead))
                lag = np.arange(L)
                j = (T_w + hh2)[:, :, None] - lag[None, None, :]  # window hour
                valid = (
                    (j >= 0)
                    & (j < T_w)
                    & (lag[None, None, :] < dt[:, None, None])
                    & live[:, :, None]
                )
                row_id = np.full(live.shape, -1, dtype=np.int64)
                row_id[live] = np.arange(int(live.sum()))
                r = np.broadcast_to(row_id[:, :, None], j.shape)[valid]
                c = self.w_col(
                    np.broadcast_to(kk2[:, :, None], j.shape)[valid], j[valid]
                )
                H = state.w_hist.shape[1] if state.w_hist.size else 0
                hist_beyond = np.zeros(live.shape)
                if H:
                    csum_w = self._history_cumsum(state.w_hist)
                    m = np.clip(dt[:, None] - 1 - (T_w + hh2), 0, H)
                    hist_beyond = np.take_along_axis(csum_w, m, axis=1)
                rhs = (n[:, None] - need - hist_beyond)[live]
                n_guard = int(live.sum())
                _block(
                    r,
                    c,
                    np.ones(r.size),
                    np.full(n_guard, -np.inf),
                    rhs,
                    n_guard,
                )
                self._n_guard_rows = n_guard
        A = sp.coo_matrix(
            (np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
            shape=(off, self.n_total),
        ).tocsr()
        lower = np.concatenate(lo)
        upper = np.concatenate(hi)
        self._append_rows(A, lower, upper)
        self._n_uc_rows = int(off)

    def _add_pocket_rows(self, pocket: PocketRequirement | None) -> None:
        """(g) VLR load-pocket commitment: ``sum_{c in set} u[c, t] >= rhs[t]``.

        One row per pocket set and window hour, over the integer ``u`` of the
        set's clusters, with
        ``rhs[t] = min(n_req, sum_c min(u_upper[c, t], ceil(n_c * a[c, t])))``:
        the requirement relaxes to the units the window can hold online — not
        inside a carried min-down (``u_upper``) and not on outage (the
        cluster's availability ``a`` covers ``ceil(n * a)`` units) — so the row
        never makes a window infeasible by itself, and an outage never forces
        an unavailable unit on. A set with no integer cluster builds no row
        (counted in :attr:`pocket_sets_skipped`). Integer rows: they are never
        priced (rule 4).
        """
        if pocket is None or pocket.n_sets == 0:
            return
        p = self.params
        k_all = self.int_idx
        T_w = self.T_w
        int_local = np.full(p.n_clusters, -1)
        int_local[k_all] = np.arange(self.n_int)
        a = p.cluster_availability(self.fleet)[k_all]  # (n_int, T_w)
        n = p.n_units[k_all].astype(float)
        avail_units = np.minimum(
            np.asarray(self.u_upper, dtype=float),
            np.maximum(np.ceil(n[:, None] * a - _AVAIL_UNIT_TOL), 0.0),
        )
        rows, cols, lower = [], [], []
        off = 0
        t = np.arange(T_w)
        for s in range(pocket.n_sets):
            loc = int_local[pocket.clusters_of(s)]
            loc = loc[loc >= 0]
            if loc.size == 0:
                self.pocket_sets_skipped += 1
                continue
            rhs = np.minimum(float(pocket.n_req[s]), avail_units[loc].sum(axis=0))
            tt = np.repeat(t, loc.size)
            kk = np.tile(loc, T_w)
            rows.append(off + tt)
            cols.append(self.u_col(kk, tt))
            lower.append(rhs)
            off += T_w
        if not off:
            return
        r = np.concatenate(rows)
        A = sp.coo_matrix(
            (np.ones(r.size), (r, np.concatenate(cols))), shape=(off, self.n_total)
        ).tocsr()
        lo = np.concatenate(lower)
        self._append_rows(A, lo, np.full(off, np.inf))
        self._n_pocket_rows = int(off)

    def _add_selfcommit_rows(self, req: SelfCommitRequirement | None) -> None:
        """(h) Sector-1 ST_GAS self-commitment: ``u[c, t] >= rhs[c, t]``.

        One row per required cluster-hour (``req.required``), over the
        cluster's integer ``u``, with
        ``rhs[c, t] = min(min_units, u_upper[c, t], ceil(n_c * a[c, t]))``: the
        requirement relaxes to the units the window can hold online — not on
        outage (availability ``a`` covers ``ceil(n * a)`` units) and not inside
        a carried min-down (``u_upper``) — so it never forces an unavailable
        unit on (rule 17) and never makes a window infeasible by itself. A
        relaxed cell builds no row and is counted in
        :attr:`selfcommit_relaxed_hours`. The online unit's MW is free above
        the output-coupling row's measured min-load ``mlf * pbar * a * u``
        (rule 18 physics; no P floor is placed). Integer rows: never priced
        (rule 4).
        """
        if req is None or req.n_sel == 0:
            return
        p = self.params
        k_all = self.int_idx
        T_w = self.T_w
        if req.required.shape != (req.n_sel, T_w):
            raise ValueError(
                f"self-commitment mask {req.required.shape} does not match the "
                f"window ({req.n_sel}, {T_w}); slice it to [t0, t1)"
            )
        int_local = np.full(p.n_clusters, -1)
        int_local[k_all] = np.arange(self.n_int)
        loc = int_local[req.clusters]
        if np.any(loc < 0):
            raise ValueError(
                "self-commitment names a cluster with no integer u: "
                f"{req.clusters[loc < 0].tolist()}"
            )
        a = p.cluster_availability(self.fleet)[k_all][loc]  # (n_sel, T_w)
        n = p.n_units[req.clusters].astype(float)
        avail_units = np.minimum(
            np.asarray(self.u_upper, dtype=float)[loc],
            np.maximum(np.ceil(n[:, None] * a - _AVAIL_UNIT_TOL), 0.0),
        )
        rhs = np.minimum(float(req.min_units), avail_units)
        need = np.asarray(req.required, dtype=bool)
        self.selfcommit_relaxed_hours = int(
            np.count_nonzero(need & (rhs < float(req.min_units)))
        )
        cell = need & (rhs > 0.0)
        ii, tt = np.nonzero(cell)
        if ii.size == 0:
            return
        off = int(ii.size)
        A = sp.coo_matrix(
            (np.ones(off), (np.arange(off), self.u_col(loc[ii], tt))),
            shape=(off, self.n_total),
        ).tocsr()
        self._append_rows(A, rhs[ii, tt], np.full(off, np.inf))
        self._n_selfcommit_rows = off

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
            A = _lp_matrix_csc(self.h)
            rows = _state_cyclic_rows(A, first, last)
            for s in range(n_s):
                r = int(rows[s])
                coef = float(A[r, int(last[s])])
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
        self._n_ramp_rows = int(n_groups)

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
            lp_build_s=self.lp_build_s,
            slim_columns=int(self.h_solve.getNumCol()),
            slim_rows=int(self.h_solve.getNumRow()),
            slim_counts=None if self.slim is None else dict(self.slim.counts),
            slim_s=self.slim_s,
            **stats,
        )
