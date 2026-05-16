"""Tests for the generation fleet inventory and vectorization."""

import unittest

import numpy as np

from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    Generator,
    assemble_mc,
    generators_to_fleet_arrays,
)


def _sample_generators() -> list[Generator]:
    """Return three generators spanning two zones and three fuel types."""
    return [
        Generator(
            unit_id="G1",
            name="Combined Cycle 1",
            zone="north",
            fuel_type="gas_cc",
            pmax_mw=400.0,
            pmin_mw=120.0,
            heat_rate=6.8,
            eford=0.04,
        ),
        Generator(
            unit_id="G2",
            name="Combustion Turbine 1",
            zone="south",
            fuel_type="gas_ct",
            pmax_mw=100.0,
            heat_rate=10.5,
            eford=0.06,
        ),
        Generator(
            unit_id="G3",
            name="Coal 1",
            zone="north",
            fuel_type="coal",
            pmax_mw=600.0,
            pmin_mw=250.0,
            heat_rate=9.9,
            eford=0.08,
        ),
    ]


class TestFleetArrays(unittest.TestCase):
    """Tests for ``generators_to_fleet_arrays`` conversion."""

    def setUp(self):
        self.hours = 24
        self.zone_names = ["north", "south"]
        self.generators = _sample_generators()
        self.fleet = generators_to_fleet_arrays(
            self.generators, self.zone_names, hours=self.hours
        )

    def test_scalar_array_shape(self):
        self.assertEqual(self.fleet.pmax.shape, (3,))
        self.assertEqual(self.fleet.n_gen, 3)

    def test_availability_shape(self):
        self.assertEqual(self.fleet.availability.shape, (3, self.hours))

    def test_zone_idx_maps_zone_names(self):
        np.testing.assert_array_equal(self.fleet.zone_idx, [0, 1, 0])

    def test_fuel_type_idx_matches_map(self):
        expected = [
            FUEL_TYPE_MAP["gas_cc"],
            FUEL_TYPE_MAP["gas_ct"],
            FUEL_TYPE_MAP["coal"],
        ]
        np.testing.assert_array_equal(self.fleet.fuel_type_idx, expected)

    def test_availability_equals_one_minus_eford(self):
        for i, gen in enumerate(self.generators):
            expected = np.full(self.hours, 1.0 - gen.eford)
            np.testing.assert_allclose(self.fleet.availability[i], expected)

    def test_unit_ids_match(self):
        self.assertEqual(self.fleet.unit_ids, ["G1", "G2", "G3"])


class TestAssembleMC(unittest.TestCase):
    """Tests for the vectorized marginal cost assembly."""

    def test_single_gen_constant_fuel_price(self):
        gen = Generator(
            unit_id="G1",
            name="CC 1",
            zone="z",
            fuel_type="gas_cc",
            pmax_mw=400.0,
            heat_rate=7.0,
            vom=3.0,
        )
        fleet = generators_to_fleet_arrays([gen], ["z"], hours=4)
        fuel_prices = np.full((1, 4), 4.0)
        mc = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
        self.assertEqual(mc.shape, (1, 4))
        np.testing.assert_allclose(mc, 7.0 * 4.0 + 3.0)

    def test_two_gens_different_heat_rates(self):
        gens = [
            Generator(
                unit_id="G1", name="CC", zone="z", fuel_type="gas_cc",
                pmax_mw=400.0, heat_rate=7.0,
            ),
            Generator(
                unit_id="G2", name="CT", zone="z", fuel_type="gas_ct",
                pmax_mw=100.0, heat_rate=11.0,
            ),
        ]
        fleet = generators_to_fleet_arrays(gens, ["z"], hours=3)
        fuel_prices = np.full((2, 3), 5.0)
        mc = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
        np.testing.assert_allclose(mc[0], 35.0)
        np.testing.assert_allclose(mc[1], 55.0)
        self.assertFalse(np.allclose(mc[0], mc[1]))

    def test_carbon_price_scales_with_emission_rate(self):
        gen = Generator(
            unit_id="G1", name="Coal", zone="z", fuel_type="coal",
            pmax_mw=600.0, heat_rate=10.0, emission_rate_co2=0.95,
        )
        fleet = generators_to_fleet_arrays([gen], ["z"], hours=2)
        fuel_prices = np.full((1, 2), 2.0)
        base = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
        with_carbon = assemble_mc(fleet, fuel_prices, carbon_price=50.0)
        np.testing.assert_allclose(with_carbon - base, 0.95 * 50.0)

    def test_custom_adder(self):
        gen = Generator(
            unit_id="G1", name="Coal", zone="z", fuel_type="coal",
            pmax_mw=600.0, heat_rate=10.0,
        )
        fleet = generators_to_fleet_arrays([gen], ["z"], hours=3)
        fuel_prices = np.full((1, 3), 2.0)
        so2_rate = np.array([0.4])
        so2_price = np.array([10.0, 20.0, 30.0])
        mc = assemble_mc(
            fleet, fuel_prices, carbon_price=0.0,
            so2=(so2_rate, so2_price),
        )
        expected = 10.0 * 2.0 + 0.4 * so2_price
        np.testing.assert_allclose(mc[0], expected)

    def test_time_varying_fuel_price(self):
        gen = Generator(
            unit_id="G1", name="CC", zone="z", fuel_type="gas_cc",
            pmax_mw=400.0, heat_rate=7.0, vom=2.0,
        )
        fleet = generators_to_fleet_arrays([gen], ["z"], hours=4)
        fuel_prices = np.array([[3.0, 4.0, 5.0, 6.0]])
        mc = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
        np.testing.assert_allclose(mc[0], 7.0 * fuel_prices[0] + 2.0)
        self.assertFalse(np.allclose(mc[0], mc[0, 0]))


if __name__ == "__main__":
    unittest.main()
