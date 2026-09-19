"""Tests for ``DispatchResult.marginal_emission_rate`` -- the emissions dual.

The marginal emission rate is ``r_B' B^-1``: the same product that gives the
zonal price, with the per-generator CO2 rate vector in place of the cost
vector. These tests pin it against the only ground truth there is -- brute-force
perturbation of the energy-balance right-hand side and a re-solve -- on cases
small enough to reason about by hand (rule: trivial cases first, one zone, a
handful of hours, then scale up).

They also pin the three properties a consumer has to carry: it is NOT the
emission rate of the unit whose ``mc`` equals the price, it is one-sided at a
degenerate vertex (and HiGHS reports the DOWN side, which is the direction an
abatement question wants), and the surrounding solve is unchanged by its
computation.
"""

import unittest

import numpy as np

from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch


def _fleet(n_gen, zones_of_gens, zone_names, hours, pmax, rates):
    """Return ``FleetArrays`` with explicit per-generator CO2 rates."""
    fleet = generators_to_fleet_arrays(
        [
            Generator(
                unit_id=f"G{i}",
                name=f"G{i}",
                zone=z,
                fuel_type="gas_cc",
                pmax_mw=pmax[i],
                pmin_mw=0.0,
                eford=0.0,
            )
            for i, z in enumerate(zones_of_gens)
        ],
        zone_names,
        hours=hours,
    )
    # Set the rates directly: the emissions dual reads ``fleet.emission_rate``
    # and nothing else, so the test states the rates rather than reproducing
    # the heat-rate x fuel-factor derivation that normally produces them.
    fleet.emission_rate = np.asarray(rates, dtype=float)
    return fleet


