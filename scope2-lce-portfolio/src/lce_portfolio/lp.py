"""Portfolio-selection LP: match hourly load with clean resources + storage.

This is a *portfolio* LP (capacity choice + hourly operation), distinct from the
market simulator's *dispatch* LP, and shares none of its code. It mirrors the
proven primitives, though: a flat column vector, fully vectorized sparse
constraint construction (no Python loop over hours), and HiGHS via ``highspy``
with ``addCols``/``addRows`` on a CSR matrix. Prices/shadow values come out as
row duals.

Column layout (flat vector, ``T = 8760``)::

    build_mw[r]  | gen[r,t] | chg[s,t] | dis[s,t] | soc[s,t] | grid_buy[t] | excess[t]

Two solve modes (see ``docs/01-lp-formulation.md``):

* **Mode A — premium_cap (default):** maximize hourly CFE matching
  (``min Σ grid_buy``) subject to portfolio premium ≤ ``delta`` $/MWh.
* **Mode B — matching_target:** minimize net portfolio cost subject to hourly
  matching ≥ ``target`` (annual, or strict per-hour for hard 24/7).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import highspy
import numpy as np
import scipy.sparse as sp

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.resources import ResourceArrays


@dataclass
class PortfolioResult:
    """Solution of one portfolio LP solve."""

    status: str
    mode: str
    setpoint: float  # delta ($/MWh) for Mode A, or target frac for Mode B
    matching_pct: float  # annual hourly CFE matching fraction achieved
    premium: float  # $/MWh above wholesale
    build_mw: np.ndarray  # (n_res,) capacity selected
    resource_names: list[str]
    gen: np.ndarray  # (n_res, T) hourly generation
    storage_charge: np.ndarray  # (n_sto, T)
    storage_discharge: np.ndarray  # (n_sto, T)
    storage_soc: np.ndarray  # (n_sto, T)
    grid_buy: np.ndarray  # (T,)
    excess: np.ndarray  # (T,)
    net_cost: float  # total portfolio net cost ($)
    bau_cost: float  # cost of buying all load at wholesale ($)
    shadow_price: float  # dual on the premium/matching constraint


class _Layout:
    """Column offsets for the flat variable vector."""

    def __init__(self, n_res: int, n_sto: int, T: int) -> None:
        self.n_res, self.n_sto, self.T = n_res, n_sto, T
        self.build_off = 0
        self.gen_off = self.build_off + n_res
        self.chg_off = self.gen_off + n_res * T
        self.dis_off = self.chg_off + n_sto * T
        self.soc_off = self.dis_off + n_sto * T
        self.buy_off = self.soc_off + n_sto * T
        self.exc_off = self.buy_off + T
        self.total = self.exc_off + T


def _energy_balance(lay: _Layout, storage_idx: np.ndarray):
    """COO triplets for the per-hour energy-balance rows (T rows)."""
    T, n_res, n_sto = lay.T, lay.n_res, lay.n_sto
    hours = np.arange(T)
    rows, cols, data = [], [], []

    # thermal/renewable generation: +1 on gen[r,t]
    rows.append(np.tile(hours, n_res))
    cols.append(lay.gen_off + np.arange(n_res * T))
    data.append(np.ones(n_res * T))

    if n_sto:
        si = np.repeat(np.arange(n_sto), T)
        th = np.tile(hours, n_sto)
        # discharge +1, charge -1
        rows.append(th)
        cols.append(lay.dis_off + si * T + th)
        data.append(np.ones(n_sto * T))
        rows.append(th)
        cols.append(lay.chg_off + si * T + th)
        data.append(-np.ones(n_sto * T))

    # grid_buy +1, excess -1
    rows.append(hours)
    cols.append(lay.buy_off + hours)
    data.append(np.ones(T))
    rows.append(hours)
    cols.append(lay.exc_off + hours)
    data.append(-np.ones(T))
    return rows, cols, data


def build_and_solve(
    config: PortfolioConfig,
    resources: ResourceArrays,
    load: np.ndarray,
    lmp: np.ndarray,
    cf: np.ndarray,
    setpoint: float,
) -> PortfolioResult:
    """Build and solve one portfolio LP.

    ``setpoint`` is the premium cap ``delta`` ($/MWh) in Mode A, or the matching
    target fraction in Mode B. ``cf`` is the ``(n_res, T)`` capacity-factor
    matrix from :func:`lce_portfolio.profiles.build_cf_matrix`.
    """
    T = config.hours
    n_res, n_sto = resources.n_res, int(resources.is_storage.sum())
    storage_idx = resources.storage_idx  # resource index r for each storage s
    lay = _Layout(n_res, n_sto, T)

    if load.shape != (T,) or lmp.shape != (T,) or cf.shape != (n_res, T):
        raise ValueError("load/lmp/cf shapes inconsistent with T and n_res")

    sum_load = float(load.sum())
    bau_cost = float(lmp @ load)
    eta = (
        np.sqrt(np.clip(resources.rte[storage_idx], 1e-6, 1.0))
        if n_sto
        else np.array([])
    )

    # ------------------------------------------------------------------ rows
    rows, cols, data = _energy_balance(lay, storage_idx)
    rlow = [load.copy()]  # energy balance: equality = load
    rupp = [load.copy()]
    roff = T  # running row offset

    # gen coupling: gen[r,t] - cf[r,t]*build[r] <= 0
    idx = np.arange(n_res * T)
    rows.append(roff + idx)
    cols.append(lay.gen_off + idx)
    data.append(np.ones(n_res * T))
    rows.append(roff + idx)
    cols.append(lay.build_off + np.repeat(np.arange(n_res), T))
    data.append(-cf.reshape(-1))
    rlow.append(np.full(n_res * T, -np.inf))
    rupp.append(np.zeros(n_res * T))
    roff += n_res * T

    if n_sto:
        si = np.repeat(np.arange(n_sto), T)
        th = np.tile(np.arange(T), n_sto)
        sidx = np.arange(n_sto * T)
        build_cols = lay.build_off + np.repeat(storage_idx, T)

        # SOC dynamics (cyclic): soc[t] - soc[t-1] - eta*chg[t] + dis[t]/eta = 0
        prev = (th - 1) % T
        rows += [roff + sidx, roff + sidx, roff + sidx, roff + sidx]
        cols += [
            lay.soc_off + si * T + th,
            lay.soc_off + si * T + prev,
            lay.chg_off + si * T + th,
            lay.dis_off + si * T + th,
        ]
        data += [
            np.ones(n_sto * T),
            -np.ones(n_sto * T),
            -np.repeat(eta, T),
            np.repeat(1.0 / eta, T),
        ]
        rlow.append(np.zeros(n_sto * T))
        rupp.append(np.zeros(n_sto * T))
        roff += n_sto * T

        # power bound: chg[t] - build <= 0 ; dis[t] - build <= 0
        for var_off in (lay.chg_off, lay.dis_off):
            rows += [roff + sidx, roff + sidx]
            cols += [var_off + si * T + th, build_cols]
            data += [np.ones(n_sto * T), -np.ones(n_sto * T)]
            rlow.append(np.full(n_sto * T, -np.inf))
            rupp.append(np.zeros(n_sto * T))
            roff += n_sto * T

        # energy bound: soc[t] - duration*build <= 0
        rows += [roff + sidx, roff + sidx]
        cols += [lay.soc_off + si * T + th, build_cols]
        data += [np.ones(n_sto * T), -np.repeat(resources.duration_h[storage_idx], T)]
        rlow.append(np.full(n_sto * T, -np.inf))
        rupp.append(np.zeros(n_sto * T))
        roff += n_sto * T

    # ---- premium / matching constraint ----
    sale = config.excess_sale_fraction
    if config.mode == "premium_cap":
        # fixed@build + Σ vom*gen + Σ lmp*buy - sale*Σ lmp*excess <= delta*ΣL + BAU
        rows.append(np.full(n_res, roff))
        cols.append(lay.build_off + np.arange(n_res))
        data.append(resources.fixed_mwyr.copy())
        rows.append(np.full(n_res * T, roff))
        cols.append(lay.gen_off + np.arange(n_res * T))
        data.append(np.repeat(resources.vom, T))
        rows.append(np.full(T, roff))
        cols.append(lay.buy_off + np.arange(T))
        data.append(lmp.copy())
        rows.append(np.full(T, roff))
        cols.append(lay.exc_off + np.arange(T))
        data.append(-sale * lmp)
        rlow.append(np.array([-np.inf]))
        rupp.append(np.array([setpoint * sum_load + bau_cost]))
        premium_row = roff
        roff += 1
    elif config.mode == "matching_target":
        if config.strict_hourly_matching:
            hours = np.arange(T)
            rows.append(roff + hours)
            cols.append(lay.buy_off + hours)
            data.append(np.ones(T))
            rlow.append(np.full(T, -np.inf))
            rupp.append((1.0 - setpoint) * load)
            premium_row = roff  # (per-hour; dual not a single scalar)
            roff += T
        else:
            rows.append(np.full(T, roff))
            cols.append(lay.buy_off + np.arange(T))
            data.append(np.ones(T))
            rlow.append(np.array([-np.inf]))
            rupp.append(np.array([(1.0 - setpoint) * sum_load]))
            premium_row = roff
            roff += 1
    else:
        raise ValueError(f"unknown mode {config.mode!r}")

    n_rows = roff
    A = sp.csr_matrix(
        (np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
        shape=(n_rows, lay.total),
    )
    row_lower = np.concatenate(rlow)
    row_upper = np.concatenate(rupp)

    # ------------------------------------------------------------- objective
    cost = np.zeros(lay.total)
    if config.mode == "premium_cap":
        # Maximize hourly matching == minimize grid purchases. A pure objective
        # keeps the LP well-scaled and fast. In the non-saturated regime the
        # premium constraint binds, so the reported (achieved) premium is the true
        # tradeoff. Once matching saturates at 100%, many portfolios tie and the
        # returned solution's premium is <= the cap (still honest — that matching
        # is reachable within budget). A least-cost tiebreak was tried but its
        # tiny mixed-scale coefficients stalled the dual simplex; not worth it.
        cost[lay.buy_off : lay.buy_off + T] = 1.0
    else:
        cost[lay.build_off : lay.build_off + n_res] = resources.fixed_mwyr
        cost[lay.gen_off : lay.chg_off] = np.repeat(resources.vom, T)
        cost[lay.buy_off : lay.buy_off + T] = lmp
        cost[lay.exc_off : lay.exc_off + T] = -sale * lmp
    if n_sto:  # storage throughput tiebreaker (ε = storage_epsilon)
        cost[lay.chg_off : lay.soc_off] += config.storage_epsilon

    # ----------------------------------------------------------- var bounds
    col_lower = np.zeros(lay.total)
    col_upper = np.full(lay.total, np.inf)
    col_lower[lay.build_off : lay.gen_off] = resources.cap_min_mw
    col_upper[lay.build_off : lay.gen_off] = resources.cap_max_mw

    # ------------------------------------------------------------- solve
    col_value, row_dual, status = _solve_highs(
        cost, col_lower, col_upper, A, row_lower, row_upper
    )

    build_mw = col_value[lay.build_off : lay.gen_off]
    gen = col_value[lay.gen_off : lay.chg_off].reshape(n_res, T)
    chg = (
        col_value[lay.chg_off : lay.dis_off].reshape(n_sto, T)
        if n_sto
        else np.zeros((0, T))
    )
    dis = (
        col_value[lay.dis_off : lay.soc_off].reshape(n_sto, T)
        if n_sto
        else np.zeros((0, T))
    )
    soc = (
        col_value[lay.soc_off : lay.buy_off].reshape(n_sto, T)
        if n_sto
        else np.zeros((0, T))
    )
    grid_buy = col_value[lay.buy_off : lay.exc_off]
    excess = col_value[lay.exc_off :]

    matching_pct = 1.0 - float(grid_buy.sum()) / sum_load if sum_load else 0.0
    net_cost = (
        float(resources.fixed_mwyr @ build_mw)
        + float((resources.vom[:, None] * gen).sum())
        + float(lmp @ grid_buy)
        - sale * float(lmp @ excess)
    )
    premium = (net_cost - bau_cost) / sum_load if sum_load else 0.0
    shadow = (
        float(row_dual[premium_row]) if premium_row < len(row_dual) else float("nan")
    )

    return PortfolioResult(
        status=status,
        mode=config.mode,
        setpoint=setpoint,
        matching_pct=matching_pct,
        premium=premium,
        build_mw=build_mw,
        resource_names=list(resources.names),
        gen=gen,
        storage_charge=chg,
        storage_discharge=dis,
        storage_soc=soc,
        grid_buy=grid_buy,
        excess=excess,
        net_cost=net_cost,
        bau_cost=bau_cost,
        shadow_price=shadow,
    )


def _solve_highs(cost, col_lower, col_upper, A, row_lower, row_upper):
    """Pass a CSR model to HiGHS and return (col_value, row_dual, status).

    Mirrors the market-sim ``addCols``/``addRows`` pattern. Uses the
    interior-point (IPM) solver: the 8760-hour cyclic storage-SOC network is a
    long temporal coupling that the dual simplex traverses slowly (it can stall
    for minutes when storage is heavily used), whereas IPM solves this structured
    LP in seconds and still returns the row duals we need. Crossover is left off
    for speed; a near-optimal interior point is fine for reporting matching%,
    premium, and build MW. Infinities are mapped to ``kHighsInf``.
    """
    inf = highspy.kHighsInf
    col_upper = np.where(np.isinf(col_upper), inf, col_upper)
    col_lower = np.where(np.isinf(col_lower), -inf, col_lower)
    row_upper = np.where(np.isinf(row_upper), inf, row_upper)
    row_lower = np.where(np.isinf(row_lower), -inf, row_lower)

    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    h.setOptionValue("solver", "ipm")
    h.setOptionValue("run_crossover", "off")
    _threads = os.environ.get("LCE_PORTFOLIO_HIGHS_THREADS")
    if _threads:
        h.setOptionValue("threads", int(_threads))
    h.addCols(
        A.shape[1],
        cost.astype(np.float64),
        col_lower.astype(np.float64),
        col_upper.astype(np.float64),
        0,
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )
    h.addRows(
        A.shape[0],
        row_lower.astype(np.float64),
        row_upper.astype(np.float64),
        A.nnz,
        A.indptr[:-1].astype(np.int32),
        A.indices.astype(np.int32),
        A.data.astype(np.float64),
    )
    h.run()
    status = h.modelStatusToString(h.getModelStatus())
    sol = h.getSolution()
    return (
        np.asarray(sol.col_value, dtype=float),
        np.asarray(sol.row_dual, dtype=float),
        status,
    )
