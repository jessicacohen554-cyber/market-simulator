"""Trivial-case tests for the ERCOT-86 RT/SCED-basis cleared-share wall.

Covers the ``ercot_offer_surface_cleared_share_rt`` gate of
:func:`market_sim.data.fleet.build_ercot_offer_surface_cleared_share_markup`:
rt-without-wall / bad-mode / bin-geometry-mismatch hard errors, composition A
("replace": RT-measured bins swap the ladder source — even downward; unmeasured
bins keep the DAM basis), composition B ("tier": floor at max(state-weighted
DAM, RT)), year-scoping (a year absent from the RT artifact is byte-identical
to the DAM-basis wall — no pooled fallback), the no-state-weight-on-RT
invariant, VOLL capping, and row scoping (peak/committed rows never touched).
Plus artifact-level checks on the committed derive outputs: shared bin
geometry, and the RT mid-band upper rungs standing above the DAM ladder for
the CT class that carries the $150-800 surface.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    build_ercot_offer_surface_cleared_share_markup,
)

T = 48
REPO = Path(__file__).resolve().parents[1]


class _FA:
    """Minimal FleetArrays stand-in (the builder only reads ``pmax``)."""

    def __init__(self, pmax):
        self.pmax = np.asarray(pmax, dtype=float)


def _gen(unit_id: str, pmax: float, hr: float, group: str = "CC_REGULAR"):
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="Z",
        fuel_type="gas_cc",
        efficiency_bin=group,
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=hr,
        vom=2.0,
        emission_rate_co2=0.4,
        nox_rate=0.1,
        eford=0.05,
        online_year=2000,
        plant_group=group,
        plant_code=1,
    )


def _fleet():
    """One CC plant: committed 50 / econhi 35 / peak 15 (mids .25/.675/.925)."""
    gens = [
        _gen("p1_committed", 50.0, 7.0),
        _gen("p1_econhi", 35.0, 9.0),
        _gen("p1_peak", 15.0, 30.0),
    ]
    fa = _FA([g.pmax_mw for g in gens])
    mc = np.vstack([np.full(T, 15.0), np.full(T, 25.0), np.full(T, 80.0)])
    net_load = np.linspace(0.0, 100.0, T)  # first half bin 0, second half bin 1
    return fa, gens, mc, net_load


def _dam_surface(tmp_path, cc_shares=(0.5, 0.5), mults=((20.0, 30.0), (20.0, 30.0))):
    surf = {
        "_provenance": {
            "netload_pct_edges": [0.5],
            "ladder_quantiles": [0.1, 0.9],
        },
        "CC": {
            "years": {
                "2024": {
                    "cleared_share": list(cc_shares),
                    "ladder": [[[0.1, m[0]], [0.9, m[1]]] for m in mults],
                }
            }
        },
    }
    p = tmp_path / "surface_dam.json"
    p.write_text(json.dumps(surf))
    return str(p)


def _rt_surface(
    tmp_path,
    mults=((100.0, 200.0), (100.0, 200.0)),
    year="2024",
    edges=(0.5,),
    quantiles=(0.1, 0.9),
    cls="CC",
):
    surf = {
        "_provenance": {
            "netload_pct_edges": list(edges),
            "ladder_quantiles": list(quantiles),
        },
        cls: {
            "years": {
                year: {
                    "ladder": [
                        [[quantiles[0], m[0]], [quantiles[-1], m[1]]] for m in mults
                    ]
                }
            }
        },
    }
    p = tmp_path / "surface_rt.json"
    p.write_text(json.dumps(surf))
    return str(p)


def _cfg(dam_path, rt_path=None, **overrides):
    kwargs = dict(
        iso="ERCOT",
        mode="backcast",
        weather_year=2024,
        ercot_offer_surface_cleared_share=True,
        ercot_offer_surface_cleared_share_path=dam_path,
    )
    if rt_path is not None:
        kwargs.update(
            ercot_offer_surface_cleared_share_rt=True,
            ercot_offer_surface_cleared_share_rt_path=rt_path,
        )
    kwargs.update(overrides)
    return ScenarioConfig(**kwargs)


def test_rt_without_wall_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = ScenarioConfig(
        iso="ERCOT",
        mode="backcast",
        weather_year=2024,
        ercot_offer_surface_cleared_share_rt=True,
    )
    with pytest.raises(ValueError, match="no wall to re-price"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_bad_mode_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(
        _dam_surface(tmp_path),
        _rt_surface(tmp_path),
        ercot_offer_surface_cleared_share_rt_mode="blend",
    )
    with pytest.raises(ValueError, match="'replace'"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_geometry_mismatch_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(
        _dam_surface(tmp_path),
        _rt_surface(tmp_path, edges=(0.25, 0.5), mults=((1.0, 2.0),) * 3),
    )
    with pytest.raises(ValueError, match="bin "):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_replace_swaps_ladder_source(tmp_path):
    """Composition A: RT-measured bins price at the RT ladder, not the DAM's."""
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_dam_surface(tmp_path)), 2024
    )
    m = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_dam_surface(tmp_path), _rt_surface(tmp_path)), 2024
    )
    assert base is not None and m is not None
    # econ row (mid 0.675, boundary 0.5 -> rel 0.35): RT ladder 100..200 vs
    # DAM 20..30 — the RT floor is strictly higher everywhere it applies.
    assert (m[1] > base[1]).all()
    # exact target: interp(0.35, [.1,.9], [100,200]) = 131.25 x gas - mc
    # (gas day varies; just confirm the ratio vs the DAM target matches the
    # ladder ratio at the same rel: (131.25)/(23.125) on the target scale)
    rel = (0.675 - 0.5) / 0.5
    rt_mult = np.interp(rel, [0.1, 0.9], [100.0, 200.0])
    dam_mult = np.interp(rel, [0.1, 0.9], [20.0, 30.0])
    np.testing.assert_allclose(
        (m[1] + mc[1]) / (base[1] + mc[1]), rt_mult / dam_mult, rtol=1e-12
    )


