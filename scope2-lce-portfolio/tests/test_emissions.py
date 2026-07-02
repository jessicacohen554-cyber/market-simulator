"""Tests for the per-ISO marginal CO2 table and config resolution (ADR 0007)."""

import numpy as np

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.emissions import (
    DEFAULT_MARGINAL_CO2_TABLE,
    apply_marginal_co2,
    load_marginal_co2,
    resolve_marginal_co2_rate,
)
from lce_portfolio.lp import build_and_solve

from conftest import daytime_solar_cf, solar_only

EXPECTED_ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")


def test_table_has_all_six_isos_with_positive_rates_and_notes() -> None:
    """The marginal-CO2 table has one row per registered ISO (ADR 0007)."""
    for iso in EXPECTED_ISOS:
        rate = load_marginal_co2(iso)
        assert rate is not None, f"missing marginal_co2 row for {iso}"
        assert rate > 0.0

    import csv

    text = DEFAULT_MARGINAL_CO2_TABLE.read_text()
    body = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )
    rows = list(csv.DictReader(body.splitlines()))
    assert {r["iso"] for r in rows} == set(EXPECTED_ISOS)
    for row in rows:
        assert row["notes"].strip(), f"empty notes for {row['iso']}"
        assert row["basis"].strip()


def test_loader_unknown_iso_returns_none() -> None:
    """An ISO absent from the table (e.g. SAMPLE) resolves to None, not KeyError."""
    assert load_marginal_co2("SAMPLE") is None
    assert load_marginal_co2("NOT_A_REAL_ISO") is None


def test_resolution_precedence_explicit_beats_table_beats_zero() -> None:
    """Explicit config value > table value > 0 (ADR 0007 precedence)."""
    # explicit override wins even though ERCOT has a table entry
    explicit_cfg = PortfolioConfig(iso="ERCOT", marginal_co2_ton_per_mwh=1.234)
    assert resolve_marginal_co2_rate(explicit_cfg) == 1.234

    # no explicit value -> falls back to the table
    table_cfg = PortfolioConfig(iso="ERCOT")
    table_rate = load_marginal_co2("ERCOT")
    assert resolve_marginal_co2_rate(table_cfg) == table_rate
    assert table_rate is not None and table_rate > 0.0

    # unknown ISO, no explicit value -> 0 (reporting off)
    off_cfg = PortfolioConfig(iso="SAMPLE")
    assert resolve_marginal_co2_rate(off_cfg) == 0.0


def test_apply_marginal_co2_injects_resolved_rate_via_with_overrides() -> None:
    """apply_marginal_co2 returns a config carrying the resolved scalar."""
    cfg = PortfolioConfig(iso="CAISO")
    resolved = apply_marginal_co2(cfg)
    assert resolved is not cfg  # frozen dataclass -> new instance
    assert resolved.marginal_co2_ton_per_mwh == load_marginal_co2("CAISO")
    # every other field is untouched
    assert resolved.iso == cfg.iso
    assert resolved.mode == cfg.mode


def test_end_to_end_solve_reports_nonzero_residual_co2_via_table() -> None:
    """A tiny solve for a real ISO gains a nonzero residual_co2_tons (ADR 0007).

    Solar-only, daytime-only CF over 24h leaves night-hour grid_buy > 0; with
    the config resolved through the ERCOT table entry the LP's own
    ``residual_co2_tons = grid_buy_mwh * rate`` (lp.py) should be positive and
    match the resolved rate exactly.
    """
    T = 24
    res = solar_only()
    cf = daytime_solar_cf(res.n_res, T)
    load = np.full(T, 100.0)
    lmp = np.full(T, 50.0)

    cfg = apply_marginal_co2(PortfolioConfig(iso="ERCOT", hours=T, mode="premium_cap"))
    assert cfg.marginal_co2_ton_per_mwh > 0.0

    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1e6)

    assert r.status == "Optimal"
    assert r.grid_buy_mwh > 0.0
    assert r.residual_co2_tons > 0.0
    assert np.isclose(
        r.residual_co2_tons, r.grid_buy_mwh * cfg.marginal_co2_ton_per_mwh
    )
