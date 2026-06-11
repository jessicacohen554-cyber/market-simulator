"""Tests for storage parameter structs and storage-aware dispatch."""

import unittest

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.config.constants import (
    STORAGE_ANNUAL_BUILD_CAP_MW,
    STORAGE_DEPLOYMENT_CEILING_MW,
)
from market_sim.model.storage import (
    STORAGE_BASE_FLEET_MW,
    StorageArrays,
    StorageUnit,
    _arbitrage_block_days,
    _degradation_cost_per_mwh,
    _elcc_for_duration,
    apply_storage_new_entry,
    build_default_storage,
    estimate_capacity_value,
    estimate_storage_revenue,
    load_eia860_pumped_storage,
    load_eia860_storage,
    storage_cap_profiles,


    resolve_pumped_storage_dispatch_adder,
    storage_units_to_arrays,
)
from market_sim.config.constants import (
    PUMPED_STORAGE_DURATION_HOURS,
    PUMPED_STORAGE_RTE,
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
            tech_name="li_ion_4hr",
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
            unit_id="B1", zone="Z0", tech_name="li_ion_4hr",
            power_cap_mw=50.0, energy_cap_mwh=200.0,
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
                tech_name="li_ion_4hr",
                power_cap_mw=100.0,
                energy_cap_mwh=400.0,
                eta_charge=0.92,
                eta_discharge=0.92,
            ),
            StorageUnit(
                unit_id="B1",
                zone="Z0",
                tech_name="li_ion_8hr",
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
        self.assertAlmostEqual(high_mw, STORAGE_BASE_FLEET_MW["ERCOT"]["high"])

    def test_unknown_pace_raises(self):
        iso = get_iso_config("ERCOT")
        with self.assertRaises(ValueError):
            build_default_storage(iso, ScenarioConfig(storage_deployment="huge"))


class TestEstimateStorageRevenue(unittest.TestCase):
    """Tests for ``estimate_storage_revenue`` arbitrage estimation."""

    @staticmethod
    def _day_night_prices(low=20.0, high=80.0):
        # 12 night hours at ``low``, 12 day hours at ``high``, every day.
        day = np.concatenate([np.full(12, low), np.full(12, high)])
        return np.tile(day, 365)

    def test_flat_prices_yield_zero_revenue(self):
        # No spread means no arbitrage; charging losses make every day a wash.
        prices = np.full(8760, 40.0)
        self.assertEqual(estimate_storage_revenue(prices, 4, 0.85), 0.0)

    def test_day_night_spread_revenue_in_expected_range(self):
        # margin ~= 80 - 20/0.85 = 56.5, x 4hr x 365 ~= 82k $/MW-yr.
        revenue = estimate_storage_revenue(self._day_night_prices(), 4, 0.85)
        self.assertGreater(revenue, 70_000.0)
        self.assertLess(revenue, 100_000.0)

    def test_longer_duration_earns_more_when_spread_persists(self):
        # The spread holds across the full 12-hour window, so 8hr storage
        # arbitrages twice the energy of 4hr storage.
        prices = self._day_night_prices()
        rev_4hr = estimate_storage_revenue(prices, 4, 0.85)
        rev_8hr = estimate_storage_revenue(prices, 8, 0.85)
        self.assertGreater(rev_8hr, rev_4hr)

    def test_lower_rte_reduces_revenue(self):
        # A lower round-trip efficiency raises the effective charging cost.
        prices = self._day_night_prices()
        high_rte = estimate_storage_revenue(prices, 4, 0.90)
        low_rte = estimate_storage_revenue(prices, 4, 0.70)
        self.assertGreater(high_rte, low_rte)


class TestLongDurationArbitrage(unittest.TestCase):
    """Long-duration storage must capture multi-day, not just daily, value."""

    @staticmethod
    def _spread_prices():
        # 12 cheap hours then 12 expensive hours, repeated every day.
        day = np.concatenate([np.full(12, 10.0), np.full(12, 300.0)])
        return np.tile(day, 365)

    def test_block_window_widens_with_duration(self):
        # Short duration cycles daily; long duration uses a multi-day window
        # sized so a full charge and discharge never overlap.
        self.assertEqual(_arbitrage_block_days(4), 1)
        self.assertEqual(_arbitrage_block_days(8), 1)
        self.assertEqual(_arbitrage_block_days(12), 1)
        self.assertGreaterEqual(_arbitrage_block_days(100) * 24, 2 * 100)

    def test_iron_air_100hr_revenue_is_positive(self):
        # The old fixed-24h window collapsed any duration >= a day to zero
        # spread, so iron-air (100h) screened as worthless and could never
        # build. With a duration-sized window it captures the spread.
        revenue = estimate_storage_revenue(self._spread_prices(), 100, 0.50)
        self.assertGreater(revenue, 0.0)

    def test_degradation_cost_reduces_revenue(self):
        prices = self._spread_prices()
        clean = estimate_storage_revenue(prices, 4, 0.85)
        degraded = estimate_storage_revenue(
            prices, 4, 0.85, degradation_cost_per_mwh=10.0
        )
        self.assertLess(degraded, clean)

    def test_degradation_cost_orders_by_cycle_life(self):
        # Long-cycle-life chemistries pay far less per MWh than li-ion.
        cfg = ScenarioConfig()
        li = _degradation_cost_per_mwh("li_ion_4hr", cfg)
        flow = _degradation_cost_per_mwh("flow_battery", cfg)
        self.assertGreater(li, 0.0)
        self.assertLess(flow, li)

    def test_degradation_toggle_off(self):
        cfg = ScenarioConfig(storage_degradation=False)
        self.assertEqual(_degradation_cost_per_mwh("li_ion_4hr", cfg), 0.0)


class TestCapacityValue(unittest.TestCase):
    """Resource-adequacy value is gated by market design and penetration."""

    def test_elcc_rises_with_duration(self):
        self.assertLess(_elcc_for_duration(4.0), _elcc_for_duration(12.0))
        self.assertLessEqual(_elcc_for_duration(100.0), 1.0)

    def test_energy_only_market_pays_no_capacity(self):
        # ERCOT is energy-only -- scarcity flows through the energy price.
        val = estimate_capacity_value(
            "li_ion_4hr", 0.0, ScenarioConfig(), "ERCOT"
        )
        self.assertEqual(val, 0.0)

    def test_capacity_market_pays_capacity(self):
        val = estimate_capacity_value(
            "li_ion_4hr", 0.0, ScenarioConfig(), "PJM"
        )
        self.assertGreater(val, 0.0)

    def test_capacity_value_declines_with_penetration(self):
        # As storage saturates the peak, marginal capacity value falls.
        low_pen = estimate_capacity_value(
            "li_ion_4hr", 0.0, ScenarioConfig(), "PJM"
        )
        high_pen = estimate_capacity_value(
            "li_ion_4hr", 60_000.0, ScenarioConfig(), "PJM"
        )
        self.assertLess(high_pen, low_pen)

    def test_longer_duration_earns_more_capacity_value(self):
        short = estimate_capacity_value(
            "li_ion_4hr", 0.0, ScenarioConfig(), "PJM"
        )
        long = estimate_capacity_value(
            "li_ion_12hr", 0.0, ScenarioConfig(), "PJM"
        )
        self.assertGreater(long, short)

    def test_config_toggle_disables_capacity_value(self):
        val = estimate_capacity_value(
            "li_ion_4hr", 0.0,
            ScenarioConfig(storage_capacity_value=False), "PJM",
        )
        self.assertEqual(val, 0.0)


class TestApplyStorageNewEntry(unittest.TestCase):
    """Tests for ``apply_storage_new_entry`` economics-based entry."""

    @staticmethod
    def _total_mw(units):
        return sum(u.power_cap_mw for u in units)

    @staticmethod
    def _flat_prices():
        return np.full(8760, 40.0)

    @staticmethod
    def _high_spread_prices():
        # An extreme day/night spread guarantees arbitrage clears any cost.
        day = np.concatenate([np.full(12, 10.0), np.full(12, 300.0)])
        return np.tile(day, 365)

    def test_flat_prices_no_entry(self):
        iso = get_iso_config("ERCOT")
        existing = build_default_storage(iso, ScenarioConfig())
        result = apply_storage_new_entry(
            existing, self._flat_prices(), 2027, ScenarioConfig(), "ERCOT"
        )
        self.assertAlmostEqual(
            self._total_mw(result), self._total_mw(existing)
        )

    def test_high_spread_triggers_entry(self):
        iso = get_iso_config("ERCOT")
        existing = build_default_storage(iso, ScenarioConfig())
        result = apply_storage_new_entry(
            existing, self._high_spread_prices(), 2027, ScenarioConfig(),
            "ERCOT",
        )
        self.assertGreater(
            self._total_mw(result), self._total_mw(existing)
        )

    def test_annual_cap_binds(self):
        # Even with huge arbitrage margins, a single year cannot build more
        # than the per-ISO annual cap.
        iso = get_iso_config("ERCOT")
        existing = build_default_storage(iso, ScenarioConfig())
        result = apply_storage_new_entry(
            existing, self._high_spread_prices(), 2027, ScenarioConfig(),
            "ERCOT",
        )
        added = self._total_mw(result) - self._total_mw(existing)
        self.assertLessEqual(added, STORAGE_ANNUAL_BUILD_CAP_MW["ERCOT"] + 1.0)

    def test_ceiling_binds(self):
        # An existing fleet already at the ceiling leaves no headroom.
        iso = get_iso_config("ERCOT")
        ceiling = STORAGE_DEPLOYMENT_CEILING_MW["ERCOT"]
        existing = [
            StorageUnit(
                unit_id="incumbent",
                zone=iso.zones[0].name,
                tech_name="li_ion_4hr",
                power_cap_mw=ceiling,
                energy_cap_mwh=ceiling * 4.0,
                eta_charge=0.92,
                eta_discharge=0.92,
                zone_idx=0,
            )
        ]
        result = apply_storage_new_entry(
            existing, self._high_spread_prices(), 2027, ScenarioConfig(),
            "ERCOT",
        )
        self.assertLessEqual(self._total_mw(result), ceiling + 1.0)

    def test_no_single_tech_exceeds_share_cap(self):
        # With extreme spread many techs are profitable, but the year's build
        # diversifies -- no single tech takes the whole budget.
        from market_sim.config.constants import (
            STORAGE_ANNUAL_BUILD_CAP_MW,
            STORAGE_TECH_BUILD_SHARE_CAP,
        )
        iso = get_iso_config("ERCOT")
        existing = build_default_storage(iso, ScenarioConfig())
        result = apply_storage_new_entry(
            existing, self._high_spread_prices(), 2030, ScenarioConfig(),
            "ERCOT",
        )
        new_by_tech: dict[str, float] = {}
        existing_ids = {u.unit_id for u in existing}
        for u in result:
            if u.unit_id not in existing_ids:
                new_by_tech[u.tech_name] = (
                    new_by_tech.get(u.tech_name, 0.0) + u.power_cap_mw
                )
        budget = STORAGE_ANNUAL_BUILD_CAP_MW["ERCOT"]
        self.assertGreater(len(new_by_tech), 1)  # diversified
        for mw in new_by_tech.values():
            self.assertLessEqual(mw, budget * STORAGE_TECH_BUILD_SHARE_CAP + 1.0)

    def test_eastern_iso_can_grow(self):
        # PJM previously had no ceiling/annual-cap, so storage could never
        # grow there. It now has both, so high spreads trigger entry.
        iso = get_iso_config("PJM")
        existing = build_default_storage(iso, ScenarioConfig())
        result = apply_storage_new_entry(
            existing, self._high_spread_prices(), 2030, ScenarioConfig(),
            "PJM",
        )
        self.assertGreater(
            self._total_mw(result), self._total_mw(existing)
        )

    def test_base_fleet_preserved_without_prior_prices(self):
        # With no price spread (the base-year case before any solve) the
        # incumbent fleet passes through untouched -- no additions.
        iso = get_iso_config("ERCOT")
        existing = build_default_storage(iso, ScenarioConfig())
        result = apply_storage_new_entry(
            existing, self._flat_prices(), 2026, ScenarioConfig(), "ERCOT"
        )
        self.assertEqual(len(result), len(existing))
        for original, returned in zip(existing, result):
            self.assertEqual(returned.unit_id, original.unit_id)
            self.assertEqual(returned.power_cap_mw, original.power_cap_mw)


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
                tech_name="li_ion_4hr",
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


class TestStorageDailyCycling(unittest.TestCase):
    """The daily SOC-cycling cap bounds storage to within-day arbitrage.

    Two days (T=48): day 0 is uniformly cheap and day 1 uniformly expensive,
    so an unconstrained battery wants to bank energy across the day boundary.
    The cap forces each day to be energy-neutral, killing that cross-day play.
    """

    T = 48
    RTE = 0.81

    def _solve(self, cycle_hours):
        eta = self.RTE**0.5
        # gen0 is a small cheap baseload (pmax 200, MC 20); gen1 (pmax 400) is
        # always on the margin since flat demand 350 > 200. gen1's MC is low on
        # day 0 (25) and high on day 1 (80), so the spread is *across* days,
        # not within them. Storage (100 MW) never zeroes gen1, so gen1 stays
        # marginal through charge/discharge.
        fleet = _make_fleet(["Z0", "Z0"], ["Z0"], hours=self.T, pmax=400.0)
        fleet.pmax[0] = 200.0
        mc = np.vstack([np.full(self.T, 20.0), np.empty(self.T)])
        mc[1, :24] = 25.0
        mc[1, 24:] = 80.0
        demand = np.full((1, self.T), 350.0)
        units = [
            StorageUnit(
                unit_id="B0", zone="Z0", tech_name="li_ion_4hr",
                power_cap_mw=100.0, energy_cap_mwh=400.0,
                eta_charge=eta, eta_discharge=eta, zone_idx=0,
            )
        ]
        arrays = storage_units_to_arrays(units, ["Z0"])
        return solve_dispatch(
            fleet, demand,
            wind_cf=np.zeros((1, self.T)), wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)), solar_cap=np.zeros(1),
            mc=mc, T=self.T,
            storage_power_cap=arrays.power_cap,
            storage_energy_cap=arrays.energy_cap,
            storage_zone_idx=arrays.zone_idx,
            eta_chg=arrays.eta_chg, eta_dis=arrays.eta_dis,
            storage_daily_cycle_hours=cycle_hours,
        )

    def test_unconstrained_banks_energy_across_days(self):
        # With no daily cap, the battery charges on the cheap day and the SOC
        # at the day boundary is well above its hour-0 level: cross-day banking.
        r = self._solve(None)
        soc = r.storage_soc[0]
        self.assertGreater(soc[24] - soc[0], 50.0)
        # It charges far more on day 0 than day 1 (banking for the dear day).
        self.assertGreater(r.storage_charge[0][:24].sum(),
                           r.storage_charge[0][24:].sum() + 50.0)

    def test_daily_cap_makes_each_day_energy_neutral(self):
        # With the 24h cap, the day-start SOC is pinned, so the boundary SOC
        # returns to the hour-0 level: no energy crosses midnight.
        r = self._solve(24)
        soc = r.storage_soc[0]
        self.assertAlmostEqual(soc[24], soc[0], places=3)

    def test_daily_cap_still_allows_within_day_arbitrage(self):
        # The cap bounds cross-day shifting, not in-day cycling: with an
        # in-day price spread the battery still charges and discharges.
        eta = self.RTE**0.5
        fleet = _make_fleet(["Z0", "Z0"], ["Z0"], hours=self.T, pmax=300.0)
        mc = np.vstack([np.full(self.T, 20.0), np.empty(self.T)])
        # Each day: cheap first half, dear second half.
        for d in range(2):
            mc[1, d * 24: d * 24 + 12] = 20.0
            mc[1, d * 24 + 12: d * 24 + 24] = 80.0
        demand = np.empty((1, self.T))
        for d in range(2):
            demand[0, d * 24: d * 24 + 12] = 200.0
            demand[0, d * 24 + 12: d * 24 + 24] = 400.0
        units = [
            StorageUnit(
                unit_id="B0", zone="Z0", tech_name="li_ion_4hr",
                power_cap_mw=100.0, energy_cap_mwh=400.0,
                eta_charge=eta, eta_discharge=eta, zone_idx=0,
            )
        ]
        arrays = storage_units_to_arrays(units, ["Z0"])
        r = solve_dispatch(
            fleet, demand,
            wind_cf=np.zeros((1, self.T)), wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)), solar_cap=np.zeros(1),
            mc=mc, T=self.T,
            storage_power_cap=arrays.power_cap,
            storage_energy_cap=arrays.energy_cap,
            storage_zone_idx=arrays.zone_idx,
            eta_chg=arrays.eta_chg, eta_dis=arrays.eta_dis,
            storage_daily_cycle_hours=24,
        )
        self.assertGreater(r.storage_discharge[0].sum(), 0.0)
        # Each day energy-neutral despite active cycling.
        soc = r.storage_soc[0]
        self.assertAlmostEqual(soc[24], soc[0], places=3)


