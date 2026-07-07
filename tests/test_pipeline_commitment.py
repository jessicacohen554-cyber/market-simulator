"""Trivial-case tests for the Stage-4 shared P2 commitment pass.

CLAUDE.md testing pattern: 1 zone, 2 generators, 24 hours. The shared
``run_commitment_pass`` must reproduce the exact inline P2 sequence both
orchestrators ran — the economic commitment screen + coal pin (backcast
``_commitment_pass`` / the runner P2 block) and the CAISO RA must-offer
bridge — statement-for-statement, byte-identical on the trivial LP.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.commitment import (
    apply_commitment_with_coal_pin,
    caiso_ra_mustoffer_min_gen,
    compute_commitment,
)
from market_sim.model.dispatch import solve_dispatch
from market_sim.pipeline import commitment as pipeline_commitment
from market_sim.pipeline.commitment import (
    build_caiso_ra_p1_prep,
    build_pjm_reserve_p1_prep,
    caiso_ra_p1_floor_fleet,
    pjm_commitment_scoped_reserve_fleet,
    run_commitment_pass,
)
from market_sim.pipeline.solve import run_energy_solve

T = 24


def _trivial_inputs(iso: str):
    """One-zone fleet on the ISO's real topology: cheap CC + peaker CT."""
    iso_config = get_iso_config(iso)
    zone_names = iso_config.zone_names
    n_zones = iso_config.n_zones
    generators = [
        Generator(
            unit_id="G0",
            name="cheap_cc",
            zone=zone_names[0],
            fuel_type="gas_cc",
            pmax_mw=500.0,
            pmin_mw=0.0,
            heat_rate=7.0,
            vom=3.0,
            eford=0.0,
        ),
        Generator(
            unit_id="G1",
            name="peaker_ct",
            zone=zone_names[0],
            fuel_type="gas_ct",
            pmax_mw=200.0,
            pmin_mw=0.0,
            heat_rate=10.0,
            vom=5.0,
            eford=0.0,
        ),
    ]
    fleet_arrays = generators_to_fleet_arrays(generators, zone_names, hours=T)
    demand = np.full((n_zones, T), 60.0)
    demand[0, 18] = 550.0  # peaky hour so the CT runs and the screen has work
    mc_base = np.vstack([np.full(T, 30.0), np.full(T, 60.0)])
    from market_sim.model.transmission import (
        build_incidence_matrix,
        get_link_bidirectional_array,
        get_ttc_array,
    )

    dispatch_kwargs = dict(
        wind_cf=np.full((n_zones, T), 0.3),
        wind_cap=np.zeros(n_zones),
        solar_cf=np.full((n_zones, T), 0.2),
        solar_cap=np.zeros(n_zones),
        voll=iso_config.voll,
        incidence=build_incidence_matrix(iso_config.links, zone_names),
        ttc=get_ttc_array(iso_config.links),
        link_bidirectional=get_link_bidirectional_array(iso_config.links),
        storage_zone_idx=None,
        T=T,
    )
    return generators, fleet_arrays, demand, mc_base, dispatch_kwargs


def _p1_state(iso: str, config: ScenarioConfig) -> dict:
    """Solve the trivial P1 and package the state dict the P2 pass consumes."""
    gens, fa, demand, mc_base, dk = _trivial_inputs(iso)
    p1 = solve_dispatch(fa, demand, mc=mc_base, **dk)
    assert p1.status == "Optimal"
    return {
        "year": 2024,
        "iso": iso,
        "fleet": gens,
        "fleet_arrays": fa,
        "mc_base": mc_base,
        "mc_bid": mc_base,  # no markup on the trivial case
        "p1_result": p1,
        "demand": demand,
        "dispatch_kwargs": dk,
        "config": config,
        "zone_names": get_iso_config(iso).zone_names,
    }


def _reference_econ_screen(state: dict):
    """The pre-Stage-4 inline economic screen + coal pin (the reference)."""
    cfg = state["config"]
    p1 = state["p1_result"]
    committed = compute_commitment(
        p1.prices,
        state["mc_base"],
        state["fleet"],
        state["fleet_arrays"],
        cfg,
        storage_charge=p1.storage_charge,
        storage_discharge=p1.storage_discharge,
        storage_zone_idx=state["dispatch_kwargs"]["storage_zone_idx"],
        demand=state["demand"],
        as_value=None,
    )
    fa_p2 = apply_commitment_with_coal_pin(
        state["fleet_arrays"],
        committed,
        p1.dispatch,
        state["fleet"],
        screen_coal=cfg.commitment_screen_coal,
        preserve_min_gen=False,
        couple_peak=False,
    )
    return solve_dispatch(
        fa_p2, state["demand"], mc=state["mc_bid"], **state["dispatch_kwargs"]
    )


