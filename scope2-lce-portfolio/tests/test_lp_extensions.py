"""PP-02b LP-extension tests: split storage, hydro budget, additionality, carbon.

Trivial-case-first and hand-computable (per the testing rule): 1–2 resources and
a 24- or 48-hour horizon wherever the physics allows, and a single full-8760
solve for the hydro monthly budget (which is defined on the calendar year).
"""

import numpy as np

from lce_portfolio.config import HOURS_PER_YEAR, PortfolioConfig
from lce_portfolio.lp import build_and_solve
from lce_portfolio.resources import ResourceArrays


# --- split storage (ADR 0006) ----------------------------------------------


def _solar_plus_split(duration_max_h: float) -> ResourceArrays:
    """Solar (day) + one power/energy-split storage tech, RTE=1 for clean sums.

    Power capex 100 $/MW-yr, energy capex 10 $/MWh-yr, duration bounds
    [4, ``duration_max_h``]. RTE=1 makes SOC dynamics soc[t]=soc[t-1]+chg−dis, so
    the energy/power sizing is exactly hand-computable.
    """
    return ResourceArrays(
        names=["solar", "split"],
        is_storage=np.array([False, True]),
        is_split=np.array([False, True]),
        fixed_mwyr=np.array([1.0, 100.0]),
        cost_energy_mwhyr=np.array([0.0, 10.0]),
        vom=np.array([0.0, 0.0]),
        cap_max_mw=np.array([1e6, 1e6]),
        cap_min_mw=np.array([0.0, 0.0]),
        cf_assumed=np.array([1.0, 0.0]),
        duration_h=np.array([0.0, 0.0]),
        duration_min_h=np.array([0.0, 4.0]),
        duration_max_h=np.array([0.0, duration_max_h]),
        rte=np.array([1.0, 1.0]),
    )


def _day_night_case(res: ResourceArrays):
    """Build+solve the canonical case: 12h day generation, 12h night load=10.

    All night energy (120 MWh) must be stored during the day, so peak SOC = 120
    and peak charge = peak discharge = 10 MW. Mode B with a 100% matching target
    forces the storage to fully bridge; least-cost sizing then pins power/energy.
    """
    T = 24
    cf = np.zeros((res.n_res, T))
    cf[0, 0:12] = 1.0  # solar available first 12 hours only
    load = np.zeros(T)
    load[12:24] = 10.0  # load only at night
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(hours=T, mode="matching_target", excess_sale_fraction=0.0)
    return build_and_solve(cfg, res, load, lmp, cf, setpoint=1.0)  # target=100%


def test_split_storage_interior_duration() -> None:
    """Duration lands strictly inside [4,100]: peak-SOC 120 / peak-power 10 = 12h.

    Energy and power are both costed, so least cost builds exactly the required
    energy (120 MWh) and power (10 MW); implied duration 12 h is interior. Cost
    arithmetic: net_cost = 1·10 (solar) + 100·10 (power) + 10·120 (energy) = 2210.
    """
    r = _day_night_case(_solar_plus_split(duration_max_h=100.0))
    assert r.status == "Optimal"
    assert r.split_names == ["split"]
    build_power = r.build_mw[1]
    build_energy = r.build_energy_mwh[0]
    duration = build_energy / build_power
    assert 4.0 <= duration <= 100.0  # within bounds
    assert np.isclose(duration, 12.0, atol=0.2)  # interior
    assert np.isclose(build_energy, 120.0, rtol=0.02)
    assert np.isclose(build_power, 10.0, rtol=0.02)
    assert np.isclose(r.build_mw[0], 10.0, rtol=0.02)  # solar
    # net cost = solar power capex + storage power capex + storage energy capex
    assert np.isclose(r.net_cost, 1 * 10 + 100 * 10 + 10 * 120, rtol=0.02)


def test_split_storage_duration_max_binds() -> None:
    """Tightening duration_max to 8 h forces power oversizing (bound binds).

    120 MWh of energy at ≤8 h duration needs ≥15 MW of power, so build_mw rises
    to 15 and the implied duration sits exactly on the 8 h ceiling.
    """
    r = _day_night_case(_solar_plus_split(duration_max_h=8.0))
    assert r.status == "Optimal"
    duration = r.build_energy_mwh[0] / r.build_mw[1]
    assert np.isclose(duration, 8.0, atol=1e-3)  # max bound binds
    assert np.isclose(r.build_mw[1], 15.0, rtol=0.02)  # power oversized
    assert np.isclose(r.build_energy_mwh[0], 120.0, rtol=0.02)


