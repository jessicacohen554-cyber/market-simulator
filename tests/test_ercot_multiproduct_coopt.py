"""Tests for ERCOT's multi-product energy+AS co-optimization.

Builds from the trivial case up (CLAUDE.md testing pattern): a 1-generator,
1-zone, 24-hour LP with a single binding AS product, then additivity, the
quality cascade, and the scarcity-input builder. Every price in these tests is
recovered as an LP dual — the honesty gate of the whole build is that the
binding product's reserve price forms from the shared-headroom/reserve-balance
duals, never an exogenous adder tuned to a target.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.results.scarcity import (
    ercot_multiproduct_reserve_coopt_inputs,
    nyiso_rcpf_product_shortfall_steps,
)


def _fleet(fuels, zone_names, hours, pmax=100.0, pmin=0.0):
    """One generator per fuel in ``fuels``, all in zone ``zone_names[0]``."""
    gens = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone=zone_names[0],
            fuel_type=f,
            pmax_mw=pmax,
            pmin_mw=pmin,
            eford=0.0,  # no derate -> headroom is exactly pmax - dispatch
        )
        for i, f in enumerate(fuels)
    ]
    return generators_to_fleet_arrays(gens, zone_names, hours=hours)


def _one_product(req_mw, max_penalty, n_ramp=10):
    """A single-product co-opt parameter bundle for solve_dispatch."""
    pen, wid = nyiso_rcpf_product_shortfall_steps(req_mw, 0.0, max_penalty, n_ramp)
    return dict(
        reserve_requirement=np.full((1, 24), float(req_mw)),
        reserve_eligible=np.ones((1, 1), dtype=bool),
        ordc_penalties=pen,
        ordc_step_widths=wid,
        reserve_balance_zone_mask=np.ones((1, 1), dtype=bool),
        reserve_balance_ordc_counts=np.array([pen.size]),
        reserve_balance_class=np.array([0]),
        reserve_headroom_eligible=np.ones((1, 1), dtype=bool),
        reserve_headroom_products=np.ones((1, 1), dtype=bool),
    )


class TestTrivialBindingProduct(unittest.TestCase):
    """1 gen, 1 zone, 24 h, one AS product — the trivial case first."""

    def _solve(self, req_mw, demand_mw=60.0, mc=20.0, max_penalty=1000.0):
        fleet = _fleet(["gas_cc"], ["Z0"], hours=24)
        demand = np.full((1, 24), demand_mw)
        mc_arr = np.full((1, 24), mc)
        return solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((1, 24)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, 24)),
            solar_cap=np.zeros(1),
            mc=mc_arr,
            voll=5000.0,
            **_one_product(req_mw, max_penalty),
        )

    def test_slack_reserve_does_not_price(self):
        # Headroom = 100 - 60 = 40 MW > 30 MW requirement -> reserve met free.
        r = self._solve(req_mw=30.0)
        self.assertIsNotNone(r.reserve_price)
        self.assertLess(float(r.reserve_price.max()), 1e-6)
        # Energy price is just the marginal cost — no scarcity lift.
        np.testing.assert_allclose(r.prices[0], 20.0, atol=1e-6)

    def test_binding_reserve_prices_and_lifts_lmp(self):
        # Requirement 90 MW > 40 MW headroom -> 50 MW shortfall, reserve prices.
        r = self._solve(req_mw=90.0)
        rp = float(r.reserve_price[0])
        self.assertGreater(rp, 0.0)
        # Co-optimization identity: a marginal MWh of energy gives up a MW of
        # reserve worth the reserve price, so LMP = mc + reserve price exactly.
        np.testing.assert_allclose(r.prices[0], 20.0 + rp, atol=1e-5)

    def test_reserve_price_monotonic_in_requirement(self):
        # A tighter AS requirement clears reserve lower on the demand curve ->
        # a higher reserve price (the scarcity is endogenous to headroom).
        low = float(self._solve(req_mw=70.0).reserve_price[0])
        high = float(self._solve(req_mw=95.0).reserve_price[0])
        self.assertGreater(high, low)

    def test_price_is_a_dual_not_an_adder(self):
        # Honesty gate: with the offer cap (max penalty) raised, the *same*
        # physical shortfall prices higher — the price tracks the demand curve
        # the LP clears against, not a fixed exogenous number.
        cheap = float(self._solve(req_mw=90.0, max_penalty=1000.0).reserve_price[0])
        dear = float(self._solve(req_mw=90.0, max_penalty=4000.0).reserve_price[0])
        self.assertGreater(dear, cheap + 1.0)


class TestAdditivity(unittest.TestCase):
    """Additive products (shared headroom) create scarcity independent ones don't."""

    def _two_products(self, additive):
        fleet = _fleet(["gas_cc"], ["Z0"], hours=24)
        demand = np.full((1, 24), 60.0)  # headroom = 40 MW
        mc = np.full((1, 24), 20.0)
        pen, wid = nyiso_rcpf_product_shortfall_steps(30.0, 0.0, 1000.0, 10)
        # Two products, each requiring 30 MW. Together 60 MW > 40 MW headroom.
        kwargs = dict(
            reserve_requirement=np.full((2, 24), 30.0),
            reserve_eligible=np.ones((2, 1), dtype=bool),
            ordc_penalties=np.concatenate([pen, pen]),
            ordc_step_widths=np.concatenate([wid, wid]),
            reserve_balance_zone_mask=np.ones((2, 1), dtype=bool),
            reserve_balance_ordc_counts=np.array([pen.size, pen.size]),
            reserve_balance_class=np.array([0, 1]),
        )
        if additive:
            # Both products share ONE headroom row -> compete for the 40 MW.
            kwargs["reserve_headroom_eligible"] = np.ones((1, 1), dtype=bool)
            kwargs["reserve_headroom_products"] = np.ones((1, 2), dtype=bool)
        else:
            # Each product its own headroom row -> each independently reuses 40.
            kwargs["reserve_headroom_eligible"] = np.ones((2, 1), dtype=bool)
            kwargs["reserve_headroom_products"] = np.eye(2, dtype=bool)
        return solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((1, 24)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, 24)),
            solar_cap=np.zeros(1),
            mc=mc,
            voll=5000.0,
            **kwargs,
        )

    def test_independent_products_do_not_price(self):
        # 30 MW each <= 40 MW headroom when each gets its own pool -> no scarcity.
        r = self._two_products(additive=False)
        self.assertLess(float(r.reserve_price.max()), 1e-6)

    def test_additive_products_price(self):
        # 30 + 30 = 60 MW > 40 MW shared headroom -> scarcity forms.
        r = self._two_products(additive=True)
        self.assertGreater(float(r.reserve_price.max()), 0.0)


