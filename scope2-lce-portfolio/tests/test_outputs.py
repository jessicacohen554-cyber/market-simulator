"""Tests for output tables, run metadata, and derived metrics."""

import json

import numpy as np

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.outputs import (
    build_mix_table,
    frontier_table,
    write_outputs,
)
from lce_portfolio.sweep import run_sweep

from conftest import daytime_solar_cf, solar_plus_battery


def _mini_sweep():
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
    return cfg, run_sweep(cfg, res, load, lmp, cf)


def test_frontier_has_derived_columns() -> None:
    """Frontier table exposes the enriched premium/surplus metrics."""
    _, sweep = _mini_sweep()
    df = frontier_table(sweep)
    for col in (
        "premium_per_year",
        "pct_over_bau",
        "capital_cost",
        "avoided_purchase_cost",
        "surplus_mwh",
        "surplus_revenue",
        "grid_buy_mwh",
        "total_load_mwh",
    ):
        assert col in df.columns
    # total load is consistent and premium_per_year ≈ premium × load
    row = df.iloc[0]
    assert np.isclose(row["total_load_mwh"], 2400.0)
    assert np.isclose(
        row["premium_per_year"],
        row["premium_per_mwh"] * row["total_load_mwh"],
        rtol=1e-4,
    )


def test_write_outputs_and_metadata(tmp_path) -> None:
    """write_outputs writes both Parquet files and, with config, a metadata JSON."""
    cfg, sweep = _mini_sweep()
    paths = write_outputs(sweep, tmp_path, config=cfg)
    assert paths["frontier"].exists() and paths["build_mix"].exists()
    assert paths["metadata"].exists()
    meta = json.loads(paths["metadata"].read_text())
    assert meta["iso"] == cfg.iso
    assert meta["config"]["mode"] == "premium_cap"
    assert len(meta["solves"]) == 2


def test_build_mix_round_trip(tmp_path) -> None:
    """Build-mix table round-trips through Parquet."""
    import pandas as pd

    cfg, sweep = _mini_sweep()
    paths = write_outputs(sweep, tmp_path, config=cfg)
    back = pd.read_parquet(paths["build_mix"])
    assert set(back.columns) == set(build_mix_table(sweep).columns)
    assert (back["build_mw"] >= 0).all()
