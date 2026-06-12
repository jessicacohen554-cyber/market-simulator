"""Tests for the pipe-and-bubble transmission model."""

import unittest

import numpy as np

from market_sim.config.constants import (
    CARB_UNSPECIFIED_IMPORT_EF,
    EXPORT_TRANCHES,
    IMPORT_NODE_LINKS,
    IMPORT_TRANCHES,
    PRICED_INTERCHANGE_DEFAULT_ISOS,
    WECC_IMPORT_EFORD,
    resolve_priced_interchange,
)
from market_sim.config.iso_configs import TransferLink, get_iso_config
from market_sim.data.fleet import (
    Generator,
    assemble_mc,
    generators_to_fleet_arrays,
)
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.transmission import (
    build_export_sinks,
    build_import_generators,
    build_incidence_matrix,
    build_wecc_export_sink,
    build_wecc_import_generators,
    extend_with_import_node,
    get_ttc_array,
    wecc_border_carbon_adder,
)

T = 24  # all transmission tests run a 24-hour horizon


def _fleet(specs, zone_names):
    """Build ``FleetArrays`` from ``(zone, pmax)`` generator specs.

    Generators are lossless (``eford=0``) with ``pmin=0`` so dispatched
    output is bounded only by ``pmax``; marginal costs are supplied
    separately to ``solve_dispatch`` via the ``mc`` argument.
    """
    generators = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone=zone,
            fuel_type="gas_cc",
            pmax_mw=pmax,
            pmin_mw=0.0,
            eford=0.0,
        )
        for i, (zone, pmax) in enumerate(specs)
    ]
    return generators_to_fleet_arrays(generators, zone_names, hours=T)


def _no_renewables(n_zones):
    """Return zero-capacity wind/solar kwargs for ``n_zones`` zones."""
    return dict(
        wind_cf=np.zeros((n_zones, T)),
        wind_cap=np.zeros(n_zones),
        solar_cf=np.zeros((n_zones, T)),
        solar_cap=np.zeros(n_zones),
    )


class TestBuildIncidenceMatrix(unittest.TestCase):
    """Tests for ``build_incidence_matrix``."""

    def test_shape_and_signs(self):
        links = [TransferLink(from_zone="A", to_zone="B", ttc_mw=1000.0)]
        incidence = build_incidence_matrix(links, ["A", "B"])
        self.assertEqual(incidence.shape, (2, 1))
        # from_zone A exports (-1), to_zone B imports (+1).
        np.testing.assert_array_equal(incidence.toarray(), [[-1.0], [1.0]])

    def test_each_link_column_sums_to_zero(self):
        links = [
            TransferLink(from_zone="A", to_zone="B", ttc_mw=100.0),
            TransferLink(from_zone="B", to_zone="C", ttc_mw=200.0),
            TransferLink(from_zone="A", to_zone="C", ttc_mw=300.0),
        ]
        incidence = build_incidence_matrix(links, ["A", "B", "C"])
        self.assertEqual(incidence.shape, (3, 3))
        # Every link withdraws from one zone and injects into another.
        np.testing.assert_array_equal(
            np.asarray(incidence.sum(axis=0)).ravel(), np.zeros(3)
        )

    def test_no_links_gives_empty_columns(self):
        incidence = build_incidence_matrix([], ["A", "B"])
        self.assertEqual(incidence.shape, (2, 0))


class TestGetTtcArray(unittest.TestCase):
    """Tests for ``get_ttc_array``."""

    def test_values_and_order(self):
        links = [
            TransferLink(from_zone="A", to_zone="B", ttc_mw=1000.0),
            TransferLink(from_zone="B", to_zone="C", ttc_mw=2500.0),
        ]
        np.testing.assert_array_equal(get_ttc_array(links), [1000.0, 2500.0])

    def test_empty(self):
        self.assertEqual(get_ttc_array([]).shape, (0,))


