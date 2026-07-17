"""Tests for the forecast determination scorer (scripts/forecast_verdict.py).

The per-category scorers and the tier/determination logic are exercised on
synthetic artifacts — no LP solve, no committed-artifact files — so the rubric's
PASS/CAVEAT/FAIL/SKIPPED semantics and the T0->T3 promotion logic are pinned
independently of any particular forecast run. Every threshold asserted here is
READ from the scorer's pre-registered module constants (which transcribe
``docs/forecast-determination-rubric.md`` §2), never re-derived and never fit to
a real run's numbers (rubric §4 — bands never widen). The scorer is loaded by
path (it lives under scripts/, not an importable package), mirroring
tests/test_calibration_verdict.py.
"""

import importlib.util
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "forecast_verdict", str(_REPO / "scripts" / "forecast_verdict.py")
)
fv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fv)


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------
def _invariants(overrides=None, ids=range(1, 15), key="ident"):
    """14 clean single-run invariants; ``overrides`` maps id->status.

    ``key`` toggles the identifier field so both the standalone
    (``ident``) and summary-embedded (``id``) shapes are exercised.
    """
    over = overrides or {}
    return [
        {
            key: f"I{i}",
            "name": f"inv {i}",
            "status": over.get(f"I{i}", "PASS"),
            "detail": f"I{i} detail",
        }
        for i in ids
    ]


def _traj(
    iso="ERCOT", years=range(2026, 2031), reserve_margin=0.15, scarcity=30, **extra
):
    """A per-year trajectory with clean adequacy signals."""
    rows = []
    for y in years:
        row = {
            "year": y,
            "reserve_margin": reserve_margin,
            "hours_ge_500": scarcity,
            "builds_thermal_mw": 100.0,
            "builds_renew_mw": 500.0,
            "builds_storage_mw": 50.0,
            "retire_mw": 0.0,
        }
        row.update(extra)
        rows.append(row)
    return rows


def _summary(
    iso="ERCOT", invariants=None, trajectory=None, wall=600.0, rss=3600.0, **over
):
    s = {
        "iso": iso,
        "start_year": 2026,
        "end_year": 2030,
        "capacity_market_clearing": over.pop("capacity_market_clearing", False),
        "total_wall_s": wall,
        "global_peak_rss_mb": rss,
        "invariants": _invariants(key="id") if invariants is None else invariants,
        "trajectory": _traj(iso) if trajectory is None else trajectory,
    }
    s.update(over)
    return s


def _run_config(iso="ERCOT", mode="forecast", **sc_over):
    sc = {
        "iso": iso,
        "mode": mode,
        "outage_source": "statistical",
        "capacity_market_clearing": False,
        "reserve_margin_build_enabled": None,
    }
    sc.update(sc_over)
    return {"cache_key": "x", "git_sha": "abc", "scenario_config": sc}


def _dof(entries=None):
    return {
        "schema": "dof-ledger/v1",
        "entries": entries
        if entries is not None
        else [
            {"name": "offer_curve", "where": "sc.offer", "identification": "published"}
        ],
    }


def _hindcast(bands="PASS", baselines=True, wrapped=True):
    score = {
        "iso": "ERCOT",
        "retirements": {
            "total_gw": {"actual": 5, "model": 5, "err_frac": 0.0, "band": bands},
            "unit_recall_gt300": {"recall": 0.8, "band": bands},
            "false_retire": {"frac_of_model": 0.05, "band": bands},
        },
        "additions": {
            "by_tech": {"wind": {"band": bands}, "solar": {"band": bands}},
            "shares": {"wind": {"band": bands}},
        },
        "co2": {"model": {"2025": 1.0}, "actual": {"2025": 1.0}},
    }
    if baselines:
        score["baselines"] = {
            "announced": {"retire_gw": 4.0, "add_gw": 6.0, "note": "x"}
        }
    return (
        {"run_id": "r", "score": score, "invariants": _invariants()}
        if wrapped
        else score
    )


def _crossover(metrics=None, marker=None):
    return {
        "iso": "ERCOT",
        "refusal_marker": marker
        if marker is not None
        else {"present": True, "scored_max_year": 2025, "read_ge_2026": False},
        "metrics": metrics if metrics is not None else [],
    }


def _battery(expectations=None):
    return {
        "iso": "ERCOT",
        "ladders": [
            {
                "test_id": "T1.1",
                "driver": "carbon",
                "expectations": expectations
                if expectations is not None
                else [{"expr_id": "e1", "gate": True, "status": "PASS", "detail": ""}],
            }
        ],
    }


