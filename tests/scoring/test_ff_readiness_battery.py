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

import json

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
    """The golden posture resolves EXACTLY what production ships (C.4(a) B1).

    Was: "every real-capacity-market ISO curve-ON, ERCOT OFF", asserted against
    the hand-maintained ``GOLDEN_CMC_BY_ISO``. That dict listed NYISO ON while
    the shipped ``ScenarioConfig`` field omits it, so the old assertion was
    green on a divergence — it tested the second answer against itself. Owner
    decision C.4(a) B1 (2026-08-03) deleted the dict and made the shipped field
    the one source; this now asserts parity with it.
    """
    from market_sim.config.capacity_market import resolve_capacity_market_clearing
    from market_sim.config.scenarios import ScenarioConfig

    shipped = ScenarioConfig().capacity_market_clearing_by_iso or {}
    for iso in ALL_ISOS:
        cfg = B.golden_posture_config(iso)
        want = bool(shipped.get(iso, False))
        assert resolve_capacity_market_clearing(cfg, iso) is want, iso

    # The two the signature names by hand, pinned so a silent re-add of either
    # to the shipped mapping is a visible test change and not a quiet flip.
    assert (
        resolve_capacity_market_clearing(B.golden_posture_config("ERCOT"), "ERCOT")
        is False
    )
    assert (
        resolve_capacity_market_clearing(B.golden_posture_config("NYISO"), "NYISO")
        is False
    )


def test_golden_posture_is_value_identical_to_the_shipped_default():
    # C.4(a) B1: golden posture and shipped posture are ONE answer. Passing the
    # mapping explicitly must equal inheriting it, on every ISO.
    from market_sim.config.scenarios import ScenarioConfig

    for iso in ALL_ISOS:
        assert (
            B.golden_posture_config(iso).capacity_market_clearing_by_iso
            == ScenarioConfig().capacity_market_clearing_by_iso
        ), iso


def test_golden_cmc_constant_is_deleted():
    # Rule 26 [R-DELETE]: the parallel constant is removed, not zeroed — a
    # second answer that still parses is a re-armable second answer.
    assert not hasattr(B, "GOLDEN_CMC_BY_ISO")


# --------------------------------------------------------------------------- #
# Part a — input-resolution walk (no LP)
# --------------------------------------------------------------------------- #
# The three walker tests below resolve the REAL input tree, including the
# derived data/clean/confirmed-retirements partition (gitignored; built by
# scripts/data/curate_confirmed_retirements.py) — pyproject's `integration`
# marker definition exactly ("exercises real data inputs, not a hermetic unit
# test"; the test_consume_* precedent). They run in the full pre-push lane.
@pytest.mark.integration
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


@pytest.mark.integration
def test_resolve_report_no_hard_fail_full_horizon():
    # The load-bearing assertion: every exogenous forward input resolves for
    # every ISO across the full 2026-2050 horizon with no MISSING/ERROR.
    rep = B.resolve_report(ALL_ISOS)
    assert rep["hard_fail_count"] == 0, rep["hard_fails"]
    assert rep["green"] is True