class TestTransmissionDispatch(unittest.TestCase):
    """End-to-end dispatch tests exercising the transmission pipes."""

    def test_uncongested_link_equalizes_prices(self):
        # 2 zones, 1 link (1000 MW). Cheap gen (MC=30) only in zone A,
        # expensive gen (MC=80) only in zone B; both zones carry demand.
        zone_names = ["A", "B"]
        fleet = _fleet([("A", 500.0), ("B", 500.0)], zone_names)
        mc = np.vstack([np.full(T, 30.0), np.full(T, 80.0)])
        demand = np.vstack([np.full(T, 100.0), np.full(T, 100.0)])

        links = [TransferLink(from_zone="A", to_zone="B", ttc_mw=1000.0)]
        incidence = build_incidence_matrix(links, zone_names)
        ttc = get_ttc_array(links)

        result = solve_dispatch(
            fleet, demand, mc=mc, T=T, incidence=incidence, ttc=ttc,
            **_no_renewables(2),
        )

        # Power flows A -> B (positive flow) and the link is not at its cap.
        self.assertTrue(np.all(result.flows[0] > 0.0))
        self.assertTrue(np.all(result.flows[0] < ttc[0]))
        # Uncongested: the cheap gen is marginal in both zones.
        np.testing.assert_allclose(result.prices, 30.0)
        # Expensive zone-B generator stays off.
        np.testing.assert_allclose(result.dispatch[1], 0.0)

    def test_zero_ttc_decouples_zones(self):
        # Same setup, but the link has zero transfer capability.
        zone_names = ["A", "B"]
        fleet = _fleet([("A", 500.0), ("B", 500.0)], zone_names)
        mc = np.vstack([np.full(T, 30.0), np.full(T, 80.0)])
        demand = np.vstack([np.full(T, 100.0), np.full(T, 100.0)])

        links = [TransferLink(from_zone="A", to_zone="B", ttc_mw=1000.0)]
        incidence = build_incidence_matrix(links, zone_names)
        ttc = np.zeros(1)  # TTC=0: TransferLink itself forbids ttc_mw=0

        result = solve_dispatch(
            fleet, demand, mc=mc, T=T, incidence=incidence, ttc=ttc,
            **_no_renewables(2),
        )

        # No flow is possible; each zone serves its own load.
        np.testing.assert_allclose(result.flows[0], 0.0)
        np.testing.assert_allclose(result.dispatch[0], 100.0)
        np.testing.assert_allclose(result.dispatch[1], 100.0)
        # Decoupled prices: each zone prices at its own generator's MC.
        np.testing.assert_allclose(result.prices[0], 30.0)
        np.testing.assert_allclose(result.prices[1], 80.0)

    def test_surplus_wind_exports_up_to_ttc(self):
        # Zone A has surplus wind; the export saturates the link.
        zone_names = ["A", "B"]
        fleet = _fleet([("A", 500.0), ("B", 500.0)], zone_names)
        mc = np.vstack([np.full(T, 40.0), np.full(T, 50.0)])
        demand_a, demand_b = 100.0, 300.0
        demand = np.vstack([np.full(T, demand_a), np.full(T, demand_b)])

        wind_cap = np.array([500.0, 0.0])
        wind_cf = np.vstack([np.full(T, 1.0), np.zeros(T)])
        wind_available = 500.0  # wind_cap[0] * cf 1.0, in zone A

        links = [TransferLink(from_zone="A", to_zone="B", ttc_mw=200.0)]
        incidence = build_incidence_matrix(links, zone_names)
        ttc = get_ttc_array(links)

        result = solve_dispatch(
            fleet, demand, mc=mc, T=T, incidence=incidence, ttc=ttc,
            wind_cf=wind_cf, wind_cap=wind_cap,
            solar_cf=np.zeros((2, T)), solar_cap=np.zeros(2),
        )

        # Flow equals min(zone-A surplus, TTC); here the link is saturated.
        surplus = wind_available - demand_a  # 400 MW
        expected_flow = min(surplus, ttc[0])  # 200 MW
        np.testing.assert_allclose(result.flows[0], expected_flow)
        # Free wind makes zone A no more expensive than the importing zone.
        self.assertTrue(np.all(result.prices[0] <= result.prices[1] + 1e-6))

    def test_ercot_like_four_zone_energy_balance(self):
        # 4 zones, 6 links, generators spread across every zone.
        zone_names = ["North", "South", "West", "Houston"]
        fleet = _fleet(
            [
                ("North", 4000.0),
                ("South", 2000.0),
                ("West", 1500.0),
                ("Houston", 3000.0),
            ],
            zone_names,
        )
        mc = np.vstack(
            [
                np.full(T, 25.0),   # North: cheapest
                np.full(T, 45.0),   # South
                np.full(T, 60.0),   # West
                np.full(T, 70.0),   # Houston: most expensive
            ]
        )
        demand = np.vstack(
            [
                np.full(T, 1500.0),  # North
                np.full(T, 1800.0),  # South
                np.full(T, 1200.0),  # West
                np.full(T, 2500.0),  # Houston
            ]
        )

        links = [
            TransferLink(from_zone="North", to_zone="South", ttc_mw=5000.0),
            TransferLink(from_zone="North", to_zone="West", ttc_mw=3000.0),
            TransferLink(from_zone="North", to_zone="Houston", ttc_mw=8000.0),
            TransferLink(from_zone="South", to_zone="Houston", ttc_mw=4000.0),
            TransferLink(from_zone="South", to_zone="West", ttc_mw=2000.0),
            TransferLink(from_zone="West", to_zone="Houston", ttc_mw=2500.0),
        ]
        incidence = build_incidence_matrix(links, zone_names)
        ttc = get_ttc_array(links)
        self.assertEqual(incidence.shape, (4, 6))

        result = solve_dispatch(
            fleet, demand, mc=mc, T=T, incidence=incidence, ttc=ttc,
            **_no_renewables(4),
        )

        # Per-zone energy balance: thermal + renewables + net flow + slack
        # must equal demand in every zone and every hour.
        n_zones = len(zone_names)
        gen_by_zone = np.zeros((n_zones, T))
        for g in range(fleet.n_gen):  # g: thermal generator index
            gen_by_zone[fleet.zone_idx[g]] += result.dispatch[g]
        net_flow = incidence @ result.flows  # (n_zones, T)
        supply = (
            gen_by_zone
            + result.wind_dispatched
            + result.solar_dispatched
            + net_flow
            + result.slack
        )
        np.testing.assert_allclose(supply, demand, atol=1e-6)
        # The flows respect the link transfer limits in both directions.
        self.assertTrue(np.all(np.abs(result.flows) <= ttc[:, None] + 1e-6))


