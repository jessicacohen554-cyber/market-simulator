"""Constraint-row builders and matrix assembly for the dispatch LP.

Package split of ``model/dispatch.py`` (refactor-consolidation plan §5 item
7): every non-reserve row family (RPS, mass caps, hydro, oil budgets, import
nodes, storage cycling/allocation, interfaces, ramps, local capacity, group
envelopes, commitment posture) and the :func:`build_constraints` assembler.
Pure code motion — every def is byte-identical to its pre-split
``dispatch.py`` source.
"""

import numpy as np
import scipy.sparse as sp

from typing import TYPE_CHECKING

from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays, _hour_to_month_index
from market_sim.model.lp.layout import (
    VariableLayout,
    _build_zone_gen_map,
    _build_zone_storage_map,
    _vstack_csr_free,
)

if TYPE_CHECKING:  # quoted annotation only; the row builder imports lazily
    from market_sim.model.lp.hydro_cascade import HydroCascadeSpec
from market_sim.model.lp.reserve_rows import (
    _build_reserve_rows,
    _build_reserve_rows_pergen,
)


def _build_rps_row(
    layout: VariableLayout,
    rps_target: float,
    demand: np.ndarray,
    eligible_gen_idx: np.ndarray | None = None,
) -> tuple[sp.csr_matrix, float]:
    """Return the single annual RPS constraint row and its lower bound.

    The row carries a ``+1`` coefficient on every wind and solar dispatch
    column across all ``T`` hours; the lower bound is ``rps_target`` times
    total annual demand. The resulting constraint
    ``renewable (+ ACP) >= rps_target * demand`` is an inequality with no upper
    bound, and its dual is the implicit REC price ($/MWh renewable-energy
    premium).

    When the layout carries an ACP escape column (``layout.n_rec_acp``), each
    hour's ACP variable also takes a ``+1`` coefficient: it is the real-market
    Alternative Compliance Payment, so a region short of physical RECs satisfies
    the row by paying the ACP rate (priced in the objective) rather than the LP
    turning infeasible. Its non-negativity plus the objective ACP cost pin the
    row's dual (the REC price) at or below the ACP ceiling — exactly how a REC
    market clears when supply is short.

    ``eligible_gen_idx`` extends the counted set beyond the wind/solar zone
    columns with thermal-block generator columns (``P[g,t]``) whose fuel the
    governing statute counts toward its *renewable* tier — e.g. NYISO existing
    hydro and biomass (CLCPA 70x30, PSL §66-p), CAISO geothermal and biomass
    (Pub. Res. Code §25741) — resolved per ISO from the cited
    ``RPS_ELIGIBLE_FUELS_BY_ISO`` table (FFR-7B Arm 1, rule 14 [R-ACCURATE];
    the under-counted set pinned those rows' duals at the ACP ceiling, FFR-6B
    §8). ``None`` (the default) keeps the exact wind+solar-only row.

    Nuclear is NEVER admitted here: an RPS is a *renewable* portfolio
    standard, so nuclear -- clean but not renewable -- is excluded (CX-6a,
    capacity-economics plan 2026-07 §6.5). Counting nuclear here would let its
    output satisfy the target and depress the REC dual toward zero wherever
    nuclear+VRE already clear it, killing the renewable-entry signal the dual
    exists to send. Nuclear's zero-emission support flows separately through
    ``eac_price_nuclear`` (ZEC/CES); a *clean/carbon-free* tier that counts
    nuclear is a separate row family (FFR-6B §6.3), never a widening of this
    row. The capacity screens' ``_RPS_ELIGIBLE_FUELS``/``_RENEWABLE_NEW_FUELS``
    remain wind/solar only: new-entry candidates are wind/solar, and existing
    non-VRE renewables' attribute revenue stays on the ``eac_*`` channels.
    """
    T = layout.T  # T: number of hours
    vph = layout.vars_per_hour
    hours = np.arange(T)[:, np.newaxis]  # t: hour index
    zones = np.arange(layout.n_zones)  # z: zone index

    wind_cols = (hours * vph + layout._w_off + zones).ravel()
    solar_cols = (hours * vph + layout._s_off + zones).ravel()

    col_groups = [wind_cols, solar_cols]
    if eligible_gen_idx is not None:
        gidx = np.asarray(eligible_gen_idx, dtype=int)  # g: eligible generators
        if gidx.size:
            col_groups.append((hours * vph + layout._p_off + gidx).ravel())
    if layout.n_rec_acp:
        # One ACP escape column per hour (a single non-negative variable),
        # +1 in the row so paying ACP substitutes for physical RECs.
        acp_cols = np.arange(T) * vph + layout._rec_acp_off
        col_groups.append(acp_cols)
    cols = np.concatenate(col_groups)
    row = sp.coo_matrix(
        (np.ones(cols.size), (np.zeros(cols.size, dtype=int), cols)),
        shape=(1, layout.total_columns),
    ).tocsr()
    rhs = rps_target * float(np.asarray(demand, dtype=float).sum())
    return row, rhs


# The two renewables that are LP *zone columns* (W[z,t]/S[z,t]), always counted
# by the RPS row; every other eligible fuel is a thermal-block generator class
# resolved through FUEL_TYPE_MAP.
_RPS_ROW_BASE_FUELS: tuple[str, str] = ("wind", "solar")


def _resolve_rps_eligible_gen_idx(
    fleet: FleetArrays,
    eligible_fuels: tuple[str, ...] | None,
) -> np.ndarray | None:
    """Resolve an RPS eligible-fuel name set to thermal-block generator indices.

    ``eligible_fuels`` is the governing statute's renewable-tier eligible set
    for the ISO (``policy.rps.get_rps_eligible_fuels``). Wind and solar are the
    LP's zone columns and are counted by the row directly, so only the names
    beyond ``_RPS_ROW_BASE_FUELS`` resolve here, against ``FUEL_TYPE_MAP``
    (data-driven per FFR-6B §6.3(2) — never a hardcoded class tuple at the call
    site). An unknown fuel name is a hard error, never a silent drop; nuclear
    is refused by name (CX-6a — a clean tier that counts nuclear is a separate
    row family, FFR-6B §6.3, not a widening of the renewable row).

    Returns ``None`` (byte-identical row) for ``None``/empty input, for the
    default wind+solar-only set, and when no generator of an eligible class
    exists in the fleet.
    """
    if not eligible_fuels:
        return None
    extra = [f for f in eligible_fuels if f not in _RPS_ROW_BASE_FUELS]
    if not extra:
        return None
    if "nuclear" in extra:
        raise ValueError(
            "nuclear is never RPS-row eligible (CX-6a): a clean/carbon-free "
            "tier that counts nuclear is a separate row family (FFR-6B §6.3), "
            "not a widening of the renewable row"
        )
    unknown = sorted(f for f in extra if f not in FUEL_TYPE_MAP)
    if unknown:
        raise ValueError(
            f"unknown RPS-eligible fuel name(s) {unknown}: every entry must "
            "resolve against FUEL_TYPE_MAP"
        )
    codes = np.array([FUEL_TYPE_MAP[f] for f in extra], dtype=int)
    gidx = np.flatnonzero(np.isin(np.asarray(fleet.fuel_type_idx), codes))
    return gidx if gidx.size else None


def _resolve_clean_region_gen_idx(
    fleet: FleetArrays,
    region_fuels: "tuple[tuple[str, ...] | np.ndarray, ...]",
    eligible_zone_mask: np.ndarray,
) -> "list[np.ndarray | None]":
    """Resolve each clean-tier region's qualifying spec to generator indices.

    The clean-family sibling of :func:`_resolve_rps_eligible_gen_idx`, with
    the ONE deliberate difference: NUCLEAR IS ADMITTED here. A clean/
    carbon-free tier that counts nuclear is exactly this separate row family
    (FFR-6B §6.3) — the renewable row's CX-6a refusal is what keeps nuclear
    out of the REC dual, not out of clean tiers. Wind and solar are the LP's
    zone columns and are counted by every region row directly, so only names
    beyond ``_RPS_ROW_BASE_FUELS`` resolve here, against ``FUEL_TYPE_MAP``
    (data-driven — the statutes genuinely differ: MN admits hydrogen and
    biomass, MI admits qualified CCS gas). An unknown fuel name is a hard
    error, never a silent drop.

    A region's qualifying spec takes ONE of two forms (SCN-WS2a, the
    federal CES target row — plan §3 WS-2 item 1):

    * a **fuel-name tuple** (every state statute): the region credits each
      qualifying generator's MWh at 1.0 — an indicator coefficient;
    * an **``(n_gen,)`` float vector** of per-generator credit fractions in
      ``[0, 1]`` (``policy.federal_ces.unit_credit_fractions`` — the SAME
      crediting rule the premium path pays, in both ``clean_capture`` and
      ``cesa_ci`` modes, so a CCS unit credits 0.95 and an unabated unit
      0): the region credits generator ``g`` at ``vector[g]``. A generator
      with a zero fraction adds no column. The vector must be aligned with
      ``fleet`` (``len == n_gen``), finite and within ``[0, 1]`` — any
      other shape or value is a hard error, because a silently misaligned
      crediting vector would credit the wrong units.

    Both forms are zone-masked identically (below). The coefficient a
    vector-form region puts on each resolved column is returned separately
    by :func:`_resolve_clean_region_gen_coeff`, so the tuple-form path —
    every MISO keeper's — stays byte-identical (the ones vector).

    ``eligible_zone_mask`` is the SAME ``(K, n_zones)`` bool mask the row
    builder applies to each region's wind/solar columns: a generator resolves
    into region ``r``'s index set only when its fuel qualifies AND its zone is
    in ``mask[r]``. The mask is mandatory — resolving by fuel alone across the
    whole fleet let Michigan's East-only row (MCL 460.1029, in-state systems
    only) be satisfied by MISO-South nuclear, defeating the row's own cited
    statutory basis (ARM3-FIX; the finding is
    ``docs/handoffs/arm3-clean-row-horizon-2026-08-09.md`` §3). Filtering
    happens here, at index construction, so the row builder stays a pure
    column-append (rule 2 [R-VECTOR] — no hour loops, no per-hour masking).

    Returns one index array (or ``None`` when no such in-mask generator
    exists in the fleet) per region, aligned with ``region_fuels``.
    """
    fuel_idx = np.asarray(fleet.fuel_type_idx)
    zone_idx = np.asarray(fleet.zone_idx, dtype=int)
    mask = np.asarray(eligible_zone_mask, dtype=bool)
    if mask.shape[0] != len(region_fuels):
        raise ValueError(
            f"clean-tier region axis mismatch: eligible_zone_mask has "
            f"{mask.shape[0]} region rows but region_fuels has "
            f"{len(region_fuels)} entries — the qualifying sets and the zone "
            "mask must describe the same regions in the same order"
        )
    # (K, n_gen): generator g is zone-eligible for region r. One gather, no
    # per-region zone loop.
    gen_in_mask = mask[:, zone_idx]
    out: "list[np.ndarray | None]" = []
    for r, fuels in enumerate(region_fuels):
        if isinstance(fuels, np.ndarray):
            # Vector form: per-generator crediting fractions (the federal
            # CES target row). Zero-fraction generators add no column.
            vec = _validate_credit_vector(fuels, fuel_idx.shape[0], r)
            gidx = np.flatnonzero((vec > 0.0) & gen_in_mask[r])
            out.append(gidx if gidx.size else None)
            continue
        extra = [f for f in fuels if f not in _RPS_ROW_BASE_FUELS]
        unknown = sorted(f for f in extra if f not in FUEL_TYPE_MAP)
        if unknown:
            raise ValueError(
                f"unknown clean-tier qualifying fuel name(s) {unknown}: every "
                "entry must resolve against FUEL_TYPE_MAP"
            )
        codes = np.array([FUEL_TYPE_MAP[f] for f in extra], dtype=int)
        gidx = np.flatnonzero(np.isin(fuel_idx, codes) & gen_in_mask[r])
        out.append(gidx if gidx.size else None)
    return out


def _validate_credit_vector(vec, n_gen: int, region: int) -> np.ndarray:
    """Return a validated ``(n_gen,)`` float crediting vector, or raise.

    The vector-form qualifying spec of :func:`_resolve_clean_region_gen_idx`
    is per-generator data that must line up with the fleet the LP is built
    on: a wrong length is a misaligned fleet (the P0→P1 fleet swap keeps
    ``n_gen``, so a mismatch is a wiring error, never a benign one); a
    non-finite or out-of-``[0, 1]`` entry is not a credit fraction.
    """
    out = np.asarray(vec, dtype=float).reshape(-1)
    if out.shape[0] != n_gen:
        raise ValueError(
            f"clean-tier region {region}: crediting vector has {out.shape[0]} "
            f"entries but the fleet has {n_gen} generators — a per-generator "
            "credit vector must be built from the SAME fleet the LP solves on"
        )
    if not np.all(np.isfinite(out)) or out.min() < 0.0 or out.max() > 1.0:
        raise ValueError(
            f"clean-tier region {region}: crediting vector entries must be "
            "finite fractions in [0, 1]"
        )
    return out


