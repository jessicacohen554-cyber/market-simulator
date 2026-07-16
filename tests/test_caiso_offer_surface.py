"""Tests for the CAISO measured DAM offer surface (C1 lane WP-A).

Mirrors ``tests/test_neiso_offer_surface_conditional.py`` for the CAISO
wrapper (``data.fleet.build_caiso_offer_surface_conditional_markup``): flag
off / wrong ISO → None; the measured binned ladder reprices CC_REGULAR and
CT_PEAKER peak rungs ONLY in tight net-load bins; edges mismatch
hard-errors. Plus the STATIC half: ``backcast_config(...,
caiso_offer_surface_measured=True)`` replaces the fitted econ_low /
econ_high / peak band multipliers with the measured JSON's values while
leaving the committed band (deliberately unarmed) and the tranche-share
geometry untouched.
"""

import json
from types import SimpleNamespace

import numpy as np
import pytest

from market_sim.data.fleet import build_caiso_offer_surface_conditional_markup

T = 100
N_RUNGS = 5


class _Gen(SimpleNamespace):
    pass


def _fleet(n):
    return SimpleNamespace(heat_rate=np.full(n, 10.0))


def _gens():
    return [
        _Gen(unit_id="CT_PEAKER_NP15_p1_peak", plant_group="CT_PEAKER"),
        _Gen(unit_id="CT_PEAKER_NP15_p1_peak5", plant_group="CT_PEAKER"),
        _Gen(unit_id="CC_REGULAR_SP15_p2_peak", plant_group="CC_REGULAR"),
    ]


def _surface(tmp_path, edges=(0.8, 0.9, 0.97), tight_mult=30.0):
    """Loose bins at the resolved peak (2.0); tightest bin's top rung raised."""
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
        "CC_REGULAR": {"base_hr": 7.4, "peak_p50": 2.0, "binned_ladder": ladder},
    }
    p = tmp_path / "caiso_surface.json"
    p.write_text(json.dumps(obj))
    return str(p)


def _config(tmp_path, **over):
    base = dict(
        iso="CAISO",
        caiso_offer_surface_conditional=True,
        caiso_offer_surface_binned_path=_surface(tmp_path),
        caiso_offer_surface_netload_pcts=(0.8, 0.9, 0.97),
        caiso_offer_surface_min_bin=0,
        caiso_offer_surface_price_cap_frac=0.95,
        voll=5000.0,
        offer_curve_by_group={
            "CT_PEAKER": {"peak": 2.0},
            "CC_REGULAR": {"peak": 2.0},
        },
    )
    base.update(over)
    return SimpleNamespace(**base)


def _net_load():
    nl = np.linspace(1000.0, 2000.0, T)
    nl[-2:] = 10_000.0
    return nl


def test_off_or_wrong_iso_is_none(tmp_path):
    fa, gens = _fleet(3), _gens()
    fuel = np.full((3, T), 3.0)
    cfg = _config(tmp_path, caiso_offer_surface_conditional=False)
    assert (
        build_caiso_offer_surface_conditional_markup(fa, gens, fuel, _net_load(), cfg)
        is None
    )
    cfg = _config(tmp_path, iso="ERCOT")
    assert (
        build_caiso_offer_surface_conditional_markup(fa, gens, fuel, _net_load(), cfg)
        is None
    )


def test_tight_bin_reprices_top_rung_only(tmp_path):
    fa, gens = _fleet(3), _gens()
    fuel = np.full((3, T), 3.0)
    cfg = _config(tmp_path)
    nl = _net_load()
    m = build_caiso_offer_surface_conditional_markup(fa, gens, fuel, nl, cfg)
    assert m is not None
    # Bin membership exactly as the mechanism computes it.
    thresholds = np.quantile(nl, (0.8, 0.9, 0.97))
    tight = np.searchsorted(thresholds, nl, side="right") == 3
    assert tight.sum() >= 2
    # Loose hours: zero markup everywhere (ladder == resolved peak).
    assert np.allclose(m[:, ~tight], 0.0)
    # Tight hours: the CT peak5 rung (rung 4) reprices from 2.0 to 30.0 —
    # markup = HR x fuel x (30/2 - 1) = 10 x 3 x 14 = 420.
    assert np.allclose(m[1, tight], 420.0)
    # Rung 0 rows hold the body multiplier in the tight bin (ratio 1).
    assert np.allclose(m[0, tight], 0.0)
    assert np.allclose(m[2, tight], 0.0)


def test_edges_mismatch_raises(tmp_path):
    fa, gens = _fleet(3), _gens()
    fuel = np.full((3, T), 3.0)
    cfg = _config(tmp_path, caiso_offer_surface_netload_pcts=(0.7, 0.9, 0.97))
    with pytest.raises(ValueError, match="netload_pcts"):
        build_caiso_offer_surface_conditional_markup(fa, gens, fuel, _net_load(), cfg)


def test_static_measured_bands_replace_fitted(tmp_path, monkeypatch):
    """caiso_offer_surface_measured swaps econ/peak mults, keeps committed."""
    import sys

    from market_sim.config import paths as paths_mod
    import market_sim.pipeline.backcast_config  # noqa: F401 — bind the module

    bc_mod = sys.modules["market_sim.pipeline.backcast_config"]

    measured = {
        "_provenance": {"note": "test fixture"},
        "CC_REGULAR": {
            "base_hr": 7.44,
            "bands": {"econ_low": 0.88, "econ_high": 1.05, "peak": 1.9},
            "unarmed": {"committed": 0.55},
        },
        "CT_PEAKER": {
            "base_hr": 10.86,
            "bands": {"econ_low": 1.01, "econ_high": 1.18, "peak": 2.6},
            "unarmed": {"committed": 0.7},
        },
    }
    (tmp_path / "caiso_offer_curve_measured.json").write_text(json.dumps(measured))
    monkeypatch.setattr(paths_mod, "CALIBRATION_DIR", tmp_path)

    base = bc_mod.backcast_config(2024, "CAISO", 24, 3.5)
    cfg = bc_mod.backcast_config(
        2024, "CAISO", 24, 3.5, caiso_offer_surface_measured=True
    )
    for cls in ("CC_REGULAR", "CT_PEAKER"):
        got = cfg.offer_curve_by_group[cls]
        want = measured[cls]["bands"]
        for band in ("econ_low", "econ_high", "peak"):
            assert got[band] == want[band], (cls, band)
        # committed band and share geometry untouched (unarmed by design).
        was = base.offer_curve_by_group[cls]
        assert got["committed"] == was["committed"]
        assert got["econ_low_share"] == was["econ_low_share"]
        assert got["pct_peaking"] == was["pct_peaking"]
    assert cfg.caiso_offer_surface_measured is True
    assert base.caiso_offer_surface_measured is False
