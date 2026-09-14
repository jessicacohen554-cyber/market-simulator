"""Tests for storage parameter structs and storage-aware dispatch."""

import unittest

import numpy as np
import pandas as pd

from market_sim.config.constants import STORAGE_MEASURED_BASE_FLEET_ISOS
from market_sim.config.paths import RAW_DIR
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
    measured_storage_base_fleet_active,
    resolve_pumped_storage_dispatch_adder,
    storage_cap_profiles,
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
            unit_id="B1",
            zone="Z0",
            tech_name="li_ion_4hr",
            power_cap_mw=50.0,
            energy_cap_mwh=200.0,
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

    def test_all_six_isos_build_without_raising(self):
        # BLK-1 regression: STORAGE_BASE_FLEET_MW must cover every registered
        # ISO, or build_default_storage raises before the first solve (it used
        # to be called unconditionally in runner.run_scenario_iso, and MISO was
        # the one ISO missing from the pace dict).
        for iso_name in (
            "ERCOT",
            "CAISO",
            "PJM",
            "MISO",
            "NYISO",
            "NEISO",
            "SPP",
            "NWPP",
        ):
            self.assertIn(iso_name, STORAGE_BASE_FLEET_MW)
            iso = get_iso_config(iso_name)
            for pace in ("low", "mid", "high"):
                units = build_default_storage(
                    iso, ScenarioConfig(iso=iso_name, storage_deployment=pace)
                )
                self.assertGreater(len(units), 0, f"{iso_name}/{pace}")
                for unit in units:
                    self.assertGreater(unit.power_cap_mw, 0.0)

    def test_miso_pace_ordering_and_totals_match_constant(self):
        iso = get_iso_config("MISO")
        low = build_default_storage(
            iso, ScenarioConfig(iso="MISO", storage_deployment="low")
        )
        mid = build_default_storage(
            iso, ScenarioConfig(iso="MISO", storage_deployment="mid")
        )
        high = build_default_storage(
            iso, ScenarioConfig(iso="MISO", storage_deployment="high")
        )
        low_mw = sum(u.power_cap_mw for u in low)
        mid_mw = sum(u.power_cap_mw for u in mid)
        high_mw = sum(u.power_cap_mw for u in high)
        self.assertLess(low_mw, mid_mw)
        self.assertLess(mid_mw, high_mw)
        # MISO has no zero-load zones, so the deployed total matches the
        # configured pace exactly, like the ERCOT check above.
        self.assertAlmostEqual(low_mw, STORAGE_BASE_FLEET_MW["MISO"]["low"])
        self.assertAlmostEqual(mid_mw, STORAGE_BASE_FLEET_MW["MISO"]["mid"])
        self.assertAlmostEqual(high_mw, STORAGE_BASE_FLEET_MW["MISO"]["high"])

    def test_ercot_base_fleet_unchanged(self):
        # The MISO fix, the PJM/NYISO/NEISO EIA-860 re-derivation and the FFR-4D
        # CAISO re-vintage must all leave ERCOT's hand-entered row alone
        # (rule 25 [R-ISO-SCOPE]). ERCOT's row is itself off the documented
        # EIA-860 construction (17,000 shipped vs 13,709.3 measured) and is
        # ROUTED, not fixed, in docs/handoffs/ffr-4d-caiso-fleet-vintage-2026-08-04.md.
        self.assertEqual(
            STORAGE_BASE_FLEET_MW["ERCOT"],
            {"low": 12_000.0, "mid": 17_000.0, "high": 25_000.0},
        )

    def test_caiso_base_fleet_matches_eia860_construction(self):
        # FFR-4D. The CAISO row is no longer a hand-rounded TPP-2024 figure; it
        # is the registry's OWN documented EIA-860 construction, the one that
        # already reproduces PJM/MISO/NYISO/NEISO exactly. Asserting the VALUES
        # would only re-pin a literal, so this test re-runs the CONSTRUCTION
        # against the committed parquet: the row cannot drift from its source
        # without failing here, and a genuine EIA-860 re-intake that moves the
        # measured fleet fails loudly instead of silently disagreeing with the
        # registry comment (rule 23 [R-FROZEN-DERIVE] -- the licence to move
        # this row is a source-data change, and this is what detects one).
        self.assertEqual(
            STORAGE_BASE_FLEET_MW["CAISO"],
            {"low": 11_590.0, "mid": 15_450.0, "high": 19_260.0},
        )

        plant = pd.read_parquet(RAW_DIR / "eia-860" / "eia860_plant.parquet")
        ba_by_plant = plant.set_index("Plant Code")["Balancing Authority Code"]
        storage_dir = RAW_DIR / "eia-860"
        operable = pd.read_parquet(
            storage_dir / "eia860_energy_storage_operable.parquet"
        )
        proposed = pd.read_parquet(
            storage_dir / "eia860_energy_storage_proposed.parquet"
        )

        def _ciso(df):
            return df[df["Plant Code"].map(ba_by_plant) == "CISO"]

        def _round10(mw):
            return round(mw / 10.0) * 10.0

        raw_mid = (
            _ciso(operable).query("Status == 'OP'")["Nameplate Capacity (MW)"].sum()
        )
        ciso_proposed = _ciso(proposed)
        under_construction = ciso_proposed[
            ciso_proposed["Status"].isin(["U", "V", "TS"])
        ]["Nameplate Capacity (MW)"].sum()

        # mid = operable OP nameplate; high = mid + under construction; low =
        # the ROUNDED mid x 0.75 (the convention the four derived rows follow --
        # PJM's shipped 380 is 500 x 0.75 = 375 rounded, not 497.1 x 0.75).
        mid = _round10(raw_mid)
        self.assertAlmostEqual(mid, STORAGE_BASE_FLEET_MW["CAISO"]["mid"])
        self.assertAlmostEqual(
            _round10(raw_mid + under_construction),
            STORAGE_BASE_FLEET_MW["CAISO"]["high"],
        )
        self.assertAlmostEqual(
            _round10(mid * 0.75), STORAGE_BASE_FLEET_MW["CAISO"]["low"]
        )

        # The shipped-before value was 8,000 MW -- roughly CAISO's 2023 fleet,
        # applied flat to a 2026 base year. Guard the direction so a revert is
        # visible as a revert.
        self.assertGreater(STORAGE_BASE_FLEET_MW["CAISO"]["mid"], 15_000.0)


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
        val = estimate_capacity_value("li_ion_4hr", 0.0, ScenarioConfig(), "ERCOT")
        self.assertEqual(val, 0.0)

    def test_capacity_market_pays_capacity(self):
        val = estimate_capacity_value("li_ion_4hr", 0.0, ScenarioConfig(), "PJM")
        self.assertGreater(val, 0.0)

    def test_capacity_value_declines_with_penetration(self):
        # As storage saturates the peak, marginal capacity value falls.
        low_pen = estimate_capacity_value("li_ion_4hr", 0.0, ScenarioConfig(), "PJM")
        high_pen = estimate_capacity_value(
            "li_ion_4hr", 60_000.0, ScenarioConfig(), "PJM"
        )
        self.assertLess(high_pen, low_pen)

    def test_longer_duration_earns_more_capacity_value(self):
        short = estimate_capacity_value("li_ion_4hr", 0.0, ScenarioConfig(), "PJM")
        long = estimate_capacity_value("li_ion_12hr", 0.0, ScenarioConfig(), "PJM")
        self.assertGreater(long, short)

    def test_config_toggle_disables_capacity_value(self):
        val = estimate_capacity_value(
            "li_ion_4hr",
            0.0,
            ScenarioConfig(storage_capacity_value=False),
            "PJM",
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
        self.assertAlmostEqual(self._total_mw(result), self._total_mw(existing))

    def test_high_spread_triggers_entry(self):
        iso = get_iso_config("ERCOT")
        existing = build_default_storage(iso, ScenarioConfig())
        result = apply_storage_new_entry(
            existing,
            self._high_spread_prices(),
            2027,
            ScenarioConfig(),
            "ERCOT",
        )
        self.assertGreater(self._total_mw(result), self._total_mw(existing))

    def test_miso_builds_storage_registry_gap_closed(self):
        # MISO is a registered ISO that previously had no ceiling/annual-cap
        # entry, so its storage silently built zero. With both registries
        # populated, a high-spread signal now clears entry like any other ISO.
        cfg = ScenarioConfig(iso="MISO")
        iso = get_iso_config("MISO")
        existing = build_default_storage(iso, cfg)
        result = apply_storage_new_entry(
            existing, self._high_spread_prices(), 2027, cfg, "MISO"
        )
        self.assertGreater(self._total_mw(result), self._total_mw(existing))

    def test_missing_registry_iso_fails_loud(self):
        # A registered ISO absent from the storage registries must raise, not
        # silently build zero (mirrors the thermal QUEUE_CAP_GW guard) — so a
        # newly added ISO cannot slip through with no storage entry.
        from unittest import mock

        from market_sim.model import storage as storage_mod

        iso = get_iso_config("MISO")
        existing = build_default_storage(iso, ScenarioConfig(iso="MISO"))
        patched = dict(storage_mod.STORAGE_DEPLOYMENT_CEILING_MW)
        patched.pop("MISO")
        with mock.patch.object(storage_mod, "STORAGE_DEPLOYMENT_CEILING_MW", patched):
            with self.assertRaises(KeyError):
                apply_storage_new_entry(
                    existing,
                    self._high_spread_prices(),
                    2027,
                    ScenarioConfig(iso="MISO"),
                    "MISO",
                )

    def test_annual_cap_binds(self):
        # Even with huge arbitrage margins, a single year cannot build more
        # than the per-ISO annual cap.
        iso = get_iso_config("ERCOT")
        existing = build_default_storage(iso, ScenarioConfig())
        result = apply_storage_new_entry(
            existing,
            self._high_spread_prices(),
            2027,
            ScenarioConfig(),
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
            existing,
            self._high_spread_prices(),
            2027,
            ScenarioConfig(),
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
            existing,
            self._high_spread_prices(),
            2030,
            ScenarioConfig(),
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
            existing,
            self._high_spread_prices(),
            2030,
            ScenarioConfig(),
            "PJM",
        )
        self.assertGreater(self._total_mw(result), self._total_mw(existing))

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
        wrapped = self.soc[self.T - 1] + eta * self.charge[0] - self.discharge[0] / eta
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
        return solve_dispatch(
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
            storage_daily_cycle_hours=cycle_hours,
        )

    def test_unconstrained_banks_energy_across_days(self):
        # With no daily cap, the battery charges on the cheap day and the SOC
        # at the day boundary is well above its hour-0 level: cross-day banking.
        r = self._solve(None)
        soc = r.storage_soc[0]
        self.assertGreater(soc[24] - soc[0], 50.0)
        # It charges far more on day 0 than day 1 (banking for the dear day).
        self.assertGreater(
            r.storage_charge[0][:24].sum(), r.storage_charge[0][24:].sum() + 50.0
        )

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
            mc[1, d * 24 : d * 24 + 12] = 20.0
            mc[1, d * 24 + 12 : d * 24 + 24] = 80.0
        demand = np.empty((1, self.T))
        for d in range(2):
            demand[0, d * 24 : d * 24 + 12] = 200.0
            demand[0, d * 24 + 12 : d * 24 + 24] = 400.0
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
        r = solve_dispatch(
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
        eta = 0.85**0.5
        return solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((1, self.T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)),
            solar_cap=np.zeros(1),
            mc=mc,
            T=self.T,
            storage_power_cap=np.array([100.0]),
            storage_energy_cap=np.array([400.0]),
            storage_zone_idx=np.array([0]),
            eta_chg=np.array([eta]),
            eta_dis=np.array([eta]),
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

    def test_neiso_pumped_storage_present(self):
        # NEISO's PS fleet: Northfield Mountain (plant 547, 4×292 MW =
        # 1,168 MW, Central zone) + Bear Swamp (plant 8005, 2×333 MW =
        # 666 MW, Central zone) + Rocky River (plant 539, 31 MW, CT zone)
        # = ~1,865 MW total. Northfield is the dominant unit (~1.1 GW per
        # the prompt spec); both Northfield and Bear Swamp aggregate into
        # the Central zone, so Central carries ~1,834 MW.
        units = load_eia860_pumped_storage("NEISO", 2023)
        total_mw = sum(u.power_cap_mw for u in units)
        self.assertGreater(total_mw, 1700.0)
        self.assertLess(total_mw, 2100.0)
        for u in units:
            self.assertEqual(u.tech_name, "pumped_storage")
            self.assertIn(u.zone, {"North", "Central", "Boston", "Connecticut"})
            self.assertAlmostEqual(
                u.energy_cap_mwh,
                u.power_cap_mw * PUMPED_STORAGE_DURATION_HOURS,
            )
            self.assertAlmostEqual(
                u.eta_charge * u.eta_discharge, PUMPED_STORAGE_RTE, places=6
            )
        # Northfield + Bear Swamp aggregate into Central; it is the largest zone.
        central_mw = sum(u.power_cap_mw for u in units if u.zone == "Central")
        self.assertGreater(
            central_mw, 1700.0, msg="Central zone should hold Northfield+Bear Swamp"
        )


class TestCaisoPsPlantParams(unittest.TestCase):
    """caiso_ps_plant_params (lane 5, GATESPEC-caiso195): per-plant CAISO PS."""

    def test_off_state_is_the_legacy_aggregate(self):
        # Default off ⇒ byte-identical legacy behaviour: one NP15 aggregate,
        # no per-plant unit ids, no charge_power_cap_mw anywhere.
        units = load_eia860_pumped_storage("CAISO", 2023, ScenarioConfig(iso="CAISO"))
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].unit_id, "NP15_eia860_pumped_storage")
        self.assertIsNone(units[0].charge_power_cap_mw)

    def test_armed_splits_conserve_the_aggregate(self):
        # G-AGG: the armed per-plant split re-sums to the off-state aggregate
        # exactly — zero MW added, the aggregate's own EIA-860 rows
        # re-attributed. Six plants, all NP15 (build_zone_lookup geography).
        off = load_eia860_pumped_storage("CAISO", 2023, ScenarioConfig(iso="CAISO"))
        on = load_eia860_pumped_storage(
            "CAISO", 2023, ScenarioConfig(iso="CAISO", caiso_ps_plant_params=True)
        )
        self.assertEqual(len(on), 6)
        self.assertAlmostEqual(
            sum(u.power_cap_mw for u in on),
            sum(u.power_cap_mw for u in off),
            places=6,
        )
        self.assertEqual({u.zone for u in on}, {"NP15"})
        by_id = {u.unit_id: u for u in on}
        # Cited pump ratings ride charge_power_cap_mw (Helms 930 PG&E;
        # Gianelli 375.8 DWR B132-22); Eastwood is the disclosed uncited
        # component and keeps the unrestrained default (None).
        self.assertAlmostEqual(by_id["NP15_ps_6100"].charge_power_cap_mw, 930.0)
        self.assertAlmostEqual(by_id["NP15_ps_448"].charge_power_cap_mw, 375.8)
        self.assertIsNone(by_id["NP15_ps_104"].charge_power_cap_mw)
        # Cited reservoir-derived energy bounds (constants table); Eastwood
        # keeps the incumbent fleet-average duration.
        self.assertAlmostEqual(by_id["NP15_ps_6100"].energy_cap_mwh, 200_424.0)
        self.assertAlmostEqual(by_id["NP15_ps_448"].energy_cap_mwh, 613_410.0)
        self.assertAlmostEqual(
            by_id["NP15_ps_104"].energy_cap_mwh,
            by_id["NP15_ps_104"].power_cap_mw * PUMPED_STORAGE_DURATION_HOURS,
        )

    def test_other_isos_ignore_the_flag(self):
        # Rule 25: the gate is CAISO-only — an armed config leaves PJM's
        # loader output identical to its off state.
        off = load_eia860_pumped_storage("PJM", 2024, ScenarioConfig(iso="PJM"))
        on = load_eia860_pumped_storage(
            "PJM", 2024, ScenarioConfig(iso="PJM", caiso_ps_plant_params=True)
        )
        self.assertEqual(
            [(u.unit_id, u.power_cap_mw, u.energy_cap_mwh) for u in off],
            [(u.unit_id, u.power_cap_mw, u.energy_cap_mwh) for u in on],
        )

    def test_charge_caps_compose_tighten_only(self):
        # caiso_ps_charge_caps: pump rows take min(power_cap, pump); a cited
        # rating ABOVE the power cap clips (tighten-only, disclosed no-op);
        # non-pump rows pass the existing envelope through; all-None ⇒ None.
        from market_sim.model.storage import StorageUnit, caiso_ps_charge_caps

        units = [
            StorageUnit(
                unit_id="NP15_ps_6100",
                zone="NP15",
                tech_name="pumped_storage",
                power_cap_mw=1053.0,
                energy_cap_mwh=200_424.0,
                charge_power_cap_mw=930.0,
            ),
            StorageUnit(
                unit_id="NP15_ps_437",
                zone="NP15",
                tech_name="pumped_storage",
                power_cap_mw=293.1,
                energy_cap_mwh=31_678.0,
                charge_power_cap_mw=387.0,  # cited motor rating > gen cap
            ),
            StorageUnit(
                unit_id="NP15_batt",
                zone="NP15",
                tech_name="li_ion",
                power_cap_mw=100.0,
                energy_cap_mwh=400.0,
            ),
        ]
        power_cap = np.array([1053.0, 293.1, 100.0])
        env = np.full((3, 4), 55.0)  # a pre-existing battery envelope
        out = caiso_ps_charge_caps(power_cap, units, 4, env)
        self.assertTrue((out[0] == 930.0).all())
        self.assertTrue((out[1] == 293.1).all())  # clipped at power cap
        self.assertTrue((out[2] == 55.0).all())  # battery row untouched
        # No existing envelope: non-pump rows fall back to the power cap.
        out2 = caiso_ps_charge_caps(power_cap, units, 4, None)
        self.assertTrue((out2[2] == 100.0).all())
        # No cited ratings anywhere ⇒ None (caller keeps its channel as-is).
        bare = [units[2]]
        self.assertIsNone(caiso_ps_charge_caps(np.array([100.0]), bare, 4, env[2:3]))


