"""Tests for the EIA-930 demand and generation loaders."""

import unittest

import numpy as np

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.eia_loader import (
    load_demand,
    load_demand_meta,
    load_generation_profiles,
)

_TEST_YEAR = 2024

# Reference peak demand bands (MW), from EIA-930: ERCOT ~85,544 MW,
# CAISO ~47,571 MW for 2024.
_ERCOT_PEAK_RANGE = (80_000.0, 90_000.0)
_CAISO_PEAK_RANGE = (45_000.0, 50_000.0)


class TestEIALoader(unittest.TestCase):
    """Tests for the EIA-930 demand and generation loaders."""

    def test_load_demand_ercot_shape(self):
        """ERCOT demand spans its six zones over a full year."""
        n_zones = get_iso_config("ERCOT").n_zones
        demand = load_demand("ERCOT", _TEST_YEAR)
        self.assertEqual(demand.shape, (n_zones, HOURS_PER_YEAR))

    def test_load_demand_caiso_shape_and_import_zone(self):
        """CAISO has two zones; the WECC_import node carries no load."""
        demand = load_demand("CAISO", _TEST_YEAR)
        self.assertEqual(demand.shape, (2, HOURS_PER_YEAR))
        self.assertTrue(np.all(demand[1] == 0.0))

    def test_load_demand_no_nan(self):
        """Allocated zonal demand contains no NaN values."""
        for iso in ("ERCOT", "CAISO"):
            self.assertFalse(np.isnan(load_demand(iso, _TEST_YEAR)).any())

    def test_ercot_peak_in_reference_band(self):
        """ERCOT peak (summed across zones) matches the EIA reference."""
        demand = load_demand("ERCOT", _TEST_YEAR)
        peak = demand.sum(axis=0).max()
        self.assertGreaterEqual(peak, _ERCOT_PEAK_RANGE[0])
        self.assertLessEqual(peak, _ERCOT_PEAK_RANGE[1])

    def test_caiso_peak_in_reference_band(self):
        """CAISO peak (summed across zones) matches the EIA reference."""
        demand = load_demand("CAISO", _TEST_YEAR)
        peak = demand.sum(axis=0).max()
        self.assertGreaterEqual(peak, _CAISO_PEAK_RANGE[0])
        self.assertLessEqual(peak, _CAISO_PEAK_RANGE[1])

    def test_zone_rows_sum_to_total_iso_demand(self):
        """Zonal demand rows are a consistent load-share split of the total."""
        iso_config = get_iso_config("ERCOT")
        demand = load_demand("ERCOT", _TEST_YEAR, iso_config)
        total_share = sum(zone.load_share for zone in iso_config.zones)
        # Each zone's row is its load_share fraction of one system series,
        # so the rows sum to total_share x that series every hour.
        nonzero = [
            (z, zone.load_share)
            for z, zone in enumerate(iso_config.zones)
            if zone.load_share > 0.0
        ]
        system = demand[nonzero[0][0]] / nonzero[0][1]
        for z, share in nonzero:
            np.testing.assert_allclose(demand[z], share * system, rtol=1e-9)
        np.testing.assert_allclose(
            demand.sum(axis=0), total_share * system, rtol=1e-9
        )

    def test_load_demand_meta_keys(self):
        """Demand metadata exposes the expected summary statistics."""
        meta = load_demand_meta("ERCOT", _TEST_YEAR)
        self.assertEqual(
            set(meta), {"peak_mw", "min_mw", "avg_mw", "total_annual_mwh"}
        )
        self.assertGreater(meta["peak_mw"], meta["avg_mw"])
        self.assertGreater(meta["avg_mw"], meta["min_mw"])

    def test_load_generation_profiles_filtered(self):
        """Generation profiles are filtered to the requested ISO and year."""
        profiles = load_generation_profiles("ERCOT", _TEST_YEAR)
        self.assertFalse(profiles.empty)
        self.assertTrue((profiles["iso"] == "ERCOT").all())
        self.assertTrue((profiles["year"] == _TEST_YEAR).all())


if __name__ == "__main__":
    unittest.main()
