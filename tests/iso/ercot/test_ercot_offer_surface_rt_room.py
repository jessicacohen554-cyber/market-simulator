"""Trivial-case tests for the ercot-242 room-axis extension of the RT wall.

Covers the ``ercot_offer_surface_cleared_share_rt_room`` gate of
:func:`market_sim.data.fleet.build_ercot_offer_surface_cleared_share_markup`
(PRECOMMIT-ercot242-room-axis-phase1-2026-08-30.md §1.3): room-without-rt /
room-without-wall / vintage-tag / parent-ladder-drift hard errors; the
measured room cell replacing the RT ladder read ONLY at hours whose embedded
measured room bin and cell exist (NaN-room hours and unmeasured cells keep
the incumbent RT basis byte-identical); year-scoping (a year absent from the
room artifact is byte-identical to the RT-armed wall); the per-cell position
tail riding through the same ``_positiontail_xy`` read when the position-tail
gate is armed. Plus artifact-level checks on the committed derive output:
parent ladders byte-identical to the frozen stepped artifact, the vintage
tag, and the embedded hourly room-bin index.
"""

import json

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    build_ercot_offer_surface_cleared_share_markup,
)
from tests.helpers import REPO_ROOT

T = 48
REPO = REPO_ROOT

ROOM_TAG = "room-binned-rtolcap-pct"


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


def _dam_surface(tmp_path):
    surf = {
        "_provenance": {"netload_pct_edges": [0.5], "ladder_quantiles": [0.1, 0.9]},
        "CC": {
            "years": {
                "2024": {
                    "cleared_share": [0.5, 0.5],
                    "ladder": [[[0.1, 20.0], [0.9, 30.0]]] * 2,
                }
            }
        },
    }
    p = tmp_path / "surface_dam.json"
    p.write_text(json.dumps(surf))
    return str(p)


RT_MULTS = ((100.0, 200.0), (100.0, 200.0))


def _rt_surface(tmp_path):
    surf = {
        "_provenance": {"netload_pct_edges": [0.5], "ladder_quantiles": [0.1, 0.9]},
        "CC": {
            "years": {
                "2024": {"ladder": [[[0.1, m[0]], [0.9, m[1]]] for m in RT_MULTS]}
            }
        },
    }
    p = tmp_path / "surface_rt.json"
    p.write_text(json.dumps(surf))
    return str(p)