# Availability factor of the WECC import tranches (1 - eford).
_IMPORT_AVAIL = 1.0 - WECC_IMPORT_EFORD


class TestWeccImportModel(unittest.TestCase):
    """End-to-end tests for the CAISO WECC import/export pseudo-generators."""

    def _solve_caiso(self, generators, caiso_demand, solar_cap=None, solar_cf=None):
        """Solve a 2-zone CAISO dispatch and return ``(result, fleet)``.

        Zones are ``["CAISO_main", "WECC_import"]`` joined by the single
        WECC_import -> CAISO_main link; demand sits only in CAISO_main.
        Marginal costs are assembled from each generator's ``vom`` field
        (all heat rates are zero), so the import merit order is exercised
        through the real cost path.
        """
        zone_names = ["CAISO_main", "WECC_import"]
        fleet = generators_to_fleet_arrays(generators, zone_names, hours=T)
        links = [
            TransferLink(
                from_zone="WECC_import", to_zone="CAISO_main", ttc_mw=15000.0
            )
        ]
        incidence = build_incidence_matrix(links, zone_names)
        ttc = get_ttc_array(links)
        mc = assemble_mc(fleet, np.zeros((len(generators), T)), carbon_price=0.0)
        demand = np.vstack([np.full(T, caiso_demand), np.zeros(T)])
        renewables = dict(
            wind_cf=np.zeros((2, T)),
            wind_cap=np.zeros(2),
            solar_cf=np.zeros((2, T)) if solar_cf is None else solar_cf,
            solar_cap=np.zeros(2) if solar_cap is None else solar_cap,
        )
        result = solve_dispatch(
            fleet, demand, mc=mc, T=T, incidence=incidence, ttc=ttc, **renewables
        )
        return result, fleet

    def test_low_demand_dispatches_only_cheapest_tranche(self):
        # CAISO demand (2000 MW) fits inside the $15 PNW_hydro tranche
        # (3000 MW * 0.98 availability = 2940 MW).
        generators = build_wecc_import_generators()
        result, _ = self._solve_caiso(generators, caiso_demand=2000.0)

        # Only tranche 0 (PNW_hydro) carries the load; the rest stay off.
        np.testing.assert_allclose(result.dispatch[0], 2000.0, atol=1e-6)
        np.testing.assert_allclose(result.dispatch[1:], 0.0, atol=1e-6)
        # The 15000 MW link is uncongested, so CAISO prices at the
        # marginal import tranche's marginal cost.
        np.testing.assert_allclose(result.prices[0], 15.0, atol=1e-6)

    def test_high_demand_dispatches_all_tranches_in_merit_order(self):
        # CAISO demand (14000 MW) needs every tranche but not their full
        # 14700 MW of available capacity.
        generators = build_wecc_import_generators()
        result, _ = self._solve_caiso(generators, caiso_demand=14000.0)

        # The three cheaper tranches load to their available maxima.
        np.testing.assert_allclose(
            result.dispatch[0], 3000.0 * _IMPORT_AVAIL, atol=1e-6
        )
        np.testing.assert_allclose(
            result.dispatch[1], 5000.0 * _IMPORT_AVAIL, atol=1e-6
        )
        np.testing.assert_allclose(
            result.dispatch[2], 4000.0 * _IMPORT_AVAIL, atol=1e-6
        )
        # The $80 tranche is marginal and only partly loaded.
        served_by_cheaper = (3000.0 + 5000.0 + 4000.0) * _IMPORT_AVAIL
        np.testing.assert_allclose(
            result.dispatch[3], 14000.0 - served_by_cheaper, atol=1e-6
        )
        # CAISO prices at the most expensive dispatched tranche.
        np.testing.assert_allclose(result.prices[0], 80.0, atol=1e-6)

    def test_surplus_solar_exports_to_sink(self):
        # A must-run CAISO_main unit (pmin 4000 MW) forces 3000 MW of
        # surplus past the 1000 MW of in-state demand; with abundant solar
        # on top, CAISO must export rather than shed.
        must_run = Generator(
            unit_id="CAISO_gas",
            name="CAISO_gas",
            zone="CAISO_main",
            fuel_type="gas_cc",
            pmax_mw=6000.0,
            pmin_mw=4000.0,
            heat_rate=0.0,
            vom=40.0,
            eford=0.0,
        )
        generators = build_wecc_import_generators() + [
            build_wecc_export_sink(),
            must_run,
        ]
        solar_cap = np.array([3000.0, 0.0])
        solar_cf = np.vstack([np.full(T, 1.0), np.zeros(T)])
        result, _ = self._solve_caiso(
            generators, caiso_demand=1000.0, solar_cap=solar_cap, solar_cf=solar_cf
        )

        # Generator order: 4 import tranches, then the sink (index 4),
        # then the CAISO_main must-run unit (index 5).
        sink_dispatch = result.dispatch[4]
        forced_surplus = 4000.0 - 1000.0  # must-run pmin minus CAISO demand

        # Link flow is negative: power moves CAISO_main -> WECC_import.
        self.assertTrue(np.all(result.flows[0] <= -forced_surplus + 1e-6))
        # The sink absorbs the export as negative generation.
        self.assertTrue(np.all(sink_dispatch <= -forced_surplus + 1e-6))
        # The must-run unit honors its minimum; the import tranches stay off.
        self.assertTrue(np.all(result.dispatch[5] >= 4000.0 - 1e-6))
        np.testing.assert_allclose(result.dispatch[:4], 0.0, atol=1e-6)


