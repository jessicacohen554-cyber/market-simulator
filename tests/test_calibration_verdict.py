"""Tests for the calibration determination scorer (scripts/calibration_verdict.py).

The per-criterion scorers and the determination decision logic are exercised on
synthetic payloads/benchmarks — no LP solve, no committed-artifact files — so the
rubric's pass/caveat/fail and quorum logic are pinned independently of any
particular keeper. The scorer is loaded by path (it lives under scripts/, not an
importable package).
"""

import importlib.util
import itertools
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


def _tail(isos):
    """Inject a synthetic actual-tail part (C3c DA-expressible benchmark).

    ``isos`` is ``{iso: {year(str): {"da_gt": int, "rt_gt": int, ...}}}`` —
    the shape of ``frontend/data/backcast/tail/actual_tail.json``'s ``isos``
    block. Sets ``cv._TAIL_CACHE`` directly so scoring tests stay hermetic
    (never reading the committed part). Call :func:`_reset_tail` to restore.
    """
    cv._TAIL_CACHE = isos


def _reset_tail():
    """Drop the injected tail part so the next read reloads from disk."""
    cv._TAIL_CACHE = None


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

    def test_preliminary_gas_fallback_other_fossil_and_fold_in(self):
        # The EIA-930 family fallback compares like for like (ERCOT 2025 C2
        # counting fix): the model gas sum includes the OTHER_FOSSIL scoring
        # bucket (930 books mixed gas-thermal under NG:NG), and when the
        # bundle carries the 930 "other" series the gas target is deflated by
        # the genuinely-folded OTHER+biomass portion. Here the raw comparison
        # (190.0 vs 196.0 = -3.1%) would breach the ±2.5% target; the
        # like-for-like one (191.2 vs 195.11 = -2.0%) passes.
        _completeness({"ERCOT": {}}, {"ERCOT": {"gas": False, "coal": False}})
        try:
            rows = cv.score_sysvol(
                2025,
                {"gmModel": {"CC_REGULAR": 190.0, "OTHER_FOSSIL": 1.2}},
                {
                    "classFull": {
                        "CC_REGULAR": 188.0,
                        "OTHER_FOSSIL": 0.6,
                        "OTHER": 0.9,
                        "biomass": 0.25,
                    },
                    "e930": {"gas": 196.0, "other": 0.26},
                },
                "ERCOT",
            )
            gas = [r for r in rows if r["key"] == "gas"][0]
            self.assertEqual(gas["status"], cv.PASS)
            self.assertIsNone(gas["classification"])
            self.assertAlmostEqual(gas["model"], 191.2, places=2)
            # target = 196.0 - max(0, 0.9 + 0.25 - 0.26) = 195.11
            self.assertAlmostEqual(gas["actual"], 195.11, places=2)
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

    def test_g21b_coal_fallback_uses_cems_anchor(self):
        # G-21b: an incomplete COAL family gates against the CEMS anchor, not
        # the raw EIA-930 coal cell. MISO-shaped numbers: 930 coal 192.1 is
        # −20.9 TWh below CEMS 213.0 (the documented attribution swap), so the
        # raw cell reads the 206.8 model +7.6% (FAIL) while the CEMS anchor
        # (213.0 × k, k from the complete 2023/24 vintages ≈ 0.961) reads +0.9%
        # (PASS). k here: 2023 185.8/191.8, 2024 176.3/185.1.
        _completeness({"MISO": {}}, {"MISO": {"gas": False, "coal": False}})
        bench_all = {
            2023: {
                "classFull": {"COAL_PRB": 121.7, "COAL_BIT": 57.1, "COAL_LIGNITE": 7.0},
                "e930": {"coal": 174.9, "coal_cems": 191.8},
            },
            2024: {
                "classFull": {"COAL_PRB": 116.5, "COAL_BIT": 53.3, "COAL_LIGNITE": 6.5},
                "e930": {"coal": 167.1, "coal_cems": 185.1},
            },
            2025: {
                "classFull": {},
                "e930": {"gas": 233.2, "coal": 192.1, "coal_cems": 213.0},
            },
        }
        try:
            rows = cv.score_sysvol(
                2025,
                {"gmModel": {"COAL_PRB": 145.2, "COAL_BIT": 56.0, "COAL_LIGNITE": 5.6}},
                bench_all[2025],
                "MISO",
                bench_all=bench_all,
            )
            coal = [r for r in rows if r["key"] == "coal"][0]
            self.assertEqual(coal["status"], cv.PASS)
            self.assertIn("CEMS", coal["source"])
            # anchor = 213.0 × mean(185.8/191.8, 176.3/185.1) ≈ 204.7
            self.assertAlmostEqual(coal["actual"], 204.71, delta=0.1)
        finally:
            _reset_completeness()

    def test_cems_gas_anchor_fallback_caiso(self):
        # Owner-signed 2026-07-12 rework: a CEMS_GAS_ANCHOR_ISOS incomplete gas
        # family gates against the committed CEMS anchor (gas_cems_grid +
        # gas_cogen_grid), never the corrupted 930 NG cell, and no fold-in
        # deflation applies (the anchor carries no geothermal/biomass).
        _completeness({"CAISO": {}}, {"CAISO": {"gas": False, "coal": False}})
        try:
            rows = cv.score_sysvol(
                2025,
                {"gmModel": {"CC_REGULAR": 52.0}},
                {
                    "classFull": {"CC_REGULAR": 40.59, "OTHER": 5.5, "biomass": 3.2},
                    "e930": {
                        "gas": 68.53,
                        "other": 0.0,
                        "gas_cems_grid": 44.0,
                        "gas_cogen_grid": 7.6,
                        "fossil_cems_grid": 51.67,
                    },
                },
                "CAISO",
            )
            gas = [r for r in rows if r["key"] == "gas"][0]
            self.assertIn("CEMS bench-gas", gas["source"])
            self.assertAlmostEqual(gas["actual"], 51.6, places=2)
            self.assertEqual(gas["status"], cv.PASS)  # 52.0 vs 51.6 = +0.8%
        finally:
            _reset_completeness()

    def test_cems_gas_anchor_absent_keeps_legacy_930_path(self):
        # A CAISO bench part predating the anchor splice keeps the legacy
        # 930-based fallback (with fold-in), labelled as such.
        _completeness({"CAISO": {}}, {"CAISO": {"gas": False, "coal": False}})
        try:
            rows = cv.score_sysvol(
                2025,
                {"gmModel": {"CC_REGULAR": 60.0}},
                {
                    "classFull": {"CC_REGULAR": 40.59, "OTHER": 5.5, "biomass": 3.2},
                    "e930": {"gas": 68.53, "other": 0.0},
                },
                "CAISO",
            )
            gas = [r for r in rows if r["key"] == "gas"][0]
            self.assertIn("930", gas["source"])
        finally:
            _reset_completeness()

    def test_g21b_gas_fallback_combined_minus_coal_anchor(self):
        # G-21b: an incomplete GAS family gates against the 930 COMBINED fossil
        # total minus the coal anchor — the mirror correction. Same MISO-shaped
        # bench: raw gas cell 233.2 carries ~+20 TWh of misattributed coal, so
        # the raw comparison reads −12.0% (FAIL) while combined-minus-anchor
        # (233.2+192.1−204.7 = 220.6) reads −7.0 ... −4.9%-class (CAVEAT range).
        _completeness({"MISO": {}}, {"MISO": {"gas": False, "coal": False}})
        bench_all = {
            2023: {
                "classFull": {"COAL_PRB": 121.7, "COAL_BIT": 57.1, "COAL_LIGNITE": 7.0},
                "e930": {"coal": 174.9, "coal_cems": 191.8},
            },
            2025: {
                "classFull": {},
                "e930": {"gas": 233.2, "coal": 192.1, "coal_cems": 213.0},
            },
        }
        try:
            rows = cv.score_sysvol(
                2025,
                {"gmModel": {"CC_REGULAR": 205.2}},
                bench_all[2025],
                "MISO",
                bench_all=bench_all,
            )
            gas = [r for r in rows if r["key"] == "gas"][0]
            self.assertIn("combined fossil minus coal anchor", gas["source"])
            # anchor (single k year 2023: 185.8/191.8=0.9687) = 206.3;
            # actual = 233.2 + 192.1 − 206.3 = 219.0
            self.assertAlmostEqual(gas["actual"], 218.99, delta=0.1)
        finally:
            _reset_completeness()

    def test_g21b_gas_fallback_complete_coal_uses_classfull_anchor(self):
        # PJM-shaped sub-case: gas incomplete but coal COMPLETE — the gas
        # remainder subtracts the trustworthy classFull coal-family sum, no
        # CEMS needed. 930 books +10.4 TWh of PJM gas as coal, so the raw gas
        # cell (366.6) reads +3.9% (CAVEAT) while combined-minus-923-coal
        # (366.6+145.9−135.5 = 377.0) reads +1.0% (PASS).
        _completeness(
            {"PJM": {"COAL_BIT": True}}, {"PJM": {"gas": False, "coal": True}}
        )
        try:
            rows = cv.score_sysvol(
                2025,
                {"gmModel": {"CC_REGULAR": 380.9}},
                {
                    "classFull": {"COAL_BIT": 135.5},
                    "e930": {"gas": 366.6, "coal": 145.9},
                },
                "PJM",
            )
            gas = [r for r in rows if r["key"] == "gas"][0]
            self.assertEqual(gas["status"], cv.PASS)
            self.assertIn("combined fossil minus coal anchor", gas["source"])
            self.assertAlmostEqual(gas["actual"], 377.0, delta=0.1)
        finally:
            _reset_completeness()

    def test_g21b_legacy_fallback_when_no_anchor(self):
        # A bench part predating the coal_cems splice (or a run with no
        # complete coal vintage) keeps the legacy raw-930 cell, labelled.
        _completeness({"MISO": {}}, {"MISO": {"gas": False, "coal": False}})
        try:
            rows = cv.score_sysvol(
                2025,
                {"gmModel": {"COAL_PRB": 206.8}},
                {"classFull": {}, "e930": {"gas": 233.2, "coal": 192.1}},
                "MISO",
            )
            coal = [r for r in rows if r["key"] == "coal"][0]
            self.assertEqual(coal["status"], cv.FAIL)  # raw cell still gates
            self.assertIn("EIA-930 grid", coal["source"])
        finally:
            _reset_completeness()

    def test_g21b_anchor_safe_where_930_matches_cems(self):
        # Where the BA's 930 attribution agrees with CEMS (ERCOT-shaped), the
        # combined-minus-anchor construction reproduces the raw gas cell to
        # within the anchor-ratio noise — the correction self-neutralizes.
        _completeness({"ERCOT": {}}, {"ERCOT": {"gas": False, "coal": False}})
        bench_all = {
            2023: {
                "classFull": {"COAL_PRB": 60.4},
                "e930": {"coal": 62.3, "coal_cems": 62.7},
            },
            2025: {
                "classFull": {},
                "e930": {"gas": 200.2, "coal": 63.4, "coal_cems": 64.4},
            },
        }
        try:
            rows = cv.score_sysvol(
                2025,
                {"gmModel": {"CC_REGULAR": 199.0}},
                bench_all[2025],
                "ERCOT",
                bench_all=bench_all,
            )
            gas = [r for r in rows if r["key"] == "gas"][0]
            # anchor = 64.4 × (60.4/62.7) = 62.04; actual = 200.2+63.4−62.04
            # = 201.56 vs raw 200.2 — within 0.7%, same PASS either way.
            self.assertEqual(gas["status"], cv.PASS)
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
    def test_mean_lmp_single_band(self):
        # Rubric v2.3 (owner amendment 2026-07-09): the target band coincides
        # with the ±10% commercial band, so -3.8% AND -7.2% are both clean
        # PASSes (no COMMERCIAL_BAND caveat range on C3a); -17.5% beyond the
        # band -> FAIL (MODEL MISS, ledgerable only).
        ypay = {"lmp": {"Z": {"p": 28.4, "d": 100.0}}}
        r = cv.score_price_mean(2024, ypay, {"avgLMP": {"rt": 29.53}})
        self.assertEqual(r["status"], cv.PASS)
        ypay = {"lmp": {"Z": {"p": 27.4, "d": 100.0}}}
        r = cv.score_price_mean(2024, ypay, {"avgLMP": {"rt": 29.53}})
        self.assertEqual(r["status"], cv.PASS)  # -7.2%: clean under v2.3
        self.assertIsNone(r["classification"])
        ypay = {"lmp": {"Z": {"p": 35.4, "d": 100.0}}}
        r = cv.score_price_mean(2024, ypay, {"avgLMP": {"rt": 42.9}})
        self.assertEqual(r["status"], cv.FAIL)  # -17.5%
        self.assertEqual(r["classification"], cv.MODEL_MISS)

    def test_mean_lmp_v24_lw_basis_preferred(self):
        # Rubric v2.4: the load-weighted actual (rt_lw) gates when present —
        # the legacy equal-hour rt is ignored even though it would FAIL the
        # same model value; the labelled legacy fallback fires only when no
        # lw field is committed.
        ypay = {"lmp": {"Z": {"p": 64.0, "d": 100.0}}}
        bench = {"avgLMP": {"rt": 48.36, "rt_lw": 64.12}}
        r = cv.score_price_mean(2023, ypay, bench)
        self.assertEqual(r["status"], cv.PASS)  # -0.2% vs lw; +32% vs legacy
        self.assertIn("load-weighted", r["metric"])
        self.assertEqual(r["actual"], 64.12)
        r = cv.score_price_mean(2023, ypay, {"avgLMP": {"rt": 48.36}})
        self.assertEqual(r["status"], cv.FAIL)  # legacy fallback still gates
        self.assertIn("LEGACY equal-hour basis", r["metric"])

    def test_price_shape_v24_lw_monthly_preferred(self):
        ypay = {"lmp": {"Z": {"pMon": [30.0] * 12, "dMon": [8.3] * 12}}}
        bench = {"avgLMP": {"rt_mon": [24.0] * 12, "rt_lw_mon": [30.5] * 12}}
        r = cv.score_price_shape(2024, ypay, bench)
        self.assertEqual(r["status"], cv.PASS)  # NRMSE 0.016 vs lw monthly
        self.assertIn("load-weighted", r["metric"])

    def test_price_shape_nrmse_single_band(self):
        # Flat monthly vectors, rubric v2.3 single band: NRMSE 0.10 and 0.17
        # both clean PASS (<= 0.20); 0.28 beyond the band -> FAIL.
        def ypay(pm):
            return {"lmp": {"Z": {"pMon": [pm] * 12, "dMon": [8.3] * 12}}}

        bench = {"avgLMP": {"rt_mon": [29.0] * 12}}
        r = cv.score_price_shape(2024, ypay(31.9), bench)
        self.assertEqual(r["status"], cv.PASS)
        r = cv.score_price_shape(2024, ypay(33.93), bench)
        self.assertEqual(r["status"], cv.PASS)  # 0.17: clean under v2.3
        self.assertIsNone(r["classification"])
        r = cv.score_price_shape(2024, ypay(37.12), bench)
        self.assertEqual(r["status"], cv.FAIL)

    def test_tail_skipped_without_ordc(self):
        rows = cv.score_price_tail(2024, {"lmp": {}}, "PJM")
        self.assertEqual(rows[0]["status"], cv.SKIPPED)

    def test_tail_skipped_without_committed_part(self):
        # No committed DA-expressible actual for the ISO-year -> SKIPPED (the
        # payload's RT count alone no longer gates), RT diagnostic still emitted.
        _tail({})
        try:
            ypay = {"ordc": {"hoursGt200": {"actual": 100, "model": 50}}}
            rows = cv.score_price_tail(2024, ypay, "PJM")
            self.assertEqual(rows[0]["status"], cv.SKIPPED)
            rt = [r for r in rows if r["key"] == "rt_diagnostic"]
            self.assertEqual(len(rt), 1)
            self.assertEqual(rt[0]["status"], cv.SKIPPED)  # report-only
            self.assertEqual(rt[0]["actual"], 100.0)  # payload RT fallback
        finally:
            _reset_tail()

    def test_tail_gates_on_da_not_rt(self):
        # v2 scope-consistency: the gate is the DA-expressible tail. Model 20h
        # vs RT 100h would have failed v1's RT ratio; vs the committed DA 24h
        # it is 0.83x, inside [0.5x, 2x] -> PASS. The RT count appears only in
        # the non-gated diagnostic row.
        _tail({"MISO": {"2024": {"da_gt": 24, "rt_gt": 100, "da_coverage": 1.0}}})
        try:
            ypay = {"ordc": {"hoursGt200": {"actual": 100, "model": 20}}}
            rows = cv.score_price_tail(2024, ypay, "MISO")
            main = rows[0]
            self.assertEqual(main["status"], cv.PASS)
            self.assertEqual(main["actual"], 24.0)
            rt = [r for r in rows if r["key"] == "rt_diagnostic"][0]
            self.assertEqual(rt["actual"], 100.0)
            self.assertEqual(rt["status"], cv.SKIPPED)
        finally:
            _reset_tail()

    def test_tail_collapsed_fails(self):
        # A collapsed tail (0h) against a material DA actual FAILs — bounded
        # below on purpose, unchanged in spirit from v1.
        _tail({"ERCOT": {"2024": {"da_gt": 68, "rt_gt": 53, "da_coverage": 1.0}}})
        try:
            ypay = {"ordc": {"hoursGt200": {"actual": 53, "model": 0}}}
            rows = cv.score_price_tail(2024, ypay, "ERCOT")
            self.assertEqual(rows[0]["status"], cv.FAIL)
            self.assertEqual(rows[0]["classification"], cv.MODEL_MISS)
        finally:
            _reset_tail()

    def test_tail_band_and_overfire(self):
        # [0.5x, 2x] on the DA actual: 1.8x PASSes, 2.5x (invented tail) FAILs,
        # 0.4x FAILs. NEISO metric label carries the $300 winter proxy.
        _tail({"NEISO": {"2024": {"da_gt": 100, "rt_gt": 60, "da_coverage": 1.0}}})
        try:
            for model, want in ((180, cv.PASS), (250, cv.FAIL), (40, cv.FAIL)):
                ypay = {"ordc": {"hoursGt200": {"actual": 60, "model": model}}}
                rows = cv.score_price_tail(2024, ypay, "NEISO")
                self.assertEqual(rows[0]["status"], want, model)
            self.assertIn("300", rows[0]["metric"])
        finally:
            _reset_tail()

    def test_tail_small_count_absolute_guard(self):
        # DA actual below 10h: the ratio is degenerate, so |model-actual| <= 10h
        # gates instead — model 0h vs DA 8h PASSes (an hourly model showing no
        # tail against a handful of DA hours is within noise), model 30h vs DA
        # 2h FAILs (invented tail; also the v1 quiet-actual token guard, now
        # tighter at 10h instead of 50h).
        _tail({"PJM": {"2023": {"da_gt": 8, "rt_gt": 6, "da_coverage": 1.0}}})
        try:
            ypay = {"ordc": {"hoursGt200": {"actual": 6, "model": 0}}}
            rows = cv.score_price_tail(2023, ypay, "PJM")
            self.assertEqual(rows[0]["status"], cv.PASS)
        finally:
            _reset_tail()
        _tail({"PJM": {"2023": {"da_gt": 2, "rt_gt": 6, "da_coverage": 1.0}}})
        try:
            ypay = {"ordc": {"hoursGt200": {"actual": 6, "model": 30}}}
            rows = cv.score_price_tail(2023, ypay, "PJM")
            self.assertEqual(rows[0]["status"], cv.FAIL)
        finally:
            _reset_tail()

    def test_tail_partial_coverage_noted(self):
        # A DA series with partial coverage (CAISO 2023 Jan-Feb aged out of
        # OASIS retention) is a lower bound — surfaced in the magnitude.
        _tail({"CAISO": {"2023": {"da_gt": 41, "rt_gt": 21, "da_coverage": 0.819}}})
        try:
            ypay = {"ordc": {"hoursGt200": {"actual": 21, "model": 30}}}
            rows = cv.score_price_tail(2023, ypay, "CAISO")
            self.assertIn("lower bound", rows[0]["magnitude"])
        finally:
            _reset_tail()


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

    @staticmethod
    def _cems_fixture():
        """Synthetic committed artifacts for the CEMS-basis C4 recompute.

        One 100-MW gas plant whose payload and CAMPD hourly CF% series are the
        SAME diurnal ramp, so the recomputed CEMS-basis r is ~1.0 while the
        payload's committed 930-based fuelRow carries r=0.10 (the corrupted
        comparator). Series are the committed b64 uint8 CF% encoding.
        """
        import base64 as _b64mod

        cf = bytes((h % 24) * 4 for h in range(8760))  # 0-92% diurnal ramp
        b64 = _b64mod.b64encode(cf).decode()
        ybench = {
            "plants": {
                "1": {
                    "group": "CC_REGULAR",
                    "npl": 100,
                    "nodata": False,
                    "campd": b64,
                    "btm": 0.0,
                }
            },
            "e930": {"gas_cems_grid": 0.4, "gas_cogen_grid": 1.0},
        }
        ypay = {
            "plants": {"1": {"m": b64}},
            "fuelRows": [
                {"fuel": "gas", "m": 20.0, "b": 70.0, "r": 0.10, "nrmse": 0.44}
            ],
        }
        return ypay, ybench

    def test_dispatch_corr_cems_recompute_caiso_post_onset(self):
        # CAISO ≥ 2024: the gas fit is recomputed from the committed hourly
        # series (payload m vs bench campd + flat cogen block) — the 930-based
        # payload values (r=0.10) score the corrupted benchmark, not the model.
        ypay, ybench = self._cems_fixture()
        gas = [
            r
            for r in cv.score_dispatch_corr(2024, ypay, ybench, "CAISO")
            if r["key"] == "gas"
        ][0]
        self.assertIn("r=1.0", gas["model"])  # identical shapes -> r ~ 1.0
        self.assertIn("CEMS", gas["metric"])

    def test_dispatch_corr_cems_pre_onset_keeps_930(self):
        # 2023 predates the corruption onset: the committed 930-based fit
        # stands (the two bases agree there — continuity).
        ypay, ybench = self._cems_fixture()
        gas = [
            r
            for r in cv.score_dispatch_corr(2023, ypay, ybench, "CAISO")
            if r["key"] == "gas"
        ][0]
        self.assertIn("r=0.1 ", gas["model"])
        self.assertNotIn("CEMS", gas["metric"])

    def test_dispatch_corr_cems_other_iso_unchanged(self):
        # Membership is CEMS-evidence-gated per ISO: a non-member ISO keeps
        # the payload's committed fit even if anchor-shaped fields exist.
        ypay, ybench = self._cems_fixture()
        gas = [
            r
            for r in cv.score_dispatch_corr(2024, ypay, ybench, "ERCOT")
            if r["key"] == "gas"
        ][0]
        self.assertIn("r=0.1 ", gas["model"])
        self.assertNotIn("CEMS", gas["metric"])


