"""Tests for the all-thermal heuristic unit commitment filter."""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    apply_coal_sunk_cost,
    generators_to_fleet_arrays,
)
from market_sim.model.commitment import (
    apply_commitment,
    compute_commitment,
    compute_ordc,
    find_runs,
)
from market_sim.model.dispatch import solve_dispatch

# Unit tests pin commitment_ordc_sigma tiny so the ORDC adder collapses to
# ~0 (reserves greatly exceed sigma), leaving margin = price - MC. The
# ORDC adder itself is exercised separately in TestComputeOrdc.
_CONFIG = ScenarioConfig(commitment_ordc_sigma=1.0)

# f-class commitment params (heat rate 6.5-7.5): min_run 8h, min_down 6h,
# startup 48.6 $/MW -- the regime exercised by the single-CC tests below.


def _single_cc(heat_rate: float = 7.0, hours: int = 24):
    """Return a one-generator gas_cc fleet (list + FleetArrays)."""
    gen = Generator(
        unit_id="CC", name="CC", zone="z", fuel_type="gas_cc",
        pmax_mw=300.0, pmin_mw=0.0, heat_rate=heat_rate, eford=0.0,
    )
    arrays = generators_to_fleet_arrays([gen], ["z"], hours=hours)
    return [gen], arrays


def _single_ct(heat_rate: float = 10.5, hours: int = 24):
    """Return a one-generator gas_ct fleet (list + FleetArrays)."""
    gen = Generator(
        unit_id="CT", name="CT", zone="z", fuel_type="gas_ct",
        pmax_mw=200.0, pmin_mw=0.0, heat_rate=heat_rate, eford=0.0,
    )
    arrays = generators_to_fleet_arrays([gen], ["z"], hours=hours)
    return [gen], arrays


def _single_coal(heat_rate: float = 10.0, hours: int = 24):
    """Return a one-generator coal fleet (list + FleetArrays)."""
    gen = Generator(
        unit_id="COAL", name="COAL", zone="z", fuel_type="coal",
        pmax_mw=500.0, pmin_mw=0.0, heat_rate=heat_rate, eford=0.0,
    )
    arrays = generators_to_fleet_arrays([gen], ["z"], hours=hours)
    return [gen], arrays


def _commit(prices, mc, gens, arrays, config=_CONFIG):
    """Run compute_commitment with zero demand/renewables (ORDC ~ 0)."""
    n_zones, T = prices.shape
    zeros = np.zeros((n_zones, T))
    return compute_commitment(
        prices, mc, gens, arrays, config,
        demand=zeros, wind_dispatched=zeros, solar_dispatched=zeros,
    )


class TestFindRuns(unittest.TestCase):
    """Tests for the consecutive-True segment finder."""

    def test_empty_and_all_false(self):
        self.assertEqual(find_runs(np.array([], dtype=bool)), [])
        self.assertEqual(find_runs(np.zeros(5, dtype=bool)), [])

    def test_segments_have_exclusive_end(self):
        mask = np.array([0, 1, 1, 1, 0, 0, 1, 1], dtype=bool)
        self.assertEqual(find_runs(mask), [(1, 4), (6, 8)])

    def test_full_run(self):
        self.assertEqual(find_runs(np.ones(4, dtype=bool)), [(0, 4)])


