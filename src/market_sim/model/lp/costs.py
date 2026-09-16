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
    rps_acp_price: "np.ndarray | float" = 0.0,
    link_flow_cost: np.ndarray | None = None,
    slack_cost: np.ndarray | None = None,
    min_injectable_mc: float | None = None,
    dis_tranche_arm_idx: np.ndarray | None = None,
    dis_tranche_price: np.ndarray | None = None,
) -> np.ndarray:
    """Assemble the flat LP objective cost vector.

    Thermal slots carry their hourly marginal cost, storage charge carries
    a small ``storage_epsilon`` penalty to break degeneracy, storage
    discharge carries that penalty net of any exogenous discharge EAC
    credit (so its slot cost can go negative), load slack carries the
    value of lost load (``voll``), wind and solar carry their dispatch
    marginal cost (negative under a production credit), overgeneration
    dump carries a tiny cost that still exceeds any production credit (and,
    when ``min_injectable_mc`` is supplied, any negative *offer* that can
    reach a dumpable node), and SOC/flow slots are zero-cost.

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
            discharge slot in $/MWh; scalar (flat), ``(n_storage,)``, or
            hourly ``(n_storage, T)`` (the P1-only reservation-price
            re-cost). Carries the pumped-storage throughput adder so PS bids
            above batteries instead of arbitraging every clearable spread.
        posture_startup_cost: ``(n_posture,)`` startup cost in $/MW applied
            to the posture SU[p,t] columns (NREL class tables, capacity-
            weighted per pool). Required when ``layout.n_posture > 0``. The
            U[p,t] columns carry NO direct cost — being online costs
            min-load energy through the coupled P variables, and cycling
            costs the SU charge; U itself is free by design.
        rps_acp_price: Alternative Compliance Payment rate in $/MWh applied to
            the RPS ACP escape columns (``layout.n_rec_acp``); a scalar (the
            legacy single ISO-wide row) or a ``(K,)`` vector pricing each
            compliance region's own escape (FFR-7B Arm 2). Sets the marginal
            cost of buying out of each row with an ACP, which caps that row's
            dual (its region's REC price) at its own ceiling. Ignored when the
            layout carries no ACP column.
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
        min_injectable_mc: Most negative marginal cost in $/MWh over the
            ``mc`` rows that can inject positive MW, folded into the
            overgeneration-dump guard below (``dump_cost_full_offer_domain``).
            ``None`` keeps the guard on the renewable/storage-credit set alone
            — byte-identical, and the historical behaviour.

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
    # ``storage_discharge_cost`` is a scalar / static ``(n_storage,)`` cost, or
    # an HOURLY ``(n_storage, T)`` cost — the P1-only storage reservation-price
    # offer (``ercot_storage_reservation_offer``) re-costs the discharge block
    # per hour at the P0→P1 seam. Every static caller broadcasts exactly as
    # before (byte-identical).
    _sdc = np.asarray(storage_discharge_cost, dtype=float)
    _sdc_t = _sdc.T if _sdc.ndim == 2 else np.broadcast_to(_sdc, (layout.n_storage,))
    block[:, layout._dis_off : layout._soc_off] = (
        storage_epsilon + _sdc_t - storage_discharge_eac
    )

    # Storage RT discharge-offer tranches (ERCOT ercot_storage_rt_offer_surface).
    # RULE 19 [R-ONE-MECH]: on an ARMED battery the measured tranche ladder
    # REPLACES the flat battery_dispatch_adder — so the armed base discharge
    # column drops its vom, keeping only the ε tiebreaker net of any EAC
    # (the base column stays the SOC/energy/power-cap spine, and Dis = Σ_k DisT,
    # so ε·Dis is exactly the R-EPSILON discharge penalty on the total). Every
    # tranche column DisT[a,k,t] then carries its own $/MWh rung; the LP fills
    # cheapest-first, so the marginal cost of the last discharged MW follows the
    # rising ladder. Pumped storage and other ISOs are untouched (their base
    # discharge keeps its own adder).
    if layout.n_dis_tranche and dis_tranche_arm_idx is not None:
        arm = np.asarray(dis_tranche_arm_idx, dtype=int)
        block[:, layout._dis_off + arm] = storage_epsilon - storage_discharge_eac
        price = np.asarray(dis_tranche_price, dtype=float)  # (K, T)
        k = price.shape[0]
        # (T, K) tiled across the n_arm armed units, matching the layout stride
        # _dis_tranche_off + a*K + k (armed-major/tranche-minor).
        dt0 = layout._dis_tranche_off
        block[:, dt0 : dt0 + layout.n_dis_tranche] = np.tile(price.T, (1, arm.size))
        if k * arm.size != layout.n_dis_tranche:
            raise ValueError(
                f"dis_tranche layout mismatch: K({k})*n_arm({arm.size}) != "
                f"n_dis_tranche({layout.n_dis_tranche})"
            )

    # Hydraulic-cascade spill / pond-volume columns (NWPP-36): the rule-9
    # storage tiebreaker ε on both, a strict preference against gratuitous
    # spill-then-refill cycles the water balance would otherwise leave
    # degenerate (≤ 1e-5 of the water value; no other cost, prices stay duals).
    if layout.n_cascade:
        c0 = layout._cas_s_off
        block[:, c0 : c0 + layout.n_cascade] = storage_epsilon

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
    # caiso-139: the guard above enumerates only the renewable/storage credit
    # set, but its stated invariant — no row may profit by generating purely to
    # dump — binds on EVERY offer that can reach a dumpable node. A generator
    # row priced below -dump_cost (the CAISO per-hub import tranches carry their
    # own measured hub, and Palo Verde crashes to -$58/MWh in the desert-SW
    # solar glut) books -mc - dump_cost per MWh of pure generate-to-dump. Where
    # the caller supplies the injectable-row minimum, the SAME guard is taken
    # over its full domain (rule 19 [R-ONE-MECH]: one mechanism, widened, not a
    # second one) — zero new free parameters, the bound is read off the offer
    # arrays the LP already carries.
    min_dumpable_mc = (
        min_renewable_mc
        if min_injectable_mc is None
        else min(min_renewable_mc, float(min_injectable_mc))
    )
    dump_cost = max(storage_epsilon, -min_dumpable_mc + storage_epsilon)
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

    # RPS ACP escape columns: priced at the Alternative Compliance Payment
    # rate — a scalar for the legacy single row, or one rate per compliance
    # region (region-major, matching the layout's ACP block order). Paying ACP
    # is the marginal cost of the last unit of RPS compliance when physical
    # RECs run short, so each row's dual cannot exceed its own ceiling.
    # Only present when an ACP price accompanies an active RPS.
    if layout.n_rec_acp:
        acp = np.asarray(rps_acp_price, dtype=float)
        if acp.ndim > 0 and acp.shape != (layout.n_rec_acp,):
            raise ValueError(
                f"rps_acp_price shape {acp.shape} != ({layout.n_rec_acp},)"
            )
        block[:, layout._rec_acp_off : layout._rec_acp_off + layout.n_rec_acp] = acp

    return cost
