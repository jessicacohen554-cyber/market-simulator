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
