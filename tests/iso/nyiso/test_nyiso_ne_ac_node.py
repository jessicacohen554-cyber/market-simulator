"""The NE AC tie's own two-way node (``nyiso_ne_ac_node``, NYISO-NEXT-11).

Trivial cases first (one node, one link, 24 hours): the topology split, the
band fleet, the hourly ``Roseton(t) + offset_k`` pricing, the posted-limit link
bounds, the Roseton loader's clock, the pooled hub repricing's NE exclusion,
the P1 bridge keeping ONLY the node's sinks, and the spec resolution (NE-split
pooled ladder, backcast-only, byte-identical off).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
from market_sim.model.interchange.nyiso import (
    NYISO_IMPORT_HUB_HURDLE,
    inject_nyiso_import_hub_prices,
    inject_nyiso_ne_ac_node_prices,
    load_nyiso_ne_ac_neighbour_price,
    nyiso_ne_ac_posted_ttc_hourly,
    split_nyiso_ne_ac_node,
)
from market_sim.model.interchange.spec import (
    IMPORT_TRANCHES_BY_YEAR,
    NYISO_IMPORT_TRANCHES_NE_SPLIT_BY_YEAR,
    NYISO_NE_AC_LADDER_BY_YEAR,
    NYISO_NE_AC_LANDING,
    NYISO_NE_AC_NEIGHBOUR_NODE,
    NYISO_NE_AC_SEAM_ROW,
    NYISO_NE_AC_ZONE,
    apply_interchange_topology,
    build_interchange_fleet,
    build_nyiso_ne_ac_node_gens,
    get_interchange_spec,
)
from market_sim.pipeline.commitment import _bridge_floored_fleet

T = 24
YEAR = 2023


class _FA:
    """Minimal FleetArrays stand-in (the injectors read unit_ids / pmin)."""

    def __init__(self, unit_ids, pmin=None, pmax=None):
        n = len(unit_ids)
        self.unit_ids = list(unit_ids)
        self.pmin = np.zeros(n) if pmin is None else np.asarray(pmin, dtype=float)
        self.pmax = np.ones(n) if pmax is None else np.asarray(pmax, dtype=float)
        self.min_gen = None
        self.min_gen_mechanism = None
        self.availability = np.ones((n, T))


def _node_ids() -> list[str]:
    return [f"{NYISO_NE_AC_ZONE}_imp#{k}" for k in range(1, 9)] + [
        f"{NYISO_NE_AC_ZONE}_exp#{k}" for k in range(1, 9)
    ]


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #


def test_ladder_is_no_wash_every_year():
    """Every export offset sits strictly below every import offset (no resale)."""
    for year, lad in NYISO_NE_AC_LADDER_BY_YEAR.items():
        assert len(lad["import"]) == SEAM_FLOW_TRANCHES
        assert len(lad["export"]) == SEAM_FLOW_TRANCHES
        assert max(lad["export"]) < min(lad["import"]), year
        # Q-Q offsets are monotone in depth.
        assert lad["import"] == sorted(lad["import"]), year
        assert lad["export"] == sorted(lad["export"], reverse=True), year


def test_split_ladder_keeps_the_incumbent_rung_grid():
    """Same rung names and grid as the pooled ladder; only NE's volume leaves."""
    for year, rungs in NYISO_IMPORT_TRANCHES_NE_SPLIT_BY_YEAR.items():
        inc = IMPORT_TRANCHES_BY_YEAR["NYISO"][year]
        assert [r[0] for r in rungs] == [r[0] for r in inc]
        assert [r[1] for r in rungs[:-1]] == [r[1] for r in inc[:-1]]


# --------------------------------------------------------------------------- #
# Topology
# --------------------------------------------------------------------------- #


def test_split_adds_one_zone_and_one_link_idempotently():
    base = get_iso_config("NYISO")
    out = split_nyiso_ne_ac_node(base, 1400.0)
    assert NYISO_NE_AC_ZONE in out.zone_names
    new = [ln for ln in out.links if NYISO_NE_AC_ZONE in (ln.from_zone, ln.to_zone)]
    assert len(new) == 1
    assert (new[0].from_zone, new[0].to_zone, new[0].ttc_mw) == (
        NYISO_NE_AC_ZONE,
        NYISO_NE_AC_LANDING,
        1400.0,
    )
    assert len(out.links) == len(base.links) + 1
    assert split_nyiso_ne_ac_node(out, 999.0) is out


# --------------------------------------------------------------------------- #
# Fleet + pricing
# --------------------------------------------------------------------------- #


