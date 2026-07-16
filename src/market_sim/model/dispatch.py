"""Economic dispatch optimization model.

Part 1: variable layout bookkeeping and objective cost-vector assembly.
Part 2: constraint-matrix construction and decision-variable bounds.
Part 3: HiGHS solver invocation and result extraction.
"""

import logging
import os
import time
from dataclasses import dataclass

import highspy
import numpy as np
import scipy.sparse as sp

from market_sim.config.constants import HOURS_PER_YEAR, STORAGE_TIEBREAKER_EPSILON
from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    FleetArrays,
    _hour_to_month_index,
    assemble_mc,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VariableLayout:
    """Maps dispatch decision variables to flat LP column indices.

    Decision variables are grouped into per-hour blocks laid out
    contiguously across ``T`` hours. Within each hour the block order is:
    thermal generation, wind, solar, storage charge, storage discharge,
    storage state-of-charge, transmission flow, per-zone load slack,
    then per-zone overgeneration dump.
    """

    n_gen: int
    n_zones: int
    n_storage: int
    n_links: int
    T: int = HOURS_PER_YEAR
    # Energy+reserve co-optimization columns, appended after the dump block so
    # every existing offset is unchanged. Both 0 (the default) leave
    # ``vars_per_hour`` and the whole layout byte-identical to the energy-only
    # LP. ``n_reserve`` is one upward-reserve variable per thermal generator
    # (R[g,t], eligibility enforced by its upper bound); ``n_ordc_steps`` is the
    # number of reserve-demand-curve shortfall variables per hour (the ORDC
    # steps that price a reserve shortfall, system-wide).
    #
    # Reserve is tracked per ZONE and per reserve *class*: ``n_reserve ==
    # n_reserve_classes * n_zones``, laid out class-major (R[c, z, t] at
    # ``_reserve_off + c*n_zones + z``). A reserve class is a distinct
    # eligibility tier — NYISO splits the full dispatchable fleet (30-minute
    # products) from the quick-start subset (10-minute products: gas-CT/oil that
    # can synchronize within 10 min), so a 10-minute reserve requirement cannot
    # be met by slow combined-cycle headroom. ERCOT/PJM run a single class
    # (``n_reserve_classes == 1``), byte-identical to the legacy per-zone layout.
    n_reserve: int = 0
    n_reserve_classes: int = 1
    n_ordc_steps: int = 0
    # Explicit per-zone storage-reserve columns RS[c, z, t] for the ERCOT
    # endogenous-storage DURATION GATE (config.ercot_storage_as_duration_gate).
    # When active, storage's upward AS is a distinct decision variable per
    # reserve class c and zone z (``n_storage_reserve == n_reserve_classes *
    # n_zones``, class-major at ``_storage_reserve_off + c*n_zones + z``) instead
    # of being pooled into the thermal shared-headroom rows, so the LP-linear
    # duration gate ``Σ_c dur_c·RS[c,z] ≤ Σ_{s∈z} SOC[s]`` can bound it by stored
    # energy. Appended AFTER the ORDC block so every existing offset is
    # unchanged; 0 (default) leaves the layout byte-identical.
    n_storage_reserve: int = 0
    # Commitment-posture columns (MISO miso_commitment_posture, design note
    # §A): per POSTURED pergen pool p, an online-capacity variable U[p,t] and
    # a startup variable SU[p,t] ≥ U[p,t] − U[p,t−1] (cyclic). Appended AFTER
    # the storage-reserve block so every existing offset is unchanged;
    # ``n_posture`` = the postured (non-fast-start) pool count, 0 (default)
    # leaves the layout byte-identical.
    n_posture: int = 0
    # RPS Alternative-Compliance-Payment (ACP) escape column. A single
    # non-negative variable per hour (``n_rec_acp`` == 0 or 1) carrying a ``+1``
    # coefficient in the annual RPS row and a cost of the ACP price ($/MWh) in
    # the objective. It represents the real-market ACP: an LSE short of RECs
    # pays the ACP rate rather than physically failing the standard, so the RPS
    # row is never infeasible and its dual (the REC price) is capped at the ACP.
    # Appended AFTER the posture block so every existing offset is unchanged; 0
    # (the default — set only when an ACP price accompanies an active RPS
    # target) leaves the layout byte-identical to the hard-constraint LP.
    n_rec_acp: int = 0

    @property
    def vars_per_hour(self) -> int:
        """Return the number of decision variables in a single hour block."""
        return (
            self.n_gen
            + 4 * self.n_zones
            + 3 * self.n_storage
            + self.n_links
            + self.n_reserve
            + self.n_ordc_steps
            + self.n_storage_reserve
            + 2 * self.n_posture
            + self.n_rec_acp
        )

    @property
    def total_columns(self) -> int:
        """Return the total LP column count across all hours."""
        return self.vars_per_hour * self.T

    @property
    def _p_off(self) -> int:
        """Per-hour offset of the thermal generation block."""
        return 0

    @property
    def _w_off(self) -> int:
        """Per-hour offset of the wind generation block."""
        return self.n_gen

    @property
    def _s_off(self) -> int:
        """Per-hour offset of the solar generation block."""
        return self.n_gen + self.n_zones

    @property
    def _chg_off(self) -> int:
        """Per-hour offset of the storage charge block."""
        return self.n_gen + 2 * self.n_zones

    @property
    def _dis_off(self) -> int:
        """Per-hour offset of the storage discharge block."""
        return self.n_gen + 2 * self.n_zones + self.n_storage

    @property
    def _soc_off(self) -> int:
        """Per-hour offset of the storage state-of-charge block."""
        return self.n_gen + 2 * self.n_zones + 2 * self.n_storage

    @property
    def _flow_off(self) -> int:
        """Per-hour offset of the transmission flow block."""
        return self.n_gen + 2 * self.n_zones + 3 * self.n_storage

    @property
    def _slack_off(self) -> int:
        """Per-hour offset of the per-zone load slack block."""
        return self.n_gen + 2 * self.n_zones + 3 * self.n_storage + self.n_links

    @property
    def _dump_off(self) -> int:
        """Per-hour offset of the per-zone overgeneration dump block."""
        return (
            self.n_gen
            + 2 * self.n_zones
            + 3 * self.n_storage
            + self.n_links
            + self.n_zones
        )

    @property
    def _reserve_off(self) -> int:
        """Per-hour offset of the upward-reserve block (co-opt only)."""
        return self._dump_off + self.n_zones

    @property
    def _ordc_off(self) -> int:
        """Per-hour offset of the ORDC shortfall block (co-opt only)."""
        return self._reserve_off + self.n_reserve

    @property
    def _storage_reserve_off(self) -> int:
        """Per-hour offset of the storage-reserve block (duration gate only)."""
        return self._ordc_off + self.n_ordc_steps

    @property
    def _posture_u_off(self) -> int:
        """Per-hour offset of the posture online-capacity block (U[p,t])."""
        return self._storage_reserve_off + self.n_storage_reserve

    @property
    def _posture_su_off(self) -> int:
        """Per-hour offset of the posture startup block (SU[p,t])."""
        return self._posture_u_off + self.n_posture

    @property
    def _rec_acp_off(self) -> int:
        """Per-hour offset of the RPS ACP escape column (RPS only)."""
        return self._posture_su_off + self.n_posture

    def p_col(self, g: int, t: int) -> int:
        """Return the column index of thermal generator ``g`` in hour ``t``."""
        return t * self.vars_per_hour + self._p_off + g

    def w_col(self, z: int, t: int) -> int:
        """Return the column index of wind in zone ``z`` in hour ``t``."""
        return t * self.vars_per_hour + self._w_off + z

    def s_col(self, z: int, t: int) -> int:
        """Return the column index of solar in zone ``z`` in hour ``t``."""
        return t * self.vars_per_hour + self._s_off + z

    def chg_col(self, s: int, t: int) -> int:
        """Return the column index of storage ``s`` charge in hour ``t``."""
        return t * self.vars_per_hour + self._chg_off + s

    def dis_col(self, s: int, t: int) -> int:
        """Return the column index of storage ``s`` discharge in hour ``t``."""
        return t * self.vars_per_hour + self._dis_off + s

    def soc_col(self, s: int, t: int) -> int:
        """Return the column index of storage ``s`` SOC in hour ``t``."""
        return t * self.vars_per_hour + self._soc_off + s

    def flow_col(self, ln: int, t: int) -> int:
        """Return the column index of transmission link ``ln`` in hour ``t``."""
        return t * self.vars_per_hour + self._flow_off + ln

    def slack_col(self, z: int, t: int) -> int:
        """Return the column index of load slack for zone ``z`` in hour ``t``."""
        return t * self.vars_per_hour + self._slack_off + z

    def dump_col(self, z: int, t: int) -> int:
        """Return the column index of dump for zone ``z`` in hour ``t``."""
        return t * self.vars_per_hour + self._dump_off + z

    def r_col(self, g: int, t: int) -> int:
        """Return the column index of generator ``g``'s reserve in hour ``t``."""
        return t * self.vars_per_hour + self._reserve_off + g

    def ordc_col(self, k: int, t: int) -> int:
        """Return the column index of ORDC shortfall step ``k`` in hour ``t``."""
        return t * self.vars_per_hour + self._ordc_off + k

    def sr_col(self, c: int, z: int, t: int) -> int:
        """Return the storage-reserve column of class ``c``, zone ``z``, hour ``t``."""
        return t * self.vars_per_hour + self._storage_reserve_off + c * self.n_zones + z

    def u_col(self, p: int, t: int) -> int:
        """Return the online-capacity column of postured pool ``p``, hour ``t``."""
        return t * self.vars_per_hour + self._posture_u_off + p

    def su_col(self, p: int, t: int) -> int:
        """Return the startup column of postured pool ``p``, hour ``t``."""
        return t * self.vars_per_hour + self._posture_su_off + p

    def acp_col(self, t: int) -> int:
        """Return the RPS ACP escape column in hour ``t`` (RPS only)."""
        return t * self.vars_per_hour + self._rec_acp_off

    def p_cols_gen(self, g: int) -> slice:
        """Return a slice selecting all ``T`` columns of thermal generator ``g``."""
        start = self._p_off + g
        return slice(start, start + self.T * self.vars_per_hour, self.vars_per_hour)


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


def _build_zone_gen_map(fleet: FleetArrays, n_zones: int) -> sp.csr_matrix:
    """Return the sparse ``(n_zones, n_gen)`` zone-membership matrix.

    Entry ``(z, g)`` is ``1`` when thermal generator ``g`` resides in zone
    ``z``. Multiplying this matrix by a generation vector sums each zone's
    generators into its energy-balance row.
    """
    n_gen = fleet.n_gen
    data = np.ones(n_gen, dtype=float)
    return sp.csr_matrix(
        (data, (fleet.zone_idx, np.arange(n_gen))),
        shape=(n_zones, n_gen),
    )


def _build_zone_storage_map(
    storage_zone_idx: np.ndarray | None, n_zones: int, n_storage: int
) -> sp.csr_matrix:
    """Return the sparse ``(n_zones, n_storage)`` storage-membership matrix.

    Entry ``(z, s)`` is ``1`` when storage unit ``s`` resides in zone ``z``.
    When ``storage_zone_idx`` is ``None`` all units default to zone ``0``.
    """
    if n_storage == 0:
        return sp.csr_matrix((n_zones, 0))
    if storage_zone_idx is None:
        zone_idx = np.zeros(n_storage, dtype=int)
    else:
        zone_idx = np.asarray(storage_zone_idx, dtype=int)
    return sp.csr_matrix(
        (np.ones(n_storage, dtype=float), (zone_idx, np.arange(n_storage))),
        shape=(n_zones, n_storage),
    )


