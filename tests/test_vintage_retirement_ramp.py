"""Month-precise COD + planned-retirement vintage ramp across resource classes.

The shared :func:`market_sim.data.cod_ramp.monthly_online_mask` engine is unit
tested in ``test_cod_ramp.py``. These tests pin the *loader integration*: each
resource class (renewable wind/solar, grid battery, pumped storage) must give a
plant only the months it actually operated — both the COD ON-ramp (a unit
commissioned mid-year contributes from its operating month on) and the
planned-retirement OFF-ramp (a unit retiring mid-year drops out from its
retirement month). Synthetic EIA-860 parquets + a stubbed zone lookup isolate
the reduction from the shipped data vintage.
"""

from __future__ import annotations

import pandas as pd
import pytest

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import renewables, zone_assignment
from market_sim.data.fleet import EIA_860_PARQUET_NAME
from market_sim.model import storage as storage_mod

_ISO = "ERCOT"
_ZONE = "West"  # a real ERCOT zone holding the synthetic plants
_YEAR = 2023


def _zone_idx() -> int:
    return get_iso_config(_ISO).zone_names.index(_ZONE)


# --- Renewables (B1) -------------------------------------------------------


def test_renewable_retirement_offramp(tmp_path, monkeypatch):
    """A solar plant retiring mid-year contributes only its in-service months."""
    pd.DataFrame(
        {
            "Plant Code": [1001, 1002],
            "Status": ["OP", "OP"],
            "Nameplate Capacity (MW)": [100.0, 50.0],
            "Operating Year": [2018, 2018],
            "Operating Month": [1, 1],
            # 1001 survives the year; 1002 retires end of June.
            "Planned Retirement Year": [2030, 2023],
            "Planned Retirement Month": [6, 6],
        }
    ).to_parquet(tmp_path / "eia860_solar_operable.parquet", index=False)
    monkeypatch.setattr(
        zone_assignment, "build_zone_lookup", lambda iso: {1001: _ZONE, 1002: _ZONE}
    )

    monthly = renewables._eia860_monthly_capacity(
        _ISO, "solar", get_iso_config(_ISO).zone_names, _YEAR, data_dir=tmp_path
    )
    assert monthly is not None
    z = _zone_idx()
    assert monthly[z, 0] == pytest.approx(150.0)  # January: both online
    assert monthly[z, 5] == pytest.approx(150.0)  # June: retiree's last month
    assert monthly[z, 6] == pytest.approx(100.0)  # July: survivor only
    assert monthly[z, -1] == pytest.approx(100.0)  # December: survivor only


def test_renewable_midyear_cod_onramp(tmp_path, monkeypatch):
    """A wind plant commissioned mid-year contributes only from its COD month."""
    pd.DataFrame(
        {
            "Plant Code": [1101, 1102],
            "Status": ["OP", "OP"],
            "Nameplate Capacity (MW)": [200.0, 60.0],
            "Operating Year": [2015, 2023],  # 1102 comes online during 2023
            "Operating Month": [1, 7],
            "Planned Retirement Year": [2030, 2030],
            "Planned Retirement Month": [12, 12],
        }
    ).to_parquet(tmp_path / "eia860_wind_operable.parquet", index=False)
    monkeypatch.setattr(
        zone_assignment, "build_zone_lookup", lambda iso: {1101: _ZONE, 1102: _ZONE}
    )

    monthly = renewables._eia860_monthly_capacity(
        _ISO, "wind", get_iso_config(_ISO).zone_names, _YEAR, data_dir=tmp_path
    )
    assert monthly is not None
    z = _zone_idx()
    assert monthly[z, 5] == pytest.approx(200.0)  # June: only the incumbent
    assert monthly[z, 6] == pytest.approx(260.0)  # July: new unit steps in
    assert monthly[z, -1] == pytest.approx(260.0)  # December: both online


# --- Grid batteries (B3) ---------------------------------------------------


def _patch_storage_dir(tmp_path, monkeypatch, code_to_zone):
    from market_sim.config import paths

    monkeypatch.setattr(paths, "active_eia860_dir", lambda: tmp_path)
    monkeypatch.setattr(zone_assignment, "build_zone_lookup", lambda iso: code_to_zone)


def test_storage_battery_retirement_offramp(tmp_path, monkeypatch):
    """A battery retiring mid-year steps the zone caps down from its month."""
    pd.DataFrame(
        {
            "Plant Code": [2001, 2002],
            "Status": ["OP", "OP"],
            "Nameplate Capacity (MW)": [200.0, 80.0],
            "Nameplate Energy Capacity (MWh)": [800.0, 320.0],
            "Operating Year": [2019, 2019],
            "Operating Month": [1, 1],
            "Planned Retirement Year": [2030, 2023],  # 2002 retires end of June
            "Planned Retirement Month": [6, 6],
        }
    ).to_parquet(tmp_path / "eia860_energy_storage_operable.parquet", index=False)
    _patch_storage_dir(tmp_path, monkeypatch, {2001: _ZONE, 2002: _ZONE})

    cfg = ScenarioConfig(weather_year=_YEAR, iso=_ISO, storage_vintage_ramp=True)
    units = storage_mod.load_eia860_storage(_ISO, _YEAR, cfg)
    battery = next(u for u in units if u.zone == _ZONE and u.tech_name == "li_ion")

    assert battery.power_cap_mw == pytest.approx(200.0)  # December = survivor
    assert battery.energy_cap_mwh == pytest.approx(800.0)
    assert battery.monthly_power_mw is not None  # intra-year change -> ramped
    mp = battery.monthly_power_mw
    assert mp[0] == pytest.approx(280.0)  # January: both online
    assert mp[5] == pytest.approx(280.0)  # June: retiree's last month
    assert mp[6] == pytest.approx(200.0)  # July: survivor only
    assert mp[-1] == pytest.approx(200.0)  # December: survivor only


