"""Tests for the coal-unit coverage append (soco-70).

``derive_thermal_tranches.append_coal_unit_coverage`` adds a COAL row for every
coal plant the artifact does not already carry one for, and must leave every
pre-existing byte untouched (the rows a keeper already reads). Trivial synthetic
CSVs only (testing pattern): the CAMPD derivation itself is replaced by a stub,
so these pin the APPEND contract — byte prefix, column order, covered-set
exclusion, idempotence — not the statistics.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from tests.helpers import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))

import derive_thermal_tranches as dtt  # noqa: E402

_HEADER = (
    "plant_code,plant_group,name,status,nameplate_mw,online_hours,committed_pct,"
    "mustrun_pct,mustrun_online_pct,online_frac,p25_cf,median_cf,peaking_pct,"
    "chp_pmin_cf,chp_sector,steam_level_cf\n"
)
_BODY = (
    "3,CC_REGULAR,Barry,ok,1821.2,8664,70.0,0.0,0.0,1.0,100.0,150.0,16.4,,,\n"
    "703,COAL,Bowen,ok,3200.0,8684,64.0,60.0,14.1,0.991,69.6,80.6,,,,\n"
)


def _artifact(tmp_path: Path) -> Path:
    path = tmp_path / "thermal_tranches_TEST.csv"
    path.write_text(_HEADER + _BODY)
    return path


def _stub(monkeypatch, seen: list) -> None:
    def rows(iso, years, covered, **_kw):
        seen.append(set(covered))
        return [
            {
                "plant_code": code,
                "plant_group": "COAL",
                "name": f"P{code}",
                "status": "ok",
                "nameplate_mw": 800.0,
                "online_hours": 5000,
                "committed_pct": 40.0,
                "mustrun_pct": 20.0,
                "mustrun_online_pct": 18.0,
                "online_frac": 0.6,
                "p25_cf": 50.0,
                "median_cf": 60.0,
            }
            for code in (3, 703)
            if code not in covered
        ]

    monkeypatch.setattr(dtt, "coal_unit_coverage_rows", rows)


def test_existing_bytes_are_an_exact_prefix(tmp_path, monkeypatch):
    """Every pre-existing byte survives; only new COAL rows are appended."""
    path = _artifact(tmp_path)
    before = path.read_bytes()
    seen: list = []
    _stub(monkeypatch, seen)
    added = dtt.append_coal_unit_coverage(path, "TEST", [2019, 2020])
    after = path.read_bytes()
    assert after.startswith(before)
    assert [r["plant_code"] for r in added] == [3]
    df = pd.read_csv(path)
    assert list(df.columns) == _HEADER.strip().split(",")
    new = df.iloc[-1]
    assert (int(new.plant_code), new.plant_group, float(new.mustrun_pct)) == (
        3,
        "COAL",
        20.0,
    )
    # a gas row at the same plant does NOT count as coal coverage
    assert seen[0] == {703}


def test_rerun_is_a_noop(tmp_path, monkeypatch):
    """A second append finds every coal plant covered and writes nothing."""
    path = _artifact(tmp_path)
    _stub(monkeypatch, [])
    dtt.append_coal_unit_coverage(path, "TEST", [2019])
    once = path.read_bytes()
    assert dtt.append_coal_unit_coverage(path, "TEST", [2019]) == []
    assert path.read_bytes() == once
