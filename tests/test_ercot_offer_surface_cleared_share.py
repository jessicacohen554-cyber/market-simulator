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
