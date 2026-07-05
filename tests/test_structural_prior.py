"""Tests for the structural-error prior + convolution (PB-3).

Covers the pure fit (:func:`fit_prior`), the log-space convolution
(:func:`convolve`), the committed-source loader, and the ensemble integration
(the ``parametric_plus_structural`` band layer). No solves: the fit is
post-processing of the committed D-7 statmode probes and synthetic inputs.

The four invariants the plan (§3.2/§3.3) and prompt call out are each asserted:
prior wider than the plug-in normal, P50 point path not shifted, convolution
recovers the input spread when eps=0, and asymmetry when the bias is non-zero.
"""

import math
import unittest

import numpy as np
import pandas as pd
from scipy.stats import norm, t

from market_sim.config.constants import (
    START_YEAR,
    STATMODE_PROBE_RUNS,
    STRUCTURAL_PRIOR_FIT_YEARS,
)
from market_sim.ensemble import bands_from_metrics, compute_bands
from market_sim.structural_prior import (
    EMISSIONS_METRIC,
    PUBLISHED_QUANTILES,
    STRUCTURAL_LAYER,
    convolve,
    default_prior,
    fit_prior,
    load_statmode_residuals,
)

YEARS = STRUCTURAL_PRIOR_FIT_YEARS


def _flat_prior(bias_by_iso, sd, isos=("ERCOT", "PJM")):
    """Fit a prior whose per-ISO eps has a chosen mean and per-year noise.

    Builds ``model = actual * exp(eps)`` with ``eps`` centred at each ISO's
    target bias and spread by +/-``sd`` around it, so the fitted bias/noise are
    controllable in tests.
    """
    statmode, actual = {}, {}
    offsets = np.linspace(-1, 1, len(YEARS))
    offsets = offsets - offsets.mean()
    scaled = offsets / (offsets.std(ddof=1) or 1.0) * sd
    for iso in isos:
        b = bias_by_iso[iso]
        base = np.full(len(YEARS), 100.0)
        eps = b + scaled
        statmode[iso] = {
            y: float(base[i] * math.exp(eps[i])) for i, y in enumerate(YEARS)
        }
        actual[iso] = {y: 100.0 for y in YEARS}
    return fit_prior(statmode, actual)


class FitPriorTests(unittest.TestCase):
    def test_eps_and_bias_from_log_ratio(self):
        statmode = {"ERCOT": {y: 110.0 for y in YEARS}}
        actual = {"ERCOT": {y: 100.0 for y in YEARS}}
        prior = fit_prior(statmode, actual)
        r = prior.per_iso["ERCOT"]
        for e in r.eps:
            self.assertAlmostEqual(e, math.log(1.1), places=10)
        self.assertAlmostEqual(r.bias, math.log(1.1), places=10)
        self.assertAlmostEqual(r.noise_sd, 0.0, places=12)

    def test_pooled_variance_and_inflation(self):
        prior = _flat_prior({"ERCOT": 0.0, "PJM": 0.2}, sd=0.05)
        # Both ISOs have the same synthetic noise, so pooled var == that var.
        self.assertAlmostEqual(prior.pooled_noise_var, 0.05**2, places=6)
        self.assertAlmostEqual(prior.small_sample_inflation, 1.0 + 1.0 / len(YEARS))
        self.assertAlmostEqual(
            prior.scale(0), math.sqrt(0.05**2 * (1 + 1 / len(YEARS))), places=6
        )

    def test_rejects_non_fit_year(self):
        # 2022 is quarantined (rule 22) -- must never enter the fit.
        statmode = {"ERCOT": {2022: 100.0, 2023: 100.0, 2024: 100.0, 2025: 100.0}}
        actual = {"ERCOT": {y: 100.0 for y in YEARS}}
        with self.assertRaises(ValueError):
            fit_prior(statmode, actual)

    def test_rejects_missing_year(self):
        statmode = {"ERCOT": {2023: 100.0, 2024: 100.0}}
        actual = {"ERCOT": {2023: 100.0, 2024: 100.0}}
        with self.assertRaises(ValueError):
            fit_prior(statmode, actual)

    def test_as_dict_serialisable_and_complete(self):
        prior = _flat_prior({"ERCOT": 0.0, "PJM": 0.2}, sd=0.05)
        d = prior.as_dict()
        self.assertEqual(d["horizon_lambda"], 0.0)
        self.assertTrue(d["dispatch_conditional"])
        self.assertIn("ERCOT", d["per_iso"])
        # Round-trips through JSON without custom encoders.
        import json

        json.loads(json.dumps(d))


