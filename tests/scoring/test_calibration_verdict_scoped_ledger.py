"""Rubric v3.10 — the scoped ledger row (lane soco-83, 2026-09-28).

Owner ruling 2026-09-27 (soco-82 decision card on 2019 COAL_BIT, verbatim:
"Ledger as limitation"), re-authorized for implementation in soco-83. ONE row —
(SOCO, 2019, fuelmix, COAL_BIT) — may be reclassified from FAIL to a ledgered
CAVEAT past the v3.1 C3c-only guard, and only for a model UNDER-run.

These tests pin that nothing else moves:

* the exact key is reached, reads CAVEAT (never PASS), keeps its magnitude,
  spends the single ledgered slot and DOWNGRADES to the caveat rung;
* any other ISO, year, class, or the over-run direction stays a FAIL;
* failing governance blocks it; the ledgered budget is still checked first;
* LEDGERABLE_CRITERIA is unchanged and the scoped table holds exactly the
  v3.10 row plus the three v3.11 SOCO C3a rows (owner ruling 2026-09-30,
  soco-94: exact rows, direction-bound, spend the slot, downgrade).
"""

import unittest

from tests.scoring.test_calibration_verdict import (
    DeterminationTests,
    _artifacts,
    _clean_attestation,
    _legit_artifact,
    cv,
)

_KEY = ("SOCO", 2019, "fuelmix", "COAL_BIT")
# Rubric v3.11 (owner ruling 2026-09-30, soco-94): the three SOCO C3a rows.
_C3A_KEYS = {
    ("SOCO", 2019, "price_mean", None),
    ("SOCO", 2020, "price_mean", None),
    ("SOCO", 2022, "price_mean", None),
}


def _art(iso="SOCO", year=2019, coal_bit=45.0, attestation=True):
    """The clean PJM-scale fixture, re-keyed, with COAL_BIT moved to ``coal_bit``.

    Actual COAL_BIT is 55 TWh on a ~721 TWh system (volume band 8 TWh), so 45
    is a -10 TWh under-run FAIL and 65 a +10 TWh over-run FAIL. The bench
    keeps the fixture's clean avgLMP: since soco-84 (owner ruling 2026-09-28
    "Score C3a vs lambda") SOCO carries a price block and scores on the
    ordinary path, so the scoped row now lands on the CALIBRATED ladder.
    """
    d = DeterminationTests()
    ypay = d._clean_year_payload()
    ypay["gmModel"]["COAL_BIT"] = coal_bit
    kw = d._clean_bench_args()
    art = _artifacts(
        ypay,
        iso=iso,
        year=year,
        attestation=_clean_attestation() if attestation else None,
        **kw,
    )
    art["legitimacy"] = _legit_artifact(year=year, r=0.9, cv_ratio=0.02, share=0.05)
    return art


def _rec(v, year, key):
    """The fuelmix record for ``(year, key)`` in a verdict."""
    for r in v["criteria"]["fuelmix"]["records"]:
        if int(r["year"]) == year and r.get("key") == key:
            return r
    raise AssertionError(f"no fuelmix record {year} {key}")


