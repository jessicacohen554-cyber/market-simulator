"""Balancing-authority membership shared by the LP fleet and the benchmark (R-SOCO-B).

``market_sim.data.ba_membership`` reads two registries so the LP fleet, the
EIA-923 benchmark and the must-run injection sit on the one boundary EIA-930
measures SOCO's load on (rule 19):

* ``ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE`` now reaches the LP fleet too, so the
  former Gulf Power plants the 2019-2023 vintages code SOCO leave the fleet —
  DATED since R-SOCO-B2 by ``ISO_BA_EXITS``: they are members until hour-ending
  UTC 2022-07-13 12:00 (owner ruling (C), hour grain);
* ``ISO_BA_JOINS`` admits PowerSouth (``AEC``) from 2021-09-01: fleet rows in the
  join year (masked offline before September), out of the benchmark before 2021
  and before September 2021.

Every other region reads empty registries and is byte-identical.
"""

import importlib.util

import pandas as pd
import pytest

from market_sim.config.constants import ISO_BA_EXITS, ISO_BA_JOINS
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
    # R-SOCO-B2: Gulf was inside SOCO's BA until 2022-07-13 (ISO_BA_EXITS).
    assert {641, 643} <= codes
    f2020 = load_fleet_from_csv("SOCO", data_dir=_EIA860 / "vintage_2020", year=2020)
    codes = {int(g.plant_code) for g in f2020}
    assert not (codes & _AEC_2021)
    assert {641, 643} <= codes
    # Vintage 2022 codes Santa Rosa FPL, but it was a member until the exit.
    f2022 = load_fleet_from_csv("SOCO", data_dir=_EIA860 / "vintage_2022", year=2022)
    assert {641, 643, 55242} <= {int(g.plant_code) for g in f2022}


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


def test_exit_registry_is_soco_gulf_to_fpl_only():
    assert ISO_BA_EXITS == {"SOCO": {"FPL": "2022-07-13 12:00"}}
    for iso in ("ERCOT", "MISO", "PJM", "NWPP", "SPP"):
        assert bm.ba_exit_stamps(iso) == {}
        assert bm.exit_member_plants(iso, 2019) == frozenset()


@pytest.mark.skipif(not _HAVE_860, reason="EIA-860 vintages not hydrated")
def test_exit_members_are_exactly_the_gulf_plants_through_2022():
    stamps = bm.ba_exit_stamps("SOCO")
    # Only plants the region's own vintages coded SOCO — never FPL's own fleet.
    assert set(stamps) == _GULF
    assert set(stamps.values()) == {pd.Timestamp("2022-07-13 12:00")}
    for y in (2019, 2020, 2021, 2022):
        assert bm.exit_member_plants("SOCO", y) == frozenset(_GULF)
    assert bm.exit_member_plants("SOCO", 2023) == frozenset()
    assert bm.exit_member_plants("SOCO", None) == frozenset()


@pytest.mark.skipif(not _HAVE_860, reason="EIA-860 vintages not hydrated")
def test_recode_drop_is_dated_by_the_exit():
    df = pd.DataFrame({"plant_id": sorted(_GULF) + [649]})
    assert bm.drop_current_ba_recoded_rows(df, "SOCO", year=2021) is df
    assert bm.drop_current_ba_recoded_rows(df, "SOCO", year=2022) is df
    out = bm.drop_current_ba_recoded_rows(df, "SOCO", year=2023)
    assert set(out["plant_id"]) == {649}


@pytest.mark.skipif(not _HAVE_860, reason="EIA-860 vintages not hydrated")
def test_exit_row_and_month_share_in_exit_year_only():
    rows = bm.ba_exit_first_outside_row("SOCO", 2022)
    # Row 4637 carries hour-ending UTC 2022-07-13 12:00 on SOCO's Central clock.
    assert set(rows) == _GULF and set(rows.values()) == {4637}
    assert bm.ba_exit_first_outside_row("SOCO", 2021) == {}
    assert bm.ba_exit_first_outside_row("SOCO", 2023) == {}
    share = bm.ba_exit_month_share("SOCO", 2022)
    assert {m for m, _ in share.values()} == {7}
    assert all(0.35 < s < 0.45 for _, s in share.values())
    assert bm.ba_exit_month_share("ERCOT", 2022) == {}


@pytest.mark.skipif(not _HAVE_860, reason="EIA-860 vintages not hydrated")
def test_benchmark_keeps_gulf_until_the_exit():
    from market_sim.data.hydro import load_monthly_generation

    rcf = _rcf()
    for y in (2019, 2020, 2021, 2022):
        assert {641, 643, 55242} <= rcf._iso_plant_ids("SOCO", y)
    assert not (rcf._iso_plant_ids("SOCO", 2023) & _GULF)
    assert not (rcf._iso_plant_ids("SOCO", None) & _GULF)
    gen = load_monthly_generation()
    frame = rcf._eia923_frame(2022, gen, "SOCO")
    gulf = frame[frame["plant_id"].isin(_GULF)]
    months = [f"m{i:02d}" for i in range(1, 13)]
    assert not gulf.empty
    assert (gulf[months[7:]] == 0.0).all().all()
    assert (gulf["annual_mwh"] - gulf[months].sum(axis=1)).abs().max() < 1e-6
    raw = gen[(gen["year"] == 2022) & gen["plant_id"].isin(_GULF)]
    assert gulf["m07"].sum() < 0.45 * raw["netgen_july_mwh"].sum()
    f2021 = rcf._eia923_frame(2021, gen, "SOCO")
    raw21 = gen[(gen["year"] == 2021) & gen["plant_id"].isin([641, 643])]
    got = f2021[f2021["plant_id"].isin([641, 643])]["annual_mwh"].sum()
    assert abs(got - raw21["netgen_annual_mwh"].sum()) < 1.0