@pytest.mark.integration
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
    # NEISO + NYISO + PJM complete; ERCOT + MISO never declared; CAISO withdrawn
    # — read from the committed calibration-complete.json (no re-derivation).
    #
    # NYISO was `withdrawn` (2026-07-19 phantom-outage re-audit) until nyiso-104b
    # RE-DECLARED it 2026-07-31 on the post-correction keeper, alongside the
    # CALIBRATED-WITH-CAVEATS determination. PJM was DECLARED the same day
    # (session pjm-142) at CALIBRATED with zero failing criteria; this test kept
    # asserting PJM == "none" for two days afterwards — an FR-21-class
    # bookkeeping desync, corrected by FFR-3B (2026-08-02).
    #
    # CAISO is the SAME desync class, caught the same way. It was declared
    # `complete` 2026-08-05 while this test still asserted "none" (so the test
    # was already failing on that string), and the rubric v3.1 owner amendment
    # 2026-08-06 then WITHDREW the marker — its keeper re-scores NOT-YET once
    # C3a mean LMP stops being ledgerable. `withdrawn` and `none` are equally
    # unauthorized to the gates (holdout_policy reads only `complete`/`final`),
    # but they are not the same fact and the marker state should not flatten
    # them: `withdrawn` records that a marker existed and was revoked, which is
    # what a later re-declaration has to reckon with.
    #
    # All `complete` markers are VALIDATION-tier only: the two-tier split
    # means `complete` no longer authorizes the touch-once locked test, which
    # needs the separate `final` block (EMPTY at HEAD).
    #
    # Two more moves this test lagged behind, both read from the committed
    # marker file (no re-derivation), and both the SAME desync class again:
    # ERCOT was DECLARED `complete` on the 2026-08-25-234-eastex-identity
    # keeper, and NYISO's marker was WITHDRAWN 2026-08-30 by owner ruling at
    # the capacity-expansion director's refresh-#12 card (the CAISO precedent
    # applied uniformly: a `complete` marker cannot stand on a NOT-YET keeper;
    # nyiso-157 re-keyed it onto a second consecutive NOT-YET). Landed on main
    # in the #4516 merge (2026-08-31); the assertions were corrected 2026-09-02
    # by the fast-tier repair lane. `withdrawn` is kept distinct from `none`
    # for the reason given above.
    #
    # NYISO RE-DECLARED `complete` 2026-09-05 (owner ruling Q38, 2026-09-04,
    # capx ledger §0af amendment 1 / §3; records lane D56-R) on the first NYISO
    # keeper lineage to read CALIBRATED (2026-09-05-nyiso-189-steam-identity),
    # exactly per the withdrawn block's own `reentry` clause — its third grant.
    # The 2026-08-30 withdrawal record is nested WHOLE beneath the new entry
    # (`complete.NYISO.prior_withdrawal_2026_08_30`), so `withdrawn` now holds
    # CAISO alone. Same desync class as every move above; the assertion moves
    # with the marker in the same commit this time
    # (docs/handoffs/FINDING-capx-d56r-nyiso-redeclaration-2026-09-05.md).
    #
    # NYISO WITHDRAWN AGAIN 2026-09-05, later the same day: the owner ruled
    # the nyiso-192 Astoria merit-panel arm promoted (nyiso192-Q1 option (i),
    # session nyiso-193) and it reads NOT-YET (C1-2024 CC_REGULAR +3.68 TWh /
    # +3.0 pp; C3c then not lone), so the Q5 uniform rule takes the marker
    # down (complete.NYISO -> withdrawn.NYISO, the D56-R entry nested whole
    # as `prior_record_2026_09_05_d56r`). `withdrawn` holds CAISO and NYISO;
    # `keeper_at_declaration` on the NYISO record is the run the marker was
    # declared on (nyiso-189), not the promoted keeper. Assertion moved in the
    # same commit as the marker (docs/calibration-log/nyiso.md, nyiso-193).
    #
    # CAISO RE-DECLARED `complete` 2026-09-06 (owner decision card, session
    # caiso-261) on the first CAISO keeper lineage to read CALIBRATED with C3a
    # PASS in every year (2026-09-06-caiso-260-b1-demand; CALIBRATED since
    # caiso-252, C3c the lone ledgered caveat) — the 2026-08-06 withdrawal's
    # own reason (a NOT-YET keeper under rubric v3.1) is gone. The withdrawn
    # record is nested WHOLE beneath the new entry
    # (`complete.CAISO.withdrawal_history_2026_08_06`). Assertion moved in the
    # same commit as the marker
    # (results/calibration/ASSESSMENT-caiso261-complete-declaration-2026-09-06.md).
    #
    # NYISO RE-DECLARED `complete` 2026-09-06 (owner in-session ruling, session
    # nyiso-209, verbatim 'Ok declare it and run 22') on the keeper lineage that
    # returned to CALIBRATED by structural repair (nyiso-196, nyiso-202) -- its
    # FOURTH grant, per the withdrawn block's own `reentry` clause. The
    # 2026-09-05 withdrawal record is nested WHOLE beneath the new entry
    # (`complete.NYISO.prior_withdrawal_2026_09_05`). With CAISO re-declared
    # the same day, `withdrawn` is EMPTY for the first time. Assertion moved
    # in the same commit as the marker
    # (docs/FINDING-nyiso209-redeclaration-and-2022-touchpoint-2026-09-06.md).
    #
    # NYISO RE-KEYED 2026-09-07 (session nyiso-213, rule 22 D-5(b)): the
    # `complete` marker's `keeper` field tracks NYISO's CURRENT designated
    # keeper, so the nyiso-213 promotion moved it
    # 2026-09-06-nyiso-202-startup-aware -> 2026-09-07-nyiso-213-summer-seam.
    # The marker's own `rekey_note` records the artifact-only determination
    # re-verification D-5(b) requires (CALIBRATED, grade 7/8, fails 0, C3c the
    # lone ledgered caveat -- IDENTICAL to the superseded keeper, so the Q5
    # "a WORSE determination STOPS the promotion" clause did not fire).
    # `declared`, `by` and `keeper_at_declaration` are untouched by a re-key, so
    # only the one string moves. The assertion did NOT move in that lane's
    # commit -- the same bookkeeping-desync class every comment above records --
    # and is corrected here by SPP-38
    # (docs/handoffs/FINDING-spp-38-2026-09-07.md §3, row 12; NOT an SPP
    # failure).
    #
    # NYISO RE-KEYED AGAIN 2026-09-09 (session nyiso-fuelvintage-1, rule 22
    # D-5(b)): the promotion of the 2019-2022 EIA-860 retiree window and
    # gas_electric_power_monthly_level, under the owner ruling of 2026-09-09
    # ("these should be promoted as keepers on both 860 and gas shape counts
    # regardless of inertness"), moved the `complete` marker's keeper
    # 2026-09-07-nyiso-213-summer-seam -> 2026-09-09-nyiso-221-fuelvintage-span.
    # The D-5(b) re-verification was artifact-only (scripts/calibration_verdict.py
    # on the committed bundle, never a solve) and read CALIBRATED with a criterion
    # table BYTE-IDENTICAL to the superseded keeper's -- zero flips in either
    # direction -- so the "a WORSE determination STOPS the promotion" clause did
    # not fire. `declared`, `by` and `keeper_at_declaration` are untouched by a
    # re-key, so again only the one string moves.
    #
    # THIS TIME THE ASSERTION MOVES IN THE PROMOTING LANE'S OWN PR, which is what
    # every comment above says should happen and what the last two re-keys failed
    # to do (nyiso-213's was corrected later by SPP-38; nyiso-202's by the merge
    # of #4516). The desync class this file keeps recording is closed here rather
    # than handed to the next lane.
    #
    # KEEPER IDS ARE READ FROM THE SHARDS, NOT PINNED AS LITERALS (owner ruling
    # R-BE, director board v43, 2026-09-25; proposal
    # docs/handoffs/FINDING-y29-promotion-provenance-2026-09-24.md §4; audit
    # lane Y-31). Every re-key above was a promotion that had to edit this
    # test, and several promoters skipped it. For every `complete` ISO the
    # marker's `keeper` must equal keepers/<ISO>.json `keeper`: a promotion
    # that re-keys the marker keeps this green, and one that forgets fails it.
    #
    # The `complete` set moves with the marker file: SPP IN (declared
    # 2026-09-13, owner, session spp-40, "Complete then run"; Y-29 §1.2,
    # confirmed R-BD); NYISO OUT (WITHDRAWN 2026-09-25 by owner ruling R-BC,
    # the Q5 uniform rule on a NOT-YET keeper -- its fourth withdrawal; the
    # prior entry nested whole as `withdrawn.NYISO.prior_record_complete_entry`).
    complete = {"ERCOT", "NEISO", "PJM", "CAISO", "SPP"}
    marker_doc = json.loads(B._MARKER_PATH.read_text())
    assert set(marker_doc["complete"]) == complete
    keepers_dir = B._MARKER_PATH.parent / "keepers"
    for iso in sorted(complete):
        state = B._marker_state(iso)
        assert state["marker"] == "complete", iso
        shard = json.loads((keepers_dir / f"{iso}.json").read_text())
        assert state["keeper"] == shard["keeper"], iso
    assert B._marker_state("MISO")["marker"] == "none"
    nyiso = B._marker_state("NYISO")
    assert nyiso["marker"] == "withdrawn"
    assert nyiso["withdrawn"] == "2026-09-25"
    assert nyiso["keeper"] == "2026-09-06-nyiso-202-startup-aware"


