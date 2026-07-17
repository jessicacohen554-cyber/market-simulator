"""Trivial-case tests for the ERCOT-72 DAM cleared-share offer boundary.

Covers :func:`market_sim.data.fleet.build_ercot_offer_surface_cleared_share_markup`
(``ScenarioConfig.ercot_offer_surface_cleared_share``): flag/ISO gating, the
rule-19 mutual exclusion with the mid-curve belt, the within-plant share
boundary (rows at/below the bin's measured cleared share are byte-identical),
row scoping (econ* only — committed and peak rungs never touched), the
raise-only floor semantics, and the bin conditionality (a tight bin's higher
boundary shelters rows a loose bin floors).
"""

import json

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    build_ercot_offer_surface_cleared_share_markup,
)

T = 48


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


def _surface(tmp_path, cc_shares=(0.5, 0.9), mults=((20.0, 30.0), (20.0, 30.0))):
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
    p = tmp_path / "surface.json"
    p.write_text(json.dumps(surf))
    return str(p)


def _cfg(path=None, **overrides):
    return ScenarioConfig(
        iso="ERCOT",
        mode="backcast",
        weather_year=2024,
        ercot_offer_surface_cleared_share=True,
        ercot_offer_surface_cleared_share_path=path,
        **overrides,
    )


def test_flag_off_is_noop(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = ScenarioConfig(iso="ERCOT", mode="backcast", weather_year=2024)
    assert (
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)
        is None
    )


def test_non_ercot_is_noop(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = ScenarioConfig(
        iso="PJM",
        mode="backcast",
        weather_year=2024,
        ercot_offer_surface_cleared_share=True,
        ercot_offer_surface_cleared_share_path=_surface(tmp_path),
    )
    assert (
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)
        is None
    )


