"""NWPP priced interface: per-seam external zones, anchored-year gating, the
served unpriced residual, and the refusal of an empty priced build (rule 19).

NEXT-19 wired the node; NEXT-20 replaced its pooled bus with one zone per seam
(docs/records/nwpp/FINDING-nwppnext20-seam-phase0-2026-10-02.md)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.interchange_config import (
    IMPORT_SEAM_ZONES,
    INTERFACE_NEIGHBORS,
    NWPP_PRICED_SEAM_LEGS,
    NeighborInterface,
    apply_interchange_topology,
    build_interchange_fleet,
    get_interchange_spec,
    require_priced_interchange_rows,
    seam_priced_in_year,
    seam_zone_links,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia930 import envelopes
from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES


def _seam(name: str, limit: float, zones: tuple[str, ...], **kw) -> NeighborInterface:
    return NeighborInterface(
        name=name,
        ba_code="X",
        gas_basis=0.0,
        marginal_heat_rate=7.0,
        hurdle=0.0,
        interface_limit_mw=limit,
        border_zones=zones,
        **kw,
    )


def _priced() -> ScenarioConfig:
    return ScenarioConfig(iso="NWPP", mode="backcast", reference_price_interface=True)


def test_seam_zone_links_rate_each_link_at_its_own_seam(monkeypatch):
    monkeypatch.setitem(
        INTERFACE_NEIGHBORS,
        "TOY",
        [_seam("A", 100.0, ("z1", "z2")), _seam("B", 40.0, ("z2",))],
    )
    monkeypatch.setitem(IMPORT_SEAM_ZONES, "TOY", {"A": "ext_A", "B": "ext_B"})
    assert seam_zone_links("TOY") == [
        ("ext_A", "z1", 100.0),
        ("ext_A", "z2", 100.0),
        ("ext_B", "z2", 40.0),
    ]


def test_a_seam_without_its_own_zone_is_refused(monkeypatch):
    monkeypatch.setitem(INTERFACE_NEIGHBORS, "TOY", [_seam("A", 1.0, ("z1",))])
    monkeypatch.setitem(IMPORT_SEAM_ZONES, "TOY", {"B": "ext_B"})
    with pytest.raises(ValueError, match="must name exactly"):
        seam_zone_links("TOY")


def test_anchored_years_only_prices_only_anchored_years():
    s = _seam("A", 1.0, ("z1",), hr_by_year={2023: 9.0}, anchored_years_only=True)
    assert seam_priced_in_year(s, 2023)
    assert not seam_priced_in_year(s, 2022)
    assert seam_priced_in_year(_seam("B", 1.0, ("z1",)), 2019)


def test_nwpp_topology_has_one_zone_per_seam_and_no_pooled_bus():
    cfg = _priced()
    spec = get_interchange_spec(cfg, "NWPP", 2023)
    base = get_iso_config("NWPP")
    ext = apply_interchange_topology(base, spec, cfg, year=2023, extend_node=True)
    assert "NWPP_external" not in ext.zone_names
    seams = {n.name: n for n in INTERFACE_NEIGHBORS["NWPP"]}
    for name, zone in IMPORT_SEAM_ZONES["NWPP"].items():
        got = {(lk.to_zone, lk.ttc_mw) for lk in ext.links if lk.from_zone == zone}
        want = {(b, seams[name].interface_limit_mw) for b in seams[name].border_zones}
        assert got == want, name
    # No external zone joins two internal zones that are not already joined by
    # an internal link at least as large as the seam (the bypass of FINDING §C).
    internal = {(lk.from_zone, lk.to_zone): lk.ttc_mw for lk in base.links}
    for seam in seams.values():
        b = seam.border_zones
        for i in range(len(b)):
            for j in range(i + 1, len(b)):
                ttc = max(
                    internal.get((b[i], b[j]), 0.0), internal.get((b[j], b[i]), 0.0)
                )
                assert ttc >= seam.interface_limit_mw, (seam.name, b[i], b[j])


@pytest.mark.parametrize("year,n_seams", [(2023, 3), (2020, 2)])
def test_nwpp_bands_land_in_their_own_zone_in_priced_years(year, n_seams):
    rows = build_interchange_fleet(get_interchange_spec(_priced(), "NWPP", year), 0.0)
    assert len(rows) == 2 * SEAM_FLOW_TRANCHES * n_seams
    zones = IMPORT_SEAM_ZONES["NWPP"]
    for g in rows:
        seam = g.unit_id.rsplit("#", 1)[0].rsplit("_ref", 1)[-1].split("_", 1)[-1]
        assert g.zone == zones[seam]
    if n_seams == 2:
        assert not any("WECC_CAN" in g.unit_id for g in rows)


def test_nwpp_default_config_builds_no_seam_rows():
    cfg = ScenarioConfig(iso="NWPP", mode="backcast")
    assert build_interchange_fleet(get_interchange_spec(cfg, "NWPP", 2023), 0.0) == []


def test_empty_priced_build_is_refused():
    with pytest.raises(ValueError, match="builds no import/export rows"):
        require_priced_interchange_rows("NWPP", 2023, [])
    require_priced_interchange_rows("NWPP", 2023, [object()])


def test_priced_legs_cover_exactly_the_priced_seams():
    assert set(NWPP_PRICED_SEAM_LEGS) == {n.name for n in INTERFACE_NEIGHBORS["NWPP"]}


@pytest.mark.parametrize(
    "year,subtracted", [(2023, 3.0 + 5.0 + 7.0), (2020, 3.0 + 5.0)]
)
def test_residual_is_position_minus_the_legs_priced_that_year(
    monkeypatch, year, subtracted
):
    hours = 8760
    utc = pd.date_range("2023-01-01 09:00", periods=hours, freq="h")
    monkeypatch.setattr(
        envelopes, "nwpp_net_interchange", lambda y, **k: np.full(hours, 100.0)
    )
    monkeypatch.setattr(
        envelopes,
        "_eia_hourly_frame_filled",
        lambda ba, y: pd.DataFrame({"UTC time": utc}),
    )
    per_leg = {
        ("CISO", ("BPAT", "PACW")): 3.0,
        ("CISO", ("NEVP",)): 5.0,
        ("BPAT", ("BCHA",)): 7.0,
    }
    monkeypatch.setattr(
        envelopes,
        "_diba_legs_export",
        lambda r, d, sgn, u: (np.full(len(u), per_leg[(r, d)]), 1.0),
    )
    got = envelopes.nwpp_unpriced_residual_interchange(year)
    assert np.allclose(got, 100.0 - subtracted)


def test_diba_leg_is_footprint_export_positive(tmp_path, monkeypatch):
    d = tmp_path / "eia-930-interchange"
    d.mkdir()
    local = pd.date_range("2024-01-01 01:00", periods=48, freq="h")
    pd.DataFrame(
        {
            "diba": pd.Categorical(["BPAT"] * 48),
            "mw": np.float32(-250.0),
            "local_time": local,
        }
    ).to_parquet(d / "CISO interchange hourly.parquet")
    monkeypatch.setattr(envelopes, "RAW_DIR", tmp_path)
    # Hour-ending 01:00 PST = 09:00 UTC.
    utc = pd.date_range("2024-01-01 09:00", periods=48, freq="h")
    leg, cov = envelopes._diba_legs_export("CISO", ("BPAT",), -1.0, utc)
    assert cov == 1.0
    assert np.allclose(leg, 250.0)  # CISO imports 250 from BPAT = NWPP exports 250
    with pytest.raises(ValueError, match="no row"):
        envelopes._diba_legs_export(
            "CISO", ("BPAT",), -1.0, utc + pd.Timedelta(days=400)
        )