def _corridor(rows=None, missing=None):
    out = {"iso": "ERCOT", "rows": rows or []}
    if missing:
        out["missing_sources"] = missing
    return out


def _attestation(all_true=True, false_one=None):
    block = {a: True for a in fv.ATTESTATION_ASSERTIONS}
    if not all_true and false_one:
        block[false_one] = False
    return block


def _art(**over):
    """Full artifacts dict with every input absent (None) unless overridden."""
    base = dict(
        summary=None,
        invariants=None,
        paired_invariants=None,
        hindcast=None,
        crossover=None,
        driver_battery=None,
        corridor=None,
        run_config=None,
        dof_ledger=None,
        attestation=None,
        position=None,
    )
    base.update(over)
    return base


def _status(rows):
    return fv._agg_rows(rows)


# ---------------------------------------------------------------------------
# FC-1 structural integrity
# ---------------------------------------------------------------------------
class FC1Tests(unittest.TestCase):
    def test_all_pass(self):
        rows = fv.score_fc1(_art(invariants=_invariants()), "t1f", "ERCOT")
        self.assertEqual(_status(rows), fv.PASS)

    def test_summary_embedded_id_key(self):
        # The summary embeds invariants under the "id" key (not "ident").
        rows = fv.score_fc1(_art(summary=_summary()), "t1f", "ERCOT")
        self.assertEqual(_status(rows), fv.PASS)

    def test_warn_is_caveat(self):
        rows = fv.score_fc1(
            _art(invariants=_invariants({"I13": "WARN"})), "t1f", "ERCOT"
        )
        self.assertEqual(_status(rows), fv.CAVEAT)
        self.assertIn("I13", rows[0]["detail"])

    def test_fail_is_fail(self):
        rows = fv.score_fc1(
            _art(invariants=_invariants({"I1": "FAIL"})), "t1f", "ERCOT"
        )
        self.assertEqual(_status(rows), fv.FAIL)
        self.assertIn("I1", rows[0]["detail"])

    def test_absent_is_skipped(self):
        rows = fv.score_fc1(_art(), "t1f", "ERCOT")
        self.assertEqual(_status(rows), fv.SKIPPED)

    def test_skip_invariant_does_not_gate(self):
        # An individual invariant SKIP (e.g. emissions absent) is noted, not gating.
        rows = fv.score_fc1(
            _art(invariants=_invariants({"I1": "SKIP"})), "t1f", "ERCOT"
        )
        self.assertEqual(_status(rows), fv.PASS)


