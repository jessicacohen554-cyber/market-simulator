"""NWPP per-BA BAL-002-WECC contingency reserve (nwpp_ba_contingency_reserve).

Design shape (families, masks, requirement arithmetic, hydro ramp backfill),
the refusals that keep the key from running silently inert or in a forecast,
and the LP semantics at trivial scale (1 zone, a CC and a CT, 4 hours): the
online-gated spinning half forces an energy-loaded CC to open headroom.
"""

from types import SimpleNamespace

import numpy as np
import pytest

from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.reserves.spec import (
    BAL002_WECC_SPIN_SHARE,
    NWPP_HYDRO_RAMP10_FRAC,
    _nwpp_design,
    build_reserve_dispatch_kwargs,
    get_reserve_design,
)
from market_sim.pipeline.kwargs import apply_reserve_coopt

T = 4
ZONES = ["NWPP-NW", "NWPP-SNV", "NWPP_ext_COI"]


def _fleet(zone_idx, fuels, pmax, ramp10, heat_rate=None):
    n = len(fuels)
    return FleetArrays(
        pmax=np.asarray(pmax, dtype=float),
        pmin=np.zeros(n),
        heat_rate=np.asarray(heat_rate if heat_rate is not None else [7.0] * n, float),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.asarray(zone_idx, dtype=int),
        fuel_type_idx=np.array([FUEL_TYPE_NAMES.index(f) for f in fuels]),
        availability=np.ones((n, T)),
        unit_ids=[f"u{i}" for i in range(n)],
        efficiency_bin=np.zeros(n),
        plant_code=np.arange(1, n + 1),
        ramp10=np.asarray(ramp10, dtype=float),
    )


def _config(**kw):
    base = dict(
        iso="NWPP",
        voll=2000.0,
        mode="backcast",
        weather_year=2024,
        nwpp_ba_contingency_reserve=True,
        energy_reserve_coopt=True,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _basis(load_mw, gen_mw):
    load = np.zeros((len(ZONES), T))
    gen = np.zeros((len(ZONES), T))
    for z, v in load_mw.items():
        load[ZONES.index(z)] = v
    for z, v in gen_mw.items():
        gen[ZONES.index(z)] = v
    return load, gen


def test_design_families_masks_and_requirement():
    fa = _fleet(
        zone_idx=[0, 1, 1, 2],
        fuels=["hydro", "gas_cc", "gas_ct", "oil"],
        pmax=[1000.0, 500.0, 100.0, 50.0],
        ramp10=[0.0, 200.0, 100.0, 50.0],
    )
    design = _nwpp_design(
        _config(),
        fa,
        T,
        ZONES,
        basis_mw=_basis({"NWPP-NW": 10000.0, "NWPP-SNV": 3000.0}, {"NWPP-SNV": 2000.0}),
    )
    names = [f.name for f in design.families]
    # The external seam node carries no member BA: no family.
    assert names == [
        "nwpp_NWPP-NW_contingency",
        "nwpp_NWPP-NW_spin",
        "nwpp_NWPP-SNV_contingency",
        "nwpp_NWPP-SNV_spin",
    ]
    req = {f.name: f.requirement for f in design.families}
    np.testing.assert_allclose(
        req["nwpp_NWPP-SNV_contingency"], 0.03 * 3000 + 0.03 * 2000
    )
    np.testing.assert_allclose(
        req["nwpp_NWPP-SNV_spin"], BAL002_WECC_SPIN_SHARE * (0.03 * 5000)
    )
    for f in design.families:
        np.testing.assert_allclose(f.ordc_penalties, [2000.0])  # the region's voll
        assert f.ordc_step_widths[0] == pytest.approx(f.requirement.max())
    # Hydro backfilled to full nameplate inside the 10-minute window.
    n_r = int(design.pergen_col.max()) + 1
    hydro_pool = int(design.pergen_col[list(design.pergen_gen_idx).index(0)])
    assert design.pergen_pool_ramp10[hydro_pool, 0] == pytest.approx(
        NWPP_HYDRO_RAMP10_FRAC * 1000.0
    )
    # Columns [0, n_r) gated spin, [n_r, 2 n_r) ungated offline.
    np.testing.assert_array_equal(
        design.pergen_online_gated_cols, np.r_[np.ones(n_r, bool), np.zeros(n_r, bool)]
    )
    cc_pool = int(design.pergen_col[list(design.pergen_gen_idx).index(1)])
    ct_pool = int(design.pergen_col[list(design.pergen_gen_idx).index(2)])
    snv_cont = design.balance_col_mask[names.index("nwpp_NWPP-SNV_contingency")]
    snv_spin = design.balance_col_mask[names.index("nwpp_NWPP-SNV_spin")]
    assert snv_cont[cc_pool] and snv_cont[ct_pool]  # spinning from both
    assert snv_cont[n_r + ct_pool] and not snv_cont[n_r + cc_pool]  # offline: CT only
    assert snv_spin[cc_pool] and snv_spin[ct_pool] and not snv_spin[n_r:].any()
    assert not snv_cont[hydro_pool]  # NW hydro never backs SNV
    assert 0.0 < design.online_rho < 1.0  # the measured NWPP statistic


def test_refusals():
    fa = _fleet([1], ["gas_cc"], [500.0], [200.0])
    with pytest.raises(ValueError, match="mode"):
        _nwpp_design(_config(mode="forecast"), fa, T, ZONES, basis_mw=_basis({}, {}))
    with pytest.raises(ValueError, match="no reserve design unless"):
        get_reserve_design(_config(nwpp_ba_contingency_reserve=False), fa, T, ZONES)
    with pytest.raises(ValueError, match="requires energy_reserve_coopt"):
        apply_reserve_coopt({}, _config(energy_reserve_coopt=False), fa, T, ZONES)
    with pytest.raises(ValueError, match="NWPP-only"):
        apply_reserve_coopt({}, _config(iso="SPP"), fa, T, ZONES)


def test_spinning_half_opens_cc_headroom():
    # One SNV zone: a cheap 400 MW CC and a dear 100 MW CT, demand 400 MW.
    # Energy-only, the CC runs at its cap. A 40 MW contingency requirement
    # (20 MW spinning) at rho 0.213 needs >= 20 MW of ONLINE headroom; the
    # offline CT can carry the non-spinning 20 MW but no spin, so the CC (or
    # a running CT) must open headroom: CC + CT energy = 400 with CC < 400.
    zones = ["NWPP-SNV"]
    fa = _fleet(
        [0, 0], ["gas_cc", "gas_ct"], [400.0, 100.0], [160.0, 100.0], [7.0, 10.0]
    )
    load = np.full((1, T), 600.0)
    gen = np.full((1, T), 733.3333333333334)  # 0.03 x (600 + 733.3) = 40 MW
    design = _nwpp_design(_config(), fa, T, zones, basis_mw=(load, gen))
    kw = build_reserve_dispatch_kwargs(design)
    r = solve_dispatch(
        fa,
        np.full((1, T), 400.0),
        wind_cf=np.zeros((1, T)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, T)),
        solar_cap=np.zeros(1),
        fuel_prices=np.full((2, T), 1.0),
        voll=2000.0,
        **kw,
    )
    assert r.status == "Optimal"
    d = np.asarray(r.dispatch)
    # The CC opens headroom; a CT run up alongside backs rho x its output.
    rho = design.online_rho
    spin = (400.0 - d[0]) + np.minimum(100.0 - d[1], rho * d[1])
    assert np.all(d[0] < 400.0 - 1.0), d[0]
    assert np.all(spin >= 20.0 - 1e-4), spin
    np.testing.assert_allclose(d.sum(axis=0), 400.0, atol=1e-4)
    # Requirement met (no $2,000 shortfall): the reserve price is the CT-CC
    # opportunity cost, far below voll.
    assert float(np.asarray(r.reserve_price).max()) < 100.0


