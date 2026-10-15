"""The UC commitment demand data layer (``data/commitment_demand.py``, lane UC-1-FIX-7).

Trivial cases first: the data-QA cut on synthetic hours, the zone mapping on
a two-zone toy, the forward season x hour lookup, then the dispatcher.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import market_sim.data.commitment_demand as cd
from market_sim.config.constants import (
    COMMITMENT_DF_DATA_ERROR_FRACTION,
    HOURS_PER_YEAR,
)
from market_sim.config.scenarios import UC_COMMITMENT_DEMAND_SOURCES


def test_sources_in_step_with_the_config():
    assert cd.COMMITMENT_DEMAND_SOURCES == UC_COMMITMENT_DEMAND_SOURCES


def test_qa_drops_missing_and_gross_errors():
    actual = np.array([100.0, 100.0, 100.0, 100.0, 0.0, 100.0])
    forecast = np.array(
        [
            103.0,
            97.0,
            100.0 + 100.0 * COMMITMENT_DF_DATA_ERROR_FRACTION,
            170.0,
            5.0,
            np.nan,
        ]
    )
    err, valid = cd.qa_forecast_error(forecast, actual)
    assert valid.tolist() == [True, True, True, False, False, False]
    np.testing.assert_allclose(err, [3.0, -3.0, 30.0, 0.0, 0.0, 0.0])


def test_backcast_increment_uses_the_loader_zone_weights_and_losses(monkeypatch):
    """The BA error is split by the demand loader's own weights and grossed up
    by the same loss factor -- the forecast mapped to zones as the actual is."""
    import market_sim.data.eia930 as e9

    err = np.zeros(HOURS_PER_YEAR)
    err[:3] = [100.0, -40.0, 0.0]
    monkeypatch.setattr(cd, "ba_forecast_error_mw", lambda iso, year: (err, 7))
    w = np.vstack([np.full(HOURS_PER_YEAR, 0.25), np.full(HOURS_PER_YEAR, 0.75)])
    monkeypatch.setattr(e9, "load_zone_weights", lambda *a, **k: w)
    inc, dropped = cd.backcast_commitment_increment(
        "SPP", 2020, None, td_loss_factor=0.1
    )
    assert dropped == 7 and inc.shape == (2, HOURS_PER_YEAR)
    np.testing.assert_allclose(inc[:, 0], [27.5, 82.5])
    np.testing.assert_allclose(inc[:, 1], [-11.0, -33.0])
    np.testing.assert_allclose(inc.sum(axis=0)[:2], [110.0, -44.0])


def test_ba_error_reads_the_hourly_frame(monkeypatch):
    import market_sim.data.eia930 as e9

    frame = pd.DataFrame(
        {
            "Demand": np.full(HOURS_PER_YEAR, 1000.0),
            "Demand forecast": np.r_[
                1050.0, 5000.0, np.full(HOURS_PER_YEAR - 2, 990.0)
            ],
        }
    )
    monkeypatch.setattr(e9, "_eia_hourly_frame_filled", lambda ba, year: frame)
    err, dropped = cd.ba_forecast_error_mw("SPP", 2020)
    assert dropped == 1
    assert err[0] == 50.0 and err[1] == 0.0 and err[2] == -10.0
    monkeypatch.setattr(e9, "_eia_hourly_frame_filled", lambda ba, year: None)
    with pytest.raises(ValueError, match="no EIA-930 hourly frame"):
        cd.ba_forecast_error_mw("SPP", 2020)


def _profile(bias_by_season: dict[str, float]) -> pd.DataFrame:
    rows = [
        dict(season=s, hour_of_day=h, bias_frac=b + h * 1e-4)
        for s, b in bias_by_season.items()
        for h in range(24)
    ]
    return pd.DataFrame(rows)


def test_forward_bias_maps_season_and_hour():
    prof = _profile({"DJF": 0.01, "MAM": 0.02, "JJA": 0.03, "SON": 0.04})
    frac = cd.forward_bias_fraction(prof)
    assert frac.shape == (HOURS_PER_YEAR,)
    assert frac[0] == pytest.approx(0.01)  # Jan 1, 00:00
    assert frac[5] == pytest.approx(0.01 + 5e-4)
    jul1_17 = (31 + 28 + 31 + 30 + 31 + 30) * 24 + 17
    assert frac[jul1_17] == pytest.approx(0.03 + 17e-4)
    assert frac[-1] == pytest.approx(0.01 + 23e-4)  # Dec 31, 23:00
    with pytest.raises(ValueError, match="lacks"):
        cd.forward_bias_fraction(prof[prof.season != "SON"])


def test_dispatcher(monkeypatch):
    demand = np.full((2, 24), 100.0)
    actual = cd.commitment_demand(
        SimpleNamespace(uc_commitment_demand_source="actual"), demand
    )
    assert actual.demand is demand and actual.basis == "actual"

    monkeypatch.setattr(
        cd,
        "load_forecast_error_profile",
        lambda iso: _profile({"DJF": 0.02, "MAM": 0.0, "JJA": 0.0, "SON": 0.0}),
    )
    fwd = cd.commitment_demand(
        SimpleNamespace(
            uc_commitment_demand_source="da_forecast", mode="forecast", iso="SPP"
        ),
        demand,
    )
    assert fwd.basis == "error_profile"
    np.testing.assert_allclose(fwd.demand[:, 0], 102.0)
    np.testing.assert_allclose(fwd.demand[:, 3], 100.0 * (1.02 + 3e-4))
    row = fwd.log_row(demand)
    assert row["increment_min_mw"] == pytest.approx(4.0)