def test_replace_applies_even_downward(tmp_path):
    """Composition A: an RT ladder BELOW the DAM one still replaces it."""
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_dam_surface(tmp_path)), 2024
    )
    m = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(_dam_surface(tmp_path), _rt_surface(tmp_path, mults=((15.0, 20.0),) * 2)),
        2024,
    )
    assert base is not None and m is not None
    assert (m[1] < base[1]).all()


def test_tier_floors_at_max(tmp_path):
    """Composition B: the floor is max(DAM, RT) elementwise."""
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_dam_surface(tmp_path)), 2024
    )
    # RT below DAM in bin 0, above it in bin 1
    rt = _rt_surface(tmp_path, mults=((1.0, 2.0), (100.0, 200.0)))
    m = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(
            _dam_surface(tmp_path),
            rt,
            ercot_offer_surface_cleared_share_rt_mode="tier",
        ),
        2024,
    )
    assert base is not None and m is not None
    # bin 0 (first half): RT lower -> DAM floor retained byte-identical
    np.testing.assert_array_equal(m[1][: T // 2], base[1][: T // 2])
    # bin 1 (second half): RT higher -> floor raised above the DAM wall
    assert (m[1][T // 2 :] > base[1][T // 2 :]).all()


def test_year_scoped_no_pooled_fallback(tmp_path):
    """A year absent from the RT artifact keeps the DAM basis byte-identical."""
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_dam_surface(tmp_path)), 2024
    )
    m = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(_dam_surface(tmp_path), _rt_surface(tmp_path, year="2025")),
        2024,
    )
    assert base is not None and m is not None
    np.testing.assert_array_equal(m, base)


def test_rt_leg_is_never_state_weighted(tmp_path):
    """The state weight scales the DAM leg only; RT bins carry the full wall."""
    fa, gens, mc, nl = _fleet()
    # state w = 0 everywhere: DAM leg dead, RT leg (bin 1 only) untouched
    state = {
        "_provenance": {"netload_pct_edges": [0.5], "hour_block_hours": 4},
        "climatology": {},
        "CC": {"years": {"2024": [0.0] * T}},
    }
    spath = tmp_path / "state.json"
    spath.write_text(json.dumps(state))
    rt = _rt_surface(tmp_path, mults=((float("nan"), float("nan")), (100.0, 200.0)))
    cfg = _cfg(
        _dam_surface(tmp_path),
        rt,
        ercot_offer_surface_cleared_share_state=True,
        ercot_offer_surface_cleared_share_state_path=str(spath),
    )
    m = build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)
    assert m is not None
    # bin 0 (no RT measurement): DAM leg state-weighted to zero -> no floor
    assert m[1][: T // 2].max() == 0.0
    # bin 1 (RT-measured): full RT wall despite w=0
    assert m[1][T // 2 :].min() > 0.0


def test_row_scoping_unchanged(tmp_path):
    """Committed and peak rows are never touched by the RT basis."""
    fa, gens, mc, nl = _fleet()
    m = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_dam_surface(tmp_path), _rt_surface(tmp_path)), 2024
    )
    assert m is not None
    assert m[0].max() == 0.0  # committed (mid 0.25 <= boundary 0.5)
    assert m[2].max() == 0.0  # peak rung (ercot_offer_surface_conditional's)


