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

import json

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


def _context(fuel_types, plant_groups, emission_rate, pmax, unit_ids=None):
    n = len(fuel_types)
    return FleetContext(
        fuel_types=list(fuel_types),
        pmax_mw=list(pmax),
        emission_rate=list(emission_rate),
        efficiency_bins=["x"] * n,
        heat_rates=[8.0] * n,
        zones=["z0"] * n,
        unit_ids=list(unit_ids) if unit_ids else [f"G{i}" for i in range(n)],
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
    gm = X.build_gmmodel(res, ctx, "ERCOT")
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
def test_capacity_events_degrade_without_actuals_target(monkeypatch, tmp_path):
    """FH-4-CAISO contract: an ISO with no committed capacity-actuals target
    degrades explicitly instead of crashing the whole crossover score.

    ``CH.load_actuals`` SystemExits for an ISO whose
    ``capacity_actuals_<iso>.csv`` was never built (CAISO today).
    ``score_capacity_events`` must mirror the missing-keeper degrade in
    ``score_dispatch_skill``: record the absence in ``capacity_events_note``,
    carry ``None`` event blocks (never a fabricated table), and keep the co2
    block scored — its actual comes from the bench, not the capacity target.
    """

    def _no_target(iso):
        raise SystemExit(f"actuals not found: capacity_actuals_{iso.lower()}.csv")

    monkeypatch.setattr(X, "load_ledgers_for_run", lambda p: {})
    monkeypatch.setattr(X.CH, "load_actuals", _no_target)
    monkeypatch.setattr(X.CH, "model_co2_by_year", lambda p: {2023: 1.0})
    monkeypatch.setattr(X, "crossover_actual_co2", lambda iso, years: {2023: 2.0})
    out = X.score_capacity_events(tmp_path, "CAISO", None)
    assert out["retirements"] is None
    assert out["additions"] is None
    assert out["additions_cod_basis"] is None
    assert out["additions_basis"] is None
    assert "no committed exit/addition target" in out["capacity_events_note"]
    assert "CAISO" in out["capacity_events_note"]
    assert out["co2"]["model"] == {"2023": 1.0}
    assert out["co2"]["actual"] == {"2023": 2.0}
    # The capacity-track actual carries its basis label (FINDING §2.3 hygiene)
    # so it is never conflated with the FC-4 eGRID basis in the same file.
    assert "FC-4 eGRID basis" in out["co2"]["actual_basis"]


def test_report_renders_capacity_events_degrade(tmp_path):
    """The (b) section renders the absence note, not a fabricated table."""
    score = {
        "run_id": "caiso-test",
        "iso": "CAISO",
        "vintage_year": 2023,
        "crossover_forward_year": 2023,
        "dispatch_skill": {
            "keeper_run_id": "k",
            "keeper_note": None,
            "metrics": {},
            "family_volume": {},
            "deferred": {},
        },
        "capacity_events_note": "capacity events not scored — no committed "
        "exit/addition target exists for CAISO",
        "retirements": None,
        "additions": None,
        "forward_invariants": {"note": "n/a", "per_year": {}},
    }
    path = tmp_path / "report.md"
    X.write_report(score, path)
    text = path.read_text()
    assert "no committed exit/addition target exists for CAISO" in text
    assert "thermal GW retired" not in text


def test_capacity_reuse_score_retirements_passthrough():
    actuals = pd.DataFrame(
        [{"kind": "retirement", "fuel": "coal", "mw": 1000, "year": 2023}]
    )
    model = pd.DataFrame([{"unit_id": "m1", "fuel": "coal", "mw": 1050, "year": 2023}])
    ret = X.CH.score_retirements(model, actuals)
    assert ret["total_gw"]["band"] == "PASS"
    assert abs(ret["total_gw"]["err_frac"] - 0.05) < 1e-9


# --------------------------------------------------------------------------- #
# FC-4 rubric contract — family volume + flat metrics + refusal marker
# (FFR-2A: folded in from the deleted scripts/_ff2d_crossover_adapter.py)
# --------------------------------------------------------------------------- #
def _fuelmix_rec(key, model, actual, status):
    return {
        "criterion": "fuelmix",
        "key": key,
        "year": 2023,
        "status": status,
        "model": model,
        "actual": actual,
    }


def test_family_volume_sums_the_family_fractionally():
    model = {"CC_REGULAR": 110.0, "CT_PEAKER": 12.0, "COAL_PRB": 40.0}
    actual = {"CC_REGULAR": 100.0, "CT_PEAKER": 10.0, "COAL_PRB": 50.0}
    gas = X._family_volume(model, actual, X._FAMILY_CLASSES["gas_twh"], "ERCOT", 2023)
    assert gas["model_twh"] == pytest.approx(122.0)
    assert gas["actual_twh"] == pytest.approx(110.0)
    assert gas["signed"] == pytest.approx(12.0 / 110.0, rel=1e-3)
    assert gas["gated"] is True
    coal = X._family_volume(model, actual, X._FAMILY_CLASSES["coal_twh"], "ERCOT", 2023)
    assert coal["signed"] == pytest.approx(-0.2)


def test_family_volume_reconciles_the_unsplit_coal_bucket():
    """The crossover regression: legacy bins report one ``COAL`` bucket.

    The bench splits coal into PRB/LIGNITE; the crossover's legacy-bin fleet
    reports the whole coal fleet as ``COAL``. Per-class the two never meet, so
    a record-based aggregation reads the model coal volume as ZERO (a 100%
    artifact). At family grain the comparison is real: 39.2 vs 60.4 TWh.
    """
    model = {"COAL": 39.24}
    actual = {"COAL_PRB": 45.09, "COAL_LIGNITE": 15.33}
    coal = X._family_volume(model, actual, X._FAMILY_CLASSES["coal_twh"], "ERCOT", 2023)
    assert coal["model_twh"] == pytest.approx(39.24)
    assert coal["actual_twh"] == pytest.approx(60.42)
    assert coal["signed"] == pytest.approx(-0.3506, abs=1e-3)
    assert coal["model_only_classes"] == ["COAL"]


def test_family_volume_flags_preliminary_vintage_classes(monkeypatch):
    monkeypatch.setattr(X.V, "class_is_gated", lambda iso, k, y: k != "ST_GAS")
    model = {"CC_REGULAR": 110.0, "ST_GAS": 20.0}
    actual = {"CC_REGULAR": 100.0, "ST_GAS": 20.0}
    gas = X._family_volume(model, actual, X._FAMILY_CLASSES["gas_twh"], "ERCOT", 2025)
    assert gas["actual_twh"] == pytest.approx(120.0)
    assert gas["incomplete_classes"] == ["ST_GAS"]
    assert gas["gated"] is False


def test_family_volume_no_actual_is_none():
    assert X._family_volume({}, {}, X._FAMILY_CLASSES["gas_twh"], "ERCOT", 2023) is None
    # Model-only family (no benchmarked actual at all) is not scorable.
    assert (
        X._family_volume(
            {"CC_REGULAR": 1.0}, {}, X._FAMILY_CLASSES["gas_twh"], "ERCOT", 2023
        )
        is None
    )


def _dispatch_stub(price_err=0.05, co2_err=-0.2, fam_gated=True):
    return {
        "metrics": {
            "price_mean": {
                "2023": {"forecast_err": price_err, "keeper_backcast_err": 0.01}
            },
            "co2": {
                "2023": {"forecast_err": abs(co2_err), "keeper_backcast_err": None}
            },
            "fuelmix": {},
            "price_shape": {},
        },
        "family_volume": {
            "gas_twh": {
                "2023": {
                    "forecast_err": 0.03,
                    "keeper_backcast_err": 0.01,
                    "gated": fam_gated,
                    "forecast_detail": {
                        "incomplete_classes": [] if fam_gated else ["ST_GAS"]
                    },
                }
            },
            "coal_twh": {},
        },
    }


def test_rubric_metrics_emits_the_scorer_contract():
    metrics, uncovered = X.rubric_metrics(_dispatch_stub())
    by = {(m["metric"], m["year"]): m for m in metrics}
    assert by[("price", 2023)]["forecast_abs_err_frac"] == pytest.approx(0.05)
    assert by[("price", 2023)]["keeper_abs_err_frac"] == pytest.approx(0.01)
    assert by[("co2", 2023)]["keeper_abs_err_frac"] is None
    assert by[("gas_twh", 2023)]["forecast_abs_err_frac"] == pytest.approx(0.03)
    # Everything the run cannot score is NAMED, never silently absent.
    assert any("coal_twh 2023" in u for u in uncovered)
    assert any("price 2024" in u for u in uncovered)
    # Only the rubric's own names are emitted — no re-keying of price_shape
    # (NRMSE) or aggregate fuelmix (TWh) onto a fractional band.
    assert {m["metric"] for m in metrics} <= {"price", "co2", "gas_twh", "coal_twh"}


def test_rubric_metrics_reports_ungated_family_instead_of_banding_it():
    metrics, uncovered = X.rubric_metrics(_dispatch_stub(fam_gated=False))
    assert not any(m["metric"] == "gas_twh" for m in metrics)
    assert any("gas_twh 2023" in u and "ST_GAS" in u for u in uncovered)


def test_rubric_metric_names_match_the_scorer_bands():
    from scripts import forecast_verdict as FV

    emitted = set(X._RUBRIC_METRIC_NAMES.values()) | set(X._FAMILY_CLASSES)
    assert emitted == set(FV.CROSSOVER_COMMERCIAL)
    assert X.QUARANTINE_FROM == FV.CROSSOVER_QUARANTINE_FLOOR
    assert tuple(X.SCORED_YEARS) == tuple(FV.CROSSOVER_SCORED_YEARS)


# --------------------------------------------------------------------------- #
# Coal class-grain repair (FINDING-capx-d5-crossover-co2-2026-08-30 §5.1):
# an unsplit-COAL fleet vs a rank-keyed bench
# --------------------------------------------------------------------------- #
def test_build_gmmodel_splits_generic_coal_to_supply_class():
    """The unsplit-COAL fleet lands on the bench's rank keys (option (a)).

    Plant 6180 (Oak Grove) is in the hand-curated ``COAL_PLANT_SUPPLY`` map
    (lignite) — the first hop of the canonical chain, so this test needs no
    derived CSVs. A plant code the chain cannot resolve stays generic ``COAL``
    (the keeper's own residual bucket), never a wrong rank.
    """
    T = 2
    dispatch = np.array([[0.5e6, 0.5e6], [0.25e6, 0.25e6]])  # 2.0 / 1.0 TWh
    res = _result(dispatch, np.zeros((1, T)), np.zeros((1, T)), np.zeros((1, T)))
    ctx = _context(
        fuel_types=["coal", "coal"],
        plant_groups=["COAL", "COAL"],  # the crossover fleet's generic class
        emission_rate=[1.0, 1.0],
        pmax=[600.0, 600.0],
        unit_ids=["COAL_North_p6180_mustrun", "COAL_West_p999999_econ"],
    )
    gm = X.build_gmmodel(res, ctx, "ERCOT")
    assert gm["COAL_LIGNITE"] == pytest.approx(1.0)  # curated: 6180 -> lignite
    assert gm["COAL"] == pytest.approx(0.5)  # unresolvable stays generic
    # The split coal is now visible to the bench-intensity CO2 construction —
    # the seam model_co2_mt_fullplant iterates bench keys over.
    ybench = {"co2": {"intensity": {"COAL_LIGNITE": 1.1}, "btmClass": {}}}
    assert X.model_co2_mt_fullplant(gm, ybench) == pytest.approx(1.1)


def test_build_gmmodel_splits_coal_numeric_head_for_non_ercot():
    """Non-ERCOT EIA-860 fleets name units ``{plant_code}_{gen}`` — the
    numeric-head parse feeds the same canonical chain (3470 W A Parish is
    curated PRB)."""
    T = 1
    dispatch = np.array([[1.0e6]])
    res = _result(dispatch, np.zeros((1, T)), np.zeros((1, T)), np.zeros((1, T)))
    ctx = _context(
        fuel_types=["coal"],
        plant_groups=[""],  # per-plant fleet: class via the fuel fallback
        emission_rate=[1.0],
        pmax=[600.0],
        unit_ids=["3470_ST5"],
    )
    gm = X.build_gmmodel(res, ctx, "PJM")
    assert gm == {"COAL_PRB": 1.0, "wind": 0.0, "solar": 0.0}


def test_bench_coal_intensity_is_actual_co2_weighted():
    ybench = {
        "co2": {
            "intensity": {"COAL_PRB": 1.0, "COAL_LIGNITE": 1.1, "CC_REGULAR": 0.4},
            "btmClass": {},
        },
        "classFull": {"COAL_PRB": 40.0, "COAL_LIGNITE": 20.0},
    }
    # weights = actual CO2: PRB 40*1.0=40, LIG 20*1.1=22 -> (40*1.0+22*1.1)/62
    assert X.bench_coal_intensity(ybench) == pytest.approx((40.0 + 24.2) / 62.0)
    # no coal intensity at all (NYISO) -> 0.0, the caller's no-op signal
    assert X.bench_coal_intensity({"co2": {"intensity": {"CC_REGULAR": 0.4}}}) == 0.0


def _rescore_bundle(tmp_path, iso, ds_metrics_co2, coal_fam, per_class, flat):
    """Materialize a minimal committed crossover bundle for the rescore mode."""
    bundle = tmp_path / f"{iso.lower()}-rescore"
    cache = bundle / iso / "k"
    cache.mkdir(parents=True)
    (bundle / "meta.json").write_text(
        json.dumps(
            {"kind": "crossover", "iso": iso, "bundle": str(cache), "cache_key": "k"}
        )
    )
    score = {
        "run_id": bundle.name,
        "iso": iso,
        "scored_years": [2023, 2024, 2025],
        "metrics": flat,
        "dispatch_skill": {
            "metrics": {
                "co2": ds_metrics_co2,
                "fuelmix": {"2023": {"forecast_per_class": per_class}},
                "price_mean": {"2023": {"forecast_err": 0.1}},
                "price_shape": {},
            },
            "family_volume": {"coal_twh": coal_fam, "gas_twh": {}},
        },
        "co2": {"model": {}, "actual": {}},
    }
    (cache / "crossover_score.json").write_text(json.dumps(score))
    return bundle, cache


def test_coal_grain_rescore_moves_only_the_co2_seam(tmp_path, monkeypatch):
    ybench = {
        "co2": {
            "egrid": 100.0,
            "intensity": {"COAL_PRB": 1.0, "COAL_LIGNITE": 1.1, "CC_REGULAR": 0.4},
            "btmClass": {},
        },
        "classFull": {"COAL_PRB": 40.0, "COAL_LIGNITE": 20.0},
    }
    monkeypatch.setattr(X, "load_bench_year", lambda iso, year: ybench)
    co2_row = {
        "forecast_err": 0.5,
        "forecast_signed": -0.5,
        "keeper_backcast_err": None,
        "input_gap": None,
        "unit": "frac (|Δ|/actual)",
        "forecast_status": "FAIL",
    }
    per_class = {"COAL_PRB": {"model": 0.0}, "COAL_LIGNITE": {"model": 0.0}}
    coal_fam = {"2023": {"forecast_detail": {"model_twh": 30.0}, "gated": True}}
    flat = [
        {
            "metric": "co2",
            "year": 2023,
            "forecast_abs_err_frac": 0.5,
            "keeper_abs_err_frac": None,
        }
    ]
    bundle, cache = _rescore_bundle(
        tmp_path, "ERCOT", {"2023": dict(co2_row)}, coal_fam, per_class, flat
    )
    X.coal_grain_rescore(bundle, tmp_path)
    out = json.loads((cache / "crossover_score.json").read_text())
    # S = 100*(1-0.5) = 50; unsplit = 30 - 0 TWh; i = (40+24.2)/62
    expected = (50.0 + 30.0 * ((40.0 + 24.2) / 62.0) - 100.0) / 100.0
    row = out["dispatch_skill"]["metrics"]["co2"]["2023"]
    assert row["forecast_signed"] == pytest.approx(expected, abs=1e-4)
    assert row["forecast_err"] == pytest.approx(abs(expected), abs=1e-4)
    assert out["metrics"][0]["forecast_abs_err_frac"] == pytest.approx(
        abs(expected), abs=1e-4
    )
    # The controls: family volume rows and C1 records are byte-untouched.
    assert out["dispatch_skill"]["family_volume"]["coal_twh"] == coal_fam
    assert (
        out["dispatch_skill"]["metrics"]["fuelmix"]["2023"]["forecast_per_class"]
        == per_class
    )
    assert out["dispatch_skill"]["metrics"]["price_mean"] == {
        "2023": {"forecast_err": 0.1}
    }
    # Provenance: the rescore block records the arithmetic.
    ry = out["rescore_co2_grain"]["per_year"]["2023"]
    assert ry["unsplit_coal_twh"] == pytest.approx(30.0)
    assert ry["signed_before"] == pytest.approx(-0.5)
    # Report-only hygiene: the capacity-track co2 basis is labelled.
    assert "STATE SUM" in out["co2"]["actual_basis"]


def test_coal_grain_rescore_is_a_noop_without_coal(tmp_path, monkeypatch):
    """The NYISO control: no coal family, no coal intensity -> nothing moves."""
    ybench = {
        "co2": {"egrid": 26.9, "intensity": {"CC_REGULAR": 0.4}, "btmClass": {}},
        "classFull": {"CC_REGULAR": 60.0},
    }
    monkeypatch.setattr(X, "load_bench_year", lambda iso, year: ybench)
    co2_row = {
        "forecast_err": 0.1013,
        "forecast_signed": 0.1013,
        "keeper_backcast_err": None,
        "input_gap": None,
        "unit": "frac (|Δ|/actual)",
        "forecast_status": "FAIL",
    }
    flat = [
        {
            "metric": "co2",
            "year": 2023,
            "forecast_abs_err_frac": 0.1013,
            "keeper_abs_err_frac": None,
        }
    ]
    bundle, cache = _rescore_bundle(
        tmp_path, "NYISO", {"2023": dict(co2_row)}, {}, {}, flat
    )
    X.coal_grain_rescore(bundle, tmp_path)
    out = json.loads((cache / "crossover_score.json").read_text())
    row = out["dispatch_skill"]["metrics"]["co2"]["2023"]
    assert row["forecast_signed"] == pytest.approx(0.1013, abs=1e-6)
    assert row["forecast_err"] == pytest.approx(0.1013, abs=1e-6)
    assert out["metrics"][0]["forecast_abs_err_frac"] == pytest.approx(0.1013, abs=1e-6)
    assert out["rescore_co2_grain"]["per_year"]["2023"]["unsplit_coal_twh"] == 0.0
