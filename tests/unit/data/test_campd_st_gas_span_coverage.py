"""Tests for the miso-279 ST_GAS span coverage of the fuel-split tranche family.

``ScenarioConfig.campd_st_gas_span_coverage`` is a sub-gate of
``campd_unit_fuel_split``: armed together they select the four
``-fuelsplit-stcov-`` companions written by
``derive_thermal_tranches.py --st-gas-span-coverage``. Trivial cases first (the
selector, the path resolver, the byte-safe appender), then the committed MISO
companions: each must START with its fuel-split companion's exact bytes and add
only ST_GAS lines, which is what makes the gate a clean single delta.
"""

from __future__ import annotations

import json

import pytest

import market_sim.data.fleet.campd_bins as cb
from market_sim.config.scenarios import ScenarioConfig
from scripts.data import derive_thermal_tranches as dtt
from tests.helpers import REPO_ROOT

PROC = REPO_ROOT / "data" / "raw" / "_processed-legacy"
FAMILY = (
    "thermal_tranches_MISO.csv",
    "thermal_tranches_online_frac_by_year_MISO.csv",
    "thermal_tranches_p25_level_mw_MISO.csv",
    "thermal_tranches_oom_level_mw_MISO.csv",
)


def _fs(name: str):
    return dtt.fuel_split_companion_path(PROC / name)


def _cov(name: str):
    return dtt.st_gas_span_coverage_companion_path(_fs(name))


def test_selector_is_a_sub_gate_of_the_fuel_split():
    """Unarmed values are the plain booleans; the tag needs the fuel split."""
    assert cb.campd_fuel_split_selector(ScenarioConfig()) is False
    assert (
        cb.campd_fuel_split_selector(ScenarioConfig(campd_unit_fuel_split=True)) is True
    )
    assert (
        cb.campd_fuel_split_selector(ScenarioConfig(campd_st_gas_span_coverage=True))
        is False
    )
    armed = ScenarioConfig(campd_unit_fuel_split=True, campd_st_gas_span_coverage=True)
    assert cb.campd_fuel_split_selector(armed) == cb.ST_GAS_SPAN_COVERAGE_TAG
    # Under per-unit attribution the fuel split is refused outright (the
    # per-unit composition was deleted at NWPP-NEXT-16), never silently read.
    with pytest.raises(ValueError):
        cb.campd_fuel_split_selector(
            ScenarioConfig(
                campd_unit_fuel_split=True,
                campd_st_gas_span_coverage=True,
                campd_per_unit_attribution=True,
            )
        )


def test_companion_path_names():
    """Deriver and resolver agree on the name; the ISO suffix stays last."""
    base = PROC / "thermal_tranches_p25_level_mw_MISO.csv"
    got = dtt.st_gas_span_coverage_companion_path(dtt.fuel_split_companion_path(base))
    assert got.name == "thermal_tranches_p25_level_mw-fuelsplit-stcov-MISO.csv"
    assert cb._fuel_split_companion(base, cb.ST_GAS_SPAN_COVERAGE_TAG) == got
    assert cb._fuel_split_companion(base, True) == dtt.fuel_split_companion_path(base)


def test_resolver_degrades_to_the_fuel_split_where_not_derived():
    """No stcov companion for PJM: it falls to PJM's incumbent, never past it."""
    tag = cb.ST_GAS_SPAN_COVERAGE_TAG
    assert cb.thermal_tranche_csv_for_iso("PJM", fuel_split=tag).name == (
        "thermal_tranches_PJM.csv"
    )
    assert cb.thermal_tranche_csv_for_iso("MISO", fuel_split=True).name == (
        "thermal_tranches-fuelsplit-MISO.csv"
    )


def test_append_rows_is_byte_safe(tmp_path):
    """Existing bytes (odd float spellings included) are kept; rows append."""
    src = tmp_path / "a.csv"
    src.write_text("plant_code,plant_group,x\n1,COAL,1.10\n2,COAL,2.2000")
    dst = tmp_path / "b.csv"
    dtt._append_rows(src, dst, [{"plant_code": 3, "plant_group": "ST_GAS", "x": 7.5}])
    assert dst.read_text() == (
        "plant_code,plant_group,x\n1,COAL,1.10\n2,COAL,2.2000\n3,ST_GAS,7.5\n"
    )


def _targets() -> set[int]:
    side = json.loads(_cov(FAMILY[0]).with_suffix(".meta.json").read_text())
    return set(side["derive_invocation"]["target_plants"])


@pytest.mark.parametrize("name", FAMILY)
def test_committed_companion_is_a_pure_append(name):
    """Every fuel-split byte survives; appended lines are target ST_GAS only."""
    base = _fs(name).read_bytes()
    comp = _cov(name).read_bytes()
    assert comp.startswith(base)
    header = base.decode().splitlines()[0].split(",")
    gcol = header.index("plant_group")
    targets = _targets()
    for line in comp[len(base) :].decode().splitlines():
        if not line.strip():
            continue
        cells = line.split(",")
        assert cells[gcol] == "ST_GAS"
        assert int(cells[0]) in targets


def test_coverage_reaches_the_st_gas_floor_readers():
    """Armed, Baxter Wilson 2050 carries an ST_GAS row at every floor layer."""
    tag = cb.ST_GAS_SPAN_COVERAGE_TAG
    for fn in (cb.thermal_tranche_p25_level, cb.thermal_tranche_online_frac):
        fn.cache_clear() if hasattr(fn, "cache_clear") else None
        assert (2050, "ST_GAS") not in fn("MISO", False, False, True)
        assert (2050, "ST_GAS") in fn("MISO", False, False, tag)
    fn = cb.thermal_tranche_p25_measured_level
    fn.cache_clear()
    assert (2050, "ST_GAS") not in fn("MISO", True)
    assert (2050, "ST_GAS") in fn("MISO", tag)