class TestGenericImportNode(unittest.TestCase):
    """Tests for the generalized per-ISO import/export node builders."""

    def test_wecc_wrappers_match_generic_builders(self):
        wrapped = build_wecc_import_generators()
        generic = build_import_generators("CAISO")
        self.assertEqual(
            [g.unit_id for g in wrapped], [g.unit_id for g in generic]
        )
        sink = build_wecc_export_sink()
        self.assertEqual(sink.zone, "WECC_import")
        self.assertEqual(sink.pmax_mw, 0.0)
        self.assertLess(sink.pmin_mw, 0.0)

    def test_unconfigured_iso_has_no_import_node(self):
        self.assertEqual(build_import_generators("ERCOT"), [])
        self.assertEqual(build_export_sinks("ERCOT"), [])
        ercot = get_iso_config("ERCOT")
        self.assertIs(extend_with_import_node(ercot), ercot)

    def test_pjm_blocks_cannot_arbitrage(self):
        # Every PJM import tranche must cost more than every export sink
        # pays, or the LP would clear phantom import->export flow for
        # profit in all hours.
        cheapest_import = min(p for _, _, p in IMPORT_TRANCHES["PJM"])
        richest_sink = max(p for _, _, p in EXPORT_TRANCHES["PJM"])
        self.assertGreater(cheapest_import, richest_sink)

    def test_pjm_node_units_live_in_external_zone(self):
        units = build_import_generators("PJM") + build_export_sinks("PJM")
        self.assertTrue(units)
        for g in units:
            self.assertEqual(g.zone, "PJM_external")
            self.assertEqual(g.fuel_type, "import")
            self.assertEqual(g.heat_rate, 0.0)

    def test_extend_with_import_node_appends_pjm_external(self):
        base = get_iso_config("PJM")
        extended = extend_with_import_node(base)
        self.assertEqual(
            extended.zone_names, [*base.zone_names, "PJM_external"]
        )
        self.assertEqual(
            extended.n_links, base.n_links + len(IMPORT_NODE_LINKS["PJM"])
        )
        # The external zone carries no load and the result still validates.
        self.assertEqual(extended.zones[-1].load_share, 0.0)
        extended.validate_topology()
        # Idempotent: a second call sees the zone present and no-ops.
        self.assertIs(extend_with_import_node(extended), extended)
        # The base config object is untouched (backcasts keep 8 zones).
        self.assertEqual(len(base.zones), 8)

    def test_caiso_topology_already_carries_its_node(self):
        caiso = get_iso_config("CAISO")
        self.assertIs(extend_with_import_node(caiso), caiso)

    def test_nyiso_neiso_blocks_cannot_arbitrage(self):
        # Every import tranche must price above every export sink, or the LP
        # would clear phantom import->export flow for free profit (P9).
        for iso in ("NYISO", "NEISO"):
            cheapest_import = min(p for _, _, p in IMPORT_TRANCHES[iso])
            richest_sink = max(p for _, _, p in EXPORT_TRANCHES[iso])
            self.assertGreater(cheapest_import, richest_sink, iso)

    def test_nyiso_neiso_node_units_live_in_external_zone(self):
        for iso, zone in (("NYISO", "NYISO_external"), ("NEISO", "HQ_import")):
            units = build_import_generators(iso) + build_export_sinks(iso)
            self.assertTrue(units, iso)
            for g in units:
                self.assertEqual(g.zone, zone, iso)
                self.assertEqual(g.fuel_type, "import", iso)
                self.assertEqual(g.heat_rate, 0.0, iso)

    def test_nyiso_imports_are_priced_in_neighbor_merit_order(self):
        # The tranche VOM carries the neighbor-hub proxy directly (no fuel
        # cost), cheapest first: HQ hydro < Ontario < PJM < ISO-NE < scarcity.
        prices = [g.vom for g in build_import_generators("NYISO")]
        self.assertEqual(prices, sorted(prices))

    def test_extend_with_import_node_appends_nyiso_external(self):
        base = get_iso_config("NYISO")
        extended = extend_with_import_node(base)
        self.assertEqual(
            extended.zone_names, [*base.zone_names, "NYISO_external"]
        )
        self.assertEqual(
            extended.n_links, base.n_links + len(IMPORT_NODE_LINKS["NYISO"])
        )
        self.assertEqual(extended.zones[-1].load_share, 0.0)
        extended.validate_topology()
        # Idempotent, and the 5-zone backcast config is untouched.
        self.assertIs(extend_with_import_node(extended), extended)
        self.assertEqual(len(base.zones), 5)

    def test_neiso_topology_already_carries_its_node(self):
        # NEISO bakes HQ_import (plus the Highgate/NB and NY-tie links) into
        # _neiso_config, like CAISO's WECC_import, so extend is a no-op.
        neiso = get_iso_config("NEISO")
        self.assertIn("HQ_import", neiso.zone_names)
        self.assertIs(extend_with_import_node(neiso), neiso)
        self.assertTrue(build_import_generators("NEISO"))


