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


def _completeness(isos, families):
    """Build a synthetic 2025 EIA-923 completeness map and load it into the scorer.

    ``isos`` is ``{iso: {class: gate_bool}}`` (status derived from the gate) and
    ``families`` is ``{iso: {fam: complete_bool}}``. Sets ``cv._COMPLETENESS_CACHE``
    directly so the scorer reads this map instead of the committed parts — keeping
    the gating tests hermetic. Call :func:`_reset_completeness` to restore.
    """
    iso_map = {
        iso: {
            klass: {
                "status": "complete" if gate else "incomplete",
                "gate": gate,
                "reasons": [] if gate else ["synthetic incomplete"],
            }
            for klass, gate in classes.items()
        }
        for iso, classes in isos.items()
    }
    cv._COMPLETENESS_CACHE = {2025: {"isos": iso_map, "families": families}}


def _reset_completeness():
    """Drop the injected completeness map so the next read reloads from disk."""
    cv._COMPLETENESS_CACHE = None


def _pjm_mix(model=None):
    """Realistic full-PJM fuel mix (TWh) -> ``(ypay, ybench)`` for score_fuelmix.

    The universal class gate scales its volume band with the ISO's TOTAL annual
    generation (``_gen_totals``), so the fixture must carry the whole mix —
    fossil classes plus the non-fossil families (nuclear/wind/solar) — not a
    single class that would collapse ``a_gen`` onto itself. Matching the real
    render, ``classFull`` and ``gmModel`` each span fossil AND non-fossil classes
    (wind/solar on the EIA-930 grid basis, nuclear on EIA-923), and
    ``_gen_totals`` counts each class once over ``classFull``. Here a_gen ≈ 721
    TWh, so 1.0% would be ≈ 7.2 TWh but the band is capped at 5 TWh ->
    ``min(7.2, 5) = 5 TWh``. Pass ``model`` to override one or more model classes;
    everything else is modelled exactly on the actual.
    """
    actual = {"CC_REGULAR": 325.0, "CT_PEAKER": 20.0, "ST_GAS": 9.0, "COAL_BIT": 55.0}
    nonfossil = {"nuclear": 270.0, "wind": 28.0, "solar": 14.0}
    # classFull/gmModel span every class (the count-once basis); wind/solar are
    # already grid-delivered (= EIA-930) here, so they enter the total once.
    classfull = {**actual, **nonfossil}
    gm = {**actual, **nonfossil}
    if model:
        gm.update(model)
    ypay = {"gmModel": gm, "nonfossil": dict(nonfossil)}
    ybench = {"classFull": dict(classfull), "e930": dict(nonfossil)}
    return ypay, ybench


