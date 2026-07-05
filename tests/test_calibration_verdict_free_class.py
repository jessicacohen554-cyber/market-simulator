"""Tests for the D-10 free-class rescore and D-3 ablation delta helpers.

Exercises ``calibration_verdict`` (loaded by path — it lives under scripts/):
``pinned_classes`` (the declared per-ISO registry), ``free_class_fuelmix_score``
(C1 all-classes vs pinned-excluded), and ``compute_ablation_delta`` (per-class
keeper-minus-twin TWh). Synthetic records/payloads only — no committed artifacts.
"""

import importlib.util
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "calibration_verdict", str(_REPO / "scripts" / "calibration_verdict.py")
)
cv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cv)


def _fuelmix(key, status, year=2023):
    return {"criterion": "fuelmix", "key": key, "year": year, "status": status}


class PinnedRegistryTest(unittest.TestCase):
    def test_chp_pinned_every_iso(self):
        for iso in ("ERCOT", "PJM", "CAISO", "NYISO", "NEISO", "MISO"):
            pins = cv.pinned_classes(iso)
            for chp in ("CC_CHP", "CT_CHP", "ST_CHP"):
                self.assertIn(chp, pins)

    def test_nyiso_adds_imports(self):
        self.assertIn("NET_IMPORTS", cv.pinned_classes("NYISO"))
        self.assertNotIn("NET_IMPORTS", cv.pinned_classes("ERCOT"))

    def test_case_insensitive(self):
        self.assertEqual(cv.pinned_classes("ercot"), cv.pinned_classes("ERCOT"))


class FreeClassScoreTest(unittest.TestCase):
    def test_excludes_pinned_from_free_count(self):
        records = [
            _fuelmix("CC_REGULAR", cv.PASS),
            _fuelmix("CT_PEAKER", cv.FAIL),
            _fuelmix("COAL_PRB", cv.PASS),
            _fuelmix("CC_CHP", cv.PASS),  # pinned
            _fuelmix("ST_CHP", cv.PASS),  # pinned
        ]
        s = cv.free_class_fuelmix_score(records, "ERCOT")
        # All-classes: 4 pass / 5 gated.
        self.assertEqual(s["all_classes"], {"pass": 4, "total": 5})
        # Free-classes: CHP removed -> 2 pass (CC_REGULAR, COAL_PRB) / 3 gated.
        self.assertEqual(s["free_classes"], {"pass": 2, "total": 3})
        self.assertIn("CC_CHP", s["pinned_excluded"])
        self.assertNotIn("CC_CHP", s["free_class_keys"])

    def test_skipped_out_of_denominator(self):
        records = [
            _fuelmix("CC_REGULAR", cv.PASS),
            _fuelmix("COAL_BIT", cv.SKIPPED),  # incomplete actual — not gated
        ]
        s = cv.free_class_fuelmix_score(records, "PJM")
        self.assertEqual(s["all_classes"], {"pass": 1, "total": 1})

    def test_caveat_counts_as_pass(self):
        records = [_fuelmix("CT_PEAKER", cv.CAVEAT)]
        s = cv.free_class_fuelmix_score(records, "ERCOT")
        self.assertEqual(s["free_classes"], {"pass": 1, "total": 1})

    def test_ignores_non_fuelmix_records(self):
        records = [
            _fuelmix("CC_REGULAR", cv.PASS),
            {"criterion": "price_mean", "key": None, "status": cv.FAIL},
        ]
        s = cv.free_class_fuelmix_score(records, "ERCOT")
        self.assertEqual(s["all_classes"]["total"], 1)


class AblationDeltaTest(unittest.TestCase):
    def _payload(self, gm_by_year):
        return {"years": {y: {"gmModel": gm} for y, gm in gm_by_year.items()}}

    def test_per_class_delta_summed_over_shared_years(self):
        keeper = self._payload(
            {"2023": {"CT_PEAKER": 10.0}, "2024": {"CT_PEAKER": 8.0}}
        )
        twin = self._payload({"2023": {"CT_PEAKER": 6.0}, "2024": {"CT_PEAKER": 5.0}})
        rows = cv.compute_ablation_delta(keeper, twin)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["class"], "CT_PEAKER")
        self.assertEqual(r["keeper_twh"], 18.0)
        self.assertEqual(r["ablation_twh"], 11.0)
        self.assertEqual(r["delta_twh"], 7.0)

    def test_only_shared_years(self):
        keeper = self._payload({"2023": {"X": 5.0}, "2025": {"X": 9.0}})
        twin = self._payload({"2023": {"X": 2.0}})  # no 2025
        rows = cv.compute_ablation_delta(keeper, twin)
        self.assertEqual(rows[0]["keeper_twh"], 5.0)  # 2025 excluded

    def test_missing_class_treated_zero_and_sorted_by_abs_delta(self):
        keeper = self._payload({"2023": {"CT_PEAKER": 3.0, "CC_REGULAR": 1.0}})
        twin = self._payload({"2023": {"CC_REGULAR": 1.0}})  # CT absent in twin
        rows = cv.compute_ablation_delta(keeper, twin)
        self.assertEqual(rows[0]["class"], "CT_PEAKER")  # largest |delta| first
        self.assertEqual(rows[0]["delta_twh"], 3.0)
        cc = next(r for r in rows if r["class"] == "CC_REGULAR")
        self.assertEqual(cc["delta_twh"], 0.0)

    def test_empty_payloads(self):
        self.assertEqual(cv.compute_ablation_delta({}, {}), [])


if __name__ == "__main__":
    unittest.main()
