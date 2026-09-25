"""Rubric v3.8 — the no-price determination class (lane SOCO-22, 2026-09-13).

Owner ruling, SOCO card S2: a run from a region with NO committed price
benchmark "reads a determination that names its own basis ... scored on
C1/C2/C4/C6/C8, never CALIBRATED, with the price gap on the determination
basis at full magnitude". Card S11 fixed the predicate: "keyed on the ABSENCE
of an actual_lmp.json block — no existing ISO can reach it".

These tests pin the four things that make the class safe:

* it is REACHED by a region with no block (SOCO, NWPP), on synthetic artifacts;
* it is UNREACHABLE by a region WITH a block, whether the price scored or not,
  and unreachable by leg (ii) when a price somehow scored without a block;
* it is never ``CALIBRATED``, every NOT-YET route is untouched, and the price
  gap is named at full magnitude on EVERY route, last;
* the predicate fails CLOSED on an unreadable reference, and no registered run
  carries the block — the durable form of the seven-keeper byte-identity proof
  in docs/handoffs/FINDING-soco-22-2026-09-13.md.

Fixtures are borrowed from tests/scoring/test_calibration_verdict.py so the
no-price run is the SAME clean PJM-scale mix that scores CALIBRATED there,
re-keyed to an ISO with no price block; nothing else changes between the
reached and unreachable cases.
"""

import json
import unittest
from pathlib import Path

from tests.scoring.test_calibration_verdict import (
    DeterminationTests,
    _artifacts,
    _clean_attestation,
    _legit_artifact,
    cv,
)

_REGISTERED_ISOS = ("CAISO", "ERCOT", "MISO", "NEISO", "NYISO", "PJM", "SPP")
_NO_BLOCK_ISOS = ("SOCO", "NWPP")


def _no_price_art(iso, *, avg_lmp=False, legit=True, target_years=None, fail=False):
    """The DeterminationTests clean fixture, re-keyed to ``iso``.

    ``avg_lmp=False`` drops the bench's ``avgLMP`` block (no measured price on
    the bench side — the model side still carries an LMP); ``legit`` attaches
    the C8 artifact so the protective gate is SCORED rather than an unscored
    downgrade of its own; ``fail`` pushes CC_REGULAR +10.8 % into a C1 FAIL.
    """
    d = DeterminationTests()
    ypay = d._clean_year_payload()
    if fail:
        ypay["gmModel"]["CC_REGULAR"] = 360.0
    kw = d._clean_bench_args()
    if not avg_lmp:
        kw.pop("avg_lmp")
    art = _artifacts(
        ypay,
        iso=iso,
        attestation=_clean_attestation(),
        target_years=target_years,
        **kw,
    )
    if legit:
        art["legitimacy"] = _legit_artifact(r=0.9, cv_ratio=0.02, share=0.05)
    return art


class PredicateTests(unittest.TestCase):
    """``_price_reference_absent`` — keyed on the committed reference, fail-closed."""

    def setUp(self):
        self._path, self._cache, self._readable = (
            cv._ACTUAL_LMP_PATH,
            cv._ACTUAL_LMP_CACHE,
            cv._ACTUAL_LMP_READABLE,
        )
        self.addCleanup(self._restore)

    def _restore(self):
        cv._ACTUAL_LMP_PATH = self._path
        cv._ACTUAL_LMP_CACHE = self._cache
        cv._ACTUAL_LMP_READABLE = self._readable

    def _reset(self):
        cv._ACTUAL_LMP_CACHE = None
        cv._ACTUAL_LMP_READABLE = None

    def test_every_registered_iso_has_a_block(self):
        self._reset()
        ref = json.loads(cv._ACTUAL_LMP_PATH.read_text())
        for iso in _REGISTERED_ISOS:
            with self.subTest(iso=iso):
                self.assertIn(iso, ref)
                self.assertFalse(cv._price_reference_absent(iso))

    def test_absent_for_regions_with_no_block(self):
        self._reset()
        for iso in _NO_BLOCK_ISOS:
            with self.subTest(iso=iso):
                self.assertTrue(cv._price_reference_absent(iso))

    def test_none_iso_is_never_absent(self):
        self._reset()
        self.assertFalse(cv._price_reference_absent(None))

    def test_unreadable_reference_fails_closed(self):
        """Absence cannot be established from a file that was not read."""
        cv._ACTUAL_LMP_PATH = Path("/nonexistent/actual_lmp.json")
        self._reset()
        self.assertIsNone(cv._actual_lmp_reference())
        for iso in _REGISTERED_ISOS + _NO_BLOCK_ISOS:
            with self.subTest(iso=iso):
                self.assertFalse(cv._price_reference_absent(iso))
        # ... and the coverage reader still treats it as empty, as before.
        self.assertIsNone(cv._actual_lmp_coverage("ERCOT", 2023, "rt"))

    def test_non_dict_reference_fails_closed(self):
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(["not", "a", "table"], fh)
        cv._ACTUAL_LMP_PATH = Path(fh.name)
        self._reset()
        self.assertIsNone(cv._actual_lmp_reference())
        self.assertFalse(cv._price_reference_absent("SOCO"))

    def test_an_empty_block_is_still_a_block(self):
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump({"SOCO": {}}, fh)
        cv._ACTUAL_LMP_PATH = Path(fh.name)
        self._reset()
        self.assertFalse(cv._price_reference_absent("SOCO"))
        self.assertTrue(cv._price_reference_absent("NWPP"))