# ---------------------------------------------------------------------------
# FC-2 adequacy & equilibrium
# ---------------------------------------------------------------------------
class FC2Tests(unittest.TestCase):
    def test_clean_t1f(self):
        art = _art(summary=_summary(), run_config=_run_config())
        self.assertEqual(_status(fv.score_fc2(art, "t1f", "ERCOT")), fv.PASS)

    def test_i12_warn_row_caveat(self):
        art = _art(
            summary=_summary(invariants=_invariants({"I12": "WARN"})),
            run_config=_run_config(),
        )
        self.assertEqual(_status(fv.score_fc2(art, "t1f", "ERCOT")), fv.CAVEAT)

    def test_i12_fail_row_fail(self):
        art = _art(
            summary=_summary(invariants=_invariants({"I12": "FAIL"})),
            run_config=_run_config(),
        )
        self.assertEqual(_status(fv.score_fc2(art, "t1f", "ERCOT")), fv.FAIL)

    def test_i13_warn_makes_row_fail(self):
        # Rubric FC-2.3: any I13 WARN ⇒ row FAIL at every scored tier.
        art = _art(
            summary=_summary(invariants=_invariants({"I13": "WARN"})),
            run_config=_run_config(),
        )
        rows = fv.score_fc2(art, "t1f", "ERCOT")
        cob = [r for r in rows if r["row"] == "row3"][0]
        self.assertEqual(cob["status"], fv.FAIL)

    def test_backstop_off_is_pass(self):
        art = _art(
            summary=_summary(),
            run_config=_run_config(reserve_margin_build_enabled=None),
        )
        r4 = [r for r in fv.score_fc2(art, "t1f", "ERCOT") if r["row"] == "row4"][0]
        self.assertEqual(r4["status"], fv.PASS)
        self.assertEqual(r4["values"]["backstop_share"], 0.0)

    def test_backstop_share_bands(self):
        # Thresholds READ from the module (rubric §2 FC-2.4): <=10% PASS, 10-30% CAVEAT, >30% FAIL.
        over = 0.5 * (
            fv.BACKSTOP_SHARE_PASS + fv.BACKSTOP_SHARE_FAIL
        )  # mid of the caveat band
        cases = {
            fv.BACKSTOP_SHARE_PASS - 0.01: fv.PASS,
            over: fv.CAVEAT,
            fv.BACKSTOP_SHARE_FAIL + 0.05: fv.FAIL,
        }
        rc = _run_config(
            iso="PJM", reserve_margin_build_enabled=True, capacity_market_clearing=True
        )
        for share, want in cases.items():
            traj = _traj(
                "PJM",
                years=[2026],
                builds_thermal_mw=1000.0,
                builds_renew_mw=0.0,
                builds_storage_mw=0.0,
                builds_thermal_backstop_mw=share * 1000.0,
            )
            art = _art(summary=_summary("PJM", trajectory=traj), run_config=rc)
            r4 = [r for r in fv.score_fc2(art, "t1f", "PJM") if r["row"] == "row4"][0]
            self.assertEqual(r4["status"], want, f"share {share}")

    def test_backstop_armed_without_split_is_skipped(self):
        rc = _run_config(
            iso="PJM", reserve_margin_build_enabled=True, capacity_market_clearing=True
        )
        art = _art(summary=_summary("PJM", trajectory=_traj("PJM")), run_config=rc)
        r4 = [r for r in fv.score_fc2(art, "t1f", "PJM") if r["row"] == "row4"][0]
        self.assertEqual(r4["status"], fv.SKIPPED)

    def test_terminal_drift_t2_only(self):
        # Row 2 is emitted at t2/t3, not at t1f (rubric §2 FC-2.2).
        art = _art(summary=_summary(), run_config=_run_config())
        self.assertNotIn("row2", {r["row"] for r in fv.score_fc2(art, "t1f", "ERCOT")})
        self.assertIn("row2", {r["row"] for r in fv.score_fc2(art, "t2", "ERCOT")})

    def test_terminal_drift_band(self):
        # ERCOT floor 0.1375; band [floor-10pp, floor+25pp] = [0.0375, 0.3875].
        floor = fv._planning_floor("ERCOT", _art())
        self.assertIsNotNone(floor)
        good = _traj("ERCOT", years=[2035], reserve_margin=floor + 0.10)
        bad = _traj(
            "ERCOT", years=[2035], reserve_margin=floor + fv.TERMINAL_DRIFT_HI_PP + 0.05
        )
        for traj, want in ((good, fv.PASS), (bad, fv.FAIL)):
            art = _art(
                summary=_summary("ERCOT", trajectory=traj), run_config=_run_config()
            )
            r2 = [r for r in fv.score_fc2(art, "t2", "ERCOT") if r["row"] == "row2"][0]
            self.assertEqual(r2["status"], want)

    def test_ercot_scarcity_report_at_t1_gate_at_t2(self):
        # Zero scarcity: report-only at t1f (non-gating), gates as CAVEAT at t2.
        traj = _traj("ERCOT", scarcity=0)
        art = _art(summary=_summary("ERCOT", trajectory=traj), run_config=_run_config())
        r6_t1 = [r for r in fv.score_fc2(art, "t1f", "ERCOT") if r["row"] == "row6"][0]
        self.assertFalse(r6_t1["gating"])
        r6_t2 = [r for r in fv.score_fc2(art, "t2", "ERCOT") if r["row"] == "row6"][0]
        self.assertTrue(r6_t2["gating"])
        self.assertEqual(r6_t2["status"], fv.CAVEAT)

    def test_ercot_scarcity_sustained_voll_fail(self):
        traj = _traj("ERCOT", years=[2026, 2027], scarcity=30)
        traj[1]["hours_ge_500"] = fv.SCARCITY_YEAR_FAIL + 1
        art = _art(summary=_summary("ERCOT", trajectory=traj), run_config=_run_config())
        r6 = [r for r in fv.score_fc2(art, "t2", "ERCOT") if r["row"] == "row6"][0]
        self.assertEqual(r6["status"], fv.FAIL)

    def test_scarcity_not_applicable_non_ercot(self):
        art = _art(
            summary=_summary("PJM", trajectory=_traj("PJM")),
            run_config=_run_config("PJM"),
        )
        self.assertNotIn("row6", {r["row"] for r in fv.score_fc2(art, "t2", "PJM")})

    def test_curve_on_position_absent_is_skipped(self):
        rc = _run_config("PJM", capacity_market_clearing=True)
        art = _art(summary=_summary("PJM", trajectory=_traj("PJM")), run_config=rc)
        r5 = [r for r in fv.score_fc2(art, "t1f", "PJM") if r["row"] == "row5"][0]
        self.assertEqual(r5["status"], fv.SKIPPED)
        self.assertTrue(r5["gating"])

    def test_curve_off_no_position_row(self):
        art = _art(
            summary=_summary("PJM", trajectory=_traj("PJM")),
            run_config=_run_config("PJM"),
        )
        self.assertNotIn("row5", {r["row"] for r in fv.score_fc2(art, "t1f", "PJM")})

    def test_curve_on_position_pass(self):
        rc = _run_config("PJM", capacity_market_clearing=True)
        art = _art(
            summary=_summary("PJM", trajectory=_traj("PJM")),
            run_config=rc,
            position={"status": "PASS", "detail": "in band"},
        )
        r5 = [r for r in fv.score_fc2(art, "t1f", "PJM") if r["row"] == "row5"][0]
        self.assertEqual(r5["status"], fv.PASS)