class GovernanceTests(unittest.TestCase):
    def test_unattested(self):
        g = cv.score_governance(
            {"scenario_config": {"outage_source": "historic"}}, None
        )
        self.assertEqual(g["status"], "UNATTESTED")

    def test_ledger_only_attestation_is_unattested(self):
        # A DOF-ledger-only attestation (free_parameters, no governance block)
        # is exactly as unattested as no file: nobody asserted the claims.
        g = cv.score_governance(
            {"scenario_config": {"outage_source": "historic"}},
            {"free_parameters": {"entries": []}},
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

    def test_ledgered_caveat_budget_is_three(self):
        # Pins MAX_LEDGERED_CAVEATS = 3 (rubric v2, memo §3a): ledgered
        # (beyond-commercial-band, measured-input-documented) caveats are
        # budgeted at 3; four of them (price_mean -13.8%, price_tail 0.25x,
        # storage +50%, dispatch_corr r=0.55) exceed the budget -> NOT-YET;
        # with the gas fleet correlation back above the floor there are
        # three -> CALIBRATED-WITH-CAVEATS.
        def art_with(gas_r):
            ypay = self._clean_year_payload()
            ypay["lmp"]["Z"]["p"] = 25.0  # -13.8% vs rt 29.0: beyond ±10% comm.
            ypay["lmp"]["Z"]["pMon"] = [25] * 12  # NRMSE 0.138 <= 0.15 -> PASS
            ypay["ordc"] = {"hoursGt200": {"actual": 100, "model": 25}}  # 0.25x
            ypay["storage"] = {"throughput_twh": 1.5}  # +50% -> beyond ±30%
            ypay["fuelRows"][0]["r"] = gas_r
            att = _clean_attestation(
                exceptions=[
                    {"criterion": "price_mean", "year": 2024, "reason": "documented"},
                    {"criterion": "price_tail", "year": 2024, "reason": "documented"},
                    {"criterion": "storage", "year": 2024, "reason": "documented"},
                    {
                        "criterion": "dispatch_corr",
                        "family": "gas",
                        "year": 2024,
                        "reason": "documented",
                    },
                ]
            )
            art = _artifacts(ypay, attestation=att, **self._clean_bench_args())
            art["bench"][2024]["storage"] = {"throughput_twh": 1.0}
            return art

        _tail({"PJM": {"2024": {"da_gt": 100, "rt_gt": 80, "da_coverage": 1.0}}})
        try:
            v = cv.determine_from_artifacts("t", art_with(0.55))  # 4 ledgered
            self.assertEqual(v["determination"], cv.NOT_YET)
            self.assertIn("caveat budget exceeded", v["reasons"][0])
            v = cv.determine_from_artifacts("t", art_with(0.80))  # 3 ledgered
            self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)
            self.assertEqual(len(v["caveats"]["ledgered"]), 3)
        finally:
            _reset_tail()

    def test_commercial_band_caveats_unbudgeted(self):
        # Auto COMMERCIAL_BAND caveats (inside the evidence-anchored outer band,
        # outside target) are listed but never consume the ledger budget. Under
        # rubric v2.3 the price criteria are single-band (price_mean -6.9% and
        # price_shape NRMSE 0.17 are clean PASSes), so only co2 +8% remains a
        # commercial-band caveat -> CALIBRATED-WITH-CAVEATS, not NOT-YET.
        ypay = self._clean_year_payload()
        ypay["lmp"]["Z"]["p"] = 27.0  # -6.9% vs rt 29.0: clean PASS (v2.3)
        ypay["lmp"]["Z"]["pMon"] = [33.93] * 12  # NRMSE 0.17: clean PASS (v2.3)
        ypay["co2"] = {"model": 108.0}
        art = _artifacts(
            ypay, attestation=_clean_attestation(), **self._clean_bench_args()
        )
        art["bench"][2024]["co2"] = {"egrid": 100.0}
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)
        self.assertEqual(len(v["caveats"]["commercial_band"]), 1)  # co2 only
        self.assertEqual(v["caveats"]["ledgered"], [])
        self.assertTrue(any("commercial-grade band" in r for r in v["reasons"]))

    def test_protective_caveat_budget_is_one(self):
        # C7/C8 keep the v1 hard budget of 1 (CLAUDE.md rule 20 / audit D-1/D-2
        # enforcement unchanged): both protective gates ledgered at once ->
        # budget exceeded -> NOT-YET; a single ledgered protective caveat with
        # the other passing -> CALIBRATED-WITH-CAVEATS.
        def art_with(legit, exceptions):
            art = _artifacts(
                self._clean_year_payload(),
                attestation=_clean_attestation(exceptions=exceptions),
                **self._clean_bench_args(),
            )
            art["legitimacy"] = legit
            return art

        both_fail = _legit_artifact(r=0.9, cv_ratio=0.02, share=0.55)
        exceptions = [
            {
                "criterion": "shape",
                "klass": "CT_PEAKER",
                "year": 2024,
                "reason": "documented",
            },
            {
                "criterion": "forced_share",
                "klass": "CT_PEAKER",
                "year": 2024,
                "reason": "documented",
            },
        ]
        v = cv.determine_from_artifacts("t", art_with(both_fail, exceptions))
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertIn("caveat budget exceeded", v["reasons"][0])
        shape_only = _legit_artifact(r=0.9, cv_ratio=0.02, share=0.05)
        v = cv.determine_from_artifacts("t", art_with(shape_only, exceptions))
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)
        self.assertEqual(len(v["caveats"]["protective"]), 1)

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


