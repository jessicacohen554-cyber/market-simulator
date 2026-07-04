"""Tests for the pipe-and-bubble transmission model."""

import unittest
import unittest.mock

import numpy as np
import pandas as pd

from market_sim.config.interchange_config import (
    EXPORT_TRANCHES,
    IMPORT_NODE_LINKS,
    IMPORT_TRANCHE_EF,
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
    CAISO_BIDIR_EXPORT_CAP_MW,
    CAISO_BIDIR_IMPORT_CAP_MW,
    CAISO_GAS_FLOOR_HOURS,
    build_caiso_bidir_intertie,
    build_export_sinks,
    build_import_generators,
    caiso_solar_deliverability_derate,
    build_incidence_matrix,
    build_interface_groups,
    build_pjm_external_flow_groups,
    build_wecc_export_sink,
    build_wecc_import_generators,
    extend_with_import_node,
    get_ttc_array,
    inject_caiso_bidir_intertie_prices,
    inject_caiso_export_hub_prices,
    inject_caiso_gas_commitment_floor,
    inject_interchange_shape,
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
            fleet,
            demand,
            mc=mc,
            T=T,
            incidence=incidence,
            ttc=ttc,
            **_no_renewables(2),
        )

        # Power flows A -> B (positive flow) and the link is not at its cap.
        self.assertTrue(np.all(result.flows[0] > 0.0))
        self.assertTrue(np.all(result.flows[0] < ttc[0]))
        # Uncongested: the cheap gen is marginal in both zones.
        np.testing.assert_allclose(result.prices, 30.0)
        # Expensive zone-B generator stays off.
        np.testing.assert_allclose(result.dispatch[1], 0.0)

    def test_one_way_link_forbids_reverse_flow(self):
        # An asymmetric interface: a one-way A->B link (is_bidirectional=False)
        # carries import into B up to its TTC but cannot carry power back B->A,
        # so pairing two opposite one-way links gives an interface different
        # import vs export ratings. Here B is cheap and A needs power, so the
        # economic flow would be B->A; the one-way A->B link must block it.
        from market_sim.model.transmission import get_link_bidirectional_array

        zone_names = ["A", "B"]
        fleet = _fleet([("A", 500.0), ("B", 500.0)], zone_names)
        mc = np.vstack([np.full(T, 80.0), np.full(T, 30.0)])  # B cheap, A dear
        demand = np.vstack([np.full(T, 300.0), np.full(T, 0.0)])  # load in A

        links = [
            TransferLink(
                from_zone="A", to_zone="B", ttc_mw=1000.0, is_bidirectional=False
            )
        ]
        incidence = build_incidence_matrix(links, zone_names)
        ttc = get_ttc_array(links)
        bidir = get_link_bidirectional_array(links)
        self.assertFalse(bool(bidir[0]))

        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=T,
            incidence=incidence,
            ttc=ttc,
            link_bidirectional=bidir,
            **_no_renewables(2),
        )
        # Reverse (B->A) flow is forbidden: flow floored at 0, so A serves its
        # own load with the dear local gen and B's cheap gen can't reach it.
        np.testing.assert_allclose(result.flows[0], 0.0, atol=1e-6)
        np.testing.assert_allclose(result.prices[0], 80.0)

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
            fleet,
            demand,
            mc=mc,
            T=T,
            incidence=incidence,
            ttc=ttc,
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
            fleet,
            demand,
            mc=mc,
            T=T,
            incidence=incidence,
            ttc=ttc,
            wind_cf=wind_cf,
            wind_cap=wind_cap,
            solar_cf=np.zeros((2, T)),
            solar_cap=np.zeros(2),
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
                np.full(T, 25.0),  # North: cheapest
                np.full(T, 45.0),  # South
                np.full(T, 60.0),  # West
                np.full(T, 70.0),  # Houston: most expensive
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
            fleet,
            demand,
            mc=mc,
            T=T,
            incidence=incidence,
            ttc=ttc,
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


