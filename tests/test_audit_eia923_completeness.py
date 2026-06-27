"""Tests for the EIA-923 completeness audit (scripts/audit_eia923_completeness.py).

The per-(ISO, class) completeness verdict and the family-gate roll-up are
exercised on synthetic ``{plant, class, year, monthly}`` frames — no on-disk
923 read — so the complete / incomplete / immaterial call and the gate logic are
pinned independently of any particular vintage. The script lives under scripts/,
so it is loaded by path.
"""

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "audit_eia923_completeness",
    str(_REPO / "scripts" / "audit_eia923_completeness.py"),
)
au = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(au)

_MCOLS = [
    "netgen_january_mwh",
    "netgen_february_mwh",
    "netgen_march_mwh",
    "netgen_april_mwh",
    "netgen_may_mwh",
    "netgen_june_mwh",
    "netgen_july_mwh",
    "netgen_august_mwh",
    "netgen_september_mwh",
    "netgen_october_mwh",
    "netgen_november_mwh",
    "netgen_december_mwh",
]


def _frame(rows):
    """Build a (plant, class) frame; each row is (plant_id, klass, annual_mwh,
    n_months_reported). Monthly cells are the annual split evenly over the first
    ``n_months`` calendar months; the rest are NaN (not reported)."""
    recs = []
    for pid, klass, annual, n_months in rows:
        rec = {"plant_id": pid, "klass": klass, "netgen_annual_mwh": annual}
        per = annual / n_months if n_months else 0.0
        for i, col in enumerate(_MCOLS):
            rec[col] = per if i < n_months else np.nan
        recs.append(rec)
    return pd.DataFrame(recs)


class AuditIsoClassTests(unittest.TestCase):
    def test_complete_when_all_plants_report_all_months(self):
        # Same two plants in both years, full 12 months -> COMPLETE.
        prior = _frame([(1, "COAL_PRB", 30e6, 12), (2, "COAL_PRB", 14e6, 12)])
        cur = _frame([(1, "COAL_PRB", 31e6, 12), (2, "COAL_PRB", 13e6, 12)])
        rec = au._audit_iso_class(cur, prior, "COAL_PRB")
        self.assertEqual(rec["status"], "complete")
        self.assertEqual(rec["n_missing_plants"], 0)
        self.assertEqual(rec["last_month"], 12)

    def test_incomplete_when_a_prior_plant_is_missing(self):
        # Plant 2 (material in prior) does not report in the current vintage ->
        # plant-reporting retention < threshold -> INCOMPLETE, even though the
        # plant that DID report is complete.
        prior = _frame([(1, "CC_REGULAR", 60e6, 12), (2, "CC_REGULAR", 40e6, 12)])
        cur = _frame([(1, "CC_REGULAR", 61e6, 12)])
        rec = au._audit_iso_class(cur, prior, "CC_REGULAR")
        self.assertEqual(rec["status"], "incomplete")
        self.assertEqual(rec["n_missing_plants"], 1)

    def test_incomplete_when_months_truncated(self):
        # All plants report but only the first 8 months are present (a vintage
        # still filling in) -> plant-month coverage below threshold -> INCOMPLETE.
        prior = _frame([(1, "ST_GAS", 20e6, 12)])
        cur = _frame([(1, "ST_GAS", 13e6, 8)])
        rec = au._audit_iso_class(cur, prior, "ST_GAS")
        self.assertEqual(rec["status"], "incomplete")
        self.assertEqual(rec["last_month"], 8)

    def test_immaterial_below_threshold(self):
        # A near-zero family member is immaterial -> never gated, never failed.
        prior = _frame([(1, "ST_CHP", 0.4e6, 12)])
        cur = _frame([(1, "ST_CHP", 0.3e6, 12)])
        rec = au._audit_iso_class(cur, prior, "ST_CHP")
        self.assertEqual(rec["status"], "immaterial")


class FamilyGateTests(unittest.TestCase):
    def test_gate_requires_complete_class_and_complete_family(self):
        # COAL_PRB & COAL_LIGNITE both complete -> coal family complete -> both
        # gate. A lone-complete class in an incomplete family does NOT gate.
        classes = {
            "COAL_PRB": {"status": "complete"},
            "COAL_LIGNITE": {"status": "complete"},
            "CC_REGULAR": {"status": "complete"},  # complete class ...
            "CT_PEAKER": {"status": "incomplete"},  # ... but family incomplete
        }
        fams = au._apply_family_gate(classes)
        self.assertTrue(fams["coal"])
        self.assertFalse(fams["gas"])
        self.assertTrue(classes["COAL_PRB"]["gate"])
        self.assertTrue(classes["COAL_LIGNITE"]["gate"])
        self.assertFalse(classes["CC_REGULAR"]["gate"])  # family not complete
        self.assertFalse(classes["CT_PEAKER"]["gate"])

    def test_immaterial_members_do_not_block_family(self):
        # An immaterial member is ignored when judging family completeness.
        classes = {
            "COAL_PRB": {"status": "complete"},
            "COAL_BIT": {"status": "immaterial"},
        }
        fams = au._apply_family_gate(classes)
        self.assertTrue(fams["coal"])
        self.assertTrue(classes["COAL_PRB"]["gate"])

    def test_empty_family_gates_nothing(self):
        classes = {"COAL_BIT": {"status": "immaterial"}}
        fams = au._apply_family_gate(classes)
        self.assertFalse(fams["coal"])
        self.assertFalse(classes["COAL_BIT"]["gate"])


if __name__ == "__main__":
    unittest.main()