class ReachedTests(unittest.TestCase):
    """A region with no block, otherwise clean, reads the new class."""

    def test_clean_no_price_run_reads_physically_calibrated(self):
        v = cv.determine_from_artifacts("t", _no_price_art("SOCO"))
        self.assertEqual(v["determination"], cv.PHYSICALLY_CALIBRATED)
        for c in cv.PRICE_CRITERIA:
            self.assertEqual(v["criteria"][c]["status"], cv.SKIPPED, c)
        for c in ("fuelmix", "sysvol", "dispatch_corr", "governance", "forced_share"):
            self.assertEqual(v["criteria"][c]["status"], cv.PASS, c)
        self.assertIn("price_unscored", v)
        pu = v["price_unscored"]
        self.assertEqual(pu["basis"], "no actual_lmp.json block for SOCO")
        self.assertEqual(pu["criteria_unscored"], list(cv.PRICE_CRITERIA))
        self.assertEqual(
            pu["scored_on"],
            ["fuelmix", "sysvol", "dispatch_corr", "governance", "forced_share"],
        )
        # The model's own price is reported, model-only, at full magnitude.
        self.assertEqual(pu["model_mean_lmp_by_year"], {"2024": 29.0})

    def test_the_basis_line_names_everything(self):
        v = cv.determine_from_artifacts("t", _no_price_art("SOCO"))
        self.assertEqual(len(v["reasons"]), 1)
        line = v["reasons"][0]
        self.assertTrue(line.startswith("PRICE UNSCORED"))
        for needle in (
            "actual_lmp.json",
            "SOCO",
            cv.CRITERIA["price_mean"][0],
            cv.CRITERIA["price_shape"][0],
            cv.CRITERIA["price_tail"][0],
            "C1/C2/C4/C6/C8 ONLY",
            "not a CALIBRATED reading",
            "MODEL-ONLY and UNVERIFIED",
            "2024: $29.00/MWh",
            "rubric v3.8",
        ):
            self.assertIn(needle, line)
        # No "unscored criteria" downgrade line and no v3.7 exempt line: the
        # price criteria are named together on the basis line instead.
        self.assertFalse(any(r.startswith("unscored criteria") for r in v["reasons"]))
        self.assertFalse(any("rubric v3.7" in r for r in v["reasons"]))
        # The headline carries the basis, since it is the only reason.
        self.assertIn("PRICE UNSCORED", cv.headline(v))

    def test_nwpp_reads_the_same_class(self):
        """NWPP card N2 limb (b): the REJECTED series never landed, so no block."""
        v = cv.determine_from_artifacts("t", _no_price_art("NWPP"))
        self.assertEqual(v["determination"], cv.PHYSICALLY_CALIBRATED)
        self.assertEqual(
            v["price_unscored"]["basis"], "no actual_lmp.json block for NWPP"
        )

    def test_render_and_condensed_carry_the_block(self):
        v = cv.determine_from_artifacts("t", _no_price_art("SOCO"))
        txt = cv.render_text(v)
        self.assertIn("CALIBRATION DETERMINATION: " + cv.PHYSICALLY_CALIBRATED, txt)
        self.assertIn("PRICE UNSCORED (rubric v3.8)", txt)
        self.assertIn("NOT a CALIBRATED reading", txt)
        self.assertEqual(cv.condensed_metrics(v)["price_unscored"], v["price_unscored"])


