"""Tests for the gas CC + CCS resource (ADR 0012, PP-08).

Trivial-first coverage of: the net-VOM arithmetic (fuel + 45Q), the load-time
low-carbon admissibility threshold, delivered-gas-price resolution precedence
(config override > per-ISO table > loud error for a fuel-burning resource),
the grid/resource residual-CO2 split (reporting only — matching credit is NOT
discounted), retrofit-vs-new economics at the mid case, and an end-to-end tiny
sweep with CCS active. Custom catalog rows are written to ``tmp_path`` CSVs
following the ``test_resources.py`` pattern.
"""

from __future__ import annotations

import numpy as np
import pytest

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.lp import build_and_solve
from lce_portfolio.resources import (
    NG_CO2_TON_PER_MMBTU,
    ResourceArrays,
    load_gas_price,
    load_resource_arrays,
)
from lce_portfolio.sweep import run_sweep

_COST_HEADER = (
    "resource,category,cost_basis,capex_kw_mid,fom_kw_yr,life_yr,cf_assumed,vom,"
    "duration_h,rte,cap_max_default_mw,active_minimal,"
    "heat_rate_mmbtu_mwh,capture_rate,emission_rate_ton_mwh,notes\n"
)


def _write_cost_table(tmp_path, rows: list[str]):
    """Write a minimal mid-sensitivity cost table and return its path."""
    table = tmp_path / "costs.csv"
    table.write_text(_COST_HEADER + "".join(r + "\n" for r in rows))
    return table


def _write_gas_table(tmp_path, rows: list[str]):
    """Write a minimal gas-price table and return its path."""
    table = tmp_path / "gas.csv"
    table.write_text("iso,price_mmbtu,basis,notes\n" + "".join(r + "\n" for r in rows))
    return table


# A valid CCS row: capture 0.95, heat rate 8.0, residual 0.05*0.0531*8 = 0.02124.
_CCS_ROW = "ccs,generation,capex_fixed,2000,50,30,0.9,16,0,0,10000,0,8.0,0.95,0.02124,t"


# --- net-VOM arithmetic ------------------------------------------------------


def test_net_vom_hand_check(tmp_path) -> None:
    """Net VOM = vom_table + HR × gas − capture × (0.0531 × HR) × 45Q, exactly."""
    table = _write_cost_table(tmp_path, [_CCS_ROW])
    cfg = PortfolioConfig(
        active_resources=("ccs",), gas_price_mmbtu=4.0, ccs_45q_per_ton=85.0
    )
    ra = load_resource_arrays(cfg, cost_table=table)
    expected = 16.0 + 8.0 * 4.0 - 0.95 * NG_CO2_TON_PER_MMBTU * 8.0 * 85.0
    assert ra.vom[0] == pytest.approx(expected)
    assert ra.emission_rate_ton_mwh[0] == pytest.approx(0.02124)


def test_45q_zero_raises_net_vom(tmp_path) -> None:
    """Disabling 45Q (0) raises the net VOM by capture × intensity × 85 vs default."""
    table = _write_cost_table(tmp_path, [_CCS_ROW])
    base = PortfolioConfig(active_resources=("ccs",), gas_price_mmbtu=4.0)
    no_credit = base.with_overrides(ccs_45q_per_ton=0.0)
    vom_with = load_resource_arrays(base, cost_table=table).vom[0]
    vom_without = load_resource_arrays(no_credit, cost_table=table).vom[0]
    assert vom_without - vom_with == pytest.approx(
        0.95 * NG_CO2_TON_PER_MMBTU * 8.0 * 85.0
    )


def test_net_vom_clamped_at_zero(tmp_path) -> None:
    """A 45Q credit exceeding fuel + VOM clamps net VOM at 0, never negative."""
    # vom 1, HR 8 @ $0.10 gas = 0.8 fuel; 45Q term ≈ 34.3 -> raw vom < 0.
    row = "ccs,generation,capex_fixed,2000,50,30,0.9,1,0,0,10000,0,8.0,0.95,0.02124,t"
    table = _write_cost_table(tmp_path, [row])
    cfg = PortfolioConfig(active_resources=("ccs",), gas_price_mmbtu=0.10)
    ra = load_resource_arrays(cfg, cost_table=table)
    assert ra.vom[0] == 0.0


