"""Tests for emissions accounting from dispatch results."""

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.results.emissions import (
    compute_emissions,
    compute_fossil_avg_rate,
    compute_nox,
    compute_so2,
    startup_co2_tons,
)


class TestStartupCo2Tons(unittest.TestCase):
    """R6 reporting-only startup CO2: model_starts x measured per-start kg."""

    def test_startup_co2_matches_manual(self):
        fit = pd.DataFrame({"plant_code": [100, 200, 300], "model_starts": [10, 4, 7]})
        kg = {100: 5000.0, 200: 2000.0}  # 300 uncovered -> zero
        out = startup_co2_tons(fit, kg)
        self.assertAlmostEqual(out.loc[100], 10 * 5000.0 / 1000.0)  # 50 t
        self.assertAlmostEqual(out.loc[200], 4 * 2000.0 / 1000.0)  # 8 t
        self.assertAlmostEqual(out.loc[300], 0.0)  # uncovered plant

    def test_empty_when_no_starts_column(self):
        fit = pd.DataFrame({"plant_code": [1], "model_gwh": [1.0]})
        self.assertTrue(startup_co2_tons(fit, {1: 100.0}).empty)


class TestComputeEmissions(unittest.TestCase):
    """``compute_emissions`` weights dispatch by per-generator CO2 rates."""

    def test_matches_manual_calculation(self):
        dispatch = np.array([[10.0, 20.0, 30.0], [5.0, 0.0, 15.0]])
        rates = np.array([0.4, 1.0])

        result = compute_emissions(dispatch, rates)

        manual = dispatch[0] * 0.4 + dispatch[1] * 1.0
        np.testing.assert_allclose(result, manual)
        self.assertEqual(result.shape, (3,))

    def test_equals_sum_of_dispatch_times_rates(self):
        rng = np.random.default_rng(0)
        dispatch = rng.uniform(0.0, 100.0, size=(7, 24))
        rates = rng.uniform(0.0, 1.0, size=7)

        np.testing.assert_allclose(
            compute_emissions(dispatch, rates),
            (dispatch * rates[:, None]).sum(axis=0),
        )

    def test_zero_rates_produce_zero_emissions(self):
        dispatch = np.full((4, 12), 50.0)

        result = compute_emissions(dispatch, np.zeros(4))

        np.testing.assert_array_equal(result, np.zeros(12))


class TestComputeFossilAvgRate(unittest.TestCase):
    """``compute_fossil_avg_rate`` is the hourly fossil-only average tCO2/MWh."""

    def test_all_fossil_fleet_matches_weighted_average(self):
        # Two fossil units, hand-computed dispatch-weighted average per hour.
        dispatch = np.array([[10.0, 20.0, 0.0], [30.0, 20.0, 5.0]])
        rates = np.array([0.4, 1.0])

        result = compute_fossil_avg_rate(dispatch, rates)

        expected = np.array(
            [
                (10.0 * 0.4 + 30.0 * 1.0) / 40.0,
                (20.0 * 0.4 + 20.0 * 1.0) / 40.0,
                (0.0 * 0.4 + 5.0 * 1.0) / 5.0,
            ]
        )
        np.testing.assert_allclose(result, expected)
        self.assertEqual(result.shape, (3,))

    def test_zero_carbon_generation_excluded_from_both_sides(self):
        # A zero-rate (nuclear-like) unit must not dilute the fossil average:
        # its MWh stay out of the denominator, its (zero) tons out of the
        # numerator, so the rate equals the fossil unit's own rate.
        dispatch = np.array([[50.0, 50.0], [1000.0, 1000.0]])
        rates = np.array([0.6, 0.0])

        result = compute_fossil_avg_rate(dispatch, rates)

        np.testing.assert_allclose(result, [0.6, 0.6])

    def test_zero_fossil_dispatch_hour_returns_zero_not_nan(self):
        # Hour 1 has no fossil dispatch at all: documented convention is 0.0
        # (nothing emitting to attribute), never nan/inf.
        dispatch = np.array([[100.0, 0.0], [200.0, 500.0]])
        rates = np.array([0.5, 0.0])  # only generator 0 is fossil

        result = compute_fossil_avg_rate(dispatch, rates)

        np.testing.assert_allclose(result, [0.5, 0.0])
        self.assertTrue(np.all(np.isfinite(result)))


