"""Tests for the NEISO condition-responsive fast-start offer surface (Limb B).

Mirrors ``tests/test_ercot_offer_surface_conditional.py`` for the NEISO
wrapper (``data.fleet.build_neiso_offer_surface_conditional_markup``): flag
off / wrong ISO → None; the measured binned ladder reprices ONLY CT_PEAKER
peak rungs, ONLY in tight net-load bins (loose bins clamp to ratio 1, i.e.
zero markup); edges mismatch hard-errors; the VOLL-fraction guard caps the
repriced offer.
"""

import json
from types import SimpleNamespace

import numpy as np
import pytest

from market_sim.data.fleet import build_neiso_offer_surface_conditional_markup

T = 100
N_RUNGS = 5


class _Gen(SimpleNamespace):
    pass


def _fleet(n):
    return SimpleNamespace(heat_rate=np.full(n, 10.0))


def _gens():
    """Three rows: CT_PEAKER peak (rung 0), CT_PEAKER peak5 (rung 4), CC peak."""
    return [
        _Gen(unit_id="CT_PEAKER_Boston_p1_peak", plant_group="CT_PEAKER"),
        _Gen(unit_id="CT_PEAKER_Boston_p1_peak5", plant_group="CT_PEAKER"),
        _Gen(unit_id="CC_REGULAR_Boston_p2_peak", plant_group="CC_REGULAR"),
    ]


def _surface(tmp_path, edges=(0.8, 0.9, 0.97), tight_mult=30.0, name="surface.json"):
    """Ladder: loose bins at the resolved peak (2.0); the tightest bin's top
    rung at ``tight_mult``."""
    n_bins = len(edges) + 1
    ladder = []
    for b in range(n_bins):
        rungs = [[0.2, 2.0] for _ in range(N_RUNGS)]
        if b == n_bins - 1:
            rungs[-1] = [0.2, tight_mult]
        ladder.append(rungs)
    obj = {
        "_provenance": {"netload_pct_edges": list(edges)},
        "CT_PEAKER": {"base_hr": 10.0, "peak_p50": 2.0, "binned_ladder": ladder},
    }
    p = tmp_path / name
    p.write_text(json.dumps(obj))
    return str(p)


def _config(tmp_path, **over):
    base = dict(
        iso="NEISO",
        neiso_offer_surface_conditional=True,
        neiso_offer_surface_binned_path=_surface(tmp_path),
        neiso_offer_surface_netload_pcts=(0.8, 0.9, 0.97),
        neiso_offer_surface_min_bin=0,
        neiso_offer_surface_price_cap_frac=0.95,
        voll=5000.0,
        offer_curve_by_group={"CT_PEAKER": {"peak": 2.0}},
    )
    base.update(over)
    return SimpleNamespace(**base)


def _net_load():
    """Hours 0..97 loose, 98-99 in the tightest (top-3%) bin."""
    nl = np.linspace(1000.0, 2000.0, T)
    nl[-2:] = 10_000.0
    return nl


def test_off_or_wrong_iso_is_none(tmp_path):
    fa, gens = _fleet(3), _gens()
    fuel = np.full((3, T), 3.0)
    cfg = _config(tmp_path, neiso_offer_surface_conditional=False)
    assert (
        build_neiso_offer_surface_conditional_markup(fa, gens, fuel, _net_load(), cfg)
        is None
    )
    cfg = _config(tmp_path, iso="ERCOT")
    assert (
        build_neiso_offer_surface_conditional_markup(fa, gens, fuel, _net_load(), cfg)
        is None
    )


def test_reprices_only_ct_peaker_top_rung_in_tight_hours(tmp_path):
    fa, gens = _fleet(3), _gens()
    fuel = np.full((3, T), 3.0)
    cfg = _config(tmp_path)
    mk = build_neiso_offer_surface_conditional_markup(fa, gens, fuel, _net_load(), cfg)
    assert mk is not None and mk.shape == (3, T)
    # CC row untouched (not in the NEISO surface groups).
    assert np.all(mk[2] == 0.0)
    # CT peak (rung 0) stays at the resolved height everywhere (ladder == 2.0).
    assert np.all(mk[0] == 0.0)
    # CT peak5 (rung 4): zero outside the top bin, repriced inside it (bin
    # membership computed exactly as the mechanism computes it).
    nl = _net_load()
    bins = np.searchsorted(np.quantile(nl, (0.8, 0.9, 0.97)), nl, side="right")
    assert np.all(mk[1, bins < 3] == 0.0)
    # energy = 10 HR x $3 = $30; ratio 30/2 = 15 -> markup = 30 x 14 = 420.
    np.testing.assert_allclose(mk[1, bins == 3], 30.0 * (30.0 / 2.0 - 1.0))
    assert (bins == 3).sum() >= 2  # the synthetic spike hours are in the bin


def test_price_cap_guard(tmp_path):
    fa, gens = _fleet(3), _gens()
    fuel = np.full((3, T), 3.0)
    # tight rung would price at 10x3x1000 = $30,000 -> capped at 0.95 x VOLL.
    cfg = _config(
        tmp_path,
        neiso_offer_surface_binned_path=_surface(
            tmp_path, tight_mult=1000.0, name="surface_hot.json"
        ),
    )
    mk = build_neiso_offer_surface_conditional_markup(fa, gens, fuel, _net_load(), cfg)
    offered = 30.0 + mk[1, -1]  # energy MC + markup
    assert offered == pytest.approx(0.95 * 5000.0)


def test_edges_mismatch_raises(tmp_path):
    fa, gens = _fleet(3), _gens()
    fuel = np.full((3, T), 3.0)
    cfg = _config(tmp_path, neiso_offer_surface_netload_pcts=(0.5, 0.9, 0.97))
    with pytest.raises(ValueError, match="netload_pcts"):
        build_neiso_offer_surface_conditional_markup(fa, gens, fuel, _net_load(), cfg)


def test_min_bin_gates_wall(tmp_path):
    fa, gens = _fleet(3), _gens()
    fuel = np.full((3, T), 3.0)
    # min_bin above the tightest bin index (3) -> everything inert.
    cfg = _config(tmp_path, neiso_offer_surface_min_bin=4)
    mk = build_neiso_offer_surface_conditional_markup(fa, gens, fuel, _net_load(), cfg)
    assert mk is None or not np.any(mk > 0.0)
