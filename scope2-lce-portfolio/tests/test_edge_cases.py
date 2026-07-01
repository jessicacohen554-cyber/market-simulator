"""Edge-case tests: infeasible solves, zonal-LMP reconciliation gaps, and a
hydro budget so tight it binds in every calendar month.
"""

import numpy as np
import pandas as pd

from lce_portfolio.config import HOURS_PER_YEAR, PortfolioConfig
from lce_portfolio.intake import collapse_zonal_lmp
from lce_portfolio.lp import build_and_solve
from lce_portfolio.resources import ResourceArrays, load_hydro_budget_mwh

# --- infeasible Mode B: strict target + tiny caps ---------------------------


def _infeasible_tiny_cap_case():
    """A 100% strict-hourly target with a cap far below load: infeasible."""
    T = 24
    res = ResourceArrays(
        names=["solar"],
        is_storage=np.array([False]),
        fixed_mwyr=np.array([1.0]),
        vom=np.array([0.0]),
        cap_max_mw=np.array([1.0]),  # tiny: can never cover 100 MW load
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([1.0]),
        duration_h=np.array([0.0]),
        rte=np.array([1.0]),
    )
    cf = np.ones((1, T))
    load = np.full(T, 100.0)
    lmp = np.full(T, 40.0)
    cfg = PortfolioConfig(hours=T, mode="matching_target", strict_hourly_matching=True)
    return build_and_solve(cfg, res, load, lmp, cf, setpoint=1.0)


def test_infeasible_strict_target_with_tiny_caps_zeroes_arrays() -> None:
    """An infeasible solve degrades to a non-Optimal status with all physical
    arrays zeroed (the ``_solve_highs`` robustness fallback), not a crash or
    stale values."""
    r = _infeasible_tiny_cap_case()

    assert r.status != "Optimal"
    assert r.build_mw.shape == (1,)
    assert np.all(r.build_mw == 0.0)
    assert np.all(r.gen == 0.0)
    assert np.all(r.grid_buy == 0.0)
    assert np.all(r.excess == 0.0)
    assert r.net_cost == 0.0


def test_infeasible_solve_reports_zero_matching_not_full_matching() -> None:
    """A failed solve must not masquerade as fully matched / cheaper-than-BAU.

    (Was an xfail-marked BUG found by PP-07: the zero-fallback arrays flowed
    into the metric formulas, reporting matching_pct=1.0 and premium=-lmp for a
    solve that served no load. Fixed by gating the derived metrics on
    ``solve_ok`` in ``build_and_solve``.)
    """
    r = _infeasible_tiny_cap_case()
    assert r.status != "Optimal"
    assert r.matching_pct == 0.0
    assert r.premium == 0.0
    assert r.pct_over_bau == 0.0
    assert r.premium_total_per_year == 0.0
    assert r.avoided_purchase_cost == 0.0


# --- collapse_zonal_lmp: a zone missing its load row entirely --------------


def test_collapse_zonal_lmp_excludes_zone_with_no_load_row() -> None:
    """A zone present in the LMP file with *no* matching load row (not merely a
    zero-load row) is excluded from that hour's average, per the documented
    inner-join contract — distinct from the zero-load-row fallback-to-mean
    case already covered in test_intake.py."""
    zonal_lmp = pd.DataFrame(
        {
            "hour": [0, 0, 1],
            "iso": ["A", "A", "A"],
            "zone": ["z1", "z2", "z1"],
            "lmp": [10.0, 999.0, 20.0],  # z2's 999 must never appear at hour 0
        }
    )
    zonal_load = pd.DataFrame(
        {
            "hour": [0, 1],
            "iso": ["A", "A"],
            "zone": ["z1", "z1"],  # z2 has no row at all for either hour
            "load_mwh": [100.0, 50.0],
        }
    )
    out = collapse_zonal_lmp(zonal_lmp, zonal_load).set_index("hour")
    assert out.loc[0, "lmp"] == 10.0  # z2 excluded entirely, not averaged in
    assert out.loc[1, "lmp"] == 20.0


# --- hydro monthly budget so tight it binds in every month -----------------


def test_hydro_budget_binds_every_calendar_month() -> None:
    """A flat load far above the monthly-budget-implied average power binds
    the hydro constraint in all 12 months at once (not just January, as in
    test_lp_extensions.py's single-month check)."""
    T = HOURS_PER_YEAR
    res = ResourceArrays(
        names=["hydro_existing"],
        is_storage=np.array([False]),
        fixed_mwyr=np.array([0.0]),
        vom=np.array([25.0]),
        cap_max_mw=np.array([1e6]),
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([1.0]),
        duration_h=np.array([0.0]),
        rte=np.array([1.0]),
        is_existing=np.array([True]),
        is_budget_hydro=np.array([True]),
    )
    cf = np.ones((1, T))
    # 5000 MW flat load: even the largest monthly ERCOT budget (May, 170 GWh
    # over 744 h) implies < 230 MW average, so every month's cap binds.
    load = np.full(T, 5000.0)
    lmp = np.full(T, 40.0)
    cfg = PortfolioConfig(
        iso="ERCOT", hours=T, mode="matching_target", excess_sale_fraction=0.0
    )
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=0.0)
    assert r.status == "Optimal"

    budget_mwh = load_hydro_budget_mwh("ERCOT")
    month_len_days = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
    month_of_hour = np.repeat(np.arange(12), month_len_days * 24)
    for m in range(12):
        gen_m = r.gen[0, month_of_hour == m].sum()
        assert np.isclose(gen_m, budget_mwh[m], rtol=1e-3), f"month {m + 1}"
