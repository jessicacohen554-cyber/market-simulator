"""FF-3G T2/T3 determination scorer shakeout (scripts/forecast_verdict.py).

The ``--tier t2`` path had never been exercised on any bundle before FF-3G
(FF-2D scored only t1f/t1x/t1h). These tests pin its behaviour on a SYNTHETIC t2
summary — NO LP solve, no committed-artifact files — covering the t2-only FC-2
rows (row2 terminal drift, row6 scarcity gate), the clean SKIPPED degradation of
the §2.1b-gated instruments (FC-3/FC-4/FC-5/FC-6, FC-2 row5 position), the
upstream delivery of the rubric §3 I12 stability escalation, and the t3
UNATTESTED path. See docs/handoffs/ff-t2-scorer-shakeout-2026-07.md.

This lives in a sibling file (not appended to tests/test_forecast_verdict.py) so
the 866-line base test file is not rewritten wholesale over the push API
(CLAUDE.md rule 27 — never regenerate a ≥300-line source file). The base module
is loaded by path and its fixture builders are reused verbatim, so every
threshold asserted here is still READ from the scorer's pre-registered constants,
never re-derived (rubric §4).
"""

import importlib.util
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
# Reuse the base test module's fv loader + fixture builders (loaded by path, the
# same way it loads the scorer — no package-import assumptions). This does NOT
# collect the base module's tests (unittest discovers those under their own
# dotted name); it only borrows the helpers.
_spec = importlib.util.spec_from_file_location(
    "_forecast_verdict_base", str(_REPO / "tests" / "test_forecast_verdict.py")
)
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)

fv = _base.fv
_art = _base._art
_summary = _base._summary
_traj = _base._traj
_invariants = _base._invariants
_run_config = _base._run_config
_dof = _base._dof
_hindcast = _base._hindcast
_crossover = _base._crossover
_battery = _base._battery
_corridor = _base._corridor
_attestation = _base._attestation
_status = _base._status


# ---------------------------------------------------------------------------
# Synthetic T2 fixtures (built the way FF-3G's shakeout builds one from a T1
# bundle: a 2026-2030 trajectory extended to 2035). Fixture data, not a forecast.
# ---------------------------------------------------------------------------
def _t2_summary(iso="ERCOT", invariants=None, reserve_margin=0.15, scarcity=25, **over):
    """A synthetic T2 (2026-2035) full_horizon_summary.

    Ten trajectory years to 2035 so the t2-only FC-2 rows have a final year
    (row2 terminal drift) and a multi-year window (row6 scarcity). No band here
    is fit to any run (rubric §4 — the scorer's constants own the thresholds).
    """
    return _summary(
        iso,
        invariants=_invariants(key="id") if invariants is None else invariants,
        trajectory=_traj(
            iso,
            years=range(2026, 2036),
            reserve_margin=reserve_margin,
            scarcity=scarcity,
        ),
        start_year=2026,
        end_year=2035,
        **over,
    )


def _t2_all_instruments(**over):
    """A T2 bundle with every required instrument present and green (=> PROMOTE)."""
    base = _art(
        summary=_t2_summary(),
        run_config=_run_config(),
        dof_ledger=_dof(),
        hindcast=_hindcast(),  # FC-3 all bands PASS + baselines
        crossover=_crossover(
            metrics=[
                {"metric": "price", "year": 2024, "forecast_abs_err_frac": 0.05},
                {"metric": "co2", "year": 2024, "forecast_abs_err_frac": 0.05},
            ]
        ),  # FC-4 clean + refusal marker
        corridor=_corridor(
            rows=[
                {"quantity": "gas_cap", "target_year": 2030, "verdict": "IN CORRIDOR"}
            ]
        ),  # FC-5 in corridor
        driver_battery=_battery(),  # FC-6 gate PASS
    )
    base.update(over)
    return base


