"""Objective cost-vector assembly for the dispatch LP.

Package split of ``model/dispatch.py`` (refactor-consolidation plan §5 item
7). Pure code motion — :func:`build_cost_vector` is byte-identical to its
pre-split ``dispatch.py`` source.
"""

import numpy as np

from market_sim.config.constants import STORAGE_TIEBREAKER_EPSILON
from market_sim.model.lp.layout import VariableLayout


def build_cost_vector(
    layout: VariableLayout,
    mc: np.ndarray,
    voll: float,
    storage_epsilon: float = STORAGE_TIEBREAKER_EPSILON,
    wind_mc: np.ndarray | float = 0.0,
    solar_mc: np.ndarray | float = 0.0,
    storage_discharge_eac: float = 0.0,
    storage_discharge_cost: np.ndarray | float = 0.0,
    ordc_penalties: np.ndarray | None = None,
    posture_startup_cost: np.ndarray | None = None,
    rps_acp_price: float = 0.0,
    link_flow_cost: np.ndarray | None = None,
    slack_cost: np.ndarray | None = None,
) -> np.ndarray:
    """Assemble the flat LP objective cost vector.

    Thermal slots carry their hourly marginal cost, storage charge carries
    a small ``storage_epsilon`` penalty to break degeneracy, storage
    discharge carries that penalty net of any exogenous discharge EAC
    credit (so its slot cost can go negative), load slack carries the
    value of lost load (``voll``), wind and solar carry their dispatch
    marginal cost (negative under a production credit), overgeneration
    dump carries a tiny cost that still exceeds any production credit, and
    SOC/flow slots are zero-cost.

    Args:
        layout: Variable layout describing the column structure.
        mc: Marginal cost array of shape ``(n_gen, T)``.
        voll: Value of lost load applied to slack variables.
        storage_epsilon: Cycling penalty on storage charge/discharge.
        wind_mc: Wind dispatch marginal cost in $/MWh; scalar (flat) or
            ``(n_zones, T)``. Negative when a production tax credit makes
            wind willing to pay to generate.
        solar_mc: Solar dispatch marginal cost in $/MWh; scalar (flat) or
            ``(n_zones, T)``.
        storage_discharge_eac: Exogenous EAC paid per MWh discharged in
            $/MWh. Subtracted from the discharge slot cost; the discharge
            level stays bounded by SOC dynamics and the power cap.
        storage_discharge_cost: Per-unit dispatch cost added to the
            discharge slot in $/MWh; scalar (flat) or ``(n_storage,)``.
            Carries the pumped-storage throughput adder so PS bids above
            batteries instead of arbitraging every clearable spread.
        posture_startup_cost: ``(n_posture,)`` startup cost in $/MW applied
            to the posture SU[p,t] columns (NREL class tables, capacity-
            weighted per pool). Required when ``layout.n_posture > 0``. The
            U[p,t] columns carry NO direct cost — being online costs
            min-load energy through the coupled P variables, and cycling
            costs the SU charge; U itself is free by design.
        rps_acp_price: Alternative Compliance Payment rate in $/MWh applied to
            the RPS ACP escape column (``layout.n_rec_acp``). Sets the marginal
            cost of buying out of the RPS with an ACP, which caps the RPS row's
            dual (the REC price) at this ceiling. Ignored when the layout
            carries no ACP column.
        link_flow_cost: Optional ``(n_links,)`` per-MWh cost on each link's
            directed flow (MISO RDT TCDC priced tiers). ``None`` keeps the
            flow block zero-cost (byte-identical). Nonzero entries are only
            valid on one-way links — enforced by :class:`DispatchModel`.
        slack_cost: Optional ``(n_zones, T)`` per-zone-hour load-slack cost
            that replaces the flat ``voll`` broadcast (the declared-window
            ELMP emergency-tier repricing,
            ``data.maxgen_events.emergency_tier_slack_cost`` — never above
            ``voll`` by construction there). ``None`` keeps the flat ``voll``
            (byte-identical).

    Returns:
        Cost vector of length ``layout.total_columns``.
    """
    cost = np.zeros(layout.total_columns, dtype=float)
    block = cost.reshape(layout.T, layout.vars_per_hour)

    # Thermal: mc is (n_gen, T); the per-hour block wants (T, n_gen).
    block[:, layout._p_off : layout._w_off] = mc.T

    # Wind and solar: dispatch marginal cost. wind_mc/solar_mc are scalar or
    # (n_zones, T); the per-hour block wants (T, n_zones).
    block[:, layout._w_off : layout._s_off] = np.broadcast_to(
        np.asarray(wind_mc, dtype=float), (layout.n_zones, layout.T)
    ).T
    block[:, layout._s_off : layout._chg_off] = np.broadcast_to(
        np.asarray(solar_mc, dtype=float), (layout.n_zones, layout.T)
    ).T

    # Storage charge: flat cycling penalty. Discharge: cycling penalty plus
    # any per-unit dispatch cost (e.g. the pumped-storage throughput adder),
    # net of any exogenous discharge EAC credit, so the slot cost can go
    # negative; SOC dynamics and the power cap still bound the discharge.
    block[:, layout._chg_off : layout._dis_off] = storage_epsilon
    block[:, layout._dis_off : layout._soc_off] = (
        storage_epsilon
        + np.broadcast_to(
            np.asarray(storage_discharge_cost, dtype=float),
            (layout.n_storage,),
        )
        - storage_discharge_eac
    )

    # Transmission flow: zero-cost by default; ``link_flow_cost`` prices a
    # link's directed flow (MISO RDT TCDC tiers — one-way links only, the
    # caller validates, since a positive cost on a signed bidirectional flow
    # would credit the reverse direction).
    if link_flow_cost is not None and layout.n_links:
        block[:, layout._flow_off : layout._slack_off] = np.asarray(
            link_flow_cost, dtype=float
        )[np.newaxis, :]

    # Load slack: value of lost load — flat, or the per-zone-hour override
    # (declared-window ELMP emergency-tier repricing). The block wants
    # (T, n_zones); slack_cost arrives (n_zones, T).
    if slack_cost is None:
        block[:, layout._slack_off : layout._dump_off] = voll
    else:
        block[:, layout._slack_off : layout._dump_off] = np.asarray(
            slack_cost, dtype=float
        ).T

    # Overgeneration dump: a tiny cost breaks degeneracy, but it must also
    # exceed the magnitude of any production credit (negative wind/solar
    # marginal cost, or the storage discharge EAC). Otherwise the LP would
    # overgenerate credited renewables to full capacity and dump the
    # surplus, paying the credit on curtailed energy and collapsing the
    # marginal price.
    min_renewable_mc = min(
        0.0,
        float(np.min(np.asarray(wind_mc, dtype=float))),
        float(np.min(np.asarray(solar_mc, dtype=float))),
        -storage_discharge_eac,
    )
    dump_cost = max(storage_epsilon, -min_renewable_mc + storage_epsilon)
    # Dump block only -- the reserve/ORDC co-opt blocks (when present) follow it
    # and are priced separately below. With no co-opt columns _reserve_off ==
    # total vars/hour, so this stays the original "to the end" assignment.
    block[:, layout._dump_off : layout._reserve_off] = dump_cost

    # Energy+reserve co-optimization (co-opt only; both blocks empty otherwise).
    # Reserve variables R[g,t] carry no direct cost -- their economic cost is the
    # energy opportunity cost, enforced by the shared-headroom constraint, which
    # is exactly what lifts the energy LMP. The ORDC shortfall steps carry the
    # published reserve-demand-curve penalty prices ($/MWh): paying step k's
    # penalty is the system's willingness-to-pay to be short reserve, so the
    # binding step sets the reserve clearing price (the balance-row dual).
    if layout.n_ordc_steps > 0:
        if ordc_penalties is None:
            raise ValueError(
                "build_cost_vector: n_ordc_steps > 0 requires ordc_penalties"
            )
        pen = np.asarray(ordc_penalties, dtype=float)
        if pen.shape != (layout.n_ordc_steps,):
            raise ValueError(
                f"ordc_penalties shape {pen.shape} != ({layout.n_ordc_steps},)"
            )
        block[:, layout._ordc_off : layout._ordc_off + layout.n_ordc_steps] = pen

    # Storage-reserve columns RS[c,z,t] (duration gate): NO direct cost, exactly
    # like the thermal reserve R[c,z] above. Storage and thermal reserve must
    # compete on their true opportunity cost alone (storage's = forgone energy
    # arbitrage via the power-competition row + the SOC duration gate; thermal's
    # = forgone energy via the shared headroom). A positive ε here would make the
    # zero-cost thermal reserve STRICTLY undercut storage wherever idle thermal
    # headroom is available, collapsing the storage AS split to ~0 — the opposite
    # of the endogenous intent. Degeneracy on storage's own power is already
    # broken by the Chg/Dis ε.

    # Commitment-posture columns: U[p,t] free (see the posture_startup_cost
    # arg note), SU[p,t] priced at the pool's NREL class startup cost — the
    # re-timing/cycling charge the design note §A adds to the P1 relief
    # channel.
    if layout.n_posture > 0:
        if posture_startup_cost is None:
            raise ValueError(
                "build_cost_vector: n_posture > 0 requires posture_startup_cost"
            )
        su_cost = np.asarray(posture_startup_cost, dtype=float)
        if su_cost.shape != (layout.n_posture,):
            raise ValueError(
                f"posture_startup_cost shape {su_cost.shape} != ({layout.n_posture},)"
            )
        block[:, layout._posture_su_off : layout._posture_su_off + layout.n_posture] = (
            su_cost[np.newaxis, :]
        )

    # RPS ACP escape column: priced at the Alternative Compliance Payment rate.
    # Paying ACP is the marginal cost of the last unit of RPS compliance when
    # physical RECs (wind+solar) run short, so the RPS row's dual cannot exceed
    # this ceiling. Only present when an ACP price accompanies an active RPS.
    if layout.n_rec_acp:
        block[:, layout._rec_acp_off : layout._rec_acp_off + layout.n_rec_acp] = (
            rps_acp_price
        )

    return cost