def _mat(klass="CT_PEAKER", model_twh=30.0, actual_twh=30.0, total_twh=None):
    """(ypay, ybench) making ``klass`` carry a chosen share of ISO load.

    With no ``total_twh`` the class IS the whole system (share 100% —
    comfortably above the C7/C8 materiality floor); pass ``total_twh`` to
    place the class below/above the 2% floor via a filler class.
    """
    cf = {klass: actual_twh}
    gm = {klass: model_twh}
    if total_twh is not None:
        cf["CC_REGULAR" if klass != "CC_REGULAR" else "ST_GAS"] = total_twh - actual_twh
    return {"gmModel": gm}, {"classFull": cf}


def _legit_artifact(
    year=2024,
    r=0.92,
    cv_ratio=1.1,
    share=0.05,
    klass="CT_PEAKER",
    d2_rows=None,
    d4_rows=None,
):
    """Synthetic legitimacy_diagnostics.json content (schema v1) for C7/C8.

    ``d2_rows`` / ``d4_rows`` (optional) inject the per-(class, mechanism) D-2
    attribution rows and the D-4 off-window rows the v2.2 grounded-above-budget
    escalation reads. Omitted by default so the below-cap / immaterial /
    stale-verdict tests keep their exact prior fixtures (an above-cap class with
    no D-2 rows then correctly fails provenance — unattributable forcing).
    """
    fail_d1 = r < 0.8 or cv_ratio < 0.5
    fail_d2 = share > (0.15 if klass == "CT_PEAKER" else 0.30)
    out = {
        "schema": "legitimacy-diagnostics/v1",
        "iso": "PJM",
        "years": [year],
        "gates": {
            "d1_min_profile_r": 0.8,
            "d1_min_cv_ratio": 0.5,
            "d1_offpeak_last_hour": 14,
            "d1_gated_classes": ["CT_PEAKER", "ST_GAS"],
            "d2_peaker_max_share": 0.10,
            "d2_merchant_max_share": 0.30,
        },
        "diagnostics": {
            "D1": {
                "rows": [
                    {
                        "year": year,
                        "class": klass,
                        "profile_r": r,
                        "model_offpeak_cv": 0.2,
                        "actual_offpeak_cv": 0.2 / cv_ratio if cv_ratio else 1,
                        "cv_ratio": cv_ratio,
                        "gated": True,
                        "verdict": "FAIL" if fail_d1 else "pass",
                    }
                ]
            },
            "D2": {
                "summary": [
                    {
                        "year": year,
                        "class": klass,
                        "forced_twh": 1.0,
                        "class_total_twh": 1.0 / share if share else 1.0,
                        "forced_share": share,
                        "limit": 0.10 if klass == "CT_PEAKER" else 0.30,
                        "lower_bound": False,
                        "verdict": "FAIL" if fail_d2 else "pass",
                    }
                ],
            },
        },
    }
    if d2_rows is not None:
        out["diagnostics"]["D2"]["rows"] = d2_rows
    if d4_rows is not None:
        out["diagnostics"]["D4"] = {"rows": d4_rows}
    return out