class PriorWidthTests(unittest.TestCase):
    def test_prior_wider_than_plugin_normal(self):
        """Fitted Student-t prior must be wider than the plug-in normal (§3.2)."""
        prior = _flat_prior({"ERCOT": 0.0, "PJM": 0.2}, sd=0.05)
        # Symmetric interval width cancels the (equal) location; compare the
        # fitted t against a plug-in normal with the un-inflated pooled scale.
        for q in (0.9, 0.95, 0.99):
            fitted = prior.scale(0) * (t.ppf(q, prior.nu) - t.ppf(1 - q, prior.nu))
            plugin = prior.plugin_normal_scale() * (norm.ppf(q) - norm.ppf(1 - q))
            self.assertGreater(fitted, plugin)

    def test_horizon_widens_variance_when_lambda_nonzero(self):
        prior = _flat_prior({"ERCOT": 0.0, "PJM": 0.2}, sd=0.05)
        base = prior.scale(0)
        # lambda == 0 -> horizon is a no-op (dispatch-conditional).
        self.assertAlmostEqual(prior.scale(10), base, places=12)
        widened = fit_prior(
            {"ERCOT": {2023: 108.0, 2024: 110.0, 2025: 112.0}},
            {"ERCOT": {y: 100.0 for y in YEARS}},
            horizon_lambda=0.1,
        )
        self.assertGreater(widened.pooled_noise_var, 0.0)
        self.assertGreater(widened.scale(5), widened.scale(0))
        self.assertFalse(widened.is_dispatch_conditional())


class ConvolveTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(0)
        self.emissions = list(100.0 + rng.normal(0, 5, size=64))
        self.values = {START_YEAR: {EMISSIONS_METRIC: self.emissions}}

    def test_zero_prior_recovers_input_spread(self):
        """eps==0 (model==actual) -> structural bands == parametric bands."""
        zero = fit_prior(
            {"ERCOT": {y: 100.0 for y in YEARS}},
            {"ERCOT": {y: 100.0 for y in YEARS}},
        )
        struct = convolve(self.values, zero, "ERCOT", seed=1)
        param = compute_bands(self.values, seed=1, quantiles=(0.1, 0.5, 0.9))
        param_by_q = {r["quantile"]: r["value"] for r in param}
        # eps==0 -> the structural sample is the parametric values each repeated
        # K times, so its quantiles recover the parametric ones (the K-fold
        # replication perturbs type-7 interpolation only negligibly).
        for row in struct:
            if row["quantile"] in param_by_q:
                self.assertAlmostEqual(
                    row["value"],
                    param_by_q[row["quantile"]],
                    delta=abs(param_by_q[row["quantile"]]) * 0.005,
                )

    def test_asymmetric_when_bias_nonzero(self):
        """Positive bias -> right-skewed published band (§3.2 asymmetry)."""
        prior = _flat_prior({"ERCOT": 0.0, "PJM": 0.2}, sd=0.03, isos=("PJM",))
        rows = {
            r["quantile"]: r["value"]
            for r in convolve(self.values, prior, "PJM", seed=2)
        }
        upper = rows[0.95] - rows[0.5]
        lower = rows[0.5] - rows[0.05]
        self.assertGreater(upper, lower)

    def test_only_emissions_gets_structural_layer(self):
        vals = {
            START_YEAR: {EMISSIONS_METRIC: self.emissions, "avg_price": self.emissions}
        }
        prior = _flat_prior({"ERCOT": 0.1, "PJM": 0.2}, sd=0.03)
        rows = convolve(vals, prior, "ERCOT", seed=3)
        self.assertEqual({r["metric"] for r in rows}, {EMISSIONS_METRIC})
        self.assertTrue(all(r["layer"] == STRUCTURAL_LAYER for r in rows))
        self.assertEqual(
            sorted({r["quantile"] for r in rows}), list(PUBLISHED_QUANTILES)
        )

    def test_deterministic_given_seed(self):
        prior = _flat_prior({"ERCOT": 0.1, "PJM": 0.2}, sd=0.03)
        a = convolve(self.values, prior, "ERCOT", seed=9)
        b = convolve(self.values, prior, "ERCOT", seed=9)
        self.assertEqual([r["value"] for r in a], [r["value"] for r in b])