def test_t1f_verdict_reads_ff2d_hold():
    # Every ISO reads HOLD at the FF-2D T1-F gate (committed verdicts JSON).
    for iso in ALL_ISOS:
        assert B._t1f_verdict(iso)["determination"] == "HOLD", iso


@pytest.mark.integration  # gate_c input-resolution walks the real data tree
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
    # NEISO holds the backcast marker; NYISO's was WITHDRAWN 2026-08-30 (owner
    # r#12 ruling, Q5-W, commit ecc2d609 — the same marker move
    # test_marker_state_reflects_committed_markers pins above). The fast-tier repair
    # of 2026-09-02 corrected that copy but not this integration-marked one, so
    # the golden data tier's run #7 (2026-08-31) failed here. Gate A is GREEN
    # for NEISO only — and the gate still does not open for either, because
    # gate B (FF-2D T1-F) reads HOLD for every ISO. That is the invariant worth
    # pinning: a backcast marker alone never opens the forecast gate, and a
    # withdrawn one does not either.
    # [2026-09-05, D56-R] NYISO RE-DECLARED `complete` (owner ruling Q38 on
    # 2026-09-05-nyiso-189-steam-identity) — Gate A is GREEN for NEISO and
    # NYISO; the invariant pinned here is unchanged: gate B still reads HOLD on
    # the FF-2D key, so neither gate opens.
    # [2026-09-05, nyiso-193, later the same day] NYISO WITHDRAWN again under
    # the Q5 uniform rule when the owner-ruled nyiso-192 promotion re-keyed the
    # keeper onto a NOT-YET run — Gate A is GREEN for NEISO only once more;
    # the pinned invariant is unchanged (gate B HOLD, neither gate opens).
    # [2026-09-06, caiso-261] CAISO RE-DECLARED `complete` (owner decision
    # card) on 2026-09-06-caiso-260-b1-demand, CALIBRATED — Gate A is GREEN
    # for NEISO and CAISO; the pinned invariant is unchanged (gate B HOLD on
    # the FF-2D key for every ISO, so no gate opens).
    # [2026-09-06, nyiso-209] NYISO RE-DECLARED `complete` (owner in-session
    # ruling, verbatim 'Ok declare it and run 22') on the keeper lineage that
    # returned to CALIBRATED by structural repair -- its FOURTH grant, and the
    # same marker move test_marker_state_reflects_committed_markers pins above.
    # That lane moved its own copy of the assertion but not this
    # integration-marked one, so this test stayed red on the string; corrected
    # by SPP-38 (docs/handoffs/FINDING-spp-38-2026-09-07.md §3, row 13; NOT an
    # SPP failure). `withdrawn` is EMPTY at HEAD. THE PINNED INVARIANT IS
    # UNCHANGED and is the point of this test: gate B (FF-2D T1-F) still reads
    # HOLD for every ISO, so a backcast marker -- complete or withdrawn -- never
    # opens the forecast gate on its own.
    assert sc["NEISO"]["gate_a_backcast"]["marker"] == "complete"
    assert sc["CAISO"]["gate_a_backcast"]["marker"] == "complete"
    assert sc["NYISO"]["gate_a_backcast"]["marker"] == "complete"
    for iso in ("NEISO", "NYISO", "CAISO"):
        assert sc[iso]["gate_b_t1f"]["determination"] == "HOLD", iso
        assert not sc[iso]["gate_open"], iso


