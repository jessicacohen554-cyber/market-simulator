"""Storage charge-provenance policy tests (ADR 0017).

Trivial-case-first (24 hours, hand-built resources): the default
``arbitrage`` policy must reproduce the historical merchant behavior
(grid charging / discharge export when profitable), and
``excess_clean_only`` must close that channel while leaving genuine
clean-surplus shifting intact.
"""

import numpy as np
import pytest

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.lp import build_and_solve
from lce_portfolio.resources import ResourceArrays

from conftest import daytime_solar_cf, solar_plus_battery


def battery_only(fixed_batt: float = 10.0) -> ResourceArrays:
    """A single 4-hour battery and no generation at all."""
    return ResourceArrays(
        names=["battery"],
        is_storage=np.array([True]),
        fixed_mwyr=np.array([fixed_batt]),
        vom=np.array([0.0]),
        cap_max_mw=np.array([1e6]),
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([0.0]),
        duration_h=np.array([4.0]),
        rte=np.array([0.9]),
    )


def spread_lmp(T: int = 24) -> np.ndarray:
    """LMP with a fat daily spread: $5 overnight, $500 in the evening peak."""
    lmp = np.full(T, 5.0)
    lmp[17:21] = 500.0
    return lmp


NIGHT = np.array([h not in range(8, 16) for h in range(24)])  # solar-off hours


def test_arbitrage_default_grid_charges_at_night() -> None:
    """Default policy: with a fat LMP spread, the battery grid-charges.

    Solar (day-only) leaves annual matching headroom in a target-0 Mode B
    solve, so the cost-minimizing LP buys cheap overnight grid energy into
    the battery and discharges it into the $500 evening peak — merchant
    arbitrage. Charging in a zero-CF hour is unambiguously grid energy.
    """
    T = 24
    res = solar_plus_battery(fixed_batt=100.0)
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    cfg = PortfolioConfig(hours=T, mode="matching_target")
    r = build_and_solve(cfg, res, load, np.copy(spread_lmp(T)), cf, setpoint=0.0)
    assert r.status == "Optimal"
    chg_t = r.storage_charge.sum(axis=0)
    assert chg_t[NIGHT].sum() > 1.0  # merchant grid charging happens


def test_excess_clean_only_forbids_grid_charging() -> None:
    """excess_clean_only closes the merchant channel in the same setup."""
    T = 24
    res = solar_plus_battery(fixed_batt=100.0)
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    cfg = PortfolioConfig(
        hours=T, mode="matching_target", storage_charge_policy="excess_clean_only"
    )
    r = build_and_solve(cfg, res, load, np.copy(spread_lmp(T)), cf, setpoint=0.0)
    assert r.status == "Optimal"
    chg_t = r.storage_charge.sum(axis=0)
    gen_t = r.gen.sum(axis=0)
    assert chg_t[NIGHT].sum() <= 1e-3  # no solar -> no charging
    assert np.all(chg_t + r.excess <= gen_t + 1e-2)  # provenance rows hold


def test_excess_clean_only_no_generation_idles_storage() -> None:
    """Degenerate fleet (battery only, no clean gen): storage stays idle.

    With zero portfolio generation the provenance rows pin both charging and
    excess sales to zero, whatever the LMP spread.
    """
    T = 24
    res = battery_only()
    cf = np.zeros((1, T))
    load = np.full(T, 100.0)
    cfg = PortfolioConfig(
        hours=T, mode="matching_target", storage_charge_policy="excess_clean_only"
    )
    r = build_and_solve(cfg, res, load, np.copy(spread_lmp(T)), cf, setpoint=0.0)
    assert r.status == "Optimal"
    assert r.storage_charge.sum() <= 1e-3
    assert r.excess.sum() <= 1e-3  # nothing may be re-sold either


def test_excess_clean_only_charge_bounded_by_clean_gen() -> None:
    """excess_clean_only still allows clean-surplus shifting, per hour.

    Daytime solar with a battery: matching must still beat the solar-only
    8/24 ceiling (storage shifts genuine surplus), while every hour respects
    chg + excess <= clean gen — in particular, zero charging at night.
    """
    T = 24
    res = solar_plus_battery()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(
        hours=T,
        mode="premium_cap",
        excess_sale_fraction=1.0,
        storage_charge_policy="excess_clean_only",
    )
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1e6)
    assert r.status == "Optimal"
    assert r.matching_pct > 8.0 / 24.0 + 1e-3  # storage still shifts surplus
    gen_t = r.gen.sum(axis=0)
    chg_t = r.storage_charge.sum(axis=0)
    assert np.all(chg_t + r.excess <= gen_t + 1e-2)  # provenance rows hold
    night = np.ones(T, dtype=bool)
    night[list(range(8, 16))] = False
    assert chg_t[night].max() <= 1e-3  # no charging when solar is off
    # discharge serves load only: buy_t <= load_t - dis_t via the balance
    dis_t = r.storage_discharge.sum(axis=0)
    assert np.all(r.grid_buy + dis_t <= load + 1e-2)


def test_arbitrage_and_excess_only_agree_without_grid_incentive() -> None:
    """With flat LMP there is no arbitrage rent: both policies match equally.

    Guards against the provenance rows accidentally cutting off legitimate
    matching value rather than just the merchant channel.
    """
    T = 24
    res = solar_plus_battery()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    base = PortfolioConfig(hours=T, mode="premium_cap", excess_sale_fraction=1.0)
    strict = base.with_overrides(storage_charge_policy="excess_clean_only")
    r_base = build_and_solve(base, res, load, lmp, cf, setpoint=1e6)
    r_strict = build_and_solve(strict, res, load, lmp, cf, setpoint=1e6)
    assert r_base.status == r_strict.status == "Optimal"
    assert np.isclose(r_base.matching_pct, r_strict.matching_pct, atol=1e-3)


def test_energy_balance_holds_under_policy() -> None:
    """The per-hour energy balance is untouched by the provenance rows."""
    T = 24
    res = solar_plus_battery()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.copy(spread_lmp(T))
    cfg = PortfolioConfig(
        hours=T, mode="premium_cap", storage_charge_policy="excess_clean_only"
    )
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1e6)
    supply = (
        r.gen.sum(axis=0)
        + r.storage_discharge.sum(axis=0)
        - r.storage_charge.sum(axis=0)
        + r.grid_buy
        - r.excess
    )
    assert np.allclose(supply, load, atol=1e-2)


def test_invalid_policy_rejected() -> None:
    """Config validation: unknown policy values raise at construction."""
    with pytest.raises(ValueError, match="storage_charge_policy"):
        PortfolioConfig(storage_charge_policy="merchant")