class TestAsymmetricHourlyTtc(unittest.TestCase):
    """Hourly export caps with a static import bound (``ttc_import``).

    The ERCOT measured-GTC overlay caps the EXPORT direction of a link with
    an hourly ``(T, n_links)`` series while the import direction keeps its
    static thermal rating — a GTC is an export stability limit, not an
    import rating.
    """

    def test_export_capped_hourly_import_keeps_static(self):
        zone_names = ["A", "B"]
        # All thermal lives in B; A is a wind pocket that flips to importing.
        fleet = _fleet([("B", 500.0)], zone_names)
        mc = np.full((1, T), 50.0)
        demand = np.vstack([np.full(T, 100.0), np.full(T, 300.0)])

        # Wind 500 MW in A for hours 0-11 (A exports its 400 MW surplus),
        # zero after (A imports its 100 MW load).
        wind_cap = np.array([500.0, 0.0])
        cf = np.zeros(T)
        cf[:12] = 1.0
        wind_cf = np.vstack([cf, np.zeros(T)])

        links = [TransferLink(from_zone="A", to_zone="B", ttc_mw=200.0)]
        incidence = build_incidence_matrix(links, zone_names)
        static = get_ttc_array(links)
        # Hourly export cap: 150 MW while the wind blows, 50 MW after —
        # below the 100 MW import A then needs, so a symmetric bound would
        # strand load in A.
        ttc_hourly = np.full((T, 1), 150.0)
        ttc_hourly[12:, 0] = 50.0

        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=T,
            incidence=incidence,
            ttc=ttc_hourly,
            ttc_import=static,
            wind_cf=wind_cf,
            wind_cap=wind_cap,
            solar_cf=np.zeros((2, T)),
            solar_cap=np.zeros(2),
        )

        # Export hours saturate the hourly cap (surplus 400 > cap 150).
        np.testing.assert_allclose(result.flows[0, :12], 150.0, atol=1e-6)
        # Import hours are bounded by the STATIC rating, not the 50 MW
        # export cap: A's 100 MW load imports in full, no slack.
        np.testing.assert_allclose(result.flows[0, 12:], -100.0, atol=1e-6)
        self.assertLessEqual(float(result.slack.max()), 1e-6)


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
            TransferLink(from_zone="WECC_import", to_zone="CAISO_main", ttc_mw=15000.0)
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
        # CAISO demand (500 MW) fits inside the $28 PNW_hydro_base tranche
        # (800 MW * 0.98 availability = 784 MW). Price is the converged P9/P12
        # re-price value (calibration-log "CAISO 4 — import re-price").
        generators = build_wecc_import_generators()
        result, _ = self._solve_caiso(generators, caiso_demand=500.0)

        # Only tranche 0 (PNW_hydro_base) carries the load; the rest stay off.
        np.testing.assert_allclose(result.dispatch[0], 500.0, atol=1e-6)
        np.testing.assert_allclose(result.dispatch[1:], 0.0, atol=1e-6)
        # The link is uncongested, so CAISO prices at the marginal import
        # tranche's marginal cost.
        np.testing.assert_allclose(result.prices[0], 28.0, atol=1e-6)

    def test_high_demand_dispatches_all_tranches_in_merit_order(self):
        # CAISO demand (10000 MW) needs every tranche but not the full
        # available import capacity (ladder total * 0.98 availability). Caps
        # are read from the ladder so the test tracks the grounded firm-block
        # volumes (DMM RA-import capacity x MIC corridor share).
        generators = build_wecc_import_generators()
        result, _ = self._solve_caiso(generators, caiso_demand=10000.0)

        # The five cheaper tranches load to their available maxima.
        cheaper_caps = [cap for _, cap, _ in IMPORT_TRANCHES["CAISO"][:5]]
        for i, cap in enumerate(cheaper_caps):
            np.testing.assert_allclose(
                result.dispatch[i], cap * _IMPORT_AVAIL, atol=1e-6
            )
        # The $180 WECC_scarcity tranche is marginal and only partly loaded.
        served_by_cheaper = sum(cheaper_caps) * _IMPORT_AVAIL
        np.testing.assert_allclose(
            result.dispatch[5], 10000.0 - served_by_cheaper, atol=1e-6
        )
        # CAISO prices at the most expensive dispatched tranche (converged
        # P9/P12 re-price value; calibration-log "CAISO 4 — import re-price").
        np.testing.assert_allclose(result.prices[0], 180.0, atol=1e-6)

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

        # Generator order: 6 import tranches, then the sink (index 6),
        # then the CAISO_main must-run unit (index 7).
        sink_dispatch = result.dispatch[6]
        forced_surplus = 4000.0 - 1000.0  # must-run pmin minus CAISO demand

        # Link flow is negative: power moves CAISO_main -> WECC_import.
        self.assertTrue(np.all(result.flows[0] <= -forced_surplus + 1e-6))
        # The sink absorbs the export as negative generation.
        self.assertTrue(np.all(sink_dispatch <= -forced_surplus + 1e-6))
        # The must-run unit honors its minimum; the import tranches stay off.
        self.assertTrue(np.all(result.dispatch[7] >= 4000.0 - 1e-6))
        np.testing.assert_allclose(result.dispatch[:6], 0.0, atol=1e-6)


class TestInterchangeShaping(unittest.TestCase):
    """Diurnal/seasonal shaping of the CAISO priced import/export node."""

    def _caiso_node_fleet(self, hours):
        import pandas as pd

        gens = build_import_generators("CAISO") + build_export_sinks("CAISO")
        zone_names = ["NP15", "ZP26", "SP15", "WECC_import"]
        fa = generators_to_fleet_arrays(gens, zone_names, hours=hours)
        clock = pd.date_range("2024-01-01", periods=hours, freq="h")
        return fa, gens, clock.month.to_numpy(), clock.hour.to_numpy()

    def test_shaping_swings_import_down_and_export_up_midday(self):
        H = 8760
        fa, gens, month, hod = self._caiso_node_fleet(H)
        avail_before = fa.availability.copy()
        applied = inject_interchange_shape(fa, "CAISO", 2024)
        self.assertTrue(applied)

        imp = np.array([g.pmax_mw > 0 for g in gens])
        exp = np.array([g.pmax_mw <= 0 and g.pmin_mw < 0 for g in gens])
        spring_mid = (np.isin(month, [4, 5])) & (hod >= 12) & (hod <= 15)
        night = hod <= 4

        # Import availability is shaped down at spring midday vs overnight.
        imp_avail = fa.availability[imp]
        self.assertLess(
            imp_avail[:, spring_mid].mean(), 0.6 * imp_avail[:, night].mean()
        )
        # And it actually changed from the flat base.
        self.assertFalse(np.allclose(fa.availability[imp], avail_before[imp]))

        # Export floor (min_gen, negative = export) opens up at spring midday.
        self.assertIsNotNone(fa.min_gen)
        exp_floor = fa.min_gen[exp]
        self.assertLess(exp_floor[:, spring_mid].mean(), -100.0)
        # Overnight export is shut (winter/night CA imports).
        self.assertGreater(exp_floor[:, night].mean(), -50.0)

    def test_export_only_leaves_imports_uncapped_but_shapes_export(self):
        # export_only=True must leave every import tranche's availability
        # byte-identical (no gross-import starvation) while still opening the
        # midday export floor exactly as the full shape does.
        H = 8760
        fa, gens, month, hod = self._caiso_node_fleet(H)
        avail_before = fa.availability.copy()
        applied = inject_interchange_shape(fa, "CAISO", 2024, export_only=True)
        self.assertTrue(applied)

        imp = np.array([g.pmax_mw > 0 for g in gens])
        exp = np.array([g.pmax_mw <= 0 and g.pmin_mw < 0 for g in gens])
        spring_mid = (np.isin(month, [4, 5])) & (hod >= 12) & (hod <= 15)

        # Imports are untouched (the regression half is skipped).
        np.testing.assert_array_equal(fa.availability[imp], avail_before[imp])
        # Export floor still opens midday (the half that unlocks negatives).
        self.assertIsNotNone(fa.min_gen)
        self.assertLess(fa.min_gen[exp][:, spring_mid].mean(), -100.0)

    def test_no_op_without_import_node(self):
        # A plain thermal fleet has no import/export rows -> returns False and
        # leaves availability untouched (byte-identical).
        gens = [
            Generator(
                unit_id="g1",
                name="g1",
                zone="NP15",
                fuel_type="gas_cc",
                pmax_mw=400.0,
                pmin_mw=0.0,
            )
        ]
        fa = generators_to_fleet_arrays(gens, ["NP15"], hours=48)
        before = fa.availability.copy()
        self.assertFalse(inject_interchange_shape(fa, "CAISO", 2024))
        np.testing.assert_array_equal(fa.availability, before)

    def test_forecast_year_is_unshaped(self):
        # No EIA-930 envelope for a forecast year -> no-op, node unchanged.
        fa, gens, _, _ = self._caiso_node_fleet(48)
        before = fa.availability.copy()
        self.assertFalse(inject_interchange_shape(fa, "CAISO", 2030))
        np.testing.assert_array_equal(fa.availability, before)