def test_econ_screen_matches_inline_reference():
    """Economic-screen path: byte-identical to the inline P2 sequence."""
    config = ScenarioConfig(hours=T, commitment_enabled=True)
    state = _p1_state("ERCOT", config)
    ref = _reference_econ_screen(dict(state))

    got = run_commitment_pass(state)
    assert got.status == "Optimal"
    assert np.array_equal(got.dispatch, ref.dispatch)
    assert np.array_equal(got.prices, ref.prices)
    # The P2 fleet bounds are stashed for the bundle writer (D-2 attribution).
    assert "fleet_arrays_p2" in state


def test_caiso_ra_branch_matches_inline_reference():
    """CAISO RA must-offer bridge: byte-identical to the inline branch."""
    config = ScenarioConfig(hours=T, commitment_enabled=False, caiso_ra_mustoffer=True)
    state = _p1_state("CAISO", config)
    fa = state["fleet_arrays"]
    p1 = state["p1_result"]

    # Reference: the pre-Stage-4 inline CAISO branch (plain physical bridge).
    ra_floor = caiso_ra_mustoffer_min_gen(
        p1.dispatch, fa, state["fleet"], config.caiso_ra_min_load_frac
    )
    base_min_gen = (
        fa.min_gen
        if fa.min_gen is not None
        else np.broadcast_to(fa.pmin[:, None], ra_floor.shape)
    )
    from market_sim.data.floor_mechanisms import MECH_RA_MUSTOFFER

    new_mech = (
        fa.min_gen_mechanism.copy()
        if getattr(fa, "min_gen_mechanism", None) is not None
        else np.zeros(ra_floor.shape, dtype=np.int8)
    )
    new_mech[ra_floor > base_min_gen] = MECH_RA_MUSTOFFER
    fa_ra = dataclasses.replace(
        fa,
        min_gen=np.maximum(base_min_gen, ra_floor),
        min_gen_mechanism=new_mech,
        pmin=fa.pmin.copy(),
    )
    fa_p2 = apply_commitment_with_coal_pin(
        fa_ra,
        np.ones(ra_floor.shape, dtype=bool),
        p1.dispatch,
        state["fleet"],
        screen_coal=False,
        preserve_min_gen=True,
    )
    ref = solve_dispatch(
        fa_p2, state["demand"], mc=state["mc_bid"], **state["dispatch_kwargs"]
    )

    got = run_commitment_pass(state)
    assert got.status == "Optimal"
    assert np.array_equal(got.dispatch, ref.dispatch)
    assert np.array_equal(got.prices, ref.prices)
    assert "fleet_arrays_p2" in state
    # The stashed P2 bounds carry the RA floor + mechanism ids.
    assert np.array_equal(state["fleet_arrays_p2"].min_gen, fa_p2.min_gen)


def test_config_override_wins_over_state_config():
    """The explicit ``config`` argument overrides ``state['config']`` (run_p2 seam)."""
    base = ScenarioConfig(hours=T, commitment_enabled=True)
    state = _p1_state("CAISO", base)
    # Override flips to the RA branch: commitment off + RA must-offer on.
    override = ScenarioConfig(
        hours=T, commitment_enabled=False, caiso_ra_mustoffer=True
    )
    got = run_commitment_pass(state, override)
    assert got.status == "Optimal"
    # The RA branch (not the economic screen) ran: its stashed P2 arrays carry
    # a raised min_gen floor where the bridge fired, and pmin is a fresh copy.
    assert state["fleet_arrays_p2"].min_gen is not None


