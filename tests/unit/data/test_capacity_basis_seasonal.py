"""W0 E.1: the published seasonal capacity basis (audit §E.1, §E.8).

Trivial cases first: one combined-cycle unit (nameplate 100, summer 90,
winter 100) is carried at 100 MW with 0.9 of it in Jun-Sep and all of it in
Oct-May, and no flat class derate; a blank winter falls to the summer rating, a
blank summer to nameplate; a block rated on one row is reallocated, its winter
included.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config import paths
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fleet import eia860 as e860
from market_sim.data.fleet.arrays import _hour_to_month_index

ZONE = "MISO-West"


@pytest.fixture
def seasonal_armed():
    """Arm the process-global basis for one test, then restore it."""
    prior = paths.eia860_seasonal_capacity_basis()
    paths.set_eia860_seasonal_capacity_basis(True)
    yield
    paths.set_eia860_seasonal_capacity_basis(prior)


def _row(gen="1", pm="CT", np_=100.0, su=90.0, wi=100.0, tech=None, es="NG"):
    return {
        "plant_id": 990001,
        "generator_id": gen,
        "plant_name": "Test",
        "state": "MN",
        "balancing_authority_code": "MISO",
        "technology": tech or "Natural Gas Fired Combined Cycle",
        "energy_source": es,
        "prime_mover": pm,
        "nameplate_capacity_mw": np_,
        "net_summer_capacity_mw": su,
        "winter_capacity_mw": wi,
        "operating_year": 2005,
        "planned_retirement_year": None,
        "planned_retirement_month": None,
        "status": "OP",
        "heat_rate": 7.0,
        "chp": "N",
    }


def _load(rows, guard: bool = False) -> list[Generator]:
    return e860._rows_to_generators(
        pd.DataFrame(rows), "MISO", None, apply_cc_summer_guard=guard
    )


def test_cc_unit_carried_at_envelope_with_season_shares(seasonal_armed):
    (g,) = _load([_row()])
    assert g.plant_group == "CC_REGULAR"
    assert g.pmax_mw == pytest.approx(100.0)
    assert g.summer_capability_frac == pytest.approx(0.9)
    assert g.winter_capability_frac == pytest.approx(1.0)


def test_blank_winter_takes_summer(seasonal_armed):
    (g,) = _load([_row(wi=None)])
    assert g.pmax_mw == pytest.approx(90.0)
    assert g.summer_capability_frac == pytest.approx(1.0)
    assert g.winter_capability_frac == pytest.approx(1.0)


def test_blank_both_takes_nameplate(seasonal_armed):
    (g,) = _load([_row(su=None, wi=None)])
    assert g.pmax_mw == pytest.approx(100.0)
    assert g.summer_capability_frac == pytest.approx(1.0)


def test_non_cc_winter_capped_at_max_nameplate_summer(seasonal_armed):
    tech = "Natural Gas Fired Combustion Turbine"
    (g,) = _load([_row(pm="GT", np_=50.0, su=45.0, wi=60.0, tech=tech)])
    assert g.plant_group == "CT_PEAKER"
    assert g.pmax_mw == pytest.approx(50.0)
    assert g.winter_capability_frac == pytest.approx(1.0)
    assert g.summer_capability_frac == pytest.approx(0.9)


def test_off_basis_is_byte_identical():
    prior = paths.eia860_seasonal_capacity_basis()
    paths.set_eia860_seasonal_capacity_basis(False)
    try:
        (g,) = _load([_row()])
    finally:
        paths.set_eia860_seasonal_capacity_basis(prior)
    assert g.pmax_mw == pytest.approx(90.0)
    assert g.summer_capability_frac is None


def test_block_on_one_row_reallocates_summer_and_winter(tmp_path, seasonal_armed):
    """A non-NG block (CA carries the block total, CTs blank) is reallocated."""
    sheet = pd.DataFrame(
        {
            "Plant Code": [990001, 990001, 990001],
            "Generator ID": ["CT1", "CT2", "CA1"],
            "Prime Mover": ["CT", "CT", "CA"],
            "Unit Code": ["1", "1", "1"],
            "Status": ["OP", "OP", "OP"],
            "Nameplate Capacity (MW)": [240.0, 240.0, 320.0],
            "Summer Capacity (MW)": [None, None, 560.0],
            "Energy Source 1": ["NG", "NG", "SGC"],
        }
    )
    sheet.to_parquet(tmp_path / "eia860_generator_operable.parquet")
    e860._cc_block_summer_ratings.cache_clear()
    df = pd.DataFrame(
        [
            {**_row("CT1", "CT", 240.0, None, None), "winter_capacity_mw": None},
            {**_row("CT2", "CT", 240.0, None, None), "winter_capacity_mw": None},
            {**_row("CA1", "CA", 320.0, 560.0, 640.0)},
        ]
    )
    out = e860._apply_cc_block_summer_rating(df, tmp_path, "SPP")
    np.testing.assert_allclose(
        out["net_summer_capacity_mw"].to_numpy(float), [168.0, 168.0, 224.0]
    )
    # The one-row WINTER total is not a generator's rating either.
    assert out["winter_capacity_mw"].isna().all()
    e860._cc_block_summer_ratings.cache_clear()


def test_availability_takes_each_season_rating_no_flat_derate():
    """The builder applies summer 0.9 Jun-Sep and winter 1.0 Oct-May only."""
    summer = np.isin(_hour_to_month_index(8760), [5, 6, 7, 8])

    def _avail(sf, wf):
        gen = Generator(
            unit_id="cc1",
            name="cc1",
            zone=ZONE,
            fuel_type="gas_cc",
            pmax_mw=100.0,
            heat_rate=7.0,
            online_year=2010,
            plant_group="CC_REGULAR",
            plant_code=990001,
            summer_capability_frac=sf,
            winter_capability_frac=wf,
        )
        cfg = ScenarioConfig(mode="backcast", weather_year=2023, iso="MISO")
        fa = generators_to_fleet_arrays(
            [gen], [ZONE], iso="MISO", config=cfg, year=2023
        )
        return fa.availability[0]

    flat = _avail(1.0, 1.0)  # seasonal basis at 1.0: no flat class derate
    legacy = _avail(None, None)  # off the basis: the flat 10 % CC derate
    np.testing.assert_allclose(legacy[summer], 0.9 * flat[summer], rtol=1e-9)
    np.testing.assert_allclose(legacy[~summer], flat[~summer], rtol=1e-9)
    seasonal = _avail(0.9, 1.0)
    np.testing.assert_allclose(seasonal[summer], 0.9 * flat[summer], rtol=1e-9)
    np.testing.assert_allclose(seasonal[~summer], flat[~summer], rtol=1e-9)