def _room_bins_hourly():
    """(T,) embedded room-bin index: NaN / tight(0) / loose(1) by quarter.

    Bin-0 hours (first half of the T net-load ramp): quarters 1-2 = room bin
    -1 (NaN) then 0; bin-1 hours: quarters 3-4 = room bin 0 then 1.
    """
    rb = np.full(T, -1, dtype=int)
    rb[T // 4 : T // 2] = 0
    rb[T // 2 : 3 * T // 4] = 0
    rb[3 * T // 4 :] = 1
    return rb


def _room_surface(
    tmp_path,
    parent=RT_MULTS,
    year="2024",
    tag=ROOM_TAG,
    cells=None,
    tails=None,
):
    """Room artifact: 2 nl bins x 2 room bins; cells[b][r] = (lo, hi) | None."""
    if cells is None:
        # tight cells price 4x the RT ladder; loose cells unmeasured
        cells = [[(400.0, 800.0), None], [(400.0, 800.0), None]]
    lr = [
        [[[0.1, c[0]], [0.9, c[1]]] if c is not None else None for c in row]
        for row in cells
    ]
    surf = {
        "_provenance": {
            "conditioning": tag,
            "netload_pct_edges": [0.5],
            "room_pct_edges": [0.5],
            "ladder_quantiles": [0.1, 0.9],
        },
        "room_bin_hourly": {year: [int(v) for v in _room_bins_hourly()]},
        "CC": {
            "years": {
                year: {
                    "ladder": [[[0.1, m[0]], [0.9, m[1]]] for m in parent],
                    "ladder_room": lr,
                    "tail_room": tails if tails is not None else [[[], []], [[], []]],
                }
            }
        },
    }
    p = tmp_path / "surface_room.json"
    p.write_text(json.dumps(surf))
    return str(p)


def _cfg(dam_path, rt_path=None, room_path=None, **overrides):
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
    if room_path is not None:
        kwargs.update(
            ercot_offer_surface_cleared_share_rt_room=True,
            ercot_offer_surface_cleared_share_rt_room_path=room_path,
        )
    kwargs.update(overrides)
    return ScenarioConfig(**kwargs)


def test_room_without_rt_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(
        _dam_surface(tmp_path),
        ercot_offer_surface_cleared_share_rt_room=True,
    )
    with pytest.raises(ValueError, match="no RT ladder to condition"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_room_without_wall_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = ScenarioConfig(
        iso="ERCOT",
        mode="backcast",
        weather_year=2024,
        ercot_offer_surface_cleared_share_rt_room=True,
    )
    with pytest.raises(ValueError, match="room axis has"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_vintage_tag_mismatch_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(
        _dam_surface(tmp_path),
        _rt_surface(tmp_path),
        _room_surface(tmp_path, tag="positiontail-netload-bins"),
    )
    with pytest.raises(ValueError, match="vintage mismatch"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_parent_ladder_drift_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(
        _dam_surface(tmp_path),
        _rt_surface(tmp_path),
        _room_surface(tmp_path, parent=((99.0, 200.0), (100.0, 200.0))),
    )
    with pytest.raises(ValueError, match="parent ladder does not"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_room_cell_replaces_only_measured_room_hours(tmp_path):
    """Measured (bin, room) cells re-read the ladder; NaN-room hours don't."""
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_dam_surface(tmp_path), _rt_surface(tmp_path)), 2024
    )
    m = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(
            _dam_surface(tmp_path),
            _rt_surface(tmp_path),
            _room_surface(tmp_path),
        ),
        2024,
    )
    assert base is not None and m is not None
    rb = _room_bins_hourly()
    # NaN-room hours (first quarter): byte-identical to the RT-armed wall.
    np.testing.assert_array_equal(m[1][rb < 0], base[1][rb < 0])
    # tight-room hours (room bin 0, measured cells at 4x): strictly above.
    assert (m[1][rb == 0] > base[1][rb == 0]).all()
    # loose-room hours (room bin 1, cell unmeasured): incumbent RT retained.
    np.testing.assert_array_equal(m[1][rb == 1], base[1][rb == 1])
    # exact target at a tight hour: interp(rel, ., [400, 800]) vs [100, 200].
    rel = (0.675 - 0.5) / 0.5
    cell_mult = np.interp(rel, [0.1, 0.9], [400.0, 800.0])
    rt_mult = np.interp(rel, [0.1, 0.9], [100.0, 200.0])
    tight = rb == 0
    np.testing.assert_allclose(
        (m[1][tight] + mc[1][tight]) / (base[1][tight] + mc[1][tight]),
        cell_mult / rt_mult,
        rtol=1e-12,
    )


def test_room_year_scoped_no_pooled_fallback(tmp_path):
    """A year absent from the room artifact is byte-identical to RT-armed."""
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_dam_surface(tmp_path), _rt_surface(tmp_path)), 2024
    )
    m = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(
            _dam_surface(tmp_path),
            _rt_surface(tmp_path),
            _room_surface(tmp_path, year="2023"),
        ),
        2024,
    )
    assert base is not None and m is not None
    np.testing.assert_array_equal(m, base)


def test_room_cell_tail_rides_positiontail_read(tmp_path):
    """With the position-tail gate armed, a cell's own tail extends its read.

    The econ row sits at rel 0.35 (below the 0.9 grid top), so a cell tail
    must NOT move it; the peak-row scope is untouched by construction, so the
    tail's reachable effect here is zero — asserted byte-identical, which is
    exactly the ercot-181 zero-support/sub-p90 invariant on the room leg.
    """
    fa, gens, mc, nl = _fleet()
    # RT artifact must be the positiontail vintage when the pt gate is armed.
    rt_surf = {
        "_provenance": {
            "conditioning": "positiontail-netload-bins",
            "netload_pct_edges": [0.5],
            "ladder_quantiles": [0.1, 0.9],
        },
        "CC": {
            "years": {
                "2024": {
                    "ladder": [[[0.1, m[0]], [0.9, m[1]]] for m in RT_MULTS],
                    "tail": [[], []],
                }
            }
        },
    }
    rt_path = tmp_path / "surface_rt_pt.json"
    rt_path.write_text(json.dumps(rt_surf))
    kw = dict(ercot_offer_surface_position_tail=True)
    base = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(
            _dam_surface(tmp_path),
            str(rt_path),
            _room_surface(tmp_path),
            **kw,
        ),
        2024,
    )
    with_tails = build_ercot_offer_surface_cleared_share_markup(
        fa,
        gens,
        mc,
        nl,
        _cfg(
            _dam_surface(tmp_path),
            str(rt_path),
            _room_surface(
                tmp_path,
                tails=[[[[0.95, 5000.0]], []], [[[0.95, 5000.0]], []]],
            ),
            **kw,
        ),
        2024,
    )
    assert base is not None and with_tails is not None
    np.testing.assert_array_equal(with_tails, base)


