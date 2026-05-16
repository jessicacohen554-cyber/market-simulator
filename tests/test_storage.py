"""Tests for storage parameter structs and storage-aware dispatch."""

import unittest

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.storage import (
    STORAGE_DEPLOYMENT_MW,
    StorageArrays,
    StorageUnit,
    build_default_storage,
    storage_units_to_arrays,
)


def _make_fleet(zones_of_gens, zone_names, hours, pmax=300.0):
    """Build ``FleetArrays`` with one always-available generator per entry."""
    generators = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone=z,
            fuel_type="gas_cc",
            pmax_mw=pmax,
            pmin_mw=0.0,
            eford=0.0,
        )
        for i, z in enumerate(zones_of_gens)
    ]
    return generators_to_fleet_arrays(generators, zone_names, hours=hours)


class TestStorageUnit(unittest.TestCase):
    """Tests for the ``StorageUnit`` Pydantic struct."""

    def test_fields_round_trip(self):
        unit = StorageUnit(
            unit_id="B0",
            zone="North",
            power_cap_mw=100.0,
            energy_cap_mwh=400.0,
            eta_charge=0.95,
            eta_discharge=0.90,
            zone_idx=2,
        )
        self.assertEqual(unit.unit_id, "B0")
        self.assertEqual(unit.zone, "North")
        self.assertEqual(unit.power_cap_mw, 100.0)
        self.assertEqual(unit.energy_cap_mwh, 400.0)
        self.assertEqual(unit.eta_charge, 0.95)
        self.assertEqual(unit.eta_discharge, 0.90)
        self.assertEqual(unit.zone_idx, 2)

    def test_efficiencies_default_to_lossless(self):
        unit = StorageUnit(
            unit_id="B1", zone="Z0", power_cap_mw=50.0, energy_cap_mwh=200.0
        )
        self.assertEqual(unit.eta_charge, 1.0)
        self.assertEqual(unit.eta_discharge, 1.0)
        self.assertEqual(unit.zone_idx, 0)


class TestStorageUnitsToArrays(unittest.TestCase):
    """Tests for ``storage_units_to_arrays`` struct-of-arrays conversion."""

    def test_arrays_align_with_units(self):
        units = [
            StorageUnit(
                unit_id="B0",
                zone="Z1",
                power_cap_mw=100.0,
                energy_cap_mwh=400.0,
                eta_charge=0.92,
                eta_discharge=0.92,
            ),
            StorageUnit(
                unit_id="B1",
                zone="Z0",
                power_cap_mw=50.0,
                energy_cap_mwh=150.0,
                eta_charge=0.80,
                eta_discharge=0.85,
            ),
        ]
        arrays = storage_units_to_arrays(units, ["Z0", "Z1"])
        self.assertIsInstance(arrays, StorageArrays)
        self.assertEqual(arrays.n_storage, 2)
        np.testing.assert_array_equal(arrays.power_cap, [100.0, 50.0])
        np.testing.assert_array_equal(arrays.energy_cap, [400.0, 150.0])
        np.testing.assert_array_equal(arrays.eta_chg, [0.92, 0.80])
        np.testing.assert_array_equal(arrays.eta_dis, [0.92, 0.85])
        # zone_idx is resolved against zone_names, not copied from the unit.
        np.testing.assert_array_equal(arrays.zone_idx, [1, 0])
        self.assertEqual(arrays.zone_idx.dtype, np.dtype(int))

    def test_empty_fleet(self):
        arrays = storage_units_to_arrays([], ["Z0"])
        self.assertEqual(arrays.n_storage, 0)


class TestBuildDefaultStorage(unittest.TestCase):
    """Tests for ``build_default_storage`` fleet construction."""

    def test_units_have_consistent_caps(self):
        iso = get_iso_config("ERCOT")
        units = build_default_storage(iso, ScenarioConfig(storage_deployment="mid"))
        self.assertGreater(len(units), 0)
        zone_names = set(iso.zone_names)
        for unit in units:
            self.assertGreater(unit.power_cap_mw, 0.0)
            self.assertGreater(unit.energy_cap_mwh, 0.0)
            self.assertIn(unit.zone, zone_names)
            self.assertGreater(unit.eta_charge, 0.0)
            self.assertLessEqual(unit.eta_charge, 1.0)

    def test_zero_load_zones_get_no_storage(self):
        # CAISO's WECC_import zone has load_share 0.0 -- no storage there.
        iso = get_iso_config("CAISO")
        units = build_default_storage(iso, ScenarioConfig())
        for unit in units:
            self.assertNotEqual(unit.zone, "WECC_import")

    def test_higher_pace_deploys_more_power(self):
        iso = get_iso_config("ERCOT")
        low = build_default_storage(iso, ScenarioConfig(storage_deployment="low"))
        high = build_default_storage(iso, ScenarioConfig(storage_deployment="high"))
        low_mw = sum(u.power_cap_mw for u in low)
        high_mw = sum(u.power_cap_mw for u in high)
        self.assertGreater(high_mw, low_mw)
        # The deployed total matches the configured pace (zero-load zones aside;
        # ERCOT has none, so all power is allocated).
        self.assertAlmostEqual(high_mw, STORAGE_DEPLOYMENT_MW["high"])

    def test_unknown_pace_raises(self):
        iso = get_iso_config("ERCOT")
        with self.assertRaises(ValueError):
            build_default_storage(iso, ScenarioConfig(storage_deployment="huge"))


