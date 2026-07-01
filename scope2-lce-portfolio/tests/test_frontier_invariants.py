"""Frontier invariant tests on a tiny (solar + battery, 24h) system.

test_sweep.py already checks Mode A matching monotonicity for one delta set;
these tests add the companion invariants: Mode B premium monotonicity, and
that Mode A never exceeds its own premium budget.
"""

import numpy as np

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.sweep import run_sweep

from conftest import daytime_solar_cf, solar_plus_battery


def _tiny_inputs(T: int = 24):
    res = solar_plus_battery()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.full(T, 30.0)
    lmp[16:20] = 90.0  # evening peak makes matching those hours valuable
    return res, cf, load, lmp


def test_mode_a_matching_non_decreasing_and_premium_within_cap() -> None:
    """Mode A: matching% never decreases as the premium cap rises, and the
    achieved premium never exceeds its own setpoint (up to solver tolerance)."""
    res, cf, load, lmp = _tiny_inputs()
    cfg = PortfolioConfig(
        hours=24,
        mode="premium_cap",
        premium_deltas=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0),
        excess_sale_fraction=0.5,
    )
    sweep = run_sweep(cfg, res, load, lmp, cf)
    assert all(r.status == "Optimal" for r in sweep.results)

    matches = [r.matching_pct for r in sweep.results]
    for a, b in zip(matches, matches[1:]):
        assert b >= a - 1e-4

    tol = 1e-3  # IPM tolerance on the premium constraint's $/MWh scale
    for r in sweep.results:
        assert r.premium <= r.setpoint + tol


def test_mode_b_premium_non_decreasing_in_target() -> None:
    """Mode B: least-cost premium never decreases as the matching target rises
    (a stricter target can only keep or raise the cost floor)."""
    res, cf, load, lmp = _tiny_inputs()
    cfg = PortfolioConfig(
        hours=24,
        mode="matching_target",
        matching_targets=(0.1, 0.3, 0.5, 0.7, 0.9, 1.0),
        excess_sale_fraction=0.5,
    )
    sweep = run_sweep(cfg, res, load, lmp, cf)
    assert all(r.status == "Optimal" for r in sweep.results)

    premiums = [r.premium for r in sweep.results]
    for a, b in zip(premiums, premiums[1:]):
        assert b >= a - 1e-6
