"""Tests for the parametric sweep: the frontier must be monotone."""

import numpy as np

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.lp import build_and_solve
from lce_portfolio.sweep import run_sweep

from conftest import daytime_solar_cf, solar_only, solar_plus_battery


def _mini_inputs(T: int = 24):
    """A small solar+battery scenario with a mild high-price evening peak."""
    res = solar_plus_battery()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    # evening hours pricier so matching them is valuable
    lmp = np.full(T, 30.0)
    lmp[16:20] = 90.0
    return res, cf, load, lmp


def test_frontier_matching_non_decreasing() -> None:
    """More premium budget can only maintain or increase achievable matching."""
    res, cf, load, lmp = _mini_inputs()
    cfg = PortfolioConfig(
        hours=24,
        mode="premium_cap",
        premium_deltas=(1.0, 5.0, 20.0, 100.0),
        excess_sale_fraction=0.5,
    )
    sweep = run_sweep(cfg, res, load, lmp, cf)
    matches = [r.matching_pct for r in sweep.results]
    assert all(r.status == "Optimal" for r in sweep.results)
    for a, b in zip(matches, matches[1:]):
        assert b >= a - 1e-4  # non-decreasing in the premium cap


def test_frontier_records_setpoints() -> None:
    """The frontier exposes (setpoint, matching, premium) per solve."""
    res, cf, load, lmp = _mini_inputs()
    cfg = PortfolioConfig(hours=24, mode="premium_cap", premium_deltas=(2.0, 10.0))
    sweep = run_sweep(cfg, res, load, lmp, cf)
    front = sweep.frontier
    assert [f[0] for f in front] == [2.0, 10.0]
    assert all(0.0 <= f[1] <= 1.0 for f in front)


def test_infeasible_setpoint_does_not_crash() -> None:
    """An impossible strict-24/7 target returns a non-Optimal status, not a crash.

    Solar-only with no storage cannot serve night hours, so strict per-hour 100%
    matching is infeasible. build_and_solve must degrade gracefully.
    """
    T = 24
    res = solar_only()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.full(T, 40.0)
    cfg = PortfolioConfig(hours=T, mode="matching_target", strict_hourly_matching=True)
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1.0)
    assert r.status != "Optimal"
    assert r.build_mw.shape == (res.n_res,)  # arrays intact despite failure
