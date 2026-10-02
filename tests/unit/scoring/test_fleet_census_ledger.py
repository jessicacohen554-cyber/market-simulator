"""W0 E.8 / E.7: the fleet census ledger and its audit / promotion gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from scripts import audit_keepers  # noqa: E402
from scripts import build_fleet_census as bfc  # noqa: E402


@pytest.fixture
def vintage(tmp_path, monkeypatch):
    """A one-vintage EIA-860 tree: three MISO thermal units."""
    vdir = tmp_path / "vintage_2023"
    vdir.mkdir()
    pd.DataFrame(
        {
            "Plant Code": [1, 1, 2],
            "Generator ID": ["CT1", "ST1", "G1"],
            "Technology": [
                "Natural Gas Fired Combined Cycle",
                "Natural Gas Fired Combined Cycle",
                "Natural Gas Fired Combustion Turbine",
            ],
            "Status": ["OP", "OP", "SB"],
            "Nameplate Capacity (MW)": [200.0, 100.0, 50.0],
            "Summer Capacity (MW)": [180.0, 90.0, 45.0],
            "Winter Capacity (MW)": [200.0, 100.0, 50.0],
            "Planned Retirement Year": [None, None, None],
        }
    ).to_parquet(vdir / "eia860_generator_operable.parquet")
    pd.DataFrame(
        {"Plant Code": [1, 2], "Balancing Authority Code": ["MISO", "MISO"]}
    ).to_parquet(vdir / "eia860_plant.parquet")
    from market_sim.config import paths

    monkeypatch.setattr(paths, "EIA_860_DIR", tmp_path)
    return tmp_path


def test_census_reports_delta_per_family(vintage):
    model = pd.DataFrame(
        {
            "plant": [1, 2],
            "family": ["CC", "CT"],
            "pmax": [300.0, 50.0],
            "summer": [270.0, 40.0],
            "winter": [300.0, 50.0],
            "avail_jul": [250.0, 40.0],
            "avail_jan": [280.0, 45.0],
        }
    )
    census = bfc.build_census("MISO", 2023, model, "fixture")
    fam = {r["family"]: r for r in census["families"]}
    assert fam["CC"]["eia860_summer_mw"] == 270.0
    assert fam["CC"]["delta_summer_pct"] == 0.0 and fam["CC"]["within_tolerance"]
    assert fam["CT"]["eia860_summer_mw"] == 45.0  # SB admitted (E.4)
    assert fam["CT"]["delta_summer_pct"] == pytest.approx(-11.111, abs=1e-3)
    assert not fam["CT"]["within_tolerance"]
    assert fam["CT"]["explained_residual_rows"][0]["plant"] == 2
    assert census["verdict"] == "OUTSIDE"
    assert census["iso_report"]["status"].startswith("UNAVAILABLE")


def _bundle(tmp_path, w0: bool) -> Path:
    b = tmp_path / "bundle"
    b.mkdir()
    (b / "meta.json").write_text(json.dumps({"iso": "MISO", "years": [2023]}))
    (b / "run_config.json").write_text(
        json.dumps({"scenario_config": {"seasonal_capacity_basis": w0}})
    )
    return b


def test_audit_fails_a_w0_keeper_missing_its_census(tmp_path):
    findings = audit_keepers.fleet_census_findings(_bundle(tmp_path, True))
    assert findings[0][0] == "fail"


def test_audit_warns_a_pre_w0_keeper(tmp_path):
    findings = audit_keepers.fleet_census_findings(_bundle(tmp_path, False))
    assert findings[0][0] == "warn"


def test_audit_ok_when_census_present(tmp_path):
    b = _bundle(tmp_path, True)
    (b / "fleet_census_2023.json").write_text("{}")
    assert audit_keepers.fleet_census_findings(b)[0][0] == "ok"
