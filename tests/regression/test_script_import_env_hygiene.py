"""Loose ``scripts/`` modules must not pin ``os.environ`` at IMPORT time.

The incident this pins (``docs/FINDING-fast-tier-repair-2026-09.md`` §4b):
``scripts/capture_keeper_goldens.py`` applied its ``DETERMINISM_ENV`` —
``MARKET_SIM_HIGHS_THREADS=1`` above all — at module scope. That is right for
its own CLI process, where the pin must precede any solve. Executed inside
pytest (``tests/scoring/test_golden_manifest_provenance.py`` loads it by path
three times) it leaked into the whole process, and HiGHS then refused every
later LP whose ``threads`` differed from the already-initialized process-global
scheduler:

    Option 'threads' is set to 1 but global scheduler has already been
    initialized to use N threads
    -> run() = kError, model status 'Not Set'
    -> RuntimeError: dispatch LP has no feasible primal solution

203 LP tests in a serial run, 24-79 in whichever xdist worker drew the file —
scheduling-dependent, hence a latent CI red, and the object behind every
inflated local fast-tier count the audit program recorded.

The consuming test was repaired by snapshotting the environment around its
by-path loads. This file pins the *other* half, routed at §7.6 and taken by
PERF-B session 2 (X-4): the scripts themselves no longer pin at import, so a
future by-path load — in a test that has no snapshot guard, or in a tool that
imports the module for one helper (``scripts/knob_jacobian.py`` imports
``replay_keeper.build_kwargs``) — is safe by construction rather than by the
caller remembering.

What is deliberately NOT asserted: that the pins are gone. Each script keeps
its ``DETERMINISM_ENV`` and applies it through ``pin_determinism_env()`` at
every entry that can reach a solve, so the CLI's determinism contract is
unchanged; the tests below check both halves.
"""

from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

from tests.helpers import REPO_ROOT

# The scripts that carry a determinism pin, and the env keys each one applies.
# MARKET_SIM_P1_BASIS_SEED joined both pins when PERF-C S1 gave the same-year
# P1 seed its own env gate (it used to ride inside the cross-year gate) and
# rule 36 [R-YEAR-ISOLATION] defaulted both off (d45d57f9, 2026-09-20).
PINNING_SCRIPTS = {
    "capture_keeper_goldens": {
        "MARKET_SIM_HIGHS_THREADS",
        "MARKET_SIM_WARMSTART",
        "MARKET_SIM_WARMSTART_XYEAR",
        "MARKET_SIM_P1_BASIS_SEED",
    },
    "replay_keeper": {"MARKET_SIM_WARMSTART_XYEAR", "MARKET_SIM_P1_BASIS_SEED"},
}


def _exec_by_path(name: str, path: Path):
    """Execute a script by path with NO environment guard.

    Deliberately unguarded — the guard is what the code under test must make
    unnecessary. The caller restores the environment afterwards so a failure
    here cannot poison the rest of the session.
    """
    spec = importlib.util.spec_from_file_location(f"_envhygiene_{name}", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestNoImportTimeEnvPin(unittest.TestCase):
    """Importing the script leaves ``os.environ`` byte-identical."""

    def _load(self, name: str):
        saved = dict(os.environ)
        try:
            mod = _exec_by_path(name, REPO_ROOT / "scripts" / f"{name}.py")
            after = dict(os.environ)
        finally:
            os.environ.clear()
            os.environ.update(saved)
        return mod, saved, after

    def test_import_does_not_mutate_the_environment(self):
        for name in PINNING_SCRIPTS:
            with self.subTest(script=name):
                _, before, after = self._load(name)
                self.assertEqual(
                    after,
                    before,
                    f"scripts/{name}.py mutated os.environ at import time — "
                    "the leak of FINDING-fast-tier-repair-2026-09 §4b",
                )

    def test_the_determinism_keys_specifically_are_untouched(self):
        # The generic equality above is the real assertion; this one names the
        # keys so a failure reads as the incident rather than as "some env var".
        for name, keys in PINNING_SCRIPTS.items():
            with self.subTest(script=name):
                _, before, after = self._load(name)
                for key in keys:
                    self.assertEqual(
                        after.get(key),
                        before.get(key),
                        f"scripts/{name}.py leaked {key} at import time",
                    )


class TestThePinIsStillReachable(unittest.TestCase):
    """Moving the pin must not weaken either script's determinism contract."""

    def _load_and_pin(self, name: str):
        saved = dict(os.environ)
        try:
            mod = _exec_by_path(name, REPO_ROOT / "scripts" / f"{name}.py")
            self.assertTrue(
                hasattr(mod, "pin_determinism_env"),
                f"scripts/{name}.py lost pin_determinism_env",
            )
            mod.pin_determinism_env()
            applied = dict(os.environ)
        finally:
            os.environ.clear()
            os.environ.update(saved)
        return mod, applied

    def test_pin_determinism_env_applies_the_declared_values(self):
        for name, keys in PINNING_SCRIPTS.items():
            with self.subTest(script=name):
                mod, applied = self._load_and_pin(name)
                self.assertEqual(set(mod.DETERMINISM_ENV), keys)
                for key, value in mod.DETERMINISM_ENV.items():
                    self.assertEqual(applied.get(key), value)

    def test_capture_pins_at_its_solve_site_too(self):
        # capture_one is the solve entry; a programmatic caller that skips
        # main() must still get the pin, so the call has to be in the function
        # AND ahead of its deferred heavy imports (which the old import-time
        # pin preceded).
        import inspect

        mod = _exec_by_path(
            "capture_keeper_goldens",
            REPO_ROOT / "scripts" / "capture_keeper_goldens.py",
        )
        src = inspect.getsource(mod.capture_one)
        self.assertIn("pin_determinism_env()", src)
        self.assertLess(
            src.index("pin_determinism_env()"),
            src.index("from scripts.run_calibration_full import solve_and_persist"),
            "the pin must precede capture_one's deferred solve imports",
        )

    def test_each_main_pins_before_doing_anything(self):
        import inspect

        for name in PINNING_SCRIPTS:
            with self.subTest(script=name):
                mod = _exec_by_path(name, REPO_ROOT / "scripts" / f"{name}.py")
                src = inspect.getsource(mod.main)
                self.assertIn("pin_determinism_env()", src)


if __name__ == "__main__":
    unittest.main()