def _resolve_clean_region_gen_coeff(
    region_fuels: "tuple[tuple[str, ...] | np.ndarray, ...]",
    region_gen_idx: "list[np.ndarray | None]",
) -> "list[np.ndarray | None]":
    """Return each region's per-column coefficients for its resolved generators.

    Aligned entry-for-entry with ``region_gen_idx`` (the output of
    :func:`_resolve_clean_region_gen_idx` on the same ``region_fuels``):
    ``None`` for a fuel-name-tuple region (indicator coefficients — the
    builder's unchanged ones vector), and ``vector[gidx]`` for a vector-form
    region, so the row carries the crediting fraction itself on every
    resolved generator column. Pure indexing; validation happened at
    resolution.
    """
    out: "list[np.ndarray | None]" = []
    for spec, gidx in zip(region_fuels, region_gen_idx):
        if isinstance(spec, np.ndarray) and gidx is not None:
            out.append(np.asarray(spec, dtype=float)[np.asarray(gidx, dtype=int)])
        else:
            out.append(None)
    return out


def _build_rps_region_rows(
    layout: VariableLayout,
    eligible_zone_mask: np.ndarray,
    obligation_frac: np.ndarray,
    demand: np.ndarray,
    acp_k0: int = 0,
    region_gen_idx: "list[np.ndarray | None] | None" = None,
    region_gen_coeff: "list[np.ndarray | None] | None" = None,
) -> tuple[sp.csr_matrix, np.ndarray]:
    """Return the K per-region annual RPS rows and their lower bounds.

    The K-row generalization of :func:`_build_rps_row` (FFR-7B Arm 2 /
    FFR-6B §3): one annual inequality per compliance region ``r``::

        sum_{z in eligible_zones(r)} sum_t (W[z,t] + S[z,t])
            + sum_t ACP_r[t]  (+ sum_{g in region_gen_idx[r]} sum_t P[g,t])
        >=  sum_z obligation_frac[r, z] * sum_t demand[z, t]

    Each region draws only on the certificates its statute admits (the
    zone-mask filter on the same arange column expression the single row
    uses — rule 2 [R-VECTOR]: the only Python loop is over K <= 6 regions,
    the same shape as ``_build_mass_cap_rows``' loop over caps) and escapes
    through its OWN ACP column (region-major slot ``acp_k0 + r`` of the
    layout's ACP block), so each row's dual is that compliance market's REC
    price, capped at its own ACP. ``K = 1, mask = all zones`` reproduces the
    single ISO-wide row byte-identically — proven by regression test
    (``tests/unit/policy/test_rps.py``), not asserted.

    THE ROWS' ONLY OUTPUT IS A PRICE. E-1 never acquires a build limb
    (FFR-6B §5.3): a force-build limb would stack against the FFR-5E
    procurement channel — the rule-19 [R-ONE-MECH] failure FFR-5B refused.

    Args:
        layout: Variable layout describing the column structure.
        eligible_zone_mask: ``(K, n_zones)`` bool LHS mask — where region
            ``r``'s certificates may be generated.
        obligation_frac: ``(K, n_zones)`` float RHS weights — within-zone
            obligated load share times the region's target.
        demand: Zonal demand ``(n_zones, T)`` in MW.
        acp_k0: First region-major ACP slot this family occupies (0 for the
            renewable family; the clean-tier family stacks after it).
        region_gen_idx: Optional per-region thermal-block generator index
            arrays (statute-qualifying non-W/S classes — the clean-tier
            family's nuclear/hydro/etc. columns). Each region's indices must
            already be restricted to its eligible zones — the resolver
            (:func:`_resolve_clean_region_gen_idx`) takes the same
            ``eligible_zone_mask`` this builder applies to the W/S columns,
            so a row's generator credit is in-mask exactly as its VRE credit
            is (ARM3-FIX). ``None`` entries add no generator columns for
            that region.
        region_gen_coeff: Optional per-region coefficient arrays aligned
            with ``region_gen_idx`` (:func:`_resolve_clean_region_gen_coeff`):
            region ``r``'s generator columns carry ``coeff[r][j]`` instead
            of ``+1`` — the federal CES target row's per-generator credit
            fraction (a CCS unit at 0.95). ``None`` (or a ``None`` entry)
            keeps the ``+1`` indicator, byte-identical to before.

    Returns:
        Tuple ``(rows, rhs)``: a ``(K, total_columns)`` CSR block and the
        ``(K,)`` lower bounds.
    """
    T = layout.T  # T: number of hours
    vph = layout.vars_per_hour
    hours = np.arange(T)[:, np.newaxis]  # t: hour index
    mask = np.asarray(eligible_zone_mask, dtype=bool)
    frac = np.asarray(obligation_frac, dtype=float)
    k_regions = mask.shape[0]
    zone_annual = np.asarray(demand, dtype=float).sum(axis=1)  # (n_zones,)

    row_idx_groups: list[np.ndarray] = []
    col_groups: list[np.ndarray] = []
    data_groups: list[np.ndarray] = []
    for r in range(k_regions):  # r: compliance region (K <= 6, never hours)
        zones_r = np.flatnonzero(mask[r])  # z: eligible zone indices
        wind_cols = (hours * vph + layout._w_off + zones_r).ravel()
        solar_cols = (hours * vph + layout._s_off + zones_r).ravel()
        groups_r = [wind_cols, solar_cols]
        data_r = [np.ones(wind_cols.size), np.ones(solar_cols.size)]
        gidx = region_gen_idx[r] if region_gen_idx is not None else None
        if gidx is not None:
            gidx = np.asarray(gidx, dtype=int)  # g: qualifying generators
            if gidx.size:
                gen_cols = (hours * vph + layout._p_off + gidx).ravel()
                groups_r.append(gen_cols)
                coeff = region_gen_coeff[r] if region_gen_coeff is not None else None
                # Column order is hour-major (t outer, g inner), so the
                # per-generator coefficient tiles across the T hours.
                data_r.append(
                    np.ones(gen_cols.size)
                    if coeff is None
                    else np.tile(np.asarray(coeff, dtype=float), T)
                )
        # Region r's own ACP escape column (one per hour), +1 so paying its
        # ACP substitutes for physical certificates in THIS region only.
        acp_cols = np.arange(T) * vph + layout._rec_acp_off + acp_k0 + r
        groups_r.append(acp_cols)
        data_r.append(np.ones(acp_cols.size))
        cols_r = np.concatenate(groups_r)
        col_groups.append(cols_r)
        data_groups.append(np.concatenate(data_r))
        row_idx_groups.append(np.full(cols_r.size, r, dtype=int))

    cols = np.concatenate(col_groups)
    rows_idx = np.concatenate(row_idx_groups)
    block = sp.coo_matrix(
        (np.concatenate(data_groups), (rows_idx, cols)),
        shape=(k_regions, layout.total_columns),
    ).tocsr()
    rhs = frac @ zone_annual  # (K,)
    return block, rhs


def _build_mass_cap_rows(layout: VariableLayout, coeffs: np.ndarray) -> sp.csr_matrix:
    """Return the stacked emissions mass-cap constraint block (rule 2).

    ``coeffs`` is ``(k, n_gen)``: entry ``(r, g)`` is the row coefficient
    ``m[g] * emission_rate[g]`` on member generator ``g`` for cap ``r`` (the
    per-generator membership weight times its CO2 emission rate). Each row sums
    that coefficient over the generator's dispatch columns across all ``T``
    hours, enforcing ``sum_{g,t} coeffs[r,g] * P[g,t] <= cap_tons[r]``.

    Only thermal-block ``P`` columns are touched — import-node and inter-zone
    flow columns get a zero coefficient, because the cap is on *in-region*
    emissions and imported energy's emissions occur outside the capped region
    (plan §4; the leakage channel is thereby represented, not suppressed). The
    block is assembled in a single COO matrix, cloned from :func:`_build_rps_row`
    — the only Python loop is a short one over the ``k`` (<=2-3) caps, never over
    hours.
    """
    T = layout.T  # T: number of hours
    vph = layout.vars_per_hour
    hours = np.arange(T)  # t: hour index
    k = coeffs.shape[0]
    row_blocks, col_blocks, data_blocks = [], [], []
    for r in range(k):  # r: cap index — short loop over the caps, never hours
        gidx = np.flatnonzero(coeffs[r])  # g: member generators for cap r
        if gidx.size == 0:
            continue
        cols = (hours[:, np.newaxis] * vph + layout._p_off + gidx).ravel()
        data = np.tile(coeffs[r, gidx], T)
        row_blocks.append(np.full(cols.size, r, dtype=int))
        col_blocks.append(cols)
        data_blocks.append(data)
    if not col_blocks:
        return sp.csr_matrix((k, layout.total_columns))
    return sp.coo_matrix(
        (
            np.concatenate(data_blocks),
            (np.concatenate(row_blocks), np.concatenate(col_blocks)),
        ),
        shape=(k, layout.total_columns),
    ).tocsr()


