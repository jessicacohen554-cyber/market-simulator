"""The pool frame's member gap guard and measured substitutes (lane NWPP-NEXT).

``_pool_hourly_frame`` used to interpolate a member's ``Demand (Adjusted)``
across a NaN hole of ANY length. For PSEI in 2020 that meant drawing the
member's whole year from about 100 reported hours. A hole is now bridged by
interpolation only up to ``_HOURLY_FRAME_MAX_GAP`` (the single-BA frame's bar).
A longer hole is filled from a measured substitute (FERC 714 load, reconciled
to the member's EIA-930 basis, or the member's own fuel columns); if the
substitute does not close it, the pool is refused. Synthetic cases pin the
mechanics. The hydrated cases pin the measured effect: 2021-2025 are unchanged,
and 2019/2020 are filled.
"""

from __future__ import annotations

import unittest
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import EIA_HOURLY_DIR, FERC_714_DIR
from market_sim.data.eia930 import frames


def _utc() -> pd.DatetimeIndex:
    return pd.date_range("2030-01-01 08:00", periods=HOURS_PER_YEAR, freq="h")


def _member(demand: np.ndarray, net_gen: np.ndarray, fuel: np.ndarray) -> pd.DataFrame:
    utc = _utc()
    return pd.DataFrame(
        {
            "UTC time": utc,
            "Local date": utc - pd.Timedelta(hours=8),
            "Hour": np.arange(HOURS_PER_YEAR) % 24 + 1,
            "Local time": utc - pd.Timedelta(hours=7),
            "Demand forecast": np.full(HOURS_PER_YEAR, np.nan),
            "Demand (Adjusted)": demand,
            "Net generation (Adjusted)": net_gen,
            "NG: NG": fuel,
        }
    )


def _shape() -> np.ndarray:
    t = np.arange(HOURS_PER_YEAR, dtype=float)
    return 1000.0 + 300.0 * np.sin(2 * np.pi * t / 24.0) + 50.0 * np.cos(t / 97.0)


class TestLongestNanRun(unittest.TestCase):
    def test_runs(self):
        self.assertEqual(frames._longest_nan_run(np.array([1.0, 2.0])), 0)
        a = np.array([np.nan, 1, np.nan, np.nan, np.nan, 2, np.nan, np.nan])
        self.assertEqual(frames._longest_nan_run(a), 3)
        self.assertEqual(frames._longest_nan_run(np.full(5, np.nan)), 5)


class TestMeasuredMemberDemand(unittest.TestCase):
    def test_reconciles_level_and_clock_before_filling(self):
        """EIA-930 = 1.2 x FERC one hour later (PSEI's 2019-20 regime): the
        fill must recover the EIA basis, not splice the raw FERC value."""
        utc = _utc()
        ferc = pd.Series(_shape(), index=utc)
        truth = 1.2 * ferc.reindex(utc - pd.Timedelta(hours=1)).to_numpy()
        demand = truth.copy()
        demand[3000:3500] = np.nan
        with mock.patch(
            "market_sim.data.ferc714.load_ferc714_hourly_demand", return_value=ferc
        ):
            out = frames._measured_member_demand(demand, utc, member="X", year=2030)
        np.testing.assert_allclose(out[3000:3500], truth[3000:3500], rtol=1e-9)
        np.testing.assert_array_equal(out[:3000], demand[:3000])

    def test_no_substitute_returns_input(self):
        d = np.array([1.0, np.nan])
        with mock.patch(
            "market_sim.data.ferc714.load_ferc714_hourly_demand", return_value=None
        ):
            out = frames._measured_member_demand(d, _utc()[:2], member="X", year=2030)
        self.assertIs(out, d)


