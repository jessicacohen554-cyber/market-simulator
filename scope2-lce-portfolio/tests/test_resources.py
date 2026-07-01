"""Tests for the resource catalog, cost resolution, caps, and hydro budgets."""

import numpy as np
import pytest

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.lp import build_and_solve
from lce_portfolio.resources import (
    capital_recovery_factor,
    load_hydro_budgets,
    load_resource_arrays,
)


def test_minimal_set_and_storage_mask() -> None:
    """Default config selects the three active_minimal resources."""
    res = load_resource_arrays(PortfolioConfig())
    assert res.names == ["solar_pv", "onshore_wind", "battery_4h"]
    assert res.n_res == 3
    # only the battery is storage; none are split
    assert res.is_storage.tolist() == [False, False, True]
    assert res.storage_idx.tolist() == [2]
    assert res.is_split.tolist() == [False, False, False]


def test_crf_math() -> None:
    """CRF matches the closed form and annualizes a synthetic capex row.

    capex 1000 $/kW, fom 20 $/kW-yr, r=0.07, n=30 -> CRF ~ 0.08059,
    fixed ~ 100,586 $/MW-yr.
    """
    crf = capital_recovery_factor(0.07, 30)
    assert np.isclose(crf, 0.08059, atol=1e-4)
    fixed = 1000.0 * 1000.0 * crf + 20.0 * 1000.0
    assert np.isclose(fixed, 100586.0, rtol=1e-2)
    # rate == 0 degenerates to straight-line 1/n
    assert np.isclose(capital_recovery_factor(0.0, 25), 1.0 / 25)


def test_capex_fixed_annualization() -> None:
    """A capex_fixed generation row is annualized capex*CRF + fom (ADR 0004)."""
    res = load_resource_arrays(PortfolioConfig(lcoe_sensitivity="mid"))
    solar = res.names.index("solar_pv")
    crf = capital_recovery_factor(0.07, 30)
    expected = 1100.0 * 1000.0 * crf + 16.0 * 1000.0  # mid capex, fom, life 30
    assert np.isclose(res.fixed_mwyr[solar], expected, rtol=1e-6)


def test_sensitivity_monotone() -> None:
    """low <= mid <= high fixed cost for a generation resource."""
    lo = load_resource_arrays(PortfolioConfig(lcoe_sensitivity="low"))
    mid = load_resource_arrays(PortfolioConfig(lcoe_sensitivity="mid"))
    hi = load_resource_arrays(PortfolioConfig(lcoe_sensitivity="high"))
    i = lo.names.index("onshore_wind")
    assert lo.fixed_mwyr[i] <= mid.fixed_mwyr[i] <= hi.fixed_mwyr[i]


def test_cap_and_floor_override() -> None:
    """Config caps/floors override the table defaults."""
    cfg = PortfolioConfig(
        resource_caps_mw={"solar_pv": 250.0},
        resource_floors_mw={"onshore_wind": 40.0},
    )
    res = load_resource_arrays(cfg)
    assert res.cap_max_mw[res.names.index("solar_pv")] == 250.0
    assert res.cap_min_mw[res.names.index("onshore_wind")] == 40.0


def test_active_resources_selection() -> None:
    """Explicit active_resources selects exactly those rows."""
    res = load_resource_arrays(PortfolioConfig(active_resources=("nuclear_new",)))
    assert res.names == ["nuclear_new"]


# --- existing resources (ppa_mwh, ADR 0008) --------------------------------


def test_ppa_mwh_mapping() -> None:
    """Existing resource: fixed_mwyr=0, vom = cost + eac_premium (table)."""
    res = load_resource_arrays(
        PortfolioConfig(active_resources=("nuclear_existing",), lcoe_sensitivity="mid")
    )
    i = res.names.index("nuclear_existing")
    assert res.fixed_mwyr[i] == 0.0
    assert np.isclose(res.vom[i], 30.0 + 4.0)  # mid cost 30 + table premium 4


def test_ppa_eac_premium_override() -> None:
    """config.eac_premium_mwh overrides the table premium column."""
    res = load_resource_arrays(
        PortfolioConfig(
            active_resources=("nuclear_existing",),
            lcoe_sensitivity="mid",
            eac_premium_mwh={"nuclear_existing": 10.0},
        )
    )
    i = res.names.index("nuclear_existing")
    assert np.isclose(res.vom[i], 30.0 + 10.0)


# --- split storage (LDES / hydrogen, ADR 0006) -----------------------------


