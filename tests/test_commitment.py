"""Tests for the startup-cost bid markup and CC/CT commitment screen."""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.commitment import (
    apply_commitment_with_coal_pin,
    compute_commitment,
    compute_monthly_markup,
    find_runs,
    reserve_adequacy_commit,
)
from market_sim.model.dispatch import solve_dispatch

_CONFIG = ScenarioConfig()

# f-class commitment params (heat rate 6.5-7.5): min_run 8h, min_down 6h,
# startup 48.6 $/MW. IRR hurdle 7% -> 48.6 x 1.07 = 52.0 $/MW.


def _single_cc(heat_rate: float = 7.0, hours: int = 24):
    """Return a one-generator gas_cc fleet (list + FleetArrays)."""
    gen = Generator(
        unit_id="CC",
        name="CC",
        zone="z",
        fuel_type="gas_cc",
        pmax_mw=300.0,
        pmin_mw=0.0,
        heat_rate=heat_rate,
        eford=0.0,
    )
    return [gen], generators_to_fleet_arrays([gen], ["z"], hours=hours)


def _single_ct(heat_rate: float = 10.5, hours: int = 24):
    """Return a one-generator gas_ct fleet (list + FleetArrays)."""
    gen = Generator(
        unit_id="CT",
        name="CT",
        zone="z",
        fuel_type="gas_ct",
        pmax_mw=200.0,
        pmin_mw=0.0,
        heat_rate=heat_rate,
        eford=0.0,
    )
    return [gen], generators_to_fleet_arrays([gen], ["z"], hours=hours)


def _single_coal(heat_rate: float = 10.0, hours: int = 24):
    """Return a one-generator coal fleet (list + FleetArrays)."""
    gen = Generator(
        unit_id="COAL",
        name="COAL",
        zone="z",
        fuel_type="coal",
        pmax_mw=500.0,
        pmin_mw=0.0,
        heat_rate=heat_rate,
        eford=0.0,
    )
    return [gen], generators_to_fleet_arrays([gen], ["z"], hours=hours)


