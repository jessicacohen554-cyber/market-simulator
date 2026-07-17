"""Tests for scenario export to compact frontend JSON.

The dispatch LP is mocked: ``run_energy_solve`` (the shared P0/P1 solve core
every ISO-year goes through, orchestrator-unification Stage 3) is patched to
return a synthetic result, so a scenario is run and cached without the cost
of solving, then exported. G-44: this used to patch the module-level
``solve_dispatch`` name, which Stage 3 made dead for the default (no
commitment-screen) config exercised here — ``runner.py`` only calls
``solve_dispatch`` directly inside the opt-in legacy P2 commitment-screen
branch (``commitment_enabled``/``ercot_as_aware_commitment``/
``caiso_ra_mustoffer``, all default-off), so the old patch silently stopped
intercepting anything and every "mocked" run was actually solving a real LP.
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
from market_sim.pipeline import EnergySolveResult
from market_sim.results import cache, export
from market_sim.results.outputs import FleetContext


def _fake_dispatch_result(fleet_arrays, demand):
    """Return a synthetic ``DispatchResult`` sized to the fleet and demand."""
    n_gen = fleet_arrays.n_gen
    n_zones, T = demand.shape
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


def _fake_energy_solve(
    fleet, fleet_arrays, demand, mc_base, dispatch_kwargs, config, **kwargs
):
    """Return a synthetic ``EnergySolveResult`` in place of the real P0/P1 solve."""
    result = _fake_dispatch_result(fleet_arrays, demand)
    return EnergySolveResult(
        r0=result,
        p1=result,
        mc_bid=mc_base,
        markup=np.zeros_like(mc_base),
        p1_fleet_arrays=fleet_arrays,
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


class TestSummarizeYearCesMetrics(unittest.TestCase):
    """W2-B additive metrics: ``clean_share`` and ``negative_price_hours``.

    Both keys are strictly additive — every pre-W2-B key keeps its exact
    value — and ``clean_share`` uses the reporting-side crediting rule so a
    CES-off config (or no config at all) still reports the physical clean
    share.
    """

    def _result(self, hours=24):
        n_zones = 2
        prices = np.full((n_zones, hours), 30.0)
        prices[0, :6] = -5.0  # 6 negative hours in zone 0 only
        return DispatchResult(
            dispatch=np.vstack(
                [np.full(hours, 10.0), np.full(hours, 40.0)]
            ),  # nuclear, gas_cc
            wind_dispatched=np.full((n_zones, hours), 5.0),
            solar_dispatched=np.zeros((n_zones, hours)),
            slack=np.zeros((n_zones, hours)),
            dump=np.zeros((n_zones, hours)),
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

    def _context(self):
        return FleetContext(
            fuel_types=["nuclear", "gas_cc"],
            pmax_mw=[100.0, 100.0],
            emission_rate=[0.0, 0.37],
            efficiency_bins=["default", "h_class"],
            heat_rates=[10.0, 6.4],
            zones=["A", "B"],
            unit_ids=["G1", "G2"],
            wind_cap_mw=50.0,
            solar_cap_mw=0.0,
            wind_potential_mwh=300.0,
            solar_potential_mwh=0.0,
            storage_energy_cap_mwh=0.0,
        )

    def test_negative_price_hours_zone_averaged(self):
        summary = export._summarize_year(self._result(), self._context())
        # 6 negative zone-hours over 2 zones -> 3.0 hours per zone.
        self.assertEqual(summary["negative_price_hours"], 3.0)

    def test_clean_share_without_config_uses_default_crediting(self):
        summary = export._summarize_year(self._result(), self._context())
        # nuclear 240 MWh + wind 240 MWh credited; total 240 + 960 + 240.
        self.assertAlmostEqual(summary["clean_share"], 480.0 / 1440.0, places=4)

    def test_clean_share_reports_bau_physical_share_when_ces_disabled(self):
        config = ScenarioConfig()  # federal_ces_enabled=False
        summary = export._summarize_year(self._result(), self._context(), config)
        self.assertGreater(summary["clean_share"], 0.0)
        self.assertAlmostEqual(summary["clean_share"], 480.0 / 1440.0, places=4)

    def test_clean_share_follows_config_crediting_mode(self):
        config = ScenarioConfig(federal_ces_crediting="cesa_ci")
        summary = export._summarize_year(self._result(), self._context(), config)
        # cesa_ci also credits the efficient unabated CCGT (0.37 t/MWh):
        # + 960 MWh x (1 - 0.37/0.82).
        expected = (480.0 + 960.0 * (1.0 - 0.37 / 0.82)) / 1440.0
        self.assertAlmostEqual(summary["clean_share"], expected, places=4)

    def test_existing_keys_unchanged_and_json_serializable(self):
        summary = export._summarize_year(self._result(), self._context())
        for field in (
            "generation_twh",
            "emissions_mt",
            "avg_price",
            "peak_price",
            "curtailment_twh",
            "capacity_gw",
            "storage_cycles",
        ):
            self.assertIn(field, summary)
        # The export path json.dumps the summary; numpy scalars would break it.
        json.dumps(summary)

    def test_zero_generation_clean_share_is_zero(self):
        result = self._result()
        result.dispatch = np.zeros_like(result.dispatch)
        result.wind_dispatched = np.zeros_like(result.wind_dispatched)
        summary = export._summarize_year(result, self._context())
        self.assertEqual(summary["clean_share"], 0.0)


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
            patch.object(runner, "run_energy_solve", side_effect=_fake_energy_solve),
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
