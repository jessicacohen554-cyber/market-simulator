"""Dispatch LP package: layout, costs, rows, bounds, and the HiGHS model.

Package split of ``model/dispatch.py`` (4,974 ln; refactor-consolidation
plan §5 item 7, 2026-07-22): the LP core now lives here as :mod:`.layout` /
:mod:`.costs` / :mod:`.rows` / :mod:`.reserve_rows` / :mod:`.bounds` /
:mod:`.model`, and ``market_sim.model.dispatch`` remains the historical
import path as a ``sys.modules``-alias facade of THIS package (the
``model/capacity.py`` / ``model/transmission.py`` pattern), so both paths
name ONE namespace object and every historical import, monkeypatch, and
attribute write keeps working. The re-export surface is pinned by
``tests/test_dispatch_facade.py``.

Pickle identity (plan §1 "Pickle identity is frozen"): the committed
``p2_state`` pickles resolve :class:`DispatchResult` (and the cross-year
warm-start cache resolves :class:`CrossYearBasis`) by ``__module__`` ==
``market_sim.model.dispatch``. Those classes and :func:`solve_dispatch` are
therefore defined PHYSICALLY in this ``__init__`` with ``__module__`` pinned
to the frozen path — never re-exported from a submodule — asserted by
``tests/test_persisted_identity.py`` and ``tests/test_p2_state_smoke.py``.
"""

import logging
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

from market_sim.config.constants import (  # noqa: F401  (historical namespace re-export)
    HOURS_PER_YEAR,
    STORAGE_TIEBREAKER_EPSILON,
)
from market_sim.data.fleet import (  # noqa: F401  (historical namespace re-export)
    FUEL_TYPE_MAP,
    FleetArrays,
    _hour_to_month_index,
    assemble_mc,
)
from market_sim.model.lp.bounds import build_variable_bounds  # noqa: F401
from market_sim.model.lp.costs import build_cost_vector  # noqa: F401
from market_sim.model.lp.layout import (  # noqa: F401
    VariableLayout,
    _build_zone_gen_map,
    _build_zone_storage_map,
    _vstack_csr_free,
)
from market_sim.model.lp.model import (  # noqa: F401
    _BASIS_BASIC,
    _BASIS_LOWER,
    DispatchModel,
    _cross_year_column_map,
)
from market_sim.model.lp.reserve_rows import (  # noqa: F401
    _build_reserve_rows,
    _build_reserve_rows_pergen,
    storage_reserve_mw,
)
from market_sim.model.lp.rows import (  # noqa: F401
    _build_gen_group_cap_rows,
    _build_hydro_rows,
    _build_import_node_rows,
    _build_interface_rows,
    _build_local_capacity_rows,
    _build_mass_cap_rows,
    _build_oil_budget_rows,
    _build_posture_energy_rows,
    _build_ramp_rows,
    _build_rps_row,
    _build_storage_alloc_rows,
    _build_storage_daily_cycle_rows,
    build_constraints,
)

logger = logging.getLogger(__name__)