class ShapeForcedShareTests(unittest.TestCase):
    """C7 (D-1 diurnal shape) and C8 (D-2 forced share) from the artifact."""

    def test_shape_skipped_without_artifact(self):
        recs = cv.score_shape(2024, None, *_mat())
        self.assertEqual(recs[0]["status"], cv.SKIPPED)
        self.assertIn("legitimacy_diagnostics.json", recs[0]["magnitude"])

    def test_shape_flat_floor_fails(self):
        legit = _legit_artifact(r=0.9, cv_ratio=0.02)  # the caiso-42 signature
        recs = cv.score_shape(2024, legit, *_mat())
        self.assertEqual(recs[0]["status"], cv.FAIL)
        self.assertEqual(recs[0]["classification"], cv.MODEL_MISS)

    def test_shape_good_profile_passes(self):
        recs = cv.score_shape(2024, _legit_artifact(r=0.92, cv_ratio=1.1), *_mat())
        self.assertEqual(recs[0]["status"], cv.PASS)

    def test_shape_year_missing_is_skipped(self):
        recs = cv.score_shape(2023, _legit_artifact(year=2024), *_mat())
        self.assertEqual(recs[0]["status"], cv.SKIPPED)

    def test_shape_immaterial_class_skipped(self):
        # v2.1 materiality floor: a class at 1% of ISO load (1 of 100 TWh) is
        # SKIPPED-immaterial even with the caiso-42 flat-floor signature — the
        # D-1 reading is annotated, never gated. At 3% of load it gates again.
        legit = _legit_artifact(r=0.9, cv_ratio=0.02)
        recs = cv.score_shape(
            2024, legit, *_mat(model_twh=1.0, actual_twh=1.0, total_twh=100.0)
        )
        self.assertEqual(recs[0]["status"], cv.SKIPPED)
        self.assertIn("immaterial", recs[0]["magnitude"])
        recs = cv.score_shape(
            2024, legit, *_mat(model_twh=3.0, actual_twh=3.0, total_twh=100.0)
        )
        self.assertEqual(recs[0]["status"], cv.FAIL)

    def test_shape_forcing_cannot_hide_below_materiality(self):
        # max(model, actual) basis: actual 1 TWh (1% of load) but the model
        # forces the class to 5 TWh (5%) -> still gated (and failing).
        legit = _legit_artifact(r=0.9, cv_ratio=0.02)
        recs = cv.score_shape(
            2024, legit, *_mat(model_twh=5.0, actual_twh=1.0, total_twh=100.0)
        )
        self.assertEqual(recs[0]["status"], cv.FAIL)

    def test_forced_share_peaker_gate_is_15pct(self):
        # v2.1 owner amendment: CT_PEAKER cap 15% (was 10%). 12% now PASSes
        # (pins the amendment), 16% FAILs, 55% FAILs, 5% PASSes.
        for share, want in (
            (0.55, cv.FAIL),
            (0.16, cv.FAIL),
            (0.12, cv.PASS),
            (0.05, cv.PASS),
        ):
            recs = cv.score_forced_share(2024, _legit_artifact(share=share), *_mat())
            self.assertEqual(recs[0]["status"], want, share)

    def test_forced_share_measured_share_overrides_artifact_verdict(self):
        # The scorer gates the MEASURED share against the rubric caps: an
        # artifact written under the old 10% gate (embedded verdict FAIL at
        # 12%) re-scores as PASS under the 15% cap without regeneration.
        legit = _legit_artifact(share=0.12)
        legit["diagnostics"]["D2"]["summary"][0]["verdict"] = "FAIL"  # stale 10%-era
        recs = cv.score_forced_share(2024, legit, *_mat())
        self.assertEqual(recs[0]["status"], cv.PASS)

    def test_forced_share_immaterial_class_skipped(self):
        # v2.1 materiality floor: 92.7% forced on a class at 1% of load is
        # SKIPPED-immaterial (reported), not a FAIL.
        recs = cv.score_forced_share(
            2024,
            _legit_artifact(share=0.927),
            *_mat(model_twh=1.0, actual_twh=1.0, total_twh=100.0),
        )
        self.assertEqual(recs[0]["status"], cv.SKIPPED)
        self.assertIn("immaterial", recs[0]["magnitude"])
        self.assertIn("92.7% forced", recs[0]["magnitude"])

    def test_forced_share_lower_bound_flagged(self):
        legit = _legit_artifact(share=0.05)
        legit["diagnostics"]["D2"]["summary"][0]["lower_bound"] = True
        recs = cv.score_forced_share(2024, legit, *_mat())
        self.assertIn("lower bound", recs[0]["magnitude"])

    # --- v2.2 grounded-above-budget escalation (rubric §1 C8) --------------
    def _grounded_legit(
        self,
        share=0.50,
        mech="ct_netload_drag",
        r=0.92,
        cv_ratio=1.1,
        d4_verdict="pass",
        klass="CT_PEAKER",
    ):
        """Above-cap artifact with a D-2 mechanism row and a D-4 window row."""
        return _legit_artifact(
            share=share,
            r=r,
            cv_ratio=cv_ratio,
            klass=klass,
            d2_rows=[
                {
                    "year": 2024,
                    "class": klass,
                    "mechanism": mech,
                    "forced_twh": 1.0,
                    "class_total_twh": 1.0 / share,
                    "share_of_class": share,
                }
            ],
            d4_rows=[
                {
                    "year": 2024,
                    "floor": mech,
                    "window": "h15-21",
                    "offwindow_share": 0.0 if d4_verdict == "pass" else 0.4,
                    "verdict": d4_verdict,
                }
            ],
        )

    def test_forced_share_grounded_above_budget_passes(self):
        # 50% forced (above the 15% peaker cap) but the driving mechanism binds
        # in-window (D-4 pass) AND the diurnal shape is good (D-1 pass): clean
        # PASS classified GROUNDED_ABOVE_BUDGET, not a FAIL.
        recs = cv.score_forced_share(2024, self._grounded_legit(), *_mat())
        self.assertEqual(recs[0]["status"], cv.PASS)
        self.assertEqual(recs[0]["classification"], cv.GROUNDED_ABOVE_BUDGET)
        self.assertIn("GROUNDED", recs[0]["magnitude"])

    def test_forced_share_above_budget_offwindow_fails(self):
        # Same 50% forcing, but the mechanism binds OFF its justified window
        # (D-4 FAIL) -> provenance fails -> C8 FAIL (forcing miscalibrated).
        recs = cv.score_forced_share(
            2024, self._grounded_legit(d4_verdict="FAIL"), *_mat()
        )
        self.assertEqual(recs[0]["status"], cv.FAIL)
        self.assertIn("provenance", recs[0]["magnitude"])
        self.assertIn("off-window", recs[0]["magnitude"])

    def test_forced_share_above_budget_bad_shape_fails(self):
        # In-window mechanism but a flat diurnal shape (the caiso-42 signature,
        # cv_ratio 0.02) -> shape fails -> C8 FAIL. This is the "shape mismatch
        # means the forcing variables are wrong" case.
        recs = cv.score_forced_share(2024, self._grounded_legit(cv_ratio=0.02), *_mat())
        self.assertEqual(recs[0]["status"], cv.FAIL)
        self.assertIn("shape", recs[0]["magnitude"])

    def test_forced_share_above_budget_unwindowed_mech_fails(self):
        # A mechanism with NO declared D-4 window cannot be grounded (rule 12).
        legit = self._grounded_legit()
        legit["diagnostics"]["D4"]["rows"] = []  # window registry has no entry
        recs = cv.score_forced_share(2024, legit, *_mat())
        self.assertEqual(recs[0]["status"], cv.FAIL)
        self.assertIn("no declared D-4 window", recs[0]["magnitude"])

    def test_forced_share_above_budget_no_mech_rows_fails(self):
        # Above cap with no attributable D-2 mechanism rows (legacy artifact):
        # provenance unverifiable -> FAIL, never a vacuous grounded pass.
        recs = cv.score_forced_share(2024, _legit_artifact(share=0.50), *_mat())
        self.assertEqual(recs[0]["status"], cv.FAIL)
        self.assertIn("unverifiable", recs[0]["magnitude"])

    def test_forced_share_grounded_note_surfaced_in_verdict(self):
        # The grounded pass is surfaced as a report NOTE (not a caveat) and does
        # not knock a clean run below CALIBRATED.
        d = DeterminationTests()
        art = _artifacts(
            d._clean_year_payload(),
            attestation=_clean_attestation(),
            **d._clean_bench_args(),
        )
        # Give the clean run a shape artifact whose CT_PEAKER is grounded above
        # budget (2024 is the clean payload's scored year).
        art["legitimacy"] = self._grounded_legit()
        art["legitimacy"]["years"] = [2024]
        art["legitimacy"]["diagnostics"]["D1"]["rows"][0]["year"] = 2024
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["criteria"]["forced_share"]["status"], cv.PASS)
        self.assertTrue(
            any("grounded above budget" in n for n in v.get("notes", [])),
            v.get("notes"),
        )

    def test_forced_exempt_mech_names_match_floor_mechanisms(self):
        # The local literal must mirror floor_mechanisms (source of truth) so it
        # cannot silently drift from the D-2 exempt / non-thermal id sets.
        from market_sim.data import floor_mechanisms as fm

        expected = {
            fm.MECH_NAMES[m] for m in (fm.D2_EXEMPT_MECHS | fm.NON_THERMAL_MECHS)
        }
        self.assertEqual(cv.FORCED_EXEMPT_MECH_NAMES, expected)

    def test_missing_artifact_caps_determination(self):
        """SKIPPED HARD C7/C8 (no artifact) can never yield clean CALIBRATED."""
        d = DeterminationTests()
        art = _artifacts(
            d._clean_year_payload(),
            attestation=_clean_attestation(),
            **d._clean_bench_args(),
        )
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)
        self.assertTrue(
            any("unscored PROTECTIVE criteria" in r for r in v["reasons"]),
            v["reasons"],
        )
        self.assertEqual(v["criteria"]["shape"]["status"], cv.SKIPPED)

    def test_flat_floor_forces_not_yet(self):
        """A flat-floor keeper FAILs C7/C8 -> NOT-YET, whatever C1 says."""
        d = DeterminationTests()
        art = _artifacts(
            d._clean_year_payload(),
            attestation=_clean_attestation(),
            **d._clean_bench_args(),
        )
        art["legitimacy"] = _legit_artifact(r=0.9, cv_ratio=0.0, share=0.55)
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertEqual(v["criteria"]["shape"]["status"], cv.FAIL)
        self.assertEqual(v["criteria"]["forced_share"]["status"], cv.FAIL)


