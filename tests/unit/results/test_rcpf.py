"""Tests for the NYISO RCPF reserve-demand-curve scarcity overlay
(results.rcpf)."""

import numpy as np
import pytest

from market_sim.config.reserve_config import (
    NEISO_RCPF_PRODUCTS,
    NYISO_RCPF_LOCATIONAL,
    NYISO_RCPF_PRODUCTS,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.results.rcpf import (
    locational_zone_adders,
    rcpf_adder,
    rcpf_product_prices,
    reserve_demand_price,
    resolve_rcpf_locational,
    resolve_rcpf_products,
)


def test_reserve_demand_price_zero_above_requirement():
    # No shortage -> no penalty.
    r = np.array([3000.0, 2620.0, 5000.0])
    p = reserve_demand_price(
        r, requirement_mw=2620.0, critical_mw=1965.0, max_penalty=750.0
    )
    assert np.allclose(p, 0.0)


def test_reserve_demand_price_max_at_or_below_critical():
    r = np.array([1965.0, 1000.0, 0.0, -500.0])
    p = reserve_demand_price(
        r, requirement_mw=2620.0, critical_mw=1965.0, max_penalty=750.0
    )
    assert np.allclose(p, 750.0)


def test_reserve_demand_price_linear_between_anchors():
    # Halfway between requirement (2620) and critical (1965) -> half max.
    mid = (2620.0 + 1965.0) / 2.0
    p = reserve_demand_price(
        np.array([mid]), requirement_mw=2620.0, critical_mw=1965.0, max_penalty=750.0
    )
    assert p[0] == pytest.approx(375.0)


def test_reserve_demand_price_monotonic_decreasing_in_reserves():
    r = np.linspace(0.0, 3000.0, 200)
    p = reserve_demand_price(r, 2620.0, 1965.0, 750.0)
    # More reserves never raise the penalty.
    assert np.all(np.diff(p) <= 1e-9)


def test_reserve_demand_price_rejects_bad_span():
    with pytest.raises(ValueError):
        reserve_demand_price(
            np.array([100.0]),
            requirement_mw=1000.0,
            critical_mw=1000.0,
            max_penalty=750.0,
        )


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
    assert ScenarioConfig().nyiso_rcpf_locational is None


# --- NEISO (ISO-NE) RCPF: ISO-aware product resolution ---------------------


def test_resolve_products_neiso_uses_isone_table():
    """A NEISO config resolves to the ISO-NE products; other ISOs unchanged."""
    assert resolve_rcpf_products(ScenarioConfig(iso="NEISO")) == NEISO_RCPF_PRODUCTS
    # The default (no iso / NYISO) path is untouched.
    assert resolve_rcpf_products(ScenarioConfig()) == NYISO_RCPF_PRODUCTS
    assert resolve_rcpf_products(ScenarioConfig(iso="NYISO")) == NYISO_RCPF_PRODUCTS
    # A NEISO override flows through the resolver and the adder.
    custom = (("ne_test", 1000.0, 0.0, 250.0),)
    cfg = ScenarioConfig(iso="NEISO", neiso_rcpf_products=custom)
    assert resolve_rcpf_products(cfg) == custom
    assert rcpf_adder(np.array([0.0]), cfg)[0] == pytest.approx(250.0)


def test_neiso_adder_dormant_above_requirement_and_stacks_below():
    """$0 when reserves clear the requirement; full stack at zero reserves."""
    cfg = ScenarioConfig(iso="NEISO")
    # Above the largest requirement (1,800 MW) -> dormant.
    assert rcpf_adder(np.array([2500.0]), cfg)[0] == pytest.approx(0.0)
    # At zero reserves -> the three penalties stack ($50 + $1,500 + $1,000).
    expected = sum(p[3] for p in NEISO_RCPF_PRODUCTS)
    assert rcpf_adder(np.array([0.0]), cfg)[0] == pytest.approx(expected)


def test_neiso_config_flag_defaults_off():
    assert ScenarioConfig().neiso_rcpf_enabled is False
    assert ScenarioConfig().neiso_rcpf_products is None


# --- locational (zonal) reserve cascade ------------------------------------

# The five model zones, ample reserves everywhere (no shortage anywhere).
_AMPLE = {
    "Upstate_West": np.full(4, 9000.0),
    "Capital_Hudson": np.full(4, 4000.0),
    "Lower_Hudson": np.full(4, 2000.0),
    "NYC": np.full(4, 6000.0),
    "Long_Island": np.full(4, 3000.0),
}


def test_locational_zero_when_every_region_ample():
    adders = locational_zone_adders(_AMPLE)
    assert set(adders) == set(_AMPLE)
    for a in adders.values():
        assert np.allclose(a, 0.0)


def test_locational_cascade_membership():
    # Upstate carries no locational region; NYC carries the most (East+SENY+
    # NYC). Reserves zero everywhere -> every region's products pin to max, so
    # the per-zone adder is the sum over the regions that contain the zone.
    zero = {z: np.zeros(2) for z in _AMPLE}
    adders = locational_zone_adders(zero)
    # Upstate is in no locational region.
    assert np.allclose(adders["Upstate_West"], 0.0)
    east_max = sum(p[3] for p in NYISO_RCPF_LOCATIONAL["East"]["products"])
    seny_max = sum(p[3] for p in NYISO_RCPF_LOCATIONAL["SENY"]["products"])
    nyc_max = sum(p[3] for p in NYISO_RCPF_LOCATIONAL["NYC"]["products"])
    # Capital_Hudson: East only.
    assert adders["Capital_Hudson"][0] == pytest.approx(east_max)
    # Lower_Hudson / Long_Island: East + SENY.
    assert adders["Lower_Hudson"][0] == pytest.approx(east_max + seny_max)
    assert adders["Long_Island"][0] == pytest.approx(east_max + seny_max)
    # NYC: East + SENY + NYC (deepest in the cascade).
    assert adders["NYC"][0] == pytest.approx(east_max + seny_max + nyc_max)
    # The cascade is strictly increasing downstate.
    assert (
        adders["NYC"][0] > adders["Lower_Hudson"][0] > adders["Capital_Hudson"][0] > 0.0
    )


def test_locational_region_headroom_is_summed_over_member_zones():
    # East requirement is 1,200 MW over F-K. Split 700 + 500 across two member
    # zones -> region reserve 1,200 == requirement -> $0 East contribution.
    at_req = {z: np.zeros(1) for z in _AMPLE}
    at_req["Capital_Hudson"] = np.array([700.0])
    at_req["Lower_Hudson"] = np.array([500.0])
    # The other East members (NYC, Long_Island) at 0 -> region total 1200.
    at_req["NYC"] = np.array([0.0])
    at_req["Long_Island"] = np.array([0.0])
    a = locational_zone_adders(at_req)
    # East region reserve = 1200 == requirement -> East contributes 0. The
    # Capital_Hudson zone is in East only, so its total adder is 0.
    assert a["Capital_Hudson"][0] == pytest.approx(0.0)
    # NYC zone still carries its SENY (reserve 500) and NYC (reserve 0)
    # shortages: SENY region reserve = 500+0+0 = 500 < 1300, NYC = 0.
    seny = NYISO_RCPF_LOCATIONAL["SENY"]["products"][0]
    seny_at_500 = seny[3] * (seny[1] - 500.0) / (seny[1] - seny[2])
    nyc_max = sum(p[3] for p in NYISO_RCPF_LOCATIONAL["NYC"]["products"])
    assert a["NYC"][0] == pytest.approx(seny_at_500 + nyc_max)


def test_locational_resolve_default_and_override():
    assert resolve_rcpf_locational(ScenarioConfig()) is NYISO_RCPF_LOCATIONAL
    custom = {"NYC": {"zones": ("NYC",), "products": (("z", 500.0, 0.0, 999.0),)}}
    cfg = ScenarioConfig(nyiso_rcpf_locational=custom)
    assert resolve_rcpf_locational(cfg) is custom
    a = locational_zone_adders({"NYC": np.zeros(1)}, config=cfg)
    assert a["NYC"][0] == pytest.approx(999.0)


def test_locational_empty_products_region_is_noop():
    # A region with no products must not raise or contribute.
    regions = {"Empty": {"zones": ("NYC", "Long_Island"), "products": ()}}
    a = locational_zone_adders(
        {"NYC": np.zeros(1), "Long_Island": np.zeros(1)}, regions=regions
    )
    for v in a.values():
        assert np.allclose(v, 0.0)
