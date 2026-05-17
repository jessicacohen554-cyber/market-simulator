"""Tests for the calibration framework.

The generation-mix and price-duration-curve checks are exercised directly
on synthetic inputs. ``run_calibration_check`` is exercised against a
synthetic ``DispatchResult`` written to a temporary cache directory, so no
dispatch LP is solved.
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from market_sim.model.dispatch import DispatchResult
from market_sim.results import cache
from market_sim.results.calibration import (
    DEFAULT_TOLERANCE,
    FAIL,
    PASS,
    SKIPPED,
    CalibrationReport,
    check_generation_mix,
    check_price_duration_curve,
    run_calibration_check,
)
from market_sim.results.outputs import FleetContext


class TestCheckGenerationMix(unittest.TestCase):
    """``check_generation_mix`` compares fuel-type generation in TWh."""

    def test_flags_deviation_above_tolerance(self):
        """A fuel more than 5% off the benchmark is flagged as failing."""
        model = {"gas_cc": 100.0, "coal": 50.0, "wind": 30.0}
        # coal is +20% off; the others are exact.
        benchmark = {"gas_cc": 100.0, "coal": 41.667, "wind": 30.0}

        result = check_generation_mix(model, benchmark, tolerance=0.05)

        self.assertEqual(result["coal"]["pass_fail"], FAIL)
        self.assertGreater(abs(result["coal"]["pct_diff"]), 0.05)
        self.assertEqual(result["gas_cc"]["pass_fail"], PASS)
        self.assertEqual(result["wind"]["pass_fail"], PASS)

    def test_passes_within_tolerance(self):
        """Every fuel within 5% of the benchmark passes."""
        model = {"gas_cc": 100.0, "coal": 50.0, "wind": 30.0}
        # Each fuel is off by at most ~3%, inside the tolerance.
        benchmark = {"gas_cc": 102.0, "coal": 48.5, "wind": 30.5}

        result = check_generation_mix(model, benchmark, tolerance=0.05)

        for fuel, detail in result.items():
            self.assertEqual(detail["pass_fail"], PASS, fuel)

    def test_boundary_deviation_just_inside_tolerance_passes(self):
        """A deviation exactly at the tolerance passes."""
        result = check_generation_mix(
            {"coal": 105.0}, {"coal": 100.0}, tolerance=0.05
        )
        self.assertEqual(result["coal"]["pass_fail"], PASS)
        self.assertAlmostEqual(result["coal"]["pct_diff"], 0.05)

    def test_fuel_missing_from_model_is_flagged(self):
        """A fuel the benchmark expects but the model omits fails."""
        result = check_generation_mix(
            {"gas_cc": 100.0}, {"gas_cc": 100.0, "nuclear": 40.0}
        )
        self.assertEqual(result["nuclear"]["model"], 0.0)
        self.assertEqual(result["nuclear"]["pass_fail"], FAIL)

    def test_accepts_annual_summary_dict(self):
        """A summary dict carrying ``generation_twh`` is accepted directly."""
        summary = {"generation_twh": {"coal": 50.0}, "avg_price": 30.0}
        result = check_generation_mix(summary, {"coal": 50.0})
        self.assertEqual(result["coal"]["pass_fail"], PASS)


class TestCheckPriceDurationCurve(unittest.TestCase):
    """``check_price_duration_curve`` compares sorted price arrays."""

    def test_produces_sensible_metrics(self):
        """Metrics are ordered P10 <= P50 <= P90 and span the inputs."""
        rng = np.random.default_rng(0)
        prices = rng.uniform(10.0, 200.0, size=8760)
        benchmark = rng.uniform(10.0, 200.0, size=8760)

        metrics = check_price_duration_curve(prices, benchmark)

        self.assertEqual(set(metrics), {"P10", "P50", "P90", "mean"})
        for key in ("P10", "P50", "P90", "mean"):
            self.assertEqual(set(metrics[key]), {"model", "benchmark", "pct_diff"})

        self.assertLessEqual(metrics["P10"]["model"], metrics["P50"]["model"])
        self.assertLessEqual(metrics["P50"]["model"], metrics["P90"]["model"])
        # The mean of a broad uniform sample sits near the median.
        self.assertGreater(metrics["mean"]["model"], metrics["P10"]["model"])
        self.assertLess(metrics["mean"]["model"], metrics["P90"]["model"])

    def test_identical_curves_have_zero_diff(self):
        """Comparing a curve against itself yields zero deviation."""
        prices = np.linspace(10.0, 100.0, 100)
        metrics = check_price_duration_curve(prices, prices)
        for detail in metrics.values():
            self.assertEqual(detail["pct_diff"], 0.0)
            self.assertEqual(detail["model"], detail["benchmark"])

    def test_accepts_two_dimensional_zonal_prices(self):
        """A ``(n_zones, T)`` price array is flattened before comparison."""
        prices = np.full((4, 24), 40.0)
        metrics = check_price_duration_curve(prices, np.full(24, 40.0))
        self.assertEqual(metrics["mean"]["model"], 40.0)

    def test_empty_prices_raise(self):
        """An empty price array is rejected."""
        with self.assertRaises(ValueError):
            check_price_duration_curve(np.array([]), np.array([1.0]))


def _fleet_context(fuel_types, pmax_mw) -> FleetContext:
    """Build a minimal ``FleetContext`` for a synthetic thermal fleet."""
    return FleetContext(
        fuel_types=list(fuel_types),
        pmax_mw=list(pmax_mw),
        emission_rate=[0.0] * len(fuel_types),
        efficiency_bins=["default"] * len(fuel_types),
        heat_rates=[0.0] * len(fuel_types),
        zones=["zone"] * len(fuel_types),
        unit_ids=[f"G{i}" for i in range(len(fuel_types))],
        wind_cap_mw=0.0,
        solar_cap_mw=0.0,
        wind_potential_mwh=0.0,
        solar_potential_mwh=0.0,
        storage_energy_cap_mwh=0.0,
    )


def _dispatch_result(dispatch, prices) -> DispatchResult:
    """Build a synthetic ``DispatchResult`` from dispatch and price arrays."""
    n_gen, T = dispatch.shape
    n_zones = prices.shape[0]
    return DispatchResult(
        dispatch=dispatch,
        wind_dispatched=np.zeros((n_zones, T)),
        solar_dispatched=np.zeros((n_zones, T)),
        slack=np.zeros((n_zones, T)),
        dump=np.zeros((n_zones, T)),
        prices=prices,
        storage_charge=None,
        storage_discharge=None,
        storage_soc=None,
        flows=None,
        objective_value=0.0,
        status="Optimal",
        build_time=0.0,
        solve_time=0.0,
    )


class TestRunCalibrationCheck(unittest.TestCase):
    """``run_calibration_check`` walks the four diagnostics in order."""

    ISO = "ERCOT"
    CACHE_KEY = "testkey"
    YEAR = 2026

    def setUp(self):
        """Redirect the cache to a temp dir and write one synthetic year."""
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name)

        T = 240
        # Two generators: one gas_cc at 100 MW flat, one coal at 50 MW flat.
        dispatch = np.vstack(
            [np.full(T, 100.0), np.full(T, 50.0)]
        )
        prices = np.full((1, T), 40.0)
        result = _dispatch_result(dispatch, prices)
        context = _fleet_context(
            fuel_types=["gas_cc", "coal"], pmax_mw=[100.0, 50.0]
        )
        path = cache.get_cache_path(self.ISO, self.CACHE_KEY, self.YEAR)
        result.to_parquet(path, context=context)

        # Generation: gas_cc = 100 MW * 240 h = 24000 MWh = 0.024 TWh; coal half.
        self._gen_twh = {"gas_cc": 0.024, "coal": 0.012}

    def tearDown(self):
        cache.CACHE_ROOT = self._orig_root
        self._tmp.cleanup()

    def test_all_diagnostics_pass_with_matching_benchmarks(self):
        """Matching benchmarks make every diagnostic pass."""
        benchmarks = {
            "year": self.YEAR,
            "generation_twh": self._gen_twh,
            "prices": np.full(240, 40.0),
            "avg_price": 40.0,
            "capacity_factors": {"gas_cc": 1.0, "coal": 1.0},
        }
        report = run_calibration_check(self.CACHE_KEY, self.ISO, benchmarks)

        self.assertIsInstance(report, CalibrationReport)
        self.assertTrue(report.passed)
        for diagnostic in report.diagnostics:
            self.assertEqual(diagnostic.status, PASS, diagnostic.name)

    def test_diagnostics_are_in_fixed_order(self):
        """The report exposes diagnostics in the documented order."""
        report = run_calibration_check(
            self.CACHE_KEY, self.ISO, {"year": self.YEAR}
        )
        names = [d.name for d in report.diagnostics]
        self.assertEqual(
            names,
            [
                "generation_mix",
                "price_duration_curve",
                "avg_price",
                "capacity_factors",
            ],
        )

    def test_generation_mix_failure_fails_the_report(self):
        """A generation-mix deviation fails diagnostic (1) and the run."""
        benchmarks = {
            "year": self.YEAR,
            "generation_twh": {"gas_cc": 0.024, "coal": 0.030},
        }
        report = run_calibration_check(self.CACHE_KEY, self.ISO, benchmarks)

        self.assertEqual(report.generation_mix.status, FAIL)
        self.assertFalse(report.passed)
        self.assertEqual(report.generation_mix.details["coal"]["pass_fail"], FAIL)

    def test_missing_benchmarks_skip_diagnostics(self):
        """Diagnostics with no benchmark are skipped, not failed."""
        report = run_calibration_check(
            self.CACHE_KEY, self.ISO, {"year": self.YEAR}
        )
        for diagnostic in report.diagnostics:
            self.assertEqual(diagnostic.status, SKIPPED, diagnostic.name)
        # A run with only skipped diagnostics still passes.
        self.assertTrue(report.passed)

    def test_default_tolerance_is_five_percent(self):
        """The framework default tolerance is ±5%."""
        self.assertEqual(DEFAULT_TOLERANCE, 0.05)


if __name__ == "__main__":
    unittest.main()