class TestReserveAdequacyCommit(unittest.TestCase):
    """Path B: the downstate spinning-reserve adequacy commit."""

    def _two_ct(self, hours=4):
        gens = [
            Generator(
                unit_id=f"CT{i}",
                name=f"CT{i}",
                zone="NYC",
                fuel_type="gas_ct",
                pmax_mw=200.0,
                pmin_mw=20.0,
                heat_rate=10.5,
                eford=0.0,
            )
            for i in range(2)
        ]
        return gens, generators_to_fleet_arrays(gens, ["NYC"], hours=hours)

    def test_commits_until_requirement_covered(self):
        gens, fa = self._two_ct()
        committed = np.zeros((2, 4), dtype=bool)  # both decommitted
        spin = np.array([True, True])
        # Requirement 150 MW < one CT's 200 MW pmax -> exactly one CT committed.
        out = reserve_adequacy_commit(committed, fa, gens, spin, 150.0)
        per_hour_committed = out.sum(axis=0)
        np.testing.assert_array_equal(per_hour_committed, [1, 1, 1, 1])
        # Committed headroom (200) covers the 150 requirement every hour.
        headroom = (fa.pmax[:, None] * fa.availability * out).sum(axis=0)
        self.assertTrue((headroom >= 150.0).all())

    def test_commits_both_when_one_insufficient(self):
        gens, fa = self._two_ct()
        committed = np.zeros((2, 4), dtype=bool)
        out = reserve_adequacy_commit(
            committed, fa, gens, np.array([True, True]), 350.0
        )
        np.testing.assert_array_equal(out.sum(axis=0), [2, 2, 2, 2])

    def test_noop_when_requirement_zero_or_no_eligible(self):
        gens, fa = self._two_ct()
        committed = np.zeros((2, 4), dtype=bool)
        np.testing.assert_array_equal(
            reserve_adequacy_commit(committed, fa, gens, np.array([True, True]), 0.0),
            committed,
        )
        np.testing.assert_array_equal(
            reserve_adequacy_commit(
                committed, fa, gens, np.array([False, False]), 150.0
            ),
            committed,
        )

    def test_preserves_already_committed(self):
        gens, fa = self._two_ct()
        committed = np.ones((2, 4), dtype=bool)  # both already on
        out = reserve_adequacy_commit(
            committed, fa, gens, np.array([True, True]), 150.0
        )
        np.testing.assert_array_equal(out, committed)  # nothing to add


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
    """The commitment screen on gas CC units: margin = price - base MC."""

    def test_flat_price_above_mc_commits_all_hours(self):
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 50.0)
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertEqual(committed.shape, (1, 24))
        self.assertTrue(committed.all())

    def test_price_below_mc_commits_no_hours(self):
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertFalse(committed.any())

    def test_long_spike_commits_those_hours(self):
        # A 12-hour profitable spike clears both the min-run (8h) and the
        # startup-cost filters, so exactly those hours commit.
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 6:18] = 50.0
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertTrue(committed[0, 6:18].all())
        self.assertFalse(committed[0, :6].any())
        self.assertFalse(committed[0, 18:].any())

    def test_short_spike_too_short_to_commit(self):
        # A 3-hour spike is below the 8-hour min-run threshold.
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 10:13] = 50.0
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertFalse(committed.any())

    def test_spike_revenue_below_startup_cost_rejected(self):
        # A 10-hour run clears the min-run filter but its total margin
        # (4 $/MWh x 10h = 40) falls short of the 52.0 $/MW IRR hurdle.
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:15] = 34.0
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertFalse(committed.any())

    def test_runs_within_min_down_are_merged(self):
        # Two accepted 8-hour runs separated by a 3-hour gap (< 6h min-down)
        # merge into one committed block that bridges the gap.
        gens, arrays = _single_cc(hours=30)
        base_mc = np.full((1, 30), 30.0)
        prices = np.full((1, 30), 20.0)
        prices[0, 0:8] = 40.0
        prices[0, 11:19] = 40.0
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertTrue(committed[0, :19].all())
        self.assertFalse(committed[0, 19:].any())

    def test_irr_hurdle_rejects_run_below_startup_cost_plus_irr(self):
        # f-class CC: startup 48.6 $/MW, IRR 7% -> hurdle 52.0 $/MW.
        # A 10-hour run at 5 $/MWh margin totals 50 -- above breakeven
        # (48.6) but below the IRR hurdle, so it is rejected.
        gens, arrays = _single_cc(heat_rate=7.0, hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:15] = 35.0  # margin 5 x 10h = 50 total
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertFalse(committed.any())

        # Lift the margin to 6 $/MWh (total 60 > 52) and the run commits.
        prices[0, 5:15] = 36.0
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertTrue(committed[0, 5:15].all())

    def test_ct_commits_for_a_single_profitable_hour(self):
        # CTs have min_run 1h: one high-margin hour justifies a start.
        gens, arrays = _single_ct(heat_rate=10.5, hours=24)
        base_mc = np.full((1, 24), 80.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 12] = 180.0  # margin 100 for one hour
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertTrue(committed[0, 12])
        self.assertEqual(int(committed.sum()), 1)

    def test_margin_uses_base_mc_not_bid_mc(self):
        # The same prices screened against base MC commit the run, but
        # screened against a higher bid MC (base + markup) they do not:
        # the margin must use the generator's actual cost.
        gens, arrays = _single_cc(heat_rate=7.0, hours=24)
        prices = np.full((1, 24), 50.0)
        base_mc = np.full((1, 24), 45.0)  # margin 5 x 24h = 120 > 52
        bid_mc = np.full((1, 24), 50.0)  # margin 0 -> nothing commits

        committed_base = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        committed_bid = compute_commitment(prices, bid_mc, gens, arrays, _CONFIG)
        self.assertTrue(committed_base.all())
        self.assertFalse(committed_bid.any())