class FuelMixTests(unittest.TestCase):
    def test_big_class_percent_band(self):
        # CC_REGULAR 325 TWh actual in a ~721 TWh ISO: the universal volume band
        # is min(2.0% of ISO load, 8 TWh) = 8 TWh (the 8 TWh cap binds). +9 TWh
        # exceeds it -> FAIL on volume; +8 TWh sits exactly on the cap -> PASS
        # (pins the 2026-07-02 loosening: the old 5 TWh cap failed a +8 miss).
        ypay, ybench = _pjm_mix({"CC_REGULAR": 334.0})
        rows = cv.score_fuelmix(2024, ypay, ybench)
        cc = [r for r in rows if r["key"] == "CC_REGULAR"][0]
        self.assertEqual(cc["status"], cv.FAIL)
        self.assertEqual(cc["classification"], cv.MODEL_MISS)
        ypay, ybench = _pjm_mix({"CC_REGULAR": 333.0})
        rows = cv.score_fuelmix(2024, ypay, ybench)
        cc = [r for r in rows if r["key"] == "CC_REGULAR"][0]
        self.assertEqual(cc["status"], cv.PASS)

    def test_small_class_absolute_band(self):
        # Small classes get the SAME universal volume band — min(2.0% of ISO load,
        # 8 TWh), here capped at 8 TWh — not the obsolete ±1 TWh size-tiered bar:
        # ST_GAS 9 TWh actual with a +1.26 TWh miss PASSES (small-class TWh noise
        # is not a structural miss), while a +9 TWh miss exceeds the 8 TWh cap ->
        # FAIL (the cap stops a small class drifting far on the margin and still
        # passing).
        ypay, ybench = _pjm_mix({"ST_GAS": 18.0})
        rows = cv.score_fuelmix(2024, ypay, ybench)
        sg = [r for r in rows if r["key"] == "ST_GAS"][0]
        self.assertEqual(sg["status"], cv.FAIL)
        ypay, ybench = _pjm_mix({"ST_GAS": 10.26})
        rows = cv.score_fuelmix(2024, ypay, ybench)
        sg = [r for r in rows if r["key"] == "ST_GAS"][0]
        self.assertEqual(sg["status"], cv.PASS)

    def test_ct_chp_excluded(self):
        rows = cv.score_fuelmix(
            2024, {"gmModel": {"CT_CHP": 0.0}}, {"classFull": {"CT_CHP": 4.0}}
        )
        self.assertFalse([r for r in rows if r["key"] == "CT_CHP"])

    def test_preliminary_incomplete_class_skipped(self):
        # A preliminary-EIA-923 vintage class whose plant data the completeness
        # audit flags INCOMPLETE has no trustworthy per-class actual to gate
        # against, so it is SKIPPED regardless of miss size (even a +9 TWh
        # over-absorption that would FAIL in a complete-vintage year). The raw gap
        # is kept as a report-only annotation that does not gate.
        _completeness(
            {"ERCOT": {"CC_REGULAR": False}}, {"ERCOT": {"gas": False, "coal": False}}
        )
        try:
            ypay, ybench = _pjm_mix({"CC_REGULAR": 334.0})
            rows = cv.score_fuelmix(2025, ypay, ybench, "ERCOT")
            cc = [r for r in rows if r["key"] == "CC_REGULAR"][0]
            self.assertEqual(cc["status"], cv.SKIPPED)
            self.assertIsNone(cc["classification"])
            self.assertAlmostEqual(cc["vintage_gap_twh"], 9.0, places=3)
            self.assertIn("incomplete plant data", cc["magnitude"])
            self.assertEqual(cc["completeness"], "incomplete")
            # A large miss is still SKIPPED, never FAIL.
            ypay, ybench = _pjm_mix({"CC_REGULAR": 360.0})  # +35 TWh
            rows = cv.score_fuelmix(2025, ypay, ybench, "ERCOT")
            cc = [r for r in rows if r["key"] == "CC_REGULAR"][0]
            self.assertEqual(cc["status"], cv.SKIPPED)
        finally:
            _reset_completeness()

    def test_preliminary_complete_class_gated(self):
        # A preliminary-vintage class the audit flags COMPLETE (its plants all
        # reported AND its family fully reported) gates exactly like a
        # complete-vintage year: a +9 TWh CC_REGULAR miss FAILs / MODEL MISS, a
        # +3 TWh miss PASSes. Only the verified-complete classes gate in 2025.
        _completeness(
            {"ERCOT": {"CC_REGULAR": True}}, {"ERCOT": {"gas": True, "coal": False}}
        )
        try:
            ypay, ybench = _pjm_mix({"CC_REGULAR": 334.0})  # +9 TWh
            rows = cv.score_fuelmix(2025, ypay, ybench, "ERCOT")
            cc = [r for r in rows if r["key"] == "CC_REGULAR"][0]
            self.assertEqual(cc["status"], cv.FAIL)
            self.assertEqual(cc["classification"], cv.MODEL_MISS)
            self.assertEqual(cc["completeness"], "complete")
            self.assertNotIn("vintage_gap_twh", cc)
            ypay, ybench = _pjm_mix({"CC_REGULAR": 328.0})  # +3 TWh
            rows = cv.score_fuelmix(2025, ypay, ybench, "ERCOT")
            cc = [r for r in rows if r["key"] == "CC_REGULAR"][0]
            self.assertEqual(cc["status"], cv.PASS)
        finally:
            _reset_completeness()

    def test_complete_vintage_year_still_gated(self):
        # 2024 is a complete-vintage year (< PRELIM_923_FROM_YEAR): the same +9 TWh
        # CC_REGULAR miss is gated normally -> FAIL / MODEL MISS, while a +3 TWh miss
        # stays inside the band -> PASS.
        ypay, ybench = _pjm_mix({"CC_REGULAR": 334.0})
        rows = cv.score_fuelmix(2024, ypay, ybench)
        cc = [r for r in rows if r["key"] == "CC_REGULAR"][0]
        self.assertEqual(cc["status"], cv.FAIL)
        self.assertEqual(cc["classification"], cv.MODEL_MISS)
        self.assertNotIn("vintage_gap_twh", cc)
        ypay, ybench = _pjm_mix({"CC_REGULAR": 328.0})
        rows = cv.score_fuelmix(2024, ypay, ybench)
        cc = [r for r in rows if r["key"] == "CC_REGULAR"][0]
        self.assertEqual(cc["status"], cv.PASS)


