"""NWPP-NEXT-19: the NWPP external node, its seam-derived border links, and the
refusal of a priced-interchange build with no rows (rule 19)."""

from __future__ import annotations

import pytest

from market_sim.config.interchange_config import (
    IMPORT_NODE_LINKS,
    INTERFACE_NEIGHBORS,
    NeighborInterface,
    apply_interchange_topology,
    build_interchange_fleet,
    get_interchange_spec,
    require_priced_interchange_rows,
    seam_derived_border_links,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES


def _seam(name: str, limit: float, zones: tuple[str, ...]) -> NeighborInterface:
    return NeighborInterface(
        name=name,
        ba_code="X",
        gas_basis=0.0,
        marginal_heat_rate=7.0,
        hurdle=0.0,
        interface_limit_mw=limit,
        border_zones=zones,
    )


def test_seam_derived_links_sum_the_seams_landing_in_each_zone(monkeypatch):
    monkeypatch.setitem(
        INTERFACE_NEIGHBORS,
        "TOY",
        [_seam("A", 100.0, ("z1", "z2")), _seam("B", 40.0, ("z2",))],
    )
    assert seam_derived_border_links("TOY") == [("z1", 100.0), ("z2", 140.0)]


def test_nwpp_links_never_bind_tighter_than_the_seams():
    links = dict(IMPORT_NODE_LINKS["NWPP"])
    for seam in INTERFACE_NEIGHBORS["NWPP"]:
        for zone in seam.border_zones:
            assert links[zone] >= seam.interface_limit_mw


def test_nwpp_reference_price_builds_bands_in_the_external_node():
    cfg = ScenarioConfig(iso="NWPP", mode="backcast", reference_price_interface=True)
    rows = build_interchange_fleet(get_interchange_spec(cfg, "NWPP", 2023), 0.0)
    seams = INTERFACE_NEIGHBORS["NWPP"]
    assert len(rows) == 2 * SEAM_FLOW_TRANCHES * len(seams)
    assert {g.zone for g in rows} == {"NWPP_external"}
    imports = sum(g.pmax_mw for g in rows)
    assert imports == pytest.approx(sum(s.interface_limit_mw for s in seams))


def test_nwpp_topology_gains_the_external_node_and_its_links():
    cfg = ScenarioConfig(iso="NWPP", mode="backcast", reference_price_interface=True)
    spec = get_interchange_spec(cfg, "NWPP", 2023)
    base = get_iso_config("NWPP")
    ext = apply_interchange_topology(base, spec, cfg, year=2023, extend_node=True)
    assert "NWPP_external" in ext.zone_names
    assert "NWPP_external" not in base.zone_names
    got = {
        (lk.to_zone, lk.ttc_mw) for lk in ext.links if lk.from_zone == "NWPP_external"
    }
    assert got == set(IMPORT_NODE_LINKS["NWPP"])


def test_nwpp_default_config_builds_no_seam_rows():
    cfg = ScenarioConfig(iso="NWPP", mode="backcast")
    assert build_interchange_fleet(get_interchange_spec(cfg, "NWPP", 2023), 0.0) == []


def test_empty_priced_build_is_refused():
    with pytest.raises(ValueError, match="builds no import/export rows"):
        require_priced_interchange_rows("NWPP", 2023, [])
    require_priced_interchange_rows("NWPP", 2023, [object()])


def _seam_named(name: str) -> NeighborInterface:
    return next(s for s in INTERFACE_NEIGHBORS["NWPP"] if s.name == name)


def test_caiso_seam_troughs_with_the_ciso_solar_glut(monkeypatch):
    """NWPP-NEXT-20: CAISO's price is set by its net load, so the CAISO seam's
    shape must fall where CISO solar is large even when gross demand is flat."""
    import numpy as np
    import pandas as pd

    from market_sim.data import neighbor_price

    hours = 8760
    noon = (np.arange(hours) % 24) == 12
    frame = pd.DataFrame(
        {
            "Demand": np.full(hours, 100.0),
            "NG: SUN": np.where(noon, 60.0, 0.0),
            "NG: WND": np.zeros(hours),
        }
    )
    monkeypatch.setattr(
        neighbor_price, "_eia_hourly_frame_filled", lambda ba, year: frame
    )
    seam = _seam_named("CAISO")
    shape, ba = neighbor_price.neighbor_load_shape(seam, 2024, hours)
    assert ba == "CISO"
    assert shape.mean() == pytest.approx(1.0)
    assert shape[noon].max() < shape[~noon].min()


def test_wecc_can_anchor_is_bc_hydros_all_hours_elap_price():
    """NWPP-NEXT-20: the WECC_CAN heat rates re-derive from the committed BCHA
    ELAP store (all hours, Canada's side of the seam), not the peak-only Mid-C
    index; the forward fallback is their mean."""
    from scripts.data.fetch_nwpp_bcha_elap import bcha_anchor_heat_rates

    seam = _seam_named("WECC_CAN")
    derived = bcha_anchor_heat_rates()["hr"]
    assert set(seam.hr_by_year) == set(derived.index) == {2023, 2024, 2025}
    for year, hr in seam.hr_by_year.items():
        assert hr == pytest.approx(derived[year], abs=0.005)
    assert seam.marginal_heat_rate == pytest.approx(
        sum(seam.hr_by_year.values()) / 3, abs=0.005
    )