class TestCaisoGasCommitmentFloor(unittest.TestCase):
    """CAISO RA must-offer midday minimum-commitment floor on the gas fleet."""

    def _gas_fleet(self, hours, cc_mw=2000.0, ct_mw=1500.0):
        # Two gas units (CC cheaper than CT) + an import tranche + an export
        # sink with a negative pmin, so the export-sink-preservation path is
        # exercised. A small default cap (3.5 GW) is well below the measured
        # NG: NG (6-9 GW midday) so the clamp path is exercised; pass a large
        # cap to leave the floor unclamped.
        gens = [
            Generator(
                unit_id="cc",
                name="cc",
                zone="NP15",
                fuel_type="gas_cc",
                pmax_mw=cc_mw,
                pmin_mw=0.0,
                heat_rate=7.0,
            ),
            Generator(
                unit_id="ct",
                name="ct",
                zone="SP15",
                fuel_type="gas_ct",
                pmax_mw=ct_mw,
                pmin_mw=0.0,
                heat_rate=10.0,
            ),
            Generator(
                unit_id="imp",
                name="imp",
                zone="WECC_import",
                fuel_type="import",
                pmax_mw=5000.0,
                pmin_mw=0.0,
            ),
            Generator(
                unit_id="exp",
                name="exp",
                zone="WECC_import",
                fuel_type="import",
                pmax_mw=0.0,
                pmin_mw=-3000.0,
            ),
        ]
        zone_names = ["NP15", "SP15", "WECC_import"]
        fa = generators_to_fleet_arrays(gens, zone_names, hours=hours)
        clock = pd.date_range("2024-01-01", periods=hours, freq="h")
        return fa, gens, clock.month.to_numpy(), clock.hour.to_numpy()

    def test_floors_gas_midday_and_leaves_night_unfloored(self):
        H = 8760
        fa, gens, month, hod = self._gas_fleet(H)
        self.assertIsNone(fa.min_gen)
        applied = inject_caiso_gas_commitment_floor(fa, "CAISO", 2024, 1.0)
        self.assertTrue(applied)
        self.assertIsNotNone(fa.min_gen)

        is_gas = np.array([g.fuel_type in ("gas_cc", "gas_ct") for g in gens])
        gas_floor = fa.min_gen[is_gas].sum(axis=0)
        lo, hi = CAISO_GAS_FLOOR_HOURS
        midday = (hod >= lo) & (hod < hi)
        night = hod < lo
        # Spring midday is floored well above zero (real CAISO ~6-7 GW gas).
        spring_mid = midday & np.isin(month, [4, 5])
        self.assertGreater(gas_floor[spring_mid].mean(), 1000.0)
        # Outside the window the gas fleet carries no floor.
        np.testing.assert_array_equal(gas_floor[night], 0.0)

    def test_floor_never_exceeds_available_capacity(self):
        # The measured NG: NG (~6-9 GW) exceeds this tiny fleet's 3.5 GW, so the
        # floor must clamp to the available cap — never manufacturing infeasible
        # demand the LP can't serve.
        H = 8760
        fa, gens, _, _ = self._gas_fleet(H)
        inject_caiso_gas_commitment_floor(fa, "CAISO", 2024, 1.0)
        is_gas = np.array([g.fuel_type in ("gas_cc", "gas_ct") for g in gens])
        cap = (fa.pmax[is_gas, None] * fa.availability[is_gas]).sum(axis=0)
        floor = fa.min_gen[is_gas].sum(axis=0)
        self.assertTrue(bool((floor <= cap + 1e-6).all()))

    def test_cheapest_unit_floored_first(self):
        # With a large CC cap (> the measured NG: NG), the whole fleet target
        # lands on the CC (cheapest) and the CT carries no floor.
        H = 8760
        fa, gens, _, hod = self._gas_fleet(H, cc_mw=30000.0, ct_mw=1500.0)
        inject_caiso_gas_commitment_floor(fa, "CAISO", 2024, 1.0)
        lo, hi = CAISO_GAS_FLOOR_HOURS
        midday = (hod >= lo) & (hod < hi)
        cc_floor = fa.min_gen[0]
        ct_floor = fa.min_gen[1]
        self.assertGreater(cc_floor[midday].mean(), 3000.0)  # carries the floor
        np.testing.assert_array_equal(ct_floor, 0.0)  # CT untouched

    def test_export_sink_pmin_preserved(self):
        # Creating min_gen must keep the export sink's negative lower bound,
        # else a zero floor would pin the sink off (no exports).
        fa, gens, _, _ = self._gas_fleet(48)
        inject_caiso_gas_commitment_floor(fa, "CAISO", 2024, 1.0)
        exp_row = [g.unit_id for g in gens].index("exp")
        np.testing.assert_array_equal(fa.min_gen[exp_row], fa.pmin[exp_row])

    def test_non_caiso_is_no_op(self):
        fa, _, _, _ = self._gas_fleet(48)
        self.assertFalse(inject_caiso_gas_commitment_floor(fa, "PJM", 2024, 1.0))
        self.assertIsNone(fa.min_gen)

    def test_gas_steam_is_excluded_from_the_floor(self):
        # The near-retired gas-steam fleet is NOT the RA must-offer midday
        # fleet; including it manufactured phantom ST_GAS (1.7 -> 3.7 TWh). The
        # floor must land only on the flexible CC/CT fleet, never on gas_st.
        H = 8760
        gens = [
            Generator(
                unit_id="cc",
                name="cc",
                zone="NP15",
                fuel_type="gas_cc",
                pmax_mw=20000.0,
                pmin_mw=0.0,
                heat_rate=7.0,
            ),
            Generator(
                unit_id="st",
                name="st",
                zone="SP15",
                fuel_type="gas_st",
                pmax_mw=5000.0,
                pmin_mw=0.0,
                heat_rate=11.0,
            ),
        ]
        fa = generators_to_fleet_arrays(gens, ["NP15", "SP15"], hours=H)
        self.assertTrue(inject_caiso_gas_commitment_floor(fa, "CAISO", 2024, 1.0))
        st_row = np.array([g.fuel_type == "gas_st" for g in gens])
        self.assertEqual(float(fa.min_gen[st_row].sum()), 0.0)
        # The CC (the flexible fleet) still carries the whole midday floor.
        cc_row = np.array([g.fuel_type == "gas_cc" for g in gens])
        self.assertGreater(float(fa.min_gen[cc_row].sum()), 0.0)

    def test_nonpositive_frac_is_no_op(self):
        fa, _, _, _ = self._gas_fleet(48)
        self.assertFalse(inject_caiso_gas_commitment_floor(fa, "CAISO", 2024, 0.0))
        self.assertIsNone(fa.min_gen)

    def test_forecast_year_is_no_op(self):
        # No EIA-930 NG: NG profile for a forecast year -> no floor.
        fa, _, _, _ = self._gas_fleet(48)
        self.assertFalse(inject_caiso_gas_commitment_floor(fa, "CAISO", 2030, 1.0))
        self.assertIsNone(fa.min_gen)

    def test_no_gas_units_is_no_op(self):
        # An all-import fleet (no gas rows) -> no floor.
        gens = [
            Generator(
                unit_id="imp",
                name="imp",
                zone="WECC_import",
                fuel_type="import",
                pmax_mw=5000.0,
                pmin_mw=0.0,
            ),
        ]
        fa = generators_to_fleet_arrays(gens, ["WECC_import"], hours=48)
        self.assertFalse(inject_caiso_gas_commitment_floor(fa, "CAISO", 2024, 1.0))
        self.assertIsNone(fa.min_gen)

    def test_frac_scales_the_floor(self):
        # A large fleet cap leaves the floor unclamped, so frac scales it
        # linearly: the 0.3 floor is exactly 0.3x the full floor.
        H = 8760
        fa_full, gens, _, hod = self._gas_fleet(H, cc_mw=30000.0)
        fa_half, _, _, _ = self._gas_fleet(H, cc_mw=30000.0)
        inject_caiso_gas_commitment_floor(fa_full, "CAISO", 2024, 1.0)
        inject_caiso_gas_commitment_floor(fa_half, "CAISO", 2024, 0.3)
        is_gas = np.array([g.fuel_type in ("gas_cc", "gas_ct") for g in gens])
        full = fa_full.min_gen[is_gas].sum(axis=0)
        half = fa_half.min_gen[is_gas].sum(axis=0)
        lo, hi = CAISO_GAS_FLOOR_HOURS
        midday = (hod >= lo) & (hod < hi) & (full > 0.0)
        self.assertTrue(midday.any())
        ratio = half[midday] / full[midday]
        self.assertTrue(np.allclose(ratio, 0.3, atol=1e-6))


