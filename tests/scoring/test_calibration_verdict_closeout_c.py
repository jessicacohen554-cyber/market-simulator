"""Rubric v3.14 / v3.16 — the close-out-C amendments (2026-10-02).

* v3.14 (owner ruling R-6): the ERCOT 2023 CONFIGURATION-EXCEPTION caveat kind.
  Exact-keyed, bound to the declared carve-out config the year solved on,
  direction-bound, governance-gated, never a PASS, off every caveat budget and
  NOT determination-downgrading; the IMM counterfactual is printed beside the
  actual. Nothing else moves.
* v3.16 (owner ruling R-9): NWPP's labelled benchmark starts in 2023, so a span
  of pre-2023 years reads PHYSICALLY-CALIBRATED (price unscored) and a mixed
  span scores price on the priced years only, naming the rest.

(v3.15, the SOCO reference-definition budget, is pinned in
``test_calibration_verdict_scoped_ledger.py``.)
"""

import unittest

from tests.scoring.test_calibration_verdict import (
    DeterminationTests,
    _artifacts,
    _clean_attestation,
    _legit_artifact,
    cv,
)

_CARVEOUT = {"outage_source": "historic", "ercot_offer_swcap_clip": True}
_FORWARD = {"outage_source": "historic", "ercot_offer_swcap_clip": False}
# The fixture model mean is ~$29/MWh: actual 40 is a -27 % under-run, 20 a
# +45 % over-run; alternating 19/39 monthly is a C3b NRMSE ~0.34 FAIL.
_SHAPE_FAIL = [19.0, 39.0] * 6


def _art(
    *,
    iso="ERCOT",
    year=2023,
    actual_rt=40.0,
    mon=None,
    config=_CARVEOUT,
    per_year=True,
    attestation=True,
    fuel_fail=False,
):
    """The clean fixture with C3a (and optionally C3b) failing for ``year``."""
    d = DeterminationTests()
    ypay = d._clean_year_payload()
    if fuel_fail:
        ypay["gmModel"]["CC_REGULAR"] = 360.0
    kw = d._clean_bench_args()
    kw["avg_lmp"] = {"rt": actual_rt, "rt_mon": list(mon or [actual_rt] * 12)}
    cfg = (
        {
            "scenario_config": {"outage_source": "historic"},
            "meta": {},
            "year_scenario_configs": {year: dict(config)},
        }
        if per_year
        else {"scenario_config": dict(config), "meta": {}}
    )
    art = _artifacts(
        ypay,
        iso=iso,
        year=year,
        config=cfg,
        attestation=_clean_attestation() if attestation else None,
        **kw,
    )
    art["legitimacy"] = _legit_artifact(year=year, r=0.9, cv_ratio=0.02, share=0.05)
    return art


def _rec(v, criterion, year):
    for r in v["criteria"][criterion]["records"]:
        if int(r["year"]) == year and r.get("key") is None:
            return r
    raise AssertionError(f"no {criterion} record {year}")


class ConfigExceptionTableTests(unittest.TestCase):
    def test_table_is_exactly_the_two_ercot_2023_rows(self):
        self.assertEqual(
            set(cv.CONFIG_EXCEPTION_ENTRIES),
            {
                ("ERCOT", 2023, "price_mean", None),
                ("ERCOT", 2023, "price_shape", None),
            },
        )
        self.assertEqual(cv.LEDGERABLE_CRITERIA, frozenset({"price_tail"}))
        self.assertEqual(cv.MAX_LEDGERED_CAVEATS, 1)
        self.assertEqual(cv.MAX_PROTECTIVE_CAVEATS, 0)