class TestMarginalEmissionRate(unittest.TestCase):
    """The emissions dual against brute-force perturbation."""

    T = 4

    def _kw(self, n_zones):
        return dict(
            wind_cf=np.zeros((n_zones, self.T)),
            wind_cap=np.zeros(n_zones),
            solar_cf=np.zeros((n_zones, self.T)),
            solar_cap=np.zeros(n_zones),
        )

    def _solve(self, demand, mc, pmax, rates, n_zones=1, zones=None):
        zones = zones or ["Z0"] * len(pmax)
        zone_names = [f"Z{i}" for i in range(n_zones)]
        fleet = _fleet(len(pmax), zones, zone_names, self.T, pmax, rates)
        return solve_dispatch(fleet, demand, mc=mc, T=self.T, **self._kw(n_zones))

    def _co2(self, result, rates):
        return float((np.asarray(result.dispatch) * np.asarray(rates)[:, None]).sum())

    def test_marginal_unit_rate_on_a_clean_merit_order(self):
        # Cheap+dirty coal-like unit full at 50; the clean CC is at the margin.
        # One more MWh comes from the CC, so MER is the CC's rate -- NOT the
        # fleet-average rate, which the dirty inframarginal unit dominates.
        pmax, rates = [50.0, 50.0], [1.00, 0.40]
        mc = np.vstack([np.full(self.T, 10.0), np.full(self.T, 30.0)])
        demand = np.full((1, self.T), 70.0)
        r = self._solve(demand, mc, pmax, rates)
        np.testing.assert_allclose(r.prices, 30.0)
        self.assertIsNotNone(r.marginal_emission_rate)
        self.assertEqual(r.marginal_emission_rate.shape, (1, self.T))
        np.testing.assert_allclose(r.marginal_emission_rate, 0.40, atol=1e-9)
        # The fleet-average rate is a different, larger number -- the whole
        # point of using the margin.
        fleet_avg = self._co2(r, rates) / float(np.asarray(r.dispatch).sum())
        self.assertGreater(fleet_avg, 0.65)

    def test_matches_brute_force_perturbation(self):
        # Ground truth: add 1 MWh of demand, re-solve, difference the CO2.
        pmax, rates = [50.0, 50.0, 50.0], [1.00, 0.40, 0.55]
        mc = np.vstack(
            [np.full(self.T, 10.0), np.full(self.T, 30.0), np.full(self.T, 80.0)]
        )
        for level, expected in ((70.0, 0.40), (120.0, 0.55)):
            with self.subTest(demand=level):
                base = self._solve(np.full((1, self.T), level), mc, pmax, rates)
                bumped = self._solve(np.full((1, self.T), level + 1.0), mc, pmax, rates)
                truth = self._co2(bumped, rates) - self._co2(base, rates)
                # Perturbing every hour at once gives T MWh of extra CO2.
                np.testing.assert_allclose(truth / self.T, expected, atol=1e-6)
                np.testing.assert_allclose(
                    base.marginal_emission_rate, expected, atol=1e-9
                )

    def test_zero_when_the_margin_is_carbon_free(self):
        # Wind covers the load; the marginal MWh displaces wind, not fossil.
        pmax, rates = [50.0], [0.80]
        mc = np.full((1, self.T), 30.0)
        fleet = _fleet(1, ["Z0"], ["Z0"], self.T, pmax, rates)
        r = solve_dispatch(
            fleet,
            np.full((1, self.T), 20.0),
            mc=mc,
            T=self.T,
            wind_cf=np.ones((1, self.T)),
            wind_cap=np.array([100.0]),
            solar_cf=np.zeros((1, self.T)),
            solar_cap=np.zeros(1),
        )
        np.testing.assert_allclose(r.marginal_emission_rate, 0.0, atol=1e-9)

    def test_congestion_gives_a_per_zone_rate(self):
        # Two zones, no link between them: each zone's margin is its own unit,
        # so the rates differ by zone -- the reason this is a per-zone array.
        pmax, rates = [100.0, 100.0], [1.00, 0.40]
        mc = np.vstack([np.full(self.T, 10.0), np.full(self.T, 30.0)])
        demand = np.vstack([np.full(self.T, 50.0), np.full(self.T, 50.0)])
        fleet = _fleet(2, ["Z0", "Z1"], ["Z0", "Z1"], self.T, pmax, rates)
        r = solve_dispatch(fleet, demand, mc=mc, T=self.T, **self._kw(2))
        self.assertEqual(r.marginal_emission_rate.shape, (2, self.T))
        np.testing.assert_allclose(r.marginal_emission_rate[0], 1.00, atol=1e-9)
        np.testing.assert_allclose(r.marginal_emission_rate[1], 0.40, atol=1e-9)

    def test_tied_offers_are_basis_arbitrary_per_hour_but_exact_in_total(self):
        # Two units offer at the SAME mc and emit 4.5x apart. "The unit whose
        # mc equals the price" cannot answer here -- both satisfy it -- and the
        # LP is degenerate, so WHICH tied column moves is basis-arbitrary and
        # differs hour to hour. The dual inherits exactly that: per hour it
        # returns one of the tied rates, and over the year it is exact. This is
        # the documented degeneracy caveat, pinned rather than papered over.
        pmax, rates = [50.0, 50.0, 50.0], [1.00, 0.20, 0.90]
        mc = np.vstack(
            [np.full(self.T, 10.0), np.full(self.T, 30.0), np.full(self.T, 30.0)]
        )
        base = self._solve(np.full((1, self.T), 70.0), mc, pmax, rates)
        bumped = self._solve(np.full((1, self.T), 71.0), mc, pmax, rates)
        truth_total = self._co2(bumped, rates) - self._co2(base, rates)

        mer = np.asarray(base.marginal_emission_rate).ravel()
        np.testing.assert_allclose(base.prices, 30.0)
        # Every hour lands on one of the two tied rates ...
        for value in mer:
            self.assertTrue(
                np.isclose(value, 0.20) or np.isclose(value, 0.90),
                f"{value} is neither tied rate",
            )
        # ... and the TOTAL is exact, which is the grain any abatement or
        # MAC number is actually read at.
        np.testing.assert_allclose(mer.sum(), truth_total, atol=1e-6)

    def test_is_the_down_derivative_at_a_degenerate_vertex(self):
        # Demand sits EXACTLY on the cheap dirty unit's capacity, so the vertex
        # is degenerate and the derivative is genuinely two different numbers:
        #   down (-1 MWh): back the dirty unit off      -> 1.00 tCO2/MWh
        #   up   (+1 MWh): start the clean CC           -> 0.40 tCO2/MWh
        # HiGHS reports the DOWN side, which is the side an abatement question
        # wants -- a new wind or solar MWh REMOVES net load. A consumer reading
        # this as "the cost of serving one more MWh" would be wrong here.
        pmax, rates = [50.0, 50.0], [1.00, 0.40]
        mc = np.vstack([np.full(self.T, 10.0), np.full(self.T, 30.0)])
        base = self._solve(np.full((1, self.T), 50.0), mc, pmax, rates)
        co2 = self._co2(base, rates)
        down = (
            co2
            - self._co2(self._solve(np.full((1, self.T), 49.0), mc, pmax, rates), rates)
        ) / self.T
        up = (
            self._co2(self._solve(np.full((1, self.T), 51.0), mc, pmax, rates), rates)
            - co2
        ) / self.T
        np.testing.assert_allclose(down, 1.00, atol=1e-6)
        np.testing.assert_allclose(up, 0.40, atol=1e-6)
        self.assertNotAlmostEqual(down, up)
        np.testing.assert_allclose(base.marginal_emission_rate, down, atol=1e-9)

    def test_unserved_load_leaves_the_rate_at_zero(self):
        # Price is VOLL and the marginal MWh is served by the slack column,
        # which emits nothing: no fossil response to attribute.
        pmax, rates = [50.0], [0.80]
        mc = np.full((1, self.T), 30.0)
        r = self._solve(np.full((1, self.T), 200.0), mc, pmax, rates)
        self.assertTrue(np.all(np.asarray(r.slack) > 0.0))
        np.testing.assert_allclose(r.marginal_emission_rate, 0.0, atol=1e-9)

    def test_solve_outputs_are_unchanged_by_the_repricing(self):
        # The emissions dual re-prices the objective at a frozen basis. The
        # objective value, status, prices and dispatch reported by the same
        # solve must be the cost solve's, not the CO2 re-pricing's.
        pmax, rates = [50.0, 50.0], [1.00, 0.40]
        mc = np.vstack([np.full(self.T, 10.0), np.full(self.T, 30.0)])
        demand = np.full((1, self.T), 70.0)
        r = self._solve(demand, mc, pmax, rates)
        expected_cost = self.T * (50.0 * 10.0 + 20.0 * 30.0)
        self.assertAlmostEqual(r.objective_value, expected_cost, places=6)
        self.assertEqual(r.status, "Optimal")
        np.testing.assert_allclose(r.prices, 30.0)
        np.testing.assert_allclose(r.dispatch[0], 50.0)
        np.testing.assert_allclose(r.dispatch[1], 20.0)


