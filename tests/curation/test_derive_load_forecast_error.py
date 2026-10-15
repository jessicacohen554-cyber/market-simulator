"""Tests for the ``load-forecast-error`` frozen derive on synthetic EIA-930 frames.

The EIA-930 frame loader is replaced by tiny synthetic years (a constant
over-forecast in summer afternoons, a QA-failing hour, a missing forecast),
``CLEAN_DIR`` is redirected to a tempdir, and the written partition is checked
against hand arithmetic. Trivial case first (one year), then pooling.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.data import eia930
from market_sim.data.commitment_demand import (
    FORECAST_ERROR_DATATYPE,
    forward_bias_fraction,
    model_hour_season_hod,
)
from scripts.data import derive_load_forecast_error as dlfe
from scripts.lib.clean_io import read_clean
from tests.helpers.base import CleanDirTestCase

SEASON, HOD = model_hour_season_hod()


def _frame(over: float) -> pd.DataFrame:
    """1,000 MW actual; DF = actual x (1 + over) in JJA 14-17 h, exact elsewhere."""
    actual = np.full(HOURS_PER_YEAR, 1000.0)
    df = actual.copy()
    hot = (SEASON == "JJA") & (HOD >= 14) & (HOD <= 17)
    df[hot] *= 1.0 + over
    df[0] = 5000.0  # a unit slip: fails the QA cut
    df[1] = np.nan  # a missing forecast row
    return pd.DataFrame({"Demand": actual, "Demand forecast": df})


class TestDeriveLoadForecastError(CleanDirTestCase):
    def _patch(self, frames: dict[int, pd.DataFrame]) -> None:
        orig = eia930._eia_hourly_frame_filled
        eia930._eia_hourly_frame_filled = lambda ba, y: frames.get(y)
        self.addCleanup(setattr, eia930, "_eia_hourly_frame_filled", orig)

    def test_one_year(self) -> None:
        self._patch({2020: _frame(0.04)})
        written = dlfe.curate(isos=["SPP"], last_year=2021)
        assert len(written) == 1
        out = read_clean(FORECAST_ERROR_DATATYPE, iso="SPP")
        assert len(out) == 4 * 24
        cell = out.set_index(["season", "hour_of_day"])
        assert abs(cell.loc[("JJA", 15), "bias_frac"] - 0.04) < 1e-12
        assert cell.loc[("JJA", 15), "mean_error_mw"] == 40.0
        assert cell.loc[("JJA", 10), "bias_frac"] == 0.0
        # Jan 1 00:00 and 01:00 are excluded (QA / missing), so DJF 0 h and 1 h
        # pool one hour fewer than DJF 2 h.
        assert cell.loc[("DJF", 0), "n_hours"] == cell.loc[("DJF", 2), "n_hours"] - 1
        assert set(out["years"]) == {"2020-2020"} and set(out["ba"]) == {"SWPP"}
        # the forward lookup reads it back onto the model clock
        frac = forward_bias_fraction(out)
        assert abs(frac[(SEASON == "JJA") & (HOD == 16)] - 0.04).max() < 1e-12

    def test_years_pool(self) -> None:
        self._patch({2019: _frame(0.02), 2021: _frame(0.06)})
        dlfe.curate(isos=["SPP"], last_year=2022)
        out = read_clean(FORECAST_ERROR_DATATYPE, iso="SPP").set_index(
            ["season", "hour_of_day"]
        )
        assert abs(out.loc[("JJA", 14), "bias_frac"] - 0.04) < 1e-12
        assert set(out["years"]) == {"2019-2021"}

    def test_no_forecast_writes_nothing(self) -> None:
        self._patch({})
        assert dlfe.curate(isos=["SPP"], last_year=2021) == []