def test_room_refuses_span_and_grain(tmp_path):
    fa, gens, mc, nl = _fleet()
    with pytest.raises(ValueError, match="undeclared composition"):
        build_ercot_offer_surface_cleared_share_markup(
            fa,
            gens,
            mc,
            nl,
            _cfg(
                _dam_surface(tmp_path),
                _rt_surface(tmp_path),
                _room_surface(tmp_path),
                ercot_shoulder_online_span=True,
                ercot_faststart_pool_offer=True,
            ),
            2024,
        )
    with pytest.raises(ValueError, match="one vintage per family"):
        build_ercot_offer_surface_cleared_share_markup(
            fa,
            gens,
            mc,
            nl,
            _cfg(
                _dam_surface(tmp_path),
                _rt_surface(tmp_path),
                _room_surface(tmp_path),
                ercot_offer_surface_continuous=True,
            ),
            2024,
        )


COMMITTED_ROOM = (
    REPO / "data/raw/_validation-source/ercot_sced_offer_wall_roombinned.json"
)
COMMITTED_STEPPED = (
    REPO / "data/raw/_validation-source/ercot_sced_offer_wall_condbinned.json"
)


@pytest.mark.skipif(not COMMITTED_ROOM.exists(), reason="room artifact not derived yet")
def test_committed_artifact_parent_identity_and_shape():
    """The committed room artifact anchors byte-exactly on the frozen wall."""
    room = json.loads(COMMITTED_ROOM.read_text())
    frozen = json.loads(COMMITTED_STEPPED.read_text())
    prov = room["_provenance"]
    assert prov["conditioning"] == ROOM_TAG
    assert prov["netload_pct_edges"] == frozen["_provenance"]["netload_pct_edges"]
    assert prov["ladder_quantiles"] == frozen["_provenance"]["ladder_quantiles"]
    assert prov["room_pct_edges"] == [0.02, 0.05, 0.10, 0.175, 0.30, 0.50, 0.70]
    n_room = len(prov["room_pct_edges"]) + 1
    n_bins = len(prov["netload_pct_edges"]) + 1
    for year, series in room["room_bin_hourly"].items():
        assert len(series) == 8760
        assert min(series) >= -1 and max(series) < n_room
    for cls in ("CC", "CT"):
        for year, tbl in room[cls]["years"].items():
            assert tbl["ladder"] == frozen[cls]["years"][year]["ladder"]
            assert len(tbl["ladder_room"]) == n_bins
            assert all(len(row) == n_room for row in tbl["ladder_room"])
            assert len(tbl["tail_room"]) == n_bins
    assert "ST" not in room and "ST_GAS" not in room  # rule 19 scope