class TestASAwareCommitment(unittest.TestCase):
    """AS revenue keeps energy-marginal units committed (AS-aware commitment)."""

    def test_none_as_value_is_byte_identical(self):
        # Passing as_value=None reproduces the energy-only screen exactly.
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:15] = 35.0  # 10-h run, margin 5x10=50 < 52 hurdle -> reject
        baseline = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        explicit_none = compute_commitment(
            prices, base_mc, gens, arrays, _CONFIG, as_value=None
        )
        self.assertFalse(baseline.any())
        np.testing.assert_array_equal(baseline, explicit_none)

    def test_as_value_lifts_run_over_hurdle(self):
        # Energy margin alone (5x10=50) is below the 52.0 IRR hurdle, so the run
        # is rejected. Adding AS revenue to those hours clears the hurdle.
        gens, arrays = _single_cc(heat_rate=7.0, hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:15] = 35.0  # margin 5 x 10h = 50
        rejected = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertFalse(rejected.any())

        as_value = np.zeros((1, 24))
        as_value[0, 5:15] = 1.0  # +10 AS -> 60 > 52 hurdle
        committed = compute_commitment(
            prices, base_mc, gens, arrays, _CONFIG, as_value=as_value
        )
        self.assertTrue(committed[0, 5:15].all())

    def test_as_value_extends_online_unit_into_as_hours(self):
        # A unit online for energy (one in-merit run) has its commitment EXTENDED
        # into the adjacent AS-priced hours it earns reserve.
        gens, arrays = _single_ct(heat_rate=10.5, hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 8:10] = 200.0  # a short, very profitable energy run (CT min_run 1)
        energy_only = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertTrue(energy_only[0, 8:10].all())
        self.assertFalse(energy_only[0, 10:14].any())

        as_value = np.zeros((1, 24))
        as_value[0, 8:14] = 100.0  # AS priced through hour 13
        committed = compute_commitment(
            prices, base_mc, gens, arrays, _CONFIG, as_value=as_value
        )
        # The online unit now stays committed through its AS-earning hours.
        self.assertTrue(committed[0, 8:14].all())

    def test_as_value_does_not_resurrect_a_cold_unit(self):
        # A unit the LP never runs for energy (no in-merit hour) is NOT brought
        # online by its idle headroom's AS credit — it is the phantom headroom the
        # screen must drop out of the reserve pool.
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)  # energy margin always negative -> cold
        as_value = np.zeros((1, 24))
        as_value[0, 8:20] = 5000.0  # huge idle AS credit
        committed = compute_commitment(
            prices, base_mc, gens, arrays, _CONFIG, as_value=as_value
        )
        self.assertFalse(committed.any())


