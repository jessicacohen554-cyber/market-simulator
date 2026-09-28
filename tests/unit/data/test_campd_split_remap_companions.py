"""Tests for the miso-280 CAMPD split-remap companions.

``campd.CAMPD_UNIT_PLANT_REMAP`` now re-keys West Riverside Energy Center's CTs
(filed by CEMS under Riverside 55641 as ``CT-03`` / ``CT-04``) to EIA plant
64020, and ``ScenarioConfig.campd_split_remap_companions`` (default False)
selects the ``-splitremap-`` companions re-derived under that remap. Trivial
cases first: the remap on a one-unit frame, the path resolvers in a tmp dir
(off = the incumbent path, on = the companion, absent = raise), the selectors,
and the builder's plant-scoped splice (a fresh file equal to the incumbent on
the remap plants reproduces it byte-for-byte). Then the committed MISO paths:
off selects exactly the keeper's files, on selects the companions.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import market_sim.data.fleet.campd_bins as cb
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import campd
from market_sim.data import outages
from scripts.data import build_campd_split_remap_companions as bsr
from tests.helpers import REPO_ROOT

RAW = REPO_ROOT / "data" / "raw"
PROC = RAW / "_processed-legacy"

#: The MISO keeper's recipe, as far as these selectors read it.
KEEPER = dict(
    mode="backcast",
    iso="MISO",
    measured_cc_heat_rates=True,
    campd_unit_fuel_split=True,
    campd_st_gas_span_coverage=True,
    unit_outage_mixed_gas_routing=True,
)


def _raw_units(facility: str, units: list[str]) -> pd.DataFrame:
    """A 2-hour raw unit-level CAMPD frame for ``units`` at ``facility``."""
    frames = []
    for u in units:
        frames.append(
            pd.DataFrame(
                {
                    "stateCode": "WI",
                    "facilityName": "Riverside Energy Center",
                    "facilityId": facility,
                    "unitId": u,
                    "date": pd.to_datetime(["2023-01-01"] * 2),
                    "hour": [0, 1],
                    "grossLoad": [100.0, 100.0],
                    "steamLoad": np.nan,
                    "so2Mass": 0.0,
                    "co2Mass": 1.0,
                    "noxMass": 0.0,
                    "heatInput": 700.0,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def test_remap_routes_west_riverside_cts_to_64020():
    """(55641, CT-03/CT-04) -> 64020; CT-01/CT-02 stay on 55641."""
    assert campd.CAMPD_UNIT_PLANT_REMAP[(55641, "CT-03")] == 64020
    assert campd.CAMPD_UNIT_PLANT_REMAP[(55641, "CT-04")] == 64020
    assert 55641 in campd.CAMPD_SPLIT_FACILITIES
    out = campd._normalize_campd(
        _raw_units("55641", ["CT-01", "CT-02", "CT-03", "CT-04"]), 2023
    )
    by_unit = out.groupby("unit_id")["plant_id"].unique()
    assert list(by_unit["CT-01"]) == [55641]
    assert list(by_unit["CT-02"]) == [55641]
    assert list(by_unit["CT-03"]) == [64020]
    assert list(by_unit["CT-04"]) == [64020]


def test_companion_name_and_absent_companion_raises(tmp_path):
    """The tag goes before the ISO token; an absent companion raises."""
    for base, want in (
        ("campd-unit-outages-unitroute-MISO.csv", "campd-unit-outages-unitroute-splitremap-MISO.csv"),
        ("campd_cc_heat_rates_MISO.csv", "campd_cc_heat_rates-splitremap-MISO.csv"),
        ("thermal_tranches-fuelsplit-stcov-MISO.csv", "thermal_tranches-fuelsplit-stcov-splitremap-MISO.csv"),
    ):  # fmt: skip
        with pytest.raises(FileNotFoundError):
            campd.split_remap_companion(tmp_path / base)
        (tmp_path / want).write_text("x\n")
        assert campd.split_remap_companion(tmp_path / base) == tmp_path / want
        assert bsr.companion_path(tmp_path / base).name == want


def test_outage_resolvers_off_on_in_tmp_dir(tmp_path, monkeypatch):
    """Off: the incumbent path. On: the '-splitremap-' companion."""
    monkeypatch.setattr(outages, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
    names = {
        "std": "campd-unit-outages-unitroute-XISO.csv",
        "shortgas": "campd-unit-outages-shortgas-XISO.csv",
        "maxgen": "campd-unit-outages-maxgen-unitroute-XISO.csv",
    }
    for n in names.values():
        (tmp_path / n).write_text("facility_id\n")
    std = outages.unit_outage_csv_for_iso("XISO", mixed_gas_routing=True)
    sg = outages.unit_outage_short_gas_csv_for_iso("XISO")
    mg = outages.unit_outage_maxgen_csv_for_iso("XISO", mixed_gas_routing=True)
    assert (std.name, sg.name, mg.name) == (
        names["std"],
        names["shortgas"],
        names["maxgen"],
    )
    with pytest.raises(FileNotFoundError):
        outages.unit_outage_csv_for_iso(
            "XISO", mixed_gas_routing=True, split_remap=True
        )
    for n in names.values():
        (tmp_path / n.replace("-XISO", "-splitremap-XISO")).write_text("facility_id\n")
    assert outages.unit_outage_csv_for_iso(
        "XISO", mixed_gas_routing=True, split_remap=True
    ).name == ("campd-unit-outages-unitroute-splitremap-XISO.csv")
    assert outages.unit_outage_short_gas_csv_for_iso("XISO", split_remap=True).name == (
        "campd-unit-outages-shortgas-splitremap-XISO.csv"
    )
    assert outages.unit_outage_maxgen_csv_for_iso(
        "XISO", True, split_remap=True
    ).name == ("campd-unit-outages-maxgen-unitroute-splitremap-XISO.csv")


def test_selectors_off_are_the_plain_values():
    """Unarmed, both selectors return exactly what they returned before."""
    keeper = ScenarioConfig(**KEEPER)
    assert keeper.campd_split_remap_companions is False
    assert campd.split_remap_armed(keeper) is False
    assert cb.measured_cc_heat_rate_selector(keeper) is True
    assert cb.measured_cc_heat_rate_selector(ScenarioConfig()) is False
    assert cb.campd_fuel_split_selector(keeper) == cb.ST_GAS_SPAN_COVERAGE_TAG


def test_selectors_on_carry_the_tag():
    """Armed, the tag rides both selectors; without the fuel split it selects the plain family.

    SPP-99 widened the no-fuel-split case from a raise to the plain family's own
    '-splitremap-' companions (``PLAIN_SPLIT_REMAP_TAG``); a missing companion
    still raises at resolution, and per-unit attribution still raises here.
    """
    armed = ScenarioConfig(**KEEPER, campd_split_remap_companions=True)
    assert campd.split_remap_armed(armed) is True
    assert cb.measured_cc_heat_rate_selector(armed) == campd.SPLIT_REMAP_TAG
    assert cb.campd_fuel_split_selector(armed) == "stcov-splitremap"
    plain = ScenarioConfig(
        campd_unit_fuel_split=True, campd_split_remap_companions=True
    )
    assert cb.campd_fuel_split_selector(plain) == campd.SPLIT_REMAP_TAG
    assert (
        cb.campd_fuel_split_selector(ScenarioConfig(campd_split_remap_companions=True))
        == cb.PLAIN_SPLIT_REMAP_TAG
    )
    with pytest.raises(ValueError):
        cb.campd_fuel_split_selector(
            ScenarioConfig(
                campd_split_remap_companions=True, campd_per_unit_attribution=True
            )
        )


def test_cache_key_is_byte_inert_off():
    """The field is registered as an optional cache-key field dropped at False."""
    base = ScenarioConfig()
    assert ScenarioConfig(campd_split_remap_companions=False).cache_key() == (
        base.cache_key()
    )
    assert ScenarioConfig(campd_split_remap_companions=True).cache_key() != (
        base.cache_key()
    )


def test_splice_control_and_delta():
    """Equal remap-plant lines reproduce the incumbent; changed lines replace only them."""
    inc = (
        "facility_id,unit_id,outage_start\n"
        "10,1,2019-01-01\n"
        "55641,CT-01,2018-02-01\n"
        "55641,CT-01,2019-03-01\n"
        "55641,CT-03,2021-03-01\n"
        "60000,1,2020-01-01\n"
        "70000,1,2020-01-01\n"
    )
    plants = {55641, 64020}
    years = set(range(2019, 2027))
    text, c = bsr.splice(
        inc,
        inc,
        plants,
        "facility_id",
        "outage_start",
        years,
        ("facility_id", "unit_id"),
    )
    assert text == inc and c == {"removed": 2, "added": 2}
    fresh = (
        "facility_id,unit_id,outage_start\n"
        "55641,CT-01,2019-03-01\n"
        "64020,CT-03,2021-03-01\n"
        "99,1,2019-05-05\n"
    )
    text, c = bsr.splice(
        inc,
        fresh,
        plants,
        "facility_id",
        "outage_start",
        years,
        ("facility_id", "unit_id"),
    )
    assert text == (
        "facility_id,unit_id,outage_start\n"
        "10,1,2019-01-01\n"
        "55641,CT-01,2018-02-01\n"  # outside --years: kept verbatim
        "55641,CT-01,2019-03-01\n"
        "60000,1,2020-01-01\n"
        "64020,CT-03,2021-03-01\n"  # new plant: its sorted position
        "70000,1,2020-01-01\n"
    )  # plant 99 is not a remap plant: never imported
    assert c == {"removed": 2, "added": 2}


def _keeper_paths(cfg: ScenarioConfig) -> dict[str, Path]:
    arm = campd.split_remap_armed(cfg)
    return {
        "std": outages.unit_outage_csv_for_iso(
            "MISO", mixed_gas_routing=True, split_remap=arm
        ),
        "shortgas": outages.unit_outage_short_gas_csv_for_iso("MISO", split_remap=arm),
        "maxgen": outages.unit_outage_maxgen_csv_for_iso("MISO", True, split_remap=arm),
        "tranches": cb.thermal_tranche_csv_for_iso(
            "MISO", fuel_split=cb.campd_fuel_split_selector(cfg)
        ),
        "p25": cb._fuel_split_companion(
            PROC / "thermal_tranches_p25_level_mw_MISO.csv",
            cb.campd_fuel_split_selector(cfg),
        ),
    }


def test_committed_miso_off_selects_the_keeper_files():
    """Off: exactly the files the keeper's resolved_inputs pins."""
    got = {k: p.name for k, p in _keeper_paths(ScenarioConfig(**KEEPER)).items()}
    assert got == {
        "std": "campd-unit-outages-unitroute-MISO.csv",
        "shortgas": "campd-unit-outages-shortgas-MISO.csv",
        "maxgen": "campd-unit-outages-maxgen-unitroute-MISO.csv",
        "tranches": "thermal_tranches-fuelsplit-stcov-MISO.csv",
        "p25": "thermal_tranches_p25_level_mw-fuelsplit-stcov-MISO.csv",
    }


