"""Trivial-case tests for the ERCOT-89 shoulder online-span anchor.

Covers the ``ercot_shoulder_online_span`` gate across its two seams
(:func:`market_sim.data.fleet.build_ercot_offer_surface_cleared_share_markup`
and :func:`market_sim.data.fleet.build_ercot_faststart_pool_markup`):
span-without-wall / span-without-RT / span-without-pool hard errors,
bin-geometry-mismatch hard error, ladder compression (a walled row's rel
rises when the measured online span is < 1.0, so its floored bid rises —
never falls), above-span clamping at the ladder top on the wall side, the
generalized pool boundary (a row between the span and the ERCOT-88 static
pool boundary becomes pool-owned), span == 1.0 byte-identity, and
year-scoping (a year absent from the span artifact keeps both the wall
geometry and the static pool boundary byte-identical — no pooled fallback).
Plus artifact-level checks on the committed derive output: shared bin
geometry with the wall artifacts, year-scoped (no pooled key), spans in
[0, 1], resolution levels in {0..3}, and a 12-month season map.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    build_ercot_faststart_pool_markup,
    build_ercot_offer_surface_cleared_share_markup,
)

T = 48
REPO = Path(__file__).resolve().parents[1]


class _FA:
    """Minimal FleetArrays stand-in (the builders only read ``pmax``)."""

    def __init__(self, pmax):
        self.pmax = np.asarray(pmax, dtype=float)


def _gen(
    unit_id: str,
    pmax: float,
    hr: float,
    group: str = "CT_PEAKER",
    min_down: int = 1,
):
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="Z",
        fuel_type="gas_ct",
        efficiency_bin=group,
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=hr,
        vom=2.0,
        emission_rate_co2=0.5,
        nox_rate=0.1,
        eford=0.05,
        online_year=2000,
        plant_group=group,
        plant_code=1,
        min_down_hours=min_down,
    )


def _fleet(peak_min_down: int = 1):
    """One CT plant: committed 30 / econ 30 / econhi 40 (mids .15/.45/.80)."""
    gens = [
        _gen("p1_committed", 30.0, 7.0),
        _gen("p1_econ", 30.0, 9.0),
        _gen("p1_econhi", 40.0, 10.0, min_down=peak_min_down),
    ]
    fa = _FA([g.pmax_mw for g in gens])
    mc = np.vstack([np.full(T, 15.0), np.full(T, 25.0), np.full(T, 30.0)])
    net_load = np.linspace(0.0, 100.0, T)  # first half bin 0, second half bin 1
    return fa, gens, mc, net_load


def _dam_surface(tmp_path, shares=(0.3, 0.3), mults=((10.0, 20.0), (10.0, 20.0))):
    surf = {
        "_provenance": {
            "netload_pct_edges": [0.5],
            "ladder_quantiles": [0.1, 0.9],
        },
        "CT": {
            "years": {
                "2024": {
                    "cleared_share": list(shares),
                    "ladder": [[[0.1, m[0]], [0.9, m[1]]] for m in mults],
                }
            }
        },
    }
    p = tmp_path / "surface_dam.json"
    p.write_text(json.dumps(surf))
    return str(p)


def _rt_surface(tmp_path, mults=((10.0, 100.0), (10.0, 100.0))):
    surf = {
        "_provenance": {
            "netload_pct_edges": [0.5],
            "ladder_quantiles": [0.1, 0.9],
        },
        "CT": {
            "years": {
                "2024": {
                    "ladder": [[[0.1, m[0]], [0.9, m[1]]] for m in mults],
                }
            }
        },
    }
    p = tmp_path / "surface_rt.json"
    p.write_text(json.dumps(surf))
    return str(p)


def _pool_surface(tmp_path, pool_frac=(0.2, 0.2), mults=((300.0, 500.0),) * 2):
    surf = {
        "_provenance": {
            "netload_pct_edges": [0.5],
            "ladder_quantiles": [0.1, 0.9],
        },
        "CT": {
            "years": {
                "2024": {
                    "pool_frac": list(pool_frac),
                    "ladder": [[[0.1, m[0]], [0.9, m[1]]] for m in mults],
                }
            }
        },
    }
    p = tmp_path / "surface_pool.json"
    p.write_text(json.dumps(surf))
    return str(p)


def _span_surface(
    tmp_path,
    span_val=0.7,
    year="2024",
    edges=(0.5,),
    cls="CT",
    name="surface_span.json",
):
    n_bins = len(edges) + 1
    mat = [[[span_val] * 6 for _ in range(4)] for _ in range(n_bins)]
    surf = {
        "_provenance": {
            "netload_pct_edges": list(edges),
            "season_of_month": [0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0],
            "hour_block_hours": 4,
            "min_cell_hours": 6,
        },
        cls: {
            "years": {
                year: {
                    "span": mat,
                    "level": [[[0] * 6] * 4] * n_bins,
                    "n_obs": [[[10] * 6] * 4] * n_bins,
                }
            }
        },
    }
    p = tmp_path / name
    p.write_text(json.dumps(surf))
    return str(p)


def _cfg(tmp_path, span_path=None, **overrides):
    kwargs = dict(
        iso="ERCOT",
        mode="backcast",
        weather_year=2024,
        ercot_offer_surface_cleared_share=True,
        ercot_offer_surface_cleared_share_path=_dam_surface(tmp_path),
        ercot_offer_surface_cleared_share_rt=True,
        ercot_offer_surface_cleared_share_rt_path=_rt_surface(tmp_path),
        ercot_faststart_pool_offer=True,
        ercot_faststart_pool_offer_path=_pool_surface(tmp_path),
    )
    if span_path is not None:
        kwargs.update(
            ercot_shoulder_online_span=True,
            ercot_shoulder_online_span_path=span_path,
        )
    kwargs.update(overrides)
    return ScenarioConfig(**kwargs)


def test_span_without_wall_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = ScenarioConfig(
        iso="ERCOT",
        mode="backcast",
        weather_year=2024,
        ercot_shoulder_online_span=True,
    )
    with pytest.raises(ValueError, match="no wall geometry to re-anchor"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_span_without_rt_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(
        tmp_path,
        span_path=_span_surface(tmp_path),
        ercot_offer_surface_cleared_share_rt=False,
    )
    with pytest.raises(ValueError, match="re-anchor"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_span_without_pool_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(
        tmp_path,
        span_path=_span_surface(tmp_path),
        ercot_faststart_pool_offer=False,
    )
    with pytest.raises(ValueError, match="faststart_pool"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_span_geometry_mismatch_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    span = _span_surface(tmp_path, edges=(0.25, 0.5))
    cfg = _cfg(tmp_path, span_path=span)
    with pytest.raises(ValueError, match="edges"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_span_compression_raises_walled_bids(tmp_path):
    """span 0.7: the in-span econ row's rel rises (0.214 -> 0.375), and the
    above-span econhi row clamps at the ladder top — both bids RISE, the
    below-boundary committed row stays untouched."""
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(tmp_path), 2024
    )
    span = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(tmp_path, span_path=_span_surface(tmp_path)), 2024
    )
    assert base is not None and span is not None
    # committed row: outside the wall's econ* family — untouched either way.
    assert base[0].max() == 0.0 and span[0].max() == 0.0
    # econ row (mid .45, in-span): compressed rel -> strictly higher floor.
    assert (span[1] > base[1]).all()
    # econhi row (mid .80 > span .7): ladder-top clamp >= its stretched rel.
    assert (span[2] >= base[2]).all() and span[2].mean() > base[2].mean()


def test_span_one_is_byte_identical(tmp_path):
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(tmp_path), 2024
    )
    span = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(tmp_path, span_path=_span_surface(tmp_path, span_val=1.0)),
        2024,
    )
    assert base is not None and span is not None
    np.testing.assert_array_equal(base, span)


def test_span_year_absent_is_byte_identical(tmp_path):
    """Year-scoping (rule 13): 2024 solve against a 2025-only span artifact
    keeps the wall geometry AND the static pool boundary byte-identical."""
    fa, gens, mc, nl = _fleet()
    span_2025 = _span_surface(tmp_path, year="2025")
    base_wall = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(tmp_path), 2024
    )
    span_wall = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(tmp_path, span_path=span_2025), 2024
    )
    np.testing.assert_array_equal(base_wall, span_wall)
    base_pool = build_ercot_faststart_pool_markup(
        fa, gens, mc, nl, _cfg(tmp_path), 2024
    )
    span_pool = build_ercot_faststart_pool_markup(
        fa, gens, mc, nl, _cfg(tmp_path, span_path=span_2025), 2024
    )
    assert (base_pool is None) == (span_pool is None)
    if base_pool is not None:
        np.testing.assert_array_equal(base_pool[0], span_pool[0])
        np.testing.assert_array_equal(base_pool[1], span_pool[1])


def test_pool_boundary_generalizes_to_span(tmp_path):
    """A row between the span (0.7) and the ERCOT-88 static boundary (0.8)
    is pool-owned ONLY under the span gate."""
    fa, gens, mc, nl = _fleet()  # econhi mid .80... use a .75-mid row instead
    gens = [
        _gen("p1_econ", 70.0, 9.0),  # mid .35
        _gen("p1_econhi", 10.0, 10.0),  # mid .75: between span .7 and 1-frac .8
        _gen("p1_peak", 20.0, 12.0),  # mid .90: above both boundaries
    ]
    fa = _FA([g.pmax_mw for g in gens])
    mc = np.vstack([np.full(T, 25.0), np.full(T, 30.0), np.full(T, 40.0)])
    nl = np.linspace(0.0, 100.0, T)
    static = build_ercot_faststart_pool_markup(fa, gens, mc, nl, _cfg(tmp_path), 2024)
    spand = build_ercot_faststart_pool_markup(
        fa, gens, mc, nl, _cfg(tmp_path, span_path=_span_surface(tmp_path)), 2024
    )
    assert static is not None and spand is not None
    # static boundary 0.8: the .75-mid row is NOT owned; span 0.7: it IS.
    assert not static[1][1].any()
    assert spand[1][1].all()
    assert (spand[0][1] > 0.0).all()
    # the .90-mid row is owned under both boundaries.
    assert static[1][2].all() and spand[1][2].all()


def test_pool_span_physics_gate_still_applies(tmp_path):
    """A min_down > 2h row above the span is never pool-owned (rule 12) —
    it stays with the wall's ladder-top clamp."""
    gens = [
        _gen("p1_econ", 70.0, 9.0),
        _gen("p1_econhi", 30.0, 10.0, min_down=4),  # slow: fails the gate
    ]
    fa = _FA([g.pmax_mw for g in gens])
    mc = np.vstack([np.full(T, 25.0), np.full(T, 30.0)])
    nl = np.linspace(0.0, 100.0, T)
    out = build_ercot_faststart_pool_markup(
        fa, gens, mc, nl, _cfg(tmp_path, span_path=_span_surface(tmp_path)), 2024
    )
    assert out is None  # no eligible row above the span -> pool inert