class TestPjmImportNodeDispatch(unittest.TestCase):
    """End-to-end dispatch through the PJM priced import/export node."""

    def _solve(self, internal_mc, demand_mw):
        """Solve a 2-zone PJM-like dispatch; returns (result, units)."""
        zone_names = ["PJM_main", "PJM_external"]
        internal = Generator(
            unit_id="PJM_gas", name="PJM_gas", zone="PJM_main",
            fuel_type="gas_cc", pmax_mw=150000.0, pmin_mw=0.0,
            heat_rate=0.0, vom=internal_mc, eford=0.0,
        )
        units = (
            [internal]
            + build_import_generators("PJM")
            + build_export_sinks("PJM")
        )
        fleet = generators_to_fleet_arrays(units, zone_names, hours=T)
        links = [
            TransferLink(
                from_zone="PJM_external", to_zone="PJM_main", ttc_mw=30000.0
            )
        ]
        incidence = build_incidence_matrix(links, zone_names)
        ttc = get_ttc_array(links)
        mc = assemble_mc(fleet, np.zeros((len(units), T)), carbon_price=0.0)
        demand = np.vstack([np.full(T, demand_mw), np.zeros(T)])
        result = solve_dispatch(
            fleet, demand, mc=mc, T=T, incidence=incidence, ttc=ttc,
            **_no_renewables(2),
        )
        return result, units

    def test_cheap_internal_power_fills_every_sink(self):
        # Internal MC $10 sits below every sink price, so all sinks absorb
        # at full capacity and the system exports their sum.
        result, units = self._solve(internal_mc=10.0, demand_mw=80000.0)
        sink_cap = sum(c for _, c, _ in EXPORT_TRANCHES["PJM"])
        exports = -result.dispatch[1 + len(IMPORT_TRANCHES["PJM"]):].sum(
            axis=0
        )
        np.testing.assert_allclose(exports, sink_cap, atol=1e-5)
        # Imports stay off: every tranche costs more than internal supply.
        n_imp = len(IMPORT_TRANCHES["PJM"])
        np.testing.assert_allclose(
            result.dispatch[1:1 + n_imp], 0.0, atol=1e-6
        )

    def test_sink_survives_min_gen_floor_fleet(self):
        # A CHP steam-following floor anywhere in the fleet activates the
        # min_gen lower-bound matrix for EVERY generator; export sinks
        # (pmin < 0) must keep their absorption range rather than being
        # pinned to a zero floor (the PJM calibration fleet always carries
        # CHP floors, so without this the node could never export).
        chp = Generator(
            unit_id="PJM_chp", name="PJM_chp", zone="PJM_main",
            fuel_type="gas_ct", pmax_mw=500.0, pmin_mw=0.0,
            heat_rate=0.0, vom=12.0, eford=0.0, chp_grid_pmin_mw=200.0,
        )
        units = [chp] + build_export_sinks("PJM")
        fleet = generators_to_fleet_arrays(
            units, ["PJM_main", "PJM_external"], hours=T
        )
        self.assertIsNotNone(fleet.min_gen)
        # The CHP floor binds; each sink keeps its negative lower bound.
        np.testing.assert_allclose(fleet.min_gen[0], 200.0)
        for i, (_, cap, _) in enumerate(EXPORT_TRANCHES["PJM"], start=1):
            np.testing.assert_allclose(fleet.min_gen[i], -cap)

    def test_expensive_internal_power_draws_scarcity_imports(self):
        # Internal MC $50 sits above the $46 tranche but below the $60 one,
        # and below no sink price, so only the cheap import tranche clears.
        result, units = self._solve(internal_mc=50.0, demand_mw=80000.0)
        tranches = IMPORT_TRANCHES["PJM"]
        self.assertEqual(tranches[0][2], 46.0)
        np.testing.assert_allclose(
            result.dispatch[1], tranches[0][1], atol=1e-5
        )
        np.testing.assert_allclose(result.dispatch[2], 0.0, atol=1e-6)
        # The richest sink pays $42 < $50: no exports.
        exports = result.dispatch[1 + len(tranches):]
        np.testing.assert_allclose(exports, 0.0, atol=1e-6)


