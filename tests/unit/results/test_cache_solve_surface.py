"""Tests for the solve-surface sidecar and its addressing effect (capx D79).

**What a bundle owes after D79.** ``results/<ISO>/<key>/`` carries
``solve_surface.json`` beside ``config.yaml``, so ``key = f(config, moved rows,
epochs)`` is reproducible from the bundle alone — the property every re-key
event so far has eroded. And the addressing half: a bundle solved on surface S1
is NOT handed to a config running on S2, and IS addressed again once S2 reverts
to S1 (the same model, so the same key, by construction of the frozen-hash drop).

The surface is moved by mutating a registry table in place and restoring it in
``finally``; ``solve_surface.reset_caches()`` drops the memoized views on both
sides so the test measures the rule, not a stale cache.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from market_sim.config import constants
from market_sim.config import solve_surface as S
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.dispatch import DispatchResult
from market_sim.results import cache


def _make_result() -> DispatchResult:
    """A minimal solved result — the sidecar does not read any of it."""
    rng = np.random.default_rng(0)
    return DispatchResult(
        dispatch=rng.random((2, 24)),
        wind_dispatched=rng.random((1, 24)),
        solar_dispatched=rng.random((1, 24)),
        slack=np.zeros((1, 24)),
        dump=np.zeros((1, 24)),
        prices=rng.random((1, 24)) * 50.0,
        storage_charge=None,
        storage_discharge=None,
        storage_soc=None,
        flows=None,
        objective_value=1.0,
        status="Optimal",
        build_time=0.1,
        solve_time=0.1,
    )


class SolveSurfaceSidecarTest(unittest.TestCase):
    """``save_result`` writes the stamp, and it agrees with ``config.yaml``."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name)

    def tearDown(self):
        cache.CACHE_ROOT = self._root
        self._tmp.cleanup()
        S.reset_caches()

    def _save(self, config: ScenarioConfig, year: int = 2030) -> Path:
        path = cache.save_result(_make_result(), config, iso=config.iso, year=year)
        return path.parent

    def test_sidecar_is_written_beside_the_config(self):
        config = ScenarioConfig(iso="ERCOT", carbon_price=40.0)
        bundle = self._save(config)
        sidecar = bundle / "solve_surface.json"
        self.assertTrue(sidecar.exists())
        self.assertTrue((bundle / "config.yaml").exists())

        stamp = json.loads(sidecar.read_text())
        self.assertEqual(stamp["iso"], "ERCOT")
        self.assertEqual(stamp["moved"], {})
        self.assertEqual(stamp["epochs"], [])
        self.assertEqual(stamp["rows"], len(S.surface_rows("ERCOT")))

    def test_sidecar_and_config_agree(self):
        """The stamp describes the surface the STORED config would hash under."""
        config = ScenarioConfig(iso="PJM")
        bundle = self._save(config)
        stored = ScenarioConfig.from_yaml(bundle / "config.yaml")
        stamp = json.loads((bundle / "solve_surface.json").read_text())
        self.assertEqual(stored.cache_key(), config.cache_key())
        self.assertEqual(stamp, S.surface_stamp(stored.iso, stored))

    def test_sidecar_is_rewritten_when_the_surface_moves(self):
        """Never `if not exists`: the stamp must date the bytes on disk."""
        config = ScenarioConfig(iso="MISO")
        first = json.loads((self._save(config) / "solve_surface.json").read_text())
        table = constants.DEMAND_GROWTH_RATES
        original = table["MISO"]
        try:
            table["MISO"] = {"sentinel": 1.0}
            S.reset_caches()
            second = json.loads((self._save(config) / "solve_surface.json").read_text())
        finally:
            table["MISO"] = original
            S.reset_caches()
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])
        self.assertEqual(list(second["moved"]), ["DEMAND_GROWTH_RATES"])

    def test_a_bundle_solved_on_S1_is_not_addressed_on_S2(self):
        """The addressing half — and its inverse, which is the (b′-1) promise."""
        config = ScenarioConfig(iso="MISO")
        key_s1 = config.cache_key()
        self._save(config, year=2030)
        self.assertTrue(cache.is_cached("MISO", key_s1, 2030))

        table = constants.DEMAND_GROWTH_RATES
        original = table["MISO"]
        try:
            table["MISO"] = {"sentinel": 1.0}
            S.reset_caches()
            key_s2 = config.cache_key()
            self.assertNotEqual(key_s2, key_s1)
            self.assertFalse(cache.is_cached("MISO", key_s2, 2030))
        finally:
            table["MISO"] = original
            S.reset_caches()

        # Reverted: the same model, so the same key, so the bundle is addressed
        # again. A re-declaration would have been needed under a naive scheme.
        self.assertEqual(config.cache_key(), key_s1)
        self.assertTrue(cache.is_cached("MISO", config.cache_key(), 2030))

    def test_another_isos_key_is_untouched_by_a_MISO_row(self):
        """Rule 25 [R-ISO-SCOPE]: a repair to one ISO's row is that ISO's."""
        other = ScenarioConfig(iso="ERCOT")
        before = other.cache_key()
        table = constants.DEMAND_GROWTH_RATES
        original = table["MISO"]
        try:
            table["MISO"] = {"sentinel": 1.0}
            S.reset_caches()
            self.assertEqual(other.cache_key(), before)
        finally:
            table["MISO"] = original
            S.reset_caches()


if __name__ == "__main__":
    unittest.main()