class TestQualityCascade(unittest.TestCase):
    """Higher-quality substitutes down: a slow product reaches the peaker pool."""

    def _solve(self, products_in_slow_only):
        # gas_cc (fast/spinning, 30 MW) + gas_ct (quick-start peaker, 400 MW).
        # Demand 180 MW. The fast pool (gas_cc, 30 MW) is smaller than the 45 MW
        # fast requirement, so the fast product is short no matter how the LP
        # redispatches; the slow product reaches the large peaker pool and is met.
        gens = [
            Generator(
                unit_id="CC",
                name="CC",
                zone="Z0",
                fuel_type="gas_cc",
                pmax_mw=30.0,
                pmin_mw=0.0,
                eford=0.0,
            ),
            Generator(
                unit_id="CT",
                name="CT",
                zone="Z0",
                fuel_type="gas_ct",
                pmax_mw=400.0,
                pmin_mw=0.0,
                eford=0.0,
            ),
        ]
        fleet = generators_to_fleet_arrays(gens, ["Z0"], hours=24)
        demand = np.full((1, 24), 180.0)
        mc = np.full((2, 24), 20.0)
        pen, wid = nyiso_rcpf_product_shortfall_steps(45.0, 0.0, 1000.0, 10)
        # Two products: index 0 "fast" (gas_cc only), index 1 "slow" (both).
        fast_elig = np.array([[True, False]])  # row 0: gas_cc only
        all_elig = np.array([[True, True]])  # row 1: both
        kwargs = dict(
            reserve_requirement=np.full((2, 24), 45.0),
            reserve_eligible=np.ones((2, 2), dtype=bool),
            ordc_penalties=np.concatenate([pen, pen]),
            ordc_step_widths=np.concatenate([wid, wid]),
            reserve_balance_zone_mask=np.ones((2, 1), dtype=bool),
            reserve_balance_ordc_counts=np.array([pen.size, pen.size]),
            reserve_balance_class=np.array([0, 1]),
            reserve_headroom_eligible=np.vstack([fast_elig, all_elig]),
            # Row 0 (fast pool) bounds product 0; row 1 (all pool) bounds both.
            reserve_headroom_products=np.array(
                [[True, False], [True, True]], dtype=bool
            ),
        )
        return solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((1, 24)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, 24)),
            solar_cap=np.zeros(1),
            mc=mc,
            voll=5000.0,
            **kwargs,
        )

    def test_fast_product_prices_higher_than_slow(self):
        # The fast pool (gas_cc, 30 MW) cannot cover the 45 MW fast requirement,
        # so the fast product is short and prices; the slow product reaches the
        # 400 MW peaker pool and is met free. Fast dual must exceed slow dual.
        r = self._solve(products_in_slow_only=False)
        by_fam = r.reserve_price_by_family  # (T, 2): col 0 fast, col 1 slow
        self.assertIsNotNone(by_fam)
        self.assertGreater(float(by_fam[0, 0]), float(by_fam[0, 1]))
        # The binding MCPC is the per-hour max across products.
        self.assertAlmostEqual(
            float(r.reserve_price_by_family.max(axis=1)[0]),
            float(by_fam[0, 0]),
            places=6,
        )


