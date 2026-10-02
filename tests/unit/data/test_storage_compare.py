"""Tests for the report-only storage dispatch comparison (scripts/lib/storage_compare)."""

from __future__ import annotations

import base64

import numpy as np
import pandas as pd

from scripts.data.build_storage_dispatch_actuals import std_hour_of_year
from scripts.lib import storage_compare as sc

T = sc.HOURS


def _dec_i16(b: str) -> np.ndarray:
    a = np.frombuffer(base64.b64decode(b), dtype="<i2").astype(float)
    a[a == -32768] = np.nan
    return a


def _write_fixture(tmp_path, monkeypatch, iso="CAISO", year=2025, obs_hours=T):
    hod = np.tile(np.arange(24), 365)
    dis = np.where((hod >= 17) & (hod < 21), 1000.0, 0.0)
    chg = np.where((hod >= 9) & (hod < 14), 900.0, 0.0)
    soc = np.cumsum(0.9 * chg - dis / 1.0) + 5000.0
    bdir = tmp_path / "bundle"
    (bdir / "hourly").mkdir(parents=True)
    pd.DataFrame(
        {
            "year": year,
            "pass": "P1",
            "tech": "li_ion",
            "hour": np.arange(T),
            "charge_mw": chg,
            "discharge_mw": dis,
            "soc_mwh": soc,
            "energy_cap_mwh": 1e5,
        }
    ).to_parquet(bdir / "hourly" / f"storage_{year}.parquet")
    net = dis - chg
    net_a = net.copy()
    net_a[obs_hours:] = np.nan
    act = tmp_path / "actuals"
    act.mkdir()
    pd.DataFrame(
        {
            "year": year,
            "hour": np.arange(T),
            "net_mw": net_a,
            "discharge_mw": np.clip(net_a, 0, None),
            "charge_mw": np.clip(-net_a, 0, None),
            "soc_mwh": soc,
            "source": "fixture",
        }
    ).to_parquet(act / f"{iso}_storage_hourly.parquet")
    monkeypatch.setattr(sc, "ACTUALS_DIR", act)
    return bdir, net


def test_identical_series_scores_perfect_and_roundtrips(tmp_path, monkeypatch):
    bdir, net = _write_fixture(tmp_path, monkeypatch)
    blk = sc.build_storage_compare(bdir, "CAISO", 2025)
    assert blk["stats"]["rNet"] == 1.0 and blk["stats"]["rDiur"] == 1.0
    assert blk["stats"]["bestLag"] == 0
    assert blk["stats"]["mDisTwh"] == blk["stats"]["aDisTwh"]
    np.testing.assert_allclose(_dec_i16(blk["net"]["m"]), net)
    assert len(blk["diur"]["m"]) == 288


def test_partial_observation_is_nan_not_zero(tmp_path, monkeypatch):
    bdir, _ = _write_fixture(tmp_path, monkeypatch, obs_hours=24 * 60)
    blk = sc.build_storage_compare(bdir, "CAISO", 2025)
    a = _dec_i16(blk["net"]["a"])
    assert np.isnan(a[24 * 60 :]).all() and blk["obsHours"] == 24 * 60
    # Month x hour cells with no observation are None, never 0.
    assert blk["diur"]["a"][11 * 24] is None


def test_too_few_hours_returns_none(tmp_path, monkeypatch):
    bdir, _ = _write_fixture(tmp_path, monkeypatch, obs_hours=24)
    assert sc.build_storage_compare(bdir, "CAISO", 2025) is None


def test_std_clock_maps_utc_to_fixed_standard_hour():
    # 2025-07-01 00:00 PDT == 07:00 UTC == 23:00 PST on Jun 30.
    utc = pd.DatetimeIndex(["2025-07-01 07:00"], tz="UTC")
    slot = std_hour_of_year(utc, 2025, "Etc/GMT+8")[0]
    assert slot == (31 + 28 + 31 + 30 + 31 + 30) * 24 - 1


def _write_bounds_fixture(tmp_path, monkeypatch, year=2025):
    """Two masked resources: A bounded [20, 80] of a 100 MWh ceiling, B [0, 50] of 50."""
    raw = tmp_path / "eoh"
    raw.mkdir()
    utc = pd.date_range(f"{year}-01-01 08:00", periods=24 * 10, freq="h", tz="UTC")
    a = pd.DataFrame(
        {
            "interval_start_utc": utc,
            "resourcebid_seq": 1,
            "min_eoh_soc_mwh": 20.0,
            "max_eoh_soc_mwh": 80.0,
        }
    )
    a.loc[0, "max_eoh_soc_mwh"] = 100.0  # the ceiling = the year max of the max bound
    b = a.assign(resourcebid_seq=2, min_eoh_soc_mwh=0.0, max_eoh_soc_mwh=50.0)
    pd.concat([a, b]).to_parquet(raw / f"caiso_rtm_eoh_soc_{year}.parquet")
    pd.DataFrame(
        {
            "resourcebid_seq": [1, 2, 3],
            "en_max_mw": [10.0, 10.0, 80.0],
            "is_storage_s1": [True, True, True],
            "submits_eoh": [True, True, False],
        }
    ).to_parquet(raw / f"caiso_rtm_storage_universe_{year}.parquet")
    monkeypatch.setattr(sc, "SOC_BOUNDS_DIR", raw)
    monkeypatch.setattr(sc, "DMM_SOC_OUTAGE_JSON", tmp_path / "absent.json")


def test_soc_bounds_envelope_on_model_clock(tmp_path, monkeypatch):
    bdir, _ = _write_fixture(tmp_path, monkeypatch)
    _write_bounds_fixture(tmp_path, monkeypatch)
    blk = sc.build_storage_compare(bdir, "CAISO", 2025)["socBounds"]
    # 08:00 UTC == 00:00 on the fixed UTC-8 clock; hour 1 avoids the ceiling row.
    assert blk["env"]["all"]["lo"][1] == round(20 / 150, 4)
    assert blk["env"]["all"]["hi"][1] == round(130 / 150, 4)
    assert blk["submitters"] == 2 and blk["mwShare"] == 0.2
    assert blk["env"]["summer"]["lo"] == [None] * 24  # January-only fixture
    assert blk["dmm"] is None
    # Model side: the fixture fleet's SOC over its 1e5 MWh capacity.
    assert len(blk["model"]["all"]) == 24 and 0 < blk["model"]["all"][0] < 1


def test_soc_bounds_absent_without_extract(tmp_path, monkeypatch):
    bdir, _ = _write_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(sc, "SOC_BOUNDS_DIR", tmp_path / "none")
    assert "socBounds" not in sc.build_storage_compare(bdir, "CAISO", 2025)
    assert sc.load_soc_bounds_envelope("ERCOT", 2025) is None
