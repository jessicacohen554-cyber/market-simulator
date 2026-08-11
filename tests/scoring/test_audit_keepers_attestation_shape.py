"""Tests for audit_keepers E10 (attestation completeness, CLAUDE.md rule 20).

E8 validates only the ``free_parameters`` DOF ledger, so a bundle carrying just
the block ``scripts/build_dof_ledger.py`` writes audits GREEN while
``calibration_verdict`` scores C6 UNATTESTED and forces NOT-YET. That is exactly
what the caiso-188 promotion shipped (``2026-08-09-caiso-188-d1-micseam``): E8
reported "0/0" on an attestation nobody had signed, and the incumbent's C3c
exceptions never carried forward either. E10 closes the hole; caiso-189
(2026-08-11) added it alongside the repair.

Exercises the pure ``attestation_shape_finding`` helper, which decides
OK / WARN / FAIL for one attestation dict, so it is testable without a bundle.
"""

import importlib.util
import unittest

from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "audit_keepers", str(REPO_ROOT / "scripts" / "audit_keepers.py")
)
ak = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ak)


def _gov(**overrides):
    """A complete governance block, with overrides applied."""
    block = dict.fromkeys(ak.GOVERNANCE_ASSERTIONS, True)
    block["attested_by"] = "test"
    block.update(overrides)
    return block


def _att(**overrides):
    """A structurally complete attestation, with overrides applied."""
    att = {
        "schema": "calibration-attestation/v1",
        "governance": _gov(),
        "exceptions": [],
        "free_parameters": {"n_entries": 0, "n_residual": 0, "entries": []},
    }
    att.update(overrides)
    return att


class TestAttestationShapeFinding(unittest.TestCase):
    def test_complete_attestation_passes(self):
        level, msg = ak.attestation_shape_finding(_att())
        self.assertEqual(level, "OK")
        self.assertIn("4/4", msg)

    def test_missing_file_fails(self):
        level, msg = ak.attestation_shape_finding(None)
        self.assertEqual(level, "FAIL")
        self.assertIn("no calibration_attestation.json", msg)

    def test_free_parameters_only_fails(self):
        # THE caiso-188 CASE: exactly what build_dof_ledger.py writes alone. E8
        # passes this ("0 entries, all with root causes"); E10 must not.
        level, msg = ak.attestation_shape_finding(
            {"free_parameters": {"n_entries": 0, "n_residual": 0, "entries": []}}
        )
        self.assertEqual(level, "FAIL")
        self.assertIn("governance", msg)
        self.assertIn("UNATTESTED", msg)

    def test_missing_governance_assertion_fails(self):
        gov = _gov()
        del gov["no_pinning_to_actuals"]
        level, msg = ak.attestation_shape_finding(_att(governance=gov))
        self.assertEqual(level, "FAIL")
        self.assertIn("no_pinning_to_actuals missing", msg)

    def test_false_assertion_fails(self):
        level, msg = ak.attestation_shape_finding(
            _att(governance=_gov(no_fit_to_price_residuals=False))
        )
        self.assertEqual(level, "FAIL")
        self.assertIn("no_fit_to_price_residuals is false", msg)

    def test_truthy_non_boolean_assertion_fails(self):
        # An assertion is a signed claim, not a coercion: "yes" / 1 must not pass
        # for a claim a human is supposed to have made deliberately.
        for value in ("yes", 1):
            with self.subTest(value=value):
                level, msg = ak.attestation_shape_finding(
                    _att(governance=_gov(no_pinning_to_actuals=value))
                )
                self.assertEqual(level, "FAIL")
                self.assertIn("not a bool", msg)

    def test_missing_exceptions_list_fails(self):
        att = _att()
        del att["exceptions"]
        level, msg = ak.attestation_shape_finding(att)
        self.assertEqual(level, "FAIL")
        self.assertIn("exceptions", msg)

    def test_exceptions_wrong_type_fails(self):
        level, msg = ak.attestation_shape_finding(_att(exceptions={}))
        self.assertEqual(level, "FAIL")
        self.assertIn("exceptions", msg)

    def test_empty_exceptions_list_is_fine(self):
        # Most keepers ledger nothing; [] is a positive statement, absence is not.
        level, _ = ak.attestation_shape_finding(_att(exceptions=[]))
        self.assertEqual(level, "OK")

    def test_missing_schema_tag_warns_but_does_not_fail(self):
        # calibration_verdict never reads "schema", so a missing version tag
        # moves no determination — surfaced, not failed (the live ERCOT keeper
        # 2026-08-09-ercot185-shaped-partial is in exactly this state).
        att = _att()
        del att["schema"]
        level, msg = ak.attestation_shape_finding(att)
        self.assertEqual(level, "WARN")
        self.assertIn("schema", msg)

    def test_missing_schema_does_not_mask_a_governance_defect(self):
        # When both are wrong the load-bearing one wins: FAIL, not WARN.
        att = _att(governance=_gov(no_pinning_to_actuals=False))
        del att["schema"]
        level, _ = ak.attestation_shape_finding(att)
        self.assertEqual(level, "FAIL")


if __name__ == "__main__":
    unittest.main()
