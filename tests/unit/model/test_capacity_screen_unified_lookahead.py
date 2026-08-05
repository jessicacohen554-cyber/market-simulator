"""FFR-5D ``capacity_screen_unified_lookahead``: screen unification + repairs.

Owner decision D-19(a) (sitting Addendum S.3/S.5, 2026-08-05). The gate does
two things as ONE mechanism:

* **UNIFICATION** — every capacity screen consumes the lookahead price object
  for its entering year, bridged/bridge-adjacent entering years included
  (runner seam; exercised end-to-end by the FFR-5D paired arms, not unit
  tests — the seam lives inside ``run_scenario_iso``'s year loop);
* **LEVEL REPAIRS** — the three FFR-5A §2a completeness gaps in
  ``_lookahead_reprice_signal``: (a) storage enters the pro-forma
  (``_storage_peak_shave_net_load``), (b) entering-fleet VRE capacity
  replaces prior-year realized output (``vre_capacity_potential``), (c)
  hourly availability replaces the annual time-mean derate
  (``hourly_availability``).

Default OFF, and the OFF path must be byte-identical — the first test class
is that regression: with every new argument at its default the function
reproduces the shipped hand-computed series exactly (same fixtures as
``test_price_signal.py``), and the repair arguments' defaults are proven
inert against an explicit-defaults call.

Trivial-first per CLAUDE.md: 2-3-unit stacks, 4-hour and 24-hour horizons,
hand-computed prices and shave levels.
"""

import unittest
from types import SimpleNamespace

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.runner import (
    _lookahead_reprice_signal,
    _storage_peak_shave_net_load,
    _storage_shave_terms,
)


def _three_unit_fixture(T=4):
    """The test_price_signal.py stack: mc [10, 20, 50], 5 GW each, avail 1."""
    fleet_arrays = SimpleNamespace(
        pmax=np.array([5000.0, 5000.0, 5000.0]),
        availability=np.ones((3, T)),
    )
    mc_cost = np.tile(np.array([[10.0], [20.0], [50.0]]), (1, T))
    result = SimpleNamespace(
        wind_dispatched=np.zeros((1, T)),
        solar_dispatched=np.zeros((1, T)),
    )
    base_demand = np.array([[2000.0, 7000.0, 12000.0, 20000.0]])
    return fleet_arrays, mc_cost, result, base_demand


class TestOffPathByteIdentical(unittest.TestCase):
    """The gate defaults OFF and the unarmed signal path is byte-identical."""

    def test_field_defaults_off(self):
        self.assertFalse(ScenarioConfig().capacity_screen_unified_lookahead)

    def test_shipped_hand_computed_series_unchanged(self):
        # The pre-FFR-5D hand-computed series (test_price_signal.py) through
        # the post-FFR-5D code with every new argument at its default.
        fleet_arrays, mc_cost, result, base_demand = _three_unit_fixture()
        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        signal = _lookahead_reprice_signal(
            config, 2024, base_demand, fleet_arrays, mc_cost, result, n_zones=2
        )
        np.testing.assert_allclose(signal[0], [10.0, 20.0, 50.0, 50.0])
        np.testing.assert_allclose(signal[1], signal[0])

    def test_explicit_defaults_are_byte_identical(self):
        # Passing the repair arguments at their documented defaults changes
        # NOTHING relative to omitting them (the whole unarmed path).
        fleet_arrays, mc_cost, result, base_demand = _three_unit_fixture()
        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        implicit = _lookahead_reprice_signal(
            config, 2024, base_demand, fleet_arrays, mc_cost, result, n_zones=1
        )
        explicit = _lookahead_reprice_signal(
            config,
            2024,
            base_demand,
            fleet_arrays,
            mc_cost,
            result,
            n_zones=1,
            vre_capacity_potential=None,
            storage_shave=None,
            hourly_availability=False,
        )
        self.assertTrue(np.array_equal(implicit, explicit))


