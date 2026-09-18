"""HiGHS model wrapper and cross-year warm-start for the dispatch LP.

Package split of ``model/dispatch.py`` (refactor-consolidation plan §5 item
7): the reusable :class:`DispatchModel` (build once, re-cost per pass), the
cross-year basis column mapper, and the compact HiGHS basis-status codes.
Pure code motion — apart from two lazy imports of the
package-``__init__``-defined result/basis classes (pickle identity, plan
§1), every def is byte-identical to its pre-split ``dispatch.py`` source.
"""

import logging
import os
import time
from typing import TYPE_CHECKING

import highspy
import numpy as np
import scipy.sparse as sp

from market_sim.data.fleet import FleetArrays, assemble_mc
from market_sim.model.lp.bounds import build_variable_bounds
from market_sim.model.lp.costs import build_cost_vector
from market_sim.model.lp.layout import VariableLayout
from market_sim.model.lp.rows import build_constraints

if TYPE_CHECKING:  # quoted annotations only; runtime imports stay lazy (cycle break)
    from market_sim.model.lp import CrossYearBasis, DispatchResult
    from market_sim.model.lp.hydro_cascade import HydroCascadeSpec

logger = logging.getLogger(__name__)


# HiGHS basis-status integer codes (HighsBasisStatus enum), captured once so the
# per-column status vectors can be carried as compact int8 arrays instead of
# millions of Python enum objects.
_BASIS_LOWER = int(highspy.HighsBasisStatus.kLower)
_BASIS_BASIC = int(highspy.HighsBasisStatus.kBasic)
# PERF-A prototype (Exp-2 memoized-enum LUT, wallclock-baseline doc): highspy
# requires Sequence[HighsBasisStatus], so the status handoff must box every
# element — but the five enum objects can be constructed once and indexed,
# instead of calling the enum constructor 13.2M times per basis apply
# (measured 14.9x: 13.4s -> 0.9s on an ERCOT-2023-sized vector, element-wise
# identical).
_BASIS_STATUS_OBJS = [highspy.HighsBasisStatus(i) for i in range(5)]


def _log_rss(label: str) -> None:
    """Peak-memory checkpoint (``MARKET_SIM_MEM_DEBUG=1``): VmRSS + VmHWM.

    Module-level twin of the ``_rss`` closure in ``DispatchModel.__init__``,
    for the solve/extraction phase — the measured owner of the year-solve
    peak (miso-169: build tops out ~5.1 GB while the solve+extraction reach
    ~14.4 GB on the plant-level MISO LP), which the build-phase checkpoints
    alone could not attribute.
    """
    if os.environ.get("MARKET_SIM_MEM_DEBUG") != "1":
        return
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith(("VmRSS", "VmHWM")):
                logger.info("MEM %s: %s", label, line.split(":")[1].strip())


