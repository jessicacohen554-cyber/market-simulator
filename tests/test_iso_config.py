"""Tests for ISO topology configurations."""

import unittest

from market_sim.config.iso_configs import get_iso_config


class TestISOConfig(unittest.TestCase):
    """Tests for ISO topology configurations."""

    def test_ercot_has_four_zones(self):
        """ERCOT defines exactly four load zones."""
        ercot = get_iso_config("ERCOT")
        self.assertEqual(ercot.n_zones, 4)

    def test_ercot_load_shares_sum_to_one(self):
        """ERCOT zone load shares sum to 1.0."""
        ercot = get_iso_config("ERCOT")
        total = sum(zone.load_share for zone in ercot.zones)
        self.assertAlmostEqual(total, 1.0)

    def test_caiso_has_two_zones(self):
        """CAISO defines one real load zone plus one import node."""
        caiso = get_iso_config("CAISO")
        self.assertEqual(caiso.n_zones, 2)

    def test_all_links_reference_valid_zones(self):
        """Every link endpoint references a defined zone in each ISO."""
        for iso_name in ("ERCOT", "CAISO"):
            config = get_iso_config(iso_name)
            valid = set(config.zone_names)
            for link in config.links:
                self.assertIn(link.from_zone, valid)
                self.assertIn(link.to_zone, valid)

    def test_unknown_iso_raises_value_error(self):
        """Requesting an unsupported ISO raises ValueError."""
        with self.assertRaises(ValueError):
            get_iso_config("WECC")

    def test_caiso_voll_is_2000(self):
        """CAISO uses a VOLL of $2,000/MWh."""
        caiso = get_iso_config("CAISO")
        self.assertEqual(caiso.voll, 2000.0)


if __name__ == "__main__":
    unittest.main()