def test_nonsplit_storage_unchanged_by_split_code() -> None:
    """A pure fixed-duration battery is unaffected by the split machinery.

    Same day/night case with a 4-hour fixed-duration battery: no build_energy
    column, energy bound uses duration_h·build_mw, and the case still solves.
    """
    T = 24
    res = ResourceArrays(
        names=["solar", "battery"],
        is_storage=np.array([False, True]),
        fixed_mwyr=np.array([1.0, 50.0]),
        vom=np.array([0.0, 0.0]),
        cap_max_mw=np.array([1e6, 1e6]),
        cap_min_mw=np.array([0.0, 0.0]),
        cf_assumed=np.array([1.0, 0.0]),
        duration_h=np.array([0.0, 4.0]),
        rte=np.array([1.0, 1.0]),
    )
    cf = np.zeros((2, T))
    cf[0, 0:12] = 1.0
    load = np.zeros(T)
    load[12:16] = 10.0  # 4-hour night load fits a 4h battery
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(hours=T, mode="matching_target", excess_sale_fraction=0.0)
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1.0)
    assert r.status == "Optimal"
    assert r.build_energy_mwh.size == 0  # no split columns
    assert r.build_mw[1] > 0.0  # battery built to bridge


# --- hydro monthly budget (ADR 0008) ---------------------------------------


def test_hydro_monthly_budget_caps_january() -> None:
    """January hydro generation is capped at ERCOT's budget; February is free.

    Full 8760 solve. ERCOT's real budget (Jan 120 GWh, Feb 110 GWh) is loaded
    from data/hydro/monthly_budgets.csv. January load (1000 MW flat = 744 GWh)
    far exceeds the 120 GWh budget, so the January constraint binds at exactly
    120,000 MWh. February load (50 MW flat = 33.6 GWh) is below its budget, so
    February hydro serves all of it, unconstrained by the 110 GWh cap.
    """
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
    cf = np.ones((1, T))  # hydro available every hour; only the budget limits it
    load = np.zeros(T)
    jan = slice(0, 31 * 24)  # 0..743
    feb = slice(31 * 24, (31 + 28) * 24)  # 744..1415
    load[jan] = 1000.0  # 744 GWh >> 120 GWh budget -> budget binds
    load[feb] = 50.0  # 33.6 GWh < 110 GWh budget -> unconstrained
    lmp = np.full(T, 40.0)
    # Mode B (least cost) so hydro (vom 25 < lmp 40) serves load but never
    # over-generates: February gen is pinned to load, not smeared up to its budget.
    cfg = PortfolioConfig(
        iso="ERCOT", hours=T, mode="matching_target", excess_sale_fraction=0.0
    )
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=0.0)
    assert r.status == "Optimal"
    jan_gen = r.gen[0, jan].sum()
    feb_gen = r.gen[0, feb].sum()
    assert np.isclose(jan_gen, 120_000.0, rtol=1e-3)  # capped at January budget
    assert np.isclose(feb_gen, 33_600.0, rtol=1e-3)  # = all Feb load, below cap
    assert feb_gen < 110_000.0  # February budget not binding


def test_hydro_budget_skipped_for_sample_iso() -> None:
    """SAMPLE ISO has no budget entry, so the constraint is skipped entirely.

    With no budget the flagged hydro can serve the whole (small) load; if the
    constraint were wrongly applied with a NaN/zero budget the solve would break.
    """
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
    load = np.full(T, 10.0)
    lmp = np.full(T, 40.0)
    cfg = PortfolioConfig(
        iso="SAMPLE", hours=T, mode="premium_cap", excess_sale_fraction=0.0
    )
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1e9)
    assert r.status == "Optimal"
    # No monthly cap: hydro matches the full load, no January ceiling.
    assert np.isclose(r.matching_pct, 1.0, atol=1e-3)


# --- additionality accounting (ADR 0008) -----------------------------------


