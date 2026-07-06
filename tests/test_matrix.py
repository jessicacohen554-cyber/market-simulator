"""Tests for the AEO/IPM-style deterministic scenario matrix (PB-0 / PB-1.1).

The dispatch LP is mocked (mirrors test_runner.py's pattern) so these tests
exercise matrix orchestration -- case expansion, the concurrency cap, cache
population, and the output bundle -- without solving a real model.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from market_sim import matrix, runner
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from market_sim.results import cache
from tests.test_runner import _FakeDispatchModel, _fake_solve
from market_sim.pipeline import commitment as pipeline_commitment
from market_sim.pipeline import solve as pipeline_solve


class MatrixTestBase(unittest.TestCase):
    """Base fixture redirecting the cache root to a temp directory."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name) / "results"
        _FakeDispatchModel.n_solves = 0

    def tearDown(self):
        cache.CACHE_ROOT = self._original_root
        self._tmp.cleanup()


class TestMatrixConfigs(unittest.TestCase):
    """matrix_configs guards forecast-only and delegates to case_configs."""

    def test_expands_cases_onto_base_config(self):
        base = ScenarioConfig(iso="ERCOT", mode="forecast", carbon_price=3.0)
        sweep_def = SweepDefinition(
            cases={"REF": {}, "GAS-LO": {"gas_price_path": "low"}}
        )
        configs = matrix.matrix_configs(base, sweep_def)
        self.assertEqual(list(configs.keys()), ["REF", "GAS-LO"])
        self.assertEqual(configs["GAS-LO"].gas_price_path, "low")
        self.assertEqual(configs["GAS-LO"].carbon_price, 3.0)

    def test_rejects_backcast_base_config(self):
        base = ScenarioConfig(iso="ERCOT", mode="backcast")
        sweep_def = SweepDefinition(cases={"REF": {}})
        with self.assertRaises(ValueError):
            matrix.matrix_configs(base, sweep_def)


class TestRunMatrix(MatrixTestBase):
    """run_matrix solves every case and caps concurrency at 2 (plan §1.3)."""

    def test_two_cases_create_two_cache_dirs(self):
        base = ScenarioConfig(iso="ERCOT", mode="forecast")
        configs = {
            "REF": base,
            "GAS-HI": base.with_overrides(gas_price_path="high"),
        }
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
        ):
            members = matrix.run_matrix(configs, "ERCOT", workers=1)

        self.assertEqual(set(members.keys()), {"REF", "GAS-HI"})
        self.assertEqual(len(set(members.values())), 2)
        cache_dirs = [d for d in (cache.CACHE_ROOT / "ERCOT").iterdir() if d.is_dir()]
        self.assertEqual(len(cache_dirs), 2)

    def test_workers_hard_capped_at_two(self):
        base = ScenarioConfig(iso="ERCOT", mode="forecast")
        configs = {"REF": base}
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
            patch.object(matrix, "ProcessPoolExecutor") as mock_pool,
        ):
            matrix.run_matrix(configs, "ERCOT", workers=8)
            mock_pool.assert_called_once_with(max_workers=matrix.MAX_CONCURRENT_CASES)

    def test_empty_configs_rejected(self):
        with self.assertRaises(ValueError):
            matrix.run_matrix({}, "ERCOT")


class TestBuildMatrixFrameAndEnvelope(MatrixTestBase):
    """The trajectory table and envelope are built from cached per-case runs."""

    def test_frame_and_envelope_from_two_cases(self):
        base = ScenarioConfig(iso="ERCOT", mode="forecast")
        configs = {
            "REF": base,
            "GAS-HI": base.with_overrides(gas_price_path="high"),
        }
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
        ):
            members = matrix.run_matrix(configs, "ERCOT", workers=1)

        with patch.object(matrix, "END_YEAR", 2026):
            df = matrix.build_matrix_frame("ERCOT", members)
            envelope = matrix.compute_envelope(df)

        self.assertEqual(set(df["case"]), {"REF", "GAS-HI"})
        self.assertEqual(set(df["year"]), {2026})
        self.assertTrue((df["label"] == matrix.LABEL).all())

        self.assertEqual(len(envelope), 1)
        row = envelope.iloc[0]
        self.assertEqual(row["year"], 2026)
        self.assertLessEqual(row["min_mt"], row["max_mt"])
        self.assertEqual(row["label"], matrix.LABEL)

    def test_empty_members_yields_empty_frame_and_envelope(self):
        df = matrix.build_matrix_frame("ERCOT", {})
        self.assertTrue(df.empty)
        envelope = matrix.compute_envelope(df)
        self.assertTrue(envelope.empty)


class TestWriteMatrixOutputs(MatrixTestBase):
    """The output bundle carries the deterministic-scenario-range label everywhere."""

    def test_bundle_written_and_labeled(self):
        base = ScenarioConfig(iso="ERCOT", mode="forecast")
        configs = {
            "REF": base,
            "GAS-HI": base.with_overrides(gas_price_path="high"),
        }
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
        ):
            members = matrix.run_matrix(configs, "ERCOT", workers=1)

        out_dir = Path(self._tmp.name) / "matrix_out"
        with patch.object(matrix, "END_YEAR", 2026):
            written = matrix.write_matrix_outputs(
                "ERCOT", base, "configs/scenario_matrix.yaml", members, out_dir
            )

        self.assertEqual(written, out_dir)
        for name in ("matrix.parquet", "envelope.parquet", "summary.md", "meta.json"):
            self.assertTrue((out_dir / name).exists(), name)

        meta = json.loads((out_dir / "meta.json").read_text())
        self.assertEqual(meta["label"], matrix.LABEL)
        self.assertEqual(set(meta["cases"].keys()), {"REF", "GAS-HI"})
        self.assertEqual(meta["years_present"], [2026])

        summary_text = (out_dir / "summary.md").read_text()
        self.assertIn(matrix.LABEL.upper(), summary_text)


class TestMatrixIdFor(unittest.TestCase):
    """matrix_id_for is deterministic and distinguishes base config / matrix file."""

    def test_same_inputs_same_id(self):
        base = ScenarioConfig(iso="ERCOT", mode="forecast")
        id1 = matrix.matrix_id_for("ERCOT", base, "configs/scenario_matrix.yaml")
        id2 = matrix.matrix_id_for("ERCOT", base, "configs/scenario_matrix.yaml")
        self.assertEqual(id1, id2)

    def test_different_base_config_different_id(self):
        base1 = ScenarioConfig(iso="ERCOT", mode="forecast", carbon_price=0.0)
        base2 = ScenarioConfig(iso="ERCOT", mode="forecast", carbon_price=5.0)
        id1 = matrix.matrix_id_for("ERCOT", base1, "configs/scenario_matrix.yaml")
        id2 = matrix.matrix_id_for("ERCOT", base2, "configs/scenario_matrix.yaml")
        self.assertNotEqual(id1, id2)


if __name__ == "__main__":
    unittest.main()