class NeverCalibratedTests(unittest.TestCase):
    """Ruling consequence (ii): never CALIBRATED, and every other route intact."""

    def test_labels_are_distinct_from_every_existing_label(self):
        existing = {cv.CALIBRATED, cv.CALIBRATED_CAVEATS, cv.NOT_YET}
        self.assertNotIn(cv.PHYSICALLY_CALIBRATED, existing)
        self.assertNotIn(cv.PHYSICALLY_CALIBRATED_CAVEATS, existing)
        self.assertNotEqual(cv.PHYSICALLY_CALIBRATED, cv.PHYSICALLY_CALIBRATED_CAVEATS)
        self.assertIn("PRICE UNSCORED", cv.PHYSICALLY_CALIBRATED)
        self.assertIn("PRICE UNSCORED", cv.PHYSICALLY_CALIBRATED_CAVEATS)
        self.assertIn("CAVEATS", cv.PHYSICALLY_CALIBRATED_CAVEATS)

    def test_clean_no_price_run_is_not_calibrated(self):
        v = cv.determine_from_artifacts("t", _no_price_art("SOCO"))
        self.assertNotIn(v["determination"], (cv.CALIBRATED, cv.CALIBRATED_CAVEATS))

    def test_a_fail_is_still_not_yet_and_still_names_the_price_gap(self):
        v = cv.determine_from_artifacts("t", _no_price_art("SOCO", fail=True))
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertEqual(v["criteria"]["fuelmix"]["status"], cv.FAIL)
        # The FAIL line keeps the headline; the price line is present and LAST,
        # so the run can never be read as having failed on price.
        self.assertTrue(v["reasons"][0].startswith("undocumented out-of-tolerance"))
        self.assertIn("fuelmix", v["reasons"][0])
        self.assertTrue(v["reasons"][-1].startswith("PRICE UNSCORED"))
        self.assertIn("price_unscored", v)

    def test_unattested_governance_is_still_not_yet(self):
        art = _no_price_art("SOCO")
        art["attestation"] = None
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertTrue(v["reasons"][0].startswith("governance gate"))
        self.assertTrue(v["reasons"][-1].startswith("PRICE UNSCORED"))

    def test_caveat_rung_on_a_data_blocked_year(self):
        v = cv.determine_from_artifacts(
            "t", _no_price_art("SOCO", target_years=[2024, 2025])
        )
        self.assertEqual(v["determination"], cv.PHYSICALLY_CALIBRATED_CAVEATS)
        self.assertEqual(v["data_blocked_years"], [2025])
        self.assertTrue(v["reasons"][0].startswith("data-blocked target year(s): 2025"))
        self.assertTrue(v["reasons"][-1].startswith("PRICE UNSCORED"))

    def test_caveat_rung_on_an_unscored_protective_criterion(self):
        """The protective fail-closed guard is untouched: no C8 artifact downgrades."""
        v = cv.determine_from_artifacts("t", _no_price_art("SOCO", legit=False))
        self.assertEqual(v["determination"], cv.PHYSICALLY_CALIBRATED_CAVEATS)
        self.assertEqual(v["criteria"]["forced_share"]["status"], cv.SKIPPED)
        self.assertTrue(v["reasons"][0].startswith("unscored PROTECTIVE criteria"))
        self.assertIn("forced_share", v["reasons"][0])
        # ... and the price criteria are NOT in that downgrade list.
        self.assertNotIn("price_mean", v["reasons"][0])

    def test_main_exit_code_semantics_are_unchanged(self):
        # main() exits non-zero on NOT-YET only; the new labels are not NOT-YET.
        self.assertNotEqual(cv.PHYSICALLY_CALIBRATED, cv.NOT_YET)
        self.assertNotEqual(cv.PHYSICALLY_CALIBRATED_CAVEATS, cv.NOT_YET)


