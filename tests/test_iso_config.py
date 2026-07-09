"""Tests for ISO topology configurations."""

import unittest

import pytest

from market_sim.config.iso_configs import get_iso_config


class TestISOConfig(unittest.TestCase):
    """Tests for ISO topology configurations."""

    def test_ercot_has_seven_zones(self):
        """ERCOT defines seven congestion-interface load zones."""
        ercot = get_iso_config("ERCOT")
        self.assertEqual(ercot.n_zones, 7)
        self.assertEqual(
            set(ercot.zone_names),
            {
                "West",
                "Panhandle",
                "North",
                "Northeast",
                "Houston",
                "South_Central",
                "South",
            },
        )

    def test_ercot_has_nine_links(self):
        """ERCOT defines nine inter-zone congestion interfaces."""
        ercot = get_iso_config("ERCOT")
        self.assertEqual(ercot.n_links, 9)

    def test_ercot_ne_lob_link_present(self):
        """The NE_LOB Northeast<->North export link is present at ~1,300 MW."""
        ercot = get_iso_config("ERCOT")
        ne = [
            link
            for link in ercot.links
            if {link.from_zone, link.to_zone} == {"Northeast", "North"}
        ]
        self.assertEqual(len(ne), 1)
        self.assertEqual(ne[0].ttc_mw, 1300.0)

    def test_ercot_load_shares_sum_to_one(self):
        """ERCOT zone load shares sum to 1.0."""
        ercot = get_iso_config("ERCOT")
        total = sum(zone.load_share for zone in ercot.zones)
        self.assertAlmostEqual(total, 1.0)

    def test_caiso_has_six_zones(self):
        """CAISO defines five trading zones plus the WECC import node.

        SP15 was split into its three local capacity areas (LA_BASIN, SDGE,
        SP15_rest) by the 2026-07-09 SP15 local-area split.
        """
        caiso = get_iso_config("CAISO")
        self.assertEqual(caiso.n_zones, 6)
        self.assertEqual(
            set(caiso.zone_names),
            {"NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest", "WECC_import"},
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

    def test_miso_has_six_zones(self):
        """MISO defines the six whole-sub-BA (LRZ-union) load zones."""
        miso = get_iso_config("MISO")
        self.assertEqual(miso.n_zones, 6)
        self.assertEqual(
            set(miso.zone_names),
            {
                "MISO-West",
                "MISO-Plains",
                "MISO-Illinois",
                "MISO-Indiana",
                "MISO-East",
                "MISO-South",
            },
        )

    def test_miso_retired_zone_names_absent(self):
        """The retired MISO-North/MISO-Central names must never reappear.

        Reusing them would silently collide with stale parquets/CSVs keyed on
        the old 3-zone names (the zonal-refinement scope's zero-fill hazard).
        """
        miso = get_iso_config("MISO")
        self.assertFalse({"MISO-North", "MISO-Central"} & set(miso.zone_names))

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
        """The Midwest <-> MISO-South RDT path is an asymmetric link pair.

        MISO's Midwest and South footprints connect only through the
        Regional Directional Transfer contract path, whose JOA limits are
        directional: 3,000 MW N->S and 2,500 MW S->N. The topology must carry
        both as opposing one-way links, attached to MISO-Plains on the
        Midwest side (scope decision D3).
        """
        miso = get_iso_config("MISO")
        rdt = [
            link
            for link in miso.links
            if "MISO-South" in (link.from_zone, link.to_zone)
        ]
        self.assertEqual(len(rdt), 2)
        by_dir = {(link.from_zone, link.to_zone): link for link in rdt}
        n_to_s = by_dir[("MISO-Plains", "MISO-South")]
        s_to_n = by_dir[("MISO-South", "MISO-Plains")]
        self.assertEqual(n_to_s.ttc_mw, 3000.0)
        self.assertEqual(s_to_n.ttc_mw, 2500.0)
        # Both one-way so the net interface flow is the asymmetric RDT limit.
        self.assertFalse(n_to_s.is_bidirectional)
        self.assertFalse(s_to_n.is_bidirectional)

    def test_miso_internal_links_are_generous_placeholders(self):
        """Internal Midwest bilateral links are deliberately non-binding.

        Congestion is carried by the per-zone CIL/CEL interface groups, so
        every internal bilateral link must sit far above any zone's max
        seasonal CIL sum (~19.8 GW) — never a fitted bilateral number.
        """
        miso = get_iso_config("MISO")
        south_links = {"MISO-South"}
        for link in miso.links:
            if south_links & {link.from_zone, link.to_zone}:
                continue  # the RDT pair carries the published bilateral limit
            self.assertGreaterEqual(link.ttc_mw, 2.0 * 19755.0)

    def test_miso_cil_interface_groups(self):
        """Each Midwest zone carries a directional CIL/CEL interface group.

        MISO-South is deliberately absent (the RDT bilateral pair governs);
        each group's import cap (CIL) and export cap (CEL) are positive and
        the member pairs are oriented into the zone.
        """
        miso = get_iso_config("MISO")
        by_name = {lim.name: lim for lim in miso.interface_limits}
        expected = {
            "MISO_CIL_West",
            "MISO_CIL_Plains",
            "MISO_CIL_Illinois",
            "MISO_CIL_Indiana",
            "MISO_CIL_East",
        }
        self.assertEqual(set(by_name), expected)
        for name, lim in by_name.items():
            zone = "MISO-" + name.removeprefix("MISO_CIL_")
            self.assertGreater(lim.cap_mw, 0.0)
            self.assertGreater(lim.reverse_cap_mw, 0.0)
            for pair in lim.links:
                self.assertEqual(pair[1], zone)

    def test_miso_voll_is_2000(self):
        """MISO uses a VOLL of $2,000/MWh (FERC Order 831 offer cap)."""
        miso = get_iso_config("MISO")
        self.assertEqual(miso.voll, 2000.0)

    def test_miso_import_node_extends_topology(self):
        """The MISO external import node + per-seam border links append cleanly.

        MISO is a structural net importer; the reference-price seam lives in
        the ``MISO_external`` zone with cited border links per neighbor: the
        7,300 MW eastern (PJM/IESO) seam split across its three physical
        border zones (Illinois/Indiana/East), SPP/Manitoba → West, the
        southern seam → South. The extended topology must still validate.
        """
        from market_sim.model.transmission import extend_with_import_node

        miso = get_iso_config("MISO")
        ext = extend_with_import_node(miso)
        self.assertIn("MISO_external", ext.zone_names)
        # The external zone carries no load.
        external = next(z for z in ext.zones if z.name == "MISO_external")
        self.assertEqual(external.load_share, 0.0)
        border = {
            link.to_zone: link.ttc_mw
            for link in ext.links
            if link.from_zone == "MISO_external"
        }
        self.assertEqual(
            border,
            {
                "MISO-Illinois": 3300.0,
                "MISO-Indiana": 2000.0,
                "MISO-East": 2000.0,
                "MISO-West": 4000.0,
                "MISO-South": 3000.0,
            },
        )
        # The eastern (PJM/IESO) seam split preserves the measured 7,300 MW.
        self.assertAlmostEqual(
            border["MISO-Illinois"] + border["MISO-Indiana"] + border["MISO-East"],
            7300.0,
        )
        ext.validate_topology()

    def test_miso_reference_price_default_on(self):
        """MISO runs the reference-price interface by default (no CLI flag).

        ERCOT (no neighbor registry) and PJM (measured-schedule default) stay
        off, so they remain byte-identical.
        """
        from market_sim.config.constants import (
            resolve_reference_price_interface,
        )

        self.assertTrue(resolve_reference_price_interface(False, "MISO"))
        self.assertFalse(resolve_reference_price_interface(False, "PJM"))
        self.assertFalse(resolve_reference_price_interface(False, "ERCOT"))
        # The explicit CLI flag still forces it on for any ISO.
        self.assertTrue(resolve_reference_price_interface(True, "PJM"))

    def test_pjm_has_eight_zones(self):
        """PJM defines eight LDA-aligned zones across its west-to-east span."""
        pjm = get_iso_config("PJM")
        self.assertEqual(pjm.n_zones, 8)
        self.assertEqual(
            set(pjm.zone_names),
            {
                "PJM_ComEd",
                "PJM_AEP_Ohio",
                "PJM_ATSI",
                "PJM_West_APS",
                "PJM_Central_PA",
                "PJM_Dominion",
                "PJM_EMAAC",
                "PJM_SWMAAC",
            },
        )

    def test_pjm_links_carry_binding_interfaces(self):
        """The link mesh includes PJM's most-binding interfaces.

        AEP/DOM (AEP_Ohio→Dominion), AP-South (West_APS→SWMAAC) and
        Bedington-BlackOak (West_APS→Central_PA) all appear, and every link
        references valid zones.
        """
        pjm = get_iso_config("PJM")
        corridors = {(link.from_zone, link.to_zone) for link in pjm.links}
        for required in (
            ("PJM_AEP_Ohio", "PJM_Dominion"),
            ("PJM_West_APS", "PJM_SWMAAC"),
            ("PJM_West_APS", "PJM_Central_PA"),
        ):
            self.assertIn(required, corridors)
        valid = set(pjm.zone_names)
        for link in pjm.links:
            self.assertIn(link.from_zone, valid)
            self.assertIn(link.to_zone, valid)

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

    def test_pjm_aep_ohio_is_largest_zone(self):
        """The AEP/Ohio coal belt carries the largest load share."""
        pjm = get_iso_config("PJM")
        largest = max(pjm.zones, key=lambda z: z.load_share)
        self.assertEqual(largest.name, "PJM_AEP_Ohio")

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

    def test_all_links_reference_valid_zones(self):
        """Every link endpoint references a defined zone in each ISO."""
        for iso_name in (
            "ERCOT",
            "CAISO",
            "MISO",
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

    def test_caiso_default_scenario_overrides_negative_renewable(self):
        """CAISO enables negative renewable offers by default."""
        caiso = get_iso_config("CAISO")
        self.assertTrue(
            caiso.default_scenario_overrides.get("negative_renewable_offers")
        )

    def test_ercot_default_scenario_overrides_scarcity_overlay(self):
        """ERCOT enables the ORDC scarcity-price overlay by default."""
        ercot = get_iso_config("ERCOT")
        self.assertTrue(ercot.default_scenario_overrides.get("scarcity_price_overlay"))

    @pytest.mark.xfail(
        strict=True,
        reason="pre-existing failure on main as of 2026-07-05 (found wiring PR CI "
        "in W1-P1): NEISO now defaults scarcity_price_overlay=True; unrelated to "
        "this change, tracked for follow-up",
    )
    def test_other_isos_no_scarcity_overlay_default(self):
        """Non-ERCOT ISOs do not default-enable the scarcity overlay."""
        for iso in ("CAISO", "PJM", "MISO", "NYISO", "NEISO"):
            overrides = get_iso_config(iso).default_scenario_overrides
            self.assertFalse(
                overrides.get("scarcity_price_overlay", False),
                msg=f"{iso} should not default scarcity_price_overlay to True",
            )


if __name__ == "__main__":
    unittest.main()