# --- ADR 0012 admissibility threshold ---------------------------------------


def test_threshold_rejects_low_capture(tmp_path) -> None:
    """capture_rate = 0.85 (≤ 0.90) is rejected at load time."""
    row = "ccs,generation,capex_fixed,2000,50,30,0.9,16,0,0,10000,0,8.0,0.85,0.02124,t"
    table = _write_cost_table(tmp_path, [row])
    cfg = PortfolioConfig(active_resources=("ccs",), gas_price_mmbtu=4.0)
    with pytest.raises(ValueError, match="capture_rate=0.85 fails the ADR 0012"):
        load_resource_arrays(cfg, cost_table=table)


def test_threshold_rejects_high_emission_rate(tmp_path) -> None:
    """emission_rate_ton_mwh = 0.06 (≥ 0.050) is rejected at load time."""
    row = "ccs,generation,capex_fixed,2000,50,30,0.9,16,0,0,10000,0,8.0,0.95,0.06,t"
    table = _write_cost_table(tmp_path, [row])
    cfg = PortfolioConfig(active_resources=("ccs",), gas_price_mmbtu=4.0)
    with pytest.raises(ValueError, match="emission_rate_ton_mwh=0.06 fails"):
        load_resource_arrays(cfg, cost_table=table)


def test_threshold_boundary_exact_values_rejected(tmp_path) -> None:
    """The bright lines are strict: capture == 0.90 and residual == 0.050 both fail."""
    row_cap = "a,generation,capex_fixed,2000,50,30,0.9,16,0,0,10000,0,8.0,0.90,0.02,t"
    row_emi = "b,generation,capex_fixed,2000,50,30,0.9,16,0,0,10000,0,8.0,0.95,0.050,t"
    for row, res in ((row_cap, "a"), (row_emi, "b")):
        table = _write_cost_table(tmp_path, [row])
        cfg = PortfolioConfig(active_resources=(res,), gas_price_mmbtu=4.0)
        with pytest.raises(ValueError, match="ADR 0012"):
            load_resource_arrays(cfg, cost_table=table)


# --- gas-price resolution ----------------------------------------------------


def test_load_gas_price_table_and_missing_iso() -> None:
    """The shipped table resolves known ISOs; an unknown ISO returns None."""
    assert load_gas_price("ERCOT") == pytest.approx(3.00)
    assert load_gas_price("NEISO") == pytest.approx(4.60)
    assert load_gas_price("SAMPLE") is None


def test_gas_price_config_override_wins(tmp_path) -> None:
    """config.gas_price_mmbtu > 0 beats the per-ISO table value."""
    table = _write_cost_table(tmp_path, [_CCS_ROW])
    gas = _write_gas_table(tmp_path, ["ERCOT,3.00,hub,t"])
    cfg = PortfolioConfig(
        iso="ERCOT",
        active_resources=("ccs",),
        gas_price_mmbtu=9.0,
        # ERCOT has caps-table rows, so the ADR 0009 eligibility filter would
        # drop this synthetic resource without an explicit cap override.
        resource_caps_mw={"ccs": 1000.0},
    )
    ra = load_resource_arrays(cfg, cost_table=table, gas_table=gas)
    assert ra.vom[0] == pytest.approx(
        16.0 + 8.0 * 9.0 - 0.95 * NG_CO2_TON_PER_MMBTU * 8.0 * 85.0
    )


def test_gas_price_falls_back_to_table(tmp_path) -> None:
    """With no override (0.0), the per-ISO table price is used."""
    table = _write_cost_table(tmp_path, [_CCS_ROW])
    gas = _write_gas_table(tmp_path, ["ERCOT,3.00,hub,t"])
    cfg = PortfolioConfig(
        iso="ERCOT",
        active_resources=("ccs",),
        resource_caps_mw={"ccs": 1000.0},  # keep past the ADR 0009 ISO filter
    )
    ra = load_resource_arrays(cfg, cost_table=table, gas_table=gas)
    assert ra.vom[0] == pytest.approx(
        16.0 + 8.0 * 3.0 - 0.95 * NG_CO2_TON_PER_MMBTU * 8.0 * 85.0
    )


