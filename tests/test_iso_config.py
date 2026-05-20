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

    def test_pjm_has_four_zones(self):
        """PJM defines four aggregated west-to-east zones."""
        pjm = get_iso_config("PJM")
        self.assertEqual(pjm.n_zones, 4)
        self.assertEqual(
            set(pjm.zone_names),
            {"PJM_West", "PJM_East", "PJM_Central", "PJM_South"},
        )

    def test_pjm_has_three_corridor_links(self):
        """PJM models its three binding congestion corridors as links.

        West→East (AP South / 5004-5005), Central→East (Eastern/ChesPenn),
        and West→South (AEP-Dominion) — a connected three-link spanning tree.
        """
        pjm = get_iso_config("PJM")
        self.assertEqual(pjm.n_links, 3)
        corridors = {(link.from_zone, link.to_zone) for link in pjm.links}
        self.assertEqual(
            corridors,
            {
                ("PJM_West", "PJM_East"),
                ("PJM_Central", "PJM_East"),
                ("PJM_West", "PJM_South"),
            },
        )

    def test_pjm_topology_connected(self):
        """Every PJM zone is reachable, so no zone is islanded."""
        pjm = get_iso_config("PJM")
        adjacency: dict[str, set[str]] = {z: set() for z in pjm.zone_names}
        for link in pjm.links:
            adjacency[link.from_zone].add(link.to_zone)
            adjacency[link.to_zone].add(link.from_zone)
        seen = {pjm.zone_names[0]}
        stack = [pjm.zone_names[0]]
        while stack:
            for neighbor in adjacency[stack.pop()]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        self.assertEqual(seen, set(pjm.zone_names))

    def test_pjm_load_shares_sum_to_one(self):
        """PJM zonal-peak load shares sum to 1.0."""
        pjm = get_iso_config("PJM")
        total = sum(zone.load_share for zone in pjm.zones)
        self.assertAlmostEqual(total, 1.0)

    def test_pjm_west_is_largest_zone(self):
        """The western AEP/ComEd belt carries the largest load share."""
        pjm = get_iso_config("PJM")
        largest = max(pjm.zones, key=lambda z: z.load_share)
        self.assertEqual(largest.name, "PJM_West")

    def test_pjm_validates(self):
        """PJM topology passes the consistency check."""
        get_iso_config("PJM").validate_topology()

    def test_pjm_voll_is_2000(self):
        """PJM uses a VOLL of $2,000/MWh (RPM provides capacity revenue)."""
        self.assertEqual(get_iso_config("PJM").voll, 2000.0)

    def test_nyiso_has_five_zones(self):
        """NYISO aggregates its eleven load zones (A–K) onto five model zones."""
        nyiso = get_iso_config("NYISO")
        self.assertEqual(nyiso.n_zones, 5)
        self.assertEqual(
            set(nyiso.zone_names),
            {
                "Upstate_West",
                "Capital_Hudson",
                "Lower_Hudson",
                "NYC",
                "Long_Island",
            },
        )

    def test_nyiso_has_four_links(self):
        """NYISO chains the four binding interfaces west-to-south."""
        nyiso = get_iso_config("NYISO")
        self.assertEqual(nyiso.n_links, 4)

    def test_nyiso_validates(self):
        """NYISO topology passes the consistency check."""
        get_iso_config("NYISO").validate_topology()

    def test_nyiso_load_shares_sum_to_one(self):
        """NYISO zone load shares sum to 1.0."""
        nyiso = get_iso_config("NYISO")
        total = sum(zone.load_share for zone in nyiso.zones)
        self.assertAlmostEqual(total, 1.0)

    def test_nyiso_downstate_import_chain_tightens(self):
        """The import path tightens toward the downstate load pockets.

        The defining feature of NYISO topology is that the NYC (J) and Long
        Island (K) pockets sit behind progressively tighter interfaces, so
        the link into NYC must be no wider than the one feeding it, and the
        Long Island import must be the tightest of all.
        """
        nyiso = get_iso_config("NYISO")
        ttc = {(lk.from_zone, lk.to_zone): lk.ttc_mw for lk in nyiso.links}
        dunwoodie_south = ttc[("Lower_Hudson", "NYC")]
        upny_seny = ttc[("Capital_Hudson", "Lower_Hudson")]
        li_import = ttc[("NYC", "Long_Island")]
        self.assertLessEqual(dunwoodie_south, upny_seny)
        self.assertLess(li_import, dunwoodie_south)

    def test_nyiso_voll_is_2000(self):
        """NYISO uses a VOLL of $2,000/MWh (ICAP provides capacity revenue)."""
        self.assertEqual(get_iso_config("NYISO").voll, 2000.0)

    def test_neiso_has_five_zones(self):
        """NEISO defines four load zones plus the HQ import node."""
        neiso = get_iso_config("NEISO")
        self.assertEqual(neiso.n_zones, 5)
        self.assertEqual(
            set(neiso.zone_names),
            {"North", "Central", "Boston", "Connecticut", "HQ_import"},
        )

    def test_neiso_validates(self):
        """NEISO topology passes the consistency check."""
        # get_iso_config already calls validate_topology(); an explicit call
        # documents the Stage-A requirement and fails loudly on regression.
        get_iso_config("NEISO").validate_topology()

    def test_neiso_load_shares_sum_to_one(self):
        """NEISO zone load shares (incl. the zero-load import node) sum to 1.0."""
        neiso = get_iso_config("NEISO")
        total = sum(zone.load_share for zone in neiso.zones)
        self.assertAlmostEqual(total, 1.0)

    def test_neiso_import_node_carries_no_load(self):
        """The HQ import node is not a load zone, so its share is zero."""
        neiso = get_iso_config("NEISO")
        hq = next(z for z in neiso.zones if z.name == "HQ_import")
        self.assertEqual(hq.load_share, 0.0)

    def test_neiso_import_pockets_present(self):
        """The Boston and Connecticut import-pocket links are present.

        Preserving the two structural ISO-NE import pockets is the whole point
        of the zone split, so the topology must carry a link feeding each from
        the Central zone.
        """
        neiso = get_iso_config("NEISO")
        boston = [
            link
            for link in neiso.links
            if {link.from_zone, link.to_zone} == {"Central", "Boston"}
        ]
        connecticut = [
            link
            for link in neiso.links
            if {link.from_zone, link.to_zone} == {"Central", "Connecticut"}
        ]
        self.assertEqual(len(boston), 1)
        self.assertEqual(len(connecticut), 1)

    def test_neiso_north_south_interface_present(self):
        """The North <-> Central (North–South) interface link is present."""
        neiso = get_iso_config("NEISO")
        north_south = [
            link
            for link in neiso.links
            if {link.from_zone, link.to_zone} == {"North", "Central"}
        ]
        self.assertEqual(len(north_south), 1)

    def test_neiso_hq_import_tie_present(self):
        """The Hydro-Québec import node ties into the Boston/NEMA pocket."""
        neiso = get_iso_config("NEISO")
        hq_tie = [
            link
            for link in neiso.links
            if {link.from_zone, link.to_zone} == {"HQ_import", "Boston"}
        ]
        self.assertEqual(len(hq_tie), 1)

    def test_neiso_voll_is_2000(self):
        """NEISO uses a VOLL of $2,000/MWh (ISO-NE energy offer cap)."""
        neiso = get_iso_config("NEISO")
        self.assertEqual(neiso.voll, 2000.0)

    def test_spp_has_two_zones(self):
        """SPP defines two north–south load zones."""
        spp = get_iso_config("SPP")
        self.assertEqual(spp.n_zones, 2)
        self.assertEqual(set(spp.zone_names), {"SPP-North", "SPP-South"})

    def test_spp_validates(self):
        """SPP topology passes the consistency check."""
        # get_iso_config already calls validate_topology(); an explicit call
        # documents the Stage-A requirement and fails loudly on regression.
        get_iso_config("SPP").validate_topology()

    def test_spp_load_shares_sum_to_one(self):
        """SPP zone load shares sum to 1.0."""
        spp = get_iso_config("SPP")
        total = sum(zone.load_share for zone in spp.zones)
        self.assertAlmostEqual(total, 1.0)

    def test_spp_wind_export_corridor_present(self):
        """The defining SPP-North <-> SPP-South wind-export link is present.

        SPP's recurring congestion is moving the wind-rich north/west output
        to load, so the topology must carry the single North<->South corridor.
        """
        spp = get_iso_config("SPP")
        corridor = [
            link
            for link in spp.links
            if {link.from_zone, link.to_zone} == {"SPP-North", "SPP-South"}
        ]
        self.assertEqual(len(corridor), 1)

    def test_spp_voll_is_2000(self):
        """SPP uses a VOLL of $2,000/MWh (FERC Order 831 offer cap)."""
        spp = get_iso_config("SPP")
        self.assertEqual(spp.voll, 2000.0)

    def test_all_links_reference_valid_zones(self):
        """Every link endpoint references a defined zone in each ISO."""
        for iso_name in (
            "ERCOT",
            "CAISO",
            "MISO",
            "SPP",
            "PJM",
            "NYISO",
            "NEISO",
        ):
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
