"""SPP spinning share: a synchronized reserve class is carried by COMMITTED headroom.

1 zone / 24 h (lane UC-SPP-SPIN, owner ruling r13). Fleet: a cheap baseload
row (60 MW), a steam-gas plant that is the one integer cluster (2 x 100 MW,
min-stable 0.5, a positive no-load) and a fast-start CT (150 MW). Night load
(80 MW) is cheaper to serve with baseload + CT than by starting the steam
unit, so with the pooled Contingency Reserve family alone (80 MW) the CT's
OFFLINE 150 MW covers the whole requirement and the steam unit stays off at
night. Adding the >= 1/2 Spinning sub-requirement (40 MW, synchronized) makes
the steam unit's committed headroom carry it: u >= 1 every hour.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.reserves.spec import (
    SPP_RSG_SPIN_MIN_SHARE,
    SPP_SPINNING_RESERVE_VRL,
    ReserveDesign,
    ReserveFamily,
    _spp_design,
    build_reserve_dispatch_kwargs,
)
from market_sim.model.uc.params import build_uc_cluster_params
from market_sim.model.uc.solve import UcSolveOptions, solve_window
from market_sim.model.uc.window import UcWindowModel, WindowState, slice_window_inputs
from market_sim.pipeline.uc import synchronized_reserve_overrides

T = 24
OPTS = UcSolveOptions(mip_rel_gap=1e-6, time_limit_s=60.0)
#: Pooled-family shortfall price far above any energy cost (met when it can be).
PENALTY = 1000.0
REQ = 80.0
ST, NUC, CT = 0, 1, 2


def _generators() -> list[Generator]:
    def gen(uid, fuel, pmax, pc, group):
        return Generator(
            unit_id=uid,
            name=uid.lower(),
            zone="Z0",
            fuel_type=fuel,
            pmax_mw=pmax,
            pmin_mw=0.0,
            heat_rate=10.0,
            vom=1.0,
            eford=0.0,
            plant_code=pc,
            plant_group=group,
        )

    return [
        gen("ST1", "gas_st", 200.0, 1, "ST_GAS"),
        gen("NUC", "nuclear", 60.0, 9, "NUCLEAR"),
        gen("CT1", "gas_ct", 150.0, 2, "CT_PEAKER"),
    ]


@pytest.fixture
def st_params_frame(monkeypatch):
    """The steam plant's ``uc-params`` row (2 x 100 MW, mlf 0.5)."""
    import market_sim.model.uc.params as ucp

    frame = pd.DataFrame(
        [
            dict(
                plant_code=1,
                uc_class="st_gas",
                n_units=2,
                hsl_mw=200.0,
                lsl_mw=100.0,
                mlf=0.5,
                ut_h=6,
                dt_h=4,
                noload_mmbtu_h=100.0,
                noload_units_fitted=2,
                noload_r2_median=0.99,
                online_frac=0.7,
                n_runs=100,
                years="2023-2025",
                source="toy",
            )
        ]
    )
    monkeypatch.setattr(ucp, "load_uc_params_frame", lambda iso: frame)


def _inputs():
    fa = generators_to_fleet_arrays(_generators(), ["Z0"], hours=T)
    demand = np.full((1, T), 150.0)
    demand[0, :7] = 80.0
    mc = np.vstack([np.full(T, 25.0), np.full(T, 5.0), np.full(T, 60.0)])
    dk = dict(
        wind_cf=np.zeros((1, T)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, T)),
        solar_cap=np.zeros(1),
        voll=5000.0,
    )
    return fa, demand, mc, dk


def _design(spin: bool) -> ReserveDesign:
    elig = np.ones(3, dtype=bool)
    fams = [
        ReserveFamily(
            name="cr",
            requirement=np.full(T, REQ),
            zone_mask=np.ones(1, dtype=bool),
            ordc_penalties=np.array([PENALTY]),
            ordc_step_widths=np.array([REQ]),
            reserve_class=0,
        )
    ]
    if not spin:
        return ReserveDesign(families=fams, eligible=elig.reshape(1, -1))
    spin_req = SPP_RSG_SPIN_MIN_SHARE * REQ
    fams.append(
        ReserveFamily(
            name="spin",
            requirement=np.full(T, spin_req),
            zone_mask=np.ones(1, dtype=bool),
            ordc_penalties=np.array([PENALTY]),
            ordc_step_widths=np.array([spin_req]),
            reserve_class=1,
        )
    )
    return ReserveDesign(
        families=fams,
        eligible=np.vstack([elig, elig]),
        synchronized=np.array([False, True]),
    )