@dataclass
class DispatchResult:
    """Solved economic-dispatch quantities and prices.

    All time-indexed arrays span ``T`` hours. Storage and flow fields are
    ``None`` when the problem has no storage units or no transmission links.

    Attributes:
        dispatch: Thermal generation, shape ``(n_gen, T)``.
        wind_dispatched: Dispatched wind per zone, shape ``(n_zones, T)``.
        solar_dispatched: Dispatched solar per zone, shape ``(n_zones, T)``.
        slack: Unserved load per zone, shape ``(n_zones, T)``.
        dump: Overgeneration absorbed per zone, shape ``(n_zones, T)``.
        prices: Zonal energy prices, shape ``(n_zones, T)``.
        storage_charge: Storage charging power, shape ``(n_storage, T)``.
        storage_discharge: Storage discharging power, shape ``(n_storage, T)``.
        storage_soc: Storage state of charge, shape ``(n_storage, T)``.
        flows: Transmission link flows, shape ``(n_links, T)``.
        objective_value: Optimal objective (total system cost).
        status: HiGHS model-status string.
        build_time: Seconds spent assembling and loading the model.
        solve_time: Seconds spent inside the solver.
        emissions: CO2 emissions per generator, shape ``(n_gen, T)``;
            ``None`` until populated by downstream emissions accounting.
        rps_shadow_price: Endogenous RPS compliance cost in $/MWh. Legacy
            single ISO-wide row: a scalar (that row's dual, THE REC price).
            Per-compliance-region grain (FFR-7B Arm 2, MISO): a per-zone
            ``(n_zones,)`` vector ``p[z] = max{dual_r : z in
            eligible_zones(r)}`` — the highest price a certificate generated
            in zone ``z`` commands across the regions whose statutes admit
            it (0 where none do). Capacity-screen consumers must index it by
            the candidate's/unit's zone via
            ``policy.rps.rps_credit_for_zone`` — a broadcast scalar would
            rebuild the E-1 defect (FFR-6B §3.2). ``None`` when no RPS
            constraint was active. Distinct from the exogenous EAC prices.
        rps_region_duals: Per-compliance-region raw row duals ``(K,)`` in
            $/MWh — region r's dual is compliance market r's REC price,
            capped at its own ACP. Diagnostics companion of the per-zone
            ``rps_shadow_price`` mapping; ``None`` on the legacy single-row
            path and when no RPS constraint was active.
        co2_cap_price: Endogenous allowance price ($/tCO2) per active emissions
            mass-cap row -- the negated dual of each cap (one entry per cap).
            ``None`` when no mass cap was active. This is a power-sector,
            no-bank scenario price (plan §2, §8), distinct from the exogenous
            RGGI/CARB adder.
    """

    dispatch: np.ndarray
    wind_dispatched: np.ndarray
    solar_dispatched: np.ndarray
    slack: np.ndarray
    dump: np.ndarray
    prices: np.ndarray
    storage_charge: np.ndarray | None
    storage_discharge: np.ndarray | None
    storage_soc: np.ndarray | None
    flows: np.ndarray | None
    objective_value: float
    status: str
    build_time: float
    solve_time: float
    emissions: np.ndarray | None = None
    rps_shadow_price: "float | np.ndarray | None" = None
    # Per-compliance-region RPS row duals (K,) — None off the K-row grain.
    rps_region_duals: np.ndarray | None = None
    # Clean/carbon-free tier row duals (K2,) — each state's clean attribute
    # price, capped at its own escape (FFR-7B Arm 3). None off the family.
    # Consumers map them to per-(fuel, zone) credits via
    # policy.clean_tiers.clean_credit_by_fuel and compose them into the
    # EXISTING max(eac, rps_shadow) doctrine — never a sum (FFR-6B §6.4).
    clean_region_duals: np.ndarray | None = None
    # Endogenous CO2 allowance price(s) ($/tCO2), one per active mass-cap row;
    # None unless a mass cap was enabled.
    co2_cap_price: list[float] | None = None
    # Energy+reserve co-optimization outputs (None unless co-opt is on).
    reserve_dispatch: np.ndarray | None = None  # (n_zones, T) upward reserve MW
    reserve_price: np.ndarray | None = None  # (T,) reserve clearing $/MWh
    # (T, n_families) per-family balance-row dual — the per-product AS clearing
    # price for ERCOT's multi-product co-opt; the per-hour max is the binding MCPC.
    reserve_price_by_family: np.ndarray | None = None
    # (T, n_families) per-family cleared ORDC shortfall MW — the sum of each
    # family's own slice of the family-major ORDC block. Reported alongside
    # ``reserve_price_by_family`` so a family's dual is interpretable: a
    # positive dual at zero shortfall is the family binding on its requirement,
    # while a positive shortfall names the ORDC step that set the price. None
    # unless the co-opt is on. Persisted by the calibration bundle's
    # ``hourly/reserve_family_<year>.parquet`` sidecar.
    reserve_shortfall_by_family: np.ndarray | None = None
    # (T, n_families) per-family HELD reserve MW — the balance row's
    # reserve-column activity (row activity minus the family's own ORDC
    # shortfall). Completes the persisted row: ``held + shortfall >=
    # requirement``, with equality iff the family binds, and the slack when it
    # does not. Taken from the row activity rather than by re-summing R columns
    # because the balance row's coefficient structure is layout-dependent
    # (per-class blocks, storage RS columns, per-generator product masks, the
    # ERCOT all-class family). None unless the co-opt is on.
    reserve_held_by_family: np.ndarray | None = None
    # (n_headroom_rows, T) dual of the reserve-supply cap rows (ERCOT RTOLCAP
    # re-scope), sign-flipped to >= 0. This is the UNINTERNALIZED part of the
    # reserve scarcity price: when the cap row is the binding reserve
    # constraint the balance dual does NOT pass into the energy LMP ("energy
    # cancels out of a sum-R cap") and this dual carries the full ORDC step;
    # when the physical shared-headroom rows bind instead, the balance dual
    # IS folded into the energy LMP (see TestErcotOrdcTotalReserve) and this
    # dual is zero. The post-solve additive RTORPA construction must therefore
    # add THIS dual, not the balance dual, to avoid double-counting scarcity
    # already priced into the energy dual. None unless a supply cap was active.
    reserve_supply_cap_dual: np.ndarray | None = None
    # (n_zones, T) cleared storage AS from the duration-gate mechanism
    # (ercot_storage_as_duration_gate) — the EXACT storage energy-vs-AS split
    # (sum over AS products of the RS[c,z] columns), not the min() attribution
    # upper bound. None unless the duration gate is active.
    storage_reserve_dispatch: np.ndarray | None = None
    # Commitment-posture outputs (None unless miso_commitment_posture is on):
    # per postured pool, the online capacity U[p,t], the startup increments
    # SU[p,t] (MW started), and the pool's cleared reserve R[p,t] — the
    # modeled online-headroom / cleared-reserve series the design note §A
    # honesty gate compares against the measured MISO ASM data.
    posture_online_mw: np.ndarray | None = None  # (q, T)
    posture_startup_mw: np.ndarray | None = None  # (q, T)
    posture_reserve_mw: np.ndarray | None = None  # (q, T)
    posture_zone_idx: np.ndarray | None = None  # (q,) pool zone index
    posture_fuel_idx: np.ndarray | None = None  # (q,) pool fuel-type index
    # Per-area LCR dual ($/MWh), shape ``(n_areas, T)``. The dual of each
    # local-capacity minimum-generation row — the uplift-like commitment
    # value of local generation. ``None`` unless ``local_capacity_constraints``
    # is active and at least one LCR area was built. Hour-major, area-minor
    # in the LP; reshaped to ``(n_areas, T)`` here. Non-negative (>= row).
    lcr_dual: np.ndarray | None = None
    # Generator membership per LCR area — list of int arrays, one per area,
    # each containing the generator LP indices that belong to that area.
    # ``None`` unless ``local_capacity_constraints`` is active.
    lcr_gen_idx: list[np.ndarray] | None = None
    # --- network duals (the ``network_<year>.parquet`` sidecar) -------------
    # Aggregate-interface row duals, shape ``(n_groups, T)``, and the flow
    # columns' reduced costs, shape ``(n_links, T)`` — both HiGHS-raw (NOT
    # sign-normalised). They close the flow column's stationarity identity
    #     lambda_to - lambda_from = -flow_dual[l] - sum_g s(g,l) * interface_dual[g]
    # whose right-hand terms are each >= 0 in the import direction and each
    # the rent charged by exactly ONE limit — the link's own TTC bound, or one
    # aggregate-interface group. That is what lets a diagnostic say WHICH
    # transmission limit binds in an hour instead of only that one does.
    # ``interface_link_idx`` / ``interface_signs`` give each group's signed
    # link membership, and ``interface_cap_up`` / ``interface_cap_dn`` its
    # per-hour row bounds ``(n_groups, T)`` (a scalar cap is broadcast). All
    # ``None`` when the LP carried no links / no interface groups.
    interface_dual: np.ndarray | None = None
    interface_link_idx: list[np.ndarray] | None = None
    interface_signs: list[np.ndarray] | None = None
    interface_cap_up: np.ndarray | None = None
    interface_cap_dn: np.ndarray | None = None
    flow_dual: np.ndarray | None = None
    # The flow columns' own bounds ``(n_links, T)`` — the per-link TTC the LP
    # actually saw (hourly where an overlay made it hourly), so the sidecar
    # records the third candidate limit's level next to its dual.
    flow_cap_up: np.ndarray | None = None
    flow_cap_dn: np.ndarray | None = None
    # --- per-generator offer + optimality (the ``unit_hourly`` sidecar) -----
    # ``gen_mc`` is the (n_gen, T) marginal-cost array THIS solve installed in
    # its objective — the LP's own offer, not a reconstruction of it; a
    # reference to the caller's array, so it costs no memory. ``gen_reduced
    # _cost`` is the generation columns' HiGHS reduced cost, (n_gen, T)
    # float32, HiGHS-raw (NOT sign-normalised), the exact twin of
    # ``flow_dual`` for the P block.
    #
    # Together they close the generation column's stationarity identity
    #     red_cost[g,t] = mc[g,t] - lambda[zone(g),t] + sum_r a(r,g) * y_r
    # whose last term is the net rent every NON-energy row (reserve headroom,
    # LCR/TSL area minima, ramp, RPS/mass-cap, ...) charges that unit-hour. It
    # is what lets a diagnostic say WHY a unit whose offer is below its own
    # zone's dual is not running — the sign says which bound it sits at
    # (> 0 lower, < 0 upper, ~ 0 interior/marginal), and the residual
    # ``red_cost - (mc - lambda)`` measures the charge and names nothing else.
    # Both ``None`` when the LP carried no generators.
    gen_mc: np.ndarray | None = None
    gen_reduced_cost: np.ndarray | None = None