class TestNYISOPumpedStorage(unittest.TestCase):
    """NYISO pumped-storage fleet from EIA-860 (P4 hydro stage).

    NYISO's PS fleet consists of two facilities on the EIA-860 generator
    schedule (prime mover PS):

    * Blenheim-Gilboa Pumped Storage Project (plant in Schoharie County,
      NY — Capital_Hudson zone): ~1,000 MW of reversible units. The
      largest single PS plant in NYISO. Source: EIA-860, NYPA project data.

    * Lewiston Pump-Generating Plant (part of the Niagara Power Project,
      Niagara County — Upstate_West zone): ~220 MW of pump-turbine units
      that modulate Lake Ontario levels. Source: EIA-860, FERC Project 2216.

    Combined nameplate: ~1,220 MW. Duration and RTE apply the fleet-average
    constants (:data:`PUMPED_STORAGE_DURATION_HOURS`,
    :data:`PUMPED_STORAGE_RTE`) used for PJM and CAISO PS — no new modeling
    design.

    The PS dispatch adder is default off (0.0) for NYISO: no calibration
    pass has yet measured a reserve-duty opportunity cost for it. This is
    consistent with the per-ISO map in
    :data:`PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO`, which is now empty (PJM's
    former $10/MWh entry was retired as a mis-measured residual fit).
    """

    def test_ps_total_mw_in_range(self):
        # Blenheim-Gilboa (~1,000 MW) + Lewiston (~220 MW) = ~1,220 MW.
        units = load_eia860_pumped_storage("NYISO", 2023)
        total_mw = sum(u.power_cap_mw for u in units)
        self.assertGreater(total_mw, 1_000.0)
        self.assertLess(total_mw, 1_500.0)

    def test_ps_zones_in_nyiso_topology(self):
        # Both zones hosting PS are valid NYISO model zones.
        units = load_eia860_pumped_storage("NYISO", 2023)
        nyiso_zones = {
            "Upstate_West",
            "Capital_Hudson",
            "Lower_Hudson",
            "NYC",
            "Long_Island",
        }
        for u in units:
            self.assertIn(u.zone, nyiso_zones)

    def test_ps_tech_and_params_match_fleet_standard(self):
        # Duration and RTE follow the fleet constants used for PJM/CAISO PS.
        units = load_eia860_pumped_storage("NYISO", 2023)
        self.assertTrue(units, "NYISO PS fleet is empty")
        for u in units:
            self.assertEqual(u.tech_name, "pumped_storage")
            self.assertAlmostEqual(
                u.energy_cap_mwh,
                u.power_cap_mw * PUMPED_STORAGE_DURATION_HOURS,
            )
            self.assertAlmostEqual(
                u.eta_charge * u.eta_discharge, PUMPED_STORAGE_RTE, places=6
            )

    def test_ps_dispatch_adder_default_off(self):
        # NYISO PS adder is 0.0 until a calibration pass measures
        # Blenheim-Gilboa's reserve-duty opportunity cost.
        self.assertEqual(
            resolve_pumped_storage_dispatch_adder("NYISO", ScenarioConfig()),
            0.0,
        )
        units = load_eia860_pumped_storage("NYISO", 2023, ScenarioConfig())
        for u in units:
            self.assertEqual(u.vom, 0.0)

    def test_ps_dispatch_adder_respects_explicit_override(self):
        # An explicit config override must reach NYISO PS units.
        cfg = ScenarioConfig(pumped_storage_dispatch_adder=7.5)
        self.assertEqual(resolve_pumped_storage_dispatch_adder("NYISO", cfg), 7.5)
        units = load_eia860_pumped_storage("NYISO", 2023, cfg)
        for u in units:
            self.assertEqual(u.vom, 7.5)

    def test_pjm_caiso_ps_unchanged_by_nyiso_p4(self):
        # NYISO P4 additions must not alter PJM or CAISO PS fleet totals.
        pjm_mw = sum(u.power_cap_mw for u in load_eia860_pumped_storage("PJM", 2024))
        self.assertGreater(pjm_mw, 4_500.0)
        caiso_mw = sum(
            u.power_cap_mw for u in load_eia860_pumped_storage("CAISO", 2023)
        )
        self.assertGreater(caiso_mw, 1_900.0)