def _build_hydro_rows(
    layout: VariableLayout,
    hydro_gen_idx: np.ndarray,
    hydro_monthly_energy: np.ndarray,
    hydro_month_index: np.ndarray,
    hydro_monthly_min: np.ndarray | None,
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Return the hydro monthly energy-budget rows and their bound vectors.

    Builds one row per ``(hydro generator, month)`` enforcing the
    inter-temporal energy budget::

        hydro_monthly_min[g, m] <= sum_{t in month m} P[g, t]
                                <= hydro_monthly_energy[g, m]

    so a reservoir picks *when* within a month to generate but not *how
    much* in total. The row's ``+1`` coefficients sit on the thermal-block
    columns of the hydro generators; the lower bound applies the run-of-river
    min-flow floor (zero when ``hydro_monthly_min`` is ``None``).

    The whole block is assembled in one ``coo_matrix`` from the
    ``(months x T)`` hour-to-month incidence -- each ``(g, t)`` pair drops a
    ``1`` into row ``g * n_months + month[t]`` -- so there is no Python loop
    over hours.

    Args:
        layout: Variable layout describing the column structure.
        hydro_gen_idx: Thermal-block indices of the hydro generators, shape
            ``(n_hydro,)``.
        hydro_monthly_energy: Monthly energy cap in MWh, shape
            ``(n_hydro, n_months)``.
        hydro_month_index: Month index (``0 <= m < n_months``) of each hour,
            shape ``(T,)``.
        hydro_monthly_min: Monthly minimum energy in MWh, shape
            ``(n_hydro, n_months)``, or ``None`` for a zero floor.

    Returns:
        Tuple ``(block, row_lower, row_upper)`` with ``block`` a CSR matrix
        of shape ``(n_hydro * n_months, layout.total_columns)``.
    """
    T = layout.T  # T: number of hours
    vph = layout.vars_per_hour
    gen_idx = np.asarray(hydro_gen_idx, dtype=int)  # (n_hydro,)
    month_index = np.asarray(hydro_month_index, dtype=int)  # (T,)
    energy = np.asarray(hydro_monthly_energy, dtype=float)
    n_hydro = gen_idx.size
    n_months = energy.shape[1]

    hours = np.arange(T)  # t: hour index
    g = np.arange(n_hydro)  # local hydro index

    # Row r = g * n_months + month[t]; column = hydro gen g's P slot in hour t.
    rows = (g[:, None] * n_months + month_index[None, :]).ravel()
    cols = (hours[None, :] * vph + layout._p_off + gen_idx[:, None]).ravel()
    data = np.ones(n_hydro * T, dtype=float)
    block = sp.coo_matrix(
        (data, (rows, cols)),
        shape=(n_hydro * n_months, layout.total_columns),
    ).tocsr()

    row_upper = energy.ravel()
    if hydro_monthly_min is None:
        row_lower = np.zeros(n_hydro * n_months, dtype=float)
    else:
        row_lower = np.asarray(hydro_monthly_min, dtype=float).ravel()
    return block, row_lower, row_upper


def _build_oil_budget_rows(
    layout: "VariableLayout",
    oil_gen_idx: np.ndarray,
    oil_monthly_budget: np.ndarray,
    oil_month_index: np.ndarray,
    gen_hour_coeff: np.ndarray | None = None,
    group_index: np.ndarray | None = None,
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Return oil-burn monthly inventory budget rows and bound vectors.

    Structurally identical to :func:`_build_hydro_rows`: one row per
    ``(row group, month)`` enforcing::

        0 <= sum_{g in group, t in month m} coeff[g, t] * P[g, t]
             <= oil_monthly_budget[group, m]

    When the budget binds in a cold-snap month, the constraint's dual
    (shadow price) IS the scarcity rent — the LP endogenously prices the
    marginal oil MWh at SRMC + shadow price, lifting the cleared LMP
    above the flat dual-fuel oil-parity cap (~$258) and producing >$300
    hours.

    Two callers share this builder:

    - The F923 monthly path (``fuel.py:load_oil_burn_budget``, oil-primary
      only): default ``gen_hour_coeff=None`` (coefficient 1, constrains
      dispatched MWh) and ``group_index=None`` (one row per generator).
    - The winter-fuel-inventory path
      (``winter_fuel_inventory.py:build_winter_fuel_budget``, Component A):
      ``gen_hour_coeff = heat_rate[g] * oil_switch_mask[g, t]`` so the row
      constrains oil energy INPUT (MMBtu) and, for dual-fuel units, only
      their exogenous oil-switch hours (gas-fired hours carry coeff 0 and
      are dropped); ``group_index`` pools the fleet into one shared-stock
      row per month.

    Args:
        layout: Variable layout describing the column structure.
        oil_gen_idx: Thermal-block indices of oil-capable generators,
            shape ``(n_oil,)``.
        oil_monthly_budget: Monthly budget cap, shape
            ``(n_groups, n_months)``, in MWh (coeff=1) or MMBtu
            (heat-rate-weighted coeff). ``np.inf`` leaves a month
            unconstrained.
        oil_month_index: Month index (``0 <= m < n_months``) of each
            hour, shape ``(T,)``.
        gen_hour_coeff: Optional per-generator (``(n_oil,)``) or
            per-generator-hour (``(n_oil, T)``) constraint coefficient.
            ``None`` uses 1.0 (dispatched MWh). Zero entries are dropped so
            the matrix stays sparse.
        group_index: Optional per-generator row-group index, shape
            ``(n_oil,)``. ``None`` gives one row per generator (backward
            compatible); a constant maps every generator into one pooled
            fleet row.

    Returns:
        Tuple ``(block, row_lower, row_upper)`` with ``block`` a CSR
        matrix of shape ``(n_groups * n_months, layout.total_columns)``.
    """
    T = layout.T
    vph = layout.vars_per_hour
    gen_idx = np.asarray(oil_gen_idx, dtype=int)
    month_index = np.asarray(oil_month_index, dtype=int)
    budget = np.asarray(oil_monthly_budget, dtype=float)
    n_oil = gen_idx.size
    n_months = budget.shape[1]

    # Row group per constrained generator: one row per generator by default
    # (F923 per-plant caller), or a shared group that pools the fleet stock.
    if group_index is None:
        group = np.arange(n_oil)
    else:
        group = np.asarray(group_index, dtype=int)
    n_groups = int(group.max()) + 1 if group.size else 0

    hours = np.arange(T)
    rows = (group[:, None] * n_months + month_index[None, :]).ravel()
    cols = (hours[None, :] * vph + layout._p_off + gen_idx[:, None]).ravel()
    if gen_hour_coeff is None:
        data = np.ones(n_oil * T, dtype=float)
    else:
        coeff = np.asarray(gen_hour_coeff, dtype=float)
        if coeff.ndim == 1:
            coeff = np.broadcast_to(coeff[:, None], (n_oil, T))
        data = np.ascontiguousarray(coeff).ravel()
        # Drop zero-coefficient entries (dual-fuel gas-fired hours) so the
        # constraint matrix does not carry ~n_oil*T explicit zeros.
        nz = data != 0.0
        rows, cols, data = rows[nz], cols[nz], data[nz]
    block = sp.coo_matrix(
        (data, (rows, cols)),
        shape=(n_groups * n_months, layout.total_columns),
    ).tocsr()

    row_upper = budget.ravel()
    row_lower = np.zeros(n_groups * n_months, dtype=float)
    return block, row_lower, row_upper


def _build_import_node_rows(
    layout: VariableLayout,
    node_gen_idx: np.ndarray,
    month_index: np.ndarray,
    monthly_lo: np.ndarray,
    monthly_hi: np.ndarray,
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Return the priced import-node monthly net-throughput band rows.

    Builds **one row per month** pinning the priced node's net interchange to
    the measured EIA-930 schedule (boundary-flow calibration constraint —
    Aurora/PLEXOS/GridView historical-validation practice; CLAUDE.md rule #11)::

        monthly_lo[m] <= sum_{t in month m} sum_{g in node} P[g, t] <= monthly_hi[m]

    The ``node`` columns are every import tranche (``P >= 0``, injects into the
    external zone) **and** every export sink (``P <= 0``, withdraws), so the
    signed sum is the node's *net* import (positive) / export (negative) energy
    — exactly the negative of the measured export-positive net interchange. The
    band keeps the priced tranches free to set the marginal price *within* the
    monthly envelope (the LP still chooses which hours/tranches clear), while the
    monthly *level* tracks the metered schedule instead of the static economic
    ladder's near-flat clearing. ``monthly_lo == monthly_hi`` makes it an
    equality (a hard monthly pin); a non-zero band half-width leaves price /
    feasibility room.

    The whole block is assembled in one ``coo_matrix`` from the hour-to-month
    map — each ``(g, t)`` pair drops a ``+1`` into row ``month[t]`` — so there
    is no Python loop over hours (CLAUDE.md rule #2).

    Args:
        layout: Variable layout describing the column structure.
        node_gen_idx: Thermal-block indices of the import-node pseudo-generators
            (import tranches + export sinks), shape ``(n_node,)``.
        month_index: Month index (``0 <= m < n_months``) of each hour, shape
            ``(T,)``.
        monthly_lo: Monthly net-import lower bound in MWh, shape ``(n_months,)``.
        monthly_hi: Monthly net-import upper bound in MWh, shape ``(n_months,)``.

    Returns:
        Tuple ``(block, row_lower, row_upper)`` with ``block`` a CSR matrix of
        shape ``(n_months, layout.total_columns)``.
    """
    T = layout.T  # T: number of hours
    vph = layout.vars_per_hour
    gen_idx = np.asarray(node_gen_idx, dtype=int)  # (n_node,)
    month_index = np.asarray(month_index, dtype=int)  # (T,)
    n_node = gen_idx.size
    n_months = np.asarray(monthly_lo).shape[0]

    hours = np.arange(T)  # t: hour index
    # Row r = month[t] (same for every node gen); column = node gen g's P slot
    # in hour t. Every (g, t) pair contributes +1 to its month's net total.
    rows = np.broadcast_to(month_index[None, :], (n_node, T)).ravel()
    cols = (hours[None, :] * vph + layout._p_off + gen_idx[:, None]).ravel()
    data = np.ones(n_node * T, dtype=float)
    block = sp.coo_matrix(
        (data, (rows, cols)),
        shape=(n_months, layout.total_columns),
    ).tocsr()
    return (
        block,
        np.asarray(monthly_lo, dtype=float),
        np.asarray(monthly_hi, dtype=float),
    )


def _build_storage_daily_cycle_rows(
    layout: VariableLayout, cycle_hours: int
) -> sp.csr_matrix:
    """Daily SOC-anchor equality rows: ``SOC[s, d*H] - SOC[s, 0] = 0``.

    One row per storage unit and per interior day boundary ``d = 1 ..
    n_days-1`` (where ``H = cycle_hours`` and ``n_days = T // H``). Pinning
    every day-start SOC to the unit's hour-0 level forces each day to be
    energy-neutral, so storage cannot bank cheap energy across days -- the
    standard daily-cycling cap that bounds perfect-foresight arbitrage to
    within-day spreads. Returns a zero-row matrix when fewer than two whole
    days fit in the horizon.
    """
    n_storage = layout.n_storage
    T = layout.T
    vph = layout.vars_per_hour
    n_days = T // cycle_hours
    if n_storage == 0 or n_days < 2:
        return sp.csr_matrix((0, layout.total_columns))

    units = np.arange(n_storage)
    boundaries = np.arange(1, n_days) * cycle_hours  # interior day starts
    n_b = boundaries.size

    # Row r = s*n_b + j couples SOC[s, boundaries[j]] (+1) to SOC[s, 0] (-1).
    rows = np.repeat(np.arange(n_storage * n_b), 2)
    soc0 = layout._soc_off + units  # (n_storage,): each unit's SOC[s, 0] column
    bcols = (
        boundaries[None, :] * vph + layout._soc_off + units[:, None]
    )  # (n_storage, n_b): SOC[s, d*H] columns
    cols = np.empty(n_storage * n_b * 2, dtype=int)
    cols[0::2] = bcols.ravel()
    cols[1::2] = np.repeat(soc0, n_b)
    data = np.tile([1.0, -1.0], n_storage * n_b)
    return sp.coo_matrix(
        (data, (rows, cols)),
        shape=(n_storage * n_b, layout.total_columns),
    ).tocsr()


def _build_storage_alloc_rows(
    layout: VariableLayout,
    batt_idx: np.ndarray,
    share: np.ndarray,
    da_frac: float,
) -> sp.csr_matrix:
    """Per-day DA charge-allocation floor rows (``caiso_charge_allocation_schedule``).

    The M1 belly allocation mechanism (owner-granted caiso-103 ask, executed
    caiso-104): the ask's per-day scheduled-volume variable ``S[d] >= 0`` with
    ``Chg_fleet[h] >= alloc_share[hod] x S[d]`` (24 floors/day) and
    ``sum_h Chg_fleet[h] <= S[d] / da_frac`` (1 cap/day) is eliminated exactly
    — ``S[d]`` is costless and appears only in those rows, so the LP always
    picks the minimal feasible ``S[d] = da_frac x sum_h Chg_fleet[h]`` and the
    Fourier-Motzkin projection onto the ``Chg`` columns is::

        sum_{s in batt} Chg[s, h]
          - share[hod(h)] x da_frac x sum_{h' in day} sum_{s in batt} Chg[s, h']
          >= 0            (one row per day-hour with share > 0)

    Identical feasible region and identical energy-balance duals, with no new
    columns (the per-hour ``VariableLayout`` invariant is preserved). Every
    charged MWh buys the measured allocation bundle across the day's shape
    except the bounded free RT-margin slice ``1 - da_frac``; a zero-charge day
    stays feasible (nothing is forced — volume-holding by construction).

    ``share`` is the hod-mapped ``(T,)`` profile (identical across days by
    construction — :func:`market_sim.model.storage
    .caiso_charge_allocation_params`); hours with ``share == 0`` (the measured
    evening/late support) carry no row. The per-day coefficient block is
    identical for every day, so the year block is a single
    ``kron(eye(n_days), day_block)`` — no Python loop over hours (rule #2).

    Returns a CSR block of shape ``(n_active_hods * n_days, total_columns)``
    (zero rows when there are no batteries or the shape is empty); row bounds
    are ``[0, inf)`` — appended by :func:`build_constraints`.
    """
    T = layout.T
    vph = layout.vars_per_hour
    batt_idx = np.asarray(batt_idx, dtype=int)
    n_days = T // 24
    if batt_idx.size == 0 or n_days == 0:
        return sp.csr_matrix((0, layout.total_columns))
    share24 = np.asarray(share, dtype=float)[:24]
    act = np.flatnonzero(share24 > 0.0)  # active hods (the measured support)
    if act.size == 0:
        return sp.csr_matrix((0, layout.total_columns))
    nb = batt_idx.size
    # Column pattern of one day: every battery Chg column of each in-day hour.
    base_cols = (
        np.arange(24)[:, None] * vph + layout._chg_off + batt_idx[None, :]
    ).ravel()  # (24 * nb,)
    hprime = np.repeat(np.arange(24), nb)  # in-day hour of each entry
    # Row k (active hod act[k]): +1 on hour act[k]'s own Chg columns,
    # -share[act[k]] x da_frac on every in-day Chg column (including its own,
    # so the diagonal coefficient is 1 - share x da_frac).
    data = (hprime[None, :] == act[:, None]).astype(float) - (
        share24[act][:, None] * float(da_frac)
    )  # (n_act, 24 * nb)
    rows = np.repeat(np.arange(act.size), 24 * nb)
    cols = np.tile(base_cols, act.size)
    day_block = sp.coo_matrix(
        (data.ravel(), (rows, cols)), shape=(act.size, 24 * vph)
    ).tocsr()
    block = sp.kron(sp.eye(n_days, format="csr"), day_block, format="csr")
    if block.shape[1] < layout.total_columns:
        # Horizon tail shorter than a whole day (never in the 8760 frame):
        # pad zero columns so the block conforms.
        block = sp.hstack(
            [
                block,
                sp.csr_matrix((block.shape[0], layout.total_columns - block.shape[1])),
            ],
            format="csr",
        )
    return block


def _build_dis_tranche_rows(
    layout: VariableLayout,
    arm_batt_idx: np.ndarray,
) -> sp.csr_matrix:
    """Storage discharge-tranche decomposition rows (ERCOT ercot_storage_rt_offer_surface).

    One equality per (armed battery unit ``a``, hour ``t``)::

        Dis[s_a, t] − Σ_k DisT[a, k, t] = 0

    tying each armed battery's single discharge column (its unchanged total —
    energy balance, SOC dynamics, power-cap bound and the AS→energy deployment
    floor all ride Dis[s,t] exactly as before) to the sum of its K priced
    tranche columns. The tranches carry the measured rising offer ladder in the
    objective (:func:`build_cost_vector`) and their widths cap each rung
    (:func:`build_variable_bounds`), so the marginal cost of the unit's last
    discharged MW follows the ladder while the base column keeps its meaning —
    the standard piecewise-linear-cost decomposition on one variable.

    Inserted after the SOC/cycle/alloc storage rows and before the
    interface/hydro/RPS/reserve tail, so the front-anchored energy-balance
    duals and the end-anchored RPS/reserve duals keep their positions. Fully
    vectorized — the loop is over the O(1) tranche count, never the 8760 hours
    (rule #2). Returns a zero-row matrix when no units are armed.

    Args:
        layout: Variable layout (``dis_tranche_k`` = K, ``_dis_tranche_off``).
        arm_batt_idx: ``(n_arm,)`` storage-unit indices of the armed batteries.

    Returns:
        CSR block of shape ``(n_arm * T, total_columns)``; row bounds are 0.
    """
    T = layout.T
    vph = layout.vars_per_hour
    k = layout.dis_tranche_k
    arm = np.asarray(arm_batt_idx, dtype=int)
    n_arm = arm.size
    if n_arm == 0 or k == 0:
        return sp.csr_matrix((0, layout.total_columns))

    # Row r = a*T + t. Base +Dis[s_a,t]; tranche −DisT[a,k,t] for each k.
    a_arr = np.repeat(np.arange(n_arm), T)  # (n_arm*T,)
    t_arr = np.tile(np.arange(T), n_arm)  # (n_arm*T,)
    s_arr = arm[a_arr]  # storage-unit index of each row's armed battery
    base_rows = np.arange(n_arm * T)
    base_cols = t_arr * vph + layout._dis_off + s_arr
    base_data = np.ones(n_arm * T)

    tr_rows = np.repeat(base_rows, k)
    kk = np.tile(np.arange(k), n_arm * T)
    a_rep = np.repeat(a_arr, k)
    t_rep = np.repeat(t_arr, k)
    tr_cols = t_rep * vph + layout._dis_tranche_off + a_rep * k + kk
    tr_data = -np.ones(n_arm * T * k)

    rows = np.concatenate([base_rows, tr_rows])
    cols = np.concatenate([base_cols, tr_cols])
    data = np.concatenate([base_data, tr_data])
    return sp.coo_matrix(
        (data, (rows, cols)), shape=(n_arm * T, layout.total_columns)
    ).tocsr()


def _build_interface_rows(
    layout: VariableLayout,
    interface_groups: list[tuple[np.ndarray, float | np.ndarray, bool]],
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Aggregate interface-limit rows: one per group per hour.

    A real interface's *simultaneous* transfer limit is smaller than the sum
    of its component paths' individual ratings (CAISO's WECC Maximum Import
    Capability ~8.3 GW vs Path 66 + Path 46 ≈ 15.4 GW). Each group caps the
    signed sum of its member links' ``Flow`` at ``cap_mw`` -- with a symmetric
    ``-cap_mw`` floor when bidirectional, so the reverse (export) direction is
    capped too. The component links keep their own per-link TTC bounds; this
    row binds only when several would otherwise load simultaneously past the
    aggregate rating.

    A group's ``cap_mw`` may be a scalar (a static rating) **or** an ``(T,)``
    array (a per-hour limit, e.g. the CAISO measured corridor deliverability
    envelope, which tightens midday). A one-sided group (``bidirectional`` False)
    caps only the upper/positive-flow direction and leaves the lower bound at
    ``-inf`` — so an import-direction corridor cap never forces the reverse
    (export) flow, which keeps the link's own physical TTC.

    Rows are hour-major (group-minor within an hour) and replicated across all
    ``T`` hours with a single Kronecker product -- no Python loop over hours.

    Args:
        layout: Variable layout describing the column structure.
        interface_groups: list of ``(link_idx, cap_mw, bidirectional)`` — or
            ``(link_idx, cap_mw, bidirectional, lower_cap_mw)`` or
            ``(link_idx, cap_mw, bidirectional, lower_cap_mw, signs)`` — where
            ``link_idx`` is the array of member link indices (into the flow
            block), ``cap_mw`` the aggregate upper limit in MW (scalar or
            ``(T,)``), ``bidirectional`` whether to also floor the signed sum at
            ``-cap_mw``, the optional ``lower_cap_mw`` (scalar or ``(T,)``)
            an explicit reverse-direction floor ``-lower_cap_mw`` that overrides
            ``bidirectional`` (for an asymmetric import/export corridor cap;
            ``None`` inside a 4/5-tuple falls back to ``bidirectional``), and
            the optional ``signs`` a ``(len(link_idx),)`` array of ±1
            coefficients orienting each member link into the group's positive
            flow direction (absent → all ``+1``, the legacy shared-orientation
            behaviour; used by the per-zone MISO CIL/CEL groups, whose member
            links do not share an orientation).

    Returns:
        Tuple ``(block, row_lower, row_upper)`` with ``block`` a CSR matrix of
        shape ``(n_groups * T, total_columns)``.
    """
    T = layout.T
    vph = layout.vars_per_hour
    n_groups = len(interface_groups)

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    # (T, n_groups) so the row-major ravel matches the kron's hour-major,
    # group-minor row order; a scalar cap broadcasts across all hours.
    upper_2d = np.empty((T, n_groups), dtype=float)
    lower_2d = np.empty((T, n_groups), dtype=float)
    for gi, group in enumerate(interface_groups):
        # A group is a 3-tuple ``(link_idx, cap, two_way)`` or a 4-tuple
        # ``(link_idx, cap, two_way, lower_cap)`` where ``lower_cap`` (scalar or
        # ``(T,)``) sets an explicit reverse-direction bound (``flow >=
        # -lower_cap``) — used for an asymmetric corridor whose import ceiling and
        # export ceiling differ (CAISO per-hub: p95 net import up, p95 net export
        # down). Absent, the reverse bound follows ``two_way`` (symmetric ``-cap``
        # or ``-inf``), so existing 3-tuple groups are byte-identical.
        link_idx, cap, two_way = group[0], group[1], group[2]
        lower_cap = group[3] if len(group) > 3 else None
        signs = group[4] if len(group) > 4 else None
        idx = np.asarray(link_idx, dtype=int)
        rows.extend([gi] * idx.size)
        cols.extend((layout._flow_off + idx).tolist())
        if signs is None:
            data.extend([1.0] * idx.size)
        else:
            data.extend(np.asarray(signs, dtype=float).tolist())
        cap_arr = np.broadcast_to(np.asarray(cap, dtype=float), (T,))
        upper_2d[:, gi] = cap_arr
        if lower_cap is not None:
            lower_2d[:, gi] = -np.broadcast_to(np.asarray(lower_cap, dtype=float), (T,))
        else:
            lower_2d[:, gi] = -cap_arr if two_way else -np.inf

    per_hour = sp.coo_matrix((data, (rows, cols)), shape=(n_groups, vph)).tocsr()
    # kron(eye(T), per_hour) tiles the per-hour coefficient block across all
    # hours; column hour-stride vph lands each link's flow in its own hour.
    block = sp.kron(sp.eye(T, format="csr"), per_hour, format="csr")
    return block, lower_2d.ravel(), upper_2d.ravel()


def _build_ramp_rows(
    layout: VariableLayout,
    fleet: FleetArrays,
    ramp_gen_idx: np.ndarray,
    ramp_group_col: np.ndarray,
    ramp_up_mw: np.ndarray,
    ramp_dn_mw: np.ndarray,
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Two-sided plant-group hourly ramp-envelope rows (``ramp_limits``).

    One row per ramp-constrained plant group per hour transition
    ``t = 1..T-1`` (no cyclic wrap — the Dec-31→Jan-1 seam carries no
    physics worth a coupling row) enforcing::

        -RD_eff[p,t] <= sum_{g in p} P[g,t] - sum_{g in p} P[g,t-1]
                     <= RU_eff[p,t]

    The envelope is a *plant* property, not a tranche property — tranches
    dispatch bang-bang within a plant while the trajectory belongs to the
    machine (same aggregation precedent as the per-gen reserve
    ``pergen_col`` grouping). ``RU``/``RD`` are the CAMPD-measured max
    observed 1-h deltas (``fleet.build_ramp_groups``), a physical-capability
    input in the same admissibility class as the measured min-stable loads
    (design doc §1.3).

    Availability-edge widening (feasibility guard): an outage onset forces
    ``dP = -P[t-1]`` regardless of any envelope, and a return/COD restores
    capacity in one hour. With ``cap[p,t] = sum_g pmax[g]*availability[g,t]``
    the bounds widen by exactly the capacity discontinuity the model itself
    imposes::

        RU_eff[p,t] = RU[p] + max(0, cap[p,t] - cap[p,t-1])
        RD_eff[p,t] = RD[p] + max(0, cap[p,t-1] - cap[p,t])

    Rows are hour-major (group-minor within an hour transition); the whole
    block is a single ``coo_matrix`` — no Python loop over hours (rule #2).

    Args:
        layout: Variable layout describing the column structure.
        ramp_gen_idx: Member thermal column indices, shape ``(n_members,)``.
        ramp_group_col: Group index of each member, shape ``(n_members,)``.
        ramp_up_mw: Per-group up-envelope in MW, shape ``(n_groups,)``.
        ramp_dn_mw: Per-group down-envelope in MW, shape ``(n_groups,)``.

    Returns:
        Tuple ``(block, row_lower, row_upper)`` with ``block`` a CSR matrix
        of shape ``(n_groups * (T-1), total_columns)``.
    """
    T = layout.T
    vph = layout.vars_per_hour
    gen_idx = np.asarray(ramp_gen_idx, dtype=int)
    group_col = np.asarray(ramp_group_col, dtype=int)
    ru = np.asarray(ramp_up_mw, dtype=float)
    rd = np.asarray(ramp_dn_mw, dtype=float)
    n_groups = ru.size

    # Coefficients: row r = (t-1)*n_groups + p holds +1 on each member's P
    # column at hour t and -1 at hour t-1. t runs 1..T-1; everything below is
    # (n_members, T-1) broadcast arithmetic raveled member-major then stacked.
    ts = np.arange(1, T)  # t: hour transitions 1..T-1
    row_block = (ts - 1)[None, :] * n_groups + group_col[:, None]  # (n_members, T-1)
    col_t = ts[None, :] * vph + layout._p_off + gen_idx[:, None]
    col_tm1 = (ts - 1)[None, :] * vph + layout._p_off + gen_idx[:, None]
    n_m = gen_idx.size
    rows = np.concatenate([row_block.ravel(), row_block.ravel()])
    cols = np.concatenate([col_t.ravel(), col_tm1.ravel()])
    data = np.concatenate([np.ones(n_m * (T - 1)), -np.ones(n_m * (T - 1))])
    block = sp.coo_matrix(
        (data, (rows, cols)),
        shape=(n_groups * (T - 1), layout.total_columns),
    ).tocsr()

    # Availability-edge widening: cap[p,t] via a (n_groups, n_gen) member map.
    member_map = sp.coo_matrix(
        (np.ones(n_m), (group_col, gen_idx)),
        shape=(n_groups, layout.n_gen),
    ).tocsr()
    cap = member_map @ (
        np.asarray(fleet.pmax, dtype=float)[:, None]
        * np.asarray(fleet.availability, dtype=float)[:, :T]
    )  # (n_groups, T)
    dcap = np.diff(cap, axis=1)  # (n_groups, T-1)
    ru_eff = ru[:, None] + np.maximum(0.0, dcap)
    rd_eff = rd[:, None] + np.maximum(0.0, -dcap)
    # Hour-major ravel to match row r = (t-1)*n_groups + p.
    return block, -rd_eff.T.ravel(), ru_eff.T.ravel()


def _build_local_capacity_rows(
    layout: VariableLayout,
    local_capacity_specs: list[tuple[np.ndarray, np.ndarray, float, np.ndarray]],
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Local-capacity (LCR-area) minimum-generation rows (``>=``, per hour).

    One row per covered LCR area per hour enforcing::

        sum_{g in area} P[g,t]
          + storage_frac * sum_{s in zone} (Dis[s,t] - Chg[s,t])
          >= rhs[t]

    the exact LP relaxation of a sub-zonal load-pocket split: the pocket's
    energy balance with its boundary import at the published study limit,
    minus the LMP separation (design doc §3). The RHS —
    ``max(0, share*zone_load[t] - import_cap)`` capped at 99.9% of in-area
    *thermal* capacity — is assembled by
    :func:`market_sim.data.local_capacity.build_local_capacity_specs` from
    published LCR study values only. The row's dual subsidizes in-area
    units' reduced costs without entering the zonal energy-balance dual —
    out-of-market (uplift-like) commitment, so the hub LMP benchmark is
    untouched.

    The per-hour pattern is identical across hours, so the block is one
    ``kron`` over an ``(n_areas, vars_per_hour)`` coefficient block — no
    Python loop over hours (rule #2). Rows are hour-major, area-minor.

    Args:
        layout: Variable layout describing the column structure.
        local_capacity_specs: Per-area ``(gen_idx, storage_idx, storage_frac,
            rhs_T)`` tuples; ``rhs_T`` has shape ``(T,)``.

    Returns:
        Tuple ``(block, row_lower, row_upper)`` with ``block`` a CSR matrix
        of shape ``(n_areas * T, total_columns)``; upper bounds are ``+inf``.
    """
    T = layout.T
    vph = layout.vars_per_hour
    n_areas = len(local_capacity_specs)

    rows: list[np.ndarray] = []
    cols: list[np.ndarray] = []
    data: list[np.ndarray] = []
    rhs_2d = np.empty((T, n_areas), dtype=float)  # hour-major ravel order
    for ai, (gen_idx, storage_idx, storage_frac, rhs_t) in enumerate(
        local_capacity_specs
    ):
        g_idx = np.asarray(gen_idx, dtype=int)
        rows.append(np.full(g_idx.size, ai))
        cols.append(layout._p_off + g_idx)
        data.append(np.ones(g_idx.size))
        s_idx = np.asarray(storage_idx, dtype=int)
        frac = float(storage_frac)
        if s_idx.size and frac > 0.0:
            # In-area share of the zone-aggregated storage: discharge helps
            # the pocket, charge deepens its need.
            rows.append(np.full(2 * s_idx.size, ai))
            cols.append(layout._dis_off + s_idx)
            cols.append(layout._chg_off + s_idx)
            data.append(np.full(s_idx.size, frac))
            data.append(np.full(s_idx.size, -frac))
        rhs_2d[:, ai] = np.asarray(rhs_t, dtype=float)[:T]

    per_hour = sp.coo_matrix(
        (np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
        shape=(n_areas, vph),
    ).tocsr()
    block = sp.kron(sp.eye(T, format="csr"), per_hour, format="csr")
    return block, rhs_2d.ravel(), np.full(n_areas * T, np.inf)


def _build_gen_group_cap_rows(
    layout: VariableLayout,
    gen_idx: np.ndarray,
    cap_t: np.ndarray,
    storage_idx: np.ndarray | None = None,
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Hourly generation-group ceiling rows (``<=``, one row per hour).

    One row per hour enforcing::

        sum_{g in group} P[g,t]
          + sum_{s in storage group} (Dis[s,t] - Chg[s,t]) <= cap_t[t]

    — the generic fleet-level deliverability ceiling. First (only) user: the
    hydro hourly deliverability envelope (``config.hydro_dispatch_envelope``),
    where ``cap_t`` is the measured per-(month × hod) percentile of EIA-930
    ``NG: WAT`` (:func:`market_sim.data.eia_loader.measured_hydro_hourly_envelope`)
    bounding the budget LP's perfect-foresight hoarding of the monthly hydro
    energy into the top price hours. ``storage_idx`` carries the
    pumped-storage units for BAs whose ``NG: WAT`` includes PS net output
    (CISO reports no separate PS series), so the capped model quantity is
    like-for-like with the measured series: conventional hydro plus PS net
    discharge. A pumping hour (Chg > 0) *loosens* the row, exactly as pumping
    load lowers the measured WAT.

    The per-hour pattern is identical across hours, so the block is one
    ``kron`` over a ``(1, vars_per_hour)`` coefficient row — no Python loop
    over hours (rule #2). Rows are hour-major.

    Args:
        layout: Variable layout describing the column structure.
        gen_idx: Member generator column indices, shape ``(n_members,)``.
        cap_t: Per-hour ceiling in MW, shape ``(T,)``.
        storage_idx: Optional member storage unit indices whose net discharge
            (``Dis - Chg``) counts against the ceiling.

    Returns:
        Tuple ``(block, row_lower, row_upper)`` with ``block`` a CSR matrix of
        shape ``(T, total_columns)``; lower bounds are ``-inf``.
    """
    T = layout.T
    g_idx = np.asarray(gen_idx, dtype=int)
    cols = [layout._p_off + g_idx]
    data = [np.ones(g_idx.size)]
    if storage_idx is not None:
        s_idx = np.asarray(storage_idx, dtype=int)
        if s_idx.size:
            cols.append(layout._dis_off + s_idx)
            data.append(np.ones(s_idx.size))
            cols.append(layout._chg_off + s_idx)
            data.append(-np.ones(s_idx.size))
    cols_all = np.concatenate(cols)
    data_all = np.concatenate(data)
    per_hour = sp.coo_matrix(
        (data_all, (np.zeros(cols_all.size, dtype=int), cols_all)),
        shape=(1, layout.vars_per_hour),
    ).tocsr()
    block = sp.kron(sp.eye(T, format="csr"), per_hour, format="csr")
    upper = np.asarray(cap_t, dtype=float)[:T]
    return block, np.full(T, -np.inf), upper


def _build_posture_energy_rows(
    layout: VariableLayout,
    posture_gen_idx: np.ndarray,
    posture_col: np.ndarray,
    posture_mlf: np.ndarray,
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Build the STANDALONE energy-only commitment-posture rows (ERCOT).

    The reserve-decoupled half of the pooled-linear commitment-posture lever
    (design note ``docs/multi-iso/miso-scarcity-posture-design-2026-07.md`` §A;
    ERCOT port ``docs/handoffs/ercot-commitment-thinness-2026-07.md``). The
    MISO/CAISO/PJM posture re-anchors a pergen RESERVE pool
    (:func:`_build_reserve_rows_pergen`), but ERCOT runs a fleet-wide ORDC
    co-opt with no pergen substrate, so this builds only the energy-side rows on
    the posture ``U``/``SU`` columns and leaves ERCOT's reserve design untouched
    (rule 19 — one mechanism, energy-side commitment friction).

    Per postured pool ``p`` (``0..q-1``; members mapped by ``posture_col``),
    three row families over the ``P`` and ``U``/``SU`` columns, all vectorized
    (no hour loop):

    * **Energy headroom** ``sum_{members j of p} P[g_j,t] − U[p,t] <= 0`` — a
      pool cannot dispatch more than the capacity it keeps online (``q*T`` rows).
    * **Min-load coupling** ``sum_{members} P − mlf_p·U[p,t] >= 0`` for pools
      with measured ``mlf_p > 0`` — being online costs min-load energy at the
      committed band (``q_mlf*T`` rows). Binds only capacity the LP itself keeps
      online; NOT a floor (forces no exogenous energy, design note §A window).
    * **Startup counting**, cyclic ``U[p,t] − U[p,t−1] − SU[p,t] <= 0`` — re-timing
      energy pays a real start (``q*T`` rows; SU cost enters build_cost_vector).

    Returns one CSR block ``[headroom | min-load | startup]`` with its lower/upper
    bound vectors, inserted before the mass_cap/RPS/reserve tail so the front
    energy-balance and the end-anchored reserve/RPS duals keep their row indices.
    """
    gidx = np.asarray(posture_gen_idx, dtype=int)
    col = np.asarray(posture_col, dtype=int)
    mlf = np.asarray(posture_mlf, dtype=float)
    q = int(mlf.size)
    T = layout.T
    vph = layout.vars_per_hour
    u_arange = layout._posture_u_off + np.arange(q)

    blocks: list[sp.csr_matrix] = []
    lowers: list[np.ndarray] = []
    uppers: list[np.ndarray] = []

    # (a) Energy headroom: sum_members P[g] − U[p] <= 0, one row per pool-hour.
    hr_per_hour = sp.coo_matrix(
        (
            np.concatenate([np.ones(gidx.size), -np.ones(q)]),
            (
                np.concatenate([col, np.arange(q)]),
                np.concatenate([layout._p_off + gidx, u_arange]),
            ),
        ),
        shape=(q, vph),
    ).tocsr()
    blocks.append(sp.kron(sp.eye(T, format="csr"), hr_per_hour, format="csr"))
    lowers.append(np.full(q * T, -np.inf))
    uppers.append(np.zeros(q * T))

    # (b) Min-load coupling on pools with measured mlf > 0: sum_members P − mlf·U
    #     >= 0. Mirrors the (a) block of :func:`_build_reserve_rows_pergen`.
    m_sel = np.flatnonzero(mlf > 0.0)
    if m_sel.size:
        pool_to_row = np.full(q, -1, dtype=int)
        pool_to_row[m_sel] = np.arange(m_sel.size)
        mem_row = pool_to_row[col]
        mem_ok = mem_row >= 0
        ml_per_hour = sp.coo_matrix(
            (
                np.concatenate([np.ones(int(mem_ok.sum())), -mlf[m_sel]]),
                (
                    np.concatenate([mem_row[mem_ok], np.arange(m_sel.size)]),
                    np.concatenate(
                        [
                            layout._p_off + gidx[mem_ok],
                            layout._posture_u_off + m_sel,
                        ]
                    ),
                ),
            ),
            shape=(m_sel.size, vph),
        ).tocsr()
        blocks.append(sp.kron(sp.eye(T, format="csr"), ml_per_hour, format="csr"))
        lowers.append(np.zeros(m_sel.size * T))
        uppers.append(np.full(m_sel.size * T, np.inf))

    # (c) Startup counting, cyclic: U[p,t] − U[p,t−1] − SU[p,t] <= 0 (same wrap
    #     convention as the storage SOC boundary — hour 0 links to hour T−1, so a
    #     year-crossing posture carries no free start). Mirrors block (b) there.
    d0 = sp.coo_matrix(
        (
            np.concatenate([np.ones(q), -np.ones(q)]),
            (
                np.concatenate([np.arange(q), np.arange(q)]),
                np.concatenate([u_arange, layout._posture_su_off + np.arange(q)]),
            ),
        ),
        shape=(q, vph),
    ).tocsr()
    d_prev = sp.coo_matrix(
        (-np.ones(q), (np.arange(q), u_arange)),
        shape=(q, vph),
    ).tocsr()
    shift_prev = sp.csr_matrix(
        (np.ones(T), (np.arange(T), (np.arange(T) - 1) % T)),
        shape=(T, T),
    )
    blocks.append(
        sp.kron(sp.eye(T, format="csr"), d0, format="csr")
        + sp.kron(shift_prev, d_prev, format="csr")
    )
    lowers.append(np.full(q * T, -np.inf))
    uppers.append(np.zeros(q * T))

    return (
        sp.vstack(blocks, format="csr"),
        np.concatenate(lowers),
        np.concatenate(uppers),
    )


def build_constraints(
    layout: VariableLayout,
    fleet: FleetArrays,
    demand: np.ndarray,
    incidence: np.ndarray | sp.spmatrix | None = None,
    storage_zone_idx: np.ndarray | None = None,
    eta_chg: np.ndarray | float | None = None,
    eta_dis: np.ndarray | float | None = None,
    rps_target: float | None = None,
    rps_eligible_fuels: tuple[str, ...] | None = None,
    rps_region_zone_mask: np.ndarray | None = None,
    rps_region_obligation_frac: np.ndarray | None = None,
    clean_region_zone_mask: np.ndarray | None = None,
    clean_region_obligation_frac: np.ndarray | None = None,
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
    coal_plant_budget: np.ndarray | None = None,
    coal_plant_gen_idx: np.ndarray | None = None,
    coal_plant_month_index: np.ndarray | None = None,
    coal_plant_gen_hour_coeff: np.ndarray | None = None,
    coal_plant_group_index: np.ndarray | None = None,
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
    reserve_requirement: np.ndarray | None = None,
    reserve_eligible: np.ndarray | None = None,
    reserve_storage_power_cap: np.ndarray | float | None = None,
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
    reserve_posture_pools: np.ndarray | None = None,
    reserve_posture_mlf: np.ndarray | None = None,
    reserve_pergen_ramp10: np.ndarray | None = None,
    reserve_pergen_col_pool: np.ndarray | None = None,
    reserve_balance_col_mask: np.ndarray | None = None,
    reserve_pergen_online_gated_cols: np.ndarray | None = None,
    reserve_pergen_pool_ramp10: np.ndarray | None = None,
    posture_gen_idx: np.ndarray | None = None,
    posture_col: np.ndarray | None = None,
    posture_mlf: np.ndarray | None = None,
    link_loss: np.ndarray | None = None,
    dis_tranche_arm_idx: np.ndarray | None = None,
    hydro_cascade: "HydroCascadeSpec | None" = None,
    row_offsets: dict | None = None,
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Assemble the LP constraint matrix and its row bound vectors.

    Two equality constraint families are built (``row_lower == row_upper``):

    * **Energy balance** -- ``n_zones`` rows per hour. For zone ``z`` and
      hour ``t`` the dispatched thermal, wind, solar, net storage, net
      transmission flow and load slack must equal ``demand[z, t]``. The
      per-hour pattern is identical across hours, so a single sparse block
      is replicated with ``scipy.sparse.kron`` -- no Python loop over hours.
    * **Storage SOC dynamics** -- ``T`` rows per storage unit (only when
      storage is present). Every hour ``t`` enforces
      ``SOC[s,t] - SOC[s,t-1] - eta_chg*Chg[s,t] + Dis[s,t]/eta_dis = 0``;
      hour ``0`` takes ``t-1`` to be the final hour ``T-1`` so the SOC
      trajectory is a closed cycle and hour ``0``'s charge/discharge are
      bound by the same dynamics as every other hour.

      **Perfect-foresight assumption.** Because the whole horizon (``T`` =
      8760 in a backcast) is solved as a single LP, storage is co-optimized
      against the entire year's prices at once -- it charges in the
      globally-cheapest hours and discharges in the globally-dearest hours
      the energy cap allows. A real operator has only ~day-ahead foresight,
      so this is an upper bound on realized arbitrage and systematically
      over-flattens net load. The per-unit ``SOC <= energy_cap`` bound keeps
      the distortion small for short-duration storage (a 4-hour battery
      cannot shift across days or seasons), so it is left in for now; it
      grows with long-duration storage. Standard mitigations are noted in
      ``model-methodology-spec.md`` (rolling-horizon dispatch, daily SOC
      cycling caps, or a price-taker arbitrage pass).

    A third, optional family adds one **RPS** inequality row when
    ``rps_target`` is set: total annual wind and solar generation must reach
    ``rps_target`` times total annual demand (nuclear and hydro are clean but
    not renewable, so they are excluded -- CX-6a). Its dual is the implicit
    REC price.

    A fourth, optional family adds **hydro monthly energy budgets** when
    ``hydro_monthly_energy`` is set: for each hydro generator and month the
    summed dispatch is bounded by the month's energy budget (and above by an
    optional run-of-river min-flow floor), giving energy-limited hydro that
    chooses *when* within a month to generate. When ``hydro_monthly_energy``
    is ``None`` no rows are added and the LP is identical to today's.

    Args:
        layout: Variable layout describing the column structure.
        fleet: Vectorized fleet arrays; supplies generator zone membership.
        demand: Zonal demand of shape ``(n_zones, T)`` in MW.
        incidence: Node-link incidence of shape ``(n_zones, n_links)``; the
            coefficient of ``Flow`` in each zone's balance. ``None`` when
            there are no links.
        link_loss: Optional ``(n_links, T)`` per-link-hour marginal loss
            fraction on ONE-WAY links (miso_zonal_loss_surface): the
            receiving zone of link ``l`` gains ``(1 - link_loss[l, t])``
            per MW of flow instead of 1, so transported energy consumes
            MWh and the zonal duals separate by the measured
            delivery-factor ratio. Zero rows leave a link lossless;
            ``None`` (default) skips the correction entirely
            (byte-identical). Loss entries are only meaningful on one-way
            (``is_bidirectional=False``) links — a signed bidirectional
            link with loss would create energy on reverse flow.
        storage_zone_idx: Zone index of each storage unit, shape
            ``(n_storage,)``. Defaults to zone ``0`` for every unit.
        eta_chg: Charge efficiency, scalar or ``(n_storage,)``. Defaults
            to ``1.0`` (lossless).
        eta_dis: Discharge efficiency, scalar or ``(n_storage,)``. Defaults
            to ``1.0`` (lossless).
        rps_target: Required renewable-energy share. When not ``None`` and
            positive, one annual RPS constraint row is appended.
        rps_eligible_fuels: The ISO statute's renewable-tier eligible fuel
            names (``policy.rps.get_rps_eligible_fuels``). Wind/solar count
            via their zone columns; other names resolve to thermal-block
            generator columns through ``FUEL_TYPE_MAP``
            (:func:`_resolve_rps_eligible_gen_idx`). ``None`` keeps the
            wind+solar-only row (byte-identical).
        rps_region_zone_mask: ``(K, n_zones)`` bool per-compliance-region
            eligibility mask (FFR-7B Arm 2, MISO). With
            ``rps_region_obligation_frac`` it REPLACES the single ISO-wide
            row with K per-region rows (:func:`_build_rps_region_rows`);
            mutually exclusive with ``rps_target``. ``None`` (default)
            keeps the legacy single-row path byte-identical.
        rps_region_obligation_frac: ``(K, n_zones)`` float per-(region,
            zone) RHS weights — within-zone obligated load share times the
            region's statutory target.
        clean_region_zone_mask: ``(K2, n_zones)`` bool clean/carbon-free
            tier eligibility mask (FFR-7B Arm 3, MISO West/East; the
            federal CES target row, SCN-WS2a) — a SECOND independent row
            family on the same region machinery, appended after whichever
            RPS family is present. Since SCN-WS2a it STANDS ALONE OR BESIDE
            EITHER RPS GRAIN (the former "requires the RPS region family"
            coupling, G-S3, is relaxed): its escape columns occupy the
            region-major ACP slots after the RPS family's (zero of them
            when no RPS row carries an escape). ``None`` (default) adds no
            rows (byte-identical).
        clean_region_obligation_frac: ``(K2, n_zones)`` float clean-tier
            RHS weights.
        clean_region_fuels: Per-region qualifying spec — a statutory
            fuel-name tuple (indicator coefficients; nuclear ADMITTED —
            FFR-6B §6.3; unknown names hard-error; out-of-mask generators
            excluded, ARM3-FIX) or an ``(n_gen,)`` per-generator credit-
            fraction vector (the federal CES target row: each generator
            column carries its own fraction). Resolved via
            :func:`_resolve_clean_region_gen_idx` /
            :func:`_resolve_clean_region_gen_coeff` under the region's
            ``clean_region_zone_mask``.
        hydro_monthly_energy: Monthly hydro energy budget in MWh, shape
            ``(n_hydro, n_months)``. When ``None`` the hydro family is
            omitted (identical LP); otherwise one budget row per hydro
            generator and month is appended.
        hydro_month_index: Month index of each hour, shape ``(T,)``. When
            ``None`` it is derived from the standard calendar.
        hydro_gen_idx: Thermal-block indices of the hydro generators, shape
            ``(n_hydro,)``. When ``None`` they are derived from the fleet's
            hydro fuel type. Must align row-for-row with
            ``hydro_monthly_energy``.
        hydro_monthly_min: Monthly minimum hydro energy in MWh (the
            run-of-river min-flow floor), shape ``(n_hydro, n_months)``.
            When ``None`` the floor is zero. Ignored unless
            ``hydro_monthly_energy`` is set.

    Returns:
        Tuple ``(A, row_lower, row_upper, lcr_row_offset, n_lcr_areas,
        iface_row_offset, n_iface_groups)`` where ``A`` is a CSR matrix --
        the row-wise layout HiGHS consumes directly -- and the bound
        vectors give the lower and upper row bounds. The energy-balance and
        storage rows are equalities; the optional RPS row has an infinite
        upper bound. The two ``*_row_offset`` / count pairs locate the
        local-capacity and aggregate-interface blocks inside the row vector
        so their duals can be read back after the solve (``-1`` / ``0`` when
        the block is absent). Both are pure *reporting* outputs: they name
        rows the assembler already built and change no row, bound or
        coefficient.
    """
    T = layout.T  # T: number of hours
    n_zones = layout.n_zones
    n_storage = layout.n_storage
    n_links = layout.n_links
    vph = layout.vars_per_hour

    zone_gen = _build_zone_gen_map(fleet, n_zones)
    zone_storage = _build_zone_storage_map(storage_zone_idx, n_zones, n_storage)
    eye_z = sp.eye(n_zones, format="csr")

    if incidence is None:
        flow_block = sp.csr_matrix((n_zones, n_links))
    else:
        flow_block = sp.csr_matrix(incidence)

    # Per-hour energy-balance block, column order matching the layout:
    # P | W | S | Chg | Dis | SOC | Flow | Slack | Dump.
    per_hour = sp.hstack(
        [
            zone_gen,  # thermal generation
            eye_z,  # wind
            eye_z,  # solar
            -zone_storage,  # charge (withdrawal)
            zone_storage,  # discharge (injection)
            sp.csr_matrix((n_zones, n_storage)),  # SOC: no balance contribution
            flow_block,  # transmission flow
            eye_z,  # load slack (+)
            -eye_z,  # overgeneration dump (-)
            # Co-opt reserve/ORDC/storage-reserve columns do not appear in the
            # energy balance (zero blocks); empty when off, keeping per_hour
            # width == vph.
            sp.csr_matrix((n_zones, layout.n_reserve)),
            sp.csr_matrix((n_zones, layout.n_ordc_steps)),
            sp.csr_matrix((n_zones, layout.n_storage_reserve)),
            # Posture U/SU columns carry no energy (zero blocks; empty when
            # the commitment-posture lever is off).
            sp.csr_matrix((n_zones, 2 * layout.n_posture)),
            # RPS ACP escape column carries no energy (zero block; empty unless
            # the RPS ACP escape is active). Keeps per_hour width == vph.
            sp.csr_matrix((n_zones, layout.n_rec_acp)),
            # Storage discharge-tranche columns carry no energy of their own —
            # the base Dis column already injects the total (Dis = Σ_k DisT via
            # the decomposition row), so the tranches are a cost decomposition,
            # not a second injection (zero block; empty off the arm, keeping
            # per_hour width == vph).
            sp.csr_matrix((n_zones, layout.n_dis_tranche)),
            # Cascade spill / pond-volume columns are WATER, not energy (zero
            # block; empty off the arm, keeping per_hour width == vph).
            sp.csr_matrix((n_zones, layout.n_cascade)),
        ],
        format="csr",
    )

    # Replicate the per-hour block across all hours without a Python loop.
    energy_balance = sp.kron(sp.eye(T, format="csr"), per_hour, format="csr")

    # Marginal transmission losses (miso_zonal_loss_surface): scale the
    # RECEIVING-end incidence entry of each lossy one-way link from +1 to
    # ``1 - link_loss[l, t]`` — transported energy costs MWh, so the zonal
    # duals separate by the measured delivery-factor ratio (prices stay LP
    # duals, rule #4; never a price adder). The loss fraction is hour-varying
    # (a monthly measured surface expanded hourly), so it cannot ride the
    # static ``per_hour`` kron block; instead the correction is a sparse
    # subtraction with one entry per (lossy link, hour), built fully
    # vectorized (rule #2). ``None`` (every flag off) skips the block —
    # byte-identical constraint matrix.
    if link_loss is not None and n_links:
        loss = np.asarray(link_loss, dtype=float)
        lossy = np.flatnonzero(loss.max(axis=1) > 0.0)  # links with any loss
        if lossy.size:
            inc_csc = sp.csc_matrix(flow_block)
            # Receiving zone of each lossy link = the +1 incidence row.
            recv = np.empty(lossy.size, dtype=int)
            for j, ln in enumerate(lossy):  # ln: lossy-link column (few)
                col = inc_csc.getcol(int(ln))
                recv[j] = int(col.indices[np.argmax(col.data)])
            hours_idx = np.arange(T)
            rows = (hours_idx[None, :] * n_zones + recv[:, None]).ravel()
            cols = (
                hours_idx[None, :] * vph + layout._flow_off + lossy[:, None]
            ).ravel()
            data = -loss[lossy, :].ravel()
            correction = sp.csr_matrix((data, (rows, cols)), shape=energy_balance.shape)
            energy_balance = (energy_balance + correction).tocsr()

    # RHS: row r = t * n_zones + z must hold demand[z, t]; demand.T ravels
    # in that hour-major, zone-minor order.
    eb_rhs = np.asarray(demand, dtype=float).T.ravel()

    # Constraint blocks are collected in row order and stacked ONCE at the end
    # via _vstack_csr_free (which releases each block as it is copied), instead
    # of a pairwise ``A = sp.vstack([A, block])`` chain that re-copies the whole
    # accumulated matrix at every step — the reserve-column-construction OOM.
    # Byte-identical result; see _vstack_csr_free. Names are ``del``'d after
    # append so the list is the sole owner and the incremental free can happen.
    blocks: list[sp.csr_matrix | None] = []
    # The two bound VECTORS are collected the same way and for the same reason
    # (PERF-C S2): each optional row family used to do
    # ``row_lower = np.concatenate([row_lower, block_lower])``, which re-copies
    # the whole accumulated vector once per family — ~20 successive copies of a
    # vector that reaches 1.03 M entries on a plant-level MISO year, i.e.
    # quadratic work for a linear result. Collect the per-block pieces in row
    # order and join each list ONCE at the return, exactly as ``blocks`` is
    # joined once by ``_vstack_csr_free``. Same pieces, same order, same
    # dtype (float64 throughout, as the pairwise chain also produced), so the
    # assembled vectors are bit-identical — and no LP row, coefficient or
    # bound changes.
    lower_parts: list[np.ndarray] = []
    upper_parts: list[np.ndarray] = []
    # Running row count, kept in step with ``lower_parts`` so the offsets that
    # used to read ``row_lower.size`` mid-assembly (the interface, LCR and
    # hydro-cascade blocks' start rows) still read the same number.
    n_rows_built = 0

    def _add_bounds(lo, hi) -> None:
        """Append one row block's ``(lower, upper)`` bounds in row order.

        ``np.asarray(..., dtype=float)`` reproduces the promotion the pairwise
        ``np.concatenate`` chain performed against the float64 accumulator,
        and is a no-op (no copy) for the float64 arrays every builder returns.
        """
        nonlocal n_rows_built
        lo_a = np.asarray(lo, dtype=float)
        hi_a = np.asarray(hi, dtype=float)
        lower_parts.append(lo_a)
        upper_parts.append(hi_a)
        n_rows_built += lo_a.size

    if n_storage == 0:
        blocks.append(energy_balance)
        del energy_balance
        _add_bounds(eb_rhs, eb_rhs)
    else:
        eta_c = np.broadcast_to(
            np.asarray(1.0 if eta_chg is None else eta_chg, dtype=float),
            (n_storage,),
        )
        eta_d = np.broadcast_to(
            np.asarray(1.0 if eta_dis is None else eta_dis, dtype=float),
            (n_storage,),
        )

        # Build every storage unit's SOC rows in one sparse construction.
        # Unit s occupies rows s*T .. (s+1)*T-1 of the combined block; its
        # T rows hold the dynamics for hours 1..T-1 plus the cyclic hour 0.
        units = np.arange(n_storage)  # s: storage unit index
        hour_off = np.arange(T) * vph  # per-hour column stride, (T,)

        # Column indices per variable type, for all units: (n_storage, T).
        all_soc_cols = hour_off[None, :] + layout._soc_off + units[:, None]
        all_chg_cols = hour_off[None, :] + layout._chg_off + units[:, None]
        all_dis_cols = hour_off[None, :] + layout._dis_off + units[:, None]

        # Row indices: dynamics rows are local hours 1..T-1, the cyclic row
        # is local hour 0, both shifted by unit s's row offset s*T.
        dyn_rows = units[:, None] * T + np.arange(1, T)[None, :]  # (n_storage, T-1)
        cyc_rows = units * T  # (n_storage,)

        neg_eta_c = -eta_c
        inv_eta_d = 1.0 / eta_d
        ones_dyn = np.ones(n_storage * (T - 1))

        all_rows = np.concatenate(
            [
                dyn_rows.ravel(),  # SOC[s,t]
                dyn_rows.ravel(),  # SOC[s,t-1]
                dyn_rows.ravel(),  # Chg[s,t]
                dyn_rows.ravel(),  # Dis[s,t]
                cyc_rows,  # cyclic: SOC[s,0]
                cyc_rows,  # cyclic: SOC[s,T-1]
                cyc_rows,  # cyclic: Chg[s,0]
                cyc_rows,  # cyclic: Dis[s,0]
            ]
        )
        all_cols = np.concatenate(
            [
                all_soc_cols[:, 1:].ravel(),  # SOC[s,t]
                all_soc_cols[:, :-1].ravel(),  # SOC[s,t-1]
                all_chg_cols[:, 1:].ravel(),  # Chg[s,t]
                all_dis_cols[:, 1:].ravel(),  # Dis[s,t]
                all_soc_cols[:, 0],  # cyclic: SOC[s,0]
                all_soc_cols[:, -1],  # cyclic: SOC[s,T-1]
                all_chg_cols[:, 0],  # cyclic: Chg[s,0]
                all_dis_cols[:, 0],  # cyclic: Dis[s,0]
            ]
        )
        all_data = np.concatenate(
            [
                ones_dyn,
                -ones_dyn,
                np.broadcast_to(neg_eta_c[:, None], (n_storage, T - 1)).ravel(),
                np.broadcast_to(inv_eta_d[:, None], (n_storage, T - 1)).ravel(),
                np.ones(n_storage),
                -np.ones(n_storage),
                neg_eta_c,
                inv_eta_d,
            ]
        )

        soc_block = sp.coo_matrix(
            (all_data, (all_rows, all_cols)),
            shape=(n_storage * T, layout.total_columns),
        ).tocsr()
        blocks.append(energy_balance)
        blocks.append(soc_block)
        del energy_balance, soc_block
        _add_bounds(eb_rhs, eb_rhs)
        _soc_rhs = np.zeros(T * n_storage)
        _add_bounds(_soc_rhs, _soc_rhs)

    # Optional daily SOC cycling cap: pin each storage unit's day-start SOC to
    # its hour-0 level so every day is energy-neutral, bounding the single-LP
    # perfect-foresight advantage to within-day arbitrage. Appended after the
    # SOC dynamics, before hydro/RPS, so the energy-balance and RPS duals keep
    # their positions.
    if storage_daily_cycle_hours and n_storage:
        cycle_block = _build_storage_daily_cycle_rows(
            layout, int(storage_daily_cycle_hours)
        )
        if cycle_block.shape[0]:
            zeros = np.zeros(cycle_block.shape[0])
            blocks.append(cycle_block)
            del cycle_block
            _add_bounds(zeros, zeros)

    # Optional per-day DA charge-allocation floors (caiso_charge_allocation_
    # schedule, M1 — the owner-granted caiso-103 belly ask executed
    # caiso-104): the fleet battery charge in each measured-support hour must
    # carry at least alloc_share[hod] x da_frac of the day's total fleet
    # charge (the exact Fourier-Motzkin elimination of the ask's per-day
    # scheduled-volume variable S[d] — see _build_storage_alloc_rows). Volume
    # stays endogenous (a zero-charge day is feasible); only the intra-day
    # allocation is conduct-constrained. Appended after the SOC/cycle rows,
    # before interface/hydro/RPS, so the front-anchored energy-balance duals
    # and the end-anchored RPS/reserve duals keep their positions. No rows
    # (identical LP) when the inputs are absent.
    if (
        storage_alloc_batt_idx is not None
        and storage_alloc_share is not None
        and storage_alloc_da_frac is not None
        and n_storage
    ):
        alloc_block = _build_storage_alloc_rows(
            layout,
            storage_alloc_batt_idx,
            storage_alloc_share,
            float(storage_alloc_da_frac),
        )
        if alloc_block.shape[0]:
            n_alloc = alloc_block.shape[0]
            blocks.append(alloc_block)
            del alloc_block
            _add_bounds(np.zeros(n_alloc), np.full(n_alloc, np.inf))

    # Optional storage discharge-tranche decomposition rows (ERCOT
    # ercot_storage_rt_offer_surface): Dis[s,t] = Σ_k DisT[a,k,t] per armed
    # battery-hour, tying each armed battery's total discharge to its priced
    # tranche columns. Appended after the SOC/cycle/alloc storage rows and
    # before interface/hydro/RPS/reserve, so the front-anchored energy-balance
    # duals and the end-anchored RPS/reserve duals keep their positions. No
    # rows (identical LP) when the arm is off.
    if layout.n_dis_tranche and dis_tranche_arm_idx is not None and n_storage:
        tranche_block = _build_dis_tranche_rows(layout, dis_tranche_arm_idx)
        if tranche_block.shape[0]:
            n_tr = tranche_block.shape[0]
            blocks.append(tranche_block)
            del tranche_block
            _add_bounds(np.zeros(n_tr), np.zeros(n_tr))

    # Optional aggregate interface limits: one row per group per hour capping
    # the signed sum of a set of links' flows at the interface's *simultaneous*
    # transfer rating (smaller than the per-path TTC sum). Appended after the
    # energy/storage rows but before hydro/RPS/reserve, so the front-anchored
    # energy-balance duals and the end-anchored RPS/reserve duals keep their
    # positions. No rows (identical LP) when no groups are supplied.
    iface_row_offset = -1
    n_iface_groups = 0
    if interface_groups:
        iface_block, iface_lower, iface_upper = _build_interface_rows(
            layout, interface_groups
        )
        if iface_block.shape[0]:
            # Record where the block starts so the solved row duals can be
            # sliced back out per group (the network sidecar's interface
            # duals). Reporting only — the block, its bounds and its
            # coefficients are exactly what was built above.
            iface_row_offset = n_rows_built
            n_iface_groups = len(interface_groups)
            blocks.append(iface_block)
            del iface_block
            _add_bounds(iface_lower, iface_upper)

    # Optional plant-group hourly ramp-envelope rows (config.ramp_limits,
    # GATED default off): CAMPD-measured two-sided trajectory bounds per
    # plant group per hour transition. Appended after the interface rows and
    # before hydro/oil/RPS/reserve, so the front-anchored energy-balance
    # duals and the end-anchored RPS/reserve duals keep their positions. No
    # rows (identical LP) when the inputs are absent.
    if ramp_gen_idx is not None and ramp_up_mw is not None:
        ramp_gen_idx = np.asarray(ramp_gen_idx, dtype=int)
        if ramp_gen_idx.size:
            ramp_block, ramp_lower, ramp_upper = _build_ramp_rows(
                layout,
                fleet,
                ramp_gen_idx,
                ramp_group_col,
                ramp_up_mw,
                ramp_dn_mw,
            )
            blocks.append(ramp_block)
            del ramp_block
            _add_bounds(ramp_lower, ramp_upper)

    # Optional local-capacity (LCR-area) minimum-generation rows
    # (config.local_capacity_constraints, GATED default off): one >= row per
    # covered area per hour, RHS from the published LCR study parameters.
    # Same placement convention as the ramp rows above. No rows (identical
    # LP) when no specs are supplied.
    lcr_row_offset = -1
    n_lcr_areas = 0
    if local_capacity_specs:
        lcr_block, lcr_lower, lcr_upper = _build_local_capacity_rows(
            layout, local_capacity_specs
        )
        if lcr_block.shape[0]:
            lcr_row_offset = n_rows_built
            n_lcr_areas = len(local_capacity_specs)
            blocks.append(lcr_block)
            del lcr_block
            _add_bounds(lcr_lower, lcr_upper)

    # Optional hydro hourly deliverability-envelope rows
    # (config.hydro_dispatch_envelope, GATED default off): one <= row per
    # hour capping the hydro fleet's total dispatch at the measured
    # per-(month x hod) EIA-930 NG:WAT percentile. Same placement convention
    # as the ramp/local-capacity rows above. No rows (identical LP) when the
    # inputs are absent.
    if hydro_envelope_gen_idx is not None and hydro_envelope_mw is not None:
        env_gen_idx = np.asarray(hydro_envelope_gen_idx, dtype=int)
        if env_gen_idx.size:
            env_block, env_lower, env_upper = _build_gen_group_cap_rows(
                layout,
                env_gen_idx,
                hydro_envelope_mw,
                storage_idx=hydro_envelope_storage_idx,
            )
            blocks.append(env_block)
            del env_block
            _add_bounds(env_lower, env_upper)

    # Optional hydro monthly energy budgets: one two-sided row per hydro
    # generator and month. Appended before the RPS row so the RPS dual stays
    # the final constraint. An empty hydro subset adds zero rows.
    if hydro_monthly_energy is not None:
        if hydro_gen_idx is None:
            hydro_gen_idx = np.flatnonzero(
                np.asarray(fleet.fuel_type_idx) == FUEL_TYPE_MAP["hydro"]
            )
        else:
            hydro_gen_idx = np.asarray(hydro_gen_idx, dtype=int)
        if hydro_month_index is None:
            hydro_month_index = _hour_to_month_index(T)
        if hydro_gen_idx.size:
            # Period FAMILIES (nyiso-220, config.hydro_budget_period_by_instrument).
            # Each hydro generator conserves energy over the period its own
            # governing instrument (or measured pondage) permits; generators with
            # no registry entry carry period 0 = the calendar month, which is the
            # unchanged behaviour. Because _build_hydro_rows already takes an
            # arbitrary generator SUBSET and an arbitrary period index, families
            # are emitted as one call each and stacked -- the row builder itself
            # needs no change, and the loop is over at most a handful of families,
            # never over hours (rule 2 [R-VECTOR] is untouched).
            if hydro_period_hours is None:
                families: list[tuple[int, np.ndarray]] = [
                    (0, np.arange(hydro_gen_idx.size, dtype=int))
                ]
            else:
                ph_arr = np.asarray(hydro_period_hours, dtype=int)
                families = [
                    (int(p), np.flatnonzero(ph_arr == p)) for p in np.unique(ph_arr)
                ]
            for period_hours, local in families:
                if not local.size:
                    continue
                if period_hours <= 0:
                    fam_energy = np.asarray(hydro_monthly_energy)[local]
                    fam_index = hydro_month_index
                    fam_min = (
                        None
                        if hydro_monthly_min is None
                        else np.asarray(hydro_monthly_min)[local]
                    )
                else:
                    from market_sim.data.hydro import allocate_period_energy

                    fam_energy, fam_index = allocate_period_energy(
                        np.asarray(hydro_monthly_energy)[local], period_hours, T
                    )
                    if hydro_monthly_min is None:
                        fam_min = None
                    else:
                        # The min-flow floor is re-expressed on the same finer
                        # grid by the identical allocation, so the two-sided row
                        # stays feasible (lower <= upper) period by period.
                        fam_min, _ = allocate_period_energy(
                            np.asarray(hydro_monthly_min)[local], period_hours, T
                        )
                        fam_min = np.minimum(fam_min, fam_energy)
                hydro_block, hydro_lower, hydro_upper = _build_hydro_rows(
                    layout,
                    hydro_gen_idx[local],
                    fam_energy,
                    fam_index,
                    fam_min,
                )
                blocks.append(hydro_block)
                del hydro_block
                _add_bounds(hydro_lower, hydro_upper)

    # Optional hydraulic-cascade water-balance rows (NWPP-36, owner ruling
    # N3; config.hydro_cascade_coupling): one EQUALITY per coupled downstream
    # plant and hour tying its turbine flow (P/η), spill and pond change to
    # the lagged upstream release plus measured side inflow. A SECOND
    # PHENOMENON beside the monthly budget above (hydraulic succession), never
    # a second budget: no generation column is added and every row is feasible
    # at zero generation, so the monthly cap stays the sole quantity mechanism
    # (rule 19 [R-ONE-MECH]). Appended right after the hydro budget rows, before
    # the oil/coal budgets and the end-anchored RPS/reserve tail, so every
    # existing dual position is unchanged. None (the default, and every run in
    # every ISO that does not arm the field) adds zero rows — byte-identical.
    if hydro_cascade is not None and layout.n_cascade:
        from market_sim.model.lp.hydro_cascade import build_hydro_cascade_rows

        cas_block, cas_lower, cas_upper = build_hydro_cascade_rows(
            layout, hydro_cascade
        )
        if cas_block.shape[0]:
            if row_offsets is not None:
                row_offsets["hydro_cascade"] = (
                    int(n_rows_built),
                    int(cas_block.shape[0]),
                )
            blocks.append(cas_block)
            del cas_block
            _add_bounds(cas_lower, cas_upper)

    # Optional oil-burn monthly inventory budget: one row per oil-capable
    # generator and month. When the budget binds, the shadow price is the
    # scarcity rent that lifts the LMP above the oil-parity cap.
    if oil_monthly_budget is not None and oil_gen_idx is not None:
        oil_gen_idx_arr = np.asarray(oil_gen_idx, dtype=int)
        if oil_month_index is None:
            oil_month_index = _hour_to_month_index(T)
        if oil_gen_idx_arr.size:
            oil_block, oil_lower, oil_upper = _build_oil_budget_rows(
                layout,
                oil_gen_idx_arr,
                oil_monthly_budget,
                oil_month_index,
                gen_hour_coeff=oil_gen_hour_coeff,
                group_index=oil_group_index,
            )
            blocks.append(oil_block)
            del oil_block
            _add_bounds(oil_lower, oil_upper)

    # Optional coal fuel-inventory monthly budget: one pooled fleet row per
    # month, capping coal energy INPUT (heat_rate * P, MMBtu) at the opening
    # stockpile plus a prior-years delivery rate. The missing CEILING on coal —
    # coal carries floors and nothing caps its energy, so the LP cannot
    # represent a fleet that drew its pile down one year and could only burn
    # what it received the next (data/coal_fuel_inventory.py).
    #
    # Shares _build_oil_budget_rows with the NEISO oil budget above but reaches
    # it through its OWN kwarg family, so the two fuel budgets append as
    # separate, independent row families and can never silently overwrite one
    # another (rule 19 [R-ONE-MECH]).
    if coal_monthly_budget is not None and coal_gen_idx is not None:
        coal_gen_idx_arr = np.asarray(coal_gen_idx, dtype=int)
        if coal_month_index is None:
            coal_month_index = _hour_to_month_index(T)
        if coal_gen_idx_arr.size:
            coal_block, coal_lower, coal_upper = _build_oil_budget_rows(
                layout,
                coal_gen_idx_arr,
                coal_monthly_budget,
                coal_month_index,
                gen_hour_coeff=coal_gen_hour_coeff,
                group_index=coal_group_index,
            )
            blocks.append(coal_block)
            del coal_block
            _add_bounds(coal_lower, coal_upper)

    # Optional per-coal-yard ANNUAL budget rows (miso-268,
    # coal_fuel_inventory_plant_grain): the pooled rows above let coal at one
    # yard fund burn at another; these cap each yard's annual coal energy INPUT
    # at its OWN opening stock plus prior-years receipts. Same builder, one
    # "month" spanning the year, its own kwarg family so it never overwrites the
    # pooled monthly rows, which stay the timing limb (rule 19 [R-ONE-MECH]).
    if coal_plant_budget is not None and coal_plant_gen_idx is not None:
        cp_idx = np.asarray(coal_plant_gen_idx, dtype=int)
        if coal_plant_month_index is None:
            coal_plant_month_index = np.zeros(T, dtype=int)
        if cp_idx.size:
            cp_block, cp_lower, cp_upper = _build_oil_budget_rows(
                layout,
                cp_idx,
                coal_plant_budget,
                coal_plant_month_index,
                gen_hour_coeff=coal_plant_gen_hour_coeff,
                group_index=coal_plant_group_index,
            )
            blocks.append(cp_block)
            del cp_block
            _add_bounds(cp_lower, cp_upper)

    # Optional priced import-node monthly net-throughput band: one row per month
    # pinning the node's net interchange (import tranches minus export sinks) to
    # the measured EIA-930 schedule (boundary-flow calibration constraint). The
    # priced tranches still set the marginal price within each month's envelope.
    # Appended after hydro and before the RPS/reserve rows so the front-anchored
    # energy-balance duals and the end-anchored RPS/reserve duals keep their
    # positions. No rows (identical LP) when no node indices are supplied.
    if import_node_gen_idx is not None and import_node_monthly_lo is not None:
        node_idx = np.asarray(import_node_gen_idx, dtype=int)
        if node_idx.size:
            if import_node_month_index is None:
                import_node_month_index = _hour_to_month_index(T)
            node_block, node_lower, node_upper = _build_import_node_rows(
                layout,
                node_idx,
                import_node_month_index,
                import_node_monthly_lo,
                import_node_monthly_hi,
            )
            blocks.append(node_block)
            del node_block
            _add_bounds(node_lower, node_upper)

    # Optional STANDALONE energy-only commitment-posture rows (ERCOT
    # ercot_commitment_posture): headroom + min-load + startup on the posture
    # U/SU columns, decoupled from any reserve spec (ERCOT has no pergen
    # substrate — the pergen posture rides _build_reserve_rows_pergen instead).
    # Inserted BEFORE the mass_cap/RPS/reserve tail so the front energy-balance
    # duals and the end-anchored reserve/RPS/mass_cap duals keep their row
    # indices (the posture rows carry no extracted dual). No rows (identical LP)
    # when absent.
    if posture_gen_idx is not None and layout.n_posture > 0:
        pos_block, pos_lower, pos_upper = _build_posture_energy_rows(
            layout,
            posture_gen_idx,
            posture_col,
            posture_mlf,
        )
        blocks.append(pos_block)
        del pos_block
        _add_bounds(pos_lower, pos_upper)

    # Optional emissions mass-cap rows: one inequality per active power-sector
    # cap, bounding in-region fossil emissions. Appended after the import-node
    # rows and immediately before the RPS row so the end-anchored dual layout is
    # [ ... | mass_cap (k) | rps (0/1) | reserve (n) ] — RPS's distance from the
    # end is unchanged (plan §4). No rows (identical LP) when absent.
    if mass_cap_coeffs is not None:
        coeffs = np.asarray(mass_cap_coeffs, dtype=float)
        if coeffs.size:
            cap_block = _build_mass_cap_rows(layout, coeffs)
            cap_rhs = np.asarray(mass_cap_rhs, dtype=float).reshape(-1)
            blocks.append(cap_block)
            del cap_block
            _add_bounds(np.full(coeffs.shape[0], -np.inf), cap_rhs)

    # Optional RPS inequality family, one of two mutually-exclusive grains:
    #  * K per-compliance-region rows (rps_region_zone_mask — FFR-7B Arm 2,
    #    MISO): each state standard's eligible-zone certificates + its own
    #    ACP escape must reach its own obligated-load RHS.
    #  * one ISO-wide row (rps_target — every other RPS ISO, where the single
    #    row is arithmetically exact under free intra-ISO REC trade,
    #    FFR-6B §2.1): statutorily-eligible renewable generation (the
    #    wind+solar zone columns, plus any thermal-block classes the ISO's
    #    statute counts — ``rps_eligible_fuels``) must reach
    #    rps_target * total demand.
    # Both are >= rows with an infinite upper bound.
    if rps_region_zone_mask is not None:
        if rps_target is not None and rps_target > 0.0:
            raise ValueError(
                "rps_region_zone_mask (per-region RPS rows) is mutually "
                "exclusive with rps_target (the single ISO-wide row) — the "
                "K-row grain REPLACES the ISO-wide row, never stacks on it "
                "(rule 19 [R-ONE-MECH])"
            )
        region_block, region_rhs = _build_rps_region_rows(
            layout,
            rps_region_zone_mask,
            rps_region_obligation_frac,
            demand,
        )
        k_regions = region_block.shape[0]
        blocks.append(region_block)
        del region_block
        _add_bounds(region_rhs, np.full(k_regions, np.inf))
    elif rps_target is not None and rps_target > 0.0:
        rps_row, rhs = _build_rps_row(
            layout,
            rps_target,
            demand,
            eligible_gen_idx=_resolve_rps_eligible_gen_idx(fleet, rps_eligible_fuels),
        )
        blocks.append(rps_row)
        del rps_row
        _add_bounds([rhs], [np.inf])

    # Optional clean/carbon-free tier family (FFR-7B Arm 3, FFR-6B E-2; the
    # federal CES target row, SCN-WS2a): a SECOND independent row family on
    # the same machinery, appended directly after whichever RPS family is
    # present (dual layout [... | mass_cap | rps 0/1/K1 | clean K2 |
    # reserve]). Its ACP escape columns occupy the region-major slots AFTER
    # the RPS family's: acp_k0 = n_rec_acp - K2, which is K1 beside the
    # region grain, 1 beside a legacy row with an escape, and 0 when the
    # family stands alone (the G-S3 coupling relaxation — the family no
    # longer requires the RPS region grain; the layout's ACP count, set by
    # the model-level assembler, is the only contract). A wind MWh
    # satisfying both its renewable row and its clean row is CORRECT — two
    # constraints, one MWh (FFR-6B §6.4); the one-certificate revenue
    # composition happens at the capacity screens (max(), never sum), not
    # here.
    #
    # SEAM FOR A SECOND CONSUMER (SCN-WS3b, the voluntary-demand row): a new
    # row family attaches here as additional clean regions — it supplies a
    # ``(K, n_zones)`` mask, a ``(K, n_zones)`` obligation fraction, a
    # ``(K,)`` escape price (the layout allocates one ACP column per region)
    # and a per-region qualifying spec (fuel-name tuple OR ``(n_gen,)``
    # credit vector); its duals come back as its slice of
    # ``clean_region_duals`` in region order. Nothing else in the LP moves.
    if clean_region_zone_mask is not None:
        k_clean = int(np.asarray(clean_region_zone_mask).shape[0])
        acp_k0 = int(layout.n_rec_acp) - k_clean
        if acp_k0 < 0:
            raise ValueError(
                f"clean-tier rows need {k_clean} ACP escape column(s) but the "
                f"layout carries {layout.n_rec_acp} — every clean row REQUIRES "
                "its own escape (FFR-6B §6.3)"
            )
        # The resolver gets the SAME zone mask the builder applies to the
        # W/S columns: a clean row's nuclear/hydro/biomass/CCS credit is
        # in-mask, never ISO-wide (ARM3-FIX — fuel-only resolution let
        # MISO-South nuclear satisfy MI's East-only row, defeating MCL
        # 460.1029).
        clean_gen_idx = _resolve_clean_region_gen_idx(
            fleet, clean_region_fuels, clean_region_zone_mask
        )
        clean_block, clean_rhs = _build_rps_region_rows(
            layout,
            clean_region_zone_mask,
            clean_region_obligation_frac,
            demand,
            acp_k0=acp_k0,
            region_gen_idx=clean_gen_idx,
            region_gen_coeff=_resolve_clean_region_gen_coeff(
                clean_region_fuels, clean_gen_idx
            ),
        )
        blocks.append(clean_block)
        del clean_block
        _add_bounds(clean_rhs, np.full(k_clean, np.inf))

    # Optional energy+reserve co-optimization rows (shared headroom + reserve
    # balance). Appended last so the reserve-balance dual is recoverable by row
    # index. Omitted (identical LP) unless the layout carries reserve columns.
    if layout.n_reserve > 0 and reserve_requirement is not None:
        if reserve_pergen_gen_idx is not None:
            # Per-generator reserve columns (R[j,t] per reserve-providing
            # unit): joint P+R headroom per unit-hour + per-family balance.
            # Mutually exclusive with the zone-aggregate spec's scoping
            # mechanisms (supply cap / zone-class online gating / additive
            # headroom) — the per-unit ramp10 variable bound supersedes them
            # all; the pergen layout's own online gating is the per-column
            # ``reserve_pergen_online_gated_cols`` coupling rows (MISO
            # miso_reserve_online_gated). Storage participates via the same
            # duration-gated RS[c,z] columns as the zone-aggregate path when
            # the layout allocated them (CAISO caiso_reserve_coopt, #1492).
            res_block, res_lower, res_upper = _build_reserve_rows_pergen(
                layout,
                fleet,
                reserve_requirement,
                reserve_pergen_gen_idx,
                pergen_col=reserve_pergen_col,
                balance_zone_mask=reserve_balance_zone_mask,
                balance_ordc_counts=reserve_balance_ordc_counts,
                posture_pools=reserve_posture_pools,
                posture_mlf=reserve_posture_mlf,
                pergen_ramp10=reserve_pergen_ramp10,
                storage_zone_idx=storage_zone_idx,
                storage_power_cap=reserve_storage_power_cap,
                storage_duration_h=reserve_storage_duration_h,
                pergen_col_pool=reserve_pergen_col_pool,
                balance_col_mask=reserve_balance_col_mask,
                online_gated_cols=reserve_pergen_online_gated_cols,
                online_rho=reserve_online_rho,
                pool_ramp10_shared=reserve_pergen_pool_ramp10,
            )
            blocks.append(res_block)
            del res_block
            _add_bounds(res_lower, res_upper)
            return (
                _vstack_csr_free(blocks, layout.total_columns),
                np.concatenate(lower_parts),
                np.concatenate(upper_parts),
                lcr_row_offset,
                n_lcr_areas,
                iface_row_offset,
                n_iface_groups,
            )
        elig = (
            np.ones(layout.n_gen, dtype=bool)
            if reserve_eligible is None
            else np.asarray(reserve_eligible, dtype=bool)
        )
        res_block, res_lower, res_upper = _build_reserve_rows(
            layout,
            fleet,
            reserve_requirement,
            elig,
            storage_zone_idx=storage_zone_idx,
            storage_power_cap=reserve_storage_power_cap,
            balance_zone_mask=reserve_balance_zone_mask,
            balance_ordc_counts=reserve_balance_ordc_counts,
            balance_reserve_class=reserve_balance_class,
            online_gated=reserve_online_gated,
            online_rho=reserve_online_rho,
            headroom_eligible=reserve_headroom_eligible,
            headroom_products=reserve_headroom_products,
            headroom_extra_cap=reserve_headroom_extra_cap,
            headroom_storage=reserve_headroom_storage,
            reserve_supply_cap=reserve_supply_cap,
            online_capacity_cap=reserve_online_capacity_cap,
            storage_duration_h=reserve_storage_duration_h,
        )
        blocks.append(res_block)
        del res_block
        _add_bounds(res_lower, res_upper)

    return (
        _vstack_csr_free(blocks, layout.total_columns),
        np.concatenate(lower_parts),
        np.concatenate(upper_parts),
        lcr_row_offset,
        n_lcr_areas,
        iface_row_offset,
        n_iface_groups,
    )