@dataclass
class CrossYearBasis:
    """A frozen HiGHS optimal basis plus the identity needed to remap it.

    The calibration solves one ISO-year per :class:`DispatchModel`. Adjacent
    years share almost all structure -- same zones, same network, mostly the
    same units -- so a year's optimal basis is a strong warm start for the next
    year's first (P0) solve, which is otherwise the one remaining cold solve
    once intra-year warm-start has made P1 cheap.

    HiGHS can only *load* a basis whose dimensions match the target LP, and the
    fleet changes year to year (retirements/additions) so the column count
    differs. Rather than grow the LP to a union "superset" fleet (option (a):
    dimensionally stable but a permanently larger, more memory-hungry matrix),
    this carries the basis with enough layout identity to *map* it onto the next
    year's columns and rows (option (c)): surviving units matched by ``unit_id``,
    index-stable per-hour blocks (wind/solar/storage/slack/dump, keyed by
    zone/unit position) copied directly, and any genuinely new column/row left
    nonbasic-at-bound / basic so HiGHS repairs the few inconsistencies. Because
    an LP's optimum is independent of the starting basis, this can only change
    the solve *path*, never the cleared prices or generation -- the same
    neutrality guarantee the intra-year warm-start relies on.

    Attributes:
        col_status: Per-column HiGHS basis status, ``int8`` of length
            ``layout.total_columns``.
        row_status: Per-row HiGHS basis status, ``int8`` of length ``n_rows``.
        layout: The :class:`VariableLayout` the basis was solved under.
        unit_ids: Generator unit identifiers in thermal-block column order, used
            to match surviving units across years.
        n_rows: Total LP row count.
        n_energy_rows: Energy-balance row count (``n_zones * T``).
        n_storage_rows: Storage SOC row count (``n_storage * T``).
    """

    col_status: np.ndarray
    row_status: np.ndarray
    layout: "VariableLayout"
    unit_ids: list
    n_rows: int
    n_energy_rows: int
    n_storage_rows: int


