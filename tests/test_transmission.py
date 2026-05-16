"""Tests for the pipe-and-bubble transmission model."""

import unittest

import numpy as np

from market_sim.config.iso_configs import TransferLink
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.transmission import build_incidence_matrix, get_ttc_array

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


if __name__ == "__main__":
    unittest.main()