def test_nyiso_path_b_wired(monkeypatch):
    """NYISO synchronised-reserve path B reaches reserve_adequacy_commit."""
    config = ScenarioConfig(
        hours=T, commitment_enabled=True, nyiso_synchronised_reserve=True
    )
    state = _p1_state("NYISO", config)
    calls = {}

    def _fake_adequacy(
        committed, fa, fleet, spin_eligible, requirement_mw, headroom_frac
    ):
        calls["requirement_mw"] = requirement_mw
        return committed

    import market_sim.results.scarcity as scarcity

    monkeypatch.setattr(pipeline_commitment, "reserve_adequacy_commit", _fake_adequacy)
    monkeypatch.setattr(
        scarcity,
        "nyiso_spin_eligible",
        lambda fa, zone_names: np.ones(len(fa.pmax), dtype=bool),
    )
    got = run_commitment_pass(state)
    assert got.status == "Optimal"
    assert "requirement_mw" in calls  # path B fired for NYISO


# ---------------------------------------------------------------------------
# P1-native CAISO RA must-offer bridge (P2 archived): the bridge is applied as a
# min_gen floor before the single P1 solve, detected from the P0 run pattern —
# no P2 re-solve. These cover the floor builder and the run_energy_solve hook.
# ---------------------------------------------------------------------------


def _gap_p0_dispatch():
    """P0 dispatch with a 2-hour midday idle gap on the CC (< its 6 h min-down).

    The CC (row 0) runs 0–9 and 12–23, idle 10–11 — a physical restart bar, so
    the plain bridge floors it at min-load across the gap. Row 1 (the peaker CT,
    min-down 1 h) is never bridged.
    """
    p0 = np.zeros((2, T))
    p0[0, :10] = 300.0
    p0[0, 12:] = 300.0
    return p0


def test_caiso_ra_p1_floor_fleet_guards():
    """The P1 floor builder / prep are no-ops off CAISO or with the mechanism off."""
    gens, fa, demand, mc_base, _dk = _trivial_inputs("CAISO")
    p0 = _gap_p0_dispatch()
    prices = np.full((demand.shape[0], T), 40.0)
    on = ScenarioConfig(hours=T, caiso_ra_mustoffer=True)
    off = ScenarioConfig(hours=T, caiso_ra_mustoffer=False)
    # Wrong ISO / mechanism off → None (no floor, ordinary warm-started P1).
    assert caiso_ra_p1_floor_fleet(on, "ERCOT", gens, fa, p0, prices, mc_base) is None
    assert caiso_ra_p1_floor_fleet(off, "CAISO", gens, fa, p0, prices, mc_base) is None
    assert build_caiso_ra_p1_prep(on, "ERCOT", gens, fa, mc_base) is None
    assert build_caiso_ra_p1_prep(off, "CAISO", gens, fa, mc_base) is None
    assert build_caiso_ra_p1_prep(on, "CAISO", gens, fa, mc_base) is not None


def test_caiso_ra_p1_floor_fleet_sets_floor_and_raises_availability():
    """A detected bridge sets the min_gen floor + mechanism id and keeps it feasible."""
    from market_sim.data.floor_mechanisms import MECH_RA_MUSTOFFER

    gens, fa, demand, mc_base, _dk = _trivial_inputs("CAISO")
    p0 = _gap_p0_dispatch()
    prices = np.full((demand.shape[0], T), 40.0)
    config = ScenarioConfig(hours=T, caiso_ra_mustoffer=True)
    floored = caiso_ra_p1_floor_fleet(config, "CAISO", gens, fa, p0, prices, mc_base)
    assert floored is not None
    # The floor is exactly min_load_frac × pmax on the CC across the gap hours.
    expected = config.caiso_ra_min_load_frac * fa.pmax[0]
    assert np.allclose(floored.min_gen[0, 10:12], expected)
    assert floored.min_gen[0, :10].max() == 0.0 and floored.min_gen[0, 12:].max() == 0.0
    assert floored.min_gen[1].max() == 0.0  # the fast-start CT is never bridged
    # Mechanism attribution + feasibility: min_gen ≤ pmax × availability.
    assert np.all(floored.min_gen_mechanism[0, 10:12] == MECH_RA_MUSTOFFER)
    assert np.all(
        floored.min_gen <= floored.availability * floored.pmax[:, None] + 1e-9
    )
    # The input fleet is not mutated.
    assert fa.min_gen is None