if __name__ == "__main__":
    unittest.main()


class TestSystemSidecarColumn(unittest.TestCase):
    """The emissions dual reaches the committable ``hourly/system_<year>``."""

    T = 5

    def _frame(self, mer):
        import types

        import scripts.run_calibration_full as rcf

        n_zones = 2
        result = types.SimpleNamespace(
            prices=np.tile(np.arange(self.T, dtype=float), (n_zones, 1)),
            slack=np.zeros((n_zones, self.T)),
            dump=np.zeros((n_zones, self.T)),
            reserve_price=np.zeros(self.T),
            marginal_emission_rate=mer,
        )
        return rcf._system_frame(
            2024,
            "P1",
            result,
            demand=np.full((n_zones, self.T), 100.0),
            zone_names=["Z0", "Z1"],
        )

    def test_column_is_written_per_zone(self):
        mer = np.vstack([np.full(self.T, 0.40), np.full(self.T, 0.95)])
        df = self._frame(mer)
        self.assertIn("marginal_emission_rate", df.columns)
        z0 = df[df.zone == "Z0"]["marginal_emission_rate"].to_numpy()
        z1 = df[df.zone == "Z1"]["marginal_emission_rate"].to_numpy()
        np.testing.assert_allclose(z0, 0.40)
        np.testing.assert_allclose(z1, 0.95)

    def test_column_is_omitted_when_absent(self):
        # A result loaded from a cache written before the dual was wired
        # carries None; the sidecar simply has no such column.
        self.assertNotIn("marginal_emission_rate", self._frame(None).columns)

    def test_column_is_omitted_on_a_shape_mismatch(self):
        self.assertNotIn(
            "marginal_emission_rate",
            self._frame(np.zeros((3, self.T))).columns,
        )


class TestWeightedMarginalRate(unittest.TestCase):
    """The shape-weighting helper behind the reported MAC denominators."""

    def setUp(self):
        from market_sim.results.emissions import weighted_marginal_rate

        self.f = weighted_marginal_rate

    def test_weights_by_the_resources_own_shape(self):
        # Rate is 0.9 at night and 0.2 midday. Solar generates only midday, so
        # it displaces the LOW rate; a flat load weighting would overstate it.
        rate = np.array([[0.9, 0.9, 0.2, 0.2]])
        solar = np.array([[0.0, 0.0, 1.0, 1.0]])
        load = np.array([[1.0, 1.0, 1.0, 1.0]])
        self.assertAlmostEqual(self.f(rate, solar), 0.2)
        self.assertAlmostEqual(self.f(rate, load), 0.55)

    def test_none_not_zero_when_nothing_generated(self):
        # A resource that never ran has no rate to report. Zero would read as
        # "displaces nothing", which would make its MAC infinite.
        rate = np.array([[0.9, 0.2]])
        self.assertIsNone(self.f(rate, np.zeros((1, 2))))

    def test_none_on_absent_or_mismatched_inputs(self):
        rate = np.array([[0.9, 0.2]])
        self.assertIsNone(self.f(None, np.ones((1, 2))))
        self.assertIsNone(self.f(rate, None))
        self.assertIsNone(self.f(rate, np.ones((2, 2))))
