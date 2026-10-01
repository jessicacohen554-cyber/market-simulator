"""Tests for the miso-278 unit-fuel split of the thermal-tranche family.

``ScenarioConfig.campd_unit_fuel_split`` selects the four ``-fuelsplit-``
companions written by ``derive_thermal_tranches.py --unit-fuel-split``. Trivial
cases first (the fuel classifier, the byte-safe line replacer, the path
resolver), then the committed MISO companions against their incumbents: every
line of a plant outside the mixed-fuel set, and every CHP line, must be
byte-identical, which is what makes the gate a clean single delta.
"""

from __future__ import annotations


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


@pytest.mark.parametrize(
    ("label", "klass"),
    [
        ("Coal", "COAL"),
        ("Coal Refuse", "COAL"),
        ("Coal, Pipeline Natural Gas", "COAL"),
        ("Pipeline Natural Gas", "GAS"),
        ("Natural Gas", "GAS"),
        ("Other Gas", "GAS"),
        ("Process Gas", "GAS"),
        ("Petroleum Coke", "OTHER"),
        ("Diesel Oil", "OTHER"),
        ("Wood", "OTHER"),
        (None, "OTHER"),
    ],
)
def test_unit_fuel_class(label, klass):
    """CAMPD's own primaryFuelInfo label decides the class; pet-coke is not coal."""
    assert dtt._unit_fuel_class(label) == klass


def test_companion_path_names():
    """The ISO suffix stays last so the companion sorts beside its incumbent."""
    base = PROC / "thermal_tranches_p25_level_mw_MISO.csv"
    got = dtt.fuel_split_companion_path(base)
    assert got.name == "thermal_tranches_p25_level_mw-fuelsplit-MISO.csv"
    assert cb._fuel_split_companion(base) == got


def test_replace_plant_rows_is_byte_safe(tmp_path):
    """Other plants' lines and kept groups are copied verbatim; rows append."""
    src = tmp_path / "a.csv"
    src.write_text(
        "plant_code,plant_group,x\n1,COAL,1.10\n2,COAL,2.2000\n2,ST_CHP,9\n3,ST_GAS,3\n"
    )
    dst = tmp_path / "b.csv"
    removed = dtt._replace_plant_rows(
        src,
        dst,
        {2},
        [{"plant_code": 2, "plant_group": "ST_GAS", "x": 7.5}],
        frozenset({"ST_CHP"}),
    )
    assert removed == 1
    assert dst.read_text() == (
        "plant_code,plant_group,x\n1,COAL,1.10\n2,ST_CHP,9\n3,ST_GAS,3\n2,ST_GAS,7.5\n"
    )


def test_selector_default_off_and_per_unit_composition_refused():
    """Off by default; under per-unit attribution it RAISES -- the per-unit
    fuel-split composition (NWPP-NEXT-14) was deleted at NWPP-NEXT-16 (rule 26)
    in favour of campd_per_unit_vintage_denominator."""
    assert cb.campd_fuel_split_selector(ScenarioConfig()) is False
    assert cb.campd_fuel_split_selector(ScenarioConfig(campd_unit_fuel_split=True))
    assert not hasattr(cb, "PER_UNIT_FUEL_SPLIT_TAG")
    for extra in ({}, {"campd_outage_merit_order_guard": True}):
        with pytest.raises(ValueError):
            cb.campd_fuel_split_selector(
                ScenarioConfig(
                    campd_unit_fuel_split=True,
                    campd_per_unit_attribution=True,
                    **extra,
                )
            )


def test_miso_karn_gas_bin_not_in_plain_online_frac():
    """Dan E Karn 1702's ST_GAS bin carries no plain-family online_frac row."""
    assert (1702, "ST_GAS") not in cb.thermal_tranche_online_frac(
        "MISO", False, False, True
    )


def test_per_unit_fuel_split_and_vintage_denominator_are_exclusive():
    """Rule 19: the per-unit fuel split never composes with the vintage
    denominator (deleted at NWPP-NEXT-16); arming both raises."""
    with pytest.raises(ValueError):
        cb.campd_fuel_split_selector(
            ScenarioConfig(
                campd_unit_fuel_split=True,
                campd_per_unit_attribution=True,
                campd_per_unit_vintage_denominator=True,
            )
        )