class FreeClassScoreTests(unittest.TestCase):
    """D-10 free-class rescore: C1 pass rate with pinned classes excluded."""

    @staticmethod
    def _fm(klass, status):
        return {"criterion": "fuelmix", "key": klass, "status": status}

    def test_free_excludes_pinned_chp(self):
        """CHP subclasses (pinned, L4) drop out of the free-class denominator."""
        records = [
            self._fm("CC_REGULAR", cv.PASS),
            self._fm("COAL_BIT", cv.FAIL),
            self._fm("CC_CHP", cv.PASS),  # pinned
            self._fm("ST_CHP", cv.PASS),  # pinned
        ]
        out = cv.free_class_score("ERCOT", records)
        self.assertEqual(out["all"], {"pass": 3, "total": 4})
        self.assertEqual(out["free"], {"pass": 1, "total": 2})
        self.assertEqual(out["headline"], "C1 all 3/4 · free 1/2")
        self.assertEqual(out["excluded_from_free"], ["CC_CHP", "ST_CHP"])

    def test_skipped_rows_not_counted(self):
        """SKIPPED fuelmix rows are outside both pass rates."""
        records = [
            self._fm("CC_REGULAR", cv.PASS),
            self._fm("COAL_PRB", cv.SKIPPED),
        ]
        out = cv.free_class_score("PJM", records)
        self.assertEqual(out["all"], {"pass": 1, "total": 1})

    def test_nyiso_pins_imports(self):
        """NYISO's declared pinned set carries the imports class (L2)."""
        self.assertIn("imports", cv.PINNED_CLASSES_BY_ISO["NYISO"])

    def test_verdict_carries_free_class_score(self):
        """determine_from_artifacts surfaces the free_class_score block."""
        d = DeterminationTests()
        art = _artifacts(
            d._clean_year_payload(),
            attestation=_clean_attestation(),
            **d._clean_bench_args(),
        )
        v = cv.determine_from_artifacts("t", art)
        self.assertIn("free_class_score", v)
        self.assertIn("headline", v["free_class_score"])


