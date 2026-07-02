"""Portfolio-selection LP: match hourly load with clean resources + storage.

This is a *portfolio* LP (capacity choice + hourly operation), distinct from the
market simulator's *dispatch* LP, and shares none of its code. It mirrors the
proven primitives, though: a flat column vector, fully vectorized sparse
constraint construction (no Python loop over hours), and HiGHS via ``highspy``
with ``addCols``/``addRows`` on a CSR matrix. Prices/shadow values come out as
row duals.

Column layout (flat vector, ``T = 8760``)::

    build_mw[r] | gen[r,t] | chg[s,t] | dis[s,t] | soc[s,t] | grid_buy[t] |
    excess[t] | build_energy[k] | exc_ex[t]

(``build_energy[k]``: one energy-capacity column per split-storage tech,
ADR 0006; ``exc_ex[t]``: existing-attributable excess, present only when
``additionality_only`` is on, ADR 0008 as amended.)

Two solve modes (see ``docs/01-lp-formulation.md``):

* **Mode A — premium_cap (default):** maximize hourly CFE matching
  (``min Σ grid_buy``) subject to portfolio premium ≤ ``delta`` $/MWh.
* **Mode B — matching_target:** minimize net portfolio cost subject to hourly
  matching ≥ ``target`` (annual, or strict per-hour for hard 24/7).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import highspy
import numpy as np
import scipy.sparse as sp

from lce_portfolio.config import HOURS_PER_YEAR, PortfolioConfig
from lce_portfolio.resources import ResourceArrays, load_hydro_budget_mwh

# Calendar month lengths for a non-leap year (days); Jan..Dec sum to 365. Used to
# aggregate the 8760 hourly generation columns into 12 monthly sums for the hydro
# energy-budget constraint (ADR 0008) without any Python loop over hours.
_MONTH_LEN_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
_HOURS_PER_DAY = 24


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
    # --- derived reporting metrics (computed in build_and_solve) --------------
    total_load_mwh: float = 0.0
    grid_buy_mwh: float = 0.0  # unmatched energy bought from grid
    surplus_mwh: float = 0.0  # clean generation sold as excess
    surplus_revenue: float = 0.0  # $ earned selling excess (× excess_sale_fraction)
    avoided_purchase_cost: float = 0.0  # $ of grid buys avoided vs BAU
    capital_cost: float = 0.0  # added clean fixed + VOM cost ($/yr)
    premium_total_per_year: float = 0.0  # net_cost − bau_cost ($/yr)
    pct_over_bau: float = 0.0  # premium as a fraction of BAU cost
    # Residual carbon (ADR 0013 grid attribution + ADR 0012 resource residual):
    #   residual_co2_tons = grid_co2_tons + resource_co2_tons
    # with the two components also reported separately so outputs can show the
    # unmatched-grid vs partial-capture-resource split.
    residual_co2_tons: float = 0.0
    grid_co2_tons: float = 0.0  # Σ_t grid_buy[t] × fossil_avg_co2_rate[t]
    resource_co2_tons: float = 0.0  # Σ_r Σ_t gen[r,t] × emission_rate_ton_mwh[r]
    # Split-storage (ADR 0006): selected energy capacity (MWh) per split tech, in
    # storage order restricted to split techs. Empty when no split tech is active.
    split_names: list[str] = field(default_factory=list)
    build_energy_mwh: np.ndarray = field(default_factory=lambda: np.zeros(0))
    # Resource names in storage order s (parallel to the storage_* arrays), so
    # reporting (ADR 0014 §2.7 SOC trace) can label each row without the
    # ResourceArrays object.
    storage_names: list[str] = field(default_factory=list)


class _Layout:
    """Column offsets for the flat variable vector.

    ``build_energy[k]`` (``bev_off``) holds one energy-capacity column per
    *split* storage tech (``n_split`` of them, ADR 0006); fixed-duration storage
    has no such column (its energy sizing is ``duration_h × build_mw``). When
    ``n_split == 0`` the block is empty and the layout is identical to PP-02's.
    """

    def __init__(
        self, n_res: int, n_sto: int, T: int, n_split: int = 0, n_exq: int = 0
    ) -> None:
        self.n_res, self.n_sto, self.T, self.n_split = n_res, n_sto, T, n_split
        self.n_exq = n_exq
        self.build_off = 0
        self.gen_off = self.build_off + n_res
        self.chg_off = self.gen_off + n_res * T
        self.dis_off = self.chg_off + n_sto * T
        self.soc_off = self.dis_off + n_sto * T
        self.buy_off = self.soc_off + n_sto * T
        self.exc_off = self.buy_off + T
        self.bev_off = self.exc_off + T  # split-storage energy-capacity columns
        # exc_ex[t]: existing-attributable excess (T columns, additionality
        # only; ADR 0008 as amended — exported existing energy is surplus,
        # not unmatched load).
        self.exq_off = self.bev_off + n_split
        self.total = self.exq_off + n_exq


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
    *,
    emission_rate: np.ndarray | None = None,
) -> PortfolioResult:
    """Build and solve one portfolio LP.

    ``setpoint`` is the premium cap ``delta`` ($/MWh) in Mode A, or the matching
    target fraction in Mode B. ``cf`` is the ``(n_res, T)`` capacity-factor
    matrix from :func:`lce_portfolio.profiles.build_cf_matrix`.

    ``emission_rate`` (keyword-only) is the ``(T,)`` hourly fossil-only average
    grid CO2 rate (tCO2/MWh) from :func:`lce_portfolio.intake.prepare_emission_rate`
    (ADR 0013). Residual carbon is attributed to unmatched purchases hour by
    hour, plus — since ADR 0012 — the residual emissions of partial-capture
    resources (gas CC + CCS) at their per-resource
    ``emission_rate_ton_mwh``::

        residual_co2_tons = Σ_t grid_buy[t] × emission_rate[t]        # grid_co2_tons
                          + Σ_r Σ_t gen[r,t] × emission_rate_ton_mwh[r]  # resource_co2_tons

    The two components are reported separately as ``grid_co2_tons`` and
    ``resource_co2_tons``. Reporting only — the matching metric and LP matching
    sums are unchanged: qualifying CCS output (past the ADR 0012 load-time
    threshold) counts *fully* toward hourly matching, with no
    intensity-weighted discount. ``emission_rate=None`` (the default) means
    grid residual-carbon reporting is off (all-zero vector), so
    ``grid_co2_tons == 0``; ``resource_co2_tons`` still accrues if a
    partial-capture resource generates.

    **Split-storage sizing (ADR 0006).** LDES and hydrogen carry a separate energy
    column ``build_energy[k]`` (MWh) costed at ``cost_energy_mwhyr``; the state of
    charge is bounded by that column (``soc ≤ build_energy``) and the duration is
    held within ``[duration_min_h, duration_max_h] × build_mw``. Fixed-duration
    storage keeps ``soc ≤ duration_h × build_mw`` unchanged.

    **Hydro monthly budget (ADR 0008).** Budget-flagged resources (existing hydro)
    have their generation capped per calendar month at the ISO's monthly energy
    budget; the constraint is skipped for ISOs without a budget entry.

    **Additionality accounting (ADR 0008, amended 2026-07-02).** With
    ``config.additionality_only`` the generation of *existing* (PPA) resources
    no longer counts toward hourly matching — but only the existing energy
    that *serves load*. Exported existing energy is surplus and per ADR 0007
    surplus is excluded from the metric entirely. The accounting identity is::

        unmatched_t = grid_buy_t + max(0, Σ_{r∈existing} gen[r,t] − excess_t)
        matching_pct = 1 − Σ_t unmatched_t / Σ_t load_t

    Excess is attributed to existing generation *first* (the only
    LP-expressible attribution; ADR 0008 amendment). In the LP this is the
    auxiliary column block ``exc_ex[t]`` with ``exc_ex ≤ excess`` and
    ``exc_ex ≤ Σ_existing gen``: Mode A penalizes ``Σ existing gen − Σ exc_ex``
    in the matching objective; Mode B puts the same net term on the matching
    constraint's buy side. When the toggle is off (default) the block is empty
    and the metric is the PP-02 ``1 − Σ grid_buy / Σ load``.
    """
    T = config.hours
    n_res, n_sto = resources.n_res, int(resources.is_storage.sum())
    storage_idx = resources.storage_idx  # resource index r for each storage s

    # --- split-storage bookkeeping (ADR 0006) -------------------------------
    split_mask_s = resources.is_split[storage_idx]  # (n_sto,) bool over storage s
    split_res_idx = storage_idx[split_mask_s]  # resource index r per split tech k
    n_split = int(split_mask_s.sum())

    # --- additionality bookkeeping (ADR 0008, amended per audit LP-1) --------
    # exc_ex[t] tracks the excess attributable to existing generation, so
    # exported existing energy is treated as surplus (excluded from the metric
    # per ADR 0007) instead of being counted as unmatched load.
    add_existing = config.additionality_only and bool(resources.is_existing.any())
    ex_idx = (
        np.flatnonzero(resources.is_existing) if add_existing else np.array([], int)
    )
    n_exq = T if add_existing else 0
    lay = _Layout(n_res, n_sto, T, n_split, n_exq)

    if load.shape != (T,) or lmp.shape != (T,) or cf.shape != (n_res, T):
        raise ValueError("load/lmp/cf shapes inconsistent with T and n_res")
    # Residual-carbon rate (ADR 0013): None -> all-zero (T,) vector, reporting off.
    if emission_rate is None:
        emission_rate = np.zeros(T)
    else:
        emission_rate = np.asarray(emission_rate, dtype=float)
        if emission_rate.shape != (T,):
            raise ValueError(
                f"emission_rate must have shape ({T},), got {emission_rate.shape}"
            )

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

        # energy bound: soc[t] <= energy capacity.
        #   fixed-duration storage: soc[t] - duration_h*build_mw <= 0
        #   split storage (ADR 0006): soc[t] - build_energy[k] <= 0
        split_pos = np.full(n_sto, -1, dtype=int)  # split-tech column k per storage s
        split_pos[split_mask_s] = np.arange(n_split)
        eb_col_s = np.where(
            split_mask_s,
            lay.bev_off + np.clip(split_pos, 0, None),
            lay.build_off + storage_idx,
        )
        eb_coef_s = np.where(split_mask_s, -1.0, -resources.duration_h[storage_idx])
        rows += [roff + sidx, roff + sidx]
        cols += [lay.soc_off + si * T + th, np.repeat(eb_col_s, T)]
        data += [np.ones(n_sto * T), np.repeat(eb_coef_s, T)]
        rlow.append(np.full(n_sto * T, -np.inf))
        rupp.append(np.zeros(n_sto * T))
        roff += n_sto * T

        # duration bounds for split storage (ADR 0006):
        #   duration_min*build_mw <= build_energy <= duration_max*build_mw
        if n_split:
            kk = np.arange(n_split)
            bev_cols = lay.bev_off + kk
            bmw_cols = lay.build_off + split_res_idx
            # min bound: build_energy - duration_min*build_mw >= 0
            rows += [roff + kk, roff + kk]
            cols += [bev_cols, bmw_cols]
            data += [np.ones(n_split), -resources.duration_min_h[split_res_idx]]
            rlow.append(np.zeros(n_split))
            rupp.append(np.full(n_split, np.inf))
            roff += n_split
            # max bound: build_energy - duration_max*build_mw <= 0
            rows += [roff + kk, roff + kk]
            cols += [bev_cols, bmw_cols]
            data += [np.ones(n_split), -resources.duration_max_h[split_res_idx]]
            rlow.append(np.full(n_split, -np.inf))
            rupp.append(np.zeros(n_split))
            roff += n_split

    # ---- hydro monthly energy budget (ADR 0008) ----
    # Budget-flagged existing hydro: Σ_{t in month m} gen[r,t] <= budget_mwh[m].
    # Skipped when the ISO has no budget entry (e.g. SAMPLE) or no budget resource.
    budget_res_idx = np.flatnonzero(resources.is_budget_hydro)
    hydro_budget_mwh = (
        load_hydro_budget_mwh(config.iso) if budget_res_idx.size else None
    )
    if budget_res_idx.size and hydro_budget_mwh is not None:
        if T != HOURS_PER_YEAR:
            raise ValueError(
                "hydro monthly-budget constraint requires the full 8760-hour "
                f"calendar (T={HOURS_PER_YEAR}); got hours={T}"
            )
        n_bud = budget_res_idx.size
        # Month index of each hour from the non-leap calendar (np.repeat, no loop).
        month_of_hour = np.repeat(np.arange(12), _MONTH_LEN_DAYS * _HOURS_PER_DAY)
        b = np.repeat(np.arange(n_bud), T)  # budget-resource position 0..n_bud-1
        res_rep = np.repeat(budget_res_idx, T)  # resource index r
        t_rep = np.tile(np.arange(T), n_bud)  # hour t
        month_rep = np.tile(month_of_hour, n_bud)  # month m of each (b, t)
        rows.append(roff + b * 12 + month_rep)
        cols.append(lay.gen_off + res_rep * T + t_rep)
        data.append(np.ones(n_bud * T))
        rlow.append(np.full(n_bud * 12, -np.inf))
        rupp.append(np.tile(hydro_budget_mwh, n_bud))
        roff += n_bud * 12

    # ---- existing-attributable excess (additionality, ADR 0008 amended) ----
    # exc_ex[t] <= excess[t] and exc_ex[t] <= Σ_existing gen[r,t]; the
    # objective/constraint pressure below pushes exc_ex up to
    # min(excess_t, existing_gen_t) — existing-first attribution, the only
    # LP-expressible choice (audit finding LP-1).
    if add_existing:
        hours_a = np.arange(T)
        exq_cols = lay.exq_off + hours_a
        rows += [roff + hours_a, roff + hours_a]
        cols += [exq_cols, lay.exc_off + hours_a]
        data += [np.ones(T), -np.ones(T)]
        rlow.append(np.full(T, -np.inf))
        rupp.append(np.zeros(T))
        roff += T
        rows.append(roff + hours_a)
        cols.append(exq_cols)
        data.append(np.ones(T))
        rows.append(roff + np.tile(hours_a, ex_idx.size))
        cols.append(
            lay.gen_off + np.repeat(ex_idx, T) * T + np.tile(hours_a, ex_idx.size)
        )
        data.append(-np.ones(ex_idx.size * T))
        rlow.append(np.full(T, -np.inf))
        rupp.append(np.zeros(T))
        roff += T

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
        if n_split:  # split-storage energy capex enters the premium budget (ADR 0006)
            rows.append(np.full(n_split, roff))
            cols.append(lay.bev_off + np.arange(n_split))
            data.append(resources.cost_energy_mwhyr[split_res_idx])
        rlow.append(np.array([-np.inf]))
        rupp.append(np.array([setpoint * sum_load + bau_cost]))
        premium_row = roff
        n_premium_rows = 1
        roff += 1
    elif config.mode == "matching_target":
        # Additionality (ADR 0008 amended): existing-resource generation NET of
        # its exported surplus counts against the matching budget — coef +1 on
        # existing gen, -1 on exc_ex (audit finding LP-1: counting gross
        # existing gen let profitable exports eat the matching headroom and
        # distorted the solve, not just the metric).
        if config.strict_hourly_matching:
            hours = np.arange(T)
            rows.append(roff + hours)
            cols.append(lay.buy_off + hours)
            data.append(np.ones(T))
            if add_existing:
                # grid_buy[t] + Σ_existing gen[r,t] - exc_ex[t] <= (1-target)*load[t]
                rows.append(roff + np.tile(hours, ex_idx.size))
                cols.append(
                    lay.gen_off + np.repeat(ex_idx, T) * T + np.tile(hours, ex_idx.size)
                )
                data.append(np.ones(ex_idx.size * T))
                rows.append(roff + hours)
                cols.append(lay.exq_off + hours)
                data.append(-np.ones(T))
            rlow.append(np.full(T, -np.inf))
            rupp.append((1.0 - setpoint) * load)
            premium_row = roff  # first of T rows; see load-weighted dual below
            n_premium_rows = T
            roff += T
        else:
            rows.append(np.full(T, roff))
            cols.append(lay.buy_off + np.arange(T))
            data.append(np.ones(T))
            if add_existing:
                # Σ grid_buy + Σ_existing gen - Σ exc_ex <= (1-target)*Σ load
                rows.append(np.full(ex_idx.size * T, roff))
                cols.append(
                    lay.gen_off
                    + np.repeat(ex_idx, T) * T
                    + np.tile(np.arange(T), ex_idx.size)
                )
                data.append(np.ones(ex_idx.size * T))
                rows.append(np.full(T, roff))
                cols.append(lay.exq_off + np.arange(T))
                data.append(-np.ones(T))
            rlow.append(np.array([-np.inf]))
            rupp.append(np.array([(1.0 - setpoint) * sum_load]))
            premium_row = roff
            n_premium_rows = 1
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
        # Additionality (ADR 0008 amended): existing-resource generation NET of
        # its exported surplus is not matching — +1 on existing gen, -1 on
        # exc_ex, so minimization drives exc_ex to min(excess, existing_gen)
        # and only load-serving existing energy is penalized (audit LP-1).
        if add_existing:
            ex_gen_cols = (
                lay.gen_off
                + np.repeat(ex_idx, T) * T
                + np.tile(np.arange(T), ex_idx.size)
            )
            cost[ex_gen_cols] += 1.0
            cost[lay.exq_off : lay.exq_off + T] = -1.0
    else:
        cost[lay.build_off : lay.build_off + n_res] = resources.fixed_mwyr
        cost[lay.gen_off : lay.chg_off] = np.repeat(resources.vom, T)
        cost[lay.buy_off : lay.buy_off + T] = lmp
        # ε tiebreak on excess (audit finding LP-2): at the ratified
        # excess_sale_fraction = 1.0 (ADR 0005) the +lmp on grid_buy exactly
        # cancels the -lmp on excess, so simultaneous buy+sell is a zero-cost
        # ray and the crossover-off IPM (ADR 0003) returns an arbitrary
        # interior point of the fat optimal face — matching_pct/grid CO2 were
        # reported from meaningless buy/excess levels. The epsilon prices the
        # ray strictly positive (a buy+sell pair now costs +ε) without
        # materially moving any true optimum, mirroring the storage_epsilon
        # degeneracy tiebreak. Mode A is immune (its objective is +1 per
        # buy-MWh) and gets no epsilon. Reported net_cost/premium recompute
        # from lmp post-hoc, so ε never leaks into the premium.
        cost[lay.exc_off : lay.exc_off + T] = -sale * lmp + config.storage_epsilon
        if n_split:  # split-storage energy capex (ADR 0006)
            cost[lay.bev_off : lay.bev_off + n_split] = resources.cost_energy_mwhyr[
                split_res_idx
            ]
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

    # Robustness: an infeasible/failed solve can return an empty (or short, or
    # garbage last-iterate) solution vector, which would crash the reshapes below
    # or corrupt the derived metrics. Substitute zeros so the sweep survives; the
    # non-"Optimal" status flags the setpoint downstream, and solve_ok gates the
    # derived metrics so an infeasible point can never masquerade as fully matched
    # / cheaper-than-BAU (it would otherwise report matching_pct=1.0 from the
    # zeroed grid_buy and premium = -bau/load from the zeroed cost terms).
    solve_ok = status == "Optimal" and col_value.size == lay.total
    if not solve_ok:
        col_value = np.zeros(lay.total)
        row_dual = np.zeros(A.shape[0])

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
    excess = col_value[lay.exc_off : lay.exc_off + T]
    build_energy = col_value[lay.bev_off : lay.bev_off + n_split]  # (n_split,) MWh

    # Split-storage energy capex ($/yr): cost_energy_mwhyr × built energy MWh.
    energy_capex = float(resources.cost_energy_mwhyr[split_res_idx] @ build_energy)

    # Matching (ADR 0007/0008 as amended): unmatched = grid purchases, plus —
    # under additionality — existing-resource generation NET of the excess
    # attributable to it (existing-first). Exported existing energy serves no
    # load, so per ADR 0007 it is surplus, excluded from the metric — not an
    # unmatched purchase (audit finding LP-1). Computed from the primal
    # gen/excess values (not the exc_ex columns) so a slack matching
    # constraint's degenerate exc_ex level can never distort the report.
    unmatched = float(grid_buy.sum())
    if add_existing:
        unmatched += float(np.clip(gen[ex_idx].sum(axis=0) - excess, 0.0, None).sum())
    matching_pct = 1.0 - unmatched / sum_load if sum_load else 0.0

    net_cost = (
        float(resources.fixed_mwyr @ build_mw)
        + energy_capex
        + float((resources.vom[:, None] * gen).sum())
        + float(lmp @ grid_buy)
        - sale * float(lmp @ excess)
    )
    premium = (net_cost - bau_cost) / sum_load if sum_load else 0.0
    shadow = (
        float(row_dual[premium_row]) if premium_row < len(row_dual) else float("nan")
    )

    # Derived reporting metrics (lmp/load are in scope here).
    capital_cost = (
        float(resources.fixed_mwyr @ build_mw)
        + energy_capex
        + float((resources.vom[:, None] * gen).sum())
    )
    surplus_revenue = sale * float(lmp @ excess)
    avoided_purchase_cost = bau_cost - float(lmp @ grid_buy)
    # Residual carbon: unmatched grid purchases at the hourly fossil-only
    # average rate (ADR 0013 — hour-varying by design, never a flat annual
    # scalar) PLUS the residual emissions of partial-capture resources at their
    # per-resource rate (ADR 0012). Matching credit is unaffected — qualifying
    # CCS output counts fully toward matching; only the carbon report sees it.
    grid_co2_tons = float(grid_buy @ emission_rate)
    resource_co2_tons = float(resources.emission_rate_ton_mwh @ gen.sum(axis=1))
    residual_co2_tons = grid_co2_tons + resource_co2_tons

    premium_total_per_year = net_cost - bau_cost
    pct_over_bau = (net_cost - bau_cost) / bau_cost if bau_cost else 0.0

    if not solve_ok:
        # A failed solve served no load: report 0% matched and a zero premium
        # rather than metrics derived from the zeroed arrays. bau_cost stays (it
        # is an input-side fact); status carries the failure downstream.
        matching_pct = 0.0
        net_cost = 0.0
        premium = 0.0
        shadow = float("nan")
        avoided_purchase_cost = 0.0
        premium_total_per_year = 0.0
        pct_over_bau = 0.0

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
        total_load_mwh=sum_load,
        grid_buy_mwh=float(grid_buy.sum()),
        surplus_mwh=float(excess.sum()),
        surplus_revenue=surplus_revenue,
        avoided_purchase_cost=avoided_purchase_cost,
        capital_cost=capital_cost,
        premium_total_per_year=premium_total_per_year,
        pct_over_bau=pct_over_bau,
        residual_co2_tons=residual_co2_tons,
        grid_co2_tons=grid_co2_tons,
        resource_co2_tons=resource_co2_tons,
        split_names=[resources.names[r] for r in split_res_idx],
        build_energy_mwh=build_energy,
        storage_names=[resources.names[r] for r in storage_idx],
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
