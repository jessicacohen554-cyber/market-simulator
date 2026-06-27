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
    EIA923_SOURCE,
    EIA930_SOURCE,
    FAIL,
    PASS,
    SKIPPED,
    CalibrationReport,
    actuals_source,
    check_cf_band_occupancy,
    check_generation_mix,
    check_hourly_dispatch_correlation,
    check_price_duration_curve,
    run_calibration_check,
    signed_volume_error,
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
        result = check_generation_mix({"coal": 105.0}, {"coal": 100.0}, tolerance=0.05)
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


class TestActualsSourceAuthority(unittest.TestCase):
    """``actuals_source`` picks EIA-930 for variable renewables, 923 otherwise."""

    def test_variable_renewables_use_eia930(self):
        """Solar and wind volume are benchmarked against EIA-930."""
        for klass in ("solar", "Solar", "wind", "WIND"):
            self.assertEqual(actuals_source(klass), EIA930_SOURCE, klass)

    def test_every_other_class_uses_eia923(self):
        """Fossil and other non-renewable classes use EIA-923 as the baseline."""
        for klass in (
            "CC_REGULAR",
            "COAL_PRB",
            "CT_PEAKER",
            "ST_GAS",
            "nuclear",
            "hydro",
        ):
            self.assertEqual(actuals_source(klass), EIA923_SOURCE, klass)

    def test_nyiso_solar_overrides_to_eia923(self):
        """NYISO solar routes to EIA-923 (EIA-930 NYIS grid solar is a structural 0)."""
        for iso in ("NYISO", "nyiso"):
            self.assertEqual(actuals_source("solar", iso), EIA923_SOURCE, iso)
            self.assertEqual(actuals_source("Solar", iso), EIA923_SOURCE, iso)
        # NYISO wind is unaffected (NYIS reports grid wind normally) and other
        # ISOs' solar keeps the default EIA-930 routing.
        self.assertEqual(actuals_source("wind", "NYISO"), EIA930_SOURCE)
        self.assertEqual(actuals_source("solar", "CAISO"), EIA930_SOURCE)
        self.assertEqual(actuals_source("solar", "ERCOT"), EIA930_SOURCE)
        # No iso argument keeps the historical default.
        self.assertEqual(actuals_source("solar"), EIA930_SOURCE)


class TestSignedVolumeError(unittest.TestCase):
    """``signed_volume_error`` is the (model - actual)/actual fraction."""

    def test_signed_fraction(self):
        """A 10% over-build and a 20% short-fall keep their signs."""
        self.assertAlmostEqual(signed_volume_error(110.0, 100.0), 0.1)
        self.assertAlmostEqual(signed_volume_error(80.0, 100.0), -0.2)

    def test_zero_actual_handling_matches_pct_diff(self):
        """Zero actual gives 0.0 for a zero model and inf for a nonzero one."""
        self.assertEqual(signed_volume_error(0.0, 0.0), 0.0)
        self.assertEqual(signed_volume_error(5.0, 0.0), float("inf"))


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


class TestCheckHourlyDispatchCorrelation(unittest.TestCase):
    """``check_hourly_dispatch_correlation`` compares hourly dispatch shape."""

    def test_perfect_match_scores_r_one_and_zero_error(self):
        """Identical hourly series correlate perfectly with no error."""
        series = np.array([100.0, 200.0, 50.0, 300.0, 150.0])
        stats = check_hourly_dispatch_correlation({"coal": series}, {"coal": series})
        self.assertAlmostEqual(stats["coal"]["pearson_r"], 1.0)
        self.assertAlmostEqual(stats["coal"]["nrmse"], 0.0)

    def test_level_offset_keeps_r_one_but_raises_nrmse(self):
        """A pure level offset leaves the shape intact; only nrmse rises."""
        actual = np.array([100.0, 200.0, 50.0, 300.0])
        stats = check_hourly_dispatch_correlation(
            {"gas": actual + 50.0}, {"gas": actual}
        )
        self.assertAlmostEqual(stats["gas"]["pearson_r"], 1.0)
        self.assertGreater(stats["gas"]["nrmse"], 0.0)

    def test_anticorrelated_series_scores_negative_r(self):
        """A model that ramps opposite the actual fleet scores r = -1."""
        stats = check_hourly_dispatch_correlation(
            {"coal": np.array([40.0, 30.0, 20.0, 10.0])},
            {"coal": np.array([10.0, 20.0, 30.0, 40.0])},
        )
        self.assertAlmostEqual(stats["coal"]["pearson_r"], -1.0)

    def test_flat_model_over_cycling_fleet_yields_nan_r(self):
        """A baseload-flat model over a cycling fleet has undefined r."""
        stats = check_hourly_dispatch_correlation(
            {"coal": np.full(8, 100.0)},
            {"coal": np.array([1.0, 9.0, 2.0, 8.0, 3.0, 7.0, 4.0, 6.0])},
        )
        self.assertTrue(np.isnan(stats["coal"]["pearson_r"]))

    def test_annual_totals_reported_in_twh(self):
        """1000 MW across 8760 h is reported as 8.76 TWh."""
        stats = check_hourly_dispatch_correlation(
            {"gas": np.full(8760, 1000.0)}, {"gas": np.full(8760, 2000.0)}
        )
        self.assertAlmostEqual(stats["gas"]["model_twh"], 8.76)
        self.assertAlmostEqual(stats["gas"]["eia_twh"], 17.52)

    def test_length_mismatch_raises(self):
        """Two series of different length cannot be correlated."""
        with self.assertRaises(ValueError):
            check_hourly_dispatch_correlation(
                {"coal": np.zeros(10)}, {"coal": np.zeros(12)}
            )

    def test_only_fuels_in_both_mappings_are_compared(self):
        """A fuel missing from either side is silently dropped."""
        stats = check_hourly_dispatch_correlation(
            {"coal": np.array([1.0, 2.0, 3.0]), "gas": np.array([1.0, 2.0, 3.0])},
            {"coal": np.array([3.0, 1.0, 2.0])},
        )
        self.assertEqual(set(stats), {"coal"})