class TestStorageWeightedCommitment(unittest.TestCase):
    """The commitment hurdle discounts margin in storage net-charging hours."""

    def _scenario(self):
        # f-class CC, hurdle 52.0. A 10-hour run at 6 $/MWh margin totals 60,
        # which clears the hurdle when unweighted (see the IRR-hurdle test).
        gens, arrays = _single_cc(heat_rate=7.0, hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:15] = 36.0
        demand = np.full((1, 24), 1000.0)
        return gens, arrays, base_mc, prices, demand

    def test_net_charging_discounts_hurdle_and_rejects_run(self):
        # Storage charges 200 MW into a 1000 MW zone during the run, so the
        # weight is 0.8: weighted margin 60 x 0.8 = 48 < 52 -> rejected.
        gens, arrays, base_mc, prices, demand = self._scenario()
        charge = np.zeros((1, 24))
        charge[0, 5:15] = 200.0
        committed = compute_commitment(
            prices,
            base_mc,
            gens,
            arrays,
            _CONFIG,
            storage_charge=charge,
            storage_discharge=np.zeros((1, 24)),
            storage_zone_idx=np.array([0]),
            demand=demand,
        )
        self.assertFalse(committed.any())

    def test_net_discharging_keeps_full_weight_and_commits(self):
        # Storage discharging keeps weight 1.0 (storage and thermal are
        # complements at the peak): the 60-total run still clears 52.
        gens, arrays, base_mc, prices, demand = self._scenario()
        discharge = np.zeros((1, 24))
        discharge[0, 5:15] = 200.0
        committed = compute_commitment(
            prices,
            base_mc,
            gens,
            arrays,
            _CONFIG,
            storage_charge=np.zeros((1, 24)),
            storage_discharge=discharge,
            storage_zone_idx=np.array([0]),
            demand=demand,
        )
        self.assertTrue(committed[0, 5:15].all())

    def test_zero_weight_disables_storage_discount(self):
        # commitment_storage_weight = 0 recovers the plain margin sum even
        # with heavy net charging: the run commits.
        gens, arrays, base_mc, prices, demand = self._scenario()
        charge = np.zeros((1, 24))
        charge[0, 5:15] = 200.0
        config = ScenarioConfig(commitment_storage_weight=0.0)
        committed = compute_commitment(
            prices,
            base_mc,
            gens,
            arrays,
            config,
            storage_charge=charge,
            storage_discharge=np.zeros((1, 24)),
            storage_zone_idx=np.array([0]),
            demand=demand,
        )
        self.assertTrue(committed[0, 5:15].all())

    def test_omitted_storage_inputs_are_a_noop(self):
        # Without the storage arguments the screen is unchanged: the run
        # clears the hurdle exactly as in the non-storage IRR-hurdle test.
        gens, arrays, base_mc, prices, _ = self._scenario()
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertTrue(committed[0, 5:15].all())

    def _trough_scenario(self):
        # A 12-hour positive-margin run (hours 5-16) with a 4-hour storage
        # net-charging trough in its middle (hours 9-12). Net charge there
        # is 60% of zone demand, so the storage weight is 0.4.
        gens, arrays = _single_cc(heat_rate=7.0, hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:17] = 50.0
        demand = np.full((1, 24), 1000.0)
        charge = np.zeros((1, 24))
        charge[0, 9:13] = 600.0
        kwargs = dict(
            storage_charge=charge,
            storage_discharge=np.zeros((1, 24)),
            storage_zone_idx=np.array([0]),
            demand=demand,
        )
        return gens, arrays, base_mc, prices, kwargs

    def test_in_merit_floor_breaks_a_run_through_a_charging_trough(self):
        # Floor off: the 12-hour run commits whole. Floor on: the trough
        # drops out and the two 4-hour pieces each fall short of the
        # 8-hour min run, so nothing commits.
        gens, arrays, base_mc, prices, kwargs = self._trough_scenario()
        off = compute_commitment(prices, base_mc, gens, arrays, _CONFIG, **kwargs)
        self.assertTrue(off[0, 5:17].all())

        cfg = ScenarioConfig(commitment_storage_in_merit_floor=0.5)
        on = compute_commitment(prices, base_mc, gens, arrays, cfg, **kwargs)
        self.assertFalse(on.any())

    def test_in_merit_floor_leaves_shallow_charging_untouched(self):
        # A shallow trough (net charge 20% of demand -> weight 0.8) stays
        # above the 0.5 floor, so the run is not broken and still commits.
        gens, arrays, base_mc, prices, kwargs = self._trough_scenario()
        kwargs["storage_charge"] = kwargs["storage_charge"].copy()
        kwargs["storage_charge"][0, 9:13] = 200.0
        cfg = ScenarioConfig(commitment_storage_in_merit_floor=0.5)
        committed = compute_commitment(prices, base_mc, gens, arrays, cfg, **kwargs)
        self.assertTrue(committed[0, 5:17].all())