# ---------------------------------------------------------------------------
# FC-3 capacity-evolution skill (hindcast)
# ---------------------------------------------------------------------------
class FC3Tests(unittest.TestCase):
    def test_all_bands_pass_with_baselines(self):
        self.assertEqual(
            _status(fv.score_fc3(_art(hindcast=_hindcast()), "t1h", "ERCOT")), fv.PASS
        )

    def test_raw_score_shape(self):
        # Accept the un-wrapped score.json shape too.
        self.assertEqual(
            _status(
                fv.score_fc3(_art(hindcast=_hindcast(wrapped=False)), "t1h", "ERCOT")
            ),
            fv.PASS,
        )

    def test_band_fail(self):
        self.assertEqual(
            _status(
                fv.score_fc3(_art(hindcast=_hindcast(bands="FAIL")), "t1h", "ERCOT")
            ),
            fv.FAIL,
        )

    def test_baselines_absent_is_caveat(self):
        rows = fv.score_fc3(_art(hindcast=_hindcast(baselines=False)), "t1h", "ERCOT")
        self.assertEqual(_status(rows), fv.CAVEAT)

    def test_absent_is_skipped(self):
        self.assertEqual(_status(fv.score_fc3(_art(), "t1h", "ERCOT")), fv.SKIPPED)


# ---------------------------------------------------------------------------
# FC-4 crossover dispatch skill
# ---------------------------------------------------------------------------
class FC4Tests(unittest.TestCase):
    def test_absent_is_skipped(self):
        self.assertEqual(_status(fv.score_fc4(_art(), "t1x", "ERCOT")), fv.SKIPPED)

    def test_marker_absent_is_fail(self):
        rows = fv.score_fc4(_art(crossover=_crossover(marker={})), "t1x", "ERCOT")
        self.assertEqual(_status(rows), fv.FAIL)
        self.assertIn("quarantine", rows[0]["row"])

    def test_marker_violated_is_fail(self):
        cx = _crossover(marker={"present": True, "read_ge_2026": True})
        self.assertEqual(
            _status(fv.score_fc4(_art(crossover=cx), "t1x", "ERCOT")), fv.FAIL
        )

    def test_clean_metrics_pass(self):
        cx = _crossover(
            metrics=[{"metric": "price", "year": 2024, "forecast_abs_err_frac": 0.05}]
        )
        self.assertEqual(
            _status(fv.score_fc4(_art(crossover=cx), "t1x", "ERCOT")), fv.PASS
        )

    def test_k_iso_contrast(self):
        # CO2 error 0.25: ERCOT K=1.5 (band .15) FAILs; PJM K=3.0 (band .30) CAVEATs.
        cx = _crossover(
            metrics=[{"metric": "co2", "year": 2024, "forecast_abs_err_frac": 0.25}]
        )
        ds_e = [
            r
            for r in fv.score_fc4(_art(crossover=cx), "t1x", "ERCOT")
            if r["row"] == "dispatch skill"
        ][0]
        ds_p = [
            r
            for r in fv.score_fc4(_art(crossover=cx), "t1x", "PJM")
            if r["row"] == "dispatch skill"
        ][0]
        self.assertEqual(ds_e["status"], fv.FAIL)
        self.assertEqual(ds_p["status"], fv.CAVEAT)
        self.assertEqual(fv.CROSSOVER_K_ISO["PJM"], 3.0)
        self.assertEqual(fv.CROSSOVER_K_ISO["ERCOT"], 1.5)

    def test_commercial_band_caveat(self):
        # Error between commercial (.10) and K*commercial (.15 for ERCOT) ⇒ CAVEAT.
        cx = _crossover(
            metrics=[{"metric": "price", "year": 2023, "forecast_abs_err_frac": 0.12}]
        )
        ds = [
            r
            for r in fv.score_fc4(_art(crossover=cx), "t1x", "ERCOT")
            if r["row"] == "dispatch skill"
        ][0]
        self.assertEqual(ds["status"], fv.CAVEAT)

    def test_never_scores_2026(self):
        # A ≥2026 metric is never scored (rule 22).
        cx = _crossover(
            metrics=[{"metric": "co2", "year": 2026, "forecast_abs_err_frac": 0.9}]
        )
        ds = [
            r
            for r in fv.score_fc4(_art(crossover=cx), "t1x", "ERCOT")
            if r["row"] == "dispatch skill"
        ][0]
        self.assertEqual(ds["status"], fv.SKIPPED)


