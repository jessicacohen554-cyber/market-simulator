"""Tests for the generation fleet inventory and vectorization."""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from market_sim.config.constants import HEAT_RATE_BINS
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    Generator,
    aggregate_fleet,
    assemble_mc,
    build_synthetic_fleet,
    generators_to_fleet_arrays,
    load_fleet_from_csv,
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


class TestFleetLoader(unittest.TestCase):
    """Tests for ``load_fleet_from_csv`` and the synthetic fleet fallback."""

    ALL_ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP"]

    def _gw(self, generators: list[Generator]) -> float:
        """Return the total fleet capacity in GW."""
        return sum(g.pmax_mw for g in generators) / 1000.0

    def test_ercot_fleet_total_in_range(self):
        fleet = load_fleet_from_csv("ERCOT")
        self.assertGreaterEqual(self._gw(fleet), 80.0)
        self.assertLessEqual(self._gw(fleet), 120.0)

    def test_caiso_fleet_total_in_range(self):
        fleet = load_fleet_from_csv("CAISO")
        self.assertGreaterEqual(self._gw(fleet), 25.0)
        self.assertLessEqual(self._gw(fleet), 50.0)

    def test_pjm_fleet_total_in_range(self):
        fleet = load_fleet_from_csv("PJM")
        self.assertGreaterEqual(self._gw(fleet), 150.0)
        self.assertLessEqual(self._gw(fleet), 200.0)

    def test_no_generators_in_wecc_import_zone(self):
        fleet = load_fleet_from_csv("CAISO")
        self.assertTrue(all(g.zone != "WECC_import" for g in fleet))

    def test_nuclear_units_are_must_run(self):
        fleet = load_fleet_from_csv("ERCOT")
        nuclear = [g for g in fleet if g.fuel_type == "nuclear"]
        self.assertTrue(nuclear)
        self.assertTrue(all(g.is_must_run for g in nuclear))

    def test_heat_rates_match_constants(self):
        fleet = load_fleet_from_csv("ERCOT")
        for gen in fleet:
            if gen.fuel_type in HEAT_RATE_BINS:
                expected = HEAT_RATE_BINS[gen.fuel_type][gen.efficiency_bin]
                self.assertEqual(gen.heat_rate, expected)

    def test_some_coal_units_have_retirement_year(self):
        fleet = load_fleet_from_csv("ERCOT")
        coal = [g for g in fleet if g.fuel_type == "coal"]
        self.assertTrue(any(g.retirement_year is not None for g in coal))

    def test_fleet_converts_to_fleet_arrays(self):
        config = get_iso_config("ERCOT")
        fleet = load_fleet_from_csv("ERCOT", config)
        arrays = generators_to_fleet_arrays(fleet, config.zone_names, hours=24)
        self.assertEqual(arrays.n_gen, len(fleet))
        self.assertEqual(arrays.pmax.shape, (len(fleet),))
        self.assertEqual(arrays.availability.shape, (len(fleet), 24))

    def test_all_seven_isos_load(self):
        for iso in self.ALL_ISOS:
            fleet = load_fleet_from_csv(iso)
            self.assertTrue(fleet, f"{iso} fleet is empty")
            zone_names = sorted({g.zone for g in fleet})
            arrays = generators_to_fleet_arrays(fleet, zone_names, hours=4)
            self.assertEqual(arrays.n_gen, len(fleet))

    def test_synthetic_fallback_when_no_csv(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            fleet = load_fleet_from_csv("ERCOT", data_dir=Path(empty_dir))
        self.assertGreaterEqual(self._gw(fleet), 80.0)
        self.assertLessEqual(self._gw(fleet), 120.0)

    def test_synthetic_matches_csv_load(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            from_fallback = load_fleet_from_csv(
                "SPP", data_dir=Path(empty_dir)
            )
        direct = build_synthetic_fleet("SPP")
        self.assertEqual(len(from_fallback), len(direct))


class TestAggregateFleet(unittest.TestCase):
    """Tests for collapsing individual units into representative units."""

    def _gas_cc_fleet(self) -> list[Generator]:
        """Ten gas_cc units across two zones and two efficiency bins.

        Five units per zone, alternating efficiency bins, so the fleet
        spans all four ``(fuel_type, efficiency_bin, zone)`` groups.
        """
        gens: list[Generator] = []
        for i in range(10):
            zone = "north" if i < 5 else "south"
            ebin = "h_class" if i % 2 == 0 else "f_class"
            gens.append(
                Generator(
                    unit_id=f"CC{i}",
                    name=f"CC{i}",
                    zone=zone,
                    fuel_type="gas_cc",
                    efficiency_bin=ebin,
                    pmax_mw=100.0 + 10.0 * i,
                    pmin_mw=20.0 + i,
                    heat_rate=6.5 + 0.1 * i,
                    vom=3.0,
                    emission_rate_co2=0.36,
                    nox_rate=0.02,
                    eford=0.05,
                )
            )
        return gens

    def test_groups_collapse_to_representative_units(self):
        # 2 zones x 2 efficiency bins -> 4 representative units.
        result = aggregate_fleet(self._gas_cc_fleet())
        self.assertEqual(len(result), 4)
        keys = {(g.fuel_type, g.efficiency_bin, g.zone) for g in result}
        self.assertEqual(
            keys,
            {
                ("gas_cc", "h_class", "north"),
                ("gas_cc", "f_class", "north"),
                ("gas_cc", "h_class", "south"),
                ("gas_cc", "f_class", "south"),
            },
        )

    def test_representative_unit_id_and_name(self):
        result = aggregate_fleet(self._gas_cc_fleet())
        for g in result:
            expected = f"{g.fuel_type}_{g.efficiency_bin}_{g.zone}"
            self.assertEqual(g.unit_id, expected)
            self.assertEqual(g.name, expected)

    def test_aggregated_pmax_is_group_sum(self):
        gens = self._gas_cc_fleet()
        result = aggregate_fleet(gens)
        for rep in result:
            group = [
                g for g in gens
                if g.fuel_type == rep.fuel_type
                and g.efficiency_bin == rep.efficiency_bin
                and g.zone == rep.zone
            ]
            self.assertAlmostEqual(rep.pmax_mw, sum(g.pmax_mw for g in group))
            self.assertAlmostEqual(rep.pmin_mw, sum(g.pmin_mw for g in group))

    def test_aggregated_heat_rate_is_capacity_weighted(self):
        gens = self._gas_cc_fleet()
        result = aggregate_fleet(gens)
        for rep in result:
            group = [
                g for g in gens
                if g.fuel_type == rep.fuel_type
                and g.efficiency_bin == rep.efficiency_bin
                and g.zone == rep.zone
            ]
            total_cap = sum(g.pmax_mw for g in group)
            expected = (
                sum(g.heat_rate * g.pmax_mw for g in group) / total_cap
            )
            self.assertAlmostEqual(rep.heat_rate, expected)

    def test_nuclear_units_pass_through_unchanged(self):
        nuclear = [
            Generator(
                unit_id="NUKE1", name="Nuke 1", zone="north",
                fuel_type="nuclear", pmax_mw=1200.0, pmin_mw=1080.0,
                heat_rate=10.4, is_must_run=True,
            ),
            Generator(
                unit_id="NUKE2", name="Nuke 2", zone="south",
                fuel_type="nuclear", pmax_mw=1350.0, pmin_mw=1215.0,
                heat_rate=10.4, is_must_run=True,
            ),
        ]
        result = aggregate_fleet(nuclear)
        self.assertEqual(result, nuclear)

    def test_scheduled_retirement_units_pass_through(self):
        # A thermal unit with a retirement_year keeps its identity so the
        # known-retirement mechanism can still apply its scheduled exit.
        gens = [
            Generator(
                unit_id="C_RET", name="C_RET", zone="north", fuel_type="coal",
                efficiency_bin="older", pmax_mw=300.0, retirement_year=2030,
            ),
            Generator(
                unit_id="C0", name="C0", zone="north", fuel_type="coal",
                efficiency_bin="older", pmax_mw=400.0,
            ),
        ]
        result = aggregate_fleet(gens)
        self.assertEqual(len(result), 2)
        ids = {g.unit_id for g in result}
        self.assertIn("C_RET", ids)
        self.assertIn("coal_older_north", ids)

    def test_round_trip_to_fleet_arrays(self):
        aggregated = aggregate_fleet(self._gas_cc_fleet())
        arrays = generators_to_fleet_arrays(
            aggregated, ["north", "south"], hours=24
        )
        self.assertEqual(arrays.n_gen, 4)
        self.assertEqual(arrays.pmax.shape, (4,))
        self.assertEqual(arrays.availability.shape, (4, 24))
        self.assertEqual(len(arrays.unit_ids), 4)


if __name__ == "__main__":
    unittest.main()
