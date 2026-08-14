"""Tests for the MISO position-conditioned measured offer surface (miso-151).

These are written against the REAL :class:`market_sim.data.fleet.Generator`
rather than a stand-in namespace, and that is the point of the module.  The
mechanism shipped with a wrong capacity-attribute name (``pmax`` instead of
``pmax_mw``) read through a silent ``getattr`` default, which drove every
tranche's own-curve position to 0.0 and collapsed the entire surface onto its
lowest position bin.  The smoke test that was supposed to catch it used a
``SimpleNamespace(pmax=...)`` and therefore *encoded the same wrong assumption
as the code* — it could not have failed.  A self-test that builds its fixture
from the production type cannot make that mistake.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from market_sim.data.fleet import Generator
from market_sim.data.offer_curves import (
    apply_miso_offer_surface,
    miso_surface_positions,
)


def _gen(label: str, cap: float, markup: float, plant: int = 1) -> Generator:
    """One CAMPD-style tranche row of a MISO gas plant."""
    return Generator(
        unit_id=f"p{plant}_{label}",
        name=label,
        zone="MISO-East",
        fuel_type="gas",
        pmax_mw=cap,
        heat_rate=7.0,
        plant_code=plant,
        plant_group="CC_REGULAR",
        bin_label=f"X_{label}",
        offer_markup_hr=markup,
    )


@pytest.fixture
def surface(tmp_path):
    """A synthetic ladder rising 10 -> 60 $/MWh across the six position bins."""
    rung = [
        [0.1, 10.0, 1],
        [0.3, 20.0, 1],
        [0.5, 30.0, 1],
        [0.7, 40.0, 1],
        [0.85, 50.0, 1],
        [0.95, 60.0, 1],
    ]
    art = {
        "_provenance": {"gas_bin_edges_usd_per_mmbtu": [2.0, 4.0]},
        "markets": {"DA": {"ladder": [[rung for _ in range(4)] for _ in range(3)]}},
    }
    path = tmp_path / "surface.json"
    path.write_text(json.dumps(art))
    return path


def _cfg(surface_path, **kw):
    from market_sim.config.scenarios import ScenarioConfig

    return ScenarioConfig(iso="MISO", mode="backcast").with_overrides(
        miso_offer_surface_measured=True,
        miso_offer_surface_path=str(surface_path),
        gas_offer_net_revenue_margin=True,
        gas_offer_margin_anchor=3.0,
        **kw,
    )


def test_positions_are_capacity_weighted_midpoints():
    """Own-curve position is the tranche's MW midpoint over its plant's total."""
    gens = [
        _gen("committed", 200.0, 0.0),
        _gen("econ_high", 100.0, 0.5),
        _gen("peak", 100.0, 2.0),
    ]
    assert np.allclose(miso_surface_positions(gens), [0.25, 0.625, 0.875])


def test_positions_read_pmax_mw_not_pmax():
    """The regression: a zero-capacity read collapses every position to 0.

    Guards the exact defect miso-151 shipped and caught — if the capacity field
    is ever renamed or silently defaulted again, positions go flat and this
    fails rather than a solve quietly repricing the fleet at one bin.
    """
    gens = [_gen("committed", 200.0, 0.0), _gen("peak", 100.0, 2.0)]
    pos = miso_surface_positions(gens)
    assert float(np.ptp(pos)) > 0.0, "positions must vary across a plant's tranches"


def test_above_base_repriced_onto_own_base_and_base_untouched(surface):
    """mc[above-base] := mc[plant base] + measured rise; base row unchanged."""
    gens = [
        _gen("committed", 200.0, 0.0),
        _gen("econ_high", 100.0, 0.5),
        _gen("peak", 100.0, 2.0),
    ]
    mc = np.array([[20.0] * 4, [35.0] * 4, [80.0] * 4])
    apply_miso_offer_surface(
        mc,
        gens,
        np.array([100.0, 200.0, 300.0, 400.0]),
        np.array([1.0, 3.0, 5.0, 3.0]),
        _cfg(surface),
    )
    assert np.allclose(mc[0], 20.0), "the base band must never be repriced"
    assert np.allclose(mc[1], 20.0 + 40.0), "position 0.625 -> bin 3 -> 40"
    assert np.allclose(mc[2], 20.0 + 50.0), "position 0.875 -> bin 4 -> 50"


def test_degenerate_positions_raise(surface):
    """A surface that cannot vary by position must fail, not silently apply."""
    gens = [_gen("econ_high", 100.0, 0.5)]
    mc = np.array([[35.0] * 4])
    with pytest.raises(ValueError, match="position coordinate is not"):
        apply_miso_offer_surface(
            mc, gens, np.array([100.0] * 4), np.array([3.0] * 4), _cfg(surface)
        )


def test_off_by_default_is_byte_identical(surface):
    """Gate off -> the offer path is untouched."""
    from market_sim.config.scenarios import ScenarioConfig

    gens = [_gen("committed", 200.0, 0.0), _gen("peak", 100.0, 2.0)]
    mc = np.array([[20.0] * 4, [80.0] * 4])
    before = mc.copy()
    apply_miso_offer_surface(
        mc,
        gens,
        np.array([100.0] * 4),
        np.array([3.0] * 4),
        ScenarioConfig(iso="MISO", mode="backcast"),
    )
    assert np.array_equal(mc, before)


def test_non_miso_iso_is_inert(surface):
    """Rule 25 [R-ISO-SCOPE]: this surface is MISO's and never transfers."""
    gens = [_gen("committed", 200.0, 0.0), _gen("peak", 100.0, 2.0)]
    mc = np.array([[20.0] * 4, [80.0] * 4])
    before = mc.copy()
    cfg = _cfg(surface).with_overrides(iso="PJM")
    apply_miso_offer_surface(mc, gens, np.array([100.0] * 4), np.array([3.0] * 4), cfg)
    assert np.array_equal(mc, before)
