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
from tests.helpers import REPO_ROOT

_REPO = REPO_ROOT
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
    """Inject a synthetic actual-tail part (the C3c RT-gated benchmark).

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

    def test_volume_band_gen_floor(self):
        # Rubric v3.4 (owner amendment 2026-08-18): the volume band is floored
        # at 3.0% of ACTUAL total generation — the share leg's own declared
        # mix-materiality — before the 8 TWh cap. Pins the three regimes of
        # _fuelmix_vol_band:
        #  * deep net-importer (gen > 2/3 load): floor binds and widens the band
        self.assertAlmostEqual(cv._fuelmix_vol_band(207.40, 175.74), 5.2722)
        #  * gen ≤ 2/3 load: the 2%-of-load term still governs, band unchanged
        self.assertAlmostEqual(cv._fuelmix_vol_band(100.0, 60.0), 2.0)
        #  * large ISO: the 8 TWh cap tops the band either way (bit-identical
        #    to the pre-v3.4 band, so PJM/MISO-scale gates are unchanged)
        self.assertAlmostEqual(cv._fuelmix_vol_band(721.0, 721.0), 8.0)
        # End-to-end on the CAISO-2023 geometry that motivated the amendment:
        # CC_REGULAR −4.244 TWh in a 207.4 TWh-load / 175.7 TWh-actual-gen
        # system fails the load term alone (±4.148) but passes the floored
        # band (±5.272) with the share leg in band (−1.8 pp) -> PASS; a miss
        # beyond the floored band still FAILs on volume.
        actual = {"CC_REGULAR": 51.8, "CT_PEAKER": 10.0}
        nonfossil = {"nuclear": 40.0, "wind": 30.0, "solar": 43.9}
        classfull = {**actual, **nonfossil}
        lmp = {f"Z{i}": {"d": 207.40 / 4} for i in range(4)}
        for cc_model, want in ((47.556, cv.PASS), (46.4, cv.FAIL)):
            gm = {**classfull, "CC_REGULAR": cc_model}
            ypay = {"gmModel": gm, "nonfossil": dict(nonfossil), "lmp": lmp}
            ybench = {"classFull": dict(classfull), "e930": dict(nonfossil)}
            rows = cv.score_fuelmix(2024, ypay, ybench)
            cc = [r for r in rows if r["key"] == "CC_REGULAR"][0]
            self.assertEqual(cc["status"], want)
            self.assertIn("max(2.0% ISO-load, 3% actual-gen)", cc["tol"])

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
            # v2.5: prelim vintage never gated — diagnostic row only.
            self.assertEqual(gas["status"], cv.SKIPPED)
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
            self.assertEqual(gas["status"], cv.SKIPPED)  # v2.5: prelim not gated
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
            # v2.5: prelim vintage never gated — anchor is a diagnostic.
            self.assertEqual(coal["status"], cv.SKIPPED)
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
            self.assertEqual(
                gas["status"], cv.SKIPPED
            )  # v2.5: prelim not gated (+0.8% diag)
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
            self.assertEqual(gas["status"], cv.SKIPPED)  # v2.5: prelim not gated
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
            self.assertEqual(
                coal["status"], cv.SKIPPED
            )  # v2.5: prelim not gated (raw-cell diagnostic)
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
            self.assertEqual(gas["status"], cv.SKIPPED)  # v2.5: prelim not gated
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

    def test_partial_month_dropped_from_both_sides_of_c3a(self):
        """A month staged from a fraction of its hours leaves the comparison.

        MISO 2022 is the case: the hub staging stops 2022-11-11 RT, so the
        committed December "month mean" is $22.82 built from ONE HOUR while
        the model's December carries the whole of Winter Storm Elliott.
        Scoring them against each other measures the staging hole. Both sides
        must fall back to the fully-staged months — and the ACTUAL must move
        too, or the mask just re-creates the mismatch on the other side.
        """
        model_mon = [50.0] * 10 + [90.0, 120.0]
        ypay = {"lmp": {"Z": {"pMon": model_mon, "dMon": [8.3] * 12}}}
        bench = {
            "avgLMP": {
                "rt_lw": 55.0,  # over the staged hours, partial months included
                "rt_lw_mon": [50.0] * 10 + [38.4, 22.8],
                "rt_cov": {"mon": [1.0] * 10 + [0.3653, 0.0013]},
            }
        }
        r = cv.score_price_mean(2022, ypay, bench)
        # Model masked to Jan-Oct (all 50.0) and the actual re-measured over
        # the same ten months (also 50.0) -> a clean 0% PASS. Un-masked this
        # is model 58.3 vs actual 55.0.
        self.assertEqual(r["status"], cv.PASS)
        self.assertEqual(r["model"], 50.0)
        self.assertEqual(r["actual"], 50.0)
        self.assertIn("fully-staged", r["metric"])

    def test_partial_month_dropped_from_c3b_nrmse(self):
        """C3b drops the same months — squaring makes a stub month dominate."""
        ypay = {"lmp": {"Z": {"pMon": [50.0] * 10 + [90.0, 120.0], "dMon": [8.3] * 12}}}
        cov = {"mon": [1.0] * 10 + [0.3653, 0.0013]}
        actual_mon = [50.0] * 10 + [38.4, 22.8]
        masked = cv.score_price_shape(
            2022, ypay, {"avgLMP": {"rt_lw_mon": actual_mon, "rt_cov": cov}}
        )
        unmasked = cv.score_price_shape(
            2022, ypay, {"avgLMP": {"rt_lw_mon": actual_mon}}
        )
        self.assertEqual(masked["status"], cv.PASS)
        self.assertEqual(masked["model"], 0.0)  # ten identical months
        self.assertEqual(unmasked["status"], cv.FAIL)  # the two stub months
        self.assertIn("dropped as partially staged", masked["metric"])

    def test_complete_coverage_vector_is_a_no_op(self):
        """An ISO-year staged complete scores exactly as it did before.

        The guard that keeps this repair from being a gate change: with every
        month at or above the threshold the mask must not fire at all, so the
        record is byte-identical to the no-coverage-vector case.
        """
        ypay = {
            "lmp": {
                "Z": {"pMon": [30.0] * 12, "dMon": [8.3] * 12, "p": 30.0, "d": 100.0}
            }
        }
        base = {"rt_lw": 30.5, "rt_lw_mon": [30.5] * 12}
        full = dict(base, rt_cov={"mon": [1.0] * 12})
        near = dict(base, rt_cov={"mon": [0.9919] + [1.0] * 11})  # SPP's January
        self.assertEqual(
            cv.score_price_mean(2024, ypay, {"avgLMP": base}),
            cv.score_price_mean(2024, ypay, {"avgLMP": full}),
        )
        self.assertEqual(
            cv.score_price_mean(2024, ypay, {"avgLMP": base}),
            cv.score_price_mean(2024, ypay, {"avgLMP": near}),
        )
        self.assertEqual(
            cv.score_price_shape(2024, ypay, {"avgLMP": base}),
            cv.score_price_shape(2024, ypay, {"avgLMP": near}),
        )

    def test_coverage_threshold_sits_in_an_empty_interval(self):
        """The threshold cannot be a fitted choice: no month lives near it.

        Every monthly coverage value the repo commits is either <= 0.3653 (a
        staging hole) or >= 0.9677 (essentially complete). If a future intake
        lands a month inside that gap, this test fails and the value stops
        being outcome-neutral — which is exactly when it needs re-deciding
        rather than silently keeping its current partition.

        The upper edge was 0.9911 until 5e6d3224 (2026-09-13) staged MISO 2021
        DA, whose October is 30/31 days (0.9677) because MISO's own archive
        omits Oct 28. That is the "loses a day to the source's own publication
        gap" case the threshold's rationale already names; every threshold in
        (0.3654, 0.9677) yields the same partition, so 0.90 is still
        outcome-neutral and the edge moves with the measurement (Y-30).
        """
        import json

        rec = json.loads(
            (
                _REPO / "data" / "raw" / "_validation-source" / "actual_lmp.json"
            ).read_text()
        )
        vals = []
        for _iso, yrs in rec.items():
            if not isinstance(yrs, dict):
                continue
            for _y, blk in yrs.items():
                if not isinstance(blk, dict):
                    continue
                for mkt in ("da", "rt"):
                    cov = blk.get(f"{mkt}_cov")
                    if isinstance(cov, dict) and cov.get("mon"):
                        vals += [float(c) for c in cov["mon"] if c is not None]
        self.assertTrue(vals, "no coverage vectors committed at all")
        inside = [v for v in vals if 0.3654 < v < 0.9677]
        self.assertEqual(
            inside, [], f"coverage values now sit near the threshold: {inside}"
        )
        self.assertTrue(0.3654 < cv.PRICE_MONTH_COVERAGE_MIN < 0.9677)

    def test_tail_skipped_without_ordc(self):
        rows = cv.score_price_tail(2024, {"lmp": {}}, "PJM")
        self.assertEqual(rows[0]["status"], cv.SKIPPED)

    def test_tail_skipped_without_committed_part(self):
        # No committed RT actual for the ISO-year -> SKIPPED (the payload's
        # own RT count never gates; the committed part is the actual).
        _tail({})
        try:
            ypay = {"ordc": {"hoursGt200": {"actual": 100, "model": 50}}}
            rows = cv.score_price_tail(2024, ypay, "PJM")
            self.assertEqual(rows[0]["status"], cv.SKIPPED)
            self.assertEqual(len(rows), 1)  # no committed DA count -> no diag
        finally:
            _reset_tail()

    def test_tail_gates_on_rt_not_da(self):
        # v2.7 owner amendment (2026-07-16): every ISO gates on the ACTUAL RT
        # scarcity tail. Model 60h vs the committed RT 100h is 0.60x, inside
        # [0.5x, 2x] -> PASS (vs the DA 24h it would read 2.5x, a FAIL). The
        # DA count appears only in the non-gated diagnostic row.
        _tail({"MISO": {"2024": {"da_gt": 24, "rt_gt": 100, "rt_coverage": 1.0}}})
        try:
            ypay = {"ordc": {"hoursGt200": {"actual": 100, "model": 60}}}
            rows = cv.score_price_tail(2024, ypay, "MISO")
            main = rows[0]
            self.assertEqual(main["status"], cv.PASS)
            self.assertEqual(main["actual"], 100.0)
            self.assertIn("RT", main["metric"])
            da = [r for r in rows if r["key"] == "da_diagnostic"][0]
            self.assertEqual(da["actual"], 24.0)
            self.assertEqual(da["status"], cv.SKIPPED)
            self.assertIn("forecast-risk premium", da["metric"])
        finally:
            _reset_tail()

    def test_tail_collapsed_fails(self):
        # A collapsed tail (0h) against a material actual FAILs — bounded
        # below on purpose, unchanged in spirit from v1.
        _tail({"ERCOT": {"2024": {"da_gt": 68, "rt_gt": 53, "da_coverage": 1.0}}})
        try:
            ypay = {"ordc": {"hoursGt200": {"actual": 53, "model": 0}}}
            rows = cv.score_price_tail(2024, ypay, "ERCOT")
            self.assertEqual(rows[0]["status"], cv.FAIL)
            self.assertEqual(rows[0]["classification"], cv.MODEL_MISS)
        finally:
            _reset_tail()

    def test_ercot_tail_gates_on_rt_da_diagnostic(self):
        # RT gating (ERCOT since v2.6(a), every ISO since v2.7): the DA tail
        # embeds the day-ahead forecast-risk premium a realized-weather
        # backcast is out of representation to price (ERCOT DA > RT; 2023:
        # 311 vs 181 h). Model 30h vs RT 53h is 0.57x -> PASS (vs DA 68h it
        # would read 0.44x, a FAIL); the DA count sits in the non-gated
        # da_diagnostic row.
        _tail(
            {
                "ERCOT": {
                    "2024": {
                        "da_gt": 68,
                        "rt_gt": 53,
                        "da_coverage": 1.0,
                        "rt_coverage": 1.0,
                    }
                }
            }
        )
        try:
            ypay = {"ordc": {"hoursGt200": {"actual": 53, "model": 30}}}
            rows = cv.score_price_tail(2024, ypay, "ERCOT")
            main = rows[0]
            self.assertEqual(main["actual"], 53.0)  # RT-gated
            self.assertEqual(main["status"], cv.PASS)
            self.assertIn("RT", main["metric"])
            da = [r for r in rows if r["key"] == "da_diagnostic"][0]
            self.assertEqual(da["actual"], 68.0)
            self.assertEqual(da["status"], cv.SKIPPED)
            self.assertIn("forecast-risk premium", da["metric"])
        finally:
            _reset_tail()

    def test_tail_band_and_overfire(self):
        # [0.5x, 2x] on the RT actual: 1.8x PASSes, 2.5x (invented tail) FAILs,
        # 0.4x FAILs. NEISO metric label carries the $300 winter proxy.
        _tail({"NEISO": {"2024": {"da_gt": 60, "rt_gt": 100, "rt_coverage": 1.0}}})
        try:
            for model, want in ((180, cv.PASS), (250, cv.FAIL), (40, cv.FAIL)):
                ypay = {"ordc": {"hoursGt200": {"actual": 60, "model": model}}}
                rows = cv.score_price_tail(2024, ypay, "NEISO")
                self.assertEqual(rows[0]["status"], want, model)
            self.assertIn("300", rows[0]["metric"])
        finally:
            _reset_tail()

    def test_tail_small_count_absolute_guard(self):
        # RT actual below 10h: the ratio is degenerate, so |model-actual| <= 10h
        # gates instead — model 0h vs RT 6h PASSes (an hourly model showing no
        # tail against a handful of RT hours is within noise), model 30h vs RT
        # 6h FAILs (invented tail; also the v1 quiet-actual token guard, now
        # tighter at 10h instead of 50h).
        _tail({"PJM": {"2023": {"da_gt": 8, "rt_gt": 6, "rt_coverage": 1.0}}})
        try:
            ypay = {"ordc": {"hoursGt200": {"actual": 6, "model": 0}}}
            rows = cv.score_price_tail(2023, ypay, "PJM")
            self.assertEqual(rows[0]["status"], cv.PASS)
        finally:
            _reset_tail()
        _tail({"PJM": {"2023": {"da_gt": 2, "rt_gt": 6, "rt_coverage": 1.0}}})
        try:
            ypay = {"ordc": {"hoursGt200": {"actual": 6, "model": 30}}}
            rows = cv.score_price_tail(2023, ypay, "PJM")
            self.assertEqual(rows[0]["status"], cv.FAIL)
        finally:
            _reset_tail()

    def test_tail_partial_coverage_noted(self):
        # An RT series with partial coverage (CAISO 2023 Jan-Feb aged out of
        # OASIS retention) is a lower bound — surfaced in the magnitude.
        _tail({"CAISO": {"2023": {"da_gt": 41, "rt_gt": 21, "rt_coverage": 0.819}}})
        try:
            ypay = {"ordc": {"hoursGt200": {"actual": 21, "model": 30}}}
            rows = cv.score_price_tail(2023, ypay, "CAISO")
            self.assertIn("lower bound", rows[0]["magnitude"])
        finally:
            _reset_tail()


# (StorageTests — the C5b score_storage suite — was removed with the criterion
# by the rubric v2.7 owner amendment 2026-07-16; the dispatch-correlation
# tests it also carried live on below.)
class DispatchCorrTests(unittest.TestCase):
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
        # CAISO from the onset vintage on: the gas fit is recomputed from the
        # committed hourly series (payload m vs bench campd + flat cogen block)
        # — the 930-based payload values (r=0.10) score the corrupted
        # benchmark, not the model. The year is derived from the registry so
        # the boundary test survives an onset move (it went 2024 -> 2023 on the
        # 2026-07-26 owner ruling); the onset VALUE is pinned by
        # tests/scoring/test_benchmark_semantics.py.
        ypay, ybench = self._cems_fixture()
        gas = [
            r
            for r in cv.score_dispatch_corr(
                cv.CEMS_GAS_ANCHOR_ONSET["CAISO"], ypay, ybench, "CAISO"
            )
            if r["key"] == "gas"
        ][0]
        self.assertIn("r=1.0", gas["model"])  # identical shapes -> r ~ 1.0
        self.assertIn("CEMS", gas["metric"])

    def test_dispatch_corr_cems_pre_onset_keeps_930(self):
        # The vintage below the onset keeps the committed 930-based fit — the
        # anchor is applied from the onset forward, never retroactively to
        # every year. Derived from the registry for the same reason as above.
        ypay, ybench = self._cems_fixture()
        gas = [
            r
            for r in cv.score_dispatch_corr(
                cv.CEMS_GAS_ANCHOR_ONSET["CAISO"] - 1, ypay, ybench, "CAISO"
            )
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


class AuthorizedPriceTuningTests(unittest.TestCase):
    """Rule 1 ``[R-STRUCT]`` carve-out (owner ruling 2026-09-05).

    The registered offer-curve band multipliers are an authorized price-tuning
    channel, so the two channel-scoped assertions may read false WHEN the run
    declares the channel. Every test here also pins that the carve-out FAILS
    CLOSED — it must never become a blanket exemption.
    """

    CFG = {"scenario_config": {"outage_source": "historic"}}
    YEARS = [2023, 2024, 2025]

    def _tuned(self, **over):
        """A clean attestation with both scoped assertions false + a declaration."""
        att = _clean_attestation()
        att["governance"]["no_fit_to_price_residuals"] = False
        att["governance"]["levers_trace_to_measured_input"] = False
        dec = {
            "channel": "offer_curve_by_group",
            "ruling": "owner ruling 2026-09-05",
            "value": "x1.10 on 11 non-steam fossil classes",
            "years_held": [2023, 2024, 2025],
            "set_ex_ante": True,
            "not_swept": True,
        }
        dec.update(over)
        att["governance"]["authorized_price_tuning"] = dec
        return att

    def test_declared_channel_scopes_the_two_assertions(self):
        g = cv.score_governance(self.CFG, self._tuned(), self.YEARS)
        self.assertEqual(g["status"], cv.PASS)
        self.assertIn("authorized price tuning declared", g["metric"] + g["magnitude"])

    def test_undeclared_price_fit_still_fails(self):
        # The amendment authorizes a DECLARED channel, never silence.
        att = _clean_attestation()
        att["governance"]["no_fit_to_price_residuals"] = False
        g = cv.score_governance(self.CFG, att, self.YEARS)
        self.assertEqual(g["status"], cv.FAIL)

    def test_wrong_channel_fails(self):
        g = cv.score_governance(
            self.CFG, self._tuned(channel="magic_adder"), self.YEARS
        )
        self.assertEqual(g["status"], cv.FAIL)

    def test_swept_value_fails(self):
        # Condition (c): selecting a factor by sweeping against the gates stays
        # forbidden — that is the fitted-mechanism selection rule 1 forbids.
        g = cv.score_governance(self.CFG, self._tuned(not_swept=False), self.YEARS)
        self.assertEqual(g["status"], cv.FAIL)

    def test_not_set_ex_ante_fails(self):
        g = cv.score_governance(self.CFG, self._tuned(set_ex_ante=False), self.YEARS)
        self.assertEqual(g["status"], cv.FAIL)

    def test_per_year_config_fails(self):
        # Condition (b): ONE config across EVERY scored year.
        g = cv.score_governance(self.CFG, self._tuned(years_held=[2025]), self.YEARS)
        self.assertEqual(g["status"], cv.FAIL)

    def test_incomplete_declaration_fails(self):
        att = self._tuned()
        del att["governance"]["authorized_price_tuning"]["ruling"]
        g = cv.score_governance(self.CFG, att, self.YEARS)
        self.assertEqual(g["status"], cv.FAIL)

    def test_carve_out_does_not_reach_pinning(self):
        # The carve-out scopes exactly two assertions. Pinning to actuals is
        # never scoped, however well the channel is declared.
        att = self._tuned()
        att["governance"]["no_pinning_to_actuals"] = False
        g = cv.score_governance(self.CFG, att, self.YEARS)
        self.assertEqual(g["status"], cv.FAIL)

    def test_forbidden_flag_machine_check_untouched(self):
        g = cv.score_governance(
            {"scenario_config": {"outage_source": "fitted"}}, self._tuned(), self.YEARS
        )
        self.assertEqual(g["status"], cv.FAIL)

    def test_clean_keeper_without_declaration_unaffected(self):
        # The amendment must be a no-op for every existing keeper.
        g = cv.score_governance(self.CFG, _clean_attestation(), self.YEARS)
        self.assertEqual(g["status"], cv.PASS)

    def test_malformed_declaration_on_otherwise_clean_run_fails(self):
        # Declared but malformed, with both assertions true: never silently carried.
        att = _clean_attestation()
        att["governance"]["authorized_price_tuning"] = {
            "channel": "offer_curve_by_group"
        }
        g = cv.score_governance(self.CFG, att, self.YEARS)
        self.assertEqual(g["status"], cv.FAIL)


class PerYearGovernanceScopeTests(unittest.TestCase):
    """Rule 1 (b) is asked of the RUN, never of a display subset of its years.

    ``build_status.build_years`` (the rule 30 (b) per-year ladder) and the
    partition-span callers in ``build_status`` / ``audit_keepers`` score one
    year of a multi-year run at a time. Before the neiso-107 fix that subset
    reached ``score_governance``, so a legitimate ``years_held``
    ``[2023, 2024, 2025]`` was compared against ``[2023]`` and FAILED — which
    rendered NOT-YET on every year of NEISO's and MISO's CALIBRATED keepers
    (``results/calibration/FINDING-neiso106-per-year-ladder-governance-defect-2026-09-06.md``).

    These tests pin BOTH halves: the span filter no longer breaks a run-level
    declaration, AND a genuinely per-year declaration still FAILs — the failure
    mode rule 1 (b) exists to catch, which a subset test would have let through.
    """

    YEARS = (2023, 2024, 2025)

    def _art(self, years_held):
        """A clean 3-year artifact declaring the authorized price-tuning channel."""
        det = DeterminationTests()
        art = _artifacts(
            det._clean_year_payload(),
            target_years=list(self.YEARS),
            **det._clean_bench_args(),
        )
        # Fan the single clean year/bench fixture across all three years.
        ypay = art["payload"]["years"]["2024"]
        ybench = art["bench"][2024]
        art["payload"]["years"] = {str(y): ypay for y in self.YEARS}
        art["bench"] = {y: ybench for y in self.YEARS}
        att = _clean_attestation()
        att["governance"]["no_fit_to_price_residuals"] = False
        att["governance"]["levers_trace_to_measured_input"] = False
        att["governance"]["authorized_price_tuning"] = {
            "channel": "offer_curve_by_group",
            "ruling": "owner ruling 2026-09-05",
            "value": "x1.10 on the non-steam fossil bands",
            "years_held": list(years_held),
            "set_ex_ante": True,
            "not_swept": True,
        }
        art["attestation"] = att
        return art

    def _gov(self, art, years=None):
        v = cv.determine_from_artifacts("t", art, years=years)
        return v["criteria"]["governance"]["status"], v

    def test_full_span_passes(self):
        # Baseline: unrestricted, the declaration covers the run's scored span.
        status, _ = self._gov(self._art(self.YEARS))
        self.assertEqual(status, cv.PASS)

    def test_single_year_subset_still_passes(self):
        # THE DEFECT. Each year rendered on its own must read the run's own
        # governance verdict, not FAIL on {2023,2024,2025} != {2023}.
        art = self._art(self.YEARS)
        for year in self.YEARS:
            with self.subTest(year=year):
                status, v = self._gov(art, years=[year])
                self.assertEqual(status, cv.PASS)
                self.assertEqual(v["scorable_years"], [year])
                self.assertNotIn(
                    "does not cover every scored year", " ".join(v["reasons"] or [])
                )

    def test_partition_span_subset_still_passes(self):
        # The same category error reached the two-config partition-span callers
        # (build_status / audit_keepers, owner two-config ruling 2026-08-26).
        status, _ = self._gov(self._art(self.YEARS), years=[2024, 2025])
        self.assertEqual(status, cv.PASS)

    def test_genuinely_per_year_declaration_still_fails_full_span(self):
        # The equality is NOT relaxed: a config held on ONE of three scored
        # years is per-year fitting and still FAILs rule 1 (b).
        status, v = self._gov(self._art([2025]))
        self.assertEqual(status, cv.FAIL)
        self.assertIn("does not cover every scored year", " ".join(v["reasons"] or []))
        self.assertEqual(v["determination"], cv.NOT_YET)

    def test_genuinely_per_year_declaration_still_fails_on_its_own_year(self):
        # And the fix must not create a hole: rendering the ONE year the
        # per-year config was held on must NOT make it pass. This is the
        # failure mode a subset test would have let through.
        status, v = self._gov(self._art([2025]), years=[2025])
        self.assertEqual(status, cv.FAIL)
        self.assertIn("does not cover every scored year", " ".join(v["reasons"] or []))
        self.assertEqual(v["determination"], cv.NOT_YET)


class LedgerTests(unittest.TestCase):
    def test_documented_fail_becomes_caveat(self):
        # v3.1: only C3c (price_tail) is ledgerable at all, so the documented
        # FAIL -> ledgered CAVEAT path is exercised there.
        rec = {
            "criterion": "price_tail",
            "key": None,
            "year": 2024,
            "status": cv.FAIL,
            "classification": cv.MODEL_MISS,
        }
        cv._apply_ledger(
            rec,
            [
                {
                    "criterion": "price_tail",
                    "year": 2024,
                    "reason": "data-blocked scarcity requirement series",
                }
            ],
        )
        self.assertEqual(rec["status"], cv.CAVEAT)
        self.assertEqual(rec["classification"], cv.MEASURED_LIMIT)

    def test_unmatched_fail_stays_fail(self):
        rec = {
            "criterion": "price_tail",
            "key": None,
            "year": 2024,
            "status": cv.FAIL,
            "classification": cv.MODEL_MISS,
        }
        cv._apply_ledger(rec, [{"criterion": "sysvol", "family": "gas", "year": 2024}])
        self.assertEqual(rec["status"], cv.FAIL)

    def test_price_tail_is_the_only_ledgerable_criterion(self):
        # v3.1 owner amendment 2026-08-06: C3c is the sole ledgerable criterion.
        self.assertEqual(cv.LEDGERABLE_CRITERIA, frozenset({"price_tail"}))

    def test_price_mean_fail_is_never_ledgerable(self):
        # v3.1 fail-closed guard, the amendment's headline case: a mean-LMP miss
        # beyond +/-10% is a MODEL MISS and no ledger entry — measured-input or
        # model-class — may reclassify it. Ledgering C3a certified a price level
        # the model does not reproduce (the CAISO caiso-175 case: 2024 +11.7%,
        # 2025 +14.8%, carried as CALIBRATED-WITH-CAVEATS until this amendment).
        for entry in (
            {"criterion": "price_mean", "year": 2025, "reason": "unrestrained PS"},
            {"criterion": "price_mean", "year": 2025, "kind": "model-class"},
        ):
            rec = {
                "criterion": "price_mean",
                "key": None,
                "year": 2025,
                "status": cv.FAIL,
                "classification": cv.MODEL_MISS,
            }
            cv._apply_ledger(rec, [entry])
            self.assertEqual(rec["status"], cv.FAIL, entry)
            self.assertEqual(rec["classification"], cv.MODEL_MISS, entry)
            self.assertNotIn("ledger_reason", rec)

    def test_other_criteria_are_never_ledgerable(self):
        # Every non-C3c criterion, including the ones whose entries sit on
        # already-committed attestations (fuelmix / sysvol / dispatch_corr):
        # the entry stays on the bundle as the historical record but no longer
        # reclassifies, so keepers re-score in place with no re-solve.
        for criterion, key in (
            ("fuelmix", "CT_PEAKER"),
            ("sysvol", "gas"),
            ("price_shape", None),
            ("dispatch_corr", "gas"),
            ("forced_share", "CT_PEAKER"),
        ):
            rec = {
                "criterion": criterion,
                "key": key,
                "year": 2024,
                "status": cv.FAIL,
                "classification": cv.MODEL_MISS,
            }
            cv._apply_ledger(
                rec,
                [
                    {
                        "criterion": criterion,
                        "klass": key,
                        "family": key,
                        "year": 2024,
                        "reason": "documented limitation",
                    }
                ],
            )
            self.assertEqual(rec["status"], cv.FAIL, criterion)

    def test_model_class_entry_caveats_supporting_criterion(self):
        # v3.0: kind=model-class reclassifies a SUPPORTING-tier FAIL to a
        # ledgered CAVEAT with the MODEL_LIMIT classification.
        rec = {
            "criterion": "price_tail",
            "key": None,
            "year": 2023,
            "status": cv.FAIL,
            "classification": cv.MODEL_MISS,
        }
        cv._apply_ledger(
            rec,
            [
                {
                    "criterion": "price_tail",
                    "year": 2023,
                    "kind": "model-class",
                    "reason": "owner-accepted LP-class scarcity-tail limit",
                }
            ],
        )
        self.assertEqual(rec["status"], cv.CAVEAT)
        self.assertEqual(rec["classification"], cv.MODEL_LIMIT)
        self.assertIn("scarcity-tail", rec["ledger_reason"])

    def test_model_class_entry_ignored_on_load_bearing_criterion(self):
        # v3.0 fail-closed guard: a model-class entry can never wave through a
        # load-bearing (or protective) criterion — the FAIL stands.
        rec = {
            "criterion": "price_mean",
            "key": None,
            "year": 2023,
            "status": cv.FAIL,
            "classification": cv.MODEL_MISS,
        }
        cv._apply_ledger(
            rec,
            [{"criterion": "price_mean", "year": 2023, "kind": "model-class"}],
        )
        self.assertEqual(rec["status"], cv.FAIL)
        self.assertEqual(rec["classification"], cv.MODEL_MISS)

    def test_model_class_entry_ignored_on_protective_criterion(self):
        rec = {
            "criterion": "forced_share",
            "key": "COAL_LIGNITE",
            "year": 2023,
            "status": cv.FAIL,
            "classification": cv.MODEL_MISS,
        }
        cv._apply_ledger(
            rec,
            [
                {
                    "criterion": "forced_share",
                    "klass": "COAL_LIGNITE",
                    "year": 2023,
                    "kind": "model-class",
                }
            ],
        )
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

    def test_documented_non_c3c_fail_is_not_excused(self):
        # ST_GAS (9 TWh actual) overshoots by +9 TWh: past the 8 TWh cap, so the
        # miss exceeds the volume band under ANY percent term (rubric v3.4 floors
        # the band at 3% of actual gen, which this fixture's 409 TWh gen would
        # otherwise widen past the old +5 TWh miss) -> the class FAILs C1 on
        # volume (share stays within 3.0pp), but C2 defers to C1 for the
        # fully-reported family so it still PASSes.
        # RUBRIC v3.1 (owner amendment 2026-08-06): the ledger entry documenting
        # that C1 fail no longer reclassifies it — C3c is the only ledgerable
        # criterion — so the FAIL stands and the determination is NOT-YET. (This
        # test pinned the OPPOSITE behaviour through v3.0, where the same fixture
        # scored CALIBRATED-WITH-CAVEATS on a documented C1 miss.)
        ypay = {
            "gmModel": {
                "CC_REGULAR": 325.0,
                "CT_PEAKER": 20.0,
                "ST_GAS": 18.0,
                "COAL_BIT": 55.0,
            },
            "nonfossil": {"nuclear": 270.0, "wind": 28.0, "solar": 14.0},
            "fuelRows": [
                {"fuel": "gas", "m": 363, "b": 354, "r": 0.8, "nrmse": 0.15},
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
                    "magnitude": "+9.0 TWh",
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
        self.assertEqual(v["criteria"]["fuelmix"]["status"], cv.FAIL)
        self.assertEqual(v["criteria"]["sysvol"]["status"], cv.PASS)
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertEqual(v["caveats"]["ledgered"], [])

    def test_only_c3c_can_consume_a_ledgered_slot(self):
        # RUBRIC v3.1 (owner amendment 2026-08-06). This test replaces
        # test_ledgered_caveat_budget_is_three, which pinned the v2/v3.0 rule
        # that any criterion could be ledgered up to a budget of 3.
        #
        # The fixture presents FOUR documented out-of-band results at once
        # (price_mean -13.8%, price_shape NRMSE 0.241, price_tail 0.25x,
        # dispatch_corr gas r=0.55), each with its own attestation entry — the
        # exact shape that scored CALIBRATED-WITH-CAVEATS on three slots before.
        # Now only C3c is ledgerable, so the other three stay FAILs and carry
        # the determination to NOT-YET; the ledgered list holds C3c alone.
        def art_with(gas_r):
            ypay = self._clean_year_payload()
            ypay["lmp"]["Z"]["p"] = 25.0  # -13.8% vs rt 29.0: beyond ±10% comm.
            ypay["ordc"] = {"hoursGt200": {"actual": 100, "model": 25}}  # 0.25x
            ypay["lmp"]["Z"]["pMon"] = [22] * 12  # NRMSE 0.241 > 0.20 -> FAIL
            ypay["fuelRows"][0]["r"] = gas_r
            att = _clean_attestation(
                exceptions=[
                    {"criterion": "price_mean", "year": 2024, "reason": "documented"},
                    {"criterion": "price_shape", "year": 2024, "reason": "documented"},
                    {"criterion": "price_tail", "year": 2024, "reason": "documented"},
                    {
                        "criterion": "dispatch_corr",
                        "family": "gas",
                        "year": 2024,
                        "reason": "documented",
                    },
                ]
            )
            return _artifacts(ypay, attestation=att, **self._clean_bench_args())

        _tail({"PJM": {"2024": {"da_gt": 80, "rt_gt": 100, "rt_coverage": 1.0}}})
        try:
            for gas_r in (0.55, 0.80):
                v = cv.determine_from_artifacts("t", art_with(gas_r))
                self.assertEqual(v["determination"], cv.NOT_YET)
                # C3c is ledgered; the three non-ledgerable ones stay FAILs.
                self.assertEqual(v["criteria"]["price_tail"]["status"], cv.CAVEAT)
                self.assertEqual(
                    v["caveats"]["ledgered"], [cv.CRITERIA["price_tail"][0]]
                )
                self.assertEqual(v["criteria"]["price_mean"]["status"], cv.FAIL)
                self.assertEqual(v["criteria"]["price_shape"]["status"], cv.FAIL)
                self.assertIn("price_mean", v["reasons"][0])
        finally:
            _reset_tail()

    def test_caveat_budgets_match_the_ledgerable_set(self):
        # v3.1 invariant: the budgets are not free-floating numbers — they are
        # the arithmetic consequence of LEDGERABLE_CRITERIA. Caveats aggregate
        # per criterion, so the ledgered ceiling is the number of ledgerable
        # non-protective criteria, and the protective ceiling is the number of
        # ledgerable protective ones (zero). Re-widening the ledgerable set
        # without revisiting the budgets fails here.
        by_tier = [
            cv.CRITERIA[c][1] for c in cv.LEDGERABLE_CRITERIA if c in cv.CRITERIA
        ]
        self.assertEqual(
            cv.MAX_LEDGERED_CAVEATS,
            sum(1 for t in by_tier if t != cv.TIER_PROTECT),
        )
        self.assertEqual(
            cv.MAX_PROTECTIVE_CAVEATS,
            sum(1 for t in by_tier if t == cv.TIER_PROTECT),
        )

    def test_commercial_band_caveats_unbudgeted(self):
        # Auto COMMERCIAL_BAND caveats (inside the evidence-anchored outer band,
        # outside target) are listed but never consume the ledger budget.
        #
        # As of the v2.9 owner amendment (2026-07-27) NO SCORED CRITERION CAN
        # PRODUCE ONE. The two-band criteria were price_mean/price_shape (both
        # collapsed to single-band at v2.3: TOL == COMMERCIAL), C2 sysvol (its
        # +/-2.5%//+/-5% band survives only on the preliminary-EIA-923 fallback
        # path, which v2.5 made SKIPPED-never-gated), and C5a co2 -- which this
        # amendment removed from the rubric because eGRID publishes no 2025
        # vintage. So the end-to-end path this test used to drive no longer
        # exists, and fabricating it would test nothing real.
        #
        # Rather than delete the coverage, pin the INVARIANT that makes it
        # unreachable. This assertion fails the moment anyone re-introduces a
        # criterion with a distinct commercial band -- which is exactly when
        # the end-to-end test above must be restored from git history.
        two_band = {
            "price_mean": (cv.PRICE_MEAN_TOL, cv.PRICE_MEAN_COMMERCIAL),
            "price_shape": (
                cv.PRICE_SHAPE_NRMSE_MAX,
                cv.PRICE_SHAPE_NRMSE_COMMERCIAL,
            ),
        }
        for name, (tol, comm) in two_band.items():
            self.assertEqual(
                tol,
                comm,
                f"{name} regained a distinct commercial band -- restore the "
                "end-to-end COMMERCIAL_BAND caveat test (git history, pre-v2.9)",
            )
        self.assertNotIn("co2", cv.CRITERIA)  # removed by v2.9
        self.assertIn("co2", cv.REPORTED_ONLY)  # still scored, not aggregated
        # The classification constant itself stays live for the restoration case.
        self.assertEqual(
            cv._band_result(0.07, 0.05, 0.10), (cv.CAVEAT, cv.COMMERCIAL_BAND)
        )

    def test_v37_an_unscored_c3c_does_not_downgrade(self):
        """Owner instruction 2026-09-10: C3c alone never makes a caveats tag.

        v3.3 made a LEDGERED C3c non-downgrading, but that path runs through
        ``_apply_c3c_standing_rule``, which only ever sees C3c when it is
        SCORED AND FAILING. A SKIPPED C3c fell into the unscored-criteria route
        instead — so the SAME accepted model-class limitation downgraded or did
        not depending on whether the ISO-year happened to have a scarcity
        bench, which is a property of the data, not of the model.
        """
        art = _artifacts(
            self._clean_year_payload(),
            attestation=_clean_attestation(),
            **self._clean_bench_args(),
        )
        # C8 needs a legitimacy artifact or it SKIPS as an unscored PROTECTIVE
        # criterion and downgrades on its own — which is the fail-closed guard
        # working, not the thing under test here.
        art["legitimacy"] = _legit_artifact(r=0.9, cv_ratio=0.02, share=0.05)
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(
            [c for c, b in v["criteria"].items() if b["status"] == cv.SKIPPED],
            ["price_tail"],
            "fixture must isolate C3c as the ONLY unscored criterion",
        )
        self.assertEqual(v["determination"], cv.CALIBRATED)
        # Still NAMED — an exemption nobody can see is the escape hatch rule 22
        # guard (d) exists to prevent.
        self.assertTrue(
            any("rubric v3.7" in r for r in v["reasons"]),
            v["reasons"],
        )

    def test_v37_exemption_never_reaches_a_load_bearing_skip(self):
        """The fail-closed guard: C3c-only, supporting-tier only.

        An unscored LOAD-BEARING criterion must still downgrade, and C3c must
        not be listed among the criteria that did it.
        """
        payload = self._clean_year_payload()
        payload["lmp"] = {}  # removes C3a and C3b as well as C3c
        art = _artifacts(
            payload, attestation=_clean_attestation(), **self._clean_bench_args()
        )
        art["legitimacy"] = _legit_artifact(r=0.9, cv_ratio=0.02, share=0.05)
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["criteria"]["price_mean"]["status"], cv.SKIPPED)
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)
        downgrading = [r for r in v["reasons"] if r.startswith("unscored criteria:")]
        self.assertTrue(downgrading, v["reasons"])
        self.assertIn("price_mean", downgrading[0])
        self.assertNotIn(
            "price_tail",
            downgrading[0],
        )

    def test_protective_gate_is_never_ledgerable(self):
        # RUBRIC v3.1 (owner amendment 2026-08-06). Replaces
        # test_protective_caveat_budget_is_one: the protective tier used to
        # allow ONE ledgered excuse, so a documented C8 forced-share breach
        # could still certify. It cannot now — C3c is the only ledgerable
        # criterion, so a C8 FAIL is NOT-YET whatever the attestation says.
        # This is the anti-self-deception tier getting stricter, not looser
        # (CLAUDE.md rule 20 [R-FORCED-BUDGET]).
        def art_with(legit, exceptions):
            art = _artifacts(
                self._clean_year_payload(),
                attestation=_clean_attestation(exceptions=exceptions),
                **self._clean_bench_args(),
            )
            art["legitimacy"] = legit
            return art

        over_budget = _legit_artifact(r=0.9, cv_ratio=0.02, share=0.55)
        exceptions = [
            {
                "criterion": "forced_share",
                "klass": "CT_PEAKER",
                "year": 2024,
                "reason": "documented",
            },
        ]
        v = cv.determine_from_artifacts("t", art_with(over_budget, exceptions))
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertEqual(v["criteria"]["forced_share"]["status"], cv.FAIL)
        self.assertEqual(v["caveats"]["protective"], [])
        self.assertIn("forced_share", v["reasons"][0])
        # Below the materiality floor the class is not gated at all, so the
        # same artifact certifies — the gate, not the ledger, is what moved.
        # RUBRIC v3.7 (owner instruction 2026-09-10): this reads a clean
        # CALIBRATED rather than CALIBRATED-WITH-CAVEATS. `price_tail` is this
        # fixture's ONLY unscored criterion, and an unscored C3c no longer
        # downgrades — "if c3c is the only caveat the status should be
        # calibrated not with caveats". The protective-tier assertions above
        # are what this test is FOR and they are untouched.
        immaterial = _legit_artifact(r=0.9, cv_ratio=0.02, share=0.05)
        v = cv.determine_from_artifacts("t", art_with(immaterial, exceptions))
        self.assertEqual(v["determination"], cv.CALIBRATED)
        self.assertEqual(
            [c for c, b in v["criteria"].items() if b["status"] == cv.SKIPPED],
            ["price_tail"],
        )

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

    # --- v2.8 coal gate-blindness correction (ERCOT-121) --------------------

    def test_forced_share_plant_group_aggregate_resolves_materiality(self):
        # The D-2 summary labels classes by CAMPD plant_group ("COAL") while
        # the payload/bench carry the scored-class rank split. Pre-v2.8 the
        # materiality lookup read 0.0 on both sides and SKIPPED the whole
        # coal fleet as immaterial; the PLANT_GROUP_MEMBERS bridge now sums
        # the members (59.3 of 400 TWh here — material), so the row gates.
        legit = _legit_artifact(klass="COAL", share=0.001)
        ypay = {
            "gmModel": {"COAL_LIGNITE": 16.7, "COAL_PRB": 42.6, "CC_REGULAR": 340.7}
        }
        ybench = {"classFull": {"COAL_LIGNITE": 15.3, "COAL_PRB": 45.1}}
        recs = cv.score_forced_share(2024, legit, ypay, ybench)
        self.assertEqual(recs[0]["status"], cv.PASS)
        self.assertNotIn("immaterial", recs[0]["magnitude"])

    def test_forced_share_unresolvable_class_still_skips(self):
        # A class name absent from both vocabularies (no aggregate mapping)
        # keeps the pre-v2.8 behaviour: share 0.0 -> SKIPPED-immaterial.
        legit = _legit_artifact(klass="NOT_A_CLASS", share=0.9)
        ypay = {"gmModel": {"CC_REGULAR": 340.7}}
        ybench = {"classFull": {"CC_REGULAR": 341.0}}
        recs = cv.score_forced_share(2024, legit, ypay, ybench)
        self.assertEqual(recs[0]["status"], cv.SKIPPED)
        self.assertIn("immaterial", recs[0]["magnitude"])

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
        self.assertEqual(v["criteria"]["forced_share"]["status"], cv.SKIPPED)
        self.assertNotIn("shape", v["criteria"])  # C7 retired (v3.1)

    def test_flat_floor_forces_not_yet(self):
        """A flat-floor keeper still FAILs -> NOT-YET after C7's retirement.

        This is the regression that the v3.1 C7 removal did not surrender the
        caiso-42 protection. The signature (off-peak CV 0.000 vs a real
        0.35-0.45) used to be caught twice — by C7 on its fixed class tuple and
        by C8's grounded-above-budget escalation. With C7 retired, C8 alone
        catches it: the class is forced past its cap, so the escalation reads
        the SAME D-1 row through ``_d1_shape`` and the flat profile fails it.
        """
        d = DeterminationTests()
        art = _artifacts(
            d._clean_year_payload(),
            attestation=_clean_attestation(),
            **d._clean_bench_args(),
        )
        art["legitimacy"] = _legit_artifact(r=0.9, cv_ratio=0.0, share=0.55)
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertEqual(v["criteria"]["forced_share"]["status"], cv.FAIL)
        self.assertNotIn("shape", v["criteria"])


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


# (StorageShapeScoreTests — the C5c score_storage_shape suite — was removed
# with the criterion by the rubric v2.7 owner amendment 2026-07-16.)


def _i16_b64(vals):
    """Encode a list of ints as the payload's little-endian int16 base64 blob.

    Mirrors ``render_calibration_html._b64_i16``: ``None`` becomes the -32768
    NOT-A-NUMBER sentinel, and the series is padded to 8760 with sentinels.
    """
    import array as _array
    import base64 as _b64
    import sys as _sys

    a = _array.array("h", [(-32768 if v is None else int(v)) for v in vals])
    a.extend([-32768] * (8760 - len(a)))
    if _sys.byteorder != "little":  # pragma: no cover
        a.byteswap()
    return _b64.b64encode(a[:8760].tobytes()).decode()


class DiurnalAmplitudeReportedOnlyTests(unittest.TestCase):
    """D-A (v3.5) — the BAND-FREE reported-only diurnal price-amplitude measure.

    The load-bearing property is the LAST test: this measurement must be
    incapable of gating. It is reported-only by owner decision 2026-08-25
    (option B of docs/DECISION-CARD-xiso-diurnal-amplitude-rubric-2026-08.md),
    because the xiso-6 band sweep found a gating criterion is vacuous below a
    25 % amplitude floor and universal above 45 %, with no external comparable
    to anchor a band.
    """

    # A measured profile with a $10 hour-of-day range (trough h00, peak h12).
    ACTUAL_HOD = [20.0] * 12 + [30.0] * 12

    def _part(self, hod=None):
        return {"PJM": {"2024": {"rt_hod": list(hod or self.ACTUAL_HOD)}}}

    def _score(self, delta_day, part=None, monkey=True):
        """Score one year whose hourly delta repeats ``delta_day`` all year."""
        blob = _i16_b64(list(delta_day) * 365)
        saved = cv._AMPLITUDE_CACHE
        cv._AMPLITUDE_CACHE = self._part() if part is None else part
        try:
            return cv.score_diurnal_amplitude(2024, {"lmpDeltaHr": blob}, "PJM")
        finally:
            cv._AMPLITUDE_CACHE = saved

    def test_zero_delta_reproduces_the_measured_amplitude(self):
        """A model equal to the actual reads 100 % amplitude, phase exact."""
        r = self._score([0] * 24)
        self.assertEqual(r["status"], cv.REPORTED)
        self.assertAlmostEqual(r["amplitude_pct"], 100.0, places=1)
        self.assertTrue(r["phase_ok"])
        self.assertEqual(r["days"], 365)

    def test_compressed_amplitude_is_measured(self):
        """Halving the swing (peak -$5) reads 50 %, and stays band-free."""
        r = self._score([0] * 12 + [-5] * 12)
        self.assertAlmostEqual(r["amplitude_pct"], 50.0, places=1)
        self.assertIsNone(r["tol"])  # BAND-FREE: no threshold to state
        self.assertIsNone(r["classification"])

    def test_sentinel_hours_drop_their_whole_day(self):
        """A -32768 sentinel masks its day rather than corrupting the profile.

        This is the MISO-2025 defect: one NaN actual hour (h8759) encodes as the
        sentinel, and reading it as a value blows the amplitude from 20.8 % to
        186.9 %. The day-drop is what keeps the statistic honest.
        """
        blob = _i16_b64([0] * 8759 + [None])
        saved = cv._AMPLITUDE_CACHE
        cv._AMPLITUDE_CACHE = self._part()
        try:
            r = cv.score_diurnal_amplitude(2024, {"lmpDeltaHr": blob}, "PJM")
        finally:
            cv._AMPLITUDE_CACHE = saved
        self.assertEqual(r["status"], cv.REPORTED)
        self.assertEqual(r["days"], 364)  # the sentinel-bearing day dropped
        self.assertAlmostEqual(r["amplitude_pct"], 100.0, places=1)

    def test_phase_error_is_reported_not_penalised(self):
        """A shifted peak reports phase OFF — and still carries no verdict."""
        r = self._score([10] * 6 + [0] * 18)  # pushes the model peak to h00-h05
        self.assertEqual(r["status"], cv.REPORTED)
        self.assertFalse(r["phase_ok"])
        self.assertIsNone(r["tol"])

    def test_skips_without_a_committed_part(self):
        r = self._score([0] * 24, part={})
        self.assertEqual(r["status"], cv.SKIPPED)

    def test_skips_when_payload_predates_the_field(self):
        saved = cv._AMPLITUDE_CACHE
        cv._AMPLITUDE_CACHE = self._part()
        try:
            r = cv.score_diurnal_amplitude(2024, {}, "PJM")
        finally:
            cv._AMPLITUDE_CACHE = saved
        self.assertEqual(r["status"], cv.SKIPPED)

    def test_degenerate_measured_range_skips(self):
        """A flat measured profile has no amplitude to be a fraction of."""
        r = self._score([0] * 24, part={"PJM": {"2024": {"rt_hod": [25.0] * 24}}})
        self.assertEqual(r["status"], cv.SKIPPED)

    def test_IT_CANNOT_GATE(self):
        """The load-bearing guarantee: D-A can never touch a determination.

        It is absent from CRITERIA (so it never reaches per_criterion, any
        caveat budget or grade_summary) and absent from LEDGERABLE_CRITERIA,
        and REPORTED is not one of the four scored statuses.
        """
        self.assertIn("diurnal_amplitude", cv.REPORTED_ONLY)
        self.assertNotIn("diurnal_amplitude", cv.CRITERIA)
        self.assertNotIn("diurnal_amplitude", cv.LEDGERABLE_CRITERIA)
        self.assertEqual(cv.LEDGERABLE_CRITERIA, frozenset({"price_tail"}))
        self.assertEqual(cv.MAX_LEDGERED_CAVEATS, 1)
        self.assertEqual(cv.MAX_PROTECTIVE_CAVEATS, 0)
        self.assertNotIn(cv.REPORTED, (cv.PASS, cv.CAVEAT, cv.FAIL, cv.SKIPPED))
        # A REPORTED record aggregates to nothing a criterion could read.
        self.assertEqual(cv._agg_status([{"status": cv.REPORTED}]), cv.SKIPPED)


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

    def test_apply_ledger_end_to_end_only_documented_year_becomes_caveat(self):
        # Regression for the "mis-scoped ledger waives an unrelated failure"
        # failure mode: two FAILing years, only one documented -> only that one
        # becomes a CAVEAT, the other stays a FAIL. Scoped to C3c since v3.1
        # (the only ledgerable criterion); the cross-CRITERION half of the same
        # protection is now structural — see LedgerTests.
        def tail_fail(year):
            return {
                "criterion": "price_tail",
                "key": None,
                "year": year,
                "status": cv.FAIL,
                "classification": cv.MODEL_MISS,
            }

        documented, undocumented = tail_fail(2024), tail_fail(2025)
        exceptions = [{"criterion": "price_tail", "year": 2024, "reason": "x"}]
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


class C3cStandingRuleTest(unittest.TestCase):
    """The C3c standing rule (rubric v3.2, owner amendment 2026-08-09).

    A LONE C3c failure with governance passing auto-ledgers to a CAVEAT in
    ANY year -- training, validation or locked test alike. These tests drive
    ``_apply_c3c_standing_rule`` directly on synthetic record sets, because the
    behaviour under test is the reclassification predicate itself, not the
    scoring that produces the records.
    """

    @staticmethod
    def _rec(criterion, year, status):
        return {"criterion": criterion, "year": year, "status": status}

    @staticmethod
    def _gov(status="PASS"):
        return {"criterion": "governance", "status": status}

    def _apply(self, records, gov_status="PASS"):
        cv._apply_c3c_standing_rule(records, self._gov(gov_status))
        return records

    def test_fires_on_a_training_year(self):
        """v3.2's widening: 2023-2025 are no longer excluded."""
        recs = self._apply([self._rec("price_tail", 2024, cv.FAIL)])
        self.assertEqual(recs[0]["status"], cv.CAVEAT)
        self.assertEqual(recs[0]["classification"], cv.MODEL_LIMIT)
        self.assertEqual(recs[0]["standing_rule"], "c3c-any-year-2026-08-09")

    def test_fires_on_every_tier_including_locked(self):
        for year in (2019, 2022, 2023, 2026):
            with self.subTest(year=year):
                recs = self._apply([self._rec("price_tail", year, cv.FAIL)])
                self.assertEqual(recs[0]["status"], cv.CAVEAT, f"year {year}")

    def test_a_second_failing_criterion_keeps_the_rule_silent(self):
        """The real guard: it can never mask a second defect."""
        recs = self._apply(
            [
                self._rec("price_tail", 2024, cv.FAIL),
                self._rec("price_mean", 2024, cv.FAIL),
            ]
        )
        self.assertEqual([r["status"] for r in recs], [cv.FAIL, cv.FAIL])

    def test_failing_governance_blocks_it(self):
        for gov in ("FAIL", "UNATTESTED"):
            with self.subTest(gov=gov):
                recs = self._apply([self._rec("price_tail", 2024, cv.FAIL)], gov)
                self.assertEqual(recs[0]["status"], cv.FAIL)

    def test_reported_only_co2_fail_does_not_silence_it(self):
        """v3.2(b): the defect that was suppressing the rule as declared.

        C5a ``co2`` was demoted to REPORTED-ONLY at v2.9 -- it is not in
        ``CRITERIA``, contributes no status, no caveat budget and no reason
        line. A ``co2`` FAIL record must therefore not count toward "lone".
        Measured live on 2026-08-09: NYISO ``2026-08-06-nyiso-130-control``
        failed C3c and nothing else, yet an unrelated ``('co2', 2025)`` FAIL
        kept the rule silent.
        """
        self.assertNotIn("co2", cv.CRITERIA, "co2 is reported-only since v2.9")
        recs = self._apply(
            [
                self._rec("price_tail", 2023, cv.FAIL),
                self._rec("co2", 2025, cv.FAIL),
            ]
        )
        self.assertEqual(recs[0]["status"], cv.CAVEAT)
        self.assertEqual(recs[1]["status"], cv.FAIL, "co2 itself is untouched")

    def test_nothing_failing_is_a_no_op(self):
        recs = self._apply([self._rec("price_tail", 2024, cv.PASS)])
        self.assertEqual(recs[0]["status"], cv.PASS)
        self.assertNotIn("standing_rule", recs[0])

    def test_it_is_never_a_pass_and_carries_its_reason(self):
        recs = self._apply([self._rec("price_tail", 2025, cv.FAIL)])
        self.assertNotEqual(recs[0]["status"], cv.PASS)
        self.assertIn("NOT A PASS", recs[0]["ledger_reason"])
        self.assertIn("any holdout or training year", recs[0]["ledger_reason"])

    def test_model_class_stays_supporting_tier_only(self):
        """The rule classifies MODEL_LIMIT; that kind is supporting-tier-only.

        Pins the fail-closed guard the rule depends on: were C3c ever promoted
        out of SUPPORTING, `_apply_ledger` would refuse a model-class entry for
        it, and this rule must not be the thing that quietly widens it.
        """
        self.assertEqual(cv.CRITERIA["price_tail"][1], cv.TIER_SUPPORT)