class PctWmeanTests(unittest.TestCase):
    """_pct (:259) and _wmean (:266) — the two scalar primitives every
    percent-error and demand-weighted-mean criterion is built from."""

    def test_zero_actual_denominator_is_none(self):
        self.assertIsNone(cv._pct(10.0, 0.0))

    def test_near_zero_actual_denominator_is_none(self):
        # abs(actual) < 1e-9 is treated as undefined, not a huge finite ratio.
        self.assertIsNone(cv._pct(10.0, 1e-10))

    def test_sign_convention_model_above_actual_is_positive(self):
        self.assertAlmostEqual(cv._pct(110.0, 100.0), 0.10)

    def test_sign_convention_model_below_actual_is_negative(self):
        self.assertAlmostEqual(cv._pct(90.0, 100.0), -0.10)

    def test_exact_match_is_zero(self):
        self.assertAlmostEqual(cv._pct(42.0, 42.0), 0.0)

    def test_negative_actual_sign_convention(self):
        # (-90 - (-100)) / (-100) = 10 / -100 = -0.10: a model that undershoots
        # in magnitude on a negative actual still reads as a negative error,
        # exactly like the positive-actual case above.
        self.assertAlmostEqual(cv._pct(-90.0, -100.0), -0.10)

    def test_wmean_empty_pairs_is_none(self):
        self.assertIsNone(cv._wmean([]))

    def test_wmean_all_zero_weight_is_none(self):
        self.assertIsNone(cv._wmean([(5.0, 0.0), (10.0, 0.0)]))

    def test_wmean_single_pair_returns_its_value(self):
        self.assertAlmostEqual(cv._wmean([(7.5, 3.0)]), 7.5)

    def test_wmean_weighted_average(self):
        # (10*1 + 20*3) / (1+3) = 70/4 = 17.5
        self.assertAlmostEqual(cv._wmean([(10.0, 1.0), (20.0, 3.0)]), 17.5)


