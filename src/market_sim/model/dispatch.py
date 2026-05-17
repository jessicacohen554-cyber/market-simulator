"""Economic dispatch optimization model.

Part 1: variable layout bookkeeping and objective cost-vector assembly.
Part 2: constraint-matrix construction and decision-variable bounds.
Part 3: HiGHS solver invocation and result extraction.
"""

import logging
import time
from dataclasses import dataclass

import highspy
import numpy as np
import scipy.sparse as sp

from market_sim.config.constants import HOURS_PER_YEAR, STORAGE_TIEBREAKER_EPSILON
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays, assemble_mc

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

    @property
    def vars_per_hour(self) -> int:
        """Return the number of decision variables in a single hour block."""
        return (
            self.n_gen
            + 4 * self.n_zones
            + 3 * self.n_storage
            + self.n_links
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

    # Storage charge: flat cycling penalty. Discharge: cycling penalty net
    # of any exogenous discharge EAC credit, so the slot cost can go
    # negative; SOC dynamics and the power cap still bound the discharge.
    block[:, layout._chg_off : layout._dis_off] = storage_epsilon
    block[:, layout._dis_off : layout._soc_off] = (
        storage_epsilon - storage_discharge_eac
    )

    # Load slack: value of lost load.
    block[:, layout._slack_off : layout._dump_off] = voll

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
    block[:, layout._dump_off :] = dump_cost

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
    fleet: FleetArrays,
    rps_target: float,
    demand: np.ndarray,
) -> tuple[sp.csr_matrix, float]:
    """Return the single annual RPS constraint row and its lower bound.

    The row carries a ``+1`` coefficient on every wind, solar and nuclear
    dispatch column across all ``T`` hours; the lower bound is
    ``rps_target`` times total annual demand. The resulting constraint
    ``clean >= rps_target * demand`` is an inequality with no upper bound,
    and its dual is the implicit REC price ($/MWh clean-energy premium).
    """
    T = layout.T  # T: number of hours
    vph = layout.vars_per_hour
    hours = np.arange(T)[:, np.newaxis]  # t: hour index
    zones = np.arange(layout.n_zones)  # z: zone index

    wind_cols = (hours * vph + layout._w_off + zones).ravel()
    solar_cols = (hours * vph + layout._s_off + zones).ravel()
    nuclear_idx = np.flatnonzero(
        np.asarray(fleet.fuel_type_idx) == FUEL_TYPE_MAP["nuclear"]
    )
    nuclear_cols = (hours * vph + layout._p_off + nuclear_idx).ravel()

    cols = np.concatenate([wind_cols, solar_cols, nuclear_cols])
    row = sp.coo_matrix(
        (np.ones(cols.size), (np.zeros(cols.size, dtype=int), cols)),
        shape=(1, layout.total_columns),
    ).tocsr()
    rhs = rps_target * float(np.asarray(demand, dtype=float).sum())
    return row, rhs


