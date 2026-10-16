"""uc-1.8: the ``lean`` solver path runs the LP heuristics (lane UC-1-FIX-9).

FINDING-ucmilp-fix9-gated-window-slowdown-2026-10-15: under the uc-1.6 reserve
u-gate the node LPs stop landing integral and the sub-MIP heuristics (RINS /
RENS / root reduced cost) are the window's only source of a good incumbent.
The change is a solver PATH: the window model HiGHS receives — matrix,
bounds, costs, integrality, so the integer feasible set — is identical under
every preset, a gated toy window returns the same optimum under the old and
the new composition, and the schedule-reuse digest separates the two so no
uc-1.7 schedule is reused.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.uc import solve as ucs
from market_sim.model.uc.params import build_uc_cluster_params
from market_sim.model.uc.window import UcWindowModel, WindowState, slice_window_inputs

from .conftest import toy_inputs

T = 24
GAP = 1e-4
_RINS_RENS_RC = (
    "mip_heuristic_run_rins",
    "mip_heuristic_run_rens",
    "mip_heuristic_run_root_reduced_cost",
)


def _opts(preset: str) -> ucs.UcSolveOptions:
    cfg = ScenarioConfig(
        iso="NEISO",
        mode="backcast",
        unit_commitment_milp=True,
        uc_mip_rel_gap=GAP,
        uc_window_time_limit_s=60.0,
        uc_solver_preset=preset,
    )
    return ucs.solve_options_from_config(cfg)


def _gated_window(fa, demand, mc, dk, params, req_mw=80.0):
    """The toy window with a reserve requirement the integer CC alone carries (u-gate live)."""
    kw = dict(dk)
    kw["reserve_requirement"] = np.full(T, req_mw)
    kw["reserve_eligible"] = np.ones(fa.n_gen, dtype=bool)
    kw["ordc_penalties"] = np.array([1000.0])
    kw["ordc_step_widths"] = np.array([req_mw])
    inputs = slice_window_inputs(fa, demand, kw, 0, T)
    n_int = int(params.integer_clusters.size)
    state = WindowState(
        u_prev=np.zeros(n_int),
        v_hist=np.zeros((n_int, 0)),
        w_hist=np.zeros((n_int, 0)),
        soc_prev=None,
        p_prev=None,
        avail_prev=None,
    )
    return UcWindowModel(inputs, params, mc, np.full((n_int, T), 200.0), state)


def _model_arrays(w: UcWindowModel) -> dict:
    lp = w.h.getLp()
    return {
        "start": np.asarray(lp.a_matrix_.start_).copy(),
        "index": np.asarray(lp.a_matrix_.index_).copy(),
        "value": np.asarray(lp.a_matrix_.value_).copy(),
        "col_cost": np.asarray(lp.col_cost_).copy(),
        "col_lower": np.asarray(lp.col_lower_).copy(),
        "col_upper": np.asarray(lp.col_upper_).copy(),
        "row_lower": np.asarray(lp.row_lower_).copy(),
        "row_upper": np.asarray(lp.row_upper_).copy(),
        "integrality": np.asarray([int(v) for v in lp.integrality_]),
    }


def test_lean_composition_turns_only_the_lp_heuristics_on():
    lean = ucs.UC_SOLVER_PRESETS["lean"]
    assert lean == dict(
        presolve="on",
        feasibility_jump=False,
        lp_heuristics=True,
        symmetry=True,
        restart=False,
    )
    opts = _opts("lean")
    assert opts.lp_heuristics is True
    # gap and time limit are the registry's, untouched by the preset
    assert opts.mip_rel_gap == GAP and opts.time_limit_s == 60.0


def test_lean_sets_the_heuristic_options_on_the_handle(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    w = _gated_window(fa, demand, mc, dk, p)
    ucs.apply_solver_options(w.h, _opts("lean"))
    assert w.h.getOptionValue("mip_heuristic_effort")[1] == pytest.approx(0.05)
    for name in _RINS_RENS_RC:
        assert w.h.getOptionValue(name)[1] is True
    assert w.h.getOptionValue("mip_heuristic_run_feasibility_jump")[1] is False
    assert w.h.getOptionValue("mip_allow_restart")[1] is False
    assert w.h.getOptionValue("mip_rel_gap")[1] == pytest.approx(GAP)


def test_the_preset_never_touches_the_window_model(uc_params_frame):
    """Same matrix, bounds, costs and integrality under every path: same integer feasible set."""
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    old_lean = dataclasses.replace(_opts("lean"), lp_heuristics=False)
    paths = {
        "lean": _opts("lean"),
        "lean_uc17": old_lean,
        "highs_default": _opts("highs_default"),
    }
    ref = None
    for opts in paths.values():
        w = _gated_window(fa, demand, mc, dk, p)
        assert w.n_reserve_gated_rows > 0  # the u-gate is live on this toy
        ucs.apply_solver_options(w.h, opts)
        arrays = _model_arrays(w)
        if ref is None:
            ref = arrays
            continue
        for key, val in arrays.items():
            np.testing.assert_array_equal(val, ref[key], err_msg=key)


def test_gated_toy_optimum_is_the_same_under_the_uc17_and_uc18_lean(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    new = _opts("lean")
    old = dataclasses.replace(new, lp_heuristics=False)
    results = {}
    for name, opts in (("uc-1.8", new), ("uc-1.7", old)):
        w = _gated_window(fa, demand, mc, dk, p)
        results[name] = ucs.solve_window(w, opts)
    a, b = results["uc-1.8"], results["uc-1.7"]
    assert a.status == b.status == "Optimal"
    assert abs(a.objective - b.objective) <= GAP * max(abs(b.objective), 1.0)
    assert np.array_equal(a.u, b.u)


def test_digest_separates_the_uc17_and_uc18_lean(
    uc_params_frame, uc_results_root, monkeypatch
):
    """A stage solved on the uc-1.7 composition is never reused by a uc-1.8 stage."""
    import market_sim.pipeline.uc as puc
    from market_sim.pipeline.solve import run_energy_solve

    from .test_floor_merit_fill import _cfg, _tranche_fleet

    puc._LAST_SOLVED.clear()
    puc.take_uc_stages()
    gens, fa, demand, mc, dk = _tranche_fleet()
    new = dict(ucs.UC_SOLVER_PRESETS["lean"])
    # The digest hashes the DA-window version (uc-1.9 left the DA windows at
    # their uc-1.8 problem, so UC_DA_DIGEST_VERSION stays "uc-1.8").
    version = puc.UC_DA_DIGEST_VERSION
    assert new["lp_heuristics"] is True and version == "uc-1.8"
    # The uc-1.7 stage: old composition and version. Restored by setting them
    # back (never monkeypatch.undo(), which would also drop uc_params_frame's patch).
    monkeypatch.setitem(ucs.UC_SOLVER_PRESETS, "lean", dict(new, lp_heuristics=False))
    monkeypatch.setattr(puc, "UC_DA_DIGEST_VERSION", "uc-1.7")
    run_energy_solve(gens, fa, demand, mc, dk, _cfg())
    monkeypatch.setitem(ucs.UC_SOLVER_PRESETS, "lean", new)
    monkeypatch.setattr(puc, "UC_DA_DIGEST_VERSION", version)
    run_energy_solve(gens, fa, demand, mc, dk, _cfg())
    s1, s2 = puc.take_uc_stages()[-2:]
    assert s1.options.lp_heuristics is False and s2.options.lp_heuristics is True
    assert s2.log["engine"]["reused_schedule"] is None
    assert s2.log["engine"]["input_digest"] != s1.log["engine"]["input_digest"]
    assert s2.log["engine"]["version"] == puc.UC_ENGINE_VERSION
    puc._LAST_SOLVED.clear()