class TestStorageDischargeCost(unittest.TestCase):
    """Per-unit discharge cost (the pumped-storage throughput adder)."""

    T = 24

    def _solve(self, discharge_cost):
        fleet = _make_fleet(["Z0", "Z0"], ["Z0"], hours=self.T, pmax=300.0)
        mc = np.vstack([np.full(self.T, 20.0), np.full(self.T, 40.0)])
        demand = np.empty((1, self.T))
        demand[0, :12] = 200.0
        demand[0, 12:] = 400.0
        eta = 0.85 ** 0.5
        return solve_dispatch(
            fleet, demand,
            wind_cf=np.zeros((1, self.T)), wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)), solar_cap=np.zeros(1),
            mc=mc, T=self.T,
            storage_power_cap=np.array([100.0]),
            storage_energy_cap=np.array([400.0]),
            storage_zone_idx=np.array([0]),
            eta_chg=np.array([eta]), eta_dis=np.array([eta]),
            storage_discharge_cost=discharge_cost,
        )

    def test_high_discharge_cost_suppresses_arbitrage(self):
        # Spread is 20 -> 40 ($20). With RTE 0.85 the cycle clears with no
        # adder; a $30/MWh discharge cost makes it uneconomic and the unit
        # sits idle instead of arbitraging.
        free = self._solve(0.0)
        priced = self._solve(np.array([30.0]))
        self.assertGreater(free.storage_discharge[0].sum(), 0.0)
        self.assertLess(priced.storage_discharge[0].sum(), 1.0)


