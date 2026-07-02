"""Regression tests for the adversarial-audit LP findings (LP-1/LP-2/LP-3/LP-4).

Each test reconstructs the minimal failing system its finding was confirmed
with (trivial-case-first: 24 hours, 1-2 resources) and pins the corrected
behavior.
"""

import numpy as np

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.lp import build_and_solve
from lce_portfolio.resources import ResourceArrays


def _wind_cheap(cap_mw: float = 200.0, fixed_mwyr: float = 24.0) -> ResourceArrays:
    """One always-on new resource, ~$1/MWh over a 24 h horizon at CF 1."""
    return ResourceArrays(
        names=["wind_new"],
        is_storage=np.array([False]),
        fixed_mwyr=np.array([fixed_mwyr]),
        vom=np.array([0.0]),
        cap_max_mw=np.array([cap_mw]),
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([1.0]),
        duration_h=np.array([0.0]),
        rte=np.array([1.0]),
    )


def _wind_plus_existing_hydro() -> ResourceArrays:
    """Cheap new wind (serves load) + profitable existing hydro (exports)."""
    return ResourceArrays(
        names=["wind_new", "hydro_existing"],
        is_storage=np.array([False, False]),
        fixed_mwyr=np.array([24.0, 0.0]),  # wind ~ $1/MWh over 24 h at CF 1
        vom=np.array([0.0, 5.0]),  # hydro PPA $5 < LMP $50: exporting profits
        cap_max_mw=np.array([200.0, 1000.0]),
        cap_min_mw=np.array([0.0, 0.0]),
        cf_assumed=np.array([1.0, 1.0]),
        duration_h=np.array([0.0, 0.0]),
        rte=np.array([1.0, 1.0]),
        is_existing=np.array([False, True]),
    )


def test_mode_b_no_simultaneous_buy_sell_at_full_resale() -> None:
    """LP-2: f=1.0 + IPM-no-crossover must not report arbitrary matching.

    Regression: at excess_sale_fraction=1.0 the +lmp on grid_buy exactly
    cancelled the -lmp on excess, so simultaneous buy+sell was a zero-cost
    ray; the interior-point solution reported matching ~0.61 (and phantom
    grid CO2) where 1.0 was achievable at identical cost. The epsilon on
    excess prices the ray strictly positive.
    """
    T = 24
    res = _wind_cheap()
    cf = np.ones((1, T))
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(hours=T, mode="matching_target", excess_sale_fraction=1.0)

    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=0.5)

    assert r.status == "Optimal"
    # Wind is far cheaper than the grid, so the true optimum buys nothing.
    assert r.grid_buy.sum() < 1.0
    assert r.matching_pct > 0.999
    # No hour simultaneously buys and sells.
    assert np.minimum(r.grid_buy, r.excess).max() < 0.01


def test_mode_b_strict_hourly_not_parked_at_target() -> None:
    """LP-2 strict variant: buy[t] must not sit at the constraint bound.

    Regression: the interior point parked buy[t] exactly at
    (1-target)*load[t] every hour, so matching == target looked like a
    binding constraint even when 100% was reachable at equal cost.
    """
    T = 24
    res = _wind_cheap()
    cf = np.ones((1, T))
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(
        hours=T,
        mode="matching_target",
        excess_sale_fraction=1.0,
        strict_hourly_matching=True,
    )

    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=0.5)

    assert r.status == "Optimal"
    assert r.matching_pct > 0.999


def test_additionality_existing_exports_are_surplus_not_unmatched() -> None:
    """LP-1: exported existing energy is surplus, not unmatched load.

    Regression (verified Mode B repro): with additionality on and target
    0.9, all load served by new wind still reported matching_pct == 0.90
    because existing-hydro exports were counted as unmatched load — and the
    matching constraint capped those profitable exports at exactly the
    (1-target)*Σload headroom, distorting the solve itself.
    """
    T = 24
    res = _wind_plus_existing_hydro()
    cf = np.ones((2, T))
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(
        hours=T,
        mode="matching_target",
        excess_sale_fraction=1.0,
        additionality_only=True,
    )

    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=0.9)

    assert r.status == "Optimal"
    # All load is served by new wind: nothing bought, fully matched.
    assert r.grid_buy.sum() < 1.0
    assert r.matching_pct > 0.999
    # The profitable existing exports are NOT capped at the old
    # (1-target)*Σload = 240 MWh headroom.
    existing_gen = float(r.gen[res.is_existing].sum())
    assert existing_gen > 1000.0
    # And every exported existing MWh shows up as surplus.
    assert r.surplus_mwh >= existing_gen - 1.0