class SysVolTests(unittest.TestCase):
    def test_complete_vintage_defers_to_c1_no_family_band(self):
        # Complete vintage: C2 no longer applies a percent-of-family band. The
        # per-class universal gate (C1) governs, so C2 PASSES (defers) but still
        # surfaces any per-class breach in its magnitude for visibility. Here
        # CC_REGULAR is -12.6 TWh, far outside the 1.0%-ISO-gen volume band, so C1
        # flags it — and the determination fails via C1.fuelmix, not C2.sysvol.
        rows = cv.score_sysvol(
            2024,
            {"gmModel": {"CC_REGULAR": 384.9}},
            {"classFull": {"CC_REGULAR": 397.5}, "e930": {"gas": 368.4}},
        )
        gas = [r for r in rows if r["key"] == "gas"][0]
        self.assertEqual(gas["status"], cv.PASS)  # defers to C1, no family band
        self.assertIn("via C1", gas["source"])
        self.assertIn("CC_REGULAR", gas["magnitude"])  # breach surfaced, not netted
        self.assertFalse(gas["vintage_reconciled"])

    def test_complete_vintage_no_invented_fail_no_masking(self):
        # The two failure modes the fold-in retires, on one ISO-year:
        #   (a) NO INVENTED FAIL — coal family is +1.75 TWh (=+3.0% of a 58 TWh
        #       family, which the old ±2.5% band failed) but each coal class is
        #       inside the 1.0%-ISO-gen volume + 1.5pp share band -> C2 PASS.
        #   (b) NO MASKING — gas family nets to ~0 (CT_PEAKER +6.8 offset by
        #       CC_REGULAR -6.9) yet CT_PEAKER is far out of band; C2 surfaces it
        #       (and C1 fails it) instead of hiding it behind the netted family.
        gm = {
            "CC_REGULAR": 143.0 - 6.9,
            "CT_PEAKER": 7.4 + 6.8,
            "COAL_PRB": 44.0,
            "COAL_LIGNITE": 15.4,
        }
        cf = {
            "classFull": {
                "CC_REGULAR": 143.0,
                "CT_PEAKER": 7.4,
                "COAL_PRB": 43.7,
                "COAL_LIGNITE": 13.9,
            },
            "e930": {
                "gas": 198.5,
                "coal": 58.8,
                "nuclear": 45.0,
                "wind": 110.0,
                "solar": 47.0,
            },
        }
        rows = cv.score_sysvol(2024, {"gmModel": gm}, cf)
        coal = [r for r in rows if r["key"] == "coal"][0]
        gas = [r for r in rows if r["key"] == "gas"][0]
        self.assertEqual(coal["status"], cv.PASS)  # (a) not invented
        self.assertIn("CT_PEAKER", gas["magnitude"])  # (b) not masked

    def test_preliminary_incomplete_family_uses_930_and_flags_reconcile(self):
        # 2025 gas family flagged INCOMPLETE by the audit: no per-class actual, so
        # C2 falls back to the EIA-930 family aggregate. 923-BTM (360) well below
        # 0.97 x 930 (372) -> reconcile fired, actual = 930, model 370.8 vs 372.7
        # is within 2.5%.
        _completeness({"ERCOT": {}}, {"ERCOT": {"gas": False, "coal": False}})
        try:
            rows = cv.score_sysvol(
                2025,
                {"gmModel": {"CC_REGULAR": 370.8}},
                {"classFull": {"CC_REGULAR": 360.0}, "e930": {"gas": 372.7}},
                "ERCOT",
            )
            gas = [r for r in rows if r["key"] == "gas"][0]
            self.assertEqual(gas["status"], cv.PASS)
            self.assertIn("930", gas["source"])
            self.assertTrue(gas["vintage_reconciled"])
        finally:
            _reset_completeness()

    def test_preliminary_complete_family_defers_to_c1(self):
        # A 2025 family the audit flags COMPLETE defers to the C1 per-class gate
        # exactly like a complete vintage — no EIA-930 family fallback. Here coal
        # is fully reported, so C2.coal PASSES via C1 and surfaces no 930 source.
        _completeness(
            {"ERCOT": {"COAL_PRB": True}}, {"ERCOT": {"gas": False, "coal": True}}
        )
        try:
            rows = cv.score_sysvol(
                2025,
                {"gmModel": {"COAL_PRB": 44.0}},
                {"classFull": {"COAL_PRB": 43.7}, "e930": {"coal": 43.7}},
                "ERCOT",
            )
            coal = [r for r in rows if r["key"] == "coal"][0]
            self.assertEqual(coal["status"], cv.PASS)
            self.assertIn("via C1", coal["source"])
            self.assertFalse(coal["vintage_reconciled"])
        finally:
            _reset_completeness()

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
        # -3.8% is within the ±5% band -> PASS; -7.2% (a pass under the old ±8%)
        # now FAILs — pins the 2026-07-02 tightening.
        ypay = {"lmp": {"Z": {"p": 28.4, "d": 100.0}}}
        r = cv.score_price_mean(2024, ypay, {"avgLMP": {"rt": 29.53}})
        self.assertEqual(r["status"], cv.PASS)
        ypay = {"lmp": {"Z": {"p": 27.4, "d": 100.0}}}
        r = cv.score_price_mean(2024, ypay, {"avgLMP": {"rt": 29.53}})
        self.assertEqual(r["status"], cv.FAIL)

    def test_mean_lmp_fail_when_far(self):
        ypay = {"lmp": {"Z": {"p": 35.4, "d": 100.0}}}
        r = cv.score_price_mean(2024, ypay, {"avgLMP": {"rt": 42.9}})
        self.assertEqual(r["status"], cv.FAIL)  # -17.5%

    def test_price_shape_nrmse_band(self):
        # Flat monthly vectors: model 31.9 vs actual 29 -> NRMSE = 0.10 <= 0.15
        # PASS; model 33.93 -> NRMSE = 0.17, a pass under the old 0.20 ceiling,
        # now FAILs — pins the 2026-07-02 tightening.
        def ypay(pm):
            return {"lmp": {"Z": {"pMon": [pm] * 12, "dMon": [8.3] * 12}}}

        bench = {"avgLMP": {"rt_mon": [29.0] * 12}}
        r = cv.score_price_shape(2024, ypay(31.9), bench)
        self.assertEqual(r["status"], cv.PASS)
        r = cv.score_price_shape(2024, ypay(33.93), bench)
        self.assertEqual(r["status"], cv.FAIL)

    def test_tail_skipped_without_ordc(self):
        r = cv.score_price_tail(2024, {"lmp": {}}, "PJM")
        self.assertEqual(r["status"], cv.SKIPPED)

    def test_tail_collapsed_fails(self):
        ypay = {"ordc": {"hoursGt200": {"actual": 100, "model": 0}}}
        r = cv.score_price_tail(2024, ypay, "ERCOT")
        self.assertEqual(r["status"], cv.FAIL)

    def test_tail_within_band_passes(self):
        # model 130h vs actual 100h = 1.30x, inside [0.7x, 1.5x] -> PASS.
        ypay = {"ordc": {"hoursGt200": {"actual": 100, "model": 130}}}
        r = cv.score_price_tail(2024, ypay, "NEISO")
        self.assertEqual(r["status"], cv.PASS)
        # NEISO tail is the >$300 proxy (rubric §5), surfaced in the metric label.
        self.assertIn("300", r["metric"])

    def test_tail_over_fired_fails(self):
        # model 160h vs actual 100h = 1.6x, above the 1.5x ceiling -> FAIL
        # (a pass under the old 2x ceiling — pins the 2026-07-02 tightening).
        ypay = {"ordc": {"hoursGt200": {"actual": 100, "model": 160}}}
        r = cv.score_price_tail(2024, ypay, "PJM")
        self.assertEqual(r["status"], cv.FAIL)
        self.assertEqual(r["classification"], cv.MODEL_MISS)

    def test_tail_under_fired_fails(self):
        # model 60h vs actual 100h = 0.6x, below the 0.7x floor -> FAIL
        # (a pass under the old 0.5x floor — pins the 2026-07-02 tightening).
        ypay = {"ordc": {"hoursGt200": {"actual": 100, "model": 60}}}
        r = cv.score_price_tail(2024, ypay, "PJM")
        self.assertEqual(r["status"], cv.FAIL)

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
        # A full PJM-scale mix (a_gen ≈ 721 TWh) where every fossil class is
        # within the universal gate (CC +1 TWh, the rest exact): all scored
        # criteria pass; tail/co2/storage skip (no data).
        return {
            "gmModel": {
                "CC_REGULAR": 326.0,
                "CT_PEAKER": 20.0,
                "ST_GAS": 9.0,
                "COAL_BIT": 55.0,
            },
            "nonfossil": {"nuclear": 270.0, "wind": 28.0, "solar": 14.0},
            "fuelRows": [
                {"fuel": "gas", "m": 355, "b": 354, "r": 0.8, "nrmse": 0.15},
                {"fuel": "coal", "m": 55, "b": 55, "r": 0.9, "nrmse": 0.15},
            ],
            "lmp": {
                "Z": {"p": 29.0, "d": 100.0, "pMon": [29] * 12, "dMon": [8.3] * 12}
            },
        }

    def _clean_bench_args(self):
        return dict(
            classfull={
                "CC_REGULAR": 325.0,
                "CT_PEAKER": 20.0,
                "ST_GAS": 9.0,
                "COAL_BIT": 55.0,
            },
            e930={
                "gas": 354.0,
                "coal": 55.0,
                "nuclear": 270.0,
                "wind": 28.0,
                "solar": 14.0,
            },
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
        # ST_GAS (9 TWh actual) overshoots by +5 TWh: the fixture's lmp zone demand
        # is 100 TWh, so the volume band = min(2.0% of load, 8 TWh) = 2.0 TWh and
        # the +5 TWh miss still exceeds it -> the class FAILs C1 on volume (share
        # stays within 3.0pp), but C2 defers to C1 for the fully-reported family
        # so it still PASSes -> a single isolated hard-gate fail, ledgered ->
        # CAVEAT in budget.
        ypay = {
            "gmModel": {
                "CC_REGULAR": 325.0,
                "CT_PEAKER": 20.0,
                "ST_GAS": 14.0,
                "COAL_BIT": 55.0,
            },
            "nonfossil": {"nuclear": 270.0, "wind": 28.0, "solar": 14.0},
            "fuelRows": [
                {"fuel": "gas", "m": 359, "b": 354, "r": 0.8, "nrmse": 0.15},
                {"fuel": "coal", "m": 55, "b": 55, "r": 0.9, "nrmse": 0.15},
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
                    "magnitude": "+5.0 TWh",
                    "reason": "documented measured-input limit",
                }
            ]
        )
        art = _artifacts(
            ypay,
            classfull={
                "CC_REGULAR": 325.0,
                "CT_PEAKER": 20.0,
                "ST_GAS": 9.0,
                "COAL_BIT": 55.0,
            },
            e930={
                "gas": 354.0,
                "coal": 55.0,
                "nuclear": 270.0,
                "wind": 28.0,
                "solar": 14.0,
            },
            avg_lmp={"rt": 29.0, "rt_mon": [29] * 12},
            attestation=att,
        )
        v = cv.determine_from_artifacts("t", art)
        # One hard-gate caveat is within the budget (<=1) -> CALIBRATED-WITH-CAVEATS.
        self.assertEqual(v["criteria"]["fuelmix"]["status"], cv.CAVEAT)
        self.assertEqual(v["criteria"]["sysvol"]["status"], cv.PASS)
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)

    def test_soft_caveat_budget_is_two(self):
        # Pins MAX_SOFT_CAVEATS = 2 (2026-07-02 re-balance, Option A: C3 stays
        # SOFT but price can no longer be caveated as freely). Three ledgered
        # soft caveats (price_mean -10.3%, price_tail 2.0x, storage +50%) exceed
        # the budget -> NOT-YET; dropping the storage caveat (model back in band)
        # leaves two -> CALIBRATED-WITH-CAVEATS.
        def art_with(storage_model):
            ypay = self._clean_year_payload()
            ypay["lmp"]["Z"]["p"] = 26.0  # -10.3% vs rt 29.0 -> price_mean FAIL
            ypay["lmp"]["Z"]["pMon"] = [26] * 12  # NRMSE 0.103 <= 0.15 -> shape PASS
            ypay["ordc"] = {"hoursGt200": {"actual": 100, "model": 200}}  # 2.0x FAIL
            ypay["storage"] = {"throughput_twh": storage_model}
            att = _clean_attestation(
                exceptions=[
                    {"criterion": "price_mean", "year": 2024, "reason": "documented"},
                    {"criterion": "price_tail", "year": 2024, "reason": "documented"},
                    {"criterion": "storage", "year": 2024, "reason": "documented"},
                ]
            )
            art = _artifacts(ypay, attestation=att, **self._clean_bench_args())
            art["bench"][2024]["storage"] = {"throughput_twh": 1.0}
            return art

        v = cv.determine_from_artifacts("t", art_with(1.5))  # +50% -> 3rd caveat
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertIn("caveat budget exceeded", v["reasons"][0])
        v = cv.determine_from_artifacts("t", art_with(1.15))  # +15% in band -> 2
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