def test_committed_miso_on_selects_the_companions():
    """On: every family resolves to its committed '-splitremap-' companion."""
    cfg = ScenarioConfig(**KEEPER, campd_split_remap_companions=True)
    got = {k: p.name for k, p in _keeper_paths(cfg).items()}
    assert got == {
        "std": "campd-unit-outages-unitroute-splitremap-MISO.csv",
        "shortgas": "campd-unit-outages-shortgas-splitremap-MISO.csv",
        "maxgen": "campd-unit-outages-maxgen-unitroute-splitremap-MISO.csv",
        "tranches": "thermal_tranches-fuelsplit-stcov-splitremap-MISO.csv",
        "p25": "thermal_tranches_p25_level_mw-fuelsplit-stcov-splitremap-MISO.csv",
    }
    cb.measured_cc_heat_rates.cache_clear()
    rates = cb.measured_cc_heat_rates("MISO", 2023, split_remap=True)
    assert 64020 in rates and 55641 in rates
    assert 64020 not in cb.measured_cc_heat_rates("MISO", 2023)


@pytest.mark.parametrize(
    "incumbent,companion,col",
    [
        ("campd-unit-outages-unitroute-MISO.csv", "campd-unit-outages-unitroute-splitremap-MISO.csv", "facility_id"),
        ("campd-unit-outages-shortgas-MISO.csv", "campd-unit-outages-shortgas-splitremap-MISO.csv", "facility_id"),
        ("campd-unit-outages-maxgen-unitroute-MISO.csv", "campd-unit-outages-maxgen-unitroute-splitremap-MISO.csv", "facility_id"),
        ("_processed-legacy/campd_cc_heat_rates_MISO.csv", "_processed-legacy/campd_cc_heat_rates-splitremap-MISO.csv", "plant_code"),
        ("_processed-legacy/thermal_tranches-fuelsplit-stcov-MISO.csv", "_processed-legacy/thermal_tranches-fuelsplit-stcov-splitremap-MISO.csv", "plant_code"),
        ("_processed-legacy/thermal_tranches_online_frac_by_year-fuelsplit-stcov-MISO.csv", "_processed-legacy/thermal_tranches_online_frac_by_year-fuelsplit-stcov-splitremap-MISO.csv", "plant_code"),
        ("_processed-legacy/thermal_tranches_p25_level_mw-fuelsplit-stcov-MISO.csv", "_processed-legacy/thermal_tranches_p25_level_mw-fuelsplit-stcov-splitremap-MISO.csv", "plant_code"),
        ("_processed-legacy/thermal_tranches_oom_level_mw-fuelsplit-stcov-MISO.csv", "_processed-legacy/thermal_tranches_oom_level_mw-fuelsplit-stcov-splitremap-MISO.csv", "plant_code"),
    ],
)  # fmt: skip
def test_committed_companion_differs_only_on_the_remap_plants(
    incumbent, companion, col
):
    """Every line outside plants 55641 / 64020 is byte-identical to the keeper's."""
    inc = (RAW / incumbent).read_text().splitlines()
    comp = (RAW / companion).read_text().splitlines()
    assert inc[0] == comp[0]
    ci = inc[0].split(",").index(col)

    def other(lines: list[str]) -> list[str]:
        return [ln for ln in lines[1:] if ln.split(",")[ci] not in ("55641", "64020")]

    assert other(inc) == other(comp)