def test_node_fleet_bands_sum_to_the_posted_medians():
    gens = build_nyiso_ne_ac_node_gens(YEAR)
    lad = NYISO_NE_AC_LADDER_BY_YEAR[YEAR]
    imp = [g for g in gens if g.pmax_mw > 0]
    exp = [g for g in gens if g.pmin_mw < 0]
    assert len(imp) == len(exp) == SEAM_FLOW_TRANCHES
    assert sum(g.pmax_mw for g in imp) == pytest.approx(lad["import_mw"])
    assert sum(-g.pmin_mw for g in exp) == pytest.approx(lad["export_mw"])
    assert {g.zone for g in gens} == {NYISO_NE_AC_ZONE}
    assert {g.fuel_type for g in gens} == {"import"}
    assert [g.unit_id for g in gens] == _node_ids()


def test_prices_are_anchor_plus_offset_hour_by_hour():
    ids = ["other_row", *_node_ids()]
    fa = _FA(ids)
    mc = np.full((len(ids), T), 7.0)
    anchor = np.linspace(10.0, 80.0, T)
    n = inject_nyiso_ne_ac_node_prices(fa, mc, YEAR, neighbour_price=anchor)
    lad = NYISO_NE_AC_LADDER_BY_YEAR[YEAR]
    assert n == 16
    np.testing.assert_allclose(mc[0], 7.0)  # untouched
    np.testing.assert_allclose(mc[1], anchor + lad["import"][0])
    np.testing.assert_allclose(mc[9], anchor + lad["export"][0])
    # no-wash: in every hour the dearest sink is below the cheapest band
    assert (mc[9:17].max(axis=0) < mc[1:9].min(axis=0)).all()


def test_pricing_refuses_a_missing_band():
    fa = _FA(_node_ids()[:-1])
    with pytest.raises(ValueError):
        inject_nyiso_ne_ac_node_prices(
            fa, np.zeros((15, T)), YEAR, neighbour_price=np.zeros(T)
        )


def test_hub_repricing_can_exclude_neiso_from_the_pooled_node(monkeypatch):
    pjm, ne = np.linspace(20, 60, T), np.linspace(70, 30, T)
    monkeypatch.setattr(
        "market_sim.data.neighbor_price.neighbor_lmp_hourly",
        lambda iso, year, run="rt", **k: {"PJM": pjm, "NEISO": ne}.get(iso),
    )
    ids = [
        "NYISO_external_PJM_west",
        "NYISO_external_ISONE_tie",
        "NYISO_external_import_scarcity",
        "NYISO_external_export_surplus",
    ]
    mc = np.full((4, T), 5.0)
    assert inject_nyiso_import_hub_prices(
        _FA(ids), mc, "NYISO", YEAR, exclude_neighbours=("NEISO",)
    )
    np.testing.assert_allclose(mc[0], pjm + NYISO_IMPORT_HUB_HURDLE)
    np.testing.assert_allclose(mc[1], 5.0)  # ISONE_tie keeps its ladder value
    np.testing.assert_allclose(mc[2], pjm + NYISO_IMPORT_HUB_HURDLE)
    np.testing.assert_allclose(mc[3], pjm - NYISO_IMPORT_HUB_HURDLE)


# --------------------------------------------------------------------------- #
# Posted limits + neighbour-price clock
# --------------------------------------------------------------------------- #


def _posting(pos: np.ndarray, neg: np.ndarray, start: str = "2023-01-01"):
    local = pd.date_range(start, periods=len(pos), freq="h")
    return pd.DataFrame(
        {
            "interface": NYISO_NE_AC_SEAM_ROW,
            "interval_start_local": local,
            "flow_mw": 0.0,
            "positive_limit_mw": pos,
            "negative_limit_mw": neg,
        }
    )


def test_posted_limits_bound_only_the_node_link_both_ways():
    topo = split_nyiso_ne_ac_node(get_iso_config("NYISO"), 1400.0)
    n = len(topo.links)
    fwd, rev = np.full((T, n), 111.0), np.full((T, n), 222.0)
    pos = np.full(T, 1400.0)
    pos[5] = 300.0
    neg = np.full(T, -1600.0)
    neg[7] = np.nan  # curated sentinel -> carried forward
    out_f, out_r = nyiso_ne_ac_posted_ttc_hourly(
        fwd, rev, topo, YEAR, T, frame=_posting(pos, neg)
    )
    j = n - 1  # the node link is appended last
    assert out_f[5, j] == 300.0 and out_f[0, j] == 1400.0
    assert out_r[7, j] == 1600.0
    np.testing.assert_allclose(np.delete(out_f, j, axis=1), 111.0)
    np.testing.assert_allclose(np.delete(out_r, j, axis=1), 222.0)


