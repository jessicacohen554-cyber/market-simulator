"""Tests for the EIA-930 demand and generation loaders."""

import unittest

import numpy as np

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.eia_loader import (
    ercot_zonal_load_shares,
    load_demand,
    load_demand_meta,
    load_ercot_battery_gen,
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
        """CAISO spans its four zones; the WECC_import node carries no load."""
        caiso = get_iso_config("CAISO")
        demand = load_demand("CAISO", _TEST_YEAR)
        self.assertEqual(demand.shape, (caiso.n_zones, HOURS_PER_YEAR))
        wecc = caiso.zone_names.index("WECC_import")
        self.assertTrue(np.all(demand[wecc] == 0.0))

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

    def test_caiso_zone_rows_are_static_share_split(self):
        """CAISO (no per-zone file) splits one series by constant load shares."""
        iso_config = get_iso_config("CAISO")
        demand = load_demand("CAISO", _TEST_YEAR, iso_config)
        # Each zone's row is its load_share fraction of one system series,
        # so the rows are constant multiples of each other every hour.
        nonzero = [
            (z, zone.load_share)
            for z, zone in enumerate(iso_config.zones)
            if zone.load_share > 0.0
        ]
        system = demand[nonzero[0][0]] / nonzero[0][1]
        for z, share in nonzero:
            np.testing.assert_allclose(demand[z], share * system, rtol=1e-9)

    def test_ercot_zonal_shares_sum_to_one(self):
        """ERCOT per-zone hourly shares are fractions summing to 1.0 each hour."""
        zone_names = get_iso_config("ERCOT").zone_names
        shares = ercot_zonal_load_shares(_TEST_YEAR, zone_names)
        self.assertIsNotNone(shares)
        self.assertEqual(shares.shape, (len(zone_names), HOURS_PER_YEAR))
        np.testing.assert_allclose(shares.sum(axis=0), 1.0, rtol=1e-9)
        # ERCOT has no Panhandle weather zone, so that model zone gets no load.
        self.assertTrue(np.all(shares[zone_names.index("Panhandle")] == 0.0))

    def test_ercot_zones_have_distinct_hourly_shapes(self):
        """Each ERCOT zone gets its own measured shape, not one scaled curve.

        The single-curve allocation made every zone a constant multiple of the
        system series (identical normalized shape); the native-load split gives
        zones distinct shapes, so their hourly fractions actually move.
        """
        iso_config = get_iso_config("ERCOT")
        demand = load_demand("ERCOT", _TEST_YEAR, iso_config)
        total = demand.sum(axis=0)
        # The rows still sum to the system series every hour (shares sum to 1).
        self.assertGreater(total.min(), 0.0)
        # West (hot, wind-belt) and Houston (coastal) no longer track a single
        # shape: their share of system load varies hour to hour.
        west = demand[iso_config.zone_names.index("West")] / total
        houston = demand[iso_config.zone_names.index("Houston")] / total
        self.assertGreater(west.std(), 1e-3)
        self.assertGreater(houston.std(), 1e-3)

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

    def test_ercot_battery_gen_2025_full_year(self):
        """2025 battery benchmark covers the year with sane magnitudes."""
        bench = load_ercot_battery_gen(2025)
        self.assertIsNotNone(bench)
        dis = bench["battery_discharge"]
        chg = bench["battery_charge"]
        self.assertEqual(dis.shape, (HOURS_PER_YEAR,))
        self.assertEqual(chg.shape, (HOURS_PER_YEAR,))
        # Non-negative wherever reported; charge exceeds discharge (RTE loss).
        self.assertTrue(np.nanmin(dis) >= 0.0)
        self.assertTrue(np.nanmin(chg) >= 0.0)
        self.assertGreater(np.nansum(chg), np.nansum(dis))
        # ERCOT 2025 fleet discharged ~5-6 TWh (EIA-930 BAT series).
        self.assertGreater(np.nansum(dis) / 1e6, 4.0)
        self.assertLess(np.nansum(dis) / 1e6, 7.0)

    def test_ercot_battery_gen_partial_year_keeps_nan(self):
        """2024 (reporting starts mid-year) keeps NaN, never gap-fills."""
        bench = load_ercot_battery_gen(2024)
        self.assertIsNotNone(bench)
        dis = bench["battery_discharge"]
        reported = ~np.isnan(dis)
        self.assertGreater(reported.sum(), 0)
        self.assertLess(reported.sum(), HOURS_PER_YEAR)


if __name__ == "__main__":
    unittest.main()
