"""Structural energy-balance check across a solve with both storage types.

Rather than checking downstream metrics (matching%, premium), this asserts
the raw per-hour physical identity the LP's energy-balance rows encode:
``gen + dis - chg + buy - excess - load ~= 0`` for every hour. This is the
test that would catch a layout/sign regression in the column/row wiring
directly (e.g. a flipped charge/discharge sign, a mis-offset column slice)
even if it happened to leave the headline metrics looking plausible.

Uses a 720-hour (one-month) horizon with both storage types (split + fixed)
active — long enough to exercise several charge/discharge cycles, short
enough to stay fast (full 8760 with 2 storage techs takes 15-35s, see
conftest.cross_feature_system's docstring and the PP-07 final report).
"""

import numpy as np

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.lp import build_and_solve

from conftest import cross_feature_system


def test_energy_balance_residual_near_zero_every_hour() -> None:
    T = 720
    res, cf, load, lmp = cross_feature_system(T=T)
    cfg = PortfolioConfig(
        hours=T,
        mode="premium_cap",
        excess_sale_fraction=0.5,
        # iso=SAMPLE has no hydro-budget table row, so the monthly-budget
        # constraint is skipped (it would otherwise raise for T != 8760);
        # hydro_existing just dispatches on its flat CF here.
        iso="SAMPLE",
    )
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=15.0)
    assert r.status == "Optimal"

    supply = (
        r.gen.sum(axis=0)
        + r.storage_discharge.sum(axis=0)
        - r.storage_charge.sum(axis=0)
        + r.grid_buy
        - r.excess
    )
    # IPM interior-point tolerance: ~1e-3 relative to the hourly load scale.
    tol = 1e-3 * np.maximum(load, 1.0)
    residual = np.abs(supply - load)
    assert np.all(residual <= tol), float(residual.max())