class TestGenericImportNode(unittest.TestCase):
    """Tests for the generalized per-ISO import/export node builders."""

    def test_wecc_wrappers_match_generic_builders(self):
        wrapped = build_wecc_import_generators()
        generic = build_import_generators("CAISO")
        self.assertEqual([g.unit_id for g in wrapped], [g.unit_id for g in generic])
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
        self.assertEqual(extended.zone_names, [*base.zone_names, "PJM_external"])
        self.assertEqual(extended.n_links, base.n_links + len(IMPORT_NODE_LINKS["PJM"]))
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
        self.assertEqual(extended.zone_names, [*base.zone_names, "NYISO_external"])
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
            unit_id="PJM_gas",
            name="PJM_gas",
            zone="PJM_main",
            fuel_type="gas_cc",
            pmax_mw=150000.0,
            pmin_mw=0.0,
            heat_rate=0.0,
            vom=internal_mc,
            eford=0.0,
        )
        units = [internal] + build_import_generators("PJM") + build_export_sinks("PJM")
        fleet = generators_to_fleet_arrays(units, zone_names, hours=T)
        links = [
            TransferLink(from_zone="PJM_external", to_zone="PJM_main", ttc_mw=30000.0)
        ]
        incidence = build_incidence_matrix(links, zone_names)
        ttc = get_ttc_array(links)
        mc = assemble_mc(fleet, np.zeros((len(units), T)), carbon_price=0.0)
        demand = np.vstack([np.full(T, demand_mw), np.zeros(T)])
        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=T,
            incidence=incidence,
            ttc=ttc,
            **_no_renewables(2),
        )
        return result, units

    def test_cheap_internal_power_fills_every_sink(self):
        # Internal MC $10 sits below every sink price, so all sinks absorb
        # at full capacity and the system exports their sum.
        result, units = self._solve(internal_mc=10.0, demand_mw=80000.0)
        sink_cap = sum(c for _, c, _ in EXPORT_TRANCHES["PJM"])
        exports = -result.dispatch[1 + len(IMPORT_TRANCHES["PJM"]) :].sum(axis=0)
        np.testing.assert_allclose(exports, sink_cap, atol=1e-5)
        # Imports stay off: every tranche costs more than internal supply.
        n_imp = len(IMPORT_TRANCHES["PJM"])
        np.testing.assert_allclose(result.dispatch[1 : 1 + n_imp], 0.0, atol=1e-6)

    def test_sink_survives_min_gen_floor_fleet(self):
        # A CHP steam-following floor anywhere in the fleet activates the
        # min_gen lower-bound matrix for EVERY generator; export sinks
        # (pmin < 0) must keep their absorption range rather than being
        # pinned to a zero floor (the PJM calibration fleet always carries
        # CHP floors, so without this the node could never export).
        chp = Generator(
            unit_id="PJM_chp",
            name="PJM_chp",
            zone="PJM_main",
            fuel_type="gas_ct",
            pmax_mw=500.0,
            pmin_mw=0.0,
            heat_rate=0.0,
            vom=12.0,
            eford=0.0,
            chp_grid_pmin_mw=200.0,
        )
        units = [chp] + build_export_sinks("PJM")
        fleet = generators_to_fleet_arrays(units, ["PJM_main", "PJM_external"], hours=T)
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
        np.testing.assert_allclose(result.dispatch[1], tranches[0][1], atol=1e-5)
        np.testing.assert_allclose(result.dispatch[2], 0.0, atol=1e-6)
        # The richest sink pays $42 < $50: no exports.
        exports = result.dispatch[1 + len(tranches) :]
        np.testing.assert_allclose(exports, 0.0, atol=1e-6)


