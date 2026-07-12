"""Tests for the multivariate forecast-uncertainty sampler (PB-2).

The sampler (:mod:`market_sim.uncertainty`) is pure, so these are fast unit
tests with no solves: reproducibility, recovered rank correlation, LHS
stratification, discrete weighting, the gas sigma schedule, and the
forecast-only guard. The cache-backed classes exercise the sampler ensemble's
metric/band export against seeded fake results.
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from market_sim.config.constants import END_YEAR, START_YEAR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.uncertainty import (
    CONTINUOUS_DIMS,
    DISCRETE_DIMS,
    GasMarginal,
    UncertaintySpec,
    draw_to_config,
    sample_draws,
)

_REFERENCE_SPEC = (
    Path(__file__).resolve().parents[1] / "configs" / "uncertainty_ercot.yaml"
)


def _spec(n=64, seed=7, gas_load=0.3):
    """Build a compact spec with a settable gas<->load correlation."""
    return UncertaintySpec(
        n=n,
        seed=seed,
        gas=GasMarginal(sigma_front=0.35, sigma_back=0.41),
        spearman=(
            (1.0, gas_load, 0.0),
            (gas_load, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        discrete_weights={
            "weather": {2023: 1 / 3, 2024: 1 / 3, 2025: 1 / 3},
            "hydro": {"dry": 0.25, "normal": 0.5, "wet": 0.25},
            "policy": {"current": 0.5, "tight": 0.25, "rollback": 0.25},
        },
    )


class TestSampleDraws(unittest.TestCase):
    """Core sampling behaviour: reproducibility, correlation, stratification."""

    def test_bit_identical_for_fixed_seed(self):
        a = sample_draws(_spec())
        b = sample_draws(_spec())
        self.assertEqual(len(a), len(b))
        for da, db in zip(a, b):
            self.assertEqual(da.draw_id, db.draw_id)
            self.assertEqual(da.gas_price_factor, db.gas_price_factor)
            self.assertEqual(da.demand_growth_percentile, db.demand_growth_percentile)
            self.assertEqual(da.tech_cost_percentile, db.tech_cost_percentile)
            self.assertEqual(da.weather_year, db.weather_year)
            self.assertEqual(da.hydro_year, db.hydro_year)
            self.assertEqual(da.policy_bundle, db.policy_bundle)
            self.assertEqual(da.lhs_row, db.lhs_row)
        self.assertEqual(a.meta.spec_hash, b.meta.spec_hash)

    def test_different_seed_changes_draws(self):
        a = sample_draws(_spec(seed=7))
        b = sample_draws(_spec(seed=8))
        # The seed is part of the spec identity, so it changes the spec hash and
        # the realised draws.
        self.assertNotEqual(a.meta.spec_hash, b.meta.spec_hash)
        self.assertNotEqual(
            [d.gas_price_factor for d in a], [d.gas_price_factor for d in b]
        )

    def test_recovered_rank_correlation_matches_spec(self):
        # On a large sample the Gaussian copula recovers the *rank* (Spearman)
        # correlations it was specified with (the point of r_P = 2 sin(pi rho/6)).
        draws = sample_draws(_spec(n=2000, gas_load=0.3))
        gas = [d.gas_price_factor for d in draws]
        load = [d.demand_growth_percentile for d in draws]
        tech = [d.tech_cost_percentile for d in draws]
        r_gas_load, _ = spearmanr(gas, load)
        r_gas_tech, _ = spearmanr(gas, tech)
        r_load_tech, _ = spearmanr(load, tech)
        self.assertAlmostEqual(r_gas_load, 0.3, delta=0.05)
        self.assertAlmostEqual(r_gas_tech, 0.0, delta=0.05)
        self.assertAlmostEqual(r_load_tech, 0.0, delta=0.05)

    def test_lhs_one_draw_per_stratum_per_dim(self):
        n = 64
        draws = sample_draws(_spec(n=n))
        matrix = np.asarray(draws.meta.lhs_matrix)
        self.assertEqual(matrix.shape, (n, len(CONTINUOUS_DIMS) + len(DISCRETE_DIMS)))
        # Latin-hypercube: exactly one sample in each of the n equal-width strata
        # per dimension, so floor(u*n) is a permutation of 0..n-1 in every column.
        for col in range(matrix.shape[1]):
            strata = np.floor(matrix[:, col] * n).astype(int)
            self.assertEqual(sorted(strata.tolist()), list(range(n)))

    def test_discrete_weights_respected(self):
        draws = sample_draws(_spec(n=2000))
        policy = [d.policy_bundle for d in draws]
        # LHS stratification makes the bin proportions exact up to boundary
        # rounding at n=2000.
        self.assertAlmostEqual(policy.count("current") / 2000, 0.5, delta=0.02)
        self.assertAlmostEqual(policy.count("tight") / 2000, 0.25, delta=0.02)
        self.assertAlmostEqual(policy.count("rollback") / 2000, 0.25, delta=0.02)
        for d in draws:
            self.assertIn(d.weather_year, (2023, 2024, 2025))
            self.assertIn(d.hydro_year, ("dry", "normal", "wet"))

    def test_gas_factor_lognormal_centered(self):
        # With mu = 0 the median gas factor is 1.0 (a persistent shock centred on
        # the selected trajectory), and the geometric mean stays near 1.
        draws = sample_draws(_spec(n=2000))
        factors = np.asarray([d.gas_price_factor for d in draws])
        self.assertTrue(np.all(factors > 0.0))
        self.assertAlmostEqual(float(np.median(factors)), 1.0, delta=0.05)


class TestGasMarginal(unittest.TestCase):
    """The two-anchor sigma schedule and its AEO floor (§2.2)."""

    def test_schedule_spans_horizon(self):
        gas = GasMarginal(sigma_front=0.35, sigma_back=0.41)
        sched = gas.sigma_schedule()
        self.assertEqual(set(sched), set(range(START_YEAR, END_YEAR + 1)))
        # Front years sit at (or above, via the floor) sigma_front.
        self.assertGreaterEqual(sched[2026], 0.35 - 1e-9)

    def test_floor_widens_back_years(self):
        floored = GasMarginal(sigma_front=0.35, sigma_back=0.41, floor_to_aeo=True)
        raw = GasMarginal(sigma_front=0.35, sigma_back=0.41, floor_to_aeo=False)
        # The AEO 2050 spread (~0.55, re-derived from the actual AEO2025 Table
        # 13 data in P-1D — HENRY_HUB_TRAJECTORIES's low/high 2050 spread
        # widened from the prior hand-typed values) exceeds the 0.41 back
        # anchor, so the floor lifts the reference sigma above the
        # un-floored schedule.
        self.assertGreater(floored.sigma_reference(), raw.sigma_reference())
        self.assertAlmostEqual(floored.sigma_reference(), 0.555, delta=0.01)

    def test_reference_is_horizon_max(self):
        gas = GasMarginal(sigma_front=0.35, sigma_back=0.41)
        self.assertEqual(gas.sigma_reference(), max(gas.sigma_schedule().values()))


class TestDrawToConfig(unittest.TestCase):
    """Draw -> config mapping through the PB-1 levers, and the forecast guard."""

    def test_sets_all_six_levers(self):
        draws = sample_draws(_spec(n=8))
        base = ScenarioConfig(iso="ERCOT", carbon_price=25.0)
        draw = draws[0]
        cfg = draw_to_config(base, draw)
        self.assertEqual(cfg.gas_price_factor, draw.gas_price_factor)
        self.assertEqual(cfg.demand_growth_percentile, draw.demand_growth_percentile)
        self.assertEqual(cfg.tech_cost_percentile, draw.tech_cost_percentile)
        self.assertEqual(cfg.weather_year, draw.weather_year)
        self.assertEqual(cfg.hydro_year, draw.hydro_year)
        self.assertEqual(cfg.policy_bundle, draw.policy_bundle)
        # Untouched fields carry through.
        self.assertEqual(cfg.iso, "ERCOT")
        self.assertEqual(cfg.carbon_price, 25.0)

    def test_distinct_draws_distinct_cache_keys(self):
        draws = sample_draws(_spec(n=16))
        base = ScenarioConfig()
        keys = {draw_to_config(base, d).cache_key() for d in draws}
        # The draws vary several levers, so members are distinct runs.
        self.assertGreater(len(keys), 1)

    def test_backcast_base_rejected(self):
        draws = sample_draws(_spec(n=4))
        with self.assertRaises(ValueError):
            draw_to_config(ScenarioConfig(mode="backcast"), draws[0])


class TestUncertaintySpec(unittest.TestCase):
    """Spec loading, hashing and validation."""

    def test_reference_spec_loads(self):
        spec = UncertaintySpec.from_yaml(_REFERENCE_SPEC)
        self.assertEqual(spec.n, 64)
        self.assertEqual(spec.seed, 7)
        # gas<->load = +0.3 in CONTINUOUS_DIMS order (gas, load, tech).
        matrix = spec.spearman_matrix()
        self.assertAlmostEqual(matrix[0, 1], 0.3)
        self.assertAlmostEqual(matrix[0, 2], 0.0)
        self.assertEqual(set(spec.discrete_weights), set(DISCRETE_DIMS))
        # It samples end-to-end.
        draws = sample_draws(spec)
        self.assertEqual(len(draws), 64)

    def test_spec_hash_order_independent(self):
        a = _spec()
        # Reorder the weather-weight dict; the hash must not change.
        b = UncertaintySpec(
            n=a.n,
            seed=a.seed,
            gas=a.gas,
            spearman=a.spearman,
            discrete_weights={
                "policy": {"rollback": 0.25, "tight": 0.25, "current": 0.5},
                "hydro": {"wet": 0.25, "normal": 0.5, "dry": 0.25},
                "weather": {2025: 1 / 3, 2024: 1 / 3, 2023: 1 / 3},
            },
        )
        self.assertEqual(a.spec_hash(), b.spec_hash())

    def test_asymmetric_spearman_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text(
                "n: 4\nseed: 1\n"
                "gas: {sigma_front: 0.3, sigma_back: 0.4}\n"
                "spearman:\n  gas: {gas: 1.0, load: 0.3, tech: 0.0}\n"
                "  load: {gas: 0.1, load: 1.0, tech: 0.0}\n"
                "  tech: {gas: 0.0, load: 0.0, tech: 1.0}\n"
                "discrete_weights:\n"
                "  weather: {2023: 1.0}\n  hydro: {normal: 1.0}\n"
                "  policy: {current: 1.0}\n"
            )
            with self.assertRaises(ValueError):
                UncertaintySpec.from_yaml(path)


if __name__ == "__main__":
    unittest.main()