# Pickle identity (plan §1): the committed p2_state pickles resolve these
# classes by __module__ == "market_sim.model.dispatch"; pin it so both
# directions of the unpickle contract survive the split
# (tests/test_persisted_identity.py).
DispatchResult.__module__ = "market_sim.model.dispatch"
CrossYearBasis.__module__ = "market_sim.model.dispatch"


def solve_dispatch(
    fleet: FleetArrays,
    demand: np.ndarray,
    wind_cf: np.ndarray,
    wind_cap: np.ndarray,
    solar_cf: np.ndarray,
    solar_cap: np.ndarray,
    mc: np.ndarray | None = None,
    fuel_prices: np.ndarray | None = None,
    carbon_price: np.ndarray | float = 0,
    nox_price: np.ndarray | float = 0,
    so2_price: np.ndarray | float = 0,
    voll: float = 5000,  # default matches ScenarioConfig.voll for ERCOT
    slack_cost: np.ndarray | None = None,
    incidence: np.ndarray | sp.spmatrix | None = None,
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
    eta_chg: np.ndarray | float | None = None,
    eta_dis: np.ndarray | float | None = None,
    wind_mc: np.ndarray | float = 0.0,
    solar_mc: np.ndarray | float = 0.0,
    storage_discharge_eac: float = 0.0,
    storage_discharge_cost: np.ndarray | float = 0.0,
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
        list[tuple[np.ndarray, np.ndarray, float, np.ndarray]] | None
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
    dump_cost_full_offer_domain: bool = False,
    dis_tranche_arm_idx: np.ndarray | None = None,
    dis_tranche_width: np.ndarray | None = None,
    dis_tranche_price: np.ndarray | None = None,
    T: int | None = None,
) -> DispatchResult:
    """Solve the linear economic-dispatch problem with HiGHS.

    Builds the variable layout, objective, constraint matrix and bounds,
    loads them into a HiGHS LP and minimizes total system cost. Zonal
    prices are recovered as the dual values of the per-zone energy-balance
    equality constraints.

    Args:
        fleet: Vectorized fleet arrays.
        demand: Zonal demand of shape ``(n_zones, T)`` in MW.
        wind_cf: Wind capacity factor of shape ``(n_zones, T)``.
        wind_cap: Installed wind capacity per zone, shape ``(n_zones,)``.
        solar_cf: Solar capacity factor of shape ``(n_zones, T)``.
        solar_cap: Installed solar capacity per zone, shape ``(n_zones,)``.
        mc: Marginal cost array of shape ``(n_gen, T)``. When ``None`` it is
            assembled from ``fuel_prices``, ``carbon_price`` and ``nox_price``.
        fuel_prices: Fuel prices passed to ``assemble_mc`` when ``mc`` is
            ``None``.
        carbon_price: Carbon price used when ``mc`` is ``None``.
        nox_price: NOx price used when ``mc`` is ``None``.
        so2_price: SO2 price used when ``mc`` is ``None``.
        voll: Value of lost load applied to load-slack variables.
        slack_cost: Optional ``(n_zones, T)`` per-zone-hour load-slack cost
            override (declared-window ELMP emergency-tier repricing). ``None``
            keeps the flat ``voll`` broadcast (byte-identical).
        dump_cost_full_offer_domain: Take the overgeneration-dump guard over
            every ``mc`` row that can inject, not just the renewable/storage
            production credits (``ScenarioConfig.dump_cost_full_offer_domain``,
            caiso-139). ``False`` is byte-identical. Present here so the
            non-warm and P2 paths, which reach the LP through this facade with
            the same ``dispatch_kwargs`` mapping, carry the flag instead of
            raising on an unexpected keyword.
        incidence: Node-link incidence of shape ``(n_zones, n_links)``.
        ttc: Total transfer capability per link, shape ``(n_links,)``
            (static) or ``(T, n_links)`` (per-hour seasonal limit).
        ttc_import: Optional reverse-direction (to->from) capability, same
            accepted shapes; when given, flow lower bounds are
            ``-ttc_import`` (asymmetric interface — ERCOT measured GTC
            export caps). ``None`` keeps the symmetric ``-ttc``.
        storage_power_cap: Charge/discharge power cap, shape ``(n_storage,)``
            or hour-varying ``(n_storage, T)`` (COD intra-year ramp; see
            ``storage.storage_cap_profiles``).
        storage_energy_cap: SOC energy cap, shape ``(n_storage,)`` or
            ``(n_storage, T)``.
        storage_zone_idx: Zone index of each storage unit.
        eta_chg: Storage charge efficiency, scalar or ``(n_storage,)``.
        eta_dis: Storage discharge efficiency, scalar or ``(n_storage,)``.
        wind_mc: Wind dispatch marginal cost in $/MWh; scalar or
            ``(n_zones, T)``. Negative under a production tax credit.
        solar_mc: Solar dispatch marginal cost in $/MWh; scalar or
            ``(n_zones, T)``.
        storage_discharge_eac: Exogenous EAC paid per MWh discharged in
            $/MWh, lowering the storage discharge slot cost.
        rps_target: Required renewable-energy share. When not ``None`` and
            positive, an annual RPS constraint is enforced and its
            dual is returned as ``DispatchResult.rps_shadow_price``.
        rps_acp_price: Optional RPS Alternative Compliance Payment ceiling in
            $/MWh. When set alongside a positive ``rps_target``, an ACP escape
            column is added so the RPS row stays feasible when physical RECs
            fall short (paying the ACP substitutes for renewable energy) and its
            dual (the REC price) is capped at this ceiling. ``None`` (default)
            keeps the RPS a hard constraint, byte-identical to before.
        rps_eligible_fuels: The ISO statute's renewable-tier eligible fuel
            names (``policy.rps.get_rps_eligible_fuels``); names beyond
            wind/solar add the matching thermal-block generator columns to the
            RPS row (FFR-7B Arm 1). ``None`` (default) keeps the
            wind+solar-only row, byte-identical to before.
        rps_region_zone_mask: ``(K, n_zones)`` bool per-compliance-region
            eligibility mask (FFR-7B Arm 2, MISO — see
            ``policy.rps.build_rps_region_arrays``). With the two companions
            below it REPLACES the single ISO-wide row with K per-region rows;
            mutually exclusive with ``rps_target``. ``None`` (default) keeps
            the legacy path, byte-identical to before.
        rps_region_obligation_frac: ``(K, n_zones)`` float per-(region, zone)
            RHS weights (within-zone obligated load share x target).
        rps_region_acp_price: ``(K,)`` per-region ACP escape prices in $/MWh
            (REQUIRED with the region rows — each row's feasibility escape).
        clean_region_zone_mask: ``(K2, n_zones)`` bool clean/carbon-free tier
            eligibility mask (FFR-7B Arm 3, MISO West/East —
            ``policy.clean_tiers.build_clean_region_arrays``; the federal
            CES target row, ``policy.federal_ces.build_federal_ces_region``).
            A second independent row family that stands alone or beside
            either RPS grain (SCN-WS2a relaxed the former "requires the RPS
            region family" coupling). ``None`` (default) adds no rows,
            byte-identical to before.
        clean_region_obligation_frac: ``(K2, n_zones)`` float clean-tier RHS
            weights.
        clean_region_acp_price: ``(K2,)`` clean-row feasibility-escape prices
            in $/MWh (REQUIRED with the clean rows).
        clean_region_fuels: Per-region qualifying spec — a statutory
            fuel-name tuple (nuclear admitted; unknown names hard-error) or an
            ``(n_gen,)`` per-generator credit-fraction vector (the federal CES
            row's ``unit_credit_fractions``).
        mass_cap_coeffs: Optional ``(k, n_gen)`` emissions mass-cap row
            coefficients (``m[g] * emission_rate[g]``); one inequality row per
            cap bounds in-region fossil emissions. ``None`` (default) adds no
            rows and the LP is identical to today's.
        mass_cap_rhs: ``(k,)`` annual tonnage budgets (row upper bounds) paired
            with ``mass_cap_coeffs``.
        mass_cap_labels: Optional per-cap labels carried onto the result.
        hydro_monthly_energy: Monthly hydro energy budget in MWh, shape
            ``(n_hydro, n_months)``. When ``None`` the hydro constraint
            family is omitted and the LP is identical to today's.
        hydro_month_index: Month index of each hour, shape ``(T,)``.
            Defaults to the standard calendar when ``None``.
        hydro_gen_idx: Thermal-block indices of the hydro generators that
            ``hydro_monthly_energy`` is keyed to. Derived from the fleet's
            hydro fuel type when ``None``.
        hydro_monthly_min: Monthly minimum hydro energy (min-flow floor) in
            MWh, shape ``(n_hydro, n_months)``. Zero floor when ``None``.
        storage_daily_cycle_hours: When set (e.g. ``24``), forces each storage
            unit's SOC back to its day-start level every this-many hours, so
            storage cannot arbitrage across days. ``None`` leaves the annual
            cyclic boundary as the only SOC anchor (full perfect foresight).
        T: Number of hours. Inferred from ``demand`` when ``None``.

    Returns:
        A populated ``DispatchResult``.

    Raises:
        RuntimeError: When HiGHS does not return a feasible primal solution.
    """
    model = DispatchModel(
        fleet,
        demand,
        wind_cf=wind_cf,
        wind_cap=wind_cap,
        solar_cf=solar_cf,
        solar_cap=solar_cap,
        voll=voll,
        slack_cost=slack_cost,
        incidence=incidence,
        ttc=ttc,
        ttc_import=ttc_import,
        wind_curtail_share=wind_curtail_share,
        solar_curtail_share=solar_curtail_share,
        storage_power_cap=storage_power_cap,
        storage_energy_cap=storage_energy_cap,
        storage_soc_min=storage_soc_min,
        storage_discharge_min=storage_discharge_min,
        storage_charge_cap=storage_charge_cap,
        storage_discharge_cap=storage_discharge_cap,
        storage_zone_idx=storage_zone_idx,
        eta_chg=eta_chg,
        eta_dis=eta_dis,
        wind_mc=wind_mc,
        solar_mc=solar_mc,
        storage_discharge_eac=storage_discharge_eac,
        storage_discharge_cost=storage_discharge_cost,
        rps_target=rps_target,
        rps_acp_price=rps_acp_price,
        rps_eligible_fuels=rps_eligible_fuels,
        rps_region_zone_mask=rps_region_zone_mask,
        rps_region_obligation_frac=rps_region_obligation_frac,
        rps_region_acp_price=rps_region_acp_price,
        clean_region_zone_mask=clean_region_zone_mask,
        clean_region_obligation_frac=clean_region_obligation_frac,
        clean_region_acp_price=clean_region_acp_price,
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
        mass_cap_labels=mass_cap_labels,
        reserve_requirement=reserve_requirement,
        reserve_eligible=reserve_eligible,
        reserve_storage=reserve_storage,
        ordc_penalties=ordc_penalties,
        ordc_step_widths=ordc_step_widths,
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
        reserve_storage_duration_h=reserve_storage_duration_h,
        reserve_pergen_gen_idx=reserve_pergen_gen_idx,
        reserve_pergen_col=reserve_pergen_col,
        reserve_pergen_ramp10=reserve_pergen_ramp10,
        reserve_posture_pools=reserve_posture_pools,
        reserve_posture_mlf=reserve_posture_mlf,
        reserve_posture_startup=reserve_posture_startup,
        reserve_pergen_col_pool=reserve_pergen_col_pool,
        reserve_balance_col_mask=reserve_balance_col_mask,
        reserve_pergen_online_gated_cols=reserve_pergen_online_gated_cols,
        reserve_pergen_pool_ramp10=reserve_pergen_pool_ramp10,
        posture_gen_idx=posture_gen_idx,
        posture_col=posture_col,
        posture_mlf=posture_mlf,
        posture_startup=posture_startup,
        link_bidirectional=link_bidirectional,
        link_flow_cost=link_flow_cost,
        link_loss=link_loss,
        dump_cost_full_offer_domain=dump_cost_full_offer_domain,
        dis_tranche_arm_idx=dis_tranche_arm_idx,
        dis_tranche_width=dis_tranche_width,
        dis_tranche_price=dis_tranche_price,
        T=T,
    )
    return model.solve(
        mc=mc,
        fuel_prices=fuel_prices,
        carbon_price=carbon_price,
        nox_price=nox_price,
        so2_price=so2_price,
    )


solve_dispatch.__module__ = "market_sim.model.dispatch"