class TestWeccBorderCarbon(unittest.TestCase):
    """CA cap-and-trade border adjustment on WECC import tranche prices."""

    def test_adder_is_unspecified_ef_times_allowance_price(self):
        # CARB MRR default EF for unspecified imports: 0.428 tCO2e/MWh.
        self.assertAlmostEqual(wecc_border_carbon_adder(35.0), 0.428 * 35.0)
        self.assertAlmostEqual(wecc_border_carbon_adder(0.0), 0.0)

    def test_default_build_carries_no_border_carbon(self):
        generators = build_import_generators("CAISO")
        for gen, (_, _, cost) in zip(generators, IMPORT_TRANCHES["CAISO"]):
            self.assertAlmostEqual(gen.vom, cost)

    def test_border_carbon_scales_each_tranche_by_its_emission_factor(self):
        # The border adjustment is the *unspecified* default (0.428 × price);
        # each tranche pays it scaled by its own EF / 0.428, so clean blocks
        # (hydro/solar, EF 0) pay nothing and unspecified blocks pay it in
        # full — matching CARB's specified-vs-unspecified treatment.
        price = 35.23  # 2024 CARB average allowance price
        adder = wecc_border_carbon_adder(price)
        generators = build_import_generators("CAISO", adder)
        ef = IMPORT_TRANCHE_EF["CAISO"]
        for gen, (name, _, cost) in zip(generators, IMPORT_TRANCHES["CAISO"]):
            self.assertAlmostEqual(gen.vom, cost + ef[name] * price)
            # The adjustment is a price term, not an emission attribute:
            # import MWh must not inflate the modeled in-state CO2 total.
            self.assertEqual(gen.emission_rate_co2, 0.0)
        # Clean blocks pay nothing; the unspecified block pays the full adder.
        self.assertAlmostEqual(generators[0].vom, IMPORT_TRANCHES["CAISO"][0][2])
        self.assertAlmostEqual(
            generators[-1].vom, IMPORT_TRANCHES["CAISO"][-1][2] + adder
        )
        # ~$15/MWh at the 2024 average allowance price.
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


class TestCaisoExportHubPrices(unittest.TestCase):
    """Neighbor-export sink repriced to the measured WECC hub LMP."""

    def _fleet(self):
        gens = [
            Generator(
                unit_id="WECC_import_export_solar",
                name="export_solar",
                zone="WECC_import",
                fuel_type="import",
                pmax_mw=0.0,
                pmin_mw=-2500.0,
                vom=8.0,
            ),
            Generator(
                unit_id="WECC_import_export_curtail",
                name="export_curtail",
                zone="WECC_import",
                fuel_type="import",
                pmax_mw=0.0,
                pmin_mw=-4000.0,
                vom=0.0,
            ),
        ]
        fa = generators_to_fleet_arrays(gens, ["WECC_import"], hours=T)
        return fa

    def test_reprices_export_solar_to_hub_leaves_curtail(self):
        fa = self._fleet()
        mc = np.zeros((2, T))
        hub = np.full(T, 37.0)
        with unittest.mock.patch(
            "market_sim.data.eia_loader.measured_import_hub_prices",
            return_value={"PNW_midC": hub, "DSW_solar_PV": hub},
        ):
            applied = inject_caiso_export_hub_prices(fa, mc, "CAISO", 2024)
        self.assertTrue(applied)
        # export_solar carries the measured hub price; export_curtail untouched.
        np.testing.assert_allclose(mc[0], hub)
        np.testing.assert_array_equal(mc[1], 0.0)

    def test_no_measured_series_is_noop(self):
        fa = self._fleet()
        mc = np.zeros((2, T))
        with unittest.mock.patch(
            "market_sim.data.eia_loader.measured_import_hub_prices",
            return_value=None,
        ):
            applied = inject_caiso_export_hub_prices(fa, mc, "CAISO", 2024)
        self.assertFalse(applied)
        np.testing.assert_array_equal(mc, 0.0)