def test_run_energy_solve_p1_prep_floors_the_scored_p1():
    """The prep hook makes P1 solve on the floored fleet; the floor binds in P1."""
    gens, fa, demand, mc_base, dk = _trivial_inputs("CAISO")
    config = ScenarioConfig(hours=T, caiso_ra_mustoffer=True)
    prices = np.full((demand.shape[0], T), 40.0)
    p0 = _gap_p0_dispatch()

    # Deterministic prep: floor from the crafted gap pattern, ignoring the LP's
    # own P0 (the trivial constant demand has no midday gap of its own).
    def prep(_r0):
        return caiso_ra_p1_floor_fleet(config, "CAISO", gens, fa, p0, prices, mc_base)

    res = run_energy_solve(gens, fa, demand, mc_base, dk, config, p1_fleet_prep=prep)
    assert res.p1.status == "Optimal"
    # P1 solved on the floored fleet (not the input one), and the floor binds:
    # the CC dispatches at least its min-load across the gap it would otherwise
    # idle through in this cheap-demand hour.
    assert res.p1_fleet_arrays is not fa
    floor = config.caiso_ra_min_load_frac * fa.pmax[0]
    assert np.all(res.p1.dispatch[0, 10:12] >= floor - 1e-6)

    # No hook → the input fleet is used unchanged (ordinary warm-started P1).
    res2 = run_energy_solve(gens, fa, demand, mc_base, dk, config)
    assert res2.p1_fleet_arrays is fa


# ---------------------------------------------------------------------------
# PJM path B — commitment-scoped reserve supply (G-20b)
# ---------------------------------------------------------------------------


def _pjm_mask_inputs():
    """One-zone PJM fleet: slow CC (min-down 6 h), fast CT, coal — 24 hours."""
    gens, fa, demand, mc_base, dk = _trivial_inputs("PJM")
    iso_config = get_iso_config("PJM")
    zone_names = iso_config.zone_names
    gens = gens + [
        Generator(
            unit_id="G2",
            name="coal_base",
            zone=zone_names[0],
            fuel_type="coal",
            pmax_mw=300.0,
            pmin_mw=0.0,
            heat_rate=10.5,
            vom=2.0,
            eford=0.0,
        ),
    ]
    fa = generators_to_fleet_arrays(gens, zone_names, hours=T)
    return gens, fa, demand, mc_base, dk


def test_build_pjm_reserve_p1_prep_guards():
    """(None, None) off-gate / off-ISO / no co-opt; hard error on a stacked path."""
    import pytest

    _gens, fa, _demand, _mc, _dk = _pjm_mask_inputs()
    on = ScenarioConfig(
        hours=T, pjm_reserve_commitment_scoped=True, energy_reserve_coopt=True
    )
    off = ScenarioConfig(hours=T, energy_reserve_coopt=True)
    no_coopt = ScenarioConfig(hours=T, pjm_reserve_commitment_scoped=True)
    assert build_pjm_reserve_p1_prep(off, "PJM", fa) == (None, None)
    assert build_pjm_reserve_p1_prep(on, "ERCOT", fa) == (None, None)
    assert build_pjm_reserve_p1_prep(no_coopt, "PJM", fa) == (None, None)
    fleet_prep, kwargs_prep = build_pjm_reserve_p1_prep(on, "PJM", fa)
    assert fleet_prep is not None and kwargs_prep is not None
    # Path A / pergen stacking is a config error (rule 19, one mechanism).
    for stacked in (
        ScenarioConfig(
            hours=T,
            pjm_reserve_commitment_scoped=True,
            energy_reserve_coopt=True,
            pjm_reserve_online_gated=True,
        ),
        ScenarioConfig(
            hours=T,
            pjm_reserve_commitment_scoped=True,
            energy_reserve_coopt=True,
            pjm_reserve_pergen=True,
        ),
    ):
        with pytest.raises(ValueError):
            build_pjm_reserve_p1_prep(stacked, "PJM", fa)


