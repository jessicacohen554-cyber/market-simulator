"""Tests for ISO topology configurations."""

import unittest


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

    def test_ercot_has_ten_links(self):
        """ERCOT defines ten link rows (nine interfaces; NE is a one-way pair)."""
        ercot = get_iso_config("ERCOT")
        self.assertEqual(ercot.n_links, 10)

    def test_ercot_northeast_link_present(self):
        """The NE boundary is an asymmetric one-way pair (ERCOT-76).

        Export keeps the measured EASTEX (East Texas GTC) limit-at-bind
        (2,300 MW pooled 2023+2024, ercot-234 card Z-A — formerly the
        mis-attributed NE_LOB series' 1,300); import carries the measured
        dark-hour carrying capability (1,788 MW pooled 2023-2025 maximum of
        EAST-zone load minus CAMPD local gross).
        """
        ercot = get_iso_config("ERCOT")
        ne = {
            (link.from_zone, link.to_zone): link
            for link in ercot.links
            if {link.from_zone, link.to_zone} == {"Northeast", "North"}
        }
        self.assertEqual(len(ne), 2)
        exp = ne[("Northeast", "North")]
        imp = ne[("North", "Northeast")]
        self.assertEqual(exp.ttc_mw, 2300.0)
        self.assertFalse(exp.is_bidirectional)
        self.assertEqual(imp.ttc_mw, 1788.0)
        self.assertFalse(imp.is_bidirectional)

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
            "SPP",
            "NWPP",
            "SOCO",
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

    # --- SPP (registered 2026-09-06, lane SPP-20; owner rulings P1-P11) -----

    def test_spp_has_two_zones(self):
        """SPP defines the two P1-ruled zones, North and South, and nothing else.

        No import node (plan §7 G7): the served EIA-930 schedule and the
        default-off neighbour blocks represent the seams.
        """
        spp = get_iso_config("SPP")
        self.assertEqual(spp.n_zones, 2)
        self.assertEqual(set(spp.zone_names), {"SPP-North", "SPP-South"})

    def test_spp_validates(self):
        """SPP topology passes the consistency check (Stage A)."""
        get_iso_config("SPP").validate_topology()

    def test_spp_load_shares_are_the_measured_sub_ba_split(self):
        """Shares = the measured 2023-2025 EIA-930 sub-BA energy split, sum 1.0."""
        spp = get_iso_config("SPP")
        shares = {z.name: z.load_share for z in spp.zones}
        self.assertEqual(shares, {"SPP-North": 0.5125, "SPP-South": 0.4875})
        self.assertAlmostEqual(sum(shares.values()), 1.0)

    def test_spp_single_link_carries_the_spp53_corridor_ttc(self):
        """One symmetric N<->S link whose TTC is SPP-53's derived corridor limit.

        3,400 MW is the binding-hours-weighted median first-contingency
        transfer of the corridor's identified flowgates, built from SPP's own
        2026 effective limits and a shift-factor identification on SPP's own
        2023-25 prices (owner ruling P13; docs/handoffs/PRECOMMIT-spp-53-
        2026-09-07.md §2.1, FINDING-spp-53-2026-09-07.md §4). It replaced
        SPP-20's 48,700 MW Tier-3 placeholder, which could not bind. The
        second assertion pins the property the placeholder lacked: the link
        sits below the residual-blind bound B_plaus = 23,300 MW (North
        non-gas capability minus North minimum load), so it CAN bind. A
        change here is a re-derivation from source data (rule 23), never a
        residual tune.
        """
        spp = get_iso_config("SPP")
        self.assertEqual(spp.n_links, 1)
        link = spp.links[0]
        self.assertEqual((link.from_zone, link.to_zone), ("SPP-North", "SPP-South"))
        self.assertTrue(link.is_bidirectional)
        self.assertEqual(link.ttc_mw, 3400.0)
        self.assertLess(link.ttc_mw, 23300.0)
        self.assertEqual(spp.interface_limits, [])

    def test_spp_voll_is_2000(self):
        """SPP uses the Order 831 cost-verified ceiling, $2,000/MWh (ruling P10)."""
        self.assertEqual(get_iso_config("SPP").voll, 2000.0)

    def test_spp_carries_no_default_overrides(self):
        """Rulings P4/P5: no reserve spec and no scarcity/ORDC seed at registration.

        The scarcity-seed checkpoint above (``["ERCOT", "NEISO"]``) is
        deliberately untouched; this pins SPP's side of it.
        """
        overrides = get_iso_config("SPP").default_scenario_overrides
        self.assertEqual(overrides, {})
        self.assertNotIn("scarcity_price_overlay", overrides)

    # --- NWPP (registered 2026-09-14, lane NWPP-20; owner rulings N1, N3-N8) --

    def test_nwpp_defines_the_five_ruled_whole_ba_zones(self):
        """Card N5: five zones, whole-BA groups, in registration order."""
        nwpp = get_iso_config("NWPP")
        self.assertEqual(nwpp.name, "NWPP")
        self.assertEqual(
            nwpp.zone_names,
            ["NWPP-NW", "NWPP-OR", "NWPP-INLAND", "NWPP-EAST", "NWPP-SNV"],
        )

    def test_nwpp_topology_validates(self):
        get_iso_config("NWPP").validate_topology()

    def test_nwpp_load_shares_are_the_pooled_adjusted_energy_shares(self):
        """Pooled 2023-2025 member Demand (Adjusted) energy shares, sum 1.0."""
        shares = {z.name: z.load_share for z in get_iso_config("NWPP").zones}
        self.assertEqual(
            shares,
            {
                "NWPP-NW": 0.3769,
                "NWPP-OR": 0.1509,
                "NWPP-INLAND": 0.1533,
                "NWPP-EAST": 0.1808,
                "NWPP-SNV": 0.1381,
            },
        )
        self.assertAlmostEqual(sum(shares.values()), 1.0, places=6)

    def test_nwpp_links_carry_the_ruled_path_ratings_as_one_way_pairs(self):
        """Card N5 tiers: Paths 35 / 16 / 20 as paired one-way links, the
        NW<->INLAND aggregation of Paths 8 + 6 + 14, and the NW<->OR Tier-3
        placeholder (a documented absence)."""
        nwpp = get_iso_config("NWPP")
        one_way = {
            (link.from_zone, link.to_zone): link.ttc_mw
            for link in nwpp.links
            if not link.is_bidirectional
        }
        self.assertEqual(one_way[("NWPP-EAST", "NWPP-SNV")], 600.0)  # Path 35 N->S
        self.assertEqual(one_way[("NWPP-SNV", "NWPP-EAST")], 580.0)  # Path 35 S->N
        self.assertEqual(one_way[("NWPP-INLAND", "NWPP-SNV")], 500.0)  # Path 16
        self.assertEqual(one_way[("NWPP-SNV", "NWPP-INLAND")], 360.0)
        self.assertEqual(one_way[("NWPP-INLAND", "NWPP-EAST")], 1600.0)  # Path 20
        self.assertEqual(one_way[("NWPP-EAST", "NWPP-INLAND")], 1250.0)
        self.assertEqual(one_way[("NWPP-INLAND", "NWPP-NW")], 8877.0)  # 8+6+14 E->W
        self.assertEqual(one_way[("NWPP-NW", "NWPP-INLAND")], 2550.0)  # 8+14 W->E
        symmetric = [link for link in nwpp.links if link.is_bidirectional]
        self.assertEqual(len(symmetric), 1)
        self.assertEqual(
            (symmetric[0].from_zone, symmetric[0].to_zone), ("NWPP-NW", "NWPP-OR")
        )
        self.assertEqual(symmetric[0].ttc_mw, 43_600.0)
        # NW<->OR, NW<->EAST, NW<->SNV, OR<->EAST, OR<->SNV, OR<->INLAND:
        # only NW<->OR is a link; the rest are not adjacent in the catalogue.
        pairs = {frozenset((l.from_zone, l.to_zone)) for l in nwpp.links}
        self.assertEqual(len(pairs), 5)
        self.assertNotIn(frozenset(("NWPP-OR", "NWPP-INLAND")), pairs)

    def test_nwpp_voll_is_the_interim_weim_cap(self):
        """PRECOMMIT-nwpp-20 §3.5: $2,000/MWh, declared interim (WEIM hard cap)."""
        self.assertEqual(get_iso_config("NWPP").voll, 2000.0)

    def test_nwpp_carries_no_default_overrides(self):
        """Gate G5 / card N8: no offer-band delta, no scarcity seed, no
        commitment bridge — legacy bins and generic 1.0 bands."""
        overrides = get_iso_config("NWPP").default_scenario_overrides
        self.assertEqual(overrides, {})

    # --- SOCO (registered 2026-09-14, lane SOCO-20; owner cards S1, S3-S7) ---

    def test_soco_has_three_geographic_zones(self):
        """SOCO defines the three S3-ruled zones, named for geography, and no
        import node (SOCO plan §7 G7): the served EIA-930 schedule and eight
        default-off neighbour blocks represent the seams."""
        soco = get_iso_config("SOCO")
        self.assertEqual(soco.n_zones, 3)
        self.assertEqual(set(soco.zone_names), {"SOCO_AL", "SOCO_GA", "SOCO_MS"})
        # Never an operating-company name (card S3 condition (ii)).
        for z in soco.zone_names:
            self.assertNotIn("Power", z)

    def test_soco_validates(self):
        """SOCO topology passes the consistency check (Stage A)."""
        get_iso_config("SOCO").validate_topology()

    def test_soco_static_shares_are_the_fleet_mw_fallback(self):
        """Static shares = the audit §5 row 4 EIA-860 fleet-MW share (GA 41,284.4 /
        AL+FL 24,803.6 / MS 4,577.7 of 70,665.7 MW), a fallback of last resort
        that SOCO-32's FERC-714 derive replaces; sum 1.0."""
        soco = get_iso_config("SOCO")
        shares = {z.name: z.load_share for z in soco.zones}
        self.assertEqual(
            shares, {"SOCO_AL": 0.3510, "SOCO_GA": 0.5842, "SOCO_MS": 0.0648}
        )
        self.assertAlmostEqual(sum(shares.values()), 1.0)

    def test_soco_links_are_tier3_bounds_that_cannot_bind(self):
        """Two symmetric links out of Alabama (AL<->GA, AL<->MS; no GA<->MS), each
        the smaller side's EIA-860 2025 ER winter capability rounded to 100 MW
        — an upper bound on flow in either direction, never a rating (card S3,
        SOCO-12 README §4b: no inter-OpCo limit is published, structurally).
        Lever SOCO-54 owns the real value."""
        soco = get_iso_config("SOCO")
        self.assertEqual(soco.n_links, 2)
        pairs = {(l.from_zone, l.to_zone): l.ttc_mw for l in soco.links}
        self.assertEqual(
            pairs, {("SOCO_AL", "SOCO_GA"): 24400.0, ("SOCO_AL", "SOCO_MS"): 4300.0}
        )
        self.assertTrue(all(l.is_bidirectional for l in soco.links))
        self.assertEqual(soco.interface_limits, [])
        # The bound property: each TTC is at or above the smaller side's whole
        # winter capability (24,446.3 -> 24,400 is the nearest-100 rounding of
        # AL+FL; MS 4,324.6 -> 4,300), i.e. the link is never the binding limit
        # on what that side can physically inject.
        self.assertGreaterEqual(pairs[("SOCO_AL", "SOCO_GA")], 24_400.0)
        self.assertGreaterEqual(pairs[("SOCO_AL", "SOCO_MS")], 4_300.0)

    def test_soco_voll_is_the_ice_class_weighted_economic_value(self):
        """Card S5: DOE/LBNL ICE Calculator 2 cost per unserved kWh at the 2-hour
        duration (residential $5.03 / non-residential $100, 2025$), weighted by
        the EIA-861 2024 BA-SOCO class mix (0.4009 / 0.5991) = $61,927 -> 61,900
        $/MWh. NOT the $2,000 Order 831 offer cap — SOCO takes no offers."""
        voll = get_iso_config("SOCO").voll
        self.assertEqual(voll, 61_900.0)
        self.assertNotEqual(voll, 2000.0)
        self.assertAlmostEqual(0.4009 * 5030.0 + 0.5991 * 100_000.0, 61_927.0, places=0)

    def test_soco_carries_no_default_overrides(self):
        """Card S5: no reserve co-optimisation and no scarcity seed — SOCO clears
        no ancillary-service market. The scarcity-seed checkpoint above is
        deliberately untouched."""
        overrides = get_iso_config("SOCO").default_scenario_overrides
        self.assertEqual(overrides, {})

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

    def test_scarcity_overlay_default_requires_grounded_ordc_params(self):
        """An ISO may default-enable the overlay ONLY with its own ORDC block.

        Re-adjudicated 2026-07-26 (fast-tier §6.3). The original assertion —
        "no non-ERCOT ISO default-enables the scarcity overlay" — was xfailed
        as an uncited "pre-existing failure", but NEISO's default is a
        deliberate, fully-cited structural mechanism: the ISO-NE winter
        scarcity ORDC overlay, parameterized from ISO-NE's own filings (VOLL
        $2,000 = Tariff III.1.10.1A offer cap; MCL 1,200 MW ~ Millstone 3
        largest single contingency; sigma 900 MW = the PAF-study winter
        reserve-error std dev; no PUCT curve shift; no ERCOT OBDRR048 floor).
        Freezing the ERCOT-only list would have blocked exactly that, so the
        invariant is re-cut to what actually matters (rule 5): an ISO that
        default-enables the overlay must carry its OWN grounded ORDC
        parameters rather than silently inheriting ERCOT's.
        """
        required = (
            "ordc_voll",
            "ordc_mcl_mw",
            "ordc_lolp_sigma_mw",
            "ordc_lolp_shift_sigma",
            "ordc_multistep_floor",
        )
        enabled = []
        for iso in ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"):
            overrides = get_iso_config(iso).default_scenario_overrides
            if not overrides.get("scarcity_price_overlay", False):
                continue
            enabled.append(iso)
            if iso == "ERCOT":
                # ERCOT IS the ScenarioConfig ORDC baseline (the curve was built
                # against PUCT's), so it overrides nothing and needs no block.
                continue
            for key in required:
                self.assertIn(
                    key,
                    overrides,
                    msg=f"{iso} default-enables the overlay without {key}",
                )
        # ERCOT and NEISO are the two ISOs with a grounded overlay today; a new
        # one is a deliberate lane decision, and this list is its checkpoint.
        self.assertEqual(sorted(enabled), ["ERCOT", "NEISO"])


if __name__ == "__main__":
    unittest.main()