def test_idle_plant_backs_no_spin_for_a_loaded_one():
    # Two CC plants in one zone: plant 1 cheap and loaded to its cap by the
    # 400 MW demand, plant 2 dearer and idle. Pooled by (zone, fuel-class),
    # plant 2's idle 400 MW sat in the same joint row as plant 1's output and
    # backed the spin for free (the NEXT-28 inert legs). Per plant, the 20 MW
    # spin needs ONLINE headroom: plant 1 opens it or plant 2 runs.
    zones = ["NWPP-SNV"]
    fa = _fleet(
        [0, 0], ["gas_cc", "gas_cc"], [400.0, 400.0], [160.0, 160.0], [7.0, 9.0]
    )
    load = np.full((1, T), 600.0)
    gen = np.full((1, T), 733.3333333333334)  # 40 MW contingency, 20 MW spin
    design = _nwpp_design(_config(), fa, T, zones, basis_mw=(load, gen))
    assert int(design.pergen_col.max()) + 1 == 2  # one pool per plant
    r = solve_dispatch(
        fa,
        np.full((1, T), 400.0),
        wind_cf=np.zeros((1, T)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, T)),
        solar_cap=np.zeros(1),
        fuel_prices=np.full((2, T), 1.0),
        voll=2000.0,
        **build_reserve_dispatch_kwargs(design),
    )
    assert r.status == "Optimal"
    d = np.asarray(r.dispatch)
    rho = design.online_rho
    spin = np.minimum(400.0 - d[0], rho * d[0]) + np.minimum(400.0 - d[1], rho * d[1])
    assert np.all(spin >= 20.0 - 1e-4), spin
    assert np.all(d[0] < 400.0 - 1.0), d  # the loaded plant gives up energy
    assert float(np.asarray(r.reserve_price).max()) > 0.0  # holding spin costs