class LedgeredC3cDoesNotDowngradeTests(unittest.TestCase):
    """RUBRIC v3.3 (owner amendment 2026-08-17).

    A LEDGERED caveat no longer downgrades the overall determination. Since
    v3.1 ledgering is restricted to C3c alone, so these tests pin exactly the
    owner's rule -- an accepted, ledgered C3c price-tail limitation is REPORTED
    but is not the thing that turns CALIBRATED into CALIBRATED-WITH-CAVEATS --
    together with the four things it deliberately does NOT change: C3c never
    reads PASS, it stays visible in every reported channel, every OTHER caveat
    route still downgrades, and a non-lone C3c failure is still NOT-YET.
    """

    def _art(self, *, exceptions=None, model_tail=25, share=0.05):
        """Clean PJM-2024 artifacts whose ONLY blemish is an out-of-band C3c.

        ``model_tail`` 25 vs the injected RT actual of 100 is 0.25x -- outside
        the [0.5x, 2x] band, so C3c is an unambiguous miss. The legitimacy
        artifact is present so C8 is SCORED (an unscored protective criterion
        would downgrade by its own route and mask what these tests measure).
        """
        d = DeterminationTests()
        ypay = d._clean_year_payload()
        ypay["ordc"] = {"hoursGt200": {"actual": 100, "model": model_tail}}
        art = _artifacts(
            ypay,
            attestation=_clean_attestation(exceptions=exceptions),
            **d._clean_bench_args(),
        )
        art["legitimacy"] = _legit_artifact(year=2024, share=share)
        return art

    _LEDGER = [{"criterion": "price_tail", "year": 2024, "reason": "documented"}]

    def setUp(self):
        _tail({"PJM": {"2024": {"da_gt": 80, "rt_gt": 100, "rt_coverage": 1.0}}})
        self.addCleanup(_reset_tail)

    def test_explicitly_ledgered_c3c_reads_calibrated(self):
        v = cv.determine_from_artifacts("t", self._art(exceptions=self._LEDGER))
        self.assertEqual(v["determination"], cv.CALIBRATED)
        self.assertEqual(v["criteria"]["price_tail"]["status"], cv.CAVEAT)
        self.assertEqual(v["criteria"]["price_tail"]["caveat_kind"], "ledgered")

    def test_standing_rule_c3c_reads_calibrated(self):
        # No exceptions entry at all: `_apply_c3c_standing_rule` auto-ledgers
        # the lone C3c failure, and v3.3 then leaves the determination clean.
        v = cv.determine_from_artifacts("t", self._art())
        self.assertEqual(v["determination"], cv.CALIBRATED)
        rec = v["criteria"]["price_tail"]["records"][0]
        self.assertEqual(rec["classification"], cv.MODEL_LIMIT)
        self.assertEqual(rec["standing_rule"], "c3c-any-year-2026-08-09")

    def test_the_miss_stays_visible_on_a_calibrated_run(self):
        """v3.3 changes what the caveat COSTS, never whether it is reported."""
        v = cv.determine_from_artifacts("t", self._art(exceptions=self._LEDGER))
        self.assertEqual(v["determination"], cv.CALIBRATED)
        # Listed as a ledgered caveat, counted in the grade summary, and named
        # on the determination basis -- silence in any of these channels is
        # what would make the amendment an escape hatch.
        self.assertEqual(v["caveats"]["ledgered"], [cv.CRITERIA["price_tail"][0]])
        self.assertEqual(v["grade_summary"]["ledgered"], 1)
        self.assertTrue(any("ledgered caveat" in r for r in v["reasons"]), v["reasons"])
        # And it is NOT absorbed into the clean-pass count: 8 scored, 7 at
        # target grade, C3c the one that is not.
        self.assertEqual(v["grade_summary"]["scored"], 8)
        self.assertEqual(v["grade_summary"]["target_grade"], 7)
        self.assertEqual(v["grade_summary"]["fails"], 0)

    def test_a_clean_tail_needs_no_caveat_at_all(self):
        # Control: the same fixture with an in-band tail is CALIBRATED with an
        # EMPTY ledger, so the tests above are measuring the amendment and not
        # some other property of the fixture.
        v = cv.determine_from_artifacts("t", self._art(model_tail=100))
        self.assertEqual(v["determination"], cv.CALIBRATED)
        self.assertEqual(v["criteria"]["price_tail"]["status"], cv.PASS)
        self.assertEqual(v["caveats"]["ledgered"], [])
        self.assertEqual(v["reasons"], [])

    def test_other_caveat_routes_still_downgrade(self):
        # v3.3 exempts the LEDGERED route only. Drop the legitimacy artifact so
        # C8 is unscored: the protective skip downgrades on its own, exactly as
        # before, even though the ledgered C3c no longer does.
        art = self._art(exceptions=self._LEDGER)
        del art["legitimacy"]
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)
        self.assertTrue(
            any("unscored PROTECTIVE criteria" in r for r in v["reasons"]),
            v["reasons"],
        )

    def test_c3c_alongside_a_second_failure_is_still_not_yet(self):
        # The lone-failure guard is what keeps v3.3 honest: with C1 also
        # failing, the standing rule stays silent, C3c stands as a FAIL too,
        # and the run is NOT-YET.
        art = self._art()
        art["payload"]["years"]["2024"]["gmModel"]["CC_REGULAR"] = 360.0
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertEqual(v["criteria"]["price_tail"]["status"], cv.FAIL)
        self.assertEqual(v["criteria"]["fuelmix"]["status"], cv.FAIL)

    def test_ledgered_budget_still_bounds_the_undowngraded_route(self):
        # v3.3 does not touch the budgets -- they are checked BEFORE it -- and
        # the ledgered budget is now the sole numeric bound on what can be
        # carried without a downgrade, so pin it at exactly one slot.
        self.assertEqual(cv.MAX_LEDGERED_CAVEATS, 1)
        self.assertEqual(cv.MAX_PROTECTIVE_CAVEATS, 0)
        self.assertEqual(cv.LEDGERABLE_CRITERIA, frozenset({"price_tail"}))
