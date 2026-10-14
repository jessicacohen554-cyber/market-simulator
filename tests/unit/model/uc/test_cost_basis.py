"""UC-1-FIX-5: the integer clusters' UC cost basis pays the no-load once.

1 cluster / 1 zone / 24 h with a known CEMS line ``F(P) = a + b P`` per unit:
the fleet heat rate is the full-output AVERAGE ``a / pbar + b`` (what every
offer band multiplies), the explicit no-load is ``a``, and the UC's cost of a
unit at any output must equal the fuel truth ``(a + b P) p + vom P``
(FINDING-ucmilp-fix5-cost-basis-2026-10-14).
"""

from __future__ import annotations

import numpy as np

from market_sim.model.uc.params import build_uc_cluster_params
from market_sim.model.uc.solve import UcSolveOptions, solve_window
from market_sim.model.uc.window import UcWindowModel, WindowState, slice_window_inputs

from .conftest import toy_inputs

T = 24
A_MMBTU_H = 50.0  # toy uc-params: 100 MMBtu/h plant / 2 units
PBAR = 100.0
HR_AVG = 7.0  # toy CC heat rate (the full-output average)
B_SLOPE = HR_AVG - A_MMBTU_H / PBAR  # 6.5 MMBtu/MWh incremental
VOM = 2.0


def _price(mc_cc: float) -> float:
    return (mc_cc - VOM) / HR_AVG


def _unit_cost(mc_uc_cc, noload_usd_h, P):
    """UC cost of one online unit at output ``P`` (MW) for one hour."""
    return noload_usd_h + mc_uc_cc * P


def test_unit_cost_equals_fuel_truth_at_pmin_and_pmax(uc_params_frame):
    _, fa, _, mc, _ = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    k = p.integer_clusters
    mc_uc = p.incremental_energy_cost(fa, mc)
    nl = p.noload_cost_per_unit_h(fa, mc)[k][0]
    price = _price(mc[0, 0])
    for P in (p.mlf[0] * PBAR, PBAR):
        truth = (A_MMBTU_H + B_SLOPE * P) * price + VOM * P
        got = _unit_cost(mc_uc[0, :], nl, P)
        np.testing.assert_allclose(got, truth, rtol=1e-12)
    # The pre-fix basis (average energy + explicit no-load) over-charges by
    # exactly a * P / pbar of fuel.
    old = nl + mc[0, :] * PBAR
    np.testing.assert_allclose(old - (nl + mc_uc[0, :] * PBAR), A_MMBTU_H * price)


def test_full_output_cost_is_the_as_offered_curve(uc_params_frame):
    _, fa, _, mc, _ = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    mc_uc = p.incremental_energy_cost(fa, mc)
    nl = p.noload_cost_per_unit_h(fa, mc)[p.integer_clusters][0]
    np.testing.assert_allclose(nl + mc_uc[0, :] * PBAR, mc[0, :] * PBAR)


def test_non_members_and_fuel_free_rows_are_untouched(uc_params_frame):
    _, fa, _, mc, _ = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    mc_uc = p.incremental_energy_cost(fa, mc)
    # Nuclear (row 1) is outside the candidate set; the CT cluster (row 2) is
    # not integer: both keep mc_base exactly.
    np.testing.assert_array_equal(mc_uc[1:], mc[1:])
    # A member whose offer passes no fuel (mc == vom) carries no no-load heat.
    mc_free = mc.copy()
    mc_free[0, :] = VOM
    np.testing.assert_array_equal(p.incremental_energy_cost(fa, mc_free)[0], VOM)
    # The input array is never mutated.
    assert p.incremental_energy_cost(fa, mc) is not mc


def test_window_objective_prices_the_cluster_at_fuel_truth(uc_params_frame):
    """The solved window's objective, decomposed, is fuel truth for the CC."""
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    k = p.integer_clusters
    mc_uc = p.incremental_energy_cost(fa, mc)
    nl = p.noload_cost_per_unit_h(fa, mc)[k]
    inputs = slice_window_inputs(fa, demand, dk, 0, T)
    state = WindowState(
        u_prev=np.zeros(1),
        v_hist=np.zeros((1, 0)),
        w_hist=np.zeros((1, 0)),
        soc_prev=None,
        p_prev=None,
        avail_prev=None,
    )
    w = UcWindowModel(inputs, p, mc_uc, nl, state)
    res = solve_window(w, UcSolveOptions(mip_rel_gap=1e-9, time_limit_s=60.0))
    assert res.status == "Optimal"
    P = np.asarray(res.dispatch, dtype=float)
    price = _price(mc[0, 0])
    truth_cc = np.sum((A_MMBTU_H * res.u[0] + B_SLOPE * P[0]) * price + VOM * P[0])
    start = np.sum(p.su_per_mw[0] * PBAR * res.v[0])
    others = np.sum(mc[1:] * P[1:])
    slack = res.objective - (truth_cc + start + others)
    assert abs(slack) <= 1e-6 * max(1.0, abs(res.objective)), slack