def test_missing_gas_price_with_ccs_is_loud_error(tmp_path) -> None:
    """A fuel-burning resource with no resolvable gas price raises, not free-rides."""
    table = _write_cost_table(tmp_path, [_CCS_ROW])
    gas = _write_gas_table(tmp_path, ["ERCOT,3.00,hub,t"])
    cfg = PortfolioConfig(iso="SAMPLE", active_resources=("ccs",))
    with pytest.raises(ValueError, match="no delivered gas price"):
        load_resource_arrays(cfg, cost_table=table, gas_table=gas)


def test_no_gas_price_needed_without_fuel_burners(tmp_path) -> None:
    """Non-fuel resources never touch the gas table (missing table is fine)."""
    row = "solar,generation,capex_fixed,1000,15,30,0.26,0,0,0,10000,1,,,,t"
    table = _write_cost_table(tmp_path, [row])
    cfg = PortfolioConfig(iso="SAMPLE", active_resources=("solar",))
    ra = load_resource_arrays(cfg, cost_table=table, gas_table=tmp_path / "absent.csv")
    assert ra.names == ["solar"]
    assert ra.emission_rate_ton_mwh[0] == 0.0


# --- emissions split in the LP (reporting only) -------------------------------


def _ccs_only_arrays(vom: float = 10.0, emission: float = 0.021) -> ResourceArrays:
    """One firm CCS-like generator with a residual emission rate."""
    return ResourceArrays(
        names=["ccs"],
        is_storage=np.array([False]),
        fixed_mwyr=np.array([1000.0]),
        vom=np.array([vom]),
        cap_max_mw=np.array([1e6]),
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([1.0]),
        duration_h=np.array([0.0]),
        rte=np.array([1.0]),
        emission_rate_ton_mwh=np.array([emission]),
    )


def test_emissions_split_and_full_matching_credit() -> None:
    """CCS serving load yields resource_co2 > 0, consistent grid_co2, and
    matching that counts CCS output fully (no intensity discount)."""
    T = 24
    cfg = PortfolioConfig(hours=T, mode="premium_cap")
    res = _ccs_only_arrays()
    load = np.full(T, 10.0)
    lmp = np.full(T, 50.0)
    cf = np.ones((1, T))
    grid_rate = np.full(T, 0.4)  # tCO2/MWh on unmatched purchases
    r = build_and_solve(cfg, res, load, lmp, cf, 1e9, emission_rate=grid_rate)
    assert r.status == "Optimal"
    gen_mwh = float(r.gen.sum())
    assert gen_mwh > 0
    assert r.resource_co2_tons == pytest.approx(gen_mwh * 0.021, rel=1e-6)
    assert r.grid_co2_tons == pytest.approx(r.grid_buy_mwh * 0.4, rel=1e-6)
    assert r.residual_co2_tons == pytest.approx(
        r.grid_co2_tons + r.resource_co2_tons, rel=1e-9
    )
    # Matching credit is NOT discounted by the residual emission rate
    # (ADR 0012 threshold-full-credit): matched = load − grid_buy only.
    assert r.matching_pct == pytest.approx(
        1.0 - r.grid_buy_mwh / r.total_load_mwh, abs=1e-9
    )


def test_ccs_not_swept_into_additionality() -> None:
    """capex-basis CCS is not is_existing: additionality leaves its credit intact."""
    T = 24
    res = _ccs_only_arrays()
    assert not res.is_existing.any()  # ppa-basis-only flag (ADR 0008/0012)
    cfg = PortfolioConfig(hours=T, mode="premium_cap", additionality_only=True)
    load = np.full(T, 10.0)
    lmp = np.full(T, 50.0)
    cf = np.ones((1, T))
    r = build_and_solve(cfg, res, load, lmp, cf, 1e9)
    # CCS generation still counts as matched under additionality_only.
    assert r.matching_pct == pytest.approx(
        1.0 - r.grid_buy_mwh / r.total_load_mwh, abs=1e-9
    )
    assert r.matching_pct > 0.99


