"""Tests for the NYISO RCPF reserve-demand-curve scarcity overlay
(results.rcpf)."""
import numpy as np
import pytest

from market_sim.config.constants import NYISO_RCPF_PRODUCTS
from market_sim.config.scenarios import ScenarioConfig
from market_sim.results.rcpf import (
    rcpf_adder,
    rcpf_product_prices,
    reserve_demand_price,
    resolve_rcpf_products,
)


def test_reserve_demand_price_zero_above_requirement():
    # No shortage -> no penalty.
    r = np.array([3000.0, 2620.0, 5000.0])
    p = reserve_demand_price(r, requirement_mw=2620.0, critical_mw=1965.0,
                             max_penalty=750.0)
    assert np.allclose(p, 0.0)


def test_reserve_demand_price_max_at_or_below_critical():
    r = np.array([1965.0, 1000.0, 0.0, -500.0])
    p = reserve_demand_price(r, requirement_mw=2620.0, critical_mw=1965.0,
                             max_penalty=750.0)
    assert np.allclose(p, 750.0)


def test_reserve_demand_price_linear_between_anchors():
    # Halfway between requirement (2620) and critical (1965) -> half max.
    mid = (2620.0 + 1965.0) / 2.0
    p = reserve_demand_price(np.array([mid]), requirement_mw=2620.0,
                             critical_mw=1965.0, max_penalty=750.0)
    assert p[0] == pytest.approx(375.0)


def test_reserve_demand_price_monotonic_decreasing_in_reserves():
    r = np.linspace(0.0, 3000.0, 200)
    p = reserve_demand_price(r, 2620.0, 1965.0, 750.0)
    # More reserves never raise the penalty.
    assert np.all(np.diff(p) <= 1e-9)


def test_reserve_demand_price_rejects_bad_span():
    with pytest.raises(ValueError):
        reserve_demand_price(np.array([100.0]), requirement_mw=1000.0,
                             critical_mw=1000.0, max_penalty=750.0)


def test_adder_zero_when_reserves_ample():
    # Above every product's requirement (max req = 2620) -> no adder.
    r = np.full(10, 5000.0)
    assert np.allclose(rcpf_adder(r), 0.0)


def test_adder_stacks_nested_products_in_deep_shortage():
    # At zero reserves every product pins to its max; the adder is the sum.
    r = np.zeros(3)
    adder = rcpf_adder(r)
    expected = sum(prod[3] for prod in NYISO_RCPF_PRODUCTS)
    assert np.allclose(adder, expected)
    # That stacked maximum clears the observed 2023 tail ($1,147/MWh).
    assert expected > 1147.0


def test_adder_only_30min_binds_in_shallow_shortage():
    # Reserves below the 30-min requirement (2620) but above the 10-min
    # requirement (1310): only the 30-min product contributes.
    r = np.array([2000.0])
    pp = rcpf_product_prices(r)
    assert pp["nyca_30min_total"][0] > 0.0
    assert pp["nyca_10min_total"][0] == 0.0
    assert pp["nyca_10min_spin"][0] == 0.0
    assert pp["adder"][0] == pytest.approx(pp["nyca_30min_total"][0])


def test_adder_monotonic_decreasing_in_reserves():
    r = np.linspace(0.0, 3000.0, 300)
    adder = rcpf_adder(r)
    assert np.all(np.diff(adder) <= 1e-9)


def test_product_prices_sum_to_adder():
    r = np.array([2500.0, 1500.0, 600.0, 100.0])
    pp = rcpf_product_prices(r)
    parts = sum(pp[prod[0]] for prod in NYISO_RCPF_PRODUCTS)
    assert np.allclose(parts, pp["adder"])
    assert np.allclose(pp["adder"], rcpf_adder(r))


def test_resolve_products_default_and_override():
    assert resolve_rcpf_products(ScenarioConfig()) == NYISO_RCPF_PRODUCTS
    custom = (("test", 1000.0, 0.0, 500.0),)
    cfg = ScenarioConfig(nyiso_rcpf_products=custom)
    assert resolve_rcpf_products(cfg) == custom
    # The override flows through the adder.
    r = np.array([0.0])
    assert rcpf_adder(r, cfg)[0] == pytest.approx(500.0)


def test_config_flag_defaults_off():
    assert ScenarioConfig().nyiso_rcpf_enabled is False
    assert ScenarioConfig().nyiso_rcpf_products is None