def _solve(spin: bool):
    fa, demand, mc, dk = _inputs()
    params = build_uc_cluster_params(fa, "SPP")
    kw = {**dk, **build_reserve_dispatch_kwargs(_design(spin))}
    kw = {**kw, **synchronized_reserve_overrides(kw, params)}
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
    w = UcWindowModel(inputs, params, mc, np.full((n_int, T), 200.0), state)
    res = solve_window(w, OPTS)
    lay = w.layout
    block = res.col_value[: w.n_lp].reshape(T, lay.vars_per_hour)
    r = block[:, lay._reserve_off : lay._reserve_off + lay.n_reserve]
    return params, kw, w, res, r


def test_steam_is_the_integer_cluster(st_params_frame):
    fa, *_ = _inputs()
    p = build_uc_cluster_params(fa, "SPP")
    assert p.integer_clusters.size == 1
    assert list(p.integer_member_gens) == [ST]


def test_overrides_restrict_synchronized_class_to_integer_members(st_params_frame):
    fa, _, _, dk = _inputs()
    p = build_uc_cluster_params(fa, "SPP")
    kw = {**dk, **build_reserve_dispatch_kwargs(_design(True))}
    elig = synchronized_reserve_overrides(kw, p)["reserve_eligible"]
    assert elig[0].tolist() == [True, True, True]  # pooled: CT offline counts
    assert elig[1].tolist() == [True, False, False]  # spin: committed ST only
    # No synchronized class -> no override (the stage keeps the caller's dict).
    assert (
        synchronized_reserve_overrides(
            {**dk, **build_reserve_dispatch_kwargs(_design(False))}, p
        )
        == {}
    )


def test_without_spin_offline_ct_covers_everything(st_params_frame):
    _, _, w, res, r = _solve(spin=False)
    assert res.status == "Optimal"
    assert (res.u[0, :7] == 0).all()  # steam off at night
    np.testing.assert_allclose(r.sum(axis=1), REQ, atol=1e-6)


def test_spin_share_forces_steam_headroom(st_params_frame):
    _, _, w, res, r = _solve(spin=True)
    assert res.status == "Optimal"
    assert (res.u[0, :] >= 1).all()  # committed every hour, night included
    n_z = w.layout.n_zones
    spin = r[:, n_z : 2 * n_z].sum(axis=1)
    pooled = r[:, :n_z].sum(axis=1)
    np.testing.assert_allclose(spin, SPP_RSG_SPIN_MIN_SHARE * REQ, atol=1e-6)
    np.testing.assert_allclose(pooled, REQ, atol=1e-6)
    # Spin <= committed steam capacity - steam output, every hour.
    st = res.dispatch[ST]
    assert np.all(spin <= 100.0 * res.u[0] - st + 1e-6)
    assert w.n_reserve_gated_rows == 2 * T  # both classes' ST entries u-gated


class _Fleet:
    """Minimal fleet stub for the SPP design (two >= 600 MW units)."""

    def __init__(self):
        self.pmax = np.array([800.0, 700.0, 100.0])
        self.availability = np.ones((3, T))
        self.plant_code = np.array([1, 2, 3])
        self.zone_idx = np.zeros(3, dtype=int)
        from market_sim.data.fleet import FUEL_TYPE_NAMES

        st = FUEL_TYPE_NAMES.index("gas_st")
        ct = FUEL_TYPE_NAMES.index("gas_ct")
        self.fuel_type_idx = np.array([st, st, ct])


class _Cfg:
    def __init__(self, spin, uc):
        self.iso = "SPP"
        self.spp_spinning_reserve_share = spin
        self.unit_commitment_milp = uc


def test_spp_design_off_is_one_family():
    d = _spp_design(_Cfg(False, True), _Fleet(), T, largest_unit_mw={})
    assert len(d.families) == 1 and d.synchronized is None
    assert "reserve_synchronized" not in build_reserve_dispatch_kwargs(d)


def test_spp_design_spin_family():
    d = _spp_design(_Cfg(True, True), _Fleet(), T, largest_unit_mw={})
    cr, sp = d.families
    np.testing.assert_allclose(sp.requirement, SPP_RSG_SPIN_MIN_SHARE * cr.requirement)
    assert sp.reserve_class == 1
    np.testing.assert_allclose(sp.ordc_penalties, [SPP_SPINNING_RESERVE_VRL])
    np.testing.assert_allclose(sp.ordc_step_widths, [sp.requirement.max()])
    assert d.eligible.shape == (2, 3)
    assert d.synchronized.tolist() == [False, True]
    kw = build_reserve_dispatch_kwargs(d)
    assert kw["reserve_synchronized"].tolist() == [False, True]
    assert kw["reserve_balance_class"].tolist() == [0, 1]


def test_spp_design_spin_refused_without_uc():
    with pytest.raises(ValueError, match="unit_commitment_milp"):
        _spp_design(_Cfg(True, False), _Fleet(), T, largest_unit_mw={})