class TestComputeCommitment(unittest.TestCase):
    """Tests for the price-based commitment screen on gas CC units."""

    def test_flat_price_above_mc_commits_all_hours(self):
        gens, arrays = _single_cc(hours=24)
        mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 50.0)
        committed = _commit(prices, mc, gens, arrays)
        self.assertEqual(committed.shape, (1, 24))
        self.assertTrue(committed.all())

    def test_price_below_mc_commits_no_hours(self):
        gens, arrays = _single_cc(hours=24)
        mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        committed = _commit(prices, mc, gens, arrays)
        self.assertFalse(committed.any())

    def test_long_spike_commits_those_hours(self):
        # A 12-hour profitable spike clears both the min-run (8h) and the
        # startup-cost filters, so exactly those hours commit.
        gens, arrays = _single_cc(hours=24)
        mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 6:18] = 50.0
        committed = _commit(prices, mc, gens, arrays)
        self.assertTrue(committed[0, 6:18].all())
        self.assertFalse(committed[0, :6].any())
        self.assertFalse(committed[0, 18:].any())

    def test_short_spike_too_short_to_commit(self):
        # A 3-hour spike is below the 8-hour min-run threshold.
        gens, arrays = _single_cc(hours=24)
        mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 10:13] = 50.0
        committed = _commit(prices, mc, gens, arrays)
        self.assertFalse(committed.any())

    def test_spike_revenue_below_startup_cost_rejected(self):
        # A 10-hour run clears the min-run filter but its total margin
        # (4 $/MWh x 10h = 40) falls short of the 48.6 $/MW startup cost.
        gens, arrays = _single_cc(hours=24)
        mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:15] = 34.0
        committed = _commit(prices, mc, gens, arrays)
        self.assertFalse(committed.any())

    def test_runs_within_min_down_are_merged(self):
        # Two accepted 8-hour runs separated by a 3-hour gap (< 6h min-down)
        # merge into one committed block that bridges the gap.
        gens, arrays = _single_cc(hours=30)
        mc = np.full((1, 30), 30.0)
        prices = np.full((1, 30), 20.0)
        prices[0, 0:8] = 40.0
        prices[0, 11:19] = 40.0
        committed = _commit(prices, mc, gens, arrays)
        self.assertTrue(committed[0, :19].all())
        self.assertFalse(committed[0, 19:].any())


class TestAllThermalScreening(unittest.TestCase):
    """CC and CT are screened; coal and non-thermal stay committed."""

    def test_cc_ct_screened_coal_and_nuclear_always_committed(self):
        gens = [
            Generator(unit_id="CC", name="CC", zone="z", fuel_type="gas_cc",
                      pmax_mw=300.0, heat_rate=7.0, eford=0.0),
            Generator(unit_id="CT", name="CT", zone="z", fuel_type="gas_ct",
                      pmax_mw=200.0, heat_rate=10.5, eford=0.0),
            Generator(unit_id="COAL", name="COAL", zone="z", fuel_type="coal",
                      pmax_mw=500.0, heat_rate=10.0, eford=0.0),
            Generator(unit_id="NUC", name="NUC", zone="z", fuel_type="nuclear",
                      pmax_mw=1000.0, heat_rate=10.0, eford=0.0),
        ]
        arrays = generators_to_fleet_arrays(gens, ["z"], hours=24)
        # Price far below every thermal MC -> CC and CT decommit. Coal
        # (commitment disabled by default) and nuclear stay committed.
        mc = np.array([
            np.full(24, 60.0),
            np.full(24, 90.0),
            np.full(24, 55.0),
            np.full(24, 10.0),
        ])
        prices = np.full((1, 24), 5.0)
        committed = _commit(prices, mc, gens, arrays)

        self.assertFalse(committed[0].any())  # CC screened off
        self.assertFalse(committed[1].any())  # CT screened off
        self.assertTrue(committed[2].all())   # coal always committed
        self.assertTrue(committed[3].all())   # nuclear always committed

    def test_irr_hurdle_rejects_run_below_startup_cost_plus_irr(self):
        # f-class CC: startup 48.6 $/MW, IRR 7% -> hurdle 52.0 $/MW.
        # A 10-hour run at 5 $/MWh margin totals 50 -- above breakeven
        # (48.6) but below the IRR hurdle, so it is rejected.
        gens, arrays = _single_cc(heat_rate=7.0, hours=24)
        mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:15] = 35.0  # margin 5 x 10h = 50 total
        committed = _commit(prices, mc, gens, arrays)
        self.assertFalse(committed.any())

        # Lift the margin to 6 $/MWh (total 60 > 52) and the run commits.
        prices[0, 5:15] = 36.0
        committed = _commit(prices, mc, gens, arrays)
        self.assertTrue(committed[0, 5:15].all())

    def test_coal_rolling_average_tolerates_overnight_dips(self):
        # 24-hour coal run with two negative-margin hours. Under a strict
        # positive-margin screen the run splits into two 11-hour segments,
        # both below the 12h min-run. The rolling average bridges the dip,
        # so the whole run is accepted.
        gens, arrays = _single_coal(heat_rate=10.0, hours=24)
        mc = np.full((1, 24), 25.0)
        prices = np.full((1, 24), 35.0)  # margin +10
        prices[0, 11:13] = 20.0          # two hours at margin -5

        # coal_commitment_enabled exercises the coal screen (off by default).
        config = ScenarioConfig(
            commitment_ordc_sigma=1.0, coal_eval_window_hours=6,
            coal_commitment_enabled=True,
        )
        committed = _commit(prices, mc, gens, arrays, config=config)
        self.assertTrue(committed.all())

        # A 1-hour window collapses the rolling average to a strict
        # positive-margin screen: the dip splits the run into two 11-hour
        # segments, both below the 12h coal min-run, so coal decommits.
        strict = ScenarioConfig(
            commitment_ordc_sigma=1.0, coal_eval_window_hours=1,
            coal_commitment_enabled=True,
        )
        committed_strict = _commit(prices, mc, gens, arrays, config=strict)
        self.assertFalse(committed_strict.any())

    def test_ct_commits_for_a_single_profitable_hour(self):
        # CTs have min_run 1h: one high-margin hour justifies a start.
        gens, arrays = _single_ct(heat_rate=10.5, hours=24)
        mc = np.full((1, 24), 80.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 12] = 180.0  # margin 100 for one hour
        committed = _commit(prices, mc, gens, arrays)
        self.assertTrue(committed[0, 12])
        self.assertEqual(int(committed.sum()), 1)