def test_roseton_loader_places_utc_hours_on_the_local_model_clock():
    utc = pd.date_range("2023-01-01 05:00", periods=T, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "node": NYISO_NE_AC_NEIGHBOUR_NODE,
            "market": "DA",
            "interval_start_utc": utc,
            "price_usd": np.arange(T, dtype=float),
        }
    )
    got = load_nyiso_ne_ac_neighbour_price(YEAR, T, frame=frame)
    # 05:00 UTC = 00:00 EST, so the local clock starts at the first row.
    np.testing.assert_allclose(got, np.arange(T, dtype=float))


def test_roseton_loader_refuses_an_empty_series():
    frame = pd.DataFrame(
        {"node": ["x"], "market": ["DA"], "interval_start_utc": [pd.Timestamp(0)]}
    )
    with pytest.raises(FileNotFoundError):
        load_nyiso_ne_ac_neighbour_price(YEAR, T, frame=frame)


# --------------------------------------------------------------------------- #
# P1 bridge: only the node's sinks keep their range
# --------------------------------------------------------------------------- #


def test_bridge_mask_keeps_only_the_selected_sinks():
    ids = ["NYISO_external_export_surplus", f"{NYISO_NE_AC_ZONE}_exp#1", "gas"]
    fa = FleetArrays(
        pmax=np.array([0.0, 0.0, 100.0]),
        pmin=np.array([-600.0, -200.0, 0.0]),
        heat_rate=np.array([0.0, 0.0, 7.0]),
        vom=np.zeros(3),
        emission_rate=np.zeros(3),
        nox_rate=np.zeros(3),
        so2_rate=np.zeros(3),
        zone_idx=np.array([0, 1, 2]),
        fuel_type_idx=np.array(
            [FUEL_TYPE_MAP["import"], FUEL_TYPE_MAP["import"], FUEL_TYPE_MAP["gas_cc"]]
        ),
        availability=np.ones((3, T)),
        unit_ids=ids,
        efficiency_bin=np.zeros(3, dtype=int),
        plant_code=np.zeros(3, dtype=int),
    )
    floor = np.zeros((3, T))
    floor[2] = 40.0
    mask = np.array([u.startswith(f"{NYISO_NE_AC_ZONE}_") for u in ids])
    out = _bridge_floored_fleet(fa, floor, 99, preserve_absorption=mask)
    np.testing.assert_allclose(out.min_gen[0], 0.0)  # pooled sink: unchanged defect
    np.testing.assert_allclose(out.min_gen[1], -200.0)  # node sink keeps its range
    np.testing.assert_allclose(out.min_gen[2], 40.0)
    # boolean False is the byte-identical legacy path
    legacy = _bridge_floored_fleet(fa, floor, 99)
    np.testing.assert_allclose(legacy.min_gen[1], 0.0)


# --------------------------------------------------------------------------- #
# Spec resolution
# --------------------------------------------------------------------------- #


def _cfg(**kw) -> ScenarioConfig:
    return ScenarioConfig(iso="NYISO", mode="backcast", **kw)


def test_spec_off_is_unchanged_and_on_swaps_the_ladder():
    off = get_interchange_spec(_cfg(), "NYISO", year=YEAR)
    assert off.nyiso_ne_ac_node is False
    assert off.import_tranches == IMPORT_TRANCHES_BY_YEAR["NYISO"][YEAR]
    on = get_interchange_spec(_cfg(nyiso_ne_ac_node=True), "NYISO", year=YEAR)
    assert on.nyiso_ne_ac_node is True
    assert on.import_tranches == NYISO_IMPORT_TRANCHES_NE_SPLIT_BY_YEAR[YEAR]
    gens_off = build_interchange_fleet(off)
    gens_on = build_interchange_fleet(on)
    assert len(gens_on) == len(gens_off) + 2 * SEAM_FLOW_TRANCHES
    topo = apply_interchange_topology(get_iso_config("NYISO"), on, _cfg(), year=YEAR)
    assert NYISO_NE_AC_ZONE in topo.zone_names


def test_spec_refuses_forecast_and_uncovered_years():
    with pytest.raises(ValueError):
        get_interchange_spec(
            ScenarioConfig(iso="NYISO", mode="forecast", nyiso_ne_ac_node=True),
            "NYISO",
            year=YEAR,
        )
    with pytest.raises(ValueError):
        get_interchange_spec(_cfg(nyiso_ne_ac_node=True), "NYISO", year=2019)


def test_flag_is_ignored_outside_nyiso():
    spec = get_interchange_spec(
        ScenarioConfig(iso="PJM", mode="backcast", nyiso_ne_ac_node=True),
        "PJM",
        year=YEAR,
    )
    assert spec.nyiso_ne_ac_node is False
