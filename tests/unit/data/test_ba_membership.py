"""Balancing-authority membership shared by the LP fleet and the benchmark (R-SOCO-B).

``market_sim.data.ba_membership`` reads two registries so the LP fleet, the
EIA-923 benchmark and the must-run injection sit on the one boundary EIA-930
measures SOCO's load on (rule 19):

* ``ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE`` now reaches the LP fleet too, so the
  former Gulf Power plants the 2019-2023 vintages code SOCO leave the fleet;
* ``ISO_BA_JOINS`` admits PowerSouth (``AEC``) from 2021-09-01: fleet rows in the
  join year (masked offline before September), out of the benchmark before 2021
  and before September 2021.

Every other region reads empty registries and is byte-identical.
"""

import importlib.util

import pandas as pd
import pytest

from market_sim.config.constants import ISO_BA_JOINS
from market_sim.data import ba_membership as bm
from tests.helpers import REPO_ROOT

_EIA860 = REPO_ROOT / "data" / "raw" / "eia-860"
_HAVE_860 = (_EIA860 / "vintage_2021" / "eia860_plant.parquet").exists()
_GULF = {641, 643, 7715, 50310, 55242, 57502, 63754, 64757, 65036}
_AEC_2021 = {53, 55, 56, 533, 6192, 7063, 56522, 64469}


def _rcf():
    spec = importlib.util.spec_from_file_location(
        "rcf_ba_membership", str(REPO_ROOT / "scripts" / "run_calibration_full.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_join_registry_is_soco_powersouth_only():
    assert ISO_BA_JOINS == {"SOCO": {"AEC": (2021, 9)}}


def test_joining_codes_by_year():
    assert bm.joining_ba_codes("SOCO", None) == ()
    assert bm.joining_ba_codes("SOCO", 2020) == ()
    assert bm.joining_ba_codes("SOCO", 2021) == ("AEC",)
    assert bm.joining_ba_codes("soco", 2023) == ("AEC",)
    for iso in ("ERCOT", "MISO", "PJM", "NWPP"):
        assert bm.joining_ba_codes(iso, 2021) == ()


def test_recode_drop_returns_same_object_when_unregistered_or_clean():
    df = pd.DataFrame({"plant_id": [641, 1]})
    assert bm.drop_current_ba_recoded_rows(df, "ERCOT") is df
    empty = df.iloc[:0]
    assert bm.drop_current_ba_recoded_rows(empty, "SOCO") is empty
    no_col = pd.DataFrame({"x": [1]})
    assert bm.drop_current_ba_recoded_rows(no_col, "SOCO") is no_col


@pytest.mark.skipif(not _HAVE_860, reason="EIA-860 vintages not hydrated")
def test_recode_drop_removes_gulf_plants_for_soco():
    df = pd.DataFrame({"plant_id": sorted(_GULF) + [649]})  # 649 = Vogtle
    out = bm.drop_current_ba_recoded_rows(df, "SOCO")
    assert set(out["plant_id"]) == {649}
    assert _GULF <= bm.current_ba_recoded_plants("SOCO")


@pytest.mark.skipif(not _HAVE_860, reason="EIA-860 vintages not hydrated")
def test_join_first_month_by_year():
    y2021 = bm.ba_join_first_month("SOCO", 2021)
    assert set(y2021) == _AEC_2021 and set(y2021.values()) == {9}
    y2019 = bm.ba_join_first_month("SOCO", 2019)
    assert set(y2019) == _AEC_2021 - {64469}
    assert set(y2019.values()) == {bm.NOT_A_MEMBER_THIS_YEAR}
    assert bm.ba_join_first_month("SOCO", 2022) == {}
    assert bm.ba_join_first_month("ERCOT", 2021) == {}


@pytest.mark.skipif(not _HAVE_860, reason="EIA-860 vintages not hydrated")
def test_vintage_fleet_drops_gulf_and_admits_powersouth_in_join_year():
    from market_sim.data.fleet import load_fleet_from_csv

    f2023 = load_fleet_from_csv("SOCO", data_dir=_EIA860 / "vintage_2023", year=2023)
    assert not ({int(g.plant_code) for g in f2023} & _GULF)
    f2021 = load_fleet_from_csv("SOCO", data_dir=_EIA860 / "vintage_2021", year=2021)
    codes = {int(g.plant_code) for g in f2021}
    assert {533, 7063} <= codes
    assert not (codes & _GULF)
    f2020 = load_fleet_from_csv("SOCO", data_dir=_EIA860 / "vintage_2020", year=2020)
    assert not ({int(g.plant_code) for g in f2020} & (_AEC_2021 | _GULF))


@pytest.mark.skipif(not _HAVE_860, reason="EIA-860 vintages not hydrated")
def test_benchmark_membership_gates_powersouth_by_year_and_month():
    from market_sim.data.hydro import load_monthly_generation

    rcf = _rcf()
    assert not (rcf._iso_plant_ids("SOCO", 2019) & {533, 7063})
    assert not (rcf._iso_plant_ids("SOCO", 2020) & {533, 7063})
    assert {533, 7063} <= rcf._iso_plant_ids("SOCO", 2021)
    assert {533, 7063} <= rcf._iso_plant_ids("SOCO", 2022)
    frame = rcf._eia923_frame(2021, load_monthly_generation(), "SOCO")
    aec = frame[frame["plant_id"].isin(_AEC_2021)]
    assert not aec.empty
    months = [f"m{i:02d}" for i in range(1, 13)]
    assert (aec[months[:8]] == 0.0).all().all()
    assert (aec["annual_mwh"] - aec[months[8:]].sum(axis=1)).abs().max() < 1e-6
    # Any other ISO's membership is untouched by the joins registry.
    assert rcf._iso_plant_ids("MISO", 2019) == rcf._iso_plant_ids("MISO", None)
