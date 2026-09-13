"""Tests for the PRICE-UNSCORED determination class (scripts/calibration_verdict.py).

NWPP-22 (owner ruling, NWPP card N2 limb (b), 2026-09-13): a run whose ISO has
NO admissible hourly price series reads a determination naming its own basis,
never a bare CALIBRATED. These tests pin the predicate and every guard on
SYNTHETIC artifacts — no registry, no committed bundle, no LP — with the
committed price-reference store injected through ``cv._ACTUAL_LMP_CACHE``
exactly as the tail part is injected through ``cv._TAIL_CACHE``.

The two load-bearing pins the lane charter names:

* the class CANNOT fire for an ISO carrying a price series, and the payload of
  such a run is byte-identical to the pre-change route;
* the class DOES fire for an ISO carrying none, with the exact string, the
  basis line first, the price criteria still SKIPPED (never PASS) and excluded
  from ``grade_summary``.
"""

import importlib.util
import json
import unittest

from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "calibration_verdict", str(REPO_ROOT / "scripts" / "calibration_verdict.py")
)
cv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cv)

# A store naming exactly the seven ISOs registered at the lane's base pin. The
# synthetic "priceless" ISO below is deliberately NOT one of them and is not
# NWPP either: the predicate is data-driven, so any key absent from the store
# behaves identically.
_STORE_WITH_SERIES = {
    iso: {"2024": {"rt": 29.0, "da": 30.0}}
    for iso in ("ERCOT", "PJM", "CAISO", "NYISO", "NEISO", "MISO", "SPP")
}
_PRICELESS_ISO = "SYNTHETIC_NOPRICE"


def _clean_attestation():
    return {
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
        },
        "exceptions": [],
    }


def _year_payload(cc_model=326.0):
    # Every fossil class inside the universal C1 gate; a full mix so the
    # volume band scales sensibly; hourly fits above the C4 floors; a model
    # price present (the model DID price — only the actual is absent).
    return {
        "gmModel": {
            "CC_REGULAR": cc_model,
            "CT_PEAKER": 20.0,
            "ST_GAS": 9.0,
            "COAL_BIT": 55.0,
        },
        "nonfossil": {"nuclear": 270.0, "wind": 28.0, "solar": 14.0},
        "fuelRows": [
            {"fuel": "gas", "m": 355, "b": 354, "r": 0.8, "nrmse": 0.15},
            {"fuel": "coal", "m": 55, "b": 55, "r": 0.9, "nrmse": 0.15},
        ],
        "lmp": {"Z": {"p": 29.0, "d": 100.0, "pMon": [29] * 12, "dMon": [8.3] * 12}},
    }


def _bench(avg_lmp):
    b = {
        "classFull": {
            "CC_REGULAR": 325.0,
            "CT_PEAKER": 20.0,
            "ST_GAS": 9.0,
            "COAL_BIT": 55.0,
        },
        "e930": {
            "gas": 354.0,
            "coal": 55.0,
            "nuclear": 270.0,
            "wind": 28.0,
            "solar": 14.0,
        },
    }
    if avg_lmp is not None:
        b["avgLMP"] = avg_lmp
    return b


def _legitimacy(years):
    """Minimal legitimacy_diagnostics.json (schema v1) so C8 SCORES a clean PASS.

    Without it C8 SKIPs as an unscored PROTECTIVE criterion and downgrades the
    physical rung on its own — the fail-closed guard working, not the thing
    under test. CT_PEAKER at 5 % forced share is under the 15 % peaker cap.
    """
    return {
        "schema": "legitimacy-diagnostics/v1",
        "iso": "PJM",
        "years": list(years),
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
                        "year": y,
                        "class": "CT_PEAKER",
                        "profile_r": 0.9,
                        "model_offpeak_cv": 0.2,
                        "actual_offpeak_cv": 0.2,
                        "cv_ratio": 1.0,
                        "gated": True,
                        "verdict": "pass",
                    }
                    for y in years
                ]
            },
            "D2": {
                "summary": [
                    {
                        "year": y,
                        "class": "CT_PEAKER",
                        "forced_twh": 1.0,
                        "class_total_twh": 20.0,
                        "forced_share": 0.05,
                        "limit": 0.10,
                        "lower_bound": False,
                        "verdict": "pass",
                    }
                    for y in years
                ],
            },
        },
    }


def _artifacts(iso, *, avg_lmp, years=(2024,), cc_model=326.0, attestation="clean"):
    return {
        "sidecar": {"id": "t", "iso": iso, "label": "test", "years": list(years)},
        "payload": {"years": {str(y): _year_payload(cc_model) for y in years}},
        "bench": {y: _bench(avg_lmp) for y in years},
        "config": {"scenario_config": {"outage_source": "historic"}, "meta": {}},
        "attestation": _clean_attestation() if attestation == "clean" else attestation,
        "legitimacy": _legitimacy(years),
    }


