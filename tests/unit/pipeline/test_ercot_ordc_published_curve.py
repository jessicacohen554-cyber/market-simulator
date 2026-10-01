"""Tests for ``ScenarioConfig.ercot_ordc_published_curve`` (R-ERCOT-24).

The flag prices ERCOT's ORDC on its published curve: the OBD's first-half
form ``1 - CDF(0.5 * mu_s, 0.707 * sigma)`` and ERCOT's seasonal mu / sigma
(Biennial ORDC Report Figure 3). Armed, both ERCOT co-opt ORDC families carry
``(n_steps, T)`` penalties on one reserve grid. Off, for another ISO, or with
S = 0, nothing moves.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[3]
for _p in (str(REPO), str(REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.config.constants import (  # noqa: E402
    ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.lp.costs import build_cost_vector  # noqa: E402
from market_sim.model.lp.layout import VariableLayout  # noqa: E402
from market_sim.model.reserves.spec import (  # noqa: E402
    ReserveDesign,
    ReserveFamily,
    build_reserve_dispatch_kwargs,
)
from market_sim.results.scarcity import (  # noqa: E402
    ercot_ordc_demand_steps,
    ercot_ordc_published_curve_active,
    ercot_published_mu_sigma_hourly,
    lolp,
    ordc_adder,
    resolve_lolp_params,
)

MAR1 = 59 * 24  # 2019-03-01 00:00 on the non-leap clock


def _ercot(year: int, **kw) -> ScenarioConfig:
    order = ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR[year]
    return ScenarioConfig(
        iso="ERCOT", mode="backcast", weather_year=year
    ).with_overrides(**order, **kw)


def test_gate_is_ercot_only_and_default_off():
    assert not ercot_ordc_published_curve_active(_ercot(2020))
    assert ercot_ordc_published_curve_active(
        _ercot(2020, ercot_ordc_published_curve=True)
    )
    pjm = ScenarioConfig(iso="PJM", ercot_ordc_published_curve=True)
    assert not ercot_ordc_published_curve_active(pjm)


def test_seasonal_table_steps_on_season_starts():
    mu, sig = ercot_published_mu_sigma_hourly(2019, 8760)
    assert mu.shape == sig.shape == (8760,)
    # Jan-Feb 2019 = the Dec-2018 season (pre-shift); Mar 1 picks up the
    # 0.25-sigma PUCT 48551 shift (~+0.25 x 1,214 MW) in the published mu_s.
    assert (mu[:MAR1] == mu[0]).all()
    assert mu[MAR1] - mu[MAR1 - 1] == pytest.approx(0.25 * sig[MAR1], abs=40.0)
    # sigma ~1.2 GW, mu_s within published bounds every year.
    for year in range(2019, 2026):
        mu, sig = ercot_published_mu_sigma_hourly(year, 8760)
        assert 1150 < sig.min() and sig.max() < 1350
        assert 250 < mu.min() and mu.max() < 950


def test_table_carries_last_season_forward_and_refuses_before_first():
    mu25, sig25 = ercot_published_mu_sigma_hourly(2025, 8760)
    assert np.unique(mu25).size == 1 and np.unique(sig25).size == 1
    with pytest.raises(ValueError):
        ercot_published_mu_sigma_hourly(2018, 8760)


def test_resolver_returns_unshifted_mu_and_guards():
    cfg = _ercot(2020, ercot_ordc_published_curve=True)
    mu, sig = resolve_lolp_params(cfg, 8760, year=2020)
    mu_s, sig_p = ercot_published_mu_sigma_hourly(2020, 8760)
    assert np.allclose(mu + cfg.ordc_lolp_shift_sigma * sig, mu_s)
    assert np.array_equal(sig, sig_p)
    with pytest.raises(ValueError):
        resolve_lolp_params(cfg, 8760)  # needs the year
    fc = ScenarioConfig(iso="ERCOT", mode="forecast").with_overrides(
        ercot_ordc_published_curve=True
    )
    with pytest.raises(ValueError):
        resolve_lolp_params(fc, 8760, year=2030)
    # Off: the flat fallback, untouched.
    off = _ercot(2020)
    assert resolve_lolp_params(off, 8760) == (
        off.ordc_lolp_mu_mw,
        off.ordc_lolp_sigma_mw,
    )


def test_obd_half_form_halves_the_shift():
    r = np.linspace(3000, 9000, 50)
    mu, sig, s = 300.0, 1200.0, 0.5
    lam = np.zeros_like(r)
    legacy = ordc_adder(
        r,
        lam,
        voll=5000.0,
        mcl_mw=2000.0,
        mu_mw=mu,
        sigma_mw=sig,
        shift_sigma=s,
        multistep_floor=False,
    )
    obd = ordc_adder(
        r,
        lam,
        voll=5000.0,
        mcl_mw=2000.0,
        mu_mw=mu,
        sigma_mw=sig,
        shift_sigma=s,
        multistep_floor=False,
        obd_half_shift=True,
    )
    full = lolp(r, mu, sig, 2000.0, s)
    half = 1.0 - __import__("scipy.special").special.ndtr(
        (r - 2000.0 - 0.5 * (mu + s * sig)) / (sig / np.sqrt(2.0))
    )
    assert np.allclose(obd, 0.5 * 5000.0 * (full + half))
    assert (obd <= legacy + 1e-12).all() and (obd < legacy).any()
    # With S = 0 the two forms coincide.
    a = ordc_adder(
        r,
        lam,
        voll=5000.0,
        mcl_mw=2000.0,
        mu_mw=mu,
        sigma_mw=sig,
        shift_sigma=0.0,
        multistep_floor=False,
    )
    b = ordc_adder(
        r,
        lam,
        voll=5000.0,
        mcl_mw=2000.0,
        mu_mw=mu,
        sigma_mw=sig,
        shift_sigma=0.0,
        multistep_floor=False,
        obd_half_shift=True,
    )
    assert np.array_equal(a, b)


def test_demand_steps_scalar_path_unchanged_and_hourly_path_shaped():
    kw = dict(voll=9000.0, mcl_mw=2000.0, shift_sigma=0.5, multistep_floor=False)
    req, pen, wid = ercot_ordc_demand_steps(mu_mw=0.0, sigma_mw=1400.0, **kw)
    assert pen.shape == wid.shape == (40,)
    assert req == pytest.approx(2000.0 + 700.0 + 5 * 1400.0)
    mu = np.array([0.0, 0.0, 300.0])
    sig = np.array([1400.0, 1400.0, 1200.0])
    req_h, pen_h, wid_h = ercot_ordc_demand_steps(mu_mw=mu, sigma_mw=sig, **kw)
    assert pen_h.shape == (40, 3) and wid_h.shape == (40,)
    assert req_h == pytest.approx(
        max(2000 + m + 0.5 * s + 5 * s for m, s in zip(mu, sig))
    )
    # Same params in hours 0/1 -> identical columns; a constant array equals
    # the scalar curve on the same grid.
    assert np.array_equal(pen_h[:, 0], pen_h[:, 1])
    _, pen_c, _ = ercot_ordc_demand_steps(
        mu_mw=np.zeros(2), sigma_mw=np.full(2, 1400.0), **kw
    )
    assert np.allclose(pen_c[:, 0], pen)
    # Penalties ascend as reserves fall, capped at VOLL.
    assert (np.diff(pen_h, axis=0) >= -1e-9).all() and pen_h.max() <= 9000.0


def test_dispatch_kwargs_promote_hourly_penalties():
    T = 3
    fam_static = ReserveFamily(
        "a", np.ones(T), np.ones(1, bool), np.array([1.0, 2.0]), np.array([10.0, 10.0])
    )
    fam_hourly = ReserveFamily(
        "b",
        np.ones(T),
        np.ones(1, bool),
        np.array([[5.0, 6.0, 7.0]]),
        np.array([20.0]),
        -1,
    )
    kw = build_reserve_dispatch_kwargs(
        ReserveDesign(families=[fam_static, fam_hourly], eligible=np.ones((1, 1), bool))
    )
    pen = kw["ordc_penalties"]
    assert pen.shape == (3, T)
    assert np.array_equal(pen[0], [1.0] * T) and np.array_equal(pen[2], [5, 6, 7])
    kw0 = build_reserve_dispatch_kwargs(
        ReserveDesign(families=[fam_static], eligible=np.ones((1, 1), bool))
    )
    assert kw0["ordc_penalties"].shape == (2,)


def test_cost_vector_takes_hourly_penalties():
    T, n = 4, 2
    layout = VariableLayout(
        T=T,
        n_gen=1,
        n_zones=1,
        n_storage=0,
        n_links=0,
        n_reserve_classes=1,
        n_ordc_steps=n,
    )
    mc = np.array([10.0])
    pen = np.array([100.0, 2000.0])
    static = build_cost_vector(layout, mc, 9000.0, ordc_penalties=pen)
    tiled = build_cost_vector(
        layout, mc, 9000.0, ordc_penalties=np.repeat(pen[:, None], T, axis=1)
    )
    assert np.array_equal(static, tiled)
    hourly = np.array([[1.0, 2.0, 3.0, 4.0], [10.0, 20.0, 30.0, 40.0]])
    scale = np.array([1.0, 1.0, 0.5, 0.5])
    got = build_cost_vector(
        layout, mc, 9000.0, ordc_penalties=hourly, ordc_penalty_hour_scale=scale
    )
    blk = got.reshape(T, layout.vars_per_hour)[
        :, layout._ordc_off : layout._ordc_off + n
    ]
    assert np.allclose(blk, (hourly * scale[None, :]).T)
    with pytest.raises(ValueError):
        build_cost_vector(layout, mc, 9000.0, ordc_penalties=np.ones((n, T + 1)))