# --- catalog rows: retrofit vs new -------------------------------------------


def test_ccs_catalog_rows_are_lmp_ppa_attribute_basis() -> None:
    """Real-catalog CCS is lmp_ppa (ADR 0020): LMP + EAC, no capex, no 45Q-in-VOM.

    Supersedes the pre-ADR-0020 capex-basis retrofit-vs-new all-in comparison —
    the capex and 45Q now accrue to the project owner (priced into the EAC by
    scripts/derive_eac_breakeven.py), and the LP sees only LMP + the EAC premium.
    """
    cfg = PortfolioConfig(
        iso="ERCOT",
        year=2030,
        active_resources=("gas_cc_ccs_new", "gas_cc_ccs_retrofit"),
    )
    ra = load_resource_arrays(cfg)
    idx = {n: i for i, n in enumerate(ra.names)}
    new, retro = idx["gas_cc_ccs_new"], idx["gas_cc_ccs_retrofit"]
    # No fixed capex enters the LP; energy is priced at the hourly LMP.
    assert ra.fixed_mwyr[new] == 0.0 and ra.fixed_mwyr[retro] == 0.0
    assert ra.lmp_indexed[new] and ra.lmp_indexed[retro]
    # VOM carries ONLY the EAC premium resolved from data/eac/eac_prices.csv 2030.
    assert ra.vom[new] == pytest.approx(20.0)
    assert ra.vom[retro] == pytest.approx(12.0)
    # Retrofit prices only the decarbonization increment -> lower clean premium.
    assert ra.vom[retro] < ra.vom[new]
    # Residual emissions are still carried for reporting (ADR 0012 unchanged).
    assert ra.emission_rate_ton_mwh[new] > 0.0


def test_ccs_rows_inactive_by_default() -> None:
    """active_minimal excludes both CCS tranches: the default catalog is unchanged
    and its emission rates are all zero (SAMPLE bit-identity guard)."""
    ra = load_resource_arrays(PortfolioConfig())
    assert "gas_cc_ccs_new" not in ra.names
    assert "gas_cc_ccs_retrofit" not in ra.names
    assert (ra.emission_rate_ton_mwh == 0.0).all()


def test_ccs_caps_present_for_all_isos() -> None:
    """Every modeled ISO carries caps rows for both CCS tranches."""
    from lce_portfolio.resources import load_resource_caps

    caps = load_resource_caps()
    for iso in ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"):
        assert caps[iso]["gas_cc_ccs_new"] > 0
        assert caps[iso]["gas_cc_ccs_retrofit"] > 0
        # Retrofit cap mirrors the contractable-fleet-share logic: never above
        # 50% of any plausible CC fleet (i.e. bounded, not a free 1e6 default).
        assert caps[iso]["gas_cc_ccs_retrofit"] <= 30000


# --- end-to-end tiny sweep ----------------------------------------------------