class DispatchModel:
    """A reusable HiGHS dispatch LP whose objective can be re-costed in place.

    The constraint matrix and the variable bounds depend only on the fleet,
    demand and network topology -- never on the marginal cost. The
    calibration's P0 (base cost) and P1 (bid cost) passes therefore share a
    byte-identical feasible region and differ *only* in the objective. Build
    the model once and call :meth:`solve` repeatedly: the second solve changes
    just the cost coefficients and warm-starts the dual simplex from the
    previous optimal basis, which converges in a handful of iterations because
    the basis stays primal-feasible when only costs move.

    The one-shot :func:`solve_dispatch` is a thin wrapper around this class, so
    a single build+solve is numerically identical to the previous code path.
    """

    def __init__(
        self,
        fleet: "FleetArrays",
        demand: np.ndarray,
        wind_cf: np.ndarray,
        wind_cap: np.ndarray,
        solar_cf: np.ndarray,
        solar_cap: np.ndarray,
        voll: float = 5000,
        incidence: "np.ndarray | sp.spmatrix | None" = None,
        ttc: np.ndarray | None = None,
        ttc_import: np.ndarray | None = None,
        wind_curtail_share: np.ndarray | None = None,
        solar_curtail_share: np.ndarray | None = None,
        storage_power_cap: np.ndarray | None = None,
        storage_energy_cap: np.ndarray | None = None,
        storage_soc_min: np.ndarray | None = None,
        storage_discharge_min: np.ndarray | None = None,
        storage_charge_cap: np.ndarray | None = None,
        storage_discharge_cap: np.ndarray | None = None,
        storage_zone_idx: np.ndarray | None = None,
        eta_chg: "np.ndarray | float | None" = None,
        eta_dis: "np.ndarray | float | None" = None,
        wind_mc: "np.ndarray | float" = 0.0,
        solar_mc: "np.ndarray | float" = 0.0,
        storage_discharge_eac: float = 0.0,
        storage_discharge_cost: "np.ndarray | float" = 0.0,
        rps_target: float | None = None,
        rps_acp_price: float | None = None,
        rps_eligible_fuels: tuple[str, ...] | None = None,
        rps_region_zone_mask: np.ndarray | None = None,
        rps_region_obligation_frac: np.ndarray | None = None,
        rps_region_acp_price: np.ndarray | None = None,
        clean_region_zone_mask: np.ndarray | None = None,
        clean_region_obligation_frac: np.ndarray | None = None,
        clean_region_acp_price: np.ndarray | None = None,
        clean_region_fuels: "tuple[tuple[str, ...], ...] | None" = None,
        hydro_monthly_energy: np.ndarray | None = None,
        hydro_month_index: np.ndarray | None = None,
        hydro_gen_idx: np.ndarray | None = None,
        hydro_monthly_min: np.ndarray | None = None,
        hydro_period_hours: np.ndarray | None = None,
        oil_monthly_budget: np.ndarray | None = None,
        oil_gen_idx: np.ndarray | None = None,
        oil_month_index: np.ndarray | None = None,
        oil_gen_hour_coeff: np.ndarray | None = None,
        oil_group_index: np.ndarray | None = None,
        coal_monthly_budget: np.ndarray | None = None,
        coal_gen_idx: np.ndarray | None = None,
        coal_month_index: np.ndarray | None = None,
        coal_gen_hour_coeff: np.ndarray | None = None,
        coal_group_index: np.ndarray | None = None,
        storage_daily_cycle_hours: int | None = None,
        storage_alloc_batt_idx: np.ndarray | None = None,
        storage_alloc_share: np.ndarray | None = None,
        storage_alloc_da_frac: float | None = None,
        interface_groups: list[tuple[np.ndarray, float, bool]] | None = None,
        ramp_gen_idx: np.ndarray | None = None,
        ramp_group_col: np.ndarray | None = None,
        ramp_up_mw: np.ndarray | None = None,
        ramp_dn_mw: np.ndarray | None = None,
        local_capacity_specs: (
            "list[tuple[np.ndarray, np.ndarray, float, np.ndarray]] | None"
        ) = None,
        hydro_envelope_gen_idx: np.ndarray | None = None,
        hydro_envelope_mw: np.ndarray | None = None,
        hydro_envelope_storage_idx: np.ndarray | None = None,
        import_node_gen_idx: np.ndarray | None = None,
        import_node_monthly_lo: np.ndarray | None = None,
        import_node_monthly_hi: np.ndarray | None = None,
        import_node_month_index: np.ndarray | None = None,
        mass_cap_coeffs: np.ndarray | None = None,
        mass_cap_rhs: np.ndarray | None = None,
        mass_cap_labels: list[str] | None = None,
        reserve_requirement: np.ndarray | None = None,
        reserve_eligible: np.ndarray | None = None,
        reserve_storage: bool = False,
        ordc_penalties: np.ndarray | None = None,
        ordc_step_widths: np.ndarray | None = None,
        reserve_balance_zone_mask: np.ndarray | None = None,
        reserve_balance_ordc_counts: np.ndarray | None = None,
        reserve_balance_class: np.ndarray | None = None,
        reserve_online_gated: np.ndarray | None = None,
        reserve_online_rho: float = 1.0,
        reserve_headroom_eligible: np.ndarray | None = None,
        reserve_headroom_products: np.ndarray | None = None,
        reserve_headroom_extra_cap: np.ndarray | None = None,
        reserve_headroom_storage: np.ndarray | None = None,
        reserve_supply_cap: np.ndarray | None = None,
        reserve_online_capacity_cap: np.ndarray | None = None,
        reserve_storage_duration_h: np.ndarray | None = None,
        reserve_pergen_gen_idx: np.ndarray | None = None,
        reserve_pergen_col: np.ndarray | None = None,
        reserve_pergen_ramp10: np.ndarray | None = None,
        reserve_posture_pools: np.ndarray | None = None,
        reserve_posture_mlf: np.ndarray | None = None,
        reserve_posture_startup: np.ndarray | None = None,
        reserve_pergen_col_pool: np.ndarray | None = None,
        reserve_balance_col_mask: np.ndarray | None = None,
        reserve_pergen_online_gated_cols: np.ndarray | None = None,
        reserve_pergen_pool_ramp10: np.ndarray | None = None,
        posture_gen_idx: np.ndarray | None = None,
        posture_col: np.ndarray | None = None,
        posture_mlf: np.ndarray | None = None,
        posture_startup: np.ndarray | None = None,
        link_bidirectional: np.ndarray | None = None,
        link_flow_cost: np.ndarray | None = None,
        link_loss: np.ndarray | None = None,
        slack_cost: np.ndarray | None = None,
        dump_cost_full_offer_domain: bool = False,
        dis_tranche_arm_idx: np.ndarray | None = None,
        dis_tranche_width: np.ndarray | None = None,
        dis_tranche_price: np.ndarray | None = None,
        hydro_cascade: "HydroCascadeSpec | None" = None,
        T: int | None = None,
    ) -> None:
        build_start = time.perf_counter()

        demand = np.asarray(demand, dtype=float)
        if T is None:
            T = demand.shape[1]
        n_zones = demand.shape[0]
        n_gen = fleet.n_gen
        n_storage = 0 if storage_power_cap is None else len(storage_power_cap)
        n_links = 0 if incidence is None else sp.csr_matrix(incidence).shape[1]

        # Storage RT discharge-offer tranches (ERCOT ercot_storage_rt_offer_surface).
        # Each armed battery unit's discharge is decomposed into K priced
        # tranches (_build_dis_tranche_rows) sharing the base Dis column's SOC,
        # energy balance and power cap. Active only when the arm supplies both
        # the armed-unit indices and the tranche width ladder.
        dis_tranche_on = (
            dis_tranche_arm_idx is not None
            and dis_tranche_width is not None
            and dis_tranche_price is not None
            and n_storage > 0
            and len(np.asarray(dis_tranche_arm_idx)) > 0
        )
        n_dis_tranche = 0
        dis_tranche_k = 0
        if dis_tranche_on:
            n_arm = int(len(np.asarray(dis_tranche_arm_idx)))
            dis_tranche_k = int(len(np.asarray(dis_tranche_width)))
            n_dis_tranche = n_arm * dis_tranche_k

        # Hydraulic-cascade coupling (NWPP-36, config.hydro_cascade_coupling):
        # two water columns per coupled downstream plant. None / an empty spec
        # leaves n_cascade = 0 and the layout byte-identical.
        n_cascade = 0
        if hydro_cascade is not None and hydro_cascade.n_coupled:
            n_cascade = 2 * int(hydro_cascade.n_coupled)

        # Energy+reserve co-optimization is active when a requirement is given.
        # Reserve is tracked per ZONE and per reserve CLASS (one reserve var +
        # one shared-headroom row per class-zone-hour, not per unit — the
        # per-unit form is tens of millions of rows at per-plant scale), plus one
        # shortfall var per published ORDC step. The class count comes from the
        # eligibility mask: a flat (n_gen,) mask is one class (ERCOT/PJM), a
        # (n_classes, n_gen) stack is multi-class (NYISO 30-min full fleet vs
        # 10-min quick-start subset).
        coopt = reserve_requirement is not None
        # Per-generator reserve columns (R[j,t] per reserve-providing unit,
        # _build_reserve_rows_pergen) supersede the zone-aggregate layout AND
        # its scoping mechanisms — the per-unit ramp10 bound replaces the
        # system-wide supply cap / online gate / additive headroom spec, so
        # passing both is a wiring error, not a combinable option.
        pergen = coopt and reserve_pergen_gen_idx is not None
        if pergen:
            if (
                reserve_supply_cap is not None
                or reserve_online_capacity_cap is not None
                or reserve_online_gated is not None
                or reserve_headroom_products is not None
            ):
                raise ValueError(
                    "reserve_pergen_gen_idx is mutually exclusive with "
                    "reserve_supply_cap / reserve_online_capacity_cap / "
                    "reserve_online_gated / reserve_headroom_products (per-gen "
                    "ramp10 bounds supersede the zone-aggregate scoping mechanisms)"
                )
            if reserve_pergen_ramp10 is None:
                raise ValueError(
                    "reserve_pergen_gen_idx requires reserve_pergen_ramp10 "
                    "(the per-column 10-min deliverable cap)"
                )
        n_reserve_classes = (
            1
            if not coopt or pergen or reserve_eligible is None
            else int(np.atleast_2d(np.asarray(reserve_eligible)).shape[0])
        )
        n_reserve = (
            0
            if not coopt
            # R-column count: the product split (reserve_pergen_col_pool)
            # carries one entry per R column; else grouped members share a
            # column (reserve_pergen_col maps member -> column), 1:1 otherwise.
            else (
                (
                    int(np.asarray(reserve_pergen_col_pool).size)
                    if reserve_pergen_col_pool is not None
                    else (
                        int(np.asarray(reserve_pergen_col).max()) + 1
                        if reserve_pergen_col is not None
                        else int(np.asarray(reserve_pergen_gen_idx).size)
                    )
                )
                if pergen
                else n_reserve_classes * n_zones
            )
        )
        # Joint-headroom pool count (pergen): the product split maps several
        # R columns onto one pool's joint P+R row; identity otherwise.
        n_pergen_pools = (
            (int(np.asarray(reserve_pergen_col_pool).max()) + 1)
            if (pergen and reserve_pergen_col_pool is not None)
            else n_reserve
        )
        n_ordc_steps = 0 if not coopt or ordc_penalties is None else len(ordc_penalties)
        # Reserve families: one system-wide balance row (ERCOT/PJM) by default,
        # or n locational families when a per-family zone mask is supplied
        # (NYISO nested reserve regions).
        n_families = (
            1
            if not coopt or reserve_balance_zone_mask is None
            else int(np.asarray(reserve_balance_zone_mask).shape[0])
        )
        # Shared-headroom rows: one per reserve class (legacy/NYISO) unless an
        # additive headroom spec is supplied (ERCOT multi-product), where the
        # row count is decoupled from the class count (e.g. a "fast" row nested
        # in an "all" row). Drives the reserve-block row count for dual indexing.
        n_headroom_rows = (
            n_reserve_classes
            if not coopt or reserve_headroom_products is None
            else int(np.atleast_2d(np.asarray(reserve_headroom_products)).shape[0])
        )
        # Duration-gated endogenous storage AS: storage gets its own per-zone
        # RS[c,z] reserve columns (n_reserve_classes * n_zones) plus a
        # power-competition row and a SOC duration-gate row per zone-hour. Active
        # only when durations are supplied, storage is present, and
        # reserve_storage is on. Both co-opt structures support it: the
        # zone-aggregate path (ERCOT ercot_storage_as_duration_gate) and the
        # per-generator path (CAISO caiso_reserve_coopt, issue #1492 — batteries
        # are CAISO's dominant AS providers, so the pergen thermal pool without
        # them over-states thermal scarcity); the RS rows are identical in both,
        # only the thermal side of the co-opt differs.
        storage_gate = (
            coopt
            and reserve_storage
            and reserve_storage_duration_h is not None
            and n_storage > 0
        )
        n_storage_reserve = n_reserve_classes * n_zones if storage_gate else 0

        # Commitment-posture pools. Two disjoint constructions share the U/SU
        # columns and the SU cost/bound machinery but differ in the rows built:
        #  * PERGEN posture (reserve_posture_pools, MISO/CAISO/PJM): re-anchors a
        #    pergen RESERVE pool — requires reserve_pergen_gen_idx; the joint-
        #    headroom / min-load / startup / ramp-gate rows ride
        #    _build_reserve_rows_pergen.
        #  * STANDALONE energy-only posture (posture_gen_idx, ERCOT
        #    ercot_commitment_posture): ERCOT runs a fleet-wide ORDC co-opt with
        #    no pergen substrate, so only the energy-side rows (headroom + min-
        #    load + startup) are built (_build_posture_energy_rows), leaving the
        #    reserve design untouched (rule 19). The two are mutually exclusive.
        standalone_posture = posture_gen_idx is not None
        if reserve_posture_pools is not None and not pergen:
            raise ValueError(
                "reserve_posture_pools requires the per-generator reserve "
                "spec (reserve_pergen_gen_idx) — the posture U columns gate "
                "the pergen pool joint-headroom and ramp rows"
            )
        if standalone_posture and reserve_posture_pools is not None:
            raise ValueError(
                "posture_gen_idx (standalone energy-only posture) is mutually "
                "exclusive with reserve_posture_pools (pergen posture) — one "
                "commitment-posture construction per solve (rule 19)"
            )
        if standalone_posture:
            n_posture = int(np.asarray(posture_mlf).size)
        else:
            n_posture = (
                0
                if reserve_posture_pools is None
                else int(np.asarray(reserve_posture_pools).size)
            )
        # RPS ACP escape columns. Legacy single ISO-wide row: one column,
        # present only when an ACP price accompanies an active RPS target.
        # Per-compliance-region grain (FFR-7B Arm 2, MISO): one column per
        # region — every region row REQUIRES its own escape (its acp price),
        # because a certificate-short region with no buyout would turn the LP
        # infeasible. Absent (default) leaves the layout byte-identical.
        rps_region_on = rps_region_zone_mask is not None
        if rps_region_on:
            if rps_target is not None and rps_target > 0.0:
                raise ValueError(
                    "rps_region_zone_mask (per-region RPS rows) is mutually "
                    "exclusive with rps_target (the single ISO-wide row) — "
                    "the K-row grain REPLACES the ISO-wide row, never stacks "
                    "on it (rule 19 [R-ONE-MECH])"
                )
            if rps_region_obligation_frac is None or rps_region_acp_price is None:
                raise ValueError(
                    "per-region RPS rows require rps_region_obligation_frac "
                    "and rps_region_acp_price — the per-region ACP escape is "
                    "the feasibility guarantee, not an option"
                )
            n_rps_rows = int(np.asarray(rps_region_zone_mask).shape[0])
            n_rec_acp = n_rps_rows
        else:
            n_rps_rows = 1 if (rps_target is not None and rps_target > 0.0) else 0
            n_rec_acp = 1 if (n_rps_rows and rps_acp_price is not None) else 0
        # Clean/carbon-free tier family (FFR-7B Arm 3; the federal CES target
        # row, SCN-WS2a): a SECOND independent row family riding the region
        # machinery. Its ACP escape columns occupy the region-major slots
        # AFTER the RPS family's (K1 of them under the region grain, 1 beside
        # a legacy row with an escape, 0 otherwise) — since SCN-WS2a the
        # family STANDS ALONE OR BESIDE EITHER RPS GRAIN (the former
        # "requires the RPS region family" coupling, G-S3, is relaxed so a
        # federal all-zone clean row can exist in every ISO). Every clean row
        # still REQUIRES its own escape (FFR-6B §6.3: a hard 100%-by-2040 row
        # is an infeasibility bomb).
        clean_region_on = clean_region_zone_mask is not None
        n_clean_rows = 0
        if clean_region_on:
            if (
                clean_region_obligation_frac is None
                or clean_region_acp_price is None
                or clean_region_fuels is None
            ):
                raise ValueError(
                    "clean-tier rows require clean_region_obligation_frac, "
                    "clean_region_acp_price (the feasibility escape) and "
                    "clean_region_fuels (the per-statute qualifying sets)"
                )
            n_clean_rows = int(np.asarray(clean_region_zone_mask).shape[0])
            n_rec_acp += n_clean_rows

        layout = VariableLayout(
            n_gen=n_gen,
            n_zones=n_zones,
            n_storage=n_storage,
            n_links=n_links,
            T=T,
            n_reserve=n_reserve,
            n_reserve_classes=n_reserve_classes,
            n_ordc_steps=n_ordc_steps,
            n_storage_reserve=n_storage_reserve,
            n_posture=n_posture,
            n_rec_acp=n_rec_acp,
            n_dis_tranche=n_dis_tranche,
            dis_tranche_k=dis_tranche_k,
            n_cascade=n_cascade,
        )
        # The discharge-tranche decomposition rides the base Dis column (which
        # keeps its exact total-discharge meaning), so it composes with the
        # energy-only measured-reservation AS path the ERCOT keeper uses. It is
        # NOT wired into the endogenous storage-AS duration gate (which gives
        # storage its own RS reserve columns): guard against that untested combo.
        if n_dis_tranche and storage_gate:
            raise ValueError(
                "ercot_storage_rt_offer_surface (discharge tranches) is not "
                "composable with the endogenous storage-AS duration gate "
                "(reserve_storage_duration_h) — the keeper's measured-reservation "
                "AS path leaves the base discharge column free to be decomposed"
            )

        # Posture U upper bound: the pool's hour-varying available capacity
        # (Σ member pmax·availability) — the RHS the joint-headroom row gives
        # up when it re-anchors to U.
        posture_ucap = None
        if standalone_posture:
            gidx_s = np.asarray(posture_gen_idx, dtype=int)
            col_s = np.asarray(posture_col, dtype=int)
            cap_s = fleet.pmax[gidx_s, np.newaxis] * fleet.availability[gidx_s]
            pool_cap_s = np.zeros((n_posture, T), dtype=float)
            np.add.at(pool_cap_s, col_s, cap_s)
            posture_ucap = pool_cap_s
        elif n_posture:
            if reserve_pergen_col_pool is not None:
                raise ValueError(
                    "reserve_posture_pools is not composable with "
                    "reserve_pergen_col_pool (the product-split pergen layout) "
                    "— the posture U re-anchor indexes pools 1:1 with R columns"
                )
            ppools = np.asarray(reserve_posture_pools, dtype=int)
            gidx_p = np.asarray(reserve_pergen_gen_idx, dtype=int)
            col_p = (
                np.arange(gidx_p.size)
                if reserve_pergen_col is None
                else np.asarray(reserve_pergen_col, dtype=int)
            )
            cap_p = fleet.pmax[gidx_p, np.newaxis] * fleet.availability[gidx_p]
            pool_cap_full = np.zeros((n_reserve, T), dtype=float)
            np.add.at(pool_cap_full, col_p, cap_p)
            posture_ucap = pool_cap_full[ppools]

        # Row-offset registry for blocks whose duals are read back after the
        # solve but which build_constraints's fixed return tuple does not name
        # (the cascade water-value duals, NWPP-36). Filled in place; empty when
        # no such block is built.
        _row_offsets: dict = {}
        (
            A,
            row_lower,
            row_upper,
            lcr_row_offset,
            n_lcr_areas,
            iface_row_offset,
            n_iface_groups,
        ) = build_constraints(
            layout,
            fleet,
            demand,
            incidence=incidence,
            storage_zone_idx=storage_zone_idx,
            eta_chg=eta_chg,
            eta_dis=eta_dis,
            rps_target=rps_target,
            rps_eligible_fuels=rps_eligible_fuels,
            rps_region_zone_mask=rps_region_zone_mask,
            rps_region_obligation_frac=rps_region_obligation_frac,
            clean_region_zone_mask=clean_region_zone_mask,
            clean_region_obligation_frac=clean_region_obligation_frac,
            clean_region_fuels=clean_region_fuels,
            hydro_monthly_energy=hydro_monthly_energy,
            hydro_month_index=hydro_month_index,
            hydro_gen_idx=hydro_gen_idx,
            hydro_monthly_min=hydro_monthly_min,
            hydro_period_hours=hydro_period_hours,
            oil_monthly_budget=oil_monthly_budget,
            oil_gen_idx=oil_gen_idx,
            oil_month_index=oil_month_index,
            oil_gen_hour_coeff=oil_gen_hour_coeff,
            oil_group_index=oil_group_index,
            coal_monthly_budget=coal_monthly_budget,
            coal_gen_idx=coal_gen_idx,
            coal_month_index=coal_month_index,
            coal_gen_hour_coeff=coal_gen_hour_coeff,
            coal_group_index=coal_group_index,
            storage_daily_cycle_hours=storage_daily_cycle_hours,
            storage_alloc_batt_idx=storage_alloc_batt_idx,
            storage_alloc_share=storage_alloc_share,
            storage_alloc_da_frac=storage_alloc_da_frac,
            interface_groups=interface_groups,
            ramp_gen_idx=ramp_gen_idx,
            ramp_group_col=ramp_group_col,
            ramp_up_mw=ramp_up_mw,
            ramp_dn_mw=ramp_dn_mw,
            local_capacity_specs=local_capacity_specs,
            hydro_envelope_gen_idx=hydro_envelope_gen_idx,
            hydro_envelope_mw=hydro_envelope_mw,
            hydro_envelope_storage_idx=hydro_envelope_storage_idx,
            import_node_gen_idx=import_node_gen_idx,
            import_node_monthly_lo=import_node_monthly_lo,
            import_node_monthly_hi=import_node_monthly_hi,
            import_node_month_index=import_node_month_index,
            mass_cap_coeffs=mass_cap_coeffs,
            mass_cap_rhs=mass_cap_rhs,
            reserve_requirement=reserve_requirement,
            reserve_eligible=reserve_eligible,
            reserve_storage_power_cap=(storage_power_cap if reserve_storage else None),
            reserve_balance_zone_mask=reserve_balance_zone_mask,
            reserve_balance_ordc_counts=reserve_balance_ordc_counts,
            reserve_balance_class=reserve_balance_class,
            reserve_online_gated=reserve_online_gated,
            reserve_online_rho=reserve_online_rho,
            reserve_headroom_eligible=reserve_headroom_eligible,
            reserve_headroom_products=reserve_headroom_products,
            reserve_headroom_extra_cap=reserve_headroom_extra_cap,
            reserve_headroom_storage=reserve_headroom_storage,
            reserve_supply_cap=reserve_supply_cap,
            reserve_online_capacity_cap=reserve_online_capacity_cap,
            reserve_storage_duration_h=(
                reserve_storage_duration_h if storage_gate else None
            ),
            reserve_pergen_gen_idx=reserve_pergen_gen_idx,
            reserve_pergen_col=reserve_pergen_col,
            reserve_posture_pools=reserve_posture_pools,
            reserve_posture_mlf=reserve_posture_mlf,
            reserve_pergen_ramp10=(
                reserve_pergen_ramp10
                if (n_posture and not standalone_posture)
                else None
            ),
            reserve_pergen_col_pool=reserve_pergen_col_pool,
            reserve_balance_col_mask=reserve_balance_col_mask,
            reserve_pergen_online_gated_cols=reserve_pergen_online_gated_cols,
            reserve_pergen_pool_ramp10=reserve_pergen_pool_ramp10,
            posture_gen_idx=(posture_gen_idx if standalone_posture else None),
            posture_col=(posture_col if standalone_posture else None),
            posture_mlf=(posture_mlf if standalone_posture else None),
            link_loss=link_loss,
            dis_tranche_arm_idx=(dis_tranche_arm_idx if dis_tranche_on else None),
            hydro_cascade=(hydro_cascade if n_cascade else None),
            row_offsets=_row_offsets,
        )
        col_lower, col_upper = build_variable_bounds(
            layout,
            fleet,
            wind_cf,
            wind_cap,
            solar_cf,
            solar_cap,
            storage_power_cap=storage_power_cap,
            storage_energy_cap=storage_energy_cap,
            storage_soc_min=storage_soc_min,
            storage_discharge_min=storage_discharge_min,
            storage_charge_cap=storage_charge_cap,
            storage_discharge_cap=storage_discharge_cap,
            ttc=ttc,
            ordc_step_widths=ordc_step_widths,
            link_bidirectional=link_bidirectional,
            reserve_pergen_ramp10=reserve_pergen_ramp10,
            ttc_import=ttc_import,
            posture_ucap=posture_ucap,
            wind_curtail_share=wind_curtail_share,
            solar_curtail_share=solar_curtail_share,
            dis_tranche_arm_idx=(dis_tranche_arm_idx if dis_tranche_on else None),
            dis_tranche_width=(dis_tranche_width if dis_tranche_on else None),
            hydro_cascade_pond_cap=(hydro_cascade.pond_cap if n_cascade else None),
        )

        _mem_debug = os.environ.get("MARKET_SIM_MEM_DEBUG") == "1"

        def _rss(label: str) -> None:
            # Peak-memory checkpoint (MARKET_SIM_MEM_DEBUG=1): the plant-level
            # ISO-year LPs run within ~1 GB of the calibration box's ceiling,
            # so locating WHICH build stage spikes is routine debugging here.
            if _mem_debug:
                with open("/proc/self/status") as f:
                    for line in f:
                        if line.startswith(("VmRSS", "VmHWM")):
                            logger.info("MEM %s: %s", label, line.split(":")[1].strip())

        _rss("after build_constraints")

        # build_constraints returns CSR -- the row-wise layout HiGHS addRows
        # consumes directly, so no format conversion is needed here. asarray
        # (not astype) so an already-int32/float64 buffer is passed through
        # without a copy — at ~150M nnz the astype copies alone were ~1.8 GB
        # of avoidable transient at the exact peak of the build.
        starts = np.asarray(A.indptr[:-1], dtype=np.int32)
        indices = np.asarray(A.indices, dtype=np.int32)
        values = np.asarray(A.data, dtype=np.float64)

        inf = highspy.kHighsInf
        # In-place inf replacement (np.where would copy each bounds array).
        col_upper[np.isinf(col_upper)] = inf
        col_lower[np.isinf(col_lower)] = -inf
        row_upper[np.isinf(row_upper)] = inf
        row_lower[np.isinf(row_lower)] = -inf
        _rss("after casts/bounds")

        h = highspy.Highs()
        h.setOptionValue("output_flag", False)
        # Memory-constrained boxes can cap HiGHS's thread count (parallel dual
        # simplex keeps per-thread factorization workspaces; on a ~12 GB
        # plant-level ISO-year LP the default all-cores run can spike past a
        # small container's RAM and get OOM-killed). Unset keeps HiGHS's
        # automatic threading; the LP optimum is identical either way.
        _threads = os.environ.get("MARKET_SIM_HIGHS_THREADS")
        if _threads:
            h.setOptionValue("threads", int(_threads))
        # Economic-dispatch LPs are already tight, and the per-hour blocks make
        # the matrix huge but trivially structured. HiGHS presolve then scales
        # with the ~1.8M column count while removing almost nothing -- on a full
        # 8760-hour model it costs ~17s of pure overhead. Skipping it lets the
        # dual simplex solve the model directly in a few seconds.
        h.setOptionValue("presolve", "off")
        if os.environ.get("MARKET_SIM_HIGHS_LEAN") == "1":
            h.setOptionValue("simplex_scale_strategy", 0)
        # Columns are added with a placeholder zero objective; the real cost
        # vector is installed per-pass in solve() via changeColsCost, which is
        # what lets a second pass warm-start from the first pass's basis.
        h.addCols(
            layout.total_columns,
            np.zeros(layout.total_columns, dtype=np.float64),
            col_lower,
            col_upper,
            0,
            np.zeros(layout.total_columns, dtype=np.int32),
            np.array([], dtype=np.int32),
            np.array([], dtype=np.float64),
        )
        _rss("after addCols")
        n_rows_A = A.shape[0]
        nnz_A = A.nnz
        if _mem_debug:
            logger.info(
                "MEM LP size: %d rows x %d cols, %d nnz (indices %s)",
                n_rows_A,
                layout.total_columns,
                nnz_A,
                indices.dtype,
            )
        # HiGHS copies the matrix internally; drop the scipy CSR shell first so
        # the peak holds one shared buffer set (starts/indices/values), not two.
        del A
        h.addRows(
            n_rows_A,
            row_lower,
            row_upper,
            nnz_A,
            starts,
            indices,
            values,
        )
        _rss("after addRows")

        self._h = h
        self.fleet = fleet
        self.layout = layout
        self.T = T
        self.n_zones = n_zones
        self.n_storage = n_storage
        self.n_links = n_links
        self.voll = voll
        # Per-zone-hour load-slack cost override (declared-window ELMP
        # emergency-tier repricing, data.maxgen_events). None -> the flat
        # ``voll`` broadcast, byte-identical. Shape-checked here so a
        # mis-oriented (T, n_zones) array fails loud, not as a silent
        # mis-priced objective.
        if slack_cost is not None:
            slack_cost = np.asarray(slack_cost, dtype=float)
            if slack_cost.shape != (n_zones, T):
                raise ValueError(
                    f"slack_cost shape {slack_cost.shape} != (n_zones, T) = "
                    f"({n_zones}, {T})"
                )
        self.slack_cost = slack_cost
        self.wind_mc = wind_mc
        self.solar_mc = solar_mc
        self.storage_discharge_eac = storage_discharge_eac
        self.storage_discharge_cost = storage_discharge_cost
        # Storage RT discharge-offer tranche pricing (ERCOT
        # ercot_storage_rt_offer_surface): the armed-battery indices and the
        # (K, T) tranche price ladder the per-solve cost vector consumes. Both
        # None off the arm (byte-identical). The (K, T) shape is checked so a
        # mis-oriented ladder fails loud, not as a silent mis-priced objective.
        if dis_tranche_on:
            price = np.asarray(dis_tranche_price, dtype=float)
            if price.shape != (dis_tranche_k, T):
                raise ValueError(
                    f"dis_tranche_price shape {price.shape} != (K, T) = "
                    f"({dis_tranche_k}, {T})"
                )
            self.dis_tranche_arm_idx = np.asarray(dis_tranche_arm_idx, dtype=int)
            self.dis_tranche_price = price
        else:
            self.dis_tranche_arm_idx = None
            self.dis_tranche_price = None
        # Overgeneration-dump guard domain (caiso-139, ScenarioConfig.
        # dump_cost_full_offer_domain; GATED default off = byte-identical).
        # When on, :meth:`solve` extends the dump price over every ``mc`` row
        # that can INJECT — the rows that could otherwise generate purely to
        # dump. Export sinks are excluded there by construction (pmax = 0), so
        # a sink's negative price, which is a willingness-to-pay on a
        # withdrawal rather than a production credit, can never inflate it.
        self.dump_cost_full_offer_domain = bool(dump_cost_full_offer_domain)
        # Per-link directed flow cost (MISO RDT TCDC tiers). A positive cost
        # on a signed bidirectional flow would CREDIT the reverse direction,
        # so nonzero entries require one-way links — fail loud, never solve a
        # credit-farming LP.
        if link_flow_cost is not None:
            lfc = np.asarray(link_flow_cost, dtype=float)
            if lfc.shape != (n_links,):
                raise ValueError(
                    f"link_flow_cost shape {lfc.shape} != (n_links={n_links},)"
                )
            nonzero = lfc != 0.0
            if nonzero.any():
                bidir = (
                    np.asarray(link_bidirectional, dtype=bool)
                    if link_bidirectional is not None
                    else np.ones(n_links, dtype=bool)
                )
                if (nonzero & bidir).any():
                    raise ValueError(
                        "link_flow_cost is nonzero on bidirectional link(s) "
                        f"{np.flatnonzero(nonzero & bidir).tolist()} — priced "
                        "flow requires one-way links (is_bidirectional=False)"
                    )
            self.link_flow_cost = lfc
        else:
            self.link_flow_cost = None
        self.rps_target = rps_target
        self.rps_acp_price = rps_acp_price
        # Per-compliance-region RPS state (FFR-7B Arm 2): the eligibility mask
        # is kept for the per-zone dual mapping in solve(); the (K,) ACP
        # vector prices the region-major ACP block. Both None on the legacy
        # single-row path.
        self._rps_region_zone_mask = (
            np.asarray(rps_region_zone_mask, dtype=bool) if rps_region_on else None
        )
        self.rps_region_acp_price = (
            np.asarray(rps_region_acp_price, dtype=float) if rps_region_on else None
        )
        self._n_rps_rows = n_rps_rows
        # Clean-tier family state (FFR-7B Arm 3): the clean ACP prices are
        # CONCATENATED after the RPS family's in the region-major ACP block,
        # matching the rows' acp_k0 = K1 slot assignment.
        self._n_clean_rows = n_clean_rows
        if clean_region_on:
            # The RPS leg of the ACP block: the K1 region escapes, the one
            # legacy-row escape, or nothing (clean family standing alone).
            if rps_region_on:
                rps_acp_leg = self.rps_region_acp_price
            elif n_rps_rows and rps_acp_price is not None:
                rps_acp_leg = np.array([float(rps_acp_price)])
            else:
                rps_acp_leg = np.zeros(0, dtype=float)
            self.rps_region_acp_price = np.concatenate(
                [rps_acp_leg, np.asarray(clean_region_acp_price, dtype=float)]
            )
        self._lcr_row_offset = lcr_row_offset
        self._n_lcr_areas = n_lcr_areas
        self._lcr_gen_idx = (
            [np.asarray(s[0], dtype=int) for s in local_capacity_specs]
            if local_capacity_specs and n_lcr_areas > 0
            else []
        )
        # Aggregate-interface (flow-group) reporting state — the network
        # sidecar's inputs. Membership/signs identify each group's links; the
        # per-hour row bounds are sliced out of the assembled bound vectors
        # ONCE here, before they are handed to HiGHS, so the post-solve
        # extraction never has to re-derive a cap. Pure bookkeeping: nothing
        # below is read by the matrix build or by HiGHS.
        self._iface_row_offset = iface_row_offset
        self._n_iface_groups = n_iface_groups
        # Cascade rows (NWPP-36): where the water-balance block sits so its
        # duals (the marginal water value per coupled plant-hour) can be read
        # back; (-1, 0) when the family is off. The spec is kept for labelling.
        self._cascade_row_offset, self._n_cascade_rows = _row_offsets.get(
            "hydro_cascade", (-1, 0)
        )
        self._hydro_cascade = hydro_cascade if n_cascade else None
        self._iface_link_idx: list[np.ndarray] = []
        self._iface_signs: list[np.ndarray] = []
        self._iface_cap_up: np.ndarray | None = None
        self._iface_cap_dn: np.ndarray | None = None
        if interface_groups and n_iface_groups > 0 and iface_row_offset >= 0:
            for grp in interface_groups:
                idx = np.asarray(grp[0], dtype=int)
                self._iface_link_idx.append(idx)
                sgn = grp[4] if len(grp) > 4 else None
                self._iface_signs.append(
                    np.ones(idx.size)
                    if sgn is None
                    else np.asarray(sgn, dtype=float)[: idx.size]
                )
            # Rows are hour-major, group-minor (the _build_interface_rows kron
            # order), so a (T, n_groups) reshape transposes to (n_groups, T).
            n_i = n_iface_groups * self.T
            self._iface_cap_up = (
                row_upper[iface_row_offset : iface_row_offset + n_i]
                .reshape(self.T, n_iface_groups)
                .T.copy()
            )
            self._iface_cap_dn = (
                row_lower[iface_row_offset : iface_row_offset + n_i]
                .reshape(self.T, n_iface_groups)
                .T.copy()
            )
        # The flow columns' own bounds (the per-link TTC the LP saw, hourly
        # where an overlay made it hourly) — the third candidate limit in the
        # network sidecar's attribution, alongside each interface group.
        self._flow_cap_up: np.ndarray | None = None
        self._flow_cap_dn: np.ndarray | None = None
        if n_links:
            self._flow_cap_up = (
                col_upper.reshape(T, layout.vars_per_hour)[
                    :, layout._flow_off : layout._slack_off
                ]
                .T.copy()
                .astype(np.float32)
            )
            self._flow_cap_dn = (
                col_lower.reshape(T, layout.vars_per_hour)[
                    :, layout._flow_off : layout._slack_off
                ]
                .T.copy()
                .astype(np.float32)
            )
        # Emissions mass-cap rows: k inequality rows appended after import-node
        # rows and before RPS (plan §4). Their duals (negated) are the endogenous
        # allowance prices, recovered end-anchored in solve().
        if mass_cap_coeffs is not None and np.asarray(mass_cap_coeffs).size:
            self._n_masscap_rows = int(np.asarray(mass_cap_coeffs).shape[0])
        else:
            self._n_masscap_rows = 0
        self.mass_cap_labels = mass_cap_labels
        # Co-opt state for re-costing and dual extraction.
        self._coopt = coopt
        self.ordc_penalties = ordc_penalties
        # Reserve block = shared-headroom rows (n_headroom_rows*n_zones*T) +
        # reserve-balance rows (n_families*T), appended last; the balance rows
        # are the final n_families*T (family-major within each hour). The
        # headroom-row count equals the reserve-class count for the legacy /
        # NYISO per-class layout and the additive-spec row count for ERCOT
        # multi-product.
        self._n_families = n_families
        # ORDC shortfall steps owned by each family, in the family-major order
        # ``_build_reserve_rows`` partitions the ORDC block with (family f owns
        # the next ``counts[f]`` columns of ``[_ordc_off, _ordc_off+n_steps)``).
        # Kept so ``solve()`` can report each family's own cleared shortfall MW
        # alongside its balance dual — the per-family reserve sidecar
        # (``hourly/reserve_family_<year>.parquet``). ``None`` = the legacy
        # single-family layout, where every step belongs to family 0.
        self._reserve_ordc_counts: np.ndarray | None = (
            None
            if reserve_balance_ordc_counts is None
            else np.asarray(reserve_balance_ordc_counts, dtype=int).ravel()
        )
        # Reserve-supply cap (ERCOT RTOLCAP re-scope) inserts one system-wide row
        # per headroom tier per hour, between the headroom and balance blocks
        # (so the balance dual stays the final n_families*T rows).
        n_supply_cap_rows = (
            n_headroom_rows * T if (coopt and reserve_supply_cap is not None) else 0
        )
        # On-line-capacity envelope (ERCOT G-22): one system-wide row per headroom
        # tier per hour, inserted after the supply-cap block and before balance
        # (so the balance dual stays the final n_families*T rows).
        n_online_cap_rows = (
            n_headroom_rows * T
            if (coopt and reserve_online_capacity_cap is not None)
            else 0
        )
        # Storage duration-gate rows: a per-zone power-competition row + a
        # per-zone SOC duration-gate row per hour (2 * n_zones * T), inserted
        # between the supply-cap and balance blocks (balance stays final).
        n_storage_gate_rows = 2 * n_zones * T if storage_gate else 0
        # Stash the tail-block row counts (zonal spec only — pergen has no
        # supply-cap block) so solve() can recover the supply-cap duals
        # end-anchored: [.. | supply_cap | online_cap | storage_gate | balance].
        self._n_supply_cap_rows = 0 if pergen else n_supply_cap_rows
        self._n_online_cap_rows = 0 if pergen else n_online_cap_rows
        self._n_storage_gate_rows_zonal = 0 if pergen else n_storage_gate_rows
        self._n_headroom_tiers = n_headroom_rows
        # Per-gen spec: joint P+R rows (n_reserve*T) + balance rows
        # (n_families*T); the balance rows stay the final n_families*T either
        # way, so the dual extraction below is layout-independent.
        if pergen:
            # Posture families (min-load q_mlf·T + startup q·T + ramp gate
            # q·T) sit between the joint and balance blocks; the storage
            # duration-gate rows (issue #1492 pergen storage AS) between the
            # posture and balance blocks; the balance rows stay the final
            # n_families*T either way.
            n_posture_rows = 0
            if n_posture:
                q_mlf = int(
                    np.count_nonzero(np.asarray(reserve_posture_mlf, dtype=float) > 0.0)
                )
                n_posture_rows = (q_mlf + 2 * n_posture) * T
            # Joint-headroom rows are per POOL (the product split maps several
            # R columns onto one pool row; identity otherwise). The online-
            # gated coupling rows (one per gated R column per hour) and the
            # shared product-ramp rows (one per pool per hour) sit between
            # the storage-gate and balance blocks (miso_reserve_online_gated;
            # both zero on every flag-off path).
            n_online_gate_rows = (
                int(
                    np.count_nonzero(
                        np.asarray(reserve_pergen_online_gated_cols, dtype=bool)
                    )
                )
                * T
                if reserve_pergen_online_gated_cols is not None
                else 0
            )
            n_shared_ramp_rows = (
                n_pergen_pools * T if reserve_pergen_pool_ramp10 is not None else 0
            )
            self._n_reserve_rows = (
                n_pergen_pools * T
                + n_posture_rows
                + n_storage_gate_rows
                + n_online_gate_rows
                + n_shared_ramp_rows
                + n_families * T
            )
        else:
            self._n_reserve_rows = (
                (
                    n_headroom_rows * n_zones * T
                    + n_supply_cap_rows
                    + n_online_cap_rows
                    + n_storage_gate_rows
                    + n_families * T
                )
                if coopt
                else 0
            )
        # Zone-incidence map for aggregating per-gen reserve columns back to
        # (n_zones, T) in solve() — every downstream consumer of
        # reserve_dispatch reads the zonal block shape.
        self._pergen = pergen
        if pergen:
            gidx = np.asarray(reserve_pergen_gen_idx, dtype=int)
            col = (
                np.arange(gidx.size)
                if reserve_pergen_col is None
                else np.asarray(reserve_pergen_col, dtype=int)
            )
            # Column zone: with the product split, pergen_col maps members to
            # POOLS and each R column inherits its pool's zone; identity map
            # (columns ≡ pools) otherwise.
            pool_zone = np.zeros(n_pergen_pools, dtype=int)
            pool_zone[col] = np.asarray(fleet.zone_idx, dtype=int)[gidx]
            if reserve_pergen_col_pool is not None:
                r_zone = pool_zone[np.asarray(reserve_pergen_col_pool, dtype=int)]
            else:
                r_zone = pool_zone
            self._pergen_zone_map = sp.csr_matrix(
                (np.ones(n_reserve), (r_zone, np.arange(n_reserve))),
                shape=(n_zones, n_reserve),
            )
        # Commitment-posture state: startup costs for the per-solve cost
        # vector, and the postured pools' (zone, fuel) identity so the
        # posture frame can label its rows without re-deriving the pooling.
        self._standalone_posture = standalone_posture
        if not n_posture:
            self._posture_startup = None
            self._posture_pools = None
            self.posture_zone_idx = None
            self.posture_fuel_idx = None
        elif standalone_posture:
            # Standalone (ERCOT) posture: pools are 0..q-1, labelled directly
            # from the member (zone, fuel) via the capacity-weighted plurality
            # (a pool is a single (zone, fuel-class) group by construction).
            self._posture_startup = np.asarray(posture_startup, dtype=float)
            self._posture_pools = np.arange(n_posture, dtype=int)
            gidx_l = np.asarray(posture_gen_idx, dtype=int)
            col_l = np.asarray(posture_col, dtype=int)
            pzone = np.zeros(n_posture, dtype=int)
            pfuel = np.zeros(n_posture, dtype=int)
            pzone[col_l] = np.asarray(fleet.zone_idx, dtype=int)[gidx_l]
            pfuel[col_l] = np.asarray(fleet.fuel_type_idx, dtype=int)[gidx_l]
            self.posture_zone_idx = pzone
            self.posture_fuel_idx = pfuel
        else:
            self._posture_startup = np.asarray(reserve_posture_startup, dtype=float)
            self._posture_pools = np.asarray(reserve_posture_pools, dtype=int)
            r_fuel = np.zeros(n_reserve, dtype=int)
            r_fuel[col] = np.asarray(fleet.fuel_type_idx, dtype=int)[gidx]
            self.posture_zone_idx = r_zone[self._posture_pools]
            self.posture_fuel_idx = r_fuel[self._posture_pools]
        # Index vector for changeColsCost. highspy exposes only the SET form
        # (num, int32 indices, float64 costs) -- there is no range variant --
        # so this array is required on every pass, but NOT during h.run().
        # It is therefore released across the solve peak and rebuilt lazily
        # (np.arange is ~0.05 s against 118 MB held on the 29.6M-column MISO
        # LP). ``None`` here means 'not currently materialised', never 'absent'.
        self._all_cols: np.ndarray | None = np.arange(
            layout.total_columns, dtype=np.int32
        )
        # Row-layout metadata for cross-year basis transfer (export/apply_cross_
        # year_basis). Generator add/retire changes only columns -- capacity is a
        # column bound and generation enters the energy balance via coefficients,
        # not new rows -- so the energy-balance rows (n_zones*T, hour-major) and
        # the storage SOC rows (n_storage*T, unit-major) are the two dimensionally
        # well-defined blocks a prior year's basis maps onto.
        self._n_rows = n_rows_A
        self._n_energy_rows = n_zones * T
        self._n_storage_rows = n_storage * T
        self.build_time = time.perf_counter() - build_start
        self._n_solves = 0

    def solve(
        self,
        mc: np.ndarray | None = None,
        fuel_prices: np.ndarray | None = None,
        carbon_price: "np.ndarray | float" = 0,
        nox_price: "np.ndarray | float" = 0,
        so2_price: "np.ndarray | float" = 0,
    ) -> "DispatchResult":
        """Install a marginal-cost vector and (re-)solve the LP.

        The first call solves cold; subsequent calls change only the objective
        coefficients and warm-start from the prior optimal basis.

        Args:
            mc: Marginal cost array of shape ``(n_gen, T)``. When ``None`` it is
                assembled from ``fuel_prices``, ``carbon_price``, ``nox_price``
                and ``so2_price``.
            fuel_prices: Fuel prices passed to ``assemble_mc`` when ``mc`` is
                ``None``.
            carbon_price: Carbon price used when ``mc`` is ``None``.
            nox_price: NOx price used when ``mc`` is ``None``.
            so2_price: SO2 price used when ``mc`` is ``None``.

        Returns:
            A populated :class:`DispatchResult`.

        Raises:
            RuntimeError: When HiGHS does not return a feasible primal solution.
        """
        # Lazy import: DispatchResult is defined physically in lp/__init__
        # (pickle identity, plan §1); a module-level import back into the
        # package would be a module-level import cycle.
        from market_sim.model.lp import DispatchResult

        layout = self.layout
        if mc is None:
            mc = assemble_mc(
                self.fleet,
                fuel_prices,
                carbon_price,
                nox_price,
                so2=(self.fleet.so2_rate, so2_price),
            )
        mc = np.asarray(mc, dtype=float)

        # Dump-guard domain (caiso-139). The per-row minimum over the hours is
        # taken with a single vectorized reduction (rule 2 [R-VECTOR]: no hour
        # loop, and no (n_gen, T) temporary), then masked to the rows that can
        # inject. ``pmax <= 0`` rows are the export sinks
        # (interchange.import_nodes.build_export_sinks: pmax 0, pmin -cap) —
        # they absorb, so their negative price is not a production credit and
        # must stay outside the guard.
        min_injectable_mc = None
        if self.dump_cost_full_offer_domain:
            injectable = np.asarray(self.fleet.pmax, dtype=float) > 0.0
            if injectable.any():
                min_injectable_mc = float(mc.min(axis=1)[injectable].min())

        cost = build_cost_vector(
            layout,
            mc,
            self.voll,
            wind_mc=self.wind_mc,
            solar_mc=self.solar_mc,
            storage_discharge_eac=self.storage_discharge_eac,
            storage_discharge_cost=self.storage_discharge_cost,
            ordc_penalties=self.ordc_penalties,
            posture_startup_cost=self._posture_startup,
            rps_acp_price=(
                self.rps_region_acp_price
                if self.rps_region_acp_price is not None
                else (self.rps_acp_price or 0.0)
            ),
            link_flow_cost=self.link_flow_cost,
            slack_cost=self.slack_cost,
            min_injectable_mc=min_injectable_mc,
            dis_tranche_arm_idx=self.dis_tranche_arm_idx,
            dis_tranche_price=self.dis_tranche_price,
        )

        h = self._h
        if self._all_cols is None:
            self._all_cols = np.arange(layout.total_columns, dtype=np.int32)
        h.changeColsCost(layout.total_columns, self._all_cols, cost)

        # Drop the two largest Python-side transients before the solve. HiGHS
        # has already COPIED the cost vector into its own colCost_ by the time
        # changeColsCost returns, and neither name is read again anywhere after
        # h.run() (the objective is rebuilt from scratch on the next pass), so
        # this is a pure lifetime fix: the LP, its optimum and every extracted
        # dual are bit-identical.
        #
        # WHY IT MATTERS, measured (miso-253): the solve+extraction phase is the
        # owner of the year-solve peak, and on the plant-level MISO LP that peak
        # is 13.30 GiB against a 13.344 GiB container ceiling -- a 0.4 % margin
        # that OOM-kills the run intermittently. ``cost`` alone is
        # ``layout.total_columns`` float64 = 237 MB on that LP (29,643,840
        # columns), and ``mc`` is a further (n_gen, T) block; together they are
        # ~450 MB of the peak, roughly 8x the margin that was missing. Holding
        # them across run() bought nothing.
        #
        # ``mc`` IS read once more after the solve — it populates
        # ``DispatchResult.gen_mc`` as a float32 COPY. Making that copy here
        # instead of after run() releases the float64 original across the peak
        # and keeps only the half-width array the result actually stores; the
        # value is identical either way because nothing mutates ``mc`` in
        # between, and asarray-with-a-dtype-change still copies, so the
        # no-aliasing guarantee the extraction comment relies on is preserved.
        #
        # ``mc`` may be a caller-owned array (the ``mc=`` argument); deleting the
        # local name only drops THIS reference and never mutates it, so a caller
        # reusing its own array across passes is unaffected.
        gen_mc_f32 = np.asarray(mc, dtype=np.float32)
        del cost
        del mc
        # Same reasoning for the column-index vector: HiGHS has consumed it,
        # and the next pass rebuilds it for ~0.05 s. 118 MB on the MISO LP.
        self._all_cols = None

        solve_start = time.perf_counter()
        h.run()
        solve_time = time.perf_counter() - solve_start
        warm = self._n_solves > 0
        self._n_solves += 1

        # Simplex iteration count read back from HighsInfo — a diagnostic
        # read after ``h.run()``, so it cannot touch the solve; it is what
        # the warm-start-class evidence tables (cross-year warm start, the
        # same-year P1 basis seed) report beside the seconds.
        try:
            _iters = int(h.getInfo().simplex_iteration_count)
            _obj = float(h.getObjectiveValue())
        except Exception:  # pragma: no cover - a log line may never break a solve
            _iters, _obj = -1, float("nan")
        logger.info(
            f"Matrix build: {self.build_time:.3f}s, "
            f"Solve: {solve_time:.3f}s ({'warm' if warm else 'cold'}, "
            f"simplex iterations {_iters}, objective {_obj:.4f})"
        )

        _, primal_status = h.getInfoValue("primal_solution_status")
        if primal_status != 2:
            status = h.modelStatusToString(h.getModelStatus())
            raise RuntimeError(
                f"dispatch LP has no feasible primal solution (status: {status})"
            )

        T = self.T
        n_zones = self.n_zones
        n_storage = self.n_storage
        n_links = self.n_links

        # --- Solution marshalling: one up-front block, largest transient
        # first. highspy 1.14 returns the HighsSolution by VALUE (a C++-side
        # copy of all four vectors, ~0.4 GB at plant-level MISO scale) and
        # converts a vector attribute to a boxed-float Python list on EVERY
        # access (~0.8 GB per access at ~25M columns) — transients that stack
        # directly on the live simplex workspace, the top of the measured
        # 14.4 GB year-solve peak (miso-169 attribution; G-40 lineage). So:
        # convert each needed vector exactly once, do the two column-length
        # conversions while nothing else from the solution is yet retained,
        # and drop the C++ copy before the rest of the extraction runs. This
        # is a pure reordering of the same reads — every downstream value is
        # bit-identical.
        _log_rss("post-run pre-extraction")
        solution = h.getSolution()
        # Flow AND generation reduced costs: highspy 1.14 has no partial
        # accessor, so the full col_dual converts, but only the (n_links, T)
        # flow block and the (n_gen, T) generation block are retained (the
        # network / unit_hourly sidecars' inputs; see the stationarity notes
        # further down and in DispatchResult where each is consumed). The
        # generation block is kept float32 — the same precision the retained
        # ``_flow_cap_*`` bounds use, and 1e-7 relative on a $/MWh reduced
        # cost is four orders below the smallest charge any diagnostic reads —
        # because it is the larger of the two by the gen:link ratio (a
        # plant-level MISO year is 2.8k gens against ~30 links, so float64
        # would retain ~200 MB against a documented 14.4 GB year peak).
        flow_dual = None
        gen_reduced_cost = None
        if n_links or layout.n_gen:
            col_dual = np.asarray(solution.col_dual, dtype=float)
            _cd_block = col_dual.reshape(T, layout.vars_per_hour)
            if n_links:
                flow_dual = _cd_block[:, layout._flow_off : layout._slack_off].T.copy()
            if layout.n_gen:
                gen_reduced_cost = (
                    _cd_block[:, layout._p_off : layout._w_off]
                    .T.copy()
                    .astype(np.float32)
                )
            del col_dual, _cd_block
            _log_rss("post col_dual extraction")
        # Reserve balance-row ACTIVITY (Ax), co-opt only: the final
        # n_families*T entries of row_value — the only output that needs the
        # row-activity vector (consumed by the per-family reserve sidecar
        # extraction below, where its role is documented).
        balance_activity = None
        if self._coopt:
            balance_activity = np.asarray(
                solution.row_value[-(self._n_families * T) :], dtype=float
            ).reshape(T, self._n_families)
        col_value = np.asarray(solution.col_value, dtype=float)
        row_dual = np.asarray(solution.row_dual, dtype=float)
        del solution
        _log_rss("post extraction")

        block = col_value.reshape(T, layout.vars_per_hour)
        dispatch = block[:, layout._p_off : layout._w_off].T
        wind_dispatched = block[:, layout._w_off : layout._s_off].T
        solar_dispatched = block[:, layout._s_off : layout._chg_off].T
        slack = block[:, layout._slack_off : layout._dump_off].T
        # Dump is the dump block only; with co-opt off _reserve_off == vph.
        dump = block[:, layout._dump_off : layout._reserve_off].T

        storage_charge = storage_discharge = storage_soc = None
        if n_storage:
            storage_charge = block[:, layout._chg_off : layout._dis_off].T
            storage_discharge = block[:, layout._dis_off : layout._soc_off].T
            storage_soc = block[:, layout._soc_off : layout._flow_off].T

        flows = None
        if n_links:
            flows = block[:, layout._flow_off : layout._slack_off].T

        # Energy-balance duals occupy the first n_zones * T rows, hour-major;
        # for a minimization the equality dual is the zonal price (no negation).
        prices = row_dual[: n_zones * T].reshape(T, n_zones).T

        # The RPS row family, when present, is appended after the energy/
        # storage/hydro/mass-cap rows; the reserve block (when on) is appended
        # *after* it, so index from the end past the reserve tail. Legacy
        # single row: scalar dual — THE REC price. Per-compliance-region grain
        # (FFR-7B Arm 2): a K-slice at the same end anchor — region r's dual
        # is compliance market r's REC price (MIRECS Michigan RECs and M-RETS
        # Iowa RECs are different products at different prices, FFR-6B §3.2) —
        # reported BOTH as the raw per-region vector (``rps_region_duals``,
        # diagnostics) and as the per-zone consumer vector
        # ``p[z] = max{dual_r : z in eligible_zones(r)}`` (0 where no region's
        # certificate can be generated in z), which is what the capacity
        # screens index by a candidate's/unit's zone.
        rps_shadow_price = None
        rps_region_duals = None
        clean_region_duals = None
        if self._n_rps_rows:
            rps_start = row_dual.size - (
                self._n_reserve_rows + self._n_clean_rows + self._n_rps_rows
            )
            rps_duals = row_dual[rps_start : rps_start + self._n_rps_rows]
            if self._rps_region_zone_mask is None:
                rps_shadow_price = float(rps_duals[0])
            else:
                rps_region_duals = np.asarray(rps_duals, dtype=float).copy()
                rps_shadow_price = np.where(
                    self._rps_region_zone_mask, rps_region_duals[:, None], 0.0
                ).max(axis=0)
        # Clean-tier family duals (FFR-7B Arm 3): the K2 rows directly after
        # the RPS family — each dual is that state's clean/carbon-free
        # attribute price, capped at its own escape. Exposed RAW; the
        # per-(fuel, zone) consumer mapping happens at the runner
        # (policy.clean_tiers.clean_credit_by_fuel), because it needs the
        # per-region qualifying sets the LP deliberately does not keep.
        if self._n_clean_rows:
            clean_start = row_dual.size - (self._n_reserve_rows + self._n_clean_rows)
            clean_region_duals = np.asarray(
                row_dual[clean_start : clean_start + self._n_clean_rows],
                dtype=float,
            ).copy()

        # Emissions mass-cap duals sit before the RPS/clean families and after
        # the import-node rows:
        # [ ... | mass_cap (k) | rps (0..K1) | clean (0..K2) | reserve (n) ].
        # Recover them end-anchored past the reserve/clean/RPS tails. HiGHS min
        # problem, <= row → dual <= 0; the reported allowance price is -λ >= 0.
        co2_cap_price = None
        if self._n_masscap_rows:
            start = row_dual.size - (
                self._n_reserve_rows
                + self._n_clean_rows
                + self._n_rps_rows
                + self._n_masscap_rows
            )
            mass_duals = row_dual[start : start + self._n_masscap_rows]
            co2_cap_price = [float(-d) for d in mass_duals]

        # Energy+reserve co-optimization outputs. Reserve dispatch is the
        # per-zone R_z block (n_zones, T); the reserve clearing price is the dual
        # of the reserve-balance rows (the final T rows), which the per-zone
        # shared-headroom constraint transfers into each zone's energy LMP above.
        reserve_dispatch = reserve_price = reserve_price_by_family = None
        reserve_supply_cap_dual = None
        reserve_shortfall_by_family = reserve_held_by_family = None
        if self._coopt:
            reserve_dispatch = block[:, layout._reserve_off : layout._ordc_off].T
            if self._pergen:
                # Aggregate the per-gen R columns to the zonal block shape
                # every downstream consumer expects ((n_zones, T)).
                reserve_dispatch = self._pergen_zone_map @ reserve_dispatch
            # Balance rows are the final n_families*T, family-major per hour.
            # Report the per-hour SUM across families as the (T,) reserve price:
            # for a single system family this is exactly the legacy balance dual;
            # for NYISO's nested families it is the total stacked reserve shadow
            # price (the locational per-zone components are already folded into
            # each zone's energy LMP via the shared-headroom dual).
            n_fam = self._n_families
            balance_duals = row_dual[-(n_fam * T) :].reshape(T, n_fam)
            reserve_price = balance_duals.sum(axis=1)
            # Per-product (per-family) reserve clearing price, (T, n_fam). For
            # ERCOT's multi-product co-opt each family is one AS product, so the
            # per-hour MAX across columns is the binding-product MCPC the measured
            # DAM-AS overlay reads — recovered here from the LP balance-row duals,
            # never an exogenous adder.
            reserve_price_by_family = balance_duals
            # Per-family cleared ORDC SHORTFALL MW, (T, n_fam). The ORDC block
            # is family-major — family f owns the next ``counts[f]`` columns of
            # ``[_ordc_off, _ordc_off + n_ordc_steps)`` (_build_reserve_rows) —
            # so a family's shortfall is the sum of its own steps. This is what
            # makes a family's balance dual READABLE: a positive dual with zero
            # shortfall is a family binding on the requirement itself, while a
            # positive shortfall names the ORDC step that set the price. Persisted
            # with the dual in ``hourly/reserve_family_<year>.parquet`` — without
            # it the sidecar cannot distinguish the two (nyiso-113 §8).
            if layout.n_ordc_steps:
                ordc_block = block[
                    :, layout._ordc_off : layout._ordc_off + layout.n_ordc_steps
                ]
                counts = self._reserve_ordc_counts
                if counts is None:
                    counts = np.array([layout.n_ordc_steps], dtype=int)
                # (n_steps, n_fam) 0/1 membership, so the partition sum is one
                # matmul. Preferred over np.add.reduceat because a family with
                # ZERO ORDC steps (legal — a family may carry no shortfall
                # curve) collides its reduceat boundary with its neighbour's;
                # the membership matrix gives it an all-zero column instead.
                fam_of_step = np.repeat(
                    np.arange(counts.size), np.asarray(counts, dtype=int)
                )
                membership = np.zeros((layout.n_ordc_steps, n_fam), dtype=float)
                membership[np.arange(fam_of_step.size), fam_of_step] = 1.0
                reserve_shortfall_by_family = ordc_block @ membership
            else:
                reserve_shortfall_by_family = np.zeros((T, n_fam), dtype=float)
            # Per-family HELD reserve MW, (T, n_fam) — the row's reserve-column
            # activity. Taken as (balance-row activity − shortfall) rather than
            # by re-summing R columns per family, because that re-sum would have
            # to re-derive the row's own coefficient structure (per-class blocks,
            # storage RS columns, per-generator columns with a product mask, and
            # the ERCOT all-class family that draws on every class) — five
            # layouts, each a chance to attribute one family's MW to another.
            # The row activity is exactly Σ_{z∈f} R + Σ_{k∈f} ORDC by
            # construction, so this is layout-independent and exact. Persisting
            # it is what makes the family row READABLE from a bundle: the
            # inequality `held + shortfall ≥ requirement` is checkable, and its
            # slack says how far a non-binding family was from binding — which
            # ``reserve_dispatch`` cannot answer, being itself discarded at
            # persist time and having no family index.
            # Row ACTIVITY (Ax) — the only output that needs it, converted
            # once in the up-front marshalling block (an energy-only LP pays
            # nothing: the conversion is gated on the same self._coopt).
            reserve_held_by_family = balance_activity - reserve_shortfall_by_family
            # Reserve-supply cap duals (zonal spec): the cap block sits directly
            # before [online_cap | storage_gate | balance] at the row tail, one
            # system-wide <= row per headroom tier per hour (hour-major). A
            # binding <= row in a HiGHS min problem carries a non-positive dual;
            # flip sign so the reported series is the >= 0 uninternalized
            # reserve scarcity price (see DispatchResult docstring).
            if self._n_supply_cap_rows:
                tail = (
                    self._n_families * T
                    + self._n_storage_gate_rows_zonal
                    + self._n_online_cap_rows
                )
                cap_d = row_dual[-(tail + self._n_supply_cap_rows) : -tail]
                n_hr_tiers = self._n_headroom_tiers
                reserve_supply_cap_dual = np.maximum(
                    0.0, -cap_d.reshape(T, n_hr_tiers).T
                )

        # Duration-gated storage AS (ercot_storage_as_duration_gate): the RS[c,z]
        # columns (after the ORDC block) summed across AS products -> (n_zones, T)
        # cleared storage AS. This is the EXACT split (storage's own reserve
        # variable), unlike the storage_reserve_mw min() attribution used when
        # storage is pooled in the shared headroom.
        storage_reserve_dispatch = None
        if self._coopt and layout.n_storage_reserve > 0:
            sr0 = layout._storage_reserve_off
            sr = block[:, sr0 : sr0 + layout.n_storage_reserve].T  # (n_sr, T)
            storage_reserve_dispatch = sr.reshape(
                layout.n_reserve_classes, n_zones, T
            ).sum(axis=0)

        # Commitment-posture outputs: pool online capacity U, startups SU,
        # and the postured pools' own cleared reserve (pre-zone-aggregation R
        # columns) — the honesty-gate series (design note §A).
        posture_online = posture_startup = posture_reserve = None
        if layout.n_posture > 0:
            u0 = layout._posture_u_off
            posture_online = block[:, u0 : u0 + layout.n_posture].T
            su0 = layout._posture_su_off
            posture_startup = block[:, su0 : su0 + layout.n_posture].T
            if not self._standalone_posture:
                # Pergen posture: the postured pools' own cleared reserve
                # (pre-zone-aggregation R columns). The standalone (ERCOT)
                # posture carries no reserve coupling, so there is none.
                r_all = block[:, layout._reserve_off : layout._ordc_off].T
                posture_reserve = r_all[self._posture_pools]

        # LCR-area duals: the >= row dual is non-negative (HiGHS min, >= row);
        # it represents the per-MWh uplift value of local committed generation
        # (the BCR/CPM analogue). Reshaped to (n_areas, T), hour-major layout.
        lcr_dual = None
        lcr_gen_idx_out = None
        if self._n_lcr_areas > 0 and self._lcr_row_offset >= 0:
            n_a = self._n_lcr_areas
            off = self._lcr_row_offset
            lcr_dual = row_dual[off : off + n_a * T].reshape(T, n_a).T
            lcr_gen_idx_out = self._lcr_gen_idx

        # Network duals (the ``network_<year>.parquet`` sidecar's inputs): the
        # aggregate-interface row duals and the flow columns' reduced costs.
        # Together with the zonal prices already extracted above they close the
        # LP's own flow-column stationarity identity, which is what makes a
        # binding transmission limit ATTRIBUTABLE without a replay:
        #
        #     lambda_to - lambda_from = -z_link - sum_g s_(g,link) * y_g
        #
        # (``z`` the flow column's reduced cost, ``y_g`` the group row's dual,
        # ``s`` the group's signed membership). Each term on the right is >= 0
        # in the import direction and is exactly the rent charged by ONE limit:
        # the link's own TTC bound, or each interface group it belongs to.
        # Signs are HiGHS-raw and deliberately NOT normalised here (a two-sided
        # group row binds up or down and the reader needs to know which) --
        # ``run_calibration_full._network_frame`` records them verbatim.
        # Read-only post-solve extraction; nothing here re-enters the model.
        # (``flow_dual`` itself was sliced out of col_dual in the up-front
        # marshalling block, before the primal column block was retained.)
        interface_dual = None
        if self._n_iface_groups > 0 and self._iface_row_offset >= 0:
            n_g = self._n_iface_groups
            off_i = self._iface_row_offset
            interface_dual = row_dual[off_i : off_i + n_g * T].reshape(T, n_g).T

        # Hydraulic-cascade diagnostics (NWPP-36): the spill and pond-volume
        # columns per coupled plant, and the water-balance row duals (the
        # marginal water value at each coupled plant-hour, $/kcfs·h). Rows are
        # laid out c-major (r = c*T + t), the columns hour-major. Read-only
        # extraction; None off the arm.
        cascade_spill = cascade_storage = cascade_water_value = None
        cascade_plant_codes = None
        if layout.n_cascade:
            n_c = layout.n_cascade // 2
            s0 = layout._cas_s_off
            v0 = layout._cas_v_off
            cascade_spill = block[:, s0 : s0 + n_c].T
            cascade_storage = block[:, v0 : v0 + n_c].T
            if self._n_cascade_rows and self._cascade_row_offset >= 0:
                off_c = self._cascade_row_offset
                cascade_water_value = row_dual[
                    off_c : off_c + self._n_cascade_rows
                ].reshape(n_c, T)
            if self._hydro_cascade is not None:
                cascade_plant_codes = np.asarray(
                    self._hydro_cascade.plant_codes, dtype=int
                )

        # Read the objective and the model status BEFORE the emissions
        # re-pricing below. That re-pricing leaves the CO2 rates installed as
        # the objective and ends on a deliberate zero-iteration ``run()``, so
        # afterwards ``getObjectiveValue()`` reports the CO2 total and
        # ``getModelStatus()`` reports ``kIterationLimit`` -- neither of which
        # is this solve's answer. The next pass reinstalls the real cost vector
        # (``changeColsCost`` runs on every pass), and everything else returned
        # here is already extracted, so these two reads are the only ones that
        # have to happen first.
        objective_value = h.getObjectiveValue()
        status = h.modelStatusToString(h.getModelStatus())
        marginal_emission_rate = self._marginal_emission_rate(n_zones, T)

        return DispatchResult(
            dispatch=dispatch,
            wind_dispatched=wind_dispatched,
            solar_dispatched=solar_dispatched,
            slack=slack,
            dump=dump,
            prices=prices,
            marginal_emission_rate=marginal_emission_rate,
            storage_charge=storage_charge,
            storage_discharge=storage_discharge,
            storage_soc=storage_soc,
            flows=flows,
            objective_value=objective_value,
            status=status,
            reserve_dispatch=reserve_dispatch,
            reserve_price=reserve_price,
            reserve_price_by_family=reserve_price_by_family,
            reserve_shortfall_by_family=reserve_shortfall_by_family,
            reserve_held_by_family=reserve_held_by_family,
            reserve_supply_cap_dual=reserve_supply_cap_dual,
            storage_reserve_dispatch=storage_reserve_dispatch,
            posture_online_mw=posture_online,
            posture_startup_mw=posture_startup,
            posture_reserve_mw=posture_reserve,
            posture_zone_idx=self.posture_zone_idx,
            posture_fuel_idx=self.posture_fuel_idx,
            build_time=self.build_time,
            solve_time=solve_time,
            rps_shadow_price=rps_shadow_price,
            rps_region_duals=rps_region_duals,
            clean_region_duals=clean_region_duals,
            co2_cap_price=co2_cap_price,
            lcr_dual=lcr_dual,
            lcr_gen_idx=lcr_gen_idx_out,
            interface_dual=interface_dual,
            interface_link_idx=(self._iface_link_idx or None),
            interface_signs=(self._iface_signs or None),
            interface_cap_up=self._iface_cap_up,
            interface_cap_dn=self._iface_cap_dn,
            flow_dual=flow_dual,
            flow_cap_up=self._flow_cap_up,
            flow_cap_dn=self._flow_cap_dn,
            # The offer array THIS solve installed — the LP's own marginal
            # cost, so a diagnostic never has to rebuild it from the fleet/fuel
            # path and can never disagree with what cleared. float32 for the
            # same reason as ``gen_reduced_cost``, and as a COPY rather than a
            # reference so the result can never alias (and be mutated through)
            # the caller's objective array.
            gen_mc=gen_mc_f32,
            gen_reduced_cost=gen_reduced_cost,
            hydro_cascade_spill=cascade_spill,
            hydro_cascade_storage=cascade_storage,
            hydro_cascade_water_value=cascade_water_value,
            hydro_cascade_plant_codes=cascade_plant_codes,
        )

    def _marginal_emission_rate(self, n_zones: int, T: int) -> "np.ndarray | None":
        """Return ``(n_zones, T)`` dCO2/d(demand) at the solve's optimal basis.

        The marginal emission rate is the **emissions dual**: the price is
        ``lambda = c_B' B^-1``, and this is the same product with the
        per-generator CO2 rate vector in place of the cost vector. It is
        therefore the exact CO2 response to a marginal MWh of load in that
        zone-hour, distributed over the whole re-dispatch the basis implies --
        not the rate of any single "marginal unit", which is not even
        well-defined here (the tranched offer curves and the co-optimized
        reserve rows routinely put several generation columns at the margin
        at once, and an interior column's ``mc`` is not the energy price).

        **How it is computed, and why this way.** HiGHS exposes
        ``getBasisTransposeSolve``, which would give ``r_B' B^-1`` in one
        triangular solve -- but its right-hand side is indexed by BASIS
        POSITION, and highspy exposes no accessor for HiGHS's ``basicIndex``
        ordering. Assuming the natural sorted ``[columns | row slacks]`` order
        is wrong: measured against brute-force RHS perturbation over 60
        randomized LPs it disagreed on 58 of them. So the dual is obtained the
        ordering-free way instead -- freeze the cost-optimal basis, swap the
        objective to the CO2 rate vector, and re-price with the simplex
        iteration limit at zero, which makes HiGHS report ``r_B' B^-1`` in ROW
        order with no permutation to recover. On the same 60 LPs that agrees
        with perturbation on 59; the one exception is a degenerate vertex where
        the derivative is genuinely one-sided and the dual returns the DOWN
        side (``tests/unit/model/test_marginal_emission_rate.py`` pins both).

        Zero iterations means no pivot can occur, so the basis, the primal
        solution and every dual already extracted are untouched. The objective
        is left holding the CO2 rates on return: ``solve`` installs the full
        cost vector through ``changeColsCost`` on every pass, so the next pass
        overwrites it regardless (the same property the ``del cost`` lifetime
        fix above already relies on). The basis and the iteration-limit option
        ARE restored, because the next pass warm-starts from the basis.

        Args:
            n_zones: Number of price zones (the energy-balance row block is
                the first ``n_zones * T`` rows, hour-major).
            T: Hours in the solve.

        Returns:
            The ``(n_zones, T)`` rate array in tCO2/MWh, or ``None`` when the
            LP carried no generators or the re-pricing did not complete. This
            is a write-only diagnostic: it never raises into the solve path.
        """
        layout = self.layout
        if not layout.n_gen or not n_zones:
            return None
        rate = np.asarray(self.fleet.emission_rate, dtype=float)
        if rate.shape != (layout.n_gen,):
            return None

        h = self._h
        saved = None
        prev_limit = None
        try:
            saved = h.getBasis()
            _, prev_limit = h.getOptionValue("simplex_iteration_limit")

            # One hour's objective under the CO2 rates: the generation block
            # carries each unit's rate, every other column (wind, solar,
            # storage, flow, slack, dump, reserve, ...) emits nothing. Installed
            # in hour CHUNKS so the transient stays a few MB rather than a
            # second full-length float64 copy of the objective -- this runs in
            # the same post-solve window that owns the measured year peak
            # (miso-253), where the cost vector alone is 237 MB at plant-level
            # MISO scale.
            vpr = layout.vars_per_hour
            hour_block = np.zeros(vpr, dtype=np.float64)
            hour_block[layout._p_off : layout._p_off + layout.n_gen] = rate
            chunk = max(1, min(T, 512))
            for t0 in range(0, T, chunk):
                t1 = min(t0 + chunk, T)
                idx = np.arange(t0 * vpr, t1 * vpr, dtype=np.int32)
                h.changeColsCost(idx.size, idx, np.tile(hour_block, t1 - t0))
            del hour_block

            h.setBasis(saved)
            h.setOptionValue("simplex_iteration_limit", 0)
            h.run()
            duals = np.asarray(h.getSolution().row_dual, dtype=float)
            if duals.size < n_zones * T:
                return None
            # Same slice and orientation as the energy-balance price block.
            return duals[: n_zones * T].reshape(T, n_zones).T.copy()
        except Exception:  # pragma: no cover - a diagnostic never fails a solve
            logger.warning("marginal emission rate unavailable", exc_info=True)
            return None
        finally:
            if prev_limit is not None:
                try:
                    h.setOptionValue("simplex_iteration_limit", int(prev_limit))
                except Exception:
                    pass
            if saved is not None:
                try:
                    h.setBasis(saved)
                except Exception:
                    pass

    def export_cross_year_basis(self) -> "CrossYearBasis | None":
        """Snapshot this model's current optimal basis for next year's solve.

        Returns ``None`` when the model has not been solved yet (no basis to
        export). The status vectors are pulled out of HiGHS once and stored as
        compact ``int8`` arrays so the carry across years is cheap.
        """
        # Lazy import: CrossYearBasis is defined physically in lp/__init__
        # (pickle identity, plan §1); a module-level import back into the
        # package would be a module-level import cycle.
        from market_sim.model.lp import CrossYearBasis

        if self._n_solves == 0:
            return None
        basis = self._h.getBasis()
        return CrossYearBasis(
            col_status=np.asarray(basis.col_status, dtype=np.int8),
            row_status=np.asarray(basis.row_status, dtype=np.int8),
            layout=self.layout,
            unit_ids=list(self.fleet.unit_ids),
            n_rows=self._n_rows,
            n_energy_rows=self._n_energy_rows,
            n_storage_rows=self._n_storage_rows,
        )

    def apply_cross_year_basis(self, prev: "CrossYearBasis | None") -> bool:
        """Install a prior year's basis, remapped onto this model's LP.

        Maps ``prev``'s column/row statuses onto this year's column/row set
        (surviving generators by ``unit_id``; index-stable per-hour blocks and
        the energy/storage rows by position) and loads the result as an *alien*
        starting basis so HiGHS repairs the handful of inconsistencies from
        fleet changes. Must be called before the first :meth:`solve`.

        A wrong or partial mapping only costs solver iterations, never
        correctness -- the LP optimum is basis-independent. Returns ``True`` when
        a basis was installed, ``False`` when it was skipped (no prior basis,
        already solved, or mismatched horizon ``T``).
        """
        if prev is None or self._n_solves > 0:
            return False
        new_layout = self.layout
        if prev.layout.T != new_layout.T:
            # Different horizon -> the hour-blocked column/row strides do not
            # line up; fall back to a cold solve.
            return False

        T = new_layout.T
        old_local, new_local = _cross_year_column_map(
            prev.layout, prev.unit_ids, new_layout, list(self.fleet.unit_ids)
        )
        vph_old = prev.layout.vars_per_hour
        vph_new = new_layout.vars_per_hour

        # Default every column nonbasic at its lower bound (0 for a dispatch
        # variable -- a sound guess for a unit absent last year), then stamp the
        # mapped statuses across all hours in one broadcast.
        col_status = np.full(new_layout.total_columns, _BASIS_LOWER, dtype=np.int8)
        hours = np.arange(T)[:, None]
        new_cols = (hours * vph_new + new_local[None, :]).ravel()
        old_cols = (hours * vph_old + old_local[None, :]).ravel()
        col_status[new_cols] = prev.col_status[old_cols]

        # Default every row's slack basic, then copy the two well-defined row
        # families. Energy-balance rows map 1:1 when the zone count is unchanged
        # (always, within an ISO); storage SOC rows map positionally for the
        # units present in both years (unit-major s*T + hour layout).
        row_status = np.full(self._n_rows, _BASIS_BASIC, dtype=np.int8)
        if prev.n_energy_rows == self._n_energy_rows:
            ne = self._n_energy_rows
            row_status[:ne] = prev.row_status[:ne]
            ns = min(prev.n_storage_rows, self._n_storage_rows)
            if ns:
                row_status[ne : ne + ns] = prev.row_status[
                    prev.n_energy_rows : prev.n_energy_rows + ns
                ]

        basis = highspy.HighsBasis()
        basis.col_status = [_BASIS_STATUS_OBJS[s] for s in col_status]
        basis.row_status = [_BASIS_STATUS_OBJS[s] for s in row_status]
        basis.alien = True
        self._h.setBasis(basis)
        return True