class TestCaisoBidirIntertie(unittest.TestCase):
    """Single signed WECC intertie: one net direction per hour, arbitrage-free."""

    def _fleet(self, border_carbon=0.0):
        gens = build_caiso_bidir_intertie(border_carbon)
        fa = generators_to_fleet_arrays(gens, ["WECC_import"], hours=T)
        return fa, gens

    def test_builder_caps_match_directional_limits(self):
        gens = build_caiso_bidir_intertie()
        import_legs = [g for g in gens if g.pmax_mw > 0.0]
        export_legs = [g for g in gens if g.pmax_mw == 0.0 and g.pmin_mw < 0.0]
        # Import legs keep the per-tranche supply curve but rescale to the cap.
        self.assertEqual(len(import_legs), len(IMPORT_TRANCHES["CAISO"]))
        self.assertAlmostEqual(
            sum(g.pmax_mw for g in import_legs), CAISO_BIDIR_IMPORT_CAP_MW, places=3
        )
        # A SINGLE export leg, bounded at the measured export-direction peak.
        self.assertEqual(len(export_legs), 1)
        self.assertAlmostEqual(export_legs[0].pmin_mw, -CAISO_BIDIR_EXPORT_CAP_MW)

    def test_reprices_both_legs_off_the_hub_arbitrage_free(self):
        fa, gens = self._fleet(border_carbon=wecc_border_carbon_adder(35.0))
        n = len(gens)
        mc = np.zeros((n, T))
        # A hub that swings high (overnight) and negative (midday solar glut).
        hub = np.tile(np.array([60.0, 60.0, 60.0, -25.0, -25.0, -25.0] * 4), 1)[
            :T
        ].astype(float)
        with unittest.mock.patch(
            "market_sim.data.eia_loader.measured_import_hub_prices",
            return_value={"PNW_midC": hub.copy(), "DSW_solar_PV": hub.copy()},
        ):
            applied = inject_caiso_bidir_intertie_prices(fa, mc, "CAISO", 2024, 35.0)
        self.assertTrue(applied)

        is_export = np.array([g.name == "export_bidir" for g in gens])
        is_import = np.array([g.pmax_mw > 0.0 for g in gens])
        # Export leg earns the hub (no CA carbon), less the ε tiebreaker.
        np.testing.assert_allclose(mc[is_export][0], hub - 1e-3)
        # Every import leg is priced at hub + a non-negative border-carbon adder
        # (+ ε), so at every hour the dearest export is STRICTLY below the
        # cheapest import: the legs cannot arbitrage and the LP carries one
        # direction per hour.
        export_price = mc[is_export].max(axis=0)
        import_price_min = mc[is_import].min(axis=0)
        self.assertTrue(np.all(import_price_min > export_price))
        # The zero-EF firm hydro/solar legs sit at hub + delivered-cost basis
        # (line-loss markup on the positive hub + OATT wheeling); the gas legs
        # additionally carry a strictly positive carbon adder above it.
        self.assertTrue(np.all(mc[is_import].max(axis=0) > export_price + 1.0))
        # The delivery basis lifts every import leg strictly above the bare hub
        # (the wheel adder is >= $2 for every tranche), and never below it even
        # in the negative-hub hours (the loss is applied to max(hub, 0) only) —
        # so the single-flow tie can never round-trip wash.
        np.testing.assert_array_less(hub, mc[is_import].min(axis=0))

    def test_no_measured_series_is_noop(self):
        fa, gens = self._fleet()
        mc = np.zeros((len(gens), T))
        with unittest.mock.patch(
            "market_sim.data.eia_loader.measured_import_hub_prices",
            return_value=None,
        ):
            applied = inject_caiso_bidir_intertie_prices(fa, mc, "CAISO", 2023, 35.0)
        self.assertFalse(applied)
        np.testing.assert_array_equal(mc, 0.0)

    def test_dispatch_carries_one_direction_per_hour(self):
        # CAISO_main load zone + the external WECC_import bubble, joined by an
        # uncongested link. An in-state $40 gas unit and a midday solar block
        # make CAISO short overnight (imports) and long midday (exports); the
        # arbitrage-free hub pricing must never do both in the same hour.
        zone_names = ["CAISO_main", "WECC_import"]
        gas = Generator(
            unit_id="CAISO_gas",
            name="CAISO_gas",
            zone="CAISO_main",
            fuel_type="gas_cc",
            pmax_mw=5000.0,
            pmin_mw=0.0,
            heat_rate=0.0,
            vom=40.0,
            eford=0.0,
        )
        gens = build_caiso_bidir_intertie() + [gas]
        fleet = generators_to_fleet_arrays(gens, zone_names, hours=T)
        # Hub: cheap overnight (imports beat $40 gas), low-but-positive midday.
        # CAISO is long off its own solar midday (internal ~$0), so it sells the
        # surplus into the tie (export earns the hub) rather than imports; the ε
        # tiebreaker keeps the LP from washing import against export.
        hod = np.arange(T) % 24
        hub = np.where((hod >= 10) & (hod <= 15), 12.0, 25.0).astype(float)
        mc = assemble_mc(fleet, np.zeros((len(gens), T)), carbon_price=0.0)
        with unittest.mock.patch(
            "market_sim.data.eia_loader.measured_import_hub_prices",
            return_value={"PNW_midC": hub.copy(), "DSW_solar_PV": hub.copy()},
        ):
            self.assertTrue(
                inject_caiso_bidir_intertie_prices(fleet, mc, "CAISO", 2024, 0.0)
            )
        # Midday solar floods CAISO_main (8 GW vs 4 GW load) -> long -> export.
        solar_cap = np.array([8000.0, 0.0])
        solar_cf = np.vstack(
            [np.where((hod >= 10) & (hod <= 15), 1.0, 0.0), np.zeros(T)]
        )
        links = [
            TransferLink(from_zone="WECC_import", to_zone="CAISO_main", ttc_mw=20000.0)
        ]
        result = solve_dispatch(
            fleet,
            np.vstack([np.full(T, 4000.0), np.zeros(T)]),
            mc=mc,
            T=T,
            incidence=build_incidence_matrix(links, zone_names),
            ttc=get_ttc_array(links),
            wind_cf=np.zeros((2, T)),
            wind_cap=np.zeros(2),
            solar_cf=solar_cf,
            solar_cap=solar_cap,
        )
        is_import = np.array([g.pmax_mw > 0.0 for g in gens])
        is_export = np.array([g.name == "export_bidir" for g in gens])
        import_mw = result.dispatch[is_import].sum(axis=0)  # >= 0
        export_mw = -result.dispatch[is_export].sum(axis=0)  # withdrawal, >= 0
        # No hour both imports and exports (one signed flow on the shared tie).
        self.assertTrue(np.all(np.minimum(import_mw, export_mw) <= 1e-6))
        # The tie genuinely reverses: imports some hours, exports the midday glut.
        self.assertGreater(import_mw.max(), 1.0)
        self.assertGreater(export_mw.max(), 1.0)
        # Directional caps hold.
        self.assertLessEqual(import_mw.max(), CAISO_BIDIR_IMPORT_CAP_MW + 1e-6)
        self.assertLessEqual(export_mw.max(), CAISO_BIDIR_EXPORT_CAP_MW + 1e-6)