class PriceUnscoredClassTests(unittest.TestCase):
    def setUp(self):
        cv._ACTUAL_LMP_CACHE = dict(_STORE_WITH_SERIES)
        cv._TAIL_CACHE = {}  # no tail part for anyone: C3c SKIPs everywhere

    def tearDown(self):
        cv._ACTUAL_LMP_CACHE = None
        cv._TAIL_CACHE = None

    # -- the two charter pins --------------------------------------------------
    def test_cannot_fire_for_an_iso_carrying_a_series(self):
        # PJM is in the store AND its bench carries an LMP actual: the price
        # criteria SCORE, and the run reads exactly what it read before the
        # class existed. The predicate is also asserted False directly.
        art = _artifacts("PJM", avg_lmp={"rt": 29.0, "rt_mon": [29] * 12})
        v = cv.determine_from_artifacts("t", art)
        self.assertNotIn("price_unscored", v)
        self.assertEqual(v["criteria"]["price_mean"]["status"], cv.PASS)
        self.assertEqual(v["criteria"]["price_shape"]["status"], cv.PASS)
        self.assertNotIn("PRICE UNSCORED", " ".join(v["reasons"]))
        self.assertIn(v["determination"], (cv.CALIBRATED, cv.CALIBRATED_CAVEATS))
        self.assertFalse(
            cv._price_series_absent(
                "PJM",
                v["scorable_years"],
                v["price_reference_blocked_years"],
                v["criteria"],
            )
        )

    def test_fires_for_an_iso_carrying_none(self):
        # Not in the store, no bench LMP actual, no tail part: every price
        # criterion is SKIPPED and the run reads the basis-naming class.
        art = _artifacts(_PRICELESS_ISO, avg_lmp=None)
        v = cv.determine_from_artifacts("t", art)
        # Every physical criterion (C1/C2/C4/C6/C8) scores PASS; the three
        # price criteria are the ONLY skips -> the physical rung is CALIBRATED.
        self.assertEqual(
            sorted(c for c, b in v["criteria"].items() if b["status"] == cv.SKIPPED),
            sorted(cv.PRICE_UNSCORED_CRITERIA),
            "fixture must isolate the price criteria as the only unscored ones",
        )
        self.assertEqual(v["determination"], cv.PHYSICALLY_CALIBRATED_PRICE_UNSCORED)
        self.assertEqual(
            v["determination"],
            "PHYSICALLY CALIBRATED — PRICE UNSCORED (no admissible hourly price series)",
        )
        # The basis line is FIRST so headline() leads with it.
        self.assertTrue(v["reasons"][0].startswith("PRICE UNSCORED — "))
        self.assertIn(_PRICELESS_ISO, v["reasons"][0])
        self.assertIn(cv.PRICE_UNSCORED_REFERENCE, v["reasons"][0])
        self.assertIn("NEVER a CALIBRATED reading", v["reasons"][0])
        self.assertTrue(
            cv.headline(v).startswith(f"DETERMINATION: {v['determination']}")
        )
        # Never a PASS: the price criteria keep SKIPPED and are not counted.
        for cid in cv.PRICE_UNSCORED_CRITERIA:
            self.assertEqual(v["criteria"][cid]["status"], cv.SKIPPED, cid)
        self.assertEqual(
            v["grade_summary"]["target_grade"], v["grade_summary"]["scored"]
        )
        self.assertNotIn(
            "price_mean",
            [c for c in v["criteria"] if v["criteria"][c]["status"] == cv.PASS],
        )
        # The structural block travels with the verdict and the sidecar.
        self.assertEqual(
            v["price_unscored"],
            {
                "iso": _PRICELESS_ISO,
                "reference": cv.PRICE_UNSCORED_REFERENCE,
                "years": [2024],
                "criteria": list(cv.PRICE_UNSCORED_CRITERIA),
                "physical_rung": cv.CALIBRATED,
            },
        )
        self.assertEqual(cv.condensed_metrics(v)["price_unscored"], v["price_unscored"])
        self.assertIn("PRICE UNSCORED", cv.render_text(v))
        self.assertEqual(v["price_reference_blocked_years"], [2024])

    # -- fail-closed legs of the predicate --------------------------------------
    def test_silent_when_the_store_is_unreadable(self):
        # An unreadable/empty store is what the loader produces on OSError or
        # bad JSON. Absence cannot be established -> the pre-existing unscored
        # route stands (CALIBRATED-WITH-CAVEATS on "unscored criteria").
        cv._ACTUAL_LMP_CACHE = {}
        art = _artifacts(_PRICELESS_ISO, avg_lmp=None)
        v = cv.determine_from_artifacts("t", art)
        self.assertNotIn("price_unscored", v)
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)
        self.assertTrue(any(r.startswith("unscored criteria: ") for r in v["reasons"]))

    def test_silent_for_a_stored_iso_whose_run_years_lack_a_bench(self):
        # The MISO-2020-alone shape: the ISO HAS a series (store record) but
        # this run's year carries no bench LMP actual. Per-year absence in an
        # ISO with a series is the coverage machinery's business, never this
        # class's -> unchanged CALIBRATED-WITH-CAVEATS route.
        art = _artifacts("MISO", avg_lmp=None, years=(2020,))
        v = cv.determine_from_artifacts("t", art)
        self.assertNotIn("price_unscored", v)
        self.assertEqual(v["determination"], cv.CALIBRATED_CAVEATS)
        self.assertEqual(v["price_reference_blocked_years"], [2020])
        self.assertTrue(any(r.startswith("unscored criteria: ") for r in v["reasons"]))

    def test_silent_when_a_scored_year_carries_a_bench_actual(self):
        # Inconsistent artifacts: the store does not name the ISO but a bench
        # part carries a price. The criteria score as they always did and the
        # class stays silent.
        art = _artifacts(_PRICELESS_ISO, avg_lmp={"rt": 29.0, "rt_mon": [29] * 12})
        v = cv.determine_from_artifacts("t", art)
        self.assertNotIn("price_unscored", v)
        self.assertEqual(v["criteria"]["price_mean"]["status"], cv.PASS)

    # -- ordering guards: every downgrading rung stays ahead of the class ------
    def test_governance_failure_still_not_yet(self):
        art = _artifacts(_PRICELESS_ISO, avg_lmp=None, attestation=None)
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertNotIn("price_unscored", v)

    def test_physical_fail_still_not_yet(self):
        # CC_REGULAR +10.8% on a big class fails C1: NOT-YET, class silent.
        art = _artifacts(_PRICELESS_ISO, avg_lmp=None, cc_model=360.0)
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(v["determination"], cv.NOT_YET)
        self.assertNotIn("price_unscored", v)

    def test_physical_caveats_carry_into_the_caveats_string(self):
        # An unscored PHYSICAL criterion (C4 with no fuelRows) still downgrades
        # the physical rung; the label carries that rung, so the price half's
        # absence can never shed a physical caveat.
        art = _artifacts(_PRICELESS_ISO, avg_lmp=None)
        art["payload"]["years"]["2024"].pop("fuelRows")
        v = cv.determine_from_artifacts("t", art)
        self.assertEqual(
            v["determination"], cv.PHYSICALLY_CALIBRATED_CAVEATS_PRICE_UNSCORED
        )
        self.assertEqual(v["price_unscored"]["physical_rung"], cv.CALIBRATED_CAVEATS)
        self.assertTrue(v["reasons"][0].startswith("PRICE UNSCORED — "))
        self.assertIn("unscored criteria: dispatch_corr", v["reasons"])

    # -- the class is never CALIBRATED, structurally --------------------------
    def test_strings_are_never_calibrated(self):
        for s in (
            cv.PHYSICALLY_CALIBRATED_PRICE_UNSCORED,
            cv.PHYSICALLY_CALIBRATED_CAVEATS_PRICE_UNSCORED,
        ):
            self.assertNotEqual(s, cv.CALIBRATED)
            self.assertNotEqual(s, cv.CALIBRATED_CAVEATS)
            self.assertFalse(s.startswith(cv.CALIBRATED))
            self.assertIn("PRICE UNSCORED", s)
        self.assertEqual(
            set(cv.PRICE_UNSCORED_BY_RUNG), {cv.CALIBRATED, cv.CALIBRATED_CAVEATS}
        )
        self.assertEqual(
            cv.PRICE_UNSCORED_CRITERIA, ("price_mean", "price_shape", "price_tail")
        )
        self.assertEqual(
            str(cv._ACTUAL_LMP_PATH.relative_to(REPO_ROOT)), cv.PRICE_UNSCORED_REFERENCE
        )

    def test_series_iso_payload_is_byte_identical_with_and_without_the_class(self):
        # The lift inside the else-branch reduces to the pre-change list when
        # the predicate is False: scoring a series-carrying ISO with the store
        # present and with the store emptied (which disables the class) yields
        # the same bytes.
        art = _artifacts("PJM", avg_lmp={"rt": 29.0, "rt_mon": [29] * 12})
        with_store = json.dumps(cv.determine_from_artifacts("t", art), sort_keys=True)
        cv._ACTUAL_LMP_CACHE = {}
        without = json.dumps(cv.determine_from_artifacts("t", art), sort_keys=True)
        self.assertEqual(with_store, without)


if __name__ == "__main__":
    unittest.main()