# ---------------------------------------------------------------------------
# FC-5 external corridor
# ---------------------------------------------------------------------------
class FC5Tests(unittest.TestCase):
    def test_absent_is_skipped(self):
        self.assertEqual(_status(fv.score_fc5(_art(), "t2", "ERCOT")), fv.SKIPPED)

    def test_in_corridor_pass(self):
        co = _corridor(
            rows=[
                {"quantity": "gas_cap", "target_year": 2030, "verdict": "IN CORRIDOR"}
            ]
        )
        self.assertEqual(
            _status(fv.score_fc5(_art(corridor=co), "t2", "ERCOT")), fv.PASS
        )

    def test_unexplained_fail(self):
        co = _corridor(
            rows=[{"quantity": "co2", "target_year": 2035, "verdict": "UNEXPLAINED"}]
        )
        self.assertEqual(
            _status(fv.score_fc5(_art(corridor=co), "t2", "ERCOT")), fv.FAIL
        )

    def test_explained_only_caveat(self):
        co = _corridor(
            rows=[
                {
                    "quantity": "solar",
                    "target_year": 2030,
                    "verdict": "EXPLAINED DIVERGENCE",
                }
            ]
        )
        self.assertEqual(
            _status(fv.score_fc5(_art(corridor=co), "t2", "ERCOT")), fv.CAVEAT
        )


# ---------------------------------------------------------------------------
# FC-6 driver response
# ---------------------------------------------------------------------------
class FC6Tests(unittest.TestCase):
    def test_absent_is_skipped(self):
        self.assertEqual(_status(fv.score_fc6(_art(), "t2", "ERCOT")), fv.SKIPPED)

    def test_gate_pass(self):
        self.assertEqual(
            _status(fv.score_fc6(_art(driver_battery=_battery()), "t2", "ERCOT")),
            fv.PASS,
        )

    def test_gate_fail(self):
        bat = _battery(
            [
                {
                    "expr_id": "#2064",
                    "gate": True,
                    "status": "FAIL",
                    "detail": "non-monotone",
                }
            ]
        )
        self.assertEqual(
            _status(fv.score_fc6(_art(driver_battery=bat), "t2", "ERCOT")), fv.FAIL
        )

    def test_vacuous_is_caveat(self):
        # Rubric FC-6.2: a gate row that SKIPs on insufficient rungs is a caveat, never a pass.
        bat = _battery(
            [
                {
                    "expr_id": "e1",
                    "gate": True,
                    "status": "SKIP",
                    "detail": "insufficient rungs (1)",
                }
            ]
        )
        self.assertEqual(
            _status(fv.score_fc6(_art(driver_battery=bat), "t2", "ERCOT")), fv.CAVEAT
        )

    def test_report_row_does_not_gate(self):
        bat = _battery(
            [
                {"expr_id": "g", "gate": True, "status": "PASS", "detail": ""},
                {
                    "expr_id": "r",
                    "gate": False,
                    "status": "WARN",
                    "detail": "report only",
                },
            ]
        )
        self.assertEqual(
            _status(fv.score_fc6(_art(driver_battery=bat), "t2", "ERCOT")), fv.PASS
        )

    def test_paired_p1_fail(self):
        paired = [
            {"ident": "P1", "name": "co2 monotone", "status": "FAIL", "detail": "rose"}
        ]
        self.assertEqual(
            _status(fv.score_fc6(_art(paired_invariants=paired), "t2", "ERCOT")),
            fv.FAIL,
        )

    def test_paired_p3_warn_is_caveat(self):
        paired = [
            {"ident": "P3", "name": "perturbation", "status": "WARN", "detail": "cliff"}
        ]
        self.assertEqual(
            _status(fv.score_fc6(_art(paired_invariants=paired), "t2", "ERCOT")),
            fv.CAVEAT,
        )


