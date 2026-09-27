"""Regression contract of the PJM mid-curve SHAPE-ON-OWN-COST scope (PJM-NEXT-5).

``ScenarioConfig.pjm_offer_midcurve_shape_segments`` sets a targeted ECON row's
bid to its plant's own committed-rung cost scaled by the measured ladder RATIO
between the two within-plant shares. Contract, on trivial cases (2-3 rows, 24 h):

* a flat measured ladder (ratio 1) prices the econ row at the plant's own
  committed cost — whatever the fitted econ band was (it may lower it);
* a rising ladder scales the plant's own cost by m(s_econ) / m(s_committed),
  independent of the gas index;
* the committed rung itself is never touched;
* a segment in both the level and the shape scope is refused (rule 19);
* ``None`` is byte-identical to the floor form.
"""

import json
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import market_sim.data.fuel as fuel_pkg
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import build_pjm_offer_midcurve_conditional_markup

YEAR = 2025
T = 24


def _gen(uid: str, group: str):
    return types.SimpleNamespace(unit_id=uid, plant_group=group)


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """A constant Henry Hub series and a surface writer."""
    hh = tmp_path / "hh.csv"
    days = pd.date_range("2024-12-25", "2025-01-05", freq="D")
    pd.DataFrame({"date": days, "price_usd_mmbtu": 3.0}).to_csv(hh, index=False)
    monkeypatch.setattr(fuel_pkg, "HENRY_HUB_DAILY_PATH", hh)

    def write(lo: float, hi: float) -> Path:
        lad = [[0.25, lo], [0.75, hi]]
        path = tmp_path / f"surf_{lo}_{hi}.json"
        path.write_text(
            json.dumps(
                {
                    "_provenance": {"netload_pct_edges": [0.5], "shares": [0.25, 0.75]},
                    "CC_LIKE": {"years": {str(YEAR): [lad, lad]}},
                    "LONG_RUN": {"years": {str(YEAR): [lad, lad]}},
                }
            )
        )
        return path

    return write


def _run(path, shape, mc_econ=100.0, level=None):
    gens = [_gen("CCA_committed", "CC_REGULAR"), _gen("CCA_econc00", "CC_REGULAR")]
    fa = types.SimpleNamespace(pmax=np.array([100.0, 100.0]), vom=np.array([2.0, 2.0]))
    mc = np.tile(np.array([[5.0], [mc_econ]]), (1, T))
    cfg = ScenarioConfig(iso="PJM").with_overrides(
        pjm_offer_midcurve_conditional=True,
        pjm_offer_midcurve_path=str(path),
        pjm_offer_midcurve_segments=("CC_LIKE",),
        pjm_offer_midcurve_level_segments=level,
        pjm_offer_midcurve_shape_segments=shape,
    )
    return mc, build_pjm_offer_midcurve_conditional_markup(
        fa, gens, mc, np.arange(T, dtype=float), cfg, YEAR
    )


def test_flat_ladder_prices_econ_at_own_committed_cost(env):
    mc, m = _run(env(2.0, 2.0), ("CC_LIKE",))
    assert np.allclose(mc[1] + m[1], 5.0)  # lowered from the fitted 100
    assert np.all(m[0] == 0.0)


def test_rising_ladder_scales_own_cost_by_the_measured_ratio(env):
    mc, m = _run(env(2.0, 4.0), ("CC_LIKE",))
    # (5 - 2) * 4/2 + 2 = 8, independent of the gas index
    assert np.allclose(mc[1] + m[1], 8.0)


def test_off_is_the_floor_form(env):
    path = env(2.0, 4.0)
    _, off = _run(path, None)
    _, empty = _run(path, ())
    assert (off is None and empty is None) or np.array_equal(off, empty)
    if off is not None:
        assert np.all(off >= 0.0)


def test_level_and_shape_overlap_is_refused(env):
    with pytest.raises(ValueError, match="rule 19"):
        _run(env(2.0, 4.0), ("CC_LIKE",), level=("CC_LIKE",))


def test_registered_default_off():
    from market_sim.config.scenarios import cache_key_drop_defaults

    assert ScenarioConfig().pjm_offer_midcurve_shape_segments is None
    assert "pjm_offer_midcurve_shape_segments" in cache_key_drop_defaults()
    assert (
        ScenarioConfig().cache_key()
        != ScenarioConfig()
        .with_overrides(pjm_offer_midcurve_shape_segments=("CC_LIKE",))
        .cache_key()
    )
