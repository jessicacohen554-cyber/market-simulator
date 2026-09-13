"""NWPP-22 pins on the rubric v3.8 no-price determination class.

The class itself landed on ``main`` from lane SOCO-22 (owner rulings S2 / S11 and
NWPP card N2 limb (b), 2026-09-13 — one branch in ``scripts/calibration_verdict.py``
serving both regions). Its general behaviour is pinned by
``tests/scoring/test_calibration_verdict_price_unscored.py``. This file adds only
what the NWPP charter asks for beyond that: the exact reading of an NWPP-shaped
MULTI-YEAR span (2023–2025) against the REAL committed price-reference store, and
a payload-level proof that an ISO carrying a series scores byte-identically
whether or not the class exists. Synthetic artifacts throughout; no registry, no
bundle, no LP.
"""

import json
import unittest

from tests.scoring.test_calibration_verdict import (
    DeterminationTests,
    _artifacts,
    _clean_attestation,
    _legit_artifact,
    cv,
)

_SPAN = (2023, 2024, 2025)


def _span_art(iso, *, avg_lmp, drop_fuelrows=False):
    """The DeterminationTests clean fixture fanned across 2023–2025 for ``iso``."""
    d = DeterminationTests()
    kw = d._clean_bench_args()
    if not avg_lmp:
        kw.pop("avg_lmp")
    ypay = d._clean_year_payload()
    if drop_fuelrows:
        ypay.pop("fuelRows")  # C4 becomes an unscored PHYSICAL criterion
    art = _artifacts(
        ypay, iso=iso, attestation=_clean_attestation(), target_years=list(_SPAN), **kw
    )
    art["payload"]["years"] = {str(y): dict(ypay) for y in _SPAN}
    art["bench"] = {y: dict(art["bench"][2024]) for y in _SPAN}
    art["legitimacy"] = _legit_artifact(r=0.9, cv_ratio=0.02, share=0.05)
    art["legitimacy"]["years"] = list(_SPAN)
    for key in ("D1", "D2"):
        rows_key = "rows" if key == "D1" else "summary"
        base = art["legitimacy"]["diagnostics"][key][rows_key][0]
        art["legitimacy"]["diagnostics"][key][rows_key] = [
            {**base, "year": y} for y in _SPAN
        ]
    return art


class NwppSpanTests(unittest.TestCase):
    """An NWPP-shaped 2023–2025 run against the committed store, no injection."""

    def setUp(self):
        cv._ACTUAL_LMP_CACHE = None
        cv._ACTUAL_LMP_READABLE = None
        cv._TAIL_CACHE = {}

    def tearDown(self):
        cv._ACTUAL_LMP_CACHE = None
        cv._ACTUAL_LMP_READABLE = None
        cv._TAIL_CACHE = None

    def test_exact_reading_on_the_full_span(self):
        v = cv.determine_from_artifacts("t", _span_art("NWPP", avg_lmp=False))
        self.assertEqual(v["determination"], "PHYSICALLY-CALIBRATED (PRICE UNSCORED)")
        self.assertEqual(v["determination"], cv.PHYSICALLY_CALIBRATED)
        self.assertEqual(v["scorable_years"], list(_SPAN))
        self.assertEqual(v["price_reference_blocked_years"], list(_SPAN))
        # Never a PASS: every price criterion SKIPPED in every year, and none
        # counted toward the target grade.
        for c in cv.PRICE_CRITERIA:
            self.assertEqual(v["criteria"][c]["status"], cv.SKIPPED, c)
            years = {r["year"] for r in v["criteria"][c]["records"] if r["key"] is None}
            self.assertEqual(years, set(_SPAN), c)
        self.assertEqual(
            v["grade_summary"]["target_grade"], v["grade_summary"]["scored"]
        )
        # The basis line names NWPP and all three years, at full magnitude.
        line = v["reasons"][-1]
        self.assertTrue(line.startswith("PRICE UNSCORED"))
        self.assertIn("NWPP", line)
        for y in _SPAN:
            self.assertIn(f"{y}: $29.00/MWh", line)
        self.assertEqual(
            v["price_unscored"]["model_mean_lmp_by_year"],
            {str(y): 29.0 for y in _SPAN},
        )

    def test_physical_caveat_reads_the_caveats_rung(self):
        v = cv.determine_from_artifacts(
            "t", _span_art("NWPP", avg_lmp=False, drop_fuelrows=True)
        )
        self.assertEqual(
            v["determination"], "PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED)"
        )
        self.assertEqual(v["determination"], cv.PHYSICALLY_CALIBRATED_CAVEATS)
        self.assertIn("unscored criteria: dispatch_corr", v["reasons"])
        self.assertTrue(v["reasons"][-1].startswith("PRICE UNSCORED"))

    def test_labels_never_read_as_calibrated(self):
        for s in (cv.PHYSICALLY_CALIBRATED, cv.PHYSICALLY_CALIBRATED_CAVEATS):
            self.assertNotEqual(s, cv.CALIBRATED)
            self.assertNotEqual(s, cv.CALIBRATED_CAVEATS)
            self.assertFalse(s.startswith(cv.CALIBRATED))
            self.assertIn("PRICE UNSCORED", s)


class SeriesIsoByteIdentityTests(unittest.TestCase):
    """An ISO carrying a series: the same bytes with the class live or disabled."""

    def tearDown(self):
        cv._ACTUAL_LMP_CACHE = None
        cv._ACTUAL_LMP_READABLE = None
        cv._TAIL_CACHE = None

    def _payload(self, iso, avg_lmp):
        cv._TAIL_CACHE = {}
        v = cv.determine_from_artifacts("t", _span_art(iso, avg_lmp=avg_lmp))
        return json.dumps(v, sort_keys=True)

    def test_full_payload_identical_with_and_without_the_class(self):
        # Scored with the committed reference (the class is live) and again
        # with the reference forced unreadable (the class cannot fire for
        # anyone): a series-carrying ISO's verdict is the same bytes either
        # way, on the full 2023–2025 span, priced and un-priced.
        for iso, avg_lmp in (("PJM", True), ("PJM", False), ("MISO", False)):
            with self.subTest(iso=iso, avg_lmp=avg_lmp):
                cv._ACTUAL_LMP_CACHE = None
                cv._ACTUAL_LMP_READABLE = None
                live = self._payload(iso, avg_lmp)
                self.assertNotIn('"price_unscored"', live)
                cv._ACTUAL_LMP_CACHE = {}
                cv._ACTUAL_LMP_READABLE = False
                disabled = self._payload(iso, avg_lmp)
                self.assertEqual(live, disabled)


if __name__ == "__main__":
    unittest.main()