# --------------------------------------------------------------------------- #
# _bundle_signature — the kill-resume drill's permutation discriminator (FFR-3J)
# --------------------------------------------------------------------------- #
def _write_stub_bundle(run_dir, dispatch, prices):
    """Write a minimal one-year cache dir _bundle_signature can read.

    Only the surface the signature touches is populated: a single
    ``year_2026.parquet`` holding the dispatch/price arrays. No config.yaml and
    no evolution ledger, so :func:`check_forecast_invariants.load_run` takes its
    documented defaults and the signature's ledger counts are all zero.
    """
    import numpy as np

    from market_sim.model.lp import DispatchResult

    run_dir.mkdir(parents=True, exist_ok=True)
    n_zones, T = prices.shape
    zeros_z = np.zeros((n_zones, T), dtype=float)
    result = DispatchResult(
        dispatch=dispatch,
        wind_dispatched=zeros_z,
        solar_dispatched=zeros_z,
        slack=zeros_z,
        dump=zeros_z,
        prices=prices,
        storage_charge=None,
        storage_discharge=None,
        storage_soc=None,
        flows=None,
        objective_value=0.0,
        status="Optimal",
        build_time=0.0,
        solve_time=0.0,
    )
    result.to_parquet(run_dir / "year_2026.parquet")
    return run_dir


