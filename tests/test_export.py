"""Tests for scenario export to compact frontend JSON.

The dispatch LP is mocked: ``solve_dispatch`` is patched to return a
synthetic :class:`DispatchResult`, so a scenario is run and cached without
the cost of solving, then exported.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from market_sim import runner
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.dispatch import DispatchResult
from market_sim.results import cache, export
from market_sim.results.outputs import FleetContext


def _fake_solve(fleet, demand, *args, **kwargs):
    """Return a synthetic ``DispatchResult`` sized to the fleet and demand."""
    n_gen = fleet.n_gen
    T = demand.shape[1]
    n_zones = demand.shape[0]
    return DispatchResult(
        dispatch=np.full((n_gen, T), 5.0),
        wind_dispatched=np.zeros((n_zones, T)),
        solar_dispatched=np.zeros((n_zones, T)),
        slack=np.zeros((n_zones, T)),
        dump=np.zeros((n_zones, T)),
        prices=np.full((n_zones, T), 30.0),
        storage_charge=None,
        storage_discharge=None,
        storage_soc=None,
        flows=None,
        objective_value=0.0,
        status="Optimal",
        build_time=0.0,
        solve_time=0.0,
    )


class TestComputeCurtailment(unittest.TestCase):
    """``compute_curtailment`` is available potential minus dispatched."""

    def test_potential_minus_dispatched(self):
        potential = np.array([[10.0, 8.0], [5.0, 6.0]])
        dispatched = np.array([[6.0, 8.0], [5.0, 2.0]])

        result = export.compute_curtailment(potential, dispatched)

        np.testing.assert_allclose(result, [[4.0, 0.0], [0.0, 4.0]])

    def test_non_negative_when_dispatch_within_potential(self):
        rng = np.random.default_rng(1)
        potential = rng.uniform(0.0, 100.0, size=(4, 50))
        dispatched = potential * rng.uniform(0.0, 1.0, size=(4, 50))

        curtailment = export.compute_curtailment(potential, dispatched)

        self.assertTrue(np.all(curtailment >= 0.0))


def _fixture_context(nox_rate=None, so2_rate=None) -> FleetContext:
    """One-gen ``FleetContext`` fixture for fast ``_summarize_year`` tests."""
    return FleetContext(
        fuel_types=["gas_cc"],
        pmax_mw=[100.0],
        emission_rate=[0.4],
        nox_rate=[] if nox_rate is None else nox_rate,
        so2_rate=[] if so2_rate is None else so2_rate,
        efficiency_bins=["default"],
        heat_rates=[7.0],
        zones=["North"],
        unit_ids=["G1"],
        wind_cap_mw=0.0,
        solar_cap_mw=0.0,
        wind_potential_mwh=0.0,
        solar_potential_mwh=0.0,
        storage_energy_cap_mwh=0.0,
    )


class TestSummarizeYearNoxSo2(unittest.TestCase):
    """W3-E2: ``_summarize_year`` reports NOx/SO2 tons alongside CO2 megatons."""

    def _result(self, gen_mwh_per_hour=10.0, hours=24):
        n_zones = 1
        return DispatchResult(
            dispatch=np.full((1, hours), gen_mwh_per_hour),
            wind_dispatched=np.zeros((n_zones, hours)),
            solar_dispatched=np.zeros((n_zones, hours)),
            slack=np.zeros((n_zones, hours)),
            dump=np.zeros((n_zones, hours)),
            prices=np.full((n_zones, hours), 30.0),
            storage_charge=None,
            storage_discharge=None,
            storage_soc=None,
            flows=None,
            objective_value=0.0,
            status="Optimal",
            build_time=0.0,
            solve_time=0.0,
        )

    def test_nox_so2_tons_match_manual_calculation(self):
        result = self._result(gen_mwh_per_hour=10.0, hours=24)
        context = _fixture_context(nox_rate=[0.002], so2_rate=[0.001])

        summary = export._summarize_year(result, context)

        total_mwh = 10.0 * 24
        self.assertAlmostEqual(summary["nox_tonnes"], total_mwh * 0.002, places=2)
        self.assertAlmostEqual(summary["so2_tonnes"], total_mwh * 0.001, places=2)
        # CO2 stays the primary column; NOx/SO2 are additive, not replacing it.
        self.assertIn("emissions_mt", summary)

    def test_missing_rates_default_to_zero(self):
        """Older cached contexts (pre-W3-E2) carry empty nox_rate/so2_rate."""
        result = self._result()
        context = _fixture_context(nox_rate=None, so2_rate=None)

        summary = export._summarize_year(result, context)

        self.assertEqual(summary["nox_tonnes"], 0.0)
        self.assertEqual(summary["so2_tonnes"], 0.0)


@pytest.mark.slow  # runs a real 3-year run_scenario_iso (fleet load dominates, ~4-5min/test)
class TestExportScenarioJson(unittest.TestCase):
    """A cached scenario exports to one valid, compact JSON file."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name) / "results"

    def tearDown(self):
        cache.CACHE_ROOT = self._original_root
        self._tmp.cleanup()

    def _run_and_export(self, end_year=2028):
        """Run and cache an ERCOT scenario, then export it; return the path."""
        config = ScenarioConfig(iso="ERCOT")
        with (
            patch.object(runner, "END_YEAR", end_year),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
        ):
            key = runner.run_scenario_iso(config, "ERCOT")

        out_dir = Path(self._tmp.name) / "out"
        with patch.object(export, "END_YEAR", end_year):
            path = export.export_scenario_json(key, "ERCOT", out_dir)
        return key, path

    def test_produces_valid_json_under_size_limit(self):
        key, path = self._run_and_export()

        self.assertTrue(path.exists())
        self.assertLess(path.stat().st_size, export.MAX_FILE_BYTES)

        payload = json.loads(path.read_text())
        self.assertEqual(payload["cache_key"], key)
        self.assertEqual(payload["iso"], "ERCOT")
        self.assertEqual(sorted(payload["years"]), ["2026", "2027", "2028"])

    def test_year_summary_has_expected_fields(self):
        _, path = self._run_and_export()

        summary = json.loads(path.read_text())["years"]["2026"]
        for field in (
            "generation_twh",
            "emissions_mt",
            "nox_tonnes",
            "so2_tonnes",
            "avg_price",
            "peak_price",
            "curtailment_twh",
            "capacity_gw",
            "storage_cycles",
        ):
            self.assertIn(field, summary)

        # The fake solve returns a flat $30/MWh price in every zone-hour.
        self.assertEqual(summary["avg_price"], 30.0)
        self.assertEqual(summary["peak_price"], 30.0)

    def test_curtailment_never_negative(self):
        _, path = self._run_and_export()

        for summary in json.loads(path.read_text())["years"].values():
            self.assertGreaterEqual(summary["curtailment_twh"], 0.0)

    def test_generation_broken_down_by_fuel(self):
        _, path = self._run_and_export()

        summary = json.loads(path.read_text())["years"]["2026"]
        # The ERCOT fleet carries every thermal fuel type, and the export
        # folds in zonal wind and solar.
        for fuel in ("gas_cc", "gas_ct", "coal", "nuclear", "wind", "solar"):
            self.assertIn(fuel, summary["generation_twh"])
            self.assertIn(fuel, summary["capacity_gw"])


if __name__ == "__main__":
    unittest.main()
