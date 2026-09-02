"""The CAMPD -> model-class crosswalk repair (nyiso-174).

Guards the two properties that make ``scripts.lib.campd_measured_classes`` a
strict CROSSWALK repair rather than a reclassification: it is a no-op wherever
the shared ``unitType`` construction already names a class the plant carries,
and it never moves a unit across the turbine/boiler prime-mover line.
"""

from __future__ import annotations

import pytest

from scripts.lib.campd_measured_classes import (
    campd_unittype_class,
    corrected_unit_class,
)

#: East River (2493) as the model fleet carries it — the measured case behind
#: the repair (EIA-860: GT x2 306.0 MW summer + ST x2 309.5 MW; no CA/CT/CS).
EAST_RIVER_GROUPS = {"CT_CHP": 306.0, "ST_CHP": 309.5}


@pytest.mark.parametrize(
    ("unit_type", "is_chp", "expected"),
    [
        ("Combined cycle", True, "CC_CHP"),
        ("Combined cycle", False, "CC_REGULAR"),
        ("Combustion turbine", True, "CT_CHP"),
        ("Combustion turbine", False, "CT_PEAKER"),
        ("Dry bottom wall-fired boiler", True, "ST_CHP"),
        ("Tangentially-fired", False, "ST_GAS"),
        ("Process heater", False, None),
    ],
)
def test_unittype_construction_is_the_shared_one(unit_type, is_chp, expected):
    """The pre-repair construction is reproduced verbatim, so both bases are
    measurable side by side."""
    assert campd_unittype_class(unit_type, is_chp) == expected


def test_east_river_turbines_land_on_the_ct_bin_not_the_cc_bin():
    """CAMPD tags East River's two GTs "Combined cycle"; the plant has no CC
    bin, so they take its turbine-family bin, ``CT_CHP``."""
    assert corrected_unit_class("CC_CHP", EAST_RIVER_GROUPS) == "CT_CHP"


def test_east_river_boilers_stay_on_the_steam_bin():
    """The steam half is already right and must not move."""
    assert corrected_unit_class("ST_CHP", EAST_RIVER_GROUPS) == "ST_CHP"


@pytest.mark.parametrize(
    "klass", ["CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS"]
)
def test_noop_when_the_plant_already_carries_the_class(klass):
    """The property that makes this a crosswalk repair: wherever the two
    constructions agree, the corrected one returns the same class."""
    assert corrected_unit_class(klass, {klass: 100.0}) == klass


def test_never_crosses_the_turbine_boiler_line():
    """A boiler-fired unit at a turbine-only plant keeps its steam class rather
    than being absorbed into a CT/CC bin — a population gap stays visible."""
    assert corrected_unit_class("ST_GAS", {"CT_PEAKER": 40.0}) == "ST_GAS"
    assert corrected_unit_class("CT_PEAKER", {"ST_GAS": 45.0}) == "CT_PEAKER"


def test_plant_absent_from_the_model_keeps_its_unittype_class():
    """The correction never invents a bin for a plant the fleet does not have."""
    assert corrected_unit_class("CC_REGULAR", {}) == "CC_REGULAR"
    assert corrected_unit_class("CC_REGULAR", None) == "CC_REGULAR"


def test_s_a_carlson_cc_row_takes_the_plants_turbine_bin():
    """nyiso-173 S1's 87 MW routing defect, same family: 2682 is tagged
    ``CC_REGULAR`` while the model carries only ``ST_GAS`` + ``CT_PEAKER``."""
    assert (
        corrected_unit_class("CC_REGULAR", {"ST_GAS": 45.0, "CT_PEAKER": 42.0})
        == "CT_PEAKER"
    )


def test_none_passes_through():
    assert corrected_unit_class(None, EAST_RIVER_GROUPS) is None