class TestApplyCommitment(unittest.TestCase):
    """Tests for applying commitment to the fleet arrays."""

    def test_availability_zeroed_only_where_decommitted(self):
        gens = [
            Generator(
                unit_id="CC", name="CC", zone="z", fuel_type="gas_cc",
                pmax_mw=300.0, heat_rate=7.0, eford=0.05,
            ),
            Generator(
                unit_id="CT", name="CT", zone="z", fuel_type="gas_ct",
                pmax_mw=200.0, heat_rate=10.5, eford=0.05,
            ),
        ]
        arrays = generators_to_fleet_arrays(gens, ["z"], hours=10)
        committed = np.ones((2, 10), dtype=bool)
        committed[0, 3:6] = False

        out = apply_commitment(arrays, committed, gens)

        self.assertTrue((out.availability[0, 3:6] == 0.0).all())
        np.testing.assert_array_equal(
            out.availability[0, :3], arrays.availability[0, :3]
        )
        np.testing.assert_array_equal(
            out.availability[0, 6:], arrays.availability[0, 6:]
        )
        np.testing.assert_array_equal(
            out.availability[1], arrays.availability[1]
        )
        # The input arrays must not be mutated in place.
        self.assertTrue((arrays.availability[0, 3:6] != 0.0).all())

    def test_coal_availability_pinned_to_pass1_dispatch(self):
        # When p1_dispatch is given, coal availability is pinned to the
        # Pass-1 dispatch fraction and coal Pmin is zeroed.
        coal = Generator(unit_id="COAL", name="COAL", zone="z",
                         fuel_type="coal", pmax_mw=400.0, pmin_mw=160.0,
                         heat_rate=10.0, eford=0.0)
        arrays = generators_to_fleet_arrays([coal], ["z"], hours=4)
        committed = np.ones((1, 4), dtype=bool)
        p1_dispatch = np.array([[400.0, 200.0, 0.0, 100.0]])

        out = apply_commitment(arrays, committed, [coal],
                               p1_dispatch=p1_dispatch)

        # availability = clip(P1 / Pmax), with a tiny floor for the zero hour.
        np.testing.assert_allclose(
            out.availability[0], [1.0, 0.5, 1e-6, 0.25]
        )
        self.assertEqual(out.pmin[0], 0.0)
        # The input arrays must not be mutated in place.
        self.assertEqual(arrays.pmin[0], 160.0)


class TestComputeOrdc(unittest.TestCase):
    """Tests for the reserve-based ORDC scarcity adder."""

    def test_ordc_near_zero_high_reserve_spikes_low_reserve(self):
        gen = Generator(
            unit_id="G", name="G", zone="z", fuel_type="gas_cc",
            pmax_mw=10_000.0, heat_rate=7.0, eford=0.0,
        )
        arrays = generators_to_fleet_arrays([gen], ["z"], hours=2)
        # Hour 0: demand 1000 -> reserves 9000 (>> sigma) -> ORDC ~ 0.
        # Hour 1: demand 11000 -> reserves -1000 -> ORDC spikes.
        demand = np.array([[1000.0, 11_000.0]])
        zeros = np.zeros((1, 2))
        ordc = compute_ordc(
            arrays, demand, zeros, zeros, voll=5000.0, sigma_mw=1000.0
        )
        self.assertEqual(ordc.shape, (1, 2))
        self.assertLess(ordc[0, 0], 1.0)
        self.assertGreater(ordc[0, 1], 1000.0)
        self.assertLessEqual(ordc[0, 1], 5000.0)  # capped at VOLL


