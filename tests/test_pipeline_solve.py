"""Trivial-case tests for the Stage-3 shared P0/P1 solve (pipeline/solve.py).

CLAUDE.md testing pattern: 1 zone, 2 generators, 24 hours. The shared
``run_energy_solve`` must reproduce the exact inline sequence both
orchestrators ran (P0 base-cost → monthly markup → P1 bid-cost), including the
warm/cold env gate and the cross-year cache seam.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.commitment import compute_monthly_markup
from market_sim.model.dispatch import solve_dispatch
from market_sim.pipeline.solve import EnergySolveResult, run_energy_solve

T = 24


class _Cfg:
    """Minimal config stub with the fields run_energy_solve reads."""

    hours = T
    gas_st_startup_spread = False
    gas_st_startup_cost = False
    chp_startup_covered = False
    coal_warm_committed = False


def _trivial_inputs():
    """One-zone ERCOT-topology fleet: cheap CC + expensive CT, 24 hours."""
    iso_config = get_iso_config("ERCOT")
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
    # Peaky hour so the CT runs some hours and the markup has a run to amortize.
    demand[0, 18] = 550.0
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
        T=T,
    )
    return generators, fleet_arrays, demand, mc_base, dispatch_kwargs


def _reference_inline_solve(generators, fleet_arrays, demand, mc_base, dk):
    """The pre-Stage-3 inline sequence, cold solves (the reference)."""
    r0 = solve_dispatch(fleet_arrays, demand, mc=mc_base, **dk)
    markup = compute_monthly_markup(generators, fleet_arrays, r0.dispatch, T)
    mc_bid = mc_base + markup
    p1 = solve_dispatch(fleet_arrays, demand, mc=mc_bid, **dk)
    return r0, p1, mc_bid


def test_run_energy_solve_matches_inline_sequence_cold(monkeypatch):
    """Cold path (WARMSTART=0): byte-identical to the inline two-solve."""
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "0")
    gens, fa, demand, mc_base, dk = _trivial_inputs()
    ref_r0, ref_p1, ref_mc_bid = _reference_inline_solve(gens, fa, demand, mc_base, dk)

    got = run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg())
    assert isinstance(got, EnergySolveResult)
    assert got.p1.status == "Optimal"
    assert np.array_equal(got.mc_bid, ref_mc_bid)
    assert np.array_equal(got.r0.dispatch, ref_r0.dispatch)
    assert np.array_equal(got.p1.dispatch, ref_p1.dispatch)
    assert np.array_equal(got.p1.prices, ref_p1.prices)


def test_run_energy_solve_warm_equals_cold_on_unique_optimum(monkeypatch):
    """Warm path: same prices/dispatch as cold on a tie-free trivial LP."""
    gens, fa, demand, mc_base, dk = _trivial_inputs()
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "0")
    cold = run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg())
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
    warm = run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg())
    assert warm.p1.status == "Optimal"
    np.testing.assert_allclose(warm.p1.dispatch, cold.p1.dispatch, atol=1e-9)
    np.testing.assert_allclose(warm.p1.prices, cold.p1.prices, atol=1e-9)


def test_xyear_cache_export_backcast_seam(monkeypatch):
    """Backcast seam: with a cache list the warm path exports this year's basis."""
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
    monkeypatch.delenv("MARKET_SIM_WARMSTART_XYEAR", raising=False)
    gens, fa, demand, mc_base, dk = _trivial_inputs()
    cache: list = []
    run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg(), xyear_cache=cache)
    # The basis is stored even with the XYEAR flag off (A/B independence),
    # exactly as the inline backcast code did.
    assert len(cache) == 1


def test_xyear_cache_none_forecast_seam(monkeypatch):
    """Forecast seam: xyear_cache=None → no export, no error (plan §8)."""
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
    gens, fa, demand, mc_base, dk = _trivial_inputs()
    got = run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg(), xyear_cache=None)
    assert got.p1.status == "Optimal"


def test_cold_path_skips_model_and_cache(monkeypatch):
    """WARMSTART=0 never builds the model, so no basis export happens."""
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "0")
    gens, fa, demand, mc_base, dk = _trivial_inputs()
    cache: list = []
    run_energy_solve(gens, fa, demand, mc_base, dk, _Cfg(), xyear_cache=cache)
    assert cache == []