class TestStorageRTEOverride(unittest.TestCase):
    """Tests that ScenarioConfig RTE overrides reach the built fleet."""

    def test_config_rte_overrides_constant(self):
        iso = get_iso_config("ERCOT")
        config = ScenarioConfig(storage_rte_4hr=0.80)  # lower than default 0.85
        units = build_default_storage(iso, config)
        li4_units = [u for u in units if "li_ion_4hr" in u.unit_id]
        for u in li4_units:
            # eta_charge * eta_discharge should equal the config RTE
            self.assertAlmostEqual(u.eta_charge * u.eta_discharge, 0.80, places=4)

    def test_default_config_matches_constant(self):
        iso = get_iso_config("ERCOT")
        config = ScenarioConfig()  # defaults: storage_rte_4hr=0.85
        units = build_default_storage(iso, config)
        li4_units = [u for u in units if "li_ion_4hr" in u.unit_id]
        for u in li4_units:
            self.assertAlmostEqual(u.eta_charge * u.eta_discharge, 0.85, places=4)


class TestStorageArbitrageDispatch(unittest.TestCase):
    """End-to-end storage behaviour in ``solve_dispatch`` (all use T=24).

    One 100 MW / 400 MWh unit (RTE 0.85) sits with two thermal generators:
    a cheap unit (MC 20) and an expensive unit (MC 80). Demand is low during
    hours 0-11 (served by the cheap unit alone) and high during hours 12-23
    (the expensive unit is needed). Storage should arbitrage the two.
    """

    T = 24
    RTE = 0.85

    def setUp(self):
        eta = self.RTE**0.5  # symmetric one-way efficiency, eta**2 == RTE
        fleet = _make_fleet(["Z0", "Z0"], ["Z0"], hours=self.T, pmax=300.0)
        mc = np.vstack(
            [np.full(self.T, 20.0), np.full(self.T, 80.0)]  # cheap, expensive
        )
        demand = np.empty((1, self.T))
        demand[0, :12] = 200.0  # low: cheap gen has spare room to charge
        demand[0, 12:] = 400.0  # high: needs the expensive gen or storage

        units = [
            StorageUnit(
                unit_id="B0",
                zone="Z0",
                power_cap_mw=100.0,
                energy_cap_mwh=400.0,
                eta_charge=eta,
                eta_discharge=eta,
                zone_idx=0,
            )
        ]
        arrays = storage_units_to_arrays(units, ["Z0"])

        self.result = solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((1, self.T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)),
            solar_cap=np.zeros(1),
            mc=mc,
            T=self.T,
            storage_power_cap=arrays.power_cap,
            storage_energy_cap=arrays.energy_cap,
            storage_zone_idx=arrays.zone_idx,
            eta_chg=arrays.eta_chg,
            eta_dis=arrays.eta_dis,
        )
        self.charge = self.result.storage_charge[0]
        self.discharge = self.result.storage_discharge[0]
        self.soc = self.result.storage_soc[0]

    def test_charges_cheap_hours_discharges_expensive_hours(self):
        # Charging concentrates in the low-price window, discharging in the high.
        self.assertGreater(self.charge[:12].sum(), 0.0)
        self.assertGreater(self.discharge[12:].sum(), 0.0)
        self.assertLess(self.charge[12:].sum(), 1.0)
        self.assertLess(self.discharge[:12].sum(), 1.0)

    def test_soc_is_cyclic(self):
        # Storage runs on a closed cycle: hour 0's dynamics wrap around from
        # the final hour, so SOC[0] is SOC[T-1] advanced by hour 0's own
        # charge/discharge -- no "free" unconstrained energy at hour 0.
        eta = self.RTE**0.5
        wrapped = (
            self.soc[self.T - 1]
            + eta * self.charge[0]
            - self.discharge[0] / eta
        )
        self.assertAlmostEqual(self.soc[0], wrapped, places=4)

    def test_energy_conservation_through_round_trip(self):
        total_charge = self.charge.sum()
        total_discharge = self.discharge.sum()
        self.assertGreater(total_charge, 0.0)
        # Over a closed SOC cycle, discharged energy == charged energy * RTE.
        self.assertAlmostEqual(
            total_discharge,
            total_charge * self.RTE,
            delta=0.01 * total_charge * self.RTE,
        )

    def test_round_trip_efficiency_loss(self):
        # RTE < 1, so strictly less energy comes out than goes in.
        self.assertLess(self.discharge.sum(), self.charge.sum())


if __name__ == "__main__":
    unittest.main()