class T2ShakeoutTests(unittest.TestCase):
    def test_instruments_absent_degrade_to_skipped_and_hold(self):
        # The realistic §2.1b-deferred state: summary + run_config + dof only, with
        # no committed hindcast/crossover/corridor/battery. Each absent instrument
        # must SKIP cleanly (never FAIL, never crash) and required-SKIPPED => HOLD.
        art = _art(summary=_t2_summary(), run_config=_run_config(), dof_ledger=_dof())
        v = fv.determine_from_artifacts(art, "t2")
        for cid in ("FC-3", "FC-4", "FC-5", "FC-6"):
            self.assertEqual(v["categories"][cid]["status"], fv.SKIPPED, cid)
        self.assertEqual(v["determination"], fv.HOLD)
        for cid in ("FC-1", "FC-2", "FC-7"):  # the scorable-from-summary categories
            self.assertNotEqual(v["categories"][cid]["status"], fv.FAIL, cid)

    def test_every_category_resolves_to_a_valid_token(self):
        # No category may crash or emit an unknown token, and render/sidecar must
        # not crash — at either extreme (bare bundle and fully-wired bundle).
        valid = {fv.PASS, fv.CAVEAT, fv.FAIL, fv.SKIPPED, fv.UNATTESTED, fv.NA}
        for art in (
            _art(summary=_t2_summary(), run_config=_run_config(), dof_ledger=_dof()),
            _t2_all_instruments(),
        ):
            v = fv.determine_from_artifacts(art, "t2")
            fv.render_text(v)
            fv.condensed_sidecar(v)
            for cid in fv.CATEGORY_ORDER:
                self.assertIn(v["categories"][cid]["status"], valid, cid)

    def test_fully_wired_promotes(self):
        v = fv.determine_from_artifacts(_t2_all_instruments(), "t2")
        self.assertEqual(v["determination"], fv.PROMOTE)

    def test_terminal_drift_row_emitted_and_scores_at_t2(self):
        # Row 2 is t2/t3-only; final-year (2035) RM 0.15 sits inside the ERCOT band
        # [floor-10pp, floor+25pp] = [0.0375, 0.3875].
        art = _art(summary=_t2_summary(), run_config=_run_config(), dof_ledger=_dof())
        rows = {r["row"]: r for r in fv.score_fc2(art, "t2", "ERCOT")}
        self.assertIn("row2", rows)
        self.assertEqual(rows["row2"]["status"], fv.PASS)
        self.assertEqual(rows["row2"]["values"]["year"], 2035)

    def test_scarcity_gates_at_t2(self):
        # ERCOT scarcity is report-only at t1f but a gating row at t2; mean 25 h/yr
        # sits in [SCARCITY_MEAN_LO, SCARCITY_MEAN_HI].
        art = _art(
            summary=_t2_summary(scarcity=25),
            run_config=_run_config(),
            dof_ledger=_dof(),
        )
        r6 = {r["row"]: r for r in fv.score_fc2(art, "t2", "ERCOT")}["row6"]
        self.assertTrue(r6["gating"])
        self.assertEqual(r6["status"], fv.PASS)

    def test_i12_fail_escalates_fc2_row1_to_fail_at_t2(self):
        # The rubric §3 t2/t3 stability escalation ("I12 breach trend fails FC-2.1")
        # is delivered UPSTREAM: a >=3-consecutive-year breach is I12 FAIL (the
        # producer's reserve_margin_consecutive_fail), which row 1 maps to FAIL. So a
        # genuine 2031-2035 chain never reaches the scorer as a stray WARN.
        art = _art(
            summary=_t2_summary(invariants=_invariants({"I12": "FAIL"}, key="id")),
            run_config=_run_config(),
            dof_ledger=_dof(),
        )
        r1 = {r["row"]: r for r in fv.score_fc2(art, "t2", "ERCOT")}["row1"]
        self.assertEqual(r1["status"], fv.FAIL)

    def test_i12_warn_is_caveat_not_fail_at_t2(self):
        # A sub-3-year excursion is I12 WARN => row CAVEAT (surfaced, never a silent
        # PASS and never an over-strict FAIL).
        art = _art(
            summary=_t2_summary(invariants=_invariants({"I12": "WARN"}, key="id")),
            run_config=_run_config(),
            dof_ledger=_dof(),
        )
        r1 = {r["row"]: r for r in fv.score_fc2(art, "t2", "ERCOT")}["row1"]
        self.assertEqual(r1["status"], fv.CAVEAT)

    def test_i12_stability_mirror_matches_producer_threshold(self):
        # The scorer's mirror constant must equal the I12 producer's own
        # consecutive-fail threshold (the coupling I12_WARN_CHAIN_FAIL documents).
        # Skips when the model stack (numpy/market_sim) is absent — the scorer's
        # tests never require it (module docstring).
        try:
            spec = importlib.util.spec_from_file_location(
                "cfi", str(_REPO / "scripts" / "check_forecast_invariants.py")
            )
            cfi = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cfi)
        except Exception as e:  # numpy / market_sim not installed
            self.skipTest(f"model stack unavailable: {e}")
        self.assertEqual(
            fv.I12_WARN_CHAIN_FAIL, cfi.Thresholds().reserve_margin_consecutive_fail
        )
        self.assertEqual(fv.STABILITY_WINDOW, (2031, 2035))

    def test_raw_crossover_shape_trips_quarantine_gate(self):
        # The committed FF-0E emitter nests refusal_marker under `meta`; the scorer
        # reads it top-level (bridged by scripts/_ff2d_crossover_adapter.py). Feeding
        # the RAW shape trips the rule-22 "marker ABSENT => FAIL" gate. Pinned so a
        # future fold-in of the marker into score_crossover.py is a conscious change,
        # not a silent verdict flip (FF-2D §4.2 routes that follow-up to L-VAL).
        raw = {
            "iso": "ERCOT",
            "meta": {
                "refusal_marker": {"read_ge_2026": False, "scored_max_year": 2025}
            },
            "dispatch_skill": {"price_mean_forecast_err_frac": {"2024": 0.05}},
        }
        rows = fv.score_fc4(_art(crossover=raw), "t2", "ERCOT")
        self.assertEqual(_status(rows), fv.FAIL)
        self.assertIn("quarantine", rows[0]["row"])

    def test_t3_attestation_absent_is_unattested_hold(self):
        # t3 reuses the whole t2 instrument set + the §5 attestation. All t2
        # instruments present and green, but no attestation => FC-7 UNATTESTED => HOLD.
        v = fv.determine_from_artifacts(_t2_all_instruments(), "t3")
        att = {r["row"]: r for r in v["categories"]["FC-7"]["rows"]}
        self.assertEqual(att["attestation"]["status"], fv.UNATTESTED)
        self.assertEqual(v["determination"], fv.HOLD)

    def test_t3_full_bundle_with_attestation_promotes(self):
        v = fv.determine_from_artifacts(
            _t2_all_instruments(attestation=_attestation()), "t3"
        )
        self.assertEqual(v["categories"]["FC-7"]["status"], fv.PASS)
        self.assertEqual(v["determination"], fv.PROMOTE)


if __name__ == "__main__":
    unittest.main()
