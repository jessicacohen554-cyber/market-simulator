"""Tests for the generation fleet inventory and vectorization."""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from market_sim.config.constants import HEAT_RATE_BINS
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    Generator,
    aggregate_fleet,
    apply_coal_tranches,
    assemble_mc,
    generators_to_fleet_arrays,
    load_fleet_from_csv,
    split_coal_tranches,
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


class TestNuclearAvailability(unittest.TestCase):
    """Tests for nuclear seasonal availability shaping."""

    def _nuclear_gen(self) -> Generator:
        return Generator(
            unit_id="nuc1", name="Test Nuclear", zone="North",
            fuel_type="nuclear", pmax_mw=1000.0, pmin_mw=900.0,
            heat_rate=0.0, vom=2.5, emission_rate_co2=0.0,
            nox_rate=0.0, eford=0.03,
        )

    def test_nuclear_availability_seasonal(self):
        """Nuclear availability reflects monthly CF factors, not flat EFORD."""
        fa = generators_to_fleet_arrays(
            [self._nuclear_gen()], ["North"], iso="ERCOT"
        )

        # Availability should NOT be flat 0.97.
        self.assertGreater(
            fa.availability[0].std(), 0.001,
            "Nuclear availability should vary by month",
        )

        # Annual average should be ~0.95.
        annual_avg = fa.availability[0].mean()
        self.assertTrue(
            0.94 < annual_avg < 0.96,
            f"Nuclear avg availability {annual_avg:.3f} outside 0.94-0.96",
        )

        # Spring months should have lower availability than summer.
        mar_hours = fa.availability[0, 1416:2160]
        jul_hours = fa.availability[0, 4344:5088]
        self.assertLess(
            mar_hours.mean(), jul_hours.mean(),
            "Spring should have lower availability than summer",
        )

    def test_no_iso_keeps_flat_availability(self):
        """Without an ISO, nuclear availability stays flat 1 - eford."""
        gen = self._nuclear_gen()
        fa = generators_to_fleet_arrays([gen], ["North"])
        np.testing.assert_allclose(fa.availability[0], 1.0 - gen.eford)

    def test_non_nuclear_unaffected_by_iso(self):
        """Non-nuclear units keep flat availability even with an ISO."""
        coal = Generator(
            unit_id="c1", name="Coal", zone="North", fuel_type="coal",
            pmax_mw=500.0, heat_rate=10.0, eford=0.08,
        )
        fa = generators_to_fleet_arrays([coal], ["North"], iso="ERCOT")
        np.testing.assert_allclose(fa.availability[0], 1.0 - coal.eford)


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
    """Tests for ``load_fleet_from_csv``."""

    ALL_ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP"]

    def _gw(self, generators: list[Generator]) -> float:
        """Return the total fleet capacity in GW."""
        return sum(g.pmax_mw for g in generators) / 1000.0

    def test_ercot_fleet_total_in_range(self):
        fleet = load_fleet_from_csv("ERCOT")
        self.assertGreaterEqual(self._gw(fleet), 70.0)
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

    def test_heat_rates_use_actual_egrid_values(self):
        # With eGRID PLHTRT joined into the parquet, gas_cc units span a
        # real heat-rate gradient instead of collapsing onto the three
        # HEAT_RATE_BINS vintage centers.
        fleet = load_fleet_from_csv("ERCOT")
        cc_hrs = {
            round(g.heat_rate, 3) for g in fleet if g.fuel_type == "gas_cc"
        }
        bin_centers = set(HEAT_RATE_BINS["gas_cc"].values())
        self.assertGreater(len(cc_hrs), len(bin_centers))
        self.assertTrue(
            cc_hrs - bin_centers, "no actual (non-bin-center) heat rates loaded"
        )

    def test_missing_heat_rate_falls_back_to_bin_centers(self):
        # Units with no eGRID match keep the vintage bin-center fallback,
        # so every loaded generator still has a positive heat rate.
        fleet = load_fleet_from_csv("ERCOT")
        self.assertTrue(
            all(g.heat_rate > 0.0 for g in fleet if g.fuel_type in HEAT_RATE_BINS)
        )

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

    def test_raises_when_no_eia860_data(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            with self.assertRaises(FileNotFoundError):
                load_fleet_from_csv("ERCOT", data_dir=Path(empty_dir))


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

    def test_more_bins_produce_more_cc_groups(self):
        # With actual per-plant heat rates, n_bins=10 yields a finer merit
        # order -- more distinct gas_cc bins than n_bins=3.
        fleet = load_fleet_from_csv("ERCOT")
        cc_3 = [g for g in aggregate_fleet(fleet, n_bins=3) if g.fuel_type == "gas_cc"]
        cc_10 = [g for g in aggregate_fleet(fleet, n_bins=10) if g.fuel_type == "gas_cc"]
        self.assertGreater(len(cc_10), len(cc_3))
        hrs_3 = {round(g.heat_rate, 2) for g in cc_3}
        hrs_10 = {round(g.heat_rate, 2) for g in cc_10}
        self.assertGreater(len(hrs_10), len(hrs_3))

    def test_n_bins_zero_disables_aggregation(self):
        gens = self._gas_cc_fleet()
        self.assertEqual(aggregate_fleet(gens, n_bins=0), gens)
        self.assertEqual(aggregate_fleet(gens, n_bins="unit"), gens)

    def test_round_trip_to_fleet_arrays(self):
        aggregated = aggregate_fleet(self._gas_cc_fleet())
        arrays = generators_to_fleet_arrays(
            aggregated, ["north", "south"], hours=24
        )
        self.assertEqual(arrays.n_gen, 4)
        self.assertEqual(arrays.pmax.shape, (4,))
        self.assertEqual(arrays.availability.shape, (4, 24))
        self.assertEqual(len(arrays.unit_ids), 4)


class TestCoalTranches(unittest.TestCase):
    """Tests for the coal take-or-pay supply-curve tranche split."""

    def _coal_and_cc(self) -> list[Generator]:
        return [
            Generator(unit_id="COAL", name="COAL", zone="z", fuel_type="coal",
                      pmax_mw=1000.0, pmin_mw=400.0, heat_rate=10.0, vom=4.5,
                      emission_rate_co2=1.0, eford=0.08),
            Generator(unit_id="CC", name="CC", zone="z", fuel_type="gas_cc",
                      pmax_mw=300.0, heat_rate=7.0, vom=2.0, eford=0.05),
        ]

    def test_split_produces_three_tranches_per_coal_bin(self):
        fleet, fuel_fracs = split_coal_tranches(
            self._coal_and_cc(), ScenarioConfig()
        )
        # 3 coal tranches + 1 unchanged CC.
        self.assertEqual(len(fleet), 4)
        self.assertEqual(len(fuel_fracs), 4)

        coal = [g for g in fleet if g.fuel_type == "coal"]
        self.assertEqual([g.unit_id for g in coal],
                         ["COAL_t1", "COAL_t2", "COAL_t3"])
        # Capacity fractions 0.30 / 0.25 / 0.45 of the 1000 MW bin.
        np.testing.assert_allclose(
            [g.pmax_mw for g in coal], [300.0, 250.0, 450.0]
        )
        # Tranches carry no Pmin floor.
        self.assertTrue(all(g.pmin_mw == 0.0 for g in coal))
        # Fuel passthrough: T1 none, T2 partial, T3 full; CC always full.
        np.testing.assert_allclose(fuel_fracs, [0.0, 0.35, 1.0, 1.0])

    def test_non_coal_passes_through_unchanged(self):
        fleet, fuel_fracs = split_coal_tranches(
            self._coal_and_cc(), ScenarioConfig()
        )
        cc = fleet[-1]
        self.assertEqual(cc.unit_id, "CC")
        self.assertEqual(cc.fuel_type, "gas_cc")
        self.assertEqual(fuel_fracs[-1], 1.0)

    def test_tranche_capacity_sums_to_original_bin(self):
        fleet, _ = split_coal_tranches(self._coal_and_cc(), ScenarioConfig())
        coal_total = sum(g.pmax_mw for g in fleet if g.fuel_type == "coal")
        self.assertAlmostEqual(coal_total, 1000.0)

    def test_apply_coal_tranches_discounts_only_fuel(self):
        # T1 bids at VOM only; T2 keeps 35% of its fuel cost; T3 unchanged.
        # Fuel cost = heat_rate (10) x fuel_price (2) = 20 $/MWh.
        # Coal MC before tranching = fuel 20 + VOM 4.5 + carbon 30 = 54.5.
        fleet, fuel_fracs = split_coal_tranches(
            self._coal_and_cc(), ScenarioConfig()
        )
        arrays = generators_to_fleet_arrays(fleet, ["z"], hours=4)
        fuel_prices = np.array([np.full(4, 2.0)] * len(fleet))
        mc = np.array([
            np.full(4, 54.5),  # COAL_t1
            np.full(4, 54.5),  # COAL_t2
            np.full(4, 54.5),  # COAL_t3
            np.full(4, 25.0),  # CC
        ])

        apply_coal_tranches(mc, fleet, arrays, fuel_fracs, fuel_prices)

        # T1: full 20 fuel removed -> 34.5 (VOM + carbon survive).
        np.testing.assert_allclose(mc[0], 34.5)
        # T2: 65% of the 20 fuel removed (13) -> 41.5.
        np.testing.assert_allclose(mc[1], 41.5)
        # T3: unchanged. CC: unchanged.
        np.testing.assert_allclose(mc[2], 54.5)
        np.testing.assert_allclose(mc[3], 25.0)

    def test_tranche_fractions_follow_config(self):
        config = ScenarioConfig(
            coal_tranche_1_frac=0.50, coal_tranche_2_frac=0.20,
            coal_tranche_3_frac=0.30,
        )
        fleet, _ = split_coal_tranches(self._coal_and_cc(), config)
        coal = [g for g in fleet if g.fuel_type == "coal"]
        np.testing.assert_allclose(
            [g.pmax_mw for g in coal], [500.0, 200.0, 300.0]
        )


if __name__ == "__main__":
    unittest.main()
