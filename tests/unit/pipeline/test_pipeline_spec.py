"""Unit tests for the Stage-1 solve-core input contracts.

``DispatchSpec.to_dispatch_kwargs`` must reproduce the hand-written base
``dispatch_kwargs`` dict key-for-key (``np.array_equal`` on every array, ``==``
on every scalar), and ``ReserveSpec.merge_into`` must reproduce
``dispatch_kwargs.update(build_reserve_dispatch_kwargs(design))`` exactly — the
neutrality guarantee that Stage 1 changes types, not values.
"""

from __future__ import annotations

import numpy as np

from market_sim.pipeline import DispatchSpec, ReserveSpec


def _fixture_arrays():
    """Small, distinct-valued arrays/scalars mirroring the base kwargs shape."""
    n_zones, n_links, T = 2, 1, 4
    return dict(
        wind_cf=np.arange(n_zones * T, dtype=float).reshape(n_zones, T),
        wind_cap=np.array([100.0, 200.0]),
        solar_cf=np.linspace(0.0, 1.0, n_zones * T).reshape(n_zones, T),
        solar_cap=np.array([50.0, 75.0]),
        voll=2000.0,
        incidence=np.array([[1.0], [-1.0]]),
        ttc=np.full((n_links, T), 500.0),
        interface_groups=None,
        link_bidirectional=np.array([True]),
        storage_power_cap=np.array([10.0]),
        storage_energy_cap=np.array([40.0]),
        storage_zone_idx=np.array([0]),
        eta_chg=np.array([0.9]),
        eta_dis=np.array([0.9]),
        wind_mc=np.array([-1.0, -1.0]),
        solar_mc=np.array([0.0, 0.0]),
        storage_discharge_eac=None,
        storage_discharge_cost=np.array([0.5]),
        rps_target=None,
        storage_daily_cycle_hours=24,
        hydro_gen_idx=None,
        hydro_monthly_energy=None,
        T=T,
    )


def test_dispatch_spec_to_kwargs_matches_hand_written_dict():
    """``to_dispatch_kwargs()`` equals the inline dict, key-for-key."""
    kw = _fixture_arrays()
    spec = DispatchSpec(**kw)
    # Hand-written dict exactly as runner.py assembles it inline.
    expected = dict(
        wind_cf=kw["wind_cf"],
        wind_cap=kw["wind_cap"],
        solar_cf=kw["solar_cf"],
        solar_cap=kw["solar_cap"],
        voll=kw["voll"],
        incidence=kw["incidence"],
        ttc=kw["ttc"],
        interface_groups=kw["interface_groups"] or None,
        link_bidirectional=kw["link_bidirectional"],
        storage_power_cap=kw["storage_power_cap"],
        storage_energy_cap=kw["storage_energy_cap"],
        storage_zone_idx=kw["storage_zone_idx"],
        eta_chg=kw["eta_chg"],
        eta_dis=kw["eta_dis"],
        wind_mc=kw["wind_mc"],
        solar_mc=kw["solar_mc"],
        storage_discharge_eac=kw["storage_discharge_eac"],
        storage_discharge_cost=kw["storage_discharge_cost"],
        rps_target=kw["rps_target"],
        storage_daily_cycle_hours=kw["storage_daily_cycle_hours"],
        hydro_gen_idx=kw["hydro_gen_idx"],
        hydro_monthly_energy=kw["hydro_monthly_energy"],
        T=kw["T"],
    )
    got = spec.to_dispatch_kwargs()

    # Same key set, in the same order (dict insertion order).
    assert list(got) == list(expected)
    for key in expected:
        e, g = expected[key], got[key]
        if isinstance(e, np.ndarray):
            assert isinstance(g, np.ndarray), key
            assert np.array_equal(e, g), key
        else:
            assert e == g, key


def test_dispatch_spec_identity_of_stored_arrays():
    """The container holds the same array objects it was given (no copy)."""
    kw = _fixture_arrays()
    spec = DispatchSpec(**kw)
    got = spec.to_dispatch_kwargs()
    assert got["wind_cf"] is kw["wind_cf"]
    assert got["storage_power_cap"] is kw["storage_power_cap"]


def _reserve_kwargs_multi():
    """A representative multi-family reserve kwargs dict (a superset of keys)."""
    return dict(
        reserve_requirement=np.array([[3.0, 3.0], [1.0, 1.0]]),
        reserve_eligible=np.array([[True, False, True], [True, True, False]]),
        ordc_penalties=np.array([100.0, 50.0]),
        ordc_step_widths=np.array([10.0, 20.0]),
        reserve_balance_zone_mask=np.array([[True, False], [False, True]]),
        reserve_balance_ordc_counts=np.array([1, 1]),
        reserve_balance_class=np.array([0, 1]),
        reserve_supply_cap=np.array([500.0, 400.0]),
        reserve_online_gated=np.array([True, False, True]),
        reserve_online_rho=0.5,
        reserve_pergen_gen_idx=np.array([0, 2]),
        reserve_pergen_ramp10=np.array([25.0, 30.0]),
    )


def test_reserve_spec_merge_into_matches_dict_update():
    """``merge_into`` reproduces ``dispatch_kwargs.update(reserve_kwargs)``."""
    rk = _reserve_kwargs_multi()
    base = {"wind_cf": np.zeros(3), "T": 8760}

    # Reference: the current inline behaviour.
    reference = dict(base)
    reference.update(rk)

    # Under test: wrap the exact dict and merge.
    got = dict(base)
    ReserveSpec.from_reserve_kwargs(rk).merge_into(got)

    assert set(got) == set(reference)
    for key in reference:
        e, g = reference[key], got[key]
        if isinstance(e, np.ndarray):
            assert np.array_equal(e, g), key
        else:
            assert e == g, key


def test_reserve_spec_absent_keys_not_injected():
    """A minimal design injects only its keys — absent ones stay absent."""
    minimal = dict(
        reserve_requirement=np.array([2.0, 2.0]),
        reserve_eligible=np.array([True, False]),
        ordc_penalties=np.array([100.0]),
        ordc_step_widths=np.array([10.0]),
    )
    spec = ReserveSpec.from_reserve_kwargs(minimal)
    got: dict = {}
    spec.merge_into(got)
    assert set(got) == set(minimal)
    # Keys the design did not emit must NOT appear (would change the LP).
    assert "reserve_supply_cap" not in got
    assert "reserve_online_gated" not in got
    # And the typed accessor returns None for them (dict.get semantics).
    assert spec.reserve_supply_cap is None
    assert spec.reserve_online_gated is None


def test_reserve_spec_typed_accessors():
    """Typed accessors return the wrapped values verbatim."""
    rk = _reserve_kwargs_multi()
    spec = ReserveSpec.from_reserve_kwargs(rk)
    assert np.array_equal(spec.reserve_requirement, rk["reserve_requirement"])
    assert np.array_equal(spec.reserve_supply_cap, rk["reserve_supply_cap"])
    assert spec.reserve_online_rho == rk["reserve_online_rho"]
    assert np.array_equal(spec.reserve_pergen_ramp10, rk["reserve_pergen_ramp10"])


def test_reserve_spec_defensive_copy():
    """Mutating the source dict after wrapping does not alter the contract."""
    rk = _reserve_kwargs_multi()
    spec = ReserveSpec.from_reserve_kwargs(rk)
    rk["reserve_online_rho"] = 999.0
    assert spec.reserve_online_rho == 0.5
