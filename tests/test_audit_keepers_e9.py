"""Tests for audit_keepers E9 — the D-3 ablation-twin keeper check (rule 21).

Exercises the pure decision helpers (loaded by path) on a temporary registry:
``_e9_finding`` (warn/fail/ok logic + grandfather) and
``_any_keeper_has_ablation_twin`` (the self-activating strict switch).
"""

import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

_REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "audit_keepers", str(_REPO / "scripts" / "audit_keepers.py")
)
ak = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ak)
cv = ak.cv


class _TmpRegistry:
    """Point cv.REGISTRY_DIR at a temp dir with the given sidecars."""

    def __init__(self, sidecars):
        self._sidecars = sidecars
        self._tmp = TemporaryDirectory()
        self._orig = cv.REGISTRY_DIR

    def __enter__(self):
        d = Path(self._tmp.name)
        cv.REGISTRY_DIR = d
        for rid, body in self._sidecars.items():
            (d / f"{rid}.json").write_text(json.dumps(body))
        return d

    def __exit__(self, *a):
        cv.REGISTRY_DIR = self._orig
        self._tmp.cleanup()


class E9FindingTest(unittest.TestCase):
    def test_missing_twin_warns_when_grandfathered(self):
        with _TmpRegistry({}):
            level, _ = ak._e9_finding({"iso": "ERCOT"}, enforce_e9=False)
        self.assertEqual(level, "WARN")

    def test_missing_twin_fails_when_enforced(self):
        with _TmpRegistry({}):
            level, _ = ak._e9_finding({"iso": "ERCOT"}, enforce_e9=True)
        self.assertEqual(level, "FAIL")

    def test_dangling_twin_always_fails(self):
        with _TmpRegistry({}):  # twin sidecar absent
            level, msg = ak._e9_finding(
                {"ablation_twin": "nope-ablation"}, enforce_e9=False
            )
        self.assertEqual(level, "FAIL")
        self.assertIn("nope-ablation", msg)

    def test_registered_twin_ok(self):
        with _TmpRegistry({"k-ablation": {"iso": "ERCOT"}}):
            level, _ = ak._e9_finding({"ablation_twin": "k-ablation"}, enforce_e9=True)
        self.assertEqual(level, "OK")


class E9SwitchTest(unittest.TestCase):
    def test_switch_off_when_no_keeper_has_twin(self):
        with _TmpRegistry({"a": {"iso": "ERCOT"}, "b": {"iso": "PJM"}}):
            self.assertFalse(ak._any_keeper_has_ablation_twin(["a", "b"]))

    def test_switch_flips_on_first_twin(self):
        with _TmpRegistry(
            {"a": {"iso": "ERCOT", "ablation_twin": "a-ablation"}, "b": {"iso": "PJM"}}
        ):
            self.assertTrue(ak._any_keeper_has_ablation_twin(["a", "b"]))

    def test_blank_twin_field_does_not_flip(self):
        with _TmpRegistry({"a": {"iso": "ERCOT", "ablation_twin": "  "}}):
            self.assertFalse(ak._any_keeper_has_ablation_twin(["a"]))


if __name__ == "__main__":
    unittest.main()
