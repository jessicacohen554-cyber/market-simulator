"""Trivial-case tests for the ERCOT-93 ST_GAS steam RT/SCED basis + online span.

Covers the steam leg of
:func:`market_sim.data.fleet.build_ercot_offer_surface_cleared_share_markup`:
the ``ercot_offer_surface_cleared_share_rt_steam_path`` (the "ST" class priced
from its OWN measured SCED online-spare ladder, rule 19 — the CC/CT RT artifact
stays ST-free) and ``ercot_shoulder_online_span_steam`` (the telemetered
ON-share conditional re-anchors the steam wall geometry over [boundary, span]),
plus the guards (span-without-steam+rt, span/steam-without-wall), the steam RT
geometry-mismatch hard error, the above-span ladder-top clamp, and the flag-off
byte-identical invariant. Plus committed-artifact checks: shared bin geometry
across the three ST artifacts and the RT steam mid-band upper rungs standing
above the DAM ST ladder.
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
    def __init__(self, pmax):
        self.pmax = np.asarray(pmax, dtype=float)


def _gen(unit_id, pmax, hr, group="ST_GAS"):
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="Z",
        fuel_type="gas_st",
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
    """One ST_GAS plant: committed 50 / econhi 35 / peak 15 (mids .25/.675/.925)."""
    gens = [
        _gen("st1_committed", 50.0, 8.0),
        _gen("st1_econhi", 35.0, 11.0),
        _gen("st1_peak", 15.0, 30.0),
    ]
    fa = _FA([g.pmax_mw for g in gens])
    mc = np.vstack([np.full(T, 18.0), np.full(T, 28.0), np.full(T, 80.0)])
    net_load = np.linspace(0.0, 100.0, T)  # first half bin 0, second half bin 1
    return fa, gens, mc, net_load


def _dam_surface(tmp_path, boundary=(0.5, 0.5), mults=((20.0, 30.0), (20.0, 30.0))):
    """A DAM cleared-share surface carrying an ST boundary + ladder."""
    surf = {
        "_provenance": {"netload_pct_edges": [0.5], "ladder_quantiles": [0.1, 0.9]},
        "ST": {
            "years": {
                "2024": {
                    "cleared_share": list(boundary),
                    "ladder": [[[0.1, m[0]], [0.9, m[1]]] for m in mults],
                }
            }
        },
    }
    p = tmp_path / "surface_dam_st.json"
    p.write_text(json.dumps(surf))
    return str(p)


def _rt_steam(
    tmp_path,
    mults=((100.0, 200.0), (100.0, 200.0)),
    year="2024",
    edges=(0.5,),
    quantiles=(0.1, 0.9),
):
    surf = {
        "_provenance": {
            "netload_pct_edges": list(edges),
            "ladder_quantiles": list(quantiles),
        },
        "ST": {
            "years": {
                year: {
                    "ladder": [
                        [[quantiles[0], m[0]], [quantiles[-1], m[1]]] for m in mults
                    ]
                }
            }
        },
    }
    p = tmp_path / "rt_steam.json"
    p.write_text(json.dumps(surf))
    return str(p)


def _span_steam(tmp_path, span_by_bin=(0.4, 0.4), year="2024", edges=(0.5,)):
    """Steam span artifact: (n_bins, 4 seasons, 6 blocks) constant ST table."""
    n_bins = len(edges) + 1
    table = [[[float(span_by_bin[b])] * 6 for _s in range(4)] for b in range(n_bins)]
    surf = {
        "_provenance": {
            "netload_pct_edges": list(edges),
            "season_of_month": [0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0],
            "hour_block_hours": 4,
        },
        "ST": {"years": {year: {"span": table}}},
    }
    p = tmp_path / "span_steam.json"
    p.write_text(json.dumps(surf))
    return str(p)


def _cfg(dam_path, steam=True, rt_steam=None, span_steam=None, **overrides):
    kwargs = dict(
        iso="ERCOT",
        mode="backcast",
        weather_year=2024,
        ercot_offer_surface_cleared_share=True,
        ercot_offer_surface_cleared_share_path=dam_path,
        ercot_offer_surface_cleared_share_steam=steam,
    )
    if rt_steam is not None:
        kwargs.update(
            ercot_offer_surface_cleared_share_rt=True,
            ercot_offer_surface_cleared_share_rt_steam_path=rt_steam,
            # point the CC/CT RT path at the same file so only the steam leg loads
            ercot_offer_surface_cleared_share_rt_path=rt_steam,
        )
    if span_steam is not None:
        kwargs.update(
            ercot_shoulder_online_span_steam=True,
            ercot_shoulder_online_span_steam_path=span_steam,
        )
    kwargs.update(overrides)
    return ScenarioConfig(**kwargs)


def test_steam_rt_basis_engages(tmp_path):
    """The ST econ row prices at the steam RT ladder, not the DAM ST ladder."""
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_dam_surface(tmp_path)), 2024
    )
    m = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(_dam_surface(tmp_path), rt_steam=_rt_steam(tmp_path)),
        2024,
    )
    assert base is not None and m is not None
    # econ row (mid 0.675, boundary 0.5 -> rel 0.35): RT ladder 100..200 far
    # above the DAM 20..30 -> the steam RT floor raises the offer.
    assert (m[1] > base[1]).all()
    rel = (0.675 - 0.5) / 0.5
    rt_mult = np.interp(rel, [0.1, 0.9], [100.0, 200.0])
    dam_mult = np.interp(rel, [0.1, 0.9], [20.0, 30.0])
    np.testing.assert_allclose(
        (m[1] + mc[1]) / (base[1] + mc[1]), rt_mult / dam_mult, rtol=1e-9
    )


def test_steam_committed_row_priced(tmp_path):
    """With a low boundary the committed ST tranche is walled too (the leg-c defect)."""
    fa, gens, mc, nl = _fleet()
    m = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(_dam_surface(tmp_path, boundary=(0.1, 0.1)), rt_steam=_rt_steam(tmp_path)),
        2024,
    )
    assert m is not None
    assert m[0].max() > 0.0  # committed (mid 0.25) is above boundary 0.1 -> walled
    assert m[2].max() == 0.0  # peak rung never touched


def test_steam_span_anchors_geometry(tmp_path):
    """A tight span raises rel -> the ST econ row prices higher up the ladder."""
    fa, gens, mc, nl = _fleet()
    no_span = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(_dam_surface(tmp_path), rt_steam=_rt_steam(tmp_path)),
        2024,
    )
    # span 0.7 (> boundary 0.5): rel = (0.675-0.5)/(0.7-0.5) = 0.875 > full-span 0.35
    with_span = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(
            _dam_surface(tmp_path),
            rt_steam=_rt_steam(tmp_path),
            span_steam=_span_steam(tmp_path, span_by_bin=(0.7, 0.7)),
        ),
        2024,
    )
    assert no_span is not None and with_span is not None
    # higher rel -> higher up the rising RT ladder -> larger markup on the econ row.
    assert (with_span[1] >= no_span[1]).all()
    assert with_span[1].max() > no_span[1].max()


def test_steam_span_above_span_clamps_ladder_top(tmp_path):
    """A row above the span takes the ladder top (rel=1), the slow-row rule."""
    fa, gens, mc, nl = _fleet()
    # span 0.6: econ mid 0.675 > span 0.6 -> above span -> rel=1 -> ladder top (200)
    m = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(
            _dam_surface(tmp_path),
            rt_steam=_rt_steam(tmp_path),
            span_steam=_span_steam(tmp_path, span_by_bin=(0.6, 0.6)),
        ),
        2024,
    )
    assert m is not None
    below_top = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(
            _dam_surface(tmp_path),
            rt_steam=_rt_steam(tmp_path),
            span_steam=_span_steam(tmp_path, span_by_bin=(0.7, 0.7)),
        ),
        2024,
    )
    assert (m[1] >= below_top[1]).all()


def test_span_steam_without_steam_and_rt_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(
        _dam_surface(tmp_path),
        span_steam=_span_steam(tmp_path),  # arms span but NOT rt
    )
    with pytest.raises(ValueError, match="arm ercot_offer_surface_cleared_"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_span_steam_without_wall_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = ScenarioConfig(
        iso="ERCOT",
        mode="backcast",
        weather_year=2024,
        ercot_shoulder_online_span_steam=True,
    )
    with pytest.raises(ValueError, match="no wall to re-anchor"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_steam_rt_geometry_mismatch_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(
        _dam_surface(tmp_path),
        rt_steam=_rt_steam(tmp_path, edges=(0.25, 0.5), mults=((1.0, 2.0),) * 3),
    )
    with pytest.raises(ValueError, match="geometry"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_steam_flags_off_byte_identical(tmp_path):
    """Steam RT + span OFF -> identical to the plain DAM-basis steam wall."""
    fa, gens, mc, nl = _fleet()
    a = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_dam_surface(tmp_path)), 2024
    )
    b = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_dam_surface(tmp_path)), 2024
    )
    assert a is not None and b is not None
    np.testing.assert_array_equal(a, b)


def test_steam_rt_year_scoped(tmp_path):
    """A year absent from the steam RT artifact keeps the DAM ST basis."""
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_dam_surface(tmp_path)), 2024
    )
    m = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(_dam_surface(tmp_path), rt_steam=_rt_steam(tmp_path, year="2025")),
        2024,
    )
    assert base is not None and m is not None
    np.testing.assert_array_equal(m, base)


# ---------------------------------------------------------------------------
# Committed-artifact checks (the real derive outputs, when present)
# ---------------------------------------------------------------------------

_VS = REPO / "data/raw/_validation-source"
_RT_STEAM = _VS / "ercot_sced_offer_wall_steam_condbinned.json"
_SPAN_STEAM = _VS / "ercot_shoulder_online_span_steam_condbinned.json"
_DAM = _VS / "ercot_dam_cleared_share_condbinned.json"


@pytest.mark.skipif(not _RT_STEAM.exists(), reason="steam RT artifact not derived")
def test_steam_artifacts_share_dam_bin_geometry():
    rt = json.loads(_RT_STEAM.read_text())
    dam = json.loads(_DAM.read_text())
    assert (
        rt["_provenance"]["netload_pct_edges"]
        == dam["_provenance"]["netload_pct_edges"]
    )
    assert (
        rt["_provenance"]["ladder_quantiles"] == dam["_provenance"]["ladder_quantiles"]
    )
    if _SPAN_STEAM.exists():
        span = json.loads(_SPAN_STEAM.read_text())
        assert (
            span["_provenance"]["netload_pct_edges"]
            == dam["_provenance"]["netload_pct_edges"]
        )


@pytest.mark.skipif(not _RT_STEAM.exists(), reason="steam RT artifact not derived")
def test_steam_rt_midband_upper_rungs_exceed_dam_st():
    """The RT steam spare's upper rungs carry the surface the DAM ST ladder lacks."""
    rt = json.loads(_RT_STEAM.read_text())
    dam = json.loads(_DAM.read_text())
    for year, tbl in rt["ST"]["years"].items():
        dam_tbl = dam["ST"]["years"].get(year)
        if dam_tbl is None:
            continue
        for b in (-3, -2):
            assert tbl["ladder"][b][-1][1] > dam_tbl["ladder"][b][-1][1]