def test_split_storage_parsing() -> None:
    """ldes/hydrogen parse as split storage with both cost components + bounds."""
    res = load_resource_arrays(PortfolioConfig(active_resources=("ldes", "hydrogen")))
    for name in ("ldes", "hydrogen"):
        i = res.names.index(name)
        assert res.is_split[i]
        assert res.is_storage[i]
        assert res.fixed_mwyr[i] > 0.0  # annualized power capex
        assert res.cost_energy_mwhyr[i] > 0.0  # annualized energy capex
        assert res.duration_min_h[i] > 0.0
        assert res.duration_max_h[i] > res.duration_min_h[i]


def test_split_storage_lp_guard() -> None:
    """Activating a split resource makes the LP raise NotImplementedError."""
    res = load_resource_arrays(PortfolioConfig(active_resources=("ldes",)))
    T = 24
    load = np.full(T, 100.0)
    lmp = np.full(T, 40.0)
    cf = np.zeros((res.n_res, T))
    cfg = PortfolioConfig(hours=T, active_resources=("ldes",))
    with pytest.raises(NotImplementedError):
        build_and_solve(cfg, res, load, lmp, cf, setpoint=10.0)


# --- per-ISO caps & eligibility (ADR 0009) ---------------------------------


def test_caps_eligibility_offshore_absent_for_ercot() -> None:
    """ERCOT has no offshore row, so offshore is ineligible even if requested."""
    res = load_resource_arrays(
        PortfolioConfig(iso="ERCOT", active_resources=("onshore_wind", "offshore_wind"))
    )
    assert "onshore_wind" in res.names
    assert "offshore_wind" not in res.names  # excluded by ERCOT caps table


def test_caps_precedence_chain() -> None:
    """config cap > caps-table cap > table default, per ADR 0009."""
    # Table caps-table value for ERCOT nuclear_existing is 2400.
    res = load_resource_arrays(
        PortfolioConfig(iso="ERCOT", active_resources=("nuclear_existing",))
    )
    assert res.cap_max_mw[0] == 2400.0
    # config override wins over the caps table.
    res2 = load_resource_arrays(
        PortfolioConfig(
            iso="ERCOT",
            active_resources=("nuclear_existing",),
            resource_caps_mw={"nuclear_existing": 999.0},
        )
    )
    assert res2.cap_max_mw[0] == 999.0


def test_caps_sample_iso_falls_back_to_default() -> None:
    """SAMPLE is absent from the caps table -> table cap_max_default_mw applies."""
    res = load_resource_arrays(
        PortfolioConfig(iso="SAMPLE", active_resources=("offshore_wind",))
    )
    # offshore is available (no ISO restriction) at its table default.
    assert res.names == ["offshore_wind"]
    assert res.cap_max_mw[0] == 1000000.0


def test_config_cap_makes_capped_out_resource_eligible() -> None:
    """A config cap admits a resource the ISO caps table would exclude."""
    res = load_resource_arrays(
        PortfolioConfig(
            iso="ERCOT",
            active_resources=("offshore_wind",),
            resource_caps_mw={"offshore_wind": 5000.0},
        )
    )
    assert res.names == ["offshore_wind"]
    assert res.cap_max_mw[0] == 5000.0


# --- hydro monthly budgets -------------------------------------------------


def test_hydro_budgets_loader() -> None:
    """12 positive monthly budgets for a known ISO; unknown ISO raises."""
    budget = load_hydro_budgets("CAISO")
    assert budget.shape == (12,)
    assert (budget > 0).all()
    with pytest.raises(ValueError):
        load_hydro_budgets("NOT_AN_ISO")


def test_all_isos_have_hydro_budgets() -> None:
    """Every ISO in the caps table with a hydro row has a complete budget."""
    for iso in ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"):
        assert load_hydro_budgets(iso).shape == (12,)


def test_floor_exceeding_cap_errors() -> None:
    """A floor above the resolved cap is an input error, not a silent LP bound flip."""
    cfg = PortfolioConfig(
        resource_caps_mw={"solar_pv": 10.0},
        resource_floors_mw={"solar_pv": 50.0},
    )
    with pytest.raises(ValueError, match="floor .* exceeds cap"):
        load_resource_arrays(cfg)


def test_missing_cost_column_errors(tmp_path) -> None:
    """A missing/blank required cost column errors instead of yielding a free resource."""
    table = tmp_path / "costs.csv"
    # capex_kw_mid column absent entirely -> must raise, not default to 0.
    table.write_text(
        "resource,category,cost_basis,fom_kw_yr,life_yr,cf_assumed,vom,"
        "duration_h,rte,cap_max_default_mw,active_minimal,notes\n"
        "solar_pv,generation,capex_fixed,15,30,0.26,0,0,0,1000,1,test row\n"
    )
    with pytest.raises(ValueError, match="required cost column"):
        load_resource_arrays(PortfolioConfig(), cost_table=table)