class TestEIA860PumpedStorage(unittest.TestCase):
    """Tests for the EIA-860 pumped-storage hydro fleet loader."""

    def test_pjm_pumped_storage_present(self):
        # PJM's PS fleet (Bath County, Muddy Run, Yards Creek, Seneca,
        # Smith Mountain) is ~5 GW; the loader must find it on the EIA-860
        # generator schedule, which the battery schedule does not cover.
        units = load_eia860_pumped_storage("PJM", 2024)
        total_mw = sum(u.power_cap_mw for u in units)
        self.assertGreater(total_mw, 4500.0)
        self.assertLess(total_mw, 6500.0)
        for u in units:
            self.assertEqual(u.tech_name, "pumped_storage")
            self.assertAlmostEqual(
                u.energy_cap_mwh,
                u.power_cap_mw * PUMPED_STORAGE_DURATION_HOURS,
            )
            # One-way legs combine to the cited round-trip efficiency.
            self.assertAlmostEqual(
                u.eta_charge * u.eta_discharge, PUMPED_STORAGE_RTE, places=6
            )

    def test_ercot_has_no_pumped_storage(self):
        self.assertEqual(load_eia860_pumped_storage("ERCOT", 2024), [])

    def test_backcast_battery_fleet_includes_pumped_storage(self):
        units = load_eia860_storage("PJM", 2024, ScenarioConfig())
        techs = {u.tech_name for u in units}
        self.assertIn("pumped_storage", techs)
        self.assertIn("li_ion", techs)

    def test_caiso_pumped_storage_present(self):
        # CAISO's PS fleet — Helms (1,053 MW per EIA-860; PG&E rates the
        # upgraded units 1,212 MW), W. R. Gianelli, Edward C Hyatt,
        # J S Eastwood, Thermalito, O'Neill — totals ~2.1 GW, all in NP15.
        units = load_eia860_pumped_storage("CAISO", 2023)
        total_mw = sum(u.power_cap_mw for u in units)
        self.assertGreater(total_mw, 1900.0)
        self.assertLess(total_mw, 2300.0)
        for u in units:
            self.assertEqual(u.tech_name, "pumped_storage")
            self.assertIn(u.zone, {"NP15", "ZP26", "SP15"})
            self.assertAlmostEqual(
                u.energy_cap_mwh,
                u.power_cap_mw * PUMPED_STORAGE_DURATION_HOURS,
            )
            self.assertAlmostEqual(
                u.eta_charge * u.eta_discharge, PUMPED_STORAGE_RTE, places=6
            )


