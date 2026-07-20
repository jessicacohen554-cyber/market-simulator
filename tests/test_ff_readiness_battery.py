"""Tests for the FF-3E full-solve readiness battery (scripts/ff_readiness_battery.py).

Trivial-first and **no LP solve**: the no-LP instruments (input-resolution walk,
config completeness, wall/RSS projection) and the schedulability guard are
exercised on the real resolvers over tiny/whole horizons, so the battery's
fail-loud semantics and the §2.1a/§2.1b posture are pinned independently of any
solve. The kill-resume drill (the battery's only LP path) is intentionally NOT
run here — it is exercised in-session via the CLI at T0 scale and recorded in the
close-out; a unit test must never solve (rule 12 / plan §2.1b).

The battery and the runner guard live under ``scripts/`` (a namespace package on
``sys.path`` via the root conftest), so they import as ``scripts.*``.
"""

import pytest

import scripts.ff_readiness_battery as B
from scripts.run_full_horizon import assert_schedulable

ALL_ISOS = B.GOLDEN_ISOS


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #
def test_hold_flat_from_constant_series():
    # A series constant from 2030 onward reports 2030 as the plateau start.
    vals = {y: (1.0 if y < 2030 else 2.0) for y in range(2026, 2051)}
    assert B._hold_flat_from(vals) == 2030


def test_hold_flat_from_varying_to_end_is_none():
    vals = {y: float(y) for y in range(2026, 2051)}  # strictly rising to 2050
    assert B._hold_flat_from(vals) is None


def test_hold_flat_from_all_constant():
    vals = {y: 3.0 for y in range(2026, 2051)}
    assert B._hold_flat_from(vals) == 2026


# --------------------------------------------------------------------------- #
# Golden posture (§2.1a)
# --------------------------------------------------------------------------- #
def test_golden_posture_default_flips():
    cfg = B.golden_posture_config("ERCOT")
    assert cfg.mode == "forecast"
    assert cfg.datacenter_load_path == "mid"
    assert cfg.correlated_forced_outage is True
    assert cfg.entry_lookahead_reprice is True
    assert (cfg.start_year, cfg.end_year) == (B.HORIZON_START, B.HORIZON_END)


def test_golden_posture_capacity_clearing_per_iso():
    from market_sim.config.capacity_market import resolve_capacity_market_clearing

    # §2.1a decision (a): every real-capacity-market ISO curve-ON, ERCOT OFF.
    for iso in ("CAISO", "PJM", "MISO", "NYISO", "NEISO"):
        cfg = B.golden_posture_config(iso)
        assert resolve_capacity_market_clearing(cfg, iso) is True, iso
    cfg = B.golden_posture_config("ERCOT")
    assert resolve_capacity_market_clearing(cfg, "ERCOT") is False


def test_golden_cmc_covers_the_five_non_ercot_isos():
    assert set(B.GOLDEN_CMC_BY_ISO) == set(ALL_ISOS) - {"ERCOT"}
    assert all(v is True for v in B.GOLDEN_CMC_BY_ISO.values())


# --------------------------------------------------------------------------- #
# Part a — input-resolution walk (no LP)
# --------------------------------------------------------------------------- #
def test_walk_inputs_trivial_single_year():
    # 1 ISO, a 1-year window: the trivial-first case (rule "test trivial first").
    rows = B.walk_inputs("ERCOT", start_year=2026, end_year=2026)
    names = {r.name for r in rows}
    # Every forward-input family the plan §2.1b(a) enumerates is present.
    for expected in (
        "demand_growth_rate",
        "datacenter_block_mw",
        "gas_price",
        "coal_price",
        "oil_price",
        "carbon_price",
        "ces_premium",
        "rps_target",
        "capacity_price_firm",
        "atb_entry_costs",
        "ira_wind_solar_last_year",
        "capacity_market_clearing",
        "confirmed_retirements",
        "weather_year_pool",
    ):
        assert expected in names, expected
    assert not [r for r in rows if r.status in B._HARD_STATUSES]


def test_resolve_report_no_hard_fail_full_horizon():
    # The load-bearing assertion: every exogenous forward input resolves for
    # every ISO across the full 2026-2050 horizon with no MISSING/ERROR.
    rep = B.resolve_report(ALL_ISOS)
    assert rep["hard_fail_count"] == 0, rep["hard_fails"]
    assert rep["green"] is True


def test_ercot_confirmed_horizon_is_reported_not_failed():
    # ERCOT's confirmed-retirement registry runs out mid-window (near-term
    # instruments only); that is an INFO horizon note, never a hard fail.
    rows = {r.name: r for r in B.walk_inputs("ERCOT")}
    cr = rows["confirmed_retirements"]
    assert cr.status in (B.INFO, B.OK, B.NA)
    assert cr.status not in B._HARD_STATUSES