class TestCoalStructural(unittest.TestCase):
    """Tests for coal Pmin, sunk fuel cost, and never-decommit behavior."""

    def test_coal_always_committed_when_screening_disabled(self):
        # coal_commitment_enabled defaults to False: coal is never screened,
        # even when its margin is deeply negative.
        gens, arrays = _single_coal(heat_rate=10.0, hours=24)
        mc = np.full((1, 24), 50.0)
        prices = np.full((1, 24), 5.0)  # far below coal MC
        committed = _commit(prices, mc, gens, arrays)
        self.assertTrue(committed.all())

    def test_coal_pmin_overridden_to_18_percent(self):
        # The loader assigns coal Pmin = 40% of Pmax. With a config, the
        # array builder overrides it to coal_pmin_fraction (18%).
        coal = Generator(unit_id="COAL", name="COAL", zone="z",
                         fuel_type="coal", pmax_mw=500.0, pmin_mw=200.0,
                         heat_rate=10.0, eford=0.0)
        plain = generators_to_fleet_arrays([coal], ["z"], hours=4)
        self.assertEqual(plain.pmin[0], 200.0)  # loader value kept

        cfg = ScenarioConfig(coal_pmin_fraction=0.18)
        arrays = generators_to_fleet_arrays([coal], ["z"], hours=4, config=cfg)
        self.assertAlmostEqual(arrays.pmin[0], 90.0)  # 0.18 x 500

    def test_coal_sunk_cost_discounts_only_fuel_not_carbon(self):
        config = ScenarioConfig(coal_fuel_sunk_fraction=0.40)
        gens = [
            Generator(unit_id="COAL", name="COAL", zone="z", fuel_type="coal",
                      pmax_mw=500.0, vom=4.5, heat_rate=10.0, eford=0.0),
            Generator(unit_id="CC", name="CC", zone="z", fuel_type="gas_cc",
                      pmax_mw=300.0, vom=2.0, heat_rate=7.0, eford=0.0),
        ]
        arrays = generators_to_fleet_arrays(gens, ["z"], hours=4)
        fuel_prices = np.array([np.full(4, 2.0), np.full(4, 3.0)])
        # Coal MC = fuel (10 x 2.0 = 20) + VOM (4.5) + carbon (30) = 54.5.
        mc = np.array([np.full(4, 54.5), np.full(4, 25.0)])

        out = apply_coal_sunk_cost(mc, arrays, gens, fuel_prices, config)

        # Only the 20 $/MWh fuel cost is discounted: 54.5 - 0.40 x 20 = 46.5.
        # The 30 $/MWh carbon component is preserved (a naive MC-VOM
        # discount would wrongly yield 34.5).
        np.testing.assert_allclose(out[0], 46.5)
        np.testing.assert_allclose(out[1], 25.0)   # CC unchanged
        np.testing.assert_allclose(mc[0], 54.5)    # input not mutated

    def test_sunk_cost_does_not_change_emission_rate(self):
        # The sunk fraction reduces the bid price only. Emission accounting
        # uses the physical emission rate, untouched by apply_coal_sunk_cost.
        config = ScenarioConfig(coal_fuel_sunk_fraction=0.40)
        coal = Generator(unit_id="COAL", name="COAL", zone="z",
                         fuel_type="coal", pmax_mw=500.0, vom=4.5,
                         heat_rate=10.0, emission_rate_co2=1.0, eford=0.0)
        arrays = generators_to_fleet_arrays([coal], ["z"], hours=4)
        before = arrays.emission_rate.copy()
        mc = np.full((1, 4), 30.0)
        fuel_prices = np.full((1, 4), 2.0)

        apply_coal_sunk_cost(mc, arrays, [coal], fuel_prices, config)

        np.testing.assert_array_equal(arrays.emission_rate, before)
        self.assertEqual(arrays.emission_rate[0], 1.0)

    def test_coal_dispatch_pinned_to_pass1_levels(self):
        hours = 12
        gens = [
            Generator(unit_id="COAL", name="COAL", zone="z", fuel_type="coal",
                      pmax_mw=300.0, pmin_mw=0.0, heat_rate=10.0, eford=0.0),
            Generator(unit_id="CC", name="CC", zone="z", fuel_type="gas_cc",
                      pmax_mw=1000.0, pmin_mw=0.0, heat_rate=7.0, eford=0.0),
        ]
        arrays = generators_to_fleet_arrays(gens, ["z"], hours=hours)
        # coal cheap (20) < CC (50). Demand swings above and below coal Pmax.
        mc = np.array([np.full(hours, 20.0), np.full(hours, 50.0)])
        demand = np.full((1, hours), 250.0)
        demand[0, 3:6] = 500.0  # spikes pull in CC
        demand[0, 8] = 150.0    # dip below coal Pmax

        kwargs = dict(
            wind_cf=np.zeros((1, hours)), wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, hours)), solar_cap=np.zeros(1),
            mc=mc, T=hours,
        )
        pass1 = solve_dispatch(arrays, demand, **kwargs)

        committed = np.ones((2, hours), dtype=bool)
        fleet_p2 = apply_commitment(
            arrays, committed, gens, p1_dispatch=pass1.dispatch
        )
        pass2 = solve_dispatch(fleet_p2, demand, **kwargs)

        coal_p1 = pass1.dispatch[0].sum()
        coal_p2 = pass2.dispatch[0].sum()
        self.assertGreater(coal_p1, 0.0)
        self.assertAlmostEqual(coal_p2, coal_p1, delta=0.01 * coal_p1)


