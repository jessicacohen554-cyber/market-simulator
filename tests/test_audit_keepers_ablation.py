"""Tests for audit_keepers E9 (ablation-twin link integrity, CLAUDE.md rule 20).

The zero-forcing ablation twin is OPTIONAL as of the 2026-07-14 owner amendment
to rule 20 (keepers no longer build or register one). E9 now only checks that a
DECLARED ``ablation_twin`` sidecar link resolves to a registered run — absence of
a twin is OK. Exercises the pure ``ablation_twin_finding`` helper, which decides
OK / FAIL for one keeper given its sidecar and a registry dir, so it is testable
without the live registry.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "audit_keepers", str(_REPO / "scripts" / "audit_keepers.py")
)
ak = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ak)


class TestAblationTwinFinding(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.reg = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, run_id, obj=None):
        (self.reg / f"{run_id}.json").write_text(json.dumps(obj or {}))

    def test_registered_twin_passes(self):
        # A resolvable declared link is still OK (existing twins stay valid).
        self._write("k-ablation")
        level, _ = ak.ablation_twin_finding(
            "new-keeper", {"ablation_twin": "k-ablation"}, self.reg
        )
        self.assertEqual(level, "OK")

    def test_missing_twin_is_ok(self):
        # No ``ablation_twin`` link: OK — the twin is optional (rule 20 owner
        # amendment 2026-07-14). Was a FAIL/WARN before the amendment.
        level, msg = ak.ablation_twin_finding("2099-brand-new-keeper", {}, self.reg)
        self.assertEqual(level, "OK")
        self.assertIn("not required", msg.lower())

    def test_dangling_twin_link_fails(self):
        # A DECLARED-but-broken link still FAILs: the sidecar asserts a twin that
        # does not resolve (a typo / an unregistered twin) — a data-integrity bug.
        level, msg = ak.ablation_twin_finding(
            "new-keeper", {"ablation_twin": "does-not-exist"}, self.reg
        )
        self.assertEqual(level, "FAIL")
        self.assertIn("does-not-exist", msg)


if __name__ == "__main__":
    unittest.main()