class TestMultiProductInputs(unittest.TestCase):
    """The scarcity input builder shapes and cascade membership."""

    def _fleet(self):
        gens = [
            Generator(
                unit_id=f"G{i}",
                name=f"G{i}",
                zone="Z0",
                fuel_type=f,
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
            )
            for i, f in enumerate(["gas_cc", "gas_ct", "coal", "nuclear", "oil"])
        ]
        return generators_to_fleet_arrays(gens, ["Z0"], hours=48)

    def test_builder_shapes_and_cascade(self):
        cfg = ScenarioConfig(iso="ERCOT", mode="backcast", weather_year=2024, hours=48)
        fleet = self._fleet()
        (
            req,
            elig,
            pen,
            wid,
            zmask,
            counts,
            rclass,
            hr_elig,
            hr_prod,
        ) = ercot_multiproduct_reserve_coopt_inputs(cfg, fleet, 48)
        n_prod = 4  # RegUp/RRS/ECRS/NonSpin
        self.assertEqual(req.shape, (n_prod, 48))
        self.assertEqual(elig.shape, (n_prod, fleet.n_gen))
        self.assertEqual(zmask.shape, (n_prod, 1))
        self.assertTrue(zmask.all())
        self.assertEqual(rclass.tolist(), [0, 1, 2, 3])
        self.assertEqual(int(counts.sum()), pen.size)
        self.assertEqual(pen.shape, wid.shape)
        # Two nested headroom rows: fast (excludes quick-start peakers) and all.
        self.assertEqual(hr_elig.shape, (2, fleet.n_gen))
        self.assertEqual(hr_prod.shape, (2, n_prod))
        # The "all" row (index 1) bounds every product; the "fast" row only the
        # three fast products (RegUp/RRS/ECRS), not Non-Spin.
        self.assertTrue(hr_prod[1].all())
        self.assertEqual(hr_prod[0].tolist(), [True, True, True, False])
        # Fast pool excludes the gas_ct/oil quick-start peakers; all pool keeps
        # them (offline quick-start can back Non-Spin).
        self.assertGreater(int(hr_elig[1].sum()), int(hr_elig[0].sum()))

    def test_requirements_match_measured_as_plan(self):
        # The per-product requirement is the measured ASPLANNP433 realization —
        # a validation target, not a fit. 2024 means are well-known (REGUP ~406,
        # RRS ~2722, ECRS ~1747, NSPIN ~2688 MW).
        cfg = ScenarioConfig(
            iso="ERCOT", mode="backcast", weather_year=2024, hours=8760
        )
        fleet = self._fleet()
        req = ercot_multiproduct_reserve_coopt_inputs(cfg, fleet, 8760)[0]
        means = req.mean(axis=1)
        self.assertGreater(means[0], 300.0)  # RegUp
        self.assertGreater(means[1], 2000.0)  # RRS
        self.assertGreater(means[2], 1000.0)  # ECRS (active 2024)
        self.assertGreater(means[3], 2000.0)  # NonSpin


