"""Unit tests for the Stage-2 shared kwargs assembly (pipeline/kwargs.py).

The Stage-2 acceptance contract (orchestrator-unification plan §7.1 item 2):
the shared core's ``dispatch_kwargs`` must equal each orchestrator's
pre-refactor inline dict key-for-key (``np.array_equal`` on every array, ``==``
on every scalar) — the forecast shape (no ``ttc_import``/``oil_*`` keys) and
the backcast shape (those keys always present, possibly ``None``-valued) both.
Plus the A5 trivial case: the ERCOT single-product design now carries the
reserve-supply cap and threads the forward drivers to it.
"""

from __future__ import annotations

import numpy as np

from market_sim.pipeline import (
    DispatchSpec,
    apply_reserve_coopt,
    build_base_dispatch_kwargs,
)


def _base_fixture():
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


def _assert_kwargs_equal(got: dict, expected: dict) -> None:
    assert set(got) == set(expected)
    for key in expected:
        e, g = expected[key], got[key]
        if isinstance(e, np.ndarray):
            assert isinstance(g, np.ndarray), key
            assert np.array_equal(e, g), key
        else:
            assert e == g, key


def test_forecast_shape_matches_runner_inline_dict():
    """Runner shape: exactly the base keys — no ttc_import, no oil_* keys."""
    kw = _base_fixture()
    got = build_base_dispatch_kwargs(DispatchSpec(**kw))
    _assert_kwargs_equal(got, kw)
    for absent in (
        "ttc_import",
        "oil_monthly_budget",
        "oil_gen_idx",
        "oil_month_index",
        "oil_gen_hour_coeff",
        "oil_group_index",
        "import_node_gen_idx",
    ):
        assert absent not in got


def test_backcast_shape_matches_calibration_inline_dict():
    """Backcast shape: ttc_import + oil_* keys present even when None-valued."""
    kw = _base_fixture()
    oil_idx = np.array([1])
    backcast = dict(
        kw,
        ttc_import=None,
        oil_monthly_budget=np.array([np.inf, 100.0]),
        oil_gen_idx=oil_idx,
        oil_month_index=None,
        oil_gen_hour_coeff=None,
        oil_group_index=None,
    )
    got = build_base_dispatch_kwargs(DispatchSpec(**backcast))
    _assert_kwargs_equal(got, backcast)
    assert "ttc_import" in got and got["ttc_import"] is None
    assert got["oil_gen_idx"] is oil_idx


def test_import_node_recon_updates_exactly_three_keys():
    """The reconciliation band adds its three keys; None adds nothing."""
    kw = _base_fixture()
    node_idx = np.array([3, 4])
    lo, hi = np.array([-10.0]), np.array([25.0])
    got = build_base_dispatch_kwargs(
        DispatchSpec(**kw), import_node_recon=(node_idx, lo, hi)
    )
    assert got["import_node_gen_idx"] is node_idx
    assert got["import_node_monthly_lo"] is lo
    assert got["import_node_monthly_hi"] is hi
    assert set(got) == set(kw) | {
        "import_node_gen_idx",
        "import_node_monthly_lo",
        "import_node_monthly_hi",
    }


class _Cfg:
    """Minimal attribute-bag config stub (getattr-with-default compatible)."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_apply_reserve_coopt_gated_off_is_noop():
    """energy_reserve_coopt off → None returned, dict untouched."""
    dk = {"T": 4}
    design = apply_reserve_coopt(
        dk, _Cfg(iso="PJM", energy_reserve_coopt=False), None, 4, ["A"]
    )
    assert design is None
    assert dk == {"T": 4}


def test_apply_reserve_coopt_caiso_excluded():
    """CAISO has no reserve design — excluded exactly as both inline blocks."""
    dk = {"T": 4}
    design = apply_reserve_coopt(
        dk, _Cfg(iso="CAISO", energy_reserve_coopt=True), None, 4, ["Z1"]
    )
    assert design is None
    assert dk == {"T": 4}


def test_apply_reserve_coopt_merges_design_kwargs_and_threads_drivers(monkeypatch):
    """The wrapper forwards the drivers and merges the design's exact key set."""
    import market_sim.config.reserve_config as rcfg

    seen = {}
    fake_kw = dict(
        reserve_requirement=np.array([5.0, 5.0]),
        reserve_eligible=np.array([True]),
        ordc_penalties=np.array([100.0]),
        ordc_step_widths=np.array([5.0]),
    )

    class _FakeDesign:
        families = []
        supply_cap = None
        online_gated = None
        online_rho = 1.0
        pergen_gen_idx = None
        pergen_ramp10 = None

    def fake_get_reserve_design(config, fleet_arrays, hours, zone_names, **drv):
        seen.update(drv, hours=hours, zone_names=zone_names)
        return _FakeDesign()

    monkeypatch.setattr(rcfg, "get_reserve_design", fake_get_reserve_design)
    monkeypatch.setattr(
        rcfg, "build_reserve_dispatch_kwargs", lambda design: dict(fake_kw)
    )

    dk = {"T": 2}
    sysload = np.array([10.0, 12.0])
    wind = np.array([1.0, 2.0])
    solar = np.array([0.5, 0.0])
    design = apply_reserve_coopt(
        dk,
        _Cfg(iso="NEISO", energy_reserve_coopt=True),
        None,
        2,
        ["Z1"],
        system_load=sysload,
        wind_gen=wind,
        solar_gen=solar,
        sim_year=2024,
    )
    assert design is not None
    assert seen["system_load"] is sysload
    assert seen["wind_gen"] is wind
    assert seen["solar_gen"] is solar
    assert seen["sim_year"] == 2024
    # Exact conditional key set merged — nothing extra injected.
    assert set(dk) == {"T"} | set(fake_kw)
    for key, val in fake_kw.items():
        assert np.array_equal(dk[key], val)