class TestHourlyAvailabilityRepair(unittest.TestCase):
    """Repair (c): the stack is derated by each hour's own availability."""

    def test_outaged_hour_prices_up_the_stack(self):
        # 2 units, mc [10, 20], 100 MW each. The cheap unit is OUT in hour 1.
        T = 2
        fleet_arrays = SimpleNamespace(
            pmax=np.array([100.0, 100.0]),
            availability=np.array([[1.0, 0.0], [1.0, 1.0]]),
        )
        mc_cost = np.tile(np.array([[10.0], [20.0]]), (1, T))
        result = SimpleNamespace(
            wind_dispatched=np.zeros((1, T)),
            solar_dispatched=np.zeros((1, T)),
        )
        base_demand = np.array([[50.0, 50.0]])
        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        hourly = _lookahead_reprice_signal(
            config,
            2024,
            base_demand,
            fleet_arrays,
            mc_cost,
            result,
            n_zones=1,
            hourly_availability=True,
        )
        # Hour 0: cheap unit fully available -> $10. Hour 1: cheap unit's
        # hourly capacity is 0, the 50 MW clears on the $20 unit.
        np.testing.assert_allclose(hourly[0], [10.0, 20.0])
        # The time-mean path smears the outage across both hours (cap 50 MW
        # mean-derated): hour 0 already exhausts the cheap tranche at 50 MW
        # and hour 1 prices identically -- the smearing the repair removes.
        mean_path = _lookahead_reprice_signal(
            config, 2024, base_demand, fleet_arrays, mc_cost, result, n_zones=1
        )
        np.testing.assert_allclose(mean_path[0], [10.0, 10.0])

    def test_searchsorted_semantics_match_scalar_path(self):
        # With time-constant availability the hourly path must reproduce the
        # scalar path EXACTLY (same left-searchsorted tie semantics at a load
        # exactly equal to a cumulative-capacity breakpoint).
        fleet_arrays, mc_cost, result, base_demand = _three_unit_fixture()
        base_demand = np.array([[5000.0, 10000.0, 15000.0, 3000.0]])  # exact ties
        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        scalar = _lookahead_reprice_signal(
            config, 2024, base_demand, fleet_arrays, mc_cost, result, n_zones=1
        )
        hourly = _lookahead_reprice_signal(
            config,
            2024,
            base_demand,
            fleet_arrays,
            mc_cost,
            result,
            n_zones=1,
            hourly_availability=True,
        )
        self.assertTrue(np.array_equal(scalar, hourly))


class TestVreCapacityRepair(unittest.TestCase):
    """Repair (b): entering-fleet VRE potential replaces realized output."""

    def test_potential_overrides_realized_output(self):
        fleet_arrays, mc_cost, result, base_demand = _three_unit_fixture()
        # Prior-year REALIZED output was zero (heavy curtailment); the
        # entering fleet's potential is 5 GW flat. The repair must net the
        # potential, not the realized zero.
        potential = np.full(4, 5000.0)
        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        signal = _lookahead_reprice_signal(
            config,
            2024,
            base_demand,
            fleet_arrays,
            mc_cost,
            result,
            n_zones=1,
            vre_capacity_potential=potential,
        )
        # net load [-3000, 2000, 7000, 15000] -> [10, 10, 20, 50]
        np.testing.assert_allclose(signal[0], [10.0, 10.0, 20.0, 50.0])

    def test_pipeline_vre_still_adds_on_top(self):
        fleet_arrays, mc_cost, result, base_demand = _three_unit_fixture()
        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        signal = _lookahead_reprice_signal(
            config,
            2024,
            base_demand,
            fleet_arrays,
            mc_cost,
            result,
            n_zones=1,
            vre_capacity_potential=np.full(4, 2500.0),
            pipeline_vre=np.full(4, 2500.0),
        )
        # Same 5 GW total netting as above (FFR-5C composition).
        np.testing.assert_allclose(signal[0], [10.0, 10.0, 20.0, 50.0])


