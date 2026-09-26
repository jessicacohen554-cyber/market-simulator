"""Tests for ``scripts.lib.heat_rate_years.union_fleet``'s class-preserving mode.

neiso-118: a unit re-classed by a later EIA-860 vintage (Canal 3, plant 1599:
CT_PEAKER in 2019-2022, oil in 2023-2025) must stay in a derive's target
population when the derive names its class, and the default (no ``klass``)
must keep the latest-record behaviour byte-for-byte.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.heat_rate_years import class_capacity, union_fleet  # noqa: E402


@dataclass
class _Gen:
    unit_id: str
    plant_code: int
    plant_group: str
    pmax_mw: float


def _fleets() -> dict[int, list]:
    return {
        2019: [
            _Gen("1599_3", 1599, "CT_PEAKER", 330.0),
            _Gen("1_1", 1, "CT_PEAKER", 50.0),
        ],
        2023: [_Gen("1599_3", 1599, "", 330.0), _Gen("1_1", 1, "CT_PEAKER", 55.0)],
    }


def test_default_keeps_latest_record():
    """Without ``klass`` the latest vintage wins, as before neiso-118."""
    union = union_fleet(_fleets())
    assert {g.unit_id: g.plant_group for g in union} == {
        "1599_3": "",
        "1_1": "CT_PEAKER",
    }
    assert class_capacity(union, "CT_PEAKER") == {1: 55.0}


def test_klass_keeps_a_unit_a_later_vintage_reclasses():
    """With ``klass`` a unit in the class in ANY year keeps its class record."""
    union = union_fleet(_fleets(), klass="CT_PEAKER")
    assert class_capacity(union, "CT_PEAKER") == {1599: 330.0, 1: 55.0}


def test_klass_still_takes_the_latest_in_class_record():
    """A unit in the class every year still reads its latest record."""
    union = union_fleet(_fleets(), klass="CT_PEAKER")
    assert [g.pmax_mw for g in union if g.unit_id == "1_1"] == [55.0]


def test_klass_family_keeps_a_coal_plant_a_later_vintage_converts():
    """soco-71: the coal derive names the coal FAMILY token, not a subclass.

    Crist (641) is COAL_BIT in 2019 and ST_GAS after its 2020 gas conversion; the
    latest-record union dropped it from the coal derive's population, so its 2019
    coal dispatched on the eGRID rate. With ``klass="COAL"`` a subclass record in
    any year keeps the plant, and a plant coal in every year is unchanged.
    """
    fleets = {
        2019: [
            _Gen("641_4", 641, "COAL_BIT", 924.0),
            _Gen("3_4", 3, "COAL_BIT", 1118.5),
        ],
        2021: [_Gen("641_4", 641, "ST_GAS", 924.0), _Gen("3_4", 3, "COAL_BIT", 1118.5)],
    }
    assert class_capacity(union_fleet(fleets), "COAL") == {3: 1118.5}
    assert class_capacity(union_fleet(fleets, klass="COAL"), "COAL") == {
        641: 924.0,
        3: 1118.5,
    }