class TestWeccBorderCarbon(unittest.TestCase):
    """CA cap-and-trade border adjustment on WECC import tranche prices."""

    def test_adder_is_unspecified_ef_times_allowance_price(self):
        # CARB MRR default EF for unspecified imports: 0.428 tCO2e/MWh.
        self.assertAlmostEqual(
            wecc_border_carbon_adder(35.0), 0.428 * 35.0
        )
        self.assertAlmostEqual(wecc_border_carbon_adder(0.0), 0.0)

    def test_default_build_carries_no_border_carbon(self):
        generators = build_import_generators("CAISO")
        for gen, (_, _, cost) in zip(generators, IMPORT_TRANCHES["CAISO"]):
            self.assertAlmostEqual(gen.vom, cost)

    def test_border_carbon_raises_every_tranche_price(self):
        adder = wecc_border_carbon_adder(35.23)  # 2024 CARB average
        generators = build_import_generators("CAISO", adder)
        for gen, (_, _, cost) in zip(generators, IMPORT_TRANCHES["CAISO"]):
            self.assertAlmostEqual(gen.vom, cost + adder)
            # The adjustment is a price term, not an emission attribute:
            # import MWh must not inflate the modeled in-state CO2 total.
            self.assertEqual(gen.emission_rate_co2, 0.0)
        # ~$15/MWh at the 2024 average allowance price.
        self.assertAlmostEqual(adder, CARB_UNSPECIFIED_IMPORT_EF * 35.23)
        self.assertGreater(adder, 14.0)
        self.assertLess(adder, 16.0)

    def test_legacy_wrapper_passes_the_adder_through(self):
        adder = wecc_border_carbon_adder(35.23)
        wrapped = build_wecc_import_generators(adder)
        generic = build_import_generators("CAISO", adder)
        self.assertEqual(
            [(g.unit_id, g.vom) for g in wrapped],
            [(g.unit_id, g.vom) for g in generic],
        )

    def test_export_sink_pays_no_border_carbon(self):
        # Exports carry no CA compliance cost; the sink's price stays 0.
        sink = build_wecc_export_sink()
        self.assertEqual(sink.vom, 0.0)


class PricedInterchangeDefaultTest(unittest.TestCase):
    """The --priced-interchange tri-state default resolution.

    CAISO has no measured-schedule mode (load_demand never nets interchange
    for it), so its backcasts must serve imports through the priced WECC node
    by default; the eastern ISOs default to their measured schedule.
    """

    def test_caiso_defaults_on(self):
        self.assertIn("CAISO", PRICED_INTERCHANGE_DEFAULT_ISOS)
        self.assertTrue(resolve_priced_interchange(None, "CAISO"))

    def test_other_isos_default_off(self):
        for iso in ("ERCOT", "PJM", "NYISO", "NEISO"):
            self.assertFalse(resolve_priced_interchange(None, iso), iso)

    def test_explicit_flag_overrides_default_both_ways(self):
        # --no-priced-interchange forces the measured schedule even for CAISO;
        # --priced-interchange forces the node on for an ISO that defaults off.
        self.assertFalse(resolve_priced_interchange(False, "CAISO"))
        self.assertTrue(resolve_priced_interchange(True, "ERCOT"))


if __name__ == "__main__":
    unittest.main()
