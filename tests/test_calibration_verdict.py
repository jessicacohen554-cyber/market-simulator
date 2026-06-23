"""Tests for the calibration determination scorer (scripts/calibration_verdict.py).

The per-criterion scorers and the determination decision logic are exercised on
synthetic payloads/benchmarks — no LP solve, no committed-artifact files — so the
rubric's pass/caveat/fail and quorum logic are pinned independently of any
particular keeper. The scorer is loaded by path (it lives under scripts/, not an
importable package).
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


def _clean_attestation(exceptions=None):
    """A governance attestation with all four assertions true."""
    return {
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
        },
        "exceptions": exceptions or [],
    }


def _artifacts(
    year_payload,
    classfull,
    *,
    iso="PJM",
    year=2024,
    e930=None,
    avg_lmp=None,
    config=None,
    attestation=None,
    target_years=None,
):
    """Build a synthetic artifacts dict for determine_from_artifacts."""
    bench = {"classFull": classfull, "e930": e930 or {}}
    if avg_lmp is not None:
        bench["avgLMP"] = avg_lmp
    return {
        "sidecar": {
            "id": "test-run",
            "iso": iso,
            "label": "test",
            "years": target_years or [year],
        },
        "payload": {"years": {str(year): year_payload}},
        "bench": {year: bench},
        "config": config
        if config is not None
        else {"scenario_config": {"outage_source": "historic"}, "meta": {}},
        "attestation": attestation,
    }


class FuelMixTests(unittest.TestCase):
    def test_big_class_percent_band(self):
        # 325 TWh actual, model 5% over -> FAIL; 3% over -> PASS.
        rows = cv.score_fuelmix(
            2024,
            {"gmModel": {"CC_REGULAR": 341.3}},
            {"classFull": {"CC_REGULAR": 325.0}},
        )
        cc = [r for r in rows if r["key"] == "CC_REGULAR"][0]
        self.assertEqual(cc["status"], cv.FAIL)
        self.assertEqual(cc["classification"], cv.MODEL_MISS)
        rows = cv.score_fuelmix(
            2024,
            {"gmModel": {"CC_REGULAR": 334.0}},
            {"classFull": {"CC_REGULAR": 325.0}},
        )
        cc = [r for r in rows if r["key"] == "CC_REGULAR"][0]
        self.assertEqual(cc["status"], cv.PASS)

    def test_small_class_absolute_band(self):
        # 8.9 TWh actual (<20): +1.26 TWh -> FAIL; +0.5 TWh -> PASS.
        rows = cv.score_fuelmix(
            2024, {"gmModel": {"ST_GAS": 10.16}}, {"classFull": {"ST_GAS": 8.9}}
        )
        sg = [r for r in rows if r["key"] == "ST_GAS"][0]
        self.assertEqual(sg["status"], cv.FAIL)
        rows = cv.score_fuelmix(
            2024, {"gmModel": {"ST_GAS": 9.4}}, {"classFull": {"ST_GAS": 8.9}}
        )
        sg = [r for r in rows if r["key"] == "ST_GAS"][0]
        self.assertEqual(sg["status"], cv.PASS)

    def test_ct_chp_excluded(self):
        rows = cv.score_fuelmix(
            2024, {"gmModel": {"CT_CHP": 0.0}}, {"classFull": {"CT_CHP": 4.0}}
        )
        self.assertFalse([r for r in rows if r["key"] == "CT_CHP"])


class SysVolTests(unittest.TestCase):
    def test_complete_vintage_uses_923_minus_btm(self):
        rows = cv.score_sysvol(
            2024,
            {"gmModel": {"CC_REGULAR": 384.9}},
            {"classFull": {"CC_REGULAR": 397.5}, "e930": {"gas": 368.4}},
        )
        gas = [r for r in rows if r["key"] == "gas"][0]
        self.assertEqual(gas["status"], cv.FAIL)  # -3.2% > 2.5%
        self.assertIn("923", gas["source"])
        self.assertFalse(gas["vintage_reconciled"])

    def test_preliminary_vintage_uses_930_and_flags_reconcile(self):
        # 2025: 923-BTM (360) well below 0.97 x 930 (372) -> reconcile fired,
        # actual = 930, model 370.8 vs 372.7 is within 2.5%.
        rows = cv.score_sysvol(
            2025,
            {"gmModel": {"CC_REGULAR": 370.8}},
            {"classFull": {"CC_REGULAR": 360.0}, "e930": {"gas": 372.7}},
        )
        gas = [r for r in rows if r["key"] == "gas"][0]
        self.assertEqual(gas["status"], cv.PASS)
        self.assertIn("930", gas["source"])
        self.assertTrue(gas["vintage_reconciled"])

    def test_immaterial_family_skipped(self):
        rows = cv.score_sysvol(
            2024,
            {"gmModel": {"COAL_BIT": 0.0}},
            {"classFull": {"COAL_BIT": 0.3}, "e930": {"coal": 0.3}},
        )
        coal = [r for r in rows if r["key"] == "coal"][0]
        self.assertEqual(coal["status"], cv.SKIPPED)


class PriceAndDispatchTests(unittest.TestCase):
    def test_mean_lmp_band(self):
        # -7.2% is within the ±8% band -> PASS.
        ypay = {"lmp": {"Z": {"p": 27.4, "d": 100.0}}}
        r = cv.score_price_mean(2024, ypay, {"avgLMP": {"rt": 29.53}})
        self.assertEqual(r["status"], cv.PASS)

    def test_mean_lmp_fail_when_far(self):
        ypay = {"lmp": {"Z": {"p": 35.4, "d": 100.0}}}
        r = cv.score_price_mean(2024, ypay, {"avgLMP": {"rt": 42.9}})
        self.assertEqual(r["status"], cv.FAIL)  # -17.5%

    def test_tail_skipped_without_ordc(self):
        r = cv.score_price_tail(2024, {"lmp": {}}, "PJM")
        self.assertEqual(r["status"], cv.SKIPPED)

    def test_tail_collapsed_fails(self):
        ypay = {"ordc": {"hoursGt200": {"actual": 100, "model": 0}}}
        r = cv.score_price_tail(2024, ypay, "ERCOT")
        self.assertEqual(r["status"], cv.FAIL)

    def test_tail_within_band_passes(self):
        # model 130h vs actual 100h = 1.30x, inside [0.5x, 2x] -> PASS.
        ypay = {"ordc": {"hoursGt200": {"actual": 100, "model": 130}}}
        r = cv.score_price_tail(2024, ypay, "NEISO")
        self.assertEqual(r["status"], cv.PASS)
        # NEISO tail is the >$300 proxy (rubric §5), surfaced in the metric label.
        self.assertIn("300", r["metric"])

    def test_tail_over_fired_fails(self):
        # model 250h vs actual 100h = 2.5x, above 2x ceiling -> FAIL.
        ypay = {"ordc": {"hoursGt200": {"actual": 100, "model": 250}}}
        r = cv.score_price_tail(2024, ypay, "PJM")
        self.assertEqual(r["status"], cv.FAIL)
        self.assertEqual(r["classification"], cv.MODEL_MISS)

    def test_tail_quiet_actual_passes_when_model_quiet(self):
        # Actual ~0 scarcity hours: a quiet model tail can't be over/under-shot.
        ypay = {"ordc": {"hoursGt200": {"actual": 0, "model": 3}}}
        r = cv.score_price_tail(2024, ypay, "NEISO")
        self.assertEqual(r["status"], cv.PASS)

    def test_tail_invented_against_quiet_actual_fails(self):
        # Actual ~0 but the model invents a large tail -> FAIL (token guard).
        ypay = {"ordc": {"hoursGt200": {"actual": 0, "model": 200}}}
        r = cv.score_price_tail(2024, ypay, "NEISO")
        self.assertEqual(r["status"], cv.FAIL)


class StorageTests(unittest.TestCase):
    def test_skipped_without_series(self):
        # No model and no actual throughput committed -> SKIPPED, never a pass.
        r = cv.score_storage(2024, {}, {})
        self.assertEqual(r["status"], cv.SKIPPED)

    def test_skipped_when_only_model_present(self):
        # Model emitted but the BA reports no storage breakout (NEISO 2023):
        # actual absent -> SKIPPED, not scored against a missing actual.
        r = cv.score_storage(2023, {"storage": {"throughput_twh": 0.34}}, {})
        self.assertEqual(r["status"], cv.SKIPPED)

    def test_within_band_passes(self):
        # model 1.15 vs actual 1.0 = +15%, inside +/-30% -> PASS.
        r = cv.score_storage(
            2024,
            {"storage": {"throughput_twh": 1.15}},
            {"storage": {"throughput_twh": 1.0}},
        )
        self.assertEqual(r["status"], cv.PASS)

    def test_over_cycling_fails(self):
        # model 0.46 vs actual 0.31 = +47% -> FAIL (MODEL MISS, needs an adder).
        r = cv.score_storage(
            2024,
            {"storage": {"throughput_twh": 0.46}},
            {"storage": {"throughput_twh": 0.31}},
        )
        self.assertEqual(r["status"], cv.FAIL)
        self.assertEqual(r["classification"], cv.MODEL_MISS)

    def test_under_cycling_fails(self):
        # model 0.56 vs actual 2.08 = -73% -> FAIL (model under-cycles PS).
        r = cv.score_storage(
            2025,
            {"storage": {"throughput_twh": 0.56}},
            {"storage": {"throughput_twh": 2.08}},
        )
        self.assertEqual(r["status"], cv.FAIL)

    def test_dispatch_corr_floor(self):
        ypay = {
            "fuelRows": [{"fuel": "gas", "m": 380, "b": 360, "r": 0.55, "nrmse": 0.16}]
        }
        gas = [r for r in cv.score_dispatch_corr(2024, ypay) if r["key"] == "gas"][0]
        self.assertEqual(gas["status"], cv.FAIL)  # r 0.55 < 0.70

    def test_dispatch_corr_immaterial_skipped(self):
        ypay = {
            "fuelRows": [{"fuel": "coal", "m": 0.3, "b": 0.3, "r": 0.0, "nrmse": 3.0}]
        }
        coal = [r for r in cv.score_dispatch_corr(2024, ypay) if r["key"] == "coal"][0]
        self.assertEqual(coal["status"], cv.SKIPPED)


class GovernanceTests(unittest.TestCase):
    def test_unattested(self):
        g = cv.score_governance(
            {"scenario_config": {"outage_source": "historic"}}, None
        )
        self.assertEqual(g["status"], "UNATTESTED")

    def test_pass(self):
        g = cv.score_governance(
            {"scenario_config": {"outage_source": "historic"}}, _clean_attestation()
        )
        self.assertEqual(g["status"], cv.PASS)

    def test_false_assertion_fails(self):
        att = _clean_attestation()
        att["governance"]["no_pinning_to_actuals"] = False
        g = cv.score_governance({"scenario_config": {}}, att)
        self.assertEqual(g["status"], cv.FAIL)

    def test_bad_outage_source_fails(self):
        g = cv.score_governance(
            {"scenario_config": {"outage_source": "fitted"}}, _clean_attestation()
        )
        self.assertEqual(g["status"], cv.FAIL)


class LedgerTests(unittest.TestCase):
    def test_documented_fail_becomes_caveat(self):
        rec = {
            "criterion": "fuelmix",
            "key": "CT_PEAKER",
            "year": 2024,
            "status": cv.FAIL,
            "classification": cv.MODEL_MISS,
        }
        cv._apply_ledger(
            rec,
            [
                {
                    "criterion": "fuelmix",
                    "klass": "CT_PEAKER",
                    "year": 2024,
                    "reason": "NEISO model-zeroed peaker",
                }
            ],
        )
        self.assertEqual(rec["status"], cv.CAVEAT)
        self.assertEqual(rec["classification"], cv.MEASURED_LIMIT)

    def test_unmatched_fail_stays_fail(self):
        rec = {
            "criterion": "fuelmix",
            "key": "CT_PEAKER",
            "year": 2024,
            "status": cv.FAIL,
            "classification": cv.MODEL_MISS,
        }
        cv._apply_ledger(rec, [{"criterion": "sysvol", "family": "gas", "year": 2024}])
        self.assertEqual(rec["status"], cv.FAIL)


class DeterminationTests(unittest.TestCase):
    def _clean_year_payload(self):
        # All scored criteria pass; tail/co2/storage skip (no data).
        return {
            "gmModel": {"CC_REGULAR": 330.0, "COAL_BIT": 100.0},
            "fuelRows": [
                {"fuel": "gas", "m": 330, "b": 325, "r": 0.8, "nrmse": 0.15},
                {"fuel": "coal", "m": 100, "b": 100, "r": 0.9, "nrmse": 0.15},
            ],
            "lmp": {
                "Z": {"p": 29.0, "d": 100.0, "pMon": [29] * 12, "dMon": [8.3] * 12}
            },
        }

    def _clean_bench_args(self):
        return dict(
            classfull={"CC_REGULAR": 325.0, "COAL_BIT": 100.0},
            e930={"gas": 325.0, "coal": 100.0},
            avg_lmp={"rt": 29.0, "rt_mon": [29] * 12},
        )

    def test_unattested_is_not_yet(self):
        art = _artifacts(self._clean_year_payload(), **self._clean_bench_args())
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["determination"], cv.NOT_YET)

    def test_clean_attested_with_skips_is_caveats(self):
        art = _artifacts(
            self._clean_year_payload(),
            attestation=_clean_attestation(),
            **self._clean_bench_args(),
        )
        v = cv.determine_from_artifacts("t", art)
        # Hard gates + scored soft pass, governance attested, but tail/co2/storage
        # are unscored -> capped at CALIBRATED-WITH-CAVEATS.
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)

    def test_undocumented_fail_forces_not_yet(self):
        ypay = self._clean_year_payload()
        ypay["gmModel"]["CC_REGULAR"] = 360.0  # +10.8% on a big class -> FAIL
        art = _artifacts(
            ypay, attestation=_clean_attestation(), **self._clean_bench_args()
        )
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["determination"], cv.NOT_YET)

    def test_documented_fail_within_budget_is_caveats(self):
        # ST_GAS is small (<20 TWh): a +1.5 TWh per-class miss FAILs C1 but leaves
        # the gas family within ±2.5% (so C2 still PASSes) -> a single isolated
        # hard-gate fail, ledgered -> CAVEAT within budget.
        ypay = {
            "gmModel": {"CC_REGULAR": 330.0, "ST_GAS": 10.4, "COAL_BIT": 100.0},
            "fuelRows": [
                {"fuel": "gas", "m": 340, "b": 334, "r": 0.8, "nrmse": 0.15},
                {"fuel": "coal", "m": 100, "b": 100, "r": 0.9, "nrmse": 0.15},
            ],
            "lmp": {
                "Z": {"p": 29.0, "d": 100.0, "pMon": [29] * 12, "dMon": [8.3] * 12}
            },
        }
        att = _clean_attestation(
            exceptions=[
                {
                    "criterion": "fuelmix",
                    "klass": "ST_GAS",
                    "year": 2024,
                    "magnitude": "+1.5 TWh",
                    "reason": "documented measured-input limit",
                }
            ]
        )
        art = _artifacts(
            ypay,
            classfull={"CC_REGULAR": 325.0, "ST_GAS": 8.9, "COAL_BIT": 100.0},
            e930={"gas": 333.9, "coal": 100.0},
            avg_lmp={"rt": 29.0, "rt_mon": [29] * 12},
            attestation=att,
        )
        v = cv.determine_from_artifacts("t", art)
        # One hard-gate caveat is within the budget (<=1) -> CALIBRATED-WITH-CAVEATS.
        self.assertEqual(v["criteria"]["fuelmix"]["status"], cv.CAVEAT)
        self.assertEqual(v["criteria"]["sysvol"]["status"], cv.PASS)
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)

    def test_data_blocked_year_recorded(self):
        art = _artifacts(
            self._clean_year_payload(),
            attestation=_clean_attestation(),
            target_years=[2023, 2024],  # 2023 absent from payload
            **self._clean_bench_args(),
        )
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["data_blocked_years"], [2023])
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)


if __name__ == "__main__":
    unittest.main()