class ScopedLedgerTests(unittest.TestCase):
    def test_table_is_exactly_one_row_and_c3c_guard_unchanged(self):
        self.assertEqual(set(cv.SCOPED_LEDGER_ENTRIES), {_KEY, *_C3A_KEYS})
        self.assertEqual(cv.LEDGERABLE_CRITERIA, frozenset({"price_tail"}))
        self.assertEqual(cv.MAX_LEDGERED_CAVEATS, 1)
        self.assertEqual(cv.SCOPED_LEDGER_ENTRIES[_KEY]["direction"], "under")

    def test_soco_2019_coal_bit_underrun_is_a_downgrading_ledgered_caveat(self):
        v = cv.determine_from_artifacts("t", _art())
        r = _rec(v, 2019, "COAL_BIT")
        self.assertEqual(r["status"], cv.CAVEAT)
        self.assertEqual(r["classification"], cv.MODEL_LIMIT)
        self.assertTrue(r["scoped_ledger"])
        self.assertIn("-10.00 TWh", r["magnitude"])  # full magnitude kept
        self.assertEqual(v["criteria"]["fuelmix"]["status"], cv.CAVEAT)
        self.assertEqual(v["criteria"]["fuelmix"]["caveat_kind"], "ledgered")
        self.assertEqual(v["grade_summary"]["ledgered"], 1)
        # It DOWNGRADES: the caveat rung, never the clean one.
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)
        self.assertIn("rubric v3.10/v3.11 scoped ledgered caveat", v["reasons"][0])
        self.assertFalse(
            any(
                "NOT determination-downgrading under rubric v3.3" in x
                for x in v["reasons"]
            )
        )

    def test_the_same_run_without_the_miss_is_clean(self):
        v = cv.determine_from_artifacts("t", _art(coal_bit=55.0))
        self.assertEqual(v["determination"], cv.CALIBRATED)

    def test_overrun_of_the_same_row_stays_fail(self):
        v = cv.determine_from_artifacts("t", _art(coal_bit=65.0))
        self.assertEqual(_rec(v, 2019, "COAL_BIT")["status"], cv.FAIL)
        self.assertEqual(v["determination"], cv.NOT_YET)

    def test_other_isos_do_not_match(self):
        for iso in ("PJM", "MISO", "NWPP", "ERCOT", "CAISO", "NYISO", "NEISO", "SPP"):
            with self.subTest(iso=iso):
                v = cv.determine_from_artifacts("t", _art(iso=iso))
                self.assertEqual(_rec(v, 2019, "COAL_BIT")["status"], cv.FAIL)
                self.assertEqual(v["determination"], cv.NOT_YET)

    def test_other_soco_years_do_not_match(self):
        for year in (2018, 2020, 2021, 2022, 2023, 2024, 2025):
            with self.subTest(year=year):
                v = cv.determine_from_artifacts("t", _art(year=year))
                r = _rec(v, year, "COAL_BIT")
                # FAIL, or SKIPPED where the committed EIA-923 completeness map
                # leaves the class ungated (a preliminary vintage) — never the
                # scoped CAVEAT.
                self.assertIn(r["status"], (cv.FAIL, cv.SKIPPED))
                self.assertNotIn("scoped_ledger", r)

    def test_other_soco_2019_class_does_not_match(self):
        d = DeterminationTests()
        ypay = d._clean_year_payload()
        ypay["gmModel"]["CC_REGULAR"] = 300.0  # -25 TWh under-run on CC
        kw = d._clean_bench_args()
        art = _artifacts(
            ypay, iso="SOCO", year=2019, attestation=_clean_attestation(), **kw
        )
        art["legitimacy"] = _legit_artifact(year=2019, r=0.9, cv_ratio=0.02, share=0.05)
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(_rec(v, 2019, "CC_REGULAR")["status"], cv.FAIL)
        self.assertEqual(v["determination"], cv.NOT_YET)

    def test_failing_governance_blocks_it(self):
        v = cv.determine_from_artifacts("t", _art(attestation=False))
        self.assertEqual(_rec(v, 2019, "COAL_BIT")["status"], cv.FAIL)
        self.assertEqual(v["determination"], cv.NOT_YET)

    def test_budget_is_checked_first(self):
        orig = cv.MAX_LEDGERED_CAVEATS
        cv.MAX_LEDGERED_CAVEATS = 0
        self.addCleanup(setattr, cv, "MAX_LEDGERED_CAVEATS", orig)
        v = cv.determine_from_artifacts("t", _art())
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertIn("caveat budget exceeded", v["reasons"][0])

    def test_attestation_ledger_entry_still_cannot_reach_c1(self):
        # An explicit exceptions-ledger entry for a C1 row anywhere else is
        # still ignored by the v3.1 guard — v3.10 widens nothing but its key.
        att = _clean_attestation(
            exceptions=[
                {"criterion": "fuelmix", "year": 2020, "key": "COAL_BIT", "reason": "x"}
            ]
        )
        art = _art(year=2020)
        art["attestation"] = att
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(_rec(v, 2020, "COAL_BIT")["status"], cv.FAIL)


