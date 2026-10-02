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
    """Only owner-ruled ISOs carry a zone-resolved source (miso-294, NYISO-NEXT-22, R-13)."""
    assert set(dal.ZONAL_LW_SOURCES) == {"ERCOT", "MISO", "NYISO", "PJM"}


NYISO_ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]


def test_nyiso_zone_resolved_weighting(tmp_path, monkeypatch):
    """NYISO: each model zone is its own series, then zone-demand-weighted."""
    price = {z: 10.0 * (i + 1) for i, z in enumerate(NYISO_ZONES)}
    pd.concat(
        pd.DataFrame(
            {"year": 2023, "hour": np.arange(T), "zone": z, "rt": p, "da": p + 1.0}
        )
        for z, p in price.items()
    ).to_parquet(tmp_path / dal.NYISO_ZONAL_PARQUET)
    monkeypatch.setattr(dal, "HOURLY_OUT", tmp_path)
    # Measured demand in the model's own zone order (iso_configs), weights 1..5.
    from market_sim.config.iso_configs import get_iso_config

    order = [zn.name for zn in get_iso_config("NYISO").zones]
    w = {z: float(i + 1) for i, z in enumerate(order)}
    demand = np.vstack([np.full(T, w[z]) for z in order])
    monkeypatch.setattr(dal, "_measured_zone_demand", lambda iso, year: demand)
    out = dal._lw_fields("NYISO", 2023)
    expect = sum(price[z] * w[z] for z in order) / sum(w.values())
    assert out["rt_lw"] == pytest.approx(round(expect, 2))
    assert out["da_lw"] == pytest.approx(round(expect + 1.0, 2))
    assert out["src_lw"] == dal.ZONAL_LW_SOURCES["NYISO"]["src_lw"]


def test_unregistered_iso_keeps_system_hub(tmp_path, monkeypatch):
    """An ISO outside the registry weights its system hub by system load."""
    pd.DataFrame(
        {"year": 2023, "hour": np.arange(T), "rt": 20.0, "da": 21.0}
    ).to_parquet(tmp_path / "actual_lmp_hourly_SPP.parquet")
    monkeypatch.setattr(dal, "HOURLY_OUT", tmp_path)
    demand = np.ones((2, T))
    monkeypatch.setattr(dal, "_measured_zone_demand", lambda iso, year: demand)
    out = dal._lw_fields("SPP", 2023)
    assert out["rt_lw"] == 20.0 and out["da_lw"] == 21.0
    assert out["src_lw"].startswith("system hub hourly series")


def test_pjm_zone_resolved_weighting(tmp_path, monkeypatch):
    """PJM (owner ruling R-13): each model zone its own series, zone-demand-weighted."""
    from market_sim.config.iso_configs import get_iso_config

    order = [zn.name for zn in get_iso_config("PJM").zones]
    price = {z: 10.0 * (i + 1) for i, z in enumerate(order)}
    pd.concat(
        pd.DataFrame(
            {"year": 2023, "hour": np.arange(T), "zone": z, "rt": p, "da": p + 1.0}
        )
        for z, p in price.items()
    ).to_parquet(tmp_path / dal.PJM_ZONAL_PARQUET)
    monkeypatch.setattr(dal, "HOURLY_OUT", tmp_path)
    w = {z: float(i + 1) for i, z in enumerate(order)}
    demand = np.vstack([np.full(T, w[z]) for z in order])
    monkeypatch.setattr(dal, "_measured_zone_demand", lambda iso, year: demand)
    out = dal._lw_fields("PJM", 2023)
    expect = sum(price[z] * w[z] for z in order) / sum(w.values())
    assert out["rt_lw"] == pytest.approx(round(expect, 2))
    assert out["da_lw"] == pytest.approx(round(expect + 1.0, 2))
    assert out["src_lw"] == dal.ZONAL_LW_SOURCES["PJM"]["src_lw"]


def test_pjm_crosswalk_covers_every_model_zone_once():
    """Every PJM model zone gets its transmission zones; none is shared or lost."""
    from market_sim.config.iso_configs import get_iso_config
    from scripts.data import derive_pjm_zonal_lmp as dpz

    cw = dpz.model_zone_to_pnodes()
    assert set(cw) == {zn.name for zn in get_iso_config("PJM").zones}
    flat = [p for v in cw.values() for p in v]
    assert len(flat) == len(set(flat)) == 21
    assert "COMED" in cw["PJM_ComEd"] and "DOM" in cw["PJM_Dominion"]
    assert set(cw["PJM_SWMAAC"]) == {"BGE", "PEPCO"}


def test_pjm_zonal_frame_simple_mean_of_constituents(tmp_path, monkeypatch):
    """A model zone's hourly price is the simple mean of its transmission zones."""
    from scripts.data import derive_pjm_zonal_lmp as dpz

    utc = pd.date_range("2023-01-01 05:00", periods=T, freq="h", tz="UTC")
    stamp = utc.strftime("%-m/%-d/%Y %-I:%M:%S %p")
    rows = []
    for name, price in (("BGE", 30.0), ("PEPCO", 50.0), ("DOM", 70.0)):
        rows.append(
            pd.DataFrame(
                {
                    "datetime_beginning_utc": stamp,
                    "pnode_name": name,
                    "total_lmp_rt": price,
                    "total_lmp_da": price + 1.0,
                }
            )
        )
    df = pd.concat(rows, ignore_index=True)
    df.to_parquet(tmp_path / "rt_hrl_lmps_2023_01.parquet")
    df.to_parquet(tmp_path / "da_hrl_lmps_2023_01.parquet")
    monkeypatch.setattr(dpz, "SRC_DIR", tmp_path)
    f = dpz.zonal_frame(2023)
    sw = f[f["zone"] == "PJM_SWMAAC"]
    assert np.allclose(sw["rt"], 40.0) and np.allclose(sw["da"], 41.0)
    assert np.allclose(f[f["zone"] == "PJM_Dominion"]["rt"], 70.0)
    assert f[f["zone"] == "PJM_ComEd"]["rt"].isna().all()