def _cross_year_column_map(
    old_layout: "VariableLayout",
    old_unit_ids: list,
    new_layout: "VariableLayout",
    new_unit_ids: list,
) -> "tuple[np.ndarray, np.ndarray]":
    """Pair old/new per-hour column indices for a cross-year basis transfer.

    Returns ``(old_local, new_local)``, two equal-length int arrays of within-
    hour column offsets whose statuses should be copied old -> new. Generators
    are matched by ``unit_id`` (so retirements drop out and additions get no
    mapping); every other per-hour block (wind, solar, storage charge/discharge/
    SOC, transmission flow, load slack, dump, reserve, ORDC) is index-stable and
    matched positionally for the units/zones/links present in both years.
    """
    old_pairs: list = []
    new_pairs: list = []

    # Generators: match surviving units by id.
    old_index = {uid: i for i, uid in enumerate(old_unit_ids)}
    for new_i, uid in enumerate(new_unit_ids):
        old_i = old_index.get(uid)
        if old_i is not None:
            old_pairs.append(old_layout._p_off + old_i)
            new_pairs.append(new_layout._p_off + new_i)

    # Index-stable blocks: (old_offset, new_offset, old_count, new_count).
    blocks = [
        (old_layout._w_off, new_layout._w_off, old_layout.n_zones, new_layout.n_zones),
        (old_layout._s_off, new_layout._s_off, old_layout.n_zones, new_layout.n_zones),
        (
            old_layout._chg_off,
            new_layout._chg_off,
            old_layout.n_storage,
            new_layout.n_storage,
        ),
        (
            old_layout._dis_off,
            new_layout._dis_off,
            old_layout.n_storage,
            new_layout.n_storage,
        ),
        (
            old_layout._soc_off,
            new_layout._soc_off,
            old_layout.n_storage,
            new_layout.n_storage,
        ),
        (
            old_layout._flow_off,
            new_layout._flow_off,
            old_layout.n_links,
            new_layout.n_links,
        ),
        (
            old_layout._slack_off,
            new_layout._slack_off,
            old_layout.n_zones,
            new_layout.n_zones,
        ),
        (
            old_layout._dump_off,
            new_layout._dump_off,
            old_layout.n_zones,
            new_layout.n_zones,
        ),
        (
            old_layout._reserve_off,
            new_layout._reserve_off,
            old_layout.n_reserve,
            new_layout.n_reserve,
        ),
        (
            old_layout._ordc_off,
            new_layout._ordc_off,
            old_layout.n_ordc_steps,
            new_layout.n_ordc_steps,
        ),
        (
            old_layout._dis_tranche_off,
            new_layout._dis_tranche_off,
            old_layout.n_dis_tranche,
            new_layout.n_dis_tranche,
        ),
        # Cascade spill and pond-volume blocks (NWPP-36): positionally stable
        # for the coupled plants present in both years (the chain membership
        # is a published inventory, so the local order is year-invariant).
        (
            old_layout._cas_s_off,
            new_layout._cas_s_off,
            old_layout.n_cascade // 2,
            new_layout.n_cascade // 2,
        ),
        (
            old_layout._cas_v_off,
            new_layout._cas_v_off,
            old_layout.n_cascade // 2,
            new_layout.n_cascade // 2,
        ),
    ]
    for old_off, new_off, old_n, new_n in blocks:
        k = min(old_n, new_n)
        if k:
            rng = np.arange(k)
            old_pairs.extend((old_off + rng).tolist())
            new_pairs.extend((new_off + rng).tolist())

    return (
        np.asarray(old_pairs, dtype=np.int64),
        np.asarray(new_pairs, dtype=np.int64),
    )