class Co2ScoreTests(unittest.TestCase):
    """score_co2 (:875) — within/outside the CO2_TOL band, SKIPPED when unset."""

    def test_within_band_passes(self):
        actual = 100.0
        model = actual * (1.0 + cv.CO2_TOL - 0.005)
        r = cv.score_co2(2024, {"co2": {"model": model}}, {"co2": {"egrid": actual}})
        self.assertEqual(r["status"], cv.PASS)

    def test_outside_target_inside_commercial_is_auto_caveat(self):
        actual = 100.0
        model = actual * (1.0 + cv.CO2_TOL + 0.01)  # +8%: between 7% and 10%
        r = cv.score_co2(2024, {"co2": {"model": model}}, {"co2": {"egrid": actual}})
        self.assertEqual(r["status"], cv.CAVEAT)
        self.assertEqual(r["classification"], cv.COMMERCIAL_BAND)

    def test_outside_commercial_band_fails(self):
        actual = 100.0
        model = actual * (1.0 + cv.CO2_COMMERCIAL + 0.01)  # +11%: beyond 10%
        r = cv.score_co2(2024, {"co2": {"model": model}}, {"co2": {"egrid": actual}})
        self.assertEqual(r["status"], cv.FAIL)
        self.assertEqual(r["classification"], cv.MODEL_MISS)

    def test_skipped_without_model(self):
        r = cv.score_co2(2024, {"co2": {}}, {"co2": {"egrid": 100.0}})
        self.assertEqual(r["status"], cv.SKIPPED)

    def test_skipped_without_actual(self):
        r = cv.score_co2(2024, {"co2": {"model": 100.0}}, {"co2": {}})
        self.assertEqual(r["status"], cv.SKIPPED)


class StorageShapeScoreTests(unittest.TestCase):
    """score_storage_shape (:931) status tokens on the positive-discharge basis
    (rubric §C5c 2026-07-03 alignment fix: both series are monthly discharge,
    not net charge-minus-discharge)."""

    # A ramp with a clear seasonal shape (CV well above STORAGE_SHAPE_MIN_CV)
    # so the degeneracy guard never fires for the pass/fail cases below.
    _ACTUAL = [float(x) for x in range(1, 13)]  # 1..12, positive discharge GWh

    def _bench(self, actual=None):
        return {"storage": {"monthly_net_gwh": actual or self._ACTUAL}}

    def test_pass_high_correlation(self):
        model = [2.0 * x for x in self._ACTUAL]  # perfectly correlated, scaled
        r = cv.score_storage_shape(
            2024, {"storage": {"monthly_net_gwh": model}}, self._bench()
        )
        self.assertEqual(r["status"], cv.PASS)

    def test_fail_anticorrelated(self):
        model = list(reversed(self._ACTUAL))  # r = -1
        r = cv.score_storage_shape(
            2024, {"storage": {"monthly_net_gwh": model}}, self._bench()
        )
        self.assertEqual(r["status"], cv.FAIL)
        self.assertEqual(r["classification"], cv.MODEL_MISS)

    def test_skipped_no_actual_monthly(self):
        r = cv.score_storage_shape(2024, {"storage": {}}, {"storage": {}})
        self.assertEqual(r["status"], cv.SKIPPED)

    def test_skipped_no_model_monthly(self):
        r = cv.score_storage_shape(2024, {"storage": {}}, self._bench())
        self.assertEqual(r["status"], cv.SKIPPED)

    def test_skipped_wrong_length(self):
        r = cv.score_storage_shape(
            2024, {"storage": {"monthly_net_gwh": [1.0] * 11}}, self._bench()
        )
        self.assertEqual(r["status"], cv.SKIPPED)

    def test_skipped_null_month(self):
        model = [1.0] * 12
        model[3] = None
        r = cv.score_storage_shape(
            2024, {"storage": {"monthly_net_gwh": model}}, self._bench()
        )
        self.assertEqual(r["status"], cv.SKIPPED)

    def test_skipped_degenerate_actual_shape(self):
        # Near-uniform actual monthly discharge (CV < STORAGE_SHAPE_MIN_CV): no
        # seasonal shape to correlate, so even the TRUE model would score r=0.
        flat_actual = self._bench([10.0] * 12)
        model = [10.0] * 12
        model[0] = 10.5  # some model variation, irrelevant — actual is degenerate
        r = cv.score_storage_shape(
            2024, {"storage": {"monthly_net_gwh": model}}, flat_actual
        )
        self.assertEqual(r["status"], cv.SKIPPED)