# ---------------------------------------------------------------------------
# A5 trivial case: ERCOT single-product design now carries the supply cap.
# ---------------------------------------------------------------------------


def _tiny_fleet_arrays():
    """One-generator fleet stub sufficient for _reserve_eligible / zone count."""

    class _FA:
        fuel_type_idx = np.array([0])
        zone_idx = np.array([0])

    return _FA()


def test_a5_ercot_single_product_design_sets_supply_cap(monkeypatch):
    """A5 fold: _ercot_design threads the drivers into the RTOLCAP supply cap.

    Previously only the multiproduct design set ``supply_cap`` — the forecast
    single-product ERCOT co-opt ran uncapped, and the backcast reached the cap
    only through run_calibration's post-design overwrite (now retired).
    """
    import market_sim.config.reserve_config as rcfg
    import market_sim.results.scarcity as scarcity

    T = 4
    cap = np.full((1, T), 4321.0)
    seen = {}

    def fake_rtolcap(
        config,
        hours,
        fleet_arrays=None,
        *,
        system_load=None,
        wind_gen=None,
        solar_gen=None,
    ):
        seen.update(
            fleet_arrays=fleet_arrays,
            system_load=system_load,
            wind_gen=wind_gen,
            solar_gen=solar_gen,
        )
        return cap

    monkeypatch.setattr(scarcity, "ercot_rtolcap_supply_cap_mw", fake_rtolcap)
    monkeypatch.setattr(
        scarcity, "resolve_lolp_params", lambda config, hours: (np.zeros(2), np.ones(2))
    )
    monkeypatch.setattr(
        scarcity,
        "ercot_ordc_demand_steps",
        lambda **kw: (3000.0, np.array([500.0]), np.array([3000.0])),
    )

    fa = _tiny_fleet_arrays()
    cfg = _Cfg(
        iso="ERCOT",
        energy_reserve_coopt=True,
        ercot_multiproduct_as_coopt=False,
        ordc_voll=5000.0,
        ordc_mcl_mw=2000.0,
        ordc_lolp_shift_sigma=0.0,
        ordc_multistep_floor=0.0,
        weather_year=2023,
        mode="backcast",
    )
    sysload = np.arange(T, dtype=float)
    wind = np.ones(T)
    solar = np.zeros(T)

    design = rcfg.get_reserve_design(
        cfg,
        fa,
        T,
        ["ERCOT"],
        system_load=sysload,
        wind_gen=wind,
        solar_gen=solar,
        sim_year=2023,
    )
    # The single-product design now carries the cap (A5)…
    assert design.supply_cap is cap
    # …built from the threaded forward drivers…
    assert seen["fleet_arrays"] is fa
    assert seen["system_load"] is sysload
    assert seen["wind_gen"] is wind
    assert seen["solar_gen"] is solar
    # …and the kwargs builder emits it to the LP.
    kw = rcfg.build_reserve_dispatch_kwargs(design)
    assert np.array_equal(kw["reserve_supply_cap"], cap)


def test_a5_supply_cap_absent_when_gated_off(monkeypatch):
    """When scarcity returns None (gate off) the design stays uncapped."""
    import market_sim.config.reserve_config as rcfg
    import market_sim.results.scarcity as scarcity

    monkeypatch.setattr(scarcity, "ercot_rtolcap_supply_cap_mw", lambda *a, **k: None)
    monkeypatch.setattr(
        scarcity, "resolve_lolp_params", lambda config, hours: (np.zeros(2), np.ones(2))
    )
    monkeypatch.setattr(
        scarcity,
        "ercot_ordc_demand_steps",
        lambda **kw: (3000.0, np.array([500.0]), np.array([3000.0])),
    )
    cfg = _Cfg(
        iso="ERCOT",
        energy_reserve_coopt=True,
        ercot_multiproduct_as_coopt=False,
        ordc_voll=5000.0,
        ordc_mcl_mw=2000.0,
        ordc_lolp_shift_sigma=0.0,
        ordc_multistep_floor=0.0,
        weather_year=2023,
        mode="backcast",
    )
    design = rcfg.get_reserve_design(cfg, _tiny_fleet_arrays(), 4, ["ERCOT"])
    assert design.supply_cap is None
    assert "reserve_supply_cap" not in rcfg.build_reserve_dispatch_kwargs(design)