class UnreachableTests(unittest.TestCase):
    """A region WITH a block can never reach the class, whatever its price does."""

    def test_block_present_price_absent_reads_as_before(self):
        """The PARTIAL / missing-year case: the ordinary rubric, unchanged."""
        v = cv.determine_from_artifacts("t", _no_price_art("PJM"))
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)
        self.assertNotIn("price_unscored", v)
        downgrading = [r for r in v["reasons"] if r.startswith("unscored criteria:")]
        self.assertEqual(len(downgrading), 1)
        self.assertIn("price_mean", downgrading[0])
        self.assertIn("price_shape", downgrading[0])
        self.assertTrue(any("rubric v3.7" in r for r in v["reasons"]))
        self.assertFalse(any(r.startswith("PRICE UNSCORED") for r in v["reasons"]))

    def test_block_present_price_present_reads_calibrated(self):
        v = cv.determine_from_artifacts("t", _no_price_art("PJM", avg_lmp=True))
        self.assertEqual(v["determination"], cv.CALIBRATED)
        self.assertNotIn("price_unscored", v)

    def test_every_registered_iso_is_unreachable(self):
        for iso in _REGISTERED_ISOS:
            with self.subTest(iso=iso):
                v = cv.determine_from_artifacts("t", _no_price_art(iso))
                self.assertNotIn("price_unscored", v)
                self.assertNotIn(
                    v["determination"],
                    (cv.PHYSICALLY_CALIBRATED, cv.PHYSICALLY_CALIBRATED_CAVEATS),
                )

    def test_leg_two_a_scored_price_overrides_absence(self):
        """No block, but the bench carries a price anyway: the ordinary path."""
        v = cv.determine_from_artifacts("t", _no_price_art("SOCO", avg_lmp=True))
        self.assertEqual(v["criteria"]["price_mean"]["status"], cv.PASS)
        self.assertEqual(v["determination"], cv.CALIBRATED)
        self.assertNotIn("price_unscored", v)
        self.assertFalse(any(r.startswith("PRICE UNSCORED") for r in v["reasons"]))

    def test_a_scored_price_tail_alone_blocks_the_branch(self):
        """Leg (ii) is ALL three: one scored price criterion is enough to refuse."""
        from tests.scoring.test_calibration_verdict import _reset_tail, _tail

        _tail({"SOCO": {"2024": {"da_gt": 80, "rt_gt": 100, "rt_coverage": 1.0}}})
        self.addCleanup(_reset_tail)
        art = _no_price_art("SOCO")
        art["payload"]["years"]["2024"]["ordc"] = {
            "hoursGt200": {"actual": 100, "model": 100}
        }
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["criteria"]["price_tail"]["status"], cv.PASS)
        self.assertNotIn("price_unscored", v)
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)


class RegisteredRunsTests(unittest.TestCase):
    """No registered run reaches the class — the durable byte-identity guard."""

    # SOCO and NWPP now register runs that legitimately carry the no-price
    # class (no actual_lmp.json block exists for either). This test was written
    # before any such run was registered, so it skips their sidecars and asserts
    # every other sidecar belongs to a price-bearing ISO; the class itself is
    # pinned by test_no_block_registered_runs_reach_the_class below (owner
    # ruling R-BE, director board v43, 2026-09-25; proposal
    # docs/handoffs/FINDING-y29-promotion-provenance-2026-09-24.md §4).

    def test_no_registered_run_carries_the_block(self):
        sidecars = sorted(cv.REGISTRY_DIR.glob("*.json"))
        self.assertTrue(sidecars, "no registered runs found")
        for p in sidecars:
            iso = json.loads(p.read_text()).get("iso")
            if iso in _NO_BLOCK_ISOS:
                continue
            with self.subTest(run=p.stem, iso=iso):
                self.assertIn(iso, _REGISTERED_ISOS)
                self.assertFalse(cv._price_reference_absent(iso))
                v = cv.determine(p.stem)
                self.assertNotIn("price_unscored", v)
                self.assertNotIn(
                    v["determination"],
                    (cv.PHYSICALLY_CALIBRATED, cv.PHYSICALLY_CALIBRATED_CAVEATS),
                )
                self.assertFalse(
                    any(r.startswith("PRICE UNSCORED") for r in v["reasons"])
                )

    def test_no_block_registered_runs_reach_the_class(self):
        sidecars = [
            p
            for p in sorted(cv.REGISTRY_DIR.glob("*.json"))
            if json.loads(p.read_text()).get("iso") in _NO_BLOCK_ISOS
        ]
        for p in sidecars:
            iso = json.loads(p.read_text()).get("iso")
            with self.subTest(run=p.stem, iso=iso):
                self.assertTrue(cv._price_reference_absent(iso))
                v = cv.determine(p.stem)
                self.assertIn("price_unscored", v)
                self.assertNotIn(
                    v["determination"], (cv.CALIBRATED, cv.CALIBRATED_CAVEATS)
                )
                self.assertTrue(
                    any(r.startswith("PRICE UNSCORED") for r in v["reasons"])
                )


if __name__ == "__main__":
    unittest.main()