def test_storage_battery_static_without_ramp(tmp_path, monkeypatch):
    """With the ramp off, a mid-year retiree leaves the fleet flat at year-end."""
    pd.DataFrame(
        {
            "Plant Code": [2001, 2002],
            "Status": ["OP", "OP"],
            "Nameplate Capacity (MW)": [200.0, 80.0],
            "Nameplate Energy Capacity (MWh)": [800.0, 320.0],
            "Operating Year": [2019, 2019],
            "Operating Month": [1, 1],
            "Planned Retirement Year": [2030, 2023],
            "Planned Retirement Month": [6, 6],
        }
    ).to_parquet(tmp_path / "eia860_energy_storage_operable.parquet", index=False)
    _patch_storage_dir(tmp_path, monkeypatch, {2001: _ZONE, 2002: _ZONE})

    cfg = ScenarioConfig(weather_year=_YEAR, iso=_ISO, storage_vintage_ramp=False)
    units = storage_mod.load_eia860_storage(_ISO, _YEAR, cfg)
    battery = next(u for u in units if u.zone == _ZONE and u.tech_name == "li_ion")
    # Year-end (December) capacity excludes the retiree; no monthly profile.
    assert battery.power_cap_mw == pytest.approx(200.0)
    assert battery.monthly_power_mw is None


def test_storage_battery_missing_retirement_columns(tmp_path, monkeypatch):
    """Absent retirement columns are a no-op: COD-only ramp, all capacity kept."""
    pd.DataFrame(
        {
            "Plant Code": [2001, 2002],
            "Status": ["OP", "OP"],
            "Nameplate Capacity (MW)": [200.0, 80.0],
            "Nameplate Energy Capacity (MWh)": [800.0, 320.0],
            "Operating Year": [2019, 2023],  # 2002 commissioned mid-2023
            "Operating Month": [1, 7],
        }
    ).to_parquet(tmp_path / "eia860_energy_storage_operable.parquet", index=False)
    _patch_storage_dir(tmp_path, monkeypatch, {2001: _ZONE, 2002: _ZONE})

    cfg = ScenarioConfig(weather_year=_YEAR, iso=_ISO, storage_vintage_ramp=True)
    units = storage_mod.load_eia860_storage(_ISO, _YEAR, cfg)
    battery = next(u for u in units if u.zone == _ZONE and u.tech_name == "li_ion")
    assert battery.power_cap_mw == pytest.approx(280.0)  # both online by Dec
    mp = battery.monthly_power_mw
    assert mp is not None
    assert mp[5] == pytest.approx(200.0)  # June: incumbent only
    assert mp[6] == pytest.approx(280.0)  # July: new unit steps in


# --- Pumped storage (B3) ---------------------------------------------------


def _write_ps_parquet(tmp_path, frame):
    frame.to_parquet(tmp_path / EIA_860_PARQUET_NAME, index=False)


def test_pumped_storage_retired_unit_excluded(tmp_path, monkeypatch):
    """A PS unit retired before the backcast year is dropped (year-precise)."""
    _write_ps_parquet(
        tmp_path,
        pd.DataFrame(
            {
                "plant_id": [3001, 3002],
                "prime_mover": ["PS", "PS"],
                "status": ["OP", "OP"],
                "nameplate_capacity_mw": [300.0, 120.0],
                "operating_year": [1980, 1980],
                "planned_retirement_year": [2031, 2022],  # 3002 gone before 2023
            }
        ),
    )
    _patch_storage_dir(tmp_path, monkeypatch, {3001: _ZONE, 3002: _ZONE})

    cfg = ScenarioConfig(weather_year=_YEAR, iso=_ISO, storage_vintage_ramp=True)
    units = storage_mod.load_eia860_pumped_storage(_ISO, _YEAR, cfg)
    ps = next(u for u in units if u.zone == _ZONE)
    assert ps.power_cap_mw == pytest.approx(300.0)  # only the survivor
    assert ps.monthly_power_mw is None  # old flat fleet -> static


def test_pumped_storage_midyear_cod_onramp(tmp_path, monkeypatch):
    """A PS unit commissioned during the year ramps in (year-precise month)."""
    _write_ps_parquet(
        tmp_path,
        pd.DataFrame(
            {
                "plant_id": [3001, 3003],
                "prime_mover": ["PS", "PS"],
                "status": ["OP", "OP"],
                "nameplate_capacity_mw": [300.0, 90.0],
                "operating_year": [1980, 2023],  # 3003 online during 2023
                "planned_retirement_year": [2031, 2040],
            }
        ),
    )
    _patch_storage_dir(tmp_path, monkeypatch, {3001: _ZONE, 3003: _ZONE})

    cfg = ScenarioConfig(weather_year=_YEAR, iso=_ISO, storage_vintage_ramp=True)
    units = storage_mod.load_eia860_pumped_storage(_ISO, _YEAR, cfg)
    ps = next(u for u in units if u.zone == _ZONE)
    assert ps.power_cap_mw == pytest.approx(390.0)  # both online by December
    mp = ps.monthly_power_mw
    assert mp is not None  # intra-year change -> ramped
    # No operating month in the generator parquet -> COD_FALLBACK_MONTH (July).
    assert mp[0] == pytest.approx(300.0)  # January: incumbent only
    assert mp[6] == pytest.approx(390.0)  # July: new unit steps in