def test_datacenter_block_plateaus_are_reported():
    # The published DC-boom anchors plateau (ERCOT ~2030, CAISO ~2040) — the
    # walk must surface the held-flat tail as a PLATEAU note.
    rows = {r.name: r for r in B.walk_inputs("ERCOT")}
    dc = rows["datacenter_block_mw"]
    assert dc.status == B.PLATEAU
    assert dc.hold_flat_from is not None and dc.hold_flat_from < B.HORIZON_END


# --------------------------------------------------------------------------- #
# Part b — config completeness (no LP)
# --------------------------------------------------------------------------- #
def test_config_completeness_all_isos_green():
    rep = B.config_report(ALL_ISOS)
    assert rep["green"] is True, {
        iso: [c for c in r["checks"] if not c["ok"]]
        for iso, r in rep["per_iso"].items()
    }


def test_config_completeness_cache_key_stable_round_trip():
    r = B.config_completeness("CAISO")
    named = {c["check"]: c["ok"] for c in r["checks"]}
    assert named["cache_key_stable_round_trip"] is True
    assert named["run_config_round_trips_value_identical"] is True


# --------------------------------------------------------------------------- #
# Part d — wall/RSS projection (no LP)
# --------------------------------------------------------------------------- #
def test_projection_structure_and_corun_plan():
    rep = B.project_full_horizon()
    per = rep["per_iso"]
    assert set(per) == set(ALL_ISOS)
    for iso, r in per.items():
        # lower bound never exceeds the super-linear projection.
        assert r["lower_bound_h"] <= r["projected_h"], iso
        assert r["projected_h"] > 0
        assert r["proj_peak_rss_gb"] > 0
    # §2.4: the two heavy per-plant ISOs (>= 8.6 GB late) run solo.
    assert set(rep["concurrency_plan"]["solo_isos"]) == {"PJM", "MISO"}
    assert rep["concurrency_plan"]["total_serial_wall_h"] > 0


def test_projection_rss_matches_no_corun_flag():
    rep = B.project_full_horizon()
    for iso, r in rep["per_iso"].items():
        assert r["no_corun"] == (r["proj_peak_rss_gb"] >= B.NO_CORUN_RSS_GB), iso


# --------------------------------------------------------------------------- #
# Part e — schedulability guard (no LP)
# --------------------------------------------------------------------------- #
def test_guard_refuses_over_cap_unauthorized():
    with pytest.raises(SystemExit):
        assert_schedulable(2026, 2050, full_solve_authorized=False)


def test_guard_allows_at_cap():
    assert assert_schedulable(2026, 2030, full_solve_authorized=False) == 5


def test_guard_allows_over_cap_when_authorized():
    assert assert_schedulable(2026, 2050, full_solve_authorized=True) == 25


def test_guard_boundary_six_years_refused():
    with pytest.raises(SystemExit):
        assert_schedulable(2026, 2031, full_solve_authorized=False)


# --------------------------------------------------------------------------- #
# Registration & §2.1b gate scorecard (no LP)
# --------------------------------------------------------------------------- #
def test_marker_state_reflects_committed_markers():
    # NEISO complete, NYISO withdrawn, the four frontier ISOs none — read from
    # the committed calibration-complete.json (no re-derivation).
    assert B._marker_state("NEISO")["marker"] == "complete"
    assert B._marker_state("NYISO")["marker"] == "withdrawn"
    for iso in ("ERCOT", "CAISO", "PJM", "MISO"):
        assert B._marker_state(iso)["marker"] == "none", iso


def test_t1f_verdict_reads_ff2d_hold():
    # Every ISO reads HOLD at the FF-2D T1-F gate (committed verdicts JSON).
    for iso in ALL_ISOS:
        assert B._t1f_verdict(iso)["determination"] == "HOLD", iso


def test_build_registration_scorecard_no_iso_gate_open():
    art = B.build_registration(drill_result=None)
    assert art["meta"]["kind"] == "readiness"
    sc = art["gate_scorecard"]
    assert set(sc) == set(ALL_ISOS)
    # No ISO clears the gate at HEAD (all HOLD on b); the decision is the owner's.
    assert all(not s["gate_open"] for s in sc.values())
    # Readiness (a-part config + resolution) is green for every ISO.
    assert all(
        s["gate_c_readiness"]["input_resolution_green"]
        and s["gate_c_readiness"]["config_green"]
        for s in sc.values()
    )
    # Only NEISO holds the backcast marker.
    assert sc["NEISO"]["gate_a_backcast"]["marker"] == "complete"
    assert sc["NYISO"]["gate_a_backcast"]["marker"] == "withdrawn"
