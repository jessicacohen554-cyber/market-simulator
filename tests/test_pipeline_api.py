"""Contract tests for the public orchestration facade
(:mod:`market_sim.pipeline.api`).

The facade is the supported programmatic entry point for scripts and
library fan-outs (refactor-consolidation plan §5, orchestrator-unification
lane). These tests pin its contract so a later decomposition of
``runner.run_scenario_iso`` cannot silently change it:

* **Signature** — ``run_scenario(config, iso) -> str`` and
  ``run_pair(pair) -> str``.
* **Picklability** — ``run_pair`` is a module-level function that pickles
  by reference (the ``ProcessPoolExecutor`` worker contract used by
  sweeps / ensembles / PB-5 slices).
* **Patch transparency** — the facade delegates to
  ``market_sim.runner.run_scenario_iso`` resolved at *call* time, so
  existing test patches of the runner attribute intercept facade calls.
* **On-disk layout** — a completed run caches each year at
  ``results/{iso}/{cache_key}/year_{year}.parquet`` with ``config.yaml``
  written alongside and a per-year ``evolution_{year}.json`` ledger.
* **Re-exports** — ``market_sim.runner`` and the ``market_sim.pipeline``
  package both re-export the facade names.

The dispatch LP is mocked (the ``test_runner.py`` fixture pattern): the
layout test exercises the real orchestration/caching path without the
cost of a full-year solve.
"""

import inspect
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

import market_sim.pipeline
import market_sim.pipeline.api as api
from market_sim import runner
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.dispatch import DispatchResult
from market_sim.pipeline import commitment as pipeline_commitment
from market_sim.pipeline import solve as pipeline_solve
from market_sim.results import cache


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


class _FakeDispatchModel:
    """Stand-in for the build-once / re-cost ``DispatchModel`` (P0/P1 path)."""

    def __init__(self, fleet, demand, **kwargs):
        self._fleet = fleet
        self._demand = demand

    def solve(self, mc=None, **kwargs):
        return _fake_solve(self._fleet, self._demand)


class TestFacadeSignature(unittest.TestCase):
    """The public surface keeps its exact signatures."""

    def test_run_scenario_signature(self):
        sig = inspect.signature(api.run_scenario)
        self.assertEqual(list(sig.parameters), ["config", "iso"])
        self.assertEqual(sig.return_annotation, "str")

    def test_run_pair_signature(self):
        sig = inspect.signature(api.run_pair)
        self.assertEqual(list(sig.parameters), ["pair"])
        self.assertEqual(sig.return_annotation, "str")


class TestRunPairPicklable(unittest.TestCase):
    """``run_pair`` ships to process-pool workers by reference."""

    def test_pickle_round_trip_is_identity(self):
        clone = pickle.loads(pickle.dumps(api.run_pair))
        self.assertIs(clone, api.run_pair)

    def test_module_level_qualname(self):
        # Pickle-by-reference requires a top-level function at a stable path.
        self.assertEqual(api.run_pair.__module__, "market_sim.pipeline.api")
        self.assertEqual(api.run_pair.__qualname__, "run_pair")


class TestPatchTransparency(unittest.TestCase):
    """Patches of ``runner.run_scenario_iso`` intercept facade calls."""

    def test_run_scenario_delegates_at_call_time(self):
        config = ScenarioConfig(iso="ERCOT")
        with patch(
            "market_sim.runner.run_scenario_iso", return_value="PATCHED-KEY"
        ) as mocked:
            self.assertEqual(api.run_scenario(config, "ERCOT"), "PATCHED-KEY")
        mocked.assert_called_once_with(config, "ERCOT")

    def test_run_pair_delegates_at_call_time(self):
        config = ScenarioConfig(iso="ERCOT")
        with patch(
            "market_sim.runner.run_scenario_iso", return_value="PATCHED-KEY"
        ) as mocked:
            self.assertEqual(api.run_pair((config, "ERCOT")), "PATCHED-KEY")
        mocked.assert_called_once_with(config, "ERCOT")


class TestReExports(unittest.TestCase):
    """Both the runner module and the pipeline package re-export the facade."""

    def test_runner_reexports(self):
        self.assertIs(runner.run_scenario, api.run_scenario)
        self.assertIs(runner.run_pair, api.run_pair)

    def test_pipeline_package_reexports(self):
        self.assertIs(market_sim.pipeline.run_scenario, api.run_scenario)
        self.assertIs(market_sim.pipeline.run_pair, api.run_pair)
        self.assertIn("run_scenario", market_sim.pipeline.__all__)
        self.assertIn("run_pair", market_sim.pipeline.__all__)


class TestCacheLayoutContract(unittest.TestCase):
    """A completed run produces the frozen on-disk layout.

    ``results/{iso}/{cache_key}/year_{year}.parquet`` + ``config.yaml`` +
    ``evolution_{year}.json`` — the layout every downstream reader
    (export, scoring, hindcast ledgers, PB-5 assembly) binds to.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name)

    def tearDown(self):
        cache.CACHE_ROOT = self._original_root
        self._tmp.cleanup()

    def test_layout_via_facade(self):
        config = ScenarioConfig(iso="ERCOT")
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
        ):
            key = api.run_scenario(config, "ERCOT")

        self.assertIsInstance(key, str)
        run_dir = cache.CACHE_ROOT / "ERCOT" / key
        self.assertTrue(
            (run_dir / "year_2026.parquet").is_file(),
            "year_{year}.parquet missing from the run directory",
        )
        self.assertTrue(
            (run_dir / "config.yaml").is_file(),
            "config.yaml missing alongside the cached years",
        )
        self.assertTrue(
            (run_dir / "evolution_2026.json").is_file(),
            "evolution_{year}.json ledger missing from the run directory",
        )


if __name__ == "__main__":
    unittest.main()
