"""Tests for the shared, worker-capped member fan-out (``pipeline/members.py``).

``pipeline.members`` is the single home for the ``(config, iso)`` pool that
``runner.run_sweep``, ``ensemble._run_configs`` and ``matrix.run_matrix`` all
reach. What matters here is the *policy* (CLAUDE.md rule 12: the default worker
count is capped, an explicit count is honoured as given) and the *contract*
(cache keys returned in input order; ``run_member_configs`` keys them by member
id). The worker itself (``pipeline.api.run_pair``) is patched out — this file
must never start a real solve.

The pool is exercised at ``workers=1`` (the in-process branch), so no
``ProcessPoolExecutor`` is spawned and the patched worker is actually visible to
the call. The capped-default policy is asserted directly on
:func:`resolve_workers`, which is the branch a multi-process run would take.
"""

from __future__ import annotations

import unittest
from unittest import mock

from market_sim.config.scenarios import ScenarioConfig
from market_sim.pipeline.members import (
    DEFAULT_MEMBER_CAP,
    resolve_workers,
    run_member_configs,
    run_pairs,
)


def _cfg(carbon_price: float) -> ScenarioConfig:
    """Return a distinguishable config (never solved — the worker is patched)."""
    return ScenarioConfig(carbon_price=carbon_price)


class TestResolveWorkers(unittest.TestCase):
    """``workers=None`` is capped (rule 12); an explicit count is honoured."""

    def test_default_capped_at_two(self):
        with mock.patch("market_sim.pipeline.members.cpu_count", return_value=32):
            self.assertEqual(resolve_workers(None, DEFAULT_MEMBER_CAP), 2)

    def test_default_never_below_one(self):
        with mock.patch("market_sim.pipeline.members.cpu_count", return_value=1):
            self.assertEqual(resolve_workers(None, DEFAULT_MEMBER_CAP), 1)

    def test_explicit_workers_honoured_above_cap(self):
        with mock.patch("market_sim.pipeline.members.cpu_count", return_value=32):
            self.assertEqual(resolve_workers(8, DEFAULT_MEMBER_CAP), 8)

    def test_caller_supplied_cap_respected(self):
        with mock.patch("market_sim.pipeline.members.cpu_count", return_value=32):
            self.assertEqual(resolve_workers(None, 4), 4)

    def test_default_cap_is_two(self):
        self.assertEqual(DEFAULT_MEMBER_CAP, 2)


class TestRunPairs(unittest.TestCase):
    """Keys come back one per pair, in the (possibly strided) input order."""

    def setUp(self):
        self.pairs = [(_cfg(0.0), "ERCOT"), (_cfg(50.0), "PJM"), (_cfg(90.0), "MISO")]

    def _run(self, **kwargs) -> list[str]:
        with mock.patch(
            "market_sim.pipeline.members.run_pair",
            side_effect=lambda pair: f"key-{pair[1]}",
        ):
            return run_pairs(self.pairs, workers=1, **kwargs)

    def test_keys_in_pair_order(self):
        self.assertEqual(self._run(), ["key-ERCOT", "key-PJM", "key-MISO"])

    def test_empty_pairs_returns_empty(self):
        self.assertEqual(run_pairs([], workers=1), [])

    def test_stride_selects_subset(self):
        self.assertEqual(self._run(stride=(1, 2)), ["key-PJM"])

    def test_stride_step_must_be_positive(self):
        with self.assertRaises(ValueError):
            run_pairs(self.pairs, workers=1, stride=(0, 0))

    def test_stride_offset_must_be_non_negative(self):
        with self.assertRaises(ValueError):
            run_pairs(self.pairs, workers=1, stride=(-1, 2))


class TestRunMemberConfigs(unittest.TestCase):
    """``{member_id: config}`` in, ``{member_id: cache_key}`` out, in order."""

    def test_keyed_by_member_id_in_input_order(self):
        configs = {2019: _cfg(0.0), 2021: _cfg(50.0)}
        with mock.patch(
            "market_sim.pipeline.members.run_pair",
            side_effect=lambda pair: f"key-{pair[0].carbon_price}",
        ):
            members = run_member_configs(configs, "ercot", workers=1)
        self.assertEqual(members, {2019: "key-0.0", 2021: "key-50.0"})
        self.assertEqual(list(members), [2019, 2021])

    def test_empty_configs_rejected(self):
        with self.assertRaises(ValueError):
            run_member_configs({}, "ERCOT", workers=1)


class TestRunSweepRoutesThroughMembers(unittest.TestCase):
    """``runner.run_sweep`` delegates to the capped helper (the rule-12 fix).

    The former private copy defaulted to an uncapped ``cpu_count - 1``; the
    sweep must now reach ``run_pairs`` and inherit its capped default. Asserted
    by patching the helper, so no config is ever expanded into a solve.
    """

    def test_delegates_with_workers_passed_through(self):
        from market_sim import runner
        from market_sim.config.scenarios import SweepDefinition

        sweep = SweepDefinition(sweep={"carbon_price": [0.0, 50.0]})
        with mock.patch(
            "market_sim.pipeline.members.run_pairs", return_value=["a", "b"]
        ) as fan_out:
            keys = runner.run_sweep(sweep)

        self.assertEqual(keys, ["a", "b"])
        fan_out.assert_called_once()
        # workers is forwarded as given: None => the helper's capped default.
        self.assertIsNone(fan_out.call_args.kwargs["workers"])
        pairs = fan_out.call_args.args[0]
        self.assertEqual([iso for _, iso in pairs], ["ERCOT", "ERCOT"])

    def test_private_run_pair_is_gone(self):
        from market_sim import runner

        self.assertFalse(hasattr(runner, "_run_pair"))


if __name__ == "__main__":
    unittest.main()