class RecomputeAndPointForecastTests(unittest.TestCase):
    def _metrics(self):
        rng = np.random.default_rng(4)
        rows = []
        for y in (START_YEAR, START_YEAR + 1):
            for i in range(32):
                rows.append(
                    {
                        "draw_id": f"draw-{i:04d}",
                        "year": y,
                        "metric": EMISSIONS_METRIC,
                        "value": float(100 + y - START_YEAR + rng.normal(0, 4)),
                    }
                )
        return pd.DataFrame(rows)

    def test_p50_point_path_not_shifted_by_prior(self):
        """Folding the prior must not move the parametric P50 (rule 13)."""
        metrics = self._metrics()
        prior = _flat_prior({"ERCOT": 0.2, "PJM": 0.2}, sd=0.03)
        without = bands_from_metrics(metrics, seed=5)
        withp = bands_from_metrics(metrics, seed=5, iso="ERCOT", prior=prior)
        param_wo = without[
            (without.layer == "parametric") & (without.quantile == 0.5)
        ].set_index("year")["value"]
        param_w = withp[
            (withp.layer == "parametric") & (withp.quantile == 0.5)
        ].set_index("year")["value"]
        pd.testing.assert_series_equal(param_wo, param_w)
        # The structural layer is present and (biased) distinct from parametric.
        self.assertIn(STRUCTURAL_LAYER, set(withp.layer))

    def test_recompute_requires_iso_with_prior(self):
        prior = _flat_prior({"ERCOT": 0.2, "PJM": 0.2}, sd=0.03)
        with self.assertRaises(ValueError):
            bands_from_metrics(self._metrics(), seed=5, prior=prior)


class CommittedSourceTests(unittest.TestCase):
    def test_default_prior_matches_d7_report_signs(self):
        """The fit off committed statmode probes reproduces the D-7 CO2 signs."""
        prior = default_prior()
        self.assertEqual(set(prior.per_iso), set(STATMODE_PROBE_RUNS))
        # D-7 report: PJM/MISO/CAISO run high (positive bias); ERCOT ~0.
        self.assertGreater(prior.bias("PJM"), 0.18)
        self.assertGreater(prior.bias("MISO"), 0.08)
        self.assertGreater(prior.bias("CAISO"), 0.08)
        self.assertLess(abs(prior.bias("ERCOT")), 0.03)
        self.assertTrue(prior.is_dispatch_conditional())
        self.assertIn("dispatch-conditional", prior.label())

    def test_loader_reads_only_fit_years(self):
        statmode, actual, run_ids = load_statmode_residuals(isos=["ERCOT"])
        self.assertEqual(sorted(statmode["ERCOT"]), list(YEARS))
        self.assertEqual(sorted(actual["ERCOT"]), list(YEARS))
        self.assertEqual(run_ids["ERCOT"], STATMODE_PROBE_RUNS["ERCOT"])


if __name__ == "__main__":
    unittest.main()