class TestStoragePeakShave(unittest.TestCase):
    """Repair (a): per-day energy-limited peak-shave / valley-fill."""

    def _day(self, peak_hour=12, base=100.0, peak=200.0):
        y = np.full(24, base)
        y[peak_hour] = peak
        return y

    def test_single_peak_shaved_and_energy_conserved_at_unit_rte(self):
        y = self._day()
        out = _storage_peak_shave_net_load(y, power_mw=50.0, energy_mwh=50.0, rte=1.0)
        # The peak hour is shaved by the full 50 MW power cap (energy budget
        # 50 MWh covers exactly one hour at full power).
        self.assertAlmostEqual(out[12], 150.0, places=6)
        # rte=1: charge == discharge, total energy unchanged.
        self.assertAlmostEqual(out.sum(), y.sum(), places=4)
        # Charge lands in non-peak hours only, never above the power cap.
        charge = out[np.arange(24) != 12] - 100.0
        self.assertTrue((charge >= -1e-9).all())
        self.assertTrue((charge <= 50.0 + 1e-9).all())
        self.assertAlmostEqual(charge.sum(), 50.0, places=4)

    def test_round_trip_losses_increase_total_load(self):
        y = self._day()
        out = _storage_peak_shave_net_load(y, power_mw=50.0, energy_mwh=50.0, rte=0.5)
        # 50 MWh discharged needs 100 MWh charged: net +50 MWh on the day.
        self.assertAlmostEqual(out.sum() - y.sum(), 50.0, places=3)
        self.assertAlmostEqual(out[12], 150.0, places=6)

    def test_power_cap_binds_before_energy(self):
        y = self._day(peak=400.0)
        out = _storage_peak_shave_net_load(y, power_mw=50.0, energy_mwh=500.0, rte=1.0)
        # One 300-MW-above-base peak hour, 50 MW power cap: shave is 50, not
        # the energy budget.
        self.assertAlmostEqual(out[12], 350.0, places=6)

    def test_energy_budget_binds_across_a_wide_peak(self):
        y = np.full(24, 100.0)
        y[10:14] = 200.0  # four peak hours
        out = _storage_peak_shave_net_load(y, power_mw=100.0, energy_mwh=100.0, rte=1.0)
        # Water-filling 100 MWh over a flat 4-hour peak: 25 MW off each hour.
        np.testing.assert_allclose(out[10:14], 175.0, atol=1e-3)

    def test_discharge_and_charge_hours_are_disjoint(self):
        rng = np.random.default_rng(7)
        y = rng.uniform(50.0, 250.0, size=48)  # two days
        out = _storage_peak_shave_net_load(y, power_mw=40.0, energy_mwh=120.0, rte=0.85)
        delta = out - y
        # No hour both charges and discharges: the fill level is bounded by
        # the shave level, so each hour moves in one direction only.
        self.assertTrue(((delta >= -40.0 - 1e-9) & (delta <= 40.0 + 1e-9)).all())
        # Per day: discharged energy = charged energy * rte (full replenish
        # possible here since headroom is ample).
        for d in range(2):
            dd = delta[d * 24 : (d + 1) * 24]
            dis = -dd[dd < 0].sum()
            chg = dd[dd > 0].sum()
            self.assertAlmostEqual(dis, chg * 0.85, places=2)

    def test_no_storage_is_a_no_op(self):
        y = self._day()
        out = _storage_peak_shave_net_load(y, power_mw=0.0, energy_mwh=0.0, rte=1.0)
        self.assertTrue(np.array_equal(out, y))

    def test_partial_trailing_day_passes_through(self):
        y = np.concatenate([self._day(), np.full(6, 500.0)])  # 30 hours
        out = _storage_peak_shave_net_load(y, power_mw=50.0, energy_mwh=50.0, rte=1.0)
        np.testing.assert_allclose(out[24:], y[24:])  # untouched tail
        self.assertAlmostEqual(out[12], 150.0, places=6)

    def test_signal_integration_kills_manufactured_scarcity_hour(self):
        # End-to-end through the signal: a peak hour that exhausts the stack
        # (priced at the top tranche) is shaved back into the $20 tranche.
        fleet_arrays, mc_cost, result, _ = _three_unit_fixture(T=24)
        base_demand = np.full((1, 24), 7000.0)
        base_demand[0, 12] = 16000.0  # exhausts the 15 GW stack
        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        unrepaired = _lookahead_reprice_signal(
            config, 2024, base_demand, fleet_arrays, mc_cost, result, n_zones=1
        )
        self.assertAlmostEqual(unrepaired[0, 12], 50.0)
        repaired = _lookahead_reprice_signal(
            config,
            2024,
            base_demand,
            fleet_arrays,
            mc_cost,
            result,
            n_zones=1,
            storage_shave=(8000.0, 8000.0, 0.9),
        )
        # 16000 - 8000 (power-capped shave, ample energy) = 8000 -> $20.
        self.assertAlmostEqual(repaired[0, 12], 20.0)


class TestStorageShaveTerms(unittest.TestCase):
    """Aggregation of StorageArrays into the (power, energy, rte) terms."""

    def test_flat_arrays_aggregate(self):
        storage = SimpleNamespace(
            power_cap=np.array([100.0, 300.0]),
            energy_cap=np.array([400.0, 600.0]),
            eta_chg=np.array([0.9, 1.0]),
            eta_dis=np.array([0.9, 1.0]),
        )
        p, e, rte = _storage_shave_terms(storage)
        self.assertEqual(p, 400.0)
        self.assertEqual(e, 1000.0)
        # Energy-weighted: (0.81*400 + 1.0*600) / 1000
        self.assertAlmostEqual(rte, 0.924, places=6)

    def test_vintage_ramp_profiles_take_final_hour(self):
        # 2-D cap profiles (storage_vintage_ramp): a unit ramping in mid-year
        # counts at its end-of-year (fully-online) capability.
        storage = SimpleNamespace(
            power_cap=np.array([[0.0, 50.0, 100.0]]),
            energy_cap=np.array([[0.0, 200.0, 400.0]]),
            eta_chg=np.array([1.0]),
            eta_dis=np.array([1.0]),
        )
        p, e, rte = _storage_shave_terms(storage)
        self.assertEqual((p, e), (100.0, 400.0))
        self.assertEqual(rte, 1.0)

    def test_empty_fleet_is_none(self):
        storage = SimpleNamespace(
            power_cap=np.zeros(0),
            energy_cap=np.zeros(0),
            eta_chg=np.zeros(0),
            eta_dis=np.zeros(0),
        )
        self.assertIsNone(_storage_shave_terms(storage))


if __name__ == "__main__":
    unittest.main()
