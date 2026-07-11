"""Tests for the CAISO demand-clock realignment (caiso-75 data fix).

Exercises ``eia_loader._load_caiso_hourly_demand(clock_realign=True)`` against
the real extract (skipped when the parquet is absent): the realignment must be
2023-only, conserve annual energy (it is a clock fix, never a rescale), pull
the misaligned window forward by exactly the measured lag, and leave the
post-window rows untouched.
"""

import unittest

import numpy as np

from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data.eia_loader import (
    _CAISO_DEMAND_CLOCK_LAG_H,
    _load_caiso_hourly_demand,
)

_EXTRACT = RAW_DATA_DIR / "eia-930-hourly" / "CISO hourly.parquet"

# Physical local hours in 2023-01-01..2023-10-31 (304 days, one 23-hour
# spring-forward day) — the realignment window's row count.
_WINDOW_ROWS = 304 * 24 - 1


@unittest.skipUnless(_EXTRACT.exists(), "CISO hourly extract not on disk")
class TestCaisoDemandClockRealign(unittest.TestCase):
    def test_2023_realigned_window_and_seam(self) -> None:
        raw = _load_caiso_hourly_demand(2023)
        fix = _load_caiso_hourly_demand(2023, clock_realign=True)
        self.assertIsNotNone(raw)
        self.assertIsNotNone(fix)
        lag = _CAISO_DEMAND_CLOCK_LAG_H
        n = _WINDOW_ROWS
        # Window rows pulled forward by the measured lag.
        np.testing.assert_allclose(fix[: n - lag], raw[lag:n])
        # Seam hour duplicates the first aligned value.
        np.testing.assert_allclose(fix[n - lag : n], raw[n])
        # Post-window rows untouched.
        np.testing.assert_allclose(fix[n:], raw[n:])
        # Clock fix, not a rescale: annual energy conserved to the seam hour.
        self.assertLess(abs(fix.mean() - raw.mean()), 1.0)

    def test_2024_byte_identical(self) -> None:
        raw = _load_caiso_hourly_demand(2024)
        fix = _load_caiso_hourly_demand(2024, clock_realign=True)
        np.testing.assert_array_equal(raw, fix)


if __name__ == "__main__":
    unittest.main()