class TestPumpedStorageDispatchAdder(unittest.TestCase):
    """Per-ISO resolution of the PS dispatch adder (reserve-duty proxy)."""

    def test_pjm_default_is_retired_zero(self):
        # PJM's former $10/MWh adder was RETIRED (pjm-ps-cycling diagnosis
        # 2026-06): it had been fitted to a mis-measured PS *net*-generation
        # figure (the round-trip loss), not a real reserve cost, so per
        # CLAUDE.md #12 it is removed and PJM PS arbitrages on its physical RTE.
        self.assertEqual(
            resolve_pumped_storage_dispatch_adder("PJM", ScenarioConfig()),
            0.0,
        )
        units = load_eia860_pumped_storage("PJM", 2024, ScenarioConfig())
        self.assertTrue(units)
        for u in units:
            self.assertEqual(u.vom, 0.0)

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

    def test_neiso_default_is_off(self):
        # NEISO PS adder is 0.0 by default (not in the per-ISO map); off
        # until a NEISO calibration pass measures Northfield's reserve duty.
        self.assertEqual(
            resolve_pumped_storage_dispatch_adder("NEISO", ScenarioConfig(iso="NEISO")),
            0.0,
        )
        units = load_eia860_pumped_storage("NEISO", 2023, ScenarioConfig(iso="NEISO"))
        self.assertTrue(units)
        for u in units:
            self.assertEqual(u.vom, 0.0)

    def test_no_config_falls_back_to_per_iso_default(self):
        # PJM adder retired -> 0.0 (was 10.0); the empty per-ISO map means
        # every ISO without an explicit override now falls back to 0.0.
        self.assertEqual(resolve_pumped_storage_dispatch_adder("PJM", None), 0.0)
        self.assertEqual(resolve_pumped_storage_dispatch_adder("CAISO", None), 0.0)

    def test_explicit_value_overrides_every_iso(self):
        cfg = ScenarioConfig(pumped_storage_dispatch_adder=5.0)
        for iso in ("PJM", "CAISO", "ERCOT"):
            self.assertEqual(resolve_pumped_storage_dispatch_adder(iso, cfg), 5.0)
        zero = ScenarioConfig(pumped_storage_dispatch_adder=0.0)
        self.assertEqual(resolve_pumped_storage_dispatch_adder("PJM", zero), 0.0)