# ---------------------------------------------------------------------------
# Committed-artifact checks (the real derive output, when present)
# ---------------------------------------------------------------------------

_SPAN_JSON = (
    REPO / "data/raw/_validation-source/ercot_shoulder_online_span_condbinned.json"
)
_DAM_JSON = REPO / "data/raw/_validation-source/ercot_dam_cleared_share_condbinned.json"


@pytest.mark.skipif(not _SPAN_JSON.exists(), reason="span artifact not derived")
def test_artifact_shares_wall_bin_geometry():
    span = json.loads(_SPAN_JSON.read_text())
    dam = json.loads(_DAM_JSON.read_text())
    assert (
        span["_provenance"]["netload_pct_edges"]
        == dam["_provenance"]["netload_pct_edges"]
    )
    assert len(span["_provenance"]["season_of_month"]) == 12
    assert span["_provenance"]["hour_block_hours"] > 0


@pytest.mark.skipif(not _SPAN_JSON.exists(), reason="span artifact not derived")
def test_artifact_is_year_scoped_and_sane():
    span = json.loads(_SPAN_JSON.read_text())
    n_bins = len(span["_provenance"]["netload_pct_edges"]) + 1
    for cls in ("CC", "CT"):
        assert "pooled" not in span.get(cls, {}), (
            "span artifact must not carry a pooled fallback (rule 13)"
        )
        for year, tbl in span[cls]["years"].items():
            mat = tbl["span"]
            lvl = tbl["level"]
            assert len(mat) == n_bins and len(lvl) == n_bins
            for b in range(n_bins):
                for s in range(4):
                    for k in range(len(mat[b][s])):
                        v = mat[b][s][k]
                        if v is not None:
                            assert 0.0 <= v <= 1.0, f"{cls} {year} span {v}"
                        assert -1 <= lvl[b][s][k] <= 3