def test_sweep_with_ccs_active_stays_monotone() -> None:
    """A SAMPLE sweep with gas_cc_ccs_new active keeps matching% non-decreasing.

    Uses a 10-day (240h) horizon instead of the full 8760: this test has no
    hydro-budget resource active (SAMPLE has no budget entry regardless), so
    nothing depends on the full calendar. The real-ATB-scale coefficients on
    gas_cc_ccs_new + battery_4h are what make full-8760 solves here slow
    (~49s each per PP-08 timing note in conftest.py's cross_feature_system
    docstring); a short multi-day window still exercises diurnal solar/battery
    dispatch, the premium-cap sweep, CCS build economics, and the monotonicity
    invariant under test.
    """
    T = 240
    cfg = PortfolioConfig(
        iso="SAMPLE",
        hours=T,
        active_resources=("solar_pv", "battery_4h", "gas_cc_ccs_new"),
        gas_price_mmbtu=3.80,
        premium_deltas=(2.0, 10.0, 30.0),
        excess_sale_fraction=0.3,
    )
    from lce_portfolio.profiles import build_cf_matrix

    ra = load_resource_arrays(cfg)
    hours = np.arange(T)
    load = 500.0 + 100.0 * np.sin(hours / 24.0 * 2 * np.pi)
    lmp = np.clip(30.0 + 20.0 * np.sin((hours % 24 - 9) / 24.0 * 2 * np.pi), 5, None)
    cf = build_cf_matrix(ra, "SAMPLE", cfg.year)[:, :T]
    sweep = run_sweep(cfg, ra, load, lmp, cf)
    pcts = [r.matching_pct for r in sweep.results]
    assert all(r.status == "Optimal" for r in sweep.results)
    assert all(b >= a - 1e-6 for a, b in zip(pcts, pcts[1:]))
    # CCS is a firm resource with flat CF: at the loosest premium it should be
    # buildable, and any CCS generation shows up in resource_co2_tons.
    last = sweep.results[-1]
    ccs_i = last.resource_names.index("gas_cc_ccs_new")
    if last.build_mw[ccs_i] > 1e-3:
        assert last.resource_co2_tons > 0.0


# --- ADR 0012 gate hardening (audit findings DL-2 / DL-3) ---------------------


def test_fuel_row_blank_capture_and_emission_rejected(tmp_path) -> None:
    """A fuel-burning row must state capture/emission explicitly (DL-2).

    Regression: blank cells defaulted to 0.0, which silently passed the
    emission test and skipped the capture test — unabated gas entered the
    catalog as a fully-matching zero-emission resource.
    """
    row = "gas_cc_unabated,generation,capex_fixed,1100,30,30,0.9,2,0,0,10000,0,6.9,,,t"
    table = _write_cost_table(tmp_path, [row])
    cfg = PortfolioConfig(active_resources=("gas_cc_unabated",), gas_price_mmbtu=4.0)
    with pytest.raises(ValueError, match="capture_rate.*missing or blank"):
        load_resource_arrays(cfg, cost_table=table)


def test_fuel_row_capture_above_one_rejected(tmp_path) -> None:
    """capture_rate > 1 must not oversize the 45Q credit (DL-3)."""
    row = "ccs,generation,capex_fixed,2000,50,30,0.9,16,0,0,10000,0,8.0,1.5,0.0,t"
    table = _write_cost_table(tmp_path, [row])
    cfg = PortfolioConfig(active_resources=("ccs",), gas_price_mmbtu=4.0)
    with pytest.raises(ValueError, match=r"must be in \(0, 1\]"):
        load_resource_arrays(cfg, cost_table=table)


def test_fuel_row_understated_emission_rate_rejected(tmp_path) -> None:
    """The stated residual rate must match (1-capture)×0.0531×HR (DL-3).

    A row claiming a near-zero residual while its capture/heat-rate imply
    0.0378 tCO2/MWh must fail the cross-check rather than slip under the
    ADR 0012 threshold.
    """
    row = "ccs,generation,capex_fixed,2000,50,30,0.9,16,0,0,10000,0,7.9,0.91,0.001,t"
    table = _write_cost_table(tmp_path, [row])
    cfg = PortfolioConfig(active_resources=("ccs",), gas_price_mmbtu=4.0)
    with pytest.raises(ValueError, match="inconsistent with"):
        load_resource_arrays(cfg, cost_table=table)


def test_fuel_row_consistent_within_rounding_tolerance(tmp_path) -> None:
    """4-decimal CSV rounding of the residual rate passes the cross-check."""
    # implied = 0.05 × 0.0531 × 7.9 = 0.0209745; stated 0.0210 (rounded).
    row = "ccs,generation,capex_fixed,2000,50,30,0.9,16,0,0,10000,0,7.9,0.95,0.0210,t"
    table = _write_cost_table(tmp_path, [row])
    cfg = PortfolioConfig(active_resources=("ccs",), gas_price_mmbtu=4.0)
    ra = load_resource_arrays(cfg, cost_table=table)
    assert ra.emission_rate_ton_mwh[0] == pytest.approx(0.0210)
