"""The UC-2 compose script on two toy legs (DESIGN section 6).

Two synthetic one-year bundles (the keeper's file shapes at toy size) compose
into one span: per-year files copy, root frames concatenate with a ``year``
column, ``run_config_<y>.json`` is kept per year, and — when the recipe arms
``unit_commitment_milp`` — the UC artifacts fold into ``hourly/`` and the
make-whole sidecar is computed from the composite's own per-unit layer.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tests.helpers import REPO_ROOT

_SPEC = importlib.util.spec_from_file_location(
    "_ucmilp_compose_span",
    Path(REPO_ROOT) / "scripts" / "probes" / "_ucmilp_compose_span.py",
)
compose_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(compose_mod)

T = 48


def _leg(
    cal: Path, name: str, year: int, armed: bool, with_uplift: bool = False
) -> Path:
    leg = cal / name
    (leg / "hourly").mkdir(parents=True)
    (leg / "dispatch").mkdir()
    cfg = {
        "scenario_config": {
            "iso": "NEISO",
            "mode": "backcast",
            "weather_year": year,
            "unit_commitment_milp": armed,
            "voll": 5000.0,
        },
        "calibration_flags": {"years": [year]},
        "solve_surface": {"fingerprint": "abc"},
    }
    (leg / "run_config.json").write_text(json.dumps(cfg))
    (leg / f"run_config_{year}.json").write_text(json.dumps(cfg))
    (leg / "meta.json").write_text(
        json.dumps({"iso": "NEISO", "years": [year], "timestamp": "2026-10-03"})
    )
    hours = np.arange(T)
    pd.DataFrame(
        {
            "pass": "P1",
            "zone": "Z0",
            "hour": hours,
            "price": 30.0 + (hours % 24 >= 7) * 20.0,
        }
    ).to_parquet(leg / "hourly" / f"system_{year}.parquet", index=False)
    um = pd.DataFrame(
        {
            "year": year,
            "pass": "P1",
            "unit_id": "CC1",
            "plant_code": 1,
            "plant_group": "CC_REGULAR",
            "fuel": "gas_cc",
            "zone": "Z0",
            "hour": hours,
            "mw": np.where(hours % 24 >= 7, 150.0, 0.0),
            "cap_mw": 200.0,
            "mc": 25.0,
            "marginal": 0,
        }
    )
    um.to_parquet(leg / "hourly" / f"unit_marginal_{year}.parquet", index=False)
    pd.DataFrame({"zone": ["Z0"] * T, "hour": hours, "price": 30.0}).to_parquet(
        leg / "system.parquet", index=False
    )
    (leg / "dispatch" / f"{year}_P1.parquet").write_bytes(b"")
    if armed:
        u = np.where(hours % 24 >= 7, 2, 0).astype(np.int16)
        v = np.where(hours % 24 == 7, 2, 0).astype(np.int16)
        pd.DataFrame(
            {
                "year": year,
                "hour": hours.astype(np.int32),
                "cluster": 0,
                "plant_code": 1,
                "uc_class": "cc",
                "u": u,
                "n": 2,
                "v": v,
                "w": 0,
                "online_mw": u * 100.0,
                "floor_mw": u * 50.0,
                "noload_usd_per_unit_h": 100.0,
            }
        ).to_parquet(leg / "hourly" / f"uc_schedule_{year}.parquet", index=False)
        (leg / f"uc_solve_log_{year}.json").write_text(
            json.dumps(
                {
                    "clusters": [{"cluster": 0, "su_per_mw": 50.0, "pbar_mw": 100.0}],
                    "windows": [],
                    "summary": {},
                }
            )
        )
        if with_uplift:
            pd.DataFrame({"year": [year], "day": [0], "uplift_usd": [-1.0]}).to_parquet(
                leg / "hourly" / f"uc_uplift_{year}.parquet", index=False
            )
    return leg


def test_compose_two_legs_gate_off(tmp_path, monkeypatch):
    cal = tmp_path / "results" / "calibration"
    monkeypatch.setattr(compose_mod, "CAL", cal)
    _leg(cal, "leg_2023", 2023, armed=False)
    _leg(cal, "leg_2024", 2024, armed=False)
    out = tmp_path / "span"
    compose_mod.compose({"leg_2023": 2023, "leg_2024": 2024}, "NEISO", out)
    assert (out / "hourly" / "system_2023.parquet").is_file()
    assert (out / "hourly" / "system_2024.parquet").is_file()
    assert (out / "run_config_2023.json").is_file() and (
        out / "run_config_2024.json"
    ).is_file()
    sysf = pd.read_parquet(out / "system.parquet")
    assert sorted(sysf["year"].unique().tolist()) == [2023, 2024]
    meta = json.loads((out / "meta.json").read_text())
    assert meta["years"] == [2023, 2024]
    assert not list((out / "hourly").glob("uc_*"))


def test_compose_folds_uc_artifacts_and_writes_uplift(tmp_path, monkeypatch):
    cal = tmp_path / "results" / "calibration"
    monkeypatch.setattr(compose_mod, "CAL", cal)
    _leg(cal, "leg_2023", 2023, armed=True)
    _leg(
        cal, "leg_2024", 2024, armed=True, with_uplift=True
    )  # a leg that already carries the frame
    out = tmp_path / "span"
    compose_mod.compose({"leg_2023": 2023, "leg_2024": 2024}, "NEISO", out)
    for y in (2023, 2024):
        assert (out / "hourly" / f"uc_schedule_{y}.parquet").is_file()
        assert (out / f"uc_solve_log_{y}.json").is_file()
    assert pd.read_parquet(out / "hourly" / "uc_uplift_2024.parquet")[
        "uplift_usd"
    ].tolist() == [-1.0]
    for y in (2023,):
        up = pd.read_parquet(out / "hourly" / f"uc_uplift_{y}.parquet")
        assert len(up) == 2  # one cluster, two days
        # day: 17 h x 150 MW at $25 cost, revenue at $50 -> no energy shortfall;
        # no-load 17 h x 2 units x $100 + start 2 x 50 x 100 = 13,400 vs margin 17*150*25 = 63,750
        assert (up["uplift_usd"] == 0.0).all()
        assert up["noload_usd"].iloc[0] == pytest.approx(17 * 2 * 100.0)
        assert up["start_usd"].iloc[0] == pytest.approx(2 * 50.0 * 100.0)


def test_compose_refuses_a_leg_without_artifacts(tmp_path, monkeypatch):
    cal = tmp_path / "results" / "calibration"
    monkeypatch.setattr(compose_mod, "CAL", cal)
    _leg(cal, "leg_2023", 2023, armed=True)
    leg = _leg(cal, "leg_2024", 2024, armed=True)
    (leg / "hourly" / "uc_schedule_2024.parquet").unlink()
    with pytest.raises(SystemExit, match="carries no"):
        compose_mod.compose(
            {"leg_2023": 2023, "leg_2024": 2024}, "NEISO", tmp_path / "span"
        )


def test_compose_refuses_disagreeing_recipes(tmp_path, monkeypatch):
    cal = tmp_path / "results" / "calibration"
    monkeypatch.setattr(compose_mod, "CAL", cal)
    _leg(cal, "leg_2023", 2023, armed=False)
    _leg(cal, "leg_2024", 2024, armed=True)
    with pytest.raises(SystemExit, match="disagree"):
        compose_mod.compose(
            {"leg_2023": 2023, "leg_2024": 2024}, "NEISO", tmp_path / "span"
        )
