"""Unit tests for the T1-X crossover scorer (FF-0E, plan §2.2).

Trivial-first, no LP solve. Covers:

* the >= 2026 structural refusal — the bench + actual loaders raise BEFORE any
  file is opened (monkeypatch ``gzip.open`` / ``open`` / ``pd.read_parquet`` to
  raise if a "2026" path is ever reached, then drive the loaders and assert they
  raised on the guard, not the open);
* the input-gap ratio arithmetic on synthetic forecast/keeper scalars (2.0, inf,
  0.0, None), divide-by-zero-safe;
* gmModel / lmp / co2 reconstruction from a tiny synthetic DispatchResult +
  FleetContext (2 gens, 2 zones, few hours) — TWh / load-weighted mean price /
  full-plant CO2 computed correctly;
* the capacity-events reuse — a synthetic ledger passes through
  ``score_capacity_hindcast.score_retirements`` unchanged.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.model.dispatch import DispatchResult
from market_sim.results.outputs import FleetContext

from scripts import score_crossover as X


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def _result(dispatch, prices, wind, solar, emissions=None):
    """Minimal DispatchResult from the arrays the scorer reads."""
    n_zones, T = prices.shape
    return DispatchResult(
        dispatch=np.asarray(dispatch, float),
        wind_dispatched=np.asarray(wind, float),
        solar_dispatched=np.asarray(solar, float),
        slack=np.zeros((n_zones, T)),
        dump=np.zeros((n_zones, T)),
        prices=np.asarray(prices, float),
        storage_charge=None,
        storage_discharge=None,
        storage_soc=None,
        flows=None,
        objective_value=0.0,
        status="Optimal",
        build_time=0.0,
        solve_time=0.0,
        emissions=None if emissions is None else np.asarray(emissions, float),
    )


def _context(fuel_types, plant_groups, emission_rate, pmax):
    n = len(fuel_types)
    return FleetContext(
        fuel_types=list(fuel_types),
        pmax_mw=list(pmax),
        emission_rate=list(emission_rate),
        efficiency_bins=["x"] * n,
        heat_rates=[8.0] * n,
        zones=["z0"] * n,
        unit_ids=[f"G{i}" for i in range(n)],
        wind_cap_mw=1000.0,
        solar_cap_mw=1000.0,
        wind_potential_mwh=0.0,
        solar_potential_mwh=0.0,
        storage_energy_cap_mwh=0.0,
        plant_groups=list(plant_groups),
    )


# --------------------------------------------------------------------------- #
# (c) >= 2026 structural refusal — the headline safety requirement
# --------------------------------------------------------------------------- #
def test_assert_scoreable_year_refuses_2026():
    with pytest.raises(ValueError):
        X._assert_scoreable_year(2026)
    with pytest.raises(ValueError):
        X._assert_scoreable_year(2027)
    # scored years are fine
    for y in (2023, 2024, 2025):
        assert X._assert_scoreable_year(y) == y


def test_bench_loader_refuses_2026_before_open(monkeypatch):
    """The bench loader raises on the guard before a 2026 file is ever read.

    ``read_bytes`` is wrapped to explode ONLY on a 2026 path (a legitimate 2025
    read passes through), so a guard that fired late — after opening the 2026
    file — would surface as an AssertionError, not the ValueError we assert.
    """
    real_read_bytes = X.Path.read_bytes

    def _guarded_read_bytes(self, *a, **k):
        if "2026" in str(self):
            raise AssertionError(f"read a quarantined 2026 file: {self}")
        return real_read_bytes(self, *a, **k)

    monkeypatch.setattr(X.Path, "read_bytes", _guarded_read_bytes)

    with pytest.raises(ValueError):
        X.load_bench_year("ERCOT", 2026)
    # 2025 loads for real; the 2026 element raises the guard ValueError.
    with pytest.raises(ValueError):
        X.load_bench("ERCOT", [2025, 2026])


def test_actual_co2_loader_refuses_2026_before_campd(monkeypatch):
    """The actual-CO2 facade raises before delegating to the CAMPD reader."""

    def _boom(*a, **k):
        raise AssertionError("actual_co2_by_year (CAMPD) was reached for 2026")

    monkeypatch.setattr(X.CH, "actual_co2_by_year", _boom)
    with pytest.raises(ValueError):
        X.crossover_actual_co2("ERCOT", [2026])
    with pytest.raises(ValueError):
        X.crossover_actual_co2("ERCOT", [2024, 2026])


def test_no_2026_file_path_is_ever_opened(monkeypatch):
    """Global guard: patch the low-level readers to explode on any 2026 path."""
    import builtins
    import gzip as _gzip

    real_open, real_gzip_open = builtins.open, _gzip.open

    def _guard_open(file, *a, **k):
        if "2026" in str(file) or "H1-2026" in str(file):
            raise AssertionError(f"opened a quarantined path: {file}")
        return real_open(file, *a, **k)

    def _guard_gzip_open(file, *a, **k):
        if "2026" in str(file):
            raise AssertionError(f"gzip-opened a quarantined path: {file}")
        return real_gzip_open(file, *a, **k)

    monkeypatch.setattr(builtins, "open", _guard_open)
    monkeypatch.setattr(_gzip, "open", _guard_gzip_open)

    # Every quarantined loader path raises ValueError on the guard, never the
    # AssertionError the patched openers would raise.
    with pytest.raises(ValueError):
        X.load_bench_year("ERCOT", 2026)
    with pytest.raises(ValueError):
        X.crossover_actual_co2("ERCOT", [2026])


# --------------------------------------------------------------------------- #
# (a) input-gap ratio arithmetic
# --------------------------------------------------------------------------- #
def test_input_gap_basic_ratio():
    f = {"err": 0.12}
    k = {"err": 0.06}
    assert X._input_gap(f, k) == 2.0


def test_input_gap_keeper_zero_is_inf_not_crash():
    assert X._input_gap({"err": 0.12}, {"err": 0.0}) == "inf"
    # both zero → a defined 0.0, not inf
    assert X._input_gap({"err": 0.0}, {"err": 0.0}) == 0.0


def test_input_gap_missing_side_is_none():
    assert X._input_gap(None, {"err": 0.06}) is None
    assert X._input_gap({"err": 0.12}, None) is None


def test_scalar_and_gap_price_mean_records():
    """_scalar → fractional error, feeds the gap identically on both sides."""
    fc = [
        {
            "criterion": "price_mean",
            "key": None,
            "year": 2023,
            "status": X.V.FAIL,
            "model": 40.0,
            "actual": 50.0,
        },
        {
            "criterion": "price_mean",
            "key": "da_diagnostic",
            "year": 2023,
            "status": X.V.SKIPPED,
            "model": 40.0,
            "actual": 60.0,
        },  # ignored
    ]
    kp = [
        {
            "criterion": "price_mean",
            "key": None,
            "year": 2023,
            "status": X.V.PASS,
            "model": 47.5,
            "actual": 50.0,
        },
    ]
    fs = X._scalar("price_mean", fc)
    ks = X._scalar("price_mean", kp)
    assert fs["err"] == pytest.approx(0.2)  # |40-50|/50
    assert ks["err"] == pytest.approx(0.05)  # |47.5-50|/50
    assert X._input_gap(fs, ks) == pytest.approx(4.0)


def test_scalar_fuelmix_aggregate_and_skip():
    recs = [
        {
            "criterion": "fuelmix",
            "key": "CC_REGULAR",
            "year": 2023,
            "status": X.V.PASS,
            "model": 10.0,
            "actual": 12.0,
        },
        {
            "criterion": "fuelmix",
            "key": "COAL_PRB",
            "year": 2023,
            "status": X.V.FAIL,
            "model": 5.0,
            "actual": 3.0,
        },
        {
            "criterion": "fuelmix",
            "key": "ST_GAS",
            "year": 2023,
            "status": X.V.SKIPPED,
            "model": 1.0,
            "actual": None,
        },  # not counted
    ]
    s = X._scalar("fuelmix", recs)
    assert s["err"] == pytest.approx(4.0)  # |10-12| + |5-3|
    assert set(s["detail"]) == {"CC_REGULAR", "COAL_PRB"}


def test_scalar_price_shape_is_nrmse():
    recs = [
        {
            "criterion": "price_shape",
            "key": None,
            "year": 2023,
            "status": X.V.PASS,
            "model": 0.14,
            "actual": None,
        }
    ]
    assert X._scalar("price_shape", recs)["err"] == pytest.approx(0.14)


def test_scalar_all_skipped_is_none():
    recs = [
        {
            "criterion": "co2",
            "key": None,
            "year": 2023,
            "status": X.V.SKIPPED,
            "model": None,
            "actual": None,
        }
    ]
    assert X._scalar("co2", recs) is None


# --------------------------------------------------------------------------- #
# gmModel / lmp / co2 reconstruction from a tiny DispatchResult + FleetContext
# --------------------------------------------------------------------------- #
def test_build_gmmodel_classes_and_twh():
    # Gen 0: CC_REGULAR (plant_group), 1 MW every hour over 1e6 hours-equivalent.
    # Use explicit MWh so the TWh math is exact: put 2e6 MWh on gen0, 1e6 on gen1.
    T = 4
    dispatch = np.array(
        [
            [0.5e6, 0.5e6, 0.5e6, 0.5e6],  # gen0 sums to 2e6 MWh -> 2.0 TWh
            [0.25e6, 0.25e6, 0.25e6, 0.25e6],  # gen1 sums to 1e6 MWh -> 1.0 TWh
        ]
    )
    wind = np.array([[0.5e6, 0.5e6, 0.5e6, 0.5e6]])  # 2e6 MWh -> 2.0 TWh
    solar = np.array([[0.25e6, 0.25e6, 0.25e6, 0.25e6]])  # 1e6 MWh -> 1.0 TWh
    prices = np.zeros((1, T))
    res = _result(dispatch, prices, wind, solar)
    ctx = _context(
        fuel_types=["gas_cc", "nuclear"],
        plant_groups=["CC_REGULAR", ""],  # nuclear has empty plant_group
        emission_rate=[0.4, 0.0],
        pmax=[600.0, 1200.0],
    )
    gm = X.build_gmmodel(res, ctx)
    assert gm["CC_REGULAR"] == pytest.approx(2.0)
    assert gm["nuclear"] == pytest.approx(1.0)  # via _FUEL_TO_CLASS
    assert gm["wind"] == pytest.approx(2.0)
    assert gm["solar"] == pytest.approx(1.0)


def test_build_lmp_load_weighted_mean_and_months():
    # One zone, two hours: prices [10, 30], demand [1, 3] -> LW mean = (10+90)/4 = 25.
    T = 2
    prices = np.array([[10.0, 30.0]])
    dispatch = np.zeros((1, T))
    res = _result(dispatch, prices, np.zeros((1, T)), np.zeros((1, T)))
    demand = np.array([[1e6, 3e6]])  # MWh
    lmp = X.build_lmp(res, demand)
    z = lmp["z0"]
    assert z["p"] == pytest.approx(25.0)
    assert z["d"] == pytest.approx(4.0)  # 4e6 MWh -> 4 TWh
    # both hours land in January (month 0)
    assert z["pMon"][0] == pytest.approx(25.0)
    assert z["dMon"][0] == pytest.approx(4.0)
    assert z["pMon"][1] is None


def test_build_lmp_none_demand_returns_empty():
    T = 2
    res = _result(
        np.zeros((1, T)), np.zeros((1, T)), np.zeros((1, T)), np.zeros((1, T))
    )
    assert X.build_lmp(res, None) == {}


def test_model_co2_fullplant_uses_bench_intensity_and_btm():
    gm = {"CC_REGULAR": 10.0, "COAL_PRB": 5.0}
    ybench = {
        "co2": {
            "intensity": {"CC_REGULAR": 0.4, "COAL_PRB": 1.0},
            "btmClass": {"CC_REGULAR": 2.0},  # 2 TWh BTM added back on CC
        }
    }
    # (10+2)*0.4 + (5+0)*1.0 = 4.8 + 5.0 = 9.8 Mt
    assert X.model_co2_mt_fullplant(gm, ybench) == pytest.approx(9.8)


def test_model_co2_fullplant_none_without_intensity():
    assert X.model_co2_mt_fullplant({"CC_REGULAR": 10.0}, {"co2": {}}) is None


def test_model_co2_physical_from_dispatch_and_rate():
    T = 2
    dispatch = np.array([[1e6, 1e6], [1e6, 1e6]])  # gen0 2e6 MWh, gen1 2e6 MWh
    res = _result(dispatch, np.zeros((2, T)), np.zeros((2, T)), np.zeros((2, T)))
    ctx = _context(
        fuel_types=["gas_cc", "coal"],
        plant_groups=["CC_REGULAR", "COAL_PRB"],
        emission_rate=[0.5, 1.0],  # tCO2/MWh
        pmax=[600.0, 600.0],
    )
    # 2e6*0.5 + 2e6*1.0 = 3e6 tonnes = 3.0 Mt
    assert X.model_co2_mt_physical(res, ctx) == pytest.approx(3.0)


def test_model_co2_physical_prefers_emissions_array():
    T = 2
    dispatch = np.array([[1e6, 1e6]])
    emissions = np.array([[1e6, 0.5e6]])  # 1.5e6 tonnes -> 1.5 Mt
    res = _result(
        dispatch,
        np.zeros((1, T)),
        np.zeros((1, T)),
        np.zeros((1, T)),
        emissions=emissions,
    )
    ctx = _context(["gas_cc"], ["CC_REGULAR"], [0.4], [600.0])
    assert X.model_co2_mt_physical(res, ctx) == pytest.approx(1.5)


# --------------------------------------------------------------------------- #
# (b) capacity-events reuse — synthetic ledger through score_retirements
# --------------------------------------------------------------------------- #
def test_capacity_reuse_score_retirements_passthrough():
    actuals = pd.DataFrame(
        [{"kind": "retirement", "fuel": "coal", "mw": 1000, "year": 2023}]
    )
    model = pd.DataFrame([{"unit_id": "m1", "fuel": "coal", "mw": 1050, "year": 2023}])
    ret = X.CH.score_retirements(model, actuals)
    assert ret["total_gw"]["band"] == "PASS"
    assert abs(ret["total_gw"]["err_frac"] - 0.05) < 1e-9
