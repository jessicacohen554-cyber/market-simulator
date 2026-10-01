"""Tests for ``ScenarioConfig.ercot_swcap_effective_hourly`` (R-ERCOT-23).

The flag makes ERCOT's system-wide offer cap hourly: inside a published LCAP
window (``constants.ERCOT_LCAP_WINDOWS_BY_YEAR`` — 2021 from Operating Day
2021-03-04 at $2,000) the ORDC penalties, the load-shed cost and the offer
clip read the LCAP, and post-solve the summed adders obey the protocol cap
lambda + adders <= SWCAP. Off, outside a window, or for another ISO, nothing
moves.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
for _p in (str(REPO), str(REPO / "src"), str(REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.config.constants import (  # noqa: E402
    ERCOT_LCAP_WINDOWS_BY_YEAR,
    ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.lp.costs import build_cost_vector  # noqa: E402
from market_sim.model.lp.layout import VariableLayout  # noqa: E402
from market_sim.pipeline.solve import _swcap_clip_level  # noqa: E402
from market_sim.results.scarcity import (  # noqa: E402
    ercot_effective_swcap_series,
    ercot_swcap_effective_active,
)
from run_calibration_full import _system_frame  # noqa: E402

LCAP_START = 62 * 24  # Operating Day 2021-03-04 on the non-leap clock


def _ercot(year: int, **kw) -> ScenarioConfig:
    order = ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR[year]
    return ScenarioConfig(
        iso="ERCOT", mode="backcast", weather_year=year
    ).with_overrides(**order, **kw)


def test_lcap_table_is_the_published_2021_window():
    """One window: 2021, from 2021-03-04 00:00 (hour 1488), at $2,000."""
    assert ERCOT_LCAP_WINDOWS_BY_YEAR == {2021: (LCAP_START, 2000.0)}


def test_series_2021_drops_to_lcap_on_march_4():
    s = ercot_effective_swcap_series(2021, 8760, 9000.0)
    assert s.shape == (8760,)
    assert (s[:LCAP_START] == 9000.0).all()
    assert (s[LCAP_START:] == 2000.0).all()


def test_series_flat_in_every_other_year():
    for year in (2019, 2020, 2022, 2023, 2024, 2025, 2030):
        hcap = ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR.get(
            year, {"ordc_voll": 5000.0}
        )
        s = ercot_effective_swcap_series(year, 8760, hcap["ordc_voll"])
        assert (s == hcap["ordc_voll"]).all()


def test_lcap_never_exceeds_hcap():
    s = ercot_effective_swcap_series(2021, 8760, 1500.0)
    assert s.max() == 1500.0


def test_gate_is_ercot_only_and_default_off():
    assert not ercot_swcap_effective_active(_ercot(2021))
    assert ercot_swcap_effective_active(_ercot(2021, ercot_swcap_effective_hourly=True))
    pjm = ScenarioConfig(iso="PJM", ercot_swcap_effective_hourly=True)
    assert not ercot_swcap_effective_active(pjm)


def test_off_cache_key_is_byte_stable_and_armed_key_moves():
    base = _ercot(2021, ercot_swcap_vintage=True)
    off = _ercot(2021, ercot_swcap_vintage=True, ercot_swcap_effective_hourly=False)
    on = _ercot(2021, ercot_swcap_vintage=True, ercot_swcap_effective_hourly=True)
    assert base.cache_key() == off.cache_key()
    assert on.cache_key() != base.cache_key()


def test_offer_clip_is_hourly_only_inside_a_window():
    on = dict(ercot_swcap_vintage=True, ercot_offer_swcap_clip=True)
    c21 = _ercot(2021, ercot_swcap_effective_hourly=True, **on)
    lvl = _swcap_clip_level(c21)
    assert isinstance(lvl, np.ndarray) and lvl.shape == (1, c21.hours)
    assert lvl[0, 0] == 9000.0 - 0.01
    assert lvl[0, -1] == 2000.0 - 0.01
    # No window: the scalar clip, exactly the pre-flag value.
    c20 = _ercot(2020, ercot_swcap_effective_hourly=True, **on)
    assert _swcap_clip_level(c20) == 9000.0 - 0.01
    # Off: the scalar clip in 2021 too.
    assert _swcap_clip_level(_ercot(2021, **on)) == 9000.0 - 0.01


def _layout_with_ordc(T: int, n_steps: int) -> VariableLayout:
    return VariableLayout(
        T=T,
        n_gen=1,
        n_zones=1,
        n_storage=0,
        n_links=0,
        n_reserve_classes=1,
        n_ordc_steps=n_steps,
    )


def test_cost_vector_penalty_scale_is_hourly_and_none_is_identity():
    """Trivial case: 1 gen, 1 zone, 4 hours, 2 ORDC steps."""
    T = 4
    layout = _layout_with_ordc(T, 2)
    mc = np.full((1, T), 30.0)
    pen = np.array([100.0, 9000.0])
    base = build_cost_vector(layout, mc, 9000.0, ordc_penalties=pen)
    ones = build_cost_vector(
        layout, mc, 9000.0, ordc_penalties=pen, ordc_penalty_hour_scale=np.ones(T)
    )
    assert np.array_equal(base, ones)
    scale = np.array([1.0, 1.0, 2000.0 / 9000.0, 2000.0 / 9000.0])
    got = build_cost_vector(
        layout, mc, 9000.0, ordc_penalties=pen, ordc_penalty_hour_scale=scale
    )
    blk = got.reshape(T, layout.vars_per_hour)[
        :, layout._ordc_off : layout._ordc_off + layout.n_ordc_steps
    ]
    assert np.allclose(blk[0], pen)
    assert np.allclose(blk[3], [100.0 * 2000 / 9000, 2000.0])
    # Everything outside the ORDC block is unchanged.
    mask = np.ones(layout.vars_per_hour, dtype=bool)
    mask[layout._ordc_off : layout._ordc_off + layout.n_ordc_steps] = False
    assert np.array_equal(got.reshape(T, -1)[:, mask], base.reshape(T, -1)[:, mask])


@dataclass
class _Result:
    prices: np.ndarray
    slack: np.ndarray
    reserve_price: np.ndarray
    reserve_price_by_family: np.ndarray
    dump: np.ndarray | None = None


def _frame(swcap):
    T = 3
    prices = np.vstack([np.full(T, 1500.0), np.full(T, 1500.0)])
    demand = np.vstack([np.full(T, 100.0), np.full(T, 100.0)])
    fam = np.array([[0.0], [300.0], [900.0]])  # ORDC total-family dual
    res = _Result(
        prices=prices,
        slack=np.zeros_like(prices),
        reserve_price=np.zeros(T),
        reserve_price_by_family=fam,
    )
    return _system_frame(
        2021,
        "P1",
        res,
        demand,
        ["A", "B"],
        iso="ERCOT",
        ercot_reserve_supply_cap=True,
        ercot_ordc_total_reserve=True,
        swcap_hourly=swcap,
    )


def test_protocol_cap_trims_adders_to_swcap_minus_lambda():
    off = _frame(None)
    a = off[off.zone == "A"].sort_values("hour")
    assert np.allclose(a.price, [1500.0, 1800.0, 2400.0])
    on = _frame(np.full(3, 2000.0))
    b = on[on.zone == "A"].sort_values("hour")
    assert np.allclose(b.price, [1500.0, 1800.0, 2000.0])
    assert np.allclose(b.ordc_adder, [0.0, 300.0, 500.0])
    # A cap that never binds is the identity.
    same = _frame(np.full(3, 9000.0))
    assert np.allclose(same.price.to_numpy(), off.price.to_numpy())