class ConfigExceptionTests(unittest.TestCase):
    def test_c3a_under_on_the_carveout_is_a_non_downgrading_caveat(self):
        v = cv.determine_from_artifacts("t", _art())
        r = _rec(v, "price_mean", 2023)
        self.assertEqual(r["status"], cv.CAVEAT)
        self.assertEqual(r["classification"], cv.CONFIG_EXCEPTION)
        self.assertTrue(r["config_exception"])
        self.assertTrue(r["magnitude"].startswith("-"))  # full magnitude kept
        self.assertEqual(
            v["criteria"]["price_mean"]["caveat_kind"], "configuration-exception"
        )
        self.assertIn("C3a mean LMP", v["caveats"]["configuration_exception"])
        self.assertEqual(v["caveats"]["ledgered"], [])
        self.assertEqual(v["determination"], cv.CALIBRATED)
        line = [x for x in v["reasons"] if "configuration-exception" in x]
        self.assertEqual(len(line), 1)
        self.assertIn("IMM counterfactual", line[0])
        self.assertIn("$35", line[0])

    def test_counterfactual_is_reported_beside_the_actual(self):
        v = cv.determine_from_artifacts("t", _art())
        cf = _rec(v, "price_mean", 2023)["counterfactual"]
        self.assertEqual(cf["ecrs_neutral_lw"], 35.0)
        self.assertEqual(tuple(cf["actual_lw_range"]), (62.0, 65.0))
        self.assertTrue(cf["model_vs_counterfactual"].startswith("-"))  # 29 < 35

    def test_c3b_above_band_is_covered_and_both_together_stay_clean(self):
        v = cv.determine_from_artifacts("t", _art(actual_rt=40.0, mon=_SHAPE_FAIL))
        self.assertEqual(
            _rec(v, "price_shape", 2023)["classification"], cv.CONFIG_EXCEPTION
        )
        self.assertEqual(
            _rec(v, "price_mean", 2023)["classification"], cv.CONFIG_EXCEPTION
        )
        # Two exception caveats spend no slot: still the clean rung.
        self.assertEqual(v["determination"], cv.CALIBRATED)

    def test_bundle_level_config_is_used_when_no_per_year_file(self):
        v = cv.determine_from_artifacts("t", _art(per_year=False))
        self.assertEqual(_rec(v, "price_mean", 2023)["status"], cv.CAVEAT)

    def test_per_year_config_wins_over_the_bundle_config(self):
        art = _art()
        art["config"]["scenario_config"]["ercot_offer_swcap_clip"] = True
        art["config"]["year_scenario_configs"][2023] = dict(_FORWARD)
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(_rec(v, "price_mean", 2023)["status"], cv.FAIL)

    def test_other_config_stays_fail(self):
        v = cv.determine_from_artifacts("t", _art(config=_FORWARD))
        self.assertEqual(_rec(v, "price_mean", 2023)["status"], cv.FAIL)
        self.assertEqual(v["determination"], cv.NOT_YET)

    def test_over_run_stays_fail(self):
        v = cv.determine_from_artifacts("t", _art(actual_rt=20.0))
        self.assertEqual(_rec(v, "price_mean", 2023)["status"], cv.FAIL)
        self.assertEqual(v["determination"], cv.NOT_YET)

    def test_other_years_stay_fail(self):
        for year in (2019, 2020, 2021, 2022, 2024, 2025):
            with self.subTest(year=year):
                v = cv.determine_from_artifacts("t", _art(year=year))
                self.assertEqual(_rec(v, "price_mean", year)["status"], cv.FAIL)

    def test_other_isos_stay_fail(self):
        for iso in ("PJM", "MISO", "CAISO", "NYISO", "NEISO", "SPP", "SOCO", "NWPP"):
            with self.subTest(iso=iso):
                v = cv.determine_from_artifacts("t", _art(iso=iso))
                self.assertNotEqual(
                    _rec(v, "price_mean", 2023).get("classification"),
                    cv.CONFIG_EXCEPTION,
                )

    def test_failing_governance_blocks_it(self):
        v = cv.determine_from_artifacts("t", _art(attestation=False))
        self.assertEqual(_rec(v, "price_mean", 2023)["status"], cv.FAIL)
        self.assertEqual(v["determination"], cv.NOT_YET)

    def test_a_second_failing_criterion_still_reads_not_yet(self):
        v = cv.determine_from_artifacts("t", _art(fuel_fail=True))
        self.assertEqual(_rec(v, "price_mean", 2023)["status"], cv.CAVEAT)
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertIn("fuelmix", v["reasons"][0])
        # ... and the exception is still named on the NOT-YET basis.
        self.assertTrue(any("configuration-exception" in x for x in v["reasons"]))


class LabelledReferenceStartTests(unittest.TestCase):
    """v3.16: NWPP years before the labelled reference start, per year."""

    def _nwpp(self, years, priced):
        d = DeterminationTests()
        kw = d._clean_bench_args()
        avg = kw.pop("avg_lmp")
        art = _artifacts(
            d._clean_year_payload(),
            iso="NWPP",
            year=years[0],
            attestation=_clean_attestation(),
            target_years=years,
            **kw,
        )
        base_bench = art["bench"][years[0]]
        base_pay = art["payload"]["years"][str(years[0])]
        art["bench"] = {}
        art["payload"]["years"] = {}
        for y in years:
            b = dict(base_bench)
            if y in priced:
                b["avgLMP"] = dict(avg)
            art["bench"][y] = b
            art["payload"]["years"][str(y)] = base_pay
        art["legitimacy"] = _legit_artifact(
            year=years[0], r=0.9, cv_ratio=0.02, share=0.05
        )
        return art

    def test_pre_reference_span_reads_physically_calibrated(self):
        v = cv.determine_from_artifacts("t", self._nwpp([2021], priced=()))
        self.assertIn(
            v["determination"],
            (cv.PHYSICALLY_CALIBRATED, cv.PHYSICALLY_CALIBRATED_CAVEATS),
        )
        self.assertIn("price_unscored", v)
        self.assertIn("begins in 2023", v["reasons"][-1])

    def test_priced_year_scores_on_the_ordinary_path(self):
        v = cv.determine_from_artifacts("t", self._nwpp([2024], priced=(2024,)))
        self.assertNotIn("price_unscored", v)
        self.assertEqual(v["criteria"]["price_mean"]["status"], cv.PASS)
        self.assertIn("WEIM ELAP", _rec(v, "price_mean", 2024)["metric"])
        self.assertEqual(v["criteria"]["price_tail"]["status"], cv.SKIPPED)

    def test_mixed_span_names_the_unpriced_years(self):
        v = cv.determine_from_artifacts("t", self._nwpp([2022, 2024], priced=(2024,)))
        self.assertNotIn("price_unscored", v)
        self.assertEqual(v["criteria"]["price_mean"]["status"], cv.PASS)
        self.assertTrue(
            any(r.startswith("PRICE UNSCORED in 2022") for r in v["reasons"])
        )

    def test_only_listed_isos_get_the_per_year_treatment(self):
        self.assertEqual(cv.LABELLED_PRICE_REFERENCE_FROM, {"NWPP": 2023})


if __name__ == "__main__":
    unittest.main()