class TestCoalAndNuclearAlwaysCommitted(unittest.TestCase):
    """Coal, nuclear and non-thermal fuels are never commitment-screened."""

    def test_coal_and_nuclear_stay_committed_at_deep_loss(self):
        gens = [
            Generator(
                unit_id="CC",
                name="CC",
                zone="z",
                fuel_type="gas_cc",
                pmax_mw=300.0,
                heat_rate=7.0,
                eford=0.0,
            ),
            Generator(
                unit_id="COAL",
                name="COAL",
                zone="z",
                fuel_type="coal",
                pmax_mw=500.0,
                heat_rate=10.0,
                eford=0.0,
            ),
            Generator(
                unit_id="NUC",
                name="NUC",
                zone="z",
                fuel_type="nuclear",
                pmax_mw=1000.0,
                heat_rate=10.0,
                eford=0.0,
            ),
        ]
        arrays = generators_to_fleet_arrays(gens, ["z"], hours=24)
        # Price far below every thermal MC.
        base_mc = np.array(
            [
                np.full(24, 60.0),
                np.full(24, 55.0),
                np.full(24, 10.0),
            ]
        )
        prices = np.full((1, 24), 5.0)
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)

        self.assertFalse(committed[0].any())  # CC screened off
        self.assertTrue(committed[1].all())  # coal always committed
        self.assertTrue(committed[2].all())  # nuclear always committed


class TestComputeMonthlyMarkup(unittest.TestCase):
    """The monthly startup-amortization markup from P0 run lengths."""

    def test_coal_and_nuclear_get_zero_markup(self):
        gens, arrays = _single_coal(hours=744)
        dispatch = np.full((1, 744), 300.0)
        markup = compute_monthly_markup(gens, arrays, dispatch, 744)
        self.assertEqual(markup.shape, (1, 744))
        self.assertTrue((markup == 0.0).all())

    def test_markup_equals_startup_over_run_length(self):
        # f-class CC, startup 48.6 $/MW. A January of uninterrupted running
        # amortizes the startup over the whole 744-hour run.
        gens, arrays = _single_cc(heat_rate=7.0, hours=744)
        dispatch = np.full((1, 744), 200.0)  # always on (> 5% of 300 MW)
        markup = compute_monthly_markup(gens, arrays, dispatch, 744)
        np.testing.assert_allclose(markup[0], 48.6 / 744.0)

    def test_shoulder_month_markup_exceeds_summer(self):
        # Two-month horizon (Jan 744h + Feb 672h). Month 1 runs continuously
        # (long run, low markup); month 2 runs in 4-hour bursts (short runs,
        # high markup).
        hours = 744 + 672
        gens, arrays = _single_cc(heat_rate=7.0, hours=hours)
        dispatch = np.zeros((1, hours))
        dispatch[0, :744] = 200.0  # month 1: continuous
        for start in range(744, hours, 8):
            dispatch[0, start : start + 4] = 200.0  # month 2: 4h on / 4h off
        markup = compute_monthly_markup(gens, arrays, dispatch, hours)

        summer = markup[0, 0]
        shoulder = markup[0, 744]
        self.assertLess(summer, shoulder)
        np.testing.assert_allclose(shoulder, 48.6 / 4.0)

    def test_idle_month_amortizes_over_unit_run(self):
        # A month with no running hours has no run to amortize over; the
        # markup falls back to startup / 1.0 rather than dividing by zero.
        gens, arrays = _single_cc(heat_rate=7.0, hours=744)
        dispatch = np.zeros((1, 744))
        markup = compute_monthly_markup(gens, arrays, dispatch, 744)
        np.testing.assert_allclose(markup[0], 48.6)


