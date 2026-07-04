"""Divert-and-backfill diagnostic + ``excess_headroom_only`` policy (ADR 0018).

Trivial-case-first (24 hours, hand-built resources): the static ADR 0017
``excess_clean_only`` rows admit a "divert-and-backfill" residual — storage
charging from clean generation in an hour the grid also serves — which the
``divert_backfill_mwh`` diagnostic exposes and the ADR 0018
``excess_headroom_only`` cut loop eliminates, without disturbing genuine
clean-surplus shifting or the two pre-existing policies.
"""

import numpy as np
import pytest

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.lp import build_and_solve, solve_with_charge_policy
from lce_portfolio.resources import ResourceArrays

from conftest import daytime_solar_cf, solar_plus_battery

TOL = 1e-3  # matches lp.EXCESS_HEADROOM_TOL_MWH


def cheap_solar_plus_battery() -> ResourceArrays:
    """Low-fixed-cost solar + 4h battery so shifting the peak is worthwhile.

    The ATB-scale fixtures in ``conftest`` price building so high that a 24h
    toy never builds storage to chase a price spike; these cheap costs make the
    shift economic, which is what surfaces divert-and-backfill.
    """
    return ResourceArrays(
        names=["solar", "battery"],
        is_storage=np.array([False, True]),
        fixed_mwyr=np.array([50.0, 50.0]),
        vom=np.array([0.0, 0.0]),
        cap_max_mw=np.array([1e6, 1e6]),
        cap_min_mw=np.array([0.0, 0.0]),
        cf_assumed=np.array([0.33, 0.0]),
        duration_h=np.array([0.0, 4.0]),
        rte=np.array([1.0, 0.9]),
    )


def divert_case():
    """Mode-B setup that provokes divert-and-backfill under excess_clean_only.

    Daytime solar (hours 8–15) can serve daytime load directly, but a fat LMP
    spread ($5 base, $500 in the evening peak) makes it cheaper to divert that
    solar into the battery — backfilling the cheap daytime load with grid buys
    — and discharge into the $500 peak. Grid charging is forbidden by the
    provenance rows, so the ONLY way to fill the battery for the peak is to
    divert clean generation, which coincides with a grid purchase in that hour.
    Returns ``(resources, cf, load, lmp)``.
    """
    T = 24
    res = cheap_solar_plus_battery()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.full(T, 5.0)
    lmp[17:21] = 500.0  # evening peak
    return res, cf, load, lmp


def test_excess_clean_only_exhibits_divert_backfill() -> None:
    """(a) Under excess_clean_only the divert diagnostic is strictly positive."""
    res, cf, load, lmp = divert_case()
    cfg = PortfolioConfig(
        hours=24, mode="matching_target", storage_charge_policy="excess_clean_only"
    )
    r = solve_with_charge_policy(cfg, res, load, lmp, cf, setpoint=0.0)
    assert r.status == "Optimal"
    assert r.divert_backfill_mwh > 1.0  # clean charging coincides with grid buys
    chg_t = r.storage_charge.sum(axis=0)
    coincident = (chg_t > TOL) & (r.grid_buy > TOL)
    assert coincident.any()  # at least one divert-and-backfill hour


def test_excess_headroom_only_eliminates_divert_backfill() -> None:
    """(b) The same case under excess_headroom_only drives the residual to ~0."""
    res, cf, load, lmp = divert_case()
    cfg = PortfolioConfig(
        hours=24, mode="matching_target", storage_charge_policy="excess_headroom_only"
    )
    r = solve_with_charge_policy(cfg, res, load, lmp, cf, setpoint=0.0)
    assert r.status == "Optimal"
    assert r.divert_backfill_mwh <= TOL  # cut loop removed the residual
    chg_t = r.storage_charge.sum(axis=0)
    # no hour charges storage while the grid also serves load in that hour
    assert not ((chg_t > TOL) & (r.grid_buy > TOL)).any()


def test_excess_headroom_only_preserves_surplus_shifting() -> None:
    """(c) Genuine clean-surplus shifting still beats the no-storage ceiling.

    Daytime solar overbuilds into true surplus (gen > load), which the battery
    stores and shifts into the night. Charging there coincides with no grid
    purchase, so the cut loop leaves it intact and matching clears well above
    the solar-only 8/24 ceiling.
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
        storage_charge_policy="excess_headroom_only",
    )
    r = solve_with_charge_policy(cfg, res, load, lmp, cf, setpoint=1e6)
    assert r.status == "Optimal"
    assert r.matching_pct > 8.0 / 24.0 + 1e-3  # storage still shifts real surplus
    assert r.divert_backfill_mwh <= TOL  # surplus charging never coincides with buys


def test_excess_headroom_only_energy_balance_holds() -> None:
    """(d) The per-hour energy balance survives the cut loop untouched."""
    res, cf, load, lmp = divert_case()
    cfg = PortfolioConfig(
        hours=24, mode="matching_target", storage_charge_policy="excess_headroom_only"
    )
    r = solve_with_charge_policy(cfg, res, load, lmp, cf, setpoint=0.0)
    supply = (
        r.gen.sum(axis=0)
        + r.storage_discharge.sum(axis=0)
        - r.storage_charge.sum(axis=0)
        + r.grid_buy
        - r.excess
    )
    assert np.allclose(supply, load, atol=1e-2)


def test_invalid_policy_rejected() -> None:
    """(e) An unknown policy value raises at config construction."""
    with pytest.raises(ValueError, match="storage_charge_policy"):
        PortfolioConfig(storage_charge_policy="headroom")
    # the new value is accepted
    PortfolioConfig(storage_charge_policy="excess_headroom_only")


@pytest.mark.parametrize("policy", ["arbitrage", "excess_clean_only"])
def test_wrapper_unchanged_for_other_policies(policy: str) -> None:
    """(f) For non-headroom policies the wrapper adds no rows or cuts.

    ``solve_with_charge_policy`` must return exactly what a bare
    ``build_and_solve`` returns for ``arbitrage``/``excess_clean_only`` — no
    provenance-row or cut-loop side effects leak into the unselected policies.
    """
    res, cf, load, lmp = divert_case()
    cfg = PortfolioConfig(
        hours=24, mode="matching_target", storage_charge_policy=policy
    )
    direct = build_and_solve(cfg, res, load, lmp, cf, setpoint=0.0)
    wrapped = solve_with_charge_policy(cfg, res, load, lmp, cf, setpoint=0.0)
    assert direct.status == wrapped.status == "Optimal"
    assert np.isclose(direct.matching_pct, wrapped.matching_pct, atol=1e-9)
    assert np.isclose(direct.net_cost, wrapped.net_cost, atol=1e-6)
    assert np.isclose(
        direct.divert_backfill_mwh, wrapped.divert_backfill_mwh, atol=1e-9
    )
    assert np.allclose(direct.build_mw, wrapped.build_mw, atol=1e-6)