def _build_rps_row(
    layout: VariableLayout,
    rps_target: float,
    demand: np.ndarray,
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

    Only wind and solar count toward the target: an RPS is a *renewable*
    portfolio standard, so existing nuclear and large hydro -- clean but not
    renewable -- are excluded (CX-6a, capacity-economics plan 2026-07 §6.5).
    Counting nuclear here would let its output satisfy the target and depress
    the REC dual toward zero wherever nuclear+VRE already clear it, killing the
    renewable-entry signal the dual exists to send. Nuclear's zero-emission
    support flows separately through ``eac_price_nuclear`` (ZEC/CES). This
    matches the capacity screens' ``_RPS_ELIGIBLE_FUELS``/``_RENEWABLE_NEW_FUELS``
    (both wind/solar only).
    """
    T = layout.T  # T: number of hours
    vph = layout.vars_per_hour
    hours = np.arange(T)[:, np.newaxis]  # t: hour index
    zones = np.arange(layout.n_zones)  # z: zone index

    wind_cols = (hours * vph + layout._w_off + zones).ravel()
    solar_cols = (hours * vph + layout._s_off + zones).ravel()

    col_groups = [wind_cols, solar_cols]
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


def _build_reserve_rows(
    layout: VariableLayout,
    fleet: FleetArrays,
    reserve_requirement: np.ndarray,
    reserve_eligible: np.ndarray,
    storage_zone_idx: np.ndarray | None = None,
    storage_power_cap: np.ndarray | float | None = None,
    balance_zone_mask: np.ndarray | None = None,
    balance_ordc_counts: np.ndarray | None = None,
    balance_reserve_class: np.ndarray | None = None,
    online_gated: np.ndarray | None = None,
    online_rho: float = 1.0,
    headroom_eligible: np.ndarray | None = None,
    headroom_products: np.ndarray | None = None,
    headroom_extra_cap: np.ndarray | None = None,
    reserve_supply_cap: np.ndarray | None = None,
    online_capacity_cap: np.ndarray | None = None,
    storage_duration_h: np.ndarray | None = None,
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Build the energy+reserve co-optimization constraint rows (zone-aggregate).

    Reserve is tracked per *zone* and per reserve *class* (``n_reserve ==
    n_reserve_classes * n_zones``), not per unit: a reserve variable
    ``R[c,z,t]`` and one shared-headroom row per class-zone-hour. This keeps the
    LP tractable at per-plant fleet scale (a per-unit headroom row for every
    generator-hour is tens of millions of rows; per-zone is a few per hour)
    while giving the same economics — the zonal headroom dual is what lifts that
    zone's energy LMP. Two families, both vectorized (no hour loop):

    * **Shared headroom** -- for each reserve class ``c``, zone ``z`` and hour
      ``t``: ``sum_{class-c eligible g in z} P[g,t] + R[c,z,t] <=
      sum_{class-c eligible g in z} cap[g,t]``. The zone's class-eligible
      capacity is split between energy and upward reserve, so committing energy
      consumes reserve headroom and vice-versa.
    * **Reserve balance** -- one row per *reserve family* ``f`` and hour ``t``,
      drawing on family ``f``'s reserve class ``c_f``:
      ``sum_{z in family f} R[c_f,z,t] + sum_{k in family f} ORDC_k[t]
      >= requirement[f,t]``. The ORDC shortfall steps let the requirement go
      unmet at the published penalty price, so the binding family's balance-row
      dual is that family's reserve clearing price.

    A *family* is one (region, reserve-product) balance constraint. ERCOT and
    PJM run a single system-wide family on a single class (every zone, every
    ORDC step), which is the default when ``balance_zone_mask`` is ``None`` and
    reproduces the legacy single-row LP byte-identically. NYISO runs nested
    *locational* families (NYCA ⊃ East ⊃ SENY ⊃ NYC) across two reserve classes:
    30-minute products draw on the full dispatchable fleet (class 0), while
    10-minute products draw only on the quick-start subset (class 1) — a
    10-minute requirement cannot be met by slow combined-cycle headroom. The
    shared per-zone ``R[c,z]`` variables feed every family of the same class
    that contains the zone, so a downstate reserve shortage stacks the
    East/SENY/NYC family penalties into the downstate zonal LMP even when the
    system is long on reserves. Because the classes are *nested* (quick-start
    units are also dispatchable), a quick-start unit's headroom feeds both its
    class-1 row (10-minute supply) and the class-0 row (30-minute supply), which
    is the correct reserve cascade: a 10-minute MW also counts toward the larger
    30-minute requirement. ``balance_zone_mask[f]`` selects family ``f``'s
    member zones, ``balance_reserve_class[f]`` its eligibility class, and
    ``balance_ordc_counts[f]`` its slice of the family-major ORDC block.

    Args:
        layout: Variable layout (``n_reserve == n_reserve_classes * n_zones``).
        fleet: Fleet arrays supplying ``pmax``, ``(n_gen, T)`` availability and
            per-generator ``zone_idx``.
        reserve_requirement: ``(T,)`` (single system-wide family) or
            ``(n_families, T)`` hourly reserve requirement in MW.
        reserve_eligible: ``(n_gen,)`` boolean (single class) or
            ``(n_classes, n_gen)`` boolean — the reserve-eligible generators of
            each class. ``layout.n_reserve_classes`` must equal the class count.
        storage_zone_idx: ``(n_storage,)`` zone of each storage unit. When given
            (with ``storage_power_cap``), storage backs upward reserve too —
            batteries respond in seconds, so they back every reserve class
            (including the 10-minute quick-start class); excluding them
            understates reserve supply and overstates scarcity.
        storage_power_cap: ``(n_storage,)`` or ``(n_storage, T)`` MW power cap;
            a unit's upward reserve room is ``cap - discharge + charge``.
        balance_zone_mask: ``(n_families, n_zones)`` boolean — member zones of
            each reserve family. ``None`` builds a single system-wide family
            spanning every zone (the legacy ERCOT/PJM behaviour).
        balance_ordc_counts: ``(n_families,)`` number of ORDC shortfall steps
            owned by each family; they partition the family-major ORDC block
            and must sum to ``layout.n_ordc_steps``. ``None`` assigns every step
            to the single system-wide family.
        balance_reserve_class: ``(n_families,)`` int — the reserve class index
            each family draws on. ``None`` (or all-zero) puts every family on
            class 0 (the single-class default). A ``-1`` entry marks an
            ALL-CLASS family: its balance row sums the reserve of **every**
            class over its member zones (``sum_c sum_{z in f} R[c,z]``) — the
            ERCOT lumped ORDC total-reserve curve (RTORPA), which prices the
            aggregate reserve level that every AS product's held MW counts
            toward, layered on top of the per-product families.
        online_gated: ``(n_classes,)`` boolean — classes whose headroom is
            online-gated (synchronised/spinning reserve). For a gated class the
            shared-headroom row is ``R[c,z] - online_rho * sum_g P[g] <= 0``
            instead of ``sum_g P[g] + R[c,z] <= sum_g cap[g]``, so idle (P=0)
            capacity contributes no reserve and only online generation backs it.
            ``None`` (default) leaves every class idle-allowed (legacy). Applies
            to the legacy per-class headroom; ignored under an additive
            ``headroom_products`` spec.
        online_rho: the online-headroom multiplier for gated classes — how much
            spinning reserve an online unit backs per MW of output (~ the fleet
            ``(pmax-pmin)/pmin`` at min load). Default 1.0.
        headroom_eligible: ``(n_headroom_rows, n_gen)`` boolean — the eligible
            generators of each *additive* headroom row. When supplied (with
            ``headroom_products``) it REPLACES the per-class headroom rows with
            caller-specified rows, so several reserve products can share one
            headroom pool ADDITIVELY (ERCOT's RegUp/RRS/ECRS/NonSpin each hold
            *separate* capacity, ~7-8 GW total, unlike NYISO's nested products
            where one MW counts for both tiers). ``None`` keeps the legacy
            per-class headroom (one row per class, byte-identical).
        headroom_products: ``(n_headroom_rows, n_reserve_classes)`` boolean —
            which products' (classes') per-zone reserve ``R[p,z]`` enter each
            headroom row's sum. Row ``h`` reads
            ``sum_{g in headroom_eligible[h] ∩ z} P[g] + sum_{p in
            headroom_products[h]} R[p,z] <= cap(headroom_eligible[h], z) +
            headroom_extra_cap[h,z]``. Nesting a "fast" row (RegUp+RRS+ECRS on
            the online-responsive set) inside an "all" row (every product on the
            online + offline-quick set) gives the additive quality cascade: a
            slow Non-Spin MW can come from offline quick-start, while the fast
            products are bounded by the smaller online-responsive headroom.
        headroom_extra_cap: ``(n_headroom_rows, n_zones, T)`` or
            ``(n_headroom_rows, n_zones)`` MW — extra non-generator headroom
            added to each additive row's RHS (e.g. offline quick-start capacity
            that backs Non-Spin without an energy term). ``None`` adds nothing.
        reserve_supply_cap: ``(n_headroom_rows, T)`` MW — a **system-wide** upper
            bound on the cleared reserve of each additive headroom row's products,
            ``sum_z sum_{p in headroom_products[h]} R[p,z] <= reserve_supply_cap[h,t]``.
            One row per headroom tier per hour, inserted **before** the balance
            rows so the balance dual indexing is unchanged. Re-scopes the reserve
            *supply* to a measured online-responsive capability (ERCOT RTOLCAP/
            RTOFFCAP) instead of the full-fleet headroom in the headroom RHS, so
            modeled reserve tightens into the band the ORDC demand curve prices.
            ``None`` (and the legacy per-class spec) adds no cap rows.
        storage_duration_h: ``(n_reserve_classes,)`` per-product sustained-delivery
            duration in hours (ERCOT ``ERCOT_AS_PRODUCT_DURATION_H``: RegUp/RRS 1 h,
            ECRS 2 h, Non-Spin 4 h). When supplied (and storage is present), the
            ERCOT endogenous-storage DURATION GATE is active: storage is REMOVED
            from the thermal shared-headroom rows and given its own explicit
            per-zone reserve columns ``RS[c,z]`` (``layout._storage_reserve_off``),
            with three additions — (a) a per-zone storage power-competition row
            ``sum_c RS[c,z] + sum_{s in z}(Dis[s]-Chg[s]) <= sum_{s in z} cap[s]``
            (the same power split that was implicit in the shared headroom, now
            explicit); (b) a per-zone LP-linear duration gate
            ``sum_c dur_c*RS[c,z] - sum_{s in z} SOC[s] <= 0`` linking cleared
            storage AS to state of charge, so a 1-h battery cannot sell 4-h
            Non-Spin on its full power; and (c) the ``RS[c,z]`` reserve joins the
            balance rows (and the supply-cap rows, so cleared storage AS still
            counts under RTOLCAP) alongside the thermal ``R[c,z]``. Both new row
            families are per-zone-hour and fully vectorized (``sp.kron`` over
            hours, no hour loop). The gate uses the zone-aggregate SOC
            (``sum_{s in z} SOC[s]``), a small relaxation when a zone mixes battery
            durations. ``None`` (default) keeps storage pooled in the shared
            headroom (byte-identical to the pre-gate co-opt).

    Returns:
        ``(block, row_lower, row_upper)``: the stacked headroom + balance rows
        and their bounds. Headroom rows are ``<=`` (lower ``-inf``); balance
        rows are ``>=`` (upper ``+inf``). Headroom rows are class-major then
        zone within each hour (row ``t*(n_classes*n_zones) + c*n_zones + z``);
        balance rows are family-major within each hour (row ``t*n_families+f``).
    """
    T = layout.T
    n_zones = layout.n_zones
    n_storage = layout.n_storage
    cap = fleet.pmax[:, np.newaxis] * fleet.availability  # (n_gen, T)
    zone_idx = np.asarray(fleet.zone_idx, dtype=int)

    # Per-class eligibility: accept a flat (n_gen,) mask (single class) or a
    # (n_classes, n_gen) stack. n_classes here must match layout.n_reserve //
    # n_zones (= layout.n_reserve_classes).
    elig2d = np.atleast_2d(
        np.asarray(reserve_eligible, dtype=bool)
    )  # (n_classes, n_gen)
    n_classes = elig2d.shape[0]

    use_storage = (
        n_storage > 0 and storage_zone_idx is not None and storage_power_cap is not None
    )
    # Duration gate (ERCOT endogenous storage AS): when per-product durations are
    # supplied and storage is present, storage is pulled OUT of the thermal
    # shared-headroom rows and given its own RS[c,z] columns + power/duration
    # rows (built after the headroom/supply-cap blocks below). ``gate`` guards
    # the two behaviours: (1) skip the storage terms in the thermal headroom
    # (else storage power is double-counted), (2) emit the RS row families.
    gate = use_storage and storage_duration_h is not None
    if gate:
        dur = np.asarray(storage_duration_h, dtype=float).reshape(n_classes)
    if use_storage:
        s_zone = np.asarray(storage_zone_idx, dtype=int)
        s_idx = np.arange(n_storage)
        spc = np.asarray(storage_power_cap, dtype=float)
        zone_storage = _build_zone_storage_map(s_zone, n_zones, n_storage)

    # --- Shared-headroom per-hour block, (n_hr*n_zones, vph). Each headroom row
    # h, zone z (row h*n_zones + z) reads
    #   sum_{g in E_h ∩ z} P[g] + sum_{p in Prod_h} R[p,z] <= cap(E_h, z) + extra
    # where E_h is the row's eligible generator set, Prod_h the set of products
    # (reserve classes) whose per-zone reserve it bounds, and the RHS the
    # eligible thermal + storage + extra capacity. The DEFAULT (legacy) spec is
    # one row per reserve class c bounding only its own R[c,z] against its
    # class-c eligible capacity — byte-identical to the previous per-class loop.
    # The ADDITIVE spec (``headroom_products`` supplied) lets several products
    # share one headroom row, so ERCOT's RegUp/RRS/ECRS/NonSpin compete for the
    # same capacity instead of each independently reusing it. Storage (when
    # supplied) backs every headroom row — batteries respond in seconds, so a
    # unit's upward room (cap - Dis + Chg) enters every row's R sum, its discharge
    # column with +1 and charge with -1 and its power cap added to the RHS.
    if headroom_products is None:
        # Legacy per-class spec: row c eligible = class-c gens, bounds R[c].
        hr_elig = elig2d  # (n_classes, n_gen)
        hr_prod = np.eye(n_classes, dtype=bool)  # (n_classes, n_classes)
        extra = None
    else:
        hr_elig = np.atleast_2d(np.asarray(headroom_eligible, dtype=bool))
        hr_prod = np.atleast_2d(np.asarray(headroom_products, dtype=bool))
        extra = (
            None
            if headroom_extra_cap is None
            else np.asarray(headroom_extra_cap, float)
        )
    n_hr = hr_prod.shape[0]
    rows: list[np.ndarray] = []
    cols: list[np.ndarray] = []
    vals: list[np.ndarray] = []
    z_all = np.arange(n_zones)
    zone_cap = np.zeros((n_hr * n_zones, T))  # RHS, headroom-row-major
    gated = (
        np.zeros(n_classes, dtype=bool)
        if online_gated is None
        else np.asarray(online_gated, dtype=bool).reshape(n_classes)
    )
    for h in range(n_hr):
        base = h * n_zones
        e_idx = np.flatnonzero(hr_elig[h])
        if headroom_products is None and gated[h]:
            # ONLINE-GATED (synchronised/spinning) class, legacy per-class path:
            # reserve can come only from ONLINE capacity, not idle headroom. Row
            # reads ``R[c,z] - rho * sum_{elig g in z} P[g] <= 0`` -> a unit at
            # P=0 contributes nothing (an offline peaker is NOT spinning
            # reserve), and an online unit backs ``rho``x its output (rho = the
            # fleet online-headroom ratio, ~ (pmax-pmin)/pmin near min load). The
            # RHS is 0 (no idle-capacity credit) and storage is excluded (its
            # room is not synchronised thermal spin). LP-linear proxy for
            # commitment-gated spinning reserve (path A); the exact gate needs an
            # online binary (path B / model.commitment). The ERCOT multi-product
            # additive spec uses the P2 commitment screen instead (its fa_p2
            # availability zeroes idle slow-start capacity out of the RHS), so
            # gating does not apply there.
            rows.append(base + zone_idx[e_idx])
            cols.append(e_idx)
            vals.append(np.full(e_idx.size, -float(online_rho)))  # -rho * P[g]
            rows.append(base + z_all)
            cols.append(layout._reserve_off + base + z_all)
            vals.append(np.ones(n_zones))  # +R[c,z]
            # zone_cap stays 0 for this class (no idle/storage credit).
            continue
        # eligible thermal P columns -> this headroom row (zone-summed)
        rows.append(base + zone_idx[e_idx])
        cols.append(e_idx)
        vals.append(np.ones(e_idx.size))
        # reserve columns R[p, z] for every product p bounded by this row
        for p in np.flatnonzero(hr_prod[h]):
            rows.append(base + z_all)
            cols.append(layout._reserve_off + int(p) * n_zones + z_all)
            vals.append(np.ones(n_zones))
        # eligible-generator -> zone incidence for this row's RHS capacity
        zone_gen_elig = sp.csr_matrix(
            (np.ones(e_idx.size), (zone_idx[e_idx], e_idx)),
            shape=(n_zones, layout.n_gen),
        )
        zc = zone_gen_elig @ cap  # (n_zones, T)
        if use_storage and not gate:
            # Pooled storage in the thermal headroom (pre-duration-gate co-opt).
            # Under the duration gate storage has its own RS columns and power
            # row instead, so it must NOT also add its room here (double count).
            rows.append(base + s_zone)
            cols.append(layout._dis_off + s_idx)
            vals.append(np.ones(n_storage))  # +Dis
            rows.append(base + s_zone)
            cols.append(layout._chg_off + s_idx)
            vals.append(-np.ones(n_storage))  # -Chg
            if spc.ndim == 2:
                zc = zc + (zone_storage @ spc)  # (n_zones, T)
            else:
                zc = zc + (zone_storage @ spc)[:, None]
        if extra is not None:
            zc = zc + (extra[h] if extra[h].ndim == 2 else extra[h][:, None])
        zone_cap[base : base + n_zones, :] = zc
    headroom_per_hour = sp.coo_matrix(
        (np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
        shape=(n_hr * n_zones, layout.vars_per_hour),
    ).tocsr()
    headroom = sp.kron(sp.eye(T, format="csr"), headroom_per_hour, format="csr")
    # RHS: headroom-row-zone-summed eligible capacity per hour, hour-major
    # (row t*(n_hr*n_zones) + h*n_zones + z).
    hr_upper = zone_cap.T.ravel()
    hr_lower = np.full(n_hr * n_zones * T, -np.inf)

    # --- Reserve-balance per-hour block, (n_families, vph): for family f a +1
    # on its member zones' reserve columns (in family f's reserve class c_f) and
    # a +1 on its slice of the ORDC block. Row f reads
    # sum_{z in f} R[c_f,z] + sum_{k in f} ORDC_k >= req[f]. Single-family
    # default (mask None) is one row over every zone/step on class 0 — the
    # legacy ERCOT/PJM LP, byte-identical.
    if balance_zone_mask is None:
        zmask = np.ones((1, n_zones), dtype=bool)
        req2d = np.asarray(reserve_requirement, dtype=float).reshape(1, T)
        ordc_counts = np.array([layout.n_ordc_steps], dtype=int)
    else:
        zmask = np.asarray(balance_zone_mask, dtype=bool)
        req2d = np.asarray(reserve_requirement, dtype=float).reshape(zmask.shape[0], T)
        ordc_counts = np.asarray(balance_ordc_counts, dtype=int)
    n_fam = zmask.shape[0]
    if balance_reserve_class is None:
        fam_class = np.zeros(n_fam, dtype=int)
    else:
        fam_class = np.asarray(balance_reserve_class, dtype=int).reshape(n_fam)
    brows: list[np.ndarray] = []
    bcols: list[np.ndarray] = []
    bvals: list[np.ndarray] = []
    # reserve columns, family-by-family (vectorized within each family): each
    # family draws on R[c_f, z] for its member zones z, so its reserve columns
    # are offset into its class block (c_f * n_zones). fam_class[f] == -1 is
    # the ALL-CLASS family (ERCOT lumped ORDC total-reserve): it draws on every
    # class's R over its member zones, so each product's held reserve counts
    # toward the total-reserve requirement exactly once.
    for f in range(n_fam):
        zsel = np.flatnonzero(zmask[f])
        fam_classes = (
            range(n_classes) if int(fam_class[f]) < 0 else (int(fam_class[f]),)
        )
        for c in fam_classes:
            brows.append(np.full(zsel.size, f))
            bcols.append(layout._reserve_off + int(c) * n_zones + zsel)
            bvals.append(np.ones(zsel.size))
            if gate:
                # Storage's duration-gated reserve RS[c,z] backs the same family
                # as the thermal R[c,z] of its class (the all-class total family,
                # fam_class -1, sums every class's RS too — cleared storage AS
                # counts toward the lumped total exactly once).
                brows.append(np.full(zsel.size, f))
                bcols.append(layout._storage_reserve_off + int(c) * n_zones + zsel)
                bvals.append(np.ones(zsel.size))
    # ORDC columns: family-major block, family f owns the next ordc_counts[f]
    off = 0
    for f in range(n_fam):
        k = int(ordc_counts[f])
        if k:
            idx = np.arange(off, off + k)
            brows.append(np.full(k, f))
            bcols.append(layout._ordc_off + idx)
            bvals.append(np.ones(k))
            off += k
    bal_per_hour = sp.coo_matrix(
        (np.concatenate(bvals), (np.concatenate(brows), np.concatenate(bcols))),
        shape=(n_fam, layout.vars_per_hour),
    ).tocsr()
    balance = sp.kron(sp.eye(T, format="csr"), bal_per_hour, format="csr")
    # Hour-major RHS (row t*n_fam + f): req2d is (n_fam, T) -> transpose -> ravel.
    bal_lower = req2d.T.ravel()
    bal_upper = np.full(n_fam * T, np.inf)

    # --- Optional reserve-supply cap block, (n_hr, vph). One system-wide row per
    # headroom row h capping that row's cleared reserve:
    #   sum_z sum_{p in Prod_h} R[p,z] <= reserve_supply_cap[h,t].
    # Inserted BETWEEN the headroom and balance blocks so the reserve-balance
    # rows stay the final n_fam*T (the dual indexing in DispatchModel relies on
    # this). Re-scopes reserve SUPPLY to a measured online-responsive capability
    # (ERCOT RTOLCAP) vs the over-counted full-fleet headroom in zone_cap. Works
    # for BOTH the additive multi-product spec (one cap row per headroom tier) and
    # the legacy per-class spec (``hr_prod`` is then the class identity, so one
    # cap row per reserve class). Absent (``reserve_supply_cap is None``) the LP
    # is byte-identical (no cap block).
    blocks = [headroom]
    lowers = [hr_lower]
    uppers = [hr_upper]
    if reserve_supply_cap is not None:
        cap = np.asarray(reserve_supply_cap, dtype=float).reshape(n_hr, T)
        crows: list[np.ndarray] = []
        ccols: list[np.ndarray] = []
        cvals: list[np.ndarray] = []
        for h in range(n_hr):
            for p in np.flatnonzero(hr_prod[h]):
                crows.append(np.full(n_zones, h))
                ccols.append(layout._reserve_off + int(p) * n_zones + z_all)
                cvals.append(np.ones(n_zones))
                if gate:
                    # Duration-gated storage AS counts under the same supply cap
                    # (RTOLCAP includes online batteries), so its RS[p,z] joins
                    # each tier's cap row exactly as the thermal R[p,z] does.
                    crows.append(np.full(n_zones, h))
                    ccols.append(layout._storage_reserve_off + int(p) * n_zones + z_all)
                    cvals.append(np.ones(n_zones))
        cap_per_hour = sp.coo_matrix(
            (np.concatenate(cvals), (np.concatenate(crows), np.concatenate(ccols))),
            shape=(n_hr, layout.vars_per_hour),
        ).tocsr()
        cap_block = sp.kron(sp.eye(T, format="csr"), cap_per_hour, format="csr")
        # Hour-major RHS (row t*n_hr + h): cap is (n_hr, T) -> transpose -> ravel.
        blocks.append(cap_block)
        lowers.append(np.full(n_hr * T, -np.inf))
        uppers.append(cap.T.ravel())

    # --- Optional ON-LINE-CAPACITY ENVELOPE block, (n_hr, vph). The G-22
    # commitment-thinness cap: one system-wide row per headroom row h bounding
    # that row's ENERGY + RESERVE by the committed on-line capacity —
    #   sum_z sum_{g in E_h ∩ z} P[g] + sum_z sum_{p in Prod_h} R[p,z]
    #       (+ sum_z sum_p RS[p,z] if the storage duration gate is on)
    #       <= online_capacity_cap[h,t].
    # Identical placement/shape to the reserve-supply cap above (inserted BEFORE
    # the balance rows so the balance dual indexing is unchanged) — but the added
    # P terms make it condition-responsive: the LP can serve/reserve no more
    # thermal than the real system had on-line, so on a tight (high-energy) hour
    # reserve is forced into shortage and the ORDC/co-opt channel prices the hour
    # up with NO offer-height change. Non-envelope tiers carry the uncapped
    # sentinel RHS (scarcity.ercot_online_capacity_envelope_mw), so their row is
    # always slack. Absent (``online_capacity_cap is None``) the LP is unchanged.
    if online_capacity_cap is not None:
        oc = np.asarray(online_capacity_cap, dtype=float).reshape(n_hr, T)
        erows: list[np.ndarray] = []
        ecols: list[np.ndarray] = []
        evals: list[np.ndarray] = []
        for h in range(n_hr):
            # eligible thermal energy P[g] for this tier's generators (zone-summed
            # into the single system-wide row h — one row per tier per hour).
            e_idx = np.flatnonzero(hr_elig[h])
            erows.append(np.full(e_idx.size, h))
            ecols.append(e_idx)
            evals.append(np.ones(e_idx.size))
            for p in np.flatnonzero(hr_prod[h]):
                erows.append(np.full(n_zones, h))
                ecols.append(layout._reserve_off + int(p) * n_zones + z_all)
                evals.append(np.ones(n_zones))
                if gate:
                    erows.append(np.full(n_zones, h))
                    ecols.append(layout._storage_reserve_off + int(p) * n_zones + z_all)
                    evals.append(np.ones(n_zones))
        env_per_hour = sp.coo_matrix(
            (np.concatenate(evals), (np.concatenate(erows), np.concatenate(ecols))),
            shape=(n_hr, layout.vars_per_hour),
        ).tocsr()
        env_block = sp.kron(sp.eye(T, format="csr"), env_per_hour, format="csr")
        blocks.append(env_block)
        lowers.append(np.full(n_hr * T, -np.inf))
        uppers.append(oc.T.ravel())

    # --- Storage duration-gate blocks (ERCOT endogenous storage AS). Two
    # per-zone-hour row families, inserted BEFORE the balance rows so the balance
    # dual stays the final n_fam*T. Both fully vectorized (sp.kron over hours).
    #  1. Power competition (n_zones per hour): the storage power split, now
    #     explicit since storage left the thermal headroom —
    #       sum_c RS[c,z] + sum_{s in z}(Dis[s] - Chg[s]) <= sum_{s in z} cap[s].
    #  2. Duration gate (n_zones per hour): the ESR State-of-Charge rule —
    #       sum_c dur_c * RS[c,z] - sum_{s in z} SOC[s] <= 0,
    #     so the stored energy (zone-aggregate SOC) must cover each product's
    #     award for its full deployment duration. Gating on the same-hour SOC[t]
    #     column is exact for held (undeployed) reserve — the power row keeps that
    #     MW from also discharging, so the SOC is not drawn down.
    if gate:
        # Power-competition per-hour matrix, (n_zones, vph).
        pw_rows: list[np.ndarray] = []
        pw_cols: list[np.ndarray] = []
        pw_vals: list[np.ndarray] = []
        for c in range(n_classes):
            pw_rows.append(z_all)
            pw_cols.append(layout._storage_reserve_off + c * n_zones + z_all)
            pw_vals.append(np.ones(n_zones))  # +RS[c,z]
        pw_rows.append(s_zone)
        pw_cols.append(layout._dis_off + s_idx)
        pw_vals.append(np.ones(n_storage))  # +Dis
        pw_rows.append(s_zone)
        pw_cols.append(layout._chg_off + s_idx)
        pw_vals.append(-np.ones(n_storage))  # -Chg
        pw_per_hour = sp.coo_matrix(
            (
                np.concatenate(pw_vals),
                (np.concatenate(pw_rows), np.concatenate(pw_cols)),
            ),
            shape=(n_zones, layout.vars_per_hour),
        ).tocsr()
        pw_block = sp.kron(sp.eye(T, format="csr"), pw_per_hour, format="csr")
        # RHS: zone-summed storage power cap, (n_zones, T) hour-major.
        if spc.ndim == 2:
            zcap = zone_storage @ spc  # (n_zones, T)
        else:
            zcap = np.broadcast_to((zone_storage @ spc)[:, None], (n_zones, T))
        blocks.append(pw_block)
        lowers.append(np.full(n_zones * T, -np.inf))
        uppers.append(np.ascontiguousarray(zcap).T.ravel())

        # Duration-gate per-hour matrix, (n_zones, vph).
        du_rows: list[np.ndarray] = []
        du_cols: list[np.ndarray] = []
        du_vals: list[np.ndarray] = []
        for c in range(n_classes):
            du_rows.append(z_all)
            du_cols.append(layout._storage_reserve_off + c * n_zones + z_all)
            du_vals.append(np.full(n_zones, float(dur[c])))  # +dur_c * RS[c,z]
        du_rows.append(s_zone)
        du_cols.append(layout._soc_off + s_idx)
        du_vals.append(-np.ones(n_storage))  # -SOC[s]
        du_per_hour = sp.coo_matrix(
            (
                np.concatenate(du_vals),
                (np.concatenate(du_rows), np.concatenate(du_cols)),
            ),
            shape=(n_zones, layout.vars_per_hour),
        ).tocsr()
        du_block = sp.kron(sp.eye(T, format="csr"), du_per_hour, format="csr")
        blocks.append(du_block)
        lowers.append(np.full(n_zones * T, -np.inf))
        uppers.append(np.zeros(n_zones * T))

    blocks.append(balance)
    lowers.append(bal_lower)
    uppers.append(bal_upper)
    # Free-concat (see _vstack_csr_free): drop the two large sub-block names so
    # the list is their sole owner and the shared-headroom block (T * n_gen nnz,
    # the largest here) is released before the stacked result is allocated.
    # Byte-identical to sp.vstack(blocks).
    del headroom, balance
    block = _vstack_csr_free(blocks, layout.total_columns)
    row_lower = np.concatenate(lowers)
    row_upper = np.concatenate(uppers)
    return block, row_lower, row_upper


def _build_reserve_rows_pergen(
    layout: VariableLayout,
    fleet: FleetArrays,
    reserve_requirement: np.ndarray,
    pergen_gen_idx: np.ndarray,
    pergen_col: np.ndarray | None = None,
    balance_zone_mask: np.ndarray | None = None,
    balance_ordc_counts: np.ndarray | None = None,
    posture_pools: np.ndarray | None = None,
    posture_mlf: np.ndarray | None = None,
    pergen_ramp10: np.ndarray | None = None,
    storage_zone_idx: np.ndarray | None = None,
    storage_power_cap: np.ndarray | None = None,
    storage_duration_h: np.ndarray | None = None,
    pergen_col_pool: np.ndarray | None = None,
    balance_col_mask: np.ndarray | None = None,
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Build the PER-GENERATOR energy+reserve co-optimization rows.

    The per-unit alternative to :func:`_build_reserve_rows`: one reserve
    variable ``R[r,t]`` per reserve-providing *asset* instead of one per
    zone-class, so reserve competes with energy **on the same marginal unit**
    — the structure that prices the sub-shortage opportunity-cost reserve
    band (docs/multi-iso/pjm-reserve-ordc.md Phase 2). An asset is one
    generator by default (``pergen_col`` omitted: R column ``j`` pairs with
    ``pergen_gen_idx[j]``), or a group of generators sharing an R column
    (``pergen_col[j]`` maps member ``j`` to its column) — the tranche-binned
    fleets aggregate per (plant, class): a plant's tranches dispatch
    bang-bang, so headroom and the 10-minute ramp are plant properties
    (the ``pjm_online_reserve`` doctrine), and the aggregation cuts the
    per-gen LP's row/column count ~4x on a 15 GB box without changing the
    physics (``sum ramp10[tranches] == RAMP10_FRAC[class] x plant pmax``).
    Two families of rows, both vectorized (no hour loop):

    * **Joint headroom** — for each R column ``r`` and hour ``t``:
      ``sum_{members j of r} P[g_j,t] + R[r,t] <= sum_j cap[g_j,t]``
      (``cap = pmax x availability``; one P term for the default 1:1
      mapping). A MW held as reserve cannot also be dispatched as energy, so
      on a fully-loaded marginal asset the row's dual is the forgone energy
      margin — the opportunity cost that lifts the reserve clearing price
      above $0 without any shortfall. The 10-minute deliverability cap
      ``R[r] <= ramp10[r]`` is a *variable bound*
      (:func:`build_variable_bounds`), not a row.
    * **Reserve balance** — one row per reserve family ``f`` and hour ``t``:
      ``sum_{r: zone[r] in family f} R[r,t] + sum_{k in f} ORDC_k[t] >=
      requirement[f,t]``. Families follow the zone-mask convention of
      :func:`_build_reserve_rows` (PJM: the RTO Reserve Zone over every model
      zone, plus the nested Mid-Atlantic/Dominion Reserve Subzone — a MAD
      reserve MW counts toward both, Manual 11 sec 4.2). The binding family's
      dual is that family's reserve clearing price; the joint-headroom rows
      transfer it into the member zones' energy LMPs.

    Storage backs reserve via the SAME duration-gated per-zone ``RS[c,z]``
    columns as the zone-aggregate path (issue #1492, CAISO
    ``caiso_reserve_coopt``): when the layout allocated storage-reserve columns
    (``reserve_storage`` + ``storage_duration_h`` + storage present) and the
    three ``storage_*`` args are supplied, each family's balance row gains the
    ``RS[0,z]`` columns of its member zones, and the two zone-hour row families
    of the zone path are appended between the posture and balance blocks: power
    competition ``Σ_c RS[c,z] + Σ_{s∈z}(Dis−Chg) ≤ Σ_{s∈z} cap[s]`` and the SOC
    duration gate ``Σ_c dur_c·RS[c,z] − Σ_{s∈z} SOC[s] ≤ 0``. The pergen layout
    carries exactly one reserve class, so ``RS[0,z]`` backs every family over
    its member zones — the same co-drawn convention as the thermal R pool
    (CAISO spin/non-spin share the marginal MW, §27.1.2.4).

    Args:
        layout: Variable layout with ``n_reserve == n_r`` (R-column count) and
            ``n_reserve_classes == 1``.
        fleet: Fleet arrays supplying ``pmax``, ``(n_gen, T)`` availability and
            per-generator ``zone_idx``.
        reserve_requirement: ``(T,)`` (single family) or ``(n_families, T)``
            hourly requirement in MW.
        pergen_gen_idx: ``(n_members,)`` int — the fleet index of every member
            generator backing an R column.
        pergen_col: ``(n_members,)`` int — the R column of each member
            (``0..n_r-1``; every column must have at least one member and all
            of a column's members must share a zone). ``None`` is the 1:1
            identity (``n_members == n_r``).
        balance_zone_mask: ``(n_families, n_zones)`` boolean member-zone mask;
            ``None`` builds a single system-wide family.
        balance_ordc_counts: ``(n_families,)`` ORDC steps owned by each family
            (family-major partition of the ORDC block); ``None`` assigns every
            step to the single family.
        posture_pools: ``(q,)`` R-pool indices carrying an online-capacity
            variable U (the commitment-posture lever, design note §A). For a
            postured pool the joint-headroom row is re-anchored to online
            capacity — ``Σ P + R − U ≤ 0`` (same nnz + one U coefficient;
            the member-capacity RHS moves to U's upper bound) — and three
            posture families are appended between the joint and balance
            blocks: min-load coupling ``Σ P − mlf·U ≥ 0`` (pools with
            ``mlf > 0``), startup counting ``U[t] − U[t−1] − SU[t] ≤ 0``
            (cyclic, like the SOC boundary), and the online ramp gate
            ``R − ρ(t)·U ≤ 0`` with ``ρ = pool ramp10 / pool capacity``
            (offline capacity contributes no 10-minute ramp).
        posture_mlf: ``(q,)`` min-stable-when-online fraction per postured
            pool (CEMS-measured, reserve_config._posture_pool_params).
        pergen_ramp10: the ``(n_r,)`` or ``(n_r, T)`` deliverable-ramp caps
            (required with ``posture_pools`` for the ramp-gate ρ).
        pergen_col_pool: ``(n_r,)`` int — the joint-headroom POOL of each R
            column (PJM ``pjm_reserve_pergen_sync`` product split: a pool's
            synchronized and non-synchronized product columns share ONE joint
            P+R row and its member-capacity RHS, so a reserve award of either
            product consumes the same iron). When given, ``pergen_col`` maps
            members to POOLS (``0..n_pools-1``) rather than to R columns.
            ``None`` is the identity (columns ≡ pools) — byte-identical to
            the pre-split layout. Mutually exclusive with ``posture_pools``
            (the posture U re-anchor indexes pools 1:1 with R columns).
        balance_col_mask: ``(n_families, n_r)`` bool — each family's complete
            R-column selection (zone ∧ product), replacing the zone-only
            selection derived from ``balance_zone_mask``. ``None`` keeps the
            zone-derived selection (byte-identical).

    Returns:
        ``(block, row_lower, row_upper)``: joint-headroom rows (``<=``,
        hour-major then R-column order), then the posture families when
        postured (min-load ``>=``, startup ``<=``, ramp gate ``<=``), then the
        storage duration-gate families when storage-gated (power competition
        ``<=``, SOC duration ``<=``), then balance rows (``>=``, hour-major
        then family order — the final ``n_families * T`` rows, the position
        the ``DispatchModel`` dual extraction relies on).
    """
    T = layout.T
    n_zones = layout.n_zones
    gidx = np.asarray(pergen_gen_idx, dtype=int)
    col = (
        np.arange(gidx.size)
        if pergen_col is None
        else np.asarray(pergen_col, dtype=int)
    )
    if col.shape != gidx.shape:
        raise ValueError(
            f"pergen_col shape {col.shape} != pergen_gen_idx shape {gidx.shape}"
        )
    n_r = layout.n_reserve
    # Product split (pergen_col_pool): pergen_col maps members to POOLS and
    # col_pool maps each of the n_r R columns to its pool; identity when the
    # split is absent (pools ≡ columns, the pre-split layout, byte-identical).
    if pergen_col_pool is not None:
        if posture_pools is not None:
            raise ValueError(
                "pergen_col_pool (the product-split pergen layout) is not "
                "composable with posture_pools — the posture U re-anchor "
                "indexes pools 1:1 with R columns"
            )
        col_pool = np.asarray(pergen_col_pool, dtype=int)
        if col_pool.shape != (n_r,):
            raise ValueError(f"pergen_col_pool shape {col_pool.shape} != ({n_r},)")
        n_pools = int(col_pool.max()) + 1 if col_pool.size else 0
        if np.unique(col_pool).size != n_pools:
            raise ValueError("pergen_col_pool must cover every pool 0..n_pools-1")
        if (
            col.size == 0
            or int(col.max()) + 1 != n_pools
            or (np.unique(col).size != n_pools)
        ):
            raise ValueError(
                "with pergen_col_pool, pergen_col must cover every pool "
                f"0..n_pools-1 (n_pools={n_pools}, "
                f"pools covered={np.unique(col).size})"
            )
    else:
        col_pool = np.arange(n_r, dtype=int)
        n_pools = n_r
        if col.size == 0 or int(col.max()) + 1 != n_r or np.unique(col).size != n_r:
            raise ValueError(
                "pergen_col must cover every R column 0..n_reserve-1 "
                f"(n_reserve={n_r}, columns covered={np.unique(col).size})"
            )
    zone_idx = np.asarray(fleet.zone_idx, dtype=int)
    # Duration-gated storage reserve (issue #1492): active iff the layout
    # allocated RS columns (it already encoded reserve_storage + durations +
    # storage-present) AND the storage args reached this builder. The layout's
    # class count sizes the RS block; the pergen layout guarantees one class.
    gate = (
        layout.n_storage_reserve > 0
        and storage_zone_idx is not None
        and storage_power_cap is not None
        and storage_duration_h is not None
    )
    if gate:
        n_classes = layout.n_reserve_classes
        dur = np.asarray(storage_duration_h, dtype=float).reshape(n_classes)
        s_zone = np.asarray(storage_zone_idx, dtype=int)
        n_storage = s_zone.shape[0]
        s_idx = np.arange(n_storage)
        spc = np.asarray(storage_power_cap, dtype=float)
        zone_storage = _build_zone_storage_map(s_zone, n_zones, n_storage)
        z_all = np.arange(n_zones)
    # Member -> R-column incidence, for the summed-capacity RHS and the
    # per-column zone below.
    member_map = sp.csr_matrix(
        (np.ones(gidx.size), (col, np.arange(gidx.size))),
        shape=(n_pools, gidx.size),
    )
    # All of a pool's members must share a zone (a plant is in one zone) —
    # the balance families select R columns by zone. Column zone = its pool's
    # zone (identity map without the product split).
    pool_zone = np.zeros(n_pools, dtype=int)
    pool_zone[col] = zone_idx[gidx]
    if np.any(member_map @ (zone_idx[gidx] != pool_zone[col]).astype(float) > 0):
        raise ValueError("pergen_col groups generators from different zones")
    r_zone = pool_zone[col_pool]

    # --- Joint-headroom per-hour block, (n_pools, vph): pool row p reads
    # sum_{members j} P[g_j] + sum_{columns r of p} R[r] <= sum_j cap[g_j]
    # (one R term per pool without the product split). A POSTURED pool's row
    # is re-anchored to its online capacity instead — sum P + R − U <= 0 —
    # so reserve can only come from capacity the LP keeps online; the member
    # capacity sum moves to U's upper bound (build_variable_bounds).
    q = 0 if posture_pools is None else int(np.asarray(posture_pools).size)
    jrows = [col, col_pool]
    jcols = [layout._p_off + gidx, layout._reserve_off + np.arange(n_r)]
    jvals = [np.ones(gidx.size), np.ones(n_r)]
    # Summed member capacity per pool, (n_pools, T). Compute pmax*availability
    # ONLY on the reserve members instead of materializing the full (n_gen, T)
    # fleet ``cap`` and fancy-indexing it: byte-identical operands (member i is
    # ``pmax[gidx[i]] * availability[gidx[i]]`` either way), but the dense
    # intermediate is (n_members, T) rather than (n_gen, T) held alongside its
    # (n_members, T) index copy, and it is released before the large ``joint``
    # kron allocates — driver (a) of the reserve-column-construction peak (G-40).
    cap_members = fleet.pmax[gidx][:, np.newaxis] * fleet.availability[gidx]
    pool_cap = member_map @ cap_members  # (n_pools, T) member caps summed per pool
    del cap_members
    joint_rhs = pool_cap  # only copied below when a postured pool mutates it
    if q:
        ppools = np.asarray(posture_pools, dtype=int)
        jrows.append(ppools)
        jcols.append(layout._posture_u_off + np.arange(q))
        jvals.append(-np.ones(q))
        # Zero the postured pools' capacity RHS on a copy — pool_cap must stay
        # intact for the ramp-gate ρ (uses pool_cap[ppools]) below.
        joint_rhs = pool_cap.copy()
        joint_rhs[ppools, :] = 0.0
    joint_per_hour = sp.coo_matrix(
        (
            np.concatenate(jvals),
            (np.concatenate(jrows), np.concatenate(jcols)),
        ),
        shape=(n_pools, layout.vars_per_hour),
    ).tocsr()
    joint = sp.kron(sp.eye(T, format="csr"), joint_per_hour, format="csr")
    # RHS hour-major (row t*n_pools + p): member caps summed per pool,
    # (n_pools, T); 0 for postured pools (the capacity bound lives on U).
    joint_upper = joint_rhs.T.ravel()
    joint_lower = np.full(n_pools * T, -np.inf)

    # --- Commitment-posture families (between joint and balance so the
    # balance rows stay the final n_families*T — the dual-extraction anchor).
    posture_blocks: list[sp.csr_matrix] = []
    posture_lower: list[np.ndarray] = []
    posture_upper: list[np.ndarray] = []
    if q:
        mlf = np.asarray(posture_mlf, dtype=float)
        # (a) Min-load coupling, pools with measured mlf > 0:
        #     sum_{members} P − mlf·U >= 0 (being online costs min-load
        #     energy; binds only capacity the LP itself holds online).
        m_sel = np.flatnonzero(mlf > 0.0)
        if m_sel.size:
            sel_pool = ppools[m_sel]  # R-pool index per min-load row
            # Members of the selected pools: map each member's pool to its
            # min-load row (or -1 when the member's pool carries no row).
            pool_to_row = np.full(n_r, -1, dtype=int)
            pool_to_row[sel_pool] = np.arange(m_sel.size)
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
                shape=(m_sel.size, layout.vars_per_hour),
            ).tocsr()
            posture_blocks.append(
                sp.kron(sp.eye(T, format="csr"), ml_per_hour, format="csr")
            )
            posture_lower.append(np.zeros(m_sel.size * T))
            posture_upper.append(np.full(m_sel.size * T, np.inf))

        # (b) Startup counting, cyclic: U[p,t] − U[p,t−1] − SU[p,t] <= 0.
        #     Same wrap convention as the storage SOC boundary: hour 0 links
        #     to hour T−1, so a year-crossing posture carries no free start.
        d0 = sp.coo_matrix(
            (
                np.concatenate([np.ones(q), -np.ones(q)]),
                (
                    np.concatenate([np.arange(q), np.arange(q)]),
                    np.concatenate(
                        [
                            layout._posture_u_off + np.arange(q),
                            layout._posture_su_off + np.arange(q),
                        ]
                    ),
                ),
            ),
            shape=(q, layout.vars_per_hour),
        ).tocsr()
        d_prev = sp.coo_matrix(
            (
                -np.ones(q),
                (np.arange(q), layout._posture_u_off + np.arange(q)),
            ),
            shape=(q, layout.vars_per_hour),
        ).tocsr()
        shift_prev = sp.csr_matrix(
            (np.ones(T), (np.arange(T), (np.arange(T) - 1) % T)),
            shape=(T, T),
        )
        posture_blocks.append(
            sp.kron(sp.eye(T, format="csr"), d0, format="csr")
            + sp.kron(shift_prev, d_prev, format="csr")
        )
        posture_lower.append(np.full(q * T, -np.inf))
        posture_upper.append(np.zeros(q * T))

        # (c) Online ramp gate: R[p,t] − ρ[p,t]·U[p,t] <= 0 with
        #     ρ = pool deliverable ramp10 / pool capacity (both availability-
        #     scaled, so ρ is the pool's class ramp fraction) — offline
        #     capacity contributes no 10-minute ramp, the design's scarcity
        #     payoff. Hour-varying coefficients, so built directly (no kron).
        if pergen_ramp10 is None:
            raise ValueError("posture_pools requires pergen_ramp10 for the ramp gate")
        r10 = np.asarray(pergen_ramp10, dtype=float)
        if r10.ndim == 1:
            r10 = np.broadcast_to(r10[:, np.newaxis], (n_r, T))
        with np.errstate(invalid="ignore", divide="ignore"):
            rho = np.where(pool_cap[ppools] > 0, r10[ppools] / pool_cap[ppools], 0.0)
        vph = layout.vars_per_hour
        t_idx = np.repeat(np.arange(T), q)  # hour of each row, hour-major
        j_idx = np.tile(np.arange(q), T)  # posture index of each row
        rg_rows = np.arange(q * T)
        rg = sp.csr_matrix(
            (
                np.concatenate([np.ones(q * T), -rho[j_idx, t_idx]]),
                (
                    np.concatenate([rg_rows, rg_rows]),
                    np.concatenate(
                        [
                            t_idx * vph + layout._reserve_off + ppools[j_idx],
                            t_idx * vph + layout._posture_u_off + j_idx,
                        ]
                    ),
                ),
            ),
            shape=(q * T, layout.total_columns),
        )
        posture_blocks.append(rg)
        posture_lower.append(np.full(q * T, -np.inf))
        posture_upper.append(np.zeros(q * T))

    # --- Reserve-balance per-hour block, (n_families, vph): family f sums the
    # R columns of its member zones' generators plus its ORDC-step slice.
    if balance_zone_mask is None:
        zmask = np.ones((1, n_zones), dtype=bool)
        req2d = np.asarray(reserve_requirement, dtype=float).reshape(1, T)
        ordc_counts = np.array([layout.n_ordc_steps], dtype=int)
    else:
        zmask = np.asarray(balance_zone_mask, dtype=bool)
        req2d = np.asarray(reserve_requirement, dtype=float).reshape(zmask.shape[0], T)
        ordc_counts = np.asarray(balance_ordc_counts, dtype=int)
    n_fam = zmask.shape[0]
    # Per-family R-column selection: the product split supplies each family's
    # complete (zone ∧ product) mask; otherwise columns are selected by zone.
    cmask = None
    if balance_col_mask is not None:
        cmask = np.asarray(balance_col_mask, dtype=bool)
        if cmask.shape != (n_fam, n_r):
            raise ValueError(
                f"balance_col_mask shape {cmask.shape} != ({n_fam}, {n_r})"
            )
    brows: list[np.ndarray] = []
    bcols: list[np.ndarray] = []
    bvals: list[np.ndarray] = []
    for f in range(n_fam):
        sel = np.flatnonzero(cmask[f] if cmask is not None else zmask[f][r_zone])
        brows.append(np.full(sel.size, f))
        bcols.append(layout._reserve_off + sel)
        bvals.append(np.ones(sel.size))
        if gate:
            # Storage's duration-gated RS[c,z] backs every family over its
            # member zones (single pergen reserve class — the co-drawn
            # spin/non-spin convention of the thermal pool above).
            zsel = np.flatnonzero(zmask[f])
            for c in range(n_classes):
                brows.append(np.full(zsel.size, f))
                bcols.append(layout._storage_reserve_off + c * n_zones + zsel)
                bvals.append(np.ones(zsel.size))
    off = 0
    for f in range(n_fam):
        k = int(ordc_counts[f])
        if k:
            idx = np.arange(off, off + k)
            brows.append(np.full(k, f))
            bcols.append(layout._ordc_off + idx)
            bvals.append(np.ones(k))
            off += k
    bal_per_hour = sp.coo_matrix(
        (np.concatenate(bvals), (np.concatenate(brows), np.concatenate(bcols))),
        shape=(n_fam, layout.vars_per_hour),
    ).tocsr()
    balance = sp.kron(sp.eye(T, format="csr"), bal_per_hour, format="csr")
    bal_lower = req2d.T.ravel()
    bal_upper = np.full(n_fam * T, np.inf)

    # --- Storage duration-gate blocks (issue #1492 pergen storage AS): the two
    # zone-hour row families of the zone-aggregate path, verbatim, inserted
    # BEFORE the balance rows so the balance dual stays the final n_fam*T.
    #  1. Power competition: sum_c RS[c,z] + sum_{s in z}(Dis - Chg)
    #     <= sum_{s in z} cap[s] — a MW held as reserve cannot also discharge.
    #  2. Duration gate: sum_c dur_c * RS[c,z] - sum_{s in z} SOC[s] <= 0 —
    #     the stored energy must cover the award for its sustain duration
    #     (CAISO ASSOC: 30-min spin/non-spin sustain).
    gate_blocks: list[sp.csr_matrix] = []
    gate_lower: list[np.ndarray] = []
    gate_upper: list[np.ndarray] = []
    if gate:
        pw_rows: list[np.ndarray] = []
        pw_cols: list[np.ndarray] = []
        pw_vals: list[np.ndarray] = []
        for c in range(n_classes):
            pw_rows.append(z_all)
            pw_cols.append(layout._storage_reserve_off + c * n_zones + z_all)
            pw_vals.append(np.ones(n_zones))  # +RS[c,z]
        pw_rows.append(s_zone)
        pw_cols.append(layout._dis_off + s_idx)
        pw_vals.append(np.ones(n_storage))  # +Dis
        pw_rows.append(s_zone)
        pw_cols.append(layout._chg_off + s_idx)
        pw_vals.append(-np.ones(n_storage))  # -Chg
        pw_per_hour = sp.coo_matrix(
            (
                np.concatenate(pw_vals),
                (np.concatenate(pw_rows), np.concatenate(pw_cols)),
            ),
            shape=(n_zones, layout.vars_per_hour),
        ).tocsr()
        gate_blocks.append(sp.kron(sp.eye(T, format="csr"), pw_per_hour, format="csr"))
        # RHS: zone-summed storage power cap, (n_zones, T) hour-major.
        if spc.ndim == 2:
            zcap = zone_storage @ spc  # (n_zones, T)
        else:
            zcap = np.broadcast_to((zone_storage @ spc)[:, None], (n_zones, T))
        gate_lower.append(np.full(n_zones * T, -np.inf))
        gate_upper.append(np.ascontiguousarray(zcap).T.ravel())

        du_rows: list[np.ndarray] = []
        du_cols: list[np.ndarray] = []
        du_vals: list[np.ndarray] = []
        for c in range(n_classes):
            du_rows.append(z_all)
            du_cols.append(layout._storage_reserve_off + c * n_zones + z_all)
            du_vals.append(np.full(n_zones, float(dur[c])))  # +dur_c * RS[c,z]
        du_rows.append(s_zone)
        du_cols.append(layout._soc_off + s_idx)
        du_vals.append(-np.ones(n_storage))  # -SOC[s]
        du_per_hour = sp.coo_matrix(
            (
                np.concatenate(du_vals),
                (np.concatenate(du_rows), np.concatenate(du_cols)),
            ),
            shape=(n_zones, layout.vars_per_hour),
        ).tocsr()
        gate_blocks.append(sp.kron(sp.eye(T, format="csr"), du_per_hour, format="csr"))
        gate_lower.append(np.full(n_zones * T, -np.inf))
        gate_upper.append(np.zeros(n_zones * T))

    # Free-concat the reserve sub-blocks (joint headroom is by far the largest —
    # T * n_members nnz). Drop the block names first so the list owns them and
    # _vstack_csr_free can release joint before allocating the stacked result,
    # instead of scipy.vstack holding joint + result simultaneously. Byte-
    # identical; this is the reserve-column-construction peak the OOM log names.
    _res_sub: list[sp.csr_matrix | None] = [
        joint,
        *posture_blocks,
        *gate_blocks,
        balance,
    ]
    del joint, balance, posture_blocks, gate_blocks
    block = _vstack_csr_free(_res_sub, layout.total_columns)
    row_lower = np.concatenate([joint_lower, *posture_lower, *gate_lower, bal_lower])
    row_upper = np.concatenate([joint_upper, *posture_upper, *gate_upper, bal_upper])
    return block, row_lower, row_upper


def storage_reserve_mw(
    reserve_dispatch: np.ndarray,
    storage_charge: np.ndarray,
    storage_discharge: np.ndarray,
    storage_power_cap: np.ndarray,
    storage_zone_idx: np.ndarray,
    n_reserve_classes: int,
) -> np.ndarray:
    """Attribute the co-opt's cleared zone reserve to storage, ``(n_zones, T)`` MW.

    The endogenous storage energy-vs-AS split (``ercot_storage_as_endogenous``)
    runs storage and thermal on **one shared per-zone reserve pool** in the
    co-optimization headroom rows (``_build_reserve_rows`` ``use_storage`` block):
    a unit's upward-reserve room ``cap − discharge + charge`` competes with its
    own arbitrage on the same power cap, so the LP's energy-vs-AS *choice* is
    exact, but the cleared reserve variable ``R[c,z]`` is a single pooled value
    backed by thermal **and** storage room and is not split between them by the
    LP. This attributes storage's share of that pool for VALIDATION ONLY — the
    measured-vs-modeled battery AS-vs-energy split — never feeding back into the
    LP.

    The attribution is **storage-first by opportunity cost**: a battery's
    marginal cost of holding upward reserve is near zero (just the forgone energy
    arbitrage), and ERCOT batteries are the dominant, fastest fast-AS provider,
    so in a reserve-priced hour the LP fills the requirement from storage room
    before dearer thermal headroom. Storage AS in zone ``z`` hour ``t`` is then
    ``min(storage upward room, total cleared zone reserve)`` — exact when storage
    is the marginal fast-AS provider, an upper bound otherwise. Fully vectorized
    (no hour loop): the per-zone reserve is the sum across reserve classes (each
    AS product is a class in the multi-product co-opt), and storage room is
    scatter-summed to zones.

    Args:
        reserve_dispatch: ``(n_reserve_classes * n_zones, T)`` cleared reserve,
            class-major (``DispatchResult.reserve_dispatch``).
        storage_charge: ``(n_storage, T)`` cleared charge MW.
        storage_discharge: ``(n_storage, T)`` cleared discharge MW.
        storage_power_cap: ``(n_storage,)`` or ``(n_storage, T)`` power cap MW.
        storage_zone_idx: ``(n_storage,)`` zone index of each storage unit.
        n_reserve_classes: Number of reserve classes (AS products) folded into
            the per-zone reserve pool.

    Returns:
        ``(n_zones, T)`` MW of cleared reserve attributed to storage. Sum over
        zones (and divide hours) for the system AS-vs-energy split.
    """
    rd = np.asarray(reserve_dispatch, dtype=float)
    n_cz, T = rd.shape
    n_zones = n_cz // int(n_reserve_classes)
    # Per-zone total cleared reserve = sum across the reserve classes (products).
    zone_reserve = rd.reshape(int(n_reserve_classes), n_zones, T).sum(axis=0)
    # Storage upward-reserve room: cap − discharge + charge (the max additional
    # discharge swing a unit could offer up as reserve), floored at 0.
    cap = np.asarray(storage_power_cap, dtype=float)
    if cap.ndim == 1:
        cap = cap[:, None]
    room = np.clip(
        cap
        - np.asarray(storage_discharge, dtype=float)
        + np.asarray(storage_charge, dtype=float),
        0.0,
        None,
    )  # (n_storage, T)
    s_zone = np.asarray(storage_zone_idx, dtype=int)
    zone_room = np.zeros((n_zones, T), dtype=float)
    np.add.at(zone_room, s_zone, room)  # scatter-sum storage room into its zone
    return np.minimum(zone_room, zone_reserve)


def _vstack_csr_free(
    blocks: list[sp.csr_matrix | None], total_cols: int
) -> sp.csr_matrix:
    """Vertically stack CSR blocks into one, releasing each input as consumed.

    Byte-for-byte identical to ``sp.vstack(blocks, format="csr")`` — same row
    order, same canonical CSR ``(data, indices, indptr)`` and the same scipy
    index dtype — but with a much lower construction peak. ``build_constraints``
    used to grow the matrix with a pairwise chain
    (``A = sp.vstack([A, block])`` per optional block): every step allocates a
    fresh copy of the *whole* accumulated matrix, so at the final (reserve-block)
    step the transient holds ~2×(|A|+|reserve|) — the OOM-killer's
    "during reserve-column construction" peak on the plant-level MISO/PJM LPs.

    Here the output ``indptr``/``indices``/``data`` are preallocated once and
    each block's slice is copied straight in; the block is then dropped from the
    ``blocks`` list (``blocks[k] = None``) so its arrays are freed before the next
    copy. Peak ≈ |result| + |largest single block| instead of ~2×|result|. The
    logical matrix is unchanged (vertical concatenation is associative and the
    inputs are already canonical CSR), so the LP — and the Stage-6 builder-swap
    byte gate — are untouched. No Python loop over hours (rule #2): the loop is
    over the O(10) constraint blocks, not the 8760 hours.

    Args:
        blocks: CSR blocks to stack top-to-bottom (``None`` entries skipped).
            MUTATED: consumed entries are set to ``None`` to release memory.
        total_cols: column count all blocks share (``layout.total_columns``).

    Returns:
        The stacked CSR matrix.
    """
    from scipy.sparse._sputils import get_index_dtype

    present = [b for b in blocks if b is not None]
    if not present:
        return sp.csr_matrix((0, total_cols))
    if len(present) == 1:
        return present[0].tocsr()

    total_rows = sum(b.shape[0] for b in present)
    total_nnz = sum(b.nnz for b in present)
    # Match scipy.sparse.bmat/vstack's index-dtype choice exactly so the result
    # is byte-identical (int32 until nnz/cols cross 2**31, then int64).
    idx_dtype = get_index_dtype(maxval=max(total_nnz, total_cols))
    indptr = np.empty(total_rows + 1, dtype=idx_dtype)
    indices = np.empty(total_nnz, dtype=idx_dtype)
    data = np.empty(total_nnz, dtype=np.float64)
    indptr[0] = 0
    rpos = 0  # rows written so far
    npos = 0  # nnz written so far
    for k in range(len(blocks)):
        b = blocks[k]
        if b is None:
            continue
        nr = b.shape[0]
        bn = b.nnz
        # Row pointers shift by the running nnz offset; column indices and data
        # copy verbatim (same column space, already sorted per row).
        indptr[rpos + 1 : rpos + nr + 1] = b.indptr[1:] + npos
        indices[npos : npos + bn] = b.indices
        data[npos : npos + bn] = b.data
        rpos += nr
        npos += bn
        blocks[k] = None  # release this block before copying the next
    return sp.csr_matrix((data, indices, indptr), shape=(total_rows, total_cols))


def build_constraints(
    layout: VariableLayout,
    fleet: FleetArrays,
    demand: np.ndarray,
    incidence: np.ndarray | sp.spmatrix | None = None,
    storage_zone_idx: np.ndarray | None = None,
    eta_chg: np.ndarray | float | None = None,
    eta_dis: np.ndarray | float | None = None,
    rps_target: float | None = None,
    hydro_monthly_energy: np.ndarray | None = None,
    hydro_month_index: np.ndarray | None = None,
    hydro_gen_idx: np.ndarray | None = None,
    hydro_monthly_min: np.ndarray | None = None,
    oil_monthly_budget: np.ndarray | None = None,
    oil_gen_idx: np.ndarray | None = None,
    oil_month_index: np.ndarray | None = None,
    oil_gen_hour_coeff: np.ndarray | None = None,
    oil_group_index: np.ndarray | None = None,
    storage_daily_cycle_hours: int | None = None,
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
        storage_zone_idx: Zone index of each storage unit, shape
            ``(n_storage,)``. Defaults to zone ``0`` for every unit.
        eta_chg: Charge efficiency, scalar or ``(n_storage,)``. Defaults
            to ``1.0`` (lossless).
        eta_dis: Discharge efficiency, scalar or ``(n_storage,)``. Defaults
            to ``1.0`` (lossless).
        rps_target: Required renewable-energy (wind+solar) share. When not
            ``None`` and positive, one annual RPS constraint row is appended.
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
        Tuple ``(A, row_lower, row_upper)`` where ``A`` is a CSR matrix --
        the row-wise layout HiGHS consumes directly -- and the bound
        vectors give the lower and upper row bounds. The energy-balance and
        storage rows are equalities; the optional RPS row has an infinite
        upper bound.
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
        ],
        format="csr",
    )

    # Replicate the per-hour block across all hours without a Python loop.
    energy_balance = sp.kron(sp.eye(T, format="csr"), per_hour, format="csr")

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
    if n_storage == 0:
        blocks.append(energy_balance)
        del energy_balance
        row_lower = eb_rhs.copy()
        row_upper = eb_rhs.copy()
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
        row_lower = np.concatenate([eb_rhs, np.zeros(T * n_storage)])
        row_upper = row_lower.copy()

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
            row_lower = np.concatenate([row_lower, zeros])
            row_upper = np.concatenate([row_upper, zeros])

    # Optional aggregate interface limits: one row per group per hour capping
    # the signed sum of a set of links' flows at the interface's *simultaneous*
    # transfer rating (smaller than the per-path TTC sum). Appended after the
    # energy/storage rows but before hydro/RPS/reserve, so the front-anchored
    # energy-balance duals and the end-anchored RPS/reserve duals keep their
    # positions. No rows (identical LP) when no groups are supplied.
    if interface_groups:
        iface_block, iface_lower, iface_upper = _build_interface_rows(
            layout, interface_groups
        )
        if iface_block.shape[0]:
            blocks.append(iface_block)
            del iface_block
            row_lower = np.concatenate([row_lower, iface_lower])
            row_upper = np.concatenate([row_upper, iface_upper])

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
            row_lower = np.concatenate([row_lower, ramp_lower])
            row_upper = np.concatenate([row_upper, ramp_upper])

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
            lcr_row_offset = row_lower.size
            n_lcr_areas = len(local_capacity_specs)
            blocks.append(lcr_block)
            del lcr_block
            row_lower = np.concatenate([row_lower, lcr_lower])
            row_upper = np.concatenate([row_upper, lcr_upper])

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
            row_lower = np.concatenate([row_lower, env_lower])
            row_upper = np.concatenate([row_upper, env_upper])

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
            hydro_block, hydro_lower, hydro_upper = _build_hydro_rows(
                layout,
                hydro_gen_idx,
                hydro_monthly_energy,
                hydro_month_index,
                hydro_monthly_min,
            )
            blocks.append(hydro_block)
            del hydro_block
            row_lower = np.concatenate([row_lower, hydro_lower])
            row_upper = np.concatenate([row_upper, hydro_upper])

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
            row_lower = np.concatenate([row_lower, oil_lower])
            row_upper = np.concatenate([row_upper, oil_upper])

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
            row_lower = np.concatenate([row_lower, node_lower])
            row_upper = np.concatenate([row_upper, node_upper])

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
            row_lower = np.concatenate([row_lower, np.full(coeffs.shape[0], -np.inf)])
            row_upper = np.concatenate([row_upper, cap_rhs])

    # Optional RPS inequality: one annual row, renewable (wind+solar)
    # generation must reach rps_target * total demand, with an infinite upper
    # bound.
    if rps_target is not None and rps_target > 0.0:
        rps_row, rhs = _build_rps_row(layout, rps_target, demand)
        blocks.append(rps_row)
        del rps_row
        row_lower = np.concatenate([row_lower, [rhs]])
        row_upper = np.concatenate([row_upper, [np.inf]])

    # Optional energy+reserve co-optimization rows (shared headroom + reserve
    # balance). Appended last so the reserve-balance dual is recoverable by row
    # index. Omitted (identical LP) unless the layout carries reserve columns.
    if layout.n_reserve > 0 and reserve_requirement is not None:
        if reserve_pergen_gen_idx is not None:
            # Per-generator reserve columns (R[j,t] per reserve-providing
            # unit): joint P+R headroom per unit-hour + per-family balance.
            # Mutually exclusive with the zone-aggregate spec's scoping
            # mechanisms (supply cap / online gating / additive headroom) —
            # the per-unit ramp10 variable bound supersedes them all. Storage
            # participates via the same duration-gated RS[c,z] columns as the
            # zone-aggregate path when the layout allocated them (CAISO
            # caiso_reserve_coopt, issue #1492).
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
            )
            blocks.append(res_block)
            del res_block
            row_lower = np.concatenate([row_lower, res_lower])
            row_upper = np.concatenate([row_upper, res_upper])
            return (
                _vstack_csr_free(blocks, layout.total_columns),
                row_lower,
                row_upper,
                lcr_row_offset,
                n_lcr_areas,
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
            reserve_supply_cap=reserve_supply_cap,
            online_capacity_cap=reserve_online_capacity_cap,
            storage_duration_h=reserve_storage_duration_h,
        )
        blocks.append(res_block)
        del res_block
        row_lower = np.concatenate([row_lower, res_lower])
        row_upper = np.concatenate([row_upper, res_upper])

    return (
        _vstack_csr_free(blocks, layout.total_columns),
        row_lower,
        row_upper,
        lcr_row_offset,
        n_lcr_areas,
    )


def build_variable_bounds(
    layout: VariableLayout,
    fleet: FleetArrays,
    wind_cf: np.ndarray,
    wind_cap: np.ndarray,
    solar_cf: np.ndarray,
    solar_cap: np.ndarray,
    storage_power_cap: np.ndarray | None = None,
    storage_energy_cap: np.ndarray | None = None,
    ttc: np.ndarray | None = None,
    ordc_step_widths: np.ndarray | None = None,
    link_bidirectional: np.ndarray | None = None,
    reserve_pergen_ramp10: np.ndarray | None = None,
    ttc_import: np.ndarray | None = None,
    posture_ucap: np.ndarray | None = None,
    wind_curtail_share: np.ndarray | None = None,
    solar_curtail_share: np.ndarray | None = None,
    storage_soc_min: np.ndarray | None = None,
    storage_discharge_min: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Assemble the LP column (decision-variable) bound vectors.

    Bounds, by variable block:

    * Thermal generation: ``pmin <= P <= pmax * availability``.
    * Wind: ``0 <= W <= wind_cf * wind_cap``.
    * Solar: ``0 <= S <= solar_cf * solar_cap``.
    * Storage: ``0 <= Chg, Dis <= power_cap``; ``0 <= SOC <= energy_cap``.
    * Transmission: ``-ttc <= Flow <= ttc`` (bidirectional links); a
      one-way link (``link_bidirectional[ln]`` False) is bounded
      ``0 <= Flow <= ttc`` so it can carry power only in its from->to
      direction (used to give an interface an asymmetric rating by pairing
      two opposite one-way links with different TTCs).
    * Load slack: ``0 <= Slack <= inf``.
    * Overgeneration dump: ``0 <= Dump <= inf``.

    Args:
        layout: Variable layout describing the column structure.
        fleet: Vectorized fleet arrays; supplies ``pmin``, ``pmax`` and the
            ``(n_gen, T)`` availability profile.
        wind_cf: Wind capacity factor of shape ``(n_zones, T)``.
        wind_cap: Installed wind capacity per zone, shape ``(n_zones,)``.
        solar_cf: Solar capacity factor of shape ``(n_zones, T)``.
        solar_cap: Installed solar capacity per zone, shape ``(n_zones,)``.
        storage_power_cap: Charge/discharge power cap, shape ``(n_storage,)``
            or hour-varying ``(n_storage, T)`` (COD intra-year ramp).
        storage_energy_cap: SOC energy cap, shape ``(n_storage,)`` or
            ``(n_storage, T)``.
        ttc: Total transfer capability per link, shape ``(n_links,)``
            (static) or ``(T, n_links)`` (per-hour seasonal limit).
        ttc_import: Optional reverse-direction (to->from) capability, same
            accepted shapes as ``ttc``. When given, the flow lower bound is
            ``-ttc_import`` instead of ``-ttc`` — used when an export-side
            stability limit (an ERCOT GTC) caps the forward direction while
            the import direction keeps its thermal rating. ``None`` keeps
            the symmetric ``-ttc`` bound (byte-identical prior behaviour).

    Returns:
        Tuple ``(col_lower, col_upper)`` of length ``layout.total_columns``.
    """
    T = layout.T  # T: number of hours
    vph = layout.vars_per_hour

    col_lower = np.zeros((T, vph), dtype=float)
    col_upper = np.zeros((T, vph), dtype=float)

    # Thermal generation: pmin <= P <= pmax * availability. A per-hour
    # min_gen (e.g. the seasonal ST_GAS reliability floor) overrides the
    # scalar pmin lower bound when present.
    if getattr(fleet, "min_gen", None) is not None:
        col_lower[:, layout._p_off : layout._w_off] = fleet.min_gen.T
    else:
        col_lower[:, layout._p_off : layout._w_off] = fleet.pmin[np.newaxis, :]
    col_upper[:, layout._p_off : layout._w_off] = (
        fleet.pmax[:, np.newaxis] * fleet.availability
    ).T

    # Wind: 0 <= W <= wind_cf * wind_cap * curtail_share. The optional
    # (n_zones, T) curtail_share in (0,1] is the ERCOT West Texas Export corridor
    # congestion ceiling (market_sim.data.curtailment_share); 1.0 / None elsewhere
    # leaves the uncurtailed potential bound unchanged.
    wind_upper = np.asarray(wind_cap, dtype=float)[:, np.newaxis] * np.asarray(
        wind_cf, dtype=float
    )
    if wind_curtail_share is not None:
        wind_upper = wind_upper * np.asarray(wind_curtail_share, dtype=float)
    col_upper[:, layout._w_off : layout._s_off] = wind_upper.T

    # Solar: 0 <= S <= solar_cf * solar_cap * curtail_share.
    solar_upper = np.asarray(solar_cap, dtype=float)[:, np.newaxis] * np.asarray(
        solar_cf, dtype=float
    )
    if solar_curtail_share is not None:
        solar_upper = solar_upper * np.asarray(solar_curtail_share, dtype=float)
    col_upper[:, layout._s_off : layout._chg_off] = solar_upper.T

    # Storage: 0 <= Chg, Dis <= power_cap; 0 <= SOC <= energy_cap. Caps are
    # static ``(n_storage,)`` arrays, or hour-varying ``(n_storage, T)`` —
    # the EIA-860 COD intra-year ramp (storage.storage_cap_profiles) feeds
    # the latter so capacity commissioned mid-year is offline before COD.
    if layout.n_storage:
        power_cap = np.asarray(storage_power_cap, dtype=float)
        power_cap = power_cap.T if power_cap.ndim == 2 else power_cap[np.newaxis, :]
        energy_cap = np.asarray(storage_energy_cap, dtype=float)
        energy_cap = energy_cap.T if energy_cap.ndim == 2 else energy_cap[np.newaxis, :]
        col_upper[:, layout._chg_off : layout._dis_off] = power_cap
        col_upper[:, layout._dis_off : layout._soc_off] = power_cap
        col_upper[:, layout._soc_off : layout._flow_off] = energy_cap
        if storage_discharge_min is not None:
            # Measured-award AS→energy deployment floor (ERCOT
            # ercot_storage_as_deployment): the released reserve draw-down that
            # the real fleet discharges at the net-load ramp. Clipped at the
            # (possibly hour-varying) discharge power cap so the bound pair stays
            # feasible by construction — the caller adds the deployed MW back to
            # ``storage_power_cap`` (rule 19: released from the AS reservation),
            # so cap ≥ floor holds.
            dmin = np.asarray(storage_discharge_min, dtype=float)
            dmin = dmin.T if dmin.ndim == 2 else dmin[np.newaxis, :]
            col_lower[:, layout._dis_off : layout._soc_off] = np.minimum(
                dmin, power_cap
            )
        if storage_soc_min is not None:
            # Measured AS sustain floor (CAISO battery reservation): the SOC
            # may not be arbitraged below the tariff sustain energy of the
            # hour's awards. Clipped at the (possibly hour-varying) energy cap
            # so the bound pair stays feasible by construction.
            soc_min = np.asarray(storage_soc_min, dtype=float)
            soc_min = soc_min.T if soc_min.ndim == 2 else soc_min[np.newaxis, :]
            col_lower[:, layout._soc_off : layout._flow_off] = np.minimum(
                soc_min, energy_cap
            )

    # Transmission flow: -ttc <= Flow <= ttc (bidirectional). A 1-D ``ttc``
    # (n_links,) broadcasts across all hours (the static-limit path); a 2-D
    # ``ttc`` (T, n_links) sets a per-hour limit per link, letting an interface
    # follow a seasonal envelope (NYISO Central-East monthly TTC).
    if layout.n_links:
        ttc_arr = np.asarray(ttc, dtype=float)
        if ttc_arr.ndim == 1:
            ttc_arr = ttc_arr[np.newaxis, :]
        if ttc_import is not None:
            # Asymmetric interface: the import (to->from) direction keeps its
            # own rating rather than mirroring the export cap (ERCOT measured
            # GTC overlay — a stability limit on exports only).
            imp_arr = np.asarray(ttc_import, dtype=float)
            if imp_arr.ndim == 1:
                imp_arr = imp_arr[np.newaxis, :]
            lower_arr = -imp_arr
        else:
            lower_arr = -ttc_arr
        if link_bidirectional is not None:
            # One-way links carry power only from->to: floor their flow at 0
            # (so a pair of opposite one-way links gives an asymmetric rating).
            oneway = ~np.asarray(link_bidirectional, dtype=bool)
            if oneway.any():
                lower_arr = np.where(oneway[np.newaxis, :], 0.0, lower_arr)
        col_lower[:, layout._flow_off : layout._slack_off] = lower_arr
        col_upper[:, layout._flow_off : layout._slack_off] = ttc_arr

    # Load slack: 0 <= Slack <= inf.
    col_upper[:, layout._slack_off : layout._dump_off] = np.inf

    # Overgeneration dump: 0 <= Dump <= inf. Bounded to the dump block so the
    # co-opt reserve/ORDC blocks (when present) keep their own bounds below;
    # with no co-opt columns _reserve_off == vph, recovering "to the end".
    col_upper[:, layout._dump_off : layout._reserve_off] = np.inf

    # Energy+reserve co-optimization bounds (co-opt only).
    # Zone-aggregate spec: per-zone reserve R_z[z,t]: 0 <= R_z <= inf; the
    # per-zone shared-headroom constraint (build_constraints: sum_{eligible g
    # in z} P + R_z <= zone cap) is what bounds it, transferring the reserve
    # price into that zone's LMP. Per-gen spec (``reserve_pergen_ramp10``
    # given): 0 <= R[j] <= ramp10[g_j] — the unit's 10-minute deliverable ramp
    # (FleetArrays.ramp10) caps what it can hold as upward reserve; the joint
    # P+R row (_build_reserve_rows_pergen) enforces availability/headroom.
    # A static ``(n_r,)`` cap applies every hour (PJM); an hourly ``(n_r, T)``
    # cap carries availability-scaled deliverable ramp (MISO: an on-outage
    # unit contributes no 10-minute ramp, so the pool's cap thins with the
    # outage overlay).
    if layout.n_reserve > 0:
        if reserve_pergen_ramp10 is not None:
            ramp10 = np.asarray(reserve_pergen_ramp10, dtype=float)
            if ramp10.shape == (layout.n_reserve,):
                col_upper[:, layout._reserve_off : layout._ordc_off] = ramp10[
                    np.newaxis, :
                ]
            elif ramp10.shape == (layout.n_reserve, layout.T):
                col_upper[:, layout._reserve_off : layout._ordc_off] = ramp10.T
            else:
                raise ValueError(
                    f"reserve_pergen_ramp10 shape {ramp10.shape} != "
                    f"({layout.n_reserve},) or ({layout.n_reserve}, {layout.T})"
                )
        else:
            col_upper[:, layout._reserve_off : layout._ordc_off] = np.inf

    # Storage-reserve columns RS[c,z,t] (duration gate): 0 <= RS <= inf; the
    # storage power-competition row and the SOC duration-gate row (both in
    # _build_reserve_rows) are what bound them. col_upper defaults to 0 (fixed),
    # so this MUST set them free when the gate is active.
    if layout.n_storage_reserve > 0:
        sr0 = layout._storage_reserve_off
        col_upper[:, sr0 : sr0 + layout.n_storage_reserve] = np.inf

    # ORDC shortfall steps S_k[t]: 0 <= S_k <= step width (MW). Each step's
    # width is the MW span the published demand curve prices at that penalty.
    if layout.n_ordc_steps > 0:
        if ordc_step_widths is None:
            raise ValueError(
                "build_variable_bounds: n_ordc_steps > 0 requires ordc_step_widths"
            )
        widths = np.asarray(ordc_step_widths, dtype=float)
        if widths.shape != (layout.n_ordc_steps,):
            raise ValueError(
                f"ordc_step_widths shape {widths.shape} != ({layout.n_ordc_steps},)"
            )
        col_upper[:, layout._ordc_off : layout._ordc_off + layout.n_ordc_steps] = (
            widths[np.newaxis, :]
        )

    # Commitment-posture columns: 0 ≤ U[p,t] ≤ pool available capacity (the
    # hour-varying Σ pmax·availability over the pool's members — an on-outage
    # MW cannot be online, so a forced outage forces U down and the restart
    # after it pays a real startup, the correct physics); 0 ≤ SU[p,t] ≤ inf
    # (the startup rows bound it from below; its cost bounds it from above).
    if layout.n_posture > 0:
        ucap = np.asarray(posture_ucap, dtype=float)
        if ucap.shape != (layout.n_posture, layout.T):
            raise ValueError(
                f"posture_ucap shape {ucap.shape} != ({layout.n_posture}, {layout.T})"
            )
        u0 = layout._posture_u_off
        col_upper[:, u0 : u0 + layout.n_posture] = ucap.T
        su0 = layout._posture_su_off
        col_upper[:, su0 : su0 + layout.n_posture] = np.inf

    # RPS ACP escape column: 0 ≤ ACP ≤ inf (its objective cost, the ACP rate,
    # bounds it from above; the RPS row draws on it only when physical RECs are
    # short). Without this the zero-init upper bound would pin it at 0 and the
    # escape would not exist.
    if layout.n_rec_acp:
        a0 = layout._rec_acp_off
        col_upper[:, a0 : a0 + layout.n_rec_acp] = np.inf

    # Clip the lower bound to never exceed the upper bound. A committed
    # thermal generator carries a positive Pmin, but the commitment screen
    # (and hour-varying availability) can drive its upper bound to zero in
    # decommitted hours. Without this clip pmin > 0 = upper would make the
    # LP infeasible; the clip forces such a generator off (0 <= P <= 0).
    col_lower = np.minimum(col_lower, col_upper)

    return col_lower.ravel(), col_upper.ravel()


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
        rps_shadow_price: Dual of the annual RPS constraint in $/MWh -- the
            endogenous RPS compliance cost. ``None`` when no RPS constraint
            was active. Distinct from the exogenous EAC prices.
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
    rps_shadow_price: float | None = None
    # Endogenous CO2 allowance price(s) ($/tCO2), one per active mass-cap row;
    # None unless a mass cap was enabled.
    co2_cap_price: list[float] | None = None
    # Energy+reserve co-optimization outputs (None unless co-opt is on).
    reserve_dispatch: np.ndarray | None = None  # (n_zones, T) upward reserve MW
    reserve_price: np.ndarray | None = None  # (T,) reserve clearing $/MWh
    # (T, n_families) per-family balance-row dual — the per-product AS clearing
    # price for ERCOT's multi-product co-opt; the per-hour max is the binding MCPC.
    reserve_price_by_family: np.ndarray | None = None
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


# HiGHS basis-status integer codes (HighsBasisStatus enum), captured once so the
# per-column status vectors can be carried as compact int8 arrays instead of
# millions of Python enum objects.
_BASIS_LOWER = int(highspy.HighsBasisStatus.kLower)
_BASIS_BASIC = int(highspy.HighsBasisStatus.kBasic)


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
        storage_zone_idx: np.ndarray | None = None,
        eta_chg: "np.ndarray | float | None" = None,
        eta_dis: "np.ndarray | float | None" = None,
        wind_mc: "np.ndarray | float" = 0.0,
        solar_mc: "np.ndarray | float" = 0.0,
        storage_discharge_eac: float = 0.0,
        storage_discharge_cost: "np.ndarray | float" = 0.0,
        rps_target: float | None = None,
        rps_acp_price: float | None = None,
        hydro_monthly_energy: np.ndarray | None = None,
        hydro_month_index: np.ndarray | None = None,
        hydro_gen_idx: np.ndarray | None = None,
        hydro_monthly_min: np.ndarray | None = None,
        oil_monthly_budget: np.ndarray | None = None,
        oil_gen_idx: np.ndarray | None = None,
        oil_month_index: np.ndarray | None = None,
        oil_gen_hour_coeff: np.ndarray | None = None,
        oil_group_index: np.ndarray | None = None,
        storage_daily_cycle_hours: int | None = None,
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
        link_bidirectional: np.ndarray | None = None,
        link_flow_cost: np.ndarray | None = None,
        slack_cost: np.ndarray | None = None,
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

        # Commitment-posture pools (design note §A): pergen-only. n_posture
        # postured pools each get a U and an SU column per hour.
        if reserve_posture_pools is not None and not pergen:
            raise ValueError(
                "reserve_posture_pools requires the per-generator reserve "
                "spec (reserve_pergen_gen_idx) — the posture U columns gate "
                "the pergen pool joint-headroom and ramp rows"
            )
        n_posture = (
            0
            if reserve_posture_pools is None
            else int(np.asarray(reserve_posture_pools).size)
        )
        # RPS ACP escape column: present only when an ACP price accompanies an
        # active RPS target. Absent (default) leaves the layout byte-identical.
        n_rec_acp = (
            1
            if (
                rps_target is not None
                and rps_target > 0.0
                and rps_acp_price is not None
            )
            else 0
        )

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
        )

        # Posture U upper bound: the pool's hour-varying available capacity
        # (Σ member pmax·availability) — the RHS the joint-headroom row gives
        # up when it re-anchors to U.
        posture_ucap = None
        if n_posture:
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

        A, row_lower, row_upper, lcr_row_offset, n_lcr_areas = build_constraints(
            layout,
            fleet,
            demand,
            incidence=incidence,
            storage_zone_idx=storage_zone_idx,
            eta_chg=eta_chg,
            eta_dis=eta_dis,
            rps_target=rps_target,
            hydro_monthly_energy=hydro_monthly_energy,
            hydro_month_index=hydro_month_index,
            hydro_gen_idx=hydro_gen_idx,
            hydro_monthly_min=hydro_monthly_min,
            oil_monthly_budget=oil_monthly_budget,
            oil_gen_idx=oil_gen_idx,
            oil_month_index=oil_month_index,
            oil_gen_hour_coeff=oil_gen_hour_coeff,
            oil_group_index=oil_group_index,
            storage_daily_cycle_hours=storage_daily_cycle_hours,
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
            reserve_supply_cap=reserve_supply_cap,
            reserve_online_capacity_cap=reserve_online_capacity_cap,
            reserve_storage_duration_h=(
                reserve_storage_duration_h if storage_gate else None
            ),
            reserve_pergen_gen_idx=reserve_pergen_gen_idx,
            reserve_pergen_col=reserve_pergen_col,
            reserve_posture_pools=reserve_posture_pools,
            reserve_posture_mlf=reserve_posture_mlf,
            reserve_pergen_ramp10=(reserve_pergen_ramp10 if n_posture else None),
            reserve_pergen_col_pool=reserve_pergen_col_pool,
            reserve_balance_col_mask=reserve_balance_col_mask,
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
            ttc=ttc,
            ordc_step_widths=ordc_step_widths,
            link_bidirectional=link_bidirectional,
            reserve_pergen_ramp10=reserve_pergen_ramp10,
            ttc_import=ttc_import,
            posture_ucap=posture_ucap,
            wind_curtail_share=wind_curtail_share,
            solar_curtail_share=solar_curtail_share,
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
        self._lcr_row_offset = lcr_row_offset
        self._n_lcr_areas = n_lcr_areas
        self._lcr_gen_idx = (
            [np.asarray(s[0], dtype=int) for s in local_capacity_specs]
            if local_capacity_specs and n_lcr_areas > 0
            else []
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
            # R columns onto one pool row; identity otherwise).
            self._n_reserve_rows = (
                n_pergen_pools * T
                + n_posture_rows
                + n_storage_gate_rows
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
        self._posture_startup = (
            None if not n_posture else np.asarray(reserve_posture_startup, dtype=float)
        )
        self._posture_pools = (
            None if not n_posture else np.asarray(reserve_posture_pools, dtype=int)
        )
        if n_posture:
            r_fuel = np.zeros(n_reserve, dtype=int)
            r_fuel[col] = np.asarray(fleet.fuel_type_idx, dtype=int)[gidx]
            self.posture_zone_idx = r_zone[self._posture_pools]
            self.posture_fuel_idx = r_fuel[self._posture_pools]
        else:
            self.posture_zone_idx = None
            self.posture_fuel_idx = None
        self._all_cols = np.arange(layout.total_columns, dtype=np.int32)
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
            rps_acp_price=(self.rps_acp_price or 0.0),
            link_flow_cost=self.link_flow_cost,
            slack_cost=self.slack_cost,
        )

        h = self._h
        h.changeColsCost(layout.total_columns, self._all_cols, cost)

        solve_start = time.perf_counter()
        h.run()
        solve_time = time.perf_counter() - solve_start
        warm = self._n_solves > 0
        self._n_solves += 1

        logger.info(
            f"Matrix build: {self.build_time:.3f}s, "
            f"Solve: {solve_time:.3f}s ({'warm' if warm else 'cold'})"
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

        solution = h.getSolution()
        col_value = np.asarray(solution.col_value, dtype=float)
        row_dual = np.asarray(solution.row_dual, dtype=float)

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

        # The RPS row, when present, is appended after the energy/storage/hydro
        # rows; its dual is the RPS shadow price. The reserve block (when on) is
        # appended *after* the RPS row, so index from the end past it.
        rps_shadow_price = None
        if self.rps_target is not None and self.rps_target > 0.0:
            rps_idx = -1 - self._n_reserve_rows
            rps_shadow_price = float(row_dual[rps_idx])

        # Emissions mass-cap duals sit before the RPS row and after the
        # import-node rows: [ ... | mass_cap (k) | rps (0/1) | reserve (n) ].
        # Recover them end-anchored past the reserve and RPS tails. HiGHS min
        # problem, <= row → dual <= 0; the reported allowance price is -λ >= 0.
        co2_cap_price = None
        if self._n_masscap_rows:
            rps_present = (
                1 if (self.rps_target is not None and self.rps_target > 0.0) else 0
            )
            start = row_dual.size - (
                self._n_reserve_rows + rps_present + self._n_masscap_rows
            )
            mass_duals = row_dual[start : start + self._n_masscap_rows]
            co2_cap_price = [float(-d) for d in mass_duals]

        # Energy+reserve co-optimization outputs. Reserve dispatch is the
        # per-zone R_z block (n_zones, T); the reserve clearing price is the dual
        # of the reserve-balance rows (the final T rows), which the per-zone
        # shared-headroom constraint transfers into each zone's energy LMP above.
        reserve_dispatch = reserve_price = reserve_price_by_family = None
        reserve_supply_cap_dual = None
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

        return DispatchResult(
            dispatch=dispatch,
            wind_dispatched=wind_dispatched,
            solar_dispatched=solar_dispatched,
            slack=slack,
            dump=dump,
            prices=prices,
            storage_charge=storage_charge,
            storage_discharge=storage_discharge,
            storage_soc=storage_soc,
            flows=flows,
            objective_value=h.getObjectiveValue(),
            status=h.modelStatusToString(h.getModelStatus()),
            reserve_dispatch=reserve_dispatch,
            reserve_price=reserve_price,
            reserve_price_by_family=reserve_price_by_family,
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
            co2_cap_price=co2_cap_price,
            lcr_dual=lcr_dual,
            lcr_gen_idx=lcr_gen_idx_out,
        )

    def export_cross_year_basis(self) -> "CrossYearBasis | None":
        """Snapshot this model's current optimal basis for next year's solve.

        Returns ``None`` when the model has not been solved yet (no basis to
        export). The status vectors are pulled out of HiGHS once and stored as
        compact ``int8`` arrays so the carry across years is cheap.
        """
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
        basis.col_status = [highspy.HighsBasisStatus(int(s)) for s in col_status]
        basis.row_status = [highspy.HighsBasisStatus(int(s)) for s in row_status]
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
    storage_zone_idx: np.ndarray | None = None,
    eta_chg: np.ndarray | float | None = None,
    eta_dis: np.ndarray | float | None = None,
    wind_mc: np.ndarray | float = 0.0,
    solar_mc: np.ndarray | float = 0.0,
    storage_discharge_eac: float = 0.0,
    storage_discharge_cost: np.ndarray | float = 0.0,
    rps_target: float | None = None,
    rps_acp_price: float | None = None,
    hydro_monthly_energy: np.ndarray | None = None,
    hydro_month_index: np.ndarray | None = None,
    hydro_gen_idx: np.ndarray | None = None,
    hydro_monthly_min: np.ndarray | None = None,
    oil_monthly_budget: np.ndarray | None = None,
    oil_gen_idx: np.ndarray | None = None,
    oil_month_index: np.ndarray | None = None,
    oil_gen_hour_coeff: np.ndarray | None = None,
    oil_group_index: np.ndarray | None = None,
    storage_daily_cycle_hours: int | None = None,
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
    link_bidirectional: np.ndarray | None = None,
    link_flow_cost: np.ndarray | None = None,
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
        rps_target: Required renewable-energy (wind+solar) share. When not
            ``None`` and positive, an annual RPS constraint is enforced and its
            dual is returned as ``DispatchResult.rps_shadow_price``.
        rps_acp_price: Optional RPS Alternative Compliance Payment ceiling in
            $/MWh. When set alongside a positive ``rps_target``, an ACP escape
            column is added so the RPS row stays feasible when physical RECs
            fall short (paying the ACP substitutes for renewable energy) and its
            dual (the REC price) is capped at this ceiling. ``None`` (default)
            keeps the RPS a hard constraint, byte-identical to before.
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
        storage_zone_idx=storage_zone_idx,
        eta_chg=eta_chg,
        eta_dis=eta_dis,
        wind_mc=wind_mc,
        solar_mc=solar_mc,
        storage_discharge_eac=storage_discharge_eac,
        storage_discharge_cost=storage_discharge_cost,
        rps_target=rps_target,
        rps_acp_price=rps_acp_price,
        hydro_monthly_energy=hydro_monthly_energy,
        hydro_month_index=hydro_month_index,
        hydro_gen_idx=hydro_gen_idx,
        hydro_monthly_min=hydro_monthly_min,
        oil_monthly_budget=oil_monthly_budget,
        oil_gen_idx=oil_gen_idx,
        oil_month_index=oil_month_index,
        oil_gen_hour_coeff=oil_gen_hour_coeff,
        oil_group_index=oil_group_index,
        storage_daily_cycle_hours=storage_daily_cycle_hours,
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
        link_bidirectional=link_bidirectional,
        link_flow_cost=link_flow_cost,
        T=T,
    )
    return model.solve(
        mc=mc,
        fuel_prices=fuel_prices,
        carbon_price=carbon_price,
        nox_price=nox_price,
        so2_price=so2_price,
    )