def test_rt_target_voll_capped(tmp_path):
    """An extreme RT ladder is capped at price_cap_frac x VOLL."""
    fa, gens, mc, nl = _fleet()
    m = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(_dam_surface(tmp_path), _rt_surface(tmp_path, mults=((1e6, 1e6),) * 2)),
        2024,
    )
    assert m is not None
    cap = 0.95 * 5000.0
    assert float((m[1] + mc[1]).max()) <= cap + 1e-9


# ---------------------------------------------------------------------------
# Committed-artifact checks (the real derive outputs, when present)
# ---------------------------------------------------------------------------

_RT_JSON = REPO / "data/raw/_validation-source/ercot_sced_offer_wall_condbinned.json"
_DAM_JSON = REPO / "data/raw/_validation-source/ercot_dam_cleared_share_condbinned.json"


@pytest.mark.skipif(not _RT_JSON.exists(), reason="RT artifact not derived")
def test_artifact_shares_dam_bin_geometry():
    rt = json.loads(_RT_JSON.read_text())
    dam = json.loads(_DAM_JSON.read_text())
    assert (
        rt["_provenance"]["netload_pct_edges"]
        == dam["_provenance"]["netload_pct_edges"]
    )
    assert (
        rt["_provenance"]["ladder_quantiles"] == dam["_provenance"]["ladder_quantiles"]
    )


@pytest.mark.skipif(not _RT_JSON.exists(), reason="RT artifact not derived")
def test_artifact_is_year_scoped_and_st_free():
    rt = json.loads(_RT_JSON.read_text())
    for cls in ("CC", "CT"):
        assert "pooled" not in rt.get(cls, {}), (
            "RT artifact must not carry a pooled fallback"
        )
    assert "ST" not in rt, "ST_GAS is out of RT scope (rule 19)"


@pytest.mark.skipif(not _RT_JSON.exists(), reason="RT artifact not derived")
def test_artifact_ct_midband_upper_rungs_exceed_dam():
    """The CT spare's upper rungs carry the $150-800 RT surface the DAM lacks."""
    rt = json.loads(_RT_JSON.read_text())
    dam = json.loads(_DAM_JSON.read_text())
    for year, tbl in rt["CT"]["years"].items():
        dam_tbl = dam["CT"]["years"].get(year)
        if dam_tbl is None:
            continue
        # mid-band bins (p80-p97, indices -3/-2 on the shared 7-bin geometry):
        # top rung (q90) of the RT ladder strictly above the DAM ladder's.
        for b in (-3, -2):
            assert tbl["ladder"][b][-1][1] > dam_tbl["ladder"][b][-1][1]