class TestInterfaceGroups(unittest.TestCase):
    """Tests for aggregate simultaneous-import interface limits (SIL/SEC)."""

    def test_caiso_config_declares_import_cap(self):
        cfg = get_iso_config("CAISO")
        cfg.validate_topology()
        self.assertEqual(len(cfg.interface_limits), 1)
        limit = cfg.interface_limits[0]
        # The two WECC import paths share one simultaneous cap below their TTC
        # sum (4,800 + 10,623 = 15,423 MW).
        self.assertEqual(
            set(tuple(p) for p in limit.links),
            {("WECC_import", "NP15"), ("WECC_import", "SP15")},
        )
        self.assertLess(limit.cap_mw, 15_423.0)

    def test_build_interface_groups_resolves_link_indices(self):
        cfg = get_iso_config("CAISO")
        groups = build_interface_groups(cfg.links, cfg.interface_limits)
        self.assertEqual(len(groups), 1)
        idx, cap, bidir, lower, signs = groups[0]
        # Path 66 / Path 46 are links 2 and 3 in the CAISO topology.
        np.testing.assert_array_equal(np.sort(idx), np.array([2, 3]))
        self.assertEqual(cap, 7500.0)
        self.assertTrue(bidir)

    def test_no_interface_limits_is_empty(self):
        cfg = get_iso_config("ERCOT")
        self.assertEqual(build_interface_groups(cfg.links, cfg.interface_limits), [])

    # --- MISO per-zone signed CIL/CEL groups (baked into _miso_config) -----

    def test_miso_signed_groups_orient_into_each_zone(self):
        """Every MISO CIL group's members are signed into its zone.

        The listed pair orientation defines the positive (import) direction:
        a link whose to_zone is the group's zone enters with +1, a link whose
        from_zone is the zone with -1 — including BOTH RDT one-way links from
        the single listed (South, Plains) pair.
        """
        cfg = get_iso_config("MISO")
        groups = build_interface_groups(cfg.links, cfg.interface_limits)
        self.assertEqual(len(groups), len(cfg.interface_limits))
        for lim, (idx, cap, bidir, lower, signs) in zip(cfg.interface_limits, groups):
            zone = "MISO-" + lim.name.removeprefix("MISO_CIL_")
            self.assertEqual(cap, lim.cap_mw)
            self.assertEqual(lower, lim.reverse_cap_mw)
            for i, sign in zip(idx, signs):
                ln = cfg.links[i]
                if sign > 0:
                    self.assertEqual(ln.to_zone, zone)
                else:
                    self.assertEqual(ln.from_zone, zone)
        # The Plains group carries all four incident corridors including both
        # RDT one-way links (net South->Plains flow from one listed pair).
        names = [lim.name for lim in cfg.interface_limits]
        plains = groups[names.index("MISO_CIL_Plains")]
        rdt_pairs = {
            (cfg.links[i].from_zone, cfg.links[i].to_zone, s)
            for i, s in zip(plains[0], plains[4])
            if "MISO-South" in (cfg.links[i].from_zone, cfg.links[i].to_zone)
        }
        self.assertEqual(
            rdt_pairs,
            {
                ("MISO-South", "MISO-Plains", 1.0),
                ("MISO-Plains", "MISO-South", -1.0),
            },
        )

    # --- NEISO HQ_import_simultaneous (baked into _neiso_config) -----------

    def test_neiso_config_declares_hq_import_cap(self):
        cfg = get_iso_config("NEISO")
        cfg.validate_topology()
        self.assertEqual(len(cfg.interface_limits), 1)
        limit = cfg.interface_limits[0]
        self.assertEqual(limit.name, "HQ_import_simultaneous")
        expected_links = {
            ("HQ_import", "Boston"),
            ("HQ_import", "North"),
            ("HQ_import", "Connecticut"),
        }
        self.assertEqual(set(tuple(p) for p in limit.links), expected_links)
        # Aggregate cap (3,850 MW) is below the sum of individual border
        # TTCs (2,000 + 900 + 1,500 = 4,400 MW).
        self.assertLess(limit.cap_mw, 4_400.0)
        self.assertEqual(limit.cap_mw, 3850.0)
        self.assertTrue(limit.bidirectional)

    def test_neiso_interface_groups_resolve_link_indices(self):
        cfg = get_iso_config("NEISO")
        groups = build_interface_groups(cfg.links, cfg.interface_limits)
        self.assertEqual(len(groups), 1)
        idx, cap, bidir, lower, signs = groups[0]
        # The three HQ_import→* links are at the end of the link list.
        hq_indices = [
            i for i, ln in enumerate(cfg.links) if ln.from_zone == "HQ_import"
        ]
        np.testing.assert_array_equal(np.sort(idx), np.sort(hq_indices))
        self.assertEqual(cap, 3850.0)
        self.assertTrue(bidir)

    # --- PJM/MISO/NYISO SIL via extend_with_import_node -------------------

    def test_pjm_extended_has_simultaneous_import_limit(self):
        cfg = extend_with_import_node(get_iso_config("PJM"))
        sil = [il for il in cfg.interface_limits if "simultaneous" in il.name]
        self.assertEqual(len(sil), 1)
        limit = sil[0]
        self.assertEqual(limit.name, "PJM_simultaneous_import")
        self.assertEqual(limit.cap_mw, 10500.0)
        self.assertTrue(limit.bidirectional)
        # All border links from PJM_external must be covered.
        ext_links = {
            (ln.from_zone, ln.to_zone)
            for ln in cfg.links
            if ln.from_zone == "PJM_external"
        }
        self.assertEqual(set(tuple(p) for p in limit.links), ext_links)
        # Cap is below the sum of individual border TTCs.
        ttc_sum = sum(ln.ttc_mw for ln in cfg.links if ln.from_zone == "PJM_external")
        self.assertLess(limit.cap_mw, ttc_sum)

    def test_miso_extended_has_simultaneous_import_limit(self):
        cfg = extend_with_import_node(get_iso_config("MISO"))
        sil = [il for il in cfg.interface_limits if "simultaneous" in il.name]
        self.assertEqual(len(sil), 1)
        limit = sil[0]
        self.assertEqual(limit.name, "MISO_simultaneous_import")
        self.assertEqual(limit.cap_mw, 8700.0)
        self.assertTrue(limit.bidirectional)
        ext_links = {
            (ln.from_zone, ln.to_zone)
            for ln in cfg.links
            if ln.from_zone == "MISO_external"
        }
        self.assertEqual(set(tuple(p) for p in limit.links), ext_links)
        ttc_sum = sum(ln.ttc_mw for ln in cfg.links if ln.from_zone == "MISO_external")
        self.assertLess(limit.cap_mw, ttc_sum)

    def test_nyiso_extended_has_simultaneous_import_limit(self):
        cfg = extend_with_import_node(get_iso_config("NYISO"))
        sil = [il for il in cfg.interface_limits if "simultaneous" in il.name]
        self.assertEqual(len(sil), 1)
        limit = sil[0]
        self.assertEqual(limit.name, "NYISO_simultaneous_import")
        self.assertEqual(limit.cap_mw, 4350.0)
        self.assertTrue(limit.bidirectional)
        ext_links = {
            (ln.from_zone, ln.to_zone)
            for ln in cfg.links
            if ln.from_zone == "NYISO_external"
        }
        self.assertEqual(set(tuple(p) for p in limit.links), ext_links)
        ttc_sum = sum(ln.ttc_mw for ln in cfg.links if ln.from_zone == "NYISO_external")
        self.assertLess(limit.cap_mw, ttc_sum)

    def test_pjm_interface_groups_from_extended_config(self):
        cfg = extend_with_import_node(get_iso_config("PJM"))
        groups = build_interface_groups(cfg.links, cfg.interface_limits)
        self.assertEqual(len(groups), 1)
        idx, cap, bidir, lower, signs = groups[0]
        ext_indices = [
            i for i, ln in enumerate(cfg.links) if ln.from_zone == "PJM_external"
        ]
        np.testing.assert_array_equal(np.sort(idx), np.sort(ext_indices))
        self.assertEqual(cap, 10500.0)
        self.assertTrue(bidir)

    def test_ercot_no_simultaneous_limit_after_extend(self):
        cfg = extend_with_import_node(get_iso_config("ERCOT"))
        self.assertEqual(cfg.interface_limits, [])


