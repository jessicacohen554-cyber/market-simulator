"""The window solver path (``uc_solver_preset``) and the HiGHS phase profile (lane UC-SPEED).

The fast-tier half of the equivalence gate: on the toy window the ``lean`` and
``highs_default`` paths return the same schedule and an objective within the
declared gap; the phase profile parses HiGHS's own log into seconds that sum
to the measured solve; the preset names in the registry and the solver table
are one set; a harness thread count reaches the handle.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config import scenarios as sc
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.uc import solve as ucs
from market_sim.model.uc.params import build_uc_cluster_params
from market_sim.model.uc.window import UcWindowModel, WindowState, slice_window_inputs

from .conftest import toy_inputs

T = 24
GAP = 1e-4


def _window(fa, demand, mc, dk, params, noload_usd_h=200.0):
    inputs = slice_window_inputs(fa, demand, dk, 0, T)
    n_int = int(params.integer_clusters.size)
    state = WindowState(
        u_prev=np.zeros(n_int),
        v_hist=np.zeros((n_int, 0)),
        w_hist=np.zeros((n_int, 0)),
        soc_prev=None,
        p_prev=None,
        avail_prev=None,
    )
    return UcWindowModel(inputs, params, mc, np.full((n_int, T), noload_usd_h), state)


def _opts(preset: str, **harness) -> ucs.UcSolveOptions:
    cfg = ScenarioConfig(
        iso="NEISO",
        mode="backcast",
        unit_commitment_milp=True,
        uc_mip_rel_gap=GAP,
        uc_window_time_limit_s=60.0,
        uc_solver_preset=preset,
    )
    return ucs.solve_options_from_config(cfg, **harness)


def test_preset_names_are_one_set_in_registry_and_solver():
    assert set(sc.UC_SOLVER_PRESET_NAMES) == set(ucs.UC_SOLVER_PRESETS)
    assert ScenarioConfig().uc_solver_preset in sc.UC_SOLVER_PRESET_NAMES
    for name, path in ucs.UC_SOLVER_PRESETS.items():
        assert set(path) == {
            "presolve",
            "feasibility_jump",
            "lp_heuristics",
            "symmetry",
            "restart",
        }, name
    bad = type(
        "C",
        (),
        dict(uc_solver_preset="fast", uc_mip_rel_gap=GAP, uc_window_time_limit_s=1.0),
    )()
    with pytest.raises(ValueError, match="uc_solver_preset"):
        ucs.solve_options_from_config(bad)


def test_lean_and_default_paths_agree_on_the_toy_schedule(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    results = {}
    for preset in sc.UC_SOLVER_PRESET_NAMES:
        w = _window(fa, demand, mc, dk, p)
        warm = w.warm_start_vector(None, T, np.zeros_like(mc), np.zeros((w.n_int, T)))
        results[preset] = ucs.solve_window(w, _opts(preset), warm)
    ref = results["highs_default"]
    for preset, res in results.items():
        assert res.status == "Optimal", preset
        assert np.array_equal(res.u, ref.u), preset
        assert abs(res.objective - ref.objective) <= GAP * max(abs(ref.objective), 1.0)
    # The toy decommits through the night under both paths (the LP cannot).
    assert (ref.u[0, :7] == 0).all() and (ref.u[0, 7:] == 2).all()


def test_phase_profile_sums_to_the_solve_and_names_the_path(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    for preset in sc.UC_SOLVER_PRESET_NAMES:
        w = _window(fa, demand, mc, dk, p)
        res = ucs.solve_window(w, _opts(preset))
        ph = res.phase
        assert ph is not None and set(ucs.PHASE_KEYS) <= set(ph)
        seconds = (
            ph["setup_s"]
            + ph["pre_root_heur_s"]
            + ph["root_lp_s"]
            + ph["tail_s"]
            + ph["report_s"]
        )
        assert abs(seconds - res.milp_s) <= 0.02 + 1e-3 * res.milp_s
        assert ph["presolve_s"] <= ph["setup_s"] + 1e-9
        assert ph["lp_iters"] >= ph["lp_iters_sep"] + ph["lp_iters_heur"]
        assert isinstance(ph["incumbent_src"], str)
        assert res.lp_build_s <= res.build_s


def test_relaxation_and_empty_integer_set_carry_a_zero_profile(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    w = _window(fa, demand, mc, dk, p)
    rel = ucs.solve_window(w, _opts("lean"), relax=True)
    assert rel.phase["lp_iters"] == 0 and rel.phase["root_lp_s"] == 0


def test_parse_highs_mip_log_reads_the_report_and_the_table():
    lines = [
        (0.01, "MIP has 10 rows; 20 cols; 30 nonzeros; 5 integer variables\n"),
        (0.05, "Presolving model\n"),
        (0.30, "Presolve reductions: rows 9(-1); columns 19(-1); nonzeros 28(-2) \n"),
        (0.31, "\nSolving MIP model with:\n   9 rows\n   19 cols\n"),
        (
            0.50,
            " J       0       0         0   0.00%   -inf            100.0     Large        0      0      0         0     0.5s\n",
        ),
        (
            1.40,
            " R       0       0         0   0.00%   90.0            91.0        1.1%        0      0      0      1234     1.4s\n",
        ),
        (
            1.60,
            "         1       0         1 100.00%   91.0            91.0        0.00%        2      1      0      1300     1.6s\n",
        ),
        (1.70, "\nSolving report\n  Status            Optimal\n"),
        (
            1.71,
            "  Repair LPs        2 (1 feasible; 7 iterations)\n  LP iterations     1300 (total)\n"
            "                    0 (strong br.)\n                    66 (separation)\n"
            "                    0 (heuristics)\n",
        ),
    ]
    ph = ucs.parse_highs_mip_log(lines, total_s=1.75)
    assert ph["presolve_s"] == pytest.approx(0.26, abs=1e-6)
    assert ph["setup_s"] == pytest.approx(0.31, abs=1e-6)
    assert ph["pre_root_heur_s"] == pytest.approx(0.19, abs=1e-6)
    assert ph["root_lp_s"] == pytest.approx(0.90, abs=1e-6)
    assert ph["tail_s"] == pytest.approx(0.30, abs=1e-6)
    assert ph["report_s"] == pytest.approx(0.05, abs=1e-6)
    assert ph["lp_iters"] == 1300 and ph["lp_iters_sep"] == 66
    assert ph["repair_lps"] == 2 and ph["warm_feasible"] == 0
    assert ph["incumbent_src"] == "JR"


def test_harness_thread_count_reaches_the_handle(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    w = _window(fa, demand, mc, dk, p)
    opts = _opts("lean", threads=2, warm_start=False)
    assert opts.threads == 2 and opts.warm_start is False
    ucs.apply_solver_options(w.h, opts)
    assert w.h.getOptionValue("threads")[1] == 2
    assert w.h.getOptionValue("parallel")[1] == "on"
    assert w.h.getOptionValue("presolve")[1] == "on"
    assert w.h.getOptionValue("mip_heuristic_run_feasibility_jump")[1] is False
    assert w.h.getOptionValue("mip_allow_restart")[1] is False
    assert w.h.getOptionValue("mip_heuristic_effort")[1] == pytest.approx(0.05)


def test_paired_run_solves_the_base_runs_window_problems(
    uc_params_frame, uc_results_root
):
    """A paired stage run (``pin``) advances along the base schedule and records,
    per window, the same-problem objective delta and kept-``u`` agreement."""
    from market_sim.pipeline.solve import run_energy_solve
    from market_sim.pipeline.uc import take_uc_stages

    T2 = 72
    gens, fa, demand, mc, dk = toy_inputs(T2, day_mw=190.0)
    cfg = ScenarioConfig(
        iso="NEISO",
        hours=T2,
        unit_commitment_milp=True,
        uc_window_hours=24,
        uc_lookahead_hours=12,
        uc_mip_rel_gap=GAP,
    )
    res = run_energy_solve(gens, fa, demand, mc, dk, cfg)
    stage = take_uc_stages()[-1]
    base = stage.run(
        stage.fleet_in, np.asarray(res.mc_bid), write=False, record_states=True
    )
    assert set(base.prev_states) == {24, 48, 72}
    base_obj = [w["objective"] for w in stage.log["windows"]]
    stage.options = ucs.options_for_arm(
        stage.options, **ucs.UC_SOLVER_PRESETS["highs_default"]
    )
    arm = stage.run(stage.fleet_in, np.asarray(res.mc_bid), write=False, pin=base)
    assert np.array_equal(arm.u, base.u)  # advanced along the pin
    wins = stage.log["windows"]
    assert all(w["paired"] is not None for w in wins)
    assert all(w["paired"]["u_kept_equal"] for w in wins)
    for w, ob in zip(wins, base_obj):
        assert abs(w["objective"] - ob) <= GAP * max(abs(ob), 1.0)
    unrecorded = stage.run(stage.fleet_in, np.asarray(res.mc_bid), write=False)
    with pytest.raises(ValueError, match="record_states"):
        stage.run(stage.fleet_in, np.asarray(res.mc_bid), write=False, pin=unrecorded)
    take_uc_stages()  # every run re-registers the stage; leave the deque empty