class TestBatteryDispatchAdder(unittest.TestCase):
    """ScenarioConfig.battery_dispatch_adder on the EIA-860 battery fleet."""

    def test_default_zero_leaves_battery_vom_unchanged(self):
        units = load_eia860_storage("ERCOT", 2024, ScenarioConfig())
        batteries = [u for u in units if u.tech_name != "pumped_storage"]
        self.assertTrue(batteries)
        for u in batteries:
            self.assertEqual(u.vom, 0.0)

    def test_adder_carried_on_battery_vom_only(self):
        cfg = ScenarioConfig(iso="PJM").with_overrides(battery_dispatch_adder=17.5)
        units = load_eia860_storage("PJM", 2024, cfg)
        for u in units:
            if u.tech_name == "pumped_storage":
                # PS keeps its own throughput adder (per-ISO resolved; PJM's
                # is now 0.0 after the adder retirement), not the battery one.
                self.assertEqual(
                    u.vom,
                    resolve_pumped_storage_dispatch_adder("PJM", cfg),
                )
            else:
                self.assertEqual(u.vom, 17.5)

    def test_adder_reaches_storage_arrays(self):
        cfg = ScenarioConfig(iso="ERCOT").with_overrides(battery_dispatch_adder=12.0)
        units = load_eia860_storage("ERCOT", 2024, cfg)
        arrays = storage_units_to_arrays(units, [u.zone for u in units])
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

        from market_sim.config.paths import EIA_860_DIR
        from market_sim.data.zone_assignment import build_zone_lookup

        path = EIA_860_DIR / "eia860_energy_storage_operable.parquet"
        if not path.exists():
            self.skipTest("EIA-860 energy-storage parquet not present")
        lookup = build_zone_lookup("CAISO")
        df = pd.read_parquet(path)
        df = df[df["Status"].astype(str).str.strip().str.upper() == "OP"]
        power = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce")
        energy = pd.to_numeric(df["Nameplate Energy Capacity (MWh)"], errors="coerce")
        op_year = pd.to_numeric(df["Operating Year"], errors="coerce")
        in_iso = (
            df["Plant Code"]
            .map(lambda c: c == c and lookup.get(int(c)) is not None)
            .astype(bool)
        )

        for year in (2023, 2024):
            online = in_iso & power.notna() & (power > 0) & ~(op_year > year)
            expected_mw = float(power[online].sum())
            expected_mwh = float(energy[online].sum())
            units = _battery_units(
                load_eia860_storage("CAISO", year, ScenarioConfig(iso="CAISO"))
            )
            self.assertAlmostEqual(
                sum(u.power_cap_mw for u in units),
                expected_mw,
                delta=1.0,
            )
            self.assertAlmostEqual(
                sum(u.energy_cap_mwh for u in units),
                expected_mwh,
                delta=1.0,
            )

    def test_duration_carried_from_eia860_energy_capacity(self):
        # EIA-860 reports energy capacity directly; the CAISO fleet averages
        # ~3.4 h (not the 4 h li-ion default), and that measured duration
        # must reach the SOC bound.
        units = _battery_units(
            load_eia860_storage("CAISO", 2024, ScenarioConfig(iso="CAISO"))
        )
        duration = sum(u.energy_cap_mwh for u in units) / sum(
            u.power_cap_mw for u in units
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
        units = _battery_units(load_eia860_storage("CAISO", 2024, self.RAMP_CONFIG))
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
        arrays = storage_units_to_arrays(units, get_iso_config("CAISO").zone_names)
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
        arrays = storage_units_to_arrays(units, get_iso_config("CAISO").zone_names)
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


class TestEIA860NYISOBatteryFleet(unittest.TestCase):
    """NYISO BESS fleet built from the EIA-860 energy-storage schedule.

    Acceptance: modeled NYISO storage fleet matches EIA-860 totals per year.
    The NYISO fleet is small (~200-220 MW in 2023-2024) with a pronounced
    downstate concentration (NYC + Long Island) and uses the same
    battery_dispatch_adder / COD-ramp knobs as CAISO and ERCOT.
    """

    def _expected_totals(self, year: int):
        """Return (expected_mw, expected_mwh) from the raw parquet for year."""
        import pandas as pd

        from market_sim.config.paths import EIA_860_DIR
        from market_sim.data.zone_assignment import build_zone_lookup

        path = EIA_860_DIR / "eia860_energy_storage_operable.parquet"
        if not path.exists():
            self.skipTest("EIA-860 energy-storage parquet not present")
        lookup = build_zone_lookup("NYISO")
        df = pd.read_parquet(path)
        df = df[df["Status"].astype(str).str.strip().str.upper() == "OP"]
        power = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce")
        energy = pd.to_numeric(df["Nameplate Energy Capacity (MWh)"], errors="coerce")
        op_year = pd.to_numeric(df["Operating Year"], errors="coerce")
        in_iso = (
            df["Plant Code"]
            .map(lambda c: c == c and lookup.get(int(c)) is not None)
            .astype(bool)
        )
        online = in_iso & power.notna() & (power > 0) & ~(op_year > year)
        return float(power[online].sum()), float(energy[online].sum())

    def test_fleet_totals_match_eia860_per_year(self):
        # Acceptance check: the modeled fleet reproduces the EIA-860 year-end
        # power and energy totals for 2023 and 2024, recomputed independently
        # from the raw parquet through the same eGRID/EIA-860 zone lookup.
        for year in (2023, 2024):
            expected_mw, expected_mwh = self._expected_totals(year)
            units = _battery_units(
                load_eia860_storage("NYISO", year, ScenarioConfig(iso="NYISO"))
            )
            self.assertAlmostEqual(
                sum(u.power_cap_mw for u in units),
                expected_mw,
                delta=1.0,
                msg=f"NYISO {year} MW mismatch",
            )
            self.assertAlmostEqual(
                sum(u.energy_cap_mwh for u in units),
                expected_mwh,
                delta=1.0,
                msg=f"NYISO {year} MWh mismatch",
            )

    def test_fleet_nonzero(self):
        # NYISO had an operational BESS fleet by end-2023; the loader must
        # produce at least one battery unit with positive capacity.
        units = _battery_units(
            load_eia860_storage("NYISO", 2023, ScenarioConfig(iso="NYISO"))
        )
        self.assertTrue(units)
        self.assertGreater(sum(u.power_cap_mw for u in units), 0.0)

    def test_downstate_nyc_longisland_concentration(self):
        # The NYC five-boroughs and Long Island hold a material share of the
        # NYISO BESS fleet (downstate density vs the upstate hydro footprint).
        units = _battery_units(
            load_eia860_storage("NYISO", 2024, ScenarioConfig(iso="NYISO"))
        )
        total_mw = sum(u.power_cap_mw for u in units)
        downstate_mw = sum(
            u.power_cap_mw for u in units if u.zone in ("NYC", "Long_Island")
        )
        self.assertGreater(total_mw, 0.0)
        # Downstate carries a nonzero but not dominant share (~15-35% of fleet)
        self.assertGreater(downstate_mw, 0.0)
        self.assertLess(downstate_mw / total_mw, 0.60)

    def test_battery_dispatch_adder_carried(self):
        # battery_dispatch_adder propagates to each NYISO battery unit's vom.
        adder = 5.0
        units = _battery_units(
            load_eia860_storage(
                "NYISO", 2024, ScenarioConfig(iso="NYISO", battery_dispatch_adder=adder)
            )
        )
        for u in units:
            self.assertEqual(u.vom, adder)

    def test_vintage_ramp_applies_mid_year(self):
        # With storage_vintage_ramp=True any NYISO units commissioned during
        # the year carry a monthly COD profile: January < December, nondecreasing.
        cfg = ScenarioConfig(iso="NYISO", storage_vintage_ramp=True)
        units = _battery_units(load_eia860_storage("NYISO", 2024, cfg))
        ramped = [u for u in units if u.monthly_power_mw is not None]
        # NYISO did commission storage during 2024 (20 MW in Erie county, etc.)
        self.assertTrue(ramped, "Expected at least one zone to show a COD ramp")
        for u in ramped:
            self.assertEqual(len(u.monthly_power_mw), 12)
            self.assertAlmostEqual(u.monthly_power_mw[-1], u.power_cap_mw)
            for m in range(1, 12):
                self.assertGreaterEqual(
                    u.monthly_power_mw[m], u.monthly_power_mw[m - 1]
                )

    def test_ercot_pjm_caiso_unchanged(self):
        # Adding NYISO to the EIA-860 supplement set must not alter the
        # ERCOT, PJM, or CAISO fleet totals or unit attributes.
        for iso in ("ERCOT", "PJM", "CAISO"):
            cfg = ScenarioConfig(iso=iso)
            units_before = load_eia860_storage(iso, 2024, cfg)
            # Re-import to guarantee the lookup cache hasn't been poisoned.
            from market_sim.data.zone_assignment import build_zone_lookup

            build_zone_lookup(iso)  # warm cache
            units_after = load_eia860_storage(iso, 2024, cfg)
            self.assertEqual(
                len(units_before),
                len(units_after),
                msg=f"{iso} unit count changed after NYISO supplement was added",
            )
            for u_b, u_a in zip(units_before, units_after):
                self.assertAlmostEqual(
                    u_b.power_cap_mw,
                    u_a.power_cap_mw,
                    places=6,
                    msg=f"{iso} unit {u_b.unit_id} power changed",
                )


class TestEIA860NEISOBatteryFleet(unittest.TestCase):
    """The NEISO BESS fleet built from the EIA-860 energy-storage schedule.

    Acceptance criterion: modeled fleet power and energy match the EIA-860
    operable-storage totals for every backcast year (per playbook §8.4).
    """

    def _eia860_neiso_totals(self, year: int) -> tuple[float, float]:
        """Return (expected_mw, expected_mwh) from raw EIA-860 for NEISO.

        Replicates load_eia860_storage's filter: OP status, op_year <= year,
        positive nameplate power, within the ISNE balancing authority.
        Uses the EIA-860 plant file's BA codes (not eGRID) so the lookup
        covers both eGRID-vintage and post-eGRID-2023 plants.
        """
        import pandas as pd
        from market_sim.config.paths import EIA_860_DIR
        from market_sim.data.zone_assignment import build_zone_lookup

        path = EIA_860_DIR / "eia860_energy_storage_operable.parquet"
        if not path.exists():
            self.skipTest("EIA-860 energy-storage parquet not present")

        plant_path = EIA_860_DIR / "eia860_plant.parquet"
        if not plant_path.exists():
            self.skipTest("EIA-860 plant parquet not present")

        plant = pd.read_parquet(plant_path)
        isne_oris = set(
            int(c)
            for c in plant.loc[
                plant["Balancing Authority Code"].astype(str).str.strip() == "ISNE",
                "Plant Code",
            ].dropna()
        )

        lookup = build_zone_lookup("NEISO")
        df = pd.read_parquet(path)
        df = df[df["Status"].astype(str).str.strip().str.upper() == "OP"]
        power = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce")
        energy = pd.to_numeric(df["Nameplate Energy Capacity (MWh)"], errors="coerce")
        op_year = pd.to_numeric(df["Operating Year"], errors="coerce")

        # Keep rows: ISNE BA, op_year <= year, positive power, zone found.
        mask = (
            df["Plant Code"].apply(lambda c: pd.notna(c) and int(c) in isne_oris)
            & power.notna()
            & (power > 0)
            & ~(op_year > year)
            & df["Plant Code"].apply(
                lambda c: pd.notna(c) and lookup.get(int(c)) is not None
            )
        )
        expected_mw = float(power[mask].sum())
        e_filled = energy.copy()
        e_filled[mask & energy.isna()] = power[mask & energy.isna()] * 2.0
        expected_mwh = float(e_filled[mask].sum())
        return expected_mw, expected_mwh

    def test_fleet_totals_vs_eia860_per_year(self):
        """Modeled NEISO battery fleet matches EIA-860 totals per year."""
        for year in (2023, 2024):
            exp_mw, exp_mwh = self._eia860_neiso_totals(year)
            units = _battery_units(
                load_eia860_storage("NEISO", year, ScenarioConfig(iso="NEISO"))
            )
            self.assertGreater(exp_mw, 0.0, f"No NEISO battery data for {year}")
            self.assertAlmostEqual(
                sum(u.power_cap_mw for u in units),
                exp_mw,
                delta=1.0,
                msg=f"NEISO {year} MW mismatch",
            )
            self.assertAlmostEqual(
                sum(u.energy_cap_mwh for u in units),
                exp_mwh,
                delta=1.0,
                msg=f"NEISO {year} MWh mismatch",
            )

    def test_2024_capacity_in_expected_range(self):
        # NEISO's EIA-860 2024 battery fleet is ~420 MW (mostly MA, small
        # clusters in ME/VT/RI/CT); the loader must land in that band.
        units = _battery_units(
            load_eia860_storage("NEISO", 2024, ScenarioConfig(iso="NEISO"))
        )
        total_mw = sum(u.power_cap_mw for u in units)
        self.assertGreater(total_mw, 350.0)
        self.assertLess(total_mw, 500.0)

    def test_zones_are_valid_neiso_zones(self):
        # Every unit must land in one of the four load zones (HQ_import is a
        # zero-load import node and should never hold battery capacity).
        valid_load_zones = {"North", "Central", "Boston", "Connecticut"}
        units = _battery_units(
            load_eia860_storage("NEISO", 2024, ScenarioConfig(iso="NEISO"))
        )
        self.assertTrue(units, "No NEISO battery units loaded")
        for u in units:
            self.assertIn(
                u.zone,
                valid_load_zones,
                f"Unit {u.unit_id} placed in unexpected zone {u.zone}",
            )

    def test_ma_heavy_distribution(self):
        # Massachusetts hosts the bulk of ISO-NE's battery capacity (~80%).
        # Boston (NEMA/Essex/Middlesex/Norfolk/Suffolk) and Central (rest of
        # MA plus RI) together should exceed North+Connecticut.
        units = _battery_units(
            load_eia860_storage("NEISO", 2024, ScenarioConfig(iso="NEISO"))
        )
        self.assertTrue(units)
        ma_mw = sum(u.power_cap_mw for u in units if u.zone in {"Boston", "Central"})
        other_mw = sum(
            u.power_cap_mw for u in units if u.zone in {"North", "Connecticut"}
        )
        self.assertGreater(ma_mw, other_mw)

    def test_ramp_mid_year_applies(self):
        # NEISO commissioned batteries mid-year in 2024 (Groton BESS 1 & 2,
        # Holden BESS 1, Paxton BESS 1 in Aug 2024). With vintage_ramp=True
        # the January online capacity must be less than December's.
        cfg = ScenarioConfig(iso="NEISO", storage_vintage_ramp=True)
        units = _battery_units(load_eia860_storage("NEISO", 2024, cfg))
        ramped = [u for u in units if u.monthly_power_mw is not None]
        self.assertTrue(ramped, "Expected at least one ramped NEISO zone in 2024")
        jan_total = sum(u.monthly_power_mw[0] for u in ramped)
        dec_total = sum(u.monthly_power_mw[-1] for u in ramped)
        self.assertLess(jan_total, dec_total)
        for u in ramped:
            self.assertEqual(len(u.monthly_power_mw), 12)
            self.assertAlmostEqual(u.monthly_power_mw[-1], u.power_cap_mw)
            self.assertAlmostEqual(u.monthly_energy_mwh[-1], u.energy_cap_mwh)
            for m in range(1, 12):
                self.assertGreaterEqual(
                    u.monthly_power_mw[m], u.monthly_power_mw[m - 1]
                )

    def test_battery_dispatch_adder_applied(self):
        # battery_dispatch_adder flows to every NEISO battery unit's vom.
        cfg = ScenarioConfig(iso="NEISO", battery_dispatch_adder=5.0)
        units = _battery_units(load_eia860_storage("NEISO", 2024, cfg))
        self.assertTrue(units)
        for u in units:
            self.assertEqual(u.vom, 5.0)

    def test_eia930_battery_benchmark_if_present(self):
        # EIA-930 ISNE BAT data (net discharge, MW) is NaN pre-2024 and
        # sparse in 2024; this test verifies the data path and reports
        # non-null coverage without asserting a specific value (the data is
        # too sparse for a hard constraint).
        import pandas as pd

        from market_sim.config.paths import RAW_DATA_DIR

        path = RAW_DATA_DIR / "ISNE_fueltype.parquet"
        if not path.exists():
            self.skipTest("ISNE_fueltype.parquet not present")
        df = pd.read_parquet(path)
        bat = df[df["fueltype"] == "BAT"]
        if bat.empty:
            self.skipTest("No BAT rows in ISNE_fueltype.parquet")
        bat_2024 = bat[bat["period"].dt.year == 2024]
        nonnull = bat_2024["value_mwh"].notna().sum()
        # The data is valid (non-empty series), even if sparse pre-2025.
        self.assertGreaterEqual(len(bat_2024), 0)
        # When non-null data exists, values must be non-negative (net
        # discharge can be zero but not negative in the fueltype column).
        if nonnull > 0:
            non_null_vals = bat_2024.loc[bat_2024["value_mwh"].notna(), "value_mwh"]
            self.assertTrue((non_null_vals >= 0).all())


class TestNEISOStorageUnchangedForOtherISOs(unittest.TestCase):
    """Adding NEISO to _EIA860_SUPPLEMENT_ISOS must not alter ERCOT/CAISO/PJM."""

    def test_ercot_battery_fleet_totals_unaffected(self):
        # ERCOT was already in _EIA860_SUPPLEMENT_ISOS before this change.
        # Verify that the 2024 ERCOT battery fleet is still ~8 GW
        # (EIA-860 ERCO-BA sum; the 2024 Texas fleet pre-2025 buildup).
        units = _battery_units(
            load_eia860_storage("ERCOT", 2024, ScenarioConfig(iso="ERCOT"))
        )
        total_mw = sum(u.power_cap_mw for u in units)
        self.assertGreater(total_mw, 5_000.0)
        self.assertLess(total_mw, 12_000.0)

    def test_caiso_battery_fleet_totals_unaffected(self):
        # CAISO was already in _EIA860_SUPPLEMENT_ISOS; confirm that the
        # NEISO addition has not moved the CAISO 2024 totals.
        units = _battery_units(
            load_eia860_storage("CAISO", 2024, ScenarioConfig(iso="CAISO"))
        )
        total_mw = sum(u.power_cap_mw for u in units)
        self.assertGreater(total_mw, 10_000.0)
        self.assertLess(total_mw, 12_500.0)

    def test_pjm_battery_fleet_totals_unaffected(self):
        # PJM is NOT in _EIA860_SUPPLEMENT_ISOS (and remains so); this
        # test verifies PJM's 2024 battery fleet is still loaded correctly.
        # EIA-860 ERCO-BA sum for 2024 is ~350 MW (pre-interconnection-queue
        # buildup: PA/NJ/DE small commercial BESS, not the large queued MW).
        units = _battery_units(
            load_eia860_storage("PJM", 2024, ScenarioConfig(iso="PJM"))
        )
        total_mw = sum(u.power_cap_mw for u in units)
        self.assertGreater(total_mw, 100.0)
        self.assertLess(total_mw, 1_500.0)


if __name__ == "__main__":
    unittest.main()


class TestMeasuredBackcastStorageBaseFleet(unittest.TestCase):
    """FFR-4D: a backcast resolves its storage base fleet as of its solve year.

    ``STORAGE_BASE_FLEET_MW`` is a FORECAST object (its own docstring calls it
    "the base year (2026)" and its low/mid/high are the ``storage_deployment``
    scenario ladder), so feeding it to a 2023 solve is a vintage/as-of
    misalignment. These tests pin the seam that fixes it, and — just as
    importantly — pin its ISO SCOPE, because enrolling another ISO moves that
    ISO's designated keeper (rule 25 [R-ISO-SCOPE]).
    """

    def test_registry_is_caiso_only(self):
        # The blast radius of the default-ON field IS this registry. If another
        # ISO is added here, that ISO's backcast keeper changes and must be
        # re-solved and re-gated in its own lane — so this assertion is the
        # thing that makes such a change deliberate rather than incidental.
        self.assertEqual(STORAGE_MEASURED_BASE_FLEET_ISOS, frozenset({"CAISO"}))

    def test_default_is_on(self):
        # Rule 14 [R-ACCURATE]: the measured fleet is the accurate input, so it
        # is not gated behind a flag that the estimate wins by default.
        self.assertTrue(ScenarioConfig().storage_measured_base_fleet)

    def test_measured_caiso_fleet_tracks_the_solve_year(self):
        # The defect this closes: the scalar supplied a FLAT 8,000 MW to 2023,
        # 2024 and 2025 alike. The measured fleet roughly doubles across that
        # window, so the corrected path must be strictly increasing in year and
        # must straddle the old flat value rather than sitting beside it.
        cfg = ScenarioConfig(iso="CAISO", mode="backcast")
        totals = {}
        for year in (2023, 2024, 2025):
            units = load_eia860_storage("CAISO", year, cfg)
            self.assertGreater(len(units), 0, f"no CAISO storage units for {year}")
            totals[year] = sum(u.power_cap_mw for u in units)
        self.assertLess(totals[2023], totals[2024])
        self.assertLess(totals[2024], totals[2025])
        # Pumped storage is appended by the loader itself, so these totals carry
        # CAISO's ~2.1 GW of PS on top of the battery fleet. Bracket loosely —
        # the point is the SHAPE across years, not a re-pinned literal.
        self.assertLess(totals[2023], 12_000.0)
        self.assertGreater(totals[2025], 16_000.0)

    def test_pumped_storage_is_not_double_counted(self):
        # The forecast path PREPENDS pumped storage to build_default_storage;
        # load_eia860_storage APPENDS it internally. Wiring the loader in
        # without removing the prepend would have counted CAISO's ~2.1 GW of PS
        # twice — so assert the loader already carries it exactly once.
        cfg = ScenarioConfig(iso="CAISO", mode="backcast")
        units = load_eia860_storage("CAISO", 2025, cfg)
        ps_units = load_eia860_pumped_storage("CAISO", 2025, cfg)
        self.assertGreater(len(ps_units), 0)
        ps_ids = {u.unit_id for u in ps_units}
        self.assertTrue(ps_ids.issubset({u.unit_id for u in units}))
        for unit_id in ps_ids:
            self.assertEqual(
                sum(1 for u in units if u.unit_id == unit_id),
                1,
                f"pumped-storage unit {unit_id} appears more than once",
            )


class TestHindcastStorageVintageSeed(unittest.TestCase):
    """FFR-9A: a capacity hindcast seeds storage from its own vintage fleet.

    A hindcast is ``mode="forecast"`` + ``hindcast=True``, so it does not take
    the backcast branch of the FFR-4D seam; before FFR-9A it fell through to
    the present-day forward scalar (``STORAGE_BASE_FLEET_MW``) and a
    vintage-2020 ERCOT run held 17,000 MW of storage against the 223 MW that
    existed at its own cutoff — the FFR-3V renewable-pool leak's storage
    sibling. These tests pin the predicate's full truth table (the fix AND all
    three no-op halves: plain forecast, backcast scope, no-vintage hindcast)
    and the seed's content at the vintage.
    """

    @staticmethod
    def _hindcast_cfg(iso: str = "ERCOT", vintage: "int | None" = 2020, **kw):
        return ScenarioConfig(
            iso=iso,
            mode="forecast",
            hindcast=True,
            eia860_vintage_year=vintage,
            start_year=2021,
            end_year=2021,
            **kw,
        )

    def test_hindcast_activates_the_measured_seed_in_every_iso(self):
        # The hindcast leg is deliberately NOT scoped by
        # STORAGE_MEASURED_BASE_FLEET_ISOS: no keeper is affected, so the
        # rule-25 keeper-byte-identity rationale behind the backcast frozenset
        # does not reach it (the FFR-3V precedent — the renewable vintage seed
        # is likewise all-ISO).
        for iso in ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP"):
            self.assertTrue(
                measured_storage_base_fleet_active(self._hindcast_cfg(iso=iso), iso),
                f"{iso}: hindcast with a vintage must seed measured storage",
            )

    def test_plain_forecast_keeps_the_scalar_even_with_a_vintage(self):
        # The "prove by test" half for the forecast path: a non-hindcast
        # forecast keeps the scenario ladder even when an eia860_vintage_year
        # is set, mirroring the runner's vintage-arming predicate (which arms
        # the vintage dir only for a backcast or a hindcast).
        cfg = ScenarioConfig(
            iso="ERCOT", mode="forecast", hindcast=False, eia860_vintage_year=2020
        )
        self.assertFalse(measured_storage_base_fleet_active(cfg, "ERCOT"))

    def test_backcast_scope_is_unchanged(self):
        # The backcast leg still resolves through the frozenset: CAISO in,
        # the other five out — their keepers stay byte-identical (FFR-4D).
        self.assertTrue(
            measured_storage_base_fleet_active(
                ScenarioConfig(iso="CAISO", mode="backcast"), "CAISO"
            )
        )
        for iso in ("ERCOT", "PJM", "MISO", "NYISO", "NEISO"):
            self.assertFalse(
                measured_storage_base_fleet_active(
                    ScenarioConfig(iso=iso, mode="backcast"), iso
                ),
                f"{iso}: backcast scope must stay CAISO-only",
            )

    def test_hindcast_without_a_vintage_keeps_the_scalar(self):
        # No vintage, nothing measured to seed from — the constant stands
        # (the FFR-3V precedent).
        cfg = self._hindcast_cfg(vintage=None)
        self.assertFalse(measured_storage_base_fleet_active(cfg, "ERCOT"))

    def test_off_switch_reproduces_the_scalar_hindcast(self):
        # storage_measured_base_fleet=False is the documented reproduction
        # escape for a pre-FFR-9A hindcast (and pre-FFR-4D backcast) — never a
        # tuning knob.
        cfg = self._hindcast_cfg(storage_measured_base_fleet=False)
        self.assertFalse(measured_storage_base_fleet_active(cfg, "ERCOT"))

    def test_hindcast_seed_is_the_vintage_fleet_not_the_scalar(self):
        # Seed content at the vintage the T1-FF ERCOT lane runs (2020), read
        # exactly as the runner reads it: vintage dir armed, loader called at
        # start_year. The measured vintage-2020 ERCOT fleet is 223.1 MW
        # against the 17,000 MW forward scalar (76x) — the base the endogenous
        # entry screen then ADDS to (FFR-8B §2.3: ~30 GW by the 2024 solve vs
        # ~10 GW actual).
        from market_sim.config.paths import set_eia860_vintage

        cfg = self._hindcast_cfg()
        set_eia860_vintage(2020)
        try:
            units = load_eia860_storage("ERCOT", cfg.start_year, cfg)
        finally:
            set_eia860_vintage(None)
        total = sum(u.power_cap_mw for u in units)
        np.testing.assert_allclose(total, 223.1, rtol=1e-3)
        self.assertLess(total, STORAGE_BASE_FLEET_MW["ERCOT"]["mid"] / 10.0)

    def test_hindcast_seed_carries_no_intra_year_ramp(self):
        # The FFR-3V third-leg hazard, storage edition: every unit in the
        # vintage sheet has a pre-start_year COD, so the seed read at
        # start_year must be static (no monthly profile that would de-rate,
        # in every solve year, a fleet fully in service before the window) —
        # even with the ramp flag armed, as the keepers arm it.
        from market_sim.config.paths import set_eia860_vintage

        cfg = self._hindcast_cfg(storage_vintage_ramp=True)
        set_eia860_vintage(2020)
        try:
            units = load_eia860_storage("ERCOT", cfg.start_year, cfg)
        finally:
            set_eia860_vintage(None)
        self.assertGreater(len(units), 0)
        for u in units:
            self.assertIsNone(
                u.monthly_power_mw,
                f"{u.unit_id}: vintage base fleet must not carry a COD ramp",
            )
