"""GRID's carried-wind leg on the NWPP served schedule (lane NWPP-47, 2026-09-22).

``envelopes.nwpp_net_interchange`` removes GRID's legs to PNM / SRP / WALC as
Desert-Southwest resources the footprint fleet does not own. Lane NWPP-47
found the PNM leg is not such a resource: it equals GRID's own EIA-930
``NG: WND`` to within 2 MW in every hour, and that wind is carried in the
model's supply (the pool frame's ``NG: WND``). Removing its export while
supplying its generation takes the energy out of the requirement twice.

``ScenarioConfig.nwpp_grid_carried_wind_served`` (GATED default off) serves
that leg. This file pins (1) the default path is byte-identical, (2) the arm
adds back exactly GRID's pool-carried wind, and (3) the measured identity the
arm rests on. ``docs/handoffs/FINDING-nwpp-47-2026-09-22.md`` §2. Reads the
committed extracts; skipped when they are not hydrated.
"""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import EIA_HOURLY_DIR, RAW_DIR

_YEARS = (2023, 2024, 2025)


def _hydrated() -> bool:
    return (EIA_HOURLY_DIR / "GRID hourly.parquet").exists() and (
        RAW_DIR / "eia-930-interchange" / "GRID interchange hourly.parquet"
    ).exists()


@unittest.skipUnless(_hydrated(), "NWPP member extracts not hydrated")
class TestGridCarriedWindServed(unittest.TestCase):
    """The arm serves the export of the wind the pool supply carries — nothing else."""

    def test_default_is_the_nwpp20_construction(self):
        from market_sim.data.eia930.envelopes import (
            _nwpp_grid_external_legs,
            nwpp_net_interchange,
        )
        from market_sim.data.eia930.frames import _eia_hourly_frame_filled

        frame = _eia_hourly_frame_filled("NWPP", 2024)
        expected = frame["Total interchange"].to_numpy(dtype=float) - (
            _nwpp_grid_external_legs(2024, pd.DatetimeIndex(frame["UTC time"]))
        )
        np.testing.assert_array_equal(nwpp_net_interchange(2024), expected)
        np.testing.assert_array_equal(
            nwpp_net_interchange(2024, grid_carried_wind_served=False), expected
        )

    def test_arm_adds_back_exactly_grids_pool_carried_wind(self):
        from market_sim.data.eia930.envelopes import (
            _nwpp_grid_pool_carried_wind,
            nwpp_net_interchange,
        )

        for year in _YEARS:
            base = nwpp_net_interchange(year)
            armed = nwpp_net_interchange(year, grid_carried_wind_served=True)
            wind = _nwpp_grid_pool_carried_wind(year)
            self.assertEqual(wind.shape, (HOURS_PER_YEAR,))
            np.testing.assert_allclose(armed - base, wind, atol=1e-9)
            # 2.073 / 2.179 / 2.002 TWh — FINDING-nwpp-47 §2.
            self.assertGreater(float(wind.sum()) / 1e6, 1.9)
            self.assertLess(float(wind.sum()) / 1e6, 2.3)

    def test_the_pnm_leg_is_grids_wind(self):
        """The measured identity the arm rests on: GRID -> PNM == GRID NG: WND."""
        from market_sim.data.eia930.envelopes import (
            _nwpp_grid_external_legs,
            _nwpp_grid_pool_carried_wind,
        )
        from market_sim.data.eia930.frames import _eia_hourly_frame_filled

        path = RAW_DIR / "eia-930-interchange" / "GRID interchange hourly.parquet"
        legs = pd.read_parquet(path)
        for year in _YEARS:
            utc = pd.DatetimeIndex(_eia_hourly_frame_filled("NWPP", year)["UTC time"])
            only_pnm = legs[legs["diba"] == "PNM"]
            pnm = _pnm_leg_on(only_pnm, utc)
            wind = _nwpp_grid_pool_carried_wind(year)
            self.assertLessEqual(float(np.abs(pnm - wind).max()), 2.0)
            # and it is a strict part of the removed Southwest set
            self.assertLess(
                float(pnm.sum()), float(_nwpp_grid_external_legs(year, utc).sum())
            )


def _pnm_leg_on(leg: pd.DataFrame, utc: pd.DatetimeIndex) -> np.ndarray:
    """Place GRID's PNM leg on the pool's UTC clock, as the envelope reader does."""
    stamps = pd.DatetimeIndex(leg["local_time"])
    try:
        loc = stamps.tz_localize(
            "America/Los_Angeles", ambiguous="infer", nonexistent="shift_forward"
        )
    except Exception:
        loc = stamps.tz_localize(
            "America/Los_Angeles", ambiguous=False, nonexistent="shift_forward"
        )
    series = pd.Series(
        leg["mw"].to_numpy(dtype=float), index=loc.tz_convert("UTC").tz_localize(None)
    )
    series = series[~series.index.duplicated()]
    return series.reindex(utc).fillna(0.0).to_numpy(dtype=float)


if __name__ == "__main__":
    unittest.main()