class TestPumpedStorageDispatchAdder(unittest.TestCase):
    """Per-ISO resolution of the PS dispatch adder (reserve-duty proxy)."""

    def test_pjm_default_is_calibrated_10(self):
        # PJM's $10/MWh reduced-form reserve duty (calibration-log
        # 2026-06-10, "pjm 3 ps-adder") flows from the per-ISO default.
        self.assertEqual(
            resolve_pumped_storage_dispatch_adder("PJM", ScenarioConfig()),
            10.0,
        )
        units = load_eia860_pumped_storage("PJM", 2024, ScenarioConfig())
        self.assertTrue(units)
        for u in units:
            self.assertEqual(u.vom, 10.0)

    def test_caiso_default_is_off(self):
        # CAISO has no calibrated reserve-duty adder yet: off by default
        # until a CAISO calibration pass says otherwise.
        self.assertEqual(
            resolve_pumped_storage_dispatch_adder("CAISO", ScenarioConfig()),
            0.0,
        )
        units = load_eia860_pumped_storage("CAISO", 2023, ScenarioConfig())
        self.assertTrue(units)
        for u in units:
            self.assertEqual(u.vom, 0.0)

    def test_no_config_falls_back_to_per_iso_default(self):
        self.assertEqual(
            resolve_pumped_storage_dispatch_adder("PJM", None), 10.0
        )
        self.assertEqual(
            resolve_pumped_storage_dispatch_adder("CAISO", None), 0.0
        )

    def test_explicit_value_overrides_every_iso(self):
        cfg = ScenarioConfig(pumped_storage_dispatch_adder=5.0)
        for iso in ("PJM", "CAISO", "ERCOT"):
            self.assertEqual(
                resolve_pumped_storage_dispatch_adder(iso, cfg), 5.0
            )
        zero = ScenarioConfig(pumped_storage_dispatch_adder=0.0)
        self.assertEqual(
            resolve_pumped_storage_dispatch_adder("PJM", zero), 0.0
        )


