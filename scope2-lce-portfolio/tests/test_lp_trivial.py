"""Trivial-case LP tests: 1 resource, 1 zone, 24 hours (per the testing rule).

Hand-computable optima verify the LP wiring before scaling to 8760.
"""

import numpy as np

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.lp import build_and_solve

from conftest import daytime_solar_cf, solar_only, solar_plus_battery


def test_solar_only_matching_capped_at_daylight() -> None:
    """Solar (daytime-only) with a generous premium can match at most 8/24.

    Load is flat 100 MWh; solar is available (CF=1) only for 8 hours/day and
    there is no storage, so the maximum hourly matching is exactly 8/24. With a
    large premium cap the LP should reach it: daytime grid purchases go to zero,
    night hours are bought from the grid.
    """
    T = 24
    res = solar_only()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(hours=T, mode="premium_cap", excess_sale_fraction=1.0)

    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1e6)

    assert r.status == "Optimal"
    assert np.isclose(r.matching_pct, 8.0 / 24.0, atol=1e-3)
    assert r.build_mw[0] >= 99.9  # enough to cover 100 MW daytime load
    # daytime purchases ~0, night purchases ~100
    assert np.allclose(r.grid_buy[8:16], 0.0, atol=1e-3)
    assert np.allclose(r.grid_buy[:8], 100.0, atol=1e-3)


def test_energy_balance_holds() -> None:
    """The returned solution satisfies the per-hour energy balance."""
    T = 24
    res = solar_only()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(hours=T, mode="premium_cap")
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1e6)
    supply = r.gen.sum(axis=0) + r.grid_buy - r.excess
    assert np.allclose(supply, load, atol=1e-3)


def test_storage_enables_overnight_matching() -> None:
    """Adding a battery lets daytime solar surplus serve night load.

    With 4-hour storage the trough hours immediately after sunset can be matched,
    so matching exceeds the solar-only 8/24 ceiling.
    """
    T = 24
    res = solar_plus_battery()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(hours=T, mode="premium_cap", excess_sale_fraction=1.0)
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1e6)
    assert r.status == "Optimal"
    assert r.matching_pct > 8.0 / 24.0 + 1e-3
    assert r.build_mw[1] > 0.0  # battery gets built


def test_matching_target_mode_feasible() -> None:
    """Mode B reaches a modest matching target and reports a premium."""
    T = 24
    res = solar_plus_battery()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(hours=T, mode="matching_target", excess_sale_fraction=1.0)
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=0.30)  # 30% matching
    assert r.status == "Optimal"
    assert r.matching_pct >= 0.30 - 1e-3