def _existing_only_system():
    """One cheap existing (PPA) resource, flat load, grid dearer than the PPA."""
    T = 24
    res = ResourceArrays(
        names=["nuclear_existing"],
        is_storage=np.array([False]),
        fixed_mwyr=np.array([0.0]),  # PPA: no fixed cost
        vom=np.array([20.0]),  # going-forward + EAC premium
        cap_max_mw=np.array([1e6]),
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([1.0]),
        duration_h=np.array([0.0]),
        rte=np.array([1.0]),
        is_existing=np.array([True]),
    )
    cf = np.ones((1, T))
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)  # grid dearer than the existing PPA
    return res, load, lmp, cf, T


def test_additionality_excludes_existing_from_matching() -> None:
    """Toggling additionality_only drops matching when existing gen > 0.

    Mode B, no matching floor (target 0): least cost serves all load with the
    cheap existing PPA in both cases. With the toggle OFF that gen counts as
    matched (100%); with it ON the same existing generation is excluded, so the
    reported matching drops to 0% even though the physical dispatch is unchanged.
    """
    res, load, lmp, cf, T = _existing_only_system()
    base = PortfolioConfig(hours=T, mode="matching_target", excess_sale_fraction=0.0)

    r_off = build_and_solve(base, res, load, lmp, cf, setpoint=0.0)
    r_on = build_and_solve(
        base.with_overrides(additionality_only=True), res, load, lmp, cf, setpoint=0.0
    )

    assert r_off.status == r_on.status == "Optimal"
    existing_gen = r_off.gen[0].sum()
    assert existing_gen > 0.0  # existing PPA actually generates
    assert np.isclose(r_off.matching_pct, 1.0, atol=1e-3)  # counts when off
    assert r_on.matching_pct < r_off.matching_pct - 0.5  # excluded when on
    assert np.isclose(r_on.matching_pct, 0.0, atol=1e-3)
    # Off-path physical dispatch: existing PPA serves all load (100 MW × 24 h).
    assert np.isclose(existing_gen, 2400.0, rtol=1e-3)
    # Same physical dispatch on both paths — only the metric differs.
    assert np.isclose(r_on.gen[0].sum(), existing_gen, rtol=1e-3)


# --- residual carbon reporting (ADR 0007) ----------------------------------


def test_residual_co2_reporting() -> None:
    """residual_co2_tons = grid_buy_mwh × marginal rate (0.4 tCO₂/MWh here).

    Solar available only 8/24 hours with flat 100 MW load leaves 16 h × 100 MWh =
    1600 MWh bought from the grid; at 0.4 tCO₂/MWh that is 640 tCO₂.
    """
    T = 24
    res = ResourceArrays(
        names=["solar"],
        is_storage=np.array([False]),
        fixed_mwyr=np.array([1000.0]),
        vom=np.array([0.0]),
        cap_max_mw=np.array([1e6]),
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([0.33]),
        duration_h=np.array([0.0]),
        rte=np.array([1.0]),
    )
    cf = np.zeros((1, T))
    cf[0, 8:16] = 1.0
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(
        hours=T,
        mode="premium_cap",
        excess_sale_fraction=1.0,
        marginal_co2_ton_per_mwh=0.4,
    )
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1e6)
    assert r.status == "Optimal"
    assert np.isclose(r.grid_buy_mwh, 1600.0, atol=1.0)
    assert np.isclose(r.residual_co2_tons, r.grid_buy_mwh * 0.4, rtol=1e-9)
    assert np.isclose(r.residual_co2_tons, 640.0, atol=1.0)


def test_residual_co2_zero_by_default() -> None:
    """Default marginal rate 0 -> residual_co2_tons is exactly 0 (feature off)."""
    T = 24
    res = ResourceArrays(
        names=["solar"],
        is_storage=np.array([False]),
        fixed_mwyr=np.array([1000.0]),
        vom=np.array([0.0]),
        cap_max_mw=np.array([1e6]),
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([0.33]),
        duration_h=np.array([0.0]),
        rte=np.array([1.0]),
    )
    cf = np.zeros((1, T))
    cf[0, 8:16] = 1.0
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(hours=T, mode="premium_cap")
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1e6)
    assert r.residual_co2_tons == 0.0