# ---------------------------------------------------------------------------
# FC-7 provenance & DOF
# ---------------------------------------------------------------------------
class FC7Tests(unittest.TestCase):
    def test_clean_forecast(self):
        art = _art(run_config=_run_config(), dof_ledger=_dof())
        self.assertEqual(_status(fv.score_fc7(art, "t1f", "ERCOT")), fv.PASS)

    def test_run_config_absent_is_fail(self):
        art = _art(dof_ledger=_dof())
        r1 = [r for r in fv.score_fc7(art, "t1f", "ERCOT") if r["row"] == "run_config"][
            0
        ]
        self.assertEqual(r1["status"], fv.FAIL)

    def test_wrong_mode_is_fail(self):
        art = _art(run_config=_run_config(mode="backcast"), dof_ledger=_dof())
        r1 = [r for r in fv.score_fc7(art, "t1f", "ERCOT") if r["row"] == "run_config"][
            0
        ]
        self.assertEqual(r1["status"], fv.FAIL)

    def test_historic_outage_overlay_armed_is_fail(self):
        art = _art(run_config=_run_config(outage_source="historic"), dof_ledger=_dof())
        ov = [
            r for r in fv.score_fc7(art, "t1f", "ERCOT") if r["row"] == "overlay-off"
        ][0]
        self.assertEqual(ov["status"], fv.FAIL)

    def test_delivered_fuel_overlay_armed_is_fail(self):
        art = _art(
            run_config=_run_config(gas_hub_basis_overlay=True), dof_ledger=_dof()
        )
        ov = [
            r for r in fv.score_fc7(art, "t1f", "ERCOT") if r["row"] == "overlay-off"
        ][0]
        self.assertEqual(ov["status"], fv.FAIL)

    def test_dof_absent_caveat_at_t1_fail_at_t3(self):
        art = _art(run_config=_run_config())
        d1 = [r for r in fv.score_fc7(art, "t1f", "ERCOT") if r["row"] == "dof ledger"][
            0
        ]
        d3 = [r for r in fv.score_fc7(art, "t3", "ERCOT") if r["row"] == "dof ledger"][
            0
        ]
        self.assertEqual(d1["status"], fv.CAVEAT)
        self.assertEqual(d3["status"], fv.FAIL)

    def test_dof_residual_without_root_cause_is_malformed(self):
        bad = _dof([{"name": "adder", "where": "sc.x", "identification": "residual"}])
        art = _art(run_config=_run_config(), dof_ledger=bad)
        d = [r for r in fv.score_fc7(art, "t1f", "ERCOT") if r["row"] == "dof ledger"][
            0
        ]
        self.assertEqual(d["status"], fv.FAIL)

    def test_dof_from_attestation_free_parameters(self):
        att = {"free_parameters": _dof()}
        art = _art(run_config=_run_config(), attestation=att)
        d = [r for r in fv.score_fc7(art, "t1f", "ERCOT") if r["row"] == "dof ledger"][
            0
        ]
        self.assertEqual(d["status"], fv.PASS)

    def test_attestation_absent_t3_is_unattested(self):
        art = _art(run_config=_run_config(), dof_ledger=_dof())
        a = [r for r in fv.score_fc7(art, "t3", "ERCOT") if r["row"] == "attestation"][
            0
        ]
        self.assertEqual(a["status"], fv.UNATTESTED)

    def test_attestation_present_true_pass(self):
        art = _art(
            run_config=_run_config(), dof_ledger=_dof(), attestation=_attestation()
        )
        a = [r for r in fv.score_fc7(art, "t3", "ERCOT") if r["row"] == "attestation"][
            0
        ]
        self.assertEqual(a["status"], fv.PASS)

    def test_attestation_false_assertion_fail(self):
        att = _attestation(all_true=False, false_one="quarantine_attested")
        art = _art(run_config=_run_config(), dof_ledger=_dof(), attestation=att)
        a = [r for r in fv.score_fc7(art, "t3", "ERCOT") if r["row"] == "attestation"][
            0
        ]
        self.assertEqual(a["status"], fv.FAIL)

    def test_hindcast_mode_overlay_check_relaxed(self):
        # A t1h run whose harness mode is not "forecast" does not run the overlay check.
        art = _art(
            run_config=_run_config(mode="backcast", outage_source="historic"),
            dof_ledger=_dof(),
        )
        r1 = [r for r in fv.score_fc7(art, "t1h", "ERCOT") if r["row"] == "run_config"][
            0
        ]
        self.assertEqual(r1["status"], fv.PASS)  # backcast is an accepted t1h mode
        self.assertNotIn(
            fv.FAIL, {r["status"] for r in fv.score_fc7(art, "t1h", "ERCOT")}
        )