def test_additionality_serving_load_still_counts_unmatched() -> None:
    """LP-1 guard: existing energy that DOES serve load stays unmatched.

    The amendment must not weaken the original exclusion: an
    existing-resource-only system with no exports still reports 0%.
    """
    T = 24
    res = ResourceArrays(
        names=["nuclear_existing"],
        is_storage=np.array([False]),
        fixed_mwyr=np.array([0.0]),
        vom=np.array([20.0]),
        cap_max_mw=np.array([1e6]),
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([1.0]),
        duration_h=np.array([0.0]),
        rte=np.array([1.0]),
        is_existing=np.array([True]),
    )
    cf = np.ones((1, T))
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    # excess_sale_fraction=0: exporting earns nothing, so the existing PPA
    # serves load only — all of it unmatched under additionality.
    cfg = PortfolioConfig(
        hours=T,
        mode="matching_target",
        excess_sale_fraction=0.0,
        additionality_only=True,
    )

    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=0.0)

    assert r.status == "Optimal"
    assert r.gen[0].sum() > 2000.0  # PPA actually serves the load
    assert r.matching_pct < 0.001


def test_hydro_budget_is_fleet_shared() -> None:
    """LP-3: the ISO monthly budget bounds the budget-hydro FLEET, not each
    resource.

    Regression: with two budget-flagged resources the LP granted each the
    full ISO budget, so fleet monthly generation reached exactly 2x the
    table value.
    """
    from lce_portfolio.config import HOURS_PER_YEAR
    from lce_portfolio.lp import _HOURS_PER_DAY, _MONTH_LEN_DAYS
    from lce_portfolio.resources import load_hydro_budget_mwh

    T = HOURS_PER_YEAR
    res = ResourceArrays(
        names=["hydro_a", "hydro_b"],
        is_storage=np.array([False, False]),
        fixed_mwyr=np.array([0.0, 0.0]),
        vom=np.array([1.0, 1.0]),
        cap_max_mw=np.array([1e6, 1e6]),
        cap_min_mw=np.array([0.0, 0.0]),
        cf_assumed=np.array([1.0, 1.0]),
        duration_h=np.array([0.0, 0.0]),
        rte=np.array([1.0, 1.0]),
        is_budget_hydro=np.array([True, True]),
    )
    cf = np.ones((2, T))
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(iso="ERCOT", hours=T, mode="premium_cap")

    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1e6)

    assert r.status == "Optimal"
    budget = load_hydro_budget_mwh("ERCOT")
    month_of_hour = np.repeat(np.arange(12), _MONTH_LEN_DAYS * _HOURS_PER_DAY)
    fleet_gen = r.gen.sum(axis=0)
    monthly = np.array([fleet_gen[month_of_hour == m].sum() for m in range(12)])
    # Fleet total respects the ISO budget in every month (small IPM slack).
    assert (monthly <= budget * 1.001).all()
    # And the budget actually binds (hydro is far cheaper than the grid).
    assert monthly.sum() > 0.9 * budget.sum()


def test_strict_hourly_shadow_price_not_hour0_dual() -> None:
    """LP-4: strict-hourly shadow_price is the load-weighted mean dual.

    Regression: only hour 0's row dual was stored, so a solve whose binding
    hours are 1..23 (hour 0 slack) reported shadow_price = 0.0 while T-1
    informative duals were dropped.
    """
    T = 24
    res = ResourceArrays(
        names=["wind_hour0", "firm_dear"],
        is_storage=np.array([False, False]),
        fixed_mwyr=np.array([1.0, 0.0]),
        vom=np.array([0.0, 80.0]),  # firm dearer than the $50 grid
        cap_max_mw=np.array([200.0, 1e6]),
        cap_min_mw=np.array([0.0, 0.0]),
        cf_assumed=np.array([1.0, 1.0]),
        duration_h=np.array([0.0, 0.0]),
        rte=np.array([1.0, 1.0]),
    )
    cf = np.zeros((2, T))
    cf[0, 0] = 1.0  # wind exists only in hour 0 -> hour 0's row is slack
    cf[1, :] = 1.0
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(
        hours=T,
        mode="matching_target",
        excess_sale_fraction=0.0,
        strict_hourly_matching=True,
    )

    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=0.9)

    assert r.status == "Optimal"
    # Binding hours 1..23 price matching at -(80-50) = -30 $/MWh; hour 0 is
    # slack at 0. Load-weighted mean ~ -30 * 23/24 ~ -28.75.
    assert r.shadow_price < -20.0
