"""Rubric v3.19 — the owner-signed REFERENCE-COVERAGE caveat kind (ruling R-40).

Owner ruling R-40 (2026-10-03, verbatim): "Caiso mean LMP for 2021 should be an
accepted caveat or only compared where data is actually available for that year
for calibration rubric. 2019 and 2020 should have that be accepted caveat for
c3a." Extended the same day: "I want c3b treated the same."

Pinned here, on the trivial clean fixture (1 zone, flat $29 model price):

* an ABSENT reference (no bench avgLMP, no actual_lmp.json year block) reads
  CAVEAT with the kind, instead of SKIPPED;
* a PARTIAL reference scores only the covered months and reads CAVEAT, with the
  in-window band verdict kept beside it as ``window_status`` — never a PASS;
* the kind never downgrades and spends no caveat slot;
* fail-closed: a registry row without its attestation twin, without governance,
  or whose record state does not match the registry, does not move.
"""

import unittest
from unittest import mock

from tests.scoring.test_calibration_verdict import (
    DeterminationTests,
    _artifacts,
    _clean_attestation,
    _legit_artifact,
    cv,
)

# Months 1-4 uncovered (rt_cov < 0.90), as CAISO 2021's OASIS RT series.
_PARTIAL_MON = [0.0, 0.0, 0.0, 0.135, 1.0, 1.0, 0.9987, 1.0, 1.0, 1.0, 1.0, 1.0]
_REF_PARTIAL = {"CAISO": {"2021": {"rt_cov": {"annual": 0.70, "mon": _PARTIAL_MON}}}}
_REF_ABSENT = {"CAISO": {"2021": {}}}
# Junk in the uncovered months: a scorer that compared them could not pass.
_JUNK_MON = [999.0] * 4 + [29.0] * 8


def _entries(year, criteria=("price_mean", "price_shape")):
    return [
        {
            "criterion": c,
            "year": year,
            "kind": "reference-coverage",
            "magnitude": "test",
            "reason": "owner ruling R-40 (test)",
        }
        for c in criteria
    ]


def _art(*, iso="CAISO", year=2021, avg_lmp=None, exceptions=None, attested=True):
    d = DeterminationTests()
    kw = d._clean_bench_args()
    kw["avg_lmp"] = avg_lmp
    art = _artifacts(
        d._clean_year_payload(),
        iso=iso,
        year=year,
        attestation=_clean_attestation(exceptions) if attested else None,
        **kw,
    )
    art["legitimacy"] = _legit_artifact(year=year, r=0.9, cv_ratio=0.02, share=0.05)
    return art


def _rec(v, criterion, year):
    for r in v["criteria"][criterion]["records"]:
        if int(r["year"]) == year and r.get("key") is None:
            return r
    raise AssertionError(f"no {criterion} record {year}")


def _determine(art, ref):
    with mock.patch.object(cv, "_actual_lmp_reference", return_value=ref):
        return cv.determine_from_artifacts("t", art)


class RegistryTests(unittest.TestCase):
    def test_registry_is_exactly_the_six_caiso_rows(self):
        self.assertEqual(
            set(cv.REFERENCE_COVERAGE_ENTRIES),
            {
                ("CAISO", y, c, None)
                for y in (2019, 2020, 2021)
                for c in ("price_mean", "price_shape")
            },
        )
        for (_, y, _, _), e in cv.REFERENCE_COVERAGE_ENTRIES.items():
            self.assertEqual(e["coverage"], "partial" if y == 2021 else "absent")
            self.assertIn("R-40", e["reason"])
        # Budgets and the ledgerable set are untouched.
        self.assertEqual(cv.LEDGERABLE_CRITERIA, frozenset({"price_tail"}))
        self.assertEqual(cv.MAX_LEDGERED_CAVEATS, 1)
        self.assertEqual(cv.RUBRIC_VERSION, "3.19")


class AbsentReferenceTests(unittest.TestCase):
    def test_absent_reference_reads_caveat_with_the_kind(self):
        v = _determine(_art(year=2019, exceptions=_entries(2019)), _REF_ABSENT)
        for c in ("price_mean", "price_shape"):
            r = _rec(v, c, 2019)
            self.assertEqual(r["status"], cv.CAVEAT)
            self.assertEqual(r["classification"], cv.REFERENCE_COVERAGE)
            self.assertEqual(r["reference_coverage"], "absent")
            self.assertIn("reference absent", r["magnitude"])
            self.assertIsNone(r["actual"])
            self.assertEqual(v["criteria"][c]["caveat_kind"], "reference-coverage")
        self.assertEqual(len(v["caveats"]["reference_coverage"]), 2)
        self.assertEqual(v["caveats"]["ledgered"], [])
        self.assertEqual(v["caveats"]["commercial_band"], [])

    def test_absent_without_attestation_twin_stays_skipped(self):
        v = _determine(_art(year=2019, exceptions=[]), _REF_ABSENT)
        for c in ("price_mean", "price_shape"):
            self.assertEqual(_rec(v, c, 2019)["status"], cv.SKIPPED)
        self.assertNotIn("reference_coverage", v["caveats"])

    def test_absent_registry_row_does_not_move_a_scored_record(self):
        # A 2019 that somehow carries a reference is scored, not absent.
        art = _art(
            year=2019,
            avg_lmp={"rt": 29.0, "rt_mon": [29] * 12},
            exceptions=_entries(2019),
        )
        v = _determine(art, {"CAISO": {"2019": {}}})
        self.assertEqual(_rec(v, "price_mean", 2019)["status"], cv.PASS)
        self.assertEqual(_rec(v, "price_shape", 2019)["status"], cv.PASS)


