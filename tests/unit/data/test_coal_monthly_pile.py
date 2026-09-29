"""Tests for the monthly pile grain of the yard rows (NWPP-NEXT-8,
coal_fuel_inventory_monthly_pile).

Trivial-first: the cumulative ceiling/floor arithmetic and its month-12 identity
with the annual rows, the per-month capacity clip, a two-month 1-zone LP where
the cumulative floor stops the take being banked in the cheaper month, the soft
floor's shortfall being paid once across the running sums, and the gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.coal_fuel_inventory import build_coal_monthly_pile  # noqa: E402
from market_sim.model.dispatch import solve_dispatch  # noqa: E402
from scripts.run_calibration import resolve_coal_monthly_pile  # noqa: E402
from tests.unit.data.test_coal_fuel_inventory import _coal_fleet  # noqa: E402

_YEAR = 8760
_JANFEB = (31 + 28) * 24  # a two-month horizon: month index 0 and 1


def _pile(pmax=1e6, parts=None, hours=_YEAR):
    fleet = _coal_fleet([1], pmax=pmax, hours=hours)
    return build_coal_monthly_pile(
        fleet,
        np.array([0]),
        np.array([0]),
        np.array([10.0]),
        np.array([[2_400.0]]),  # annual ceiling: stock 1,200 + receipts 1,200
        (1_200.0,),
        {0: (1_200.0, -600.0)} if parts is None else parts,
        hours,
    )


def test_month_twelve_is_the_annual_identity():
    ceiling, floor, mi, prov = _pile()
    assert ceiling.shape == floor.shape == (1, 12)
    assert prov.n_months == 12 and mi.shape == (_YEAR,)
    # ceiling_m = 1200 + m/12 * 1200; floor_m = max(0, -600 + m/12 * 1200).
    assert ceiling[0, -1] == pytest.approx(2_400.0)
    assert floor[0, -1] == pytest.approx(600.0)
    assert ceiling[0, 0] == pytest.approx(1_300.0)
    assert floor[0, :6].tolist() == pytest.approx([0.0] * 6)
    assert floor[0, 6] == pytest.approx(100.0)
    assert np.all(np.diff(ceiling[0]) >= 0) and np.all(np.diff(floor[0]) >= 0)


def test_ceiling_only_when_no_floor_is_armed():
    fleet = _coal_fleet([1], hours=_YEAR)
    ceiling, floor, _mi, _p = build_coal_monthly_pile(
        fleet,
        np.array([0]),
        np.array([0]),
        np.array([10.0]),
        np.array([[2_400.0]]),
        (1_200.0,),
        None,
        _YEAR,
    )
    assert floor is None and ceiling[0, -1] == pytest.approx(2_400.0)


def test_floor_clipped_per_month_to_what_the_units_can_burn():
    # 0.01 MW x HR 10 = 0.1 MMBtu/h: 74.4 MMBtu through January.
    ceiling, floor, _mi, prov = _pile(pmax=0.01, parts={0: (24_000.0, 0.0)})
    assert floor[0, 0] == pytest.approx(0.1 * 744)
    assert floor[0, -1] == pytest.approx(0.1 * _YEAR)
    assert prov.floor_clipped_to_capacity == 12
    assert np.all(floor <= ceiling + 1e-9)


def _janfeb_base(T, **extra):
    fleet = _coal_fleet([1], heat_rate=10.0, pmax=100.0, hours=T)
    demand = np.full((1, T), 100.0)
    jan = np.arange(T) < 31 * 24
    # Coal is dearer in January than in February; gas undercuts both.
    mc = np.vstack([np.where(jan, 40.0, 35.0), np.full(T, 30.0)])
    base = dict(
        wind_cf=np.zeros((1, T)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, T)),
        solar_cap=np.zeros(1),
        coal_plant_gen_idx=np.array([0]),
        coal_plant_month_index=jan.astype(int) ^ 1,  # Jan -> 0, Feb -> 1
        coal_plant_gen_hour_coeff=np.array([10.0]),
        coal_plant_group_index=np.array([0]),
    )
    base.update(extra)
    return fleet, demand, mc, base


def test_cumulative_floor_stops_banking_the_take_in_the_cheaper_month():
    T = _JANFEB
    fleet, demand, mc, base = _janfeb_base(T)
    # Annual form: a 1,200 MWh take lands entirely in cheaper February.
    r_ann = solve_dispatch(
        fleet,
        demand,
        mc=mc,
        T=T,
        coal_plant_budget=np.array([[1e9]]),
        coal_plant_floor=np.array([[12_000.0]]),
        **{**base, "coal_plant_month_index": np.zeros(T, dtype=int)},
    )
    jan = slice(0, 31 * 24)
    assert float(r_ann.dispatch[0, jan].sum()) == pytest.approx(0.0, abs=1e-4)
    # Monthly pile: at least 600 MWh must be burned by the end of January.
    r_mon = solve_dispatch(
        fleet,
        demand,
        mc=mc,
        T=T,
        coal_plant_budget=np.array([[1e9, 1e9]]),
        coal_plant_floor=np.array([[6_000.0, 12_000.0]]),
        **base,
    )
    assert float(r_mon.dispatch[0, jan].sum()) == pytest.approx(600.0, abs=1e-4)
    assert float(r_mon.dispatch[0].sum()) == pytest.approx(1200.0, abs=1e-4)


def test_cumulative_ceiling_stops_front_loading():
    T = _JANFEB
    fleet, demand, _mc, base = _janfeb_base(T)
    # Coal now undercuts gas everywhere; the pile funds only 300 MWh by end-Jan.
    mc = np.vstack([np.full(T, 20.0), np.full(T, 30.0)])
    r = solve_dispatch(
        fleet,
        demand,
        mc=mc,
        T=T,
        coal_plant_budget=np.array([[3_000.0, 1e9]]),
        **base,
    )
    assert float(r.dispatch[0, : 31 * 24].sum()) == pytest.approx(300.0, abs=1e-4)


def test_soft_floor_shortfall_is_paid_once_across_the_running_sums():
    T = _JANFEB
    fleet, demand, mc, base = _janfeb_base(T)
    kw = dict(
        coal_plant_budget=np.array([[1e9, 1e9]]),
        coal_plant_floor_price=np.array([1.0]),
        **base,
    )
    # Coal unavailable: the whole take is unmet. A 5,000 MMBtu take due by
    # end-January is still the SAME 5,000 at end-February, so it costs 5,000
    # once, not 10,000.
    fleet.availability[0, :] = 0.0
    r0 = solve_dispatch(fleet, demand, mc=mc, T=T, **kw)
    r1 = solve_dispatch(
        fleet, demand, mc=mc, T=T, coal_plant_floor=np.array([[5_000.0, 5_000.0]]), **kw
    )
    assert r1.objective_value - r0.objective_value == pytest.approx(5_000.0, rel=1e-6)


def _cfg(**kw) -> ScenarioConfig:
    return ScenarioConfig(mode="backcast").with_overrides(**kw)


def test_gate_default_off():
    assert resolve_coal_monthly_pile(_cfg(), "NWPP", True) is False


def test_gate_arms_for_nwpp_with_the_floor():
    assert resolve_coal_monthly_pile(
        _cfg(coal_fuel_inventory_monthly_pile=True), "NWPP", True
    )


def test_gate_requires_the_take_floor():
    with pytest.raises(ValueError, match="requires coal_fuel_inventory_take_floor"):
        resolve_coal_monthly_pile(
            _cfg(coal_fuel_inventory_monthly_pile=True), "NWPP", False
        )


def test_gate_refuses_other_isos():
    with pytest.raises(ValueError, match="R-ISO-SCOPE"):
        resolve_coal_monthly_pile(
            _cfg(coal_fuel_inventory_monthly_pile=True), "MISO", True
        )


def test_cache_key_unchanged_off_and_distinct_armed():
    base = ScenarioConfig()
    assert (
        base.cache_key()
        == ScenarioConfig(coal_fuel_inventory_monthly_pile=False).cache_key()
    )
    assert (
        base.cache_key()
        != ScenarioConfig(coal_fuel_inventory_monthly_pile=True).cache_key()
    )