class TestApplyCommitmentWithCoalPin(unittest.TestCase):
    """Tests for applying the commitment screen to the fleet arrays."""

    def test_cc_availability_zeroed_only_where_decommitted(self):
        gens = [
            Generator(
                unit_id="CC",
                name="CC",
                zone="z",
                fuel_type="gas_cc",
                pmax_mw=300.0,
                heat_rate=7.0,
                eford=0.05,
            ),
            Generator(
                unit_id="CT",
                name="CT",
                zone="z",
                fuel_type="gas_ct",
                pmax_mw=200.0,
                heat_rate=10.5,
                eford=0.05,
            ),
        ]
        arrays = generators_to_fleet_arrays(gens, ["z"], hours=10)
        committed = np.ones((2, 10), dtype=bool)
        committed[0, 3:6] = False
        p1_dispatch = np.zeros((2, 10))

        out = apply_commitment_with_coal_pin(arrays, committed, p1_dispatch, gens)
        self.assertTrue((out.availability[0, 3:6] == 0.0).all())
        np.testing.assert_array_equal(
            out.availability[0, :3], arrays.availability[0, :3]
        )
        np.testing.assert_array_equal(out.availability[1], arrays.availability[1])
        # The input arrays must not be mutated in place.
        self.assertTrue((arrays.availability[0, 3:6] != 0.0).all())

    def test_coal_availability_pinned_to_pass1_dispatch(self):
        coal = Generator(
            unit_id="COAL",
            name="COAL",
            zone="z",
            fuel_type="coal",
            pmax_mw=400.0,
            pmin_mw=0.0,
            heat_rate=10.0,
            eford=0.0,
        )
        arrays = generators_to_fleet_arrays([coal], ["z"], hours=4)
        committed = np.ones((1, 4), dtype=bool)
        p1_dispatch = np.array([[400.0, 200.0, 0.0, 100.0]])

        out = apply_commitment_with_coal_pin(arrays, committed, p1_dispatch, [coal])
        # availability = clip(P1 / Pmax), with a tiny floor for the zero hour.
        np.testing.assert_allclose(out.availability[0], [1.0, 0.5, 1e-6, 0.25])

    def test_nuclear_pmin_preserved(self):
        # Nuclear is not screened; its must-run Pmin survives into P2.
        nuc = Generator(
            unit_id="NUC",
            name="NUC",
            zone="z",
            fuel_type="nuclear",
            pmax_mw=1000.0,
            pmin_mw=900.0,
            heat_rate=10.0,
            eford=0.0,
        )
        arrays = generators_to_fleet_arrays([nuc], ["z"], hours=4)
        out = apply_commitment_with_coal_pin(
            arrays, np.ones((1, 4), dtype=bool), np.zeros((1, 4)), [nuc]
        )
        self.assertEqual(out.pmin[0], 900.0)


class TestCoalPinnedInPass2(unittest.TestCase):
    """Coal dispatch is identical between P1 and the P2 re-solve."""

    def test_coal_dispatch_pinned_to_pass1_levels(self):
        hours = 12
        gens = [
            Generator(
                unit_id="COAL",
                name="COAL",
                zone="z",
                fuel_type="coal",
                pmax_mw=300.0,
                pmin_mw=0.0,
                heat_rate=10.0,
                eford=0.0,
            ),
            Generator(
                unit_id="CC",
                name="CC",
                zone="z",
                fuel_type="gas_cc",
                pmax_mw=1000.0,
                pmin_mw=0.0,
                heat_rate=7.0,
                eford=0.0,
            ),
        ]
        arrays = generators_to_fleet_arrays(gens, ["z"], hours=hours)
        # Coal cheap (20) < CC (50). Demand swings above and below coal Pmax.
        mc = np.array([np.full(hours, 20.0), np.full(hours, 50.0)])
        demand = np.full((1, hours), 250.0)
        demand[0, 3:6] = 500.0  # spikes pull in CC
        demand[0, 8] = 150.0  # dip below coal Pmax

        kwargs = dict(
            wind_cf=np.zeros((1, hours)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, hours)),
            solar_cap=np.zeros(1),
            mc=mc,
            T=hours,
        )
        pass1 = solve_dispatch(arrays, demand, **kwargs)

        committed = np.ones((2, hours), dtype=bool)
        fleet_p2 = apply_commitment_with_coal_pin(
            arrays, committed, pass1.dispatch, gens
        )
        pass2 = solve_dispatch(fleet_p2, demand, **kwargs)

        coal_p1 = pass1.dispatch[0].sum()
        coal_p2 = pass2.dispatch[0].sum()
        self.assertGreater(coal_p1, 0.0)
        self.assertAlmostEqual(coal_p2, coal_p1, delta=0.01 * coal_p1)


if __name__ == "__main__":
    unittest.main()