class PartialReferenceTests(unittest.TestCase):
    def test_partial_scores_only_covered_months_and_never_passes(self):
        art = _art(
            avg_lmp={"rt": 200.0, "rt_mon": _JUNK_MON}, exceptions=_entries(2021)
        )
        v = _determine(art, _REF_PARTIAL)
        mean, shape = _rec(v, "price_mean", 2021), _rec(v, "price_shape", 2021)
        # On the covered window the model is exact: the junk months are masked.
        self.assertEqual(mean["actual"], 29.0)
        self.assertEqual(mean["magnitude"], "+0.0%")
        self.assertEqual(shape["magnitude"], "NRMSE 0.000")
        for r in (mean, shape):
            self.assertEqual(r["status"], cv.CAVEAT)  # never PASS
            self.assertEqual(r["window_status"], cv.PASS)
            self.assertEqual(r["reference_coverage"], "partial")
            self.assertEqual(r["coverage_annual"], 0.70)

    def test_partial_window_fail_reads_caveat_with_window_fail(self):
        art = _art(
            avg_lmp={"rt": 40.0, "rt_mon": [40.0] * 12}, exceptions=_entries(2021)
        )
        r = _rec(_determine(art, _REF_PARTIAL), "price_mean", 2021)
        self.assertEqual(r["status"], cv.CAVEAT)
        self.assertEqual(r["window_status"], cv.FAIL)
        self.assertTrue(r["magnitude"].startswith("-27"))  # on-window magnitude

    def test_partial_registry_row_needs_partial_coverage(self):
        art = _art(
            avg_lmp={"rt": 40.0, "rt_mon": [40.0] * 12}, exceptions=_entries(2021)
        )
        full = {"CAISO": {"2021": {"rt_cov": {"annual": 1.0, "mon": [1.0] * 12}}}}
        self.assertEqual(
            _rec(_determine(art, full), "price_mean", 2021)["status"], cv.FAIL
        )

    def test_partial_without_attestation_twin_stays_fail(self):
        art = _art(avg_lmp={"rt": 40.0, "rt_mon": [40.0] * 12}, exceptions=[])
        v = _determine(art, _REF_PARTIAL)
        self.assertEqual(_rec(v, "price_mean", 2021)["status"], cv.FAIL)
        self.assertEqual(v["determination"], cv.NOT_YET)


class NonDowngradingTests(unittest.TestCase):
    def test_kind_never_downgrades(self):
        # Control: the same fixture with a full, matching reference.
        ctrl = _determine(
            _art(avg_lmp={"rt": 29.0, "rt_mon": [29] * 12}), {"CAISO": {"2021": {}}}
        )
        art = _art(
            avg_lmp={"rt": 40.0, "rt_mon": [40.0] * 12}, exceptions=_entries(2021)
        )
        v = _determine(art, _REF_PARTIAL)
        self.assertEqual(v["determination"], ctrl["determination"])
        line = [x for x in v["reasons"] if "reference-coverage" in x]
        self.assertEqual(len(line), 1)
        self.assertIn("R-40", line[0])

    def test_absent_kind_never_downgrades(self):
        ctrl = _determine(
            _art(year=2019, avg_lmp={"rt": 29.0, "rt_mon": [29] * 12}),
            {"CAISO": {"2019": {}}},
        )
        v = _determine(_art(year=2019, exceptions=_entries(2019)), _REF_ABSENT)
        self.assertEqual(v["determination"], ctrl["determination"])

    def test_governance_failure_blocks_it(self):
        art = _art(year=2019, exceptions=_entries(2019), attested=False)
        v = _determine(art, _REF_ABSENT)
        self.assertEqual(_rec(v, "price_mean", 2019)["status"], cv.SKIPPED)

    def test_other_iso_with_an_entry_does_not_move(self):
        art = _art(
            iso="ERCOT",
            avg_lmp={"rt": 40.0, "rt_mon": [40.0] * 12},
            exceptions=_entries(2021),
        )
        ref = {"ERCOT": {"2021": {"rt_cov": {"annual": 0.7, "mon": _PARTIAL_MON}}}}
        v = _determine(art, ref)
        self.assertEqual(_rec(v, "price_mean", 2021)["status"], cv.FAIL)
        self.assertNotIn("reference_coverage", v["caveats"])


if __name__ == "__main__":
    unittest.main()