class TestTwoPassDispatch(unittest.TestCase):
    """Integration test: commitment shifts energy from CC to CT."""

    def test_commitment_shifts_cc_energy_to_ct(self):
        hours = 24
        gens = [
            Generator(
                unit_id="COAL", name="COAL", zone="z", fuel_type="coal",
                pmax_mw=300.0, pmin_mw=0.0, heat_rate=9.5, eford=0.0,
            ),
            Generator(
                unit_id="CC", name="CC", zone="z", fuel_type="gas_cc",
                pmax_mw=300.0, pmin_mw=0.0, heat_rate=7.0, eford=0.0,
            ),
            Generator(
                unit_id="CT", name="CT", zone="z", fuel_type="gas_ct",
                pmax_mw=500.0, pmin_mw=0.0, heat_rate=10.5, eford=0.0,
            ),
        ]
        arrays = generators_to_fleet_arrays(gens, ["z"], hours=hours)

        # Merit order: coal 20 < CC 30 < CT 80 $/MWh.
        mc = np.column_stack([
            np.full(hours, 20.0),
            np.full(hours, 30.0),
            np.full(hours, 80.0),
        ]).T

        # Low base demand (coal-only) with four scattered 2-hour spikes
        # that pull in CC and CT. The 2-hour CC runs are far below the
        # 8-hour min-run, so the commitment screen decommits CC entirely.
        demand = np.full((1, hours), 250.0)
        for start in (4, 10, 16, 20):
            demand[0, start:start + 2] = 700.0

        kwargs = dict(
            wind_cf=np.zeros((1, hours)), wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, hours)), solar_cap=np.zeros(1),
            mc=mc, T=hours,
        )
        pass1 = solve_dispatch(arrays, demand, **kwargs)

        # ORDC sigma 200 MW: during the 700 MW spikes (400 MW reserve) the
        # adder makes the marginal CT's run profitable enough to commit,
        # while off-spike (850 MW reserve) it stays negligible.
        config = ScenarioConfig(commitment_ordc_sigma=200.0)
        committed = compute_commitment(
            pass1.prices, mc, gens, arrays, config,
            demand=demand,
            wind_dispatched=pass1.wind_dispatched,
            solar_dispatched=pass1.solar_dispatched,
        )
        fleet_p2 = apply_commitment(
            arrays, committed, gens, p1_dispatch=pass1.dispatch
        )
        pass2 = solve_dispatch(fleet_p2, demand, **kwargs)

        cc_p1, cc_p2 = pass1.dispatch[1].sum(), pass2.dispatch[1].sum()
        ct_p1, ct_p2 = pass1.dispatch[2].sum(), pass2.dispatch[2].sum()

        self.assertGreater(cc_p1, 0.0)
        self.assertLess(cc_p2, cc_p1)
        self.assertGreater(ct_p2, ct_p1)


if __name__ == "__main__":
    unittest.main()