class TestBatteryDispatchAdder(unittest.TestCase):
    """ScenarioConfig.battery_dispatch_adder on the EIA-860 battery fleet."""

    def test_default_zero_leaves_battery_vom_unchanged(self):
        units = load_eia860_storage("ERCOT", 2024, ScenarioConfig())
        batteries = [u for u in units if u.tech_name != "pumped_storage"]
        self.assertTrue(batteries)
        for u in batteries:
            self.assertEqual(u.vom, 0.0)

    def test_adder_carried_on_battery_vom_only(self):
        cfg = ScenarioConfig(iso="PJM").with_overrides(
            battery_dispatch_adder=17.5
        )
        units = load_eia860_storage("PJM", 2024, cfg)
        for u in units:
            if u.tech_name == "pumped_storage":
                # PS keeps its own throughput adder (per-ISO resolved:
                # PJM's calibrated $10), not the battery one.
                self.assertEqual(
                    u.vom,
                    resolve_pumped_storage_dispatch_adder("PJM", cfg),
                )
            else:
                self.assertEqual(u.vom, 17.5)

    def test_adder_reaches_storage_arrays(self):
        cfg = ScenarioConfig(iso="ERCOT").with_overrides(
            battery_dispatch_adder=12.0
        )
        units = load_eia860_storage("ERCOT", 2024, cfg)
        arrays = storage_units_to_arrays(
            units, [u.zone for u in units]
        )
        self.assertTrue((arrays.vom == 12.0).all())


