"""Tests for the PERF-B session 3 adaptive-pass guards in ``run_calibration``.

Charter C-1a (``docs/handoffs/perfb-session2-markup-charter-2026-09.md`` §2):
the ercot-221 adaptive-expectation pass is skipped when its P1 storage
discharge cost is ELEMENTWISE IDENTICAL to the one pass 1 solved with — an
exact equality, never a tolerance, because the claim is identity of the LP.
The helpers live in the 6k-line orchestrator; they are exec'd out of its AST
here so the test does not pay the module import.
"""

from __future__ import annotations

import ast
import unittest

import numpy as np

from tests.helpers import REPO_ROOT

ORCH = REPO_ROOT / "scripts" / "run_calibration.py"


def _load_helper(name: str):
    tree = ast.parse(ORCH.read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    ns = {"np": np}
    exec(compile(ast.Module([fn], type_ignores=[]), str(ORCH), "exec"), ns)
    return ns[name]


class TestP1StorageCostIdentical(unittest.TestCase):
    """The exact-equality guard."""

    @classmethod
    def setUpClass(cls):
        cls.guard = staticmethod(_load_helper("_p1_storage_cost_identical"))

    def setUp(self):
        self.vom = np.array([2.0, 3.5, 0.0])
        self.T = 48
        self.kwargs = {"storage_discharge_cost": self.vom}

    def test_max_vom_floor_equal_to_vom_everywhere_is_identical(self):
        floor = np.zeros(self.T)
        cand = np.maximum(self.vom[:, None], floor[None, :])
        self.assertTrue(self.guard(cand, None, self.kwargs))

    def test_floor_below_fleet_max_vom_but_above_one_unit_is_not_identical(self):
        # The log's counter compares the floor against vom.max() (3.5); a floor
        # of 1.0 reads "0 window hours above vom" there yet CHANGES the unit
        # whose vom is 0.0 — the guard must catch it (charter ⚠ on C-1a).
        floor = np.zeros(self.T)
        floor[18] = 1.0
        cand = np.maximum(self.vom[:, None], floor[None, :])
        self.assertGreater(float(self.vom.max()), 1.0)
        self.assertFalse(self.guard(cand, None, self.kwargs))

    def test_pass1_override_is_the_reference_when_present(self):
        override = np.full((3, self.T), 7.0)
        self.assertTrue(self.guard(np.full((3, self.T), 7.0), override, self.kwargs))
        self.assertFalse(self.guard(np.full((3, self.T), 7.0), None, self.kwargs))

    def test_no_tolerance(self):
        cand = np.broadcast_to(self.vom[:, None], (3, self.T)).copy()
        cand[1, 5] += 1e-12
        self.assertFalse(self.guard(cand, None, self.kwargs))

    def test_scalar_default_and_missing_key(self):
        self.assertTrue(self.guard(np.zeros((3, self.T)), None, {}))
        self.assertTrue(
            self.guard(np.full((3, self.T), 4.0), None, {"storage_discharge_cost": 4.0})
        )
        self.assertFalse(
            self.guard(np.full((3, self.T), 4.0), None, {"storage_discharge_cost": 5.0})
        )

    def test_shape_mismatch_is_not_identical(self):
        self.assertFalse(
            self.guard(
                np.zeros((2, self.T)), None, {"storage_discharge_cost": self.vom}
            )
        )

    def test_nan_is_never_identical(self):
        cand = np.broadcast_to(self.vom[:, None], (3, self.T)).copy()
        cand[0, 0] = np.nan
        self.assertFalse(self.guard(cand, None, self.kwargs))


class TestPass2Wiring(unittest.TestCase):
    """The guard gates the ercot-221 pass-2 call and the decision is logged."""

    def test_pass_two_is_conditional_on_the_guard(self):
        text = ORCH.read_text()
        i_guard = text.index("_pass2_identical = _p1_storage_cost_identical(")
        i_if = text.index("if not _pass2_identical:", i_guard)
        i_call = text.index("p1_storage_discharge_cost=_adaptive_cost,", i_if)
        # guard -> conditional -> the pass-2 run_energy_solve call, in order.
        self.assertLess(i_guard, i_if)
        self.assertLess(i_if, i_call)
        self.assertIn("pass 2 SKIPPED, pass 1 IS the scored pass (C-1a)", text)

    def test_the_sidecar_is_recorded_before_the_conditional(self):
        text = ORCH.read_text()
        i_side = text.index('ercot221_adaptive = {\n            "s_model": _s_m,')
        i_if = text.index("if not _pass2_identical:")
        self.assertLess(i_side, i_if)


if __name__ == "__main__":
    unittest.main()
