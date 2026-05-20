"""Tests for ISO topology configurations."""

import unittest

from market_sim.config.iso_configs import get_iso_config


class TestISOConfig(unittest.TestCase):
    """Tests for ISO topology configurations."""

    def test_ercot_has_six_zones(self):
        """ERCOT defines six congestion-interface load zones."""
        ercot = get_iso_config("ERCOT")
        self.assertEqual(ercot.n_zones, 6)
        self.assertEqual(
            set(ercot.zone_names),
            {"West", "Panhandle", "North", "Houston", "South_Central", "South"},
        )

    def test_ercot_has_eight_links(self):
        """ERCOT defines eight inter-zone congestion interfaces."""
        ercot = get_iso_config("ERCOT")
        self.assertEqual(ercot.n_links, 8)

    def test_ercot_load_shares_sum_to_one(self):
        """ERCOT zone load shares sum to 1.0."""
        ercot = get_iso_config("ERCOT")
        total = sum(zone.load_share for zone in ercot.zones)
        self.assertAlmostEqual(total, 1.0)

    def test_caiso_has_four_zones(self):
        """CAISO defines three trading zones plus the WECC import node."""
        caiso = get_iso_config("CAISO")
        self.assertEqual(caiso.n_zones, 4)
        self.assertEqual(
            set(caiso.zone_names), {"NP15", "ZP26", "SP15", "WECC_import"}
        )

    def test_caiso_validates(self):
        """CAISO topology passes the consistency check."""
        # get_iso_config already calls validate_topology(); an explicit
        # call documents the Stage-A requirement and fails loudly if the
        # links or load shares regress.
        get_iso_config("CAISO").validate_topology()

    def test_caiso_load_shares_sum_to_one(self):
        """CAISO zone load shares (incl. the zero-load import node) sum to 1.0."""
        caiso = get_iso_config("CAISO")
        total = sum(zone.load_share for zone in caiso.zones)
        self.assertAlmostEqual(total, 1.0)

    def test_caiso_import_node_carries_no_load(self):
        """The WECC import node is not a load zone, so its share is zero."""
        caiso = get_iso_config("CAISO")
        wecc = next(z for z in caiso.zones if z.name == "WECC_import")
        self.assertEqual(wecc.load_share, 0.0)

    def test_miso_has_three_zones(self):
        """MISO defines three sub-regional load zones."""
        miso = get_iso_config("MISO")
        self.assertEqual(miso.n_zones, 3)
        self.assertEqual(
            set(miso.zone_names),
            {"MISO-North", "MISO-Central", "MISO-South"},
        )

    def test_miso_validates(self):
        """MISO topology passes the consistency check."""
        # get_iso_config already calls validate_topology(); an explicit call
        # documents the Stage-A requirement and fails loudly on regression.
        get_iso_config("MISO").validate_topology()

    def test_miso_load_shares_sum_to_one(self):
        """MISO zone load shares sum to 1.0."""
        miso = get_iso_config("MISO")
        total = sum(zone.load_share for zone in miso.zones)
        self.assertAlmostEqual(total, 1.0)

    def test_miso_rdt_contract_path_present(self):
        """The defining MISO-Central <-> MISO-South RDT link is present.

        MISO's Midwest and South footprints connect only through the
        Regional Directional Transfer contract path; the topology must carry
        it as a link, seeded at the ~3,000 MW north->south RDT limit.
        """
        miso = get_iso_config("MISO")
        rdt = [
            link
            for link in miso.links
            if {link.from_zone, link.to_zone}
            == {"MISO-Central", "MISO-South"}
        ]
        self.assertEqual(len(rdt), 1)
        self.assertEqual(rdt[0].ttc_mw, 3000.0)

    def test_miso_wind_export_corridor_present(self):
        """The MISO-North <-> MISO-Central wind-export corridor is present."""
        miso = get_iso_config("MISO")
        corridor = [
            link
            for link in miso.links
            if {link.from_zone, link.to_zone}
            == {"MISO-North", "MISO-Central"}
        ]
        self.assertEqual(len(corridor), 1)

    def test_miso_voll_is_2000(self):
        """MISO uses a VOLL of $2,000/MWh (FERC Order 831 offer cap)."""
        miso = get_iso_config("MISO")
        self.assertEqual(miso.voll, 2000.0)

    def test_all_links_reference_valid_zones(self):
        """Every link endpoint references a defined zone in each ISO."""
        for iso_name in ("ERCOT", "CAISO", "MISO"):
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