def _fm(klass, status="PASS"):
    return {"criterion": "fuelmix", "key": klass, "status": status}


class LedgerMatchTests(unittest.TestCase):
    """_ledger_match (:289) — a mis-scoped exception must not waive an
    unrelated criterion/year/class's failure."""

    def test_matches_on_criterion_year_key(self):
        exceptions = [
            {"criterion": "fuelmix", "klass": "COAL_BIT", "year": 2024, "reason": "x"}
        ]
        self.assertIsNotNone(cv._ledger_match(exceptions, "fuelmix", 2024, "COAL_BIT"))

    def test_wrong_criterion_does_not_match(self):
        # A sysvol exception must never waive an unrelated fuelmix FAIL.
        exceptions = [
            {"criterion": "sysvol", "family": "gas", "year": 2024, "reason": "x"}
        ]
        self.assertIsNone(cv._ledger_match(exceptions, "fuelmix", 2024, "gas"))

    def test_wrong_year_does_not_match(self):
        exceptions = [
            {"criterion": "fuelmix", "klass": "COAL_BIT", "year": 2023, "reason": "x"}
        ]
        self.assertIsNone(cv._ledger_match(exceptions, "fuelmix", 2024, "COAL_BIT"))

    def test_wrong_class_does_not_match(self):
        # An exception documented for CT_PEAKER must not silently waive a
        # DIFFERENT class's (e.g. COAL_BIT's) failure in the same year.
        exceptions = [
            {"criterion": "fuelmix", "klass": "CT_PEAKER", "year": 2024, "reason": "x"}
        ]
        self.assertIsNone(cv._ledger_match(exceptions, "fuelmix", 2024, "COAL_BIT"))

    def test_keyless_criterion_matches_on_criterion_year_alone(self):
        # Criteria with no sub-key (price_mean, co2, storage, ...) legitimately
        # match with key=None on both sides.
        exceptions = [{"criterion": "price_mean", "year": 2024, "reason": "x"}]
        self.assertIsNotNone(cv._ledger_match(exceptions, "price_mean", 2024, None))

    def test_apply_ledger_end_to_end_only_documented_class_becomes_caveat(self):
        # Regression for the "mis-scoped ledger waives an unrelated failure"
        # failure mode: two FAILing classes, only one documented -> only that
        # one becomes a CAVEAT, the other stays a FAIL.
        documented = _fm("CT_PEAKER", cv.FAIL)
        undocumented = _fm("COAL_BIT", cv.FAIL)
        exceptions = [
            {"criterion": "fuelmix", "klass": "CT_PEAKER", "year": None, "reason": "x"}
        ]
        documented["year"] = 2024
        undocumented["year"] = 2024
        exceptions[0]["year"] = 2024
        cv._apply_ledger(documented, exceptions)
        cv._apply_ledger(undocumented, exceptions)
        self.assertEqual(documented["status"], cv.CAVEAT)
        self.assertEqual(undocumented["status"], cv.FAIL)


class CompletenessMapTests(unittest.TestCase):
    """class_is_gated (:372) / family_is_complete (:387) — a completeness-map
    bug must not silently drop (mis-gate) a class or family."""

    def test_no_completeness_part_gates_by_default(self):
        # No committed completeness part for this year (complete-vintage year):
        # every class/family gates as usual, regardless of the map's contents.
        self.assertTrue(cv.class_is_gated("PJM", "CC_REGULAR", 2024))
        self.assertTrue(cv.family_is_complete("PJM", "gas", 2024))

    def test_class_absent_from_map_defaults_to_not_gated(self):
        # A completeness-map bug that OMITS a class (typo, missing audit row)
        # must default to "not gated" (safe/conservative) -- never silently
        # fall through to "gated", which would score a FAIL/PASS against an
        # actual the audit never verified.
        _completeness(
            {"ERCOT": {"CC_REGULAR": True}}, {"ERCOT": {"gas": True, "coal": False}}
        )
        try:
            self.assertFalse(cv.class_is_gated("ERCOT", "COAL_BIT", 2025))
        finally:
            _reset_completeness()

    def test_family_absent_from_map_defaults_to_incomplete(self):
        _completeness({"ERCOT": {}}, {"ERCOT": {"gas": True}})
        try:
            self.assertFalse(cv.family_is_complete("ERCOT", "coal", 2025))
        finally:
            _reset_completeness()

    def test_gate_flag_honored_both_directions(self):
        _completeness(
            {"PJM": {"CC_REGULAR": True, "COAL_BIT": False}}, {"PJM": {"gas": True}}
        )
        try:
            self.assertTrue(cv.class_is_gated("PJM", "CC_REGULAR", 2025))
            self.assertFalse(cv.class_is_gated("PJM", "COAL_BIT", 2025))
        finally:
            _reset_completeness()


class AggStatusTests(unittest.TestCase):
    """_agg_status (:1206) is the worst-of-children aggregator every criterion's
    multi-year result folds through; it must be stable regardless of the
    order its per-year records arrive in (determinism guard)."""

    @staticmethod
    def _mk(statuses):
        return [{"status": s} for s in statuses]

    def test_all_pass_is_pass(self):
        self.assertEqual(self._agg([cv.PASS, cv.PASS]), cv.PASS)

    def _agg(self, statuses):
        return cv._agg_status(self._mk(statuses))

    def test_all_skipped_is_skipped(self):
        self.assertEqual(self._agg([cv.SKIPPED, cv.SKIPPED]), cv.SKIPPED)

    def test_empty_is_skipped(self):
        self.assertEqual(cv._agg_status([]), cv.SKIPPED)

    def test_fail_dominates_caveat_pass_and_skipped(self):
        self.assertEqual(self._agg([cv.PASS, cv.CAVEAT, cv.FAIL, cv.SKIPPED]), cv.FAIL)

    def test_caveat_beats_pass_and_skipped(self):
        self.assertEqual(self._agg([cv.PASS, cv.CAVEAT, cv.SKIPPED]), cv.CAVEAT)

    def test_pass_is_not_masked_by_a_skipped_sibling(self):
        self.assertEqual(self._agg([cv.PASS, cv.SKIPPED]), cv.PASS)

    def test_order_independent_with_fail_present(self):
        statuses = [cv.FAIL, cv.CAVEAT, cv.PASS, cv.SKIPPED]
        results = {self._agg(list(p)) for p in itertools.permutations(statuses)}
        self.assertEqual(results, {cv.FAIL})

    def test_order_independent_without_fail(self):
        statuses = [cv.CAVEAT, cv.PASS, cv.SKIPPED]
        results = {self._agg(list(p)) for p in itertools.permutations(statuses)}
        self.assertEqual(results, {cv.CAVEAT})

    def test_order_independent_pass_and_skipped_only(self):
        statuses = [cv.PASS, cv.SKIPPED, cv.PASS, cv.SKIPPED]
        results = {self._agg(list(p)) for p in itertools.permutations(statuses)}
        self.assertEqual(results, {cv.PASS})


if __name__ == "__main__":
    unittest.main()
