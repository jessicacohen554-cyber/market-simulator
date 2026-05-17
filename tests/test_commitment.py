"""Tests for the 2-pass heuristic unit commitment filter."""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.commitment import (
    apply_commitment,
    compute_commitment,
    find_runs,
)
from market_sim.model.dispatch import solve_dispatch

# f-class commitment params (heat rate 6.5-7.5): min_run 8h, min_down 6h,
# startup 48.6 $/MW -- the regime exercised by the single-CC tests below.
_CONFIG = ScenarioConfig()


def _single_cc(heat_rate: float = 7.0, hours: int = 24):
    """Return a one-generator gas_cc fleet (list + FleetArrays)."""
    gen = Generator(
        unit_id="CC", name="CC", zone="z", fuel_type="gas_cc",
        pmax_mw=300.0, pmin_mw=0.0, heat_rate=heat_rate, eford=0.0,
    )
    arrays = generators_to_fleet_arrays([gen], ["z"], hours=hours)
    return [gen], arrays


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
        committed = compute_commitment(prices, mc, gens, arrays, _CONFIG)
        self.assertEqual(committed.shape, (1, 24))
        self.assertTrue(committed.all())

    def test_price_below_mc_commits_no_hours(self):
        gens, arrays = _single_cc(hours=24)
        mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        committed = compute_commitment(prices, mc, gens, arrays, _CONFIG)
        self.assertFalse(committed.any())

    def test_long_spike_commits_those_hours(self):
        # A 12-hour profitable spike clears both the min-run (8h) and the
        # startup-cost filters, so exactly those hours commit.
        gens, arrays = _single_cc(hours=24)
        mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 6:18] = 50.0
        committed = compute_commitment(prices, mc, gens, arrays, _CONFIG)
        self.assertTrue(committed[0, 6:18].all())
        self.assertFalse(committed[0, :6].any())
        self.assertFalse(committed[0, 18:].any())

    def test_short_spike_too_short_to_commit(self):
        # A 3-hour spike is below the 8-hour min-run threshold.
        gens, arrays = _single_cc(hours=24)
        mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 10:13] = 50.0
        committed = compute_commitment(prices, mc, gens, arrays, _CONFIG)
        self.assertFalse(committed.any())

    def test_spike_revenue_below_startup_cost_rejected(self):
        # A 10-hour run clears the min-run filter but its total margin
        # (4 $/MWh x 10h = 40) falls short of the 48.6 $/MW startup cost.
        gens, arrays = _single_cc(hours=24)
        mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:15] = 34.0
        committed = compute_commitment(prices, mc, gens, arrays, _CONFIG)
        self.assertFalse(committed.any())

    def test_runs_within_min_down_are_merged(self):
        # Two accepted 8-hour runs separated by a 3-hour gap (< 6h min-down)
        # merge into one committed block that bridges the gap.
        gens, arrays = _single_cc(hours=30)
        mc = np.full((1, 30), 30.0)
        prices = np.full((1, 30), 20.0)
        prices[0, 0:8] = 40.0
        prices[0, 11:19] = 40.0
        committed = compute_commitment(prices, mc, gens, arrays, _CONFIG)
        self.assertTrue(committed[0, :19].all())
        self.assertFalse(committed[0, 19:].any())

    def test_coal_always_committed(self):
        coal = Generator(
            unit_id="C", name="C", zone="z", fuel_type="coal",
            pmax_mw=500.0, pmin_mw=0.0, heat_rate=9.5, eford=0.0,
        )
        arrays = generators_to_fleet_arrays([coal], ["z"], hours=24)
        mc = np.full((1, 24), 25.0)
        prices = np.full((1, 24), 5.0)  # far below MC
        committed = compute_commitment(prices, mc, [coal], arrays, _CONFIG)
        self.assertTrue(committed.all())

    def test_ct_always_committed(self):
        ct = Generator(
            unit_id="CT", name="CT", zone="z", fuel_type="gas_ct",
            pmax_mw=200.0, pmin_mw=0.0, heat_rate=10.5, eford=0.0,
        )
        arrays = generators_to_fleet_arrays([ct], ["z"], hours=24)
        mc = np.full((1, 24), 80.0)
        prices = np.full((1, 24), 10.0)  # far below MC
        committed = compute_commitment(prices, mc, [ct], arrays, _CONFIG)
        self.assertTrue(committed.all())


class TestApplyCommitment(unittest.TestCase):
    """Tests for zeroing availability in decommitted hours."""

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

        out = apply_commitment(arrays, committed)

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

        committed = compute_commitment(
            pass1.prices, mc, gens, arrays, ScenarioConfig()
        )
        pass2 = solve_dispatch(
            apply_commitment(arrays, committed), demand, **kwargs
        )

        cc_p1, cc_p2 = pass1.dispatch[1].sum(), pass2.dispatch[1].sum()
        ct_p1, ct_p2 = pass1.dispatch[2].sum(), pass2.dispatch[2].sum()

        self.assertGreater(cc_p1, 0.0)
        self.assertLess(cc_p2, cc_p1)
        self.assertGreater(ct_p2, ct_p1)


if __name__ == "__main__":
    unittest.main()