def test_midcurve_coarming_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(_surface(tmp_path), ercot_offer_surface_midcurve_conditional=True)
    with pytest.raises(ValueError, match="one mechanism per row"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_boundary_and_row_scoping(tmp_path):
    """Econ row above the loose-bin boundary floors; committed/peak never do."""
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(_surface(tmp_path))
    m = build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)
    assert m is not None
    # committed (mid 0.25 <= 0.5) untouched everywhere
    assert m[0].max() == 0.0
    # econ (mid 0.675): floored in bin 0 (boundary 0.5), sheltered in bin 1
    # (boundary 0.9 > mid) — the tight bin's HIGHER measured cleared share
    # shelters capacity the loose bin walls.
    assert m[1][: T // 2].min() > 0.0
    assert m[1][T // 2 :].max() == 0.0
    # peak rung (mid 0.925): never touched even where it exceeds the boundary
    # (owned by ercot_offer_surface_conditional, rule 19)
    assert m[2].max() == 0.0


def test_floor_only_raises(tmp_path):
    """A wall at/below the model bid leaves the row byte-identical."""
    fa, gens, mc, nl = _fleet()
    # wall mult 1.0x on ~$2 gas -> target ~ $2, far below the $25 econ bid
    cfg = _cfg(_surface(tmp_path, mults=((1.0, 1.0), (1.0, 1.0))))
    m = build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)
    assert m is None  # nothing floored -> byte-identical None


def test_nan_boundary_bin_is_sheltered(tmp_path):
    """A bin with no measured boundary contributes no floor."""
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(_surface(tmp_path, cc_shares=(float("nan"), 0.5)))
    m = build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)
    assert m is not None
    # bin 0 (NaN boundary): sheltered; bin 1 (boundary 0.5 < mid 0.675): floors
    assert m[1][: T // 2].max() == 0.0
    assert m[1][T // 2 :].min() > 0.0


def _state(tmp_path, year_w=None, clim=None, edges=(0.5,)):
    """Write a minimal ERCOT-73 commitment-loading state JSON."""
    entry = {}
    if year_w is not None:
        entry["years"] = {"2024": list(year_w)}
    else:
        entry["years"] = {}
    state = {
        "_provenance": {
            "netload_pct_edges": list(edges),
            "hour_block_hours": 4,
        },
        "climatology": {"CC": clim} if clim is not None else {},
        "CC": entry,
    }
    p = tmp_path / "state.json"
    p.write_text(json.dumps(state))
    return str(p)


def test_state_without_wall_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = ScenarioConfig(
        iso="ERCOT",
        mode="backcast",
        weather_year=2024,
        ercot_offer_surface_cleared_share_state=True,
    )
    with pytest.raises(ValueError, match="nothing to scope"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_state_year_series_scales_markup(tmp_path):
    """w=0 hours are un-walled; w=0.5 hours carry exactly half the markup."""
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_surface(tmp_path)), 2024
    )
    w = [0.0] * (T // 2) + [0.5] * (T // 2)
    cfg = _cfg(
        _surface(tmp_path),
        ercot_offer_surface_cleared_share_state=True,
        ercot_offer_surface_cleared_share_state_path=_state(tmp_path, year_w=w),
    )
    m = build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)
    # base floors econ row in bin 0 (first half of hours); w=0 kills it there
    assert base is not None and base[1][: T // 2].min() > 0.0
    assert m is None or m[1][: T // 2].max() == 0.0
    # second half: base has no floor there (bin-1 boundary 0.9 shelters the
    # row), and the state weight can only scale DOWN — still no floor
    if m is not None:
        assert m[1][T // 2 :].max() == 0.0


def test_state_half_weight_halves_markup(tmp_path):
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_surface(tmp_path)), 2024
    )
    cfg = _cfg(
        _surface(tmp_path),
        ercot_offer_surface_cleared_share_state=True,
        ercot_offer_surface_cleared_share_state_path=_state(tmp_path, year_w=[0.5] * T),
    )
    m = build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)
    assert m is not None
    np.testing.assert_allclose(m[1], 0.5 * base[1])


def test_state_missing_year_uses_climatology(tmp_path):
    """A year absent from the artifact falls back to the bin x block table."""
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_surface(tmp_path)), 2024
    )
    # climatology: bin 0 -> w=0.25 in every block, bin 1 -> w=1.0
    clim = [[0.25] * 6, [1.0] * 6]
    cfg = _cfg(
        _surface(tmp_path),
        ercot_offer_surface_cleared_share_state=True,
        ercot_offer_surface_cleared_share_state_path=_state(tmp_path, clim=clim),
    )
    m = build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)
    assert m is not None
    np.testing.assert_allclose(m[1][: T // 2], 0.25 * base[1][: T // 2])


def test_state_edges_mismatch_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(
        _surface(tmp_path),
        ercot_offer_surface_cleared_share_state=True,
        ercot_offer_surface_cleared_share_state_path=_state(
            tmp_path, year_w=[1.0] * T, edges=(0.25, 0.5)
        ),
    )
    with pytest.raises(ValueError, match="bin edges"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


# ---------------------------------------------------------------------------
# ERCOT-77 steam extension (ercot_offer_surface_cleared_share_steam)
# ---------------------------------------------------------------------------


def _st_fleet():
    """One ST_GAS plant: committed 40 / econc00 40 / peak 20 (mids .2/.6/.9)."""
    gens = [
        _gen("s1_committed", 40.0, 10.0, group="ST_GAS"),
        _gen("s1_econc00", 40.0, 11.0, group="ST_GAS"),
        _gen("s1_peak", 20.0, 14.0, group="ST_GAS"),
    ]
    fa = _FA([g.pmax_mw for g in gens])
    mc = np.vstack([np.full(T, 30.0), np.full(T, 33.0), np.full(T, 45.0)])
    net_load = np.linspace(0.0, 100.0, T)
    return fa, gens, mc, net_load


def _st_surface(tmp_path, st_shares=(0.3, 0.9), mults=((25.0, 40.0), (25.0, 40.0))):
    surf = {
        "_provenance": {
            "netload_pct_edges": [0.5],
            "ladder_quantiles": [0.1, 0.9],
        },
        "ST": {
            "years": {
                "2024": {
                    "cleared_share": list(st_shares),
                    "ladder": [[[0.1, m[0]], [0.9, m[1]]] for m in mults],
                }
            }
        },
    }
    p = tmp_path / "surface_st.json"
    p.write_text(json.dumps(surf))
    return str(p)


def test_steam_without_wall_is_hard_error(tmp_path):
    fa, gens, mc, nl = _st_fleet()
    cfg = ScenarioConfig(
        iso="ERCOT",
        mode="backcast",
        weather_year=2024,
        ercot_offer_surface_cleared_share_steam=True,
    )
    with pytest.raises(ValueError, match="no wall to extend"):
        build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)


def test_steam_flag_off_leaves_st_rows_untouched(tmp_path):
    """The wall alone (no steam flag) never prices ST_GAS rows (rule 19)."""
    fa, gens, mc, nl = _st_fleet()
    cfg = _cfg(_st_surface(tmp_path))
    m = build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)
    assert m is None  # ST-only fleet, ST_GAS out of scope -> byte-identical


def test_steam_scope_committed_and_econ_not_peak(tmp_path):
    """Steam cliff floors committed AND econ rows above the boundary; peak never."""
    fa, gens, mc, nl = _st_fleet()
    cfg = _cfg(
        _st_surface(tmp_path),
        ercot_offer_surface_cleared_share_steam=True,
    )
    m = build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)
    assert m is not None
    # committed (mid 0.2 <= 0.3 boundary) sheltered in bin 0
    assert m[0][: T // 2].max() == 0.0
    # econ (mid 0.6 > 0.3): floored in bin 0, sheltered in bin 1 (boundary .9)
    assert m[1][: T // 2].min() > 0.0
    assert m[1][T // 2 :].max() == 0.0
    # peak rung: never touched (ercot_offer_surface_conditional's rows)
    assert m[2].max() == 0.0


def test_steam_committed_above_boundary_floors(tmp_path):
    """A committed ST row above the measured boundary is priced by the cliff."""
    fa, gens, mc, nl = _st_fleet()
    cfg = _cfg(
        _st_surface(tmp_path, st_shares=(0.1, 0.1)),
        ercot_offer_surface_cleared_share_steam=True,
    )
    m = build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)
    assert m is not None
    assert m[0].min() > 0.0  # committed mid 0.2 > 0.1 boundary in both bins


def test_steam_cc_rows_unchanged_by_extension(tmp_path):
    """Arming the steam flag leaves the CC/CT wall byte-identical (rule 19)."""
    fa, gens, mc, nl = _fleet()
    base = build_ercot_offer_surface_cleared_share_markup(
        fa, gens, mc, nl, _cfg(_surface(tmp_path)), 2024
    )
    cfg = _cfg(
        _surface(tmp_path),
        ercot_offer_surface_cleared_share_steam=True,
    )
    m = build_ercot_offer_surface_cleared_share_markup(fa, gens, mc, nl, cfg, 2024)
    assert base is not None and m is not None
    np.testing.assert_array_equal(m, base)