class TestVendoredParityScope2(unittest.TestCase):
    """The scope2-lce-portfolio vendored copy matches the upstream function.

    The LCE portfolio tool is import-isolated (it never imports
    ``market_sim``), so the parity check lives here on the market_sim side:
    the vendored module is pure numpy and is loaded by file path only.
    """

    VENDORED_PATH = (
        Path(__file__).resolve().parents[1]
        / "scope2-lce-portfolio"
        / "src"
        / "lce_portfolio"
        / "vendored"
        / "fossil_avg_rate.py"
    )

    def _load_vendored(self):
        spec = importlib.util.spec_from_file_location(
            "_vendored_fossil_avg_rate", self.VENDORED_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_vendored_copy_produces_identical_outputs(self):
        vendored = self._load_vendored()
        rng = np.random.default_rng(42)
        dispatch = rng.uniform(0.0, 500.0, size=(9, 48))
        dispatch[:, 7] = 0.0  # a zero-dispatch hour exercises the 0.0 branch
        rates = rng.uniform(0.0, 1.2, size=9)
        rates[[1, 4, 6]] = 0.0  # zero-carbon units

        np.testing.assert_array_equal(
            compute_fossil_avg_rate(dispatch, rates),
            vendored.compute_fossil_avg_rate(dispatch, rates),
        )


class TestComputeNox(unittest.TestCase):
    """``compute_nox`` follows the same pattern with NOx rates."""

    def test_matches_manual_calculation(self):
        dispatch = np.array([[100.0, 200.0], [50.0, 25.0]])
        rates = np.array([0.0015, 0.0003])

        result = compute_nox(dispatch, rates)

        manual = dispatch[0] * 0.0015 + dispatch[1] * 0.0003
        np.testing.assert_allclose(result, manual)
        self.assertEqual(result.shape, (2,))


class TestComputeSo2(unittest.TestCase):
    """``compute_so2`` mirrors ``compute_nox``/``compute_emissions`` with SO2 rates."""

    def test_matches_manual_calculation(self):
        dispatch = np.array([[100.0, 200.0], [50.0, 25.0]])
        rates = np.array([0.0008, 0.0001])

        result = compute_so2(dispatch, rates)

        manual = dispatch[0] * 0.0008 + dispatch[1] * 0.0001
        np.testing.assert_allclose(result, manual)
        self.assertEqual(result.shape, (2,))

    def test_zero_rates_produce_zero_so2(self):
        dispatch = np.full((3, 8), 40.0)

        result = compute_so2(dispatch, np.zeros(3))

        np.testing.assert_array_equal(result, np.zeros(8))


class TestNoxSo2ReproduceCampdMass(unittest.TestCase):
    """W3-E2: NOx/SO2 system tons reproduce a fixture plant's CAMPD annual mass.

    Mirrors ``test_emission_rate_basis.py``'s CO2 round-trip guard: a plant's
    measured ``nox_kg_per_mwh_net`` / ``so2_kg_per_mwh_net`` rate (from
    :func:`market_sim.data.campd.plant_emission_rates`), applied via
    :func:`compute_nox` / :func:`compute_so2` to that same net generation,
    must reproduce the plant's measured CAMPD NOx/SO2 mass within backfill
    tolerance -- the same identity CO2 is already guarded on.
    """

    def _fixture_plant(self, parasitic: float) -> pd.DataFrame:
        """One 1-gen plant, 24 on-hours, NOx/SO2 reported for every hour."""
        n = 24
        ts = pd.date_range("2023-06-01 00:00", periods=n, freq="h")
        gross = np.full(n, 200.0)
        heat = gross * 8.0  # 8 MMBtu/MWh gross
        return pd.DataFrame(
            {
                "plant_id": 12345,
                "facility_name": "Fixture",
                "state": "TX",
                "year": 2023,
                "date": ts.normalize(),
                "hour": ts.hour,
                "gross_mw": gross,
                "steam_load": np.nan,
                "co2_kg": heat * 53.0,
                "nox_kg": gross * 0.02,
                "so2_kg": gross * 0.01,
                "heat_mmbtu": heat,
                "hour_of_year": np.arange(n),
            }
        )

    def test_nox_tons_reproduce_measured_mass(self):
        from market_sim.data import campd

        parasitic = 0.94  # 6% station service
        df = self._fixture_plant(parasitic)
        rates = campd.plant_emission_rates(df, {12345: parasitic})
        row = rates[(rates["plant_id"] == 12345) & (rates["year"] == 2023)].iloc[0]

        net_mwh_per_hour = float(df["gross_mw"].iloc[0]) * parasitic
        dispatch = np.full((1, len(df)), net_mwh_per_hour)
        nox_rate_tons_per_mwh = row["nox_kg_per_mwh_net"] / 1000.0

        result_tons = float(compute_nox(dispatch, [nox_rate_tons_per_mwh]).sum())
        measured_tons = float(df["nox_kg"].sum()) / 1000.0

        self.assertAlmostEqual(result_tons, measured_tons, delta=measured_tons * 1e-3)

    def test_so2_tons_reproduce_measured_mass(self):
        from market_sim.data import campd

        parasitic = 0.94
        df = self._fixture_plant(parasitic)
        rates = campd.plant_emission_rates(df, {12345: parasitic})
        row = rates[(rates["plant_id"] == 12345) & (rates["year"] == 2023)].iloc[0]

        net_mwh_per_hour = float(df["gross_mw"].iloc[0]) * parasitic
        dispatch = np.full((1, len(df)), net_mwh_per_hour)
        so2_rate_tons_per_mwh = row["so2_kg_per_mwh_net"] / 1000.0

        result_tons = float(compute_so2(dispatch, [so2_rate_tons_per_mwh]).sum())
        measured_tons = float(df["so2_kg"].sum()) / 1000.0

        self.assertAlmostEqual(result_tons, measured_tons, delta=measured_tons * 1e-3)


if __name__ == "__main__":
    unittest.main()
