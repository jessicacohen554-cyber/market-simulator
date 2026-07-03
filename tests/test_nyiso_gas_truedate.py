"""True-date placement of NYISO daily hub-gas quotes + Iroquois print override.

The NYISO daily leg (:func:`_nyiso_hub_daily_gas_prices`) places each measured
Transco Z6 NY trading-day quote on its actual calendar day (interpolating the
non-trading gaps) instead of spreading the month's quote list evenly, so a
cold-snap print lands on the day it happened; the month stays mean-preserving.
Where ≥2 measured Iroquois Z2 prints exist for a month they locally supersede
the reconstruction across the day span they bracket (rule #13), moving the
monthly mean by exactly what the measured prints say.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import fuel as fuel_mod
from market_sim.data.fuel import _nyiso_hub_daily_gas_prices


@pytest.fixture()
def cfg():
    return ScenarioConfig(iso="NYISO", mode="backcast", hours=8760)


def _write_transco(tmp_path, rows):
    p = tmp_path / "transco.csv"
    p.write_text(
        "date,transco_z6_ny_usd_mmbtu,henry_hub_usd_mmbtu\n"
        + "\n".join(f"{d},{v},{v}" for d, v in rows)
        + "\n"
    )
    return p


def test_quote_lands_on_true_calendar_day(cfg, tmp_path, monkeypatch):
    # Three Jan quotes; the spike is on the 20th. Even spreading would put the
    # middle quote on the 16th; true-date placement keeps it on the 20th.
    transco = _write_transco(
        tmp_path,
        [("2024-01-05", 2.0), ("2024-01-20", 20.0), ("2024-01-25", 2.0)],
    )
    monkeypatch.setattr(
        fuel_mod,
        "iso_hub_monthly_gas_prices",
        lambda *a, **k: np.array([6.0] + [np.nan] * 11),
    )
    out = _nyiso_hub_daily_gas_prices(cfg, 2024, transco_path=transco)
    jan = out.reshape(365, 24)[:31, 0]
    assert int(np.argmax(jan)) == 19  # 0-based day index for Jan 20
    # Mean-preserving at the monthly level.
    assert jan.mean() == pytest.approx(6.0, rel=1e-9)


def test_iroquois_prints_supersede_reconstruction(cfg, tmp_path, monkeypatch):
    transco = _write_transco(tmp_path, [("2024-12-05", 3.0), ("2024-12-28", 3.0)])
    iq = tmp_path / "iroquois.csv"
    iq.write_text(
        "date,iroquois_z2_usd_mmbtu,source\n"
        "2024-12-20,9.0,wednesday\n"
        "2024-12-24,15.0,weekly_high\n"
    )
    monkeypatch.setattr(
        fuel_mod,
        "iso_hub_monthly_gas_prices",
        lambda *a, **k: np.array([np.nan] * 11 + [3.16]),
    )
    monkeypatch.setattr(fuel_mod, "IROQUOIS_Z2_DAILY_PATH", iq)
    out = _nyiso_hub_daily_gas_prices(cfg, 2024, transco_path=transco)
    dec = out.reshape(365, 24)[334:, 0]
    # Prints land on their true days and interpolate between (20th..24th).
    assert dec[19] == pytest.approx(9.0)
    assert dec[23] == pytest.approx(15.0)
    assert dec[21] == pytest.approx(12.0)  # midpoint of the bracketed span
    # Outside the bracketed span the reconstruction stands (flat-ish ~3.16).
    assert dec[5] < 4.0
    # The monthly mean RISES with the measured prints (deliberately NOT
    # re-normalized back to the under-read reconstruction level).
    assert dec.mean() > 3.16


def test_single_print_never_relevels_a_month(cfg, tmp_path, monkeypatch):
    transco = _write_transco(tmp_path, [("2024-12-05", 3.0)])
    iq = tmp_path / "iroquois.csv"
    iq.write_text("date,iroquois_z2_usd_mmbtu,source\n2024-12-20,30.0,weekly_high\n")
    monkeypatch.setattr(
        fuel_mod,
        "iso_hub_monthly_gas_prices",
        lambda *a, **k: np.array([np.nan] * 11 + [3.16]),
    )
    monkeypatch.setattr(fuel_mod, "IROQUOIS_Z2_DAILY_PATH", iq)
    out = _nyiso_hub_daily_gas_prices(cfg, 2024, transco_path=transco)
    dec = out.reshape(365, 24)[334:, 0]
    assert dec.mean() == pytest.approx(3.16, rel=1e-9)


def test_reconciled_winter_spread_preserves_measured_annual():
    """Rule #13 reconciliation: annual mean == the committed (SOM) annual."""
    import pandas as pd

    from market_sim.data.fuel import nyiso_reconciled_reference_monthly

    hub = pd.read_csv("data/raw/gas-prices/transco_z6_iroquois_monthly.csv")
    for year in (2023, 2024, 2025):
        rec = nyiso_reconciled_reference_monthly(year)
        assert rec is not None
        iq, tz = rec
        committed = hub[hub.date.str.startswith(f"{year}-")]
        assert iq.mean() == pytest.approx(
            committed.iroquois_z2_usd_mmbtu.mean(), rel=1e-9
        )
        # Winter-concentration: the constrained months carry more premium than
        # the flat construction, unconstrained months less.
        spread = iq - tz
        assert spread.min() >= -1e-9  # premium never negative
        assert spread.max() > spread.mean() * 2  # concentrated, not flat


def test_reconciled_dec_2024_lifts_toward_complex():
    from market_sim.data.fuel import nyiso_reconciled_reference_monthly

    iq, _tz = nyiso_reconciled_reference_monthly(2024)
    assert 6.0 < iq[11] < 9.0  # flat construction read 3.16; complex ~9


def test_zonal_monthly_ratios(cfg):
    from market_sim.data.fuel import nyiso_zonal_gas_ratios_monthly

    off = nyiso_zonal_gas_ratios_monthly(
        cfg.with_overrides(
            nyiso_iroquois_winter_spread=True, nyiso_zonal_gas_basis=True
        ),
        2024,
    )
    assert off is not None
    # Reference zones ride the reference untouched.
    np.testing.assert_allclose(off["Capital_Hudson"], 1.0)
    np.testing.assert_allclose(off["Long_Island"], 1.0)
    # NYC resolves to its own measured hub monthly: ratio < 1 in premium months.
    assert off["NYC"][11] < 0.6  # Dec-2024: Transco 3.30 / Iroquois 7.41
    assert off["NYC"][4] == pytest.approx(1.0, abs=0.15)  # May: no premium
    # Flag off -> None (byte-identical legacy path).
    assert (
        nyiso_zonal_gas_ratios_monthly(
            cfg.with_overrides(nyiso_zonal_gas_basis=True), 2024
        )
        is None
    )