def _c3a_art(year, actual_rt, iso="SOCO", attestation=True):
    """The clean fixture with C1 clean and the C3a actual moved to ``actual_rt``.

    The fixture's model mean is ~$29/MWh, so an actual of 25 is a +16 % over-run
    FAIL and 34 a -15 % under-run FAIL. The monthly actual stays flat at 29 so
    C3b is unaffected.
    """
    d = DeterminationTests()
    kw = d._clean_bench_args()
    kw["avg_lmp"] = {"rt": actual_rt, "rt_mon": [29] * 12}
    art = _artifacts(
        d._clean_year_payload(),
        iso=iso,
        year=year,
        attestation=_clean_attestation() if attestation else None,
        **kw,
    )
    art["legitimacy"] = _legit_artifact(year=year, r=0.9, cv_ratio=0.02, share=0.05)
    return art


def _c3a(v, year):
    """The C3a record for ``year`` in a verdict."""
    for r in v["criteria"]["price_mean"]["records"]:
        if int(r["year"]) == year:
            return r
    raise AssertionError(f"no price_mean record {year}")


class ScopedLedgerC3aTests(unittest.TestCase):
    """Rubric v3.11: the three SOCO C3a rows, each bound to its year's sign."""

    def test_directions(self):
        dirs = {k[1]: cv.SCOPED_LEDGER_ENTRIES[k]["direction"] for k in _C3A_KEYS}
        self.assertEqual(dirs, {2019: "over", 2020: "over", 2022: "under"})

    def test_rows_reach_in_their_own_direction_and_downgrade(self):
        for year, actual in ((2019, 25.0), (2020, 25.0), (2022, 34.0)):
            with self.subTest(year=year):
                v = cv.determine_from_artifacts("t", _c3a_art(year, actual))
                r = _c3a(v, year)
                self.assertEqual(r["status"], cv.CAVEAT)
                self.assertEqual(r["classification"], cv.MODEL_LIMIT)
                self.assertTrue(r["scoped_ledger"])
                self.assertEqual(v["grade_summary"]["ledgered"], 1)
                self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)
                self.assertIn("price_mean", v["reasons"][0])

    def test_wrong_sign_stays_fail(self):
        for year, actual in ((2019, 34.0), (2020, 34.0), (2022, 25.0)):
            with self.subTest(year=year):
                v = cv.determine_from_artifacts("t", _c3a_art(year, actual))
                self.assertEqual(_c3a(v, year)["status"], cv.FAIL)
                self.assertEqual(v["determination"], cv.NOT_YET)

    def test_other_soco_years_stay_fail(self):
        for year in (2021, 2023, 2024, 2025):
            for actual in (25.0, 34.0):
                with self.subTest(year=year, actual=actual):
                    v = cv.determine_from_artifacts("t", _c3a_art(year, actual))
                    self.assertEqual(_c3a(v, year)["status"], cv.FAIL)

    def test_other_isos_stay_fail(self):
        for iso in ("PJM", "MISO", "NWPP", "ERCOT", "CAISO", "NYISO", "NEISO", "SPP"):
            with self.subTest(iso=iso):
                v = cv.determine_from_artifacts("t", _c3a_art(2019, 25.0, iso=iso))
                self.assertEqual(_c3a(v, 2019)["status"], cv.FAIL)

    def test_failing_governance_blocks_it(self):
        v = cv.determine_from_artifacts("t", _c3a_art(2019, 25.0, attestation=False))
        self.assertEqual(_c3a(v, 2019)["status"], cv.FAIL)
        self.assertEqual(v["determination"], cv.NOT_YET)

    def test_c1_and_c3a_together_exceed_the_single_slot(self):
        art = _art(year=2019)
        art["bench"] = _c3a_art(2019, 25.0)["bench"]
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(_c3a(v, 2019)["status"], cv.CAVEAT)
        self.assertEqual(_rec(v, 2019, "COAL_BIT")["status"], cv.CAVEAT)
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertIn("caveat budget exceeded", v["reasons"][0])


if __name__ == "__main__":
    unittest.main()
