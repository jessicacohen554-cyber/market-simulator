"""Tests for hourly fossil-average residual-carbon attribution (ADR 0013).

Covers the vendored :func:`compute_fossil_avg_rate` copy, the emission-rate
intake (``(hour, iso, fossil_avg_co2_rate)``, same validation rigor as the
ADR 0011 LMP contract), the ``build_fossil_avg_co2_rate.py`` export script
against a synthetic market-sim dispatch Parquet (no ``market_sim`` import
anywhere), and the end-to-end LP wiring — including proof that the residual
uses HOUR-VARYING rates and is not silently collapsed to a scalar. Parity of
the vendored function with upstream lives in the *market_sim* test tree
(``tests/test_emissions.py::TestVendoredParityScope2``), because that side of
the comparison imports the market simulator package.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.intake import emissions_intake, prepare_emission_rate
from lce_portfolio.lp import build_and_solve
from lce_portfolio.sweep import run_sweep
from lce_portfolio.vendored.fossil_avg_rate import compute_fossil_avg_rate

from conftest import daytime_solar_cf, solar_only

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "build_fossil_avg_co2_rate.py"
)


# --- vendored compute_fossil_avg_rate ---------------------------------------


def test_fossil_avg_rate_all_fossil_weighted_average() -> None:
    """All-fossil fleet: rate is the dispatch-weighted average per hour."""
    dispatch = np.array([[10.0, 20.0, 0.0], [30.0, 20.0, 5.0]])
    rates = np.array([0.4, 1.0])
    got = compute_fossil_avg_rate(dispatch, rates)
    expected = np.array(
        [
            (10.0 * 0.4 + 30.0 * 1.0) / 40.0,
            (20.0 * 0.4 + 20.0 * 1.0) / 40.0,
            5.0 * 1.0 / 5.0,
        ]
    )
    np.testing.assert_allclose(got, expected)


def test_fossil_avg_rate_excludes_zero_carbon_generation() -> None:
    """A zero-rate (nuclear-like) unit is excluded from numerator AND denominator."""
    dispatch = np.array([[50.0, 50.0], [1000.0, 1000.0]])
    rates = np.array([0.6, 0.0])
    np.testing.assert_allclose(compute_fossil_avg_rate(dispatch, rates), [0.6, 0.6])


def test_fossil_avg_rate_zero_fossil_hour_is_zero_not_nan() -> None:
    """Zero fossil dispatch -> rate 0.0 (documented convention), never nan/inf."""
    dispatch = np.array([[100.0, 0.0], [200.0, 500.0]])
    rates = np.array([0.5, 0.0])
    got = compute_fossil_avg_rate(dispatch, rates)
    np.testing.assert_allclose(got, [0.5, 0.0])
    assert np.all(np.isfinite(got))


# --- emission-rate intake (ADR 0013 contract) --------------------------------


def _rate_frame(T: int = 8760, iso: str = "ERCOT") -> pd.DataFrame:
    """Full-calendar synthetic rate frame: 0.5 t/MWh first half, 0.3 second."""
    rate = np.where(np.arange(T) < T // 2, 0.5, 0.3)
    return pd.DataFrame({"hour": np.arange(T), "iso": iso, "fossil_avg_co2_rate": rate})


def test_prepare_emission_rate_round_trips_full_calendar(tmp_path) -> None:
    """A valid full-8760 file returns the hour-ordered (8760,) vector."""
    path = tmp_path / "rates.csv"
    df = _rate_frame()
    # Shuffle rows: intake must sort by hour, not trust file order.
    df.sample(frac=1.0, random_state=0).to_csv(path, index=False)

    vec = prepare_emission_rate(path, "ERCOT")

    assert vec.shape == (8760,)
    assert np.allclose(vec[:4380], 0.5) and np.allclose(vec[4380:], 0.3)


def test_emissions_intake_missing_column_raises(tmp_path) -> None:
    path = tmp_path / "rates.csv"
    _rate_frame().rename(columns={"fossil_avg_co2_rate": "rate"}).to_csv(
        path, index=False
    )
    with pytest.raises(ValueError, match="missing columns"):
        emissions_intake(path)


def test_emissions_intake_negative_rate_raises(tmp_path) -> None:
    """A negative rate is a data error, not a legitimate carbon credit."""
    df = _rate_frame()
    df.loc[7, "fossil_avg_co2_rate"] = -0.1
    path = tmp_path / "rates.csv"
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match="non-negative"):
        emissions_intake(path)


def test_prepare_emission_rate_missing_hour_is_hard_error(tmp_path) -> None:
    """A missing hour raises (ADR 0010 convention), never a silent zero-fill."""
    df = _rate_frame()
    df = df[df["hour"] != 1234]
    path = tmp_path / "rates.csv"
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match="missing 1 of 8760"):
        prepare_emission_rate(path, "ERCOT")


def test_prepare_emission_rate_duplicate_hour_rejected(tmp_path) -> None:
    df = _rate_frame()
    df = pd.concat([df, df.iloc[[42]]], ignore_index=True)
    path = tmp_path / "rates.csv"
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match="duplicate"):
        prepare_emission_rate(path, "ERCOT")


def test_prepare_emission_rate_unknown_iso_raises_keyerror(tmp_path) -> None:
    path = tmp_path / "rates.csv"
    _rate_frame().to_csv(path, index=False)
    with pytest.raises(KeyError, match="SAMPLE"):
        prepare_emission_rate(path, "SAMPLE")


# --- export script (synthetic market-sim dispatch fixture) -------------------


def _load_script():
    """Import the export script as a module by file path (never market_sim)."""
    spec = importlib.util.spec_from_file_location(
        "build_fossil_avg_co2_rate", _SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_dispatch_fixture(
    path: Path,
    dispatch: np.ndarray,
    rates: np.ndarray | None,
):
    """Write a Parquet mimicking market_sim.results.outputs.to_parquet.

    Only the pieces the export script consumes are reproduced: the per-hour
    ``list<float64>`` ``dispatch`` column (one list entry per generator) and
    the ``market_sim_fleet`` schema-metadata JSON carrying ``emission_rate``
    (omitted when ``rates`` is ``None``, to exercise the missing-metadata
    error path).
    """
    n_gen, T = dispatch.shape
    arr = np.ascontiguousarray(dispatch.T, dtype=np.float64)
    flat = pa.array(arr.ravel(), type=pa.float64())
    offsets = pa.array(np.arange(0, (T + 1) * n_gen, n_gen, dtype=np.int32))
    table = pa.table(
        {
            "hour": pa.array(np.arange(T), type=pa.int32()),
            "dispatch": pa.ListArray.from_arrays(offsets, flat),
        }
    )
    if rates is not None:
        table = table.replace_schema_metadata(
            {
                b"market_sim_fleet": json.dumps(
                    {"emission_rate": [float(r) for r in rates]}
                ).encode()
            }
        )
    pq.write_table(table, path)


def test_export_script_end_to_end_matches_hand_computation(tmp_path) -> None:
    """Script reads a synthetic dispatch Parquet and writes the ADR 0013 contract."""
    # 3 generators (coal-like 0.9, gas-like 0.4, nuclear-like 0.0), 4 hours;
    # hour 3 has zero fossil dispatch.
    dispatch = np.array(
        [
            [100.0, 0.0, 50.0, 0.0],
            [100.0, 200.0, 0.0, 0.0],
            [500.0, 500.0, 500.0, 500.0],
        ]
    )
    rates = np.array([0.9, 0.4, 0.0])
    fixture = tmp_path / "year_2030.parquet"
    _write_dispatch_fixture(fixture, dispatch, rates)

    script = _load_script()
    out_dir = tmp_path / "out"
    rc = script.main(
        [
            "--iso",
            "ERCOT",
            "--year",
            "2030",
            "--result",
            str(fixture),
            "--out-dir",
            str(out_dir),
        ]
    )
    assert rc == 0

    back = pd.read_parquet(out_dir / "ERCOT_2030_fossil_avg_co2_rate.parquet")
    assert list(back.columns) == ["hour", "iso", "fossil_avg_co2_rate"]
    assert (back["iso"] == "ERCOT").all()
    expected = np.array(
        [
            (100.0 * 0.9 + 100.0 * 0.4) / 200.0,  # 0.65
            200.0 * 0.4 / 200.0,  # 0.40
            50.0 * 0.9 / 50.0,  # 0.90
            0.0,  # zero-fossil hour
        ]
    )
    np.testing.assert_allclose(
        back.sort_values("hour")["fossil_avg_co2_rate"].to_numpy(), expected
    )


def test_export_script_rejects_parquet_without_fleet_metadata(tmp_path) -> None:
    """A dispatch file with no fleet context is a clear error, not a KeyError."""
    fixture = tmp_path / "year_2030.parquet"
    _write_dispatch_fixture(fixture, np.ones((2, 3)), rates=None)
    script = _load_script()
    with pytest.raises(ValueError, match="market_sim_fleet"):
        script.read_dispatch_and_rates(fixture)


# --- LP wiring (residual_co2_tons, ADR 0013) ---------------------------------


def test_no_emissions_file_means_zero_residual() -> None:
    """emission_rate=None (no emissions_file, e.g. SAMPLE) -> residual is 0."""
    T = 24
    res = solar_only()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(iso="SAMPLE", hours=T, mode="premium_cap")

    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1e6)

    assert r.status == "Optimal"
    assert r.grid_buy_mwh > 0.0  # unmatched energy exists...
    assert r.residual_co2_tons == 0.0  # ...but reporting is off


def test_end_to_end_residual_reflects_hour_varying_rates() -> None:
    """residual_co2_tons is the exact hourly dot product, not a scalar collapse.

    Solar covers hours 8-15 of a flat 100 MW load, leaving grid_buy = 100 MWh
    in hours 0-7 and 16-23. The rate vector is 0.5 (hours 0-7), 0.1 (8-15),
    0.2 (16-23):

        residual = 8×100×0.5 + 8×100×0.2 = 560 tCO2

    whereas any flat-scalar collapse of the same vector (mean 0.2667 × 1600
    MWh ≈ 426.7 t) would NOT match — proving the vector wiring is real.
    """
    T = 24
    res = solar_only()
    cf = daytime_solar_cf(res.n_res, T)  # solar available hours 8..15
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    rate = np.empty(T)
    rate[:8], rate[8:16], rate[16:] = 0.5, 0.1, 0.2
    cfg = PortfolioConfig(iso="ERCOT", hours=T, mode="premium_cap")

    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1e6, emission_rate=rate)

    assert r.status == "Optimal"
    assert np.isclose(r.grid_buy_mwh, 1600.0, atol=1.0)
    assert np.isclose(r.residual_co2_tons, float(r.grid_buy @ rate), rtol=1e-9)
    assert np.isclose(r.residual_co2_tons, 560.0, atol=1.0)
    scalar_collapse = r.grid_buy_mwh * rate.mean()
    assert not np.isclose(r.residual_co2_tons, scalar_collapse, rtol=0.05)


def test_run_sweep_threads_emission_rate_to_every_setpoint() -> None:
    """run_sweep passes the vector down; every frontier point carries a residual."""
    T = 24
    res = solar_only()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    rate = np.full(T, 0.4)
    cfg = PortfolioConfig(
        iso="ERCOT", hours=T, mode="premium_cap", premium_deltas=(1.0, 1e6)
    )

    sweep = run_sweep(cfg, res, load, lmp, cf, emission_rate=rate)

    for r in sweep.results:
        assert np.isclose(r.residual_co2_tons, float(r.grid_buy @ rate), rtol=1e-9)


def test_lp_rejects_wrong_length_emission_rate() -> None:
    """A rate vector that does not span the horizon is a hard shape error."""
    T = 24
    res = solar_only()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)
    cfg = PortfolioConfig(hours=T, mode="premium_cap")
    with pytest.raises(ValueError, match="emission_rate"):
        build_and_solve(
            cfg, res, load, lmp, cf, setpoint=1e6, emission_rate=np.zeros(23)
        )
