"""The NWPP pool frame and served schedule (lane NWPP-20, 2026-09-14).

Pins the demand convention NWPP-10 §1.3 established (Adjusted column, per-
member dropout screen, NO spike screen, AVRN/GRID as 0.0, UTC join onto the
Pacific local year) and the served-interchange construction fixed in
``docs/handoffs/PRECOMMIT-nwpp-20-2026-09-14.md`` §3.4. Reads the committed
per-BA extracts NWPP-11 landed; skipped when they are not hydrated.
"""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import EIA_HOURLY_DIR


def _hydrated() -> bool:
    return (EIA_HOURLY_DIR / "BPAT hourly.parquet").exists() and (
        EIA_HOURLY_DIR / "NEVP hourly.parquet"
    ).exists()


@unittest.skipUnless(_hydrated(), "NWPP member extracts not hydrated")
class TestPoolFrame(unittest.TestCase):
    YEAR = 2024

    @classmethod
    def setUpClass(cls):
        from market_sim.data.eia930.frames import _eia_hourly_frame_filled

        cls.frame = _eia_hourly_frame_filled("NWPP", cls.YEAR)

    def test_pool_frame_has_the_single_ba_shape(self):
        self.assertIsNotNone(self.frame)
        self.assertEqual(len(self.frame), HOURS_PER_YEAR)
        for col in (
            "UTC time",
            "Demand",
            "Net generation",
            "Total interchange",
            "NG: WND",
            "NG: SUN",
            "NG: WAT",
        ):
            self.assertIn(col, self.frame.columns)

    def test_demand_reproduces_the_cleaned_coincident_peak(self):
        """Adjusted column, summed over 17 BAs: 52,564 MW in 2024 (audit §4.2)."""
        demand = self.frame["Demand"].to_numpy(dtype=float)
        self.assertFalse(np.isnan(demand).any())
        self.assertAlmostEqual(float(demand.max()), 52_564.0, places=0)
        self.assertGreater(float(demand.min()), 0.0)

    def test_generation_only_members_add_no_demand(self):
        """AVRN and GRID serve zero load in every hour (NWPP-10 §2 item 4)."""
        for ba in ("AVRN", "GRID"):
            df = pd.read_parquet(EIA_HOURLY_DIR / f"{ba} hourly.parquet")
            self.assertTrue(df["Demand (Adjusted)"].isna().all(), ba)

    def test_interchange_column_is_the_energy_balance_position(self):
        """Σ (NG_adj − D_adj), never Σ member Total interchange (BPAT's is
        over-reported by ~36 TWh in 2024, PRECOMMIT §3.4)."""
        ng = self.frame["Net generation"].to_numpy(dtype=float)
        d = self.frame["Demand"].to_numpy(dtype=float)
        ti = self.frame["Total interchange"].to_numpy(dtype=float)
        np.testing.assert_allclose(ti, ng - d)
        self.assertLess(abs(float(ti.sum()) / 1e6), 10.0)  # ±10 TWh, not +32


@unittest.skipUnless(_hydrated(), "NWPP member extracts not hydrated")
class TestServedSchedule(unittest.TestCase):
    def test_2025_dropout_repair_runs_per_member(self):
        """NEVP posts 17 exact-zero hours in 2025 that a footprint sum can never
        read as zero — the screen must run per member before the sum."""
        from market_sim.data.eia930 import frames
        from market_sim.data.eia930.demand import _load_nwpp_hourly_demand

        # The pool frame is lru-cached, so an earlier test in the same process
        # would have consumed the one-time screen warning: clear every layer.
        frames._pool_hourly_frame.cache_clear()
        frames._eia_hourly_frame.cache_clear()
        frames._eia_hourly_frame_filled.cache_clear()
        with self.assertLogs("market_sim.data.eia_loader", level="WARNING") as logs:
            demand = _load_nwpp_hourly_demand(2025)
        self.assertIsNotNone(demand)
        self.assertTrue(
            any(
                "NEVP 2025" in line and "17 demand-dropout" in line
                for line in logs.output
            )
        )
        self.assertAlmostEqual(float(demand.max()), 50_953.0, places=0)

    def test_served_schedule_removes_grids_southwest_legs(self):
        from market_sim.data.eia930.envelopes import nwpp_net_interchange
        from market_sim.data.eia930.frames import _eia_hourly_frame_filled

        served = nwpp_net_interchange(2024)
        self.assertEqual(served.shape, (HOURS_PER_YEAR,))
        position = _eia_hourly_frame_filled("NWPP", 2024)["Total interchange"].to_numpy(
            dtype=float
        )
        removed = position - served
        # GRID's PNM / SRP / WALC legs: +9.8 TWh of Desert-Southwest export in 2024.
        self.assertGreater(float(removed.sum()) / 1e6, 9.0)
        self.assertLess(float(removed.sum()) / 1e6, 10.5)
        self.assertLess(float(served.sum()) / 1e6, 0.0)  # a net importer in 2024


if __name__ == "__main__":
    unittest.main()
