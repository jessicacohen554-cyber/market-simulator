"""Fail-closed gates on every path that rebuilds a solve recipe from meta.json.

A committed bundle's ``meta.json`` is the authoritative snapshot of its
``solve_and_persist`` kwargs, so any path that reconstructs kwargs from one is a
solve entry point in its own right. Two program-level gates have to reach every
such path, and neither lives inside ``solve_and_persist``:

* ``enforce_legacy_p2_kwargs`` — the ARCHIVED P2 commitment pass (audit row O5).
  The CLI gate ``_enforce_legacy_p2_gate`` only sees *parsed CLI args*, so a
  bundle recorded with ``commitment=true`` re-armed P2 invisibly on replay. That
  is how P2 crossed three NEISO keeper generations with no operator decision
  anywhere in the chain.
* ``enforce_holdout_year_gate`` — rule 22 ``[R-HOLDOUT]``, freeze-first and
  fail-closed.

Session neiso-99 closed the O5 seam at ``run_replay_bundle`` and
``replay_keeper.main`` but shipped no regression test, and left the third path
(``knob_jacobian.solve_year``, which calls ``solve_and_persist`` directly from a
free ``--year``) gated by neither. These tests pin all three paths and the gate's
own semantics. No LP is solved: every case is asserted at the refusal, and
``solve_and_persist`` is asserted never to be reached.
"""

import inspect
import json
import unittest
from pathlib import Path
from unittest import mock

from scripts import knob_jacobian as kj
from scripts import replay_keeper as rk
from scripts import run_calibration_full as rcf


class TestLegacyP2KwargGate(unittest.TestCase):
    """``enforce_legacy_p2_kwargs`` semantics on a RECONSTRUCTED recipe."""

    def test_production_recipe_passes(self):
        """The production basis (P0/P1) is untouched by the gate."""
        rcf.enforce_legacy_p2_kwargs({"commitment": False, "iso": "NEISO"}, False)

    def test_every_archived_kwarg_is_gated(self):
        """Each name in LEGACY_P2_KWARGS hard-fails on its own."""
        self.assertTrue(rcf.LEGACY_P2_KWARGS, "the gated-kwarg tuple went empty")
        for name in rcf.LEGACY_P2_KWARGS:
            with self.subTest(kwarg=name):
                with self.assertRaises(SystemExit) as cm:
                    rcf.enforce_legacy_p2_kwargs({name: True}, False)
                self.assertIn(name, str(cm.exception))
                self.assertIn("--enable-legacy-p2", str(cm.exception))

    def test_unlock_permits_the_archived_pass(self):
        """``--enable-legacy-p2`` is the deliberate last-resort escape."""
        rcf.enforce_legacy_p2_kwargs({"commitment": True}, True)

    def test_failure_is_hard_not_a_silent_rewrite(self):
        """The recipe is never quietly rewritten (miso-50..53 regression class)."""
        kwargs = {"commitment": True, "iso": "NEISO"}
        with self.assertRaises(SystemExit):
            rcf.enforce_legacy_p2_kwargs(kwargs, False)
        self.assertTrue(
            kwargs["commitment"],
            "the gate mutated the recipe instead of refusing it — a replay that "
            "silently solves something other than the bundle it names",
        )


class TestEveryReplayPathIsGated(unittest.TestCase):
    """All three recipe-reconstruction paths call the archived-P2 gate."""

    def test_run_replay_bundle_calls_the_gate(self):
        src = inspect.getsource(rcf.run_replay_bundle)
        self.assertIn("enforce_legacy_p2_kwargs", src)

    def test_replay_keeper_main_calls_the_gate(self):
        src = inspect.getsource(rk.main)
        self.assertIn("enforce_legacy_p2_kwargs", src)

    def test_knob_jacobian_solve_year_calls_both_gates(self):
        src = inspect.getsource(kj.solve_year)
        self.assertIn("enforce_legacy_p2_kwargs", src)
        self.assertIn("enforce_holdout_year_gate", src)


class TestKnobJacobianSolveYearGates(unittest.TestCase):
    """The D-11 diagnostic's own solve path refuses before it reaches an LP."""

    def _run(self, tmp: Path, *, year: int, kwargs: dict, **flags):
        (tmp / "meta.json").write_text(json.dumps({"iso": "NEISO", "hours": 8760}))
        with (
            mock.patch.object(rk, "build_kwargs", return_value=dict(kwargs)),
            mock.patch.object(rcf, "solve_and_persist") as solve,
            mock.patch.object(rcf, "_load_reference", return_value={}),
        ):
            with self.assertRaises(SystemExit) as cm:
                kj.solve_year(tmp, "NEISO", year, {}, tmp / "out", {}, **flags)
            solve.assert_not_called()
        return str(cm.exception)

    def test_out_of_training_year_is_refused(self):
        """``--year 2019`` no longer reaches an LP just because it is an int.

        The locked-test tier is touch-once and the spend freeze is ACTIVE, so
        this must fail closed with neither flag nor marker able to reach it.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            msg = self._run(Path(td), year=2019, kwargs={"commitment": False})
        self.assertIn("2019", msg)

    def test_archived_p2_recipe_is_refused(self):
        """An in-window year still cannot silently re-arm P2 from meta.json."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            msg = self._run(Path(td), year=2024, kwargs={"commitment": True})
        self.assertIn("--enable-legacy-p2", msg)

    def test_production_recipe_in_window_reaches_the_solve(self):
        """The gates refuse only what they name — the normal path is unchanged."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "meta.json").write_text(json.dumps({"iso": "NEISO", "hours": 8760}))
            with (
                mock.patch.object(
                    rk, "build_kwargs", return_value={"commitment": False}
                ),
                mock.patch.object(
                    rcf, "solve_and_persist", return_value=tmp / "solved"
                ) as solve,
                mock.patch.object(rcf, "_load_reference", return_value={}),
            ):
                out = kj.solve_year(tmp, "NEISO", 2024, {}, tmp / "out", {})
            solve.assert_called_once()
            self.assertEqual(out, tmp / "solved")


if __name__ == "__main__":
    unittest.main()