def _battery_units(units):
    """Return the non-pumped-storage units of an EIA-860 storage fleet."""
    return [u for u in units if u.tech_name != "pumped_storage"]


class TestEIA860CAISOBatteryFleet(unittest.TestCase):
    """The CAISO BESS fleet built from the EIA-860 energy-storage schedule."""

    def test_2024_capacity_matches_published(self):
        # California's grid-scale battery fleet crossed 10 GW during 2024
        # (CEC, "California Exceeds 10,000 MW of Battery Storage", 2024);
        # CAISO's DMM 2024 annual report puts the ISO fleet at ~11 GW by
        # year-end, and the EIA-860 CISO-BA sum is 11.1 GW. The loader
        # must land in that band.
        units = _battery_units(
            load_eia860_storage("CAISO", 2024, ScenarioConfig(iso="CAISO"))
        )
        total_mw = sum(u.power_cap_mw for u in units)
        self.assertGreater(total_mw, 10_000.0)
        self.assertLess(total_mw, 12_500.0)

    def test_fleet_matches_eia860_totals_per_year(self):
        # Acceptance check: the modeled fleet reproduces the EIA-860
        # year-end power and energy totals, recomputed independently from
        # the raw parquet through the same eGRID/EIA-860 zone lookup.
        import pandas as pd

        from market_sim.data.fleet import EIA_860_DIR
        from market_sim.data.zone_assignment import build_zone_lookup

        path = EIA_860_DIR / "eia860_energy_storage_operable.parquet"
        if not path.exists():
            self.skipTest("EIA-860 energy-storage parquet not present")
        lookup = build_zone_lookup("CAISO")
        df = pd.read_parquet(path)
        df = df[df["Status"].astype(str).str.strip().str.upper() == "OP"]
        power = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce")
        energy = pd.to_numeric(
            df["Nameplate Energy Capacity (MWh)"], errors="coerce"
        )
        op_year = pd.to_numeric(df["Operating Year"], errors="coerce")
        in_iso = df["Plant Code"].map(
            lambda c: c == c and lookup.get(int(c)) is not None
        ).astype(bool)

        for year in (2023, 2024):
            online = in_iso & power.notna() & (power > 0) & ~(op_year > year)
            expected_mw = float(power[online].sum())
            expected_mwh = float(energy[online].sum())
            units = _battery_units(load_eia860_storage(
                "CAISO", year, ScenarioConfig(iso="CAISO")
            ))
            self.assertAlmostEqual(
                sum(u.power_cap_mw for u in units), expected_mw, delta=1.0,
            )
            self.assertAlmostEqual(
                sum(u.energy_cap_mwh for u in units), expected_mwh,
                delta=1.0,
            )

    def test_duration_carried_from_eia860_energy_capacity(self):
        # EIA-860 reports energy capacity directly; the CAISO fleet averages
        # ~3.4 h (not the 4 h li-ion default), and that measured duration
        # must reach the SOC bound.
        units = _battery_units(
            load_eia860_storage("CAISO", 2024, ScenarioConfig(iso="CAISO"))
        )
        duration = (
            sum(u.energy_cap_mwh for u in units)
            / sum(u.power_cap_mw for u in units)
        )
        self.assertGreater(duration, 3.0)
        self.assertLess(duration, 4.0)


