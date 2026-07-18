"""Incomplete-EIA-923-vintage guard in ``scripts/data/build_calibration_reference``.

The current-year EIA-923 release is a partial monthly survey (~70% of plants),
so it silently under-counts every fuel — most severely the variable renewables,
which have no CEMS backfill. The guard sources wind/solar from EIA-930 (grid
telemetry) per fuel when EIA-923 under-counts them, and stamps the year block
``eia923_incomplete`` only when the *whole* vintage is a partial release. These
tests pin that logic (synthetic, source-independent) plus the live CAISO/ERCOT
behaviour against the committed data.
"""

import importlib.util
import unittest
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "bcr", str(REPO / "scripts" / "data" / "build_calibration_reference.py")
)
bcr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bcr)


class TestIncompleteRenewableFuels(unittest.TestCase):
    """``_incomplete_renewable_fuels`` flags an under-counted renewable, per fuel."""

    def setUp(self):
        self._orig = bcr._eia930_annual_by_fuel
        # EIA-930 grid truth used for every case below.
        bcr._eia930_annual_by_fuel = lambda iso, year: {
            "wind": 20.0,
            "solar": 50.0,
            "net_gen": 200.0,
        }

    def tearDown(self):
        bcr._eia930_annual_by_fuel = self._orig

    def test_complete_vintage_flags_nothing(self):
        raw = {"wind": 19.5, "solar": 49.0, "gas_cc": 60.0}
        self.assertEqual(bcr._incomplete_renewable_fuels("X", 2024, raw), [])

    def test_under_counted_wind_only(self):
        raw = {"wind": 4.0, "solar": 49.0}  # wind 20% of 930, solar fine
        self.assertEqual(bcr._incomplete_renewable_fuels("X", 2025, raw), ["wind"])

    def test_under_counted_solar_only(self):
        raw = {"wind": 19.5, "solar": 30.0}  # solar 60% of 930
        self.assertEqual(bcr._incomplete_renewable_fuels("X", 2025, raw), ["solar"])

    def test_both_under_counted(self):
        raw = {"wind": 4.0, "solar": 30.0}
        self.assertEqual(
            set(bcr._incomplete_renewable_fuels("X", 2025, raw)), {"wind", "solar"}
        )

    def test_missing_vintage_flags_nothing(self):
        """No EIA-923 at all (empty raw) is left missing, not fabricated."""
        self.assertEqual(bcr._incomplete_renewable_fuels("X", 2021, {}), [])


class TestGuardOverride(unittest.TestCase):
    """``_guard_incomplete_eia923`` swaps in EIA-930 only for flagged fuels."""

    def setUp(self):
        self._orig = bcr._eia930_annual_by_fuel
        bcr._eia930_annual_by_fuel = lambda iso, year: {
            "wind": 20.0,
            "solar": 50.0,
            "net_gen": 200.0,
        }

    def tearDown(self):
        bcr._eia930_annual_by_fuel = self._orig

    def test_overrides_only_the_under_counted_fuel(self):
        raw = {"wind": 4.0, "solar": 49.0, "gas_cc": 60.0, "gas_ct": 8.0}
        out = bcr._guard_incomplete_eia923("X", 2025, raw)
        self.assertEqual(out["wind"], 20.0)  # swapped to EIA-930
        self.assertEqual(out["solar"], 49.0)  # left on EIA-923
        self.assertEqual(out["gas_cc"], 60.0)  # thermal untouched
        self.assertEqual(out["gas_ct"], 8.0)

    def test_complete_vintage_is_byte_identical(self):
        raw = {"wind": 19.5, "solar": 49.0, "gas_cc": 60.0}
        self.assertEqual(bcr._guard_incomplete_eia923("X", 2024, raw), raw)

    def test_does_not_mutate_input(self):
        raw = {"wind": 4.0, "solar": 49.0}
        bcr._guard_incomplete_eia923("X", 2025, raw)
        self.assertEqual(raw["wind"], 4.0)


class TestVintageIncompleteFlag(unittest.TestCase):
    """``_eia923_is_incomplete`` fires only on a whole-vintage shortfall."""

    def setUp(self):
        self._frame = bcr._eia923_ba_frame
        self._e930 = bcr._eia930_annual_by_fuel
        bcr._eia930_annual_by_fuel = lambda iso, year: {"net_gen": 200.0}

    def tearDown(self):
        bcr._eia923_ba_frame = self._frame
        bcr._eia930_annual_by_fuel = self._e930

    def _frame_with_total_twh(self, twh):
        return pd.DataFrame(
            {"net_gen": [twh * bcr._MWH_PER_TWH], "pm": ["CA"], "fc": ["NG"]}
        )

    def test_full_vintage_not_flagged(self):
        bcr._eia923_ba_frame = lambda iso, year: self._frame_with_total_twh(195.0)
        self.assertFalse(bcr._eia923_is_incomplete("X", 2024))

    def test_partial_vintage_flagged(self):
        # 148 / 200 = 74%, well below the 90% completeness floor.
        bcr._eia923_ba_frame = lambda iso, year: self._frame_with_total_twh(148.0)
        self.assertTrue(bcr._eia923_is_incomplete("X", 2025))

    def test_no_vintage_not_flagged(self):
        bcr._eia923_ba_frame = lambda iso, year: None
        self.assertFalse(bcr._eia923_is_incomplete("X", 2021))


class TestLiveData(unittest.TestCase):
    """Behaviour against the committed EIA-923 / EIA-930 extracts."""

    def test_caiso_2025_wind_sourced_from_eia930(self):
        raw = bcr._eia923_generation_raw("CAISO", 2025)
        guarded = bcr._eia923_generation("CAISO", 2025)
        if not raw:
            self.skipTest("no CAISO 2025 EIA-923 vintage in this checkout")
        self.assertLess(raw["wind"], 10.0)  # truncated survey
        self.assertGreater(guarded["wind"], 15.0)  # EIA-930 grid total
        self.assertTrue(bcr._eia923_is_incomplete("CAISO", 2025))

    def test_ercot_2024_complete_is_byte_identical(self):
        raw = bcr._eia923_generation_raw("ERCOT", 2024)
        if not raw:
            self.skipTest("no ERCOT 2024 EIA-923 vintage in this checkout")
        self.assertEqual(bcr._eia923_generation("ERCOT", 2024), raw)
        self.assertFalse(bcr._eia923_is_incomplete("ERCOT", 2024))


if __name__ == "__main__":
    unittest.main()