class TestCheckCfBandOccupancy(unittest.TestCase):
    """``check_cf_band_occupancy`` compares hours spent per CF band."""

    def test_identical_series_score_perfect(self):
        """Matching distributions give overlap 1, EMD 0 and band r 1."""
        rng = np.random.default_rng(7)
        mw = rng.uniform(0.0, 100.0, size=200)
        occ = check_cf_band_occupancy(mw, mw.copy(), capacity_mw=100.0)
        self.assertEqual(occ["band_overlap"], 1.0)
        self.assertEqual(occ["cf_emd"], 0.0)
        self.assertEqual(occ["band_r"], 1.0)

    def test_shuffled_hours_still_score_perfect(self):
        """The check is timing-free: permuting hours changes nothing."""
        rng = np.random.default_rng(7)
        mw = rng.uniform(0.0, 100.0, size=200)
        occ = check_cf_band_occupancy(rng.permutation(mw), mw, capacity_mw=100.0)
        self.assertEqual(occ["band_overlap"], 1.0)
        self.assertEqual(occ["cf_emd"], 0.0)

    def test_level_shift_is_caught(self):
        """A model parked one band below the actual scores zero overlap."""
        model = np.full(100, 75.0)  # 70-80% band
        actual = np.full(100, 95.0)  # 90-100% band
        occ = check_cf_band_occupancy(model, actual, capacity_mw=100.0)
        self.assertEqual(occ["band_overlap"], 0.0)
        self.assertAlmostEqual(occ["cf_emd"], 0.20, places=6)

    def test_emd_scales_with_distance(self):
        """Mass parked further from the observed level costs more EMD."""
        actual = np.full(100, 95.0)
        near = check_cf_band_occupancy(np.full(100, 85.0), actual, capacity_mw=100.0)[
            "cf_emd"
        ]
        far = check_cf_band_occupancy(np.full(100, 55.0), actual, capacity_mw=100.0)[
            "cf_emd"
        ]
        self.assertLess(near, far)

    def test_band_layout_and_top_band_owns_full_cf(self):
        """band_width 0.10 yields ten bands; CF == 1.0 lands in the top."""
        occ = check_cf_band_occupancy(
            np.array([100.0, 0.0]),
            np.array([100.0, 0.0]),
            capacity_mw=100.0,
        )
        self.assertEqual(len(occ["bands"]), 10)
        self.assertEqual(occ["bands"][-1]["model_hours"], 1)
        self.assertEqual(occ["bands"][0]["model_hours"], 1)

    def test_five_percent_bands(self):
        """band_width 0.05 yields twenty bands."""
        occ = check_cf_band_occupancy(
            np.array([50.0]),
            np.array([50.0]),
            capacity_mw=100.0,
            band_width=0.05,
        )
        self.assertEqual(len(occ["bands"]), 20)

    def test_default_capacity_is_joint_max(self):
        """Without a nameplate, the larger series maximum sets the CF scale."""
        occ = check_cf_band_occupancy(np.array([40.0, 80.0]), np.array([50.0, 100.0]))
        self.assertEqual(occ["capacity_mw"], 100.0)

    def test_length_mismatch_raises(self):
        """Two series of different length cannot be compared."""
        with self.assertRaises(ValueError):
            check_cf_band_occupancy(np.zeros(10), np.zeros(12))

    def test_all_zero_series_raise(self):
        """Two dead series have no capacity scale to normalize against."""
        with self.assertRaises(ValueError):
            check_cf_band_occupancy(np.zeros(10), np.zeros(10))


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
        dispatch = np.vstack([np.full(T, 100.0), np.full(T, 50.0)])
        prices = np.full((1, T), 40.0)
        result = _dispatch_result(dispatch, prices)
        context = _fleet_context(fuel_types=["gas_cc", "coal"], pmax_mw=[100.0, 50.0])
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
        report = run_calibration_check(self.CACHE_KEY, self.ISO, {"year": self.YEAR})
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
        report = run_calibration_check(self.CACHE_KEY, self.ISO, {"year": self.YEAR})
        for diagnostic in report.diagnostics:
            self.assertEqual(diagnostic.status, SKIPPED, diagnostic.name)
        # A run with only skipped diagnostics still passes.
        self.assertTrue(report.passed)

    def test_default_tolerance_is_five_percent(self):
        """The framework default tolerance is ±5%."""
        self.assertEqual(DEFAULT_TOLERANCE, 0.05)


if __name__ == "__main__":
    unittest.main()
