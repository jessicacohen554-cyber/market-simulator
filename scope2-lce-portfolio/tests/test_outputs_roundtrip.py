"""Round-trip tests for write_outputs: Parquet schemas + summarize() rendering.

test_outputs.py already checks the in-memory frontier/build-mix DataFrames and
a basic write+exists check; these tests read the written Parquet files back
and check the documented columns (including residual_co2_tons, ADR 0013) and
run-metadata JSON keys survive the round trip, and that summarize() toggles
its CO2 column correctly.
"""

import json
from dataclasses import fields

import numpy as np
import pandas as pd

from lce_portfolio.config import LMP_KIND_HOURLY, PortfolioConfig
from lce_portfolio.outputs import summarize, write_outputs
from lce_portfolio.sweep import run_sweep

from conftest import daytime_solar_cf, solar_plus_battery


def _sweep(co2_rate: float = 0.0):
    """Tiny 24h sweep; ``co2_rate`` > 0 threads a flat hourly emission-rate
    vector (ADR 0013) so residual_co2_tons is exercised end-to-end."""
    res = solar_plus_battery()
    cf = daytime_solar_cf(res.n_res, 24)
    load = np.full(24, 100.0)
    lmp = np.full(24, 40.0)
    lmp[16:20] = 90.0
    cfg = PortfolioConfig(
        hours=24,
        mode="premium_cap",
        premium_deltas=(5.0, 20.0),
        excess_sale_fraction=0.5,
    )
    emission_rate = np.full(24, co2_rate) if co2_rate > 0 else None
    return cfg, run_sweep(cfg, res, load, lmp, cf, emission_rate=emission_rate)


def test_frontier_parquet_round_trip_includes_residual_co2(tmp_path) -> None:
    cfg, sweep = _sweep(co2_rate=0.4)
    paths = write_outputs(sweep, tmp_path, config=cfg)
    back = pd.read_parquet(paths["frontier"])

    expected_cols = {
        "iso",
        "mode",
        "setpoint",
        "matching_pct",
        "premium_per_mwh",
        "premium_per_year",
        "pct_over_bau",
        "net_cost",
        "bau_cost",
        "capital_cost",
        "avoided_purchase_cost",
        "surplus_mwh",
        "surplus_revenue",
        "grid_buy_mwh",
        "total_load_mwh",
        "residual_co2_tons",
        "shadow_price",
        "status",
    }
    assert expected_cols <= set(back.columns)
    assert len(back) == len(sweep.results)
    for r, (_, row) in zip(sweep.results, back.iterrows()):
        assert np.isclose(row["residual_co2_tons"], r.residual_co2_tons)
        assert row["residual_co2_tons"] > 0.0  # nonzero rate -> nonzero residual


def test_build_mix_parquet_round_trip(tmp_path) -> None:
    cfg, sweep = _sweep()
    paths = write_outputs(sweep, tmp_path, config=cfg)
    back = pd.read_parquet(paths["build_mix"])

    assert set(back.columns) == {"iso", "setpoint", "resource", "build_mw"}
    expected_rows = sum(len(r.resource_names) for r in sweep.results)
    assert len(back) == expected_rows
    assert (back["build_mw"] >= 0.0).all()


def test_run_metadata_json_keys_round_trip(tmp_path) -> None:
    cfg, sweep = _sweep(co2_rate=0.4)
    paths = write_outputs(sweep, tmp_path, config=cfg)
    meta = json.loads(paths["metadata"].read_text())

    assert set(meta) == {
        "tool_version",
        "iso",
        "mode",
        "lmp_kind",
        "config",
        "solves",
    }
    assert meta["lmp_kind"] == LMP_KIND_HOURLY  # _sweep() default (HP-01)
    assert len(meta["solves"]) == len(sweep.results)
    for solve, r in zip(meta["solves"], sweep.results):
        assert set(solve) == {"setpoint", "status", "matching_pct", "premium_per_mwh"}
        assert solve["status"] == r.status
        assert np.isclose(solve["matching_pct"], r.matching_pct)
    # every PortfolioConfig field is present in the serialized config
    assert set(meta["config"]) == {f.name for f in fields(PortfolioConfig)}


def test_summarize_renders_co2_column_when_nonzero() -> None:
    _, sweep = _sweep(co2_rate=0.4)
    text = summarize(sweep)
    assert "residualCO2(t)" in text


def test_summarize_omits_co2_column_when_zero() -> None:
    _, sweep = _sweep(co2_rate=0.0)
    text = summarize(sweep)
    assert "residualCO2(t)" not in text