def test_pjm_commitment_scoped_mask_physics():
    """Slow units mask in offline hours, min-down gaps bridge, fast-start exempt.

    Unit physics (NREL class tables): the heat-rate-7 CC is f-class (min-down
    6 h, startup $48.6/MW) -> gated; the heat-rate-10 CT is frame (min-down
    1 h, startup $24.5/MW) -> fast-start, NEVER masked; coal (min-down 16 h,
    $100/MW) -> gated.
    """
    _gens, fa, _demand, _mc, _dk = _pjm_mask_inputs()
    config = ScenarioConfig(
        hours=T, pjm_reserve_commitment_scoped=True, energy_reserve_coopt=True
    )
    p0 = np.zeros((3, T))
    # CC: online 0-9, off 10-11 (2 h gap < 6 h min-down -> bridged online),
    # online 12-15, offline 16-23 (a real 8 h > 6 h shutdown -> masked).
    p0[0, 0:10] = 400.0
    p0[0, 12:16] = 400.0
    # CT idle all day (fast-start: stays available). Coal offline all day.
    masked = pjm_commitment_scoped_reserve_fleet(config, fa, p0)
    assert masked is not None and masked is not fa
    # CC: full availability through the bridged gap, zeroed in the real gap.
    assert np.all(masked.availability[0, 0:16] == fa.availability[0, 0:16])
    assert np.all(masked.availability[0, 16:] == 0.0)
    # CT (fast-start) untouched everywhere despite idling in P0.
    assert np.array_equal(masked.availability[1], fa.availability[1])
    # Coal offline in P0 all day -> masked all day.
    assert np.all(masked.availability[2] == 0.0)
    # The input fleet is never mutated.
    assert fa.availability.max() > 0.0
    # An all-online pattern masks nothing -> None (ordinary warm-started P1).
    p0_all_on = np.full((3, T), 50.0)
    assert pjm_commitment_scoped_reserve_fleet(config, fa, p0_all_on) is None


def test_pjm_kwargs_prep_recomputes_supply_cap_on_masked_fleet():
    """The P1 supply cap is Σ ramp10 × availability over the MASKED fleet."""
    _gens, fa, _demand, _mc, _dk = _pjm_mask_inputs()
    fa = dataclasses.replace(fa, ramp10=np.array([100.0, 200.0, 30.0]))
    config = ScenarioConfig(
        hours=T,
        pjm_reserve_commitment_scoped=True,
        energy_reserve_coopt=True,
        pjm_reserve_supply_cap=True,
    )
    fleet_prep, kwargs_prep = build_pjm_reserve_p1_prep(config, "PJM", fa)

    class _R0:
        dispatch = np.zeros((3, T))

    _R0.dispatch[0, 0:12] = 400.0  # CC online first half only; CT+coal idle
    p1_fa = fleet_prep(_R0)
    assert p1_fa is not None
    overrides = kwargs_prep(_R0, p1_fa)
    assert set(overrides) == {"reserve_supply_cap"}
    cap = overrides["reserve_supply_cap"]
    assert cap.shape == (1, T)
    # First half: CC (100, online) + CT (200, fast-start, always deliverable);
    # second half (CC masked): CT only. Coal idles all day -> masked, and its
    # 30 MW never enters. All availabilities are 1.0 in the trivial fleet.
    assert np.allclose(cap[0, :12], 300.0)
    assert np.allclose(cap[0, 12:], 200.0)
    # No mask fired -> no override (the design-time cap stands).
    assert kwargs_prep(_R0, fa) is None


def test_run_energy_solve_p1_kwargs_prep_cold_solve_and_merge():
    """A kwargs override rides the P1 solve only; None keeps the warm path."""
    gens, fa, demand, mc_base, dk = _trivial_inputs("PJM")

    calls: list = []

    def kwargs_prep(_r0, _p1_fa):
        calls.append(1)
        return None

    res = run_energy_solve(
        gens,
        fa,
        demand,
        mc_base,
        dk,
        ScenarioConfig(hours=T),
        p1_kwargs_prep=kwargs_prep,
    )
    assert calls and res.p1.status == "Optimal"
    assert res.p1_fleet_arrays is fa

    # An actual override: cap the CT's pmax via a trivially different kwargs
    # dict (T unchanged) — the P1 must re-solve cold and stay optimal, and the
    # P0 result must be identical to the no-hook run (the override is P1-only).
    base = run_energy_solve(gens, fa, demand, mc_base, dk, ScenarioConfig(hours=T))

    def kwargs_prep2(_r0, _p1_fa):
        return {"voll": dk["voll"]}  # same value, but a NEW dict -> cold P1

    res2 = run_energy_solve(
        gens,
        fa,
        demand,
        mc_base,
        dk,
        ScenarioConfig(hours=T),
        p1_kwargs_prep=kwargs_prep2,
    )
    assert res2.p1.status == "Optimal"
    assert np.array_equal(res2.r0.dispatch, base.r0.dispatch)
    np.testing.assert_allclose(res2.p1.dispatch, base.p1.dispatch, atol=1e-9)
    np.testing.assert_allclose(res2.p1.prices, base.p1.prices, atol=1e-9)