class TestPoolGapGuard(unittest.TestCase):
    """A synthetic two-member pool through the real ``_pool_hourly_frame``."""

    def _pool(self, psei_demand, psei_ng, psei_fuel, ferc=None):
        base = _shape()
        members = {
            "CLK": _member(base, base, base),
            "MEM": _member(psei_demand, psei_ng, psei_fuel),
        }
        frames._pool_hourly_frame.cache_clear()
        with (
            mock.patch.dict(frames._POOL_CLOCK_BA, {"TPOOL": "CLK"}),
            mock.patch.object(frames, "_pool_member_frames", return_value=members),
            mock.patch(
                "market_sim.data.ferc714.load_ferc714_hourly_demand", return_value=ferc
            ),
        ):
            out = frames._pool_hourly_frame("TPOOL", 2030)
        frames._pool_hourly_frame.cache_clear()
        return out

    def test_gap_at_the_bar_is_still_interpolated(self):
        d = _shape()
        d[100 : 100 + frames._HOURLY_FRAME_MAX_GAP] = np.nan
        out = self._pool(d, _shape(), _shape())
        self.assertIsNotNone(out)
        self.assertFalse(np.isnan(out["Demand"].to_numpy()).any())

    def test_gap_over_the_bar_without_substitute_refuses(self):
        d = _shape()
        d[100 : 101 + frames._HOURLY_FRAME_MAX_GAP] = np.nan
        with self.assertLogs("market_sim.data.eia_loader", level="ERROR"):
            out = self._pool(d, _shape(), _shape())
        self.assertIsNone(out)

    def test_mostly_missing_member_is_refused_not_fabricated(self):
        """The PSEI-2020 shape: ~100 reported hours of 8,760."""
        d = np.full(HOURS_PER_YEAR, np.nan)
        d[::90] = 1000.0
        self.assertIsNone(self._pool(d, _shape(), _shape()))

    def test_gap_over_the_bar_takes_the_measured_substitute(self):
        d = _shape()
        d[100:400] = np.nan
        ferc = pd.Series(_shape(), index=_utc())
        out = self._pool(d, _shape(), _shape(), ferc=ferc)
        self.assertIsNotNone(out)
        np.testing.assert_allclose(out["Demand"].to_numpy(), 2 * _shape())

    def test_net_generation_gap_is_filled_from_fuel_columns(self):
        ng = _shape()
        ng[100:400] = np.nan
        out = self._pool(_shape(), ng, 0.5 * _shape())
        self.assertIsNotNone(out)
        got = out["Net generation"].to_numpy()
        # CLK contributes _shape() everywhere; MEM its fuel sum in the hole.
        np.testing.assert_allclose(got[100:400], 1.5 * _shape()[100:400])
        np.testing.assert_allclose(got[:100], 2 * _shape()[:100])

    def test_net_generation_gap_without_fuel_refuses(self):
        ng = _shape()
        ng[100:400] = np.nan
        fuel = _shape()
        fuel[100:400] = np.nan
        self.assertIsNone(self._pool(_shape(), ng, fuel))


def _hydrated() -> bool:
    return (EIA_HOURLY_DIR / "PSEI hourly.parquet").exists() and (
        FERC_714_DIR / "psei_hourly_planning_area_demand_2018_2024.csv"
    ).exists()


@unittest.skipUnless(_hydrated(), "NWPP member extracts / FERC 714 not hydrated")
class TestMeasuredEffect(unittest.TestCase):
    def test_2020_assembles_on_the_reconciled_basis(self):
        """Pre-guard, PSEI 2020 was drawn through ~100 points; now it is FERC
        714 x the member's own 2020 EIA/FERC ratio at the measured -1 h clock.

        270.30 since lane NWPP-NEXT-2: PSEI's double-booked Colstrip share
        (``NG: COL``, 2.15 TWh in 2020) is removed from its NG and Demand
        before the ratio is measured, so the ratio is 1.06 rather than 1.19
        (was 273.37 on the double-booked basis)."""
        frames._pool_hourly_frame.cache_clear()
        frame = frames._pool_hourly_frame("NWPP", 2020)
        self.assertIsNotNone(frame)
        twh = float(frame["Demand"].sum()) / 1e6
        self.assertAlmostEqual(twh, 270.30, delta=0.05)

    def test_2019_psei_gap_is_filled_not_interpolated(self):
        frames._pool_hourly_frame.cache_clear()
        with self.assertLogs("market_sim.data.eia_loader", level="WARNING") as logs:
            frame = frames._pool_hourly_frame("NWPP", 2019)
        self.assertIsNotNone(frame)
        self.assertTrue(
            any("PSEI EIA-930 demand missing 384 h" in line for line in logs.output)
        )

    def test_2021_2025_have_no_member_gap_over_the_bar(self):
        """The guard is inert where the keeper's scored years live."""
        for year in range(2021, 2026):
            members = frames._pool_member_frames("NWPP", year)
            for ba, df in members.items():
                if ba in frames._POOL_GENERATION_ONLY_BAS:
                    continue
                for col in ("Demand (Adjusted)", "Net generation (Adjusted)"):
                    run = frames._longest_nan_run(df[col].to_numpy(dtype=float))
                    self.assertLessEqual(
                        run, frames._HOURLY_FRAME_MAX_GAP, (year, ba, col)
                    )


if __name__ == "__main__":
    unittest.main()