class TestStorageVintageRamp(unittest.TestCase):
    """The intra-year COD capacity ramp (``storage_vintage_ramp``)."""

    RAMP_CONFIG = ScenarioConfig(iso="CAISO", storage_vintage_ramp=True)

    def test_caiso_ramp_applies_mid_year(self):
        # CAISO commissioned ~3.6 GW during 2024 (EIA-860), so with the ramp
        # on, January online capacity must sit well below December, and the
        # monthly profile must be nondecreasing with December equal to the
        # year-end scalar caps.
        units = _battery_units(
            load_eia860_storage("CAISO", 2024, self.RAMP_CONFIG)
        )
        ramped = [u for u in units if u.monthly_power_mw is not None]
        self.assertTrue(ramped)
        jan = sum(u.monthly_power_mw[0] for u in ramped)
        dec = sum(u.monthly_power_mw[-1] for u in ramped)
        self.assertLess(jan, dec - 2_000.0)
        for u in ramped:
            self.assertEqual(len(u.monthly_power_mw), 12)
            self.assertAlmostEqual(u.monthly_power_mw[-1], u.power_cap_mw)
            self.assertAlmostEqual(u.monthly_energy_mwh[-1], u.energy_cap_mwh)
            for m in range(1, 12):  # m: month index
                self.assertGreaterEqual(
                    u.monthly_power_mw[m], u.monthly_power_mw[m - 1]
                )

    def test_cap_profiles_expand_to_hours(self):
        units = load_eia860_storage("CAISO", 2024, self.RAMP_CONFIG)
        arrays = storage_units_to_arrays(
            units, get_iso_config("CAISO").zone_names
        )
        power, energy = storage_cap_profiles(units, arrays, 8760)
        self.assertEqual(power.shape, (arrays.n_storage, 8760))
        self.assertEqual(energy.shape, (arrays.n_storage, 8760))
        # Capacity steps up across the year; December hours carry the
        # year-end caps.
        self.assertLess(power[:, 0].sum(), power[:, -1].sum())
        np.testing.assert_allclose(power[:, -1], arrays.power_cap)
        np.testing.assert_allclose(energy[:, -1], arrays.energy_cap)

    def test_cap_profiles_static_without_ramp(self):
        # Ramp off: the static 1-D arrays pass through untouched, so the
        # LP bounds (and every existing backcast) are bit-identical.
        units = load_eia860_storage("CAISO", 2024, ScenarioConfig(iso="CAISO"))
        arrays = storage_units_to_arrays(
            units, get_iso_config("CAISO").zone_names
        )
        power, energy = storage_cap_profiles(units, arrays, 8760)
        self.assertIs(power, arrays.power_cap)
        self.assertIs(energy, arrays.energy_cap)

    def test_ercot_pjm_default_fleets_unchanged(self):
        # The ramp is a per-ISO calibration opt-in: with the default config
        # ERCOT and PJM keep flat year-end fleets and zero-cost battery
        # discharge, leaving their calibrated backcasts untouched.
        for iso in ("ERCOT", "PJM"):
            units = load_eia860_storage(iso, 2024, ScenarioConfig(iso=iso))
            for u in units:
                self.assertIsNone(u.monthly_power_mw)
                self.assertIsNone(u.monthly_energy_mwh)
                if u.tech_name != "pumped_storage":
                    self.assertEqual(u.vom, 0.0)

    def test_dispatch_honors_hour_varying_caps(self):
        # A unit offline in day 1 (caps 0) and online in day 2 (100 MW /
        # 400 MWh) must sit idle through day 1's identical price spread and
        # arbitrage only day 2.
        T = 48
        fleet = _make_fleet(["Z0", "Z0"], ["Z0"], hours=T, pmax=400.0)
        fleet.pmax[0] = 300.0  # cheap gen short of the peak -> price spread
        mc = np.vstack([np.full(T, 20.0), np.full(T, 80.0)])
        demand = np.full((1, T), 200.0)
        demand[0, 12:24] = 400.0
        demand[0, 36:48] = 400.0
        power_cap = np.zeros((1, T))
        power_cap[0, 24:] = 100.0
        energy_cap = np.zeros((1, T))
        energy_cap[0, 24:] = 400.0
        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=T,
            wind_cf=np.zeros((1, T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
            storage_power_cap=power_cap,
            storage_energy_cap=energy_cap,
            storage_zone_idx=np.array([0]),
            eta_chg=np.array([0.92]),
            eta_dis=np.array([0.92]),
        )
        charge = result.storage_charge[0]
        discharge = result.storage_discharge[0]
        self.assertAlmostEqual(charge[:24].sum(), 0.0, places=6)
        self.assertAlmostEqual(discharge[:24].sum(), 0.0, places=6)
        self.assertGreater(discharge[24:].sum(), 0.0)
        self.assertLessEqual(charge.max(), 100.0 + 1e-6)


if __name__ == "__main__":
    unittest.main()
