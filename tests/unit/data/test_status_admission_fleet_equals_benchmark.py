"""W0 E.8 / E.4: OP + SB admitted fleet-wide; one population with the benchmark.

The EIA-923 benchmark counts every plant in the region that generated; the
fleet used to keep ``OP`` only, so a plant generating from an ``SB`` unit was
benchmarked but never carried (FINDING-nwppnext2-standby-census). W0 takes the
ruling's "the fleet admits what the benchmark counts" branch: ``SB`` is
admitted by status alone (owner ruling Q2 — never selected on EIA-923), the
bin-constituent COD list reads the SAME status set, and the ``OA``/``OS``-only
envelope is reported by the census, never fitted.
"""

from __future__ import annotations

import pandas as pd
import pytest

from market_sim.config import paths
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import cod_ramp
from market_sim.data.fleet import eia860 as e860


def _row(plant, gen, status):
    return {
        "plant_id": plant,
        "generator_id": gen,
        "plant_name": f"P{plant}",
        "state": "MN",
        "balancing_authority_code": "MISO",
        "technology": "Natural Gas Fired Combustion Turbine",
        "energy_source": "NG",
        "prime_mover": "GT",
        "nameplate_capacity_mw": 50.0,
        "net_summer_capacity_mw": 45.0,
        "operating_year": 2001,
        "planned_retirement_year": None,
        "planned_retirement_month": None,
        "status": status,
        "heat_rate": 11.0,
        "chp": "N",
    }


@pytest.fixture
def standby_armed():
    prior = paths.eia860_standby_admitted()
    paths.set_eia860_standby_admission(True)
    yield
    paths.set_eia860_standby_admission(prior)


def test_backcast_default_admits_standby():
    assert ScenarioConfig(mode="backcast").admit_standby_units is True
    assert ScenarioConfig(mode="forecast").admit_standby_units is False


def test_sb_unit_carried_os_only_plant_not(standby_armed):
    df = pd.DataFrame([_row(1, "A", "SB"), _row(2, "B", "OS"), _row(3, "C", "OA")])
    gens = e860._rows_to_generators(df, "MISO", None, apply_cc_summer_guard=False)
    assert {g.plant_code for g in gens} == {1}


def test_bin_constituents_read_the_same_status_set(tmp_path, standby_armed):
    pd.DataFrame(
        {
            "Plant Code": [1, 2],
            "Operating Year": [2001, 2001],
            "Operating Month": [6, 6],
            "Nameplate Capacity (MW)": [50.0, 50.0],
            "Status": ["SB", "OS"],
            "Technology": ["Natural Gas Fired Combustion Turbine"] * 2,
            "Energy Source 1": ["NG", "NG"],
            "Prime Mover": ["GT", "GT"],
        }
    ).to_parquet(tmp_path / "eia860_generator_operable.parquet")
    cod_ramp._load_unit_cod_map.cache_clear()
    units = cod_ramp._load_unit_cod_map(
        tmp_path, tuple(sorted(paths.eia860_operable_statuses()))
    )
    assert {k[0] for k in units} == {1}
    cod_ramp._load_unit_cod_map.cache_clear()
