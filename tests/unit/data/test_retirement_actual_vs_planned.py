"""W0 E.8 / E.5: a backcast retires a unit at its ACTUAL date, never a planned one."""

from __future__ import annotations

import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import cod_ramp


def _dir(tmp_path):
    # Plant 10: operable, PLANNED retirement 2024-12 (paper date).
    pd.DataFrame(
        {
            "Plant Code": [10],
            "Operating Year": [1990],
            "Operating Month": [1],
            "Nameplate Capacity (MW)": [100.0],
            "Planned Retirement Year": [2024],
            "Planned Retirement Month": [12],
        }
    ).to_parquet(tmp_path / "eia860_generator_operable.parquet")
    # Plant 20: ACTUAL retirement 2023-07 (the retiree channel's record).
    pd.DataFrame(
        {
            "plant_id": [20],
            "operating_year": [1985],
            "operating_month": [1],
            "nameplate_capacity_mw": [200.0],
            "planned_retirement_year": [2023],
            "planned_retirement_month": [7],
        }
    ).to_parquet(tmp_path / cod_ramp._RETIRED_WINDOW_NAME)
    cod_ramp._load_cod_map.cache_clear()
    return tmp_path


def test_planned_retirement_ignored_actual_kept(tmp_path):
    d = _dir(tmp_path)
    cod = cod_ramp._load_cod_map(d, True)
    assert cod[10][2] is None  # planned 2024-12 never read
    assert cod[20][2:] == (2023, 7)  # actual 2023-07 masks out from Aug-2023
    cod_ramp._load_cod_map.cache_clear()


def test_off_path_still_reads_planned(tmp_path):
    d = _dir(tmp_path)
    cod = cod_ramp._load_cod_map(d)
    assert cod[10][2:] == (2024, 12)
    cod_ramp._load_cod_map.cache_clear()


def test_backcast_default_forecast_off():
    assert ScenarioConfig(mode="backcast").backcast_actual_retirement_only is True
    assert ScenarioConfig(mode="forecast").backcast_actual_retirement_only is False
