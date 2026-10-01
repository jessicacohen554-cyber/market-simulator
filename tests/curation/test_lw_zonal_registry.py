"""Tests for the zone-resolved ``*_lw`` actual (``derive_actual_lmp._lw_fields``).

Covers the per-ISO ``ZONAL_LW_SOURCES`` registry added by miso-294: MISO's
zone-resolved branch (multi-hub zones averaged, MISO-Plains on the declared
MINN+ILLINOIS proxy, zone-demand weighting) and the guarantee that an ISO
outside the registry keeps the system-hub construction.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.data import derive_actual_lmp as dal

T = dal._HOURS_PER_YEAR
MISO_ZONES = [
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
]
HUB_PRICE = {
    "MINN.HUB": ("MISO-West", 10.0),
    "ILLINOIS.HUB": ("MISO-Illinois", 30.0),
    "INDIANA.HUB": ("MISO-Indiana", 40.0),
    "MICHIGAN.HUB": ("MISO-East", 50.0),
    "ARKANSAS.HUB": ("MISO-South", 60.0),
    "TEXAS.HUB": ("MISO-South", 80.0),
}


@pytest.fixture
def miso_archive(tmp_path, monkeypatch):
    """A flat-price MISO zonal archive and a constant per-zone demand."""
    rows = [
        pd.DataFrame(
            {
                "year": 2023,
                "hour": np.arange(T),
                "hub": hub,
                "zone": zone,
                "rt": price,
                "da": price + 1.0,
            }
        )
        for hub, (zone, price) in HUB_PRICE.items()
    ]
    pd.concat(rows).to_parquet(tmp_path / dal.MISO_ZONAL_PARQUET)
    monkeypatch.setattr(dal, "HOURLY_OUT", tmp_path)
    # Zone weights 1..6 (MW, constant every hour), in model-zone order.
    demand = np.repeat(np.arange(1.0, 7.0)[:, None], T, axis=1)
    monkeypatch.setattr(dal, "_measured_zone_demand", lambda iso, year: demand)
    return demand


def test_miso_zone_resolved_weighting(miso_archive):
    """Per-zone hub mean, Plains proxy, then zone-demand-weighted."""
    out = dal._lw_fields("MISO", 2023)
    zone_price = {
        "MISO-West": 10.0,
        "MISO-Plains": (10.0 + 30.0) / 2,  # MINN+ILLINOIS proxy
        "MISO-Illinois": 30.0,
        "MISO-Indiana": 40.0,
        "MISO-East": 50.0,
        "MISO-South": (60.0 + 80.0) / 2,  # multi-hub zone averaged
    }
    w = np.arange(1.0, 7.0)
    expect = sum(zone_price[z] * wi for z, wi in zip(MISO_ZONES, w)) / w.sum()
    assert out["rt_lw"] == pytest.approx(round(expect, 2))
    assert out["da_lw"] == pytest.approx(round(expect + 1.0, 2))
    assert out["rt_lw_mon"] == [pytest.approx(round(expect, 2))] * 12
    assert out["src_lw"] == dal.ZONAL_LW_SOURCES["MISO"]["src_lw"]


def test_miso_zone_map_from_archive(miso_archive):
    """The zone -> hubs map is read from the archive, Plains added as a proxy."""
    z = pd.read_parquet(dal.HOURLY_OUT / dal.MISO_ZONAL_PARQUET)
    zm = dal._miso_zone_to_hubs(z)
    assert zm["MISO-South"] == ("ARKANSAS.HUB", "TEXAS.HUB")
    assert zm["MISO-Plains"] == dal.MISO_PLAINS_PROXY_HUBS


def test_registry_scope_is_ruled_isos_only():
    """Only owner-ruled ISOs carry a zone-resolved source (miso-294 scope)."""
    assert set(dal.ZONAL_LW_SOURCES) == {"ERCOT", "MISO"}


def test_unregistered_iso_keeps_system_hub(tmp_path, monkeypatch):
    """An ISO outside the registry weights its system hub by system load."""
    pd.DataFrame(
        {"year": 2023, "hour": np.arange(T), "rt": 20.0, "da": 21.0}
    ).to_parquet(tmp_path / "actual_lmp_hourly_PJM.parquet")
    monkeypatch.setattr(dal, "HOURLY_OUT", tmp_path)
    demand = np.ones((2, T))
    monkeypatch.setattr(dal, "_measured_zone_demand", lambda iso, year: demand)
    out = dal._lw_fields("PJM", 2023)
    assert out["rt_lw"] == 20.0 and out["da_lw"] == 21.0
    assert out["src_lw"].startswith("system hub hourly series")