# ---------------------------------------------------------------------------
# FC-8 runtime feasibility (never blocks)
# ---------------------------------------------------------------------------
class FC8Tests(unittest.TestCase):
    def test_within_budget_pass(self):
        art = _art(summary=_summary(wall=600.0, rss=3600.0))
        self.assertEqual(_status(fv.score_fc8(art, "t1f", "ERCOT")), fv.PASS)

    def test_over_budget_caveat(self):
        art = _art(
            summary=_summary(wall=fv.RUNTIME_WALL_BUDGET_S["t1f"] + 60, rss=3600.0)
        )
        self.assertEqual(_status(fv.score_fc8(art, "t1f", "ERCOT")), fv.CAVEAT)

    def test_high_rss_caveat(self):
        art = _art(summary=_summary(wall=100.0, rss=fv.RUNTIME_RSS_NOCORUN_MB + 100))
        self.assertEqual(_status(fv.score_fc8(art, "t1f", "ERCOT")), fv.CAVEAT)

    def test_absent_perf_skipped(self):
        self.assertEqual(_status(fv.score_fc8(_art(), "t1f", "ERCOT")), fv.SKIPPED)

    def test_never_fails(self):
        # Even absurdly over budget, FC-8 caps at CAVEAT.
        art = _art(summary=_summary(wall=10 * 3600, rss=20000.0))
        self.assertNotEqual(_status(fv.score_fc8(art, "t3", "ERCOT")), fv.FAIL)


# ---------------------------------------------------------------------------
# Tier applicability matrix (rubric §3 table) + determination logic
# ---------------------------------------------------------------------------
class ApplicabilityTests(unittest.TestCase):
    def test_matrix_transcribes_rubric_table(self):
        R, O, r, n, run = fv.REQUIRED, fv.OPTIONAL, fv.REPORT, fv.NA, fv.RUNTIME
        expect = {
            "FC-1": {"t1f": R, "t1x": R, "t1h": O, "t2": R, "t3": R},
            "FC-2": {"t1f": R, "t1x": O, "t1h": n, "t2": R, "t3": R},
            "FC-3": {"t1f": n, "t1x": r, "t1h": R, "t2": R, "t3": R},
            "FC-4": {"t1f": n, "t1x": R, "t1h": n, "t2": R, "t3": R},
            "FC-5": {"t1f": r, "t1x": r, "t1h": n, "t2": R, "t3": R},
            "FC-6": {"t1f": O, "t1x": n, "t1h": n, "t2": R, "t3": R},
            "FC-7": {"t1f": R, "t1x": R, "t1h": R, "t2": R, "t3": R},
            "FC-8": {t: run for t in fv.TIERS},
        }
        self.assertEqual(fv.APPLICABILITY, expect)


def _passing_t1f():
    """A minimal 1-ISO t1f bundle that cleanly PROMOTEs."""
    return _art(
        summary=_summary(),
        run_config=_run_config(),
        dof_ledger=_dof(),
    )


