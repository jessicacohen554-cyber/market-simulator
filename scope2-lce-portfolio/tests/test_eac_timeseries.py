"""Tests for annual EAC time series, lmp_ppa attribute pricing, storage tolling,
the new attribute/uprate/RoR/12h resources, and the breakeven EAC helper.

Covers ADR 0020 (EAC series + market-indexed attribute basis), ADR 0021 (the
breakeven derivation), and ADR 0022 (storage tolling). Trivial-first: series
resolution and cost mapping are checked directly, the "premium == EAC" invariant
is checked with a 24-hour single-resource LP, and the breakeven helper is checked
as a pure function.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.lp import build_and_solve
from lce_portfolio.profiles import build_cf_matrix
from lce_portfolio.resources import (
    ResourceArrays,
    load_eac_prices,
    load_resource_arrays,
    resolve_eac_series,
)

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from derive_eac_breakeven import (  # noqa: E402
    CAPACITY_PRICE_KW_YR,
    breakeven_eac,
    credit_45q_per_mwh,
)


# --- EAC series loading + resolution ----------------------------------------


def test_series_resolution_exact_forwardfill_earliest_absent() -> None:
    """Exact year wins; else latest prior; else earliest; None when absent."""
    series = {"x": [(2030, 5.0), (2040, 4.0), (2050, 3.0)]}
    assert resolve_eac_series("x", 2040, series) == 4.0  # exact
    assert resolve_eac_series("x", 2045, series) == 4.0  # forward-fill from 2040
    assert resolve_eac_series("x", 2025, series) == 5.0  # before first -> earliest
    assert resolve_eac_series("x", 2060, series) == 3.0  # after last -> latest prior
    assert resolve_eac_series("missing", 2030, series) is None


def test_packaged_series_has_expected_resources() -> None:
    """The shipped eac_prices.csv covers every attribute-basis resource."""
    series = load_eac_prices()
    for name in (
        "nuclear_existing",
        "hydro_existing",
        "hydro_ror",
        "nuclear_uprate",
        "onshore_wind_ppa",
        "solar_pv_ppa",
        "offshore_wind_ppa",
        "gas_cc_ccs_new",
        "gas_cc_ccs_retrofit",
    ):
        assert name in series and series[name]


def test_series_rejects_negative(tmp_path) -> None:
    """A negative eac_mwh in the series table is a data error."""
    bad = tmp_path / "eac.csv"
    bad.write_text("resource,year,eac_mwh,notes\nx,2030,-1,t\n")
    with pytest.raises(ValueError, match="non-negative"):
        load_eac_prices(bad)


def test_series_rejects_duplicate(tmp_path) -> None:
    """A duplicate (resource, year) row raises rather than last-wins."""
    bad = tmp_path / "eac.csv"
    bad.write_text("resource,year,eac_mwh,notes\nx,2030,5,a\nx,2030,6,b\n")
    with pytest.raises(ValueError, match="duplicate"):
        load_eac_prices(bad)


# --- lmp_ppa market-indexed attribute resources -----------------------------


def test_lmp_ppa_vom_is_eac_and_indexed() -> None:
    """nuclear_uprate loads as lmp_ppa: fixed=0, vom=EAC(2030)=6, lmp_indexed."""
    cfg = PortfolioConfig(iso="SAMPLE", year=2030, active_resources=("nuclear_uprate",))
    ra = load_resource_arrays(cfg)
    assert ra.fixed_mwyr[0] == 0.0
    assert ra.vom[0] == pytest.approx(6.0)
    assert bool(ra.lmp_indexed[0])
    assert not ra.is_existing[0]  # lmp_ppa is additional, not the ppa_mwh carve-out


def test_series_year_resolution_flows_into_resource() -> None:
    """A 2050 run picks the 2050 series value (onshore_wind_ppa 5->3)."""
    cfg30 = PortfolioConfig(
        iso="SAMPLE", year=2030, active_resources=("onshore_wind_ppa",)
    )
    cfg50 = PortfolioConfig(
        iso="SAMPLE", year=2050, active_resources=("onshore_wind_ppa",)
    )
    assert load_resource_arrays(cfg30).vom[0] == pytest.approx(5.0)
    assert load_resource_arrays(cfg50).vom[0] == pytest.approx(3.0)


def test_config_override_beats_series() -> None:
    """config.eac_premium_mwh wins over the annual series."""
    cfg = PortfolioConfig(
        iso="SAMPLE",
        year=2030,
        active_resources=("nuclear_uprate",),
        eac_premium_mwh={"nuclear_uprate": 12.0},
    )
    assert load_resource_arrays(cfg).vom[0] == pytest.approx(12.0)


def test_empty_series_file_falls_back_to_table_column() -> None:
    """eac_prices_file='' disables the series; lmp_ppa row w/ blank column -> 0."""
    cfg = PortfolioConfig(
        iso="SAMPLE",
        year=2030,
        active_resources=("nuclear_uprate",),
        eac_prices_file="",
    )
    assert load_resource_arrays(cfg).vom[0] == 0.0


def test_override_key_must_match_attribute_resource() -> None:
    """An eac_premium_mwh key matching no attribute-basis resource raises (DL-9)."""
    cfg = PortfolioConfig(
        iso="SAMPLE", active_resources=("solar_pv",), eac_premium_mwh={"solar_pv": 5.0}
    )
    with pytest.raises(ValueError, match="do not match any attribute-basis"):
        load_resource_arrays(cfg)


# --- LP: premium of an lmp-indexed resource equals its EAC -------------------


def test_lmp_indexed_premium_equals_eac() -> None:
    """A firm lmp_ppa resource serving all load yields premium == EAC, flat.

    Energy is bought at the hourly LMP (a wash vs BAU) and the only net cost is
    the EAC, regardless of the (varying) price shape — the ADR 0020 invariant.
    """
    T = 24
    eac = 7.0
    res = ResourceArrays(
        names=["ccs_like"],
        is_storage=np.array([False]),
        fixed_mwyr=np.array([0.0]),
        vom=np.array([eac]),
        cap_max_mw=np.array([1e6]),
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([1.0]),
        duration_h=np.array([0.0]),
        rte=np.array([1.0]),
        lmp_indexed=np.array([True]),
    )
    cfg = PortfolioConfig(hours=T, mode="premium_cap")
    load = np.full(T, 10.0)
    lmp = 20.0 + 30.0 * np.sin(np.arange(T) / 24.0 * 2 * np.pi)  # varying, positive
    cf = np.ones((1, T))
    r = build_and_solve(cfg, res, load, lmp, cf, 1e9)
    assert r.status == "Optimal"
    assert r.matching_pct == pytest.approx(1.0, abs=1e-4)
    # abs=1e-3: the crossover-off IPM (ADR 0003) leaves sub-1e-4 MWh residuals,
    # so the premium lands on EAC only to interior-point tolerance.
    assert r.premium == pytest.approx(eac, abs=1e-3)


def test_zero_eac_lmp_indexed_is_zero_premium() -> None:
    """A zero-EAC firm clean resource is free clean energy: premium == 0."""
    T = 24
    res = ResourceArrays(
        names=["free_clean"],
        is_storage=np.array([False]),
        fixed_mwyr=np.array([0.0]),
        vom=np.array([0.0]),
        cap_max_mw=np.array([1e6]),
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([1.0]),
        duration_h=np.array([0.0]),
        rte=np.array([1.0]),
        lmp_indexed=np.array([True]),
    )
    cfg = PortfolioConfig(hours=T, mode="premium_cap")
    load = np.full(T, 10.0)
    lmp = np.full(T, 45.0)
    r = build_and_solve(cfg, res, load, lmp, cf=np.ones((1, T)), setpoint=1e9)
    assert r.premium == pytest.approx(0.0, abs=1e-6)


# --- storage tolling (ADR 0022) ---------------------------------------------


def test_tolling_overrides_fixed_cost() -> None:
    """storage_pricing='tolling' uses tolling_kw_yr*1000 in place of capex CRF."""
    cfg = PortfolioConfig(
        iso="SAMPLE", active_resources=("battery_4h",), storage_pricing="tolling"
    )
    ra = load_resource_arrays(cfg)
    assert ra.fixed_mwyr[0] == pytest.approx(195.0 * 1000.0)  # mid tolling $/kW-yr


def test_tolling_capex_differ() -> None:
    """The tolling and capex bases give different fixed_mwyr for the same row."""
    capex = load_resource_arrays(
        PortfolioConfig(iso="SAMPLE", active_resources=("battery_8h",))
    ).fixed_mwyr[0]
    toll = load_resource_arrays(
        PortfolioConfig(
            iso="SAMPLE", active_resources=("battery_8h",), storage_pricing="tolling"
        )
    ).fixed_mwyr[0]
    assert toll == pytest.approx(310.0 * 1000.0)
    assert toll != pytest.approx(capex)


def test_tolling_requires_price(tmp_path) -> None:
    """A storage row with no tolling price under tolling mode raises."""
    header = (
        "resource,category,cost_basis,capex_kw_mid,fom_kw_yr,life_yr,cf_assumed,"
        "duration_h,rte,cap_max_default_mw,active_minimal,vom,notes\n"
    )
    row = "bat,storage,capex_fixed,1000,20,15,0,4,0.86,10000,1,0,t\n"
    table = tmp_path / "costs.csv"
    table.write_text(header + row)
    cfg = PortfolioConfig(
        iso="SAMPLE", active_resources=("bat",), storage_pricing="tolling"
    )
    with pytest.raises(ValueError, match="storage_pricing='tolling' but no"):
        load_resource_arrays(cfg, cost_table=table)


def test_storage_pricing_validation() -> None:
    """An invalid storage_pricing is rejected at config construction."""
    with pytest.raises(ValueError, match="storage_pricing must be"):
        PortfolioConfig(storage_pricing="bogus")


# --- new resources load + CF aliasing ---------------------------------------


def test_new_resources_load() -> None:
    """nuclear_uprate, hydro_ror, battery_12h all load for SAMPLE."""
    cfg = PortfolioConfig(
        iso="SAMPLE",
        active_resources=("nuclear_uprate", "hydro_ror", "battery_12h"),
    )
    ra = load_resource_arrays(cfg)
    assert set(ra.names) == {"nuclear_uprate", "hydro_ror", "battery_12h"}
    b12 = ra.names.index("battery_12h")
    assert ra.is_storage[b12] and ra.duration_h[b12] == pytest.approx(12.0)


def test_attribute_wind_reuses_base_shape() -> None:
    """onshore_wind_ppa gets the same synthetic CF shape as onshore_wind."""
    cfg = PortfolioConfig(
        iso="SAMPLE", active_resources=("onshore_wind", "onshore_wind_ppa")
    )
    ra = load_resource_arrays(cfg)
    cf = build_cf_matrix(ra, "SAMPLE", cfg.year)
    i = ra.names.index("onshore_wind")
    j = ra.names.index("onshore_wind_ppa")
    # Same cf_assumed target (0.42) and same shape alias -> identical rows.
    assert np.allclose(cf[i], cf[j])
    assert cf[j].mean() > 0.0  # not a flat/zero fallback


# --- breakeven EAC helper (ADR 0021) ----------------------------------------


def test_breakeven_positive_and_capacity_reduces_it() -> None:
    """A capacity-revenue offset lowers the breakeven EAC."""
    base = dict(
        capex_kw=2700.0,
        fom_kw_yr=62.0,
        cf=0.9,
        hurdle_rate=0.09,
        term_years=20.0,
        expected_lmp_mwh=40.0,
        vom_mwh=16.0,
        fuel_mwh=30.0,
    )
    no_cap = breakeven_eac(**base, capacity_kw_yr=0.0)
    with_cap = breakeven_eac(**base, capacity_kw_yr=100.0)
    assert no_cap > 0.0
    assert with_cap < no_cap


def test_breakeven_ercot_no_capacity_offset() -> None:
    """ERCOT is energy-only: its registry capacity price is zero."""
    assert CAPACITY_PRICE_KW_YR["ERCOT"] == 0.0
    assert CAPACITY_PRICE_KW_YR["PJM"] > 0.0


def test_breakeven_45q_offset_reduces_eac() -> None:
    """A §45Q credit (project revenue) lowers the buyer's breakeven EAC."""
    credit = credit_45q_per_mwh(
        capture_rate=0.95, heat_rate_mmbtu_mwh=7.9, price_45q_per_ton=85.0
    )
    assert credit > 0.0
    common = dict(
        capex_kw=2700.0,
        fom_kw_yr=62.0,
        cf=0.9,
        hurdle_rate=0.09,
        term_years=20.0,
        expected_lmp_mwh=40.0,
        vom_mwh=16.0,
        fuel_mwh=30.0,
    )
    assert breakeven_eac(**common, credit_45q_mwh=credit) < breakeven_eac(
        **common, credit_45q_mwh=0.0
    )


def test_breakeven_floors_at_zero() -> None:
    """Offsets exceeding the required all-in floor the EAC at zero, not negative."""
    eac = breakeven_eac(
        capex_kw=100.0,
        fom_kw_yr=1.0,
        cf=0.5,
        hurdle_rate=0.05,
        term_years=20.0,
        expected_lmp_mwh=500.0,  # huge LMP swamps the cost
    )
    assert eac == 0.0
