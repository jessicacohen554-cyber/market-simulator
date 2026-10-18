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
from tests.helpers.stale_snapshot import disable_stale_snapshot_repair

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
    def setUp(self) -> None:
        super().setUp()
        # Synthetic SWPP frames; the stale-snapshot repair is not under test.
        disable_stale_snapshot_repair(self)

    def _patch(self, frames: dict[int, pd.DataFrame]) -> None:
        orig = eia930._eia_hourly_frame_filled
        eia930._eia_hourly_frame_filled = lambda ba, y: frames.get(y)
        self.addCleanup(setattr, eia930, "_eia_hourly_frame_filled", orig)

    def test_one_year(self) -> None:
        self._patch({2020: _frame(0.04)})
        written = dlfe.curate(isos=["NEISO"], last_year=2021)
        assert len(written) == 1
        out = read_clean(FORECAST_ERROR_DATATYPE, iso="NEISO")
        assert len(out) == 4 * 24
        cell = out.set_index(["season", "hour_of_day"])
        assert abs(cell.loc[("JJA", 15), "bias_frac"] - 0.04) < 1e-12
        assert cell.loc[("JJA", 15), "mean_error_mw"] == 40.0
        assert cell.loc[("JJA", 10), "bias_frac"] == 0.0
        # Jan 1 00:00 and 01:00 are excluded (QA / missing), so DJF 0 h and 1 h
        # pool one hour fewer than DJF 2 h.
        assert cell.loc[("DJF", 0), "n_hours"] == cell.loc[("DJF", 2), "n_hours"] - 1
        assert set(out["years"]) == {"2020-2020"} and set(out["ba"]) == {"ISNE"}
        assert set(out["basis"]) == {"eia930_da_forecast"}
        # the forward lookup reads it back onto the model clock
        frac = forward_bias_fraction(out)
        assert abs(frac[(SEASON == "JJA") & (HOD == 16)] - 0.04).max() < 1e-12

    def test_years_pool(self) -> None:
        self._patch({2019: _frame(0.02), 2021: _frame(0.06)})
        dlfe.curate(isos=["NEISO"], last_year=2022)
        out = read_clean(FORECAST_ERROR_DATATYPE, iso="NEISO").set_index(
            ["season", "hour_of_day"]
        )
        assert abs(out.loc[("JJA", 14), "bias_frac"] - 0.04) < 1e-12
        assert set(out["years"]) == {"2019-2021"}

    def test_no_forecast_writes_nothing(self) -> None:
        self._patch({})
        assert dlfe.curate(isos=["SPP"], last_year=2021) == []

    def test_spp_derives_from_the_mtlf_and_skips_years_without_vintages(self) -> None:
        """R19: SPP's profile is its MTLF at the DA-RUC (the EIA DF, here 10x
        the actual, is never read); a year with no vintage partition is skipped."""
        from market_sim.data import load_forecast_vintages as lfv

        def frame(y: int) -> pd.DataFrame:
            f = _frame(0.0)
            f["Demand forecast"] = 10_000.0
            f["UTC time"] = pd.date_range(
                f"{y}-01-01 06:00", periods=HOURS_PER_YEAR, freq="h"
            )
            return f

        self._patch({2018: frame(2018), 2020: frame(2020)})
        ends = pd.DatetimeIndex(frame(2020)["UTC time"]).tz_localize("UTC")
        vint = pd.DataFrame(
            {
                "area": "SPP",
                "issue_time_utc": pd.Timestamp("2019-12-01", tz="UTC"),
                "interval_end_utc": ends,
                "forecast_mw": 1010.0,
            }
        )
        orig = (lfv.available_years, lfv.load_vintages)
        lfv.available_years = lambda iso: [2019, 2020]
        lfv.load_vintages = lambda iso, years, area=None: vint
        self.addCleanup(setattr, lfv, "available_years", orig[0])
        self.addCleanup(setattr, lfv, "load_vintages", orig[1])
        dlfe.curate(isos=["SPP"], last_year=2021)
        out = read_clean(FORECAST_ERROR_DATATYPE, iso="SPP")
        assert set(out["years"]) == {"2020-2020"}
        assert set(out["basis"]) == {"spp_mtlf_da_ruc"}
        assert np.allclose(out["bias_frac"], 0.01)

    def test_caiso_derives_net_of_storage_charging(self) -> None:
        """R17: CAISO's actual is Demand - max(-NG: OTH, 0)."""
        f = pd.DataFrame(
            {
                "Demand": np.full(HOURS_PER_YEAR, 1000.0),
                "Demand forecast": np.full(HOURS_PER_YEAR, 900.0),
                "NG: OTH": np.full(HOURS_PER_YEAR, -100.0),
            }
        )
        self._patch({2024: f})
        dlfe.curate(isos=["CAISO"], last_year=2024)
        out = read_clean(FORECAST_ERROR_DATATYPE, iso="CAISO")
        assert np.allclose(out["bias_frac"], 0.0) and np.allclose(
            out["mean_error_mw"], 0.0
        )
        assert set(out["basis"]) == {"eia930_da_forecast_net_storage_charging"}