def test_bundle_signature_discriminates_permutation_from_different_values(tmp_path):
    """A row permutation must move the byte hash but NOT the multiset hash.

    This is the FFR-3J discriminator the kill-resume drill leans on: identical
    aggregates with differing byte hashes are ambiguous between a re-ordering of
    the arrays and a genuinely different solve, and only an order-insensitive
    hash separates them. Pinned on synthetic arrays (no LP) so the drill's
    verdict semantics stay trustworthy without a solve.

    Also pins the axis subtlety: ``np.sort`` sorts along the LAST axis, so the
    ``*_sorted_hash`` is NOT invariant to a permutation of the ROWS — it is the
    fully flattened ``*_multiset_hash`` that is.
    """
    import numpy as np

    rng = np.random.default_rng(0)
    disp = rng.random((5, 24)) * 100.0
    price = rng.random((3, 24)) * 50.0
    perm_g = [3, 0, 4, 1, 2]  # generator re-ordering
    perm_z = [2, 0, 1]  # zone re-ordering

    a = B._bundle_signature(_write_stub_bundle(tmp_path / "a", disp, price))[2026]
    b = B._bundle_signature(
        _write_stub_bundle(tmp_path / "b", disp[perm_g], price[perm_z])
    )[2026]

    # A permutation is exactly what the drill saw: equal aggregates, unequal bytes.
    assert a["dispatch_sum"] == b["dispatch_sum"]
    assert a["price_sum"] == b["price_sum"]
    assert a["dispatch_hash"] != b["dispatch_hash"]
    assert a["price_hash"] != b["price_hash"]

    # The flattened multiset hash sees through the permutation — this is the
    # branch that means "same numbers, different order".
    assert a["dispatch_multiset_hash"] == b["dispatch_multiset_hash"]
    assert a["price_multiset_hash"] == b["price_multiset_hash"]

    # The last-axis sort does NOT, because the rows themselves moved.
    assert a["dispatch_sorted_hash"] != b["dispatch_sorted_hash"]

    # A genuinely different value moves the multiset hash too — the other branch.
    disp_c = disp.copy()
    disp_c[0, 0] += 1e-6
    c = B._bundle_signature(_write_stub_bundle(tmp_path / "c", disp_c, price))[2026]
    assert c["dispatch_multiset_hash"] != a["dispatch_multiset_hash"]


def test_bundle_signature_is_identical_for_identical_bundles(tmp_path):
    """Two byte-identical bundles produce equal signatures (the drill's PASS)."""
    import numpy as np

    rng = np.random.default_rng(1)
    disp = rng.random((4, 12)) * 100.0
    price = rng.random((2, 12)) * 50.0
    a = B._bundle_signature(_write_stub_bundle(tmp_path / "a", disp, price))
    b = B._bundle_signature(_write_stub_bundle(tmp_path / "b", disp, price))
    assert a == b