class DeterminationTests(unittest.TestCase):
    def test_minimal_bundle_promotes(self):
        v = fv.determine_from_artifacts(_passing_t1f(), "t1f")
        self.assertEqual(v["determination"], fv.PROMOTE)
        self.assertEqual(v["categories"]["FC-1"]["status"], fv.PASS)
        self.assertEqual(v["categories"]["FC-7"]["status"], fv.PASS)

    def test_required_fail_holds(self):
        art = _passing_t1f()
        art["summary"] = _summary(invariants=_invariants({"I1": "FAIL"}))
        v = fv.determine_from_artifacts(art, "t1f")
        self.assertEqual(v["determination"], fv.HOLD)
        self.assertTrue(any("FC-1" in r for r in v["reasons"]))

    def test_required_skipped_holds(self):
        # FC-1 is required at t1f; an absent invariant record ⇒ HOLD.
        art = _passing_t1f()
        art["summary"] = _summary(invariants=[])
        v = fv.determine_from_artifacts(art, "t1f")
        self.assertEqual(v["determination"], fv.HOLD)

    def test_caveat_promotes_with_caveats(self):
        # Drop the DOF ledger ⇒ FC-7 CAVEAT at t1f ⇒ PROMOTE-WITH-CAVEATS.
        art = _passing_t1f()
        art["dof_ledger"] = None
        v = fv.determine_from_artifacts(art, "t1f")
        self.assertEqual(v["determination"], fv.PROMOTE_CAVEATS)

    def test_optional_absent_does_not_hold(self):
        # FC-6 is optional at t1f; its absence must not HOLD a clean bundle.
        v = fv.determine_from_artifacts(_passing_t1f(), "t1f")
        self.assertEqual(v["categories"]["FC-6"]["status"], fv.SKIPPED)
        self.assertEqual(v["determination"], fv.PROMOTE)

    def test_report_only_fail_does_not_hold(self):
        # FC-5 is report-only at t1f; a corridor UNEXPLAINED must not gate.
        art = _passing_t1f()
        art["corridor"] = _corridor(
            rows=[{"quantity": "co2", "target_year": 2030, "verdict": "UNEXPLAINED"}]
        )
        v = fv.determine_from_artifacts(art, "t1f")
        self.assertEqual(v["categories"]["FC-5"]["status"], fv.FAIL)
        self.assertEqual(v["determination"], fv.PROMOTE)  # report-only never gates

    def test_fc8_over_budget_never_holds(self):
        art = _passing_t1f()
        art["summary"] = _summary(wall=99 * 3600, rss=20000.0)
        v = fv.determine_from_artifacts(art, "t1f")
        self.assertEqual(v["categories"]["FC-8"]["status"], fv.CAVEAT)
        self.assertEqual(
            v["determination"], fv.PROMOTE_CAVEATS
        )  # caveat surfaced, never HOLD

    def test_t1h_skips_absent_inputs(self):
        # At t1h, FC-2/FC-4/FC-5/FC-6 are NA — never scored, never silently passed —
        # and the bundle promotes on FC-3 + FC-7. FC-1 is optional at t1h and reads
        # the invariants the hindcast sidecar embeds (so it scores PASS, not blocking).
        art = _art(
            hindcast=_hindcast(),
            run_config=_run_config(),
            dof_ledger=_dof(),
        )
        v = fv.determine_from_artifacts(art, "t1h")
        self.assertEqual(v["categories"]["FC-2"]["status"], fv.NA)
        self.assertEqual(v["categories"]["FC-4"]["status"], fv.NA)
        self.assertEqual(v["categories"]["FC-5"]["status"], fv.NA)
        self.assertEqual(v["categories"]["FC-6"]["status"], fv.NA)
        self.assertEqual(
            v["categories"]["FC-1"]["status"], fv.PASS
        )  # from sidecar invariants
        self.assertEqual(v["categories"]["FC-3"]["status"], fv.PASS)
        self.assertEqual(v["determination"], fv.PROMOTE)

    def test_t1h_optional_invariants_absent_skipped_not_blocking(self):
        # FC-1 is OPTIONAL at t1h: a hindcast score with no embedded invariants ⇒
        # FC-1 SKIPPED (recorded, never silently passed) and must NOT HOLD.
        art = _art(
            hindcast={
                "run_id": "r",
                "score": _hindcast(wrapped=False),
            },  # no invariants
            run_config=_run_config(),
            dof_ledger=_dof(),
        )
        v = fv.determine_from_artifacts(art, "t1h")
        self.assertEqual(v["categories"]["FC-1"]["status"], fv.SKIPPED)
        self.assertEqual(v["determination"], fv.PROMOTE)

    def test_t1h_required_hindcast_skipped_holds(self):
        # FC-3 is required at t1h; no hindcast score ⇒ HOLD (the NEISO precedent).
        art = _art(run_config=_run_config(), dof_ledger=_dof())
        v = fv.determine_from_artifacts(art, "t1h")
        self.assertEqual(v["categories"]["FC-3"]["status"], fv.SKIPPED)
        self.assertEqual(v["determination"], fv.HOLD)

    def test_sidecar_roundtrips(self):
        v = fv.determine_from_artifacts(_passing_t1f(), "t1f")
        side = fv.condensed_sidecar(v)
        self.assertEqual(side["schema"], "forecast-verdict/v1")
        self.assertEqual(side["determination"], fv.PROMOTE)
        self.assertIn("FC-1", side["categories"])


if __name__ == "__main__":
    unittest.main()
