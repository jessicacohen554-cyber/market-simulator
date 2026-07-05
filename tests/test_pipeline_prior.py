"""Unit tests for ``pipeline.PriorYearResults`` (the typed cross-year state).

The typed object must be a drop-in for the former ``prior_results`` dict:
attribute access and dict-style ``[...]`` / ``.get`` / ``in`` must all agree,
and ``.get`` must match ``dict.get`` semantics exactly (present → value, absent
→ default). Types come from the actual producers; no invented optionality.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.pipeline import PriorYearResults


def _make(**overrides) -> PriorYearResults:
    """Build a fully-populated ``PriorYearResults`` with distinct sentinels."""
    base = dict(
        fleet_arrays=object(),
        dispatch_result=object(),
        prices=np.array([10.0, 20.0]),
        peak_demand=1234.5,
        planned_additions=[{"unit": "A"}],
        mc_cost=np.array([1.0, 2.0, 3.0]),
        rps_shadow_price=5.0,
        retrofit_log=[{"annual_net_savings_per_mw": 100.0}],
        storage_power_mw=42.0,
        storage_as_revenue_per_mw_yr=7.0,
        thermal_as_revenue_per_mw_yr={"gas_cc": 3.0},
        wind_cap_mw=1000.0,
        solar_cap_mw=2000.0,
        storage_firm_mw=15.0,
    )
    base.update(overrides)
    return PriorYearResults(**base)


def test_attribute_and_item_access_agree():
    """``pr.x`` and ``pr["x"]`` return the same object for every field."""
    pr = _make()
    for key in [f for f in PriorYearResults._field_names()]:
        assert pr[key] is getattr(pr, key), key


def test_getitem_matches_producer_values():
    """A few fields read back exactly what was stored."""
    prices = np.array([99.0, 1.0])
    pr = _make(prices=prices, peak_demand=8.5)
    assert pr["prices"] is prices
    assert pr["peak_demand"] == 8.5
    assert pr["rps_shadow_price"] == 5.0


def test_get_matches_dict_get_semantics():
    """``.get`` mirrors ``dict.get``: present → value, absent → default."""
    pr = _make(rps_shadow_price=0.0)
    ref = dict(
        rps_shadow_price=0.0,
        prices=pr.prices,
        storage_as_revenue_per_mw_yr=7.0,
    )
    # Present keys.
    assert pr.get("rps_shadow_price") == ref.get("rps_shadow_price")
    assert pr.get("prices") is ref.get("prices")
    # A falsy-but-present value is returned, not the default (truthiness check
    # in runner.py:450 relies on this).
    assert pr.get("rps_shadow_price", 999.0) == 0.0
    # Absent key → default (None and explicit).
    assert pr.get("does_not_exist") is None
    assert pr.get("does_not_exist", "d") == "d"
    assert pr.get("does_not_exist", "d") == dict().get("does_not_exist", "d")


def test_contains():
    """``in`` reports membership over the defined fields."""
    pr = _make()
    assert "prices" in pr
    assert "storage_as_revenue_per_mw_yr" in pr
    assert "not_a_field" not in pr


def test_getitem_missing_raises_keyerror():
    """Unknown-key item access raises ``KeyError`` like a dict."""
    pr = _make()
    with pytest.raises(KeyError):
        _ = pr["nope"]


def test_all_fifteen_keys_present():
    """The typed object carries one field per current ``prior_results`` key.

    ``price_signal`` is the capacity-screen price signal added by the
    capacity-economics EWMA/lookahead mechanism (plan §2.2-§2.3); it is a real
    cross-year field, so the exact-key-set contract includes it.
    """
    expected = {
        "fleet_arrays",
        "dispatch_result",
        "prices",
        "price_signal",
        "peak_demand",
        "planned_additions",
        "mc_cost",
        "rps_shadow_price",
        "retrofit_log",
        "storage_power_mw",
        "storage_as_revenue_per_mw_yr",
        "thermal_as_revenue_per_mw_yr",
        "wind_cap_mw",
        "solar_cap_mw",
        "storage_firm_mw",
    }
    assert set(PriorYearResults._field_names()) == expected


def test_evolve_fleet_prior_attr_reads_the_typed_object():
    """``capacity._prior_attr`` (getattr fallback) reads the typed object."""
    from market_sim.model.capacity import _prior_attr

    pr = _make(peak_demand=777.0, wind_cap_mw=1.5)
    assert _prior_attr(pr, "peak_demand", 0.0) == 777.0
    assert _prior_attr(pr, "wind_cap_mw", 0.0) == 1.5
    # Missing attr falls back to the default (evolve_fleet relies on this).
    assert _prior_attr(pr, "unknown_key", "dflt") == "dflt"
