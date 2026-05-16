"""Tests for the generation fleet inventory and vectorization."""

import unittest

import numpy as np

from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    Generator,
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


if __name__ == "__main__":
    unittest.main()
