"""Economic dispatch optimization model.

Part 1: variable layout bookkeeping and objective cost-vector assembly.
Part 2: constraint-matrix construction and decision-variable bounds.
Part 3: HiGHS solver invocation and result extraction.
"""

import time
from dataclasses import dataclass

import highspy
import numpy as np
import scipy.sparse as sp

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.data.fleet import FleetArrays, assemble_mc


@dataclass(frozen=True)
class VariableLayout:
    """Maps dispatch decision variables to flat LP column indices.

    Decision variables are grouped into per-hour blocks laid out
    contiguously across ``T`` hours. Within each hour the block order is:
    thermal generation, wind, solar, storage charge, storage discharge,
    storage state-of-charge, transmission flow, then per-zone load slack.
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
            + 2 * self.n_zones
            + 3 * self.n_storage
            + self.n_links
            + self.n_zones
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

    def p_cols_gen(self, g: int) -> slice:
        """Return a slice selecting all ``T`` columns of thermal generator ``g``."""
        start = self._p_off + g
        return slice(start, start + self.T * self.vars_per_hour, self.vars_per_hour)


def build_cost_vector(
    layout: VariableLayout,
    mc: np.ndarray,
    voll: float,
    storage_epsilon: float = 0.001,
) -> np.ndarray:
    """Assemble the flat LP objective cost vector.

    Thermal slots carry their hourly marginal cost, storage charge and
    discharge carry a small ``storage_epsilon`` penalty to break degeneracy,
    load slack carries the value of lost load (``voll``), and renewable and
    SOC/flow slots are zero-cost.

    Args:
        layout: Variable layout describing the column structure.
        mc: Marginal cost array of shape ``(n_gen, T)``.
        voll: Value of lost load applied to slack variables.
        storage_epsilon: Cycling penalty on storage charge/discharge.

    Returns:
        Cost vector of length ``layout.total_columns``.
    """
    cost = np.zeros(layout.total_columns, dtype=float)
    block = cost.reshape(layout.T, layout.vars_per_hour)

    # Thermal: mc is (n_gen, T); the per-hour block wants (T, n_gen).
    block[:, layout._p_off : layout._w_off] = mc.T

    # Storage charge and discharge: flat cycling penalty.
    block[:, layout._chg_off : layout._dis_off] = storage_epsilon
    block[:, layout._dis_off : layout._soc_off] = storage_epsilon

    # Load slack: value of lost load.
    block[:, layout._slack_off :] = voll

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


def build_constraints(
    layout: VariableLayout,
    fleet: FleetArrays,
    demand: np.ndarray,
    incidence: np.ndarray | sp.spmatrix | None = None,
    storage_zone_idx: np.ndarray | None = None,
    eta_chg: np.ndarray | float | None = None,
    eta_dis: np.ndarray | float | None = None,
) -> tuple[sp.csc_matrix, np.ndarray, np.ndarray]:
    """Assemble the LP constraint matrix and its row bound vectors.

    Two constraint families are built, both equalities (``row_lower ==
    row_upper``):

    * **Energy balance** -- ``n_zones`` rows per hour. For zone ``z`` and
      hour ``t`` the dispatched thermal, wind, solar, net storage, net
      transmission flow and load slack must equal ``demand[z, t]``. The
      per-hour pattern is identical across hours, so a single sparse block
      is replicated with ``scipy.sparse.kron`` -- no Python loop over hours.
    * **Storage SOC dynamics** -- ``T`` rows per storage unit (only when
      storage is present). Hours ``1..T-1`` enforce
      ``SOC[s,t] - SOC[s,t-1] - eta_chg*Chg[s,t] + Dis[s,t]/eta_dis = 0``
      and hour ``0`` enforces the cyclic boundary ``SOC[s,0] = SOC[s,T-1]``.

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

    Returns:
        Tuple ``(A, row_lower, row_upper)`` where ``A`` is a CSC matrix and
        the bound vectors give the (equal) lower and upper row bounds.
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
    # P | W | S | Chg | Dis | SOC | Flow | Slack.
    per_hour = sp.hstack(
        [
            zone_gen,                            # thermal generation
            eye_z,                               # wind
            eye_z,                               # solar
            -zone_storage,                       # charge (withdrawal)
            zone_storage,                        # discharge (injection)
            sp.csr_matrix((n_zones, n_storage)),  # SOC: no balance contribution
            flow_block,                          # transmission flow
            eye_z,                               # load slack
        ],
        format="csr",
    )

    # Replicate the per-hour block across all hours without a Python loop.
    energy_balance = sp.kron(sp.eye(T, format="csr"), per_hour, format="csr")

    # RHS: row r = t * n_zones + z must hold demand[z, t]; demand.T ravels
    # in that hour-major, zone-minor order.
    eb_rhs = np.asarray(demand, dtype=float).T.ravel()

    if n_storage == 0:
        A = energy_balance.tocsc()
        row_lower = eb_rhs.copy()
        return A, row_lower, row_lower.copy()

    eta_c = np.broadcast_to(
        np.asarray(1.0 if eta_chg is None else eta_chg, dtype=float), (n_storage,)
    )
    eta_d = np.broadcast_to(
        np.asarray(1.0 if eta_dis is None else eta_dis, dtype=float), (n_storage,)
    )

    hours = np.arange(T)  # t: hour index
    dyn_rows = np.arange(1, T)  # dynamics rows cover hours 1..T-1
    soc_mats = []
    for s in range(n_storage):  # s: storage unit index
        soc_cols = hours * vph + layout._soc_off + s
        chg_cols = hours * vph + layout._chg_off + s
        dis_cols = hours * vph + layout._dis_off + s
        rows = np.concatenate(
            [dyn_rows, dyn_rows, dyn_rows, dyn_rows, [0], [0]]
        )
        cols = np.concatenate(
            [
                soc_cols[1:],       # SOC[s,t]
                soc_cols[:-1],      # SOC[s,t-1]
                chg_cols[1:],       # Chg[s,t]
                dis_cols[1:],       # Dis[s,t]
                [soc_cols[0]],      # cyclic: SOC[s,0]
                [soc_cols[-1]],     # cyclic: SOC[s,T-1]
            ]
        )
        data = np.concatenate(
            [
                np.ones(T - 1),
                -np.ones(T - 1),
                np.full(T - 1, -eta_c[s]),
                np.full(T - 1, 1.0 / eta_d[s]),
                [1.0],
                [-1.0],
            ]
        )
        soc_mats.append(
            sp.coo_matrix(
                (data, (rows, cols)), shape=(T, layout.total_columns)
            )
        )

    soc_block = sp.vstack(soc_mats, format="csr")
    A = sp.vstack([energy_balance, soc_block], format="csc")
    row_lower = np.concatenate([eb_rhs, np.zeros(T * n_storage)])
    return A, row_lower, row_lower.copy()


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
    col_upper[:, layout._slack_off :] = np.inf

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
        prices: Zonal energy prices, shape ``(n_zones, T)``.
        storage_charge: Storage charging power, shape ``(n_storage, T)``.
        storage_discharge: Storage discharging power, shape ``(n_storage, T)``.
        storage_soc: Storage state of charge, shape ``(n_storage, T)``.
        flows: Transmission link flows, shape ``(n_links, T)``.
        objective_value: Optimal objective (total system cost).
        status: HiGHS model-status string.
        build_time: Seconds spent assembling and loading the model.
        solve_time: Seconds spent inside the solver.
    """

    dispatch: np.ndarray
    wind_dispatched: np.ndarray
    solar_dispatched: np.ndarray
    slack: np.ndarray
    prices: np.ndarray
    storage_charge: np.ndarray | None
    storage_discharge: np.ndarray | None
    storage_soc: np.ndarray | None
    flows: np.ndarray | None
    objective_value: float
    status: str
    build_time: float
    solve_time: float


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
    voll: float = 5000,
    incidence: np.ndarray | sp.spmatrix | None = None,
    ttc: np.ndarray | None = None,
    storage_power_cap: np.ndarray | None = None,
    storage_energy_cap: np.ndarray | None = None,
    storage_zone_idx: np.ndarray | None = None,
    eta_chg: np.ndarray | float | None = None,
    eta_dis: np.ndarray | float | None = None,
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

    cost = build_cost_vector(layout, mc, voll)
    A, row_lower, row_upper = build_constraints(
        layout,
        fleet,
        demand,
        incidence=incidence,
        storage_zone_idx=storage_zone_idx,
        eta_chg=eta_chg,
        eta_dis=eta_dis,
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

    # HiGHS addRows consumes the matrix row-wise; convert from CSC to CSR.
    A_csr = A.tocsr()
    starts = A_csr.indptr[:-1].astype(np.int32)
    indices = A_csr.indices.astype(np.int32)
    values = A_csr.data.astype(np.float64)

    inf = highspy.kHighsInf
    col_upper = np.where(np.isinf(col_upper), inf, col_upper)
    col_lower = np.where(np.isinf(col_lower), -inf, col_lower)

    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
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
        A_csr.shape[0],
        row_lower,
        row_upper,
        A_csr.nnz,
        starts,
        indices,
        values,
    )
    build_time = time.perf_counter() - build_start

    solve_start = time.perf_counter()
    h.run()
    solve_time = time.perf_counter() - solve_start

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
    slack = block[:, layout._slack_off :].T

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

    return DispatchResult(
        dispatch=dispatch,
        wind_dispatched=wind_dispatched,
        solar_dispatched=solar_dispatched,
        slack=slack,
        prices=prices,
        storage_charge=storage_charge,
        storage_discharge=storage_discharge,
        storage_soc=storage_soc,
        flows=flows,
        objective_value=h.getObjectiveValue(),
        status=h.modelStatusToString(h.getModelStatus()),
        build_time=build_time,
        solve_time=solve_time,
    )
