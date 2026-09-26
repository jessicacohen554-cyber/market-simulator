"""Tests for the supply-consistent CAISO demand input (caiso-80 Option A).

Exercises ``eia_loader._load_caiso_hourly_demand(supply_consistent=True)``
against the committed derived artifact (skipped when absent): the honest
series must load clean 8760-hour years at the FINDING §6 pre-registered
annual levels, sit BELOW the raw corrupt Demand cell in every year, take
precedence over ``clock_realign``, and leave the flag-off path byte-identical
to the raw cell.
"""

import unittest

import numpy as np

from market_sim.config.paths import (
    CAISO_SUPPLY_CONSISTENT_DEMAND_DIR,
    RAW_DATA_DIR,
)
from market_sim.data.eia_loader import _load_caiso_hourly_demand

_EXTRACT = RAW_DATA_DIR / "eia-930-hourly" / "CISO hourly.parquet"
_ARTIFACT_2024 = (
    CAISO_SUPPLY_CONSISTENT_DEMAND_DIR / "caiso_supply_consistent_demand_2024.csv"
)

# FINDING-caiso80-demand-basis-wedge-2026-07-13 §6 pre-registered annual
# levels (TWh), ±1.5 window (mirrors the derive script's guard).
_EXPECTED_TWH = {2023: (206.2, 209.2), 2024: (210.9, 213.9), 2025: (203.8, 206.8)}


@unittest.skipUnless(
    _EXTRACT.exists() and _ARTIFACT_2024.exists(),
    "CISO extract or supply-consistent artifact not on disk",
)
class TestCaisoSupplyConsistentDemand(unittest.TestCase):
    def test_levels_below_corrupt_cell(self) -> None:
        for year, (lo, hi) in _EXPECTED_TWH.items():
            raw = _load_caiso_hourly_demand(year)
            honest = _load_caiso_hourly_demand(year, supply_consistent=True)
            self.assertEqual(honest.shape[0], 8760)
            self.assertFalse(np.isnan(honest).any())
            self.assertGreater(honest.min(), 0.0)
            total = honest.sum() / 1e6
            self.assertTrue(
                lo <= total <= hi,
                f"{year}: {total:.2f} TWh outside pre-registered [{lo}, {hi}]",
            )
            # The honest series removes the fabricated block + host wedge:
            # strictly below the raw Demand cell in every year.
            self.assertLess(total, raw.sum() / 1e6)

    def test_precedence_over_clock_realign(self) -> None:
        a = _load_caiso_hourly_demand(2023, supply_consistent=True)
        b = _load_caiso_hourly_demand(2023, clock_realign=True, supply_consistent=True)
        np.testing.assert_array_equal(a, b)

    def test_flag_off_byte_identical(self) -> None:
        raw = _load_caiso_hourly_demand(2024)
        off = _load_caiso_hourly_demand(2024, supply_consistent=False)
        np.testing.assert_array_equal(raw, off)

    def test_missing_year_fails_loudly(self) -> None:
        with self.assertRaises(FileNotFoundError):
            _load_caiso_hourly_demand(2018, supply_consistent=True)


if __name__ == "__main__":
    unittest.main()