def build_constraints(
    layout: VariableLayout,
    fleet: FleetArrays,
    demand: np.ndarray,
    incidence: np.ndarray | sp.spmatrix | None = None,
    storage_zone_idx: np.ndarray | None = None,
    eta_chg: np.ndarray | float | None = None,
    eta_dis: np.ndarray | float | None = None,
    rps_target: float | None = None,
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

    A third, optional family adds one **RPS** inequality row when
    ``rps_target`` is set: total annual wind, solar and nuclear generation
    must reach ``rps_target`` times total annual demand. Its dual is the
    implicit REC price.

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
        rps_target: Required clean-energy share. When not ``None`` and
            positive, one annual RPS constraint row is appended.

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
            zone_gen,                            # thermal generation
            eye_z,                               # wind
            eye_z,                               # solar
            -zone_storage,                       # charge (withdrawal)
            zone_storage,                        # discharge (injection)
            sp.csr_matrix((n_zones, n_storage)),  # SOC: no balance contribution
            flow_block,                          # transmission flow
            eye_z,                               # load slack (+)
            -eye_z,                              # overgeneration dump (-)
        ],
        format="csr",
    )

    # Replicate the per-hour block across all hours without a Python loop.
    energy_balance = sp.kron(sp.eye(T, format="csr"), per_hour, format="csr")

    # RHS: row r = t * n_zones + z must hold demand[z, t]; demand.T ravels
    # in that hour-major, zone-minor order.
    eb_rhs = np.asarray(demand, dtype=float).T.ravel()

    if n_storage == 0:
        A = energy_balance
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
                cyc_rows,          # cyclic: SOC[s,0]
                cyc_rows,          # cyclic: SOC[s,T-1]
                cyc_rows,          # cyclic: Chg[s,0]
                cyc_rows,          # cyclic: Dis[s,0]
            ]
        )
        all_cols = np.concatenate(
            [
                all_soc_cols[:, 1:].ravel(),   # SOC[s,t]
                all_soc_cols[:, :-1].ravel(),  # SOC[s,t-1]
                all_chg_cols[:, 1:].ravel(),   # Chg[s,t]
                all_dis_cols[:, 1:].ravel(),   # Dis[s,t]
                all_soc_cols[:, 0],            # cyclic: SOC[s,0]
                all_soc_cols[:, -1],           # cyclic: SOC[s,T-1]
                all_chg_cols[:, 0],            # cyclic: Chg[s,0]
                all_dis_cols[:, 0],            # cyclic: Dis[s,0]
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
        A = sp.vstack([energy_balance, soc_block], format="csr")
        row_lower = np.concatenate([eb_rhs, np.zeros(T * n_storage)])
        row_upper = row_lower.copy()

    # Optional RPS inequality: one annual row, clean generation must reach
    # rps_target * total demand, with an infinite upper bound.
    if rps_target is not None and rps_target > 0.0:
        rps_row, rhs = _build_rps_row(layout, fleet, rps_target, demand)
        A = sp.vstack([A, rps_row], format="csr")
        row_lower = np.concatenate([row_lower, [rhs]])
        row_upper = np.concatenate([row_upper, [np.inf]])

    return A, row_lower, row_upper


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
) -> tuple[np.ndarray, np.ndarray]:
    """Assemble the LP column (decision-variable) bound vectors.

    Bounds, by variable block:

    * Thermal generation: ``pmin <= P <= pmax * availability``.
    * Wind: ``0 <= W <= wind_cf * wind_cap``.
    * Solar: ``0 <= S <= solar_cf * solar_cap``.
    * Storage: ``0 <= Chg, Dis <= power_cap``; ``0 <= SOC <= energy_cap``.
    * Transmission: ``-ttc <= Flow <= ttc`` (bidirectional).
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
        storage_power_cap: Charge/discharge power cap, shape ``(n_storage,)``.
        storage_energy_cap: SOC energy cap, shape ``(n_storage,)``.
        ttc: Total transfer capability per link, shape ``(n_links,)``.

    Returns:
        Tuple ``(col_lower, col_upper)`` of length ``layout.total_columns``.
    """
    T = layout.T  # T: number of hours
    vph = layout.vars_per_hour

    col_lower = np.zeros((T, vph), dtype=float)
    col_upper = np.zeros((T, vph), dtype=float)

    # Thermal generation: pmin <= P <= pmax * availability.
    col_lower[:, layout._p_off : layout._w_off] = fleet.pmin[np.newaxis, :]
    col_upper[:, layout._p_off : layout._w_off] = (
        fleet.pmax[:, np.newaxis] * fleet.availability
    ).T

    # Wind: 0 <= W <= wind_cf * wind_cap.
    col_upper[:, layout._w_off : layout._s_off] = (
        np.asarray(wind_cap, dtype=float)[:, np.newaxis]
        * np.asarray(wind_cf, dtype=float)
    ).T

    # Solar: 0 <= S <= solar_cf * solar_cap.
    col_upper[:, layout._s_off : layout._chg_off] = (
        np.asarray(solar_cap, dtype=float)[:, np.newaxis]
        * np.asarray(solar_cf, dtype=float)
    ).T

    # Storage: 0 <= Chg, Dis <= power_cap; 0 <= SOC <= energy_cap.
    if layout.n_storage:
        power_cap = np.asarray(storage_power_cap, dtype=float)[np.newaxis, :]
        energy_cap = np.asarray(storage_energy_cap, dtype=float)[np.newaxis, :]
        col_upper[:, layout._chg_off : layout._dis_off] = power_cap
        col_upper[:, layout._dis_off : layout._soc_off] = power_cap
        col_upper[:, layout._soc_off : layout._flow_off] = energy_cap

    # Transmission flow: -ttc <= Flow <= ttc (bidirectional).
    if layout.n_links:
        ttc_row = np.asarray(ttc, dtype=float)[np.newaxis, :]
        col_lower[:, layout._flow_off : layout._slack_off] = -ttc_row
        col_upper[:, layout._flow_off : layout._slack_off] = ttc_row

    # Load slack: 0 <= Slack <= inf.
    col_upper[:, layout._slack_off : layout._dump_off] = np.inf

    # Overgeneration dump: 0 <= Dump <= inf.
    col_upper[:, layout._dump_off :] = np.inf

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
    voll: float = 5000,  # default matches ScenarioConfig.voll for ERCOT
    incidence: np.ndarray | sp.spmatrix | None = None,
    ttc: np.ndarray | None = None,
    storage_power_cap: np.ndarray | None = None,
    storage_energy_cap: np.ndarray | None = None,
    storage_zone_idx: np.ndarray | None = None,
    eta_chg: np.ndarray | float | None = None,
    eta_dis: np.ndarray | float | None = None,
    wind_mc: np.ndarray | float = 0.0,
    solar_mc: np.ndarray | float = 0.0,
    storage_discharge_eac: float = 0.0,
    rps_target: float | None = None,
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
        voll: Value of lost load applied to load-slack variables.
        incidence: Node-link incidence of shape ``(n_zones, n_links)``.
        ttc: Total transfer capability per link, shape ``(n_links,)``.
        storage_power_cap: Charge/discharge power cap, shape ``(n_storage,)``.
        storage_energy_cap: SOC energy cap, shape ``(n_storage,)``.
        storage_zone_idx: Zone index of each storage unit.
        eta_chg: Storage charge efficiency, scalar or ``(n_storage,)``.
        eta_dis: Storage discharge efficiency, scalar or ``(n_storage,)``.
        wind_mc: Wind dispatch marginal cost in $/MWh; scalar or
            ``(n_zones, T)``. Negative under a production tax credit.
        solar_mc: Solar dispatch marginal cost in $/MWh; scalar or
            ``(n_zones, T)``.
        storage_discharge_eac: Exogenous EAC paid per MWh discharged in
            $/MWh, lowering the storage discharge slot cost.
        rps_target: Required clean-energy share. When not ``None`` and
            positive, an annual RPS constraint is enforced and its dual is
            returned as ``DispatchResult.rps_shadow_price``.
        T: Number of hours. Inferred from ``demand`` when ``None``.

    Returns:
        A populated ``DispatchResult``.

    Raises:
        RuntimeError: When HiGHS does not return a feasible primal solution.
    """
    build_start = time.perf_counter()

    demand = np.asarray(demand, dtype=float)
    if T is None:
        T = demand.shape[1]
    n_zones = demand.shape[0]
    n_gen = fleet.n_gen
    n_storage = 0 if storage_power_cap is None else len(storage_power_cap)
    n_links = 0 if incidence is None else sp.csr_matrix(incidence).shape[1]

    layout = VariableLayout(
        n_gen=n_gen, n_zones=n_zones, n_storage=n_storage, n_links=n_links, T=T
    )

    if mc is None:
        mc = assemble_mc(fleet, fuel_prices, carbon_price, nox_price)
    mc = np.asarray(mc, dtype=float)

    cost = build_cost_vector(
        layout, mc, voll, wind_mc=wind_mc, solar_mc=solar_mc,
        storage_discharge_eac=storage_discharge_eac,
    )
    A, row_lower, row_upper = build_constraints(
        layout,
        fleet,
        demand,
        incidence=incidence,
        storage_zone_idx=storage_zone_idx,
        eta_chg=eta_chg,
        eta_dis=eta_dis,
        rps_target=rps_target,
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
        ttc=ttc,
    )

    # build_constraints returns CSR -- the row-wise layout HiGHS addRows
    # consumes directly, so no format conversion is needed here.
    starts = A.indptr[:-1].astype(np.int32)
    indices = A.indices.astype(np.int32)
    values = A.data.astype(np.float64)

    inf = highspy.kHighsInf
    col_upper = np.where(np.isinf(col_upper), inf, col_upper)
    col_lower = np.where(np.isinf(col_lower), -inf, col_lower)
    row_upper = np.where(np.isinf(row_upper), inf, row_upper)
    row_lower = np.where(np.isinf(row_lower), -inf, row_lower)

    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    # Economic-dispatch LPs are already tight, and the per-hour blocks make
    # the matrix huge but trivially structured. HiGHS presolve then scales
    # with the ~1.8M column count while removing almost nothing -- on a full
    # 8760-hour model it costs ~17s of pure overhead. Skipping it lets the
    # dual simplex solve the model directly in a few seconds.
    h.setOptionValue("presolve", "off")
    h.addCols(
        layout.total_columns,
        cost,
        col_lower,
        col_upper,
        0,
        np.zeros(layout.total_columns, dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )
    h.addRows(
        A.shape[0],
        row_lower,
        row_upper,
        A.nnz,
        starts,
        indices,
        values,
    )
    build_time = time.perf_counter() - build_start

    solve_start = time.perf_counter()
    h.run()
    solve_time = time.perf_counter() - solve_start

    logger.info(f"Matrix build: {build_time:.3f}s, Solve: {solve_time:.3f}s")

    _, primal_status = h.getInfoValue("primal_solution_status")
    if primal_status != 2:
        status = h.modelStatusToString(h.getModelStatus())
        raise RuntimeError(
            f"dispatch LP has no feasible primal solution (status: {status})"
        )

    solution = h.getSolution()
    col_value = np.asarray(solution.col_value, dtype=float)
    row_dual = np.asarray(solution.row_dual, dtype=float)

    block = col_value.reshape(T, layout.vars_per_hour)
    dispatch = block[:, layout._p_off : layout._w_off].T
    wind_dispatched = block[:, layout._w_off : layout._s_off].T
    solar_dispatched = block[:, layout._s_off : layout._chg_off].T
    slack = block[:, layout._slack_off : layout._dump_off].T
    dump = block[:, layout._dump_off :].T

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

    # The RPS row, when present, is the final constraint row; its dual is
    # the RPS shadow price -- the marginal cost of raising the clean-
    # energy floor by one MWh.
    rps_shadow_price = None
    if rps_target is not None and rps_target > 0.0:
        rps_shadow_price = float(row_dual[-1])

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
        build_time=build_time,
        solve_time=solve_time,
        rps_shadow_price=rps_shadow_price,
    )