class TestPjmExternalFlowGroups(unittest.TestCase):
    """PJM congestion Lever A: external star-node deliverability caps."""

    def test_one_asymmetric_group_per_external_link(self):
        cfg = extend_with_import_node(get_iso_config("PJM"))
        zone_names = cfg.zone_names
        n = len(zone_names)
        T = 8
        import_cap = np.full((n, T), 1000.0)
        export_cap = np.full((n, T), 2000.0)
        groups = build_pjm_external_flow_groups(
            cfg.links, import_cap, export_cap, zone_names
        )
        # One group per PJM_external link (the 5 IMPORT_NODE_LINKS borders).
        ext_links = [ln for ln in cfg.links if ln.from_zone == "PJM_external"]
        self.assertEqual(len(groups), len(ext_links))
        self.assertTrue(ext_links)
        for idx, ic, two_way, ec in groups:
            # Asymmetric one-sided group: distinct import (up) and export (down)
            # caps, never the symmetric two-way path.
            self.assertEqual(idx.size, 1)
            self.assertFalse(two_way)
            link = cfg.links[int(idx[0])]
            self.assertEqual(link.from_zone, "PJM_external")
            np.testing.assert_array_equal(
                ic, import_cap[zone_names.index(link.to_zone)]
            )
            np.testing.assert_array_equal(
                ec, export_cap[zone_names.index(link.to_zone)]
            )

    def test_non_pjm_topology_yields_no_groups(self):
        # An ISO whose links carry no PJM_external from_zone gets no caps.
        cfg = get_iso_config("ERCOT")
        n = len(cfg.zone_names)
        groups = build_pjm_external_flow_groups(
            cfg.links, np.zeros((n, 4)), np.zeros((n, 4)), cfg.zone_names
        )
        self.assertEqual(groups, [])


class TestCaisoSolarDeliverabilityDerate(unittest.TestCase):
    """Tests for the CAISO Lever-D local solar deliverability derate."""

    def _patch_solar_frac(self, frac):
        """Patch caiso_solar_fraction (imported inside the function) to return frac."""
        return unittest.mock.patch(
            "market_sim.data.eia_loader.caiso_solar_fraction",
            return_value=(None if frac is None else np.asarray(frac, dtype=float)),
        )

    def test_derate_tracks_one_minus_k_times_penetration(self):
        frac = np.array([0.0, 0.2, 0.5, 0.8])
        with self._patch_solar_frac(frac):
            d = caiso_solar_deliverability_derate(2024, 4, k=0.15, floor=0.50)
        np.testing.assert_allclose(d, np.clip(1.0 - 0.15 * frac, 0.50, 1.0))
        # No penetration → no derate (potential delivered in full).
        self.assertAlmostEqual(d[0], 1.0)
        # Higher penetration → deeper cut (more curtailment headroom).
        self.assertLess(d[3], d[1])

    def test_floor_clamps_extreme_penetration(self):
        # A huge k would cut below the floor; the floor guards it.
        with self._patch_solar_frac([1.0, 1.0]):
            d = caiso_solar_deliverability_derate(2024, 2, k=0.9, floor=0.50)
        np.testing.assert_allclose(d, 0.50)

    def test_nonpositive_k_is_noop(self):
        with self._patch_solar_frac([0.5, 0.5]):
            self.assertIsNone(
                caiso_solar_deliverability_derate(2024, 2, k=0.0, floor=0.50)
            )

    def test_missing_penetration_returns_none(self):
        with self._patch_solar_frac(None):
            self.assertIsNone(
                caiso_solar_deliverability_derate(2024, 8, k=0.15, floor=0.50)
            )

    def test_more_solar_means_more_curtailment(self):
        # The mechanism's forward property: at a higher penetration the SAME
        # potential is curtailed more (the volume responds to the build).
        with self._patch_solar_frac([0.3]):
            low = caiso_solar_deliverability_derate(2024, 1, k=0.15, floor=0.50)
        with self._patch_solar_frac([0.6]):
            high = caiso_solar_deliverability_derate(2024, 1, k=0.15, floor=0.50)
        self.assertGreater(1.0 - high[0], 1.0 - low[0])


if __name__ == "__main__":
    unittest.main()