class TestASAwareUnitValue(unittest.TestCase):
    """The AS-aware commitment value: reserve price x headroom, cascade-aware."""

    def _fleet(self):
        gens = [
            Generator(
                unit_id=f"G{i}",
                name=f"G{i}",
                zone="Z0",
                fuel_type=f,
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,  # no derate -> availability 1.0
            )
            # fast: gas_cc/coal/nuclear; quick-start: gas_ct/oil; none: wind
            for i, f in enumerate(
                ["gas_cc", "gas_ct", "coal", "nuclear", "oil", "wind"]
            )
        ]
        return generators_to_fleet_arrays(gens, ["Z0"], hours=4)

    def test_none_reserve_price_is_zero(self):
        from market_sim.results.scarcity import ercot_as_aware_unit_value

        fleet = self._fleet()
        av = ercot_as_aware_unit_value(fleet, np.zeros((fleet.n_gen, 4)), None, 4)
        self.assertEqual(av.shape, (fleet.n_gen, 4))
        self.assertFalse(av.any())

    def test_value_is_price_times_headroom_with_cascade(self):
        from market_sim.results.scarcity import ercot_as_aware_unit_value

        fleet = self._fleet()
        # Products RegUp/RRS/ECRS (fast) / NonSpin (slow). One hour priced.
        rp = np.zeros((4, 4))  # (T, n_prod)
        rp[1, 0] = 10.0  # a FAST product (RegUp) prices at $10 in hour 1
        rp[1, 3] = 4.0  # NonSpin (slow) prices at $4 in hour 1
        p1 = np.zeros((fleet.n_gen, 4))
        p1[0, 1] = 40.0  # gas_cc runs 40 MW in hour 1 -> headroom 60
        av = ercot_as_aware_unit_value(fleet, p1, rp, 4)
        # gas_cc (fast): proxy = max over all products = $10, headroom 60 -> 600.
        self.assertAlmostEqual(av[0, 1], 600.0)
        # coal/nuclear (fast, full 100 headroom): 10 x 100 = 1000.
        self.assertAlmostEqual(av[2, 1], 1000.0)
        self.assertAlmostEqual(av[3, 1], 1000.0)
        # gas_ct/oil (quick-start): only the NonSpin (slow) price applies -> 4x100.
        self.assertAlmostEqual(av[1, 1], 400.0)
        self.assertAlmostEqual(av[4, 1], 400.0)
        # wind holds no responsive reserve -> zero everywhere.
        self.assertFalse(av[5].any())
        # No AS value in the unpriced hours.
        self.assertFalse(av[:, [0, 2, 3]].any())


if __name__ == "__main__":
    unittest.main()
